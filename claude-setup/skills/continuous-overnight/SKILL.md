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

**Important — two-layer trust boundary:** rules 1–5 are SKILL-LEVEL contracts the LLM follows. They do NOT bypass Claude Code's HARNESS-LEVEL tool-permission system. If `Bash`/`Write`/`Edit`/`Task`/etc. require a permission prompt, the harness will block waiting for user approval — silently, while the user is asleep. The autonomy envelope **assumes** tool permissions are pre-granted. See `<Pre_Flight>` below for the required setup.
</Policy_Envelope>

<Pre_Flight>
Required setup BEFORE invoking this skill — without these, the loop will silently
hang on tool-permission prompts during the night.

### 1. Tool-permission mode (pick ONE)

**Option A (recommended for true overnight) — bypass-permissions mode:**
Press `Shift+Tab` in the active Claude Code session until the mode indicator at the
bottom shows `bypass-permissions`. Three modes cycle:
- `plan` (no execution)
- `accept-edits` (Write/Edit auto-approved, Bash still prompts)
- `bypass-permissions` (everything auto-approved) ← required for overnight

This persists for the duration of the Claude Code session. Re-enabling per session.

**Option B — CLI flag at launch:**
```sh
claude --dangerously-skip-permissions
```
Same effect as bypass-permissions mode, set at process start. Required if
launching headlessly (e.g. via tmux + `claude -p`).

**Option C — narrow allow-list in `~/.claude/settings.json`:**
For users uncomfortable with full bypass, allow only the tools the loop needs:
```json
{
  "permissions": {
    "allow": [
      "Bash(*)",
      "Write",
      "Edit",
      "Read",
      "Glob",
      "Grep",
      "Agent",
      "Skill",
      "ToolSearch",
      "TaskCreate",
      "TaskUpdate",
      "TaskList"
    ]
  }
}
```
`Bash(*)` is broad — replace with specific commands (`Bash(git:*)`, `Bash(node:*)`)
if you want tighter scope.

### 2. Long-lived shell

Claude Code session must survive the night. Network blip / lid-close / terminal
quit kills the loop. Use `tmux` or `screen`:

```sh
# Launch in detached tmux session
tmux new-session -d -s overnight 'claude --dangerously-skip-permissions -p "/athena:continuous-overnight <task>"'

# Re-attach in the morning
tmux attach -t overnight
```

For the `--dangerously-skip-permissions` to take effect headlessly, it MUST be
on the launch command — `Shift+Tab` only works in interactive mode and won't
help an already-launched headless session.

### 3. Sanity verify before launch

```sh
# Confirm Node.js for hooks
node -v   # must be >= 20

# Confirm athena plugin enabled
grep -A1 'enabledPlugins' ~/.claude/settings.json   # should show athena@athena-local: true

# Confirm working dir state
git status   # advisory — overnight loops on dirty trees mix changes
```

### 4. Optional but useful

- Set `OVERNIGHT_TASK` budget caps in the prompt: `--max-hours=N --max-iter=N`.
- Note any external service quotas (OpenAI/Anthropic rate limits, GitHub Actions minutes) — the loop blocks on rate-limit but doesn't pre-check quotas.
- Plan a morning review window — the loop produces `SUMMARY.md` or `BLOCKED.md`; both need human eyes.

### What happens if Pre-flight is skipped

| Skipped step | Failure mode |
|---|---|
| Permission mode | Loop hangs at first Bash/Write call. No error, just silent wait. Wakes user up. |
| tmux/long-lived shell | SIGHUP on terminal close → process dies mid-iteration → state.json left as `running` → next session-start surfaces zombie. |
| Node.js 20+ | Hooks fail to load → consistency check + session-start surfacing skipped. |
| athena plugin enabled | `/athena:` skill invocations not recognized; the entire skill stack is unreachable. |

</Pre_Flight>

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
This skill assumes the user has completed the `<Pre_Flight>` setup above
(permission mode + long-lived shell + plugin verification). The skill itself does
not spawn a tmux wrapper or set permission flags — those are out-of-scope to keep
the plugin pure.

Quick reference for the typical "launch and walk away" path:

```sh
tmux new-session -d -s overnight \
  'claude --dangerously-skip-permissions -p "/athena:continuous-overnight <task>"'

# Morning:
tmux attach -t overnight
cat .athena/continuous/*/SUMMARY.md   # or BLOCKED.md
```

If you launched WITHOUT `--dangerously-skip-permissions` and the loop hangs
mid-night on a permission prompt: that is the documented failure mode in
`<Pre_Flight>` step 1 — the autonomy envelope is a SKILL-level contract and
does not bypass Claude Code's harness-level permission gating. Re-launch with
the flag.
</Runner_Note>

Original task:
{{PROMPT}}
