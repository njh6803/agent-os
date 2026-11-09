# 2026-11-10 (06:24) mcp-http 실제 모델 시험

세션 제목 `feature/04-real-model-calc-over-remote-mcp-server`. 브랜치 같은 이름, 워크트리 `.claude/worktrees/04-real-model-calc-over-remote-mcp-server`(기준 `df69924f`, 02의 병합 커밋). 모델 Sonnet 5.5 / high(지시문). 나란히 도는 티켓은 03이다.

## 사용자 프롬프트

> .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/mcp-http/issues/04-real-model-calc-over-remote-mcp-server.md
>
> 이번 요청 범위: PR과 병합까지

## 한 일

티켓 04를 구현했다. `tests/test_main.py`에 `llm` 마커의 시험 하나(`test_calc_가_원격_mcp_서버에_주소로_붙어_그_도구로_계산하고_트레이스에_도구_호출이_남는다`)와 도우미 `_replace_in`을 더했다. `src/`와 픽스처(`tests/mcp_http.py`, `tests/mcp_http_server.py`)는 건드리지 않았다.

- 저장소의 플러그인을 `_copy_repo_plugins`로 임시 루트에 복사하고(규칙 파일 `plugins/rules.toml` 포함) 02의 `serving`으로 HTTP 픽스처를 별도 프로세스로 띄운다. 그 주소를 `url`로 적은 http 모양의 mcp 플러그인 `remote-calc`를 임시 루트에 쓴다(`plugins/mcp/`에는 http 예시를 두지 않았다. ADR 0049).
- calc 매니페스트의 `mcp`와 규칙 파일의 `[agents.calc]` 줄을 `remote-calc`로 바꾼다. 둘 다 원문이 정확히 한 번 있어야 바뀐다(`_replace_in`).
- 실제 CLI 프로세스로 `17 더하기 25는?`을 돌려 종료 코드 0, 출력에 `42`, `tool_called`(`ok`)가 있고 마지막 이벤트가 `run_finished`인 것을 본다. 양성 대조로 픽스처 기록 파일에 POST가 있는지 본다. `ANTHROPIC_API_KEY`가 없으면 단언 메시지와 함께 실패한다. 트레이스는 `tmp_path` 아래다.

## 검증

- 빨강: 02가 접속을 이미 들여서 구현 전에 빨갤 수 없었다. 티켓대로 계산 결과 단언을 `42`에서 `43`으로 일부러 틀리게 두고 돌리자 그 단언(`assert "43" in result.stdout`, 출력은 `42\n`)에서 실패했고, 그 앞의 접속과 답은 지나갔다. 되돌린 판은 통과다(둘 다 손으로 봤다).
- `uv run ruff check .`와 `uv run ruff format --check .`는 초록이다.
- 러너 `uv run python tools/run_checks.py`(백그라운드, 종료 코드 0): check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright 둘, run-hooks 통과, pytest 542.9초, web-verify 673.8초(출력을 읽었다). 이 티켓은 web과 `openapi.json`을 건드리지 않아 e2e와 사진 비교는 치지 않았다. 러너는 `_replace_in`을 고치기(아래 셀프 리뷰) 전에 시작했으므로 그 한 곳은 커밋의 pre-commit이 다시 본다.
- `uv run --env-file ../../../.env pytest -m llm`: 아홉 개 통과(339.33초). 한 줄: `LLM 토큰 합계 55,545(입력 54,486, 출력 1,059). 트레이스 13개, 모델 호출 24건. 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다`. 새 시험만 따로 돌린 판은 1,667 토큰이다.
- `uv run python tools/sibling_overlap.py`: 번호 겹침 없음, 함께 고친 파일 없음. 03 워크트리와 겹치는 파일이 없다.
- 티켓 `Status: done`. 03이 아직 열려 있어 기능 계획의 `**끝:**` 줄은 쓰지 않았다. `plan_table.py`는 바꾼 파일이 없다.

## 셀프 리뷰

`/code-review`. 범위는 기준 `df69924f`, 파일 2개(작업 트리), 커밋 0개, 미추적 0개다. 표준 축은 sonnet·high, 명세 축은 세션의 모델이다. 둘 다 Critical·Major는 없었다.

고친 것:

- 표준 Minor: `_replace_in`의 독스트링이 "한 곳을 바꾼다"인데 `str.replace`는 모든 출현을 바꾸고 출현 수를 단언하지 않았다. 그래서 `text.count(old) == 1`을 단언하고 독스트링을 그 동작("정확히 한 번 나올 때만")에 맞췄다. 두 패턴은 지금 각각 한 번만 나온다.

남긴 것과 이유:

- 명세 Minor: 양성 대조(기록 파일의 POST)는 연결만 해도 `initialize`와 `tools/list`가 POST로 남아 도구 호출까지는 증명하지 않는다. 서브에이전트는 `ToolCalled.server`를 단언하자고 했으나 그 칸은 `run_paused`에만 있고 `tool_called`에는 없다(`sdk/events.py`). 도구 호출이 그 서버의 것이라는 근거는 calc가 고른 mcp가 그 플러그인 하나뿐이라는 것이고, 티켓이 요구한 양성 대조는 "POST 요청이 있는지"다. 이 티켓의 몫만 쓰기에 따라 더하지 않았다.
- 표준 판단 거리: 임시 루트의 매니페스트를 고쳐 쓰는 일이 파일 안에 세 모양(`_replace_in`, `_set_conversation_limit`의 이어 붙이기, 규칙 파일을 통째로 쓰는 시험)으로 있다. 합칠 만큼 크지 않다. `_replace_in`이라는 이름이 무엇을 바꾸는지 말하지 않는다는 지적은 호출 둘과 독스트링이 말한다고 보고 두었다.
- `"42" in result.stdout`은 선례(`"4"`)와 같은 수준이다. 모델이 도구를 안 불러도 이 단언만으로는 통과하지만 `tool_called` 단언이 그것을 막는다.

다시 돌린 명령: `uv run ruff check tests/test_main.py`와 포맷 검사는 고친 뒤 초록이다. 손으로 치는 나머지 다섯과 `-m llm`은 고치기 전의 판으로 초록이었고(`-m llm`은 고친 뒤 판으로 다시 돌려 아홉 통과), 커밋의 pre-commit이 고친 판을 다시 돈다.
