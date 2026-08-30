# 008 — 전역 설치본이 18커밋 동안 멈춰 있었다 (`plugin update` 는 버전이 같으면 아무것도 안 한다)

- **발견** — 2026-08-30 아침. 사용자가 새 스킬 `/harness:checkpoint` 를 불렀는데 unknown command. 설치본(`~/.claude/plugins/cache/harness-local/harness/0.1.0`)의 `installed_plugins.json` 기록이 `2026-08-29 01:52Z · 78bd7e42`, 그 뒤 main 은 18커밋. `hooks/pre-tool`·`session-start`·`hooks.json`·`harnesslib.py` 전부 repo 와 달랐고 스킬은 26/29.
- **증상** — `scripts/plugin-refresh` 가 "완료" 를 찍었지만 `claude plugin update harness@harness-local` 은 `already at the latest version (0.1.0)` 으로 복사를 건너뛴다. plugin.json 의 version 문자열이 갱신 판단 기준이다.
- **피해** — 2026-08-29 아침 이후 **대화형 세션의 훅은 옛 버전**: D1 게이트 안내·D2 private 네트워크 차단·D4 readonly·2026-08-29 밤의 강화(fail-closed·wrapper·human_scope) 전부 대화형에는 없었다. 무인 밤은 `--plugin-dir`(live) 라 영향 없음. 실제 유출·오작동은 관측되지 않았다(사용자 세션은 private repo 에서 네트워크를 시도하지 않았다).
- **원인** — 배송 결정(A-2, CONTEXT 2026-08-29)에서 "설치본은 스냅샷 복사 → refresh 로 갱신" 까지는 맞았지만, refresh 가 *실제로 복사되었는지* 확인하지 않았다. "완료" 메시지가 검증이 아니었다.
- **해소** — `scripts/plugin-refresh`: `uninstall` + `install` 로 강제 복사하고, 끝에 `git ls-files hooks runner skills .claude-plugin` 을 설치본과 `cmp` 로 대조해 하나라도 다르면 exit 1. 이 커밋.
- **재발 방지** — refresh 자체가 검증한다(다르면 실패). 세션 시작 훅에 "설치본 sha ≠ repo HEAD" 경고를 넣는 것은 다음 후보(대화형에서만 의미).
- **가정 변경** — ASSUMPTIONS "배송(전역 설치)" 행에 "갱신은 버전 게이트 — 강제 재설치 + 대조" 추가.
- **일반화** — "완료" 를 찍는 스크립트는 자기 결과를 검증해야 한다. 하네스의 원칙(모델의 done 은 판정이 아니다, P6)은 셸 스크립트에도 똑같이 적용된다.
