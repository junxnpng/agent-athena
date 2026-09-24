# 근거 검증 시스템

AI-helper에서 구현된 P1–P5를 이식했다. 인용의 존재(L1), 질의 합치·인용 충실성(심판 파일 왕복), 조건·태그(L2), 산술(L6), 정답 세트 대비 재현율을 검사한다. P6 변이·인수 시험과 P7 최종 게이트는 아직 미구현이다.

**Codex·Claude 공통 사용 안내: [USAGE.md](USAGE.md)**

```sh
runner/evidence-verify --help
runner/evidence-verify schema --print-required
```

루트에서 실행하거나 진입점을 절대경로로 호출한다. Python 3.9 stdlib만 필요하다. 실행 설정은 `config/*.json`, 기본 실행 원장은 `results/verify-ledger.sqlite`다. 실제 검증에는 별도 논문 입력 저장소를 `KVCPOOL` 또는 `--source-root`로 지정해야 한다.

## 이식 자료

- `tools/verify/`: CLI와 검증 라이브러리.
- `tests/verify/`: 원본 회귀 시험을 JSON 계약에 맞춘 사본. 기존 pytest 환경에서 추가 회귀 검사할 때 사용한다.
- 루트 `tests/test_evidence_port.py`: stdlib 필수 이식 검사. `scripts/check`가 실행한다.
- `upstream/config/`, `upstream/results/`: 원본 YAML 설정과 판정 감사 기록. 현재 실행에서 자동 사용하지 않는다.
- `upstream-manifest.json`: 반입 원본 파일 SHA-256. 동기화 사본에는 git 메타데이터가 없어 커밋 식별자는 없다.
- `skills/claim-judge/SKILL.md`: 기존 판정 프로토콜 참조 문서. 전역 스킬로 설치하지 않는다.
- `plans/`, `spec/`, `docs/`, `refs/`, `gold/`, `reports/`: 원본 설계·연구·측정 기록. 과거 환경의 경로와 시험 결과를 포함한다.

기존 YAML의 내용은 JSON으로 전환했고 임계 프로토콜은 `v3-athena-json1`이다. 원본 YAML 해시로 봉인된 SQLite 원장은 반입하지 않았다. 실측값을 새 환경에서 재현한 것으로 간주하지 않는다.

## 검증

루트에서 `scripts/check`를 실행한다. pytest가 이미 설치된 개발 환경에서는 다음 추가 회귀 검사를 실행할 수 있다. 필수 실행 경로에는 pytest·PyYAML 의존성이 없다.

```sh
python3 -m pytest -p no:cacheprovider -c verify/pytest.ini verify/tests/verify -q
python3 -S -m unittest discover -s tests -p 'test_evidence_*.py' -q
```

Codex·Claude 판정 파일 호환성은 합성 데이터로 시험한다. 실제 모델의 판정 품질과 원본 논문 기반 시험은 별도 입력·실행이 필요하다.
