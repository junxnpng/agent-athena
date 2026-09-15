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

위 대화형 구성만으로는 I7을 보장할 수 없다. 무인 실행은 아래의 별도 드라이버를 사용한다.

근거: [OpenAI 공식 Hooks 문서](https://learn.chatgpt.com/docs/hooks).

## 검증

- Codex CLI 설치 성공: `harness@harness-local`, 버전 `0.1.0`, 활성화 상태 확인.
- 설치본의 hooks/runner/skills 112개 파일이 원본과 일치, 스킬 28개 확인.
- 새 회귀 테스트 3개에서 기존 누락을 확인한 뒤 패치 경로 차단 테스트 통과.
- CLI `/hooks`에서 harness의 PreToolUse와 SessionStart를 개별 신뢰하고 활성 상태 확인.
- 전체 `scripts/check`: 141개 테스트 통과(197초), portable-lint 및 dash 실행 검증 통과. 로그: `/tmp/athena-codex-check.log`. Ubuntu OS에서 직접 실행한 검증은 아님.

## 무인 실행 드라이버

`runner/codex_driver.py`가 `codex exec --json`을 실행하고 기존 `ModelRun`으로 변환한다.
실제 작업·계획 제안·교훈 제안을 연결했으며, 검증·실패 패치 보존·되돌림·커밋은 기존 러너가 담당한다.
사용자 설정을 읽지 않고 플러그인/MCP/웹/위임을 끈다. 프로젝트 설정과 별도 훅의 혼입은 사전 거부한다.
실행마다 검토된 하네스 원본 훅을 주입한다. 일반 작업은 네트워크 없는 쓰기 샌드박스,
제안은 읽기 전용 샌드박스다. 셸 경로 검사는 휴리스틱이며 OS 경계와 러너 사후 검사를 함께 사용한다.

토큰 사용량은 로그 `usage`에 기록한다. Codex 비용은 `cost_known: false`이며,
기존 로그 작성기가 null 필드를 생략하므로 `cost_usd` 필드가 없을 수 있다.
달러·사용률·턴 제한은 명시적 null 해제가 필요하다. 시간·작업 수·실패 횟수로 실행을 제한한다.
`night-loop`는 `--max-total-usd 0`을 요구한다. 설정 예시는 README에 있다.

CLI 0.154.0에서는 `turn.started`가 SessionStart 완료보다 먼저 관측됐다.
훅 카나리아는 첫 모델 활동 또는 완료 이벤트에서 검사하며, 이전 실행의 카나리아는 지운다.
훅이 없으면 실행을 중단한다. CLI 시작 경고인 `item`의 `error`와 실제 `turn.failed`를 구분한다.

### 검증 범위

- 기존 대화형 변경: 이번 실행에서 `scripts/check` 141개 통과, 181.715초.
- 드라이버 테스트: JSONL 사용량·오류·완료 이벤트 누락·훅 누락·시간 초과·설정 혼입 검사.
- 임시 Git repo에서 정상 작업 커밋, 실패 패치 보존과 되돌림, SIGTERM 중단 복구 검사.
- 실제 Codex CLI에서 시작 훅 실행, 프로젝트 안 파일 추가와 밖 쓰기 차단 확인.
- 실제 Codex CLI에서 `.harness/` 파일 쓰기와 읽기 전용 세션의 패치 차단, 셸 파일 읽기 성공 확인.
  네트워크 시도는 DNS 오류로 연결되지 않았으며 이 관측만으로 모든 외부 통신 경로를 검증한 것은 아니다.
- 실제 `runner/night --driver codex`에서 `calc.mul()` 작업을 수행했다. 작업·전체 검증 후
  러너가 `14abbff`로 커밋했고 SUMMARY에 완료 1건·비용 미상이 표시됐다(임시 저장소, 모델 실행 약 52초).
- 루프가 남은 시간을 내부 밤에 전달하도록 수정했다. 명시한 더 짧은 밤 상한은 유지한다.
  최소 작업 시간보다 적게 남으면 새 밤을 시작하지 않는다. 검증·정리는 별도 타임아웃이다.
- Ubuntu OS에서 직접 실행한 검증은 수행하지 않았다.
- 최종 `scripts/check`: **158개 테스트 통과(199.187초)**. portable-lint와 dash 훅 실행 검증도 통과했다.
  로그: `/tmp/athena-codex-final-check.log`. Python 3.9 구문 검사와 `git diff --check`도 통과했다.
