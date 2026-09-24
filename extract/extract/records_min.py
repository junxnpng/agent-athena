"""Build verifier records by copying sealed segments, not model-written quotes."""
from __future__ import annotations

import hashlib
import json

from tools.verify.schema import CONDITION_FIELDS, validate


def build_records(payload: dict, selections: list[dict], *, agent: str, model: str) -> list[dict]:
    if agent not in ('codex', 'claude') or not model.strip() or '\n' in model:
        raise ValueError('에이전트와 모델 식별자가 필요합니다')
    picked = {row['segment_id']: row for row in selections}
    sha8 = hashlib.sha256(json.dumps([payload['run_id'], selections, agent, model],
                                    sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()[:8]
    records = []
    for segment in payload['segments']:
        choice = picked.get(segment['segment_id'])
        if choice is None:
            continue
        record = {'record_id': segment['segment_id'] + '@' + sha8,
                  'paper_id': payload['slug'], 'quote': segment['text'],
                  'locator': {name: segment[name] for name in ('page', 'section', 'para_id')},
                  'claim_text': choice['memo'], 'kind': choice['kind'],
                  'conditions': dict.fromkeys(CONDITION_FIELDS, 'unextracted'), 'numbers': [],
                  'extractor_id': f'{agent}-session:{model}', 'run_id': payload['run_id'],
                  'resolved_para_ids': segment['resolved_para_ids']}
        result = validate(record)
        if result.status != 'pass':
            raise ValueError(f'레코드 스키마 실패: {result.details}')
        records.append(record)
    if len(records) != len(selections):
        raise ValueError('선택 수와 레코드 수 불일치')
    return records
