# VENDORED — 이식 스킬 대장

외부 스킬은 **고정 커밋에서 정독 감사 후** 복사한다 (docs/handoff-pack-2026-08-28.md 4부가 감사 정본). 자동 업데이트 금지 — 갱신은 수동 재감사로만.

- **위치**: Claude Code 플러그인은 `skills/<이름>/SKILL.md` 한 단계만 스캔한다 (2026-08-28 실측: `skills/vendor/<이름>/`은 로드되지 않음).
  그래서 스킬 본체는 `skills/<이름>/`에, 이 대장만 `skills/vendor/`에 둔다. **로드 제외**할 스킬은 `skills/vendor/<이름>/`에 둔다 (예: to-tickets — P7 착수 때 승격).
- **frontmatter**: vendored 스킬은 upstream frontmatter를 유지한다 (`disable-model-invocation`·`argument-hint`·`license` 등). 하네스의 "2키만" 규칙은 자작 러너용 스킬에만 — `scripts/check`는 이 대장에 있는 이름을 면제한다.
- **모드 A 전용 표시**: 네트워크 지시가 있는 스킬은 frontmatter 바로 아래 첫 줄에 `> 모드 A 전용 — 네트워크(I7)…`를 둔다. 무인 러너(모드 B)에서는 pre-tool 훅이 네트워크를 차단한다(이중 방어).
- 커밋 단위 = 스킬 하나 (`[vendor] <이름> from <repo>@<커밋7>`). 되돌리기 단위.

| 이름 | 소스repo | 커밋 | 라이선스 | 감사일 | 수정 내역 |
|---|---|---|---|---|---|
| verification-before-completion | obra/superpowers | b36e0829c6d0 | MIT | 2026-08-28 | 없음 |
| systematic-debugging | obra/superpowers | b36e0829c6d0 | MIT | 2026-08-28 | superpowers: 접두어 2곳 제거 |
| ponytail-review | DietrichGebert/ponytail | 2ed6c52c9d7e | MIT | 2026-08-28 | 없음 |
| grilling | mattpocock/skills | 6654f6b60cd9 | MIT | 2026-08-28 | 없음 |
| brainstorming | obra/superpowers | b36e0829c6d0 | MIT | 2026-08-28 | scripts/server.cjs 텔레메트리 상수 고정(외부 로고 fetch 제거) |
| teach | mattpocock/skills | 6654f6b60cd9 | MIT | 2026-08-28 | 첫 줄 모드 A 전용 표시 |
| arxiv-search | langchain-ai/deepagents | 457ac435e121 | MIT | 2026-08-28 | 모드A 표시 · main() print 버그 수정 · 경로 |
