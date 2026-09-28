# Matt Pocock skills 목록

## 범위

- 원본: `../../skills/` (이 문서 기준 상대 경로).
- 로컬 `skills/**/SKILL.md` 실측: **38개**.
- 기본 Claude 플러그인 포함: **25개** (Engineering 18개 + Productivity 7개).
- 실험 스킬 9개와 기타 스킬 4개는 기본 플러그인에서 제외.
- 로컬 파일의 정의를 요약한 목록이며, 설치·실행 검증이나 최신 upstream 상태 확인은 포함하지 않는다.

## 목록

### 개발 — 18개

| 스킬 | 용도 | 기본 플러그인 |
|---|---|---|
| [ask-matt](../../skills/skills/engineering/ask-matt/SKILL.md) | 상황에 맞는 스킬·작업 흐름 안내 | 포함 |
| [code-review](../../skills/skills/engineering/code-review/SKILL.md) | 저장소 규칙과 원래 사양 두 축으로 리뷰 | 포함 |
| [codebase-design](../../skills/skills/engineering/codebase-design/SKILL.md) | 작은 인터페이스와 깊은 모듈 설계 | 포함 |
| [diagnosing-bugs](../../skills/skills/engineering/diagnosing-bugs/SKILL.md) | 재현·축소·가설·계측 기반 버그 진단 | 포함 |
| [domain-modeling](../../skills/skills/engineering/domain-modeling/SKILL.md) | 도메인 용어·CONTEXT.md·ADR 정리 | 포함 |
| [grill-with-docs](../../skills/skills/engineering/grill-with-docs/SKILL.md) | 심층 질문과 도메인 용어·ADR 문서화 | 포함 |
| [implement](../../skills/skills/engineering/implement/SKILL.md) | 사양·티켓에 따라 구현 | 포함 |
| [improve-codebase-architecture](../../skills/skills/engineering/improve-codebase-architecture/SKILL.md) | 구조 개선 후보 조사·HTML 보고·설계 질문 | 포함 |
| [prototype](../../skills/skills/engineering/prototype/SKILL.md) | 설계 질문을 검증할 임시 프로토타입 제작 | 포함 |
| [research](../../skills/skills/engineering/research/SKILL.md) | 신뢰할 만한 출처 조사와 Markdown 기록 | 포함 |
| [resolving-merge-conflicts](../../skills/skills/engineering/resolving-merge-conflicts/SKILL.md) | 양쪽 변경 의도를 추적해 merge/rebase 충돌 해결 | 포함 |
| [setup-matt-pocock-skills](../../skills/skills/engineering/setup-matt-pocock-skills/SKILL.md) | 트래커·분류 라벨·문서 경로 초기 설정 | 포함 |
| [tdd](../../skills/skills/engineering/tdd/SKILL.md) | 작은 기능 단위의 Red–Green–Refactor | 포함 |
| [to-spec](../../skills/skills/engineering/to-spec/SKILL.md) | 대화를 사양으로 정리해 트래커에 게시 | 포함 |
| [to-tickets](../../skills/skills/engineering/to-tickets/SKILL.md) | 계획·사양을 의존성이 있는 작업 티켓으로 분해 | 포함 |
| [triage](../../skills/skills/engineering/triage/SKILL.md) | 이슈·외부 PR 분류, 검증, 작업 지시서 작성 | 포함 |
| [wayfinder](../../skills/skills/engineering/wayfinder/SKILL.md) | 여러 세션에 걸친 큰 작업의 의사결정 계획 | 포함 |
| [wizard](../../skills/skills/engineering/wizard/SKILL.md) | 사람이 직접 수행할 설정 절차를 셸 마법사로 제작 | 포함 |

### 생산성 — 7개

| 스킬 | 용도 | 기본 플러그인 |
|---|---|---|
| [grill-me](../../skills/skills/productivity/grill-me/SKILL.md) | 계획·아이디어를 구체화하는 심층 인터뷰 | 포함 |
| [grilling](../../skills/skills/productivity/grilling/SKILL.md) | 다른 스킬에서도 사용하는 공통 인터뷰 절차 | 포함 |
| [handoff](../../skills/skills/productivity/handoff/SKILL.md) | 다음 에이전트용 인계 문서 작성 | 포함 |
| [teach](../../skills/skills/productivity/teach/SKILL.md) | 작업 공간을 활용한 여러 세션의 학습 | 포함 |
| [to-questionnaire](../../skills/skills/productivity/to-questionnaire/SKILL.md) | 다른 담당자에게 물어볼 질문지 작성 | 포함 |
| [wait-what](../../skills/skills/productivity/wait-what/SKILL.md) | 이해되지 않은 설명을 맥락부터 다시 설명 | 포함 |
| [writing-for-agents](../../skills/skills/productivity/writing-for-agents/SKILL.md) | 에이전트용 지침·스킬·문서 작성 | 포함 |

### 실험 — 9개

| 스킬 | 용도 | 기본 플러그인 |
|---|---|---|
| [claude-handoff](../../skills/skills/in-progress/claude-handoff/SKILL.md) | 새 Claude 백그라운드 에이전트로 작업 인계 | 제외 |
| [implement-spec](../../skills/skills/in-progress/implement-spec/SKILL.md) | 사양 전체를 작업 그래프로 실행하고 PR로 통합 | 제외 |
| [loop-me](../../skills/skills/in-progress/loop-me/SKILL.md) | 여러 세션에서 워크플로 사양 구체화 | 제외 |
| [pr](../../skills/skills/in-progress/pr/SKILL.md) | 근거·변경 전후·범위를 담은 PR 본문 작성 | 제외 |
| [retro](../../skills/skills/in-progress/retro/SKILL.md) | 세션 후 에이전트 환경 개선 — 아직 설계 메모 수준 | 제외 |
| [setup-ts-deep-modules](../../skills/skills/in-progress/setup-ts-deep-modules/SKILL.md) | TypeScript 모듈 경계를 dependency-cruiser로 검사 | 제외 |
| [writing-beats](../../skills/skills/in-progress/writing-beats/SKILL.md) | 글의 흐름을 단계별로 구성 | 제외 |
| [writing-fragments](../../skills/skills/in-progress/writing-fragments/SKILL.md) | 인터뷰로 글쓰기 재료 수집 | 제외 |
| [writing-shape](../../skills/skills/in-progress/writing-shape/SKILL.md) | 수집한 재료를 문단 단위의 글로 구성 | 제외 |

### 기타 — 4개

| 스킬 | 용도 | 기본 플러그인 |
|---|---|---|
| [git-guardrails-claude-code](../../skills/skills/misc/git-guardrails-claude-code/SKILL.md) | 위험한 Git 명령을 막는 Claude 훅 설정 | 제외 |
| [migrate-to-shoehorn](../../skills/skills/misc/migrate-to-shoehorn/SKILL.md) | 테스트의 as 단언을 shoehorn으로 전환 | 제외 |
| [scaffold-exercises](../../skills/skills/misc/scaffold-exercises/SKILL.md) | 교육용 문제·풀이·설명 디렉터리 생성 | 제외 |
| [setup-pre-commit](../../skills/skills/misc/setup-pre-commit/SKILL.md) | Husky·lint-staged·포맷·타입·테스트 검사 설정 | 제외 |

## Codex·Claude 사용 범위

- 38개 스킬 모두 `agents/openai.yaml`을 포함한다.
- Claude 플러그인 배포와 Codex 등의 파일 설치 방식을 구분한다.
- 사용자 명시 호출 전용 스킬은 자동 호출이 제한된다. 실제 호출 정책은 각 스킬의 frontmatter와 `agents/openai.yaml`을 확인한다.
- `in-progress`는 베타이며 변경·제거될 수 있다. 특히 `retro`는 README상 아직 기능이 완성되지 않은 설계 메모다.
- Claude 훅·백그라운드 CLI 또는 TypeScript 도구에 의존하는 스킬은 대상 환경에 맞는 준비가 필요하다.

## agent-athena와의 관계

- 이름이 같은 스킬 11개: `domain-modeling`, `grilling`, `handoff`, `improve-codebase-architecture`, `research`, `retro`, `teach`, `to-spec`, `to-tickets`, `wait-what`, `writing-for-agents`.
- Athena의 `review-changes`는 이식 대장상 원본 `code-review`를 이름 변경한 스킬이다.
- 이름이 같아도 버전·본문·수정 내역이 같다는 뜻은 아니다. Athena는 고정 커밋 감사 후 선별 이식한다.

## 근거

- [원본 README](../../skills/README.md)
- [플러그인 포함 목록](../../skills/.claude-plugin/plugin.json)
- [실험 스킬 상태](../../skills/skills/in-progress/README.md)
- [Athena 이식 대장](../skills/vendor/VENDORED.md)
