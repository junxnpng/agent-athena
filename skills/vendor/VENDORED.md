# VENDORED — 이식 스킬 대장

외부 스킬은 **고정 커밋에서 정독 감사 후** 이식한다 (docs/handoff-pack-2026-08-28.md 4부가 감사 정본). 자동 업데이트 금지 — 갱신은 수동 재감사로만.

- **위치**: Claude Code 플러그인은 `skills/<이름>/SKILL.md` 한 단계만 스캔한다 (2026-08-28 실측: `skills/vendor/<이름>/`은 로드되지 않음).
  그래서 스킬 본체는 `skills/<이름>/`에, 이 대장만 `skills/vendor/`에 둔다. **로드 제외**할 스킬은 `skills/vendor/<이름>/`에 둔다 (2026-08-29 현재 없음 — to-tickets 는 P7-lite 착수로 승격).
- **frontmatter**: 원본 유지형 vendored 스킬은 upstream frontmatter를 유지한다 (`disable-model-invocation`·`argument-hint`·`license` 등). 하네스의 "2키만" 규칙은 자작 스킬과 아래 통합 이식판에 적용 — `scripts/check`는 이 대장에 있는 이름을 면제한다.
- **모드 A 전용 표시**: 네트워크 지시가 있는 스킬은 frontmatter 바로 아래 첫 줄에 `> 모드 A 전용 — 네트워크(I7)…`를 둔다. 무인 러너(모드 B)에서는 pre-tool 훅이 네트워크를 차단한다(이중 방어).
- 커밋 단위 = 스킬 하나 (`[vendor] <이름> from <repo>@<커밋7>`). 되돌리기 단위.

| 이름 | 소스repo | 커밋 | 라이선스 | 감사일 | 수정 내역 |
|---|---|---|---|---|---|
| verification-before-completion | obra/superpowers | b36e0829c6d0 | MIT | 2026-08-28 | 없음 |
| systematic-debugging | obra/superpowers | b36e0829c6d0 | MIT | 2026-08-28 | superpowers: 접두어 2곳 제거 |
| ponytail-review | DietrichGebert/ponytail | 2ed6c52c9d7e | MIT | 2026-08-28 | 없음 |
| grilling | 통합 출처는 [PORTS.json](PORTS.json) | PORTS.json의 전체 SHA | MIT | 2026-09-28 | 사용자 요청 통합판. 기존 이식 이력은 git으로 보존; 변경·감사는 [보고서](../../docs/skill-port-review.md) |
| brainstorming | obra/superpowers | b36e0829c6d0 | MIT | 2026-08-28 | scripts/server.cjs 텔레메트리 상수 고정(외부 로고 fetch 제거) |
| teach | mattpocock/skills | 6654f6b60cd9 | MIT | 2026-08-28 | 첫 줄 모드 A 전용 표시 |
| arxiv-search | langchain-ai/deepagents | 457ac435e121 | MIT | 2026-08-28 | 모드A 표시 · main() print 버그 수정 · 경로 |
| handoff | 통합 출처는 [PORTS.json](PORTS.json) | PORTS.json의 전체 SHA | MIT | 2026-09-28 | 사용자 요청 통합판. 기존 이식 이력은 git으로 보존; 변경·감사는 [보고서](../../docs/skill-port-review.md) |
| writing-plans | obra/superpowers | b36e0829c6d0 | MIT | 2026-08-28 | subagent-driven 참조 제거 · 접두어 정리 |
| domain-modeling | mattpocock/skills | 6654f6b60cd9 | MIT | 2026-08-28 | 없음 |
| research | 통합 출처는 [PORTS.json](PORTS.json) | PORTS.json의 전체 SHA | MIT | 2026-09-28 | 사용자 요청 통합판. 기존 이식 이력은 git으로 보존; 변경·감사는 [보고서](../../docs/skill-port-review.md) |
| to-spec | 통합 출처는 [PORTS.json](PORTS.json) | PORTS.json의 전체 SHA | MIT | 2026-09-28 | 사용자 요청 통합판. 기존 이식 이력은 git으로 보존; 변경·감사는 [보고서](../../docs/skill-port-review.md) |
| wait-what | mattpocock/skills | 6654f6b60cd9 | MIT | 2026-08-28 | CONTEXT-MAP 절 삭제 |
| writing-for-agents | 통합 출처는 [PORTS.json](PORTS.json) | PORTS.json의 전체 SHA | MIT | 2026-09-28 | 사용자 요청 통합판. 기존 이식 이력은 git으로 보존; 변경·감사는 [보고서](../../docs/skill-port-review.md) |
| skill-creator | anthropics/skills | 3b3fad96af16 | Apache-2.0 | 2026-08-28 | 없음 (환경노트: py3.10+, PyYAML) |
| frontend-design | anthropics/skills | 3b3fad96af16 | Apache-2.0 | 2026-08-28 | 없음 |
| improve-codebase-architecture | mattpocock/skills | 6654f6b60cd9 | MIT | 2026-08-28 | codebase-design 부재 폴백 1구 · 모드A 표시 |
| review-changes | mattpocock/skills | 6654f6b60cd9 | MIT | 2026-08-28 | setup 참조 → 사용자 질문으로 · **rename** code-review → review-changes (2026-08-29, 공식 플러그인 `code-review`·내장 `code-review`와 3중 이름 충돌 — 팩 3부 M절) |
| receiving-code-review | obra/superpowers | b36e0829c6d0 | MIT | 2026-08-28 | 모드 A 전용 표시 (gh api — 공통 사항 4) |
| using-git-worktrees | obra/superpowers | b36e0829c6d0 | MIT | 2026-08-28 | 없음 |
| executing-plans | obra/superpowers | b36e0829c6d0 | MIT | 2026-08-28 | subagent-driven/finishing 참조 제거 (Step 3 마무리 3줄 → 사람 보고 1줄) |
| retro | mattpocock/skills | 6654f6b60cd9 | MIT | 2026-08-28 | 없음 (in-progress 출처 표시) |
| test-driven-development | obra/superpowers | b36e0829c6d0 | MIT | 2026-08-28 | 없음 |
| webapp-testing | anthropics/skills | 3b3fad96af16 | Apache-2.0 | 2026-08-28 | 없음 (Playwright는 init.sh 계약) |
| dsh-trim-cot-leakage | deepseek-ai/deepseek-harness | cd5ef8148158 | MIT | 2026-08-28 | dsh 결합 4곳 범용화 |
| to-tickets | mattpocock/skills | 6654f6b60cd9 | MIT | 2026-08-28 | 트래커 발행부 삭제 · 2026-08-29 P7-lite 착수로 `skills/to-tickets/` 승격(로드) — 대화형 분해용, 무인 제안은 `runner/decompose --propose` |

## 사용자 요청 통합 이식판

이번 요청에서 허용한 13종의 출처·고정 커밋·파일 SHA-256은 [PORTS.json](PORTS.json)이 정본이다.
이 항목은 upstream 원문 유지형이 아니라 동작을 조합한 adapted 이식이다. frontmatter는
name·description 두 키로 통일하고 원본의 Codex 명시 호출 정책은 agents/openai.yaml에 보존한다.
이는 이번 요청 범위의 통합이며, 에이전트가 임의로 자기 스킬을 생성하도록 일반 정책을 바꾸지 않는다.

원본 저장소의 선택된 SKILL.md와 연결된 SKILL-MECHANICS.md·메타데이터·MIT 라이선스를 읽고,
작업 트리 파일이 고정 커밋의 내용과 같음을 대조했다. 각 파생 스킬 폴더에 해당 저작권·허가문을 포함했다.
공통 실행 지침은 [PORTABILITY.md](../shared/PORTABILITY.md)이며, 패키지에는 shared 디렉터리도 포함한다.

| 신규 이름 | 원본 | 역할 |
|---|---|---|
| deep-interview | OMC deep-interview + Matt grilling/grill-me | 통합 인터뷰 정본 |
| grill-me | Matt grill-me + 공통 인터뷰 | 호환 진입점 |
| external-context | OMC external-context + Matt research | research 호환 진입점 |
| ralph | OMC ralph | 상태·런타임을 제외한 구현·검증·리뷰 절차 |
| claude-handoff | Matt claude-handoff + handoff | 양쪽 런타임의 실행 인계 진입점 |
| writing-fragments | Matt writing-fragments | 글감 수집 |
| writing-shape | Matt writing-shape | 논지와 단락 구성 |
| writing-beats | Matt writing-beats | 개념을 소개하며 전개 선택 |

기존 다섯 이름(grilling·research·handoff·to-spec·writing-for-agents)은 위 원래 표에서 통합판으로 연결한다.
전체는 원본 유지형 21개 + 통합 이식 13개 + 자작 2개 = 36개다.
