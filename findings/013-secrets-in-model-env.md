# 013 — 부모 환경의 시크릿이 모델 세션으로 그대로 흘러간다 (보안 리뷰 R5, defense-in-depth)

- **발견** — 2026-08-31, 라운드 2 보안 리뷰.
- **증상** — `drivers.build_env` 가 `dict(os.environ)` 로 부모 환경을 통째 복사해 `claude -p`(`--dangerously-skip-permissions`, 무제한 Bash)에 넘긴다. 사람이 터미널에서 `night-detached` 를 띄웠고 그 셸이 `~/.config/my-secrets/tokens.env` 를 source 했거나 `.zshrc` 에 `GH_TOKEN`·클라우드 자격이 있으면, 모델이 `env`/`printenv` 로 읽어 write_scope 파일에 써넣고 `commit_all` 이 그걸 repo 이력에 커밋할 수 있다.
- **피해** — 현재 shipped launchd(night plist)는 tokens.env 를 source 하지 않아 트리거되지 않음. 사람의 수동 실행이 유일한 현 경로. 방어적 수정.
- **원인** — 신뢰 경계(모델은 신뢰 밖) 밖으로 나가는 env 에 allow/deny 리스트가 없었다.
- **해소** — `build_env` 가 이름에 TOKEN·SECRET·PASSWORD·CREDENTIAL·PRIVATE_KEY·`_KEY`·APIKEY 가 든 변수를 제외한다(`_is_secret`). `ANTHROPIC_*`(모델 호출에 필요)·`HARNESS_*`(러너가 다시 설정)는 예외. 테스트 `test_build_env_scrubs_secrets_keeps_anthropic`.
- **재발 방지** — 시크릿 이름 규칙은 완전하지 않다(임의 이름의 자격은 못 거른다) — allow-list 가 더 안전하나 모델이 필요로 하는 env 목록이 불확실해 deny-list 로 시작. tokens.env 를 쓰는 잡(daily·report)과 night 잡을 같은 plist 에 두지 않는 현 분리를 유지한다.
- **가정 변경** — ASSUMPTIONS "세션 환경 부산물" 행에 "시크릿 이름은 모델 세션 env 에서 제외" 추가.
