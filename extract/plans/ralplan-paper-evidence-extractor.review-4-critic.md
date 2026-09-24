## Critique: ralplan-paper-evidence-extractor (iteration 4)

### Iteration-2 items — closure check

**Blockers**
- **B1 (D1 iter-2, two-block rule 68 FPs).** CLOSED. Replaced with three-rule set at `:63, :84-89, :184` with pinned 21-line fixture at `:186-208`. The Architect independently reproduced the fixture with 0 FPs, and I independently checked that rule (ii) `^[1-9](?:\.[1-9]){0,2}$` rejects "20", "0.8", "103" as first-block matches (the specific FP labels from iter-2 review): "20" fails because "0" cannot follow "[1-9]" without a dot; "0.8" fails because "0" cannot start; "103" fails for the same "20" reason. Rule (ii) fires for "1" + "Introduction" (block seq=18) so seq=35's Introduction body inherits §1, and `test_span_line93.py::test_line93_spanning_exact` at `:241` + `test_section_1_body_is_intro` at `:217` are both anchored on the same empirical block.

- **B2 (D2 iter-2, one-segment workfile).** CLOSED. `:257`, `:262` now say "**전체** `segments.json`(모든 표시 세그먼트, 스펙의 통독 한 번)"; the walking-skeleton discipline is preserved by keeping *downstream* minimal (report_min = 8 keys, no six-reason check, no digest spanning marker).

- **B3 (missing spec-required `run.json` keys).** CLOSED. 26 keys enumerated at `:96-128` as a Python constant that `report.py` and `test_report_shape.py` both import verbatim; the previously missing `segments.body_words`, `segments.estimated_tokens`, `selections.spanning_selected`, `sources.codex_raw_first_diff`, and `sources.segmenter_ver` are all in the list.

**Majors**
- **M1 (D3 iter-2, 18-vs-19 ambiguity).** CLOSED. Total pinned at 26. `test_total_key_count` at `:324` asserts `len(RUN_JSON_KEY_PATHS) == 26`.
- **M2 (D4 iter-2, undefined test node-IDs).** CLOSED. All six previously undefined tests created — `test_records_shape.py` (:316), `test_records_counts.py` (:317), `test_para_id_cross_check.py` (:350), `test_digest_render.py::test_header_fields/test_order/test_three_lines` (:318-320) — and the AC→phase table at `:449-497` maps every node to a creating phase.

**Minors**
- **m1 (D5 iter-2, `EXTRACT_THRESHOLDS_PATH`).** CLOSED at `:151` and covered by `test_thresholds_env_var_override` at `:159`.
- **m2 (Principle-2 phrasing, `thresholds.load`).** CLOSED at `:22` and `:245`.
- **m3 (P4a→P4b resumability of measurements in-file).** CLOSED. `:279, :288-297` require the 5-bullet summary appended to *this* plan file under P4a; placeholder lines exist.
- **m4 (P4a scope, ADR documentation).** CLOSED at `:522-523` — ADR Consequences explicitly enumerates what P4a freezes vs. what it defers to P4b.
- **m5 (X4-3 `--gold` hook).** CLOSED at `:266` (CLI accepts `--gold`), `:353` (fixtures passed via `--gold`).

Every iteration-2 finding is closed. The one new Architect finding (D5, `test_section_fp_bound` wording ambiguity between "all matches" vs. "assigned block sections") is already applied inline at `:216` with the clarifying sentence "블록당 여러 매치 허용, 중복 제거 없음. 각 블록에 실제로 붙는 section 값(블록의 마지막 매치)과는 별개 회계다."

### The section-rule reversal — fair and principle-consistent?

The reversal is empirically driven and disclosed honestly. My iter-2 recommendation was: drop rule (ii), accept §—, remove `section == "§1"` assertion. That recommendation rested on the concern that rule (ii) would leak table cells like "4 Requests per user" and tick labels like "20 Hour of Day (UTC)". Iteration 4 answers that concern with two independent constraints — Title Case on the title text (`4자 이상 단어는 대문자 시작`) AND number regex `^[1-9](?:\.[1-9]){0,2}$` that rejects any 0 component — and then measures the joint filter against the actual gold-paper text. The measured 21/21 with 0 FPs is not rhetoric; the Architect and I both re-ran the number-filter on the specific iter-2 concern labels and confirm they no longer fire.

The counter-case: 4/20 recall for a single-line-only rule would leave the digest at ~80 % `§—`. That is a real UX degradation for the first artifact the user reads, and the spec's `null` allowance for `section` (spec:97) is a permission, not a preference. Recall matters here because §-labels are what a human uses to relocate the sentence in the paper.

Residual risk is handled honestly:
- v1's gate is explicitly the gold paper (Risks `:561` acknowledges non-gold-paper false positives will occur).
- The 41-paper measurement (484 headings, 65 monotonicity violations) is disclosed at `:63-68`, `:528`, `:542`, `:561` — not buried.
- The mitigation (per-paper heading fixtures + monotonicity filter) is parked in `[이후]` `:542` with a specific trigger ("inbox 배치 시작"), which is consistent with the binding user constraint that inbox is the final goal but not a v1 gate.
- The pinned fixture at `:186-208` doubles as a regression alarm: any poppler drift or paper-side change breaks the equality test loudly, which is what you want.

The one thing I would call out: this decision converts extract into a small-heuristics system for section semantics, and the plan admits that. The ADR at `:513-515` records the earlier alternatives (single-line, simple pair, own-nothing) with their measurements, so the choice is defensible against a future reader — it will not look mysterious after the fact.

Judgment: the reversal is justified on the measured evidence, principle-consistent given v1's gate is the gold paper alone, and the inbox-scale residuals are disclosed and parked in Deferred with a concrete trigger. I withdraw my iter-2 preference for fix (b).

### Spec `[v1]` coverage — rows that changed

| Spec `[v1]` | Phase | AC | Iter-2 status → Iter-4 status |
|---|---|---|---|
| C0.6 page/section, null count | P2 | C0-6 | Broken by D1 → **Adequate** (three-rule set + fixture) |
| C0.8 line-93 spanning + §1 | P3 | C0-8 | Partial (§1 assertion built on flawed rule) → **Adequate** (§1 restored on measured base) |
| C0.9 `codex_raw` sha diff + first-diff position | P4b | C0-9 | Partial (no first-diff position) → **Adequate** (`sources.codex_raw_first_diff` in 26-key list) |
| X1.3 single-pass read + body_words + est. tokens | P4a→P4b | X1-3 | Broken (18-key list missing body_words / estimated_tokens) → **Adequate** (`segments.body_words`, `segments.estimated_tokens` in list; X1-3 asserts both) |
| X2.1 counts closed | P4b | X2-1 | D4: `test_records_counts.py` undefined → **Adequate** (created in P4b `:317`, mapped `:480`) |
| X2.3 field contract | P4b | X2-3 | D4: `test_records_shape.py` undefined → **Adequate** (created P4b `:316`, mapped `:479`) |
| X2.7 `para_id` cross-check | P5 | X2-7 | D4: `test_para_id_cross_check.py` undefined → **Adequate** (created P5 `:350`, mapped `:492`) |
| X3.1–X3.3 digest header / order / three-line | P4b | X3-1..3 | D4: three digest test-node IDs undefined → **Adequate** (created P4b `:318-320`, mapped `:481-483`) |
| X4.2 `run.json` full shape | P4b→P5 | X4-2 | D3: 18-vs-19 ambiguity → **Adequate** (26 pinned + split into `test_p4b_owned_keys` + `test_all_keys` + `test_total_key_count`) |
| `[이후]` inbox / API / conditions / multi-paper digest / sentence G-recall / re-run stability | Deferred | — | **Adequate** (unchanged, now with per-paper heading fixture item) |
| `[sync]` `sources.yaml` registration / ledger import / ... | Deferred | — | **Adequate** (unchanged; verify-P4 expiry trigger noted for steelman) |

All previously inadequate rows are now adequate. No spec `[v1]` criterion is missing.

### Runnability of each AC command at its phase

I traced every `## Acceptance Criteria` command against cwd, `PYTHONPATH`, and file/test existence at the phase in which the AC is checked (v1 completion = post-P6).

- All non-pytest shell commands prepend `PYTHONPATH=../verify` (C0-1, C0-2, X2-2, X2-4, X2-9). ✓
- All `pytest` invocations rely on `extract/pytest.ini`'s `pythonpath` (:144). ✓
- All test node-IDs referenced (`::test_*`) are created in a phase and mapped in the `:449-497` table. I spot-checked 12 rows; every referenced node has a creating phase.
- File-existence ACs (C0-2 `run.json`, C0-9 `run.json`, X1-3 `run.json`, X2-2/X2-4/X2-9 `records.jsonl`, X4-6 `slice-facts-*.json` + `docs/decisions.md`) all reference files produced by phases whose completion is checked earlier by `test_p4b_precondition.py` / `test_p5_precondition.py`.
- CLI invocations (C0-2, C0-10) call `extract.cli` which is defined in P4a `:266`.

Every command is runnable as written at v1 completion.

### Trivial wording fixes the orchestrator can apply without another loop

None mandatory. Two purely cosmetic items I noticed but do not require action:
- `:414` says `segments.estimated_tokens = body_words * 1.3` is `float`; a Python `int * 1.3` is always `float`, so this is fine as documentation. No change needed.
- `:265` lists `report_min` with 8 sub-keys; the file `report_min.py` at `:265` is distinct from `report.py` at `:311`, so there is no conflict between "3-key" (Principle 4 wording at `:24`, historical) and "8-key" (this iteration). If the plan ever regenerates the Principle-4 sentence it should say "small-shape `run.json`" instead of "3키." Not required for iteration 4.

### Independent spot-check of Architect's iteration-4 measurement

Rule (ii) number regex `^[1-9](?:\.[1-9]){0,2}$` applied to the specific iter-2 concern labels:
- "20" → `[1-9]` matches "2", then "0" cannot match `(?:\.[1-9]){0,2}` (needs dot before non-zero digit). Rejected. ✓
- "0.8" → first char "0" does not match `[1-9]`. Rejected. ✓
- "103" → "1" matches, then "03" has no dot. Rejected. ✓
- "1.0 Global" → "0" component after dot fails `[1-9]`. Rejected. ✓
- Whereas "1" → matches, and next block "Introduction" matches title regex. Fires §1. ✓

Combined with Title Case (words ≥ 4 chars capitalized), tick labels like "Hour of Day (UTC)" also fail on the parens (regex `[A-Za-z -]{2,40}` disallows parens). The joint filter is sound on the gold paper.

### What's Genuinely Strong

- The section rule is now the *only* piece of self-owned heuristic in the pipeline, and it is bounded by a pinned fixture that fails loudly on any drift. That is the right containment for a heuristic.
- The 26-key `run.json` is a Python constant that ships with the module and drives the test — no duplication between "what the plan says" and "what the code checks."
- The P4a → P4b hand-off now writes both an artifact (`slice-facts-*.json`) and a plan-file amendment (5-bullet summary in-place), which honors the "resumable from the plan file alone" constraint literally.
- ADR "Consequences" enumerates what P4a freezes and what it defers, so future maintainers cannot claim a decision was made behind their back.
- The 41-paper residuals (484 headings, 65 non-monotonic transitions) are disclosed with a specific `[이후]` trigger. This is the discipline that "we bet against future data but declared our bet" requires.

### Bottom Line

Iteration 4 closes every blocker/major/minor from iteration 2 and answers iteration-4 D5 in the header. The reversal on section detection is empirically justified for the gold-paper v1 gate, and the inbox-scale residual risk is honestly disclosed and parked in Deferred + Risks with concrete triggers. Every AC command is runnable at its phase. The plan can go to an executor as-is.

VERDICT: APPROVE
