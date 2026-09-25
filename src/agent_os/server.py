"""HTTP 표면의 조립 층. `create_app()` 하나만 내보낸다(ADR 0010).

모듈 수준 전역 `app` 을 두지 않는다. 두면 어댑터를 넘길 자리가 없어져 조립 층이 둘로 갈리고,
import 시점에 플러그인 경로와 트레이스 디렉터리가 고정되어 테스트가 가짜 포트 대신 진짜
파일시스템을 쓰게 된다.

라우터를 마운트하는 자리도 여기다. 관리 라우터와 채널 라우터 둘이고, 채널과 관리는 서로를 import
하지 않는다. 트레이스 포트 하나를 두 라우터가 함께 쓴다.
"""

from __future__ import annotations

from importlib.metadata import version
from typing import TextIO

from fastapi import FastAPI

from agent_os.admin.http import Health, admin_router
from agent_os.channel.http.router import CHANNEL_PREFIX, channel_router
from agent_os.core.ports import ChatModel, Clock, PluginSource, ToolSource, TraceStore
from agent_os.http.auth import RequireToken
from agent_os.http.errors import AssignRequestId, install_error_handlers
from agent_os.sdk import Principal

# 계약 파일의 머리. 관리와 채널을 함께 말한다(ADR 0010 의 2026-09-24 이력). 관리만 말하면 채널이
# 붙은 순간 "실행을 일으키지 않는다"가 거짓이 된다.
_TITLE = "Agent OS HTTP API"
_DESCRIPTION = (
    "관리는 등록된 플러그인과 지나간 실행을 읽고 실행을 일으키지 않는다. "
    "채널은 실행을 일으켜 그 이벤트 스트림을 돌려준다. 두 면은 서로 다른 토큰으로 연다."
)


def create_app(
    *,
    plugins: PluginSource,
    trace: TraceStore,
    model: ChatModel,
    tools: ToolSource,
    clock: Clock,
    principal: Principal,
    admin_token: str,
    channel_token: str,
    stderr: TextIO,
) -> FastAPI:
    """관리 API 와 HTTP 채널이 선 앱 하나. 포트는 부르는 쪽이 만들어 넘긴다.

    관리 라우터는 플러그인과 트레이스 포트만 받는다. 도구 포트를 받지 않으므로 조회 하나가 MCP 서버
    여럿을 띄우는 것이 구조적으로 불가능하다(ADR 0010 의 2026-09-24 이력). 모델과 도구와 시계는
    채널만 받는다. 실행의 주체도 채널이 받는다 — 요청에서 받지 않고, 그 출처(`serve` 의 OS 사용자)를
    정하는 것은 부르는 쪽이다(ADR 0015). 어댑터를 만들어 넘기는 자리는 `main.py` 이고 라우터는 받은
    것만 쓴다(ADR 0010).

    채널의 실행은 앱의 수명이 소유한다. 채널 라우터가 들고 온 수명이 앱의 수명에 합쳐지므로 서버가
    수명을 열어야 실행을 받고, 닫으면 남은 실행이 취소된다(ADR 0014).

    빈 토큰을 거부하는 이유는 인증 없이 도는 면을 기본값으로 남기지 않기 위해서다(ADR 0011). 같은
    두 토큰을 거부하는 이유는 같으면 토큰을 가른 것이 무효인데 요청 시점에는 그것을 알아챌 길이
    없어서다(ADR 0015). 진단과 종료 코드로 그것을 운영자에게 말하는 것은 `serve` 의 몫이고,
    여기서는 그런 앱이 만들어지지 않는다는 것까지다.

    미들웨어의 순서가 의도다. 추적 식별자가 바깥이라 인증이 낸 401 과 라우터가 낸 500 이 같은
    식별자를 들고 나간다. 나중에 건 것이 바깥이므로 인증을 먼저 건다.
    """
    if not admin_token or not channel_token:
        raise ValueError("관리 API 와 채널은 토큰 없이 설 수 없다")
    if admin_token == channel_token:
        raise ValueError("관리 토큰과 채널 토큰이 같으면 설 수 없다")
    app = FastAPI(
        title=_TITLE,
        description=_DESCRIPTION,
        version=version("agent-os"),
    )
    app.include_router(admin_router(health=Health(status="ok"), plugins=plugins, trace=trace))
    app.include_router(
        channel_router(
            plugins=plugins,
            model=model,
            tools=tools,
            trace=trace,
            clock=clock,
            principal=principal,
            stderr=stderr,
        )
    )
    install_error_handlers(app)
    app.add_middleware(RequireToken, default=admin_token, prefixes={CHANNEL_PREFIX: channel_token})
    app.add_middleware(AssignRequestId, stderr=stderr)
    return app
