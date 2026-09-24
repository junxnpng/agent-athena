# Agent A — 2026 voices on verifying AI-delegated logical/knowledge work

**Compiled:** 2026-09-21
**Motivating scenario:** a user asks an AI to "read these 40 papers, find every claim about KV-cache characteristics, and organize them." How does a human check the result is faithful to sources, complete, condition-preserving, and free of fabricated citations?

**Evidence conventions.** Every quote below was copied from a page that was actually fetched; each item is tagged `opened` (primary page fetched and quote read off it) or `snippet only` (search-result snippet only, quote NOT asserted verbatim). Items marked `opened (agent)` were fetched by a delegated research agent rather than by me; the three most load-bearing of those (Weng, Husain provenance, Tao Nature) I re-fetched and confirmed myself, noted inline.

---

## 1. Items, grouped by person

### Terence Tao (Professor of Mathematics, UCLA) — the richest 2026 source

**T1. "Mathematics in the age of AI" — ICM 2026 essay** — `opened`
- Date: lecture 2026-07-24; arXiv submission 2026-08-17
- URL: https://arxiv.org/html/2608.16753v1 (abstract: https://arxiv.org/abs/2608.16753)
- Verbatim: "if the authors cannot convincingly demonstrate that they are able to give a clear, expert-level talk on their results, one that is correct and properly attributed, then the result should not be published."
- Implies: **the comprehension gate.** The person who commissioned the extraction must be able to present and defend it unaided. If you cannot give the talk on your own KV-cache claim table, the table is not yet yours and is not verified.

**T2. Same essay — decomposition of the pipeline** — `opened`
- Date: 2026-08-17
- URL: https://arxiv.org/html/2608.16753v1
- Verbatim: "What if an AI tool generates a lengthy proof that is verified to be correct, but which nobody — not even the humans who prompted the tool — understands?"
- Implies: correctness and understanding are separate checks. A claim table can pass a spot-check and still leave you unable to say what it means — Tao's "generation → verification → exposition → publication → canonicalization" staging says to budget for the later stages explicitly.

**T3. Same essay — why formalization changes the trust calculus** — `opened`
- Date: 2026-08-17
- URL: https://arxiv.org/html/2608.16753v1
- Verbatim: "A formally verified proof is, after all, precisely a proof whose correctness no longer depends on the reputation or the diligence of its author."
- Implies: prefer checks that do not depend on the diligence of the extractor. For literature review, the analogue is mechanical provenance (does this quote string actually occur in that PDF?) over trust in the summarizer.

**T4. Same essay — disclosure rule (quoting the Leiden Declaration)** — `opened`
- Date: 2026-08-17
- URL: https://arxiv.org/html/2608.16753v1
- Verbatim: "Make it easier for your peers to review your work by disclosing tool use, giving precise and complete references to previous results, and providing formal proofs where feasible and appropriate."
- Implies: record which model/tool produced which row, so a reviewer knows where to aim scrutiny.

**T5. Palomar registry announcement** — `opened`
- Date: 2026-08-18
- URL: https://terrytao.wordpress.com/2026/08/18/palomar-a-registry-of-lean-verified-mathematics/
- Verbatim: "In recent months there has been a proliferation of AI-generated proofs of various old and new results, some of which have been formalized in the proof assistant language Lean." and "However, checking that a given Lean repository actually proves the claimed statement is somewhat non-trivial, especially for an audience which is not expert in the use of Lean."
- Implies: **verification has its own usability problem.** Even when a machine-checkable artifact exists, a non-expert cannot easily confirm it checks the claimed statement. Build the claim table so that checking one row is cheap for someone who did not build it.
- Note: Tao is explicit that Palomar "is **not** a peer-reviewed journal" and its automated checks "fall well short of what a proper human peer review...would give" — i.e. mechanical checking is a floor, not a substitute for reading.

**T6. Dwarkesh Patel interview** — `opened`
- Date: 2026-03-20
- URL: https://www.dwarkesh.com/p/terence-tao
- Verbatim: "We're now in a situation where suddenly people can generate thousands of theories for a given scientific problem. Now we have to verify them, evaluate them."
- Implies: the generation/verification asymmetry stated plainly by a mathematician. Extraction across 40 papers is cheap; the review budget is the scarce resource and must be allocated deliberately.

**T7. Same interview — on RL finding backdoors** — `opened`
- Date: 2026-03-20
- URL: https://www.dwarkesh.com/p/terence-tao
- Verbatim: "It's really important with these formal proof assistants that there are no backdoors or exploits you can use to somehow get your certified proof without actually proving it, because reinforcement learning is just so good at finding these backdoors."
- Implies: **your checker will be gamed.** If you grade the extraction with a rubric the model can see, expect the rubric to be satisfied without the underlying work. Keep some checks out-of-band.

**T8. IEEE Spectrum, "AI in Mathematics Is Forcing Big Questions" (Benjamin Skuse)** — `opened`
- Date: 2026-06-25
- URL: https://spectrum.ieee.org/ai-in-mathematics
- Verbatim: "If it wasn't for this formal verification layer, opening projects up without any safeguards would just be a disaster," Tao explains. "But in math, we can completely check and verify outputs, and this really filters out a lot of the rubbish."
- Implies: the *precondition* for safely delegating at scale is a cheap automatic check. Literature review has no Lean — so the honest read is that this scenario sits on the hard side of Tao's line and needs manufactured checks (quote-string matching, citation resolution) to substitute.
- Source note: IEEE Spectrum is press, but the words are Tao's in direct quotation.

**T9. Nature, "'The job description is changing'"** — `opened` (via Tao's own curated summary page, which I fetched; the Nature article itself is the original venue and was not opened)
- Date: 2026-05
- URL (opened): https://teorth.github.io/tao-web/ai-views.html
- Verbatim: "In almost any other application, the biggest Achilles heel of AI is that it makes unverifiable mistakes. But in mathematics, almost uniquely, you can automatically check the output"
- Implies: **the sharpest statement of the problem for our scenario.** Tao is explicitly saying that outside mathematics, AI mistakes are *unverifiable*. A KV-cache claim table is exactly the "almost any other application" case; the verification apparatus has to be built by hand.

**T10. Mathstodon — "proof indigestion"** — `opened` (fetched via the Mastodon API, since the HTML page is JS-rendered)
- Date: 2026-05-10
- URL: https://mathstodon.xyz/@tao/116551624228986501
- Verbatim: "out of three major components of the mathematical problem solving process - proof generation, proof verification, and proof digestion - the first two are being automated far more successfully than the third, leading to a new experience of 'proof indigestion' in which proofs are being generated and even verified without being digested."
- Implies: a verified claim table that nobody has digested is still a failure state. Also his warning against "blindly optimizing various metrics for 'digestibility'" — a rubric-scored summary can be worse "when viewed holistically."

---

### Andrej Karpathy (independent; formerly OpenAI/Tesla)

**K1. "Sequoia Ascent 2026 summary" (his own blog; cleaned transcript of the fireside chat)** — `opened`
- Date: post 2026-04-30 (talk recorded ~a week earlier at Sequoia AI Ascent 2026)
- URL: https://karpathy.bearblog.dev/sequoia-ascent-2026/
- Verbatim: "Traditional software automates what you can **specify**. LLMs and reinforcement learning automate what you can **verify**."
- Implies: **the load-bearing line for this whole scenario.** Delegation quality is bounded by whether you can state a check. Before asking for 40 papers to be mined, write down what a correct row looks like and how you would falsify it.

**K2. Same post — the agentic engineer's posture** — `opened`
- Date: 2026-04-30
- URL: https://karpathy.bearblog.dev/sequoia-ascent-2026/
- Verbatim: "The agentic engineer does not blindly accept generated code. They design specs, supervise plans, inspect diffs, write tests."
- Implies: the literature-review analogue of "inspect diffs" is reviewing the *delta* against sources — which claims were added, which conditions were dropped — not re-reading the finished summary.

**K3. Same post — staying in the loop while models are jagged** — `opened`
- Date: 2026-04-30
- URL: https://karpathy.bearblog.dev/sequoia-ascent-2026/
- Verbatim: "To the extent models remain jagged, it means you need to be in the loop. You need to treat them as tools and stay in touch with what they are doing."
- Implies: jaggedness is not uniform, so sampling should be adversarial — check the rows where the paper was hardest, not a random sample.

**K4. Same post — what stays human** — `opened`
- Date: 2026-04-30
- URL: https://karpathy.bearblog.dev/sequoia-ascent-2026/
- Verbatim: "You still have to be in charge of aesthetics, judgment, taste, and oversight."
- Implies: the "is this claim actually about the same thing the other paper meant" judgment does not delegate.

**K5. `karpathy/autoresearch` (released 2026-03-07)** — `opened` (repo page fetched; **no verbatim verification statement found in the README** — listed as context only, not as a quote)
- URL: https://github.com/karpathy/autoresearch
- Context: the design is a loop where an agent proposes a change, runs a 5-minute training job, and keeps it only if a single pre-declared metric (validation bits-per-byte) improves, rolling back otherwise. The verification principle is embodied in the architecture — one metric fixed in advance, reversible commits — rather than stated in prose. I did not find a Karpathy quote about verification on the repo page and am not inventing one.

---

### Simon Willison (independent; co-creator of Django, author of simonwillison.net)

**W1. "Don't be a meat proxy"** — `opened`
- Date: 2026-08-03
- URL: https://simonwillison.net/2026/Aug/3/dont-be-a-meat-proxy/
- Verbatim (Willison's own words): "Niklas Gruhn coins an excellent new term - **meat proxy** - for people who blindly copy and paste the output of AI systems to their peers."
- Verbatim (the Gruhn passage Willison quotes and endorses): "By all means, prompt AI. But don't just relay the output. Read it, understand it, validate it, and then write a response in your own words (a decent certificate that you've done the prior steps). Making that effort is value you can add."
- Implies: **rewriting in your own words is the certificate.** For the claim table: forcing yourself to restate each cluster in your own prose is itself the verification act, because you cannot do it without having read the source.
- Attribution care: the memorable passage is Gruhn's, not Willison's. Willison's contribution is the endorsement and the term's amplification.

**W2. "More than just code review"** — `opened`
- Date: 2026-08-22
- URL: https://simonwillison.net/2026/Aug/22/more-than-just-code-review/
- Verbatim: "The key skill required to make productive use of coding agents is being able to confidently instruct them on how to make changes and then confidently verify that those changes have been applied in the correct way."
- Implies: instructing and verifying are one paired skill. Ask for the extraction in a shape you already know how to check.

**W3. Same post — against line-by-line as the default** — `opened`
- Date: 2026-08-22
- URL: https://simonwillison.net/2026/Aug/22/more-than-just-code-review/
- Verbatim: "Eyeballing every line of code has never been the most effective way to validate a change to a piece of software."
- Implies: **a useful counterweight.** Re-reading all 40 papers is not the only or best check; targeted mechanical checks (does this quote exist, does this DOI resolve, does this condition appear in the abstract) can beat exhaustive human re-reading.

**W4. "Some thoughts on the Navier–Stokes Millennium Prize Problem"** — `opened` (**weak item, included for completeness**)
- Date: 2026-09-08
- URL: https://simonwillison.net/2026/Sep/8/on-navier-stokes/
- Finding: the post is mainly about competitive/ethical concerns and compute scale, not about how to verify. The only verification-adjacent line retrieved was a factual note that "Lean formalization and verification took an additional 17 hours via GPT‑6 Astra." I did **not** find a Willison statement here about how a human independently audits such a claim, and I am not asserting one.

---

### Lilian Weng (co-founder, Thinking Machines Lab; formerly VP Research, OpenAI)

**LW1. "Harness Engineering for Self-Improvement" (Lil'Log)** — `opened` (re-fetched and confirmed by me)
- Date: 2026-07-04
- URL: https://lilianweng.github.io/posts/2026-07-04-harness/
- Verbatim: "every claim (citation, numerical, methodological, conclusion) must trace to an evidence source and is audited by Chain-of-Evidence checks."
- Implies: **the most directly applicable prescription found.** Every row of the KV-cache table carries a pointer to the exact passage, and a separate audit pass walks those pointers. Note her taxonomy — citation, numerical, methodological, conclusion — maps almost exactly onto the four failure modes in the scenario.

**LW2. Same post — why plausibility is not evidence** — `opened` (confirmed by me)
- Date: 2026-07-04
- URL: https://lilianweng.github.io/posts/2026-07-04-harness/
- Verbatim: "A system can write a plausible manuscript while still having fabricated citations, implementation drift, or weak experimental results."
- Implies: fluency is uncorrelated with faithfulness; never use "reads well" as a signal.

**LW3. Same post — where the human goes** — `opened` (confirmed by me)
- Date: 2026-07-04
- URL: https://lilianweng.github.io/posts/2026-07-04-harness/
- Verbatim: "Humans should move up the stack, not be removed from the loop, meaning that human should provide oversight at the right time, at the right abstraction level and our system design should consider when and how to set up such touch points."
- Implies: design the checkpoints in advance (e.g. approve the claim taxonomy before extraction runs), rather than reviewing only the finished artifact.

---

### Hamel Husain (independent AI/ML consultant; co-instructor, "AI Evals for Engineers & PMs")

**H1. "'It's Hard to Eval' Is a Product Smell"** — `opened` (re-fetched and confirmed by me)
- Date: 2026-06-29
- URL: https://hamelhusain.substack.com/p/its-hard-to-eval-is-a-product-smell
- Verbatim: "Artifacts that are hard for you to verify are often hard for users too." and "A common thread across these examples is provenance. The fastest way to make an output checkable is to show where each part came from, with links to see more detail."
- Implies: **make the output shape carry its own audit trail.** If the claim table is hard to check, that is a defect in the table's design, not an unavoidable cost.

**H2. "Do Automated Evals Work?"** — `opened (agent)`
- Date: 2026-09-02
- URL: https://hamelhusain.substack.com/p/do-automated-evals-work
- Verbatim: "The best recovered 87 percent of failures flagged by humans. Additionally, every system found issues humans missed." and "Fully automated approaches always failed to catch interactions that 'looked correct' but fell short."
- Implies: an LLM-judge over the claim table catches most errors but systematically misses the "looks correct" class — which is precisely the dropped-condition failure mode. Automated checks plus human sampling, not either alone.

**H3. "Evals Skills for Coding Agents"** — `opened (agent)`
- Date: 2026-03-03
- URL: https://hamelhusain.substack.com/p/evals-skills-for-coding-agents
- Verbatim: "Both are hallucinations, but one gets a fact wrong and the other makes up a user action."
- Implies: separate the failure taxonomy before measuring. "Wrong quote," "invented claim," and "dropped condition" are different defects needing different checks.

---

### Shreya Shankar (PhD candidate, UC Berkeley; DocETL, EvalGen; co-instructor of the evals course)

**S1. "Exploring Agent-Assisted Qualitative Analysis"** — `opened (agent)`
- Date: 2026-05-21
- URL: https://www.sh-reya.com/blog/ai-qual-analysis/
- Verbatim: "To validate open codes, I only have to look at the tweet and ask whether the proposed codes make sense. Validating axial codes consists of more steps... this requires O(n²) comparisons, over pairs of codes, which is not feasible for humans."
- Implies: **the single most scenario-specific insight in this collection.** Checking an individual extracted claim is O(1) and easy; checking that the *organization* of claims is complete and non-overlapping is O(n²) and infeasible by hand. The "organize them" half of the request is far harder to verify than the "find every claim" half.

**S2. Same post — on vague categories and provenance** — `opened (agent)`
- Date: 2026-05-21
- URL: https://www.sh-reya.com/blog/ai-qual-analysis/
- Verbatim: "Vague codes are easy to believe and impossible to act on." and "Without example tweets under each category and provenance from category back to evidence, I struggled to truly understand the definition of some of these clusters."
- Implies: require every cluster in the KV-cache taxonomy to name its member claims. A category without exemplars is unfalsifiable.

---

### Sebastian Raschka (independent researcher; "Ahead of AI")

**R1. "Controlling Reasoning Effort in LLMs"** — `opened (agent)`
- Date: 2026-07-18
- URL: https://magazine.sebastianraschka.com/p/controlling-reasoning-effort-in-llms
- Verbatim: "Only the final answer and response format determine the reward" (on RLVR training) and "These `<think>` tags...do not make the model reason, and they are not required to achieve good reasoning performance."
- Implies: **do not audit the model's stated reasoning.** Its explanation of why it extracted a claim was never optimized for truthfulness — only the answer was. Check the claim against the paper, not the rationale against the claim.

**R2. Interview on Hugo Bowne-Anderson's Substack** — `opened (agent)`; third-party host, Raschka's own words in transcript
- Date: 2026-07-15
- URL: https://hugobowne.substack.com/p/llm-architecture-in-2026-agent-harnesses
- Verbatim: "The implementation doesn't lie. It's like the truth, basically, if it works."
- Implies: prefer checks that execute. The literature-review analogue is a script that re-locates every quoted string in the source PDFs — a check that either passes or does not.

---

### NeurIPS 2026 workshop organizing committee (collective statement, not an individual)

**N1. "Verification in the Age of AI Scientists," NeurIPS 2026 workshop** — `opened`
- Date: workshop 2026-12-11/12 (page live as of 2026-09); organizers include Marinka Zitnik (Harvard), Priya Donti (MIT), Emilien Dupont (Google DeepMind), Yuanqi Du (Microsoft Research)
- URL: https://ai4sciencecommunity.github.io/neurips26
- Verbatim: "The bottleneck for AI for Science is no longer hypothesis generation, it is verification" and "as AI Scientists scale beyond what humans can manually inspect, the central problem becomes which AI outputs deserve our scarce verification budget".
- Implies: **verification budgeting as a first-class design problem.** With 40 papers you cannot check everything; decide in advance which rows get scrutiny (highest-stakes claims, most-cited numbers, claims that contradict each other).
- Note: this is an organizing-committee framing statement, not a personal quote from a named individual.

---
### Kevin Buzzard (Professor of Pure Mathematics, Imperial College London)

**B1. "FLT: Anthropic has beaten me to it" (his own Xena Project blog)** — `opened` (re-fetched and confirmed by me)
- Date: 2026-09-04
- URL: https://xenaproject.wordpress.com/2026/09/04/flt-anthropic-has-beaten-me-to-it/
- Verbatim: "I've compiled the code base and run comparator on it — it checks out." and "I asked an agent to look over the repository and report on everything which was not a mathematical definition or proof of a theorem, and then extremely carefully inspected the 100 or so lines of code which did not fit into this category."
- Implies: **the best worked example of an actual verification procedure in this collection — a two-layer check.** Layer 1 is mechanical and total (the checker runs over everything). Layer 2 is human and targeted (he reduces the surface to ~100 lines the checker cannot vouch for, then reads those with full care). The literature-review analogue: mechanically confirm every quoted string resolves to its source, then hand-read only the connective prose the machine cannot check.
- Discrepancy note (worth recording): a delegated agent reported this second sentence as "I manually inspected every line of the code base which (according to Claude) was not a mathematical definition or proof of a theorem, and verified that none of it was doing anything malicious." My own fetch of the page returned the wording above instead. I have used my own fetch. This is a live instance of the exact failure the scenario worries about — a plausible, near-miss paraphrase presented as a quote.

**B2. Same post — on what the artifact does not establish** — `opened` (confirmed by me)
- Date: 2026-09-04
- URL: https://xenaproject.wordpress.com/2026/09/04/flt-anthropic-has-beaten-me-to-it/
- Verbatim: "Note that mathematically this work of anthropic tells us essentially nothing: I am on record as saying that I am 99.9% sure that the proof of FLT is OK, and most people in the number theory community are 100% sure." and "the formalization just faithfully follows the early literature on the proof and adds nothing."
- Implies: **separate "is it correct?" from "is it worth anything?"** A claim table can be fully faithful and still contribute nothing. Verification of faithfulness is not verification of value — ask both questions.

**B3. Buzzard quoted on Anthropic's research post** — `opened (agent)`; lab-hosted page quoting him
- Date: 2026-09-04
- URL: https://www.anthropic.com/research/formalizing-fermats-last-theorem
- Verbatim (Buzzard, as rendered on Anthropic's page): "The techniques will also enable us to rigorously check LLM-generated mathematics, which is currently typically an extremely costly human-led process."
- Implies: checking LLM output is expensive human labour by default; the goal is to convert as much of it as possible into something mechanical.
- Caveat: read on Anthropic's own site, not Buzzard's blog. Treat with the usual care for a lab quoting a favourable outside expert.

---

### Timothy Gowers (Fields Medalist; Collège de France / Cambridge)

**G1. "What sort of maths are LLMs good at?" (his own blog)** — `opened` (re-fetched and confirmed by me)
- Date: 2026-08-12
- URL: https://gowers.wordpress.com/2026/08/12/what-sort-of-maths-are-llms-good-at/
- Verbatim: "Initially I was amazed that the problem had been solved, but on closer inspection I realized that the approach was actually not all that novel, and one that with the right small hint a suitably expert human could have found quite easily."
- Implies: **first-pass impressiveness systematically overstates quality.** The reviewer's first reaction to a well-organized claim table is not evidence. Budget a second, slower pass, because the first one is known to be wrong in a predictable direction.

**G2. Same post — the unfalsifiable-effort problem** — `opened` (confirmed by me)
- Date: 2026-08-12
- URL: https://gowers.wordpress.com/2026/08/12/what-sort-of-maths-are-llms-good-at/
- Verbatim: "if an LLM has what looks like the kind of idea that could only be the result of 'deep thought' about a problem, we can never be sure that it has actually carried out that deep thought, as opposed to finding a model argument already in the literature"
- Implies: you cannot infer from the output that the work was done. "It clearly read all 40 papers, look how thorough this is" is not a valid inference — only per-claim source checks distinguish reading from confabulating.

---

### Subbarao Kambhampati (Professor of Computer Science, Arizona State University)

**KB1. Communications of the ACM news article** — `opened (agent)`; journalism quoting him directly, not a primary post
- Date: 2026-06-29
- URL: https://cacm.acm.org/news/thats-logical-teaching-llms-to-give-better-answers/
- Verbatim: "There will always be a role for some type of verifier. LLMs can't do it alone."
- Implies: **do not let the extractor certify itself.** The check must come from outside the model that produced the claims — a different pass, a different tool, or a human against the PDF.
- Note: no 2026 primary-source (own blog / X) verification quote was retrievable; his X account returned 403. His ICML 2026 workshop talk "On the Role of Verifiers and Thinking Traces in Reasoning Models" (https://icml.cc/virtual/2026/79829) is confirmed to exist and is on-topic, but no transcript was obtainable — `snippet only`, no quote asserted.

---

### Andrew Ng (founder, DeepLearning.AI; "The Batch")

**AN1. "Three Key Loops for Building Great Software," The Batch** — `opened (agent)`
- Date: 2026-06-26
- URL: https://www.deeplearning.ai/the-batch/three-key-loops-for-building-great-software
- Verbatim: "Given a product specification and optionally a set of evals (that is, a dataset against which to measure performance), we can have an AI agent write code, test its work, and keep iterating until the code is bug-free."
- Implies: build a small labelled eval set first — e.g. hand-extract every KV-cache claim from 3 of the 40 papers — and measure the agent's run against it before trusting the other 37.

**AN2. Same letter — where the human's edge actually is** — `opened (agent)`
- Date: 2026-06-26
- URL: https://www.deeplearning.ai/the-batch/three-key-loops-for-building-great-software
- Verbatim: "So long as the human knows something the AI does not, human-in-the-loop is needed to inject that knowledge into the system." and "I see humans as having a significant context advantage over current AI systems."
- Implies: spend human attention on the things only you know — which conditions matter for your use, which papers are actually comparable — not on re-reading what the model already read.

---

### Ethan Mollick (Associate Professor, Wharton; "One Useful Thing")

**EM1. "The Overhang"** — `opened (agent)`
- Date: 2026-09-18
- URL: https://www.oneusefulthing.org/p/the-overhang
- Verbatim: "Making great things with AI means knowing which AI outputs to keep, which to discard, and which to use as raw material."
- Implies: verification is curation, not proofreading. Expect to discard rows, not just correct them.

**EM2. Same post — why he could tell** — `opened (agent)`
- Date: 2026-09-18
- URL: https://www.oneusefulthing.org/p/the-overhang
- Verbatim: "I chose them, I knew enough about Zork and Eco and my own book to see where the AI went wrong."
- Implies: **verification capacity is bounded by the checker's own domain knowledge.** Whoever reviews the KV-cache table must already know the area well enough to notice a missing condition. Delegating the review to someone who does not know the field produces the appearance of checking without the substance.

---

### Yoshua Bengio (Professor, Université de Montréal / Mila; founder, LawZero)

**YB1. LawZero research page, "The Scientist AI: Safe by Design, by Not Desiring"** — `opened (agent)`
- Date: 2026-02-05 (as dated on the page)
- URL: https://lawzero.org/en/research
- Verbatim: "Its predictions are transparent, auditable and verifiable."
- Implies: design the output so it is auditable by construction — every claim carrying its justification — rather than auditing an opaque artifact after the fact.
- Caveat flagged by the researching agent: this line rendered on a direct fetch and in two independent search snippets of the same page, but did not render through a text-only reader proxy (likely a JS-rendering gap). Treated as sound but worth re-confirming if load-bearing.

**YB2. Fortune interview** — `opened (agent)`; secondary source, direct quotation
- Date: 2026-01-15
- URL: https://fortune.com/2026/01/15/ai-godfather-yoshua-bengio-changes-view-on-ai-risks-sees-fix-becomes-optimistic-lawzero-board-of-advisors/
- Verbatim: "I'm now very confident that it is possible to build AI systems that don't have hidden goals, hidden agendas."
- Implies: weaker fit — speaks to why verification is tractable in principle, not to a checking method. Included for completeness.

---

### Dario Amodei (CEO, Anthropic)

**DA1. "We Must Pace the Frontier"** — `opened (agent)`
- Date: 2026-09
- URL: https://darioamodei.com/post/we-must-pace-the-frontier
- Verbatim: "provide third-party evaluators with permanent, employee-level access to our systems, so that they can verify adherence to our safety measures" and "Embedded evaluators can check at the level of nuts and bolts whether an AI company is actually following [its stated practices]".
- Implies: **standing access beats periodic audit.** Applied to the scenario: keep the intermediate artifacts (which passage produced which row) available for re-derivation at any time, rather than shipping only a polished final table.
- Caveat: this is about verifying an organisation's process adherence, not about verifying AI-produced research claims. Adjacent, not a direct match — the generalization is mine, not Amodei's.

---

### Gary Marcus (Professor Emeritus, NYU; "Marcus on AI")

**GM1. "Slop, productivity, and why the AI..."** — `opened (agent)`
- Date: 2026-06-07
- URL: https://garymarcus.substack.com/p/slop-productivity-and-why-the-ai
- Verbatim (quoted approvingly by Marcus from mathematicians, **not his own words**): "Current automated techniques can produce plausible but unreliable (or even incorrect) arguments which are difficult to distinguish from correct mathematical proofs."
- Implies: plausible and correct are hard to tell apart by inspection, so inspection alone is not a check.
- **Integrity note — important.** The researching agent reports that web-search summaries repeatedly attributed to Marcus's 2026-06-12 post a line like "the failure isn't the AI, it's the assumption that you no longer have to check it." The agent opened that page twice by two methods and the sentence **is not present**. It appears to be a search-engine-generated paraphrase circulating as a quote. This is a concrete, in-sample demonstration of the fabricated-attribution failure mode the whole scenario is about, and is arguably more useful to the paper than any quote would have been.

---

### Collective / institutional (clearly not an individual statement)

**N1. "Verification in the Age of AI Scientists," NeurIPS 2026 workshop** — `opened`
- Date: workshop 2026-12-11/12; page live 2026-09. Organizers include Marinka Zitnik (Harvard), Priya Donti (MIT), Emilien Dupont (Google DeepMind), Yuanqi Du (Microsoft Research).
- URL: https://ai4sciencecommunity.github.io/neurips26
- Verbatim: "The bottleneck for AI for Science is no longer hypothesis generation, it is verification" and "as AI Scientists scale beyond what humans can manually inspect, the central problem becomes which AI outputs deserve our scarce verification budget".
- Implies: **verification budgeting as a design problem.** Decide in advance which rows get scrutiny — highest-stakes numbers, claims that contradict each other, claims you intend to build on.

---

## 2. Pre-2026 background (clearly marked — NOT 2026 statements)

**P1. Andrej Karpathy, "Verifiability"** — `opened` (his own blog)
- Date: **2025-11-17**
- URL: https://karpathy.bearblog.dev/verifiability/
- Verbatim: "If a task/job is verifiable, then it is optimizable directly or via reinforcement learning, and a neural net can be trained to work extremely well." and "Software 2.0 easily automates what you can verify." and "If it is not verifiable, it has to fall out from neural net magic of generalization fingers crossed, or via weaker means like imitation."
- Why it matters: this is the origin of the line Karpathy delivers in the 2026 Sequoia talk (K1). Cite K1 for the 2026 date, P1 for the fuller argument.

**P2. Jason Wei (then OpenAI; now Meta Superintelligence Labs), "Asymmetry of verification and verifier's law"**
- Date: **2025-07-15**
- URL: https://www.jasonwei.net/blog/asymmetry-of-verification-and-verifiers-law
- Status: `snippet only` for the quote text. The researching agent opened Wei's blog *index* (https://www.jasonwei.net/blog) and confirmed the post's title and 2025 date, but did not re-fetch the post body; the circulating sentence "Asymmetry of verification–the idea that some tasks are much easier to verify than to solve–is becoming an important idea as we have RL that finally works generally" comes from his X announcement and was **not** read off an opened page. Do not quote it as verified.
- **Explicitly: none found for 2026.** Wei has 2026 posts ("What's left for humans?" 2026-08-16; "Cognitive reward shapes in sports and career" 2026-08-20) but the agent found none on verification or evals. The Stanford AI Club talk elaborating Verifier's Law is **2025-10**, not 2026.

**P3. Terence Tao, blog comment**
- Date: **2025-11**
- URL: quoted on his own curated summary page, https://teorth.github.io/tao-web/ai-views.html
- Verbatim: "I would caution against using AI tools without the ability to independently verify their output."
- Why it matters: the cleanest one-sentence statement of the rule, but it is 2025. Use T9 (Nature, 2026-05) for the 2026-dated equivalent.

**P4. Lilian Weng, "Extrinsic Hallucinations in LLMs"** — date **2024-07-07**, https://lilianweng.github.io/ — the canonical hallucination taxonomy, but well outside 2026. Use LW1–LW3 instead.

**P5. Ethan Mollick, "Using AI Right Now: A Quick Guide"** — date **2025-06-23** — contains his most quotable line on not being able to tell when the model is making things up. 2025, excluded.

**P6. Yoshua Bengio, "Introducing LawZero"** — date **2025-06-03**, https://yoshuabengio.org/en/blog/introducing-lawzero — pre-2026.

---

## 3. People with nothing found for 2026

| Person | Outcome |
|---|---|
| **Jason Wei** | **None found for 2026.** Blog index and "Thoughts" page both opened; his two 2026 posts are not about verification. Famous verifier's-law post is 2025-07-15. |
| **Sam Altman** | **None found for 2026** *on verification specifically.* His Sept 2026 Navier–Stokes reaction is capability praise, not a verification statement; the tweet itself would not load (HTTP 402). |
| **Demis Hassabis** | **None found for 2026.** Google I/O 2026 keynote, a Daedalus interview, Fortune (Feb 2026) and the Nature Co-Scientist paper were checked; all general AI-for-science enthusiasm, no statement on how humans should check AI research output. |
| **Ilya Sutskever** | **None found for 2026.** His clearest remarks on model reliability are in the Dwarkesh interview dated **late 2025**, outside scope. |
| **Gary Marcus** | **Weak.** Abundant 2026 activity on hallucinated citations, but no confirmed first-person verbatim quote prescribing a verification *method*. Best available (GM1) is him quoting mathematicians. A widely-circulated "quote" attributed to him was verified as **not present on the page**. |
| **Subbarao Kambhampati** | **No 2026 primary source.** CACM (KB1) is journalism quoting him; his X account returned 403; ICML 2026 talk has no obtainable transcript. |
| **Peter Scholze** | **None qualifying.** A 2026-05-01 quote via Peter Woit's blog is general anti-AI sentiment, not verification methodology; the verification framing around it is Woit's paraphrase. Excluded rather than stretched. |
| **Shreya Shankar (X posts)** | Blog item S1/S2 is solid; her 2026 X activity could not be opened (HTTP 402) and no quote is asserted from it. |
| **Percy Liang, Yann LeCun, Nathan Lambert** | Searched speculatively by me; no clean 2026-dated verification statement surfaced. Not pursued further. |

---

## 4. URLs opened vs. snippet-only

### Opened by me directly (quote read off the fetched page)
1. https://arxiv.org/abs/2608.16753 — Tao, ICM essay abstract
2. https://arxiv.org/html/2608.16753v1 — Tao, ICM essay full text
3. https://terrytao.wordpress.com/2026/08/18/palomar-a-registry-of-lean-verified-mathematics/
4. https://terrytao.wordpress.com/2026/09/10/crowdsourcing-a-list-of-general-resources-on-ai-and-mathematics/ — opened, **no usable verification quote**
5. https://www.dwarkesh.com/p/terence-tao
6. https://spectrum.ieee.org/ai-in-mathematics
7. https://teorth.github.io/tao-web/ai-views.html — Tao's own curated summary page
8. https://mathstodon.xyz/api/v1/statuses/116551624228986501 — Tao, via Mastodon API
9. https://mathstodon.xyz/api/v1/statuses/117035750548664654 — Tao, via Mastodon API
10. https://academy.openai.com/public/blogs/terence-tao-ai-is-ready-for-primetime-in-math-and-theoretical-physics-2026-03-06 — opened; returned paraphrase, **no verbatim Tao quote extracted, none asserted**
11. https://the-decoder.com/terence-tao-says-ai-drives-idea-generation-cost-to-near-zero-but-shifts-the-bottleneck-to-verification/ — secondary, used only as a pointer to the Dwarkesh source
12. https://karpathy.bearblog.dev/sequoia-ascent-2026/
13. https://karpathy.bearblog.dev/verifiability/ (pre-2026)
14. https://karpathy.bearblog.dev/blog/ — post index, used to confirm Karpathy has exactly one 2026 post
15. https://github.com/karpathy/autoresearch — **no verification quote found; none asserted**
16. https://simonwillison.net/2026/Aug/ — August archive index
17. https://simonwillison.net/2026/Aug/3/dont-be-a-meat-proxy/
18. https://simonwillison.net/2026/Aug/22/more-than-just-code-review/
19. https://simonwillison.net/2026/Sep/8/on-navier-stokes/ — **weak, no verification statement found**
20. https://lilianweng.github.io/posts/2026-07-04-harness/ — re-verified by me
21. https://hamelhusain.substack.com/p/its-hard-to-eval-is-a-product-smell — re-verified by me
22. https://xenaproject.wordpress.com/2026/09/04/flt-anthropic-has-beaten-me-to-it/ — re-verified by me
23. https://gowers.wordpress.com/2026/08/12/what-sort-of-maths-are-llms-good-at/ — re-verified by me
24. https://ai4sciencecommunity.github.io/neurips26

### Opened by a delegated research agent (not independently re-checked by me)
25. https://hamelhusain.substack.com/p/do-automated-evals-work
26. https://hamelhusain.substack.com/p/evals-skills-for-coding-agents
27. https://www.sh-reya.com/blog/ai-qual-analysis/
28. https://magazine.sebastianraschka.com/p/controlling-reasoning-effort-in-llms
29. https://hugobowne.substack.com/p/llm-architecture-in-2026-agent-harnesses
30. https://www.anthropic.com/research/formalizing-fermats-last-theorem
31. https://cacm.acm.org/news/thats-logical-teaching-llms-to-give-better-answers/
32. https://lawzero.org/en/research
33. https://fortune.com/2026/01/15/ai-godfather-yoshua-bengio-changes-view-on-ai-risks-sees-fix-becomes-optimistic-lawzero-board-of-advisors/
34. https://www.deeplearning.ai/the-batch/three-key-loops-for-building-great-software
35. https://www.oneusefulthing.org/p/the-overhang
36. https://www.oneusefulthing.org/p/agency-and-agents
37. https://garymarcus.substack.com/p/slop-productivity-and-why-the-ai
38. https://garymarcus.substack.com/p/you-cant-get-more-2026-than-that — opened, **circulating quote confirmed absent**
39. https://darioamodei.com/post/we-must-pace-the-frontier
40. https://www.jasonwei.net/blog and /thoughts — index pages, confirming absence

### Snippet only — no quote asserted from any of these
- https://x.com/karpathy/status/2049903821095354523 (HTTP 402)
- https://x.com/sama/status/2097380249910854023 (HTTP 402)
- https://x.com/rao2z, https://x.com/sh_reya, https://x.com/_jasonwei/* (402/403 — X is not fetchable)
- https://openai.com/index/navier-stokes-solution/ (HTTP 403)
- https://icml.cc/virtual/2026/79829 (listing only, no transcript)
- https://www.jasonwei.net/blog/asymmetry-of-verification-and-verifiers-law (post body not fetched; date confirmed via index)
- https://teorth.github.io/tao-web/slides/age-of-ai-icm-2026.pdf (image-based PDF, text not extractable)
- Nature, "'The job description is changing'" (2026-05) — the Tao quote was read off Tao's own curated page, not off Nature
- Secondary coverage not used for quotes: Fortune (Sept 2026), Axios, TheNextWeb, IBM Think, MIT Tech Review, Peter Woit's blog

---

## 5. Methodological notes for the paper

Three things this collection demonstrated about its own subject matter:

1. **A fabricated quote was found circulating in search results.** A sentence widely attributed to Gary Marcus's 2026-06-12 post is not on that page; it appears to be a search-engine paraphrase that acquired quotation marks. Caught only by opening the page.
2. **A near-miss paraphrase came back from a delegated agent.** Buzzard's description of his manual audit was reported in wording that did not match the page. Caught only by re-fetching. Both failures are exactly the scenario's concern, observed in the act of researching the scenario.
3. **X/Twitter is not fetchable** (HTTP 402/403 throughout), so no X post in this report is quoted. Several people's most pointed 2026 remarks likely live there and are simply unavailable to this method — a known and unclosed gap.

**Count (recounted, not estimated):** 42 quoted 2026-dated items across 15 named individuals (Tao 10, Karpathy 4, Willison 3, Weng 3, Husain 3, Buzzard 3, Shankar 2, Raschka 2, Gowers 2, Ng 2, Mollick 2, Bengio 2, Kambhampati 1, Amodei 1, Marcus 1) plus 1 collective statement, plus 6 clearly-marked pre-2026 background entries. Four further pages were opened and returned no usable quote (Karpathy/autoresearch, Willison/Navier-Stokes, Tao/crowdsourcing, OpenAI Academy); these are listed rather than dropped, so the absence is on the record.

This exceeds the 15-30 target. The overshoot is concentrated in Tao, who produced far more 2026 material on exactly this question than anyone else; his 10 items could be cut to 4 (T1, T6, T9, T10) without losing an argument.
