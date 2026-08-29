#!/usr/bin/env python3
"""drivers — 모델 런타임 호출 어댑터. 부기는 여기 없다: 프롬프트를 만들고, 프로세스를 돌리고, 관측값을 돌려준다.

claude: `claude -p` + stream-json. 훅은 --plugin-dir로 세션 한정 주입 (설치 불필요, 실측 확인).
        사용자 설정 소스(전역 플러그인·훅·출력 스타일)는 --setting-sources 로 뺀다 — 무인 세션이 대화형 환경을 상속하지 않게 (findings/004).
fake:   HARNESS_FAKE_MODEL 셸 명령 (테스트 / 드라이런). 작업 JSON을 stdin으로 받는다.
codex:  Phase 6.

I9: 파일별 편집 횟수 같은 관측은 stream-json을 *밖에서* 세어 얻는다 — 훅으로 세면 관측이 대상을 바꾼다.
I7: WebFetch / WebSearch / MCP 를 끄고(신뢰불가 콘텐츠 다리), 네트워크 egress는 pre-tool 훅이 막는다.
"""
from __future__ import annotations

import json
import os
import queue as _queue
import re
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import harnesslib as H

PROMPTS = Path(__file__).resolve().parent / "prompts"
WRITE_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
DISALLOWED_TOOLS = "WebFetch,WebSearch,AskUserQuestion"
SETTING_SOURCES = "project,local"  # user 제외: 전역 enabledPlugins·훅·출력 스타일이 무인 세션에 실리지 않게 (findings/004). 대상 repo 의 project/local 은 도메인 소유라 유지
RESULT_RE = re.compile(r"RESULT:\s*(done|partial|blocked)\b", re.IGNORECASE)
KNOWN_DRIVERS = ("claude", "fake")


@dataclass
class ModelRun:
    ok: bool
    timed_out: bool = False
    error: str = ""
    exit: Optional[int] = None
    seconds: float = 0.0
    turns: int = 0
    cost_usd: float = 0.0
    edits: Dict[str, int] = field(default_factory=dict)       # P9 재료: 파일별 편집 횟수
    tool_counts: Dict[str, int] = field(default_factory=dict)
    skills: Dict[str, int] = field(default_factory=dict)      # 모델이 스스로 부른 스킬 (Skill tool_use 의 input.skill) — 자동 호출 실사용률 (findings/004)
    denials: int = 0                                          # 훅이 거부한 도구 호출 수
    result_text: str = ""
    self_report: str = ""                                     # 모델의 RESULT: 자기 보고 — 판정이 아니다 (P6)
    saw_result: bool = False
    stream_path: Optional[str] = None
    assistant_turns: int = 0                                  # 스트림에서 센 assistant 메시지 수 (result 가 없어도 안다)
    slept_seconds: float = 0.0                                # 벽시계 − 단조시계 차이 = 머신이 잠든 시간 (findings/002)
    rate_limit_utilization: Optional[float] = None            # 5시간 창 사용률 (rate_limit_event)
    hooks_dead: bool = False                                  # 카나리아 부재 — 플러그인 훅이 로드되지 않은 세션 (즉시 중단)
    hook_fires: int = 0                                       # 카나리아 줄 수 = session-start 발화 횟수 (2+ = 이중 발화)


@dataclass
class TaskContext:
    repo: H.Repo
    domain: H.Domain
    night_id: str
    task: H.Task
    state: H.TaskState
    attempt: int
    timeout_minutes: float
    deadline_epoch: float
    spec_text: str


# ────────────────────────────────────────────────────────────── 프롬프트 (md = 지침, 강제 아님)

def render(template: str, mapping: Dict[str, Any]) -> str:
    text = (PROMPTS / template).read_text(encoding="utf-8")
    for k, v in mapping.items():
        text = text.replace("{{%s}}" % k, str(v))
    return text


def build_system_prompt() -> str:
    return (PROMPTS / "system.md").read_text(encoding="utf-8").strip()


def _history(ctx: TaskContext) -> str:
    hist = ctx.state.failure_history
    if not hist:
        return "없음 (첫 시도)"
    parts: List[str] = []
    for f in hist[-3:]:
        head = "시도 %s (%s): %s — %s" % (f.get("attempt", "?"), f.get("night", "?"), f.get("stage", "?"), f.get("reason", "?"))
        body = (f.get("tail") or "").strip()
        block = "```\n%s\n```" % "\n".join(body.splitlines()[-25:]) if body else ""
        patch = ("이전 시도의 diff: `%s` (필요하면 `git apply <경로>`로 되살릴 수 있다)" % f["patch"]) if f.get("patch") else "이전 시도의 diff 없음"
        parts.append("\n".join(x for x in (head, block, patch) if x))
    return "\n\n".join(parts) + "\n\n실패 흔적은 지우지 말고, 같은 접근을 그대로 반복하지 마라."


def build_task_prompt(ctx: TaskContext) -> str:
    t = ctx.task
    cmd, metric = H.normalize_verify(t.verify)
    thr = ""
    if metric:
        bounds = ["%s %s" % (k, v) for k, v in metric.items() if k in ("min", "max")]
        thr = " — 출력 마지막 줄의 숫자가 " + ", ".join(bounds) + " 이어야 한다"
    tools = "\n".join(
        "- %s: `%s` %s" % (x.get("name", "?"), x.get("cmd", "?"), x.get("note", "")) for x in ctx.domain.tools
    ) or "(없음)"
    return render("task.md", {
        "task_id": t.id, "attempt": ctx.attempt, "max_attempts": ctx.domain.max_attempts, "title": t.title,
        "night_id": ctx.night_id, "timeout_minutes": int(ctx.timeout_minutes), "repo": ctx.repo.root,
        "goal": t.goal, "verify_cmd": cmd, "verify_threshold": thr, "global_verify": ctx.domain.verify_cmd,
        "write_scope": ", ".join("`%s`" % p for p in ctx.domain.write_scope),
        "spec": ctx.spec_text.strip() or "(spec.md 비어 있음)", "tools": tools, "history": _history(ctx),
    })


def build_env(ctx: TaskContext) -> Dict[str, str]:
    env = dict(os.environ)
    env.pop("CLAUDECODE", None)  # Claude Code 안에서 러너를 띄워도 중첩 실행으로 취급되지 않게
    env.update({
        "HARNESS_ROOT": str(H.HARNESS_ROOT),
        "HARNESS_REPO": str(ctx.repo.root),
        "HARNESS_NIGHT": ctx.night_id,
        "HARNESS_TASK_ID": str(ctx.task.id),
        "HARNESS_ATTEMPT": str(ctx.attempt),
        "HARNESS_DEADLINE_EPOCH": str(int(ctx.deadline_epoch)),
    })
    return env


# ────────────────────────────────────────────────────────────── dispatch

def run_task(ctx: TaskContext, driver_name: str, stream_path: Path) -> ModelRun:
    prompt = build_task_prompt(ctx)
    if driver_name == "claude":
        return run_claude(ctx, prompt, build_system_prompt(), stream_path)
    if driver_name == "fake":
        return run_fake(ctx, prompt, stream_path)
    raise H.HarnessError("모르는 드라이버: %s (가능: %s)" % (driver_name, ", ".join(KNOWN_DRIVERS)))


PROPOSE_DISALLOWED = "Write,Edit,MultiEdit,NotebookEdit"  # 제안은 읽기 전용 탐색 — 쓰기는 Bash 휴리스틱+러너 되돌리기가 받는다


def propose_context(repo: H.Repo, domain: H.Domain, timeout_minutes: float) -> TaskContext:
    """P7-lite 제안 실행용 컨텍스트 — 밤이 아니라 'propose' 세션. 훅은 러너 모드(HARNESS_NIGHT=propose)로 뜬다."""
    task = H.Task(id="propose", title="계획 제안 (P7-lite)", goal="", verify="true", estimate_minutes=domain.leaf_min, origin="plan")
    return TaskContext(repo=repo, domain=domain, night_id="propose", task=task, state=H.TaskState(id="propose"), attempt=1,
                       timeout_minutes=timeout_minutes, deadline_epoch=time.time() + timeout_minutes * 60.0, spec_text="")


def run_propose(ctx: TaskContext, driver_name: str, prompt: str, stream_path: Path) -> ModelRun:
    if driver_name == "claude":
        return run_claude(ctx, prompt, build_system_prompt(), stream_path, extra_disallowed=PROPOSE_DISALLOWED)
    if driver_name == "fake":
        return run_fake(ctx, prompt, stream_path)
    raise H.HarnessError("모르는 드라이버: %s (가능: %s)" % (driver_name, ", ".join(KNOWN_DRIVERS)))


# ────────────────────────────────────────────────────────────── claude -p

def _ingest(run: ModelRun, ctx: TaskContext, line: bytes) -> None:
    try:
        ev = json.loads(line)
    except (ValueError, UnicodeDecodeError):
        return
    if not isinstance(ev, dict):
        return
    t = ev.get("type")
    if t == "rate_limit_event":
        info = ev.get("rate_limit_info") or {}
        u = ((info.get("unifiedWindows") or {}).get("five_hour") or {}).get("utilization")
        if u is None:
            u = info.get("utilization")
        if u is not None:
            run.rate_limit_utilization = max(run.rate_limit_utilization or 0.0, float(u))
    elif t == "assistant":
        run.assistant_turns += 1
        for c in (ev.get("message") or {}).get("content") or []:
            if not isinstance(c, dict) or c.get("type") != "tool_use":
                continue
            name = str(c.get("name") or "?")
            run.tool_counts[name] = run.tool_counts.get(name, 0) + 1
            inp = c.get("input") or {}
            if name in WRITE_TOOLS:
                fp = ctx.repo.rel(inp.get("file_path") or inp.get("notebook_path") or "?")
                run.edits[fp] = run.edits.get(fp, 0) + 1
            elif name == "Bash":  # heredoc / 리다이렉션 쓰기도 센다 (첫 밤 실측: 모델은 파일을 전부 Bash 로 썼다)
                for t in H.bash_write_targets(str(inp.get("command") or "")):
                    fp = ctx.repo.rel(t if os.path.isabs(t) else os.path.join(str(ctx.repo.root), t))
                    run.edits[fp] = run.edits.get(fp, 0) + 1
            elif name == "Skill":  # 스킬은 지침이라 호출은 확률적 — 실제로 불렸는지는 스트림에서만 안다 (I9)
                sk = str(inp.get("skill") or "?")
                run.skills[sk] = run.skills.get(sk, 0) + 1
    elif t == "result":
        run.saw_result = True
        run.turns = int(ev.get("num_turns") or 0)
        run.cost_usd = float(ev.get("total_cost_usd") or 0.0)
        run.result_text = str(ev.get("result") or "")
        run.denials = len(ev.get("permission_denials") or [])
        if ev.get("is_error"):
            run.error = "result is_error: " + H.tail(run.result_text, 300)
        m = RESULT_RE.search(run.result_text)
        run.self_report = m.group(1).lower() if m else ""


def run_claude(ctx: TaskContext, prompt: str, system_prompt: str, stream_path: Path, extra_disallowed: str = "") -> ModelRun:
    run = ModelRun(ok=False, stream_path=str(stream_path))
    exe = H.find_claude()
    if not exe:
        run.error = "claude CLI를 찾을 수 없다 (PATH, ~/.local/bin, /usr/local/bin)"
        return run
    drv = ctx.domain.driver
    args = [
        exe, "-p", prompt,
        "--output-format", "stream-json", "--verbose", "--include-hook-events",  # 훅 거부도 관측 기록에 남긴다
        "--plugin-dir", str(H.HARNESS_ROOT),
        "--setting-sources", SETTING_SOURCES,
        "--max-turns", str(int(drv.get("max_turns") or 120)),
        "--dangerously-skip-permissions",
        "--strict-mcp-config",
        "--disallowedTools", DISALLOWED_TOOLS + ("," + extra_disallowed if extra_disallowed else ""),
        "--append-system-prompt", system_prompt,
    ]
    for flag, key in (("--model", "model"), ("--effort", "effort"), ("--max-budget-usd", "max_budget_usd")):
        if drv.get(key):
            args += [flag, str(drv[key])]
    env = build_env(ctx)
    timeout = ctx.timeout_minutes * 60.0
    stream_path.parent.mkdir(parents=True, exist_ok=True)
    canary = stream_path.with_suffix(".canary")  # session-start 훅이 쓴다 — 존재 = 플러그인 훅 생존 증명
    canary.unlink(missing_ok=True)               # 이전 시도의 파일이 생존으로 위장하면 안 된다
    env["HARNESS_CANARY"] = str(canary)
    canary_checked = False
    start = time.time()
    start_mono = time.monotonic()  # 잠든 시간은 세지 않는다 (macOS mach_absolute_time / Linux CLOCK_MONOTONIC)
    proc = subprocess.Popen(
        args, cwd=str(ctx.repo.root), stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, start_new_session=True,
    )
    lines: "_queue.Queue[Optional[bytes]]" = _queue.Queue()
    stderr_buf: List[bytes] = []

    def pump_out() -> None:
        assert proc.stdout is not None
        for ln in iter(proc.stdout.readline, b""):
            lines.put(ln)
        lines.put(None)

    def pump_err() -> None:
        assert proc.stderr is not None
        stderr_buf.append(proc.stderr.read())

    pumps = [threading.Thread(target=pump_out, daemon=True), threading.Thread(target=pump_err, daemon=True)]
    for th in pumps:
        th.start()
    try:
        with stream_path.open("ab") as out:
            while True:
                left = timeout - (time.monotonic() - start_mono)
                if left <= 0:
                    run.timed_out = True
                    H.kill_group(proc)
                    break
                try:
                    ln = lines.get(timeout=min(1.0, left))
                except _queue.Empty:
                    continue
                if ln is None:
                    break
                out.write(ln)
                _ingest(run, ctx, ln)
                if not canary_checked and (run.assistant_turns or run.saw_result):
                    # 모델이 말하기 시작했다 = SessionStart 훅은 이미 끝났어야 한다. 없으면 훅 없이 도는 중 — 무방비
                    canary_checked = True
                    if not canary.exists():
                        run.hooks_dead = True
                        run.error = "훅 카나리아 없음 — 플러그인 훅이 로드되지 않았다 (쓰기 중재·trifecta 가드 부재), 즉시 중단"
                        H.kill_group(proc)
                        break
                    try:  # 줄 수 = 발화 횟수. 2 이상이면 전역 설치와 --plugin-dir 이 겹친 것 — 죽이지 않고 기록만 (훅은 살아 있다)
                        run.hook_fires = max(1, len(canary.read_text(encoding="utf-8").splitlines()))
                    except OSError:
                        run.hook_fires = 1
    except BaseException:
        H.kill_group(proc)
        raise
    finally:
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            H.kill_group(proc)
            proc.wait()
        for th in pumps:  # stderr 를 다 읽기 전에 stderr_buf 를 보면 빈 오류가 된다 (조기 종료 경로)
            th.join(timeout=5)
        for pipe in (proc.stdout, proc.stderr):
            try:
                pipe.close()
            except OSError:
                pass
    run.exit = proc.returncode
    run.seconds = time.time() - start
    run.slept_seconds = max(0.0, run.seconds - (time.monotonic() - start_mono))
    if not run.saw_result:
        run.turns = run.assistant_turns  # result 가 없어도 "0턴" 이 아니라 실제 진행을 보고한다 (findings/003)
    err = b"".join(stderr_buf).decode("utf-8", "replace").strip()
    if run.timed_out:
        run.error = "모델 시간 초과 (%d분)" % int(ctx.timeout_minutes)
    elif proc.returncode != 0 and not run.error:
        run.error = "claude exit %s: %s" % (proc.returncode, H.tail(err, 400) or "(stderr 없음)")
    elif not run.saw_result and not run.error:
        run.error = "result 이벤트 없음: %s" % (H.tail(err, 400) or "(stderr 없음)")
    run.ok = run.saw_result and not run.timed_out and not run.error
    return run


# ────────────────────────────────────────────────────────────── fake (테스트 / 드라이런)

def run_fake(ctx: TaskContext, prompt: str, stream_path: Path) -> ModelRun:
    script = os.environ.get("HARNESS_FAKE_MODEL") or str(ctx.domain.driver.get("fake_cmd") or "")
    if not script:
        return ModelRun(ok=False, error="fake 드라이버: HARNESS_FAKE_MODEL 미설정")
    payload = json.dumps({
        "night": ctx.night_id, "attempt": ctx.attempt, "task": ctx.task.to_json(), "prompt": prompt,
    }, ensure_ascii=False)
    code, out, secs, to = H.run_shell(script, ctx.repo.root, ctx.timeout_minutes * 60.0,
                                      env=build_env(ctx), stdin_text=payload)
    stream_path.parent.mkdir(parents=True, exist_ok=True)
    stream_path.write_text(out, encoding="utf-8")
    run = ModelRun(ok=(code == 0 and not to), timed_out=to, exit=code, seconds=secs, turns=1,
                   result_text=H.tail(out, 1500), saw_result=True, stream_path=str(stream_path))
    for ln in out.splitlines():  # 가짜 모델은 "EDIT <path>" 줄로 편집을, "COST <usd>" 줄로 비용을, "SKILL <이름>" 줄로 스킬 호출을 알린다
        if ln.startswith("EDIT "):
            fp = ln[5:].strip()
            run.edits[fp] = run.edits.get(fp, 0) + 1
        elif ln.startswith("COST "):
            try:
                run.cost_usd = float(ln[5:].strip())
            except ValueError:
                pass
        elif ln.startswith("SKILL "):
            sk = ln[6:].strip()
            run.skills[sk] = run.skills.get(sk, 0) + 1
    m = RESULT_RE.search(out)
    run.self_report = m.group(1).lower() if m else ""
    run.slept_seconds = float(os.environ.get("HARNESS_FAKE_SLEPT") or 0)  # 테스트: 잠듦 흉내
    if os.environ.get("HARNESS_FAKE_RATE"):                               # 테스트: 창 사용률 흉내
        run.rate_limit_utilization = float(os.environ["HARNESS_FAKE_RATE"])
    if to:
        run.error = "모델 시간 초과 (%d분)" % int(ctx.timeout_minutes)
    elif code != 0:
        run.error = "fake exit %d" % code
    return run
