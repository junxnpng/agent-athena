"""drivers 단위 테스트 — 스트림 집계 (result 없이도 턴 수·rate limit 을 안다)."""
from __future__ import annotations

import sys
import tempfile
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


if __name__ == "__main__":
    unittest.main()
