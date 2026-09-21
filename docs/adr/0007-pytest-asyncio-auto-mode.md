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
- 경고 전부를 에러로 올리지는 않는다. langchain과 프로바이더 SDK의 deprecation 경고가 우리 잘못이 아닌 이유로 스위트를 빨갛게 만들기 때문이다. 좁혀서 `RuntimeWarning` 하나만 올린다.
