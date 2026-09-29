# Codex PostToolUse JSON 오류 수정

증상: `Hook failed — hook returned invalid post-tool-use JSON output`가 연속으로 표시됐다.

## 원인과 재현

이 repo의 harness는 SessionStart·PreToolUse만 등록한다. 문제를 재현한 코드는 Codex 캐시에 설치된 `security-guidance` 2.0.8의 `hooks/security_reminder_hook.py`다.

설치본의 `emit_metrics`에는 `PLUGIN_ROOT`가 있는 Codex 환경에서 Claude 전용 `metrics`·`rewakeSummary`를 제외하는 처리가 이미 있었다. 그러나 다음 두 분기는 이를 우회했다.

- Bash 훅 중복 실행: `{"metrics":{"bash_hook_dedup":true}}`를 직접 출력.
- 패턴 검사: `metrics`와 경고 문맥을 담은 객체를 직접 출력.

Codex의 [PostToolUse 출력 스키마](https://github.com/openai/codex/blob/main/codex-rs/hooks/schema/generated/post-tool-use.command.output.schema.json)는 `additionalProperties: false`이며 `metrics`·`rewakeSummary`를 허용하지 않는다. [공식 훅 문서](https://learn.chatgpt.com/docs/hooks)의 `PostToolUse` 계약에 따라 경고는 `hookSpecificOutput.additionalContext`로 전달한다.

원본 함수·중복 출력 구문을 AST로 읽어 네트워크/모델 호출 없이 실행한 결과, 공통 함수는 `{}`를 내지만 중복 구문은 금지된 `metrics` 필드를 냈다. 수정 후 실제 함수에서 중복 `{}`, 패턴 경고의 정상 이벤트 JSON, Stop의 `decision: block`·`reason` 보존을 확인했다.

Bash용 후처리 항목이 7개이므로 중복 경로가 반복 오류를 만드는 구조와 부합한다. 사용자가 본 여섯 메시지 각각을 런타임 로그의 특정 호출과 대응시키지는 못했다.

## 수정 및 재적용

`scripts/repair-codex-security-hook`는 두 직접 출력을 공통 `emit_metrics` 호출로 바꾼다. 공통 함수의 Codex 필터가 없는 알려진 원본에는 해당 필터도 추가한다. 경고·차단·검사 코드는 보존한다. 훅 비활성화, 신뢰 해시 수정, 설정의 제한 완화는 하지 않는다.

```sh
# 설치본 검사만 수행
python3 -S scripts/repair-codex-security-hook
# 백업 후 적용
python3 -S scripts/repair-codex-security-hook --apply
```

기본 대상은 `~/.codex/plugins/cache/claude-plugins-official/security-guidance/*/hooks/security_reminder_hook.py`다. 특정 설치본은 `--plugin-dir PATH`로 선택한다. Claude 설치본은 자동으로 수정하지 않는다. 필터는 `PLUGIN_ROOT`가 없는 환경에서 기존 telemetry 출력을 보존한다.

원본은 같은 폴더의 `security_reminder_hook.py.before-codex-json-fix`에 남긴다. 수정은 원자적으로 기록하고 실행 권한을 유지한다. 재실행은 무변경이다. 예상과 다른 upstream 코드나 충돌하는 백업을 만나면 수정을 거부하므로, 플러그인 업데이트 후에는 다시 검사해야 한다. 백업에서 복구하면 현재 수정이 사라진다.

## 검증

- 회귀: `python3 -S -m unittest discover -s tests -p test_codex_hook_repair.py`
- 전체: `scripts/check`
- 실제 설치본: `python3 -S scripts/repair-codex-security-hook`가 `이미 적용됨`을 출력해야 한다.

회귀 시험은 Codex/Claude 출력 차이, 경고 보존, 부분 수정본 보완, 백업·권한·멱등성, 알 수 없는 코드의 무변경 거부를 검사한다. 실제 모델 보안 리뷰를 새로 호출하지 않았으며, Codex UI에서 사용자가 보았던 모든 개별 실패를 재생한 시험은 아니다.
