# Architect Review — ralplan-paper-evidence-extractor (iteration 4, delta)

## Status of iteration-3 D1–D4

- **D1 (section under-detection).** **Resolved.** I ran the three rules exactly as written at plan `:63, :84-89, :184` against `pdftotext -q $KVCPOOL/papers/workload__year-in-llm-serving.pdf -` piped through `tools.verify.paragraphs.split_blocks`. The rules produce **21 matches, 0 false positives, in document order**, identical to the pinned fixture at `:187-208`. Block `seq=35` (the line-93 continuation, first line `highly skewed popularity…`) is preceded by the pair-rule match at `seq=18` (`1 Introduction`), so its propagated `section == "§1"` — this matches both `test_section_1_body_is_intro` at `:217` and the revived `test_span_line93.py::test_line93_spanning_exact` assertion at `:241, :406`.
- **D2 (P4b vs P5 phase alignment for `test_all_keys`).** **Resolved.** Plan splits the shape test at `:322-324` into `test_p4b_owned_keys` (asserts the 23 P4b-owned keys are non-empty and the 3 P5-owned keys are `{}` placeholders) and `test_all_keys` (asserts the 3 P5-owned keys are non-empty after P5). AC X4-2 at `:441` names all three tests. AC→phase table at `:485, :495` places `test_p4b_owned_keys` in P4b and `test_all_keys` in P5. `report.py` at `:311` says the three placeholders are seeded in P4b and overwritten by P5's `variants.py`/`para_check.py`/`g_recall.py` at `:342-344`. ADR Consequences at `:524` restates the split.
- **D3 (regex scope).** **Resolved.** `:84` and `:184` both say verbatim "블록 안의 각 줄에 적용(첫 줄뿐 아니라); 매치가 있으면 그 블록의 마지막 매치가 그 블록의 section이 되며 이후 블록에 propagate; 첫 매치 이전 블록은 null."
- **D4 (fixture circularity).** **Resolved.** `:210` explicitly forbids the auto-populate path: "실행자가 규칙 출력을 픽스처에 붙여 넣는 자동 절차는 금지(테스트 순환성 회피)." The 21-line fixture is pinned inline at `:187-208` as authored ground truth.

## Verified consistency of the two changes with the rest of the plan

- DR option (d) at `:59-68` now enumerates D1 (three rules, chosen), D2 (single-line, 4/20 recall — the previous iteration), D3 (simple pair, 17 hits with 6 false positives — measured), D4 (own nothing) — each with measurement, correct trade description.
- Deferred at `:542` and Risks at `:561` both cite the 41-paper measurement (484 headings, 65 monotonicity violations) as the trigger for per-paper fixtures and a monotonicity filter — internally consistent with the DR row.
- No dangling references to `test_section_1_body_is_null` or "§— for §1" outside their rejected-alternative contexts (verified via `grep`).
- `run.json` keys accounting: 26 keys with three P5-owned; `RUN_JSON_KEY_PATHS` list at `:92-127` has the intended split marked inline. P4b Exit check at `:333` runs the full pytest suite; `test_p4b_owned_keys` asserts placeholders, so P4b won't fail on the three unfilled keys.

## New verified defects

### D5. [minor] `test_section_fp_bound` semantics ambiguous between "all matches" and "assigned block sections"

**Verified partially wrong.** Under the rule "block section = last match in the block, propagate forward" (`:84, :184`), block `seq=37` matches both `2 Background` and `2.1 LLM Inference` on its two lines and is assigned `§2.1` (last match wins). Block `seq=567` matches both `7 Load Balancing` and `7.1 Production Systems` and is assigned `§7.1`. So the *list of section values actually assigned to blocks* has 19 entries, missing `2 Background` and `7 Load Balancing`. The *list of raw regex matches, no de-dup* has 21 entries.

The plan pins 21 as the fixture (`:186-208`) and `test_section_fp_bound` at `:216` says "세 규칙 세트가 정답 논문에서 매치한 heading 목록 == 픽스처 21행 (순서까지 동일)." Under interpretation A ("all matches") the test passes with 21; under interpretation B ("assigned block sections") the test would need 19 and fail against the pinned 21.

I measured both:
- Interpretation A (all regex matches, order preserved): 21 items, exact equality with fixture. ✓
- Interpretation B (block sections, deduplicated): 19 items, missing `2 Background` and `7 Load Balancing`. ✗

The plan's intent is A (since it pinned 21), but the wording lets an executor implement B. Because "매치가 있으면 그 블록의 마지막 매치가 그 블록의 section" (`:84`) is the *assignment* rule, an executor reading it as "so the test checks assigned sections" would produce 19 and fail. The user-visible digest labels are B (block 37 shows `§2.1`, not `§2`), which is semantically correct because §2 has no body content before §2.1 in the paper — so the fixture (A) documents "what the rules matched" while the digest documents "what blocks got labelled".

**Fix.** One-sentence clarification at `:216` (or `:186`): "이 테스트가 비교하는 목록은 세 규칙이 정답 논문에 대해 문서 순서로 낸 **모든** (번호, 제목) 매치이며(블록당 중복 허용 · dedup 없음), 각 블록에 실제로 할당되는 section 값(마지막 매치, `:84`)과는 별개 회계다. 정답 논문에서 seq 37은 두 매치(`2 Background`·`2.1 LLM Inference`)를 모두 픽스처에 내고 자신은 `§2.1`을 받는다; seq 567도 같다."

## Judgment

The plan is ready for the Critic's final verdict; D5 is a one-line wording clarification that does not require re-review.

## References

- `.athena/plans/ralplan-paper-evidence-extractor.md:63-68` — DR option (d) three-rule set with measurements.
- `.athena/plans/ralplan-paper-evidence-extractor.md:84, :184` — three rules and last-match-wins assignment rule; regex scope explicit ("블록 안의 각 줄에 적용").
- `.athena/plans/ralplan-paper-evidence-extractor.md:87-89` — measurement note (21 matches, 0 false positives, order pinned).
- `.athena/plans/ralplan-paper-evidence-extractor.md:186-210` — pinned fixture (21 lines) with auto-populate ban.
- `.athena/plans/ralplan-paper-evidence-extractor.md:216-217` — `test_section_fp_bound` (D5 ambiguity) and `test_section_1_body_is_intro`.
- `.athena/plans/ralplan-paper-evidence-extractor.md:241, :406` — C0-8 revived `section == "§1"` assertion.
- `.athena/plans/ralplan-paper-evidence-extractor.md:311, :322-324, :354, :441, :485, :495, :524` — 26-key placement, P4b/P5 test split, AC→phase mapping.
- `.athena/plans/ralplan-paper-evidence-extractor.md:542, :561` — Deferred and Risks: 41-paper measurement (484 headings, 65 monotonicity violations) as trigger for per-paper fixtures.
- Measurement: `pdftotext -q $KVCPOOL/papers/workload__year-in-llm-serving.pdf -` → `tools.verify.paragraphs.split_blocks(text, "extract_raw")` (697 blocks). Three-rule run produced 21 matches (all-matches) or 19 (block-sections after last-match dedup); seq 35 → §1 either way.
