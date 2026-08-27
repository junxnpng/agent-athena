# 001 · heredoc 쓰기가 쓰기 범위 검사(I6)를 우회한다

- **발견**: night-001 (GreedyAtena, 2026-08-27, opus). 로그 `model_done`의 `tool_counts = {"Bash": 7|10|9}`, `edits: null` — 파일 3개가 생겼는데 편집 0회. 스트림: `cat > tests/test_collectors_fx.py <<'PYEOF'`.
- **증상**: 훅 `pre-tool`의 I6 검사가 Write/Edit/MultiEdit/NotebookEdit의 `file_path`만 봤다. bypass 모드에서 모델은 Bash heredoc으로 파일을 쓴다(그쪽이 기본 쓰기 채널). P9 편집 카운터도 같은 경로만 세어 0.
- **피해**: 없음 — 범위 안(`tests/`)에만 썼다. 그러나 `write_scope: ["tests"]`가 `src/` 수정을 막는다는 보장이 실제로는 없었다.
- **원인**: 관측 지점이 "도구 호출"이었다. 파일을 쓰는 방법은 열거할 수 없다(heredoc, `python -c open()`, `tee`, 서브셸, 스크립트 안의 쓰기…).
- **해소** (커밋 `262f2dd`): 관측 지점을 "트리 변화"로 옮겼다. 러너가 모델 종료 직후 `git status --porcelain -z`로 변경 경로를 얻어 `scope_violations()`로 판정 — 위반이면 검증기를 돌리지 않고 `stage: scope`로 실패 처리(패치 보존 → 되돌림). 훅과 P9는 `bash_write_targets()` 휴리스틱(`>` `>>` `tee` · `sed -i` · `cp/mv` · `touch/mkdir`)으로 보강 — 조기 거부용이고 완전성은 러너 몫.
- **재발 방지**: `tests/test_e2e.py::test_scope_violation_is_judged_by_runner` · `tests/test_hooks.py::test_bash_write_targets_are_scope_checked` · `tests/test_harnesslib.py::ScopeTests`, `GitTests::test_changed_paths_includes_untracked_and_renames`
- **가정 변경**: ASSUMPTIONS "P3-lite 쓰기 범위 (I6)" 행 — "훅이 막는다" → "훅은 조기 거부, 러너가 최종 판정".
- **일반화**: 불변식은 도구 호출이 아니라 **결과**(트리·로그)에서 판정한다. 같은 원리가 이미 P6(모델의 done이 아니라 검증기)과 P1(카운터가 아니라 로그 fold)에 있다. 새 불변식을 훅에만 걸고 싶어지면 이 파일을 다시 읽는다.
