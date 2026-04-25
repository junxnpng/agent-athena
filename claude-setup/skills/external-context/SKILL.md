---
name: external-context
description: Decompose a query into 2-5 facets and run parallel document-specialist agents. Synthesizes external documentation, references, and citations into one report.
argument-hint: "<topic or question>"
---

[EXTERNAL-CONTEXT ACTIVATED]

<Purpose>
For questions whose answer requires fresh external information from multiple
angles — official docs + community gotchas + comparison + best practices.
A single document-specialist run misses the breadth; multiple sequential runs
duplicate setup. external-context decomposes the query into orthogonal
facets and fans out parallel document-specialist agents, then synthesizes
their outputs with citations preserved.

Sibling pattern to multi-review (different fan-out axis: facets instead of
personas) and sciresearch (different agent: doc-specialist instead of scientist).
</Purpose>

<Use_When>
- Question needs information from multiple sources/angles (best practices + gotchas + comparison)
- "What's the latest on X?" / "Compare X vs Y" / "How do people use X in production?"
- SDK / library / framework questions where official docs alone are insufficient
- Pre-implementation context gathering before executor / autopilot starts
</Use_When>

<Do_Not_Use_When>
- Single concrete doc lookup ("what does X function return?") — call document-specialist directly
- Question about THIS codebase — use explore or researcher
- Speculative / opinion question with no factual basis to fetch
- Need data analysis on results — use sciresearch
</Do_Not_Use_When>

<Steps>

1. **Parse query** from `{{PROMPT}}`.

2. **Decompose into 2–5 orthogonal facets**
   Each facet:
   - Has a distinct search focus (no overlap)
   - Names likely source types (official docs, GitHub issues, blog posts, benchmarks)
   - Is independently answerable

   Example for "Compare Prisma vs Drizzle ORM for PostgreSQL":
   - Facet 1: Official feature parity matrix from each project's docs
   - Facet 2: Performance benchmarks from independent third parties
   - Facet 3: Migration / type-safety gotchas from GitHub issues
   - Facet 4: Real-world production usage stories (blog posts, post-mortems)

3. **Fan out parallel document-specialist agents** (single message, N Task calls)

   For each facet i:
   ```
   Task(
     subagent_type="athena:document-specialist",
     prompt="""
     Search topic: <facet i description>
     Sources to prioritize: <facet i's likely source types>

     Use WebSearch + WebFetch. For each finding, cite the URL and the
     publication / commit date if available. Surface contradictions
     between sources rather than picking one.

     Output structured: Findings (with citations), Contradictions, Confidence.
     """
   )
   ```

   Cap at **5 parallel agents** — beyond that, dilution > value.

4. **Wait for all** to complete. Save individual outputs to
   `.athena/external-context/<timestamp>/facet-<i>.md`.

5. **Synthesize** using format below. Critical: preserve every URL — the user
   may want to follow up on a specific source.

</Steps>

<Synthesis_Format>
## External Context — <query>

### Key Findings (3–5 headline points across all facets)
1. **<finding>** — Source: [title](url) (date)
2. **<finding>** — Source: [title](url) (date)

### Detailed Results

#### Facet 1: <name>
<aggregated findings with full citations>

#### Facet 2: <name>
...

### Contradictions / Open Disagreements
[If sources disagree, surface explicitly — don't smooth over]
- Source A says X (with citation), Source B says Y (with citation). Possible reason: ...
- (skip section if none)

### Confidence Per Facet
| Facet | Confidence | Reason |
|-------|-----------|--------|
| 1     | High/Med/Low | <e.g., "official docs + 3 corroborating sources"> |

### Sources
[Full list of every URL touched, deduped]

---
Saved: `.athena/external-context/<timestamp>/`
- query.md, facet-1.md … facet-N.md, synthesis.md
</Synthesis_Format>

<Rules>
- Cap at 5 parallel agents. More = noise, not signal.
- Document-specialist agents must use WebSearch + WebFetch — not memory.
- Every finding must carry its source URL. No bare claims.
- Surface contradictions explicitly. If two reputable sources disagree, that itself is a finding.
- Do NOT collapse low-confidence facets into the "Key Findings" headline — keep them in the detailed section with confidence labels.
</Rules>

<Final_Checklist>
- [ ] Query decomposed into 2–5 orthogonal facets (no overlap)
- [ ] All facets ran in parallel (single message, N Task calls)
- [ ] Each finding carries a URL citation
- [ ] Contradictions surfaced (or "none" stated)
- [ ] Confidence per facet stated
- [ ] Saved under `.athena/external-context/<timestamp>/`
</Final_Checklist>

Query:
{{PROMPT}}
