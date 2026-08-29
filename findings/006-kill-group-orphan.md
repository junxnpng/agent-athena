# 006 — killpg 한 번은 fork 직후의 손자를 놓친다

- **발견** — 2026-08-29 리뷰. `tests/test_drivers.py::test_canary_missing_kills_immediately_even_with_stale_file` 가 3회 중 1회 61초(`assertLess(run.seconds, 10)`). 원시 재현: setsid 자식(`sh` → `sleep 60`)의 첫 출력을 읽자마자 `kill_group` → 30회 중 1회 그룹에 프로세스 1개 잔존(리더 `sh` 는 SIGTERM 으로 죽음). 순수 `killpg(SIGTERM)`·`killpg(SIGKILL)` 은 0/30.
- **증상** — 카나리아(훅 생존 증명) 부재를 감지해 "즉시 중단" 했는데 자식 `sleep` 이 stdout 파이프를 잡은 채 60초를 다 살았다. 실전이면 훅 없는 무방비 세션이 그만큼 더 돈다.
- **피해** — 아직 실전 밤에서 관측된 적은 없다(카나리아 부재 자체가 드물다). 테스트 스위트의 간헐 실패.
- **원인** — `os.killpg(pgid, SIGTERM)` 이 그룹 멤버를 순회하는 순간 `sh` 가 `sleep` 을 fork 하는 중이면 새 자식은 시그널을 받지 못한다. 옛 `kill_group` 은 리더가 죽으면(`proc.poll()`) 곧장 돌아와 잔존 프로세스를 다시 보지 않았고, killpg 가 ESRCH 면 아예 아무것도 하지 않았다.
- **해소** — `harnesslib.kill_group`: SIGTERM 은 그룹 + 리더 pid + `ps -A -o pid= -o pgid=` 로 찾은 그룹 잔존에 각각, 유예(기본 10초, 인자) 뒤 SIGKILL 을 두 번(첫 SIGKILL 과 동시에 fork 된 것까지). `run_shell` 의 두 번째 `communicate` 에 5초 상한.
- **재발 방지** — `tests/test_harnesslib.py::KillGroupTests`(SIGTERM 을 무시하는 손자 두 개가 0.5초 유예 뒤 전부 사라진다).
- **가정 변경** — ASSUMPTIONS "프로세스 그룹 청소".
- **일반화** — "그룹에 시그널 한 번" 은 스냅샷이다. 정리는 *관측 → 시그널 → 재관측* 루프여야 하고, 리더의 종료는 그룹의 종료가 아니다.
