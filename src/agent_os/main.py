"""agent-os 명령의 진입점. 조합 층.

채널, 관리, 어댑터를 조립해 넘기는 유일한 자리다. 슬라이스 2에서 `serve`가
`agent_os.server`를 부른다.

**사이트 파일은 여기서 읽는다**(ADR 0023). TOML 의 키 이름과 손상 판정은 이 모듈이 소유하고, 읽은
값은 공용 층의 사이트 목록 타입(`agent_os.http.sites`)으로 `create_app` 에 넘긴다 — 토큰이 들어오는
자리와 같다. 어댑터가 아니다. 포트의 구현이 아니라 조립이 읽는 구성이다(운영자 파일 `disabled.toml`
은 포트의 메서드라 어댑터이고, 사이트 파일은 `create_app` 의 인자라 다르다).

**OS 사용자 이름에 `|` 가 들면 `serve`·`run`·`resume` 이 시작 자리에서 끝난다.** 최종 사용자의
주체는 `발급자|sub` 이고 사이트 파일이 발급자에 `|` 를 금지한다. 이 가드가 OS 사용자 쪽을 막아, `|`
가 든 주체는 언제나 최종 사용자이고 그 밖은 언제나 OS 사용자다. 두 이름 공간이 겹치면 주체 비교가
거짓이 된다(ADR 0015 이력).
"""

from __future__ import annotations

import getpass
import io
import os
import re
import sys
import tomllib
from collections.abc import Sequence
from ipaddress import IPv6Address
from pathlib import Path
from typing import Literal, TextIO

import uvicorn
from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from agent_os.adapters.anthropic import AnthropicModels, resolve_model_name
from agent_os.adapters.clock import SystemClock
from agent_os.adapters.filesystem import FilesystemPlugins
from agent_os.adapters.jsonl import JsonlTrace
from agent_os.adapters.mcp import McpTools
from agent_os.channel.cli.interrupt import run_interruptibly
from agent_os.channel.cli.main import (
    EXIT_FAILED,
    EXIT_FINISHED,
    ResumeArgs,
    RunArgs,
    ServeArgs,
    parse_args,
    resume_command,
    run_command,
)
from agent_os.channel.http.limits import DEFAULT_CONCURRENT_RUNS
from agent_os.core.ports import PluginError
from agent_os.core.run import DEFAULT_RUN_TIMEOUT_SECONDS
from agent_os.http.sites import PRINCIPAL_SEPARATOR, Site, SiteKey, SiteLimits, Sites
from agent_os.sdk import (
    PLUGIN_NAME_PATTERN,
    AgentName,
    PluginKind,
    PluginName,
    Principal,
    is_plugin_name,
)
from agent_os.server import create_app

# 토큰은 환경변수로만 들어온다(ADR 0011, ADR 0015). 명령줄 인자는 프로세스 목록과 셸 이력에 남는다.
ADMIN_TOKEN_ENV = "AGENT_OS_ADMIN_TOKEN"
CHANNEL_TOKEN_ENV = "AGENT_OS_CHANNEL_TOKEN"
# 바인딩을 허용하는 주소 전부. 자라면 ADR 0011 의 이력에 쌓는다. 집합이 아니라 열인 이유는
# 진단에 그대로 실려서, 순서가 실행마다 달라지면 운영자가 읽는 문장이 달라지기 때문이다.
# 관리 화면과 위젯의 시작 래퍼(`web/apps/admin/tools/loopback.ts`,
# `web/apps/widget/tools/start.ts`)가 같은 목록을 따로 든다. 바꾸면 셋을 함께 고친다.
LOOPBACK_HOSTS = ("127.0.0.1", "::1")
# 서버를 멈출 때 연결이 남은 응답을 기다리는 상한(초). uvicorn 의 기본값은 연결이 전부 끝날
# 때까지 앱의 수명을 닫지 않아, 멈추라는 명령이 실행 하나가 끝나기를 제한 없이 기다린다(ADR 0014
# 의 2026-09-24 이력). 유예가 지나면 남은 연결이 끊기고 앱의 수명이 닫히며 남은 실행은 전부
# 취소되어 결말 없음이 된다. 5 초는 결말 직전의 실행이 마지막 이벤트를 흘릴 여유이고, 모델 호출
# 하나(수십 초)를 기다려 주는 길이가 아니다. 그 실행은 트레이스에 결말 없음으로 남는다.
SHUTDOWN_GRACE_SECONDS = 5

_NO_ADMIN_TOKEN_DIAGNOSTIC = (
    f"{ADMIN_TOKEN_ENV} 가 비어 있다. 관리 API 는 토큰 없이 서지 않는다(ADR 0011).\n"
    f"  인증 없는 서버를 띄워 놓고 401 만 보게 되는 것을 막으려고 시작 자리에서 끝낸다.\n"
    f"  값을 정해 {ADMIN_TOKEN_ENV} 로 넘긴 뒤 다시 친다."
)
_NO_CHANNEL_TOKEN_DIAGNOSTIC = (
    f"{CHANNEL_TOKEN_ENV} 가 비어 있다. 채널도 토큰 없이 서지 않는다(ADR 0015).\n"
    f"  채널만 조용히 끄고 관리만 세우지 않으려고 시작 자리에서 끝낸다.\n"
    f"  관리 토큰과 다른 값을 정해 {CHANNEL_TOKEN_ENV} 로 넘긴 뒤 다시 친다."
)
_SAME_TOKENS_DIAGNOSTIC = (
    f"{ADMIN_TOKEN_ENV} 와 {CHANNEL_TOKEN_ENV} 가 같다. 두 토큰은 서로 달라야 한다(ADR 0015).\n"
    f"  같으면 트레이스를 읽는 권한이 실행을 일으키는 권한이 되고, 요청 시점에는 그것을 알아챌\n"
    f"  길이 없다. 둘 중 하나를 다른 값으로 정한 뒤 다시 친다."
)
_NOT_LOOPBACK_DIAGNOSTIC = (
    "--host 는 루프백만 받는다({allowed}). 받은 값: {host}\n"
    "  벗어나면 토큰이 헤더에 평문으로 실리고 마스킹되지 않은 트레이스도 평문으로 나간다.\n"
    "  원격에서 보려면 SSH 포트 포워딩을 쓴다: ssh -L {port}:127.0.0.1:{port} <서버>"
)
_NOT_POSITIVE_TIMEOUT_DIAGNOSTIC = (
    "--run-timeout 은 1 이상의 정수(초)다. 받은 값: {value}\n"
    "  0 이하면 모델이나 도구를 기다리는 실행은 모두 그 자리에서 run_failed 로 끝난다.\n"
    "  빼면 core 의 기본값 {default}초다."
)
_NOT_POSITIVE_CONCURRENT_RUNS_DIAGNOSTIC = (
    "--end-user-concurrent-runs 는 1 이상의 정수다. 받은 값: {value}\n"
    "  0 이하면 최종 사용자 경로의 모든 시작·결정·이어 가기가 429 로 거절된다.\n"
    "  빼면 채널의 기본값 {default} 이다."
)


def main(argv: list[str] | None = None) -> int:
    _use_utf8(sys.stdout, sys.stderr)
    args = parse_args(argv)
    # serve 를 먼저 가르는 이유는 serve 가 기본 모델의 문제를 다른 구성 오류와 한 목록에 모아 내기
    # 때문이다. 모델을 여기서 확인하면 serve 의 진단이 모델 하나에서 먼저 끊긴다.
    if isinstance(args, ServeArgs):
        return _serve(args)
    user = getpass.getuser()
    problem = _os_user_problem(user) or _model_problem(args.model, args.plugins_root)
    if problem is not None:
        sys.stderr.write(f"{problem}\n")
        return EXIT_FAILED
    default_model = _default_model(args.model)
    if isinstance(args, ResumeArgs):
        return run_interruptibly(lambda: _resume(args, default_model, Principal(user)))
    return run_interruptibly(lambda: _run(args, default_model, Principal(user)))


def _default_model(flag: str | None) -> PluginName:
    """기본 모델의 이름은 플래그, 환경변수 순이고 코드의 기본값은 없다. 둘 다 없거나 비었거나
    이름의 패턴을 어긴 지정은 `ValueError` 다. 실행 전에 거부한다.

    경계 입력이라 `is_plugin_name` 으로 걸러서 감싼다(`sdk/ids.py`). 패턴 위반이 실행 준비의
    `PluginError` 까지 숨어들면 오타가 첫 실행에서야 드러나고 구성 오류를 준비 단계의 오류가
    대신한다. 문구는 값과 패턴을 든다. 그 이름의 매니페스트가 있는지는 `_model_problem` 이 본다.
    """
    name = resolve_model_name(os.environ, flag)
    if not is_plugin_name(name):
        raise ValueError(
            f"모델 이름 {name!r} 이 플러그인 이름의 패턴을 어긴다: {PLUGIN_NAME_PATTERN}\n"
            "  모델은 plugins/models/<이름>/plugin.toml 의 플러그인이고 이름으로 고른다."
        )
    return PluginName(name)


def _serve(args: ServeArgs) -> int:
    """관리 API 와 HTTP 채널을 한 앱으로 세운다. 구성 오류는 요청 시점이 아니라 여기서 끝난다.

    실행 식별자가 생기기 전이라 트레이스가 없는 `PluginError` 계열과 같은 성격이다. 진단을 모아
    한 번에 내는 이유는 하나씩 내면 운영자가 고치고 다시 치고 또 막히기 때문이다.

    여기서 한 번 푸는 것은 기본 모델의 이름이고 모델이 아니다. 이름이 없거나 패턴을 어기거나 그
    이름의 모델 매니페스트가 없거나 읽히지 않으면 구성 오류 목록의 한 항목이다(`_model_problem`).
    모델은 실행마다 core 가 모델 소스로 그 이름(이나 에이전트가 고른 이름)의 매니페스트에서
    만든다(ADR 0040). 요청마다 고르지 않는다(ADR 0014). API 키는 보지 않는다 — CLI 처럼 실행
    안의 `run_failed` 로 드러난다. 채널 실행의 주체는 이 프로세스의 OS 사용자다(ADR 0015).
    신원의 출처를 정하는 것이 조립이라 채널이 스스로 읽지 않고 여기서 넘긴다.

    마지막 줄에 닿기 전에 검사가 끝나 있어야 한다. 순서가 뒤집히면 토큰 없는 서버가 잠시라도
    서고, 그것이 이 명령이 막으려던 바로 그 상태다.

    사이트 파일은 여기서 한 번 읽고 요청마다 읽지 않는다. 요청마다 읽으면 파일이 깨지는 순간부터
    최종 사용자 경로가 모두 500 이다(ADR 0023).

    실행 타임아웃은 받은 그대로 넘긴다. 없으면 없음을 넘겨 core 의 기본값이 선다. 0 이하는 모델이나
    도구를 기다리는 실행이 모두 그 자리에서 실패하는 서버라 다른 구성 오류와 함께 여기서 끝난다.
    전역 동시 실행 상한도 같다 — 없으면 채널의 기본값이고 0 이하는 구성 오류다.
    """
    admin_token = os.environ.get(ADMIN_TOKEN_ENV, "")
    channel_token = os.environ.get(CHANNEL_TOKEN_ENV, "")
    user = getpass.getuser()
    sites = _read_sites(args.site_file)
    problems = _configuration_problems(args, admin_token, channel_token, user, sites)
    if problems or not isinstance(sites, Sites):
        sys.stderr.write("".join(f"{problem}\n" for problem in problems))
        return EXIT_FAILED
    uvicorn.run(
        create_app(
            plugins=FilesystemPlugins(args.plugins_root),
            trace=JsonlTrace(args.traces),
            models=AnthropicModels(),
            default_model=_default_model(args.model),
            tools=McpTools(),
            clock=SystemClock(),
            principal=Principal(user),
            admin_token=admin_token,
            channel_token=channel_token,
            sites=sites,
            run_timeout_seconds=args.run_timeout_seconds,
            end_user_concurrent_runs=args.end_user_concurrent_runs,
            stderr=sys.stderr,
        ),
        host=args.host,
        port=args.port,
        timeout_graceful_shutdown=SHUTDOWN_GRACE_SECONDS,
    )
    return EXIT_FINISHED


def _configuration_problems(
    args: ServeArgs,
    admin_token: str,
    channel_token: str,
    user: str,
    sites: Sites | Sequence[str],
) -> list[str]:
    """서버가 서지 못하는 이유 전부. 비어 있으면 선다.

    사이트 파일의 문제와 OS 사용자 이름의 `|` 도 토큰·호스트·모델 진단과 같은 목록에 든다. 사이트
    파일은 부르는 쪽이 한 번 읽어 그 결과(사이트 목록이거나 문제들)를 넘긴다 — 진단과 앱이 같은
    읽기를 본다.

    토큰은 있나 없나, 같나 다르나만 보고 값을 진단에 싣지 않는다(원칙 V). 구성을 되읊는 진단이
    비밀을 같이 되읊는 자리이고, 표준 에러는 셸 이력과 CI 로그로 흘러간다.

    공백만 있는 토큰도 없는 것으로 본다. 환경변수 하나의 오타가 "설정했다고 믿는 서버"를 만드는
    것이 이 명령이 막으려는 상태이고, `_decision` 이 공백뿐인 거부 사유를 없는 것으로 보는 것과
    같은 판단이다. 대신 통과한 토큰은 다듬지 않고 그대로 넘긴다 — 비밀을 조용히 고쳐 넘기면
    운영자가 정한 값과 서버가 요구하는 값이 갈린다. 같은지도 다듬지 않은 값으로 본다.

    두 토큰이 같다는 진단은 채널 토큰이 있을 때만 낸다. 없는 쪽이 있으면 그 진단이 먼저이고,
    둘 다 비어 "같다"는 것은 고칠 거리가 아니다.
    """
    problems: list[str] = []
    if not admin_token.strip():
        problems.append(_NO_ADMIN_TOKEN_DIAGNOSTIC)
    if not channel_token.strip():
        problems.append(_NO_CHANNEL_TOKEN_DIAGNOSTIC)
    elif channel_token == admin_token:
        problems.append(_SAME_TOKENS_DIAGNOSTIC)
    if args.host not in LOOPBACK_HOSTS:
        problems.append(
            _NOT_LOOPBACK_DIAGNOSTIC.format(
                allowed=", ".join(LOOPBACK_HOSTS), host=args.host, port=args.port
            )
        )
    if args.run_timeout_seconds is not None and args.run_timeout_seconds <= 0:
        problems.append(
            _NOT_POSITIVE_TIMEOUT_DIAGNOSTIC.format(
                value=args.run_timeout_seconds, default=DEFAULT_RUN_TIMEOUT_SECONDS
            )
        )
    if args.end_user_concurrent_runs is not None and args.end_user_concurrent_runs <= 0:
        problems.append(
            _NOT_POSITIVE_CONCURRENT_RUNS_DIAGNOSTIC.format(
                value=args.end_user_concurrent_runs, default=DEFAULT_CONCURRENT_RUNS
            )
        )
    model = _model_problem(args.model, args.plugins_root)
    if model is not None:
        problems.append(model)
    if not isinstance(sites, Sites):
        problems.extend(sites)
    os_user = _os_user_problem(user)
    if os_user is not None:
        problems.append(os_user)
    return problems


def _model_problem(flag: str | None, plugins_root: Path) -> str | None:
    """기본 모델을 쓸 수 없으면 그 진단(질의). `serve` 와 CLI `run`·`resume` 이 시작 자리에서 같이
    쓴다.

    네 갈래다. 이름이 없거나 비었다, 이름의 패턴을 어긴다(둘은 CLI 와 같은 `_default_model` 이
    푼다), 그 이름의 모델 매니페스트가 없다, 있지만 읽히지 않는다(어댑터의 `PluginError` 문구
    그대로이고 잘못 적은 값은 싣지 않는다). 읽은 매니페스트는 이 확인에만 쓰고 버린다. 실행은 실행
    준비마다 다시 읽는다(ADR 0040). 꺼짐은 보지 않는다 — 운영 중에 바뀌는 상태라 시작의 조건이
    아니고, 그것을 쓰는 실행이 거부된다(HTTP 는 409, CLI 는 실행 준비의 진단). 이름은 확인이 끝난 뒤
    한 번 다시 푼다.
    """
    try:
        name = _default_model(flag)
        manifest = FilesystemPlugins(plugins_root).read_manifest(PluginKind.MODEL, name)
    except (ValueError, PluginError) as error:
        return str(error)
    if manifest is None:
        path = plugins_root / "models" / name / "plugin.toml"
        return (
            f"기본 모델 플러그인이 없다: {name}\n"
            f"  {path} 을 두거나 --model·AGENT_OS_MODEL 의 이름을 고친다."
        )
    return None


def _os_user_problem(user: str) -> str | None:
    """OS 사용자 이름이 주체가 될 수 없으면 그 진단(질의). 모듈 독스트링의 가드다.

    `getpass.getuser()` 는 `LOGNAME`·`USER`·`LNAME`·`USERNAME` 환경변수를 먼저 읽으므로 이름에 어떤
    글자든 올 수 있다(ADR 0023). 그래서 금지를 OS 에 기대지 않고 여기서 본다.
    """
    if PRINCIPAL_SEPARATOR not in user:
        return None
    return _OS_USER_DIAGNOSTIC.format(user=user, separator=PRINCIPAL_SEPARATOR)


_OS_USER_DIAGNOSTIC = (
    "OS 사용자 이름 {user!r} 에 '{separator}' 가 들어 있다. 그 글자가 든 주체는 최종 사용자의\n"
    "  것(발급자{separator}sub)이라 이 이름으로는 실행의 주체를 가를 수 없다(ADR 0023).\n"
    "  LOGNAME·USER·USERNAME 을 '{separator}' 없는 이름으로 정한 뒤 다시 친다."
)


# --- 사이트 파일 -------------------------------------------------------------------------
#
# 모양은 TOML 이고 `schema_version = "1"` 이 필수다. 사이트마다 `[[sites]]` 표 하나에 발급자
# (`issuer`), 대상(`audience`), 공개 키 목록(`[[sites.public_keys]]` 마다 PEM 문자열 `pem` 과 선택
# `kid`), 허용 출처(`allowed_origins`), 열 에이전트(`agents`), 선택 상한 표(`[sites.limits]`)다.
# 상한 표의 키는 여섯이고 값마다 선택이다 — `request_chars`, `concurrent_runs_per_principal`,
# `hourly_runs_per_principal`, `concurrent_runs_per_site`, `hourly_runs_per_site`,
# `subscriptions_per_principal`. 1 이상의 엄격한 정수이고(매니페스트의 `conversation_limit` 과 같은
# 규칙) 적지 않은 값은 HTTP 채널의 기본값이다. 이 모양은 숫자 기본값을 짓지 않는다 — 값이 서는
# 자리는 채널의 한 곳이다. 모르는 키는 손상이다 — 운영자 파일(ADR 0017)과 같은 규칙이고, 오타가
# 조용히 무시되면 운영자가 적었다고 믿는 것과 서버가 쓰는 것이 갈린다. 값은 엄격한 타입이다 — 수를
# 글자로, 글자를 목록으로, 불린이나 실수를 정수로 받아 주지 않는다. 그래서 열은 TOML 배열이 읽히는
# 그대로 `list` 다(엄격한 검증은 `tuple` 필드에 리스트를 받지 않는다). 허용 출처는 브라우저가
# `Origin` 헤더에 싣는 표기 그대로다(`_origin_rule`). 위젯
# 빌드(`web/apps/widget/tools/site-file.ts`)도 이 파일을 읽어 합친 허용 출처와 가장 작은
# `request_chars` 를 쓴다(web-widget 티켓 04). 빌드는 키와 타입과 판, `request_chars` 의 범위, 허용
# 출처의 표기를 이 모양과 같게 보고, 그 밖의 제약(공개 키의 수, 다른 상한의 범위, 서버만 읽는 값의
# 뜻)은 보지 않는다. 빌드의 TOML 파서는 TOML 1.1 을 따라 tomllib(1.0)이 거절하는 문법도 받는다. 그런
# 파일로는 빌드가 지나도 serve 가 뜨지 못한다.

_STRICT = ConfigDict(extra="forbid", frozen=True, strict=True)


class _PublicKeyEntry(BaseModel):
    """공개 키 하나. PEM(SubjectPublicKeyInfo) 문자열과 선택 kid."""

    model_config = _STRICT

    pem: str
    kid: str | None = None


class _LimitsEntry(BaseModel):
    """상한 표. 값마다 선택이고 1 이상의 정수다. 빠진 값은 채널의 기본값이다."""

    model_config = _STRICT

    request_chars: int | None = Field(default=None, ge=1)
    concurrent_runs_per_principal: int | None = Field(default=None, ge=1)
    hourly_runs_per_principal: int | None = Field(default=None, ge=1)
    concurrent_runs_per_site: int | None = Field(default=None, ge=1)
    hourly_runs_per_site: int | None = Field(default=None, ge=1)
    subscriptions_per_principal: int | None = Field(default=None, ge=1)

    def to_site_limits(self) -> SiteLimits:
        """공용 층의 상한 표로(질의)."""
        return SiteLimits(
            request_chars=self.request_chars,
            concurrent_runs_per_principal=self.concurrent_runs_per_principal,
            hourly_runs_per_principal=self.hourly_runs_per_principal,
            concurrent_runs_per_site=self.concurrent_runs_per_site,
            hourly_runs_per_site=self.hourly_runs_per_site,
            subscriptions_per_principal=self.subscriptions_per_principal,
        )


class _SiteEntry(BaseModel):
    """사이트 하나. 허용 출처와 열 에이전트는 비어 있을 수 있되 적어야 한다. 상한 표는 선택이다."""

    model_config = _STRICT

    issuer: str
    audience: str
    public_keys: list[_PublicKeyEntry] = Field(min_length=1)
    allowed_origins: list[str]
    agents: list[str]
    limits: _LimitsEntry = Field(default_factory=_LimitsEntry)


class _SiteFile(BaseModel):
    """사이트 파일 전체. 사이트가 없는 파일은 사이트 없음과 같다."""

    model_config = _STRICT

    schema_version: Literal["1"]
    sites: list[_SiteEntry] = Field(default_factory=list[_SiteEntry])


class _Problem(BaseModel):
    """pydantic 검증 오류 하나에서 읽는 것. 받은 값(`input`)은 읽지 않는다 — 진단에 키 값이 실린다.

    느슨한 타입의 오류 항목을 손으로 좁히면 그 자리가 타입 우회가 되므로 pydantic 으로 다시 읽는다
    (공용 층의 에러 봉투와 같은 이유).
    """

    model_config = ConfigDict(extra="ignore", frozen=True)

    loc: tuple[str | int, ...] = ()
    msg: str = ""


_PROBLEMS = TypeAdapter[tuple[_Problem, ...]](tuple[_Problem, ...])


def _read_sites(path: Path | None) -> Sites | list[str]:
    """사이트 파일을 읽어 사이트 목록으로, 또는 받아들일 수 없는 이유들로(질의).

    경로가 없으면 사이트 없음이다. 경로를 줬는데 파일이 없거나 깨졌으면 구성 오류다 — 경로를 잘못
    적은 것이 조용히 401 이 되지 않게 한다(ADR 0023). 이유는 전부 모아 하나의 진단으로 낸다. 진단에
    키 값을 싣지 않는다(원칙 V. 공개 키라도 — 진단은 짧아야 한다). 자리는 `sites[0].public_keys[1]`
    꼴로 가리킨다.
    """
    if path is None:
        return Sites()
    try:
        document = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [_site_file_diagnostic(path, ["파일이 없다"])]
    except (OSError, UnicodeDecodeError) as error:
        return [_site_file_diagnostic(path, [f"읽을 수 없다({type(error).__name__})"])]
    except tomllib.TOMLDecodeError as error:
        return [_site_file_diagnostic(path, [f"TOML 이 아니다: {error}"])]
    try:
        parsed = _SiteFile.model_validate(document)
    except ValidationError as error:
        problems = _PROBLEMS.validate_python(error.errors())
        return [_site_file_diagnostic(path, [f"{_place(p.loc)}: {p.msg}" for p in problems])]
    sites, problems = _sites_of(parsed)
    return [_site_file_diagnostic(path, problems)] if problems else sites


def _sites_of(parsed: _SiteFile) -> tuple[Sites, list[str]]:
    """모양을 지난 파일의 사이트 목록과, 모양으로는 말할 수 없는 규칙의 위반들(질의).

    발급자는 비지 않았고 사이트끼리 겹치지 않으며 `|` 를 품지 않는다(주체 이름 `발급자|sub` 가 짝
    하나로 정해지는 조건). 한 사이트 안에서 `kid` 는 겹치지 않고 `kid` 없는 키는 많아야 하나다(키를
    고르는 규칙). 열 에이전트는 플러그인 이름의 패턴을 지킨다 — 없는 이름은 구성 오류가 아니다.
    플러그인 루트는 `serve` 가 뜬 뒤에도 바뀌고(ADR 0003) 요청 때 core 의 부재가 답한다. 허용 출처는
    브라우저가 싣는 표기여야 한다(`_origin_rule`). 진단은 어긴 규칙을 말하되 값을 싣지 않는다 —
    사용자 정보를 적은 값에는 비밀번호가 들 수 있다.
    """
    problems: list[str] = []
    seen: dict[str, int] = {}
    sites: list[Site] = []
    for index, entry in enumerate(parsed.sites):
        place = f"sites[{index}]"
        if not entry.issuer.strip():
            problems.append(f"{place}.issuer 가 비었다")
        elif entry.issuer in seen:
            problems.append(f"{place}.issuer 가 sites[{seen[entry.issuer]}] 의 것과 겹친다")
        else:
            seen[entry.issuer] = index
        if PRINCIPAL_SEPARATOR in entry.issuer:
            problems.append(f"{place}.issuer 에 '{PRINCIPAL_SEPARATOR}' 가 들어 있다")
        keys, key_problems = _keys_of(place, entry.public_keys)
        problems.extend(key_problems)
        problems.extend(_key_id_problems(place, entry.public_keys))
        problems.extend(
            f"{place}.agents[{at}] 가 플러그인 이름의 패턴을 어긴다"
            for at, name in enumerate(entry.agents)
            if not is_plugin_name(name)
        )
        problems.extend(
            f"{place}.allowed_origins[{at}]: 브라우저가 Origin 헤더에 싣는 표기가 아니다"
            f"(규칙 {rule}). {_ORIGIN_RULES[rule]}"
            for at, origin in enumerate(entry.allowed_origins)
            if (rule := _origin_rule(origin)) is not None
        )
        sites.append(
            Site(
                issuer=entry.issuer,
                audience=entry.audience,
                keys=keys,
                allowed_origins=tuple(entry.allowed_origins),
                agents=frozenset(AgentName(name) for name in entry.agents),
                limits=entry.limits.to_site_limits(),
            )
        )
    return Sites(entries=tuple(sites)), problems


def _keys_of(
    place: str, entries: Sequence[_PublicKeyEntry]
) -> tuple[tuple[SiteKey, ...], list[str]]:
    """공개 키들과, 읽지 못한 키의 문제들(질의). 읽지 못한 키는 건너뛴다.

    SubjectPublicKeyInfo PEM(`BEGIN PUBLIC KEY`)만 받는다. `cryptography` 의 읽기는 PKCS#1
    (`BEGIN RSA PUBLIC KEY`)도 받지만 사이트 파일의 형식은 하나로 둔다 — 키를 만드는 도구마다 기본
    형식이 달라, 둘을 받으면 운영자가 어느 것을 적어야 하는지가 문서와 갈린다.
    """
    keys: list[SiteKey] = []
    problems: list[str] = []
    for at, entry in enumerate(entries):
        where = f"{place}.public_keys[{at}].pem"
        if not entry.pem.lstrip().startswith(_SPKI_HEADER):
            problems.append(f"{where} 이 SubjectPublicKeyInfo 형식의 PEM 이 아니다")
            continue
        try:
            key = load_pem_public_key(entry.pem.encode("utf-8"))
        except (ValueError, UnsupportedAlgorithm):
            problems.append(f"{where} 이 PEM 공개 키로 읽히지 않는다")
            continue
        if not isinstance(key, RSAPublicKey):
            problems.append(f"{where} 이 RSA 공개 키가 아니다")
            continue
        keys.append(SiteKey(kid=entry.kid, key=key))
    return tuple(keys), problems


_SPKI_HEADER = "-----BEGIN PUBLIC KEY-----"


def _key_id_problems(place: str, entries: Sequence[_PublicKeyEntry]) -> list[str]:
    """한 사이트 안의 `kid` 규칙 위반들(질의). 겹치는 `kid` 와 둘 이상인 `kid` 없는 키."""
    problems: list[str] = []
    kids = [entry.kid for entry in entries if entry.kid is not None]
    if len(kids) != len(set(kids)):
        problems.append(f"{place}.public_keys 에 같은 kid 가 둘 이상이다")
    if sum(1 for entry in entries if entry.kid is None) > 1:
        problems.append(f"{place}.public_keys 에 kid 없는 키가 둘 이상이다")
    return problems


# 허용 출처의 표기(web-widget 티켓 04, ADR 0024). 값은 브라우저가 `Origin` 헤더에 싣는 직렬화
# 그대로여야 한다 — 다른 표기는 CORS 와 `frame-ancestors` 에서 조용히 어느 출처와도 맞지 않는다.
# 규칙의 이름과 차례와 사례는 `tests/fixtures/site_file/` 가 원천이고, 위젯 빌드
# (`web/apps/widget/tools/site-file.ts`)가 같은 차례로 판정한다. 차례가 다르면 두 규칙을 함께 어긴
# 값에서 두 언어가 다른 이름을 낸다.
type _OriginRule = Literal[
    "wildcard",
    "null",
    "shape",
    "scheme",
    "case",
    "path",
    "userinfo",
    "port",
    "default-port",
    "idn",
    "ipv6",
    "host",
    "ipv4",
]
_ORIGIN_RULES: dict[_OriginRule, str] = {
    "wildcard": "'*' 를 적지 않는다. 출처를 하나씩 적는다",
    "null": "'null' 은 불투명한 출처라 받지 않는다",
    "shape": "'스킴://호스트' 꼴로 적는다",
    "scheme": "스킴은 http 나 https 다",
    "case": "스킴과 호스트는 소문자로 적는다",
    "path": "호스트와 포트 뒤에 경로, 끝 슬래시, 질의, 조각을 적지 않는다",
    "userinfo": "사용자 정보('@' 앞)를 적지 않는다",
    "port": "포트는 앞에 0 이 없는 65535 이하의 십진수다",
    "default-port": "기본 포트(http 의 80, https 의 443)는 적지 않는다",
    "idn": "국제화 도메인은 퓨니코드(xn--)로 적는다",
    "ipv6": (
        "IPv6 주소는 대괄호 안에 앞의 0 이 없는 소문자 16진수 그룹으로 적고, 0 이 둘 이상 이어진"
        " 가장 긴 열 가운데 앞의 것을 :: 로 줄인다. IPv4 를 품은 주소도 점으로 적지 않는다"
    ),
    "host": (
        "호스트는 비지 않고, 브라우저가 거절하거나 바꾸는 글자"
        "(공백, 제어 문자, %, <, >, ^, |, \\ 등)가 없다"
    ),
    "ipv4": "IPv4 주소는 앞에 0 이 없는 0~255 의 십진수 넷을 점으로 잇는다",
}
_ORIGIN_SHAPE = re.compile(r"([A-Za-z][A-Za-z0-9+.\-]*)://([^/?#]*)(.*)", re.DOTALL)
_UPPERCASE = re.compile(r"[A-Z]")
_PORT = re.compile(r"0|[1-9][0-9]{0,4}")
_MAX_PORT = 65535
_DEFAULT_PORTS: dict[str, int] = {"http": 80, "https": 443}
# WHATWG URL 의 금지된 도메인 글자(forbidden domain code point). ASCII 도메인에 이 글자가 들면
# 브라우저의 URL 파서가 실패한다. `%` 는 퍼센트 인코딩을 먼저 풀어 그 결과를 보므로, 든 값은
# 바뀌거나 실패한다.
_FORBIDDEN_DOMAIN = re.compile(r"[\x00-\x20#%/:<>?@\[\\\]^|\x7f]")
# 끝 라벨이 이 꼴이면 브라우저는 호스트를 IPv4 로 읽는다(WHATWG URL 의 ends in a number checker).
_NUMERIC_LABEL = re.compile(r"[0-9]+|0x[0-9a-f]*")
_IPV4_PART = re.compile(r"0|[1-9][0-9]{0,2}")
_IPV4_PARTS = 4
_MAX_IPV4_PART = 255


def _origin_rule(origin: str) -> _OriginRule | None:
    """허용 출처가 어긴 첫 규칙의 이름, 또는 없음(질의). 규칙의 뜻은 `_ORIGIN_RULES`."""
    if "*" in origin:
        return "wildcard"
    if origin == "null":
        return "null"
    shape = _ORIGIN_SHAPE.fullmatch(origin)
    if shape is None:
        return "shape"
    scheme, authority, rest = shape.groups()
    if scheme.lower() not in _DEFAULT_PORTS:
        return "scheme"
    if _UPPERCASE.search(scheme + authority):
        return "case"
    if rest:
        return "path"
    if "@" in authority:
        return "userinfo"
    host, after = _split_host(authority)
    if after and not (after.startswith(":") and _is_port(after[1:])):
        return "port"
    if after == f":{_DEFAULT_PORTS[scheme]}":
        return "default-port"
    return _host_rule(host)


def _split_host(authority: str) -> tuple[str, str]:
    """권한부를 호스트와 그 뒤(`""` 이거나 `:` 로 시작하는 글)로(질의). 대괄호로 적은 호스트는 `]`
    에서, 그 밖은 첫 `:` 에서 가른다. 닫는 `]` 가 없으면 모두 호스트다."""
    if authority.startswith("["):
        end = authority.find("]")
        cut = len(authority) if end < 0 else end + 1
    else:
        end = authority.find(":")
        cut = len(authority) if end < 0 else end
    return authority[:cut], authority[cut:]


def _is_port(text: str) -> bool:
    return _PORT.fullmatch(text) is not None and int(text) <= _MAX_PORT


def _host_rule(host: str) -> _OriginRule | None:
    """호스트가 어긴 규칙의 이름, 또는 없음(질의). 대소문자는 부르는 쪽이 먼저 봤다."""
    if not host.isascii():
        return "idn"
    if host.startswith("["):
        return None if _is_canonical_ipv6(host) else "ipv6"
    if not host or _FORBIDDEN_DOMAIN.search(host):
        return "host"
    labels = host.split(".")
    # 끝 라벨은 끝 점 하나를 떼고 본다(ends in a number checker). 그렇게 IPv4 로 읽힌 호스트는
    # 브라우저가 정규형으로 다시 적고 끝 점도 뗀다(IPv4 parser, `127.0.0.1.` 은 `127.0.0.1` 이
    # 된다). 그래서 정규형 판정은 끝 점째 본다.
    names = labels[:-1] if len(labels) > 1 and not labels[-1] else labels
    if _NUMERIC_LABEL.fullmatch(names[-1]):
        return None if _is_canonical_ipv4(labels) else "ipv4"
    return None


def _is_canonical_ipv6(host: str) -> bool:
    """대괄호 안이 브라우저가 적는 꼴과 같은가. 영역 식별자(`%`)는 파이썬이 받아 그대로 두므로
    따로 막는다."""
    if not host.endswith("]") or "%" in host:
        return False
    inner = host[1:-1]
    try:
        address = IPv6Address(inner)
    except ValueError:
        return False
    return _serialized_ipv6(address) == inner


def _serialized_ipv6(address: IPv6Address) -> str:
    """브라우저가 적는 IPv6 주소(WHATWG URL 의 IPv6 serializer)(질의). 16진수 그룹 여덟을 앞의 0
    없이 소문자로 적고, 0 이 둘 이상 이어진 가장 긴 열 가운데 앞의 것을 `::` 로 줄인다.

    `IPv6Address.compressed` 는 쓰지 않는다. 같은 3.12 에서도 판에 따라 IPv4 매핑 주소
    (`::ffff:0:0/96`)를 달리 적는다. CPython v3.12.15 의 `IPv6Address.__str__` 은 그 주소를
    `_ipv4_mapped_ipv6_to_str` 로 `::ffff:1.2.3.4` 처럼 점으로 적고, v3.12.10 에는 그 갈래가 없어
    `::ffff:102:304` 로 적는다(두 판의 `Lib/ipaddress.py` 를 `gh api` 로 받아 읽었다). 점 표기는
    RFC 5952 5절이 권하는 꼴이고 브라우저는 그렇게 적지 않는다(두 원문의 웹 요약을 봤다, 픽스처
    README 의 `ipv6`).
    """
    packed = address.packed
    groups = [int.from_bytes(packed[at : at + 2]) for at in range(0, len(packed), 2)]
    best_start, best_length, start = -1, 1, -1
    for index, group in enumerate(groups):
        if group:
            start = -1
            continue
        if start < 0:
            start = index
        if index - start + 1 > best_length:
            best_start, best_length = start, index - start + 1
    hexes = [f"{group:x}" for group in groups]
    if best_start < 0:
        return ":".join(hexes)
    return f"{':'.join(hexes[:best_start])}::{':'.join(hexes[best_start + best_length :])}"


def _is_canonical_ipv4(parts: Sequence[str]) -> bool:
    return len(parts) == _IPV4_PARTS and all(
        _IPV4_PART.fullmatch(part) is not None and int(part) <= _MAX_IPV4_PART for part in parts
    )


def _place(loc: Sequence[str | int]) -> str:
    """검증 오류의 자리를 `sites[0].public_keys[1].pem` 꼴로."""
    text = ""
    for part in loc:
        text += f"[{part}]" if isinstance(part, int) else (f".{part}" if text else part)
    return text or "(파일 전체)"


def _site_file_diagnostic(path: Path, problems: Sequence[str]) -> str:
    """사이트 파일 하나의 진단. 문제마다 한 줄이다."""
    lines = "".join(f"\n  - {problem}" for problem in problems)
    return (
        f"사이트 파일 {path} 을 받아들일 수 없다(ADR 0023).{lines}\n"
        "  고친 뒤 다시 친다. --site-file 을 빼면 최종 사용자 경로의 모든 토큰이 401 이다."
    )


async def _run(args: RunArgs, default_model: PluginName, principal: Principal) -> int:
    return await run_command(
        args.agent,
        args.request,
        principal,
        previous_run=args.previous_run,
        default_model=default_model,
        plugins=FilesystemPlugins(args.plugins_root),
        models=AnthropicModels(),
        tools=McpTools(),
        trace=JsonlTrace(args.traces),
        clock=SystemClock(),
        stdout=sys.stdout,
        stderr=sys.stderr,
        progress=sys.stderr if args.verbose else None,
        traces=args.traces,
        plugins_root=args.plugins_root,
    )


async def _resume(args: ResumeArgs, default_model: PluginName, approver: Principal) -> int:
    """승인자는 요청한 주체와 같은 출처에서 온다. 결정은 그 실행의 주체만 내리므로 언제나 자기
    승인이고, 최종 사용자의 실행에는 core 가 다른 주체로 거절한다(ADR 0009 의 2026-10-03 이력)."""
    return await resume_command(
        args.run_id,
        args.pause_index,
        args.decision,
        approver,
        default_model=default_model,
        plugins=FilesystemPlugins(args.plugins_root),
        models=AnthropicModels(),
        tools=McpTools(),
        trace=JsonlTrace(args.traces),
        clock=SystemClock(),
        stdout=sys.stdout,
        stderr=sys.stderr,
        progress=sys.stderr if args.verbose else None,
        traces=args.traces,
        plugins_root=args.plugins_root,
    )


def _use_utf8(*streams: TextIO) -> None:
    """Windows 콘솔의 cp949 가 한국어 진단을 깨뜨리지 않게 한다(CLAUDE.md 환경 함정)."""
    for stream in streams:
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
