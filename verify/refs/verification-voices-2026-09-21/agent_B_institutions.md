# Institutional practices for verifying AI-produced research/knowledge work — 2026 evidence

Compiled 2026-09-21. Scenario in view: a user asks an AI to "read these 40 papers, find every claim about
KV-cache characteristics, and organize them" — what institutional machinery exists in 2026 to check that
such output is faithful, complete, and not fabricated?

**Method note on quotes.** Every string in a `>` block was returned by WebFetch's extraction pass over the
page named, flagged by that pass as copied rather than summarized. I have not re-keyed them by hand. Where
the extraction pass explicitly said it was characterizing rather than copying, the item says so and the text
is left unquoted. Nothing here is my own paraphrase dressed as a quote.

**Status vocabulary.** "opened" = I fetched the primary page with WebFetch. "snippet only" = I saw it in a
search result but never opened the primary. "opened (secondary)" = I opened a news/secondary page that
reports on a primary I could not open.

---

## 1. Items by organization type

### 1a. AI labs

---

**[L1] Anthropic — Claude Science**
- Date: **2026-06-30** ("Publication Date: Jun 30, 2026" on page)
- URL: https://www.anthropic.com/news/claude-science-ai-workbench
- Status: **opened** (two separate fetches)
- Mechanism: **independent reviewer agent** auditing citations, numbers and figure-code consistency, with
  self-correction; **reproducibility bundle** attached to every figure; **actor-critic pairing** in
  literature-review pipelines.

> "a reviewer agent checks citations and calculations, flagging and correcting errors"

> "As the pipeline runs, a reviewer agent inspects the outputs, flagging incorrect citations, untraceable
> numbers, and figures that don't match their underlying code, and self-correcting as it goes"

> "Every output carries an auditable history of how it was made, so you can validate and reproduce the results"

> "When it generates a figure, Claude Science includes the exact code and environment that produced it, a
> plain-language description of how it was created, and the full message history"

This is the single most direct 2026 answer to the scenario — the literature-review use case is described
explicitly:

> "The sub-agents read through thousands of papers, pulling the central claim and the key quantitative
> finding, and storing them in an evidence state database"

> "A key component of the workflow, enabled by Claude Science, is the use of actor-critic pairs: one agent
> creates content while a separate reviewer agent evaluates it for accuracy and citation fidelity."

> "Jérôme Lecoq, a neuroscientist at the Allen Institute, used Claude Science to build a multi-agent
> "computational review template" comprising about 20 custom skills geared towards writing long-form reviews."

> "Before Claude Science, it could take Lecoq's team as many as two years to write such a review. He now has
> about 10 reviews, many more than 100 pages, with citations that were checked over by reviewer agents."

Numbers on the page, each with its source sentence as returned: "over 60 curated skills and connectors";
"about 20 custom skills"; "many more than 100 pages"; "one-tenth the time"; "up to 50 Claude Science AI for
Science projects"; "up to $30,000 in credits".

**Caveat worth carrying:** the extraction pass reported that the page contains *no* explicit statement about
hallucination, fabrication prevention, or any verification-accuracy metric. The reviewer agent is asserted,
not measured. There is no published recall or precision figure for it.

---

**[L2] Anthropic — Expanding our support for scientists**
- Date: **2026-08-27**
- URL: https://www.anthropic.com/news/expanding-support-for-scientists
- Status: **opened**
- Mechanism: **institutional verification of the user** (PI attestation) rather than of the output; repeats
  the auditable-artifact claim.

> "You must be a principal investigator or equivalent at an academic or nonprofit research institution to
> qualify; once verified, you can add the researchers in your lab to your plan."

The page says Claude Science "produces auditable artifacts". Numbers as returned: "10,000 initial seats";
"$15 per month" for premium seats with 5x usage limits; "Up to $50,000 in credits per project".

---

**[L3] OpenAI — "Evaluating large language models for accuracy incentivizes hallucinations", *Nature***
- Date: **2026-04-22** (Nature 653(8116), 1047–1051; DOI 10.1038/s41586-026-10549-w; PMID 42020757)
- Authors: Adam Tauman Kalai (OpenAI), Ofir Nachum (OpenAI), Santosh S. Vempala (Georgia Tech),
  Edwin Zhang (OpenAI/Isara Labs)
- URL (opened): https://pmc.ncbi.nlm.nih.gov/articles/PMC13216060/ — the nature.com URL 303-redirects to an
  IdP login and could not be opened.
- Status: **opened** (PMC mirror of the primary)
- Mechanism: **open scoring rubrics** — publishing the penalty for a wrong answer so that abstention becomes
  rational. This is the peer-reviewed journal version of the 2025 "why language models hallucinate" work.

> "facts lacking repeated support in training data (such as one-off details) yield unavoidable errors,
> whereas recurring regularities (such as grammar) do not."

> "guessing is a dominant strategy for binary evaluations"

> "correct answers receive 1 and incorrect answers receive −1 (hence abstain if <50% likely to be correct)"

> "with open rubrics, the mitigation helps across the board"

Numbers: tested four frontier models on SimpleQA ("4,326 questions"). Direct relevance to the scenario: a
model asked to "find *every* claim" is being scored on coverage, which is exactly the binary-accuracy regime
this paper says rewards guessing over abstention.

---

**[L4] OpenAI Forum — Terence Tao, "AI is ready for primetime in math and theoretical physics"**
- Date: **2026-03-10** (post); talk given that week at IPAM, "Accelerating Math and Theoretical Physics with AI"
- URL: https://forum.openai.com/public/blogs/terence-tao-ai-is-ready-for-primetime-in-math-and-theoretical-physics-2026-03-10
- Status: **opened**
- Mechanism: **formal verification (Lean)** as the checking layer, with an explicit statement of its limit.

> "reliable verification of proofs is important as AI increases the number of proposed solutions to
> well-known problems"

> "A literature search that once entailed hours or weeks of searching databases and libraries can now be
> shortened to a prompt that returns a useful map of relevant papers in minutes."

> "AI can make this worse by producing arguments that look polished while hiding the weak step"

The extraction pass characterized (did not quote) the Lean point as: his answer is formal verification using
tools such as Lean, which verifies a proof line by line and can keep AI honest. It reported that the page
contains no Tao statement quantifying how much human verification remains necessary.

A related Tao framing — that Lean guarantees only that a proof is formally rigorous, not that the formal
statement matches the intended one — appeared in search snippets from teorth.github.io and secondary
coverage. **Snippet only; not verified against a primary.** Flagged because it is the sharpest statement of
the residual gap, and it should be confirmed before being quoted.

---

**[L5] Google DeepMind — Co-Scientist blog (Nature paper announcement)**
- Date: **2026-05-19**
- URL: https://deepmind.google/blog/co-scientist-a-multi-agent-ai-partner-to-accelerate-research/
- Status: **opened**
- Mechanism: **dedicated "virtual peer reviewer" agent**, **majority of compute spent on verification**,
  **cross-checking claims against literature and databases**, **Elo tournament of competing hypotheses**.

> "Acts as a 'virtual peer reviewer,' critically evaluating hypotheses for correctness, quality, and novelty."

> "The majority of the system's computation is dedicated to _verifying_ these hypotheses. By deeply
> cross-checking claims against scientific literature and data, the system ensures that claims remain
> grounded, factually accurate, and logically coherent."

> "The system currently integrates web search and specialized databases like ChEMBL and UniProt to
> incorporate additional knowledge."

> "an 'idea tournament', using pairwise comparisons and simulated scientific debates to prioritize the most
> promising paths and hypotheses"

**Caveat:** the extraction pass reported that this page contains *no* mention of a numerical-claim
verification module, no fabrication/plagiarism penalty, and no accuracy metric. Search snippets attributed a
"separate verification module cross-checks every numerical claim against the actual results of the executed
code" and "fabrication rates of 80 to 100 percent in existing systems" to secondary coverage
(the-decoder.com). **Snippet only — do not cite as DeepMind's own wording.**

---

**[L6] Google DeepMind (public policy) — "Conjecture machines: AI agents and the new validation bottleneck in science"**
- Date: **July 2026** (page gives month, not day)
- Authors: Don Wallace, Conor Griffin, Sean O'Neill, Thang Luong, Owen Larter
- URL: https://deepmind.google/public-policy/conjecture-machines-ai-agents-and-the-new-validation-bottleneck-in-science/
- Status: **opened**
- Mechanism: names the problem directly — generation is cheap, refutation is not — and recommends
  **peer-review modernization with watermarking and "Human-AI Interaction Cards"**.

> "AI agents are conjecture machines, making ideas and candidate solutions abundant and relatively cheap.
> Refutations remain physical and institutional — and so, costly and slow."

> "We are moving toward a future of serious 'proof indigestion' where AI generates breakthroughs faster than
> humans can review them."

Numbers as returned, each with its context: "1.4 million cirrhosis deaths a year"; the US NSF invested
"$100 million towards a national network of distributed facilities"; the UK allocated "£81 million" for the
Materials Innovation Factory.

Four stated priorities (extraction-pass summary, not quoted): universal access to agents for independent
evaluation; agent-ready datasets with APIs and quality control; experimental infrastructure investment;
peer-review modernization with documented AI usage via watermarking and "Human-AI Interaction Cards".

This is the best 2026 institutional articulation of *why* the scenario is hard: the bottleneck moved from
producing the claim to checking it.

---

**[L7] METR — "Analyzing coding agent transcripts to upper bound productivity gains from AI agents"**
- Date: **2026-02-17**
- URL: https://metr.org/notes/2026-02-17-exploratory-transcript-analysis-for-estimating-time-savings-from-coding-agents/
- Status: **opened**
- **Negative finding, recorded as such.** The extraction pass reported the note contains no sentences about
  time spent reviewing or verifying agent output, review overhead, or the share of human time spent checking.

> "~1.5x to ~13x on Claude Code-assisted tasks for 7 METR technical staff in January 2026"

> "5305 Claude Code transcripts generated in January 2026 by 7 METR technical staff"

---

**[L8] METR — "Measuring the Self-Reported Impact of Early-2026 AI on Technical Worker Productivity"**
- Date: **2026-05-11**
- URL: https://metr.org/blog/2026-05-11-ai-usage-survey/
- Status: **opened**
- **Also largely a negative finding.** No sentences on verification burden or trust in AI output in the main
  text. The only adjacent phrase returned was "the permissions and review processes participants subject AIs
  to", described as collected but not analyzed in the main findings.

Numbers: 349 technical workers (87 software engineers, 71 researchers, 129 academics/PhD students, 48
founders/managers); median "1.4–2x change in the value in their work due to AI tools"; median speed change
"3x"; response rate "approximately 2% for respondents we email"; "10 respondents" filtered out of 359 raw.

**Bottom line for the METR target:** no 2026 METR report measuring human verification time was found. The
closest artifacts measure time *savings*, and both explicitly do not decompose review time.

---

**[L9] UK AI Security Institute — "'Did you lie?': Evaluating Lie Detectors across Model Scale and Belief-Verified Model Organisms"**
- Date: **2026-06-17**
- Authors: Alan Cooney, David Africa, **Geoffrey Irving**
- URL: https://www.aisi.gov.uk/research/did-you-lie-evaluating-lie-detectors-across-model-scale-and-belief-verified-model-organisms
- Status: **opened**
- Mechanism: **post-hoc honesty detection** — a chain-of-thought judge and activation probes applied to
  belief-verified testbeds. Adjacent to, not the same as, debate/scalable oversight.

> "a chain-of-thought judge, a logprob classifier, and two activation probes, including Did-You-Lie (DYL), a
> new method for training follow-up probes"

> "only the chain-of-thought judge remains strong, with 0.82 balanced accuracy"

Across 31 models from 2B to 1T parameters. Relevance: the one detector that survives is the one that reads
the model's stated reasoning — i.e. checking the *trace*, which is the same move as demanding source spans.

---

### 1b. Research tools (literature search, extraction, synthesis)

---

**[T1] Elicit — "Evaluating Elicit's Systematic Literature Review Capabilities"**
- Date: **2026-09-17**
- URL: https://elicit.com/blog/evaluating-elicit-slr
- Status: **opened**
- Mechanism: **recall estimation against a gold corpus** (Cochrane reviews) at every pipeline stage, plus
  **hand review of a sample of automated grades**. This is the closest thing in 2026 to a published answer
  to "is the extraction complete?"

> "95.0% recall on included studies, using only the review title as the query"

> "96.9% sensitivity" (abstract screening), with "92.54% specificity"

> "99.5% paper-level recall with 94.8% per-criterion accuracy" (full-text screening)

> "95.6% correct on Methods, Participants, and Interventions" (extraction)

> "994 unique reviews covering 38,493 study records"

Sampling frame: "balanced by round-robin sampling across 12 MeSH areas". Human spot-checks of the LLM grader:
"We randomly selected 25 of the answers that were graded correct to review by hand"; "reviewed by hand all 17
answers that were graded wrong"; for full-text screening they "manually examined roughly 30" of 138
inconsistent judgments. Stated limitation: extraction evaluation was restricted to "open-access studies only".

---

**[T2] Ai2 — "AstaBench update: New results, plus adoption from industry"**
- Date: **2026-04-30**
- URL: https://allenai.org/blog/astabench-update-spring-2026
- Status: **opened**
- Mechanism: **reproducible benchmarking with controlled retrieval corpora and per-problem rubrics graded by
  LLM-as-judge**; open-sourced so third parties can re-run.

> "everything is open so anyone can run it, submit to the leaderboard, or build on the tools"

> "The evaluation framework, tools, and a large collection of baseline agents...are all open-source."

Reported adoption: UK AI Security Institute via Inspect Evals; General Reasoning (SUPER-Expert on
OpenReward); agent submissions from Elicit, SciSpace, Distyl AI, EvoScientist. One score returned with a
model name: Claude Opus 4.7 at 58.0% overall.

**Caveat:** the extraction pass found no citation- or attribution-checking methodology and no
recall/precision metrics on this update page. The literature-review-table task and the "LLM-as-a-judge"
rubric grading came from search snippets and from the AstaBench paper (arXiv 2510.21652, **2025**), not from
this 2026 page.

---

**[T3] Edison Scientific (FutureHouse spinout) — Kosmos agent documentation**
- Date: **undated page** (fetched 2026-09-21)
- URL: https://docs.edisonscientific.com/agents
- Status: **opened**, but the page carries no date and no metrics.
- Mechanism: **full traceability of each conclusion to code lines and literature passages**.

> "Every conclusion is fully auditable, so you can trace any finding back to its original code or scientific source."

**Everything else about Kosmos is snippet only and should not be cited as 2026 primary material.** Search
snippets attribute "79.4%" claim accuracy and "80% reproducibility" to independent benchmarks, and attribute
to Edison the warning that traceable sources "do not make every conclusion correct". Kosmos itself was
announced **November 2025** — pre-2026. Treat the numbers as unverified.

---

### 1c. Research institutions / peer-reviewed measurement of the problem

---

**[R1] University of Pennsylvania — Rao, Wong, Callison-Burch, "Detecting and Correcting Reference Hallucinations in Commercial LLMs and Deep Research Agents"**
- Date: **2026-04-03** (arXiv 2604.03173)
- URL: https://arxiv.org/abs/2604.03173
- Status: **opened**
- Mechanism: **URL liveness checking against the Wayback Machine**, distinguishing hallucinated from
  link-rotted citations, plugged back in as an **agentic self-correction tool** (`urlhealth`).

> "We address six research questions about citation URL validity using 10 models and agents on DRBench
> (53,090 URLs) and 3 models on ExpertQA (168,021 URLs across 32 academic fields). We find that 3--13% of
> citation URLs are hallucinated -- they have no record in the Wayback Machine and likely never existed --
> while 5--18% are non-resolving overall. Deep research agents generate substantially more citations per
> query than search-augmented LLMs but hallucinate URLs at higher rates."

> "Domain effects are pronounced: non-resolving rates range from 5.4% (Business) to 11.4% (Theology), with
> per-model effects even larger."

> "In agentic self-correction experiments, models equipped with urlhealth reduce non-resolving citation URLs
> by 6--79× to under 1%, though effectiveness depends on the model's tool-use competence."

The most directly transferable 2026 result for the scenario: an existence check is cheap, catches a
single-digit-to-low-double-digit percentage of bad citations, and closes most of the gap when the agent can
call it mid-run. Note what it does *not* check — that the live source actually supports the claim.

---

**[R2] Badalova & Mayr — "Detecting Hallucinated and Suspicious Citations: What Current Tools Can and Cannot Do"**
- Date: **2026-07-17** (v1), **2026-07-28** (v2) (arXiv 2607.22693)
- URL: https://arxiv.org/abs/2607.22693
- Status: **opened**
- Mechanism: **comparative evaluation of five deployed citation-checking tools** — the counterweight to R1.

> "In this position paper, we review recent studies on hallucinated references and evaluate several currently
> available tools for detecting problematic references using documents containing hallucinated citations. The
> tools assessed include CheckIfExist, HalluCiteChecker, Hallucinator, Hallucinated Reference Finder (HalRef),
> and RefChecker. While these systems can provide useful early warnings in many cases, their performance is
> limited by reference extraction errors, incomplete metadata, limited database coverage, and inconsistent
> verification results."

> "more transparent and multi-source detection systems are still needed"

No precision/recall figures in the abstract or visible metadata.

---

**[R3] Shailendra, Kadel, Sharma, Tahidul, Saxena — "L-PRISMA: An Extension of PRISMA in the Era of Generative Artificial Intelligence (GenAI)"**
- Date: **2026-01-06** (arXiv 2603.19236)
- URL: https://arxiv.org/abs/2603.19236
- Status: **opened**
- Mechanism: **a deterministic statistical pre-screening layer inserted before the LLM**, so that the
  reproducible part of the pipeline is reproducible by construction, with human-led synthesis on top.

> "reproducibility, transparency, and auditability, the core PRISMA principles, are being challenged by the
> inherent non-determinism of LLMs and the risks of hallucination and bias amplification. To address these
> limitations, this study integrates human-led synthesis with a GenAI-assisted statistical pre-screening step.
> Human oversight ensures scientific validity and transparency, while the deterministic nature of the
> statistical layer enhances reproducibility."

---

### 1d. Publishers and standards bodies

---

**[P1] The Lancet — Topaz et al., "Fabricated citations: an audit across 2·5 million biomedical papers"**
- Date: **2026-05-07** (STAT, opened, states this; one secondary blog says May 9 — see discrepancy note)
- URL (primary, **NOT opened — HTTP 403**):
  https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(26)00603-3/fulltext
- Status: **primary not opened.** All numbers below come from three secondary pages I *did* open.
- Mechanism: **CITADEL** — automated identifier-vs-title matching, LLM triage of mismatches, then
  cross-reference against multiple scholarly databases.

Numbers, each kept with the page that carried it — **not merged, because they disagree**:

From **The Scientist** (opened; https://www.the-scientist.com/one-in-277-biomedical-papers-carry-fake-references-74480):
> "2.5 million biomedical papers"
> "125.6 million references"
> "4,046 fabricated references—whose claimed titles did not correspond to any existing publication—across 2,810 papers"
> "One in 2,828 papers contained at least one fabricated reference in 2023, which steeply increased to one in 277 in the first few weeks of 2026"
> "about four in 10,000 papers contained fabricated references in 2023, which spiked to 56.9 per 10,000 papers in early 2026"

From **Retraction Watch** (opened; https://retractionwatch.com/2026/05/07/one-in-277-pubmed-indexed-papers-in-2026-shows-fabricated-references-says-analysis/):
> "nearly 2.5 million papers published"
> "Topaz's group located 97.1 million references"
> "4,406 'fabricated' references that appeared in a total of 2,810 papers"
> 2023: "one in 2,828"; 2025: "one in 458"; first seven weeks of 2026: "one in 277"

From **STAT** (opened; https://www.statnews.com/2026/05/07/lancet-study-finds-steep-rise-fraudulent-citations-academic-papers/):
> "over 2 million papers and 97 million citations"
> "around 4,000 fabricated citations among 2,800 papers"
> "In 2023, 1 in 2,828 papers contained one or more fabricated references, but in 2025 that number had reached 1 in 458 — a sixfold increase"
> "During the first seven weeks of 2026, the rate reached 1 in 277 papers"
> "more than a third of fabricated citations come from two publishers"

> **DISCREPANCY — do not resolve by picking one.** The fabricated-reference count is **4,046** in The
> Scientist and **4,406** in Retraction Watch (digit transposition in one of them). The reference denominator
> is **125.6 million** references examined (The Scientist) vs **97.1 million** located/evaluated (Retraction
> Watch) vs "97 million citations" (STAT) — these may be two different stages (extracted vs verifiable), but
> I could not confirm that against the primary. **The primary must be opened before any of these is quoted.**
> The three rates 1-in-2,828 / 1-in-458 / 1-in-277 are consistent across all three sources.

Method, verbatim from **The Scientist**:
> "compared whether the title of each reference matched that of the paper that its DOI or PubMed identifier
> directed to. They then passed the paper titles flagged for mismatches through LLMs and cross-referenced
> these with other scholarly databases like Google Scholar, CrossRef, and OpenAlex. The team concluded that a
> reference was fabricated if its title did not appear in any of these databases."

Recommendations, verbatim from **The Scientist**:
> "Publishers could introduce tools to automatically verify references before beginning the peer review process."
> "If indexing services add integrity metadata to article records, users could assess the reliability of references."

Topaz, verbatim from **Retraction Watch**:
> "For papers with one or two fabricated references that are incidental to the main findings, I think
> correction and transparency may be more proportionate than retraction."

**What publishers told STAT they already do** (verbatim fragments from the opened STAT page): Science
journals employ "an automated tool to check references"; JAMA and NEJM both use "tools to validate citations";
PLOS said "We are looking to incorporate this into our publishing workflows and have been exploring offerings
in this space" and flagged "false positives in which legitimate references are flagged due to erroneous,
incomplete or inaccurate information."

---

**[P2] The Lancet — "Fabricated references: a new threat to editorial integrity" (companion editorial)**
- Date: **2026** (exact date not confirmed)
- URL: https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(26)00798-1/abstract
- Status: **snippet only — HTTP 403 on fetch.** Search snippets attribute to it: "91% of articles with
  problematic references had only one or two fabricated citations" and "routine automated verification can
  close this gap before fabricated references reach the published record". **Unverified; do not quote.**

---

**[P3] Springer Nature — "Springer Nature embraces AI tools across the publishing process…" (press release)**
- Date: **2026-03-12**
- URL: https://group.springernature.com/gp/group/media/press-releases/ai-tools-support-less-friction-and-increased-author-satisfaction/27849346
- Status: **opened**
- Mechanism: **publisher-side automated integrity screening at submission**, with human sign-off.

> "In 2025, over 1.5m papers benefited from nearly 60 AI tools supporting screening, editorial evaluation,
> retention and research integrity"

> "AI tools identified 25,000 papers as having issues such as image manipulation, fake references and
> fabricated text."

Other numbers on the page: "More than half a million 'clicks to submit' took place via Journal Finder";
"Editor Evaluation tool was used across nearly half a million manuscripts"; "Peer Reviewer Recommender
generated over 400,000 recommendations"; "Journal Transfer Recommender made over half a million transfer
recommendations (a 40% increase on 2024)"; author/editor/reviewer satisfaction "90%, 70% and 81%
respectively rating their experience as 'good' or 'excellent'". Human oversight phrases returned: "always
with expert human oversight" and "clear human oversight and accountability".

**Note:** Geppetto (AI-generated-content detection) and the irrelevant-reference checker are *not* named on
this 2026 page; those tool names come from earlier (2025) press releases and from search snippets.

---

**[P4] Springer Nature — AI guidance for researchers and communities (policy page)**
- Date: **undated; footer "© 2026 Springer Nature"** (fetched 2026-09-21)
- URL: https://group.springernature.com/gp/group/ai/ai-guidance-for-our-researchers-and-communities
- Status: **opened**
- Mechanism: **disclosure requirement + explicit duty to verify references + confidentiality bar on uploading
  manuscripts to public AI**. This is the policy that most directly governs the scenario.

> "Researchers may use AIGC to gather and summarize literature or obtain conceptual clarifications but must
> verify the accuracy and authenticity of AI-generated information, especially because AI can produce
> fabricated or outdated references."

> "ensure all citations are relevant, accurate, and truthful"

> "Authors remain responsible and accountable for the use of AI in their research, where it adheres with our
> guidance and principles."

> "Peer reviewers may use secure or institutionally-approved AI tools to assist them in line with our AI
> policies and in compliance with applicable laws."

> "AI may support reviewers, it cannot replace reviewer expertise, critique or judgement."

> "should not upload manuscript content to unsecured or public AI systems"

> "Use of AIGC must be fully and transparently declared, including tool versions, usage dates, prompts, and
> the extent of AI contribution."

> "The use of generative AI tools should be declared in the Introduction or Acknowledgements of the manuscript."

**Dating caveat:** the page carries no "last updated" stamp. Its 2026 status rests only on the copyright
footer. Treat as "current as of 2026-09-21" rather than "published in 2026".

---

**[P5] ICMJE — Recommendations updated January 2026**
- Date: **January 2026** (the ICMJE news listing, opened, shows exactly one 2026 item: "Up-Dated ICMJE
  Recommendations")
- URLs: https://www.icmje.org/news-and-editorials/ (opened) and
  https://www.icmje.org/recommendations/browse/roles-and-responsibilities/defining-the-role-of-authors-and-contributors.html (opened)
- Status: **opened** (both), but the recommendations page itself displays no version date, so the
  January-2026 dating comes from the news listing.
- Mechanism: **mandatory disclosure at submission + author duty to review and verify + attribution and full
  citations required**.

> "Authors should carefully review and edit the result because AI can generate authoritative-sounding output"

> "Humans must ensure there is appropriate attribution of all quoted material, including full citations."

> "At submission, the journal should require authors to disclose whether they used artificial intelligence (AI)-assisted"

> "Authors who use such technology should describe, in both the cover letter and the submitted work"

> "Chatbots (such as ChatGPT) should not be listed as authors because they cannot be responsible for the accuracy"

**Caveat:** the extraction pass returned these fragments truncated near ~125 characters. Each should be
re-read in full before being quoted in a paper.

---

**[P6] Nature Portfolio — AI editorial policy**
- Status: **NOT opened.** https://www.nature.com/nature-portfolio/editorial-policies/ai and
  https://www.nature.com/nature/editorial-policies/ai both 303-redirect to `idp.nature.com`. Every
  nature.com article URL I tried did the same (see §4).
- What I have is **snippet only**, from search results, and it is broadly consistent with the Springer Nature
  page [P4] above, which I *did* open — reviewers may use secure/institutionally-approved tools but must not
  upload manuscripts to unsecured or public AI, and AI cannot replace reviewer judgement. **Use [P4] as the
  citable source; do not quote Nature's own page until it is opened.**
- Two 2026 Nature-portfolio pieces identified but not opened (all 303 to IdP):
  - "AI in peer review: the elephant in the editorial room", *Evidence-Based Dentistry*, s41432-026-01227-x
  - "Peer review in the time of artificial intelligence", *Nature Nanotechnology*, s41565-026-02177-2
  - "First AI tool to detect suspicious peer reviews rolled out by academic publisher", Nature news, d41586-026-01454-3

---

### 1e. Conferences

---

**[C1] AAAI-26 — "AI-Assisted Peer Review at Scale: The AAAI-26 AI Review Pilot"**
- Date: **2026-04-15** (arXiv 2604.13940)
- Authors: Joydeep Biswas, Sheila Schoepp, Gautham Vasan, Anthony Opipari, Arthur Zhang, Zichao Hu,
  Sebastian Joseph, Matthew Lease, Junyi Jessy Li, Peter Stone, Kiri L. Wagstaff, Matthew E. Taylor,
  Odest Chadwicke Jenkins
- URLs: https://arxiv.org/abs/2604.13940 (opened) and https://arxiv.org/html/2604.13940v1 (opened)
- Mechanism: **multi-stage pipeline with self-critique, a "peer review of peer reviews" quality check, and a
  sampled citation-existence audit via the GPTZero API.** This is the largest deployed instance of
  AI-checking-AI in 2026 scholarly publishing.

From the abstract:
> "every main-track submission at AAAI-26 received one clearly identified AI review from a state-of-the-art
> system. The system combined frontier models, tool use, and safeguards in a multi-stage process to generate
> reviews for all 22,977 full-review papers in less than a day."

> "participants not only found AI reviews useful, but actually preferred them to human reviews on key
> dimensions such as technical accuracy and research suggestions"

The concrete verification step, from the full text:
> "We implemented a quality-checking workflow to identify potential issues in the generated reviews, similar
> to previous work on 'peer reviews of peer reviews.'"

> "We randomly sampled 100 reviews generated by the AAAI-26 AI review system and checked for hallucinated
> citations using the GPTZero API. There were 1356 citations in the sampled reviews. GPTZero identified 1346
> of the citations as valid."

The quality check screened for: "(1) revealing author identities; (2) potentially offensive language or
content in the review; (3) judgments that may have been biased based on gender, geography, or other factors;
and (4) missing structural elements." Survey responses: 5,834 total — authors 3,075, program committee 2,184,
senior program committee 550, area chairs 25. The extraction pass reported no AI reviews were recorded as
rejected or filtered from the final deployment.

> **Note the scale of the audit:** 100 reviews sampled out of 22,977 generated; 1,346 of 1,356 citations
> judged valid (i.e. 10 were not). That is a ~0.4% sample. The paper's own phrasing does not present it as a
> population estimate and neither should anyone citing it.

---

**[C2] NeurIPS 2026 — "AI-Generated Papers in the NeurIPS 2026 Position Paper Track"**
- Date: **2026-06-02**
- URL: https://blog.neurips.cc/2026/06/02/ai-generated-papers-in-the-neurips-2026-position-paper-track/
- Status: **opened**
- Mechanism: **detector-triggered desk rejection with a documented-provenance appeal** — authors can rebut a
  flag by showing version history, i.e. proving process rather than arguing about the text.

> "state how AI tools were used in the preparation of the paper, if at all, and to attest that they have not
> used AI in ways contrary to the above rule"

> "a link to an online version of their paper that has a version history"

Reviewers must commit to "not using AI tools to write their reviews." Papers must be "substantially written
by human authors, meaning that AI is used only for copy-editing or similar peripheral changes to the main
text."

Numbers, each as returned: "178 submissions (18.4% of all submissions) will be desk rejected"; "123
submissions (12.7%) will be requested to provide evidence of substantial human engagement"; "28.2% (273 /
969) of submissions substantially used AI for writing"; "70.5%" of 2026 PPT submissions scored ≥50% on
Pangram; "42.7%" scored ≥90%; "28.2%" received 100% Pangram scores. Thresholds: automatic desk rejection at
≥0.9; conditional rejection in the 0.8–0.9 band, with an appeal deadline of "June 15th, 2026".

> The provenance-appeal design is the transferable idea for the scenario: when the artifact cannot be
> verified from its content alone, verify the *process* that produced it.

---

## 2. Pre-2026 background (kept short)

- **Pangram Labs, "Pangram Predicts 21% of ICLR Reviews are AI-Generated"** — **2025-11-18**, opened,
  https://www.pangram.com/blog/pangram-predicts-21-of-iclr-reviews-are-ai-generated. Despite concerning
  ICLR **2026**, the analysis is dated 2025. Verbatim: "We found 21%, or 15,899 reviews, were _fully
  AI-generated_."; "We found over half of the reviews had some form of AI involvement, either AI editing,
  assistance, or full AI-generation."; "Paper submissions, on the other hand, are still mostly human-written
  (61% were mostly human-written)."; "9% of submissions had over 50% AI content"; "Pangram's overall false
  positive rate is 1 in 10,000 on test set documents."; "Pangram's false positive rate on held-out scientific
  papers from ArXiV is 1 in 100,000." The widely-cited denominators 75,800 and 76,139, and the 86.2%
  agreement with author accusations, came from **search snippets only** and are not in what I opened.
  Pangram sells detection tools — a stated commercial interest.
- **GPTZero, "GPTZero uncovers 50+ Hallucinations in ICLR 2026"** — **2025-12-05**, opened,
  https://gptzero.me/news/iclr-2026/. "GPTZero used our Hallucination Check tool to scan 300 papers under
  review by the prestigious International Conference on Learning Representations (ICLR). We discovered that
  50 submissions included at least one obvious hallucitation, which were not previously reported."; "each of
  these submissions has already been reviewed by 3-5 peer experts, most of whom missed the fake citation(s)".
  Method: "our AI agent, trained in-house, to flag any citations in a document that can't be found online",
  with a human making the final call on whether a flawed citation is AI-generated.
- **PRISMA-trAIce** (Transparent Reporting of AI in Comprehensive Evidence Synthesis) — *JMIR AI*,
  **2025-12-10**, DOI 10.2196/80247, opened at https://pmc.ncbi.nlm.nih.gov/articles/PMC12694947/. Item M8
  asks "What proportion of AI outputs were manually reviewed/verified?", "Did reviewers work independently
  when validating AI outputs?", and "How were discrepancies between AI and human reviewers, or among multiple
  human reviewers, resolved?"; M9 requires "The metrics used (eg, accuracy, sensitivity, specificity,
  precision, recall, F1-score)". The paper states it "has not yet been published" as a formal consensus
  guideline. **Closest existing checklist to the scenario — but 2025, not 2026.**
- **Cochrane / Campbell / JBI / CEE joint position statement on AI in evidence synthesis** — **2025**,
  Cochrane Database Syst Rev ED000178. Endorses the RAISE recommendations; requires human oversight and holds
  synthesists responsible. See §3 for the 2026 search outcome.
- **Agents4Science** (Stanford + Together AI) — first edition held **2025-10-22**; analysis paper arXiv
  2511.15534, **November 2025**. AI-authored and AI-reviewed, with 79 top-scoring papers additionally
  assessed by a human expert.
- **OpenAI "confessions"** — arXiv 2512.08093 / https://openai.com/index/how-confessions-can-keep-language-models-honest/,
  **December 2025**. A second output judged only on honesty, not on task performance. No 2026 follow-up found
  (§3).
- **AstaBench paper** — arXiv 2510.21652, **2025**; ICLR 2026 camera-ready. The 2026 item is the update blog [T2].
- **Elicit "How we evaluated Elicit Systematic Review"** — **2025-03-18**, opened,
  https://elicit.com/blog/how-we-evaluated-elicit-systematic-review. Superseded by [T1]; retained because it
  carries the LLM-judge validation figure: "verifying extractions with LLMs has 89% agreement with manual
  verification".

---

## 3. Targets with nothing found for 2026

- **METR — a report measuring human verification time.** **None found for 2026.** Two 2026 METR artifacts
  were opened ([L7], [L8]); both measure time savings and neither decomposes review or verification time.
- **UK AI Security Institute — 2026 debate / scalable-oversight results.** **None found for 2026.** The AISI
  research listing page was opened; its seven 2026 entries (Jun–Aug 2026) cover preferences, optimal
  stopping, item response theory, multi-agent control, lie detection, prefill awareness, and AI-identity
  disclosure. Nothing on debate or scalable oversight. [L9] is a Geoffrey Irving co-authored 2026 honesty
  paper and is the nearest hit. Prover-estimator debate (Brown-Cohen, Irving, Piliouras) is **2025**.
- **OpenAI — a 2026 post specifically on Deep Research citation accuracy.** **None found for 2026 as a
  primary.** openai.com/index/introducing-deep-research/ returned HTTP 403 on fetch. Search snippets describe
  a **2026-02-10** update adding MCP connections and the ability to "restrict web searches to trusted sites",
  which is a scoping control rather than a verification mechanism. **Snippet only; unverified.**
- **OpenAI — Prover-Verifier Games 2026 follow-up.** **None found for 2026.**
- **OpenAI — a 2026 "confessions" follow-up.** **None found for 2026.** The confessions work is December 2025.
- **OpenAI — 2026 chain-of-thought monitorability post.** openai.com/index/evaluating-chain-of-thought-monitorability/
  returned HTTP 403; **date unconfirmed**, so it is not claimed as a 2026 item.
- **Cochrane — 2026 AI guidance.** **None found for 2026 on the primary.** methods.cochrane.org/ai/resources
  was opened and contains no dated 2026 resource. A search snippet referred to "New guidance released in
  March 2026"; **unverified — do not cite.** The citable position statement is 2025.
- **COPE — 2026 guidance.** **None found for 2026** as a primary COPE document.
- **Consensus, Scite, Undermind, Semantic Scholar — 2026 posts on how they verify extractions/citations.**
  **None found for 2026 as primaries.** All hits were third-party tool reviews and comparison blogs. Scite's
  claim of classifying "1.2B+ individual citation statements as supporting, contradicting, or mentioning" is
  **snippet only, from a comparison blog**, not from Scite.
- **FutureHouse — a 2026 post on verification.** **None found for 2026.** PaperQA2/WikiCrow are 2024;
  Robin and ether0 are 2025; Kosmos is November 2025 (Edison Scientific spinout). Only the undated docs
  page [T3] was opened.
- **PRISMA-AI 2026 reporting guideline.** **None found for 2026.** PRISMA-AI is the older AI-as-subject
  extension; PRISMA-trAIce is December 2025; L-PRISMA [R3] is January 2026 but is an individual proposal,
  not a consensus guideline. A "PRISMA 2026" checklist update was described in a **snippet only** (casrai.org)
  as finalized end-2025 with fields for AI-assisted screening; **unverified — do not cite.**
- **ICLR 2026 — an official conference statement with AI-review statistics.** **None found as an ICLR
  primary.** The statistics circulating come from Pangram (2025-11-18) and GPTZero (2025-12-05), both
  vendors, and from Nature news coverage.
- **Agents4Science 2026 edition.** **None found for 2026.**
- **Science / AAAS — a 2026 policy document.** **None found as a primary.** The only sourced 2026 datum is
  from the opened STAT article: Science journals employ "an automated tool to check references".

---

## 4. URLs opened vs snippet-only

### Opened with WebFetch (primary or named secondary)

| # | URL | Result |
|---|-----|--------|
| 1 | https://www.anthropic.com/news/claude-science-ai-workbench | OK (×2) |
| 2 | https://www.anthropic.com/news/expanding-support-for-scientists | OK |
| 3 | https://pmc.ncbi.nlm.nih.gov/articles/PMC13216060/ | OK (Nature/OpenAI hallucination paper) |
| 4 | https://forum.openai.com/public/blogs/terence-tao-…-2026-03-10 | OK |
| 5 | https://deepmind.google/blog/co-scientist-a-multi-agent-ai-partner-to-accelerate-research/ | OK |
| 6 | https://deepmind.google/public-policy/conjecture-machines-ai-agents-and-the-new-validation-bottleneck-in-science/ | OK |
| 7 | https://metr.org/notes/2026-02-17-exploratory-transcript-analysis-…/ | OK |
| 8 | https://metr.org/blog/2026-05-11-ai-usage-survey/ | OK |
| 9 | https://www.aisi.gov.uk/research | OK (listing) |
| 10 | https://www.aisi.gov.uk/research/did-you-lie-…-model-organisms | OK |
| 11 | https://elicit.com/blog/evaluating-elicit-slr | OK |
| 12 | https://elicit.com/blog/how-we-evaluated-elicit-systematic-review | OK (2025) |
| 13 | https://allenai.org/blog/astabench-update-spring-2026 | OK |
| 14 | https://docs.edisonscientific.com/agents | OK (undated) |
| 15 | https://arxiv.org/abs/2604.03173 | OK |
| 16 | https://arxiv.org/abs/2607.22693 | OK |
| 17 | https://arxiv.org/abs/2603.19236 | OK (L-PRISMA) |
| 18 | https://arxiv.org/abs/2604.13940 | OK |
| 19 | https://arxiv.org/html/2604.13940v1 | OK (safeguards detail) |
| 20 | https://blog.neurips.cc/2026/06/02/ai-generated-papers-…/ | OK |
| 21 | https://www.pangram.com/blog/pangram-predicts-21-of-iclr-reviews-are-ai-generated | OK (2025) |
| 22 | https://gptzero.me/news/iclr-2026/ | OK (2025) |
| 23 | https://pmc.ncbi.nlm.nih.gov/articles/PMC12694947/ | OK (PRISMA-trAIce, 2025) |
| 24 | https://group.springernature.com/gp/group/media/press-releases/…/27849346 | OK |
| 25 | https://group.springernature.com/gp/group/ai/ai-guidance-for-our-researchers-and-communities | OK |
| 26 | https://www.icmje.org/news-and-editorials/ | OK |
| 27 | https://www.icmje.org/recommendations/browse/roles-and-responsibilities/defining-the-role-of-authors-and-contributors.html | OK |
| 28 | https://methods.cochrane.org/ai/resources | OK (no 2026 content) |
| 29 | https://retractionwatch.com/2026/05/07/…/ | OK (secondary) |
| 30 | https://www.the-scientist.com/one-in-277-biomedical-papers-carry-fake-references-74480 | OK (secondary) |
| 31 | https://www.statnews.com/2026/05/07/lancet-study-finds-steep-rise-fraudulent-citations-academic-papers/ | OK (secondary) |

### Attempted and FAILED (so: snippet only)

| URL | Failure |
|-----|---------|
| https://www.thelancet.com/…/PIIS0140-6736(26)00603-3/fulltext | HTTP 403 |
| https://www.thelancet.com/…/PIIS0140-6736(26)00798-1/abstract | HTTP 403 |
| https://openai.com/index/evaluating-chain-of-thought-monitorability/ | HTTP 403 |
| https://openai.com/index/introducing-deep-research/ | HTTP 403 |
| https://www.nature.com/articles/s41586-026-10549-w | 303 → idp.nature.com (used PMC instead) |
| https://www.nature.com/articles/s41565-026-02177-2 | 303 → idp.nature.com |
| https://www.nature.com/articles/s41432-026-01227-x | 303 → idp.nature.com |
| https://www.nature.com/articles/d41586-026-01454-3 | 303 → idp.nature.com |
| https://www.nature.com/nature-portfolio/editorial-policies/ai | 303 → idp.nature.com |
| https://pubmed.ncbi.nlm.nih.gov/… (2 attempts) | cookie wall |

### Snippet-only claims flagged in the body — none of these should be quoted without opening the primary

- DeepMind Co-Scientist: "separate verification module cross-checks every numerical claim against the actual
  results of the executed code"; "fabrication rates of 80 to 100 percent in existing systems" (the-decoder.com)
- Tao: Lean "verifies the formal statement itself, not whether this statement matches the intended meaning"
  (secondary aggregators)
- Kosmos: 79.4% claim accuracy; 80% reproducibility
- Lancet editorial [P2]: the 91% figure; "routine automated verification can close this gap"
- Cochrane "new guidance released in March 2026"
- "PRISMA 2026" checklist update with AI-assisted-screening fields (casrai.org)
- Pangram ICLR denominators 75,800 / 76,139; the 86.2% agreement with author accusations
- Nature Portfolio AI policy wording (use the Springer Nature page [P4], which was opened)
- Scite's "1.2B+ individual citation statements"
- OpenAI Deep Research 2026-02-10 update text

### Budget note

The WebSearch budget for this session (200 calls) was exhausted before the Nature-portfolio editorials and a
few publisher primaries could be chased through alternative routes. Highest-value unfinished work, in order:
(1) open the Lancet primary to settle 4,046 vs 4,406 and 125.6M vs 97.1M; (2) open the Nature Portfolio AI
policy and the two 2026 Nature-portfolio peer-review editorials via an institutional proxy; (3) confirm
whether Cochrane published March 2026 AI guidance.

---

## 5. What the 2026 record actually supports, for the scenario

Reading only the items dated 2026 and opened:

1. **A separate checking agent is now the standard architecture, at Anthropic and DeepMind alike** — Claude
   Science's reviewer agent [L1] and Co-Scientist's Reflection agent plus verification-dominant compute
   budget [L5]. Neither publishes a measured catch rate for it.
2. **The only published recall numbers for literature extraction come from a vendor** — Elicit [T1], against
   994 Cochrane reviews. 95.0% search recall is the number that bears directly on "find *every* claim", and
   it is self-reported.
3. **Citation existence checking is cheap, effective and now measured** — 3–13% of agent citation URLs are
   hallucinated, and tool-equipped self-correction cuts non-resolving URLs to under 1% [R1]. But existence
   checking does not establish that the source supports the claim, and the deployed tools that try are
   unreliable [R2].
4. **Institutions have converged on process evidence over content inspection** — reproducibility bundles
   [L1], version-history appeals [C2], traceability to source passages [T3], Human-AI Interaction Cards [L6],
   and PRISMA-trAIce's "what proportion of AI outputs were manually reviewed?" (2025).
5. **The base rate of the failure is now documented at scale and rising fast** — 1 in 2,828 papers (2023) →
   1 in 458 (2025) → 1 in 277 (first seven weeks of 2026) [P1].
