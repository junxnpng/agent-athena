"""Recall (judgment 3): gold recall, probes and targets, elusion bound, capture-recapture.

Gold recall compares the registered gold sentences with the L1-passed rows of
each extractor set and their union, at three levels: claim_present (a row's
quote covers the sentence), conditions_match (not applicable in v1: G carries no
condition labels) and numbers_match (the covering row records the sentence's
numbers). Probes and a target set are not applicable while the record sets are
frozen. The elusion sample is drawn once, with the registered n and seed, from
the unused-paragraph frame fixed at registration; its exact binomial upper bound
is reported as achievable before review and as observed after. Chapman's
capture-recapture estimate is always labelled a lower bound.
"""
from __future__ import annotations

import csv
import dataclasses
import difflib
import hashlib
import json
import pathlib
import random
import re
import sqlite3


from . import ledger, queries, stats, thresholds
from . import paragraphs as pg
from .convert import gold
from .l1_exists import extractor_set
from .l6_arith import Numbers, Value, number_strings
from .paths import CONFIG_DIR, sha256_file
from .schema import CONDITION_FIELDS

VERIFIER_ID = "recall-v1"
CONFIG_PATH = CONFIG_DIR / "recall.json"
LEVELS = ("claim_present", "conditions_match", "numbers_match")
UNION = "union"
FROZEN = "not-applicable: extractor runs are frozen"
FROZEN_WHY = ("both record sets were extracted before this check existed, so a probe planted now"
              " tests the recall code, not the extractor, and a target set chosen now is drawn"
              " after the run it would measure, while the target method draws it before")
TSV_FIELDS = ("sample_id", "para_id", "seq", "word_count", "missed_claims", "note", "text")
_SUPERSCRIPT = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


class RecallError(RuntimeError):
    pass


@dataclasses.dataclass
class Config:
    data: dict
    sha256: str

    @property
    def version(self) -> str:
        return self.data["version"]


def load_config(path: pathlib.Path = CONFIG_PATH) -> Config:
    return Config(json.loads(pathlib.Path(path).read_text(encoding="utf-8")), sha256_file(path))


# --- matching ----------------------------------------------------------------

def coverage(sentence: str, quote: str, cfg: Config) -> float:
    """Share of the sentence's canonical characters in common runs with the quote."""
    s, q = pg.canon(sentence), pg.canon(quote or "")
    if not s:
        return 0.0
    run = min(int(cfg.data["claim_present"]["min_run_chars"]), len(s))
    blocks = difflib.SequenceMatcher(None, s, q, autojunk=False).get_matching_blocks()
    return sum(b.size for b in blocks if b.size >= run) / len(s)


def covers(sentence: str, quote: str, cfg: Config) -> bool:
    return coverage(sentence, quote, cfg) >= float(cfg.data["claim_present"]["min_cover"])


def _same(a: Value, b: Value) -> bool:
    if a.dim is not None and b.dim is not None and a.dim != b.dim:
        return False
    return abs(a.value - b.value) <= max(a.tol, b.tol) + 1e-9 * max(abs(a.value), abs(b.value))


class Reader:
    """Numbers of gold sentences and of rows, read with the L6 number grammar."""

    def __init__(self, cfg: Config, numbers: Numbers | None = None):
        self.numbers = numbers or Numbers.load()
        self.ignore = [re.compile(p) for p in cfg.data["numbers"]["ignore"]]
        self.power = re.compile(cfg.data["numbers"]["power"])

    def gold(self, sentence: str) -> list[Value]:
        text = sentence
        for pattern in self.ignore:
            text = pattern.sub(" ", text)
        text = self.power.sub(lambda m: m.group(1) + m.group(2).translate(_SUPERSCRIPT), text)
        return self.numbers.parse(text)

    def match(self, wanted: list[Value], strings: list[str]) -> bool:
        if not wanted:
            return False
        have = [v for s in strings for v in self.numbers.parse(s)]
        return all(any(_same(w, h) for h in have) for w in wanted)


# --- gold recall -------------------------------------------------------------

def _set_names(row_set: dict[str, str]) -> list[str]:
    names = set(row_set.values()) | {"claude", "codex"}
    return sorted(names, key=lambda k: (k == "codex", k))


def _table(per: list[dict], row_set: dict[str, str], names: list[str], cond_na: str) -> dict:
    table: dict = {level: {} for level in LEVELS}
    table["conditions_match"] = {"not_applicable": cond_na}
    with_numbers = [p for p in per if p["numbers"]]
    for name in names + [UNION]:
        members = {r for r, s in row_set.items() if name == UNION or s == name}
        for level, key, eligible in (("claim_present", "covered_by", per),
                                     ("numbers_match", "numbers_by", with_numbers)):
            matched_rows = {r for p in per for r in p[key]} & members
            table[level][name] = {
                "recall": [sum(1 for p in eligible if set(p[key]) & members), len(eligible)],
                "precision": [len(matched_rows), len(members)]}
    return table


def _chapman(conn, paper_id: str, rows, row_set: dict[str, str], names: list[str],
             cfg: Config) -> dict:
    frame = {b["para_id"] for b in ledger.frame_blocks(conn, paper_id)}
    sets = {n: {"rows": 0, "blocks": set()} for n in names}
    for r in rows:
        s = sets[row_set[r["row_id"]]]
        s["rows"] += 1
        s["blocks"] |= set(json.loads(r["para_ids_json"] or "[]")) & frame
    present = sorted((n for n in names if sets[n]["rows"]), key=lambda n: -sets[n]["rows"])
    out = {"unit": "frame blocks", "lower_bound": True, "chapman_estimate": None, "skipped": None,
           "sets": {n: {"rows": s["rows"], "blocks": len(s["blocks"])} for n, s in sets.items()},
           "n1": None, "n2": None, "m": None}
    if len(present) < 2:
        out["skipped"] = "single extractor set"
        return out
    big, small = present[0], present[1]
    b1, b2 = sets[big]["blocks"], sets[small]["blocks"]
    out.update(n1=len(b1), n2=len(b2), m=len(b1 & b2), pair=[big, small])
    ratio = sets[small]["rows"] / sets[big]["rows"]
    least = float(cfg.data["capture_recapture"]["min_size_ratio"])
    if ratio < least:
        out["skipped"] = (f"asymmetric sets ({small} {sets[small]['rows']} rows vs {big}"
                          f" {sets[big]['rows']} rows, ratio {ratio:.2f} < min_size_ratio {least})")
        return out
    out["chapman_estimate"] = stats.chapman(out["n1"], out["n2"], out["m"])
    return out


@dataclasses.dataclass
class Summary:
    paper_id: str
    run_id: str
    protocol_ver: str
    query_id: str | None
    config_version: str
    config_sha256: str
    gold_split_count: int
    rows_by_set: dict
    delivered: dict
    table: dict
    sentences: list[dict]
    chapman: dict
    misses: dict

    def meta(self) -> dict:
        return {"verifier_id": VERIFIER_ID, **dataclasses.asdict(self)}

    @classmethod
    def from_meta(cls, meta: dict) -> "Summary":
        return cls(**{f.name: meta[f.name] for f in dataclasses.fields(cls)})


def _locate_misses(conn, paper_id: str, per: list[dict]) -> dict:
    """Where the gold sentences no row covers sit: unused-pool blocks, used blocks, elsewhere."""
    hay = pg.Haystack(ledger.unit_blocks(conn, paper_id))
    ids = dict(zip(hay.seqs, hay.para_ids))
    frame = {b["para_id"] for b in ledger.frame_blocks(conn, paper_id)}
    pool = {b["para_id"] for b in ledger.unused_pool(conn, paper_id)}
    out = {"pool": {}, "used": 0, "off_frame": 0, "unlocated": 0}
    for p in per:
        if p["covered_by"]:
            continue
        blocks = [ids[s] for s in pg.resolve(p["text"], hay)]
        p["blocks"] = blocks
        in_pool = [b for b in blocks if b in pool]
        for b in in_pool:
            out["pool"].setdefault(b, []).append(p["gold_id"])
        if not blocks:
            out["unlocated"] += 1
        elif not in_pool:
            out["used" if any(b in frame for b in blocks) else "off_frame"] += 1
    return out


def gold_floor(s: Summary, e: dict) -> dict | None:
    """Sampled blocks that hold a gold sentence no row covers: a floor on the review's k."""
    if not e.get("sample"):
        return None
    blocks = sorted(set(s.misses["pool"]) & set(e["sample"]["para_ids"]))
    n = e["sample"]["n"]
    return {"k": len(blocks), "blocks": blocks,
            "upper": stats.upper_bound(len(blocks), n, e["confidence"]) if blocks else None}


def _conditions_complete(row) -> bool:
    cond = json.loads(row["conditions_json"] or "{}")
    return all(str(cond.get(f) or "").strip() for f in CONDITION_FIELDS)


def run(conn: sqlite3.Connection, paper_id: str, query_id: str | None = None,
        cfg: Config | None = None) -> Summary:
    guard = thresholds.begin(conn)
    protocol_ver = str(guard.data["protocol_ver"])
    cfg = cfg or load_config()
    if query_id is not None and queries.get(conn, query_id) is None:
        raise RecallError(f"unknown query {query_id}")
    golds = gold.sentences(conn, paper_id)
    greg = gold.registration(conn, paper_id)
    rows = ledger.l1_passed(conn, paper_id)
    row_set = {r["row_id"]: extractor_set(r["row_id"], r["l1_tautological"]) for r in rows}
    names = _set_names(row_set)
    reader = Reader(cfg)
    row_numbers = {r["row_id"]: number_strings(json.loads(r["numbers_json"] or "[]")) for r in rows}
    per = []
    for g in golds:
        covered = [r["row_id"] for r in rows if covers(g["text"], r["quote"], cfg)]
        wanted = reader.gold(g["text"])
        per.append({"gold_id": g["gold_id"], "seq": g["seq"], "text": g["text"],
                    "covered_by": covered, "numbers": [v.text.strip() for v in wanted],
                    "numbers_by": [r for r in covered if reader.match(wanted, row_numbers[r])]})
    complete = sum(1 for r in rows if _conditions_complete(r))
    cond_na = (f"not-applicable: G carries no condition labels (gold rows are sentences),"
               f" and {complete}/{len(rows)} L1-passed rows carry the five condition fields")
    stamp = ledger.now()
    seq = conn.execute("select count(*) from runs where run_kind='recall'").fetchone()[0] + 1
    s = Summary(paper_id, f"recall-{paper_id}-{seq:03d}", protocol_ver, query_id,
                cfg.version, cfg.sha256, len(golds),
                {n: sum(1 for v in row_set.values() if v == n) for n in names},
                ledger.delivered(conn, paper_id), _table(per, row_set, names, cond_na), per,
                _chapman(conn, paper_id, rows, row_set, names, cfg),
                _locate_misses(conn, paper_id, per))
    guard.check()
    meta = {**s.meta(), "gold_run_id": greg["run_id"] if greg else None}
    with conn:
        conn.execute("BEGIN")
        conn.execute(
            "insert into runs(run_id, run_kind, thresholds_sha256, protocol_ver, meta_json,"
            " created_at) values (?,?,?,?,?,?)",
            (s.run_id, "recall", guard.sha, protocol_ver, json.dumps(meta, ensure_ascii=False), stamp))
        conn.executemany(
            "insert into checks(row_id, layer, verifier_id, protocol_ver, run_id, verdict,"
            " detail_json, query_id) values (?, 'recall', ?, ?, ?, ?, ?, ?)",
            [(p["gold_id"], VERIFIER_ID, protocol_ver, s.run_id,
              "present" if p["covered_by"] else "absent",
              json.dumps({k: p[k] for k in ("covered_by", "numbers", "numbers_by")}), query_id)
             for p in per])
    return s


# --- elusion -----------------------------------------------------------------

def draw(pool: list[dict], n: int, seed: int) -> list[dict]:
    """n blocks drawn without replacement by random.Random(seed); independent of pool order."""
    ordered = sorted(pool, key=lambda b: (b["seq"], b["para_id"]))
    return sorted(random.Random(seed).sample(ordered, n), key=lambda b: b["seq"])


def n_for_target(target: float, confidence: float) -> int:
    """Smallest n whose zero-error one-sided upper bound is at most target."""
    n = 1
    while stats.upper_bound(0, n, confidence) > target:
        n += 1
    return n


def _runs_of(conn, kind: str, **meta) -> list[tuple[str, dict, str]]:
    out = []
    for run_id, meta_json, created in conn.execute(
            "select run_id, meta_json, created_at from runs where run_kind=? order by created_at,"
            " run_id", (kind,)):
        m = json.loads(meta_json)
        if all(m.get(k) == v for k, v in meta.items()):
            out.append((run_id, m, created))
    return out


def _sample(conn, paper_id: str) -> dict | None:
    found = _runs_of(conn, "elusion-sample", paper_id=paper_id,
                     extraction_runs=ledger.extraction_runs(conn, paper_id))
    return {**found[0][1], "created_at": found[0][2]} if found else None


def _review(conn, sample_id: str) -> dict | None:
    found = _runs_of(conn, "elusion-review", sample_id=sample_id)
    return found[0][1] if found else None


def export_elusion(conn: sqlite3.Connection, paper_id: str, out: pathlib.Path) -> dict:
    """Draw the registered elusion sample once and write it for review."""
    guard = thresholds.begin(conn)
    n, seed = int(guard.data["elusion_n"]), int(guard.data["sample_seed"])
    old = _sample(conn, paper_id)
    if old is not None:
        raise RecallError(f"resampling forbidden: {paper_id} already has elusion sample"
                          f" {old['sample_id']} for these extraction runs (drawn {old['created_at']},"
                          f" {old['file']}); a registered sample is reviewed, never redrawn")
    pool = ledger.unused_pool(conn, paper_id)
    if len(pool) < n:
        raise RecallError(f"{paper_id}: unused pool {len(pool)} < elusion_n {n}; the registered n"
                          " cannot be drawn from this paper")
    picked = draw(pool, n, seed)
    variant = ledger.paragraph_unit(conn)["variant"]
    texts = ledger.block_texts(conn, paper_id, variant)
    runs = ledger.extraction_runs(conn, paper_id)
    key = json.dumps({"paper_id": paper_id, "extraction_runs": runs,
                      "para_ids": [b["para_id"] for b in picked]})
    sample_id = f"elusion-{paper_id}-{hashlib.sha256(key.encode()).hexdigest()[:12]}"
    out = pathlib.Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(TSV_FIELDS)
        for b in picked:
            text = " ".join(texts[b["para_id"]].split())
            w.writerow([sample_id, b["para_id"], b["seq"], b["word_count"], "", "", text])
    guard.check()
    meta = {"paper_id": paper_id, "sample_id": sample_id, "extraction_runs": runs, "n": n,
            "seed": seed, "unused_pool": len(pool), "para_ids": [b["para_id"] for b in picked],
            "file": str(out), "file_sha256": sha256_file(out)}
    conn.execute("insert into runs(run_id, run_kind, thresholds_sha256, protocol_ver, meta_json,"
                 " created_at) values (?,?,?,?,?,?)",
                 (sample_id, "elusion-sample", guard.sha, str(guard.data["protocol_ver"]),
                  json.dumps(meta), ledger.now()))
    return meta


def import_elusion(conn: sqlite3.Connection, paper_id: str, path: pathlib.Path,
                   reviewer: str, cfg: Config | None = None) -> dict:
    """Record the review of the sample: missed claims per block, once."""
    cfg = cfg or load_config()
    sample = _sample(conn, paper_id)
    if sample is None:
        raise RecallError(f"no elusion sample for {paper_id}: draw it with --elusion-export")
    if _review(conn, sample["sample_id"]) is not None:
        raise RecallError(f"review of {sample['sample_id']} already recorded")
    if not str(reviewer or "").strip():
        raise RecallError("a review needs the reviewer's name")
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    if any(r.get("sample_id") != sample["sample_id"] for r in rows):
        raise RecallError(f"{path}: sample_id does not match {sample['sample_id']}")
    ids = [r.get("para_id") for r in rows]
    if sorted(ids) != sorted(sample["para_ids"]):
        raise RecallError(f"{path}: the file must list exactly the sampled blocks"
                          f" ({len(sample['para_ids'])}), once each")
    missed = {}
    for r in rows:
        value = (r.get("missed_claims") or "").strip()
        if not value:
            raise RecallError(f"{path}: block {r['para_id']} not reviewed (missed_claims is empty)")
        if not value.isdigit():
            raise RecallError(f"{path}: block {r['para_id']}: missed_claims {value!r} is not a count")
        missed[r["para_id"]] = int(value)
    k, n = sum(1 for m in missed.values() if m), len(missed)
    upper = stats.upper_bound(k, n, float(cfg.data["elusion"]["confidence"]))
    meta = {"paper_id": paper_id, "sample_id": sample["sample_id"], "reviewer": reviewer.strip(),
            "k": k, "n": n, "missed_claims_total": sum(missed.values()), "upper": upper,
            "blocks": missed, "file": str(path), "file_sha256": sha256_file(path)}
    conn.execute("insert into runs(run_id, run_kind, meta_json, created_at) values (?,?,?,?)",
                 (f"{sample['sample_id']}-review", "elusion-review", json.dumps(meta), ledger.now()))
    return meta


def elusion_status(conn: sqlite3.Connection, paper_id: str, cfg: Config | None = None) -> dict:
    guard = thresholds.begin(conn)
    cfg = cfg or load_config()
    n, conf = int(guard.data["elusion_n"]), float(cfg.data["elusion"]["confidence"])
    target = float(cfg.data["elusion"]["target_upper"])
    frame = ledger.frame_blocks(conn, paper_id)
    pool = ledger.unused_pool(conn, paper_id)
    sample = _sample(conn, paper_id)
    review = _review(conn, sample["sample_id"]) if sample else None
    return {"frame": len(frame), "used": len(frame) - len(pool), "unused_pool": len(pool),
            "elusion_n": n, "seed": int(guard.data["sample_seed"]), "sample": sample,
            "review": review, "confidence": conf, "target_upper": target,
            "achievable_upper": stats.upper_bound(0, n, conf) if n else None,
            "observed_upper": review["upper"] if review else None,
            "n_for_target": n_for_target(target, conf),
            "refused": sample is None and len(pool) < n}


# --- output ------------------------------------------------------------------

def _ratio(pair: list[int]) -> str:
    a, b = pair
    return f"{a / b:.3f} ({a}/{b})" if b else f"n/a ({a}/{b})"


def format_table(s: Summary) -> list[str]:
    names = [n for n in s.table["claim_present"]]
    lines = ["| level | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    for level in LEVELS:
        cells = s.table[level]
        if "not_applicable" in cells:
            lines.append(f"| {level} | " + " | ".join(["not-applicable [3]"] * len(names)) + " |")
            continue
        lines.append(f"| {level} | " + " | ".join(
            f"R {_ratio(cells[n]['recall'])} · P {_ratio(cells[n]['precision'])}" for n in names) + " |")
    cp = s.table["claim_present"]
    codex = s.delivered.get("codex", {})
    held = sum(codex.get("quarantined", {}).values())
    lines += [
        "",
        "R = gold sentences matched / gold sentences (numbers_match: sentences with at least one"
        " number); P = rows matched / L1-passed rows of the set.",
        f"[1] codex rests on {s.rows_by_set.get('codex', 0)} L1-passed rows ({codex.get('rows', 0)}"
        f" delivered; {held} records quarantined, a Codex record yields a row only with one"
        f" fragment), so union ≈ claude: union recalls {cp[UNION]['recall'][0]}/{s.gold_split_count}"
        f" gold sentences at claim_present, claude alone {cp['claude']['recall'][0]}.",
        "[2] P is measured against a hand pick, not an exhaustive extraction: a row outside G can"
        " still be valid evidence, so P is a lower bound on precision.",
        f"[3] conditions_match: {s.table['conditions_match']['not_applicable']}.",
    ]
    return lines


def format_elusion(e: dict, floor: dict | None = None) -> list[str]:
    pct = lambda x: f"{100 * x:.1f}%"   # noqa: E731
    lines = ["elusion (frame: blocks of the paragraph unit that no delivered row resolves into;"
             " fragments of quarantined records do not count as used):",
             f"  frame: {e['frame']}, used: {e['used']}, unused_pool: {e['unused_pool']}",
             f"  elusion_n: {e['elusion_n']} (registered), sample_seed: {e['seed']}"]
    if e["sample"]:
        lines.append(f"  sample: {e['sample']['sample_id']}, {e['sample']['n']} blocks,"
                     f" {e['sample']['file']}")
    elif e["refused"]:
        lines.append(f"  sample: refused (unused pool {e['unused_pool']} < elusion_n {e['elusion_n']})")
    else:
        lines.append("  sample: not drawn (drawn once with --elusion-export PATH)")
    r = e["review"]
    if r:
        lines.append(f"  review: {r['k']}/{r['n']} blocks with a missed claim"
                     f" ({r['missed_claims_total']} claims) by {r['reviewer']}")
    elif e["sample"]:
        lines.append("  review: pending (fill missed_claims per block, then --elusion-import PATH"
                     " --reviewer NAME)")
    conf = f"one-sided {pct(e['confidence'])}, exact binomial"
    if e["achievable_upper"] is not None:
        lines.append(f"  upper_bound ({conf}): achievable at 0 errors {pct(e['achievable_upper'])}"
                     f" (n={e['elusion_n']})"
                     + (f"; observed {pct(e['observed_upper'])} (k={r['k']}, n={r['n']})" if r else ""))
    if floor and floor["k"]:
        lines.append(f"  gold floor: k >= {floor['k']} (sampled blocks holding a gold sentence no row"
                     f" covers: {', '.join(floor['blocks'])}), so the observed bound will be"
                     f" >= {pct(floor['upper'])} if the review counts those sentences")
    if e["unused_pool"] < e["n_for_target"]:
        lines.append(f"  {100 * e['target_upper']:g}% upper bound is unreachable at k=1: 0 errors need"
                     f" n >= {e['n_for_target']}, the unused pool has {e['unused_pool']} blocks")
    return lines


def format_chapman(c: dict) -> list[str]:
    sets = "; ".join(f"{n}: {v['rows']} rows -> {v['blocks']} blocks" for n, v in c["sets"].items())
    lines = ["capture-recapture (unit: frame blocks the L1-passed rows resolve into):", f"  {sets}"
             + (f"; both: {c['m']}" if c["m"] is not None else "")]
    if c["skipped"]:
        lines.append(f"  chapman_estimate: skipped: {c['skipped']}")
    else:
        lines.append(f"  chapman_estimate: {c['chapman_estimate']:.1f}"
                     f" (n1={c['n1']}, n2={c['n2']}, m={c['m']})")
    lines.append("  lower_bound: true (two extractors that miss the same blocks for the same reason"
                 " bias the estimate low)")
    return lines


def format_misses(m: dict) -> str:
    in_pool = sum(len(v) for v in m["pool"].values())
    return (f"{in_pool} in {len(m['pool'])} unused-pool blocks, {m['used']} in blocks a row already"
            f" uses (block-level elusion cannot see them), {m['off_frame']} in blocks under the"
            f" frame's word minimum, {m['unlocated']} not located")


def format_probes() -> list[str]:
    return [f"probes P: {FROZEN}", f"target set T: {FROZEN}", f"  why: {FROZEN_WHY}."]


def format_summary(s: Summary, e: dict | None = None) -> str:
    missed = [p for p in s.sentences if not p["covered_by"]]
    lines = [f"recall {s.paper_id} run {s.run_id}",
             f"verifier: {VERIFIER_ID}, protocol: {s.protocol_ver}, config: {s.config_version}"
             f" ({s.config_sha256[:12]})",
             f"query: {s.query_id or '-'} (gold recall does not depend on the query)",
             f"gold: {s.gold_split_count} sentences (user notes excluded); rows: L1-passed only — "
             + ", ".join(f"{n} {k}" for n, k in s.rows_by_set.items()),
             "", "G recall and precision:", "", *format_table(s), "", *format_probes(), ""]
    if e is not None:
        lines += format_elusion(e, gold_floor(s, e)) + [""]
    lines += format_chapman(s.chapman)
    lines += ["", f"gold sentences no row covers ({len(missed)}): {format_misses(s.misses)}"]
    lines += [f"  {p['gold_id']} [{', '.join(p.get('blocks') or ['-'])}]: {p['text'][:90]}"
              for p in missed] or ["  none"]
    return "\n".join(lines)
