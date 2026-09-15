# harness — 개인 AI 하네스 레이어 v0

Claude Code / Codex 위에 얹는 도메인 무의존 레이어. 밤에 한 명령으로 시작해 무인으로 돌고, 아침에 `.harness/SUMMARY.md` 하나로 결과를 본다.
사양 `docs/spec-v0.md` · 상주 지침 `CLAUDE.md` · 어휘 `CONTEXT.md` · 가정 `ASSUMPTIONS.md` · 거절 기록 `.out-of-scope/`

## 요구사항
- **macOS 13+ 또는 Ubuntu 22.04+** (Ubuntu 20.04 는 python 3.8 / git 2.25 — 미검증)
- python3 ≥ 3.9 (stdlib만) · git ≥ 2.25 · `claude` CLI 2.1+ (`PATH` 또는 `~/.local/bin`) 또는 `codex` CLI 0.154.0+ (`PATH`)
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
9. 그 다음에야 무인으로: **`scripts/night-detached --repo <path> --hours 8`** — 터미널을 닫아도 살아남고(nohup + 새 세션) 맥/우분투 잠자기를 막는다(caffeinate / systemd-inhibit). 멈추려면 `kill $(cut -d' ' -f1 <repo>/.harness/sessions/lock)`. 대화형에서 스킬·훅을 쓰려면 한 번만 `claude plugin marketplace add <이 repo 경로>` → `claude plugin install harness@harness-local`, 이후 스킬·훅 커밋마다 `scripts/plugin-refresh`(설치본은 스냅샷). 아침까지 밤을 잇고 싶으면 **`scripts/night-detached loop --repo <path> --until-hours 7 --max-total-usd 40`** — 창·예산으로 끝난 밤 뒤에 다음 밤을 띄우고, 큐가 비거나 총비용 상한에 닿으면 멈춘다(`runner/night-loop`)

## 무인 실행 주의 (findings/002)
- **맥북은 뚜껑을 닫으면 잠든다.** `caffeinate`는 유휴 잠자기만 막는다 → 전원 연결 + 뚜껑 열어두기, 또는 Ubuntu 서버에서.
- 잠들면 러너가 감지해 그 시도를 무효로 하고(실패 횟수 미산입) 밤을 끝낸다. SUMMARY 결론에 "머신이 잠듦 (밤 중단)". 확인: `pmset -g log | grep -E 'Sleep|Wake'`
- 부당하게 막힌 작업은 `runner/queue unblock task-NNN --reason "..." --repo <path>` 로 푼다 (로그에 이벤트로 남는다)

## 아침
- `.harness/SUMMARY.md` (결론 / 완료 / 막힘 / 다음 밤 / 이상 징후) · `.harness/BLOCKED.md`
- 커밋은 `harness/night-NNN` 브랜치에만 있다. 검토 후 `git merge harness/night-NNN`. **push는 러너가 절대 하지 않는다**
- 다시 만들기: `runner/summary --repo <path>` (로그에서 재생성 — 로그가 진실의 원천)

## 명령
| 명령 | 역할 |
|---|---|
| `runner/night` | 밤 하나 실행 (P4 5단계 → P2 선택 → 드라이버 → P6 판정 → 커밋 → P10) |
| `runner/queue status \| next \| load \| unblock` | 큐 상태 / 다음 선택 / ID 발급+검증 / 막힘 해제 (P2, P1, P8) |
| `runner/id next night\|task` | ID 발급 (P1) |
| `runner/summary` | SUMMARY.md / BLOCKED.md 재생성 (P10) |
| `runner/init` | 대상 repo `.harness/` 골격 |
| `runner/decompose --check` | 계획 검증. 자동 분해(P7)는 Phase 3 |
| `scripts/night-detached` | 밤을 분리 실행 (취침 시점의 한 명령) · `loop` 앞에 붙이면 `runner/night-loop` |
| `runner/night-loop` | 밤 여러 개를 마감까지 잇는다 (창·예산 종료 시 다음 밤, 총비용 상한·밤 수·마감으로 멈춤) |
| `scripts/plugin-refresh` | 전역 설치본(스냅샷)을 repo 현재 상태로 갱신 |
| `skills/diagram/` | 자작 2호 — 요소 셋 이상이 엮이면 mermaid 를 먼저 (팩 §3 초안, 2026-08-29) |
| `runner/decompose --propose` | P7-lite: 사양·계획 상태·지난 SUMMARY 로 리프 제안 → `.harness/plan.proposed.json` (이미 통과하는 검증기는 버림) |
| `runner/queue approve task-NNN` | 승인 게이트(`verify: "approval"`)를 사람이 연다 — 대화형에서 '승인'·'시작해'·'진행해' |
| `domain.json data_class` | `public`(기본) / `private`: private 는 대화형에서도 curl 류·WebFetch/WebSearch·네트워크 스킬 호출을 훅이 거부 (재무·건강·지식 repo) |
| `.harness-readonly` (하네스 루트) | 회사 설치: 마커가 있으면 훅이 하네스 안 쓰기·commit 을 거부. `git clone --branch <tag>` → `touch .harness-readonly` → 전역 설치, 갱신은 `git pull` + `scripts/plugin-refresh` |
| `runner/verify-doc <md>` | 산출물(Markdown+frontmatter) 결정론 검증기 — 필수 키·섹션·내부 링크·인용 키(bib)·표 숫자↔CSV/JSON·최소 단어. 논문·리포트 리프의 `verify` 에 쓴다. 품질은 승인 게이트 |
| `runner/queue accept` | 제안을 plan.json 에 편입 (id 발급·검증). `domain.json plan.auto_propose/auto_accept` 가 켜진 repo 는 night-loop 가 큐가 빌 때 자동으로 |
| `scripts/check` | 하네스 자가 검증 (테스트 + CLAUDE.md 60줄 + 훅·플러그인 JSON + 이식성 린트) |

## 스킬
- 이식 스킬 25종이 `skills/<이름>/`에 있다 (대장 `skills/vendor/VENDORED.md`: 소스·고정 커밋·라이선스·감사일·수정 내역). `> 모드 A 전용` 표시가 있는 스킬은 네트워크를 쓰므로 대화형에서만.
- 문서 4종(docx·xlsx·pptx·pdf)은 공식 설치: `claude plugin marketplace add anthropics/skills && claude plugin install document-skills@anthropic-agent-skills`
- 갱신은 수동 재감사로만. 새 외부 스킬은 고정 커밋 클론 → 전 파일 정독 → 복사 → 대장 행 → 스킬당 커밋 `[vendor] …`

## 대화형으로 훅 쓰기
`claude --plugin-dir /path/to/agent-athena` — `.harness/`가 있는 repo에서만 훅이 켜진다 (다른 repo에서는 무해).
전역 설치와 러너를 같이 쓰지 않는다 — 훅이 두 번 뜬다.

## 아침 다이제스트 (선택)
`scripts/morning-digest --dry-run` 이 `~/workspace/*/.harness/SUMMARY.md` 의 결론·승인 대기·막힘·이상 징후를 한 통으로 만든다. 텔레그램으로 받으려면 `~/.config/my-secrets/tokens.env` 에 `HARNESS_BOT_TOKEN`·`HARNESS_CHAT_ID` 를 두고 `templates/launchd/com.harness.morning-digest.plist` 를 등록한다(07:30). 모델은 개입하지 않는다 — 실시간 알림이 아니라 아침 SUMMARY 의 배달이다.

## Codex 대화형 환경

Codex CLI 0.154.0에서 기존 Claude 플러그인을 직접 설치한다. `AGENTS.md`는
`CLAUDE.md`를 가리키며, 스킬과 `hooks/run-hook`을 공유한다.

```sh
codex plugin marketplace add /path/to/agent-athena2
codex plugin add harness@harness-local
codex -C /path/to/your-repo
```

같은 marketplace가 다른 복제본을 가리키면 `codex plugin marketplace remove harness-local`
후 위 명령으로 다시 등록한다. 소스를 갱신한 뒤에도 `codex plugin add harness@harness-local`로
재설치하고 새 대화를 연다. `scripts/plugin-refresh`는 Claude 설치본용이다.

CLI의 `/hooks`에서 harness의 SessionStart와 PreToolUse 정의를 검토하고 신뢰해야 훅이 실행된다.
설치·활성화만으로는 훅이 신뢰되지 않는다. PreToolUse는 Codex의 Bash와 MCP 호출 및
`apply_patch`의 추가·수정·삭제·이동 대상 모두를 검사한다. `.harness/`가 없는 프로젝트에서는
도메인 제한을 적용하지 않는다(`.harness-readonly`는 별도 적용).

Codex의 호스팅 웹 검색과 일부 도구 경로에는 PreToolUse가 적용되지 않는다.
따라서 이 구성만으로 비공개 데이터의 외부 통신 차단(I7)을 보장하지 않는다.
무인 실행은 아래의 별도 Codex 드라이버 설정을 사용한다.
공식 동작 근거: [Codex Hooks](https://learn.chatgpt.com/docs/hooks).
비교·적용 내역: [Codex 환경 이식 보고서](docs/codex-environment.md).

## Codex 무인 실행

`runner/night --driver codex`는 Codex CLI 0.154.0 이상의 저장된 인증을 사용한다.
먼저 `codex login`으로 인증한다. 기존 대상 repo의 `.harness/domain.json`에서
다음 항목을 **병합**한다(쓰기 범위·검증 명령 등 기존 계약은 유지).

```json
{
  "driver": {"name": "codex", "model": null, "effort": null, "max_budget_usd": null, "max_turns": null},
  "budget": {"max_night_usd": null, "max_day_usd": null, "rate_limit_stop": null}
}
```

Codex JSONL은 토큰 사용량을 제공하지만 달러 비용·5시간 창 사용률·내부 턴 상한은
이 드라이버에서 강제하지 못한다. 해당 제한이 설정돼 있으면 실행을 거부한다.
비용은 로그의 `cost_known: false`와 SUMMARY의 **비용 미상**으로 표시한다.
시간·작업 수·실패 횟수 제한은 기존 러너가 적용한다.
루프는 남은 시간을 각 밤에 전달하고 최소 작업 시간보다 적게 남으면 새 밤을 시작하지 않는다.
검증·정리는 별도 타임아웃으로 실행되므로 종료 처리가 마감 시각을 넘길 수 있다.

```sh
runner/night --repo /path/to/repo --driver codex --dry-run
runner/night --repo /path/to/repo --driver codex --hours 0.5 --max-tasks 1
# 여러 밤을 시간 상한으로 연결: 0은 달러 총비용 제한 해제
runner/night-loop --repo /path/to/repo --driver codex --until-hours 2 --max-total-usd 0
```

사용자 설정·플러그인·자동 스킬 탐색·MCP·웹·위임을 제외하고, 하네스 원본 훅을 실행마다
명시적으로 주입한다. 이 검토된 훅을 실행하기 위해 해당 호출에만 훅 신뢰 확인을 생략한다.
다른 `hooks.json` 또는 프로젝트·상위 디렉터리의 `.codex/config.toml`이 있으면 사전 거부한다.
사용자 `config.toml`은 무시하므로 모델·effort는 위 계약으로 지정한다.

작업은 네트워크 없는 `workspace-write`, 계획·교훈 제안은 `read-only` 샌드박스를 사용한다.
셸 쓰기 검사는 휴리스틱이며 최종 쓰기 범위 판정·실패 복구·성공 커밋은 기존 러너가 수행한다.
OS 샌드박스 실패 시 권한을 확대해 재실행하지 않는다. 종료는 기존 SIGTERM/SIGINT 절차를 따른다.
