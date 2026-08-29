"""승인 게이트 (D1, 2026-08-29) — verify: "approval" 작업은 사람이 runner/queue approve 로 연다. 모델은 자격을 얻지 않고, 의존 작업은 승인 뒤 풀린다."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(HERE))
import harnesslib as H  # noqa: E402
from test_e2e import FAKE, make_repo, sh  # noqa: E402
from test_harnesslib import ev, task  # noqa: E402

NIGHT = str(ROOT / "runner" / "night")
QUEUE = str(ROOT / "runner" / "queue")


class GateUnitTests(unittest.TestCase):
    def test_gate_state_eligibility_and_approval(self):
        gate = task("task-001", "설계 승인", verify="approval", est=0)
        work = task("task-002", "구현", deps=("task-001",))
        dom = H.Domain({})
        self.assertTrue(gate.is_gate)
        self.assertFalse(work.is_gate)
        st = H.derive_states([], [gate, work])
        self.assertEqual((st["task-001"].state, st["task-002"].state), ("gate", "pending"))
        self.assertEqual(H.eligible([gate, work], st, dom), [])  # 게이트는 모델 자격 없음, 의존 작업은 막힘
        st = H.derive_states([ev("task_approved", task="task-001", by="human")], [gate, work])
        self.assertEqual(st["task-001"].state, "passed")
        self.assertIsNotNone(st["task-001"].approved_at)
        self.assertEqual([t.id for t in H.eligible([gate, work], st, dom)], ["task-002"])

    def test_validate_plan_allows_zero_estimate_only_for_gates(self):
        dom = H.Domain({})
        self.assertEqual(H.validate_plan([task("task-001", "g", verify="approval", est=0)], dom), [])
        self.assertTrue(any("estimate_minutes" in e for e in H.validate_plan([task("task-001", "x", est=0)], dom)))

    def test_summary_and_dag_show_pending_gate(self):
        gate = task("task-001", "결과 해석 승인", verify="approval", est=0)
        work = task("task-002", "다음 단계", deps=("task-001",))
        n = "night-003"
        events = [ev("night_started", night=n), ev("night_ended", night=n, reason="queue_empty")]
        c = H.collect_night(events, [gate, work], H.Domain({}), n)
        text = H.render_summary(c)
        self.assertIn("## 승인 대기", text)
        self.assertIn("- task-001 결과 해석 승인 — 뒤에 task-002", text)
        self.assertIn('task001["🔒 task-001 결과 해석 승인"]', text)


class GateE2E(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.env = dict(os.environ, HARNESS_FAKE_MODEL=FAKE)
        self.env.pop("HARNESS_NIGHT", None)

    def tearDown(self):
        self.tmp.cleanup()

    def run_(self, *args):
        return sh("python3", *args, "--repo", str(self.root), env=self.env, check=False)

    def test_night_waits_for_gate_then_runs_dependent_after_approve(self):
        make_repo(self.root, tasks=[
            {"title": "게이트: 설계 승인", "goal": "설계를 보고 결정", "verify": "approval", "estimate_minutes": 0},
            {"title": "[add-mul] mul 추가", "goal": "mul", "verify": "python3 -c \"import calc; assert calc.mul(3,4)==12\"", "estimate_minutes": 5, "depends_on": ["#0"]},
        ])
        p = self.run_(NIGHT, "--driver", "fake")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        repo = H.Repo(self.root)
        self.assertIn("## 승인 대기", repo.summary.read_text(encoding="utf-8"))
        self.assertEqual([e for e in H.read_log(repo.log) if e["event"] == "task_started"], [])  # 아무 모델 호출도 없었다
        bad = self.run_(QUEUE, "approve", "task-002")
        self.assertNotEqual(bad.returncode, 0)  # 게이트가 아닌 작업은 승인 대상이 아니다
        ok = self.run_(QUEUE, "approve", "task-001", "--note", "ok")
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        self.assertIn("승인: task-001 게이트: 설계 승인 → 자격: task-002", ok.stdout)
        self.assertTrue(sh("git", "-C", str(self.root), "log", "-1", "--format=%s").stdout.startswith("[harness] approve task-001"))
        again = self.run_(QUEUE, "approve", "task-001")
        self.assertNotEqual(again.returncode, 0)  # 두 번 열 수 없다
        p = self.run_(NIGHT, "--driver", "fake")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        _, tasks = H.load_plan(repo)
        st = H.derive_states(H.read_log(repo.log), tasks)
        self.assertEqual((st["task-001"].state, st["task-002"].state), ("passed", "passed"))
        status = self.run_(QUEUE, "status").stdout
        self.assertIn("task-001  passed", status)


if __name__ == "__main__":
    unittest.main()
