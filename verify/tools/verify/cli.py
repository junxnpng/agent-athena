"""Command-line entry point: `python -m tools.verify <command> ...`."""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

from . import (judge, l1_exists, l2_schema, l6_arith, ledger, paths, queries, recall, report,
               schema, thresholds, waivers)
from .convert import claude, codex, common, gold

CONVERTERS = {"claude": claude, "codex": codex}


def _ledger_arg(p: argparse.ArgumentParser) -> None:
    p.add_argument("--ledger", type=pathlib.Path, default=paths.DEFAULT_LEDGER,
                   help="ledger path (default: results/verify-ledger.sqlite)")


def _source_arg(p: argparse.ArgumentParser) -> None:
    p.add_argument("--source-root", default=None,
                   help=f"input tree (default: ${paths.SOURCE_ENV})")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="verify")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("schema", help="evidence-record contract")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--print-required", action="store_true")
    g.add_argument("--validate", type=pathlib.Path, metavar="JSONL")

    p = sub.add_parser("ledger", help="ledger management")
    lsub = p.add_subparsers(dest="action", required=True)
    q = lsub.add_parser("init")
    _ledger_arg(q)
    q = lsub.add_parser("sql", help="run a read-only query, sqlite3-style output")
    q.add_argument("statement")
    _ledger_arg(q)
    q = lsub.add_parser("import", help="load a converter output file")
    q.add_argument("--file", type=pathlib.Path, required=True, action="append")
    _ledger_arg(q)
    _source_arg(q)

    p = sub.add_parser("query", help="queries (topic + claim)")
    qsub = p.add_subparsers(dest="action", required=True)
    q = qsub.add_parser("register")
    q.add_argument("--file", type=pathlib.Path, required=True)
    _ledger_arg(q)

    p = sub.add_parser("convert", help="convert an extractor's records to the contract,"
                       " or load the verbatim waivers or the gold set into the ledger")
    p.add_argument("extractor", choices=sorted(CONVERTERS) + ["gold", "waivers"])
    p.add_argument("--paper", help="paper slug (required for record sets)")
    p.add_argument("--out", type=pathlib.Path, default=None,
                   help="output file (default: results/converted/<extractor>-<paper>.json)")
    p.add_argument("--file", type=pathlib.Path, default=None,
                   help="waivers TSV (default: the waivers entry of config/sources.json) or gold"
                   " file (default: the source entry of config/gold_split.json)")
    _ledger_arg(p)
    _source_arg(p)

    p = sub.add_parser("l1", help="existence check of every quote row against the paper's texts")
    p.add_argument("--paper", required=True)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--all-variants", action="store_true",
                   help="every variant the paper has (the default)")
    g.add_argument("--variants", help="comma-separated subset of variants")
    p.add_argument("--report-variants", action="store_true",
                   help="also report the grade counts of each variant alone")
    _ledger_arg(p)
    _source_arg(p)

    p = sub.add_parser("l2", help="schema and tag check of every L1-passed row")
    p.add_argument("--paper", required=True)
    _ledger_arg(p)

    p = sub.add_parser("l6", help="arithmetic check of every L1-passed row")
    p.add_argument("--paper", required=True)
    _ledger_arg(p)
    p.add_argument("--source-root", default=None,
                   help=f"input tree for the Codex fragment check (default: ${paths.SOURCE_ENV};"
                   " skipped when neither is set)")

    p = sub.add_parser("recall", help="recall against G, elusion sample, capture-recapture")
    p.add_argument("--paper", required=True)
    p.add_argument("--query", default=None, help="query id, recorded with the run")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--elusion-export", type=pathlib.Path, metavar="TSV",
                   help="draw the registered elusion sample (once) and write it for review")
    g.add_argument("--elusion-import", type=pathlib.Path, metavar="TSV",
                   help="record the reviewed sample (missed_claims filled per block)")
    p.add_argument("--reviewer", help="who reviewed the sample (required with --elusion-import)")
    _ledger_arg(p)

    p = sub.add_parser("paragraphs", help="paragraph unit and unused pool")
    psub = p.add_subparsers(dest="action", required=True)
    q = psub.add_parser("pool")
    q.add_argument("--paper", required=True)
    _ledger_arg(q)

    p = sub.add_parser("judge", help="alignment: lexical sweep and the judge file round trip")
    jsub = p.add_subparsers(dest="action", required=True)
    q = jsub.add_parser("sweep", help="tier0 routing of every L1-passed row")
    q.add_argument("--backend", choices=["lexical"], default="lexical")
    q.add_argument("--paper", help="paper slug (default: the only paper in the ledger)")
    q.add_argument("--query", help="query id (default: the only registered query)")
    _ledger_arg(q)
    q = jsub.add_parser("export", help="write the judge's work file and seal its sha256")
    q.add_argument("--agent", choices=judge.AGENTS, default="manual",
                   help="judge client; only claude reads the Claude usage cache")
    q.add_argument("--paper", help="paper slug (default: the only paper in the ledger)")
    q.add_argument("--query", help="query id (default: the only registered query)")
    q.add_argument("--tier", choices=sorted(judge.TIERS), default="mid")
    q.add_argument("--context", choices=judge.CONTEXTS, default="para")
    q.add_argument("--swap-order", action="store_true", help="alternate query/evidence order")
    q.add_argument("--limit", type=int, default=20)
    q.add_argument("--out-dir", type=pathlib.Path, default=None,
                   help="default: results/judge")
    _ledger_arg(q)
    _source_arg(q)
    q = jsub.add_parser("import", help="check and record the judge's verdicts")
    q.add_argument("--export", type=pathlib.Path, required=True)
    q.add_argument("--verdicts", type=pathlib.Path, default=None,
                   help="default: the export path with .verdicts.jsonl")
    q.add_argument("--verifier-id", required=True)
    q.add_argument("--protocol-ver", required=True)
    q.add_argument("--manifest", required=True, help="sha256 printed by judge export")
    q.add_argument("--tokens-in", type=int, default=None)
    q.add_argument("--tokens-out", type=int, default=None)
    q.add_argument("--wallclock-s", type=float, default=None,
                   help="default: seconds since the export")
    _ledger_arg(q)
    _source_arg(q)

    p = sub.add_parser("report", help="the verification report of one paper and query")
    p.add_argument("--paper", required=True)
    p.add_argument("--query", required=True)
    p.add_argument("--out", type=pathlib.Path, default=None,
                   help="default: reports/verify-report-<paper>.md")
    p.add_argument("--strict", action="store_true", help="refuse while any section is not-run")
    _ledger_arg(p)
    _source_arg(p)

    p = sub.add_parser("slice", help="decision-gate facts of the thin slice")
    ssub = p.add_subparsers(dest="action", required=True)
    q = ssub.add_parser("facts")
    q.add_argument("--paper", required=True)
    q.add_argument("--query", required=True)
    q.add_argument("--out-dir", type=pathlib.Path, default=None, help="default: results/")
    _ledger_arg(q)

    p = sub.add_parser("thresholds", help="registered thresholds")
    tsub = p.add_subparsers(dest="action", required=True)
    for name in ("register", "show"):
        q = tsub.add_parser(name)
        q.add_argument("--file", type=pathlib.Path, default=thresholds.DEFAULT_PATH)
        _ledger_arg(q)
    return ap


def cmd_schema(args) -> int:
    if args.print_required:
        print("\n".join(schema.required_summary()))
        return 0
    status = collections.Counter()
    reasons = collections.Counter()
    for line in args.validate.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        res = schema.validate(json.loads(line))
        status[res.status] += 1
        reasons.update(res.reasons)
    print(f"pass: {status['pass']}, quarantine: {status['quarantine']}")
    for code, n in sorted(reasons.items()):
        print(f"  {code}: {n}")
    return 0


def cmd_ledger(args) -> int:
    if args.action == "init":
        ledger.init(args.ledger)
        print(f"ledger {args.ledger}: {len(ledger.TABLES)} tables")
        return 0
    if args.action == "sql":
        for row in ledger.query_readonly(args.ledger, args.statement):
            print("|".join("" if v is None else str(v) for v in row))
        return 0
    root = paths.source_root(args.source_root)
    conn = ledger.init(args.ledger)
    for f in args.file:
        payload = json.loads(f.read_text(encoding="utf-8"))
        counts = ledger.import_converted(conn, payload, root)
        print(f"{payload['extractor_id']} {payload['paper_id']}: rows: {counts['rows']},"
              f" quarantined: {counts['quarantined']}, already present: {counts['skipped']}")
    return 0


def cmd_query(args) -> int:
    conn = ledger.init(args.ledger)
    q = queries.load(args.file)
    queries.register(conn, q)
    print(f"query {q['query_id']} registered: {q['topic']}")
    return 0


def cmd_convert(args) -> int:
    if args.extractor == "gold":
        if not args.paper:
            raise common.ConvertError("convert gold needs --paper")
        res = gold.register(ledger.init(args.ledger), args.paper, args.file)
        print(gold.format_summary(res))
        return 0
    root = paths.source_root(args.source_root)
    if args.extractor == "waivers":
        return _convert_waivers(args, root)
    if not args.paper:
        raise common.ConvertError(f"convert {args.extractor} needs --paper")
    res = CONVERTERS[args.extractor].convert(root, args.paper)
    out = args.out or paths.RESULTS_DIR / "converted" / f"{args.extractor}-{args.paper}.json"
    common.write_payload(res, out)
    print(common.format_summary(res))
    print(f"wrote {out}")
    return 0


def _convert_waivers(args, root: pathlib.Path) -> int:
    path = args.file or waivers.default_path(root)
    conn = ledger.init(args.ledger)
    counts = waivers.import_tsv(conn, path)
    total, codes = conn.execute("select count(*), count(distinct reason_code) from waivers").fetchone()
    print(f"waivers: {total} (inserted {counts['inserted']}), reason codes: {codes}")
    for code, n in conn.execute("select reason_code, count(*) from waivers group by reason_code"
                                " order by count(*) desc, reason_code"):
        print(f"  {code}: {n}")
    print("\n".join(waivers.format_rates(waivers.rates(conn, root))))
    return 0


def cmd_l1(args) -> int:
    root = paths.source_root(args.source_root)
    conn = ledger.init(args.ledger)
    names = [v.strip() for v in args.variants.split(",")] if args.variants else None
    summary = l1_exists.run(conn, root, args.paper, names)
    print(l1_exists.format_summary(summary, l1_exists.waived_refs(conn, args.paper),
                                   args.report_variants))
    return 0


def cmd_l2(args) -> int:
    conn = ledger.init(args.ledger)
    print(l2_schema.format_summary(l2_schema.run(conn, args.paper)))
    return 0


def cmd_l6(args) -> int:
    conn = ledger.init(args.ledger)
    try:
        root = paths.source_root(args.source_root)
    except paths.SourceRootError:
        if args.source_root:
            raise
        root = None
    print(l6_arith.format_summary(l6_arith.run(conn, root, args.paper)))
    return 0


def cmd_judge(args) -> int:
    conn = ledger.init(args.ledger)
    if args.action == "import":
        verdicts = args.verdicts or args.export.with_suffix(".verdicts.jsonl")
        res = judge.import_verdicts(conn, paths.source_root(args.source_root), args.export,
                                    verdicts, args.verifier_id, args.protocol_ver, args.manifest,
                                    args.tokens_in, args.tokens_out, args.wallclock_s)
        print(judge.format_import(res))
        return 0
    paper = args.paper or judge.default_paper(conn)
    query = args.query or judge.default_query(conn)
    if args.action == "sweep":
        print(judge.format_sweep(judge.sweep(conn, paper, query)))
        return 0
    ex = judge.export(conn, paths.source_root(args.source_root), paper, query, args.tier,
                      args.context, args.swap_order, args.limit, args.out_dir, args.agent)
    print(f"export {ex.path}")
    print(f"manifest {ex.sha256}")
    print(f"items: {len(ex.payload['items'])}, tier: {ex.payload['tier']}, context:"
          f" {ex.payload['context_width']}, judge protocol: {ex.payload['judge_protocol']}")
    print(f"verdicts go to {ex.path.with_suffix('.verdicts.jsonl')}")
    print(f"judge instructions: {judge.SKILL_PATH}")
    return 0


def cmd_report(args) -> int:
    conn = ledger.init(args.ledger)
    text = report.render(conn, paths.source_root(args.source_root), args.paper, args.query,
                         args.strict)
    out = args.out or paths.ROOT / "reports" / f"verify-report-{args.paper}.md"
    print(f"wrote {report.write(text, out)}")
    return 0


def cmd_slice(args) -> int:
    conn = ledger.init(args.ledger)
    facts = report.slice_facts(conn, args.paper, args.query)
    path = report.write_slice_facts(facts, args.out_dir)
    print(json.dumps(facts, ensure_ascii=False, indent=1))
    print(f"wrote {path}")
    return 0


def cmd_recall(args) -> int:
    conn = ledger.init(args.ledger)
    if args.elusion_import and not args.reviewer:
        build_parser().error("--elusion-import needs --reviewer")
    if args.elusion_export:
        sample = recall.export_elusion(conn, args.paper, args.elusion_export)
        print(f"elusion sample {sample['sample_id']}: sampled: {sample['n']} of unused_pool"
              f" {sample['unused_pool']} (seed {sample['seed']}) -> {sample['file']}")
    if args.elusion_import:
        res = recall.import_elusion(conn, args.paper, args.elusion_import, args.reviewer)
        print(f"elusion review of {res['sample_id']}: {res['k']}/{res['n']} blocks with a missed"
              f" claim, by {res['reviewer']}")
    s = recall.run(conn, args.paper, args.query)
    print(recall.format_summary(s, recall.elusion_status(conn, args.paper)))
    return 0


def cmd_paragraphs(args) -> int:
    conn = ledger.init(args.ledger)
    frame = ledger.frame_blocks(conn, args.paper)
    pool = ledger.unused_pool(conn, args.paper)
    unit = ledger.paragraph_unit(conn)
    print(f"{args.paper} paragraph unit: {unit['variant']} {unit['split']}"
          f" >= {unit['min_words']} words")
    print(f"frame: {len(frame)}, used: {len(frame) - len(pool)}, unused_pool: {len(pool)}")
    return 0


def cmd_thresholds(args) -> int:
    conn = ledger.init(args.ledger)
    if args.action == "register":
        run_id = thresholds.register(conn, args.file)
        print(f"registered {args.file} sha256 {thresholds.sha256_file(args.file)} as {run_id}")
        return 0
    guard = thresholds.begin(conn, args.file)
    print(f"registered as {guard.run_id}, sha256 {guard.sha}")
    for key in thresholds.REQUIRED_KEYS:
        print(f"{key}: {json.dumps(guard.data[key], ensure_ascii=False)}")
    return 0


COMMANDS = {"schema": cmd_schema, "ledger": cmd_ledger, "query": cmd_query,
            "convert": cmd_convert, "paragraphs": cmd_paragraphs, "thresholds": cmd_thresholds,
            "l1": cmd_l1, "l2": cmd_l2, "l6": cmd_l6, "judge": cmd_judge, "recall": cmd_recall,
            "report": cmd_report,
            "slice": cmd_slice}
ERRORS = (paths.SourceRootError, common.ConvertError, ledger.LedgerError,
          queries.QueryError, thresholds.ThresholdsError, l1_exists.L1Error,
          waivers.WaiverError, gold.GoldError, judge.JudgeError, report.ReportIncomplete,
          l6_arith.L6Error, recall.RecallError)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return COMMANDS[args.command](args)
    except paths.SourceRootError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ERRORS as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
