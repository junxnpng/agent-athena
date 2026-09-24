"""Arithmetic check (L6) of every L1-passed row.

Four parts:
- derived_from: a contract number whose `derived_from` is an expression is
  recomputed and compared with its value at the value's printed precision. An
  arithmetic mean of ratios is flagged (the mean of ratios is geometric). v1
  rows carry no derived_from pointer, so this part reports `applicable_rows: 0`.
- free number strings: every number and unit is parsed, `a / b ≈ c` arithmetic
  inside a string is recomputed, and markers of unreported values and of the
  extractor's own arithmetic are counted.
- intra_doc_conflict: keyed values (`P99 ≈ 15분`) of two different records of
  the same paper that disagree beyond printed precision after unit conversion.
- Codex fragments: the fragment's sha256 in the source record against its text,
  and its presence in the raw and layout texts (a port of the old
  codex_verify_metric_sources check).
A row with any finding is `flag` with reason codes, otherwise `pass`.
"""
from __future__ import annotations

import ast
import dataclasses
import hashlib
import itertools
import json
import math
import pathlib
import re
import sqlite3


from . import ledger, normalize as nz, thresholds
from .convert import common
from .l1_exists import load_variants
from .paths import CONFIG_DIR, sha256_file

VERIFIER_ID = "l6-arith-v1"
VERDICTS = ("pass", "flag")
NUMBERS_PATH = CONFIG_DIR / "numbers.json"
FRAGMENT_VARIANTS = ("codex_raw", "codex_layout")

_NUM = r"\d{1,3}(?:,\d{3})+(?!\d)|\d+(?:\.\d+)?"
_SUPERSCRIPT = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")
_THOUSANDS = re.compile(r"(?<![\d.])\d{1,3}(?:,\d{3})+(?![\d,])")
_INLINE = re.compile(rf"(?<![\w.,])({_NUM})\s*([/×*÷+])\s*({_NUM})\s*(?:≈|=)\s*(?:약\s*|~\s*)?({_NUM})")
_KEY = re.compile(r"(?<![\w.\-])([A-Za-z][\w.\-]*|[가-힣]+)\s*(?:=|≈)\s*(?:약\s*|~\s*)?")
_AFTER_KEYED = re.compile(r"\s*[/×*÷+]\s*\d|/\d")
_RANGE_DASH = re.compile(r"\s*[–\-~]\s*~?\s*")


class L6Error(RuntimeError):
    pass


def _decimals(text: str) -> int:
    return len(text.split(".", 1)[1]) if "." in text else 0


def _plain(text: str) -> float:
    return float(text.replace(",", ""))


def _strip_thousands(text: str) -> str:
    return _THOUSANDS.sub(lambda m: m.group(0).replace(",", ""), text)


# --- derived_from ---------------------------------------------------------

def _mean(*xs: float) -> float:
    return sum(xs) / len(xs)


def _geomean(*xs: float) -> float:
    if any(x <= 0 for x in xs):
        raise ValueError("geomean of a non-positive value")
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


FUNCTIONS = {
    "ratio": lambda a, b: a / b,
    "pct_change": lambda old, new: (new - old) / old * 100,
    "mean": _mean,
    "geomean": _geomean,
}
_BINOPS = {ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b,
           ast.Mult: lambda a, b: a * b, ast.Div: lambda a, b: a / b,
           ast.Pow: lambda a, b: a ** b}


class _Unparseable(Exception):
    pass


def _eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        return _BINOPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        value = _eval(node.operand)
        return -value if isinstance(node.op, ast.USub) else value
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id in FUNCTIONS and not node.keywords and node.args):
        return FUNCTIONS[node.func.id](*(_eval(a) for a in node.args))
    raise _Unparseable(ast.dump(node)[:60])


def _ratio_mean(tree: ast.AST) -> bool:
    return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "mean"
               and any(isinstance(a, ast.Call) and isinstance(a.func, ast.Name)
                       and a.func.id == "ratio" for a in n.args)
               for n in ast.walk(tree))


@dataclasses.dataclass(frozen=True)
class Recompute:
    status: str                 # consistent | mismatch | unparseable
    computed: float | None
    reasons: list


def recompute(value: str, expr: str) -> Recompute:
    """Evaluate a derived_from expression and compare it with the printed value.

    The expression takes numbers, + - * / **, parentheses and the functions
    ratio, pct_change, mean and geomean; thousands separators are dropped, so
    function arguments are separated by a comma and a space.
    """
    m = re.search(r"[-+]?\d+(?:\.\d+)?", _strip_thousands(str(value)))
    try:
        if m is None:
            raise _Unparseable("value")
        tree = ast.parse(_strip_thousands(expr), mode="eval")
        computed = _eval(tree)
    except (_Unparseable, SyntaxError, ArithmeticError, ValueError, TypeError):
        return Recompute("unparseable", None, [])
    target = float(m.group(0))
    tol = 0.5 * 10 ** -_decimals(m.group(0).lstrip("+-")) + 1e-12 * abs(target)
    status = "consistent" if abs(computed - target) <= tol else "mismatch"
    return Recompute(status, computed, ["ratio_arithmetic_mean"] if _ratio_mean(tree) else [])


# --- free number strings --------------------------------------------------

@dataclasses.dataclass(frozen=True)
class Value:
    text: str                   # the number as printed, with its unit
    value: float                # converted to the dimension's base
    dim: str | None
    tol: float                  # half a unit of the last printed digit, in the base


@dataclasses.dataclass(frozen=True)
class Keyed:
    key: str
    text: str
    value: float
    dim: str | None
    tol: float


class Numbers:
    def __init__(self, cfg: dict):
        self.version = cfg["version"]
        self.units = {u: (d, float(f)) for u, (d, f) in cfg["units"].items()}
        self.multipliers = {k: float(v) for k, v in cfg["multipliers"].items()}
        self.markers = {k: list(v) for k, v in cfg["markers"].items()}
        alts = []
        for u in sorted(self.units, key=len, reverse=True):
            tail = r"(?![A-Za-z])" if re.match(r"[A-Za-z]", u) else ""
            alts.append(re.escape(u) + tail)
        mult = "".join(re.escape(k) for k in self.multipliers)
        self.number = re.compile(
            rf"(?<![\w.])(?P<num>{_NUM})(?P<sup>[⁻⁰¹²³⁴⁵⁶⁷⁸⁹]+)?(?P<mult>[{mult}](?![A-Za-z]))?"
            rf"(?:\s*(?P<unit>{'|'.join(alts)}))?")

    @classmethod
    def load(cls, path: pathlib.Path = NUMBERS_PATH) -> "Numbers":
        return cls(json.loads(pathlib.Path(path).read_text(encoding="utf-8")))

    def _value(self, m: re.Match, inherit: tuple | None = None) -> Value:
        num = m.group("num")
        base = _plain(num)
        tol = 0.5 * 10 ** -_decimals(num)
        if m.group("sup"):
            base = base ** int(m.group("sup").translate(_SUPERSCRIPT))
            tol = 0.0
        factor = self.multipliers.get(m.group("mult") or "", 1.0)
        dim, unit_factor = self.units.get(m.group("unit") or "", (None, 1.0))
        if m.group("unit") is None and inherit is not None:
            dim, unit_factor = inherit
        scale = factor * unit_factor
        return Value(m.group(0), base * scale, dim, tol * scale)

    def parse(self, text: str) -> list[Value]:
        """Every number of a string; the first number of a range takes the second's unit."""
        matches = list(self.number.finditer(text or ""))
        out = []
        for i, m in enumerate(matches):
            inherit = None
            nxt = matches[i + 1] if i + 1 < len(matches) else None
            if (nxt is not None and m.group("unit") is None and m.group("mult") is None
                    and nxt.group("unit") and _RANGE_DASH.fullmatch(text[m.end():nxt.start()])):
                inherit = self.units[nxt.group("unit")]
            out.append(self._value(m, inherit))
        return out

    def keyed(self, text: str) -> list[Keyed]:
        """`key = value` and `key ≈ value` pairs; lists and arithmetic operands are skipped."""
        out = []
        for k in _KEY.finditer(text or ""):
            m = self.number.match(text, k.end())
            if m is None or _AFTER_KEYED.match(text, m.end()):
                continue
            v = self._value(m)
            out.append(Keyed(k.group(1).lower(), v.text.strip(), v.value, v.dim, v.tol))
        return out

    def inline(self, text: str) -> list[dict]:
        """`a op b ≈ c` inside a string, recomputed at c's printed precision."""
        out = []
        for m in _INLINE.finditer(text or ""):
            a, op, b, c = _plain(m.group(1)), m.group(2), _plain(m.group(3)), m.group(4)
            got = a + b if op == "+" else a * b if op in "×*" else a / b if b else math.inf
            ok = abs(got - _plain(c)) <= 0.5 * 10 ** -_decimals(c) + 1e-12 * abs(got)
            out.append({"text": m.group(0), "computed": got, "consistent": ok})
        return out

    def marked(self, text: str, marker: str) -> bool:
        return any(w in (text or "") for w in self.markers[marker])


def number_strings(numbers: list) -> list[str]:
    out = []
    for item in numbers:
        if isinstance(item, dict):
            if item.get("raw"):
                out.append(str(item["raw"]))
            elif item.get("value") is not None:
                out.append(f"{item['value']} {item.get('unit', '')}".strip())
        elif str(item).strip():
            out.append(str(item))
    return out


def _derived(numbers: list) -> list[dict]:
    return [n for n in numbers if isinstance(n, dict)
            and str(n.get("derived_from") or "").strip() not in ("", "none")]


# --- Codex fragments ------------------------------------------------------

def _fragment_checks(conn, root: pathlib.Path, paper_id: str, rows: list) -> dict[str, dict]:
    codex = [r for r in rows if r["extractor_id"] == "codex"]
    if not codex:
        return {}
    _, _, records = common.load_records(root, "codex", paper_id)
    by_id = {r["id"]: r for r in records}
    registered = json.loads(conn.execute("select variants_json from papers where paper_id=?",
                                         (paper_id,)).fetchone()[0])
    variants, _ = load_variants(conn, root, paper_id,
                                [v for v in FRAGMENT_VARIANTS if v in registered])
    texts = {v.name: nz.loose(v.text).text for v in variants}
    out = {}
    for r in codex:
        rec = by_id.get(r["record_id"])
        if rec is None:
            raise L6Error(f"{r['row_id']}: record {r['record_id']} is not in the Codex source")
        frag_id = json.loads(r["record_json"])["locator"].get("fragment_id")
        frag = next((f for f in rec.get("fragments", []) if f["id"] == frag_id), None)
        if frag is None:
            raise L6Error(f"{r['row_id']}: fragment {frag_id} is not in record {r['record_id']}")
        sha_ok = (hashlib.sha256(frag["text"].encode()).hexdigest() == frag.get("sha256")
                  and frag["text"] == r["quote"])
        needle = nz.loose(r["quote"]).text
        present = {v: bool(needle) and needle in texts.get(v, "") for v in FRAGMENT_VARIANTS}
        out[r["row_id"]] = {"fragment_id": frag_id, "sha256_ok": sha_ok, **present}
    return out


# --- run ------------------------------------------------------------------

@dataclasses.dataclass
class Summary:
    paper_id: str
    run_id: str
    protocol_ver: str
    rows: list[dict]
    derived: dict
    numbers: dict
    inline: dict
    conflicts: list[dict]
    keyed_values: int
    fragments: dict | None
    verdicts: dict


def run(conn: sqlite3.Connection, root: pathlib.Path | None, paper_id: str) -> Summary:
    """Check every L1-passed row; the Codex fragment part needs the source root."""
    guard = thresholds.begin(conn)
    protocol_ver = str(guard.data["protocol_ver"])
    nums = Numbers.load()
    rows = ledger.l1_passed(conn, paper_id)
    reasons: dict[str, list[str]] = {r["row_id"]: [] for r in rows}
    details: dict[str, dict] = {r["row_id"]: {} for r in rows}

    def flag(row_id: str, code: str) -> None:
        if code not in reasons[row_id]:
            reasons[row_id].append(code)

    derived = {"rows": len(rows), "applicable_rows": 0, "numbers": 0, "consistent": 0,
               "mismatch": 0, "unparseable": 0, "ratio_arithmetic_mean": 0}
    counts = {"rows_with_numbers": 0, "rows_parsed": 0, "values": 0, "unreported": 0,
              "extractor_arithmetic": 0}
    inline = {"found": 0, "consistent": 0, "mismatch": 0}
    keyed: dict[str, list[Keyed]] = {}
    for r in rows:
        rid, numbers = r["row_id"], json.loads(r["numbers_json"] or "[]")
        applicable = _derived(numbers)
        if applicable:
            derived["applicable_rows"] += 1
            results = []
            for n in applicable:
                res = recompute(str(n.get("value", "")), str(n["derived_from"]))
                derived["numbers"] += 1
                derived[res.status] += 1
                derived["ratio_arithmetic_mean"] += bool(res.reasons)
                if res.status != "consistent":
                    flag(rid, f"derived_from_{res.status}")
                for code in res.reasons:
                    flag(rid, code)
                results.append({"derived_from": n["derived_from"], "value": n.get("value"),
                                "status": res.status, "computed": res.computed})
            details[rid]["derived_from"] = results
        strings = number_strings(numbers)
        values = [v for s in strings for v in nums.parse(s)]
        counts["rows_with_numbers"] += bool(strings)
        counts["rows_parsed"] += bool(values)
        counts["values"] += len(values)
        counts["unreported"] += any(nums.marked(s, "unreported") for s in strings)
        counts["extractor_arithmetic"] += any(nums.marked(s, "extractor_arithmetic") for s in strings)
        found = [x for s in strings for x in nums.inline(s)]
        for x in found:
            inline["found"] += 1
            inline["consistent" if x["consistent"] else "mismatch"] += 1
            if not x["consistent"]:
                flag(rid, "inline_arith_mismatch")
        keyed[rid] = [k for s in strings for k in nums.keyed(s)]
        details[rid].update(values=len(values), inline=found,
                            keyed=[f"{k.key}={k.text}" for k in keyed[rid]])

    record = {r["row_id"]: (r["extractor_id"], r["record_id"]) for r in rows}
    conflicts = []
    for a, b in itertools.combinations(sorted(keyed), 2):
        if record[a] == record[b]:
            continue
        for ka, kb in itertools.product(keyed[a], keyed[b]):
            if (ka.key == kb.key and ka.dim == kb.dim
                    and abs(ka.value - kb.value) > max(ka.tol, kb.tol)):
                pair = {"key": ka.key, "rows": [a, b], "values": [ka.text, kb.text]}
                if pair not in conflicts:
                    conflicts.append(pair)
                    flag(a, "intra_doc_conflict")
                    flag(b, "intra_doc_conflict")

    fragments = None
    if root is not None:
        checks = _fragment_checks(conn, root, paper_id, rows)
        fragments = {"rows": len(checks),
                     "sha256_ok": sum(c["sha256_ok"] for c in checks.values()),
                     **{f"in_{v}": sum(c[v] for c in checks.values()) for v in FRAGMENT_VARIANTS},
                     "in_neither": sum(not any(c[v] for v in FRAGMENT_VARIANTS)
                                       for c in checks.values())}
        for rid, c in checks.items():
            details[rid]["fragment"] = c
            if not c["sha256_ok"]:
                flag(rid, "fragment_sha_mismatch")
            if not any(c[v] for v in FRAGMENT_VARIANTS):
                flag(rid, "fragment_not_in_text")

    out_rows = [{"row_id": r["row_id"], "verdict": "flag" if reasons[r["row_id"]] else "pass",
                 "reasons": reasons[r["row_id"]], "detail": details[r["row_id"]],
                 "l1_tautological": r["l1_tautological"]} for r in rows]
    verdicts = dict.fromkeys(VERDICTS, 0)
    for r in out_rows:
        verdicts[r["verdict"]] += 1
    stamp = ledger.now()
    seq = conn.execute("select count(*) from runs where run_kind='l6'").fetchone()[0] + 1
    run_id = f"l6-{paper_id}-{seq:03d}"
    s = Summary(paper_id, run_id, protocol_ver, out_rows, derived, counts, inline, conflicts,
                sum(len(v) for v in keyed.values()), fragments, verdicts)
    guard.check()
    with conn:
        conn.execute("BEGIN")
        conn.execute(
            "insert into runs(run_id, run_kind, thresholds_sha256, protocol_ver, meta_json,"
            " created_at) values (?,?,?,?,?,?)",
            (run_id, "l6", guard.sha, protocol_ver,
             json.dumps({"paper_id": paper_id, "verifier_id": VERIFIER_ID, "rows": len(rows),
                         "derived_from": derived, "numbers": counts, "inline": inline,
                         "conflict_pairs": len(conflicts), "conflicts": conflicts,
                         "keyed_values": s.keyed_values, "fragments": fragments,
                         "verdicts": verdicts, "numbers_sha256": sha256_file(NUMBERS_PATH)},
                        ensure_ascii=False), stamp))
        conn.executemany(
            "insert into checks(row_id, layer, verifier_id, protocol_ver, run_id, verdict,"
            " reason_code, l1_tautological, detail_json) values (?, 'l6', ?, ?, ?, ?, ?, ?, ?)",
            [(r["row_id"], VERIFIER_ID, protocol_ver, run_id, r["verdict"],
              ",".join(r["reasons"]) or None, r["l1_tautological"],
              json.dumps(r["detail"], ensure_ascii=False)) for r in out_rows])
    return s


def format_derived(d: dict) -> str:
    line = f"derived_from: applicable_rows: {d['applicable_rows']} (of {d['rows']} rows)"
    if not d["applicable_rows"]:
        return line + " — no row carries a derived_from pointer"
    return (line + f"; numbers {d['numbers']}: consistent {d['consistent']}, mismatch"
            f" {d['mismatch']}, unparseable {d['unparseable']}, arithmetic mean of ratios"
            f" {d['ratio_arithmetic_mean']}")


def format_fragments(f: dict | None) -> str:
    if f is None:
        return "codex fragments: skipped (no source root)"
    return (f"codex fragments: {f['rows']} rows, sha256 ok {f['sha256_ok']}/{f['rows']},"
            f" in codex_raw {f['in_codex_raw']}/{f['rows']}, in codex_layout"
            f" {f['in_codex_layout']}/{f['rows']}, in neither {f['in_neither']}")


def format_summary(s: Summary) -> str:
    n = s.numbers
    lines = [f"l6 {s.paper_id} run {s.run_id}",
             f"verifier: {VERIFIER_ID}, protocol: {s.protocol_ver}",
             f"rows: {len(s.rows)} (L1-passed rows only)",
             format_derived(s.derived),
             f"numbers (free strings): rows with numbers {n['rows_with_numbers']}/{len(s.rows)},"
             f" rows with parsed values {n['rows_parsed']}, values {n['values']};"
             f" marked unreported {n['unreported']}, marked extractor arithmetic"
             f" {n['extractor_arithmetic']}",
             f"inline arithmetic: found {s.inline['found']}, consistent {s.inline['consistent']},"
             f" mismatch {s.inline['mismatch']}",
             f"intra_doc_conflict: {len(s.conflicts)} pairs ({s.keyed_values} keyed values compared)"]
    lines += [f"  {c['key']}: {c['rows'][0]} {c['values'][0]} vs {c['rows'][1]} {c['values'][1]}"
              for c in s.conflicts]
    lines += [format_fragments(s.fragments),
              f"verdict: pass {s.verdicts['pass']}, flag {s.verdicts['flag']}",
              "rows:", "row_id\tverdict\treasons\tvalues\tkeyed"]
    for r in s.rows:
        d = r["detail"]
        lines.append(f"{r['row_id']}\t{r['verdict']}\t{','.join(r['reasons']) or '-'}"
                     f"\t{d['values']}\t{'; '.join(d['keyed']) or '-'}")
    return "\n".join(lines)
