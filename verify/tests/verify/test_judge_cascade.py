"""The cheap first sweep only routes: it can never say that evidence supports a claim."""
from __future__ import annotations
import sqlite3

import pytest

from tools.verify import cli, judge, queries
from tools.verify.backends import lexical
from .conftest import QUERY, SLUG

ROWS = [
    "We analyze a one-year production trace from a serverless platform.",
    "Most requests share a long system prompt with an earlier request from the same user.",
    "Prefix reuse is not common: no request shares a prompt.",
    "The model may suggest 42 tokens per second for CompanyX users.",
    "",
    "Figure 2 shows that input lengths are much longer than output lengths",
]


def test_routes_are_closed_and_never_support():
    assert lexical.ROUTES == ("insufficient", "needs-judge")
    backend = lexical.LexicalBackend()
    for quote in ROWS:
        for claim in (QUERY["claim_text"], "Decode dominates latency.", ""):
            route = backend.route(quote, {"topic": QUERY["topic"], "claim_text": claim})
            assert route.verdict in lexical.ROUTES


def test_route_features():
    backend = lexical.LexicalBackend()
    q = {"topic": QUERY["topic"], "claim_text": QUERY["claim_text"]}
    hit = backend.route(ROWS[1], q)
    assert hit.verdict == "needs-judge" and hit.features["content_overlap"] >= 2
    miss = backend.route(ROWS[5], q)
    assert miss.verdict == "insufficient" and miss.features["content_overlap"] == 0
    flags = backend.route(ROWS[3], {"topic": "CompanyX", "claim_text": "It serves 42 tokens."})
    assert flags.features["shared_numbers"] == ["42"]
    assert flags.features["shared_proper_nouns"] == ["companyx"]
    assert flags.features["modality"] and not flags.features["negation"]
    assert backend.route(ROWS[2], q).features["negation"]


def test_sweep_covers_l1_passed_rows_only(checked):
    s = judge.sweep(checked, SLUG, QUERY["query_id"])
    assert s.rows == 5
    assert s.routes == {"needs-judge": 3, "insufficient": 2}
    assert s.escalation_rate == pytest.approx(0.6)
    assert s.expensive_ratio == 0 and s.tier2_invoked is False
    rows = checked.execute("select tier, verifier_id, query_id, verdict from checks"
                           " where layer='align'").fetchall()
    assert {r[:3] for r in rows} == {("tier0", lexical.VERIFIER_ID, QUERY["query_id"])}


def test_sweep_skips_miss_rows(checked, source_root):
    from tools.verify import l1_exists
    checked.execute("update claims set quote='words that are nowhere in the paper at all'"
                    " where row_id='claude:DM-B1.q2'")
    l1_exists.run(checked, source_root, SLUG)
    s = judge.sweep(checked, SLUG, QUERY["query_id"])
    assert s.rows == 4
    ids = {r for (r,) in checked.execute("select row_id from checks where layer='align'")}
    assert "claude:DM-B1.q2" not in ids


def test_tier0_cannot_store_supports(checked):
    with pytest.raises(sqlite3.IntegrityError, match="judge verdicts"):
        checked.execute(
            "insert into checks(row_id, layer, verifier_id, protocol_ver, verdict, tier, query_id,"
            " evidence_span, matched_variant, char_start, char_end)"
            " values ('claude:DM-A1.q1', 'align', 'lexical-v1', 'v2', 'supports', 'tier0',"
            " 'demo-reuse', 'x', 'codex_raw', 0, 1)")


def test_sweep_needs_a_confirmed_query(checked):
    queries.register(checked, dict(QUERY, query_id="draft", confirmed_by=None))
    with pytest.raises(queries.QueryError, match="not confirmed"):
        judge.sweep(checked, SLUG, "draft")


def test_default_query_is_the_only_registered_one(checked):
    assert judge.default_query(checked) == QUERY["query_id"]
    queries.register(checked, dict(QUERY, query_id="other"))
    with pytest.raises(judge.JudgeError, match="--query"):
        judge.default_query(checked)


def test_cli_sweep_reports_observations(checked, ledger_path, capsys):
    checked.close()
    assert cli.main(["judge", "sweep", "--backend", "lexical", "--paper", SLUG,
                     "--ledger", str(ledger_path)]) == 0
    out = capsys.readouterr().out
    assert "escalation_rate: 0.600 (observed, 3/5)" in out
    assert "expensive_ratio: 0 (tier2 not invoked)" in out
    assert "supports" not in out
