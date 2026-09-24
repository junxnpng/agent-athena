"""Registered thresholds: registered once before the first layer runs, read-only afterwards."""
from __future__ import annotations

import json
import pathlib
import sqlite3


from . import ledger
from .paths import CONFIG_DIR, sha256_file

DEFAULT_PATH = CONFIG_DIR / "thresholds.json"
REQUIRED_KEYS = (
    "protocol_ver", "l1_pass_grades", "waiver_reason_required", "elusion_n", "sample_seed",
    "mutation_detect_min", "mutation_fp_max", "kappa_report_only", "escalation_max",
    "leakage_n", "context_width_default", "paragraph_unit",
)


class ThresholdsError(RuntimeError):
    pass


class ThresholdsChanged(ThresholdsError):
    pass


def load(path: pathlib.Path = DEFAULT_PATH) -> dict:
    path = pathlib.Path(path)
    if not path.is_file():
        raise ThresholdsError(f"{path}: not found")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ThresholdsError(f"{path}: not a mapping")
    missing = [k for k in REQUIRED_KEYS if k not in data]
    if missing:
        raise ThresholdsError(f"{path}: missing {', '.join(missing)}")
    return data


def registration(conn: sqlite3.Connection, protocol_ver: str) -> tuple[str, str] | None:
    return conn.execute(
        "select run_id, thresholds_sha256 from runs where run_kind='thresholds-register'"
        " and protocol_ver=? order by created_at, run_id limit 1", (protocol_ver,)).fetchone()


def registered_path(conn: sqlite3.Connection) -> pathlib.Path | None:
    """The file of the earliest registration, the one every later run is held to."""
    row = conn.execute("select meta_json from runs where run_kind='thresholds-register'"
                       " order by created_at, run_id limit 1").fetchone()
    return pathlib.Path(json.loads(row[0])["path"]) if row else None


def register(conn: sqlite3.Connection, path: pathlib.Path = DEFAULT_PATH) -> str:
    """Record the file's sha256 in runs. One registration per protocol version."""
    data = load(path)
    sha = sha256_file(path)
    ver = str(data["protocol_ver"])
    existing = registration(conn, ver)
    if existing is not None:
        if existing[1] != sha:
            raise ThresholdsError(
                f"thresholds for protocol {ver} already registered as {existing[1][:12]};"
                " a different file needs a new protocol_ver")
        return existing[0]
    papers = [p for (p,) in conn.execute(
        "select distinct paper_id from claims where status='row' order by paper_id")]
    if not papers:
        raise ThresholdsError("import records before registering thresholds:"
                              " elusion_n is bounded by the measured unused-paragraph pool")
    units = ledger.imported_units(conn)
    if units != [data["paragraph_unit"]]:
        raise ThresholdsError(f"paragraph unit {data['paragraph_unit']} differs from the unit the"
                              f" imported rows were located in ({units}); convert and import again")
    pools = {p: len(ledger.unused_pool(conn, p, data["paragraph_unit"])) for p in papers}
    smallest = min(pools.values())
    if int(data["elusion_n"]) > smallest:
        raise ThresholdsError(f"elusion_n={data['elusion_n']} exceeds the unused-paragraph pool"
                              f" ({json.dumps(pools)})")
    run_id = f"thresholds-{ver}-{sha[:12]}"
    conn.execute(
        "insert into runs(run_id, run_kind, input_sha256, thresholds_sha256, protocol_ver,"
        " meta_json, created_at) values (?,?,?,?,?,?,?)",
        (run_id, "thresholds-register", sha, sha, ver,
         json.dumps({"path": str(pathlib.Path(path).resolve()), "unused_pool": pools}),
         ledger.now()))
    return run_id


class Guard:
    """Holds the registered sha for the length of a run; check() dies on any change."""

    def __init__(self, path: pathlib.Path, sha: str, run_id: str, data: dict):
        self.path, self.sha, self.run_id, self.data = pathlib.Path(path), sha, run_id, data

    def check(self) -> None:
        current = sha256_file(self.path)
        if current != self.sha:
            raise ThresholdsChanged(f"thresholds changed mid-run: registered {self.sha[:12]},"
                                    f" file now {current[:12]}")


def begin(conn: sqlite3.Connection, path: pathlib.Path | None = None) -> Guard:
    """Start a run under the registered thresholds (the registered file unless one is named)."""
    path = path or registered_path(conn) or DEFAULT_PATH
    data = load(path)
    reg = registration(conn, str(data["protocol_ver"]))
    if reg is None:
        raise ThresholdsError("thresholds not registered: run `verify thresholds register`")
    guard = Guard(path, reg[1], reg[0], data)
    guard.check()
    return guard
