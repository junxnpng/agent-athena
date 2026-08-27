#!/usr/bin/env python3
"""가짜 모델 — e2e 테스트용 드라이버 스크립트. 작업 JSON을 stdin으로 받아 제목의 태그대로 트리를 바꾼다.

태그: [add-mul] [add-sub] [hopeless] [break-global] [repair]
출력 규약: "EDIT <path>" 줄 = 편집 1회 (P9 카운터), 마지막 줄 "RESULT: ..." = 자기 보고 (판정 아님).
"""
import json
import os
import sys
from pathlib import Path

d = json.load(sys.stdin)
t = d["task"]
title = t["title"]
root = Path(os.environ["HARNESS_REPO"])
calc = root / "calc.py"

if "[add-mul]" in title:
    calc.write_text(calc.read_text() + "\n\ndef mul(a, b):\n    return a * b\n")
    print("EDIT calc.py")
elif "[add-sub]" in title:
    calc.write_text(calc.read_text() + "\n\ndef sub(a, b):\n    return a - b\n")
    print("EDIT calc.py")
elif "[hopeless]" in title:
    # 헛도는 모델 흉내: 같은 파일을 9번 만진다 → doom loop 신호
    for _ in range(9):
        print("EDIT notes.txt")
    (root / "notes.txt").write_text("attempt %s\n" % d["attempt"])
elif "[break-global]" in title:
    # 리프는 통과하지만 전체 검증을 깨뜨린다
    (root / "wanted.txt").write_text("leaf ok\n")
    (root / "test_calc.py").write_text((root / "test_calc.py").read_text() + "\n\ndef test_broken():\n    assert False\n")
    print("EDIT wanted.txt")
    print("EDIT test_calc.py")
elif "복구" in title or "[repair]" in title:
    (root / "FIXED").write_text("fixed\n")
    print("EDIT FIXED")
print("RESULT: done — fake model (%s)" % title)
