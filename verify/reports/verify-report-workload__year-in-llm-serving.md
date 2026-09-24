# Verification report: workload__year-in-llm-serving

Query `gold-kv-reuse-v2` (confirmed by jun.heo): Production LLM serving traffic reuses prompt prefixes across requests.

**L1 grade distribution** (best grade over the variants; representative number):

| set | rows | exact | strict | loose | gapped | MISS | PASS |
|---|---:|---:|---:|---:|---:|---:|---:|
| claude | 44 | 0 | 29 | 9 | 6 | 0 | 44/44 |
| codex (l1_tautological=1) | 7 | 2 | 4 | 0 | 0 | 1 | 6/7 |

## Existence

- verifier: l1-exists-v2, protocol: v2, latest run: `l1-workload__year-in-llm-serving-004-2026-09-23T06:39:05Z`
- pass grades: exact, strict, loose, gapped
- variants: codex_raw, codex_layout, claude_body; claude_column: unavailable
- verdicts: PASS 50, MISS 1 (waivers are a separate table, never a verdict)
- waiver_rate: this paper 0/44 rows; overall 48/1489 rows (46/804 records)

## Alignment

- tier0 sweep `sweep-workload__year-in-llm-serving-gold-kv-reuse-v2-001` (lexical-v1): 50 rows, needs-judge 40, insufficient 10
- escalation_rate: 0.800 (observed)
- expensive_ratio: 0 (tier2 not invoked)
- judged rows: 20 by claude-sonnet-5/subagent (claim-judge-v1, tier1)

| alignment \ faithfulness | supports | refutes | insufficient | unknown |
|---|---:|---:|---:|---:|
| supports | 7 | 0 | 2 | 0 |
| refutes | 0 | 0 | 0 | 0 |
| insufficient | 8 | 0 | 3 | 0 |
| unknown | 0 | 0 | 0 | 0 |

## Recall

- `recall-workload__year-in-llm-serving-001-2026-09-23T09:25:26Z` (recall-v1, v3), config recall-v1; gold: 40 sentences; rows: L1-passed only (claude 44, codex 6)

| level | claude | codex | union |
|---|---|---|---|
| claim_present | R 0.575 (23/40) · P 0.318 (14/44) | R 0.000 (0/40) · P 0.000 (0/6) | R 0.575 (23/40) · P 0.280 (14/50) |
| conditions_match | not-applicable [3] | not-applicable [3] | not-applicable [3] |
| numbers_match | R 1.000 (3/3) · P 0.045 (2/44) | R 0.000 (0/3) · P 0.000 (0/6) | R 1.000 (3/3) · P 0.040 (2/50) |

R = gold sentences matched / gold sentences (numbers_match: sentences with at least one number); P = rows matched / L1-passed rows of the set.
[1] codex rests on 6 L1-passed rows (7 delivered; 30 records quarantined, a Codex record yields a row only with one fragment), so union ≈ claude: union recalls 23/40 gold sentences at claim_present, claude alone 23.
[2] P is measured against a hand pick, not an exhaustive extraction: a row outside G can still be valid evidence, so P is a lower bound on precision.
[3] conditions_match: not-applicable: G carries no condition labels (gold rows are sentences), and 0/50 L1-passed rows carry the five condition fields.

- probes P: not-applicable: extractor runs are frozen
- target set T: not-applicable: extractor runs are frozen
- why: both record sets were extracted before this check existed, so a probe planted now tests the recall code, not the extractor, and a target set chosen now is drawn after the run it would measure, while the target method draws it before.

- gold sentences no row covers: 6 in 3 unused-pool blocks, 11 in blocks a row already uses (block-level elusion cannot see them), 0 in blocks under the frame's word minimum, 0 not located

```
elusion (frame: blocks of the paragraph unit that no delivered row resolves into; fragments of quarantined records do not count as used):
  frame: 70, used: 36, unused_pool: 34
  elusion_n: 34 (registered), sample_seed: 20260922
  sample: elusion-workload__year-in-llm-serving-8b8cc779427e, 34 blocks, results/elusion/elusion-workload__year-in-llm-serving.tsv
  review: pending (fill missed_claims per block, then --elusion-import PATH --reviewer NAME)
  upper_bound (one-sided 95.0%, exact binomial): achievable at 0 errors 8.4% (n=34)
  gold floor: k >= 3 (sampled blocks holding a gold sentence no row covers: codex_raw#0047, codex_raw#0341, codex_raw#0541), so the observed bound will be >= 21.3% if the review counts those sentences
  5% upper bound is unreachable at k=1: 0 errors need n >= 59, the unused pool has 34 blocks
capture-recapture (unit: frame blocks the L1-passed rows resolve into):
  claude: 44 rows -> 34 blocks; codex: 6 rows -> 7 blocks; both: 6
  chapman_estimate: skipped: asymmetric sets (codex 6 rows vs claude 44 rows, ratio 0.14 < min_size_ratio 0.5)
  lower_bound: true (two extractors that miss the same blocks for the same reason bias the estimate low)
```

## Condition preservation

- L2 schema/tags `l2-workload__year-in-llm-serving-001-2026-09-23T09:03:43Z` (l2-schema-v1, v3): 50 rows, pass 0, quarantine 50 (quarantined rows are not comparable)
- quarantine_rate: 1.000 (50/50) — input diagnostic, prior expectation 100%
- reason codes: missing_condition_field 50, missing_number_field 47, modality_raised 6
- L6 arithmetic `l6-workload__year-in-llm-serving-002-2026-09-23T09:05:46Z` (l6-arith-v1, v3): 50 rows, pass 49, flag 1
- derived_from: applicable_rows: 0 (of 50 rows) — no row carries a derived_from pointer
- inline arithmetic in number strings: found 1, consistent 1, mismatch 0
- intra_doc_conflict: 0 pairs (8 keyed values compared)
- codex fragments: 6 rows, sha256 ok 6/6, in codex_raw 5/6, in codex_layout 0/6, in neither 1

## Not applicable

- L6 derived_from recomputation: applicable_rows: 0 (no row carries a derived_from pointer)
- recall probes P and target set T: not-applicable: extractor runs are frozen
- recall conditions_match: not-applicable: G carries no condition labels (gold rows are sentences), and 0/50 L1-passed rows carry the five condition fields
