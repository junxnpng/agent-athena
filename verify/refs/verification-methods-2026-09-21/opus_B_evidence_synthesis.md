# 근거종합(evidence synthesis)·체계적 문헌고찰 방법론에서 본 추출 검증
## 특히 layer 3(recall/completeness), layer 4(교차추출자 판정), 정량적 통과기준

작성 2026-09-21. 표기 원칙: **"출처가 말한 것"** 과 **(추론)** 을 분리했다. 수치는 출처가 직접 보고한 것만, 나온 자리와 함께 적었다. 열어서 확인하지 못한 URL은 §5와 출처표에 명시했다.

---

## 1. 요약

의학 체계적 문헌고찰은 우리가 지금 설계하려는 7층 검증과 거의 같은 문제를 60년간 풀어 왔다. 핵심 합의는 세 가지다. (a) **추출은 두 명이 독립으로 하고 사전에 정의된 절차로 불일치를 해소한다** — Cochrane은 결과 데이터(outcome data)에 대해 이를 *Mandatory* 표준(C46)으로, 연구 특성(study characteristics)에 대해 *Highly desirable*(C45)로 못박았고, Buscemi 2006은 단일추출이 이중추출보다 오류가 **상대적으로 21.7% 더 많다(P = .019)** 고 보고했다. (b) **합치도는 우연보정 계수로 재고, 사전에 임계값을 정해 놓고 스케일업 전에 통과 여부를 본다** — Krippendorff α의 관례적 기준은 α ≥ .800, .667~.800은 잠정적 결론용이며, Hayes & Krippendorff 2007은 "점추정 α"가 아니라 **"α_min에 미달할 확률 q"** 를 부트스트랩으로 계산해 판정하라는, 우리 목적에 더 맞는 형태를 제시한다. (c) **정답셋이 없을 때의 recall은 포획-재포획과 TAR 정지규칙으로 추정한다** — Kastner 2009는 4개 DB가 전체 추정 문헌의 **68%(초록 수준)/81%(전문 수준)** 만 잡았다고 보고했고, Cormack & Grossman의 target method는 **크기 10의 target set이면 95% 신뢰도로 recall 0.7을 보장**한다. LLM 추출에 대해서는 2024~2026년 평가가 축적되어, **"단독 추출자가 아니라 이중추출 워크플로의 보조 추출자/제2검토자"** 라는 권고가 일관되게 나온다(Shankar 2026, Schmidt 2024, Konet 2024). 우리의 Claude/Codex 두 추출자 구조는 이 문헌에서 보면 "이중추출 + 판정"의 자동화 변형이며, 따라서 **불일치 건만 사람이 원문을 본다**는 layer 4 설계는 Cochrane 절차와 정확히 일치한다.

---

## 2. 방법별 정리

### 2.1 이중 독립 추출 + 판정/합의 (layer 4의 원형)

**(1) Cochrane Handbook, Chapter 5: Collecting data**
- 출처: Li T, Higgins JPT, Deeks JJ (eds). *Cochrane Handbook for Systematic Reviews of Interventions*, current version. <https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-05> (열림)
- 하는 일: 데이터 수집 양식 설계, 추출자 훈련, 이중추출, 불일치 해소 절차를 규정한다.
- 출처가 말한 것: MECIR Box 5.5.a 기준 **C46(Mandatory)** — "Use (at least) two people working independently to extract outcome data from reports of each study, and define in advance the process for resolving disagreements." **C45(Highly desirable)** 는 같은 문장의 study characteristics 판이다. §5.4.3: "All data collection forms and data systems should be thoroughly pilot-tested before launch". §5.5.3: 훈련은 "at the onset of the data extraction process and periodically over the course of the project". §5.5.5: 불일치 해소 절차는 프로토콜에 "specified in the protocol for identifying and resolving disagreements" 되어 있어야 하고, 통상 논의로 해소하되 필요시 제3자 중재.
- MECIR 원문: <https://www.cochrane.org/authors/handbooks-and-manuals/mecir-manual/standards-conduct-new-cochrane-intervention-reviews-c1-c75/performing-review-c24-c75/collecting-data-included-studies-c43-c51> (열림). C43(Mandatory) 파일럿된 양식 사용, C51(Mandatory) 효과 크기·방향이 원보고와 일치하는지 검증.
- 층 대응: **layer 4 전체**. C43·C45/C46 → 두 추출자 + 사전정의 판정절차. **C51은 우리 layer 6(내부 일관성)의 직계 조상**이다 — "원문의 값과 리뷰에 옮겨적은 값의 크기·방향이 같은가"를 별도 mandatory 항목으로 둔 것.
- (추론) `numbers`·`kind`는 outcome data에 해당하니 C46급(필수 이중), `conditions`·링크는 C45급(권장)으로 등급을 나눠 예산을 배분하면 이 표준의 취지에 맞다.

**(2) Buscemi 2006 — 단일 vs 이중 추출 오류율**
- Buscemi N, Hartling L, Vandermeer B, Tjosvold L, Klassen TP. "Single data extraction generated more errors than double data extraction in systematic reviews." *J Clin Epidemiol* 2006;59(7):697-703. doi:10.1016/j.jclinepi.2005.11.010, PMID 16765272.
- 출처가 말한 것(초록, Results): "Single data extraction resulted in more errors than double data extraction (**relative difference: 21.7%, P = .019**)." / "There was no substantial difference between methods in effect estimates for most outcomes." / "The average time spent for single data extraction was less than the average time for double data extraction (**relative difference: 36.1%, P = .003**)."
- 중요한 설계 디테일(초록 Methods): 비교 대상은 "단일추출 + 제2자 검증(verifier)" vs "두 명 독립추출"이었다. 즉 **검증(verification)은 독립추출과 같지 않다.**
- 층 대응: layer 4의 정당화. (추론) 우리가 "Claude가 추출하고 Codex가 검토한다"로 설계하면 이 논문이 말하는 열등한 쪽(single + verify)에 해당한다. 현재처럼 **둘이 서로 모른 채 독립 추출 후 대조**하는 구조를 유지해야 한다.

**(3) Mathes, Klaßen, Pieper 2017 — 오류 빈도 방법론적 리뷰**
- *BMC Med Res Methodol* 2017;17(1):152. doi:10.1186/s12874-017-0431-4, PMID 29179685. (Springer 직링크는 로그인 리다이렉트, Europe PMC로 확인)
- 출처가 말한 것: 6개 연구를 종합해 "**a high rate of extraction errors (up to 50%)**", 오류가 효과추정치에 영향을 주는 경우가 잦았고, 추출 방법·추출자 특성은 오류율에 "moderate effect"였다. 결론은 확립된 표준을 뒷받침하는 근거 자체가 약하다는 것.
- 층 대응: 통과기준 설정의 현실 기준선. (추론) "연구 단위 오류율 최대 50%"는 항목(item) 단위가 아니라 논문 단위 지표로 보이므로, 우리 41편 코퍼스에서 **논문 단위로 1건 이상 오류가 있는 비율**을 별도 지표로 두면 이 문헌과 비교 가능해진다.

### 2.2 평가자 간 합치도 지표와 그 해석 (layer 4의 계량화)

**(4) Cohen's κ** — Cohen J. "A Coefficient of Agreement for Nominal Scales." *Educational and Psychological Measurement* 1960;20:37-46. doi:10.1177/001316446002000104. 명목 범주에 대한 우연보정 합치도. **원문 PDF는 열지 못했다**(§5).

**(5) Landis & Koch 1977 벤치마크** — *Biometrics* 1977;33(1):159-174. κ 구간 해석(<0 no, 0–0.20 slight, 0.21–0.40 fair, 0.41–0.60 moderate, 0.61–0.80 substantial, 0.81–1 almost perfect). **원문을 열지 못했고**, 위 구간표는 검색 요약과 2차 출처에서만 확인했으므로 인용 시 2차 인용으로 표기해야 한다(§5).

**(6) Artstein & Poesio 2008 — 전산언어학의 합치도 서베이**
- "Survey Article: Inter-Coder Agreement for Computational Linguistics." *Computational Linguistics* 2008;34(4):555-596. doi:10.1162/coli.07-034-R2. <https://aclanthology.org/J08-4004/> (열림 — 서지정보만, 초록 본문은 그 페이지에 없음)
- 하는 일: κ, Scott's π, Krippendorff α를 주석 코퍼스 맥락에서 비교하고 범주 간 거리(가중), 다중 코더, 단위화(unitizing)를 다룬다.
- 층 대응: (추론) **필드마다 지표를 달리 써야 한다** — `kind`(5개 명목 범주)는 κ/α, `numbers`는 단순 일치율, `conditions`는 단위화 합치도.

**(7) Krippendorff's α와 임계값**
- Krippendorff K. "Computing Krippendorff's Alpha-Reliability." 2011.1.25 (literature updated 2013.9.13), UPenn ScholarlyCommons. <https://www.asc.upenn.edu/sites/default/files/2021-03/Computing%20Krippendorff's%20Alpha-Reliability.pdf> (열림, 본문 추출 성공)
- 출처가 말한 것: α는 관찰자 수·측정수준·표본크기·결측 유무와 무관하게 쓸 수 있는 일반화된 신뢰도 계수이며, "To rely on data generated by any method, α needs to be far from these two extreme conditions, ideally α=1."
- Hayes AF, Krippendorff K. "Answering the Call for a Standard Reliability Measure for Coding Data." *Communication Methods and Measures* 2007;1(1):77-89. <https://www.asc.upenn.edu/sites/default/files/2021-03/Answering%20the%20Call%20for%20a%20Standard%20Reliability%20Measure%20for%20Coding%20Data.pdf> (열림, 본문 추출 성공)
- 출처가 말한 것(pp. 271-278 상당 부분): 부트스트랩으로 α의 95% CI와 **"probability, q, of failing to achieve α_min"** 을 α_min = 0.9/0.8/0.7/0.67/0.6/0.5에 대해 계산한다. 예시에서 "the confidence interval for α_true is 0.7078 to 0.8078", "q = 0.0125 for α_min = 0.70, and **q = 0.9473 for α_min = 0.80**", 따라서 "if this research problem demands that reliability must not be below α_min = 0.800, our reliability data would suggest serious trouble."
- 층 대응: **layer 4의 통과기준을 점추정이 아니라 위험확률로 쓰라**는 직접 처방. (추론) 우리 기준은 "κ ≥ 0.8"이 아니라 "**q(α < 0.667) ≤ 0.05**" 같은 형태가 옳다. 41편 × 필드별 레코드는 부트스트랩 표본으로 충분하다.
- 관례적 절단값(α ≥ .800 신뢰, .667~.800 잠정, < .667 폐기)은 Krippendorff의 *Content Analysis* 교과서에 나오는 것으로 널리 인용되나, **위 두 PDF 본문에서 그 문장 자체를 그대로 찾지는 못했다**. 위 Hayes & Krippendorff의 α_min = 0.67/0.70/0.80 계산 예시가 그 관례를 반영한다(추론).

### 2.3 LLM 데이터 추출 평가 연구 (2024–2026)

| 연구 | 대상/규모 | 출처가 보고한 수치 | 권고 역할 |
|---|---|---|---|
| **Gartlehner 2024** *Res Synth Methods* 15(4):576-589, doi:10.1002/jrsm.1710 | Claude 2, RCT 10편 × 16 항목 = 160 data elements | "overall accuracy of **96.3%**", 재현 "replication 1: 96.9%; replication 2: 95.0%", "Claude 2 made **6 errors on 160** data items. The most common errors (**n = 4**) were **missed data items**" | proof-of-concept; 효율·정확도 향상 잠재력 |
| **Konet 2024** *Res Synth Methods* 15(5):818-824, doi:10.1002/jrsm.1732 | Claude 2 vs GPT-4, 같은 10편 | Claude 2 **96.3%**, GPT-4(플러그인) **68.8%** — "most of the errors were due to the plug-in"; 본문 발췌를 직접 주면 **98.7%** / **100%** | "it remains essential for a **human investigator to validate LLM extractions**" |
| **Khraisha 2024** *Res Synth Methods* 15(4):616-626, doi:10.1002/jrsm.1715 | GPT-4, human-out-of-the-loop, 다국어·회색문헌 | 우연일치·데이터 불균형 보정 시 "performance scores to drop across all stages: for data extraction, performance was **moderate**" | "substantial caution should be exercised" |
| **Schmidt 2024/2025** arXiv:2405.14445 | GPT-4, 임상/동물/사회과학 각 10편 + EBM-NLP 100초록 | "accuracy of around 80% ... **82%** for human clinical, **80%** for animal, **72%** for human social sciences"; PICO 중 participants·intervention/control >80%, outcomes는 난항 | "value in using LLMs, for example as **second or third reviewers**" |
| **Reason 2024** *PharmacoEcon Open* 8:205-220, doi:10.1007/s41669-024-00476-9 | GPT-4, NMA 4 사례 | "**> 99% success rate** of accurately extracting data across 20 runs" | 수동 분석과 동일한 기술적 검증 병행 권고 |
| **Lai 2025** *npj Digit Med* 8:74, doi:10.1038/s41746-025-01457-w | 107 trials, 추출 + risk of bias | Moonshot-v1-128k, Claude-3.5-sonnet "high accuracy (**≥95%**)", LLM-assisted "**≥97%**"; 시간 14.7·5.9분 vs 86.9·10.4분 | 인간 전문성과 결합 시 유효 |
| **Gartlehner 2025** *Ann Intern Med* 178(12):1763-1771, doi:10.7326/ANNALS-25-00739 | 6개 진행 중 SR, **9,341 data elements / 63 studies** | AI-assisted **91.0% (CI 90.4–91.6)** vs human-only **89.0% (CI 88.3–89.6)**; sensitivity 89.4% vs 86.5%; "reduced data extraction time by a median of **41 minutes per study**" | "a viable, more efficient alternative to human-only methods" |
| **Shankar, Lim, Qian 2026** *J Biomed Inform* 181:105086, doi:10.1016/j.jbi.2026.105086 | 27편 평가연구의 체계적 문헌고찰(2025-12까지 검색) | 정확도 **47%–99.9%**; 범주형·문자열 **74–96%** vs 수치형 **47–88%**; **오류의 60–74%가 누락(omission)**, 환각(hallucination) **0.08–6%**; 시간절감 33–87%; Claude vs GPT event counts **OR 1.70** | "as **assistive tools within dual-extraction workflows requiring human verification, rather than as autonomous extractors**" |
| **Peng 2025** *BMJ Open* 15:e106546, doi:10.1136/bmjopen-2025-106546 | RCT 프로토콜 (1:2 배정) | AI추출+인간검증 vs 인간이중추출, 주결과 "the percentage of correct extractions" | (프로토콜; 결과 미발표) |
| **Hilkenmeier 2025** *Soc Sci Comput Rev*, doi:10.1177/08944393251404052 | Elicit, 43편 × 602 data points | Elicit **81.4%** vs human **86.7%**, 차이 비유의; ground truth는 3인 합의 | "semi-automated second reviewer" — **출판사 페이지를 직접 열지 못함**(§5) |

- 층 대응: **layer 3·4 통과기준의 근거**. Shankar 2026의 **"오류의 60–74%가 누락"** 은 layer 3(recall)이 layer 1(verbatim)보다 우선 예산 대상이라는 직접 근거다. 환각률 0.08–6%는 layer 1 예상 적발률의 하한(추론). Konet 2024의 "본문 발췌를 주면 98.7~100%"는 PDF 통째가 아니라 **문단 단위 투입**이 맞다는 뜻이고, 이는 layer 3의 shingle coverage와 자연스럽게 맞물린다(추론).

### 2.4 정답을 모를 때의 recall 추정 (layer 3의 핵심)

**(8) 포획-재포획(capture–recapture)**
- Kastner M, Straus SE, McKibbon KA, Goldsmith CH. "The capture-mark-recapture technique can be used as a stopping rule when searching in systematic reviews." *J Clin Epidemiol* 2009;62(2):149-157. doi:10.1016/j.jclinepi.2008.06.001, PMID 18722088.
- 출처가 말한 것: CMR(Horizon Estimate) 모형으로 "the total number of potential articles was **1,838** for the first level of screening, and **49** for the full-text level. The four databases provided **68%** of known articles for the first level of screening and **81%** for full-text screening." 결론은 "The CMR technique can be used in systematic reviews to estimate the closeness to capturing the total body of literature."
- Rücker G, Reiser V, Motschall E, Binder H, Meerpohl JJ, Antes G, Schumacher M. "Boosting qualifies capture-recapture methods for estimating the comprehensiveness of literature searches for systematic reviews." *J Clin Epidemiol* 2011;64(12):1364-1372. doi:10.1016/j.jclinepi.2011.03.008, PMID 21684116.
- 출처가 말한 것: 수동 모형선택은 "82 missing articles (95% CI: 52-128)", boosting은 "127 (95% CI: 86-186)"; 두 번째 예에서는 140 (116-168) vs 188 (159-223). 결론: "manual model selection yielded large estimates, varying markedly, with broad confidence intervals. By contrast, **boosting was robust against overfitting**."
- 층 대응(추론): **layer 3의 교차추출자 diff를 그대로 2-source capture–recapture로 읽을 수 있다.** Claude만 a, Codex만 b, 둘 다 c → Lincoln–Petersen N̂ ≈ (a+c)(b+c)/c, 누락 = N̂ − (a+b+c). Rücker의 경고는 **두 추출자가 독립이 아니면(같은 프롬프트·같은 섹션 우선순위) 추정치가 크게 편향된다**는 뜻으로 읽어야 한다.
- 주의: Lincoln–Petersen/Chapman/Chao 각 추정량의 원 논문은 열지 않았다.

**(9) TAR 정지규칙 — target method / knee method (Cormack & Grossman)**
- 원전: Cormack GV, Grossman MR. "Engineering Quality and Reliability in Technology-Assisted Review." *SIGIR* 2016. doi:10.1145/2911451.2911510 — **DOI 랜딩(dl.acm.org)이 403이라 직접 열지 못했다**(§5). 아래 정의는 이를 인용·재구현한 열람 가능한 2차 출처에서 가져왔다.
- 경유 출처: Stevenson M, Bin-Hezam R. "Stopping Methods for Technology Assisted Reviews based on Point Processes." *ACM TOIS* (2024). <https://arxiv.org/pdf/2311.08597> (PDF 본문 추출 성공)
- 출처가 말한 것 — **target method**: "The target method [15] attempts to overcome these limitations with an approach that **guarantees a target recall will be achieved with a specified confidence level**. The approach proceeds by randomly sampling documents from the collection to identify a 'target set' of relevant documents. Once these have been identified, all documents in the ranking are examined up to the final one in the target set. ... Cormack and Grossman [15] state that a **target set size of 10 is sufficient to guarantee recall of 0.7 with 95% confidence**."
- 출처가 말한 것 — **knee method**: "The knee method [15] ... makes use of a 'knee detection' algorithm [51] to identify an **inflection point in the gain curve** produced by plotting the cumulative total of relevant documents identified against the rank. The slope ratio, ρ, at a point in the gain curve is computed as the gradient preceding that point divided by the curve gradient immediately following it. ... Cormack and Grossman [15] suggest **6 as a suitable value of ρ** in experiments where the target recall is 0.7."
- 층 대응: **layer 3의 정지규칙**. (추론) 우리 판으로 옮기면 — 41편에서 **무작위로 10개의 "반드시 잡혀야 할" 근거 스팬을 사람이 미리 골라 target set으로 숨겨 두고**, 두 추출자의 합집합이 그 10개를 전부 포함할 때 비로소 recall ≥ 0.7(95% 신뢰)을 주장한다. 이는 아래 (12) gold-standard seeding과 같은 장치다.

**(10) Elusion 검정과 통계적으로 유효한 정지규칙**
- Lewis DD, Yang E, Frieder O. "Certifying One-Phase Technology-Assisted Reviews." *CIKM* 2021. arXiv:2108.12746. (PDF 본문 추출 성공)
- 출처가 말한 것(§3, p.3): "Other measures of interest in TAR are precision = TP/(TP+FP) and **elusion = FN/(FN+TN)**. Elusion (which one desires to be low) can be thought of as **precision in the unreviewed documents** and has mostly seen use in the law." 또한 반복 표본검정의 위험을 명시한다: "all RPET approaches suffer from **sequential bias induced by multiple testing**: the process is more likely to stop when sampling fluctuation gives" (favourable 결과를 줄 때). 초록: "we provide the **first broadly applicable and statistically valid sample-based stopping rules** for one-phase TAR."
- Yang E, Lewis DD, Frieder O. "Heuristic Stopping Rules For Technology-Assisted Review." *DocEng* 2021. arXiv:2106.09871. 초록: "We propose two new heuristic stopping rules, **Quant and QuantCI** based on model-based estimation techniques from survey research. We compare them against a range of proposed heuristics and find they are accurate at hitting a range of recall targets while substantially reducing review costs."
- 층 대응: **layer 3의 잔차 확인을 정식화한다.** (추론) 우리 판 elusion test: 두 추출자가 모두 "근거 아님"으로 넘긴 문단에서 무작위 n개를 사람이 읽고, 실제 추출 대상이었던 비율이 elusion — 이 값으로 recall을 역산한다. **경고**: Lewis의 sequential bias 지적 때문에 "미달이면 더 돌리고 다시 표본"을 반복하면 통과기준이 무효가 된다. 표본 크기와 임계값을 **사전 고정**할 것.

**(11) Chao 추정량을 정지기준으로**
- Bron MP, van der Heijden PGM, Feelders AJ, Siebes APJM. "Using Chao's Estimator as a Stopping Criterion for Technology-Assisted Review." arXiv:2404.01176 (2024-04-01).
- 출처가 말한 것(초록): "we propose and evaluate a new ensemble-based Active Learning strategy and **a stopping criterion based on Chao's Population Size Estimator** that estimates the prevalence of relevant documents in the dataset. Our simulation study demonstrates that this criterion performs well on several datasets."
- 층 대응: layer 3. 2-source 대신 **"추출 빈도 분포"에서 미관측 개수를 추정**하는 쪽이며, 우리의 numeric-token sweep처럼 여러 신호가 같은 스팬을 여러 번 건드리는 상황에 맞다(추론).

**(12) 최신 종합**: Fletcher AHA, Stevenson M. "Confidence-Based Stopping Methods for Systematic Reviews." SIGIR '26 (2026-07). arXiv:2606.15380 — knee/target을 포함한 정지규칙 계보를 정리하고 비교한다(위 인용문 일부는 이 논문에서도 동일하게 확인됨).

### 2.5 수용 표집(acceptance sampling)과 오류율 상한

- **Rule of three**: 표본 n에서 사건이 0건이면 모비율의 95% 상한이 대략 3/n. 원전은 Hanley JA, Lippman-Hand A. "If nothing goes wrong, is everything all right? Interpreting zero numerators." *JAMA* 1983;249(13):1743-1745. — **원문 PDF가 스캔 이미지라 본문을 확인하지 못했다**(§5). 따라서 이 규칙은 2차 인용으로만 쓰고, 실제 계산은 아래 정확법으로 대체하는 편이 안전하다(추론).
- **Clopper–Pearson 정확 이항 신뢰구간**과 표본크기 n ≈ 4/W²(폭 W의 95% CI; W = 0.05 → n ≈ 400, W = 0.03 → n ≈ 1000)는 표준 통계이며 특정 논문에 귀속되지 않는다. 본 조사에서 **원전을 특정해 열지 못했으므로 출처표에서 제외**했다.
- (추론) 실무 기준: 41편 × 두 추출자에서 나온 전체 레코드 모집단에서 **무작위 300건**을 층화표집(층 = kind 태그)해 사람이 원문 대조하면, 관측 오류 0건일 때 오류율 95% 상한 ≈ 1%, 관측 3건일 때 점추정 1%·상한 약 2.9%. 이 숫자를 "layer 1·2의 전수검사 대신 쓰는 감사 표본"의 크기로 쓸 수 있다.

### 2.6 NLP 데이터셋 구축의 주석 품질관리

**(13) Programmatic Gold (gold-standard seeding, attention check의 원형)**
- Oleson D, Sorokin A, Laughlin G, Hester V, Le J, Biewald L. "Programmatic Gold: Targeted and Scalable Quality Assurance in Crowdsourcing." *Human Computation: Papers from the 2011 AAAI Workshop (WS-11-11)*, CrowdFlower. <https://cdn.aaai.org/ocs/ws/ws0800/3995-16701-1-PB.pdf> (PDF 본문 추출 성공)
- 출처가 말한 것(§2.1): "A gold standard dataset is a set of **gold units, each with a known correct answer j\* and a feedback message** explaining why the answer is chosen. We can explicitly estimate worker accuracy by **randomly injecting gold units into the workflow**." / 정확도는 "a_gold = 1 − N_missed/N_shown" 이고 "computed only after the worker has seen **at least N₀ = 4 gold units**"; 정확도가 t_reject 미만이면 "they are rejected from the task", 그보다 높은 t_warn에서 경고. 훈련 모드는 "Training continues until the worker has completed **N_training = 4 gold units correctly**"이며 훈련 중 실수는 이후 정확도 추정에 반영하지 않는다. 작업자는 gold 정답에 **이의를 제기할 수 있고**("contest the gold message"), 받아들여지면 그 답은 정답으로 처리된다.
- 층 대응(추론): **스케일업 전 게이트.** 사람이 만든 정답 excerpt 레코드 20~40건을 41편 사이에 섞어 두고, 각 프롬프트 리비전이 a_gold ≥ t_reject를 넘겨야 전체 코퍼스에 투입한다. "이의 제기 후 gold 수정" 경로는 **정답셋 자체의 오류를 잡는 장치**로 그대로 가져올 값이 있다.

**(14) 실제 NLP 데이터셋들이 얼마나 지키는가**
- Klie J-C, Eckart de Castilho R, Gurevych I. "Analyzing Dataset Annotation Quality Management in the Wild." arXiv:2307.08153 (2023-07-16 제출, 2024-03-09 개정).
- 출처가 말한 것(초록): 텍스트 데이터셋을 소개하는 **591편**을 "annotator management, agreement, adjudication, or data validation" 관점에서 주석했고, 다수는 좋거나 훌륭한 품질관리를 적용하지만 "**30% of the works**"는 미흡했으며, 연구자들이 "errors, especially when **using inter-annotator agreement and computing annotation error rates**"를 자주 범한다고 보고한다.
- 층 대응: 통과기준 문서화. (추론) 이 논문이 지적하는 대표적 실수 — 표본크기 근거 없이 "100건" 같은 어림수로 오류율을 재는 것 — 은 §2.5의 표본크기 계산으로 정확히 막을 수 있다.

### 2.7 GRADE / risk-of-bias 식 확실성 태깅 ( `kind` 태그의 유비 — 간략)

- Cochrane Handbook Chapter 14, "Completing 'Summary of findings' tables and grading the certainty of the evidence." <https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-14> (열림)
- 출처가 말한 것: §14.2.1 확실성 정의 "the extent to which one can be confident that an estimate of effect or association is close to the quantity of specific interest", 4단계(high/moderate/low/very low). §14.2.2 하향 5영역: risk of bias, inconsistency, **indirectness**("evidence addressing a restricted version of the main review question"), imprecision, publication bias. 심각하면 1단계, 매우 심각하면 2단계 하향.
- 원전 Guyatt GH 외. "GRADE: an emerging consensus on rating quality of evidence and strength of recommendations." *BMJ* 2008;336(7650):924-926. doi:10.1136/bmj.39489.470347.AD — **직접 열지 못했다**(§5).
- 층 대응(추론): `kind` 사다리(production observation > testbed > simulation > secondary citation > author interpretation)는 GRADE의 "설계에 따른 시작 등급"과 같은 구조이고, **indirectness가 layer 7(정의 비교가능성)의 정확한 대응물**이다 — 같은 비교 행에 정의 태그가 다른 값을 놓는 것이 곧 indirectness. Table 1 각 행에 4단계 확실성 기호를 붙이면 layer 5의 조건 유실이 표 위에서 바로 보인다.

---

## 3. 7층 × 방법 × 출처 대응표

| 층 / 기준 | 대응 방법 | 출처 번호(§4) |
|---|---|---|
| L1 verbatim fidelity | 감사 표본 + 정확 이항 CI; gold unit 주입 | 13, (표본크기는 추론) |
| L2 number & kind 태깅 | κ/α 필드별 적용; GRADE식 확실성 등급; LLM 오류 유형 분포(누락 60–74%, 환각 0.08–6%) | 4,5,6,7,8,18,30 |
| **L3 recall / completeness** | 2-source capture–recapture(교차추출자 diff), Chao 추정량, elusion 검정, target/knee 정지규칙, Quant/QuantCI | 19,20,21,22,23,24,25,26,27 |
| **L4 교차추출자 판정** | Cochrane 이중 독립추출 + 사전정의 판정(C45/C46), 불일치 건만 사람이 원문(§5.5.5); 단일 vs 이중 오류차 21.7%; α_min 미달확률 q | 1,2,3,4,7,8,9 |
| L5 상향 조건 유실 | MECIR C51(원보고 대비 크기·방향 검증); GRADE indirectness/imprecision 하향 | 2,30 |
| L6 내부 일관성·산술 | MECIR C51; 추출오류가 효과추정치에 미치는 영향(최대 50% 논문에 오류) | 2,4 |
| L7 정의 비교가능성 | GRADE indirectness; Artstein & Poesio의 범주 간 거리·단위화 | 7,30 |
| 통과기준(정량) | q(α<α_min) ≤ 0.05; target set 10 → recall 0.7 @95%; knee ρ≈6; 감사표본 n≈300 → 오류율 상한 ~1%(0건 시) | 8,22,23, (n은 추론) |
| 스케일업 전 게이트 | gold unit N₀=4 이후 정확도 산출, t_reject 미달 시 투입 중단; 파일럿 양식(C43) | 1,2,13 |

---

## 4. 출처 표

| # | 제목 | 저자/기관 | 연도 | URL | 열림 |
|---|---|---|---|---|---|
| 1 | Cochrane Handbook Ch.5: Collecting data | Li, Higgins, Deeks (Cochrane) | current (2024–) | https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-05 | ✅ |
| 2 | MECIR standards C43–C51, Collecting data from included studies | Cochrane | current | https://www.cochrane.org/authors/handbooks-and-manuals/mecir-manual/standards-conduct-new-cochrane-intervention-reviews-c1-c75/performing-review-c24-c75/collecting-data-included-studies-c43-c51 | ✅ |
| 3 | Single data extraction generated more errors than double data extraction | Buscemi, Hartling, Vandermeer, Tjosvold, Klassen | 2006 | https://doi.org/10.1016/j.jclinepi.2005.11.010 (PMID 16765272) | ✅ (Europe PMC 경유) |
| 4 | Frequency of data extraction errors and methods to increase data extraction quality | Mathes, Klaßen, Pieper | 2017 | https://doi.org/10.1186/s12874-017-0431-4 (PMID 29179685) | ✅ (Europe PMC 경유; Springer 직링크는 로그인 리다이렉트) |
| 5 | A Coefficient of Agreement for Nominal Scales | Cohen J | 1960 | https://doi.org/10.1177/001316446002000104 | ❌ 원문 미열람 |
| 6 | The Measurement of Observer Agreement for Categorical Data | Landis JR, Koch GG (*Biometrics* 33(1):159-174) | 1977 | https://doi.org/10.2307/2529310 | ❌ 원문 미열람 |
| 7 | Survey Article: Inter-Coder Agreement for Computational Linguistics | Artstein R, Poesio M (*Computational Linguistics* 34(4)) | 2008 | https://aclanthology.org/J08-4004/ | ✅ (서지 확인; 초록 본문은 해당 페이지에 없음) |
| 8 | Answering the Call for a Standard Reliability Measure for Coding Data | Hayes AF, Krippendorff K (*Comm Methods & Measures* 1(1):77-89) | 2007 | https://www.asc.upenn.edu/sites/default/files/2021-03/Answering%20the%20Call%20for%20a%20Standard%20Reliability%20Measure%20for%20Coding%20Data.pdf | ✅ 본문 추출 |
| 9 | Computing Krippendorff's Alpha-Reliability | Krippendorff K (UPenn) | 2011 (lit. upd. 2013) | https://www.asc.upenn.edu/sites/default/files/2021-03/Computing%20Krippendorff's%20Alpha-Reliability.pdf | ✅ 본문 추출 |
| 10 | Data extraction for evidence synthesis using a large language model: proof-of-concept | Gartlehner G 외 12인 (RTI/Danube Univ) | 2024 | https://doi.org/10.1002/jrsm.1710 (PMID 38432227) | ✅ (Europe PMC 경유; Wiley 직링크 403) |
| 11 | Can large language models replace humans in systematic reviews? (GPT-4) | Khraisha Q, Put S, Kappenberg J, Warraitch A, Hadfield K | 2024 | https://doi.org/10.1002/jrsm.1715 (PMID 38484744) | ✅ (Europe PMC 경유; Wiley 직링크 403) |
| 12 | Performance of two large language models for data extraction in evidence synthesis | Konet A, Thomas I, Gartlehner G 외 | 2024 | https://doi.org/10.1002/jrsm.1732 (PMID 38895747) | ✅ (Europe PMC 경유) |
| 13 | Exploring the use of a Large Language Model for data extraction in systematic reviews | Schmidt L, Hair K, Graziosi S 외 | 2024 (v2 2025-02) | https://arxiv.org/abs/2405.14445 | ✅ |
| 14 | Artificial Intelligence to Automate Network Meta-Analyses: Four Case Studies | Reason T, Benbow E, Langham J, Gimblett A, Klijn SL, Malcolm B | 2024 | https://doi.org/10.1007/s41669-024-00476-9 (PMID 38340277) | ✅ (Europe PMC 경유) |
| 15 | Language models for data extraction and risk of bias assessment in complementary medicine | Lai H 외, ADVANCED Working Group (*npj Digit Med* 8:74) | 2025 | https://doi.org/10.1038/s41746-025-01457-w (PMID 39890970) | ✅ (Europe PMC 경유) |
| 16 | AI-Assisted Data Extraction With a Large Language Model: A Study Within Reviews | Gartlehner G 외 17인 (*Ann Intern Med* 178(12)) | 2025 | https://doi.org/10.7326/ANNALS-25-00739 (PMID 41183336) | ✅ (Europe PMC 경유) |
| 17 | Evaluating the AI Tool "Elicit" as a Semi-Automated Second Reviewer | Hilkenmeier F, Pelzer M, Stierle C, Fink-Lamotte J | 2025 | https://doi.org/10.1177/08944393251404052 | ❌ 출판사 페이지 미열람(검색 요약만) |
| 18 | Performance of large language models in data extraction for evidence synthesis: A systematic review | Shankar R, Lim A, Qian X (*J Biomed Inform* 181:105086) | 2026 | https://doi.org/10.1016/j.jbi.2026.105086 (PMID 42501879) | ✅ (Europe PMC 경유) |
| 19 | Comparing the accuracy of AI-assisted data extraction versus human double extraction: RCT protocol | Peng Z, Fan S, Tian Y 외 (*BMJ Open* 15:e106546) | 2025 | https://doi.org/10.1136/bmjopen-2025-106546 (PMID 41198207) | ✅ (Europe PMC 경유) |
| 20 | The capture-mark-recapture technique can be used as a stopping rule when searching in systematic reviews | Kastner M, Straus SE, McKibbon KA, Goldsmith CH | 2009 | https://doi.org/10.1016/j.jclinepi.2008.06.001 (PMID 18722088) | ✅ (Europe PMC 경유) |
| 21 | Boosting qualifies capture-recapture methods for estimating comprehensiveness of literature searches | Rücker G, Reiser V, Motschall E 외 | 2011 | https://doi.org/10.1016/j.jclinepi.2011.03.008 (PMID 21684116) | ✅ (Europe PMC 경유) |
| 22 | Engineering Quality and Reliability in Technology-Assisted Review (SIGIR '16) — target/knee method 원전 | Cormack GV, Grossman MR | 2016 | https://doi.org/10.1145/2911451.2911510 | ❌ dl.acm.org 403 |
| 23 | Stopping Methods for Technology Assisted Reviews based on Point Processes (*ACM TOIS*) | Stevenson M, Bin-Hezam R (Univ. of Sheffield) | 2024 | https://arxiv.org/pdf/2311.08597 (also https://doi.org/10.1145/3631990) | ✅ 본문 추출 |
| 24 | Heuristic Stopping Rules For Technology-Assisted Review (DocEng '21) — Quant, QuantCI | Yang E, Lewis DD, Frieder O | 2021 | https://arxiv.org/abs/2106.09871 | ✅ |
| 25 | Certifying One-Phase Technology-Assisted Reviews (CIKM '21) — elusion 정의, sequential bias | Lewis DD, Yang E, Frieder O | 2021 | https://arxiv.org/abs/2108.12746 | ✅ 본문 추출 |
| 26 | Using Chao's Estimator as a Stopping Criterion for Technology-Assisted Review | Bron MP, van der Heijden PGM, Feelders AJ, Siebes APJM | 2024 | https://arxiv.org/abs/2404.01176 | ✅ |
| 27 | Confidence-Based Stopping Methods for Systematic Reviews (SIGIR '26) | Fletcher AHA, Stevenson M | 2026 | https://arxiv.org/html/2606.15380 | ✅ |
| 28 | Programmatic Gold: Targeted and Scalable Quality Assurance in Crowdsourcing (AAAI HCOMP WS-11-11) | Oleson D, Sorokin A, Laughlin G, Hester V, Le J, Biewald L (CrowdFlower) | 2011 | https://cdn.aaai.org/ocs/ws/ws0800/3995-16701-1-PB.pdf | ✅ 본문 추출 |
| 29 | Analyzing Dataset Annotation Quality Management in the Wild | Klie J-C, Eckart de Castilho R, Gurevych I (UKP/TU Darmstadt) | 2023 (rev. 2024) | https://arxiv.org/abs/2307.08153 | ✅ |
| 30 | Cochrane Handbook Ch.14: grading the certainty of the evidence (GRADE) | Cochrane | current | https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-14 | ✅ |
| 31 | If nothing goes wrong, is everything all right? (rule of three 원전, *JAMA* 249(13):1743-5) | Hanley JA, Lippman-Hand A | 1983 | https://jhanley.biostat.mcgill.ca/Reprints/If_Nothing_Goes_1983.pdf | ❌ 스캔 PDF, 본문 추출 실패 |

총 31건. 열어서 확인 26건 / 확인 실패 5건(#5, #6, #17, #22, #31).

---

## 5. 못 찾은 것 · 불확실한 것

1. **Cohen 1960, Landis & Koch 1977 원문**: 열지 못했다. κ 구간 해석표(0.61–0.80 substantial 등)는 검색 요약과 2차 출처에서만 확인했으므로, 논문에 쓸 때는 **2차 인용으로 표기**하거나 원문을 별도 확보해야 한다.
2. **Krippendorff α의 .800/.667 절단값**: "α ≥ .800에 의존, .667–.800은 잠정"이라는 관례는 널리 통용되나, 내가 본문까지 확인한 두 PDF(#8, #9)에서 **그 문장 자체를 그대로 찾지는 못했다**. #8에서 확인한 것은 α_min = 0.67/0.70/0.80에 대한 미달확률 q 계산 예시다. 원 출처는 Krippendorff의 *Content Analysis: An Introduction to Its Methodology* 단행본으로 보이며, 이 조사에서는 확보하지 못했다.
3. **Hanley & Lippman-Hand 1983 (rule of three)**: McGill 리프린트 PDF가 스캔 이미지여서 본문 문장을 확인할 수 없었다. 3/n 규칙 자체는 널리 쓰이지만, **이 출처의 문장을 인용하지는 말 것**. 대신 Clopper–Pearson 정확구간으로 직접 계산하는 편이 안전하다.
4. **Cormack & Grossman 2016 SIGIR 원전**: DOI 랜딩이 403이었다. target set 10 → recall 0.7 @ 95%, knee ρ = 6은 **Stevenson & Bin-Hezam(#23)이 원전을 인용한 문장**에서 가져왔으므로, 정확히는 2차 인용이다.
5. **Hilkenmeier 2025 (Elicit, 81.4% vs 86.7%)**: Sage 페이지를 열지 못했고 검색 요약만 확보했다. 인용하려면 원문 확인이 필요하다.
6. **Guyatt 2008 BMJ GRADE 원전**: PubMed/BMJ 모두 열리지 않았다. GRADE 서술은 열람 가능한 Cochrane Handbook Ch.14(#30)로 대체했다.
7. **acceptance sampling의 원전 특정 실패**: "n = 4/W²", Clopper–Pearson 등은 표준 통계라 특정 논문에 귀속되지 않고, 이 조사에서 권위 있는 단일 원전을 특정하지 못했다. 출처표에서 제외했고, §2.5의 구체 숫자(n≈300 → 상한 ~1%)는 **내 계산(추론)** 이다.
8. **Li 2015 / Jonnalagadda 2015**: 과제 지시에 언급된 "Li 2015"는 Li T 외 "Innovations in Data Collection, Management, and Archiving for Systematic Reviews" (*Ann Intern Med* 2015)로 보이나, 단일 vs 이중 추출 오류율을 **직접 비교한 수치**는 확인하지 못했다. 그 역할은 Buscemi 2006(#3)과 Mathes 2017(#4)로 충분히 커버된다.
9. **LLM 추출 수치 간 비교 함정**: #10(96.3%)과 #16(91.0%)은 분모가 다르다(160 항목·편의표본 vs 9,341 항목·6개 진행 중 SR). #18의 범위 "47%–99.9%"에서 상단은 **단일 데이터포인트 수준**이고 연구 단위 정확도는 더 낮다고 #18이 명시했다. 이 숫자들을 한 행에 나란히 놓으면 그 자체가 layer 7 위반이다(추론).
