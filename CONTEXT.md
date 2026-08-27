# CONTEXT — 어휘 · 금지어 · 해소 기록

이 파일은 **하네스 자체**의 어휘다. 대상 도메인(공부/일/코딩)의 어휘는 여기 없다 — 그것은 `<repo>/.harness/spec.md`의 몫이다.

## 어휘

| 용어 | 뜻 | 소유 |
|---|---|---|
| 사양 spec | 도메인이 주는 목표 + 지시문. `.harness/spec.md`. 유일한 입구 | 도메인 |
| 계획 plan | 사양을 리프 작업으로 분해한 것. `.harness/plan.json`. 재생성 가능 | 하네스 (v0: 사람이 손으로) |
| 밤 night | 하네스 세션 하나. `night-NNN`. 밤 하나 = 브랜치 하나 = SUMMARY 하나 | 하네스 (P1 발급) |
| 작업 task | 계획의 리프. `task-NNN`. 5~30분. 검증기 필수 | 하네스 (P1 발급) |
| 시도 attempt | 작업 하나에 대한 모델 호출 한 번. `task_started` ~ 판정 사이 | 러너 |
| 검증기 verifier | exit 0 = pass인 명령. 레벨 0(exit) / 1(스칼라 임계값) / 2(구조화 리포트, v0 미지원) | 도메인 |
| 리프 검증 / 전체 검증 | 작업별 검증기 / `.harness/verify` 스모크. **둘 다** 통과해야 커밋 | 러너 (P6) |
| 판정 verdict | 검증기 결과로 러너가 내리는 passed / failed. 모델의 "done"이 아니다 | 러너 (P6) |
| 막힘 blocked | 최대 시도 횟수만큼 실패한 작업. `BLOCKED.md`로 격리, 큐에서 제외 | 러너 (P8) |
| 아사 starvation | 자격이 있는데 계속 선택되지 않은 작업. 대기 시간 > 임계 → 무조건 먼저 | 러너 (P2) |
| 복구 작업 repair | 밤 시작 스모크가 실패했을 때 러너가 발급하는 작업. 통과 전까지 다른 작업을 돌리지 않는다 | 러너 (P4-5) |
| 드라이버 driver | 모델 런타임 호출 어댑터. `claude` (`claude -p`) / `fake` (테스트) / codex (Phase 6) | 러너 |
| 러너 runner | 바깥 루프. `runner/night`. 부기 전담, 내용은 만지지 않는다 | 하네스 |
| 훅 hook | Claude Code 이벤트에 붙는 결정론적 스크립트. md 바깥에서 강제력이 있는 유일한 지점 | 하네스 |
| 로그 log | `.harness/log.jsonl`. append-only. 모든 상태는 여기서 파생 | 러너 (I2, I3) |
| 쓰기 범위 write scope | 계약 ④. `domain.json: write_scope`. 밖이면 훅이 거부 | 도메인 → 훅 (I6) |

## 금지어 · 헷갈리는 말

| 쓰지 말 것 | 대신 | 이유 |
|---|---|---|
| "세션" (무수식) | "밤 night" 또는 "CC 세션" | Claude Code 세션(프로세스 하나)과 하네스 세션(밤 하나)이 다르다. 밤 하나에 CC 세션이 여러 개 뜬다 |
| "done" / "완료했다" (모델의 말) | "passed" / "검증 통과" | 모델의 주장은 판정이 아니다 (P6) |
| "사이클" | "밤" / "시도" | 옛 루프의 용어. 사이클 번호를 md에 적게 한 것이 라벨 795곳 오염의 원인 |
| 날짜 ID (`2026-08-27-…`) | `night-NNN` / `task-NNN` | 날짜는 메타데이터. 같은 날 두 번 돌면 충돌한다 |
| "우선순위 점수" (무수식) | `priority`(계획 필드) / "도메인 점수"(`domain_rank`) | 아사 방지와 도메인 점수는 다른 층이다 |
| "상태 파일" | 없음 — 로그를 fold한다 | I3. `plan.json`에 `status` 필드를 넣고 싶어지면 그것이 위반 신호 |
| "커밋했다" (모델의 말) | 러너만 커밋한다 | 커밋 정책 §6. 모델의 `git commit`은 훅이 거부 |
| "에이전트" | "모델" / "드라이버" / "러너" 중 하나 | 셋 중 무엇을 말하는지 매번 달랐다 |

## 해소 기록

- **2026-08-27 · 실패 시도의 작업 트리** — 검증 실패 시 트리를 마지막 green 커밋으로 되돌린다 (`.harness/` 제외). 대신 diff를 `.harness/sessions/<night>/<task>.<attempt>.patch`로 남기고, 다음 시도 프롬프트에 패치 경로와 검증 출력 꼬리를 넣는다. 근거: §4 "깨진 코드 위에 쌓지 않는다"와 I4 "실패 흔적은 지우지 않는다"를 동시에 만족.
- **2026-08-27 · 훅 주입 경로** — 러너는 `claude --plugin-dir <harness>`로 훅을 세션 한정 주입한다 (설치 불필요, 헤드리스 `-p`에서도 SessionStart/PreToolUse 동작 실측). 플러그인을 전역 설치한 채 러너를 돌리면 훅이 두 번 뜨므로 하지 않는다. 대화형: `claude --plugin-dir ~/workspace/agent-athena`.
- **2026-08-27 · 스모크는 밤에 한 번** — 5단 계층에서 "세션 = 밤"이므로 P4의 스모크(4단계)는 러너가 밤 시작에 한 번 돌리고 로그에 남긴다. 작업별 CC 세션의 훅은 로그의 결과를 보여줄 뿐 다시 돌리지 않는다 (`HARNESS_NIGHT` 환경변수로 구분). 러너 밖 대화형 세션에서는 훅이 직접 돌린다.
- **2026-08-27 · 복구 작업** — 스모크 실패 시 러너가 `origin: repair` 작업을 발급해 계획에 넣고, 통과 전까지 다른 작업을 선택하지 않는다. 최대 시도 초과 시 밤을 끝낸다 — red 트리 위에서는 어떤 검증도 의미가 없다.
- **2026-08-27 · 밤 브랜치 기점** — 직전 밤 브랜치가 HEAD에 병합됐으면 HEAD에서, HEAD가 직전 밤의 조상(미병합, 새 작업 없음)이면 직전 밤 브랜치에서 잇는다. 둘 다 아니면(분기) 거부한다. 로그가 git에 있으므로 기점을 잘못 잡으면 ID가 충돌한다.
- **2026-08-27 · P9는 훅이 아니라 스트림** — 파일별 편집 횟수는 `claude -p --output-format stream-json`의 `tool_use`를 러너가 밖에서 세어 얻는다. post-tool 훅으로 세면 관측이 대상 세션 안에서 돈다 (I9). 그래서 v0에 `post-tool` 훅이 없다.
- **2026-08-27 · macOS에 `timeout`이 없다** — 모든 타임아웃은 Python `subprocess` + 프로세스 그룹 kill로 구현. 셸에서 `timeout` 명령을 쓰지 않는다. `claude --print`는 stdin을 기다리므로 `stdin=DEVNULL` 필수 (KnockAtena 프로토타입에서 실측).
- **2026-08-27 · P3·P8 일부를 Phase 1에 당김** — 빌드 순서상 Phase 4지만, 쓰기 범위 거부(I6)와 최대 시도 초과 격리 없이는 무인 루프가 안전하지 않다. 멱등 키(P3 본체)와 병리 종합(P9)은 Phase 4 그대로.
- **2026-08-27 · macOS + Ubuntu 동시 지원** — 셸 파일은 dash 호환 POSIX sh 만(`scripts/portable-lint` 가 bashism·BSD/GNU 분기 명령을 거부), git ≥ 2.25(`init -b` 금지, 테스트는 `symbolic-ref`), stdio·subprocess 는 UTF-8 명시(`LANG=C` 서버), `claude` 는 PATH + `~/.local/bin` 등에서 탐색, 부기 파일 이름은 대소문자 무시 비교(macOS FS). 이 세션엔 컨테이너가 없어 Ubuntu 실기는 미검증 — `dash` + `shellcheck` 로 대체 검증했다. **Ubuntu 첫 밤 전에 `scripts/check` 부터.**
- **2026-08-27 · 쓰기 범위는 러너가 최종 판정한다** — GreedyAtena 첫 밤(night-001, opus)에서 모델이 파일을 전부 `cat > f <<'EOF'` 로 써서(bypass 모드에서는 Bash 가 기본 쓰기 채널) 훅의 Write/Edit 경로 검사와 P9 편집 카운터가 아무것도 못 봤다. 해소: 훅은 Bash 리다이렉션·sed -i·cp/mv 대상까지 휴리스틱으로 조기 거부하고, 러너가 모델 종료 직후 `git status` 로 범위 밖 변경을 잡아 검증기도 돌리지 않고 실패 처리한다(`stage: scope`). 관측 지점을 도구 호출에서 트리 변화로 옮기면 열거 불완전성이 사라진다. 상세: `findings/001-heredoc-bypasses-write-scope.md`.
- **2026-08-27 · `setsid`도 macOS에 없다** — 분리 실행은 `scripts/night-detached`(nohup + python `os.setsid()` + caffeinate/systemd-inhibit)로만 한다. 첫 무인 밤을 띄우다 발견.
- **2026-08-27 · 플랜의 `id`는 러너가 쓴다** — 손으로 쓴 `plan.json`에는 `id`를 넣지 않는다. `runner/queue load`(또는 `night`)가 로그 ∪ 계획의 최댓값+1로 발급해 파일에 써 넣는다. 사람이 `id`를 적으면 형식·중복만 검사하고 그대로 쓴다 (I1은 *모델*이 계산하지 않는다는 뜻이다).
