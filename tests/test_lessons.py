"""A1 무변경 시도 억제 + B1 refine-lite (prime-agent 리뷰 도입분, 2026-09-02) — 단위 + fake 드라이버 e2e."""
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
import harnesslib as H  # noqa: E402
import drivers as D  # noqa: E402

from fixtures import FAKE, NIGHT, PLAN, make_repo, sh  # noqa: E402

NOOP_PLAN = [  # fake_model 이 모르는 태그 — 트리를 전혀 바꾸지 않는다 (A1)
    {"title": "[noop] 아무것도 안 바꾸는 작업", "goal": "x", "verify": "test -f NEVER_EXISTS", "estimate_minutes": 5, "priority": 1},
]


def lessons_json(*items):
    return json.dumps({"lessons": list(items)}, ensure_ascii=False)


class LessonsUnit(unittest.TestCase):
    def repo(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root / ".harness").mkdir()
        self.addCleanup(self.tmp.cleanup)
        return H.Repo(root)

    def test_parse_lessons_enforces_caps_and_evidence(self):
        text = "떠들기\n```json\n%s\n```\n" % lessons_json(
            {"title": "정상", "evidence": "막힘 task-001", "suggestion": "고쳐라", "target": "prompts"},
            {"title": "증거 없음 — 버려진다", "evidence": "", "suggestion": "s", "target": "spec"},
            {"title": "이상한 target", "evidence": "e", "suggestion": "s", "target": "sudo rm -rf"},
            {"title": "T" * 300, "evidence": "E" * 900, "suggestion": "S" * 900, "target": "spec"},
            {"title": "상한 밖 — 잘린다", "evidence": "e", "suggestion": "s", "target": "spec"},
        )
        out = H.parse_lessons(text, max_items=3)
        self.assertEqual(len(out), 3)  # 증거 없는 1건 버림 + max 3 절단
        self.assertEqual(out[0]["title"], "정상")
        self.assertEqual(out[1]["target"], "other")           # 모르는 target 은 other
        self.assertEqual(len(out[2]["title"]), H.LESSON_MAX_TITLE)
        self.assertEqual(len(out[2]["evidence"]), H.LESSON_MAX_TEXT)
        self.assertEqual(H.parse_lessons("json 블록 없음", 3), [])
        self.assertEqual(H.parse_lessons("```json\n{\"lessons\": \"객체 아님\"}\n```", 3), [])

    def test_write_lessons_keeps_recent_nights_and_replaces_same_night(self):
        repo = self.repo()
        les = [{"title": "t", "evidence": "e", "suggestion": "s", "target": "prompts"}]
        for n in ("night-001", "night-002", "night-003", "night-004"):
            H.write_lessons(repo, n, les, keep_nights=3)
        body = repo.lessons.read_text(encoding="utf-8")
        self.assertIn("## night-004", body)
        self.assertIn("## night-002", body)
        self.assertNotIn("## night-001", body)                # 밀려났다 (무상한 축적 금지)
        self.assertLess(body.index("## night-004"), body.index("## night-003"))  # 새 밤이 위
        H.write_lessons(repo, "night-004", [{"title": "교체됨", "evidence": "e", "suggestion": "s", "target": "spec"}], keep_nights=3)
        body = repo.lessons.read_text(encoding="utf-8")
        self.assertEqual(body.count("## night-004"), 1)       # 같은 밤 재실행은 교체지 중복 아님
        self.assertIn("교체됨", body)
        self.assertNotIn("### t →", body.split("## night-003")[0])

    def test_lesson_evidence_picks_failure_signals_and_caps(self):
        tasks = [H.Task(id="task-001", title="제목", goal="g", verify="true", estimate_minutes=5)]
        ev = [
            {"event": "task_blocked", "task": "task-001", "reason": "3회 연속 검증 실패"},
            {"event": "task_failed", "task": "task-001", "attempt": 2, "noop": True},
            {"event": "task_failed", "task": "task-001", "attempt": 3, "infra": True, "reason": "머신 잠듦"},
            {"event": "scope_violation", "task": "task-001", "attempt": 1, "paths": ["evil.py"]},
            {"event": "model_done", "task": "task-001", "attempt": 1, "denials": 5},
            {"event": "smoke", "ok": False, "tail": "AssertionError: boom"},
            {"event": "task_passed", "task": "task-001"},     # 통과는 교훈감이 아니다
        ]
        lines = "\n".join(H.lesson_evidence(ev, tasks))
        for frag in ("막힘 task-001", "무변경 시도", "인프라", "범위 위반", "훅 거부 5회", "스모크 실패"):
            self.assertIn(frag, lines)
        self.assertEqual(H.lesson_evidence([{"event": "task_passed", "task": "task-001"}], tasks), [])
        many = [{"event": "scope_violation", "task": "task-001", "attempt": i, "paths": ["x"]} for i in range(40)]
        self.assertEqual(len(H.lesson_evidence(many, tasks)), H.LESSON_MAX_EVIDENCE_LINES)

    def test_close_orphaned_lessons(self):
        repo = self.repo()
        H.append_event(repo.log, "lessons_started", night="night-007", stream="s")
        n = H.close_orphaned_proposals(repo)
        self.assertEqual(n, 1)
        last = H.read_log(repo.log)[-1]
        self.assertEqual((last["event"], last["night"], last["ok"]), ("lessons_proposed", "night-007", False))
        self.assertEqual(H.close_orphaned_proposals(repo), 0)  # 멱등

    def test_model_changed_paths_excludes_runner_bookkeeping(self):
        changed = [".harness/log.jsonl", ".harness/sessions/night-001/x.stream.jsonl", "calc.py", ".harness/domain.json"]
        self.assertEqual(H.model_changed_paths(changed), ["calc.py", ".harness/domain.json"])
        self.assertEqual(H.model_changed_paths([".harness/log.jsonl"]), [])  # noop 판정: 러너 로그만 바뀐 건 무변경

    def test_day_cost_includes_lessons(self):
        ts = H.iso(H.now())
        events = [{"ts": ts, "event": "model_done", "cost_usd": 1.0},
                  {"ts": ts, "event": "lessons_proposed", "cost_usd": 0.25}]
        self.assertAlmostEqual(H.day_cost_usd(events), 1.25)

    def _history_of(self, failure):
        ctx = D.TaskContext(repo=H.Repo(Path(".")), domain=H.Domain({}), night_id="night-001",
                            task=H.Task(id="task-001", title="t", goal="g", verify="true", estimate_minutes=5),
                            state=H.TaskState(id="task-001", failure_history=[failure]), attempt=2,
                            timeout_minutes=5, deadline_epoch=0, spec_text="")
        return D._history(ctx)

    def test_history_marks_noop_attempts(self):  # A2
        text = self._history_of({"attempt": 1, "night": "night-001", "stage": "leaf", "reason": "무변경 시도 — …; leaf verify exit 1", "noop": True})
        self.assertIn("트리를 전혀 바꾸지 않았다", text)
        self.assertIn("실제 변경을 만들어라", text)

    def test_history_warns_after_interrupted_attempt(self):  # A3
        text = self._history_of({"attempt": 1, "night": "night-001", "stage": "interrupted", "infra": True, "reason": "러너 중단"})
        self.assertIn("판정 없이 중단", text)
        self.assertIn("트리 밖 부작용", text)
        self.assertNotIn("실제 변경을 만들어라", text)  # noop 아님 — noop 전용 문구는 없다


class LessonsE2E(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.env = dict(os.environ, HARNESS_FAKE_MODEL=FAKE)
        self.env.pop("HARNESS_NIGHT", None)

    def tearDown(self):
        self.tmp.cleanup()

    def night(self, *extra, check=True):
        return sh("python3", NIGHT, "--repo", str(self.root), "--driver", "fake", *extra, env=self.env, check=check)

    def test_noop_attempts_skip_verify_and_get_explicit_reason(self):  # A1 + A2 + B1 경로
        make_repo(self.root, tasks=NOOP_PLAN)
        p = self.night()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        repo = H.Repo(self.root)
        events = H.read_log(repo.log)
        _, tasks = H.load_plan(repo)
        st = H.derive_states(events, tasks)["task-001"]
        self.assertEqual((st.state, st.failures), ("blocked", 3))
        verifies = [e for e in events if e.get("event") == "verify" and e.get("task") == "task-001"]
        self.assertEqual(len(verifies), 3)
        self.assertEqual([bool(e.get("cached")) for e in verifies], [False, True, True])  # 1회 실행 + 2회 생략
        self.assertTrue(all(e.get("noop") for e in events if e.get("event") == "task_failed"))
        self.assertIn("무변경 시도", st.last_failure["reason"])
        summary = repo.summary.read_text(encoding="utf-8")
        self.assertIn("무변경 시도 3회: task-001", summary)
        # B1: 막힘+무변경이 교훈감 → fake 기본 교훈이 제안된다
        les = next(e for e in reversed(events) if e.get("event") == "lessons_proposed")
        self.assertEqual((les["ok"], les["count"], les["titles"]), (True, 1, ["fake 교훈"]))
        self.assertIn("fake 교훈", repo.lessons.read_text(encoding="utf-8"))
        self.assertIn("## 제안된 교훈", summary)
        self.assertIn("fake 교훈", summary)
        # 부기 커밋에 포함 — 트리는 clean
        self.assertEqual(sh("git", "-C", str(self.root), "status", "--porcelain").stdout, "")

    def test_lessons_env_override_and_caps(self):
        make_repo(self.root, tasks=NOOP_PLAN)
        items = [{"title": "교훈%d" % i, "evidence": "e", "suggestion": "s", "target": "spec"} for i in range(6)]
        self.env["HARNESS_FAKE_LESSONS"] = lessons_json(*items)
        self.night()
        repo = H.Repo(self.root)
        les = next(e for e in reversed(H.read_log(repo.log)) if e.get("event") == "lessons_proposed")
        self.assertEqual(les["count"], 3)  # domain 기본 max=3 — 코드가 자른다
        self.assertEqual(len(les["titles"]), 3)

    def test_lessons_disabled_by_domain(self):
        make_repo(self.root, tasks=NOOP_PLAN, domain={"lessons": {"propose": False}})
        self.night()
        events = H.read_log(H.Repo(self.root).log)
        self.assertFalse([e for e in events if e.get("event", "").startswith("lessons_")])
        self.assertFalse(H.Repo(self.root).lessons.exists())

    def test_lessons_skipped_without_evidence(self):
        make_repo(self.root, tasks=PLAN[:2])  # 전부 통과하는 밤 — 교훈감 없음, 모델을 부르지 않는다
        p = self.night()
        self.assertIn("교훈 제안 생략", p.stdout)
        events = H.read_log(H.Repo(self.root).log)
        self.assertFalse([e for e in events if e.get("event", "").startswith("lessons_")])
        self.assertFalse(H.Repo(self.root).lessons.exists())


if __name__ == "__main__":
    unittest.main()
