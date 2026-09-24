"""P4a observations, explicitly distinct from the P4b complete run schema."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Optional

from tools.verify.convert.gold import parse, load_rules
from tools.verify.paragraphs import Haystack, resolve, split_blocks
from .existence import check_against_codex, require_exact


def build_report(payload: dict, records: list[dict], selections: list[dict], raw: str,
                 codex_raw: Optional[str] = None, gold: Optional[Path] = None) -> dict:
    grades = Counter(require_exact(record['quote'], raw).grade for record in records)
    codex_grades = (dict(Counter(check_against_codex(record['quote'], codex_raw).grade
                                for record in records)) if codex_raw is not None else None)
    recall = {'status': 'unavailable', 'rate': None}
    if gold is not None:
        parsed = parse(gold.read_text(encoding='utf-8'), load_rules())
        haystack = Haystack(split_blocks(raw, 'extract_raw'))
        gold_blocks = {seq for item in parsed.of('sentence') for seq in resolve(item.text, haystack)}
        selected = {int(para.rsplit('#', 1)[1]) for record in records for para in record['resolved_para_ids']}
        recall = {'status': 'report_only', 'gold_blocks': len(gold_blocks),
                  'covered_blocks': len(gold_blocks & selected),
                  'rate': len(gold_blocks & selected) / len(gold_blocks) if gold_blocks else None}
    return {'stage': 'P4a-prototype', 'run_id': payload['run_id'],
            'sources': dict(payload['sources'], segmenter_ver=payload['segmenter_ver'],
                            codex_raw_equal=(payload['sources']['comparison'] or {}).get('equal')),
            'segments': dict(payload['counts'], spanning=payload['spanning']),
            'selections': {'count': len(records), 'kinds': dict(Counter(r['kind'] for r in records)),
                           'spanning': sum(len(r['resolved_para_ids']) > 1 for r in records),
                           'short_block_count': sum(payload['block_words'][r['locator']['para_id']] < 20 for r in records),
                           'boundary_flags': [s for s in selections if s.get('boundary_flag')]},
            'checks': {'schema': {'pass': len(records), 'quarantine': 0},
                       'l1_extract_raw': dict(grades), 'codex_raw': codex_grades,
                       'g_recall_report_only': recall}, 'gates_sha256': payload['gates_sha256']}
