"""Final v1 report: strict source gates and explicitly report-only comparisons."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Optional

from tools.verify.convert.gold import parse, load_rules
from tools.verify.l1_exists import Variant, check_quote
from tools.verify.paragraphs import Haystack, resolve, split_blocks
from .existence import require_exact
from .para_check import check as check_paragraphs
from .textlayer import compare_text

RUN_JSON_KEY_PATHS = [
    'sources.pdf_sha256', 'sources.extract_raw_sha256', 'sources.poppler_version',
    'sources.codex_raw_equal', 'sources.codex_raw_diff_lines', 'sources.codex_raw_first_diff',
    'sources.segmenter_ver', 'segments.blocks', 'segments.total', 'segments.removed_by_reason',
    'segments.displayed', 'segments.spanning', 'segments.body_words', 'segments.estimated_tokens',
    'selections.count', 'selections.kind_dist', 'selections.boundary_flags',
    'selections.spanning_selected', 'selections.short_block_count', 'selections.section_null_count',
    'checks.schema', 'checks.l1_extract_raw', 'checks.per_variant_grades',
    'checks.para_id_cross_check', 'checks.g_recall_report_only', 'gates_sha256']


def build_report(payload: dict, records: list[dict], selections: list[dict], raw: str,
                 codex_raw: Optional[str] = None, gold: Optional[Path] = None,
                 variants: Optional[dict] = None) -> dict:
    grades = Counter(require_exact(record['quote'], raw).grade for record in records)
    texts = dict(variants or {})
    if codex_raw is not None:
        texts['codex_raw'] = codex_raw
    variant_report, suspects = {}, []
    for name in ('codex_raw', 'codex_layout', 'claude_body', 'claude_column'):
        text = texts.get(name)
        if text is None:
            variant_report[name] = {'status': 'unavailable', 'grades': None, 'non_exact': []}
            continue
        rows = [(r['record_id'], check_quote(r['quote'], [Variant(name, text)]).grade) for r in records]
        variant_report[name] = {'status': 'report_only', 'grades': dict(Counter(g for _, g in rows)),
                               'non_exact': [{'record_id': i, 'grade': g} for i, g in rows if g != 'exact']}
        if name == 'claude_body':
            suspects = [i for i, g in rows if g == 'MISS']
    cross = check_paragraphs(records, raw)
    if not cross['ok']:
        raise ValueError('para_id 교차 확인 실패: ' + str(cross))
    reference = texts.get('codex_raw')
    comparison = compare_text(raw, reference) if reference is not None else None
    if comparison and comparison['equal']:
        own, other = split_blocks(raw, 'extract_raw'), split_blocks(reference, 'codex_raw')
        cross['codex_raw_alignment'] = {'status': 'checked', 'blocks': len(own),
                                        'ok': [(b.seq, b.text) for b in own] == [(b.seq, b.text) for b in other]}
    else:
        cross['codex_raw_alignment'] = {'status': 'deferred_sync' if reference is not None else 'unavailable'}
    recall = {'status': 'unavailable', 'rate': None}
    if gold is not None:
        parsed = parse(gold.read_text(encoding='utf-8'), load_rules())
        haystack = Haystack(split_blocks(raw, 'extract_raw'))
        gold_blocks = {seq for item in parsed.of('sentence') for seq in resolve(item.text, haystack)}
        selected = {int(para.rsplit('#', 1)[1]) for record in records for para in record['resolved_para_ids']}
        recall = {'status': 'report_only', 'gold_blocks': len(gold_blocks),
                  'covered_blocks': len(gold_blocks & selected),
                  'rate': len(gold_blocks & selected) / len(gold_blocks) if gold_blocks else None}
    comparison = comparison or {}
    sources = dict(payload['sources'], segmenter_ver=payload['segmenter_ver'],
                   codex_raw_equal=comparison.get('equal'),
                   codex_raw_diff_lines=comparison.get('diff_lines') if comparison.get('equal') is False else None,
                   codex_raw_first_diff=comparison.get('first_diff'))
    # Older P4a files lack body_words; subtract only generated spanning markers.
    body_words = payload.get('body_words', sum(len(s['text'].split()) - max(0, len(s['fragments']) - 1)
                                              for s in payload['segments']))
    segments = dict(payload['counts'], spanning=dict(payload['spanning'], emitted=payload['spanning']['formed']),
                    body_words=body_words, estimated_tokens=body_words * 1.3,
                    removed_reference_words=payload.get('removed_reference_words'),
                    reference_words_baseline=2248 if payload['slug'] == 'workload__year-in-llm-serving' else None,
                    boundary_warnings=payload['boundary_warnings'])
    return {'stage': 'v1', 'acceptance': 'pending_real_data', 'run_id': payload['run_id'],
            'query': dict(payload['query'], unconfirmed=not bool(payload['query'].get('confirmed_by'))),
            'sources': sources, 'segments': segments,
            'selections': {'count': len(records), 'kind_dist': dict(Counter(r['kind'] for r in records)),
                           'spanning_selected': sum(len(r['resolved_para_ids']) > 1 for r in records),
                           'short_block_count': sum(payload['block_words'][r['locator']['para_id']] < 20 for r in records),
                           'section_null_count': sum(r['locator']['section'] is None for r in records),
                           'boundary_flags': [{'segment_id': s['segment_id'], 'reason': s['boundary_reason']}
                                              for s in selections if s.get('boundary_flag')]},
            'checks': {'schema': {'pass': len(records), 'quarantine': 0},
                       'l1_extract_raw': dict(grades), 'codex_raw': variant_report['codex_raw']['grades'],
                       'per_variant_grades': variant_report, 'layout_suspect': suspects,
                       'para_id_cross_check': cross, 'g_recall_report_only': recall},
            'gates_sha256': payload['gates_sha256']}
