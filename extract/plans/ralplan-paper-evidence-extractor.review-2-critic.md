## Critique: ralplan-paper-evidence-extractor (iteration 2)

### What's Being Proposed
Iteration 2 keeps the same architecture (top-level `extract` package, verify-as-library, sealed skill round-trip, gates first) and closes almost every mechanical objection from iteration 1: `PYTHONPATH` prepended, `QueryError → sys.exit(1)`, `paragraph_unit.split` runtime gate, `References` structural detection, `empty_memo` one-sentence rule, single-substring `SKILL.md` grep, 7-key `gates.yaml`, ADR line for `sha8` intent, and the steelman "verify absorbs the segmenter" alternative with expiry. Two structural changes: P4 is split into **P4a walking skeleton + decision gate** and **P4b hardening**; and a new two-block section-detection rule "digit-only block + Title Case block" is added so that `test_span_line93.py::section == "§1"` can pass. `run.json` grows to an enumerated 18-key list.

### Independent spot-checks

**D1 — CONFIRMED (blocker).** I confirmed multiple digit-only + Title-Case pairs in the actual `codex_raw` text:

- lines 502–506: block `20` followed by block `Hour of Day (UTC)` → rule fires `§20`
- lines 513–517: block `0.8` followed by block `CDF` → `§0.8`
- lines 592–594: block `103` followed by block `Output tokens` → `§103`
- lines 745–747: block `4000` followed by `Output tokens`
- lines 1219: `0.8` → `Figure 10: Monthly model mix among the top models` (long body block — this one may or may not fire depending on how "Title Case" is defined, but the pattern recurs)
- ~30 more `0.8`/`0.6`/`0.4` blocks throughout Figures 4/6/7/9

The Architect's count of 68 is very plausible. Since these false hits propagate `§0.8` / `§103` forward until the next real section marker, `locator.section` will show absurd values for entire ranges of body blocks, and the digest line `[kind · §0.8 · p.N]` reads as a data-integrity problem to any human reader. `run.json.selections.section_null_count` is also silently wrong.

**On the fix choice.** Two options were offered. I recommend the coordinator's **fix (b): drop rule (ii), accept `§—` for §1 body, remove the `section == "§1"` assertion from `test_span_line93.py`**. Reasons:

1. The spec explicitly permits `section: string | null` (spec:97, spec-schema), so `§—` for Introduction body is spec-compliant. There is nothing broken about `§—`; it is honest.
2. Even the Architect's proposed regex `^[1-9]\d?(\.\d+){0,2}$` + title regex still fires on rows like `4\n\nRequests per user` (table cell), and `103` itself is 3 digits — the "\d?" bounds it out unless you widen. Every widening lets in another false positive. Owning section detection turns a small correctness system into a small heuristics system (Architect's antithesis is right here).
3. The load-bearing invariant — spanning yields an exact quote — is proven by the L1 `grade == "exact"` half of `test_span_line93`. The `section == "§1"` half is decorative to that test.
4. The digest already had null-section handling (`§—`, plan:385). This uses existing machinery instead of adding new heuristics.
5. Cost: readers see `§—` for Introduction body items. This is a small, honest UI cost. Users of §-labels for finding text in the PDF still get page numbers and `[…]` markers.

If the executor really wants section labels for §1 body, add rule (ii) back in a later iteration with a `test_section_fp_bound` that must fire ≤ 15 times against the gold paper — but not in v1.

**D2 — CONFIRMED (blocker).** Plan:183 literally says "**세그먼트 하나짜리** workfile" (a one-segment workfile). This contradicts three things simultaneously: (i) plan:188's `export_segments_min(query, segments, out_dir)` uses plural `segments`; (ii) spec:111 explicitly requires "segments.json은 논문의 표시 세그먼트 전부를 한 파일에 담고 쪼개지 않는다"; (iii) all five decision-gate values at plan:212–216 (kind distribution, short_block_count, spanning success rate, L1 grade distribution, G-block recall) are ill-defined on a single segment. It is either a translation slip (should read "one workfile containing all segments") or a genuine but broken design. Either way the plan is not executable as written.

The fix is a single-clause rewrite of :183 to say "the full `segments.json` (all display segments) but a minimal-shape downstream chain (records_min → digest_min → 3-key `run.json`, no six-reason workfile checks yet, no spanning marker in the digest)." Small textual edit; no phase re-scoping.

### Coverage table — spec `[v1]` → iteration-2 phase → AC bullet → adequate?

| Spec `[v1]` (paraphrased) | Phase | AC bullet | Adequate? |
|---|---|---|---|
| Query file, required fields, `unconfirmed`, `QueryError → exit 1` | P1 | C0-1 | Yes |
| `extract_raw` source, PDF/text/poppler in report | P2 + P4a report_min → P4b report | C0-2 | Yes |
| `extract_raw == codex_raw` → blocks match | P2 | C0-3 | Yes |
| Block↔segment byte round-trip | P2 | C0-4 | Yes |
| `segmenter.yaml`, abbreviations | P2 | C0-5 | Yes |
| page/section, `\f=16`, null-section count | P2 | C0-6 | **Broken by D1** — section values wrong |
| Removal closed, References structural | P2 | C0-7 | Yes |
| Line-93 spanning, `[…]` exact | P3 | C0-8 | Yes on spanning correctness; the extra `section == "§1"` assertion is broken by D1 |
| `extract_raw` vs `codex_raw` sha diff, **first-difference position** | P4b report | C0-9 | **Partial** — 18-key list has `codex_raw_equal` and `codex_raw_diff_lines` but no `codex_raw_first_diff_position`; spec:100 and plan:83 both require it |
| `paragraph_unit.split == blank_line_block` runtime gate | P1 | C0-10 | Yes (with D5 fix) |
| SKILL.md + symlink | P4a | X1-1 | Yes |
| Six-reason file round-trip | P4b | X1-2 | Yes |
| Single-pass read; **body_words + estimated tokens** in report | P4a→P4b | X1-3 | **Broken** — the 18-key list (segments = 4 keys) has no `segments.body_words` and no `segments.estimated_tokens`; spec:111 and plan:191 both require them |
| memo single-line, `\n` rejected | P4b | X1-4 | Yes |
| SKILL four rules | P4a | X1-5 | Yes |
| N=N, quarantine 0 | P4b | X2-1 | Uses `tests/test_records_counts.py` — **D4: undefined** |
| Field contract | P4b | X2-3 | Uses `tests/test_records_shape.py` — **D4: undefined** |
| Schema pass N, quarantine 0 | P4b | X2-2 | Yes |
| No `none`, 5 × `unextracted` | P4b | X2-4 | Yes |
| L1 exact against `extract_raw` | P3 | X2-5 | Yes (mutation test relaxed per M2) |
| `codex_raw` grade dist | P5 | X2-6 | Yes |
| `para_id` cross-check | P5 | X2-7 | Uses `tests/test_para_id_cross_check.py` — **D4: undefined** |
| Per-variant grades, "text-layer scramble suspect" | P5 | X2-8 | Yes |
| kind + memo N/N | P4b | X2-9 | Yes |
| Digest header 9 fields | P4b | X3-1 | Uses `test_header_fields` — **D4: undefined** |
| Order (page → block seq → sent n) | P4b | X3-2 | Uses `test_order` — **D4: undefined** |
| Three-line item, `§—` for null | P4b | X3-3 | Uses `test_three_lines` — **D4: undefined** |
| Spanning marker round-trip | P4b | X3-4 | Yes (`test_span_marker_roundtrip` is created at :275) |
| Digest deterministic | P5 | X3-5 | Yes |
| `gates.yaml` sha256 in report | P1 + P4b | X4-1 | Yes |
| `run.json` full shape | P4b | X4-2 | **Broken by D3** (18 vs 19), **plus missing keys** (body_words, estimated_tokens, spanning-selection count, first-diff position) |
| G recall report-only | P5 | X4-3 | Yes (fixture-based, m6 resolved) |
| Tests-first + 80% coverage | P6 | X4-4 | Yes |
| No ledger / conn-bound calls | P3 + P6 | X4-5 | Yes |
| P4b/P5 precondition (slice-facts, decisions) | P4b + P5 | X4-6 | Yes |

### Findings

#### Blockers

1. **B1 — D1 two-block section rule.** 68 false positives from tick labels and table cells make `locator.section` and the digest systematically wrong through the body. Endorse fix (b): remove rule (ii) from :86 and :136; delete the `section == "§1"` assertion from :166 and :357; keep §— for §1 body. The load-bearing L1-exact test still verifies spanning. Do not attempt to tighten rule (ii) in v1 — the false-positive frontier is deep.

2. **B2 — D2 "one-segment workfile" (P4a scope).** :183 contradicts :188 and spec:111. Rewrite :183 to "the full segments.json (all display segments) but a minimal downstream chain (records_min → digest_min → 3-key run.json)." Keep :211–216 decision-gate list as is. One-sentence fix.

3. **B3 — `run.json` missing spec-required keys.** Iteration 2 shipped an 18-key enumeration but three spec-mandated report items are not in it:
   - `segments.body_words` and `segments.estimated_tokens` (spec:111 + spec X4 group "세그먼트 수: … 본문 낱말 수와 추정 토큰")
   - `selections.spanning_selection_count` (spec X4 group "선택 결과: … spanning segment 선택 수") — the plan has `segments.spanning.candidates/emitted` (segmentation-side, i.e., how many spanning segments were emitted from segmenting) but not "how many spanning segments the LLM chose"
   - `sources.codex_raw_first_diff_position` (spec:100 + plan:83)

   Required change: enumerate these explicitly and update the "18" count everywhere (`:31`, `:239`, `:270`, `:392`, `:12`). This is more than typo-fixing.

#### Majors

4. **M1 — D3 18-vs-19-key ambiguity.** Plan :267 writes `checks.para_id_cross_check (…) + checks.g_recall_report_only (…)` with a `+`, ambiguous between "one key with nested field" and "two peer keys." X4-2 (:392) hard-codes "열여덟 항목" but a natural reading of :267 yields 19. Required change: state the literal Python list of key path strings in the plan (`KEY_PATHS = [...]`) so `test_report_shape.py::test_all_keys` imports it verbatim, and match the count in the AC text. (This must be resolved *together* with B3's added keys — the final count will be 20 or 21, not 18.)

5. **M2 — D4 six test node IDs referenced by AC but not created.** `tests/test_records_counts.py`, `tests/test_records_shape.py`, `tests/test_para_id_cross_check.py`, and `tests/test_digest_render.py::{test_header_fields, test_order, test_three_lines}` are all named in the AC but no phase's "먼저 쓰는 테스트" list creates them. This is not cosmetic — pytest node-ID ACs are "runnable" only if the nodes exist. Required change: add explicit bullets to P4b's "먼저 쓰는 테스트" creating `test_records_shape.py`, `test_records_counts.py`, and `test_digest_render.py` with the three functions above (span_marker_roundtrip is already there). Add `test_para_id_cross_check.py` to P5.

#### Minors

6. **m1 — D5 `EXTRACT_THRESHOLDS_PATH` env var not spelled out in `gates.py`.** The test at :200 exports it, but :104's description of `assert_paragraph_unit_split()` does not say the wrapper reads it. Add "reads `os.environ.get('EXTRACT_THRESHOLDS_PATH')` and passes it (or `DEFAULT_PATH`) to `tools.verify.thresholds.load(path=…)`" at :104, plus one `test_thresholds_env_var_override` case in P1. Small.

7. **m2 — Principle-2 phrasing.** :29 lists allowed verify functions but omits `thresholds.load` (used by :104). `thresholds.load` is verified DB-free (verify/tools/verify/thresholds.py:29-39). Add it to the whitelist so `test_no_ledger.py` and the Principle text agree. Documentation-only.

8. **m3 — P4a → P4b resumability residual.** Plan tests file existence of `slice-facts-*.json` and `docs/decisions.md`, but a fresh P4b session must open the JSON to know what was observed. Endorse the Architect's suggestion: add "on P4a completion, append a 5-bullet summary of measurements to this plan file under the `- [ ] 결정 게이트` line" so the plan-file-only resumability rule is not violated. Small.

9. **m4 — D6 residual P4a scope.** P4a still fixes CLI subcommand names, three-line digest layout, `record_id = <segment_id>@<sha8>`, `run.json` group naming (`sources.*`). Not a defect; note in ADR "Consequences" that these are frozen. Documentation-only.

10. **m5 — X4-3 fixture-based test still needs implementation detail.** `test_cli_exit_code_independent_of_g_recall` needs the CLI to accept a `--gold <path>` override or an env var to point at the synthetic gold, else the fixtures are inert. Spell that hook out in P5's `report.py`/`cli.py` description.

### Hidden Assumptions (unchanged from iter-1, restated)

- pdftotext byte-equality with `codex_raw` will hold for future inbox papers (Risks now acknowledges this and offers to promote `[sync]` early — good).
- Session model will not persist writing forbidden fields; the plan's response is a `.rej-<n>.log` and manual re-run (Risks acknowledges — acceptable for v1).

### What If You're Wrong About…

- **Rule (ii) being fixable.** The Architect's proposed regex still lets `4 Requests per user` through. Every widening of "title-block first line" admits table headers. Better to bet on §— than to keep chasing regex boundaries; hence fix (b).
- **The 18-key `run.json` being a fixable enumeration.** Once you add body_words + estimated_tokens + spanning-selection count + first-diff position, the actual count is closer to 22. The plan should state a literal list once and stop counting.
- **P4a's "minimal downstream chain" being small.** It still creates six modules and six test files and freezes CLI subcommand names, the three-line digest layout, `record_id` schema, and `run.json` group naming (Architect D6). If P4a's observation is surprising (e.g., LLM picks primarily short-block segments), P4b unwinds a lot. Note in ADR Consequences.

### Architect items — endorse / modify / reject

- **Endorse D1** as blocker; **modify** the suggested fix to (b) drop rule (ii), accept §—, remove the §1 assertion. Architect's regex tightening (a) is fragile.
- **Endorse D2** as blocker with the Architect's one-sentence rewrite.
- **Endorse D3** as major; **augment** with B3 — the missing spec-mandated keys mean the total is not 18.
- **Endorse D4** as major with the Architect's fix; must be applied verbatim.
- **Endorse D5** as minor with the Architect's fix.
- **Endorse D6** as documentation-only; not a defect.
- **Endorse status table** as accurate on iter-1 items closed.
- **Endorse synthesis items 1, 2, 4, 5, 6, 7** (with modification #1 → fix (b), not (a)).
- **Modify synthesis item 3** — the choice between 18 and 19 is moot once B3 forces the count higher; state the literal list and let the number fall out.

### What's Genuinely Strong

- Every mechanical iter-1 defect is closed except D1 (partial by construction) and the P4 split.
- The steelman "verify absorbs the segmenter" is added to ADR with a concrete expiry trigger (verify P4). This is exactly the discipline iter-1 lacked.
- The `PYTHONPATH=../verify` convention is stated once at :76 and applied consistently across every AC and every CLI example.
- `paragraph_unit.split` runtime gate is elevated from missing-spec-requirement to Principle 3 clause with an isolated test. Clean.
- P4b/P5 precondition tests that assert artifact existence give resumability a real gate.

### Bottom Line

Iteration 2 fixes ~14 of 15 iter-1 issues, but introduces three blockers of its own (D1 68-false-positive rule, D2 self-contradicting P4a scope, B3 missing spec-required `run.json` keys) plus one major-scale gap (D4 undefined test node IDs). The blockers require design-level choices (drop rule (ii); rewrite P4a scope; enumerate missing keys with spec-provenance) that go beyond mechanical wording edits and warrant one more Architect+Critic loop to verify internal consistency (especially the final `run.json` key count).

VERDICT: ITERATE
