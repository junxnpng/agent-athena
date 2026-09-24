"""Verbatim-check waivers: free-form reasons mapped to reason codes, kept apart from verdicts.

A waiver records that a quote was confirmed by hand although the text matcher
failed on it. It lives in its own table and never changes an L1 verdict.
"""
from __future__ import annotations

import csv
import dataclasses
import json
import pathlib
import sqlite3


from .convert import common
from .paths import CONFIG_DIR

CODES_PATH = CONFIG_DIR / "waiver_reasons.json"


class WaiverError(RuntimeError):
    pass


@dataclasses.dataclass(frozen=True)
class Codes:
    codes: dict[str, list[str]]
    fallback: dict[str, list[str]]


def load_codes(path: pathlib.Path = CODES_PATH) -> Codes:
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    codes = {code: list(spec.get("patterns") or []) for code, spec in data["codes"].items()}
    fallback = {code: list(pats) for code, pats in (data.get("fallback") or {}).items()}
    unknown = [c for c in fallback if c not in codes]
    if unknown:
        raise WaiverError(f"{path}: fallback to undefined code {', '.join(unknown)}")
    return Codes(codes, fallback)


def _earliest(text: str, table: dict[str, list[str]]) -> str | None:
    best = None
    for code, patterns in table.items():
        for p in patterns:
            at = text.find(p)
            if at >= 0 and (best is None or at < best[0]):
                best = (at, code)
    return best[1] if best else None


def map_reason(text: str, codes: Codes) -> str:
    code = _earliest(text, codes.codes) or _earliest(text, codes.fallback)
    if code is None:
        raise WaiverError(f"no reason code for waiver reason: {text[:80]}")
    return code


def default_path(root: pathlib.Path) -> pathlib.Path:
    return root / common.sources()["waivers"]


def read_tsv(path: pathlib.Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh, delimiter="\t"))
    out = []
    for n, cells in enumerate(rows[1:], start=2):
        if not any(c.strip() for c in cells):
            continue
        cells += [""] * (5 - len(cells))
        slug, qid, frag, reason, method = (c.strip() for c in cells[:5])
        if not reason:
            raise WaiverError(f"{path}:{n}: waiver {slug} {qid} without a reason")
        out.append({"paper_id": slug, "row_ref": qid, "frag_sha1_12": frag or None,
                    "reason_text": reason, "verification_method": method or None})
    return out


def import_tsv(conn: sqlite3.Connection, path: pathlib.Path,
               codes: Codes | None = None) -> dict:
    """Insert every waiver with its reason code; a re-import must agree with the first."""
    codes = codes or load_codes()
    items = read_tsv(path)
    inserted = 0
    with conn:
        conn.execute("BEGIN")
        for w in items:
            code = map_reason(w["reason_text"], codes)
            old = conn.execute(
                "select reason_code, reason_text from waivers where paper_id=? and row_ref=?"
                " and frag_sha1_12 is ?", (w["paper_id"], w["row_ref"], w["frag_sha1_12"])).fetchone()
            if old is not None:
                if old != (code, w["reason_text"]):
                    raise WaiverError(f"{w['paper_id']} {w['row_ref']} already imported with"
                                      f" reason {old[0]}; a waiver is not rewritten")
                continue
            conn.execute(
                "insert into waivers(paper_id, row_ref, frag_sha1_12, reason_code, reason_text,"
                " verification_method, source_file) values (?,?,?,?,?,?,?)",
                (w["paper_id"], w["row_ref"], w["frag_sha1_12"], code, w["reason_text"],
                 w["verification_method"], str(path)))
            inserted += 1
    return {"read": len(items), "inserted": inserted}


def rates(conn: sqlite3.Connection, root: pathlib.Path) -> dict:
    """waiver_rate per ledger paper (Claude rows) and over the whole Claude record file.

    Waivers are per quote, so the overall rate is waived quotes over every Claude
    quote; the record-level pair (distinct waived records over records) is given
    beside it and never mixed into it.
    """
    papers = {}
    for (paper,) in conn.execute("select distinct paper_id from claims where extractor_id='claude'"
                                 " and status='row' order by paper_id"):
        rows = {r.split(":", 1)[1] for (r,) in conn.execute(
            "select row_id from claims where paper_id=? and extractor_id='claude' and status='row'",
            (paper,))}
        waived = {r for (r,) in conn.execute("select row_ref from waivers where paper_id=?", (paper,))}
        papers[paper] = (len(rows & waived), len(rows))
    path = common.records_path(root, "claude")
    records = json.loads(path.read_text(encoding="utf-8"))["records"]
    quotes = sum(len(r.get("quotes") or []) for r in records)
    refs = conn.execute("select paper_id, row_ref from waivers").fetchall()
    waived_records = {(p, ref.rsplit(".q", 1)[0]) for p, ref in refs}
    return {"papers": papers, "overall_rows": (len(refs), quotes),
            "overall_records": (len(waived_records), len(records))}


def format_rates(r: dict) -> list[str]:
    lines = [f"waiver_rate {p}: {a}/{b} rows" for p, (a, b) in r["papers"].items()]
    (a, b), (c, d) = r["overall_rows"], r["overall_records"]
    lines.append(f"waiver_rate overall: {a}/{b} rows ({c}/{d} records)")
    return lines
