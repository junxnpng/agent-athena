---
name: research
description: Structured AI/ML research workflow — survey, analyze, recommend
argument-hint: "<research question or topic>"
---

<Purpose>
Structured research workflow for AI/ML topics. Survey techniques, analyze trade-offs,
and produce actionable recommendations with optional experiment design.
</Purpose>

<Use_When>
- User wants to understand a technique, paper, or approach
- User needs to compare multiple approaches for a problem
- User wants experiment design for an AI/ML idea
- User says "research", "survey", "what's the state of the art"
</Use_When>

<Do_Not_Use_When>
- User wants to brainstorm new ideas → use ideate
- User wants to implement something → use autopilot or delegate to executor
- Quick factual question → answer directly
</Do_Not_Use_When>

<Steps>
1. **Clarify**: Pin down the exact research question.
   - What problem are we solving?
   - What constraints exist? (compute, data, timeline)
   - What's the success metric?

2. **Survey**: Use researcher (opus) to investigate.
   - Search for relevant papers, techniques, implementations
   - Identify key approaches (at least 3 distinct ones)
   - Note maturity level of each (established / emerging / experimental)

3. **Analyze**: Deep comparison on dimensions that matter.
   - Performance (accuracy, speed, scalability)
   - Complexity (implementation difficulty, maintenance)
   - Requirements (data, compute, expertise)
   - Maturity (production-proven vs research-only)

4. **Critique**: Use critic (opus) to stress-test findings.
   - Are the comparisons fair?
   - What biases exist in the survey?
   - What's being overlooked?
   - Is the recommendation premature?

5. **Synthesize**: Produce final recommendation.
   - Top 1-2 approaches with clear reasoning
   - Honest about what we don't know
   - If experiment needed: design with baselines, metrics, ablations

6. **Persist**: Save findings if substantial.
   - Save to `.athena/research/<topic-slug>.md` for future reference
</Steps>

<Output_Format>
## Research: [Topic]

### Question
[Precise research question]

### Survey Results
#### [Approach 1]
- Source: [paper/repo/technique name]
- Key idea: [1-2 sentences]
- Maturity: [Established / Emerging / Experimental]
- Strengths: [for our use case]
- Weaknesses: [for our use case]

### Comparison Matrix
| Approach | Performance | Complexity | Compute | Maturity |
|----------|------------|------------|---------|----------|

### Critique
- [Bias/gap identified]: [implication]

### Recommendation
[Which approach and why. What we don't know yet.]

### Experiment Design (if applicable)
- Hypothesis: [what we expect]
- Baseline: [what to compare against]
- Metrics: [what to measure]
- Ablations: [what to vary]
- Estimated effort: [time/compute]

### Open Questions
- [What remains unclear and how to resolve it]
</Output_Format>

Research topic:
{{PROMPT}}
