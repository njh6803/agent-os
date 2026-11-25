"""위젯 관리 서버의 계약 파일 생성기(ADR 0064). 계약 파일은 `widget-admin/openapi.json` 이다.

위젯 쪽 생성 클라이언트가 이 파일에서 만들어지므로, 파일이 앱과 어긋나면 생성된 클라이언트가 조용히
틀린다. 최신성은 pytest 하나가 판정한다(`tests/widget_admin/test_contract.py`). 새 훅을 만들지
않는다.

    PYTHONUTF8=1 uv run python tools/export_widget_admin_openapi.py

앱을 짓는 함수가 데이터베이스 객체를 받으므로 자리표시자 객체로 앱을 세운다. 객체를 만드는 것은
엔진을 짓는 일이라 데이터베이스에 닿지 않고, 스키마는 데이터베이스를 읽지 않는다. 주소는 어디에도
연결되지 않는 값이다. 쓰지 않으므로 닫을 연결도 없다.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

from widget_admin.database import WidgetAdminDatabase
from widget_admin.server import create_app

ROOT = Path(__file__).resolve().parent.parent
OPENAPI_PATH = ROOT / "widget-admin" / "openapi.json"

_PLACEHOLDER_URL = "postgresql://openapi-export-only:unused@127.0.0.1:1/unused"


def document() -> str:
    """계약 파일의 내용. 테스트가 이것과 커밋된 파일을 비교한다.

    키를 정렬하는 이유는 diff 를 안정시키기 위해서다. 파이썬 사전의 순서는 삽입 순서라 프레임워크가
    필드를 더하는 자리에 따라 파일 전체가 흔들린다. ASCII 로 이스케이프하지 않는 이유는 한국어
    설명이 그대로 읽혀야 하기 때문이고, 파일은 UTF-8 이다.
    """
    database = WidgetAdminDatabase(_PLACEHOLDER_URL)
    app = create_app(database=database, stderr=io.StringIO())
    return json.dumps(app.openapi(), indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def main() -> None:
    # 줄 끝을 고정한다. 기본값은 플랫폼에 따라 CRLF 가 되어 계약 파일이 OS 마다 달라진다.
    OPENAPI_PATH.write_text(document(), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
