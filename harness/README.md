# harness — 개인 AI 하네스 레이어 v0

Claude Code / Codex 위에 얹는 도메인 무의존 레이어. 밤에 한 명령으로 시작해 무인으로 돌고, 아침에 `.harness/SUMMARY.md` 하나로 결과를 본다.
사양 `docs/spec-v0.md` · 상주 지침 `CLAUDE.md` · 어휘 `CONTEXT.md` · 가정 `ASSUMPTIONS.md` · 거절 기록 `.out-of-scope/`

## 요구사항
- **macOS 13+ 또는 Ubuntu 22.04+** (Ubuntu 20.04 는 python 3.8 / git 2.25 — 미검증)
- python3 ≥ 3.9 (stdlib만) · git ≥ 2.25 · `claude` CLI 2.1+ (`PATH` 또는 `~/.local/bin`)
- `/bin/sh` 는 POSIX 만 쓴다 — macOS(bash 3.2 sh 모드)와 Ubuntu(dash) 둘 다. `scripts/portable-lint` 가 갈리는 구문을 거부하고,
  `dash`·`shellcheck` 가 깔려 있으면 `scripts/check` 가 훅을 dash 로 실제 실행해 본다 (macOS: `brew install dash shellcheck`)
- 대상 repo 의 `.harness/verify` / `init.sh` 도 같은 규칙으로 쓴다 (템플릿이 그렇게 되어 있다)

## 첫 밤 (spec 부록 체크리스트)
1. 대상 repo 하나를 고른다 — 작고 검증기가 명확한 것. 작업 트리가 clean이어야 한다
2. `runner/init --repo <path>` → `.harness/` 골격 생성 (계약 5개 + plan 템플릿)
3. `.harness/verify` 작성 — exit 0만 되면 된다. `echo ok`로 시작해도 무방
4. `.harness/spec.md`에 목표 3~5문장
5. `.harness/plan.json`에 리프 3개 — 각 5~30분, `verify` 명시. **`id`는 쓰지 않는다** (러너가 발급)
6. `runner/decompose --check --repo <path>` → 계획 검증 (접수 게이트: 검증기 없는 리프는 거부)
7. `runner/night --repo <path> --hours 0.5` → **감독 하에 30분**
8. `.harness/SUMMARY.md`가 5분 안에 읽히는지 확인
9. 그 다음에야 무인으로: `runner/night --repo <path> --hours 8`

## 아침
- `.harness/SUMMARY.md` (결론 / 완료 / 막힘 / 다음 밤 / 이상 징후) · `.harness/BLOCKED.md`
- 커밋은 `harness/night-NNN` 브랜치에만 있다. 검토 후 `git merge harness/night-NNN`. **push는 러너가 절대 하지 않는다**
- 다시 만들기: `runner/summary --repo <path>` (로그에서 재생성 — 로그가 진실의 원천)

## 명령
| 명령 | 역할 |
|---|---|
| `runner/night` | 밤 하나 실행 (P4 5단계 → P2 선택 → 드라이버 → P6 판정 → 커밋 → P10) |
| `runner/queue status \| next \| load` | 큐 상태 / 다음 선택 / ID 발급+검증 (P2, P1) |
| `runner/id next night\|task` | ID 발급 (P1) |
| `runner/summary` | SUMMARY.md / BLOCKED.md 재생성 (P10) |
| `runner/init` | 대상 repo `.harness/` 골격 |
| `runner/decompose --check` | 계획 검증. 자동 분해(P7)는 Phase 3 |
| `scripts/check` | 하네스 자가 검증 (테스트 + CLAUDE.md 60줄 + 훅·플러그인 JSON) |

## 대화형으로 훅 쓰기
`claude --plugin-dir /path/to/harness` — `.harness/`가 있는 repo에서만 훅이 켜진다 (다른 repo에서는 무해).
전역 설치와 러너를 같이 쓰지 않는다 — 훅이 두 번 뜬다.
