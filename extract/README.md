# 질의 기반 논문 근거 발췌기

현재 **v1의 P1–P5 기능과 P6 자동 회귀·커버리지 검사**가 구현되어 있다. 실제 논문의 P2·P3 인수 시험과 실제 모델 선택·사람 검토는 대기 중이다. 사용자가 구현을 먼저 완료한 뒤 verify와 함께 실데이터 검증하기로 순서를 변경했다. 인수 완료와 구현 완료를 구별한다. Python 3.9 stdlib로 실행하며 Codex·Claude 모두 같은 CLI를 사용한다.

```sh
runner/evidence-extract check --query extract/config/queries/gold-kv-reuse.json
```

`check`는 질의 계약, 7개 게이트 항목, verify의 `paragraph_unit.split == blank_line_block`을 검사한다. 성공하면 JSON으로 질의·게이트·게이트 파일 SHA-256을 출력한다. `confirmed_by`가 없는 질의는 `unconfirmed: true`로 표시한다. 이는 발췌 전 입력 검사이며 질의 승인이나 논문 검증 완료를 뜻하지 않는다.

`EXTRACT_THRESHOLDS_PATH`로 검사할 verify 임계 파일을 지정할 수 있다. 기본값은 `verify/config/thresholds.json`이다. 입력 검사는 원장·결과 파일을 생성하지 않는다.

## P2 라이브러리

`textlayer.extract_raw(Path(pdf), codex_raw=reference_text)`는 로컬 `pdftotext` 기본 모드로 추출하며 PDF·텍스트 SHA-256, Poppler 버전, 대조 결과를 반환한다. Poppler 실행 파일은 시스템에 있어야 한다. Python 패키지는 추가하지 않는다. 스캔 PDF의 빈 텍스트 층은 실패하며 OCR은 하지 않는다.

```sh
PYTHONPATH=extract:verify python3 -S - /absolute/path/paper.pdf <<'PYTHON'
from pathlib import Path
import sys
from extract.textlayer import extract_raw
from extract.pipeline import segment_text
raw, metadata = extract_raw(Path(sys.argv[1]))
result = segment_text(raw)
print(metadata)
print({"전체": len(result["segments"]), "표시": len(result["kept"]),
       "제거": result["removed_by_reason"]})
PYTHON
```

- `pipeline.segment_text`는 문단 계약을 먼저 검사하고 verify 문단 번호를 유지한다. 결과는 dataclass를 포함한 Python 객체이며 아직 P4a의 `segments.json` 형식은 아니다.
- 세그먼트의 `char_start`·`char_end`는 원문 Unicode 문자 인덱스(끝 제외)다. 문장 뒤 공백도 보존하므로 세그먼트를 이어 붙이면 원래 블록이 복원된다. `first_diff`만 UTF-8 **바이트** 인덱스다. `diff_lines`는 줄 변경 구간별 양쪽 줄 수 중 큰 값의 합이다.
- 제목은 계획의 세 규칙으로 감지한다. 한 블록에 여러 제목이 있으면 모두 목록에 기록하고 마지막 제목을 해당 블록에 붙인다.
- 참고문헌은 첫 줄이 References인 블록부터 끝까지 제거 분류한다. 반복 머리말은 여러 페이지의 첫 두 블록 위치에 있는 동일한 짧은 블록(30낱말·2줄 이하)만 후보로 삼는다. 이는 보수적 휴리스틱이며 gold 문서 검증 전이다.
- `arxiv_stamp`를 인수로 전달하면 해당 독립 블록만 제거한다. 생략 시 독립 arXiv 식별자 형식을 감지한다. 본문에 섞인 표시는 남기고 `boundary_warnings`에 기록한다. 표를 별도로 제거하지 않으며, 제거 세그먼트도 사유와 함께 반환한다.
- 블록 안쪽에 페이지 구분자가 끼어 verify의 줄바꿈 정규화가 인용을 바꾸는 경우에는 오류로 중단한다. 원문의 내용이나 세그먼트 번호를 고치지 않는다.

합성 PDF의 실제 Poppler 실행, 약어·소수·지수, 제목·페이지, 반복 문자열 위치, 제거 회계와 오류 처리는 `tests/test_extract_segments.py`로 검증한다. 고정 제목 21행은 원본 계획의 값을 그대로 보존했다. 원본 자료가 준비되면 다음 시험이 PDF 해시·텍스트 일치·제목 21개·페이지·문단 복원을 확인한다.

```sh
KVCPOOL=/absolute/path/kvcpool-trace-gen python3 -S -m unittest discover -s tests -p test_extract_segments.py -v
```

`KVCPOOL`이 없으면 gold 시험은 명시적으로 skip되며 P2 인수 완료를 뜻하지 않는다. 설정했는데 파일이나 결과가 다르면 실패한다.

## P3 인용 연결

`pipeline.prepare_segments`는 P2의 전체·제거·표시 전 세그먼트를 유지하고, 연결 후 `displayed`를 추가한다. 앞 문단의 미완결 끝 조각과 다음 본문 블록(20낱말 이상)의 첫 조각을 ` […] `로 잇는다. 번호·제목 경계를 넘지 않으며 캡션과 숫자 중심 표를 건너뛴다. 본문 후보는 절반 넘는 낱말에 문자가 있어야 한다. 이는 텍스트 기반 휴리스틱이며 일반적인 표·머리말 분류를 보장하지 않는다.

연결된 세그먼트는 첫 조각의 ID·페이지·절을 유지한다. `char_start`·`char_end`도 첫 조각의 범위이며, 전체 인용의 위치는 `fragments`의 원문별 범위를 사용한다. `resolved_para_ids`에는 두 문단이 들어간다. 소비된 뒤 조각은 다시 표시하거나 다른 인용에 재사용하지 않는다. 전체 원본 수는 `kept + removed`, 연결 후 표시 수는 `kept - spanning.formed`로 대조한다.

L1은 verify의 `Variant`·`check_quote`를 호출한다. 목록의 기호 조각도 보존하며 등급을 측정한다. **선택되어 레코드로 만들어지는 인용**은 모두 exact여야 한다. 원장 연결·등록·waiver는 수행하지 않는다. verify 모듈이 내부적으로 원장 모듈을 import하지만 extract는 원장 API를 호출하지 않는다.

## v1 실행

```sh
runner/evidence-extract segment \
  --query extract/config/queries/gold-kv-reuse.json \
  --slug workload__year-in-llm-serving \
  --source-root /absolute/path/kvcpool-trace-gen
```

직접 PDF를 지정하려면 `--source-root` 대신 `--pdf /absolute/path/paper.pdf`를 사용한다. 선택적으로 `--title "논문 제목"`, `--codex-raw FILE`, `--arxiv-stamp TEXT`, `--out-dir DIR`를 줄 수 있다. 제목을 생략하면 slug를 표시한다. `--source-root`를 주면 verify의 `sources.json`에 설정된 네 텍스트 변형을 찾아 실행 폴더에 복사하고 각 SHA-256을 봉인한다. 직접 PDF와 `--source-root`를 함께 지정해도 된다. `build`는 봉인된 사본만 읽으며, 없는 변형은 `unavailable`로 보고한다. 기본 출력 위치는 `extract/results/<query_id>/<run_id>/`이며 실행 ID는 날짜 없이 생성된다. 모든 표시 세그먼트를 한 파일에 담고 SHA-256을 함께 쓴다.

출력된 `workfile`과 [선택 지침](SELECTION.md)을 Codex 또는 Claude 세션에 전달하고, 출력된 `selections` 경로에 선택 JSONL을 작성한다. 모델이 문장을 받아 적지 않으며 코드가 원문을 복사한다.

```sh
runner/evidence-extract build \
  --query extract/config/queries/gold-kv-reuse.json \
  --slug workload__year-in-llm-serving \
  --workfile /absolute/path/workload__year-in-llm-serving.segments.json \
  --selections /absolute/path/workload__year-in-llm-serving.selections.jsonl \
  --agent codex --model 실제모델명
```

Claude는 `--agent claude`를 사용한다. `.records.jsonl`, 한국어 메모의 `.md`, `.run.json`, `slice-facts-<run_id>.json`을 같은 실행 폴더에 쓴다. 질의·게이트·세그먼트 봉인·원문 해시를 검사하고 선택 파일 한 줄이라도 틀리면 전체를 거부한다. 성공 결과는 덮어쓰지 않으므로 새 선택 실험은 새 `segment` 실행으로 시작한다.

`--gold PATH`는 verify의 handpicked 형식 파일을 받는다. 지정 논문 slug에서는 반입된 gold 파일이 기본값이다. 그 밖의 논문은 gold 미지정 시 회수율을 unavailable로 보고한다. codex_raw 등급과 G 블록 회수율은 보고 전용이며 통과를 막지 않는다. 보고서는 최종 계약의 26개 필수 키와 부가 진단을 포함한다. `stage: v1`, `acceptance: pending_real_data`를 기록하며, 미확인 질의는 `query.unconfirmed: true`다. 변형별 비정확 행·텍스트 층 뒤섞임 의심·짧은 문장·반복 문장 목록은 보고용이다. 원천 L1 exact 실패나 문단 위치 불일치는 빌드를 중단한다.

새 스킬·심볼릭 링크를 만드는 원본 계획 부분은 루트 규칙에 따라 공통 문서로 대체했다. 에이전트 식별자는 `codex-session:<model>` 또는 `claude-session:<model>`이다. Python 3.10·PyYAML·pytest 필수 구성은 Python 3.9·JSON·unittest로 대체한다.

## 최종 계약과 재현

- 선택 파일은 한 줄이라도 잘못되면 전체 거부한다. `unknown_id`, `removed_id`, `duplicate_id`, `invalid_kind`, `invalid_memo`, `unexpected_field`를 구별한다. JSON/필수 필드/경계 표지 형식 오류는 `invalid_format`이다. 첫 위반 행·사유를 `.selections.jsonl.rej-N.log`에 남기며 이전 기록을 덮어쓰지 않는다.
- 메모는 비어 있지 않은 한 줄이어야 한다. 한국어 여부와 의미 충실성은 모델·사람 검토 대상이다. `boundary_flag: true`에는 비어 있지 않은 `boundary_reason`이 필요하다.
- 레코드는 질의·제목·인용 조각·조각별 페이지를 함께 보존한다. 다이제스트는 문서 순서로 정렬하고, 연결 위치에 `⏎p.N`을 표시한다. 원문 자체의 `[…]`는 바꾸지 않는다. 조건 5필드는 `unextracted`, 수치는 빈 배열이며 v1의 의도된 범위다.
- 0건 선택도 정상 실행이다. 빈 JSONL에는 질의 메타데이터를 담을 행이 없으므로 빈 다이제스트 재생성에는 봉인 작업 파일과 실행 에이전트 정보가 필요하다.
- 전체 수는 `total = kept_before_spanning + sum(removed_by_reason)`이고, `displayed = kept_before_spanning - spanning.formed`다. 본문 낱말 수는 연결 전 표시 대상 원문 기준으로 세므로 생성된 `[…]`를 토큰 추정에 더하지 않는다.
- `codex_raw`가 같을 때만 블록 번호·텍스트 대응을 검사한다. 다르면 바이트 첫 차이·줄 차이를 보고하고 대응 등록을 sync 단계로 남긴다. 원장에 등록된 실제 행과의 대조는 실데이터 검증에서 한다.
- 성공 산출물은 덮어쓰지 않는다. 파일마다 원자적으로 기록하지만 실행 폴더 전체의 트랜잭션은 아니다. 쓰기 도중 중단되어 일부 산출물만 남았다면 새 `segment` 실행으로 재시도한다.

선택이 있는 JSONL에서 같은 발췌집을 재생성한다.

```sh
PYTHONPATH=extract:verify python3 -S - path/to/paper.records.jsonl <<'PYTHON'
import json
import sys
from pathlib import Path
from extract.digest_min import render
records = [json.loads(line) for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()]
print(render(records), end="")
PYTHON
```

## 자동 검사와 남은 인수

```sh
python3 -S scripts/check-extract
scripts/check
```

`check-extract`는 단위·합성 통합 테스트와 표준 라이브러리 `trace` 실행 가능 줄 커버리지 80% 게이트를 실행한다. 추가 Python 패키지는 필요 없다. 이 측정은 coverage.py 측정과 구분한다. 실데이터가 없어서 skip된 테스트는 통과로 세지 않는다.

1. `KVCPOOL` 원본 자료로 P2·P3 gold 시험을 생략 없이 통과시킨다.
2. 실제 논문 전체 세그먼트를 Codex 또는 Claude가 읽고 선택 파일을 작성한다.
3. 최종 보고서의 세그먼트·선택·L1·변형 대조·G 회수율과 발췌집을 사람이 검토한다.
4. verify의 실제 자료 검사와 함께 결과를 대조한다. 원장 변환기·`extract_raw` 등록·`unextracted` 해석은 별도 sync 범위이며 현재 JSONL을 `ledger import`에 직접 넣을 수 없다.

구현·검증 범위와 남은 절차: [완료 기록](docs/v1-implementation.md). 합성 결과를 실제 모델 측정이나 사람 승인으로 대신 기록하지 않는다. 원본 계획의 인수 체크박스는 아직 미완료 상태를 유지한다. inbox 배치·API 호출·조건/수치 추출은 v1 이후 범위다.

원본: [계획](plans/ralplan-paper-evidence-extractor.md), [스펙](spec/deep-interview-paper-evidence-extractor.md). 공통 에이전트 사용법: [verify/USAGE.md](../verify/USAGE.md).
