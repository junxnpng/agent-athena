"""Existence check (L1): does each quote occur in the paper's own text?

A quote is split into pieces at elision marks, and the pieces must occur in order
in one text variant. The grade is the strictest profile at which they do:
exact (raw text), strict (the six normalization rules), loose (alphanumerics
only), gapped (loose, allowing a few intrusions of foreign text such as a running
header or a figure block between long runs of the quote), else MISS. A row's grade is its best over every available variant; the
verdict is PASS when the grade is one of the registered `l1_pass_grades` and
MISS otherwise. Waivers never enter the verdict: they stay in their own table.
"""
from __future__ import annotations

import bisect
import collections
import dataclasses
import functools
import hashlib
import json
import pathlib
import sqlite3

from . import ledger, normalize as nz, thresholds
from .convert import common
from .paragraphs import PIECE_SPLIT

VERIFIER_ID = "l1-exists-v2"
VERDICTS = ("PASS", "MISS")
GRADES = ("exact", "strict", "loose", "gapped")
ALL_GRADES = GRADES + ("MISS",)


class L1Error(RuntimeError):
    pass


class Variant:
    """One text variant with its normalized forms, built on first use."""

    def __init__(self, name: str, text: str):
        self.name, self.text = name, text

    @functools.cached_property
    def exact(self) -> nz.Normalized:
        return nz.Normalized(self.text, tuple(range(len(self.text))))

    @functools.cached_property
    def strict(self) -> nz.Normalized:
        return nz.strict(self.text)

    @functools.cached_property
    def loose(self) -> nz.Normalized:
        return nz.loose(self.text)

    def form(self, grade: str) -> nz.Normalized:
        return self.loose if grade == "gapped" else getattr(self, grade)


def _needles(quote: str, grade: str) -> list[str]:
    out = []
    for piece in PIECE_SPLIT.split(quote):
        piece = piece.strip()
        if not nz.loose(piece).text:
            continue
        if grade == "exact":
            out.append(piece)
        elif grade == "strict":
            out.append(nz.strict_needle(piece))
        else:
            out.append(nz.loose(piece).text)
    return [n for n in out if n]


def _runs(hay: nz.Normalized, needle: str, start: int,
          g: nz.Gapped) -> tuple[int, int] | None:
    """Match needle at or after start as at most g.max_runs runs with bounded gaps.

    Each run is the longest prefix of the rest of the needle found in the allowed
    window (anywhere for the first run, within g.max_gap_chars original characters
    of the previous run otherwise). A run shorter than g.min_run fails the match,
    unless the whole needle is that short.
    """
    min_run = min(g.min_run, len(needle))
    i, pos, first = 0, start, None
    for _ in range(g.max_runs):
        if first is None:
            limit = len(hay.text)
        else:
            reach = hay.index[pos - 1] + 1 + g.max_gap_chars
            limit = bisect.bisect_right(hay.index, reach)
        lo, hi, at = 0, len(needle) - i, -1
        while lo < hi:
            m = (lo + hi + 1) // 2
            hit = hay.text.find(needle[i:i + m], pos, limit + m)
            if hit >= 0:
                lo, at = m, hit
            else:
                hi = m - 1
        if lo < min_run:
            return None
        at = hay.text.find(needle[i:i + lo], pos, limit + lo)
        first = at if first is None else first
        i, pos = i + lo, at + lo
        if i == len(needle):
            return first, pos
    return None


def _gapped_embed(hay: nz.Normalized, needles: list[str], g: nz.Gapped) -> tuple[int, int] | None:
    start, first = 0, None
    for needle in needles:
        hit = _runs(hay, needle, start, g)
        if hit is None:
            return None
        first = hit[0] if first is None else first
        start = hit[1]
    return first, start


def _embed(hay: nz.Normalized, needles: list[str], exact: bool) -> tuple[int, int] | None:
    """Shortest in-order embedding of the needles: try each occurrence of the first."""
    best = None
    first = nz.find(hay, needles[0], 0, not exact)
    while first is not None:
        end, ok = first[1], True
        for needle in needles[1:]:
            hit = nz.find(hay, needle, end, not exact)
            if hit is None:
                ok = False
                break
            end = hit[1]
        if not ok:
            break  # later occurrences of the first piece cannot do better
        if best is None or end - first[0] < best[1] - best[0]:
            best = (first[0], end)
        first = nz.find(hay, needles[0], first[0] + 1, not exact)
    return best


@dataclasses.dataclass(frozen=True)
class Result:
    grade: str
    variant: str | None
    char_start: int | None
    char_end: int | None
    per_variant: dict


def grade_in(quote: str, variant: Variant) -> tuple[str, tuple[int, int] | None]:
    for grade in GRADES:
        needles = _needles(quote, grade)
        if not needles:
            return "MISS", None
        if grade == "gapped":
            hit = _gapped_embed(variant.form(grade), needles, nz.load().gapped)
        else:
            hit = _embed(variant.form(grade), needles, grade == "exact")
        if hit is not None:
            return grade, variant.form(grade).span(*hit)
    return "MISS", None


def check_quote(quote: str, variants: list[Variant]) -> Result:
    """Best grade over the variants; ties go to the earlier variant."""
    per_variant: dict[str, str] = {}
    best: Result | None = None
    for v in variants:
        grade, span = grade_in(quote, v)
        per_variant[v.name] = grade
        if span is not None and (best is None or GRADES.index(grade) < GRADES.index(best.grade)):
            best = Result(grade, v.name, span[0], span[1], per_variant)
    if best is None:
        return Result("MISS", None, None, None, per_variant)
    return dataclasses.replace(best, per_variant=per_variant)


def extractor_set(row_id: str, tautological: int) -> str:
    return "codex" if tautological else row_id.split(":", 1)[0]


@dataclasses.dataclass
class Summary:
    paper_id: str
    run_id: str
    protocol_ver: str
    pass_grades: list[str]
    variants: list[str]
    unavailable: list[str]
    grades: dict            # extractor set -> grade -> rows (best over variants)
    per_variant: dict       # variant -> extractor set -> grade -> rows
    verdicts: dict
    rows: list[dict]


def load_variants(conn: sqlite3.Connection, root: pathlib.Path, paper_id: str,
                  names: list[str] | None = None) -> tuple[list[Variant], list[str]]:
    """Variants registered for the paper, refusing any text changed since registration."""
    row = conn.execute("select variants_json from papers where paper_id=?", (paper_id,)).fetchone()
    if row is None:
        raise L1Error(f"{paper_id}: not in the ledger; import its records first")
    registered = json.loads(row[0])
    unknown = [n for n in names or [] if n not in registered]
    if unknown:
        raise L1Error(f"unknown variant {', '.join(unknown)} (known: {', '.join(registered)})")
    paths = common.variant_paths(root, paper_id)
    variants, unavailable = [], []
    for name in paths:
        if names and name not in names:
            continue
        if registered.get(name) == "unavailable":
            unavailable.append(name)
            continue
        if paths[name] is None:
            raise L1Error(f"{paper_id}: variant {name} registered but missing under {root}")
        text = paths[name].read_text(errors="replace")
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != registered[name]:
            raise L1Error(f"{paper_id}: {name} text changed since registration")
        variants.append(Variant(name, text))
    return variants, unavailable


def _variants_sha(conn: sqlite3.Connection, paper_id: str) -> str:
    row = conn.execute("select variants_json from papers where paper_id=?", (paper_id,)).fetchone()
    return hashlib.sha256(row[0].encode("utf-8")).hexdigest()


def run(conn: sqlite3.Connection, root: pathlib.Path, paper_id: str,
        names: list[str] | None = None) -> Summary:
    guard = thresholds.begin(conn)
    pass_grades = list(guard.data["l1_pass_grades"])
    protocol_ver = str(guard.data["protocol_ver"])
    variants, unavailable = load_variants(conn, root, paper_id, names)
    cfg = nz.load()
    claims = conn.execute("select row_id, quote, l1_tautological from claims where paper_id=?"
                          " and status='row' order by row_id", (paper_id,)).fetchall()
    stamp = ledger.now()
    seq = conn.execute("select count(*) from runs where run_kind='l1'").fetchone()[0] + 1
    run_id = f"l1-{paper_id}-{seq:03d}"
    grades = collections.defaultdict(lambda: dict.fromkeys(ALL_GRADES, 0))
    per_variant = {v.name: collections.defaultdict(lambda: dict.fromkeys(ALL_GRADES, 0))
                   for v in variants}
    verdicts: collections.Counter = collections.Counter()
    rows = []
    results = []
    for row_id, quote, taut in claims:
        res = check_quote(quote, variants)
        verdict = "PASS" if res.grade in pass_grades else "MISS"
        group = extractor_set(row_id, taut)
        grades[group][res.grade] += 1
        for name, g in res.per_variant.items():
            per_variant[name][group][g] += 1
        verdicts[verdict] += 1
        detail = dict(res.per_variant, **dict.fromkeys(unavailable, "unavailable"))
        span = (res.variant, res.char_start, res.char_end) if verdict == "PASS" else (None,) * 3
        results.append((row_id, verdict, res.grade, *span, taut,
                        json.dumps({"per_variant": detail}, sort_keys=True)))
        rows.append({"row_id": row_id, "verdict": verdict, "grade": res.grade,
                     "matched_variant": span[0], "char_start": span[1], "char_end": span[2],
                     "l1_tautological": taut})
    guard.check()
    with conn:
        conn.execute("BEGIN")
        conn.execute(
            "insert into runs(run_id, run_kind, input_sha256, thresholds_sha256, protocol_ver,"
            " meta_json, created_at) values (?,?,?,?,?,?,?)",
            (run_id, "l1", _variants_sha(conn, paper_id), guard.sha, protocol_ver,
             json.dumps({"paper_id": paper_id, "variants": [v.name for v in variants],
                         "unavailable": unavailable, "pass_grades": pass_grades,
                         "normalization_sha256": cfg.sha256}), stamp))
        conn.executemany(
            "insert into checks(row_id, layer, verifier_id, protocol_ver, run_id, verdict, grade,"
            " matched_variant, char_start, char_end, l1_tautological, detail_json)"
            " values (?, 'l1', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(r[0], VERIFIER_ID, protocol_ver, run_id, *r[1:]) for r in results])
    return Summary(paper_id, run_id, protocol_ver, pass_grades, [v.name for v in variants],
                   unavailable, {k: dict(v) for k, v in grades.items()},
                   {k: {g: dict(c) for g, c in v.items()} for k, v in per_variant.items()},
                   dict(verdicts), rows)


def waived_refs(conn: sqlite3.Connection, paper_id: str) -> set[str]:
    return {r for (r,) in conn.execute("select row_ref from waivers where paper_id=?", (paper_id,))}


def format_summary(s: Summary, waived: set[str], report_variants: bool) -> str:
    sets = sorted(s.grades, key=lambda k: (k == "codex", k))
    label = {k: ("codex (l1_tautological=1)" if k == "codex" else k) for k in sets}
    head = "\t" + "\t".join(ALL_GRADES)
    lines = [f"l1 {s.paper_id} run {s.run_id}",
             f"verifier: {VERIFIER_ID}, protocol: {s.protocol_ver},"
             f" pass grades: {', '.join(s.pass_grades)}",
             "variants: " + ", ".join(s.variants)
             + "".join(f"; {u}: unavailable" for u in s.unavailable)]
    if report_variants:
        lines.append("per variant (rows at each grade in that variant alone):")
        lines.append("  variant\tset\trows" + head)
        for name in s.variants:
            for k in sets:
                c = s.per_variant[name].get(k, dict.fromkeys(ALL_GRADES, 0))
                lines.append(f"  {name}\t{label[k]}\t{sum(c.values())}\t"
                             + "\t".join(str(c[g]) for g in ALL_GRADES))
    lines.append("grade distribution (best over variants):")
    lines.append("  set\trows" + head + "\tPASS")
    for k in sets:
        c = s.grades[k]
        passed = sum(c[g] for g in s.pass_grades)
        lines.append(f"  {label[k]}\t{sum(c.values())}\t" + "\t".join(str(c[g]) for g in ALL_GRADES)
                     + f"\t{passed}/{sum(c.values())}")
    lines.append(f"verdict: PASS {s.verdicts.get('PASS', 0)}, MISS {s.verdicts.get('MISS', 0)}")
    refs = {r["row_id"].split(":", 1)[1] for r in s.rows if r["row_id"].startswith("claude:")}
    lines.append(f"waived (waivers table, not a verdict): {len(refs & waived)}")
    lines.append("rows:")
    lines.append("row_id\tverdict\tgrade\tmatched_variant\tchar_start\tchar_end\twaived")
    for r in s.rows:
        ref = r["row_id"].split(":", 1)[1]
        cells = [r["row_id"], r["verdict"], r["grade"], r["matched_variant"], r["char_start"],
                 r["char_end"], "yes" if r["row_id"].startswith("claude:") and ref in waived else "-"]
        lines.append("\t".join("NULL" if c is None else str(c) for c in cells))
    return "\n".join(lines)
