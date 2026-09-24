"""Lossless sentence slices; offsets are Unicode character positions in raw text."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Optional

from tools.verify.paragraphs import Block

DEFAULT_PATH = Path(__file__).resolve().parents[1] / "config/segmenter.json"


@dataclass(frozen=True)
class Segment:
    segment_id: str
    text: str
    page: int
    section: Optional[str]
    para_id: str
    char_start: int
    char_end: int
    resolved_para_ids: tuple[str, ...]


def load_config(path: Path = DEFAULT_PATH) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(cfg, dict) or cfg.get("segmenter_ver") != "v1"
            or not isinstance(cfg.get("abbreviations"), list)
            or not all(isinstance(a, str) and a for a in cfg["abbreviations"])
            or cfg.get("protect_decimals") is not True or cfg.get("protect_exponents") is not True):
        raise ValueError("segmenter v1 설정이 올바르지 않습니다")
    return cfg


def split_block_to_segments(block: Block, cfg: dict) -> list[Segment]:
    text = block.text
    protected = set()
    for abbreviation in cfg["abbreviations"]:
        for match in re.finditer(r"(?<!\w)" + re.escape(abbreviation), text):
            protected.update(range(match.start(), match.end()))
    for match in re.finditer(r"\d+\.\d+|\d+\^\d+", text):
        protected.update(range(match.start(), match.end()))
    cuts = []
    for match in re.finditer(r'[.!?]+["\u201d\u2019\')\]]*(?:\s+|$)', text):
        if not any(i in protected for i in range(match.start(), match.end()) if text[i] in '.!?'):
            cuts.append(match.end())
    if not cuts or cuts[-1] != len(text):
        cuts.append(len(text))
    start = 0
    result = []
    base = getattr(block, "char_start", 0)
    for end in cuts:
        if end > start:
            result.append(Segment(f"{block.para_id}.s{len(result) + 1}", text[start:end],
                                  getattr(block, "page", 1), getattr(block, "section", None),
                                  block.para_id, base + start, base + end, (block.para_id,)))
        start = end
    return result
