"""Use the verifier's pure L1 API, with extract's narrower exact-only gate."""
from __future__ import annotations

from tools.verify.l1_exists import Result, Variant, check_quote


def check_against_raw(quote: str, text: str) -> Result:
    return check_quote(quote, [Variant('extract_raw', text)])


def check_against_codex(quote: str, codex_raw: str) -> Result:
    return check_quote(quote, [Variant('codex_raw', codex_raw)])


def require_exact(quote: str, text: str) -> Result:
    result = check_against_raw(quote, text)
    if result.grade != 'exact':
        raise ValueError(f'extract_raw L1 must be exact, got {result.grade}')
    return result
