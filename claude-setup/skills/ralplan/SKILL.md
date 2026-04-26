---
name: ralplan
description: Pre-execution consensus gate — runs planner → architect → critic in a closed loop until consensus, then hands off to ralph/autopilot. Catches vague prompts before they waste autonomous cycles.
argument-hint: "[--interactive] [--deliberate] <task description>"
---

[RALPLAN ACTIVATED]

<Purpose>
Many failures of ralph / autopilot / continuous-overnight are not bugs — they're
underspecified prompts. Ralplan exists to intercept vague execution requests
("ralph improve the app") and redirect them through a Planner → Architect → Critic
consensus loop BEFORE autonomous execution begins. Output is a tested,
testable plan with an ADR and explicit acceptance criteria.
</Purpose>

<Use_When>
- About to invoke ralph / autopilot / continuous-overnight on a non-trivial task
- The task has 2+ viable approaches and the choice matters
- User says "ralplan", "plan first", "consensus", or invokes execution on a vague prompt
- High-risk work (auth, migrations, destructive changes, public API) — even with concrete anchors, deliberate consensus is worth the cycles
</Use_When>

<Do_Not_Use_When>
- Prompt has concrete anchors (file path, function name, issue #, code snippet, numbered steps) AND scope is small — execute directly
- User explicitly bypasses (`force:` or `!` prefix on the execution call)
- Single-file edit / one-shot answer
</Do_Not_Use_When>

<Pre_Execution_Gate>
The gate auto-passes when the prompt has ANY concrete signal:

| Signal | Example | Why passes |
|--------|---------|-----------|
| File path | `ralph fix src/auth.ts` | Specific file |
| Issue/PR number | `autopilot implement #42` | Concrete work item |
| Symbol name | `ralph fix processKeywordDetector` | Specific function |
| Numbered steps | `ralph do: 1. Add X 2. Test Y` | Structured deliverables |
| Acceptance criteria | `add login — accepts: ...` | Explicit success def |
| Error reference | `fix TypeError in auth flow` | Specific symptom |
| Code block | `apply: ```ts ... ```` | Concrete code |

The gate FIRES (redirects to ralplan) when:
- Execution keyword (ralph/autopilot/continuous-overnight) present, AND
- Prompt is ≤15 effective words, AND
- No concrete anchor matched

**"Effective words" definition:** whitespace-separated tokens after stripping (a) fenced code blocks (```...```), (b) inline backticked code (`...`), and (c) markdown link URLs (the `(http...)` portion of `[text](url)` links — the visible link text still counts). Counts the tokens a human reader would describe as "words in the request" — not URL noise or code.

Bypass: prefix the execution call with `force:` or `!`.
</Pre_Execution_Gate>

<Steps>

1. **Planner — initial plan + RALPLAN-DR summary**
   Delegate to **planner** (opus) with prompt:
   ```
   Produce a plan for: <task>
   Output BEFORE the plan body, a RALPLAN-DR summary:
     - Principles (3-5)
     - Decision Drivers (top 3, ranked)
     - Viable Options (≥2) with bounded pros/cons each
     - If only one option remains, explicit invalidation rationale for alternatives
   {if --deliberate: also include pre-mortem (3 failure scenarios) + expanded test plan (unit/integration/e2e/observability)}

   Then the plan body. The plan body MUST include a section with the LITERAL heading
   `## Acceptance Criteria` (case-sensitive, exactly two `#`, no trailing punctuation).
   Under that heading, list each criterion as a checkbox bullet:
     - [ ] <runnable test command, specific scenario, or verifiable acceptance condition>
   Each bullet must be testable on its own (a command or scenario, not "code is good").

   This format is contractual: ralph's plan-path detection (ralph/SKILL.md Step 1.a) and
   autopilot's plan-path short-circuit (autopilot/SKILL.md pre-Phase-0 block) both look
   for this exact heading + bullet pattern. Any other heading text or bullet style will
   silently fall through to re-decomposition, defeating the consensus contract.

   Save to .athena/plans/ralplan-<slug>.md
   ```

2. **Optional user check** (`--interactive` only)
   Use `AskUserQuestion` to present the RALPLAN-DR summary + plan draft:
   - Proceed to architect review
   - Request changes (revise + redo Planner pass)
   - Skip review (terminal: output current plan)

   **Autonomy bypass:** if any `.athena/continuous/<id>/state.json` exists with `state.attention === true`, treat as `--interactive=false` regardless of flag — SKIP this user check and proceed to architect review (step 3). Log decision to `.athena/continuous/<id>/decisions.md`.

3. **Architect review** — sequential, AWAIT before step 4
   Delegate to **architect** (opus). Architect must produce:
   - Strongest steelman antithesis (the best argument against the plan)
   - At least one real tradeoff tension (not "consider X" — name it: "Y vs Z, plan picks Y, but Z would buy us A at cost B")
   - Synthesis if possible (where antithesis informs an updated plan element)
   {if --deliberate: also flag any principle violation explicitly}

4. **Critic evaluation** — only AFTER architect completes
   Delegate to **critic** (opus). Critic enforces:
   - Principle ↔ Option consistency
   - Fair alternatives (no straw-man rejection)
   - Risk mitigation clarity
   - Testable acceptance criteria (must be runnable, not "looks good")
   - Concrete verification steps
   {if --deliberate: must REJECT plans with missing/weak pre-mortem or expanded test plan}

   Critic verdict: APPROVE | ITERATE | REJECT.

5. **Re-review loop** (max 5 iterations)
   If verdict ≠ APPROVE:
   a. Collect Architect + Critic feedback
   b. Hand back to Planner with explicit feedback to revise
   c. Return to step 3 (Architect)
   d. Then step 4 (Critic)
   e. Repeat until APPROVE or 5 iterations
   f. If 5 iterations without APPROVE: surface best version + remaining objections, ask user to override or abandon

6. **Final plan + ADR**
   Plan must include an ADR section:
   - **Decision** (one sentence)
   - **Drivers** (referenced from RALPLAN-DR)
   - **Alternatives considered** (with invalidation rationale)
   - **Why chosen** (explicit tradeoffs accepted)
   - **Consequences** (what changes downstream — test, ops, docs)
   - **Follow-ups** (deferred items with owners)

7. **Execution bridge** (`--interactive` only) — `AskUserQuestion`:
   - Approve and execute via ralph (sequential, persistent)
   - Approve and execute via autopilot (full lifecycle, parallel where possible)
   - Approve and execute via continuous-overnight (autonomous, overnight)
   - Request changes (back to step 5)
   - Reject (abandon, save plan to .athena/plans/ for later)

   On approval: invoke the chosen Skill explicitly. NEVER implement directly — ralplan is a planning lane.

   **Autonomy auto-handoff:** if any `.athena/continuous/<id>/state.json` exists with `state.attention === true`, SKIP the AskUserQuestion. After consensus (step 6 ADR present + critic APPROVE), immediately route to a downstream execution skill with the saved plan path.

   **Caller detection (explicit-sentinel only — no heuristic substring match):** ralplan does NOT inspect the prompt for natural-language signatures (those are too easy to false-positive on, e.g. a user prompt that mentions "autopilot Phase 0 expansion" by name). Routing is determined ONLY by an explicit sentinel at the START of the prompt:

   - If the prompt starts with the literal token `[from=autopilot]` (whitespace allowed before/after) → invoke `/athena:autopilot` with the plan path. Autopilot's plan-path short-circuit (see autopilot/SKILL.md `<Steps>` opening note) skips its Phase 0/1, so no double-planning. Autopilot is responsible for prepending this sentinel when delegating to ralplan.
   - Otherwise (no sentinel, or different sentinel) → invoke `/athena:ralph` with the plan path. Ralph's plan-path detection (Step 1.a) reads acceptance criteria directly from the plan, so the consensus output is preserved.

   - Pass plan path explicitly: e.g. `Skill(skill="athena:ralph", args="<plan path>")`
   - Do NOT pass `--interactive` to the downstream skill.
   - Log handoff decision (chosen target + reason) to `.athena/continuous/<id>/decisions.md`.

   **Default safety:** ralph is the documented default — it is sequential and evidence-locked, and it cannot re-invoke ralplan (no ping-pong risk). Autopilot routing is opt-in via the `[from=autopilot]` sentinel only.

   This closes the autonomy dead-end: a continuous-overnight session that hits the ralplan gate must terminate at an executing skill, never at "plan saved, awaiting approval".

</Steps>

<Rules>
- Steps 3 (Architect) and 4 (Critic) MUST run sequentially. Do NOT parallel-batch them — Critic needs Architect's output as context.
- Author and reviewer must be different agents. Planner authors; Architect+Critic review. Same opus context can NOT both write and self-approve.
- Plan must reference real file paths or function names where applicable. Pure prose plans are too easy to fool yourself with.
- Acceptance criteria must be runnable. "Tests pass" is not enough — name the test suite or the specific scenario.
- Do NOT skip the ADR. Future-you needs to know why this approach won.
- If Critic returns REJECT 3 consecutive iterations on the same issue, treat as fundamental — surface to user, don't keep mutating the plan around it.
</Rules>

<Final_Checklist>
- [ ] Planner produced RALPLAN-DR summary (Principles, Drivers, Options) before plan body
- [ ] Architect review ran AFTER planner output, with explicit antithesis + tradeoff tension
- [ ] Critic evaluation ran AFTER architect, with verdict (APPROVE/ITERATE/REJECT)
- [ ] If iterated: each loop ran the full Planner→Architect→Critic cycle (no shortcuts)
- [ ] Final plan saved to `.athena/plans/ralplan-<slug>.md`
- [ ] ADR present (Decision, Drivers, Alternatives, Why chosen, Consequences, Follow-ups)
- [ ] Acceptance criteria are testable (runnable command or explicit scenario)
- [ ] On --interactive: execution handed off via Skill() to ralph/autopilot/continuous-overnight, NOT implemented inline
</Final_Checklist>

Task:
{{PROMPT}}
