# Ralplan iteration 1 — Architect review (athena:architect, opus, 2026-09-22)

대상: `.athena/plans/ralplan-verification-system.md` (Planner 초안, 245줄). 계약: `.athena/specs/deep-interview-verification-system.md`. 모든 경로는 `/work/jun/priv-mb-eval/kvcpool-trace-gen` 기준.

## Steelman antithesis

**이 계획의 v1 대표 수치는 코드를 한 줄도 쓰기 전에 이미 정해져 있고, 실제로 움직일 수 있는 유일한 수치는 이미 구현되어 있다. 그러므로 이것은 "측정 장치를 7단계로 짓는 계획"이 아니라 "입력 데이터의 알려진 형태를 7단계에 걸쳐 재확인하는 계획"이다.** 실측 근거:

- **L2 격리율은 상수다.** `claude_pattern_data.json`의 정답 논문 30행은 `caveats` 키가 있으나 전부 비어 있고(전체 804행 중에도 155행만 비어 있지 않음), 5조건 필드(unit·denominator·window·ideal_or_measured·baseline)는 두 벌 어디에도 키 자체가 없다. `codex`의 `conditions`는 37행 모두 46–281자의 한국어 자유 산문이라 결정론적 5필드 분해가 불가능하다. 즉 ADR이 v1의 대표 수치로 못 박은 L2 격리율(plan:211)은 오늘 jq로 계산되는 100%다. 사전에 값을 아는 지표는 스키마 계약의 구속력에 대한 증거가 아니라 입력 형식에 대한 기술이다.
- **L6은 대상 행이 0이다.** `numbers`는 Claude가 자유 문자열 list(정답 논문 28항목, 그중 산술 기호 포함 18), Codex는 단일 문자열이다. `derived_from` 포인터는 두 벌 어디에도 없다. 스펙 V4(spec:101)의 [v1] 조건은 v1 데이터에서 공집합 위에서 참이 된다.
- **Codex 쪽 L1은 동어반복에 가깝다.** Codex 레코드에는 `quote` 필드가 아예 없다. 존재하는 것은 `fragments[{page,bbox,text,sha256}]`이고 1,164행 전부 `quote_status = FULL_FRAGMENT_MATCH_TO_PDF_TEXT`다. 정답 논문 37행이 참조하는 블록 id는 720개(레코드당 최대 40 fragment, 첫 fragment는 Abstract 전체)다. 계획은 이 fragment 더미에서 `quote` 한 개를 어떻게 만드는지 어디에도 적지 않았고(P1 plan:73은 locator만 말한다), 무엇을 고르든 PDF 블록 원문이므로 L1은 이미 통과가 보장된 대상을 다시 검사한다.
- **따라서 v1에서 진짜 정보가 나오는 층은 Claude 인용 44행에 대한 L1 하나뿐이고, 그것은 `tools/quotes_verbatim_check.py`(90줄)가 이미 하고 있다.**
- **게이트는 구조적으로 통과할 수 없다.** plan:144의 UNVERIFIED 규칙 + plan:129의 변이 표를 L2에 적용하면, 기준선 판정이 상수(quarantine)이므로 검출률 정의가 "격리되었나"면 `synonym_swap` 오탐률도 100%(임계 0.1 초과 → UNVERIFIED), "기준선 대비 판정이 바뀌었나"면 `condition_delete` 검출률이 0%(임계 0.9 미달 → UNVERIFIED)다. 어느 정의든 L2는 UNVERIFIED고 `gate`는 종료 코드 1이다. 여기에 B-2의 κ 게이트가 더해진다.
- **tier0을 stdlib 어휘 스크리너로 둔 것은 가장 덜 중요한 선택이다.** 계획 자신이 "G 67 레코드 규모에서는 tier1이 100%를 덮어도 예산 안"(plan:42)이라고 적었다. 즉 v1에는 캐스케이드가 없다. tier0은 승격률이 항상 100%인, 측정 불가능한 라우터다. NLI냐 API냐는 1,900행 시점의 문제이고, ADR의 (b) 표는 v1에 영향이 없는 선택을 가장 길게 정당화한다. SQLite 역시 반대할 이유가 없다(다만 `.venv`에 duckdb 1.5.5·pyarrow가 이미 설치되어 있다. ADR의 "SQLite vs JSONL" 이분법은 실제 환경에서 성립하지 않는다).
- **대안적 v1:** P1 → P2 → tier1 1회 왕복 → 보고서 뼈대까지 수직으로 한 번 관통하고, 그 실행이 내놓은 수치를 보고 P3–P6의 존폐를 정한다. 지금 순서는 `l2_schema.py`·`inject.py`·`agree.py`를 다 쓴 뒤에야 "5조건 필드는 어디에도 없었다"를 알게 되는 순서다.

## Tradeoff tensions

1. **tier0 lexical router vs tier0 없이 tier1이 전량 판정; 계획은 tier0을 택한다.** tier0 생략은 `tools/verify/judge.py`·`backends/lexical.py`·`test_judge_cascade.py`의 라우팅 테스트와 `thresholds.yaml`의 승격률 항목을 통째로 지우고, 의미 없는 AC(V2-2 plan:162의 `escalated/total`은 81/81, `expensive_ratio`는 lexical 백엔드에서 상수 0)를 없앤다. 비용은 1,900행 확장 시점에 라우터를 다시 짓는 일과, 스펙 V2(spec:85)의 "값싼 전수 스윕" 문구를 명시적으로 어기게 되는 것이다(지금은 문구만 지키고 내용은 비어 있다).
2. **단일 SQLite 원장 vs duckdb-over-JSONL; 계획은 SQLite를 택한다(plan:31, `ledger.py` plan:70).** duckdb는 이미 `.venv`에 있어 의존 0을 유지한 채 JSONL의 장점(git diff 가능한 입력)과 SQLite의 장점(조인)을 동시에 준다. 비용은 트랜잭션·무결성 제약과, B-4(plan:178)가 의존하는 `gold` 직접 UPDATE 거부 트리거다. 이 한 가지가 SQLite 채택의 실질적 근거이므로 ADR (a)에 그렇게 적으면 근거가 훨씬 단단해진다.
3. **7단계 선구축 vs 얇은 수직 슬라이스; 계획은 7단계를 택한다(plan:63–147).** 슬라이스를 먼저 돌리면 "Codex에 `quote`가 없다", "5조건 필드는 두 벌 모두 부재", "`derived_from` 0행"을 `l2_schema.py`·`inject.py`를 쓰기 전에 안다. 비용은 `report.py`의 "네 판정이 모두 들어야 하고 하나라도 비면 실패"(plan:145) 규칙을 슬라이스 단계에서 한 번 완화했다가 P7에서 조이는 이중 작업이다.
4. **G를 존재 검사 기준이자 사람 κ 기준으로 재사용 vs 새 손 라벨 100건; 계획은 재사용을 택한다(Principle 5, `agree.py` plan:132).** 실측: G 본문은 9줄 파일의 단일 6.7 KB 줄이고, 순진한 문장 분할로 38조각·`->` 5개, 메모와 엉키지 않은 본문 문장은 33개다. n=33에서 부트스트랩 κ 게이트(κ_min 0.7, q ≤ 0.05; plan:142)는 진짜 κ≈0.85인 심판에 대해서도 통과 확률이 0.52다(3클래스·2000/300 부트스트랩 시뮬레이션; n=67 0.78, n=100 0.89, n=300 1.00). 설계 문서 자신이 "사람 라벨 ≥ 100건"을 적어 두었다(design:213). 비용은 사람 시간이며, 그것이 Principle 5와 정면으로 부딪친다.

## Verification of contractual format

- 리터럴 `## Acceptance Criteria` 표제: 있다(plan:151). 하위는 전부 `- [ ]` 불릿이며 38개, 대부분 실행 가능한 명령 형태다.
- `## ADR`(plan:192)에 Decision(194) / Drivers(196) / Alternatives considered(198) / Why chosen(205) / Consequences(207) / Follow-ups(214) 여섯 항목이 모두 있다.
- **지금 그대로는 시험 불가능한 불릿:**
  - **C0-2**(154): `N+M`이 30·37과 같아야 한다고 하지만, P1(plan:72)은 인용당 1행(`<id>.q<n>`)으로 펼친다. 정답 논문 Claude 30행의 `quotes` 총합은 44(0개 2행, 1개 14행, 2개 12행, 3개 2행)다. 계획 내부 모순.
  - **V2-2**(162)·**V4-1**(169)·plan:6/42/44/194/200: "67 레코드"는 틀린 단위다(실제 44+37=81, 또는 정의에 따라 다름). V2-2의 `expensive_ratio ≤ 0.05`는 lexical 백엔드 단독 실행에서 상수 0이라 무조건 참이다.
  - **V1-3**(158): "빈 값 0건"이 MISS 행의 `char_offset`에 무엇을 요구하는지 미정의.
  - **V1-1**(156): `claude_column` 변형은 `papers/claude_column_text/`에 `splitwise`·`dualmap` 두 편뿐이고 정답 논문에는 없다.
  - **V1-4**(159): `claude_verbatim_waivers_strict.tsv`는 48행이지만 정답 논문 행은 0건이다. v1 보고서의 `waiver_rate`는 0/81로 내용이 없다.
  - **B-3**(177): 9-15 리뷰 문서(239줄)에 정답 논문 슬러그 언급이 0건이다. `claude_50` §1-a 21건, merge-log N6 5쌍, waiver 48건도 모두 다른 논문 대상이다. 이 AC는 계획이 [이후]로 미룬 "나머지 40편 변환"(plan:219) 없이는 실행 불가다.
  - **V3-2**(166): 목표 집합 T 10개의 출처·선정 절차가 계획 어디에도 없다. G에서 뽑으면 재현율 측정이 순환한다.
  - **DE-2**(183): `--sample <등록된 n>`이라 쓰지만 `thresholds.yaml` 항목 목록(plan:142)에 `leakage_n`이 없다. tier1·tier2 두 벌의 에이전트 파일 왕복이 선행해야 하므로 단일 명령이 아니다.
  - **DE-3**(184): export 세 벌 × 에이전트 판정이 필요해 CI/pytest 안에 들어갈 수 없다. 시나리오임을 명시해야 한다.
  - **A-1**(172): "표 행 8개"인데 plan:129의 연산자는 9종(8 + `synonym_swap`)이다.

## Spec coverage gaps

- **Query/주제 입력이 계획에 전혀 없다(가장 큰 구멍).** 스펙 Goal(spec:32)은 "주제나 주장 하나와 … 근거 레코드 묶음"을 입력으로 못 박고, Ontology의 `Query`(spec:212)와 `AlignmentCheck`(spec:217, "EvidenceRecord × Query")가 이를 실체화한다. 계획 파일에는 `query`/`topic`/`주제` 문자열이 0회 등장하고, DDL 10개 테이블(plan:70)에 `queries`가 없다. 결과적으로 판정 2가 "레코드가 내 주제와 합치하는가"가 아니라 "quote가 claim_text를 뒷받침하는가"(충실성)로 조용히 축소된다.
- **spec V2 [v1] "1차 전수 스윕은 값싼 수단으로"(spec:85)**: 형식만 충족. tier0은 `supports`를 낼 수 없으므로(plan:116) 합치 판정에 기여가 0이고, 계획 자신이 tier1 100% 커버를 예상한다(plan:42).
- **spec V2 [v1] "모든 레코드에 … 하나와 근거 스팬"(spec:84)**: 전 행 verdict 충족을 확인하는 AC가 없다.
- **spec V4 [v1] `derived_from` 재계산(spec:101)**: v1 대상 행 0. 명목상 커버(P3).
- **spec C0 [v1] 필수 필드 `quote`(spec:69)**: Codex 레코드에 `quote` 필드가 없고 계획이 생성 규칙을 정하지 않았다. `locator.para_id`도 두 벌 모두 부재.
- **spec V1 [v1] "존재 검사 실패는 즉시 기각"(spec:80)**: MISS 행이 L2/judge로 흘러가지 못하게 하는 규칙이 파이프라인(plan:146)에 없다.
- **spec B [v1] 회귀 케이스(spec:116)**: 위 B-3 항목대로 v1 범위(k=1) 밖.
- **spec D3 [v1](spec:130)**: 커버되나 순환이다. G 본문에 `inferencesystem`·`broadaccess`·`MiniMaxM2.5`·`DeepSeekR1`·`10^2`가 들어 있고 이 문자열들은 `codex_..._raw.txt`에만 존재한다(layout·claude 본문 0회). 즉 G는 codex_raw 추출본을 붙여 넣은 것이다. 실측 33문장 대조: codex_raw strict 23 + loose 8 = 31, claude_body strict 12 + loose 19 = 31, codex_layout strict 3. DE-1(182)의 "layout 단독이면 MISS였을 문장 수"는 표본이 raw에서 왔기 때문에 크게 나올 수밖에 없다.
- **Elusion 상한의 달성 가능성(spec:94)**: 정답 논문의 빈 줄 블록은 20단어 이상 기준 70개, Codex가 참조하는 블록 id는 720개다. 0오류 기준 95% 정확 이항 상한은 n=10에서 25.9%, n=20에서 13.9%다. plan:142의 "재현율 ≥ 0.9"를 elusion으로 뒷받침하려면 n≈59가 필요하다.
- 사소: plan:70이 "9 테이블"이라 쓰고 10개를 나열한다.

## Synthesis

1. **[blocking] 행 단위를 확정한다.** Claude=인용당 1행(44), Codex=`quote` 구성 규칙 명문화(어느 fragment인지, 아니면 `quote` 부재를 `no_quote` 격리로 처리할지). plan:6/42/44/162/169/194/200의 "67"과 C0-2(154)의 `N+M=30` 규칙을 함께 고친다.
2. **[blocking] P3~P6 앞에 얇은 수직 슬라이스 단계를 넣는다.** convert → ledger import → l1 → tier1 export/import 1회(≤20행) → 보고서 뼈대. `report.py`의 "네 판정 모두" 규칙(plan:145)은 P7에서 조이고 슬라이스에서는 `not-run` 표기를 허용한다고 한 줄 적는다.
3. **[blocking] Query를 넣거나, 스펙 축소를 ADR에 명시한다.** `queries` 테이블 + `--query`/`--topic` 인자를 P1에 추가하거나, "v1의 판정 2는 quote↔claim_text 충실성으로 한정하고 주제 합치는 v2"라고 Alternatives/Consequences에 적는다. 조용한 축소만 금지.
4. **[blocking] L2 격리율의 지위를 바꾼다.** plan:211의 "v1의 대표 수치"를 "입력 진단치이며 사전 기대값은 두 벌 모두 100%"로 다시 쓰고, 대표 수치 자리는 L1 일치 등급 분포(변형별)로 옮긴다.
5. **[blocking] 변이 검출의 정의를 plan:129에 명문화한다.** "기준선 실행 대비 verdict 또는 사유 코드의 변화"로 정의하고, 기준선이 상수인 층에서는 해당 연산자를 `not-applicable`로 보고하도록 한다(그렇지 않으면 L2는 무조건 UNVERIFIED → 게이트 영구 실패).
6. **[blocking] B-2(176)와 plan:142의 κ 게이트를 완화하거나 표본을 키운다.** n=33에서는 좋은 심판도 48% 확률로 떨어진다. 권고: v1은 κ와 부트스트랩 CI를 보고만 하고 pass/fail을 걸지 않는다(단순 일치율 단독 보고 금지는 유지).
7. **[blocking] B-3(177)·V1-4(159)의 범위를 정한다.** 둘 다 정답 논문 밖 자산이다. (a) 회귀 케이스를 k=1에서 돌 수 있는 것만 남기거나, (b) "해당 슬러그의 Claude 레코드만 추가 변환"을 v1 예외로 올린다.
8. **[optional] `normalization.yaml`에 여섯째 규칙(줄바꿈 접합으로 사라진 공백)을 추가**하고, plan:142의 "L1 pass 100%"가 `exact|strict|loose` 중 어디까지를 pass로 세는지 정의한다(실측: claude_body는 33문장 중 19문장이 loose에서만 맞는다).
9. **[optional] DE-1(182)에 순환성 주석을 단다.** G가 codex_raw 붙여넣기임을 명시하고, 독립 대조군으로 PDF에서 직접 옮겨 적은 5문장을 넣거나, 이 시험을 "추출 노이즈 진단"으로만 읽는다고 적는다.
10. **[optional] `thresholds.yaml` 항목 목록(plan:142)에 `leakage_n`과 `escalation_max`를 추가**한다. 함께 V1-1의 `claude_column`, A-1의 8 vs 9, plan:70의 "9 테이블" 표기를 고친다.

## Principle check

- **Principle 3 "층을 섞지 않는다"(plan:15) ↔ V1-5(plan:160)의 verdict 집합 `{PASS, MISS, WAIVED}`.** waiver의 사유는 "쪽 이미지(p.2)로 원문 어순 직접 확인"처럼 사람의 시각 판단이다. 결정론적 L1의 출력 집합 안에 사람 판정을 넣는 것은 원칙의 정확한 위반 형태다(주체가 모델이 아니라 사람일 뿐). 권고: waiver는 별도 열/별도 테이블로 두고 L1 verdict는 `{PASS, MISS}`로 닫는다.
- **Principle 4 "임계는 실행 전에 등록한다"(plan:16) ↔ 단계 순서.** `config/thresholds.yaml`은 P7에서 만들어지는데(plan:142), P2·P3·P4·P5는 그 전에 자기 층을 돌린다. P4의 재표집 방지(plan:108)는 `elusion_n`·`sample_seed`가 이미 등록되어 있다고 전제하므로 P4가 P7에 역의존한다. 임계 등록은 P1 직후로 올려야 한다.
- **Principle 5 "첫 짜는 사람 손이 적게 드는 모양"(plan:17) ↔ P6.** `known_errors.tsv`(약 90 케이스 수작업 정리, plan:131), `gaming_records.jsonl` 작성(plan:135), 감사 대기열 처리(B-4), DE-2·DE-3의 에이전트 왕복 두세 벌은 며칠 단위 사람 작업이다. 스펙 제약(spec:48)과도 부딪친다. P6를 v1에서 "이미 파일로 존재하는 케이스만"으로 줄이는 편이 원칙에 맞는다.
- **Principle 1 "LLM은 심판이지 기록자가 아니다"(plan:13) ↔ 파일 왕복(plan:50, 117).** tier1/tier2 판정 행을 JSONL로 쓰는 주체가 에이전트이므로, 기록자 역할이 부분적으로 모델에 있다. 권고: import 시 "원문에서 스팬 문자열이 실제로 그 오프셋에 있는가"와 "export 행 수 == import 행 수"를 강제한다고 한 줄 추가.
- Principle 2의 앞 절("검사기는 없는 것을 지어내지 않는다")은 변환기 설계(plan:68, 74)에서 일관되게 지켜진다. 문제는 뒤 절(격리율을 대표 지표로 삼는 것)뿐이다.

## References

- plan:6,42,70,72,116,129,142,144,160,162,169,177,182,211
- spec:32,69,80,84,85,94,101,116,130,212,217
- `docs/patterns/gold/workload__year-in-llm-serving_handpicked.md:9` — G 전체가 이 한 줄(6.7 KB), `->` 메모 5개
- `claude_pattern_data.json` — 정답 논문 30행 / 인용 44개 / `caveats` 전부 빈 값
- `codex_pattern_data.json` — `quote` 필드 부재, `quote_status` 1,164행 모두 `FULL_FRAGMENT_MATCH_TO_PDF_TEXT`
- `claude_verbatim_waivers_strict.tsv` — 48행, 정답 논문 슬러그 0건
- `docs/plans/verification-system-design-2026-09-22.md:213,218-226`
