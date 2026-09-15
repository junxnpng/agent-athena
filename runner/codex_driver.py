"""Codex 비대화형 실행 어댑터 — 실행 관측을 기존 ModelRun으로 변환한다."""
from __future__ import annotations

import json
import math
import os
import queue
import re
import shlex
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import List

import harnesslib as H
import drivers as D


def unsupported_limits(domain: H.Domain) -> List[str]:
    """Codex JSONL로 강제할 수 없는 예산 항목 이름을 반환한다.

    명시된 제한을 조용히 무시하지 않는다. null은 해당 제한을 해제한다.
    """
    values = {"budget.max_night_usd": domain.max_night_usd,
              "budget.max_day_usd": domain.max_day_usd,
              "budget.rate_limit_stop": domain.rate_limit_stop,
              "driver.max_budget_usd": domain.driver.get("max_budget_usd"),
              "driver.max_turns": domain.driver.get("max_turns")}
    return [name for name, value in values.items() if value is not None]


def preflight(repo: H.Repo, domain: H.Domain) -> str:
    limits = unsupported_limits(domain)
    if limits:
        raise H.HarnessError("Codex가 지원하지 않는 제한: %s. 시간 제한으로 실행하려면 해당 값을 null로 명시하라" % ", ".join(limits))
    # CLI override는 다른 레이어의 훅을 지우지 않는다. 검토하지 않은 훅을 함께 신뢰하지 않는다.
    paths = [p / ".codex" / name for p in (repo.root, *repo.root.parents)
             for name in ("config.toml", "hooks.json")]
    config_home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    paths.append(config_home / "hooks.json")
    mixed = [str(p) for p in paths if p.exists() and p != config_home / "config.toml"]
    if mixed:
        raise H.HarnessError("Codex 무인 실행에 별도 설정/훅을 섞을 수 없다: " + ", ".join(mixed))
    binary = shutil.which("codex")
    if not binary:
        raise H.HarnessError("codex CLI를 PATH에서 찾을 수 없다")
    try:
        version = subprocess.run([binary, "--version"], capture_output=True, encoding="utf-8", timeout=10, check=True)
    except (OSError, subprocess.SubprocessError) as e:
        raise H.HarnessError("Codex CLI 버전 확인 실패: %s" % e)
    found = re.search(r"codex-cli (\d+)\.(\d+)\.(\d+)", version.stdout)
    if not found or tuple(map(int, found.groups())) < (0, 154, 0):
        raise H.HarnessError("Codex CLI 0.154.0 이상이 필요하다")
    return binary


def ingest(result: D.ModelRun, ctx: D.TaskContext, line: bytes) -> None:
    result.cost_known = False
    try:
        event = json.loads(line)
    except (ValueError, UnicodeDecodeError):
        return
    if not isinstance(event, dict):
        return
    kind = event.get("type")
    if kind == "turn.started":
        result.turns += 1
    elif kind == "turn.completed":
        result.saw_result = True
        for key, value in (event.get("usage") or {}).items():
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                result.usage[key] = result.usage.get(key, 0) + value
    elif kind in ("turn.failed", "error"):
        error = event.get("error") or {}
        result.error = "Codex: " + str(error.get("message") or event.get("message") or "실행 실패")
    elif kind == "item.completed":
        item = event.get("item") or {}
        itype = item.get("type")
        if itype == "agent_message":
            result.assistant_turns += 1
            result.result_text = str(item.get("text") or "")
            match = D.RESULT_RE.search(result.result_text)
            result.self_report = match.group(1).lower() if match else ""
        elif itype in ("command_execution", "file_change"):
            tool = "Bash" if itype == "command_execution" else "apply_patch"
            result.tool_counts[tool] = result.tool_counts.get(tool, 0) + 1
            if itype == "file_change" and item.get("status") == "completed":
                for change in item.get("changes") or []:
                    path = ctx.repo.rel(change["path"])
                    result.edits[path] = result.edits.get(path, 0) + 1


def command(binary: str, ctx: D.TaskContext, system_prompt: str, readonly: bool) -> List[str]:
    args = [binary, "exec", "--json", "--ephemeral", "--ignore-user-config", "--ignore-rules", "--strict-config",
            "--sandbox", "read-only" if readonly else "workspace-write", "--dangerously-bypass-hook-trust",
            "-C", str(ctx.repo.root)]
    config = ['approval_policy="never"', 'web_search="disabled"', 'mcp_servers={}',
              'sandbox_workspace_write.network_access=false',
              'sandbox_workspace_write.exclude_slash_tmp=true',
              'sandbox_workspace_write.exclude_tmpdir_env_var=true',
              'sandbox_workspace_write.writable_roots=[]',
              'shell_environment_policy.inherit="core"', 'shell_environment_policy.ignore_default_excludes=false',
              'features.hooks=true', 'features.plugins=false', 'features.apps=false',
              'features.multi_agent=false', 'features.browser_use=false', 'features.computer_use=false',
              'features.image_generation=false', 'features.js_repl=false', 'features.code_mode=false',
              'features.memories=false', 'features.shell_snapshot=false',
              'features.skill_mcp_dependency_install=false', 'features.skip_host_skill_discovery=true',
              'skills.include_instructions=false', 'developer_instructions=' + json.dumps(system_prompt, ensure_ascii=False)]
    for event, hook in (("SessionStart", "session-start"), ("PreToolUse", "pre-tool")):
        cmd = shlex.quote(str(H.HARNESS_ROOT / "hooks" / "run-hook")) + " " + hook
        config.append('hooks.%s=[{matcher=".*",hooks=[{type="command",command=%s}]}]' % (event, json.dumps(cmd)))
    if ctx.domain.driver.get("model"):
        args += ["--model", str(ctx.domain.driver["model"])]
    if ctx.domain.driver.get("effort"):
        config.append("model_reasoning_effort=" + json.dumps(ctx.domain.driver["effort"]))
    for value in config:
        args += ["-c", value]
    return args


def run(ctx: D.TaskContext, prompt: str, system_prompt: str, stream_path: Path, readonly: bool = False) -> D.ModelRun:
    result = D.ModelRun(ok=False, cost_known=False, stream_path=str(stream_path))
    try:
        binary = preflight(ctx.repo, ctx.domain)
    except H.HarnessError as e:
        result.error = str(e)
        return result
    timeout = min(ctx.timeout_minutes * 60, ctx.deadline_epoch - time.time())
    if not math.isfinite(timeout) or timeout <= 0:
        result.timed_out, result.error = True, "Codex 실행 시간 예산이 없다"
        return result
    stream_path.parent.mkdir(parents=True, exist_ok=True)
    canary = stream_path.with_suffix(".canary")
    canary.unlink(missing_ok=True)
    env = D.build_env(ctx)
    # 인증은 CLI 저장 인증을 사용한다. 다른 런타임 API 키도 자식 환경에서 제거한다.
    env = {k: v for k, v in env.items() if not k.upper().startswith("ANTHROPIC")}
    env.update(HARNESS_CANARY=str(canary), HARNESS_CODEX="1", HARNESS_READONLY="1" if readonly else "")
    args = command(binary, ctx, system_prompt, readonly) + [prompt]
    start, mono = time.time(), time.monotonic()
    lines: queue.Queue = queue.Queue()
    errors: List[bytes] = []
    try:
        proc = subprocess.Popen(args, cwd=str(ctx.repo.root), stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, start_new_session=True)
    except OSError as e:
        result.error = "Codex 시작 실패: %s" % e
        return result

    def stdout() -> None:
        for line in iter(proc.stdout.readline, b""):
            lines.put(line)
        lines.put(None)

    def stderr() -> None:
        # stderr는 실패 진단용 tail만 유지한다.
        for block in iter(lambda: proc.stderr.read(4096), b""):
            errors.append(block)
            if len(errors) > 4:
                del errors[0]

    threads = [threading.Thread(target=stdout, daemon=True), threading.Thread(target=stderr, daemon=True)]
    for thread in threads:
        thread.start()
    checked = False
    try:
        with stream_path.open("wb") as out:
            while True:
                left = timeout - (time.monotonic() - mono)
                if left <= 0:
                    result.timed_out = True
                    H.kill_group(proc)
                    break
                try:
                    line = lines.get(timeout=min(left, 0.2))
                except queue.Empty:
                    continue
                if line is None:
                    break
                out.write(line)
                ingest(result, ctx, line)
                # Codex는 SessionStart 완료 전 turn.started를 보낸다. 첫 모델 활동에서 확인한다.
                try:
                    event = json.loads(line)
                except (ValueError, UnicodeDecodeError):
                    event = {}
                active_item = isinstance(event, dict) and event.get("type") in ("item.started", "item.completed") and (
                    (event.get("item") or {}).get("type") in ("agent_message", "command_execution", "file_change", "reasoning"))
                if not checked and (active_item or result.saw_result):
                    checked = True
                    if not canary.exists():
                        result.hooks_dead, result.error = True, "Codex 훅 카나리아 없음 — 실행 중단"
                        H.kill_group(proc)
                        break
                    result.hook_fires = len(canary.read_text(encoding="utf-8").splitlines())
            # stdout을 닫고도 남아 있는 프로세스에 전체 시간 예산을 넘겨주지 않는다.
            try:
                proc.wait(timeout=max(0.01, timeout - (time.monotonic() - mono)))
            except subprocess.TimeoutExpired:
                result.timed_out = True
                H.kill_group(proc)
    except BaseException:
        H.kill_group(proc)
        raise
    finally:
        H.kill_group(proc)
        proc.wait()
        for thread in threads:
            thread.join(timeout=2)
        proc.stdout.close()
        proc.stderr.close()
    result.exit = proc.returncode
    result.seconds = time.time() - start
    result.slept_seconds = max(0.0, result.seconds - (time.monotonic() - mono))
    if result.timed_out:
        result.error = "Codex 모델 시간 초과"
    elif result.exit and not result.error:
        result.error = "Codex exit %s: %s" % (result.exit, H.tail(b"".join(errors).decode("utf-8", "replace"), 500))
    elif not result.saw_result and not result.error:
        result.error = "Codex turn.completed 이벤트 없음"
    result.ok = result.saw_result and not result.error and not result.timed_out
    return result
