"""Final extraction contracts: rejected selections, provenance and diagnostics."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'verify'))
sys.path.insert(0, str(ROOT / 'extract'))
from extract import workfile_min, records_min, digest_min, report_min
from extract.pipeline import prepare_segments

LEFT = 'The production workload shows that many different applications and users send requests to language model platforms which serve models with'
RIGHT = 'highly skewed popularity across users and deployments because a small group of models receives most requests throughout the entire observation period.'
RAW = '1 Introduction\n\n' + LEFT + '\n\n\f' + RIGHT + '\n\nReferences\n\nA reference.'
QUERY = {'query_id': 'test', 'topic': 'requests', 'claim_text': 'Requests vary.', 'source': 'test'}


class FinalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.meta = {'pdf_sha256': 'a' * 64, 'extract_raw_sha256': hashlib.sha256(RAW.encode()).hexdigest(),
                     'poppler_version': 'test', 'comparison': None}
        self.path, _ = workfile_min.export_segments(QUERY, prepare_segments(RAW), self.root,
            slug='paper', raw=RAW, metadata=self.meta, gates_sha256='b' * 64)
        self.payload = workfile_min.load_export(self.path)
        self.pick = {'segment_id': 'extract_raw#0002.s1', 'kind': 'measurement', 'memo': '요청 분포의 관측이다.'}

    def records(self):
        return records_min.build_records(self.payload, [self.pick], agent='codex', model='test')

    def test_six_rejections_have_stable_codes_and_preserve_input(self):
        cases = [('unknown_id', dict(self.pick, segment_id='unknown')),
                 ('removed_id', dict(self.pick, segment_id=self.payload['removed_ids'][0])),
                 ('duplicate_id', self.pick), ('invalid_kind', dict(self.pick, kind='supports')),
                 ('invalid_memo', dict(self.pick, memo='two\nlines')),
                 ('unexpected_field', dict(self.pick, quote='invented'))]
        for code, row in cases:
            with self.subTest(code=code):
                path = self.root / (code + '.jsonl')
                source = json.dumps(self.pick) + '\n' + json.dumps(row) + '\n'
                path.write_text(source, encoding='utf-8')
                with self.assertRaises(ValueError) as caught:
                    workfile_min.import_selections_min(path, self.payload)
                self.assertEqual(getattr(caught.exception, 'code', None), code)
                self.assertEqual(getattr(caught.exception, 'line_no', None), 2)
                logs = list(self.root.glob(code + '.jsonl.rej-*.log'))
                self.assertEqual(len(logs), 1)
                self.assertEqual(json.loads(logs[0].read_text())['code'], code)
                self.assertEqual(path.read_text(), source)

    def test_digest_uses_record_provenance_for_page_marker_and_query(self):
        records = self.records()
        self.assertEqual(records[0].get('fragment_pages'), [1, 2])
        self.assertEqual(records[0].get('query'), QUERY)
        rendered = digest_min.render(records)
        self.assertIn('⏎p.2', rendered)
        self.assertIn('unconfirmed', rendered)
        quote_line = next(line for line in rendered.splitlines() if '⏎p.2' in line)
        self.assertEqual(re.sub(r'⏎p\.\d+', '[…]', quote_line), ' '.join(records[0]['quote'].split()))
        self.assertEqual(rendered, digest_min.render(json.loads(json.dumps(records))))

    def test_report_has_final_fields_and_honest_missing_inputs(self):
        report = report_min.build_report(self.payload, self.records(), [self.pick], RAW)
        self.assertEqual(report['stage'], 'v1')
        self.assertEqual(report['acceptance'], 'pending_real_data')
        self.assertTrue(report['query']['unconfirmed'])
        self.assertEqual(report['segments']['body_words'], len((LEFT + ' ' + RIGHT).split()) + 2)
        self.assertEqual(report['segments']['estimated_tokens'], report['segments']['body_words'] * 1.3)
        self.assertEqual(report['selections']['spanning_selected'], 1)
        self.assertEqual(report['selections']['section_null_count'], 0)
        self.assertEqual(report['checks']['per_variant_grades']['claude_body']['status'], 'unavailable')
        self.assertTrue(report['checks']['para_id_cross_check']['ok'])
        self.assertIsNone(report['sources']['codex_raw_diff_lines'])
        self.assertEqual(report['segments']['removed_reference_words'], 3)
        self.assertEqual(len(report_min.RUN_JSON_KEY_PATHS), 26)
        for key in report_min.RUN_JSON_KEY_PATHS:
            current = report
            for part in key.split('.'):
                current = current[part]

    def test_variant_miss_is_report_only_and_identifies_suspect(self):
        report = report_min.build_report(self.payload, self.records(), [self.pick], RAW,
                                         variants={'codex_raw': RAW, 'claude_body': 'Other content.'})
        variants = report['checks']['per_variant_grades']
        self.assertEqual(variants['codex_raw']['grades'], {'exact': 1})
        self.assertEqual(variants['claude_body']['grades'], {'MISS': 1})
        self.assertEqual(report['checks']['layout_suspect'], [self.records()[0]['record_id']])

    def test_wrong_paragraph_rejected_but_repetition_and_short_are_reported(self):
        from extract.para_check import check
        quote = 'Repeated observations are reported in this production workload.'
        raw = quote + '\n\n' + quote + '\n\nTiny.'
        rows = [{'record_id': 'repeat', 'quote': quote, 'locator': {'para_id': 'extract_raw#0002'}},
                {'record_id': 'short', 'quote': 'Tiny.', 'locator': {'para_id': 'extract_raw#0003'}}]
        result = check(rows, raw)
        self.assertTrue(result['ok'])
        self.assertEqual(result['repeated_first_hit_mismatch'], ['repeat'])
        self.assertEqual(result['empty_resolve_short'], ['short'])
        rows[0]['locator']['para_id'] = 'extract_raw#0003'
        self.assertFalse(check(rows, raw)['ok'])

    def test_digest_sorts_by_numeric_document_position(self):
        record = self.records()[0]
        later = copy.deepcopy(record)
        later.update(record_id='extract_raw#0010.s1@hash', quote='Later.', fragment_pages=[3], quote_fragments=['Later.'], claim_text='나중')
        later['locator'].update(page=3, para_id='extract_raw#0010')
        rendered = digest_min.render([later, record])
        self.assertLess(rendered.index('⏎p.2'), rendered.index('Later.'))

    def test_cli_snapshots_variants_rejects_tampering_and_builds_empty(self):
        import contextlib
        import io
        from unittest import mock
        from extract.cli import main
        from tools.verify.convert.common import variant_paths, sources
        source = self.root / 'source'
        source.mkdir()
        for name, template in sources()['variants'].items():
            target = source / template.format(slug='paper')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(RAW if name == 'codex_raw' else 'Other text.', encoding='utf-8')
        query = self.root / 'query.json'
        query.write_text(json.dumps(QUERY), encoding='utf-8')
        with mock.patch('extract.textlayer.extract_raw', return_value=(RAW, self.meta)), contextlib.redirect_stdout(io.StringIO()):
            code = main(['segment', '--query', str(query), '--slug', 'paper', '--source-root', str(source),
                         '--out-dir', str(self.root / 'cli'), '--title', 'A Research Paper'])
        self.assertEqual(code, 0)
        work = next((self.root / 'cli').rglob('*.segments.json'))
        payload = workfile_min.load_export(work)
        self.assertEqual(payload['title'], 'A Research Paper')
        snapshot = work.parent / 'paper.claude_body.txt'
        self.assertTrue(snapshot.is_file())
        picks = work.parent / 'paper.selections.jsonl'
        picks.write_text('', encoding='utf-8')
        command = ['build', '--query', str(query), '--slug', 'paper', '--workfile', str(work),
                   '--selections', str(picks), '--agent', 'claude', '--model', 'test']
        snapshot.write_text('tampered', encoding='utf-8')
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(command), 1)
        self.assertFalse((work.parent / 'paper.run.json').exists())
        snapshot.write_text('Other text.', encoding='utf-8')
        # Build uses the sealed snapshots even if originals disappear.
        for variant in variant_paths(source, 'paper').values():
            variant.unlink()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(command), 0)
        report = json.loads((work.parent / 'paper.run.json').read_text())
        self.assertEqual(report['stage'], 'v1')
        self.assertEqual(report['selections']['count'], 0)
        self.assertEqual(report['checks']['per_variant_grades']['claude_body']['status'], 'report_only')
        digest = (work.parent / 'paper.md').read_text()
        self.assertIn('A Research Paper', digest)
        self.assertIn('claude-session:test', digest)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(command), 1)

    def test_malformed_selection_and_repeated_rejections_leave_evidence(self):
        path = self.root / 'malformed.jsonl'
        for source in ('{', '[]', '{}', json.dumps(dict(self.pick, kind=[])),
                       json.dumps(dict(self.pick, boundary_flag=True))):
            path.write_text(source, encoding='utf-8')
            with self.assertRaises(ValueError):
                workfile_min.import_selections_min(path, self.payload)
        self.assertEqual(len(list(self.root.glob('malformed.jsonl.rej-*.log'))), 5)

    def test_literal_ellipsis_is_not_replaced_as_a_page_boundary(self):
        records = self.records()
        record = records[0]
        record['quote'] = 'Literal […] notation […] second page.'
        record['quote_fragments'] = ['Literal […] notation', 'second page.']
        rendered = digest_min.render(records)
        self.assertIn('Literal […] notation ⏎p.2 second page.', rendered)

    def test_memo_trailing_newline_is_rejected(self):
        path = self.root / 'newline.jsonl'
        path.write_text(json.dumps(dict(self.pick, memo='메모\n')) + '\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            workfile_min.import_selections_min(path, self.payload)

    def test_gold_empty_and_zero_coverage_are_report_only(self):
        for text, rate in [('## 원문(그대로)\n### \n', None), ('## 원문(그대로)\n### A reference.\n', None),
                           ('## 원문(그대로)\n### ' + RIGHT + '\n', 0.0)]:
            gold = self.root / 'gold.md'
            gold.write_text(text, encoding='utf-8')
            report = report_min.build_report(self.payload, [], [], RAW, gold=gold)
            self.assertEqual(report['checks']['g_recall_report_only']['rate'], rate)
            self.assertEqual(report['checks']['schema'], {'pass': 0, 'quarantine': 0})


if __name__ == '__main__':
    unittest.main()
