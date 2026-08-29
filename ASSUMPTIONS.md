# ASSUMPTIONS — 컴포넌트별 가정 기록

> "하네스의 모든 컴포넌트는 모델이 스스로 못 하는 것에 대한 가정을 인코딩한다." — Anthropic Labs

컴포넌트를 추가하면 여기에 한 줄을 같이 적는다. 모델 메이저 업데이트 때마다 표를 훑어 **가정이 무너진 컴포넌트를 지운다.** 삭감 절차가 없으면 하네스는 단조 증가한다.

기준: "유효" 칸은 2026-08 시점 Claude 5 세대(Fable / Opus / Sonnet 5)를 기준으로 적었다. 재측정 시점 기본값 = 모델 메이저 업데이트.
등급(spec §11): **A** 독립 출처 4+ · **B** 실측 근거 · **C** 단일 출처/벤더 · **D** 연구 근거 없음(개인 경험). D는 남에게 권할 때 반드시 등급을 같이 준다.

| 컴포넌트 | 가정 (모델이 스스로 못 하는 것) | 유효 · 등급 | 코드 위치 |
|---|---|---|---|
| P1 ID 발급 | 모델이 카운터를 세면 어긋난다 (라벨 795곳 오염 실측) | Claude 5 · B | `runner/harnesslib.py: next_id` |
| P2 아사 방지 | 점수 기반 선택은 낮은 점수 항목을 영원히 굶긴다 | 개인 경험 · **D** | `harnesslib.py: select_next` |
| P2 도메인 점수 | 동률일 때 모델 판단보다 결정론적 순서가 재현성이 높다 | Claude 5 · C | `harnesslib.py: domain_rank` |
| P3-lite 쓰기 범위 (I6) | 모델이 repo 밖·부기 파일을 건드릴 수 있다. 훅은 조기 거부(휴리스틱 — Write/Edit 경로 + Bash 리다이렉션), **러너가 git status 로 최종 판정**(도구 무관, 완전). 첫 밤 실측: 모델은 파일을 전부 heredoc 으로 썼다 | Claude 5 · B | `hooks/pre-tool`, `harnesslib.py: scope_violations`, `runner/night` |
| P4 밤 시작 5단계 | 모델이 기존 상태를 확인하지 않고 새 작업을 시작한다 | Claude 5 · B | `runner/night`, `hooks/session-start` |
| P4-4 스모크 | 깨진 트리 위에 쌓는 것을 모델이 감지하지 못한다 | Claude 5 · B | `runner/night` (밤 시작 1회) |
| P5 예산 집행 | 모델은 남은 시간을 모른다 / 무시한다 | 구조적(모델 무관) · A | `runner/night` deadline, `hooks/pre-tool` |
| P6 종료 판정 | 모델이 자기 작업을 과대평가한다 | Claude 5 · B | `harnesslib.py: run_verify`, `runner/night` |
| P8-lite 최대 시도 격리 | 같은 실패를 반복해도 스스로 접근을 바꾸지 않는다 | Claude 5 · B | `runner/night` (`max_attempts`) |
| P9 편집 횟수 카운터 | doom loop를 모델이 자각하지 못한다 | Claude 5 · B | `runner/drivers.py` (stream 집계) → `render_summary` |
| P10 SUMMARY | 모델이 쓴 요약은 자기 평가가 섞인다 — 로그에서 기계적으로 생성 | 구조적 · A | `harnesslib.py: render_summary` |
| 실패 시도 되돌리기 | 부분 진행된 깨진 상태에서 이어가면 더 나빠진다 | Claude 5 · C | `harnesslib.py: Git.revert_worktree` |
| 리프 상한 30분 | 30분 이상 한 작업에서 일관성을 잃는다 | Claude 5 · B | `domain.json: budget.leaf_max_minutes` |
| I7 trifecta 가드 | 프롬프트 인젝션을 모델이 스스로 막지 못한다 → 외부 통신 다리를 끊는다. **한계**: 직접 친 Bash 명령만 잡는다 — 모델이 쓴 스크립트 안의 네트워크 호출은 샌드박스 없이는 못 막는다 (실측: `git commit`·`curl` 직접 호출은 거부됨) | 구조적 · A | `hooks/pre-tool` (curl/wget/ssh…), `drivers.py` (WebFetch/WebSearch/MCP 차단) |
| I9 스트림 관측 | (설계 제약) 훅으로 세면 관측이 대상을 바꾼다 | 개인 경험 · **D** | `runner/drivers.py` |
| 밤 = 세션 계층 | 사람 부재 구간을 한 단위로 묶어야 인수인계가 된다 | 개인 경험 · **D** | `runner/night` |
| 잠듦 감지 | 무인 실행의 전제 "머신이 깨어 있다"가 깨질 수 있다(뚜껑) — 막을 수 없으니 감지해 조기 종료 | 구조적 · A | `drivers.py` slept_seconds, `runner/night` SLEEP_ABORT_SEC |
| 인프라 실패 분리 | 무응답·잠듦은 작업의 실패가 아니다 — 같은 카운터에 넣으면 무고한 작업이 막힌다 | 구조적 · A | `harnesslib.py: derive_states` (infra), `runner/queue unblock` |
| 복구 작업 우선 | red 트리에서 모델은 "내 작업은 됐다"고 판단하고 넘어간다 | Claude 5 · B | `harnesslib.py: select_next` (repair 우선) |
| 훅 생존 카나리아 | 훅은 자기 부재를 알릴 수 없다 — `--plugin-dir` 주입이 조용히 실패하면 `--dangerously-skip-permissions`만 남아 무방비다 (I6·I7이 전부 훅에 걸려 있다). session-start가 카나리아 파일을 쓰고, 드라이버가 첫 assistant 이벤트에서 존재를 확인 — 없으면 즉시 중단 (`hooks_dead`) | 구조적 · A | `hooks/session-start`, `drivers.py: run_claude`, `runner/night` |
| G2 계획 DAG 렌더 | 모델이 그린 다이어그램은 자기 평가가 섞인다 — 러너가 plan.json+상태에서 결정론적으로 mermaid 렌더 (P10과 같은 원리) | 구조적 · A | `harnesslib.py: render_plan_dag` |
| 비용 상한 기본값 | 모델은 자기 비용을 모르고, null 상한은 상한이 아니다 (night-002: 55분에 5시간 창 67% 실측). 시도당 `driver.max_budget_usd` · 밤당 `budget.max_night_usd` · 창 사용률 `budget.rate_limit_stop` 삼중 기본값 — 해제는 명시적 null 로만 | 구조적 · A | `harnesslib.py: DOMAIN_DEFAULTS`, `runner/night` |
| 설정 소스 격리 | 무인 세션은 사용자의 대화형 환경(전역 플러그인 34개·훅·출력 스타일)을 기본으로 상속한다 — 모델은 "학습 모드: 사용자 몫을 남겨라" 같은 대화형 지시를 무인 상황에서 걸러내지 못한다(night-001·002 스트림 8/8 상속, 6/8에서 ★ Insight 출력). 러너는 `--setting-sources project,local`로 user 소스를 뺀다 (`--bare`는 훅까지 꺼서 부적합) | 구조적 · A | `drivers.py: SETTING_SOURCES` |
| 스킬 자동 호출 관측 | 스킬은 md 지침이라 호출은 설명문 매칭의 확률이고 모델 급에 따라 다르다(실측 2026-08-28: sonnet 0/2, opus 1/1). 러너 프롬프트는 스킬을 지목하지 않으므로 실사용률은 스트림의 `Skill` tool_use를 세어야만 보인다 → `model_done.skills`, SUMMARY "스킬 자동 호출" | Claude 5 · B | `drivers.py: _ingest`, `harnesslib.py: collect_night` |
| heredoc 본문 제외 | 조기 거부 휴리스틱은 재현율만 걱정했지만 정밀도가 낮으면 거부가 곧 우회 유도다 — 모델은 거부당하면 다른 도구로 같은 쓰기를 한다(night-003: `cat > tests/x.py <<EOF` 거부 → `Write`). heredoc 본문은 데이터라 스캔에서 빼고, 실행형(`bash <<EOF`)만 남긴다 | Claude 5 · B | `harnesslib.py: strip_heredoc_bodies`, `hooks/pre-tool: check_bash` |
| 연속 밤 루프 | 밤이 5시간 창·예산으로 끝나면 사람이 없는 한 아무도 다음 밤을 띄우지 않는다 — 대화형 루프 스킬(/loop 류)은 러너 밖에서 세션을 반복하는 것이라 층이 틀리다. `runner/night-loop`가 밤을 잇되 밤 안은 만지지 않고, 총비용 상한·마감·밤 수로 묶는다(밤당 상한은 밤마다 새로 시작하므로) | 구조적 · A | `runner/night-loop`, `scripts/night-detached loop` |
| P7-lite 제안 필터 | 모델이 만든 계획에는 빈 작업(이미 통과하는 검증기)·자기 참조·검증기 없는 항목이 섞인다 — 러너가 제안된 검증기를 현재 트리에서 돌려 통과하면 버리고, 계획 검증(I5·리프 크기·순환)에 걸리면 제안 전체를 반려한다. 채택·id 발급은 사람/러너(I1) | Claude 5 · C | `runner/decompose: propose`, `harnesslib.py: accept_proposed` |
| 승인 게이트 | 모델은 사람의 결정(설계 확정·결과 해석·방향)을 대신 내릴 수 없고, 내리면 안 된다 — 승인은 검증기의 한 종류로 두어 게이트 뒤 작업이 사람 없이 시작되지 않게 한다 | 구조적 · A | `harnesslib.py: Task.is_gate, derive_states`, `runner/queue approve` |
| 읽기 전용 하네스 | 회사 머신의 세션은 하네스 버그를 그 자리에서 고치고 싶어 한다 — 커밋할 수 없는 곳의 수정은 유실되므로 마커로 쓰기 자체를 막고 발견만 남기게 한다 | 구조적 · A | `hooks/pre-tool: readonly_reason` |
| 산출물 검증기 | 산문 산출물의 품질은 기계가 못 재지만 형식·참조·수치 일치는 잴 수 있다 — 모델이 인용을 지어내거나 표의 숫자를 데이터와 다르게 적는 일(실측 다수)을 결정론으로 걸러내고, 품질 판단은 사람 게이트에 남긴다 | Claude 5 · B | `runner/verify-doc` |
| 데이터 등급(private) | 비공개 데이터가 있는 repo에서는 사람이 승인 루프에 있어도 인젝션이 만든 유출 요청을 사람이 알아채지 못한다(bypass 모드, URL 쿼리에 실어 보내는 한 번의 fetch) — 네트워크 다리를 훅으로 끊는 것만 강제다 | 구조적 · A | `hooks/pre-tool` (data_class), `harnesslib.py: network_skills` |
| 아침 다이제스트 | 밤의 결과는 사람이 아침에 *찾아가서* 읽는다는 가정은 repo 가 7개가 되면 깨진다 — 게이트를 잊는다. 배달은 결정론 스크립트가 SUMMARY 를 사용자 채팅으로 옮기는 것뿐이고(모델 없음 → I7 인젝션 경로 없음), 밤 중 알림은 여전히 범위 밖이다 | 구조적 · 모델 무관 | `scripts/morning-digest`, `templates/launchd/com.harness.morning-digest.plist` |
| 일일 비용 상한 | 밤·루프 단위 상한은 다시 띄우면 0 부터라 하루 총량을 못 막는다(2026-08-29 $68 실측). 하루 총량은 상태 파일이 아니라 로그 fold(자정 이후 model_done·plan_proposed 합)로 파생하고, 형제 repo 합산은 레지스트리 없이 워크스페이스 구조로 찾는다 | 구조적 · 모델 무관 | `harnesslib.day_cost_usd`, `runner/night`(exit 4·cost_day), `runner/night-loop --max-day-usd` |
| 프로세스 그룹 청소 | killpg 한 번으로 그룹이 다 죽는다는 가정은 틀렸다 — fork 직후의 손자가 시그널을 놓쳐 파이프를 잡고 살아남는다(1/30, findings/006). 리더 종료 뒤 `ps` 로 그룹 잔존을 훑어 SIGKILL 한다 | 구조적 · 모델 무관 | `harnesslib.kill_group` |
| 훅 fail-closed | 가드가 예외로 죽으면 통과가 아니라 거부다 — Claude Code 는 훅 exit 1 을 비차단으로 보고 도구를 실행한다. domain.json 이 깨져도 public 이 아니라 private 로 닫는다 | 구조적 · 모델 무관 | `hooks/pre-tool` |
| 대화형 전용 경로(human_scope) | I6 는 대화형에서도 강제다(사람이 매 쓰기를 보지 않는다 — bypass). 사람이 넣는 자료(수집함·기록)는 write_scope 가 아니라 human_scope 로 열어, 밤은 지어낼 수 없고 낮에는 승인 루프 안에서 쓴다 | 구조적 · 모델 무관 | `hooks/pre-tool: check_path`, `harnesslib.Domain.human_scope` |

## 지운 것
(아직 없음. 지울 때는 행을 여기로 옮기고 날짜·근거를 적는다 — 되살릴 때 필요하다.)
