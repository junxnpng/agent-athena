# Codex 시작 이벤트와 훅 완료 순서

- 발견: Codex CLI 0.154.0 비대화형 드라이버를 임시 Git 저장소에서 검증했다.
- 증상: `turn.started`를 받자마자 카나리아를 확인하면 정상 훅도 미로드로 판정했다.
- 피해: 모델 작업을 시작하기 전에 실행이 중단됐다. 검증용 임시 저장소에서만 발생했다.
- 원인: 실제 JSONL에서 `turn.started`는 SessionStart 훅 완료보다 먼저 전달된다.
  시작 이벤트 시점에는 카나리아가 없었고 첫 agent_message 시점에는 생성돼 있었다.
- 해소: 첫 모델 활동(`item`의 agent_message/command_execution/file_change/reasoning) 또는
  `turn.completed` 시점에 카나리아를 확인한다. 경고 item은 모델 활동으로 세지 않는다.
- 재발 방지: `test_turn_started_can_precede_session_start_hook`이 이 순서를 재현한다.
  훅 누락·이전 실행 카나리아가 있는 경우의 중단 테스트도 유지한다.
- 가정 변경: 세션 시작 알림과 시작 훅 완료는 같은 시점이 아니다. 런타임별 이벤트 순서를 확인한다.
- 일반화: 실행 시작 이벤트는 모든 준비 절차가 끝났다는 증명이 아니다.
