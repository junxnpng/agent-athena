"""Extraction preflight must enforce the verifier contract before any output."""
from __future__ import annotations

import hashlib
import importlib
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "verify"))
sys.path.insert(0, str(ROOT / "extract"))


class ExtractPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)

    def module(self, name):
        self.assertTrue((ROOT / "extract/extract" / (name + ".py")).is_file(),
                        "extract preflight module is not implemented: " + name)
        return importlib.import_module("extract." + name)

    def write_json(self, name, data):
        path = self.path / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_gate_keys_and_hash(self):
        gates = self.module("gates")
        data = gates.load_gates()
        self.assertEqual(set(data), {"schema_valid", "l1_variant", "l1_grades", "l1_pass_rate",
                                     "kind_memo_rate", "g_recall", "codex_raw_grades"})
        self.assertEqual(data["l1_variant"], "extract_raw")
        self.assertEqual(gates.sha256_of(gates.DEFAULT_PATH),
                         hashlib.sha256(gates.DEFAULT_PATH.read_bytes()).hexdigest())
        del data["schema_valid"]
        with self.assertRaisesRegex(RuntimeError, "schema_valid"):
            gates.load_gates(self.write_json("missing.json", data))

    def test_wrong_split_is_rejected_with_environment_override(self):
        gates = self.module("gates")
        from tools.verify import thresholds
        data = thresholds.load()
        data["paragraph_unit"]["split"] = "other"
        bad = self.write_json("bad.json", data)
        with mock.patch.dict(os.environ, {"EXTRACT_THRESHOLDS_PATH": str(bad)}):
            with self.assertRaisesRegex(RuntimeError, "blank_line_block"):
                gates.assert_paragraph_unit_split()
        good = self.write_json("good.json", thresholds.load())
        with mock.patch.dict(os.environ, {"EXTRACT_THRESHOLDS_PATH": str(good)}):
            gates.assert_paragraph_unit_split()

    def test_query_remains_unconfirmed_until_user_confirms(self):
        query = self.module("query")
        data = {"query_id": "demo", "topic": "reuse", "claim_text": "Requests reuse prefixes.",
                "source": "synthetic test"}
        path = self.write_json("query.json", data)
        self.assertTrue(query.load(path)["unconfirmed"])
        data["confirmed_by"] = "test user"
        self.assertFalse(query.load(self.write_json("confirmed.json", data))["unconfirmed"])
        del data["claim_text"]
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            query.load(self.write_json("missing.json", data))
        self.assertEqual(error.exception.code, 1)

    def test_source_path_requires_an_existing_directory(self):
        paths = self.module("paths")
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(paths.SourceRootError):
                paths.source_root()
        self.assertEqual(paths.source_root(str(self.path)), self.path)
        with self.assertRaises(paths.SourceRootError):
            paths.source_root(str(self.path / "absent"))

    def test_cli_runs_without_site_packages_and_blocks_bad_contract(self):
        query = self.write_json("query.json", {"query_id": "demo", "topic": "reuse",
            "claim_text": "Requests reuse prefixes.", "source": "test"})
        command = [sys.executable, "-S", str(ROOT / "runner/evidence-extract"), "check",
                   "--query", str(query)]
        result = subprocess.run(command, cwd="/", capture_output=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["query"]["unconfirmed"])
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(len(payload["gates_sha256"]), 64)
        from tools.verify import thresholds
        config = thresholds.load()
        config["paragraph_unit"]["split"] = "other"
        bad = self.write_json("bad.json", config)
        env = dict(os.environ, EXTRACT_THRESHOLDS_PATH=str(bad))
        result = subprocess.run(command, cwd="/", env=env, capture_output=True,
                                encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("blank_line_block", result.stderr)
        self.assertFalse((self.path / "results").exists())


if __name__ == "__main__":
    unittest.main()
