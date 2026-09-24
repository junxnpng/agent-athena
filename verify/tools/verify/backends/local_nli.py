"""Placeholder for a local NLI model (MiniCheck class). Resumed when the corpus grows."""
from __future__ import annotations

from .base import JudgeBackend, Route


class LocalNLIBackend(JudgeBackend):
    verifier_id = "local-nli-unset"

    def route(self, quote: str, query: dict) -> Route:
        raise NotImplementedError("local NLI backend is a stub in v1")
