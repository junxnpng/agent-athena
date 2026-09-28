"""Render a deterministic digest from record provenance, with page transitions."""
from __future__ import annotations

from typing import Optional


def _position(record: dict) -> tuple:
    locator = record['locator']
    segment = record['record_id'].split('@')[0]
    return (locator['page'], int(locator['para_id'].rsplit('#', 1)[1]), int(segment.rsplit('.s', 1)[1]))


def render(records: list[dict], payload: Optional[dict] = None) -> str:
    # Empty runs have no records to carry metadata; their sealed workfile supplies it.
    first = records[0] if records else {}
    context = payload or {}
    query = first.get('query', context.get('query', {}))
    slug = first.get('paper_id', context.get('slug', ''))
    lines = [f"# {slug}", '', f"논문 제목: {first.get('paper_title', context.get('title', slug))}",
             f"질의: {query.get('query_id', '')}", f"주제: {query.get('topic', '')}",
             f"주장: {query.get('claim_text', '')}",
             '질의 확인: ' + ('확인됨' if query.get('confirmed_by') else '미확인 (unconfirmed)'),
             f"실행: {first.get('run_id', context.get('run_id', ''))}",
             '추출기: ' + first.get('extractor_id', context.get('extractor_id', '선택 없음')),
             f'문장 수: {len(records)}', '']
    for record in sorted(records, key=_position):
        locator = record['locator']
        quote = ' '.join(record['quote'].split())
        fragments = record.get('quote_fragments', [])
        pages = record.get('fragment_pages', [])
        if len(fragments) > 1:
            if len(pages) != len(fragments) or ' […] '.join(fragments) != record['quote']:
                raise ValueError('다이제스트 인용 조각이 레코드와 다릅니다')
            quote = ' '.join(fragments[0].split())
            for fragment, page in zip(fragments[1:], pages[1:]):
                quote += f" ⏎p.{page} " + ' '.join(fragment.split())
        lines.extend([quote, '-> ' + record['claim_text'],
                      f"[{record['kind']} · {locator['section'] or '§—'} · p.{locator['page']}]", ''])
    return '\n'.join(lines)
