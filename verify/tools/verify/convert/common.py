"""Pieces shared by the record converters."""
from __future__ import annotations

import collections
import dataclasses
import json
import pathlib
import re


from .. import paragraphs as pg
from ..paths import CONFIG_DIR

SOURCES_PATH = CONFIG_DIR / "sources.json"
KIND_MAP_PATH = CONFIG_DIR / "kind_map.json"
THRESHOLDS_PATH = CONFIG_DIR / "thresholds.json"
_SECTION = re.compile(r"§\s*[\w.~\-–]+")


class ConvertError(RuntimeError):
    pass


def sources() -> dict:
    return json.loads(SOURCES_PATH.read_text(encoding="utf-8"))


def records_path(root: pathlib.Path, extractor: str) -> pathlib.Path:
    return root / sources()["records"][extractor]


def variant_paths(root: pathlib.Path, slug: str) -> dict[str, pathlib.Path | None]:
    """Every configured text variant of a paper; None where the file does not exist."""
    out: dict[str, pathlib.Path | None] = {}
    for name, template in sources()["variants"].items():
        path = root / template.format(slug=slug)
        out[name] = path if path.is_file() else None
    return out


def pdf_path(root: pathlib.Path, slug: str) -> pathlib.Path:
    return root / sources()["pdf"].format(slug=slug)


def paragraph_unit() -> dict:
    return json.loads(THRESHOLDS_PATH.read_text(encoding="utf-8"))["paragraph_unit"]


def unit_blocks(root: pathlib.Path, slug: str) -> list[pg.Block]:
    """Blocks of the variant the paragraph unit is defined on."""
    variant = paragraph_unit()["variant"]
    path = variant_paths(root, slug)[variant]
    if path is None:
        raise ConvertError(f"{slug}: paragraph-unit variant {variant} is missing")
    return pg.split_blocks(path.read_text(errors="replace"), variant)


def section_of(location: str) -> str | None:
    """The first § token of a free-form location; None when the location names no section."""
    m = _SECTION.search(location or "")
    return m.group(0).replace(" ", "") if m else None


class KindMap:
    def __init__(self, labels: dict[str, list[str]]):
        self.pairs = [(label, kind) for kind, items in labels.items() for label in items]

    @classmethod
    def load(cls, path: pathlib.Path = KIND_MAP_PATH) -> "KindMap":
        return cls(json.loads(path.read_text(encoding="utf-8"))["labels"])

    def map(self, text: str) -> str | None:
        best = None
        for label, kind in self.pairs:
            at = (text or "").find(label)
            if at < 0:
                continue
            key = (at, -len(label))
            if best is None or key < best[0]:
                best = (key, kind)
        return best[1] if best else None


@dataclasses.dataclass
class ConvertResult:
    extractor_id: str
    paper_id: str
    run_id: str
    source_file: str
    source_sha256: str
    source_records: int
    rows: list[dict]
    quarantined: list[dict]
    fragments: list[dict] = dataclasses.field(default_factory=list)
    title: str | None = None

    @property
    def closed(self) -> int:
        """Source records that ended as rows or as quarantine; never both."""
        rows = {r["record_id"] for r in self.rows}
        held = {q["record_id"] for q in self.quarantined}
        if rows & held:
            raise ConvertError(f"records both delivered and quarantined: {sorted(rows & held)}")
        return len(rows) + len(held)

    def payload(self) -> dict:
        return {
            "extractor_id": self.extractor_id, "paper_id": self.paper_id,
            "run_id": self.run_id, "title": self.title, "source_file": self.source_file,
            "source_sha256": self.source_sha256, "source_records": self.source_records,
            "rows": self.rows, "quarantined": self.quarantined, "fragments": self.fragments,
            "paragraph_unit": paragraph_unit(),
        }


def format_summary(res: ConvertResult) -> str:
    counts = collections.Counter(q["reason_code"] for q in res.quarantined)
    if len(counts) == 1:
        reasons = f" ({next(iter(counts))})"
    elif counts:
        reasons = " (" + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())) + ")"
    else:
        reasons = ""
    return (f"{res.extractor_id} {res.paper_id}\n"
            f"source_records: {res.source_records}, rows: {len(res.rows)}, "
            f"quarantined_records: {len(res.quarantined)}{reasons}, "
            f"closed: {res.closed}/{res.source_records}\n"
            f"run_id: {res.run_id}")


def write_payload(res: ConvertResult, out: pathlib.Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res.payload(), ensure_ascii=False, indent=1) + "\n")


def load_records(root: pathlib.Path, extractor: str, slug: str) -> tuple[pathlib.Path, dict, list[dict]]:
    path = records_path(root, extractor)
    if not path.is_file():
        raise ConvertError(f"{extractor} record file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    records = [r for r in data["records"] if r.get("paper") == slug]
    if not records:
        raise ConvertError(f"no {extractor} records for paper {slug}")
    return path, data, records


def resolve_locator(quote: str, hay: pg.Haystack) -> tuple[str | None, list[str]]:
    """(primary para_id, every resolved para_id) for a quote in the paragraph unit."""
    ids = dict(zip(hay.seqs, hay.para_ids))
    first = pg.primary(quote, hay)
    return (ids[first] if first is not None else None), [ids[s] for s in pg.resolve(quote, hay)]


def locator(section: str | None, page, para_id: str | None, **extra) -> dict:
    loc = {"section": section, "page": page, "para_id": para_id}
    loc.update(extra)
    return loc
