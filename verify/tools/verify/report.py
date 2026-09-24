"""The verification report and the slice facts of the decision gate.

The report has four judgment sections: existence, alignment, recall and
condition preservation. A section whose layer has not run says `not-run`; a
strict render refuses to produce a report while any section says so. The head of
the report carries the L1 grade distribution, the representative number of v1.
"""
from __future__ import annotations

import collections
import json
import pathlib
import sqlite3

from . import judge, l1_exists, l2_schema, l6_arith, ledger, queries, recall, usage, waivers
from .paths import RESULTS_DIR
from .schema import CONDITION_FIELDS

SECTIONS = ("Existence", "Alignment", "Recall", "Condition preservation")
NOT_RUN = "not-run"


class ReportIncomplete(RuntimeError):
    pass


def _latest_run(conn: sqlite3.Connection, kind: str, **meta) -> tuple | None:
    for run_id, protocol, meta_json, created in conn.execute(
            "select run_id, protocol_ver, meta_json, created_at from runs where run_kind=?"
            " order by created_at desc, run_id desc", (kind,)):
        m = json.loads(meta_json or "{}")
        if all(m.get(k) == v for k, v in meta.items()):
            return run_id, protocol, m, created
    return None


def l1_grades(conn: sqlite3.Connection, paper_id: str) -> dict:
    """Grade counts of each extractor set under the latest existence check of every row."""
    grades: dict = collections.defaultdict(lambda: dict.fromkeys(l1_exists.ALL_GRADES, 0))
    for row_id, taut, grade in conn.execute(
            "select l.row_id, l.l1_tautological, l.grade from v_l1_latest l"
            " join claims c using(row_id) where c.paper_id=?", (paper_id,)):
        grades[l1_exists.extractor_set(row_id, taut)][grade] += 1
    return {k: grades[k] for k in sorted(grades, key=lambda k: (k == "codex", k))}


def _grade_table(grades: dict, pass_grades: list[str]) -> list[str]:
    cols = l1_exists.ALL_GRADES
    lines = ["| set | rows | " + " | ".join(cols) + " | PASS |",
             "|---|---:|" + "---:|" * len(cols) + "---:|"]
    for k, c in grades.items():
        n = sum(c.values())
        label = "codex (l1_tautological=1)" if k == "codex" else k
        passed = sum(c[g] for g in pass_grades)
        lines.append(f"| {label} | {n} | " + " | ".join(str(c[g]) for g in cols)
                     + f" | {passed}/{n} |")
    return lines


def _existence(conn, root, paper_id, run) -> list[str]:
    run_id, protocol, meta, _ = run
    verdicts = dict(conn.execute(
        "select l.verdict, count(*) from v_l1_latest l join claims c using(row_id)"
        " where c.paper_id=? group by l.verdict", (paper_id,)).fetchall())
    verifiers = sorted({v for (v,) in conn.execute(
        "select distinct l.verifier_id from v_l1_latest l join claims c using(row_id)"
        " where c.paper_id=?", (paper_id,))})
    rates = waivers.rates(conn, root)
    mine = rates["papers"].get(paper_id, (0, 0))
    (a, b), (c, d) = rates["overall_rows"], rates["overall_records"]
    return [
        f"- verifier: {', '.join(verifiers)}, protocol: {protocol}, latest run: `{run_id}`",
        f"- pass grades: {', '.join(meta['pass_grades'])}",
        f"- variants: {', '.join(meta['variants'])}"
        + "".join(f"; {u}: unavailable" for u in meta["unavailable"]),
        f"- verdicts: PASS {verdicts.get('PASS', 0)}, MISS {verdicts.get('MISS', 0)}"
        " (waivers are a separate table, never a verdict)",
        f"- waiver_rate: this paper {mine[0]}/{mine[1]} rows; overall {a}/{b} rows ({c}/{d} records)",
    ]


def _alignment(conn, paper_id, query_id) -> list[str] | None:
    sweep = _latest_run(conn, "judge-sweep", paper_id=paper_id, query_id=query_id)
    judged = conn.execute(
        "select j.alignment, j.faithfulness, j.verifier_id, j.protocol_ver, j.tier"
        " from v_judgments j join claims c using(row_id) where c.paper_id=? and j.query_id=?",
        (paper_id, query_id)).fetchall()
    if sweep is None and not judged:
        return None
    lines = []
    if sweep is None:
        lines.append(f"- tier0 sweep: {NOT_RUN}")
    else:
        routes = dict(conn.execute("select verdict, count(*) from checks where run_id=?"
                                   " group by verdict", (sweep[0],)).fetchall())
        n = sum(routes.values())
        esc = routes.get("needs-judge", 0)
        lines += [f"- tier0 sweep `{sweep[0]}` ({sweep[2]['verifier_id']}): {n} rows,"
                  f" needs-judge {esc}, insufficient {routes.get('insufficient', 0)}",
                  f"- escalation_rate: {esc / n:.3f} (observed)" if n else "- escalation_rate: n/a"]
        tier2 = sum(1 for j in judged if j[4] == "tier2")
        lines.append("- expensive_ratio: " + (f"{tier2 / n:.3f}" if tier2 else "0 (tier2 not invoked)"))
    if not judged:
        lines.append(f"- tier1 judge: {NOT_RUN}")
        return lines
    who = sorted({f"{j[2]} ({j[3]}, {j[4]})" for j in judged})
    lines.append(f"- judged rows: {len(judged)} by {', '.join(who)}")
    last = _latest_run(conn, "judge-import", paper_id=paper_id, query_id=query_id)
    if last and last[2].get("usage"):
        lines.append(f"- {usage.format_delta(last[2]['usage'])} (latest round trip)")
    table = collections.Counter((j[0], j[1]) for j in judged)
    lines += ["", "| alignment \\ faithfulness | " + " | ".join(judge.VERDICTS) + " |",
              "|---|" + "---:|" * len(judge.VERDICTS)]
    for a in judge.VERDICTS:
        lines.append(f"| {a} | " + " | ".join(str(table[(a, f)]) for f in judge.VERDICTS) + " |")
    return lines


def _conditions(conn, paper_id) -> list[str] | None:
    l2 = _latest_run(conn, "l2", paper_id=paper_id)
    l6 = _latest_run(conn, "l6", paper_id=paper_id)
    if l2 is None and l6 is None:
        return None
    lines = []
    if l2 is None:
        lines.append(f"- L2 schema/tags: {NOT_RUN}")
    else:
        run_id, protocol, m, _ = l2
        lines += [f"- L2 schema/tags `{run_id}` ({m['verifier_id']}, {protocol}): {m['rows']} rows,"
                  f" pass {m['pass']}, quarantine {m['quarantine']} (quarantined rows are not comparable)",
                  f"- {l2_schema.format_rate(m['quarantine'], m['rows'])}",
                  "- reason codes: " + (", ".join(f"{k} {v}" for k, v in m["reasons"].items())
                                        or "none")]
    if l6 is None:
        lines.append(f"- L6 arithmetic: {NOT_RUN}")
    else:
        run_id, protocol, m, _ = l6
        inline = m["inline"]
        lines += [f"- L6 arithmetic `{run_id}` ({m['verifier_id']}, {protocol}): {m['rows']} rows,"
                  f" pass {m['verdicts']['pass']}, flag {m['verdicts']['flag']}",
                  f"- {l6_arith.format_derived(m['derived_from'])}",
                  f"- inline arithmetic in number strings: found {inline['found']},"
                  f" consistent {inline['consistent']}, mismatch {inline['mismatch']}",
                  f"- intra_doc_conflict: {m['conflict_pairs']} pairs"
                  f" ({m['keyed_values']} keyed values compared)",
                  f"- {l6_arith.format_fragments(m['fragments'])}"]
    return lines


def _recall(conn, paper_id) -> list[str] | None:
    run = _latest_run(conn, "recall", paper_id=paper_id)
    if run is None:
        return None
    s = recall.Summary.from_meta(run[2])
    lines = [f"- `{s.run_id}` ({recall.VERIFIER_ID}, {run[1]}), config {s.config_version};"
             f" gold: {s.gold_split_count} sentences; rows: L1-passed only ("
             + ", ".join(f"{n} {k}" for n, k in s.rows_by_set.items()) + ")", "",
             *recall.format_table(s), "", *[f"- {line.strip()}" for line in recall.format_probes()], "",
             f"- gold sentences no row covers: {recall.format_misses(s.misses)}", ""]
    e = recall.elusion_status(conn, paper_id)
    lines += ["```", *recall.format_elusion(e, recall.gold_floor(s, e)),
              *recall.format_chapman(s.chapman), "```"]
    return lines


def _not_applicable(conn, paper_id) -> list[str]:
    out = []
    l6 = _latest_run(conn, "l6", paper_id=paper_id)
    if l6 is not None and not l6[2]["derived_from"]["applicable_rows"]:
        out.append("- L6 derived_from recomputation: applicable_rows: 0"
                   " (no row carries a derived_from pointer)")
    rc = _latest_run(conn, "recall", paper_id=paper_id)
    if rc is not None:
        out += [f"- recall probes P and target set T: {recall.FROZEN}",
                f"- recall conditions_match: {rc[2]['table']['conditions_match']['not_applicable']}"]
    return out or ["- none recorded yet"]


def render(conn: sqlite3.Connection, root: pathlib.Path, paper_id: str, query_id: str,
           strict: bool = False) -> str:
    run = _latest_run(conn, "l1", paper_id=paper_id)
    if run is None:
        raise ReportIncomplete(f"{paper_id}: no l1 run; the report starts from the existence check")
    query = queries.get(conn, query_id)
    if query is None:
        raise ReportIncomplete(f"unknown query {query_id}")
    grades = l1_grades(conn, paper_id)
    sections = {"Existence": _existence(conn, root, paper_id, run),
                "Alignment": _alignment(conn, paper_id, query_id),
                "Recall": _recall(conn, paper_id), "Condition preservation": _conditions(conn, paper_id)}
    missing = [name for name, body in sections.items()
               if body is None or any(NOT_RUN in line for line in body)]
    if strict and missing:
        raise ReportIncomplete(f"sections not run: {', '.join(missing)}")
    titles = {"Existence": "존재", "Alignment": "합치", "Recall": "재현율",
              "Condition preservation": "조건 보존"}
    out = [f"# 근거 검증 보고서: {paper_id}", "",
           f"질의 `{query_id}` ({'확인자: ' + query['confirmed_by'] if query['confirmed_by'] else '미확인 초안'}):"
           f" {query['claim_text']}", "",
           "**L1 grade distribution — 원문 변형별 최상위 일치 등급 분포**", "",
           "이 보고서는 실행된 검사 결과입니다. 변이 시험·인수 게이트(P6·P7)는 미구현이며, "
           "미실행 검사와 적용 대상이 없는 검사를 구분해 표시합니다.", "",
           *_grade_table(grades, run[2]["pass_grades"]), ""]
    for name in SECTIONS:
        body = sections[name]
        out += [f"## {titles[name]} ({name})", ""] + (body if body is not None else [NOT_RUN]) + [""]
    out += ["## 적용 대상 없음 (Not applicable)", "", *_not_applicable(conn, paper_id), ""]
    return "\n".join(out)


def write(text: str, out: pathlib.Path) -> pathlib.Path:
    out = pathlib.Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    return out


# --- slice facts ----------------------------------------------------------

def _rows_with(rows, test) -> dict:
    return {"rows": sum(1 for r in rows if test(r)), "of": len(rows)}


def _conditions_complete(row) -> bool:
    cond = json.loads(row["conditions_json"] or "{}")
    return all(str(cond.get(f) or "").strip() for f in CONDITION_FIELDS)


def _has_derived_from(row) -> bool:
    return any(isinstance(n, dict) and n.get("derived_from")
               for n in json.loads(row["numbers_json"] or "[]"))


def slice_facts(conn: sqlite3.Connection, paper_id: str, query_id: str) -> dict:
    """The five measured facts the decision gate reads."""
    run = _latest_run(conn, "judge-import", paper_id=paper_id, query_id=query_id)
    if run is None:
        raise ReportIncomplete(f"{paper_id} x {query_id}: no judge import; run judge export/import first")
    run_id, protocol, meta, created = run
    rows = ledger.l1_passed(conn, paper_id)
    judged = conn.execute("select alignment, faithfulness from v_judgments where run_id=?",
                          (run_id,)).fetchall()
    align = dict.fromkeys(judge.VERDICTS, 0)
    faith = dict.fromkeys(judge.VERDICTS, 0)
    for a, f in judged:
        align[a] += 1
        faith[f] += 1
    budget = conn.execute("select tokens_in, tokens_out, wallclock_s from budget where run_id=?",
                          (run_id,)).fetchone()
    tokens = None if budget[0] is None and budget[1] is None else (budget[0] or 0) + (budget[1] or 0)
    return {
        "run_id": run_id, "paper_id": paper_id, "query_id": query_id,
        "verifier_id": meta["verifier_id"], "protocol_ver": protocol, "created_at": created,
        "l1_grades": l1_grades(conn, paper_id),
        "conditions_complete_rows": _rows_with(rows, _conditions_complete),
        "derived_from_rows": _rows_with(rows, _has_derived_from),
        "tier1": {"rows": len(judged), "alignment": align, "faithfulness": faith,
                  "unknown_ratio": align["unknown"] / len(judged) if judged else None},
        "round_trip": {"tokens": tokens, "tokens_in": budget[0], "tokens_out": budget[1],
                       "wallclock_s": budget[2],
                       "usage_points": (meta.get("usage") or {}).get("points"),
                       "usage": meta.get("usage")},
    }


def write_slice_facts(facts: dict, out_dir: pathlib.Path | None = None) -> pathlib.Path:
    out_dir = pathlib.Path(out_dir or RESULTS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"slice-facts-{facts['run_id']}.json"
    path.write_text(json.dumps(facts, ensure_ascii=False, indent=1) + "\n")
    return path
