# 09: 측정 아님 가르기 — 계정·설정·모델·오염·한도를 회차마다 보고, 걸린 회차를 그 이유와 함께 측정 아님으로 적는다

**What to build:** 회차 도구가 회차를 열기 전에 전용 설정 폴더의 계정을 대 보고(스토리 16·17), 첫 호출의 init에서 설정을 본다. 회차가 끝나면 도구 입력에서 답이 새는 길을 찾는 오염 검사를 돌고(스토리 30), 막는 규칙에 막혀 아무것도 얻지 못한 호출은 오염이 아니라 거부 수로만 남긴다(스토리 31). 세션 기록의 모델과 노력이 갈래와 다르면 측정 아님이고(스토리 32), 서브에이전트는 하네스가 정한 모델이나 세션이 고른 모델이면 통과한다(스토리 33). 계정 한도에 막힌 회차는 측정 아님(한도)과 풀리는 시각을 적는다(스토리 29의 앞 몫). 판정하는 함수는 값만 받는다. 걸린 회차를 다시 돌지, 과제를 뺄지, 러너를 멈출지는 10이 정한다.

근거는 `.scratch/model-rerun/spec.md`의 "클론과 설정 폴더"의 계정·설정 폴더의 설정과 그 2026-10-22 주석 둘(계정의 `auth status` 실제 값과 맞지 않으면 멈추는 것, 설정의 허용 플러그인), "한도", "오염 검사" 전체와 그 2026-10-22 주석 셋(커밋 메시지 떼기, 조각 경계, `permission_denials` 합치기), "모델 확인" 전체, "러너가 기대는 `claude -p`의 동작"의 한도 이벤트와 사용률, Testing Decisions "회차 하나"의 오염·모델·계정·설정 항목이다. 설계 5절이 원천이고 명세가 고친 자리(거부된 호출, 낱말 `gh`, 쓰기 내용의 대상, 서브에이전트의 허용 모임, `~/.claude` 전체)는 명세가 원천이다. 한도 표지의 선례는 `tools/canary.py`이고 그 시험은 `tests/tools/test_canary.py`다. 기록에 남기는 꼴은 `.claude/rules/tools.md`의 허용 목록 항목을 따른다.

08의 회차 고리(호출마다의 스트림, 끄기)를 쓴다. 이 티켓은 10을 막는다.

**Blocked by:** 08

**Status:** ready-for-agent

### 계정과 설정

- [ ] **회차마다 열기 전에 그 설정 폴더로 `claude auth status --json`을 읽는다.** 종료 코드와 상관없이 stdout의 JSON을 푼다. `loggedIn`이 참이고, `email`의 `@` 앞이 명령 줄로 받은 계정 이름과 같고, `configDirectory`가 넘긴 문자열과 글자 그대로 같아야 한다. 하나라도 다르거나 JSON이 풀리지 않으면 회차를 열지 않고, 10이 러너를 멈출 수 있게 그 까닭을 돌려준다. 기록에는 계정 이름만 적고 이메일은 적지 않는다
- [ ] **회차를 열기 전에 그 설정 폴더의 `settings.json`에 `env` 키가 없는지 본다**
- [ ] **첫 호출의 init 이벤트에서 `mcp_servers`가 비었고, `plugins`가 허용 모임 안인지 본다.** 허용 모임은 프로브가 본 내장 셋(`cc-plugin-agents-md`, `cc-plugin-telemetry`, `cc-plugin-plugin-authoring`, `.scratch/model-rerun/probes/README.md`)과 클론의 `.claude/settings.json`(B의 것)이 켠 플러그인의 합이다. 하나라도 아니면 08의 끄기로 그 호출을 끄고 "측정 아님(설정)"으로 적는다. 쓴 비용은 기록에 남아 예산 셈에 든다

### 모델

- [ ] **본 세션의 기록 파일에서 `<synthetic>`을 뺀 assistant 줄이 모두 갈래의 모델(전체 이름)과 갈래의 노력이다**
- [ ] **서브에이전트 기록의 assistant 줄은 모델만 본다.** 허용 모임은 갈래의 모델, 하네스가 정한 모델(클론의 `.claude/agents/*.md`의 `model` 값과 `code-review` 스킬이 표준 축에 주는 `sonnet`), 그 세션이 Agent 도구 입력의 `model`로 직접 고른 모델의 합이다. 별칭은 전체 이름으로 바꾼다(`sonnet`, `haiku`, `opus`, `inherit`과 빈 값은 갈래의 모델). 서브에이전트의 노력은 수만 기록에 남긴다
- [ ] **다르면 "측정 아님(모델)"이고, 어느 모델이 몇 줄이었는지를 기록에 적는다.** 파일럿(11)이 이 수로 허용 모임을 사람과 정한다

### 오염

- [ ] **도구 입력은 stream-json의 `tool_use`이고, 서브에이전트의 것(`parent_tool_use_id`가 붙은 이벤트)도 든다**
- [ ] **셸 명령(Bash, PowerShell)과 웹 도구의 입력에서 `github.com`, `githubusercontent.com`, `njh6803/agent-os`, 낱말 `gh`, `open_session.ps1`, `claude://`를 찾는다.** 낱말 `gh`는 앞뒤가 낱말 글자가 아닌 것이고, 찾기 전에 `git commit`의 메시지(`-m`·`--message`의 인자, `-F -`로 넘긴 heredoc 본문)를 뗀다. `bash`에 넘긴 heredoc처럼 명령이 되는 본문은 떼지 않는다. 주소와 다른 꼴은 떼지 않은 명령 전체에서 찾는다. 메시지를 떼는 파서는 git이 메시지를 받는 길(`-m` 여럿, `-am`처럼 붙인 옵션, `--message=`, `-F -`와 `-F <파일>`)을 먼저 나열하고 길마다 시험을 둔다(`.claude/rules/tools.md`의 하류 항목과 같은 까닭). 선례 `tools/hook_bash_commit_msg.py`의 `message_files`는 그 가운데 `-F <파일>`(`--file`)만 다루고 heredoc 본문은 모두 벗긴다. `-m`·`--message`의 인자와 `-F -`의 heredoc 본문을 메시지로 읽고, `bash`에 넘긴 heredoc 본문은 남기는 길은 그 함수에 없어 새로 짓는다
- [ ] **모든 도구 입력의 경로 값과 셸 명령에서 주 체크아웃 경로와 사용자의 `~/.claude` 경로를 찾는다.** 대소문자, `/`와 `\`, Git Bash의 `/c/` 꼴을 가리지 않고, 찾는 경로 뒤에 경로 구분자, 따옴표, 공백, 글의 끝이 올 때만 걸린다. `~/.claude-rerun` 같은 이웃 이름은 걸리지 않는다
- [ ] **막은 바깥 도구의 이름과 Skill 입력의 `open-session`을 찾는다**
- [ ] **Write·Edit·NotebookEdit의 내용(Write의 `content`, Edit의 `new_string`, NotebookEdit의 `new_source`)은 대상 파일이 `.md`가 아니고 `tests/` 밖일 때만 주소 셋을 찾는다.** 낱말 `gh`는 내용에서 찾지 않는다
- [ ] **결과의 `permission_denials`에 든 호출은 오염으로 세지 않는다.** 한 호출에 결과 이벤트가 여럿이면 그 모두의 `permission_denials`를 도구 호출 id로 합친다. 그 수는 거부된 호출 수로 남긴다
- [ ] **찾는 꼴은 상수이고 꼴마다 이름이 있다.** 회차 기록에는 걸린 꼴의 이름과 도구 이름만 남기고 입력은 옮기지 않는다. 걸리면 "측정 아님(오염)"이다

### 한도

- [ ] **`rate_limit_event`의 `status: rejected`이거나 결과의 `api_error`가 `usage_limit_reached`면 "측정 아님(한도)"이고 `resetsAt`을 적는다**(`tools/canary.py`와 같은 표지). 결과의 `api_error`만 있거나, `resetsAt`이 비거나 없거나 시각으로 읽히지 않으면(숫자가 아닌 값) 그 칸을 비워 적는다. `tools/canary.py`도 앞의 것은 `_result`가 "풀리는 시각 모름"으로, 뒤의 것은 `_describe_resets`가 "풀리는 시각 모름"이나 "읽지 못했다"로 적는다. 비운 한도를 어떻게 다룰지는 10이 정한다(명세 "한도"의 2026-10-23 주석). `allowed_warning`은 기록만 한다
- [ ] **회차의 첫과 끝의 `utilization`을 창마다 적는다**

### 시험과 검증

- [ ] **사례**(명세 Testing Decisions "회차 하나"): 계정 확인(가짜가 로그아웃이면 종료 1과 `email` 없는 JSON을 내는 것, 다른 계정, 슬래시나 대소문자만 다른 `configDirectory`), 설정 확인(`env` 키, 빈 `mcp_servers`가 아닌 것, B가 켠 플러그인은 통과하고 그 밖의 플러그인은 끄고 측정 아님(설정)), 모델·노력 불일치와 하네스가 정한 서브에이전트 모델·Agent 입력으로 고른 모델의 통과, 오염(`xargs gh`, `["gh", "api"]`는 걸리고 `high `는 걸리지 않음, `git commit -F -` heredoc과 `-m` 메시지 안의 `gh`는 걸리지 않고 `bash` heredoc 안의 `gh`는 걸림, Write 내용의 주소는 `.py`에서 걸리고 `.md`와 `tests/` 아래에서 걸리지 않음, `~/.claude` 경로는 걸리고 `~/.claude-rerun`은 걸리지 않음, `/c/` 꼴과 대소문자, 서브에이전트의 도구 입력, 거부된 호출을 오염으로 세지 않는 것과 결과 이벤트 여럿의 거부 합치기), 한도 표지와 `resetsAt`, 결과의 `api_error`만 있는 한도와 `resetsAt`이 빈 거절의 빈 칸, 사용률
- [ ] **기록에 남기는 꼴을 반박한다.** 걸린 꼴의 이름과 도구 이름 말고 입력의 글이 기록에 실리는 길이 없는지, 명령 치환, 따옴표 낱말, 여러 줄 명령을 든 입력으로 본다(`.claude/rules/tools.md`의 허용 목록 항목)
- [ ] **하위 프로세스 호출마다 시간 제한을 둔다**(`.claude/rules/tools.md`의 시간 제한 항목)
- [ ] **원칙 III를 지킨다**
- [ ] 검증 명령이 모두 초록이다
- [ ] **기능을 닫지 않는다**

### 04에서 넘어온 메모

- 04의 막는 규칙은 주 체크아웃과 사용자의 `~/.claude`만 막는다. 같은 뿌리 아래의 다른 회차 폴더(함께 도는 갈래와 앞선 갈래의 클론, 원본 stream-json)와 전용 설정 폴더의 세션 기록은 막지 않아, 세션이 다른 갈래의 풀이를 읽을 수 있다. 명세의 오염 목록에 없는 길이라 그 두 경로를 오염 꼴로 더할지 이 티켓이 정한다. 자기 회차 폴더 안은 오염이 아니므로, 뿌리를 찾는 꼴은 자기 회차 폴더를 빼야 한다.
- 04의 막는 규칙은 경로마다 그대로의 꼴과 링크를 푼 꼴(`deny_heads`)을 함께 건다. 오염 찾기가 두 꼴을 다 볼지도 이 티켓이 정한다.

### 06에서 넘어온 메모

- 이 티켓이 내는 칸(`denied_calls`, `utilization_start`·`utilization_end`, `contamination`, `model_mismatch`)은 `tools/rerun_session.py`의 `Elsewhere`로 `round_record`에 들어간다. 06은 그 칸을 짓지 않는다.
- 첫 init의 칸은 `launched.summary.init`(`Init`)의 `tools`·`plugins`·`mcp_servers`·`version`이다. 기록에는 `tools`만 `init_tools`로 옮긴다. `claude --version`은 `claude_version(claude, env=..., cwd=...)`이 첫 줄을 판의 꼴로 내고, 읽지 못하면 `None`이다.
- 노력과 모델의 수는 `transcript_counts(config_dir, 세션 id)`가 본 세션과 서브에이전트로 나눠 내고(`<synthetic>`이고 노력이 없는 줄은 뺐다), 기록의 `main_lines`·`subagent_lines`에 든다. 불일치 판정은 그 수와 갈래의 모델·노력을 견준다.
- `summarize_call`은 init과 결과 이벤트와 이벤트 수만 남기고 한도 이벤트(`rate_limit_event`)는 남기지 않는다. 한도의 판정은 원본 줄(`launched.drove.lines`나 `launched.stream_file`)에서 `parse_event`로 읽는다.
- 가짜(`tests/tools/fake_claude.py`)는 `write_script(..., logged_in=..., email=...)`로 `auth status`의 답(로그아웃이면 종료 1과 `email` 없는 JSON), `version=...`으로 `--version`의 답, `init_event(tools=..., plugins=..., mcp_servers=...)`로 init의 칸을 정한다. 한도 이벤트는 `rate_limit_event(status=...)`와 `limit_result()`가 짓는다.

### 08에서 넘어온 메모

- 이 티켓의 판정이 들어갈 자리는 `tools/rerun_continue.py`의 `run_sessions(..., screen=...)`이다. `screen(launched)`는 호출이 끝날 때마다 가장 먼저 불리고, 돌려준 `End`가 그 회차의 끝이다(끝이 아니면 `None`). 08의 `call_end`(시간, `error_max_budget_usd`, init이나 결과 이벤트 없음)보다 앞이라, 한도 표지가 든 호출이 결과 이벤트가 없어도 측정 아님(호출)이 되지 않는다(시험 `test_막는_판정이_낸_끝이_측정_아님_호출보다_앞선다`).
- 설정 항목의 "08의 끄기로 그 호출을 끄고"에 맞는 자리는 아직 없다. 08의 끄기는 `drive`가 마감을 넘기거나 출력을 닫고도 끝나지 않은 호출에서만 한다. `screen`은 호출이 끝난 뒤에 불리므로, init을 받은 직후에 끄려면 `drive`에 줄을 받을 때마다 부르는 판정(끄라고 답하면 끈다)을 더해야 한다. 끄는 함수는 `tools/rerun_session.py`의 `_ours`(끄기 직전에 명령 줄에 그 호출의 세션 id가 있는지 본다)와 `_kill`(나무째 끄고 거둔다)을 그대로 쓴다. 호출이 멈춘 꼴은 `Stop`이고, 지금 세션의 `runner_killed`는 마감에 닿아 끈 호출(`Stop.DEADLINE_KILLED`)에만 선다. 설정으로 끈 호출을 `Stop`의 어느 꼴로 적고 `runner_killed`를 세울지는 이 티켓이 정한다.
- 측정 아님의 끝은 `End(END_NOT_MEASURED, "<이유>", <풀리는 시각>)`이다. 08의 하위 이유 상수(`REASON_*`)는 `tools/rerun_continue.py`에 있고, 시험이 그 값이 `tools/rerun_files.py`의 `CAP_REASONS`·`NOT_MEASURED_REASONS`에 드는지 본다.
