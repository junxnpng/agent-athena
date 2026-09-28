"""Sealed whole-document export and all-or-nothing selection input."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
import uuid

from tools.verify.schema import KINDS


def safe_name(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', value):
        raise ValueError('식별자는 영문·숫자로 시작하고 영문·숫자·밑줄·점·하이픈만 포함해야 합니다')
    return value


def export_segments(query: dict, segments: dict, out_dir: Path, *, slug: str,
                    raw: str, metadata: dict, gates_sha256: str, title: str = '') -> tuple[Path, str]:
    slug = safe_name(slug)
    query_id = safe_name(query['query_id'])
    run_id = f'{query_id}-{uuid.uuid4().hex[:12]}-{slug}'
    directory = Path(out_dir) / run_id
    payload = {'protocol_ver': 'paper-extract-v1', 'run_id': run_id, 'slug': slug,
               'title': title or slug, 'query': query, 'sources': metadata, 'gates_sha256': gates_sha256,
               'segmenter_ver': segments['segmenter_ver'],
               'segments': [asdict(s) for s in segments['displayed']],
               'counts': {'blocks': len(segments['blocks']), 'total': len(segments['segments']),
                          'kept_before_spanning': len(segments['kept']),
                          'removed_by_reason': segments['removed_by_reason'],
                          'displayed': len(segments['displayed'])},
               'spanning': segments['spanning'],
               'removed_reference_words': segments['removed_reference_words'],
               'body_words': sum(len(s.text.split()) for s in segments['kept']),
               'boundary_warnings': segments['boundary_warnings'],
               'removed_ids': [r['segment'].segment_id for r in segments['removed']],
               'block_words': {b.para_id: b.word_count for b in segments['blocks']}}
    data = (json.dumps(payload, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    seal = hashlib.sha256(data).hexdigest()
    directory.mkdir(parents=True, exist_ok=False)
    path = directory / f'{slug}.segments.json'
    path.write_bytes(data)
    path.with_suffix('.sha256').write_text(seal + '\n', encoding='utf-8')
    (directory / f'{slug}.extract_raw.txt').write_bytes(raw.encode('utf-8'))
    return path, seal


def load_export(path: Path) -> dict:
    path = Path(path)
    data = path.read_bytes()
    seal = path.with_suffix('.sha256').read_text(encoding='utf-8').strip()
    if hashlib.sha256(data).hexdigest() != seal:
        raise ValueError('segments SHA-256 불일치')
    payload = json.loads(data)
    if payload.get('protocol_ver') != 'paper-extract-v1':
        raise ValueError('지원하지 않는 선택 파일 프로토콜')
    safe_name(payload['slug'])
    safe_name(payload['run_id'])
    return payload


class SelectionError(ValueError):
    """Stable rejection code with the first offending input line."""

    def __init__(self, code: str, line_no: int):
        self.code, self.line_no = code, line_no
        super().__init__(f'선택 파일 {line_no}행: {code}')


def _validate_selection(row, known: set, removed: set, seen: set, line_no: int) -> None:
    def reject(code):
        raise SelectionError(code, line_no)
    if not isinstance(row, dict) or not {'segment_id', 'kind', 'memo'} <= row.keys():
        reject('invalid_format')
    if set(row) - {'segment_id', 'kind', 'memo', 'boundary_flag', 'boundary_reason'}:
        reject('unexpected_field')
    if not isinstance(row['kind'], str) or row['kind'] not in KINDS:
        reject('invalid_kind')
    if not isinstance(row['memo'], str) or not row['memo'].strip() or any(c in row['memo'] for c in '\n\r\v\f\x85\u2028\u2029'):
        reject('invalid_memo')
    if 'boundary_flag' in row and not isinstance(row['boundary_flag'], bool):
        reject('invalid_format')
    if ('boundary_reason' in row and not isinstance(row['boundary_reason'], str)
            or row.get('boundary_flag') and not row.get('boundary_reason', '').strip()):
        reject('invalid_format')
    identifier = row['segment_id']
    if not isinstance(identifier, str):
        reject('unknown_id')
    if identifier in removed:
        reject('removed_id')
    if identifier not in known:
        reject('unknown_id')
    if identifier in seen:
        reject('duplicate_id')


def import_selections_min(path: Path, payload: dict) -> list[dict]:
    path = Path(path)
    known = {s['segment_id'] for s in payload['segments']}
    removed = set(payload['removed_ids'])
    seen = set()
    selections = []
    try:
        for line_no, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            try:
                row = json.loads(line)
            except ValueError as exc:
                raise SelectionError('invalid_format', line_no) from exc
            _validate_selection(row, known, removed, seen, line_no)
            seen.add(row['segment_id'])
            selections.append(row)
    except SelectionError as exc:
        # Exclusive creation preserves all previous rejection evidence.
        index = 1
        while True:
            log = path.with_name(path.name + f'.rej-{index}.log')
            try:
                with log.open('x', encoding='utf-8') as stream:
                    json.dump({'code': exc.code, 'line': exc.line_no}, stream)
                break
            except FileExistsError:
                index += 1
        raise
    return selections
