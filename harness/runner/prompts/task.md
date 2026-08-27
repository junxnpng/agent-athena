# 작업 {{task_id}} (시도 {{attempt}}/{{max_attempts}}) — {{title}}

밤 {{night_id}} · 시간 상한 {{timeout_minutes}}분 (초과 시 프로세스가 강제 종료된다) · 작업 디렉토리 `{{repo}}`

## 목표
{{goal}}

## 검증기 — 러너가 돌려서 판정한다. 끝내기 전에 직접 한 번 실행하라
- 이 작업: `{{verify_cmd}}`{{verify_threshold}}
- 전체 스모크: `{{global_verify}}`
- 둘 다 통과해야 커밋된다. 하나라도 실패하면 이 시도의 변경은 되돌려지고(패치는 보존) 다음 시도로 넘어간다.

## 쓰기 범위
{{write_scope}}

## 도메인 사양 (`.harness/spec.md`)
{{spec}}

## 특수 도구
{{tools}}

## 이전 시도
{{history}}

## 끝내는 법
1. 검증기를 직접 실행해 통과를 확인한다.
2. 커밋하지 않는다. `.harness/` 파일을 쓰지 않는다.
3. 마지막 줄: `RESULT: done|partial|blocked — 한 줄 이유`
