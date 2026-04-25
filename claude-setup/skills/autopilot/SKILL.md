---
name: autopilot
description: Full autonomous execution from idea to working code
argument-hint: "<product idea or task description>"
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
- Exploring options or brainstorming → use plan or ideate skill
- User wants step-by-step control → work interactively
</Do_Not_Use_When>

<Steps>
1. **Phase 0 — Expansion**: Turn the idea into a detailed spec
   - Use architect (opus) to extract requirements and create technical spec
   - Use critic (opus) to challenge assumptions and find gaps
   - Output: clear requirements with acceptance criteria
   - If input is vague (no files, functions, or concrete anchors): ask for clarification first

2. **Phase 1 — Planning**: Create an implementation plan
   - Use planner (opus) to decompose into ordered steps
   - Use critic (opus) to validate the plan
   - Identify parallel opportunities and risks

3. **Phase 2 — Execution**: Implement the plan
   - Delegate to executor (sonnet) — simple tasks
   - Delegate to executor with model=opus — complex tasks
   - Run independent tasks in parallel
   - Save state to `.athena/state/autopilot.json` after each step

4. **Phase 3 — QA**: Cycle until all checks pass
   - Build, lint, typecheck, test
   - Fix failures and repeat (max 5 cycles)
   - If same error persists 3 times → stop and report fundamental issue

5. **Phase 4 — Validation**: Multi-perspective review in parallel
   - code-reviewer: quality and logic check
   - security-reviewer: vulnerability scan (for auth/security code)
   - verifier: completion verification with evidence
   - All must approve; fix and re-validate on rejection

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
