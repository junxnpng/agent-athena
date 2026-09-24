# Ralplan iteration 2 — Architect re-review (athena:architect, opus, 2026-09-22)

대상: `.athena/plans/ralplan-verification-system.md`(Planner 2판, 261줄). 경로는 `/work/jun/priv-mb-eval/kvcpool-trace-gen` 기준. plan을 직접 읽고 데이터로 재검증했다.

## Blocking items status

1. **행 단위(arch #1) — PARTIAL.** 규칙은 명확하다: plan:64–69에 `1 인용 = 1 행`, Codex는 `fragments == 1`인 레코드만 `fragments[0].text`를 quote로 쓰고 나머지는 `multi_fragment_no_quote` 격리(실측: 정답 논문 fragment 수 최소 1·최대 72, 단일 fragment 레코드 7건, plan:5·68·163과 일치). `checks.l1_tautological=1`과 "대표 수치 집계에서 분리"도 plan:68에 있다. 다만 `l1_tautological`을 확인하는 AC가 없고(V1-1 plan:167의 변형별 표에 분리 열이 없다), plan:41·214는 옛 단위 "81행"(=44+37)을 그대로 쓴다. 새 규칙에서는 51행(44+7)이다.
2. **얇은 수직 슬라이스(arch #2) — RESOLVED.** Principle 5(plan:17), P3(plan:97–107), 결정 게이트(plan:106), ADR의 7단계 선구축 기각(plan:216).
3. **Query 1급 입력(arch #3) — RESOLVED.** `queries` 테이블(plan:76, 11 테이블), `--query`를 judge·report·recall이 받음(plan:77·81), export가 `query.topic`/`query.claim_text`를 실어 보냄(plan:102 + QUERY-1 plan:165), alignment(record×query)와 faithfulness(quote↔claim_text)를 별도 열로 병기(plan:77 + V2-1 plan:172).
4. **L2 격리율 강등(arch #4a) — RESOLVED.** plan:114가 "입력 진단치, 사전 기대값 100%"로 명시하고 대표 수치를 L1 등급 분포로 옮겼다(plan:114·199·220·226). V4-1(plan:181)이 라벨을 강제한다.
5. **변이 검출 정의 + not-applicable(arch #4b / critic #4) — RESOLVED.** 검출 = 기준선 대비 `verdict` 또는 `reason_code` 변화(plan:133), 필드 부재 조합은 `not-applicable`이며 UNVERIFIED에서 제외(plan:134·150·186).
6. **κ 보고 전용 + 사람 라벨(arch #6, critic 근거 교체) — PARTIAL.** report-only와 pass/fail 게이트 제거는 완료(plan:136·188·217·239), 33문장 3분류를 사람이 붙이는 새 비용도 명시했다(plan:136). 그러나 κ의 짝짓기 단위가 없다. 사람은 G 문장 33개에 라벨을 붙이는데 검증기가 판정하는 것은 레코드 행(44+7)이다. 같은 항목에 대한 두 라벨이 없으면 κ는 계산 자체가 불가능한데, G 문장을 judge 대상 행으로 태우는 단계가 P3·P5·P6 어디에도 없다(judge export는 plan:102에서 L1 PASS 행 `--limit 20`만 대상).
7. **회귀 케이스 예외(arch #7) — RESOLVED.** 해당 슬러그의 Claude 레코드만 v1 예외 변환(plan:137·189·234), `waiver_rate`는 `gold: 0/44` + `overall: 48/804` 두 값(plan:93·170).
8. **탐침 P·목표 집합 T 공허(critic 추가 1) — NOT RESOLVED(형태만 바뀜).** P·T를 `not-applicable: extractor runs are frozen`으로 내리고 사유까지 적은 것은 옳다(plan:125·178). 문제는 대체된 유일한 정량 보증인 elusion이 실측상 불가능하다는 것이다. 등록 단위(raw 빈 줄 블록 ≥20단어)는 70개이고, Claude 인용 44개가 31블록을, Codex fragment 700개까지 더하면 63블록을 덮는다 → 미사용 풀은 7블록(Claude 인용만 "사용"으로 쳐도 39). plan:125·179·224가 등록하려는 `elusion_n ≈ 59`는 두 정의 모두에서 표집 불가다. n=7이면 0오류 상한은 34.8%다.
9. **단계 완료 기준(critic 추가 2) — RESOLVED(경미한 누락).** 모든 P에 "닫는 AC"와 `- [ ] 완료`가 있다(plan:82·95·107·118·126·144·154). 다만 배정된 AC는 39개인데 목록은 40개다. QUERY-1(plan:165)이 어느 단계에도 배정되지 않았다. 또 B-1은 P5의 산출물(`convert gold`, plan:124)을 시험하는데 P6가 닫는다.

추가 지시 항목: thresholds P1 등록 — RESOLVED(plan:80 + OP-1 plan:166, Principle 4 문언 plan:16 수정). MISS 즉시 기각 — RESOLVED(공용 뷰 `v_l1_passed`, plan:92 + V1-5 plan:171). Driver 3 정정 + duckdb 대안 — RESOLVED(plan:23, A3 표 plan:33, ADR plan:213이 trigger 부재 단 하나를 기각 사유로 명시).

## New tensions or regressions

1. **결정 게이트(plan:106) vs 선등록 임계(Principle 4, plan:16).** 게이트가 "P4~P6의 범위, 특히 변이 연산자·인수 시험 규모를 확정한다"고 하지만, 그 규모를 정하는 값(`mutation_detect_min`, `mutation_fp_max`, `elusion_n`, `leakage_n`)은 plan:80에서 이미 등록되고 "이후 단계는 읽기만"으로 닫혔다. 권고 문언: "등록 임계는 불변이고, 게이트는 `not-applicable` 판정과 실행 범위만 확정한다."
2. **B-1의 "본문 문장 33행"(plan:124·187)이 계획 자신의 분할 규칙과 어긋난다.** 계획이 고정한 규칙(`->` 앞뒤 절단 → `.`+대문자 분할 → 약어·지수 금지 목록)을 그대로 돌리면 본문 문장은 37개가 나온다. 33은 iteration 1의 임시 계수다. 첫 문장 `User behavior induces temporal locality…`는 한줄평과 `****`로 붙어 있어 `**` 처리를 규칙에 넣지 않으면 통째로 유실된다. `user_note` 6건(한줄평 1 + `->` 5)은 실측과 일치한다.
3. **Codex 7행 축소의 파급이 뒤쪽 AC에 반영되지 않았다.** V3-1(plan:177)의 `codex` 재현율 열은 7행 기준이 되어 `union ≈ claude`가 되고, C-3(plan:193)의 raw/layout 차등 대상도 7행뿐이라 "어려운 사례" 수집이 거의 비며, 포획-재포획(V3-4)의 "독립된 두 벌"도 44 대 7의 비대칭이 된다. 보고서가 이 축소를 명시하지 않으면 수치가 오독된다.
4. **B-3 예외가 대표 수치를 오염시킬 수 있다.** 다른 슬러그의 Claude 레코드를 같은 원장에 넣으면(plan:137) 대표 수치인 L1 등급 분포와 `overall` waiver_rate 분모가 논문 혼합이 된다. 보고서의 논문별 분리 집계가 필요하다.
5. 경미: default query(plan:77)가 G 한줄평을 포함한다. 한줄평은 "디테일한 분석은 없음" 같은 논문 평가문이라 근거 합치의 기준 명제로 부적절하다. topic/claim 문장만 쓰도록 한정 권고.

## Contractual format

- 리터럴 `## Acceptance Criteria` 있음(plan:158). 불릿 40개(실측), `[R]` 33 / `[S]` 7 표기(plan:203)와 일치하며 `[S]`가 CI 밖임을 명시해 TEST-1(plan:201)과의 충돌이 해소됐다. `## ADR`의 여섯 항목 모두 유지(plan:207·209·211·220·222·229).
- 여전히 문제 있는 불릿: **V3-3(plan:179)** — 유일하게 "거짓으로 고정된" AC. `elusion_n=59`는 미사용 풀 7(또는 39)에서 표집 불가. **QUERY-1(plan:165)** — 단계 배정 없음. **B-1(plan:187)** — 등록 수치 33이 분할 규칙 산출값(37)과 불일치. V2-3(plan:174) — 공허하나 스스로 드러냈으므로 수용 가능. V4-2·V4-1·V2-2·V1-4 — "공허한 임계 통과"에서 "명시적 관측 보고"로 바뀌어 시험 가능하고 정직하다. A-3(plan:186) — `not-applicable`만 남은 층은 사실상 무판정이라 보고서에 `UNTESTED(not-applicable)` 등급을 따로 두도록 권고(선택).

## Recommendation

아키텍트 관점에서 APPROVE-ready 아님. blocking 2건, optional 4건. 9개 차단 항목 중 6건은 실제로 닫혔고, 남은 것은 모두 문서 편집 한 번으로 닫힌다.

1. **[blocking]** `elusion_n`을 실측 풀에 맞춰 다시 쓴다(plan:125·179·224). "사용된 문단"의 정의를 둘 중 하나로 고정하고(두 벌 기준 미사용 7 / Claude 인용만 기준 39), 달성 가능한 n과 그때의 상한을 적는다(n=7→34.8%, n=20→13.9%). 5% 상한은 k=1에서 불가능임을 Deferred(plan:236)에 명시한다.
2. **[blocking]** B-2의 κ 짝짓기 단위를 한 문장으로 정한다(plan:136): "G 33(또는 재계수된) 문장을 `gold` 행으로 judge export에 함께 실어 같은 query로 3분류를 받고, 사람 라벨과 행 단위로 짝지어 κ를 낸다." 없으면 B-2는 계산 불가이고, 새로 쓰기로 한 사람 30분이 버려진다.
3. **[optional]** B-1의 33을 계획 규칙으로 재계수한 값(37)으로 바꾸거나, 분할 규칙에 `**`·`10^N`·`Figure Na` 처리를 추가한 뒤 나온 값을 등록한다. "숫자는 규칙을 돌려서 얻는다"를 명시.
4. **[optional]** plan:41·214의 "81행"을 51행(44+7)으로 정정.
5. **[optional]** QUERY-1을 P1의 닫는 AC에 넣고, B-1을 P6에서 P5로 옮긴다. `l1_tautological` 분리 보고를 V1-1 또는 REPORT-1 문언에 넣는다.
6. **[optional]** P3 결정 게이트의 권한 범위를 한 문장으로 한정하고(등록 임계 불변), default query에서 한줄평 평가문을 제외한다.

## References

- plan:5,41,64-69,76-81,92,102,106,114,124-125,133-137,150,163-203,213-226
- review-1-critic.md:25-31,44,48
- `papers/codex_source_text/codex_workload__year-in-llm-serving.txt` — 문단 단위 70블록, 미사용 7(두 벌)·39(Claude만)
- `docs/patterns/gold/workload__year-in-llm-serving_handpicked.md:9` — 계획 규칙 적용 시 본문 37문장·`user_note` 6건, 첫 문장이 `****`로 한줄평에 접합
