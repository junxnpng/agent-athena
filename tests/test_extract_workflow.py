"""Minimal P4a file round trip; source text is copied by code, never the model."""
from __future__ import annotations

import contextlib
import importlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'verify'))
sys.path.insert(0, str(ROOT / 'extract'))
RAW = '1 Introduction\n\nWe measured twenty requests in the production system. The result is useful.\n\nReferences\n\nReference text.'
QUERY = {'query_id': 'test-query', 'topic': 'requests', 'claim_text': 'Requests are measurable.', 'source': 'test'}


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def module(self, name):
        self.assertTrue((ROOT / 'extract/extract' / (name + '.py')).is_file(), name + ' is not implemented')
        return importlib.import_module('extract.' + name)

    def export(self):
        workfile = self.module('workfile_min')
        from extract.pipeline import prepare_segments
        from extract.gates import DEFAULT_PATH, sha256_of
        import hashlib
        meta = {'pdf_sha256': 'a' * 64, 'extract_raw_sha256': hashlib.sha256(RAW.encode()).hexdigest(),
                'poppler_version': 'test', 'comparison': None}
        return workfile.export_segments(QUERY, prepare_segments(RAW), self.root, slug='paper',
                                        raw=RAW, metadata=meta, gates_sha256=sha256_of(DEFAULT_PATH))

    def test_export_all_displayed_and_seal(self):
        path, seal = self.export()
        import hashlib
        payload = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), seal)
        self.assertEqual(len(payload['segments']), 3)
        self.assertNotIn('Reference text.', [s['text'] for s in payload['segments']])
        self.assertEqual(path.with_suffix('.sha256').read_text(encoding='utf-8').strip(), seal)
        self.assertEqual(payload['query']['query_id'], 'test-query')

    def test_records_digest_and_model_identity(self):
        workfile = self.module('workfile_min')
        records_module = self.module('records_min')
        digest = self.module('digest_min')
        path, seal = self.export()
        payload = workfile.load_export(path)
        selection = self.root / 'pick.jsonl'
        selection.write_text(json.dumps({'segment_id': payload['segments'][1]['segment_id'],
                             'kind': 'measurement', 'memo': '실측 요청 수를 보고한다.'}) + '\n', encoding='utf-8')
        picks = workfile.import_selections_min(selection, payload)
        from tools.verify.schema import validate
        for agent in ('codex', 'claude'):
            records = records_module.build_records(payload, picks, agent=agent, model='test-model')
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]['quote'], payload['segments'][1]['text'])
            self.assertEqual(validate(records[0]).status, 'pass')
            self.assertEqual(set(records[0]['conditions'].values()), {'unextracted'})
            self.assertEqual(records[0]['numbers'], [])
            self.assertIn(agent, records[0]['extractor_id'])
            rendered = digest.render(records, payload)
            self.assertIn('-> 실측 요청 수를 보고한다.', rendered)
            self.assertIn('[measurement · §1 · p.1]', rendered)
            self.assertEqual(rendered, digest.render(records, payload))
        path.write_text(path.read_text(encoding='utf-8') + ' ', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            workfile.load_export(path)

    def test_missing_field_rejects_entire_selection(self):
        workfile = self.module('workfile_min')
        path, _ = self.export()
        payload = workfile.load_export(path)
        selection = self.root / 'bad.jsonl'
        selection.write_text('{"segment_id":"extract_raw#0002.s1","kind":"measurement"}\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            workfile.import_selections_min(selection, payload)

    def test_bad_contract_blocks_cli_before_source_access(self):
        from extract.cli import main
        from tools.verify import thresholds
        data = thresholds.load()
        data['paragraph_unit']['split'] = 'unsupported'
        config = self.root / 'thresholds.json'
        config.write_text(json.dumps(data), encoding='utf-8')
        query = self.root / 'query.json'
        query.write_text(json.dumps(QUERY), encoding='utf-8')
        for command, extra in [('segment', ['--pdf', str(self.root / 'absent.pdf')]),
                               ('build', ['--selections', str(self.root / 'absent.jsonl'), '--agent', 'claude', '--model', 'test'])]:
            error = io.StringIO()
            with mock.patch.dict('os.environ', {'EXTRACT_THRESHOLDS_PATH': str(config)}), contextlib.redirect_stderr(error):
                self.assertEqual(main([command, '--query', str(query), '--slug', 'paper'] + extra), 1)
            self.assertIn('blank_line_block', error.getvalue())

    def test_path_identifiers_cannot_escape_output(self):
        workfile = self.module('workfile_min')
        for value in ('../escape', '/tmp/escape', 'a/b', '', '..'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                workfile.safe_name(value)

    def test_gold_recall_is_report_only(self):
        workfile = self.module('workfile_min')
        report = self.module('report_min')
        records_module = self.module('records_min')
        path, _ = self.export()
        payload = workfile.load_export(path)
        choices = [{'segment_id': payload['segments'][1]['segment_id'], 'kind': 'measurement', 'memo': '관측'}]
        records = records_module.build_records(payload, choices, agent='codex', model='test')
        gold = self.root / 'gold.md'
        gold.write_text('## 원문(그대로)\n### We measured twenty requests in the production system.\n', encoding='utf-8')
        result = report.build_report(payload, records, choices, RAW, codex_raw='different', gold=gold)
        self.assertEqual(result['checks']['codex_raw'], {'MISS': 1})
        self.assertEqual(result['checks']['g_recall_report_only']['covered_blocks'], 1)
        self.assertEqual(result['checks']['g_recall_report_only']['rate'], 1.0)

    def test_cli_roundtrip_and_stale_query_rejected(self):
        from extract.cli import main
        query = self.root / 'query.json'
        query.write_text(json.dumps(QUERY), encoding='utf-8')
        pdf = self.root / 'paper.pdf'
        pdf.write_bytes(b'%PDF fixture')
        import hashlib
        meta = {'pdf_sha256': hashlib.sha256(pdf.read_bytes()).hexdigest(),
                'extract_raw_sha256': hashlib.sha256(RAW.encode()).hexdigest(),
                'poppler_version': 'test', 'comparison': None}
        self.module('workfile_min')
        out = self.root / 'result'
        with mock.patch('extract.textlayer.extract_raw', return_value=(RAW, meta)), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(['segment', '--query', str(query), '--slug', 'paper', '--pdf', str(pdf), '--out-dir', str(out)]), 0)
        workfile = next(out.rglob('paper.segments.json'))
        payload = json.loads(workfile.read_text(encoding='utf-8'))
        picks = workfile.parent / 'paper.selections.jsonl'
        picks.write_text(json.dumps({'segment_id': payload['segments'][1]['segment_id'],
                         'kind': 'measurement', 'memo': '측정 결과이다.'}) + '\n', encoding='utf-8')
        command = ['build', '--query', str(query), '--slug', 'paper', '--workfile', str(workfile),
                   '--selections', str(picks), '--agent', 'codex', '--model', 'test-model']
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(command), 0)
        report = json.loads((workfile.parent / 'paper.run.json').read_text(encoding='utf-8'))
        self.assertEqual(report['checks']['l1_extract_raw'], {'exact': 1})
        self.assertEqual(report['selections']['count'], 1)
        self.assertTrue((workfile.parent / 'paper.records.jsonl').is_file())
        raw_path = workfile.parent / 'paper.extract_raw.txt'
        original = raw_path.read_bytes()
        raw_path.write_bytes(b'changed')
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            self.assertEqual(main(command), 1)
        self.assertIn('SHA-256', error.getvalue())
        raw_path.write_bytes(original)
        query.write_text(json.dumps(dict(QUERY, claim_text='A different claim.')), encoding='utf-8')
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(command), 1)


if __name__ == '__main__':
    unittest.main()
