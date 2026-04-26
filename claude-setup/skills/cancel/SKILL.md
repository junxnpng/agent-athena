---
name: cancel
description: Cancel active athena loop-mode (autopilot, ralph, continuous-overnight, deep-interview, deep-dive, self-improve) and clean up state. Preserves evidence — never deletes artifact directories.
argument-hint: "[--force]"
---

# Cancel Skill

Stop active athena loop-mode session(s) and mark their state as cancelled.

## Usage

```
/athena:cancel           # Smart cancel — detect and cancel active loop modes
/athena:cancel --force   # Clear single-file state (autopilot/ralph). Dir-based modes still preserve artifacts.
```

Or say: "cancel", "stop", "abort"

## Loop modes (cancellable)

| Mode | State location | Notes |
|------|----------------|-------|
| autopilot | `.athena/state/autopilot.json` | Single file |
| ralph | `.athena/state/ralph.json` | Single file |
| continuous-overnight | `.athena/continuous/<id>/state.json` | Dir-based (preserve decisions.md + results/) |
| deep-interview | `.athena/deep-interview/<slug>/state.json` | Dir-based (preserve transcript) |
| deep-dive | `.athena/deep-dive/<slug>/state.json` | Dir-based (preserve trace + interview) |
| self-improve | `.athena/self-improve/<slug>/state/loop.json` | Dir-based (preserve all rounds) |

## One-shot modes (NOT cancellable — artifacts are evidence)

`sciresearch`, `multi-review`, `trace`, `external-context` produce timestamped
artifact directories (`.athena/<mode>/<timestamp>/`). These are not loops —
once started, they fan out and write outputs. If the artifact dir exists
it's evidence, not state. cancel does NOT touch them.

`ralplan` runs a bounded re-review loop (≤5 iterations) within a single
invocation — there is no persistent state.json to flip. To abort an in-progress
ralplan run, end the session (Ctrl-C / kill the tmux pane). Saved plan
artifacts under `.athena/plans/` remain as evidence.

## Process-kill caveat

cancel marks state files but does NOT kill background processes (e.g.,
benchmark commands spawned by self-improve, long builds spawned by ralph).
After cancel, `kill` orphaned PIDs manually if needed, or rely on tmux/shell
session shutdown to reap them.

## What It Does

### 1. Detect active loop modes

For each loop mode listed above, check whether the state file indicates an
active session. Single-file modes signal liveness via file existence; dir-based
modes use `state.attention === true` regardless of `status` (so a blocked
continuous-overnight that left `attention=true` for morning surfacing is still
cancellable):

```
Read .athena/state/autopilot.json — active if file EXISTS (single-file, no `attention` field; presence = live)
Read .athena/state/ralph.json     — active if file EXISTS (single-file, no `attention` field; presence = live)
List .athena/continuous/*/state.json   — active if state.attention === true (any status; blocked sessions ARE cancellable)
List .athena/deep-interview/*/state.json — active if state.attention === true
List .athena/deep-dive/*/state.json      — active if state.attention === true
List .athena/self-improve/*/state/loop.json — active if loop.attention === true (any status; blocked is cancellable)
```

### 2. Cancel each active mode

**Single-file modes (autopilot, ralph):**
- **READ the state file FIRST** — extract phase / iteration / criteria-count for the message. Required ordering: read → format message → delete file. Reading after delete yields `undefined/undefined` in messages.
- Then remove the state file (`rm .athena/state/<mode>.json`).
- Report cancellation with the values captured above.

**Dir-based modes (continuous-overnight, deep-interview, deep-dive, self-improve):**
- Set BOTH `status: cancelled` AND `attention: false` in the state JSON via atomic write (temp file + rename). Uniform across all dir-based loop modes — `cancelled` is distinct from `blocked` (which means "rate-limit / 3x failure / infra block, exit gracefully") and from `done` (graceful completion).
- The `attention: false` write is REQUIRED — the session-start surfacing filter only re-surfaces sessions where `state.attention === true`. Without `attention=false`, a cancelled session re-surfaces forever.
- Write a `CANCELLED.md` in the mode's directory with:
  - reason: "user-cancelled"
  - timestamp
  - last completed step / iteration / round
- DO NOT delete the directory — decisions, transcripts, intermediate results stay for morning review

### 3. Force mode (`--force`)

- Single-file modes: delete the state file
- Dir-based modes: STILL preserve directories. Force only clears the single-file `.athena/state/` entries.
- Removing dir-based artifacts is a manual user action — `rm -rf .athena/<mode>/<id>/`. Never automated; the artifacts may have hours of work in them.

## Messages

| Mode | Message |
|------|---------|
| autopilot | "Autopilot cancelled at phase: {phase}." |
| ralph | "Ralph cancelled. {N}/{total} criteria completed." |
| continuous-overnight | "Continuous-overnight {id} cancelled at iteration {N}. Artifacts at .athena/continuous/{id}/ preserved." |
| deep-interview | "Deep-interview {slug} cancelled at round {N} (ambiguity {score}%). Transcript at .athena/deep-interview/{slug}/ preserved." |
| deep-dive | "Deep-dive {slug} cancelled at phase {phase}. Trace + interview artifacts preserved." |
| self-improve | "Self-improve {slug} cancelled at iteration {N}. All rounds preserved at .athena/self-improve/{slug}/." |
| Force | "Single-file state cleared (autopilot/ralph). Dir-based artifacts preserved." |
| None | "No active loop modes detected." |

## Why preserve dir-based artifacts even on --force?

Dir-based modes accumulate evidence across iterations / rounds / Q&A cycles —
hours of agent work, decision logs, benchmark scores, transcripts. Auto-deleting
on cancel/force is a footgun. Preserving means the user can:
- Review what got done before deciding to redo
- Resume manually by editing state.json (set status back to running) if appropriate
- Promote insights to user-level skills via skillify / learner

If the user truly wants a fresh start, they delete the directory themselves —
explicit, not implicit.
