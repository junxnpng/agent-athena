"""Evidence-record contract and a stdlib validator for it.

A condition value must be a non-empty string; the literal "none" states that the
field was checked and is absent in the source. A missing key is never filled in:
the record is quarantined with a reason code instead.
"""
from __future__ import annotations

import dataclasses
import json
import pathlib

from .paths import CONFIG_DIR

SCHEMA_PATH = CONFIG_DIR / "evidence_record.schema.json"

REQUIRED = ("record_id", "paper_id", "quote", "locator", "claim_text", "conditions",
            "numbers", "kind", "extractor_id", "run_id")
LOCATOR_FIELDS = ("section", "page", "para_id")
CONDITION_FIELDS = ("unit", "denominator", "window", "ideal_or_measured", "baseline")
NUMBER_FIELDS = ("value", "unit", "definition", "derived_from")
KINDS = ("measurement", "author_interpretation", "extrapolation")
NONE_VALUE = "none"


@dataclasses.dataclass
class Validation:
    status: str                      # "pass" | "quarantine"
    reasons: list[str]               # distinct reason codes, in first-seen order
    details: list[str]               # field paths behind the reason codes


def load_schema(path: pathlib.Path = SCHEMA_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(record: dict) -> Validation:
    reasons: list[str] = []
    details: list[str] = []

    def flag(code: str, where: str) -> None:
        if code not in reasons:
            reasons.append(code)
        details.append(where)

    for name in REQUIRED:
        if name not in record:
            flag("missing_required_field", name)

    locator = record.get("locator")
    if "locator" in record:
        if not isinstance(locator, dict):
            flag("invalid_type", "locator")
        else:
            for name in LOCATOR_FIELDS:
                if name not in locator:
                    flag("missing_required_field", f"locator.{name}")

    conditions = record.get("conditions")
    if "conditions" in record:
        if not isinstance(conditions, dict):
            flag("invalid_type", "conditions")
        else:
            for name in CONDITION_FIELDS:
                if name not in conditions:
                    flag("missing_condition_field", f"conditions.{name}")
                elif not isinstance(conditions[name], str):
                    flag("invalid_type", f"conditions.{name}")
                elif not conditions[name].strip():
                    flag("empty_condition_value", f"conditions.{name}")

    numbers = record.get("numbers")
    if "numbers" in record:
        if not isinstance(numbers, list):
            flag("invalid_type", "numbers")
        else:
            for i, item in enumerate(numbers):
                if not isinstance(item, dict):
                    flag("invalid_type", f"numbers[{i}]")
                    continue
                for name in NUMBER_FIELDS:
                    if name not in item:
                        flag("missing_number_field", f"numbers[{i}].{name}")

    if "kind" in record and record["kind"] not in KINDS:
        flag("invalid_kind", "kind")

    for name in ("record_id", "paper_id", "quote", "claim_text", "extractor_id", "run_id"):
        if name in record and not isinstance(record[name], str):
            flag("invalid_type", name)

    return Validation("quarantine" if reasons else "pass", reasons, details)


def required_summary() -> list[str]:
    """Human-readable list of required fields, nested fields spelled out."""
    return [
        "record_id",
        "paper_id",
        "quote",
        "locator{" + ",".join(LOCATOR_FIELDS) + "}",
        "claim_text",
        f"conditions({len(CONDITION_FIELDS)}){{" + ",".join(CONDITION_FIELDS) + "}",
        "numbers[]{" + ",".join(NUMBER_FIELDS) + "}",
        "kind{" + ",".join(KINDS) + "}",
        "extractor_id",
        "run_id",
    ]
