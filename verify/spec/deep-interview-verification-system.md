# Deep Interview Spec: 재사용 가능한 근거 검증 시스템

> **위치 (2026-09-22 이전).** 이 계획과 검증 시스템은 `/work/jun/AI-helper/verify/`(저장소 jun-heo/AI-helper)에 산다. 상대 경로는 모두 `/work/jun/AI-helper/verify/` 기준이며, 실행은 `cd /work/jun/AI-helper/verify` 뒤 `/athena:autopilot plans/ralplan-verification-system.md`. `~/.claude/skills`는 저장소 `.claude/skills/`로의 심볼릭 링크라 스킬 본체는 `skills/`(이 디렉토리 아래)에 두고 저장소 `.claude/skills/<name>`을 그곳으로의 심볼릭 링크로 만든다. 입력 데이터(레코드 두 벌, waivers, 원문 텍스트, 옛 검사 스크립트)는 kvcpool-trace-gen에 남으며 `$KVCPOOL`=`/work/jun/priv-mb-eval/kvcpool-trace-gen`로 가리킨다. 변환기는 이 경로를 `--source-root`(default: `KVCPOOL` 환경 변수)로 받는다. 검토 기록 `plans/*.review-*.md`는 이전 전 경로(`.athena/...`, `docs/plans/...`)를 그대로 담고 있다.

## Metadata

| 항목 | 값 |
|---|---|
| Interview ID | `verification-system` |
| Rounds | 7 |
| Final Ambiguity | 17.0% |
| Type | brownfield |
| Threshold | 20% |
| Status | done |
| Challenge modes used | contrarian (R4), simplifier (R6) |
| 초안 설계 | `docs/verification-system-design-2026-09-22.md` |
| 인수 시험 브레인스토밍 | `docs/verifier-acceptance-brainstorm-2026-09-22.md` |
| 정답 세트 G | `gold/workload__year-in-llm-serving_handpicked.md` |

## Clarity Breakdown

최종 라운드(R7) 기준이다.

| Dimension | Score | Weight | Weighted |
|---|---|---|---|
| goal | 0.85 | 0.35 | 0.2975 |
| constraints | 0.80 | 0.25 | 0.2000 |
| success | 0.82 | 0.25 | 0.2050 |
| context | 0.85 | 0.15 | 0.1275 |
| **합계** | — | 1.00 | **0.8300** (ambiguity 0.17) |

## Goal

**주제나 주장 하나와 외부에서 만들어진 근거 레코드 묶음, 그리고 코퍼스 텍스트를 입력으로 받아, 레코드마다 존재·합치·재현율·조건 보존의 네 판정을 내는 재사용 가능한 검증 시스템을 만든다.**

- 대상은 41편 한 번의 점검이 아니라 다음 주제에도 그대로 다시 돌릴 수 있는 도구다. (R1)
- 입력 계약은 스키마이며, 레코드를 누가 만들었는지는 묻지 않는다. 사람이 손으로 뽑았든 어떤 모델이 뽑았든 같은 스키마면 같은 검증을 받는다. (R3)
- 출력은 보고서 하나이고, 보고서에는 네 판정이 모두 들어 있어야 「검증됐다」고 부른다. (R2)
- 판정의 무게는 결정론적 코드와 원장에 두고, LLM은 단계식 심판으로만 쓴다. (R4)
- 첫 짜는 사람 손이 적게 드는 모양으로 낸다. 이미 손으로 뽑아 둔 논문 한 편이 사람 기준의 출발점이다. (R6, R7)

## Constraints

- **경계는 검증뿐이다.** 코퍼스에서 논문을 고르는 일(검색)과 문장을 뽑는 일(발췌)은 시스템 밖이다. 코퍼스 텍스트와 근거 레코드는 주어진 것으로 본다. (R3)
- **입력 스키마가 제품 계약이다.** 외부 추출기는 스키마만 지키면 되고, 스키마를 못 지킨 레코드는 격리 또는 기각한다. (R3)
- **LLM 심판을 허용하되 단계식으로 쓴다.** 소형 → 중형 → 고가 순으로 올리고, 아래 단계가 올려 보낸 항목에만 위 단계를 쓴다. (R4)
- **고가 모델은 PDF를 다시 읽지 않는다.** 고가 단계에는 잘라낸 컨텍스트(인용 + 그 인용이 있는 문단 + 대상 문장)만 준다. (R4)
- **토큰을 적게 쓰는 것이 설계 제약이다.** 전수 스윕은 값싼 수단으로만 한다. (R4)
- **인수 시험 네 갈래를 모두 완성 조건으로 삼는다.** A 오류 주입·심기, B 사람 기준, C 성질 시험, D·E 깨기·단계식 시험. (R5)
- **사람 시간은 최소로 쓴다.** 새로 손 라벨을 만들지 않고, 이미 손으로 뽑아 둔 문장을 정답으로 재사용한다. (R6)
- **첫 짜의 정답 세트는 논문 한 편(k=1)이다.** `workload__year-in-llm-serving`의 한줄평 + 원문 문장 약 40개 + `->` 메모가 G다. (R6, R7)
- **환경은 `.venv`(Python 3.10.12) stdlib 위주다.** numpy·pandas·scipy·torch·sentence-transformers가 없으므로 첫 짜의 결정론적 층은 stdlib로 짜고, NLI는 로컬 소형 모델 또는 API 중 하나를 선택 사항으로 둔다. (codebase_context)
- **검사기는 생성기가 고칠 수 없는 자리에 둔다.** 임계값은 실행 전에 등록하고 통과할 때까지 재표집하지 않는다. (설계 P6·P7, Lewis 2021)

## Non-Goals

- **발췌(추출)와 검색.** 문장을 고르는 일도, 어떤 논문을 읽을지 정하는 일도 시스템 밖이다. (R3)
- **결론의 참·거짓과 가치 판단.** 원문 충실성·완결성·문서 내 일관성·조건 보존까지만 보증한다. 표가 충실해도 기여인지는 따로 묻는다. (설계 P8)
- **종합 문장(보고서 수준) 검증.** v1은 레코드 수준만 검증한다. 설계 §3.7의 드리프트 층은 v1에서 다루지 않는다. (R7 기본값)
- **정답 세트를 여러 편으로 넓히는 일.** 첫 짜는 k=1이다. (R6)
- **심판 패널 다수결.** 단일 최고 심판을 항목 단위로 쓴다. (Kohli 2026)
- **41편 규모의 정량 meta-regression.** 설계 §3.8에서 이미 제외했다.
- **검증기 이름 없는 오류율 비교.** 같은 `verifier_id`·`protocol_ver` 안에서만 비율을 견준다. (Goo 2026)

## Acceptance Criteria

표기: `[v1]`은 첫 출시의 완료 조건, `[이후]`는 v1 이후 단계의 조건이다.

### C0. 입력 스키마 계약

- [ ] `[v1]` 근거 레코드 JSON 스키마 파일이 저장소에 존재한다. 필수 필드: `record_id`, `paper_id`, `quote`, `locator`(section·page·para_id), `claim_text`, `conditions`(세는 단위·분모 모집단·관측 창·이상/실측·기준선), `numbers[]`(value·unit·definition·derived_from), `kind`(measurement / author_interpretation / extrapolation), `extractor_id`, `run_id`.
- [ ] `[v1]` 정답 논문의 기존 두 레코드 벌이 손 수정 없이 변환기를 거쳐 이 스키마로 들어간다. Claude 30행, Codex 37행 모두 변환 성공 또는 사유 코드가 붙은 격리로 끝난다.
- [ ] `[v1]` 조건 필드에 값이 없을 때 「없음」을 명시한 레코드는 통과하고, 필드 자체가 빠진 레코드는 격리된다.
- [ ] `[이후]` 나머지 40편(Claude 804·Codex 1,164 전량)이 같은 변환기로 들어간다.

### V1. 판정 1 — 문장별 존재 + 위치

- [ ] `[v1]` 존재 검사는 **사용 가능한 모든 추출 변형**(codex raw, codex layout, claude 본문 텍스트, 해당 논문에 column text가 있으면 그것까지)을 대상으로 돌고, 결과에 **어느 변형에서 일치했는지**를 적는다. 어느 변형에서도 일치가 없을 때만 MISS로 판정한다.
- [ ] `[v1]` 정규화 규칙이 파일로 고정되어 있다. 공백 접기, 하이픈·붙임표 통일, 따옴표 통일, 합자 풀기, 문장 첫 글자 대소문자 차이 허용.
- [ ] `[v1]` G의 문장 전부에 대해 존재 판정 + 변형명 + 문자 오프셋이 나온다.
- [ ] `[v1]` 기존 waiver 48건이 사유 코드를 가진 구조화 예외로 옮겨지고, waiver 비율 자체가 보고 지표로 나온다.
- [ ] `[v1]` 존재 검사 실패는 즉시 기각이며, 이 층의 출력에는 모델 판단이 섞이지 않는다.

### V2. 판정 2 — 주장 합치 3분류 + 근거 스팬

- [ ] `[v1]` 모든 레코드에 supports / refutes / insufficient 중 하나와 근거 스팬(문자 오프셋)이 붙는다. Unknown 표기를 허용한다.
- [ ] `[v1]` 1차 전수 스윕은 값싼 수단(MiniCheck급 로컬 NLI 또는 소형 모델)으로 돌고, 심판 단계는 플래그된 행과 무작위 표본에만 쓴다.
- [ ] `[v1]` 모든 판정 행에 `verifier_id`와 `protocol_ver`가 기록된다. (Goo 2026)
- [ ] `[v1]` 근거 스팬이 비어 있는 supports/refutes 판정은 통과하지 못한다.
- [ ] `[이후]` 독립 검증 질문(레코드만 보이는 새 컨텍스트에서 조건을 되묻고 원 조건 필드와 대조)을 붙인다.

### V3. 판정 3 — 놓친 근거 추정치(재현율)

- [ ] `[v1]` G 대비 재현율·정밀도를 레코드 벌별(Claude, Codex, 합집합)로 내고, 필드 수준(주장 있음 / 조건 맞음 / 수치 맞음)으로 나눠 보고한다.
- [ ] `[v1]` 탐침 P 회수율과 목표 집합 T(10개) 회수가 보고된다. (Cormack & Grossman target method)
- [ ] `[v1]` 두 벌 중 어느 쪽도 쓰지 않은 문단에서 뽑은 elusion 표본의 크기 n을 실행 전에 등록하고, 정확 이항 상한으로 보고한다. 통과를 노린 재표집은 하지 않는다. (Lewis 2021)
- [ ] `[v1]` 독립적인 레코드 벌이 둘 있을 때만 포획-재포획 추정을 내고, 추정치는 하한으로 표기한다.
- [ ] `[이후]` 심은 오류 비율로 잔여 오류를 추정한다. (브레인스토밍 A2)

### V4. 판정 4 — 조건·수치 보존

- [ ] `[v1]` 조건 5필드의 존재/「없음」 명시를 전수 검사하고, 미완은 비교표 진입을 막는다.
- [ ] `[v1]` `derived_from`이 있는 수치를 재계산하고, 같은 논문 안에서 같은 양을 다르게 말하는 행을 격리한다.
- [ ] `[v1]` 단위 변경·수치 자리바꿈·조건 삭제·조건 넓힘·양태 상승(may → is)을 판정 대상 오류 유형으로 명시하고 각각 검출 결과를 낸다.
- [ ] `[이후]` 종합 문장의 조건 포함 관계와 확신 표지 diff. (설계 §3.7, v1에서 다루지 않음)

### 시험 A — 오류 주입·심기 (known-answer)

- [ ] `[v1]` 변이 연산자 8종(인용 한 단어 치환, 수치 자리바꿈, 단위 변경, 조건 삭제, 조건 넓힘, 양태 상승, 출처 논문 뒤바꿈, 주장–인용 짝 바꾸기) × 각 50건에 대한 유형별 검출률 표가 나온다.
- [ ] `[v1]` 뜻이 바뀌지 않는 변이(동의어 치환)로 오탐률을 따로 잰다.
- [ ] `[v1]` 검사기가 자기 표적 오류 유형에서 등록 검출률에 못 미치면 그 층의 pass는 「미검증」으로 표기된다.
- [ ] `[이후]` 합성 코퍼스 픽스처로 파이프라인 끝까지 회귀 시험. (브레인스토밍 A4)

### 시험 B — 사람 기준 (human reference)

- [ ] `[v1]` G가 문장 단위로 파싱되어 스키마 레코드로 등록된다. 한줄평·`->` 메모는 사용자 해석으로 별도 필드에 남고 원문 문장과 섞이지 않는다.
- [ ] `[v1]` G 대비 합치 판정의 κ(또는 α)를 부트스트랩해 「기준 미달 확률 q」로 보고한다. 단순 일치율만으로 통과를 선언하지 않는다. (Norman 2026)
- [ ] `[v1]` 회귀 케이스: 이미 사람이 찾아 둔 오류(9-15 리뷰 지적, `claude_50` §1-a 21건, merge-log N6 5쌍, waiver 48건의 정당한 예외/진짜 오류 구분)를 고정 테스트로 굳히고, 하나라도 놓치면 사유를 적어야 통과한다.
- [ ] `[v1]` 감사-후-채점 절차가 정의되어 있다. 검증기와 G가 어긋나면 근거를 대고 감사자가 판정하며, G의 수정 이력이 남는다. (DeepFact)
- [ ] `[이후]` 그림자 모드: 게이트로 승격하기 전 기존 수작업 리뷰와 나란히 N회 돌려 결정을 비교만 한다.
- [ ] `[이후]` 정답 논문을 k>1로 넓힌다.

### 시험 C — 정답 없이 성질로 (oracle-free)

- [ ] `[v1]` 메타모픽 관계 최소 4개가 단위 테스트로 있다. (a) 좌우·순서를 바꿔도 판정 불변, (b) 무관한 문단을 컨텍스트에 더해도 존재 판정 불변, (c) 수치를 바꾸면 보존 판정이 정해진 방향으로 뒤집힘, (d) 레코드 부분집합만 돌려도 각 행 판정이 전체 실행과 같음. (T.Y. Chen 1998)
- [ ] `[v1]` 재검사 일치(test–retest): 같은 입력을 두 번 넣어 단계별 판정 뒤집힘 비율을 낸다.
- [ ] `[v1]` 차등 테스트: 추출 변형 둘(raw/layout) 또는 프롬프트 둘의 불일치를 「어려운 사례」로 모은다.
- [ ] `[이후]` CheckList식 능력 × 시험 유형 행렬을 채운다.

### 시험 D·E — 깨기와 단계식

- [ ] `[v1]` 추출 노이즈 강건성(D3): 하이픈 분절·합자·열 순서·각주 끼어들기에 대한 존재 검사 오탐률을 raw/layout 쌍과 waiver로 측정한다. **정답 논문 표본에서 layout 텍스트만 보면 참인 문장을 MISS로 부르는 사례가 실제로 나왔으므로, 이 시험은 v1 완료 조건이다.**
- [ ] `[v1]` 승격 누출률(E1): 소형 단계가 통과시킨 항목에서 표본을 뽑아 고가 단계가 재판정하고, 통과분 중 틀린 비율을 정확 이항 상한으로 보고한다.
- [ ] `[v1]` 컨텍스트 절단 충분성(E3): 고가 단계에 인용만 / 인용+문단 / 인용+문단±1을 줄 때 판정이 바뀌는 비율을 내고, 바뀌지 않는 최소 컨텍스트를 기록한다. (Konet 2024)
- [ ] `[v1]` 예산 완주(F2): 1,000 레코드당 토큰·벽시계와 고가 단계 호출 비율이 보고되고, 등록된 상한을 넘으면 실패로 처리된다.
- [ ] `[v1]` 게이밍 시험(D2): 검증기 규칙을 그대로 보여 준 뒤 최소 노력으로 통과를 노리는 레코드를 만들어 보고, 통과하면 그 검사를 대역 밖으로 옮긴다.
- [ ] `[이후]` 적대적 라운드(D1): 다른 모델에게 「통과하지만 틀린 레코드」를 만들게 하고 통과율로 사각 지도를 그린다. (FEVER 2.0)
- [ ] `[이후]` 보정 곡선과 conformal 상한(E2).

### 운영

- [ ] `[v1]` 임계값이 `config/thresholds.yaml`에 실행 전에 등록되고 해시가 출처 묶음에 남는다.
- [ ] `[이후]` 모델 판·프롬프트가 바뀔 때마다 A·C 묶음을 CI처럼 재실행하고 변이 점수 추이를 기록한다. (F1)
- [ ] `[이후]` 오탐 1건이 먹는 사람 시간을 재서 임계에 반영한다. (F3)

## Assumptions Exposed & Resolved

| Assumption | Challenge | Resolution |
|---|---|---|
| 「찾아서 발췌하고 검증한다」에는 검색·발췌도 든다 | R3에서 경계를 셋 중 하나로 고르게 함 | 「검증만」. 발췌·검색은 밖, 입력 스키마가 계약이 됨 |
| 검증에 쓸 판단 자원은 사람 또는 결정론적 코드뿐이다 | R4 **contrarian** — 사람만 / 로컬 소형 / API 보정·기록 / API 자유의 상한을 되물음 | LLM 심판 허용. 단, 소형→중형→고가 단계식이고 고가 단계는 PDF를 다시 읽지 않고 잘라낸 컨텍스트만 받음 |
| 인수 시험은 여섯 갈래 중 골라 담는 것이다 | R5에서 최소 세트를 권고 | 네 갈래(A·B·C·D·E) 전부를 완성 조건으로 채택. 대신 v1/이후로 나눔 |
| 인수 시험을 넓히면 사람 시간이 크게 든다 | R6 **simplifier** — 감사자가 쓸 수 있는 시간을 직접 물음 | 새 손 라벨을 만들지 않고 이미 뽑아 둔 문장을 G로 재사용. 첫 출시는 자동 시험 위주, B는 그 한 편에서 출발 |
| 정답 세트는 저장소 안 어딘가에 있다 | R7에서 위치를 물음 | 저장소 밖(사용자 노트)이었고, R7에서 `gold/workload__year-in-llm-serving_handpicked.md`로 편입 |
| 정답 세트는 k=3편이 필요하다 (설계 §3.1) | R6·R7 | k=1로 좁힘. 나머지 편수는 이후 단계 |
| 존재 검사는 텍스트 한 벌만 보면 된다 | 스펙 작성 중 정답 문장 표본 재확인 | 변형마다 결과가 달라지므로 모든 변형을 보고 일치한 변형명을 적는 방식으로 고정 (V1-1) |

### 기본값으로 남긴 미결 항목 (결정 아님)

| 항목 | 기본값 | 다시 열어야 하는 시점 |
|---|---|---|
| 토큰 예산 수치 | 고가 단계 호출은 레코드의 5% 이하. 레코드당 토큰 상한은 첫 실행 전에 `config/thresholds.yaml`에 등록 | 첫 실행 전 |
| 발췌기와 같은 계열 모델을 심판으로 쓰는 것 | 허용하되 `checks.verifier_id`에 적고 보고서에 드러낸다. 다른 계열을 우선한다 | 심판 보정(κ) 결과가 계열별로 갈릴 때 |
| 통과 임계값 | 설계 §4의 예시 표를 프로젝트 값으로 등록. 등록 후 재표집 없음 | 등록 전 한 번, 이후에는 프로토콜 판 올림과 함께만 |
| 종합 문장(보고서 수준) 검증 | v1에서 다루지 않는다. v1은 레코드 수준만 | 레코드 층이 안정된 뒤 |
| 레코드 벌이 하나뿐일 때의 재현율 둘째 신호 | G 대비 재현율 + 심어 둔 탐침 + 미사용 문단 elusion 표본. 포획-재포획은 독립된 두 벌이 있을 때만 | 새 코퍼스에 한 벌만 들어올 때 |

## Technical Context

### 저장소에 이미 있는 것 (brownfield)

| 자산 | 경로 | v1에서 |
|---|---|---|
| L1 존재 검사 원형 | `$KVCPOOL/tools/quotes_verbatim_check.py` — codex raw 텍스트와 `$KVCPOOL/docs/patterns/claude_quotes/*.md` 대상, 출력은 MISS 목록 + 「checked N quotes, M without a verbatim match」 | **편입·확장.** 모든 추출 변형 검사와 변형명 보고로 바꾼다 |
| waiver 목록 | `$KVCPOOL/docs/patterns/260911_claude_quotes_final/claude_work/claude_verbatim_waivers_strict.tsv` 48건 (slug·qid·frag_sha1_12·사유·확인 방법) | **편입.** 사유 코드 구조화 + 회귀 케이스 |
| 재현율 도구 원형 | `$KVCPOOL/tools/quotes_coverage.py` — 수치 토큰/문단/병합 문단 3종. 옛 세트(`$KVCPOOL/docs/patterns/claude_quotes`, `$KVCPOOL/docs/patterns/evidence.tsv`)를 가리킴 | **재조준.** 현재 레코드 벌과 문단 단위로 |
| Claude 레코드 | `$KVCPOOL/docs/patterns/260911_claude_quotes_final/claude_pattern_data.json` records 804 (id, paper, location, section, page, stars, topic, quotes[], meaning, why, numbers[], caveats, unreported, kind, links, check, relation, conversion, secondary, figure_read) | **정답 논문분 30행만** 스키마 변환 |
| Codex 레코드 | `$KVCPOOL/docs/patterns/260911_codex_quotes_final/codex_pattern_data.json` records 1,164 (id, blocks, location, kind, topic, meaning, conditions, numbers, links, paper, title, version, pdf, fragments[{id,page,bbox,text,sha256}]) | **정답 논문분 37행만** 스키마 변환. `fragments`의 page·bbox·sha256이 locator 설계의 기준 |
| 수치 대조 자산 | `claude_work/claude_numbers_raw.tsv` 638행, `codex_verify_metric_sources.py`(fragment sha256, raw/layout 양쪽 존재 검사), `codex_numeric_sources.tsv` 65,843행 | **편입.** V4의 출발점 |
| 빌더 assert | `claude_build_patterns.py:206`(중복 id), `codex_build_patterns.py:14,23,29,42,43`(id·blocks·refs 존재), `$KVCPOOL/tools/patterns_publish.py:49` | v1은 그대로 둔다. 링크 강제 검사로의 대체는 이후 |
| 원문 텍스트 | `$KVCPOOL/papers/*.pdf` 41편, `$KVCPOOL/papers/codex_source_text/` 82 txt(raw+layout), `$KVCPOOL/docs/patterns/260911_claude_quotes_final/claude_source_text/` 41 txt, `papers/claude_column_text/` 2 | **v1 입력.** 변형 목록이 곧 존재 검사의 대상 집합 |
| 실행 환경 | `.venv` Python 3.10.12, stdlib 위주. numpy·pandas·scipy·torch·sentence-transformers 없음 | 결정론적 층은 stdlib로. NLI는 외부 의존을 따로 결정 |

### 정답 논문 표본 재확인 (L1 정규화·강건성 근거)

`workload__year-in-llm-serving`의 손 발췌에서 6구를 뽑아, 공백·하이픈·따옴표·합자·대소문자를 정규화한 뒤 세 추출 변형에 대해 문자열 포함을 확인했다.

- 합집합 기준 6구 모두 어느 한 변형에는 원문 그대로 있었다. `codex_workload__year-in-llm-serving.txt`(raw)에서 6구, `claude_workload__year-in-llm-serving.txt`에서 5구가 일치했다.
- `_layout.txt`만 보았다면 2구만 일치하고 나머지는 MISS로 불렸을 것이다. 원인은 두 단 조판이 섞여 문장이 다른 단의 조각으로 끊기는 것이다.
- 한 구는 사용자가 문장 앞의 「Thus, 」를 떼고 `Even`으로 적어 둔 경우였다. 문장 첫 글자 대소문자 차이를 정규화에 넣어야 잡힌다.
- 따라서 L1은 텍스트 한 벌이 아니라 변형 전부를 보고, 어느 변형에서 맞았는지를 함께 내야 한다. (브레인스토밍 D3)

### 구현 형태 (설계 §2.3에서 채택)

| 층 | 형태 | v1 |
|---|---|---|
| 원장(SQLite), L1 존재, 스키마 검사, 산술 검사, 재현율 추정, 오류 주입, 게이트 | Python 패키지 `tools/verify/` + CLI 하위 명령 | **짓는다** (`ledger.py`, `l1_exists.py`, `l2_schema.py`, `l6_arith.py`, `recall.py`, `inject.py`, `gate.py`, `config/thresholds.yaml`) |
| 교차 판정(α 부트스트랩), 드리프트 diff | `agree.py`, `drift.py` | 이후 |
| 심판 프롬프트·순서 교대·Unknown 규칙 | 스킬 `~/.claude/skills/claim-judge/` | **짓는다** (얇게) |
| 추출기 프롬프트 | 스킬 `~/.claude/skills/claim-extract/` | 짓지 않는다 (발췌는 시스템 밖) |
| 파이프라인 진입점·보고서 | 스킬 `~/.claude/skills/verify-run/` | **짓는다** |
| 출시 차단 훅에서 `gate.py` 호출 | Stop 또는 빌드 전 훅 | 이후 |
| NLI 1차 전수 스윕 | MiniCheck급 로컬 소형 모델 | **v1의 선택 지점** — 로컬 의존을 들일지 API 소형 단계로 대신할지는 첫 실행 전에 결정 |

기존 `quotes_verbatim_check.py` → `l1_exists.py`, `quotes_coverage.py` → `recall.py`, `codex_verify_metric_sources.py` → `l6_arith.py`가 각각의 출발점이다.

## Ontology

최종 라운드(R7)의 16개 엔티티다. 필드는 인터뷰에서 적힌 것과 설계 §2.2의 원장 스키마에서 온다.

| Entity | Type | Fields | Relationships |
|---|---|---|---|
| Corpus | input | papers, text(변형별), paragraphs | Paper·Paragraph를 담는다. EvidenceRecord의 대조 대상 |
| Query | input | topic, claim | AlignmentCheck의 기준. Report의 머리 |
| EvidenceRecord | artifact | record_id, paper_id, quote, locator, claim_text, conditions, numbers[], kind, extractor_id, run_id | InputSchema를 따른다. 네 Check의 대상 단위 |
| InputSchema | contract | 필수 필드, 조건 5필드, 「없음」 규칙, 버전 | Extractor와 VerificationSystem 사이의 계약 |
| Extractor | external | extractor_id, model, run | EvidenceRecord를 만든다. 시스템 밖 |
| ExistenceCheck | check | verdict, matched_variant, offset, normalization, waiver_reason | EvidenceRecord.quote → Corpus 변형. 실패는 즉시 기각 |
| AlignmentCheck | check | verdict(supports/refutes/insufficient), evidence_span, rationale, verifier_id, protocol_ver | EvidenceRecord × Query. JudgeCascade가 수행 |
| RecallEstimate | check | gold_recall, probe_recall, target_recall, elusion_upper, capture_recapture | GoldPaper·Corpus 미사용 문단에 기댄다 |
| PreservationCheck | check | condition_fields, unit, derived_from_recompute, modality_shift | EvidenceRecord.conditions·numbers 대상 |
| JudgeCascade | component | small, mid, expensive, context_cut, escalation_rate | AlignmentCheck를 수행. TokenBudget의 지배를 받는다 |
| TokenBudget | constraint | per_record_cap, expensive_call_ratio, wallclock | JudgeCascade를 제한. 위반은 실패 |
| AcceptanceSuite | test | mutation, human_sample, metamorphic, adversarial, leakage | VerificationSystem을 시험한다. MutationOperators를 쓴다 |
| MutationOperators | test | 연산자 8종, 등가 변이, 유형별 검출률·오탐률 | AcceptanceSuite A갈래의 재료 |
| GoldPaper | data | slug, handpicked_sentences, user_notes, source_variants | RecallEstimate·AlignmentCheck의 기준(k=1) |
| Report | artifact | 네 판정, verifier_id, 임계 대비 결과, 출처 묶음 | VerificationSystem의 산출물 |
| VerificationSystem | system | reusable, layers, thresholds, ledger | 위 전부를 묶는 시스템 경계 |

## Ontology Convergence

| Round | Count | New | Changed | Stable | Stability |
|---|---|---|---|---|---|
| 1 | 6 | 6 | 0 | 0 | — |
| 2 | 9 | 3 | 0 | 6 | 0.67 |
| 3 | 11 | 2 | 1 | 8 | 0.82 |
| 4 | 13 | 2 | 0 | 11 | 0.85 |
| 5 | 15 | 2 | 0 | 13 | 0.87 |
| 6 | 16 | 1 | 0 | 15 | 0.94 |
| 7 | 16 | 0 | 0 | 16 | 1.00 |

## Interview Transcript

<details>
<summary>Full Q&A (7 rounds)</summary>

**Round 1 — goal**

Q. 이 시스템을 만들어서 결국 손에 쥐고 싶은 것은 무엇입니까? 완성됐을 때 「됐다」고 말하게 되는 산출물 하나를 고르면?

A. 재사용 가능한 검증 시스템인데, 어떤 주제나 주장이 담긴 논문을 찾아서 corpus로부터 근거 문장을 발췌하고, 그 문장이 진짜 있는 말인지, 내가 원하는 주제나 주장과 합치하는지 등을 검증하는 시스템이 필요.

→ ambiguity 65.5% (weakest: success)

**Round 2 — success**

Q. 시스템이 근거 문장 목록을 내놓았을 때 보고서에 반드시 들어 있어야 「검증됐다」고 받아들일 항목은?

A. 문장별 존재 판정 + 위치, 주장 합치 3분류 + 근거 스팬, 놓친 근거 추정치(재현율), 조건·수치 보존 판정 (넷 모두)

→ ambiguity 50.75% (weakest: constraints)

**Round 3 — constraints**

Q. 시스템의 경계는 어디입니까? 검증만 / 발췌+검증 / 검색+발췌+검증

A. 검증만

→ ambiguity 37.25% (weakest: constraints)

**Round 4 — constraints (challenge: contrarian)**

Q. 검증기 안에서 허용할 판단 자원의 상한은? (사람만 / 로컬 소형 / API LLM 보정·기록 / API LLM 자유)

A. AI(LLM) 심판 허용. 소형·중형·비싼 모델을 함께 써서 토큰을 적게 쓰고 싶다. 비싼 모델이 PDF를 다시 보고 확인하는 것은 토큰이 많이 들어서 피해야 한다.

→ ambiguity 32.25% (weakest: success)

**Round 5 — success**

Q. 여섯 갈래 중 「검증 시스템 완성」의 조건으로 삼을 것은?

A. A 오류 주입·심기, B 사람 기준, C 성질 시험, D·E 깨기·단계식 시험 (넷 모두)

메모: 사용자가 답하기 전에 인수 시험 브레인스토밍을 요청했고, 결과를 `docs/verifier-acceptance-brainstorm-2026-09-22.md`에 저장했다. (A known-answer, B human reference, C oracle-free, D adversarial, E cascade, F operations)

→ ambiguity 25.3% (weakest: constraints)

**Round 6 — constraints (challenge: simplifier)**

Q. 첫 실전 적용에서 감사자가 쓸 수 있는 시간은? (반나절~하루 / 2–3일 / 1주 이상 / 거의 없음)

A. 논문 하나 기준으로 내가 뽑아 놓은 문장들이 있다. 이것을 기준으로 사람 표본을 잡고 진행. (사람 시간은 기존 손 작업을 정답으로 재사용하는 수준)

→ ambiguity 21.55% (weakest: context)

**Round 7 — context**

Q. 「논문 하나 기준으로 내가 뽑아 놓은 문장들」은 저장소의 어느 것입니까?

A. 저장소 밖(사용자 노트). 'A Year in LLM Serving (Harvard)' 논문(workload__year-in-llm-serving)에 대한 한줄평 + 원문 문장 약 40개 + '->' 메모를 붙여 넣음. gold/workload__year-in-llm-serving_handpicked.md로 저장. (붙여 넣은 원문 약 7 KB는 그대로 해당 파일에 보관)

→ ambiguity 17.0% — 임계 20% 아래, 인터뷰 종료.

</details>
