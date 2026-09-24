"""Filesystem anchors. Everything is relative to the verify/ directory."""
from __future__ import annotations

import hashlib
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"
RESULTS_DIR = ROOT / "results"
DEFAULT_LEDGER = RESULTS_DIR / "verify-ledger.sqlite"
SOURCE_ENV = "KVCPOOL"


class SourceRootError(RuntimeError):
    pass


def source_root(value: str | None) -> pathlib.Path:
    """Resolve --source-root, falling back to the KVCPOOL environment variable."""
    value = value or os.environ.get(SOURCE_ENV)
    if not value:
        raise SourceRootError(f"no source root: pass --source-root or set {SOURCE_ENV}")
    path = pathlib.Path(value)
    if not path.is_dir():
        raise SourceRootError(f"source root does not exist: {path}")
    return path


def sha256_file(path: pathlib.Path | str) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
