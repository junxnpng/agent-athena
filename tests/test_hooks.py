"""훅 테스트 — pre-tool 거부 규칙과 session-start 5단계를 실제 프로세스로 돌려 고정한다."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUN_HOOK = str(ROOT / "hooks" / "run-hook")
# HARNESS_TEST_SH=dash 이면 run-hook 을 그 셸로 실행한다 — Ubuntu /bin/sh(dash) 재현. scripts/check 가 dash 가 있으면 켠다.
SH = [os.environ["HARNESS_TEST_SH"]] if os.environ.get("HARNESS_TEST_SH") else []
sys.path.insert(0, str(ROOT / "runner"))
import harnesslib as H  # noqa: E402
from _util import git_init  # noqa: E402


class HookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        git_init(self.root)
        h = self.root / ".harness"
        h.mkdir()
        (h / "domain.json").write_text(json.dumps({"write_scope": ["src", "docs/notes.md"]}))
        (h / "plan.json").write_text(json.dumps({"tasks": [{"id": "task-001", "title": "t", "goal": "g", "verify": "true", "estimate_minutes": 5}]}))
        (h / "verify").write_text("#!/bin/sh\necho smoke-ok\n")
        os.chmod(h / "verify", 0o755)
        (h / "spec.md").write_text("s")
        (h / "init.sh").write_text("#!/bin/sh\nexit 0\n")
        (self.root / "src").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def hook(self, name, payload, runner=False, **env_extra):
        env = dict(os.environ)
        env.pop("HARNESS_NIGHT", None)
        env.pop("HARNESS_DEADLINE_EPOCH", None)
        if runner:
            env["HARNESS_NIGHT"] = "night-001"
        env.update(env_extra)
        payload = dict({"cwd": str(self.root), "session_id": "s"}, **payload)
        p = subprocess.run(SH + [RUN_HOOK, name], input=json.dumps(payload), capture_output=True, text=True, encoding="utf-8", env=env)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout) if p.stdout.strip() else None

    def decision(self, out):
        return (out or {}).get("hookSpecificOutput", {}).get("permissionDecision")

    def bash(self, cmd, runner=False, **env):
        return self.decision(self.hook("pre-tool", {"tool_name": "Bash", "tool_input": {"command": cmd}}, runner, **env))

    def write(self, path, runner=False):
        return self.decision(self.hook("pre-tool", {"tool_name": "Write", "tool_input": {"file_path": path, "content": "x"}}, runner))

    def test_inert_outside_harness_repo(self):
        with tempfile.TemporaryDirectory() as other:
            p = subprocess.run(SH + [RUN_HOOK, "pre-tool"], input=json.dumps({"cwd": other, "tool_name": "Bash", "tool_input": {"command": "git push"}}),
                               capture_output=True, text=True, encoding="utf-8")
            self.assertEqual((p.returncode, p.stdout), (0, ""))
            p = subprocess.run(SH + [RUN_HOOK, "session-start"], input=json.dumps({"cwd": other}), capture_output=True, text=True, encoding="utf-8")
            self.assertEqual((p.returncode, p.stdout), (0, ""))

    def test_commit_push_denied_in_both_modes(self):
        self.assertEqual(self.bash("git commit -m 'x'"), "deny")
        self.assertEqual(self.bash("git add . && git push origin main", runner=True), "deny")
        self.assertIsNone(self.bash("git status && git diff"))

    def test_network_and_installs_denied_only_in_runner_mode(self):
        self.assertIsNone(self.bash("curl https://example.com"))
        self.assertEqual(self.bash("curl https://example.com", runner=True), "deny")
        self.assertEqual(self.bash("python3 x.py | pip install foo", runner=True), "deny")
        self.assertEqual(self.bash("git fetch origin", runner=True), "deny")
        self.assertEqual(self.bash("git reset --hard HEAD", runner=True), "deny")
        self.assertIsNone(self.bash("python3 -m pytest -q", runner=True))

    def test_bookkeeping_files_denied(self):
        self.assertEqual(self.bash("echo x >> .harness/log.jsonl"), "deny")
        self.assertEqual(self.bash("sed -i '' 's/a/b/' .harness/SUMMARY.md"), "deny")
        self.assertEqual(self.write(str(self.root / ".harness" / "log.jsonl")), "deny")
        self.assertIsNone(self.write(str(self.root / ".harness" / "plan.json")))          # 대화형: 사람이 계획을 쓴다
        self.assertEqual(self.write(str(self.root / ".harness" / "plan.json"), runner=True), "deny")
        self.assertIsNone(self.write(str(self.root / ".harness" / "sessions" / "n.txt"), runner=True))

    def test_write_scope(self):
        self.assertIsNone(self.write(str(self.root / "src" / "a.py")))
        self.assertIsNone(self.write("src/b.py"))
        self.assertIsNone(self.write(str(self.root / "docs" / "notes.md")))
        self.assertEqual(self.write(str(self.root / "lib" / "c.py")), "deny")
        self.assertEqual(self.write("/etc/passwd"), "deny")
        self.assertEqual(self.write(str(Path.home() / "harness-outside.txt")), "deny")  # repo 밖 + tmp 밖

    def test_bash_write_targets_are_scope_checked(self):
        self.assertIsNone(self.bash("cat > src/a.py <<'EOF'\nx\nEOF"))
        self.assertEqual(self.bash("echo x > lib/b.py"), "deny")
        self.assertEqual(self.bash("python3 gen.py | tee lib/c.txt", runner=True), "deny")
        self.assertIsNone(self.bash("python3 -m pytest -q > /tmp/out.txt 2>&1"))
        self.assertIsNone(self.bash("python3 -m pytest -q 2>&1 | tail -3"))

    def test_budget_message(self):
        out = self.hook("pre-tool", {"tool_name": "Bash", "tool_input": {"command": "ls"}}, runner=True, HARNESS_DEADLINE_EPOCH="1")
        self.assertIn("예산이 끝났다", out["systemMessage"])

    def test_session_start_interactive_runs_smoke(self):
        out = self.hook("session-start", {"source": "startup"})
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "SessionStart")
        for needle in ("1. 작업 디렉토리", "2. 최근 로그", "3. 현재 작업 (P2가 결정", "task-001", "4. 스모크", ": ok", "5. 기존 문제"):
            self.assertIn(needle, ctx)

    def test_session_start_runner_mode_reads_smoke_from_log(self):
        H.append_event(self.root / ".harness" / "log.jsonl", "smoke", night="night-001", ok=False, exit=1, seconds=0.2, cmd=".harness/verify")
        H.append_event(self.root / ".harness" / "log.jsonl", "task_started", night="night-001", task="task-001", attempt=1)
        out = self.hook("session-start", {"source": "startup"}, runner=True, HARNESS_TASK_ID="task-001")
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("러너 모드 night-001", ctx)
        self.assertIn("4. 스모크 (밤 시작에 러너가 실행", ctx)
        self.assertIn("실패", ctx)
        self.assertIn("task-001 t · 시도 1/3", ctx)


if __name__ == "__main__":
    unittest.main()
