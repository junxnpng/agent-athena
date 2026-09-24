"""Placeholder for a small API model as the first sweep. Resumed when the corpus grows."""
from __future__ import annotations

from .base import JudgeBackend, Route


class SmallAPIBackend(JudgeBackend):
    verifier_id = "api-small-unset"

    def route(self, quote: str, query: dict) -> Route:
        raise NotImplementedError("small API backend is a stub in v1")
