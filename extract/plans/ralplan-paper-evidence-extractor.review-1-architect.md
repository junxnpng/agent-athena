# Architect Review — ralplan-paper-evidence-extractor (iteration 1)

## Steelman antithesis

You are building a parallel verify-like system that duplicates verify's segmentation, page/section inference, normalization, and reporting layers, while its declared coupling ("verify는 라이브러리로만 부른다") is very thin. Extract re-implements section detection, block-level spanning, page inference from `\f`, sentence segmentation, removal filters, digest rendering, and paragraph_unit reporting — all of which have close analogs in verify or in verify's plan (its `paragraphs.py`, `l1_exists`, `report.py`, `paragraphs.split_blocks`, `queries`). This creates two parallel truths for "what is a paragraph", "what is a body block", "what is section §N", and "what is the paragraph_unit variant". When any real paper triggers a difference between extract's segmenter and verify's block layer, extract diverges silently. The `[sync]` items (`sources.yaml` registration, ledger import, `para_id` equivalence, `codex_raw` block correspondence) then become the reconciliation of two independent implementations, not one. The alternative — extract writes only `segments.json`, and verify consumes and blocks/pages/sections it via its existing `paragraphs.split_blocks` + a small block-to-segments helper *added inside verify* — keeps one source of truth. The plan bets against verify ever being ready; if it is ready in six weeks that bet is lost and the duplicated layers must be retired.

## Tradeoff tensions

- **Precision on spanning targets vs. recall on Section 1 (Introduction).** Plan picks precision by requiring "본문 블록 = ≥20 words **and** non-null section" (`ralplan-paper-evidence-extractor.md:144`). Buys: no false spans into headers/table rows (which are all < 20 words anyway). Costs: the gold paper's own `line 93` test case falls in Section 1, where `1` and `Introduction` are two separate blocks (see below), so the section is null and the spanning target is filtered out. Just relaxing to "≥20 words" would recover recall at essentially no precision cost, because the 20-word gate already filters headers and table cells (Table 1 caption = 13 words, header block "Nixon et al." = 3 words).
- **"Thin slice" as observation before hardening vs. P4 building most of the system.** Plan picks C1 ("얇은 수직 슬라이스"), but P4 is not a slice: it introduces workfile.py, records.py, digest.py, report.py, cli.py, SKILL.md, symlink, six workfile rejection reasons, section-null rendering, spanning marker roundtrip, and eighteen `run.json` keys, with seven test files. Buys: definitive first measurement of LLM selection behavior. Costs: ~10 modules and ~200 lines of shape decisions are frozen (workfile 6 reasons, digest marker convention `⏎p.N`, `record_id` sha8 scheme) before any Claude selection is observed — precisely the shapes P4 was supposed to inform.
- **`empty_memo` sentinel doubling as `newline_in_memo` vs. distinct reason codes.** Plan picks doubling ("사유는 여섯 개로 닫혔으므로 … `empty_memo` 사유로 거부한다", `:168`). Buys: closed set of six reasons. Costs: the reason code `empty_memo` no longer describes what the user did wrong; the paragraph explaining this is internally contradictory ("`empty_memo`가 아니라 … `empty_memo` 사유로 거부한다").
- **Own `extract.paths` (own `SOURCE_ENV = "KVCPOOL"`, own `source_root`) vs. reuse of `tools.verify.paths`.** Plan picks own (`:92`). Buys: extract stands alone, no accidental verify coupling. Costs: two definitions of `SOURCE_ENV` that must be kept in lockstep; when verify adds a new env fallback, extract silently diverges.

## Verified defects

### D1. [blocker] Section-null filter in P3 spanning kills `test_span_line93.py`

**Verified wrong.** The plan's spanning target rule is "본문 블록 = ≥20 words **and** section이 null이 아닌 블록" (`ralplan-paper-evidence-extractor.md:144`), with section detection `^(\d+(?:\.\d+)*)\s+([A-Z].+)$` (`:118`).

Evidence, measured on the actual gold paper text (`$KVCPOOL/papers/codex_source_text/codex_workload__year-in-llm-serving.txt`):

- Lines 72–74 are `1\n\nIntroduction\n`: `1` is one blank-line block and `Introduction` is another. The single-line regex never matches either alone.
- With `split_blocks` on the real pdftotext output (697 blocks), the first regex match is at seq 37 ("2 Background"). The next hit is seq 0021 header "2 Background" onward.
- Line 93's continuation lands in `block seq=35` ("highly skewed popularity and support users with diverse…", 290 words). Under the plan's rule, block 35's section is null, so it is filtered out of spanning targets, and the spanning between block 20 and block 35 is never emitted. The `check_quote` on the never-emitted spanning `quote` cannot return `exact`.

Concrete fix: **drop the `section != null` requirement from the "본문 블록" definition** (keep ≥ 20 words). Alternatively, treat "digits-only block immediately followed by a `Title Case` block" as a two-block section marker. The first fix is smaller and enough — headers and table cells in this paper are all < 20 words, so the ≥ 20-word gate alone is not lossy in practice.

References:
- Plan: `.athena/plans/ralplan-paper-evidence-extractor.md:118` (section regex), `:144` (본문 블록 rule).
- Real text: `$KVCPOOL/papers/codex_source_text/codex_workload__year-in-llm-serving.txt:72-74` and `:167`.
- Runtime measurement (session output above): between end-block seq=20 and target block seq=35 there are 14 intervening blocks, all ≤ 15 words except the end-block itself.

### D2. [major] `test_existence_library.py`: single-char mutation is not guaranteed MISS

**Verified partially wrong.** Plan claims (`:150`): "그 세그먼트에 한 글자를 바꾸면 `MISS`가 나온다." The gapped grade in verify (`verify/config/normalization.yaml:52-54`: `min_run: 20, max_runs: 3, max_gap_chars: 1000`) is designed exactly to tolerate mid-quote intrusions.

Empirical check I ran with `check_quote` against constructed haystacks showed MISS for two mutation patterns, so the *specific* test the plan sketches can be made to pass. But the plan's principle ("MISS는 언제나 세그먼트 분할·복사 경로의 버그", `:369`) is stronger than the test: if the mutated quote is long and the mutation sits ≥ 20 chars from either end, `_runs` (`l1_exists.py:82-105`) can split the loose-form needle into two 20+ char runs and still find them in-order — grade `gapped`, not MISS. The MISS result depends on where the mutation lands.

Concrete fix: state the test as `grade != "exact"` (or `grade in {"strict","loose","gapped","MISS"}`), not `grade == "MISS"`; if the intent is truly MISS, force the mutation into a position < `min_run` from a needle end and add a comment saying the test relies on `min_run=20`.

References:
- Plan: `.athena/plans/ralplan-paper-evidence-extractor.md:150`, `:369`.
- Code: `/work/jun/AI-helper/verify/tools/verify/l1_exists.py:82-105`, `/work/jun/AI-helper/verify/config/normalization.yaml:52-54`.

### D3. [minor] `queries.load` raises, does not `sys.exit(1)`

**Verified accurate but under-specified.** Plan says the wrapper's exit code 1 fires "필수 필드가 빠진 경우에만" (`:93`), and C0-1 asserts a shell command with exit 1 on the missing case (`:265`). The verify function actually raises `QueryError` (`verify/tools/verify/queries.py:26-27`), never `sys.exit`. This is fine only if `extract.query.load` (or the CLI entry) explicitly catches `QueryError` and returns / `sys.exit(1)`. Plan should say so, and the P1 tests should exercise it.

Reference: `/work/jun/AI-helper/verify/tools/verify/queries.py:21-31`.

### D4. [minor] Exit-check commands run `python -m tools.verify …` from `extract/` without setting `PYTHONPATH`

**Verified wrong for the CLI path.** The plan's P4 Exit check (`:202`) and X2-2 (`:286`) use `.venv/bin/python -m tools.verify …` and `.venv/bin/python -c "from tools.verify.schema import validate; …"` while `cd extract`. `pytest.ini`'s `pythonpath = . ../verify` only applies to pytest, not to `python -m` or `python -c`. So these commands as written fail with `ModuleNotFoundError: tools`. Fix: either prepend `PYTHONPATH=../verify` in the acceptance commands, or add a `sitecustomize.py` / `.pth` under `extract/.venv/lib/python3.10/site-packages/` that adds `../verify`. Prefer the explicit `PYTHONPATH=…` on the command lines because the plan claims the runs should be reproducible without hidden environment setup.

References: `.athena/plans/ralplan-paper-evidence-extractor.md:202,266,286`.

### D5. [minor] The workfile-rejection paragraph is self-contradictory

**Verified confusing, not wrong.** Plan `:168`: "memo에 줄바꿈이 있으면 `empty_memo`가 아니라 `invalid_kind`도 아닌 새 사유가 아니라 「빈 memo」와 같은 취급으로 `empty_memo` 재사용은 하지 않는다 — 사유는 여섯 개로 닫혔으므로 `unexpected_field`가 아니라면 `empty_memo`로 통일하지 않고, memo에서 `\n`이 발견되면 `empty_memo`가 아니라 「비지 않은 한 줄 memo만 허용」이라는 X1의 기준으로 `empty_memo` 사유로 거부한다." The paragraph negates and re-affirms the same outcome. Rewrite in one sentence: "memo is invalid if empty or contains `\n`; both are rejected under `empty_memo`." X1-4 (`:280`) then makes sense as one test asserting `\n`-in-memo → `empty_memo`.

### D6. [minor / decision drift] Principle 4 vs. actual P4 shape

**Verified partially wrong.** Principle 4 (`:18`) says the thin slice should be observed before hardening. P4 (`:161–204`) requires seven test files and ~ten new modules and freezes eighteen `run.json` keys and six workfile rejection codes before any Claude selection is seen. This is the same "층별 완성 후 슬라이스" pattern that option C2 was rejected for on `:54`. A truer slice would be: segment.json with 1 segment → hand-written 1-selection.jsonl → 1 record → 1-line md digest → 3-key report; freeze the eighteen keys only in P5. Trade-off: the current shape gives a single P4 milestone but the same milestone locks the workfile format.

## Verified confirmations (not defects)

To keep the Planner from over-editing, these plan claims are verified true:

- Package layout A1 is correct: `verify/tools/__init__.py` is a regular package (`/work/jun/AI-helper/verify/tools/__init__.py` present, empty), so a namespace-extended `tools.extract` under `extract/` is impossible; putting `extract` at the top level and adding `../verify` to `pythonpath` gives a collision-free import graph. I ran `PYTHONPATH=.:/work/jun/AI-helper/verify python3 -c "from tools.verify import paragraphs, l1_exists, normalize, schema"` from an empty `extract/` skeleton — it succeeded.
- `verify/tools/verify/paths.py:8` resolves `ROOT` from `__file__`, not `cwd`. Extract can import `tools.verify.schema` and `tools.verify.l1_exists` from anywhere; `verify/config/normalization.yaml` and `evidence_record.schema.json` are found regardless of the calling process's cwd.
- `schema.validate` (`verify/tools/verify/schema.py:37-92`) accepts extra top-level keys silently and accepts `"unextracted"` as a `conditions.*` value (only empty strings, missing keys, or non-string types are quarantined). So the plan's design — five `unextracted` values, `numbers: []`, extra `resolved_para_ids` key — passes.
- `paragraphs.PIECE_SPLIT = re.compile(r"…|\.\.\.|\[[^\]]*\]|\*\*|\|")` (`verify/tools/verify/paragraphs.py:22`). I confirmed by direct run that `check_quote("piece1 […] piece2", [Variant("extract_raw", …)])` returns `Result(grade="exact", per_variant={"extract_raw":"exact"})` when both pieces are contiguous substrings in order. So the spanning contract holds — assuming D1 is fixed and the spanning is actually emitted.
- `ledger._insert_claim` (`verify/tools/verify/ledger.py:457`) already reads `item.get("resolved_para_ids", [])`; the extra field passes cleanly into the ledger during the eventual `[sync]`.
- `pdftotext -q` on the gold PDF produces 16 `\f` characters (I ran `pdftotext … | tr -d -c '\f' | wc -c` → `16`). The plan's page-inference math (`page = 1 + count of \f before block start`) works.

## Principle violations

- The plan's own **Principle 4** ("얇은 수직 슬라이스가 하드닝의 근거를 만든다") is violated in practice by P4's size. See D6.
- **Binding user constraint** "phases must be resumable in a fresh session from the plan file alone" — partially at risk: the P4 slice depends on measured facts written to `slice-facts-<run_id>.json` (`:175`) and on hand-recorded decisions ("결정 게이트 (사람)", `:204`) that live outside the plan file. If a fresh session resumes at P5 without reading `slice-facts-*.json`, the hardening scope is under-specified. Concrete fix: state in the plan that `slice-facts-<run_id>.json` and a `docs/decisions.md` snapshot must exist and must be linked from this file before P5 starts.
- No other user-constraint violation seen: relative paths, English code/comments, no phase labels in code, `gold-kv-reuse.yaml` unconfirmed handled, `[sync]` items deferred behind verify P4–P7.

## Synthesis — edits for the next iteration

1. **P3, `spanning.py` rule (`ralplan-paper-evidence-extractor.md:144`)**: drop the `section != null` requirement from "본문 블록". Keep ≥ 20 words. Add an inline comment that headers and table cells in the gold paper are ≤ 15 words. (Fixes D1; unblocks `test_span_line93.py`.)
2. **P3, `test_existence_library.py` (`ralplan-paper-evidence-extractor.md:150`)**: state the mutation test as `grade != "exact"` (or force the mutation into position < 20 chars from either end, with a comment referencing `verify/config/normalization.yaml:52-54`). (Fixes D2.)
3. **P1, `extract/extract/query.py` (`:93`)**: add an explicit sentence "converts `queries.QueryError` into `sys.exit(1)`" and add that assertion to `tests/test_query_loader.py`. (Fixes D3.)
4. **AC/Exit-check commands (`:202,266,286`)**: prepend `PYTHONPATH=../verify` (or `PYTHONPATH=.:$( pwd )/../verify`) to every `python -m tools.verify …` and `python -c "from tools.verify.…"` invocation in the AC. (Fixes D4.)
5. **P4, `workfile.py` reasons (`:168`)**: rewrite the confusing paragraph to a single sentence: "memo is `empty_memo` iff `not memo.strip()` or `"\n" in memo`. The six-code closure is preserved." (Fixes D5.)
6. **P4, thin-slice cut (`:161-204`)**: split P4 into two phases: **P4a walking skeleton** (one-segment segment.json + hand-written one-line selection + one-line digest + three-key `run.json`) and **P4b** (six-reason workfile + eighteen-key `run.json` + digest spanning marker) predicated on P4a's measured facts. Move `test_digest_render.py::test_span_marker_roundtrip`, `test_report_shape.py`, and the six workfile rejection tests into P4b. (Addresses D6 and Principle 4.)
7. **Resumability (`:63-72`)**: add a bullet "before starting P5, `slice-facts-<run_id>.json` and `extract/docs/decisions.md` must both exist and be committed; the plan file lists their paths verbatim." (Addresses the binding user constraint.)
8. **Steelman answer (optional)**: add a one-paragraph ADR alternative reading "verify absorbs the segmenter" — record why extract is standalone (verify's Non-Goal declaration + user's decision 2026-09-23), and set a follow-up trigger "revisit standalone status when verify P4 lands" so this bet has an expiry.

## References

- `/work/jun/AI-helper/.athena/plans/ralplan-paper-evidence-extractor.md:118` — section regex (D1).
- `/work/jun/AI-helper/.athena/plans/ralplan-paper-evidence-extractor.md:144` — "본문 블록" rule (D1).
- `/work/jun/AI-helper/.athena/plans/ralplan-paper-evidence-extractor.md:150` — mutation test claim (D2).
- `/work/jun/AI-helper/.athena/plans/ralplan-paper-evidence-extractor.md:168` — self-contradictory `empty_memo` paragraph (D5).
- `/work/jun/AI-helper/.athena/plans/ralplan-paper-evidence-extractor.md:202,266,286` — commands without `PYTHONPATH` (D4).
- `/work/jun/AI-helper/verify/tools/verify/paragraphs.py:22` — `PIECE_SPLIT`, confirms `[…]` elision handling.
- `/work/jun/AI-helper/verify/tools/verify/paragraphs.py:76-87` — `split_blocks`, confirms `\f`→`\n` behavior.
- `/work/jun/AI-helper/verify/tools/verify/l1_exists.py:82-105` — `_runs`, root of D2 concern.
- `/work/jun/AI-helper/verify/tools/verify/l1_exists.py:162-173` — `check_quote` confirmed usable with single-`Variant` list.
- `/work/jun/AI-helper/verify/tools/verify/schema.py:37-92` — `validate`, confirms extra keys and `"unextracted"` pass.
- `/work/jun/AI-helper/verify/tools/verify/queries.py:21-31` — `load` raises, does not exit (D3).
- `/work/jun/AI-helper/verify/tools/verify/paths.py:8` — file-relative `ROOT`, resolves config from anywhere.
- `/work/jun/AI-helper/verify/tools/verify/ledger.py:457` — `resolved_para_ids` already recognized by verify.
- `/work/jun/AI-helper/verify/tools/__init__.py` — regular package, blocks A2 namespace approach as the plan claims.
- `/work/jun/AI-helper/verify/config/normalization.yaml:52-54` — gapped rules `min_run=20, max_runs=3, max_gap_chars=1000` (D2).
- `/work/jun/priv-mb-eval/kvcpool-trace-gen/papers/codex_source_text/codex_workload__year-in-llm-serving.txt:72-74` — `1` / blank / `Introduction` block layout (D1).
- `/work/jun/priv-mb-eval/kvcpool-trace-gen/papers/codex_source_text/codex_workload__year-in-llm-serving.txt:167` — continuation of the line 93 sentence (D1).
