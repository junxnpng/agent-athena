# LLM 산출물의 충실성·귀속·인용 검증 기성 방법론 (Facet A)

작성일: 2026-09-21 · 대상 레이어: 1(축자 충실), 2(숫자·kind 태깅), 5(상향 조건 드리프트) 중심

---

## 1. 요약

"LLM이 쓴 문장이 인용한 출처에 실제로 귀속되는가"를 재는 기성 방법은 크게 네 갈래다. (a) **정의·주석 프레임워크**: AIS가 "According to the source, the response ..."라는 판정 기준과 2단계 주석 파이프라인을 제공하고, SciFact/FEVER가 SUPPORTS/REFUTES/NOTENOUGHINFO 라벨 + 근거 문장(rationale) 선택이라는 작업 형식을 고정했다. (b) **NLI/함의 기반 자동 채점**: TRUE가 11개 데이터셋에서 대규모 NLI와 QG-QA가 가장 강하다는 것을 메타평가로 보였고(평균 ROC AUC 최고 81.5, 앙상블 86.0), SummaC는 문장 단위로 쪼개 집계하는 granularity 교정으로 74.4% balanced accuracy를 얻었으며, ALCE는 바로 그 TRUE 모델(T5-11B NLI)로 citation recall/precision을 계산한다. MiniCheck는 770M 모델로 GPT-4급 정확도를 400배 싼 비용에 낸다. (c) **원자 분해 후 검증**: FActScore(atomic facts, 자동 추정기 오차 <2%), SAFE(검색 증강, 인간과 72% 일치), RAGAS(F=|V|/|S|). (d) **자가·교차 검증 프롬프팅**: CoVe(Wikidata precision 0.17→0.36, 전기 생성 FActScore 55.9→71.4), self-consistency, LM-vs-LM 교차신문, multiagent debate. 레이어 5가 겨냥하는 "조건 소실"은 2025년 Peters & Chin-Yee가 **generalization bias**로 직접 계량했다(4,900개 요약, 과일반화 26–73%, 인간 요약 대비 OR = 4.85). 다만 자동 채점기를 심판으로 쓸 때의 신뢰도에는 확립된 한계가 있다: AutoAIS는 시스템 수준 Pearson 0.96이지만 인스턴스 수준에서는 "much lower and more variable"이고, LLM 심판에는 position/verbosity/self-enhancement 편향이 있으며, Dorner et al.은 심판이 피평가 모델보다 정확하지 않으면 어떤 디바이어싱도 필요한 인간 라벨을 절반 넘게 줄일 수 없음을 증명했다.

---

## 2. 방법별 정리

### 2.1 NLI/함의 기반 귀속·충실성 채점

**AIS (Attributable to Identified Sources)** — Rashkin et al., *Measuring Attribution in Natural Language Generation Models*, arXiv:2112.12870 (v1 2021-12-23, v2 2022-08-02). 출처가 명시된(identified) 문서에 대해 생성문이 "According to the source, the response ..."로 읽히는지를 사람이 판정하는 프레임워크이며, "a two-stage annotation pipeline"을 정의하고 대화형 QA·요약·table-to-text 세 과제에 인스턴스화했다. 초록에는 IAA 수치가 제시되지 않는다(본문 미열람). → **레이어 1·5의 판정 문구 자체**로 그대로 차용 가능: 요약 문장 S와 레코드 R에 대해 "According to R, S"가 참인지만 묻게 하면 조건 소실이 곧 불참이 된다.

**AutoAIS / Attributed QA** — Bohnet et al., arXiv:2212.08037 (2022-12-15). AIS를 NLI로 자동화: §3.2에서 "a T5 checkpoint with 11B parameters fine-tuned on NLI-related tasks", 점수 ≥0.5를 유효로 본다. §5.5/Fig.3에서 시스템 수준 **Pearson 0.96**("correlation between system AIS and AutoAIS scores is remarkably strong, with a Pearson coefficient of 0.96"), 그러나 인스턴스 수준은 "much lower and more variable"이며 저자들이 "care should be taken against reading individual AutoAIS scores too closely"라고 명시. → **레이어 5 자동화의 가장 중요한 경고**: 자동 점수는 집계 지표로만 쓰고, 개별 문장 플래그는 사람 확인을 거쳐야 한다. (추론) 즉 "드리프트 비율 추정"에는 써도 좋고 "이 문장은 드리프트다"라는 단정에는 부족하다.

**TRUE** — Honovich et al., *TRUE: Re-evaluating Factual Consistency Evaluation*, NAACL 2022, arXiv:2204.04991. 11개 데이터셋 / 4개 과제군(요약 5, 대화 3, 사실검증 2, 패러프레이즈 1)을 **이진**("the entire target text is factually consistent w.r.t the given grounding text or not")으로 통일하고 example-level meta-evaluation을 한다. Table 3 기준 평균 ROC AUC: **ANLI 81.5, SCZS 81.4, Q² 80.7**, 셋 앙상블 **86.0**(단일 최고 대비 +4.5). → 레이어 5의 채점기 선택 근거. (추론) 상호보완적이므로 NLI + QG-QA 앙상블이 단일 LLM 심판보다 안전한 1차 필터다.

**SummaC** — Laban, Schnabel, Bennett, Hearst, TACL (arXiv:2111.09525, 2021). 문서-요약 granularity 불일치가 NLI 실패 원인이라 보고 "segmenting documents into sentence units and aggregating scores between pairs of sentences". SummaC_Conv는 벤치마크에서 **74.4% balanced accuracy**, 선행 대비 **+5%p**. → 레이어 5에 직접: 요약 문장 하나 vs 레코드 여러 개를 문장쌍 행렬로 놓고 최대/집계.

**MiniCheck / LLM-AggreFact** — Tang, Laban, Durrett, EMNLP 2024, arXiv:2404.10774. grounding 문서 대비 문장 단위 사실검증 전용 소형 모델. **MiniCheck-FT5(770M)**가 "reaches GPT-4 accuracy" while "400x lower cost". → 41편 × 두 추출기 × 다수 레코드라는 규모에서 **전수 1차 스윕**을 현실적으로 만드는 도구. (추론) 전수는 MiniCheck, 플래그된 것만 강한 LLM/사람.

**ALCE** — Gao, Yen, Yu, Chen, EMNLP 2023, arXiv:2305.14627. 인용 생성 최초 벤치마크. fluency/correctness/citation quality 3축이며 citation recall·precision은 "we use TRUE, a T5-11B model fine-tuned on a collection of natural language inference (NLI) datasets"로 계산한다. 초록: "on the ELI5 dataset, even the best models lack complete citation support 50% of the time". 인간 대조(§6, Appendix G.5): citation recall 자동-인간 **정확도 85.1%, Cohen's κ 0.698**; citation precision **77.6%, κ 0.525**. → **레이어 2·5의 정확한 템플릿**. recall = "이 문장이 인용한 레코드들이 합쳐서 문장을 지지하는가", precision = "각 인용이 필요한가"(불필요 인용 = 과잉 귀속). κ 0.525라는 숫자는 precision 쪽 자동화가 recall보다 훨씬 덜 믿을 만하다는 뜻이다.

**AttrScore** — Yue et al., *Automatic Evaluation of Attribution by Large Language Models*, EMNLP 2023 Findings, arXiv:2305.06311. 귀속을 **attributable / extrapolatory / contradictory** 3분류로 정식화하고, QA·fact-checking·NLI·요약 데이터를 재활용해 소형 모델을 파인튜닝하거나 LLM을 프롬프팅한다. New Bing 실사용 질의 기반 12개 도메인 테스트셋 보유. 초록에 수치 없음(본문 미열람). → **레이어 2의 kind 태그와 거의 1:1**: extrapolatory ≈ author interpretation / 근거 초과, contradictory ≈ 인용 오류.

**AttributionBench** — Li, Yue, Liao, Sun, arXiv:2402.15089 (2024-02-23). 여러 귀속 데이터셋 통합 벤치마크. "a fine-tuned GPT-3.5 only achieves around 80% macro-F1 under a binary classification formulation"이며, 오류는 "nuanced information" 처리 실패와 모델/주석자 정보 비대칭에서 온다. → **자동 귀속 판정의 천장이 80% 근방**이라는 현실적 기대치 설정. (추론) 따라서 레이어 5를 전자동으로 닫을 수 없고 레이어 4(사람 개입)와 반드시 짝지어야 한다.

**RAGAS** — Es, James, Espinosa-Anke, Schockaert, arXiv:2309.15217 (2023-09-26). Faithfulness는 답변을 statement로 분해한 뒤 컨텍스트 지지 여부를 판정해 **F = |V|/|S|**. Answer Relevance는 답변에서 역생성한 질문 n개와 원 질문의 코사인 유사도 평균, Context Relevance는 추출 문장 수 / 전체 문장 수. WikiEval 인간 일치 정확도: **faithfulness 0.95, answer relevance 0.78, context relevance 0.70**. 실무 도구 문서는 docs.ragas.io(본 조사에서 직접 열지 않음 — 아래 §5). → 레이어 5의 문장 단위 점수화. (추론) WikiEval은 저자 자체 제작 소규모 셋이라 0.95는 낙관적일 소지.

**FActScore** — Min et al., EMNLP 2023, arXiv:2305.14251. 생성문을 atomic facts로 쪼개 신뢰 가능한 지식원이 지지하는 비율을 계산. 자동 추정기는 "less than a 2% error rate", 13개 LM의 6,500개 생성을 평가했고 이는 "would have cost $26K if evaluated by humans", ChatGPT는 "only achieves 58%". → 레이어 2·3: 레코드 하나를 atomic claim들로 쪼개면 numbers/conditions가 각각 독립 검증 단위가 된다.

**SAFE / LongFact / F1@K** — Wei et al., *Long-form factuality in large language models*, NeurIPS 2024, arXiv:2403.18802 (Google DeepMind). 응답을 개별 사실로 분해하고 Google 검색 질의를 다단계로 던져 지지 여부 판정. "SAFE agrees with crowdsourced human annotators 72% of the time"; 불일치 100건 무작위 표본에서 "SAFE wins 76% of the time"; "more than 20 times cheaper than human annotators". → 레이어 1의 외부 확인(논문 원문이 아닌 웹 근거)에 응용 가능. **72%는 높지 않다**는 점을 명시해야 한다.

### 2.2 자가 검증 프롬프팅

**Chain-of-Verification (CoVe)** — Dhuliawala et al., arXiv:2309.11495 (2023-09-20), Findings of ACL 2024. 4단계: 초안 → 검증 질문 계획 → **질문을 독립적으로 답변**(초안에 오염되지 않게) → 최종 수정. Llama 65B few-shot 기준 Wikidata 리스트 질문 precision **0.17 → 0.36**(Table 1), hallucinated answers **2.95 → 0.68**; MultiSpanQA F1 **0.39 → 0.48**(Table 2); 전기 생성 FactScore **55.9 → 71.4**(Table 3, 참고로 ChatGPT 58.7, PerplexityAI 61.6). → **레이어 2·5에 가장 직접적인 프롬프트 설계 원칙**: 요약 문장에서 "이 문장이 암묵 가정하는 조건은?"을 검증 질문으로 뽑고, 그 질문을 **원 레코드만 보여준 새 컨텍스트에서** 답하게 한다(독립 답변이 효과의 핵심).

**Self-Consistency** — Wang et al., ICLR 2023, arXiv:2203.11171. 샘플링된 추론 경로를 주변화해 최빈 답 선택. GSM8K **+17.9%**, SVAMP **+11.0%**, AQuA **+12.2%**, StrategyQA **+6.4%**, ARC-challenge **+3.9%**. → 레이어 2·6의 파생값 재계산에 적합(수치 계산은 답이 하나로 수렴하므로 다수결이 잘 먹는다). (추론) 반면 레이어 5의 "조건이 살아남았는가"는 개방형 판정이라 다수결 이득이 더 작을 것.

**Factored Verification** — George & Stuhlmüller, WIESP @ IJCNLP-AACL 2023, arXiv:2310.10627. **학술 논문 요약**의 환각을 자동 탐지하고 Factored Critiques로 자가수정. HaluEval **76.2% accuracy**. 요약당 환각 추정치: ChatGPT(16k) **0.62**, GPT-4 **0.84**, Claude 2 **1.55** → 자가수정 후 **0.49 / 0.46 / 0.95**. 저자들은 환각이 "subtle"하다고 경고. → 본 과제와 도메인이 동일(논문 요약)하므로 **레이어 5의 기저율 참고치**로 가장 가깝다.

### 2.3 LLM-as-a-judge 신뢰도와 보정

**MT-Bench / Chatbot Arena** — Zheng et al., NeurIPS 2023 D&B, arXiv:2306.05685. GPT-4 같은 강한 심판이 인간 선호와 "over 80% agreement"이며 "the same level of agreement between humans"라고 보고. 동시에 **position bias, verbosity bias, self-enhancement bias, limited reasoning ability**를 한계로 명시. → 레이어 4의 심판 사용 근거이자 경고.

**G-Eval** — Liu et al., arXiv:2303.16634 (2023-03-29), EMNLP 2023. 과제 소개 + 평가 기준 → CoT 평가 단계 자동 생성 → form-filling → 출력 점수의 확률가중합. SummEval에서 **Spearman 0.514**로 "outperforming all previous methods by a large margin". 초록 자체가 LLM 생성 텍스트 선호 편향 가능성을 경고. → **레이어 5의 루브릭 채점 형식**(조건 보존 여부를 5개 세부 항목 폼으로).

**Large Language Models are not Fair Evaluators** — Wang et al., arXiv:2305.17926 (2023-05-29). 순서만 바꿔도 순위가 뒤집힘: ChatGPT 심판에서 "Vicuna-13B could beat ChatGPT on 66 over 80 tested queries". 대책 3종: Multiple Evidence Calibration(근거 먼저 쓰게), Balanced Position Calibration(순서 바꿔 평균), Human-in-the-Loop Calibration(balanced position diversity entropy로 어려운 사례를 사람에게). → **레이어 4 설계 그 자체**: 두 추출기(Claude/Codex) 레코드를 심판에 넣을 때 **좌우 순서를 반드시 교대**하고, 엔트로피 높은 건만 사람이 원문을 본다.

**Judging the Judges: A Systematic Study of Position Bias in LLM-as-a-Judge** — Shi et al., arXiv:2406.07791 (2024-06-12), AACL-IJCNLP 2025 채택. repetition stability / position consistency / preference fairness 3지표. 규모: "15 LLM judges across MTBench and DevBench with 22 tasks and approximately 40 solution-generating models", "over 150,000 evaluation instances". position bias는 무작위가 아니고 심판·과제별로 크게 다르며, 프롬프트 길이와는 약한 상관, **두 답변의 품질 차이와는 강한 상관**. (추론) 두 추출기가 비슷한 품질일수록 위치 편향이 커지므로, 레이어 4에서 순서 교대가 특히 중요하다.

**Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge (CALM)** — Ye et al., arXiv:2410.02736 (2024-10-03). 12종 편향을 자동 프레임워크로 계량. 초록은 "significant biases persist in certain specific tasks"라고만 하고 구체 수치·12종 목록은 초록에 없음(본문 미열람).

**심판 보정의 이론적 한계** — Dorner, Nastl, Hardt, *Limits to scalable evaluation at the frontier: LLM as Judge won't beat twice the data*, ICLR 2025, arXiv:2410.13341. 핵심 정리: "when the judge is no more accurate than the evaluated model, no debiasing method can decrease the required amount of ground truth labels by more than half"이며 실제 절감은 그보다 더 작다. → **레이어 4의 예산 계산 근거**: 인간 표본을 2배로 늘리는 것이 심판 도입보다 확실하다. (추론) 따라서 "심판으로 인간 검토를 대체"가 아니라 "심판으로 우선순위만 매기고 인간 표본 크기는 통계적으로 정한다"가 맞는 설계.

### 2.4 교차 모델 검증 / 토론

**LM vs LM: Detecting Factual Errors via Cross Examination** — Cohen, Hamri, Geva, Globerson, arXiv:2305.13281 (2023-05-22). 한 모델이 주장하고 다른 모델이 **신문관**으로 다회 턴 질문해 자기모순을 유도한다("an incorrect claim is likely to result in inconsistency with other claims that the model generates"). 초록은 "outperforms existing methods and baselines, often by a large gap"라고만 하고 수치 없음(본문 미열람). → 레이어 4의 "두 추출기가 다를 때" 절차를 기계화하는 틀.

**Multiagent Debate** — Du, Li, Torralba, Tenenbaum, Mordatch, *Improving Factuality and Reasoning in Language Models through Multiagent Debate*, arXiv:2305.14325 (2023-05-23). 여러 인스턴스가 각자 답하고 여러 라운드 토론해 합의. 초록에 정량 수치 없음(본문 미열람). 블랙박스 모델에 그대로 적용 가능하다는 점만 명시.

### 2.5 수치 충실성

**HERMAN** — Zhao, Cohen, Webber, *Reducing Quantity Hallucinations in Abstractive Summarization*, Findings of EMNLP 2020, arXiv:2009.13312. 날짜·수·금액 등 **quantity entity**를 인식하고 원문 근거 여부를 검증해 beam 후보를 재순위화. 초록: 상승 순위 요약이 "higher Precision ... without a comparable loss in Recall, resulting in higher F₁", 예비 인간 평가에서 선호. 구체 %는 초록에 없음. → **레이어 2의 정석**: 숫자를 엔티티로 추출해 원문 스팬과 대조하는 것이 LLM 판단보다 먼저다.

**Walters & Wilder**, *Fabrication and errors in the bibliographic citations generated by ChatGPT*, Scientific Reports 13 (2023), DOI 10.1038/s41598-023-41032-5. 42개 주제, 84편 문헌 리뷰, 636개 인용. "55% of the GPT-3.5 citations but just 18% of the GPT-4 citations are fabricated"; 실재하는 인용 중에서도 "43% of the real GPT-3.5 citations but just 24% of the real GPT-4 citations include substantive citation errors". → **레이어 1의 존재 이유**를 직접 뒷받침: 인용이 실재해도 4분의 1은 실질 오류를 포함한다. (추론) 따라서 quote 문자열 일치와 별개로 **섹션/페이지 메타데이터도 독립 검증**해야 한다.

### 2.6 과일반화 / 한정어 소실 (레이어 5 핵심)

**Generalization bias in large language model summarization of scientific research** — Uwe Peters & Benjamin Chin-Yee, *Royal Society Open Science* 12(4): 241776 (2025); arXiv:2504.00025. 10개 주요 LLM, **4,900개 요약**을 원문과 대조. "DeepSeek, ChatGPT-4o, and LLaMA 3.3 70B overgeneralizing in 26 to 73% of cases"; 인간 요약 대비 "LLM summaries were nearly five times more likely to contain broad generalizations (**OR = 4.85, 95% CI [3.06, 7.70]**)"; **정확성을 명시적으로 지시해도** 대부분의 LLM이 여전히 더 넓게 일반화했고, 최신 모델이 오히려 더 나빴다. 완화책으로 낮은 temperature와 일반화 정확도 벤치마킹을 제안. → **레이어 5가 실재하는 실패 모드임을 계량한 유일한 직접 증거**. (추론) "정확히 써라" 프롬프트로는 못 막으므로, 생성 단계가 아니라 **사후 대조 검증 단계**에 예산을 써야 한다는 결론이 따라온다.

### 2.7 과학적 주장 검증의 라벨 체계

**SciFact** — Wadden et al., *Fact or Fiction: Verifying Scientific Claims*, EMNLP 2020, arXiv:2004.14974. "a dataset of 1.4K expert-written scientific claims paired with evidence-containing abstracts". 시스템은 근거 초록을 고르고 SUPPORTS/REFUTES 라벨을 붙이며 **"identify rationales justifying each decision"** — 즉 근거 문장을 반드시 지목해야 한다. (초록 자체는 SUPPORTS/REFUTES만 명시.)

**FEVER** — Thorne, Vlachos, Christodoulopoulos, Mittal, NAACL 2018, arXiv:1803.05355. 185,445 claims, 라벨 **"Supported, Refuted or NotEnoughInfo"**, 주석자 일치 **Fleiss κ 0.6841**. 근거까지 맞춰야 하는 조건에서 베이스라인 **31.87%**, 라벨만 맞히면 되는 조건에서 **50.91%**. → **레이어 2·5의 라벨 스킴과 난이도 감각**: 근거 스팬까지 요구하면 정확도가 절반 아래로 떨어진다는 것이 이 19%p 격차의 의미다. NOT ENOUGH INFO 라벨은 "레코드가 그 문장을 지지하지도 반박하지도 않음" = 조건 드리프트 후보를 담는 자리다.

---

## 3. 7층 대응표

| 층 | 방법 | 출처 | 어떻게 쓰나 |
|---|---|---|---|
| 1 축자 충실 | 인용 메타데이터 독립검증 | Walters & Wilder 2023 | 문자열 일치와 별개로 섹션/페이지를 따로 확인 (실재 인용도 24–43% 실질 오류) |
| 1 | AIS 판정 문구 | Rashkin 2021 | "According to the source, ..." 이진 판정으로 주석 지침 고정 |
| 1 | SAFE 검색 증강 | Wei 2024 | 원문 외부 확인이 필요할 때; 인간 일치 72%임을 감안 |
| 2 숫자·kind | quantity entity 검증 | Zhao 2020 (HERMAN) | 숫자를 엔티티로 뽑아 원문 스팬 대조를 LLM 판단보다 선행 |
| 2 | 3분류 귀속 태깅 | Yue 2023 (AttrScore) | attributable / extrapolatory / contradictory ↔ 팀의 kind 태그 매핑 |
| 2 | atomic fact 분해 | Min 2023 (FActScore) | numbers/conditions를 각각 독립 검증 단위로 쪼갬 |
| 2 | self-consistency | Wang 2022 | 파생값 재계산 다수결 (GSM8K +17.9%) |
| 3 재현율 | 원자 분해 기반 recall | FActScore, ALCE citation recall | 문단 shingle 대신 claim 단위 커버리지 |
| 4 교차 판정 | 순서 교대 + MEC/BPC/HITLC | Wang 2023 (Fair Evaluators) | 두 추출기 레코드 좌우 교대, 엔트로피 높은 건만 사람 |
| 4 | position bias 계량 | Shi 2024 | repetition stability/position consistency로 심판 자체를 먼저 검사 |
| 4 | 교차신문 / 토론 | Cohen 2023, Du 2023 | 불일치 레코드쌍에 신문관 모델 투입 |
| 4 | 인간 표본 예산 | Dorner 2024 (ICLR 2025) | 심판 디바이어싱으로 인간 라벨 절감은 최대 2배 |
| 5 조건 드리프트 | generalization bias 측정틀 | Peters & Chin-Yee 2025 | 요약문 일반화 폭을 원문 대비 코딩; 프롬프트로는 못 막힘 |
| 5 | 문장쌍 NLI 집계 | Laban TACL (SummaC), Honovich 2022 (TRUE) | 요약 문장 vs 레코드 문장 행렬, 앙상블 86.0 ROC AUC |
| 5 | citation recall/precision | Gao 2023 (ALCE) | 인용 레코드가 문장을 지지하는가 / 불필요 인용인가 |
| 5 | faithfulness = \|V\|/\|S\| | Es 2023 (RAGAS) | 요약 문장을 statement로 쪼개 지지 비율 |
| 5 | 검증 질문 독립 답변 | Dhuliawala 2023 (CoVe) | "이 문장이 가정한 조건은?"을 레코드만 보고 답하게 |
| 5 | 루브릭 폼 채점 | Liu 2023 (G-Eval) | 조건 보존 항목별 form-filling |
| 5 | 대규모 저비용 스윕 | Tang 2024 (MiniCheck) | 770M으로 전수 1차 필터, 400x 저렴 |
| 5 | 라벨 스킴 | Wadden 2020, Thorne 2018 | SUPPORTS/REFUTES/NEI + rationale 지목 강제 |
| 6 산술·내부정합 | 논문요약 환각 탐지 | George & Stuhlmüller 2023 | 요약당 환각 0.62–1.55 → 자가수정 후 0.46–0.95 |
| 7 정의 비교가능성 | (직접 대응 없음) | — | AttrScore의 extrapolatory, FEVER의 NEI가 가장 가까움 (추론) |

---

## 4. 출처 표

| # | 제목 | 저자/기관 | 연도 | URL | 열어서 확인 |
|---|---|---|---|---|---|
| 1 | Measuring Attribution in Natural Language Generation Models (AIS) | Rashkin et al. (Google) | 2021/2022 | https://arxiv.org/abs/2112.12870 | 예(초록) |
| 2 | Attributed Question Answering (AutoAIS) | Bohnet et al. (Google) | 2022 | https://arxiv.org/abs/2212.08037 | 예(초록+ar5iv 본문) |
| 3 | TRUE: Re-evaluating Factual Consistency Evaluation | Honovich et al., NAACL | 2022 | https://arxiv.org/abs/2204.04991 | 예(초록+ar5iv 본문; PDF는 파싱 실패) |
| 4 | SummaC: Re-Visiting NLI-based Models for Inconsistency Detection | Laban, Schnabel, Bennett, Hearst, TACL | 2021 | https://arxiv.org/abs/2111.09525 | 예(초록) |
| 5 | MiniCheck: Efficient Fact-Checking of LLMs on Grounding Documents | Tang, Laban, Durrett, EMNLP | 2024 | https://arxiv.org/abs/2404.10774 | 예(초록) |
| 6 | Enabling LLMs to Generate Text with Citations (ALCE) | Gao, Yen, Yu, Chen, EMNLP | 2023 | https://arxiv.org/abs/2305.14627 | 예(초록+ar5iv 본문) |
| 7 | Automatic Evaluation of Attribution by LLMs (AttrScore) | Yue et al., EMNLP Findings | 2023 | https://arxiv.org/abs/2305.06311 | 예(초록만) |
| 8 | AttributionBench: How Hard is Automatic Attribution Evaluation? | Li, Yue, Liao, Sun | 2024 | https://arxiv.org/abs/2402.15089 | 예(초록) |
| 9 | Ragas: Automated Evaluation of Retrieval Augmented Generation | Es, James, Espinosa-Anke, Schockaert | 2023 | https://arxiv.org/abs/2309.15217 | 예(초록+ar5iv 본문) |
| 10 | FActScore | Min et al., EMNLP | 2023 | https://arxiv.org/abs/2305.14251 | 예(초록) |
| 11 | Long-form factuality in LLMs (SAFE) | Wei et al., Google DeepMind, NeurIPS | 2024 | https://arxiv.org/abs/2403.18802 | 예(초록) |
| 12 | Chain-of-Verification Reduces Hallucination | Dhuliawala et al., Meta AI / ETH, Findings ACL 2024 | 2023 | https://arxiv.org/abs/2309.11495 | 예(초록+ar5iv 본문) |
| 13 | Self-Consistency Improves CoT Reasoning | Wang et al., Google, ICLR | 2022/2023 | https://arxiv.org/abs/2203.11171 | 예(초록) |
| 14 | LM vs LM: Detecting Factual Errors via Cross Examination | Cohen, Hamri, Geva, Globerson | 2023 | https://arxiv.org/abs/2305.13281 | 예(초록만) |
| 15 | Improving Factuality and Reasoning through Multiagent Debate | Du et al., MIT/Google Brain | 2023 | https://arxiv.org/abs/2305.14325 | 예(초록만) |
| 16 | G-Eval: NLG Evaluation using GPT-4 | Liu et al., Microsoft, EMNLP | 2023 | https://arxiv.org/abs/2303.16634 | 예(초록) |
| 17 | Large Language Models are not Fair Evaluators | Wang et al., PKU/Tencent | 2023 | https://arxiv.org/abs/2305.17926 | 예(초록) |
| 18 | Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena | Zheng et al., NeurIPS D&B | 2023 | https://arxiv.org/abs/2306.05685 | 예(초록) |
| 19 | Judging the Judges: Position Bias in LLM-as-a-Judge | Shi et al., Dartmouth, AACL-IJCNLP 2025 | 2024 | https://arxiv.org/abs/2406.07791 | 예(초록) |
| 20 | Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge (CALM) | Ye et al. | 2024 | https://arxiv.org/abs/2410.02736 | 예(초록만) |
| 21 | Limits to scalable evaluation at the frontier | Dorner, Nastl, Hardt, MPI-IS, ICLR 2025 | 2024 | https://arxiv.org/abs/2410.13341 | 예(초록) |
| 22 | Generalization bias in LLM summarization of scientific research | Peters & Chin-Yee, R. Soc. Open Sci. 12:241776 | 2025 | https://arxiv.org/abs/2504.00025 | 예(초록) |
| 23 | Reducing Quantity Hallucinations in Abstractive Summarization | Zhao, Cohen, Webber, Findings EMNLP | 2020 | https://arxiv.org/abs/2009.13312 | 예(초록) |
| 24 | Factored Verification: ... Summaries of Academic Papers | George & Stuhlmüller, WIESP@IJCNLP-AACL | 2023 | https://arxiv.org/abs/2310.10627 | 예(초록) |
| 25 | Fact or Fiction: Verifying Scientific Claims (SciFact) | Wadden et al., AI2, EMNLP | 2020 | https://arxiv.org/abs/2004.14974 | 예(초록) |
| 26 | FEVER: a large-scale dataset for Fact Extraction and VERification | Thorne et al., NAACL | 2018 | https://arxiv.org/abs/1803.05355 | 예(초록) |
| 27 | Fabrication and errors in the bibliographic citations generated by ChatGPT | Walters & Wilder, Scientific Reports 13 | 2023 | https://www.nature.com/articles/s41598-023-41032-5 | 예(리디렉션 경유) |
| 28 | Ragas 실무 문서 (practitioner) | Ragas 프로젝트 | — | https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/ | **아니오** (검색 결과에만 등장, 직접 열지 않음) |

---

## 5. 못 찾은 것 · 불확실한 것

- **레이어 7(정의 비교가능성)에 대응하는 확립된 벤치마크·방법을 찾지 못했다.** 분모/가중/ideal-vs-realized 같은 정의 태그를 맞춰 비교 가능성을 판정하는 전용 연구를 찾지 못했고, 가장 가까운 것은 AttrScore의 extrapolatory 범주와 FEVER/SciFact의 NOT ENOUGH INFO 라벨이다 (추론).
- **초록에 수치가 없어 효과 크기를 인용하지 못한 것**: AttrScore(#7), LM vs LM(#14), Multiagent Debate(#15), CALM의 12종 편향 목록과 수치(#20), AIS의 IAA(#1), HERMAN의 구체 %(#23). 본문을 열지 않았으므로 수치를 쓰지 않았다.
- **AttributedQA의 인스턴스 수준 상관계수**는 본문이 "much lower and more variable"이라고만 하고 수치를 주지 않는다(확인한 범위 내에서).
- **RAGAS 공식 문서(#28)는 직접 열지 않았다.** 페이지 URL은 검색 결과에 존재하나 본 조사에서 fetch하지 않았으므로 §2.1의 RAGAS 수식·수치는 전부 arXiv 본문(#9) 기준이다.
- **arXiv PDF 직접 fetch가 여러 번 실패**(바이너리 파싱)했다. TRUE·CoVe·ALCE·AutoAIS의 본문 수치는 ar5iv HTML 미러로 확인했다. ar5iv는 arXiv 원문의 자동 변환본이므로 표 번호가 최종본과 어긋날 가능성이 있다 (추론).
- **후속 비판 메모**: (a) MT-Bench의 ">80% agreement"는 이후 position-bias 연구(#17, #19)와 Dorner의 이론적 한계(#21)에 의해 "심판이 인간을 대체한다"는 해석으로 확장될 수 없음이 밝혀졌다. (b) G-Eval은 자기 초록에서 LLM 생성 텍스트 선호 편향을 스스로 경고한다. (c) AutoAIS류 자동 AIS는 시스템 수준에서만 신뢰 가능하다. (d) FActScore/SAFE의 자동 판정은 각각 "<2% error rate"와 "72% agreement"로 신뢰도 편차가 크며 동일 수준으로 취급하면 안 된다.
- **팀 설계에 대한 함의 (추론)**: 레이어 5는 자동화로 닫히지 않는다. AttributionBench의 ~80% macro-F1 천장, ALCE citation precision κ=0.525, Dorner의 2배 한계를 합치면, 현실적 설계는 "MiniCheck/NLI로 전수 스윕 → CoVe식 조건 검증 질문으로 후보 좁힘 → 순서 교대한 LLM 심판으로 우선순위 → 통계적으로 정한 크기의 인간 표본으로 드리프트율을 구간추정"이다.
