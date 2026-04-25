---
name: learner
description: Extract a hard-won, codebase-specific insight from the current session as a learned-skill note that survives compaction.
argument-hint: "<topic slug>"
---

[LEARNER ACTIVATED]

<Purpose>
The current session debugged something non-obvious, hit a hidden gotcha, or
uncovered behavior that only matters in THIS codebase. Capture it as a learned
note so the next session (or next person) doesn't have to re-derive it.
This is NOT a generic skill library — it's hard-won knowledge tied to the
current repo.
</Purpose>

<Use_When>
- Just solved a bug that took real investigation (not a 1-liner fix)
- Discovered a non-obvious workaround that's specific to this codebase
- Hit a gotcha that wastes time when forgotten
- Uncovered undocumented behavior that affects this project
</Use_When>

<Do_Not_Use_When>
- Generic programming patterns — those belong in language docs / library docs
- Anything Googleable in 5 minutes
- Code conventions / style — those belong in CLAUDE.md or rules files
- Single-shot trivia with no debugging effort behind it
</Do_Not_Use_When>

<Quality_Gate>
Before extracting, ALL three must be true:

1. **Non-Googleable** — couldn't be found via web search in 5 minutes
2. **Context-specific** — references actual file paths, error messages, or codebase patterns
3. **Hard-won** — required real debugging effort to discover

If any of these fails, do NOT save. Reply to the user explaining which gate failed.
</Quality_Gate>

<Steps>

1. **Quality gate check** (above). Abort with reason if any fail.

2. **Gather inputs**
   - **Problem**: the SPECIFIC error / symptom / confusion. Include exact error text, file:line, command that triggered it.
   - **Solution**: the EXACT fix — code snippet, config change, or precise instruction. Not "handle edge cases".
   - **Triggers**: keywords likely to surface when hitting this again (error fragments, file names, symptom phrases).

3. **Decide topic slug** (kebab-case, ≤40 chars). Used as filename and skill name.

4. **Compose body** using this template:
   ```markdown
   ---
   name: <slug>-learned
   description: <one-line, mentions the specific symptom>
   triggers:
     - <error fragment>
     - <file or function name>
     - <symptom phrase>
   ---

   # <Slug Title>

   ## The Insight
   The underlying PRINCIPLE — the mental model, not the fix. What is *true*
   about this codebase that isn't obvious from reading it?

   ## Why This Matters
   What goes wrong if you don't know this? What symptom led here?

   ## Recognition Pattern
   How do you know when this applies? What error / behavior signals it?

   ## The Approach
   How should Claude THINK about this — the decision-making heuristic.
   Not just code; the reasoning that produces correct code.

   ## Example
   Concrete code or config snippet, as illustration of the principle
   (not copy-paste material).
   ```

5. **Save** to `.athena/learned/<slug>.md` (project-local, under `.athena/` so
   gitignored by default). User can promote to `docs/` or commit manually if
   the team should share it.

6. **Report**:
   - Saved path
   - Triggers list (so user can sanity-check they'll fire)
   - Whether quality gate passed cleanly or had a borderline call
</Steps>

<Rules>
- Reusability test: can Claude apply this to a NEW situation, not just the identical one? If no, don't save.
- Prefer principle over recipe. "Wrap each I/O op separately because lifecycle mismatches happen between ops" beats "add try/except around line 42".
- Triggers must be specific. "error", "bug", "issue" are useless. "ECONNRESET in proxy", "ESM resolution in dist/" are useful.
- Save location is `.athena/learned/` — never `claude-setup/skills/` (plugin scope) and never `~/.claude/skills/` (would leak codebase-specific knowledge to unrelated projects).
- One file per insight. Don't batch unrelated learnings into one note.
</Rules>

<Final_Checklist>
- [ ] Quality gate passed (non-Googleable + context-specific + hard-won)
- [ ] File at `.athena/learned/<slug>.md` exists with valid frontmatter
- [ ] Triggers are specific (no generic words)
- [ ] Body uses Insight / Why / Recognition / Approach / Example structure
- [ ] Solution includes file path or precise location, not vague advice
</Final_Checklist>

Topic argument:
{{PROMPT}}
