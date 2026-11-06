# 2026-11-06 (06) 도구 명세의 서버 이름과 같은 이름 검사 (approval-rules 티켓 03)

세션 제목: `feature/03-tool-server-name-and-duplicate-tool-check`. 브랜치도 같다. 워크트리는 `.claude/worktrees/03-tool-server-name-and-duplicate-tool-check`.

## 사용자 프롬프트

> 사용자: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. … 인자: `.scratch/approval-rules/issues/03-tool-server-name-and-duplicate-tool-check.md`
> 다음 작업: 도구 명세(`ToolSpec`)가 서버 이름을 들고, 같은 이름의 도구는 연결 직후 실패하게 한다. 다음 단계: 구현. 어디서: 새 세션, 나란히 여는 2 중 2. 모델: Sonnet 5.5 / high. 이번 요청 범위: 구현·리뷰·커밋까지

## 한 것 (커밋 전, 워크트리에 있다)

- `core/ports.py`: `ToolSpec`에 필수 칸 `server: PluginName`을 `name` 바로 뒤에 더했고, `ToolConnection`의 독스트링에 "한 연결 안에서 도구 이름은 유일하고 어댑터가 보장한다"를 적었다.
- `adapters/mcp.py`: `McpConnection.tools()`가 `server=route.server`를 싣는다. `connect`가 도구를 이름으로 모으는 자리에서 같은 이름이 이미 있으면 `ValueError("같은 이름의 도구가 둘이다: <도구> (<앞서 모은 서버>, <겹친 서버>)")`를 던진다. 모듈 독스트링에도 적었다.
- 던지는 예외의 타입은 `ValueError`로 골랐다(내장이고 "연결을 열지 못함"의 `ConnectionError`와 가르려는 뜻: 서버가 못 붙은 것이 아니라 구성이 겹친 것). 어댑터 시험이 `type(raised.value) is ValueError`로 예외 그룹으로 감싸여 나오지 않음을 재고 초록이다. 앞서 연 서버의 문맥(`_opened`)이 겉봉을 벗긴다는 것이 이 시험으로 확인됐다.
- 시험: `tests/adapters/test_mcp.py`에 둘(`server`가 서버 플러그인 이름인 것·서버 하나는 그대로 열리는 것, 같은 픽스처 서버를 `first`·`second`로 열면 두 이름을 든 `ValueError`인 것), `tests/core/test_run.py`에 `DuplicateTools`와 core 사례 하나(원인 `tool_connection`, 메시지에 두 서버 이름).
- 생성자: core·router·end_user 시험의 가짜 연결이 모두 `server`를 채운다. 셋 다 상수 `DEFAULT_SERVER = PluginName("fake")`를 쓴다(04가 가짜 플러그인 소스의 기본 규칙을 이 이름에 맞춘다). core 시험의 `FakeConnection`·`FakeTools`는 `owners` 인자(도구 이름 → 서버 이름, 없으면 기본 서버)도 받는다. router·end_user의 가짜는 기본 서버만 쓴다. 프로브 `.scratch/approval-rules/probes/all_deny_resume_call.py`의 `ADD`는 `server=PluginName("probe")`를 채웠고, 모듈로 불러 `ADD.server`가 만들어지는 것만 봤다(측정은 돌리지 않았다).
- 문서: `.claude/rules/core.md`의 포트 표 `ToolSource` 행과 실패 정책(같은 이름의 도구는 연결 직후 `run_failed`, 원인 도구 연결), `.claude/rules/adapters.md`의 MCP 예외 항목(같은 이름 검사와 `ToolSpec.server`). `writing-for-agents`를 불러 쓴 뒤 고쳤다.
- 옛 표현 잔존: `조용히 덮|뒤 서버가|서버가 앞 서버|routes\[|같은 이름의 도구|도구 이름이 겹`을 살아 있는 문서에서 찾았고 옛 말("뒤 서버가 앞 서버의 도구를 덮는다")은 없었다(`docs/agents/domain.md`의 "조용히 덮어쓰지 말고"는 ADR에 관한 다른 문장이다).
- 티켓 `03-…md`: 체크박스 전부 `[x]`, `Status: done`으로 고쳤다(첫 편집은 `in-progress`로 바꿨다).

## 검증 (이 세션이 쳤다)

- `uv run ruff check . && uv run ruff format --check .`: 통과.
- `uv run python tools/run_checks.py`: 전부 통과(check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright 둘, run-hooks, pytest 367.8초, web-verify 535.3초). 종료 코드 0.
- `uv run --env-file ../../../.env pytest -m llm -q`: 7 passed, 185초. 출력의 토큰 줄: `LLM 토큰 합계 58,188(입력 57,094, 출력 1,094). 트레이스 10개, 모델 호출 22건. 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다.` 일지 검사 절에 옮긴다.
- 위젯 e2e·관리 e2e·사진 비교는 이 티켓이 그 면을 건드리지 않아 치지 않았다(티켓: 서버 하나만 고른 에이전트라 행동이 바뀌지 않는다).

근거의 종류: 검증 절의 통과와 수치는 이 세션이 친 명령의 출력을 본 것이다. 옛 표현 잔존은 Grep으로 본 것이다. 예외 타입을 `ValueError`로 고른 까닭은 이 세션의 판단이지 명세가 정한 것이 아니다(티켓이 "이 티켓이 정하고 내장 타입"이라 했다). `FakeConnection`의 `owners` 인자는 04가 도구마다 서버를 달리 줄 때 쓰라고 core 시험에만 더한 것으로, 쓰는 시험은 아직 없다(`DEFAULT_SERVER`로만 돈다).

## 카나리아 (새 세션이 `tools/canary.py`로 돌렸다)

`.claude/rules/core.md`·`adapters.md`를 고쳤으므로 `tools/sibling_overlap.py`가 알린 카나리아 명세 여섯을 새 `claude -p` 세션으로 돌렸다(claude 2.1.318, HEAD `c974bea9` 위의 커밋하지 않은 작업 트리. 러너가 찍은 줄이다). 다섯은 통과 4, 실패 0, "없음" 섞인 통과 0이다: `core_rule_shortcuts`, `core_rule_runtime_only_events`, `core_rule_read_cap_thread`, `adapters_rule_new_optional_fields`, `adapters_rule_boundary_exceptions`. 여섯째 `core_rule_pre_owner_damage`는 질문을 고치기 전의 판이 두 번 돌아 통과 3 · 실패 1, 통과 2 · 실패 2였다. 실패 셋은 모두 실험군이고 답이 core.md의 실패 정책 항목에서 왔다고 밝혔으며(규칙은 실렸고 대조군은 두 번 다 "없음"), (2)의 문장에 "둘 다"·"그 자리들을"을 끼워 바꿔 옮겨 카나리아 글자와 어긋났다. 그 문장은 이 브랜치가 고치지 않았고 core.md에 글자 그대로 있다(Grep으로 본 것). 그래서 규칙이 실리지 않은 것이 아니라 옮겨 쓰기가 흔들린 것으로 읽었고(어림이다. 이 흔들림이 이 브랜치의 문장 추가와 무관하다는 것을 가르는 갈래는 돌리지 않았다), 질문 (2)에 "낱말을 더하거나 빼거나 바꾸지 말고 실린 그대로 옮긴다"를 더해 다시 돌리자 통과 4였다. 질문을 좁힌 것은 `# 최신 결과:` 줄에 적었다. 여섯 명세의 `# 최신 결과:` 줄을 모두 고쳤다.

## 인계 시점의 상태

- (인계 당시의 기록이다. 이후 새 세션이 `/code-review`와 카나리아 여섯을 마쳤고 위 두 절에 있다.) 컨텍스트가 인계 문턱을 넘어 `셀프 리뷰 직전`에서 넘겼다. 그때는 `/code-review`가 돌지 않았고 커밋하지 않았다.
- 알림(`tools/sibling_overlap.py`): `.claude/rules/core.md`·`adapters.md`를 이 브랜치에서 고쳤는데 그 파일을 원천으로 든 카나리아 명세(`adapters_rule_new_optional_fields.toml`, `adapters_rule_boundary_exceptions.toml`, `core_rule_pre_owner_damage.toml`, `core_rule_read_cap_thread.toml`, `core_rule_runtime_only_events.toml`, `core_rule_shortcuts.toml`)가 있다. 새 `claude -p` 세션에서 `tools/canary.py`로 불러 보고 그 명세의 `# 최신 결과:` 줄을 고쳐야 한다(`docs/constitution/operations.md` 환경 규약 상세). 계정 한도로 돌리지 못하면 그 절의 항목대로 사전 확인만 돌린다.
- 같은 파일을 02 워크트리(`02-rules-file-read`)도 고친다: `.claude/rules/adapters.md`, `.claude/rules/core.md`, `src/agent_os/core/ports.py`, `tests/channel/http/test_end_user.py`, `tests/channel/http/test_router.py`, `tests/core/test_run.py`. 먼저 병합되는 쪽이 앞이고 뒤 쪽이 합친다(티켓 03 머리 문단).

open-session을 부른다 2026-11-05T21:57Z

## 셀프 리뷰 (`/code-review`, 새 세션이 돌았다)

범위: base `c974bea9`, 파일 10개 변경, 커밋 0개, 미추적 1개(이 일지). 두 축 모두 Critical·Major 0이다. 표준 축은 Minor 2·Nit 4, 명세 축은 Minor 3·Nit 2였다. 명세 축 서브에이전트는 코드를 직접 돌려 이 셋을 봤다고 보고했다(보고의 말이고 이 세션이 다시 돌린 것이 아니다. 둘째는 아래 새 시험과 변이로 이 세션도 봤다). 같은 픽스처를 세 이름으로 열면 문구에는 처음 겹친 둘만 든다, 앞 둘이 겹치고 셋째 명령이 없으면 `ConnectionError`가 아니라 `ValueError`다, 예외는 `ExceptionGroup`으로 감싸이지 않는다(셋째는 이 세션도 기존 어댑터 시험이 `type(raised.value) is ValueError`로 단언해 초록인 것을 봤다).

- **고친 것.**
  - `.scratch/approval-rules/probes/README.md`의 `all_deny_resume_call.py` 행: "묶음 B가 … 뒤에는 `ADD`에 `server=`를 더해야 가져온다"는 이미 한 일이 미래형으로 남은 문장이었다. "티켓 03이 더했다. `ADD`가 만들어지는 것은 모듈로 불러 손으로 봤고(커밋한 프로브의 결과가 아니다) 이 프로브의 회차는 다시 돌리지 않았다"로 고쳤다.
  - `tests/core/test_run.py`의 `DuplicateTools` 사례: 문서가 "도구와 두 서버 이름"을 든다고 쓰는데 서버 이름만 단언했다. 도구 이름 `add`의 단언을 더했다.
  - `tests/adapters/test_mcp.py`에 `test_겹친_서버_뒤의_서버는_열리지_않는다`를 더했다. 모듈 독스트링과 `adapters.md`가 단언하는데 시험이 없던 문장("겹친 서버 뒤의 서버는 열리지 않는다")이다. 셋째 서버를 띄울 수 없는 명령으로 두어, 열렸다면 `ConnectionError`가 난다. 빨강은 변이로 봤다: `mcp.py`의 `if earlier is not None:`을 `… and False:`로 손으로 바꿔 이 시험과 앞의 겹침 시험이 모두 빨개지는 것을 봤고(새 시험은 `ConnectionError: MCP 서버 third(...)에 붙지 못했다`), 되돌려 초록을 다시 봤다(`tools/mutate.py`가 아니라 손으로 한 변이다).
- **남긴 것과 이유.**
  - `FakeConnection`·`FakeTools`의 `owners` 인자(쓰는 시험 없음): 티켓이 "가짜 연결은 도구마다 서버 이름을 들고, 적지 않으면 기본 서버 이름 하나를 쓴다"를 요구했다. 두 보고가 서로 반대로 짚었다(명세 축은 범위 넘침으로, 같은 축의 다른 지적은 "같은 규약"이 반만 참이라고). 요구의 글자를 따라 core 가짜에만 두고, router·end_user는 기본 서버만 쓴다. 04가 도구마다 서버를 달리 줄 때 처음 쓴다.
  - `DEFAULT_SERVER`가 세 시험 파일에 따로 있는 것(Duplicated Code 판단 항목): 티켓이 세 가짜가 같은 규약을 쓰게 하라 했고 세 시험 파일은 서로를 import하지 않는다. 공용 상수는 04의 재량으로 둔다.
  - 한 서버 안에서 같은 이름이 겹치면 `(x, x)`로 던지는 갈래(Nit): MCP가 한 서버 안의 이름 겹침을 막는지는 확인하지 않았고, 동작은 안전한 쪽(실패)이다. 문구와 문서가 "서버들이 같은 이름의 도구를 내면"이라 이 갈래를 말하지 않는다. 시험은 더하지 않았다.
  - `McpTools.connect` 독스트링이 같은 이름 검사의 실패를 말하지 않는 것(Nit): 모듈 독스트링과 `adapters.md`·`core.md`에 있다.
- **다시 돌린 명령.** 새 시험 셋은 초록이다(`uv run pytest tests/adapters/test_mcp.py -q -k "겹친_서버 or 같은_이름 or 도구_명세는"` 3 passed, `tests/core/test_run.py -k 같은_이름의_도구` 1 passed). 린트·형식은 `ruff format`을 시험 파일 둘에 쳤다. 전체 검증 명령은 커밋이 부르는 pre-commit으로 갈음한다(결과는 커밋 뒤).

## PR 직전 리뷰 (CodeRabbit CLI 대신 대체 둘)

`coderabbit auth status`가 `Seat: not assigned`(`Plan: Free`)라 CLI를 돌리지 못했다. 대체 둘인 `bug-perf-review` 서브에이전트와 내장 `/security-review`를 나란히 돌렸다.

- **`/security-review`**: 지적 없음. 같은 이름 검사는 서버가 다른 서버의 도구를 덮어쓰던 길을 막는 쪽이고, 오류 문구에 서버가 낸 도구 이름이 실리는 것은 로그 스푸핑 범주라 제외 대상이다(이 세션이 diff의 실행 코드 둘을 읽고 판정했다. 하위 작업으로 가르지 않았다).
- **`bug-perf-review`**: Critical·Major 0, Minor 1, 오탐 2. 서브에이전트가 어댑터 시험 22개를 돌려 통과를 봤다고 보고했다(보고의 말이고 이 세션이 다시 돌린 것이 아니다).
  - **유효(Minor), 고쳤다.** `.scratch/web-admin/probes/probe_stale_decision.py`와 `.scratch/web-widget/probes/event_timing.py`가 `ToolSpec`을 `server=` 없이 만든다. 이 세션이 `ToolSpec(` grep으로 두 줄을 확인했다. pyright·pytest 범위 밖이라 게이트에 잡히지 않는다. 두 곳에 `server=PluginName("probe")`를 더했다(`PluginName`은 두 파일이 이미 불러온다). 두 프로브를 다시 돌리지는 않았다.
  - **오탐.** 셋 이상이 겹칠 때 문구에 처음 겹친 둘만 드는 것은 문서에 적힌 의도다. 겹침을 던지기 전에 열린 서버는 `AsyncExitStack`이 닫는다.
  - **남은 한계.** core 시험의 `DuplicateTools`는 가짜가 `ValueError`를 직접 던지는 것이라 어댑터와 core를 한 번에 잇는 시험은 없다. 이음새는 코드를 읽어 확인했고 함수로 부르지는 않았다.
