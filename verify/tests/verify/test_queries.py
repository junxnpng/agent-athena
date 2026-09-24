from __future__ import annotations
import sqlite3

import pytest

from tools.verify import cli, ledger, queries

GOLD_QUERY = queries.CONFIG_DIR / "gold-kv-reuse.json"


def _write(tmp_path, body):
    path = tmp_path / "q.json"
    path.write_text(body)
    return path


def test_default_query_file_is_valid():
    q = queries.load(GOLD_QUERY)
    assert q["query_id"] == "gold-kv-reuse"
    assert q["topic"] and q["claim_text"]
    assert "한줄평" not in q["claim_text"]


def test_register_once(ledger_path):
    conn = ledger.init(ledger_path)
    queries.register(conn, queries.load(GOLD_QUERY))
    queries.register(conn, queries.load(GOLD_QUERY))  # identical re-register is a no-op
    assert conn.execute("select count(*) from queries").fetchone()[0] == 1
    assert queries.get(conn, "gold-kv-reuse")["topic"]


def test_changed_query_is_refused(ledger_path, tmp_path):
    conn = ledger.init(ledger_path)
    queries.register(conn, queries.load(GOLD_QUERY))
    changed = dict(queries.load(GOLD_QUERY), claim_text="different")
    with pytest.raises(queries.QueryError, match="already registered"):
        queries.register(conn, changed)


def test_missing_fields_rejected(tmp_path):
    with pytest.raises(queries.QueryError, match="claim_text"):
        queries.load(_write(tmp_path, '{"query_id": "x", "topic": "t", "source": "s"}'))
    with pytest.raises(queries.QueryError, match="mapping"):
        queries.load(_write(tmp_path, '["a"]'))


def test_resolve_by_id_or_file(ledger_path, tmp_path):
    conn = ledger.init(ledger_path)
    q = queries.resolve(conn, str(GOLD_QUERY))
    assert queries.resolve(conn, q["query_id"]) == q
    with pytest.raises(queries.QueryError, match="unknown query"):
        queries.resolve(conn, "nope")


def test_register_cli(tmp_path, capsys):
    path = tmp_path / "l.sqlite"
    assert cli.main(["query", "register", "--file", str(GOLD_QUERY), "--ledger", str(path)]) == 0
    assert sqlite3.connect(path).execute("select count(*) from queries").fetchone()[0] == 1
    assert "gold-kv-reuse" in capsys.readouterr().out


def test_unconfirmed_query_is_refused_where_confirmation_is_required(ledger_path):
    q = queries.load(GOLD_QUERY)
    assert q["confirmed_by"] is None
    with pytest.raises(queries.QueryError, match="not confirmed"):
        queries.require_confirmed(q)
    queries.require_confirmed(dict(q, confirmed_by="user"))
