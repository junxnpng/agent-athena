#!/usr/bin/env python3
"""가짜 모델 — e2e 테스트용 드라이버 스크립트. 작업 JSON을 stdin으로 받아 제목의 태그대로 트리를 바꾼다.

태그: [add-mul] [add-sub] [hopeless] [break-global] [repair] [cost:N]
제안 모드: task.id == "propose" 면 HARNESS_FAKE_PROPOSAL(JSON 문자열)을, 없으면 기본 제안(mul 작업 + 이미 통과하는 빈 작업)을 ```json 블록으로 낸다.
출력 규약: "EDIT <path>" 줄 = 편집 1회 (P9 카운터), "COST <usd>" 줄 = 비용 보고, "SKILL <이름>" 줄 = 스킬 자동 호출 1회, 마지막 줄 "RESULT: ..." = 자기 보고 (판정 아님).
"""
import json
import os
import re
import sys
from pathlib import Path

d = json.load(sys.stdin)
t = d["task"]
title = t["title"]
root = Path(os.environ["HARNESS_REPO"])
calc = root / "calc.py"

if t.get("id") == "propose":
    default = {"rationale": "fake 제안", "tasks": [
        {"title": "[add-mul] mul 추가 (제안)", "goal": "mul(a,b)", "verify": "python3 -c \"import calc; assert calc.mul(3,4)==12\"", "estimate_minutes": 5, "priority": 1},
        {"title": "빈 작업 — 검증기가 이미 통과한다", "goal": "x", "verify": "true", "estimate_minutes": 5, "priority": 0},
    ]}
    print("탐색 끝.\n```json\n%s\n```\nRESULT: done — 제안" % (os.environ.get("HARNESS_FAKE_PROPOSAL") or json.dumps(default, ensure_ascii=False)))
    sys.exit(0)
if "[add-mul]" in title:
    calc.write_text(calc.read_text() + "\n\ndef mul(a, b):\n    return a * b\n")
    print("EDIT calc.py")
    print("SKILL harness:test-driven-development")  # 스킬 호출 흉내 → 스트림 집계 → SUMMARY "스킬 자동 호출"
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
elif "[out-of-scope]" in title:
    # 쓰기 범위 밖에 파일을 만든다 (heredoc 흉내) — 러너가 git status 로 잡아야 한다
    (root / "evil.py").write_text("print('evil')\n")
    print("EDIT evil.py")
elif "복구" in title or "[repair]" in title:
    (root / "FIXED").write_text("fixed\n")
    print("EDIT FIXED")
m = re.search(r"\[cost:([0-9.]+)\]", title)
if m:
    print("COST " + m.group(1))
print("RESULT: done — fake model (%s)" % title)
