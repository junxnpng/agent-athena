from __future__ import annotations
from tools.verify.convert import codex, common
from .conftest import GOLD_SLUG, SLUG


def test_single_fragment_becomes_quote(source_root):
    res = codex.convert(source_root, SLUG)
    assert [r["row_id"] for r in res.rows] == ["codex:DM001.q1"]
    row = res.rows[0]
    assert row["quote"].startswith("Prefix reuse is common")
    assert row["l1_tautological"] == 1
    assert row["conditions"] == {}
    assert row["conditions_raw"] == "free prose about scope"
    assert row["numbers"] == [{"raw": "UTC; 24h"}]
    assert row["locator"]["fragment_id"] == "p03b100"
    assert row["locator"]["para_id"] == "codex_raw#0004"
    assert row["locator"]["section"] == "§3.1"


def test_multi_fragment_is_quarantined_with_fragments_kept(source_root):
    res = codex.convert(source_root, SLUG)
    [q] = res.quarantined
    assert q["record_id"] == "DM002" and q["reason_code"] == "multi_fragment_no_quote"
    assert len(res.fragments) == 3
    assert {f["record_id"] for f in res.fragments} == {"DM001", "DM002"}
    assert res.closed == res.source_records == 2


def test_numbers_are_kept_raw():
    assert codex._numbers("미보고") == [{"raw": "미보고"}]
    assert codex._numbers("  ") == []


def test_gold_paper_counts(real_root):
    res = codex.convert(real_root, GOLD_SLUG)
    assert (res.source_records, len(res.rows), res.closed) == (37, 7, 37)
    assert {q["reason_code"] for q in res.quarantined} == {"multi_fragment_no_quote"}
    text = common.format_summary(res)
    assert ("source_records: 37, rows: 7, quarantined_records: 30 (multi_fragment_no_quote),"
            " closed: 37/37") in text


def test_fragment_without_page_or_location_is_unresolved(source_root):
    import json
    path = source_root / "docs/patterns/260911_codex_quotes_final/codex_pattern_data.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["records"][0]["location"] = ""
    data["records"][0]["fragments"][0]["page"] = None
    path.write_text(json.dumps(data, ensure_ascii=False))
    res = codex.convert(source_root, SLUG)
    assert {q["record_id"]: q["reason_code"] for q in res.quarantined}["DM001"] == "locator_unresolved"


def test_empty_fragment_is_no_quote(source_root):
    import json
    path = source_root / "docs/patterns/260911_codex_quotes_final/codex_pattern_data.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["records"][0]["fragments"][0]["text"] = "  \n"
    path.write_text(json.dumps(data, ensure_ascii=False))
    res = codex.convert(source_root, SLUG)
    assert {q["record_id"]: q["reason_code"] for q in res.quarantined}["DM001"] == "no_quote"
