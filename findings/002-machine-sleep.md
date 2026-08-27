# 002 · 머신이 잠들면 밤이 통째로 탄다 — `caffeinate -i`는 유휴 잠자기만 막는다

- **발견**: night-002 (GreedyAtena, 2026-08-27 23:41 → 08-28 00:36, opus, 무인). `pmset -g log`: `23:43:42 Entering Sleep state due to 'Software Sleep'` — task-004 시작 52초 뒤(뚜껑/메뉴 잠자기). 이후 DarkWake(15~17분 간격, 1분 남짓)에서만 러너가 진행. 로그: 10분 상한 시도가 17~20분, `model_done.turns=0`(집계 착시 → 003).
- **증상**: 55분 예산 중 유효 작업 시간 ~3분. 시도 3개가 "시간 초과"로 실패 처리되고 task-004(news)가 **부당하게 blocked**. 드라이버 타임아웃이 `time.time()` 기반이라 잠든 시간이 모델 시간으로 계산됐다. 러너는 잠듦을 전혀 몰랐다.
- **피해**: task-004 부당 차단(`queue unblock`으로 해제). 비용 $0 — 모델은 잠든 동안 돌지 않았다. 사람은 아침에 "모델이 hang했다"고 오독할 뻔했다.
- **원인**: 무인 실행의 전제 "머신이 깨어 있다"를 아무 컴포넌트도 검사하지 않았다. `caffeinate -i`는 *idle* sleep 전용이고, 소프트웨어/뚜껑 잠자기는 사용자 공간에서 막을 수 없다.
- **해소** (커밋: 이 파일과 같은 커밋): (1) 드라이버가 벽시계−단조시계 차로 잠든 시간을 측정 → `model_done.slept_seconds` (2) 120초 이상이면 시도 무효(`task_failed infra=true`, 실패 횟수 미산입) + 밤 종료 `machine_slept` (3) 타임아웃 루프를 단조시계로 — 잠든 시간을 모델 시간으로 세지 않는다 (4) 부당 차단 해제용 `runner/queue unblock` (5) 무응답(시간 초과 + 0턴) 2연속이면 `driver_unhealthy`로 종료.
- **재발 방지**: `tests/test_e2e.py::test_machine_sleep_ends_night_without_consuming_attempts`, `test_queue_unblock` · `tests/test_harnesslib.py::InfraTests`
- **가정 변경**: ASSUMPTIONS 새 행 "잠듦 감지", "인프라 실패 분리".
- **일반화**: 무인 실행의 *환경* 전제도 가정이다 — 막을 수 없으면 **감지해서 조기에 끝내고 아침에 크게 말한다**. 인프라 실패(잠듦·무응답)를 작업 실패와 같은 카운터에 넣으면 무고한 작업이 막힌다. 운영: 맥북은 전원 연결 + 뚜껑 열어두기, 가능하면 Ubuntu 서버.
