# 갈래 C 검증 장부 (Fable 직접 확인, 2026-09-21)

| # | 출처 | 보고서 주장 | 확인 결과 | 확인 경로 |
|---|---|---|---|---|
| 3 | SciFact-Open 2022 | 500K 초록, 279 claims, 「at least 15 F1」, specificity mismatch 91/206 (44%), 표 53/18/20, 충돌 증거 문장 | **일치**. 「81 claims 중 16 (20%)」은 본문 열 분리로 grep이 어긋나 아래 별도 확인 | PDF 줄 34–86, 269–311 |
| 4 | ContraDoc 2024 | 449/442, 100–2200 토큰, 73/220/155, Numeric 유형, GPT4 「outperform humans … still unreliable」 | **일치** | PDF 줄 39–40, 157, 194–226 |
| 18 | SoK Benchmarking Flaws 2019 | 22 결함, 50편, 평균 5, 무결함 1편, B3 bad math 10%→20% = 100% more, 5s→20s 75% 대 300%, B5 geometric mean, D1 no baseline, A2 incomparable | **일치** | PDF 줄 21, 94, 200–227, 538, 745, 805, 208 |
| 17 | Cochrane ch.10 | I² 정의, 4구간, 「importance depends on」, subgroup 관찰적·다중성·「truly pre-specified」 | **일치**. 단 「공변량당 10편」 규칙은 페이지에 명시되지 않음 (보고서도 §번호 미확인이라 적음) | WebFetch |
| 5 | ClaimDiff 2023 | 2,941 쌍 / 268 기사 / 19%p 격차 | **일치** | arXiv 초록 |
| 10 | Evidence Inference 2019 | intervention·comparator·outcome, 10,000+ prompts | **일치** | ACL Anthology 초록 |
| 11 | SciClaim 2021 | 12,738 labels, 5종 association + qualifications | **일치**. 「Qualifier·Epistemic 노드 타입」은 초록에 없음 (본문 스키마 이름으로 보이나 미확인) | arXiv 초록 |
| 13 | Claimify 블로그 2025-03-19 | 99% entailed, 「Cannot be disambiguated」 | **일치** | MS 블로그 |
| 15 | δ-NLI 2020 | bird/penguin 정의, 「up to 68% of the time」 | **일치** | ACL Anthology 초록 |
| 22 | Qiu et al. 2024 | 「increasing the hit ratio can actually hurt the throughput」 | **일치** | arXiv 초록 |
| 23 | REFORMS | 32 questions, 19 researchers | **일치**. 「8개 모듈」은 초록에 없음 | arXiv 초록 |
| 28 | Nuijten 2016 | 250,000 p-values, 절반, 8편 중 1편, 49.6%/12.9% | **일치** | PMC |
| 33 | sciwrite-lint 2026 | 검사 항목 열거, 30 unseen papers, error injection | **일치** | arXiv 초록 |
| 34 | arXiVeri 2023 | AutoTV 정의, table/cell matching | **일치** | arXiv 초록 |
| 36 | Table-Text Alignment 2025 | 「fail to recover human-aligned rationales」 | **일치** | arXiv 초록 |
| 37 | QuanTemp 2024 | macro-F1 58.32 | **일치**. claims 수는 초록에 없음 (보고서도 미검증 표시) | arXiv 초록 |
| 9 | BioDivergence | 2026-08-30 철회 | **일치**. 인용 금지 | arXiv |
| 26 | Peters & Chin-Yee 2025 | 갈래 A와 동일 | **일치** | 갈래 A 장부 참조 |
| 8, 14, 16, 19, 20, 21, 24, 25, 27, 29, 30, 31, 32, 35, 38 | 미열람 표시 출처 | 보고서가 내용을 인용하지 않았거나 2차로만 씀 | 확인 생략 | — |

## 판정

- 수치 주장 17건 중 원문과 다른 것 **0건**. 초록에 없는 세부(SciClaim 노드 이름, REFORMS 모듈 수, Cochrane 10편 규칙)는 본문 확인 전까지 쓰지 않는다.
- 채택할 함의(추론): 충돌 후보의 다수가 조건·구체성 차이라는 기대 분포(SciFact-Open 44%/20%)를 설계 전제로 삼되 비율은 옮기지 않는다. 조건 축은 스윕 전에 사전 등록하고 사후 설명은 가설로 표기한다(Cochrane). 6층은 sciwrite-lint의 검사 항목과 SoK B3·B5를 그대로 항목화한다. 7층은 SoK D1·A2·F3·F4와 OHR/BHR 구분, GRADE indirectness가 가장 가까운 선례이며 전용 방법은 없다.
