---
name: multi-review
description: 6-persona parallel review (objective, critic, creative, conservative, rigor, contrarian) with synthesis. Use when reviewing significant code, designs, papers, or research artifacts.
argument-hint: "<file path | branch | PR url | text/idea to review>"
---

[MULTI-REVIEW ACTIVATED]

<Purpose>
Spawn 6 reviewer personas in parallel, each applying a distinct mindset to the same target.
Synthesize results into one report that surfaces consensus, divergence, and blocking issues.
</Purpose>

<Use_When>
- Reviewing significant code change before merge/commit
- Reviewing a paper, research design, or hypothesis
- Reviewing an architectural decision or RFC
- User says "review this from all angles", "multi review", "thorough review"
</Use_When>

<Do_Not_Use_When>
- Trivial code change → use single code-reviewer or skip
- Just want quality check → use code-reviewer alone
- Want only one specific lens → call reviewer agent with single PERSONA directly
</Do_Not_Use_When>

<Personas_And_Models>
| Persona | Model | Override at call time |
|---|---|---|
| objective    | sonnet | `model="claude-sonnet-4-6"` |
| critic       | opus   | `model="claude-opus-4-7"` |
| creative     | opus   | `model="claude-opus-4-7"` |
| conservative | sonnet | `model="claude-sonnet-4-6"` |
| rigor        | opus   | `model="claude-opus-4-7"` |
| contrarian   | opus   | `model="claude-opus-4-7"` |
</Personas_And_Models>

<Steps>

1. **Parse target**
   - File path → read content (or summarize if huge)
   - Branch / commit → `git diff <base>..<target>` summary
   - Text/idea → use as-is
   - URL → WebFetch and excerpt
   - Save target context to `.athena/multi-review/<timestamp>/target.md`

2. **Detect domain** (affects rigor persona behavior)
   - AI/ML code or paper → all 6 personas, rigor uses [STAT-MISSING]/[BASELINE-CONCERN]
   - Pure engineering code → all 6, rigor focuses on test coverage / proof obligations
   - Idea/design (no code) → all 6, rigor focuses on logical soundness

3. **Spawn 6 reviewers in PARALLEL** (single message, 6 Task tool calls)

   Each Task call:
   ```
   Task(
     subagent_type="athena:reviewer",
     model=<per-persona model>,
     prompt="""
     PERSONA: <name>
     TARGET: <inline content or path reference>
     DOMAIN: <ai-research|engineering|idea>

     Apply your persona EXACTLY as defined. Do not water down to be balanced.
     """
   )
   ```

4. **Wait for all 6 to complete.** Save individual reports to `.athena/multi-review/<timestamp>/<persona>.md`.

5. **Synthesize** using the format below.

</Steps>

<Synthesis_Format>
## Multi-Review Report — <target name>

### Common Ground (≥3 personas agreed)
- [observation cited by which personas]

### Blocking Issues (must fix before approval)
[from critic + rigor primarily]
- **[HIGH]** [issue] — [persona] @ [file:line if applicable]
- **[HIGH]** ...

### Production / Reproduction Concerns
[from conservative]
- ...

### Scientific Rigor Issues (AI work)
[from rigor; skip section if non-AI]
- [STAT-MISSING] ...
- [BASELINE-CONCERN] ...

### Alternative Approaches Worth Exploring
[from creative]
- [alternative]: [why novel here]

### Counter-position (if convincing)
[from contrarian — only include if their case is genuinely strong]
- Steelman summary: [...]
- Implication if true: [...]

### Factual Baseline
[brief, from objective — for shared understanding]

### Verdict
- APPROVE / REQUEST CHANGES / RECONSIDER APPROACH
- Reasoning: [1-2 sentences citing which personas drove the verdict]

### Priority Action Order
1. [most urgent — usually a HIGH blocking issue]
2. [next]
3. [worth considering — alternative or contrarian]

---
Saved: `.athena/multi-review/<timestamp>/`
- target.md, objective.md, critic.md, creative.md, conservative.md, rigor.md, contrarian.md, synthesis.md
</Synthesis_Format>

<Rules>
- ALL 6 personas must run. Don't skip "to save tokens" — multi-review's value IS the diversity.
- Synthesis must NOT water down individual personas to consensus. Surface divergence honestly.
- If contrarian's case is weak, briefly acknowledge but don't inflate.
- If rigor finds [STAT-MISSING] in AI work, that's automatically a blocking issue (verdict ≠ APPROVE).
- Verdict is your judgment as orchestrator — not majority vote.
</Rules>

<Final_Checklist>
- [ ] All 6 reviewer reports saved to `.athena/multi-review/<timestamp>/`
- [ ] Synthesis covers all sections (skip rigor only if non-AI)
- [ ] Verdict justified by which personas drove it
- [ ] Priority order is actionable (not vague)
</Final_Checklist>

Target:
{{PROMPT}}
