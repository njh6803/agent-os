"""저장소의 판 번호. 저장소는 0.0.0으로 두어 소스에서 바로 돌린 것이 판 이미지가 아님을 드러내고,
실제 번호는 CI가 이미지를 지을 때만 넣는다(ADR 0056 결정 "저장소의 번호").

저장소 상태를 재는 시험이다. 판을 바꾼 파일 셋(`pyproject.toml`, `uv.lock`, `openapi.json`)이 서로
어긋나면, 소스에서 바로 돌린 것이 이미지의 번호를 달았거나 잠금 검사가 빨개진다. 둘째 설치 묶음
`widget-admin` 도 같은 셋(`widget-admin/pyproject.toml`, `uv.lock` 의 그 항목,
`widget-admin/openapi.json`)이 0.0.0 이다(ADR 0064).
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPOSITORY_VERSION = "0.0.0"


def _pyproject_version() -> str:
    document = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return str(document["project"]["version"])


def test_pyproject_의_판이_0_0_0이다() -> None:
    assert _pyproject_version() == REPOSITORY_VERSION


def test_잠금_파일의_자기_패키지_항목이_pyproject_의_판과_같다() -> None:
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    own = [package for package in lock["package"] if package["name"] == "agent-os"]

    assert len(own) == 1
    assert own[0]["version"] == _pyproject_version()


def test_계약_파일의_판_칸이_pyproject_의_판과_같다() -> None:
    contract = json.loads((ROOT / "openapi.json").read_text(encoding="utf-8"))

    assert contract["info"]["version"] == _pyproject_version()


def _widget_admin_version() -> str:
    path = ROOT / "widget-admin" / "pyproject.toml"
    document = tomllib.loads(path.read_text(encoding="utf-8"))
    return str(document["project"]["version"])


def test_위젯_관리_묶음의_판도_0_0_0이다() -> None:
    assert _widget_admin_version() == REPOSITORY_VERSION


def test_잠금_파일의_위젯_관리_묶음_항목이_그_묶음의_판과_같다() -> None:
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    own = [package for package in lock["package"] if package["name"] == "widget-admin"]

    assert len(own) == 1
    assert own[0]["version"] == _widget_admin_version()


def test_위젯_관리_계약_파일의_판_칸이_그_묶음의_판과_같다() -> None:
    path = ROOT / "widget-admin" / "openapi.json"
    contract = json.loads(path.read_text(encoding="utf-8"))

    assert contract["info"]["version"] == _widget_admin_version()
