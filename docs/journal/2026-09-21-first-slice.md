# 첫 슬라이스 구현 일지 · 2026-09-21

`/implement`로 `.scratch/first-slice/`의 티켓 일곱을 한 세션에 구현한 기록. 브랜치 `feature/first-slice`에 티켓당 커밋 하나. 기록 규칙은 [킥오프 일지](2026-09-19-kickoff.md) 머리말과 같다.

## 결과

- **원칙 I의 판정 통과(기한 하루 전).** `uv run --env-file .env pytest -m llm`이 둘 다 초록이다. 모델 어댑터가 실제로 답하고(4초), CLI 프로세스가 `calc`를 띄워 `npx`로 `everything` MCP 서버를 올리고 Anthropic이 `add` 도구를 불러 답하며 트레이스에 `llm_called`와 `tool_called`가 모두 남는다(14초). PRD의 성공 조건 둘이 닫혔다.
- 기본 스위트 86개가 네트워크 없이 7초에 돈다. pyright strict 0, ruff 0, import-linter 3/3.
- 데모: `uv run agent-os run calc "2 더하기 2는?"`. `--verbose`면 이벤트가 표준 에러로, 트레이스는 `traces/<run_id>.jsonl`.

## 브랜치 전략

> 사용자: (선택) "슬라이스 하나를 한 브랜치로 (추천)"

운영 규약은 티켓마다 브랜치와 PR인데, 기한을 이유로 한 브랜치를 추천했고 사용자가 골랐다. 커밋은 티켓당 하나로 잘라 두었다.

## 01 의존성과 테스트 설정

- tech.md 표대로 바꿨다. mcp가 2.2.0에서 1.30.0으로 내려갔다(ADR 0001이 예상한 대가).
- ADR 0007이 적은 `error::RuntimeWarning` 하나로는 `await` 누락이 안 걸렸다. 일부러 await를 뺀 테스트로 확인하니 GC 시점의 unraisable 예외라 pytest가 `PytestUnraisableExceptionWarning`으로 감싸고 통과했다. 그 경고도 에러로 올려야 실제로 빨개진다. ADR 0007 이력에 적었다.

## 02 모델 호출 (원칙 I)

- ChatModel 포트는 langchain-core 추상 클래스. `call_model`이 `AIMessage`를 `ModelReply`로 감싼다.
- strict 마찰 하나: pyright가 pydantic 별칭 필드를 별칭 이름으로만 받고 `Field(None, alias=...)`의 위치 기본값을 기본값으로 안 본다. `cast` 대신 별칭으로 부르고 `timeout=None, stop=None`을 명시했다.
- 키를 지우고 돌리면 실패(skip 아님), 기본 스위트에서 deselected. 둘 다 실측.

## 03 sdk 계약

- `schema_version` Literal["1"], `PluginKind` StrEnum 넷, 에이전트 `mcp = [...]`, mcp `[server]`, `run_started.principal` 필수, NewType 넷, `ctx.run_id`·`ctx.now()`.
- ADR 0008 초안을 `proposed`로 쓰고 구현을 계속했다. 결정은 승인된 명세에 이미 있었다.

## 04 실행 함수와 루프 — ADR 0001 후퇴

- 오늘이 후퇴 체크포인트였다. langgraph 1.2.11의 `add_node`·`compile`·`ainvoke`가 strict에서 전부 "partially unknown"이고, 그 `Unknown`이 라이브러리 시그니처 안(`CachePolicy[Unknown]`, `Command[Unknown]`)이라 호출하는 쪽에서 풀 수 없다. 남는 길은 pyright 규칙을 끄는 것뿐이라 원칙 III 위반이다.
- 하루를 더 쓰지 않고 바로 후퇴했다. "풀리나"보다 "풀리는 종류인가"가 먼저였다. 루프를 langchain-core 위에 40줄로 직접 썼다. 포트 다섯과 플러그인 계약은 그대로. langgraph를 의존성에서 빼고 ADR 0001 이력, rules/core.md, tech.md, CLAUDE.md를 고쳤다.
- 후퇴 대상이 ADR 0001의 "anthropic SDK 내장 루프"가 아닌 이유도 적었다. 그 ADR 뒤에 포트가 langchain-core로 정해졌고 명세가 "바뀌는 것은 루프 구현 하나"라고 못 박았기 때문이다.

## 05 디스크 어댑터

- 파일시스템 PluginSource(고유 모듈명 `agent_os_plugins.<name>.<module>`, `sys.path` 불변), JSONL TraceSink(첫 줄 헤더, `union_tag_invalid`만 골라 `UnknownEvent(raw)`), 시스템 Clock. 18개 테스트가 첫 실행에 통과했다.

## 06 CLI

- 불리언 플래그 인자 대신 `progress: TextIO | None`. `main`이 어댑터 넷을 조립하고 주체는 `getpass.getuser()`. Windows cp949 대비로 표준 스트림을 UTF-8로.
- 표면 테스트는 `tmp_path`에 쓴 픽스처 에이전트로 `main()`을 부른다. `ChatAnthropic`이 키 없이 생성되는 것을 확인해서 가능했다.

## 07 MCP 도구

- ToolSource 포트: `connect(servers)` → async context manager → `ToolConnection`(도구 목록, `call`). 어댑터는 langchain-mcp-adapters로 서버마다 세션을 유지.
- 실측 셋. (1) `get_input_jsonschema()`는 Runnable 입력 스키마라 top-level `anyOf`가 생겨 Anthropic이 도구를 버린다. `args_schema`가 맞다. (2) `ToolCall`로 부르면 `ToolMessage.status`로 isError를 안다. (3) async 픽스처로 세션을 열면 pytest-asyncio가 setup·teardown을 다른 태스크에서 돌려 anyio 취소 범위가 터진다. 테스트 본문에서 `async with`로 연다. ADR 0007 이력과 rules/tests.md에 적었다.
- 어댑터 테스트는 파이썬 FastMCP 서버에 붙어 네트워크도 Node도 없이 돈다.
- pyright 프로브를 처음에 `.scratch/`에 두어 "0 errors, 0 informations"를 받았다. 점 디렉터리라 기본 exclude였다. 킥오프 일지에 적힌 같은 실수의 반복이다. `tests/` 아래에서 다시 쟀다.

## 셀프 리뷰 (`/code-review main`)

Critical·Major 없음. 반영한 것: `ctx.tool()`의 예외 경로가 `ok=false`와 다르게 취급되던 것(테스트 이름과 단언이 모순이었다), try 블록 안 로직 분리, 용어집 피할 말(세션·응답·프롬프트)을 새 항목으로 정의하거나 이름 변경(`ToolSession`→`ToolConnection`), 빈 `--model` 진단, 테스트 셋 추가, ADR 0008에 `Json`·`ToolError` 기록. 후속으로 남긴 것: MCP 어댑터의 예외 감싸기, 테스트 픽스처 중복.

## PR 전략 재검토

> 사용자: "근데 티켓별로 PR을 올리는건 별로야?"

별로가 아니었다. 티켓별 PR이 문서화된 규약이고 한 브랜치는 기한 때문에 추천한 것이었다. 기한 이유가 사라졌으니 규약대로 간다. 커밋이 티켓당 하나라 각 커밋에서 브랜치를 딴다.

> 사용자: (선택) "티켓별 PR 일곱 (규약대로)", "승인 (accepted로 바꾼다)"

ADR 0008이 accepted가 됐다.

## 추천과 결정이 갈린 곳

- 브랜치 전략. 처음엔 한 브랜치를 추천했고 사용자가 골랐다가, 사용자 질문으로 티켓별 PR로 돌아갔다. 추천의 근거(기한)가 사라진 뒤에도 추천을 갱신하지 않은 것이 문제였다.

## 에이전트가 번복하거나 고친 것

- ADR 0007의 "RuntimeWarning을 에러로"가 실제로는 안 걸리는 것을 실측으로 잡았다. 설정이 그럴듯한 것과 검사가 도는 것은 다르다.
- pyright 프로브를 exclude 경로(`.scratch/`)에 두어 무효한 "0 errors"를 받았다. 킥오프 세션과 같은 실수. `informations` 수가 0인 것이 단서였다.
- 07의 첫 e2e가 `ExceptionGroup: unhandled errors in a TaskGroup`으로 죽었는데 원인이 안 보였다. `_describe`가 그룹을 펼치게 고쳤고, 실제 원인은 도구 스키마였다.
- 셀프 리뷰가 "직접 도구 호출의 예외 경로" 결함을 잡았다. 테스트 이름은 "에이전트가 잡을 수 있는 ToolError"인데 단언은 `RunFailed`였다. 이름을 행동 명세로 쓰는 규칙이 모순을 드러냈다.

## 다음

- 브랜치 일곱(`feature/01-...`~`feature/07-...`)을 각 커밋에서 따고 01부터 차례로 PR을 연다. 앞 PR이 squash 병합되면 다음을 main에 rebase한다. 셀프 리뷰 반영, ADR 0008 승인, 이 일지와 티켓 상태는 07 PR에 얹는다.
- PR마다 `gh pr comment <번호> --body "@coderabbitai review"`(operations.md). CodeRabbit CLI는 시간당 3회라 슬라이스 전체에 한 번 돌리고 그 결과를 PR들이 참조한다.
- 다 병합되면 `.scratch/plan.md`의 first-slice를 done으로 바꾸고 http-channel, admin-api, interrupts가 프론티어로 열린다.
- 슬라이스 2 인터럽트 티켓이 열릴 때 langgraph의 strict 타입을 같은 프로브(`tests/` 아래에서)로 다시 잰다. ADR 0001 이력.
- 후속 후보(티켓 07 코멘트): MCP 어댑터 예외 감싸기, 테스트 픽스처 중복 정리. 회고에서 규칙 후보로 볼 것: "검사 도구의 대상이 그 도구의 범위 안인지 먼저 본다"가 두 세션 연속 반복됐다(세 번째면 규칙 후보).

## 회고 (2026-09-21, 슬라이스를 닫은 뒤)

> 사용자: "추천대로 회고 먼저하는데 회고 시점은 자동 아니였나?"

계기가 자동("일지의 '다음' 절을 갱신하며 단계를 닫을 때")인데 에이전트가 일지를 쓰고도 돌리지 않고 물어봤다. 후보 다섯 중 넷을 사용자가 승인해 반영했다(PR은 `chore/retro-2026-09-21`). (1) retro 계기 훅 — `docs/journal/*.md`를 쓰면 `tools/hook_journal_retro.py`가 컨텍스트에 계기를 넣는다. 이 저장소의 첫 훅. (2) heredoc 훅 — 40줄 넘는 heredoc을 `tools/hook_bash_heredoc.py`가 deny하고 Write로 안내한다. 같은 세션에서 두 번 어긴 지침의 훅화. (3) `tools/gh_run_summary.py`가 거부된 도구 이름을 집계한다. (4) CLAUDE.md 환경 함정에 pyright 프로브 위치, operations.md에 CodeRabbit 한도 대체 규약(+ADR 0006 이력). 환경 변경 없이 기록만: 추천 근거가 사라진 뒤 추천을 갱신하지 않은 것(브랜치 전략).
