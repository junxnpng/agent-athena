---
name: ralph
description: Persistent loop — keep working until task is verified complete
argument-hint: "<task description>"
---

[RALPH — ITERATION {{ITERATION}}/{{MAX}}]

<Purpose>
Ralph is a persistence loop. It keeps working on a task until completion is verified.
No silent partial completions. No "should work". Evidence or keep going.
</Purpose>

<Use_When>
- User says "ralph", "don't stop", "keep going", "finish this", "must complete"
- Task needs guaranteed completion with verification
- Work may require multiple iterations and retry on failure
</Use_When>

<Do_Not_Use_When>
- Full idea-to-code pipeline → use autopilot
- Just exploring or planning → delegate to planner agent directly
- Quick one-shot fix → delegate to executor directly
</Do_Not_Use_When>

<Steps>
1. **Setup** (first iteration only):
   a. Break the task into discrete acceptance criteria
   b. Write criteria to `.athena/state/ralph.json`:
      ```json
      {
        "active": true,
        "task": "<original task>",
        "iteration": 1,
        "max_iterations": 10,
        "criteria": [
          {"id": 1, "description": "...", "passes": false},
          {"id": 2, "description": "...", "passes": false}
        ],
        "started_at": "<ISO timestamp>"
      }
      ```
   c. Criteria must be specific and testable — NOT "implementation is complete"

2. **Pick next criterion**: Select the highest-priority unmet criterion.

3. **Implement**: Delegate to appropriate agents.
   - Code work → executor (default opus 4.7)
   - Investigation / non-deterministic bug → tracer (hypotheses) → debugger (fix)
   - Run independent tasks in parallel; use `run_in_background: true` for long builds
   - Cleanup smell detected after iteration (duplicates, dead code, needless wrappers, weak coverage) → invoke `/athena:ai-slop-cleaner` on the iteration's changed files (standard mode, NOT `--review`). Return to step 4 verify after cleanup completes.

4. **Verify**: For each acceptance criterion:
   - Run the specific check (test, build, manual verification)
   - Show fresh output as evidence
   - If met → mark `passes: true` in ralph.json
   - If not → continue working, do NOT mark complete

5. **Check completion**:
   - All criteria `passes: true`? → proceed to Step 6
   - Not all complete? → increment iteration, loop to Step 2
   - Iteration limit reached? → report remaining issues

6. **Final verification**: Use verifier agent to confirm all criteria with evidence.
   - On approval → invoke cancel skill for cleanup
   - On rejection → fix issues, re-verify

7. **On rejection**: Fix issues raised, loop back to Step 4.
</Steps>

<Rules>
- NEVER claim completion without fresh verification output
- NEVER reduce scope to meet a deadline — report what's incomplete instead
- If same issue fails 3+ iterations, report as fundamental blocker
- Fire independent tasks in parallel — don't wait sequentially
- Use `run_in_background: true` for builds and test suites
- Update `.athena/state/ralph.json` after every iteration
</Rules>

<Final_Checklist>
- [ ] All acceptance criteria have `passes: true`
- [ ] Criteria are task-specific (not generic boilerplate)
- [ ] Fresh test output shows all tests pass
- [ ] Fresh build output shows success
- [ ] Verifier confirmed with evidence
- [ ] State cleaned up via cancel skill
</Final_Checklist>

Original task:
{{PROMPT}}
