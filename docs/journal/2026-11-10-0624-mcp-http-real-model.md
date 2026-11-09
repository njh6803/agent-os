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

## PR 직전 리뷰(coderabbit-review)

범위: 기준 `origin/main`, 커밋 하나(`cecd4162`), 미커밋 변경 없음(이 일지의 이 절은 이 뒤에 쓴 것이다). 서브에이전트가 CLI 0.7.5로 `coderabbit review --agent --include-untracked --base origin/main`을 돌렸다. `Plan: Free`, `Seat: not assigned`였으나 리뷰는 파일 3개를 끝까지 돌아 `review_completed`, 지적 0건이다(CLI 축).

밀 주장 셋을 서브에이전트가 코드와 대 봤고 모두 맞았다. 근거는 `grep -o`로 센 `mcp = ["everything"]`(`plugins/agents/calc/plugin.toml`)와 `allow = ["everything:*"]`(`plugins/rules.toml`)가 각각 정확히 한 번이라는 것, ADR 0049 "시험" 항목의 같은 문장, `.claude/rules/core.md`와 `core/run.py`의 `tool_connection` 규정, `git diff origin/main --stat`이 세 파일(시험, 티켓, 일지)뿐이고 픽스처와 `src/`가 비어 있다는 것이다. 일지의 시간·토큰 수치는 재현하지 않았고 일지 기록을 읽었다고 서브에이전트가 밝혔다.

고친 것: 없음. 남긴 것: 없음. 오탐: 없음.

## PR

푸시(`git push -u origin feature/04-real-model-calc-over-remote-mcp-server`, 커밋 하나 `cecd4162`)하고 `gh pr create`로 PR #508(`test: 실제 모델로 calc가 원격 MCP 서버의 도구를 쓰고 트레이스가 남는 시험 (mcp-http 04)`)을 열었다. 본문은 저장소 템플릿을 채웠다(`--body-file`, 계약 영향 없음, 변경 유형 `test`). 저장소는 `njh6803/agent-os`다. 열린 직후 컨텍스트가 인계 문턱을 넘어 "PR 연 뒤" 계기가 왔고, `get_session`의 `self`에 `parentSessionId`가 없어 곁 세션이 아니므로 `handoff.md`대로 넘긴다. 이 세션은 구현, 셀프 리뷰, 커밋, PR 직전 리뷰, 푸시, PR 열기까지 했다. 봇 회차, 회고(`retro`), "다음" 절은 쓰지 않았다(봇 회차 뒤에 쓰는 순서는 앞선 일지 `2026-11-10-0421-mcp-http-connect.md`와 같다).

## 인계(PR 연 뒤)

제목을 `feature/04-real-model-calc-over-remote-mcp-server (인계함)`으로 바꾸고 워크트리 잠금을 풀었다. 이 세션이 띄운 백그라운드 작업은 모두 끝나 있어 멈출 것이 없었다. 낸 지시문은 아래 그대로다.

```
다음 작업: .scratch/mcp-http/issues/04-real-model-calc-over-remote-mcp-server.md (실제 모델로 calc 예시가 원격 MCP 서버의 도구를 쓰고 트레이스가 남는다)
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/mcp-http/issues/04-real-model-calc-over-remote-mcp-server.md
브랜치: feature/04-real-model-calc-over-remote-mcp-server
모델: Sonnet 5.5 / high. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-10-0624-mcp-http-real-model.md
이어받을 상태: 인계: PR 연 뒤. 일지는 docs/journal/2026-11-10-0624-mcp-http-real-model.md 이고 "PR"·"인계(PR 연 뒤)"가 이 인계다. PR #508이 열렸고 헤드는 cecd4162이며 셀프 리뷰(Critical·Major 없음)와 PR 직전 리뷰(CLI 지적 0건)는 끝났다. 일지의 "PR 직전 리뷰"·"PR"·"인계(PR 연 뒤)" 절은 커밋되지 않았다. 구현을 다시 하지 않는다. 남은 일: 첫 @coderabbitai review 코멘트와 wait_ci(merge.md 2 봇 회차), 봇 지적 반영, 회고(retro)와 일지의 "다음" 절(앞선 일지 2026-11-10-0421-mcp-http-connect.md처럼 봇 회차 뒤), 일지 커밋·푸시, merge.md의 워크트리 병합. 병합 직전에 origin/main에 티켓 03이 done으로 병합되었는지 본다(.scratch/mcp-http/issues/03-session-close-request-from-cancelled-runs.md). 03이 먼저 병합되었으면 이 PR이 그 기능의 마지막 열린 티켓을 닫는 것이라 기능 계획 .scratch/mcp-http/plan.md에 **끝:** 줄을 적고 plan_table.py를 돌려 같은 PR에 싣는다(implement SKILL.md의 티켓 맞추기). 이 PR이 먼저 병합되면 끝 줄은 03이 적는다.
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-11-09T21:48:30Z

## 이어받은 세션과 PR 봇 회차 1

제목을 `feature/04-real-model-calc-over-remote-mcp-server`로 되돌리고 `EnterWorktree(path)`로 워크트리에 들어갔다(헤드 `cecd4162`, origin/main은 앞서 있지 않았다). PR #508은 `njh6803/agent-os`의 것이다. `@coderabbitai review`를 남기고 `tools/wait_ci.py 508`을 띄웠다. 끝 줄은 "모두 통과. CodeRabbit: Review rate limited"다(`gh pr view 508 --json comments`와 `gh pr checks 508`을 손으로 읽었다).

CodeRabbit은 한도에 걸려("Next included review available in 28 minutes") 이 PR의 CodeRabbit 회차는 0이다. claude-review는 첫 회차이고 Critical·Major 없이 Minor 하나와 Nit 하나를 냈다. 경계 쪽은 지적이 없었다. 보류 이유를 PR 코멘트에 남겼다(`issuecomment-6752558568`).

- [Minor] 새 시험의 본문이 임시 루트 준비, CLI 실행, 단언을 한 함수에 잇는다. 보류. 쓰는 곳이 하나라 도우미로 뽑는 것은 이 티켓의 몫을 넘는다(implement "이 티켓의 몫만 쓰기"). 티켓 03이 비슷한 시험을 더하면 그때 뽑는다(아래 "다음").
- [Nit] 일지 날짜 `2026-11-10`이 리뷰 시점과 다르다는 지적. 오탐. 이름은 파일을 만든 로컬 날짜이고(ADR 0045 결정 7) 차이는 리뷰어 쪽 시계다.

## 회고

후보 넷. 승인 없음, 기각 넷. 만료 없음(`tools/queue_open_rows.py`를 이 워크트리와 `--ref origin/main`으로 두 번 돌려 "만료할 항목: (없음)"을 보았다). 넘긴 것은 없다.

기각.
- 구현 전에 빨강을 볼 수 없었다(02가 접속을 이미 들였다). 티켓이 정한 길(단언을 일부러 틀리게 두고 그 단언에서 실패하는 것을 본다)로 풀었고 새 사고가 아니다.
- `_replace_in`의 독스트링이 동작과 어긋난 것을 셀프 리뷰가 잡았다. 리뷰가 제 몫을 한 것이고 표준에 더할 새 판단 기준도 아니다.
- 인계 계기로 구현 세션과 봇 회차 세션이 나뉘었다. 정해진 절차(`handoff.md`)대로 되었다.
- CodeRabbit이 한도에 걸렸다. merge.md 회차 세기가 이미 정한 길이고 회차로 세지 않았다.

## 다음

- 남은 티켓은 03(`.scratch/mcp-http/issues/03-session-close-request-from-cancelled-runs.md`) 하나다. 이 PR(04)이 먼저 병합되면 03이 기능 `mcp-http`의 마지막 열린 티켓이므로, 03을 닫는 커밋이 기능 계획 `.scratch/mcp-http/plan.md`에 `**끝:** YYYY-MM-DD`를 적고 `uv run python tools/plan_table.py`를 돌려 `.scratch/plan.md`까지 같은 PR에 싣는다(implement SKILL.md "티켓 맞추기"). 03의 워크트리(`.claude/worktrees/03-session-close-request-from-cancelled-runs`)는 이미 있다.
- 04에서 보류하고 맡은 티켓이 없는 것: 새 시험의 준비 코드(임시 루트에 플러그인을 쓰고 매니페스트와 규칙 파일을 치환하는 부분)를 도우미로 뽑는 일(claude-review 첫 회차 Minor). 03이 `tests/test_main.py`에 같은 모양의 시험을 더하게 되면 그때 같이 뽑는다. 03의 체크박스에는 없다.
- 셀프 리뷰가 남긴 것(양성 대조가 도구 호출까지는 증명하지 않는 점)도 그대로다. `tool_called`에 `server` 칸이 없어 이벤트 계약을 바꾸지 않고는 단언할 수 없다.
- 워크트리에서 병합하므로 주 체크아웃은 갱신되지 않는다. 새 세션이 워크트리에 들어가기 전에 주 체크아웃 세션의 `tidy-checkouts`가 당긴다(merge.md "워크트리에서 병합할 때").
