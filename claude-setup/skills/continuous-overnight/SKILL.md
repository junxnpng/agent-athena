---
name: continuous-overnight
description: Autonomous overnight execution — run a long task while user sleeps, log every decision, block loud on rate-limit or repeated hypothesis failure. Never asks the user.
argument-hint: "<task or research question> [--max-hours=8] [--max-iter=20]"
---

[CONTINUOUS-OVERNIGHT ACTIVATED — id={{ID}}]

<Purpose>
Run a substantial task autonomously across hours, typically while the user is asleep.
The agent makes its own decisions inside a tight policy envelope, logs every choice
verifiably, and **fails loud (BLOCKED.md) rather than guessing or retrying forever.**
Designed for: research sweeps, data analysis pipelines, multi-file refactors,
long-running reproductions.
</Purpose>

<Use_When>
- User says "overnight", "while I sleep", "run this through the night"
- Task is large enough that interactive ralph would require many user touches
- Reproduction or sweep with clear evaluation criteria
</Use_When>

<Do_Not_Use_When>
- Task fits in one or two iterations → use autopilot or ralph
- User must approve intermediate decisions → use ralph (interactive loop)
- No clear success criterion (would loop forever) → ask user to refine first
- Task touches production / paid APIs without spending caps configured
</Do_Not_Use_When>

<Policy_Envelope>
This skill operates under strict autonomy policies — see CLAUDE.md `<autonomy_for_overnight>`.
Summary of the binding rules:

1. **Never ask the user.** Pick reasonable default + log to `decisions.md`.
2. **Decision log format:**
   `[YYYY-MM-DD HH:MM] DECISION: chose X over Y/Z. Reason: ... Confidence: low/med/high. Verifiable next morning by: ...`
3. **Block, do not retry, on rate-limit hit.** Write `BLOCKED.md`, set `state.status=blocked`, exit.
   Reason: stale prompts auto-resumed hours later may run on outdated context.
4. **Block on hypothesis failure ≥3x.** Do NOT auto-switch hypotheses without sign-off.
   Write `BLOCKED.md` with the failed hypothesis + last 3 evidence snippets, exit.
5. **Hard caps:** Max wall time (default 8h) and max iterations (default 20). Whichever hits first → graceful done.
</Policy_Envelope>

<State_Layout>
All runtime state lives under `.athena/continuous/<id>/`:

```
.athena/continuous/<id>/
├── state.json         single source of truth — see schema below
├── decisions.md       append-only autonomous decision log
├── results/           artifacts, intermediate outputs, evidence files
└── BLOCKED.md         present iff status == blocked (reason + replay hint)
```

`state.json` schema:
```json
{
  "id": "<id, e.g. 2026-04-25-overnight-lr-sweep>",
  "attention": true,
  "status": "running | blocked | done | cancelled",
  "task": "<original user task verbatim>",
  "started_at": "<ISO>",
  "last_action_at": "<ISO>",
  "max_hours": 8,
  "max_iterations": 20,
  "iteration": <int>,
  "hypothesis": {
    "current": "<active hypothesis being tested>",
    "attempts": <int>,
    "history": [{"text": "...", "result": "fail|success", "evidence_path": "results/..."}]
  },
  "decisions_count": <int>
}
```
</State_Layout>

<Steps>

1. **Setup** (first activation only)
   a. Generate `id` = `<YYYY-MM-DD>-overnight-<slug>` from task description.
   b. Create `.athena/continuous/<id>/` and write initial `state.json` (`status: "running"`, `iteration: 0`).
   c. Touch `decisions.md` with header `# Decisions Log — <id>`.
   d. Parse optional flags from prompt: `--max-hours=N`, `--max-iter=N`. Apply to state.

2. **Decompose task into hypotheses** (iteration 0)
   - Delegate to **planner** (opus) with prompt:
     "Decompose this task into a prioritized list of testable hypotheses. Each hypothesis must have an explicit verification criterion. Return as JSON array."
   - Save planner output to `state.hypothesis.history` (status pending).
   - Set `state.hypothesis.current` to first item.
   - Log decision: chose hypothesis ordering, reason from planner output.

3. **Iteration loop** (until done / blocked / cap hit)

   a. **Wall time / iteration check** — if either cap hit, jump to step 5 (graceful done).

   b. **Pick next action** for `state.hypothesis.current`:
      - If verification criterion already met → mark hypothesis success, advance to next pending hypothesis.
      - Else delegate work:
         - Code change → executor
         - Investigation / non-deterministic → tracer → debugger
         - Data analysis → scientist
         - Doc lookup → document-specialist

   c. **Run, capture evidence** to `results/iter-<N>-<short>.{md,log,json}`. Reference path in decisions.md.

   d. **Verify** with verifier or domain-specific check. Update `state.hypothesis.history[i].result`.

   e. **Decision logging:** every non-trivial choice (which agent, which sub-approach, which alternative was rejected) must append a line to `decisions.md` in the format from `<Policy_Envelope>` rule 2.

   f. **Failure handling:**
      - Rate-limit error from any agent → write BLOCKED.md, set `status=blocked`, **leave `attention=true`**, exit. (Rule 3.) (`attention=true` on blocked is intentional: session-start.mjs surfaces active sessions and routes blocked ones to the BLOCKED notice for morning review. Setting `attention=false` here would silently hide the failure.)
      - Same hypothesis attempted 3x without success → write BLOCKED.md with hypothesis text + last 3 evidence paths, set `status=blocked`, leave `attention=true`, exit. (Rule 4.)
      - Disk full / missing required file → write BLOCKED.md, set `status=blocked`, leave `attention=true`, exit.

   g. Increment `iteration`, update `last_action_at`. Loop.

4. **Hypothesis exhaustion** (all hypotheses tried)
   - If any succeeded with criterion met → step 5 (done).
   - If all failed → write BLOCKED.md noting "all hypotheses exhausted, none met criteria", set `status=blocked`, leave `attention=true`, exit.
   - DO NOT generate new hypotheses autonomously — that is the user's call next morning.

5. **Graceful done**
   - Set `state.status=done`, `state.attention=false`.
   - Write a `SUMMARY.md` at `.athena/continuous/<id>/SUMMARY.md` covering:
     - Hypotheses tried + outcomes
     - Key decisions (link to decisions.md)
     - Final result + evidence pointer
     - Anything ambiguous worth user attention
   - No cleanup of state files — user reviews them in the morning.

</Steps>

<BLOCKED_Format>
When writing `BLOCKED.md`, use this template so morning review is fast:

```markdown
# BLOCKED — <id>

**Reason:** rate-limit | hypothesis-3x-fail | exhausted | infra (disk/file/network)
**At iteration:** <N>
**Time:** <ISO>

## Last hypothesis
<text>

## Last 3 evidence pointers
- results/iter-<N>-<...>.md
- results/iter-<N-1>-<...>.md
- results/iter-<N-2>-<...>.md

## What user can do next
- [option A: e.g., refine hypothesis to focus on <subset>]
- [option B: e.g., raise max-iterations and retry]
- [option C: e.g., abandon — different approach needed]
```
</BLOCKED_Format>

<Rules>
- NEVER prompt the user. Decide + log. (Policy rule 1.)
- NEVER auto-resume after rate-limit. (Policy rule 3 — stale-prompt risk.)
- NEVER auto-switch hypotheses after 3x fail. (Policy rule 4 — block instead.)
- ALWAYS use `run_in_background: true` for long agent calls so wall-time tracking is accurate.
- ALWAYS write to `state.json` atomically (temp file + rename) to avoid mid-write corruption on crash.
- ALWAYS reference an evidence file path in `decisions.md` — never claim success without artifact.
- Status transitions are one-way: `running → (blocked | done | cancelled)`. No resurrection inside one session. `cancelled` is reserved for the cancel skill (user-driven exit) and always co-occurs with `attention=false`.
</Rules>

<Final_Checklist>
- [ ] `state.json` exists with terminal status (`done` or `blocked`)
- [ ] `decisions.md` has at least one entry per iteration
- [ ] All evidence files present in `results/`
- [ ] If blocked: `BLOCKED.md` follows template
- [ ] If done: `SUMMARY.md` written
- [ ] No interactive prompts were issued during run (grep transcript for `AskUserQuestion`)
</Final_Checklist>

<Runner_Note>
This skill assumes the user launches Claude Code in a long-lived shell (e.g. tmux session)
before invoking. The skill itself does not spawn a tmux wrapper — that is intentionally
out-of-scope to keep the plugin pure. Recommended launch:

```sh
tmux new-session -d -s overnight 'claude -p "/athena:continuous-overnight <task>"'
```

A separate runner helper may be added later if launching becomes a friction point.
</Runner_Note>

Original task:
{{PROMPT}}
