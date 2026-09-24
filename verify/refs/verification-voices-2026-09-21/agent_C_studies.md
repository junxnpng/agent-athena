# Agent C — 2026 empirical studies on AI literature-review / synthesis / citation errors and verification

(The agent could not write files; this is its final message saved verbatim by Fable on 2026-09-21. HTML entities unescaped.)

## 10-line summary — strongest 5 findings

1. **Omission dominates, not fabrication.** SciLitBench (arXiv 2609.05505, 2026-08-29): strongest models "recover only 30% of annotated evaluation evidence and 25% of limitations." Oami et al. (Front. Digit. Health, 2026-04-29): Missing Data = **67–93% of all errors**, fabricated data only **0.7–14%**.
2. **Citations that resolve still don't support the claim.** "Cited but Not Verified" (2605.06635, 2026-05-07): link validity **>94%**, relevance **>80%**, but **factual accuracy 39–77%** — and a **~42% drop** when tool calls scale 2 → 150.
3. **Rewriting inflates certainty, and it compounds.** "From 'May' to 'Is'" (2606.07951, 2026-06-06): distortion in **up to 75%** of outputs, increases 1.5–2x more often than decreases; claude-haiku-4.5 medical **20% → 40% from 1 to 5 iterations**.
4. **Tuple extraction collapses.** "Diagnosing Structural Failures" (2602.10881, IRCDL 2026): "full meta-analytic association tuples extracted with **near-zero reliability**"; named modes = role reversal, cross-analysis binding drift, **numeric misattribution**.
5. **Re-running ≠ verifying; verifier choice sets the answer.** 2607.20527: unsupported-citation rate reads **3% → 18% on identical outputs** by verifier strictness, verifier-to-verifier negative agreement **0.27–0.30**. 2608.26885: two identical GPT-5.4 runs disagreed on 94/1,131 records (29 eligible). What works: deterministic tools (6–79x, +8.0pp, +12.0%) and humans as adjudicators (**60.8% → 90.9%**, DeepFact).

---

## 0. Fidelity caveat — read before quoting

I reached every primary page via `WebFetch`, which **runs a summarizing model over the page and returns its extraction**. Strings in quotes below are what that extraction returned as verbatim; almost certainly faithful, but I did not see raw page bytes and cannot guarantee character-level fidelity.

**One exception:** arXiv 2605.07723 was fetched as PDF and I read the rendered page images. Its abstract is verbatim at full fidelity — the only quote here I stake that claim on.

`snippet only` = from a WebSearch blurb, **not opened**. Do not quote those. **Do not merge numbers across sources** — §1.A documents a live discrepancy.

---

## 1. Studies by error type

### 1.A — Fabricated citations: prevalence in the published record

**A1. Topaz M, Roguin N, Gupta P, Zhang Z, Peltonen LM. "Fabricated citations: an audit across 2·5 million biomedical papers." *The Lancet* 2026 May 9; 407(10541):1779–1781. DOI 10.1016/S0140-6736(26)00603-3**
- **NOT opened** (thelancet.com → HTTP 403). Author list/DOI = `snippet only`. Numbers below from four **opened** secondaries: EurekAlert/Columbia Nursing, Retraction Watch (2026-05-07), CIDRAP, STAT (2026-05-07).
- Corpus: PMC Open Access subset, 2023-01-01 → 2026-02-18. CIDRAP (opened): "Scanned PubMed Central's Open Access subset from January 2023 to February 2026 to audit 2.5 million research papers and 126 million structured references". `snippet only`: "2,471,758 papers and 125,615,773 structured references… 97.1 million (77%) carried a PubMed identifier and were verified."
- **Rates (consistent across all four opened secondaries):** 2023 **1 in 2,828** papers → end-2025 **1 in 458** → first 7 weeks of 2026 **1 in 277**. STAT: "During the first seven weeks of 2026, the rate reached 1 in 277 papers". Per-10,000 framing, CIDRAP: "Four per 10,000 papers in 2023, to 51.3 per 10,000 at the end of 2025 and 56.9 per 10,000 in the early part of this year". EurekAlert gives "approximately 57 per 10,000 by early 2026" (rounding, not conflict).
- **⚠ NUMERIC DISCREPANCY — do not average, do not silently pick one:**

| Source (all opened) | fabricated refs | affected papers |
|---|---|---|
| EurekAlert / Columbia | "4,046 fake citations across 2,810 papers" | 2,810 |
| Retraction Watch | "4,406 across 2,810 papers" | 2,810 |
| CIDRAP | "4,046 were likely fake" | "2,564 papers affected" |
| STAT | "around 4,000 fabricated citations among 2,800 papers" | ~2,800 |

  4,046 has 2 attestations, 4,406 has 1 (likely transposition); 2,810 has 2, 2,564 has 1. **Resolve against the Lancet PDF before publishing.**
- Concentration — Retraction Watch: **91%** of affected papers had 1–2 fake refs; one publisher "produced fabrications at more than fourteen times the rate of the most selective journals"; review articles **57% higher** rate (CIDRAP: "16.7 vs 10.6 per 10,000 papers").
- EurekAlert: "at the time of the audit, **98.4%** of affected papers had not received any publisher action"; "one paper we reviewed had **18 out of 30** fake references".
- **Verification method** (CIDRAP): AI-built automated reference verification — retrieve bibliographic records, compare metadata by "text-similarity scoring," sequential false-positive filters, verify against multiple databases. **Reported precision: 91%.** Retraction Watch adds AI was used to "distinguish genuine fabrications from formatting discrepancies such as informally abbreviated titles."
- Topaz (Retraction Watch): "For papers with one or two fabricated references that are incidental to the main findings, correction and transparency may be more proportionate than retraction."

**A2. Zhao, Wang, Stuart, De Vaan, Ginsparg, Yin — "LLM hallucinations in the wild: Large-scale evidence from non-existent citations." arXiv 2605.07723, v1 2026-05-08** (Cornell/UCLA/Tsinghua/Berkeley Haas). **Opened — PDF read directly.**

> **VERBATIM ABSTRACT (full fidelity):** "Large language models (LLMs) are known to generate plausible but false information across a wide range of contexts, yet the real-world magnitude and consequences of this hallucination problem remain poorly understood. Here we leverage a uniquely verifiable object — scientific citations — to audit 111 million references across 2.5 million papers in arXiv, bioRxiv, SSRN, and PubMed Central. We find a sharp rise in non-existent references following widespread LLM adoption, with a conservative estimate of 146,932 hallucinated citations in 2025 alone. These errors are diffusely embedded across many papers but especially pronounced in fields with rapid AI uptake, in manuscripts with linguistic signatures of AI-assisted writing, and among small and early-career author teams. At the same time, hallucinated references disproportionately assign credit to already prominent and male scholars, suggesting that LLM-generated errors may reinforce existing inequities in scientific recognition. Preprint moderation and journal publication processes capture only a fraction of these errors, suggesting that the spread of hallucinated content has outpaced existing safeguards. Together, these findings demonstrate that LLM hallucinations are infiltrating knowledge production at scale, threatening both the reliability and equity of future scientific discovery as human and AI systems draw on the existing literature."

- **⚠ CORRECTION TO THE TASK BRIEF:** "~111 million references from ~2.5 million papers" is **this arXiv paper**, not The Lancet's. Different corpora, different authors, dates one day apart. The Lancet: ~126M structured refs, 97.1M verified, ~2.47M PMC-OA papers. **Do not conflate.**
- Intro (p.2, read directly): citations are the right probe because "A cited reference exists or it does not"; alternatives rejected as human evaluation "costly to scale" or "automated LLM-based pipelines that might reintroduce model-specific biases into the analysis"; estimate is a floor — "the prevalence we measure here likely understates what is occurring in less structured knowledge domains."

**A3. Ansari, S. — "Compound Deception in Elite Peer Review: A Failure Mode Taxonomy of 100 Fabricated Citations at NeurIPS 2025." arXiv 2602.05930, v1 2026-02-05.** Single author. **Opened.**
- Primary-mode taxonomy: Total Fabrication **66%**, Partial Attribute Corruption **27%**, Identifier Hijacking **4%**, Placeholder Hallucination **2%**, Semantic Hallucination **1%**.
- Quoted: "every hallucination (100%) exhibited compound failure modes. The distribution of secondary characteristics was dominated by Semantic Hallucination (63%) and Identifier Hijacking (29%), which often appeared alongside Total Fabrication to create a veneer of plausibility and false verifiability. These compound structures exploit multiple verification heuristics simultaneously, explaining why peer review fails to detect them."
- Quoted: "appearing in 53 published papers (approx. 1% of all accepted papers)" despite "review by 3-5 expert researchers per paper"; "92% of contaminated papers contain 1-2 hallucinations (minimal AI use) while 8% contain 4-13 hallucinations (heavy reliance)."
- Proposes "mandatory automated citation verification at submission." Analysis of GPTZero's finds, not an independent detector.

**A4. GPTZero — NeurIPS 2025 audit, announced 2026-01-21.** https://gptzero.me/news/neurips/ **Opened.**
- Quoted: "scanning 4841 papers accepted by the equally prestigious Conference on Neural Information Processing Systems (NeurIPS), we discovered 100s of hallucinated citations"; "Below, we uncover 100 confirmed hallucinations in the table below, spanning over 51 NeurIPS papers."
- **⚠ 51 vs 53:** GPTZero's page says **51**; Ansari says **53**. Record both.
- Taxonomy: author fabrication (e.g. "John Doe and Jane Smith"); title/metadata mixing; publication falsification (fake DOIs, URLs, volumes).
- Method: AI agent flags unavailable citations → **human expert verification of every flagged item**. Self-reported "99% catch rate" with higher false positives. Coined "vibe citing."

**A5. Russinovich, Siva Kumar, Salem — "Phantom References: Hallucinated Citations That Survive Peer Review at Top-Tier Conferences." arXiv 2607.00738, v1 2026-07-01** (Microsoft). **Opened.**
- Deliberately conservative definition, quoted: "a conservative definition limited to identity-level failures: non-existent works and substantial author-list mismatches."
- Quoted: "roughly one in twenty NeurIPS and USENIX Security papers contains at least two likely hallucinated academic-paper-like references." Reference-level rates "usually below 1%." Venues: ICLR, ICML, NeurIPS, USENIX Security. Papers with 5+ hallucinated citations found, "including award-winning papers."
- `RefChecker`: bibliographic resolution + web-search escalation, **~$0.04/paper**, open-sourced.
- A `snippet only` claim of "20% of sampled ICLR 2026 submissions contained at least one AI hallucination" — **unverified, do not cite.**

**A6. Bienz, Pearson, Garcia de Gonzalo — "The Case of the Mysterious Citations." arXiv 2602.05867, v1 2026-02-05.** **Opened.**
> Abstract (as returned): "Mysterious citations are routinely appearing in peer-reviewed publications throughout the scientific community. In this paper, we developed an automated pipeline and examine the proceedings of four major high-performance computing conferences, comparing the accuracy of citations between the 2021 and 2025 proceedings. While none of the 2021 papers contained mysterious citations, every 2025 proceeding did, impacting 2-6% of published papers. In addition, we observe a sharp rise in paper title and authorship errors, motivating the need for stronger citation-verification practice."
- **The only 2026 prevalence study I found sampling HPC venues** rather than biomed/ML. Clean 2021 zero baseline → **2–6%** of 2025 papers. Error types: mysterious citations, title errors, authorship errors.

**A7. Xu, Z. et al. (17 authors) — "GhostCite: A Large-Scale Analysis of Citation Validity in the Age of Large Language Models." arXiv 2602.06718, v1 2026-02-06.** **Opened (abs + HTML v2).**
> Abstract (as returned, full): "Citations provide the basis for trusting scientific claims; when they are invalid or fabricated, this trust collapses. With the advent of Large Language Models (LLMs), this risk has intensified: LLMs are increasingly used for academic writing, but their tendency to fabricate citations ("ghost citations") poses a systemic threat to citation validity. To quantify this threat, we develop CiteVerifier, an open-source framework for large-scale citation verification, and conduct a comprehensive study of citation validity in the LLM era through three complementary experiments. First, we benchmark 13 LLMs on citation generation task in various research domains, finding that all models hallucinate citations at rate from 14.23% to 94.93%. Second, we analyze 2.2 million citations from 56,381 papers at AI/ML and Security venues (2020–2025), finding that 1.07% of papers contain invalid citations, with an 80.9% increase in 2025. Third, we survey 97 researchers, finding that 87.2% use AI-powered tools in their workflows, 76.7% of reviewers do not thoroughly check references, and 74.5% view peer review as ineffective at catching citation errors."
- 13 models quoted: "GPT-5, Claude-Sonnet-4, Gemini-2.5-Pro, Grok-4-Fast, Llama-4-Maverick, Phi-4, GLM-4.5, Hunyuan-A13B-Instruct, UI-TARS-1.5-7B, Qwen3-Max, DeepSeek-Chat-V3.1, ERNIE-4.5-21B-A3B, Kimi-K2-0905". The 80.9% increase is "from 2020–2024 baseline of 0.89% to 1.61%."
- `CiteVerifier`: GROBID → Qwen3-Flash reparser on failure → cascaded cache → DBLP+Google Scholar → web search → LLM reparse; title similarity, Levenshtein, "empirical calibrated threshold θ=0.9". Validated by 16 trained assistants over one month + 400-citation sample: "Valid accuracy was 100%, and invalid accuracy was 98% (392/400)."
- **⚠** The JCOM editorial's "between 14% and 92% of 375,440 AI-generated citations were fabricated" is a second-hand restatement of this. GhostCite's own range is **14.23%–94.93%**; the 375,440 count is not in its abstract. **Cite GhostCite, not JCOM.**

### 1.B — Fabrication/breakage rates *generated by* models and agents

**B1. Rao, Wong, Callison-Burch — "Detecting and Correcting Reference Hallucinations in Commercial LLMs and Deep Research Agents." arXiv 2604.03173, v1 2026-04-03** (UPenn). **Opened.**
- 10 models/agents; DRBench (**53,090 URLs**) + ExpertQA (**168,021 URLs**).
- "3–13% of citations reference URLs that never existed" (Wayback absence); "5–18% of citations are non-resolving overall." Domain spread **5.4% (Business) → 11.4% (Theology)**.
- **Key structural finding:** "Deep research agents produce more citations but hallucinate at higher rates than search-augmented LLMs."
- Taxonomy: complete fabrication vs link-rot, separated via Wayback presence.
- `urlhealth` (open source): self-correction "reduced problematic citations by 6–79 times, achieving sub-1% error rates."

**B2. Rao, Callison-Burch — "BibTeX Citation Errors in Scientific Publishing Agents: Evaluation and Mitigation." arXiv 2604.03159, v1 2026-04-03.** **Opened.**
- Taxonomy, quoted: "omission, partial corruption, substitution, and hallucination."
- 931 papers, 4 domains, ~23,000 field-level observations. Baseline **83.6%** field accuracy; **only 50.9% of entries fully correct**; **−27.7pp** from popular to recent papers.
- `clibib` two-stage (search separated from revision) → **91.5%** field accuracy (+8.0pp), **78.3%** fully correct; regression **0.8%** vs single-stage loop **4.8%**.

**B3. Chen, Quan, Lin, Tang — "Where Fake Citations Are Made: Tracing Field-Level Hallucination to Specific Neurons in LLMs." arXiv 2604.18880, v1 2026-04-20** (Rutgers). **Opened.**
- 9 models, **108,000** generated references. **Author names are the most frequent failure field across all models**; citation style had no measurable effect.
- Neuron-level CETT + elastic-net + stability selection on Qwen2.5-32B-Instruct → "FH-neurons"; suppression reduced, amplification increased field-level hallucination.

**B4. Gao, Zhang, Disis, Zhang et al. (~30 authors) — "Errors in AI-Assisted Retrieval of Medical Literature: A Comparative Study." arXiv 2603.22344, v1 2026-03-21.** **Opened.**
> Quoted: "We evaluated 2,000 references retrieved by 5 LLMs (Grok-2, ChatGPT GPT-4.1, Google Gemini Flash 2.5, Perplexity AI, and DeepSeek GPT-4) for 40 randomly-selected original articles (10 per journal) published Jan. 2024 to July 2025 from British Medical Journal (BMJ), Journal of the American Medical Association, and The New England Journal of Medicine (NEJM)."
- Overall **complete failure rate 47.8%**; Grok **0.57** (best) → Gemini **0.11** (worst); average score ratio **0.29** (range 0–1.25). Multimetric score = DOI + PubMed ID + Google Scholar link validity + relevance. **Free-version platforms only.**

### 1.C — Misattribution / faithfulness: real citation, unsupported claim

**C1. Onweller, Lumer, Huber, Ramchandani, Subbiah, Feld — "Cited but Not Verified: Parsing and Evaluating Source Attribution in LLM Deep Research Agents." arXiv 2605.06635, v1 2026-05-07** (PwC). **Opened.**
- **Most important number set for our scenario:** link validity **>94%**; relevance **>80%**; **factual accuracy 39–77%**. A citation that resolves and is on-topic still fails to support its claim a quarter to three-fifths of the time.
- **"Approximately 42% drop in factual accuracy when tool calls scale from 2 to 150."** More searching ≠ better grounding.
- Open-source models: "fewer than half generate cited reports successfully in one-shot setting."
- Method: AST parsing + three dimensions (Link Works / Relevant Content / Fact Check) with rubric-based LLM-as-a-judge "calibrated through human review." Framing: "a critical disconnect between surface-level citation quality and factual reliability."

**C2. Goo, Kim, Han, Jo, Kim, Kim — "Evaluating and Guarding Citation Faithfulness in Agentic Scientific Synthesis." arXiv 2607.20527, v1 2026-07-10.** **Opened.**
- Targets exactly the tooling in our scenario: "Agentic LLM systems such as OpenScholar and PaperQA2 read the scientific literature and return cited answers."
- **Methodological bombshell:** unsupported-citation rates range **"from about 3% to about 18%" on identical outputs**, depending only on verifier strictness. Verifier-to-verifier negative-specific agreement **0.27–0.30**.
- Methods: (i) gold-anchored evaluation protocol calibrated against human annotation rather than model verdicts; (ii) **conformal guard** — "a split-conformal layer placing a distribution-free, finite-sample bound on truly unsupported citations." Their verifier: **recall 0.94 on supported class, held out**. Four 27–35B open models, three agentic pipelines, SciFact/QASA/PubMedQA. Stated limit: guarantee is on catch rates, not conclusion correctness.

**C3. Williams, R. — "Faithful by Design: Evaluating and Improving LLM-Generated Clinical Trial Summaries for Multi-Stakeholder Audiences." arXiv 2607.09932, v1 2026-07-10.** **Opened.**
- 200 stratified AACT trials, 3 audiences, **1,800 summaries**, GPT-4o / Claude Sonnet 4.6 / Gemini 2.5 Flash, six-dimension faithfulness schema, cross-encoder NLI.
- Quoted: **"Unsupported Claims was identified as the dominant failure mode across all three models, with a mean annotation score of 1.55 out of three."**
- KG-augmented retrieval: entailment **+0.0125**, faithfulness **+0.0130** (p<0.0001) — significant but practically tiny. Evidence that RAG-style patches do **not** close this gap.

**C4. Miyai, Toyooka, Zhao, Watanabe, Yamasaki, Aizawa — "Paper Reconstruction Evaluation: Evaluating Presentation and Hallucination in AI-written Papers." arXiv 2604.01128, v1 2026-04-01** (UTokyo). **Opened.**
- PaperRecon: overview from a real paper → agent writes full paper → compare to original. Two **orthogonal** axes: Presentation (rubric), Hallucination ("agentic evaluation grounded in the original paper source"). PaperWrite-Bench: **51 papers** from top venues, all post-2025 (contamination control).
- Quoted: "ClaudeCode achieves higher presentation quality at the cost of **more than 10 hallucinations per paper on average**, whereas Codex produces fewer hallucinations but lower presentation quality."
- **Directly applicable:** presentation quality and factual fidelity trade off. A well-organized synthesis is not evidence of an accurate one.

### 1.D — Omission / recall

**D1. "Performance of large language models in data extraction for evidence synthesis: A systematic review." *J Biomed Inform*, 2026-07-25.** PII S1532046426001103; PubMed 42501879.
- **NOT opened** (ScienceDirect 403, PubMed cookie wall, EuropePMC 403). All figures `snippet only`, from two independent search result sets.
- `snippet only`: **"Omissions were the dominant error type (60–74%), with hallucination rates of only 0.08–6%."** Also: overall accuracy **47–99.9%**; categorical/string **74–96%** vs numerical **47–88%**; **27 studies** (GPT-4/4o n=15, Claude 2–3.5 n=10, Gemini n=3); Claude 3.5 Sonnet assistive **91.0% (95% CI 90.4–91.6)** vs human-only **89.0%**; Claude>GPT **OR 1.70** for event counts; time savings **33–87%**; **74.1%** low risk of bias. Conclusion: assistive tools "within dual-extraction workflows requiring human verification."
- **⚠** Brief calls this "Shankar 2026." **No page I opened named the authors. Do not attribute to a named first author.**

**D2. Oami, Okada, Maeda, Nakada — "Performance of large language models and prompt engineering strategies for data extraction in systematic reviews." *Frontiers in Digital Health*, 2026-04-29, DOI 10.3389/fdgth.2026.1799623** (PubMed 42137114). **Opened.**
- **Cleanest independently-opened corroboration of omission-dominance.** Four-type taxonomy with shares: **Missing Data 67–93%**, Incorrect Data **14–51%**, Fabricated Data **0.7–14%**, Other.
- Per-model (background / outcome): ChatGPT-4o **81.6% / 64.4%**; Claude 3 Sonnet **92.4% / 80.7%**; Gemini 1.5 Pro **90.2% / 27.8%**.
- Inter-session consistency, same prompt × 3 sessions: background 76.3/89.6/91.3%; outcome **44.8**/65.6/56.9%. Non-determinism is a first-order error source.
- CoT and self-reflection gave "modest improvements." Verification: two independent human reviewers vs manual reference standard, third for disagreements.

**D3. Zabaleta, Lin — "SciLitBench: Benchmark and Design Principles for LLM-Powered Systematic Literature Reviews." arXiv 2609.05505, v1 2026-08-29.** **Opened.**
> Quoted: "Data extraction reveals a different reliability regime: performance declines from 0.97 accuracy for publication year to 0.37 Jaccard overlap for computational approach, while the strongest models recover only 30% of annotated evaluation evidence and 25% of limitations."
- 42,981 records, 1,012 full texts, 888 annotated papers, **22 open-weight LLMs across six families**. Explicit inclusion/exclusion criteria **+28.8% F₂** on title/abstract; researcher rationales **+15%** on full-text.
- Stated boundary: "a practical boundary between high-recall screening and evidence-complete extraction."
- **30% / 25% is the number to quote when asked "will it find every claim?"**

**D4. Xiong, Luo, Xia et al. (18 authors) — "AutoResearchBench: Benchmarking AI Agents on Complex Scientific Literature Discovery." arXiv 2604.25256, v1 2026-04-28** (BAAI/RUC). **Opened.**
- Quoted: "(1) Deep Research, which requires tracking down a specific target paper through a progressive, multi-step probing process, and (2) Wide Research, which requires comprehensively collecting a set of papers satisfying given conditions."
- Strongest LLMs: **9.39%** accuracy (Deep Research), **9.31% IoU** (Wide Research); many baselines below 5%. This bounds *finding* the corpus, not processing a supplied one.

**D5. Figalová, Huestegge, Böckler-Raettig — "Evaluating human and LLM screening workflows in a conceptually complex scoping review: Recall–workload trade-offs and run-to-run consistency." arXiv 2608.26885, v1 2026-08-27.** Preregistered. **Opened.**
- 1,131 records, 316 verified-eligible, 4 trained assistants on non-overlapping subsets, 7 complete LLM runs.
- Humans: recall **82.3–82.9%**, retaining 42.2–45.0%. Gemini 3.1: recall **83.9%**, retaining **56.7%** — matched human recall only by retaining far more, so workload savings were much smaller than headline claims.
- **"Two nominally identical GPT-5.4 runs agreed on 91.7% of records but disagreed on 94 records, including 29 verified eligible records."**

**D6. Shafqat, Patterson, Liss — "Knowledge Synthesis Review Framework: Task-Level Benchmarking of LLM-Based Systems for Multi-Source Evidence Synthesis." arXiv 2608.12741, v1 2026-08-13.** **Opened.**
- 244-document benchmark from a 1,893-document corpus, 4 source types; gold standard **92.2% agreement, kappa 0.80**. GPT-5, Claude Sonnet 4, Gemini 2.5 Pro, NotebookLM.
> Quoted: "No system led on all tasks. Claude Sonnet 4 achieved the highest screening accuracy (82.8%) and GPT-5 the highest recall (91.8%) at the expense of lower specificity. Extraction exceeded 90% agreement for titles and sources but degraded in author and reference fields. Performance declined most in interpretive analysis and cross-source synthesis, where expert judgment remained essential."
- **The gradient is the finding:** mechanical fields ≫ author/reference fields ≫ interpretive analysis ≫ cross-source synthesis. Our task sits at the worst end.

**D7. Lahlou, Gouttebroze, Oraee, Madera — "Writing literature reviews with AI: principles, hurdles and some lessons learned." arXiv 2603.20235, v1 2026-03-08** (LSE / Paris IAS). **Opened.** 31pp + 193pp appendices; qualitative, 6 review versions.
- **Number to quote:** "in our case there was only **20% overlap** between paper selections by humans and the LLM."
- Five pitfalls, quoted: "(1) The bias of ignorance (you do not know what you do not get) in the selection of relevant papers. (2) Alignment and digital sycophancy… (3) Mainstreaming… (4) Limited capacity for creative restructuring, with vague and ambiguous statements. (5) Lack of critical perspective, coming from distant reading and political correctness."
- Expertise paradox, quoted: "Most pitfalls can be addressed by prompting, but only if the user knows the domain well enough to detect them. There is a paradox: producing a good AI-assisted review requires expertise that comes from reading the literature, which is precisely what AI was meant to reduce."
- Also: "The same LLM, given the same corpus of 280 papers but different selections, produced dramatically different reviews, from mainstream and politically neutral to critical and post-colonial, though neither orientation was intended." And: "LLM outputs always appear at first glance to be well written, well informed and thought out, but closer reading reveals gaps, biases and lack of depth."
- **Caveat:** qualitative, n=6 versions, one corpus. A well-documented case study, not a rate estimate.

### 1.E — Over-generalization / dropped conditions / certainty distortion

2026 work reframes this as **epistemic faithfulness / certainty distortion**, which is why it doesn't surface under "generalization bias" searches.

**E1. Belem, Wu, Yao, Steyvers, Singh, Smyth — "From 'May' to 'Is': Certainty Distortion in Language Model Rewriting." arXiv 2606.07951, v1 2026-06-06** (UC Irvine). **Opened.**
- **Primary 2026 citation for this error class.** "certainty distortion affects **up to 75%** of LM outputs"; models increase certainty **1.5–2x more often** than decrease. Medical, claude-haiku-4.5: **20%** of single-iteration examples, **rising to 40% after five iterations**.
- **The compounding result is the actionable one** — iterative rewriting (exactly what multi-pass "read then reorganize" does) roughly doubles certainty inflation from one pass to five.
- Framing: authors use "hedges (e.g., may, could), non-factive verbs (e.g., suggest, appear), and source attribution (e.g., according to) to signal what is established versus what is tentative"; when modified, "readers may form beliefs or make decisions that go beyond what the evidence supports." They argue "epistemic faithfulness — preserving not just what is said, but the degree of certainty with which it is said — deserves attention alongside factuality."
- Method: LM-based metric aligned to human certainty judgments; prompt-based interventions tested (effectiveness not quantified in what I read).

**E2. Jang, Lee, Choi — "SciZoom: A Large-scale Benchmark for Hierarchical Scientific Summarization across the LLM Era." arXiv 2603.16131, v1 2026-03-17.** **Opened.**
- 44,946 papers (NeurIPS/ICLR/ICML/EMNLP, 2020–2025), stratified Pre-/Post-LLM around Nov-2022; compression up to 600:1.
- Corpus-level hedge stripping: **"23% decline in hedging"**; formulation shifts "up to 10x for certain expressions"; "more assertive yet uniform scientific discourse." A `snippet only` variant gives "22.8%… 1.88 to 1.45 occurrences per 1,000 words" — the **23%** is what I saw on the abstract page.
- **Caveat:** correlational corpus drift, not controlled measurement of a model dropping a qualifier.

**E3. Bakhshi, A.D. — "Saying More Than They Know: A Framework for Quantifying Epistemic-Rhetorical Miscalibration in Large Language Models." arXiv 2604.19768, v1 2026-03-27.** Single author. **Opened.**
- 225 argumentative texts, ~0.6M tokens. Metrics: Form-Meaning Divergence, Genuine-to-Performed Epistemic Ratio, Rhetorical Device Distribution Entropy.
- "systematic miscalibration with rhetorical intensity not proportionate to epistemic grounding"; tricolon ~2x expert rate (Δ=0.95); **"performed hesitancy markers appear at 2x human density in LLM output"**; FMD elevated (p<0.001, Δ=0.68).
- **Most useful insight:** LLMs emit *more* hedging-shaped language while being *less* epistemically grounded — surface hedges are not a reliable signal that conditions were preserved. Pairs with E1: hedges stripped where they matter, added where they don't.
- **Caveat:** rhetoric-focused, argumentative texts, single author, no venue. Suggestive only.

### 1.F — Wrong numbers / structural extraction failures

**F1. Tan, D'Souza — "Diagnosing Structural Failures in LLM-Based Evidence Extraction for Meta-Analysis." arXiv 2602.10881, v1 2026-02-11. Accepted at IRCDL 2026.** **Opened.**
- **Most relevant failure taxonomy in this report for our task:** role reversals; cross-analysis binding drift; instance compression in dense results sections; **numeric misattribution**.
- Moderate on single-property queries; "degrades sharply once tasks require stable binding between variables, roles, statistical methods, and effect sizes"; "full meta-analytic association tuples extracted with **near-zero reliability**." Long-context inputs make it worse.
- Method: "a structural, diagnostic framework that evaluates LLM-based evidence extraction as a progression of schema-constrained queries with increasing relational and numerical complexity." Two SOTA LLMs, single- and multi-document, curated corpus across five domains.

**F2. Yang, Zhu, Han, Han, Shen, Wang, Ioannidis, Rangwala — "When LLMs Read Tables Carelessly: Measuring and Reducing Data Referencing Errors." arXiv 2606.32029, v1 2026-06-30** (AWS). **Opened.**
> Abstract (as returned, full): "While large language models (LLMs) perform well on table tasks, they still make data referencing errors (DREs), i.e., incorrectly citing or omitting table values, despite understanding the table structure. Beyond final-answer accuracy, DREs directly compromise the correctness and reliability of intermediate reasoning steps. Yet prior studies have only offered limited, small-scale analyses. In this work, we present the first systematic evaluation of tabular data referencing errors across different models and tasks. Our results show that DREs occur across all tested models (1.7B to 20B parameters). Furthermore, we demonstrate that incorporating data referencing as a critic significantly improves answer accuracy up to 12.0%, through critic-based filtering and rejection sampling. Finally, we trained a lightweight 4B-parameter critic model that achieves an average F1 score of 78.2% in detecting both in-distribution and out-of-distribution DREs, and effectively assists inference for larger models."
- Note "incorrectly citing **or omitting** table values" — omission-dominance again, now at individual-number granularity. Model range 1.7B–20B excludes frontier models; extrapolate with care.

### 1.G — AI reviewers (same "read a paper, make claims about it" task shape)

**G1. Kim, Yoon, Gashteovski et al. (58 authors) — "On the limits and opportunities of AI reviewers: Reviewing the reviews of Nature-family papers with 45 expert scientists." arXiv 2605.20668, v1 2026-05-20.** **Opened.**
> Quoted: "45 domain scientists in Physical, Biological, and Health Sciences spent 469 hours rating 2,960 individual criticisms (each targeting one specific aspect of a paper) from human-written and AI-generated reviews of 82 Nature-family papers on correctness, significance, and sufficiency of evidence."
- GPT-5.2 **60.0%** vs top human reviewer **48.2%** (p = 0.009); AI-to-AI overlap **21%** vs human-to-human **3%**; AI surfaces **26%** of issues humans miss; **16** recurring AI weakness patterns.
- **Necessary counterweight:** AI critique is not uniformly worse than expert critique. But the 21% vs 3% overlap means **AI reviewers are highly correlated** — "ask a second model" recovers far less independent signal than asking a second human.
- Their framing: prior work focused on "whether their verdicts match human verdicts (e.g., score alignment, acceptance prediction), which is insufficient to characterize their capabilities and limits."

**G2. Nguyen, Hao, Elazar, Tan — "Benchmarking Agentic Review Systems." arXiv 2606.19749, v1 2026-06-18** (UChicago/AI2). **Opened.**
> Quoted: "Every system performs above chance in pairwise accuracy, and the best is OpenAIReview + GPT-5.5 at 83.0%… The strongest configuration (OpenAIReview + GPT-5.5) catches 71.6% of injected errors, leaving substantial room for improvement. The union of detections across six models reaches 83.3% recall, suggesting different models detect different errors and better harness design can potentially increase performance."
- **Reusable design:** injected-error perturbation benchmark — four error categories planted into papers across eight arXiv subject classes, measure detection recall against ground truth.
- Deployment: user votes skew positive **1.44 to 1**; "the most common complaints are about false positives and minor nitpicks."

**G3. Lin, Yao, Hsiao, Chen, Shuai — "HalluPeer: A Taxonomy-driven Benchmark for Detecting Hallucinations in Scientific Peer Reviews." arXiv 2609.03580, v1 2026-09-03.** **Opened.**
- 12,000 papers, 38,000 reviews; aligned triples (paper / human review / hallucination-injected review) annotated for **detection, classification, localization**.
- Key stated finding: "existing detectors struggle to separate hallucinations from legitimate critique." Specific F1 not on the abstract page.

**G4. Wang, Liu, Xu et al. — "When AI reviews science: Can we trust the referee?" arXiv 2604.23593, v1 2026-04-26.** **Opened.**
- "hidden prompt injections embedded in manuscripts can steer LLM-generated reviews toward unjustifiably positive judgments"; also adversarial phrasing, authority bias, length bias, fabricated claims. Treatment-control probes on ICLR 2025 submissions, two LLM referees.
- **No quantified error rates in what I opened** — cite for threat model, not rates.

**G5. La Rosa, Nasser — "AI in peer review: the elephant in the editorial room." *Evidence-Based Dentistry*, 2026-06-04, DOI 10.1038/s41432-026-01227-x** (PubMed 42243266).
- **NOT opened** (nature.com 303 → IdP auth). `snippet only`: Frontiers survey of "over 1,600 academics… across 111 countries found that **53%** of peer reviewers have used AI tools"; computational analysis estimated "between **6.5% and 16.9%** of reviews contained text substantially modified by large language models." Editorial, not empirical — context only.

---

## 2. Verification methods with measured performance

| # | Method | Paper / date | Checks | Measured performance | Opened |
|---|---|---|---|---|---|
| V1 | `RefChecker` — bibliographic resolution + web-search escalation | Phantom References, 2607.00738, 2026-07-01 | citation identity | **~$0.04/paper**; found ~1-in-20 NeurIPS/USENIX'25 papers with ≥2 hallucinated refs | yes |
| V2 | `urlhealth` — Wayback liveness + failure classification, used for self-correction | 2604.03173, 2026-04-03 | URL ever existed vs link-rot | cut problematic citations **6–79x**, to **sub-1%** | yes |
| V3 | `clibib` — deterministic BibTeX retrieval, two-stage | 2604.03159, 2026-04-03 | BibTeX field correctness | 83.6→**91.5%** field acc; 50.9→**78.3%** fully-correct; regression **0.8%** vs 4.8% single-stage | yes |
| V4 | `CiteVerifier` — GROBID + LLM reparse, cascaded cache→DBLP/Scholar→web, Levenshtein θ=0.9 | GhostCite, 2602.06718, 2026-02-06 | citation validity at scale | verifier validated on 400 sampled: **valid acc 100%, invalid acc 98% (392/400)**; 16 annotators × 1 month | yes |
| V5 | `CiteAudit` — multi-agent: metadata extraction → memory lookup → web retrieval → judgment | Shi, Sun, Zhang, Sun, Chawla, Ye; 2602.23452, 2026-02-26 | fabricated references | generated bench **97.3% acc / 93.8% prec / 100% rec / F1 0.968** (2nd-best Gemini-3-Pro 81.4% / 0.769); real-world **97.2% / 82.3% / 100% / F1 0.903** vs Claude-Sonnet 74.0%/0.444, GPTZero 55.7%/0.312. Bench **6,475 real + 2,967 fake**. 5-type taxonomy: title-level, author-level, metadata mismatch, compound cross-field | yes |
| V6 | `CiteTracer` — cascading multi-agent, 12-code taxonomy over Real/Potential/Hallucinated | 2605.08583, 2026-05-09 | field-level citation classification | **97.1% overall acc**; F1 Real 97.0 / Potential 95.8 / Hallucinated 98.5. Bench 2,450 synthetic + **957 real-world fabrications from ICLR 2026 and rejected submissions** | yes |
| V7 | `CiteCheck` — retrieval + structured LLM comparison + calibrated decision rules; Exact/Minor/Major | 2605.27700, 2026-05-26 | metadata corruption severity | **Macro-F1 88.7%, acc 88.9%**; 982-citation physics benchmark with controlled corruptions | yes |
| V8 | **Conformal guard** + gold-anchored verifier validation | 2607.20527, 2026-07-10 | claim-level citation support | verifier **recall 0.94 supported class (held out)**; exposes **3%→18%** swing from verifier strictness; verifier negative agreement **0.27–0.30** | yes |
| V9 | **Audit-then-Score (AtS)** — verifier disputes label with evidence → auditor adjudicates → label revised before scoring | DeepFact, 2603.05912, 2026-03-06 | benchmark label validity | unassisted PhD experts **60.8%** on hidden micro-gold; after **four AtS rounds, 90.9%** | yes |
| V10 | **DRE critic** — 4B critic + rejection sampling | 2606.32029, 2026-06-30 | wrong/omitted table values | critic **F1 78.2%**; answer accuracy **+12.0%** | yes |
| V11 | **Injected-error perturbation benchmark** + multi-model union | 2606.19749, 2026-06-18 | error-catching recall vs ground truth | best single **71.6%**; **union of 6 models 83.3%** | yes |
| V12 | **Dual independent human extraction** + third-reviewer adjudication | Oami et al., 2026-04-29 | extraction correctness | reference method; surfaced 67–93% Missing-Data share | yes |
| V13 | **Task-routing with continuous expert validation (KSR)** | 2608.12741, 2026-08-13 | screening/extraction/analysis/synthesis separately | gold standard 92.2% agr., kappa 0.80; screening 82.8% acc / 91.8% recall; synthesis still needs experts | yes |
| V14 | **Publisher-side CrossRef/Semantic Scholar checking** + mandatory AI disclosure + retraction policy | JCOM editorial (Joubert & Riedlinger), 2026-03-11, DOI 10.22323/388620260304154318 | fabricated references at journal level | policy, no measured performance. JCOM will "reject, withdraw, or retract manuscripts that contain fabricated references…before, during, or after peer review" | yes |
| V15 | **Mandatory automated citation verification at submission** | Ansari, 2602.05930 | fabricated citations | proposal only | yes |

**What the landscape says:**
1. **Existence-checking is close to solved; support-checking is not.** V1–V7 report 88–97% on "does this reference exist / is the metadata right." Claim-support (C1, C2) has no comparable number — V8 shows it isn't even well-defined without first validating the verifier.
2. **Verifier disagreement is the unreported confound.** V8's 3%→18% swing on identical outputs; any single 2026 "unsupported citation rate" is verifier-dependent.
3. **Tool-use beats prompting.** V2 (6–79x), V3 (+8.0pp), V10 (+12.0%) all add a deterministic external check. Prompt engineering alone gave "modest improvements" (D2); prompting *for accuracy* made over-generalization worse in the 2025 background study.
4. **Ensembling helps but less than hoped.** V11: 71.6% → 83.3% across six models. G1: AI-reviewer overlap 21% vs 3% for humans — a second model is a correlated check.
5. **Experts are better auditors than labelers.** V9: 60.8% → 90.9%. Have humans adjudicate disputes, not label from scratch.

---

## 3. Background (pre-2026)

- **Peters & Chin-Yee, "Generalization bias in large language model summarization of scientific research," *Royal Society Open Science* 12(4):241776, April 2025** (arXiv 2504.00025; PMC12042776). 10 LLMs, ~4,900 summaries. Over-generalization **26–73%** for DeepSeek / ChatGPT-4o / LLaMA 3.3 70B; LLM summaries "nearly five times more likely" than human ones to contain broad generalizations; **prompting explicitly for accuracy made models nearly twice as likely to overgeneralize**; newer models worse. `snippet only` this session — canonical background for §1.E.
- **Zhan, Suvada, Xu, Tian, Cara, Wallace, Ali, "Accelerating the pace and accuracy of systematic reviews using AI: a validation study," *Systematic Reviews*, 2025-12-18, DOI 10.1186/s13643-025-02997-8** (PMC12829171). **Opened — and it is 2025, not 2026.** Review Copilot (GPT-4) vs humans on 4 published SRs: title/abstract **99.2% sens / 83.6% spec** (bal. acc 91.4%, kappa 0.83); full-text **97.6% / 47.4%** (bal. acc 72.5%, kappa 0.74); 66–75% fewer person-hours; 95.4% agreement between repeat runs.
- Not 2026, frequently returned by 2026-phrased searches: DeepResearch Bench (2506.11763, Jun 2025); ResearchRubrics (2511.07685, Nov 2025); DeepTRACE (2509.04499, Sep 2025); CiteGuard (2510.17853, Oct 2025, 68% on CiteME); LLM-REVal (2510.12367); AutoSurvey2 (2510.26012); Structure-Guided Memory Consolidation (2508.04306).

---

## 4. Leads that were non-existent, mis-dated, or mis-attributed

| Lead as given | Verdict |
|---|---|
| "The Lancet (May 2026) auditing ~111 million references from ~2.5 million papers" | **Conflation of two distinct studies.** 111M refs / 2.5M papers / arXiv+bioRxiv+SSRN+PMC = **Zhao et al., arXiv 2605.07723** (v1 2026-05-08). The Lancet paper (Topaz et al.) audited PMC-OA only: ~126M structured refs, 97.1M verified, ~2.47M papers. The 1-in-2,828 / 458 / 277 rates belong to **The Lancet**. |
| Lancet article itself | **Found but NOT opened** (403). Authors *Topaz M, Roguin N, Gupta P, Zhang Z, Peltonen LM*, DOI 10.1016/S0140-6736(26)00603-3, 407(10541):1779–1781 are `snippet only`. |
| GPTZero Jan 2026 (4,841 / 100 / 53) | Mostly confirmed on primary page: 4,841 papers, 100 confirmed hallucinations. But GPTZero says **"over 51 NeurIPS papers"**; the **53** is Ansari's number. |
| arXiv 2602.05930 (66% fabrications) | **Confirmed, opened.** 66% is the *primary*-mode share; secondary modes distributed separately (Semantic 63%, Identifier Hijacking 29%). |
| arXiv 2605.08583, 2602.05867, 2603.20235, 2605.20668, 2604.01128 | **All confirmed, all opened, all 2026.** |
| ScienceDirect S221462962600191X (publisher-led verification) | **Exists, NOT opened** — 403 on both `/pii/` and `/abs/pii/`. No numbers extracted. Substituted the JCOM editorial (opened) for the publisher-policy angle. |
| PMC12829171 (systematic reviews validation) | **Exists, opened — but 2025-12-18.** Moved to background. |
| PMC13507689 (Living SRs → Fully AI-Driven) | **Exists, opened.** Mojadeddi, Baker, Rosenberg; *Cureus*, 2026-07-26, DOI 10.7759/cureus.113428. **Narrative/perspective, not empirical** — no error rates. Only numbers: SR publications "median annual growth rate of 26%"; Cochrane reviews "decreased since 2015." Excluded from §1. |
| Nature EBD s41432-026-01227-x | **Exists (2026-06-04), NOT opened** (303 → IdP). Editorial. `snippet only` numbers in G5. |
| "Shankar 2026 J Biomed Inform, 60–74% omissions" | **Paper exists** (2026-07-25, PII S1532046426001103, PubMed 42501879); 60–74% / 0.08–6% appear in two independent snippets. **NOT opened** (403 / cookie walls ×3). **"Shankar" unconfirmed.** Direction independently corroborated by Oami et al. (opened): Missing Data 67–93%, Fabricated 0.7–14%. |
| "2026 over-generalization follow-up to Peters & Chin-Yee" | **No direct replication found.** 2026 work exists under different framing: certainty distortion (2606.07951), epistemic-rhetorical miscalibration (2604.19768), corpus hedge decline (2603.16131). Peters & Chin-Yee is **April 2025**. |
| "DeepResearch Bench successors / ResearchRubrics dated 2026" | ResearchRubrics = **Nov 2025**; DeepResearch Bench = **Jun 2025**. Genuine 2026 successors: **DRACO** (2602.11685), **DeepFact** (2603.05912), **Cited but Not Verified** (2605.06635). |
| "2026 cross-model agreement / LLM-as-judge validity" | Found: **Norman, Rivera, Hughes, "Reliability without Validity," arXiv 2606.19544, v1 2026-06-17, opened.** 21 judges, 3 benchmarks, 118 runs, **~541,000 judgments**. Exact-match agreement overstates reliability by **33–41 percentage points** vs Cohen's kappa on MT-Bench; rankings shift up to **14 positions** across benchmarks; two production judges had test-retest >0.95 *while* position bias >0.10; verbosity bias minimal (<0.011). Proposes a "Minimum Viable Validation Protocol." **General-purpose, not evidence-synthesis-specific** — flag when citing. |

**2026 items found but not deeply pursued (leads, all `snippet only` unless noted):** **DRACO** (2602.11685, v1 2026-02-12, Perplexity AI; Zhong, Zhang, Southern, Yang, Wang, Jung, Zhang, Yarats, Ho, Ma) — **abstract opened**: 10 domains, sources from 40 countries, tasks from de-identified real Perplexity Deep Research requests, rubrics on factual accuracy / breadth-depth / presentation / citation quality. The widely-repeated "best system achieves only **65% citation quality and 68% factual accuracy**" is `snippet only`, **not on the abstract page I opened** — verify in the PDF. Also: ScholarQuest (2606.20235); SurveyLens (2602.11238); SurveyReview (2608.07641); DeepSurvey (2605.29522, cites 0.728 citation recall / 0.681 precision); StructSurvey (2607.01243); PaperTrail (2602.21045); MedJUDGE scoping review (2604.25933); "Reference Accuracy in LLM Chatbots" (PubMed 41546380); "Evaluation of AI Citation Accuracy in Anterior Segment Research" (PubMed 42161604).

---

## 5. URLs opened vs snippet-only

**Opened (42):** statnews.com/2026/05/07/lancet-study-finds-steep-rise-fraudulent-citations-academic-papers/ · retractionwatch.com/2026/05/07/one-in-277-pubmed-indexed-papers-in-2026-shows-fabricated-references-says-analysis/ · eurekalert.org/news-releases/1127364 · cidrap.umn.edu/anti-science/review-uncovers-rising-rate-fake-references-published-biomedical-papers · arxiv.org/abs/{2604.03173, 2604.03159, 2602.05930, 2602.05867, 2605.08583, 2603.20235, 2605.20668, 2604.01128, 2605.06635, 2603.05912, 2602.06718 (+html v2), 2604.18880, 2603.22344, 2602.10881, 2605.07723 (+pdf, read directly), 2606.19544, 2602.23452 (+html v1), 2605.27700, 2609.05505, 2607.20527, 2604.23593, 2602.11685, 2607.09932, 2604.25256, 2606.32029, 2609.03580, 2607.00738, 2606.07951, 2604.19768, 2603.16131, 2606.19749, 2608.12741, 2608.26885} · gptzero.me/news/neurips/ · pmc.ncbi.nlm.nih.gov/articles/{PMC12829171, PMC13507689}/ · frontiersin.org/journals/digital-health/articles/10.3389/fdgth.2026.1799623/full · jcom.sissa.it/article/pubid/JCOM_2501_2026_E/

**Attempted and blocked — NOT opened:** thelancet.com …PIIS0140-6736(26)00603-3/fulltext (403) · sciencedirect.com …S221462962600191X, both `/pii/` and `/abs/pii/` (403) · sciencedirect.com …S1532046426001103 (not attempted after two SD 403s) · pubmed.ncbi.nlm.nih.gov/42501879/ (cookie wall) · europepmc.org/article/MED/42161604 (403) · nature.com/articles/s41432-026-01227-x (303 → idp.nature.com)

**Snippet-only (leads, not citations):** Peters & Chin-Yee 2025 numbers; Lancet author list & DOI; Lancet "2,471,758 papers / 125,615,773 refs / 97.1M (77%)"; J Biomed Inform 60–74% omissions and all sub-numbers; EBD editorial 53% and 6.5–16.9%; DRACO 65%/68%; SciZoom 22.8% and 1.88→1.45; "20% of ICLR 2026 submissions"; ScholarQuest 1.80% zero-recall; DeepSurvey 0.728/0.681; all chatbot reference-validity percentages from the Fox News-sourced result; everything in §4's "not deeply pursued" list.

---

## 6. Mapping to the motivating scenario

"Read these 40 papers, find every claim about KV-cache characteristics, organize them":

| Error type | Expected severity | Best 2026 evidence |
|---|---|---|
| **Fabricated citations** | **Low** — papers are supplied, nothing to invent. Risk returns only if the agent adds references. | Phantom References (~1-in-20 papers, ≥2 hallucinated refs); Lancet 1-in-277 early 2026; Mysterious Citations 2–6% of 2025 HPC papers |
| **Misattributed claims** | **High** | Cited but Not Verified: link validity >94%, relevance >80%, **factual accuracy 39–77%**; Faithful by Design: "Unsupported Claims… dominant failure mode," 1.55/3 |
| **Omitted claims** | **Highest, least visible** | SciLitBench: **30% of evaluation evidence, 25% of limitations** recovered; Oami: Missing Data **67–93%** of errors; J Biomed Inform (snippet) omissions **60–74%** |
| **Over-generalization / dropped conditions** | **High, compounds with iteration** | From 'May' to 'Is': distortion in **up to 75%** of outputs, increases 1.5–2x more often than decreases, **20% → 40% from 1 to 5 iterations** |
| **Wrong numbers** | **High for tuples, moderate for isolated values** | Structural Failures: "full meta-analytic association tuples… near-zero reliability," worse with long context; Oami: numerical **47–88%** vs categorical **74–96%** |

Three cautions this corpus supports:

1. **The ask is tuple extraction, not fact lookup.** "Every claim about KV-cache characteristics" is `(claim, condition/config, number, source paper)` — exactly the structure 2602.10881 reports as near-zero-reliability, with named modes *role reversal*, *cross-analysis binding drift*, *numeric misattribution*. Expect number and condition to detach.
2. **Reorganizing is not free.** 2606.07951 shows certainty inflation roughly doubling from one to five rewrite passes. Every "now reorganize by theme" step can strip a qualifier.
3. **Re-running is not verification.** 2608.26885: two identical GPT-5.4 runs disagreed on 94 of 1,131 records, 29 verified-eligible. 2605.20668: AI reviewers overlap each other at 21% vs 3% for humans — a second model is a correlated check. What works: deterministic external tools (6–79x, +8.0pp, +12.0%), humans as *adjudicators* not labelers (60.8% → 90.9%), and injected-error perturbation benchmarks that supply ground truth to measure recall against (71.6% single model / 83.3% six-model union).
