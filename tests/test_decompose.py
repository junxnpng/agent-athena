"""decompose --propose / queue accept / night-loop 제안 연결 — fake 드라이버로 P7-lite 를 끝까지 돌린다."""
from __future__ import annotations

import json
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

DECOMPOSE = str(ROOT / "runner" / "decompose")
QUEUE = str(ROOT / "runner" / "queue")
NIGHT = str(ROOT / "runner" / "night")
LOOP = str(ROOT / "runner" / "night-loop")


class JsonBlockTests(unittest.TestCase):
    def test_last_fenced_block_wins_and_trailing_result_line_is_ignored(self):
        text = "생각…\n```json\n{\"tasks\": []}\n```\n더 생각…\n```json\n{\"rationale\": \"r\", \"tasks\": [{\"title\": \"t\"}]}\n```\nRESULT: done — 제안 1개"
        self.assertEqual(H.extract_json_block(text)["tasks"][0]["title"], "t")
        self.assertIsNone(H.extract_json_block("no json here"))
        self.assertEqual(H.extract_json_block('prose {"a": {"b": 1}} tail')["a"]["b"], 1)  # 펜스 없는 마지막 객체
        self.assertIsNone(H.extract_json_block("```json\n[1, 2]\n```"))  # 객체가 아니면 None

    def test_offset_deps_only_rewrites_index_refs(self):
        t = H.task_from_json({"title": "b", "goal": "g", "verify": "true", "estimate_minutes": 5, "depends_on": ["#1", "task-003"]})
        H.offset_deps([t], 12)
        self.assertEqual(t.depends_on, ["#13", "task-003"])


class ProposeE2E(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.env = dict(os.environ, HARNESS_FAKE_MODEL=FAKE)
        self.env.pop("HARNESS_NIGHT", None)
        self.env.pop("HARNESS_FAKE_PROPOSAL", None)

    def tearDown(self):
        self.tmp.cleanup()

    def run_(self, *args, check=False):
        return sh("python3", *args, "--repo", str(self.root), env=self.env, check=check)

    def test_propose_filters_vacuous_then_accept_then_night_passes(self):
        make_repo(self.root, tasks=[])
        p = self.run_(DECOMPOSE, "--propose", "--driver", "fake")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        repo = H.Repo(self.root)
        meta, proposed = H.read_proposed(repo)
        self.assertEqual([t.title for t in proposed], ["[add-mul] mul 추가 (제안)"])  # `true` 검증기 작업은 빈 작업이라 버려졌다
        self.assertEqual(meta["dropped"][0]["reason"], "검증기가 지금 이미 통과한다 — 빈 작업")
        ev = [e for e in H.read_log(repo.log) if e["event"] == "plan_proposed"][-1]
        self.assertEqual((ev["ok"], ev["proposed"], ev["kept"], ev["dropped"], ev["round"]), (True, 2, 1, 1, 1))
        self.assertTrue(sh("git", "-C", str(self.root), "log", "-1", "--format=%s").stdout.startswith("[harness] plan proposal 1"))
        self.assertEqual(sh("git", "-C", str(self.root), "status", "--porcelain").stdout, "")  # 부기 커밋으로 트리는 clean
        st = self.run_(QUEUE, "status")
        self.assertIn("제안 대기: 1개", st.stdout)
        # plan.json 은 아직 그대로 — 제안은 채택 전까지 계획이 아니다
        self.assertEqual(json.loads(repo.plan.read_text())["tasks"], [])
        ac = self.run_(QUEUE, "accept", "--all")
        self.assertEqual(ac.returncode, 0, ac.stdout + ac.stderr)
        self.assertIn("채택: task-001", ac.stdout)
        self.assertFalse(repo.proposed.exists())
        _, tasks = H.load_plan(repo)
        self.assertEqual([(t.id, t.origin) for t in tasks], [("task-001", "proposal")])
        self.assertEqual([e for e in H.read_log(repo.log) if e["event"] == "plan_accepted"][-1]["ids"], ["task-001"])
        n = self.run_(NIGHT, "--driver", "fake")
        self.assertEqual(n.returncode, 0, n.stdout + n.stderr)
        states = H.derive_states(H.read_log(repo.log), tasks)
        self.assertEqual(states["task-001"].state, "passed")

    def test_accept_rejects_partial_pick_with_missing_dependency(self):
        make_repo(self.root, tasks=[])
        self.env["HARNESS_FAKE_PROPOSAL"] = json.dumps({"tasks": [
            {"title": "a", "goal": "g", "verify": "test -f A", "estimate_minutes": 5},
            {"title": "b", "goal": "g", "verify": "test -f B", "estimate_minutes": 5, "depends_on": ["#0"]},
        ]})
        self.assertEqual(self.run_(DECOMPOSE, "--propose", "--driver", "fake").returncode, 0)
        bad = self.run_(QUEUE, "accept", "1")
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("수락 목록에 없다", bad.stderr)
        ok = self.run_(QUEUE, "accept", "--all")
        self.assertEqual(ok.returncode, 0, ok.stderr)
        _, tasks = H.load_plan(H.Repo(self.root))
        self.assertEqual(tasks[1].depends_on, ["task-001"])  # '#0' → 발급된 id

    def test_invalid_proposal_is_rejected_without_touching_plan(self):
        make_repo(self.root, tasks=[])
        self.env["HARNESS_FAKE_PROPOSAL"] = json.dumps({"tasks": [{"title": "no verify", "goal": "g", "estimate_minutes": 5}]})
        p = self.run_(DECOMPOSE, "--propose", "--driver", "fake")
        self.assertEqual(p.returncode, 1)
        self.assertIn("verify 없음", p.stderr)
        self.assertFalse(H.Repo(self.root).proposed.exists())


class LoopProposeE2E(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.env = dict(os.environ, HARNESS_FAKE_MODEL=FAKE)
        self.env.pop("HARNESS_NIGHT", None)

    def tearDown(self):
        self.tmp.cleanup()

    def loop(self):
        return sh("python3", LOOP, "--repo", str(self.root), "--wait-minutes", "0", "--max-total-usd", "100", "--driver", "fake", env=self.env, check=False)

    def test_auto_propose_and_accept_chain_until_nothing_left(self):
        make_repo(self.root, tasks=[], domain={"plan": {"auto_propose": True, "auto_accept": True, "max_rounds": 3}})
        p = self.loop()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        events = H.read_log(H.Repo(self.root).log)
        self.assertEqual([e["reason"] for e in events if e["event"] == "night_ended"], ["queue_empty", "queue_empty"])
        rounds = [e for e in events if e["event"] == "plan_proposed"]
        self.assertEqual([(r["ok"], r["kept"]) for r in rounds], [(True, 1), (True, 0)])  # 2회차: mul 이 이미 통과 → 제안 0 → 멈춤
        self.assertIn("제안 채택 (auto_accept)", p.stdout)
        self.assertIn("루프 종료 (queue_empty) · 밤 2개", p.stdout)
        _, tasks = H.load_plan(H.Repo(self.root))
        self.assertEqual([(t.id, t.origin) for t in tasks], [("task-001", "proposal")])
        self.assertEqual(H.derive_states(events, tasks)["task-001"].state, "passed")

    def test_without_auto_accept_loop_stops_pending_for_human(self):
        make_repo(self.root, tasks=[], domain={"plan": {"auto_propose": True, "auto_accept": False}})
        p = self.loop()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("루프 종료 (proposal_pending)", p.stdout)
        self.assertTrue(H.Repo(self.root).proposed.exists())

    def test_default_domain_never_proposes(self):
        make_repo(self.root, tasks=[])
        p = self.loop()
        self.assertIn("루프 종료 (queue_empty) · 밤 1개", p.stdout)
        self.assertFalse(H.Repo(self.root).proposed.exists())


if __name__ == "__main__":
    unittest.main()
