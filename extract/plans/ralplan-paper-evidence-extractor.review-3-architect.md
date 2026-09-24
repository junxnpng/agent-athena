# Architect Review — ralplan-paper-evidence-extractor (iteration 3)

## Steelman antithesis

Iteration 3 closes the mechanical debt from iteration 2 (D2–D6, B2, B3, M1–M5) but the section-detection choice that fixed D1 has a hidden failure the DR never measured: applied to the actual gold paper, the single-line regex at `:85, :176` catches **4** of the paper's ~20 section headings — `2 Background`, `2.1 LLM Inference`, `7 Load Balancing`, `7.1 Production Systems`. The other 16 headings (`2.2 LLM Workload`, `3.3 Token Shape`, `4.1 Heterogeneity`, `5 Burstiness`, `5.1`, `6.1 Production System`, `6.2 Arrival Locality`, `6.3 GDSF`, `6.3.1`–`6.3.3`, `7.1.1`, `7.1.2`, `7.2 Load Balancing Simulation`, `7.2.1`, `7.2.2`, `8`, `9 Conclusion`) are pdftotext-split across two blocks (number-only block + title-only block) or emerge from PDF with the section number followed by the title *and body sentence* on one line (`6.3.1 Session Reconstruction. Since the trace does not include prompts…`), which the anchored `^…$` regex cannot match. Consequence: `locator.section` is null for roughly 85% of body blocks; the digest shows `[kind · §— · p.N]` for essentially every entry that isn't in §2 or §7. The Critic's (b) argument — "`§—` is honest for §1 body" — quietly generalized to "every §" without the plan naming the cost. The plan's own fixture example at `:178` lists 10 headings the regex demonstrably misses; whoever fills `tests/fixtures/gold_section_headings.txt` from the example fails `test_section_fp_bound`, and whoever fills it from the regex output makes the test circular (the Critic's own warning at iter-1 review §2).

## Tradeoff tensions

- **Own section detection minimally vs. own it well vs. don't own it (`.athena/plans/ralplan-paper-evidence-extractor.md:65-69, :85, :176`).** Plan picks minimal ownership (D1 single-line rule) to avoid the D2 false-positive frontier. Measured cost: 4/20 recall on the gold paper, and — since `pdftotext` split behavior is deterministic per PDF layout — most academic papers will hit the same "digit block / title block" pattern, so future inbox papers will look the same. Alternative "own it well" (targeted digits-only + Title-Case block rule with tight number bounds, `re.fullmatch(r"[1-9](\.\d){0,2}", num)` and `re.fullmatch(r"[A-Z][A-Za-z][A-Za-z -]{2,40}", title)` — I traced this manually; it would recover roughly `2.2, 3.3, 4.1, 5, 5.1, 6.1, 6.2, 6.3, 7.2, 8, 9` while filtering `20 Hour of Day (UTC)` / `0.8 CDF` / `103 Output tokens` because the number can't exceed 9 with ≤ 2 dots) would recover ~11 more headings with, plausibly, zero gold-paper false positives, at the cost of a second rule with its own fixture. Alternative "don't own it" would strip section from the digest entirely and drop `section_null_count` from `run.json`, buying a smaller v1 at the cost of a spec deviation.
- **Fixture from human-visible sections vs. from regex output (`:178, :184`).** Plan doesn't disambiguate. Both readings fail: human-visible → `test_section_fp_bound` fails (regex catches 4, fixture has 10+); regex-output → the test just asserts "the regex agrees with itself". Buys a passing test in the second case; costs any signal that the rule is doing something.

## Verified defects

### D1. [blocker] Regex catches only 4 of the paper's ~20 section headings

**Verified wrong.** I ran the plan's regex `^(\d+(?:\.\d+){0,2})\s+([A-Z][A-Za-z][A-Za-z -]{2,60})$` against the actual `pdftotext -q` output of the gold PDF, both against block first lines and against every line in every block, using `verify.tools.verify.paragraphs.split_blocks`. The rule fires against exactly these lines:

- seq 0037: `2 Background`
- seq 0037: `2.1 LLM Inference` (matches only if the rule is per-line, since both lines share a block after `split_blocks` joins consecutive non-empty lines)
- seq 0567: `7 Load Balancing`
- seq 0567: `7.1 Production Systems`

The other headings fail for one of two structural reasons, verified by `grep`:

- Number-alone lines exist at 263 (`2.2`), 637 (`3.3`), 813 (`4.1`), 987 (`5`), 1199 (`5.1`), 1529 (`6.1`), 1698 (`6.2`), 1856 (`6.3`), 2121 (`7.2`), 2472 (`9`); title-alone lines exist at 265 (`LLM Workload`), 639 (`Token Shape`), 815 (`Heterogeneity`), 1225 (`Burstiness`), 1531 (`Production System`), 1700 (`Arrival Locality`), 1858 (`GDSF`), 2123 (`Load Balancing Simulation`), 2474 (`Conclusion`). The single-line regex can never see them together.
- Subsection lines `6.3.1 Session Reconstruction. Since the trace does not include prompts or explicit session identifiers, we reconstruct` (line 1875) etc. contain the section header AND the paragraph's first sentence on one line — the anchored `^…$` cannot match because of the trailing body text.

The plan claims (`:65`, DR row D1) "run.json.selections.section_null_count가 참값을 낸다" and calls the residual "오탐 국경을 늘리지 않는다" — but the *actual* measurement wasn't done. Digest impact: `[kind · §— · p.N]` for essentially every entry outside §2 and §7. Plan example fixture at `:178` lists `2 Background, 2.2 LLM Workload, 3.3 Token Shape, 4.1 Heterogeneity, 5 Burstiness, 6.1 Production System, 6.2 Arrival Locality, 6.3 GDSF, 7.2 Load Balancing Simulation, 9 Conclusion` — the regex catches 1 of those 10.

Consequence for `test_section_fp_bound` at `:184` ("픽스처의 열거된 목록과 완전히 동일"): unrunnable as written.

**Fix (choose one).**

- (a) Accept the measurement, correct `:178` to say verbatim: "픽스처는 정확히 네 문자열을 담는다: `2 Background`, `2.1 LLM Inference`, `7 Load Balancing`, `7.1 Production Systems`. §1과 그 밖 모든 절 본문은 `§—`으로 렌더된다. 이는 스펙 허용값이며 다이제스트 UX 비용으로 문서에 남긴다." Correct DR row D1 at `:65` to say "정답 논문 20개 heading 중 4개를 잡고 16개는 `§—`; 다이제스트가 대부분 `§—`이 됨을 트레이드로 받아들인다." Correct `test_section_fp_bound` to `set(regex.matches) == set(fixture) == {…}` and pin the 4 strings in the plan.
- (b) Add a targeted second rule: "digits-only block matching `^[1-9](\.\d){0,2}$` immediately followed by a block whose first line matches `^[A-Z][A-Za-z][A-Za-z -]{2,40}$` (no digits, no parens, no periods) becomes `§<num>`." Verify against the gold paper (my manual trace suggests it catches 2.2, 3.3, 4.1, 5, 5.1, 6.1, 6.2, 6.3, 7.2, 8, 9 with zero false positives — tick labels are excluded because their numbers exceed 9 or contain dots > 2 or their "titles" contain digits/parens). Then re-populate `:178` with the 15 detected strings and keep the equality assertion.

**References.** `:65-69, :85, :176, :178, :184`; measured with `pdftotext -q $KVCPOOL/papers/workload__year-in-llm-serving.pdf -` and `verify.tools.verify.paragraphs.split_blocks`; grep lines from `$KVCPOOL/papers/codex_source_text/codex_workload__year-in-llm-serving.txt:263, 265, 637, 639, 813, 815, 987, 1199, 1223, 1225, 1529, 1531, 1698, 1700, 1856, 1858, 2121, 2123, 2472, 2474`.

### D2. [major] `test_report_shape.py::test_all_keys` runs in P4b but 3 keys are P5-computed

**Verified wrong.** The AC → phase table at `:459` places `tests/test_report_shape.py::*` in P4b. Plan `:287` says P4b's `report.py` "26키 채우는 최종. `RUN_JSON_KEY_PATHS` 상수를 export." But three of the 26 keys are produced by P5 modules:

- `checks.per_variant_grades` — filled by `variants.py` (`:318`, P5).
- `checks.para_id_cross_check` — filled by `para_check.py` (`:319`, P5).
- `checks.g_recall_report_only` — filled by `g_recall.py` (`:320`, P5).

The plan doesn't say P4b's `report.py` includes placeholder empty dicts for the three P5-owned keys. If P4b's implementation naturally omits them (or the modules that compute them don't exist yet), then `test_all_keys` (`:298`) fails at P4b's Exit check (`:305`, `.venv/bin/pytest -q` returns non-zero), which blocks P4b completion.

**Fix.** Add one line to `:287`: "P4b의 `report.py`는 26 키를 모두 dict에 넣되, P5가 채울 세 키(`checks.per_variant_grades`, `checks.para_id_cross_check`, `checks.g_recall_report_only`)는 P4b에선 빈 dict `{}` 자리표를 두고 P5의 각 모듈이 덮어쓴다." Optionally split `test_report_shape.py::test_all_keys` into `test_p4b_owned_keys` (23 keys) and `test_all_keys` (26 keys, run in P5) to make the phase alignment explicit.

**References.** `:287, :298, :305, :459, :318-320`.

### D3. [minor] Regex application scope under-specified

**Verified partial.** The plan says "단일 줄 정규식" at `:85` and "단일 줄 규칙 하나만" at `:176` but does not say whether it applies to block first lines only or to every line in every block. Because `paragraphs.split_blocks` glues consecutive non-empty lines into one block (`verify/tools/verify/paragraphs.py:76-87`), the two interpretations differ by one heading on the gold paper (`2.1 LLM Inference` — same block as `2 Background`, so "block first line" catches 3, "any line" catches 4).

**Fix.** Add to `:85` or `:176`: "규칙은 블록 안의 각 줄에 대해 적용한다(첫 줄뿐만 아니라); 매치한 블록에서 처음 매치한 (번호, 제목)을 그 블록의 section으로 삼고 이후 블록에 propagate한다."

### D4. [minor] `test_section_fp_bound` circular vs. fails-as-written

**Verified partial.** Plan `:178` tells the executor to fill `tests/fixtures/gold_section_headings.txt` "실행자가 정답 논문에서 뽑아 넣는" (from the real text) and lists 10 example strings, then `:184` asserts "매치 결과가 픽스처의 열거된 목록과 완전히 동일." If the executor takes the 10-heading example literally, `test_section_fp_bound` fails (D1). If the executor fills the fixture with the actual regex output, the test is circular. The plan doesn't tell them which.

**Fix (in conjunction with D1's fix).** Pin the fixture content verbatim in the plan itself: "The fixture contains exactly these four lines: `2 Background`, `2.1 LLM Inference`, `7 Load Balancing`, `7.1 Production Systems`. Any drift from a new poppler version or a different paper requires re-populating the fixture from a fresh measurement." Update `:178` example to match. This makes the test non-circular because the fixture is authored, not scraped.

## Item-by-item status vs. iteration 2

| Item | Status | Evidence |
|---|---|---|
| Architect D1 (spanning section-null filter) | **replaced** by new D1 above | `:85, :176` — the `section != null` gate is gone; the new regex under-detects |
| Architect D2 (P4a one-segment) | **resolved** | `:225` "전체 `segments.json`(모든 표시 세그먼트, 스펙의 통독 한 번)"; `:230` uses plural in name and semantics |
| Architect D3 (18-key ambiguity) | **resolved** | `:87-125` literal `RUN_JSON_KEY_PATHS` with 26 entries |
| Architect D4 (missing test IDs) | **resolved** | AC → phase table `:424-467`; every AC-referenced node maps to a phase that creates it |
| Architect D5 (env var) | **resolved** | `:143` reads `EXTRACT_THRESHOLDS_PATH` and forwards to `thresholds.load(path=…)`; test `:151` |
| Architect D6 (P4a residual scope) | **documented** | ADR Consequences `:491-492` names frozen items and negotiable items |
| Critic B1 (D1 rule ii, fix (b)) | **applied, but see new D1** | Rule (ii) gone (`:483` invalidates D2); `section == "§1"` assertion removed at `:209`; the under-detection was not measured |
| Critic B2 (D2 one-segment) | **resolved** | same as Architect D2 |
| Critic B3 (missing spec-required keys) | **resolved** | `:96, :100, :107-108, :113` add `codex_raw_first_diff`, `body_words`, `estimated_tokens`, `spanning_selected` |
| Critic M1 (18/19 ambiguity) | **resolved** | `RUN_JSON_KEY_PATHS` literal at `:92-124`, `test_total_key_count == 26` at `:300` |
| Critic M2 (D4 undefined tests) | **resolved** | AC → phase table lines 424-467; each node ID has a phase |
| Critic m1 (env var wording) | **resolved** | same as D5 |
| Critic m2 (Principle-2 whitelist) | **resolved** | `:24` adds `thresholds.load`; `:213` allows `thresholds.load` |
| Critic m3 (P4a→P4b resumability) | **resolved** | `:264, :268-273` 5-bullet summary in plan file; `:290` precondition asserts existence |
| Critic m4 (P4a frozen items) | **documented** | ADR Consequences `:491-492` |
| Critic m5 (CLI `--gold` hook) | **resolved** | `:234, :320, :329` add `--gold` option, default path spelled out |

## Principle / binding-constraint check

- **Principle 1** — intact.
- **Principle 2** — intact (whitelist now includes `thresholds.load`, and `X4-5` at `:419` allows it while still blocking `ledger/thresholds.begin/load_variants/queries.register`).
- **Principle 3** — intact (`paragraph_unit.split` gate at `:143`; C0-10 at `:383`).
- **Principle 4** — partially intact. P4a is genuinely thin on downstream (records_min/digest_min/report_min are minimal), full on segments.json (spec compliance). P4b's `test_all_keys` before P5 populates its dependencies is the residual violation (D2 above).
- **Binding "resumable from plan file alone"** — satisfied for P4b (5-bullet summary appended to plan at `:268-273`) and P5 (P4b outputs are files with well-defined paths).
- **Binding "≥ 80% coverage"** — declared in P6 (`:347`).
- **Binding "relative paths only, English code/comments, no phase labels in code"** — no violation observed.

## Synthesis — edits for iteration 4

All four items below are **wording edits, not design changes**; they can be applied without another full loop provided the coordinator picks a lane for D1 (fix (a) accept 4/20, or fix (b) add the targeted second rule).

1. **D1 (`:65, :85, :176, :178, :184`, DR row D1).** Pick one lane. If fix (a): rewrite `:178` example to the four verbatim strings I measured; update `:65` narrative to state "정답 논문에서 규칙이 잡는 heading은 4개이고 §1을 포함한 나머지 절 본문은 `§—`으로 렌더한다"; change `test_section_fp_bound` at `:184` to compare against the pinned four-string set. If fix (b): add the targeted "digits-only block + Title-Case block" rule with number bound `^[1-9](\.\d){0,2}$` and title bound `^[A-Z][A-Za-z][A-Za-z -]{2,40}$` to `:85, :176`; re-measure and pin the resulting heading set (my back-of-envelope: 15 hits, 0 false positives on the gold paper).
2. **D2 (`:287, :298, :459`).** Add one sentence to `:287`: "P4b's `report.py` fills all 26 keys; for the three P5-computed keys (`checks.per_variant_grades`, `checks.para_id_cross_check`, `checks.g_recall_report_only`) it stores `{}` as a placeholder that P5's modules overwrite." No new tests required.
3. **D3 (`:85` or `:176`).** Add: "The regex is applied to every line of every block (not only the block's first line); the first line in a block that matches becomes that block's `§<num>` and propagates."
4. **D4 (`:178, :184`).** Pin the fixture content verbatim in the plan itself (dependent on D1 lane). Reword `:184` to "the fixture is the authored expected set; `test_section_fp_bound` asserts set equality; drift (new poppler, new paper) requires re-authoring the fixture." Removes both the circularity and the fails-as-written possibility.

If iteration 4 applies items 1(a) + 2 + 3 + 4 as text edits, no further Architect+Critic loop is needed to verify internal consistency — but the coordinator should re-run the measurement in item 1 once the fixture is pinned, so `test_section_fp_bound` is not authored blind.

## References

- `.athena/plans/ralplan-paper-evidence-extractor.md:65-69` — DR option (d) rows; the "true-value" claim for `section_null_count` is what my measurement disproves (D1).
- `.athena/plans/ralplan-paper-evidence-extractor.md:85, :176` — single-line regex; scope under-specified (D3).
- `.athena/plans/ralplan-paper-evidence-extractor.md:87-125` — literal `RUN_JSON_KEY_PATHS` (26 keys); resolves iter-2 D3/B3/M1.
- `.athena/plans/ralplan-paper-evidence-extractor.md:143, :151, :383` — `EXTRACT_THRESHOLDS_PATH` wiring and test (resolves iter-2 D5).
- `.athena/plans/ralplan-paper-evidence-extractor.md:178, :184` — fixture instructions and equality assertion (D1, D4).
- `.athena/plans/ralplan-paper-evidence-extractor.md:225, :230` — P4a scope rewrite (resolves iter-2 D2).
- `.athena/plans/ralplan-paper-evidence-extractor.md:264, :268-273` — 5-bullet summary insertion point (resolves iter-2 m3).
- `.athena/plans/ralplan-paper-evidence-extractor.md:287, :298, :300, :318-320, :459` — P4b/P5 phase alignment for `test_all_keys` (D2).
- `.athena/plans/ralplan-paper-evidence-extractor.md:424-467` — AC → phase table (resolves iter-2 D4/M2).
- `.athena/plans/ralplan-paper-evidence-extractor.md:483-484` — ADR invalidation of two-block rule and steelman "verify absorbs segmenter"; expiry trigger at verify P4 (resolves iter-2 M5).
- `.athena/plans/ralplan-paper-evidence-extractor.md:491-492` — P4a frozen vs negotiable items (resolves iter-2 m4).
- `/work/jun/AI-helper/verify/tools/verify/paragraphs.py:22, :76-87` — `PIECE_SPLIT`, `split_blocks`; both still valid for spanning (unchanged).
- `/work/jun/AI-helper/verify/tools/verify/thresholds.py:29-39` — `load(path)` is DB-free and safe for `gates.py` (as required by `:143`).
- `$KVCPOOL/papers/codex_source_text/codex_workload__year-in-llm-serving.txt:220-221, :263, :265, :637, :639, :813, :815, :987, :1199, :1223, :1225, :1529, :1531, :1698, :1700, :1856, :1858, :1875, :1895, :1906, :1967-1968, :2077, :2101, :2121, :2123, :2161, :2352, :2472, :2474` — the number/title split patterns that break the single-line regex (D1).

---

## Orchestrator measurement (2026-09-23, after this review)

The review's fix (b) estimate ("~15 hits, 0 false positives") was measured and found optimistic: the plain pair rule gives 17 hits with 6 false positives (`1.0 Global`×3, `4 Requests per user`, `8 Output tokens`, `5 Instance cache size`, `1.8 Replication ratio`). Adding "no zero component in the number" and "Title Case title (every word of length ≥4 capitalized)" to all rules, applying the line rule to every line, and adding a run-in heading rule (`N.N Title. Body…`) yields exactly 21 headings with 0 false positives and strictly increasing numbers on the gold paper. Across all 41 papers the same rules detect 484 headings with 65 non-increasing transitions. The line-93 continuation block (seq 35) gets `§1`.
