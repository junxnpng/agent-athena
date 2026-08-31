"""테스트 공용 픽스처 — e2e 계열 5개 파일이 같이 쓴다 (test_e2e 에서 분리: 테스트 모듈을 서로 import 하지 않는다, 리뷰 라운드 1 잔여)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "runner"))
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
