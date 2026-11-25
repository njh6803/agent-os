"""위젯 관리 서버의 HTTP 표면을 짓는 자리(ADR 0064).

앱을 만드는 함수는 `create_app()` 하나이고 모듈 수준 전역 `app` 이 없다. 전역 앱은 import 시점에
데이터베이스를 고정해 시험이 시험마다 다른 데이터베이스를 쓰지 못하게 하고, 내보내기 도구가 앱을
짓는 것만으로 데이터베이스에 닿게 된다. 데이터베이스 객체는 기본값 없는 인자로 받는다.

**미들웨어는 바깥에서 안쪽으로 `AssignRequestId` → 응답 머리 → `CatchUnexpected` → 라우터다.**
추적 식별자를 심는 것이 가장 바깥이라 모든 응답이 같은 식별자를 든다. 머리를 다는 자리가
`CatchUnexpected` 보다 바깥이라 핸들러가 놓친 예외의 500에도 머리가 붙는다. 데이터베이스 확인
(티켓 03)은 그보다 더 바깥에 선다. 머리를 달아야 하는 경로는 경로로 가르고, 그 비교는 `is_under`
하나다.

**읽는 경로의 갈래는 넷이다.** 등록된 이름은 200, 등록되지 않은 이름과 꼴이 틀린 이름은 글자까지
같은 404 봉투, 데이터베이스가 답하지 못하면 500 봉투다. 꼴은 `re.fullmatch` 로 이름 전체에 걸고 꼴이
틀린 이름은 데이터베이스에 묻지 않는다. 경로 인자의 `pattern` 은 쓰지 않는다. 그것은 맞지 않는
이름에 422 를 내어 등록되지 않은 이름의 404 와 갈린다. 꼴이 틀린 이름과 등록되지 않은 이름의 답이
같아야 위젯이 이름의 꼴을 따로 알 필요가 없다.
"""

from __future__ import annotations

import importlib.metadata
from typing import Literal, TextIO

from fastapi import APIRouter, FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from widget_admin.database import WidgetAdminDatabase
from widget_admin.errors import (
    INTERNAL_MESSAGE,
    INVALID_REQUEST_MESSAGE,
    NOT_FOUND_MESSAGE,
    AssignRequestId,
    CatchUnexpected,
    ErrorEnvelope,
    install_error_handlers,
)
from widget_admin.paths import is_under
from widget_admin.settings import WidgetSettings, is_site_name

WIDGET_SETTINGS_PREFIX = "/widget-settings"

# 다른 출처의 페이지가 읽도록 여는 머리 셋. 위젯은 사이트의 페이지에서 돌아 출처가 사이트마다
# 다르다. 허용 출처가 `*` 하나이고 자격 증명을 허락하지 않으므로 출처를 견줄 일이 없다. 그래서
# Starlette 의 CORS 미들웨어를 쓰지 않는다. 그것이 하는 일(출처 견주기, preflight 답하기)이 하나도
# 들지 않는다. `Allow-Methods` 와 `Allow-Credentials` 를 싣지 않는다.
_OPEN_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Expose-Headers": "X-Request-Id",
    "Cache-Control": "no-store",
}

# 라우트가 계약에 적는 에러와 그 설명. 422 를 적지 않으면 FastAPI 가 자기 모양
# (`HTTPValidationError`)을 붙여 계약이 봉투가 아닌 것을 약속한다. 이 라우트는 경로 인자에 제약이
# 없어 422 를 내지 않지만, 라우터가 모든 라우트에 붙이는 것이라 봉투로 적어 둔다.
_DOCUMENTED_ERRORS = {
    404: NOT_FOUND_MESSAGE,
    422: INVALID_REQUEST_MESSAGE,
    500: INTERNAL_MESSAGE,
}


class Health(BaseModel):
    """살아 있다는 것만 답한다. 내부 구성을 싣지 않는다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["ok"]


class _OpenHeaders(BaseHTTPMiddleware):
    """위젯 설정 접두사 아래의 모든 응답에 머리 셋을 단다. 에러 응답에도 붙는다."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        if is_under(request.url.path, WIDGET_SETTINGS_PREFIX):
            for name, value in _OPEN_HEADERS.items():
                response.headers[name] = value
        return response


def _documented_errors() -> dict[int | str, dict[str, object]]:
    return {
        status: {"model": ErrorEnvelope, "description": description}
        for status, description in _DOCUMENTED_ERRORS.items()
    }


def _product_version() -> str:
    """계약의 `info.version`. 설치된 `widget-admin` 묶음의 판이다."""
    return importlib.metadata.version("widget-admin")


def _router(database: WidgetAdminDatabase) -> APIRouter:
    router = APIRouter()

    @router.get(
        f"{WIDGET_SETTINGS_PREFIX}/{{site}}",
        operation_id="read_widget_settings",
        response_model=WidgetSettings,
        responses=_documented_errors(),
        summary="사이트 하나의 위젯 설정을 읽는다",
    )
    async def read_widget_settings(site: str) -> WidgetSettings:
        # 꼴이 틀린 이름은 데이터베이스에 묻지 않고 등록되지 않은 이름과 같은 404 로 답한다.
        if not is_site_name(site):
            raise HTTPException(status_code=404)
        found = await database.read_widget_settings(site)
        if found is None:
            raise HTTPException(status_code=404)
        return found

    @router.get("/health", operation_id="read_health", response_model=Health)
    async def read_health() -> Health:
        # 프로세스가 답하는지만 본다. 데이터베이스에 묻지 않는다.
        return Health(status="ok")

    return router


def create_app(*, database: WidgetAdminDatabase, stderr: TextIO) -> FastAPI:
    """위젯 관리 서버의 앱을 짓는다. 데이터베이스 객체와 실패 기록을 남길 출력을 받는다."""
    # 끝 `/` 를 다르게 쓴 경로를 다른 경로로 돌려보내지 않는다. 돌려보내면 사이트 이름 뒤에 `/` 를
    # 붙인 요청이 307 로 갈라 위젯이 갈래를 가르게 된다.
    app = FastAPI(
        title="위젯 관리 서버",
        version=_product_version(),
        redirect_slashes=False,
    )
    install_error_handlers(app)
    app.include_router(_router(database))
    # 나중에 건 것이 바깥이다. 안쪽에서 바깥으로 변환, 머리, 식별자 순이다.
    app.add_middleware(CatchUnexpected)
    app.add_middleware(_OpenHeaders)
    app.add_middleware(AssignRequestId, stderr=stderr)
    return app
