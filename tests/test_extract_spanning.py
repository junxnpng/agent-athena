"""Spanning preserves both source slices and never absorbs intervening blocks."""
from __future__ import annotations

import ast
from pathlib import Path
import os
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'verify'))
sys.path.insert(0, str(ROOT / 'extract'))

LEFT = 'This production workload contains many different requests and reveals that modern language model platforms serve many different models with'
RIGHT = 'highly skewed popularity across users and deployments because a small group of models receives most requests throughout the entire observation period.'


class SpanningTests(unittest.TestCase):
    def run_pipeline(self, raw):
        from extract import pipeline
        self.assertTrue(hasattr(pipeline, 'prepare_segments'), 'P3 pipeline is not implemented')
        return pipeline.prepare_segments(raw)

    def test_span_skips_header_and_caption_without_absorbing_them(self):
        raw = '1 Introduction\n\n' + LEFT + '\n\n\fConference Header\n\nTable 1. A table caption with more than twenty words that must never be included inside a source quotation selected from the actual paper body.\n\n' + RIGHT
        result = self.run_pipeline(raw)
        span = next(s for s in result['displayed'] if len(s.resolved_para_ids) == 2)
        self.assertEqual(span.text, LEFT + ' […] ' + RIGHT)
        self.assertEqual(span.section, '§1')
        self.assertEqual(span.page, 1)
        self.assertEqual(span.segment_id, 'extract_raw#0002.s1')
        self.assertEqual(span.resolved_para_ids, ('extract_raw#0002', 'extract_raw#0005'))
        self.assertEqual([f.page for f in span.fragments], [1, 2])
        for fragment in span.fragments:
            self.assertEqual(raw[fragment.char_start:fragment.char_end], fragment.text)
        self.assertTrue(any(s.text.startswith('Table 1.') for s in result['displayed']))
        self.assertTrue(any(s.text == 'Conference Header' for s in result['displayed']))
        self.assertFalse(any(s.segment_id == 'extract_raw#0005.s1' for s in result['displayed']))
        self.assertEqual(len(result['displayed']), len(result['kept']) - result['spanning']['formed'])
        self.assertTrue(all(check.grade == 'exact' for check in result['l1']))

    def test_numeric_table_is_not_a_continuation(self):
        table = 'Model Requests\n' + ' '.join(str(i) for i in range(30))
        result = self.run_pipeline(LEFT + '\n\n' + table + '\n\n' + RIGHT)
        span = next(s for s in result['displayed'] if len(s.fragments) == 2)
        self.assertEqual(span.text, LEFT + ' […] ' + RIGHT)
        self.assertTrue(any(s.text == table for s in result['displayed']))

    def test_finished_sentence_section_boundary_and_references_do_not_join(self):
        for middle, left in [('\n\n', LEFT + '.'), ('\n\n2 Background\n\n', LEFT),
                             ('\n\nReferences\n\n', LEFT)]:
            with self.subTest(middle=middle):
                result = self.run_pipeline('1 Introduction\n\n' + left + middle + RIGHT)
                self.assertEqual(result['spanning']['formed'], 0)

    def test_one_source_fragment_cannot_be_reused(self):
        result = self.run_pipeline(LEFT + '\n\n' + LEFT + '\n\n' + RIGHT)
        used = [f.segment_id for s in result['displayed'] for f in s.fragments]
        self.assertEqual(len(used), len(set(used)))

    def test_real_library_exact_mutation_and_codex_reporting(self):
        from extract import pipeline
        self.assertTrue(hasattr(pipeline, 'prepare_segments'), 'P3 pipeline is not implemented')
        from extract.existence import check_against_raw, check_against_codex, require_exact
        raw = LEFT + '\n\n' + RIGHT
        quote = LEFT + ' […] ' + RIGHT
        with mock.patch('sqlite3.connect', side_effect=AssertionError('ledger access')):
            self.assertEqual(check_against_raw(quote, raw).grade, 'exact')
            require_exact(quote, raw)
            mutated = quote.replace('production', 'prXduction')
            self.assertNotEqual(check_against_raw(mutated, raw).grade, 'exact')
            with self.assertRaisesRegex(ValueError, 'exact'):
                require_exact(mutated, raw)
            self.assertEqual(check_against_codex(quote, 'unrelated source').grade, 'MISS')
            self.assertEqual(check_against_codex(quote, raw).variant, 'codex_raw')

    def test_extractor_has_no_ledger_calls_or_imports(self):
        forbidden = {'ledger', 'begin', 'load_variants', 'register'}
        for path in (ROOT / 'extract/extract').glob('*.py'):
            tree = ast.parse(path.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for alias in node.names:
                        self.assertNotIn(alias.name.split('.')[-1], forbidden, str(path))
                elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    self.assertNotIn(node.func.attr, forbidden, str(path))

    def test_nonlexical_display_fragment_is_preserved_for_selection(self):
        result = self.run_pipeline('Symbols\n\n***\n\nA readable sentence.')
        self.assertTrue(any(s.text == '***' for s in result['displayed']))
        self.assertTrue(any(check.grade == 'MISS' for check in result['l1']))

    def test_gold_line93_span(self):
        root = os.environ.get('KVCPOOL')
        if not root:
            self.skipTest('KVCPOOL 없음: P3 line93 인수 미완료')
        from extract.textlayer import extract_raw
        raw, _ = extract_raw(Path(root) / 'papers/workload__year-in-llm-serving.pdf')
        result = self.run_pipeline(raw)
        span = next(s for s in result['displayed'] if 'modern LLM platforms serve many models with' in s.text)
        self.assertEqual(len(span.fragments), 2)
        self.assertEqual(span.section, '§1')
        self.assertNotIn('Table 1', span.text)
        from extract.existence import check_against_raw
        self.assertEqual(check_against_raw(span.text, raw).grade, 'exact')


if __name__ == '__main__':
    unittest.main()
