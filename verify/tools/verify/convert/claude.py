"""Claude record set -> evidence rows. One quote is one row."""
from __future__ import annotations

import pathlib

from .. import paragraphs as pg
from ..paths import sha256_file
from . import common


def convert(root: pathlib.Path, slug: str) -> common.ConvertResult:
    path, data, records = common.load_records(root, "claude", slug)
    sha = sha256_file(path)
    run_id = f"claude-{sha[:8]}-{slug}"
    kinds = common.KindMap.load()
    hay = pg.Haystack(common.unit_blocks(root, slug))

    rows: list[dict] = []
    quarantined: list[dict] = []
    for rec in records:
        rid = rec["id"]
        kind = kinds.map(rec.get("kind", ""))
        if not rec.get("quotes"):
            quarantined.append({"record_id": rid, "reason_code": "no_quote", "record": rec})
            continue
        if kind is None:
            quarantined.append({"record_id": rid, "reason_code": "kind_unmapped", "record": rec})
            continue
        if rec.get("page") is None and not rec.get("location"):
            quarantined.append({"record_id": rid, "reason_code": "locator_unresolved", "record": rec})
            continue
        for n, quote in enumerate(rec["quotes"], start=1):
            para_id, para_ids = common.resolve_locator(quote, hay)
            rows.append({
                "row_id": f"claude:{rid}.q{n}",
                "record_id": rid,
                "paper_id": slug,
                "quote": quote,
                "locator": common.locator(common.section_of(rec.get("location", "")),
                                          rec.get("page"), para_id,
                                          location_raw=rec.get("location", "")),
                "resolved_para_ids": para_ids,
                "claim_text": rec.get("meaning", ""),
                "conditions": {},
                "numbers": [{"raw": s} for s in rec.get("numbers", []) if str(s).strip()],
                "kind": kind,
                "source_kind": rec.get("kind", ""),
                "extractor_id": "claude",
                "run_id": run_id,
                "l1_tautological": 0,
            })
    return common.ConvertResult("claude", slug, run_id, str(path), sha, len(records),
                                rows, quarantined, title=records[0].get("paper_title"))
