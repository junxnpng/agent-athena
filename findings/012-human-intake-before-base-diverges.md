# 012 — human_scope 반입 커밋이 기점 확정 전에 일어나 다음 밤이 '분기'로 거부된다 (라운드 2 정확성 리뷰, High)

- **발견** — 2026-08-31, 라운드 2 정확성 리뷰. findings/009(human_scope 반입) 자신이 만든 회귀.
- **증상** — `preflight()` 가 `resolve_base()` 보다 먼저 돌아, 반입 커밋을 **현재 체크아웃된 브랜치**(보통 main)에 앉힌다. 시나리오: 밤 1 이 `harness/night-001` 에 끝나고 미병합 → 사람이 SUMMARY 안내대로 main 체크아웃 → 낮 스케줄러가 `inbox/` 에 파일 → 다음 밤 preflight 가 그걸 **main 에** 커밋 → 이제 main 에 night-001 에 없는 커밋이, night-001 에 main 에 없는 커밋이 있어 `resolve_base` 가 두 이력을 분기로 보고 `HarnessError("HEAD 와 … 가 분기했다")` → exit 2 → night-loop 가 사람 개입 필요로 멈춘다. findings/009 가 살리려던 예약 밤 패턴(예약 밤 + 사이의 사람 병합 + 스케줄러의 human_scope 쓰기)이 정확히 깨진다.
- **피해** — 관측 전 코드 리뷰로 잡음(예약 밤 launchd 는 일·수라 아직 이 순서를 안 밟았다).
- **원인** — 반입 커밋을 preflight(기점 확정 전)에 둔 것. "러너만 커밋한다" 는 지켰지만 *어느 브랜치에* 를 빠뜨렸다.
- **해소** — 반입을 `intake_human_scope()` 로 빼서 `resolve_base()`+`git.checkout(base)` **뒤에** 부른다 — 커밋이 기점(base) 브랜치 위에 앉아 밤 브랜치의 조상이 되고 분기가 안 생긴다. preflight 는 더 이상 dirty 를 커밋하지 않는다(clean 판정도 intake 로 이동). 테스트 `test_human_intake_on_unmerged_branch_does_not_diverge`.
- **재발 방지** — "커밋은 기점 확정 뒤에만": 트리를 바꾸는 preflight 단계는 브랜치가 정해진 뒤로. 잔여(보안 리뷰 R-lock, Medium): 반입 커밋이 lock 획득 전이라 동시 실행(수동+launchd) 시 git index.lock 경합으로 한쪽이 죽을 수 있다 — 손상은 아니고 재시도로 풀린다, 별도 처리 미룸.
- **가정 변경** — CONTEXT "human_scope 반입" 기록에 "기점 확정 뒤" 추가.
