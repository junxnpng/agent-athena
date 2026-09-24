"""Tier0: a stdlib lexical router over numbers, units, negation, modality and names.

It routes and nothing else. `insufficient` means the row shares no content word,
number or proper noun with the query; everything else goes to the judge.
"""
from __future__ import annotations

import pathlib
import re

import json

from ..paths import CONFIG_DIR
from .base import JudgeBackend, Route

CONFIG_PATH = CONFIG_DIR / "lexical.json"
ROUTES = ("insufficient", "needs-judge")
VERIFIER_ID = "lexical-v1"
_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9'’\-]*|\d+(?:\.\d+)?")
_NUMBER = re.compile(r"\d+(?:\.\d+)?")
_SENTENCE_END = re.compile(r"[.!?:]\s*$")


class LexicalBackend(JudgeBackend):
    verifier_id = VERIFIER_ID
    tier = "tier0"

    def __init__(self, path: pathlib.Path = CONFIG_PATH):
        cfg = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        self.version = cfg["version"]
        self.min_overlap = int(cfg["min_content_overlap"])
        self.suffixes = tuple(cfg["suffixes"])
        self.stop = {w.lower() for w in cfg["stopwords"]}
        self.negations = {w.lower() for w in cfg["negations"]}
        self.modality = {w.lower() for w in cfg["modality"]}

    def _stem(self, word: str) -> str:
        for suffix in self.suffixes:
            if word.endswith(suffix) and len(word) - len(suffix) >= 3:
                word = word[:-len(suffix)]
                break
        return word[:-1] if word.endswith("e") and len(word) > 3 else word

    def _words(self, text: str) -> list[str]:
        out = []
        for tok in _TOKEN.findall(text or ""):
            out.extend(p for p in re.split(r"[-]", tok.lower()) if p)
        return out

    def _content(self, text: str) -> set[str]:
        return {self._stem(w) for w in self._words(text)
                if w not in self.stop and not _NUMBER.fullmatch(w) and len(w) > 1}

    def _proper_nouns(self, text: str) -> set[str]:
        """Capitalized tokens that do not start a sentence, and tokens with inner capitals."""
        names = set()
        for m in _TOKEN.finditer(text or ""):
            tok = m.group(0)
            if not tok[0].isalpha():
                continue
            inner = any(c.isupper() for c in tok[1:])
            initial = m.start() == 0 or bool(_SENTENCE_END.search(text[:m.start()]))
            if inner or (tok[0].isupper() and not initial):
                names.add(tok.lower())
        return names

    def route(self, quote: str, query: dict) -> Route:
        q_text = f"{query.get('topic', '')}. {query.get('claim_text', '')}"
        words = set(self._words(quote))
        overlap = sorted(self._content(quote) & self._content(q_text))
        numbers = sorted(set(_NUMBER.findall(quote or "")) & set(_NUMBER.findall(q_text)))
        q_words = set(self._words(q_text))
        names = sorted(n for n in self._proper_nouns(quote) if n in q_words)
        features = {
            "content_overlap": len(overlap), "shared_words": overlap,
            "shared_numbers": numbers, "shared_proper_nouns": names,
            "negation": sorted(words & self.negations),
            "modality": sorted(words & self.modality),
        }
        connected = len(overlap) >= self.min_overlap or numbers or names
        return Route("needs-judge" if connected else "insufficient", features)
