# 2026-10-21 (10) mcp-shutdown 티켓 02: 경계의 예외

브랜치 `feature/02-boundary-exceptions`, 워크트리 `.claude/worktrees/02-boundary-exceptions`. 티켓은 `.scratch/mcp-shutdown/issues/02-boundary-exceptions.md`. 03(`feature/03-posix-launcher`)과 나란히 돈다.

> 사용자: "`.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/mcp-shutdown/issues/02-boundary-exceptions.md" (지시문: 이번 요청 범위는 PR과 병합까지)

## 체크아웃 정리

`tidy-checkouts`가 루트를 `c2c2105f`에서 `5040230c`(origin/main)로 당겼다. 쉬는 세션의 프로세스만 쥔 워크트리 둘(`mcp-shutdown-to-tickets`, `morning-report-followup`)을 `end-holders`로 풀고 그 워크트리와 브랜치를 지웠다. 나머지는 실행 중인 세션, 병합된 PR 없음, 쥔 프로세스, 앱의 표지로 남겼고 사람에게 넘길 것은 없었다.

## 구현

- **여는 함수의 꼴.** 01의 `_session(stack, server)`과 시제품의 `_open(stack, name, server)`는 탈출 스택을 받아 거기에 등록하는 출력 인자 꼴이었다(PR #337 claude-review Nit). 서버마다 `@asynccontextmanager` 하나(`_opened`)를 두는 꼴을 골랐다. 그 안에서 서버를 띄우는 `_session`(세션과 도구 목록을 내주는 문맥)에 들어가고, 이 서버의 태스크 그룹 두 겹을 지나 나온 그룹을 그 자리에서 벗긴다. 그래서 `connect`는 연 순서대로 `_opened`를 탈출 스택에 넣기만 하고 예외를 기억하지 않는다. 겉봉을 벗기는 넷이 이 꼴에서 초록이라 생성기를 한 겹 더 지나는 것이 문제가 되지 않았다. 첫 판은 `_opened` 한 함수에 여는 단계를 다 넣었다가 ruff의 try 문 규칙(PLW0717, 11 > 5)에 걸려 `_connecting`(여는 동안의 예외를 `ConnectionError`로 바꾸는 문맥)과 `_session`으로 나눴다.
- **원인(`__cause__`).** 세션을 연 뒤의 실패(`python -c pass`의 `MCPError: Connection closed`)는 `_session`의 태스크 그룹에 싸인 그룹이 `_connecting`에 닿아, 원인이 그 그룹이고 글은 그룹을 펼친 것이다. 없는 명령의 원인은 `FileNotFoundError` 그대로다. 시제품은 그룹 안쪽에서 바꿔 원인이 잎이었다. 티켓의 "원인의 글은 예외 그룹을 펼친 것이다"와 맞아 이대로 두었다.
- **도구 호출.** 세션의 `call_tool`이 낸 예외를 서버와 도구를 든 `RuntimeError`로 바꾼다. `_Route`가 서버 이름을 든다.

## 빨강을 먼저 본 것

테스트를 먼저 고치고 01의 어댑터로 돌렸다. 7 failed, 8 passed. 겉봉을 보는 넷(사례 3, 뜨자마자 끝나는 서버, 던진 예외 그룹, yield에 멈춘 제너레이터)은 `--tb=line`에서 그룹의 글로 빨갰다(`[single exception in ExceptionGroup]`의 `MCPError: Connection closed`, 두 겹 그룹의 `is` 단언, `[single exception in BaseExceptionGroup]`의 `GeneratorExit`). 기동 실패는 `FileNotFoundError`, 1000쪽과 사례 4는 바뀌지 않은 타입으로 빨갰다. 구현 뒤 15 passed(56.8초).

## 소비 지점

`write_failure.py --expect closed`가 네 사례 모두 측정이고 기대대로였다. 대조군으로 어댑터만 origin/main의 것으로 바꾼 트리에서 `--expect escaped`가 쓰기 사례 둘의 `BaseExceptionGroup`으로 기대대로였다. 결과는 프로브 README의 "2026-10-21 결과 — 티켓 02의 소비 지점".

## 문서

`.claude/rules/adapters.md`에 경계의 예외 셋을 한 항목으로, `ToolSource` 독스트링에 연결이 안의 예외를 바꾸지 않는다는 한 줄을, 어댑터 모듈 독스트링에 경계의 예외 문단을 더했다. 잔존: 서버 기동 실패를 `FileNotFoundError`로, 뜨자마자 죽는 서버를 두 겹 그룹으로 적은 살아 있는 문장은 고친 테스트 둘 밖에 없었다(`src`, `tests`, `.claude`, 헌법, 루트 문서를 `FileNotFoundError|두 겹|ExceptionGroup|기동 실패|뜨자마자|Connection closed|예외 그룹`으로 찾았다). core와 채널의 가짜 포트 `BrokenTools`는 이미 `ConnectionError`다.

## 검사 (셀프 리뷰 전)

- `uv run ruff check .`와 `uv run ruff format --check .`: 통과(889 files).
- `uv run python tools/run_checks.py`: zizmor, lint-imports, check-instructions, check-type-escapes, pyright(59.2초), run-hooks(191.9초), pytest(403.8초)가 Passed까지 찍혔다. 그 뒤 인계 절차가 그 백그라운드 작업을 멈춰 나머지(web 등)의 결과는 없다. 새 세션이 셀프 리뷰를 반영한 뒤 다시 돈다.
- 아직 돌리지 않은 것: `uv run --env-file ../../../.env pytest -m llm`(어댑터를 건드렸다), 카나리아 둘(`tools/sibling_overlap.py`가 `adapters.md` 변경으로 `adapters_rule_new_optional_fields.toml`을 짚었고, 새 항목을 묻는 `.scratch/mcp-shutdown/probes/canary/adapters_rule_boundary_exceptions.toml`을 더했다. 사전 확인 `--preflight`는 둘 다 통과).
- `tools/sibling_overlap.py`가 일지 07을 10으로 옮겼다(`ticket-for-every-pr-to-tickets` 워크트리가 07을 썼다). 03(PR #338)이 `src/agent_os/adapters/mcp.py`와 `tests/adapters/test_mcp.py`를 함께 고친다. 뒤에 병합되는 쪽이 합친다.

## 인계

셀프 리뷰 직전에 컨텍스트가 인계 문턱을 넘어 인계 계기가 왔다. 이 세션의 제목은 `feature/02-boundary-exceptions`였고 `feature/02-boundary-exceptions (인계함)`으로 바꾼다. 커밋하지 않은 변경이 워크트리에 있다.

지시문:

```
다음 작업: .scratch/mcp-shutdown/issues/02-boundary-exceptions.md. run_failed가 어느 MCP 서버가 무엇 때문에 실패했는지 말하고, 어댑터의 예외가 내장 타입으로 포트를 넘으며, 결말을 쓴 실행은 그것으로 끝난다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/mcp-shutdown/issues/02-boundary-exceptions.md
브랜치: feature/02-boundary-exceptions
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-21-10-boundary-exceptions.md(구현, 빨강, 소비 지점, 검사, 인계 절), .scratch/mcp-shutdown/issues/03-posix-launcher.md(나란히 도는 형제, PR #338)
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 기점 origin/main)부터 한다. 티켓의 어댑터·테스트·문서 체크박스는 구현했고 체크 표시는 아직 하지 않았다. 남은 것: 셀프 리뷰 반영, run_checks 전체 다시(앞 회차는 pytest까지 Passed를 찍고 인계로 멈췄다), -m llm, 카나리아 둘(adapters_rule_new_optional_fields.toml과 새 adapters_rule_boundary_exceptions.toml의 최신 결과 줄), 티켓 체크 표시, 병합 직전의 기능 닫기 판정(03의 Status). 일지 docs/journal/2026-10-21-10-boundary-exceptions.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-21T09:59:00Z

## 셀프 리뷰 (새 세션, 기점 `5040230c`)

> 사용자: (next-session 지시문) "이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 기점 origin/main)부터 한다."

범위: 바뀐 파일 5, 커밋 0, 미추적 2(카나리아 명세, 이 일지). 두 축 모두 Critical·Major 없음. 표준 축은 Minor 5·Nit 5, 명세 축은 Minor 3·Nit 1. 두 축 모두 `write_failure.py`의 `--expect closed`와 대조군 `--expect escaped`를 다시 돌려 README와 같았다.

- 고친 것
  - 닫힌 주장(두 축). `adapters.md`의 "나가는 예외는 내장 타입이고 mcp의 타입은 포트를 넘지 않는다 … 셋이다"에 반례가 셋이었다(`LookupError`, `__cause__`의 mcp 그룹과 `MCPError`, 닫기가 실패해 그대로 내는 그룹). 고친 문장: "MCP ToolSource가 던지는 예외의 타입은 내장이고 mcp의 타입으로 던지지 않는다", "원인(`__cause__`)에는 mcp의 원래 예외(그 그룹과 `MCPError`)가 그대로 남는다", "없는 도구를 부르면 `LookupError`다". 어댑터 모듈 독스트링도 "던지는 예외의 타입은 내장이다 … 원인(`__cause__`)에는 mcp 의 원래 예외가 남는다"로 맞췄다.
  - 포트 독스트링의 보편 주장(명세 축). 고친 문장: "연결은 안(부르는 쪽)에서 난 예외를 감싸지 않고 그 객체 그대로 내보낸다. 닫기가 실패하면 그 실패가 함께 나올 수 있다."
  - 테스트 공백(두 축). 서버 둘 가운데 둘째가 열리지 않는 사례(`test_둘째_서버가_열리지_않아도_연결_오류_하나다`)와 여는 도중의 취소 사례(`test_여는_도중의_취소는_연결_오류로_바꾸지_않는다`)를 더했다. 사례 4는 `match`에 `Connection closed`를 더해 까닭까지 본다. 셋 다 구현 뒤라 `ticket02_mutations.toml`로 빨강을 봤다(프로브 README의 "티켓 02의 셀프 리뷰 변이").
  - 기점(명세 축 Nit). README 대조군의 "`origin/main`의 것"을 `5040230c`로 고쳤다.
  - `_Escaped.unwrap` 독스트링의 시제품 이력(표준 축 Nit)을 "잎까지 내려가 견주면 그 경우 겉봉을 벗기지 못한다"로 바꿨다.
- 남긴 것
  - `_describe`·`_is_group`이 `core/run.py`의 것과 같다(Duplicated Code). 어댑터가 core의 비공개 함수를 쓰지 않는 경계(원칙 IV와 `.claude/rules/core.md`의 포트 경계)라 둔다. 출력 꼴도 다르다.
  - `_opened`의 `try`가 `yield`를 감싼다(판단 기준 2). 문맥 관리자가 연결 안의 예외를 받는 자리가 그 `yield`라 피할 수 없다.
  - `_session` 이름, 테스트 이름의 구현 용어, 포트 문장의 어색함은 Nit라 둔다(포트 문장은 위에서 고쳤다).
- 고친 것(이어서): `.scratch/plan.md` 16행의 현재형 "마지막 것이 지금 main의 결함 하나를 고친다 … 예외 그룹을 밖으로 올린다"를 "그때 main의 결함 하나를 고쳤다(티켓 02) … 올렸다"로 바꿨다. 기능을 03이 닫아도 03은 이 문장을 모르므로 이 PR에서 고친다.

## 검사 (셀프 리뷰 반영 뒤, 커밋 전)

- `uv run ruff check .`와 `uv run ruff format --check .`: 통과(890 files).
- `uv run python tools/run_checks.py`: zizmor, lint-imports, check-instructions, check-type-escapes, pyright(50.9초), pytest(496.2초), web-verify(543.4초)는 Passed. run-hooks(260.8초)는 `hook_journal_retro`의 "main(merge-base)에 이미 있는 순번으로 새 일지를 만든 Write" 한 사례가 빨갰다. 출력이 훅이 `tools/sibling_overlap.py`를 대 보지 못했을 때의 문구(`_unchecked`)였고, 같은 때 카나리아 둘이 함께 돌았다. `uv run python tools/run_hooks.py`를 홀로 다시 돌리자 그 사례를 포함해 페이로드 137건 어긋남 0건이었다. 이 브랜치는 훅과 도구를 건드리지 않았다.
- `uv run --env-file ../../../.env pytest -m llm`: 7 passed(290.3초). LLM 토큰 합계 58,308(입력 57,234, 출력 1,074), 트레이스 10개, 모델 호출 23건, 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다.
- 카나리아 둘(claude 2.1.302, HEAD `5040230c`에 커밋하지 않은 작업 트리): `adapters_rule_boundary_exceptions.toml` 통과 4, `adapters_rule_new_optional_fields.toml` 통과 4. 두 명세의 최신 결과 줄을 고쳤다.
- 변이 `ticket02_mutations.toml`: 변이 3 모두 표지까지 기대대로 빨갰다.
