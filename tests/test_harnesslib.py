"""harnesslib 단위 테스트 — 부기 코어의 결정론을 고정한다."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "runner"))
import harnesslib as H  # noqa: E402
from _util import git_init  # noqa: E402


def task(id, title="t", verify="true", est=10, deps=(), prio=0, origin="plan"):
    return H.Task(id=id, title=title, goal="g", verify=verify, estimate_minutes=est, depends_on=list(deps), priority=prio, origin=origin)


def ev(event, ts=None, **k):
    d = {"ts": ts or H.iso(H.now()), "event": event}
    d.update(k)
    return d


class IdTests(unittest.TestCase):
    def test_next_id_from_log_and_plan(self):
        events = [ev("night_started", night="night-002"), ev("task_started", night="night-002", task="task-007")]
        tasks = [task("task-009"), task(None)]
        self.assertEqual(H.next_id("night", events), "night-003")
        self.assertEqual(H.next_id("task", events, tasks), "task-010")
        self.assertEqual(H.next_id("task", []), "task-001")

    def test_assign_ids_and_index_deps(self):
        tasks = [task(None, "a"), task(None, "b", deps=["#0"]), task("task-005", "c", deps=["#1"])]
        new = H.assign_ids(tasks, [ev("task_started", task="task-003")])
        self.assertEqual([t.id for t in new], ["task-006", "task-007"])
        self.assertEqual(tasks[1].depends_on, ["task-006"])
        self.assertEqual(tasks[2].depends_on, ["task-007"])


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.domain = H.Domain({})

    def test_gate_rejects_missing_verifier_and_bad_estimates(self):
        errs = H.validate_plan([task("task-001", verify=""), task("task-002", est=45), task("task-003", est=2)], self.domain)
        self.assertTrue(any("I5" in e for e in errs))
        self.assertTrue(any("task-002" in e and "5~30" in e for e in errs))
        self.assertTrue(any("task-003" in e for e in errs))

    def test_gate_rejects_unknown_dep_dup_id_and_cycle(self):
        errs = H.validate_plan([task("task-001", deps=["task-009"]), task("task-001")], self.domain)
        self.assertTrue(any("depends_on" in e for e in errs))
        self.assertTrue(any("중복" in e for e in errs))
        errs = H.validate_plan([task("task-001", deps=["task-002"]), task("task-002", deps=["task-001"])], self.domain)
        self.assertTrue(any("순환" in e for e in errs))

    def test_gate_accepts_good_plan(self):
        self.assertEqual(H.validate_plan([task("task-001"), task("task-002", deps=["task-001"])], self.domain), [])


class StateTests(unittest.TestCase):
    def test_fold(self):
        events = [
            ev("task_enqueued", task="task-001"), ev("task_started", task="task-001", attempt=1, night="night-001"),
            ev("task_failed", task="task-001", attempt=1, stage="leaf", reason="exit 1"),
            ev("task_started", task="task-001", attempt=2, night="night-001"),
            ev("task_passed", task="task-001", attempt=2, commit="abc"),
            ev("task_started", task="task-002", attempt=1, night="night-001"),
        ]
        st = H.derive_states(events, [task("task-001"), task("task-002"), task("task-003")])
        self.assertEqual(st["task-001"].state, "passed")
        self.assertEqual((st["task-001"].attempts, st["task-001"].failures, st["task-001"].commit), (2, 1, "abc"))
        self.assertEqual(st["task-002"].state, "started")
        self.assertEqual(st["task-003"].state, "pending")
        self.assertEqual([s.id for s in H.dangling_started(st)], ["task-002"])


class SelectTests(unittest.TestCase):
    def setUp(self):
        self.domain = H.Domain({"budget": {"starvation_minutes": 60, "max_attempts": 3}})
        self.now = H.now()

    def enq(self, tid, minutes_ago):
        return ev("task_enqueued", ts=H.iso(self.now - timedelta(minutes=minutes_ago)), task=tid)

    def test_priority_then_failures_then_fifo(self):
        tasks = [task("task-001", prio=1), task("task-002", prio=5), task("task-003", prio=5)]
        events = [self.enq("task-001", 10), self.enq("task-002", 10), self.enq("task-003", 9),
                  ev("task_started", task="task-002"), ev("task_failed", task="task-002")]
        order = [t.id for t in H.rank(tasks, H.derive_states(events, tasks), self.domain, self.now)]
        self.assertEqual(order, ["task-003", "task-002", "task-001"])

    def test_starving_task_beats_priority(self):
        tasks = [task("task-001", prio=0), task("task-002", prio=99)]
        events = [self.enq("task-001", 90), self.enq("task-002", 1)]
        self.assertEqual(H.select_next(tasks, H.derive_states(events, tasks), self.domain, self.now).id, "task-001")

    def test_repair_first_even_if_others_starve(self):
        tasks = [task("task-001", prio=0), task("task-009", origin="repair", est=5)]
        events = [self.enq("task-001", 500), self.enq("task-009", 0)]
        self.assertEqual(H.select_next(tasks, H.derive_states(events, tasks), self.domain, self.now).id, "task-009")

    def test_deps_budget_and_blocked(self):
        tasks = [task("task-001", est=25), task("task-002", deps=["task-001"]), task("task-003", est=5)]
        events = [self.enq("task-001", 1), self.enq("task-002", 1), self.enq("task-003", 1)]
        st = H.derive_states(events, tasks)
        self.assertEqual([t.id for t in H.eligible(tasks, st, self.domain)], ["task-001", "task-003"])
        self.assertEqual([t.id for t in H.eligible(tasks, st, self.domain, remaining_minutes=10)], ["task-003"])
        events += [ev("task_started", task="task-003"), ev("task_failed", task="task-003")] * 3 + [ev("task_blocked", task="task-003")]
        events += [ev("task_started", task="task-001"), ev("task_passed", task="task-001", commit="x")]
        st = H.derive_states(events, tasks)
        self.assertEqual([t.id for t in H.eligible(tasks, st, self.domain)], ["task-002"])


class ScopeTests(unittest.TestCase):
    def test_bash_write_targets(self):
        self.assertEqual(H.bash_write_targets("cat > tests/x.py <<'EOF'\nprint(1)\nEOF"), ["tests/x.py"])
        self.assertEqual(H.bash_write_targets("python -m pytest -q 2>&1 | tee out.log"), ["out.log"])
        self.assertEqual(H.bash_write_targets("echo hi > /dev/null; ls 2>&1 >&2"), [])
        self.assertEqual(H.bash_write_targets("cp a.py b/c.py && mv d e && touch f.txt"), ["b/c.py", "e", "f.txt"])
        self.assertEqual(H.bash_write_targets("sed -i '' 's/a/b/' src/m.py"), ["src/m.py"])
        self.assertEqual(H.bash_write_targets("grep -c '>' file.txt"), [])

    def test_scope_violations(self):
        d = H.Domain({"write_scope": ["tests"]})
        changed = ["tests/t.py", "src/x.py", ".harness/log.jsonl", ".harness/plan.json", ".harness/sessions/n/x", "evil.py"]
        self.assertEqual(H.scope_violations(d, changed), ["src/x.py", ".harness/plan.json", "evil.py"])
        self.assertEqual(H.scope_violations(H.Domain({}), changed), [".harness/plan.json"])


class VerifyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = H.Repo(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_level0(self):
        self.assertTrue(H.run_verify(self.repo, "true", 5).ok)
        r = H.run_verify(self.repo, "echo boom; exit 3", 5)
        self.assertFalse(r.ok)
        self.assertEqual((r.exit, r.reason), (3, "exit 3"))
        self.assertIn("boom", r.tail)

    def test_level1_metric(self):
        self.assertTrue(H.run_verify(self.repo, {"cmd": "echo 'acc 0.95'", "metric": {"min": 0.9}}, 5).ok)
        r = H.run_verify(self.repo, {"cmd": "echo 0.5", "metric": {"min": 0.9}}, 5)
        self.assertFalse(r.ok)
        self.assertEqual(r.metric, 0.5)
        self.assertFalse(H.run_verify(self.repo, {"cmd": "echo nope", "metric": {"max": 1}}, 5).ok)

    def test_timeout_kills_process_group(self):
        t0 = time.time()
        code, out, secs, to = H.run_shell("sleep 30 & sleep 30", self.repo.root, 0.5)
        self.assertTrue(to)
        self.assertLess(time.time() - t0, 5)

    def test_missing_verifier(self):
        self.assertFalse(H.run_verify(self.repo, None, 5).ok)


class GitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.git = H.Git(self.root)
        git_init(self.root)
        (self.root / "a.txt").write_text("v1\n")
        (self.root / ".harness").mkdir()
        (self.root / ".harness" / ".gitignore").write_text("sessions/\n")
        (self.root / ".harness" / "log.jsonl").write_text('{"event":"x"}\n')
        self.assertIsNotNone(self.git.commit_all("init"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_revert_preserves_harness_dir_and_saves_patch(self):
        (self.root / "a.txt").write_text("v2\n")
        (self.root / "new.txt").write_text("n\n")
        with (self.root / ".harness" / "log.jsonl").open("a") as f:
            f.write('{"event":"y"}\n')
        patch = self.root / ".harness" / "sessions" / "night-001" / "task-001.1.patch"
        self.assertTrue(self.git.save_patch(patch))
        text = patch.read_text()
        self.assertIn("v2", text)
        self.assertIn("new.txt", text)
        self.assertNotIn("log.jsonl", text)
        self.git.revert_worktree()
        self.assertEqual((self.root / "a.txt").read_text(), "v1\n")
        self.assertFalse((self.root / "new.txt").exists())
        self.assertEqual((self.root / ".harness" / "log.jsonl").read_text().count("\n"), 2)
        self.assertTrue(patch.exists())

    def test_changed_paths_includes_untracked_and_renames(self):
        (self.root / "a.txt").write_text("v2\n")
        (self.root / "new.txt").write_text("n\n")
        with (self.root / ".harness" / "log.jsonl").open("a") as f:
            f.write('{"event":"y"}\n')
        self.assertEqual(sorted(self.git.changed_paths()), [".harness/log.jsonl", "a.txt", "new.txt"])
        self.git.run("mv", "a.txt", "renamed.txt")
        self.assertIn("renamed.txt", self.git.changed_paths())
        self.assertNotIn("a.txt", self.git.changed_paths())

    def test_night_branches_and_ancestry(self):
        self.assertEqual(self.git.night_branches(), [])
        self.git.create_branch("harness/night-002")
        self.git.create_branch("harness/night-010")
        self.assertEqual([n for n, _ in self.git.night_branches()], [2, 10])
        self.assertTrue(self.git.is_ancestor("main", "harness/night-010"))
        self.assertIsNone(self.git.commit_all("nothing"))


class SummaryTests(unittest.TestCase):
    def test_render_counts_and_anomalies(self):
        tasks = [task("task-001", "one"), task("task-002", "two"), task("task-003", "three")]
        n = "night-004"
        events = [
            ev("night_started", night=n, branch="harness/night-004"),
            ev("task_enqueued", night=n, task="task-001"), ev("task_enqueued", night=n, task="task-002"), ev("task_enqueued", night=n, task="task-003"),
            ev("task_started", night=n, task="task-001", attempt=1),
            ev("model_done", night=n, task="task-001", attempt=1, edits={"x.py": 11}, cost_usd=1.5, seconds=30),
            ev("task_passed", night=n, task="task-001", attempt=1, commit="abc1234"),
            ev("task_started", night=n, task="task-002", attempt=1),
            ev("task_failed", night=n, task="task-002", attempt=1, stage="leaf", reason="exit 1", tail="Error: boom"),
            ev("task_blocked", night=n, task="task-002", attempts=1, reason="3회 연속 검증 실패"),
            ev("night_ended", night=n, reason="budget"),
        ]
        c = H.collect_night(events, tasks, H.Domain({}), n)
        text = H.render_summary(c)
        self.assertIn("# night-004", text)
        self.assertIn("완료 1 / 실패(재시도 예정) 0 / 막힘 1 / 미착수 1", text)
        self.assertIn("task-001 one — 커밋 `abc1234`", text)
        self.assertIn("doom loop 의심: task-001 같은 파일 11회 편집 (x.py)", text)
        self.assertIn("1. task-003 three", text)
        self.assertIn("$1.50", text)
        blocked = H.render_blocked(events, tasks)
        self.assertIn("## task-002 two", blocked)
        self.assertIn("Error: boom", blocked)


if __name__ == "__main__":
    unittest.main()
