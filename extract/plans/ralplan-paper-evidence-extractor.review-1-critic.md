## Critique: ralplan-paper-evidence-extractor (iteration 1)

### What's Being Proposed

Build a query-based evidence extractor in a new top-level `extract/` package that (a) turns a PDF into `extract_raw` via `pdftotext`, (b) slices it into sentence segments inside verify's paragraph blocks, (c) hands the segments to a Claude Code skill through a sealed file round-trip, (d) copies quotes into `evidence_record.schema.json`-shaped JSONL by ID (never by LLM re-typing), and (e) renders a per-paper digest and a `run.json` report. Coupling to verify stops at pure-function library calls; ledger, thresholds, and `sources.yaml` registration are `[sync]` work. The plan structures this as P1 skeleton → P2 text layer → P3 spanning + L1 → P4 thin slice → P5 hardening → P6 coverage, with a "decision gate" between P4 and P5. Principle 1 (code copies quotes) is the core correctness argument.

### Coverage Table — spec `[v1]` → plan phase → plan AC bullet

| Spec `[v1]` (paraphrased) | Phase | AC bullet | Adequate? |
|---|---|---|---|
| C0 · query file load, required fields, `unconfirmed` | P1 | C0-1 | Yes (see D3) |
| C0 · `extract_raw` source, PDF sha, poppler ver in report | P2 (report in P4) | C0-2 | Partial — C0-2 references `run.json` written by the P4 CLI, not P2 |
| C0 · `extract_raw == codex_raw` → verify blocks match | P2 | C0-3 | Yes |
| C0 · segment ↔ block text byte round-trip | P2 | C0-4 | Yes |
| C0 · `segmenter.yaml`, abbreviation unit tests | P2 | C0-5 | Yes |
| C0 · page/section, `\f=16`, null section count | P2 | C0-6 | Yes |
| C0 · removal closed (refs/header/arxiv), 2,248-word ref count | P2 | C0-7 | Yes |
| C0 · line-93 spanning, `[…]` L1 exact | P3 | C0-8 | **Broken by D1** — target block has section=null so the `본문 블록` filter (plan:144) throws it away |
| C0 · `extract_raw` vs `codex_raw` sha diff, first difference position | P4/P5 | C0-9 | Yes |
| C0 · **`paragraph_unit.split` must be `blank_line_block` else refuse to run** | **missing** | **missing** | Blocker — spec:94 explicitly requires this runtime gate; no bullet, no phase |
| X1 · SKILL.md + symlink | P4 | X1-1 | Yes |
| X1 · six-reason file round-trip | P4 | X1-2 | Yes (but see D5) |
| X1 · single-pass read; body words + est. tokens | P4 | X1-3 | Partial — the "18 keys" of `run.json` are not enumerated |
| X1 · memo single-line; `\n` rejected | P4 | X1-4 | Yes (via D5-fixed prose) |
| X1 · SKILL four rules | P4 | X1-5 | Testable via grep, but the grep regex is brittle |
| X2 · counts closed (N=N, quarantine 0) | P4 | X2-1 | Yes |
| X2 · field contract | P4 | X2-3 | Yes |
| X2 · `verify schema --validate` → pass N, quarantine 0 | P4 | X2-2 | **Broken by D4** — command imports `tools.verify.schema` with no PYTHONPATH |
| X2 · `unextracted` × 5; no `none` | P4 | X2-4 | **Broken by D4** — same import issue |
| X2 · L1 exact against `extract_raw`, N/N | P3+P4 | X2-5 | Yes (test-level) |
| X2 · `codex_raw` grade distribution (report only) | P5 | X2-6 | Yes |
| X2 · `para_id` cross-check | P5 | X2-7 | Yes |
| X2 · per-variant grades, "text-layer scramble suspect" list | P5 | X2-8 | Yes |
| X2 · kind + memo N/N | P4 | X2-9 | Yes |
| X3 · digest header 9 fields | P4 | X3-1 | Yes |
| X3 · order (page → block seq → sent no) | P4 | X3-2 | Yes |
| X3 · three-line item | P4 | X3-3 | Yes |
| X3 · spanning marker `⏎p.N` round-trip | P4 | X3-4 | Yes, but the "collapse whitespace" step is under-defined |
| X3 · digest deterministic | P6 | X3-5 | Yes |
| X4 · `gates.yaml` sha256 in report | P1+P4 | X4-1 | Yes; but plan lists 8 keys while spec lists 7 (extra `paragraph_unit_variant`) |
| X4 · `run.json` full shape | P4/P5 | X4-2 | **Vague** — "열여덟 항목" is asserted without enumerating them |
| X4 · G recall report-only | P5 | X4-3 | Yes, but "값을 인위로 0으로 놓고" is implementation-dependent |
| X4 · tests-first + ≥ 80 % coverage | P6 | X4-4 | Yes |

`[이후]` (6 spec items) and `[sync]` (9 spec items) are all parked in Deferred; nothing has slipped into v1.

### Independent spot-check of the Architect's key findings

- **D1 — CONFIRMED, blocker.** I opened `codex_workload__year-in-llm-serving.txt`: lines 72–74 are `1` / blank / `Introduction` and line 167 begins `highly skewed popularity and support users with diverse…`. The regex at plan:118, `^(\d+(?:\.\d+)*)\s+([A-Z].+)$`, requires digits and title on the same line and matches neither block, so section propagation before line 167 stays null. The block starting at line 167 has section=null, and the plan's `본문 블록 = ≥20 words AND section != null` gate (plan:144) filters it out of spanning targets. The line-93 spanning is never emitted, so `check_quote` at C0-8 cannot return `exact`. This kills the load-bearing test.
- **D2 — CONFIRMED, major.** `check_quote` iterates `exact → strict → loose → gapped` (`l1_exists.py:148-159`) with `min_run=20, max_runs=3, max_gap_chars=1000`. A single-char mutation in the interior of a > 40-char quote leaves ≥ 20 canonical chars on either side and returns `gapped`, not `MISS`. The plan's principle "MISS는 언제나 세그먼트 분할·복사 경로의 버그" (plan:369) is therefore not enforced by a "single-char mutation → MISS" test.
- **D4 — CONFIRMED, more consequential than the Architect labeled it.** The plan's exit checks and shell-embedded ACs at :202, :266, :286 all use `python -m tools.verify …` or `python -c "from tools.verify.schema import validate"` from `extract/` with no `PYTHONPATH`. `pytest.ini`'s `pythonpath` only applies inside pytest, not to `python -m` or `python -c`. Multiple ACs (C0-2, X2-2, X2-4, P4 exit check) fail on the command as written.

### Findings

#### Blockers

1. **B1 — P3 spanning rule discards its own fixed test target (Architect D1).**
   Required change: at plan:144 drop the `section != null` requirement from "본문 블록" and keep only "≥ 20 words". Alternately, add a two-block section rule for `digits-only block` immediately followed by `Title Case block`. Without one of these, C0-8 / `test_span_line93.py` and Principle 1's constructive guarantee cannot both hold.

2. **B2 — Missing spec-mandated runtime gate on `paragraph_unit.split`.**
   Spec:94 requires that the runner refuse to execute unless `verify/config/thresholds.yaml`'s `paragraph_unit.split == "blank_line_block"`. No phase, no AC bullet mentions this. Required change: add a check to `extract/extract/gates.py` (or `paths.py`) called at CLI entry, and add an AC bullet under C0.

3. **B3 — Multiple ACs are un-runnable as written (Architect D4).**
   Every `python -m tools.verify …` and `python -c "from tools.verify.…"` in the plan (plan:202, :266, :286) needs `PYTHONPATH=../verify` prepended, or `extract/.venv` needs a `.pth` entry that adds `../verify`. Because the plan explicitly claims runs should reproduce "without hidden environment setup," prefer inline `PYTHONPATH=…` on every command.

#### Majors

4. **M1 — P4 is not a thin slice (Architect D6), violates Principle 4.**
   P4 introduces `workfile.py`, `records.py`, `digest.py`, `report.py`, `cli.py`, `SKILL.md`, symlink, 6 rejection reasons, spanning marker round-trip, 18 `run.json` keys, and 7 test files — the shape decisions that P4 was supposed to be informed by. Required change: split into **P4a (walking skeleton)** — 1 segment → 1-line hand-written `selections.jsonl` → 1 record → 3-key `run.json` → 1-item digest — and **P4b (six-reason workfile + full report + spanning marker)**, gated on P4a's slice-facts. This matches the C1 option the DR claims to choose.

5. **M2 — `test_existence_library.py` mutation may return `gapped`, not `MISS` (Architect D2).**
   State the mutation test at plan:150 as `grade != "exact"` (or `grade in {"strict","loose","gapped","MISS"}`) or force the mutation to land within `min_run` chars of a needle end and cite `normalization.yaml:52-54`.

6. **M3 — X4-2 AC is vague ("18 items").**
   The plan asserts `run.json` has "eighteen items" but does not enumerate them. Anyone executing the plan will guess a different 18. Required change: list the eighteen key paths verbatim (grouped as: sources 5, segments 4, selections 5, checks 4), and make `test_report_shape.py::test_all_keys` iterate over that literal list.

7. **M4 — Resumability of P5 depends on artifacts outside the plan file.**
   `slice-facts-<run_id>.json` is a runtime artifact (plan:175, :191–197) that a fresh P5 session cannot reconstruct from the plan alone. This violates the binding "each phase resumable from the plan file alone." Required change: add to the plan a bullet "before P5 begins, `results/gold-kv-reuse/slice-facts-<run_id>.json` and `extract/docs/decisions.md` MUST exist and be committed; P5's opening test asserts their presence."

8. **M5 — Architect's antithesis (verify absorbs the segmenter) is never answered in the DR.**
   The plan invokes "verify declares extraction Non-Goal" as if that settled it, but verify's Non-Goal was about *selection*, not *sentence segmentation*. verify already owns block-level `split_blocks`; a small `block-to-sentences` helper could naturally live in verify's `paragraphs.py`. The plan bets that verify will not add it. Required change: add one paragraph to ADR "Alternatives considered" that (i) states this option, (ii) records the user's 2026-09-23 decision that "verify coupling stops at the file contract" as its refutation, and (iii) sets an explicit expiry: "revisit standalone status when verify P4 lands."

#### Minors

9. **m1 — D3 (queries.load raises, does not exit).** Add "converts `queries.QueryError` into `sys.exit(1)`" to plan:93 and add an explicit test to `test_query_loader.py`.

10. **m2 — D5 workfile paragraph is self-contradictory.** Replace plan:168 with the single sentence "memo is `empty_memo` iff `not memo.strip()` or `"\n" in memo`; the six-code closure is preserved."

11. **m3 — `gates.yaml` has 8 keys but spec X4 enumerates 7.** Either drop `paragraph_unit_variant` (already implied by `l1_variant`), or add a spec-provenance note explaining why this 8th key is here. Fix `test_required_keys` accordingly.

12. **m4 — `codex_raw` 2489행 hardcoded as References anchor.** If poppler drift moves lines, the anchor breaks. Structural detection (blank line + block whose first line matches `^References$`) is more robust.

13. **m5 — X1-5 grep regex is brittle.** `grep -Ec '^(방향을 가리지 않는 관련성|…)'` requires exact line-start prefixes. Easy for SKILL.md to inadvertently prepend a bullet marker and fail. Prefer four sentence-level assertions.

14. **m6 — X4-3 test premise ("값을 인위로 0으로 놓고") is not implementable without a monkeypatch hook.** Specify how the g_recall value is forced to 0 (env var? synthetic gold file?), or reduce the AC to a static "gates.yaml declares g_recall: report_only" check.

15. **m7 — sha8 = selections.jsonl sha256 앞 8자, 매 실행 다름 (plan:76).** `record_id` therefore changes every run. Reasonable, but should be called out as a design consequence (not a bug) so someone doesn't try to "fix" it. Not a defect, but worth an ADR line.

### Hidden Assumptions

- **The gold paper's plaintext will remain byte-identical to `codex_raw` under whatever poppler the developer has.** The plan pins 22.02.0 and asserts byte equality, but any drift silently skips `test_blocks_align_with_codex_raw` and hides real divergences. The Risks section mentions this; a `run.json` field alone is passive.
- **Every reference block in every future paper starts with a block literally beginning with `References`.** The plan uses this in P2. Some ACM/USENIX PDFs use `REFERENCES` or bibliography formatting with column headers first.
- **`paragraphs.resolve` will always ground the cross-check.** For short segments (< 20 canonical chars AND < 9 words), verify returns empty; the plan says these are "put in a list," but the list is not gated for X2-7 pass/fail.
- **The Claude Code session model that runs the skill will faithfully write `{segment_id, kind, memo}` and nothing else.** The six rejection reasons are a strong contract, but if the model persists in writing `quote` fields, the whole file is rejected on every attempt. The plan has no retry loop or "next-run" convention.

### What If You're Wrong About…

- **verify staying paragraph-only.** If verify P4 or later adds sentence-level segmentation for its own purposes (e.g., for `convert/gold.py`'s sentence-level G recall — a `[이후]` item you already committed to), you now have two segmenters and two page-inference rules on the same paper. The `[sync]` list grows to include reconciliation of segmenter output, not just `sources.yaml` registration. The plan has no expiry for the "standalone extract" decision.
- **`pdftotext` default mode staying byte-equal to `codex_raw` across the inbox.** Measured 2026-09-23 on the gold paper only. The final goal is "one query × every PDF in `inbox/`." If mode drift shows up in even one inbox paper, `codex_raw`-derived confidence and manifest cross-checks are useless for that paper, and the `[sync]` "register `extract_raw` in `sources.yaml`" item becomes required *before* v1 finishes, not after.
- **Single Claude session producing consistent kind/memo across a 10 K-word body.** The plan measures selection behavior once, then freezes the gate. If sessions vary widely in `boundary_flag` frequency and 20-word-block selections, the "decision gate" becomes a moving target.

### Architect items — endorsements

- **Endorse D1, D2, D3, D4, D5.** Verified above; D4 should be elevated to **blocker** because it breaks several `[R]`-mode ACs as-written.
- **Endorse D6** and elevate to **major** — Principle-4 self-violation is not a minor issue; it is the difference between a plan that observes-then-hardens and one that hardens by fiat.
- **Endorse synthesis items 1, 2, 3, 4, 5, 6, 7** verbatim.
- **Endorse synthesis item 8** (steelman "verify absorbs the segmenter") but strengthen it: this is not optional. The plan's Alternatives section already lists five rejected options and the antithesis is not among them.

### What's Genuinely Strong

- The "code copies quotes, LLM outputs IDs" invariant (Principle 1) is a real correctness argument, not decoration, and is testable.
- Package layout A1 is empirically verified — the Architect ran `PYTHONPATH=.:.../verify python -c "from tools.verify import …"` and it works. The A2/A3 refutations are honest, not straw-manned.
- The registered-gate vs decision-gate separation is a good structural idea and mirrors verify's P1/P3 discipline.
- Spanning-marker round-trip (`quote` ↔ `⏎p.N` ↔ `[…]`) as an AC is thoughtful — it will catch a whole class of digest-renderer bugs cheaply.

### Bottom Line

The plan is well-structured, empirically grounded, and (via A1 and the sealed round-trip) makes the right coupling decisions, but it is not executable as written: the section-null filter in P3 kills its own fixed test target (D1), the shell commands in four ACs fail because `PYTHONPATH` is unset (D4), a spec-mandated runtime gate (`paragraph_unit.split`) is silently missing, and P4 hardens shape decisions that Principle 4 promised to leave to observation. Fix D1, D4, the missing `split` gate, and split P4 into P4a/P4b before handing this to an executor.

VERDICT: ITERATE
