"""Read a verifier query while retaining its confirmation status."""
from __future__ import annotations

from pathlib import Path
import sys
from typing import Union

from tools.verify import queries


def load(path: Union[Path, str]) -> dict:
    try:
        value = queries.load(path)
    except queries.QueryError as exc:
        print(f"질의 오류: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    return dict(value, unconfirmed=not bool(value["confirmed_by"]))
