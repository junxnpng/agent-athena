# 질의 기반 논문 근거 발췌기

현재 **P1 사전 검사, P2 텍스트·세그먼트, P3 인용 연결, P4a 파일 왕복 프로토타입**이 구현되어 있다. 지정 논문의 P2·P3 인수 시험과 P4a 실제 모델 측정·사람 결정 게이트는 미완료다. Python 3.9 stdlib로 실행하며 Codex·Claude 모두 같은 CLI를 사용한다.

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

## P4a 프로토타입 실행

```sh
runner/evidence-extract segment \
  --query extract/config/queries/gold-kv-reuse.json \
  --slug workload__year-in-llm-serving \
  --source-root /absolute/path/kvcpool-trace-gen
```

직접 PDF를 지정하려면 `--source-root` 대신 `--pdf /absolute/path/paper.pdf`를 사용한다. 선택적으로 `--codex-raw FILE`, `--arxiv-stamp TEXT`, `--out-dir DIR`를 줄 수 있다. 기본 출력 위치는 `extract/results/<query_id>/<run_id>/`이며 실행 ID는 날짜 없이 생성된다. 모든 표시 세그먼트를 한 파일에 담고 SHA-256을 함께 쓴다.

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

`--gold PATH`는 verify의 handpicked 형식 파일을 받는다. 지정 논문 slug에서는 반입된 gold 파일이 기본값이다. 그 밖의 논문은 gold 미지정 시 회수율을 unavailable로 보고한다. codex_raw 등급과 G 블록 회수율은 보고 전용이며 통과를 막지 않는다. P4a의 보고서는 아직 P4b의 26키 최종 보고 형식이 아니다.

새 스킬·심볼릭 링크를 만드는 원본 계획 부분은 루트 규칙에 따라 공통 문서로 대체했다. 에이전트 식별자는 `codex-session:<model>` 또는 `claude-session:<model>`이다. Python 3.10·PyYAML·pytest 필수 구성은 Python 3.9·JSON·unittest로 대체한다.

## 남은 인수 절차

1. `KVCPOOL` 원본 자료로 P2·P3 gold 시험을 생략 없이 통과시킨다.
2. 실제 논문 전체 세그먼트를 현재 Codex 또는 Claude 모델이 읽고 선택 파일을 작성한다.
3. P4a의 다섯 측정값(세그먼트·선택·L1·변형 대조·G 회수율)을 검토하고 사람 결정 게이트를 기록한다.
4. 그 뒤 P4b의 최종 계약·보고서, P5 교차 대조, P6 커버리지를 진행한다.

합성 테스트 결과를 실제 논문 측정이나 사람 승인으로 대신 기록하지 않는다. 테스트는 루트 `tests/test_evidence_extract.py`와 `tests/test_extract_*.py`이며 `scripts/check`에 포함된다. 원본 계획의 체크박스는 아직 인수 미완료 상태를 유지한다.

원본: [계획](plans/ralplan-paper-evidence-extractor.md), [스펙](spec/deep-interview-paper-evidence-extractor.md). 공통 에이전트 사용법: [verify/USAGE.md](../verify/USAGE.md).
