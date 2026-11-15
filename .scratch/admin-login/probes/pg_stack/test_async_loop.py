"""저장소의 pytest 설정에서 비동기 조합을 돈다.

저장소 루트에서 이 파일의 경로를 주어 돌리면 루트의 `pyproject.toml` 이 설정이 된다. 곧
`asyncio_mode = "auto"`(ADR 0007. 데코레이터도 마커도 없는 `async def`)이고 `RuntimeWarning` 과
거두지 못한 예외의 경고가 오류다. 조합의 결과는 단언하지 않고 `PG_PROBE_OUT` 파일에 한 줄씩 적는다.
그래서 pytest 의 통과·실패는 조합이 실패했는지가 아니라 그 설정이 경고를 오류로 올렸는지를 말한다.
`--import-mode=importlib` 은 이 폴더를 `sys.path` 에 넣지 않으므로 띄우는 쪽이 `PYTHONPATH` 로
넣는다.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

import pytest
from exercise import ASYNC_LABELS, DSN_ENV, run_async_stack

OUT_ENV = "PG_PROBE_OUT"


@pytest.mark.parametrize("label", ASYNC_LABELS)
async def test_async_stack(label: str) -> None:
    outcome = await run_async_stack(label, os.environ[DSN_ENV])
    with Path(os.environ[OUT_ENV]).open("a", encoding="utf-8") as out:
        out.write(json.dumps(asdict(outcome), ensure_ascii=False) + "\n")
