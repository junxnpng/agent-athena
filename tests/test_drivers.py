"""drivers 단위 테스트 — 스트림 집계 (result 없이도 턴 수·rate limit 을 안다)."""
from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "runner"))
import drivers as D  # noqa: E402
import harnesslib as H  # noqa: E402


class IngestTests(unittest.TestCase):
    def test_turns_rate_limit_and_bash_edits_without_result(self):
        with tempfile.TemporaryDirectory() as d:
            ctx = SimpleNamespace(repo=H.Repo(Path(d).resolve()))
            run = D.ModelRun(ok=False)
            lines = [
                b'{"type":"system","subtype":"init"}',
                b'{"type":"rate_limit_event","rate_limit_info":{"unifiedWindows":{"five_hour":{"utilization":0.67}}}}',
                b'{"type":"assistant","message":{"content":[{"type":"text","text":"hi"}]}}',
                b'{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Bash","input":{"command":"cat > tests/t.py <<EOF\\nx\\nEOF"}}]}}',
                b'{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Edit","input":{"file_path":"%s/src/a.py"}}]}}' % d.encode(),
                b'not json',
            ]
            for ln in lines:
                D._ingest(run, ctx, ln)
            self.assertEqual(run.assistant_turns, 3)
            self.assertEqual(run.rate_limit_utilization, 0.67)
            self.assertFalse(run.saw_result)
            self.assertEqual(run.edits, {"tests/t.py": 1, "src/a.py": 1})
            self.assertEqual(run.tool_counts, {"Bash": 1, "Edit": 1})
            D._ingest(run, ctx, b'{"type":"result","subtype":"success","num_turns":7,"total_cost_usd":1.5,"result":"ok\\nRESULT: done - x","permission_denials":[{}]}')
            self.assertEqual((run.turns, run.cost_usd, run.denials, run.self_report, run.saw_result), (7, 1.5, 1, "done", True))


class ClaudeCanaryTests(unittest.TestCase):
    """run_claude 훅 생존 카나리아 — session-start 훅이 쓴 파일이 없으면 첫 assistant 이벤트에서 즉시 죽인다.

    가짜 claude 실행 파일을 PATH 앞에 놓고 stream-json 을 흉내 낸다. 카나리아를 만드는 쪽 = 훅이 로드된 세션.
    """

    ASSISTANT = '{"type":"assistant","message":{"content":[{"type":"text","text":"hi"}]}}'
    RESULT = '{"type":"result","num_turns":1,"total_cost_usd":0.1,"result":"RESULT: done"}'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        (self.root / "bin").mkdir()
        (self.root / "repo").mkdir()
        self.old_path = os.environ.get("PATH", "")
        os.environ["PATH"] = str(self.root / "bin") + os.pathsep + self.old_path

    def tearDown(self):
        os.environ["PATH"] = self.old_path
        self.tmp.cleanup()

    def fake_claude(self, lines, touch_canary, sleep_after=False, double_fire=False):
        data = self.root / "bin" / "stream.jsonl"
        data.write_text("\n".join(lines) + "\n", encoding="utf-8")
        body = ["#!/bin/sh"]
        if touch_canary:
            body.append(': > "$HARNESS_CANARY"')
        if double_fire:
            body.append('printf "a\\nb\\n" > "$HARNESS_CANARY"')
        body.append('cat "%s"' % data)
        if sleep_after:
            body.append("sleep 60")
        exe = self.root / "bin" / "claude"
        exe.write_text("\n".join(body) + "\n", encoding="utf-8")
        exe.chmod(0o755)

    def run_claude(self):
        task = H.Task(id="task-001", title="t", goal="g", verify="true", estimate_minutes=5)
        ctx = D.TaskContext(repo=H.Repo(self.root / "repo"), domain=H.Domain({}), night_id="night-001",
                            task=task, state=H.TaskState(id="task-001"), attempt=1,
                            timeout_minutes=0.3, deadline_epoch=time.time() + 600, spec_text="")
        stream = self.root / "repo" / ".harness" / "sessions" / "night-001" / "task-001.1.stream.jsonl"
        return D.run_claude(ctx, "p", "s", stream), stream

    def test_canary_present_runs_to_completion(self):
        self.fake_claude([self.ASSISTANT, self.RESULT], touch_canary=True)
        run, stream = self.run_claude()
        self.assertEqual((run.hooks_dead, run.ok, run.saw_result, run.error), (False, True, True, ""))
        self.assertTrue(stream.with_suffix(".canary").exists())

    def test_canary_two_lines_reports_double_fire_but_survives(self):
        self.fake_claude([self.ASSISTANT, self.RESULT], touch_canary=False, double_fire=True)
        run, _ = self.run_claude()
        self.assertEqual((run.hooks_dead, run.ok, run.hook_fires), (False, True, 2))  # 훅은 살아 있다 — 기록만

    def test_canary_missing_kills_immediately_even_with_stale_file(self):
        self.fake_claude([self.ASSISTANT, self.RESULT], touch_canary=False, sleep_after=True)
        # 이전 시도의 카나리아가 남아 있어도 생존으로 위장하면 안 된다 — 드라이버가 시작 전에 지운다
        stale = self.root / "repo" / ".harness" / "sessions" / "night-001" / "task-001.1.stream.canary"
        stale.parent.mkdir(parents=True, exist_ok=True)
        stale.write_text("stale\n", encoding="utf-8")
        run, stream = self.run_claude()
        self.assertTrue(run.hooks_dead)
        self.assertFalse(run.ok)
        self.assertFalse(run.timed_out)  # 시간 초과가 아니라 카나리아 판정으로 죽었다
        self.assertIn("카나리아", run.error)
        self.assertLess(run.seconds, 10.0)  # sleep 60 을 기다리지 않고 즉시 죽인다


if __name__ == "__main__":
    unittest.main()
