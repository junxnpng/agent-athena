---
title: 개인 AI 시스템 — 반출 팩 (전체 합본)
created: 2026-08-28
tags:
  - ai-system
  - handoff
  - skills
  - vendoring
  - patch
status: ready
구성: 1부 작업지시 · 2부 spec v1 · 3부 카탈로그 · 4부 vendoring 전수 감사(적응 diff 정본) · 5부 코드 패치(git am)
---

> [!abstract] 반출은 이 파일 하나면 된다
> 기존 팩(1~3부)에 회사 세션(2026-08-28)의 두 산출물을 합본: **4부 = vendoring 26종 전수 감사**(전원 적재,
> 적응 diff의 정본 — 1부 적응 열보다 우선), **5부 = agent-athena 코드 패치**(커밋 `598b344` = 훅 카나리아·
> 비용 상한·S2 완화·G2 DAG; 기준 `894cf7d` 위에 `git am`).
> ⚠ **5부의 패치 블록은 공백·빈 줄이 보존돼야 한다** — 이 파일을 볼트에 파일째 넣고, 추출은 소스 모드에서.
> 원본 3파일(ai-system-handoff-pack.md / handoff-vendor-audit.md / handoff-code-patch.md)의 합본이므로
> 원본을 고치면 재합본 필요.

> [!abstract] 이 문서 하나가 전부다
> 회사 세션에서 확정한 것을 집에서 실행하기 위한 단일 팩.
> **1부**만 읽으면 바로 실행 가능. 2부는 이 작업이 놓이는 전체 그림, 3부는 근거(전수 카탈로그).
> agent-athena repo에는 v0(docs/spec-v0.md)이 이미 있다 — 2부(v1)가 그 상위 문서다.

> [!note] 집 세션 적용 기록 (2026-08-28)
> 5부 패치는 `894cf7d` 위에 `git am`으로 적용됐다(아래 5부의 패치 블록은 적용된 커밋의 `git format-patch` 출력).
> 1부·4부의 vendoring 실행 결과는 `skills/vendor/VENDORED.md`와 커밋 로그(`[vendor] …`)에 있다.

# 1부 — 작업 지시: 스킬 vendoring (Tier 1+2)

> [!tip] 시작 프롬프트 (이걸 그대로 붙여넣기)
> ```
> agent-athena repo에 이 문서를 놓고, "1부 — 작업 지시"를 읽고 그대로 수행해줘.
> Tier 1·2 전부 실행. 스킬 하나당 커밋 하나. 감사에서 의심스러운 게 나오면
> 그 스킬만 보류하고 사유를 VENDORED.md에 적어. 끝나면 scripts/check 통과
> 확인하고 VENDORED.md 요약을 보여줘.
> ```

> [!important] 2026-08-28 갱신 — 감사는 이미 끝났다
> 26종 전수 정독 감사를 회사 세션에서 선행 완료 — 판정(전원 적재·보류 0)·소견·**적응 diff의 정본은
> **4부(vendoring 사전 감사)****다. 아래 표의 적응 열과 다르면 감사 문서가 우선(감사가 갱신한 항목:
> systematic-debugging·writing-plans·executing-plans·research·code-review·arxiv-search·brainstorming·dsh-trim-cot-leakage).
> 집 작업 = 클론 → 복사 → 감사 문서의 적응 적용 → 커밋 (재정독은 스팟 체크로 충분).
> da·ds 고정 커밋도 감사 시점으로 확정: da `457ac435e121` · ds `cd5ef8148158`.

## 목표

외부 스킬을 agent-athena에 vendoring한다. **Tier 1+2 전부 실행 (vendor 26 + 공식 설치 4)** —
Tier 2 전량 채택은 2026-08-28 사용자 결정. 유일한 보류 사유는 **감사에서 나온 의심**뿐이다.

> [!note] 분량 감각
> vendor 26종 전수 정독 감사는 하루를 넘길 수 있다. 끊어야 하면 아래 순서대로 —
> **B-Tier1(밤샘 품질) → 설치 4종(잡무 즉효) → A-Tier1 → Tier 2** — 어디서 멈춰도 손해가 적다.

## 절대 규칙

1. **고정 커밋에서만 가져온다** (아래 표). 최신 HEAD 금지 — 감사한 버전과 달라진다.
2. **복사 전에 그 스킬의 모든 파일을 정독한다** — 지시문 속 네트워크·유출 경로, 조건부 지시(semantic supply-chain).
   의심스러우면 건너뛰고 VENDORED.md에 사유를 적는다.
3. **PROPRIETARY는 복사 금지**: anthropic docx/xlsx/pptx/pdf는 라이선스가 "Services 밖 추출·보관·파생물 금지".
   → 공식 플러그인/마켓플레이스 경로로 **설치**만 한다.
4. **superpowers의 hooks/는 가져오지 않는다** — 우리 훅과 이중 발화. `skills/<이름>/` 디렉토리만.
5. 스킬 하나 = 커밋 하나 (`[vendor] <이름> from <repo>@<커밋7자리>`). 되돌리기 단위.
6. 새 스킬마다 **I7 재검사**: 본문에 네트워크 지시가 있으면 "모드 A 전용" 표시를 frontmatter 아래 첫 줄에 명시.
7. 에이전트(너)가 스킬 내용을 창작·확장하지 않는다. 적응 열에 적힌 수정만.

## 사전 준비

```bash
mkdir -p skills/vendor && touch skills/vendor/VENDORED.md
W=$(mktemp -d)
git clone -q https://github.com/mattpocock/skills.git      $W/mp && git -C $W/mp checkout -q 6654f6b60cd9
git clone -q https://github.com/obra/superpowers.git       $W/sp && git -C $W/sp checkout -q b36e0829c6d0
git clone -q https://github.com/anthropics/skills.git      $W/ant && git -C $W/ant checkout -q 3b3fad96af16
git clone -q https://github.com/DietrichGebert/ponytail.git $W/pt && git -C $W/pt checkout -q 2ed6c52c9d7e
git clone -q https://github.com/langchain-ai/deepagents.git $W/da  && git -C $W/da checkout -q 457ac435e121
git clone -q https://github.com/deepseek-ai/deepseek-harness.git $W/ds && git -C $W/ds checkout -q cd5ef8148158
```

VENDORED.md 행 형식: `| 이름 | 소스repo | 커밋 | 라이선스 | 감사일 | 수정 내역 |`

## Tier 1 — 무조건 실행

권장 순서: **B(밤샘 품질) → 설치 4종(잡무 즉효) → A 나머지**.

### B 트랙 (무인 밤샘용 — 모델 호출형)

| # | 스킬 | 소스 경로 | 라이선스 | 적응 |
|---|---|---|---|---|
| 1 | verification-before-completion | `$W/sp/skills/verification-before-completion/` | MIT | 없음 |
| 2 | systematic-debugging | `$W/sp/skills/systematic-debugging/` (11파일) | MIT | 없음 |
| 3 | ponytail-review | `$W/pt/skills/ponytail-review/` ← **루트 skills/, .openclaw/ 아님** | MIT | 없음 |

### 공식 설치 (복사 금지)

| # | 스킬 | 방법 |
|---|---|---|
| 4 | docx · xlsx · pptx · pdf | Claude Code 공식 플러그인/마켓플레이스에서 anthropics 스킬 설치. **파일을 repo로 복사하지 않는다** |

### A 트랙 (대화형)

| # | 스킬 | 소스 경로 | 라이선스 | 적응 |
|---|---|---|---|---|
| 5 | grilling | `$W/mp/skills/productivity/grilling/` | MIT | 없음 |
| 6 | brainstorming | `$W/sp/skills/brainstorming/` (4파일) | MIT | 없음 |
| 7 | teach | `$W/mp/skills/productivity/teach/` (6파일) | MIT | `argument-hint`는 CC 확장이지만 A 전용이라 유지 |
| 8 | arxiv-search | `$W/da/libs/code/examples/skills/arxiv-search/` | MIT | 본문 첫 줄에 "모드 A 전용 — 네트워크(I7)" 명시 |
| 9 | handoff | `$W/mp/skills/productivity/handoff/` | MIT | 저장 위치를 OS tmp → `.harness/sessions/`로 변경 |
| 10 | writing-plans | `$W/sp/skills/writing-plans/` | MIT | 없음. plan.json 계약(리프 5~30분·검증기 필수)과 모순되는 문장 있으면 우리 쪽 우선 주석 |
| 11 | domain-modeling | `$W/mp/skills/engineering/domain-modeling/` | MIT | CONTEXT.md 경로 언급이 우리 규약과 일치 — 그대로 |

## Tier 2 — 전부 실행 (2026-08-28 사용자 결정)

Tier 1과 같은 절차. 보류는 감사에서 의심이 나온 스킬만 (사유를 VENDORED.md에).

### A 트랙

| 스킬 | 소스 경로 | 적응 |
|---|---|---|
| research | `$W/mp/skills/engineering/research/` | 없음 (백그라운드 위임 = CC Task) |
| to-spec | `$W/mp/skills/engineering/to-spec/` | 이슈 트래커 발행부 → 로컬 md 저장으로 대체 |
| wait-what | `$W/mp/skills/productivity/wait-what/` | CONTEXT-MAP 언급 → CONTEXT.md 단수로 |
| writing-for-agents | `$W/mp/skills/productivity/writing-for-agents/` | 없음 |
| skill-creator | `$W/ant/skills/skill-creator/` (18파일) | Apache-2.0 확인됨. eval 스크립트 포함 — 전부 정독 |
| frontend-design | `$W/ant/skills/frontend-design/` | Apache-2.0 |
| improve-codebase-architecture | `$W/mp/skills/engineering/improve-codebase-architecture/` | grilling 위임부 확인 |
| code-review | `$W/mp/skills/engineering/code-review/` | 없음 |
| receiving-code-review | `$W/sp/skills/receiving-code-review/` | 없음 |
| using-git-worktrees | `$W/sp/skills/using-git-worktrees/` | 없음 |
| executing-plans | `$W/sp/skills/executing-plans/` | 없음 |
| retro | `$W/mp/skills/in-progress/retro/` | ⚠ in-progress 성숙도 — findings/ 초안 생성으로 연결 검토 |

### B 트랙

| 스킬 | 소스 경로 | 적응 |
|---|---|---|
| test-driven-development | `$W/sp/skills/test-driven-development/` | 없음 |
| webapp-testing | `$W/ant/skills/webapp-testing/` | Apache-2.0. Playwright 의존 — init.sh 계약으로 |
| dsh-trim-cot-leakage | `$W/ds/.agents/skills/dsh-trim-cot-leakage/` | **범용화**: "deepseek-harness repo" 언급 제거, 일반 문서 대상으로 |
| to-tickets | `$W/mp/skills/engineering/to-tickets/` | ⚠ vendor하되 **당장 로드하지 않음** — P7 착수 시 plan.json 생성기 원료 |

## 완료 기준

- [ ] vendor 26종(T1 10 + T2 16)이 `skills/vendor/`에, 각각 커밋 하나씩 — 보류분은 제외
- [ ] VENDORED.md에 전 항목 (소스·커밋·라이선스·감사일·수정 내역), 보류는 "보류: <사유>" 한 줄
- [ ] 문서 4종 공식 설치 확인 (`claude`에서 스킬 목록에 보임)
- [ ] `scripts/check` 통과
- [ ] `claude --plugin-dir .` 스모크: 스킬들이 목록에 뜨고, USER 호출형이 슬래시로 보임
- [ ] 네트워크 지시가 있는 스킬(arxiv-search 등)에 "모드 A 전용" 표시
- [ ] to-tickets는 vendor하되 로드 제외 상태 확인 (P7 착수 전까지)

## 하지 말 것 (이 작업의 범위 밖)

- 스킬 본문 개선·확장 (적응 열의 수정만)
- superpowers hooks/ · using-superpowers · 병렬 쓰기 계열(subagent-driven, dispatching-parallel)
- vercel-labs/agent-skills 일체 (LICENSE 없음) · doc-coauthoring (동일)
- 새 스킬 자작 (그건 다음 작업 — writing-for-agents+skill-creator vendor 후)


---

# 2부 — 개인 AI 시스템 spec v1

> [!abstract] 한 줄
> **Claude 기반 개인 AI 시스템.** 세 도메인(공부 / 리서치+회사일 / 잡무)을
> 두 실행 모드(대화형 / 무인)로 처리한다. v0의 밤샘 하네스는 이 시스템의 **한 날개**다.

## 0. v0에서 무엇이 바뀌나

v0은 무인 밤샘 하네스에 편중됐다. 원인 둘 — 대화가 가장 어려운 결정(A2·B8)으로 파고들었고
그 답이 전부 무인 실행 쪽에 있었다는 것, 그리고 "도메인 무의존"을 커버리지로 착각한 것.
**인프라가 도메인 무의존인 것과 세 도메인이 실제로 굴러가는 것은 다른 문제다.**

| | v0 | v1 |
|---|---|---|
| 범위 | 무인 밤샘 하네스 | 시스템 전체 (대화형 + 무인 + 공유 기반) |
| 스킬 | 자작 4개 후보 | **외부 hot 스킬 이식이 1급 트랙** + 자작 |
| 도메인 | "무의존"으로 처리 | 도메인별 적합표 (무엇을 쓰고 무엇이 비는가) |
| v0 산출물 | — | **그대로 유효.** agent-athena는 모드 B의 구현이자 시스템의 배송 수단(플러그인) |

> [!important] v0을 버리지 않는다
> agent-athena의 훅·CONTEXT·.out-of-scope·ASSUMPTIONS·findings 문화는 **공유 기반**이고,
> 러너는 모드 B다. v1은 그 옆에 모드 A(대화형)와 스킬 이식 트랙을 세우는 것이다.

---

## 1. 시스템 전경

```
개인 AI 시스템 (Claude Code 기반 · Codex는 Phase 후순위)
│
├─ 모드 A · 대화형 (daily driver)          ← v1의 신규 트랙
│    사람이 있다. 승인·방향 전환이 실시간.
│    스킬 팔레트(이식+자작) · 훅은 부기 보호만
│
├─ 모드 B · 무인 (night)                   ← v0 구현 완료 (agent-athena)
│    사람이 없다. 검증기 있는 작업만. I7 엄격.
│
└─ 공유 기반
     skills/ (이식 vendor + 자작) · CONTEXT.md 어휘 · .out-of-scope/ 거절 기록
     ASSUMPTIONS.md 가정 · hooks (부기 강제) · findings/ 실패 기록
     메모리·노트 층 (미정 — §7)
```

### 도메인 × 모드 적합표

| 도메인 | 모드 A (대화형) | 모드 B (무인) |
|---|---|---|
| **개인 AI 공부** | **주 무대.** teach·research·grilling 계열 스킬 | 부분 가능 — 검증기를 만들 수 있는 것만 (예: 인용 검증기 붙은 논문 노트) |
| **리서치 + 회사일** | 탐색·설계·리뷰 | **주 무대.** 실험·구현·벤치는 검증기가 자연스럽다 |
| **개인 잡무** | **주 무대.** 문서·슬라이드·주간보고·메일 초안 | ⛔ 원칙적 배제 — §5 trifecta 참조 |

> [!note] 모드를 가르는 기준은 도메인이 아니라 두 가지다
> ① 검증기를 붙일 수 있는가 (없으면 무인 불가 — v0 접수 게이트 그대로)
> ② lethal trifecta 세 요소가 겹치는가 (겹치면 사람이 있어야 한다)

---

## 2. 모드 A — 대화형 daily driver

새로 만들 것이 의외로 적다. 런타임은 Claude Code, 부기 보호는 기존 훅이
`.harness/` 있는 repo에서만 켜지므로 일반 repo에서는 무해하다. 필요한 것:

- [x] **배송 결정** (2026-08-29): agent-athena를 전역 플러그인으로 설치하는 것을 정본으로 한다.
      러너의 `--plugin-dir` 주입과 이중 발화하므로 **러너는 전역 설치 감지 시 `--plugin-dir`를 생략**
      (또는 계속 주입하되 훅 카나리아로 확인 — 하네스 리뷰 H1과 같은 건).
- [ ] **스킬 팔레트**: §3의 이식 스킬 + 자작. 대화형에서는 사용자 호출(`disable-model-invocation`)도 허용 —
      v0의 "2키 제한"은 **무인 러너용 스킬에만** 적용한다 (사람이 슬래시를 칠 수 있으니 제한 근거가 없다).
- [ ] **대화형 훅 완화 확인**: pre-tool은 이미 대화형에서 부기 파일·commit/push만 막는다 — 유지.
      단 대상 repo에서 사람이 커밋을 시켰을 때 거부되는 동작이 의도인지 재확인 (하네스 리뷰 S2).

---

## 3. 스킬 이식 트랙 ← v1의 핵심 추가

### 근거

- 큐레이션된(사람이 쓴) 스킬은 실측 +16.6%p (SkillsBench). **자작 금지 조항과 충돌하지 않는다** —
  금지된 것은 "에이전트 자가 생성"이고, 이식은 정확히 그 반대다.
- 보안: 레지스트리는 무심사(조사에서 26.1% 결함) → **읽고 vendoring한 것만, 자동 업데이트 금지** (v0 정책 유지).

### 이식 파이프라인 (스킬 하나당)

1. **고정**: 소스 repo를 특정 커밋으로 클론
2. **감사**: 모든 파일을 읽는다 — 지시문에 숨은 네트워크·유출 경로 (semantic supply-chain)
3. **복사**: `skills/vendor/<이름>/` + `VENDORED.md`에 한 줄 (소스 · 커밋 · 라이선스 · 감사일 · 수정 내역)
4. **적응**: 아래 적응 규칙
5. **trifecta 재검사** (I7 — 스킬 추가는 공격면 추가다)
6. 갱신은 수동 재감사로만

### 적응 규칙 (클론 실측에서 확인된 것)

| 소스 특성 | 처리 |
|---|---|
| mattpocock: `Skill tool` 호출·슬래시 상호참조 (Claude Code 종속) | 대화형 전용으로 표시. 무인 러너 프롬프트에서 참조 금지 |
| mattpocock: 이슈 트래커 CLI 가정 (gh/linear) | `CONTEXT.md`의 Issue tracker 설정으로 갈음하거나 해당 부분 제거 |
| superpowers: 자체 SessionStart 훅 | **훅은 이식하지 않는다** — 스킬만. 우리 훅과 이중 발화 |
| 이름 충돌 (양쪽에 tdd·code-review 계열) | 한 소스만 채택, `VENDORED.md`에 탈락 사유 |

### 이식 목록 — 확정 (2026-08-28)

전수 조사(10 repo, ~135종)와 티어링은 **3부의 "최종 티어 — 두 트랙"**이 정본이다.
결정: **트랙 A·B의 Tier 1+2 전량 채택** — vendor 26 + 공식 설치 4(anthropic 문서 4종, PROPRIETARY라 복사 금지).
실행 절차·소스 경로·고정 커밋·적응 사항은 **1부**에 있다.

미클론이던 anthropics/skills는 클론·확인 완료 — 문서 4종(docx·xlsx·pptx·pdf)은 실재하며
라이선스가 스킬 단위로 갈린다(문서 4종 PROPRIETARY / frontend-design 등 Apache-2.0).

### 자작 스킬 후보 (이식이 아니라 직접 쓸 것 — writing-for-agents+skill-creator vendor 후)

**자작 2호 `diagram`** (모델 호출형, 모드 A·B 겸용) — 초안:

```yaml
name: diagram
description: 구조·흐름·상태가 3개 이상 엮인 설명을 할 때, 산문보다 먼저 mermaid 다이어그램으로
  제시한다. 아키텍처 설명, 실행 흐름, 상태 전이, 데이터 관계를 다룰 때 사용.
```

본문 규칙 (핵심 4줄):
1. 형식 선택은 내용이 정한다 — 관계·의존 → `flowchart` · 시간 순서·호출 → `sequenceDiagram` ·
   상태 전이 → `stateDiagram` · 데이터 모델 → `erDiagram`
2. 노드 12개를 넘으면 다이어그램을 쪼갠다 (하나에 다 넣지 않는다)
3. 다이어그램은 주장이다 — 코드·로그에서 확인한 사실만 그린다. 바라는 구조를 그리지 않는다
4. 렌더 대상은 Obsidian·GitHub (mermaid 네이티브) — 이미지 파일을 만들지 않는다

배경: 그래프 시각화 트렌드 조사(2026-08-28) 결론 — **생성은 위임, 사람 몫은 읽기·요청 어휘·검증뿐.**
같은 이유로 SUMMARY의 계획 DAG(G2)는 모델이 아니라 **러너가 결정론적으로 렌더**한다.

> [!warning] 이식하지 않는 것
> `find-skills`·`setup-*` 류 메타 스킬 (레지스트리 인프라 — 우리는 vendoring이라 불필요),
> superpowers의 `subagent-driven-development`·`dispatching-parallel-agents` (쓰기 병렬 —
> v0 금지 조항과 충돌, `.out-of-scope/parallel-writes.md`에 이미 있음).

---

## 4. 도메인별 채움

### 개인 AI 공부
- 이식: `teach` · `research` · `grilling`
- 자작 후보: 논문 노트 파이프라인 (기존 kvsnoop `verify_citations.py`가 검증기 원형 —
  인용 검증기가 붙으면 **공부도 모드 B에 넣을 수 있다**)
- 빈 곳: 복습·간격 반복 같은 학습 루프 — 필요해지면 그때 (`.out-of-scope` 후보)

### 리서치 + 회사일
- 모드 B가 주 무대 (v0 그대로). 이식: `grilling`·`writing-plans`·`systematic-debugging`
- 회사 repo에 붙일 때: `.harness/` 계약 5개 + **회사 데이터는 trifecta 검사 강화** (§5)

### 개인 잡무
- **기존 41개 스킬 목록이 코드가 아니라 요구사항 카탈로그다.** 폐기 대상은 구현이지 목록이 아니다:
  - [ ] slack-weekly-digest → 주간 다이제스트 (Slack MCP)
  - [ ] weekly-report → 주간보고 (Jira 커밋 수집)
  - [ ] slide-system / slides → 슬라이드 생성
  - [ ] google-workspace-api → 메일·캘린더 (기존 `get_gtoken` 방식 재사용)
  - [ ] next-work → 다음 작업 추천
- 이식: anthropics 문서 스킬(확인 후) · `to-spec`
- **전부 모드 A 전용.** 이유는 §5.

---

## 5. 안전 — 모드별 I7 차등

v0의 I7(trifecta 금지)은 유지하되, **모드가 완화 조건이다**:

| | 모드 A (사람 있음) | 모드 B (무인) |
|---|---|---|
| 네트워크·MCP | 허용 (사람이 승인 루프에 있다) | 차단 (현행 pre-tool + disallowedTools) |
| 비공개 데이터 (메일·Slack·회사 문서) | 허용하되 **외부 전송 전 사람 확인** | ⛔ 접근 자체를 계약에 안 넣는다 |
| 판단 근거 | Claude Code auto-mode와 동일 원리 — 승인 루프의 사람이 세 번째 요소를 끊는다 | 세 요소를 끊을 사람이 없다 |

> [!danger] 잡무를 무인으로 돌리고 싶어질 것이다
> "자는 동안 메일함 정리"가 정확히 trifecta 완성형이다(비공개 데이터 + 신뢰불가 콘텐츠 + 네트워크).
> 하고 싶어지면 `.out-of-scope/unattended-chores.md`를 먼저 쓴다 — 탈출구는
> "읽기 전용 수집 + 아침에 사람이 발송"으로 쪼개는 것.

---

## 6. 빌드 순서 개정

v0 Phase 3~6과 병합한 단일 트랙. **하네스 리뷰의 H1(훅 카나리아)·M1(비용 상한)이 최우선.**

- [x] **Phase A-0** 하네스 안전 마감: 훅 생존 카나리아 + domain.json 비용 기본값 *(하네스 리뷰 H1·M1)* — 2026-08-28 완료.
      카나리아 = session-start가 `HARNESS_CANARY` 파일을 쓰고 드라이버가 첫 assistant 이벤트에서 확인, 없으면 즉시 중단(`hooks_dead`, 시도 미산입, 밤 종료).
      비용 = 기본값 시도당 $5(`driver.max_budget_usd`) · 밤 $20(`budget.max_night_usd`, 러너 집행) · 5시간 창 사용률 0.85(`budget.rate_limit_stop`, 판정 후 중단). 해제는 명시적 null.
- [x] **Phase A-1** 스킬 이식 (2026-08-28 완료, 26종·커밋 26개) — **전수 감사는 08-28 선행 완료(**4부(vendoring 사전 감사)**: 26종 전원 적재·적응 diff 포함), 남은 것은 기계적 실행**: Tier 1+2 전량 (1부 절차) — 순서: B-Tier1 → 문서 4종 설치 → A-Tier1 → Tier 2
- [x] **Phase A-2** 배송 결정 실행: 전역 플러그인 설치 + 러너 이중 발화 해소 — 2026-08-29 완료 (실측: 이중 발화 없음, CONTEXT 해소 기록)
- [~] **Phase A-3** 도메인 가동 검증: 기동 스모크 27/27 (2026-08-29, `docs/skills-smoke-2026-08-29.md`) · 실사용 1회씩은 사용자 몫 (안 쓰이는 스킬은 여기서 드러난다 → H2 폐기 후보)
- [~] **Phase A-4** 자작 2호 `diagram` 완료(2026-08-29, `skills/diagram/`) · 자작 1호 주간보고/슬라이드는 Jira·Slack 자격증명 결정 뒤
- [~] **Phase B-3** (구 v0 Phase 3) 자동 분해 P7 — 2026-08-29 **P7-lite**(제안→현재-실패 필터→채택, `plan.auto_*` 옵션) 완료. 사양 자체를 리프로 완전 분해하는 것은 계속 열림
- [ ] **Phase B-6** Codex 이식 — 최후순위 유지 (2026-08-29: `codex` CLI 미설치 — 설치 후 드라이버 착수)

## 7. 미결정

| 항목 | 상태 |
|---|---|
| 메모리·노트 층 | 파일 기반으로 시작(연구 합의). Obsidian 볼트와 잇는 방법은 실사용 후 |
| 잡무의 정확한 범위 | §4 카탈로그를 가정으로 시작 — 빠진 게 있으면 추가 |
| anthropics/skills 실내용 | 클론 후 확정 (§3 이식 목록의 ⚠ 항목) |
| 회사일과 개인 시스템의 경계 | 회사 repo에서 모드 B를 돌리기 전에 한 번 결정 필요 |


---

# 3부 — 스킬 카탈로그 (기능별 전수판)

> [!abstract] 이 문서가 무엇인가
> star-history 주간 top 10 + skills.sh top 15 + mattpocock/skills를 **전부 클론해 SKILL.md 전수 조사**(10 repo, ~135종)한 뒤,
> **비슷한 일을 하는 스킬끼리 묶은** 카탈로그. 같은 그룹 안에서 경쟁자끼리 비교하고 하나를 고르면 된다.
> **최종 선택은 사용자가 한다** — 평결은 추천이지 결정이 아니다.
>
> 평결: ✅ 추천 · 🔶 후보 · ⏸ 보류(라이선스/검토) · ❌ 제외(사유)
> 조사 깊이: census는 전수, 본문 정독은 ✅/🔶 위주 — vendoring 확정 전 전수 정독 필요 (2부 §3 파이프라인 2단계).

## 출처 약어와 고정 커밋

| 약어 | repo | commit | 라이선스 |
|---|---|---|---|
| **mp** | mattpocock/skills | `6654f6b60cd9` | MIT |
| **sp** | obra/superpowers | `b36e0829c6d0` | MIT |
| **ant** | anthropics/skills | `3b3fad96af16` | **스킬별 상이** (Apache / PROPRIETARY) |
| **pt** | DietrichGebert/ponytail | `2ed6c52c9d7e` | MIT |
| **ds** | deepseek-harness `.agents/skills` | `cd5ef8148158` (08-28 감사 고정) | MIT |
| **da** | langchain-ai/deepagents | `457ac435e121` (08-28 감사 고정) | MIT |
| **vc** | vercel-labs/agent-skills | `20e89cc4bb25` | **LICENSE 없음** |
| **ab** | vercel-labs/agent-browser | `fbd046c23a2c` | Apache-2.0 |

집에서: `git clone <url> && git checkout <commit>`. 갱신은 수동 재감사로만.

> [!warning] 라이선스 교훈 둘
> ① **ant는 한 repo 안에서 스킬별로 라이선스가 다르다** — docx/xlsx/pptx/pdf는 PROPRIETARY
> ("Services 밖 추출·보관·파생물 금지")라 vendoring 불가. 나머지 대부분 Apache-2.0.
> ② **vc는 LICENSE 파일이 없다** — 전부 보류.

---

## A. 요구사항 정렬·발산 — 코딩 전에 생각을 다듬는다

| 스킬 | 출처 | 줄 | 한 줄 | 평결 |
|---|---|---|---|---|
| grilling | mp | 28 | 계획·결정을 design tree로 집요하게 인터뷰 (설치 56만) | ✅ 리서치·공부 |
| brainstorming | sp | 250 | 창작·기능 작업 전 필수 발산 | ✅ 모드 A |
| grill-me | mp | 7 | "Call grilling" 별칭 (설치 99만이지만 별칭) | ❌ grilling만 있으면 됨 |
| grill-with-docs | mp | 7 | grilling + ADR·용어집 생성 별칭 (설치 84만) | 🔶 이식 후 1줄 자작으로 재현 |
| loop-me | mp | 32 | 만들려는 워크플로 사양을 grilling (in-progress) | 🔶 |
| to-questionnaire | mp | 54 | 답 못 하는 결정을 타인용 설문으로 | 🔶 회사 협업 |

> grilling과 brainstorming은 **경쟁이 아니라 단계가 다르다** — brainstorming(발산) → grilling(수렴). 둘 다 가능.

## B. 계획·분해·사양화 — 우리 P7의 이웃

| 스킬 | 출처 | 줄 | 한 줄 | 평결 |
|---|---|---|---|---|
| writing-plans | sp | 171 | 사양 → 다단계 계획, 코드 만지기 전 | ✅ **P7 프롬프트 원료 1순위** |
| to-spec | mp | 75 | 대화 → 사양 문서 발행 | ✅ 잡무·리서치 |
| to-tickets | mp | 105 | 계획 → 의존 관계 선언된 티켓 분해 | 🔶 **plan.json 생성기로 개조 후보** (P7 원료 2순위) |
| executing-plans | sp | 64 | 계획을 리뷰 체크포인트와 함께 실행 | 🔶 writing-plans 짝 |
| wayfinder | mp | 128 | 세션 하나에 안 담기는 큰 작업을 결정 티켓 지도로 | 🔶 우리 계획 계층과 겹침 — 아이디어만 |
| implement / implement-spec | mp | 15·35 | 구현 위임 별칭 | ❌ 구성 스킬만 있으면 불필요 |

## C. 구현 규율 — TDD·격리·충돌

| 스킬 | 출처 | 줄 | 한 줄 | 평결 |
|---|---|---|---|---|
| test-driven-development | sp | 320 | 구현 전 TDD 강제 | ✅ |
| tdd | mp | 38 | red-green-refactor 참조 (설치 78만) | ❌ **sp TDD와 중복 — sp 채택** (모델 호출형, 더 깊음) |
| using-git-worktrees | sp | 167 | 격리 작업의 worktree 규율 | ✅ 기존 clone-workflow 대체 |
| resolving-merge-conflicts | mp | 14 | merge/rebase 충돌 해소 | 🔶 작고 무해 |
| prototype | mp | 26 | 설계 질문에 답하는 일회용 프로토타입 | 🔶 |

## D. 디버깅 — 하나만 고른다

| 스킬 | 출처 | 줄 | 한 줄 | 평결 |
|---|---|---|---|---|
| systematic-debugging | sp | 283 | 수정 제안 전 체계적 진단 (버그·테스트 실패·이상 동작) | ✅ **채택 추천** |
| diagnosing-bugs | mp | 138 | 어려운 버그·성능 회귀의 진단 루프 | ❌ 위와 중복 — 더 구조적인 sp 채택 |

## E. 리뷰·안티슬롭 — 용도가 갈려서 병존 가능

| 스킬 | 출처 | 줄 | 한 줄 | 평결 |
|---|---|---|---|---|
| ponytail-review | pt | 52 | diff 과잉 설계를 한 줄 지적 (delete/stdlib/native/yagni/shrink) | ✅ **모드 B 재시도 전 doom loop 완화 기대** |
| code-review | mp | 87 | 고정점 이후 변경을 Standards+Spec 2축 리뷰 | 🔶 ponytail과 성격 다름(포괄 vs 삭제 지향) — 병존 가능 |
| requesting-code-review | sp | 95 | 완료·병합 전 리뷰 요청 의식 | 🔶 |
| receiving-code-review | sp | 205 | 리뷰 피드백을 구현 전 검증 | 🔶 회사일 — 기존 resolve 워크플로 대체 후보 |
| dsh-find-simplifications | ds | 146 | 비자명한 단순화 후보 발굴 + 노트 축적 | 🔶 ponytail-audit과 겹침(접근 다름) |
| ponytail-audit | pt | — | repo 전체 과잉 설계 랭킹 | 🔶 H2(폐기 리듬) 도구 |
| ponytail / ponytail-debt | pt | — | 게으른 시니어 전역 모드 / 미룬 것 장부 | 🔶 review만으로 충분할 수도 |
| web-design-guidelines | vc | 39 | UI 코드의 웹 인터페이스 지침 준수 리뷰 (설치 58만) | ⏸ 라이선스 |
| ponytail-gain / ponytail-help | pt | — | 성과 스코어보드 / 도움말 | ❌ 계측·인프라 |

## F. 완료·통합·git 안전 — 우리 하네스와 가장 많이 겹치는 그룹

| 스킬 | 출처 | 줄 | 한 줄 | 평결 |
|---|---|---|---|---|
| verification-before-completion | sp | 120 | 완료 주장 전 검증 실행 강제 | ✅ **C1 대응. v0 자작 후보였던 것 — 이식으로 대체** |
| finishing-a-development-branch | sp | 225 | 완료 후 통합 방식 결정 | 🔶 |
| dsh-pre-push-checks | ds | 123 | push·리뷰 요청 전 검사 의식 | 🔶 preflight 아이디어 원천 |
| dsh-merging-stacked-prs | ds | 127 | 의존 PR 스택 병합 | 🔶 회사일에 스택 PR 쓰면 |
| git-guardrails-claude-code | mp | 95 | 위험 git 명령 차단 훅 설치 | ❌ **우리 pre-tool이 이미 함** |
| setup-pre-commit | mp | 91 | Husky pre-commit 설정 | ❌ TS 생태계 특화 |

## G. 공부·리서치 — 도메인 직격

| 스킬 | 출처 | 줄 | 한 줄 | 평결 |
|---|---|---|---|---|
| teach | mp | 140 | 다세션 학습 상태 유지하며 가르침 (설치 54만) | ✅ **공부 핵심** |
| research | mp | 12 | 1차 소스 조사 → md 저장 (백그라운드 위임) | ✅ |
| arxiv-search | da | 33 | arXiv 검색·초록·주제 필터 | ✅ 작고 직격 — **모드 A 전용** (네트워크=I7, 무인에서 발화 불가) |
| web-research | da | 77 | 다중 소스 → 서브에이전트 → 인용 리포트 | 🔶 모드 A 전용(네트워크) |
| academy-guide | ant | 147 | Anthropic 교육 과정 안내 | ❌ 남의 커리큘럼 |

## H. 문서·산문 — 잡무의 절반

| 스킬 | 출처 | 줄 | 한 줄 | 평결 |
|---|---|---|---|---|
| docx / xlsx / pptx / pdf | ant | 91~314 | Word/Excel/PPT/PDF 조작 (스크립트 동반) | ⏸ **PROPRIETARY — vendor 금지, 공식 채널 설치.** 주간보고·슬라이드는 이걸로 충족 |
| dsh-trim-cot-leakage | ds | 45 | 추론 전사처럼 새는 산문(죽은 결정 인용) 탐지·수정 | ✅ **뜻밖의 수확 — SUMMARY·문서 품질 직결. 범용화 쉬움** |
| doc-coauthoring | ant | 375 | 문서 공저 워크플로 (컨텍스트→반복→검증) | ⏸ LICENSE 없음 — 확인 후 |
| writing-guidelines | vc | 39 | 산문 스타일 리뷰 | ⏸ 라이선스 |
| writing-beats / fragments / shape | mp | 67~79 | 글쓰기 3부작 (탐색→구조→성형, in-progress) | 🔶 블로그 쓰면 |
| dsh-doc-standards / dsh-prose-standard | ds | 56·81 | dsh repo 문서·산문 규범 | ❌ 남의 규범 — **"repo 규범을 스킬로" 패턴만 배울 것** |
| internal-comms | ant | 32 | Anthropic 사내 커뮤니케이션 형식 | ❌ 남의 회사 형식 — 자작 보고 스킬의 본보기로만 |

## I. 디자인·시각 산출물

| 스킬 | 출처 | 줄 | 한 줄 | 평결 |
|---|---|---|---|---|
| frontend-design | ant | 55 | 템플릿 냄새 없는 UI 설계 지침 (설치 83만) | ✅ 회사 프론트 |
| theme-factory | ant | 59 | 산출물 테마 10종 | 🔶 기존 theme-setup 대체 후보 |
| canvas-design | ant | 129 | 디자인 철학 기반 png/pdf | 🔶 |
| web-artifacts-builder | ant | 73 | React+Tailwind 복합 아티팩트 | 🔶 |
| record-browser-gif | ds | 110 | 브라우저 데모 GIF 녹화 | 🔶 문서·보고 장식 |
| algorithmic-art / brand-guidelines / slack-gif-creator | ant | — | p5.js 예술 / **Anthropic 브랜드** / Slack GIF | ❌ |

## J. 웹 자동화·앱 테스트 — 도구 동반, trifecta 주의

| 스킬 | 출처 | 줄 | 한 줄 | 평결 |
|---|---|---|---|---|
| webapp-testing | ant | 95 | Playwright로 로컬 웹앱 검증·스크린샷·로그 | ✅ **모드 B evaluator 원료** |
| dogfood | ab | 220 | 웹앱 체계적 탐색·버그 발견 | 🔶 로컬 한정으로 |
| core / agent-browser | ab | 519·52 | snapshot-and-ref 브라우저 자동화 CLI | ⏸ webapp-testing으로 충분한지 먼저 |
| slack | ab | 285 | Slack 브라우저 조작 | ⏸ **Slack MCP와 중복** |
| electron / agentcore / vercel-sandbox / protected-vercel | ab | — | 특수 환경 | ❌ 당장 불요 |
| derive-client | ab | 86 | HAR 녹화 → 내부 API 역공학 | ❌ 회사 환경 오남용 위험 — `.out-of-scope` 후보 |

## K. 세션 연속성·기억 — 미결정 '메모리 층'의 이웃

| 스킬 | 출처 | 줄 | 한 줄 | 평결 |
|---|---|---|---|---|
| handoff | mp | 16 | 대화를 인수인계 문서로 압축 | ✅ 저장 위치를 `.harness/sessions/`로 적응 |
| remember | da | 118 | 대화에서 지식 추출·저장 (내장 메모리 스킬) | 🔶 **메모리 층 참고 구현 — 채택 아니어도 정독** |
| retro | mp | 44 | 코딩 세션 회고 (in-progress) | 🔶 회고 → findings 초안 흐름 가능 |
| dsh-archive-agent-notes | ds | 68 | Agent Notes 추가·감사·보관 | ❌ dsh 전용 — 노트 수명주기 패턴만 참고 |
| claude-handoff | mp | 18 | 백그라운드 에이전트로 즉시 인계 | ❌ handoff로 충분 |
| deepagents-thread-inspector | da | 50 | Deep Agents 세션 DB 검사 | ❌ 타 런타임 전용 |

## L. 어휘·아키텍처 — CONTEXT.md 규약의 이웃

| 스킬 | 출처 | 줄 | 한 줄 | 평결 |
|---|---|---|---|---|
| domain-modeling | mp | 74 | CONTEXT.md 작성·용어 다듬기 | ✅ **우리 규약과 직결** |
| wait-what | mp | 7 | 설명 재요청 (STE100 + CONTEXT.md 어휘) | ✅ 작고 맞물림 |
| codebase-design | mp | 114 | deep module 설계 어휘 | 🔶 공부 겸용 |
| improve-codebase-architecture | mp | 71 | 심화 기회 스캔 → HTML 리포트 → grilling (설치 81만) | 🔶 회사 repo 점검, 대화형 전용 |

## M. 메타 — 스킬을 만들고 다듬는 스킬 (3중복 정리 필요)

| 스킬 | 출처 | 줄 | 한 줄 | 평결 |
|---|---|---|---|---|
| skill-creator | ant | 485 | 스킬 생성·개선·**eval·트리거 최적화** | ✅ 도구로 채택 |
| writing-for-agents | mp | 81 | 스킬·AGENTS.md 작성 규범 | ✅ 규범으로 채택 (병용) |
| writing-skills | sp | 679 | 스킬 작성·검증 방법론 (대작) | ❌ 위 둘로 충분 |
| skill-creator | da | — | 동명 비교용 | ❌ ant 채택 |
| wizard | mp | 44 | 사람만 할 수 있는 단계의 bash 마법사 생성 | 🔶 잡무(프로비저닝) |
| mcp-builder | ant | 236 | MCP 서버 제작 가이드 | 🔶 잡무 통합 만들 때 |
| find-skills / ask-matt / setup-matt-pocock-skills / using-superpowers | vc·mp·sp | — | 레지스트리·라우터·설정·상주 강제 | ❌ 인프라 (using-superpowers는 점진 공개 철학과 충돌) |

## N. 병렬 — 전원 제외 (v0 금지 조항)

| 스킬 | 출처 | 줄 | 평결 |
|---|---|---|---|
| subagent-driven-development | sp | 568 | ❌ 쓰기 병렬 |
| dispatching-parallel-agents | sp | 167 | ❌ 동상. 단 **읽기 부분은 G3 참고자료** |

## 일괄 제외 (조사했으나 표에 안 올린 것)

- **da 예제 15종** (blog-post, social-media, cudf, text-to-sql, competitor-analysis…) — 예제 에이전트 동봉물
- **ds 나머지** (dsh-code-review, dsh-doc-site-sync, dsh-translate-docs) — dsh repo 전용
- **mp misc** (migrate-to-shoehorn, scaffold-exercises, setup-ts-deep-modules) — TS 강좌·도구 특화
- **azure-skills 79종** — Azure 미사용 (미조사)
- **lark-doc / lark-vc-agent** (skills.sh 10·12위) — Feishu 미사용
- **claude-api / discernment-nudge** (ant) — 이미 내장/불요
- **pi 17종** — 전부 테스트 픽스처. **openai/codex·orca·OmniRoute** — 런타임/제품, 스킬 없음
- **free-claude-code** (star-history 9위) — "무료 토큰" 프록시, **공급망 관점 접근 금지**

---

## 최종 티어 — 두 트랙

소비자 축으로 가른다. **트랙 A = 내가 대화형에서 쓰는 것** · **트랙 B = 완전위임(무인 밤샘)에서 에이전트가 쓰는 것**.
티어 의미: **1 = 무조건 가져옴 · 2 = 고민해봄 · 3 = 더 고민**. (아예 안 가져올 것은 티어 밖 — 각 그룹 표의 ❌와 아래 "티어 밖" 참조.)

> [!important] 2026-08-28 결정: **Tier 2 전량 채택.** 실행은 1부. Tier 3만 미결로 남는다.

> [!note] 로딩 메커니즘 — 분리 배포는 필요 없다
> 플러그인 하나에 다 실려도: USER 호출형은 B에서 아무도 슬래시를 안 치므로 자연 비활성(상주 ~100토큰/개),
> 네트워크 스킬은 pre-tool 훅이 B에서 차단(이중 방어). 구분의 실익은 배포가 아니라
> **감사 우선순위와 장애 시 의심 순서**다 — 밤샘이 이상하면 B-Tier1 3종부터 본다.

### 트랙 A — 내가 쓸 때 (대화형)

| 티어 | 스킬 | 근거 |
|---|---|---|
| **1 무조건** | `grilling` (mp) + `brainstorming` (sp) | 발산→수렴, 단계가 달라 둘 다 |
| **1** | `teach` (mp) · `arxiv-search` (da) | 공부 도메인 코어. arxiv는 A 전용(네트워크) |
| **1** | `handoff` (mp) | 집↔회사 이동이 워크플로 상수 |
| **1** | `writing-plans` (sp) | P7 전까지 plan.json은 내가 쓴다 — 그 품질을 이게 정함 |
| **1** | `domain-modeling` (mp) | CONTEXT.md 규약 직결, 74줄 |
| **1** | `docx` `xlsx` `pptx` `pdf` (ant) | 잡무 절반. ⚠ vendor 금지 — **공식 플러그인 설치** |
| **2 고민** | `research` (mp) · `to-spec` (mp) · `wait-what` (mp) | 싸고 무해 — arxiv/대화로 부족해지면 |
| **2** | `writing-for-agents` (mp) + `skill-creator` (ant) | **잡무 자작 스킬 쓰는 날 Tier 1로 승격** |
| **2** | `frontend-design` (ant) · `improve-codebase-architecture` (mp) | 회사 프론트·repo 점검 재개 시 |
| **2** | `code-review` (mp) · `receiving-code-review` (sp) | 회사 PR 워크플로 대체 검토 시 |
| **2** | `using-git-worktrees` (sp) · `executing-plans` (sp) · `retro` (mp) | 병행 작업·계획 실행·회고 |
| **3 더 고민** | `to-questionnaire` (mp) · `wizard` (mp) · `theme-factory` (ant) · `canvas-design` (ant) · `web-artifacts-builder` (ant) · `record-browser-gif` (ds) · `codebase-design` (mp) · writing 3부작 (mp) | 특정 상황용 — 그 상황이 오면 |
| **3** | `web-research` (da) · `mcp-builder` (ant) · `agent-browser` core/dogfood (ab) | 도구·통합 동반 — 필요가 구체화되면 |
| **3** | `doc-coauthoring` (ant) · vc 전체 | ⚠ 라이선스 미해결 — 해결되면 2로 |

### 트랙 B — 완전위임 시 (무인 모드 B)

| 티어 | 스킬 | 근거 |
|---|---|---|
| **1 무조건** | `verification-before-completion` (sp) | C1(자기 검증 생략) = 실측 1위 실패 모드 |
| **1** | `systematic-debugging` (sp) | 재시도 품질 — 같은 접근 반복을 끊는 절차 |
| **1** | `ponytail-review` (pt) | 안티슬롭 + doom loop 완화, 52줄 |
| **2 고민** | `test-driven-development` (sp) | 코딩 리프 품질. 러너 verify-first가 결과는 이미 강제 |
| **2** | `webapp-testing` (ant) | evaluator 원료 (localhost = I7 통과) |
| **2** | `dsh-trim-cot-leakage` (ds) | SUMMARY·산문 후처리 — 범용화 개조 필요 |
| **2** | `writing-plans` (sp) · `to-tickets` (mp) | **P7 자동화 시 하네스 소비로 승격** (그 전까지는 A 트랙) |
| **3 더 고민** | `ponytail` 전역 모드 (pt) | B 전체 성격을 바꿈 — review만으로 충분한지 먼저 |
| **3** | `resolving-merge-conflicts` (mp) | B에서 충돌은 드묾(러너가 되돌림) |
| **3** | `finishing-a-development-branch` (sp) | 아침 병합은 사람 몫이 원칙 |
| **3** | `dsh-find-simplifications` (ds) · `ponytail-audit` (pt) | 야간 audit 작업 유형이 생기면 |
| **3** | `remember` (da) | 메모리 층 설계 후에 — 지금은 정독만 |

### 티어 밖 (안 가져옴 — 사유는 각 그룹 표)

별칭(grill-me·grill-with-docs·implement류) · 중복 패자(mp tdd·mp diagnosing-bugs·sp writing-skills·da skill-creator) ·
pre-tool이 대체(git-guardrails·setup-pre-commit) · 쓰기 병렬(subagent-driven·dispatching-parallel) ·
상주 강제(using-superpowers) · 남의 규범(brand·internal-comms·academy·dsh repo 규범) ·
리스크(derive-client·free-claude-code·ab slack) · 불요(algorithmic-art·slack-gif·lark·azure·레지스트리 인프라)

### 첫날 작업량

**A-Tier1 vendor 7종 + 공식 설치 4종, B-Tier1 vendor 3종 = vendor 10 + 설치 4.**
각 vendor는 전수 정독 감사 대상 — 하루 분량. Tier 2는 트리거가 올 때 하나씩 (미리 당기면 감사 비용만 쌓인다).

## 그래프 → 하네스 이식

agent-athena 대조 결과 **그래프 런타임의 요체는 이미 구현돼 있다**: `plan.json` `depends_on`+순환검사 = DAG,
log fold = 이벤트 소싱 체크포인트, `resolve_base`+dangling 닫기 = 재개, 리프 타임아웃·인프라 분리 = 노드 격리.
이식할 것은 런타임이 아니라:

- [ ] **G1 어휘**: deepseek turn/step + 이벤트 3분류(Session/Agent/Capability) — 새 이벤트·훅 추가 시 첫 질문
- [ ] **G2 SUMMARY에 계획 DAG를 mermaid로** — 막힌 작업이 무엇을 물고 있는지 아침에 그림으로 (findings/003 연장).
  **확정(2026-08-28)**: Langfuse 방식 2모드 — aggregated(계획 DAG+상태 배지) 먼저, expanded(log 언롤)는 다음.
  렌더는 모델이 아니라 **러너가 plan.json+log에서 결정론적으로** (부기는 프로그램)
- [ ] **G3 읽기 팬아웃은 모델 층에서** — 러너 병렬 없음(E2). 리프 안 Task 위임 허용을 프롬프트에 명시.
  참고: sp dispatching-parallel-agents의 읽기 부분

## 집에서의 실행 순서 (Phase A-1)

1. 고정 커밋 재클론 → 선택한 것 **전수 정독 감사** → `skills/vendor/` + VENDORED.md(소스·커밋·라이선스·감사일·수정) → 적응 → I7 재검사
2. PROPRIETARY 4종은 공식 채널 설치로 별도 처리
3. **두 트랙 Tier 1부터** (vendor 10 + 설치 4) — 순서 추천: B-Tier1 3종(밤샘 품질) → A의 문서 4종 설치(잡무 즉효) → A 나머지 7종

---

# 4부 — vendoring 사전 감사: Tier 1+2 전수 정독 결과

> [!abstract] 이 문서가 무엇인가
> 팩 1부(vendoring 작업 지시)의 **감사 단계를 회사 세션에서 선행한 결과물.**
> vendor 대상 26종의 모든 파일(12,672줄)을 고정 커밋에서 정독했고, 판정·소견·적응 diff·VENDORED.md 행을 여기 적었다.
> **고정 커밋이 같으므로 집에서 클론하면 바이트 단위로 같은 내용이 나온다** — 집 작업은 이 문서대로
> 클론 → 복사 → 적응 적용 → 커밋의 기계적 실행이면 된다. 재정독은 선택(스팟 체크 권장).
> 적응 diff는 이 문서가 정본이다. 팩 1부의 적응 열과 다르면(감사가 갱신한 곳) 이 문서가 우선.

## 감사 방법

- 소스 6개 repo를 고정 커밋으로 클론, 26종 스킬 디렉토리의 **전 파일 정독** (지시문·스크립트·에이전트 문서·예제).
- 예외 2건: `skill-creator`의 `eval-viewer/viewer.html`(1,325줄)·`assets/eval_review.html`(146줄)은
  UI 코드라 **외부 참조·통신 표면 전수 열거**(script src/href/fetch/WebSocket/eval 전부) + 구조 확인으로 감사.
  결과는 아래 항목에 기재.
- 스크리닝 정규식(네트워크·설치·유출·베이스64·웹훅 등)을 26종 전체에 돌려 정독과 교차 확인.

## 고정 커밋 (집에서 이대로 클론)

| 약어 | repo | commit | 라이선스 (확인함) |
|---|---|---|---|
| mp | mattpocock/skills | `6654f6b60cd9` | MIT |
| sp | obra/superpowers | `b36e0829c6d0` | MIT |
| ant | anthropics/skills | `3b3fad96af16` | 스킬별 — 아래 3종은 각 디렉토리 LICENSE.txt로 **Apache-2.0 확인** |
| pt | DietrichGebert/ponytail | `2ed6c52c9d7e` | MIT |
| **da** | langchain-ai/deepagents | **`457ac435e121`** ← 팩에 없던 고정, 2026-08-28 감사 시점 HEAD | MIT |
| **ds** | deepseek-ai/deepseek-harness | **`cd5ef8148158`** ← 동일 | MIT |

```bash
W=$(mktemp -d)
git clone -q https://github.com/mattpocock/skills.git       $W/mp  && git -C $W/mp  checkout -q 6654f6b60cd9
git clone -q https://github.com/obra/superpowers.git        $W/sp  && git -C $W/sp  checkout -q b36e0829c6d0
git clone -q https://github.com/anthropics/skills.git       $W/ant && git -C $W/ant checkout -q 3b3fad96af16
git clone -q https://github.com/DietrichGebert/ponytail.git $W/pt  && git -C $W/pt  checkout -q 2ed6c52c9d7e
git clone -q https://github.com/langchain-ai/deepagents.git $W/da  && git -C $W/da  checkout -q 457ac435e121
git clone -q https://github.com/deepseek-ai/deepseek-harness.git $W/ds && git -C $W/ds checkout -q cd5ef8148158
```

## 종합 판정

**26종 전부 적재 가능. 보류 0.** 악성 지시·숨은 유출 경로·조건부 지시문은 한 건도 없었다.
다만 아래 **공통 사항 5가지**와 스킬별 적응(표의 "적응" 열)을 반영할 것.

### 공통 사항

1. **로딩 메커니즘 확인 필수** — 팩은 `skills/vendor/<이름>/`에 복사하라고 하지만, Claude Code 플러그인의
   스킬 스캔이 `skills/<이름>/SKILL.md` 한 단계만 본다면 vendor/ 중첩은 로드되지 않는다.
   `claude --plugin-dir .` 스모크에서 스킬 목록에 안 뜨면: 스킬 본체를 `skills/<이름>/`로 두고
   `skills/vendor/VENDORED.md`(대장)만 vendor/에 유지. **to-tickets의 "로드 제외"는 이 메커니즘을 역이용**
   (로드되는 위치 밖에 두기)하거나 SKILL.md를 `SKILL.md.hold`로 개명.
2. **frontmatter 2키 규칙은 vendored에 적용하지 않는다** — teach·handoff·wait-what 등은 `disable-model-invocation`,
   `argument-hint`를, ant 3종은 `license` 키를 갖는다. upstream 유지(수정 최소화 원칙). 현행 `scripts/check`는
   `skills/*/SKILL.md`만 스캔하므로 충돌 없음 — 스킬을 `skills/<이름>/`로 옮기게 되면 check의 2키 검사에
   vendor 예외를 추가해야 한다 (VENDORED.md에 있는 이름은 면제).
3. **mp 스킬들의 `agents/openai.yaml` 동봉 파일은 유지** — 무해한 인터페이스 메타데이터고 Codex 이식(B-6) 때 재료가 된다.
4. **네트워크 지시가 있는 스킬 = "모드 A 전용 — 네트워크(I7)" 첫 줄 표시 대상**: arxiv-search, research(팩 적응란에 없던
   감사 소견), web 계열 지시가 있는 improve-codebase-architecture(CDN)·receiving-code-review(gh api)·teach(자료 탐색).
   무인 러너에서는 pre-tool이 이중 방어하므로 표시는 감사 우선순위용.
5. **파이썬 문법 버전** — skill-creator 스크립트는 3.10+ 문법(`str | None`)을 쓴다. 하네스의 3.9 규칙은
   우리 코드용이므로 vendored 스크립트에는 적용하지 않되, 집 머신 python3가 3.10+인지 확인.
   quick_validate.py는 PyYAML 의존(없으면 `pip install pyyaml` — 부트스트랩/venv 몫).

---

## B-Tier1 (밤샘 품질 — 최우선 3종)

### 1. verification-before-completion (sp) — ✅ 적재, 적응 없음
- 1파일 120줄, MIT. 순수 규율 지시문(증거 없이 완료 주장 금지). 네트워크·스크립트 없음.
- frontmatter 2키. 우리 P6(검증기 판정)과 정합 — 모델 쪽 자기규율을 보강.
- VENDORED: `| verification-before-completion | obra/superpowers | b36e0829c6d0 | MIT | 2026-08-28 | 없음 |`

### 2. systematic-debugging (sp) — ✅ 적재, 적응 1건 (팩의 "없음"에서 갱신)
- 11파일 1,247줄, MIT. 4단계 디버깅 규율 + 보조기법 3편 + eval 픽스처 4편 + CREATION-LOG.
- `find-polluter.sh`는 bash+npm 가정(수동 실행용 참고 스크립트) — portable-lint 대상 아님, 그대로 둠.
- test-pressure-*.md는 가상 시나리오 픽스처 — 숨은 지시 없음, 스킬 검증 재료로 가치 있어 유지.
- **적응**: SKILL.md의 크로스 참조 2곳에서 `superpowers:` 접두어 제거 —
  `superpowers:test-driven-development` → `test-driven-development`,
  `superpowers:verification-before-completion` → `verification-before-completion`
  (우리 플러그인에서 그 네임스페이스는 해석 안 됨. 두 스킬 다 vendor하므로 평이름으로).
- VENDORED: `| systematic-debugging | obra/superpowers | b36e0829c6d0 | MIT | 2026-08-28 | superpowers: 접두어 2곳 제거 |`

### 3. ponytail-review (pt) — ✅ 적재, 적응 없음
- 1파일 57줄, MIT. 삭제 지향 리뷰 포맷(delete/stdlib/native/yagni/shrink) + 종료어("Lean already. Ship.").
- 스모크 테스트·assert 자기검증은 삭제 대상으로 찍지 말라는 경계 조항까지 안전. 네트워크 없음.
- VENDORED: `| ponytail-review | DietrichGebert/ponytail | 2ed6c52c9d7e | MIT | 2026-08-28 | 없음 |`

## 공식 설치 4종 (vendor 금지)

docx·xlsx·pptx·pdf — ant repo에서 실재 확인(감사 범위 밖, PROPRIETARY 라이선스 확인됨).
공식 플러그인/마켓플레이스로 설치. 절차는 집에서 `claude` 대화로 확인(마켓플레이스 명령은 버전에 따라 다름).

## A-Tier1 (대화형 7종)

### 4. grilling (mp) — ✅ 적재, 적응 없음
- 2파일 31줄(SKILL.md + openai.yaml), MIT. 프론티어 단위 라운드 인터뷰. 사실 조사는 서브에이전트에 위임(읽기 팬아웃 — G3 정합).
- VENDORED: `| grilling | mattpocock/skills | 6654f6b60cd9 | MIT | 2026-08-28 | 없음 |`

### 5. brainstorming (sp) — ✅ 적재 8파일 전체, 적응 1건 (팩의 "4파일" 가정은 구식 — 실제 8파일 2,030줄)
- MIT. SKILL.md(250줄, HARD-GATE 승인 게이트 + 3경로 분류)와 spec-document-reviewer-prompt.md는 클린.
- **visual companion 동봉 서버**(server.cjs 723줄 + start/stop-server.sh + helper.js + frame-template.html + visual-companion.md):
  전 파일 정독 결과 방어적 설계(기본 127.0.0.1 바인드, 세션 키 인증 + 타이밍세이프 비교, umask 077, PID 위생,
  워처 기반 로컬 서빙). node 필요(모드 A 도구 — 우리 환경 요건에 추가).
- **유일한 외부 통신**: 서버가 만든 페이지에 브랜드 로고 `https://primeradiant.com/...png`를 심음 —
  브라우저發 이미지 fetch = 사실상 사용 비콘. 단 `SUPERPOWERS_DISABLE_TELEMETRY`/`DISABLE_TELEMETRY`/
  `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` env를 존중해 끌 수 있게 되어 있음.
- **적응** (server.cjs 1줄): `const SUPERPOWERS_TELEMETRY_DISABLED = TELEMETRY_DISABLE_ENV_VARS.some(...)` →
  `const SUPERPOWERS_TELEMETRY_DISABLED = true;  // vendored: 외부 로고 fetch(사용 비콘) 제거` —
  env 상태와 무관하게 zero-egress 보장.
- SKILL.md의 `docs/superpowers/specs/` 저장 경로는 "(User preferences ... override)" 문구가 있어 유지.
  `elements-of-style:` 참조는 "if available" 조건부라 유지.
- 사소: visual-companion.md Design Tips가 목업에 Unsplash 실사진 사용을 권함(브라우저發 외부 fetch) — 모드 A 도구라 수용, 인지만.
- VENDORED: `| brainstorming | obra/superpowers | b36e0829c6d0 | MIT | 2026-08-28 | server.cjs 텔레메트리 상수 고정(외부 로고 fetch 제거) |`

### 6. teach (mp) — ✅ 적재, 적응 없음
- 6파일 289줄, MIT. 학습 워크스페이스(MISSION/RESOURCES/학습기록/GLOSSARY 포맷 4편 동봉). 클린.
- frontmatter에 `disable-model-invocation`+`argument-hint`(사용자 호출형) — 유지. 자료 탐색은 네트워크 함의 → 모드 A 전용 표시.
- VENDORED: `| teach | mattpocock/skills | 6654f6b60cd9 | MIT | 2026-08-28 | 첫 줄 모드 A 전용 표시 |`

### 7. arxiv-search (da) — ✅ 적재, 적응 3건 (팩 1건 + 감사 2건)
- 2파일 94줄, MIT. arxiv 패키지 기반 검색 CLI + 사용 지시.
- **감사에서 실제 결함 발견**: `arxiv_search.py`의 `main()`이 `query_arxiv(...)` 반환값을 **print하지 않는다** —
  CLI로 돌리면 출력이 항상 빈다. upstream 버그.
- **적응**: ① 본문 첫 줄에 "모드 A 전용 — 네트워크(I7)" (팩) ② `main()` 마지막 줄
  `query_arxiv(args.query, max_papers=args.max_papers)` → `print(query_arxiv(args.query, max_papers=args.max_papers))`
  ③ 사용 예의 `~/.deepagents/...` 경로 → vendor 경로로.
- VENDORED: `| arxiv-search | langchain-ai/deepagents | 457ac435e121 | MIT | 2026-08-28 | 모드A 표시 · main() print 버그 수정 · 경로 |`

### 8. handoff (mp) — ✅ 적재, 적응 1건 (팩대로)
- 2파일 21줄, MIT. 사용자 호출형(2키 + disable-model-invocation + argument-hint). 민감정보 redact 지시 내장.
- **적응**: "Save to the temporary directory of the user's OS - not the current workspace." →
  "Save to `.harness/sessions/` when the repo has one; otherwise the temporary directory of the user's OS — not tracked files."
- VENDORED: `| handoff | mattpocock/skills | 6654f6b60cd9 | MIT | 2026-08-28 | 저장 위치 .harness/sessions/ 우선 |`

### 9. writing-plans (sp) — ✅ 적재, 적응 3건 (팩 "없음"에서 갱신 — 병렬 쓰기 금지와 충돌)
- 2파일 220줄, MIT. 계획 작성 규율(bite-sized 단계, No Placeholders, 자기 리뷰) + 계획 리뷰어 프롬프트. 본체 클린.
- **문제**: 헤더 템플릿과 Execution Handoff 절이 `superpowers:subagent-driven-development`(우리 금지 — 쓰기 병렬)를
  권장 경로로 지정한다.
- **적응**: ① 헤더 템플릿의 "REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
  superpowers:executing-plans" → "REQUIRED SUB-SKILL: Use executing-plans" ② Execution Handoff 절의 두 옵션 제시 →
  executing-plans 단일 경로로 축약(옵션 1 문단 삭제) ③ `superpowers:using-git-worktrees` → `using-git-worktrees`.
- plan.json 계약과의 관계: 이 스킬의 산출물은 사람용 계획 md — plan.json(리프 5~30분·검증기 필수)의 원료 단계.
  모순 문장은 없었음.
- VENDORED: `| writing-plans | obra/superpowers | b36e0829c6d0 | MIT | 2026-08-28 | subagent-driven 참조 제거 · 접두어 정리 |`

### 10. domain-modeling (mp) — ✅ 적재, 적응 없음
- 4파일 184줄, MIT. CONTEXT.md/CONTEXT-MAP/ADR 포맷 — 우리 CONTEXT.md 규약과 정합(단일 컨텍스트면 그대로 동작).
- VENDORED: `| domain-modeling | mattpocock/skills | 6654f6b60cd9 | MIT | 2026-08-28 | 없음 |`

## Tier 2 — A 트랙 (12종)

### 11. research (mp) — ✅ 적재, 적응 1건 (감사 추가)
- 2파일 15줄, MIT. 1차 소스 조사 → md 저장, 백그라운드 위임(CC Task).
- **적응**: 1차 소스 조사 = 웹 접근 함의 → 본문 첫 줄 "모드 A 전용 — 네트워크(I7)" 표시 (팩 적응란에 없던 소견).
- VENDORED: `| research | mattpocock/skills | 6654f6b60cd9 | MIT | 2026-08-28 | 모드 A 전용 표시 |`

### 12. to-spec (mp) — ✅ 적재, 적응 2건 (팩대로 + 구체화)
- 2파일 80줄, MIT. 대화 → 스펙 합성(인터뷰 없이), seam 우선 테스트 설계 포함 — 좋은 본체.
- **적응**: ① "The issue tracker and triage label vocabulary should have been provided... run `/setup-matt-pocock-skills`."
  문단 삭제 ② Process 3의 "publish it to the project issue tracker. Apply the `ready-for-agent` triage label..." →
  "save it as a local Markdown file (repo 관례 위치, 없으면 `docs/specs/`)".
- VENDORED: `| to-spec | mattpocock/skills | 6654f6b60cd9 | MIT | 2026-08-28 | 트래커 발행 → 로컬 md 저장 |`

### 13. wait-what (mp) — ✅ 적재, 적응 1건 (팩대로)
- 2파일 12줄, MIT. **적응**: "(follow `CONTEXT-MAP.md` to the right one if the repo has more than one)" 괄호 절 삭제.
- VENDORED: `| wait-what | mattpocock/skills | 6654f6b60cd9 | MIT | 2026-08-28 | CONTEXT-MAP 절 삭제 |`

### 14. writing-for-agents (mp) — ✅ 적재, 적응 없음. 품질 최상급
- 3파일 106줄(SKILL.md + SKILL-MECHANICS.md + openai.yaml), MIT. 컨텍스트 포인터·2로드·정보 계층·leading word·
  가지치기 — 자작 스킬 규범으로 즉시 사용 가능. 클린.
- VENDORED: `| writing-for-agents | mattpocock/skills | 6654f6b60cd9 | MIT | 2026-08-28 | 없음 |`

### 15. skill-creator (ant) — ✅ 적재 18파일 전체, 적응 없음 (환경 노트 2건)
- 18파일 5,654줄, **Apache-2.0 (LICENSE.txt 동봉 확인)**. 스킬 제작·eval·설명 최적화 루프 전체.
- 실행 표면 전수 감사: 모든 모델 호출은 `claude -p` 서브프로세스(세션 인증 재사용, 별도 API 키 없음).
  eval 뷰어는 **127.0.0.1 바인드** stdlib 서버, 파일은 data URI로 임베드, 피드백은 로컬 feedback.json.
- 외부 참조(브라우저發): Google Fonts(viewer/eval_review/generate_report) + **SheetJS CDN(xlsx 미리보기,
  SRI integrity 해시 고정 — 변조 차단됨)**. 오프라인이면 폰트·xlsx 미리보기만 저하. 수정 불요 판단.
- 주의 2건: ① `generate_review.py`의 `_kill_port`가 기본 포트 3117 점유 프로세스를 SIGTERM — 로컬이지만
  3117을 다른 게 쓰면 죽일 수 있음(운영 노트) ② `run_eval.py`는 프로젝트 `.claude/commands/`에 임시 커맨드
  파일을 만들었다 지움 — 대상 repo가 git-clean일 때 돌릴 것.
- VENDORED: `| skill-creator | anthropics/skills | 3b3fad96af16 | Apache-2.0 | 2026-08-28 | 없음 (환경노트: py3.10+, PyYAML) |`

### 16. frontend-design (ant) — ✅ 적재, 적응 없음
- SKILL.md 55줄 + LICENSE.txt, **Apache-2.0 확인**. 순수 디자인 지침(템플릿 냄새 회피 캘리브레이션 포함). 클린.
- frontmatter `license` 키 유지 (공통 사항 2).
- VENDORED: `| frontend-design | anthropics/skills | 3b3fad96af16 | Apache-2.0 | 2026-08-28 | 없음 |`

### 17. improve-codebase-architecture (mp) — ✅ 적재, 적응 1건 + 의존 노트
- 3파일 199줄, MIT. 핫스팟 탐색 → HTML 리포트(OS tmp에 생성) → grilling 루프. grilling·domain-modeling 위임부는
  둘 다 vendor하므로 해석됨 ✓.
- **미이식 의존**: `/codebase-design` 스킬(Tier 3)을 어휘 소스로 호출 — 미설치 시 호출이 실패하고 HTML-REPORT.md의
  용어 절만으로 동작. **적응**: 그 호출 문장 끝에 "(codebase-design 미설치면 HTML-REPORT.md의 용어 절을 어휘로 쓴다)" 1구 추가.
  실사용에서 아쉬우면 codebase-design을 Tier 3에서 승격.
- 리포트가 Tailwind/Mermaid **CDN**을 로드(브라우저發) → 본문 첫 줄 모드 A 전용 표시.
- VENDORED: `| improve-codebase-architecture | mattpocock/skills | 6654f6b60cd9 | MIT | 2026-08-28 | codebase-design 부재 폴백 1구 · 모드A 표시 |`

### 18. code-review (mp) — ✅ 적재, 적응 1건 (감사 추가)
- 2파일 90줄, MIT. Standards/Spec 2축 병렬 서브에이전트 리뷰(읽기 팬아웃 — 허용) + Fowler smell 12종 베이스라인.
- **적응**: "If `docs/agents/issue-tracker.md` is missing, tell the user to run `/setup-matt-pocock-skills`." →
  "If no issue tracker doc exists, ask the user where the spec lives."
- VENDORED: `| code-review | mattpocock/skills | 6654f6b60cd9 | MIT | 2026-08-28 | setup 참조 → 사용자 질문으로 |`

### 19. receiving-code-review (sp) — ✅ 적재, 적응 없음
- 1파일 205줄, MIT. 수행적 동의 금지·검증 후 구현·YAGNI 체크. `gh api` 스레드 답글 지침(회사 A용) 포함 — 유지.
- VENDORED: `| receiving-code-review | obra/superpowers | b36e0829c6d0 | MIT | 2026-08-28 | 없음 |`

### 20. using-git-worktrees (sp) — ✅ 적재, 적응 없음
- 1파일 167줄, MIT. 격리 감지 → 네이티브 도구 우선 → git 폴백, gitignore 안전검증. 클린.
- Step 2의 npm/pip install은 워크트리 셋업(모드 A) — 러너 모드면 pre-tool이 차단(이중 방어).
- VENDORED: `| using-git-worktrees | obra/superpowers | b36e0829c6d0 | MIT | 2026-08-28 | 없음 |`

### 21. executing-plans (sp) — ✅ 적재, 적응 3건 (팩 "없음"에서 갱신)
- 1파일 64줄, MIT. 계획 로드 → 비판 리뷰 → 태스크 실행 → 막히면 중단.
- **적응**: ① "Tell your human partner that Superpowers works much better with... use superpowers:subagent-driven-development
  instead" 문단 삭제(금지 스킬 + using-superpowers 참조) ② Step 3의 "REQUIRED SUB-SKILL: superpowers:finishing-a-development-branch"
  → "모든 태스크 완료·검증 후 사용자에게 보고한다 — 병합·마무리는 사람 몫" ③ `superpowers:using-git-worktrees` → 평이름.
- VENDORED: `| executing-plans | obra/superpowers | b36e0829c6d0 | MIT | 2026-08-28 | subagent-driven/finishing 참조 제거 |`

### 22. retro (mp) — ✅ 적재, 적응 없음 (in-progress 성숙도 배지 유지)
- 2파일 49줄, MIT. 세션 회고 → 환경 개선 후보 7범주. writing-for-agents 참조(vendor함 ✓).
- CODING_STANDARDS.md·리뷰어 에이전트 언급은 mp 생태계 가정이지만 없어도 동작(후보 제안이 전부).
  실사용에서 findings/ 초안 연결은 이후 자작 확장으로.
- VENDORED: `| retro | mattpocock/skills | 6654f6b60cd9 | MIT | 2026-08-28 | 없음 (in-progress 출처 표시) |`

## Tier 2 — B 트랙 (4종)

### 23. test-driven-development (sp) — ✅ 적재, 적응 없음
- 2파일 518줄, MIT. Iron Law + red-green-refactor + 합리화 반박표 + writing-good-tests.md(mock 규율·change detector 금지).
  전 파일 클린, 네트워크 없음.
- VENDORED: `| test-driven-development | obra/superpowers | b36e0829c6d0 | MIT | 2026-08-28 | 없음 |`

### 24. webapp-testing (ant) — ✅ 적재, 적응 없음 (환경 노트)
- 6파일 506줄, **Apache-2.0 확인**. Playwright 로컬 웹앱 검증 + with_server.py(서버 수명주기, localhost 폴링) + 예제 3편.
- 전부 localhost — I7 통과. Playwright 의존은 대상 repo `.harness/init.sh` 계약으로(팩대로).
- 사소: console_logging.py 예제가 `/mnt/user-data/outputs/`(claude.ai 샌드박스 경로)에 저장 — 예제라 그대로 두되 인지.
- VENDORED: `| webapp-testing | anthropics/skills | 3b3fad96af16 | Apache-2.0 | 2026-08-28 | 없음 (Playwright는 init.sh 계약) |`

### 25. dsh-trim-cot-leakage (ds) — ✅ 적재, 적응 4건 (팩 "범용화"의 구체화)
- 3파일 372줄, MIT. CoT 누수 8분류 + "HEAD의 독자가 해석 가능한가" 단일 테스트 + keep 규칙 + 과교정 함정 —
  품질 매우 높음(SUMMARY·문서 후처리 직결).
- dsh repo 결합이 깊어 범용화 필요. **적응**:
  ① SKILL.md의 "**REQUIRED BACKGROUND:** [dsh-prose-standard](...)  ... [committed-artifact-citations note](...)" 문장 →
  "배경 원칙: 모든 문장은 완결된 명제로 서고, 인용은 커밋된 소유자가 있는 것만 남긴다." (미이식 스킬·노트 참조 제거)
  ② Workflow 1의 "per [dsh-prose-standard]..." → "명시적 스코프를 요구한다; `vendor/`·아카이브는 건드리지 않는다"
  ③ Workflow 3·5의 dsh 고유 게이트(doc-sync·verify-type-equiv·bilingual re-record·dsh-doc) 열거 →
  "touched surface에 repo가 정의한 문서 게이트가 있으면 그것을 돌린다"로 일반화
  ④ recall-batteries.md 호출 규칙의 dsh 경로 exclusions(`.agents/notes/archived` 등) → 일반 예시로
  (`--glob '!vendor/**' --glob '!node_modules/**'` + "repo의 아카이브 경로"). 중국어 배터리는 그대로 둠(삭제·창작 금지).
- references/examples.md는 무수정 유지 — 캘리브레이션 가치가 본체.
- VENDORED: `| dsh-trim-cot-leakage | deepseek-ai/deepseek-harness | cd5ef8148158 | MIT | 2026-08-28 | dsh 결합 4곳 범용화 |`

### 26. to-tickets (mp) — ✅ 적재하되 **로드 제외** (팩대로), 적응 2건
- 2파일 110줄, MIT. tracer-bullet 수직 분해 + blocking edge 선언 + expand-contract(wide refactor) — P7 원료로 우수.
- **적응**: ① `/setup-matt-pocock-skills` 문장 삭제 ② Process 5를 로컬 파일 모드만 남김
  (실제 트래커 발행 절 삭제 — 우리는 plan.json 생성기 원료로 쓸 것).
- **로드 제외 방법은 공통 사항 1을 따른다** (P7 착수 때 활성화).
- VENDORED: `| to-tickets | mattpocock/skills | 6654f6b60cd9 | MIT | 2026-08-28 | 트래커 발행부 삭제 · 로드 제외 상태 |`

---

## 집 실행 절차 (요약)

1. 위 고정 커밋으로 클론 (블록 그대로).
2. 팩 1부의 사전 준비(`skills/vendor/VENDORED.md` 생성) 후, **B-Tier1 → 설치 4종 → A-Tier1 → Tier 2** 순서로
   스킬당: 복사 → 이 문서의 적응 diff 적용 → I7 재검사(이 문서의 소견으로 갈음 가능, 스팟 체크 권장) →
   VENDORED.md 행 추가(위에 완성본) → 커밋 `[vendor] <이름> from <repo>@<커밋7>`.
3. `scripts/check` + `claude --plugin-dir .` 스모크 — **공통 사항 1(로딩 메커니즘)을 여기서 판정**.
4. 팩 1부의 완료 기준 체크리스트로 마감.

---

# 5부 — agent-athena 코드 반출 패치

> [!abstract] 무엇인가
> 회사 머신(push 불가)에서 만든 agent-athena 커밋 1개를 집으로 옮기는 반출물.
> **기준 커밋 `894cf7d`** 위에 적용하면 회사 쪽 `598b344`와 같은 내용이 된다.
> 내용: 훅 생존 카나리아(발화 횟수 포함) · 비용 상한 기본값(시도 $5/밤 $20/창 0.85) ·
> S2 대화형 commit/push 완화 · G2 계획 DAG mermaid 렌더 · stderr 레이스 수정. 상세는 팩 2부 §6 Phase A-0.

## 적용 절차 (집에서)

```
cd agent-athena
git rev-parse --short HEAD        # 894cf7d 인지 확인. 다르면 아래 '기준이 다를 때'
# 아래 패치 블록 전체(From ... 부터 끝까지)를 a0.patch 로 저장한 뒤:
git am --3way --whitespace=fix a0.patch
./scripts/check                   # 47 tests, exit 0 이어야 한다
```

- **코드 블록을 원문 그대로 저장할 것** — 공백·빈 줄이 깨지면 `git am`이 실패한다.
  Obsidian에서는 소스 모드로 복사하거나 파일째 내보낸다.
- **기준이 다를 때** (집 HEAD가 894cf7d 이후로 진행): `git am --3way`가 대부분 흡수한다.
  충돌 시 무리하게 풀지 말고 팩 2부 §6 Phase A-0 서술로 재구현하는 편이 안전하다.
- 적용 후 기대 diffstat:

```
 ASSUMPTIONS.md                    |  3 ++
 CLAUDE.md                         |  2 +-
 hooks/pre-tool                    |  3 +-
 hooks/session-start               |  7 ++++
 runner/drivers.py                 | 39 +++++++++++++++++++--
 runner/harnesslib.py              | 60 +++++++++++++++++++++++++++++++--
 runner/night                      | 27 ++++++++++++---
 templates/harness-dir/domain.json | 10 +++---
 tests/fake_model.py               |  8 +++--
 tests/test_drivers.py             | 71 +++++++++++++++++++++++++++++++++++++++
 tests/test_e2e.py                 | 43 ++++++++++++++++++++++++
 tests/test_harnesslib.py          | 30 +++++++++++++++++
 tests/test_hooks.py               | 14 ++++++--
 13 files changed, 296 insertions(+), 21 deletions(-)
```

## 패치

(집 세션에서 적용된 커밋의 `git format-patch --stdout -1` 출력 — 아래 블록은 스크립트가 채운다)

`````diff
From 72b4ef45ea165b775c3d1ba12e90af980a12079d Mon Sep 17 00:00:00 2001
From: "jun.heo" <jun.heo@mangoboost.io>
Date: Fri, 28 Aug 2026 16:09:09 +0900
Subject: [PATCH] =?UTF-8?q?feat(harness):=20=ED=9B=85=20=EC=83=9D=EC=A1=B4?=
 =?UTF-8?q?=20=EC=B9=B4=EB=82=98=EB=A6=AC=EC=95=84=20+=20=EB=B9=84?=
 =?UTF-8?q?=EC=9A=A9=20=EC=83=81=ED=95=9C=20=EA=B8=B0=EB=B3=B8=EA=B0=92=20?=
 =?UTF-8?q?+=20S2=20=EC=99=84=ED=99=94=20+=20=EA=B3=84=ED=9A=8D=20DAG=20?=
 =?UTF-8?q?=EB=A0=8C=EB=8D=94?=
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit

- 카나리아: session-start가 HARNESS_CANARY에 발화 기록을 append, 드라이버가
  첫 assistant 이벤트에서 확인 — 없으면 즉시 중단 (hooks_dead, 인프라 실패,
  시도 미산입, 밤 종료). --plugin-dir 로딩 실패 = 무방비 세션 차단.
  줄 수 = 발화 횟수 — 2 이상이면 전역 설치와의 이중 발화로 기록 (배송 결정 재료)
- 비용: 시도당 $5 (driver.max_budget_usd) · 밤 $20 (budget.max_night_usd,
  러너 집행 cost_budget) · 5시간 창 0.85 (budget.rate_limit_stop, 판정 후
  rate_limited). null 상한은 상한이 아니다 — 해제는 명시적 null 로만
- S2: 대화형에서 사람이 시킨 git commit/push는 막지 않는다 (사람이 승인
  루프에 있다, 2026-08-28 결정). 러너 모드 거부는 부기의 근간이라 유지
- G2: SUMMARY에 계획 DAG를 mermaid로 — 러너가 plan.json+상태에서 결정론적
  렌더 (aggregated 먼저, expanded는 다음)
- run_claude stderr 펌프 스레드 join (조기 종료 시 stderr 유실 레이스)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
---
 ASSUMPTIONS.md                    |  3 ++
 CLAUDE.md                         |  2 +-
 hooks/pre-tool                    |  3 +-
 hooks/session-start               |  7 +++
 runner/drivers.py                 | 39 +++++++++++++++--
 runner/harnesslib.py              | 60 ++++++++++++++++++++++++--
 runner/night                      | 27 +++++++++---
 templates/harness-dir/domain.json | 10 +++--
 tests/fake_model.py               |  8 +++-
 tests/test_drivers.py             | 71 +++++++++++++++++++++++++++++++
 tests/test_e2e.py                 | 43 +++++++++++++++++++
 tests/test_harnesslib.py          | 30 +++++++++++++
 tests/test_hooks.py               | 14 +++++-
 13 files changed, 296 insertions(+), 21 deletions(-)

diff --git a/ASSUMPTIONS.md b/ASSUMPTIONS.md
index efa0f02..1a4e6fd 100644
--- a/ASSUMPTIONS.md
+++ b/ASSUMPTIONS.md
@@ -28,6 +28,9 @@
 | 잠듦 감지 | 무인 실행의 전제 "머신이 깨어 있다"가 깨질 수 있다(뚜껑) — 막을 수 없으니 감지해 조기 종료 | 구조적 · A | `drivers.py` slept_seconds, `runner/night` SLEEP_ABORT_SEC |
 | 인프라 실패 분리 | 무응답·잠듦은 작업의 실패가 아니다 — 같은 카운터에 넣으면 무고한 작업이 막힌다 | 구조적 · A | `harnesslib.py: derive_states` (infra), `runner/queue unblock` |
 | 복구 작업 우선 | red 트리에서 모델은 "내 작업은 됐다"고 판단하고 넘어간다 | Claude 5 · B | `harnesslib.py: select_next` (repair 우선) |
+| 훅 생존 카나리아 | 훅은 자기 부재를 알릴 수 없다 — `--plugin-dir` 주입이 조용히 실패하면 `--dangerously-skip-permissions`만 남아 무방비다 (I6·I7이 전부 훅에 걸려 있다). session-start가 카나리아 파일을 쓰고, 드라이버가 첫 assistant 이벤트에서 존재를 확인 — 없으면 즉시 중단 (`hooks_dead`) | 구조적 · A | `hooks/session-start`, `drivers.py: run_claude`, `runner/night` |
+| G2 계획 DAG 렌더 | 모델이 그린 다이어그램은 자기 평가가 섞인다 — 러너가 plan.json+상태에서 결정론적으로 mermaid 렌더 (P10과 같은 원리) | 구조적 · A | `harnesslib.py: render_plan_dag` |
+| 비용 상한 기본값 | 모델은 자기 비용을 모르고, null 상한은 상한이 아니다 (night-002: 55분에 5시간 창 67% 실측). 시도당 `driver.max_budget_usd` · 밤당 `budget.max_night_usd` · 창 사용률 `budget.rate_limit_stop` 삼중 기본값 — 해제는 명시적 null 로만 | 구조적 · A | `harnesslib.py: DOMAIN_DEFAULTS`, `runner/night` |
 
 ## 지운 것
 (아직 없음. 지울 때는 행을 여기로 옮기고 날짜·근거를 적는다 — 되살릴 때 필요하다.)
diff --git a/CLAUDE.md b/CLAUDE.md
index a3618e4..e611615 100644
--- a/CLAUDE.md
+++ b/CLAUDE.md
@@ -24,7 +24,7 @@ Claude Code / Codex 위에 얹는 도메인 무의존 레이어. 밤새 무인
 
 ## 커밋 정책 (전역 규칙의 유일한 예외)
 - 러너만 커밋한다. 단위 = 검증 통과. 브랜치 `harness/night-NNN`. **push 금지.** 메시지 접두어 `[harness night-NNN task-NNN]`.
-- 모델은 commit/push를 하지 않는다 — `pre-tool` 훅이 거부한다.
+- 러너 모드에서 모델은 commit/push를 하지 않는다 — `pre-tool` 훅이 거부한다. 대화형은 막지 않는다(사람이 승인 루프에, S2).
 
 ## 작업 규칙 (이 repo를 고칠 때)
 - 코드는 Python 3.9 stdlib만. `from __future__ import annotations` 필수, `X | None` 런타임 문법 금지. 외부 의존성 추가 금지.
diff --git a/hooks/pre-tool b/hooks/pre-tool
index beb39d2..aba1815 100755
--- a/hooks/pre-tool
+++ b/hooks/pre-tool
@@ -28,11 +28,12 @@ PLAN = r"\.harness/(plan\.json|spec\.md|domain\.json|verify|init\.sh|\.gitignore
 WRITE_OPS = r"(>>?|\btee\b|\bsed\s+-i|\bmv\b|\bcp\b|\brm\b|\btruncate\b)[^|;&]*"
 
 ALWAYS_DENY = [
-    (r"\bgit\s+(push|commit)\b", "commit/push 는 러너의 몫이다 (spec §6). 검증이 통과하면 러너가 커밋한다"),
     (WRITE_OPS + BOOK, "부기 파일(log.jsonl / SUMMARY.md / BLOCKED.md)은 러너 소유다 — 읽기만"),
     (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*\s+(/|~|\$HOME)(\s|$|/\s)", "파괴적 삭제"),
 ]
 RUNNER_DENY = [
+    # commit/push 는 대화형에서는 막지 않는다 — 사람이 승인 루프에 있다 (S2, 2026-08-28 결정). 러너 모드는 부기의 근간이라 유지
+    (r"\bgit\s+(push|commit)\b", "commit/push 는 러너의 몫이다 (spec §6). 검증이 통과하면 러너가 커밋한다"),
     (r"(^|[|;&]\s*|\$\(\s*|`\s*)(curl|wget|ssh|scp|sftp|nc|ncat|telnet|rsync)\b", "네트워크 접근 금지 (I7). 필요한 것은 .harness/init.sh 의 몫"),
     (r"\b(pip3?|pipx|uv|npm|pnpm|yarn|brew|apt(-get)?|cargo|go)\s+(install|add|get|update|upgrade)\b", "패키지 설치는 부트스트랩(.harness/init.sh)의 몫 (I7)"),
     (r"\bgit\s+(fetch|pull|clone|remote)\b|(^|[|;&]\s*)gh\s", "네트워크 접근 금지 (I7)"),
diff --git a/hooks/session-start b/hooks/session-start
index b640c4e..b135fb8 100755
--- a/hooks/session-start
+++ b/hooks/session-start
@@ -84,6 +84,13 @@ def build(cwd: Path) -> str:
 
 def main() -> int:
     H.ensure_utf8_stdio()
+    canary = os.environ.get("HARNESS_CANARY")
+    if canary:  # 러너가 지정한 카나리아 — 존재 = "플러그인 훅이 로드됐고 돌 수 있다"의 증명 (없으면 드라이버가 즉시 중단).
+        try:    # append: 줄 수 = 발화 횟수 — 전역 설치와 --plugin-dir 주입이 겹치면 2줄이 된다 (배송 결정의 이중 발화 감지)
+            with open(canary, "a", encoding="utf-8") as f:
+                f.write("%s pid=%d\n" % (H.iso(H.now()), os.getpid()))
+        except OSError as e:
+            print("session-start: 카나리아 쓰기 실패: %s" % e, file=sys.stderr)
     try:
         data = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace"))
     except (ValueError, OSError):
diff --git a/runner/drivers.py b/runner/drivers.py
index 7ad165c..0abbca2 100644
--- a/runner/drivers.py
+++ b/runner/drivers.py
@@ -49,6 +49,8 @@ class ModelRun:
     assistant_turns: int = 0                                  # 스트림에서 센 assistant 메시지 수 (result 가 없어도 안다)
     slept_seconds: float = 0.0                                # 벽시계 − 단조시계 차이 = 머신이 잠든 시간 (findings/002)
     rate_limit_utilization: Optional[float] = None            # 5시간 창 사용률 (rate_limit_event)
+    hooks_dead: bool = False                                  # 카나리아 부재 — 플러그인 훅이 로드되지 않은 세션 (즉시 중단)
+    hook_fires: int = 0                                       # 카나리아 줄 수 = session-start 발화 횟수 (2+ = 이중 발화)
 
 
 @dataclass
@@ -202,6 +204,10 @@ def run_claude(ctx: TaskContext, prompt: str, system_prompt: str, stream_path: P
     env = build_env(ctx)
     timeout = ctx.timeout_minutes * 60.0
     stream_path.parent.mkdir(parents=True, exist_ok=True)
+    canary = stream_path.with_suffix(".canary")  # session-start 훅이 쓴다 — 존재 = 플러그인 훅 생존 증명
+    canary.unlink(missing_ok=True)               # 이전 시도의 파일이 생존으로 위장하면 안 된다
+    env["HARNESS_CANARY"] = str(canary)
+    canary_checked = False
     start = time.time()
     start_mono = time.monotonic()  # 잠든 시간은 세지 않는다 (macOS mach_absolute_time / Linux CLOCK_MONOTONIC)
     proc = subprocess.Popen(
@@ -221,8 +227,9 @@ def run_claude(ctx: TaskContext, prompt: str, system_prompt: str, stream_path: P
         assert proc.stderr is not None
         stderr_buf.append(proc.stderr.read())
 
-    threading.Thread(target=pump_out, daemon=True).start()
-    threading.Thread(target=pump_err, daemon=True).start()
+    pumps = [threading.Thread(target=pump_out, daemon=True), threading.Thread(target=pump_err, daemon=True)]
+    for th in pumps:
+        th.start()
     try:
         with stream_path.open("ab") as out:
             while True:
@@ -239,6 +246,18 @@ def run_claude(ctx: TaskContext, prompt: str, system_prompt: str, stream_path: P
                     break
                 out.write(ln)
                 _ingest(run, ctx, ln)
+                if not canary_checked and (run.assistant_turns or run.saw_result):
+                    # 모델이 말하기 시작했다 = SessionStart 훅은 이미 끝났어야 한다. 없으면 훅 없이 도는 중 — 무방비
+                    canary_checked = True
+                    if not canary.exists():
+                        run.hooks_dead = True
+                        run.error = "훅 카나리아 없음 — 플러그인 훅이 로드되지 않았다 (쓰기 중재·trifecta 가드 부재), 즉시 중단"
+                        H.kill_group(proc)
+                        break
+                    try:  # 줄 수 = 발화 횟수. 2 이상이면 전역 설치와 --plugin-dir 이 겹친 것 — 죽이지 않고 기록만 (훅은 살아 있다)
+                        run.hook_fires = max(1, len(canary.read_text(encoding="utf-8").splitlines()))
+                    except OSError:
+                        run.hook_fires = 1
     except BaseException:
         H.kill_group(proc)
         raise
@@ -248,6 +267,13 @@ def run_claude(ctx: TaskContext, prompt: str, system_prompt: str, stream_path: P
         except subprocess.TimeoutExpired:
             H.kill_group(proc)
             proc.wait()
+        for th in pumps:  # stderr 를 다 읽기 전에 stderr_buf 를 보면 빈 오류가 된다 (조기 종료 경로)
+            th.join(timeout=5)
+        for pipe in (proc.stdout, proc.stderr):
+            try:
+                pipe.close()
+            except OSError:
+                pass
     run.exit = proc.returncode
     run.seconds = time.time() - start
     run.slept_seconds = max(0.0, run.seconds - (time.monotonic() - start_mono))
@@ -279,13 +305,20 @@ def run_fake(ctx: TaskContext, prompt: str, stream_path: Path) -> ModelRun:
     stream_path.write_text(out, encoding="utf-8")
     run = ModelRun(ok=(code == 0 and not to), timed_out=to, exit=code, seconds=secs, turns=1,
                    result_text=H.tail(out, 1500), saw_result=True, stream_path=str(stream_path))
-    for ln in out.splitlines():  # 가짜 모델은 "EDIT <path>" 줄로 편집을 알린다 (P9 경로 테스트용)
+    for ln in out.splitlines():  # 가짜 모델은 "EDIT <path>" 줄로 편집을, "COST <usd>" 줄로 비용을 알린다
         if ln.startswith("EDIT "):
             fp = ln[5:].strip()
             run.edits[fp] = run.edits.get(fp, 0) + 1
+        elif ln.startswith("COST "):
+            try:
+                run.cost_usd = float(ln[5:].strip())
+            except ValueError:
+                pass
     m = RESULT_RE.search(out)
     run.self_report = m.group(1).lower() if m else ""
     run.slept_seconds = float(os.environ.get("HARNESS_FAKE_SLEPT") or 0)  # 테스트: 잠듦 흉내
+    if os.environ.get("HARNESS_FAKE_RATE"):                               # 테스트: 창 사용률 흉내
+        run.rate_limit_utilization = float(os.environ["HARNESS_FAKE_RATE"])
     if to:
         run.error = "모델 시간 초과 (%d분)" % int(ctx.timeout_minutes)
     elif code != 0:
diff --git a/runner/harnesslib.py b/runner/harnesslib.py
index 56d501d..c50273a 100644
--- a/runner/harnesslib.py
+++ b/runner/harnesslib.py
@@ -126,8 +126,10 @@ DOMAIN_DEFAULTS: Dict[str, Any] = {
         "leaf_max_minutes": 30,    # 리프 상한 = 작업당 모델 타임아웃 (ASSUMPTIONS: 30분 이상에서 일관성 상실)
         "max_attempts": 3,         # 이 횟수 실패하면 blocked (P8-lite)
         "starvation_minutes": 1440,  # 이보다 오래 기다린 작업은 무조건 먼저 (P2, 등급 D)
+        "max_night_usd": 20.0,       # 밤 누적 비용 상한 (USD). null 상한은 상한이 아니다 — 해제는 명시적 null 로만
+        "rate_limit_stop": 0.85,     # 5시간 창 사용률이 이 이상 관측되면 밤 종료 (구독 요금제의 실질 예산; night-002 실측 67%)
     },
-    "driver": {"name": "claude", "model": None, "effort": None, "max_turns": 120, "max_budget_usd": None},
+    "driver": {"name": "claude", "model": None, "effort": None, "max_turns": 120, "max_budget_usd": 5.0},
 }
 
 
@@ -198,6 +200,16 @@ class Domain:
     def starvation_minutes(self) -> float:
         return float(self.raw["budget"]["starvation_minutes"])
 
+    @property
+    def max_night_usd(self) -> Optional[float]:
+        v = self.raw["budget"].get("max_night_usd")
+        return None if v is None else float(v)
+
+    @property
+    def rate_limit_stop(self) -> Optional[float]:
+        v = self.raw["budget"].get("rate_limit_stop")
+        return None if v is None else float(v)
+
     @property
     def driver(self) -> Dict[str, Any]:
         return dict(self.raw["driver"])
@@ -899,7 +911,10 @@ def collect_night(events: Sequence[Dict[str, Any]], tasks: Sequence[Task], domai
             if n >= DOOM_EDIT_THRESHOLD:
                 anomalies.append("doom loop 의심: %s 같은 파일 %d회 편집 (%s)" % (e["task"], n, f))
         turns = int(e.get("turns") or 0)
-        if e.get("slept_seconds"):
+        if e.get("hooks_dead"):
+            anomalies.append("훅 미로드: %s (시도 %s) — 카나리아 없음, 쓰기 중재·trifecta 가드가 없는 세션이라 즉시 중단했다. --plugin-dir 경로와 플러그인 로딩을 확인하라" % (
+                e["task"], e.get("attempt")))
+        elif e.get("slept_seconds"):
             slept_total += float(e["slept_seconds"])
             anomalies.append("머신 잠듦 %s: %s (시도 %s) — caffeinate 는 유휴 잠자기만 막는다. 뚜껑을 열어두거나 서버에서 돌린다" % (
                 fmt_duration(float(e["slept_seconds"])), e["task"], e.get("attempt")))
@@ -910,6 +925,9 @@ def collect_night(events: Sequence[Dict[str, Any]], tasks: Sequence[Task], domai
             anomalies.append("드라이버 오류: %s (시도 %s) — %s" % (e["task"], e.get("attempt"), str(e["error"])[:120]))
         if e.get("denials"):
             anomalies.append("훅 거부 %d회: %s (시도 %s)" % (int(e["denials"]), e["task"], e.get("attempt")))
+        if int(e.get("hook_fires") or 0) > 1:
+            anomalies.append("훅 이중 발화 %d회: %s (시도 %s) — 전역 플러그인 설치와 --plugin-dir 주입이 겹쳤는지 확인 (배송 결정)" % (
+                int(e["hook_fires"]), e["task"], e.get("attempt")))
     rl = max((float(e.get("rate_limit") or 0) for e in ne if e.get("event") == "model_done"), default=0.0)
     if rl >= 0.5:
         anomalies.append("5시간 창 사용률 최대 %d%% — 다음 밤 창이 겹치면 느려진다" % round(rl * 100))
@@ -948,6 +966,37 @@ def _error_line(text: Optional[str]) -> str:
     return lines[-1][:160]
 
 
+DAG_BADGE = {"passed": "✅", "blocked": "⛔", "failed": "🔁", "started": "🏃", "pending": "⬜"}
+
+
+def _dag_node(tid: Any) -> str:
+    """mermaid 노드 id — 영숫자만 남긴다 (하이픈은 파서가 엣지로 오독할 수 있다)."""
+    s = re.sub(r"[^0-9A-Za-z]", "", str(tid)) or "x"
+    return s if s[0].isalpha() else "n" + s
+
+
+def render_plan_dag(tasks: Sequence[Task], states: Dict[str, TaskState]) -> str:
+    """계획 DAG를 mermaid로 (G2 aggregated) — 막힌 작업이 무엇을 물고 있는지 아침에 그림으로 보인다.
+    렌더는 러너가 plan.json+상태에서 결정론적으로 한다 (부기는 프로그램 — 모델이 그리지 않는다).
+    Obsidian·GitHub가 네이티브 렌더. expanded(log 언롤) 모드는 다음."""
+    ids = sorted(t.id for t in tasks if t.id)
+    if not ids:
+        return ""
+    by_id = {t.id: t for t in tasks if t.id}
+    lines = ["```mermaid", "flowchart TD"]
+    for tid in ids:
+        t = by_id[tid]
+        st = states.get(tid) or TaskState(id=tid)
+        title = re.sub(r'["\[\]{}()<>`|#;]', "", t.title).strip()[:40]
+        lines.append('  %s["%s %s %s"]' % (_dag_node(tid), DAG_BADGE.get(st.state, "⬜"), tid, title))
+    for tid in ids:
+        for dep in by_id[tid].depends_on:
+            if dep in by_id:
+                lines.append("  %s --> %s" % (_dag_node(dep), _dag_node(tid)))
+    lines.append("```")
+    return "\n".join(lines)
+
+
 def render_summary(c: Dict[str, Any]) -> str:
     started, ended = c["started"], c["ended"]
     s_ts = started.get("ts") if started else None
@@ -956,13 +1005,18 @@ def render_summary(c: Dict[str, Any]) -> str:
     by_id, states = c["by_id"], c["states"]
     reason = {"budget": "예산 소진", "queue_empty": "큐 비움", "max_tasks": "작업 수 상한", "interrupted": "중단됨",
               "smoke_unrepairable": "스모크 복구 실패", "bootstrap_failed": "부트스트랩 실패",
-              "machine_slept": "머신이 잠듦 (밤 중단)", "driver_unhealthy": "드라이버 무응답 연속 (밤 중단)"}.get(
+              "machine_slept": "머신이 잠듦 (밤 중단)", "driver_unhealthy": "드라이버 무응답 연속 (밤 중단)",
+              "cost_budget": "비용 상한 도달", "rate_limited": "5시간 창 사용률 상한 도달",
+              "hooks_dead": "훅 미로드 (밤 중단)"}.get(
         (ended or {}).get("reason", ""), (ended or {}).get("reason", "진행 중"))
     branch = (started or {}).get("branch", "?")
     out = ["# %s · %s → %s (%s)" % (c["night"], fmt_clock(s_ts), fmt_clock(e_ts), dur), ""]
     out += ["## 결론",
             "완료 %d / 실패(재시도 예정) %d / 막힘 %d / 미착수 %d · 종료: %s · 브랜치 `%s` · 비용 $%.2f" % (
                 len(c["passed"]), len(c["retry_ids"]), len(c["blocked"]), len(c["pending"]), reason, branch, c["cost"]), ""]
+    dag = render_plan_dag(list(by_id.values()), states)
+    if dag:
+        out += ["## 계획 DAG (✅통과 ⛔막힘 🔁재시도 ⬜미착수)", dag, ""]
     out += ["## 완료 (검증 통과)"]
     if c["passed"]:
         for e in c["passed"]:
diff --git a/runner/night b/runner/night
index 7d2bda1..a0b0f49 100755
--- a/runner/night
+++ b/runner/night
@@ -135,7 +135,9 @@ def run_night(args: argparse.Namespace) -> int:
     if git.branch_exists(branch):
         raise H.HarnessError("브랜치 %s 가 이미 있다 (로그와 브랜치가 어긋남). 지우거나 병합한 뒤 다시" % branch)
     git.create_branch(branch, "HEAD")
-    say("%s 시작 · 기점 %s (%s) · 브랜치 %s · 예산 %.1fh · 드라이버 %s" % (night_id, git.head(), note, branch, hours, driver_name))
+    cost_cap = "없음" if domain.max_night_usd is None else "$%.0f" % domain.max_night_usd
+    say("%s 시작 · 기점 %s (%s) · 브랜치 %s · 예산 %.1fh · 비용 상한 %s · 드라이버 %s" % (
+        night_id, git.head(), note, branch, hours, cost_cap, driver_name))
 
     if not repo.gitignore.exists():
         repo.gitignore.write_text(GITIGNORE_BODY, encoding="utf-8")
@@ -160,7 +162,8 @@ def run_night(args: argparse.Namespace) -> int:
     try:
         H.append_event(log, "night_started", night=night_id, branch=branch, base=git.head(), base_note=note,
                        budget_minutes=int(hours * 60), deadline=H.iso(deadline), driver=driver_name,
-                       model=domain.driver.get("model"), leaf_max_minutes=domain.leaf_max, max_attempts=domain.max_attempts)
+                       model=domain.driver.get("model"), leaf_max_minutes=domain.leaf_max, max_attempts=domain.max_attempts,
+                       max_night_usd=domain.max_night_usd, rate_limit_stop=domain.rate_limit_stop)
 
         # 지난 밤이 판정 없이 죽었으면 닫는다 (append-only로 — 지우지 않는다)
         states = H.derive_states(H.read_log(log), tasks)
@@ -220,6 +223,7 @@ def run_night(args: argparse.Namespace) -> int:
 
         # ── 루프
         tasks_run = 0
+        night_cost = 0.0  # 이 밤의 누적 비용 (USD) — model_done 합계와 같아야 한다
         driver_fails = 0  # 연속 무응답(시간 초과 + 0턴) 횟수
         while True:
             now_dt = H.now()
@@ -227,6 +231,10 @@ def run_night(args: argparse.Namespace) -> int:
             if remaining < domain.leaf_min:
                 ended_reason = "budget"
                 break
+            if domain.max_night_usd is not None and night_cost >= domain.max_night_usd:
+                ended_reason = "cost_budget"
+                say("누적 비용 $%.2f ≥ 상한 $%.2f → 밤 종료" % (night_cost, domain.max_night_usd))
+                break
             if args.max_tasks and tasks_run >= args.max_tasks:
                 ended_reason = "max_tasks"
                 break
@@ -249,12 +257,14 @@ def run_night(args: argparse.Namespace) -> int:
             stream_path = sessions_dir / ("%s.%d.stream.jsonl" % (task.id, attempt))
             run = D.run_task(ctx, driver_name, stream_path)
             tasks_run += 1
+            night_cost += run.cost_usd
             H.append_event(log, "model_done", night=night_id, task=task.id, attempt=attempt, ok=run.ok, timed_out=run.timed_out,
                            seconds=round(run.seconds, 1), turns=run.turns, cost_usd=round(run.cost_usd, 4),
                            edits=run.edits or None, tool_counts=run.tool_counts or None, denials=run.denials or None,
                            self_report=run.self_report or None, error=run.error or None,
                            slept_seconds=round(run.slept_seconds) if run.slept_seconds >= 30 else None,
-                           rate_limit=run.rate_limit_utilization,
+                           rate_limit=run.rate_limit_utilization, hooks_dead=run.hooks_dead or None,
+                           hook_fires=run.hook_fires if run.hook_fires > 1 else None,
                            result_tail=H.tail(run.result_text, 1500), stream=repo.rel(stream_path))
             say("  모델 %s · %s · %d턴 · $%.2f · 자기보고 %s%s" % (
                 "ok" if run.ok else "오류", H.fmt_duration(run.seconds), run.turns, run.cost_usd, run.self_report or "-",
@@ -262,7 +272,9 @@ def run_night(args: argparse.Namespace) -> int:
 
             # 인프라 실패 — 작업의 실패가 아니다: 시도 횟수를 먹지 않고, 계속해 봐야 소용없으면 밤을 끝낸다 (findings/002)
             infra = None
-            if run.slept_seconds >= SLEEP_ABORT_SEC:
+            if run.hooks_dead:
+                infra = ("hooks", "플러그인 훅 미로드 (카나리아 없음) — 쓰기 중재·trifecta 가드가 없는 무방비 실행", "hooks_dead")
+            elif run.slept_seconds >= SLEEP_ABORT_SEC:
                 H.append_event(log, "sleep_detected", night=night_id, task=task.id, attempt=attempt, seconds=round(run.slept_seconds))
                 infra = ("sleep", "머신이 %s 잠듦 — 시도 무효 (caffeinate 는 유휴 잠자기만 막는다)" % H.fmt_duration(run.slept_seconds), "machine_slept")
             elif run.timed_out and run.turns == 0:
@@ -333,6 +345,11 @@ def run_night(args: argparse.Namespace) -> int:
                         ended_reason = "smoke_unrepairable"
                         break
             in_flight = None
+            rl = run.rate_limit_utilization
+            if domain.rate_limit_stop is not None and rl is not None and rl >= domain.rate_limit_stop:
+                ended_reason = "rate_limited"
+                say("  5시간 창 사용률 %d%% ≥ 상한 %d%% → 밤 종료 (창이 풀린 뒤 다시)" % (round(rl * 100), round(domain.rate_limit_stop * 100)))
+                break
     except Interrupted:
         if in_flight:
             task, attempt = in_flight
@@ -366,7 +383,7 @@ def run_night(args: argparse.Namespace) -> int:
             lock.unlink()
         except FileNotFoundError:
             pass
-    return 0 if ended_reason in ("budget", "queue_empty", "max_tasks") else 3
+    return 0 if ended_reason in ("budget", "queue_empty", "max_tasks", "cost_budget", "rate_limited") else 3
 
 
 def main() -> int:
diff --git a/templates/harness-dir/domain.json b/templates/harness-dir/domain.json
index 63ee944..7038dd4 100644
--- a/templates/harness-dir/domain.json
+++ b/templates/harness-dir/domain.json
@@ -11,9 +11,11 @@
     "leaf_min_minutes": 5,
     "leaf_max_minutes": 30,
     "max_attempts": 3,
-    "starvation_minutes": 1440
+    "starvation_minutes": 1440,
+    "max_night_usd": 20,
+    "rate_limit_stop": 0.85
   },
-  "_budget": "leaf_max = 작업당 모델 타임아웃. max_attempts 실패 시 blocked. starvation_minutes 보다 오래 기다린 작업은 무조건 먼저 (P2)",
-  "driver": {"name": "claude", "model": null, "effort": null, "max_turns": 120, "max_budget_usd": null},
-  "_driver": "name: claude | fake. model: sonnet/opus/... (null = CLI 기본). max_budget_usd: 시도당 비용 상한"
+  "_budget": "leaf_max = 작업당 모델 타임아웃. max_attempts 실패 시 blocked. starvation_minutes 보다 오래 기다린 작업은 무조건 먼저 (P2). max_night_usd = 밤 누적 비용 상한(USD) — null 상한은 상한이 아니다, 해제는 명시적 null 로만. rate_limit_stop = 5시간 창 사용률이 이 이상이면 밤 종료 (null = 해제)",
+  "driver": {"name": "claude", "model": null, "effort": null, "max_turns": 120, "max_budget_usd": 5},
+  "_driver": "name: claude | fake. model: sonnet/opus/... (null = CLI 기본). max_budget_usd: 시도당 비용 상한 (USD, null = 해제)"
 }
diff --git a/tests/fake_model.py b/tests/fake_model.py
index d2b9599..3585467 100755
--- a/tests/fake_model.py
+++ b/tests/fake_model.py
@@ -1,11 +1,12 @@
 #!/usr/bin/env python3
 """가짜 모델 — e2e 테스트용 드라이버 스크립트. 작업 JSON을 stdin으로 받아 제목의 태그대로 트리를 바꾼다.
 
-태그: [add-mul] [add-sub] [hopeless] [break-global] [repair]
-출력 규약: "EDIT <path>" 줄 = 편집 1회 (P9 카운터), 마지막 줄 "RESULT: ..." = 자기 보고 (판정 아님).
+태그: [add-mul] [add-sub] [hopeless] [break-global] [repair] [cost:N]
+출력 규약: "EDIT <path>" 줄 = 편집 1회 (P9 카운터), "COST <usd>" 줄 = 비용 보고, 마지막 줄 "RESULT: ..." = 자기 보고 (판정 아님).
 """
 import json
 import os
+import re
 import sys
 from pathlib import Path
 
@@ -39,4 +40,7 @@ elif "[out-of-scope]" in title:
 elif "복구" in title or "[repair]" in title:
     (root / "FIXED").write_text("fixed\n")
     print("EDIT FIXED")
+m = re.search(r"\[cost:([0-9.]+)\]", title)
+if m:
+    print("COST " + m.group(1))
 print("RESULT: done — fake model (%s)" % title)
diff --git a/tests/test_drivers.py b/tests/test_drivers.py
index 922e63e..68e33c4 100644
--- a/tests/test_drivers.py
+++ b/tests/test_drivers.py
@@ -1,8 +1,10 @@
 """drivers 단위 테스트 — 스트림 집계 (result 없이도 턴 수·rate limit 을 안다)."""
 from __future__ import annotations
 
+import os
 import sys
 import tempfile
+import time
 import unittest
 from pathlib import Path
 from types import SimpleNamespace
@@ -36,5 +38,74 @@ class IngestTests(unittest.TestCase):
             self.assertEqual((run.turns, run.cost_usd, run.denials, run.self_report, run.saw_result), (7, 1.5, 1, "done", True))
 
 
+class ClaudeCanaryTests(unittest.TestCase):
+    """run_claude 훅 생존 카나리아 — session-start 훅이 쓴 파일이 없으면 첫 assistant 이벤트에서 즉시 죽인다.
+
+    가짜 claude 실행 파일을 PATH 앞에 놓고 stream-json 을 흉내 낸다. 카나리아를 만드는 쪽 = 훅이 로드된 세션.
+    """
+
+    ASSISTANT = '{"type":"assistant","message":{"content":[{"type":"text","text":"hi"}]}}'
+    RESULT = '{"type":"result","num_turns":1,"total_cost_usd":0.1,"result":"RESULT: done"}'
+
+    def setUp(self):
+        self.tmp = tempfile.TemporaryDirectory()
+        self.root = Path(self.tmp.name).resolve()
+        (self.root / "bin").mkdir()
+        (self.root / "repo").mkdir()
+        self.old_path = os.environ.get("PATH", "")
+        os.environ["PATH"] = str(self.root / "bin") + os.pathsep + self.old_path
+
+    def tearDown(self):
+        os.environ["PATH"] = self.old_path
+        self.tmp.cleanup()
+
+    def fake_claude(self, lines, touch_canary, sleep_after=False, double_fire=False):
+        data = self.root / "bin" / "stream.jsonl"
+        data.write_text("\n".join(lines) + "\n", encoding="utf-8")
+        body = ["#!/bin/sh"]
+        if touch_canary:
+            body.append(': > "$HARNESS_CANARY"')
+        if double_fire:
+            body.append('printf "a\\nb\\n" > "$HARNESS_CANARY"')
+        body.append('cat "%s"' % data)
+        if sleep_after:
+            body.append("sleep 60")
+        exe = self.root / "bin" / "claude"
+        exe.write_text("\n".join(body) + "\n", encoding="utf-8")
+        exe.chmod(0o755)
+
+    def run_claude(self):
+        task = H.Task(id="task-001", title="t", goal="g", verify="true", estimate_minutes=5)
+        ctx = D.TaskContext(repo=H.Repo(self.root / "repo"), domain=H.Domain({}), night_id="night-001",
+                            task=task, state=H.TaskState(id="task-001"), attempt=1,
+                            timeout_minutes=0.3, deadline_epoch=time.time() + 600, spec_text="")
+        stream = self.root / "repo" / ".harness" / "sessions" / "night-001" / "task-001.1.stream.jsonl"
+        return D.run_claude(ctx, "p", "s", stream), stream
+
+    def test_canary_present_runs_to_completion(self):
+        self.fake_claude([self.ASSISTANT, self.RESULT], touch_canary=True)
+        run, stream = self.run_claude()
+        self.assertEqual((run.hooks_dead, run.ok, run.saw_result, run.error), (False, True, True, ""))
+        self.assertTrue(stream.with_suffix(".canary").exists())
+
+    def test_canary_two_lines_reports_double_fire_but_survives(self):
+        self.fake_claude([self.ASSISTANT, self.RESULT], touch_canary=False, double_fire=True)
+        run, _ = self.run_claude()
+        self.assertEqual((run.hooks_dead, run.ok, run.hook_fires), (False, True, 2))  # 훅은 살아 있다 — 기록만
+
+    def test_canary_missing_kills_immediately_even_with_stale_file(self):
+        self.fake_claude([self.ASSISTANT, self.RESULT], touch_canary=False, sleep_after=True)
+        # 이전 시도의 카나리아가 남아 있어도 생존으로 위장하면 안 된다 — 드라이버가 시작 전에 지운다
+        stale = self.root / "repo" / ".harness" / "sessions" / "night-001" / "task-001.1.stream.canary"
+        stale.parent.mkdir(parents=True, exist_ok=True)
+        stale.write_text("stale\n", encoding="utf-8")
+        run, stream = self.run_claude()
+        self.assertTrue(run.hooks_dead)
+        self.assertFalse(run.ok)
+        self.assertFalse(run.timed_out)  # 시간 초과가 아니라 카나리아 판정으로 죽었다
+        self.assertIn("카나리아", run.error)
+        self.assertLess(run.seconds, 10.0)  # sleep 60 을 기다리지 않고 즉시 죽인다
+
+
 if __name__ == "__main__":
     unittest.main()
diff --git a/tests/test_e2e.py b/tests/test_e2e.py
index 0ddac67..934be12 100644
--- a/tests/test_e2e.py
+++ b/tests/test_e2e.py
@@ -105,6 +105,8 @@ class NightE2E(unittest.TestCase):
         self.assertIn("# night-001", summary)
         self.assertIn("완료 2 / 실패(재시도 예정) 0 / 막힘 2 / 미착수 0", summary)
         self.assertIn("doom loop 의심: task-003 같은 파일 9회 편집 (notes.txt)", summary)
+        self.assertIn("## 계획 DAG", summary)
+        self.assertIn("task001 --> task002", summary)  # depends_on 이 엣지로
         self.assertIn("## task-003", repo.blocked.read_text())
         self.assertTrue((repo.sessions / "night-001" / "task-003.1.stream.jsonl").exists())
         self.assertFalse((repo.sessions / "lock").exists())
@@ -167,6 +169,47 @@ class NightE2E(unittest.TestCase):
         self.assertIn("머신이 잠듦 (밤 중단)", summary)
         self.assertIn("머신 잠듦 5m00s: task-001", summary)
 
+    def test_cost_budget_ends_night(self):
+        tasks = [
+            {"title": "[add-mul][cost:12] mul 추가", "goal": "mul", "verify": "python3 -c \"import calc; assert calc.mul(3,4)==12\"", "estimate_minutes": 5, "priority": 2},
+            {"title": "[add-sub] sub 추가", "goal": "sub", "verify": "python3 -c \"import calc; assert calc.sub(3,4)==-1\"", "estimate_minutes": 5, "priority": 1},
+        ]
+        make_repo(self.root, tasks=tasks, domain={"budget": {"hours": 0.5, "max_attempts": 3, "max_night_usd": 10}})
+        p = self.night()
+        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)  # 비용 상한은 시간 예산과 같은 정상 종료다
+        repo = H.Repo(self.root)
+        events = H.read_log(repo.log)
+        self.assertEqual(events[-1]["reason"], "cost_budget")
+        self.assertEqual(events[-1]["cost_usd"], 12.0)
+        started = [e["task"] for e in events if e["event"] == "task_started"]
+        self.assertEqual(started, ["task-001"])  # 두 번째 작업은 시작도 못 한다
+        _, tasks = H.load_plan(repo)
+        st = H.derive_states(events, tasks)
+        self.assertEqual(st["task-001"].state, "passed")   # 상한 판정은 다음 선택 전 — 이미 산 시도는 버리지 않는다
+        self.assertEqual(st["task-002"].state, "pending")
+        self.assertIn("종료: 비용 상한 도달", repo.summary.read_text())
+
+    def test_rate_limit_stop_ends_night(self):
+        tasks = [
+            {"title": "[add-mul] mul 추가", "goal": "mul", "verify": "python3 -c \"import calc; assert calc.mul(3,4)==12\"", "estimate_minutes": 5, "priority": 2},
+            {"title": "[add-sub] sub 추가", "goal": "sub", "verify": "python3 -c \"import calc; assert calc.sub(3,4)==-1\"", "estimate_minutes": 5, "priority": 1},
+        ]
+        make_repo(self.root, tasks=tasks)  # 기본값 rate_limit_stop=0.85
+        self.env["HARNESS_FAKE_RATE"] = "0.95"
+        p = self.night()
+        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
+        repo = H.Repo(self.root)
+        events = H.read_log(repo.log)
+        self.assertEqual(events[-1]["reason"], "rate_limited")
+        started = [e["task"] for e in events if e["event"] == "task_started"]
+        self.assertEqual(started, ["task-001"])
+        _, tasks = H.load_plan(repo)
+        st = H.derive_states(events, tasks)
+        self.assertEqual(st["task-001"].state, "passed")   # 판정이 끝난 뒤에 멈춘다 — 시도를 버리지 않는다
+        summary = repo.summary.read_text()
+        self.assertIn("종료: 5시간 창 사용률 상한 도달", summary)
+        self.assertIn("5시간 창 사용률 최대 95%", summary)
+
     def test_queue_unblock(self):
         make_repo(self.root, tasks=[PLAN[2]])  # hopeless → 3회 실패 → blocked
         self.assertEqual(self.night().returncode, 0)
diff --git a/tests/test_harnesslib.py b/tests/test_harnesslib.py
index 1c207ff..62974a7 100644
--- a/tests/test_harnesslib.py
+++ b/tests/test_harnesslib.py
@@ -286,5 +286,35 @@ class SummaryTests(unittest.TestCase):
         self.assertIn("종료: 머신이 잠듦 (밤 중단)", H.render_summary(c))
 
 
+class PlanDagTests(unittest.TestCase):
+    def test_render_plan_dag_nodes_edges_badges(self):
+        tasks = [task("task-001", "[add-mul] mul 추가"), task("task-002", "sub", deps=("task-001",)), task("task-003", "c")]
+        states = {"task-001": H.TaskState(id="task-001", state="passed"),
+                  "task-002": H.TaskState(id="task-002", state="blocked"),
+                  "task-003": H.TaskState(id="task-003", state="pending")}
+        dag = H.render_plan_dag(tasks, states)
+        self.assertIn("```mermaid", dag)
+        self.assertIn('task001["✅ task-001 add-mul mul 추가"]', dag)  # 대괄호 등 mermaid 특수문자는 라벨에서 제거
+        self.assertIn('task002["⛔ task-002 sub"]', dag)
+        self.assertIn('task003["⬜ task-003 c"]', dag)
+        self.assertIn("task001 --> task002", dag)
+        self.assertEqual(H.render_plan_dag([task(None, "id 없음")], {}), "")  # id 미발급 계획은 그리지 않는다
+
+    def test_summary_contains_dag_and_double_fire_anomaly(self):
+        tasks = [task("task-001", "a"), task("task-002", "b", deps=("task-001",))]
+        n = "night-010"
+        events = [
+            ev("night_started", night=n),
+            ev("model_done", night=n, task="task-001", attempt=1, turns=3, cost_usd=0.1, hook_fires=2),
+            ev("task_passed", night=n, task="task-001", attempt=1, commit="abc"),
+            ev("night_ended", night=n, reason="queue_empty"),
+        ]
+        c = H.collect_night(events, tasks, H.Domain({}), n)
+        self.assertIn("훅 이중 발화 2회: task-001", "\n".join(c["anomalies"]))
+        s = H.render_summary(c)
+        self.assertIn("## 계획 DAG", s)
+        self.assertIn("task001 --> task002", s)
+
+
 if __name__ == "__main__":
     unittest.main()
diff --git a/tests/test_hooks.py b/tests/test_hooks.py
index 3d6bda4..2f30516 100644
--- a/tests/test_hooks.py
+++ b/tests/test_hooks.py
@@ -65,8 +65,10 @@ class HookTests(unittest.TestCase):
             p = subprocess.run(SH + [RUN_HOOK, "session-start"], input=json.dumps({"cwd": other}), capture_output=True, text=True, encoding="utf-8")
             self.assertEqual((p.returncode, p.stdout), (0, ""))
 
-    def test_commit_push_denied_in_both_modes(self):
-        self.assertEqual(self.bash("git commit -m 'x'"), "deny")
+    def test_commit_push_denied_only_in_runner_mode(self):
+        self.assertIsNone(self.bash("git commit -m 'x'"))                                 # 대화형: 사람이 승인 루프에 있다 (S2)
+        self.assertIsNone(self.bash("git push origin work"))
+        self.assertEqual(self.bash("git commit -m 'x'", runner=True), "deny")
         self.assertEqual(self.bash("git add . && git push origin main", runner=True), "deny")
         self.assertIsNone(self.bash("git status && git diff"))
 
@@ -112,6 +114,14 @@ class HookTests(unittest.TestCase):
         for needle in ("1. 작업 디렉토리", "2. 최근 로그", "3. 현재 작업 (P2가 결정", "task-001", "4. 스모크", ": ok", "5. 기존 문제"):
             self.assertIn(needle, ctx)
 
+    def test_session_start_writes_canary(self):
+        canary = self.root / ".harness" / "sessions" / "night-001" / "task-001.1.stream.canary"
+        canary.parent.mkdir(parents=True)
+        self.hook("session-start", {"source": "startup"}, runner=True, HARNESS_CANARY=str(canary))
+        self.assertTrue(canary.exists())  # 존재 = 플러그인 훅 생존 증명 — 드라이버가 첫 assistant 이벤트에서 확인한다
+        self.hook("session-start", {"source": "startup"}, runner=True, HARNESS_CANARY=str(canary))
+        self.assertEqual(len(canary.read_text().splitlines()), 2)  # append — 줄 수 = 발화 횟수 (이중 발화 감지 재료)
+
     def test_session_start_runner_mode_reads_smoke_from_log(self):
         H.append_event(self.root / ".harness" / "log.jsonl", "smoke", night="night-001", ok=False, exit=1, seconds=0.2, cmd=".harness/verify")
         H.append_event(self.root / ".harness" / "log.jsonl", "task_started", night="night-001", task="task-001", attempt=1)
-- 
2.50.1 (Apple Git-155)

`````
