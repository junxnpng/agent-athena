---
name: ideate
description: Structured ideation — brainstorm, critique, and evaluate ideas
argument-hint: "<problem or domain to ideate on>"
---

<Purpose>
Structured ideation workflow. Generate diverse ideas, stress-test them with harsh
but constructive critique, and converge on the most promising paths.
</Purpose>

<Use_When>
- User wants to brainstorm approaches for a problem
- User has an idea and wants honest evaluation
- User says "ideate", "brainstorm", "what if", "ideas for"
- User wants to explore before committing to an approach
</Use_When>

<Do_Not_Use_When>
- User wants research on existing techniques → use research skill
- User already knows what to build → use autopilot or plan
- Quick opinion → answer directly
</Do_Not_Use_When>

<Review_Tone>
Apply these lenses in strict priority order:
1. **Devil's advocate** — attack first. What's wrong? What breaks? What's naive?
2. **Multi-perspective** — then broaden. User/technical/business/research angles.
3. **Feasibility/ROI** — then ground it. Is it worth the effort?
4. **Encouragement** — last. Acknowledge what's genuinely strong. Brief.
</Review_Tone>

<Steps>
1. **Frame**: Define the problem space clearly.
   - What are we trying to achieve?
   - What constraints exist?
   - What's been tried before? (if known)

2. **Diverge**: Use ideator (opus) to generate ideas.
   - At least 3 genuinely distinct approaches (not variations)
   - Include at least 1 unconventional/non-obvious option
   - Each idea: concept, strengths, weaknesses, feasibility

3. **Attack**: Use critic (opus) to tear apart each idea.
   - What's the fatal flaw in each?
   - What hidden assumptions exist?
   - Which ideas are "interesting but impractical"?
   - Which ideas survive scrutiny?

4. **Evaluate**: Score surviving ideas.
   - Impact: how much does it move the needle?
   - Effort: how hard to build/test/maintain?
   - Risk: what could go wrong?
   - Novelty: does it offer something new?

5. **Converge**: Recommend top 1-2 ideas with reasoning.
   - Be direct about why others were eliminated
   - Acknowledge remaining uncertainties
   - Suggest next step (research? prototype? plan?)
</Steps>

<Output_Format>
## Ideation: [Topic]

### Problem
[What we're solving, key constraints]

### Ideas Generated
#### 1. [Idea Name]
- Concept: [1-2 sentences]
- Strengths: [specific]
- Fatal flaw: [critic's main attack]
- Survives? [Yes/No — why]

#### 2. [Idea Name]
...

### Evaluation (survivors only)
| Idea | Impact | Effort | Risk | Novelty | Score |
|------|--------|--------|------|---------|-------|

### Recommendation
[Top pick and direct reasoning. Don't hedge.]

### What Deserves More Scrutiny
[Assumptions or decisions that need validation before committing]

### Suggested Next Step
[research / prototype / plan / abandon]
</Output_Format>

Ideation topic:
{{PROMPT}}
