from __future__ import annotations
import copy
import json

import pytest

from tools.verify import cli, schema


def _record(**over):
    rec = {
        "record_id": "YR-A1", "paper_id": "p", "quote": "q",
        "locator": {"section": "§3", "page": 3, "para_id": "codex_raw#0001"},
        "claim_text": "c",
        "conditions": {k: "none" for k in schema.CONDITION_FIELDS},
        "numbers": [{"value": "14.2", "unit": "ratio", "definition": "in/out", "derived_from": "none"}],
        "kind": "measurement", "extractor_id": "claude", "run_id": "r1",
    }
    rec.update(over)
    return rec


def test_schema_file_lists_the_contract():
    data = schema.load_schema()
    assert set(data["required"]) == set(schema.REQUIRED)
    assert data["properties"]["conditions"]["required"] == list(schema.CONDITION_FIELDS)
    assert data["properties"]["kind"]["enum"] == list(schema.KINDS)


def test_condition_value_none_passes():
    assert schema.validate(_record()).status == "pass"


def test_missing_condition_key_is_quarantined():
    rec = _record()
    del rec["conditions"]["baseline"]
    result = schema.validate(rec)
    assert result.status == "quarantine"
    assert result.reasons == ["missing_condition_field"]
    assert "conditions.baseline" in result.details


def test_empty_conditions_are_not_filled_in():
    rec = _record(conditions={})
    before = copy.deepcopy(rec)
    result = schema.validate(rec)
    assert result.status == "quarantine"
    assert rec == before
    assert len([d for d in result.details if d.startswith("conditions.")]) == 5


def test_empty_condition_string_is_not_none():
    rec = _record()
    rec["conditions"]["unit"] = ""
    assert schema.validate(rec).reasons == ["empty_condition_value"]


def test_missing_required_field():
    rec = _record()
    del rec["quote"]
    result = schema.validate(rec)
    assert result.status == "quarantine"
    assert "missing_required_field" in result.reasons


def test_bad_kind_and_types():
    assert "invalid_kind" in schema.validate(_record(kind="observation")).reasons
    assert "invalid_type" in schema.validate(_record(numbers="3")).reasons
    assert "invalid_type" in schema.validate(_record(locator="p.3")).reasons
    assert "invalid_type" in schema.validate(_record(conditions="none")).reasons


def test_number_item_missing_fields():
    result = schema.validate(_record(numbers=[{"raw": "14.2:1"}]))
    assert result.reasons == ["missing_number_field"]
    assert "numbers[0].value" in result.details
    assert "invalid_type" in schema.validate(_record(numbers=["14.2"])).reasons


def test_locator_fields_required():
    rec = _record(locator={"page": 3})
    assert "missing_required_field" in schema.validate(rec).reasons


def test_print_required(capsys):
    assert cli.main(["schema", "--print-required"]) == 0
    out = capsys.readouterr().out
    for name in ("record_id", "paper_id", "quote", "locator", "claim_text", "conditions",
                 "numbers[]", "kind", "extractor_id", "run_id"):
        assert name in out
    for name in schema.CONDITION_FIELDS:
        assert name in out
    assert "conditions(5)" in out


def test_validate_command(tmp_path, capsys):
    path = tmp_path / "r.jsonl"
    good, bad = _record(), _record(conditions={})
    path.write_text(json.dumps(good) + "\n" + json.dumps(bad) + "\n")
    assert cli.main(["schema", "--validate", str(path)]) == 0
    out = capsys.readouterr().out
    assert "pass: 1" in out and "quarantine: 1" in out and "missing_condition_field: 1" in out
