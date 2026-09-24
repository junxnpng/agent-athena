"""Pair unfinished body fragments without consuming intervening source blocks."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
import re

from .pagesection import LocatedBlock
from .segmenter import Fragment, Segment

CAPTION = re.compile(r'^\s*(?:Table|Figure|Fig\.|Algorithm|Listing)\s+\d', re.I)
TERMINAL = re.compile(r'[.!?]["\u201d\u2019\')\]]*\s*$')


def _prose(text: str) -> bool:
    words = text.split()
    return bool(words) and sum(any(c.isalpha() for c in word) for word in words) > len(words) / 2


def _body(block: LocatedBlock, heading_ids: set[str]) -> bool:
    return (block.word_count >= 20 and block.para_id not in heading_ids
            and not CAPTION.match(block.text) and _prose(block.text))


def _with_fragment(segment: Segment) -> Segment:
    fragment = Fragment(segment.segment_id, segment.text, segment.para_id, segment.page,
                        segment.char_start, segment.char_end)
    return replace(segment, fragments=(fragment,))


def join_spanning(blocks: list[LocatedBlock], kept: list[Segment],
                  heading_ids: set[str]) -> tuple[list[Segment], dict]:
    by_block = defaultdict(list)
    originals = [_with_fragment(segment) for segment in kept]
    for segment in originals:
        by_block[segment.para_id].append(segment)
    consumed = set()
    replacements = {}
    candidates = 0
    for index, block in enumerate(blocks):
        source = by_block[block.para_id]
        if (not source or block.para_id in heading_ids or CAPTION.match(block.text) or not _prose(block.text)
                or not any(len(word) >= 4 and word[0].islower() for word in block.text.split())):
            continue
        tail = source[-1]
        if tail.segment_id in consumed or TERMINAL.search(tail.text):
            continue
        candidates += 1
        for following in blocks[index + 1:]:
            # A heading is a boundary even if its number repeats an earlier section.
            if following.para_id in heading_ids or following.section != block.section:
                break
            target = by_block[following.para_id]
            if not target or not _body(following, heading_ids):
                continue
            head = target[0]
            if head.segment_id in consumed:
                break
            replacements[tail.segment_id] = replace(
                tail, text=tail.text + ' […] ' + head.text,
                resolved_para_ids=(tail.para_id, head.para_id),
                fragments=tail.fragments + head.fragments)
            consumed.update((tail.segment_id, head.segment_id))
            break
    displayed = [replacements.get(segment.segment_id, segment) for segment in originals
                 if segment.segment_id not in consumed or segment.segment_id in replacements]
    return displayed, {'candidates': candidates, 'formed': len(replacements)}
