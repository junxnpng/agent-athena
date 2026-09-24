# 갈래 A 검증 장부 (Fable 직접 확인, 2026-09-21)

방법: 보고서가 인용한 URL을 WebFetch로 열거나, PDF는 pdftotext로 풀어 해당 수치의 원문 줄을 grep했다.

| # | 출처 | 보고서 주장 | 확인 결과 | 확인 경로 |
|---|---|---|---|---|
| 22 | Peters & Chin-Yee 2025 | 10 LLM, 4,900 요약, 과일반화 26–73%, OR 4.85 [3.06, 7.70], 정확성 프롬프트 무효, 최신 모델이 더 나쁨 | **일치** | arXiv 2504.00025 초록. 게재지(R. Soc. Open Sci. 12:241776)는 출판사 페이지 403으로 미확인 |
| 6 | ALCE | 자동-인간 일치 recall 85.1%/κ 0.698, precision 77.6%/κ 0.525, TRUE T5-11B 사용 | **일치** | PDF 본문 §7 및 §G.5 (줄 578–584, 1045–1046) |
| 3 | TRUE | 평균 ROC AUC ANLI 81.5, SCZS 81.4, Q² 80.7, 앙상블 86.0 | **일치, 단서 하나** | 표 3의 「Avg. w/o VitC, FEVER」 행. 즉 11개 전체 평균이 아니라 VitaminC·FEVER를 뺀 9개 평균이다 |
| 5 | MiniCheck | 770M, GPT-4 정확도, 400배 저렴 | **일치** | 초록 |
| 12 | CoVe | 0.17→0.36, 환각 2.95→0.68, MultiSpanQA 0.39→0.48, FActScore 55.9→71.4, ChatGPT 58.7, Perplexity 61.6 | **일치** | PDF 표 1·2·3 (줄 308–381, 425–450) |
| 2 | AutoAIS | 시스템 수준 Pearson 0.96, 인스턴스 수준 「lower and more variable」, 「too closely」 경고, T5 11B | **일치** | PDF 줄 399, 474, 483, 543–545 |
| 21 | Dorner et al. | 「no debiasing method can decrease the required amount of ground truth labels by more than half」, ICLR 2025 | **일치** | 초록 |
| 17 | Wang et al. 2023 | 66/80, 보정 3종 | **일치** | 초록 |
| 27 | Walters & Wilder 2023 | 42주제·84편·636인용, 조작 55%/18%, 실재 인용의 실질 오류 43%/24% | **일치** | Europe PMC 초록 (nature.com은 리디렉션) |
| 24 | Factored Verification | HaluEval 76.2%, 요약당 환각 0.62/0.84/1.55 → 0.49/0.46/0.95, 「subtle」 | **일치** | PDF 초록 줄 23–33, 표 줄 174–176 |
| 8 | AttributionBench | 파인튜닝 GPT-3.5 약 80% macro-F1, 실패 원인 두 가지 | **일치** | 초록 |
| 4 | SummaC | 74.4% balanced accuracy, +5%p, 문장 단위 분할·집계 | **일치** | 초록. TACL 게재는 2022년 vol.10 (arXiv 2021) |
| 26 | FEVER | 185,445 claims, 3 라벨, Fleiss κ 0.6841, 31.87%/50.91% | **일치** | 초록 |
| 9 | RAGAS | WikiEval 일치 0.95/0.78/0.70 | **일치** | PDF 표 (줄 269). WikiEval은 저자 제작 소규모 셋 |
| 10 | FActScore | <2% 오차, 6,500 생성·13 LM·$26K, ChatGPT 58% | **일치** | 초록 |
| 11 | SAFE | 72% 일치, 불일치 100건 중 76% 승, 20배 저렴, NeurIPS 2024 | **일치** | 초록 |
| 16 | G-Eval | Spearman 0.514, LLM 생성문 선호 편향 경고 | **일치** | 초록 |
| 13 | Self-Consistency | GSM8K +17.9 등 5개 수치 | **일치** | 초록 |
| 18 | MT-Bench | >80% 일치, 편향 4종 | **일치** | 초록 |
| 19 | Shi et al. | 15 심판·22 과제·약 40 모델·15만 인스턴스, 품질 격차와 강한 상관, 길이와 약한 상관, AACL-IJCNLP 2025 | **일치** | 초록 |
| 25 | SciFact | 1.4K expert-written claims, SUPPORTS/REFUTES, rationale 지목 | **일치** | 초록 |
| 1 | AIS | 2단계 주석 파이프라인, 3개 과제 | **일치**. 「According to the source」 문구는 본문 표현이라 초록에서는 미확인 | 초록 |
| 7, 14, 15, 20, 23 | AttrScore, LM vs LM, Multiagent Debate, CALM, HERMAN | 보고서가 수치를 쓰지 않음 | 확인 생략 (수치 주장 없음) | — |

## 판정

- 수치 주장 22건 중 원문과 다른 것 **0건**. 단서가 붙는 것 1건 (TRUE 평균의 모집단).
- 보고서 §5의 「레이어 7에 대응하는 확립된 방법을 찾지 못했다」는 갈래 C 결과와 대조해 판단한다.
- 보고서의 함의(추론) 중 채택할 것: 조건 드리프트는 생성 프롬프트로 못 막고 사후 대조에 예산을 써야 한다(Peters & Chin-Yee). 자동 판정은 집계 지표로만 쓰고 개별 문장 판정은 사람에게(AutoAIS, AttributionBench). 두 추출기 비교 시 좌우 순서 교대(Wang, Shi). 심판 도입으로 사람 표본을 절반 이하로 줄일 수 없다(Dorner).
