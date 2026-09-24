from __future__ import annotations
import shutil

import pytest
import json

from tools.verify import cli, ledger, thresholds
from tools.verify.convert import claude, codex
from .conftest import SLUG


@pytest.fixture
def loaded(ledger_path, source_root):
    conn = ledger.init(ledger_path)
    for mod in (claude, codex):
        ledger.import_converted(conn, mod.convert(source_root, SLUG).payload(), source_root)
    return conn


@pytest.fixture
def tfile(tmp_path):
    path = tmp_path / "thresholds.json"
    shutil.copy(thresholds.DEFAULT_PATH, path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["elusion_n"] = 1
    path.write_text(json.dumps(data, sort_keys=False, ensure_ascii=False))
    return path


def test_registered_file_has_all_keys():
    data = thresholds.load(thresholds.DEFAULT_PATH)
    assert set(thresholds.REQUIRED_KEYS) <= set(data)
    assert data["l1_pass_grades"] == ["exact", "strict", "loose", "gapped"]


def test_register_fills_runs(loaded, tfile):
    run_id = thresholds.register(loaded, tfile)
    sha = loaded.execute("select thresholds_sha256 from runs where run_id=?", (run_id,)).fetchone()[0]
    assert sha == thresholds.sha256_file(tfile)
    assert thresholds.register(loaded, tfile) == run_id  # same file: same registration


def test_edit_mid_run_dies(loaded, tfile):
    thresholds.register(loaded, tfile)
    guard = thresholds.begin(loaded, tfile)
    guard.check()
    tfile.write_text(tfile.read_text(encoding="utf-8").replace('"sample_seed": ', '"sample_seed": 1'))
    with pytest.raises(thresholds.ThresholdsChanged, match="thresholds changed mid-run"):
        guard.check()
    with pytest.raises(thresholds.ThresholdsChanged, match="thresholds changed mid-run"):
        thresholds.begin(loaded, tfile)


def test_reregister_different_file_refused(loaded, tfile):
    thresholds.register(loaded, tfile)
    tfile.write_text(tfile.read_text(encoding="utf-8").replace('"mutation_fp_max": 0.1', '"mutation_fp_max": 0.2'))
    with pytest.raises(thresholds.ThresholdsError, match="already registered"):
        thresholds.register(loaded, tfile)


def test_begin_without_registration(ledger_path, tfile):
    with pytest.raises(thresholds.ThresholdsError, match="not registered"):
        thresholds.begin(ledger.init(ledger_path), tfile)


def test_missing_key_refused(loaded, tfile):
    data = json.loads(tfile.read_text(encoding="utf-8"))
    del data["elusion_n"]
    tfile.write_text(json.dumps(data))
    with pytest.raises(thresholds.ThresholdsError, match="elusion_n"):
        thresholds.register(loaded, tfile)


def test_elusion_n_bounded_by_pool(loaded, tfile):
    pool = ledger.unused_pool(loaded, SLUG)
    assert [b["para_id"] for b in pool] == ["codex_raw#0005"]
    data = json.loads(tfile.read_text(encoding="utf-8"))
    data["elusion_n"] = 2
    tfile.write_text(json.dumps(data))
    with pytest.raises(thresholds.ThresholdsError, match="exceeds the unused-paragraph pool"):
        thresholds.register(loaded, tfile)


def test_register_needs_imported_rows(ledger_path, tfile):
    with pytest.raises(thresholds.ThresholdsError, match="import records"):
        thresholds.register(ledger.init(ledger_path), tfile)


def test_cli_register_and_show(loaded, ledger_path, tfile, capsys):
    loaded.close()
    args = ["--ledger", str(ledger_path), "--file", str(tfile)]
    assert cli.main(["thresholds", "register", *args]) == 0
    assert cli.main(["thresholds", "show", *args]) == 0
    out = capsys.readouterr().out
    assert thresholds.sha256_file(tfile) in out and "elusion_n: 1" in out
    tfile.write_text(tfile.read_text(encoding="utf-8") + "\n ")
    assert cli.main(["thresholds", "show", *args]) == 1
    assert "thresholds changed mid-run" in capsys.readouterr().err


def test_register_refuses_unit_other_than_imported(loaded, tfile):
    data = json.loads(tfile.read_text(encoding="utf-8"))
    data["paragraph_unit"]["min_words"] = 30
    tfile.write_text(json.dumps(data))
    with pytest.raises(thresholds.ThresholdsError, match="paragraph unit"):
        thresholds.register(loaded, tfile)


def test_import_after_registration_checks_the_seal(loaded, tfile, source_root, monkeypatch):
    thresholds.register(loaded, tfile)
    monkeypatch.setattr(thresholds, "DEFAULT_PATH", tfile)
    payload = claude.convert(source_root, SLUG).payload()
    assert ledger.import_converted(loaded, payload, source_root)["skipped"] == 6
    tfile.write_text(tfile.read_text(encoding="utf-8") + "\n ")
    with pytest.raises(thresholds.ThresholdsChanged):
        ledger.import_converted(loaded, payload, source_root)


def test_guard_uses_the_registered_file_by_default(loaded, tfile):
    thresholds.register(loaded, tfile)
    assert thresholds.begin(loaded).path == tfile
    assert ledger.frame_blocks(loaded, SLUG)  # unit read from the registered file


def test_missing_file_is_a_thresholds_error(tmp_path):
    with pytest.raises(thresholds.ThresholdsError, match="not found"):
        thresholds.load(tmp_path / "absent.json")


def test_a_new_protocol_version_registers_beside_the_old(loaded, tfile):
    first = thresholds.register(loaded, tfile)
    data = json.loads(tfile.read_text(encoding="utf-8"))
    data["protocol_ver"] = "v9"
    tfile.write_text(json.dumps(data, sort_keys=False, ensure_ascii=False))
    second = thresholds.register(loaded, tfile)
    assert second != first and second.startswith("thresholds-v9-")
    assert thresholds.begin(loaded).run_id == second
