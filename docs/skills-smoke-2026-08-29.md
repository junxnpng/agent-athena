# 스킬 기동 스모크 — 2026-08-29 (Phase A-3 lite)

27종을 임시 클론에서 haiku 로 `/harness:<이름>` 슬래시 호출 (4턴·쓰기 도구 금지, 대상 `runner/night` 3문장 시연). **전부 rc 0·오류 0**, 총 $1.32.
이것은 *로드·실행·형식* 검증이다. "쓰이는가"(A-3 본체)는 도메인별 실사용에서만 드러난다 — 안 쓰이는 스킬은 그때 폐기 후보(H2).

| 스킬 | 턴 | 비용 | 메모 |
|---|---|---|---|
| arxiv-search | 3 | $0.084 | 모드 A 전용 — 네트워크 없이 시연만 |
| brainstorming | 2 | $0.052 | 정상 — 스킬 성격대로 응답 |
| diagram | 2 | $0.042 | mermaid flowchart 먼저 냄 (규칙 1·4 준수) |
| domain-modeling | 2 | $0.047 | 정상 — 스킬 성격대로 응답 |
| dsh-trim-cot-leakage | 2 | $0.052 | 정상 — 스킬 성격대로 응답 |
| executing-plans | 2 | $0.04 | 정상 — 스킬 성격대로 응답 |
| frontend-design | 2 | $0.048 | 정상 — 스킬 성격대로 응답 |
| grilling | 2 | $0.04 | 정상 — 스킬 성격대로 응답 |
| handoff | 2 | $0.04 | 정상 — 스킬 성격대로 응답 |
| improve-codebase-architecture | 2 | $0.046 | 정상 — 스킬 성격대로 응답 |
| ponytail-review | 2 | $0.05 | L288-290·L331-333 패치 저장→되돌리기 3회 중복 지적 → 백로그 |
| receiving-code-review | 2 | $0.049 | 정상 — 스킬 성격대로 응답 |
| research | 2 | $0.043 | 정상 — 스킬 성격대로 응답 |
| retro | 2 | $0.046 | 정상 — 스킬 성격대로 응답 |
| review-changes | 6 | $0.074 | rename 후 정상 로드 (6턴 — 기준점 탐색) |
| skill-creator | 3 | $0.063 | 시연만 — scripts/ 는 py3.10+·PyYAML 필요 (uv run --with pyyaml --python 3.12) |
| systematic-debugging | 2 | $0.048 | 정상 — 스킬 성격대로 응답 |
| teach | 2 | $0.048 | 정상 — 스킬 성격대로 응답 |
| test-driven-development | 2 | $0.053 | 정상 — 스킬 성격대로 응답 |
| to-spec | 2 | $0.048 | Problem Statement 골격으로 응답 |
| to-tickets | 2 | $0.046 | 정상 — 스킬 성격대로 응답 |
| using-git-worktrees | 4 | $0.032 | normal checkout 임을 감지 |
| verification-before-completion | 2 | $0.04 | 정상 — 스킬 성격대로 응답 |
| wait-what | 3 | $0.053 | 용어 3문장 정의 (영문) |
| webapp-testing | 3 | $0.044 | CLI 라 해당 없음이라고 판단 (정상) |
| writing-for-agents | 2 | $0.047 | 정상 — 스킬 성격대로 응답 |
| writing-plans | 2 | $0.045 | 정상 — 스킬 성격대로 응답 |

## 남은 것
- 실사용 1회씩(공부: teach·research·grilling·arxiv-search / 리서치·회사일: grilling·writing-plans·systematic-debugging / 잡무: 문서 4종·to-spec) — 사용자.
- 무인 밤의 스킬 *자동* 호출은 0/26 (night-003~008) — 설명문 매칭만으로는 안 부른다. 러너 프롬프트에서 B-Tier1 3종을 지목할지 결정 필요.
- 백로그: `runner/night` 패치 저장→되돌리기 3회 중복 → 헬퍼로 (ponytail-review 지적).
