# 004 · 무인 세션이 사용자의 대화형 환경을 통째로 상속한다 — `--plugin-dir`는 추가이지 대체가 아니다

- **발견**: 2026-08-28, 스킬 자동 호출 실측 중. 헤드리스 `claude -p --plugin-dir <harness>` 세션의 `init` 이벤트에 플러그인 **35개**(사용자 전역 34 + harness). night-001·002의 무인 스트림 **8/8**에 `learning-output-style`·`explanatory-output-style`의 SessionStart 훅 컨텍스트("You are in 'learning' output style mode… identify opportunities where the user can write 5-10 lines… request contributions")가 들어갔고, **6/8 시도에서 모델이 `★ Insight` 블록을 실제로 출력**했다.
- **증상**: 무인 모델이 대화형 전용 지시를 받는다 — 교육용 블록 출력(토큰 낭비), "사용자가 쓸 코드를 남겨라"(무인에서는 작업을 안 끝내라는 뜻).
- **피해**: 실측 피해 0건(작업을 남긴 흔적 regex 0건). 위험은 실재 — 다음에 어떤 전역 플러그인·훅이 켜지든 밤에 그대로 실린다. 사람이 대화형 환경을 바꾸면 무인 밤의 행동이 조용히 바뀐다.
- **원인**: 러너가 `--plugin-dir`로 하네스를 *더했을* 뿐, user 설정 소스(`~/.claude/settings.json`의 `enabledPlugins`·훅·모델·스타일)를 *빼지* 않았다. 무인 실행의 컨텍스트는 명시적으로 빼지 않으면 사람의 환경을 상속한다.
- **해소** (커밋: 이 파일과 같은 커밋): `drivers.py`가 `--setting-sources project,local`(user 제외)을 넘긴다. 실측: 플러그인 1(harness) · 스킬 25 유지 · 스타일 훅 컨텍스트 0줄. `--bare`는 훅·키체인 읽기까지 꺼서 부적합(하네스 훅 I6·I7이 죽고 API 키 인증만 남는다). 대상 repo의 project/local 설정은 도메인 소유라 유지한다(GreedyAtena는 `permissions`뿐). 플래그가 없는 구버전 `claude`면 즉시 실패해 밤이 크게 끝난다 — 조용한 상속보다 낫다. 부수: 같은 실측에서 스킬 자동 호출이 확률적임이 드러나(sonnet 0/2, opus 1/1 `harness:brainstorming`) 스트림의 `Skill` tool_use를 세어 `model_done.skills` → SUMMARY "스킬 자동 호출" 절로 보인다 (P9·I9와 같은 원리).
- **재발 방지**: `tests/test_drivers.py::ClaudeCanaryTests::test_args_exclude_user_settings_but_keep_plugin_dir` · `IngestTests`(skills 집계) · `tests/test_harnesslib.py::SummaryTests`(스킬 절·없음 한 줄) · `tests/test_e2e.py::test_full_night_then_second_night`(가짜 모델 `SKILL` 줄 → SUMMARY).
- **가정 변경**: ASSUMPTIONS 새 행 "설정 소스 격리", "스킬 자동 호출 관측".
- **일반화**: 격리는 "무엇을 넣나"가 아니라 **"무엇을 빼나"**로 정의한다. 무인 실행이 의존하는 컨텍스트는 전부 러너가 명시해야 하고, 사람의 편의 설정은 기본값으로 새어 들어온다고 가정한다. 스킬은 md라 지침이다 — 불렸는지는 관측으로만 알 수 있고, 반드시 일어나야 하는 것은 러너(P6)가 맡는다.
