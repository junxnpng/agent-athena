"""Attach source offsets and conservative section headings to verify blocks."""
from __future__ import annotations

from dataclasses import dataclass, replace
import re
from typing import Optional

from tools.verify.paragraphs import Block, split_blocks

NUMBER = r"[1-9](?:\.[1-9]){0,2}"
LINE = re.compile(r"^(" + NUMBER + r")\s+([A-Z][A-Za-z][A-Za-z -]{2,60})$")
RUN_IN = re.compile(r"^([1-9](?:\.[1-9]){1,2})\s+([A-Z][A-Za-z][A-Za-z -]{2,60})\.\s")
TITLE = re.compile(r"^[A-Z][A-Za-z][A-Za-z -]{2,40}$")


@dataclass(frozen=True)
class LocatedBlock(Block):
    char_start: int
    char_end: int
    page: int
    section: Optional[str]


@dataclass(frozen=True)
class Heading:
    number: str
    title: str
    para_id: str
    char_start: int


def _title_case(title: str) -> bool:
    return all(len(word) < 4 or word[0].isupper() for word in title.split())


def locate_blocks(text: str) -> tuple[list[LocatedBlock], list[Heading]]:
    normalized = text.replace("\f", "\n")
    blocks = []
    cursor = 0
    for block in split_blocks(text, "extract_raw"):
        start = normalized.index(block.text, cursor)
        end = start + len(block.text)
        # verify normalizes form feeds. Never present a modified quote as raw text.
        if text[start:end] != block.text:
            raise ValueError("블록 내부 form feed: 원문 보존 문단 계약을 만족하지 않습니다")
        blocks.append(LocatedBlock(block.variant, block.seq, block.text, start, end,
                                   1 + text.count("\f", 0, start), None))
        cursor = end
    headings = []
    section = None
    located = []
    for i, block in enumerate(blocks):
        hits = []
        if re.fullmatch(NUMBER, block.text.strip()) and i + 1 < len(blocks):
            title = blocks[i + 1].text.split("\n")[0]
            if TITLE.fullmatch(title) and _title_case(title):
                hits.append(Heading(block.text.strip(), title, block.para_id, block.char_start))
        offset = block.char_start
        for line in block.text.split("\n"):
            match = LINE.fullmatch(line) or RUN_IN.match(line)
            if match and _title_case(match[2]):
                hits.append(Heading(match[1], match[2], block.para_id, offset))
            offset += len(line) + 1
        if hits:
            section = "§" + hits[-1].number
            headings.extend(hits)
        located.append(replace(block, section=section))
    return located, headings
