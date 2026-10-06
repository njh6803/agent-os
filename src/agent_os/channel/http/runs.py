"""실행을 앱의 수명에 묶는다. 요청은 그 실행의 이벤트를 받아 흘릴 뿐이다(ADR 0014).

**실행은 연결에 묶이지 않는다.** 라우트가 `run()` 을 그대로 흘리면 끊김에서 제너레이터가
취소되고, `CancelledError` 가 core 의 `except Exception` 을 지나쳐 `run_failed` 도 없이 도구를 반쯤
부른 실행이 남는다. 그래서 실행은 요청의 태스크가 아니라 앱의 수명이 연 태스크 그룹에서 돈다.
끊김이 취소하는 것은 그 요청의 태스크뿐이다.

**도는 실행은 등록부에 이름표가 달린다**(ADR 0023). 트레이스만으로는 도는 실행과 결말 없음을 가를 수
없어서, 앱이 지금 도는 실행을 `run_id` 로 안다. 실행 하나에 실황 하나 — 지금 받는 쪽들(시작·결정
응답의 연결, 구독 연결)의 송신 흐름 목록이다. 실행의 태스크가 이벤트를 받으면 그 트레이스 인덱스를
붙여 모든 흐름에 넣고, 실행이 끝나면 흐름을 닫고 등록부에서 뺀다. 실행이 스스로 등록부를 떠나는
자리는 그 하나다. 그 밖에 이름표가 바뀌는 때는 하나 — 멈춘 실행이 도구 연결을 닫는 사이에 그
실행의 재개가 와 같은 식별자로 새 실황을 다는 때다(`Runs._drive`). 포트가 아니다 — 프로세스
메모리이고 앱을 다시 시작하면 비어 있다(ADR 0012).

**인덱스는 그 이벤트가 트레이스에 쓰인 줄의 자리다.** `run()` 이 낸 첫 이벤트(`run_started`)가 0
이고, `resume()` 이 낸 첫 이벤트(결정)는 `pause_index + 1` 이다 — core 가 `pause_index` 를 마지막
이벤트의 자리로 확인했다(ADR 0014 의 2026-09-28 이력). 그 뒤로 하나씩 는다. core 는 이벤트를
트레이스에 쓴 뒤 내고, 이 모듈은 받은 이벤트를 await 없이 흐름에 넣는다. 그래서 실행의 태스크가
멈춰 있는 동안에는 그 태스크가 트레이스에 쓴 이벤트가 전부 이미 실황에 들어가 있다(재개한 실행의
실황은 결정부터이고 그 앞은 트레이스에만 있다). 구독이 트레이스 읽기와
등록부 보기를 await 없이 한 걸음에 하면 빠짐도 중복도 없는 것이 이것 하나에 기댄다.

**실행은 받는 쪽을 기다리지 않는다.** 실행과 받는 쪽 사이는 연결마다 1,000 프레임까지 쌓이는
흐름이고(`BACKLOG_FRAMES`, ADR 0023) 실행은 기다리지 않고 넣는다. 받는 쪽이 떠났거나 그만큼
뒤처졌으면 그 흐름만 닫고 버린다. 받는 쪽은 쌓인 것을 다 받은 뒤 결말 없이 끝난 스트림을 보고,
최종 사용자는 구독으로 다시 붙고 운영자는 트레이스로 이어 본다. 버려도 잃는 것이 없다 — 흐름에 넣는
이벤트는 core 가 이미 트레이스에 쓴 것이다. 크기가 제한된 흐름에 기다리며 넣으면 느린 수신자 하나가
실행을 세운다. 바이트는 세지 않는다 — 최종 사용자 항목은 프롬프트와 도구 결과를 싣지 않아 작고,
운영자 채널의 큰 프레임(첫 턴의 프롬프트)은 실행마다 하나라 1,000 개가 쌓이는 자리가 아니다
(end-user-channel 명세 "백로그"). 운영자 채널(`/runs`)도 같은 값이다.

**최종 사용자 경로의 실행은 동시 실행의 칸 하나를 차지한다**(`limits` 모듈). 칸의 입장과 반환은 이
등록부 한 곳이 소유한다. 입장은 실행을 수명에 넘기는 자리(`Runs.start`)에서 상한을 보고 칸을
차지하는 것이고 await 없이 한 걸음이다 — 동시 요청 둘이 마지막 칸을 함께 차지하지 못한다. 반환은
실행의 태스크가 끝나는 한 자리에서 꼭 한 번이다. 첫 이벤트 전의 실행 전 실패(404·409·500 으로 답하는
것 전부), 결말(끝남·실패·일시정지), 타임아웃, 앱 종료의 취소가 모두 그 자리를 지난다. 시작·결정
응답의 연결이 끊긴 것은 반환이 아니다 — 실행은 계속 돈다. 칸을 돌려주는 것과 실행이 끝나 흐름을
닫는 것 사이에 await 가 없으므로, 그렇게 닫힌 스트림의 끝을 본 받는 쪽이 곧바로 보낸 다음 요청은
그 칸을 쓸 수 있다. 백로그로 잘린 흐름은 실행이 아직 돌고 있어 칸을 쥔 채 끝난다.

**앱이 멈추면 실행을 기다리지 않고 취소한다.** 그 실행은 결말 없음이다. core 의 트레이스 쓰기가
동기라 취소가 반쪽 줄을 남기지 않는다. 실행 하나가 통째로 한 태스크에서 돌므로 도구 연결도 그
태스크 안에서 열리고 닫히고, MCP 어댑터의 anyio 취소 범위가 진입과 종료를 같은 태스크에서 본다.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TextIO

import anyio
from anyio.abc import TaskGroup
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream

from agent_os.channel.http.limits import RunQuota, Seat
from agent_os.core.ports import Clock
from agent_os.http.sites import EndUser
from agent_os.sdk import Event, RunId

# 받는 쪽 하나의 흐름에 쌓일 수 있는 이벤트의 수(모듈 독스트링). 넘으면 그 흐름만 닫는다. 값은
# 어림이다 — 실행 하나가 내는 이벤트는 루프 상한(10턴)에 턴마다 도구 호출 수를 곱한 정도라 보통
# 수십이고, 받는 쪽이 이만큼 뒤처진 것은 떠난 것과 같다. 다시 볼 조건은 메모리가 실제로 문제가 될
# 때다(end-user-channel 명세 "백로그").
BACKLOG_FRAMES = 1_000


@dataclass(frozen=True)
class Indexed:
    """트레이스 인덱스를 단 이벤트 하나. 인덱스는 그 이벤트가 트레이스에 쓰인 줄의 자리다."""

    index: int
    event: Event


# 두 태스크가 함께 도는 사이라 반환값으로 건넬 수 없어 칸 하나를 둔다. 실행의 태스크가 한 번 적고
# 요청의 태스크가 한 번 읽는 통로이고, 흐름을 닫기 전에 적으므로 요청 쪽이 흐름의 끝을 본 때에는
# 언제나 적혀 있다. 흐름에 싣지 않는 이유는 흐름의 항목이 인덱스를 단 이벤트 하나로 남아야 받는 쪽이
# 갈래 없이 읽기 때문이다. anyio 의 `TaskGroup.start` 가 같은 일을 하지만 넘긴 값이 `Any` 로 돌아와
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

    def __init__(self, first: Indexed, rest: MemoryObjectReceiveStream[Indexed]) -> None:
        self._first = first
        self._rest = rest

    @classmethod
    async def opened(
        cls, rest: MemoryObjectReceiveStream[Indexed], failure: _PreRunFailure
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

    async def items(self) -> AsyncIterator[Indexed]:
        """첫 이벤트부터 결말까지. 받는 쪽이 떠나 이 제너레이터가 닫히면 흐름도 닫힌다."""
        with self._rest:
            yield self._first
            async for item in self._rest:
                yield item


class _Live:
    """도는 실행 하나의 실황. 지금 받는 쪽들의 송신 흐름 목록이다."""

    def __init__(self) -> None:
        self._sends: list[MemoryObjectSendStream[Indexed]] = []

    def join(self) -> MemoryObjectReceiveStream[Indexed]:
        """받는 쪽 하나를 더하고 그 수신 흐름을 돌려준다. 그 뒤에 넣는 것부터 받는다."""
        send, receive = anyio.create_memory_object_stream[Indexed](BACKLOG_FRAMES)
        self._sends.append(send)
        return receive

    def offer(self, item: Indexed) -> None:
        """기다리지 않고 모든 받는 쪽에 넣는다. 떠난 쪽과 백로그가 찬 쪽은 그 흐름을 닫고 버린다 —
        그 이벤트는 트레이스에 있다. 남은 받는 쪽은 그대로 받는다."""
        for send in tuple(self._sends):
            try:
                send.send_nowait(item)
            except (anyio.BrokenResourceError, anyio.WouldBlock):
                self._sends.remove(send)
                send.close()

    def close(self) -> None:
        """받는 쪽 전부에 끝을 알린다. 그들이 흐름의 끝을 본다."""
        for send in self._sends:
            send.close()
        self._sends.clear()


class Runs:
    """앱의 수명이 소유하는 실행들과 그 등록부. 수명이 열려 있는 동안만 실행을 받는다.

    실행 하나의 실패가 수명 전체로 번지지 않게 실행의 태스크가 예외를 스스로 받는다. 태스크 그룹은
    자식 하나의 예외에 형제 전부를 취소하므로, 그대로 두면 디스크 오류 하나가 다른 실행들과 앱의
    수명을 함께 끝낸다. 첫 이벤트 전의 예외는 요청이 상태 코드로 말하고, 그 뒤의 것은 결말 없이
    닫힌 스트림과 서버 기록 한 줄로 남는다.
    """

    def __init__(
        self, *, stderr: TextIO, clock: Clock, end_user_concurrent_runs: int | None
    ) -> None:
        self._stderr = stderr
        self._group: TaskGroup | None = None
        self._live: dict[RunId, _Live] = {}
        self._quota = RunQuota(clock=clock, concurrent_runs=end_user_concurrent_runs)

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

    async def start(
        self,
        events: AsyncIterator[Event],
        *,
        request_id: str,
        first_index: int,
        end_user: EndUser | None,
    ) -> RunStream:
        """실행 하나를 수명에 넘기고 첫 이벤트를 기다린다. 첫 이벤트 전의 예외는 여기서 다시 던진다.

        `first_index` 는 그 실행이 낼 첫 이벤트의 트레이스 인덱스다(모듈 독스트링). 수명이
        열리지 않았으면 실행을 받지 않는다. 받으면 그 실행을 소유할 것이 없어 요청의 태스크에
        묶이고, 그것이 이 모듈이 막으려는 모양이다. 추적 식별자는 실행이 도중에 멈췄을 때 그 기록을
        클라이언트가 받은 `X-Request-Id` 와 잇는다. 응답의 연결은 실황의 첫 받는 쪽이다.

        `end_user` 는 최종 사용자 경로의 실행이면 그 신원이고 운영자 채널은 없음이다. 있으면 실행을
        넘기기 전에 상한을 보고 칸을 차지한다 — 걸리면 `LimitExceeded` 이고 실행은 시작되지 않아
        core 에 닿지 않는다. 검사와 차지와 넘김 사이에 await 가 없다.
        """
        group = self._group
        if group is None:
            raise RuntimeError("앱의 수명이 열리지 않아 실행을 받을 수 없다")
        seat = None if end_user is None else self._quota.take(end_user)
        live = _Live()
        receive = live.join()
        failure = _PreRunFailure()
        group.start_soon(self._drive, events, live, failure, request_id, first_index, seat)
        return await RunStream.opened(receive, failure)

    def join(self, run_id: RunId) -> MemoryObjectReceiveStream[Indexed] | None:
        """도는 실행이면 그 실황에 받는 쪽 하나를 붙여 수신 흐름을 돌려주고, 아니면 없음이다.

        await 가 없다. 구독이 트레이스를 읽고 이것을 부르는 사이에 await 가 없어야, 그 사이에 실행이
        이벤트를 내 빠지거나 두 번 나가지 않는다(ADR 0023). 붙은 받는 쪽은 그 뒤에 쓰이는 이벤트부터
        받고 실행이 끝나면 흐름의 끝을 본다.
        """
        live = self._live.get(run_id)
        return None if live is None else live.join()

    async def _drive(
        self,
        events: AsyncIterator[Event],
        live: _Live,
        failure: _PreRunFailure,
        request_id: str,
        first_index: int,
        seat: Seat | None,
    ) -> None:
        """실행을 결말까지 몬다. 받는 쪽이 떠나도 멈추지 않는다.

        **이벤트와 이벤트 사이에 await 하지 않는다.** core 는 도구 연결과 실행 타임아웃의
        anyio 취소 범위 안에서 yield 한다. 그 사이의 await 에서 앱이 멈추며 취소를 받으면
        제너레이터가 취소 범위 안에 멈춘 채 남고, 나중에 다른 태스크가 그것을 닫아 태스크 그룹이
        깨진다(스크래치 프로브로 쟀다). await 없이 넣으면 취소는 제너레이터가 스스로 기다리는
        자리에만 닿아 범위를 따라 풀린다.
        같은 이유로 첫 이벤트를 받은 자리와 등록부에 다는 자리 사이에도 await 가 없다.

        등록부에는 첫 이벤트로 실행 식별자를 안 뒤에 단다. 같은 식별자의 이름표가 이미 있으면(멈춘
        실행이 도구 연결을 닫는 사이에 그 실행의 재개가 온 것이다) 새 실황으로 바꾸고, 뗄 때는 자기
        실황일 때만 뗀다. 앞 실황에 붙어 있던 받는 쪽은 그 실행의 끝을 이미 트레이스에 둔 것이다.

        첫 이벤트 뒤의 예외는 core 가 이벤트를 트레이스에 쓰지 못한 것뿐이다. 나머지는 core 가
        `run_failed` 로 바꾼다. 그 실행은 결말 없음이고 받는 쪽은 결말 없이 닫힌 스트림을 본다.

        최종 사용자 경로의 칸은 바깥 `finally` 에서 돌려준다. 실행 전 실패도 결말도 앱 종료의
        취소도 이 태스크가 끝나는 자리라 꼭 한 번이다. 흐름을 닫는 것과 await 없이 한 걸음이다
        (모듈 독스트링). 취소된 태스크의 `finally` 라 여기서 await 하면 그 자리에서 다시 취소된다.
        """
        try:
            first = await _take_first(events)
            if isinstance(first, Exception):
                failure.error = first
                return
            self._live[first.run_id] = live
            try:
                await _offer_all(first, events, live, first_index)
            except Exception as error:
                self._stderr.write(_interruption(request_id, first, error))
            finally:
                if self._live.get(first.run_id) is live:
                    del self._live[first.run_id]
        finally:
            if seat is not None:
                self._quota.give_back(seat)
            live.close()


async def _take_first(events: AsyncIterator[Event]) -> Event | Exception:
    """첫 이벤트, 또는 그 전에 난 예외. 실행 전 실패는 core 가 첫 yield 앞에서 던진다."""
    try:
        first = await anext(events, None)
    except Exception as error:
        return error
    return first if first is not None else RuntimeError("실행이 이벤트 없이 끝났다")


async def _offer_all(
    first: Event, events: AsyncIterator[Event], live: _Live, first_index: int
) -> None:
    """첫 이벤트부터 결말까지 인덱스를 붙여 넣는다. 이벤트 사이에 await 가 없다 — `Runs._drive`."""
    index = first_index
    live.offer(Indexed(index, first))
    async for event in events:
        index += 1
        live.offer(Indexed(index, event))


def _interruption(request_id: str, first: Event, error: Exception) -> str:
    """실행이 도중에 멈췄다는 서버 기록 한 줄(질의). 요청 실패의 줄과 같이 추적 식별자를 든다."""
    name = type(error).__name__
    return f"실행 중단: request_id={request_id} run_id={first.run_id} {name}: {error}\n"
