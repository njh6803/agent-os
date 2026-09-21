---
status: accepted
date: 2026-09-21
---

# 비동기 테스트는 pytest-asyncio auto 모드로 돌린다

첫 슬라이스의 주 이음매는 포트 다섯을 주입받는 core의 실행 함수이고, 그중 ToolSource는 시작과 종료의 수명을 가진다. 테스트마다 `asyncio.run()`으로 이벤트 루프를 직접 돌리는 지금 방식으로는 async 픽스처를 만들 수 없어서 그 수명 관리가 테스트 본문마다 반복된다. pytest-asyncio를 dev 의존성으로 더하고 `asyncio_mode = "auto"`로 둔다. 테스트는 `async def`로 쓰고 데코레이터도 마커도 import도 없다.

## Considered Options

- **`asyncio.run()` 유지.** 의존성이 늘지 않고 ADR도 필요 없다. 대신 async 픽스처가 불가능해 수명 있는 포트를 테스트마다 열고 닫아야 하고, 래퍼 함수와 본문 함수로 쪼개져 테스트가 행동을 그대로 읽히게 쓰기 어렵다. 이 비용은 슬라이스마다 반복되고 슬라이스 2의 HTTP 채널에서 더 커진다.
- **anyio의 pytest 플러그인.** anyio 4.15.1이 이미 전이 의존성으로 있어 설치가 없다. 그러나 선언하지 않은 전이 의존성에 직접 기대는 것이고, 백엔드 픽스처와 마커가 추가로 든다.

## Consequences

- dev 의존성이 하나 는다. 해석 결과 pytest-asyncio 1.4.0이 pytest 9.1.1과 충돌 없이 설치되고 추가 전이 의존성은 없다(2026-09-21 실측).
- 기존 `sdk` 테스트의 `asyncio.run` 사용을 같은 티켓에서 바꾼다. 한 저장소에 두 방식을 두지 않는다.
- `asyncio.run`을 빼먹은 코루틴은 pyright strict가 잡지 못하고 pytest는 `RuntimeWarning`만 내며 통과한다(2026-09-21 실측). auto 모드는 실행기를 붙이는 단계 자체를 없애 이 실패 양식을 지우지만, `await`를 빼먹는 쪽은 남는다. 그래서 pytest 설정에서 `RuntimeWarning`을 에러로 올린다. 원칙 II의 근거다.
- **anyio 취소 범위를 쓰는 어댑터는 async 픽스처로 열 수 없다(2026-09-21 실측, 티켓 07).** pytest-asyncio는 async generator 픽스처의 setup과 teardown을 서로 다른 태스크에서 돌린다. MCP의 stdio 클라이언트는 anyio 태스크 그룹이라 들어간 태스크에서 나가야 하고, 픽스처 teardown에서 `Attempted to exit cancel scope in a different task than it was entered in`으로 터진다. 이 ADR이 auto 모드를 고른 이유였던 "수명 있는 포트를 async 픽스처로 연다"는 우리 가짜(순수 파이썬)에는 맞고 anyio 기반 어댑터에는 맞지 않는다. 그런 어댑터는 테스트 본문에서 `async with`로 열고 닫는다. 같은 이유로 core의 `run()`(async generator 안의 `async with tools.connect()`)은 소비자가 한 태스크에서 끝까지 돌려야 하고, 중간에 버리면 finalizer 태스크에서 닫히며 같은 오류가 난다. 슬라이스 2의 HTTP 채널이 클라이언트 연결 끊김을 다룰 때 이것을 먼저 본다.
- **`RuntimeWarning` 하나만으로는 부족했다(2026-09-21 실측, 티켓 01).** `await` 누락 경고는 코루틴이 GC될 때 터지는 unraisable 예외라서, `error::RuntimeWarning`만 두면 pytest가 그것을 `PytestUnraisableExceptionWarning`으로 감싸 테스트가 그대로 통과한다. `error::pytest.PytestUnraisableExceptionWarning`을 같이 올려야 실제로 빨개진다. 설정이 그럴듯해 보이는 것과 검사가 도는 것은 다르다는 것을 일부러 await를 뺀 테스트로 확인했다.
- 경고 전부를 에러로 올리지는 않는다. langchain과 프로바이더 SDK의 deprecation 경고가 우리 잘못이 아닌 이유로 스위트를 빨갛게 만들기 때문이다. 좁혀서 `RuntimeWarning` 하나만 올린다.
