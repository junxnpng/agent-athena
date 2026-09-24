"""Offset-preserving text normalization for the existence check.

Every rule is fixed in `config/normalization.json`; the code only knows how each
rule id transforms text. A normalized string keeps, for each of its characters,
the offset of the original character it came from, so a match found in
normalized space maps back to a span of the variant text.
"""
from __future__ import annotations

import dataclasses
import functools
import pathlib
import re

import json

from .paths import CONFIG_DIR

DEFAULT_PATH = CONFIG_DIR / "normalization.json"
_LINE_BREAK_HYPHEN = re.compile(r"-[ \t]*\n\s*")


class NormalizationError(RuntimeError):
    pass


@dataclasses.dataclass(frozen=True)
class Gapped:
    min_run: int
    max_runs: int
    max_gap_chars: int


@dataclasses.dataclass(frozen=True)
class Config:
    rules: dict
    strict: tuple[str, ...]
    loose_citation: str
    gapped: Gapped
    sha256: str


@functools.lru_cache(maxsize=4)
def load(path: pathlib.Path = DEFAULT_PATH) -> Config:
    import hashlib

    raw = pathlib.Path(path).read_bytes()
    data = json.loads(raw)
    rules = data.get("rules") or {}
    strict = tuple(data["profiles"]["strict"])
    unknown = [r for r in list(rules) + list(strict) if r not in _RULES]
    if unknown:
        raise NormalizationError(f"{path}: unknown rule {', '.join(unknown)}")
    missing = [r for r in strict if r not in rules]
    if missing:
        raise NormalizationError(f"{path}: profile uses undefined rule {', '.join(missing)}")
    g = data["profiles"]["gapped"]
    return Config(rules, strict, data["profiles"]["loose"]["citation"],
                  Gapped(int(g["min_run"]), int(g["max_runs"]), int(g["max_gap_chars"])),
                  hashlib.sha256(raw).hexdigest())


@dataclasses.dataclass(frozen=True)
class Normalized:
    text: str
    index: tuple[int, ...]  # original offset of each normalized character

    def span(self, start: int, end: int) -> tuple[int, int]:
        """Original [start, end) covered by normalized [start, end)."""
        return self.index[start], self.index[end - 1] + 1


Chars = list[tuple[str, int]]


def _hyphen(chars: Chars, rule: dict) -> Chars:
    table, drop = rule.get("map", {}), set(rule.get("drop", []))
    out: Chars = []
    for ch, pos in chars:
        if ch in drop:
            continue
        out.append((table.get(ch, ch), pos))
    if not rule.get("join_line_break"):
        return out
    text = "".join(c for c, _ in out)
    keep = [True] * len(out)
    for m in _LINE_BREAK_HYPHEN.finditer(text):
        for i in range(m.start(), m.end()):
            keep[i] = False
    return [c for c, k in zip(out, keep) if k]


def _mapping(chars: Chars, rule: dict) -> Chars:
    table = rule.get("map", {})
    out: Chars = []
    for ch, pos in chars:
        out.extend((c, pos) for c in table.get(ch, ch))
    return out


def _whitespace(chars: Chars, rule: dict) -> Chars:
    out: Chars = []
    for ch, pos in chars:
        if ch.isspace():
            if out and out[-1][0] == " ":
                continue
            out.append((" ", pos))
        else:
            out.append((ch, pos))
    return out


def _sentence_case(chars: Chars, rule: dict) -> Chars:
    terminators = set(rule.get("terminators", ".!?"))
    out: Chars = []
    initial, gap = True, False
    for ch, pos in chars:
        if ch.isalpha():
            out.append((ch.lower() if initial else ch, pos))
            initial = gap = False
            continue
        out.append((ch, pos))
        if ch in terminators:
            gap = True
        elif ch.isspace():
            initial = initial or gap
        elif not ch.isdigit():
            gap = False
        else:
            initial = gap = False
    return out


def _line_join_space(chars: Chars, rule: dict) -> Chars:
    return [(c, p) for c, p in chars if not c.isspace()]


_RULES = {"hyphen": _hyphen, "ligature": _mapping, "quotes": _mapping,
          "whitespace": _whitespace, "sentence_case": _sentence_case,
          "line_join_space": _line_join_space}


def apply(text: str, rules: list[str] | tuple[str, ...], cfg: Config | None = None) -> Normalized:
    cfg = cfg or load()
    chars: Chars = [(c, i) for i, c in enumerate(text)]
    for name in rules:
        if name not in _RULES or name not in cfg.rules:
            raise NormalizationError(f"unknown rule {name}")
        chars = _RULES[name](chars, cfg.rules[name])
    return Normalized("".join(c for c, _ in chars), tuple(p for _, p in chars))


def strict(text: str, cfg: Config | None = None) -> Normalized:
    cfg = cfg or load()
    return apply(text, cfg.strict, cfg)


def strict_needle(text: str, cfg: Config | None = None) -> str:
    return strict(text.strip(), cfg).text


def loose(text: str, cfg: Config | None = None) -> Normalized:
    """Citation markers dropped, then lower-case alphanumerics only."""
    cfg = cfg or load()
    cited = [False] * len(text)
    for m in re.finditer(cfg.loose_citation, text):
        for i in range(m.start(), m.end()):
            cited[i] = True
    chars = [(c.lower(), i) for i, c in enumerate(text)
             if not cited[i] and c.isascii() and c.isalnum()]
    return Normalized("".join(c for c, _ in chars), tuple(p for _, p in chars))


def find(hay: Normalized, needle: str, start: int = 0,
         either_case_first: bool = True) -> tuple[int, int] | None:
    """Earliest [start, end) of needle in hay at or after start, in normalized offsets.

    The needle's first letter (not its first character) may match in either case:
    a quote piece may capitalize a mid-sentence start or lower-case a sentence start.
    """
    if not needle:
        return None
    candidates = {needle}
    first = next((i for i, c in enumerate(needle) if c.isalpha()), None)
    if either_case_first and first is not None:
        head, ch, tail = needle[:first], needle[first], needle[first + 1:]
        candidates |= {head + ch.lower() + tail, head + ch.upper() + tail}
    best = None
    for cand in candidates:
        at = hay.text.find(cand, start)
        if at >= 0 and (best is None or at < best):
            best = at
    return None if best is None else (best, best + len(needle))
