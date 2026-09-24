# 갈래 B 검증 장부 (Fable 직접 확인, 2026-09-21)

방법: 의학 문헌은 Europe PMC REST로 초록을 받아 숫자 문장을 출력해 대조했다. PDF는 pdftotext로 풀어 grep했다. Cochrane 페이지는 WebFetch.

| # | 출처 | 보고서 주장 | 확인 결과 | 확인 경로 |
|---|---|---|---|---|
| 2 | MECIR C43·C45·C46·C51 | C46 Mandatory 「two people working independently … outcome data … define in advance the process for resolving disagreements」, C45 Highly desirable, C43 piloted form, C51 magnitude and direction 대조 | **일치** | MECIR 페이지 |
| 3 | Buscemi 2006 | 단일 추출이 이중 추출보다 오류 상대 21.7% 더 많음 (P = .019), 시간 36.1% 절감 (P = .003) | **일치** | Europe PMC 초록 |
| 4 | Mathes 2017 | 추출 오류율 「up to 50%」 | **일치** | Europe PMC 초록 |
| 8 | Hayes & Krippendorff 2007 | CI 0.7078–0.8078, q = 0.0125 (α_min 0.70), q = 0.9473 (α_min 0.80), 「serious trouble」 | **일치** | PDF 줄 274–290 |
| 10 | Gartlehner 2024 | Claude 2, 10편 × 16항목 = 160, 정확도 96.3%, 재현 96.9/95.0, 오류 6건 중 누락 4건 | **일치** | Europe PMC 초록 |
| 12 | Konet 2024 | Claude 2 96.3%, GPT-4 플러그인 68.8%, 발췌 제공 시 98.7%/100% | **일치** | Europe PMC 초록 |
| 13 | Schmidt 2024 | 약 80%, 82/80/72%, 「second or third reviewers」 | **일치** | arXiv 초록 |
| 14 | Reason 2024 | >99%, 20 runs | **일치** | Europe PMC 초록 |
| 15 | Lai 2025 | ≥95%, LLM 보조 ≥97%, 14.7·5.9분 대 86.9·10.4분 | **일치** | Europe PMC 초록 |
| 16 | Gartlehner 2025 | 9,341 항목·63 연구, AI 보조 91.0% (90.4–91.6) 대 사람 89.0%, 민감도 89.4/86.5, 41분 절감 | **일치** | Europe PMC 초록. 추가로 두 방법 일치율 77.2%, 중대 오류 2.5% 대 2.7%도 초록에 있음 |
| 18 | Shankar 2026 | 27편, 47–99.9%, 범주형 74–96% 대 수치형 47–88%, 누락 60–74%, 환각 0.08–6%, OR 1.70 | **일치** | Europe PMC 초록 |
| 11 | Khraisha 2024 | 우연 일치·불균형 보정 시 추출 성능 「moderate」 | **일치** | Europe PMC 초록 |
| 20 | Kastner 2009 | 1,838 / 49, 68% / 81% | **일치** | Europe PMC 초록 |
| 21 | Rücker 2011 | 82 (52–128) 대 127 (86–186), 140 (116–168) 대 188 (159–223) | **일치** | Europe PMC 초록 |
| 23 | Stevenson & Bin-Hezam 2024 | target set 10이면 95% 신뢰로 recall 0.7, knee ρ = 6 | **일치** (Cormack & Grossman의 2차 인용임을 보고서도 명시) | PDF 줄 142, 160–165 |
| 25 | Lewis 2021 | elusion = FN/(FN+TN), 「precision in the unreviewed」, 「sequential bias induced by multiple testing」, 「first broadly applicable and statistically valid」 | **일치** | PDF 줄 18, 101–102, 401 |
| 28 | Programmatic Gold 2011 | a_gold = 1 − N_missed/N_shown, N₀ = 4, N_training = 4, contest 가능 | **일치** | PDF 줄 99–119, 276 |
| 29 | Klie 2023 | 591편, 30% subpar, IAA·오류율 계산 실수 | **일치** | arXiv 초록 |
| 5, 6, 17, 22, 31 | Cohen 1960, Landis & Koch 1977, Hilkenmeier 2025, Cormack & Grossman 2016, Hanley & Lippman-Hand 1983 | 보고서가 미열람으로 표시 | 확인 생략. **2차 인용으로만 취급** | — |

## 판정

- 수치 주장 18건 중 원문과 다른 것 **0건**.
- 보고서 §5의 미확인 항목은 그대로 유효하다. Krippendorff α의 .800/.667 절단값과 rule of three는 원문 문장을 확인하지 못했으므로 인용하지 않는다.
- 채택할 함의(추론): 추출 오류의 다수가 누락이므로 3층(재현율)에 1층(원문 일치)보다 예산을 더 둔다. 「한쪽이 추출하고 다른 쪽이 검토」는 Buscemi가 열등하다고 본 구조이므로 두 추출기의 독립을 유지한다. 통과 기준은 점추정 κ가 아니라 α_min 미달 확률 q로 둔다. 잔여 문단 표본 검사는 크기와 임계를 사전 고정하고 재표집하지 않는다.
