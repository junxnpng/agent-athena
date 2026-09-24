# Ralplan iteration 1 — Critic evaluation (athena:critic, opus, 2026-09-22)

대상: `.athena/plans/ralplan-verification-system.md`(Planner 초안), `ralplan-verification-system.review-1-architect.md`, 계약 `.athena/specs/deep-interview-verification-system.md`.

**Steelman.** 계획의 뼈대는 계약에 충실하다. 결정론적 층을 코드에 두고, LLM은 파일 왕복 심판으로만 쓰고, 임계를 실행 전에 해시로 박고, 인수 시험 네 갈래를 pytest 안으로 끌어들인 것. 이 네 결정은 스펙 R4·R5와 설계 P6·P7이 실제로 요구하는 것이고 각각 대안보다 낫다. 문제는 골격이 아니라 v1 데이터 위에서 이 골격이 무엇을 측정하는지다.

## 1. Principle ↔ Option 일관성 (아키텍트 4건 검증)

- **P4(임계 선등록) ↔ 단계 순서 — 확증, 차단.** 아키텍트는 P2부터라 했으나 더 이르다. plan:75(P1)가 이미 "문단 단위 선택은 `thresholds.yaml`에 등록"이라 쓰고, plan:108(P4)은 `elusion_n`·`sample_seed`가 등록돼 있다고 전제하는데 파일은 plan:142(P7)에서 생긴다. P1이 P7에 역의존한다.
- **P5(사람 손 최소) ↔ P6 — 확증.** `known_errors.tsv` 약 90 케이스 수작업 + `gaming_records.jsonl` 창작 + B-4 감사 대기열 + DE-2/DE-3의 에이전트 왕복 2~3벌은 며칠짜리다. spec:48과도 충돌한다.
- **P1(LLM은 기록자가 아니다) ↔ 파일 왕복 — 확증, 단 경미.** 아키텍트 권고(스팬 오프셋 검증 + 행 수 일치)에 하나 더: export가 manifest sha256을 내고 import가 그 해시로 항목 집합의 폐쇄성을 강제해야 한다.
- **P3(층을 섞지 않는다) ↔ V1-5의 `{PASS, MISS, WAIVED}` — 부분 반박.** Principle 3의 문언은 "L1 출력에 모델 판단이 들어가면"이다. waiver는 사람 판단이므로 문언 위반은 아니다. 그러나 실질 문제는 남는다: plan:142의 "L1 pass 100%"가 WAIVED를 pass로 세는지 미정의라 임계가 두 값을 갖는다. 차단 사유를 "원칙 위반"에서 "임계 정의 공백"으로 바꿔 유지한다.

## 2. 대안 기각의 공정성

- **JSONL — 공정.** 일곱 층 조인 논거는 성립하고, "원장은 git 밖 재생성물"로 JSONL의 장점을 흡수한 것도 정직하다.
- **local NLI — 결론은 타당, 전제는 사실 오류.** `torch` 2.5 GB 논거는 유효하다. 그러나 Driver 3의 "`.venv`는 sqlite3·PyYAML·pytest만 있음"은 거짓이다. 실측: `duckdb-1.5.5`, `pyarrow-25.0.1`, `jinja2`, `markdown`, `tabulate`, `pygments`가 이미 설치돼 있다.
- **duckdb — 기각 자체가 없다(미검토).** 차단으로 올리지는 않는다. duckdb에는 trigger가 없어 B-4(`gold` 직접 UPDATE 거부)를 지탱하지 못한다. 선택은 옳고 근거가 틀렸다. ADR (a)의 무효화 근거를 "무결성 제약과 trigger가 필요하고 duckdb는 그것을 주지 않는다"로 다시 쓰면 된다.
- **small API — 공정.** 키 부재·비결정성은 실재한다.

## 3. 차단 위험별 완화 여부와 한 줄 수정

계획이 아래 일곱 건을 완화하는 장치를 하나도 갖고 있지 않다.

1. **행 단위 30 vs 44 — 확증, Critical.** Claude 30건·Codex 37건을 직접 셌고, Claude 레코드 중 `"quotes":[]`인 행이 실제로 있다. 인용당 1행이면 C0-2의 `N+M=30`은 성립 불가다. spec:70도 30/37 단위를 쓰므로 계획 내부 모순이자 계약 모순이다. → 한 줄: "행 단위는 인용 1건 = 1행이며, 변환 요약은 원 레코드 30·37 전부가 '행 산출 또는 사유 붙은 격리'로 닫혔음을 따로 보고한다. 인용 0건 레코드는 `no_quote` 격리."
2. **Query/주제 부재 — 확증, Critical.** 계획 전문에 `query`/`topic` 0회, DDL에 `queries` 없음. spec:32의 Goal 문장과 Ontology `AlignmentCheck`(spec:217, "EvidenceRecord × Query")가 사라져 판정 2가 조용히 충실성 검사로 축소된다. 이건 범위 축소가 아니라 다른 제품이다. → 한 줄: P1에 `queries` 테이블과 `--query`를 넣고 judge export에 query를 실어 보낸다(기본값은 paper topic).
3. **L2 격리율을 대표 수치로 삼음 — 확증, High.** 두 벌 어디에도 5필드 키가 없고 Codex `conditions`는 자유 산문임을 확인했다. 사전에 값을 아는 수치를 "스키마 계약이 구속력을 갖는다는 증거"(plan:211)라 부르는 것은 논리 비약이다. → 한 줄: "입력 진단치이며 사전 기대값 100%"로 강등하고 대표 수치 자리를 L1 변형별 일치 등급 분포로 옮긴다.
4. **게이트 구조적 실패 — 확증, Critical, 아키텍트보다 강하게.** 검출 정의 문제 이전에 연산자 자체가 적용 불가다: 없는 필드는 `condition_delete`로 지울 수도 `condition_widen`으로 넓힐 수도 없다. → 한 줄: 검출 = "기준선 실행 대비 verdict 또는 사유 코드 변화"로 정의하고, 대상 필드가 부재해 변이를 만들 수 없는 조합은 `not-applicable`로 보고하며 UNVERIFIED 판정에서 제외한다.
5. **κ 게이트 n=33 — 방향 확증, 근거는 교체.** 검정력(0.52)은 둘째 문제다. 더 큰 문제는 G에 라벨이 없다는 것이다. `docs/patterns/gold/workload__year-in-llm-serving_handpicked.md`는 사용자가 좋다고 고른 문장 나열이고 supports/refutes/insufficient 라벨이 한 개도 없다. "G 파생 라벨"(plan:132)은 존재하지 않는 것을 지어내는 단계이며 Principle 2를 어긴다. → 한 줄: v1의 B-2는 κ·부트스트랩 CI를 보고만 하고 pass/fail을 걸지 않으며, 라벨을 어떤 규칙으로 파생하는지(또는 33문장에 사람이 3분류를 붙이는 비용)를 명시한다.
6. **B-3 / V1-4 범위 — 확증.** waiver TSV 48행에 정답 논문 슬러그가 0건임을 확인했고, `papers/claude_column_text/`에는 `splitwise`·`dualmap` 두 편뿐이라 V1-1의 `claude_column` 변형도 정답 논문에서 공집합이다. 단, spec:116은 이 회귀 케이스를 [v1]로 못 박았으므로 그냥 버리면 계약 위반이다. → 한 줄: 회귀 케이스에 필요한 논문의 Claude 레코드만 변환하는 것을 v1 예외로 올리고, `waiver_rate`는 "정답 논문 0/N, 전체 48/804"로 두 값을 병기한다.
7. **thresholds.yaml P7 생성 — 확증(§1 P4).** → 한 줄: 임계 등록을 P1 말미로 올리고 이후 단계는 읽기만 한다.

## 4. Acceptance Criteria 분류 (38개)

- **RUNNABLE 26**: C0-1, C0-3, V1-1, V1-2, V1-4, V1-5, V2-1, V2-2, V2-3, V2-4, V3-1, V3-3, V3-4, V4-1, V4-3, A-2, A-3, B-2, C-1, C-3, DE-1, DE-4, DE-5, OP-1, 스킬, 테스트·커버리지.
- **SCENARIO 5**(에이전트 왕복이 선행해 CI에 못 들어감): B-4, C-2, DE-2, DE-3, 보고서.
- **NOT TESTABLE AS WRITTEN 7**: C0-2(30 vs 44), V1-3("빈 값 0건"이 MISS 오프셋에 무엇을 요구하는지 미정의 + G 문장 분할 규칙 부재), V3-2(T의 출처·선정 절차 없음), V4-2(`derived_from` 0행), A-1(표 행 8 vs 연산자 9), B-1(단일 6.7 KB 줄의 문장 분할 규칙과 대조 기준 수치 미등록), B-3(k=1 밖 자산).
- **공허(v1 데이터에서 항상 참) 6**: V2-2의 `expensive_ratio ≤ 0.05`(lexical 단독이면 상수 0), V2-3(DDL이 NOT NULL이면 항상 0), V4-1의 "quarantine→`comparable=0`"(구성상 참, 전 행 quarantine), V4-2(공집합 위 참), V1-4의 `waiver_rate`(정답 논문 0/N), V3-2의 `recall >= 0.7 (95% conf.)` 주석(고정 문자열).
- **항상 거짓 1**: `보고서` 불릿 + `gate`: §3-4를 고치기 전에는 UNVERIFIED로 종료 코드 1이 고정이다.

## 5. 단계별 검증 절차

- **테스트 우선은 지켜진다.** P1–P7 모두 "먼저 쓰는 테스트" 파일 목록이 있고 RED→GREEN이 공통 규칙에 박혀 있다. 진짜 강점이다.
- **완료 판정이 없다 — 차단(추가).** 어느 단계도 "이 단계가 닫는 AC 불릿은 무엇이고, 어떤 명령이 어떤 값을 내면 끝인가"를 적지 않는다. 계획 파일에 단계 상태 표시도 없다. 사용자 규칙(plan-workflow)은 단계 상태를 계획 파일에서 추적하고 새 세션이 대화 이력 없이 재개할 수 있어야 한다고 요구한다. → 한 줄: 각 P에 "닫는 AC: …"와 `- [ ] 완료` 표기를 붙인다.

## 6. 아키텍트가 놓친 것

- **탐침 P가 정의상 공허하다 — Critical(추가).** plan:107의 "G의 등록된 부분집합을 원장에서 숨김 처리"는 추출기가 아니라 recall 코드를 시험한다. 두 레코드 벌은 이미 동결되어 있으므로 지금 심는 탐침은 회수율에 아무 정보를 주지 않고, probe_recall ≡ P로 제한한 gold_recall이다. 같은 이유로 T도 무효다: Cormack–Grossman target method는 목표를 측정 대상 실행 이전에 독립 표집할 것을 요구하는데, 오늘 고르는 T는 어떤 방식이든 사후다. → 한 줄: v1의 P·T는 `not-applicable: extractor runs are frozen`으로 보고하고, 신뢰 진술은 elusion 상한만 낸다.
- **MISS 즉시 기각 규칙 부재 — Medium.** spec:80이 [v1]로 요구한다. 파이프라인(plan:146)에 MISS 행을 L2/judge에서 배제하는 문장 한 줄이 필요하다.
- **Driver 3의 사실 오류(§2).** 근거 문장이 검증 가능하게 틀린 계획은 자기 기준에 못 미친다.
- **아키텍트를 강등한 것**: Principle 3 위반 주장(§1 넷째)과 duckdb(§2). 둘 다 실재하는 지적이나 재구조화가 아니라 문언 수정으로 닫힌다.

## 무엇이 진짜 좋은가

tier0이 `supports`를 낼 수 없게 만든 것, 변환기가 「없음」을 대신 써 주지 않는 것, 임계 sha256을 출처 묶음에 박는 것, 등가 변이 오탐률을 검출률과 같은 표에 두는 것. 네 가지는 이 계획이 문헌을 읽고 얻은 값이고 대안 설계에서 흔히 빠지는 자리다. 방향은 옳다.

## 판정 근거

아키텍트의 antithesis는 "순서를 바꾸라"는 말이지 "다른 시스템을 지어라"가 아니다. 골격(결정론적 층 + 원장 + 단계식 심판 + 선등록 임계)은 계약이 요구하는 그대로다. 차단 항목 9건(아키텍트 7 전부 유지, 단 #6의 근거를 라벨 부재로 교체 + 탐침/T 무효 + 단계 완료 판정 부재 추가)은 전부 계획 문서 한 번의 편집으로 닫힌다. 다만 §3-1, §3-2, §3-4, §6-1은 수치와 AC 문언을 동시에 고쳐야 하므로 부분 수정은 오히려 모순을 늘린다.

VERDICT: ITERATE
