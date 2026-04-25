---
name: sciresearch
description: Decompose a large research question into testable hypotheses, run scientist agents in parallel on each, and synthesize [STAT:*]-backed findings into one report with contradiction surfacing.
argument-hint: "<research question> [--n=<4-8>]"
---

[SCIRESEARCH ACTIVATED]

<Purpose>
For research questions too large for a single scientist run — e.g.,
"Does architecture X outperform Y on benchmark Z (and at what cost)?",
"Is technique T's improvement reproducible across seeds, scales, and tasks?".
Decompose into independent testable hypotheses, fan out to parallel scientist agents,
then synthesize their [STAT:*]-backed findings while surfacing contradictions
and knowledge gaps. Sibling pattern to /athena:multi-review (different fan-out axis).
</Purpose>

<Use_When>
- Research question has multiple natural sub-questions (overall vs ablation vs cost)
- User says "run a study", "investigate this thoroughly", "compare X vs Y", "ablation"
- Existing data needs to be re-analyzed under several lenses
- Pre-experiment exploration before committing compute
</Use_When>

<Do_Not_Use_When>
- Single hypothesis only → call scientist agent directly
- Literature/prior-art question (no data analysis) → use researcher
- SDK/library doc lookup → use document-specialist
- Implementation work (writing the experiment harness) → use executor
</Do_Not_Use_When>

<Steps>

1. **Parse & frame the question**
   - Extract: target claim, available data sources, comparison axis (if any), success criterion.
   - If the question is too vague to test ("is X good?"), ask the user to refine *once* before fan-out — bad hypothesis decomposition wastes parallel scientist runs.
   - Save framed question to `.athena/sciresearch/<timestamp>/question.md`.

2. **Decompose into hypotheses** (the leverage step)
   - Delegate to **planner** (opus) with prompt:
     ```
     Decompose this research question into 4-8 INDEPENDENT, testable hypotheses.
     Each hypothesis must:
       - State a specific prediction (not "X works better" — say "X has ≥5% accuracy gain on benchmark Z at p<0.05")
       - Be testable from available data without new data collection (or flag if it requires new runs)
       - Be ORTHOGONAL to other hypotheses (no overlap that wastes parallel work)
     Return as JSON: [{id, prediction, verification_method, data_required, orthogonality_note}, ...]
     ```
   - Save planner output to `hypotheses.json`. Show user the list with one-liners; proceed unless prompted otherwise.

3. **Fan out to scientists in PARALLEL** (single message, N Task tool calls)

   For each hypothesis i in hypotheses.json:
   ```
   Task(
     subagent_type="athena:scientist",
     model="claude-opus-4-7",
     prompt="""
     [OBJECTIVE] Test hypothesis H{i}: <prediction>
     [VERIFICATION METHOD] <from planner>
     [DATA] <pointer to data_required>

     Apply your full investigation protocol (SETUP → EXPLORE → HYPOTHESIZE → ANALYZE → VISUALIZE → CRITIQUE → REPORT).
     Output the standard [OBJECTIVE]/[DATA]/[HYPOTHESIS]/[FINDING]/[LIMITATION] structure with [STAT:*] markers.
     Save report to `.athena/sciresearch/<timestamp>/H{i}-report.md`.

     Constraint: Do NOT branch into other hypotheses you discover mid-analysis — note them under [LIMITATION] for cross-synthesis instead.
     """
   )
   ```

4. **Wait for all scientists** to complete. Save outputs side by side under
   `.athena/sciresearch/<timestamp>/H<i>-report.md`.

5. **Synthesize** using the format below. Critical: do not flatten conflicting findings into a smooth narrative — surface the conflict.

</Steps>

<Synthesis_Format>
## SciResearch Report — <question summary>

### Question
<one-paragraph framing from step 1>

### Hypotheses tested (N)
| H# | Prediction | Verdict | Confidence |
|----|------------|---------|------------|
| H1 | <text>     | supported / refuted / inconclusive | high/med/low |
| ... |

### Findings rollup
[One row per hypothesis, showing only the headline [FINDING] + key [STAT:*] markers]

- **H1**: [headline finding]
  - [STAT:effect_size] ...
  - [STAT:ci] ...
  - [STAT:n], [STAT:seeds]
- **H2**: ...
- ...

### Cross-hypothesis contradictions
[If two hypotheses' findings disagree on a shared variable, list explicitly]
- H2 reports +5% accuracy gain ([STAT:ci] [3.1, 6.9]); H4 reports no significant effect on the same variable ([STAT:p_value] 0.31, n=80). Possible reason: <if scientists noted it under LIMITATION>.
- (skip section if no contradictions)

### Aggregated limitations
[Union of [LIMITATION] sections across all scientists, deduped]

### Knowledge gaps
[Hypotheses that planner identified but were marked "data not available" — listed for follow-up experiment design]

### Verdict on the original question
- <supported | partially supported | refuted | inconclusive>
- Reasoning: which hypotheses drove the verdict, and what would need to change for the verdict to flip
- Confidence: high/med/low — calibrated against worst-case [LIMITATION]s

### Suggested next experiments
1. <highest-leverage missing experiment, motivated by gap or contradiction>
2. ...

---
Saved: `.athena/sciresearch/<timestamp>/`
- question.md, hypotheses.json, H1-report.md … HN-report.md, synthesis.md
</Synthesis_Format>

<Rules>
- ALL N scientists must run in parallel (single message, multiple Task calls). Do not serialize "to be safe" — the value of sciresearch IS the parallel coverage.
- DO NOT cross-pollinate scientists. Each must work on its own hypothesis without seeing siblings' outputs — that's how independence is preserved.
- Synthesis must NOT smooth over contradictions. Surfacing conflicts is the orchestrator's primary job.
- If a scientist returns no [STAT:*] markers (i.e., no measurable evidence), record verdict as **inconclusive**, not "supported" — even if the prose sounds confident.
- If [LIMITATION] count exceeds [FINDING] count for a hypothesis, downgrade its confidence to low automatically.
- Verdict on the original question is the orchestrator's judgment — not a hypothesis vote count. Weight by evidence quality.
</Rules>

<Final_Checklist>
- [ ] N hypotheses generated (4-8) and stored in `hypotheses.json`
- [ ] All N scientists ran in parallel (verify in transcript)
- [ ] Each H<i>-report.md present with [STAT:*] markers
- [ ] Contradictions section surfaces real conflicts (or explicitly says "none")
- [ ] Knowledge gaps section lists data-unavailable hypotheses for follow-up
- [ ] Verdict justified by which hypotheses drove it
</Final_Checklist>

Original question:
{{PROMPT}}
