"""Local file orchestration for the P4a prototype; no automatic model calls."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import os

from . import digest_min, gates, pipeline, records_min, report_min, textlayer, workfile_min
from .paths import RESULTS_DIR, source_root


def segment(args, loaded: dict) -> dict:
    gates.assert_paragraph_unit_split()
    slug = workfile_min.safe_name(args.slug)
    workfile_min.safe_name(loaded['query_id'])
    reference = args.codex_raw
    pdf = args.pdf
    if pdf is None:
        root = source_root(args.source_root)
        pdf = root / 'papers' / (slug + '.pdf')
        if reference is None:
            candidate = root / 'papers/codex_source_text' / ('codex_' + slug + '.txt')
            reference = candidate if candidate.is_file() else None
    codex_raw = reference.read_bytes().decode('utf-8', errors='replace') if reference else None
    raw, meta = textlayer.extract_raw(pdf, codex_raw)
    prepared = pipeline.prepare_segments(raw, args.arxiv_stamp)
    meta['codex_raw_sha256'] = hashlib.sha256(codex_raw.encode('utf-8')).hexdigest() if codex_raw is not None else None
    out = args.out_dir if args.out_dir else RESULTS_DIR / loaded['query_id']
    path, seal = workfile_min.export_segments(loaded, prepared, out, slug=slug, raw=raw,
                                             metadata=meta, gates_sha256=gates.sha256_of(args.gates))
    if codex_raw is not None:
        (path.parent / (slug + '.codex_raw.txt')).write_bytes(codex_raw.encode('utf-8'))
    return {'status': '선택 대기', 'workfile': str(path), 'sha256': seal,
            'selections': str(path.parent / (slug + '.selections.jsonl')),
            'displayed': len(prepared['displayed']),
            'instructions': str(Path(__file__).resolve().parents[1] / 'SELECTION.md')}


def _read_checked(path: Path, expected: str) -> str:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f'원문 SHA-256 불일치: {path.name}')
    return data.decode('utf-8')


def build(args, loaded: dict) -> dict:
    gates.assert_paragraph_unit_split()
    slug = workfile_min.safe_name(args.slug)
    path = args.workfile or args.selections.parent / (slug + '.segments.json')
    payload = workfile_min.load_export(path)
    if payload['query'] != loaded or payload['slug'] != slug:
        raise ValueError('봉인된 질의 또는 논문과 현재 입력이 다릅니다')
    if payload['gates_sha256'] != gates.sha256_of(args.gates):
        raise ValueError('봉인 뒤 게이트가 변경되었습니다')
    raw = _read_checked(path.parent / (slug + '.extract_raw.txt'), payload['sources']['extract_raw_sha256'])
    codex_sha = payload['sources'].get('codex_raw_sha256')
    codex_raw = _read_checked(path.parent / (slug + '.codex_raw.txt'), codex_sha) if codex_sha else None
    choices = workfile_min.import_selections_min(args.selections, payload)
    records = records_min.build_records(payload, choices, agent=args.agent, model=args.model)
    gold = args.gold
    if gold is None and slug == 'workload__year-in-llm-serving':
        gold = Path(__file__).resolve().parents[2] / 'verify/gold/workload__year-in-llm-serving_handpicked.md'
    report = report_min.build_report(payload, records, choices, raw, codex_raw, gold)
    files = {slug + '.records.jsonl': ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records),
             slug + '.md': digest_min.render(records, payload),
             slug + '.run.json': json.dumps(report, ensure_ascii=False, indent=2) + '\n',
             'slice-facts-' + payload['run_id'] + '.json': json.dumps(report, ensure_ascii=False, indent=2) + '\n'}
    # Build validates everything before publishing any artifact. Each file is replaced atomically.
    for name, content in files.items():
        target = path.parent / name
        if target.exists():
            raise ValueError(f'기존 결과를 덮어쓰지 않습니다: {target}; 새 segment 실행이 필요합니다')
    for name, content in files.items():
        with tempfile.NamedTemporaryFile(dir=path.parent, mode='w', encoding='utf-8', delete=False) as temp:
            temporary = Path(temp.name)
            temp.write(content)
        try:
            os.replace(str(temporary), str(path.parent / name))
        finally:
            temporary.unlink(missing_ok=True)
    return {'status': '빌드 완료', 'stage': 'P4a-prototype', 'records': len(records),
            'report': str(path.parent / (slug + '.run.json')),
            'digest': str(path.parent / (slug + '.md'))}
