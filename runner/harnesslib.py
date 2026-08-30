#!/usr/bin/env python3
"""harnesslib — 하네스 부기 코어. 프로그램이 소유하는 컴포넌트의 공용 로직.

여기 있는 것은 전부 "모델이 우회하면 안 되는 것"이다:
  P1 ID 발급 · P2 작업 선택(아사 방지) · P5 예산 · P6 판정(검증기) · P8-lite 격리 · P10 SUMMARY

규칙:
  - Python 3.9 stdlib only. 외부 의존성 없음.
  - 상태는 log.jsonl을 fold해서 파생한다 (I3). 상태 파일을 따로 만들지 않는다.
  - log.jsonl에는 append만 한다 (I2).
  - 이 모듈은 모델을 호출하지 않는다 (그건 drivers.py).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

HARNESS_ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("HARNESS_ROOT", str(HARNESS_ROOT))  # 도메인 검증기·부트스트랩이 $HARNESS_ROOT/runner/verify-doc 등을 찾는다 (회사 경로 무관)
HDIR_NAME = ".harness"
CONTRACT_FILES = ("spec.md", "verify", "init.sh", "domain.json", "plan.json")
BOOKKEEPING_OUTPUTS = ("log.jsonl", "SUMMARY.md", "BLOCKED.md", "plan.proposed.json")
APPROVAL_VERIFY = "approval"  # 게이트 작업의 검증기 값 — 사람의 승인(task_approved 이벤트)만 통과시킨다
PROPOSED_NAME = "plan.proposed.json"  # P7-lite: 러너가 제안한 리프 — 사람이(또는 plan.auto_accept 로) 받아들여야 plan.json 에 들어간다
ID_RE = re.compile(r"^(night|task)-(\d{3,})$")
NIGHT_BRANCH_PREFIX = "harness/"
TAIL_CHARS = 3000
# ASSUMPTIONS: P9 — 같은 파일을 이 횟수 이상 편집하면 doom loop 의심 (Claude 5 · B)
DOOM_EDIT_THRESHOLD = 8


class HarnessError(Exception):
    """계약 위반 / preflight 실패. 메시지는 사람이 읽는다."""


# ────────────────────────────────────────────────────────────── 플랫폼 (macOS + Ubuntu)

def ensure_utf8_stdio() -> None:
    """LANG=C 인 Ubuntu 서버에서 한글 출력이 UnicodeEncodeError 로 죽지 않게. 진입점과 훅이 첫 줄에서 부른다."""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


CLAUDE_CANDIDATES = (".local/bin/claude", ".claude/local/claude", ".npm-global/bin/claude")


def find_claude() -> Optional[str]:
    """claude CLI 경로. PATH → 흔한 설치 위치 (macOS / Ubuntu 공통). 비대화형 셸(nohup, at)에서 PATH 가 짧아도 찾는다."""
    found = shutil.which("claude")
    if found:
        return found
    home = Path.home()
    for rel in CLAUDE_CANDIDATES:
        cand = home / rel
        if cand.is_file() and os.access(cand, os.X_OK):
            return str(cand)
    for cand in (Path("/usr/local/bin/claude"), Path("/opt/homebrew/bin/claude")):
        if cand.is_file() and os.access(cand, os.X_OK):
            return str(cand)
    return None


# ────────────────────────────────────────────────────────────── time

def now() -> datetime:
    return datetime.now().astimezone()


def iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def parse_iso(s: str) -> datetime:
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.astimezone()
    return dt


def fmt_duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return "%dh%02dm" % (h, m)
    if m:
        return "%dm%02ds" % (m, s)
    return "%ds" % s


def fmt_clock(s: Optional[str]) -> str:
    """ISO → 'YYYY-MM-DD HH:MM' (SUMMARY 헤더용)."""
    if not s:
        return "?"
    try:
        return parse_iso(s).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return s


def tail(text: Optional[str], n: int = TAIL_CHARS) -> str:
    text = text or ""
    return text if len(text) <= n else "…" + text[-n:]


# ────────────────────────────────────────────────────────────── domain.json (계약 ②③④⑤ + 예산)

DOMAIN_DEFAULTS: Dict[str, Any] = {
    "write_scope": ["."],
    "human_scope": [],           # 대화형에서만 쓸 수 있는 경로 (사람이 넣는 수집함·기록) — 러너 모드는 write_scope 만 본다 (2026-08-29)
    "tools": [],
    "verify": {"cmd": ".harness/verify", "timeout_sec": 600, "smoke_timeout_sec": 120},
    "bootstrap": {"cmd": ".harness/init.sh", "timeout_sec": 600},
    "budget": {
        "hours": 8,
        "leaf_min_minutes": 5,     # 리프 하한 (spec §1)
        "leaf_max_minutes": 30,    # 리프 상한 = 작업당 모델 타임아웃 (ASSUMPTIONS: 30분 이상에서 일관성 상실)
        "max_attempts": 3,         # 이 횟수 실패하면 blocked (P8-lite)
        "starvation_minutes": 1440,  # 이보다 오래 기다린 작업은 무조건 먼저 (P2, 등급 D)
        "max_night_usd": 20.0,       # 밤 누적 비용 상한 (USD). null 상한은 상한이 아니다 — 해제는 명시적 null 로만
        "max_day_usd": None,         # 일일(로컬 자정 이후) 누적 상한 (USD) — 밤·루프 상한과 달리 다시 띄워도 리셋되지 않는다 (2026-08-29 $68 실측). null = 해제
        "rate_limit_stop": 0.85,     # 5시간 창 사용률이 이 이상 관측되면 밤 종료 (구독 요금제의 실질 예산; night-002 실측 67%)
    },
    "driver": {"name": "claude", "model": None, "effort": None, "max_turns": 120, "max_budget_usd": 5.0},
    "data_class": "public",      # public | private — private 면 대화형에서도 네트워크(curl 류·WebFetch/WebSearch·네트워크 스킬)를 훅이 거부 (D2, trifecta 를 구조로 끊는다)
    "plan": {
        "auto_propose": False,   # 큐가 비면 night-loop 가 decompose --propose 를 돌린다 (P7-lite)
        "auto_accept": False,    # 제안을 사람 승인 없이 plan.json 에 넣는다 — 무인 "완성도 반복" 은 이 둘을 켠 repo 에서만
        "propose_count": 6,      # 한 번에 제안할 리프 수
        "max_rounds": 3,         # 루프 한 번당 제안 횟수 상한 (무한 생성 방지)
    },
}


def _merge(base: Dict[str, Any], over: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    out = dict(base)
    for k, v in (over or {}).items():
        if k.startswith("_") or k.startswith("$"):
            continue  # 문서용 키
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


class Domain:
    """domain.json + 기본값. 속성은 전부 읽기 전용 뷰."""

    def __init__(self, raw: Optional[Dict[str, Any]] = None):
        self.raw = _merge(DOMAIN_DEFAULTS, raw or {})

    @property
    def write_scope(self) -> List[str]:
        ws = self.raw.get("write_scope") or ["."]
        return [str(p) for p in ws]

    @property
    def human_scope(self) -> List[str]:
        """대화형에서만 쓸 수 있는 경로 — 사람이 넣는 자료(수집함·기록·팩트). 러너 모드와 러너의 최종 판정(scope_violations)은
        write_scope 만 본다: 밤은 출처·기록을 지어낼 수 없고, 낮에는 사람이 승인 루프에 있다 (2026-08-29)."""
        return [str(p) for p in (self.raw.get("human_scope") or [])]

    @property
    def tools(self) -> List[Dict[str, Any]]:
        return list(self.raw.get("tools") or [])

    @property
    def verify_cmd(self) -> str:
        return str(self.raw["verify"]["cmd"])

    @property
    def data_class(self) -> str:
        v = str(self.raw.get("data_class") or "public")
        if v not in ("public", "private"):
            raise HarnessError("domain.json data_class 는 public | private (지금: %s)" % v)
        return v

    @property
    def is_private(self) -> bool:
        return self.data_class == "private"

    @property
    def plan_auto_propose(self) -> bool:
        return bool(self.raw["plan"]["auto_propose"])

    @property
    def plan_auto_accept(self) -> bool:
        return bool(self.raw["plan"]["auto_accept"])

    @property
    def plan_propose_count(self) -> int:
        return int(self.raw["plan"]["propose_count"])

    @property
    def plan_max_rounds(self) -> int:
        return int(self.raw["plan"]["max_rounds"])

    @property
    def verify_timeout(self) -> int:
        return int(self.raw["verify"]["timeout_sec"])

    @property
    def smoke_timeout(self) -> int:
        return int(self.raw["verify"].get("smoke_timeout_sec") or self.verify_timeout)

    @property
    def bootstrap_cmd(self) -> str:
        return str(self.raw["bootstrap"]["cmd"])

    @property
    def bootstrap_timeout(self) -> int:
        return int(self.raw["bootstrap"]["timeout_sec"])

    @property
    def hours(self) -> float:
        return float(self.raw["budget"]["hours"])

    @property
    def leaf_min(self) -> int:
        return int(self.raw["budget"]["leaf_min_minutes"])

    @property
    def leaf_max(self) -> int:
        return int(self.raw["budget"]["leaf_max_minutes"])

    @property
    def max_attempts(self) -> int:
        return int(self.raw["budget"]["max_attempts"])

    @property
    def starvation_minutes(self) -> float:
        return float(self.raw["budget"]["starvation_minutes"])

    @property
    def max_night_usd(self) -> Optional[float]:
        v = self.raw["budget"].get("max_night_usd")
        return None if v is None else float(v)

    @property
    def max_day_usd(self) -> Optional[float]:
        """일일(로컬 자정 이후) 누적 상한 — 로그에서 파생한다(day_cost_usd). 기본 None = 해제."""
        v = self.raw["budget"].get("max_day_usd")
        return None if v is None else float(v)

    @property
    def rate_limit_stop(self) -> Optional[float]:
        v = self.raw["budget"].get("rate_limit_stop")
        return None if v is None else float(v)

    @property
    def driver(self) -> Dict[str, Any]:
        return dict(self.raw["driver"])


def load_domain(repo: "Repo") -> Domain:
    if not repo.domain.exists():
        return Domain({})
    try:
        data = json.loads(repo.domain.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise HarnessError("domain.json 파싱 실패: %s" % e)
    if not isinstance(data, dict):
        raise HarnessError("domain.json은 객체여야 한다")
    return Domain(data)


# ────────────────────────────────────────────────────────────── 경로

@dataclass(frozen=True)
class Repo:
    root: Path

    @property
    def hdir(self) -> Path:
        return self.root / HDIR_NAME

    @property
    def spec(self) -> Path:
        return self.hdir / "spec.md"

    @property
    def verify(self) -> Path:
        return self.hdir / "verify"

    @property
    def init(self) -> Path:
        return self.hdir / "init.sh"

    @property
    def domain(self) -> Path:
        return self.hdir / "domain.json"

    @property
    def plan(self) -> Path:
        return self.hdir / "plan.json"

    @property
    def log(self) -> Path:
        return self.hdir / "log.jsonl"

    @property
    def summary(self) -> Path:
        return self.hdir / "SUMMARY.md"

    @property
    def blocked(self) -> Path:
        return self.hdir / "BLOCKED.md"

    @property
    def proposed(self) -> Path:
        return self.hdir / PROPOSED_NAME

    @property
    def sessions(self) -> Path:
        return self.hdir / "sessions"

    @property
    def gitignore(self) -> Path:
        return self.hdir / ".gitignore"

    def rel(self, p: Union[str, Path]) -> str:
        try:
            return str(Path(p).resolve().relative_to(self.root.resolve()))
        except ValueError:
            return str(p)


def find_repo(start: Union[str, Path]) -> Optional[Repo]:
    """start에서 위로 올라가며 .harness/ 를 찾는다. 없으면 None (훅이 다른 repo에서 무해하게 꺼지는 근거)."""
    p = Path(start).resolve()
    for cand in (p, *p.parents):
        if (cand / HDIR_NAME).is_dir():
            return Repo(cand)
    return None


MODE_A_MARK = "모드 A 전용"  # 네트워크 지시가 있는 스킬은 SKILL.md 앞부분에 이 표시가 있다 (VENDORED 규약) — private repo 에서는 훅이 호출을 거부


def network_skills(root: Optional[Path] = None) -> List[str]:
    """'모드 A 전용' 표시가 있는 스킬 이름 — 목록을 따로 관리하지 않고 SKILL.md 에서 읽는다 (한 곳의 진실)."""
    base = (root or HARNESS_ROOT) / "skills"
    out: List[str] = []
    for sk in sorted(base.glob("*/SKILL.md")):
        try:
            head = sk.read_text(encoding="utf-8", errors="replace")  # 파일 전체 — vendored frontmatter 가 길어 표시가 12줄 밖으로 밀려도 놓치지 않는다
        except OSError:
            continue
        if MODE_A_MARK in head:
            out.append(sk.parent.name)
    return out


def contract_missing(repo: Repo) -> List[str]:
    return [name for name in CONTRACT_FILES if not (repo.hdir / name).exists()]


# ────────────────────────────────────────────────────────────── I6 쓰기 범위

_REDIRECT_RE = re.compile(r"(?:(?<![<>&\-=!])>>?|\btee\b(?:\s+-[a-z]+)*)\s*[\"']?([^\s\"'<>|;&()`]+)")  # `->` `=>` `!>` 는 리다이렉션이 아니다 (findings/005)
_HEREDOC_RE = re.compile(r"<<(-?)\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")
# 명령 앞에 붙는 wrapper — `env X=1 curl` `time curl` `nice -n 5 python3 <<PY` `uv run python <<PY` `xargs -I{} curl {}` 는 같은 명령이다 (2026-08-29 리뷰 실측 우회)
WRAPPER_RE = r"(?:(?:sudo|env|time|nice|nohup|stdbuf|command|exec|caffeinate|xargs|uv\s+run|poetry\s+run|pipx\s+run)(?:\s+-\S+(?:\s+\d+)?)*(?:\s+[A-Za-z_][A-Za-z0-9_]*=\S*)*\s+|[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*"  # `nice -n 5` 의 숫자 인자까지
_SHELL_HEREDOC_RE = re.compile(r"(?:^|[|;&(]\s*)" + WRAPPER_RE + r"(?:\S*/)?(?:sh|bash|zsh|dash|ksh)\b[^|;&\n]*<<")  # 본문이 셸로 실행된다 — `>` 가 진짜 리다이렉션
EXEC_HEREDOC_RE = re.compile(r"(?:^|[|;&(]\s*)" + WRAPPER_RE + r"(?:\S*/)?(?:sh|bash|zsh|dash|ksh|python[0-9.]*|perl|ruby|node)\b[^|;&\n]*<<")  # 본문이 무엇이든 실행된다 — 거부 규칙(commit/push·네트워크)은 여기까지 본다
_SED_I_RE = re.compile(r"\bsed\s+-i(?:\s*'')?\s+(?:-e\s+)?(?:'[^']*'|\"[^\"]*\"|\S+)\s+([^\s|;&]+)")
_CP_MV_RE = re.compile(r"\b(?:cp|mv)\s+(?:-\S+\s+)*\S+\s+([^\s|;&]+)")
_TOUCH_RE = re.compile(r"\b(?:touch|mkdir(?:\s+-p)?)\s+([^\s|;&]+)")
_RM_RE = re.compile(r"(?:^|[|;&(]\s*)" + WRAPPER_RE + r"(?:rm|unlink|rmdir)((?:\s+[^\s|;&]+)+)")  # 삭제도 트리 변경이다 — `rm .harness-readonly` 가 D4 를 끄던 구멍 (2026-08-29 리뷰)


def strip_heredoc_bodies(cmd: str, keep: "re.Pattern[str]" = _SHELL_HEREDOC_RE) -> str:
    """heredoc 본문은 데이터라 스캔에서 뺀다 — night-003 실측: `def f() -> str:`·`<title>{x}`·주석의 `->` 를 쓰기 대상으로 오인해
    범위 안 쓰기를 거부했다 (findings/005). `keep` 에 맞는 머리 줄의 heredoc 은 본문을 그대로 둔다 — 기본은 셸 실행형(`bash <<EOF`):
    그 안의 `>` 만 진짜 리다이렉션이다. night-004 실측 2: `python3 - <<PY` 본문의 `<b>Sentiment</b>` 도 오인했다 — 파이썬 본문의 `>` 는 셸이 아니다.
    거부 규칙(commit/push·네트워크)은 EXEC_HEREDOC_RE 로 인터프리터 본문까지 본다 (`os.system("git commit")` 우회 방지).
    머리 줄(`cat > f <<EOF`)은 항상 훑는다. 놓치는 쪽은 러너의 git status 최종 판정이 받는다."""
    lines = cmd.splitlines()
    out: List[str] = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        out.append(ln)
        i += 1
        m = _HEREDOC_RE.search(ln)
        if not m or keep.search(ln):
            continue
        word, strip_tabs = m.group(3), bool(m.group(1))
        while i < len(lines):
            body = lines[i]
            i += 1
            if (body.lstrip("\t") if strip_tabs else body).rstrip() == word:
                out.append(body)
                break
    return "\n".join(out)


_LEADING_CD_RE = re.compile(r'''^\s*cd\s+(?:"([^"]+)"|'([^']+)'|(\S+))\s*(?:&&|;)''')


def leading_cd(cmd: str, cwd: Path) -> Path:
    """`cd <dir> && …` 로 시작하는 명령의 상대 경로 기준 — night-005 실측 3: `cd /tmp && cat > t.py` 의 `t.py` 를 repo 기준으로 풀어
    허용된 임시 디렉토리 쓰기를 거부했다 (findings/005). 앞머리 cd 하나만 본다 — 그 뒤는 휴리스틱 범위 밖."""
    m = _LEADING_CD_RE.match(cmd)
    if not m:
        return cwd
    target = Path(m.group(1) or m.group(2) or m.group(3) or ".").expanduser()
    return target if target.is_absolute() else cwd / target


def bash_write_targets(cmd: str) -> List[str]:
    """Bash 명령에서 쓰기 대상 경로를 휴리스틱으로 뽑는다 (> >> tee · sed -i · cp/mv 목적지 · touch/mkdir).

    완전하지 않다 — 훅의 조기 거부와 P9 편집 카운터용. 최종 판정은 러너가 git status 로 한다 (scope_violations).
    첫 밤 실측: bypass 모드의 모델은 파일을 전부 `cat > f <<EOF` 로 써서 Write/Edit 경로 검사가 아무것도 못 봤다.
    """
    cmd = strip_heredoc_bodies(cmd)
    out: List[str] = []
    for m in _REDIRECT_RE.finditer(cmd):
        t = m.group(1)
        if t.startswith("&") or t in ("/dev/null", "/dev/stdout", "/dev/stderr"):
            continue
        out.append(t)
    for rx in (_SED_I_RE, _CP_MV_RE, _TOUCH_RE):
        out.extend(m.group(1) for m in rx.finditer(cmd))
    for m in _RM_RE.finditer(cmd):
        out.extend(a for a in m.group(1).split() if not a.startswith("-"))
    return out


def scope_violations(domain: Domain, changed_paths: Sequence[str]) -> List[str]:
    """I6 최종 판정 — git 이 본 변경 경로(repo 상대) 중 쓰기 범위 밖. 도구와 무관하다 (heredoc, python open() 포함).

    .harness/log.jsonl 은 러너 자신이 시도 중에 쓰므로 제외, .harness/sessions/ 는 작업 공간. 나머지 .harness/* 는 위반.
    """
    scopes = [s.strip("/") for s in domain.write_scope]
    bad: List[str] = []
    for raw in changed_paths:
        p = raw.strip("/")
        if p == HDIR_NAME + "/log.jsonl" or p.startswith(HDIR_NAME + "/sessions/"):
            continue
        if p == HDIR_NAME or p.startswith(HDIR_NAME + "/"):
            bad.append(p)
            continue
        if "." in scopes:
            continue
        if not any(p == s or p.startswith(s + "/") for s in scopes):
            bad.append(p)
    return bad


# ────────────────────────────────────────────────────────────── log.jsonl (I2 append-only)

def read_log(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    out: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                out.append({"event": "_corrupt", "line": ln, "raw": line[:200]})
                continue
            if isinstance(ev, dict):
                out.append(ev)
    return out


def append_event(path: Path, event: str, **fields: Any) -> Dict[str, Any]:
    """한 줄 append. ts는 여기서만 찍는다 (모델이 찍지 않는다 — I1)."""
    ev: Dict[str, Any] = {"ts": iso(now()), "event": event}
    ev.update({k: v for k, v in fields.items() if v is not None})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return ev


# ────────────────────────────────────────────────────────────── plan.json

@dataclass
class Task:
    id: Optional[str]
    title: str
    goal: str
    verify: Union[str, Dict[str, Any], None]
    estimate_minutes: int
    depends_on: List[str] = field(default_factory=list)
    priority: int = 0
    origin: str = "plan"          # plan | repair
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def verify_cmd(self) -> str:
        return normalize_verify(self.verify)[0]

    @property
    def is_gate(self) -> bool:
        """승인 게이트 — 검증기가 'approval': 사람이 runner/queue approve 로 exit 0 을 준다. 모델은 자격을 얻지 않는다 (D1, 2026-08-29)."""
        return self.verify_cmd == APPROVAL_VERIFY

    def to_json(self) -> Dict[str, Any]:
        d = dict(self.raw)
        d.update({
            "id": self.id,
            "title": self.title,
            "goal": self.goal,
            "verify": self.verify,
            "estimate_minutes": self.estimate_minutes,
            "depends_on": list(self.depends_on),
            "priority": self.priority,
            "origin": self.origin,
        })
        return {k: v for k, v in d.items() if v is not None}


def _task_from_json(t: Dict[str, Any]) -> Task:
    try:
        return Task(
            id=t.get("id"),
            title=str(t.get("title") or "").strip(),
            goal=str(t.get("goal") or "").strip(),
            verify=t.get("verify"),
            estimate_minutes=int(t.get("estimate_minutes") or 0),
            depends_on=[str(d) for d in (t.get("depends_on") or [])],
            priority=int(t.get("priority") or 0),
            origin=str(t.get("origin") or "plan"),
            raw=dict(t),
        )
    except (TypeError, ValueError) as e:  # `priority: []`·`estimate_minutes: "abc"` — traceback 대신 접수 게이트의 반려 메시지
        raise HarnessError("plan.json 작업 필드 파싱 실패 (%s): %s" % (str(t.get("title") or t.get("id") or "?")[:60], e))


def load_plan(repo: Repo) -> Tuple[Dict[str, Any], List[Task]]:
    if not repo.plan.exists():
        raise HarnessError("plan.json이 없다: %s" % repo.plan)
    try:
        data = json.loads(repo.plan.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise HarnessError("plan.json 파싱 실패: %s" % e)
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
        raise HarnessError('plan.json은 {"tasks": [...]} 형태여야 한다')
    tasks = []
    for i, t in enumerate(data["tasks"]):
        if not isinstance(t, dict):
            raise HarnessError("plan.json tasks[%d]가 객체가 아니다" % i)
        tasks.append(_task_from_json(t))
    meta = {k: v for k, v in data.items() if k != "tasks"}
    return meta, tasks


def save_plan(repo: Repo, meta: Dict[str, Any], tasks: Sequence[Task]) -> None:
    data = dict(meta)
    data["tasks"] = [t.to_json() for t in tasks]
    repo.plan.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def task_from_json(t: Dict[str, Any]) -> Task:
    return _task_from_json(t)


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)\n\s*```", re.S)


def extract_json_block(text: str) -> Optional[Dict[str, Any]]:
    """모델 출력에서 마지막 ```json 블록(없으면 마지막 최상위 {…})을 객체로. 못 찾으면 None — 파싱 실패는 제안 실패다, 추측하지 않는다."""
    blocks = _JSON_FENCE_RE.findall(text or "")
    for cand in reversed(blocks):
        try:
            obj = json.loads(cand)
        except ValueError:
            continue
        if isinstance(obj, dict):
            return obj
    start = (text or "").rfind("{\"")
    while start != -1:
        try:
            obj = json.loads(text[start:text.rfind("}") + 1])
            return obj if isinstance(obj, dict) else None
        except ValueError:
            start = text.rfind("{\"", 0, start)
    return None


def offset_deps(tasks: Sequence[Task], base: int) -> None:
    """제안 안의 '#i' 의존을 plan.json 에 이어 붙일 위치(base+i)로 옮긴다. 발급된 id 참조는 그대로."""
    for t in tasks:
        t.depends_on = ["#%d" % (base + int(d[1:])) if d.startswith("#") and d[1:].isdigit() else d for d in t.depends_on]


def plan_state_summary(tasks: Sequence[Task], states: Dict[str, "TaskState"]) -> str:
    """제안 프롬프트용 — 계획의 각 작업을 상태와 함께 한 줄씩 (모델은 이걸 보고 겹치지 않는 다음 일을 고른다)."""
    if not tasks:
        return "(계획 비어 있음)"
    out = []
    for t in tasks:
        st = states.get(t.id) if t.id else None
        out.append("- %s [%s] %s — 검증기 `%s`" % (t.id or "#?", st.state if st else "pending", t.title, t.verify_cmd[:90]))
    return "\n".join(out)


def read_proposed(repo: Repo) -> Tuple[Dict[str, Any], List[Task]]:
    if not repo.proposed.exists():
        return {}, []
    try:
        data = json.loads(repo.proposed.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise HarnessError("%s 파싱 실패: %s" % (PROPOSED_NAME, e))
    tasks = [_task_from_json(t) for t in (data.get("tasks") or []) if isinstance(t, dict)]
    return {k: v for k, v in data.items() if k != "tasks"}, tasks


def accept_proposed(repo: Repo, domain: Domain, events: Sequence[Dict[str, Any]], picks: Optional[Sequence[int]] = None) -> List[Task]:
    """제안 → plan.json. picks 는 제안 목록의 인덱스(None = 전부). id 는 여기서 발급(I1: 모델이 아니라 러너가), 계획 검증 통과 못 하면 아무것도 안 바꾼다."""
    pmeta, proposed = read_proposed(repo)
    if not proposed:
        raise HarnessError("받아들일 제안이 없다 (%s)" % PROPOSED_NAME)
    chosen_idx = list(range(len(proposed))) if picks is None else [int(i) for i in picks]
    bad = [i for i in chosen_idx if not (0 <= i < len(proposed))]
    if bad:
        raise HarnessError("제안 인덱스 범위 밖: %s (0~%d)" % (bad, len(proposed) - 1))
    chosen = [proposed[i] for i in chosen_idx]
    for t in chosen:  # 부분 수락 시 '#i' 가 빠진 작업을 가리키면 반려
        for d in t.depends_on:
            if d.startswith("#") and d[1:].isdigit() and int(d[1:]) not in chosen_idx:
                raise HarnessError("%s 의 의존 %s 가 수락 목록에 없다" % (t.title, d))
    remap = {"#%d" % old: "#%d" % new for new, old in enumerate(chosen_idx)}
    for t in chosen:
        t.depends_on = [remap.get(d, d) for d in t.depends_on]
        t.id = None
        t.origin = "proposal"
    meta, tasks = load_plan(repo)
    offset_deps(chosen, len(tasks))
    merged = list(tasks) + chosen
    errors = validate_plan(merged, domain)
    if errors:
        raise HarnessError("제안이 계획 검증을 통과하지 못했다:\n - " + "\n - ".join(errors))
    assign_ids(merged, events)
    save_plan(repo, meta, merged)
    rest = [t for i, t in enumerate(proposed) if i not in chosen_idx]
    if rest:
        data = dict(pmeta)
        data["tasks"] = [t.to_json() for t in rest]
        repo.proposed.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        repo.proposed.unlink()
    return chosen


def validate_plan(tasks: Sequence[Task], domain: Domain) -> List[str]:
    """접수 게이트. 빈 리스트 = 통과. I5(검증기 필수) · 리프 5~30분 · 의존성 · 순환 · ID 형식."""
    errors: List[str] = []
    ids = [t.id for t in tasks if t.id]
    for tid in ids:
        if not ID_RE.match(tid):
            errors.append("%s: id 형식은 task-NNN" % tid)
    dupes = {i for i in ids if ids.count(i) > 1}
    for d in sorted(dupes):
        errors.append("%s: id 중복" % d)
    known = set(ids) | {"#%d" % i for i in range(len(tasks))}
    for i, t in enumerate(tasks):
        label = t.id or "#%d" % i
        if not t.title:
            errors.append("%s: title 없음" % label)
        if not t.goal:
            errors.append("%s: goal 없음" % label)
        if not t.verify_cmd:
            errors.append("%s: verify 없음 — 검증기 없는 작업은 큐에 못 들어간다 (I5)" % label)
        lo = 0 if t.is_gate else (domain.leaf_min if t.origin != "repair" else 1)  # 게이트는 모델 시간을 쓰지 않는다
        if not (lo <= t.estimate_minutes <= domain.leaf_max):
            errors.append("%s: estimate_minutes=%s, 리프는 %d~%d분" % (label, t.estimate_minutes, lo, domain.leaf_max))
        for d in t.depends_on:
            if d not in known:
                errors.append("%s: depends_on '%s' 가 계획에 없다" % (label, d))
            if d == t.id or d == "#%d" % i:
                errors.append("%s: 자기 자신에 의존" % label)
    # 순환
    index = {t.id: i for i, t in enumerate(tasks) if t.id}
    index.update({"#%d" % i: i for i in range(len(tasks))})
    color = [0] * len(tasks)

    def dfs(i: int) -> bool:
        color[i] = 1
        for d in tasks[i].depends_on:
            j = index.get(d)
            if j is None:
                continue
            if color[j] == 1:
                return True
            if color[j] == 0 and dfs(j):
                return True
        color[i] = 2
        return False

    for i in range(len(tasks)):
        if color[i] == 0 and dfs(i):
            errors.append("depends_on 순환 (%s 포함)" % (tasks[i].id or "#%d" % i))
            break
    return errors


# ────────────────────────────────────────────────────────────── P1 ID 발급 (로그 ∪ 계획의 최댓값 + 1)

def _id_num(s: Any, kind: str) -> int:
    m = ID_RE.match(str(s or ""))
    return int(m.group(2)) if m and m.group(1) == kind else 0


def max_id(kind: str, events: Sequence[Dict[str, Any]], tasks: Sequence[Task] = ()) -> int:
    m = 0
    for ev in events:
        m = max(m, _id_num(ev.get(kind), kind))
    if kind == "task":
        for t in tasks:
            m = max(m, _id_num(t.id, "task"))
    return m


def next_id(kind: str, events: Sequence[Dict[str, Any]], tasks: Sequence[Task] = ()) -> str:
    if kind not in ("night", "task"):
        raise HarnessError("kind는 night|task")
    return "%s-%03d" % (kind, max_id(kind, events, tasks) + 1)


def assign_ids(tasks: Sequence[Task], events: Sequence[Dict[str, Any]]) -> List[Task]:
    """id 없는 작업에 발급하고, depends_on의 '#N' 인덱스 참조를 id로 바꾼다. 발급된 작업 목록을 돌려준다."""
    assigned: List[Task] = []
    n = max_id("task", events, tasks)
    for t in tasks:
        if not t.id:
            n += 1
            t.id = "task-%03d" % n
            assigned.append(t)
    for t in tasks:
        fixed = []
        for d in t.depends_on:
            if d.startswith("#") and d[1:].isdigit() and int(d[1:]) < len(tasks):
                fixed.append(tasks[int(d[1:])].id or d)
            else:
                fixed.append(d)
        t.depends_on = fixed
    return assigned


# ────────────────────────────────────────────────────────────── 상태 파생 (I3: 로그의 fold)

@dataclass
class TaskState:
    id: str
    state: str = "pending"        # pending | started | failed | passed | blocked
    attempts: int = 0
    failures: int = 0
    enqueued_at: Optional[str] = None
    started_at: Optional[str] = None
    last_night: Optional[str] = None
    last_failure: Optional[Dict[str, Any]] = None
    failure_history: List[Dict[str, Any]] = field(default_factory=list)
    last_model: Optional[Dict[str, Any]] = None
    commit: Optional[str] = None
    blocked_reason: Optional[str] = None
    approved_at: Optional[str] = None                        # 게이트 승인 시각 (task_approved)


def derive_states(events: Sequence[Dict[str, Any]], tasks: Sequence[Task]) -> Dict[str, TaskState]:
    states: Dict[str, TaskState] = {t.id: TaskState(id=t.id) for t in tasks if t.id}
    for t in tasks:
        if t.id and t.is_gate:
            states[t.id].state = "gate"  # 사람이 열기 전까지 — 모델 자격 없음, 의존 작업도 막힘
    for ev in events:
        tid = ev.get("task")
        if not tid:
            continue
        st = states.get(tid)
        if st is None:
            st = states[tid] = TaskState(id=tid)
        e = ev.get("event")
        if e == "task_enqueued":
            st.enqueued_at = st.enqueued_at or ev.get("ts")
        elif e == "task_started":
            st.attempts += 1
            st.state = "started"
            st.started_at = ev.get("ts")
            st.last_night = ev.get("night")
        elif e == "model_done":
            st.last_model = ev
        elif e == "task_failed":
            if not ev.get("infra"):  # 머신 잠듦·드라이버 무응답은 작업의 실패가 아니다 — 시도 횟수를 먹지 않는다
                st.failures += 1
            st.state = "failed"
            st.last_failure = ev
            st.failure_history.append(ev)
        elif e == "task_approved":  # 사람이 게이트를 연다 (runner/queue approve). 승인 = 게이트의 검증 통과
            st.state = "passed"
            st.approved_at = ev.get("ts")
        elif e == "task_unblocked":  # 사람이 푼다 (runner/queue unblock). 로그는 append-only 이므로 이벤트로 남긴다
            st.state = "pending"
            st.failures = 0
            st.blocked_reason = None
        elif e == "task_passed":
            st.state = "passed"
            st.commit = ev.get("commit")
        elif e == "task_blocked":
            st.state = "blocked"
            st.blocked_reason = ev.get("reason")
    return states


def gate_openable(t: Task, states: Dict[str, TaskState]) -> bool:
    """게이트를 지금 열 수 있나 — 의존 작업이 전부 통과했을 때만. 선행 작업이 남은 게이트는 SUMMARY '뒤에 올 게이트' 로 따로 보이고
    `queue approve` 가 거부한다 (게이트는 검문소다 — 순서를 건너뛰어 열면 검문이 아니다, 2026-08-30)."""
    return all((states.get(d) or TaskState(id=d)).state == "passed" for d in t.depends_on)


def dangling_started(states: Dict[str, TaskState]) -> List[TaskState]:
    """판정 없이 끝난 시도 (지난 밤이 죽은 경우). 러너가 밤 시작에 task_failed(interrupted)로 닫는다."""
    return [st for st in states.values() if st.state == "started"]


# ────────────────────────────────────────────────────────────── P2 작업 선택

def domain_rank(task: Task, st: TaskState) -> Tuple[Any, ...]:
    """P2의 '도메인 점수' — 아사 상태가 아닌 자격 작업들 사이의 정렬 키 (작을수록 먼저).

    TODO(jun): 여기가 사용자가 결정할 지점이다. 아사 방지는 select_next()가 프로그램으로 강제하고,
    이 함수는 그 *다음* 순서만 정한다. 5~10줄로 정책을 적어라. 고려할 축:
      - task.priority      계획이 준 우선순위 (클수록 중요)
      - st.failures        실패한 작업을 바로 재시도할지(정보가 신선함) / 뒤로 보낼지(doom loop 회피)
      - 의존 팬아웃         이 작업이 풀리면 자격을 얻는 작업 수 (병목 먼저)
      - task.estimate_minutes  짧은 것부터(완료 수 최대화) vs 긴 것부터(밤 초반의 큰 컨텍스트 활용)
    기본값: priority 내림차순 → 실패 적은 순 → 먼저 들어온 순 → id.
    ASSUMPTIONS: P2 도메인 점수 (Claude 5 · C)
    """
    return (-task.priority, st.failures, st.enqueued_at or "", task.id or "")


def eligible(tasks: Sequence[Task], states: Dict[str, TaskState], domain: Domain,
             remaining_minutes: Optional[float] = None) -> List[Task]:
    """자격: 미완 · 미차단 · 시도 여유 · 의존성 충족 · 남은 예산에 들어감."""
    out = []
    for t in tasks:
        if not t.id:
            continue
        st = states.get(t.id) or TaskState(id=t.id)
        if st.state in ("passed", "blocked", "started", "gate"):
            continue
        if st.failures >= domain.max_attempts:
            continue
        if any((states.get(d) or TaskState(id=d)).state != "passed" for d in t.depends_on):
            continue
        if remaining_minutes is not None and t.estimate_minutes > remaining_minutes:
            continue
        out.append(t)
    return out


def waited_minutes(st: TaskState, now_dt: datetime) -> float:
    if not st.enqueued_at:
        return 0.0
    try:
        return (now_dt - parse_iso(st.enqueued_at)).total_seconds() / 60.0
    except ValueError:
        return 0.0


def rank(tasks: Sequence[Task], states: Dict[str, TaskState], domain: Domain,
         now_dt: Optional[datetime] = None, remaining_minutes: Optional[float] = None) -> List[Task]:
    """P2 전체 순서. 1) 복구 작업 2) 아사 작업(오래 기다린 순) 3) domain_rank.
    ASSUMPTIONS: P2 아사 방지 (개인 경험 · D) — 점수 기반 선택은 낮은 점수 항목을 영원히 굶긴다.
    """
    now_dt = now_dt or now()
    el = eligible(tasks, states, domain, remaining_minutes)
    if not el:
        return []
    repair = [t for t in el if t.origin == "repair"]
    if repair:
        return sorted(repair, key=lambda t: t.id or "")
    st_of = lambda t: states.get(t.id) or TaskState(id=t.id)  # noqa: E731
    starving = [t for t in el if waited_minutes(st_of(t), now_dt) > domain.starvation_minutes]
    rest = [t for t in el if t not in starving]
    starving.sort(key=lambda t: (st_of(t).enqueued_at or "", t.id or ""))
    rest.sort(key=lambda t: domain_rank(t, st_of(t)))
    return starving + rest


def select_next(tasks: Sequence[Task], states: Dict[str, TaskState], domain: Domain,
                now_dt: Optional[datetime] = None, remaining_minutes: Optional[float] = None) -> Optional[Task]:
    order = rank(tasks, states, domain, now_dt, remaining_minutes)
    return order[0] if order else None


# ────────────────────────────────────────────────────────────── 프로세스 실행 (타임아웃 = 프로세스 그룹 kill; macOS에 timeout 없음)

def _group_members(pgid: int) -> List[int]:
    """프로세스 그룹의 살아 있는 pid 들 (자기 자신 제외). `ps -A -o pid= -o pgid=` 는 BSD·procps 공통."""
    try:
        p = subprocess.run(["ps", "-A", "-o", "pid=", "-o", "pgid="], capture_output=True, text=True, encoding="utf-8", errors="replace")
    except OSError:
        return []
    out: List[int] = []
    for ln in p.stdout.splitlines():
        parts = ln.split()
        if len(parts) >= 2 and parts[1].isdigit() and int(parts[1]) == pgid and parts[0].isdigit() and int(parts[0]) != os.getpid():
            out.append(int(parts[0]))
    return out


def _signal_group(proc: subprocess.Popen, sig: int) -> None:
    """그룹 전체 + 리더 pid. killpg 가 ESRCH 면(리더가 아직 setsid 전이거나 이미 죽음) pid 로 직접 — 조용히 돌아가지 않는다."""
    try:
        os.killpg(proc.pid, sig)
    except (ProcessLookupError, PermissionError):
        try:
            os.kill(proc.pid, sig)
        except (ProcessLookupError, PermissionError):
            pass
    for pid in _group_members(proc.pid):  # fork 직후라 killpg 를 놓친 손자 — findings/006 실측 1/30
        try:
            os.kill(pid, sig)
        except (ProcessLookupError, PermissionError):
            pass


def kill_group(proc: subprocess.Popen, grace: float = 10.0) -> None:
    """SIGTERM → grace 초 → SIGKILL, 그룹 잔존 프로세스까지 훑는다. findings/006: killpg 한 번은 fork 직후의 손자를 놓쳐(1/30)
    `sleep 60` 이 파이프를 잡은 채 살아남았다 — 카나리아 '즉시 중단' 약속이 60초 지연되던 원인."""
    if proc.poll() is not None and not _group_members(proc.pid):
        return
    _signal_group(proc, signal.SIGTERM)
    deadline = time.monotonic() + max(0.0, grace)
    while time.monotonic() < deadline:
        if proc.poll() is not None and not _group_members(proc.pid):
            return
        time.sleep(0.05)
    _signal_group(proc, signal.SIGKILL)
    time.sleep(0.05)
    _signal_group(proc, signal.SIGKILL)  # 첫 SIGKILL 과 동시에 fork 된 것까지


def run_shell(cmd: str, cwd: Union[str, Path], timeout_sec: float,
              env: Optional[Dict[str, str]] = None, stdin_text: Optional[str] = None) -> Tuple[int, str, float, bool]:
    """(exit, combined output, seconds, timed_out). stdin은 닫는다 (없으면 hang하는 CLI가 있다)."""
    start = time.time()
    proc = subprocess.Popen(
        ["sh", "-c", cmd], cwd=str(cwd),
        stdin=subprocess.PIPE if stdin_text is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        env=env, start_new_session=True,
    )
    timed_out = False
    try:
        out, _ = proc.communicate(input=stdin_text.encode("utf-8") if stdin_text is not None else None,
                                  timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        kill_group(proc)
        try:
            out, _ = proc.communicate(timeout=5)  # 이미 죽였다 — 잔여 출력만 최선노력으로 회수, 파이프를 잡은 손자가 있어도 매달리지 않는다
        except subprocess.TimeoutExpired:
            out = b""
        timed_out = True
    except BaseException:
        kill_group(proc)
        raise
    return proc.returncode, (out or b"").decode("utf-8", "replace"), time.time() - start, timed_out


# ────────────────────────────────────────────────────────────── P6 판정 (검증기)

@dataclass
class VerifyResult:
    ok: bool
    exit: int
    seconds: float
    tail: str
    timed_out: bool
    cmd: str
    metric: Optional[float] = None
    reason: str = ""


def normalize_verify(spec: Any) -> Tuple[str, Optional[Dict[str, Any]]]:
    """문자열(레벨 0) 또는 {"cmd", "metric": {"min"|"max"}} (레벨 1)."""
    if isinstance(spec, str):
        return spec.strip(), None
    if isinstance(spec, dict):
        m = spec.get("metric")
        return str(spec.get("cmd") or "").strip(), (m if isinstance(m, dict) else None)
    return "", None


def _last_float(text: str) -> Optional[float]:
    for line in reversed(text.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            return float(line.split()[-1])
        except ValueError:
            return None
    return None


def run_verify(repo: Repo, spec: Any, timeout_sec: float, env: Optional[Dict[str, str]] = None) -> VerifyResult:
    """모델의 'done'과 무관하게 검증기를 돌려 판정한다. ASSUMPTIONS: P6 (Claude 5 · B)."""
    cmd, metric = normalize_verify(spec)
    if not cmd:
        return VerifyResult(False, -1, 0.0, "", False, "", None, "검증기 없음")
    code, out, secs, to = run_shell(cmd, repo.root, timeout_sec, env)
    ok = (code == 0) and not to
    reason = "timeout %ss" % int(timeout_sec) if to else ("exit %d" % code if code else "")
    m: Optional[float] = None
    if metric is not None and ok:
        m = _last_float(out)
        lo, hi = metric.get("min"), metric.get("max")
        if m is None:
            ok, reason = False, "metric: 마지막 줄이 숫자가 아니다"
        elif lo is not None and m < float(lo):
            ok, reason = False, "metric %s < min %s" % (m, lo)
        elif hi is not None and m > float(hi):
            ok, reason = False, "metric %s > max %s" % (m, hi)
    return VerifyResult(ok, code, secs, tail(out), to, cmd, m, reason)


# ────────────────────────────────────────────────────────────── git (러너 전용 커밋 경로 — spec §6)

EXCLUDE_HDIR = ":(exclude)" + HDIR_NAME


class Git:
    def __init__(self, root: Union[str, Path]):
        self.root = Path(root)

    def run(self, *args: str, check: bool = True) -> str:
        p = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if check and p.returncode != 0:
            raise HarnessError("git %s: %s" % (" ".join(args), (p.stderr or p.stdout).strip()))
        return p.stdout.strip()

    def is_repo(self) -> bool:
        p = subprocess.run(["git", "-C", str(self.root), "rev-parse", "--show-toplevel"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        return p.returncode == 0 and Path(p.stdout.strip()).resolve() == self.root.resolve()

    def is_clean(self) -> bool:
        return self.run("status", "--porcelain") == ""

    def head(self) -> str:
        return self.run("rev-parse", "--short", "HEAD")

    def branch(self) -> str:
        return self.run("rev-parse", "--abbrev-ref", "HEAD")

    def branch_exists(self, name: str) -> bool:
        return subprocess.run(["git", "-C", str(self.root), "rev-parse", "--verify", "--quiet", "refs/heads/" + name],
                              capture_output=True).returncode == 0

    def is_ancestor(self, a: str, b: str) -> bool:
        return subprocess.run(["git", "-C", str(self.root), "merge-base", "--is-ancestor", a, b],
                              capture_output=True).returncode == 0

    def checkout(self, ref: str) -> None:
        self.run("checkout", "-q", ref)

    def create_branch(self, name: str, base: str = "HEAD") -> None:
        self.run("checkout", "-q", "-b", name, base)

    def night_branches(self) -> List[Tuple[int, str]]:
        out = self.run("for-each-ref", "--format=%(refname:short)", "refs/heads/" + NIGHT_BRANCH_PREFIX)
        found = []
        for name in out.splitlines():
            m = ID_RE.match(name[len(NIGHT_BRANCH_PREFIX):])
            if m and m.group(1) == "night":
                found.append((int(m.group(2)), name))
        return sorted(found)

    def commit_all(self, message: str) -> Optional[str]:
        """전체 add + commit. 변경이 없으면 None. push는 절대 하지 않는다."""
        self.run("add", "-A", "--", ".")
        if subprocess.run(["git", "-C", str(self.root), "diff", "--cached", "--quiet"]).returncode == 0:
            return None
        self.run("commit", "-q", "-m", message)
        return self.head()

    def commit_harness(self, message: str) -> Optional[str]:
        """.harness/ 만 add + commit (SUMMARY·BLOCKED·log). 밤이 이상 종료해 트리가 더러워도 모델의 편집을 부기 커밋에 섞지 않는다 (I8)."""
        p = subprocess.run(["git", "-C", str(self.root), "status", "--porcelain", "--", HDIR_NAME],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if not p.stdout.strip():
            return None
        self.run("add", "-A", "--", HDIR_NAME)
        self.run("commit", "-q", "-m", message, "--", HDIR_NAME)
        return self.head()

    def save_patch(self, path: Path) -> bool:
        """실패 시도의 diff(.harness 제외, 새 파일 포함)를 path에 남긴다. I4: 실패 흔적은 지우지 않는다."""
        self.run("add", "-A", "--", ".", EXCLUDE_HDIR)
        diff = self.run("diff", "--cached", "--binary", "HEAD", "--", ".", EXCLUDE_HDIR)
        self.run("reset", "-q", "--", ".", EXCLUDE_HDIR)
        if not diff.strip():
            return False
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(diff + "\n", encoding="utf-8")
        return True

    def revert_worktree(self) -> None:
        """작업 트리를 HEAD로 되돌린다. .harness/는 건드리지 않는다 (로그 보존).
        ASSUMPTIONS: 실패 시도 되돌리기 (Claude 5 · C)."""
        self.run("reset", "-q", "--", ".", EXCLUDE_HDIR)
        self.run("checkout", "-q", "--", ".", EXCLUDE_HDIR)
        self.run("clean", "-fdq", "--", ".", EXCLUDE_HDIR)

    def changed_paths(self) -> List[str]:
        """작업 트리의 변경 경로 (추적 변경 + 미추적, ignore 제외). 이름 변경은 새 경로만."""
        # run() 은 stdout 을 strip 하므로 쓰지 않는다 — porcelain 첫 항목의 선행 공백(' M path')이 잘린다
        p = subprocess.run(["git", "-C", str(self.root), "status", "--porcelain", "-z", "--untracked-files=all"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if p.returncode != 0:
            raise HarnessError("git status: %s" % p.stderr.strip())
        fields = p.stdout.split("\0")
        paths: List[str] = []
        i = 0
        while i < len(fields):
            f = fields[i]
            i += 1
            if len(f) < 4:
                continue
            paths.append(f[3:])
            if f[0] in ("R", "C"):  # 다음 필드는 원래 경로
                i += 1
        return paths

    def log_oneline(self, n: int = 5) -> str:
        return self.run("log", "--oneline", "-n", str(n), check=False)


# ────────────────────────────────────────────────────────────── P10 아침 산출물 (로그에서만 생성)

def day_cost_usd(events: Sequence[Dict[str, Any]], now_dt: Optional[datetime] = None) -> float:
    """오늘(로컬 자정 이후) 모델 비용 — model_done + plan_proposed 의 cost_usd 합. 상태 파일 없이 로그에서 파생한다 (I3).
    일일 상한(budget.max_day_usd)은 밤·루프 상한과 달리 밤을 다시 띄워도 리셋되지 않는다 (2026-08-29 하루 $68 실측)."""
    now_dt = now_dt or now()
    day_start = now_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    total = 0.0
    for e in events:
        if e.get("event") not in ("model_done", "plan_proposed"):
            continue
        try:
            ts = parse_iso(str(e.get("ts") or ""))
        except ValueError:
            continue
        if ts >= day_start:
            total += float(e.get("cost_usd") or 0)
    return total


def events_for_night(events: Sequence[Dict[str, Any]], night_id: str) -> List[Dict[str, Any]]:
    return [e for e in events if e.get("night") == night_id]


def latest_night_id(events: Sequence[Dict[str, Any]]) -> Optional[str]:
    n = max_id("night", events)
    return "night-%03d" % n if n else None


def collect_night(events: Sequence[Dict[str, Any]], tasks: Sequence[Task], domain: Domain,
                  night_id: str) -> Dict[str, Any]:
    ne = events_for_night(events, night_id)
    states = derive_states(events, tasks)
    by_id = {t.id: t for t in tasks if t.id}
    started = next((e for e in ne if e.get("event") == "night_started"), None)
    ended = next((e for e in reversed(ne) if e.get("event") == "night_ended"), None)
    passed = [e for e in ne if e.get("event") == "task_passed"]
    blocked = [e for e in ne if e.get("event") == "task_blocked"]
    failed_ids: List[str] = []
    for e in ne:
        if e.get("event") == "task_failed" and e["task"] not in failed_ids:
            failed_ids.append(e["task"])
    done_ids = {e["task"] for e in passed} | {e["task"] for e in blocked}
    retry_ids = [t for t in failed_ids if t not in done_ids]
    pending = [t for t in tasks if t.id and states[t.id].state == "pending"]
    cost = sum(float(e.get("cost_usd") or 0) for e in ne if e.get("event") == "model_done")
    anomalies: List[str] = []
    slept_total = 0.0
    for e in ne:
        if e.get("event") != "model_done":
            continue
        for f, n in sorted((e.get("edits") or {}).items(), key=lambda kv: -kv[1]):
            if n >= DOOM_EDIT_THRESHOLD:
                anomalies.append("doom loop 의심: %s 같은 파일 %d회 편집 (%s)" % (e["task"], n, f))
        turns = int(e.get("turns") or 0)
        if e.get("hooks_dead"):
            anomalies.append("훅 미로드: %s (시도 %s) — 카나리아 없음, 쓰기 중재·trifecta 가드가 없는 세션이라 즉시 중단했다. --plugin-dir 경로와 플러그인 로딩을 확인하라" % (
                e["task"], e.get("attempt")))
        elif e.get("slept_seconds"):
            slept_total += float(e["slept_seconds"])
            anomalies.append("머신 잠듦 %s: %s (시도 %s) — caffeinate 는 유휴 잠자기만 막는다. 뚜껑을 열어두거나 서버에서 돌린다" % (
                fmt_duration(float(e["slept_seconds"])), e["task"], e.get("attempt")))
        elif e.get("timed_out"):
            anomalies.append("모델 시간 초과: %s (시도 %s, %d턴, $%.2f)%s" % (
                e["task"], e.get("attempt"), turns, float(e.get("cost_usd") or 0), " — 0턴 = 무응답" if turns == 0 else " — 느림, 상한을 올리거나 작업을 쪼갠다"))
        elif e.get("error"):
            anomalies.append("드라이버 오류: %s (시도 %s) — %s" % (e["task"], e.get("attempt"), str(e["error"])[:120]))
        if e.get("denials"):
            anomalies.append("훅 거부 %d회: %s (시도 %s)" % (int(e["denials"]), e["task"], e.get("attempt")))
        if int(e.get("hook_fires") or 0) > 1:
            anomalies.append("훅 이중 발화 %d회: %s (시도 %s) — 전역 플러그인 설치와 --plugin-dir 주입이 겹쳤는지 확인 (배송 결정)" % (
                int(e["hook_fires"]), e["task"], e.get("attempt")))
    rl = max((float(e.get("rate_limit") or 0) for e in ne if e.get("event") == "model_done"), default=0.0)
    if rl >= 0.5:
        anomalies.append("5시간 창 사용률 최대 %d%% — 다음 밤 창이 겹치면 느려진다" % round(rl * 100))
    for e in ne:
        if e.get("event") == "scope_violation":
            anomalies.append("쓰기 범위 위반: %s (시도 %s) — %s" % (e["task"], e.get("attempt"), ", ".join(e.get("paths") or [])[:120]))
    smoke = next((e for e in ne if e.get("event") == "smoke"), None)
    if smoke and not smoke.get("ok"):
        anomalies.append("밤 시작 스모크 실패 (복구 작업 발급)")
    skills: Dict[str, Dict[str, Any]] = {}  # 모델이 스스로 부른 스킬 — 호출은 지침(설명문 매칭)이라 확률적, 실사용률은 여기서만 보인다 (findings/004)
    for e in ne:
        if e.get("event") != "model_done":
            continue
        for sk, n in (e.get("skills") or {}).items():
            d = skills.setdefault(str(sk), {"count": 0, "tasks": []})
            d["count"] += int(n or 0)
            if e.get("task") not in d["tasks"]:
                d["tasks"].append(e.get("task"))
    end_dt = parse_iso(ended["ts"]) if ended else now()
    next_tasks = rank(tasks, states, domain, now_dt=end_dt)[:3]
    return {
        "night": night_id, "started": started, "ended": ended, "states": states, "by_id": by_id,
        "passed": passed, "blocked": blocked, "retry_ids": retry_ids, "pending": pending,
        "cost": cost, "anomalies": anomalies, "next": next_tasks, "events": ne, "skills": skills,
    }


def _title(by_id: Dict[str, Task], tid: str) -> str:
    t = by_id.get(tid)
    return t.title if t else "(계획에 없음)"


_ERROR_LINE = re.compile(r"error|traceback|assert|fail|exception|not found", re.IGNORECASE)


def _error_line(text: Optional[str]) -> str:
    """검증 출력에서 사람이 읽을 한 줄 — 오류처럼 보이는 첫 줄, 없으면 마지막 줄 (findings/003: '마지막 오류: 0')."""
    lines = [re.sub(r"\x1b\[[0-9;]*m", "", ln).strip() for ln in (text or "").splitlines()]
    lines = [ln for ln in lines if ln]
    if not lines:
        return "(출력 없음)"
    for ln in lines:
        if _ERROR_LINE.search(ln):
            return ln[:160]
    return lines[-1][:160]


DAG_BADGE = {"passed": "✅", "blocked": "⛔", "failed": "🔁", "started": "🏃", "pending": "⬜", "gate": "🔒"}


def _dag_node(tid: Any) -> str:
    """mermaid 노드 id — 영숫자만 남긴다 (하이픈은 파서가 엣지로 오독할 수 있다)."""
    s = re.sub(r"[^0-9A-Za-z]", "", str(tid)) or "x"
    return s if s[0].isalpha() else "n" + s


def render_plan_dag(tasks: Sequence[Task], states: Dict[str, TaskState]) -> str:
    """계획 DAG를 mermaid로 (G2 aggregated) — 막힌 작업이 무엇을 물고 있는지 아침에 그림으로 보인다.
    렌더는 러너가 plan.json+상태에서 결정론적으로 한다 (부기는 프로그램 — 모델이 그리지 않는다).
    Obsidian·GitHub가 네이티브 렌더. expanded(log 언롤) 모드는 다음."""
    ids = sorted(t.id for t in tasks if t.id)
    if not ids:
        return ""
    by_id = {t.id: t for t in tasks if t.id}
    lines = ["```mermaid", "flowchart TD"]
    for tid in ids:
        t = by_id[tid]
        st = states.get(tid) or TaskState(id=tid)
        title = re.sub(r'["\[\]{}()<>`|#;]', "", t.title).strip()[:40]
        lines.append('  %s["%s %s %s"]' % (_dag_node(tid), DAG_BADGE.get(st.state, "⬜"), tid, title))
    for tid in ids:
        for dep in by_id[tid].depends_on:
            if dep in by_id:
                lines.append("  %s --> %s" % (_dag_node(dep), _dag_node(tid)))
    lines.append("```")
    return "\n".join(lines)


def render_summary(c: Dict[str, Any]) -> str:
    started, ended = c["started"], c["ended"]
    s_ts = started.get("ts") if started else None
    e_ts = ended.get("ts") if ended else None
    dur = fmt_duration((parse_iso(e_ts) - parse_iso(s_ts)).total_seconds()) if s_ts and e_ts else "진행 중"
    by_id, states = c["by_id"], c["states"]
    reason = {"budget": "예산 소진", "queue_empty": "큐 비움", "max_tasks": "작업 수 상한", "interrupted": "중단됨",
              "smoke_unrepairable": "스모크 복구 실패", "bootstrap_failed": "부트스트랩 실패",
              "machine_slept": "머신이 잠듦 (밤 중단)", "driver_unhealthy": "드라이버 무응답 연속 (밤 중단)",
              "cost_budget": "비용 상한 도달", "cost_day": "일일 비용 상한 도달", "rate_limited": "5시간 창 사용률 상한 도달",
              "hooks_dead": "훅 미로드 (밤 중단)"}.get(
        (ended or {}).get("reason", ""), (ended or {}).get("reason", "진행 중"))
    branch = (started or {}).get("branch", "?")
    out = ["# %s · %s → %s (%s)" % (c["night"], fmt_clock(s_ts), fmt_clock(e_ts), dur), ""]
    out += ["## 결론",
            "완료 %d / 실패(재시도 예정) %d / 막힘 %d / 미착수 %d · 종료: %s · 브랜치 `%s` · 비용 $%.2f" % (
                len(c["passed"]), len(c["retry_ids"]), len(c["blocked"]), len(c["pending"]), reason, branch, c["cost"]), ""]
    dag = render_plan_dag(list(by_id.values()), states)
    if dag:
        out += ["## 계획 DAG (✅통과 ⛔막힘 🔁재시도 ⬜미착수)", dag, ""]
    out += ["## 완료 (검증 통과)"]
    if c["passed"]:
        for e in c["passed"]:
            st = states.get(e["task"])
            secs = (st.last_model or {}).get("seconds") if st else None
            out.append("- %s %s — 커밋 `%s` (시도 %s%s)" % (
                e["task"], _title(by_id, e["task"]), e.get("commit", "?"), e.get("attempt", "?"),
                ", %s" % fmt_duration(secs) if secs else ""))
    else:
        out.append("- (없음)")
    out += ["", "## 막힘 — BLOCKED.md 참조"]
    if c["blocked"]:
        for e in c["blocked"]:
            st = states.get(e["task"])
            lf = st.last_failure if st else None
            out.append("- %s %s — %s. 마지막 시도: %s · `%s`" % (
                e["task"], _title(by_id, e["task"]), e.get("reason", "?"), (lf or {}).get("reason", "?"), _error_line((lf or {}).get("tail"))))
    else:
        out.append("- (없음)")
    out += ["", "## 실패 (다음 밤 재시도)"]
    if c["retry_ids"]:
        for tid in c["retry_ids"]:
            st = states[tid]
            lf = st.last_failure or {}
            out.append("- %s %s — %d회 실패 (%s: %s)" % (tid, _title(by_id, tid), st.failures, lf.get("stage", "?"), lf.get("reason", "?")))
    else:
        out.append("- (없음)")
    gates = [t for t in by_id.values() if t.id and t.is_gate and (states.get(t.id) or TaskState(id=t.id)).state == "gate"]
    now_gates = [t for t in gates if gate_openable(t, states)]
    later_gates = [t for t in gates if not gate_openable(t, states)]
    if now_gates:
        out += ["", "## 승인 대기 — 지금 열 수 있다 (`runner/queue approve task-NNN`, 대화형에서는 '승인'·'시작해'·'진행해')"]
        for t in now_gates:
            waiting = [d.id for d in by_id.values() if t.id in d.depends_on]
            out.append("- %s %s%s" % (t.id, t.title, (" — 뒤에 %s" % ", ".join(map(str, waiting))) if waiting else ""))
    if later_gates:  # 선행 작업이 남은 게이트는 아침 목록을 어지럽히지 않게 따로 — 다이제스트는 위 절만 센다
        out += ["", "## 뒤에 올 게이트 (선행 작업이 끝나야 열린다)"]
        for t in later_gates:
            pending = [d for d in t.depends_on if (states.get(d) or TaskState(id=d)).state != "passed"]
            out.append("- %s %s — 앞에 %s" % (t.id, t.title, ", ".join(pending)))
    out += ["", "## 다음 밤에 할 것 (P2가 선택)"]
    if c["next"]:
        for i, t in enumerate(c["next"], 1):
            out.append("%d. %s %s (priority %d, %d분)" % (i, t.id, t.title, t.priority, t.estimate_minutes))
    else:
        out.append("- (자격 있는 작업 없음 — 계획을 다시 쓰거나 BLOCKED.md를 본다)")
    out += ["", "## 스킬 자동 호출 (모델이 스스로 부른 것 — 지침이지 강제가 아니다)"]
    if c.get("skills"):
        for sk, d in sorted(c["skills"].items(), key=lambda kv: (-kv[1]["count"], kv[0])):
            out.append("- %s ×%d — %s" % (sk, d["count"], ", ".join(str(t) for t in d["tasks"])))
    else:
        out.append("- (없음)")
    out += ["", "## 이상 징후"]
    out += ["- " + a for a in c["anomalies"]] or ["- (없음)"]
    out += ["", "## 병합", "검토 후 `git merge %s`. push는 러너가 하지 않았다. 로그: `.harness/log.jsonl` (append-only)." % branch, ""]
    return "\n".join(out)


def render_blocked(events: Sequence[Dict[str, Any]], tasks: Sequence[Task]) -> str:
    states = derive_states(events, tasks)
    by_id = {t.id: t for t in tasks if t.id}
    blocked = [st for st in states.values() if st.state == "blocked"]
    out = ["# BLOCKED — 막힌 작업 (로그에서 생성, 손으로 고치지 않는다)", ""]
    if not blocked:
        out.append("(없음)")
        return "\n".join(out) + "\n"
    for st in sorted(blocked, key=lambda s: s.id):
        t = by_id.get(st.id)
        out.append("## %s %s" % (st.id, t.title if t else "(계획에 없음)"))
        out.append("- 사유: %s · 시도 %d회" % (st.blocked_reason or "?", st.attempts))
        if t:
            out.append("- 목표: %s" % t.goal)
            out.append("- 검증기: `%s`" % t.verify_cmd)
        for f in st.failure_history:
            out.append("")
            out.append("### 시도 %s (%s) — %s: %s" % (f.get("attempt", "?"), f.get("night", "?"), f.get("stage", "?"), f.get("reason", "?")))
            if f.get("patch"):
                out.append("- 패치: `%s`" % f["patch"])
            tl = (f.get("tail") or "").strip()
            if tl:
                lines = tl.splitlines()[-30:]
                out.append("```")
                out.extend(lines)
                out.append("```")
        out.append("")
    return "\n".join(out) + "\n"


def write_morning_outputs(repo: Repo, night_id: str, domain: Optional[Domain] = None) -> Tuple[Path, Path]:
    """SUMMARY.md + BLOCKED.md. 입력은 로그와 계획뿐 — 러너 메모리에 있는 것은 쓰지 않는다 (재생성 가능성 보장)."""
    domain = domain or load_domain(repo)
    events = read_log(repo.log)
    _, tasks = load_plan(repo)
    c = collect_night(events, tasks, domain, night_id)
    repo.summary.write_text(render_summary(c), encoding="utf-8")
    repo.blocked.write_text(render_blocked(events, tasks), encoding="utf-8")
    return repo.summary, repo.blocked
