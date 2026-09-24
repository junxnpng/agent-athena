# Architect Review — ralplan-paper-evidence-extractor (iteration 2)

## Steelman antithesis

The revision closes almost every mechanical objection from iteration 1 (D2–D6, B2, B3, M2–M5), but it doubles down on a self-owned section-detection heuristic that the plan now needs for two orthogonal jobs: (a) making the load-bearing `test_span_line93` pass, and (b) filling `locator.section` for every record and every digest item. The new "digits-only block + Title-Case block" rule at `:86, :136` succeeds at (a) but fires 68 times against 15 real section headers on the gold paper — most false hits come from figure tick labels like `20 Hour of Day (UTC)`, `0.8 CDF`, `103 Output tokens`. So the digest and `run.json.selections.section_null_count` derived from the same rule will be systematically wrong. The plan's real bet is that extract can own section semantics all by itself; a plan that instead used only rule (i) (single-line `N Title`) for real sections and left the line-93 span guarded by "≥ 20-word body block" alone would give the same correctness where it matters (spanning, existence) and would have to admit `section: null` for Section 1 of the gold paper — which the spec explicitly allows. Owning section detection is the choice that turns a small correctness system into a small heuristics system, and the plan does not surface that trade.

## Tradeoff tensions

- **Precision of the section field vs. recall on line-93 spanning.** Plan picks a broad two-block rule that catches "1 Introduction" *and* everything shaped like `<digit>\n\n<CapitalizedWord>` (`:86`). Buys: the spanning target for line 93 sits in §1, and `test_span_line93.py::section == "§1"` (`:166,:357`) passes. Costs: 68 spurious detections on the gold paper alone (measured — see D1 below), each of which then propagates as `§0.8` / `§20` / `§103` to subsequent blocks until the next real section. What that would buy if reversed: keep rule (i) only, accept `section: null` for §1 body blocks, drop the `section == "§1"` assertion in test_span_line93.py (the exact-grade of the spanning quote alone still verifies the load-bearing invariant). The plan does not weigh this.
- **P4a as "one-segment workfile" vs. P4a as observation phase.** Plan `:183` writes "세그먼트 하나짜리 workfile"; plan `:188` writes `export_segments_min(query, segments, out_dir)` (plural); plan `:211–216` lists decision-gate values that only mean anything if the session sees every display segment (`selections.count`, `kind_dist`, `short_block_count`, spanning success count, L1 grade distribution). Buys "small P4a"; costs "meaningful observation." The two goals collide inside one phase.
- **Enumerated 18 keys in `run.json` (X4-2, M3) vs. actual list.** Plan enumerates 5+4+5+4 but tacks `checks.g_recall_report_only` onto the fourth checks item with a `+` (`:267`). Buys: a definite test asset. Costs: whoever reads the plan can't tell whether checks has 4 or 5 keys, so `test_report_shape.py::test_all_keys` (`:276, :392`) will differ from executor to executor.

## Verified defects

### D1. [blocker → carried over as partial] Two-block section rule fires 68 times on the gold paper

**Verified wrong.** New rule (`.athena/plans/ralplan-paper-evidence-extractor.md:86, :136`): "숫자만 있는 블록 + 바로 뒤 Title Case 블록 → §N". I ran the rule against the actual `pdftotext` output of `$KVCPOOL/papers/workload__year-in-llm-serving.pdf` (697 blocks). Only 15 sections exist (Intro through §9 Conclusion, with a few subsections). The rule fires **68 times**. Real sections that are correctly caught: `1 Introduction` (seq 18 — good, this is what makes the line-93 test pass), `2.2 LLM Workload`, `3.3 Token Shape`, `4.1 Heterogeneity`, `5 Burstiness`, `6.1 Production System`, `6.2 Arrival Locality`, `6.3 GDSF`, `7.2 Load Balancing Simulation`, `9 Conclusion`. Real false positives (representative):

- seq=0107 `§20` from tick label "20\n\nHour of Day (UTC)"
- seq=0112 `§0.8` from "0.8\n\nCDF"
- seq=0137 `§103` from "103\n\nOutput tokens"
- seq=0203 `§20` from "20\n\nConference'17…" (running header)
- seq=0290 `§4` from table "4\n\nRequests per user"
- seq=0332 `§0.0` from "0.0\n\nNov"
- seq=0343 `§5.1` from "5.1\n\nMost models are bursty…" (a partial hit — 5.1 is real, but the title captured is the next paragraph, not the section title)

Consequence: (a) the load-bearing `test_span_line93.py` still passes because block 18's Introduction detection is the first hit and §1 propagates through blocks 19–36 (I confirmed the between-section detections lie further into the paper). (b) But `locator.section` gets systematically wrong values (`§0.8`, `§103`, `§20`, `§4`, `§0.0`) all through the body, and the digest shows those as `[kind · §0.8 · p.N]`. (c) `run.json.selections.section_null_count` is understated because the false hits overwrite null.

**Fix.** Tighten rule (ii) with any of: `int(number) <= 12 and "." not in number` unless dotted; require the "title" block to start with a word (not a digit-inclusive label like "Output tokens", "Hour of Day (UTC)"); reject if the pair sits inside a `\f`-adjacent run whose surrounding blocks look like tick labels (all ≤ 3 words, mostly numeric). The safest small change: rule (ii) is admitted only if `number` matches `^[1-9]\d?(\.\d+){0,2}$` AND the next block's first line is `re.fullmatch(r"[A-Z][A-Za-z][A-Za-z -]{2,40}", first_line)`. That kept "1 Introduction" and killed "20 Hour of Day (UTC)" / "0.8 CDF" / "103 Output tokens" in a quick mental trace.

**References.** `.athena/plans/ralplan-paper-evidence-extractor.md:86, :136, :142, :166, :357`; measured on `$KVCPOOL/papers/codex_source_text/codex_workload__year-in-llm-serving.txt` and `$KVCPOOL/papers/workload__year-in-llm-serving.pdf` via `pdftotext -q … -` and `tools.verify.paragraphs.split_blocks`.

### D2. [blocker] P4a "one-segment workfile" contradicts the observation contract

**Verified wrong (new in iteration 2).** Plan `:183` says P4a's pipeline is "세그먼트 **하나짜리** workfile · 세션 selections · 최소 레코드 · 최소 다이제스트 · 3키 run.json." Plan `:188` says `export_segments_min(query, segments, out_dir)` (plural). Plan `:211–216` says the decision gate returns: (1) segment counts and spanning success, (2) *selection count N*, kind distribution, `short_block_count`, `boundary_flag` presence, (3) L1 grade distribution across N records, (4) per-variant grades, (5) G-block recall. All of (1)–(5) require the full segment set. A one-segment workfile makes the observation trivial (kind distribution is a single value; short_block_count is 0 or 1; selection count is 0 or 1) and cannot inform P4b. Meanwhile spec X1 says "통독은 한 번이다. `segments.json`은 논문의 표시 세그먼트 전부를 한 파일에 담고 쪼개지 않는다." (`.athena/specs/deep-interview-paper-evidence-extractor.md:111`), so a one-segment workfile also violates the spec.

**Fix.** Delete "세그먼트 하나짜리" from `:183`. Say "the full segments.json (all display segments), a minimal-shape records/digest/report chain, and no six-reason workfile checks yet." Keep the decision-gate values list unchanged.

**References.** `:183, :188, :211-216`; spec `.athena/specs/deep-interview-paper-evidence-extractor.md:111`.

### D3. [major] `run.json` 18-key enumeration is ambiguous

**Verified wrong.** Plan `:241-270` enumerates key groups labelled "sources (5) / segments (4) / selections (5) / checks (4)" — sum 18. But the last checks bullet is written `... checks.para_id_cross_check (…) + checks.g_recall_report_only (…)` (`:267`) which reads naturally as two separate keys. Under that reading, checks has 5 entries, total 19. `test_report_shape.py::test_all_keys` at `:276` and X4-2 (`:392`) both say "iterate the string list" — if the iteration list has 19 items, X4 acceptance says "18 items" (`:392`), and readers will disagree on which 18 to test.

**Fix.** Either move `checks.g_recall_report_only` out of the `+` into its own bullet under checks (then relabel "checks (5)" and change the AC text to 19), or explicitly declare "checks has 4 top-level keys; the fourth key's *value* dict contains `g_recall_report_only`" and demote the "+" into a nested field bullet. Whichever choice, the AC text at `:392` and the iterator list must match by count. Add the literal Python list to the plan so an executor cannot re-invent it.

**References.** `:241-270, :276, :392`.

### D4. [major] Six test node-IDs referenced by ACs are not created by any phase

**Verified wrong.** These test files/nodes are named in ACs but no phase's "먼저 쓰는 테스트" list creates them:

- `tests/test_records_counts.py` — AC X2-1 (`:371`), not defined anywhere.
- `tests/test_records_shape.py` — AC X2-3 (`:373`), not defined.
- `tests/test_para_id_cross_check.py` — AC X2-7 (`:377`), not defined. P5 only creates `test_para_id_edges.py` (`:302`).
- `tests/test_digest_render.py::test_header_fields` — AC X3-1 (`:383`), not defined.
- `tests/test_digest_render.py::test_order` — AC X3-2 (`:384`), not defined.
- `tests/test_digest_render.py::test_three_lines` — AC X3-3 (`:385`), not defined.

Only `tests/test_digest_render.py::test_span_marker_roundtrip` is created (in P4b, `:275`).

**Fix.** Add each of these as an explicit bullet under the "먼저 쓰는 테스트" of P4b or P5, or fold them into the existing `test_records_min.py` / `test_digest_min.py` files with named test functions. Preferred: P4b creates `test_digest_render.py::{test_header_fields, test_order, test_three_lines, test_span_marker_roundtrip}` in one file; P4b creates `test_records_shape.py` and `test_records_counts.py`; P5 renames `test_para_id_edges.py` to include `test_para_id_cross_check.py` as a peer file or merges the two.

**References.** `:371, :373, :377, :383-385`.

### D5. [minor] `EXTRACT_THRESHOLDS_PATH` env var used in test but not spelled out in `gates.py`

**Verified partially correct.** Plan `:200` (`test_cli_split_gate.py`) exports `EXTRACT_THRESHOLDS_PATH=<tmp>` and expects the CLI to honor it. But P1's `gates.py` description at `:101–104` says `assert_paragraph_unit_split()` calls `tools.verify.thresholds.load()` — with no argument override path. `tools.verify.thresholds.load(path=DEFAULT_PATH)` (`verify/tools/verify/thresholds.py:29`) accepts a `path` argument, so the mechanism is available, but the plan does not say the wrapper reads the env var. The result is that the test as written will not be red-then-green: implementing `gates.py` per the plan without the env var means the test is untestable, and implementing it per the test means the plan is under-specified.

**Fix.** In `:104`, add "reads `os.environ.get('EXTRACT_THRESHOLDS_PATH')` and passes it (or `DEFAULT_PATH`) to `tools.verify.thresholds.load(path=…)`." Add a test `test_thresholds_env_var_override` in P1 or P4a.

**References.** `:104, :200`; `verify/tools/verify/thresholds.py:29-39` shows `load(path=DEFAULT_PATH)` is safe (YAML only, no DB, no ledger side-effects).

### D6. [minor] P4a "walking skeleton" scope still large enough to freeze several shapes

**Partially resolved.** The plan split P4 into P4a (walking skeleton) and P4b (hardening), which honors Principle 4 more than iteration 1 did. But P4a still creates six modules (`workfile_min`, `records_min`, `digest_min`, `report_min`, `cli`, plus `SKILL.md` and the symlink) with six test files, and it freezes: the CLI subcommand names, the three-line digest item layout, the `record_id = <segment_id>@<sha8>` scheme, the `run.json` group naming (`sources.*`), and the SKILL.md four-rule sentences. If P4a observes something surprising (e.g. sessions consistently need a different `record_id` scheme or SKILL rewrite), P4b still has to unwind those.

**Fix.** Not necessary for iteration 3 — this is a residual trade-off, not a blocker. But note it in ADR "Consequences" so future executors know which P4a decisions are frozen and which are negotiable.

## Item-by-item status vs. reviews

| Item | Source | Status | Evidence |
|---|---|---|---|
| D1 spanning section-null filter | iter-1 Architect | **partial** | Filter removed (`:85, :162`); §1 for line 93 works, but new two-block rule fires 68 spurious hits (D1 above) |
| D2 mutation MISS claim | iter-1 Architect | **resolved** | Test rewritten as `grade != "exact"` with citation `:169-170` |
| D3 queries.load → sys.exit(1) | iter-1 Architect | **resolved** | `:100, :114` add explicit wrapper + test |
| D4 missing PYTHONPATH | iter-1 Architect | **resolved** | Every non-pytest shell command in ACs now has `PYTHONPATH=../verify` (`:350, :351, :365, :372, :374, :379`) |
| D5 empty_memo prose | iter-1 Architect | **resolved** | Single-sentence rule at `:235`, `:274` |
| D6 P4 not thin | iter-1 Architect | **partial** | Split into P4a/P4b; residual scope discussed above |
| B1 spanning filter | iter-1 Critic | **partial** | Same as D1 |
| B2 `paragraph_unit.split` runtime gate | iter-1 Critic | **resolved** | `:104` gate function, `:110-111` unit tests, `:200` CLI test, `:359` AC C0-10; `thresholds.load` verified DB-free |
| B3 un-runnable ACs | iter-1 Critic | **resolved** | Same as D4 |
| M1 not-thin P4 | iter-1 Critic | **partial** | Same as D6 |
| M2 mutation test | iter-1 Critic | **resolved** | Same as D2 |
| M3 vague 18-key list | iter-1 Critic | **partial** | List added `:241-270`, but count/enumeration inconsistent (D3 above) |
| M4 resumability | iter-1 Critic | **resolved** | `test_p4b_precondition`, `test_p5_precondition` (`:273, :299`) assert slice-facts+decisions exist |
| M5 steelman ADR | iter-1 Critic | **resolved** | `:412` adds the "verify absorbs segmenter" alternative with expiry trigger tied to verify P4 |
| m1 QueryError → exit | iter-1 Critic | **resolved** | Same as D3 |
| m2 empty_memo prose | iter-1 Critic | **resolved** | Same as D5 |
| m3 gates.yaml key count | iter-1 Critic | **resolved** | 7 keys at `:105`, X4-1 says "일곱 키" `:391` |
| m4 References anchor | iter-1 Critic | **resolved** | `:135` uses `re.match(r"^\s*References\s*$", …, IGNORECASE)`, not line number |
| m5 SKILL grep | iter-1 Critic | **resolved** | `:204` uses lowercased substring search, four sentences |
| m6 g_recall implementable | iter-1 Critic | **resolved** | `:303-305` adds `gold_empty.md` / `gold_full.md` fixtures |
| m7 record_id sha8 rationale | iter-1 Critic | **resolved** | ADR line at `:414` |

## Principle / binding-constraint violations remaining

- **Principle 1 ("code copies quotes, LLM outputs IDs") — still intact**, verified.
- **Principle 2 ("verify는 라이브러리로만") — intact** but slightly widened by `thresholds.load()` in `gates.py`. `thresholds.load` is DB-free (verified in `verify/tools/verify/thresholds.py:29-39`); `test_no_ledger.py`'s AST check at `:171, :395` explicitly forbids only `thresholds.begin`, not `thresholds.load`, so no violation. No change required, but the plan's phrasing at `:29` should list `thresholds.load` alongside the allowed functions.
- **Principle 4 ("얇은 수직 슬라이스") — partial**, see D6.
- **Binding constraint "each phase resumable from the plan file alone" — partial.** M4 fixes the file-existence gate but the plan file itself still cannot reconstitute the P4a observations that P4b hardens against. Acceptable if the executor commits `slice-facts-<run_id>.json` and `docs/decisions.md`, which the plan tells them to do (`:220`), but this is worth one more sentence in the plan: "P4a's completion is recorded as a paragraph in this plan file under P4a, summarizing what was measured."

## Synthesis — edits for iteration 3

1. **P3/P4a section rule (`.athena/plans/ralplan-paper-evidence-extractor.md:86, :136, :142, :357`).** Tighten rule (ii) so tick labels don't fire it. Concrete acceptance: rule (ii) fires ≤ 15 times against the gold paper (a `tests/test_pagesection.py::test_section_fp_bound` assertion). Suggested regex: `number` matches `^[1-9]\d?(\.\d+){0,2}$` and title-block first line matches `^[A-Z][A-Za-z][A-Za-z -]{2,40}$` (no digits, no parens). If tightening this cleanly is not possible in v1, drop rule (ii) entirely, accept `§—` for §1 blocks, and remove `section == "§1"` from `test_span_line93.py` at `:166, :357` — the L1 exact grade alone still verifies spanning correctness. (Fixes D1.)
2. **P4a scope (`:183`).** Replace "세그먼트 하나짜리 workfile" with "the full segments.json (all display segments) but a minimal downstream chain (records_min → digest_min → 3-key run.json)." Keep the decision-gate value list at `:211-216`. (Fixes D2.)
3. **run.json key list (`:241-270, :276, :392`).** Choose one of: (a) demote `checks.g_recall_report_only` to a nested field inside `checks.para_id_cross_check.value` and keep 18 keys; (b) promote it to its own key, relabel "checks (5)", update the AC text and the test's iteration list to 19. State the literal Python list in the plan so `test_report_shape.py::test_all_keys` uses it verbatim. (Fixes D3.)
4. **Test file creation (`:198-204, :272-277, :298-306`).** In P4b add explicit "먼저 쓰는 테스트" bullets creating `tests/test_records_shape.py`, `tests/test_records_counts.py`, and `tests/test_digest_render.py` with `test_header_fields`, `test_order`, `test_three_lines`, `test_span_marker_roundtrip`. In P5 add `tests/test_para_id_cross_check.py` (or fold its assertions into `tests/test_para_id_edges.py` and update ACs X2-7). (Fixes D4.)
5. **`gates.py` env-var override (`:104`).** Add "reads `os.environ.get('EXTRACT_THRESHOLDS_PATH')` and passes it (or `DEFAULT_PATH`) to `tools.verify.thresholds.load(path=…)`" so the P4a test at `:200` has a symmetric specification. (Fixes D5.)
6. **Principle-2 phrasing (`:29`).** Add `thresholds.load` to the list of allowed pure functions, and update `tests/test_no_ledger.py` at `:171, :395` if needed to explicitly whitelist `thresholds.load` (currently only `thresholds.begin` is denied, so this is documentation-only). (Nit; addresses a small ambiguity.)
7. **Plan-file resumability of P4a→P4b (M4 residual).** Add one sentence to P4a: "On completion, append a 5-bullet summary of the slice-facts measurements to this plan file under P4a's `- [ ] 결정 게이트` bullet so a fresh P4b session can read the observations without opening `slice-facts-<run_id>.json`." (Small hardening of the binding constraint.)

## References

- `.athena/plans/ralplan-paper-evidence-extractor.md:86` — two-block section rule (D1).
- `.athena/plans/ralplan-paper-evidence-extractor.md:136` — pagesection.py behavior (D1).
- `.athena/plans/ralplan-paper-evidence-extractor.md:142, :166, :357` — assertions built on the rule (D1).
- `.athena/plans/ralplan-paper-evidence-extractor.md:183` — "one-segment workfile" (D2).
- `.athena/plans/ralplan-paper-evidence-extractor.md:188, :211-216` — plural segments and decision-gate values (D2).
- `.athena/plans/ralplan-paper-evidence-extractor.md:241-270, :276, :392` — 18-key enumeration and iterator (D3).
- `.athena/plans/ralplan-paper-evidence-extractor.md:371, :373, :377, :383-385` — undefined test node-IDs (D4).
- `.athena/plans/ralplan-paper-evidence-extractor.md:100, :104, :200` — `sys.exit(1)`, `assert_paragraph_unit_split`, env-var test (D5).
- `.athena/specs/deep-interview-paper-evidence-extractor.md:111` — spec-required "통독 한 번" for the whole paper (D2).
- `/work/jun/AI-helper/verify/tools/verify/thresholds.py:29-39` — `load(path)` is DB-free, safe to call from `gates.py` (D5, Principle 2).
- `/work/jun/AI-helper/verify/tools/verify/paragraphs.py:76-87` — `split_blocks` used to reproduce block sequence in the D1 measurement.
- `$KVCPOOL/papers/codex_source_text/codex_workload__year-in-llm-serving.txt:72-74, :167` — text used to verify the two-block rule fires §1 correctly for line-93 spanning.
