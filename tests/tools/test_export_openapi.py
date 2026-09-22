"""계약 파일의 최신성. `openapi.json` 이 `create_app().openapi()` 와 어긋나면 빨개진다.

늦으면 그 사이에 커밋되는 계약 파일이 앱과 달라도 검사 넷이 전부 초록이고, 슬라이스 3 의
생성 클라이언트가 조용히 틀린다(스토리 27).
"""

from __future__ import annotations

import json

from tools.export_openapi import OPENAPI_PATH, document


def test_커밋된_계약_파일이_앱과_같다() -> None:
    committed = OPENAPI_PATH.read_text(encoding="utf-8")

    assert committed == document(), (
        "openapi.json 이 앱과 어긋난다. "
        "PYTHONUTF8=1 uv run python tools/export_openapi.py 로 다시 뽑는다"
    )


def test_계약_파일이_이름_있는_타입을_싣는다() -> None:
    """생성 클라이언트의 타입 이름이 익명 구조체가 되지 않는다(스토리 28)."""
    schemas = json.loads(document())["components"]["schemas"]

    assert {"Health", "ErrorEnvelope", "ErrorCode", "Violation"} <= set(schemas)
