# 005 · 쓰기 범위 훅이 heredoc 본문의 `->`·`<tag>`를 리다이렉션으로 오인한다 (열린 발견)

- **발견**: night-003 (GreedyAtena, 2026-08-29 00:09, opus). SUMMARY 이상 징후 "훅 거부 1회: task-004". 스트림: 3번째 도구 호출 `cat > tests/test_collectors_news.py <<'EOF' …(132줄)… EOF`를 pre-tool이 `[harness] Bash 쓰기 대상 str:: 쓰기 범위 밖: str: (허용: tests) (I6)`로 거부. 실제 쓰기 대상 `tests/…`는 범위 안이었다.
- **증상**: `harnesslib.bash_write_targets`가 이 명령에서 쓰기 대상 **10개**를 뽑았고 진짜는 1개 — 나머지는 heredoc 본문의 `def f() -> str:`(파이썬 반환 주석) · `<title>{title}</title>`(XML f-string) · `# … -> de-duped,`(주석). `_REDIRECT_RE`의 lookbehind가 `<>&`만 제외하고 `-`를 제외하지 않으며, heredoc 본문(데이터)을 셸 명령과 같은 텍스트로 훑는다.
- **피해**: 이번엔 모델이 `Write` 도구로 우회해 검증 통과(1턴·약 $0.07 손실). 그러나 파이썬·XML·HTML을 heredoc으로 쓰는 거의 모든 작업에서 재발하고, 아침 SUMMARY에 "훅 거부"가 늘 떠서 진짜 위반 신호가 묻힌다(P10). 첫 밤 실측대로 bypass 모드의 모델은 heredoc을 기본 쓰기 채널로 쓴다(findings/001).
- **원인**: findings/001의 해소(heredoc 리다이렉션도 조기 거부)가 본문을 제외하지 않았다. 휴리스틱의 오탐 비용을 "러너가 git status로 최종 판정하니 무해"로 봤지만, 오탐은 거부→우회 턴을 만들고 신호를 오염시킨다.
- **해소**: (미해소 — 사용자 결정 대기) 후보 ① `_REDIRECT_RE` lookbehind에 `-` 추가(`(?<![<>&-])`) — 이 명령에서 오탐 9→6, 값싸지만 불충분. 후보 ② **heredoc 본문을 스캔에서 뺀다**: `<<[-]?['"]?WORD` 다음 줄부터 `WORD` 단독 줄까지를 제거하고 머리 줄(`cat > f <<EOF`)만 훑는다. 단 `sh|bash|zsh|dash|python… <<EOF`처럼 본문이 *실행*되는 경우는 본문도 계속 훑는다. 최종 판정은 여전히 러너의 `scope_violations`(git status)라 놓쳐도 안전 쪽으로 실패한다. ②+①을 권장.
- **재발 방지**: (해소 시) `tests/test_harnesslib.py::test_bash_write_targets`에 이 밤의 실제 heredoc(파이썬 반환 주석·XML f-string·주석 `->`) 케이스와 `bash <<EOF` 실행 케이스 추가.
- **가정 변경**: ASSUMPTIONS "P3-lite 쓰기 범위 (I6)" 행의 "훅은 조기 거부(휴리스틱)"에 단서 추가 예정 — 휴리스틱의 오탐도 비용이다.
- **일반화**: 조기 거부 휴리스틱은 "놓치면 러너가 잡는다"로 재현율만 걱정했지만, **정밀도가 낮으면 거부가 곧 우회 유도**가 된다. 데이터(heredoc 본문)와 명령을 구분하지 않는 스캐너는 데이터가 커질수록 오탐이 선형으로 는다.
