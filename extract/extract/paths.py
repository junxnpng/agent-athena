"""Extraction paths and the shared source-root contract."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from tools.verify.paths import SOURCE_ENV, SourceRootError
from tools.verify.paths import source_root as _source_root

EXTRACT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = EXTRACT_ROOT / "config"
RESULTS_DIR = EXTRACT_ROOT / "results"


def source_root(value: Optional[str] = None) -> Path:
    return _source_root(value)
