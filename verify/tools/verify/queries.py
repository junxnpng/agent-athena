"""Queries: the topic and claim a record set is judged against."""
from __future__ import annotations

import pathlib
import sqlite3

import json

from .ledger import now
from .paths import CONFIG_DIR as _CONFIG

CONFIG_DIR = _CONFIG / "queries"
FIELDS = ("query_id", "topic", "claim_text", "source")
COLUMNS = FIELDS + ("confirmed_by",)


class QueryError(RuntimeError):
    pass


def load(path: pathlib.Path | str) -> dict:
    try:
        data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise QueryError(f"{path}: cannot read a JSON query: {exc}") from exc
    if not isinstance(data, dict):
        raise QueryError(f"{path}: a query file must be a mapping")
    missing = [f for f in FIELDS if not str(data.get(f) or "").strip()]
    if missing:
        raise QueryError(f"{path}: missing {', '.join(missing)}")
    query = {f: str(data[f]).strip() for f in FIELDS}
    confirmed = data.get("confirmed_by")
    query["confirmed_by"] = str(confirmed).strip() if confirmed else None
    return query


def require_confirmed(query: dict) -> None:
    """A query written by anyone but the user must be confirmed before it is judged against."""
    if not query.get("confirmed_by"):
        raise QueryError(f"query {query['query_id']} is not confirmed: set confirmed_by in its file"
                         " after reading it, and register it under a new id")


def register(conn: sqlite3.Connection, query: dict) -> None:
    """Insert a query; an identical re-register is a no-op, a changed one is refused."""
    old = get(conn, query["query_id"])
    if old is not None:
        if old != query:
            raise QueryError(f"query {query['query_id']} already registered with different content;"
                             " register it under a new id")
        return
    conn.execute("insert into queries(query_id, topic, claim_text, source, confirmed_by,"
                 " registered_at) values (?,?,?,?,?,?)", (*[query[f] for f in COLUMNS], now()))


def get(conn: sqlite3.Connection, query_id: str) -> dict | None:
    row = conn.execute("select query_id, topic, claim_text, source, confirmed_by from queries"
                       " where query_id=?", (query_id,)).fetchone()
    return dict(zip(COLUMNS, row)) if row else None


def resolve(conn: sqlite3.Connection, ref: str) -> dict:
    """`--query <id|file>`: a registered id, or a query file (registered on the way)."""
    path = pathlib.Path(ref)
    if path.suffix == ".json" and path.is_file():
        query = load(path)
        register(conn, query)
        return query
    query = get(conn, ref)
    if query is None:
        raise QueryError(f"unknown query {ref}: register it with `verify query register --file`")
    return query
