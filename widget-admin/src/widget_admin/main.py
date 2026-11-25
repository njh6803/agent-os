"""`widget-admin` 명령의 진입점: `serve` 와 `migrate`(ADR 0064, ADR 0066).

`widget-admin serve [--host <주소>] [--port <번호>]` 는 위젯 관리 서버를 띄운다. 기본 주소는
`127.0.0.1:8100` 이다. `widget-admin migrate` 는 위젯 쪽 표를 마지막 판까지 앞으로만 올린다. 둘 다
`python -m widget_admin.main` 으로도 돈다.

**연결 문자열은 환경 변수 `WIDGET_ADMIN_DATABASE_URL` 하나로만 받는다.** 비밀번호가 든 값이라 명령줄
인자로 받지 않는다(프로세스 목록과 셸 이력에 남는다). 그 밖의 환경 변수와 파일은 읽지 않는다. 읽지
못하는 진단도 값을 싣지 않는다(원칙 V). 비밀번호가 든 값이라 표준 오류가 셸 이력과 CI 로그로
흘러가기 때문이다.

**닿는지와 표의 판은 여기서 보지 않는다.** 앱의 수명이 열릴 때 가장 바깥 미들웨어가 본다
(`widget_admin.lifespan`). 그래서 uvicorn 에 수명을 늘 켜라고 넘기고(`lifespan="on"`), 확인에서
멈추면 uvicorn 이 종료 코드 3 으로 끝난다. 이 함수가 3 을 1 로 바꾸지 않는다.

**`--host` 판정은 Agent OS 의 `serve` 와 같은 사본이다**(ADR 0056 결정 "루프백 규칙의 예외"). 판정
사례는 `tests/fixtures/container_network/cases.json` 이 잠근다. 진단의 글은 `serve` 의 것에서 까닭의
줄 하나만 다르다. 이 서버에는 토큰도 트레이스도 없어서다.

이 모듈은 `agent_os` 를 import 하지 않는다(import-linter 의 독립 계약).
"""

from __future__ import annotations

import argparse
import asyncio
import io
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple, TextIO

import uvicorn

from widget_admin.database import DatabaseUrl, WidgetAdminDatabase, parse_database_url
from widget_admin.server import create_app

EXIT_FINISHED = 0
EXIT_FAILED = 1

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8100
# 데이터베이스 주소도 환경 변수로만 들어온다. 비밀번호가 든 값이라 명령줄 인자로 받지 않는다.
DATABASE_URL_ENV = "WIDGET_ADMIN_DATABASE_URL"
# 바인딩을 허용하는 주소 전부. 진단에 그대로 실려서, 순서가 실행마다 달라지면 운영자가 읽는 문장이
# 달라진다. Agent OS 의 `serve`(`agent_os.main`)와 관리 화면, 위젯, 위젯 테스트 페이지가 같은 목록과
# 같은 예외를 따로 든다. 바꾸면 다섯을 함께 고치고, 같은 판정을 내는지는
# `tests/fixtures/container_network/cases.json` 이 잠근다.
LOOPBACK_HOSTS = ("127.0.0.1", "::1")
# 루프백 규칙의 예외. 둘이 함께 있을 때만 `0.0.0.0` 하나가 더 허용된다. 표지 파일은 이미지를 지을 때
# root 소유로 굽고(앱 사용자는 만들 수 없고 개발 PC 에는 그 경로가 없다) "이미지 안에서만"을,
# compose 가 주는 환경 변수가 "명시적"을 맡는다. 이름과 경로는 다섯 프로세스가 같은 것을 쓴다.
IMAGE_MARKER = Path("/etc/agent-os/image")
CONTAINER_NETWORK_ENV = "AGENT_OS_CONTAINER_NETWORK"
CONTAINER_NETWORK_HOST = "0.0.0.0"
# 서버를 멈출 때 연결이 남은 응답을 기다리는 상한(초). Agent OS 와 같다. uvicorn 의 기본값은 연결이
# 전부 끝날 때까지 앱의 수명을 닫지 않는다.
SHUTDOWN_GRACE_SECONDS = 5

_NOT_LOOPBACK_DIAGNOSTIC = (
    "--host 는 루프백만 받는다({allowed}). 받은 값: {host}\n"
    "  벗어나면 TLS 없이 평문으로 열리고, 앞단 프록시가 넘기는 경로의 목록도 지나지 않는다.\n"
    "  원격에서 보려면 SSH 포트 포워딩을 쓴다: ssh -L {port}:127.0.0.1:{port} <서버>"
)
_ENV_HINT_DIAGNOSTIC = (
    "  이미지 안에서 컨테이너 네트워크 주소({container})에 묶으려면"
    f" 환경 변수 {CONTAINER_NETWORK_ENV}=1 도 준다."
)
_OUTSIDE_IMAGE_DIAGNOSTIC = (
    f"  {CONTAINER_NETWORK_ENV} 는 이미지 밖에서는 켜지지 않는다"
    f"(표지 파일 {IMAGE_MARKER.as_posix()} 가 없다)."
)
_CONTAINER_NETWORK_DIAGNOSTIC = (
    "--host 는 루프백이나 컨테이너 네트워크 주소만 받는다({allowed}). 받은 값: {host}\n"
    "  컨테이너 네트워크 주소는 {container} 하나다. 다른 주소와 이름은 받지 않는다.\n"
    "  원격에서 보려면 SSH 포트 포워딩을 쓴다: ssh -L {port}:127.0.0.1:{port} <서버>"
)
_NOT_ONE_ENV_DIAGNOSTIC = (
    f"{CONTAINER_NETWORK_ENV} 는 비우거나 1 만 받는다. 받은 값: {{value}}\n"
    "  오타가 조용히 꺼짐으로 읽히지 않게 시작 자리에서 끝낸다."
)
# 데이터베이스 주소의 진단은 높임말이다. 글은 명세 widget-admin-server 의 "멈출 때의 글"이 원천이고,
# `serve` 와 `migrate` 가 같은 글을 쓴다. 비밀번호가 든 값이라 값은 싣지 않는다(원칙 V). 이름이
# 공개인 까닭은 배포 안내의 시험(widget-admin-server 04 가 더한다)이 이 글을 안내의 표와 견주려고
# 읽기 때문이다. 글에 ADR 번호를
# 싣지 않는다. 운영자는 ADR 을 모르고, 안내는 저장소 안의 말을 쓰지 않아 옮겨 적을 수 없다.
NO_DATABASE_URL_DIAGNOSTIC = (
    f"{DATABASE_URL_ENV} 이 비어 있습니다. widget-admin 의 serve 와 migrate 는 PostgreSQL"
    " 데이터베이스가 있어야 돕니다.\n"
    "  단독 배포에서는 compose 가 .env 의 WIDGET_ADMIN_DATABASE_PASSWORD 로 이 값을 짓습니다."
    " 개발 PC 의 값은 README 에 있습니다."
)
UNREADABLE_DATABASE_URL_DIAGNOSTIC = (
    f"{DATABASE_URL_ENV} 을 읽지 못했습니다."
    " postgresql://계정:비밀번호@호스트:포트/데이터베이스 꼴이어야 합니다.\n"
    "  값에는 비밀번호가 들어 있어 여기 찍지 않습니다. 비밀번호에 @ 가 들면 주소를 읽지 못하므로,"
    " 비밀번호는 영문자와 숫자만 씁니다."
)


class ContainerNetwork(NamedTuple):
    """루프백 규칙의 예외를 켜는 두 입력. 판정은 이 값만 보고 파일도 환경도 읽지 않는다.

    `image_marker` 는 표지 파일(`IMAGE_MARKER`)이 있는가(파일인지는 가리지 않는다), `env` 는 환경
    변수의 값(없으면 `None`)이다.
    """

    image_marker: bool
    env: str | None


def main(argv: Sequence[str] | None = None) -> int:
    _use_utf8(sys.stdout, sys.stderr)
    args = _parser().parse_args(argv)
    if args.command == "serve":
        return _serve(str(args.host), int(args.port))
    return _migrate()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="widget-admin", description="위젯 관리 서버")
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve", help="위젯 관리 서버를 띄운다")
    serve.add_argument("--host", default=DEFAULT_HOST, help="듣는 주소(루프백만 받는다)")
    serve.add_argument("--port", type=int, default=DEFAULT_PORT, help="듣는 포트")
    commands.add_parser("migrate", help="위젯 쪽 표를 마지막 판까지 올린다")
    return parser


def _serve(host: str, port: int) -> int:
    """위젯 관리 서버를 세운다. 구성 오류는 요청 시점이 아니라 여기서 끝난다.

    진단을 모아 한 번에 낸다. 하나씩 내면 운영자가 고치고 다시 치고 또 막힌다. 값이 있으면 객체를
    지어 앱에 넘기기만 한다. 닿는지와 표의 판은 앱의 수명이 열릴 때 가장 바깥 미들웨어가 본다.
    """
    database_url = _read_database_url()
    problems: list[str] = []
    binding = binding_problem(host, str(port), _container_network())
    if binding is not None:
        problems.append(binding)
    if isinstance(database_url, str):
        problems.append(database_url)
    if problems or isinstance(database_url, str):
        sys.stderr.write("".join(f"{problem}\n" for problem in problems))
        return EXIT_FAILED
    uvicorn.run(
        create_app(database=_build_database(database_url), stderr=sys.stderr),
        host=host,
        port=port,
        timeout_graceful_shutdown=SHUTDOWN_GRACE_SECONDS,
        # `auto` 는 앱이 수명을 모른다고 보면 경고만 찍고 소켓을 연다. 데이터베이스를 확인하지 못한
        # 서버가 뜨는 길이라, 수명은 늘 켜고 확인이 막으면 uvicorn 이 3 으로 끝나게 한다.
        lifespan="on",
    )
    return EXIT_FINISHED


def _read_database_url() -> DatabaseUrl | str:
    """환경 변수의 주소를 읽는다. 읽었으면 주소, 못 읽었으면 그 진단이다.

    `serve` 와 `migrate` 가 같은 판정과 같은 글을 쓴다. 값에는 비밀번호가 들어 있어 진단은 값을 싣지
    않는다(원칙 V). 앞뒤의 공백과 개행은 걷고 읽는다.
    """
    value = os.environ.get(DATABASE_URL_ENV, "").strip()
    if not value:
        return NO_DATABASE_URL_DIAGNOSTIC
    url = parse_database_url(value)
    if url is None:
        return UNREADABLE_DATABASE_URL_DIAGNOSTIC
    return url


def _build_database(url: DatabaseUrl) -> WidgetAdminDatabase:
    """데이터베이스 객체를 짓는 자리. 닿지 못해 기다리는 알림은 표준 오류로 간다.

    조립이라 여기 하나로 모았고, 시험이 기다림의 길이를 줄인 객체로 바꿔 끼운다.
    """
    return WidgetAdminDatabase(url, notice=_notice)


def _notice(message: str) -> None:
    sys.stderr.write(f"{message}\n")


def _migrate() -> int:
    """위젯 쪽 표를 이 판의 마지막 판까지 올린다. 주소는 환경 변수로만 받는다.

    결과 글은 성공이면 표준 출력, 멈췄으면 표준 오류로 간다. 객체가 글 대신 예외를 던지면 예외의
    글을 싣지 않고 까닭만 싣는 글로 바꿔 끝낸다.
    """
    url = _read_database_url()
    if isinstance(url, str):
        sys.stderr.write(f"{url}\n")
        return EXIT_FAILED
    return asyncio.run(_migrate_database(_build_database(url)))


async def _migrate_database(database: WidgetAdminDatabase) -> int:
    try:
        result = await database.migrate()
    except Exception as error:  # 어떤 예외든 까닭만 싣는 글로 바꿔 끝낸다
        sys.stderr.write(f"{database.unexpected_problem(error)}\n")
        code = EXIT_FAILED
    else:
        (sys.stdout if result.ok else sys.stderr).write(f"{result.message}\n")
        code = EXIT_FINISHED if result.ok else EXIT_FAILED
    try:
        await database.close()
    except Exception as error:  # 닫다 실패해도 예외의 글과 역추적은 싣지 않는다
        sys.stderr.write(f"{database.close_problem(error)}\n")
        return EXIT_FAILED
    return code


def _container_network() -> ContainerNetwork:
    """지금 프로세스의 두 입력. 판정(`binding_problem`)과 달리 파일과 환경을 읽는 자리다."""
    return ContainerNetwork(
        image_marker=IMAGE_MARKER.exists(), env=os.environ.get(CONTAINER_NETWORK_ENV)
    )


def binding_problem(host: str, port: str, network: ContainerNetwork) -> str | None:
    """듣는 주소의 구성 오류. 받으면 `None`. `port` 는 SSH 안내에 싣는다.

    루프백 둘은 늘 받는다. `0.0.0.0` 하나는 표지 파일이 있고 환경 변수가 `1` 일 때만 더 받는다.
    다른 IPv4 주소, `::`, 이름은 예외가 켜져도 거부한다. 컨테이너 네트워크의 주소는 뜰 때마다 바뀌고
    프록시는 뒷단에 IPv4 로만 걸기 때문이다. 환경 변수가 없거나 비었으면 꺼진 것이고, `1` 이 아닌
    값은 호스트와 상관없이 구성 오류다.

    진단은 경우마다 다르다. 환경 변수만 있고 표지 파일이 없으면 이미지 밖에서는 켜지지 않는다고
    말하고, 표지 파일만 있고 환경 변수가 없으면 지금의 진단에 그 환경 변수를 알린다. 사례는
    `tests/fixtures/container_network/cases.json` 이다.
    """
    if network.env not in (None, "", "1"):
        return _NOT_ONE_ENV_DIAGNOSTIC.format(value=network.env)
    if host in LOOPBACK_HOSTS:
        return None
    enabled = network.image_marker and network.env == "1"
    if enabled and host == CONTAINER_NETWORK_HOST:
        return None
    if enabled:
        return _CONTAINER_NETWORK_DIAGNOSTIC.format(
            allowed=", ".join((*LOOPBACK_HOSTS, CONTAINER_NETWORK_HOST)),
            host=host,
            container=CONTAINER_NETWORK_HOST,
            port=port,
        )
    base = _NOT_LOOPBACK_DIAGNOSTIC.format(allowed=", ".join(LOOPBACK_HOSTS), host=host, port=port)
    if host != CONTAINER_NETWORK_HOST:
        return base
    if network.image_marker:
        return f"{base}\n{_ENV_HINT_DIAGNOSTIC.format(container=CONTAINER_NETWORK_HOST)}"
    if network.env == "1":
        return f"{base}\n{_OUTSIDE_IMAGE_DIAGNOSTIC}"
    return base


def _use_utf8(*streams: TextIO) -> None:
    """Windows 콘솔의 cp949 가 한국어 진단을 깨뜨리지 않게 한다(CLAUDE.md 환경 함정)."""
    for stream in streams:
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
