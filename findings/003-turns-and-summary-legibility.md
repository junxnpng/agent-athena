# 003 · "0턴" 착시와 읽히지 않는 SUMMARY 오류 줄

- **발견**: night-002. `model_done.turns=0, cost_usd=0`이라 "무응답"으로 읽혔으나 스트림에는 assistant 메시지 8~9개·thinking·`api_retry`가 있었다(느렸을 뿐, 그리고 002의 잠듦). SUMMARY의 "마지막 오류: `0`" — `count_passed`가 마지막에 찍는 숫자 줄을 기계적으로 인용. 이상 징후에 시간 초과가 "모델 시간 초과" + "드라이버 오류" 두 줄로 중복.
- **증상 / 피해**: 아침 5분 안에 상황 파악 실패(P10 목표 위반). 진단하려면 스트림 파일을 직접 열어야 했다.
- **원인**: `turns`를 `result` 이벤트의 `num_turns`에서만 읽었다 — 시간 초과면 result가 없다. 요약이 출력 꼬리의 *마지막* 줄을 인용했다.
- **해소**: assistant 메시지 수를 세어 result가 없으면 그것을 턴 수로 · 시간 초과는 한 줄로(턴·비용, "0턴 = 무응답" / "느림 — 상한을 올리거나 작업을 쪼갠다" 구분) · 오류처럼 보이는 첫 줄 인용(ANSI 제거) · 막힘 항목에 마지막 시도의 사유 표기 · 5시간 창 사용률 표시(밤 중 최대 67%였다).
- **재발 방지**: `tests/test_drivers.py::IngestTests`, `tests/test_harnesslib.py::SummaryTests::test_anomalies_distinguish_slow_hang_and_sleep`, `InfraTests::test_error_line_prefers_error_looking_line`
- **가정 변경**: 없음 (P10 구현 품질).
- **일반화**: 아침 산출물은 "무엇이 일어났나"가 아니라 **"무엇을 해야 하나"**가 읽혀야 한다. 숫자 하나가 두 뜻(무응답 vs 느림)을 가지면 갈라서 쓴다.
