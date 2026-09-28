"""Cross-check source locators without confusing repeated first hits with errors."""
from __future__ import annotations

from tools.verify.paragraphs import Haystack, canon, primary, resolve, split_blocks, words


def check(records: list[dict], raw: str) -> dict:
    haystack = Haystack(split_blocks(raw, 'extract_raw'))
    result = {'ok': True, 'checked': 0, 'mismatches': [], 'empty_resolve_short': [],
              'empty_resolve_other': [], 'repeated_first_hit_mismatch': []}
    for record in records:
        quote, identifier = record['quote'], record['record_id']
        hits = resolve(quote, haystack)
        if not hits:
            key = 'empty_resolve_short' if len(canon(quote)) < 20 and len(words(quote)) < 9 else 'empty_resolve_other'
            result[key].append(identifier)
            continue
        result['checked'] += 1
        para = record['locator']['para_id']
        if para not in {f'extract_raw#{seq:04d}' for seq in hits}:
            result['mismatches'].append(identifier)
        elif para != f'extract_raw#{primary(quote, haystack):04d}':
            result['repeated_first_hit_mismatch'].append(identifier)
    result['ok'] = not result['mismatches'] and not result['empty_resolve_other']
    return result
