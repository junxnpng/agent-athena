"""File round trip with the judge: the export is sealed, the import only accepts what resolves."""
from __future__ import annotations
import hashlib
import json
import sqlite3

import pytest

from tools.verify import cli, judge, queries
from tools.verify.convert import common
from .conftest import QUERY, SLUG

PROTOCOL = judge.skill_protocol()


ROOT = [None]


@pytest.fixture(autouse=True)
def _root(source_root):
    ROOT[0] = source_root


@pytest.fixture
def exported(checked, source_root, tmp_path):
    judge.sweep(checked, SLUG, QUERY["query_id"])
    return checked, judge.export(checked, source_root, SLUG, QUERY["query_id"], tier="mid", context="para",
                                 swap_order=True, limit=20, out_dir=tmp_path)


def _span(item, part="quote"):
    ctx = item["context"]["text"]
    s, e = item["quote_span"]["start"], item["quote_span"]["end"]
    return {"start": s, "end": e, "text": ctx[s:e]}


def _verdicts(ex, override=None):
    override = override or {}
    lines = []
    for item in ex.payload["items"]:
        line = {"item": item["item"], "row_id": item["row_id"],
                "alignment": {"verdict": "supports", "evidence_span": _span(item), "rationale": "r"},
                "faithfulness": {"verdict": "unknown", "rationale": "cannot tell"}}
        line.update(override.get(item["item"], {}))
        lines.append(line)
    return lines


def _write(tmp_path, lines, name="v.jsonl"):
    path = tmp_path / name
    path.write_text("".join(json.dumps(l, ensure_ascii=False) + "\n" for l in lines))
    return path


def _import(conn, ex, path, **kw):
    args = dict(verifier_id="test-judge", protocol_ver=PROTOCOL, manifest=ex.sha256)
    args.update(kw)
    return judge.import_verdicts(conn, ROOT[0], ex.path, path, **args)


# --- export ---------------------------------------------------------------

def test_export_items_carry_the_query_and_context(exported):
    conn, ex = exported
    items = ex.payload["items"]
    assert [i["row_id"] for i in items] and len(items) == 3  # needs-judge rows only
    for item in items:
        assert item["query"]["topic"] == QUERY["topic"]
        assert item["query"]["claim_text"] == QUERY["claim_text"]
        ctx = item["context"]["text"]
        assert ctx[item["quote_span"]["start"]:item["quote_span"]["end"]]
        assert item["record_claim_text"]
    assert ex.sha256 == hashlib.sha256(ex.path.read_bytes()).hexdigest()
    run = conn.execute("select input_sha256 from runs where run_id=?", (ex.export_id,)).fetchone()
    assert run == (ex.sha256,)


def test_context_is_a_span_of_the_matched_variant(exported, source_root):
    _, ex = exported
    item = ex.payload["items"][0]
    c = item["context"]
    text = common.variant_paths(source_root, SLUG)[c["variant"]].read_text(encoding="utf-8")
    assert text[c["char_start"]:c["char_end"]] == c["text"]


def test_swap_order_alternates_presentation(exported):
    _, ex = exported
    orders = [tuple(i["presentation"]) for i in ex.payload["items"]]
    assert set(orders) == {("query", "evidence"), ("evidence", "query")}


def test_export_order_is_seeded_and_limited(checked, source_root, tmp_path):
    judge.sweep(checked, SLUG, QUERY["query_id"])
    a = judge.export(checked, source_root, SLUG, QUERY["query_id"], limit=2, out_dir=tmp_path / "a")
    b = judge.export(checked, source_root, SLUG, QUERY["query_id"], limit=2, out_dir=tmp_path / "b")
    assert [i["row_id"] for i in a.payload["items"]] == [i["row_id"] for i in b.payload["items"]]
    assert len(a.payload["items"]) == 2 and a.export_id != b.export_id


def test_export_refuses_unconfirmed_query_and_missing_sweep(checked, source_root, tmp_path):
    queries.register(checked, dict(QUERY, query_id="draft", confirmed_by=None))
    with pytest.raises(queries.QueryError, match="not confirmed"):
        judge.export(checked, source_root, SLUG, "draft", out_dir=tmp_path)
    with pytest.raises(judge.JudgeError, match="sweep"):
        judge.export(checked, source_root, SLUG, QUERY["query_id"], out_dir=tmp_path)


def test_export_dies_on_a_pdf_path(checked, source_root, tmp_path):
    judge.sweep(checked, SLUG, QUERY["query_id"])
    checked.execute("update claims set claim_text='see papers/demo.pdf' where row_id='claude:DM-A1.q1'")
    with pytest.raises(judge.JudgeError, match="PDF path"):
        judge.export(checked, source_root, SLUG, QUERY["query_id"], out_dir=tmp_path)


# --- import ---------------------------------------------------------------

def test_import_records_both_judgments_as_separate_columns(exported, tmp_path, source_root):
    conn, ex = exported
    res = _import(conn, ex, _write(tmp_path, _verdicts(ex)))
    assert res.rows == 3
    rows = conn.execute("select row_id, alignment, faithfulness, verifier_id, protocol_ver, tier,"
                        " query_id from v_judgments").fetchall()
    assert len(rows) == 3
    assert {r[1:] for r in rows} == {("supports", "unknown", "test-judge", PROTOCOL, "tier1",
                                      QUERY["query_id"])}
    for variant, start, end, span in conn.execute(
            "select matched_variant, char_start, char_end, evidence_span from checks"
            " where layer='align' and tier='tier1'"):
        text = common.variant_paths(source_root, SLUG)[variant].read_text(encoding="utf-8")
        assert text[start:end] == span
    budget = conn.execute("select stage, tier, rows, expensive_calls from budget").fetchall()
    assert budget == [("judge", "tier1", 3, 0)]


def test_supports_without_span_is_refused(exported, tmp_path):
    """V2-4: an empty evidence span cannot back supports or refutes."""
    conn, ex = exported
    for bad in ({"verdict": "supports", "evidence_span": {"start": 0, "end": 0, "text": ""}},
                {"verdict": "refutes"}):
        lines = _verdicts(ex, {1: {"alignment": bad}})
        with pytest.raises(judge.ImportRefused, match="evidence span"):
            _import(conn, ex, _write(tmp_path, lines))
    assert conn.execute("select count(*) from checks where tier='tier1'").fetchone() == (0,)


def test_manifest_mismatch_is_refused(exported, tmp_path):
    conn, ex = exported
    with pytest.raises(judge.ImportRefused, match="manifest"):
        _import(conn, ex, _write(tmp_path, _verdicts(ex)), manifest="0" * 64)


def test_edited_export_is_refused(exported, tmp_path):
    conn, ex = exported
    payload = json.loads(ex.path.read_text(encoding="utf-8"))
    payload["items"].pop()
    ex.path.write_text(json.dumps(payload))
    new_sha = hashlib.sha256(ex.path.read_bytes()).hexdigest()
    with pytest.raises(judge.ImportRefused, match="manifest"):
        _import(conn, ex, _write(tmp_path, _verdicts(ex)[:-1]), manifest=new_sha)


def test_row_count_mismatch_is_refused(exported, tmp_path):
    conn, ex = exported
    lines = _verdicts(ex)
    with pytest.raises(judge.ImportRefused, match="rows"):
        _import(conn, ex, _write(tmp_path, lines[:-1]))
    with pytest.raises(judge.ImportRefused, match="rows"):
        _import(conn, ex, _write(tmp_path, lines + [lines[0]]))


def test_unresolved_span_is_refused(exported, tmp_path):
    conn, ex = exported
    item = ex.payload["items"][0]
    span = dict(_span(item), text="words the context does not have")
    lines = _verdicts(ex, {1: {"alignment": {"verdict": "supports", "evidence_span": span}}})
    with pytest.raises(judge.ImportRefused, match="does not resolve"):
        _import(conn, ex, _write(tmp_path, lines))
    span = dict(_span(item), end=len(item["context"]["text"]) + 5)
    lines = _verdicts(ex, {1: {"alignment": {"verdict": "refutes", "evidence_span": span}}})
    with pytest.raises(judge.ImportRefused, match="does not resolve"):
        _import(conn, ex, _write(tmp_path, lines))


def test_missing_or_unknown_verdict_is_refused(exported, tmp_path):
    conn, ex = exported
    for bad in ({"faithfulness": {}}, {"alignment": {"verdict": "maybe"}}):
        with pytest.raises(judge.ImportRefused, match="verdict"):
            _import(conn, ex, _write(tmp_path, _verdicts(ex, {2: bad})))
    lines = _verdicts(ex)
    del lines[0]["alignment"]
    with pytest.raises(judge.ImportRefused, match="verdict"):
        _import(conn, ex, _write(tmp_path, lines))


def test_unknown_needs_no_span_and_rows_must_match_items(exported, tmp_path):
    conn, ex = exported
    lines = _verdicts(ex, {1: {"alignment": {"verdict": "unknown"}}})
    lines[1]["row_id"] = "claude:somewhere-else.q1"
    with pytest.raises(judge.ImportRefused, match="row_id"):
        _import(conn, ex, _write(tmp_path, lines))
    lines = _verdicts(ex, {1: {"alignment": {"verdict": "unknown"}}})
    assert _import(conn, ex, _write(tmp_path, lines)).verdicts["alignment"]["unknown"] == 1


def test_protocol_and_duplicate_import_are_refused(exported, tmp_path):
    conn, ex = exported
    path = _write(tmp_path, _verdicts(ex))
    with pytest.raises(judge.ImportRefused, match="protocol"):
        _import(conn, ex, path, protocol_ver="claim-judge-v0")
    _import(conn, ex, path)
    with pytest.raises(judge.ImportRefused, match="already imported"):
        _import(conn, ex, path)


def test_bad_json_line_is_refused(exported, tmp_path):
    conn, ex = exported
    path = tmp_path / "v.jsonl"
    path.write_text("{not json\n")
    with pytest.raises(judge.ImportRefused, match="line 1"):
        _import(conn, ex, path)


def test_judge_verdict_trigger(checked):
    with pytest.raises(sqlite3.IntegrityError, match="judge verdicts"):
        checked.execute("insert into checks(row_id, layer, verifier_id, protocol_ver, verdict, tier,"
                        " query_id) values ('claude:DM-A1.q1', 'align', 'j', 'p', 'supports',"
                        " 'tier1', 'demo-reuse')")
    with pytest.raises(sqlite3.IntegrityError, match="judge verdicts"):
        checked.execute("insert into checks(row_id, layer, verifier_id, protocol_ver, verdict, tier,"
                        " query_id) values ('claude:DM-A1.q1', 'align', 'j', 'p', 'needs-judge',"
                        " 'tier1', 'demo-reuse')")


def test_cli_round_trip(checked, ledger_path, source_root, tmp_path, capsys):
    checked.close()
    base = ["--ledger", str(ledger_path), "--source-root", str(source_root)]
    assert cli.main(["judge", "sweep", "--backend", "lexical", "--paper", SLUG,
                     "--ledger", str(ledger_path)]) == 0
    assert cli.main(["judge", "export", "--paper", SLUG, "--tier", "mid", "--query",
                     QUERY["query_id"], "--context", "para", "--swap-order", "--limit", "20",
                     "--out-dir", str(tmp_path), *base]) == 0
    out = capsys.readouterr().out
    export_path = next(l.split(" ", 1)[1] for l in out.splitlines() if l.startswith("export "))
    sha = next(l.split(" ", 1)[1] for l in out.splitlines() if l.startswith("manifest "))
    payload = json.loads(open(export_path).read())
    ex = judge.Export(payload["export_id"], __import__("pathlib").Path(export_path), sha, payload)
    path = _write(tmp_path, _verdicts(ex))
    assert cli.main(["judge", "import", "--export", export_path, "--verdicts", str(path),
                     "--verifier-id", "test-judge", "--protocol-ver", PROTOCOL,
                     "--manifest", sha, "--tokens-in", "1000", "--tokens-out", "200", *base]) == 0
    assert "imported 3 rows" in capsys.readouterr().out
    assert cli.main(["judge", "import", "--export", export_path, "--verdicts", str(path),
                     "--verifier-id", "test-judge", "--protocol-ver", PROTOCOL,
                     "--manifest", "0" * 64, *base]) == 1
    assert "manifest" in capsys.readouterr().err


def test_usage_is_recorded_around_the_round_trip(checked, source_root, tmp_path, usage_cache):
    usage_cache.write_text(json.dumps({"five_hour": {"utilization": 23, "resets_at": "r1"}}))
    judge.sweep(checked, SLUG, QUERY["query_id"])
    ex = judge.export(checked, source_root, SLUG, QUERY["query_id"], out_dir=tmp_path, agent="claude")
    usage_cache.write_text(json.dumps({"five_hour": {"utilization": 31, "resets_at": "r1"}}))
    res = judge.import_verdicts(checked, source_root, ex.path, _write(tmp_path, _verdicts(ex)),
                                "test-judge", PROTOCOL, ex.sha256)
    assert res.usage["points"] == 8
    meta = json.loads(checked.execute("select meta_json from runs where run_id=?",
                                      (res.run_id,)).fetchone()[0])
    assert meta["usage"]["start"]["used_pct"] == 23 and meta["usage"]["end"]["used_pct"] == 31
    assert "5h usage: 23% -> 31% (+8pt" in judge.format_import(res)
    from tools.verify import report
    assert report.slice_facts(checked, SLUG, QUERY["query_id"])["round_trip"]["usage_points"] == 8
    assert "5h usage: 23% -> 31%" in report.render(checked, source_root, SLUG, QUERY["query_id"])


def test_missing_usage_does_not_stop_the_round_trip(exported, tmp_path):
    conn, ex = exported
    res = _import(conn, ex, _write(tmp_path, _verdicts(ex)))
    assert res.usage["points"] is None and "unavailable" in judge.format_import(res)
