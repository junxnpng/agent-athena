# Claude Multi-Agent Setup Interview

> Status: **구축 완료** — Phase 1~5 전체 완료. `./setup.sh` 실행으로 설치 가능.
> Last updated: 2026-04-17
> Reference: `oh-my-claudecode/` 프로젝트 구조 참고하여 `claude-setup/` 구축 완료

---

## 취합 완료

### 작업 환경 & 역할

| 항목 | 내용 |
|------|------|
| **작업 범위** | 풀스택, AI/LLM 연구, Verilog(추후 추가), 아이디어 생성, 기타 다양 |
| **주 언어** | Python, Go 중심 + AI/LLM 생태계 (CUDA/C++, Jupyter, Bash 등) |
| **체제** | 1인 개발 |

### 에이전트 선호 (Q4, Q5)

- **필요 영역**: 구현 + 연구/분석 + 아이디어/통찰 + 리뷰 다방면
- **모델 라우팅**: 복잡도 기반 하이쿠/소넷/오퍼스 혼합 (일률 배정 X)

### 워크플로우 선호 (Q6, Q10)

- **핵심 원칙**: 같은 동작 3회 이상 반복 시 자동 추출 제안
  - 3 steps 이하 + 단일 에이전트 → slash command (`~/.claude/commands/*.md`)
  - 4 steps 이상 OR 복수 에이전트 → workflow (`skills/{name}/SKILL.md`)
- 이 규칙은 CLAUDE.md에도 이미 반영됨 (`<operating_principles>` 섹션)

### 코드 리뷰/검증 (Q7)

- 자동이면 좋겠으나, 구체적 설정은 이후 필요할 때 논의

---

## 답변 완료

### 세션 시작 자동화 (Q8 → Q11)

- **선택: E** — 마지막 작업 컨텍스트 리마인드
- "지난 세션에서 X 작업 중이었음" 자동 주입

### 코드 작성 후 자동 검증 (Q9 → Q12)

- **선택: 1, 2, 5**
  - **Lint** — PostToolUse (Edit/Write) 트리거, ruff(Python), golangci-lint(Go)
  - **Typecheck** — PostToolUse (Edit/Write) 트리거, mypy/pyright(Python), Go 빌드체크
  - **빌드 체크** — Stop (작업 완료 직전) 트리거, 전체 빌드 성공 여부

### 특화 에이전트 (Q13)

- **researcher** — 논문/기법 조사, 관련 연구 정리, 실험 설계 제안 (opus)
- **ideator** — 아이디어 브레인스토밍, 다각도 분석, 실현가능성 평가 (opus)
- **critic** — 아이디어/설계/코드에 대한 건설적 비판, 약점 지적 (opus)

### 아이디어 리뷰 스타일 (Q14)

- 우선순위: **b > c > d > a**
  1. 냉정한 약점 분석 (devil's advocate) — 기본 톤
  2. 다각도 시각 제시 — 약점 분석 후 여러 관점 보완
  3. 실현가능성/ROI 중심 — 실용적 판단 포함
  4. 격려 + 개선점 — 최후순위, 필요 시에만

---

## 구축 결과

### Phase 1 — 플러그인 골격 ✅
- `.claude-plugin/plugin.json`, `hooks/hooks.json`, `scripts/run.cjs`
- 훅 스크립트: session-start.mjs, post-tool-check.mjs, stop-check.mjs

### Phase 2 — 에이전트 정의 ✅
- 11개 에이전트: explore(haiku), executor, debugger, architect, planner, code-reviewer, security-reviewer, verifier, researcher, ideator, critic
- `AGENTS.md` 카탈로그

### Phase 3 — 스킬 (워크플로우) ✅
- 6개 스킬: autopilot, ralph, plan, cancel, research, ideate

### Phase 4 — 자동 셋업 ✅
- `setup.sh` (copy/link/uninstall 모드)

### Phase 5 — 선택 확장 ✅
- `.gitignore`, `templates/rules/` (python, golang, security)
- `templates/project-gitignore`
