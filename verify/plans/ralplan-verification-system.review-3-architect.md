# Ralplan iteration 3 — Architect verification (athena:architect, opus, 2026-09-22)

plan(262줄)과 critic-2를 읽고, elusion 풀 수치는 직접 다시 세어 대조했다.

## Closing edits status

- **(a) elusion 프레임 + n — RESOLVED.** 표집 프레임이 P1으로 올라가 정의까지 박혔다: 「미사용 문단 = 문단 블록 전체 − `claims` 행의 인용이 해결된 블록, 격리 레코드(`multi_fragment_no_quote`)의 fragment는 사용으로 세지 않음」(plan:80). `elusion_n`은 P1 말미에 실제로 세어 그 값 이하로 등록하고(plan:80·224), P5는 같은 프레임을 그대로 쓴다(plan:125). 달성 가능한 상한만 보고하고(n=7→34.8%, n=20→13.9%, n=38→약 7.6%), V3-3(plan:179)은 ①풀 크기 출력 ②`elusion_n ≤ 풀 크기` ③상한을 달성 가능한 값 그대로 ④재표집 시 종료 코드 1을 요구한다. 5% 불가는 Deferred(plan:237)에 사유와 함께 적혔다. 결정 게이트 권한도 한 문장으로 한정됐다(plan:106). 정합성: 이 정의는 plan:68(격리 fragment는 `paragraphs`에 locator 근거로만 등록)과 모순되지 않는다. 다만 spec:94의 문언("두 벌 어느 쪽도 쓰지 않은")보다 좁은 정의이며(문언대로면 풀은 7), 그 축소를 한 절로 밝혀 두면 감사자가 읽기 쉽다.
- **(b) κ 짝짓기 — RESOLVED.** 사람 라벨의 대상이 P3가 tier1에 태운 `record × query` 행과 동일한 행 집합(20행, 가능하면 L1 PASS 51행 전부)으로 바뀌었고, κ는 그 행 단위로 심판 판정과 짝짓는다(plan:136). G는 재현율 기준으로만 쓰고 κ 짝짓기에서 빠진다는 문장도 명시됐다. `config/gold_labels.tsv`는 `thresholds.yaml`과 같이 등록 시 sha256을 출처 묶음에 박는다(plan:136). B-2(plan:188)는 보고 전용·종료 코드 0을 유지하고 `unpaired labels` 실패 조건을 추가했다.
- **(c) G 분할 규칙 + 등록 수치 — RESOLVED.** plan:124가 `**`/`****` 강조 표지 분리를 규칙 첫 항목으로 올리고, `->` 메모의 종료 지점(다음 원문 문장 시작까지)도 규칙에 들어갔다. 등록 수치는 하드코딩 금지·규칙 산출값을 `gold_split_count`로 기록으로 바뀌었고(plan:124·187), `user_note` 6건만 실측 확정으로 남겼다. B-1(plan:187)은 첫 문장 생존까지 시험한다.

## Optionals check

적용 완료: `81행`→51행(plan:41·214), QUERY-1을 P1 닫는 AC에 배정(plan:82), B-1을 P5로 이동(plan:126), `l1_tautological` 별도 열 집계를 V1-1에 명문화(plan:167), default query에서 한줄평 제외 + 사유(plan:77), Codex 7행 비대칭 시 `skipped: asymmetric sets`(V3-4 plan:180), B-3 예외 논문의 논문별 분리 집계(plan:151), `UNTESTED(not-applicable)` 등급을 UNVERIFIED와 구분(plan:150·186), Principle 5에 spec:48 계약 제약 복원(plan:17). 아홉 항목 모두 반영, 누락 없음.

## Contractual format

- 리터럴 `## Acceptance Criteria` 있음. 불릿 40개, 단계별 닫는 AC 합계 5+5+5+3+5+14+3 = 40으로 전부 배정.
- v1 데이터에서 시험 불가능하거나 항상 참인 불릿은 남아 있지 않다. V3-3은 "풀 크기 출력 + `n ≤ 풀` + 달성 가능 상한"으로, B-2는 행 단위 짝짓기로, B-1은 규칙 산출값으로 바뀌었다.
- 표기 문제 하나: plan:80과 V3-3(plan:179)의 "실측 38". 같은 프레임을 매칭 규칙만 달리해 다시 세면 커버 35 / 미사용 35가 나온다(블록 경계와 부분 문자열 매칭 폭에 민감). AC가 요구하는 것은 "풀 크기를 출력하고 `elusion_n ≤ 풀 크기`"이므로 게이트로 작동하지는 않지만, 38을 참고값(구현 규칙에 따라 35–38)으로 표기해 두면 구현자가 리터럴로 오해하지 않는다.

## Verdict (architect side)

**APPROVE-ready.** 세 차단 편집이 모두 실제로 들어갔고 새 모순을 만들지 않았다. 남은 것은 blocking이 아닌 표기 다듬기 둘이며 다음 편집 때 함께 처리하면 충분하다.

1. [optional] plan:80·179의 "실측 38"을 "참고값 35–38(구현의 블록·매칭 규칙에 따라 흔들림, 등록값은 P1 실측으로 받는다)"로.
2. [optional] plan:80의 미사용 정의에 "이 정의는 spec:94의 문언보다 좁다. 격리 레코드는 비교에 들어가지 않으므로 「인도된 레코드 집합의 누락」을 재는 쪽으로 한정했다" 한 절 추가.

## References

- plan:17,41,68,77,80,82,106,124,126,136,150,151,165,167,179,180,186,187,214,224,237
- review-2-critic.md:47-49,53
- `papers/codex_source_text/codex_workload__year-in-llm-serving.txt` — 70블록 중 51행 인용이 덮는 블록 35(플래너 계수 32), 미사용 풀 35–38
