"""The interface every judge backend implements."""
from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class Route:
    verdict: str
    features: dict


class JudgeBackend:
    """A backend maps (quote, query) to a verdict. Subclasses name their verifier."""

    verifier_id = "abstract"
    tier = "tier0"

    def route(self, quote: str, query: dict) -> Route:
        raise NotImplementedError
