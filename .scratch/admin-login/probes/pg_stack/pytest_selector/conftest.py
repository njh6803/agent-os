"""가르는 갈래: 이 폴더의 비동기 시험만 Selector 루프에서 돌게 한다.

pytest-asyncio 의 `pytest_asyncio_loop_factories` 훅이 시험이 도는 루프를 만드는 공장을 고른다.
저장소의 pytest 설정은 그대로이고 이 `conftest.py` 가 이 폴더에만 그 훅을 더한다. 윈도에서 psycopg
의 비동기 모드가 저장소 설정의 기본 루프에서 거부되는 것이 루프 때문인지를, 같은 시험을 루프만 바꿔
돌려 가른다.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping

import pytest


def pytest_asyncio_loop_factories(
    config: pytest.Config, item: pytest.Item
) -> Mapping[str, Callable[[], asyncio.AbstractEventLoop]]:
    del config, item
    return {"selector": asyncio.SelectorEventLoop}
