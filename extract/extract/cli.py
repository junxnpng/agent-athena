"""Local extraction CLI for preflight and the minimal P4a file round trip."""
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
    segment = commands.add_parser("segment", help="전체 표시 세그먼트와 SHA-256 봉인 생성")
    build = commands.add_parser("build", help="선택 ID에서 레코드·발췌집 생성")
    for command in (segment, build):
        command.add_argument("--query", type=Path, required=True)
        command.add_argument("--gates", type=Path, default=gates.DEFAULT_PATH)
        command.add_argument("--slug", required=True)
    segment.add_argument("--pdf", type=Path)
    segment.add_argument("--source-root")
    segment.add_argument("--codex-raw", type=Path)
    segment.add_argument("--out-dir", type=Path)
    segment.add_argument("--arxiv-stamp")
    build.add_argument("--workfile", type=Path)
    build.add_argument("--selections", type=Path, required=True)
    build.add_argument("--agent", choices=("codex", "claude"), required=True)
    build.add_argument("--model", required=True)
    build.add_argument("--gold", type=Path)
    args = parser.parse_args(argv)
    try:
        gates.assert_paragraph_unit_split()
        criteria = gates.load_gates(args.gates)
        loaded = query.load(args.query)
        if args.command == "check":
            result = {"status": "ready", "query": loaded, "gates": criteria,
                      "gates_sha256": gates.sha256_of(args.gates)}
        else:
            from . import workflow
            result = getattr(workflow, args.command)(args, loaded)
    except (OSError, RuntimeError, ValueError, KeyError, TypeError) as exc:
        print(f"발췌 실행 실패: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
