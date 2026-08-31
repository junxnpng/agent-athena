"""일일 비용 상한 — 로그 fold(day_cost_usd) · night preflight 거부(exit 4) · 밤 중 종료(cost_day) · night-loop 멈춤(형제 repo 합산)."""
from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(HERE))
import harnesslib as H  # noqa: E402
from fixtures import FAKE, NIGHT, PLAN, make_repo, sh  # noqa: E402

LOOP = str(ROOT / "runner" / "night-loop")
COST_PLAN = [
    {"title": "[add-mul][cost:3] mul", "goal": "g", "verify": "python3 -c \"import calc; assert calc.mul(3,4)==12\"", "estimate_minutes": 5, "priority": 2},
    {"title": "[add-sub][cost:3] sub", "goal": "g", "verify": "python3 -c \"import calc; assert calc.sub(3,4)==-1\"", "estimate_minutes": 5, "priority": 1},
]


class DayCostFold(unittest.TestCase):
    def test_folds_today_only_and_counts_proposals(self):
        now = H.now().replace(hour=12, minute=0, second=0, microsecond=0)
        today, yesterday = H.iso(now - timedelta(hours=1)), H.iso(now - timedelta(hours=13))
        events = [
            {"ts": yesterday, "event": "model_done", "cost_usd": 5.0},
            {"ts": today, "event": "model_done", "cost_usd": 1.5},
            {"ts": today, "event": "plan_proposed", "cost_usd": 0.5},
            {"ts": today, "event": "task_passed"},
            {"ts": "garbage", "event": "model_done", "cost_usd": 9.0},
            {"event": "model_done", "cost_usd": 9.0},
        ]
        self.assertAlmostEqual(H.day_cost_usd(events, now), 2.0)
        self.assertEqual(H.day_cost_usd([], now), 0.0)

    def test_domain_default_is_off(self):
        self.assertIsNone(H.Domain({}).max_day_usd)
        self.assertEqual(H.Domain({"budget": {"max_day_usd": 12}}).max_day_usd, 12.0)


class DayCapE2E(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self.tmp.name).resolve() / "ws"  # 형제 repo 합산 테스트를 위해 전용 부모 디렉토리
        self.root = self.ws / "repo"
        self.root.mkdir(parents=True)
        self.env = dict(os.environ, HARNESS_FAKE_MODEL=FAKE)
        self.env.pop("HARNESS_NIGHT", None)

    def tearDown(self):
        self.tmp.cleanup()

    def night(self):
        return sh("python3", NIGHT, "--repo", str(self.root), "--driver", "fake", env=self.env, check=False)

    def loop(self, *extra):
        return sh("python3", LOOP, "--repo", str(self.root), "--wait-minutes", "0", "--driver", "fake", *extra, env=self.env, check=False)

    def seed_today(self, path: Path, usd: float) -> None:
        H.append_event(path, "model_done", night="night-000", task="task-000", attempt=1, cost_usd=usd)

    def ends(self):
        return [e for e in H.read_log(H.Repo(self.root).log) if e["event"] == "night_ended"]

    def test_night_refuses_to_start_when_day_cap_spent(self):
        make_repo(self.root, tasks=PLAN[:1], domain={"budget": {"hours": 0.5, "max_attempts": 3, "max_day_usd": 1.0}})
        self.seed_today(H.Repo(self.root).log, 1.25)
        sh("git", "-C", str(self.root), "add", "-A")
        sh("git", "-C", str(self.root), "commit", "-q", "-m", "seed")
        p = self.night()
        self.assertEqual(p.returncode, 4, p.stdout + p.stderr)
        self.assertIn("일일 상한", p.stdout)
        self.assertNotIn("night_started", [e["event"] for e in H.read_log(H.Repo(self.root).log)])
        branches = sh("git", "-C", str(self.root), "branch", "--list", "harness/*").stdout
        self.assertEqual(branches.strip(), "")  # 브랜치도 만들지 않는다

    def test_night_ends_mid_night_with_cost_day(self):
        make_repo(self.root, tasks=COST_PLAN, domain={"budget": {"hours": 0.5, "max_attempts": 3, "max_day_usd": 2.5}})
        p = self.night()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        end = self.ends()[-1]
        self.assertEqual((end["reason"], end["passed"]), ("cost_day", 1))  # 첫 작업 $3 ≥ 상한 → 둘째는 미착수
        self.assertIn("일일 비용 상한 도달", (H.Repo(self.root).hdir / "SUMMARY.md").read_text(encoding="utf-8"))

    def test_loop_stops_before_night_on_repo_day_cap(self):
        make_repo(self.root, tasks=PLAN[:1], domain={"budget": {"hours": 0.5, "max_attempts": 3, "max_day_usd": 1.0}})
        self.seed_today(H.Repo(self.root).log, 2.0)
        sh("git", "-C", str(self.root), "add", "-A")
        sh("git", "-C", str(self.root), "commit", "-q", "-m", "seed")
        p = self.loop()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("cost_day", p.stdout)
        self.assertEqual(self.ends(), [])

    def test_loop_machine_wide_cap_folds_sibling_repos(self):
        make_repo(self.root, tasks=PLAN[:1])
        sib = self.ws / "sibling" / ".harness"
        sib.mkdir(parents=True)
        self.seed_today(sib / "log.jsonl", 5.0)  # 다른 repo 가 오늘 $5 씀
        p = self.loop("--max-day-usd", "4")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("cost_day_all", p.stdout)
        self.assertEqual(self.ends(), [])
        p = self.loop("--max-day-usd", "40", "--max-nights", "1")  # 상한 안이면 정상
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(len(self.ends()), 1)


if __name__ == "__main__":
    unittest.main()
