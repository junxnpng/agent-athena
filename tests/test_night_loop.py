"""night-loop e2e — fake 드라이버로 밤을 여러 개 잇는다: 계속/대기/멈춤 판단 · 총비용 상한 · 큐 비움 · 인프라 실패."""
from __future__ import annotations

import importlib.machinery
import importlib.util
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

LOOP = str(ROOT / "runner" / "night-loop")


def loop_module():
    loader = importlib.machinery.SourceFileLoader("night_loop", LOOP)  # 확장자 없는 진입점 — 로더를 명시해야 한다
    spec = importlib.util.spec_from_loader("night_loop", loader)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


PLAN = [
    {"title": "[add-mul][cost:3] mul", "goal": "g", "verify": "python3 -c \"import calc; assert calc.mul(3,4)==12\"", "estimate_minutes": 5, "priority": 2},
    {"title": "[add-sub][cost:3] sub", "goal": "g", "verify": "python3 -c \"import calc; assert calc.sub(3,4)==-1\"", "estimate_minutes": 5, "priority": 1},
]


class DecideTests(unittest.TestCase):
    def test_reason_table(self):
        L = loop_module()
        self.assertEqual((L.decide("budget", 0), L.decide("max_tasks", 0)), ("now", "now"))
        self.assertEqual((L.decide("rate_limited", 0), L.decide("cost_budget", 0)), ("wait", "wait"))
        for r in ("queue_empty", "machine_slept", "hooks_dead", "driver_unhealthy", "smoke_unrepairable", "bootstrap_failed", "interrupted", "???"):
            self.assertEqual(L.decide(r, 0), "stop", r)
        self.assertEqual(L.decide("budget", 3), "stop")  # 비정상 exit 는 사유와 무관하게 멈춘다 — 사람이 봐야 한다


class LoopE2E(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.env = dict(os.environ, HARNESS_FAKE_MODEL=FAKE)
        self.env.pop("HARNESS_NIGHT", None)

    def tearDown(self):
        self.tmp.cleanup()

    def loop(self, *extra):
        return sh("python3", LOOP, "--repo", str(self.root), "--wait-minutes", "0", "--driver", "fake", *extra, env=self.env, check=False)

    def ends(self):
        return [e for e in H.read_log(H.Repo(self.root).log) if e["event"] == "night_ended"]

    def test_chains_nights_until_queue_empty(self):
        make_repo(self.root, tasks=PLAN)
        p = self.loop("--max-tasks", "1", "--max-total-usd", "100")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual([e["reason"] for e in self.ends()], ["max_tasks", "max_tasks", "queue_empty"])  # 밤 하나 = 작업 하나, 셋째 밤은 빈 큐
        self.assertIn("루프 종료 (queue_empty) · 밤 3개 · 총비용 $6.00", p.stdout)
        repo = H.Repo(self.root)
        _, tasks = H.load_plan(repo)
        st = H.derive_states(H.read_log(repo.log), tasks)
        self.assertEqual({t.id: st[t.id].state for t in tasks}, {"task-001": "passed", "task-002": "passed"})
        self.assertEqual(sh("git", "-C", str(self.root), "rev-parse", "--abbrev-ref", "HEAD").stdout.strip(), "harness/night-003")  # 밤이 이어진다

    def test_total_cost_cap_stops_loop(self):
        make_repo(self.root, tasks=PLAN)
        p = self.loop("--max-tasks", "1", "--max-total-usd", "5")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual([e["reason"] for e in self.ends()], ["max_tasks", "max_tasks"])  # 3 + 3 ≥ 5 → 셋째 밤을 띄우지 않는다
        self.assertIn("루프 종료 (cost_cap) · 밤 2개 · 총비용 $6.00", p.stdout)

    def test_infra_failure_stops_loop_with_exit_3(self):
        make_repo(self.root, tasks=PLAN)
        self.env["HARNESS_FAKE_SLEPT"] = "900"  # 머신 잠듦 흉내 → 밤이 machine_slept 로 끝난다
        p = self.loop("--max-total-usd", "100")
        self.assertEqual(p.returncode, 3, p.stdout + p.stderr)
        self.assertEqual([e["reason"] for e in self.ends()], ["machine_slept"])
        self.assertIn("루프 종료 (machine_slept) · 밤 1개", p.stdout)

    def test_missing_harness_dir_is_rejected(self):
        p = self.loop()
        self.assertEqual(p.returncode, 2)
        self.assertIn(".harness/ 가 없다", p.stderr)


if __name__ == "__main__":
    unittest.main()
