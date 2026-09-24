"""Deterministic three-line digest; spanning page markers belong to P4b."""
from __future__ import annotations


def render(records: list[dict], payload: dict) -> str:
    query = payload['query']
    lines = [f"# {payload['slug']}", '', f"질의: {query['query_id']}",
             f"주제: {query['topic']}", f"주장: {query['claim_text']}",
             '질의 확인: ' + ('확인됨' if query.get('confirmed_by') else '미확인'),
             f"실행: {payload['run_id']}",
             '추출기: ' + (records[0]['extractor_id'] if records else '선택 없음'),
             f'문장 수: {len(records)}', '']
    for record in records:
        locator = record['locator']
        lines.extend([' '.join(record['quote'].split()), '-> ' + record['claim_text'],
                      f"[{record['kind']} · {locator['section'] or '§—'} · p.{locator['page']}]", ''])
    return '\n'.join(lines)
