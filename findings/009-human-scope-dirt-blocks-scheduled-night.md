# 009 — 낮의 수집물(human_scope 미추적 파일)이 예약 밤을 막는다 (preflight 거부 · 범위 오판 · git clean 삭제)

- **발견** — 2026-08-30 낮. athena-ai-brief 에 "일요일 23:00 밤 → 월요일 07:00 주간 메일" 을 걸려다 코드를 읽어 확인. 06:30 스케줄러(`scripts/daily.py` → `collect.py`)는 `inbox/` 에 파일을 쓰지만 커밋하지 않고, `inbox/` 는 `human_scope`(write_scope 밖)다.
- **증상** — (a) `runner/night` preflight 는 `git status --porcelain` 이 비어 있지 않으면 "작업 트리가 clean 이 아니다" 로 거부한다 → 수집기가 한 번이라도 돈 뒤에는 예약 밤이 영원히 안 뜬다(월요일은 조용하다). (b) 거부가 없었다면: 범위 판정 `changed_paths()` 는 기준선 없이 `git status` 전체를 보므로 미추적 `inbox/*.md` 가 매 시도 `scope` 위반이 된다. (c) 실패 되돌리기 `revert_worktree` 의 `git clean -fd` 가 미추적 수집물을 지운다(사람 자료 소실).
- **피해** — 아직 없음(게이트 2b 전이라 스케줄러 미등록). 코드 읽기로 잡았다.
- **원인** — human_scope 를 도입할 때(리뷰 라운드 1) "낮에 사람이 넣는다" 만 생각했고 "낮에 *프로그램* 이 넣고 아무도 커밋하지 않는다" 를 빠뜨렸다. 커밋 정책 "러너만 커밋한다" 가 스케줄러 산출물에는 구멍이었다.
- **해소** — preflight: dirt 가 human_scope 안뿐이면 러너가 `[harness] human_scope 반입: N개 (inbox)` 로 커밋하고(`human_intake` 이벤트, 경로·sha) 시작한다. human_scope 밖 dirt 가 하나라도 섞이면 사람 작업으로 보고 전부 거부(아무것도 커밋하지 않는다). 이 커밋 — `harnesslib.human_scope_paths` · `Git.commit_paths` · `tests/test_e2e.py::test_human_scope_dirt_is_committed_by_preflight`.
- **재발 방지** — e2e 테스트가 "미추적 human_scope 파일 → 반입 커밋 → 밤 진행" 과 "섞이면 거부·미커밋" 둘 다 고정. 예약 밤은 `templates/launchd/com.harness.night.ai-brief.plist`(일요일 23:00 `night-loop` 3h·$10).
- **가정 변경** — ASSUMPTIONS 에 "human_scope 반입 커밋" · "예약 밤(launchd)" 행 추가. 한계로 고정: 반입 커밋은 HEAD 에 남는다 — HEAD 가 미병합 밤의 조상이면(사람이 main 을 체크아웃만 하고 병합하지 않은 상태) 다음 밤의 기점 판정이 "분기" 로 거부한다. 사람이 병합해서 푼다.
- **일반화** — 상태를 만드는 주체가 셋(사람·모델·프로그램)인데 커밋 주체는 하나(러너)면, 나머지 둘의 산출물이 어떻게 러너에게 닿는지 경로가 있어야 한다. "clean 이 아니면 거부" 는 사람 작업을 보호하지만 프로그램 산출물에는 데드락이다.
