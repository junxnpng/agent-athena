"""Schema and tag check (L2) of every L1-passed row.

A row passes when its five condition keys are present (a value may be "none"),
every number carries value / unit / definition / derived_from, its kind is one of
the three tags, a comparison names its baseline, and its claim_text is not more
certain than its quote. Any failure quarantines the row with reason codes, and a
quarantined row is not comparable (`comparable: 0`). Nothing is filled in.

The quarantine rate is an input diagnostic: neither v1 record set carries the
five condition keys, so its prior expectation is 100%.
"""
from __future__ import annotations

import collections
import dataclasses
import json
import pathlib
import re
import sqlite3


from . import ledger, schema, thresholds
from .l1_exists import extractor_set
from .paths import CONFIG_DIR, sha256_file

VERIFIER_ID = "l2-schema-v1"
VERDICTS = ("pass", "quarantine")
MODALITY_PATH = CONFIG_DIR / "modality.json"
COMPARISON_PATH = CONFIG_DIR / "comparison.json"
LEVELS = ("hedged", "plain", "universal")
DIAGNOSTIC_LABEL = "input diagnostic, prior expectation 100%"


class Lexicon:
    """English markers as whole words, Korean markers as substrings."""

    def __init__(self, en: list[str], ko: list[str]):
        self.en = [re.compile(r"(?<![a-z])" + re.escape(w.lower()) + r"(?![a-z])") for w in en]
        self.ko = list(ko)

    def hit(self, text: str) -> bool:
        low = (text or "").lower()
        return any(p.search(low) for p in self.en) or any(w in low for w in self.ko)


class Modality:
    def __init__(self, cfg: dict):
        self.version = cfg["version"]
        self.hedge = Lexicon(cfg["hedge"]["en"], cfg["hedge"]["ko"])
        self.universal = Lexicon(cfg["universal"]["en"], cfg["universal"]["ko"])

    @classmethod
    def load(cls, path: pathlib.Path = MODALITY_PATH) -> "Modality":
        return cls(json.loads(pathlib.Path(path).read_text(encoding="utf-8")))

    def level(self, text: str) -> str:
        if self.hedge.hit(text):
            return "hedged"
        return "universal" if self.universal.hit(text) else "plain"

    def raised(self, quote: str, claim: str) -> bool:
        return LEVELS.index(self.level(claim)) > LEVELS.index(self.level(quote))


def load_comparison(path: pathlib.Path = COMPARISON_PATH) -> Lexicon:
    cfg = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    return Lexicon(cfg["en"], cfg["ko"])


def contract_record(row: sqlite3.Row) -> dict:
    """The row as an evidence record: ledger columns over the converter's item."""
    rec = json.loads(row["record_json"])
    rec.update(quote=row["quote"], claim_text=row["claim_text"], kind=row["kind"],
               conditions=json.loads(row["conditions_json"] or "{}"),
               numbers=json.loads(row["numbers_json"] or "[]"))
    return rec


def check_row(row: sqlite3.Row, modality: Modality, comparison: Lexicon) -> dict:
    rec = contract_record(row)
    res = schema.validate(rec)
    reasons, details = list(res.reasons), list(res.details)
    cond = rec["conditions"] if isinstance(rec["conditions"], dict) else {}
    if (cond.get("baseline") == schema.NONE_VALUE
            and (comparison.hit(rec["quote"]) or comparison.hit(rec["claim_text"]))):
        reasons.append("comparison_without_baseline")
        details.append("conditions.baseline")
    levels = {"quote": modality.level(rec["quote"]), "claim": modality.level(rec["claim_text"])}
    if LEVELS.index(levels["claim"]) > LEVELS.index(levels["quote"]):
        reasons.append("modality_raised")
        details.append("claim_text")
    verdict = "quarantine" if reasons else "pass"
    return {"row_id": row["row_id"], "set": extractor_set(row["row_id"], row["l1_tautological"]),
            "verdict": verdict, "reasons": reasons, "details": details,
            "comparable": int(verdict == "pass"), "modality": levels}


@dataclasses.dataclass
class Summary:
    paper_id: str
    run_id: str
    protocol_ver: str
    rows: list[dict]
    verdicts: dict
    reasons: collections.Counter
    by_set: dict            # extractor set -> (quarantined, rows)

    @property
    def quarantine_rate(self) -> float | None:
        return self.verdicts["quarantine"] / len(self.rows) if self.rows else None


def run(conn: sqlite3.Connection, paper_id: str) -> Summary:
    guard = thresholds.begin(conn)
    protocol_ver = str(guard.data["protocol_ver"])
    modality, comparison = Modality.load(), load_comparison()
    results = [check_row(r, modality, comparison) for r in ledger.l1_passed(conn, paper_id)]
    verdicts = dict.fromkeys(VERDICTS, 0)
    reasons: collections.Counter = collections.Counter()
    by_set: dict = collections.defaultdict(lambda: [0, 0])
    for r in results:
        verdicts[r["verdict"]] += 1
        reasons.update(r["reasons"])
        by_set[r["set"]][0] += r["verdict"] == "quarantine"
        by_set[r["set"]][1] += 1
    stamp = ledger.now()
    seq = conn.execute("select count(*) from runs where run_kind='l2'").fetchone()[0] + 1
    run_id = f"l2-{paper_id}-{seq:03d}"
    s = Summary(paper_id, run_id, protocol_ver, results, verdicts, reasons,
                {k: tuple(v) for k, v in sorted(by_set.items(), key=lambda kv: (kv[0] == "codex", kv[0]))})
    guard.check()
    with conn:
        conn.execute("BEGIN")
        conn.execute(
            "insert into runs(run_id, run_kind, thresholds_sha256, protocol_ver, meta_json,"
            " created_at) values (?,?,?,?,?,?)",
            (run_id, "l2", guard.sha, protocol_ver,
             json.dumps({"paper_id": paper_id, "verifier_id": VERIFIER_ID, "rows": len(results),
                         **verdicts, "quarantine_rate": s.quarantine_rate,
                         "reasons": dict(sorted(reasons.items())), "by_set": s.by_set,
                         "modality_sha256": sha256_file(MODALITY_PATH),
                         "comparison_sha256": sha256_file(COMPARISON_PATH)}), stamp))
        conn.executemany(
            "insert into checks(row_id, layer, verifier_id, protocol_ver, run_id, verdict,"
            " reason_code, l1_tautological, detail_json) values (?, 'l2', ?, ?, ?, ?, ?, ?, ?)",
            [(r["row_id"], VERIFIER_ID, protocol_ver, run_id, r["verdict"],
              ",".join(r["reasons"]) or None, int(r["set"] == "codex"),
              json.dumps({k: r[k] for k in ("details", "comparable", "modality")}))
             for r in results])
    return s


def format_rate(quarantined: int, rows: int) -> str:
    rate = f"{quarantined / rows:.3f}" if rows else "n/a"
    return f"quarantine_rate: {rate} ({quarantined}/{rows}) — {DIAGNOSTIC_LABEL}"


def format_summary(s: Summary) -> str:
    lines = [f"l2 {s.paper_id} run {s.run_id}",
             f"verifier: {VERIFIER_ID}, protocol: {s.protocol_ver}",
             f"rows: {len(s.rows)} (L1-passed rows only)",
             f"verdict: pass {s.verdicts['pass']}, quarantine {s.verdicts['quarantine']}",
             format_rate(s.verdicts["quarantine"], len(s.rows)),
             "  by set: " + ", ".join(f"{k} {q}/{n}" for k, (q, n) in s.by_set.items()),
             "reason codes (a row may carry several):"]
    lines += [f"  {code}: {n}" for code, n in sorted(s.reasons.items())] or ["  none"]
    lines += ["rows:", "row_id\tverdict\treasons\tmodality(quote>claim)"]
    for r in s.rows:
        lines.append(f"{r['row_id']}\t{r['verdict']}\t{','.join(r['reasons']) or '-'}"
                     f"\t{r['modality']['quote']}>{r['modality']['claim']}")
    return "\n".join(lines)
