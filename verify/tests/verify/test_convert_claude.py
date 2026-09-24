from __future__ import annotations
import json

import pytest

from tools.verify import cli
from tools.verify.convert import claude, common
from .conftest import GOLD_SLUG, SLUG


def test_rows_are_one_per_quote(source_root):
    res = claude.convert(source_root, SLUG)
    ids = [r["row_id"] for r in res.rows]
    assert ids == ["claude:DM-A1.q1", "claude:DM-B1.q1", "claude:DM-B1.q2", "claude:DM-C1.q1"]
    assert {q["record_id"]: q["reason_code"] for q in res.quarantined} == {
        "DM-A2": "no_quote", "DM-Z9": "kind_unmapped"}
    assert res.source_records == 5
    assert res.closed == 5


def test_kind_mapping_uses_leftmost_label(source_root):
    rows = {r["row_id"]: r for r in claude.convert(source_root, SLUG).rows}
    assert rows["claude:DM-A1.q1"]["kind"] == "measurement"
    assert rows["claude:DM-B1.q1"]["kind"] == "measurement"
    assert rows["claude:DM-C1.q1"]["kind"] == "extrapolation"
    assert rows["claude:DM-B1.q1"]["source_kind"] == "실제 관측 + 저자의 해석"


def test_absent_fields_are_not_invented(source_root):
    row = claude.convert(source_root, SLUG).rows[0]
    assert row["conditions"] == {}
    assert row["numbers"] == [{"raw": "14.2:1 (our arithmetic)"}]
    assert row["l1_tautological"] == 0
    assert row["extractor_id"] == "claude"
    assert row["run_id"].startswith("claude-")
    assert "2026-09-15" not in row["run_id"]


def test_locator_resolves_to_raw_block(source_root):
    rows = {r["row_id"]: r for r in claude.convert(source_root, SLUG).rows}
    loc = rows["claude:DM-A1.q1"]["locator"]
    assert loc == {"section": "§3", "page": 3, "para_id": "codex_raw#0002",
                   "location_raw": "§3 · p.3 좌단"}
    assert rows["claude:DM-B1.q2"]["locator"]["para_id"] == "codex_raw#0004"


def test_summary_format(source_root):
    text = common.format_summary(claude.convert(source_root, SLUG))
    assert "source_records: 5" in text
    assert "rows: 4" in text
    assert "quarantined_records: 2 (kind_unmapped: 1, no_quote: 1)" in text
    assert "closed: 5/5" in text


def test_kind_map_is_deterministic():
    km = common.KindMap.load()
    assert km.map("실제 관측 — 스키마") == "measurement"
    assert km.map("시뮬레이션 — 설정") == "extrapolation"
    assert km.map("저자의 요약") == "author_interpretation"
    assert km.map("2차 인용 / 저자의 해석") == "author_interpretation"
    assert km.map("2차 인용") is None
    assert km.map("") is None


def test_unknown_paper_fails(source_root):
    with pytest.raises(common.ConvertError, match="no claude records"):
        claude.convert(source_root, "nope__nope")


def test_convert_cli_writes_file(source_root, tmp_path, capsys):
    out = tmp_path / "c.json"
    assert cli.main(["convert", "claude", "--paper", SLUG, "--source-root", str(source_root),
                     "--out", str(out)]) == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["extractor_id"] == "claude" and len(payload["rows"]) == 4
    assert "closed: 5/5" in capsys.readouterr().out


def test_missing_source_root(monkeypatch, capsys):
    monkeypatch.delenv("KVCPOOL", raising=False)
    assert cli.main(["convert", "claude", "--paper", SLUG]) == 2
    assert "KVCPOOL" in capsys.readouterr().err


def test_gold_paper_counts(real_root):
    res = claude.convert(real_root, GOLD_SLUG)
    assert (res.source_records, len(res.rows), res.closed) == (30, 44, 30)
    assert [q["reason_code"] for q in res.quarantined] == ["no_quote", "no_quote"]
    text = common.format_summary(res)
    assert "source_records: 30, rows: 44, quarantined_records: 2 (no_quote), closed: 30/30" in text


def test_section_is_null_without_section_token():
    assert common.section_of("p.3 좌단") is None
    assert common.section_of("§3.2 · p.4 우단") == "§3.2"


def test_payload_records_paragraph_unit(source_root):
    assert claude.convert(source_root, SLUG).payload()["paragraph_unit"] == common.paragraph_unit()


def test_run_id_names_the_paper(source_root):
    assert claude.convert(source_root, SLUG).run_id.endswith(f"-{SLUG}")


def test_closed_refuses_overlap(source_root):
    res = claude.convert(source_root, SLUG)
    res.quarantined.append({"record_id": res.rows[0]["record_id"], "reason_code": "no_quote"})
    with pytest.raises(common.ConvertError, match="both"):
        res.closed


def test_payload_carries_title(source_root):
    from tools.verify.convert import codex
    assert codex.convert(source_root, SLUG).payload()["title"] == "Demo"
