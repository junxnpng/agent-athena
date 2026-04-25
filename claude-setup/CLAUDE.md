# My Claude Code Environment

<operating_principles>
- Read before write: never modify a file you haven't read in this session.
- Prove, don't claim: show execution output before declaring completion.
- Minimal diff: change only what was requested. No drive-by refactors.
- Explore first: for broad or multi-file requests, read code before proposing changes.
- Detect repetition: when multi-step work (e.g., explore+analyze+modify) repeats 3+ times with the same structure in one session, propose extraction:
  - ≤3 steps + single agent → slash command (~/.claude/commands/*.md)
  - ≥4 steps OR multiple agents combined → workflow (~/.claude/skills/{name}/SKILL.md)
  Single commands/simple questions are excluded.
</operating_principles>

<delegation_rules>
Delegate: multi-file changes → executor (via planner if complex). Security code → security-reviewer.
Post-implementation review → code-reviewer. Architecture questions → architect.
Bug investigation → debugger. Research → researcher. Ideas → ideator. Critique → critic.
Work directly: single-file edits, simple questions, git/shell commands.
</delegation_rules>

<model_routing>
haiku: explore (fast codebase search).
sonnet: executor, debugger, verifier, security-reviewer.
opus: architect, planner, code-reviewer, researcher, ideator, critic.
</model_routing>

<agent_catalog>
Prefix: `athena:`. See `agents/*.md` for full prompts.

Fast: explore (haiku)
Implementation: executor (sonnet), debugger (sonnet)
Analysis (READ-ONLY): architect (opus), planner (opus), code-reviewer (opus), security-reviewer (sonnet), verifier (sonnet)
Research & Ideas (READ-ONLY): researcher (opus), ideator (opus), critic (opus)
</agent_catalog>

<skills>
Invoke via `/athena:<name>`.

Workflow: `autopilot` (idea→code), `ralph` (persistent loop), `plan` (strategic planning), `cancel` (stop active mode)
Research: `research` (structured survey+analysis), `ideate` (brainstorm+critique)

Keyword triggers: "autopilot"/"build me"→autopilot, "ralph"/"don't stop"/"keep going"→ralph, "plan this"→plan, "cancel"/"stop"→cancel, "research"/"survey"→research, "ideate"/"brainstorm"→ideate
</skills>

<execution_protocols>
Broad requests (vague verbs, no target, 3+ areas): explore → plan → implement.
Run 2+ independent tasks in parallel. Use run_in_background for builds/tests.
Never self-approve: authoring and review must be separate passes.
Completion requires: build pass + tests pass + no type errors + no debug artifacts.
</execution_protocols>

<verification>
Claim evidence: "Fixed" → failing test now passes. "Implemented" → build+types clean.
"Refactored" → existing tests still pass. "Debugged" → root cause at file:line.
Banned: "should work", "probably", "seems to". Run the command instead.
Thorough review required for: auth/*, security/*, *secret*, *.env*, schema/config changes.
</verification>

<git_workflow>
Git rules: follow ~/.claude/rules/harness-common/common.md (covers commit convention, no auto git add/commit/push, branch naming).
</git_workflow>

<plans>
Plan documents: create both English and Korean versions, and keep them in sync on every update.
- English: canonical reference Claude uses for execution.
- Korean: user review version. Content must mirror English.
</plans>

<security>
Follow ~/.claude/rules/harness-common/security.md. For auth/security changes → security-reviewer agent.
</security>

<language_rules>
Language-specific rules live in ~/.claude/rules/harness-{typescript|python|golang}/.
</language_rules>

