"""Elusion sample: registered n from the unused-paragraph frame, drawn once, exact upper bound."""
from __future__ import annotations
import csv

import pytest

from tools.verify import cli, ledger, recall, stats
from .conftest import SLUG
from .test_recall import register_gold


@pytest.fixture
def recalled(checked, tmp_path):
    register_gold(checked, tmp_path)
    return checked


def _rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def _write(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), delimiter="\t")
        w.writeheader()
        w.writerows(rows)


def test_draw_is_seeded_and_exact():
    pool = [{"para_id": f"p{i}", "seq": i} for i in range(40)]
    a = recall.draw(pool, 7, 20260922)
    assert a == recall.draw(list(reversed(pool)), 7, 20260922)
    assert len(a) == 7 and len({b["para_id"] for b in a}) == 7


def test_status_reports_the_pool_and_the_achievable_bound(recalled):
    e = recall.elusion_status(recalled, SLUG)
    assert e["unused_pool"] == len(ledger.unused_pool(recalled, SLUG)) == 1
    assert e["elusion_n"] == 1 and e["sample"] is None
    assert e["achievable_upper"] == pytest.approx(stats.upper_bound(0, 1))
    assert e["n_for_target"] == 59
    text = "\n".join(recall.format_elusion(e))
    assert "5% upper bound is unreachable" in text and "k=1" in text


def test_n_for_target_matches_the_bound():
    n = recall.n_for_target(0.05, 0.95)
    assert stats.upper_bound(0, n) <= 0.05 < stats.upper_bound(0, n - 1)


def test_export_draws_exactly_n_and_seals_the_sample(recalled, tmp_path):
    out = tmp_path / "elusion.tsv"
    sample = recall.export_elusion(recalled, SLUG, out)
    rows = _rows(out)
    assert len(rows) == sample["n"] == 1
    assert rows[0]["para_id"] == ledger.unused_pool(recalled, SLUG)[0]["para_id"]
    assert rows[0]["missed_claims"] == "" and "load balancer" in rows[0]["text"]
    assert recall.elusion_status(recalled, SLUG)["sample"]["sample_id"] == sample["sample_id"]


def test_resampling_is_forbidden(recalled, tmp_path):
    recall.export_elusion(recalled, SLUG, tmp_path / "a.tsv")
    with pytest.raises(recall.RecallError, match="resampling forbidden"):
        recall.export_elusion(recalled, SLUG, tmp_path / "b.tsv")
    assert not (tmp_path / "b.tsv").exists()


def test_pool_smaller_than_n_is_refused(recalled, tmp_path, monkeypatch):
    monkeypatch.setattr(ledger, "unused_pool", lambda *a, **k: [])
    with pytest.raises(recall.RecallError, match="pool 0 < elusion_n 1"):
        recall.export_elusion(recalled, SLUG, tmp_path / "a.tsv")


def test_review_import_gives_the_observed_bound(recalled, tmp_path):
    out = tmp_path / "e.tsv"
    recall.export_elusion(recalled, SLUG, out)
    rows = _rows(out)
    rows[0]["missed_claims"] = "0"
    _write(out, rows)
    res = recall.import_elusion(recalled, SLUG, out, "tester")
    assert (res["k"], res["n"]) == (0, 1)
    e = recall.elusion_status(recalled, SLUG)
    assert e["review"]["reviewer"] == "tester"
    assert e["observed_upper"] == pytest.approx(stats.upper_bound(0, 1))
    with pytest.raises(recall.RecallError, match="already recorded"):
        recall.import_elusion(recalled, SLUG, out, "tester")


@pytest.mark.parametrize("edit, message", [
    (lambda r: r.update(missed_claims=""), "not reviewed"),
    (lambda r: r.update(missed_claims="-1"), "not a count"),
    (lambda r: r.update(para_id="codex_raw#9999"), "sampled blocks"),
    (lambda r: r.update(sample_id="other"), "sample_id"),
])
def test_review_import_refuses_a_bad_file(recalled, tmp_path, edit, message):
    out = tmp_path / "e.tsv"
    recall.export_elusion(recalled, SLUG, out)
    rows = _rows(out)
    rows[0]["missed_claims"] = "0"
    edit(rows[0])
    _write(out, rows)
    with pytest.raises(recall.RecallError, match=message):
        recall.import_elusion(recalled, SLUG, out, "tester")


def test_review_needs_a_sample(recalled, tmp_path):
    with pytest.raises(recall.RecallError, match="no elusion sample"):
        recall.import_elusion(recalled, SLUG, tmp_path / "x.tsv", "tester")


def test_cli_export_twice_exits_one(recalled, ledger_path, tmp_path, capsys):
    args = ["recall", "--paper", SLUG, "--ledger", str(ledger_path)]
    assert cli.main(args + ["--elusion-export", str(tmp_path / "a.tsv")]) == 0
    out = capsys.readouterr().out
    assert "unused_pool: 1" in out and "sampled: 1" in out
    assert cli.main(args + ["--elusion-export", str(tmp_path / "b.tsv")]) == 1
    assert "resampling forbidden" in capsys.readouterr().err


def test_cli_import_needs_a_reviewer(recalled, ledger_path, tmp_path, capsys):
    args = ["recall", "--paper", SLUG, "--ledger", str(ledger_path)]
    assert cli.main(args + ["--elusion-export", str(tmp_path / "a.tsv")]) == 0
    with pytest.raises(SystemExit):
        cli.main(args + ["--elusion-import", str(tmp_path / "a.tsv")])


POOL_SENTENCE = ("This paragraph is never quoted by any extractor and talks about the load balancer,"
                 " its hashing policy, and the number of replicas that the operator provisions each day.")


def test_missed_gold_sentences_are_located_in_pool_or_used_blocks(checked, tmp_path):
    register_gold(checked, tmp_path, "Demo**한줄평: x****Requests span a wide range of token lengths. "
                  "Figure 2 shows that input lengths are much longer than output lengths for every"
                  f" model family we study in the trace. {POOL_SENTENCE} Nothing like this is in the"
                  " paper at all.")
    s = recall.run(checked, SLUG)
    pool_id = ledger.unused_pool(checked, SLUG)[0]["para_id"]
    assert s.misses["pool"] == {pool_id: [f"{SLUG}:s003"]}
    assert (s.misses["used"], s.misses["unlocated"]) == (0, 1)
    recall.export_elusion(checked, SLUG, tmp_path / "e.tsv")
    e = recall.elusion_status(checked, SLUG)
    text = "\n".join(recall.format_elusion(e, recall.gold_floor(s, e)))
    assert "gold floor: k >= 1" in text
