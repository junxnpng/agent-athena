from __future__ import annotations
import sqlite3

import pytest

from tools.verify import cli, ledger


def test_init_creates_eleven_tables(ledger_path):
    conn = ledger.init(ledger_path)
    names = {r[0] for r in conn.execute("select name from sqlite_master where type='table'"
                                            " and name not like 'sqlite_%'")}
    assert names == set(ledger.TABLES)
    assert len(ledger.TABLES) == 11
    ledger.init(ledger_path)  # idempotent


def test_checks_provenance_columns_not_null(ledger_path):
    conn = ledger.init(ledger_path)
    cols = {r[1]: r[3] for r in conn.execute("pragma table_info(checks)")}
    assert cols["verifier_id"] == 1 and cols["protocol_ver"] == 1
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("insert into checks(row_id, layer, verifier_id, protocol_ver, verdict)"
                     " values ('x', 'l1', NULL, 'v1', 'PASS')")


def _gold(conn):
    conn.execute("insert into gold(gold_id, paper_id, seq, text, kind, source)"
                 " values ('g1', 'p', 1, 'orig', 'sentence', 'hand')")


def test_gold_rejects_direct_update_and_delete(ledger_path):
    conn = ledger.init(ledger_path)
    _gold(conn)
    with pytest.raises(sqlite3.IntegrityError, match="audit"):
        conn.execute("update gold set text='edited' where gold_id='g1'")
    with pytest.raises(sqlite3.IntegrityError, match="audit"):
        conn.execute("delete from gold where gold_id='g1'")


def test_gold_revision_through_audit(ledger_path):
    conn = ledger.init(ledger_path)
    _gold(conn)
    conn.execute("insert into audits(audit_id, gold_id, auditor, decision, new_text)"
                 " values ('a1', 'g1', 'human', 'revise', 'fixed')")
    conn.execute("update gold set text='fixed', revision=revision+1, audit_id='a1' where gold_id='g1'")
    assert conn.execute("select text, revision from gold").fetchone() == ("fixed", 2)
    with pytest.raises(sqlite3.IntegrityError):  # the same audit cannot be replayed
        conn.execute("update gold set text='again', revision=revision+1, audit_id='a1'")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("update audits set decision='confirm'")


def test_claims_status_constraints(ledger_path):
    conn = ledger.init(ledger_path)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("insert into claims(row_id, record_id, paper_id, extractor_id, run_id, status)"
                     " values ('c:x.q1', 'x', 'p', 'c', 'r', 'row')")  # a row needs a quote
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("insert into claims(row_id, record_id, paper_id, extractor_id, run_id, status)"
                     " values ('c:x', 'x', 'p', 'c', 'r', 'quarantined')")  # needs a reason


def test_ledger_init_cli(tmp_path, capsys):
    path = tmp_path / "l.sqlite"
    assert cli.main(["ledger", "init", "--ledger", str(path)]) == 0
    assert path.exists()
    assert "11 tables" in capsys.readouterr().out


def _load(ledger_path, source_root):
    from tools.verify.convert import claude, codex
    from .conftest import SLUG
    conn = ledger.init(ledger_path)
    for mod in (claude, codex):
        ledger.import_converted(conn, mod.convert(source_root, SLUG).payload(), source_root)
    return conn


def test_import_registers_rows_quarantine_and_texts(ledger_path, source_root):
    conn = _load(ledger_path, source_root)
    status = dict(conn.execute("select status, count(*) from claims group by status").fetchall())
    assert status == {"row": 5, "quarantined": 3}
    variants = dict(conn.execute(
        "select variant, count(*) from paragraphs group by variant").fetchall())
    assert variants == {"codex_raw": 6, "codex_layout": 1, "claude_body": 6, "codex_fragment": 3}
    paper = conn.execute("select variants_json, pdf_sha256 from papers").fetchone()
    assert '"claude_column": "unavailable"' in paper[0] and paper[1]
    runs = conn.execute("select count(*) from runs where run_kind='convert'").fetchone()[0]
    assert runs == 2


def test_import_is_idempotent(ledger_path, source_root):
    _load(ledger_path, source_root)
    conn = _load(ledger_path, source_root)
    assert conn.execute("select count(*) from claims").fetchone()[0] == 8


def test_import_refuses_changed_text(ledger_path, source_root):
    from tools.verify.convert import claude
    from .conftest import SLUG
    conn = _load(ledger_path, source_root)
    raw = source_root / f"papers/codex_source_text/codex_{SLUG}.txt"
    raw.write_text(raw.read_text(encoding="utf-8") + "\nextra\n")
    with pytest.raises(ledger.LedgerError, match="text changed"):
        ledger.import_converted(conn, claude.convert(source_root, SLUG).payload(), source_root)


def test_import_cli(ledger_path, source_root, tmp_path, capsys):
    from .conftest import SLUG
    out = tmp_path / "c.json"
    assert cli.main(["convert", "codex", "--paper", SLUG, "--source-root", str(source_root),
                     "--out", str(out)]) == 0
    assert cli.main(["ledger", "import", "--file", str(out), "--ledger", str(ledger_path),
                     "--source-root", str(source_root)]) == 0
    text = capsys.readouterr().out
    assert "rows: 1" in text and "quarantined: 1" in text
    assert cli.main(["paragraphs", "pool", "--paper", SLUG, "--ledger", str(ledger_path)]) == 0
    assert "unused_pool: 3" in capsys.readouterr().out


def test_gold_paper_pool(real_root, ledger_path):
    from tools.verify.convert import claude, codex
    from .conftest import GOLD_SLUG
    conn = ledger.init(ledger_path)
    for mod in (claude, codex):
        ledger.import_converted(conn, mod.convert(real_root, GOLD_SLUG).payload(), real_root)
    frame = ledger.frame_blocks(conn, GOLD_SLUG)
    pool = ledger.unused_pool(conn, GOLD_SLUG)
    assert len(frame) == 70
    assert len(pool) == 34


def test_sql_command_is_read_only(ledger_path, capsys):
    ledger.init(ledger_path).close()
    assert cli.main(["ledger", "sql", "select count(*) from queries", "--ledger", str(ledger_path)]) == 0
    assert capsys.readouterr().out.strip() == "0"
    assert cli.main(["ledger", "sql", "delete from queries", "--ledger", str(ledger_path)]) == 1
    assert "readonly" in capsys.readouterr().err


def test_sql_command_needs_existing_ledger(tmp_path, capsys):
    assert cli.main(["ledger", "sql", "select 1", "--ledger", str(tmp_path / "none.sqlite")]) == 1
    assert "no ledger" in capsys.readouterr().err


def test_gold_revision_must_carry_the_audit_text(ledger_path):
    conn = ledger.init(ledger_path)
    _gold(conn)
    conn.execute("insert into audits(audit_id, gold_id, auditor, decision, new_text)"
                 " values ('a1', 'g1', 'human', 'revise', 'fixed')")
    with pytest.raises(sqlite3.IntegrityError, match="audit"):
        conn.execute("update gold set text='other', revision=revision+1, audit_id='a1'")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("insert into audits(audit_id, gold_id, auditor, decision)"
                     " values ('a2', 'g1', 'human', 'revise')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("insert into gold(gold_id, paper_id, seq, text, kind, source)"
                     " values ('g2', 'p', 1, 'dup', 'sentence', 'hand')")


def test_import_refuses_a_different_paragraph_unit(ledger_path, source_root):
    from tools.verify.convert import claude, codex
    from .conftest import SLUG
    conn = ledger.init(ledger_path)
    ledger.import_converted(conn, claude.convert(source_root, SLUG).payload(), source_root)
    payload = codex.convert(source_root, SLUG).payload()
    payload["paragraph_unit"] = dict(payload["paragraph_unit"], min_words=30)
    with pytest.raises(ledger.LedgerError, match="paragraph unit"):
        ledger.import_converted(conn, payload, source_root)


def test_init_adds_new_columns_to_an_old_ledger(ledger_path):
    conn = sqlite3.connect(ledger_path)
    conn.execute("create table checks (check_id integer primary key, row_id text not null,"
                 " layer text not null, verifier_id text not null, protocol_ver text not null,"
                 " run_id text, verdict text not null, grade text, matched_variant text,"
                 " char_start integer, char_end integer, evidence_span text, reason_code text,"
                 " l1_tautological integer not null default 0, detail_json text,"
                 " created_at text not null default '')")
    conn.close()
    conn = ledger.init(ledger_path)
    cols = {r[1] for r in conn.execute("pragma table_info(checks)")}
    assert {"query_id", "tier"} <= cols
