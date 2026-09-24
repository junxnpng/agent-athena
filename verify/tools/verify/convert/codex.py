"""Codex record set -> evidence rows.

Codex records carry no quote field. Only a record with exactly one fragment gets
a quote (that fragment's text); the rest are quarantined, and all fragments are
kept as locator evidence. A fragment is PDF block text, so its existence check
passes by construction: rows are marked l1_tautological.
"""
from __future__ import annotations

import pathlib

from .. import paragraphs as pg
from ..paths import sha256_file
from . import common


def _numbers(text: str) -> list[dict]:
    return [{"raw": text.strip()}] if text and text.strip() else []


def convert(root: pathlib.Path, slug: str) -> common.ConvertResult:
    path, data, records = common.load_records(root, "codex", slug)
    sha = sha256_file(path)
    run_id = f"codex-{sha[:8]}-{slug}"
    kinds = common.KindMap.load()
    hay = pg.Haystack(common.unit_blocks(root, slug))

    rows: list[dict] = []
    quarantined: list[dict] = []
    fragments: list[dict] = []
    for rec in records:
        rid = rec["id"]
        frags = rec.get("fragments") or []
        for f in frags:
            fragments.append({"record_id": rid, "fragment_id": f["id"], "page": f.get("page"),
                              "bbox": f.get("bbox"), "text": f["text"], "sha256": f.get("sha256")})
        kind = kinds.map(rec.get("kind", ""))
        if len(frags) != 1:
            quarantined.append({"record_id": rid, "reason_code": "multi_fragment_no_quote",
                                "fragment_ids": [f["id"] for f in frags], "record": rec})
            continue
        if kind is None:
            quarantined.append({"record_id": rid, "reason_code": "kind_unmapped", "record": rec})
            continue
        frag = frags[0]
        if not (frag.get("text") or "").strip():
            quarantined.append({"record_id": rid, "reason_code": "no_quote", "record": rec})
            continue
        if frag.get("page") is None and not rec.get("location"):
            quarantined.append({"record_id": rid, "reason_code": "locator_unresolved", "record": rec})
            continue
        para_id, para_ids = common.resolve_locator(frag["text"], hay)
        rows.append({
            "row_id": f"codex:{rid}.q1",
            "record_id": rid,
            "paper_id": slug,
            "quote": frag["text"],
            "locator": common.locator(common.section_of(rec.get("location", "")),
                                      frag.get("page"), para_id,
                                      location_raw=rec.get("location", ""),
                                      fragment_id=frag["id"]),
            "resolved_para_ids": para_ids,
            "claim_text": rec.get("meaning", ""),
            "conditions": {},
            "conditions_raw": rec.get("conditions", ""),
            "numbers": _numbers(rec.get("numbers", "")),
            "kind": kind,
            "source_kind": rec.get("kind", ""),
            "extractor_id": "codex",
            "run_id": run_id,
            "l1_tautological": 1,
        })
    return common.ConvertResult("codex", slug, run_id, str(path), sha, len(records),
                                rows, quarantined, fragments, title=records[0].get("title"))
