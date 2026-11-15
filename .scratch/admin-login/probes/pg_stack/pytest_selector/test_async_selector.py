"""`test_async_loop.py` 와 같은 시험을 이 폴더의 `conftest.py` 가 고른 Selector 루프에서 돈다."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

import pytest
from exercise import ASYNC_LABELS, DSN_ENV, run_async_stack

OUT_ENV = "PG_PROBE_OUT"


@pytest.mark.parametrize("label", ASYNC_LABELS)
async def test_async_stack_on_selector(label: str) -> None:
    outcome = await run_async_stack(label, os.environ[DSN_ENV])
    with Path(os.environ[OUT_ENV]).open("a", encoding="utf-8") as out:
        out.write(json.dumps(asdict(outcome), ensure_ascii=False) + "\n")
