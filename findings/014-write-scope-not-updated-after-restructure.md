# 014 — 디렉토리를 옮기고 write_scope 를 갱신하지 않아 밤이 산출물 0 으로 '통과' 했다

- **발견** — 2026-08-31 12:15, athena-research night-006. 패널 리뷰 리프 5개가 전부 `passed` 인데 `projects/kvcache-cmx/reviews/` 가 비어 있었다. 밤의 모델이 원인을 `docs/findings/night-006-task-035-write-scope.md` 에 정확히 남겨 두었다(거부 메시지·원인·"검증기 자체는 통과한다" 까지).
- **증상** — 같은 날 오전의 멀티 주제 재구성(산출물을 `projects/<slug>/` 로 이동)에서 `domain.json write_scope` 를 옛 목록(`ideas·docs·paper·src·tests·experiments·references.bib`)으로 두었다. 훅이 `projects/**` 쓰기를 전부 거부했고(Write·Bash 리다이렉션 양쪽), 리프의 검증기 `lab.review check --dir …/reviews` 는 리뷰가 **0편이어도** "문제 0" 으로 exit 0 이라 판정이 통과였다.
- **피해** — 밤 하나(6리프, 약 35분)가 산출물 없이 지나갔다. 트리 손상 없음. 리프는 `passed` 로 로그에 남아(I2·I3) 되돌릴 수 없어 새 id 로 재시도했다.
- **원인** — 둘이 겹쳤다. (a) `write_scope` 는 코드가 아니라 **계약**이라 테스트·검증기가 안 잡는다 — 디렉토리 구조를 바꾸는 작업의 체크리스트에 없었다. (b) 산출물을 만드는 리프의 검증기가 **부재를 통과**시켰다. P6("판정은 검증기가")의 사각지대: 검증기가 빈 결과를 통과시키면 판정 자체가 무의미하다.
- **해소** — (a) `night` preflight 가 `write_scope`·`human_scope` 중 트리에 없는 경로를 경고한다(`test_preflight_warns_about_scope_paths_missing_from_tree`). (b) `lab.review --expect <파일…>` 로 있어야 할 산출물을 요구하고, 리뷰 리프 검증기 전부에 붙였다(athena-research, 테스트 +2). (c) research `write_scope` = `projects·src·tests·docs`.
- **재발 방지** — **산출물을 만드는 리프의 검증기는 존재를 요구해야 한다**(`--expect`·`test -f`·verify-doc 에 경로 지정). 빈 결과를 통과시키는 검증기는 검증기가 아니다. 구조 변경 시 `domain.json` 갱신은 이제 preflight 경고가 상기시킨다.
- **가정 변경** — ASSUMPTIONS "검증기는 부재를 통과시키면 안 된다" 행 추가.
