# 2026-09-21 · 인터럽트 03: 게이트에서 멈춘다

인터럽트 슬라이스의 셋째 티켓. 여기서 처음 기능이 데모 가능해진다. `requires_approval`을 단
에이전트를 돌리면 승인 대상 도구 직전에 실행이 `run_paused`로 끝나고, CLI가 실행 식별자와 승인
요청을 찍고 전용 종료 코드로 끝난다. `/implement`로 새 세션에서 시작했고 브랜치는
`feature/03-pause-at-the-gate`. 이음매는 명세가 정한 둘, `core`의 `run()`과 CLI 표면이다.
sdk 계약은 건드리지 않았다.

## 한 것

- **도구 호출 길을 하나로.** 루프(`loop.py`)가 `ToolConnection`을 받아 스스로 도구를 부르던 것을
  컨텍스트의 호출 함수 하나(`ToolCaller`)를 받게 바꿨다. 게이트, 마스킹, 기록이 `_Context._call`
  한 자리에 있어 모델이 부르든 에이전트가 `ctx.tool()`로 직접 부르든 같은 정책을 지난다. 명세의
  "정책은 도구에 붙지 경로에 붙지 않는다"를 구조로 만든 것이다. 두 파일에 따로 있던 `_call_safely`
  중복도 하나로 줄었고, 01이 보류한 "`on_tool_call` 원시값 묶기"는 콜백이 사라져 닫혔다.
- **일시정지 신호.** 승인 대상을 만나면 컨텍스트가 `run_paused`를 쌓고 `_Paused`를 올린다.
  `BaseException`에서 파생한 이유는 `asyncio.CancelledError`와 같다. 플러그인의 `except Exception`이
  삼키면 도구는 안 불렸는데 사람에게 묻지도 않은 채 성공으로 끝나는 조용한 실패가 된다. 삼키거나
  다른 예외로 감싸도 컨텍스트가 그 뒤의 모델·도구 호출을 하지 않고 실행 조립부가 뒤따르는 이벤트와
  예외를 통과시키지 않는다. `SwallowingAgent`와 `WrappingAgent` 테스트가 그 최악의 플러그인 둘이다.
  `ctx.paused`는 읽기 전용 property 라 플러그인이 되돌릴 수 없다. 실행 조립부는 신호를 `async with tools.connect`
  안에서 받아 연결을 정상으로 닫는다. 신호가 MCP 어댑터의 `__aexit__`를 지나며 anyio 가 감쌀
  여지를 두지 않기 위해서다.
- **도구 연결 직후 실재 검사.** `requires_approval`이 가리키는 도구, `secret_args`가 가리키는
  도구와 인자(JSON Schema `properties`의 키)가 실재하지 않으면 `LookupError`로 실행이 실패하고
  트레이스가 남는다. 인자 검사는 `properties`가 없는 스키마에서도 fail-closed 다. 이름 있는 인자가
  없는 도구에 비밀 인자를 선언한 것은 오타이기 때문이다.
- **CLI.** `run_paused`를 받으면 표준 출력에 `일시정지: <run_id>`, `도구:`, `인자:`(JSON) 셋을
  찍고 종료 코드 3으로 끝난다. 2는 argparse 가 인자 오류에 쓰므로 피했다. 재개 명령 안내는 04가
  명령을 만들 때 붙인다. 지금 찍으면 없는 명령을 안내하게 된다.
- `.claude/rules/core.md`의 실패 정책 줄과 게이트 줄을 코드와 같은 커밋에서.

## 테스트를 고친 것

실재 검사가 켜지면서 기존 테스트 다섯이 빨개졌다. 전부 가짜 도구에 인자 스키마가 없거나
(`{}`), 실재하지 않는 도구(`read_inbox`, `send_email`, `other`)에 선언을 걸어 두고 있었다. 명세가
그 상태를 실패로 정했으므로 실재하는 도구와 인자를 선언하도록 고쳤다. `FakeTools`에 도구별 인자
이름(`params`)이 생긴 것이 그 결과다. `test_model.py`의 루프 직접 호출 둘도 새 시그니처로.

CLI 일시정지 테스트는 진짜 stdio MCP 서버(`tests/adapters/mcp_fixture_server.py`)를 임시
디렉터리의 mcp 플러그인으로 등록해 돈다. 게이트가 도구 앞에서 멈추므로 서버는 붙기만 하고
불리지 않는다. 모델은 안 쓴다. mcp 의 `stdio_client`가 `errlog=sys.stderr`를 정의 시점에 묶어
`capsys`와 충돌하지 않는 것을 소스로 먼저 확인했다.

## TDD 의 모양

첫 테스트(모델 경로의 일시정지) 하나만 red 였고 나머지 여섯(직접 호출, 한 턴에 둘, 삼키는
에이전트, 실재 검사 셋)은 붙이자마자 초록이었다. 첫 슬라이스를 만들 때 이미 여섯을 염두에 둔
구현을 했기 때문이다. 수직 슬라이스를 어긴 것이라 적어 둔다. 대신 여섯이 각각 다른 행동을 판정
하므로 남긴다.

## 셀프 리뷰

두 축이 Minor 여섯을 냈고 넷을 고쳤다. 표준 축: 출력의 "승인 대기"가 용어집 피할 말("대기")이라
"일시정지"로, `reject`와 `refuse`가 섞인 것을 `_stay_paused`로, `ctx.paused`가 공개 가변 속성이라
플러그인이 `ctx.paused = False`로 되돌릴 수 있던 것을 읽기 전용 property 로. 명세 축: 신호를 자기
예외로 감싸 올리는 에이전트에서 `run_paused` 뒤에 `run_failed`가 덧붙던 것. 04가 "마지막 이벤트가
`run_paused`인가"로 재개 가능을 판정하면 그 실행이 재개 불가가 된다. 멈춘 뒤 올라온 예외는 조립부가
삼킨다. `WrappingAgent` 테스트를 먼저 빨갛게 보고 고쳤다.

명세 두 줄도 고쳤다. "마스킹된 인자는 마스킹된 채로 보인다"는 금지 규칙 때문에 도달 불가능한
요구가 되었고, CLI 테스트의 "모델도 도구도 쓰지 않는다"는 실재 검사가 도구 목록을 요구해 진짜
stdio 서버를 붙이게 되었다. 둘 다 새 결정이 아니라 사실 기록이라 명세에 날짜와 함께 적었다.

남긴 것 넷, 전부 Nit 이다. `approvals`·`secrets`가 함께 다니는 것(04가 재개에 정책 묶음이 실제로
필요할 때), `_reject_unknown_declarations`의 같은 모양 셋, `FakeConnection`의 병렬 매핑 둘, `break`
뒤 에이전트 제너레이터를 `aclose()`하지 않는 것(계약 타입이 `AsyncIterator`라 `aclose`를 보장하지
않고, 에이전트의 `finally`가 도구를 불러도 `_stay_paused`가 막는다).

## PR 직전 CodeRabbit CLI

3건, 유효 3. 둘을 고쳤고 하나는 이미 열린 문제다.

- **Major, 연결 정리 실패가 일시정지를 덮어쓴다.** `finally`가 `run_paused`를 흘린 뒤 `async with`를
  나가며 `__aexit__`가 터지면 그 예외는 `try` 밖이라 `run()`이 `run_failed`를 덧붙였다. MCP 어댑터의
  anyio 취소 범위가 실제로 이렇게 터지는 것을 ADR 0007 이력이 적어 두었으니 이론이 아니다.
  `FlakyCloseTools`로 빨갛게 보고 고쳤다.
- **Major, 위조 `RunPaused`.** 에이전트가 게이트를 거치지 않고 `RunPaused`를 지어내 마지막에 yield
  하면 `isinstance(last, RunPaused)` 판정이 속아 정상 일시정지로 쳤다. 04가 그 `tool`·`args`를 승인
  대상으로 믿게 되는 자리다. 판정을 이벤트 종류가 아니라 런타임이 실제로 게이트를 통과시켰는지
  (`ctx.paused`를 조립부가 `nonlocal`로 넘겨받은 것)로 바꿨다. `ForgingAgent`로 빨갛게 보고 고쳤다.
  둘을 한 플래그가 닫는다. 남는 물음 하나는 에이전트가 런타임 소유 이벤트(`run_started`,
  `run_paused`, `run_failed`)를 아예 못 내게 타입으로 가를 것인가다. `ChattyAgent`가 `tool_called`를
  지어내는 기존 관행과 "다른 이벤트는 그대로 통과한다"는 규칙에 닿는 계약 변경이라 이번에 하지
  않는다. 04가 재개 입력을 신뢰하는 자리를 만들 때 ADR 후보로 올린다.
- **Critical, 도구 결과 `content`에 비밀이 실릴 수 있다.** 맞지만 ADR 0009의 2026-09-21 이력이 이미
  열린 문제로 적고 결정을 미룬 것이다. 이번 diff가 만든 갭이 아니라 보류.

## 검사

`pytest` 156 passed, `ruff` check·format 통과, `pyright` 49파일 0 errors(`filesAnalyzed`로 먼저
확인), `lint-imports` 3 kept. 옛 이름(`on_tool_call`, `NoTools`) 잔존은 살아 있는 트리에서 0이다.
남은 것은 사람이 지울 옛 워크트리 둘뿐이다.

## 다음

- 커밋 뒤 `/code-review`, PR 직전 `coderabbit-review`, `/git-pr`, `@coderabbitai review`,
  `/git-pr-feedback`, `/git-pr-merge`. 병합은 이 세션이 한다.
- 다음 티켓은 04(승인하고 재개한다). 새 세션에서 시작한다. 04가 이어받는 것:
  - 게이트는 `_Context._call` 한 자리다. 재생 구간의 도구 호출도 그 자리를 지나야 "재개 뒤 둘째에서
    다시 멈춘다"가 성립한다. 재생기는 `_call`과 `llm()`의 안쪽(실제 포트 호출)만 바꾸면 된다.
  - `_Paused`는 `BaseException`이고 `execute()` 안에서만 잡힌다. `resume()`이 `run()`과 내부를
    공유한다면 같은 조립부를 쓴다.
  - 실재 검사 `_reject_unknown_declarations`는 연결 직후이고 재개에서도 같은 자리에서 돈다.
    승인을 기다리는 사이 매니페스트가 바뀌었으면 여기서 먼저 걸린다.
  - CLI 의 승인 요청 출력에 `agent-os resume` 안내 줄을 붙이는 것은 04가 명령을 만들 때다.
- 워크트리 `.claude/worktrees/`의 옛 둘은 여전히 사람이 지운다.
