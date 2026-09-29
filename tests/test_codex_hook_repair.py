"""Security hook output must retain warnings while excluding Claude telemetry."""
from __future__ import annotations

import contextlib
import importlib.machinery
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = '''import json
import os

def emit_metrics(metrics, additional_context=None):
    out = {"metrics": metrics, "rewakeSummary": "Review summary"}
    if additional_context:
        out["hookSpecificOutput"] = {"hookEventName": "PostToolUse", "additionalContext": additional_context}
    print(json.dumps(out), flush=True)

def dedup():
    print(json.dumps({"metrics": {"bash_hook_dedup": True}}), flush=True)

def pattern():
    output = {"metrics": {"pattern_hits": 1}, "hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "Security warning"}}
    print(json.dumps(output))
'''


class CodexHookRepairTests(unittest.TestCase):
    def repair(self):
        path = ROOT / 'scripts/repair-codex-security-hook'
        self.assertTrue(path.is_file(), 'repeatable hook repair is missing')
        return importlib.machinery.SourceFileLoader('repair_security_hook', str(path)).load_module()

    def test_all_output_paths_preserve_warnings_and_remove_only_telemetry(self):
        repair = self.repair()
        fixed = repair.patch_source(FIXTURE)
        for runtime in ('codex', 'claude'):
            with mock.patch.dict(os.environ, {'PLUGIN_ROOT': '/fixture'} if runtime == 'codex' else {}, clear=True):
                ns = {}
                exec(compile(fixed, '<fixture>', 'exec'), ns)
                for name in ('dedup', 'pattern'):
                    out = io.StringIO()
                    with contextlib.redirect_stdout(out):
                        ns[name]()
                    payload = json.loads(out.getvalue())
                    self.assertEqual('metrics' in payload, runtime == 'claude')
                    self.assertEqual('rewakeSummary' in payload, runtime == 'claude')
                    if name == 'pattern':
                        self.assertEqual(payload['hookSpecificOutput'], {'hookEventName': 'PostToolUse', 'additionalContext': 'Security warning'})
                    elif runtime == 'codex':
                        self.assertEqual(payload, {})
        self.assertEqual(repair.patch_source(fixed), fixed)

    def test_install_keeps_backup_and_is_idempotent(self):
        repair = self.repair()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'security_reminder_hook.py'
            path.write_text(FIXTURE, encoding='utf-8')
            path.chmod(0o755)
            self.assertTrue(repair.apply(path))
            self.assertEqual(path.with_suffix('.py.before-codex-json-fix').read_text(), FIXTURE)
            self.assertEqual(path.stat().st_mode & 0o777, 0o755)
            self.assertFalse(repair.apply(path))

    def test_unknown_upstream_layout_is_not_modified(self):
        repair = self.repair()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'security_reminder_hook.py'
            path.write_text('print("changed upstream")\n', encoding='utf-8')
            with self.assertRaises(ValueError):
                repair.apply(path)
            self.assertEqual(path.read_text(), 'print("changed upstream")\n')
            self.assertFalse(path.with_suffix('.py.before-codex-json-fix').exists())

    def test_existing_partial_fix_is_completed(self):
        repair = self.repair()
        partial = FIXTURE.replace('    print(json.dumps(out), flush=True)',
            '    if os.environ.get("PLUGIN_ROOT"):\n        out.pop("metrics", None)\n        out.pop("rewakeSummary", None)\n    print(json.dumps(out), flush=True)')
        fixed = repair.patch_source(partial)
        self.assertEqual(fixed.count('out.pop("metrics", None)'), 1)
        self.assertEqual(repair.patch_source(fixed), fixed)


if __name__ == '__main__':
    unittest.main()
