---
name: trace
description: Evidence-driven causal investigation — runs 3 competing tracer hypotheses in parallel, rebuttal round, then ranked synthesis with critical unknown and discriminating probe. Stops at "why" — does NOT cross into requirements gathering or fixing.
argument-hint: "<observation to trace>"
---

[TRACE ACTIVATED]

<Purpose>
For ambiguous, causal, evidence-heavy questions where the goal is to explain
**why** something happened — not to jump to a fix. Single-tracer runs miss
alternative explanations; trace fans out 3 deliberately different hypothesis
lanes via athena:tracer agents, runs a rebuttal round between leaders, and
returns a ranked synthesis with the next-best probe to collapse uncertainty.

This is the deep-dive Phase 1–3 used standalone. If you also need
requirements crystallization, use deep-dive (which adds the interview phase).
</Purpose>

<Use_When>
- Bug investigation: "Why does X fail intermittently?"
- Performance / latency / resource behavior explanation
- Postmortem / pre-mortem causal analysis
- Experimental result tracing: "Why did metric Y move?"
- Config / routing / orchestration behavior — non-obvious dependencies
- Architecture failure analysis: "Why is this design producing X effect?"
</Use_When>

<Do_Not_Use_When>
- Cause is already known and you just need a fix → executor or debugger
- Need requirements from the trace findings → use deep-dive (trace + interview)
- Single-source lookup ("what does X return?") → document-specialist
- The question is "what should we build?" not "why did X happen?" → deep-interview
</Do_Not_Use_When>

<Core_Tracing_Contract>
Always preserve these 7 distinctions in the output. Never collapse them.

1. **Observation** — what was actually observed
2. **Hypotheses** — competing explanations (≥3, deliberately different)
3. **Evidence For** — what supports each
4. **Evidence Against / Gaps** — what contradicts or is missing
5. **Current Best Explanation** — the leader right now
6. **Critical Unknown** — the missing fact keeping leaders apart
7. **Discriminating Probe** — the highest-value next step to collapse uncertainty

Never collapse trace into:
- A generic fix-it loop
- A debugger summary
- A raw dump of agent output
- Fake certainty when evidence is incomplete
</Core_Tracing_Contract>

<Evidence_Strength_Hierarchy>
Treat evidence as ranked, not flat:

1. Controlled reproduction / direct experiment / uniquely discriminating artifact
2. Primary source artifact with tight provenance (trace events, logs, metrics, configs, git history, file:line behavior)
3. Multiple independent sources converging on the same explanation
4. Single-source code-path or behavioral inference
5. Weak circumstantial clues (timing, naming, stack order, resemblance to prior bugs)
6. Intuition / analogy / speculation

Down-rank hypotheses that depend mostly on lower tiers when stronger contradictory evidence exists.
</Evidence_Strength_Hierarchy>

<Steps>

1. **Restate the observation** precisely. Generate a kebab-case slug.

2. **Generate 3 deliberately different hypothesis lanes**.
   Default partition (unless the problem suggests better):
   - Lane 1: **Code-path / implementation cause**
   - Lane 2: **Config / environment / orchestration cause**
   - Lane 3: **Measurement / artifact / assumption mismatch cause**

   Workers must pursue distinctly different explanations — not the same one in parallel.

3. **Lane confirmation** via `AskUserQuestion`:
   > Investigating: "<observation>"
   > Proposed lanes:
   > 1. <hypothesis 1>
   > 2. <hypothesis 2>
   > 3. <hypothesis 3>
   > Confirm and start, or adjust hypotheses?

   **Autonomy bypass:** if any `.athena/continuous/<id>/state.json` exists with `state.attention === true`, SKIP the AskUserQuestion. Deterministic default = accept the proposed 3 lanes as generated (the default partition Code-path / Config / Measurement covers the common cases; the rebuttal round at step 6 catches mis-partitions). Log decision to `.athena/continuous/<id>/decisions.md`.

4. **Spawn 3 tracer lanes in PARALLEL** (single message, 3 Task calls):
   ```
   Task(
     subagent_type="athena:tracer",
     prompt="""
     Lane: <hypothesis_N>
     Observation: <observed result>
     {if brownfield: include codebase context in <context>...</context>}

     Tasks per athena:tracer protocol:
     - Restate the lane hypothesis
     - Gather evidence FOR the lane
     - Gather evidence AGAINST the lane
     - Rank evidence strength (controlled reproduction → speculation)
     - Name the critical unknown for this lane
     - Recommend best discriminating probe
     - Apply systems / premortem / science lenses if relevant
     """
   )
   ```

5. **Wait for all 3.** Save individual outputs to `.athena/trace/<slug>/lane-<i>.md`.

6. **Rebuttal round.** Identify leader (highest evidence strength) and strongest non-leader. Have the non-leader present its best argument against the leader; force the leader to answer with evidence, not assertion.
   - If rebuttal materially weakens leader → re-rank.
   - If two "different" hypotheses reduce to same root mechanism → merge them, say so explicitly.
   - If they imply different next probes → keep separate.

7. **Apply cross-check lenses** to leader (when they can surface a missed explanation):
   - **Systems lens** — queues, retries, backpressure, feedback loops, upstream/downstream, boundary failures
   - **Premortem lens** — assume current best is incomplete; what failure mode would embarrass the trace?
   - **Science lens** — controls, confounders, measurement bias, alternative variables, falsifiable predictions

8. **Synthesize** using format below. Save to `.athena/trace/<slug>/synthesis.md`.

</Steps>

<Synthesis_Format>
## Trace — <observation summary>

### Observed Result
<exact observation>

### Ranked Hypotheses
| Rank | Hypothesis | Confidence | Evidence Strength | Why it leads |
|------|------------|-----------|-------------------|--------------|
| 1    | ...        | High/Med/Low | Strong/Moderate/Weak | ... |
| 2    | ...        | ...       | ...               | ... |
| 3    | ...        | ...       | ...               | ... |

### Evidence Summary by Hypothesis
- **Hypothesis 1**: ...
- **Hypothesis 2**: ...
- **Hypothesis 3**: ...

### Evidence Against / Missing
- **Hypothesis 1**: ...
- ...

### Rebuttal Round
- Best rebuttal to leader: ...
- Why leader held / failed: ...

### Convergence / Separation Notes
- ...

### Most Likely Explanation
<current best — may be "insufficient evidence" if all lanes are low-confidence>

### Critical Unknown
<single most important missing fact>

### Recommended Discriminating Probe
<single next probe that would collapse uncertainty fastest>

### Why Down-Ranked
[For each non-leading hypothesis, explicitly state why — "contradicted by X", "lost rebuttal", "ad hoc assumptions", etc.]

---
Saved: `.athena/trace/<slug>/`
- observation.md, lane-1.md, lane-2.md, lane-3.md, synthesis.md
</Synthesis_Format>

<Rules>
- 3 lanes MUST run in parallel (single message, 3 Task calls). Sequential fallback only if infrastructure forces it — note explicitly.
- Lanes MUST be deliberately different. Same hypothesis in 3 worker prompts is wasted parallelism.
- Rebuttal round is mandatory — even if leader looks dominant. Forcing the rebuttal often re-ranks.
- Down-ranking must be explicit ("contradicted by X" / "lost rebuttal" / "explains fewer facts" / "ad hoc assumptions") — teaching the reader why one beat the other.
- Trace stops at "why" + "what to probe next". Does NOT recommend a fix or generate requirements. For fix → debugger; for requirements → deep-interview or deep-dive.
- Convergence claim requires same root mechanism OR independent evidence streams pointing to the same explanation. Similar language alone is not convergence.
</Rules>

<Final_Checklist>
- [ ] 3 distinct hypothesis lanes generated and user-confirmed
- [ ] All 3 tracer lanes ran in parallel (single message verified)
- [ ] Each lane returned: hypothesis, evidence for, evidence against, strength rank, critical unknown, discriminating probe
- [ ] Rebuttal round executed between leader and strongest non-leader
- [ ] At least one cross-check lens (systems / premortem / science) applied to leader
- [ ] Synthesis includes ranked table, critical unknown, single recommended probe
- [ ] Down-ranking reasons stated explicitly per non-leading hypothesis
- [ ] Saved to `.athena/trace/<slug>/`
</Final_Checklist>

Observation:
{{PROMPT}}
