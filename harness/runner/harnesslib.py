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
import signal
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

HARNESS_ROOT = Path(__file__).resolve().parent.parent
HDIR_NAME = ".harness"
CONTRACT_FILES = ("spec.md", "verify", "init.sh", "domain.json", "plan.json")
BOOKKEEPING_OUTPUTS = ("log.jsonl", "SUMMARY.md", "BLOCKED.md")
ID_RE = re.compile(r"^(night|task)-(\d{3,})$")
NIGHT_BRANCH_PREFIX = "harness/"
TAIL_CHARS = 3000
# ASSUMPTIONS: P9 — 같은 파일을 이 횟수 이상 편집하면 doom loop 의심 (Claude 5 · B)
DOOM_EDIT_THRESHOLD = 8


class HarnessError(Exception):
    """계약 위반 / preflight 실패. 메시지는 사람이 읽는다."""


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
    "tools": [],
    "verify": {"cmd": ".harness/verify", "timeout_sec": 600, "smoke_timeout_sec": 120},
    "bootstrap": {"cmd": ".harness/init.sh", "timeout_sec": 600},
    "budget": {
        "hours": 8,
        "leaf_min_minutes": 5,     # 리프 하한 (spec §1)
        "leaf_max_minutes": 30,    # 리프 상한 = 작업당 모델 타임아웃 (ASSUMPTIONS: 30분 이상에서 일관성 상실)
        "max_attempts": 3,         # 이 횟수 실패하면 blocked (P8-lite)
        "starvation_minutes": 1440,  # 이보다 오래 기다린 작업은 무조건 먼저 (P2, 등급 D)
    },
    "driver": {"name": "claude", "model": None, "effort": None, "max_turns": 120, "max_budget_usd": None},
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
    def tools(self) -> List[Dict[str, Any]]:
        return list(self.raw.get("tools") or [])

    @property
    def verify_cmd(self) -> str:
        return str(self.raw["verify"]["cmd"])

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


def contract_missing(repo: Repo) -> List[str]:
    return [name for name in CONTRACT_FILES if not (repo.hdir / name).exists()]


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
        lo = domain.leaf_min if t.origin != "repair" else 1
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


def derive_states(events: Sequence[Dict[str, Any]], tasks: Sequence[Task]) -> Dict[str, TaskState]:
    states: Dict[str, TaskState] = {t.id: TaskState(id=t.id) for t in tasks if t.id}
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
            st.failures += 1
            st.state = "failed"
            st.last_failure = ev
            st.failure_history.append(ev)
        elif e == "task_passed":
            st.state = "passed"
            st.commit = ev.get("commit")
        elif e == "task_blocked":
            st.state = "blocked"
            st.blocked_reason = ev.get("reason")
    return states


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
        if st.state in ("passed", "blocked", "started"):
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

def kill_group(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        return
    for _ in range(100):
        if proc.poll() is not None:
            return
        time.sleep(0.1)
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


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
        out, _ = proc.communicate()
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
        p = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True)
        if check and p.returncode != 0:
            raise HarnessError("git %s: %s" % (" ".join(args), (p.stderr or p.stdout).strip()))
        return p.stdout.strip()

    def is_repo(self) -> bool:
        p = subprocess.run(["git", "-C", str(self.root), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
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

    def log_oneline(self, n: int = 5) -> str:
        return self.run("log", "--oneline", "-n", str(n), check=False)


# ────────────────────────────────────────────────────────────── P10 아침 산출물 (로그에서만 생성)

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
    for e in ne:
        if e.get("event") != "model_done":
            continue
        for f, n in sorted((e.get("edits") or {}).items(), key=lambda kv: -kv[1]):
            if n >= DOOM_EDIT_THRESHOLD:
                anomalies.append("doom loop 의심: %s 같은 파일 %d회 편집 (%s)" % (e["task"], n, f))
        if e.get("timed_out"):
            anomalies.append("모델 시간 초과: %s (시도 %s)" % (e["task"], e.get("attempt")))
        if e.get("denials"):
            anomalies.append("훅 거부 %d회: %s (시도 %s)" % (int(e["denials"]), e["task"], e.get("attempt")))
        if e.get("error"):
            anomalies.append("드라이버 오류: %s — %s" % (e["task"], str(e["error"])[:120]))
    smoke = next((e for e in ne if e.get("event") == "smoke"), None)
    if smoke and not smoke.get("ok"):
        anomalies.append("밤 시작 스모크 실패 (복구 작업 발급)")
    end_dt = parse_iso(ended["ts"]) if ended else now()
    next_tasks = rank(tasks, states, domain, now_dt=end_dt)[:3]
    return {
        "night": night_id, "started": started, "ended": ended, "states": states, "by_id": by_id,
        "passed": passed, "blocked": blocked, "retry_ids": retry_ids, "pending": pending,
        "cost": cost, "anomalies": anomalies, "next": next_tasks, "events": ne,
    }


def _title(by_id: Dict[str, Task], tid: str) -> str:
    t = by_id.get(tid)
    return t.title if t else "(계획에 없음)"


def _last_line(text: Optional[str]) -> str:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    return lines[-1][:160] if lines else "(출력 없음)"


def render_summary(c: Dict[str, Any]) -> str:
    started, ended = c["started"], c["ended"]
    s_ts = started.get("ts") if started else None
    e_ts = ended.get("ts") if ended else None
    dur = fmt_duration((parse_iso(e_ts) - parse_iso(s_ts)).total_seconds()) if s_ts and e_ts else "진행 중"
    by_id, states = c["by_id"], c["states"]
    reason = {"budget": "예산 소진", "queue_empty": "큐 비움", "max_tasks": "작업 수 상한", "interrupted": "중단됨",
              "smoke_unrepairable": "스모크 복구 실패", "bootstrap_failed": "부트스트랩 실패"}.get(
        (ended or {}).get("reason", ""), (ended or {}).get("reason", "진행 중"))
    branch = (started or {}).get("branch", "?")
    out = ["# %s · %s → %s (%s)" % (c["night"], fmt_clock(s_ts), fmt_clock(e_ts), dur), ""]
    out += ["## 결론",
            "완료 %d / 실패(재시도 예정) %d / 막힘 %d / 미착수 %d · 종료: %s · 브랜치 `%s` · 비용 $%.2f" % (
                len(c["passed"]), len(c["retry_ids"]), len(c["blocked"]), len(c["pending"]), reason, branch, c["cost"]), ""]
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
            out.append("- %s %s — %s. 마지막 오류: `%s`" % (
                e["task"], _title(by_id, e["task"]), e.get("reason", "?"), _last_line((lf or {}).get("tail"))))
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
    out += ["", "## 다음 밤에 할 것 (P2가 선택)"]
    if c["next"]:
        for i, t in enumerate(c["next"], 1):
            out.append("%d. %s %s (priority %d, %d분)" % (i, t.id, t.title, t.priority, t.estimate_minutes))
    else:
        out.append("- (자격 있는 작업 없음 — 계획을 다시 쓰거나 BLOCKED.md를 본다)")
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
