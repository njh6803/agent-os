"""pyright strict가 await를 잊은 코루틴을 잡는지 확인하는 탐침."""


async def _collect() -> list[int]:
    return [1]


def test_forgot_asyncio_run() -> None:
    events = _collect()
    assert events is not None
