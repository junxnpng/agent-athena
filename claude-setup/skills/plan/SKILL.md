---
name: plan
description: Strategic planning before implementation
argument-hint: "<what to plan>"
---

<Purpose>
Create a thorough execution plan before writing any code.
Explore the codebase, design the approach, identify risks, get critique — then decide.
</Purpose>

<Use_When>
- User says "plan this", "let's plan", "plan the"
- Task is complex enough to benefit from planning before implementation
- User wants to review approach before committing
</Use_When>

<Do_Not_Use_When>
- Simple task with obvious approach → just do it
- User wants autonomous execution → use autopilot
- User wants brainstorming, not planning → use ideate
</Do_Not_Use_When>

<Steps>
1. **Explore**: Understand the current codebase state
   - Map relevant files and structure
   - Identify existing patterns to follow
   - Find potential conflicts or dependencies

2. **Design**: Use planner (opus) to create the execution plan
   - Break into atomic, ordered steps
   - Assign file ownership per step
   - Identify parallel opportunities
   - Estimate complexity per step

3. **Critique**: Use critic (opus) to challenge the plan
   - What assumptions are fragile?
   - What could go wrong?
   - What's missing?
   - Is there a simpler approach?

4. **Refine**: Incorporate critique into the final plan
   - Address critical issues
   - Document accepted risks
   - Finalize step order and dependencies

5. **Present**: Show the plan to the user for approval
   - English plan (canonical for execution)
   - Korean plan (user review version)
   - Clear next steps: "approve to proceed" or "adjust X"
</Steps>

<Output_Format>
## Plan: [Title]

### Goal
[What we're building and why]

### Steps
1. [Step] — [files] — [trivial/scoped/complex]
   Depends on: none
2. [Step] — [files] — [complexity]
   Depends on: 1

### Parallel Opportunities
- Steps X and Y can run simultaneously

### Risks & Mitigations
- [Risk]: [how to handle]

### Critique Response
- [Issue raised]: [how addressed / accepted as risk]

### Acceptance Criteria
- [ ] [criterion]
</Output_Format>

Planning:
{{PROMPT}}
