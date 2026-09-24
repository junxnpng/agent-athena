"""Conservative whole-block removal; mixed content stays visible with warnings."""
from __future__ import annotations

from collections import defaultdict
import re
from typing import Optional

from .pagesection import LocatedBlock
from .segmenter import Segment


def classify_blocks(blocks: list[LocatedBlock], arxiv_stamp: Optional[str] = None) -> tuple[dict, list]:
    # Only identical short blocks in the first two block positions on >=2 pages
    # qualify as headers. This intentionally leaves uncertain material visible.
    starts = defaultdict(int)
    candidates = defaultdict(set)
    positions = {}
    for block in blocks:
        position = starts[block.page]
        starts[block.page] += 1
        positions[block.para_id] = position
        if position < 2 and block.word_count <= 30 and len(block.text.splitlines()) <= 2:
            candidates[block.text].add(block.page)
    headers = {text for text, pages in candidates.items() if len(pages) >= 2}
    reasons = {}
    warnings = []
    references = False
    for block in blocks:
        stripped = block.text.strip()
        references = references or bool(re.fullmatch(r"\s*References\s*", block.text.split('\n')[0], re.I))
        stamp = (stripped == arxiv_stamp.strip()) if arxiv_stamp else bool(
            re.fullmatch(r"arXiv:\d{4}\.\d{4,5}(?:v\d+)?(?:\s+\[[^\]\n]+\])?(?:\s+\d{1,2}\s+[A-Za-z]+\s+\d{4})?", stripped))
        if references:
            reasons[block.para_id] = 'references'
        elif stamp:
            reasons[block.para_id] = 'arxiv_stamp'
        elif block.text in headers and positions[block.para_id] < 2:
            reasons[block.para_id] = 'running_header'
        elif 'arXiv:' in block.text:
            warnings.append({'para_id': block.para_id, 'reason': 'embedded_arxiv_stamp'})
    return reasons, warnings


def partition(segments: list[Segment], reasons: dict) -> dict:
    kept, removed = [], []
    counts = dict.fromkeys(('references', 'running_header', 'arxiv_stamp'), 0)
    for segment in segments:
        reason = reasons.get(segment.para_id)
        if reason:
            removed.append({'segment': segment, 'reason': reason})
            counts[reason] += 1
        else:
            kept.append(segment)
    return {'kept': kept, 'removed': removed, 'removed_by_reason': counts}
