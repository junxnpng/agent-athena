"""P2 contracts: lossless segmentation and conservative source filtering."""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'verify'))
sys.path.insert(0, str(ROOT / 'extract'))


class SegmentationTests(unittest.TestCase):
    def test_lossless_abbreviations_and_offsets(self):
        from extract.segmenter import split_block_to_segments, load_config
        from tools.verify.paragraphs import Block
        text = 'Use e.g. 0.75 vs. 10^2, cf. Fig. 1 and Eq. 3. Next sentence!  Final fragment'
        segments = split_block_to_segments(Block('extract_raw', 1, text), load_config())
        self.assertEqual(len(segments), 3)
        self.assertEqual(''.join(s.text for s in segments), text)
        for i, segment in enumerate(segments, 1):
            self.assertEqual(segment.text, text[segment.char_start:segment.char_end])
            self.assertEqual(segment.segment_id, 'extract_raw#0001.s' + str(i))

    def test_heading_rules_pages_and_multiple_matches(self):
        from extract.pagesection import locate_blocks
        raw = 'Preface\n\n1 Introduction\n\nBody\n\n\f2 Background\n2.1 LLM Inference\n\n3\n\nToken Shape\n\n3.1 Production System. Body here.\n\n4 this is ordinary prose\n'
        blocks, headings = locate_blocks(raw)
        self.assertEqual([h.number for h in headings], ['1', '2', '2.1', '3', '3.1'])
        self.assertIsNone(blocks[0].section)
        self.assertEqual(blocks[2].section, '§1')
        self.assertEqual(blocks[3].section, '§2.1')
        self.assertEqual(blocks[3].page, 2)
        self.assertEqual(blocks[4].section, '§3')
        self.assertEqual(blocks[5].section, '§3')
        self.assertEqual(blocks[-1].section, '§3.1')
        for block in blocks:
            self.assertEqual(raw[block.char_start:block.char_end], block.text)

    def test_repeated_text_offsets_and_embedded_page_break(self):
        from extract.pagesection import locate_blocks
        blocks, _ = locate_blocks('Same\n\n\fSame\n\nSame')
        self.assertEqual([b.char_start for b in blocks], [0, 7, 13])
        with self.assertRaisesRegex(ValueError, 'form feed'):
            locate_blocks('first\fsecond')

    def test_whole_block_filter_and_accounting(self):
        from extract.pipeline import segment_text
        raw = ('Conference Header\n\n1 Introduction\n\nData 12 34\n\narXiv:2608.13573v2\n\n'
               '\fConference Header\n\nBody has arXiv:2608.13573v2 embedded. Keep it.\n\n'
               'references\n\nA citation. Another citation.')
        result = segment_text(raw, arxiv_stamp='arXiv:2608.13573v2')
        reasons = result['removed_by_reason']
        self.assertEqual(reasons['running_header'], 2)
        self.assertEqual(reasons['arxiv_stamp'], 1)
        self.assertEqual(reasons['references'], 3)
        self.assertEqual(len(result['kept']) + len(result['removed']), len(result['segments']))
        self.assertTrue(any('Data 12 34' in s.text for s in result['kept']))
        self.assertTrue(any('embedded' in s.text for s in result['kept']))
        self.assertTrue(result['boundary_warnings'])

    def test_text_comparison_byte_offsets(self):
        from extract.textlayer import compare_text
        self.assertEqual(compare_text('한a', '한b')['first_diff'], 3)
        self.assertEqual(compare_text('a', 'ab')['first_diff'], 1)
        self.assertEqual(compare_text('same', 'same'),
                         {'equal': True, 'diff_lines': 0, 'first_diff': None})

    def test_pdf_process_metadata_and_errors(self):
        from extract.textlayer import extract_raw
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'sample.pdf'
            path.write_bytes(b'%PDF-synthetic')
            with mock.patch('extract.textlayer._run', side_effect=['pdftotext version test', 'Hello\n\f']) as run:
                text, meta = extract_raw(path, codex_raw='Hello\n\f')
            self.assertEqual(text, 'Hello\n\f')
            self.assertEqual(meta['pdf_sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(meta['extract_raw_sha256'], hashlib.sha256(text.encode()).hexdigest())
            self.assertTrue(meta['comparison']['equal'])
            self.assertEqual(run.call_args.args[0], ['pdftotext', '-q', str(path.resolve()), '-'])


    def test_real_poppler_and_failure(self):
        from extract.textlayer import extract_raw, _run
        if not shutil.which('pdftotext'):
            self.skipTest('Poppler 미설치: 실제 PDF 실행 생략')
        stream = b'BT /F1 12 Tf 72 700 Td (Hello extraction.) Tj ET'
        objects = [b'<< /Type /Catalog /Pages 2 0 R >>',
                   b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
                   b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
                   b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
                   b'<< /Length ' + str(len(stream)).encode() + b' >>\nstream\n' + stream + b'\nendstream']
        pdf = b'%PDF-1.4\n'
        offsets = [0]
        for i, obj in enumerate(objects, 1):
            offsets.append(len(pdf))
            pdf += str(i).encode() + b' 0 obj\n' + obj + b'\nendobj\n'
        start = len(pdf)
        pdf += b'xref\n0 6\n0000000000 65535 f \n'
        pdf += b''.join(('%010d 00000 n \n' % offset).encode() for offset in offsets[1:])
        pdf += b'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n' + str(start).encode() + b'\n%%EOF\n'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.pdf'
            path.write_bytes(pdf)
            raw, meta = extract_raw(path)
            self.assertIn('Hello extraction.', raw)
            self.assertEqual(raw.count('\f'), 1)
            self.assertIn('version', meta['poppler_version'])
            path.write_bytes(b'invalid pdf')
            with self.assertRaises(RuntimeError):
                extract_raw(path)
        with self.assertRaisesRegex(RuntimeError, '시간 제한'):
            _run([sys.executable, '-c', 'import time; time.sleep(10)'], timeout=0.05)

    def test_all_configured_abbreviations(self):
        from extract.segmenter import load_config, split_block_to_segments
        from tools.verify.paragraphs import Block
        cfg = load_config()
        for abbreviation in cfg['abbreviations']:
            with self.subTest(abbreviation=abbreviation):
                text = 'See ' + abbreviation + ' example. Next sentence.'
                pieces = split_block_to_segments(Block('extract_raw', 1, text), cfg)
                self.assertEqual(len(pieces), 2)
                self.assertEqual(''.join(s.text for s in pieces), text)

    def test_gold_corpus_acceptance(self):
        from extract.textlayer import extract_raw
        from extract.pipeline import segment_text
        from tools.verify.paragraphs import split_blocks
        root = os.environ.get('KVCPOOL')
        if not root:
            self.skipTest('KVCPOOL 원본 논문 부재: P2 gold 인수 시험 미완료')
        papers = Path(root) / 'papers'
        pdf = papers / 'workload__year-in-llm-serving.pdf'
        reference = papers / 'codex_source_text/codex_workload__year-in-llm-serving.txt'
        raw, meta = extract_raw(pdf, codex_raw=reference.read_bytes().decode('utf-8'))
        self.assertEqual(meta['pdf_sha256'], '4156391d98baafc6201319cc01015fa4bebdfef9740ade64110565fcb041a144')
        self.assertTrue(meta['comparison']['equal'], meta['comparison'])
        self.assertEqual(raw.count('\f'), 16)
        result = segment_text(raw)
        expected = (ROOT / 'tests/fixtures/gold_section_headings.txt').read_text(encoding='utf-8').splitlines()
        self.assertEqual([h.number + ' ' + h.title for h in result['headings']], expected)
        self.assertEqual(result['blocks'][34].section, '§1')
        self.assertTrue(result['blocks'][34].text.startswith('highly skewed popularity'))
        self.assertEqual(result['blocks'][36].section, '§2.1')
        self.assertEqual(result['blocks'][566].section, '§7.1')
        self.assertEqual(len({b.section for b in result['blocks'] if b.section}), 19)
        self.assertEqual([b.text for b in result['blocks']],
                         [b.text for b in split_blocks(reference.read_text(encoding='utf-8'), 'codex_raw')])
        for block in result['blocks']:
            pieces = [s for s in result['segments'] if s.para_id == block.para_id]
            self.assertEqual(''.join(s.text for s in pieces), block.text)
        for segment in result['segments']:
            self.assertTrue(1 <= segment.page <= 16)
            self.assertEqual(raw[segment.char_start:segment.char_end], segment.text)


if __name__ == '__main__':
    unittest.main()
