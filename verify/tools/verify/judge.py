"""Alignment judging: a lexical sweep, then a sealed file round trip with the judge.

`sweep` routes every L1-passed row with the tier0 lexical backend. `export` writes
the rows the sweep sent on as one JSON file whose sha256 is sealed in the ledger.
The judge (an agent following skills/claim-judge) writes one JSONL line per item.
`import_verdicts` accepts that file only when the export is unchanged, the lines
match the items one to one, every verdict is in the closed set, and every
evidence span resolves in the context and in the variant text it came from.
"""
from __future__ import annotations

import collections
import dataclasses
import datetime as _dt
import hashlib
import json
import pathlib
import re
import sqlite3

from . import l1_exists, ledger, queries, thresholds, usage
from .backends import lexical
from .paths import RESULTS_DIR, ROOT

SKILL_PATH = ROOT / "skills" / "claim-judge" / "SKILL.md"
VERDICTS = ("supports", "refutes", "insufficient", "unknown")
SPAN_REQUIRED = ("supports", "refutes")
PARTS = (("alignment", "align"), ("faithfulness", "faith"))
TIERS = {"mid": "tier1", "expensive": "tier2"}
CONTEXTS = ("quote", "para", "para1")
AGENTS = ("codex", "claude", "manual")
_BLANK = re.compile(r"\n\s*\n")
_PDF = re.compile(r"\.pdf\b", re.IGNORECASE)


class JudgeError(RuntimeError):
    pass


class ImportRefused(JudgeError):
    pass


def skill_protocol(path: pathlib.Path = SKILL_PATH) -> str:
    """The protocol version the judge skill declares in its front matter."""
    head = pathlib.Path(path).read_text(encoding="utf-8").split("---")[1]
    for line in head.splitlines():
        if line.startswith("protocol_ver:"):
            return line.split(":", 1)[1].strip()
    raise JudgeError(f"{path}: no protocol_ver in the front matter")


def default_query(conn: sqlite3.Connection) -> str:
    ids = [q for (q,) in conn.execute("select query_id from queries order by query_id")]
    if len(ids) != 1:
        raise JudgeError(f"{len(ids)} queries registered ({', '.join(ids) or 'none'}); pass --query")
    return ids[0]


def default_paper(conn: sqlite3.Connection) -> str:
    ids = [p for (p,) in conn.execute("select paper_id from papers order by paper_id")]
    if len(ids) != 1:
        raise JudgeError(f"{len(ids)} papers in the ledger; pass --paper")
    return ids[0]


def _query(conn: sqlite3.Connection, query_id: str) -> dict:
    query = queries.get(conn, query_id)
    if query is None:
        raise JudgeError(f"unknown query {query_id}: register it with `verify query register`")
    queries.require_confirmed(query)
    return query


def _seq(conn: sqlite3.Connection, kind: str) -> int:
    return conn.execute("select count(*) from runs where run_kind=?", (kind,)).fetchone()[0] + 1


# --- tier0 sweep ----------------------------------------------------------

@dataclasses.dataclass
class SweepSummary:
    run_id: str
    paper_id: str
    query_id: str
    rows: int
    routes: dict
    escalation_rate: float
    expensive_calls: int
    expensive_ratio: float
    tier2_invoked: bool


def sweep(conn: sqlite3.Connection, paper_id: str, query_id: str,
          backend: lexical.LexicalBackend | None = None) -> SweepSummary:
    guard = thresholds.begin(conn)
    query = _query(conn, query_id)
    backend = backend or lexical.LexicalBackend()
    rows = ledger.l1_passed(conn, paper_id)
    if not rows:
        raise JudgeError(f"{paper_id}: no L1-passed rows; run `verify l1` first")
    run_id = f"sweep-{paper_id}-{query_id}-{_seq(conn, 'judge-sweep'):03d}"
    routes: collections.Counter = collections.Counter()
    checks = []
    for r in rows:
        route = backend.route(r["quote"], query)
        routes[route.verdict] += 1
        checks.append((r["row_id"], backend.verifier_id, str(guard.data["protocol_ver"]), run_id,
                       route.verdict, r["l1_tautological"], json.dumps(route.features), query_id))
    guard.check()
    with conn:
        conn.execute("BEGIN")
        conn.execute(
            "insert into runs(run_id, run_kind, thresholds_sha256, protocol_ver, meta_json,"
            " created_at) values (?,?,?,?,?,?)",
            (run_id, "judge-sweep", guard.sha, backend.version,
             json.dumps({"paper_id": paper_id, "query_id": query_id,
                         "verifier_id": backend.verifier_id, "rows": len(rows)}), ledger.now()))
        conn.executemany(
            "insert into checks(row_id, layer, verifier_id, protocol_ver, run_id, verdict,"
            " l1_tautological, detail_json, query_id, tier)"
            " values (?, 'align', ?, ?, ?, ?, ?, ?, ?, 'tier0')", checks)
    expensive = conn.execute(
        "select count(*) from checks c join claims cl using(row_id) where c.layer='align'"
        " and c.tier='tier2' and c.query_id=? and cl.paper_id=?", (query_id, paper_id)).fetchone()[0]
    return SweepSummary(run_id, paper_id, query_id, len(rows), dict(routes),
                        routes["needs-judge"] / len(rows), expensive, expensive / len(rows),
                        expensive > 0)


def format_sweep(s: SweepSummary) -> str:
    ratio = (f"{s.expensive_ratio:.3f} ({s.expensive_calls}/{s.rows})" if s.tier2_invoked
             else "0 (tier2 not invoked)")
    return "\n".join([
        f"judge sweep {s.paper_id} x {s.query_id} run {s.run_id}",
        f"backend: {lexical.VERIFIER_ID} (routes only: {', '.join(lexical.ROUTES)})",
        f"rows (L1 passed): {s.rows}",
        "routes: " + ", ".join(f"{k} {s.routes.get(k, 0)}" for k in lexical.ROUTES),
        f"escalation_rate: {s.escalation_rate:.3f} (observed, {s.routes.get('needs-judge', 0)}/{s.rows})",
        f"expensive_ratio: {ratio}",
    ])


# --- export ---------------------------------------------------------------

@dataclasses.dataclass
class Export:
    export_id: str
    path: pathlib.Path
    sha256: str
    payload: dict


def _block_bounds(text: str) -> list[tuple[int, int]]:
    """[start, end) of every blank-line block of a text."""
    bounds, start = [], 0
    for m in _BLANK.finditer(text):
        if m.start() > start:
            bounds.append((start, m.start()))
        start = m.end()
    if start < len(text):
        bounds.append((start, len(text)))
    return bounds


def context_span(text: str, start: int, end: int, width: str) -> tuple[int, int]:
    """The context around a quote span: the quote itself, its blocks, or one more each side."""
    if width == "quote":
        return start, end
    bounds = _block_bounds(text)
    first = next((i for i, (s, e) in enumerate(bounds) if e > start), 0)
    last = next((i for i in range(len(bounds) - 1, -1, -1) if bounds[i][0] < end), len(bounds) - 1)
    if width == "para1":
        first, last = max(first - 1, 0), min(last + 1, len(bounds) - 1)
    return min(bounds[first][0], start), max(bounds[last][1], end)


def _order_key(seed: int, row_id: str) -> str:
    return hashlib.sha256(f"{seed}:{row_id}".encode()).hexdigest()


def _walk_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _walk_strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _walk_strings(v)


def export(conn: sqlite3.Connection, root: pathlib.Path, paper_id: str, query_id: str,
           tier: str = "mid", context: str = "para", swap_order: bool = False, limit: int = 20,
           out_dir: pathlib.Path | None = None, agent: str = "manual") -> Export:
    if agent not in AGENTS:
        raise JudgeError(f"unknown agent {agent}")
    if tier not in TIERS:
        raise JudgeError(f"unknown tier {tier} (known: {', '.join(TIERS)})")
    if context not in CONTEXTS:
        raise JudgeError(f"unknown context width {context} (known: {', '.join(CONTEXTS)})")
    guard = thresholds.begin(conn)
    query = _query(conn, query_id)
    routed = {r: v for r, v in conn.execute(
        "select row_id, verdict from v_alignment where query_id=? and tier='tier0'", (query_id,))}
    rows = [r for r in ledger.l1_passed(conn, paper_id) if r["row_id"] in routed]
    if not rows:
        raise JudgeError(f"{paper_id} x {query_id}: no tier0 routes; run `verify judge sweep` first")
    seed = int(guard.data["sample_seed"])
    chosen = sorted((r for r in rows if routed[r["row_id"]] == "needs-judge"),
                    key=lambda r: _order_key(seed, r["row_id"]))[:limit]
    variants = {v.name: v.text for v in l1_exists.load_variants(conn, root, paper_id)[0]}
    items = []
    for n, r in enumerate(chosen, start=1):
        text = variants[r["matched_variant"]]
        c0, c1 = context_span(text, r["char_start"], r["char_end"], context)
        presentation = ["evidence", "query"] if swap_order and n % 2 == 0 else ["query", "evidence"]
        items.append({
            "item": n, "row_id": r["row_id"], "paper_id": paper_id, "record_id": r["record_id"],
            "extractor_id": r["extractor_id"], "kind": r["kind"], "l1_grade": r["l1_grade"],
            "quote": r["quote"], "record_claim_text": r["claim_text"],
            "query": {"query_id": query["query_id"], "topic": query["topic"],
                      "claim_text": query["claim_text"]},
            "context": {"width": context, "variant": r["matched_variant"], "char_start": c0,
                        "char_end": c1, "text": text[c0:c1]},
            "quote_span": {"start": r["char_start"] - c0, "end": r["char_end"] - c0},
            "presentation": presentation,
        })
    export_id = f"judge-{paper_id}-{query_id}-{_seq(conn, 'judge-export'):03d}"
    payload = {
        "export_id": export_id, "paper_id": paper_id, "tier": TIERS[tier], "tier_name": tier,
        "agent": agent,
        "context_width": context, "swap_order": swap_order, "judge_protocol": skill_protocol(),
        "thresholds_protocol": str(guard.data["protocol_ver"]), "thresholds_sha256": guard.sha,
        "sample_seed": seed, "query": {k: query[k] for k in ("query_id", "topic", "claim_text")},
        "instructions": "Follow skills/claim-judge/SKILL.md; write one JSON line per item.",
        "items": items,
    }
    bad = [s for s in _walk_strings(payload) if _PDF.search(s)]
    if bad:
        raise JudgeError(f"export would carry a PDF path ({bad[0][:80]}); the judge never sees PDFs")
    out_dir = pathlib.Path(out_dir or RESULTS_DIR / "judge")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{export_id}.json"
    data = (json.dumps(payload, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
    path.write_bytes(data)
    sha = hashlib.sha256(data).hexdigest()
    (out_dir / f"{export_id}.manifest.sha256").write_text(f"{sha}  {path.name}\n")
    conn.execute(
        "insert into runs(run_id, run_kind, input_sha256, thresholds_sha256, protocol_ver,"
        " meta_json, created_at) values (?,?,?,?,?,?,?)",
        (export_id, "judge-export", sha, guard.sha, payload["judge_protocol"],
         json.dumps({"paper_id": paper_id, "query_id": query_id, "tier": TIERS[tier],
                     "context": context, "items": len(items), "path": str(path),
                     "row_ids": [i["row_id"] for i in items],
                     "usage_start": usage.snapshot_for(agent)}), ledger.now()))
    return Export(export_id, path, sha, payload)


# --- import ---------------------------------------------------------------

@dataclasses.dataclass
class ImportResult:
    run_id: str
    export_id: str
    rows: int
    verdicts: dict
    usage: dict


def _read_lines(path: pathlib.Path) -> list[dict]:
    lines = []
    for n, raw in enumerate(pathlib.Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            line = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ImportRefused(f"{path} line {n}: not JSON ({exc.msg})") from exc
        if not isinstance(line, dict):
            raise ImportRefused(f"{path} line {n}: not a JSON object")
        lines.append(line)
    return lines


def _check_span(item: dict, part: str, judgment: dict, variant_text: str) -> tuple | None:
    """(text, absolute start, absolute end) of a resolved span, or None when there is none."""
    n, verdict = item["item"], judgment["verdict"]
    span = judgment.get("evidence_span")
    if not span or not str(span.get("text") or "").strip():
        if verdict in SPAN_REQUIRED:
            raise ImportRefused(f"item {n}: {part} {verdict} without an evidence span")
        return None
    ctx = item["context"]["text"]
    try:
        start, end = int(span["start"]), int(span["end"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ImportRefused(f"item {n}: {part} evidence span needs integer start and end") from exc
    if not (0 <= start < end <= len(ctx)) or ctx[start:end] != span["text"]:
        raise ImportRefused(f"item {n}: {part} evidence span does not resolve in the context")
    a0 = item["context"]["char_start"] + start
    if variant_text[a0:a0 + (end - start)] != span["text"]:
        raise ImportRefused(f"item {n}: {part} evidence span does not resolve in"
                            f" {item['context']['variant']}")
    return span["text"], a0, a0 + (end - start)


def import_verdicts(conn: sqlite3.Connection, root: pathlib.Path, export_path: pathlib.Path,
                    verdicts_path: pathlib.Path, verifier_id: str, protocol_ver: str,
                    manifest: str, tokens_in: int | None = None, tokens_out: int | None = None,
                    wallclock_s: float | None = None) -> ImportResult:
    data = pathlib.Path(export_path).read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if sha != manifest:
        raise ImportRefused(f"manifest {manifest[:12]} does not match the export file ({sha[:12]})")
    payload = json.loads(data)
    export_id = payload["export_id"]
    run = conn.execute("select input_sha256, created_at, meta_json from runs where run_id=?"
                       " and run_kind='judge-export'", (export_id,)).fetchone()
    if run is None:
        raise ImportRefused(f"{export_id}: no such export in the ledger")
    if run[0] != sha:
        raise ImportRefused(f"{export_id}: the export file does not match the manifest sealed at"
                            f" export ({run[0][:12]})")
    if protocol_ver != payload["judge_protocol"]:
        raise ImportRefused(f"protocol {protocol_ver} differs from the export's"
                            f" {payload['judge_protocol']}")
    if not verifier_id.strip():
        raise ImportRefused("a verifier id is required")
    vsha = hashlib.sha256(pathlib.Path(verdicts_path).read_bytes()).hexdigest()
    for (meta,) in conn.execute("select meta_json from runs where run_kind='judge-import'"):
        meta = json.loads(meta)
        if meta["export_id"] == export_id and meta["verdicts_sha256"] == vsha:
            raise ImportRefused(f"{verdicts_path} already imported for {export_id}")

    items = {i["item"]: i for i in payload["items"]}
    lines = _read_lines(verdicts_path)
    if len(lines) != len(items):
        raise ImportRefused(f"rows: the export has {len(items)} items, the verdicts {len(lines)} lines")
    variants = {v.name: v.text for v in
                l1_exists.load_variants(conn, root, payload["paper_id"])[0]}
    seen: set = set()
    rows = []
    counts = {name: dict.fromkeys(VERDICTS, 0) for name, _ in PARTS}
    for line in lines:
        item = items.get(line.get("item"))
        if item is None or line["item"] in seen:
            raise ImportRefused(f"rows: item {line.get('item')} is not a distinct export item")
        seen.add(line["item"])
        if line.get("row_id") != item["row_id"]:
            raise ImportRefused(f"item {item['item']}: row_id {line.get('row_id')} is not"
                                f" {item['row_id']}")
        for name, layer in PARTS:
            judgment = line.get(name)
            if not isinstance(judgment, dict) or judgment.get("verdict") not in VERDICTS:
                raise ImportRefused(f"item {item['item']}: {name} verdict missing or not one of"
                                    f" {', '.join(VERDICTS)}")
            span = _check_span(item, name, judgment, variants[item["context"]["variant"]])
            counts[name][judgment["verdict"]] += 1
            rows.append((item, layer, judgment, span))

    seq = conn.execute("select count(*) from runs where run_kind='judge-import' and run_id like ?",
                       (f"{export_id}-import-%",)).fetchone()[0] + 1
    run_id = f"{export_id}-import-{seq:02d}"
    if wallclock_s is None:
        started = _dt.datetime.strptime(run[1], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_dt.timezone.utc)
        wallclock_s = (_dt.datetime.now(_dt.timezone.utc) - started).total_seconds()
    tier = payload["tier"]
    query_id = payload["query"]["query_id"]
    start = json.loads(run[2]).get("usage_start") or {"window": None, "unavailable": "not recorded"}
    used = usage.delta(start, usage.snapshot_for(payload.get("agent", "manual")))
    with conn:
        conn.execute("BEGIN")
        conn.execute(
            "insert into runs(run_id, run_kind, input_sha256, thresholds_sha256, protocol_ver,"
            " meta_json, created_at) values (?,?,?,?,?,?,?)",
            (run_id, "judge-import", vsha, payload["thresholds_sha256"], protocol_ver,
             json.dumps({"export_id": export_id, "verifier_id": verifier_id,
                         "verdicts_path": str(verdicts_path), "verdicts_sha256": vsha,
                         "paper_id": payload["paper_id"], "query_id": query_id,
                         "usage": used}), ledger.now()))
        for item, layer, judgment, span in rows:
            text, a0, a1 = span if span else (None, None, None)
            conn.execute(
                "insert into checks(row_id, layer, verifier_id, protocol_ver, run_id, verdict,"
                " matched_variant, char_start, char_end, evidence_span, detail_json, query_id, tier)"
                " values (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (item["row_id"], layer, verifier_id, protocol_ver, run_id, judgment["verdict"],
                 item["context"]["variant"] if span else None, a0, a1, text,
                 json.dumps({"item": item["item"], "rationale": judgment.get("rationale"),
                             "presentation": item["presentation"],
                             "context_width": item["context"]["width"]}, ensure_ascii=False),
                 query_id, tier))
        conn.execute(
            "insert into budget(run_id, stage, tier, rows, tokens_in, tokens_out, wallclock_s,"
            " expensive_calls) values (?,?,?,?,?,?,?,?)",
            (run_id, "judge", tier, len(items), tokens_in, tokens_out, wallclock_s,
             len(items) if tier == "tier2" else 0))
    return ImportResult(run_id, export_id, len(items), counts, used)


def format_import(res: ImportResult) -> str:
    lines = [f"imported {res.rows} rows from {res.export_id} as {res.run_id}"]
    for name, _ in PARTS:
        lines.append(f"  {name}: " + ", ".join(f"{k} {v}" for k, v in res.verdicts[name].items()))
    lines.append(f"  {usage.format_delta(res.usage)}")
    return "\n".join(lines)
