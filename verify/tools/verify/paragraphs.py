"""Paragraph blocks per text variant, quote-to-block resolution, and the unused pool.

The paragraph unit is a blank-line block of an extracted text. A quote resolves into
a block by a contiguous canonical match of one of its pieces, or by sharing at
least two 8-word shingles with the block; the second path catches quotes that the
extraction interrupts with figure labels or column spill. A single shared shingle
is treated as a repeated phrase, not as the quote. The unused pool (the
elusion sampling frame) is every block of at least `min_words` words that no
delivered row's quote resolves into. Fragments of quarantined records are not rows
and so never count as used.
"""
from __future__ import annotations

import bisect
import dataclasses
import re
import unicodedata

MIN_PROBE = 20          # canonical characters; shorter quote pieces never resolve
SHINGLE = 8             # words per shingle
MIN_SHINGLE_HITS = 2    # shared shingles needed for a block to count without a contiguous match
PIECE_SPLIT = re.compile(r"…|\.\.\.|\[[^\]]*\]|\*\*|\|")
_CITE = re.compile(r"\[\s*\d+(?:\s*[,\-–]\s*\d+)*\s*\]")
_HYPHEN_BREAK = re.compile(r"-\s*\n\s*")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


@dataclasses.dataclass(frozen=True)
class Block:
    variant: str
    seq: int
    text: str

    @property
    def para_id(self) -> str:
        return f"{self.variant}#{self.seq:04d}"

    @property
    def word_count(self) -> int:
        return len(self.text.split())


@dataclasses.dataclass(frozen=True)
class MergedBlock:
    variant: str
    seq: int
    text: str
    members: tuple[int, ...]

    @property
    def para_id(self) -> str:
        return f"{self.variant}~m{self.seq:04d}"

    @property
    def word_count(self) -> int:
        return len(self.text.split())


def canon(text: str) -> str:
    """Loose canonical form used only to locate a quote's block: alphanumerics only."""
    text = unicodedata.normalize("NFKC", text)
    text = _HYPHEN_BREAK.sub("", _CITE.sub(" ", text))
    return _NON_ALNUM.sub("", text.lower())


def words(text: str) -> list[str]:
    text = unicodedata.normalize("NFKC", text)
    text = _HYPHEN_BREAK.sub("", _CITE.sub(" ", text))
    return _NON_ALNUM.sub(" ", text.lower()).split()


def shingles(tokens: list[str], n: int = SHINGLE) -> set[str]:
    return {" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


def split_blocks(text: str, variant: str) -> list[Block]:
    out: list[Block] = []
    buf: list[str] = []
    for line in text.replace("\f", "\n").split("\n"):
        if line.strip():
            buf.append(line)
        elif buf:
            out.append(Block(variant, len(out) + 1, "\n".join(buf)))
            buf = []
    if buf:
        out.append(Block(variant, len(out) + 1, "\n".join(buf)))
    return out


def merge_blocks(blocks: list[Block], target: int = 60) -> list[MergedBlock]:
    """Greedily join consecutive blocks until each holds at least `target` words."""
    out: list[MergedBlock] = []
    buf: list[Block] = []
    words = 0
    for block in blocks:
        buf.append(block)
        words += block.word_count
        if words >= target:
            out.append(_merged(buf, len(out) + 1))
            buf, words = [], 0
    if buf:
        out.append(_merged(buf, len(out) + 1))
    return out


def _merged(buf: list[Block], seq: int) -> MergedBlock:
    return MergedBlock(buf[0].variant, seq, "\n".join(b.text for b in buf),
                       tuple(b.seq for b in buf))


def frame(blocks: list[Block], min_words: int) -> list[Block]:
    return [b for b in blocks if b.word_count >= min_words]


class Haystack:
    """Canonical concatenation of blocks with a map back to block sequence numbers."""

    def __init__(self, blocks: list[Block]):
        self.seqs = [b.seq for b in blocks]
        self.para_ids = [b.para_id for b in blocks]
        self.shingles = [shingles(words(b.text)) for b in blocks]
        self.starts: list[int] = []
        parts: list[str] = []
        pos = 0
        for block in blocks:
            self.starts.append(pos)
            c = canon(block.text)
            parts.append(c)
            pos += len(c)
        self.text = "".join(parts)

    def blocks_for(self, start: int, end: int) -> list[int]:
        first = bisect.bisect_right(self.starts, start) - 1
        last = bisect.bisect_right(self.starts, end - 1) - 1
        return self.seqs[first:last + 1]


def _hits(quote: str, hay: Haystack) -> tuple[list[int], set[int]]:
    """Blocks hit by contiguous pieces (in quote order) and by shared shingles."""
    contiguous: list[int] = []
    for piece in PIECE_SPLIT.split(quote):
        probe = canon(piece)
        if len(probe) < MIN_PROBE:
            continue
        at = hay.text.find(probe)
        while at >= 0:
            contiguous.extend(s for s in hay.blocks_for(at, at + len(probe)) if s not in contiguous)
            at = hay.text.find(probe, at + len(probe))
    probes = shingles(words(quote))
    shingled = {seq for seq, block in zip(hay.seqs, hay.shingles)
                if len(block & probes) >= MIN_SHINGLE_HITS}
    return contiguous, shingled


def _haystack(blocks: list[Block] | Haystack) -> Haystack:
    return blocks if isinstance(blocks, Haystack) else Haystack(blocks)


def resolve(quote: str, blocks: list[Block] | Haystack) -> list[int]:
    """Sequence numbers of the blocks the quote lands in (empty: unresolved)."""
    contiguous, shingled = _hits(quote, _haystack(blocks))
    return sorted(set(contiguous) | shingled)


def primary(quote: str, blocks: list[Block] | Haystack) -> int | None:
    """The block a locator points at: the first contiguous hit, else the first shingle hit."""
    contiguous, shingled = _hits(quote, _haystack(blocks))
    if contiguous:
        return contiguous[0]
    return min(shingled) if shingled else None
