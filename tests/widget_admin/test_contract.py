"""위젯 관리 서버의 계약 파일 `widget-admin/openapi.json` 이 코드와 맞는가(명세 widget-admin-server
"계약 파일과 생성 클라이언트").

계약 파일은 내보내기 도구가 뽑고 손으로 고치지 않는다. 최신성은 이 시험 하나가 판정한다. 파일 안의
약속(판 표시가 필수 정수이고 한 값으로 못 박히지 않은 것, 에러 문서가 봉투인 것)도 함께 본다.
"""

from __future__ import annotations

import importlib.metadata
import json

from tools.export_widget_admin_openapi import OPENAPI_PATH, document

PATH = "/widget-settings/{site}"


def _committed():
    return json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))


def test_커밋된_계약_파일은_앱이_지금_내는_계약과_같다() -> None:
    assert OPENAPI_PATH.read_text(encoding="utf-8") == document()


def test_계약_파일은_개행이_줄바꿈_하나이고_한국어가_그대로_읽힌다() -> None:
    raw = OPENAPI_PATH.read_bytes()

    assert b"\r\n" not in raw
    assert "위젯 관리 서버".encode() in raw


def test_계약의_판은_설치된_묶음의_판이다() -> None:
    info = _committed()["info"]

    assert info["version"] == importlib.metadata.version("widget-admin")


def test_읽는_경로의_작업_이름과_에러_문서가_계약에_있다() -> None:
    operation = _committed()["paths"][PATH]["get"]
    responses = operation["responses"]

    assert operation["operationId"] == "read_widget_settings"
    assert set(responses) == {"200", "404", "422", "500"}
    for status in ("404", "422", "500"):
        schema = responses[status]["content"]["application/json"]["schema"]
        assert schema == {"$ref": "#/components/schemas/ErrorEnvelope"}


def test_계약에_프레임워크_기본_검증_오류_모양이_없다() -> None:
    schemas = _committed()["components"]["schemas"]

    assert "HTTPValidationError" not in schemas
    assert "ValidationError" not in schemas


def test_판_표시는_필수_정수이고_한_값으로_못_박히지_않는다() -> None:
    settings = _committed()["components"]["schemas"]["WidgetSettings"]
    version = settings["properties"]["schema_version"]

    assert "schema_version" in settings["required"]
    assert version == {"title": "Schema Version", "type": "integer"}


def test_위젯_설정의_열쇠는_판_표시와_열아홉_칸이고_모두_필수다() -> None:
    settings = _committed()["components"]["schemas"]["WidgetSettings"]

    assert len(settings["properties"]) == 20
    assert set(settings["required"]) == set(settings["properties"])
    assert settings["additionalProperties"] is False
