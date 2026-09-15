"""Codex JSONL과 프로세스 경계 검증. 모델 호출만 작은 CLI 대역으로 대체한다."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "runner"))
import drivers as D
import harnesslib as H
import codex_driver as C
from fixtures import make_repo, sh, NIGHT


def domain():
    return H.Domain({"driver": {"name": "codex", "max_budget_usd": None, "max_turns": None},
                     "budget": {"rate_limit_stop": None}})


class CodexTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.ctx = D.propose_context(H.Repo(self.repo), domain(), 0.1)
        self.stream = self.root / "result.jsonl"

    def fake_cli(self, body):
        exe = self.bin / "codex"
        exe.write_text('#!' + sys.executable + '\nimport json, os, sys, time\nfrom pathlib import Path\n' +
                       'if "--version" in sys.argv:\n print("codex-cli 0.154.0"); sys.exit()\n' + body,
                       encoding="utf-8")
        exe.chmod(0o755)

    def invoke(self, readonly=False):
        with patch.dict(os.environ, {"PATH": str(self.bin) + os.pathsep + os.environ["PATH"]}):
            return C.run(self.ctx, "task", "system", self.stream, readonly=readonly)

    def test_jsonl_records_usage_edits_and_final_message(self):
        run = D.ModelRun(ok=False)
        for event in [
            {"type": "turn.started"},
            {"type": "item.completed", "item": {"id": "a", "type": "command_execution", "command": "ls", "status": "completed", "exit_code": 0}},
            {"type": "item.completed", "item": {"id": "b", "type": "file_change", "changes": [{"path": str(self.repo / "a.py"), "kind": "update"}], "status": "completed"}},
            {"type": "item.completed", "item": {"id": "c", "type": "agent_message", "text": "RESULT: done — 完了"}},
            {"type": "turn.completed", "usage": {"input_tokens": 100, "cached_input_tokens": 40, "output_tokens": 12}},
        ]:
            C.ingest(run, self.ctx, json.dumps(event).encode())
        self.assertEqual(run.edits, {"a.py": 1})
        self.assertEqual(run.tool_counts, {"Bash": 1, "apply_patch": 1})
        self.assertEqual(run.usage, {"input_tokens": 100, "cached_input_tokens": 40, "output_tokens": 12})
        self.assertEqual(run.self_report, "done")
        self.assertTrue(run.saw_result)
        self.assertFalse(run.cost_known)

    def test_success_uses_controlled_config_and_readonly_proposal(self):
        self.fake_cli('Path(os.environ["HARNESS_CANARY"]).write_text("ok\\n")\n'
                      'Path("args.json").write_text(json.dumps(sys.argv))\n'
                      'print(json.dumps({"type":"turn.completed","usage":{"input_tokens":3,"output_tokens":2}}))\n')
        run = self.invoke(readonly=True)
        self.assertTrue(run.ok, run.error)
        args = json.loads((self.repo / "args.json").read_text(encoding="utf-8"))
        self.assertEqual(args[args.index("--sandbox") + 1], "read-only")
        self.assertIn("--ignore-user-config", args)
        self.assertIn('web_search="disabled"', args)
        self.assertIn('features.plugins=false', args)
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", args)

    def test_missing_hook_canary_stops_before_waiting_for_model(self):
        self.fake_cli('print(json.dumps({"type":"turn.started"}),flush=True)\n'
                      'print(json.dumps({"type":"item.started","item":{"type":"command_execution","id":"a"}}),flush=True)\ntime.sleep(60)\n')
        self.stream.with_suffix(".canary").write_text("stale", encoding="utf-8")
        run = self.invoke()
        self.assertFalse(run.ok)
        self.assertTrue(run.hooks_dead)
        self.assertLess(run.seconds, 5)

    def test_turn_started_can_precede_session_start_hook(self):
        self.fake_cli('print(json.dumps({"type":"turn.started"}),flush=True)\ntime.sleep(0.1)\n'
                      'Path(os.environ["HARNESS_CANARY"]).write_text("ok\\n")\n'
                      'print(json.dumps({"type":"turn.completed","usage":{}}))\n')
        result = self.invoke()
        self.assertTrue(result.ok, result.error)

    def test_timeout_terminates_process_group(self):
        self.fake_cli('import subprocess\nPath(os.environ["HARNESS_CANARY"]).write_text("ok\\n")\n'
                      'subprocess.Popen([sys.executable,"-c","import time; from pathlib import Path; time.sleep(1); Path(\'escaped\').touch()"] )\n'
                      'time.sleep(60)\n')
        self.ctx.timeout_minutes = 0.005
        run = self.invoke()
        self.assertTrue(run.timed_out)
        time.sleep(1.1)
        self.assertFalse((self.repo / "escaped").exists())

    def test_failed_or_missing_final_event_is_not_success(self):
        for body in ['print(json.dumps({"type":"turn.failed","error":{"message":"quota exceeded"}}))',
                     'print("not-json")', 'print(json.dumps({"type":"turn.completed"})); sys.exit(9)']:
            with self.subTest(body=body):
                self.fake_cli('Path(os.environ["HARNESS_CANARY"]).write_text("ok\\n")\n' + body + '\n')
                run = self.invoke()
                self.assertFalse(run.ok)
                self.assertTrue(run.error)

    def test_unsupported_budget_fails_before_invoking_cli(self):
        self.ctx.domain = H.Domain({})
        self.fake_cli('Path("called").touch()\n')
        run = self.invoke()
        self.assertFalse(run.ok)
        self.assertIn("max_budget_usd", run.error)
        self.assertIn("rate_limit_stop", run.error)
        self.assertFalse((self.repo / "called").exists())

    def test_project_config_cannot_add_tools_or_permissions(self):
        (self.repo / ".codex").mkdir()
        (self.repo / ".codex/config.toml").write_text('web_search="live"', encoding="utf-8")
        self.fake_cli('Path("called").touch()\n')
        run = self.invoke()
        self.assertFalse(run.ok)
        self.assertIn(".codex", run.error)
        self.assertFalse((self.repo / "called").exists())

    def test_night_commits_verified_work_and_records_unknown_cost(self):
        self.fake_cli('Path(os.environ["HARNESS_CANARY"]).write_text("ok\\n")\n'
                      'Path("calc.py").write_text("def add(a,b): return a+b\\ndef mul(a,b): return a*b\\n")\n'
                      'print(json.dumps({"type":"turn.started"}))\n'
                      'print(json.dumps({"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":5}}))\n')
        config = domain().raw
        config["lessons"]["propose"] = False
        make_repo(self.repo, domain=config, tasks=[{"title": "mul", "goal": "mul", "verify": "python3 -c 'import calc; assert calc.mul(3,4)==12'", "estimate_minutes": 5}])
        env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ["PATH"])
        result = sh(sys.executable, NIGHT, "--repo", str(self.repo), "--driver", "codex", "--max-tasks", "1", env=env, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        events = H.read_log(H.Repo(self.repo).log)
        self.assertTrue(any(e["event"] == "task_passed" for e in events), result.stdout)
        model = next(e for e in events if e["event"] == "model_done")
        self.assertIsNone(model.get("cost_usd"))
        self.assertFalse(model["cost_known"])
        self.assertEqual(model["usage"]["output_tokens"], 5)
        self.assertIn("비용 미상", H.Repo(self.repo).summary.read_text(encoding="utf-8"))
        self.assertEqual(sh("git", "status", "--porcelain", cwd=self.repo).stdout, "")

    def test_failed_verification_reverts_work_but_keeps_patch(self):
        self.fake_cli('Path(os.environ["HARNESS_CANARY"]).write_text("ok\\n")\n'
                      'Path("calc.py").write_text("def add(a,b): return 999\\n")\n'
                      'print(json.dumps({"type":"turn.started"}))\n'
                      'print(json.dumps({"type":"turn.completed","usage":{}}))\n')
        config = domain().raw
        config["lessons"]["propose"] = False
        config["budget"]["max_attempts"] = 1
        make_repo(self.repo, domain=config, tasks=[{"title": "fail", "goal": "fail", "verify": "false", "estimate_minutes": 5}])
        env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ["PATH"])
        result = sh(sys.executable, NIGHT, "--repo", str(self.repo), "--driver", "codex", "--max-tasks", "1", env=env, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("999", (self.repo / "calc.py").read_text(encoding="utf-8"))
        events = H.read_log(H.Repo(self.repo).log)
        failure = next(e for e in events if e["event"] == "task_failed")
        self.assertTrue((self.repo / failure["patch"]).exists())
        self.assertFalse(any(e["event"] == "task_passed" for e in events))

    def test_loop_rejects_dollar_limit_for_codex_before_starting_night(self):
        make_repo(self.repo, domain=domain().raw)
        result = sh(sys.executable, str(Path(NIGHT).with_name("night-loop")), "--repo", str(self.repo),
                    "--driver", "codex", check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("max-total-usd", result.stderr)
        self.assertFalse(H.Repo(self.repo).log.exists())

    def test_propose_and_lessons_use_readonly_adapter(self):
        self.fake_cli('Path(os.environ["HARNESS_CANARY"]).write_text("ok\\n")\n'
                      'Path("args.json").write_text(json.dumps(sys.argv))\n'
                      'print(json.dumps({"type":"item.completed","item":{"type":"agent_message","text":"```json\\n{\\"tasks\\":[],\\"lessons\\":[]}\\n```"}}))\n'
                      'print(json.dumps({"type":"turn.completed","usage":{"output_tokens":2}}))\n')
        with patch.dict(os.environ, {"PATH": str(self.bin) + os.pathsep + os.environ["PATH"]}):
            for call in (D.run_propose, D.run_lessons):
                result = call(self.ctx, "codex", "propose", self.stream)
                self.assertTrue(result.ok, result.error)
                args = json.loads((self.repo / "args.json").read_text(encoding="utf-8"))
                self.assertEqual(args[args.index("--sandbox") + 1], "read-only")
                self.assertIn('"lessons":[]', result.result_text)

    def test_interrupt_restores_tree_and_records_interrupted_attempt(self):
        self.fake_cli('Path(os.environ["HARNESS_CANARY"]).write_text("ok\\n")\n'
                      'Path("calc.py").write_text("changed\\n")\n'
                      'print(json.dumps({"type":"turn.started"}),flush=True)\ntime.sleep(60)\n')
        config = domain().raw
        config["lessons"]["propose"] = False
        make_repo(self.repo, domain=config, tasks=[{"title": "interrupt", "goal": "interrupt", "verify": "false", "estimate_minutes": 5}])
        env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ["PATH"])
        proc = subprocess.Popen([sys.executable, NIGHT, "--repo", str(self.repo), "--driver", "codex"],
                                env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", start_new_session=True)
        try:
            deadline = time.monotonic() + 10
            while (self.repo / "calc.py").read_text(encoding="utf-8") != "changed\n" and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertEqual((self.repo / "calc.py").read_text(encoding="utf-8"), "changed\n")
            proc.send_signal(signal.SIGTERM)
            proc.communicate(timeout=15)
        finally:
            H.kill_group(proc, grace=0.2)
            proc.communicate()
        events = H.read_log(H.Repo(self.repo).log)
        self.assertEqual(events[-1]["reason"], "interrupted")
        self.assertTrue(any(e.get("stage") == "interrupted" for e in events))
        self.assertIn("return a + b", (self.repo / "calc.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
