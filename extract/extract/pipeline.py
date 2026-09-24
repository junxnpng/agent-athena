"""Read-only P2 composition; no ledger, model calls, or record generation."""
from __future__ import annotations

from typing import Optional

from .gates import assert_paragraph_unit_split
from .pagesection import locate_blocks
from .removal import classify_blocks, partition
from .segmenter import load_config, split_block_to_segments


def segment_text(text: str, arxiv_stamp: Optional[str] = None) -> dict:
    assert_paragraph_unit_split()
    cfg = load_config()
    blocks, headings = locate_blocks(text)
    segments = [segment for block in blocks for segment in split_block_to_segments(block, cfg)]
    reasons, warnings = classify_blocks(blocks, arxiv_stamp)
    result = partition(segments, reasons)
    result.update(blocks=blocks, headings=headings, segments=segments,
                  segmenter_ver=cfg['segmenter_ver'], boundary_warnings=warnings,
                  removed_reference_words=sum(len(item['segment'].text.split())
                                              for item in result['removed']
                                              if item['reason'] == 'references'))
    return result


def prepare_segments(text: str, arxiv_stamp: Optional[str] = None) -> dict:
    """Add P3 display segments; retain P2 originals for lossless accounting."""
    from .existence import check_against_raw
    from .spanning import join_spanning

    result = segment_text(text, arxiv_stamp)
    displayed, counts = join_spanning(result['blocks'], result['kept'],
                                     {heading.para_id for heading in result['headings']})
    checks = [check_against_raw(segment.text, text) for segment in displayed]
    result.update(displayed=displayed, spanning=counts, l1=checks)
    return result
