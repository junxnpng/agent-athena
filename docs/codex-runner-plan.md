# Codex 실행 드라이버 구현 계획

목표: 기존 검증·되돌림·커밋 흐름에 Codex CLI 0.154.0의 비대화형 실행을 연결한다.
Python 3.9 표준 라이브러리, macOS/Ubuntu, 순차 쓰기 규칙을 유지한다.

## 구현과 검증

- [x] 기존 대화형 패치의 `scripts/check` 결과 확인 후 별도 커밋.
- [x] `tests/test_codex.py`: JSON 이벤트, 오류·시간 초과, 훅 누락, 권한·설정 격리,
  지원하지 않는 예산 제한을 실제 프로세스 경계에서 검증하는 실패 테스트 작성.
- [x] `runner/codex_driver.py`: CLI 점검, 제한된 실행 설정, JSONL 해석, 프로세스 종료 구현.
  외부 인터페이스는 `preflight(repo, domain)`과 `run(ctx, prompt, system_prompt, stream_path, readonly=False)`.
  실행 결과는 기존 `drivers.ModelRun`을 사용하고 토큰 사용량과 비용 제공 여부를 추가한다.
- [x] `runner/drivers.py`: task/propose/lessons를 연결. 제안은 읽기 전용 샌드박스.
- [x] `runner/night`, `runner/decompose`, `runner/harnesslib.py`: 비용 미상을 로그·요약에 표시.
  달러/사용률 제한을 적용할 수 없는 실행은 사전 거부하고 시간 제한으로만 실행할 수 있음을 명시한다.
- [x] `runner/night-loop`: 비용 미상 드라이버를 달러 상한으로 실행하지 못하게 거부.
- [x] 임시 Git 저장소에서 성공 커밋·실패 복구·중단을 통합 검증하고 실제 Codex 실행 확인.
- [x] README·가정·이식 보고서를 갱신하고 `scripts/check` 후 기능 커밋.

## 실행 계약

`codex exec --json --ephemeral --ignore-user-config --ignore-rules`를 사용한다.
사용자 플러그인·MCP·웹·위임을 끄고 네트워크 없는 샌드박스를 사용한다.
별도 hooks.json 및 프로젝트 Codex 설정이 실행 설정에 섞이는 경우 사전 거부한다.
검토된 로컬 하네스 훅만 명시적으로 주입하고 실행 시작 카나리아를 확인한다.
작업 성공 판정은 모델 자기 보고가 아니라 기존 검증기가 담당한다.

근거: [비대화형 실행](https://learn.chatgpt.com/docs/non-interactive-mode),
[훅](https://learn.chatgpt.com/docs/hooks), 설치된 CLI의 `exec --help`.

## 검증 중 발견한 수정

- SessionStart 완료 전에 전달되는 `turn.started`를 훅 완료로 해석하지 않는다(findings/015).
- 루프의 남은 시간을 각 밤에 전달하고 최소 작업 시간이 남지 않으면 중단한다(findings/016).

## 최종 검증

`scripts/check`: 158개 통과(199.187초), portable-lint·dash 검증 통과.
실제 Codex 작업의 검증·커밋, 보호 경로 차단과 읽기 전용 동작을 임시 저장소에서 확인했다.
