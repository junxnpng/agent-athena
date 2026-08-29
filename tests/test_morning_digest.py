"""morning-digest — SUMMARY.md 파싱·수집·렌더·분할·전송(가짜 urlopen). 결정론 스크립트라 픽스처로 전부 고정한다."""
from __future__ import annotations

import importlib.machinery
import importlib.util
import io
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = str(ROOT / "scripts" / "morning-digest")

FRESH = """# night-002 · 2026-08-29 22:40 → 2026-08-29 22:50 (9m24s)

## 결론
완료 5 / 실패(재시도 예정) 0 / 막힘 0 / 미착수 0 · 종료: 큐 비움 · 브랜치 `harness/night-002` · 비용 $3.16

## 계획 DAG (✅통과 ⛔막힘 🔁재시도 ⬜미착수)
```mermaid
flowchart TD
  a["x"]
```

## 완료 (검증 통과)
- task-003 무엇 — 커밋 `c084844`

## 막힘 — BLOCKED.md 참조
- (없음)

## 실패 (다음 밤 재시도)
- task-009 수집기 (시도 2/2)

## 승인 대기 — 사람이 연다 (`runner/queue approve task-NNN`, 대화형에서는 '승인'·'시작해'·'진행해')
- task-002 게이트 1: 편집 방침 승인 — 뒤에 task-003, task-004

## 이상 징후
- task-004 7턴 · $0.66 — 느림
"""

OLD = """# night-024 · 2026-08-27 01:00 → 2026-08-27 03:10 (2h10m)

## 결론
완료 4 / 실패(재시도 예정) 1 / 막힘 0 / 미착수 6 · 종료: 예산 소진 · 브랜치 `harness/night-024` · 비용 $9.80

## 승인 대기 — 사람이 연다
- (없음)

## 이상 징후
- (없음)
"""


def load():
    loader = importlib.machinery.SourceFileLoader("morning_digest", SCRIPT)
    spec = importlib.util.spec_from_loader("morning_digest", loader)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


class MorningDigestTests(unittest.TestCase):
    def setUp(self):
        self.mod = load()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        for name, body in (("athena-a", FRESH), ("athena-b", OLD)):
            (self.root / name / ".harness").mkdir(parents=True)
            (self.root / name / ".harness" / "SUMMARY.md").write_text(body, encoding="utf-8")
        (self.root / "athena-c" / ".harness").mkdir(parents=True)  # 밤 없음
        (self.root / "not-a-repo").mkdir()
        self.now = datetime(2026, 8, 30, 7, 30)

    def tearDown(self):
        self.tmp.cleanup()

    def test_parse_summary(self):
        info = self.mod.parse_summary(FRESH)
        self.assertEqual(info["night"], "night-002")
        self.assertEqual(info["end"], "2026-08-29 22:50")
        self.assertIn("완료 5", info["conclusion"])
        self.assertNotIn("브랜치", info["conclusion"])
        self.assertEqual(info["gates"], ["task-002 게이트 1: 편집 방침 승인 — 뒤에 task-003, task-004"])
        self.assertEqual(info["blocked"], [])
        self.assertEqual(info["failed"], ["task-009 수집기 (시도 2/2)"])
        self.assertEqual(len(info["anomalies"]), 1)

    def test_collect_and_render(self):
        items = self.mod.collect(self.root, self.now, 24.0)
        self.assertEqual([i["repo"] for i in items], ["athena-a", "athena-b", "athena-c"])
        self.assertTrue(items[0]["fresh"])
        self.assertFalse(items[1]["fresh"])
        self.assertIsNone(items[2]["night"])
        text = self.mod.render(items, self.now)
        self.assertIn("athena-a — night-002 (22:40→22:50) 완료 5", text)
        self.assertIn("🔒 승인 대기: task-002", text)
        self.assertIn("🔁 실패: task-009", text)
        self.assertIn("⚠ 이상 징후:", text)
        self.assertIn("athena-b — 최근 밤 없음 (마지막 night-024, 2026-08-27)", text)
        self.assertIn("athena-c — 밤 없음", text)
        self.assertIn("합계: 지난 밤 1개 · $3.16 · 승인 대기 1개", text)

    def test_split_message(self):
        text = "\n".join("줄%03d" % i for i in range(1000))
        parts = self.mod.split_message(text, limit=50)
        self.assertTrue(all(len(p) <= 50 for p in parts))
        self.assertEqual("\n".join(parts), text)
        long = "x" * 120
        self.assertEqual(self.mod.split_message(long, limit=50), ["x" * 50, "x" * 50, "x" * 20])

    def test_send_uses_fixed_host_and_reports_parts(self):
        calls = []

        class Resp(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_urlopen(req, timeout=0):
            calls.append((req.full_url, json.loads(req.data.decode("utf-8")), timeout))
            return Resp(b'{"ok": true}')

        self.mod.urllib.request.urlopen = fake_urlopen
        n = self.mod.send("TOKEN", "123", "a\n" + "b" * 4500)
        self.assertEqual(n, 3)  # "a" / 4000 / 500 — 줄 경계 분할
        self.assertTrue(all(u.startswith("https://api.telegram.org/botTOKEN/sendMessage") for u, _, _ in calls))
        self.assertEqual(calls[0][1]["chat_id"], "123")

    def test_send_raises_on_not_ok(self):
        class Resp(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        self.mod.urllib.request.urlopen = lambda req, timeout=0: Resp(b'{"ok": false, "description": "bad"}')
        with self.assertRaises(RuntimeError):
            self.mod.send("T", "1", "x")

    def test_main_without_token_exits_2_but_prints(self):
        import contextlib
        import os
        old = {k: os.environ.pop(k, None) for k in ("HARNESS_BOT_TOKEN", "HARNESS_CHAT_ID")}
        try:
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = self.mod.main(["--root", str(self.root)])
            self.assertEqual(rc, 2)
            self.assertIn("아침 다이제스트", out.getvalue())
            self.assertIn("HARNESS_BOT_TOKEN", err.getvalue())
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(self.mod.main(["--root", str(self.root), "--dry-run"]), 0)
        finally:
            for k, v in old.items():
                if v is not None:
                    os.environ[k] = v


if __name__ == "__main__":
    unittest.main()
