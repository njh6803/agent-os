"""모델마다 따로 준 HTTP 클라이언트가 닫히지 않은 채 놓일 때(질문 10)의 사례. `openai_compat.py`가
모아 돌린다.

후보 어댑터(`adapter_candidate.py`)는 모델을 만들 때마다 제 비동기 HTTP 클라이언트를 준다.
라이브러리가 주소별로 캐시해 나눠 쓰는 클라이언트는 둘째 이벤트 루프에서 실패하기
때문이다(`cases_request.py`의 `two_loops_*`). 대가로 그 클라이언트를 닫는 자리가 없다. core 는
실행을 준비할 때마다 모델을 만들고 실행이 끝나면 놓으므로, 놓인 모델의 연결이 어떻게 되는지 본다.

갈래는 클라이언트 둘과 놓이는 때 둘이다. 클라이언트는 라이브러리 기본값(쉬는 연결을 풀에 남긴다,
`keepalive_*`)과 지금 후보(쉬는 연결을 두지 않는다, `candidate_*`)다. 놓이는 때는 그 실행의 이벤트
루프가 아직 돌 때(`serve`의 실행)와 루프가 닫힌 뒤(시험이 `asyncio.run`이 끝난 뒤까지 모델을 쥔
경우)다. 한 루프에서 실행이 이어지는 모양은 `runs_in_one_loop`이 갈래 넷으로 본다.

`keepalive_released_*`의 표지는 셋이다. 그 루프에서 부른 호출이 답을 받았다, 놓기 직전 그
클라이언트의 연결 풀에 열린 연결이 하나 이상 있다(놓이는 순간 정리할 것이 실제로 있었다), 같은 갈래
안에서 탐지의 자기 시험이 잡힌다(`__del__`에서 예외를 내는 객체와 경고를 내는 객체를 놓으면 탐지가
둘 다 잡는다. 잡을 것이 있으면 잡는다는 양성 대조다). 결과는 모델을 놓은 뒤 잡힌 unraisable 예외와
경고의 목록이다. 경고는 모든 종류를 `always`로 받아, 파이썬의 기본 필터가 숨기는 `ResourceWarning`도
센다. 다른 사례의 표지는 그 사례의 독스트링이 적는다.

연결 풀은 비공개 속성(`root_async_client._client._transport._pool`)으로 읽는다. 측정의 표지로만 쓰고
어댑터가 기대는 것이 아니다. 서버 쪽의 연결 수는 `fake_server.py`의 `opened_connections`와
`closed_connections`다. 그 서버는 쉬는 연결을 스스로 닫지 않는다.
"""

from __future__ import annotations

import asyncio
import gc
import sys
import time
import warnings
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass, field

import anyio
import httpx2
import openai
from fake_server import FakeServer, Received, Reply, Responder, completion
from langchain_core.language_models import BaseChatModel
from support import Case, Report, call, candidate, chat, echo, ok_not_json, said

SELF_TEST_ERROR = "detector-self-test-unraisable"
SELF_TEST_WARNING = "detector-self-test-warning"
RUNS = 5
SETTLE_SECONDS = 1.0
# 실패하거나 취소되는 실행의 수. 500 은 실행마다 세 번 보내 1.3초쯤 걸려 적게 둔다.
FAILED_RUNS = 3
# 도구 호출이 든 실행 하나가 모델을 부르는 횟수의 흉내.
CALLS = 4
# 서버가 답하기까지의 시간과, 그 전에 호출을 끊는 기한.
SLOW_SECONDS = 1.5
CANCEL_AFTER = 0.5


@dataclass
class Caught:
    unraisable: list[str] = field(default_factory=list[str])
    warnings: list[str] = field(default_factory=list[str])


@contextmanager
def catching() -> Generator[Caught]:
    """이 안에서 난 unraisable 예외와 경고를 모은다. 나가기 직전에 쓰레기 수집을 한 번 돌린다."""
    caught = Caught()
    before = sys.unraisablehook

    def hook(args: sys.UnraisableHookArgs) -> None:
        shown = f"{type(args.exc_value).__name__}: {args.exc_value}"
        caught.unraisable.append(f"{shown} ({args.err_msg or ''} {args.object!r})")

    sys.unraisablehook = hook
    try:
        with warnings.catch_warnings(record=True) as log:
            warnings.simplefilter("always")
            yield caught
            gc.collect()
        caught.warnings.extend(f"{entry.category.__name__}: {entry.message}" for entry in log)
    finally:
        sys.unraisablehook = before


class _Raises:
    def __del__(self) -> None:
        raise RuntimeError(SELF_TEST_ERROR)


class _Warns:
    def __del__(self) -> None:
        warnings.warn(SELF_TEST_WARNING, ResourceWarning, stacklevel=1)


def _self_test() -> bool:
    """탐지가 `__del__`의 예외와 경고를 잡는지. 모델과 따로 돌려 결과에 섞지 않는다."""
    with catching() as caught:
        _Raises()
        _Warns()
    return any(SELF_TEST_ERROR in line for line in caught.unraisable) and any(
        SELF_TEST_WARNING in line for line in caught.warnings
    )


def _keepalive_client() -> httpx2.AsyncClient:
    """라이브러리 기본값의 클라이언트. 응답을 다 읽은 연결을 쉬는 연결로 풀에 남긴다."""
    return openai.DefaultAsyncHttpxClient()


def _keepalive_model(base_url: str) -> BaseChatModel:
    return candidate(base_url, http_async_client=_keepalive_client())


def _open_connections(model: object) -> int | None:
    """그 모델의 비동기 클라이언트 연결 풀에서 닫히지 않은 연결의 수. 읽지 못하면 없음."""
    root = getattr(model, "root_async_client", None)
    http = getattr(root, "_client", None)
    transport = getattr(http, "_transport", None)
    pool = getattr(transport, "_pool", None)
    connections = getattr(pool, "connections", None)
    if connections is None:
        return None
    return sum(1 for connection in connections if not connection.is_closed())


def _report(row: dict[str, object]) -> Report:
    caught = row["caught"]
    assert isinstance(caught, Caught)
    opened = row["open_before_release"]
    measured = (
        row["text"] == "pong"
        and isinstance(opened, int)
        and opened >= 1
        and row["self_test"] is True
    )
    result = f"unraisable {len(caught.unraisable)}건, 경고 {len(caught.warnings)}건"
    return Report(
        measured=measured,
        result=result,
        data={
            "open_before_release": opened,
            "self_test": row["self_test"],
            "unraisable": caught.unraisable,
            "warnings": caught.warnings,
            "requests": row["requests"],
        },
    )


async def keepalive_released_inside_loop() -> Report:
    """기본값 클라이언트의 모델을 실행의 루프가 아직 돌 때 놓는다. `serve`의 실행이 끝나는
    모양이다."""
    with FakeServer() as server:
        model = _keepalive_model(server.base_url)
        outcome = await call(model, tools=False)
        opened = _open_connections(model)
        tested = _self_test()
        with catching() as caught:
            del model
            gc.collect()
            for _ in range(5):
                await asyncio.sleep(0)
        requests = len(server.requests)
    row: dict[str, object] = {
        "text": said(outcome),
        "open_before_release": opened,
        "self_test": tested,
        "caught": caught,
        "requests": requests,
    }
    return _report(row)


async def keepalive_released_after_loop_closed() -> Report:
    """기본값 클라이언트의 모델을 그 루프가 닫힌 뒤에 놓는다. 다른 스레드의 `asyncio.run`에서
    쓴다."""
    with FakeServer() as server:
        row = await asyncio.to_thread(_use_then_release, server.base_url)
        row["requests"] = len(server.requests)
    return _report(row)


def _use_then_release(base_url: str) -> dict[str, object]:
    holder: dict[str, object] = {}

    async def use() -> str | None:
        model = _keepalive_model(base_url)
        outcome = await call(model, tools=False)
        holder["model"] = model
        holder["open"] = _open_connections(model)
        return said(outcome)

    text = asyncio.run(use())
    opened = holder.pop("open", None)
    tested = _self_test()
    with catching() as caught:
        holder.clear()
    return {"text": text, "open_before_release": opened, "self_test": tested, "caught": caught}


async def _close(model: BaseChatModel) -> None:
    root = getattr(model, "root_async_client", None)
    close = getattr(root, "close", None)
    if close is None:
        raise RuntimeError("모델에서 비동기 클라이언트를 찾지 못했다")
    await close()


async def _runs(make: Callable[[str], BaseChatModel], *, close: bool) -> dict[str, object]:
    """한 루프에서 실행 `RUNS`번을 흉내 낸다. 실행마다 모델을 새로 만들어 한 번 부르고 놓는다.

    다 놓은 뒤 `SETTLE_SECONDS`를 기다려, 서버가 받은 연결과 클라이언트가 닫은 연결을 센다.
    """
    with FakeServer() as server:
        answered = 0
        for _ in range(RUNS):
            model = make(server.base_url)
            outcome = await call(model, tools=False)
            answered += said(outcome) == "pong"
            if close:
                await _close(model)
            del model
            gc.collect()
            await asyncio.sleep(0)
        await asyncio.sleep(SETTLE_SECONDS)
        return {
            "answered": answered,
            "requests": len(server.requests),
            "opened": server.opened_connections,
            "closed": server.closed_connections,
        }


async def runs_in_one_loop() -> Report:
    """`serve`처럼 한 루프에서 실행이 이어질 때, 놓인 모델의 연결이 닫히는지 갈래 넷으로 본다.

    - `keepalive`: 모델마다 기본값 클라이언트를 주고 닫지 않고 놓는다.
    - `keepalive_closed`: 같은 모델을 놓기 전에 클라이언트를 닫는다. 서버가 닫힌 연결을 세는지 보는
      양성 대조다. 이 갈래의 `closed`가 `RUNS`여야 다른 갈래의 0 이 "닫히지 않았다"는 뜻이 된다.
    - `candidate`: 지금 후보. 모델마다 쉬는 연결을 두지 않는 클라이언트를 준다.
    - `shared_cache`: 손대지 않은 `ChatOpenAI`. 라이브러리가 주소별로 캐시한 클라이언트를 나눠 쓴다.

    표지는 양성 대조의 `closed`가 `RUNS`이고, 모든 갈래가 실행마다 답을 받았다는 것이다.
    """
    branches = {
        "keepalive": await _runs(_keepalive_model, close=False),
        "keepalive_closed": await _runs(_keepalive_model, close=True),
        "candidate": await _runs(lambda url: candidate(url), close=False),
        "shared_cache": await _runs(lambda url: chat(url), close=False),
    }
    measured = branches["keepalive_closed"]["closed"] == RUNS and all(
        row["answered"] == RUNS and row["requests"] == RUNS for row in branches.values()
    )
    result = ", ".join(
        f"{name} 연결 {row['opened']}개 중 닫힘 {row['closed']}개" for name, row in branches.items()
    )
    return Report(measured=measured, result=result, data={"runs": RUNS, "branches": branches})


async def candidate_released_after_loop_closed() -> Report:
    """후보의 모델을 그 루프가 닫힌 뒤에 놓는다. `keepalive_released_after_loop_closed`와 견준다.

    표지는 그 루프에서 답을 받았고, 놓기 전에 서버가 연결 하나를 받아 하나가 닫혔으며(풀에 남은
    연결이 없다), 탐지의 자기 시험이 잡힌 것이다. 결과는 놓은 뒤 잡힌 unraisable 예외와 경고다.
    """
    with FakeServer() as server:
        row = await asyncio.to_thread(_candidate_then_release, server)
    caught = row["caught"]
    assert isinstance(caught, Caught)
    measured = (
        row["text"] == "pong"
        and row["opened"] == 1
        and row["closed_before_release"] == 1
        and row["self_test"] is True
    )
    result = f"unraisable {len(caught.unraisable)}건, 경고 {len(caught.warnings)}건"
    data = {key: value for key, value in row.items() if key != "caught"}
    data |= {"unraisable": caught.unraisable, "warnings": caught.warnings}
    return Report(measured=measured, result=result, data=data)


def _candidate_then_release(server: FakeServer) -> dict[str, object]:
    holder: dict[str, object] = {}

    async def use() -> str | None:
        model = candidate(server.base_url)
        holder["model"] = model
        return said(await call(model, tools=False))

    text = asyncio.run(use())
    deadline = time.monotonic() + SETTLE_SECONDS
    while server.closed_connections < 1 and time.monotonic() < deadline:
        time.sleep(0.05)
    closed = server.closed_connections
    tested = _self_test()
    with catching() as caught:
        holder.clear()
    return {
        "text": text,
        "opened": server.opened_connections,
        "closed_before_release": closed,
        "self_test": tested,
        "caught": caught,
    }


def _slow(_request: Received) -> Reply:
    time.sleep(SLOW_SECONDS)
    return completion()


async def _failing_runs(
    make: Callable[[str], BaseChatModel], respond: Responder, *, cancel: bool
) -> dict[str, int]:
    """한 루프에서 실패로 끝나는 실행 `FAILED_RUNS`번을 흉내 낸다. 실행마다 모델을 새로 만들어 한 번
    부르고 놓는다. `cancel`이면 답을 기다리는 호출을 `CANCEL_AFTER`초 기한으로 끊는다.

    다 놓은 뒤 기다려 서버가 받은 연결과 끝난 연결을 센다. 끊는 갈래는 서버의 응답 함수가 깨어나
    끊긴 연결을 알아챌 때까지(`SLOW_SECONDS`) 더 기다린다.
    """
    with FakeServer(respond) as server:
        ended = 0
        for _ in range(FAILED_RUNS):
            model = make(server.base_url)
            if cancel:
                with anyio.move_on_after(CANCEL_AFTER) as scope:
                    await call(model, tools=False)
                ended += scope.cancelled_caught
            else:
                outcome = await call(model, tools=False)
                ended += outcome.error is not None
            del model
            gc.collect()
            await asyncio.sleep(0)
        await asyncio.sleep(SETTLE_SECONDS + (SLOW_SECONDS if cancel else 0.0))
        return {
            "ended_as_expected": ended,
            "requests": len(server.requests),
            "opened": server.opened_connections,
            "closed": server.closed_connections,
        }


async def candidate_connections_after_failures() -> Report:
    """실패하거나 취소된 호출 뒤에 놓인 후보 모델의 연결이 닫히는지 갈래 다섯으로 본다.

    - `status_401`, `status_500`, `not_json`: 서버가 401, 500(SDK 가 두 번 더 보낸다), JSON 이 아닌
      200 을 준다.
    - `cancelled`: 서버가 `SLOW_SECONDS`초 뒤에 답하는데 `CANCEL_AFTER`초 기한이 호출을 끊는다. 실행
      타임아웃이 답을 기다리는 모델 호출을 끊는 모양이다.
    - `keepalive_401`: 대조. 기본값 클라이언트(쉬는 연결을 남긴다)의 모델이 401 을 받는다. 이 갈래에
      닫히지 않은 연결이 남아야, 다른 갈래에서 받은 연결과 끝난 연결의 수가 같은 것이 "닫혔다"는
      뜻이 된다.

    표지는 모든 갈래의 실행이 기대한 대로(예외나 취소로) 끝났고, 요청이 실행 수만큼은 닿았으며,
    대조 갈래에 닫히지 않은 연결이 남은 것이다.
    """
    branches = {
        "status_401": await _failing_runs(lambda url: candidate(url), echo(401), cancel=False),
        "status_500": await _failing_runs(lambda url: candidate(url), echo(500), cancel=False),
        "not_json": await _failing_runs(lambda url: candidate(url), ok_not_json, cancel=False),
        "cancelled": await _failing_runs(lambda url: candidate(url), _slow, cancel=True),
        "keepalive_401": await _failing_runs(_keepalive_model, echo(401), cancel=False),
    }
    control = branches["keepalive_401"]
    measured = control["closed"] < control["opened"] and all(
        row["ended_as_expected"] == FAILED_RUNS and row["requests"] >= FAILED_RUNS
        for row in branches.values()
    )
    result = ", ".join(
        f"{name} 연결 {row['opened']}개 중 닫힘 {row['closed']}개" for name, row in branches.items()
    )
    data = {"runs": FAILED_RUNS, "branches": branches}
    return Report(measured=measured, result=result, data=data)


async def _calls(make: Callable[[str], BaseChatModel]) -> dict[str, int]:
    """모델 하나를 `CALLS`번 차례로 부른 뒤 놓는다. 놓기 전과 놓은 뒤에 끝난 연결을 따로 센다."""
    with FakeServer() as server:
        model = make(server.base_url)
        answered = 0
        for _ in range(CALLS):
            answered += said(await call(model, tools=False)) == "pong"
        await asyncio.sleep(SETTLE_SECONDS)
        closed_before_release = server.closed_connections
        del model
        gc.collect()
        await asyncio.sleep(SETTLE_SECONDS)
        return {
            "answered": answered,
            "requests": len(server.requests),
            "opened": server.opened_connections,
            "closed_before_release": closed_before_release,
            "closed": server.closed_connections,
        }


async def calls_on_one_model() -> Report:
    """한 실행이 모델 하나를 여러 번 부를 때(도구 호출이 든 실행) 연결이 어떻게 되는지.

    - `candidate`: 지금 후보. 호출마다 연결을 새로 맺고, 놓기 전에 이미 닫는지.
    - `keepalive`: 대조. 기본값 클라이언트는 연결 하나를 다시 쓴다. 이 갈래가 받은 연결이 하나여야
      후보 갈래의 수가 "호출마다 새 연결"이라는 뜻이 된다.

    표지는 두 갈래가 호출마다 답을 받았고 대조 갈래가 연결 하나만 쓴 것이다.
    """
    branches = {
        "candidate": await _calls(lambda url: candidate(url)),
        "keepalive": await _calls(_keepalive_model),
    }
    measured = branches["keepalive"]["opened"] == 1 and all(
        row["answered"] == CALLS and row["requests"] == CALLS for row in branches.values()
    )
    result = ", ".join(
        f"{name} 연결 {row['opened']}개, 놓기 전 닫힘 {row['closed_before_release']}개, "
        f"놓은 뒤 닫힘 {row['closed']}개"
        for name, row in branches.items()
    )
    return Report(measured=measured, result=result, data={"calls": CALLS, "branches": branches})


CASES: dict[str, Case] = {
    "keepalive_released_inside_loop": keepalive_released_inside_loop,
    "keepalive_released_after_loop_closed": keepalive_released_after_loop_closed,
    "runs_in_one_loop": runs_in_one_loop,
    "candidate_released_after_loop_closed": candidate_released_after_loop_closed,
    "candidate_connections_after_failures": candidate_connections_after_failures,
    "calls_on_one_model": calls_on_one_model,
}
