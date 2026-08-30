# 010 — 세션 Python 의 바이트코드 캐시가 트리 안에 떨어져 범위 위반이 됐다

- **발견** — 2026-08-31 00:34, athena-research night-002 task-021(실험 러너) 시도 1: `stage: scope`, 위반 경로 `Library/Caches/com.apple.python/Library/Developer/CommandLineTools/…/_bootlocale.cpython-39.pyc`. 시도 2 는 통과.
- **증상** — macOS 시스템 Python(CommandLineTools 3.9)은 읽기 전용 stdlib 의 .pyc 를 `$HOME/Library/Caches/com.apple.python/<원본 절대경로>` 에 쓴다. 세션 안의 어떤 명령이 HOME 을 트리 안으로 두었고(러너는 HOME 을 바꾸지 않는다 — 모델의 셸 명령으로 추정, 스트림에서 특정 못 함), 그 캐시가 repo 안에 생겨 러너의 최종 범위 판정(`changed_paths`, 기준선 없음)에 잡혔다.
- **피해** — 시도 하나(약 $2 · 8분) 소모, 되돌리기(`git clean`)가 캐시를 지워 트리는 깨끗. 통과한 작업 내용은 2차 시도에서 다시 만들어졌다.
- **원인** — 세션 환경이 "쓰기 범위 밖에 부산물을 남기지 않는다" 를 보장하지 않았다. 범위 판정은 정확했다(I6) — 환경이 판정을 오염시킨 것.
- **해소** — `drivers.build_env` 가 `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=<repo>/.harness/sessions/pycache` 를 세션 env 에 넣는다(sessions/ 는 gitignore 이고 범위 판정에서 제외). 테스트 `test_build_env_keeps_python_bytecode_out_of_the_tree`.
- **재발 방지** — 같은 부류(도구가 HOME·CWD 기준으로 남기는 캐시: pytest `.pytest_cache`, pip, npm)는 대상 repo 의 `.gitignore` 몫이다 — `runner/init` 골격의 gitignore 에 `.pytest_cache/`·`__pycache__/` 가 있는지 아침에 확인(미확인).
- **가정 변경** — ASSUMPTIONS "세션 환경 부산물" 행 추가.
