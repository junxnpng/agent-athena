"""Plan usage snapshots taken before and after the LLM part of a run.

The snapshot is read from the usage cache the user's statusline keeps (see
`config/usage.json`). It is account-wide and at most a few minutes old, so the
difference between two snapshots is an observation, never a gate.
"""
from __future__ import annotations

import datetime as _dt
import json
import pathlib
import time


from .paths import CONFIG_DIR

CONFIG_PATH = CONFIG_DIR / "usage.json"
LABELS = {"five_hour": "5h", "seven_day": "7d"}


def load(path: pathlib.Path = CONFIG_PATH) -> dict:
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def snapshot_for(agent: str) -> dict:
    """Only Claude runs can use the Claude statusline cache."""
    if agent == "claude":
        return snapshot()
    return {"taken_at": _now(), "window": "five_hour", "agent": agent,
            "unavailable": f"no usage adapter for {agent}"}


def snapshot(cfg: dict | None = None) -> dict:
    """{taken_at, window, used_pct, resets_at, age_s, stale} or {taken_at, window, unavailable}."""
    cfg = cfg or load()
    path, window = pathlib.Path(cfg["path"]), cfg["window"]
    base = {"taken_at": _now(), "window": window, "source": str(path)}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        age = time.time() - path.stat().st_mtime
    except (OSError, json.JSONDecodeError) as exc:
        return dict(base, unavailable=f"cannot read {path}: {exc.__class__.__name__}")
    entry = data.get(window) if isinstance(data, dict) else None
    if not isinstance(entry, dict) or entry.get("utilization") is None:
        return dict(base, unavailable=f"no {window} utilization in {path}")
    return dict(base, used_pct=float(entry["utilization"]), resets_at=entry.get("resets_at"),
                age_s=round(age, 1), stale=age > float(cfg["max_age_s"]))


def delta(start: dict, end: dict) -> dict:
    out = {"window": start.get("window"), "start": start, "end": end, "points": None, "note": ""}
    missing = [s for s in (start, end) if "unavailable" in s]
    if missing:
        out["note"] = "unavailable: " + missing[0]["unavailable"]
        return out
    if start.get("resets_at") != end.get("resets_at"):
        out["note"] = "reset during run"
        return out
    out["points"] = round(end["used_pct"] - start["used_pct"], 1)
    if start["stale"] or end["stale"]:
        out["note"] = "stale snapshot"
    return out


def _elapsed(start: dict, end: dict) -> str:
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    try:
        s = (_dt.datetime.strptime(end["taken_at"], fmt)
             - _dt.datetime.strptime(start["taken_at"], fmt)).total_seconds()
    except (KeyError, ValueError):
        return "?"
    return f"{s / 60:.0f} min"


def _pct(v: float) -> str:
    return f"{v:g}%"


def format_delta(d: dict) -> str:
    label = LABELS.get(d.get("window"), d.get("window"))
    s, e = d["start"], d["end"]
    if d["points"] is None and "unavailable" in d["note"]:
        return f"{label} usage: {d['note']}"
    head = f"{label} usage: {_pct(s['used_pct'])} -> {_pct(e['used_pct'])}"
    if d["points"] is None:
        return f"{head} ({d['note']}, {_elapsed(s, e)})"
    tail = f"{d['points']:+g}pt, {_elapsed(s, e)}, account-wide"
    return f"{head} ({tail}{'; ' + d['note'] if d['note'] else ''})"
