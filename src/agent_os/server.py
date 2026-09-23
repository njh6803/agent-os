"""HTTP 표면의 조립 층. `create_app()` 하나만 내보낸다(ADR 0010).

모듈 수준 전역 `app` 을 두지 않는다. 두면 어댑터를 넘길 자리가 없어져 조립 층이 둘로 갈리고,
import 시점에 플러그인 경로와 트레이스 디렉터리가 고정되어 테스트가 가짜 포트 대신 진짜
파일시스템을 쓰게 된다.

라우터를 마운트하는 자리도 여기다. 이번에는 관리 라우터 하나뿐이고 `http-channel` 이 `/runs` 를
더한다. 채널과 관리는 서로를 import 하지 않는다.
"""

from __future__ import annotations

from importlib.metadata import version
from typing import TextIO

from fastapi import FastAPI

from agent_os.admin.auth import RequireToken
from agent_os.admin.http import AssignRequestId, Health, admin_router, install_error_handlers
from agent_os.core.ports import PluginSource, TraceStore

_TITLE = "Agent OS 관리 API"
_DESCRIPTION = "등록된 플러그인과 지나간 실행을 읽는다. 읽기 전용이고 실행을 일으키지 않는다."


def create_app(
    *,
    plugins: PluginSource,
    trace: TraceStore,
    token: str,
    stderr: TextIO,
) -> FastAPI:
    """관리 API 앱 하나. 포트는 부르는 쪽이 만들어 넘긴다.

    도구 포트를 받지 않는다. 조회 하나가 MCP 서버 여럿을 띄우는 것이 구조적으로 불가능하다는
    뜻이고, 서버 하나가 죽어 있을 때 목록이 통째로 실패하는 길을 시그니처가 먼저 닫는다.

    포트 둘은 관리 라우터에 넘어가 플러그인 포트는 `/plugins` 둘이, 트레이스 포트는 `/traces` 둘이
    쓴다. 어댑터를 만들어 넘기는 자리는 `main.py` 이고 라우터는 받은 것만 쓴다(ADR 0010).

    빈 토큰을 거부하는 이유는 인증 없이 도는 서버를 기본값으로 남기지 않기 위해서다(ADR 0011).
    진단과 종료 코드로 그것을 운영자에게 말하는 것은 `serve` 의 몫이고, 여기서는 그런 앱이
    만들어지지 않는다는 것까지다.

    미들웨어의 순서가 의도다. 추적 식별자가 바깥이라 인증이 낸 401 과 라우터가 낸 500 이 같은
    식별자를 들고 나간다. 나중에 건 것이 바깥이므로 인증을 먼저 건다.
    """
    if not token:
        raise ValueError("관리 API 는 토큰 없이 설 수 없다")
    app = FastAPI(
        title=_TITLE,
        description=_DESCRIPTION,
        version=version("agent-os"),
    )
    app.include_router(admin_router(health=Health(status="ok"), plugins=plugins, trace=trace))
    install_error_handlers(app)
    app.add_middleware(RequireToken, token=token)
    app.add_middleware(AssignRequestId, stderr=stderr)
    return app
