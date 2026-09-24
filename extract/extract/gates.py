"""Load registered extraction gates and enforce paragraph compatibility."""
from __future__ import annotations

import json
import os
from pathlib import Path

from tools.verify import thresholds
from tools.verify.paths import sha256_file
from .paths import CONFIG_DIR

DEFAULT_PATH = CONFIG_DIR / "gates.json"
REQUIRED_KEYS = ("schema_valid", "l1_variant", "l1_grades", "l1_pass_rate",
                 "kind_memo_rate", "g_recall", "codex_raw_grades")


def load_gates(path: Path = DEFAULT_PATH) -> dict:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"{path}: cannot read JSON gates: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{path}: gates must be a mapping")
    missing = [key for key in REQUIRED_KEYS if key not in value]
    if missing:
        raise RuntimeError(f"{path}: missing gates: {', '.join(missing)}")
    return value


def sha256_of(path: Path) -> str:
    return sha256_file(path)


def assert_paragraph_unit_split() -> None:
    path = Path(os.environ.get("EXTRACT_THRESHOLDS_PATH") or thresholds.DEFAULT_PATH)
    try:
        data = thresholds.load(path)
    except (OSError, ValueError, thresholds.ThresholdsError) as exc:
        raise RuntimeError(f"{path}: cannot load verifier thresholds: {exc}") from exc
    unit = data.get("paragraph_unit")
    if not isinstance(unit, dict) or unit.get("split") != "blank_line_block":
        raise RuntimeError("verify paragraph_unit.split must be blank_line_block")
