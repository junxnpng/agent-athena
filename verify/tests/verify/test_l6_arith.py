"""L6: derived_from recomputation, free number strings, intra-document conflicts,
unit conversion and the Codex fragment hash / raw-layout presence check."""
from __future__ import annotations
import hashlib
import json
import sqlite3

import pytest

from tools.verify import cli, l1_exists, l6_arith as l6, ledger
from .conftest import GOLD_SLUG, SLUG


def _set(conn, row_id, **cols):
    for col, value in cols.items():
        conn.execute(f"update claims set {col}=? where row_id=?",
                     (value if isinstance(value, str) else json.dumps(value), row_id))


def _raw(conn, row_id, *strings):
    _set(conn, row_id, numbers_json=[{"raw": s} for s in strings])


def _row(summary, row_id):
    return next(r for r in summary.rows if r["row_id"] == row_id)


# --- derived_from ---------------------------------------------------------

@pytest.mark.parametrize("value,expr,status", [
    ("14.2", "35795761 / 2522394", "consistent"),
    ("14.2", "35,795,761 / 2,522,394", "consistent"),
    ("15.0", "35795761 / 2522394", "mismatch"),
    ("4", "geomean(2, 8)", "consistent"),
    ("25%", "pct_change(80, 100)", "consistent"),
    ("-20", "pct_change(100, 80)", "consistent"),
    ("0.5", "ratio(1, 2)", "consistent"),
    ("2.7", "27 / 10", "consistent"),
    ("3", "__import__('os')", "unparseable"),
    ("3", "1 / 0", "unparseable"),
    ("n/a", "1 + 2", "unparseable"),
])
def test_recompute(value, expr, status):
    assert l6.recompute(value, expr).status == status


def test_arithmetic_mean_of_ratios_is_flagged():
    res = l6.recompute("0.75", "mean(ratio(1, 2), ratio(1, 1))")
    assert res.status == "consistent" and res.reasons == ["ratio_arithmetic_mean"]
    assert l6.recompute("0.707", "geomean(ratio(1, 2), ratio(1, 1))").reasons == []


def test_v1_rows_have_no_derived_from_pointer(checked):
    s = l6.run(checked, None, SLUG)
    assert s.derived["applicable_rows"] == 0 and s.derived["rows"] == 5


def test_derived_from_rows_are_recomputed(checked):
    _set(checked, "claude:DM-A1.q1", numbers_json=[
        {"value": "14.2", "unit": "ratio", "definition": "in:out", "derived_from": "35795761 / 2522394"},
        {"value": "3.0", "unit": "x", "definition": "d", "derived_from": "10 / 4"},
        {"value": "1", "unit": "x", "definition": "d", "derived_from": "none"}])
    s = l6.run(checked, None, SLUG)
    assert s.derived["applicable_rows"] == 1
    assert (s.derived["consistent"], s.derived["mismatch"], s.derived["unparseable"]) == (1, 1, 0)
    assert _row(s, "claude:DM-A1.q1")["reasons"] == ["derived_from_mismatch"]


# --- free number strings --------------------------------------------------

def test_parse_numbers():
    vals = l6.Numbers.load().parse("P50 ≈ 0.1초 · 입력 ~10²–10⁵ · ~500K · 5–7% · 35,795,761")
    got = [(v.value, v.dim) for v in vals]
    assert (0.1, "time") in got and (100.0, None) in got and (100000.0, None) in got
    assert (500000.0, None) in got and (5.0, "percent") in got and (7.0, "percent") in got
    assert (35795761.0, None) in got
    assert (1e-3, None) in [(v.value, v.dim) for v in l6.Numbers.load().parse("10⁻³–10⁴")]


def test_keyed_values_convert_units():
    nums = l6.Numbers.load()
    keyed = {k.key: (k.value, k.dim) for k in nums.keyed("P50 ≈ 0.1초 · P99 ≈ 15분 · K = 10")}
    assert keyed == {"p50": (0.1, "time"), "p99": (900.0, "time"), "k": (10.0, None)}
    # a list or the left side of an arithmetic expression is not a keyed value
    assert nums.keyed("N=5/10/15/20") == []
    assert nums.keyed("비 = 35,795,761 / 2,522,394 ≈ 14.2:1") == []


def test_markers_and_parsed_counts(checked):
    s = l6.run(checked, None, SLUG)
    assert s.numbers["rows_with_numbers"] == 5
    assert s.numbers["rows_parsed"] == 5
    assert s.numbers["extractor_arithmetic"] == 4  # the four Claude rows say "our arithmetic"
    assert s.numbers["unreported"] == 0


def test_inline_arithmetic(checked):
    _raw(checked, "claude:DM-A1.q1", "입력:출력 토큰 비 = 35,795,761 / 2,522,394 ≈ 14.2:1")
    _raw(checked, "claude:DM-C1.q1", "10 / 4 = 3.0")
    s = l6.run(checked, None, SLUG)
    assert s.inline == {"found": 2, "consistent": 1, "mismatch": 1}
    assert _row(s, "claude:DM-A1.q1")["verdict"] == "pass"
    assert _row(s, "claude:DM-C1.q1")["reasons"] == ["inline_arith_mismatch"]


# --- intra-document conflicts ---------------------------------------------

def test_intra_doc_conflict_pairs(checked):
    _raw(checked, "claude:DM-A1.q1", "P99 ≈ 15분")
    _raw(checked, "claude:DM-C1.q1", "P99 ≈ 20분")
    _raw(checked, "codex:DM001.q1", "P99 ≈ 900초")
    s = l6.run(checked, None, SLUG)
    assert s.conflicts == [{"key": "p99", "rows": ["claude:DM-A1.q1", "claude:DM-C1.q1"],
                            "values": ["15분", "20분"]},
                           {"key": "p99", "rows": ["claude:DM-C1.q1", "codex:DM001.q1"],
                            "values": ["20분", "900초"]}]
    assert _row(s, "claude:DM-C1.q1")["reasons"] == ["intra_doc_conflict"]


def test_rows_of_one_record_never_conflict(checked):
    _raw(checked, "claude:DM-B1.q1", "P99 ≈ 15분")
    _raw(checked, "claude:DM-B1.q2", "P99 ≈ 20분")
    assert l6.run(checked, None, SLUG).conflicts == []


def test_printed_precision_is_the_tolerance(checked):
    _raw(checked, "claude:DM-A1.q1", "P80 ≈ 10초")
    _raw(checked, "claude:DM-C1.q1", "P80 ≈ 10.4초")
    assert l6.run(checked, None, SLUG).conflicts == []


# --- Codex fragments ------------------------------------------------------

def test_codex_fragments_hash_and_presence(checked, source_root):
    s = l6.run(checked, source_root, SLUG)
    assert s.fragments == {"rows": 1, "sha256_ok": 1, "in_codex_raw": 1, "in_codex_layout": 1,
                           "in_neither": 0}


def test_fragment_hash_mismatch_is_flagged(checked, source_root):
    path = source_root / "docs/patterns/260911_codex_quotes_final/codex_pattern_data.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["records"][0]["fragments"][0]["sha256"] = hashlib.sha256(b"other").hexdigest()
    path.write_text(json.dumps(data, ensure_ascii=False))
    s = l6.run(checked, source_root, SLUG)
    assert s.fragments["sha256_ok"] == 0
    assert _row(s, "codex:DM001.q1")["reasons"] == ["fragment_sha_mismatch"]


def test_fragment_check_is_skipped_without_a_source_root(checked):
    assert l6.run(checked, None, SLUG).fragments is None


# --- ledger, view, CLI ----------------------------------------------------

def test_miss_rows_never_reach_l6(checked, source_root):
    _set(checked, "claude:DM-A1.q1", quote="words that are nowhere in the paper at all")
    l1_exists.run(checked, source_root, SLUG)
    assert "claude:DM-A1.q1" not in {r["row_id"] for r in l6.run(checked, None, SLUG).rows}


def test_checks_and_run_meta(checked, source_root):
    _raw(checked, "claude:DM-C1.q1", "10 / 4 = 3.0")
    s = l6.run(checked, source_root, SLUG)
    rows = dict(checked.execute("select row_id, reason_code from checks where layer='l6'"
                                " and run_id=?", (s.run_id,)).fetchall())
    assert rows == {"claude:DM-A1.q1": None, "claude:DM-B1.q1": None, "claude:DM-B1.q2": None,
                    "claude:DM-C1.q1": "inline_arith_mismatch", "codex:DM001.q1": None}
    meta = json.loads(checked.execute("select meta_json from runs where run_id=?",
                                      (s.run_id,)).fetchone()[0])
    assert meta["derived_from"]["applicable_rows"] == 0 and meta["conflict_pairs"] == 0
    assert meta["verdicts"] == {"pass": 4, "flag": 1}


def test_l6_verdict_trigger(checked):
    ins = ("insert into checks(row_id, layer, verifier_id, protocol_ver, verdict, reason_code)"
           " values ('x', 'l6', 'v', 'p', ?, ?)")
    for verdict, reason in (("pass", "intra_doc_conflict"), ("flag", None), ("PASS", None)):
        with pytest.raises(sqlite3.IntegrityError, match="l6 verdicts"):
            checked.execute(ins, (verdict, reason))


def test_format_says_applicable_rows_zero(checked, source_root):
    text = l6.format_summary(l6.run(checked, source_root, SLUG))
    assert "derived_from: applicable_rows: 0 (of 5 rows)" in text
    assert "intra_doc_conflict: 0 pairs" in text
    assert "codex fragments: 1 rows, sha256 ok 1/1" in text


def test_cli_l6(checked, ledger_path, source_root, capsys):
    checked.close()
    assert cli.main(["l6", "--paper", SLUG, "--ledger", str(ledger_path),
                     "--source-root", str(source_root)]) == 0
    out = capsys.readouterr().out
    assert "applicable_rows: 0" in out and "l6-arith-v1" in out


def test_gold_paper_l6(real_root, ledger_path):
    from tools.verify import thresholds
    from tools.verify.convert import claude, codex
    conn = ledger.init(ledger_path)
    for mod in (claude, codex):
        ledger.import_converted(conn, mod.convert(real_root, GOLD_SLUG).payload(), real_root)
    thresholds.register(conn)
    l1_exists.run(conn, real_root, GOLD_SLUG)
    s = l6.run(conn, real_root, GOLD_SLUG)
    assert s.derived["applicable_rows"] == 0 and s.derived["rows"] == 50
    assert s.inline == {"found": 1, "consistent": 1, "mismatch": 0}  # YR-A1: 35,795,761 / 2,522,394
    assert s.fragments["rows"] == 6 and s.fragments["sha256_ok"] == 6
