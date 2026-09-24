"""The hand-picked gold set G: sentence split by fixed rules, user notes kept apart.

G is one pasted line: a heading, the one-line review, then paper sentences with
the user's `->` notes between them. The rules live in config/gold_split.json;
the number of gold sentences is what they produce, recorded at registration as
gold_split_count. Notes are registered as `user_note` rows and never enter a
sentence. Gold rows change afterwards only through an audit record.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import pathlib
import re
import sqlite3


from ..paths import CONFIG_DIR, ROOT, sha256_file

RULES_PATH = CONFIG_DIR / "gold_split.json"


class GoldError(RuntimeError):
    pass


@dataclasses.dataclass(frozen=True)
class Rules:
    version: str
    source: str
    section: str
    line_prefix: str
    emphasis: re.Pattern
    review_label: str
    note_arrow: str
    sentence_end: re.Pattern
    abbreviations: tuple[str, ...]
    camel_glue: bool
    openers: re.Pattern | None
    no_split: tuple[str, ...]
    sha256: str


def load_rules(path: pathlib.Path = RULES_PATH) -> Rules:
    path = pathlib.Path(path)
    cfg = json.loads(path.read_text(encoding="utf-8"))
    words = cfg["note_end"].get("sentence_openers") or []
    openers = re.compile(r"(?<=[a-z]) (?=(?:" + "|".join(map(re.escape, words)) + r")\b)") \
        if words else None
    return Rules(cfg["version"], cfg["source"], cfg["section"], cfg["line_prefix"],
                 re.compile(cfg["emphasis"]), cfg["review_label"], cfg["note_arrow"],
                 re.compile(cfg["sentence_end"]), tuple(cfg.get("abbreviations") or ()),
                 bool(cfg["note_end"].get("camel_glue")), openers,
                 tuple(cfg.get("no_split") or ()), sha256_file(path))


def source_path(slug: str, rules: Rules | None = None) -> pathlib.Path:
    return ROOT / (rules or load_rules()).source.format(slug=slug)


@dataclasses.dataclass(frozen=True)
class Item:
    kind: str                   # sentence | user_note
    text: str
    boundary_repaired: int      # the start was split out of text glued without a space


@dataclasses.dataclass
class Parsed:
    heading: str | None
    items: list[Item]

    def of(self, kind: str) -> list[Item]:
        return [i for i in self.items if i.kind == kind]

    def sha256(self) -> str:
        blob = json.dumps([dataclasses.astuple(i) for i in self.items], ensure_ascii=False)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def pasted_line(text: str, rules: Rules) -> str:
    """The one line of pasted text under the section heading, without its prefix."""
    lines = text.splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == rules.section)
    except StopIteration:
        raise GoldError(f"no pasted line: section {rules.section!r} not found") from None
    for line in lines[start + 1:]:
        if line.startswith(rules.line_prefix):
            return line[len(rules.line_prefix):]
        if line.startswith("## "):
            break
    raise GoldError(f"no pasted line starting with {rules.line_prefix!r} under {rules.section!r}")


def _ends_abbreviation(text: str, dot: int, rules: Rules) -> bool:
    head = text[:dot + 1]
    return any(head.endswith(a) and (len(head) == len(a) or not head[-len(a) - 1].isalnum())
               for a in rules.abbreviations)


def _periods(text: str, rules: Rules) -> list[int]:
    """Offsets just after every sentence-ending period."""
    return [m.end() for m in rules.sentence_end.finditer(text)
            if not _ends_abbreviation(text, m.start(), rules)]


def _inside_name(text: str, at: int, rules: Rules) -> bool:
    for name in rules.no_split:
        for m in re.finditer(re.escape(name), text):
            if m.start() < at < m.end():
                return True
    return False


def _note_end(text: str, rules: Rules) -> int:
    """Where a note typed onto the next pasted sentence ends: the earliest note boundary."""
    ends = _periods(text, rules)
    if rules.camel_glue:
        ends += [m.start() for m in re.finditer(r"(?<=[a-z])(?=[A-Z][a-z])", text)
                 if not _inside_name(text, m.start(), rules)]
    if rules.openers is not None:
        ends += [m.start() for m in rules.openers.finditer(text)]
    return min(ends, default=len(text))


def _glued(text: str, at: int) -> int:
    """1 when the boundary at `at` has no whitespace on either side."""
    return int(0 < at < len(text) and not text[at - 1].isspace() and not text[at].isspace())


def _sentences(text: str, rules: Rules, first_repaired: int) -> list[Item]:
    out, start = [], 0
    for end in _periods(text, rules) + [len(text)]:
        piece = text[start:end].strip()
        if piece:
            out.append(Item("sentence", piece, first_repaired if start == 0 else _glued(text, start)))
        start = end
    return out


def _body(segment: str, rules: Rules) -> list[Item]:
    parts = segment.split(rules.note_arrow)
    items = _sentences(parts[0], rules, 0)
    for part in parts[1:]:
        end = _note_end(part, rules)
        note = part[:end].strip()
        if note:
            items.append(Item("user_note", note, 0))
        items += _sentences(part[end:], rules, _glued(part, end))
    return items


def parse(text: str, rules: Rules) -> Parsed:
    segments = rules.emphasis.split(pasted_line(text, rules))
    heading = None
    if len(segments) > 1:
        heading, segments = segments[0].strip() or None, segments[1:]
    items: list[Item] = []
    for seg in segments:
        if not seg.strip():
            continue
        if seg.strip().startswith(rules.review_label):
            items.append(Item("user_note", seg.strip(), 0))
        else:
            items += _body(seg, rules)
    return Parsed(heading, items)


# --- registration --------------------------------------------------------

@dataclasses.dataclass
class Registered:
    paper_id: str
    run_id: str
    source_file: str
    heading: str | None
    sentences: int
    notes: int
    repaired: int
    inserted: int
    rules: Rules


def registration(conn: sqlite3.Connection, slug: str) -> dict | None:
    row = conn.execute("select meta_json from runs where run_kind='gold-register'"
                       " and json_extract(meta_json, '$.paper_id')=? order by created_at limit 1",
                       (slug,)).fetchone()
    return json.loads(row[0]) if row else None


def register(conn: sqlite3.Connection, slug: str, path: pathlib.Path | None = None,
             rules: Rules | None = None) -> Registered:
    """Register G once. The same file again is a no-op; a different split is refused."""
    from ..ledger import now

    rules = rules or load_rules()
    path = pathlib.Path(path or source_path(slug, rules))
    if not path.is_file():
        raise GoldError(f"gold file not found: {path}")
    parsed = parse(path.read_text(encoding="utf-8"), rules)
    sentences, notes = parsed.of("sentence"), parsed.of("user_note")
    if not sentences:
        raise GoldError(f"{path}: the rules produced no gold sentence")
    res = Registered(slug, f"gold-{slug}-{parsed.sha256()[:12]}", str(path), parsed.heading,
                     len(sentences), len(notes), sum(i.boundary_repaired for i in sentences), 0, rules)
    old = registration(conn, slug)
    if old is not None:
        if old["items_sha256"] != parsed.sha256():
            raise GoldError(f"{slug}: gold already registered as {old['run_id']} with a different"
                            " split; gold rows change only through an audit record")
        res.run_id = old["run_id"]
        return res
    meta = {"paper_id": slug, "run_id": res.run_id, "source_file": str(path),
            "rules_version": rules.version, "rules_sha256": rules.sha256,
            "gold_split_count": len(sentences), "user_notes": len(notes),
            "boundary_repaired": res.repaired, "heading": parsed.heading,
            "items_sha256": parsed.sha256()}
    with conn:
        conn.execute("BEGIN")
        conn.execute("insert into runs(run_id, run_kind, input_sha256, meta_json, created_at)"
                     " values (?,?,?,?,?)",
                     (res.run_id, "gold-register", sha256_file(path), json.dumps(meta, ensure_ascii=False),
                      now()))
        for kind, items, tag, width in (("sentence", sentences, "s", 3), ("user_note", notes, "n", 2)):
            for seq, item in enumerate(items, start=1):
                conn.execute(
                    "insert into gold(gold_id, paper_id, seq, text, kind, source, owner,"
                    " boundary_repaired) values (?,?,?,?,?,'hand','user',?)",
                    (f"{slug}:{tag}{seq:0{width}d}", slug, seq, item.text, kind, item.boundary_repaired))
                res.inserted += 1
    return res


def sentences(conn: sqlite3.Connection, slug: str) -> list[dict]:
    """The registered gold sentences of a paper in order (their current revision)."""
    cols = ("gold_id", "seq", "text", "boundary_repaired", "revision")
    rows = conn.execute(f"select {', '.join(cols)} from gold where paper_id=? and kind='sentence'"
                        " order by seq", (slug,)).fetchall()
    if not rows:
        raise GoldError(f"{slug}: no gold sentences; run `verify convert gold --paper {slug}`")
    return [dict(zip(cols, r)) for r in rows]


def format_summary(res: Registered) -> str:
    return "\n".join([
        f"gold {res.paper_id}: {res.source_file}",
        f"rules: {res.rules.version} (config/gold_split.json, sha256 {res.rules.sha256[:12]})",
        f"heading: {res.heading} (not gold)",
        f"gold_split_count: {res.sentences} (boundary_repaired: {res.repaired})",
        f"user_notes: {res.notes} (kept apart from the sentences)",
        f"run {res.run_id}: inserted {res.inserted}"
        + ("" if res.inserted else " (already registered)"),
    ])
