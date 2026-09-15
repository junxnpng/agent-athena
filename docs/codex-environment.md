# Codex 환경 이식 보고서

## 기준 저장소

| 로컬 저장소 | HEAD | 마지막 커밋 시각 | 상태 |
| --- | --- | --- | --- |
| `~/workspace/agent-athena` | `9bd1d64` | 2026-08-31 12:18 KST | 비교 시 변경 없음 |
| `~/workspace/agent-athena2` | `4c55f04` | 2026-09-06 09:26 KST | 비교 시 변경 없음, 이번 이식 대상 |
| `~/workspace/agent-athena3` | `9bd1d64` | 2026-08-31 12:18 KST | 비교 시 변경 없음 |

`agent-athena2`는 다른 두 복제본의 HEAD를 포함하고 한 커밋 앞선다.
추가 커밋은 9개 파일을 변경했으며 무변경 시도의 검증 생략·시도 소진,
실패 이력 안내, refine-lite 교훈 제안 및 테스트를 포함한다. 원격 fetch 없이 로컬 이력을 비교했다.

## 적용

- Codex CLI 0.154.0의 `harness-local` 원본을 `agent-athena`에서 `agent-athena2`로 변경.
- 기존 사용자 설정은 `~/.codex/config.toml.before-athena2`에 백업.
- 기존 `AGENTS.md → CLAUDE.md` 링크 및 `skills/`를 재사용.
- 기존 Claude 플러그인 형식을 Codex 호환 로더로 설치. 사양의 별도 생성 매니페스트 없이 설치 가능함을 실제 CLI로 확인.
- `apply_patch`의 모든 대상 경로와 이동 목적지를 기존 쓰기 범위·부기 파일·읽기 전용 검사에 연결.
- Claude 환경과 다른 두 복제본은 유지. 커밋·push는 수행하지 않음.

## 사용 및 한계

새 Codex 대화를 `agent-athena2`에서 시작한다. CLI `/hooks`에서 harness의
SessionStart와 PreToolUse의 실제 명령을 검토하고 두 훅만 신뢰·활성화했다. 다른 플러그인의 훅 신뢰 상태는 유지했다. 이후 훅 정의가 바뀌면 다시 검토해야 한다. 설치 자체와 훅 신뢰는 별개다.
공식 문서에 따르면 플러그인 훅에는 `CLAUDE_PLUGIN_ROOT` 호환 변수가 제공되며,
Bash와 apply_patch는 `tool_input.command`를 전달한다.

밤샘 러너의 Codex 드라이버는 구현하지 않았다. 호스팅 웹 검색과 일부 도구 호출은 훅 밖이므로
이 구성만으로 I7을 보장할 수 없다. 대화형 환경 구성과 무인 실행 검증은 구분한다.

근거: [OpenAI 공식 Hooks 문서](https://learn.chatgpt.com/docs/hooks).

## 검증

- Codex CLI 설치 성공: `harness@harness-local`, 버전 `0.1.0`, 활성화 상태 확인.
- 설치본의 hooks/runner/skills 112개 파일이 원본과 일치, 스킬 28개 확인.
- 새 회귀 테스트 3개에서 기존 누락을 확인한 뒤 패치 경로 차단 테스트 통과.
- CLI `/hooks`에서 harness의 PreToolUse와 SessionStart를 개별 신뢰하고 활성 상태 확인.
- 전체 `scripts/check`: 141개 테스트 통과(197초), portable-lint 및 dash 실행 검증 통과. 로그: `/tmp/athena-codex-check.log`. Ubuntu OS에서 직접 실행한 검증은 아님.
