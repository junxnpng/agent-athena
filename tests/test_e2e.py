"""e2e — fake 드라이버로 runner/night 를 실제 git repo 위에서 돌린다. 루프·판정·커밋·되돌리기·격리·SUMMARY 를 한 번에 본다."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "runner"))
import harnesslib as H  # noqa: E402
from _util import git_init  # noqa: E402

NIGHT = str(ROOT / "runner" / "night")
FAKE = "python3 %s" % (HERE / "fake_model.py")


def sh(*args, cwd=None, env=None, check=True):
    return subprocess.run(list(args), cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", check=check)


def make_repo(tmp: Path, verify_ok=True, tasks=None, domain=None):
    git_init(tmp)
    (tmp / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    (tmp / "test_calc.py").write_text("import calc\n\ndef test_add():\n    assert calc.add(1, 2) == 3\n")
    h = tmp / ".harness"
    h.mkdir()
    (h / ".gitignore").write_text("sessions/\n")
    (h / "spec.md").write_text("# spec\n계산기 모듈을 채운다.\n")
    body = "" if verify_ok else "test -f FIXED || { echo 'FIXED missing'; exit 1; }\n"
    run_all = "python3 -c \"import inspect, test_calc; [f() for n, f in inspect.getmembers(test_calc, inspect.isfunction) if n.startswith('test_')]; print('ok')\""
    (h / "verify").write_text("#!/bin/sh\ncd \"$(dirname \"$0\")/..\" || exit 1\n%s%s\n" % (body, run_all))
    (h / "init.sh").write_text("#!/bin/sh\nexit 0\n")
    os.chmod(h / "verify", 0o755)
    os.chmod(h / "init.sh", 0o755)
    (h / "domain.json").write_text(json.dumps(dict({"budget": {"hours": 0.5, "max_attempts": 3}, "driver": {"name": "fake"}}, **(domain or {}))))
    (h / "plan.json").write_text(json.dumps({"version": 1, "tasks": tasks or []}, ensure_ascii=False, indent=1))
    sh("git", "-C", str(tmp), "add", "-A")
    sh("git", "-C", str(tmp), "commit", "-q", "-m", "init")


PLAN = [
    {"title": "[add-mul] mul 추가", "goal": "mul(a,b)", "verify": "python3 -c \"import calc; assert calc.mul(3,4)==12\"", "estimate_minutes": 5, "priority": 2},
    {"title": "[add-sub] sub 추가", "goal": "sub(a,b)", "verify": "python3 -c \"import calc; assert calc.sub(3,4)==-1\"", "estimate_minutes": 5, "priority": 1, "depends_on": ["#0"]},
    {"title": "[hopeless] 될 리 없는 작업", "goal": "x", "verify": "test -f NEVER_EXISTS", "estimate_minutes": 5, "priority": 3},
    {"title": "[break-global] 리프는 통과, 전체는 깨짐", "goal": "x", "verify": "test -f wanted.txt", "estimate_minutes": 5, "priority": 0},
]


class NightE2E(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.env = dict(os.environ, HARNESS_FAKE_MODEL=FAKE)
        self.env.pop("HARNESS_NIGHT", None)

    def tearDown(self):
        self.tmp.cleanup()

    def night(self, *extra, check=True):
        return sh("python3", NIGHT, "--repo", str(self.root), "--driver", "fake", *extra, env=self.env, check=check)

    def test_full_night_then_second_night(self):
        make_repo(self.root, tasks=PLAN)
        p = self.night("--dry-run")
        self.assertIn("night-001", p.stdout)
        self.assertIn("task-003* [hopeless]", p.stdout)  # priority 3 이 먼저, id 는 메모리 발급

        p = self.night()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        repo = H.Repo(self.root)
        events = H.read_log(repo.log)
        kinds = [e["event"] for e in events]
        self.assertEqual(kinds[0], "night_started")
        self.assertEqual(kinds[-1], "night_ended")
        self.assertIn("smoke", kinds)
        _, tasks = H.load_plan(repo)
        self.assertEqual([t.id for t in tasks], ["task-001", "task-002", "task-003", "task-004"])
        self.assertEqual(tasks[1].depends_on, ["task-001"])
        st = H.derive_states(events, tasks)
        self.assertEqual(st["task-001"].state, "passed")
        self.assertEqual(st["task-002"].state, "passed")
        self.assertEqual((st["task-003"].state, st["task-003"].failures), ("blocked", 3))
        self.assertEqual((st["task-004"].state, st["task-004"].failures), ("blocked", 3))
        self.assertEqual(st["task-004"].last_failure["stage"], "global")
        self.assertTrue(st["task-004"].last_failure.get("patch"))
        ended = events[-1]
        self.assertEqual((ended["reason"], ended["passed"], ended["blocked"]), ("queue_empty", 2, 2))
        # 되돌리기: 실패한 시도의 흔적이 트리에 없다, 성공한 것은 있다
        self.assertFalse((self.root / "notes.txt").exists())
        self.assertFalse((self.root / "wanted.txt").exists())
        self.assertIn("def sub", (self.root / "calc.py").read_text())
        self.assertNotIn("test_broken", (self.root / "test_calc.py").read_text())
        # 커밋 정책
        log = sh("git", "-C", str(self.root), "log", "--format=%s", "harness/night-001").stdout.splitlines()
        self.assertTrue(all(l.startswith("[harness night-001") for l in log[:-1]), log)
        self.assertIn("[harness night-001 task-001] [add-mul] mul 추가", log)
        self.assertEqual(sh("git", "-C", str(self.root), "status", "--porcelain").stdout, "")
        self.assertEqual(sh("git", "-C", str(self.root), "rev-parse", "--abbrev-ref", "HEAD").stdout.strip(), "harness/night-001")
        summary = repo.summary.read_text()
        self.assertIn("# night-001", summary)
        self.assertIn("완료 2 / 실패(재시도 예정) 0 / 막힘 2 / 미착수 0", summary)
        self.assertIn("doom loop 의심: task-003 같은 파일 9회 편집 (notes.txt)", summary)
        self.assertIn("## 계획 DAG", summary)
        self.assertIn("task001 --> task002", summary)  # depends_on 이 엣지로
        self.assertIn("## task-003", repo.blocked.read_text())
        self.assertTrue((repo.sessions / "night-001" / "task-003.1.stream.jsonl").exists())
        self.assertFalse((repo.sessions / "lock").exists())

        # 둘째 밤: main 으로 돌아가도 미병합 night-001 에서 잇는다. 큐가 비어 즉시 끝난다
        sh("git", "-C", str(self.root), "checkout", "-q", "main")
        p = self.night()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("night-002", p.stdout)
        self.assertIn("미병합", p.stdout)
        self.assertEqual(sh("git", "-C", str(self.root), "merge-base", "--is-ancestor", "harness/night-001", "harness/night-002", check=False).returncode, 0)
        events = H.read_log(H.Repo(self.root).log)
        self.assertEqual(events[-1]["reason"], "queue_empty")
        self.assertEqual(H.latest_night_id(events), "night-002")

    def test_repair_task_when_smoke_fails(self):
        make_repo(self.root, verify_ok=False, tasks=PLAN[:1])
        p = self.night("--max-tasks", "3")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        repo = H.Repo(self.root)
        _, tasks = H.load_plan(repo)
        self.assertEqual([t.origin for t in tasks], ["plan", "repair"])
        events = H.read_log(repo.log)
        st = H.derive_states(events, tasks)
        self.assertEqual(st["task-002"].state, "passed")   # 복구 작업이 먼저 돌아 통과
        self.assertEqual(st["task-001"].state, "passed")
        started = [e["task"] for e in events if e["event"] == "task_started"]
        self.assertEqual(started, ["task-002", "task-001"])

    def test_scope_violation_is_judged_by_runner(self):
        make_repo(self.root, tasks=[{"title": "[out-of-scope] 범위 밖 쓰기", "goal": "x", "verify": "true", "estimate_minutes": 5}],
                  domain={"write_scope": ["tests"]})
        p = self.night("--max-tasks", "1")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        events = H.read_log(H.Repo(self.root).log)
        failed = [e for e in events if e["event"] == "task_failed"]
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]["stage"], "scope")
        self.assertIn("evil.py", failed[0]["reason"])
        self.assertEqual([e for e in events if e["event"] == "scope_violation"][0]["paths"], ["evil.py"])
        self.assertFalse((self.root / "evil.py").exists())
        self.assertNotIn("verify", [e["event"] for e in events if e.get("task") == "task-001"])  # 범위 위반이면 검증기도 안 돈다

    def test_machine_sleep_ends_night_without_consuming_attempts(self):
        make_repo(self.root, tasks=PLAN[:1])
        self.env["HARNESS_FAKE_SLEPT"] = "300"
        p = self.night(check=False)
        self.assertEqual(p.returncode, 3, p.stdout + p.stderr)  # 정상 종료 사유가 아니다
        events = H.read_log(H.Repo(self.root).log)
        kinds = [e["event"] for e in events]
        self.assertIn("sleep_detected", kinds)
        self.assertEqual(events[-1]["reason"], "machine_slept")
        failed = [e for e in events if e["event"] == "task_failed"]
        self.assertEqual((failed[0]["stage"], failed[0].get("infra")), ("sleep", True))
        _, tasks = H.load_plan(H.Repo(self.root))
        st = H.derive_states(events, tasks)["task-001"]
        self.assertEqual((st.state, st.attempts, st.failures), ("failed", 1, 0))  # 시도 횟수를 먹지 않는다
        self.assertNotIn("def mul", (self.root / "calc.py").read_text())  # 되돌려졌다
        summary = H.Repo(self.root).summary.read_text()
        self.assertIn("머신이 잠듦 (밤 중단)", summary)
        self.assertIn("머신 잠듦 5m00s: task-001", summary)

    def test_cost_budget_ends_night(self):
        tasks = [
            {"title": "[add-mul][cost:12] mul 추가", "goal": "mul", "verify": "python3 -c \"import calc; assert calc.mul(3,4)==12\"", "estimate_minutes": 5, "priority": 2},
            {"title": "[add-sub] sub 추가", "goal": "sub", "verify": "python3 -c \"import calc; assert calc.sub(3,4)==-1\"", "estimate_minutes": 5, "priority": 1},
        ]
        make_repo(self.root, tasks=tasks, domain={"budget": {"hours": 0.5, "max_attempts": 3, "max_night_usd": 10}})
        p = self.night()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)  # 비용 상한은 시간 예산과 같은 정상 종료다
        repo = H.Repo(self.root)
        events = H.read_log(repo.log)
        self.assertEqual(events[-1]["reason"], "cost_budget")
        self.assertEqual(events[-1]["cost_usd"], 12.0)
        started = [e["task"] for e in events if e["event"] == "task_started"]
        self.assertEqual(started, ["task-001"])  # 두 번째 작업은 시작도 못 한다
        _, tasks = H.load_plan(repo)
        st = H.derive_states(events, tasks)
        self.assertEqual(st["task-001"].state, "passed")   # 상한 판정은 다음 선택 전 — 이미 산 시도는 버리지 않는다
        self.assertEqual(st["task-002"].state, "pending")
        self.assertIn("종료: 비용 상한 도달", repo.summary.read_text())

    def test_rate_limit_stop_ends_night(self):
        tasks = [
            {"title": "[add-mul] mul 추가", "goal": "mul", "verify": "python3 -c \"import calc; assert calc.mul(3,4)==12\"", "estimate_minutes": 5, "priority": 2},
            {"title": "[add-sub] sub 추가", "goal": "sub", "verify": "python3 -c \"import calc; assert calc.sub(3,4)==-1\"", "estimate_minutes": 5, "priority": 1},
        ]
        make_repo(self.root, tasks=tasks)  # 기본값 rate_limit_stop=0.85
        self.env["HARNESS_FAKE_RATE"] = "0.95"
        p = self.night()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        repo = H.Repo(self.root)
        events = H.read_log(repo.log)
        self.assertEqual(events[-1]["reason"], "rate_limited")
        started = [e["task"] for e in events if e["event"] == "task_started"]
        self.assertEqual(started, ["task-001"])
        _, tasks = H.load_plan(repo)
        st = H.derive_states(events, tasks)
        self.assertEqual(st["task-001"].state, "passed")   # 판정이 끝난 뒤에 멈춘다 — 시도를 버리지 않는다
        summary = repo.summary.read_text()
        self.assertIn("종료: 5시간 창 사용률 상한 도달", summary)
        self.assertIn("5시간 창 사용률 최대 95%", summary)

    def test_queue_unblock(self):
        make_repo(self.root, tasks=[PLAN[2]])  # hopeless → 3회 실패 → blocked
        self.assertEqual(self.night().returncode, 0)
        QUEUE = str(ROOT / "runner" / "queue")
        p = sh("python3", QUEUE, "unblock", "task-001", "--reason", "테스트", "--repo", str(self.root), env=self.env, check=False)
        self.assertEqual(p.returncode, 0, p.stderr)
        rows = json.loads(sh("python3", QUEUE, "status", "--json", "--repo", str(self.root), env=self.env).stdout)
        self.assertEqual((rows[0]["state"], rows[0]["failures"], rows[0]["attempts"]), ("pending", 0, 3))
        p = sh("python3", QUEUE, "unblock", "task-001", "--repo", str(self.root), env=self.env, check=False)
        self.assertEqual(p.returncode, 1)  # 이미 pending

    def test_preflight_rejections(self):
        make_repo(self.root, tasks=[{"title": "no verifier", "goal": "g", "estimate_minutes": 10}])
        p = self.night(check=False)
        self.assertEqual(p.returncode, 2)
        self.assertIn("I5", p.stderr)
        (self.root / ".harness" / "plan.json").write_text(json.dumps({"tasks": PLAN[:1]}))
        p = self.night(check=False)
        self.assertEqual(p.returncode, 2)
        self.assertIn("clean", p.stderr)


if __name__ == "__main__":
    unittest.main()
