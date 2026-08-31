# 011 — .harness/ 조작이 되돌려지지 않고 커밋돼 다음 세션이 실행한다 (보안 리뷰 R2, Critical)

- **발견** — 2026-08-31, 라운드 2 보안 리뷰(읽기 전용 에이전트). 코드 추적으로.
- **증상** — 밤 세션의 모델이 `.harness/domain.json`(또는 plan.json·verify)을 훅이 못 보는 방식(`python3 -c "open('.harness/domain.json','w')…"` — WRITE_OPS 정규식·bash_write_targets 어디에도 안 걸림)으로 덮어쓴다. 러너의 `scope_violations` 는 이걸 위반으로 **잡지만**, 되돌리기 `revert_worktree`/`save_patch` 가 `:(exclude).harness` 로 `.harness` 트리 **전체를 제외**해 조작 파일을 되돌리지 않는다. 조작 파일이 트리에 남아, 같은 밤 뒤 작업이 성공하면 `commit_all`(`add -A`)이, 아니면 밤 끝 `commit_harness`(`add -A -- .harness`)가 커밋한다. 커밋된 `domain.json` 의 `verify.cmd` 를 다음 대화형 세션의 `hooks/session-start` 가 `run_verify` 로 `sh -c` 실행한다(확인 프롬프트 없음), 다음 밤 preflight/스모크도 실행 — 운영자 권한 RCE.
- **피해** — 관측된 악용 없음(모델이 실제로 시도한 적 없음). 코드 경로로 확인.
- **원인** — findings/009 에서 `revert_worktree` 가 로그 보존을 위해 `.harness` 전체를 제외했는데, 시도 중 러너가 쓰는 것은 `log.jsonl` 과 `sessions/` 뿐이라는 사실을 되돌리기에 반영하지 않았다. 관측(scope_violations)은 정확했고 처치(revert)가 구멍이었다.
- **해소** — `revert_worktree` 가 `.harness` 도 되돌린다 — 단 `log.jsonl` 과 `sessions/` 만 `:(exclude)` 로 보존(`reset`·`checkout`·`clean` 세 번). 조작은 실패 시도 되돌리기에서 사라져 어떤 커밋에도 못 들어간다. 테스트 `test_revert_worktree_restores_hdir_tampering`.
- **재발 방지** — "관측되는 것은 되돌려져야 한다": scope_violations 가 위반으로 세는 경로 집합과 revert 가 복원하는 경로 집합이 일치하는지가 계약이다. 한계: 훅은 여전히 인터프리터 코드 안 쓰기를 못 잡는다(findings/001·005·007) — 러너의 트리 기준 판정이 최종 방어선이고, 이제 그 방어선이 되돌리기까지 포함한다.
- **가정 변경** — ASSUMPTIONS "실패 시도 되돌리기" 행에 ".harness 조작 포함(log·sessions 만 보존)" 추가.
