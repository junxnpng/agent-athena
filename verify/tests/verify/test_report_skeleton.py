from __future__ import annotations
import json

import pytest

from tools.verify import cli, judge, report
from .conftest import QUERY, SLUG
from .test_judge_io import PROTOCOL, _verdicts, _write

SECTIONS = ("존재 (Existence)", "합치 (Alignment)", "재현율 (Recall)", "조건 보존 (Condition preservation)")


def test_skeleton_has_four_sections_and_allows_not_run(checked, source_root):
    text = report.render(checked, source_root, SLUG, QUERY["query_id"])
    for name in SECTIONS:
        assert f"## {name}" in text
    assert text.count("not-run") == 3  # alignment, recall and conditions have not run yet
    head = text.split("## 존재 (Existence)")[0]
    assert "L1 grade distribution" in head and "| claude | 4 |" in head
    assert "waiver_rate" in text and "rows" in text


def test_strict_report_refuses_not_run_sections(checked, source_root):
    with pytest.raises(report.ReportIncomplete, match="Alignment, Recall, Condition preservation"):
        report.render(checked, source_root, SLUG, QUERY["query_id"], strict=True)


def test_alignment_section_after_a_round_trip(checked, source_root, tmp_path):
    judge.sweep(checked, SLUG, QUERY["query_id"])
    ex = judge.export(checked, source_root, SLUG, QUERY["query_id"], out_dir=tmp_path)
    judge.import_verdicts(checked, source_root, ex.path, _write(tmp_path, _verdicts(ex)), "test-judge",
                          PROTOCOL, ex.sha256)
    text = report.render(checked, source_root, SLUG, QUERY["query_id"])
    section = text.split("## 합치 (Alignment)")[1].split("## 재현율 (Recall)")[0]
    assert "not-run" not in section
    assert "escalation_rate: 0.600 (observed)" in section
    assert "test-judge" in section and "supports" in section and "faithfulness" in section
    assert text.count("not-run") == 2


def test_report_needs_an_existence_run(ledger_path, source_root):
    from tools.verify import ledger
    with pytest.raises(report.ReportIncomplete, match="l1"):
        report.render(ledger.init(ledger_path), source_root, SLUG, QUERY["query_id"])


def test_slice_facts(checked, source_root, tmp_path):
    judge.sweep(checked, SLUG, QUERY["query_id"])
    ex = judge.export(checked, source_root, SLUG, QUERY["query_id"], out_dir=tmp_path)
    res = judge.import_verdicts(checked, source_root, ex.path, _write(tmp_path, _verdicts(ex)), "test-judge",
                                PROTOCOL, ex.sha256, tokens_in=900, tokens_out=100)
    facts = report.slice_facts(checked, SLUG, QUERY["query_id"])
    assert facts["run_id"] == res.run_id
    assert facts["l1_grades"]["claude"]["exact"] == 3
    assert facts["conditions_complete_rows"] == {"rows": 0, "of": 5}
    assert facts["derived_from_rows"] == {"rows": 0, "of": 5}
    assert facts["tier1"]["rows"] == 3
    assert facts["tier1"]["alignment"] == {"supports": 3, "refutes": 0, "insufficient": 0,
                                           "unknown": 0}
    assert facts["tier1"]["unknown_ratio"] == 0
    assert facts["tier1"]["faithfulness"]["unknown"] == 3
    assert facts["round_trip"]["tokens"] == 1000 and facts["round_trip"]["wallclock_s"] >= 0
    path = report.write_slice_facts(facts, tmp_path)
    assert path.name == f"slice-facts-{res.run_id}.json"
    assert json.loads(path.read_text(encoding="utf-8"))["tier1"]["rows"] == 3


def test_slice_facts_need_a_judge_run(checked):
    with pytest.raises(report.ReportIncomplete, match="judge import"):
        report.slice_facts(checked, SLUG, QUERY["query_id"])


def test_cli_report_and_facts(checked, ledger_path, source_root, tmp_path, capsys):
    checked.close()
    out = tmp_path / "r.md"
    args = ["--paper", SLUG, "--query", QUERY["query_id"], "--ledger", str(ledger_path)]
    assert cli.main(["report", *args, "--source-root", str(source_root), "--out", str(out)]) == 0
    assert "## 재현율 (Recall)" in out.read_text(encoding="utf-8")
    assert cli.main(["slice", "facts", *args, "--out-dir", str(tmp_path)]) == 1
    assert "judge import" in capsys.readouterr().err


def test_condition_section_after_l2_and_l6(checked, source_root):
    from tools.verify import l2_schema, l6_arith
    l2_schema.run(checked, SLUG)
    text = report.render(checked, source_root, SLUG, QUERY["query_id"])
    section = text.split("## 조건 보존 (Condition preservation)")[1].split("## 적용 대상 없음 (Not applicable)")[0]
    assert "quarantine_rate: 1.000 (5/5) — input diagnostic, prior expectation 100%" in section
    assert "L6 arithmetic: not-run" in section
    l6_arith.run(checked, source_root, SLUG)
    text = report.render(checked, source_root, SLUG, QUERY["query_id"])
    section = text.split("## 조건 보존 (Condition preservation)")[1].split("## 적용 대상 없음 (Not applicable)")[0]
    assert "not-run" not in section
    assert "derived_from: applicable_rows: 0 (of 5 rows)" in section
    assert "intra_doc_conflict: 0 pairs" in section and "l6-arith-v1" in section
    tail = text.split("## 적용 대상 없음 (Not applicable)")[1]
    assert "derived_from recomputation: applicable_rows: 0" in tail
