"""L2: the contract fields of every L1-passed row, the kind tag, the baseline of a
comparison and the modality of the claim against its quote."""
from __future__ import annotations
import json
import sqlite3

import pytest

from tools.verify import cli, l1_exists, l2_schema as l2, ledger
from .conftest import GOLD_SLUG, SLUG

FULL = {"unit": "requests", "denominator": "all requests", "window": "one year",
        "ideal_or_measured": "measured", "baseline": "none"}
NUMBER = {"value": "14.2", "unit": "ratio", "definition": "input:output tokens",
          "derived_from": "none"}


def _set(conn, row_id, **cols):
    for col, value in cols.items():
        if not isinstance(value, str):
            value = json.dumps(value)
        conn.execute(f"update claims set {col}=? where row_id=?", (value, row_id))


def _complete(conn, row_id, conditions=None, numbers=None):
    _set(conn, row_id, conditions_json=conditions or FULL, numbers_json=numbers or [NUMBER])


def _row(summary, row_id):
    return next(r for r in summary.rows if r["row_id"] == row_id)


def test_rows_without_condition_keys_are_quarantined(checked):
    s = l2.run(checked, SLUG)
    assert len(s.rows) == 5
    assert s.verdicts == {"pass": 0, "quarantine": 5}
    assert s.reasons["missing_condition_field"] == 5
    assert all(r["comparable"] == 0 for r in s.rows)
    assert s.quarantine_rate == 1.0


def test_a_complete_row_passes_and_is_comparable(checked):
    _complete(checked, "claude:DM-A1.q1")
    r = _row(l2.run(checked, SLUG), "claude:DM-A1.q1")
    assert (r["verdict"], r["reasons"], r["comparable"]) == ("pass", [], 1)


def test_none_passes_but_an_empty_value_does_not(checked):
    _complete(checked, "claude:DM-A1.q1", dict(FULL, window="none"))
    _complete(checked, "claude:DM-B1.q1", dict(FULL, window="  "))
    s = l2.run(checked, SLUG)
    assert _row(s, "claude:DM-A1.q1")["verdict"] == "pass"
    assert _row(s, "claude:DM-B1.q1")["reasons"] == ["empty_condition_value"]


def test_free_number_strings_lack_unit_and_definition(checked):
    _set(checked, "claude:DM-A1.q1", conditions_json=FULL)
    r = _row(l2.run(checked, SLUG), "claude:DM-A1.q1")
    assert r["reasons"] == ["missing_number_field"]
    assert "numbers[0].unit" in r["details"] and "numbers[0].definition" in r["details"]


def test_a_row_without_numbers_needs_no_number_fields(checked):
    _complete(checked, "claude:DM-A1.q1", numbers=[])
    _set(checked, "claude:DM-A1.q1", numbers_json=[])
    assert _row(l2.run(checked, SLUG), "claude:DM-A1.q1")["verdict"] == "pass"


def test_kind_outside_the_three_tags_is_quarantined(checked):
    _complete(checked, "claude:DM-A1.q1")
    _set(checked, "claude:DM-A1.q1", kind="opinion")
    assert _row(l2.run(checked, SLUG), "claude:DM-A1.q1")["reasons"] == ["invalid_kind"]


def test_a_comparison_needs_a_baseline(checked):
    # DM-C1: "input lengths are much longer than output lengths"
    _complete(checked, "claude:DM-C1.q1")
    r = _row(l2.run(checked, SLUG), "claude:DM-C1.q1")
    assert r["reasons"] == ["comparison_without_baseline"]
    _complete(checked, "claude:DM-C1.q1", dict(FULL, baseline="output lengths"))
    assert _row(l2.run(checked, SLUG), "claude:DM-C1.q1")["verdict"] == "pass"


@pytest.mark.parametrize("quote,claim,raised", [
    ("Reuse may explain the gap.", "Reuse explains the gap.", True),
    ("Reuse may explain the gap.", "Reuse may explain the gap.", False),
    ("Reuse explains the gap.", "Reuse always explains the gap.", True),
    ("Reuse explains the gap.", "Reuse likely explains the gap.", False),
    ("Reuse suggests locality.", "저자는 지역성이 원인이라고 추정한다.", False),
    ("Reuse suggests locality.", "지역성이 원인이다.", True),
    ("Reuse is common.", "모든 요청이 재사용된다.", True),
    ("In our setting reuse is high.", "Reuse is high.", True),
])
def test_modality_raise_is_flagged(quote, claim, raised):
    levels = l2.Modality.load()
    assert levels.raised(quote, claim) is raised


def test_modality_flag_quarantines_a_complete_row(checked):
    _complete(checked, "claude:DM-A1.q1")
    _set(checked, "claude:DM-A1.q1", claim_text="CompanyX always serves every model.")
    r = _row(l2.run(checked, SLUG), "claude:DM-A1.q1")
    assert r["reasons"] == ["modality_raised"]
    assert r["modality"] == {"quote": "plain", "claim": "universal"}


def test_miss_rows_never_reach_l2(checked, source_root):
    _set(checked, "claude:DM-A1.q1", quote="words that are nowhere in the paper at all")
    l1_exists.run(checked, source_root, SLUG)
    s = l2.run(checked, SLUG)
    assert "claude:DM-A1.q1" not in {r["row_id"] for r in s.rows}
    assert len(s.rows) == 4


def test_checks_rows_carry_verifier_protocol_and_reasons(checked):
    _complete(checked, "claude:DM-A1.q1")
    s = l2.run(checked, SLUG)
    rows = checked.execute("select row_id, verdict, reason_code, verifier_id, protocol_ver,"
                           " detail_json from checks where layer='l2' and run_id=?",
                           (s.run_id,)).fetchall()
    assert len(rows) == 5
    by_id = {r[0]: r for r in rows}
    assert by_id["claude:DM-A1.q1"][1:3] == ("pass", None)
    assert by_id["claude:DM-B1.q1"][2] == "missing_condition_field,missing_number_field"
    assert {r[3] for r in rows} == {l2.VERIFIER_ID} and {r[4] for r in rows} == {"v3-athena-json1"}
    assert json.loads(by_id["claude:DM-A1.q1"][5])["comparable"] == 1
    meta = json.loads(checked.execute("select meta_json from runs where run_id=?",
                                      (s.run_id,)).fetchone()[0])
    assert meta["paper_id"] == SLUG and meta["quarantine"] == 4 and meta["rows"] == 5


def test_l2_verdict_trigger(checked):
    ins = ("insert into checks(row_id, layer, verifier_id, protocol_ver, verdict, reason_code)"
           " values ('x', 'l2', 'v', 'p', ?, ?)")
    for verdict, reason in (("pass", "missing_condition_field"), ("quarantine", None),
                            ("MISS", None)):
        with pytest.raises(sqlite3.IntegrityError, match="l2 verdicts"):
            checked.execute(ins, (verdict, reason))
    checked.execute(ins, ("quarantine", "missing_condition_field"))


def test_format_labels_the_rate_as_an_input_diagnostic(checked):
    text = l2.format_summary(l2.run(checked, SLUG))
    assert "quarantine_rate: 1.000 (5/5) — input diagnostic, prior expectation 100%" in text
    assert "missing_condition_field: 5" in text
    assert "claude:DM-C1.q1\tquarantine" in text


def test_cli_l2(checked, ledger_path, capsys):
    checked.close()
    assert cli.main(["l2", "--paper", SLUG, "--ledger", str(ledger_path)]) == 0
    out = capsys.readouterr().out
    assert "input diagnostic, prior expectation 100%" in out and "l2-schema-v1" in out


def test_cli_l2_needs_thresholds(ledger_path, capsys):
    ledger.init(ledger_path).close()
    assert cli.main(["l2", "--paper", SLUG, "--ledger", str(ledger_path)]) == 1
    assert "thresholds not registered" in capsys.readouterr().err


def test_gold_paper_l2(real_root, ledger_path):
    """Neither record set carries the five condition keys: every L1-passed row is quarantined."""
    from tools.verify import thresholds
    from tools.verify.convert import claude, codex
    conn = ledger.init(ledger_path)
    for mod in (claude, codex):
        ledger.import_converted(conn, mod.convert(real_root, GOLD_SLUG).payload(), real_root)
    thresholds.register(conn)
    l1_exists.run(conn, real_root, GOLD_SLUG)
    s = l2.run(conn, GOLD_SLUG)
    assert len(s.rows) == 50 and s.verdicts == {"pass": 0, "quarantine": 50}
    assert s.reasons["missing_condition_field"] == 50
