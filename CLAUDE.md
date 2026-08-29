# harness — 개인 AI 하네스 레이어 (v0)

Claude Code / Codex 위에 얹는 도메인 무의존 레이어. 밤새 무인으로 돌고 아침에 `SUMMARY.md` 하나로 결과를 본다.
런타임(루프·도구 디스패치·모델)은 만들지 않는다 — Claude Code / Codex가 담당한다. 전체 사양: `docs/spec-v0.md`.

## 핵심 원칙 — 파일 종류가 강제력을 정한다
- **md에 쓴 것은 지침, 훅·스크립트에 쓴 것만 강제.** 부기(ID·카운터·상태 전이·커밋)는 절대 md에 쓰지 않는다.
- 부기는 프로그램(`runner/`, `hooks/`), 내용은 모델(프롬프트·스킬).
- 계획(`plan.json`)은 재생성 가능. 불변인 것은 실행 이력(`log.jsonl`, append-only). 상태는 로그를 fold해서 파생한다.

## 레이아웃
- `runner/night` 밤 하나 실행(진입점) · `runner/night-loop` 밤 여러 개 잇기(창·예산 종료 시, 총비용 상한) · `runner/queue` 선택 정책·`accept`·`approve`(승인 게이트 `verify: "approval"`) · `runner/id` ID 발급 · `runner/summary` 아침 산출물
- `runner/init` 대상 repo 골격 · `runner/decompose --check` 계획 검증 · `--propose` 리프 제안(P7-lite: 제안은 러너, 채택은 사람 또는 `plan.auto_accept`; 검증기는 지금 실패해야 채택)
- `runner/harnesslib.py` 공용 부기(로그 fold·상태 파생·P2 정책·검증기·git·SUMMARY) · `runner/drivers.py` 모델 드라이버(claude/fake)
- `hooks/run-hook` 진입점 → `session-start`(P4) · `pre-tool`(쓰기 중재·trifecta·예산·`.harness-readonly` 회사 읽기전용). 확장자 없음 — Windows 자동감지 회피
- `tests/` 단위+e2e 테스트 · `scripts/check` 자가 검증(테스트 + 이 파일 60줄 제한 + 훅/플러그인 JSON) · `scripts/plugin-refresh` 전역 설치본 갱신
- `skills/<이름>/` 이식 스킬 25종(대장 `skills/vendor/VENDORED.md`, 감사 정본 `docs/handoff-pack-2026-08-28.md` 4부) · `skills/vendor/<이름>/` = 로드 제외(to-tickets)
- `templates/harness-dir/` 대상 repo `.harness/` 골격 · `docs/` 사양(v0 `spec-v0.md`, v1은 반출 팩 2부) · `.out-of-scope/` 거절 기록 · `findings/` 실패 기록 · `ASSUMPTIONS.md` 가정 · `CONTEXT.md` 어휘
- 대상 repo: `<repo>/.harness/{spec.md, verify, init.sh, domain.json, plan.json, log.jsonl, SUMMARY.md, BLOCKED.md}` — git 추적

## 불변식 (위반 시 실행 거부 — 코드가 검사한다)
- I1 모델은 ID·카운터를 계산하지 않는다 · I2 `log.jsonl` append-only · I3 상태는 로그의 파생물(별도 상태 파일 없음)
- I4 실패 흔적을 컨텍스트에서 지우지 않는다 · I5 검증기 없는 작업은 큐에 못 들어간다 · I6 쓰기는 계약 ④ 경로 안에서만
- I7 lethal trifecta 금지(비공개 데이터·신뢰불가 콘텐츠·외부 통신 동시 성립 X) · I8 `plan.json` ↔ `log.jsonl` 분리 · I9 관측이 대상을 변형하지 않는다

## 커밋 정책 (전역 규칙의 유일한 예외)
- 러너만 커밋한다. 단위 = 검증 통과. 브랜치 `harness/night-NNN`. **push 금지.** 메시지 접두어 `[harness night-NNN task-NNN]`.
- 러너 모드에서 모델은 commit/push를 하지 않는다 — `pre-tool` 훅이 거부한다. 대화형은 막지 않는다(사람이 승인 루프에, S2).

## 작업 규칙 (이 repo를 고칠 때)
- 코드는 Python 3.9 stdlib만. `from __future__ import annotations` 필수, `X | None` 런타임 문법 금지. 외부 의존성 추가 금지.
- **macOS와 Ubuntu 둘 다에서 돈다.** 셸은 `#!/bin/sh` POSIX(dash 호환)만. BSD/GNU가 갈리는 명령(`sed -i` `readlink -f` `realpath` `timeout` `date -d/-v` `stat -c/-f`)과 bashism 금지 — `scripts/portable-lint`가 거부한다. 타임아웃은 Python 프로세스 그룹 kill. subprocess는 `encoding="utf-8"` 명시.
- 컴포넌트를 추가하면 `ASSUMPTIONS.md`에 "가정 + 유효 모델 급" 한 줄을 같이 적는다. 스킬·도구 추가 시 I7 재검사.
- 자작 스킬 frontmatter는 `name`, `description` 2키만(Codex 이식성). vendored 스킬(`skills/vendor/VENDORED.md`)은 upstream 유지. 에이전트가 자기 스킬을 만들지 않는다. 외부 스킬은 고정 커밋 감사 후 vendoring만.
- 날짜를 식별자로 쓰지 않는다. 계획에 세부 구현을 쓰지 않는다. 쓰기 작업을 병렬화하지 않는다.
- 범위 밖 요청은 `.out-of-scope/`에 파일로 남긴다(요청 / 이유 / 탈출구 / 과거 요청). 어휘 충돌은 `CONTEXT.md` 해소 기록에.
- 끝내기 전에 `scripts/check`를 돌린다 — **파이프 뒤에 두지 않는다**(`check | tail`은 exit code를 가린다). 파일로 받아 `$?`로 게이트.
- 밤이 하네스의 구멍을 드러내면 `findings/NNN-*.md`에 남긴다(발견/증상/피해/원인/해소/재발 방지/가정 변경). 사용자 검토용 산출물(SUMMARY·보고서)은 한글.
