"""Sealed whole-document export and minimal all-or-nothing selection input."""
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
                    raw: str, metadata: dict, gates_sha256: str) -> tuple[Path, str]:
    slug = safe_name(slug)
    query_id = safe_name(query['query_id'])
    run_id = f'{query_id}-{uuid.uuid4().hex[:12]}-{slug}'
    directory = Path(out_dir) / run_id
    payload = {'protocol_ver': 'paper-extract-v1', 'run_id': run_id, 'slug': slug,
               'query': query, 'sources': metadata, 'gates_sha256': gates_sha256,
               'segmenter_ver': segments['segmenter_ver'],
               'segments': [asdict(s) for s in segments['displayed']],
               'counts': {'blocks': len(segments['blocks']), 'total': len(segments['segments']),
                          'kept_before_spanning': len(segments['kept']),
                          'removed_by_reason': segments['removed_by_reason'],
                          'displayed': len(segments['displayed'])},
               'spanning': segments['spanning'],
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


def import_selections_min(path: Path, payload: dict) -> list[dict]:
    known = {s['segment_id'] for s in payload['segments']}
    seen = set()
    selections = []
    for line_no, line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(), 1):
        try:
            row = json.loads(line)
            if not isinstance(row, dict) or not {'segment_id', 'kind', 'memo'} <= row.keys():
                raise ValueError('필수 필드 누락')
            if set(row) - {'segment_id', 'kind', 'memo', 'boundary_flag', 'boundary_reason'}:
                raise ValueError('허용하지 않는 필드')
            if not isinstance(row['segment_id'], str) or row['segment_id'] not in known or row['segment_id'] in seen:
                raise ValueError('알 수 없거나 중복된 세그먼트')
            if row['kind'] not in KINDS or not isinstance(row['memo'], str) or not row['memo'].strip():
                raise ValueError('kind 또는 memo 오류')
            if '\n' in row['memo'] or '\r' in row['memo']:
                raise ValueError('memo는 한 줄이어야 합니다')
            if 'boundary_flag' in row and not isinstance(row['boundary_flag'], bool):
                raise ValueError('boundary_flag는 불리언이어야 합니다')
            if 'boundary_reason' in row and not isinstance(row['boundary_reason'], str):
                raise ValueError('boundary_reason은 문자열이어야 합니다')
        except (ValueError, TypeError) as exc:
            raise ValueError(f'선택 파일 {line_no}행: {exc}') from exc
        seen.add(row['segment_id'])
        selections.append(row)
    return selections
