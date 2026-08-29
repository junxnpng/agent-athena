"""verify-doc — 산출물 결정론 검증기 (D3). 각 검사의 통과/실패를 임시 파일로 고정한다."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VD = str(ROOT / "runner" / "verify-doc")

GOOD = """---
title: 실험 노트 1
status: draft
tags: [a, b]
---
# 실험 노트

## 방법
[설계 문서](design.md) 를 따랐다. 결과는 [[notes]] 참고. 외부: https://example.com/x

## 결과
| 지표 | 값 |
|---|---|
| p50 | 12.5 |
| p99 | 1,024 |

근거는 [@kim2024] 와 \\cite{lee2023,park2022} 이다.
"""


class VerifyDocTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        (self.root / "design.md").write_text("# d\n", encoding="utf-8")
        (self.root / "notes.md").write_text("# n\n", encoding="utf-8")
        (self.root / "refs.bib").write_text("@article{kim2024, title={x}}\n@inproceedings{ lee2023 , title={y}}\n@misc{park2022,}\n", encoding="utf-8")
        (self.root / "data.csv").write_text("metric,value\np50,12.5\np99,1024\n", encoding="utf-8")
        (self.root / "data.json").write_text('{"p50": 12.5, "nested": {"p99": "1,024"}}', encoding="utf-8")
        self.doc = self.root / "note.md"
        self.doc.write_text(GOOD, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_(self, *args):
        return subprocess.run([sys.executable, VD, str(self.doc), "--root", str(self.root), *args], capture_output=True, text=True, encoding="utf-8")

    def test_full_pass(self):
        p = self.run_("--require-keys", "title,status", "--sections", "방법,결과", "--bib", str(self.root / "refs.bib"),
                      "--data", str(self.root / "data.csv"), "--min-words", "10")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("verify-doc: ok", p.stdout)
        self.assertEqual(self.run_("--data", str(self.root / "data.json")).returncode, 0)  # JSON 중첩·"1,024" 문자열도 숫자로

    def test_each_failure_is_named(self):
        p = self.run_("--require-keys", "title,author", "--sections", "방법,논의", "--bib", str(self.root / "refs.bib"), "--min-words", "500")
        self.assertEqual(p.returncode, 1)
        for needle in ("frontmatter 키 없음/비어 있음: author", "필수 섹션 없음: 논의", "단어 수"):
            self.assertIn(needle, p.stdout)
        self.assertNotIn("인용 키가 bib 에 없다", p.stdout)

    def test_missing_link_citation_and_number_are_caught(self):
        self.doc.write_text(GOOD.replace("design.md", "gone.md").replace("[[notes]]", "[[nowhere]]").replace("kim2024", "ghost2020").replace("12.5", "13.7"), encoding="utf-8")
        p = self.run_("--bib", str(self.root / "refs.bib"), "--data", str(self.root / "data.csv"))
        self.assertEqual(p.returncode, 1)
        for needle in ("링크 대상 없음: gone.md", "위키링크 대상 없음: [[nowhere]]", "인용 키가 bib 에 없다: ghost2020", "표의 숫자가 데이터에 없다: 13.7"):
            self.assertIn(needle, p.stdout)

    def test_frontmatter_required_by_default(self):
        self.doc.write_text("# 제목\n\n본문\n", encoding="utf-8")
        self.assertEqual(self.run_().returncode, 1)
        self.assertIn("frontmatter 없음", self.run_().stdout)
        self.assertEqual(self.run_("--no-frontmatter").returncode, 0)

    def test_missing_file(self):
        self.doc = self.root / "nope.md"
        p = self.run_()
        self.assertEqual(p.returncode, 1)
        self.assertIn("파일 없음", p.stdout)


if __name__ == "__main__":
    unittest.main()
