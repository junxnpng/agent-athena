# Verifying an AI agent's knowledge work — 2026 practitioner & method-level sources

**Research date:** 2026-09-21
**Scope question:** how a human (or a second system) checks an agent that was told "read these 40 papers, find every claim about KV-cache characteristics, and organize them", along five axes:
(a) each cited claim exists in the source and is faithfully stated; (b) nothing important was omitted (recall); (c) qualifiers/conditions were not dropped; (d) numbers are right; (e) the synthesis is logically consistent.

**Quote-fidelity convention used below.** Every quote was copied from a page I opened. Quotes marked **[2-pass]** were re-fetched a second time with a "reproduce exactly, character for character" prompt and matched; treat those as reliable verbatim. Quotes marked **[1-pass]** came from a single fetch — the fetch layer summarizes, so a 1-pass quote can be a near-verbatim reconstruction rather than an exact string. **Do not publish a [1-pass] quote without re-opening the page.** One concrete case of this drift is documented in §5.

Item count: **29** (26 in the 2026 main sections, 3 in pre-2026 background).

---

## 1. Items by direction

### 1.1 Karpathy — gen-verify loop, autoresearch, LLM Council

---

**[D1] Andrej Karpathy — "Sequoia Ascent 2026 summary"**
- Org/author: Andrej Karpathy (personal blog, bearblog)
- Date: **30 April 2026** (talk ~ week earlier)
- URL: https://karpathy.bearblog.dev/sequoia-ascent-2026/
- Access: **opened**
- Verbatim **[2-pass]**:
  > "Traditional computers automate what you can specify in code. This latest round of LLMs can automate what you can verify."
- Verbatim **[2-pass]**:
  > "Ultimately, almost everything can be made verifiable to some extent, some things more easily than others. Even for writing, you can imagine having a council of LLM judges and getting something reasonable."
- Verbatim **[2-pass]**:
  > "When frontier labs train these LLMs, they train them in giant reinforcement learning environments with verification rewards."
- **Technique (one line):** *Verifiability-first task framing* — before you delegate, define the check; for soft outputs (like a literature synthesis) the fallback check is a panel/"council" of LLM judges.
- Note: Karpathy himself hedges ("you can imagine", "something reasonable") — this is an aspiration, not a measured result. See **[D12]** for the measured limit of judge panels.

---

**[D2] Andrej Karpathy — `karpathy/autoresearch` (README)**
- Org/author: Andrej Karpathy
- Date: repo released **March 2026** (README carries a March 2026 note; repo page itself shows no explicit creation date)
- URL: https://github.com/karpathy/autoresearch
- Access: **opened**
- Verbatim **[1-pass]**:
  > "The metric is **val_bpb** (validation bits per byte) — lower is better, and vocab-size-independent so architectural changes are fairly compared."
- Verbatim **[1-pass]**:
  > "By design, training runs for a **fixed 5-minute time budget** (wall clock, excluding startup/compilation), regardless of the details of your compute."
- Verbatim **[1-pass]**:
  > "**`prepare.py`** — fixed constants, one-time data prep (downloads training data, trains a BPE tokenizer), and runtime utilities (dataloader, evaluation). Not modified."
- Verbatim **[1-pass]**:
  > "**`program.md`** — baseline instructions for one agent. Point your agent here and let it go. **This file is edited and iterated on by the human**."
- **Technique (one line):** *Cheap, fixed-budget verifier that the agent cannot edit* — one number, one fixed wall-clock cost, scorer file held outside the agent's write scope, objective authored by the human.
- **Why it transfers to a paper-reading task:** the analogue is a fixed-cost claim-level check (e.g. "does this exact sentence appear in the PDF?") owned by a script the agent cannot rewrite, plus a human-authored `program.md`-equivalent defining what "a good claim table" means.

---

**[D3] Karpathy's "LLM Council" (multi-model cross-check)**
- URL: https://github.com/karpathy/llm-council
- Access: **snippet only** (repo not opened; described via search results and secondary write-ups)
- Status: the *concept* (stage 1 independent answers → stage 2 anonymized cross-ranking → stage 3 chairman synthesis) is well attested, but I did **not** open the repo, and the repo predates 2026. The 2026-dated follow-ons I saw were secondary (an April 2026 project index; a claim that Perplexity shipped "Model Council" in Feb 2026) — **all snippet only, treat as unverified pointers.**
- **Technique (one line):** *Anonymized multi-model cross-review then synthesis.*
- **Important caveat:** the strongest 2026 measurement of exactly this pattern is negative — see **[D12]**.

---

### 1.2 Simon Willison 2026

---

**[D4] Simon Willison — "Don't be a meat proxy"**
- Author: Simon Willison (linking Niklas Gruhn)
- Date: **3 August 2026**
- URL: https://simonwillison.net/2026/Aug/3/dont-be-a-meat-proxy/
- Access: **opened**
- Verbatim (Willison) **[1-pass]**:
  > "Niklas Gruhn coins an excellent new term - meat proxy - for people who blindly copy and paste the output of AI systems to their peers."
- Verbatim (Gruhn, as quoted by Willison) **[1-pass]**:
  > "By all means, prompt AI. But don't just relay the output. Read it, understand it, validate it, and then write a response in your own words (a decent certificate that you've done the prior steps). Making that effort is value you can add."
- Original essay: https://gruhn.me/blog/2026-08-03/ (**snippet only** — not opened)
- **Technique (one line):** *Restatement-in-your-own-words as a cheap proof-of-reading* — a human-side gate on forwarding agent output.

---

**[D5] Simon Willison — "More than just code review"**
- Date: **22 August 2026**
- URL: https://simonwillison.net/2026/Aug/22/more-than-just-code-review/
- Access: **opened**
- Verbatim, complete entry **[2-pass]**:
  > "The key skill required to make productive use of coding agents is being able to confidently instruct them on how to make changes and then confidently verify that those changes have been applied in the correct way."
  > "Sometimes this involves reviewing every line of code they have written, but there are other ways to achieve that goal."
  > "Eyeballing every line of code has never been the most effective way to validate a change to a piece of software."
- **Technique (one line):** *Verify the property, not the prose* — substitute a targeted check for exhaustive line-by-line reading.
- **Direct application:** re-reading all 40 papers is the "eyeball every line" move; a claim-level existence/faithfulness check is the property check.

---

**[D6] Simon Willison — "Some thoughts on the Navier–Stokes Millennium Prize Problem"**
- Date: **8 September 2026**
- URL: https://simonwillison.net/2026/Sep/8/on-navier-stokes/
- Access: **opened** (and re-opened with an exact-reproduction prompt)
- **NEGATIVE FINDING, stated plainly:** Willison does **not** describe assessing or verifying the mathematical claim himself. His own sentences are about provenance, credit and training-data ethics, not about checking the proof. Verbatim **[2-pass]**:
  > "My interpretation of what happened here is that OpenAI heard that some Millennium Prize problems had been solved using LLMs and saw this as an opportunity to demonstrate the power of their latest model, without thinking too hard about the optics of scooping a team who had been using OpenAI's own models to work on this problem for the best part of a year."
  > "When an AI lab says that my data is 'used to improve model performance', _what does that actually mean_?"
- The only verification-shaped sentence on the page is quoted *from OpenAI*, not from Willison **[2-pass]**:
  > "Lean formalization and verification took an additional 17 hours via GPT‑6 Astra."
- **Technique (one line):** *Defer the technical check to a mechanical checker + ask instead who/what produced the claim* (provenance questioning). Useful mainly as the "what a careful non-expert actually does" data point.

---

**[D7] Simon Willison — "Agentic Engineering Patterns" (newsletter)**
- Date: **27 February 2026**
- URL: https://simonw.substack.com/p/agentic-engineering-patterns
- Access: **opened** — but yield was thin; only one on-topic passage found.
- Verbatim **[1-pass]**:
  > "Automated tests are no longer optional when working with coding agents. The old excuses for not writing them - that they're time consuming and expensive to constantly rewrite while a codebase is rapidly evolving - no longer hold when an agent can knock them into shape in just a few minutes. They're also _vital_ for ensuring AI-generated code does what it claims to do."
- **Technique (one line):** *Mechanized regression checks as the default trust mechanism for agent output.*

---

### 1.3 Anthropic 2026

---

**[D8] Anthropic — "Demystifying evals for AI agents"**
- Org: Anthropic (engineering blog)
- Date: **9 January 2026**
- URL: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- Access: **opened** (re-opened with exact-reproduction prompt)
- Verbatim **[2-pass]**:
  > "Coverage checks define key facts a good answer must include, and source quality checks confirm the consulted sources are authoritative, rather than simply the first retrieved."
- Verbatim **[2-pass]**:
  > "LLM-as-judge graders should be closely calibrated with human experts to gain confidence that there is little divergence between the human grading and model grading."
- Verbatim **[2-pass]**:
  > "To avoid hallucinations, give the LLM a way out, like providing an instruction to return "Unknown" when it doesn't have enough information."
- Verbatim **[2-pass]**:
  > "Read the transcripts!"
- Verbatim **[2-pass]**:
  > "Failures should seem fair: it's clear what the agent got wrong and why."
- Verbatim **[1-pass]** (scoring shape):
  > "For each task, scoring can be weighted (combined grader scores must hit a threshold), binary (all graders must pass), or a hybrid."
- **Technique (one line):** *Pre-declared coverage checks (a must-include fact list) + human-calibrated judges + an explicit "Unknown" escape hatch + transcript reading.*
- **Direct application:** the "coverage check" is the single most transferable idea for recall — write down, before or independently of the agent's run, the KV-cache claims a correct table MUST contain.

---

**[D9] Anthropic — "Claude Science, an AI workbench for scientists"**
- Org: Anthropic (news)
- Date: **30 June 2026**
- URL: https://www.anthropic.com/news/claude-science-ai-workbench
- Access: **opened**
- Verbatim **[1-pass]** (reviewer agent):
  > "incorrect citations, untraceable numbers, and figures that don't match their underlying code, and self-correcting as it goes"
- Verbatim **[1-pass]** (provenance bundle):
  > "the exact code and environment that produced it, a plain-language description of how it was created, and the full message history"
- Verbatim **[1-pass]**:
  > "Every output carries an auditable history of how it was made, so you can validate and reproduce the results."
- **Technique (one line):** *A separate reviewer agent whose job is exactly three checks — citation correctness, number traceability, figure↔code consistency — plus a provenance bundle attached to every artifact.*
- This is the closest thing in 2026 to a vendor-shipped version of the check the task asks for. Note it is a *product description*, not an evaluation: no measured detection rate is given.

---

### 1.4 Systematic-review / evidence-synthesis methods 2026

---

**[D10] Vivekanantha et al. — dual-LLM data extraction (GPT-5.2 + Gemini 3 Pro)**
- Journal: *Knee Surgery, Sports Traumatology, Arthroscopy*
- Date: **21 April 2026** (online; Aug 2026 issue)
- URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC13418397/
- Access: **opened**
- Verbatim **[1-pass]**:
  > "Across all 384 fields, both LLMs produced fully correct outputs in 315 (82%) cases, while at least one model was fully correct in 365 (95.1%)."
- Verbatim **[1-pass]**:
  > "At least one model was fully correct in over 95% of fields, supporting the use of a dual‐LLM framework as a reliable first‐pass tool for human verification."
- Verbatim **[1-pass]** (the protocol):
  > "two independent LLMs can extract data from the same study, with disagreements and conflicts that arise used to identify data that require human verification"
- Verbatim **[1-pass]** (failure mode — directly relevant to condition-dropping):
  > "Most errors were due to omission of minor details in complex domains such as surgical details."
- Verbatim **[1-pass]** (human-side risk):
  > "caution by human verifiers must be taken to minimise automation bias"
- **Technique (one line):** *Independent dual extraction by two different models; disagreement is the routing signal for scarce human attention.*
- **Caveat worth carrying:** 82% both-correct means ~18% of fields carry disagreement; and the residual error mode is **omission of detail**, i.e. exactly the qualifier-dropping failure. Agreement alone does not catch a condition both models drop.

---

**[D11] Figalová, Huestegge & Böckler-Raettig — recall/workload trade-offs and run-to-run consistency**
- arXiv: **2608.26885**, submitted **27 August 2026**
- URL: https://arxiv.org/abs/2608.26885
- Access: **opened**
- Verbatim (abstract, **[1-pass]** but arXiv abstract text is literal page text):
  > "No workflow recovered all verified eligible records."
  > "Two nominally identical GPT-5.4 file-batch runs agreed on 91.7% of records but differed on 94 records, including 29 verified eligible records retained by only one run."
  > "For high-recall tasks, LLMs are better suited to validated, auditable, human-supervised workflows than autonomous exclusion."
- **Technique (one line):** *Repeat-run consistency as a recall diagnostic* — run the same prompt twice and treat the symmetric difference as a lower bound on what a single run missed.
- **Why this matters for a 40-paper sweep:** a nominally identical repeat run disagreed on 8.3% of records and *uniquely* retained 29 truly eligible items. If your agent ran once, you have no idea which claims a second run would have found.

---

### 1.5 Judges, panels, and the limits of self/peer verification

---

**[D12] Guneet Kohli — "Nine Judges, Two Effective Votes: Correlated Errors Undermine LLM Evaluation Panels"**
- arXiv: **2605.29800**, submitted **28 May 2026**
- URL: https://arxiv.org/abs/2605.29800
- Access: **opened**
- Verbatim (abstract):
  > "Testing a panel of 9 frontier LLMs from 7 model families on three natural language inference datasets (each with 100 human annotations per item), we find that the 9 judges effectively provide only about 2 independent votes' worth of information."
  > "Roughly three-quarters of the panel's nominal independence is lost because the models make the same mistakes on the same items."
  > "the panel's actual accuracy falls 8-22 percentage points short of what independent voting would achieve, and the best single judge matches or outperforms the full panel across all conditions."
  > "Neither adding more judges nor using smarter aggregation algorithms helps -- established methods close at most 11% of this gap, even with access to the correct answers."
- **Technique (one line):** *Measure the effective independence of your judge panel before trusting it* — and the negative result: a council of LLM judges is worth far less than its headcount.
- **This is the single most important counterweight to [D1]/[D3].** If you use a multi-model council to check the KV-cache claim table, you must assume its errors are largely shared, and budget human checks accordingly.

---

**[D13] Peng et al. — "Can LLM-as-a-Judge Reliably Verify Rubrics in Agentic Scenarios?" (RuVerBench)**
- arXiv: **2606.29920**, v1 **29 June 2026**, v2 **2 September 2026**
- URL: https://arxiv.org/abs/2606.29920
- Access: **opened**
- Verbatim (abstract):
  > "RuVerBench covers two prevalent agentic domains, deep research and agentic coding, with 2,458 instances, each containing a model-generated output, a rubric, and a human-annotated label indicating whether the output satisfies the rubric."
  > "we evaluate numerous frontier LLMs and find that even the most advanced models achieve strong performance but still exhibit substantial noise."
  > "We find that weaker models are more sensitive to prompt variations, batched verification presents a trade-off between accuracy and efficiency, and majority voting yields effective but diminishing returns."
- **Technique (one line):** *Rubric-item-level verification with human-labeled ground truth, one rubric item at a time (not batched) when accuracy matters.*

---

**[D14] Wang et al. — "The Verification Horizon: No Silver Bullet for Coding Agent Rewards"**
- arXiv: **2606.26300**, v1 **24 June 2026**, v2 **29 June 2026**
- URL: https://arxiv.org/abs/2606.26300
- Access: **opened**
- Verbatim (abstract):
  > "A classical intuition holds that verifying a solution is easier than producing one. For today's coding agents, this intuition is being inverted: as foundation models develop stronger reasoning capabilities and engineering harnesses grow more sophisticated, generating complex candidate solutions is no longer difficult -- reliably verifying them has become the harder problem."
  > "Every verifier we can build is only a proxy for human intent, never the intent itself."
  > "we characterize the quality of verification signals along three dimensions -- scalability, faithfulness, and robustness"
  > "no fixed reward function can remain effective as policy capability continues to grow; and verification must co-evolve with the generator."
- **Technique (one line):** *Score your verifier itself on scalability / faithfulness / robustness, and expect to revise it as the generator improves.*

---

**[D15] Chen et al. — "Judging Is Not Enumerating: Silent Omissions in LLM-Authored Acceptable Sets"**
- arXiv: **2608.01000**, submitted **2 August 2026**
- URL: https://arxiv.org/abs/2608.01000
- Access: **opened**
- Verbatim (abstract):
  > "models judge whether a candidate belongs far better than they author the set itself"
  > "The dominant error is omission, which resists audit: an over-inclusion is a token a reviewer can challenge, a missing member an absence whose discovery is the authoring problem itself."
  > "Models detect planted over-inclusions 6-7x more often than planted omissions, and a production deployment of 43,227 items fails omission-first at 10:1."
  > "Gating authored verifiers on a known-correct probe cuts false rejection from 58-92% to at most 5%, but keeps only 5-39% of suites."
- **Technique (one line):** *Planted-item probes* — seed known-correct items into the corpus and measure how many the agent's set recovers; and the structural warning that asking a model "did you miss anything?" is the weakest possible recall check.
- **This is the sharpest theoretical statement of your axis (b).** "Find *every* claim about KV-cache characteristics" is exactly a set-authoring task, and the paper's core result is that models are much better at judging membership than at enumerating the set — so the right protocol is *generate candidates broadly, then judge*, never *ask for the set and trust it*.

---

**[D16] Cho & Sun — "When Should an AI Workflow Release? Always-Valid Inference for Black-Box Generate-Verify Systems"**
- arXiv: **2605.12947**, submitted **13 May 2026**
- URL: https://arxiv.org/abs/2605.12947
- Access: **opened**
- Verbatim (abstract):
  > "Each iteration can improve the candidate, but it also creates a release decision: when to stop and output the current result?"
  > "The wrapper builds a hard-negative reference pool of high-scoring failures, calibrates deployment-time evaluator scores against this pool, and accumulates the resulting evidence with an e-process."
  > "we show that a conservative reference pool yields finite-sample control of the probability of releasing on infeasible tasks, that is, tasks for which the given workflow is not capable of producing a reliable solution."
- **Technique (one line):** *Calibrate the verifier's score against a hard-negative pool and use an anytime-valid stopping rule*, so repeated checking does not silently inflate confidence.

---

### 1.6 Citation grounding / span-level attribution 2026

---

**[D17] Onweller, Lumer, Huber, Ramchandani, Subbiah, Feld — "Cited but Not Verified: Parsing and Evaluating Source Attribution in LLM Deep Research Agents"**
- arXiv: **2605.06635**, submitted **7 May 2026**
- URL: https://arxiv.org/abs/2605.06635
- Access: **opened**
- Verbatim (abstract):
  > "Citations are evaluated along three dimensions. (1) Link Works verifies URL accessibility, (2) Relevant Content measures topical alignment, and (3) Fact Check validates factual accuracy against source content."
  > "Unlike methods that verify claims in isolation, our framework closes the loop by retrieving the actual cited content, enabling human or model evaluators to judge each citation against its source."
  > "our results reveal that even the strongest frontier models maintain link validity above 94% and relevance above 80%, yet achieve only 39-77% factual accuracy"
  > "Fact Check accuracy drops by approximately 42% on average across two frontier models as tool calls scale from 2 to 150, demonstrating that more retrieval does not produce more accurate citations."
- **Technique (one line):** *Three-tier citation audit — existence (link/record resolves) → relevance (topically on-point) → faithfulness (the source actually says it)* — with the source content re-retrieved rather than trusted from the model's memory.
- **The headline number for your use case:** existence and relevance look fine (94%/80%) while *faithfulness* sits at 39–77%. A citation audit that stops at "the paper exists" measures almost nothing.
- **Second headline:** deeper research made faithfulness *worse*, not better — a 40-paper sweep is squarely in the regime where this degrades.

---

**[D18] Rao, Wong & Callison-Burch — "Detecting and Correcting Reference Hallucinations in Commercial LLMs and Deep Research Agents"**
- arXiv: **2604.03173**, submitted **3 April 2026**
- URL: https://arxiv.org/abs/2604.03173
- Access: **opened**
- Verbatim (abstract):
  > "We find that 3--13% of citation URLs are hallucinated -- they have no record in the Wayback Machine and likely never existed -- while 5--18% are non-resolving overall."
  > "Deep research agents generate substantially more citations per query than search-augmented LLMs but hallucinate URLs at higher rates."
  > "we release urlhealth, an open-source tool for URL liveness checking and stale-vs-hallucinated classification using the Wayback Machine."
  > "In agentic self-correction experiments, models equipped with urlhealth reduce non-resolving citation URLs by 6--79× to under 1%, though effectiveness depends on the model's tool-use competence."
- **Technique (one line):** *Automated existence check against an independent archive (Wayback), distinguishing link-rot from fabrication*, then feed the result back to the agent for self-correction.

---

**[D19] Shi, Sun, Zhang, Sun, Chawla & Ye — "CiteAudit: You Cited It, But Did You Read It?"**
- arXiv: **2602.23452**, v1 **26 February 2026**, v3 **1 May 2026**
- URL: https://arxiv.org/abs/2602.23452
- Access: **opened**
- Verbatim (abstract):
  > "large language models (LLMs) have introduced a critical risk: fabricated references that appear plausible but correspond to no real publications"
  > "We design a multi-agent verification pipeline that decomposes citation checking into metadata extraction, memory lookup, web-based retrieval, and final judgment."
  > "As manual verification becomes infeasible and existing automated tools remain fragile, we introduce CiteAudit, a comprehensive benchmark and detection framework for hallucinated citations."
- **Technique (one line):** *Decompose citation checking into staged sub-checks (metadata → memory → retrieval → judgment) rather than one holistic "is this real?" call.*
- Note: the abstract does not itemize error categories or give accuracy figures; the related-work snippets I saw citing "MisCiteBench" and "11–57% citation hallucination rates" were **snippet only** and are not asserted here.

---

**[D20] Elicit — systematic review product page (tool that shows source spans)**
- Org: Elicit
- Date on page when fetched: **17 September 2026**
- URL: https://elicit.com/solutions/systematic-review
- Access: **opened**
- Verbatim **[1-pass]**:
  > "Elicit cites every AI-generated claim with the exact sentence or figure from the underlying paper."
  > "Every decision is PRISMA-auditable with exclusion reasons, per-criterion scores, and supporting quotes."
  > "Every extraction is supported by quotes or figures from the source."
- Self-reported numbers on the page **[1-pass]**: "99.5%" screening recall, "96% Data extraction accuracy", "99.4% Data extraction accuracy", "0 False negatives; no key information missed".
- **Technique (one line):** *Span-anchored extraction — every extracted value carries the exact source sentence/figure, so checking is a string comparison rather than a re-read.*
- **Vendor-claim warning:** these are self-reported marketing figures on a product page. The page does **not** tell users to verify extractions against source papers. An independent feasibility study (Cambridge Core, *Research Synthesis Methods*) reporting that Elicit's accuracy "varied and was sensitive to prompt design, user account, and algorithm change" was **snippet only** — I did not open it, so treat that as a pointer, not evidence.

---

### 1.7 Formal / mechanical verification as a pattern (Tao 2026)

---

**[D21] Terence Tao — "Palomar – a registry of Lean verified mathematics"**
- Author: Terence Tao (What's new)
- Date: **18 August 2026**
- URL: https://terrytao.wordpress.com/2026/08/18/palomar-a-registry-of-lean-verified-mathematics/
- Access: **opened** (re-opened with exact-reproduction prompt)
- Verbatim **[2-pass]** — *the general principle you asked for, stated by Tao*:
  > "In recent months there has been a proliferation of AI-generated proofs of various old and new results, some of which have been formalized in the proof assistant language Lean. However, checking that a given Lean repository actually proves the claimed statement is somewhat non-trivial, especially for an audience which is not expert in the use of Lean: one has to first check that the claimed formal Lean statements have proofs that typecheck, that the proofs do not contain any 'cheats' such as adding additional axioms, and that the formal statements also match (in a semantic sense) the informal description of the claimed results."
- Verbatim **[2-pass]**:
  > "The first check (a) is purely mechanical, using the Lean tool Comparator"
  > "the second check (b) is non-deterministic, being performed by a large language model"
  > "that the solution module typechecks and proves exactly the results claimed in the challenge file"
  > "Palomar is **not** a peer-reviewed journal"
- **Technique (one line):** *Split the check into a purely mechanical part and an explicitly non-deterministic (LLM) part, label which is which, and refuse to let the mechanical pass stand in for peer review.*
- **Most transferable idea in this whole report for your problem:** Tao's three-part check maps exactly onto a claim table — (i) the formal artifact is internally consistent (the quote string actually occurs in the PDF), (ii) no "cheats" were added (no extra assumptions smuggled in), (iii) the *informal restatement semantically matches* the formal claim. (iii) is your condition/qualifier-drop check, and Tao explicitly marks it as the non-deterministic, LLM-performed, least-trustworthy leg.

---

**[D22] Terence Tao — "Mathematics in the age of AI"**
- arXiv: **2608.16753**, submitted **17 August 2026** (ICM 2026 essay)
- URL: https://arxiv.org/abs/2608.16753 · HTML: https://arxiv.org/html/2608.16753v1
- Access: **opened** (HTML full text)
- Verbatim **[1-pass]**:
  > "A formally verified proof is, after all, precisely a proof whose correctness no longer depends on the reputation or the diligence of its author."
  > "What if an AI tool generates a lengthy proof that is verified to be correct, but which nobody — not even the humans who prompted the tool — understands?"
  > "But passing an automatic filter is not a substitute for community acceptance; I do not believe that human referees can be removed from the publication process."
  > "The use of artificial intelligence in preparing papers can introduce material that makes reviewing more demanding."
- **Technique (one line):** *Mechanical checking decouples correctness from author reputation — but it is a filter, not a substitute for human acceptance.*
- **Fidelity note:** these are 1-pass extractions from a long HTML document; a targeted second pass failed to return a single contiguous passage covering all themes (the fetch layer correctly refused to invent one). Re-open the PDF before quoting any of these in print.

---

**[D23] Terence Tao — living AI-views summary (quote aggregation)**
- URL: https://teorth.github.io/tao-web/ai-views.html
- Last updated: **17 September 2026**
- Access: **opened** — but this is a **secondary compilation** of Tao quotes with attributions to other outlets.
- Quote it surfaces, attributed to **IEEE Spectrum, June 2026** **[1-pass, secondary]**:
  > "in math, we can completely check and verify outputs, and this really filters out a lot of the rubbish."
- Quotes it surfaces from Nov 2025 blog comments **[1-pass, secondary, pre-2026]**: "I would caution against using AI tools without the ability to independently verify their output."; "human experts remain the best metaprogram for these tools."
- **Technique (one line):** *Domain-dependent verifiability* — Tao's point is that math is unusually lucky; a KV-cache claim table has no typechecker, so the "filters out the rubbish" property does not transfer for free.
- **Handling:** do not cite the IEEE Spectrum line without opening the IEEE Spectrum piece.

---

**[D24] Terence Tao — "SAIR competition – Lean Kernel Challenge"**
- Date: **16 September 2026**
- URL: https://terrytao.wordpress.com/2026/09/16/sair-competition-lean-kernel-challenge/
- Access: **opened**
- Verbatim **[1-pass]**:
  > "We're excited to launch Stage 1 of the Lean Kernel Challenge, a multi-stage competition to improve the performance of verified computation in the Lean 4 kernel that the whole community can benefit from."
  > "Verified computation uses the Lean kernel to check computational results as part of a proof."
- **Technique (one line):** *Invest in making the mechanical checker fast enough to be used routinely* — a funding/infrastructure signal, not a method for text claims. **Low relevance to this task**; included for completeness of the named direction.

---

### 1.8 Evals practitioners 2026 (Husain / Shankar / Yan)

---

**[D25] Hamel Husain & Shreya Shankar — "Why is error analysis so important in AI evals, and how is it performed?" (AI Evals FAQ)**
- Date: published **27 June 2025**, **last modified 1 September 2026** — the agent-specific guidance is the 2026 layer
- URL: https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html
- Access: **opened** (re-opened with exact-reproduction prompt)
- Verbatim **[2-pass]**:
  > "Start by annotating at least 30 traces yourself before reviewing suggestions from an agent."
  > "A working pool of roughly 100 diverse traces is a useful guardrail for this human-agent loop."
  > "Human annotator(s) (ideally a [benevolent dictator](...)) review and write open-ended notes about traces, noting any issues."
  > "Accept or reject its suggestions and keep iterating until you reach [theoretical saturation](https://delvetool.com/blog/theoreticalsaturation), meaning new reviews stop revealing failure modes or changing existing ones."
- **Technique (one line):** *Human-first error analysis with a fixed minimum sample (≥30 read personally, ~100 pool) and open→axial coding until theoretical saturation*, before any automated judge is built.
- **Direct application:** read ~30 of the agent's claim rows yourself against their sources; the failure taxonomy you derive (e.g. "condition dropped", "number transposed", "claim merged from two papers") becomes the rubric for the automated pass over the rest.

---

**[D26] Hamel Husain & Shreya Shankar — "Evals Skills for Coding Agents"**
- Date: published **2 March 2026**, modified **31 August 2026**
- URL: https://hamel.dev/blog/posts/evals-skills/
- Access: **opened** — **thin yield.** The page names skills but does not restate the validation protocol.
- Verbatim fragments **[1-pass]**: an "error-discovery" skill that "helps you sample traces intelligently"; a "validate-evaluator" skill involving "Calibrate LLM judges against human labels".
- **Technique (one line):** *Package the judge-calibration step as a first-class, repeatable artifact rather than an ad-hoc prompt.*
- Listed for completeness; **[D25]** is the substantive source.

---

**[D27] Eugene Yan — "How to Work and Compound with AI"**
- Date: **3 May 2026** (page shows "May 2026")
- URL: https://eugeneyan.com/writing/working-with-ai/
- Access: **opened** (re-opened with exact-reproduction prompt)
- Verbatim **[2-pass]**:
  > "I think of verification as a ladder."
  > "Make it easy for the model to verify the work."
  > "For long-running tasks, have models watch models."
  > "We can do this in various ways. For example, the pair programmer can watch for execution drift—is the model doing the task right?"
- Verbatim **[1-pass]** (the ladder, expanded):
  > "Shift verification left; catch errors at write time."
  > "Near the bottom are post-edit hooks that run `ruff format`, `ruff check --fix` on files the model just updated. This happens deterministically and doesn't cost tokens. Higher on the ladder are tests, evals, LLM reviews, etc."
- **Technique (one line):** *A verification ladder — cheap/deterministic at the bottom, expensive/judgement at the top — plus a fresh-context second session that re-reads the spec and watches for execution vs. direction drift.*
- **Direct application:** bottom rung for a claim table = a script that greps each quoted span in the source PDF (deterministic, free); top rung = a human reading the synthesis for logical consistency. The "fresh-context watcher" is the natural mechanism for axis (e).

---

### 1.9 Directions that yielded nothing usable from 2026

Stated explicitly, per the rules:

- **OpenAI 2026 guidance on evaluating Deep Research outputs / graders.** I found the OpenAI page https://openai.com/index/frontierscience/ (rubric-based grading of scientific tasks, model-based grader, 7/10 threshold) but the server returned **HTTP 403** and I could not open it. The rubric details I saw are **snippet only** and are therefore not presented as items. **No opened OpenAI 2026 primary source on this topic.**
- **OpenAI "confessions" follow-ups.** The confessions paper is arXiv **2512.08093** (December **2025**) — pre-2026, and I did not open it. I found no opened 2026-dated OpenAI follow-up. The 2026 commentary I saw was secondary. **Nothing to report from 2026.**
- **Prover-Verifier follow-ups (2026).** Nothing 2026-dated surfaced in my searches. **Nothing to report.**
- **Anthropic Citations API 2026 update.** The Citations API launch is **January 2025** (see §4). I found no opened 2026-dated Anthropic post updating it. A 2026-dated third-party SDK changelog line surfaced but is **snippet only** and irrelevant as guidance.
- **Google grounding 2026.** The Gemini grounding docs (`groundingSupports`, `segment`, `confidenceScores`) are undated vendor documentation, and the docs state confidence scores are **not available for Gemini 2.5 and later** — so the one machine-readable confidence signal was removed. **No 2026-dated primary guidance item.**
- **Cochrane/RAISE 2026 recommendations specifically.** The joint position statement I opened is dated **11 November 2025** (see §4). Search results referenced "guidance issued in March 2026" with categories "acceptable use / use requiring human verification / inappropriate use"; I could **not** open a primary 2026 document containing that text — the Cochrane page redirected to a 2025 webinar listing that does not reproduce the recommendations, and the RAISE papers live on OSF (https://osf.io/fwaud/) which I did not open. **The three-category framing is snippet only and should not be cited as a 2026 Cochrane position without opening the OSF papers.**
- **Capture–recapture recall estimation applied to LLM extraction in 2026.** The one concrete 2026 mention I saw (a two-source Chapman estimator between OpenAlex and Crossref) came with a stated caveat that the estimator's independence assumption was violated, and another tool explicitly stating it implements *neither* capture–recapture nor relative recall. Both **snippet only**. **No solid 2026 primary source for capture–recapture on LLM extraction.** The closest usable 2026 substitutes are **[D11]** (repeat-run symmetric difference) and **[D15]** (planted-item probes).
- **A 2026 study on LLMs dropping qualifiers/conditions specifically.** The canonical study (Peters & Chin-Yee, generalization bias) is **2025** — see §4. I found no 2026-dated replacement. The nearest 2026 evidence for condition-drop is indirect: **[D10]**'s "omission of minor details" finding and **[D15]**'s omission-dominance result.

---

## 2. Technique taxonomy, with supporting 2026 sources

| # | Technique | What it answers | 2026 sources |
|---|---|---|---|
| T1 | **Existence check** — does the cited source exist at all? Resolve against an independent archive; separate link-rot from fabrication | (a), partly | **[D18]** urlhealth/Wayback (3–13% hallucinated URLs); **[D19]** CiteAudit staged pipeline; **[D17]** "Link Works" tier (>94%, i.e. nearly useless alone); **[D23-adjacent]** Retraction Watch **[F2]** |
| T2 | **Span-level attribution** — every claim carries the exact source sentence, so checking is string comparison not re-reading | (a), (c), (d) | **[D20]** Elicit "the exact sentence or figure from the underlying paper"; **[D9]** Anthropic reviewer agent flagging "untraceable numbers" |
| T3 | **Faithfulness check (re-retrieve the source, judge claim vs. source)** — distinct from T1/T2 and much weaker in practice | (a), (c) | **[D17]** "Fact Check" tier at only 39–77%, degrading ~42% as tool calls scale 2→150; **[D13]** rubric-item verification with human labels |
| T4 | **Independent re-extraction + agreement** — two different models (or a model and a human) extract independently; disagreement routes human attention | (a), (b), (d) | **[D10]** dual-LLM (82% both-correct, 95.1% at-least-one); **[D11]** repeat-run disagreement on 8.3% of records |
| T5 | **Recall estimation / omission probing** — planted known-correct items, repeat-run symmetric difference, pre-declared must-include lists | (b) | **[D15]** planted-item probes; omissions detected 6–7× less often than over-inclusions; **[D11]** 29 eligible records retained by only one of two identical runs; **[D8]** "Coverage checks define key facts a good answer must include" |
| T6 | **Condition / qualifier diff** — compare the agent's restatement against the source's scope conditions, semantically | (c) | **[D21]** Tao's check (b): does the informal description *semantically match* the formal claim — explicitly the non-deterministic leg; **[D10]** residual errors are "omission of minor details"; **[D15]** omission is the dominant, audit-resistant error. **Weakest-supported cell in 2026** (see §1.9) |
| T7 | **Numeric recomputation / traceability** — every number traces to a source or to the code that produced it | (d) | **[D9]** Claude Science flags "untraceable numbers" and "figures that don't match their underlying code"; **[D10]** numeric/nuanced fields are where dual-LLM error concentrates |
| T8 | **Mechanical / formal checking** — a deterministic checker that does not depend on the author's reputation; label which legs are mechanical vs. LLM | (a), (d), (e) | **[D21]** Palomar's mechanical (a) vs. non-deterministic (b) split; **[D22]** "correctness no longer depends on the reputation or the diligence of its author"; **[D24]** Lean Kernel Challenge; **[D2]** autoresearch's uneditable scorer |
| T9 | **Cheap fixed-budget verifier the generator cannot edit** — one number, bounded cost, human-authored objective | all | **[D2]** autoresearch (val_bpb, fixed 5-min budget, `prepare.py` not modified, `program.md` "edited and iterated on by the human"); **[D1]** "automate what you can verify"; **[D14]** score the verifier on scalability/faithfulness/robustness |
| T10 | **Human sampling with a fixed sample size** — read N yourself before automating; iterate to theoretical saturation | (a)–(e) | **[D25]** "at least 30 traces yourself", ~100-trace pool, open→axial coding, theoretical saturation; **[D8]** "Read the transcripts!"; **[D16]** anytime-valid stopping so repeated checks don't inflate confidence |
| T11 | **Calibrate the judge against human labels before trusting it** — and measure the judge's own error, not just its verdicts | meta | **[D8]** "closely calibrated with human experts"; **[D13]** RuVerBench human-annotated labels, "substantial noise"; **[D26]** "validate-evaluator" skill |
| T12 | **Multi-model cross-review (council)** — and the 2026 correction to it | (e) | **[D1]** "a council of LLM judges" (aspirational); **[D3]** LLM Council pattern (snippet only); **[D12]** ⚠️ **measured: 9 judges ≈ 2 independent votes; best single judge matches or beats the panel** |
| T13 | **Adversarial / fresh-context second reader** — a separate session with clean context re-reads the spec and the output, watching for drift | (e) | **[D27]** "have models watch models", execution drift vs. direction drift; **[D9]** a separate reviewer agent, not the author |
| T14 | **Disclosure / provenance bundle** — ship the code, environment, message history and method alongside the result | meta, (e) | **[D9]** "Every output carries an auditable history of how it was made"; **[D20]** "PRISMA-auditable with exclusion reasons, per-criterion scores, and supporting quotes"; **[D11]** "validated, auditable, human-supervised workflows"; **[P3]** Cochrane 2025 transparent-reporting rule |
| T15 | **Human restatement as proof-of-reading** — the forwarder must write the conclusion in their own words | meta | **[D4]** "write a response in your own words (a decent certificate that you've done the prior steps)" |
| T16 | **Verify the property, not the prose** — substitute a targeted check for exhaustive re-reading | all | **[D5]** "Eyeballing every line of code has never been the most effective way to validate a change"; **[D27]** the verification ladder; **[D7]** automated tests as the default trust mechanism |

### 2.1 What the 2026 evidence actually says about your five axes

- **(a) existence + faithful statement** — best covered. But note the split measured in **[D17]**: existence ≈94%, faithfulness 39–77%. Checking that the paper exists is nearly free and nearly worthless; checking that it *says that* is the expensive, load-bearing step.
- **(b) recall / omission** — structurally the hardest, and 2026 says so explicitly. **[D15]**: "a missing member an absence whose discovery is the authoring problem itself", and models detect planted over-inclusions 6–7× more often than planted omissions. The only 2026-supported mitigations are pre-declared must-include lists (**[D8]**), planted probes (**[D15]**), and repeat-run difference (**[D11]**). Asking the agent to self-audit for omissions is the one approach the evidence rules out.
- **(c) dropped qualifiers/conditions** — **weakest-supported axis in 2026.** Tao **[D21]** names the check ("semantic match between informal description and formal claim") and flags it as the LLM-performed, non-deterministic leg. **[D10]** finds residual errors are omissions of detail. The canonical quantitative study is 2025 (**[P2]**). Treat condition-drop as a known, unmeasured risk and handle it with T2 (span anchoring) + T10 (human sampling).
- **(d) numbers** — **[D9]** (untraceable numbers, figure↔code mismatch) and **[D10]** (numeric fields error-prone). T2 + T7: require the source span for every number so the check is arithmetic/string comparison, not judgement.
- **(e) synthesis consistency** — least mechanizable. **[D27]** fresh-context watcher and **[D12]**'s warning that a judge council buys much less independence than it appears to. **[D22]**: "passing an automatic filter is not a substitute for community acceptance."

### 2.2 A minimal protocol the 2026 sources jointly support

1. Before looking at output, write the **coverage list** of claims a correct table must contain (**[D8]**), and plant a few known claims as probes (**[D15]**).
2. Require **span anchoring** on every row — exact quoted sentence + locator (**[D20]**, **[D9]**).
3. Run a **deterministic existence/containment pass**: does the quoted span literally occur in the PDF; does the reference resolve (**[D18]**). Cheap, uneditable by the agent (**[D2]**).
4. **Re-run the extraction independently** (different model or second pass); treat the symmetric difference as the human work queue (**[D10]**, **[D11]**).
5. **Read ≥30 rows yourself** against sources; derive a failure taxonomy; iterate to saturation (**[D25]**, **[D8]**).
6. Only then build an **LLM judge, calibrated against those human labels**, item-by-item not batched (**[D13]**, **[D8]**); assume a panel gives ~2 votes of independence, not N (**[D12]**).
7. **Fresh-context second reader** for synthesis-level consistency (**[D27]**).
8. Ship the **provenance bundle** and disclose the method (**[D9]**, **[D20]**, **[P3]**).

---

## 3. Failure cases 2026 (what motivates all this)

**[F1] EY Canada retracts "Points of Attack" after 16 of 27 citations fail — GPTZero investigation**
- Authors: Om Ogale, Paul Esau, Alex Cui (GPTZero)
- Date: **14 May 2026**; EY pulled the report the same day
- URL: https://gptzero.me/investigations/ey
- Access: **opened**
- Verbatim **[1-pass]**:
  > "Now, more than ever, it's crazy to accept citations on faith — even those from a reputable source like Ernst & Young."
  > "One of our team members manually verified Hallucination Check's results to ensure their accuracy."
- Method: automated hallucination check over every citation, then **manual human verification of the automated results** — i.e. exactly T11 (validate the validator). Reported: 16 of 27 cited sources fabricated, misattributed, or broken; a cited McKinsey report and a cited Gartner document that do not exist; two Wired URLs returning 404. Some fabricated citations appear to have been "laundered" from low-quality blogs into the EY publication.
- **Lesson for this task:** a 27-citation report from a Big Four firm failed the *existence* check (T1) at 59%. Institutional reputation is not a substitute for the check.

**[F2] Retraction Watch — fabricated references in PubMed-indexed papers, 12× in two years**
- Author: Avery Orrall, Retraction Watch
- Date: **7 May 2026**
- URL: https://retractionwatch.com/2026/05/07/one-in-277-pubmed-indexed-papers-in-2026-shows-fabricated-references-says-analysis/
- Access: **opened**
- Verbatim **[1-pass]**:
  > "one in 277 papers published in the first seven weeks of 2026 referenced a paper that didn't exist"
  > "Fabricated citations in the biomedical literature have increased 12-fold in two years"
  > "publishers should integrate automated reference verification into submission workflows before peer review begins"
- Rates given: 1 in 277 (2026) vs 1 in 458 (2025) vs 1 in 2,828 (2023). Work led by Maxim Topaz (Columbia), published as a letter to *The Lancet*; the detection itself used AI to "distinguish genuine fabrications from formatting discrepancies such as informally abbreviated titles."
- **Technique embedded:** automated reference verification as a *gate before* review, not a step after it (T1 as a pipeline stage).
- Related, **snippet only**: reports that arXiv would ban researchers with hallucinated references (Retraction Watch weekend reads, 23 May 2026) — not opened, treat as a pointer.

**[F3] Damien Charlotin — AI Hallucination Cases database**
- Author: Damien Charlotin
- Accessed/last updated: **21 September 2026**
- URL: https://www.damiencharlotin.com/hallucinations/
- Access: **opened**
- **Count as displayed on 21 Sep 2026: 2,046 cases.**
- Verbatim **[1-pass]** (inclusion criteria):
  > "This database tracks legal _decisions_ I.e., all documents where the use of AI, whether established or merely alleged, is addressed in more than a passing reference by the court or tribunal. Notably, this does not cover mere allegations of hallucinations, but only cases where the court or tribunal has explicitly found (or implied) that a party relied on hallucinated content or material."
- Trajectory (**snippet only**, from secondary trackers — treat as approximate): ~1,490 cases in May 2026, 1,598 on 9 June 2026, 1,668 on 2 July 2026 → **2,046 on 21 September 2026**. Sanction figures quoted by secondary sources (e.g. $15,000 per attorney; ~$109,700 combined in *Couvrette v. Wisnovsky*) are **snippet only and unverified**.
- **Lesson:** the strict inclusion bar matters — these are adjudicated findings, not accusations, and the count roughly doubled inside 2026.

**[F4] Deloitte Australia (2025) → the 2026 pattern**
- The Deloitte AU incident itself is **2025** (AU$439,000 contract; ~AU$291,000 / final-instalment refund; ≥20 hallucinated citations and a fabricated judicial quote; disclosed use of Azure OpenAI GPT-4o). Placed here only as the origin of the pattern; **all details snippet only — I did not open a primary source**, and it is pre-2026.
- The 2026 instance of the same pattern is **[F1]** (EY), which I did open.
- Secondary claims that KPMG was likewise caught, and that FINRA issued a 2026 warning, are **snippet only and unverified**.

**[F5] Deep research agents hallucinate citations at *higher* rates than plain search-augmented LLMs**
- Source: **[D18]**, arXiv 2604.03173, 3 April 2026 — **opened**
- Verbatim: "Deep research agents generate substantially more citations per query than search-augmented LLMs but hallucinate URLs at higher rates."
- Paired with **[D17]**'s finding that Fact Check accuracy drops ~42% as tool calls scale from 2 to 150.
- **Lesson specific to your task:** the "read 40 papers and organize everything" shape of request is the *worst case*, not a neutral case. More sources and more tool calls made faithfulness worse in both 2026 measurements.

---

## 4. Pre-2026 background (clearly marked — NOT 2026)

**[P1] Shankar, Zamfirescu-Pereira, Hartmann, Parameswaran & Arawjo — "Who Validates the Validators? Aligning LLM-Assisted Evaluation of LLM Outputs with Human Preferences"**
- arXiv **2404.12272**, April **2024** (UIST 2024). URL: https://arxiv.org/abs/2404.12272 — **snippet only** (not opened in this session).
- Introduces EvalGen and **criteria drift**: users need criteria to grade outputs, but grading outputs is how they discover the criteria. This is the foundation under **[D25]**'s insistence that a human reads traces *before* a judge is written.

**[P2] Peters & Chin-Yee — "Generalization bias in large language model summarization of scientific research"**
- *Royal Society Open Science*, **2025** (arXiv 2504.00025). URL: https://royalsocietypublishing.org/doi/pdf/10.1098/rsos.241776 — **snippet only** (not opened).
- ~4,900 summaries across 10 models; overgeneralization in 26–73% of cases for several models even when explicitly prompted for accuracy; LLM summaries reportedly ~5× more likely than human-authored ones to contain broad generalizations; newer models sometimes worse.
- **This is still the best quantitative basis for axis (c)** (dropped qualifiers/conditions) — and it is 2025, not 2026. I found no 2026 replacement.

**[P3] Cochrane / Campbell / JBI / CEE — joint position statement on AI in evidence synthesis**
- *Cochrane Database of Systematic Reviews* editorial ED000178, **11 November 2025**. Authors incl. Flemyng, Noel-Storr, Macura, Gartlehner, Thomas, Meerpohl, Jordan, Minx, Eisele-Metzger, Hamel, Jemioło, Porritt, Grainger. URL: https://www.cochranelibrary.com/cdsr/doi/10.1002/14651858.ED000178/full — **opened**.
- Verbatim **[1-pass]**:
  > "AI and automation in evidence synthesis should be used with human oversight."
  > "Evidence synthesists are ultimately responsible for their evidence synthesis, including the decision to use artificial intelligence (AI) and automation, and to ensure adherence to legal and ethical standards."
  > "Any use of AI or automation that makes or suggests judgements should be fully and transparently reported in the evidence synthesis report."
- The **RAISE** recommendations it endorses live at https://osf.io/fwaud/ — **not opened**. Any "March 2026 three-category guidance" claim needs that source first (see §1.9).

**[P4] Other clearly pre-2026 items referenced above, not counted as items:**
- Anthropic **Citations API** (January 2025) — span-level grounding where `cited_text` is *extracted* from the document rather than generated. https://claude.com/blog/introducing-citations-api and Willison's note https://simonwillison.net/2025/Jan/24/anthropics-new-citations-api/ — **snippet only**. Mechanically this is the cleanest implementation of T2.
- Anthropic **"How we built our multi-agent research system"** (June 2025) — the LLM-judge rubric over factual accuracy / citation accuracy / completeness / source quality / tool efficiency, and the finding that human testers caught failure modes the judge missed. **Snippet only**; the 2026 successor I opened is **[D8]**.
- Anthropic **"Building Effective Agents"** (December 2024) — the evaluator-optimizer pattern. **Snippet only.**
- OpenAI **"Training LLMs for Honesty via Confessions"**, arXiv 2512.08093 (December 2025). **Snippet only.**
- Karpathy **llm-council** repo — predates 2026. **Snippet only** (see **[D3]**).

---

## 5. URLs opened vs. snippet-only

### 5.1 Opened (fetched and read)

Re-fetched a second time with an exact-reproduction prompt (**[2-pass]**, highest quote confidence):
1. https://karpathy.bearblog.dev/sequoia-ascent-2026/
2. https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
3. https://eugeneyan.com/writing/working-with-ai/
4. https://terrytao.wordpress.com/2026/08/18/palomar-a-registry-of-lean-verified-mathematics/
5. https://simonwillison.net/2026/Aug/22/more-than-just-code-review/
6. https://simonwillison.net/2026/Sep/8/on-navier-stokes/
7. https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html

Opened once (**[1-pass]**):
8. https://github.com/karpathy/autoresearch
9. https://simonwillison.net/2026/Aug/3/dont-be-a-meat-proxy/
10. https://simonw.substack.com/p/agentic-engineering-patterns
11. https://www.anthropic.com/news/claude-science-ai-workbench
12. https://arxiv.org/abs/2606.26300 (Verification Horizon)
13. https://arxiv.org/abs/2605.29800 (Nine Judges, Two Effective Votes)
14. https://arxiv.org/abs/2605.06635 (Cited but Not Verified)
15. https://arxiv.org/abs/2602.23452 (CiteAudit)
16. https://arxiv.org/abs/2608.01000 (Judging Is Not Enumerating)
17. https://arxiv.org/abs/2608.26885 (Recall–workload trade-offs)
18. https://arxiv.org/abs/2605.12947 (When Should an AI Workflow Release?)
19. https://arxiv.org/abs/2604.03173 (Reference Hallucinations / urlhealth)
20. https://arxiv.org/abs/2606.29920 (RuVerBench)
21. https://arxiv.org/abs/2608.16753 + https://arxiv.org/html/2608.16753v1 (Tao, Mathematics in the age of AI)
22. https://teorth.github.io/tao-web/ai-views.html (secondary compilation)
23. https://terrytao.wordpress.com/2026/09/16/sair-competition-lean-kernel-challenge/
24. https://gptzero.me/investigations/ey
25. https://retractionwatch.com/2026/05/07/one-in-277-pubmed-indexed-papers-in-2026-shows-fabricated-references-says-analysis/
26. https://www.damiencharlotin.com/hallucinations/
27. https://elicit.com/solutions/systematic-review
28. https://pmc.ncbi.nlm.nih.gov/articles/PMC13418397/ (dual-LLM extraction)
29. https://www.cochranelibrary.com/cdsr/doi/10.1002/14651858.ED000178/full (2025)
30. https://hamel.dev/blog/posts/evals-skills/
31. https://www.cochrane.org/events/recommendations-and-guidance-responsible-ai-evidence-synthesis (redirect target; **contained nothing usable**)

### 5.2 Attempted but blocked
- https://openai.com/index/frontierscience/ — **HTTP 403**
- https://www.sciencedirect.com/science/article/abs/pii/S1532046426001103 — **HTTP 403** (2026 systematic review of LLM data extraction)
- https://pubmed.ncbi.nlm.nih.gov/42501879/ — **cookie wall**, no content
- https://training.cochrane.org/resource/recommendations-and-guidance-on-responsible-ai-in-evidence-synthesis — **301** to a page with no recommendation text

### 5.3 Snippet only (seen in search results; NOT opened — do not quote)
https://gruhn.me/blog/2026-08-03/ · https://github.com/karpathy/llm-council · https://osf.io/fwaud/ · https://arxiv.org/abs/2404.12272 · https://royalsocietypublishing.org/doi/pdf/10.1098/rsos.241776 · https://arxiv.org/abs/2512.08093 · https://claude.com/blog/introducing-citations-api · https://simonwillison.net/2025/Jan/24/anthropics-new-citations-api/ · https://www.anthropic.com/research/building-effective-agents · https://arxiv.org/abs/2606.02060 · https://arxiv.org/abs/2605.08583 · https://arxiv.org/abs/2601.22984 · https://arxiv.org/abs/2606.19749 · https://arxiv.org/abs/2510.07926 · https://www.cambridge.org/core/journals/research-synthesis-methods/article/.../C97DAEC70C3173A260F0B12E729E7250 · https://ai.google.dev/gemini-api/docs/google-search · https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/grounding/grounding-with-google-search · https://retractionwatch.com/2026/05/23/weekend-reads-arxiv-ban-hallucinated-references-... · Deloitte/EY news coverage (Business Standard, Futurism, Fortune, TechCrunch, computing.co.uk, ia.acs.org.au, lawyer-monthly.com)

### 5.4 Secondary aggregators seen but deliberately NOT used as evidence
aibuilderclub.com · dooza.ai · mer.vin · kingy.ai · theaiopportunities.com · remio.ai · digitalapplied.com · futureagi.com · ability.ai · sonarsource.com · lumenalta.com · getaigovernance.net · vibegraveyard.ai · koreadeep.com · medium.com posts · theneuralbase.com · paperguide.ai · manusights.com. These are pointers only; several make specific numeric claims I could not confirm against a primary source.

### 5.5 A documented quote-drift incident (methodological note)
The same page (**[D1]**, Karpathy) returned two *different* renderings of the same idea on two fetches:

- 1st fetch: "Traditional software automates what you can **specify**. LLMs and reinforcement learning automate what you can **verify**."
- 2nd fetch, exact-reproduction prompt: "Traditional computers automate what you can specify in code. This latest round of LLMs can automate what you can verify."

The second is the one used in this report. This is a live demonstration of the exact failure mode the report is about: a summarizing layer produced a fluent, plausible, *wrong* string and presented it as a quote — and only a second independent pass against the primary source caught it (T4 + T1 in this report's own taxonomy). **Every [1-pass] quote above carries this risk.** Re-open before publishing.

### 5.6 Budget note
The WebSearch budget for this session (200 calls) was exhausted before the OpenAI-2026 and RAISE-2026 directions could be chased with further queries; those gaps are stated explicitly in §1.9 rather than filled with secondary material.
