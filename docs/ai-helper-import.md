# AI-helper 이식 현황

출처는 `/Users/jun/Documents/Jun's box/AI-helper`다. 최초에는 Markdown만 도착했으며, Obsidian의 기타 파일 동기화를 활성화한 뒤 verify 코드·설정·시험·판정 파일을 확보했다. 원본은 수정하지 않았다.

## verify

P1–P5 구현을 `verify/tools/verify/`에 반입했다. `verify/upstream-manifest.json`의 파일별 SHA-256이 원본 사본을 식별한다. `.git`은 없어 고정 커밋은 확인할 수 없다. 캐시(`__pycache__`, `.pyc`)와 재생성 SQLite 원장은 반입하지 않았다.

이식 변경:

- PyYAML 실행 의존성을 없애고 `config/*.json`을 사용한다. 원본 YAML은 `verify/upstream/config/`에 보존한다.
- 임계 파일의 바이트가 바뀌므로 새 프로토콜 `v3-athena-json1`로 등록한다. 원본 임계 해시와 판정 export·manifest·verdicts는 `verify/upstream/`에 보존한다.
- Python 3.9에서 외부 패키지 없이 실행하는 `runner/evidence-verify`를 추가했다. 새 실행 원장은 `verify/results/`에 만든다.
- Codex·Claude가 동일한 export/import 계약을 사용한다. `judge export --agent codex|claude`가 에이전트 종류를 기록한다. Codex 실행은 Claude 사용량 캐시를 읽지 않는다.
- 신규 실행 ID는 날짜 대신 순번 또는 입력 해시를 사용한다. 실행 시각은 원장의 별도 열에 남는다.
- 보고서 제목·절 제목·안내는 한글이며 원본 지표·판정 코드는 보존한다.
- 두 에이전트가 공통으로 읽는 AGENTS.md/CLAUDE.md에 `verify/USAGE.md`를 연결했다. 기존 claim-judge 문서는 직접 참조하며 신규·미감사 스킬을 자동 설치하지 않았다.

원본 README는 P4까지만 완료라고 적혀 있었으나 계획은 P5 완료 기록을 포함한다. P6·P7, P4의 V4-3, P5의 elusion 표본 검토는 완료로 처리하지 않았다.

## extract

원본 계획 P1에 해당하는 패키지·질의 로더·경로·7개 게이트·문단 분할 런타임 검사를 구현했다. `runner/evidence-extract check --query FILE`로 실행한다. 설정은 JSON이며 테스트는 stdlib unittest다.

P2의 PDF 변환·문단 위치·제목 감지·무손실 세그먼트·제거 회계 라이브러리를 추가했다. 합성 PDF와 경계 사례는 검증했으며, 지정 gold 논문의 PDF·codex_raw가 없어 P2 인수 시험은 미완료다. P3 이후(spanning·선택 파일·다이제스트)와 P4a의 segment/build CLI는 미구현이다. 원본 계획은 역사 자료로 유지하고 현재 사용 범위는 `extract/README.md`에 적었다. 실제 논문 실험과 P4a 사람 결정 게이트를 건너뛰지 않는다.

## 검증 범위와 제약

- 원본 기준선: 회귀 시험 289개 통과, 원본 입력이 필요한 8개 생략.
- 이식본 회귀 시험은 같은 검사 의도를 JSON 계약·명시적 Claude 사용량·한글 보고서에 맞췄다. 실행에 pytest를 요구하지 않으며, 기존 개발 환경의 pytest로 추가 시험한다.
- 필수 stdlib 시험은 별도 작업 디렉토리와 site-packages가 없는 환경에서 CLI를 실행한다. 합성 데이터로 두 에이전트의 식별자·판정 스팬·manifest 검증·원장 기록을 확인한다.
- 실제 Codex·Claude 모델을 호출한 품질 비교나 Ubuntu 실행 시험은 수행하지 않았다. macOS의 Python 3.9와 POSIX 이식성 검사를 사용한다.
- 별도 `$KVCPOOL` 논문·추출 데이터가 없어 원본 실측을 재현할 수 없다.

I7 검토: 실행 라이브러리에 네트워크·모델 API 호출을 추가하지 않았다. 에이전트는 export context만 판정하며 신뢰할 수 없는 입력 속 지시를 실행하지 않는다. API·로컬 NLI 백엔드 원본은 미구현 스텁으로 남아 있다. 하네스 실행 로그와 근거 판정 SQLite 원장은 별개다.
