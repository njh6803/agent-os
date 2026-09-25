"""실행을 앱의 수명에 묶는다. 요청은 그 실행의 이벤트를 받아 흘릴 뿐이다(ADR 0014).

**실행은 연결에 묶이지 않는다.** 라우트가 `run()` 을 그대로 흘리면 끊김에서 제너레이터가
취소되고, `CancelledError` 가 core 의 `except Exception` 을 지나쳐 `run_failed` 도 없이 도구를 반쯤
부른 실행이 남는다. 그래서 실행은 요청의 태스크가 아니라 앱의 수명이 연 태스크 그룹에서 돈다.
끊김이 취소하는 것은 그 요청의 태스크뿐이다.

**실행은 받는 쪽을 기다리지 않는다.** 둘 사이는 크기 제한이 없는 흐름 하나이고 실행은 기다리지 않고
넣는다. 받는 쪽이 느리면 쌓이고 떠나면 버린다. 버려도 잃는 것이 없다 — 흐름에 넣는 이벤트는 core 가
이미 트레이스에 쓴 것이다. 상한을 두지 않는 이유는 쌓이는 양이 그 실행이 낸 이벤트만큼이고 실행이
끝나거나 받는 쪽이 떠나면 사라지기 때문이다. 여러 실행이 겹친 합은 범위 밖에 둔 동시 실행 상한의
문제다(명세 Further Notes). 크기가 제한된 흐름에 기다리며 넣으면 느린 수신자 하나가 실행을 세운다.

**앱이 멈추면 실행을 기다리지 않고 취소한다.** 그 실행은 결말 없음이다. core 의 트레이스 쓰기가
동기라 취소가 반쪽 줄을 남기지 않는다. 실행 하나가 통째로 한 태스크에서 돌므로 도구 연결도 그
태스크 안에서 열리고 닫히고, MCP 어댑터의 anyio 취소 범위가 진입과 종료를 같은 태스크에서 본다.
"""

from __future__ import annotations

import math
from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TextIO

import anyio
from anyio.abc import TaskGroup
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream

from agent_os.sdk import Event


# 두 태스크가 함께 도는 사이라 반환값으로 건넬 수 없어 칸 하나를 둔다. 실행의 태스크가 한 번 적고
# 요청의 태스크가 한 번 읽는 통로이고, 흐름을 닫기 전에 적으므로 요청 쪽이 흐름의 끝을 본 때에는
# 언제나 적혀 있다. 흐름에 싣지 않는 이유는 흐름의 항목이 이벤트 하나로 남아야 계약의 스트림 항목과
# 같은 타입이기 때문이다. anyio 의 `TaskGroup.start` 가 같은 일을 하지만 넘긴 값이 `Any` 로 돌아와
# 첫 이벤트가 타입 없이 흐른다(원칙 III).
@dataclass
class _PreRunFailure:
    """실행이 첫 이벤트를 내기 전에 끝났다면 그 이유."""

    error: Exception | None = None

    def raised(self) -> Exception:
        """요청 쪽이 다시 던질 것(질의). 이유 없이 끝났으면 앱이 멈추며 그 실행을 취소한 것이다."""
        if self.error is not None:
            return self.error
        return RuntimeError("실행이 첫 이벤트를 내기 전에 끝났다")


class RunStream:
    """실행 하나를 받는 쪽 하나. 만들어졌을 때 첫 이벤트는 이미 받았다."""

    def __init__(self, first: Event, rest: MemoryObjectReceiveStream[Event]) -> None:
        self._first = first
        self._rest = rest

    @classmethod
    async def opened(
        cls, rest: MemoryObjectReceiveStream[Event], failure: _PreRunFailure
    ) -> RunStream:
        """첫 이벤트를 기다린다. 그 전에 실행이 끝났으면 그 이유를 요청의 태스크에서 다시 던진다.

        기다리다 요청이 취소되면 흐름을 닫아 실행이 더 넣지 않게 한다.
        """
        try:
            first = await anext(rest, None)
        except BaseException:
            rest.close()
            raise
        if first is None:
            rest.close()
            raise failure.raised()
        return cls(first, rest)

    async def events(self) -> AsyncIterator[Event]:
        """첫 이벤트부터 결말까지. 받는 쪽이 떠나 이 제너레이터가 닫히면 흐름도 닫힌다."""
        with self._rest:
            yield self._first
            async for event in self._rest:
                yield event


class Runs:
    """앱의 수명이 소유하는 실행들. 수명이 열려 있는 동안만 실행을 받는다.

    실행 하나의 실패가 수명 전체로 번지지 않게 실행의 태스크가 예외를 스스로 받는다. 태스크 그룹은
    자식 하나의 예외에 형제 전부를 취소하므로, 그대로 두면 디스크 오류 하나가 다른 실행들과 앱의
    수명을 함께 끝낸다. 첫 이벤트 전의 예외는 요청이 상태 코드로 말하고, 그 뒤의 것은 결말 없이
    닫힌 스트림과 서버 기록 한 줄로 남는다.
    """

    def __init__(self, *, stderr: TextIO) -> None:
        self._stderr = stderr
        self._group: TaskGroup | None = None

    @asynccontextmanager
    async def lifespan(self, app: object) -> AsyncGenerator[None]:
        """앱의 수명. 닫힐 때 남은 실행을 기다리지 않고 취소한다."""
        async with anyio.create_task_group() as group:
            self._group = group
            try:
                yield
            finally:
                self._group = None
                group.cancel_scope.cancel()

    async def start(self, events: AsyncIterator[Event], *, request_id: str) -> RunStream:
        """실행 하나를 수명에 넘기고 첫 이벤트를 기다린다. 첫 이벤트 전의 예외는 여기서 다시 던진다.

        수명이 열리지 않았으면 실행을 받지 않는다. 받으면 그 실행을 소유할 것이 없어 요청의 태스크에
        묶이고, 그것이 이 모듈이 막으려는 모양이다. 추적 식별자는 실행이 도중에 멈췄을 때 그 기록을
        클라이언트가 받은 `X-Request-Id` 와 잇는다.
        """
        group = self._group
        if group is None:
            raise RuntimeError("앱의 수명이 열리지 않아 실행을 받을 수 없다")
        send, receive = anyio.create_memory_object_stream[Event](math.inf)
        failure = _PreRunFailure()
        group.start_soon(self._drive, events, send, failure, request_id)
        return await RunStream.opened(receive, failure)

    async def _drive(
        self,
        events: AsyncIterator[Event],
        send: MemoryObjectSendStream[Event],
        failure: _PreRunFailure,
        request_id: str,
    ) -> None:
        """실행을 결말까지 몬다. 받는 쪽이 떠나도 멈추지 않는다.

        **이벤트와 이벤트 사이에 await 하지 않는다.** core 는 도구 연결의 anyio 취소 범위 안에서
        yield 한다. 그 사이의 await 에서 앱이 멈추며 취소를 받으면 제너레이터가 취소 범위 안에 멈춘
        채 남고, 나중에 다른 태스크가 그것을 닫아 태스크 그룹이 깨진다(스크래치 프로브로 쟀다).
        await 없이 넣으면 취소는 제너레이터가 스스로 기다리는 자리에만 닿아 범위를 따라 풀린다.

        첫 이벤트 뒤의 예외는 core 가 이벤트를 트레이스에 쓰지 못한 것뿐이다. 나머지는 core 가
        `run_failed` 로 바꾼다. 그 실행은 결말 없음이고 받는 쪽은 결말 없이 닫힌 스트림을 본다.
        """
        with send:
            first = await _take_first(events)
            if isinstance(first, Exception):
                failure.error = first
                return
            _offer(send, first)
            try:
                await _offer_rest(events, send)
            except Exception as error:
                self._stderr.write(_interruption(request_id, first, error))


async def _take_first(events: AsyncIterator[Event]) -> Event | Exception:
    """첫 이벤트, 또는 그 전에 난 예외. 실행 전 실패는 core 가 첫 yield 앞에서 던진다."""
    try:
        first = await anext(events, None)
    except Exception as error:
        return error
    return first if first is not None else RuntimeError("실행이 이벤트 없이 끝났다")


async def _offer_rest(events: AsyncIterator[Event], send: MemoryObjectSendStream[Event]) -> None:
    """나머지를 결말까지 넣는다. 이벤트 사이에 await 가 없다 — 이유는 `Runs._drive`."""
    async for event in events:
        _offer(send, event)


def _offer(send: MemoryObjectSendStream[Event], event: Event) -> None:
    """기다리지 않고 넣는다. 받는 쪽이 떠났으면 버린다 — 그 이벤트는 이미 트레이스에 있다."""
    try:
        send.send_nowait(event)
    except anyio.BrokenResourceError:
        pass


def _interruption(request_id: str, first: Event, error: Exception) -> str:
    """실행이 도중에 멈췄다는 서버 기록 한 줄(질의). 요청 실패의 줄과 같이 추적 식별자를 든다."""
    name = type(error).__name__
    return f"실행 중단: request_id={request_id} run_id={first.run_id} {name}: {error}\n"
