---
name: skillify
description: Capture a repeatable workflow from the current session as a reusable SKILL.md draft so it doesn't need to be rediscovered.
argument-hint: "<workflow name> [--draft]"
---

[SKILLIFY ACTIVATED]

<Purpose>
When the current session uncovered a multi-step workflow that worked well and is
likely to repeat, capture it as a concrete SKILL.md instead of letting it
vanish at session end. Output is an immediately invokable skill (default) or
a draft for later review (--draft).
</Purpose>

<Use_When>
- The session executed a repeatable workflow ≥3 times with the same shape
- User says "make this a skill", "skillify", "save this workflow"
- A non-obvious sequence of agent calls / decisions worked and should not be re-derived next time
</Use_When>

<Do_Not_Use_When>
- Workflow ran only once — wait for the pattern to repeat before extracting
- It's a generic technique someone could Google in 5 minutes — don't pollute the skill library
- Branching decisions are still unresolved — note them and ask the user before drafting
- The "workflow" is really a single agent call — just remember the agent, not a skill
</Do_Not_Use_When>

<Steps>

1. **Identify the workflow**
   - What concrete task did this session do, end to end?
   - What were the inputs (file paths, prompt shape, prior state)?
   - What sequence of decisions / agent calls / verifications happened?
   - What was the success criterion (how did we know it was done)?

2. **Extract structure**
   - Ordered steps (terse, imperative form)
   - Constraints / pitfalls hit during the session that future runs should avoid
   - Optional "Do_Not_Use_When" cases (where this workflow misfires)

3. **Decide save target** (see `<Save_Locations>` below)
   - Default: user-level `~/.claude/skills/<name>/SKILL.md`
   - `--draft` flag → project-local `.athena/skills/draft/<name>.md`

4. **Generate the SKILL.md**
   - YAML frontmatter (name, description, argument-hint if applicable)
   - Body sections in athena style: Purpose / Use_When / Do_Not_Use_When / Steps / Rules / Final_Checklist
   - Reference specific agents by name (e.g., `Task(subagent_type="athena:executor", ...)`) so the consistency checker can validate

5. **Write the file** atomically. Print absolute path so the user can inspect.

6. **Report**
   - Saved location
   - Open questions or fuzzy parts that future runs should re-decide
   - Suggested first invocation (so the user can sanity-check it)

</Steps>

<Save_Locations>
| Mode | Path | Behavior |
|------|------|----------|
| Default | `~/.claude/skills/<name>/SKILL.md` | User-level — Claude Code auto-loads on next session, immediately invokable as `<name>` (no plugin prefix) |
| `--draft` | `.athena/skills/draft/<name>.md` | Project-local draft — gitignored via `.athena/`, user reviews and manually promotes |

The athena plugin itself is a marketplace package; do NOT silently add new skills under `claude-setup/skills/` — that would change the plugin scope without sign-off. User-level + draft are the safe targets.
</Save_Locations>

<Rules>
- Capture only workflows that REPEATED. Single-run "interesting" sequences are not skills, they're notes.
- Frontmatter is mandatory and must include `name` + `description`. No plain markdown without frontmatter.
- Reference athena agents by their canonical names (executor, scientist, etc.) so consistency check passes.
- Prefer explicit success criteria over vague prose ("output passes verifier" beats "looks correct").
- If a branching decision is unresolved (e.g., "depends on whether codebase is Python or Go"), document it as an Open Question and DO NOT bake in an arbitrary default.
- Never write the new skill into `claude-setup/skills/` — that's the plugin source of truth, modified by intentional plugin work, not by skillify.
</Rules>

<Final_Checklist>
- [ ] Workflow has fired ≥3 times this session (or user explicitly authorized single-instance extraction)
- [ ] SKILL.md has valid YAML frontmatter (name + description minimum)
- [ ] Steps are ordered and concrete (no vague "handle edge cases")
- [ ] Referenced agents exist in athena catalog (consistency checker would pass)
- [ ] File saved to user-level or `.athena/skills/draft/` — NOT to plugin source
- [ ] Open questions surfaced explicitly if any
</Final_Checklist>

Workflow argument:
{{PROMPT}}
