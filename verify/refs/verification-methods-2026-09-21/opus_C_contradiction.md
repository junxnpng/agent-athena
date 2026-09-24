# 모순 탐지 · 조건 인지형 주장 비교 · 문서 내 일관성 검사 — 확립된 방법 조사

작성일 2026-09-21. 대상 층: Layer 5(상향 조건 드리프트), Layer 6(문서 내 일관성·산술), Layer 7(정의 비교가능성), 그리고 교차 논문 모순 스윕.

---

## 1. 한 문단 요약

이 팀이 세우려는 7층 중 5·6·7층과 모순 스윕은 모두 이미 다른 분야에서 이름이 붙은 문제다. (a) 교차 논문 모순은 과학 주장 검증(SciFact/MultiVerS의 SUPPORTS·REFUTES)과, 더 정확히는 **SciFact-Open**이 보고한 "충돌 증거(conflicting evidence)"와 "specificity mismatch" 현상에 대응한다 — SciFact-Open은 충돌의 상당수가 진짜 불일치가 아니라 주장·증거의 **범위(구체성) 차이**였다고 보고한다. (b) 조건을 실어 나르는 주장 표현은 의학의 PICO/ICO 스키마, **SciClaim**의 qualifier 노드, **Claimify**의 모호성 플래그, **Decontextualization**, **Defeasible NLI**의 strengthener/weakener 개념이 이미 형식을 제공한다. (c) "값 차이를 조건 차이로 설명한다"의 정식 대응물은 메타분석의 **subgroup analysis / meta-regression**이며, Cochrane Handbook은 이 절차의 관찰적 성격·다중성·사전명세 요구를 명시한다. (d) 시스템 분야에서 같은 지표 이름이 다른 정의를 숨기는 문제는 **SoK: Benchmarking Flaws in Systems Security**(22개 결함)와 캐시 문헌의 OHR/BHR 구분이 직접 다룬다. (e) 요약 시 조건이 떨어지는 현상은 2025년 Royal Society Open Science의 **generalization bias** 논문이 실측했다. (f) 본문·표 숫자 대조는 **statcheck / GRIM / SPRITE**의 계보와 2026년의 **sciwrite-lint**, **arXiVeri**가 도구화했다.

---

## 2. 방법별 절

### 2.1 과학 문헌의 모순 · 불일치 탐지

**SciFact (Fact or Fiction: Verifying Scientific Claims)** — Wadden 외, EMNLP 2020, <https://aclanthology.org/2020.emnlp-main.609/>. 초록 인용: *"We introduce scientific claim verification, a new task to select abstracts from the research literature containing evidence that SUPPORTS or REFUTES a given scientific claim, and to identify rationales justifying each decision. To study this task, we construct SciFact, a dataset of 1.4K expert-written scientific claims paired with evidence-containing abstracts annotated with labels and rationales."* → 모순 스윕의 라벨 체계 원형. **매핑(추론)**: 팀의 excerpt record는 이미 "verbatim quote + paraphrase + links" 구조라 rationale 개념을 갖고 있으므로, 주장쌍에 SUPPORTS/REFUTES/NEI 3라벨을 붙이고 **rationale(어느 문장이 근거인지)을 반드시 함께 저장**하는 관행을 그대로 차용할 수 있다.

**MultiVerS** — Wadden 외, Findings of NAACL 2022, <https://aclanthology.org/2022.findings-naacl.6/>. 전체 문서 문맥(Longformer)을 공유 인코딩해 라벨과 rationale을 멀티태스크로 예측. 초록: *"...to label scientific documents which Support or Refute an input claim, and to select evidentiary sentences (or rationales) justifying each predicted label."* **매핑(추론)**: 조건이 초록이 아니라 본문 실험 설정에 적혀 있는 시스템 논문에서는 문장 단위가 아닌 전체 문서 문맥 판정이 필수다.

**SciFact-Open** — Wadden 외, Findings of EMNLP 2022, <https://aclanthology.org/2022.findings-emnlp.347/> (PDF <https://arxiv.org/abs/2210.13777>). **이 팀에 가장 직접적인 선행 연구.** 논문 본문 인용: *"Of the 81 claims in SCIFACT-OPEN with at least 2 ECAPs, 16 of them (20%) have conflicting evidence."* 그리고 바로 이어서 *"In examining these conflicts, we found that they were often a result of specificity mismatches."* 구체성 분류 표(206 ECAPs 기준)는 Evidence matches claim 115 / Evidence more specific than claim 53 / Evidence more general than claim 18 / Evidence closely related to claim 20 이며, 캡션은 *"Specificity mismatches are common, comprising 44% of annotated examples."* 라 적는다. 코퍼스는 *"500K research abstracts"*, 신규 주장 279개, 기존 모델은 *"performance drops of at least 15 F1"*. **매핑**: 모순 스윕의 3분류("different definition / different condition / genuine conflict")를 그대로 정당화하는 실증치. **(추론)** SciFact-Open이 보인 44%/20% 비율은 도메인이 다르므로 KV-cache 코퍼스에 그대로 옮길 수 없으나, "충돌 후보의 다수가 조건 차이"라는 **기대 분포**를 설계 전제로 삼을 근거는 된다.

**ContraDoc** — Li, Raheja, Kumar, NAACL 2024, <https://aclanthology.org/2024.naacl-long.362/> (arXiv 2023-11-15, <https://arxiv.org/abs/2311.09182>). 문서 **내부** 자기모순 데이터셋. 본문 인용: *"CONTRADOC contains 449 self-contradictory ... and 442"* (non-contradictory), 문서 길이는 *"range from 100 tokens to 2200"*, 범위 라벨은 *"Our dataset contains 73, 220, and 155 documents with intra, local, and global"* 모순. 유형 8종에 **Numeric**("Number mismatch or number ...")이 포함된다. 초록: *"While GPT4 performs the best and can outperform humans on this task, we find that it is still unreliable and struggles with self-contradictions that require more nuance and context."* **매핑**: Layer 6의 "body vs table vs caption vs abstract" 검사는 정확히 ContraDoc의 **global scope** 문제다. **(추론)** 전 논문을 한 번에 던지는 단일 프롬프트는 global 모순에서 성능이 떨어지므로, 팀은 (초록, 표 캡션, 본문 수치 문장)만 추출해 **짧은 후보쌍으로 축약한 뒤** 판정하는 편이 유리하다.

**ClaimDiff** — Ko 외, Findings of ACL 2023, <https://arxiv.org/abs/2205.12221>. *"2,941 annotated claim pairs from 268 news articles"*, 그리고 *"...strong baselines struggle to detect them, showing over a 19% absolute gap"*. 참/거짓이 아니라 한 주장이 다른 주장을 **강화/약화**하는지를 라벨링. **매핑**: 모순 스윕에서 "정반대 방향"만이 아니라 "같은 방향인데 세기가 다름"을 잡는 축.

**LLM을 모순 검증자로 쓰는 최근 두 편** — *Contradiction Detection in RAG Systems* (Gokul 외, arXiv 2025-03-31, <https://arxiv.org/abs/2504.00180>)는 검색 문서 집합 내 모순 검증을 평가하며 초록에 수치 없이 *"larger models generally perform better"* 와 CoT 효과의 모델 의존성만 보고한다. *Improved Evidence Extraction and Metrics for Document Inconsistency Detection with LLMs* (Tan 외, arXiv 2026-01-06, 2026-04-08 개정, <https://arxiv.org/abs/2601.02627>)는 "redact-and-retry framework with constrained filtering" 과 증거 추출 전용 지표를 제안(초록에 수치 없음). **매핑(추론)**: 모순을 "있다/없다"로만 채점하지 말고 **증거 span 회수율**을 별도 채점할 것.

**생의학 모순 코퍼스**: Alamri & Stevenson, *A corpus of potentially contradictory research claims from cardiovascular research abstracts*, Journal of Biomedical Semantics 2016, DOI 10.1186/s13326-016-0083-z — **URL을 열지 못했다**(Springer 인증 리다이렉트). 검색 요약은 "259 abstracts / 24 systematic reviews / 4 cardiovascular topics"라고 하나 **원문 확인 실패이므로 수치는 신뢰하지 말 것**. 또한 `arXiv:2606.11208` BioDivergence(맥락적 모순 taxonomy)는 **2026-08-30 철회(withdrawn)** 되었으므로 인용해서는 안 된다.

### 2.2 조건을 실어 나르는 구조화된 주장 표현

**PICO / ICO — Evidence Inference** — Lehman, DeYoung, Barzilay, Wallace, NAACL 2019, <https://aclanthology.org/N19-1371/>. 초록: 과제는 *"intervention, comparator, and outcome"* 3요소 질의에 대해 결과 방향(증가/감소/차이없음)을 추론하는 것이며 코퍼스는 *"10,000+ prompts coupled with full-text articles describing RCTs."* **매핑**: 팀의 record를 (변수, 패턴) 대신 **(population, intervention, comparator, outcome, effect-direction)** 5튜플로 정규화하면, 비교 가능성 판정이 "C(=baseline)가 같은가?"라는 단일 질문으로 환원된다. **(추론)** KV-cache 도메인에서 comparator는 곧 baseline 설정(no-reuse? prefix-cache-on? 다른 스케줄러?)이며, 이것이 팀이 말하는 denominator 문제의 절반이다.

**SciClaim** — Magnusson & Friedman, EMNLP 2021, arXiv 2021-09-21, <https://arxiv.org/abs/2109.10453>. 초록: *"our novel graph annotation schema incorporates not only coarse-grained entity spans as nodes and relations as edges between them, but also fine-grained attributes that modify entities and their relations, for a total of 12,738 labels in the corpus"*, 그리고 *"SciClaim captures causal, comparative, predictive, statistical, and proportional associations over experimental variables along with their qualifications, subtypes, and evidence."* 엔티티 타입에 **Qualifier**(주장의 적용 범위를 제한하는 span)와 **Epistemic**(믿음 상태)이 따로 있다. **매핑**: Layer 7의 "definition tag"를 자유 텍스트 caveat가 아니라 **그래프 노드 타입**으로 두라는 선례.

**Claimify (Towards Effective Extraction and Evaluation of Factual Claims)** — Metropolitansky & Larson, arXiv 2025-02-15(v2 2025-06-06), <https://arxiv.org/abs/2502.10855>; Microsoft Research 블로그 2025-03-19, <https://www.microsoft.com/en-us/research/blog/claimify-extracting-high-quality-claims-from-language-model-outputs/>. 블로그 인용: *"99% of claims extracted by Claimify are entailed by their source sentence"*, 그리고 문맥이 모호성을 해소하지 못하면 추측하지 않고 **"Cannot be disambiguated"** 로 표시한다. arXiv 초록 자체에는 수치가 없다. **매핑**: Layer 5의 실행 규칙 — 요약 문장이 record가 지지하지 않는 해석을 요구하면 **문장을 쓰지 말고 "판정 불가"로 남긴다**.

**Decontextualization** — Choi 외, TACL 2021, <https://aclanthology.org/2021.tacl-1.27/> (열지 않음; arXiv <https://arxiv.org/abs/2102.05169>). 문장을 문맥 밖에서도 해석 가능하도록 의미 보존 재작성. **매핑(추론)**: verbatim quote를 요약에 옮길 때 "홀로 서면 어떤 조건이 사라지는가"를 명시적 재작성 단계로 만들면 Layer 5가 기계화된다.

**Defeasible NLI (δ-NLI)** — Rudinger 외, Findings of EMNLP 2020, <https://aclanthology.org/2020.findings-emnlp.418/>. 초록: *"Defeasible inference is a mode of reasoning in which an inference (X is a bird, therefore X flies) may be weakened or overturned in light of new evidence (X is a penguin)."* update를 **strengthener / weakener** 로 분류하는 과제, 생성 모델은 *"up to 68% of the time"* 성공. **매핑**: 조건 diff를 "값이 다르다"가 아니라 "조건 U가 주장 H를 약화시키는가"로 형식화하는 정확한 언어. **(추론)** 모순 스윕의 auto-diff 결과를 weakener/strengthener/무관 3분류로 라벨링하면 "different condition"과 "genuine conflict"의 경계가 조작적으로 정의된다.

**Wikidata qualifiers / hyper-relational KG** — *Handling Wikidata Qualifiers in Reasoning*, arXiv 2023-04-06, <https://arxiv.org/abs/2304.03375> (열지 않음). 주요 triple에 qualifier-value 쌍을 붙여 **유효 맥락(validity context)** 을 표현. **매핑(추론)**: (variable, pattern, value)에 (denominator, population, window, ideal/realized) qualifier를 붙이면 qualifier 집합 불일치 시 자동 non-comparable 플래그가 가능하다.

### 2.3 이질성을 조건으로 설명하는 메타분석 관행

**Cochrane Handbook, Chapter 10 (Analysing data and undertaking meta-analyses)** — <https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-10> (열어서 확인). §10.10.2의 I² 정의: *"This describes the percentage of the variability in effect estimates that is due to heterogeneity rather than sampling error (chance)."* 해석 가이드는 *"0% to 40%: might not be important"*, *"30% to 60%: may represent moderate heterogeneity"*, *"50% to 90%: may represent substantial heterogeneity"*, *"75% to 100%: considerable heterogeneity"* 이고, *"The importance of the observed value of I² depends on (1) magnitude and direction of effects, and (2) strength of evidence for heterogeneity."* §10.11은 이질성 탐구 수단으로 **subgroup analysis**와 **meta-regression**을 둔다. §10.11.3의 경고: subgroup 비교는 무작위화의 보호를 받지 못하는 **관찰적** 비교이고, *"many characteristics vary across studies from which one may choose"* 라는 다중성 문제가 있으며, *"Reliable conclusions can only be drawn from analyses that are truly pre-specified before inspecting the studies' results."*

**매핑**: 팀의 "(b) 조건 차이로 모순을 설명한다"는 정확히 subgroup analysis다. 그러므로 Cochrane의 세 가지 규율을 그대로 수입해야 한다 — (1) 조건 축(population/denominator/workload/model/capacity/metric)을 **스윕 전에 사전 등록**할 것, (2) 사후에 찾아낸 설명은 "가설"로만 표기할 것, (3) 조건 축 하나당 충분한 논문 수가 없으면 설명을 확정하지 말 것. **(추론)** 41편 규모에서 조건 축이 6개면 Cochrane이 회귀에 권하는 "축당 10편" 기준에 미달하므로, 이 코퍼스에서 조건 설명은 **정성적 subgroup 서술**로 제한하고 정량 meta-regression은 시도하지 않는 것이 맞다.

### 2.4 시스템 연구의 지표·분모 비교가능성

**SoK: Benchmarking Flaws in Systems Security** — van der Kouwe, Heiser, Andriesse, Bos, Giuffrida, IEEE EuroS&P 2019, PDF <https://download.vusec.net/papers/benchmarking-crimes_eurosp19.pdf> (열어서 텍스트 추출 확인). 초록: *"we identify 22 benchmarking flaws that threaten the validity of systems security evaluations, and survey 50 defense papers published in top venues ... tier-1 papers contain an average of five benchmarking flaws and we find only a single paper in our sample without any benchmarking flaws."* 이 팀에 직접 걸리는 결함 코드:
- **B3: bad math** — *"refers to incorrect computations with overhead numbers"*, 예시 인용: *"the difference between 10% overhead and 20% overhead is presented as 10% more overhead, while it is actually 100% more (i.e., 2×)"*, 그리고 5s→20s를 *"a 75% slowdown ... rather than a 300% slowdown"* 로 제시하는 경우.
- **B5: incorrect averaging across benchmark scores** — 비율(ratio)을 산술평균/중앙값으로 묶는 것. 본문: *"Only the geometric mean is appropriate for averaging overhead ratios."*
- **B2: throughput degraded by x% ⇒ overhead is x%** — 지표 변환에서 정의가 바뀌는 전형.
- **D1: no proper baseline** — *"Absolute performance numbers with no baseline to compare against cannot be compared between systems."*
- **A2 / F3 / F4**(benchmark subsetting, subbenchmarks not listed, relative numbers only) — 분모·모집단이 공개되지 않아 비교가 불가능해지는 경우. A2에 대해 *"if different papers use subsets, the overall slowdown ... making those numbers incomparable."*

**매핑**: Layer 6은 B3/B5를, Layer 7은 B2/D1/A2/F3/F4를 그대로 체크 항목으로 쓸 수 있다. 원조는 Gernot Heiser의 목록 <https://gernot-heiser.org/benchmarking-crimes.html>(논문 참고문헌 [1]; 나는 열지 않음).

**Mogul, "Brittle metrics in operating systems research"**, HotOS 1999, <https://ieeexplore.ieee.org/document/798383/> — **유료 벽으로 열지 못했다.** 위 SoK 논문이 참고문헌 [19]로 인용하고 있다는 사실만 확인. 주장 내용은 인용하지 않는다.

**캐시 지표의 분모 문제** — AdaptSize (Berger 외, USENIX NSDI 2017, <https://www.usenix.org/conference/nsdi17/technical-sessions/presentation/berger>, 열지 않음)가 **object hit ratio (OHR)** 와 **byte hit ratio (BHR)** 를 분리해 부르는 관행의 대표 사례다. 또한 Qiu, Yang, Harchol-Balter, *Can Increasing the Hit Ratio Hurt Cache Throughput?*, arXiv 2024-04-24, <https://arxiv.org/abs/2404.16219> (열어서 확인)은 *"increasing the hit ratio can actually hurt the throughput (and response time) for many caching algorithms"* 라고 보고한다. **매핑**: "hit rate"가 token/request/block 중 무엇을 세는지에 따라 값이 달라진다는 팀의 문제의식은 캐시 문헌에서 이미 OHR vs BHR로 이름이 붙어 있고, **hit ratio 개선이 곧 성능 개선이 아니라는 점**까지 출판된 반례가 있다. **(추론)** 따라서 비교 행에 넣기 전 요구할 정의 태그는 최소 4개다: 세는 단위(token/request/block/byte), 분모에 포함되는 요청의 정의(uncacheable을 넣는가), 창(window), ideal(오프라인 최적) vs realized.

**REFORMS** — Kapoor 외 19인, Science Advances 2024, DOI <https://doi.org/10.1126/sciadv.adk3452>, 프리프린트 arXiv 2023-08-15 <https://arxiv.org/abs/2308.07832> (arXiv 확인). *"a checklist containing 32 questions"*, 8개 모듈, 19인 합의. **NeurIPS ML Reproducibility Checklist / Pineau 외, JMLR 2021** <https://arxiv.org/abs/2003.12206>(열지 않음)도 metric 정의 기술을 항목으로 둔다. **매핑(추론)**: Layer 7의 정의 태그 스키마를 새로 만들지 말고 이 두 체크리스트의 항목명을 재사용할 것. 비율=기하평균·처리율=조화평균 관행의 표준 출처는 **Statistically Rigorous Java Performance Evaluation** (Georges 외, OOPSLA 2007, <https://dl.acm.org/doi/10.1145/1297027.1297033>, 열지 않음)이며 SoK B5와 짝을 이룬다.

### 2.5 LLM 요약의 과일반화 · qualifier 소실

**Generalization bias in large language model summarization of scientific research** — Uwe Peters, Benjamin Chin-Yee, *Royal Society Open Science* 12(4):241776, 2025년 4월, DOI <https://doi.org/10.1098/rsos.241776>, 프리프린트 arXiv 2025-03-28 <https://arxiv.org/abs/2504.00025> (arXiv 열어서 확인). 수치: 10개 LLM, **4,900개 요약** 비교. 명시적 정확성 프롬프트를 주어도 DeepSeek·ChatGPT-4o·LLaMA 3.3 70B가 *"in 26 to 73% of cases"* 과일반화. 사람 요약 대비 *"LLM summaries were nearly five times more likely to contain broad generalizations (OR = 4.85, 95% CI [3.06, 7.70])"*. 신형 모델이 구형보다 나빴다. 저자 권고는 temperature를 낮출 것, 과일반화 정확도로 벤치마킹할 것, 그리고 **"부정확을 피하라"는 식의 프롬프트 표현을 오히려 피할 것**.

**매핑**: Layer 5의 존재 이유를 정량화한 유일한 직접 증거. **(추론)** 이 논문이 관찰한 "정확성 강조 프롬프트가 역효과"라는 결과는, 팀이 요약 단계에서 프롬프트 문구로 조건 보존을 해결하려는 시도를 **검증 패스 없이는 신뢰하지 말라**는 뜻이다. 즉 Layer 5는 생성 측 프롬프트가 아니라 **사후 대조 검사**로 구현해야 한다.

**Semi-Supervised Exaggeration Detection of Health Science Press Releases** — Wright & Augenstein, EMNLP 2021, <https://aclanthology.org/2021.emnlp-main.845/> (열지 않음; arXiv <https://arxiv.org/abs/2108.13493>). 보도자료와 원논문 초록 쌍에 대해 **주장 강도(claim strength)** 를 라벨링하고 과장 여부를 판정. **매핑(추론)**: 팀의 (요약 문장, 인용된 record) 쌍은 정확히 (press release, abstract) 쌍과 같은 구조이므로, 이 과제의 "원문 강도 → 요약 강도" 비교 프레이밍을 그대로 옮길 수 있다.

### 2.6 논문 본문·표 숫자 자동 대조

**statcheck** — Nuijten, Hartgerink, van Assen, Epskamp, Wicherts, *The prevalence of statistical reporting errors in psychology (1985–2013)*, Behavior Research Methods 2016, DOI 10.3758/s13428-015-0664-2, <https://pmc.ncbi.nlm.nih.gov/articles/PMC5101263/> (열어서 확인). *"over 250,000 p-values"* 검사, *"half of all published psychology papers that use NHST contained at least one p-value that was inconsistent"*, *"One in eight papers contained a grossly inconsistent p-value"* (결과절 기준 49.6% / 12.9%). 후속: Nuijten & Epskamp, Research Synthesis Methods 2020, DOI 10.1002/jrsm.1408 (Wiley 403 — **열지 못함**); Nuijten & Wicherts, AMPPS 2024, DOI 10.1177/25152459241258945 (열지 않음) — peer review에 statcheck를 넣은 저널에서 불일치가 더 가파르게 감소.

**GRIM / SPRITE** — Brown & Heathers, *The GRIM Test*, SPPS 2017, DOI 10.1177/1948550616673876 (열지 않음; PeerJ 프리프린트 <https://peerj.com/preprints/2064/>)은 보고된 평균이 표본 크기와 산술적으로 양립 가능한지 검사하고, SPRITE(Heathers 외, PeerJ Preprints 2018, <https://peerj.com/preprints/26968/>, 열지 않음)는 평균·SD·N·범위로부터 가능한 원자료를 역구성한다. **매핑**: Layer 6의 파생값 재계산·component sum 검사와 같은 계열. **(추론)** 시스템판 GRIM은 "보고된 비율이 보고된 분모로 나누어떨어지는가"이며 41편에 즉시 적용 가능한 가장 값싼 검사다.

**sciwrite-lint** — Sergey V Samsonau, arXiv 2026-04-09(2026-05-24 개정), <https://arxiv.org/abs/2604.08501> (열어서 확인). 초록 인용: 내부 일관성 검사로 *"numbers in text vs. tables, abstract vs. body, figure captions vs. content, statistical results vs. their verbal interpretation, plus structural cross-references (dangling cites, orphan references)"* 를 수행하고, *"evaluate on 30 unseen papers (arXiv and bioRxiv) with error injection and LLM-adjudicated false-positive analysis"*. **매핑**: Layer 6의 사실상 완전한 사양서. 평가 방법론(오류 주입 + 오탐 판정)도 그대로 차용 가능.

**arXiVeri** — Shin, Xie, Albanie, arXiv 2023-06-13, <https://arxiv.org/abs/2306.07968> (열어서 확인). *"the novel task of automatic table verification (AutoTV), in which the objective is to verify the accuracy of numerical data in tables by cross-referencing cited sources"*, 하위 과제는 table matching과 cell matching. 초록에 성능 수치 없음. **매핑**: 2차 인용 검증(논문 A의 표가 논문 B의 표 수치를 옮겼는가)에 직결 — 팀 record의 `kind: secondary citation`이 바로 이 과제다.

**SciTab / Table-Text Alignment** — SciTab(Lu 외, EMNLP 2023, <https://aclanthology.org/2023.emnlp-main.483/>, 열지 않음)은 실제 논문에서 뽑은 1.2K 주장 + 표 증거로 compositional reasoning을 요구한다. Table-Text Alignment(Ho 외, arXiv 2025-06-12, 2025-09-17 개정, <https://arxiv.org/abs/2506.10486>, 확인)는 여기에 셀 단위 rationale을 사람 주석으로 덧붙이고 *"most LLMs, while often predicting correct labels, fail to recover human-aligned rationales"* 라고 보고한다. **매핑**: Layer 6은 "라벨이 맞았는가"가 아니라 **"어느 셀을 근거로 삼았는가"** 를 채점해야 한다.

### 2.7 수치 주장 팩트체킹 (산술 재검증 관행)

**QuanTemp** — Venktesh V, Anand, Anand, Setty, SIGIR 2024, arXiv 2024-03-25, <https://arxiv.org/abs/2403.17169> (열어서 확인). 초록: *"we release QuanTemp, a diverse, multi-domain dataset focused exclusively on numerical claims"*, 그리고 *"our best baselines achieve a macro-F1 of 58.32"*. (검색 요약에 나온 "15,514 claims / 423,320 evidence snippets"는 초록에서 직접 확인하지 못했으므로 **미검증**으로 둔다.) **FEVEROUS** — Aly 외, NeurIPS 2021 Datasets & Benchmarks, <https://arxiv.org/abs/2106.05707> (열지 않음): 87,026 주장을 문장 + 표 셀 증거로 검증. **매핑**: 수치 주장은 claim decomposition 후 개별 산술 단계로 쪼개 검증하는 것이 표준이라는 관행적 근거. **(추론)** 팀의 `numbers` 필드는 "값 + 단위 + 분모 + 도출식"으로 분해해 저장해야 재검증이 가능하다.

---

## 3. 층 · 스윕 대응표

| 층 / 스윕 | 방법 | 출처 | 구체적 용법 |
|---|---|---|---|
| **L5 상향 조건 드리프트** | Generalization bias 측정 | Peters & Chin-Yee 2025 (RSOS) | 요약 문장별 "원문보다 넓은가" 이진 판정 + OR 기반 보고 |
| L5 | Exaggeration / claim strength | Wright & Augenstein, EMNLP 2021 | (요약, record) 쌍을 (press release, abstract) 쌍으로 취급해 강도 비교 |
| L5 | Claimify "Cannot be disambiguated" | Metropolitansky & Larson 2025 | 조건이 해소 안 되면 요약 문장을 쓰지 않고 보류 |
| L5 | Decontextualization | Choi 외, TACL 2021 | 인용을 홀로 서게 재작성하며 잃는 조건을 노출 |
| L5 | Specificity mismatch 유형학 | SciFact-Open, Findings EMNLP 2022 | more specific / more general / closely related 4분류로 드리프트 라벨링 |
| **L6 문서 내 일관성·산술** | sciwrite-lint 검사 항목 | arXiv 2604.08501 (2026) | numbers-vs-tables, abstract-vs-body, caption-vs-content 그대로 구현 |
| L6 | statcheck 계보 | Nuijten 외 2016 | 보고된 파생값을 원자료로 재계산해 불일치 플래그 |
| L6 | GRIM / SPRITE | Brown & Heathers 2017 / Heathers 외 2018 | 비율 ↔ 분모 정수 정합성, 합계 = 부분합 검사 |
| L6 | ContraDoc scope(intra/local/global) | Li 외, NAACL 2024 | 초록↔본문 불일치를 global scope 사례로 분류·평가 |
| L6 | AutoTV (arXiVeri) | Shin 외 2023 | `kind: secondary citation` record의 표 셀 대조 |
| L6 | SciTab + cell-level rationale | Lu 외 2023 / Ho 외 2025 | 판정과 함께 근거 셀을 요구해 우연히 맞은 판정 제거 |
| L6 | B3 bad math / B5 incorrect averaging | SoK EuroS&P 2019 | %p vs 배수 혼동, 비율의 산술평균 금지 |
| **L7 정의 비교가능성** | OHR vs BHR 구분 | AdaptSize NSDI 2017 | hit rate에 단위 태그(token/request/block/byte) 강제 |
| L7 | hit ratio ≠ throughput | Qiu 외 arXiv 2404.16219 | 지표 간 대리(proxy) 가정을 명시적으로 기록 |
| L7 | D1 no proper baseline / F4 relative only | SoK EuroS&P 2019 | baseline 미기재 값은 비교 행 진입 금지 |
| L7 | A2 subsetting / F3 subbenchmarks | SoK EuroS&P 2019 | 모집단(어떤 워크로드 부분집합)이 다르면 non-comparable |
| L7 | REFORMS 32항목 / NeurIPS 체크리스트 | Kapoor 외 2024 / Pineau 외 2021 | 정의 태그 필드명을 기존 체크리스트에서 차용 |
| L7 | SciClaim Qualifier·Epistemic 노드 | Magnusson & Friedman 2021 | 조건을 자유 텍스트가 아닌 타입 있는 노드로 저장 |
| L7 | hyper-relational qualifier | arXiv 2304.03375 | qualifier 집합 불일치 시 자동 non-comparable |
| **모순 스윕** | SUPPORTS/REFUTES/NEI + rationale | SciFact 2020, MultiVerS 2022 | 주장쌍 라벨 체계 + 근거 문장 동반 저장 |
| 모순 스윕 | conflicting evidence 정의 | SciFact-Open 2022 | "한 주장이 한쪽에서 지지·다른 쪽에서 반박" 조작적 정의 |
| 모순 스윕 | strengthen/weaken 축 | ClaimDiff 2023 | 방향 반전 외에 "세기 차이"도 잡음 |
| 모순 스윕 | strengthener / weakener update | Defeasible NLI 2020 | condition auto-diff 결과를 약화/강화/무관으로 분류 |
| 모순 스윕 | subgroup analysis / meta-regression, I² | Cochrane Handbook ch.10 | 조건 축 사전 등록, 사후 설명은 "가설"로 표기 |
| 모순 스윕 | PICO / ICO 정규화 | Lehman 외 NAACL 2019 | comparator(=baseline) 동일성으로 비교가능성 1차 필터 |
| 모순 스윕 | RAG 문맥 모순 검증자 | Gokul 외 2025 | LLM을 검증자로 쓸 때 CoT 효과가 모델 의존적임에 주의 |

---

## 4. 출처 표

| # | 제목 | 저자 / 기관 | 연도 | URL | 열어서 확인 |
|---|---|---|---|---|---|
| 1 | Fact or Fiction: Verifying Scientific Claims (SciFact) | Wadden 외 / AI2 · UW | 2020 (EMNLP) | https://aclanthology.org/2020.emnlp-main.609/ | ✅ |
| 2 | MultiVerS | Wadden 외 / AI2 | 2022 (Findings NAACL) | https://aclanthology.org/2022.findings-naacl.6/ | ✅ |
| 3 | SciFact-Open | Wadden 외 / AI2 | 2022 (Findings EMNLP) | https://aclanthology.org/2022.findings-emnlp.347/ · https://arxiv.org/abs/2210.13777 | ✅ (PDF 본문 확인) |
| 4 | ContraDoc | Li, Raheja, Kumar / UT Austin · Grammarly | 2023-11 arXiv, 2024 NAACL | https://aclanthology.org/2024.naacl-long.362/ · https://arxiv.org/abs/2311.09182 | ✅ (PDF 본문 확인) |
| 5 | ClaimDiff | Ko 외 / KAIST 외 | 2022-05 arXiv, 2023 Findings ACL | https://arxiv.org/abs/2205.12221 | ✅ |
| 6 | Contradiction Detection in RAG Systems | Gokul, Tenneti, Nakkiran / Amazon | 2025-03-31 | https://arxiv.org/abs/2504.00180 | ✅ |
| 7 | Improved Evidence Extraction and Metrics for Document Inconsistency Detection with LLMs | Tan 외 | 2026-01-06 (rev 2026-04-08) | https://arxiv.org/abs/2601.02627 | ✅ |
| 8 | A corpus of potentially contradictory research claims from cardiovascular abstracts | Alamri & Stevenson / Sheffield | 2016 | https://doi.org/10.1186/s13326-016-0083-z | ❌ (Springer 인증 리다이렉트) |
| 9 | BioDivergence | Hossain 외 / UCF | 2026-04-23, **2026-08-30 철회** | https://arxiv.org/abs/2606.11208 | ✅ (철회 확인) |
| 10 | Inferring Which Medical Treatments Work from Reports of Clinical Trials | Lehman, DeYoung, Barzilay, Wallace / MIT · Northeastern | 2019 (NAACL) | https://aclanthology.org/N19-1371/ | ✅ |
| 11 | SciClaim (Extracting Fine-Grained Knowledge Graphs of Scientific Claims) | Magnusson & Friedman / SIFT | 2021-09-21 (EMNLP 2021) | https://arxiv.org/abs/2109.10453 | ✅ |
| 12 | Towards Effective Extraction and Evaluation of Factual Claims (Claimify) | Metropolitansky & Larson / Microsoft | 2025-02-15 (v2 2025-06-06) | https://arxiv.org/abs/2502.10855 | ✅ |
| 13 | Claimify 블로그 | Microsoft Research | 2025-03-19 | https://www.microsoft.com/en-us/research/blog/claimify-extracting-high-quality-claims-from-language-model-outputs/ | ✅ |
| 14 | Decontextualization: Making Sentences Stand-Alone | Choi 외 / Google · UT Austin | 2021 (TACL) | https://aclanthology.org/2021.tacl-1.27/ | ❌ (미열람) |
| 15 | Thinking Like a Skeptic: Defeasible Inference in NL (δ-NLI) | Rudinger 외 / AI2 · UMD | 2020 (Findings EMNLP) | https://aclanthology.org/2020.findings-emnlp.418/ | ✅ |
| 16 | Handling Wikidata Qualifiers in Reasoning | — | 2023-04 | https://arxiv.org/abs/2304.03375 | ❌ (미열람) |
| 17 | Cochrane Handbook ch.10 Analysing data and undertaking meta-analyses | Deeks, Higgins, Altman / Cochrane | current (v6.x) | https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-10 | ✅ |
| 18 | SoK: Benchmarking Flaws in Systems Security | van der Kouwe, Heiser, Andriesse, Bos, Giuffrida | 2019 (IEEE EuroS&P) | https://download.vusec.net/papers/benchmarking-crimes_eurosp19.pdf | ✅ (PDF 본문 확인) |
| 19 | Gernot's List of Systems Benchmarking Crimes | Heiser / UNSW | 2010– | https://gernot-heiser.org/benchmarking-crimes.html | ❌ (미열람) |
| 20 | Brittle metrics in operating systems research | Mogul / Compaq WRL | 1999 (HotOS) | https://ieeexplore.ieee.org/document/798383/ | ❌ (유료 벽) |
| 21 | AdaptSize | Berger 외 / CMU · Akamai | 2017 (NSDI) | https://www.usenix.org/conference/nsdi17/technical-sessions/presentation/berger | ❌ (미열람) |
| 22 | Can Increasing the Hit Ratio Hurt Cache Throughput? | Qiu, Yang, Harchol-Balter / CMU | 2024-04-24 | https://arxiv.org/abs/2404.16219 | ✅ |
| 23 | REFORMS | Kapoor 외 19인 / Princeton 외 | 2023-08 arXiv, 2024 Science Advances | https://arxiv.org/abs/2308.07832 · https://doi.org/10.1126/sciadv.adk3452 | ✅ (arXiv) |
| 24 | Improving Reproducibility in ML Research (NeurIPS checklist) | Pineau 외 / McGill · Meta | 2020 arXiv, 2021 JMLR | https://arxiv.org/abs/2003.12206 | ❌ (미열람) |
| 25 | Statistically Rigorous Java Performance Evaluation | Georges, Buytaert, Eeckhout / Ghent | 2007 (OOPSLA) | https://dl.acm.org/doi/10.1145/1297027.1297033 | ❌ (미열람) |
| 26 | Generalization bias in LLM summarization of scientific research | Peters & Chin-Yee / Utrecht · Western | 2025-04 (RSOS 12:241776) | https://doi.org/10.1098/rsos.241776 · https://arxiv.org/abs/2504.00025 | ✅ (arXiv) |
| 27 | Semi-Supervised Exaggeration Detection of Health Science Press Releases | Wright & Augenstein / Copenhagen | 2021 (EMNLP) | https://aclanthology.org/2021.emnlp-main.845/ | ❌ (미열람) |
| 28 | The prevalence of statistical reporting errors in psychology (1985–2013) | Nuijten 외 / Tilburg | 2016 (Behav Res Methods) | https://pmc.ncbi.nlm.nih.gov/articles/PMC5101263/ | ✅ |
| 29 | "statcheck": Automatically detect statistical reporting inconsistencies | Nuijten & Epskamp | 2020 (Res Synth Methods) | https://doi.org/10.1002/jrsm.1408 | ❌ (Wiley 403) |
| 30 | Implementing Statcheck During Peer Review… | Nuijten & Wicherts / Tilburg | 2024 (AMPPS 7(2)) | https://doi.org/10.1177/25152459241258945 | ❌ (미열람) |
| 31 | The GRIM Test | Brown & Heathers | 2017 (SPPS) | https://doi.org/10.1177/1948550616673876 · https://peerj.com/preprints/2064/ | ❌ (미열람) |
| 32 | SPRITE | Heathers, Anaya, van der Zee, Brown | 2018 (PeerJ Preprints) | https://peerj.com/preprints/26968/ | ❌ (미열람) |
| 33 | sciwrite-lint | Samsonau / NYU | 2026-04-09 (rev 2026-05-24) | https://arxiv.org/abs/2604.08501 | ✅ |
| 34 | arXiVeri | Shin, Xie, Albanie | 2023-06-13 | https://arxiv.org/abs/2306.07968 | ✅ |
| 35 | SCITAB | Lu 외 | 2023 (EMNLP) | https://aclanthology.org/2023.emnlp-main.483/ · https://arxiv.org/abs/2305.13186 | ❌ (미열람) |
| 36 | Table-Text Alignment | Ho 외 / NII 외 | 2025-06-12 (rev 2025-09-17) | https://arxiv.org/abs/2506.10486 | ✅ |
| 37 | QuanTemp | Venktesh V 외 / TU Delft · Stavanger | 2024-03-25 (SIGIR 2024) | https://arxiv.org/abs/2403.17169 | ✅ |
| 38 | FEVEROUS | Aly 외 / Cambridge · Amazon | 2021 (NeurIPS D&B) | https://arxiv.org/abs/2106.05707 | ❌ (미열람) |

---

## 5. 못 찾은 것 · 불확실한 것

1. **"hit rate 정의가 논문마다 다르다"를 직접 다룬 출판 가이드라인은 찾지 못했다.** 캐시 문헌은 OHR/BHR을 구분해 쓰지만, "같은 지표 이름이 다른 정의를 숨긴다"를 주제로 삼은 시스템 분야 논문은 SoK EuroS&P 2019의 개별 결함 항목(D1/F4/A2)이 가장 가까웠다. 검색 결과 상위에 뜬 CDN 벤더 블로그(Cloudflare, ioriver, Aerospike 등)는 "request hit rate vs byte hit rate가 10–20%p 차이" 같은 유용한 서술을 담고 있으나 **비출판 마케팅 문서라 인용하지 않았다.**
2. **Alamri & Stevenson (2016) 심혈관 모순 코퍼스**는 URL을 열지 못했다(Springer 인증). "259 abstracts / 24 systematic reviews"라는 수치는 검색 요약에만 근거하므로 **검증되지 않았다.**
3. **BioDivergence (arXiv 2606.11208)** 는 taxonomy가 이 팀의 요구("contextual difference vs genuine contradiction")와 거의 일치하지만 **2026-08-30 철회**되었다. 저자 스스로 상당한 수정이 필요하다고 밝혔으므로 **근거로 쓰면 안 된다.** (아이디어 참고용으로만.)
4. **Claimify의 coverage 87.6% / precision 96.7%** 수치는 MarkTechPost 등 2차 매체에만 있었고 arXiv 초록·MS 블로그에서 확인하지 못했다. 확인된 수치는 블로그의 entailment 99%뿐이다.
5. **QuanTemp의 15,514 claims / 423,320 evidence snippets**는 검색 요약에만 있고 초록 인용으로 확인하지 못했다.
6. **Mogul, "Brittle metrics in operating systems research" (HotOS 1999)** 는 IEEE 유료 벽으로 열지 못했다. SoK 논문의 참고문헌 [19]에 존재한다는 사실만 확인했고, 내용은 인용하지 않았다.
7. **컴퓨터 시스템 분야에 특화된 메타분석/이질성 방법론 논문**은 찾지 못했다. Kitchenham의 소프트웨어공학 SLR 가이드라인이 인접하지만 원문을 열지 못했고, 시스템 성능 수치의 subgroup 분석을 다룬 정식 방법론은 검색 범위에서 나오지 않았다. 현 시점에서는 Cochrane ch.10을 직접 차용하는 것이 최선으로 보인다. (추론)
8. **41편 규모에서 정량 meta-regression은 권하지 않는다.** Cochrane은 회귀 공변량당 최소 10편을 권하며(검색 요약 기준이므로 §번호는 미확인), 조건 축이 6개면 이 기준에 미달한다. 조건 설명은 서술적 subgroup으로 제한할 것. (추론)
