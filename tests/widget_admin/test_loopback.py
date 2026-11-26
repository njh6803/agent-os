"""`widget-admin serve` 의 `--host` 판정(루프백 규칙)을 본다.

이 판정은 다섯째 사본이다. `serve`, 관리 화면, 위젯, 위젯 테스트 페이지가 같은 규칙을 따로 들고
있고(앱 사이 import 는 층 경계가 막는다), 사례는 `tests/fixtures/container_network/cases.json` 이
잠근다. 위젯 관리 서버의 시험도 그 표의 `binding` 판정과 진단의 신호를 읽는다. 선례는
`tests/test_main.py` 의 같은 시험이다. 진단의 글은 `serve` 의 것에서 까닭의 줄 하나만 다르다(명세
widget-admin-server "루프백 규칙").
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import BaseModel
from tests.widget_admin.support import SECRET

from widget_admin import main as main_module
from widget_admin.main import (
    CONTAINER_NETWORK_ENV,
    DATABASE_URL_ENV,
    IMAGE_MARKER,
    ContainerNetwork,
    binding_problem,
    main,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
UNREACHABLE = f"postgresql://widget_admin:{SECRET}@127.0.0.1:1/probe"


class _Signal(BaseModel):
    contains: list[str]
    excludes: list[str]


class _Row(BaseModel):
    marker: bool
    env: str | None
    verdicts: dict[str, str]


class _NetworkCases(BaseModel):
    """`tests/fixtures/container_network/cases.json`. 파이썬은 듣는 주소(`binding`)만 읽는다."""

    env_name: str
    marker_path: str
    binding: list[_Row]
    binding_signals: dict[str, _Signal]


NETWORK_CASES = _NetworkCases.model_validate_json(
    (REPO_ROOT / "tests" / "fixtures" / "container_network" / "cases.json").read_text(
        encoding="utf-8"
    )
)
# (표지 파일, 환경 변수, 호스트, 판정의 종류). 표의 칸 하나가 사례 하나다.
BINDING_CASES = [
    (row.marker, row.env, host, verdict)
    for row in NETWORK_CASES.binding
    for host, verdict in row.verdicts.items()
]


def test_사례_표는_판정의_종류를_모두_갖고_있다() -> None:
    """표가 비거나 한 종류가 빠지면 아래 사례 시험이 그 칸 없이 초록이 된다."""
    assert {verdict for *_, verdict in BINDING_CASES} == set(NETWORK_CASES.binding_signals) | {"ok"}
    assert NETWORK_CASES.env_name == CONTAINER_NETWORK_ENV
    assert NETWORK_CASES.marker_path == IMAGE_MARKER.as_posix()


@pytest.mark.parametrize(
    ("marker", "env", "host", "verdict"),
    BINDING_CASES,
    ids=[f"표지{int(m)}-{e!r}-{h}-{v}" for m, e, h, v in BINDING_CASES],
)
def test_듣는_주소의_판정이_사례_표와_같다(
    *, marker: bool, env: str | None, host: str, verdict: str
) -> None:
    found = binding_problem(host, "8100", ContainerNetwork(image_marker=marker, env=env))

    if verdict == "ok":
        assert found is None
        return
    assert found is not None
    signal = NETWORK_CASES.binding_signals[verdict]
    for text in signal.contains:
        assert text.format(host=host, env=env) in found
    for text in signal.excludes:
        assert text not in found


def test_루프백이_아닌_주소의_진단은_까닭의_줄만_serve와_다르다() -> None:
    found = binding_problem("0.0.0.0", "8100", ContainerNetwork(image_marker=False, env=None))

    assert found == (
        "--host 는 루프백만 받는다(127.0.0.1, ::1). 받은 값: 0.0.0.0\n"
        "  벗어나면 TLS 없이 평문으로 열리고, 앞단 프록시가 넘기는 경로의 목록도 지나지 않는다.\n"
        "  원격에서 보려면 SSH 포트 포워딩을 쓴다: ssh -L 8100:127.0.0.1:8100 <서버>"
    )


def test_serve의_까닭의_줄은_이_서버의_진단에_없다() -> None:
    found = binding_problem("0.0.0.0", "8100", ContainerNetwork(image_marker=False, env=None))

    assert found is not None
    assert "토큰이 헤더에" not in found
    assert "트레이스" not in found


@pytest.fixture
def image_marker(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """표지 파일의 자리를 임시 경로로 바꾼다. `/etc` 에 파일을 만들지 않는다."""
    path = tmp_path / "agent-os-image"
    monkeypatch.setattr(main_module, "IMAGE_MARKER", path)
    return path


@pytest.fixture
def uvicorn_calls(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []

    def run(app: object, **kwargs: object) -> None:
        calls.append({"app": app, **kwargs})

    monkeypatch.setattr(main_module.uvicorn, "run", run)
    return calls


@pytest.fixture(autouse=True)
def _database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """주소 문제가 호스트 문제와 섞이지 않게 읽히는 주소를 준다."""
    monkeypatch.setenv(DATABASE_URL_ENV, UNREACHABLE)
    monkeypatch.delenv(CONTAINER_NETWORK_ENV, raising=False)


def test_표지_파일과_환경_변수가_함께_있으면_serve가_0_0_0_0에_선다(
    monkeypatch: pytest.MonkeyPatch,
    image_marker: Path,
    uvicorn_calls: list[dict[str, object]],
) -> None:
    """판정은 순수 함수지만 진입점이 실제 표지 파일과 환경 변수를 거기에 이어야 켜진다."""
    image_marker.write_text("", encoding="utf-8")
    monkeypatch.setenv(CONTAINER_NETWORK_ENV, "1")

    code = main(["serve", "--host", "0.0.0.0", "--port", "9999"])

    assert code == 0
    assert [(call["host"], call["port"]) for call in uvicorn_calls] == [("0.0.0.0", 9999)]


@pytest.mark.parametrize(
    ("marker", "env", "signal"),
    [
        (False, "1", "이미지 밖에서는 켜지지 않는다"),
        (True, None, "AGENT_OS_CONTAINER_NETWORK=1"),
        (True, "true", "받은 값: true"),
        (False, None, "루프백만 받는다"),
    ],
    ids=["환경 변수만", "표지 파일만", "환경 변수 오타", "둘 다 없음"],
)
def test_둘이_함께_있지_않으면_serve는_0_0_0_0에_서지_않고_경우에_맞는_진단을_낸다(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    image_marker: Path,
    uvicorn_calls: list[dict[str, object]],
    *,
    marker: bool,
    env: str | None,
    signal: str,
) -> None:
    if marker:
        image_marker.write_text("", encoding="utf-8")
    if env is not None:
        monkeypatch.setenv(CONTAINER_NETWORK_ENV, env)

    code = main(["serve", "--host", "0.0.0.0"])

    captured = capsys.readouterr()
    assert code == 1
    assert captured.out == ""
    assert signal in captured.err
    assert SECRET not in captured.err
    assert uvicorn_calls == []


def test_루프백이_아닌_주소는_serve가_받지_않고_1로_끝난다(
    capsys: pytest.CaptureFixture[str], uvicorn_calls: list[dict[str, object]]
) -> None:
    code = main(["serve", "--host", "192.168.0.10", "--port", "8100"])

    captured = capsys.readouterr()
    assert code == 1
    assert "받은 값: 192.168.0.10" in captured.err
    assert "ssh -L 8100:127.0.0.1:8100" in captured.err
    assert uvicorn_calls == []
