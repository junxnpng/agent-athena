---
name: ccg
description: Tri-model orchestration — Claude decomposes the request, fans out to Codex CLI + Gemini CLI for external advisor perspectives, then synthesizes the three views. Requires external CLIs (athena does not bundle them).
argument-hint: "<task or question>"
---

[CCG ACTIVATED]

<Purpose>
For requests where parallel external perspectives add value beyond what a
single Claude run produces — typical case: backend/architecture from Codex
+ UX/design/docs from Gemini, then Claude synthesizes both with explicit
disagreement surfacing.

This is a DOCUMENTATION-ONLY skill in athena's scope. Athena focuses on
Anthropic / Claude-native workflows; the Codex and Gemini CLIs are external
infrastructure that the user must install + configure separately. CCG works
when both CLIs are available, gracefully falls back when one or both are
missing.
</Purpose>

<Use_When>
- Backend/analysis + frontend/UX work in one request
- Code review where architecture (Codex) and UX/readability (Gemini) lenses both matter
- Cross-validation where Codex and Gemini may legitimately disagree
- Fast advisor-style external input without spinning up sub-agent infrastructure
</Use_When>

<Do_Not_Use_When>
- Single-perspective task — call the appropriate athena agent directly (executor / code-reviewer / etc.)
- Codex AND Gemini CLIs both unavailable — ccg refuses on this case (no cross-validation possible); use a single-agent athena alternative directly (executor / code-reviewer / etc.)
- Sensitive code that should not leave the local box (Codex/Gemini calls send prompt content to their respective providers)
- Need quantitative analysis — use scientist or sciresearch (different rigor)
</Do_Not_Use_When>

<Requirements>
External CLIs (athena does NOT install these — user responsibility):

| Provider | Install command (typical) |
|----------|--------------------------|
| Codex    | `npm install -g @openai/codex`  |
| Gemini   | `npm install -g @google/gemini-cli`  |

On invocation, check both. If neither is on PATH, refuse:
> CCG requires Codex CLI and/or Gemini CLI. Neither found.
> Install one or both and re-invoke, or use a single-provider athena
> agent (code-reviewer / critic / architect) for similar effect without
> external dependencies.

If only one is available: continue with that single advisor + Claude
synthesis, and explicitly note the missing perspective in output.
</Requirements>

<Steps>

1. **Check CLI availability**
   ```bash
   command -v codex
   command -v gemini
   ```
   If both missing → refuse per Requirements section.

2. **Decompose request** into:
   - **Codex prompt** — architecture, correctness, backend reasoning, risks, test strategy
   - **Gemini prompt** — UX, content clarity, alternatives, edge-case usability, doc polish
   - **Synthesis plan** — how to reconcile likely conflict areas

3. **Invoke advisors via Bash** (skill nesting is not supported in Claude Code; call the CLIs directly)
   ```bash
   codex "<codex prompt>"
   gemini "<gemini prompt>"
   ```
   Run in parallel where possible (background + wait). Capture stdout.

4. **Save artifacts** to `.athena/ccg/<timestamp>/`:
   - `codex.md` — codex output
   - `gemini.md` — gemini output
   - `claude-prompts.md` — the decomposition Claude used (for audit)

5. **Synthesize** — Claude writes the unified answer with these required sections:
   - **Agreed recommendations** (where both advisors converge)
   - **Conflicting recommendations** (explicit, named — do NOT smooth over)
   - **Chosen final direction + rationale** (Claude's call as orchestrator, not majority vote)
   - **Action checklist** (concrete next steps)

</Steps>

<Synthesis_Format>
## CCG Result — <task summary>

### Agreed Recommendations
- (Codex + Gemini both endorse) ...

### Conflicting Recommendations
[Surface explicitly — do not pick one silently]
- Codex says: <X>. Gemini says: <Y>. The disagreement is rooted in: <reason>.

### Final Direction
<Claude's synthesis — picks one or proposes a third path with explicit rationale>

### Risks of Chosen Direction
<from the side that lost — preserve the dissent's reasoning so future-you doesn't forget why>

### Action Checklist
1. ...
2. ...

---
Sources: `.athena/ccg/<timestamp>/codex.md`, `gemini.md`
</Synthesis_Format>

<Rules>
- CLI availability check is the FIRST step. Never proceed assuming presence.
- Skill nesting not supported — invoke CLIs via Bash, never via Skill().
- Conflicting recommendations MUST be surfaced (not silently chosen). The value of CCG is the disagreement, not the agreement.
- Claude is the synthesis orchestrator, not a majority voter. If Claude disagrees with both advisors, say so + explain.
- Sensitive content warning: Codex sends to OpenAI, Gemini sends to Google. If the task involves code/data that shouldn't leave local, refuse and recommend single-agent athena alternatives instead.
- Single-provider fallback (only Codex OR only Gemini available) is acceptable but must be flagged in synthesis ("missing UX perspective" / "missing architecture perspective").
</Rules>

<Final_Checklist>
- [ ] CLI availability checked before any prompt construction
- [ ] Decomposition saved to `claude-prompts.md` for audit
- [ ] Advisor outputs saved to `codex.md` / `gemini.md`
- [ ] Synthesis surfaces conflicts explicitly (not collapsed)
- [ ] Claude's chosen direction includes rationale, not just verdict
- [ ] Risks of chosen direction preserved (lost-side reasoning kept)
- [ ] If single-provider fallback: missing perspective flagged
</Final_Checklist>

Task:
{{PROMPT}}
