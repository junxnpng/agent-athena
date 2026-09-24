# verify — 재사용 가능한 근거 검증 시스템

주제·주장 하나와 외부에서 만들어진 근거 레코드 묶음, 코퍼스 텍스트를 받아 레코드마다 **존재 · 합치 · 재현율 · 조건 보존** 네 판정을 내는 시스템. 2026-09-22 deep-interview → ralplan(3회 반복, Critic APPROVE)으로 계획이 확정됐고, 같은 날 kvcpool-trace-gen에서 이 저장소로 옮겨 왔다. **P1–P4 완료(2026-09-23, 브랜치 `verify-system`; P4의 V4-3은 P6 `inject`와 함께 닫음)**, P5–P7 미완료. 진행 상태는 계획 파일의 `- [x] 완료` 표시와 실행 기록을 본다.

## 배치

```
plans/   ralplan-verification-system.md          실행 정본. 단계별 `- [ ] 완료` 표시가 진행 상태
         ralplan-verification-system.review-{1,2,3}-{architect,critic}.md   검토 기록(이전 전 경로 그대로)
spec/    deep-interview-verification-system.md   인수 기준 40개
docs/    verification-system-design-2026-09-22.md, verifier-acceptance-brainstorm-2026-09-22.md
         decisions.md                            (P1 이후 생성) NLI 백엔드·행 단위·κ 보고 전용 결정
refs/    verification-methods-2026-09-21.md, verification-voices-2026-09-21.md  + 각 폴더(에이전트 원문, grep 대조)
gold/    workload__year-in-llm-serving_handpicked.md   정답 세트 G (k=1, 사용자 노트 원문)
```

P1부터 생기는 것: `tools/verify/`(패키지·CLI), `tests/verify/`, `config/`(thresholds·queries·schema), `results/`(원장 sqlite는 git 밖, bundle·slice-facts JSON은 추적), `reports/`, `.venv/`, 그리고 `skills/verify-run`·`skills/claim-judge`(본체는 여기, 저장소 `.claude/skills/<name>`이 이곳을 가리키는 심볼릭 링크).

## 경로 규칙

- 문서 안 상대 경로는 모두 이 디렉토리(`/work/jun/AI-helper/verify/`) 기준.
- 입력 데이터는 원 저장소에 남아 있다. `KVCPOOL=/work/jun/priv-mb-eval/kvcpool-trace-gen`. Claude 레코드 804건·Codex 레코드 1,164건·waivers·원문 텍스트·옛 검사 스크립트가 `$KVCPOOL/docs/patterns/...`, `$KVCPOOL/tools/...`, `$KVCPOOL/papers/...`에 있다. 변환기는 `--source-root`(default: 환경 변수 `KVCPOOL`)로 받는다.
- 검토 기록 6편은 이전 전에 쓰인 것이라 `.athena/plans/...`, `docs/plans/...` 같은 옛 경로를 그대로 담고 있다.

## 실행

```bash
cd /work/jun/AI-helper/verify
export KVCPOOL=/work/jun/priv-mb-eval/kvcpool-trace-gen
# Claude Code를 이 디렉토리에서 열고
/athena:autopilot plans/ralplan-verification-system.md
```

autopilot은 계획 경로를 받으면 자체 계획 단계를 건너뛰고 P1부터 간다. 테스트 먼저(RED→GREEN), 코드·주석은 영어, 임계는 P1 말미에 `config/thresholds.yaml`로 등록하고 이후 바꾸지 않는다. 커밋은 사용자가 한다.
