"""Recall against G: claude / codex / union x claim_present / conditions_match / numbers_match."""
from __future__ import annotations
import json

import pytest

from tools.verify import cli, ledger, recall, report, stats
from tools.verify.convert import gold
from .conftest import QUERY, SLUG

G_LINE = ("Demo Paper**한줄평: 짧은 평****We analyze a one-year production trace from CompanyX, a "
          "serverless LLM inference platform that serves 2 regions.Requests span a wide range of "
          "token lengths. Prefix reuse is common: most requests share a long system prompt with an "
          "earlier request from the same user. The load balancer runs 12 replicas per region.-> 메모 "
          "하나.Figure 2 shows that input lengths are much longer than output lengths for every "
          "model family we study in the trace.")


def register_gold(conn, tmp_path, line=G_LINE):
    path = tmp_path / "demo_gold.md"
    path.write_text(f"# G\n\n## 원문(그대로)\n\n### {line}\n")
    return gold.register(conn, SLUG, path)


@pytest.fixture
def recalled(checked, tmp_path):
    register_gold(checked, tmp_path)
    return checked


CFG = recall.load_config()


def test_coverage_is_character_level_on_the_canonical_form():
    s = "production studies examine KV-cache reuse and inferencesystem behavior [17, 18]"
    q = "Production studies examine KV-cache reuse and inference system behavior at scale."
    assert recall.coverage(s, q, CFG) == 1.0
    assert recall.covers(s, q, CFG)
    assert not recall.covers(s, "An unrelated sentence about load balancers and replicas.", CFG)


def test_short_sentence_is_covered_whole_or_not_at_all():
    s = "DeepSeek V3.2 lies between these two cases."
    assert recall.covers(s, "and DeepSeek V3.2 lies between these two cases. Then", CFG)
    assert not recall.covers(s, "DeepSeek V3.2 lies between", CFG)


def test_partial_quote_needs_half_the_sentence():
    s = "Figure 2 shows that input lengths are much longer than output lengths for every model family."
    assert recall.covers(s, "Figure 2 shows that input lengths are much longer than output lengths", CFG)
    assert not recall.covers(s, "input lengths are much longer than", CFG)


def test_gold_numbers_skip_citations_figures_and_versions():
    nums = recall.Reader(CFG)
    vals = nums.gold("Figure 2a shows that DeepSeek-V3.2 [8] and MiniMaxM2.5 take 10^2 to 10^5 tokens,"
                     " and 27 GB moves in 2.7 s over 10 GB/s.")
    assert [v.value for v in vals] == [100, 100000, 27e9, 2.7, 10e9]


def test_lower_case_figure_references_are_not_numbers():
    assert recall.Reader(CFG).gold("Figure 4a shows it, and figure 4b shows TTFT; see Table 2.") == []


def test_numbers_match_needs_every_number():
    nums = recall.Reader(CFG)
    vals = nums.gold("A 100K-token context occupies roughly 27 GB, about 2.7 s over 10 GB/s.")
    assert nums.match(vals, ["100K tokens · 27 GB · 2.7초 · 10 GB/s"])
    assert not nums.match(vals, ["27 GB · 2.7 s"])
    assert not nums.match([], ["27 GB"])


def test_table_levels_and_sets(recalled):
    s = recall.run(recalled, SLUG, QUERY["query_id"])
    cp = s.table["claim_present"]
    assert cp["claude"] == {"recall": [4, 5], "precision": [4, 4]}
    assert cp["codex"] == {"recall": [1, 5], "precision": [1, 1]}
    assert cp["union"] == {"recall": [4, 5], "precision": [5, 5]}
    assert "not_applicable" in s.table["conditions_match"]
    nm = s.table["numbers_match"]
    assert nm["claude"]["recall"] == [0, 2] and nm["union"]["recall"] == [0, 2]


def test_numbers_match_counts_a_row_that_records_the_numbers(recalled):
    recalled.execute("update claims set numbers_json=? where row_id='claude:DM-A1.q1'",
                     (json.dumps([{"raw": "2 regions"}]),))
    s = recall.run(recalled, SLUG)
    assert s.table["numbers_match"]["claude"] == {"recall": [1, 2], "precision": [1, 4]}
    assert s.table["numbers_match"]["codex"]["recall"] == [0, 2]


def test_miss_rows_never_count(recalled, source_root):
    from tools.verify import l1_exists
    recalled.execute("update claims set quote='words that are nowhere in the paper at all'"
                     " where row_id='codex:DM001.q1'")
    l1_exists.run(recalled, source_root, SLUG)
    s = recall.run(recalled, SLUG)
    assert s.table["claim_present"]["codex"] == {"recall": [0, 5], "precision": [0, 0]}


def test_output_reports_probes_targets_and_the_union_footnote(recalled):
    text = recall.format_summary(recall.run(recalled, SLUG, QUERY["query_id"]))
    assert "probes P: not-applicable: extractor runs are frozen" in text
    assert "target set T: not-applicable: extractor runs are frozen" in text
    assert "planted now tests the recall code" in text
    assert "union ≈ claude" in text
    assert "| claim_present |" in text and "| conditions_match |" in text and "| numbers_match |" in text


def test_run_is_recorded_with_one_check_per_gold_sentence(recalled):
    s = recall.run(recalled, SLUG, QUERY["query_id"])
    rows = recalled.execute("select row_id, verdict, verifier_id, protocol_ver, query_id from checks"
                            " where layer='recall' and run_id=?", (s.run_id,)).fetchall()
    assert len(rows) == 5
    assert {r[1] for r in rows} == {"present", "absent"}
    assert all(r[2] == recall.VERIFIER_ID and r[3] and r[4] == QUERY["query_id"] for r in rows)
    meta = json.loads(recalled.execute("select meta_json from runs where run_id=?",
                                       (s.run_id,)).fetchone()[0])
    assert meta["config_sha256"] == CFG.sha256 and meta["gold_split_count"] == 5


def test_recall_verdicts_are_closed(recalled):
    import sqlite3
    with pytest.raises(sqlite3.IntegrityError, match="recall verdicts"):
        recalled.execute("insert into checks(row_id, layer, verifier_id, protocol_ver, verdict)"
                         " values ('g', 'recall', 'x', 'v', 'maybe')")


def test_recall_needs_gold(checked):
    with pytest.raises(gold.GoldError, match="convert gold"):
        recall.run(checked, SLUG)


def test_unknown_query_is_refused(recalled):
    with pytest.raises(recall.RecallError, match="unknown query"):
        recall.run(recalled, SLUG, "no-such-query")


# --- capture-recapture ------------------------------------------------------

def test_asymmetric_sets_skip_chapman(recalled):
    c = recall.run(recalled, SLUG).chapman
    assert c["skipped"].startswith("asymmetric sets")
    assert c["lower_bound"] is True and c["chapman_estimate"] is None


def test_single_set_skips_chapman(recalled, source_root):
    from tools.verify import l1_exists
    recalled.execute("update claims set quote='words that are nowhere in the paper at all'"
                     " where row_id='codex:DM001.q1'")
    l1_exists.run(recalled, source_root, SLUG)
    assert recall.run(recalled, SLUG).chapman["skipped"] == "single extractor set"


def test_comparable_sets_give_a_lower_bound(recalled):
    cfg = recall.load_config()
    cfg.data["capture_recapture"]["min_size_ratio"] = 0.2
    c = recall.run(recalled, SLUG, cfg=cfg).chapman
    assert c["skipped"] is None and c["lower_bound"] is True
    assert c["chapman_estimate"] == pytest.approx(stats.chapman(c["n1"], c["n2"], c["m"]))
    text = "\n".join(recall.format_chapman(c))
    assert "chapman_estimate:" in text and "lower_bound: true" in text


# --- CLI and report --------------------------------------------------------

def test_cli_recall(recalled, ledger_path, capsys):
    assert cli.main(["recall", "--paper", SLUG, "--query", QUERY["query_id"],
                     "--ledger", str(ledger_path)]) == 0
    out = capsys.readouterr().out
    assert "claim_present" in out and "chapman_estimate: skipped: asymmetric sets" in out
    assert "unused_pool: 1" in out


def test_report_fills_the_recall_section(recalled, source_root):
    recall.run(recalled, SLUG, QUERY["query_id"])
    text = report.render(recalled, source_root, SLUG, QUERY["query_id"])
    body = text.split("## 재현율 (Recall)", 1)[1].split("\n## ", 1)[0]
    assert "not-run" not in body
    assert "claim_present" in body and "not-applicable: extractor runs are frozen" in body
    assert "lower_bound: true" in body
