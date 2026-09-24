# ralplan — 재사용 가능한 근거 검증 시스템 (v1) · iteration 3 (Critic APPROVE, 2026-09-22)

> **위치 (2026-09-22 이전).** 이 계획과 검증 시스템은 `/work/jun/AI-helper/verify/`(저장소 jun-heo/AI-helper)에 산다. 상대 경로는 모두 `/work/jun/AI-helper/verify/` 기준이며, 실행은 `cd /work/jun/AI-helper/verify` 뒤 `/athena:autopilot plans/ralplan-verification-system.md`. `~/.claude/skills`는 저장소 `.claude/skills/`로의 심볼릭 링크라 스킬 본체는 `skills/`(이 디렉토리 아래)에 두고 저장소 `.claude/skills/<name>`을 그곳으로의 심볼릭 링크로 만든다. 입력 데이터(레코드 두 벌, waivers, 원문 텍스트, 옛 검사 스크립트)는 kvcpool-trace-gen에 남으며 `$KVCPOOL`=`/work/jun/priv-mb-eval/kvcpool-trace-gen`로 가리킨다. 변환기는 이 경로를 `--source-root`(default: `KVCPOOL` 환경 변수)로 받는다. 검토 기록 `plans/*.review-*.md`는 이전 전 경로(`.athena/...`, `docs/plans/...`)를 그대로 담고 있다.

- 스펙: `spec/deep-interview-verification-system.md` / 초안 설계: `docs/verification-system-design-2026-09-22.md` / 인수 시험: `docs/verifier-acceptance-brainstorm-2026-09-22.md`
- 정답 세트 G: `gold/workload__year-in-llm-serving_handpicked.md` (k=1, 6.6 KB 한 줄, `->` 메모 5개)
- 실측 입력 규모: Claude 원 레코드 **30** → 인용 **44** (인용 0건 2행 · 1건 14 · 2건 12 · 3건 2), Codex 원 레코드 **37** (fragment 1–72개, 단일 fragment 7행)
- 제안 브랜치: `verify-system`
- 리뷰 반영: architect #1–#7 (critic 수정판) + critic 추가 2건 + optional 3건

## RALPLAN-DR

### Principles

1. **판정의 무게는 코드와 원장에 둔다.** 모든 판정 행은 `verifier_id`·`protocol_ver`와 함께 SQLite에 남는다. 심판이 쓴 JSONL은 import 시 스팬 해결·행 수 일치·manifest sha256으로 봉인되어, 모델이 기록자가 되지 못하게 한다.
2. **검사기는 없는 것을 지어내지 않는다.** 조건 필드가 없으면 「없음」을 대신 써 주지 않고, G에 없는 라벨을 파생하지 않는다. 부재는 격리이거나 `not-applicable`이지 추정이 아니다.
3. **층을 섞지 않는다.** L1 verdict는 `{PASS, MISS}`로 닫고 waiver는 별도 테이블·별도 열로 둔다. L1 MISS 행은 이후 층에 들어가지 못한다.
4. **임계는 첫 층을 돌리기 전에 등록한다.** `config/thresholds.yaml`은 **P1 말미에 등록**되고 이후 단계는 읽기만 한다. sha256이 출처 묶음에 박힌다.
5. **사람 시간은 계약 제약이다(spec:48) — 그리고 먼저 한 번 관통한 뒤 측정된 사실 위에서 나머지를 정한다.** 새 손 라벨을 만들지 않는 것이 기본이며, v1이 그 제약을 소비하는 자리는 B-2(사람 라벨 30분)와 B-3(예외 논문 변환) 둘뿐이고 각각 ADR에 사유가 적혀 있다. 얇은 수직 슬라이스(P1→P2→P3)가 끝나기 전에는 L2·L6·재현율·인수 시험의 범위를 확정하지 않는다.

### Decision Drivers (순위)

1. **감사 가능성과 재현성** — 판정마다 누가·어느 프로토콜로·어느 입력 해시 위에서 냈는지가 남아야 한다 (스펙 V2-3·OP-1).
2. **v1 데이터에서 실제로 움직이는 수치를 먼저 얻는 것** — 사전에 값이 정해진 지표에 단계를 쓰지 않는다.
3. **환경 제약** — (이전 위치 kvcpool-trace-gen의 `.venv` 기준 기록. 새 위치의 `.venv`는 P1에서 만들며 sqlite3·PyYAML·pytest·coverage를 넣는다; duckdb 등은 없다.) 원래 기록: `.venv`(Python 3.10.12)에는 `sqlite3`·PyYAML·pytest에 더해 **duckdb 1.5.5, pyarrow 25.0.1, jinja2, markdown, tabulate, pygments**가 이미 있다. 없는 것은 torch·transformers·numpy·scipy·coverage다.

### Viable Options

**(a) 저장 형태 — SQLite 원장  vs  JSONL + 스크립트  vs  duckdb-over-JSONL**

| 안 | 장점 | 단점 |
|---|---|---|
| **A1. SQLite + `tools/verify/` CLI (채택)** | 일곱 층이 같은 `checks`에 쓰므로 「어느 행이 어느 층에서 왜 떨어졌나」가 조인 한 번; stdlib `sqlite3`; 트랜잭션; **trigger로 `gold` 직접 UPDATE를 거부**할 수 있어 B-4(감사-후-채점)의 수정 이력 강제가 DB 층에서 성립 | 텍스트 diff 불가 → 원장을 git 밖 재생성 산출물로 두고 보고서 md/JSON을 커밋 대상으로 삼아 상쇄 |
| A2. JSONL + 스크립트 | git diff·grep으로 읽힘, 도구 불필요 | 일곱 층의 조인을 손으로 재구성; 무결성 제약 없음 → 고아 행; 동시 쓰기에서 파일 파손 |
| A3. duckdb-over-JSONL (이미 설치됨) | 의존 0을 유지한 채 JSONL의 diff 가능성과 SQL 조인을 동시에 줌; 집계 성능 우수 | **trigger가 없다.** `gold` 불변성·`checks` 무결성 제약을 애플리케이션 코드로 옮겨야 하고, 그러면 「검사기는 생성기가 고칠 수 없는 자리에」(설계 P6)가 코드 규율로 내려간다 |

**무효화 근거:** A2는 층이 2~3개일 때만 성립한다. **A3는 성능·diff 면에서 A1보다 낫지만 trigger 부재 한 가지가 결정적이다** — B-4의 「G 수정은 감사 기록을 통해서만」을 DB가 강제하지 못하면 스펙 B-4의 「G의 수정 이력이 남는다」가 규약에 불과해진다. 그 외에는 A3가 열등하지 않다는 점을 명시해 둔다.

**(b) NLI 1차 전수 스윕 — 로컬 모델 vs 소형 API vs stdlib 스크리너 + 중형 심판**

| 안 | 장점 | 단점 |
|---|---|---|
| B1. MiniCheck급 로컬 모델 | 토큰 0, 오프라인 재현; HF 캐시에 Qwen3-0.6B 존재 | torch+transformers ≈ 2.5 GB를 들이면 결정론적 층의 pytest까지 그 의존에 묶임; v1 규모(51행)에 이득 없음 |
| B2. 소형 API 모델 | 설치 0, 품질 우위 | 환경에 키 없음; 네트워크 의존 테스트가 TDD 루프를 깸; 「값싼 전수 스윕」 제약과 충돌 |
| **B3. tier0 = stdlib 어휘 스크리너 + tier1 = 중형 심판 (채택)** | 의존 0, 완전 결정론; tier0은 **`supports`를 낼 수 없고** 라우팅만 한다; v1 규모에서 tier1이 전량을 덮어도 예산 안 | **v1에서는 캐스케이드가 사실상 없다** — tier0 승격률은 100%에 가깝고 `expensive_ratio`는 tier2를 부르기 전까지 0이다. 이것을 AC에서 「공허한 임계 통과」로 쓰지 않고 `escalation_rate`를 **관측값으로만** 보고한다 |

**무효화 근거:** B1·B2 모두 v1 규모에서 이득이 없고 환경 제약과 충돌한다. 둘 다 버리지 않고 `JudgeBackend` 인터페이스 뒤 스텁(`backends/{api_small,local_nli}.py`)으로 남기며, 40편(≈1,900행) 확장 시점에 재개한다. **v1의 tier0은 캐스케이드의 증명이 아니라 자리 잡기임을 ADR에 명시한다.**

**(c) 심판 실행 경로 — 파일 왕복 vs CLI가 직접 API 호출**

| 안 | 장점 | 단점 |
|---|---|---|
| **C1. 파일 왕복 (채택)** — `judge export`(manifest sha256 포함) → 에이전트가 `~/.claude/skills/claim-judge/`를 따라 JSONL 작성 → `judge import`(해시·행 수·스팬 검증) | 심판 입출력이 파일로 남아 감사 가능; 순서 교대 = export 두 벌; 키 불필요; export/import가 순수 함수라 pytest 100% 커버 | 1회 실행이 아니라 3단계; import 검증 로직이 필수 |
| C2. CLI가 API 직접 호출 | 한 번에 끝남 | 키 필요, 비결정적, 원 프롬프트·응답을 따로 적어야 함, 테스트가 네트워크에 묶임 |

**무효화 근거:** C2는 Driver 1·3을 동시에 깬다.

---

## 계획 본문 (v1)

공통 규칙: **테스트를 먼저 쓴다**(RED→GREEN→REFACTOR). 코드·주석·docstring은 영어. **코드 안에 단계 번호를 적지 않는다.** `git add/commit/push`는 사용자가 한다. 실행은 항상 `.venv/bin/python`. 각 단계는 「닫는 AC」와 `- [ ] 완료` 표기를 가지며, 새 세션은 이 파일만 읽고 재개한다.

선행 1회: `.venv/bin/pip install coverage`.

### 행 단위 정의 (전 단계 공통)

- **1 인용 = 1 행.** `row_id = "<extractor>:<record_id>.q<n>"`.
- **Claude**: 정답 논문 원 레코드 30 → 행 44. `quotes: []`인 2행은 행을 내지 않고 `no_quote` 사유로 격리.
- **Codex**: `quote` 필드가 없다. 규칙 — **`fragments`가 정확히 1개인 레코드만 그 `fragments[0].text`를 `quote`로 삼는다**(정답 논문 7행). 2개 이상이면 `multi_fragment_no_quote`로 격리하고, fragment는 `paragraphs`에 locator 근거로만 등록한다. Codex 인용은 PDF 블록 원문이므로 L1 통과가 구성상 보장된다 — `checks.l1_tautological=1`로 표시하고 대표 수치 집계에서 분리한다.
- **변환 요약은 항상 「원 레코드 30·37 전부가 행 산출 또는 사유 코드 붙은 격리로 닫혔다」를 보고한다.** 행 수(44·7)와 원 레코드 수(30·37)를 섞어 쓰지 않는다.

### P1 — 계약 · 원장 · 쿼리 · 변환기 · 임계 등록  〔테이블: papers, paragraphs, queries, claims, runs〕

먼저 쓰는 테스트: `tests/verify/test_schema.py`, `test_ledger.py`, `test_queries.py`, `test_convert_claude.py`, `test_convert_codex.py`, `test_paragraphs.py`, `test_thresholds.py`.

- `config/evidence_record.schema.json` — 필수: `record_id, paper_id, quote, locator{section,page,para_id}, claim_text, conditions{unit,denominator,window,ideal_or_measured,baseline}, numbers[]{value,unit,definition,derived_from}, kind∈{measurement,author_interpretation,extrapolation}, extractor_id, run_id`. 조건 값은 문자열 또는 `"none"`(=「없음」 명시). **키 부재 = 격리, `"none"` = 통과.** stdlib 검증기(`schema.py`).
- `tools/verify/ledger.py` — **11 테이블**: `papers, paragraphs, queries, claims, runs, checks, gold, audits, injections, waivers, budget`. `gold`에 직접 UPDATE를 거부하는 trigger. 원장 default `results/verify-ledger.sqlite` (git 밖, 재생성 가능).
- **Query를 1급 입력으로 둔다.** `queries(query_id, topic, claim_text, source, registered_at)`. `--query <id|file>` 인자를 `judge`·`report`·`recall`이 받는다. 정답 논문의 default query = 논문 topic + 주장 문장만으로 사람이 한 줄로 적어 `config/queries/gold-kv-reuse.yaml`에 등록한다. **G의 한줄평은 제외한다** — 「디테일한 분석은 없음」 같은 논문 평가문이라 근거 합치의 기준 명제로 쓸 수 없다(`user_note`에만 남는다). **판정 2는 `record × query`의 3분류 + 스팬**이고, `quote ↔ claim_text` 충실성은 **별도 하위 검사**(`faithfulness`)로 같은 행에 병기한다. 합치를 충실성으로 대체하지 않는다.
- `tools/verify/convert/{claude,codex}.py` — 위 행 단위 규칙대로. `kind`는 `config/kind_map.yaml`의 결정론적 매핑(실제 관측→measurement / 저자의 해석·논증·요약·가설→author_interpretation / 저자의 계산·시뮬레이션→extrapolation), 매핑 없으면 `kind_unmapped` 격리. Codex `conditions` 자유 산문은 `conditions_raw`로 보존하고 5필드는 채우지 않는다. 사유 코드: `no_quote`, `multi_fragment_no_quote`, `missing_condition_field`, `kind_unmapped`, `locator_unresolved`.
- `tools/verify/paragraphs.py` — 변형별 문단 분할(빈 줄 블록 + `quotes_coverage.py`의 ~60단어 재병합). 정답 논문 raw 기준 20단어 이상 블록 70개.
- **`config/thresholds.yaml`을 여기서 등록한다**(P7이 아니다). 항목: `l1_pass_grades`(아래 참조), `waiver_reason_required`, `elusion_n`(아래 프레임에서 역산), `sample_seed`, `mutation_detect_min`, `mutation_fp_max`, `kappa_report_only`, `escalation_max`, `leakage_n`, `expensive_call_ratio_max`, `tokens_per_record_max`, `wallclock_max_s`, `context_width_default`, `paragraph_unit`. 등록 후 sha256이 `runs.thresholds_sha256`에 박히고, 실행 중 변경되면 죽는다. **elusion 표집 프레임을 여기서 함께 확정한다**: 미사용 문단 = 문단 블록 전체에서 `claims` 행의 인용이 해결된 블록을 뺀 나머지이며, **격리 레코드(`multi_fragment_no_quote` 등)의 fragment는 「사용」으로 세지 않는다.** P1 말미에는 `paragraphs.py`와 두 변환기가 모두 있으므로 이 수를 실제로 세어 `elusion_n`을 **그 값 이하로** 등록한다. 실측(정답 논문, 20단어 이상 블록 70개): 행이 된 인용 51개가 32–35블록을 덮어 **미사용 풀 = 35–38(참고값. 블록 경계·매칭 규칙에 따라 흔들리며, 등록값은 P1 실측으로 받는다)**. 이것은 측정된 풀에서 역산하는 등록이지 사후 조정이 아니다(Principle 4와 충돌하지 않는다). 이 정의는 spec:94의 문언(「두 벌 어느 쪽도 쓰지 않은」)보다 좁다. 격리 레코드는 비교에 들어가지 않으므로 「인도된 레코드 집합의 누락」을 재는 쪽으로 한정한 것이며, 문언대로 세면 풀은 7이 된다.
- CLI: `verify ledger init`, `verify query register`, `verify convert claude|codex|waivers|gold`, `verify ledger import`, `verify thresholds register|show`.
- **닫는 AC:** C0-1, C0-2, C0-3, QUERY-1, OP-1.  `- [x] 완료` (2026-09-23, 브랜치 `verify-system`)
- **실행 기록 (P1).** 테스트 80개 통과, 커버리지 98%. 실측: Claude 30→44행(`no_quote` 2), Codex 37→7행(`multi_fragment_no_quote` 30), 문단 틀 70 · 사용 36 · **미사용 풀 34 → `elusion_n: 34` 등록**(참고값 35–38보다 작다. 인용이 그림 라벨로 끊겨 연속 일치가 안 되는 6행을 8단어 shingle ≥2개 일치로 해결한 결과. 연속 일치만 쓰면 40이고 6행이 위치 미해결). `thresholds.yaml` sha256 `bc642452b7f6…`. 결정 사항은 `docs/decisions.md`.
  - 이 환경에는 `sqlite3` 셸이 없다. AC의 `sqlite3 results/verify-ledger.sqlite "<sql>"`는 `.venv/bin/python -m tools.verify ledger sql "<sql>"`(읽기 전용)로 같은 값을 낸다.
  - QUERY-1의 `judge export` 절은 P3에서 닫는다. **기본 쿼리 `config/queries/gold-kv-reuse.yaml`은 에이전트 초안이며 `confirmed_by`가 비어 있다.** P3의 `judge export`는 `queries.require_confirmed`를 불러야 하고, 사용자가 확인(또는 새 id로 재작성)하기 전에는 거부된다.
  - `convert waivers`는 P2(V1-4), `convert gold`는 P5(B-1)에서 만든다.
  - 이후 단계에 넘기는 것: 모든 층은 진입 시 `thresholds.begin(conn)`을 부른다(등록 파일 기준 봉인 검사). P5 `recall`은 등록 뒤에 들어온 논문의 풀이 `elusion_n`보다 작으면 실행 시점에 거부한다. P6 `verify audit`은 감사자 신원·작성 경로를 강제한다(현재 trigger는 revise 감사 행 존재·`new_text` 일치·재사용 금지까지만 강제).

### P2 — L1 존재 검사 (모든 변형 · 일치 등급 · MISS 즉시 기각)  〔테이블: papers, checks, waivers〕

먼저 쓰는 테스트: `tests/verify/test_normalize.py`, `test_l1_exists.py`, `test_miss_blocks_downstream.py`.

- `config/normalization.yaml` — 고정 규칙 **6종**: 공백 접기, 하이픈·soft hyphen 통일, 따옴표 통일, 합자 풀기, 문장 첫 글자 대소문자 허용, **줄바꿈 접합으로 사라진 공백 복원**(`inferencesystem` ↔ `inference system`). 프로필 `strict`(6규칙)와 `loose`(비영숫자 전면 제거 = 기존 `quotes_verbatim_check.canon`).
- **일치 등급** `exact | strict | loose | MISS`(v2에서 `gapped` 추가 — 실행 기록 참조). **`l1_pass_grades: [exact, strict, loose]`를 임계 파일에 등록**하고 등급별 분포를 항상 함께 낸다. `WAIVED`는 verdict가 아니라 `waivers` 테이블의 별도 열이다 — L1 verdict 집합은 `{PASS, MISS}`로 닫힌다.
- 변형 집합은 **해당 논문에 실제로 있는 것만**: `codex_raw`, `codex_layout`, `claude_body`, (`claude_column`은 `splitwise`·`dualmap` 두 편뿐 → 정답 논문에서는 `unavailable`로 보고). 전 변형 MISS일 때만 MISS.
- **오프셋 의미 명문화**: PASS 행은 `matched_variant`와 그 변형 안의 `char_start/char_end`를 갖는다. MISS 행은 둘 다 NULL이며 **이것이 허용되는 유일한 NULL**이다.
- **MISS 즉시 기각**: `checks`에 `l1_verdict='MISS'`인 row_id는 L2·L6·judge·recall이 입력에서 제외한다(공용 뷰 `v_l1_passed`로 강제, 테스트로 확인).
- waiver 이관: 48행의 자유 서술 사유를 코드로 사상(`italic_reorder, gap_exceeded, stamp_intrusion, column_interleave, ligature, visual_check`). **정답 논문 행은 0건이므로 `waiver_rate`는 두 값으로 보고한다 — 정답 논문 `0/44`, 전체 `48/804`.**
- CLI: `verify l1 --paper <slug> --all-variants --report-variants`.
- **닫는 AC:** V1-1, V1-2, V1-3, V1-4, V1-5.  `- [x] 완료` (2026-09-23, 브랜치 `verify-system`)
- **실행 기록 (P2).** 테스트 127개 통과·4 skip(아직 없는 하위 층 모듈의 `v_l1_passed` 경유 검사 — 모듈이 생기면 자동으로 켜진다), 커버리지 98%. 결정 사항은 `docs/decisions.md`.
  - **protocol v1 실측**: Claude 44행 = exact 0 · strict 29 · loose 9 · **MISS 6**, Codex 7행 = exact 2 · strict 4 · loose 0 · **MISS 1**. PASS 44, MISS 7. Claude MISS 6행은 P1에서 shingle로만 위치가 풀린 그 6행으로, 원문에 있지만 쪽 머리글·그림 블록·쪽 넘김이 인용 한가운데 끼어 연속 일치가 없는 **거짓 음성**이었다.
  - **사용자 결정 → protocol v2 (2026-09-23)**: v1은 거짓 양성을 감수하고 끊긴 진짜 인용을 살린다. 등급 `gapped` 추가 — 인용 조각의 loose 형태를 **최대 3덩어리 · 덩어리당 20자 이상 · 덩어리 사이 원문 1,000자 이하**로 맞춘다(인용 글자는 전부 순서대로 맞아야 한다). `normalization.yaml` version 2, `thresholds.yaml` `protocol_ver: v2`, `l1_pass_grades: [exact, strict, loose, gapped]`, sha256 `7a79a963a011…`, verifier `l1-exists-v2`. **매개변수는 6행을 본 뒤 정한 사후 결정**이며 v1 등록(`bc642452b7f6…`)은 원장에 남는다.
  - **정답 논문 L1 (v2, 대표 수치, 결정 게이트 ①)**: Claude 44행 = exact 0 · strict 29 · loose 9 · **gapped 6** · MISS 0, Codex 7행 = exact 2 · strict 4 · gapped 0 · **MISS 1**. **PASS 50, MISS 1.** 변형별: `codex_raw` Claude 42/44, `claude_body` 44/44, `codex_layout` 1/44(두 단이 한 줄에 나란히 놓인 레이아웃), `claude_column: unavailable`. P3 judge 입력은 Claude 44 + Codex 6.
  - **Codex 「L1 통과가 구성상 보장」은 7행 중 1행에서 틀렸다**: `YR036.q1` fragment가 절 번호 `8`로 시작하는데 raw 텍스트는 그 번호를 다른 곳에 둔다. v2에서도 MISS(첫 덩어리가 3자짜리 우연 일치).
  - loose 9행 중 8행은 추출이 줄 끝 하이픈을 이미 지운 경우(`platform-hosted` → `platformhosted`), 1행은 수식 첨자다. 하이픈 규칙은 넓히지 않았다.
  - **V1-4 편차**: `waiver_rate` 전체값은 계획의 `48/804`가 아니라 **`48/1489 rows (46/804 records)`**로 낸다. waiver는 인용 단위인데 804는 원 레코드 수라 단위가 섞여 있었다. 정답 논문은 `0/44 rows`. reason code는 5종(italic_reorder 32 · stamp_intrusion 9 · gap_exceeded 5 · column_interleave 1 · visual_check 1, `ligature` 0).
  - 이후 단계에 넘기는 것: L2·L6·judge·recall은 행을 `ledger.l1_passed(conn, paper)`(뷰 `v_l1_passed`)로만 받는다. 새 모듈 이름이 `ledger.DOWNSTREAM_LAYERS`와 다르면 그 튜플도 고친다. `l1` 실행은 매번 새 run을 남기고 행마다 최신 L1 판정이 이긴다. **P6 `quote_word_swap` 변이 시험이 `gapped`의 거짓 양성률을 재는 자리다.**

### P3 — 얇은 수직 슬라이스: tier1 심판 1회 왕복 + 보고서 뼈대 → **결정 게이트**  〔테이블: queries, checks, budget〕

먼저 쓰는 테스트: `tests/verify/test_judge_io.py`, `test_judge_cascade.py`, `test_report_skeleton.py`.

- `tools/verify/judge.py` + `backends/lexical.py` (tier0, `verifier_id=lexical-v1`): 수치·단위·부정·양태·고유명 겹침으로 **라우팅만** 한다. 출력은 `insufficient` 또는 `needs-judge`이며 `supports`를 낼 수 없다(테스트로 강제). `escalation_rate`는 임계 통과가 아니라 **관측값**으로 보고한다.
- `verify judge export --tier mid --query <id> --context para --swap-order --limit 20` → 작업 JSON(쿼리 본문 + 인용 + 그 인용이 있는 문단 + `claim_text` 포함, **PDF 경로 포함 시 실패로 죽음**) + `manifest.sha256`.
- `verify judge import --verifier-id <id> --protocol-ver <v> --manifest <sha>` 가 강제하는 것: (1) manifest sha256 일치 → 에이전트가 행을 추가·삭제·수정할 수 없음, (2) **export 행 수 == import 행 수**, (3) `supports`/`refutes`의 `evidence_span` 오프셋이 원문에서 실제로 그 문자열로 해결됨, (4) `Unknown` 허용, (5) verdict 없는 행 거부.
- `tools/verify/report.py` 뼈대 — 네 판정 절을 모두 내되 **슬라이스 단계에서는 미실행 절에 `not-run`을 허용**한다. P7에서 「하나라도 비면 실패」로 조인다.
- `skills/claim-judge/SKILL.md` 초판(저장소 `.claude/skills/claim-judge`는 이 디렉토리로의 심볼릭 링크로 만든다. `~/.claude/skills`가 저장소로의 링크라 Claude는 그대로 찾는다) — 항목 단위(묶음 금지), 근거 스팬 선기술, Unknown 허용, 좌우 순서 교대, 출력 JSONL 스키마, 「PDF를 열지 말 것」, 「manifest를 고치지 말 것」.
- **결정 게이트 (사람이 읽고 다음을 정한다).** 슬라이스 실행이 내놓는 측정 사실: ① L1 변형별 일치 등급 분포 (Claude 44행 / Codex 7행), ② 조건 5필드 실제 충족 행 수, ③ `derived_from` 포인터가 있는 행 수, ④ tier1 20행의 3분류 분포와 `Unknown` 비율, ⑤ 20행 왕복의 토큰·벽시계. 이 다섯 값을 `results/slice-facts-<run_id>.json`에 적고, **P4~P6의 범위(특히 L6·변이 연산자·인수 시험 규모)를 여기서 확정한다.** **게이트의 권한은 여기까지다 — 등록 임계는 불변이고, 게이트는 `not-applicable` 판정과 실행 범위만 확정한다.** 사전 기대: ②③은 0에 가깝다 → 해당 층은 `applicable_rows: 0`을 정직하게 보고하는 것이 v1의 산출물이다.
- **닫는 AC:** V2-1, V2-2, V2-3, V2-4, JUDGE-1.  `- [x] 구현·측정 완료` (2026-09-23) · `- [ ] 결정 게이트(사람)`
- **실행 기록 (P3).** 테스트 162개 통과·3 skip, 커버리지 97%. 결정 사항은 `docs/decisions.md`.
  - **쿼리**: 판정 2는 계획대로 「어떤 주장이든 × L1 통과 전 행」 형태다(패턴 페이지 주장을 쿼리로 쓰는 인용 감사 형태는 기존 주장만 검사하므로 기본형에서 제외). 슬라이스는 시스템 시험용 쿼리 `gold-kv-reuse-v2`(「Production LLM serving traffic reuses prompt prefixes across requests.」, 사용자 승인)로 돌렸다. 초안 `gold-kv-reuse`는 미확인 상태로 남는다. 쿼리가 둘이라 V2-2 명령에는 `--query gold-kv-reuse-v2`가 필요하다.
  - 심판: Claude Sonnet 5 서브에이전트(새 컨텍스트, 스킬과 export만 봄), `verifier_id=claude-sonnet-5/subagent`, `protocol_ver=claim-judge-v1`. 추출기와 같은 계열임을 verifier_id로 드러낸다.
  - **결정 게이트 측정 사실** (`results/slice-facts-judge-workload__year-in-llm-serving-gold-kv-reuse-v2-001-import-01.json`):
    - ① L1 (protocol v2): Claude 44 = exact 0 · strict 29 · loose 9 · gapped 6 · MISS 0, Codex 7 = exact 2 · strict 4 · MISS 1.
    - ② 조건 5필드 충족 행: **0/50**. ③ `derived_from` 행: **0/50** (사전 기대대로).
    - ④ tier0: 50행 중 needs-judge 40 · insufficient 10, `escalation_rate 0.800`(관측값), tier2 미호출. tier1 20행: alignment supports 9 · insufficient 11 · refutes 0 · **unknown 0**, faithfulness supports 15 · insufficient 5. supports 9건 중 2건(YR-G1.q1, YR-G2.q2)은 설계 권고 문장을 근거로 삼아 엄격히 보면 insufficient다(P6 B-2 사람 라벨이 잴 몫). tier0이 올린 20행 중 11행이 insufficient로 끝났다.
    - ⑤ 왕복 비용: **163,683 토큰(서브에이전트 총량, 입출력 구분 없음) · 648초 / 20행 ≈ 8,200 토큰/행** — 등록 상한 `tokens_per_record_max: 4000`의 약 2배. 스킬 읽기·자체 검증 스크립트의 고정 비용이 섞여 있어 행당 순비용은 더 작지만 지금은 분리할 수 없다. (이후 사용자 결정으로 예산 상한을 없앴다 — 아래 v3.)
  - 보고서 뼈대: `reports/verify-report-workload__year-in-llm-serving.md`(존재·합치 채움, 재현율·조건 보존 `not-run`).
  - `results/judge/`의 export·manifest·verdicts와 slice facts는 커밋 대상으로 둔다(verdicts는 재생성할 수 없는 감사 기록).
  - **사용자 결정 → protocol v3 (2026-09-23)**: 검증에 토큰 예산을 두지 않는다. `tokens_per_record_max`·`wallclock_max_s`·`expensive_call_ratio_max`를 임계 파일에서 뺐다(sha256 `3906ce67700a…`, v1·v2 등록은 원장에 남음). 대신 **심판 왕복 전후의 5시간 한도 사용률**을 기록한다: `judge export`가 시작 스냅샷, `judge import`가 끝 스냅샷을 원장에 남기고 import 출력·보고서·slice facts에 `5h usage: a% -> b% (+Npt, M min, account-wide)`로 낸다(`config/usage.yaml`, `tools/verify/usage.py`). 출처는 statusline이 2분마다 갱신하는 `/tmp/.claude-usage-cache.json`이며 statusline은 고치지 않았다. 계정 전체 값이고, 창이 도중에 초기화되면 `reset during run`, 5분보다 오래된 스냅샷은 `stale snapshot`, 못 읽으면 `unavailable`로 적는다. 첫 왕복(import-01)은 이 기능 전이라 사용률 기록이 없다.

### P4 — L2 스키마/태그 · L6 산술  〔테이블: claims, checks〕

먼저 쓰는 테스트: `tests/verify/test_l2_schema.py`, `test_l6_arith.py`, `test_stats.py`.

- `tools/verify/l2_schema.py` — 조건 5필드 존재/「없음」 명시, 수치의 단위·정의, 비교 행의 기준선, `kind` 태그. 판정 `pass | quarantine` + 사유 코드. 격리 행은 `comparable=0`.
- **L2 격리율의 지위 변경:** 이것은 **입력 진단치**이며 **사전 기대값은 두 벌 모두 100%**다(두 레코드 벌 어디에도 5필드 키가 없다). 「스키마 계약이 구속력을 갖는다는 증거」가 아니라 입력 형식의 기술이다. **v1의 대표 수치 자리는 L1 변형별 일치 등급 분포가 갖는다.**
- `config/modality.yaml` — 양태 어휘(may/might/suggests/in our setting ↔ is/always/all). L2가 인용과 `claim_text`의 양태 등급 차이를 결정론적으로 플래그.
- `tools/verify/l6_arith.py` — `derived_from` 재계산(비율 증감, 비의 평균은 기하평균), 같은 논문 안의 `intra_doc_conflict`, 단위 환산 일관성. `codex_verify_metric_sources.py`의 fragment sha256 + raw/layout 이중 존재 검사를 이식. **`derived_from` 포인터는 두 벌 모두 0행이므로 v1 보고는 `applicable_rows: 0`이 정상이며, 실제로 도는 것은 `numbers` 자유 문자열 파싱 + intra-doc 대조다.**
- `tools/verify/stats.py` — Clopper–Pearson 정확 이항, Cohen κ, 부트스트랩(`random.Random(seed)`), Chapman 추정. stdlib만.
- **닫는 AC:** V4-1, V4-2, V4-3.  `- [x] 완료` (2026-09-23, V4-1·V4-2·`stats.py`) · `- [ ] V4-3` (P6 `inject`와 함께 닫는다)
- **실행 기록 (P4).** 테스트 245개 통과·1 skip(`recall.py` 미작성), 커버리지 97%(`l2_schema` 100%, `l6_arith` 96%, `stats` 95%). 결정 사항은 `docs/decisions.md`. 결정 게이트는 계획대로 확정(L2 격리율 = 입력 진단치, L6 `derived_from` = `applicable_rows: 0`). 두 층 모두 `ledger.l1_passed`로만 행을 받는다(`test_miss_blocks_downstream.py`가 두 모듈에서 켜짐).
  - **L2** (`l2-schema-v1`, `config/modality.yaml`·`config/comparison.yaml`): 계약 검사는 `schema.validate`를 원장 열(조건·수치·kind·인용·주장)에 그대로 돌리고, 여기에 비교 행의 `baseline: "none"`(`comparison_without_baseline`)과 양태 상승(`modality_raised`, hedged < plain < universal에서 주장이 인용보다 위)을 더한다. 사유가 하나라도 있으면 `quarantine`·`comparable: 0`. 판정 집합은 trigger `checks_l2_closed`로 닫힌다.
  - **정답 논문 L2 (V4-1)**: 50행 = pass 0 · **quarantine 50 → `quarantine_rate: 1.000 (50/50) — input diagnostic, prior expectation 100%`**(claude 44/44, codex 6/6). 사유: `missing_condition_field` 50, `missing_number_field` 47(수치 없는 3행 제외), `modality_raised` 6. 양태 6건 중 2건(`YR-B5.q2`, `YR-G1.q1`)은 「shows up」 뜻의 `appears`에 걸린 **어휘 거짓 양성**, 4건은 긴 인용 안의 `may` 절을 주장이 옮기지 않은 경우다(절 단위가 아니라 인용 전체 단위 플래그). 측정 뒤 어휘를 고치지 않았다.
  - **L6** (`l6-arith-v1`, `config/numbers.yaml`): `derived_from` 식 재계산(인쇄 자릿수 반 단위 허용, 비의 산술평균 플래그), 자유 문자열의 수치·단위 파싱과 문자열 안 `a / b ≈ c` 재계산, 키 붙은 값(`P99 ≈ 15분`)의 단위 환산 후 같은 논문 다른 레코드 간 `intra_doc_conflict`, Codex fragment sha256 + raw/layout 존재(옛 `codex_verify_metric_sources.py` 이식; `--source-root` 없으면 건너뜀). 판정 `pass | flag`, trigger `checks_l6_closed`.
  - **정답 논문 L6 (V4-2)**: **`derived_from: applicable_rows: 0 (of 50 rows)`**. 수치 문자열 있는 행 47/50, 값이 파싱된 행 43, 값 337개, 「미보고」 표지 15행, 「우리 쪽 계산」 표지 2행. 문자열 안 산술 1건(`YR-A1` 35,795,761 / 2,522,394 ≈ 14.2) 일치. 키 붙은 값 8개, **`intra_doc_conflict` 0쌍**. Codex fragment 6행: sha256 6/6 일치, codex_raw 5/6, codex_layout 0/6(두 단이 한 줄), **어느 쪽에도 없음 1 → `codex:YR023.q1` flag** — fragment가 절 머리 `6.3 Cache Simulations`로 시작하는데 raw 텍스트는 그 머리를 다른 곳에 둔다(`YR036.q1`과 같은 꼴). L1은 `claude_body`에서 strict로 통과시켰으므로 L1 판정과 L6 flag가 갈리는 행이다.
  - **`stats.py`**: Clopper–Pearson(양측·단측 상한/하한, 이항 CDF 이분법), Cohen κ(우연 일치 1이면 `None`), 백분위 부트스트랩(`random.Random(seed)`, 정의되지 않는 재표본은 건너뛰고 `n_valid`로 셈), Chapman. 0오류 단측 95% 상한은 n=7→34.8%, n=20→13.9%, n=34→8.4%, n=38→7.6%로 계획 수치와 일치.
  - 보고서: 「Condition preservation」 절이 최신 L2·L6 실행으로 채워지고, 「Not applicable」에 `derived_from` 재계산이 올라간다(재현율 절만 `not-run`).
  - V4-3(`inject` 다섯 연산자 표)은 `inject.py`가 필요해 P6에서 닫는다. 이후 단계에 넘기는 것: P6 `modality_raise`의 표적은 L2 `modality_raised`, `unit_change`·`number_transpose`는 L6(단, v1 행에는 `derived_from`과 키 붙은 값이 거의 없어 검출 경로가 문자열 안 산술 1건과 키 값 8개뿐이다), `condition_delete`·`condition_widen`은 5필드가 없어 `not-applicable`. P5 elusion 상한과 P6 κ·부트스트랩은 `stats.py`를 쓴다.

### P5 — 재현율 (G recall + elusion)  〔테이블: gold, paragraphs, checks〕

먼저 쓰는 테스트: `tests/verify/test_gold_parse.py`, `test_recall.py`, `test_elusion.py`.

- `tools/verify/convert/gold.py` — G(6.6 KB 한 줄)를 문장 단위로 파싱. **분할 규칙을 파일에 고정**: **`**`/`****` 강조 표지 분리(첫 본문 문장 `User behavior induces temporal locality…`가 한줄평과 `****`로 접합되어 있어 이 처리가 없으면 통째로 유실된다)**, `. ` 뒤 대문자 시작, `->` 절단과 **메모가 어디서 끝나는지**(다음 원문 문장 시작까지), `Figure Na`/`10^2` 등 약어·지수 분할 금지 목록. **한줄평과 `->` 뒤 메모는 `user_note`로 분리**하고 본문과 섞지 않는다. **등록 기준 수치는 규칙을 돌려서 얻은 값으로 적는다 — 규칙 산출값(등록 시 기록).** 임시 계수를 그대로 쓰지 않는다: 같은 원문에 대해 iteration 1의 임시 계수는 33, 리뷰의 재계수는 37이었고, 메모 종료 지점을 어떻게 잡느냐에 따라 값이 크게 흔들린다는 것이 이 수치를 규칙에서만 받아야 하는 이유다. `user_note` **6건**(한줄평 1 + `->` 5)은 실측 확정. 경계 복원 행은 `boundary_repaired=1`.
- `tools/verify/recall.py` — (1) G 대비 재현율·정밀도를 `claude / codex / union` × `claim_present / conditions_match / numbers_match`로, (2) **탐침 P와 목표 집합 T는 `not-applicable: extractor runs are frozen`으로 보고한다** — 두 레코드 벌은 이미 동결되어 있어 지금 심는 탐침은 추출기가 아니라 recall 코드를 시험하고, Cormack–Grossman target method는 목표를 측정 대상 실행 **이전에** 독립 표집할 것을 요구하는데 오늘 고르는 T는 어떤 방식이든 사후다, (3) **재현율 신뢰 진술은 G 대비 재현율 + elusion 상한만으로 낸다.** 표집 프레임은 P1에서 확정한 「미사용 문단」 정의(격리 레코드의 fragment는 사용으로 세지 않음)를 그대로 쓴다. **달성 가능한 상한을 그대로 보고한다** — 0오류 기준 95% 정확 이항 상한은 n=7→34.8%, n=20→13.9%, **n=38(실측 풀 전체)→약 7.6%**. `elusion_n`은 P1에서 등록되고, 같은 `(run_id, paper)`에서 재표집을 시도하면 종료 코드 1, (4) 포획-재포획 Chapman은 독립된 두 벌이 있을 때만 내고 `lower_bound: true`를 박는다.
- **닫는 AC:** B-1, V3-1, V3-2, V3-3, V3-4.  `- [x] 완료` (2026-09-23, 브랜치 `verify-system`) · `- [ ] elusion 표본 검토(검토자 결정 대기)`
- **실행 기록 (P5).** 테스트 297개 통과(skip 0 — `test_miss_blocks_downstream`이 `recall.py`에서도 켜짐), 커버리지 97%(`recall` 98%, `convert/gold` 97%). 결정 사항은 `docs/decisions.md`.
  - **G 분할 (B-1)**: 규칙은 `config/gold_split.yaml`(`gold-split-v1`). **`gold_split_count: 40`**(규칙 산출값, iteration 1의 33·리뷰의 37과 다름), `user_notes: 6`(한줄평 1 + `->` 5), 제목 1건은 gold가 아니다, `boundary_repaired` 24. `****` 뒤 첫 문장 `User behavior induces temporal locality…`가 살아남고, 문장에 메모·한글·`->`·`**`가 0건. 메모 끝은 메모 안에서만 쓰는 세 경계(마침표 + 대문자, `promptsOutput` 같은 소문자·대문자 접합, `opportunities While` 같은 문장 시작어)의 가장 이른 곳이다. **`->` 메모 5건 중 4건의 영어 본문은 실제로 논문 문장이다**(사용자가 원문을 옮겨 적고 `->`로 표시). 규칙은 사용자의 표시를 따르고 메모를 본문으로 되돌리지 않았다.
  - **G 재현율 (V3-1)**: `recall-v1`(`config/recall.yaml`), 행은 `ledger.l1_passed`로만(Claude 44 · Codex 6. Codex는 계획의 7행 중 L1 MISS `YR036.q1`이 빠진다). claim_present = Claude **23/40**(P 14/44), Codex **0/40**(P 0/6), union **23/40**(P 14/50) → **union = claude**. numbers_match = 수치가 있는 G 문장 3개 중 3(Claude). conditions_match = `not-applicable`(G에 조건 라벨이 없고, 5필드를 가진 행이 0/50). 포함 판정은 두 봉우리로 갈린다: 덮인 23문장은 전부 coverage 1.0, 못 덮인 17문장은 어떤 인용과도 23자 이상 연속으로 겹치지 않는다(임계 40자·50%는 결과를 가르지 않는다). 첫 실행에서 소문자 `figure 4b`를 수치 4로 읽은 버그를 고치고(테스트 추가) 원장을 P5 이전 사본으로 되돌려 다시 돌렸다.
  - **탐침·목표 집합 (V3-2)**: `probes P` / `target set T`: `not-applicable: extractor runs are frozen` + 사유 문장.
  - **elusion (V3-3)**: 틀 70 · 사용 36 · **미사용 풀 34**(P1 틀 그대로), `elusion_n: 34` → **표본 = 풀 전체**. 표본 `elusion-workload__year-in-llm-serving-8b8cc779427e` → `results/elusion/elusion-workload__year-in-llm-serving.tsv`(커밋 대상, 원장에 sha256 봉인). 같은 추출 실행으로 다시 뽑으면 `resampling forbidden`, 종료 코드 1. 0오류 상한 **8.4%(n=34)**, 5%는 n≥59가 필요해 k=1에서 도달 불가라고 출력한다. **G 하한**: 못 덮인 G 문장 중 6개가 풀 블록 3개(`#0047`, `#0341`, `#0541`)에 있다 → 검토가 이 문장들을 누락으로 세면 k≥3, 상한 ≥ **21.3%**. 나머지 11개는 이미 다른 행이 쓰는 블록 안에 있어 블록 단위 elusion으로는 보이지 않는다. **검토(`--elusion-import TSV --reviewer NAME`)는 미실행**이다. 사람이 34블록을 읽을지(스펙 48의 사람 시간을 새로 쓴다), 에이전트 판정으로 할지는 사용자가 정한다.
  - **포획-재포획 (V3-4)**: 단위 = 틀 블록. Claude 44행 → 34블록, Codex 6행 → 7블록, 겹침 6 → `chapman_estimate: skipped: asymmetric sets (… ratio 0.14 < min_size_ratio 0.5)`, `lower_bound: true`. 한 벌만이면 `skipped: single extractor set`. `min_size_ratio`는 `config/recall.yaml`에 있다(`thresholds.yaml`은 봉인되어 있어 키를 더하면 새 protocol_ver가 필요하다).
  - 보고서: 「Recall」 절이 채워져 `report --strict`가 통과한다(네 절 모두 채워짐). 「Not applicable」에 P·T와 conditions_match가 올라간다.
  - 이후 단계에 넘기는 것: P6 B-4 `verify audit`은 `gold` 행(`<slug>:sNNN`, `:nNN`)을 대상으로 한다. `gold` 등록은 `runs.gold-register`의 `items_sha256`에 봉인되어, 같은 파일은 다시 등록해도 no-op이고 다른 분할은 거부된다. 재현율 checks 행은 `layer='recall'`, `row_id=gold_id`다.

### P6 — 인수 시험 (A · B · C · D·E)  〔테이블: injections, audits, gold, checks, budget〕

먼저 쓰는 테스트(= 산출물 자체가 테스트): `test_inject.py`, `test_metamorphic.py`, `test_retest.py`, `test_differential.py`, `test_regression_known_errors.py`, `test_gaming.py`, `test_leakage.py`, `test_context_cut.py`, `test_budget.py`.

- `tools/verify/inject.py` — 연산자 **9종 = 오류 8 + 등가 1**: `quote_word_swap`, `number_transpose`, `unit_change`, `condition_delete`, `condition_widen`, `modality_raise`, `paper_swap`, `claim_quote_shuffle` + 등가 `synonym_swap`. 각 50건, 시드는 등록.
  - **검출의 정의: 기준선 실행 대비 `verdict` 또는 `reason_code`의 변화.** 변화 없음 = 미검출.
  - **`not-applicable` 규칙:** 대상 필드가 부재해 변이를 구성할 수 없는 조합(예: 5필드가 없는 행에 `condition_delete`·`condition_widen`)은 `not-applicable`로 보고하고 **UNVERIFIED 판정에서 제외한다.** 이 규칙이 없으면 L2는 어느 검출 정의로도 영구 UNVERIFIED가 되어 게이트가 구조적으로 통과 불가다.
  - 보고 표: 연산자 8행(오류) + `synonym_swap` 오탐률 1행, 각 행에 `n`, `detected`, `not_applicable`, `rate`.
- **B-2 사람 κ — G에는 합치 라벨이 없다.** 채택안 (a): **사람 라벨의 대상은 P3 슬라이스가 tier1에 태운 `record × query` 행과 동일한 행 집합이다 — 20행, 가능하면 L1 PASS 51행 전부.** 그 행에 default query 기준 3분류를 사람이 한 번 붙이고(약 30분, v1에서 유일하게 새로 드는 사람 시간), κ는 **그 행 단위로 심판 판정과 짝지어** 낸다. **G의 정답 문장은 재현율 기준으로만 쓰고 κ 짝짓기에는 쓰지 않는다**(사람은 문장에, 심판은 레코드 행에 라벨하면 짝지을 단위가 없다). 결과는 `config/gold_labels.tsv`에 등록하며, **`thresholds.yaml`과 마찬가지로 등록 시 sha256을 출처 묶음에 박는다** — 판정을 본 뒤 라벨을 고치는 문을 닫기 위해서다. `tools/verify/agree.py`가 κ와 부트스트랩 CI를 **보고만** 하고 **pass/fail 게이트를 걸지 않는다**(n=20~51 규모에서는 진짜 κ≈0.85인 심판도 절반 안팎의 확률로 떨어진다). 단순 일치율 단독 보고 금지는 유지. **라벨을 G에서 기계적으로 파생하는 것은 금지**(Principle 2).
- **B-3 회귀 케이스의 v1 범위.** 9-15 리뷰 16건·`claude_50` §1-a 21건·merge-log N6 5쌍·waiver 48건은 **전부 정답 논문 밖**이다. v1 예외: **그 케이스들이 가리키는 논문의 Claude 레코드만 추가 변환한다**(슬러그 목록을 `tests/verify/fixtures/known_errors.tsv`에 적고 변환기를 그 슬러그에만 돌린다). 케이스 파일은 **이미 문서에 표로 존재하는 것만 옮겨 적고 새로 창작하지 않는다**(Principle 5). 미검출 케이스는 `skip_reason` 없이는 실패.
- 메타모픽 4관계: (a) 순서·좌우 교대 불변, (b) 무관 문단 추가에도 존재 판정 불변, (c) 수치 변경 시 보존 판정의 방향성, (d) 부분집합 실행 = 전체 실행.
- C-2 재검사 일치(tier별 뒤집힘 비율), C-3 차등(`codex_raw` vs `codex_layout` 불일치 → `hard_cases.tsv`).
- **DE-1 추출 노이즈(D3)에 순환성 주석을 단다.** 실측: G 본문에 `inferencesystem`·`broadaccess`·`MiniMaxM2.5`·`10^2`가 있고 이 문자열은 `codex_raw`에만 있다 → **G는 codex_raw 추출본을 붙여 넣은 것**이다(리뷰 시점의 표본 33문장 대조 — 등록 수치가 아니다: codex_raw strict 23 + loose 8, claude_body strict 12 + loose 19, codex_layout strict 3). 따라서 「layout 단독이면 MISS였을 문장 수」는 크게 나올 수밖에 없고, **이 시험은 독립 대조가 아니라 추출 노이즈 진단**으로만 읽는다고 보고서에 적는다.
- DE-2 누출률(등록된 `leakage_n`), DE-3 컨텍스트 절단(quote / quote+para / quote+para±1 → `minimal_sufficient_context`), DE-4 예산(`budget` 테이블 → 1,000행 환산·고가 호출 비율과 심판 왕복 전후 5시간 한도 사용률 변화, **보고만 한다** — v3에서 예산 상한 제거).
- D2 게이밍: `tests/verify/fixtures/gaming_records.jsonl`(최소 노력 레코드). 통과하면 테스트가 실패하고 어느 검사가 우회됐는지 출력.
- `verify audit` — 감사-후-채점 대기열 + `audits` 기록. `gold` 수정은 trigger 때문에 `audits` 경유로만 가능하고 `gold.revision`이 오른다.
- **닫는 AC:** A-1, A-2, A-3, B-2, B-3, B-4, C-1, C-2, C-3, DE-1, DE-2, DE-3, DE-4, DE-5.  `- [ ] 완료`

### P7 — 게이트 · 보고서 · 스킬 · 커버리지  〔테이블: runs, checks 전부〕

먼저 쓰는 테스트: `test_gate.py`, `test_report.py`.

- `tools/verify/gate.py` — 등록 임계 대비 판정, **UNVERIFIED 표기**(자기 표적 변이 유형에서 등록 검출률 미달 시 그 층의 pass를 무효화)와 **`UNTESTED(not-applicable)` 표기**(변이를 구성할 수 없어 시험 자체가 없었던 층 — 미달과 구분한다), 출처 묶음 `results/verify-bundle-<run_id>.json` 봉인(입력 해시·runs·checks·audits·injections·임계 파일과 sha256). 미달이면 종료 코드 1.
- `tools/verify/report.py` — P3의 뼈대를 조인다: **네 판정 절이 모두 채워져야 하며 하나라도 `not-run`이면 파일을 쓰지 않고 실패.** 각 절에 `verifier_id`·`protocol_ver`·임계 대비·**L1 등급 분포(대표 수치, B-3 예외 논문이 원장에 있으면 논문별로 분리 집계)**·waiver_rate 두 값·L2 격리율(입력 진단치 표기)·예산 실적·`not-applicable` 목록.
- `skills/verify-run/SKILL.md`(`.claude/skills/verify-run` 링크도 함께) — convert → ledger import → query register → l1 → (MISS 제외) → judge export/import → l2 → l6 → recall → inject → accept → gate → report 순서와 「임계는 실행 전 등록, 실행 중 수정 금지」.
- 커버리지: `.venv/bin/coverage run -m pytest tests/verify -q && .venv/bin/coverage report --include='tools/verify/*' --fail-under=80`.
- **닫는 AC:** REPORT-1, SKILL-1, TEST-1.  `- [ ] 완료`

---

## Acceptance Criteria

표기: `[R]` = 명령 하나로 실행 가능(CI/pytest 진입 가능), `[S]` = 에이전트 파일 왕복이 선행하는 시나리오.

- [x] **C0-1 [R]** `.venv/bin/python -m tools.verify schema --print-required` 가 `record_id, paper_id, quote, locator, claim_text, conditions(5), numbers[], kind, extractor_id, run_id` 를 모두 출력하고 `config/evidence_record.schema.json` 이 존재한다.
- [x] **C0-2 [R]** `.venv/bin/python -m tools.verify convert claude --paper workload__year-in-llm-serving` 이 `source_records: 30, rows: 44, quarantined_records: 2 (no_quote), closed: 30/30` 을, `... convert codex ...` 가 `source_records: 37, rows: 7, quarantined_records: 30 (multi_fragment_no_quote), closed: 37/37` 을 출력한다 — **원 레코드 전부가 행 산출 또는 사유 코드 붙은 격리로 닫힌다.**
- [x] **C0-3 [R]** `.venv/bin/python -m pytest tests/verify/test_schema.py -q` — 조건 값이 `"none"`이면 pass, 키가 없으면 `quarantine(missing_condition_field)`.
- [x] **QUERY-1 [R]** `.venv/bin/python -m tools.verify query register --file config/queries/gold-kv-reuse.yaml` 후 `sqlite3 results/verify-ledger.sqlite "select count(*) from queries"` 가 `1` 이고, `judge export` 산출 JSON의 모든 항목에 `query.topic` 과 `query.claim_text` 가 들어 있다.
- [x] **OP-1 [R]** `.venv/bin/python -m tools.verify thresholds register` 가 P1 말미에 성공하고 `runs.thresholds_sha256` 이 채워지며, 파일을 실행 중 고치면 `thresholds changed mid-run` 으로 죽는다 (`tests/verify/test_thresholds.py`).
- [x] **V1-1 [R]** `.venv/bin/python -m tools.verify l1 --paper workload__year-in-llm-serving --all-variants --report-variants` 가 `codex_raw / codex_layout / claude_body` 각각의 일치 수를 내고 `claude_column: unavailable` 을 명시하며(정답 논문에 없는 변형을 요구하지 않는다), **`l1_tautological=1` 행(Codex 7행)을 별도 열로 분리해 집계**한다.
- [x] **V1-2 [R]** `config/normalization.yaml` 에 6규칙(공백·하이픈·따옴표·합자·문장 첫 글자·줄바꿈 접합 공백)이 있고 `.venv/bin/python -m pytest tests/verify/test_normalize.py -q` 가 규칙별 단위 테스트로 통과한다.
- [x] **V1-3 [R]** 같은 l1 명령이 **행마다 `(verdict, matched_variant, char_start, char_end, grade)`** 를 내고, `verdict=PASS` 행의 오프셋 4값이 전부 non-null이며 `verdict=MISS` 행만 `matched_variant/char_*`가 NULL이다(그 외 NULL 0건).
- [x] **V1-4 [R]** `.venv/bin/python -m tools.verify convert waivers` 후 `sqlite3 ... "select count(*), count(distinct reason_code) from waivers"` 가 `48|<=6` 을 내고, 보고서가 `waiver_rate` 를 **두 값**(`gold: 0/44`, `overall: 48/804`)으로 적는다.
- [x] **V1-5 [R]** `.venv/bin/python -m pytest tests/verify/test_l1_exists.py::test_verdict_closed tests/verify/test_miss_blocks_downstream.py -q` — L1 verdict 집합이 `{PASS, MISS}` 로 닫히고(WAIVED는 별도 테이블), `l1_exists.py` 가 judge/backends를 import하지 않으며, MISS 행이 L2·L6·judge·recall 입력에서 제외된다.
- [x] **V2-1 [S]** `judge export --tier mid --query gold-kv-reuse --limit 20` → 에이전트 판정 → `judge import` 후, 해당 20행 전부가 `supports|refutes|insufficient|unknown` 중 하나와 원문에서 해결되는 `evidence_span` 을 갖고, **`alignment`(record × query)와 `faithfulness`(quote ↔ claim_text)가 별도 열로 병기된다.**
- [x] **V2-2 [R]** `.venv/bin/python -m tools.verify judge sweep --backend lexical --paper workload__year-in-llm-serving` 이 L1 PASS 전 행을 돌고 `escalation_rate` 와 `expensive_ratio` 를 **관측값으로** 출력한다(임계 통과 주장을 하지 않는다. tier2 미호출 시 `expensive_ratio: 0 (tier2 not invoked)`).
- [x] **V2-3 [R]** `sqlite3 ... "select count(*) from checks where verifier_id is null or protocol_ver is null"` 이 `0` 이고, 두 열이 DDL에서 `NOT NULL` 임을 `test_ledger.py` 가 확인한다.
- [x] **V2-4 [R]** `.venv/bin/python -m pytest tests/verify/test_judge_io.py -q` — `evidence_span` 빈 `supports`/`refutes` 거부.
- [x] **JUDGE-1 [R]** 같은 테스트 파일에서 (1) manifest sha256 불일치, (2) export 행 수 != import 행 수, (3) 스팬 오프셋이 원문에서 해결되지 않음 — **세 경우 모두 import가 거부**한다.
- [x] **V3-1 [R]** `.venv/bin/python -m tools.verify recall --paper workload__year-in-llm-serving --query gold-kv-reuse` 가 `claude / codex / union` × `claim_present / conditions_match / numbers_match` 3×3 재현율·정밀도 표를 내고, **`codex` 열이 7행 기준이라 `union ≈ claude` 가 된다는 사실을 표 각주로 적는다.**
- [x] **V3-2 [R]** 같은 출력이 탐침 P와 목표 집합 T를 `not-applicable: extractor runs are frozen` 으로 보고하고, 그 사유 문장을 함께 적는다(공허한 `10/10` 주장을 하지 않는다).
- [x] **V3-3 [R]** `... recall --elusion-export /tmp/elusion.tsv` 가 (1) P1에서 확정한 프레임으로 **미사용 풀 크기를 출력하고**(정답 논문 참고값 35–38), (2) 등록된 `elusion_n ≤ 풀 크기` 만큼 정확히 표집하며, (3) 0오류 기준 Clopper–Pearson 상한을 **달성 가능한 값 그대로**(n=35→약 8.2%, n=38→약 7.6%) 보고하고, (4) 같은 run_id로 재실행하면 `resampling forbidden` 으로 종료 코드 1이다. **5% 상한은 k=1에서 도달 불가이며 그 사실을 출력에 적는다.**
- [x] **V3-4 [R]** 같은 출력의 포획-재포획 절이 `chapman_estimate` 와 `lower_bound: true` 를 함께 적고, 한 벌만 있을 때 `skipped: single extractor set` 을, **44 대 7처럼 비대칭일 때 `skipped: asymmetric sets` 를** 적는다.
- [x] **V4-1 [R]** `.venv/bin/python -m tools.verify l2 --paper workload__year-in-llm-serving` 이 L1 PASS 전 행의 조건 5필드 판정을 내고, 요약에 `quarantine_rate` 를 **`input diagnostic, prior expectation 100%`** 라벨과 함께 적는다.
- [x] **V4-2 [R]** `.venv/bin/python -m tools.verify l6 --paper workload__year-in-llm-serving` 이 `derived_from` 재계산 대상을 `applicable_rows: 0` 으로 **명시적으로** 보고하고, 별도로 `numbers` 자유 문자열 파싱 결과와 `intra_doc_conflict` 쌍 수를 낸다.
- [ ] **V4-3 [R]** `.venv/bin/python -m tools.verify inject --operators unit_change,number_transpose,condition_delete,condition_widen,modality_raise --n 50` 이 다섯 유형의 `detected / not_applicable / rate` 를 표적 층과 함께 표로 낸다.
- [ ] **A-1 [R]** `.venv/bin/python -m tools.verify inject --all --n 50 --report /tmp/mutation.md` 가 **오류 연산자 8행 + 등가 연산자 1행 = 9행** 표를 만들고, 각 행이 `n=50` 과 `not_applicable` 수를 함께 적는다.
- [ ] **A-2 [R]** 같은 보고서의 `synonym_swap` 행이 **오탐률**로 표기되고 `thresholds.yaml` 의 `mutation_fp_max` 와 대조된다.
- [ ] **A-3 [R]** `.venv/bin/python -m pytest tests/verify/test_gate.py::test_unverified_marking -q` — 검출률이 등록 임계 아래인 층은 `UNVERIFIED` 로 표기되고, **`not-applicable` 조합만 남은 층은 UNVERIFIED가 아니라 `UNTESTED(not-applicable)` 등급으로 표기된다**(무판정과 미달을 구분한다).
- [x] **B-1 [R]** `.venv/bin/python -m tools.verify convert gold --paper workload__year-in-llm-serving` 이 **분할 규칙 산출값만큼의 본문 문장**(하드코딩 금지, 등록 시 수치를 `gold_split_count` 로 기록)과 `user_note` **6건**(한줄평 1 + `->` 5)을 분리해 등록하고, 첫 본문 문장 `User behavior induces temporal locality…` 가 `****` 접합에서 살아남으며, `gold.text` 에 메모 문자열이 0건 섞인다.
- [ ] **B-2 [S]** `config/gold_labels.tsv` (**P3가 tier1에 태운 것과 같은 행 집합** × 3분류, 사람 30분, 등록 시 sha256이 출처 묶음에 박힘) 등록 후 `.venv/bin/python -m tools.verify agree --query gold-kv-reuse --bootstrap 2000` 이 **행 단위로 짝지은** `kappa` 와 부트스트랩 CI를 **보고만** 하고 종료 코드 0으로 끝난다(pass/fail 게이트 없음). 짝지을 수 없는 라벨이 있으면 `unpaired labels` 로 죽는다. 단순 일치율 단독 보고는 `test_agree.py` 가 막는다.
- [ ] **B-3 [R]** `.venv/bin/python -m pytest tests/verify/test_regression_known_errors.py -q` — `fixtures/known_errors.tsv` 의 케이스(9-15 리뷰 16 + `claude_50` §1-a 21 + merge-log N6 5 + waiver 48)가 **해당 슬러그의 Claude 레코드만 추가 변환한 상태**에서 돌고, 미검출은 `skip_reason` 없이는 실패한다.
- [ ] **B-4 [S]** `verify audit --queue /tmp/q.tsv` → 감사자 판정 입력 → `sqlite3 ... "select revision, count(*) from gold group by revision"` 에 수정 이력이 남고, `UPDATE gold SET text=...` 직접 실행은 trigger가 거부한다.
- [ ] **C-1 [R]** `.venv/bin/python -m pytest tests/verify/test_metamorphic.py -q` — 순서 불변 / 무관 문단 추가 불변 / 수치 변경 방향성 / 부분집합 독립성 네 관계가 각각 테스트로 존재한다.
- [ ] **C-2 [S]** `verify accept retest --runs 2` (tier1 왕복 2벌 선행) 가 tier별 판정 뒤집힘 비율을 출력한다.
- [ ] **C-3 [R]** `.venv/bin/python -m tools.verify accept differential --variants codex_raw,codex_layout --out /tmp/hard_cases.tsv` 가 불일치 행을 모으고, **대상이 Codex 7행뿐이라 수집이 거의 빈다는 사실을 출력에 적는다.**
- [ ] **DE-1 [R]** `.venv/bin/python -m tools.verify accept noise --paper workload__year-in-llm-serving` 이 네 축(하이픈 분절·합자·열 순서·각주)의 오탐률과 **「layout 단독이면 MISS였을 문장 수」**를 내고, 출력에 **`caveat: G was pasted from codex_raw; this is an extraction-noise diagnostic, not an independent comparison`** 을 함께 적는다.
- [ ] **DE-2 [S]** `verify accept leakage --tier mid --sample <thresholds.leakage_n>` (tier1·tier2 왕복 선행) 이 통과분 오판 비율과 Clopper–Pearson 상한을 낸다.
- [ ] **DE-3 [S]** `verify accept context-cut --widths quote,para,para1` (export 3벌 × 에이전트 판정 선행) 이 폭별 변화율과 `minimal_sufficient_context` 한 값을 기록한다.
- [ ] **DE-4 [R]** `.venv/bin/python -m tools.verify budget report --run <run_id>` 가 1,000행 환산 토큰·벽시계·고가 호출 비율과 **5시간 한도 사용률 변화(%p)** 를 내고 종료 코드 0으로 끝난다(**v3: 예산 상한 없음, 보고 전용**).
- [ ] **DE-5 [R]** `.venv/bin/python -m pytest tests/verify/test_gaming.py -q` — `fixtures/gaming_records.jsonl` 이 게이트를 통과하면 실패하고, 어느 검사가 우회됐는지 메시지에 나온다.
- [ ] **REPORT-1 [S]** `verify report --paper workload__year-in-llm-serving --query gold-kv-reuse --out reports/verify-report-workload__year-in-llm-serving.md` 가 네 판정 절을 모두 채워 생성되고(하나라도 `not-run`이면 파일을 쓰지 않고 종료 코드 1), 머리에 **L1 변형별 일치 등급 분포**를 대표 수치로 싣는다.
- [ ] **SKILL-1 [R]** `~/.claude/skills/claim-judge/SKILL.md` 와 `~/.claude/skills/verify-run/SKILL.md` 가 존재하고, 전자에 순서 교대·Unknown 허용·스팬 필수·PDF 재열람 금지·manifest 불변이, 후자에 파이프라인 호출 순서가 적혀 있다.
- [ ] **TEST-1 [R]** `.venv/bin/python -m pytest tests/verify -q` 전부 통과하고 `.venv/bin/coverage run -m pytest tests/verify -q && .venv/bin/coverage report --include='tools/verify/*' --fail-under=80` 이 종료 코드 0이다.

합계 **40개** — RUNNABLE 33, SCENARIO 7 (V2-1, B-2, B-4, C-2, DE-2, DE-3, REPORT-1).

## ADR

**Decision.** 검증 시스템 v1을 `tools/verify/` Python 패키지 + SQLite 주장 원장으로 짓되, **P1(계약·원장·쿼리·변환기·임계 등록) → P2(L1) → P3(tier1 1회 왕복 + 보고서 뼈대) 얇은 수직 슬라이스를 먼저 관통하고 그 측정값 위에서 L2·L6·재현율·인수 시험의 범위를 확정한다.** 행 단위는 1 인용 = 1 행이고, 판정 2는 `record × query`의 3분류다.

**Drivers.** (1) 감사 가능성·재현성, (2) v1 데이터에서 실제로 움직이는 수치를 먼저 얻기, (3) 환경 제약(`.venv`에 duckdb·pyarrow·jinja2·markdown·tabulate는 있고 torch·numpy·coverage는 없다).

**Alternatives considered.**
- *JSONL + 스크립트* — 일곱 층 조인·무결성 제약 부재로 무효화. 리뷰 가능성은 「원장은 git 밖 재생성물, 보고서를 커밋」으로 흡수.
- *duckdb-over-JSONL* — **이미 설치되어 있고 집계·diff 면에서 SQLite보다 낫다.** 무효화 사유는 단 하나: **trigger가 없어 `gold` 직접 UPDATE 거부를 DB가 강제하지 못한다.** 그러면 B-4의 「G 수정 이력이 남는다」가 코드 규율로 내려간다. 그 외에는 열등하지 않다.
- *MiniCheck급 로컬 NLI / 소형 API* — 51행(44+7) 규모에 torch 2.5 GB는 이득이 없고, API는 키가 없으며 네트워크 의존 테스트가 TDD를 깬다. 인터페이스 스텁으로 남기고 40편 확장 시 재개.
- *CLI가 API 직접 호출* — 비결정적·비감사적이라 Driver 1·3을 동시에 깸.
- *7단계 선구축(iteration 1의 순서)* — `l2_schema.py`·`inject.py`·`agree.py`를 다 쓴 뒤에야 「5조건 필드는 두 벌 모두 부재」를 알게 된다. 슬라이스 우선으로 교체.
- *κ 게이트(κ_min 0.7, q ≤ 0.05)* — **G에 합치 라벨이 한 개도 없다.** 라벨을 G에서 파생하는 것은 없는 것을 지어내는 일(Principle 2 위반)이고, n=33에서는 진짜 κ≈0.85인 심판도 48% 확률로 떨어진다. 사람 라벨을 P3가 태운 행 집합(20~51행, 약 30분)에 새로 받되 **보고 전용**으로 낮춘다.
- *탐침 P·목표 집합 T* — 두 레코드 벌이 동결되어 있어 정의상 공허하다(오늘 심는 탐침은 recall 코드를 시험하고, T는 사후 표집이다). `not-applicable`로 정직하게 보고.

**Why chosen (받아들인 절충).** (1) SQLite의 diff 불가를 받아들이고 trigger를 얻는다. (2) **v1에는 사실상 캐스케이드가 없다** — tier0 승격률은 100%에 가깝고 `expensive_ratio`는 tier2를 부르기 전까지 0이다. 이것을 임계 통과로 포장하지 않고 관측값으로만 적는 대가로, 1,900행 확장 시점의 라우터 자리를 미리 잡는다. (3) 대표 수치를 L2 격리율(상수 100%)에서 **L1 변형별 일치 등급 분포**로 옮긴다 — 후자만이 코드를 쓰기 전에 값을 모르는 수치다. (4) 사람 시간 30분을 새로 쓴다. **계약 제약 「사람 시간은 최소로」(spec:48)를 소비하는 것은 B-2(라벨 30분)와 B-3(예외 논문 변환) 둘뿐이며**, 라벨 없이 κ를 지어내는 것보다는 낫다는 판단이다.

**Consequences.**
- *테스트* — `tests/verify/` 약 20개 파일, 커버리지 80% 게이트. RUNNABLE 33건은 CI에 들어가고 SCENARIO 7건은 에이전트 왕복을 문서화한 절차로 남는다.
- *운영* — `config/thresholds.yaml`은 **P1 말미 등록**, 이후 읽기 전용. 원장은 `results/` (`.gitignore`). `l1_pass_grades`·`elusion_n`(실측 풀, 참고값 35–38, 이하에서 역산)·`leakage_n`·`escalation_max`가 등록 항목에 포함된다.
- *문서* — 보고서 `reports/verify-report-<slug>.md`, 출처 묶음 `results/verify-bundle-<run_id>.json`, 슬라이스 사실 `results/slice-facts-<run_id>.json`. `docs/decisions.md`에 NLI 백엔드·행 단위·κ 보고 전용 세 줄.
- *예상 결과의 정직한 선언* — L2 격리율 100%, `derived_from` 적용 행 0, Codex L1 통과 7/7(구성상 보장), 탐침·T `not-applicable`. 이것들은 **입력 진단치이지 시스템의 성능 수치가 아니다.** v1이 내놓는 새 정보는 Claude 44행의 L1 등급 분포와 tier1 판정의 3분류 분포다.
- *커밋* — git 작업은 사용자가 한다. 단계 완료 시 커밋 메시지를 코드 블록으로 전달한다.

**Follow-ups.** 아래 Deferred 전부. 특히 40편 전량 변환 · NLI 백엔드 재결정 · 진짜 캐스케이드 측정은 한 묶음이다.

## Deferred (v2+)

스펙이 `[이후]`로 표기한 것
- C0: 나머지 40편(Claude 804 · Codex 1,164 전량) 변환. *단 B-3 회귀 케이스가 가리키는 슬러그의 Claude 레코드만 v1 예외로 선행 변환한다.*
- V2: 독립 검증 질문(레코드만 보이는 새 컨텍스트에서 조건 되묻기 → 원 조건 필드 대조).
- V3: 심은 오류 비율로 잔여 오류 추정(bebugging, A2). 탐침 P·목표 집합 T는 **새 추출 실행이 생길 때** 되살린다.
- V3: **elusion 5% 상한은 k=1에서 도달 불가다.** 미사용 풀이 약 35–38블록이라 0오류 기준 상한은 약 7.6–8.2%가 한계이고, 5%에는 n≥59가 필요하다. 5% 이하 상한은 정답 논문을 k>1로 넓혀 풀을 키운 뒤에만 가능하다.
- V4: 종합 문장의 조건 포함 관계와 확신 표지 diff (설계 §3.7 드리프트 층).
- A: 합성 코퍼스 픽스처로 파이프라인 끝까지 회귀(A4).
- B: 그림자 모드(B4), 정답 논문 k > 1, 사람 라벨 ≥ 100건에 기반한 **κ pass/fail 게이트**.
- C: CheckList식 능력 × 시험 유형 행렬(C4).
- D·E: 적대적 라운드(D1), 보정 곡선·conformal 상한(E2).
- 운영: 모델 판·프롬프트 변경 시 A·C 묶음 CI 재실행(F1), 오탐 1건의 사람 시간 측정(F3).

이 계획이 의식적으로 빼는 것
- `drift.py`와 `synth_sentences` 테이블 — DDL조차 v1에 넣지 않는다.
- 출시 차단 훅(Stop / PreToolUse에서 `gate.py` 호출) — CLI로만.
- `~/.claude/skills/claim-extract/` — 발췌는 시스템 밖.
- `backends/api_small.py`·`backends/local_nli.py` — 인터페이스 스텁만. **실측 가능한 캐스케이드(승격률·누출률이 0이 아닌 값)는 v2의 일이다.**
- 기존 빌더 assert의 링크 강제 검사 대체.
- 41편 규모 정량 meta-regression, 심판 패널 다수결 (스펙 Non-Goals).
- 독립 대조군 구축(PDF에서 직접 옮겨 적은 문장으로 DE-1의 순환성 해소) — v1은 순환성을 주석으로 밝히는 데 그친다.

---

계획 파일 커밋 메시지(사용자가 실행):

```
A verification plan that measures L1 before it builds the rest, and says not-applicable where the data is empty

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```
