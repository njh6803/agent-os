# 2026-10-21 (06) mcp-shutdown 티켓 01: mcp 2와 CLI의 Ctrl+C

브랜치 `feature/01-mcp-2-and-cli-interrupt`, 워크트리 `.claude/worktrees/01-mcp-2-and-cli-interrupt`. 티켓은 `.scratch/mcp-shutdown/issues/01-mcp-2-and-cli-interrupt.md`.

> 사용자: "`.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/mcp-shutdown/issues/01-mcp-2-and-cli-interrupt.md … 다음 작업: … mcp 2로 옮겨 취소된 실행의 MCP 서버도 닫힌 뒤 끝나게 하고, CLI가 Ctrl+C를 직접 받는다 / 다음 단계: 구현 / 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고 … 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 … 이어받을 상태: 없음 … 이번 요청 범위: PR과 병합까지"

## 체크아웃 정리

`tidy-checkouts`가 루트를 `561b37cb`에서 `ed5618cb`로 당겼다. 지운 것은 워크트리 `ticket-for-every-pr-design`과 그 브랜치 `docs/ticket-for-every-pr-design`, 브랜치 `worktree-ticket-for-every-pr-to-spec`이다. 22개를 남겼고 사람에게 넘길 것은 없었다.

## 구현

순서는 티켓의 "의존성과 헌법" 절 머리대로 사례 1의 빨강을 1.30.0에서 먼저 보고 의존성을 바꿨다.

- **의존성.** `langchain-mcp-adapters`를 빼고 `mcp>=2.3,<3`을 직접 의존으로 두었다. 락은 패키지 84개이고 오르고 들고 빠지는 것이 명세의 "락의 변화"와 같았다(락의 패키지 이름을 `tomllib`로 세어 견줬다). 설치한 판은 2.3.0이고 명세의 측정과 같은 판이다. `pyproject.toml`의 주석 둘과 import-linter 금지 목록 둘(`langchain_mcp_adapters` → `mcp`)을 고쳤다.
- **어댑터.** 서버마다 상류의 `stdio_client`와 `ClientSession`을 탈출 스택에 열고 `initialize()` 뒤 도구 목록을 커서 끝까지 따른다. 빈 커서는 끝이고 1000쪽을 넘으면 `RuntimeError`다. 결과의 글은 텍스트 블록과 텍스트 리소스의 글이다.
- **픽스처.** `mcp_fixture_server.py`를 `mcp.server.mcpserver.MCPServer`로 옮기고 `fail`이 `ToolError`를 던진다. 새 가짜 프로세스 모듈 `tests/adapters/mcp_lingering.py`(역할 넷, 하트비트, 멈춤 파일, 120초)와 쪽 나눔 서버 `tests/adapters/mcp_paged_server.py`를 두었다.
- **CLI 처리기.** `src/agent_os/channel/cli/interrupt.py`의 `run_interruptibly`를 조합 층의 run과 resume이 `asyncio.run` 대신 부른다. 첫 번째는 주 코루틴을 감싼 anyio 취소 범위의 `cancel`을 `loop.call_soon_threadsafe`로 루프에 맡기고, 두 번째는 표준 에러에 한 줄을 쓰고 곧바로 끝낸다. 끝나는 꼴은 POSIX가 SIGINT, 윈도우가 `os._exit(0xC000013A - 2**32)`다.
- **둘째의 한 줄.** 티켓은 "버퍼를 거치지 않고"이고 `os.write(2, …)`가 그 말 그대로지만, 윈도우 콘솔에서는 서술자 2에 쓴 UTF-8 바이트를 콘솔의 코드 페이지로 읽어 한글이 깨질 것으로 봤다(어림, 콘솔에서 재지 않았다). 그래서 표준 에러의 원시 파일(`sys.stderr.buffer.raw`)에 쓰고, 그 모양이 아니면 서술자에 쓴다. 원시 파일은 `getattr`로 꺼내 `io.RawIOBase`로 좁힌다. typeshed의 `TextIOWrapper`와 `BufferedWriter`가 제네릭이라 `isinstance`로 좁히면 pyright strict가 형식 인자를 알 수 없음으로 막았다(오류 넷).

## 빨강을 먼저 본 것

- 사례 1(도구 호출 도중의 기한): 1.30.0에서 `stay.hb 하트비트가 자란다`로 빨갰고 2.3.0에서 초록이다. 1.x의 `FastMCP`로 물러선 갈래는 올린 뒤 지웠다.
- 쪽 나눔 둘: 커서가 `None`이 아닌 동안 따르기만 하는 어댑터로 둘 다 기한의 `TimeoutError`였다. 빈 글의 끝과 1000쪽 상한을 더한 뒤 2.76초, 1.65초에 초록이다.
- 처리기의 닫기 시작 뒤 한 번: 시제품의 처리기(첫째를 네이티브 취소로 전하는 판)로 30초 상한에 걸렸다.
- 처리기의 쓰기 실패: 쓰기 실패를 넘기지 않는 판으로 종료 코드 120이었다(명세 검토의 임시 스크립트와 같다).

## 대조 (`asyncio.run` 그대로)

테스트 파일의 사본에서 자식 둘의 `run_interruptibly(main)`을 `asyncio.run(main())`으로 바꿔 돌렸다(세션 스크래치패드, 손으로 봤다). 3 failed, 1 passed였다.

- 한 번: 종료 코드는 3221225786으로 같고 표준 에러가 한 줄 대신 `KeyboardInterrupt`의 추적이다.
- 두 번, 닫기 시작 뒤 한 번: 30초 안에 끝나지 않았다.
- 쓰기 실패: 초록이다. 파이프가 닫혀 추적을 쓰지 못해도 같은 꼴로 끝난다. 이 사례가 가르는 것은 쓰기 실패를 넘기지 않는 처리기다(위).

## 손으로 본 것

- **시간.** 테스트의 `_누른다`를 사례마다 세 번 불렀다(윈도우, 홀로). 둘째 뒤 끝나기까지 0.015~0.017초(문턱 1초), 닫기 시작 뒤 첫째 뒤 끝나기까지 1.47~1.53초(문턱 8초)였다. 명세의 시제품(0.006~0.133초, 1.48~1.56초)과 같은 자리다. 닫기 시작 뒤 사례는 세 번 모두 닫기 끝의 표지가 누름 뒤 약 1.45초에 쓰였다 — 취소가 보호된 닫기 뒤에 와 연결이 정상으로 나섰고, 주 코루틴이 값을 돌려준 뒤 `run_interruptibly`가 눌림을 보고 중단으로 끝냈다. 그래서 처리기는 범위의 결과뿐 아니라 눌림 표지도 본다.
- **틈 둘.** 스크래치 스크립트(`gaps.py`)로 처리기 객체를 직접 불렀다. 범위를 잡기 전에 눌리면 주 코루틴이 첫 기다림에서 끊겨 `_Cancelled`가 돌아왔다(`['started']`). 루프가 닫힌 뒤에 눌리면 한 줄(`실행을 중단했다.`)을 남기고 3221225786으로 끝났다(`Popen`으로 본 값. Git Bash의 `$?`는 127로 보였다). 처리기를 되돌리기 전의 틈은 루프가 닫힌 뒤와 같은 길이다.
- **조합 층.** `tests/test_main.py`가 처리기를 단 채 in-process로 지난다(108 passed). 주 스레드이기 때문이다.

## 문서

헌법 `tech.md`의 런타임 의존성 행과 판 3.0.48, `.claude/rules/core.md` 포트 표, `adapters.md` 첫 슬라이스 문장, `channel.md`의 수명 문장, `runs.py`의 모듈·수명 독스트링, `test_end_user.py`의 수명 테스트 독스트링, core `_Body._connected` 독스트링, MCP 어댑터 모듈과 테스트 모듈의 독스트링, CLI 채널 모듈의 종료 코드, README `## 관리 화면`의 init 항목, `plan.md`의 mcp-shutdown 행(`in-progress`)을 고쳤다. `channel.md`와 `runs.py`는 닫는 시간을 다시 적지 않고 어댑터 독스트링을 가리킨다.

MCP 어댑터 모듈 독스트링의 "닫는 데 하나에 약 2초"는 mcp 2.3.0 `client/stdio.py`의 `PROCESS_TERMINATION_TIMEOUT = 2.0`을 읽고 썼다. `_all_tools` 독스트링과 쪽 상한 주석은 옛 라이브러리 이름 대신 "앞서 기대던 어댑터 라이브러리"라 적었다. 헌법 3.0.48은 `sibling_overlap.py`가 본 형제의 가장 높은 판(3.0.47) 위다.

잔존 grep(티켓의 일곱)은 살아 있는 문서에서 0이다. 걸린 것 가운데 남긴 것은 기록(일지, done인 기능의 `.scratch`, ADR 0001·0014의 이력 항목, 대기열의 닫힌 행 34)과, ADR 본문의 바뀜 포인터(ADR 0001), ADR 0014 Consequences의 "기다리지 않고 취소한다"(명세가 그 뜻으로 남긴다고 정했다), 진행 중인 mcp-shutdown의 명세·티켓·프로브가 바꿀 대상과 옛 판을 적은 대목이다. `plan.md`의 행은 기능의 요지를 끝난 사실로 고쳐 옛 이름을 뺐다.

## 검사 (셀프 리뷰 전)

- `uv run ruff check .` 0. `uv run ruff format --check .`은 `tests/adapters/test_mcp.py`의 리스트 내포 한 줄로 1이었고, `ruff format`으로 고친 뒤 러너를 띄웠다.
- `uv run pyright` 0, `uv run lint-imports` 0.
- `uv run python tools/run_checks.py` 0. 여덟이 모두 Passed다(pytest 312.5초, web-verify 414.0초, run-hooks 135.0초, pyright 42.9초). 일지 번호를 옮기고 `plan.md`를 고친 것은 러너가 도는 동안이었다.
- `uv run --env-file ../../../.env pytest -m llm`: 띄웠으나 7개 가운데 둘을 지난 자리에서 인계로 멈췄다. 결과가 없다. 새 세션이 다시 돌린다.
- 이어받은 세션이 셀프 리뷰 반영 전에 다시 돌렸다. 7 passed(317.79초). LLM 토큰 합계 57,854(입력 56,823, 출력 1,031), 트레이스 10개, 모델 호출 23건, 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다.

## 검사 (셀프 리뷰 반영 뒤)

- `uv run ruff check .` 0, `uv run ruff format --check .` 0(881파일), `uv run pyright` 0, `uv run lint-imports` 계약 다섯 유지.
- `uv run --env-file ../../../.env pytest -m llm`: 7 passed(183.09초). LLM 토큰 합계 54,973(입력 53,898, 출력 1,075), 트레이스 10개, 모델 호출 22건, 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다.
- `tools/mutate.py --check`: 변이 셋의 원문이 한 번씩 있다(독스트링을 고친 뒤).
- 나머지(pytest, 지침·타입 우회·훅·web 등)는 이 커밋의 pre-commit으로 갈음한다.
- 커밋 `9cbb0a80`의 pre-commit: 모두 Passed. 러너는 399.2초였다(pytest 398.6초, web-verify 392.2초, run-hooks 111.8초, pyright 44.2초). ruff 둘, 표·줄 구분 문자·변이 표(`--staged`)·카나리아 명세 모양·헌법 판·커밋 메시지도 Passed였다. 인용 대조는 경고 5건을 냈다(막지 않는다). 일지의 넷 가운데 셋은 고쳐서 이제 저장소에 없는 문장을 옮긴 것(셀프 리뷰 표준 축 1과 명세 축 (c)가 인용한 옛 독스트링, 반영 줄의 첫 고침)이고, 하나는 원문의 쉼표를 빠뜨린 것(반영 줄의 `runs.py` 항목, 커밋 뒤에 고쳤다)이다. `docs/constitution/README.md` 11행은 판 줄이 한 줄이라 옛 이력의 인용이 함께 걸린 것이다.

## 카나리아

`sibling_overlap.py`가 이 브랜치에서 고친 rules 셋을 원천으로 드는 카나리아 명세 일곱(`.scratch/end-user-continuation/probes/canary/`)을 알렸다. 이 PC, claude 판은 원본의 init 이벤트에서 아직 읽지 않았다(새 세션이 `# 최신 결과:` 줄에 적을 때 원본에서 읽는다). 원본은 세션 스크래치패드의 `canary/<명세 이름>/`이고 인계로 사라질 수 있다.

- `adapters_rule_new_optional_fields.toml`: 통과 4.
- `channel_rule_end_user_paths.toml`: 통과 4.
- `core_rule_shortcuts.toml`: 통과 3 · 실패 1. 실패는 실험군 1/3이고 러너가 `실험군 답에 카나리아가 없다: _follow`로 냈다. 그 회차의 답은 `(1) **옛 대화는 지도 없음이 이어진다**`와 `(2) _walk`였다. 규칙은 실렸고(규칙 본문을 옮겼다) 질문이 묻는 갈래와 다른 갈래(옛 대화)를 답한 것으로 본다. 이 브랜치는 그 문단을 고치지 않았다(포트 표 한 줄만). 다시 돌릴지, 질문을 고칠지는 새 세션이 정한다.
- 남은 넷: `channel_rule_pre_owner_damage.toml`, `core_rule_pre_owner_damage.toml`, `core_rule_read_cap_thread.toml`, `core_rule_runtime_only_events.toml`. 돌리지 않았다.

일곱 명세의 `# 최신 결과:` 줄은 아직 고치지 않았다.

이어받은 세션(같은 날)이 남은 넷과 `core_rule_shortcuts`를 다시 돌렸다. 원본은 그 세션 스크래치패드의 `canary/<명세 이름>/`(`core_rule_shortcuts`는 `core_rule_shortcuts_2/`)이고, 갈래는 둘 다 이 워크트리의 커밋 `ed5618cb`(작업 트리에 커밋하지 않은 rules 변경)다. claude 판은 앞 세션 원본 열둘과 이 세션 원본 스물의 init 이벤트가 모두 2.1.302다.

- `channel_rule_pre_owner_damage.toml`, `core_rule_pre_owner_damage.toml`, `core_rule_read_cap_thread.toml`, `core_rule_runtime_only_events.toml`: 모두 통과 4.
- `core_rule_shortcuts.toml` 다시 돌림: 통과 4. 세 회차 모두 (1)과 (2) `_follow`를 옮겼고 셋째는 `_walk`를 옛 대화 쪽으로 덧붙였다. 앞의 실패 1은 규칙이 실린 채 다른 갈래의 함수를 답한 것으로 판정한다. 이 브랜치가 고친 것은 포트 표 한 줄이고 그 문단이 아니며, 명세 머리 주석이 첫 판에서도 함수 이름이 흔들렸다고 적는다. 질문은 고치지 않는다.

셀프 리뷰 반영이 `channel.md` 본문의 수명 문장을 다시 고쳤다. 그 파일을 원천으로 드는 둘(`channel_rule_end_user_paths`, `channel_rule_pre_owner_damage`)은 같은 판(claude 2.1.302, `claude --version`)으로 이 브랜치에서 통과했고, 고친 곳이 본문뿐이고 명세는 고치지 않아 `tools/canary.py --preflight`로 갈음했다(사전 확인 통과 2). 일곱 명세의 `# 최신 결과:` 줄을 이 회차로 고쳤고, 둘에는 갈음을 덧붙였다. 실제로 다시 돌린 결과가 앞선 갈음 기록을 대신해 그 기록(2026-10-20의 갈음 문장)은 지웠다.

## 인계

셀프 리뷰 직전에 인계 계기가 왔다(세션 컨텍스트 321,875 토큰). 이 세션은 `/code-review`를 불렀으나 그 단계를 밟지 않았다. 인계하지 않는 다섯 때에 들지 않는다. 요청 범위는 PR과 병합까지이고, 지시문의 "이어받을 상태"는 `없음`이며, `get_session`의 `self`에 `parentSessionId`가 없다. 이 세션의 지금 제목은 `feature/01-mcp-2-and-cli-interrupt`다.

새 세션이 할 것은 차례로 셀프 리뷰(`/code-review`, 기점 `origin/main`)와 반영, 남은 카나리아 넷과 `core_rule_shortcuts`의 판정, 일곱 명세의 `# 최신 결과:` 줄, `-m llm`, 이 일지의 셀프 리뷰·카나리아·검사 절 마무리, 커밋, PR 직전 리뷰, PR, 병합, 일지 `## 다음`과 next-session이다. 커밋하지 않은 변경은 이 워크트리에 있다(`git status`).

지시문:

다음 작업: .scratch/mcp-shutdown/issues/01-mcp-2-and-cli-interrupt.md. mcp 2로 옮겨 취소된 실행의 MCP 서버도 닫힌 뒤 끝나게 하고, CLI가 Ctrl+C를 직접 받는다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/mcp-shutdown/issues/01-mcp-2-and-cli-interrupt.md
브랜치: feature/01-mcp-2-and-cli-interrupt
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-21-06-mcp-2-and-cli-interrupt.md(그 워크트리의 커밋하지 않은 파일)의 "인계"와 "카나리아"
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(`/code-review`)부터 한다. 검사 다섯과 러너는 리뷰 전에 초록이었고, `-m llm`은 인계로 멈춰 결과가 없으며, 카나리아는 일곱 가운데 셋을 돌렸다(`core_rule_shortcuts` 실패 1). docs/journal/2026-10-21-06-mcp-2-and-cli-interrupt.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지

open-session을 부른다 2026-10-21T04:55:32Z

## 셀프 리뷰 (이어받은 세션)

> 사용자(지시문): "이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(`/code-review`)부터 한다. … 이번 요청 범위: PR과 병합까지"

이어받은 세션이 워크트리에 `EnterWorktree(path)`로 들어와 `/code-review`를 기점 `origin/main`(`ed5618cb`)으로 돌렸다. 범위는 diff 17파일, 미추적 5, 커밋 0이다. 표준 축은 sonnet·high, 명세 축은 본 세션의 모델이다.

**표준 축**(하드 위반 0, 주장 여섯과 판단 다섯):

1. Major(판단). 어댑터 모듈 독스트링이 취소된 실행이 "서버와 그 아래 프로세스가 내려간 뒤에" 끝난다고 단정한다. 상류 `_stop_server_process`는 유예 안에 스스로 끝난 서버의 트리를 끄지 않고 `close_process_job`은 POSIX에서 아무 일도 하지 않아, POSIX에서는 그 서버의 자식이 남는다. → 고친다.
2. Minor. 같은 독스트링의 "하나에 약 2초"와 "넷"이 명세가 잰 SIGTERM까지 무시하는 서버(Linux 4.0초)와 serve 종료의 늦어짐을 뺐다. → 고친다(명세 "닫는 데 드는 시간" 표의 잰 값 셋으로).
3. Minor. `runs.py` 모듈·`lifespan` 독스트링, `channel.md`, `test_end_user.py` 독스트링에서 "실행이 끝나기를 기다리지 않는다"와 "MCP 서버를 닫기까지 기다린다"가 맞부딪힌다. 수명의 태스크 그룹은 취소된 자식이 끝나기를 기다리고, ADR 0034가 남긴 뜻은 취소 전의 유예가 없다는 것이다. → 고친다.
4. Minor. `interrupt.py`의 "신호 처리기는 … 루프를 깨우지 않아"는 POSIX에만 맞다. 3.12의 Proactor 루프는 주 스레드에서 `signal.set_wakeup_fd`를 단다(`proactor_events.py` 643행, POSIX 루프는 `add_signal_handler`에서만 단다. 본 세션이 소스를 읽었다). → 고친다.
5. Nit. core `_Body._connected`의 새 문장은 프로브 `close_fails` 하나가 근거이고 그 프로브는 다른 태스크에서 닫아 닫기를 터뜨린 길만 잰다(명세 159행). → 고친다(그 한정을 적는다).
6. Nit. `interrupt.py`가 JSONL 미완 줄의 출처를 `.claude/rules/adapters.md`로 달았는데 거기에는 그 규칙이 없다. → 고친다(`jsonl` 모듈 독스트링으로).
- 판단: "앞서 기대던 어댑터 라이브러리"가 무엇인지 말하지 않는다. → 고친다(ADR 0034를 가리킨다).
- 판단: `MAX_TOOL_PAGES`가 공개 상수인데 모듈 안에서만 쓴다. → 남긴다. 이 저장소는 문서가 이름으로 가리키는 값을 공개 상수로 둔다(`BACKLOG_FRAMES`, `READ_CAP`).
- 판단: 테스트 두 파일의 `press()`·`folder`·`_멈췄다`가 비슷하다. → 남긴다. import 모드가 importlib라 테스트 폴더끼리 보조 함수를 가져다 쓰는 길이 없고(`test_mcp.py`의 `LINGERING` 주석), 자식 스크립트는 문자열이라 모듈로 나눌 수 없다.
- 판단: `McpConnection`이 비공개 `_Route`를 받고 `route.tool`을 파헤친다. → 남긴다. 연결은 그 모듈의 `connect`만 만든다.
- Nit: `_write_unbuffered`의 `suppress(OSError)` 몸통에 `_raw_stderr()`가 섞였다(`CODING_STANDARDS.md` 에러 처리). → 고친다.
- Nit: 한 번 누르는 사례의 `INTERRUPTED in stderr`는 `FORCED`도 맞힌다(`FORCED`가 `INTERRUPTED`로 시작한다). → 고친다(`FORCED`가 없다는 단언과 그 변이).

**명세 축**(범위 넘침 0):

- (a) Minor. 결과의 글(텍스트 블록과 텍스트 리소스를 이어 붙인다)을 재는 테스트가 없다. → 고친다(픽스처 도구와 테스트, 변이로 빨강).
- (c) Minor. 첫 Ctrl+C 뒤 주 코루틴이 취소가 아닌 예외로 끝나면 추적이 찍히고 종료 코드가 1이다(명세 축이 자식 프로세스로 손으로 봤다). `run_interruptibly` 독스트링의 "눌렸으면 … 중단의 꼴로 끝난다"가 거짓이다. → 고친다(실패하는 테스트 먼저).
- (c) Minor. 표준 축 1과 같다.
- (c) Minor. `interrupt.py`가 원인을 단정한다("네이티브 취소는 … 보호를 뚫을 수 있어"). ADR 0034의 2026-10-21 이력은 "상류의 무엇이 끝나지 않는지는 가르지 않았다"이다. → 고친다.
- (c) Nit. 표준 축 4와 같다.
- (c) Nit. README 항목의 "끈 서버가 좀비로 남을 수 있다"는 런처(티켓 03)가 끈 서버의 어림이고, 이 티켓에서는 서버가 이 프로세스의 직접 자식이라 asyncio가 거둔다. 상류 독스트링은 그룹 기다림이 상한까지 간다는 것만 말하고 그 기다림은 유예를 넘긴 서버에만 든다. → 고친다.
- (c) Nit. 처리기 테스트 1·2와 닫기 사례 1이 서버가 호출을 받았다는 `slow` 표지를 단언하지 않는다. → 고친다.

### 반영

**고친 것.**

- 어댑터 모듈 독스트링(표준 1·2, 명세 (c)): 상류가 트리를 끄는 조건(유예 안에 끝나지 않은 서버만), 두 OS의 끄는 법, 윈도우만 Job Object를 닫아 남은 자손을 거둔다는 것과 POSIX에서는 스스로 끝난 서버의 자식이 남는다는 것, 명세 표의 잰 값 셋, 늦어지는 것에 serve의 종료를 더했다. 목록은 "넷"에서 "셋"이 되었다(가장 빨리 닫히는 모양을 첫 항목에 합쳤다). 상류 `_stop_server_process`와 `terminate_posix_process_tree`를 끝까지 열고 썼다. 첫 고침에서 "SIGTERM을 보내고 2초 뒤 SIGKILL"로 썼다가, 상류가 그룹이 사라지지 않을 때만 SIGKILL을 보내는 것을 보고 그 조건을 넣었다.
- 쪽 상한 주석과 `_all_tools` 독스트링(표준 판단): "앞서 기대던 라이브러리(ADR 0034 가 바꾼 것)"로 ADR을 가리킨다. 이름(`langchain-mcp-adapters`)을 한 번 넣었다가 뺐다. 이 브랜치가 살아 있는 문서에서 그 이름의 잔존을 0으로 맞췄고(위 "문서"), ADR 0034가 그 이름을 여섯 번 든다.
- `runs.py` 모듈·`lifespan` 독스트링, `channel.md`, `test_end_user.py` 독스트링(표준 3): "스스로 끝나기를 기다리지 않고 곧바로 취소한다"와 "수명의 태스크 그룹은 취소된 실행의 태스크가 끝나기를 기다리고, 그 끝에 MCP 서버의 닫기가 든다"(`channel.md`의 문장)로 나눴다. `lifespan`의 `finally`가 `group.cancel_scope.cancel()` 뒤 태스크 그룹을 나가는 코드를 보고 썼다.
- `interrupt.py`(표준 4·6, 판단 하나, Nit 하나, 명세 (c) 둘): 깨움 서술자 문장을 POSIX와 윈도우로 갈랐고, JSONL 출처를 `agent_os.adapters.jsonl`의 모듈 독스트링으로, 원인 단정을 ADR 0034 이력의 "가르지 않았다"로 고쳤다. `_write_unbuffered`는 `_raw_stderr()`를 `suppress` 밖으로 뺐다. 눌린 뒤 주 코루틴이 예외로 끝나는 길은 실패하는 테스트(`test_누른_뒤_실행이_취소가_아닌_예외로_끝나도_중단의_꼴로_끝난다`, 고치기 전 종료 코드 1)를 먼저 보고 `_run_guarded`로 고쳤다.
- core `_Body._connected` 독스트링(표준 5): 프로브가 다른 태스크에서 닫아 범위를 나가는 자리의 예외만 냈고, core는 그 길을 밟지 않으며 다른 까닭의 닫기는 재지 않았다는 한정을 적었다. 상류 `stdio_client`의 `finally`를 열고 썼다.
- README의 init 항목(명세 (c)): 좀비 문장을 빼고, 그룹 기다림이 유예를 넘겨 상류가 그룹째 끄는 서버에만 든다는 조건과 init 없이 재지 않았다는 것을 적었다. 좀비는 런처가 들어와야 생기는 어림이라 티켓 03의 "문서와 독스트링"에 볼 항목으로 넘겼다.
- 테스트(명세 (a)·(c), Nit): 픽스처 서버에 `blocks` 도구(텍스트, 이미지, 텍스트 리소스, 텍스트)와 결과의 글 테스트를 더했고, 한 번 누르는 사례 둘에 `FORCED`가 없다는 단언을, 처리기 테스트 둘과 닫기 사례 1에 `slow` 표지 단언을 더했다.
- 변이 `.scratch/mcp-shutdown/probes/ticket01_mutations.toml`(셋, 구현 뒤에 써서 빨강을 본 적이 없던 단언). 첫 회차는 표지 없이 셋 모두 빨갰다. 그 뒤 변이를 손으로 넣어 `E` 줄을 보고 고른 단언에서만 나오는 문구를 `expect_output`으로 더해 다시 돌렸고, 셋 모두 표지까지 기대대로 빨갰다(프로브 README의 2026-10-21 결과).
- 티켓 03에 받는 쪽 항목 둘을 더했다(어댑터 독스트링의 POSIX 문장, README의 좀비). 03의 Blocked by는 01이다.

**남긴 것.** `MAX_TOOL_PAGES` 공개 상수, 두 테스트 파일의 비슷한 보조 함수, `McpConnection`이 `_Route`를 받는 것(이유는 위 판단 줄).

**PR 직전 리뷰에 밀 주장**(반영으로 새로 쓴 사실 문장, 원문):

1. 어댑터 모듈: "상류의 닫기는 서버의 입력을 닫고 서버가 스스로 끝나기를 2초 기다린 뒤, 그때까지 끝나지 않은 서버만 프로세스 트리째 끈다. 윈도우는 Job Object 를 곧바로 끝내고, POSIX 는 그룹에 SIGTERM 을 보내 2초 안에 그룹이 사라지지 않으면 SIGKILL 을 보낸다. 윈도우는 그 뒤 Job Object 를 닫아 남은 자손을 거두고, POSIX 는 그것을 하지 않아 유예 안에 스스로 끝난 서버가 남긴 자식은 남는다"
2. 어댑터 모듈: "잰 값은 입력이 닫히면 스스로 끝나는 서버가 0.18~0.46초, 입력이 닫혀도 끝나지 않는 서버가 2.0~2.2초(상류의 유예), SIGTERM 까지 무시하는 서버(POSIX)가 4.0초다"
3. 어댑터 모듈: "그만큼 기한 뒤의 결말, HTTP 채널의 동시 실행 칸 반환, serve 의 종료가 늦다."
4. `runs.py`: "수명의 태스크 그룹은 취소된 실행의 태스크가 끝나기를 기다린다. 상류의 stdio 클라이언트가 서버의 닫기를 취소에서 보호하므로 그 끝에는 MCP 서버마다의 닫기가 든다"(`channel.md`와 `test_end_user.py`도 같은 뜻)
5. `interrupt.py`: "신호 처리기는 루프가 기다리는 도중에도 주 스레드에서 돌지만 POSIX 의 루프는 그것으로 깨어나지 않는다. asyncio 는 `add_signal_handler` 를 쓸 때만 신호의 깨움 서술자를 달고, 윈도우의 Proactor 루프만 처음부터 단다"
6. `interrupt.py`: "눌린 뒤 주 코루틴이 취소가 아닌 예외로 끝나도(취소를 받은 정리가 터졌다) 그 추적 대신 같은 한 줄로 끝난다."
7. `interrupt.py`: "주 태스크의 네이티브 취소(러너의 첫 번째)로 전하면, 서버를 닫는 도중에 온 첫째 뒤 mcp 2.3.0 에서 CLI 가 10초 안에 끝나지 않았다(ADR 0034 의 2026-10-21 이력. 상류의 무엇이 끝나지 않는지는 가르지 않았다)."
8. core `_connected`: "상류의 닫기는 서버를 끄는 일을 보호된 `finally` 에서 먼저 하고 그 뒤에 자기 취소 범위를 나간다 … 프로브는 닫기를 연 태스크가 아닌 태스크에서 해 범위를 나가는 자리의 예외를 냈고, 그 예외로 끝난 닫기 뒤에도 서버는 내려갔다 … core 는 연결을 연 태스크에서 닫으므로 그 길을 밟지 않고, 다른 까닭으로 끝난 닫기는 재지 않았다."
9. README: "init이 없으면, 입력이 닫혀도 2초 안에 끝나지 않아 상류가 그룹째 끄는 서버마다 그 그룹이 사라지기를 기다리는 시간이 상한(2초)을 다 채운다고 상류가 적었다"
10. 프로브 README의 2026-10-21 "티켓 01의 셀프 리뷰 변이" 문단과 표의 `ticket01_mutations.toml` 행.

## 인계 (커밋 뒤)

커밋 `9cbb0a80`(pre-commit 모두 Passed, 위 "검사 (셀프 리뷰 반영 뒤)") 직후 인계 계기가 왔다(세션 컨텍스트 350,089 토큰, 경계 `커밋 뒤`). 인계하지 않는 다섯 때에 들지 않는다. 커밋은 성공했고, 요청 범위는 PR과 병합까지이며, 이 세션의 지시문의 "이어받을 상태"는 `인계: 셀프 리뷰 직전`이라 경계가 다르다. 이 세션이 쓴 `인계 못함` 줄은 없고, `get_session`의 `self`에 `parentSessionId`가 없다. 이 세션의 지금 제목은 `feature/01-mcp-2-and-cli-interrupt`다.

이 세션이 번복하거나 고친 것은 위 "### 반영"의 고친 것 줄에 있다. 어댑터 독스트링의 SIGKILL 조건을 상류 코드에 맞춰 고쳤고, 옛 라이브러리 이름을 한 번 넣었다가 뺐다. 그 밖에 프로브 README의 변이 결과 문단에 처음 쓴 "실패한 단언은 두 회차가 같았다"를 뺐다. 첫 회차에는 표지가 없어 어느 단언이 빨갰는지 보지 않았기 때문이다. 커밋 뒤에는 일지의 인용 하나(`channel.md` 문장의 쉼표)를 고쳤고, 검사 절에 pre-commit 결과를 적었다. 이 둘과 이 절은 커밋하지 않았다.

새 세션이 할 것은 차례로 다음과 같다.

1. 커밋 뒤 변이 전체 실행(`tools/mutate.py`, 표 `.scratch/mcp-shutdown/probes/ticket01_mutations.toml`)
2. PR 직전 리뷰(`docs/constitution/operations.md` 리뷰 파이프라인). origin/main이 `ed5618cb`에서 움직였으면 먼저 합친다. CodeRabbit CLI는 좌석이 없어(Seat: not assigned) 돌지 못하므로 `/security-review`와 `bug-perf-review` 서브에이전트로 대신한다. 그 브리프에는 위 "PR 직전 리뷰에 밀 주장" 열을 "나열 밖도 잰다"와 함께 싣는다.
3. PR(`/git-pr`)과 봇 회차, 병합
4. 일지 `## 다음`과 next-session

지시문:

다음 작업: .scratch/mcp-shutdown/issues/01-mcp-2-and-cli-interrupt.md. mcp 2로 옮겨 취소된 실행의 MCP 서버도 닫힌 뒤 끝나게 하고, CLI가 Ctrl+C를 직접 받는다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/mcp-shutdown/issues/01-mcp-2-and-cli-interrupt.md
브랜치: feature/01-mcp-2-and-cli-interrupt
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-21-06-mcp-2-and-cli-interrupt.md(그 워크트리의 작업 트리 판)의 "인계 (커밋 뒤)"와 "### 반영"의 "PR 직전 리뷰에 밀 주장"
이어받을 상태: 인계: 커밋 뒤. `9cbb0a80`까지 구현, 셀프 리뷰 반영, 검사(pre-commit 모두 Passed, `-m llm` 7 passed)를 마쳤다. 아직 푸시하지 않았고 열린 PR이 없다. 남은 단계는 차례로 커밋 뒤 변이 전체 실행(`.scratch/mcp-shutdown/probes/ticket01_mutations.toml`), PR 직전 리뷰(`/security-review`와 `bug-perf-review`, 브리프에 일지의 "PR 직전 리뷰에 밀 주장" 열), PR, 봇 회차, 병합, 일지 `## 다음`과 next-session이다. 워크트리에 커밋하지 않은 일지 변경이 있다. docs/journal/2026-10-21-06-mcp-2-and-cli-interrupt.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지

잠금 풀기는 `is not locked`로 넘어갔다.

open-session을 부른다 2026-10-21T06:02:00Z

`tools/open_session.ps1`은 `fired=15:03:16`, `page=`, `folder=C:\project\agent`, `model=Opus 5.5`(원래 Sonnet 5.5), `effort=xhigh`(원래 high), `restore=필요`까지 낸 뒤 "모델을 고르는 사이 입력창의 지시문이 바뀌었다. 보내지 않았다."로 멈췄다(종료 코드 1, `idle=1340s`). open-session 3의 모델 오류 갈래라 같은 파일로 다시 돌리지 않았다. 사람에게 입력창을 보고 보내 달라고 부탁하고 턴을 끝냈다. 제목은 `(인계함)` 그대로 둔다. 남은 화면이 보내지면 그것이 인계 세션이다.

사용자가 다시 시도하라고 했다. 다시 돌리기 전에 그 브랜치 제목의 세션이 생기지 않았고 남은 화면이 창에 없음을 봤다. 멈춘 06:03 무렵 다른 두 브랜치의 인계 열기가 함께 있어 그 딥링크가 입력창을 덮은 것으로 본다(가르지 않았다). 같은 파일로 다시 돌려 `sent=15:15:21`로 보냈다. 고르기 전 값이 이미 `Opus 5.5 / xhigh`라 `restored=바뀐 것 없음`이었고, 첫 시도가 남긴 기본값(원래 Sonnet 5.5 / high)은 되돌리지 않았다. 새 세션 `local_483f5cb7`은 제목 `feature/01-mcp-2-and-cli-interrupt`, `cwd` 루트, `claude-opus-5-5` / `xhigh`다. 분할은 `split=`로 됐고, `focus`는 제목이 90초 뒤에 붙어 행을 찾지 못했다(새 세션은 메인 창 첫 패널에 보인다).

## PR 직전 리뷰 (둘째로 이어받은 세션)

> 사용자(지시문): "이어받을 상태: 인계: 커밋 뒤. `9cbb0a80`까지 구현, 셀프 리뷰 반영, 검사(pre-commit 모두 Passed, `-m llm` 7 passed)를 마쳤다. 아직 푸시하지 않았고 열린 PR이 없다. … 이번 요청 범위: PR과 병합까지"

이 세션이 `EnterWorktree(path)`로 들어왔다. origin/main은 `ed5618cb` 그대로라 합치지 않았다. 순서는 지시문과 달리 PR 직전 리뷰를 변이 전체 실행보다 먼저 돌렸다. `tools/mutate.py` 독스트링이 전체 실행을 셀프 리뷰와 PR 직전 리뷰를 반영해 커밋한 뒤에 한 번 돌게 정했고, 리뷰가 시험을 고치면 그 전의 실행은 옛 시험을 잰 것이기 때문이다. 이 리뷰가 실제로 시험을 고쳤다.

CodeRabbit CLI는 좌석이 없어 대체 둘을 나란히 돌렸다.

- `/security-review`: 취약점 0. 서브태스크가 MCP 서버를 띄우는 명령·환경·작업 폴더, 도구 결과를 글로 바꾸는 길, 서버가 보내는 요청(샘플링·elicitation·루트 목록은 기본 콜백이 거절한다), 처리기의 고정 문구, 의존성 교체를 따라갔다. 자식의 환경은 mcp 2.3.0 `get_default_environment()`의 허용 목록뿐이라 API 키가 넘어가지 않는다. 후보가 없어 오탐 거르기 단계는 돌지 않았다.
- `bug-perf-review`(sonnet): Minor 넷(유효 둘, 보류 둘). 밀 주장 열 가운데 1~8과 10은 일치였다(9는 아래 1). 호출 예산 40을 넘겨 50에서 멈췄다고 보고가 스스로 적었다.

트리아지(본 세션이 근거를 열었다):

1. 유효 → 고쳤다. README init 항목(밀 주장 9)이 상류의 조건을 뺐다. 상류 독스트링은 그룹이 모든 구성원이 죽어 거두어져야 사라진다고 적고, 그래서 그 기다림은 자손을 둔 서버에만 든다. Python 3.12 `asyncio/unix_events.py`의 기본 자식 감시자(`PidfdChildWatcher`, `ThreadedChildWatcher`)가 제 자식의 번호만 `waitpid`하는 것을 읽고, 자손 없는 서버는 asyncio가 거둔다고 적었다. 티켓 03의 README 항목에 런처가 들어오면 이 문장도 다시 쓴다는 것을 더했다.
2. 유효 → 고쳤다. `run_interruptibly`가 물려받은 SIGINT 무시를 덮어썼다. 셸이 작업 제어 없이 띄운 백그라운드 작업(`agent-os run … &`)이 같은 터미널의 Ctrl+C에 끊긴다. 이전의 `asyncio.run`은 처리기가 `default_int_handler`일 때만 제 처리기를 단다(`asyncio/runners.py`). 실패하는 테스트(`test_SIGINT를_무시한_채_시작하면_그_무시를_지킨다`, 고치기 전 종료 코드 3221225786과 `실행을 중단했다.`)를 먼저 보고, 처리기가 기본값이 아니면 `asyncio.run` 그대로 도는 갈래로 고쳤다. 같은 갈래가 이전 처리기가 `None`(파이썬 밖에서 단 처리기)이라 되돌리기가 `TypeError`를 내는 경우도 닫는다.
3. 보류 → 고쳤다. 두 번 누르는 사례의 둘째가 첫째의 0.5초 뒤라는 시간으로 갈렸다. 부하 아래에서 자식이 굶으면 둘째가 취소보다 먼저 오거나 POSIX에서 두 신호가 처리기 한 번으로 합쳐질 수 있다(코드를 읽은 어림, 재현하지 않았다). 고치는 값이 작아 둘째를 취소 표지(`cancelled`) 뒤로 옮겼다. 고친 시험이 아직 무는지 둘째가 곧바로 끝내지 않는 변이를 손으로 넣어 봤고 `FORCED` 단언이 빨갰다(둘째는 취소 표지 0.052초 뒤, 끝은 둘째 1.96초 뒤). 그 변이를 표의 넷째로 더했다. `FORCED_WITHIN_SECONDS` 주석의 "끊지 못하면 둘째 뒤 약 1.5초"는 둘째가 앞당겨져 "약 2초"로 고쳤다.
4. 보류 → 오탐. core `_connected`의 프로브 문장(밀 주장 8)은 명세 "결말 뒤 닫기의 예외"(158~159행)와 같다. 리뷰가 부수로 물은 CLI `_report`는 `_show`가 이벤트 열을 끝까지 돈다(`async for`, 중간에 나가지 않는다).

PR 봇에 밀 주장(이 반영으로 새로 쓴 사실 문장)은 PR 본문에 싣는다. README의 자손 조건과 asyncio의 거두기, `interrupt.py`의 백그라운드 작업 문장, `test_interrupt.py` 독스트링의 두 신호가 합쳐진다는 문장이다.

검사(커밋 전): `uv run ruff check .` 0, `uv run ruff format --check .` 0(881파일), 바꾼 두 파일의 `uv run pyright` 0, `tests/channel/cli/test_interrupt.py` 6 passed(56.02초), `tools/mutate.py --check` 변이 넷의 원문이 한 번씩 있다.
