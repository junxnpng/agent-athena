# 근거 검증 이식과 발췌기 착수 계획

목표: AI-helper의 구현된 verify를 Python 3.9 stdlib 환경으로 이식하고 Codex·Claude가 같은 파일 왕복 계약으로 사용하게 한다. 검증 후 extract P1을 구현한다.

기준: `verify/plans/ralplan-verification-system.md`, `extract/plans/ralplan-paper-evidence-extractor.md`, 루트 AGENTS.md. 원본의 미완료 verify P6·P7과 extract P2 이후를 완료로 간주하지 않는다.

## 제약

- 실행 코드는 Python 3.9 stdlib, 외부 의존성 추가 없음. 셸은 POSIX.
- 동기화 원본은 읽기 전용으로 취급한다. 기존 반입 자료가 있는 현재 작업 공간에서 순차 변경한다.
- 커밋·push·새 모델 런타임·외부 통신은 수행하지 않는다.
- 원본 계획과 감사 결과는 역사 자료로 보존한다. 구성 형식 변경으로 과거 봉인 해시가 달라지므로 원본 원장을 새 실행 원장으로 사용하지 않는다.
- 새 스킬을 만들거나 미감사 원본 스킬을 전역 설치하지 않는다. 양쪽 에이전트가 읽는 공통 작업 문서와 CLI를 제공한다.

## 작업과 완료 근거

1. verify 구현·테스트·설정·판정 자료를 반입하고 파일 해시를 남긴다. 캐시와 재생성 SQLite 원장은 제외한다. 원본 테스트 결과를 기준선으로 확인한다.
2. 설정을 JSON으로 이식하고 Python 3.9에서 외부 패키지 없이 CLI가 동작하도록 한다. 원본 회귀 시험은 기존 설치된 pytest로 실행하고, 필수 검증은 stdlib unittest로 작성한다.
3. Codex·Claude 공통 실행 안내와 판정 입력 계약을 연결한다. 양쪽 verifier 식별자로 같은 export/import 검증을 통과하는지 검사한다. 특정 공급자의 사용량을 다른 공급자의 수치로 보고하지 않는다.
4. extract P1의 질의 로더·경로·7개 게이트·문단 분할 계약을 구현한다. 실패 입력과 정상 입력을 먼저 테스트하고 CLI까지 확인한다.
5. 반입 현황·가정·사용 설명을 갱신한다. `scripts/check`, verify 회귀 시험, site-packages 없는 실행 검증을 통과한 범위만 보고한다.

## 후속 P2

PDF 텍스트·출처 해시·문단 위치·세그먼트·제거 회계를 구현한다. 합성·경계 사례는 필수 검사로 검증하며, 지정 gold 자료가 없는 동안 원본 계획의 P2 완료와 P3 선행 조건 충족을 선언하지 않는다. 진행 현황과 실행 방법은 `extract/README.md`에 기록한다.
