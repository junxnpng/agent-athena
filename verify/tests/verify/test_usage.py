from __future__ import annotations
import json
import os
import time

import pytest

from tools.verify import usage


def _cache(tmp_path, pct, resets="2026-09-23T11:30:00+00:00", age=0):
    path = tmp_path / "usage.json"
    path.write_text(json.dumps({"five_hour": {"utilization": pct, "resets_at": resets},
                                "seven_day": {"utilization": 80, "resets_at": "x"}}))
    t = time.time() - age
    os.utime(path, (t, t))
    return path


def _cfg(path):
    return {"path": str(path), "window": "five_hour", "max_age_s": 300}


def test_snapshot_reads_the_window(tmp_path):
    s = usage.snapshot(_cfg(_cache(tmp_path, 23.5)))
    assert s["used_pct"] == 23.5 and s["window"] == "five_hour"
    assert s["resets_at"].startswith("2026-09-23T11:30") and s["stale"] is False


def test_missing_or_bad_cache_is_unavailable(tmp_path):
    assert usage.snapshot(_cfg(tmp_path / "none.json"))["unavailable"]
    bad = tmp_path / "bad.json"
    bad.write_text("{")
    assert usage.snapshot(_cfg(bad))["unavailable"]
    bad.write_text(json.dumps({"seven_day": {}}))
    assert "five_hour" in usage.snapshot(_cfg(bad))["unavailable"]


def test_old_cache_is_stale(tmp_path):
    assert usage.snapshot(_cfg(_cache(tmp_path, 10, age=900)))["stale"] is True


def test_delta_in_points_and_reset(tmp_path):
    a = usage.snapshot(_cfg(_cache(tmp_path, 23)))
    b = usage.snapshot(_cfg(_cache(tmp_path, 31)))
    d = usage.delta(a, b)
    assert d["points"] == 8 and d["note"] == ""
    assert usage.format_delta(d).startswith("5h usage: 23% -> 31% (+8pt")
    c = usage.snapshot(_cfg(_cache(tmp_path, 2, resets="2026-09-23T16:30:00+00:00")))
    assert usage.delta(a, c)["points"] is None and usage.delta(a, c)["note"] == "reset during run"
    gone = usage.snapshot(_cfg(tmp_path / "none.json"))
    assert usage.delta(a, gone)["points"] is None
    assert "unavailable" in usage.format_delta(usage.delta(a, gone))


def test_stale_end_is_flagged(tmp_path):
    a = usage.snapshot(_cfg(_cache(tmp_path, 23)))
    b = usage.snapshot(_cfg(_cache(tmp_path, 30, age=900)))
    assert usage.delta(a, b)["note"] == "stale snapshot"
