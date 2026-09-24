from __future__ import annotations
import ast
import json
import pathlib
import sqlite3

import pytest

from tools.verify import cli, l1_exists as l1, normalize as nz
from .conftest import GOLD_SLUG, RAW_TEXT, SLUG, seal

VARIANTS = {"codex_raw": RAW_TEXT, "codex_layout": RAW_TEXT.replace("\n\n", "\n")}


def _variants(texts=VARIANTS):
    return [l1.Variant(name, text) for name, text in texts.items()]


def test_grades_from_exact_to_miss():
    vs = _variants()
    assert l1.check_quote("Requests span a wide range of token lengths.", vs).grade == "exact"
    assert l1.check_quote("Prefix reuse is common: most requests share a long system prompt with an"
                          "\nearlier request", vs).grade == "strict"
    assert l1.check_quote("“Prefix reuse is common”", vs).grade == "loose"  # quote marks absent from the text
    assert l1.check_quote("user-deployed models.", vs).grade == "loose"  # text goes on: "models across"
    assert l1.check_quote("words that are nowhere in the paper", vs).grade == "MISS"


INTRUDED = ("Figure 14a shows that per-user inter-arrival time remains on the order of\n\n"
            "Conference'17, July 2017, Washington, DC, USA\n\nNixon et al.\n\n"
            "minutes for most of the trace, but declines toward early 2026.")
QUOTE = ("Figure 14a shows that per-user inter-arrival time remains on the order of minutes"
         " for most of the trace, but declines toward early 2026.")


def test_gapped_grade_tolerates_an_intrusion():
    vs = _variants({"v": "Intro text.\n\n" + INTRUDED})
    res = l1.check_quote(QUOTE, vs)
    assert res.grade == "gapped"
    assert vs[0].text[res.char_start:res.char_end] == INTRUDED.rstrip(".")  # loose drops the stop


def test_gapped_grade_limits():
    far = INTRUDED.replace("Nixon et al.", "x " * 600)
    assert l1.check_quote(QUOTE, _variants({"v": far})).grade == "MISS"  # gap over 1000 chars
    three = ("Figure 14a shows that per-user\nHEADER A\ninter-arrival time remains on the\n"
             "HEADER B\norder of minutes for most of the\nHEADER C\ntrace, but declines"
             " toward early 2026.")
    assert l1.check_quote(QUOTE, _variants({"v": three})).grade == "MISS"  # four runs
    short = "Figure 14a shows that per-user inter-arrival time remains on the order of minutes"
    stray = short + " for\nXX\nmost of\nYY\nthe trace, but declines toward early 2026."
    assert l1.check_quote(QUOTE, _variants({"v": stray})).grade == "MISS"  # a run under 20


def test_offsets_are_a_span_of_the_matched_variant():
    vs = _variants()
    quote = "prefix reuse is common:  most requests share a long system prompt"
    res = l1.check_quote(quote, vs)
    assert res.grade == "strict" and res.variant == "codex_raw"
    text = VARIANTS[res.variant][res.char_start:res.char_end]
    assert text == "Prefix reuse is common: most requests share a long system prompt"


def test_pieces_match_in_order_and_span_the_shortest_embedding():
    vs = _variants({"v": "alpha beta. gamma delta. alpha beta and then gamma delta end."})
    res = l1.check_quote("alpha beta … gamma delta end", vs)
    assert res.grade == "exact"
    assert vs[0].text[res.char_start:res.char_end] == "alpha beta and then gamma delta end"
    assert l1.check_quote("gamma delta end … alpha beta. gamma", vs).grade == "MISS"


def test_best_grade_over_variants_and_per_variant_grades():
    vs = _variants({"a": "the inference-\nsystem is fast", "b": "The inference system is fast"})
    res = l1.check_quote("The inference system is fast", vs)
    assert (res.grade, res.variant) == ("exact", "b")
    assert res.per_variant == {"a": "strict", "b": "exact"}


def test_verdict_closed(sealed, source_root, tmp_path, ledger_path):
    """L1 verdicts are PASS or MISS; waivers never become a verdict."""
    summary = l1.run(sealed, source_root, SLUG)
    verdicts = {v for (v,) in sealed.execute("select distinct verdict from checks where layer='l1'")}
    assert verdicts <= {"PASS", "MISS"}
    assert set(l1.VERDICTS) == {"PASS", "MISS"}
    assert summary.verdicts == {"PASS": 5}
    with pytest.raises(sqlite3.IntegrityError, match="l1 verdicts"):
        sealed.execute("insert into checks(row_id, layer, verifier_id, protocol_ver, verdict)"
                       " values ('claude:DM-A1.q1', 'l1', 'x', 'v1', 'WAIVED')")


def test_pass_grades_come_from_the_registered_thresholds(ledger_path, source_root, tmp_path):
    conn = seal(ledger_path, source_root, tmp_path, l1_pass_grades=["exact", "strict"],
                protocol_ver="test")
    l1.run(conn, source_root, SLUG)
    row = conn.execute("select verdict, grade, matched_variant, char_start, char_end from checks"
                       " where row_id='claude:DM-A1.q1'").fetchone()
    assert row == ("MISS", "loose", None, None, None)


def test_only_miss_rows_have_null_offsets(sealed, source_root):
    sealed.execute("update claims set quote='words that are nowhere in the paper at all'"
                   " where row_id='claude:DM-C1.q1'")
    l1.run(sealed, source_root, SLUG)
    rows = sealed.execute("select verdict, matched_variant, char_start, char_end, grade from checks"
                          " where layer='l1'").fetchall()
    assert len(rows) == 5
    for verdict, variant, start, end, grade in rows:
        if verdict == "PASS":
            assert None not in (variant, start, end, grade)
        else:
            assert (variant, start, end, grade) == (None, None, None, "MISS")
    with pytest.raises(sqlite3.IntegrityError, match="l1 verdicts"):
        sealed.execute("insert into checks(row_id, layer, verifier_id, protocol_ver, verdict, grade)"
                       " values ('claude:DM-A1.q1', 'l1', 'x', 'v1', 'PASS', 'exact')")
    with pytest.raises(sqlite3.IntegrityError, match="l1 verdicts"):
        sealed.execute("insert into checks(row_id, layer, verifier_id, protocol_ver, verdict, grade,"
                       " matched_variant, char_start, char_end)"
                       " values ('claude:DM-A1.q1', 'l1', 'x', 'v1', 'MISS', 'MISS', 'codex_raw', 1, 2)")


def test_checks_carry_provenance_and_tautology(sealed, source_root):
    summary = l1.run(sealed, source_root, SLUG)
    rows = dict(sealed.execute("select row_id, l1_tautological from checks where layer='l1'"))
    assert rows["codex:DM001.q1"] == 1 and rows["claude:DM-A1.q1"] == 0
    ids = set(sealed.execute("select distinct verifier_id, protocol_ver, run_id from checks"))
    assert ids == {(l1.VERIFIER_ID, summary.protocol_ver, summary.run_id)}
    run = sealed.execute("select thresholds_sha256, meta_json from runs where run_id=?",
                         (summary.run_id,)).fetchone()
    assert run[0] and json.loads(run[1])["normalization_sha256"] == nz.load().sha256
    detail = json.loads(sealed.execute("select detail_json from checks where row_id='claude:DM-A1.q1'")
                        .fetchone()[0])
    assert detail["per_variant"]["claude_column"] == "unavailable"


def test_summary_separates_tautological_rows_and_unavailable_variants(sealed, source_root):
    s = l1.run(sealed, source_root, SLUG)
    assert s.unavailable == ["claude_column"]
    assert s.grades["claude"] == {"exact": 3, "strict": 0, "loose": 1, "gapped": 0, "MISS": 0}
    assert s.grades["codex"] == {"exact": 0, "strict": 1, "loose": 0, "gapped": 0, "MISS": 0}
    assert s.per_variant["codex_layout"]["claude"]["exact"] == 3


def test_changed_variant_text_is_refused(sealed, source_root):
    raw = source_root / f"papers/codex_source_text/codex_{SLUG}.txt"
    raw.write_text(raw.read_text(encoding="utf-8") + "\nmore\n")
    with pytest.raises(l1.L1Error, match="changed since registration"):
        l1.run(sealed, source_root, SLUG)


def test_run_needs_registered_thresholds(ledger_path, source_root):
    from tools.verify import ledger, thresholds
    from tools.verify.convert import claude
    conn = ledger.init(ledger_path)
    ledger.import_converted(conn, claude.convert(source_root, SLUG).payload(), source_root)
    with pytest.raises(thresholds.ThresholdsError, match="not registered"):
        l1.run(conn, source_root, SLUG)


def test_l1_does_not_import_the_judge():
    src = pathlib.Path(l1.__file__).read_text(encoding="utf-8")
    names = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.ImportFrom):
            names.add(node.module or "")
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
    assert not any("judge" in n or "backends" in n for n in names), names


def test_cli_reports_variants_and_rows(sealed, ledger_path, source_root, capsys):
    sealed.close()
    assert cli.main(["l1", "--paper", SLUG, "--all-variants", "--report-variants",
                     "--ledger", str(ledger_path), "--source-root", str(source_root)]) == 0
    out = capsys.readouterr().out
    assert "claude_column: unavailable" in out
    assert "codex (l1_tautological=1)" in out
    assert "claude:DM-A1.q1\tPASS\tloose\tcodex_raw\t" in out
    for name in ("codex_raw", "codex_layout", "claude_body"):
        assert f"\n  {name}" in out


def test_cli_unknown_variant(sealed, ledger_path, source_root, capsys):
    sealed.close()
    assert cli.main(["l1", "--paper", SLUG, "--variants", "codex_raw,nope",
                     "--ledger", str(ledger_path), "--source-root", str(source_root)]) == 1
    assert "unknown variant" in capsys.readouterr().err


def test_gold_paper_grade_distribution(real_root, ledger_path):
    """Measured 2026-09-23 on the gold paper; see docs/decisions.md for the gapped and MISS rows."""
    from tools.verify import ledger, thresholds
    from tools.verify.convert import claude, codex
    conn = ledger.init(ledger_path)
    for mod in (claude, codex):
        ledger.import_converted(conn, mod.convert(real_root, GOLD_SLUG).payload(), real_root)
    thresholds.register(conn)
    s = l1.run(conn, real_root, GOLD_SLUG)
    assert s.unavailable == ["claude_column"]
    assert s.grades == {"claude": {"exact": 0, "strict": 29, "loose": 9, "gapped": 6, "MISS": 0},
                        "codex": {"exact": 2, "strict": 4, "loose": 0, "gapped": 0, "MISS": 1}}
    assert s.verdicts == {"PASS": 50, "MISS": 1}
    # the layout text sets the two columns side by side: only one short quote, split
    # across a column line, matches it (gapped)
    assert s.per_variant["codex_layout"]["claude"] == {"exact": 0, "strict": 0, "loose": 0,
                                                       "gapped": 1, "MISS": 43}
    gapped = {r["row_id"] for r in s.rows if r["grade"] == "gapped"}
    assert gapped == {"claude:YR-B1.q1", "claude:YR-C2.q1", "claude:YR-E1.q1", "claude:YR-G3.q1",
                      "claude:YR-H2.q1", "claude:YR-H4.q2"}
    assert {r["row_id"] for r in s.rows if r["verdict"] == "MISS"} == {"codex:YR036.q1"}
