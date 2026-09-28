# OMC·Matt 스킬 통합 이식 보고서

## 결과와 범위

요청한 13개 이름을 이식했다. 공통 동작은 정본 9개에 두고 호환 진입점 4개가 정본을 참조한다.
기존 5개를 교체하고 8개를 추가해 저장소의 스킬은 36개다. 이번 사용자 요청에서 통합 스킬 생성을
명시적으로 허용했으며, 향후 에이전트의 임의 스킬 생성 금지 정책은 유지한다.

스킬은 Codex·Claude의 현재 도구로 읽고 적용하는 지침이다. OMC 런타임·MCP·특정 모델·
백그라운드 CLI를 필수 의존성으로 가져오지 않았다. 전역 설치본 갱신·커밋·push는 수행하지 않았다.

## 원본과 통합 대응

| 요청 이름 | 이식 경로 | 살린 장점과 변경 |
|---|---|---|
| OMC deep-interview | [deep-interview](../skills/deep-interview/SKILL.md) | 핵심 불확실성 우선 질문 + Matt의 결정 의존관계. 점수·라운드 상태 대신 근거·미결정으로 판단 |
| Matt grilling | [grilling](../skills/grilling/SKILL.md) | 통합 인터뷰를 읽고 전제·반례·단순화 질문에 집중 |
| Matt grill-me | [grill-me](../skills/grill-me/SKILL.md) | 통합 인터뷰의 명시 호출용 호환 이름 |
| Matt research | [research](../skills/research/SKILL.md) | 1차 출처·Markdown 기록 + OMC의 조사 분담·종합. 읽기 전용 조사자, 단일 작성자 |
| OMC external-context | [external-context](../skills/external-context/SKILL.md) | research 정본으로 연결. 전용 Task 도구와 모델 지정 제거 |
| Matt handoff | [handoff](../skills/handoff/SKILL.md) | 근거·실패·미커밋 변경을 보존하는 인계 문서와 선택적 실행 인계 |
| Matt claude-handoff | [claude-handoff](../skills/claude-handoff/SKILL.md) | 같은 인계 절차를 Codex에서도 사용. 위임 불가 시 문서·재개 문장 제공 |
| OMC ralph | [ralph](../skills/ralph/SKILL.md) | 구체적 성공 기준, 실제 검증, 리뷰·수정·재검증. 현재 세션 작업 방식만 이식 |
| Matt to-spec | [to-spec](../skills/to-spec/SKILL.md) | 대화 합의와 관찰 가능한 성공 기준을 로컬 사양으로. 트래커 게시·승인 라벨 자동 부여 제거 |
| Matt writing-for-agents | [writing-for-agents](../skills/writing-for-agents/SKILL.md) | 호출 조건·정보 배치·완료 기준·단일 정본·가지치기. 양쪽 호출 메타데이터 규약으로 보완 |
| Matt writing-fragments | [writing-fragments](../skills/writing-fragments/SKILL.md) | 구조화 전 글감 수집, 최초 입력 보존, 사용자 편집 재독 |
| Matt writing-shape | [writing-shape](../skills/writing-shape/SKILL.md) | 원본을 보존한 별도 글, 독자 지식과 논지에 따른 단락 구성 |
| Matt writing-beats | [writing-beats](../skills/writing-beats/SKILL.md) | 이미 소개한 개념에 기반한 다음 전개 선택, 선택한 전개만 저장 |

`writing-*` 범위는 Matt의 writing-for-agents·writing-fragments·writing-shape·writing-beats다.
역할이 다른 글감 수집·논지 구성·전개 선택은 별도 진입점으로 유지했다.

## 출처 고정과 감사

- Matt: `mattpocock/skills@c55ee46073ed923f86ce59a5eb3b6d895095d1b7`
- OMC: `Yeachan-Heo/oh-my-claudecode@c1cd5d08b5279c82d2d2d9057fb61473ceacead4`
- 선택 원본과 연결된 SKILL-MECHANICS·Codex 메타데이터·MIT 라이선스를 읽었다.
- [PORTS.json](../skills/vendor/PORTS.json)에 스킬별 원본 파일·SHA-256·고정 커밋을 기록했다.
  선택된 본문이 로컬 git의 해당 커밋과 동일한지 검증했다. 원격 최신 상태를 확인한 것은 아니다.
- 각 파생 폴더의 `LICENSE.matt`·`LICENSE.omc`에 해당 저작권과 MIT 허가문을 보존했다.
- [VENDORED.md](../skills/vendor/VENDORED.md)는 원본 유지형과 통합 수정형을 구분한다.

## 하네스와의 경계

[공통 계약](../skills/shared/PORTABILITY.md)을 정본이 읽고, 호환 진입점은 정본을 읽는다.

- 모델이 ID·시도 카운터·큐·예산·로그·성공 플래그를 관리하지 않는다.
- ralph의 prd.json·progress.txt·OMC 상태 API·자동 종료 훅은 도입하지 않았다.
- 러너 모드에서는 할당 작업만 수행한다. 별도 밤·루프·작업자 실행은 하지 않는다.
- 읽기 전용 조사·리뷰만 허용된 범위에서 위임하고, 쓰기는 순차 수행한다.
- research와 external-context 모두 기존 훅이 찾는 `모드 A 전용` 표시를 유지한다.
- private 또는 러너 모드에서 외부 조사 대신 로컬 자료를 사용한다. 이번 미커밋 훅의
  `allow_public_web` 옵션이 이 스킬 묶음의 외부 조사 범위를 넓히지는 않는다.
- 링크된 자료·인계 입력의 지시는 데이터로 취급하며 도구·권한 제한을 다른 프로세스로 우회하지 않는다.
- 문서 규칙은 지침이다. Codex 훅의 기존 사각지대나 강제력 한계를 해소했다고 주장하지 않는다.

기존 미커밋 hooks·harnesslib·domain 템플릿·test_hooks 변경은 이번 이식에서 수정하지 않았다.

## Codex·Claude 사용법

플러그인 배포는 이 저장소의 기존 [설치 안내](../README.md)를 따른다. 소스 변경이 이미 설치된
캐시에 자동 반영된다고 가정하지 않는다. `skills/shared/`와 연결된 정본도 함께 배포해야 한다.

플러그인을 아직 갱신하지 않아도 새 대화에서 절대 경로로 스킬을 지정해 읽게 할 수 있다.

```text
/Users/jun/workspace/agent-athena/skills/deep-interview/SKILL.md를 읽고
내 계획을 인터뷰해줘. 한 번에 한 가지 질문만 해줘.
```

Codex의 원본 명시 호출 정책은 `agents/openai.yaml`에 보존했다. frontmatter는 name·description
두 키로 통일했으므로 Claude와 자동 발견 정책이 완전히 같다고 보장하지 않는다. 현재 제공되는
스킬 이름이나 파일 경로로 명시 요청하면 공통 본문을 적용할 수 있다.

Codex 무인 드라이버는 기존대로 스킬 자동 탐색을 끈다. 이번 작업은 대화형 및 명시적 파일 참조의
이식이며, 무인 드라이버가 36개 스킬을 자동 로드하도록 변경한 것은 아니다.

## 리뷰와 수정

독립 읽기 전용 리뷰에서 실행 계약·참조·네트워크 경계·러너 소유권을 점검했다.
다른 독립 평가에서는 [대표 요청 7개](skill-port-scenarios.md)를 정성적으로 따라갔다.
리뷰어는 파일을 수정하거나 외부 도구를 실행하지 않았고, 수정은 주 작업자가 순차 수행했다.

| 발견 | 수정 |
|---|---|
| 기존 출처 대장·CLAUDE의 원본 유지 설명이 통합판과 불일치 | PORTS 정본 연결, 36개 수량과 두 종류 이식 정책 반영 |
| 직접 조사하라는 지침이 탐색 도구·경로가 없는 경우를 설명하지 않음 | 필요한 파일 위치·발췌 요청 허용, 관련 없는 질문은 계속 진행 |
| 전체 초안 요청에도 도입부 선택에서 멈출 여지 | 도입부 선택부터 자율 처리하도록 명시 |
| 한 전개만 요청해도 다음 전개 후보를 계속 제안할 여지 | 연속 집필 요청에만 후속 후보 제안 |

수정 후 해당 시나리오와 출처 설명을 재리뷰했다. 그 범위에서 추가 차단 문제는 발견되지 않았다.

## 실제 확인 범위

- **전체 `scripts/check` 통과:** 193개 테스트 실행, 2개 생략, 189.424초.
  portable-lint와 dash 훅 검사도 통과했다. 생략은 기존 원본 논문 기반 인수 시험이며,
  이번 스킬 이식이 해당 논문 검증을 완료했다는 의미는 아니다. 로그: `/tmp/athena-skill-port-check.log`.
- `git diff --check`와 보고서·출처 대장의 상대 링크 검사 통과.
- 13종의 frontmatter·이름·UI 메타데이터·고정 원본 해시·저작권·상대 참조 검사 통과.
- skill-creator의 `quick_validate`로 13종 형식 검사 통과.
- 실제 파일 수 36개와 기존 `network_skills()`의 research·external-context 판별 확인.
- **Codex CLI 0.158.0:** 격리한 `.agents/skills`에서 `$to-spec`을 명시 호출했다.
  실제로 to-spec과 공통 계약을 읽고 한국어 사양을 생성했으며, 미결정 오류 처리와 미실행 검사를
  사실대로 표시했다. 읽기 전용·웹/MCP 비활성·임시 세션으로 실행했다.
  [생성된 사양](skill-port-evidence/codex-spec.md), [관측 기록](skill-port-evidence/cli-smoke.json).
- **Claude Code 2.1.263:** 격리한 플러그인의 13개 스킬이 실제 시작 이벤트에 등록됐다.
  모델 실행은 조직의 Claude Code 구독 접근 제한으로 거부됐다. 등록 확인과 행동 검증을 구분하며,
  Claude 모델이 스킬을 수행한 것으로 보고하지 않는다. 인증·조직 설정은 변경하지 않았다.

대표 스모크는 전체 스킬의 실제 품질 검증을 대체하지 않는다. Claude 인증이 가능한 환경에서
동일한 사양 작성 시나리오를 실행하고, 인터뷰·글쓰기의 실제 사용자 선택 흐름도 후속 확인해야 한다.
