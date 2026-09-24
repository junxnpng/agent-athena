"""SQLite claim ledger: schema, integrity triggers, and import of converted records.

The ledger is a regenerable artifact kept outside git. Every check row carries
verifier_id and protocol_ver (NOT NULL). Gold rows cannot be updated or deleted
directly; a revision goes through an audit record and bumps gold.revision.
An existence-check row is PASS with a matched span or MISS without one, and
later layers see only the rows of v_l1_passed.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import pathlib
import sqlite3

from . import paragraphs as pg
from .convert import common
from .paths import sha256_file

TABLES = ("papers", "paragraphs", "queries", "claims", "runs", "checks", "gold",
          "audits", "injections", "waivers", "budget")
# Layers after the existence check; each takes its rows from l1_passed only.
DOWNSTREAM_LAYERS = ("l2_schema", "l6_arith", "judge", "recall")

DDL = """
CREATE TABLE IF NOT EXISTS papers (
    paper_id      TEXT PRIMARY KEY,
    title         TEXT,
    pdf_path      TEXT,
    pdf_sha256    TEXT,
    variants_json TEXT NOT NULL,
    registered_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS paragraphs (
    paper_id    TEXT NOT NULL REFERENCES papers(paper_id),
    variant     TEXT NOT NULL,
    para_id     TEXT NOT NULL,
    seq         INTEGER,
    text        TEXT NOT NULL,
    sha256      TEXT NOT NULL,
    word_count  INTEGER NOT NULL,
    page        INTEGER,
    bbox_json   TEXT,
    PRIMARY KEY (paper_id, variant, para_id)
);
CREATE TABLE IF NOT EXISTS queries (
    query_id      TEXT PRIMARY KEY,
    topic         TEXT NOT NULL,
    claim_text    TEXT NOT NULL,
    source        TEXT NOT NULL,
    confirmed_by  TEXT,
    registered_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS runs (
    run_id            TEXT PRIMARY KEY,
    run_kind          TEXT NOT NULL,
    extractor_id      TEXT,
    input_sha256      TEXT,
    thresholds_sha256 TEXT,
    protocol_ver      TEXT,
    meta_json         TEXT,
    created_at        TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS claims (
    row_id          TEXT PRIMARY KEY,
    record_id       TEXT NOT NULL,
    paper_id        TEXT NOT NULL REFERENCES papers(paper_id),
    extractor_id    TEXT NOT NULL,
    run_id          TEXT NOT NULL REFERENCES runs(run_id),
    status          TEXT NOT NULL CHECK (status IN ('row', 'quarantined')),
    reason_code     TEXT,
    quote           TEXT,
    section         TEXT,
    page            INTEGER,
    para_id         TEXT,
    para_ids_json   TEXT,
    claim_text      TEXT,
    conditions_json TEXT,
    conditions_raw  TEXT,
    numbers_json    TEXT,
    kind            TEXT,
    source_kind     TEXT,
    l1_tautological INTEGER NOT NULL DEFAULT 0,
    record_json     TEXT NOT NULL,
    imported_at     TEXT NOT NULL,
    CHECK (status != 'row' OR quote IS NOT NULL),
    CHECK (status != 'quarantined' OR reason_code IS NOT NULL)
);
CREATE TABLE IF NOT EXISTS checks (
    check_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    row_id          TEXT NOT NULL,
    layer           TEXT NOT NULL,
    verifier_id     TEXT NOT NULL,
    protocol_ver    TEXT NOT NULL,
    run_id          TEXT,
    verdict         TEXT NOT NULL,
    grade           TEXT,
    matched_variant TEXT,
    char_start      INTEGER,
    char_end        INTEGER,
    evidence_span   TEXT,
    reason_code     TEXT,
    l1_tautological INTEGER NOT NULL DEFAULT 0,
    detail_json     TEXT,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    query_id        TEXT,
    tier            TEXT
);
CREATE TABLE IF NOT EXISTS audits (
    audit_id         TEXT PRIMARY KEY,
    gold_id          TEXT,
    row_id           TEXT,
    auditor          TEXT NOT NULL,
    decision         TEXT NOT NULL CHECK (decision IN ('confirm', 'revise', 'dispute', 'reject')),
    new_text         TEXT,
    dispute_evidence TEXT,
    created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    CHECK (decision != 'revise' OR new_text IS NOT NULL)
);
CREATE TABLE IF NOT EXISTS gold (
    gold_id           TEXT PRIMARY KEY,
    paper_id          TEXT NOT NULL,
    seq               INTEGER NOT NULL,
    text              TEXT NOT NULL,
    kind              TEXT NOT NULL CHECK (kind IN ('sentence', 'user_note')),
    source            TEXT NOT NULL CHECK (source IN ('hand', 'planted', 'target')),
    owner             TEXT,
    disputable        INTEGER NOT NULL DEFAULT 1,
    boundary_repaired INTEGER NOT NULL DEFAULT 0,
    revision          INTEGER NOT NULL DEFAULT 1,
    audit_id          TEXT REFERENCES audits(audit_id),
    registered_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE (paper_id, kind, seq)
);
CREATE TABLE IF NOT EXISTS injections (
    inj_id          TEXT PRIMARY KEY,
    run_id          TEXT,
    row_id          TEXT NOT NULL,
    operator        TEXT NOT NULL,
    is_equivalence  INTEGER NOT NULL DEFAULT 0,
    seed            INTEGER,
    mutated_json    TEXT,
    target_layer    TEXT,
    baseline_json   TEXT,
    mutated_result  TEXT,
    detected        INTEGER,
    not_applicable  INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE TABLE IF NOT EXISTS waivers (
    waiver_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id            TEXT NOT NULL,
    row_ref             TEXT NOT NULL,
    frag_sha1_12        TEXT,
    reason_code         TEXT NOT NULL,
    reason_text         TEXT,
    verification_method TEXT,
    source_file         TEXT,
    UNIQUE (paper_id, row_ref, frag_sha1_12)
);
CREATE TABLE IF NOT EXISTS budget (
    budget_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          TEXT NOT NULL,
    stage           TEXT NOT NULL,
    tier            TEXT,
    rows            INTEGER NOT NULL,
    tokens_in       INTEGER,
    tokens_out      INTEGER,
    wallclock_s     REAL,
    expensive_calls INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TRIGGER IF NOT EXISTS checks_l1_closed
BEFORE INSERT ON checks
WHEN NEW.layer = 'l1' AND NOT (
    (NEW.verdict = 'PASS' AND NEW.grade IS NOT NULL AND NEW.grade != 'MISS'
     AND NEW.matched_variant IS NOT NULL AND NEW.char_start IS NOT NULL
     AND NEW.char_end IS NOT NULL)
    OR (NEW.verdict = 'MISS' AND NEW.grade IS NOT NULL AND NEW.matched_variant IS NULL
        AND NEW.char_start IS NULL AND NEW.char_end IS NULL)
)
BEGIN
    SELECT RAISE(ABORT, 'l1 verdicts are PASS with a matched span or MISS without one');
END;
CREATE VIEW IF NOT EXISTS v_l1_latest AS
SELECT c.* FROM checks c
WHERE c.layer = 'l1'
  AND c.check_id = (SELECT max(c2.check_id) FROM checks c2
                    WHERE c2.layer = 'l1' AND c2.row_id = c.row_id);
CREATE VIEW IF NOT EXISTS v_l1_passed AS
SELECT cl.*, l.grade AS l1_grade, l.matched_variant, l.char_start, l.char_end,
       l.run_id AS l1_run_id
FROM claims cl JOIN v_l1_latest l ON l.row_id = cl.row_id
WHERE cl.status = 'row' AND l.verdict = 'PASS';
CREATE TRIGGER IF NOT EXISTS checks_judge_closed
BEFORE INSERT ON checks
WHEN NEW.layer IN ('align', 'faith') AND NOT (
    NEW.verdict IN ('supports', 'refutes', 'insufficient', 'unknown', 'needs-judge')
    AND NEW.tier IN ('tier0', 'tier1', 'tier2')
    AND (NEW.layer != 'align' OR NEW.query_id IS NOT NULL)
    AND (NEW.tier != 'tier0' OR NEW.verdict IN ('insufficient', 'needs-judge'))
    AND (NEW.verdict != 'needs-judge' OR NEW.tier = 'tier0')
    AND (NEW.verdict NOT IN ('supports', 'refutes')
         OR (NEW.evidence_span IS NOT NULL AND length(trim(NEW.evidence_span)) > 0
             AND NEW.matched_variant IS NOT NULL AND NEW.char_start IS NOT NULL
             AND NEW.char_end > NEW.char_start))
)
BEGIN
    SELECT RAISE(ABORT, 'judge verdicts are closed: supports/refutes need a resolved span; tier0 only routes');
END;
CREATE TRIGGER IF NOT EXISTS checks_l2_closed
BEFORE INSERT ON checks
WHEN NEW.layer = 'l2' AND NOT (
    (NEW.verdict = 'pass' AND NEW.reason_code IS NULL)
    OR (NEW.verdict = 'quarantine' AND NEW.reason_code IS NOT NULL)
)
BEGIN
    SELECT RAISE(ABORT, 'l2 verdicts are pass without a reason or quarantine with one');
END;
CREATE TRIGGER IF NOT EXISTS checks_l6_closed
BEFORE INSERT ON checks
WHEN NEW.layer = 'l6' AND NOT (
    (NEW.verdict = 'pass' AND NEW.reason_code IS NULL)
    OR (NEW.verdict = 'flag' AND NEW.reason_code IS NOT NULL)
)
BEGIN
    SELECT RAISE(ABORT, 'l6 verdicts are pass without a reason or flag with one');
END;
CREATE TRIGGER IF NOT EXISTS checks_recall_closed
BEFORE INSERT ON checks
WHEN NEW.layer = 'recall' AND NEW.verdict NOT IN ('present', 'absent')
BEGIN
    SELECT RAISE(ABORT, 'recall verdicts are present or absent');
END;
CREATE VIEW IF NOT EXISTS v_alignment AS
SELECT c.* FROM checks c
WHERE c.layer = 'align'
  AND c.check_id = (SELECT c2.check_id FROM checks c2
                    WHERE c2.layer = 'align' AND c2.row_id = c.row_id
                      AND c2.query_id = c.query_id
                    ORDER BY c2.tier DESC, c2.check_id DESC LIMIT 1);
CREATE VIEW IF NOT EXISTS v_judgments AS
SELECT a.row_id, a.query_id, a.tier, a.verifier_id, a.protocol_ver, a.run_id,
       a.verdict AS alignment, a.evidence_span AS alignment_span,
       f.verdict AS faithfulness, f.evidence_span AS faithfulness_span
FROM checks a
LEFT JOIN checks f ON f.layer = 'faith' AND f.run_id = a.run_id AND f.row_id = a.row_id
WHERE a.layer = 'align' AND a.tier != 'tier0';
CREATE TRIGGER IF NOT EXISTS gold_update_only_via_audit
BEFORE UPDATE ON gold
WHEN NOT (
    NEW.revision = OLD.revision + 1
    AND NEW.audit_id IS NOT NULL
    AND NEW.audit_id IS NOT OLD.audit_id
    AND NEW.gold_id = OLD.gold_id
    AND EXISTS (SELECT 1 FROM audits a
                WHERE a.audit_id = NEW.audit_id AND a.gold_id = OLD.gold_id
                  AND a.decision = 'revise' AND a.new_text = NEW.text)
    AND NOT EXISTS (SELECT 1 FROM gold g WHERE g.audit_id = NEW.audit_id)
)
BEGIN
    SELECT RAISE(ABORT, 'gold rows change only through an audit record (revise)');
END;
CREATE TRIGGER IF NOT EXISTS gold_no_delete
BEFORE DELETE ON gold
BEGIN
    SELECT RAISE(ABORT, 'gold rows are never deleted; record an audit instead');
END;
CREATE TRIGGER IF NOT EXISTS audits_append_only_update
BEFORE UPDATE ON audits
BEGIN
    SELECT RAISE(ABORT, 'audits are append-only');
END;
CREATE TRIGGER IF NOT EXISTS audits_append_only_delete
BEFORE DELETE ON audits
BEGIN
    SELECT RAISE(ABORT, 'audits are append-only');
END;
"""


class LedgerError(RuntimeError):
    pass


def now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def connect(path: pathlib.Path | str) -> sqlite3.Connection:
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, isolation_level=None)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# Columns added after the first ledgers were built; init() adds them where missing.
ADDED_COLUMNS = {"checks": (("query_id", "TEXT"), ("tier", "TEXT"))}


def init(path: pathlib.Path | str) -> sqlite3.Connection:
    conn = connect(path)
    for table, columns in ADDED_COLUMNS.items():
        present = {r[1] for r in conn.execute(f"pragma table_info({table})")}
        if present:
            for name, kind in columns:
                if name not in present:
                    conn.execute(f"alter table {table} add column {name} {kind}")
    conn.executescript(DDL)
    return conn


def query_readonly(path: pathlib.Path | str, statement: str) -> list[tuple]:
    """Run one statement on a read-only connection (a stand-in for the sqlite3 shell)."""
    path = pathlib.Path(path)
    if not path.is_file():
        raise LedgerError(f"no ledger at {path}")
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return conn.execute(statement).fetchall()
    except sqlite3.Error as exc:
        raise LedgerError(str(exc)) from exc
    finally:
        conn.close()


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def register_paper(conn: sqlite3.Connection, root: pathlib.Path, paper_id: str,
                   title: str | None = None) -> dict:
    """Register a paper and the paragraph blocks of every available text variant.

    A paper registered earlier must still have identical texts: a changed text
    invalidates every existence check made against it, so the import stops.
    """
    variants: dict[str, str] = {}
    texts: dict[str, str] = {}
    for name, path in common.variant_paths(root, paper_id).items():
        if path is None:
            variants[name] = "unavailable"
        else:
            texts[name] = path.read_text(errors="replace")
            variants[name] = _sha(texts[name])
    pdf = common.pdf_path(root, paper_id)
    row = conn.execute("select variants_json from papers where paper_id=?", (paper_id,)).fetchone()
    if row is not None:
        old = json.loads(row[0])
        changed = sorted(k for k in set(old) | set(variants) if old.get(k) != variants.get(k))
        if changed:
            raise LedgerError(f"{paper_id}: text changed for {', '.join(changed)} since registration")
        return variants
    with conn:
        conn.execute("BEGIN")
        conn.execute(
            "insert into papers(paper_id, title, pdf_path, pdf_sha256, variants_json, registered_at)"
            " values (?,?,?,?,?,?)",
            (paper_id, title, str(pdf), sha256_file(pdf) if pdf.is_file() else None,
             json.dumps(variants, sort_keys=True), now()))
        for name, text in texts.items():
            for b in pg.split_blocks(text, name):
                conn.execute(
                    "insert into paragraphs(paper_id, variant, para_id, seq, text, sha256, word_count)"
                    " values (?,?,?,?,?,?,?)",
                    (paper_id, name, b.para_id, b.seq, b.text, _sha(b.text), b.word_count))
    return variants


def imported_units(conn: sqlite3.Connection, paper_id: str | None = None) -> list[dict]:
    """Distinct paragraph units the imported extraction runs were converted under."""
    units: list[dict] = []
    for (meta,) in conn.execute("select meta_json from runs where run_kind='convert'"):
        meta = json.loads(meta)
        if paper_id is not None and meta.get("paper_id") != paper_id:
            continue
        if meta.get("paragraph_unit") not in units:
            units.append(meta.get("paragraph_unit"))
    return units


def _check_unit(conn: sqlite3.Connection, payload: dict) -> None:
    """Every row of a paper is located in one paragraph unit, the registered one once sealed."""
    from . import thresholds

    unit = payload.get("paragraph_unit")
    if unit is None:
        raise LedgerError("converter output has no paragraph unit: convert it again")
    if conn.execute("select 1 from runs where run_kind='thresholds-register' limit 1").fetchone():
        guard = thresholds.begin(conn)
        if guard.data["paragraph_unit"] != unit:
            raise LedgerError(f"paragraph unit {unit} differs from the registered"
                              f" {guard.data['paragraph_unit']}")
    for other in imported_units(conn, payload["paper_id"]):
        if other != unit:
            raise LedgerError(f"{payload['paper_id']}: paragraph unit {unit} differs from the"
                              f" unit already imported ({other})")


def _register_fragments(conn: sqlite3.Connection, paper_id: str, fragments: list[dict]) -> None:
    for f in fragments:
        sha = _sha(f["text"])
        old = conn.execute("select sha256 from paragraphs where paper_id=? and variant='codex_fragment'"
                           " and para_id=?", (paper_id, f["fragment_id"])).fetchone()
        if old is not None:
            if old[0] != sha:
                raise LedgerError(f"{paper_id}: fragment {f['fragment_id']} has two different texts")
            continue
        conn.execute(
            "insert into paragraphs(paper_id, variant, para_id, seq, text, sha256, word_count,"
            " page, bbox_json) values (?,?,?,?,?,?,?,?,?)",
            (paper_id, "codex_fragment", f["fragment_id"], None, f["text"], sha,
             len(f["text"].split()), f.get("page"), json.dumps(f.get("bbox"))))


def import_converted(conn: sqlite3.Connection, payload: dict, root: pathlib.Path) -> dict:
    """Load one converter payload: paper texts, the extraction run, rows and quarantine."""
    paper_id = payload["paper_id"]
    _check_unit(conn, payload)
    register_paper(conn, root, paper_id, payload.get("title"))
    run_id = payload["run_id"]
    counts = {"rows": 0, "quarantined": 0, "skipped": 0}
    with conn:
        conn.execute("BEGIN")
        conn.execute(
            "insert or ignore into runs(run_id, run_kind, extractor_id, input_sha256, meta_json,"
            " created_at) values (?,?,?,?,?,?)",
            (run_id, "convert", payload["extractor_id"], payload["source_sha256"],
             json.dumps({"source_file": payload["source_file"],
                         "source_records": payload["source_records"],
                         "paper_id": paper_id,
                         "paragraph_unit": payload["paragraph_unit"]}), now()))
        _register_fragments(conn, paper_id, payload.get("fragments", []))
        for row in payload["rows"]:
            counts[_insert_claim(conn, row, "row", run_id)] += 1
        for q in payload["quarantined"]:
            counts[_insert_claim(conn, q, "quarantined", run_id, payload)] += 1
    return counts


def _insert_claim(conn, item: dict, status: str, run_id: str, payload: dict | None = None) -> str:
    if status == "row":
        row_id = item["row_id"]
    else:
        row_id = f"{payload['extractor_id']}:{item['record_id']}"
    old = conn.execute("select run_id from claims where row_id=?", (row_id,)).fetchone()
    if old is not None:
        if old[0] != run_id:
            raise LedgerError(f"{row_id} already imported from run {old[0]}")
        return "skipped"
    if status == "row":
        loc = item["locator"]
        conn.execute(
            "insert into claims(row_id, record_id, paper_id, extractor_id, run_id, status, quote,"
            " section, page, para_id, para_ids_json, claim_text, conditions_json, conditions_raw,"
            " numbers_json, kind, source_kind, l1_tautological, record_json, imported_at)"
            " values (?,?,?,?,?,'row',?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (row_id, item["record_id"], item["paper_id"], item["extractor_id"], run_id,
             item["quote"], loc.get("section"), loc.get("page"), loc.get("para_id"),
             json.dumps(item.get("resolved_para_ids", [])), item["claim_text"],
             json.dumps(item["conditions"], ensure_ascii=False), item.get("conditions_raw"),
             json.dumps(item["numbers"], ensure_ascii=False), item["kind"],
             item.get("source_kind"), item.get("l1_tautological", 0),
             json.dumps(item, ensure_ascii=False), now()))
        return "rows"
    conn.execute(
        "insert into claims(row_id, record_id, paper_id, extractor_id, run_id, status,"
        " reason_code, record_json, imported_at) values (?,?,?,?,?,'quarantined',?,?,?)",
        (row_id, item["record_id"], payload["paper_id"], payload["extractor_id"], run_id,
         item["reason_code"], json.dumps(item, ensure_ascii=False), now()))
    return "quarantined"


def paragraph_unit(conn: sqlite3.Connection) -> dict:
    """The registered paragraph unit once thresholds are sealed, else the configured one."""
    from . import thresholds

    if thresholds.registered_path(conn) is not None:
        return thresholds.begin(conn).data["paragraph_unit"]
    return common.paragraph_unit()


def frame_blocks(conn: sqlite3.Connection, paper_id: str, unit: dict | None = None) -> list[dict]:
    """Blocks of the paragraph unit that are large enough to be sampled."""
    unit = unit or paragraph_unit(conn)
    cur = conn.execute(
        "select para_id, seq, word_count from paragraphs where paper_id=? and variant=?"
        " and word_count >= ? order by seq", (paper_id, unit["variant"], unit["min_words"]))
    return [{"para_id": p, "seq": s, "word_count": w} for p, s, w in cur]


def used_para_ids(conn: sqlite3.Connection, paper_id: str) -> set[str]:
    used: set[str] = set()
    for (ids,) in conn.execute("select para_ids_json from claims where paper_id=? and status='row'",
                               (paper_id,)):
        used.update(json.loads(ids or "[]"))
    return used


def unused_pool(conn: sqlite3.Connection, paper_id: str, unit: dict | None = None) -> list[dict]:
    """The elusion frame: framed blocks that no delivered row's quote resolves into."""
    used = used_para_ids(conn, paper_id)
    return [b for b in frame_blocks(conn, paper_id, unit) if b["para_id"] not in used]


def unit_blocks(conn: sqlite3.Connection, paper_id: str) -> list[pg.Block]:
    """Every block of the paragraph unit's variant, in order (the locator's haystack)."""
    variant = paragraph_unit(conn)["variant"]
    return [pg.Block(variant, seq, text) for seq, text in conn.execute(
        "select seq, text from paragraphs where paper_id=? and variant=? order by seq",
        (paper_id, variant))]


def block_texts(conn: sqlite3.Connection, paper_id: str, variant: str) -> dict[str, str]:
    return dict(conn.execute("select para_id, text from paragraphs where paper_id=? and variant=?",
                             (paper_id, variant)).fetchall())


def extraction_runs(conn: sqlite3.Connection, paper_id: str) -> list[str]:
    """Run ids of the record sets imported for a paper: the delivered set a sample is drawn for."""
    return [r for (r,) in conn.execute("select distinct run_id from claims where paper_id=?"
                                       " order by run_id", (paper_id,))]


def delivered(conn: sqlite3.Connection, paper_id: str) -> dict[str, dict]:
    """Per extractor: rows delivered, source records, and quarantined records by reason."""
    out: dict[str, dict] = {}
    for ext, status, reason, rows, records in conn.execute(
            "select extractor_id, status, reason_code, count(*), count(distinct record_id)"
            " from claims where paper_id=? group by extractor_id, status, reason_code"
            " order by extractor_id", (paper_id,)):
        d = out.setdefault(ext, {"rows": 0, "row_records": 0, "quarantined": {}})
        if status == "row":
            d["rows"] += rows
            d["row_records"] += records
        else:
            d["quarantined"][reason] = records
    return out


def l1_passed(conn: sqlite3.Connection, paper_id: str) -> list[sqlite3.Row]:
    """Rows whose latest existence check is PASS: the only input of every later layer."""
    old = conn.row_factory
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute("select * from v_l1_passed where paper_id=? order by row_id",
                            (paper_id,)).fetchall()
    finally:
        conn.row_factory = old
