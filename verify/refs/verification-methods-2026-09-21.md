# 발췌 검증 방법론 — 문헌 조사와 검증 결과 (2026-09-21)

> **위치 (2026-09-22 이전).** `/work/jun/AI-helper/verify/`(jun-heo/AI-helper) 기준 상대 경로. `$KVCPOOL`=`/work/jun/priv-mb-eval/kvcpool-trace-gen`은 입력 데이터가 남아 있는 원 저장소다.

41편 발췌(Claude 804·Codex 1,164 레코드)와 그 위에 세우려는 7층 검증 틀에 대해, 「AI가 이런 논리적 검증을 어떻게 잘하는가」를 다룬 확립된 방법을 찾고 그 근거를 원문으로 확인한 기록이다.

## 0. 방법

- **조사.** Opus 에이전트 셋이 갈래를 나눠 웹 조사를 했다. A: LLM 산출물의 충실성·귀속·인용 검증. B: 체계적 문헌고찰의 이중 추출·판정·재현율 추정·통과 기준. C: 문헌 간 모순 탐지, 조건 인식 비교, 문서 내 일관성. 보고서 원문은 [`verification-methods-2026-09-21/`](verification-methods-2026-09-21/)의 `opus_A_faithfulness.md`, `opus_B_evidence_synthesis.md`, `opus_C_contradiction.md`.
- **검증.** Fable(이 문서의 작성자)이 세 보고서가 인용한 출처를 직접 열었다. arXiv 초록은 WebFetch, 본문 수치가 있는 논문은 PDF를 받아 `pdftotext`로 풀고 해당 수치의 줄을 grep, 의학 문헌은 Europe PMC REST로 초록을 받아 대조했다. 장부는 같은 폴더의 `verify_A.md`, `verify_B.md`, `verify_C.md`.
- **원칙.** 아래 본문에는 원문에서 확인한 것만 적었다. 보고서가 「미열람」으로 표시했거나 내가 확인하지 못한 것은 §5와 §7에 따로 모았다.

## 1. 검증 결과 요약

| 갈래 | 보고서 출처 수 | 수치 주장 대조 | 원문과 다른 것 | 단서 |
|---|---|---|---|---|
| A 충실성·귀속 | 28 | 22건 | 0 | TRUE 평균은 11개가 아니라 VitaminC·FEVER를 뺀 9개 데이터셋 평균 |
| B 근거종합 | 31 | 18건 | 0 | 없음 |
| C 모순·조건 | 38 | 17건 | 0 | 초록에 없는 세부 셋(§7) |

세 보고서 모두 「출처가 말한 것」과 「추론」을 구분해 적었고, 표본 대조에서 인용 수치 오류는 나오지 않았다. 다만 열지 못한 출처의 수치를 검색 요약에서 가져온 자리가 있어 §7에 인용 금지 목록으로 정리했다.

## 2. 층별로 확인된 방법

### 1층 원문 일치

- **인용이 실재해도 실질 오류가 남는다.** Walters & Wilder 2023(Scientific Reports)은 636개 인용 중 실재하는 인용의 24%(GPT-4)에서 43%(GPT-3.5)에 실질 오류가 있었다고 보고한다. 문자열 일치와 별개로 §·쪽 표기를 따로 검증해야 하는 이유다.
- **판정 틀.** AIS(Rashkin 2021)는 「생성문이 명시된 출처에 귀속되는가」를 사람이 판정하는 2단계 주석 파이프라인을 정의했다. 요약 문장과 레코드 사이의 판정 문구로 그대로 쓸 수 있다.

### 2층 수치·성격 태그

- **귀속의 3분류.** AttrScore(Yue 2023)는 attributable / extrapolatory / contradictory로 나눈다. extrapolatory가 이 프로젝트의 「저자 해석·근거 초과」, contradictory가 「인용 오류」에 대응한다.
- **원자 분해.** FActScore(Min 2023)는 생성문을 atomic fact로 쪼개 개별 검증한다. 레코드의 numbers·conditions를 각각 독립 검증 단위로 두는 근거다. 자동 추정기 오차는 그 도메인에서 2% 미만이었다.
- **원보고와의 크기·방향 대조.** Cochrane MECIR C51(Mandatory)은 「연구가 보고한 효과의 크기와 방향을 리뷰에 옮긴 것과 대조하라」고 못박는다. 2층의 재계산 검사가 여기에 해당한다.
- **확실성 등급.** Cochrane Handbook 14장의 GRADE는 설계에 따른 시작 등급과 다섯 하향 사유(그중 indirectness)를 둔다. kind 태그 사다리와 같은 구조다.

### 3층 재현율

- **LLM 추출 오류의 대부분은 누락이다.** Shankar 2026(J Biomed Inform)의 27편 체계적 고찰은 오류의 60–74%가 누락이고 환각은 0.08–6%라고 보고한다. Gartlehner 2024의 160항목 실험에서도 오류 6건 중 4건이 누락이었다. 예산은 1층보다 3층에 둬야 한다.
- **문단 단위 투입이 정확도를 올린다.** Konet 2024는 PDF 통째보다 발췌 텍스트를 줬을 때 Claude 2가 98.7%, GPT-4가 100%를 냈다고 보고한다. 잔여 문단을 재추출할 때 논문 전체가 아니라 문단을 넣는 근거다.
- **정답 없이 재현율 추정.** Kastner 2009는 포획-재포획으로 문헌 검색의 포괄도를 68%(초록 수준)·81%(전문 수준)로 추정했다. Rücker 2011은 모형 선택에 따라 추정치가 크게 흔들림을 보였다. 두 추출기가 독립일 때만 2-source 추정이 성립한다.
- **정지 규칙.** Cormack & Grossman의 target method는 무작위로 찾은 목표 집합 10개를 전부 회수하면 95% 신뢰로 recall 0.7을 보장하고, knee method는 이득 곡선의 기울기비 6을 쓴다(Stevenson & Bin-Hezam 2024 경유). Lewis 2021은 elusion을 「미검토 문서에서의 정밀도」로 정의하고, 표본 검정을 통과할 때까지 반복하면 sequential bias로 보장이 깨진다고 경고한다.
- **정답 심기.** Programmatic Gold(Oleson 2011)는 정답을 아는 단위를 무작위로 섞어 작업자 정확도를 재고, 4개 이상 본 뒤에만 정확도를 계산하며, 작업자가 정답에 이의를 제기할 수 있게 한다.

### 4층 교차 판정

- **이중 독립 추출은 의무.** Cochrane MECIR C46(Mandatory)은 결과 데이터를 「두 사람이 독립으로 추출하고 불일치 해소 절차를 사전에 정하라」고 한다. C45는 연구 특성에 같은 것을 Highly desirable로 둔다.
- **추출 후 검토는 이중 추출과 다르다.** Buscemi 2006은 「단일 추출 + 검증자」가 「두 명 독립 추출」보다 오류가 상대 21.7% 많았다(P = .019)고 보고한다. Claude·Codex 구조를 「한쪽이 뽑고 다른 쪽이 검토」로 바꾸면 열등한 쪽이 된다.
- **합치도 통과 기준.** Hayes & Krippendorff 2007은 α의 점추정 대신 부트스트랩으로 「α_min에 미달할 확률 q」를 계산하라고 한다. 예시에서 CI 0.7078–0.8078인 데이터가 α_min 0.70에는 q = 0.0125, 0.80에는 q = 0.9473이었다.
- **LLM 심판의 한계.** Wang 2023은 순서만 바꿔도 80개 중 66개에서 판정이 뒤집힘을 보였고 순서 교대·근거 선기술·사람 개입 세 보정을 제안했다. Shi 2024(15만 인스턴스)는 위치 편향이 두 답의 품질 격차가 작을수록 커진다고 했다. Dorner 2024(ICLR 2025)는 심판이 피평가 모델보다 정확하지 않으면 어떤 디바이어싱도 필요한 사람 라벨을 절반 넘게 줄일 수 없음을 증명했다. AutoAIS(Bohnet 2022)는 시스템 수준 상관 0.96이지만 개별 점수는 「훨씬 낮고 변동이 크다」고 저자가 경고했고, AttributionBench(Li 2024)는 파인튜닝 판정기의 천장을 약 80% macro-F1로 보고한다.

### 5층 조건 드리프트

- **실재하는 실패 모드.** Peters & Chin-Yee 2025(R. Soc. Open Sci. 12(4))는 10개 LLM의 요약 4,900개에서 과일반화가 26–73%였고, 사람 요약 대비 OR 4.85 [3.06, 7.70]였으며, 정확성을 명시적으로 지시해도 대부분 더 넓게 일반화했고 최신 모델이 더 나빴다고 보고한다. 조건 보존은 생성 프롬프트가 아니라 사후 대조로 구현해야 한다.
- **인용 검증 템플릿.** ALCE(Gao 2023)는 citation recall(인용된 근거들이 문장을 지지하는가)과 precision(각 인용이 필요한가)을 NLI(TRUE T5-11B)로 재고, 사람과의 일치가 recall 85.1%/κ 0.698, precision 77.6%/κ 0.525였다. precision 쪽 자동화가 덜 믿을 만하다.
- **채점기.** TRUE(Honovich 2022)는 NLI·QG-QA 앙상블이 9개 데이터셋 평균 ROC AUC 86.0으로 단일 최고(81.5)보다 낫다고 보고한다. SummaC(Laban)는 문장 단위 분할·집계로 74.4% balanced accuracy. MiniCheck(Tang 2024)는 770M 모델로 GPT-4 정확도를 400배 싼 비용에 낸다. 전수 1차 스윕은 이것으로 하고 걸린 것만 강한 모델·사람에게 보낸다.
- **검증 질문의 독립 답변.** Chain-of-Verification(Dhuliawala 2023)은 검증 질문을 초안과 분리된 컨텍스트에서 답하게 해 Wikidata precision 0.17→0.36, 전기 생성 FActScore 55.9→71.4를 얻었다. 「이 문장이 암묵 가정한 조건은?」을 레코드만 보여준 새 컨텍스트에서 답하게 하는 형식이다.
- **판정 불가의 자리.** Claimify(Microsoft 2025)는 문맥으로 모호성이 안 풀리면 「Cannot be disambiguated」로 남긴다. FEVER의 NotEnoughInfo, SciFact의 rationale 지목 강제도 같은 역할이다.
- **논문 요약 기저율.** Factored Verification(George & Stuhlmüller 2023)은 학술 논문 요약에서 요약당 환각 0.62–1.55건을 찾았고 자가 수정 후 0.46–0.95건이었으며, 환각이 「subtle」하다고 적었다.

### 6층 문서 내 일치·산술

- **검사 항목 사양.** sciwrite-lint(Samsonau 2026)는 본문 대 표 숫자, 초록 대 본문, 그림 캡션 대 내용, 통계 대 서술, 끊긴 인용을 검사하고, 30편에 오류를 주입해 평가하며 오탐은 LLM이 판정한다. 6층 검사기의 사양과 평가법을 그대로 쓸 수 있다.
- **이런 오류는 흔하다.** statcheck 연구(Nuijten 2016)는 심리학 논문의 p값 25만 개를 검사해 논문의 49.6%에 불일치가, 12.9%에 결론을 바꿀 수 있는 불일치가 있었다고 보고한다.
- **산술 결함의 목록.** SoK: Benchmarking Flaws(van der Kouwe 2019)는 22개 결함 중 B3 bad math(10%→20% 오버헤드는 10%가 아니라 100% 증가, 5s→20s는 75%가 아니라 300%)와 B5 잘못된 평균(비율에는 기하평균만 적절)을 든다. 50편 중 결함 없는 논문은 1편이었다.
- **전역 모순은 어렵다.** ContraDoc(Li 2024)은 문서 내 자기모순 449건에서 GPT-4가 사람을 넘지만 여전히 불안정하다고 보고한다. 초록·캡션·본문 수치 문장만 뽑아 짧은 후보쌍으로 만든 뒤 판정하는 편이 낫다. Table-Text Alignment(Ho 2025)는 LLM이 라벨은 맞히면서 근거 셀은 못 짚는다고 보고하므로 판정과 함께 근거 셀을 요구한다.

### 7층 정의 비교가능성

- **전용 방법은 없다.** 갈래 A와 C가 독립적으로 같은 결론을 냈다. 가장 가까운 선례는 다음이다.
- SoK의 D1(기준선 없는 절대값은 비교 불가), A2·F3(부분집합·하위 벤치마크 미공개로 비교 불가), F4(상대값만 제시).
- Qiu 2024는 「적중률을 올려도 처리량이 나빠질 수 있다」를 보여 지표 간 대리 가정을 기록해야 함을 뒷받침한다.
- REFORMS(Kapoor 2023)의 32항목 체크리스트는 정의 태그 필드명을 새로 만들지 않고 빌려 쓸 출처다.
- GRADE의 indirectness는 「정의가 다른 값을 같은 행에 놓는 것」의 의학 쪽 이름이다.
- SciClaim(Magnusson & Friedman 2021)은 주장 그래프에 qualification을 속성으로 넣었고, Evidence Inference(Lehman 2019)의 intervention·comparator·outcome 틀에서 comparator 동일성이 비교 가능성의 1차 필터다.

### 교차 논문 모순 스윕

- **충돌의 다수는 구체성 차이다.** SciFact-Open(Wadden 2022)에서 근거가 둘 이상인 81개 주장 중 16개(20%)에 충돌 증거가 있었고, 206개 주장-근거 쌍의 44%가 specificity mismatch(근거가 주장보다 더 구체적 53, 더 일반적 18, 인접 20)였다. 「정의 다름 / 조건 다름 / 진짜 충돌」 3분류의 실증 근거다. 비율은 도메인이 달라 옮기지 않는다.
- **세기 차이도 잡는다.** ClaimDiff(Ko 2023)는 참·거짓이 아니라 한 주장이 다른 주장을 강화·약화하는지를 2,941쌍에 라벨링했다. δ-NLI(Rudinger 2020)의 strengthener/weakener는 조건 diff를 「조건 U가 주장 H를 약화시키는가」로 형식화하는 언어다.
- **조건 설명은 사전 등록.** Cochrane Handbook 10장은 subgroup 비교가 관찰적이고 「연구마다 다른 특성이 많아」 다중성 문제가 있으며, 「결과를 보기 전에 진짜로 사전 명세된 분석에서만 신뢰할 결론이 나온다」고 한다. 연구 수가 매우 적은 탐색은 가치가 의심스럽다고도 적는다.

## 3. 설계 결정으로 옮기면

1. **두 추출기의 독립을 유지한다.** 한쪽이 뽑고 다른 쪽이 검토하는 구조로 바꾸지 않는다. (C46, Buscemi)
2. **예산은 3층에 먼저.** 누락이 오류의 다수다. 잔여 문단 재추출은 논문 전체가 아니라 문단 단위로 넣는다. (Shankar, Gartlehner 2024, Konet)
3. **재현율은 셋으로 잰다.** 문단 커버리지의 2-source 포획-재포획, 사람이 미리 고른 「반드시 잡혀야 할」 스팬 10개의 회수, 두 추출기가 모두 버린 문단의 elusion 표본. 표본 크기와 임계는 실행 전에 고정하고 재표집하지 않는다. (Kastner, Cormack & Grossman 경유, Lewis)
4. **합치도는 q로 보고한다.** 필드별 Krippendorff α를 부트스트랩해 α_min 미달 확률을 낸다. 점추정 κ 하나로 통과를 선언하지 않는다. (Hayes & Krippendorff)
5. **5층은 사후 대조 파이프라인이다.** (요약 문장, 인용 레코드의 quote+conditions) 쌍을 MiniCheck급 NLI로 전수 스윕 → 조건 검증 질문을 레코드만 보이는 새 컨텍스트에서 답하게 함 → 좌우 순서를 교대한 LLM 심판으로 우선순위 → 통계적으로 정한 크기의 사람 표본. 「정확히 써라」 프롬프트는 대책이 아니다. (Peters & Chin-Yee, Tang, Dhuliawala, Wang, Dorner)
6. **라벨은 셋 + 근거 + 구체성.** SUPPORTS/REFUTES/NEI에 근거 스팬을 반드시 붙이고, NEI 후보에는 더 구체적/더 일반적/인접 중 하나를 단다. 조건이 안 풀리면 문장을 쓰지 않고 「판정 불가」로 남긴다. (SciFact, SciFact-Open, FEVER, Claimify)
7. **조건 축은 스윕 전에 등록한다.** 분모·모집단·관측 창·이상/실측·시뮬/프로덕션·기준선. 사후에 찾은 설명은 「가설」로 표기한다. 41편 규모에서 정량 meta-regression은 하지 않는다. (Cochrane 10장)
8. **6층 검사기는 sciwrite-lint 항목 + SoK B3·B5로 만들고, 오류 주입으로 검사기 자체를 평가한다.** 표 판정에는 근거 셀을 요구한다. (Samsonau, van der Kouwe, Ho)
9. **7층 태그는 다섯 개를 최소로 강제한다.** 세는 단위, 분모 모집단, 창, 이상/실측, 기준선. 기준선이 없는 값은 비교 행에 넣지 않는다. Table 1 행에는 GRADE식 확실성 기호를 붙인다. (SoK D1, REFORMS, GRADE)
10. **정답 심기로 스케일업을 게이트한다.** 사람이 확인한 레코드를 코퍼스에 섞어 두고, 추출 프롬프트를 고칠 때마다 그 정확도를 넘겨야 전체에 투입한다. 정답에 대한 이의 제기 경로를 둔다. (Oleson)
11. **오류율은 크기를 정한 표본으로 낸다.** 어림수 「100건」이 아니라 정확 이항 구간으로 폭을 정한다. 계산상 300건에서 0건이면 95% 상한이 약 1%다. (Klie의 경고, 계산은 우리 것)

## 4. 이 프로젝트의 기존 도구와 맞춰 보면

| 층 | 기존 도구 | 문헌이 더 요구하는 것 |
|---|---|---|
| 1 | `$KVCPOOL/tools/quotes_verbatim_check.py`, waivers 33건 | §·쪽 메타데이터 독립 검증 |
| 2 | `claude_numbers_raw.tsv`, `codex_verify_metric_sources.py` | 3분류 귀속 태그, 원자 분해, C51식 크기·방향 대조 |
| 3 | `$KVCPOOL/tools/quotes_coverage.py`(옛 세트 대상) | 현재 두 벌에 재조준, 포획-재포획 추정, 목표 집합, elusion 표본 |
| 4 | 없음(9-15 리뷰는 수작업) | 구간 짝짓기 + 필드 diff, α의 q, 순서 교대 심판 |
| 5 | 없음(빌더는 ID 존재만 assert) | NLI 스윕 → 독립 검증 질문 → 심판 → 사람 표본 |
| 6 | `claude_50` §1-a 수작업 21건 | sciwrite-lint식 검사기 + 오류 주입 평가 |
| 7 | merge-log N6 수작업 5쌍 | 스키마 강제 태그 5개, 기준선 없으면 진입 금지 |

## 5. 못 찾은 것

- 7층(정의 비교가능성)을 정면으로 다룬 확립된 방법·벤치마크. 시스템 분야에서 「같은 지표 이름이 다른 정의를 숨긴다」를 주제로 한 출판 가이드라인도 찾지 못했다. 캐시 문헌의 OHR/BHR 구분은 관행으로 존재하나 원 논문(AdaptSize)은 열지 않았다.
- 컴퓨터 시스템 분야에 특화된 이질성·subgroup 방법론. 현재는 Cochrane 10장을 직접 차용하는 것이 최선이다.
- Cochrane의 「공변량당 10편」 규칙은 열어 본 페이지에 명시되어 있지 않다. 「연구 수가 매우 적으면 가치가 의심스럽다」까지만 확인했다.

## 6. 출처 (검증된 것만, 갈래 표시)

| 출처 | 갈래 | 확인 경로 |
|---|---|---|
| Rashkin et al., Measuring Attribution in NLG (AIS), arXiv 2112.12870 | A | 초록 |
| Bohnet et al., Attributed QA (AutoAIS), arXiv 2212.08037 | A | PDF 본문 |
| Honovich et al., TRUE, NAACL 2022, arXiv 2204.04991 | A | PDF 표 3 |
| Laban et al., SummaC, TACL, arXiv 2111.09525 | A | 초록 |
| Tang, Laban, Durrett, MiniCheck, EMNLP 2024, arXiv 2404.10774 | A | 초록 |
| Gao et al., ALCE, EMNLP 2023, arXiv 2305.14627 | A | PDF §7·§G.5 |
| Yue et al., AttrScore, arXiv 2305.06311 | A | 보고서 인용 수치 없음 |
| Li et al., AttributionBench, arXiv 2402.15089 | A | 초록 |
| Es et al., RAGAS, arXiv 2309.15217 | A | PDF 표 |
| Min et al., FActScore, EMNLP 2023, arXiv 2305.14251 | A | 초록 |
| Wei et al., SAFE, NeurIPS 2024, arXiv 2403.18802 | A | 초록 |
| Dhuliawala et al., Chain-of-Verification, arXiv 2309.11495 | A | PDF 표 1–3 |
| Wang et al., Self-Consistency, ICLR 2023, arXiv 2203.11171 | A | 초록 |
| Liu et al., G-Eval, arXiv 2303.16634 | A | 초록 |
| Wang et al., LLMs are not Fair Evaluators, arXiv 2305.17926 | A | 초록 |
| Zheng et al., MT-Bench, arXiv 2306.05685 | A | 초록 |
| Shi et al., Judging the Judges, arXiv 2406.07791 | A | 초록 |
| Dorner, Nastl, Hardt, Limits to scalable evaluation, ICLR 2025, arXiv 2410.13341 | A | 초록 |
| Peters & Chin-Yee, Generalization bias, R. Soc. Open Sci. 12(4):241776, 2025 | A·C | arXiv 초록 + Europe PMC 서지 |
| George & Stuhlmüller, Factored Verification, arXiv 2310.10627 | A | PDF |
| Wadden et al., SciFact, EMNLP 2020, arXiv 2004.14974 | A·C | 초록 |
| Thorne et al., FEVER, NAACL 2018, arXiv 1803.05355 | A | 초록 |
| Walters & Wilder, Scientific Reports 13, 2023, doi 10.1038/s41598-023-41032-5 | A | Europe PMC 초록 |
| Cochrane MECIR C43–C51 | B | 페이지 |
| Buscemi et al., J Clin Epidemiol 2006, PMID 16765272 | B | Europe PMC 초록 |
| Mathes et al., BMC Med Res Methodol 2017, PMID 29179685 | B | Europe PMC 초록 |
| Hayes & Krippendorff, Comm Methods & Measures 2007 | B | PDF |
| Gartlehner et al., Res Synth Methods 2024, doi 10.1002/jrsm.1710 | B | Europe PMC 초록 |
| Konet et al., Res Synth Methods 2024, doi 10.1002/jrsm.1732 | B | Europe PMC 초록 |
| Khraisha et al., Res Synth Methods 2024, doi 10.1002/jrsm.1715 | B | Europe PMC 초록 |
| Schmidt et al., arXiv 2405.14445 | B | 초록 |
| Reason et al., PharmacoEcon Open 2024 | B | Europe PMC 초록 |
| Lai et al., npj Digit Med 8:74, 2025 | B | Europe PMC 초록 |
| Gartlehner et al., Ann Intern Med 2025, doi 10.7326/ANNALS-25-00739 | B | Europe PMC 초록 |
| Shankar, Lim, Qian, J Biomed Inform 2026, doi 10.1016/j.jbi.2026.105086 | B | Europe PMC 초록 |
| Kastner et al., J Clin Epidemiol 2009, PMID 18722088 | B | Europe PMC 초록 |
| Rücker et al., J Clin Epidemiol 2011, PMID 21684116 | B | Europe PMC 초록 |
| Stevenson & Bin-Hezam, ACM TOIS 2024, arXiv 2311.08597 | B | PDF |
| Lewis, Yang, Frieder, CIKM 2021, arXiv 2108.12746 | B | PDF |
| Oleson et al., Programmatic Gold, AAAI HCOMP WS 2011 | B | PDF |
| Klie et al., arXiv 2307.08153 | B | 초록 |
| Cochrane Handbook ch.10, ch.14 | B·C | 페이지 |
| Wadden et al., SciFact-Open, Findings EMNLP 2022, arXiv 2210.13777 | C | PDF |
| Li, Raheja, Kumar, ContraDoc, NAACL 2024, arXiv 2311.09182 | C | PDF |
| Ko et al., ClaimDiff, Findings ACL 2023, arXiv 2205.12221 | C | 초록 |
| Lehman et al., Evidence Inference, NAACL 2019 | C | ACL Anthology 초록 |
| Magnusson & Friedman, SciClaim, EMNLP 2021, arXiv 2109.10453 | C | 초록 |
| Microsoft Research, Claimify 블로그, 2025-03-19 | C | 페이지 |
| Rudinger et al., Defeasible NLI, Findings EMNLP 2020 | C | ACL Anthology 초록 |
| van der Kouwe et al., SoK: Benchmarking Flaws, EuroS&P 2019 | C | PDF |
| Qiu, Yang, Harchol-Balter, arXiv 2404.16219 | C | 초록 |
| Kapoor et al., REFORMS, arXiv 2308.07832 | C | 초록 |
| Nuijten et al., Behav Res Methods 2016, PMC5101263 | C | PMC |
| Samsonau, sciwrite-lint, arXiv 2604.08501 | C | 초록 |
| Shin, Xie, Albanie, arXiVeri, arXiv 2306.07968 | C | 초록 |
| Ho et al., Table-Text Alignment, arXiv 2506.10486 | C | 초록 |
| Venktesh et al., QuanTemp, SIGIR 2024, arXiv 2403.17169 | C | 초록 |

## 7. 대조한 것 / 고친 것 / 뺀 것 / 2차 인용

**대조한 것.** 세 보고서의 수치 주장 57건을 원문(초록·PDF 본문·Europe PMC 초록·공식 페이지)과 대조했다. 원문과 다른 것은 없었다.

**고친 것.** TRUE의 평균 ROC AUC는 11개 데이터셋이 아니라 VitaminC·FEVER를 뺀 9개의 평균이다. SummaC의 TACL 게재는 2022년(arXiv 2021). Peters & Chin-Yee의 게재지 정보는 출판사 페이지가 403이라 Europe PMC 서지로 확인했다.

**뺀 것 (인용 금지).**
- BioDivergence(arXiv 2606.11208). 2026-08-30 철회.
- Alamri & Stevenson 2016 심혈관 모순 코퍼스의 수치. 원문 미열람.
- Hilkenmeier 2025(Elicit 81.4% 대 86.7%). 원문 미열람.
- Krippendorff α의 .800/.667 절단값. 열어 본 두 PDF에 그 문장이 없다.
- Rule of three의 원전 문장(Hanley & Lippman-Hand 1983). 스캔본이라 미확인.
- Claimify의 coverage 87.6%·precision 96.7%. 2차 매체에만 있다.
- QuanTemp의 claims 수, REFORMS의 「8개 모듈」, SciClaim의 「Qualifier·Epistemic」 노드 이름, Cochrane의 「공변량당 10편」. 초록·페이지에 없다.
- AIS의 「According to the source」 문구. 본문 표현이라 초록에서는 미확인.
- Mogul 1999 「Brittle metrics」. 유료 벽.

**2차 인용.** Cormack & Grossman 2016의 target set 10·기울기비 6은 Stevenson & Bin-Hezam 2024가 원전을 인용한 문장에서 확인했다. Landis & Koch 1977의 κ 구간표는 원문 미열람이다. RAGAS의 WikiEval 일치도 0.95/0.78/0.70은 저자 자체 제작 소규모 셋의 값이다.
