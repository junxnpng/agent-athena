---
name: summary
description: Snapshot of where you left off in this repo — branch, recent commits, active modes, plan progress, in-flight files. NO diff content (too heavy).
argument-hint: "[--full]  (--full also dumps active plan markdown)"
---

[SUMMARY ACTIVATED]

<Purpose>
Quickly answer "what was I doing in this repo?" by aggregating git state, athena mode state, and plan documents.
Designed to be cheap to run — no expensive diff content, no LLM-heavy analysis.
</Purpose>

<Use_When>
- User says "where was I", "summary", "what was I doing", "catch me up", "내가 뭐 하고 있었지"
- Returning to a repo after time away
- Starting a new session in an existing project
</Use_When>

<Do_Not_Use_When>
- User asks for code review → use multi-review or code-reviewer
- User asks for plan → use planner agent
- User wants diff content → use `git diff` directly
</Do_Not_Use_When>

<Steps>

1. **Git state** (cheap)
   ```
   git branch --show-current
   git log --oneline -5
   git diff --name-only        # uncommitted file LIST only (no content)
   git diff --cached --name-only
   git status --short          # also catches untracked
   ```
   Capture: current branch, last 5 commit subjects, uncommitted file count + names (max 20), untracked count.

2. **Athena mode state** (read JSON files in `.athena/state/`)
   ```
   ls .athena/state/*.json 2>/dev/null
   ```
   For each found file, read and report:
   - mode name (from filename)
   - active flag, current phase/iteration, started_at
   - task description (from inside the JSON)

3. **Continuous-overnight state** (if `.athena/continuous/*/` dirs exist)
   ```
   ls .athena/continuous/
   ```
   For each session dir, check:
   - state.json — status (running/blocked/done)
   - decisions.md — line count (autonomous decisions made)
   - results/ — file count

4. **Plans** (read recent plan markdown)
   ```
   ls -t .athena/plans/*.md | head -3
   ```
   For most recent plan: title + current phase marker (look for `[x]` checkboxes).
   If `--full` flag passed, dump full content of most recent plan.

5. **Last context** (read `.athena/last-context.json`)
   - summary, timestamp, modified files (if hook saved it from prior session)

6. **TODO/FIXME scan** (cheap, line numbers only)
   ```
   git diff --name-only | xargs grep -nE "TODO:|FIXME:" 2>/dev/null | head -20
   ```
   List file:line only, not content.

7. **Synthesize output** in format below.

</Steps>

<Output_Format>
## Where you left off

**Branch:** <name>  (<N> commits ahead of <base> if known)

**Recent commits:**
- <hash> <subject>
- ...

**Uncommitted:** <N> modified, <M> untracked  (showing first 10)
- file1
- file2
- ...

## Active modes
[from .athena/state/*.json]
- **<mode-name>**: phase <X/Y>, started <relative time>, task: "<description>"

[if continuous-overnight active:]
- **continuous-overnight** (<id>): status=<running|blocked|done>, decisions=<N>, results=<M>

## Last plan
[from .athena/plans/]
- **<title>**: phase <current>/<total>
- File: `.athena/plans/<file>.md`

## Last context
[from .athena/last-context.json]
- "<summary>" (<relative time> ago)

## In-flight TODO/FIXME
- file:line
- ...

## Suggested next
[1-2 concrete next actions based on state]
- e.g., "Resume ralph (iteration 5/10)" → `/athena:ralph continue`
- e.g., "Active continuous-overnight is BLOCKED — check `.athena/continuous/<id>/BLOCKED.md`"
- e.g., "No active mode. Branch has 3 uncommitted files — commit or `/athena:multi-review` first?"
</Output_Format>

<Constraints>
- Never read large files. List file names, not content.
- Skip diff content entirely (too heavy, user can `git diff` if needed).
- Total output should fit in ~50 lines.
- If `.athena/` doesn't exist, just give git state + note "no active athena modes".
- If git not initialized, just give plan/mode state + note "not a git repo".
</Constraints>

Argument:
{{PROMPT}}
