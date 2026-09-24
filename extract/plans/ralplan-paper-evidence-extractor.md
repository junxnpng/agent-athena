# ralplan — 질의 기반 논문 근거 발췌기 (v1) · iteration 4 (Critic APPROVE, 2026-09-23)

> **위치.** 이 계획과 발췌기는 `verify/` 옆 새 디렉토리 `extract/`에 산다. 상대 경로는 저장소 루트(`.` = `AI-helper/` 저장소 루트) 기준이며, 외부 데이터는 `KVCPOOL=kvcpool-trace-gen` 저장소 루트를 가리키는 환경 변수 기준 상대 경로로만 적는다. 실행은 `cd extract && .venv/bin/pytest`와 `cd extract && PYTHONPATH=../verify .venv/bin/python -m extract.cli …`. 스킬 본체는 `extract/skills/paper-extract/`에, 저장소 심볼릭 링크는 `.claude/skills/paper-extract/`가 그곳을 가리키게 만든다. 인터뷰 기록 `state.json`은 옮기지 않았고, 계획을 만든 원 작업 트리의 git 밖 `.athena/deep-interview/paper-evidence-extractor/`에 남아 있다.

> **합의 상태.** planner → architect → critic 4회 반복 끝에 critic APPROVE(2026-09-23). 3회차는 architect가 원문 측정으로 치명 결함(절 제목 인식 4/20)을 확인해 critic 판정 없이 수정으로 넘겼고, 4회차에서 architect·critic 모두 검토했다. 4회차 뒤 architect D5 문구 한 줄(`test_section_fp_bound`가 비교하는 목록의 정의)을 orchestrator가 반영했다.
>
> **검토 기록.** 같은 디렉토리의 `ralplan-paper-evidence-extractor.review-{1,2,3,4}-{architect,critic}.md`(3회차 critic 없음). 이 계획·검토 기록·스펙은 2026-09-23 git 밖 `.athena/`에서 `extract/plans/`·`extract/spec/`으로 옮겼고, 검토 기록은 이전 전 경로(`.athena/...`)를 그대로 담고 있다. 회차별 계획 사본 `.iter-{1,2,3,4}.md`는 옮기지 않고 원 작업 트리의 `.athena/plans/`에 남겼다.
>
> **재개 방법.** 단계마다 새 세션에서 연다. `export KVCPOOL=<kvcpool-trace-gen 저장소 루트>` 뒤 이 파일(`extract/plans/ralplan-paper-evidence-extractor.md`)을 읽고, 완료 표시가 없는 첫 단계부터 한다. P4a의 결정 게이트는 사람이 판단하고 5-bullet 요약을 이 파일에 적는다.

### iteration 4 변경 요약 (검토 응답 대응표)

- **1 · section 감지 규칙 세 개 세트로 교체(측정된 규칙).** 단일 줄 규칙 하나만으로는 정답 논문의 20 heading 중 4개만 잡히는 것이 orchestrator 측정으로 확인됨. iteration 4는 세 규칙 세트로 교체하고, 정답 논문에서 21개 heading을 오탐 0으로 잡는 것을 측정으로 못박음. **line 93 continuation 블록의 section이 `§1`이 되도록** `test_span_line93.py`·C0-8에 `section == "§1"` 단정을 되살리고, `test_section_1_body_is_null` 대신 `test_section_1_body_is_intro`로 그 블록의 section이 `§1`임을 단정. 픽스처 21행을 계획 본문에 그대로 못박음. DR 옵션 (d)에 세 대안(단일 줄 4/20, 단순 pair 17개·오탐 6, 소유하지 않기)을 측정치와 함께 나열. 41편 전체에서 484 heading·65 단조성 위반 있음 — inbox 배치에 대비한 완화는 [이후].
- **2 · `run.json` 키 배치 (P4b vs P5).** P4b의 `report.py`가 26 키 dict를 모두 쓰되, P5가 계산해 채우는 세 키(`checks.per_variant_grades`·`checks.para_id_cross_check`·`checks.g_recall_report_only`)는 P4b에서 빈 dict `{}` 자리표로 두고 P5의 각 모듈이 덮어쓴다. shape 테스트를 둘로 분할: `test_report_shape.py::test_p4b_owned_keys`(P4b에서 23 키 값 채움) · `test_report_shape.py::test_all_keys`(P5에서 26 키, 세 키의 값도 비지 않음 확인). AC→단계 매핑과 X4-2를 갱신.
- **3 · section 규칙 적용 범위 명시.** 공통 정의 절과 P2의 `pagesection.py` 설명 모두에 「블록 안 각 줄에 적용(첫 줄뿐 아니라). 매치된 블록 안에서 마지막으로 매치한 (번호, 제목)이 그 블록의 section이 되고, 이후 블록에 propagate하며, 첫 heading 이전 블록은 null」이라고 명시.

- 스펙: `extract/spec/deep-interview-paper-evidence-extractor.md`
- 하류 시스템 계획: `verify/plans/ralplan-verification-system.md`
- 정답 논문 원본: `$KVCPOOL/papers/workload__year-in-llm-serving.pdf`, 대조 텍스트 `$KVCPOOL/papers/codex_source_text/codex_workload__year-in-llm-serving.txt`, manifest `$KVCPOOL/papers/codex_source_manifest.json`
- 정답 세트 G: `verify/gold/workload__year-in-llm-serving_handpicked.md`
- 브랜치: `paper-extract` (2026-09-23 `origin/main` `fd22c0f`에서 생성)

## RALPLAN-DR

### Principles

1. **인용은 코드가 복사한다.** LLM 출력에는 `{segment_id, kind, memo}`만 있고, `quote`는 `extract_raw`의 부분 문자열(spanning이면 `조각1 […] 조각2`)이다. 존재 통과는 구성상 보장되어야 하며, 실패는 세그먼트 분할·복사 경로의 버그다.
2. **verify는 라이브러리로만 부른다.** verify의 순수 함수(`schema.validate`, `paragraphs.split_blocks`/`resolve`/`primary`, `l1_exists.check_quote`, `normalize.load`, `queries.load`, `thresholds.load`)만 import한다. `thresholds.begin`·`load_variants`·`queries.register` 같은 conn-바인딩 진입점은 부르지 않는다.
3. **첫 실행 전에 통과 기준을 파일로 등록한다.** `extract/config/gates.yaml`을 실행보다 먼저 만들고 실행 보고에 그 파일의 sha256을 남긴다. 또한 `verify/config/thresholds.yaml`의 `paragraph_unit.split`이 `blank_line_block`이 아니면 CLI가 첫 줄에서 죽는다.
4. **얇은 수직 슬라이스가 하드닝의 근거를 만든다.** P4a는 전체 `segments.json`(스펙의 통독 한 번)을 만들고 최소 하류만 둔다. 관측을 `slice-facts-<run_id>.json`·이 계획 파일의 5-bullet 요약·`extract/docs/decisions.md`에 남긴 뒤 P4b가 workfile 6사유·26키 run.json·spanning 마커·SKILL.md 조임을 결정.
5. **테스트 먼저, 코드·주석은 영어, 커밋은 사용자.** 코드·주석·docstring에서 「계획 단계」를 참조하지 않는다.

### Decision Drivers (순위)

1. **verify와의 결합을 계약까지로 좁히기.**
2. **세그먼트 계약의 원문 충실성.** `quote` 전량 exact, `para_id`가 verify 블록 id와 일치. spanning `[…]`이 `verify/tools/verify/paragraphs.py:22`의 `\[[^\]]*\]` 분기에 걸린다.
3. **환경 제약** — Python 3.10 + stdlib + PyYAML, poppler 22.02.0.

### Viable Options

**(a) 패키지 배치와 verify import 경로**

| 안 | 장점 | 단점 |
|---|---|---|
| **A1. 최상위 패키지 `extract`(채택).** `extract/extract/*.py`, `pytest.ini`의 `pythonpath = . ../verify`. pytest 밖 명령은 `PYTHONPATH=../verify`. | verify와 충돌 없음. verify 파일 무수정. Architect 실측 확인. | 스펙 초안 `extract/tools/extract/…` 이름과 어긋남. |
| A2. `extract/tools/extract/*.py`. | 초안 이름과 일치. | verify의 `verify/tools/__init__.py`(실존 · 빈 파일)와 최상위 `tools` 패키지 충돌. |
| A3. `sys.path.insert` per module. | 유연. | 로드 순서 의존, 테스트 격리 파괴. |

**(b) 스킬 왕복 방식**

| 안 | 장점 | 단점 |
|---|---|---|
| **B1. 파일 왕복(채택).** verify `judge export/import` 패턴. | 감사 가능. 6사유가 단위 테스트로. | 3단계 실행. |
| B2. 세션이 records.jsonl 직접. | 왕복 1회. | Principle 1 위반. |
| B3. CLI가 API 호출. | 왕복 없음. | 스펙 v1 제외. |

**(c) 첫 실행 지점 — 얇은 슬라이스 vs 층별 완성**

| 안 | 장점 | 단점 |
|---|---|---|
| **C1. 얇은 슬라이스(채택).** P4a는 전체 segments.json + 최소 하류. | Principle 4 준수. | P4a 뒤 사람 개입. |
| C2. 층별 완성. | 초기 커버리지. | 관측 없는 결정. |
| C3. 스킬을 모형 대체. | 결정적. | 세션 관측 없음. |

**(d) section 감지 규칙 (iteration 4 실측 갱신)**

| 안 | 장점 | 단점 (측정치 포함) |
|---|---|---|
| **D1. 세 규칙 세트(채택).** (i) 줄 규칙 `^([1-9](?:\.[1-9]){0,2})\s+([A-Z][A-Za-z][A-Za-z -]{2,60})$`, (ii) pair 규칙 「블록 전체 텍스트가 `^[1-9](?:\.[1-9]){0,2}$`이고 바로 다음 블록의 첫 줄이 `^[A-Z][A-Za-z][A-Za-z -]{2,40}$`」, (iii) run-in 규칙 `^([1-9](?:\.[1-9]){1,2})\s+([A-Z][A-Za-z][A-Za-z -]{2,60})\.\s`. 셋 모두 「제목의 4자 이상 단어는 대문자로 시작」(Title Case)을 함께 요구. 규칙은 블록 안 각 줄에 적용하고, 마지막 매치가 그 블록 section이 되며 이후 블록에 propagate. | **정답 논문에서 21개 heading을 오탐 0으로 정확히 잡음**(측정치). 41편 전체에서 484 heading·65 비단조 전이 존재 → inbox에 오탐/누락 여지. `10` 이상 절, `2.10` 같은 소절 배제. |
| D2. 단일 줄 규칙만 (iteration 3안). | 규칙이 짧고 오탐 최소. | **정답 논문에서 20 heading 중 4개만 잡음**(측정치): `2 Background`, `2.1 LLM Inference`, `7 Load Balancing`, `7.1 Production Systems`. 다이제스트가 대부분 `§—`. |
| D3. 단순 pair 규칙 추가 (iteration 2안). | recall 상승. | **정답 논문에서 17 hit 중 6 오탐**(측정치): `1.0 Global`×3, `4 Requests per user`, `8 Output tokens`, `5 Instance cache size`, `1.8 Replication ratio`. `§0.8`/`§103` 같은 값이 본문에 전파. |
| D4. section을 아예 소유하지 않기 (모두 null). | 코드 작음. | 사용자가 다이제스트에서 매 줄 `§—`을 봐야 함. 스펙은 null을 허용하지만 UX 비용이 큼. |

**무효화 근거.** D2·D3는 측정 기반으로 recall 부족(D2) 또는 오탐 다수(D3). D4는 UX 비용. D1은 세 규칙 + Title Case + 「번호에 0 성분 없음」의 결합으로 오탐을 0으로 밀어냈고, 41편에서의 잔여 오탐/누락은 [이후]로 넘겨 관리한다.

---

## 계획 본문 (v1)

공통 규칙: **테스트 먼저**(RED→GREEN→REFACTOR). 코드·주석·docstring은 영어. 코드·주석에 「Phase」·「Step」·「§」 단계 표기를 적지 않는다. `git add/commit/push`는 사용자가 한다. 실행은 항상 `extract/.venv/bin/python`. **pytest 밖 명령은 `PYTHONPATH=../verify`를 정면에 붙인다.** 각 단계에 `- [ ] 완료` 표시. 새 세션은 이 파일만 읽고 재개.

선행 1회: `cd extract && python3 -m venv .venv && .venv/bin/pip install pytest PyYAML coverage`.

### 세그먼트·행 단위 정의 (전 단계 공통)

- **1 선택 = 1 세그먼트 = 1 레코드.** `segment_id = <para_id>.s<n>`, `record_id = <segment_id>@<sha8>`(sha8 = `selections.jsonl` sha256 앞 8자, 매 실행 다름 — ADR에 의도임 명시), `run_id = <query_id>-<date>-<sha8>-<slug>`, `extractor_id = claude-code-skill:<model>`.
- **PDF → 텍스트 층.** `extract_raw`는 매 실행 `pdftotext <pdf> -`(기본 모드) 결과. UTF-8·`errors="replace"`. 실행 보고에 PDF sha256, 텍스트 sha256, poppler 버전, `codex_raw` 일치 여부(같으면 diff 관련 필드는 null, 다르면 diff 줄 수와 첫 차이 위치).
- **블록.** `verify/tools/verify/paragraphs.py:76`의 `split_blocks(text, "extract_raw")`. `para_id = f"extract_raw#{seq:04d}"`. `codex_raw`가 같은 텍스트일 때 verify 블록 id와 번호 동일.
- **spanning segment.** 앞 블록의 「끝 조각 후보」(마침표·물음표·느낌표·닫는 큰따옴표로 끝나지 않음)를 **다음 「본문 블록」(20낱말 이상, section 값 무관)**의 첫 조각과 잇는다. 사이의 header·표·캡션은 흡수하지 않는다. `text = "조각1 […] 조각2"`, `resolved_para_ids = [para_id_first, para_id_last]`.
- **section 감지 규칙 (세 규칙 세트, iteration 4 확정).** 세 규칙은 모두 **블록 안의 각 줄에 대해** 적용한다(첫 줄뿐 아니라). 어떤 블록에서 어느 규칙이든 매치하면 그 블록의 section은 **마지막으로 매치한 (번호, 제목)** 을 `§<번호>` 형태로 만든 값이며, 그 값을 이후 블록에 propagate한다. 첫 매치 이전의 블록은 null. 세 규칙 모두 제목 텍스트에 「길이 ≥ 4인 단어는 모두 대문자로 시작」(Title Case) 조건을 추가로 검사한다.
  - **(i) 줄 규칙.** `^([1-9](?:\.[1-9]){0,2})\s+([A-Z][A-Za-z][A-Za-z -]{2,60})$`.
  - **(ii) pair 규칙.** 블록의 stripped 전체 텍스트가 `^[1-9](?:\.[1-9]){0,2}$`에 fullmatch하고, 바로 다음 블록의 첫 줄이 `^[A-Z][A-Za-z][A-Za-z -]{2,40}$`에 fullmatch할 때 그 두 블록의 section은 `§<번호>`.
  - **(iii) run-in 규칙.** `^([1-9](?:\.[1-9]){1,2})\s+([A-Z][A-Za-z][A-Za-z -]{2,60})\.\s`.
  - 숫자에는 `0` 성분이 나올 수 없으므로 `1.0 Global` 같은 표 캡션은 제외되고, 「제목은 숫자·괄호 없음」이 tick 라벨(`20 Hour of Day (UTC)`, `0.8 CDF`)을 제외한다.
  - **측정 결과(정답 논문, orchestrator).** 세 규칙 세트가 **정확히 21개 heading, 오탐 0**을 잡음. 목록(선언 순, 문서 순서와 같음): `1 Introduction | 2 Background | 2.1 LLM Inference | 2.2 LLM Workload | 3.3 Token Shape | 4.1 Heterogeneity | 5 Burstiness | 6.1 Production System | 6.2 Arrival Locality | 6.3 GDSF | 6.3.1 Session Reconstruction | 6.3.2 Cache Simulation | 6.3.3 Results | 7 Load Balancing | 7.1 Production Systems | 7.1.1 General Overview | 7.1.2 Routing-Induced Cache Duplication | 7.2 Load Balancing Simulation | 7.2.1 Simulator and Routing Policies | 7.2.2 Simulation Results | 9 Conclusion`. 누락(`3`, `3.1`, `3.2`, `4`, `5.1`, `6`, `8`)은 받아들이고 해당 블록은 직전 heading을 이어받는다. **line 93 continuation 블록(seq 35, `highly skewed popularity`로 시작)은 `1 Introduction`(seq 18) 이후이므로 section = `§1`**.

### `run.json` 키 목록 (정본)

이 리스트가 `extract/extract/report.py`의 상수이자 `tests/test_report_shape.py`의 iterator다. **총 26 키.** P4b의 `report.py`는 26 키를 모두 dict에 씀. 그 중 세 키(`checks.per_variant_grades`·`checks.para_id_cross_check`·`checks.g_recall_report_only`)는 P4b에서 빈 dict `{}` 자리표만 두고 P5의 각 모듈이 실제 값으로 덮어쓴다. 나머지 23 키는 P4b에서 값을 채운다.

```python
RUN_JSON_KEY_PATHS = [
    # sources (7) — P4b fills. spec X4 "원천".
    "sources.pdf_sha256",
    "sources.extract_raw_sha256",
    "sources.poppler_version",
    "sources.codex_raw_equal",
    "sources.codex_raw_diff_lines",       # null when equal
    "sources.codex_raw_first_diff",       # first differing byte offset; null when equal
    "sources.segmenter_ver",
    # segments (7) — P4b fills. spec X4 "세그먼트 수" and body_words/estimated_tokens.
    "segments.blocks",
    "segments.total",
    "segments.removed_by_reason",         # {references, running_header, arxiv_stamp}
    "segments.displayed",                 # total - sum(removed)
    "segments.spanning",                  # {candidates, emitted}
    "segments.body_words",
    "segments.estimated_tokens",          # body_words * 1.3
    # selections (6) — P4b fills. spec X4 "선택 결과".
    "selections.count",
    "selections.kind_dist",               # {measurement, author_interpretation, extrapolation}
    "selections.boundary_flags",          # list of {segment_id, reason}
    "selections.spanning_selected",       # spanning segments the LLM chose
    "selections.short_block_count",       # selections from <20-word blocks
    "selections.section_null_count",
    # checks — 2 filled by P4b, 3 placeholders {} in P4b filled by P5.
    "checks.schema",                      # {pass, quarantine} — P4b
    "checks.l1_extract_raw",              # {exact, strict, loose, gapped, miss} — P4b
    "checks.per_variant_grades",          # {} in P4b, filled by P5 variants.py
    "checks.para_id_cross_check",         # {} in P4b, filled by P5 para_check.py
    "checks.g_recall_report_only",        # {} in P4b, filled by P5 g_recall.py
    # provenance (1) — P4b fills.
    "gates_sha256",
]
```

**P4b가 값 채우는 23 키(P4b 소유):** 위 목록에서 `checks.per_variant_grades`·`checks.para_id_cross_check`·`checks.g_recall_report_only`를 제외한 나머지 전부.

**P5가 값 채우는 3 키:** 위 세 개.

---

### P1 — 패키지 스켈레톤 + verify 라이브러리 wrapper + 런타임 게이트

**목표.** `extract` 패키지가 실존. `paragraph_unit.split` 런타임 게이트가 걸림. 첫 테스트가 돈다.

**선행 상태.** 없음.

**필요 파일.**
- `extract/pytest.ini` — `[pytest]\npythonpath = . ../verify\ntestpaths = tests`.
- `extract/extract/__init__.py`.
- `extract/extract/paths.py` — `EXTRACT_ROOT = pathlib.Path(__file__).resolve().parents[1]`, `CONFIG_DIR`, `RESULTS_DIR`, `SOURCE_ENV = "KVCPOOL"`, `source_root()`.
- `extract/extract/query.py` — `load(path)`가 `tools.verify.queries.load(path)`를 부르고 `queries.QueryError`를 `sys.exit(1)`로 변환. `confirmed_by`가 없으면 `unconfirmed=True`만 반환.
- `extract/extract/gates.py`:
  - `load_gates(path)`가 등록 항목 일곱 개(`schema_valid`, `l1_variant`, `l1_grades`, `l1_pass_rate`, `kind_memo_rate`, `g_recall`, `codex_raw_grades`) 존재 확인.
  - `sha256_of(path)`.
  - `assert_paragraph_unit_split()`가 `os.environ.get("EXTRACT_THRESHOLDS_PATH")`를 읽고, 있으면 그 경로를, 없으면 verify의 `tools.verify.thresholds.DEFAULT_PATH`를 `tools.verify.thresholds.load(path=…)`에 넘긴다. `data["paragraph_unit"]["split"] != "blank_line_block"`이면 `RuntimeError`. **CLI가 첫 줄에서 부른다.**
- `extract/config/gates.yaml` — 스펙 X4 그대로.
- `extract/config/queries/gold-kv-reuse.yaml` — 개발·테스트 픽스처.

**먼저 쓰는 테스트.**
- `tests/test_gates.py::test_required_keys` — 일곱 키 존재.
- `tests/test_gates.py::test_split_gate_rejects_bad_value` — 임시 thresholds가 `paragraph_unit.split: something-else`면 `RuntimeError`.
- `tests/test_gates.py::test_split_gate_passes_blank_line_block` — 정상값 통과.
- `tests/test_gates.py::test_thresholds_env_var_override` — `EXTRACT_THRESHOLDS_PATH` monkeypatch로 override 확인.
- `tests/test_query_loader.py::test_missing_required_exit_1` — 필수 필드 하나 빠진 파일 → `SystemExit(1)`.
- `tests/test_query_loader.py::test_unconfirmed_ok` — `confirmed_by` 비면 `unconfirmed=True`, 종료 0.
- `tests/test_query_loader.py::test_query_error_maps_to_exit1` — verify의 `QueryError`가 `sys.exit(1)`.
- `tests/test_paths.py` — `KVCPOOL` 미설정 시 `SourceRootError`.
- `tests/test_verify_import.py` — `from tools.verify import paragraphs, l1_exists, normalize, schema, queries, thresholds` 임포트.

**닫는 스펙 조항.** C0 「질의 파일 로드」, C0 「`paragraph_unit.split` 런타임 게이트」, X4 「gates.yaml 등록 항목 7개」.

**Exit check.** `cd extract && .venv/bin/pytest -q` 종료 0.

**- [ ] 완료**

---

### P2 — 텍스트 층 + 블록 대조 + 세그먼트 분할

**목표.** PDF → `extract_raw`, 블록화, 문장 세그먼트, page/section 부여, 참고문헌·running header·arXiv 스탬프 세그먼트 단위 제거.

**선행 상태.** P1 완료.

**필요 파일.**
- `extract/extract/textlayer.py` — `extract_raw(pdf_path) -> (text, meta)`가 `pdftotext -q <pdf> -`(기본 모드) subprocess. meta에 PDF sha256, 텍스트 sha256, poppler 버전. `codex_raw`가 주어지면 `equal`(bool)·`diff_lines`(int|null)·`first_diff`(첫 다른 바이트 오프셋, null when equal)를 함께 반환.
- `extract/extract/segmenter.py` — `Segment(segment_id, text, page, section, para_id, char_start, char_end, resolved_para_ids)`. `split_block_to_segments(block, cfg)`는 블록 안에서만 문장을 자름.
- `extract/extract/removal.py` — 세그먼트 통째 제거. 사유 `references`, `running_header`, `arxiv_stamp`. 첫 줄이 `re.match(r"^\s*References\s*$", line, flags=re.IGNORECASE)`인 블록부터 문서 끝까지 참고문헌.
- `extract/extract/pagesection.py` — page = 1 + (블록 시작 앞 `\f` 개수). **section 감지는 세 규칙 세트: (i) 줄 규칙 `^([1-9](?:\.[1-9]){0,2})\s+([A-Z][A-Za-z][A-Za-z -]{2,60})$`, (ii) pair 규칙 「블록 전체 텍스트가 `^[1-9](?:\.[1-9]){0,2}$` + 다음 블록 첫 줄 `^[A-Z][A-Za-z][A-Za-z -]{2,40}$`」, (iii) run-in 규칙 `^([1-9](?:\.[1-9]){1,2})\s+([A-Z][A-Za-z][A-Za-z -]{2,60})\.\s`. 셋 모두 제목의 4자 이상 단어에 대해 Title Case를 요구. 규칙은 블록 안의 각 줄에 적용하고, 매치가 있으면 그 블록의 마지막 매치가 그 블록의 section이 되며 이후 블록에 propagate. 첫 매치 이전 블록은 null.**
- `extract/config/segmenter.yaml` — `segmenter_ver: v1`, 약어 목록 `["e.g.", "i.e.", "et al.", "Fig.", "Eq.", "Sec.", "vs.", "cf.", "resp.", "Refs.", "No."]`, 소수점 규칙, `\d\^\d` 지수 규칙.
- `tests/fixtures/gold_section_headings.txt` — **본 계획이 내용을 못박음**. 정확히 아래 21행(문서 순서):
  ```
  1 Introduction
  2 Background
  2.1 LLM Inference
  2.2 LLM Workload
  3.3 Token Shape
  4.1 Heterogeneity
  5 Burstiness
  6.1 Production System
  6.2 Arrival Locality
  6.3 GDSF
  6.3.1 Session Reconstruction
  6.3.2 Cache Simulation
  6.3.3 Results
  7 Load Balancing
  7.1 Production Systems
  7.1.1 General Overview
  7.1.2 Routing-Induced Cache Duplication
  7.2 Load Balancing Simulation
  7.2.1 Simulator and Routing Policies
  7.2.2 Simulation Results
  9 Conclusion
  ```
  이 픽스처는 orchestrator 측정에서 저자로 확정한 값이다. poppler 버전 드리프트나 다른 논문에서 drift가 관측되면 새 측정에서 저자로 다시 확정해야 한다. **실행자가 규칙 출력을 픽스처에 붙여 넣는 자동 절차는 금지**(테스트 순환성 회피).

**먼저 쓰는 테스트.**
- `tests/test_textlayer.py` — 정답 논문 PDF sha256 = manifest 값 `4156391d98baafc6201319cc01015fa4bebdfef9740ade64110565fcb041a144`. `extract_raw`가 `codex_raw`와 바이트 일치. poppler 버전 문자열이 빈 문자열 아님. `first_diff`가 `equal == True`이면 null.
- `tests/test_blocks_align_with_codex_raw.py` — 두 텍스트 같으면 `split_blocks` 결과가 verify 블록과 전부 일치. 다르면 skip + diff 줄 수 로그.
- `tests/test_pagesection.py::test_pages_in_range` — 세그먼트 전부 1..16, `\f`=16.
- `tests/test_pagesection.py::test_section_fp_bound` — 세 규칙 세트가 정답 논문에서 매치한 heading 목록이 `tests/fixtures/gold_section_headings.txt`의 21행과 **완전히 순서까지 동일**(리스트 동치, 오탐 0). 비교하는 목록은 세 규칙이 문서 순서로 낸 **모든** (번호, 제목) 매치다(블록당 여러 매치 허용, 중복 제거 없음). 각 블록에 실제로 붙는 section 값(블록의 마지막 매치)과는 별개 회계다. 정답 논문에서 seq 37은 `2 Background`와 `2.1 LLM Inference` 두 매치를 모두 목록에 내고 자신은 `§2.1`을 받으며, seq 567도 같은 방식으로 `7 Load Balancing`·`7.1 Production Systems`를 내고 `§7.1`을 받는다. 그래서 블록에 붙는 서로 다른 section 값은 19개다.
- `tests/test_pagesection.py::test_section_1_body_is_intro` — 정답 논문 line 93 continuation 블록(seq 35, 텍스트가 `highly skewed popularity`로 시작)의 `section == "§1"`.
- `tests/test_segmenter_abbreviations.py` — 「e.g.」·「i.e.」·「et al.」·「Fig. 1」·「Eq. 3」·「Sec. 4.2」·「vs.」·「0.75」·「10^2」를 자르지 않음.
- `tests/test_removal.py` — 사유별 표지 + `References`가 대소문자 무시로 감지. 표 안 세그먼트 남음. 남은 + 제거 = 전체.
- `tests/test_block_text_roundtrip.py` — 정답 논문 모든 블록에서 세그먼트를 이으면 블록 텍스트 바이트 일치.

**닫는 스펙 조항.** C0 「PDF sha256·poppler 버전·segmenter_ver」, C0 「블록 대응」, C0 「블록 텍스트 복원」, C0 「segmenter.yaml 약어」, C0 「page/section, null 허용」, C0 「제거 수 닫힘 + References 구조 감지」, C0 「sha256 일치 여부·첫 차이 위치」.

**Exit check.** `cd extract && .venv/bin/pytest tests/test_textlayer.py tests/test_blocks_align_with_codex_raw.py tests/test_pagesection.py tests/test_segmenter_abbreviations.py tests/test_removal.py tests/test_block_text_roundtrip.py -q`. 정답 논문에서 「skip 0」.

**- [ ] 완료**

---

### P3 — spanning segment + verify L1 라이브러리 대조

**목표.** 쪽 넘김·그림·표가 문장을 끊은 자리에서 두 조각을 `[…]`로 잇고, `l1_exists.check_quote`를 라이브러리로 호출.

**선행 상태.** P2 완료.

**필요 파일.**
- `extract/extract/spanning.py` — 앞 블록의 「끝 조각 후보」와 다음 「본문 블록」(20낱말 이상)의 첫 조각을 잇는다. 사이 header·표·캡션 흡수 없음.
- `extract/extract/existence.py` — `verify.tools.verify.l1_exists.check_quote(quote, [Variant("extract_raw", text)])`만 부른다. `check_against_codex(quote, codex_raw)`도 같은 방식(보고 전용).

**먼저 쓰는 테스트.**
- `tests/test_span_line93.py::test_line93_spanning_exact` — 정답 논문 line 93 세그먼트가 line 167 조각과 spanning으로 묶이고, `check_quote(quote, [Variant("extract_raw", extract_raw_text)])`가 `grade == "exact"`. **그 세그먼트의 `section == "§1"`**(D1 세 규칙 세트가 `1 Introduction`을 잡음).
- `tests/test_span_ordering.py` — 끼어든 header·Table 1 세그먼트가 spanning 안으로 흡수되지 않고 그대로 남는다.
- `tests/test_existence_library.py::test_extract_raw_exact` — 정답 논문 임의 세그먼트가 `extract_raw`에서 exact.
- `tests/test_existence_library.py::test_interior_mutation_not_exact` — 세그먼트 안 한 글자 mutation에 대해 `grade != "exact"`. 주석: `verify/config/normalization.yaml:52-54`의 `min_run=20 / max_runs=3 / max_gap_chars=1000`이면 긴 세그먼트 가운데의 한 글자 변경은 `gapped`로도 통과 가능.
- `tests/test_no_ledger.py` — `extract.*` 임포트 그래프에 `tools.verify.ledger`, `tools.verify.thresholds.begin`, `tools.verify.l1_exists.load_variants`, `tools.verify.queries.register`가 없음을 `ast.parse`로 확인. `thresholds.load`는 허용.

**닫는 스펙 조항.** C0 「쪽 넘김 합치기 + line 93 고정 테스트」, X2 「L1 exact against extract_raw」.

**Exit check.** `cd extract && .venv/bin/pytest tests/test_span_line93.py tests/test_span_ordering.py tests/test_existence_library.py tests/test_no_ledger.py -q` 종료 0.

**- [ ] 완료**

---

### P4a — 얇은 수직 슬라이스 (walking skeleton) + 결정 게이트

**목표.** 관측이 목적. **전체 `segments.json`(모든 표시 세그먼트, 스펙의 통독 한 번)** 을 만들고 세션이 실제 selections를 쓰게 한 뒤, 최소 하류 체인(records_min → digest_min → 작은 run.json)만 지난다. workfile 6사유 검사 없음, 다이제스트 spanning 마커 없음.

**선행 상태.** P1·P2·P3 완료. `KVCPOOL` export.

**필요 파일 (최소).**
- `extract/extract/workfile_min.py` — `export_segments(query, segments, out_dir) -> (path, sha256)`이 **모든 표시 세그먼트**를 담은 JSON을 쓰고 sha256을 `<slug>.segments.sha256`에 쓴다. `import_selections_min`은 필수 필드 존재만 확인. 첫 줄 위반이면 종료 1(6사유 세분화 없음).
- `extract/extract/records_min.py` — 스키마 필수 키와 `conditions.*` 다섯 개 전부 `"unextracted"`, `numbers=[]`, `resolved_para_ids`.
- `extract/extract/digest_min.py` — 문서 순서 세 줄 항목(spanning 마커는 나중). null section은 `§—`.
- `extract/extract/report_min.py` — 작은 run.json 부분집합: `sources.pdf_sha256`, `sources.extract_raw_sha256`, `sources.poppler_version`, `sources.codex_raw_equal`, `segments.total`, `segments.displayed`, `selections.count`, `checks.l1_extract_raw`.
- `extract/extract/cli.py` — `segment`·`build` 서브커맨드. **첫 줄에서 `gates.assert_paragraph_unit_split()` 호출.** `build`는 `--gold <path>` 옵션을 받고 default는 `../verify/gold/workload__year-in-llm-serving_handpicked.md`.
- `extract/skills/paper-extract/SKILL.md` — front matter `name: paper-extract`, `protocol_ver: paper-extract-v1`. 네 규칙 문장 단위 명시: 「Select for relevance in any direction」·「Do not open the PDF or any other source」·「Never write the sentence text; only ids」·「Kind values follow verify's kind_map labels」.
- `.claude/skills/paper-extract` → `extract/skills/paper-extract` 심볼릭 링크.
- `extract/results/<query_id>/slice-facts-<run_id>.json` · `extract/docs/decisions.md`.

**먼저 쓰는 테스트.**
- `tests/test_symlink.py` · `tests/test_cli_split_gate.py` · `tests/test_records_min.py` · `tests/test_digest_min.py` · `tests/test_report_min.py` · `tests/test_skill_rules.py::test_four_rules_present` · `tests/test_workfile_min.py::test_missing_required_field_exits_1`.

**슬라이스 실행 순서 (사람).**
1. `cd extract && PYTHONPATH=../verify .venv/bin/python -m extract.cli segment --query config/queries/gold-kv-reuse.yaml --slug workload__year-in-llm-serving`.
2. 세션 Claude가 `paper-extract` 스킬을 따라 `<slug>.selections.jsonl` 작성.
3. `cd extract && PYTHONPATH=../verify .venv/bin/python -m extract.cli build --query config/queries/gold-kv-reuse.yaml --slug workload__year-in-llm-serving --selections results/gold-kv-reuse/workload__year-in-llm-serving.selections.jsonl --model <session model name>`.

**결정 게이트에 낼 다섯 값** → `slice-facts-<run_id>.json`으로 저장 + **이 계획 파일 P4a `- [ ] 결정 게이트` 아래에 5-bullet 요약 이어붙임** + `docs/decisions.md`에 해석:
1. 세그먼트 수(블록·전체·사유별 제거·displayed)·spanning 후보·성사.
2. LLM 선택 수 N, kind 분포, 20낱말 미만 블록 선택, spanning 선택, `boundary_flag` 여부.
3. `extract_raw` L1 등급 분포. exact N/N이 아니면 실패.
4. `codex_raw`(있으면 `claude_body`·`codex_layout`) 등급.
5. G 블록 회수율.

**닫는 스펙 조항.** C0-8 line 93 · X1 SKILL + 심볼릭 링크 · X1 통독 한 번 · X2 필드 계약 · X2 exact against extract_raw · X4 gates 등록 · C0 런타임 게이트.

**Exit check.** 위 7개 테스트 pass + 슬라이스 세 명령 성공 + `slice-facts-<run_id>.json`·`extract/docs/decisions.md` 존재 + 이 계획 파일 P4a 아래에 5-bullet 요약이 추가됨.

**- [ ] 구현·측정 완료** / **- [ ] 결정 게이트 (사람 · 5-bullet 요약을 이 파일에 이어 적기)**

*여기 아래에 P4a 완료 시 5-bullet 요약을 적는다:*
- (1) …
- (2) …
- (3) …
- (4) …
- (5) …

---

### P4b — 6사유 파일 거부 · 26키 run.json(23키 값 + 3키 자리표) · spanning 마커 · SKILL.md 조임

**목표.** P4a 관측 위에서 workfile 6사유·26키 run.json·다이제스트 spanning 마커·SKILL.md 규칙 조임.

**선행 상태.** P4a 완료. 첫 테스트가 `slice-facts-<run_id>.json`·`extract/docs/decisions.md`·이 파일 P4a 아래 5-bullet 요약 존재를 확인.

**필요 파일 (확장).**
- `extract/extract/workfile.py` — 파일 전체 거부 6사유. memo는 `not memo.strip()` or `"\n" in memo`이면 `empty_memo`.
- `extract/extract/records.py` — `record_id = <segment_id>@<sha8>` 규약.
- `extract/extract/digest.py` — spanning 항목의 인용 줄에서 `[…]` → `⏎p.N`. 왕복: `re.sub(r"\s+", " ", s).strip()`.
- `extract/extract/report.py` — **26 키 dict를 모두 씀**. `checks.per_variant_grades`·`checks.para_id_cross_check`·`checks.g_recall_report_only`는 **P4b에서 빈 dict `{}` 자리표**로 두고 P5의 각 모듈(`variants.py`·`para_check.py`·`g_recall.py`)이 실제 값으로 덮어쓴다. 나머지 23 키는 P4b에서 값을 채운다. `RUN_JSON_KEY_PATHS` 상수를 export.

**먼저 쓰는 테스트.**
- `tests/test_p4b_precondition.py` — slice-facts·decisions.md 존재.
- `tests/test_workfile_reject.py::test_unknown_id`·`::test_removed_id`·`::test_duplicate_id`·`::test_invalid_kind`·`::test_empty_or_newline_memo`·`::test_unexpected_field` (여섯).
- `tests/test_records_shape.py` — 필드 계약(스키마 필수, `conditions.*` 다섯 = `"unextracted"`, `numbers == []`, `locator` 세 키, `kind` 세 값, `extractor_id` 패턴, `run_id` 패턴, `record_id` 패턴, spanning일 때 `resolved_para_ids` 길이 ≥ 2).
- `tests/test_records_counts.py` — 선택 N줄 = 레코드 N개, quarantine 0.
- `tests/test_digest_render.py::test_header_fields` — 머리 아홉 항목.
- `tests/test_digest_render.py::test_order` — page → 블록 seq → 문장 번호, 항목 N개 = 레코드 N개.
- `tests/test_digest_render.py::test_three_lines` — 세 줄 형식, null section은 `§—`.
- `tests/test_digest_render.py::test_span_marker_roundtrip` — `⏎p.N` → `[…]` → `re.sub(r"\s+", " ", s).strip()` = `quote`.
- `tests/test_report_shape.py::test_p4b_owned_keys` — 26 키 dict가 존재하고, **P4b 소유 23 키의 값이 빈 dict가 아니다** (예: `checks.schema`·`checks.l1_extract_raw`·`sources.*`·`segments.*`·`selections.*`·`gates_sha256` 전부 비지 않음). 나머지 3 키(`checks.per_variant_grades`·`checks.para_id_cross_check`·`checks.g_recall_report_only`)는 이 단계에서 `{}` 자리표.
- `tests/test_report_shape.py::test_gates_sha256` — `gates_sha256`이 실행 파일 sha256과 일치.
- `tests/test_report_shape.py::test_total_key_count` — `len(RUN_JSON_KEY_PATHS) == 26`이고 dict에 26 키가 모두 존재.
- `tests/test_skill_rules.py::test_hardened` — 네 규칙 문장은 여전히 있고, P4a 관측에 따라 추가된 문장이 있으면 그것도 문장 단위로 검색.

**닫는 스펙 조항.** X1 「파일 왕복 6사유」·X1 memo 한 줄·X2 「N=N, quarantine 0」·X2 「필드 계약」·X2 「schema pass=N quarantine=0」·X2 「`unextracted`×5, none 0」·X2 「kind+memo N/N」·X3 「세 줄 항목」·X3 「header 아홉 항목」·X3 「문서 순서」·X3 「spanning 마커 왕복」·X4 「26키 run.json」(P4b 소유 23키 값 채움)·X4 「gates_sha256」·C0 「codex_raw diff·first_diff」·X1 「본문 낱말·추정 토큰」.

**Exit check.** `cd extract && .venv/bin/pytest -q` 종료 0 + `PYTHONPATH=../verify .venv/bin/python -m tools.verify schema --validate results/gold-kv-reuse/workload__year-in-llm-serving.records.jsonl`가 `pass N, quarantine 0`.

**- [ ] 완료**

---

### P5 — 변형 대조 · `para_id` 교차 · G 블록 회수율 · 다이제스트 결정론

**목표.** 변형별 등급, `para_id` 교차 확인, 「단 섞임 의심」 목록, G 블록 회수율(보고 전용), 다이제스트 결정론. `run.json`의 세 P5-소유 키를 실제 값으로 덮어씀.

**선행 상태.** P4b 완료.

**필요 파일 (확장).**
- `extract/extract/variants.py` — `sources.yaml`을 읽어 세 변형에서 quote 등급 계산. **`run.json`의 `checks.per_variant_grades`를 덮어쓴다.** `extract_raw` exact인데 `claude_body` MISS인 행은 「텍스트 층 뒤섞임 의심」 목록.
- `extract/extract/para_check.py` — `paragraphs.resolve`가 비지 않은 경우 `para_id`가 그 집합에 든다. 짧은 세그먼트·반복 문장은 목록으로 분리. **`run.json`의 `checks.para_id_cross_check`를 덮어쓴다.**
- `extract/extract/g_recall.py` — G 파일 경로는 CLI `--gold`(default `../verify/gold/workload__year-in-llm-serving_handpicked.md`)에서 옴. **`run.json`의 `checks.g_recall_report_only`를 덮어쓴다.**

**먼저 쓰는 테스트.**
- `tests/test_p5_precondition.py` — P4a·P4b 산출물 존재.
- `tests/test_variant_report.py` — 세 변형 등급 분포가 `checks.per_variant_grades`에 실림. 없는 변형은 `unavailable`.
- `tests/test_layout_suspect_list.py` — 「텍스트 층 뒤섞임 의심」 목록이 `run.json`에.
- `tests/test_para_id_cross_check.py` — 「set에 든 행에 대해서만」 pass/fail. `checks.para_id_cross_check.ok`가 정합.
- `tests/test_para_id_edges.py` — 짧은/반복 두 목록(`empty_resolve_short`·`repeated_first_hit_mismatch`)이 정합.
- `tests/test_g_recall_report_only.py::test_gates_declare_report_only` — `gates.yaml`의 `g_recall == "report_only"`.
- `tests/test_g_recall_report_only.py::test_cli_exit_code_independent_of_g_recall` — `tests/fixtures/gold_empty.md`·`tests/fixtures/gold_full.md`를 `--gold`로 각각 넘겨 CLI 종료 코드 0.
- `tests/test_report_shape.py::test_all_keys` — 26 키가 모두 존재하고, **세 P5-소유 키의 값이 비지 않음** (`checks.per_variant_grades`·`checks.para_id_cross_check`·`checks.g_recall_report_only` 각각이 비지 않은 dict).
- `tests/test_digest_deterministic.py` — 같은 records.jsonl 두 번 렌더 시 md 바이트 일치.

**닫는 스펙 조항.** X2 「codex_raw 등급 분포」·X2 「para_id 교차 확인」·X2 「변형별 등급 · 층 뒤섞임」·X4 「run.json 완결(26키 · 세 P5 키 값 채움)」·X4 「G 회수율 보고」·X3 「다이제스트 결정론」.

**Exit check.** `cd extract && .venv/bin/pytest -q` 종료 0. `run.json`이 26키 완결.

**- [ ] 완료**

---

### P6 — 커버리지 + 통합 회귀

**목표.** 줄 커버리지 80% 이상. `.claude/skills/paper-extract` 최종 검사. `extract` 임포트 그래프 최종 확인.

**선행 상태.** P5 완료.

**먼저 쓰는 테스트 / 명령.**
- `cd extract && .venv/bin/coverage run -m pytest -q && .venv/bin/coverage report --include='extract/*' --fail-under=80`.
- `tests/test_no_ledger.py` 최종.
- `tests/test_symlink_target.py` — `.claude/skills/paper-extract`의 realpath.

**닫는 스펙 조항.** X4 「테스트 먼저 + 80%」.

**Exit check.** 커버리지 명령 종료 0.

**- [ ] 완료**

---

### 병렬 가능성

- P2의 세 파일(`textlayer.py` / `segmenter.py` + `segmenter.yaml` + `pagesection.py` / `removal.py`)은 서로 독립.
- P4b의 세 폴리시(6사유 workfile · P4b-소유 23 키 채우기 · SKILL.md 조임)는 관측 이후라 독립. 병렬.
- P5의 세 파일(`variants.py`·`para_check.py`·`g_recall.py`)은 P4b records + 자리표에만 의존. 병렬.
- P1과 P2 `textlayer.py` 초안은 동시에 시작 가능.

---

## Acceptance Criteria

표기: `[R]`은 명령 하나로 실행 가능, `[S]`는 세션 파일 왕복 선행 시나리오. **기준 cwd는 `extract/`. pytest 밖 명령은 `PYTHONPATH=../verify`를 정면에 붙인다.**

### C0 · 입력·세그먼트

- [ ] **C0-1 [R]** `PYTHONPATH=../verify .venv/bin/python -c "from extract.query import load; load('config/queries/gold-kv-reuse.yaml')"`가 종료 0. 필수 필드 하나 빠진 파일이면 종료 1. `confirmed_by` 비면 `unconfirmed=True`. verify `QueryError`가 `sys.exit(1)`.
- [ ] **C0-2 [R]** `KVCPOOL=$KVCPOOL PYTHONPATH=../verify .venv/bin/python -m extract.cli segment --query config/queries/gold-kv-reuse.yaml --slug workload__year-in-llm-serving`가 segments.json·sha256을 쓴다. 뒤이은 build에서 `<slug>.run.json`의 `sources.pdf_sha256`(manifest 값)·`sources.extract_raw_sha256`·`sources.poppler_version`·`sources.segmenter_ver`가 채워진다.
- [ ] **C0-3 [R]** `.venv/bin/pytest tests/test_blocks_align_with_codex_raw.py -q` — 정답 논문에서 skip 없이 통과.
- [ ] **C0-4 [R]** `.venv/bin/pytest tests/test_block_text_roundtrip.py -q`.
- [ ] **C0-5 [R]** `.venv/bin/pytest tests/test_segmenter_abbreviations.py -q`.
- [ ] **C0-6 [R]** `.venv/bin/pytest tests/test_pagesection.py -q` — page ∈ 1..16, `\f`=16, `test_section_fp_bound`(세 규칙 세트가 `gold_section_headings.txt`의 21행과 순서까지 일치), `test_section_1_body_is_intro`(seq 35 블록 `section == "§1"`). `run.json.selections.section_null_count`에 반영.
- [ ] **C0-7 [R]** `.venv/bin/pytest tests/test_removal.py -q`.
- [ ] **C0-8 [R]** `.venv/bin/pytest tests/test_span_line93.py::test_line93_spanning_exact -q` — spanning된 quote가 `grade == "exact"`이고 그 세그먼트 `section == "§1"`.
- [ ] **C0-9 [R]** `<slug>.run.json`이 `sources.codex_raw_equal`·`sources.codex_raw_diff_lines`·`sources.codex_raw_first_diff`를 담는다.
- [ ] **C0-10 [R]** `verify/config/thresholds.yaml`의 `paragraph_unit.split == "blank_line_block"`이 아니면 CLI 첫 줄에서 종료 1. `.venv/bin/pytest tests/test_cli_split_gate.py tests/test_gates.py::test_thresholds_env_var_override -q`.

### X1 · 선택·출력

- [ ] **X1-1 [R]** `.venv/bin/pytest tests/test_symlink.py tests/test_symlink_target.py -q`.
- [ ] **X1-2 [R]** `.venv/bin/pytest tests/test_workfile_reject.py -q`.
- [ ] **X1-3 [S]** 슬라이스 세 명령 성공 뒤 `<slug>.run.json`의 `segments.body_words`(정수)·`segments.estimated_tokens = body_words * 1.3`(float)·`segments.total`·`segments.displayed`·`selections.count`·`selections.spanning_selected` 정수.
- [ ] **X1-4 [R]** `.venv/bin/pytest tests/test_workfile_reject.py::test_empty_or_newline_memo -q`.
- [ ] **X1-5 [R]** `.venv/bin/pytest tests/test_skill_rules.py -q`.

### X2 · 레코드·존재 검사

- [ ] **X2-1 [R]** `.venv/bin/pytest tests/test_records_min.py tests/test_records_counts.py -q`.
- [ ] **X2-2 [R]** `PYTHONPATH=../verify .venv/bin/python -c "import json; from tools.verify.schema import validate; recs=[json.loads(l) for l in open('results/gold-kv-reuse/workload__year-in-llm-serving.records.jsonl')]; r=[validate(x).status for x in recs]; print('pass', r.count('pass'), 'quarantine', r.count('quarantine'))"`가 `pass N, quarantine 0`.
- [ ] **X2-3 [R]** `.venv/bin/pytest tests/test_records_shape.py -q`.
- [ ] **X2-4 [R]** `PYTHONPATH=../verify .venv/bin/python -c "import json; recs=[json.loads(l) for l in open('results/gold-kv-reuse/workload__year-in-llm-serving.records.jsonl')]; assert all('none' not in r['conditions'].values() for r in recs) and all(all(v=='unextracted' for v in r['conditions'].values()) for r in recs); print('ok', len(recs))"`가 `ok N`.
- [ ] **X2-5 [R]** `.venv/bin/pytest tests/test_existence_library.py -q`.
- [ ] **X2-6 [R]** `.venv/bin/pytest tests/test_variant_report.py -q` — `run.json.checks.per_variant_grades`에 등급 분포(P5에서 값 채움).
- [ ] **X2-7 [R]** `.venv/bin/pytest tests/test_para_id_cross_check.py tests/test_para_id_edges.py -q` — pass/fail은 「set에 든 행」에 대해서만. 짧은/반복은 두 목록.
- [ ] **X2-8 [R]** `.venv/bin/pytest tests/test_layout_suspect_list.py -q`.
- [ ] **X2-9 [R]** `PYTHONPATH=../verify .venv/bin/python -c "import json; recs=[json.loads(l) for l in open('results/gold-kv-reuse/workload__year-in-llm-serving.records.jsonl')]; assert all(r['kind'] in ('measurement','author_interpretation','extrapolation') and r['claim_text'].strip() for r in recs); print('ok', len(recs))"`가 `ok N`.

### X3 · 다이제스트

- [ ] **X3-1 [R]** `.venv/bin/pytest tests/test_digest_render.py::test_header_fields -q`.
- [ ] **X3-2 [R]** `.venv/bin/pytest tests/test_digest_render.py::test_order -q`.
- [ ] **X3-3 [R]** `.venv/bin/pytest tests/test_digest_render.py::test_three_lines -q`.
- [ ] **X3-4 [R]** `.venv/bin/pytest tests/test_digest_render.py::test_span_marker_roundtrip -q`.
- [ ] **X3-5 [R]** `.venv/bin/pytest tests/test_digest_deterministic.py -q`.

### X4 · 운영·보고

- [ ] **X4-1 [R]** `.venv/bin/pytest tests/test_gates.py::test_required_keys tests/test_report_shape.py::test_gates_sha256 -q` — `gates.yaml` 일곱 키·`gates_sha256`.
- [ ] **X4-2 [R]** `.venv/bin/pytest tests/test_report_shape.py::test_p4b_owned_keys tests/test_report_shape.py::test_all_keys tests/test_report_shape.py::test_total_key_count -q` — P4b는 23 키 값 채움(3 키는 자리표 `{}`), P5 뒤에는 26 키 모두 값이 비지 않음, `len(RUN_JSON_KEY_PATHS) == 26`.
- [ ] **X4-3 [R]** `.venv/bin/pytest tests/test_g_recall_report_only.py -q` — `gates.yaml`의 `g_recall == "report_only"`. `--gold`로 픽스처 두 개 각각 CLI 돌려 종료 0.
- [ ] **X4-4 [R]** `.venv/bin/coverage run -m pytest -q && .venv/bin/coverage report --include='extract/*' --fail-under=80`.
- [ ] **X4-5 [R]** `.venv/bin/pytest tests/test_no_ledger.py -q` — `extract`가 `tools.verify.ledger`·`thresholds.begin`·`l1_exists.load_variants`·`queries.register`를 부르지 않음. `thresholds.load`는 허용.
- [ ] **X4-6 [R]** `.venv/bin/pytest tests/test_p4b_precondition.py tests/test_p5_precondition.py -q` — 각 단계 진입 시 `slice-facts-<run_id>.json`·`docs/decisions.md` 존재.

### AC가 부르는 테스트 노드 → 만드는 단계

| 테스트 노드 | 만드는 단계 | AC |
|---|---|---|
| `tests/test_query_loader.py::*` | P1 | C0-1 |
| `tests/test_gates.py::test_required_keys` | P1 | X4-1 |
| `tests/test_gates.py::test_split_gate_rejects_bad_value` | P1 | C0-10 |
| `tests/test_gates.py::test_split_gate_passes_blank_line_block` | P1 | C0-10 |
| `tests/test_gates.py::test_thresholds_env_var_override` | P1 | C0-10 |
| `tests/test_paths.py` | P1 | 환경 |
| `tests/test_verify_import.py` | P1 | 환경 |
| `tests/test_textlayer.py` | P2 | C0-2 |
| `tests/test_blocks_align_with_codex_raw.py` | P2 | C0-3 |
| `tests/test_pagesection.py::test_pages_in_range` | P2 | C0-6 |
| `tests/test_pagesection.py::test_section_fp_bound` | P2 | C0-6 |
| `tests/test_pagesection.py::test_section_1_body_is_intro` | P2 | C0-6 |
| `tests/test_segmenter_abbreviations.py` | P2 | C0-5 |
| `tests/test_removal.py` | P2 | C0-7 |
| `tests/test_block_text_roundtrip.py` | P2 | C0-4 |
| `tests/test_span_line93.py::test_line93_spanning_exact` | P3 | C0-8 |
| `tests/test_span_ordering.py` | P3 | C0-8(보조) |
| `tests/test_existence_library.py::*` | P3 | X2-5 |
| `tests/test_no_ledger.py` | P3(초안)·P6(최종) | X4-5 |
| `tests/test_symlink.py` | P4a | X1-1 |
| `tests/test_cli_split_gate.py` | P4a | C0-10 |
| `tests/test_records_min.py` | P4a | X2-1 |
| `tests/test_digest_min.py` | P4a | 관측 |
| `tests/test_report_min.py` | P4a | 관측 |
| `tests/test_skill_rules.py::test_four_rules_present` | P4a | X1-5 |
| `tests/test_workfile_min.py::test_missing_required_field_exits_1` | P4a | 관측 |
| `tests/test_p4b_precondition.py` | P4b | X4-6 |
| `tests/test_workfile_reject.py::*` | P4b | X1-2, X1-4 |
| `tests/test_records_shape.py` | P4b | X2-3 |
| `tests/test_records_counts.py` | P4b | X2-1 |
| `tests/test_digest_render.py::test_header_fields` | P4b | X3-1 |
| `tests/test_digest_render.py::test_order` | P4b | X3-2 |
| `tests/test_digest_render.py::test_three_lines` | P4b | X3-3 |
| `tests/test_digest_render.py::test_span_marker_roundtrip` | P4b | X3-4 |
| `tests/test_report_shape.py::test_p4b_owned_keys` | P4b | X4-2 |
| `tests/test_report_shape.py::test_gates_sha256` | P4b | X4-1 |
| `tests/test_report_shape.py::test_total_key_count` | P4b | X4-2 |
| `tests/test_skill_rules.py::test_hardened` | P4b | X1-5 |
| `tests/test_p5_precondition.py` | P5 | X4-6 |
| `tests/test_variant_report.py` | P5 | X2-6 |
| `tests/test_layout_suspect_list.py` | P5 | X2-8 |
| `tests/test_para_id_cross_check.py` | P5 | X2-7 |
| `tests/test_para_id_edges.py` | P5 | X2-7 |
| `tests/test_g_recall_report_only.py::*` | P5 | X4-3 |
| `tests/test_report_shape.py::test_all_keys` | P5 | X4-2 |
| `tests/test_digest_deterministic.py` | P5 | X3-5 |
| `tests/test_symlink_target.py` | P6 | X1-1 |

---

## ADR

**Decision.** 발췌기 v1을 `extract/` 밑 최상위 패키지 `extract`로 짓되, verify는 라이브러리(`schema.validate`, `paragraphs.split_blocks`/`resolve`/`primary`, `l1_exists.check_quote`, `normalize.load`, `queries.load`, `thresholds.load`)로만 부른다. **P1(스켈레톤·gate·query loader·`paragraph_unit.split` 런타임 게이트) → P2(text layer + blocks + segmenter + removal, 세 규칙 section 감지) → P3(spanning + verify L1 라이브러리) → P4a(walking skeleton: 전체 segments.json + 최소 하류) → 결정 게이트 → P4b(6사유·26키 중 23키 값 채움·3키 자리표·spanning 마커·SKILL 조임) → P5(변형·교차·G recall·결정론, 3키 값 덮어씀) → P6(커버리지)**.

**Drivers.** (1) verify 결합을 스키마 JSONL과 순수 함수로 좁히기, (2) 세그먼트 계약의 원문 충실성, (3) Python 3.10 + stdlib + PyYAML 환경.

**Alternatives considered.**
- 스펙 초안 배치 `extract/tools/extract/*.py` — verify `tools/__init__.py` 실존으로 충돌. 무효화.
- verify의 conn-바인딩 진입점 재사용 — 원장·등록 임계 요구. 스펙 사용자 결정과 충돌.
- LLM에게 인용을 받아쓰기 — Principle 1 위반.
- CLI가 API 호출 — 스펙 v1 제외.
- 층별 완성 후 슬라이스(C2) — 관측 없는 결정. 무효화.
- **section 감지 단일 줄 규칙만.** 정답 논문 20 heading 중 4개만 잡음(측정치). 다이제스트가 대부분 `§—`. 세 규칙 세트가 이를 21개로 확장하며 오탐 0 유지.
- **section 감지 단순 pair 규칙 추가.** 17 hit 중 6 오탐(측정치). Title Case와 「번호에 0 성분 없음」을 세 규칙 모두에 붙여 오탐 0으로 밀어냈다.
- **verify가 문장 세그멘터를 흡수(steelman).** 사용자 결정(2026-09-23) 「v1의 verify 결합은 파일 계약과 라이브러리 호출까지」로 무효화. **만료 트리거: verify P4가 랜딩하는 시점**에 재검토.

**Why chosen (받아들인 절충).** (1) 스펙 초안 이름을 버려도 verify 파일 무수정·단일 pytest 설정. (2) P4a가 전체 `segments.json`을 만들되(스펙 준수) 하류는 최소만 두어 관측 없이 얼리는 결정 최소화. (3) section 감지는 세 규칙 세트로 정답 논문 recall과 오탐을 모두 만족. 41편 전체에서 484 heading·65 비단조 전이 있음을 인정하고 inbox 완화는 [이후]. (4) `record_id = <segment_id>@<sha8>`은 매 실행 달라지는 게 의도 — verify `_insert_claim`이 같은 `row_id`를 다른 run에서 거부하는 규약과 정합.

**Consequences.**
- 코드: `extract/extract/*.py` 여덟 안팎. `extract/tests/*.py` 25 안팎. 커버리지 80%.
- 운영: `extract/config/gates.yaml`은 P1 등록·이후 읽기 전용. 사출물 `extract/results/<query_id>/<slug>.{records.jsonl,md,run.json,segments.json,segments.sha256,selections.jsonl}` + `slice-facts-<run_id>.json` + `extract/docs/decisions.md`.
- **P4a에서 얼리는 결정(P4b가 바꾸지 않음):** CLI 서브커맨드 이름(`segment`·`build`), 세 줄 다이제스트 항목 레이아웃, `record_id` 규약, `run.json` 그룹 이름, CLI `--gold` 후크 이름.
- **P4a에서 얼리지 않는 결정(P4b가 관측 위에서 조임):** workfile 6사유 문자열의 순서·형식, 다이제스트 spanning 마커 문자(`⏎p.N` 가정), SKILL.md 조임 문장.
- **P4b/P5 소유 분리:** `run.json`의 세 키(`checks.per_variant_grades`·`checks.para_id_cross_check`·`checks.g_recall_report_only`)는 P4b에선 `{}` 자리표이고 P5의 세 모듈이 값을 채운다. 테스트도 `test_p4b_owned_keys`(23키 값 채움 확인) 와 `test_all_keys`(P5 뒤 26키 값 채움 확인) 로 분리.
- 문서: `extract/spec/deep-interview-paper-evidence-extractor.md`(2026-09-23 `.athena/specs/`에서 옮김). `extract/README.md`. `extract/docs/decisions.md`는 P4a 결정 게이트 뒤에 만든다. **이 계획 파일 P4a `- [ ] 결정 게이트` 아래에 5-bullet 요약을 사람 손으로 이어 붙인다.**
- 커밋: git 작업은 사용자.

**Follow-ups.** Deferred 전부 — 특히 verify sync는 verify P4–P7 완료 뒤 한 묶음. steelman 재검토도 같은 시점. 41편에서 section 규칙의 단조성 완화도 inbox 배치의 일부.

---

## Deferred

### [이후] (v1 뒤 단계)

- **inbox 배치 (최종 목표).** `inbox/` 아래 PDF 전부에 질의 하나 적용. 트리거: inbox 준비.
- **API 어댑터.** `segments.json`을 API로.
- **조건 5필드와 `numbers` 채우기.** 검사는 verify V4.
- **여러 편 묶은 다이제스트.** slug 순 절.
- **G 회수율 문장 단위.** verify P5 `convert/gold.py`가 문장 파싱을 도입.
- **재실행 일치.** Jaccard와 kind 뒤집힘 비율.
- **section 감지의 단조 필터 + 논문별 heading 픽스처.** 41편 세트에서 484 heading·65 비단조 전이가 관측되므로, inbox 배치에서는 section 번호가 비단조적으로 후퇴할 때 그 heading을 오탐으로 표지하고, 논문마다 저자가 확정한 heading 픽스처를 두어 `test_section_fp_bound`를 논문별로 돌린다. 트리거: inbox 배치 시작.

### [sync] (verify 완성 뒤)

- **`extract_raw`를 verify `sources.yaml`에 변형으로 등록.** 트리거: verify P2 이후. inbox 논문에서 poppler 드리프트가 관측되면 v1 안에서라도 앞당길 수 있다.
- **원장 들이기.** verify 일반 변환기로 records.jsonl을 payload에 감싸 삽입.
- **`row_id = <extractor_id>:<record_id>.q1` 재현.**
- **`verify l1 --paper workload__year-in-llm-serving` 결과 · `matched_variant = extract_raw`.**
- **waivers 표에 이 시스템 행 0건.**
- **`l1_tautological = 0`.**
- **`codex_raw` 블록 대응 등록.**
- **조건 표지 해석 규칙(`unextracted` 미완 처리).** 트리거: verify V4.
- **verify P5 탐침 P·목표 집합 T 재개.**
- **verify가 세그멘터를 흡수(steelman) 재검토.** verify P4 랜딩 시.

---

## Risks

- **section 세 규칙 세트의 논문 밖 잔여 오탐/누락.** 41편 전체에서 484 heading·65 비단조 전이가 관측됨(측정치). 정답 논문에서는 21 heading 오탐 0으로 정합하지만, 다른 논문에서는 오탐이 나올 수 있다. 완화: `test_section_fp_bound`가 정답 논문에 대해 순서까지 픽스처와 일치할 것을 강제. 논문별 픽스처와 단조 필터는 [이후]에 인용.
- **번호 패턴이 `10` 이상 절·`2.10` 같은 소절을 제외.** `[1-9]` 시작·`.[1-9]` 하위 성분 규칙이 그 경우 recall을 잃는다. 정답 논문에는 그런 heading이 없어 문제 없음. inbox에서 나오면 픽스처가 그 사실을 저자에게 노출.
- **문장 분할 오류(약어·소수점·`10^2`).** 완화: `test_segmenter_abbreviations.py`에 열두 부류 못을 박고, 새 약어는 파일에 추가 후 `segmenter_ver`를 올림.
- **poppler 버전 드리프트 — inbox 논문에서.** 완화: `run.json`의 `sources.codex_raw_equal == false` 목록을 실행 보고에 낸다. false인 논문이 있으면 「`extract_raw`를 `sources.yaml`에 등록」 [sync]를 v1 안에서라도 앞당길 수 있다.
- **세션이 계속 금지 필드를 쓴다.** 6사유 파일 전체 거부 반복. 완화: `<slug>.selections.jsonl.rej-<n>.log`에 첫 위반과 사유. 사용자는 SKILL.md 규칙을 세션에 다시 붙여넣어 재실행.
- **LLM이 표 칸·축 라벨 조각을 고르는 것.** P4a 관측(`selections.short_block_count`)에 따라 P4b에서 SKILL.md에 「본문 문단에서만」 문장을 추가할지 결정.
- **memo 충실성.** SKILL.md에서 memo를 한 줄로 규정. 해석·추론은 싣지 않는다.
- **`extract_raw` MISS는 언제나 버그.** waiver 없음. spanning 조각 경계에서 하이픈이 verify `PIECE_SPLIT` 앞에서 정확히 분리되지 않으면 실패. 완화: `test_span_line93.py`가 실측 자리를 못으로 박음.
- **`para_id` 교차 확인의 짧은 세그먼트 목록.** 정준 20자 미만 + 9낱말 미만은 pass/fail 계산에서 제외. `run.json.checks.para_id_cross_check`의 두 목록은 보고 전용.
- **G 블록 회수율 정의 흔들림.** verify P5가 문장 파싱을 확정하기 전. v1은 블록 단위·보고 전용.
