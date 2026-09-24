"""Shared fixtures: a synthetic source tree shaped like the kvcpool-trace-gen inputs."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib


SLUG = "demo__paper"
GOLD_SLUG = "workload__year-in-llm-serving"

RAW_TEXT = """Title of a Demo Paper
Some Author

We analyze a one-year production trace from CompanyX, a serverless LLM inference platform that serves both platform-hosted and user-deployed models across many regions and tenants.

Requests span a wide range of token lengths. Figure 2 shows that input lengths are much longer than output lengths for every model family we study in the trace.

Prefix reuse is common: most requests share a long system prompt with an earlier request from the same user, which makes per-user caching effective in production.

This paragraph is never quoted by any extractor and talks about the load balancer, its hashing policy, and the number of replicas that the operator provisions each day.

Short line.
"""

LAYOUT_TEXT = RAW_TEXT.replace("\n\n", "\n")
CLAUDE_BODY = RAW_TEXT


def _claude_record(rid, quotes, kind="실제 관측", page=3, location="§3 · p.3 좌단"):
    return {
        "id": rid, "paper": SLUG, "page": page, "location": location,
        "section": "A. demo", "topic": "t", "quotes": quotes,
        "meaning": f"claim of {rid}", "why": "", "numbers": ["14.2:1 (our arithmetic)"],
        "caveats": [], "unreported": [], "kind": kind,
    }


def _codex_record(rid, texts, kind="실제 관측", location="§3.1; Fig.1(e)"):
    frags = [
        {"id": f"p03b{rid[-1]}{i:02d}", "page": 3, "bbox": [0, 0, 1, 1], "text": t,
         "sha256": hashlib.sha256(t.encode()).hexdigest()}
        for i, t in enumerate(texts)
    ]
    return {
        "id": rid, "blocks": " ".join(f["id"] for f in frags), "location": location,
        "kind": kind, "topic": "t", "meaning": f"claim of {rid}",
        "conditions": "free prose about scope", "numbers": "UTC; 24h",
        "paper": SLUG, "title": "Demo", "pdf": f"papers/{SLUG}.pdf", "fragments": frags,
    }


CLAUDE_RECORDS = [
    _claude_record("DM-A1", ["We analyze a one-year production trace from CompanyX, a serverless LLM inference platform that serves both platform-hosted and user-deployed models."]),
    _claude_record("DM-A2", []),
    _claude_record("DM-B1", [
        "Requests span a wide range of token lengths.",
        "Prefix reuse is common: most requests share a long system prompt with an earlier request from the same user",
    ], kind="실제 관측 + 저자의 해석"),
    _claude_record("DM-C1", ["Figure 2 shows that input lengths are much longer than output lengths"], kind="저자의 계산 (가정값 위의 산술)"),
    _claude_record("DM-Z9", ["Something"], kind="2차 인용"),
]

CODEX_RECORDS = [
    _codex_record("DM001", ["Prefix reuse is common: most requests share a long system prompt with an earlier\nrequest from the same user, which makes per-user caching effective in production.\n"]),
    _codex_record("DM002", ["Requests span a wide range of token lengths.", "Figure 2 shows that input lengths"], kind="시뮬레이션 / 합성 설정"),
]


def write_source(tmp_path: pathlib.Path) -> pathlib.Path:
    root = tmp_path / "src"
    cq = root / "docs/patterns/260911_claude_quotes_final"
    xq = root / "docs/patterns/260911_codex_quotes_final"
    (cq / "claude_source_text").mkdir(parents=True)
    xq.mkdir(parents=True)
    (root / "papers/codex_source_text").mkdir(parents=True)
    (cq / "claude_pattern_data.json").write_text(json.dumps(
        {"generated": "2026-09-15", "records": CLAUDE_RECORDS}, ensure_ascii=False))
    (xq / "codex_pattern_data.json").write_text(json.dumps(
        {"records": CODEX_RECORDS}, ensure_ascii=False))
    (root / f"papers/codex_source_text/codex_{SLUG}.txt").write_text(RAW_TEXT)
    (root / f"papers/codex_source_text/codex_{SLUG}_layout.txt").write_text(LAYOUT_TEXT)
    (cq / f"claude_source_text/claude_{SLUG}.txt").write_text(CLAUDE_BODY)
    (root / f"papers/{SLUG}.pdf").write_bytes(b"%PDF-demo")
    return root
