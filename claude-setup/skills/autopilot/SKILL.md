---
name: autopilot
description: Full autonomous execution from idea to working code
argument-hint: "<product idea or task description> [--review=heavy]"
---

<Purpose>
Autopilot takes a brief idea and autonomously handles the full lifecycle:
spec → plan → implement → QA → validate. Produces working, verified code.
</Purpose>

<Use_When>
- User says "autopilot", "build me", "create me", "full auto"
- Task requires multiple phases: planning, coding, testing, validation
- User wants hands-off execution to completion
</Use_When>

<Do_Not_Use_When>
- Quick fix or single file change → delegate to executor directly
- Exploring options or brainstorming → delegate to architect (design) or critic (devil's advocate) directly
- User wants step-by-step control → work interactively
</Do_Not_Use_When>

<Steps>
**Plan-path short-circuit (applies before Phase 0):** if the input is a path string (matches `^[^ ]+\.md$`, file exists, AND contains a `## Acceptance Criteria` or `### Acceptance Criteria` heading), the spec is considered already produced (by ralplan, deep-interview, or deep-dive). SKIP Phase 0 and Phase 1 entirely — read the plan and proceed directly to Phase 2 with its acceptance criteria. The `Acceptance Criteria` heading is the canonical signal — uniform with ralph's plan-path detection — so a README with `## Plan` does NOT short-circuit. If the regex matches but the heading is absent, the input is treated as ambiguous and falls through to Phase 0 with a logged note (do NOT silently re-decompose the path string itself). This prevents ralplan→autopilot ping-pong: ralplan's consensus plan is the contract, autopilot must NOT re-decompose it.

1. **Phase 0 — Expansion** (only if no plan-path supplied): Turn the idea into a detailed spec
   - Use architect (opus) to extract requirements and create technical spec
   - Use critic (opus) to challenge assumptions and find gaps
   - Output: clear requirements with acceptance criteria
   - If input is vague (no files, functions, or concrete anchors): ask for clarification first

2. **Phase 1 — Planning** (only if no plan-path supplied): Create an implementation plan
   - Use planner (opus) to decompose into ordered steps
   - Use critic (opus) to validate the plan
   - Identify parallel opportunities and risks

3. **Phase 2 — Execution**: Implement the plan
   - Delegate to executor (default opus 4.7) — fire independent tasks in parallel
   - Use `run_in_background: true` for long builds/tests so Phase 3 can prepare in parallel
   - Save state to `.athena/state/autopilot.json` after each step

4. **Phase 3 — QA**: Cycle until all checks pass
   - Build, lint, typecheck, test
   - Fix failures and repeat (max 5 cycles)
   - If same error persists 3 times → stop and report fundamental issue

5. **Phase 4 — Validation**: Pick review depth based on user intent.

   **Default (M — medium):** parallel review with
   - code-reviewer: quality, logic, conventions
   - critic: devil's advocate — hidden assumptions, weak invariants, attack surface
   - verifier: completion verification with evidence

   **Heavy (H) — escalate to multi-review when ANY of these signals are present:**
   - User prompt contains `--review=heavy`, `thorough`, `deep validation`, `multi-review`, or names a security-critical domain (auth, payments, key handling, deserialization, file uploads)
   - Phase 1 plan flagged the work as production-critical
   - Then call `/athena:multi-review` skill on the diff/branch + verifier on top.

   All chosen reviewers must approve; fix and re-validate on rejection (max 3 rounds).

6. **Phase 5 — Cleanup**: Clear state on success
   - Remove `.athena/state/autopilot.json`
   - Report summary of what was built
</Steps>

<Escalation>
- Same QA error 3 cycles → report as fundamental issue
- Validation fails 3 rounds → stop and report
- User says "stop"/"cancel" → invoke cancel skill
- Missing info → ask user before proceeding
</Escalation>

<Final_Checklist>
- [ ] All 5 phases completed
- [ ] All validators approved
- [ ] Tests pass (fresh output shown)
- [ ] Build succeeds (fresh output shown)
- [ ] State files cleaned up
</Final_Checklist>

Original task:
{{PROMPT}}
