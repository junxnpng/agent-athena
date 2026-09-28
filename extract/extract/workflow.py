"""Local file orchestration for the v1 extractor; no automatic model calls."""
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
    from tools.verify.convert.common import variant_paths
    pdf = args.pdf
    references = {}
    if pdf is None or args.source_root:
        root = source_root(args.source_root)
        if pdf is None:
            pdf = root / 'papers' / (slug + '.pdf')
        references = {name: path for name, path in variant_paths(root, slug).items() if path is not None}
    if args.codex_raw is not None:
        references['codex_raw'] = args.codex_raw
    texts = {name: path.read_bytes().decode('utf-8', errors='replace') for name, path in references.items()}
    title = args.title.strip()
    if len(title.splitlines()) > 1:
        raise ValueError('논문 제목은 한 줄이어야 합니다')
    raw, meta = textlayer.extract_raw(pdf, texts.get('codex_raw'))
    prepared = pipeline.prepare_segments(raw, args.arxiv_stamp)
    meta['variant_sha256'] = {name: hashlib.sha256(text.encode('utf-8')).hexdigest()
                              for name, text in texts.items()}
    meta['codex_raw_sha256'] = meta['variant_sha256'].get('codex_raw')
    out = args.out_dir if args.out_dir else RESULTS_DIR / loaded['query_id']
    path, seal = workfile_min.export_segments(loaded, prepared, out, slug=slug, raw=raw,
                                             metadata=meta, gates_sha256=gates.sha256_of(args.gates), title=title)
    for name, text in texts.items():
        (path.parent / (slug + '.' + name + '.txt')).write_bytes(text.encode('utf-8'))
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
    variants = {name: _read_checked(path.parent / (slug + '.' + name + '.txt'), sha)
                for name, sha in payload['sources'].get('variant_sha256', {}).items()}
    choices = workfile_min.import_selections_min(args.selections, payload)
    records = records_min.build_records(payload, choices, agent=args.agent, model=args.model)
    gold = args.gold
    if gold is None and slug == 'workload__year-in-llm-serving':
        gold = Path(__file__).resolve().parents[2] / 'verify/gold/workload__year-in-llm-serving_handpicked.md'
    report = report_min.build_report(payload, records, choices, raw, codex_raw, gold, variants)
    payload['extractor_id'] = f'{args.agent}-session:{args.model}'
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
    return {'status': '빌드 완료', 'stage': 'v1', 'records': len(records),
            'report': str(path.parent / (slug + '.run.json')),
            'digest': str(path.parent / (slug + '.md'))}
