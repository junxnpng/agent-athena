"""A row whose existence check is MISS never reaches a later layer.

Every later layer (L2, L6, judge, recall) reads its input through
`ledger.l1_passed`, i.e. the view v_l1_passed: rows whose latest L1 verdict is PASS.
"""
from __future__ import annotations
import pathlib

import pytest

from tools.verify import l1_exists as l1, ledger
from .conftest import SLUG

LAYER_DIR = pathlib.Path(ledger.__file__).parent


def _miss(conn, row_id):
    conn.execute("update claims set quote='words that are nowhere in the paper at all'"
                 " where row_id=?", (row_id,))


def test_miss_rows_are_excluded(sealed, source_root):
    _miss(sealed, "claude:DM-C1.q1")
    l1.run(sealed, source_root, SLUG)
    ids = {r["row_id"] for r in ledger.l1_passed(sealed, SLUG)}
    assert "claude:DM-C1.q1" not in ids
    assert ids == {"claude:DM-A1.q1", "claude:DM-B1.q1", "claude:DM-B1.q2", "codex:DM001.q1"}


def test_unchecked_rows_are_excluded(sealed):
    assert ledger.l1_passed(sealed, SLUG) == []


def test_latest_check_decides(sealed, source_root):
    l1.run(sealed, source_root, SLUG)
    assert len(ledger.l1_passed(sealed, SLUG)) == 5
    _miss(sealed, "claude:DM-A1.q1")
    l1.run(sealed, source_root, SLUG)
    assert "claude:DM-A1.q1" not in {r["row_id"] for r in ledger.l1_passed(sealed, SLUG)}


def test_passed_rows_carry_the_l1_span(sealed, source_root):
    l1.run(sealed, source_root, SLUG)
    row = next(r for r in ledger.l1_passed(sealed, SLUG) if r["row_id"] == "claude:DM-B1.q1")
    assert (row["l1_grade"], row["matched_variant"]) == ("exact", "codex_raw")
    assert row["char_end"] - row["char_start"] == len(row["quote"])


def test_quarantined_records_never_pass(sealed, source_root):
    l1.run(sealed, source_root, SLUG)
    ids = {r["row_id"] for r in ledger.l1_passed(sealed, SLUG)}
    held = {r for (r,) in sealed.execute("select row_id from claims where status='quarantined'")}
    assert held and not ids & held


@pytest.mark.parametrize("module", ledger.DOWNSTREAM_LAYERS)
def test_downstream_layers_read_through_the_view(module):
    path = LAYER_DIR / f"{module}.py"
    if not path.is_file():
        pytest.skip(f"{module}.py not written yet")
    src = path.read_text(encoding="utf-8")
    assert "l1_passed" in src, f"{module} must take its rows from ledger.l1_passed"
    assert "from claims" not in src.lower(), f"{module} reads claims directly"
