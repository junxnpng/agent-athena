"""The imported verifier must run without third-party packages."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from evidence_fixtures import SLUG, write_source

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "verify"))
from tools.verify import judge, ledger, l1_exists, queries, report, thresholds, usage
from tools.verify.convert import claude, codex


class VerifierPortTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-S", str(ROOT / "runner/evidence-verify"), *args],
            cwd="/", capture_output=True, encoding="utf-8", timeout=30,
        )

    def test_contract_cli_without_site_packages_from_another_directory(self):
        result = self.run_cli("schema", "--print-required")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("record_id", result.stdout)

    def test_json_query_registration_without_site_packages(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            query = path / "query.json"
            query.write_text(json.dumps({"query_id": "reuse", "topic": "reuse",
                "claim_text": "Requests reuse prefixes.", "source": "synthetic test"}),
                encoding="utf-8")
            result = self.run_cli("query", "register", "--file", str(query),
                                  "--ledger", str(path / "ledger.sqlite"))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("reuse", result.stdout)

    def test_cli_help_exposes_judge_file_round_trip(self):
        result = self.run_cli("judge", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("export", result.stdout)
        self.assertIn("import", result.stdout)

    def test_both_agents_use_sealed_round_trip(self):
        for agent in ("codex", "claude"):
            with self.subTest(agent=agent), tempfile.TemporaryDirectory() as temp:
                path = Path(temp)
                source = write_source(path)
                conn = ledger.init(path / "ledger.sqlite")
                self.addCleanup(conn.close)
                for converter in (claude, codex):
                    ledger.import_converted(conn, converter.convert(source, SLUG).payload(), source)
                config = thresholds.load()
                config["elusion_n"] = 1
                config_path = path / "thresholds.json"
                config_path.write_text(json.dumps(config), encoding="utf-8")
                thresholds.register(conn, config_path)
                existence = l1_exists.run(conn, source, SLUG)
                self.assertRegex(existence.run_id, r"^l1-demo__paper-\d+$")
                queries.register(conn, {"query_id": "reuse", "topic": "Prefix reuse",
                    "claim_text": "Most requests share a long system prompt with an earlier request.",
                    "source": "synthetic test", "confirmed_by": "test"})
                judge.sweep(conn, SLUG, "reuse")
                with mock.patch.object(usage, "snapshot", return_value={
                        "window": "five_hour", "unavailable": "test cache absent"}):
                    exported = judge.export(conn, source, SLUG, "reuse", out_dir=path, agent=agent)
                self.assertEqual(exported.payload["agent"], agent)
                self.assertGreater(len(exported.payload["items"]), 0)
                verdicts = path / "verdicts.jsonl"
                lines = []
                for item in exported.payload["items"]:
                    start, end = item["quote_span"]["start"], item["quote_span"]["end"]
                    lines.append({"item": item["item"], "row_id": item["row_id"],
                        "alignment": {"verdict": "supports", "evidence_span": {
                            "start": start, "end": end, "text": item["context"]["text"][start:end]}},
                        "faithfulness": {"verdict": "unknown"}})
                verdicts.write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")
                result = judge.import_verdicts(conn, source, exported.path, verdicts,
                    agent + ":synthetic-test", exported.payload["judge_protocol"], exported.sha256)
                self.assertEqual(result.rows, len(lines))
                rendered = report.render(conn, source, SLUG, "reuse")
                self.assertIn("# 근거 검증 보고서", rendered)
                self.assertIn("## 조건 보존", rendered)
                self.assertEqual(conn.execute("select distinct verifier_id from checks where run_id=?",
                    (result.run_id,)).fetchall(), [(agent + ":synthetic-test",)])
                if agent == "codex":
                    self.assertIn("unavailable", result.usage["note"])
                    self.assertNotIn("claude", json.dumps(result.usage))
                exported.path.write_text("{}", encoding="utf-8")
                with self.assertRaisesRegex(judge.ImportRefused, "manifest"):
                    judge.import_verdicts(conn, source, exported.path, verdicts,
                        agent + ":synthetic-test", "claim-judge-v1", exported.sha256)

    def test_invalid_json_is_a_query_error(self):
        with tempfile.TemporaryDirectory() as temp:
            query = Path(temp) / "bad.json"
            query.write_text("{", encoding="utf-8")
            with self.assertRaises(queries.QueryError):
                queries.load(query)


if __name__ == "__main__":
    unittest.main()
