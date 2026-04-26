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

   a. **Plan-path detection**: if the task input is a path string (input has no whitespace, matches `^[^ ]+\.md$` after trimming surrounding whitespace, the file exists, AND the file contains a section heading matching `## Acceptance Criteria` or `### Acceptance Criteria`), READ the plan file and lift acceptance criteria directly from that section. Each `- [ ] <description>` line becomes one criterion. Skip step 1.b's decomposition. This is the path used when ralplan auto-handoffs under continuous-overnight autonomy — the consensus plan is the contract, not a re-decomposition target. If the regex matches but the file lacks the heading, FAIL LOUDLY: log "plan-path detected but no Acceptance Criteria section found" to ralph.json `notes` field and fall through to step 1.b (do NOT silently treat the literal path as the task description).

   b. **Otherwise — decompose**: break the task into discrete acceptance criteria.

   c. Write criteria to `.athena/state/ralph.json`. Single-file mode: liveness signal is **file presence** (no `attention` field) — uniform with autopilot, opposite of dir-based modes (which use `state.attention`). Cancel deletes the file:
      ```json
      {
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
   d. Criteria must be specific and testable — NOT "implementation is complete"

2. **Pick next criterion**: Select the highest-priority unmet criterion.

3. **Implement**: Delegate to appropriate agents.
   - Code work → executor (default opus 4.7)
   - Investigation / non-deterministic bug → tracer (hypotheses) → debugger (fix)
   - Run independent tasks in parallel; use `run_in_background: true` for long builds

4. **Verify**: For each acceptance criterion:
   - Run the specific check (test, build, manual verification)
   - Show fresh output as evidence
   - If met → mark `passes: true` in ralph.json
   - If not → continue working, do NOT mark complete

4.5. **Cleanup pass (post-Verify)**: If cleanup smell observed in iteration's changed files (duplicates, dead code, needless wrappers, weak coverage) → invoke `/athena:ai-slop-cleaner` on those files (standard mode, NOT `--review`). After cleanup, return to step 4 to re-verify regressions. Skip this step if no smell observed.

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
