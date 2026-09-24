# 질의 기반 논문 근거 발췌기

현재 **P1 사전 검사와 P2 텍스트·문단·세그먼트 라이브러리**가 구현되어 있다. P2의 지정 논문 인수 시험은 원본 PDF·대조 텍스트가 없어 미완료다. Python 3.9 stdlib로 실행하며 Codex·Claude 모두 같은 CLI를 사용한다.

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

## 다음 구현

 P3는 여러 문단에 걸친 인용 연결, P4a는 첫 실제 논문 실험과 사람 결정 게이트다. `segment`·`build` 명령, 에이전트 선택 파일, 다이제스트는 아직 구현되지 않았다.

이 저장소에서는 원본 계획의 Python 3.10·PyYAML·pytest 필수 구성을 Python 3.9·JSON·unittest로 대체한다. 테스트는 루트 `tests/test_evidence_extract.py`·`tests/test_extract_segments.py`이며 `scripts/check`에 포함된다. 원본 계획은 이전 환경의 기준을 보존하므로 실제 진행 현황은 이 문서를 따른다.

원본: [계획](plans/ralplan-paper-evidence-extractor.md), [스펙](spec/deep-interview-paper-evidence-extractor.md). 공통 에이전트 사용법: [verify/USAGE.md](../verify/USAGE.md).
