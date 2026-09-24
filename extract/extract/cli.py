"""Validate extraction inputs without generating records or touching a ledger."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Optional, Sequence

from . import gates, query


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="evidence-extract")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="질의·게이트·verify 문단 계약 사전 검사")
    check.add_argument("--query", type=Path, required=True)
    check.add_argument("--gates", type=Path, default=gates.DEFAULT_PATH)
    args = parser.parse_args(argv)
    try:
        gates.assert_paragraph_unit_split()
        criteria = gates.load_gates(args.gates)
        loaded = query.load(args.query)
        result = {"status": "ready", "query": loaded, "gates": criteria,
                  "gates_sha256": gates.sha256_of(args.gates)}
    except (OSError, RuntimeError) as exc:
        print(f"발췌 사전 검사 실패: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
