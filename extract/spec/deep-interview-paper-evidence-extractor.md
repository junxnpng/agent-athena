# Deep Interview Spec: 질의 기반 논문 근거 발췌기

> **위치 (가정).** 이 시스템은 `verify/` 옆에 새 디렉토리 `extract/`(저장소 jun-heo/AI-helper)를 만들어 두는 것을 가정한다. verify가 발췌를 Non-Goal로 선언했으므로 verify 디렉토리 안에는 넣지 않는다. 스킬 본체는 `extract/skills/paper-extract/`에 두고, 저장소 `.claude/skills/paper-extract`를 그곳으로의 심볼릭 링크로 만든다. (`verify/skills/claim-judge`와 같은 배치) 스킬 이름은 나중에 바꿀 수 있다. 이 스펙 파일은 `extract/spec/deep-interview-paper-evidence-extractor.md`에 두는 것을 가정한다. **계획(ralplan) 단계에서 다른 위치를 고를 수 있다.**
>
> **경로 규칙 (사용자 결정 2026-09-23).** 문서·코드·설정 어디에도 절대 경로를 쓰지 않는다. 저장소 안 경로는 저장소 루트 기준 상대 경로이고, 저장소 밖 자료(원문 텍스트, PDF, 이전 발췌)는 환경 변수 `$KVCPOOL`(kvcpool-trace-gen 저장소 루트) 기준으로 적는다. 인터뷰 기록은 `.athena/deep-interview/paper-evidence-extractor/state.json`이다.

## Metadata

| 항목 | 값 |
|---|---|
| Interview ID | `paper-evidence-extractor` |
| Rounds | 6 |
| Final Ambiguity | 16.55% (state.json 기록 0.17) |
| Type | brownfield |
| Threshold | 20% |
| Status | done (R6에서 임계 아래로 내려옴). 사용자 검토 2026-09-23 반영 |
| Challenge modes used | contrarian (R4), simplifier (R6) |
| 출력 계약 | `verify/config/evidence_record.schema.json`, 검사기 `verify/tools/verify/schema.py` |
| 질의 형식 | `verify/config/queries/gold-kv-reuse.yaml`, 로더 `verify/tools/verify/queries.py` |
| 문단 단위·L1 규칙 | `verify/config/thresholds.yaml`(`paragraph_unit`, `l1_pass_grades`), `verify/config/normalization.yaml`, `verify/docs/decisions.md` |
| 원문 변형 목록 | `verify/config/sources.yaml` |
| 하류 시스템 스펙 | `verify/spec/deep-interview-verification-system.md` |
| 정답 세트 G | `verify/gold/workload__year-in-llm-serving_handpicked.md` |

## Clarity Breakdown

최종 라운드(R6) 기준이다. 가중치는 brownfield 기본값이다.

| Dimension | Score | Weight | Weighted |
|---|---|---|---|
| goal | 0.85 | 0.35 | 0.2975 |
| constraints | 0.82 | 0.25 | 0.2050 |
| success | 0.80 | 0.25 | 0.2000 |
| context | 0.88 | 0.15 | 0.1320 |
| **합계** | — | 1.00 | **0.8345** (ambiguity 0.1655) |

## Goal

**질의 하나(주제 + 주장 한 문장)와 논문(첫 짜는 한 편, 최종은 inbox 전부)을 받아, 본문에서 질의와 관련된 원문 문장을 골라 `evidence_record.schema.json`을 만족하는 레코드로 내고, 같은 레코드로 논문별 발췌 문장 목록(다이제스트)을 렌더하는 발췌기를 만든다.**

- 정본은 verify 입력 레코드다. 다이제스트는 레코드에서 렌더한 파생물이다. (R1)
- 사용자가 보고 싶은 모습은 「논문별로 발췌한 문장들이 쭉 나오는 것」이다. 문장마다 `-> 메모`와 `[kind · §section · p.N]`가 붙는다. (R2, R5)
- 「제대로 뽑혔다」는 원문 충실성으로 판정한다. 판정은 verify의 존재 검사(L1)가 한다. 문장 내용이 질의를 지지하는지, 조건이 보존됐는지는 verify의 다른 층이 따로 본다. (R2)
- 인용 문장은 코드가 복사한다. 원문을 번호 붙은 문장(세그먼트)으로 미리 자르고, LLM은 번호만 고른다. 그래서 L1 통과는 구조로 보장되고, 남는 위험은 문장 경계가 깨지는 곳뿐이다. (R3)
- LLM은 참고문헌을 뺀 본문 텍스트 전체를 한 번에, 한 모델로 읽는다. (R4)
- LLM은 고른 문장마다 kind 3분류와 「왜 관련인가」를 한국어 한 줄로 붙인다. 이 한 줄이 `claim_text`에 들어간다. (R5)
- 실행 형태는 Claude Code 스킬이고, 세션의 Claude가 읽는다. 첫 짜의 목표는 정답 논문 `workload__year-in-llm-serving` 한 편을 끝까지 돌리는 것이다. (R6)
- 최종 목표는 **질의 하나를 `inbox/`에 담긴 논문 전부에 적용**하는 것이다. 첫 짜는 한 편이고, 이후 단계에서 inbox 전체로 넓힌다. 어떤 논문을 inbox에 넣을지는 사용자가 정한다. (사용자 결정 2026-09-23)

## Constraints

- **경계는 발췌까지다.** 원문에 있는 문장을 고르고 위치를 적는 일까지만 한다. supports/refutes 판정, 조건 보존 판정, 결론의 참·거짓은 verify가 맡는다. (R2)
- **정본은 레코드다.** 다이제스트는 레코드만 입력으로 받아 렌더하고, 레코드에 없는 정보를 더하지 않는다. (R1)
- **인용은 코드가 복사한다. LLM 출력에는 문장 텍스트가 없다.** LLM이 내는 것은 `{segment_id, kind, memo}`뿐이다. 코드가 `segment_id`로 원문 텍스트를 가져와 `quote`에 넣는다. (R3)
- **세그먼트 계약이 정확성 논증의 전부다.** (R3, codebase_context, 가정)
  1. *원천 (사용자 결정 2026-09-23: 원본은 PDF).* 세그먼트 원천은 시스템이 PDF에서 `pdftotext`(기본 모드)로 직접 만든 텍스트 층 `extract_raw`다. 정답 논문도 inbox 논문도 같은 경로를 탄다. 기존 `codex_raw`(verify가 지금 대조하는 변형, `verify/config/thresholds.yaml`의 `paragraph_unit.variant`)는 원천이 아니라 대조·측정 상대다. 두 텍스트가 같으면(같은 pdftotext 모드·버전) verify의 블록 id와 그대로 맞고, 다르면 그 차이를 보고하며 `extract_raw`를 verify 변형으로 등록하는 일은 `[sync]`다. 파일은 verify와 같은 방식(UTF-8, `errors="replace"`)으로 읽고, 실행 기록에 PDF와 텍스트의 sha256, poppler 버전을 남긴다.
  2. *블록.* 문단 블록은 verify의 `paragraphs.split_blocks(text, "extract_raw")` 결과를 그대로 쓴다. 이 함수는 복제하지 않고 import한다. (가정) `locator.para_id`는 세그먼트가 나온 블록의 id(`extract_raw#NNNN`)다. `extract_raw`와 `codex_raw`가 같은 텍스트면 번호도 verify의 블록 id와 같다.
  3. *문장.* 문장은 블록 안에서만 자른다. `segment_id = <para_id>.s<n>`이다. 세그먼트 텍스트는 `block.text[start:end]` 그대로이며, 줄바꿈·줄끝 하이픈·인용 번호까지 한 글자도 바꾸지 않는다. 블록 경계를 넘는 세그먼트는 아래 5의 spanning segment만이다.
  4. *제거.* 참고문헌, running header, arXiv 스탬프는 세그먼트(블록) 통째로만 LLM 화면에서 뺀다. 세그먼트 안의 글자를 지우지 않고, 번호도 다시 매기지 않는다. 블록 안에 끼어든 스탬프처럼 통째로 뺄 수 없는 것은 그대로 두고, 경계 깨짐으로 보고한다.
  5. *쪽 넘김 합치기 (사용자 결정 2026-09-23).* 쪽 넘김이나 그림·표 블록이 끼어들어 한 문장이 두 블록에 걸치면, 앞 블록의 끝 조각과 다음 본문 블록의 첫 조각을 **하나의 spanning segment로 묶는다.** 의미가 완결되게 보이기 위해서다. 세그먼트 텍스트는 `조각1 […] 조각2`이고, 조각마다 원문 부분 문자열 그대로다. `[…]`는 verify L1이 인용을 조각으로 나누는 생략 표지이므로, 조각 둘이 순서대로 원문에 있으면 exact로 통과한다. 사이에 끼어든 header·표·캡션 세그먼트는 묶지 않고 그대로 남긴다. `segment_id`는 첫 조각의 것, `locator.para_id`는 첫 조각의 블록이며, `resolved_para_ids`에 두 블록을 모두 적는다.
  6. *귀결.* 모든 `quote`는 `extract_raw`의 원문 부분 문자열(spanning segment면 조각마다)이므로 `extract_raw`에서 exact로 맞아야 한다. **거기서 나는 L1 MISS(또는 strict·loose·gapped)는 면제할 대상이 아니라 세그먼트 분할이나 복사 경로의 버그다.** 이 시스템의 행에는 waiver를 쓰지 않는다. `codex_raw`에 대한 등급은 두 텍스트 층이 얼마나 같은지를 말해 주는 보고값이다.
- **통독은 한 번, 한 모델로 한다.** 참고문헌을 뺀 본문 전체를 쪼개지 않고 한 번에 읽힌다. 토큰 예산은 설계 제약이 아니다. PDF를 문서로 넣지 않고 텍스트로 넣는다. (R4)
- **레코드 필드의 범위는 인용 + 위치 + kind + 메모다.** `conditions`와 `numbers`는 v1에서 비우고, 채우는 일은 이후 단계로 넘긴다. verify 검사기가 빈 조건 값을 격리하므로 v1은 다섯 필드에 미추출 표지 `unextracted`를 넣어 스키마 검사를 통과시키고, verify가 이 표지를 어떻게 읽을지는 verify 완성 뒤 동기화 단계에서 정한다. (R5, 충돌 1, 사용자 결정 2026-09-23)
- **L1 기준은 verify에 등록된 통과 등급보다 좁다.** 이 시스템은 자기 원천 `extract_raw`에 대해 exact만 통과로 친다. verify v2가 통과로 치는 strict·loose·gapped도 여기서는 실패다. 코드가 원문을 복사하므로 exact는 구성상 보장되어야 하고, 아니면 버그다. (R5 「L1 strict 통과」를 원천 확정 뒤 더 좁힘, codebase_context)
- **실행은 Claude Code 스킬로 한다.** API 키를 쓰지 않고 세션 모델이 읽는다. 모델 이름은 `extractor_id`에 남긴다. (R6)
- **첫 짜는 정답 논문 한 편이다.** inbox 배치(최종 목표)와 API 어댑터는 이후 단계다. (R6, 사용자 결정 2026-09-23)
- **선택 기준은 방향을 가리지 않는 관련성이다.** 질의를 지지하는 문장, 제한하는 문장, 반박하는 문장, 조건을 다는 문장을 똑같이 고른다. 방향 판정은 verify의 일이기 때문이다. (R2에서 파생)
- **verify의 계약은 읽기만 한다.** 스키마, 문단 단위, 임계, 정규화 규칙은 verify 쪽 파일을 그대로 읽는다. verify 쪽을 바꿔야 할 일이 생기면 verify의 결정으로 따로 연다. (가정)
- **verify와의 결합은 파일 계약까지다.** v1은 스키마를 만족하는 JSONL을 내고, 검사가 필요하면 verify의 모듈(`schema`, `normalize`, `l1_exists`, `paragraphs`)을 라이브러리로 부른다. 원장 들이기, 보고서 연동, 조건 표지의 해석 같은 메타데이터 구성은 verify 구현이 끝난 뒤 동기화한다. 아래 기준의 `[sync]` 표기가 그 단계다. (사용자 결정 2026-09-23)
- **환경은 Python 3.10 stdlib + PyYAML이다.** `verify/.venv`에는 pytest·PyYAML·coverage만 있다. `pdftotext`/`pdfinfo`(poppler)는 시스템에 있고, PyMuPDF 1.27은 시스템 python3에만 있다. `pdftotext`(poppler)는 v1부터 PDF에서 텍스트 층을 만드는 도구다. 버전을 실행 보고에 남긴다. (codebase_context, 사용자 결정 2026-09-23)
- **코드·주석·docstring은 영어로 쓴다. 테스트를 먼저 쓴다. 커밋은 사용자가 한다.** (codebase_context, 사용자 규칙)

## Non-Goals

- **합치 판정(supports / refutes / insufficient).** verify의 판정 층(`judge sweep`/`export`/`import`, 스킬 `claim-judge`)이 한다. 레코드에 방향 라벨을 넣지 않는다. (R2)
- **조건 5필드와 수치 채우기 (v1).** 이후 단계에서 채운다. 채운 뒤의 보존 검사는 verify V4가 한다. (R5)
- **G 회수율을 통과 기준으로 삼는 일.** G는 보고만 한다. (R2)
- **놓친 근거(재현율) 보증.** verify V3(elusion 표본, G 대비 재현율)의 일이다. 이 시스템은 G 회수율을 참고용으로만 낸다. (R2)
- **부분 문장 스팬, 여러 문장을 합친 인용 (v1).** 레코드 하나는 세그먼트 하나다. (기본값)
- **PDF를 문서로 LLM에 주는 일, 단계식·다중 모델 읽기.** 텍스트 통독, 한 모델로 한다. (R4)
- **그림·표 이미지 판독.** 텍스트 층에 없는 값(예: pdftotext가 빠뜨리는 그림 안 라벨)은 뽑지 않는다. (codebase_context)
- **어떤 논문을 읽을지 고르는 일(검색).** 입력은 질의와 논문(첫 짜 한 편, 최종은 inbox 전부)이다. inbox에 무엇을 넣을지는 사용자가 정한다. (인터뷰 범위 밖)
- **패턴 배정·종합 서술.** 옛 파이프라인의 「804건 중 647건 미배정」은 이 시스템이 풀 문제가 아니다. (codebase_context)
- **API 실행과 inbox 배치 (v1).** 이후 단계다. inbox 배치는 최종 목표다. (R6, 사용자 결정 2026-09-23)

## Acceptance Criteria

표기: `[v1]`은 첫 출시(정답 논문 한 편)의 완료 조건, `[이후]`는 v1 뒤 단계의 조건, `[sync]`는 verify 구현이 끝난 뒤 두 시스템의 메타데이터를 맞추는 단계의 조건이다. 수치 N은 그 실행에서 고른 문장 수다.

### C0. 입력·세그먼트

- [ ] `[v1]` 질의 파일은 **사용자가 실행 시점에 쓴다.** 형식은 verify의 질의 yaml과 같고 `queries.load`로 읽는다. `query_id`·`topic`·`claim_text`·`source`가 필수다. 이 가운데 하나가 빠진 파일을 넣으면 종료 코드 1로 멈추는 테스트가 있다. 개발·테스트는 픽스처 질의(`gold-kv-reuse.yaml` 초안의 복제)를 쓰며, 그 초안은 사용자 결정이 아니다. `confirmed_by`가 비어 있어도 실행은 하고, 실행 보고와 다이제스트 머리에 `unconfirmed`가 찍힌다. (사용자 확인 2026-09-23)
- [ ] `[v1]` 정답 논문의 세그먼트 원천은 시스템이 `$KVCPOOL/papers/workload__year-in-llm-serving.pdf`에서 `pdftotext`(기본 모드)로 만든 `extract_raw` 하나다. 실행 보고에 PDF sha256(manifest 값과 같아야 함), 텍스트 sha256, poppler 버전이 적힌다.
- [ ] `[v1]` `extract_raw`가 `codex_raw`와 바이트 단위로 같으면, 블록 수와 블록마다의 `para_id`·텍스트가 verify 원장의 `paragraphs`(variant `codex_raw`) 행과 전부 일치하는 테스트가 있다. 다르면 이 테스트는 건너뛰고 diff 줄 수를 보고하며, 블록 대응은 `[sync]`로 넘긴다. `verify/config/thresholds.yaml`의 `paragraph_unit.split`이 `blank_line_block`이 아니면 실행을 거부한다.
- [ ] `[v1]` 세그먼트 텍스트는 원문 조각이다. 정답 논문의 모든 블록에서, 세그먼트 텍스트와 그 사이 공백을 이으면 블록 텍스트가 바이트 단위로 복원된다. (블록 N개 전부. spanning segment는 조각을 각자의 블록에 되돌려 센다) 블록 경계를 넘는 세그먼트는 spanning segment뿐이고, 그 수를 보고한다.
- [ ] `[v1]` 문장 분할 규칙은 파일로 고정한다. (가정: `extract/config/segmenter.yaml`, 약어 목록 `e.g.`·`i.e.`·`et al.`·`Fig.`·`Eq.`·`Sec.`·`vs.`, 소수점, `10^2` 같은 지수) 실행 기록에 `segmenter_ver`가 남는다. 약어 부류마다 「여기서 자르지 않는다」 단위 테스트가 있다.
- [ ] `[v1]` 세그먼트마다 page와 section을 단다. page는 1 + (블록 시작 앞의 `\f` 개수)다. 정답 논문에서는 모든 세그먼트가 1..16 안에 든다. (manifest `pages: 16`, `\f` 16개) section은 제목 블록에서 추정한 `§<번호>` 형식(verify `section_of`와 같은 모양)이고 null을 허용한다. null인 세그먼트 수를 보고한다.
- [ ] `[v1]` 제거는 세그먼트 단위로만 하고 수가 닫힌다. 참고문헌(정답 논문 `codex_raw` 2489행 `References` 블록부터 목록 끝까지), running header 블록(쪽 머리에 반복되는 줄, 예: 95·97·234·236행), arXiv 스탬프(`$KVCPOOL/papers/codex_source_manifest.json`의 `arxiv_stamp`)를 사유 코드와 함께 실행 보고에 나열한다. 제거 + 표시 = 전체 세그먼트 수가 성립한다. 제거한 참고문헌 낱말 수는 측정치 2,248과 나란히 보고한다.
- [ ] `[v1]` 쪽 넘김을 합친다. 정답 논문 `codex_raw` 93행 「…modern LLM platforms serve many models with」는 쪽 넘김 뒤 header와 Table 1이 끼어드는 자리다. 이 조각이 다음 본문 블록의 첫 조각과 하나의 spanning segment가 되고, 그 `quote`가 `조각1 […] 조각2` 꼴로 verify L1에서 exact 통과하는 고정 테스트가 있다. 끼어든 header·Table 1은 그 세그먼트에 들어가지 않는다.
- [ ] `[v1]` `extract_raw`와 `codex_raw`의 sha256 일치 여부(다르면 diff 줄 수와 첫 차이 위치)를 실행 보고에 기록한다. manifest에 `codex_raw`를 만든 모드가 적혀 있지 않기 때문이다.
- [ ] `[sync]` `extract_raw`를 verify `sources.yaml`의 변형으로 등록해, verify L1이 이 시스템의 원천 텍스트에 직접 대조한다.
- [ ] `[이후]` inbox의 PDF 전부가 같은 경로(PDF → `extract_raw` → 세그먼트)를 탄다.

### X1. 선택·출력

- [ ] `[v1]` `extract/skills/paper-extract/SKILL.md`가 있고, `.claude/skills/paper-extract`가 그 디렉토리를 가리킨다.
- [ ] `[v1]` 작업 파일을 한 번 주고받는다. (verify `judge export/import`와 같은 방식, 가정)
  - 코드가 `<slug>.segments.json`을 쓰고 sha256을 봉인한다. 내용은 질의와, 제거되지 않은 세그먼트 전부를 id와 함께 담은 것이다.
  - 세션 Claude가 `<slug>.selections.jsonl`을 쓴다. 한 줄에 `{segment_id, kind, memo}` 하나이고, 선택으로 `boundary_flag`와 사유를 붙일 수 있다.
  - 코드가 들이면서 한 줄이라도 틀리면 파일 전체를 거부한다. 거부 사유는 여섯 가지이고, 사유마다 테스트가 있다. 없는 id, 제거된 id, 중복 id, 세 값 밖의 kind, 빈 memo, 허용하지 않은 필드(`quote`, `text`, `verdict`, `stance` 등)가 그것이다.
- [ ] `[v1]` 통독은 한 번이다. `segments.json`은 논문의 표시 세그먼트 전부를 한 파일에 담고 쪼개지 않는다. 실행 보고에 본문 낱말 수와 추정 토큰(낱말 × 1.3)이 찍힌다.
- [ ] `[v1]` memo는 한국어 한 줄이다. 줄바꿈이 있는 memo는 거부된다.
- [ ] `[v1]` SKILL.md에 네 규칙이 적혀 있다. 방향을 가리지 않는 관련성으로 고른다. PDF나 다른 원천을 열지 않는다. 문장 텍스트를 쓰지 않는다. kind 세 값은 verify `kind_map.yaml`의 라벨 뜻을 따른다.
- [ ] `[이후]` API 어댑터를 붙인다. 같은 `segments.json`을 API에 보내 같은 형식의 `selections.jsonl`을 받고, 같은 들이기 검사를 거친다. 모델은 `extractor_id`에 남고, 실제 토큰 수가 보고된다.
- [ ] `[이후]` inbox 배치(최종 목표). `inbox/` 아래 PDF 전부에 질의 하나를 적용해 논문마다 C0–X3을 통과하고, 실패한 논문을 나열한다. 41편은 inbox의 한 예다.

### X2. 레코드·존재 검사

- [ ] `[v1]` 수가 닫힌다. 선택 N줄 = 레코드 N개이고, 스키마 격리는 0이다.
- [ ] `[sync]` verify 원장에 들어간 행이 N개이고, 행 id는 `<extractor_id>:<record_id>.q1`이다.
- [ ] `[v1]` 필드가 계약대로 채워진다. (N/N) `quote`는 세그먼트 텍스트와 바이트 단위로 같다. `locator.para_id`는 세그먼트의 블록 id, `locator.page`는 정수, `locator.section`은 문자열 또는 null이다. `claim_text`는 memo, `kind`는 LLM이 준 값, `numbers`는 `[]`, `paper_id`는 slug다. `extractor_id`는 `claude-code-skill:<model>`, `run_id`는 `<query_id>-<date>-<sha8>-<slug>`이다.
- [ ] `[v1]` 레코드를 한 줄 한 레코드로 `verify schema --validate`에 넣으면 `pass: N, quarantine: 0`이 나온다.
- [ ] `[v1]` 조건 필드에 `none`을 가진 행은 0이다. `none`은 「확인했고 원문에 없다」는 뜻인데, 이 시스템은 조건을 확인하지 않기 때문이다. 다섯 필드는 모든 행에서 미추출 표지 `unextracted`를 갖는다. verify가 이 표지를 미완으로 읽는 규칙은 `[sync]`다.
- [ ] `[v1]` verify의 L1 대조 함수(`normalize`, `l1_exists`)를 라이브러리로 불러 `extract_raw`에 대조하면, 모든 행이 exact다. (N/N) strict 이하가 하나라도 나오면 복사 경로 어딘가에서 텍스트가 변형됐다는 뜻이므로 실패다.
- [ ] `[v1]` 같은 함수로 `codex_raw`에 대조한 등급 분포를 보고한다. 두 텍스트 층이 같으면 exact N/N이고, 다르면 등급이 떨어진 행을 diff와 함께 나열한다. 통과 기준은 아니다.
- [ ] `[sync]` 같은 결과가 원장 경로(`verify l1 --paper workload__year-in-llm-serving`)에서도 나오고, `matched_variant`가 `extract_raw`다.
- [ ] `[sync]` verify waivers 표에 이 시스템의 행을 가리키는 항목은 0이다.
- [ ] `[sync]` `l1_tautological`은 0으로 둔다. (verify는 이 값이 1인 행을 `codex` 묶음으로 센다.) 「`codex_raw` 대조는 구성상 통과」라는 사실은 실행 보고에 따로 적는다.
- [ ] `[v1]` `para_id`를 교차 확인한다. `extract_raw` 블록에 대해 verify `paragraphs.resolve(quote)`가 비지 않는 행에서는, 이 시스템의 `para_id`가 그 집합 안에 든다. (N/N) 너무 짧아 풀리지 않는 행(정준 20자 미만이면서 9낱말 미만)과, 반복 문장이라 첫 hit가 다른 블록을 가리키는 행은 목록으로 낸다. `codex_raw` 블록과의 대응은 두 텍스트가 같을 때만 성립하고, 다르면 `[sync]`다.
- [ ] `[v1]` 변형별 등급을 보고한다. 같은 대조 함수로 `claude_body`·`codex_layout`(있으면 `claude_column`까지) 등급 분포를 적되 통과 기준으로 쓰지 않는다. `extract_raw`에서는 exact인데 `claude_body`에서 MISS인 행은 「텍스트 층 뒤섞임 의심」 목록으로 낸다. (단 섞임, 이탤릭 순서 뒤바뀜, 스탬프 끼어듦)
- [ ] `[v1]` 모든 행에 kind(세 값 중 하나)와 비지 않은 memo가 있다. (N/N)
- [ ] `[이후]` 조건 5필드와 `numbers`를 채우는 단계를 붙이고, 검사는 verify V4가 한다. verify `slice facts`의 `conditions_complete_rows`가 미추출 표지 행을 완결로 세지 않는다. 이를 위한 verify 쪽 변경은 `[sync]`다.

### X3. 다이제스트

- [ ] `[v1]` `<slug>.md`가 있다. 머리에 논문 slug와 제목, `query_id`, topic, claim, 질의 확인 상태, `run_id`, `extractor_id`, 문장 수가 있다.
- [ ] `[v1]` 레코드 하나가 항목 하나다. (항목 N개 = 레코드 N개) 문서 순서(page → 블록 seq → 문장 번호)로 늘어서는지 테스트가 확인한다.
- [ ] `[v1]` 항목은 세 줄이다. 인용, `-> memo`, `[kind · §section · p.N]` 순서다. section이 null이면 `§—`로 쓴다. (가정)
- [ ] `[v1]` 인용 표시는 공백만 접는다. 표시 문자열은 레코드 `quote`에 공백 접기만 한 것과 같다. (N/N) spanning segment는 조각을 이어 한 문장으로 보이고, `quote`의 `[…]` 자리에는 쪽 넘김 표지(가정: `⏎p.N`)를 둔다. 표지를 `[…]`로 되돌리고 공백을 접으면 `quote`와 같다.
- [ ] `[v1]` 다이제스트는 레코드만의 함수다. 같은 레코드 파일로 다시 렌더하면 바이트 단위로 같은 파일이 나온다.
- [ ] `[이후]` 질의 하나에 대해 여러 편을 묶은 다이제스트. 논문별 절을 두고, 순서는 slug 순이다.

### X4. 운영·보고

- [ ] `[v1]` 통과 기준은 첫 실행 전에 파일로 등록한다. (가정: `extract/config/gates.yaml`) 내용은 `schema_valid: 1.0`, `l1_variant: extract_raw`, `l1_grades: [exact]`, `l1_pass_rate: 1.0`, `kind_memo_rate: 1.0`, `g_recall: report_only`, `codex_raw_grades: report_only`이다. 실행 보고에 이 파일의 sha256이 남는다.
- [ ] `[v1]` 실행 보고 `<slug>.run.json`이 있다. (가정) 다음 항목을 담는다.
  - 원천: PDF sha256, `extract_raw` sha256과 poppler 버전, `codex_raw`와의 일치 여부, `segmenter_ver`.
  - 세그먼트 수: 블록·세그먼트·사유별 제거·표시 수, 본문 낱말 수와 추정 토큰.
  - 선택 결과: 선택 수, kind 분포, `boundary_flag` 목록, spanning segment 선택 수, 20낱말 미만 블록(표 칸, 축 라벨)에서 나온 선택 수, section null 수.
  - 검사 결과: 스키마 결과, verify L1 등급 분포, 변형별 등급, `para_id` 교차 확인 결과, G 회수율.
- [ ] `[v1]` G 회수율은 보고만 한다. G 블록은 G 원문과 8낱말 shingle을 2개 이상 공유하거나 정준 20자 이상 조각이 연속으로 일치하는 문단 블록이다. (verify `paragraphs`의 해소 규칙) 회수율 = |선택 세그먼트의 블록 ∩ G 블록| / |G 블록|이다. 이 값은 어떤 통과도 막지 않는다.
- [ ] `[v1]` `extract` 테스트가 먼저 쓰이고 전부 통과한다. 줄 커버리지는 80% 이상이다. 세그먼트 계약, 들이기 거부, 레코드 빌드, 다이제스트 렌더, 제거 사유가 모두 테스트 대상이다.
- [ ] `[이후]` G 회수율을 문장 단위로 잰다. verify P5의 `convert/gold.py`가 G를 문장으로 가른 뒤 그 목록을 쓴다.
- [ ] `[이후]` 재실행 일치. 같은 논문·질의로 두 번 돌려 선택 집합의 Jaccard와, 두 실행에서 kind가 뒤집힌 비율을 낸다.
- [ ] `[sync]` 살아 있는 추출기가 생겼으므로 verify P5의 탐침 P·목표 집합 T를 적용할 수 있게 된다. verify 계획은 이것을 「extractor runs are frozen」이라는 이유로 not-applicable로 두었다. 이 항목은 verify 쪽에서 다시 연다.

## Assumptions Exposed & Resolved

| Assumption | Challenge | Resolution |
|---|---|---|
| 발췌기의 산출물은 사람이 읽는 발췌집이다 | R1에서 네 가지 중 하나를 고르게 함 | 정본은 verify 입력 레코드이고, 발췌집은 파생 렌더다 |
| 잘 뽑혔는지는 G 회수율이나 사람 수정량으로 본다 | R2에서 판정 기준을 고르게 함 | verify 통과율(원문 충실성)로 본다. 내용 검증은 따로 하고, G는 보고만 한다 |
| LLM이 문장을 받아 적어도 된다 | R3. 옛 발췌의 waiver 48건과 정답 논문 L1 MISS 6건을 근거로 제시 | 코드가 복사한다. 원문을 번호 붙은 세그먼트로 자르고 LLM은 번호만 고른다 |
| 토큰을 아끼려면 LLM에게 후보만 보여 줘야 한다 (단계식 또는 코드 필터 먼저) | R4 **contrarian**. 통독 / 단계식 / 코드 필터 후 LLM / 통독+상한을 되물음. 「PDF 대신 토큰 덜 쓰는 방식은 없나」라는 사용자 질문에는 실측으로 답함. (41편 약 63만 토큰, 참고문헌 제외 약 49만, 논문당 본문 중앙값 약 1.3만) | 텍스트 통독, 한 모델, 참고문헌 제외로 정함. 토큰 예산은 제약이 아니다. PDF 문서 입력(인터뷰 중 추정으로 텍스트의 2–3배, 측정 아님)은 쓰지 않는다 |
| 레코드를 다 채워야 완성이다 | R5에서 필드 범위를 고르게 함 | 인용 + kind + 한 줄 메모까지다. 조건·수치는 비우고 이후 단계로 넘긴다 |
| 쓸모가 있으려면 처음부터 API 스크립트로 41편을 돌려야 한다 | R6 **simplifier**. 정할 것은 실행 주체와 첫 짜 범위 두 가지뿐이라고 좁힘 | Claude Code 스킬 + 정답 논문 한 편으로 정함. API와 41편은 이후다 |

### 인터뷰어 기본값 (결정 아님)

| Assumption | Challenge | Resolution |
|---|---|---|
| 질의 입력은 verify 질의 yaml 모양(`query_id`, `topic`, `claim_text`, `source`, `confirmed_by`)을 `config/queries/` 아래에서 재사용한다 | 인터뷰에서 묻지 않음 | 「기본값, 확인 필요」. `verify/config/queries/`를 직접 읽기를 권한다. 같은 `query_id`로 verify 보고서와 이어지게 하기 위해서다 |
| 세그먼트 단위는 verify 문단 블록(`codex_raw`의 `blank_line_block`) 안의 문장이다. `segment_id = <para_id>.s<n>`, page는 form feed에서, section은 최선 추정(null 허용)으로 얻는다 | 인터뷰에서 묻지 않음 | 「기본값, 확인 필요」. 세그먼트 계약 2–3에 반영했다 |
| 원천 텍스트는 41편이면 `codex_raw`, 새 PDF면 `pdftotext` raw 모드다. 참고문헌·header·스탬프는 세그먼트 통째로 빼고, 세그먼트 텍스트는 바꾸지 않는다 | 사용자 검토: 「PDF를 원본으로 하면 되겠네」 | **결정(2026-09-23).** 모든 논문이 PDF → `pdftotext`(기본 모드) → `extract_raw` 경로를 탄다. `codex_raw`는 대조·측정 상대다. 제거·불변 규칙은 그대로다 |
| LLM 출력은 `{segment_id, kind, memo}` JSON 목록이다. v1에서 레코드 하나는 세그먼트 하나이고, 연속 선택은 다이제스트에서 나란히 놓인다. 부분 문장 스팬은 없다 | 인터뷰에서 묻지 않음 | 「기본값, 확인 필요」. X1 작업 파일 형식에 반영했다 |
| 다이제스트는 논문별 문서 순서다. 머리는 질의 topic + claim, 항목은 인용 / `-> memo` / `[kind · §section · p.N]`이다 | 인터뷰에서 묻지 않음 | 「기본값, 확인 필요」. X3에 반영했다 |
| 임계: 스키마 유효 100%, `extract_raw`에서 exact로 L1 PASS 100%(MISS는 버그이고 면제 없음), 모든 행에 kind·memo, G 회수율은 보고만, LLM이 표시한 경계 깨짐은 실행 보고에 나열 | 인터뷰에서 수치를 묻지 않음 | 「기본값, 확인 필요」. X2·X4에 반영했다 |
| 배치는 `verify/` 옆 `extract/`이고, 스킬 본체는 `extract/skills/paper-extract`, `.claude/skills/`에 심볼릭 링크를 둔다 | 인터뷰에서 묻지 않음 | 「기본값, 확인 필요」. verify 설계 표는 발췌 스킬 이름으로 `claim-extract`를 예약해 두었으므로(짓지 않음으로 표기) 이름도 계획에서 고른다 |
| 출력은 `results/extract/<query_id>/<slug>.records.json`과 `<slug>.md`, `extractor_id`는 `claude-code-skill:<model>`, `run_id`는 `<query_id>-<date>-<sha8>-<slug>`이다 | 인터뷰에서 묻지 않음 | 「기본값」. 기준은 저장소 루트 상대 경로 `extract/results/<query_id>/…`이고 정본은 JSONL(`<slug>.records.jsonl`)이다. `sha8`은 `selections.jsonl`의 sha256 앞 8자로 둔다 (가정) |

### 스펙 작성 중 드러난 충돌 (결정 아님)

| Assumption | Challenge | Resolution |
|---|---|---|
| 1. 「조건은 빈 채로 두고」와 「스키마 유효 100%」가 함께 성립한다 | `schema.py`는 조건 키가 없으면 `missing_condition_field`, 빈 문자열이면 `empty_condition_value`로 격리한다. `none`은 「확인했고 없음」이라는 주장이다. verify 자체 변환기가 쓰는 `conditions: {}`도 `schema --validate`에서는 격리된다 | **결정(2026-09-23).** v1은 다섯 필드에 `unextracted`를 넣어 검사기를 통과시킨다. verify `report._conditions_complete`가 비지 않은 문자열을 완결로 세는 문제는 verify 구현이 끝난 뒤 `[sync]`에서 표지를 미완으로 읽는 규칙으로 푼다. 첫 실행을 막지 않는다 |
| 2. verify는 스키마만 지킨 레코드를 받아들인다 | `verify convert`는 `claude`·`codex` 변환기뿐이다. `ledger import`는 변환기 payload(`extractor_id`, `paper_id`, `run_id`, `source_file`, `source_sha256`, `source_records`, `rows`, `quarantined`, `paragraph_unit`)를 요구한다 | **결정(2026-09-23).** v1은 스키마를 만족하는 JSONL만 낸다. 원장에 들이는 방법(verify 일반 변환기 또는 payload 직접 작성)은 `[sync]`에서 정한다. 권장은 verify 쪽 일반 변환기다. verify의 내부 형식을 verify 안에 가두기 때문이다 |
| 3. `record_id`는 `<slug>:<segment_id>`면 충분하다 | verify `_insert_claim`은 같은 `row_id`를 다른 run에서 다시 들이지 않는다 | 「기본값」. `record_id = <segment_id>@<sha8>`로 run마다 다르게 한다. 원장 충돌 여부는 `[sync]`에서 확인한다 |
| 4. 메모는 `claim_text`에 넣어도 무해하다 | `claim-judge`는 `record_claim_text`에 대해 faithfulness(「원문이 추출기가 말한 것을 말하는가」)를 판정한다. 원문 밖의 해석을 담은 「왜 관련인가」 메모는 insufficient/refutes로 나올 수 있다 | 「가정, 확인 필요」. SKILL.md에서 memo를 「이 문장이 질의에 대해 말하는 것」을 한 줄로 적도록 규정하고, 해석은 싣지 않는다. faithfulness 결과는 verify 쪽 관찰이고, 이 시스템의 통과 기준이 아니다 |
| 5. 질의는 확인된 상태로 들어온다 | `gold-kv-reuse.yaml`은 에이전트 초안이다. (`confirmed_by` 비어 있음) verify는 이 질의에 대한 판정을 거부한다 | **확인(2026-09-23).** 질의는 사용자가 실행 시점에 쓴다. 초안 yaml은 개발·테스트 픽스처일 뿐이다. `confirmed_by`가 비어도 발췌는 실행하고 `unconfirmed`로 표시한다 |
| 6. 산출물 `.records.json`은 곧 verify 입력이다 | `verify schema --validate`는 JSONL을 읽는다 | 「기본값」. 정본은 한 줄 한 레코드(JSONL) `<slug>.records.jsonl`이다 |
| 7. L1 exact면 PDF에 충실하다 | exact는 `codex_raw`에 대한 충실성이다. 이탤릭 순서 뒤바뀜, 스탬프 끼어듦, 단 섞임처럼 텍스트 층 자체의 결함은 구성상 통과한다 | X2의 변형별 등급 보고로 드러낸다. 통과 기준에는 넣지 않는다 |
| 8. 문장은 블록 안에서 끝난다 | 정답 논문 `codex_raw` 93–99행: 쪽 넘김, header 두 줄, Table 1이 한 문장 사이에 끼어든다 | **결정(2026-09-23).** 합친다. 두 조각을 `[…]`로 이은 spanning segment 하나로 두고, L1은 조각 대조로 exact 통과한다. 의미가 완결되게 보이는 것이 이유다. (계약 5) |

### 사용자 검토 결정 (2026-09-23)

spec 초안을 읽은 뒤 사용자가 내린 결정이다. 위 표들의 해당 행에도 반영했다.

| 항목 | 결정 |
|---|---|
| 경로 | 절대 경로를 쓰지 않는다. 저장소 루트 상대 경로와 `$KVCPOOL` 기준 상대 경로만 쓴다 |
| 최종 목표 | 질의 하나를 `inbox/`의 논문 전부에 적용하는 것. 첫 짜는 정답 논문 한 편 |
| verify 결합 | v1은 스키마 JSONL과 라이브러리 호출까지만. 원장·보고·조건 표지 해석은 verify 완성 뒤 `[sync]`에서 맞춘다 |
| 쪽 넘김 | 합친다. spanning segment, `[…]`로 이어 L1 조각 대조로 통과 |
| 원본 | PDF. 텍스트 층은 시스템이 매 실행 `pdftotext`(기본 모드)로 만든다(`extract_raw`). `codex_raw`는 대조·측정 상대 |
| 텍스트 층 모드 (측정 2026-09-23) | poppler 22.02.0의 `pdftotext` 기본 모드 출력이 41편 전부에서 `codex_raw`와 바이트 단위로 같다. `-raw` 모드는 정답 논문에서 3,246줄 다르다. 그래서 `extract_raw`는 기본 모드로 만들며, 같은 poppler 버전에서는 verify의 블록 id와 그대로 맞는다. 이름의 `raw`는 기존 변형 이름을 따른 것이다 |
| 메모 규정, 다이제스트 형식 | spec 초안대로 |
| 질의 | 사용자가 실행 시점에 쓴다. 초안 yaml은 개발 픽스처 |
| 스킬 이름 | `paper-extract`로 두되 나중에 바꿀 수 있다 |

## Technical Context

### 출력 계약 (`verify/config/evidence_record.schema.json`, `verify/tools/verify/schema.py`)

- 레코드 하나는 인용 하나다. 필수 필드는 `record_id`, `paper_id`, `quote`, `locator{section, page, para_id}`, `claim_text`, `conditions{unit, denominator, window, ideal_or_measured, baseline}`, `numbers[]{value, unit, definition, derived_from}`, `kind`, `extractor_id`, `run_id`다.
- `locator`의 세 키는 반드시 있어야 하고, 값은 null일 수 있다. (`section`: string|null, `page`: integer|null, `para_id`: string|null)
- 조건 값은 비지 않은 문자열이어야 하고, `"none"`은 「확인했고 원문에 없다」는 뜻이다. 키가 빠지면 채우지 않고 격리한다. JSON Schema 파일에는 `minLength`가 없지만, 실제 검사기 `schema.validate`는 빈 문자열을 `empty_condition_value`로 격리한다.
- `numbers`는 빈 배열이어도 유효하다. `kind`는 `measurement` / `author_interpretation` / `extrapolation` 중 하나다.
- `verify schema --validate <JSONL>`은 `pass: N, quarantine: M`과 사유 코드별 수를 찍는다.
- kind의 뜻은 verify `config/kind_map.yaml`의 원 라벨에서 가져온다. SKILL.md도 이 뜻을 가르친다.

| kind | kind_map 원 라벨 |
|---|---|
| measurement | 실제 관측, 실제 프로덕션 트레이스, 실배포 관측, 저자 트레이스 관측, 테스트베드, 저자의 마이크로벤치마크 측정 |
| author_interpretation | 저자의 해석·논증·요약·가설·분석·분류·문제 규정·한계 서술·위치 짓기, 설계·구현 설명, 설계·기전 설명, 기전 설명, 방법 설명 |
| extrapolation | 저자의 계산, 저자의 모형, 시뮬레이션 |

### verify가 이 출력을 검사하는 방식

- **문단 단위(봉인됨).** `thresholds.yaml`의 `paragraph_unit`은 `{variant: codex_raw, split: blank_line_block, min_words: 20}`이다. `ledger._check_unit`은 등록된 단위와 다른 단위의 payload를 거부한다.
- **블록 id.** `paragraphs.Block.para_id`는 `f"{variant}#{seq:04d}"`이고, `seq`는 모든 비지 않은 블록에 매긴다. 20낱말 미만 블록도 번호를 받는다. `min_words`는 elusion 프레임에만 쓴다.
- **쪽 넘김.** `split_blocks`는 `\f`를 줄바꿈으로 바꾼다. 쪽 머리 header 줄 앞에는 빈 줄이 생기므로, 쪽 넘김은 늘 블록을 가른다.
- **행 단위.** 인용 하나가 행 하나이고, `row_id = <extractor>:<record_id>.q<n>`이다.
  - `l1_exists.extractor_set`은 `row_id`의 첫 콜론 앞을 묶음 이름으로 쓴다. `claude-code-skill:<model>`은 `claude-code-skill`로 묶이고, `l1_tautological=1`인 행은 `codex`로 묶인다.
  - `_insert_claim`은 같은 `row_id`가 다른 run에서 오면 거부한다.
  - `register_paper`는 등록 뒤 변형 텍스트의 sha256이 바뀌면 import를 멈춘다.
- **인용 → 블록 해소.** 조각 하나가 정준형으로 연속 일치하거나(정준 20자 이상, `MIN_PROBE`), 8낱말 shingle을 2개 이상 공유하면 그 블록에 해소된다. `primary`는 첫 연속 hit를 고른다. 따라서 논문에 두 번 나오는 문장은 앞쪽 블록을 가리킨다.
- **L1 대조.**
  - 인용은 생략 표지(`…`, `...`, `[...]`, `**`, `|`)에서 조각으로 나뉘고, 조각들은 한 변형 안에서 순서대로 나와야 한다.
  - `[^\]]*`를 쓰므로 `[18, 21, 23, 25]` 같은 인용 번호 괄호도 생략 표지로 읽힌다. 원문 그대로이므로 통과에는 영향이 없지만, 괄호 안 글자는 대조되지 않는다.
  - 등급은 exact(원문 부분 문자열) > strict(정규화 6규칙) > loose(영숫자만) > gapped(20자 이상 3구간, 사이 1,000자까지)다. 변형 중 가장 좋은 등급을 쓰고, 같으면 `sources.yaml`에서 앞선 변형(`codex_raw`가 맨 앞)을 쓴다. verifier는 `l1-exists-v2`, protocol은 `v2`다.
- **정답 논문 L1 측정(2026-09-23).** Claude 44행은 v1에서 MISS 6이었다. 모두 header·그림 블록이 인용 가운데 끼어든 경우였다. v2 gapped로 통과하게 됐고, 이것이 사용자가 오탐을 감수한 결정이다. 이 시스템은 블록 안 세그먼트만 쓰므로 gapped에 기댈 일이 없어야 한다.
- **판정 층.** `claim-judge`는 행마다 `alignment`(증거 ↔ 질의 claim)와 `faithfulness`(증거 ↔ `record_claim_text`)를 낸다. memo가 `claim_text`로 들어가므로 faithfulness의 대상이 된다.

### 원문 텍스트 변형과 정답 논문 `codex_raw`의 실제 모습

- **원본과 텍스트 층 (사용자 결정 2026-09-23).** 원본은 PDF다. LLM과 대조 코드가 읽는 것은 PDF의 텍스트 층이고, 이 시스템은 그것을 매 실행 `pdftotext`(기본 모드)로 직접 꺼내 `extract_raw`라 부른다. 정답 논문도 inbox 논문도 같다. `codex_raw`는 Codex 실행 때 같은 방식으로 꺼내 둔 파일(`$KVCPOOL/papers/codex_source_text/codex_<slug>.txt`)이고 verify가 지금 대조하는 변형이다. 두 파일이 같으면 「원문 그대로」가 두 시스템에서 같은 뜻이 되고, 다르면 `extract_raw`를 verify 변형으로 등록하는 것이 `[sync]`의 첫 일이다.
- `sources.yaml`의 변형은 `codex_raw`(`papers/codex_source_text/codex_{slug}.txt`), `codex_layout`(두 단을 한 줄에 나란히 놓아 여러 줄 인용이 연속 일치하지 않음), `claude_body`(`claude_extract.py`, `pdftotext -bbox`로 단을 인식한 재추출), `claude_column`(2편만)이다.
- `$KVCPOOL/papers/codex_source_manifest.json`은 편마다 PDF sha256, 쪽수, `arxiv_stamp`, 텍스트 경로를 적는다. `codex_raw`를 만든 `pdftotext` 모드는 적혀 있지 않다.
- 정답 논문 `codex_raw`에 대해 확인한 사실은 다음과 같다.
  - `\f` 16개로 16쪽이다. (manifest `pages: 16`)
  - 스탬프 `arXiv:2608.13573v2`는 1행에 한 번 나오는 독립 블록이다.
  - running header(`Conference’17, July 2017, Washington, DC, USA`, `Nixon et al.`, 논문 제목)는 쪽 머리에서 독립 블록이다.
  - `References`는 2489행이고, 그 뒤에 부록 제목은 보이지 않는다.
  - 26–30행은 `Abstract`, `Keywords` 제목 뒤에 초록 본문이 오는 순서로 뒤섞여 있고, `§번호 제목` 형태의 제목 줄은 드물다. (220·221·1967·1968행 등) section은 최선 추정일 수밖에 없다.
- 어느 쪽 PDF 도구도 그림 안 라벨을 텍스트 층에 싣지 않는 경우가 있다. (Codex 피드백 기록: DualMap p.10/p.18 라벨 23개)

### 실행 환경

`verify/.venv`는 Python 3.10.12에 pytest·PyYAML·coverage만 있다. (numpy·torch 없음) 시스템에는 `pdftotext`/`pdfinfo`(poppler)와 PyMuPDF 1.27(시스템 python3)이 있다. 클론마다 워크스페이스 안에 `.venv`를 따로 만드는 규칙이 있다. `extract/.venv`를 같은 구성으로 만들고 verify 패키지는 경로로 import하는 것을 가정한다.

### 이전 발췌와 알려진 실패 → 이 설계의 대응

이전 발췌는 `$KVCPOOL/docs/patterns/claude_evidence_extraction_prompt.md`(와 codex 쌍)였다. 긴 한국어 프롬프트 하나로 `papers/` 전체를 KV-pool 연구 목표에 비춰 읽게 했다. 산출은 `claude_quotes/<slug>.md` 1,313구와 `claude_pattern_data.json` 804건이었고, Codex는 1,164건을 냈다. (quote 필드 없이 fragment만)

| 알려진 실패 (review-feedback 09-09, claude-pattern-full-review 09-15) | 이 설계에서 |
|---|---|
| 인용을 요약하며 올라가는 동안 조건·분모가 사라짐 | 인용은 세그먼트 원문 그대로이고, 요약은 memo에만 둔다. 조건 추출은 이후 단계다 |
| 수치를 다른 실험에 잘못 붙임 | v1은 `numbers`를 비운다 |
| verbatim waiver 48건 (italic reorder 32, stamp intrusion 9, gap 5, column interleave 1, visual 1) | 받아 적기에서 오는 오류는 구조적으로 사라진다. 텍스트 층 자체의 결함은 `codex_raw`에 있으면 그대로 복사되므로, 변형별 등급으로 드러낸다 |
| layout 텍스트만 보면 참인 문장이 MISS | 원천이 raw 모드 텍스트 층(`extract_raw`)이다. layout 모드는 대조 보고에만 쓴다 |
| 정답 논문 44행 중 6행이 header·그림 끼어듦으로 L1 MISS | 세그먼트는 블록 안에서 자르고, 쪽을 넘는 문장은 두 조각을 `[…]`로 이은 spanning segment 하나로 둔다. verify L1은 조각을 순서대로 대조하므로 끼어든 header·그림이 있어도 exact로 통과한다 |
| 804건 중 647건이 패턴에 배정되지 않음 | 범위 밖이다. 대신 레코드는 생성 시점부터 질의 하나(`query_id`)에 묶인다 |

### 토큰 측정 (R4)

41편 `codex_raw`는 485,568낱말(약 63.1만 토큰)이고, 참고문헌이 23%이며 본문은 약 48.6만 토큰이다. 논문당 중앙값은 12,043낱말(약 1.57만 토큰, 본문 약 1.3만)이다. 정답 논문은 12,254낱말이고 그중 2,248이 참고문헌이므로, 본문은 약 1만 낱말(약 1.3만 토큰)이다. 한 편의 본문을 세션 한 번에 읽히는 데 제약이 없다는 R4 판단의 근거다. 세그먼트 id 표기가 더하는 토큰은 실행 보고에서 잰다.

### 정답 세트 G

`verify/gold/workload__year-in-llm-serving_handpicked.md`는 사용자가 뽑은 원문 약 40문장에 한줄평과 `->` 메모를 붙인 것이다. 문장 경계가 붙어 있다. (첫 문장이 한줄평과 `****`로 접합되어 있음) verify 계획(P5, 미완)은 규칙에 따라 계수가 33–37로 흔들린다고 적었고, 문장 파싱을 `convert/gold.py`로 고정할 예정이다. 그래서 v1의 G 회수율은 문장 파싱이 필요 없는 블록 단위로 정의했다. 참고로 옛 Claude 발췌는 이 논문에서 30건 44구를 냈고, verify 프레임은 70블록 중 36블록을 사용으로 셌다.

### 구현 형태 (가정, 이름은 계획에서 확정)

| 층 | 형태 | v1 |
|---|---|---|
| PDF → 텍스트 층 (`pdftotext`(기본 모드), PDF·텍스트 sha256과 poppler 버전 기록, `codex_raw` 대조) | `extract/tools/extract/textlayer.py` | **짓는다** |
| 세그먼트 분할 (블록 → 문장, 제거, page/section, spanning 합치기) | `extract/tools/extract/segment.py`, 규칙 파일 `extract/config/segmenter.yaml` | **짓는다** |
| 작업 파일 내보내기·들이기 (sha256 봉인, 줄 단위 검사, 파일 단위 거부) | `workfile.py` + CLI `extract segment` / `extract build --model <id>` | **짓는다** |
| 레코드 빌더·다이제스트 렌더·실행 보고 | `records.py`, `digest.py`, `report.py` | **짓는다** |
| 선택 프롬프트 | 스킬 `extract/skills/paper-extract/SKILL.md` | **짓는다** |
| verify 검사 | `schema.validate`, `normalize`/`l1_exists` 대조, `paragraphs.resolve`를 라이브러리로 | **쓴다** |
| inbox 배치, API 어댑터 | — | 이후 (inbox는 최종 목표) |
| verify 원장 들이기·보고 연동·조건 표지 해석·`extract_raw` 변형 등록 | verify 쪽 일반 변환기 또는 payload 직접 작성, `sources.yaml` | sync (verify 완성 뒤) |

## Ontology

최종 라운드(R6)의 8개 엔티티다.

| Entity | Type | Fields | Relationships |
|---|---|---|---|
| Paper | input | slug, pdf_path, pages | has one SourceText; has many EvidenceRecord |
| SourceText | reference | variant_name (`extract_raw`), text, offsets, sha256, poppler_version | produced from Paper by `pdftotext`(기본 모드); reference for existence check; compared with `codex_raw` |
| Query | input | claim_or_topic_text | drives ExtractorRun |
| EvidenceRecord | output | record_id, paper_id, quote (copied from Segment), locator{section, page, para_id}, claim_text (= one-line memo, Korean), conditions (empty, later stage), numbers (empty, later stage), kind (LLM 3-class), extractor_id, run_id | conforms to verify schema; quote must exist in SourceText |
| ExtractorRun | process | extractor_id (claude-code-skill:<session model>), run_id, query_id, paper slug, model | runs inside a Claude Code session as a skill; reads SourceText body (references stripped); answers Query; emits EvidenceRecord + PaperDigest |
| PaperDigest | derived-output | per-paper sentence list | rendered from EvidenceRecord; what the user reads |
| VerifySystem | downstream | L1 existence, L2–L4 content (separate) | consumes EvidenceRecord; defines success |
| Segment | unit | segment_id, text (spanning이면 `조각1 […] 조각2`), page, section, char_offsets | partitions SourceText; selected by ExtractorRun; copied into EvidenceRecord.quote |

스펙 본문에는 작업 파일(`segments.json`/`selections.jsonl`)과 실행 보고라는 산출물이 더 나온다. 이 둘은 인터뷰 온톨로지에 없던 구현 산출물이고, 각각 ExtractorRun의 입출력과 VerifySystem 보고 쪽에 속한다.

## Ontology Convergence

| Round | Count | New | Changed | Stable | Stability |
|---|---|---|---|---|---|
| 1 | 6 | 6 | 0 | 0 | — |
| 2 | 7 | 1 | 1 | 5 | 0.86 |
| 3 | 8 | 1 | 0 | 7 | 0.88 |
| 4 | 8 | 0 | 0 | 8 | 1.00 |
| 5 | 8 | 0 | 0 | 8 | 1.00 |
| 6 | 8 | 0 | 0 | 8 | 1.00 |

state.json은 R1을 `stable: 6`으로 기록했지만, 이전 라운드가 없으므로 0으로 적었다. R2의 변화는 SourceText 신규와 Digest → PaperDigest 개명이다. R3에서 Segment가 새로 나왔다. R5·R6에서는 EvidenceRecord 필드에 값 규칙이, ExtractorRun에 필드(`query_id`, `model`)가 붙었지만 엔티티 집합과 관계 구조는 그대로라 기록상 changed 0이다.

## Interview Transcript

<details>
<summary>Full Q&A (6 rounds)</summary>

**Round 1 — goal**

Q. 이 시스템의 1차 산출물은 무엇입니까? (verify 입력 레코드 / 사람이 읽는 발췌집 / 둘 다 / 범용 도구)

A. verify 입력 레코드. evidence_record.schema.json을 만족하는 레코드 묶음이 정본, 발췌집은 파생 렌더.

→ ambiguity 63.0% (weakest: success). 메모: 완성 기준이 읽기 방식과 예산 제약을 거꾸로 정하므로 다음에는 success를 묻는다.

**Round 2 — success**

Q. 논문별 발췌 문장 목록이 나온 뒤, 「제대로 뽑혔다」를 무엇으로 판정합니까? (G 회수율 / verify 통과율 / 이전 발췌보다 나음 / 사람 수정 최소)

A. verify 통과율. 원문 기준으로 얼마나 제대로 뽑혔는지 확인이 필요. 문장 자체(내용)에 대한 검증은 따로 한다. 원하는 모습은 논문별로 발췌 문장이 쭉 나오는 것.

→ ambiguity 46.25% (weakest: constraints). 메모: 통과 기준이 원문 그대로이므로, LLM이 받아 적는지 코드가 복사하는지가 통과율을 결정한다.

**Round 3 — constraints**

Q. 발췌 문장을 누가 베낍니까? (코드가 복사 / LLM이 받아 적기 / 혼합 / 미결)

A. 코드가 복사. 원문을 문장·문단 단위로 잘라 번호를 붙이고 LLM은 번호만 고른다. 존재 검사는 구조적으로 통과.

→ ambiguity 37.25% (weakest: constraints). 메모: LLM이 논문 전체를 보는지 후보만 보는지, 토큰 예산이 제약인지가 아직 정해지지 않았다.

**Round 4 — constraints (challenge: contrarian)**

Q. LLM이 논문을 어떻게 통독합니까? (텍스트 통독 한 모델 / 단계식 / 코드 필터 후 LLM / 통독+상한 등록)

사용자 질문: PDF 대신 토큰 덜 쓰는 통독 방식은 없나? → 측정: 41편 텍스트 63만 토큰, 참고문헌 제외 49만, 논문당 중앙값 1.3만.

A. 텍스트 통독, 한 모델. 참고문헌을 뺀 본문 텍스트 전체를 한 모델이 한 번에 읽고 세그먼트 번호를 고른다. 토큰 예산은 제약 아님.

→ ambiguity 29.95% (weakest: success). 메모: 존재 통과는 구조로 보장된다. 남은 문제는 통과 조건이 인용만인지 필드 완성까지인지이고, 이것이 완성 범위와 LLM 출력 크기를 정한다.

**Round 5 — success**

Q. 통과 조건에 문장 외에 무엇을 더 넣습니까? (인용+kind+한줄 메모 / 인용+위치만 / 전체 필드 / 인용+메모, kind 나중)

A. 인용 + kind + 한줄 메모. LLM이 문장마다 kind 3분류와 한국어 한 줄(왜 관련인가)을 붙인다. 조건·수치는 빈 채로 두고 이후 단계로. 완성 = 스키마 유효 100% + L1 strict 통과 + 모든 행에 kind·메모.

→ ambiguity 22.45% (weakest: goal). 메모: 실행 형태(스킬 vs API 스크립트)가 모델·키·재현성을 한 번에 정한다. 다음은 simplifier로 묻는다.

**Round 6 — goal (challenge: simplifier)**

Q. 읽기를 어디에서 실행하고, 처음에 어디까지 만듭니까? (Claude Code 스킬+정답 논문 1편 / API 스크립트+41편 배치 / 스킬 먼저, API 다음 / 스킬+41편)

사용자 질문: 여기서 정해줘야 될 것이 뭐야? → 실행 주체(스킬 vs API 스크립트)와 첫 짜 범위 두 가지라고 설명.

A. Claude Code 스킬 + 정답 논문 1편. 세션의 Claude가 읽는다. API 키 불필요. 첫 목표는 year-in-llm-serving 한 편을 끝까지 돌려 보는 것.

→ ambiguity 16.55%. 임계 20% 아래로 내려와 인터뷰를 마쳤다. 남은 빈칸(질의 형식, 정렬, 임계 수치)은 인터뷰어 기본값으로 채우고 가정으로 표시했다.

</details>
