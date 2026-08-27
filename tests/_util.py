"""테스트 공용 — git 저장소 초기화 (git 2.25 호환: `init -b` 대신 symbolic-ref)."""
from __future__ import annotations

import subprocess
from pathlib import Path


def git_init(root: Path, branch: str = "main") -> None:
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "symbolic-ref", "HEAD", "refs/heads/" + branch], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "t"], check=True)
