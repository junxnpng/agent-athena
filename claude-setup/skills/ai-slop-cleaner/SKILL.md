---
name: ai-slop-cleaner
description: Regression-safe deletion-first cleanup of AI-generated bloat (duplicates, dead code, needless wrappers, weak tests) without scope drift. Has a reviewer-only mode (--review).
argument-hint: "<target file(s) or scope> [--review]"
---

[AI-SLOP-CLEANER ACTIVATED]

<Purpose>
Clean AI-generated code slop in a bounded, regression-safe way. Code that
"works but feels bloated, repetitive, weakly tested, or over-abstracted"
gets a deletion-first pass — behavior preserved by tests, scope locked
to the requested files, no drive-by redesigns. `--review` is a separate
reviewer-only pass over already-drafted cleanup work (writer/reviewer
separation).
</Purpose>

<Use_When>
- User says `deslop`, `anti-slop`, `AI slop`, `clean up AI bloat`
- Code feels noisy / repetitive / over-abstracted but works
- Recent implementation left duplicate logic, dead code, wrapper layers, or weak coverage
- Reviewer-only anti-slop pass requested via `--review`
- Goal is simplification, not new feature delivery
</Use_When>

<Do_Not_Use_When>
- Task is mainly a new feature build → use autopilot or executor
- User wants broad redesign instead of incremental cleanup
- Generic refactor with no simplification intent
- Behavior is too unclear to protect with tests or a verification plan — clarify first
</Do_Not_Use_When>

<Posture>
- Preserve behavior unless the user explicitly asks for changes.
- Lock behavior with focused regression tests FIRST whenever practical.
- Write the cleanup plan before touching code.
- Prefer deletion over addition.
- Reuse existing utilities before introducing new ones.
- No new dependencies unless explicitly requested.
- Diffs small, reversible, smell-focused.
- Stay concise and evidence-dense.
</Posture>

<Steps>

1. **Protect current behavior first**
   - Identify what must stay the same (the contract being preserved).
   - Add or run the narrowest regression tests needed BEFORE editing.
   - If tests cannot come first, write the verification plan explicitly first.

2. **Write a cleanup plan before code**
   - Bound the pass to the requested files / feature area.
   - List the concrete smells to remove (per category below).
   - Order: safest deletion → riskier consolidation.

3. **Classify the slop**
   - **Duplication** — repeated logic, copy-paste branches, redundant helpers
   - **Dead code** — unused exports, unreachable branches, stale flags, debug leftovers
   - **Needless abstraction** — pass-through wrappers, speculative indirection, single-use helper layers
   - **Boundary violations** — hidden coupling, misplaced responsibilities, wrong-layer imports
   - **Missing tests** — behavior not locked, weak regression coverage, edge-case gaps

4. **Run one smell-focused pass at a time**
   - **Pass 1: Dead code deletion**
   - **Pass 2: Duplicate removal**
   - **Pass 3: Naming + error-handling cleanup**
   - **Pass 4: Test reinforcement**
   - Re-run targeted verification after each pass.
   - Do NOT bundle unrelated refactors into one edit set.

5. **Quality gates**
   - Regression tests stay green.
   - Run lint, typecheck, and the relevant unit/integration tests for the touched area.
   - Run any existing static or security checks.
   - On gate failure: fix it or back out the risky cleanup. Never force through.

6. **Report (evidence-dense)**
   - **Changed files** (paths only, not diffs)
   - **Simplifications** (what was removed/consolidated, terse list)
   - **Behavior lock evidence** (test names + pass output snippet)
   - **Remaining risks / deferred items**
</Steps>

<Review_Mode>
`--review` is a reviewer-only pass after cleanup work has been drafted by a
prior writer pass. It exists to preserve writer/reviewer separation —
a single context must NOT both author cleanup and self-approve high-impact removal.

In review mode:
1. Do NOT start by editing files.
2. Inspect the cleanup plan, changed files, and verification evidence.
3. Check specifically for:
   - Leftover dead code or unused exports
   - Duplicate logic that should have been consolidated
   - Needless wrappers that still blur boundaries
   - Missing tests or weak verification for preserved behavior
   - Cleanup that appears to have changed behavior without intent
4. Produce a reviewer verdict (APPROVE / REQUEST CHANGES) with required follow-ups.
5. Hand changes back to a separate writer pass; do NOT fix and approve in one step.
</Review_Mode>

<Ralph_Integration>
ralph (the persistence loop skill) may invoke ai-slop-cleaner as a bounded
post-review cleanup pass when its iteration produced code that has slop smells.

When invoked from ralph:
- Run in standard mode (NOT `--review`)
- Cleanup scope = the ralph session's changed files only (not the whole repo)
- After cleanup, return control to ralph for post-cleanup regression verification
- `--review` remains a deliberate human-triggered follow-up, not a default ralph step
</Ralph_Integration>

<Rules>
- Behavior preservation is non-negotiable. Any cleanup that changes behavior without explicit user OK is a bug — back it out.
- Scope creep is the most common slop-cleaner failure mode. The pass must end at the files in the cleanup plan.
- Treat new user instructions as local scope updates, not as license to expand the pass.
- Same writer context must NOT both write and self-approve high-impact removals — call writer pass + reviewer pass separately (or have a different agent verify).
- Prefer code-reviewer or critic agent for the reviewer pass when delegating.
</Rules>

<Final_Checklist>
- [ ] Behavior locked by tests before code edits (or explicit verification plan written)
- [ ] Cleanup plan written and bounded to requested scope
- [ ] Each smell pass run separately (no bundled refactors)
- [ ] All quality gates pass (tests + lint + typecheck)
- [ ] Diff is deletion-heavy, not addition-heavy
- [ ] Report names changed files + simplifications + verification evidence + remaining risks
- [ ] In `--review` mode: NO file edits made by the reviewer pass
</Final_Checklist>

Target / scope:
{{PROMPT}}
