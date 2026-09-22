"""관리 API 의 HTTP 표면. 에러 봉투와 예외를 상태 코드로 옮기는 표가 여기 한 곳에 있다.

성공 응답은 봉투로 감싸지 않는다. 생값이고 추적 식별자는 `X-Request-Id` 헤더로 나간다. 에러만
봉투이고 `code` 어휘는 상태 코드와 1:1 인 넷이다(ADR 0010). 표가 라우트마다 흩어지면 새 라우트가
같은 예외에 다른 답을 하므로 한 곳이고, `core` 의 예외는 상태 코드를 모른다.

라우트를 더하는 자리는 `admin_router()` 다. 이 티켓은 `/health` 하나만 두고 데이터 라우트는
04·05·06 이 채운다. 그 라우트들이 부재를 말하는 방법은 `HTTPException(404)` 이고 그것도 이 표를
지난다.

**실패 하나가 기록 한 줄이다.** 봉투를 만드는 것과 기록하는 것을 가른다 — 봉투 만들기는 질의라
부수효과가 없고, 기록은 `AssignRequestId` 가 응답이 나갈 때 한 번 한다. 부르는 쪽은
`remember_failure()` 로 남길 문구를 적어 둘 뿐이다. 둘을 한 함수에 두면 봉투만 필요한 호출자가
모르는 사이에 기록을 남긴다(`CODING_STANDARDS.md` 의 CQS).

**계약에 박히는 것들의 규약 둘.** pydantic 은 클래스 독스트링을 스키마의 `description` 으로 그대로
싣고 FastAPI 는 라우트 함수 이름으로 `operationId` 를 짓는다. 둘 다 `openapi.json` 에 들어가
슬라이스 3 의 생성 클라이언트가 읽으므로, **모델의 독스트링은 한 줄로 쓰고 논증은 `#` 주석에
둔다**(그러지 않으면 주석을 다듬는 것이 계약 변경으로 보인다). **라우트는 `operation_id` 를 손으로
준다**(기본값은 `read_health_health_get` 꼴이라 그대로 클라이언트의 함수 이름이 된다).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal, TextIO
from uuid import uuid4

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, TypeAdapter
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from agent_os.core.ports import PluginError

REQUEST_ID_HEADER = "X-Request-Id"
UNAUTHORIZED_MESSAGE = "토큰이 없거나 틀리다"

# 추적 식별자와 기록에 남길 문구를 담는 ASGI scope 의 키. 미들웨어와 예외 핸들러가 이것으로
# 만나, 헤더와 봉투가 같은 값을 쓰고 실패 하나가 한 줄만 남는다. 남의 키와 부딪히지 않게
# 패키지 이름을 앞에 둔다.
_REQUEST_ID_KEY = "agent_os.request_id"
_FAILURE_KEY = "agent_os.failure_detail"

_INVALID_REQUEST = "요청의 형식이 올바르지 않다"
# 예기치 않은 실패의 문구. 원인은 서버 기록에만 남는다 — 밖으로 내면 내부 사정이 함께 나간다.
_INTERNAL = "서버가 요청을 처리하지 못했다"


# StrEnum 인 이유는 생성 클라이언트가 이름 있는 타입을 받기 위해서다(ADR 0008 이 같은 이유로
# 골랐다). 값이 늘면 openapi.json 이 바뀌므로 어휘를 늘리는 것은 계약 변경이다.
class ErrorCode(StrEnum):
    """에러 봉투의 어휘. 상태 코드와 1:1 인 넷이다."""

    UNAUTHORIZED = "unauthorized"
    INVALID_REQUEST = "invalid_request"
    NOT_FOUND = "not_found"
    INTERNAL_ERROR = "internal_error"


class Violation(BaseModel):
    """형식 오류 하나. field 는 `query.limit` 처럼 점으로 이은 경로 문자열이다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    field: str
    message: str


# request_id 가 본문에 있는 것은 같은 값을 두 자리에 둔 것이 아니라 성공 응답을 감싸지 않기로 한
# 결과다(ADR 0010). 성공 쪽에서는 그 값이 헤더로만 나간다. violations 에 기본값을 두지 않는 이유는
# 그것이 곧 스키마의 required 에서 빠지는 것이라, 서버는 언제나 넷을 싣는데 생성 클라이언트는
# 선택 필드로 받게 되기 때문이다. 봉투를 만드는 자리가 한 곳이라 비용이 없다.
class ErrorEnvelope(BaseModel):
    """에러 응답의 모양. 성공 응답은 이것으로 감싸지 않는다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: ErrorCode
    message: str
    violations: tuple[Violation, ...]
    request_id: str


# 인증 없이 경계 밖으로 나가는 유일한 응답이다(스토리 42, ADR 0011). 값이 하나뿐인 것을 타입이
# 말한다 — 상태를 실어 나르는 자리가 되면 그 순간 이 응답이 인증 없이 구성을 알려 주는 창이 된다.
class Health(BaseModel):
    """살아 있다는 것만 답한다. 내부 구성을 싣지 않는다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["ok"]


class _ErrorDetail(BaseModel):
    """FastAPI 검증 오류 하나에서 읽는 것. 나머지 필드는 봉투에 싣지 않는다.

    pydantic 으로 다시 읽는 이유는 `RequestValidationError.errors()` 의 항목이 느슨한 타입이라
    손으로 좁히면 그 자리가 곧 타입 우회가 되기 때문이다(원칙 III).
    """

    model_config = ConfigDict(extra="ignore", frozen=True)

    loc: tuple[str | int, ...] = ()
    msg: str = ""


_DETAILS = TypeAdapter[tuple[_ErrorDetail, ...]](tuple[_ErrorDetail, ...])


@dataclass(frozen=True)
class _Failure:
    """예외 하나가 밖에서 어떻게 보이는가. 상태 코드와 문구와 형식 오류와 헤더가 한 항목이다.

    헤더가 여기 있는 이유는 상태 코드가 요구하는 헤더가 있기 때문이다. 405 의 `Allow` 는
    라우터가 예외에 붙여 주는데, 봉투를 새 응답으로 만들면서 버리면 RFC 9110 이 요구하는 것을
    잃는다.
    """

    status: int
    message: str
    violations: tuple[Violation, ...] = ()
    headers: Mapping[str, str] | None = None


# 상태 코드 하나가 어휘 하나다. 표 밖의 상태 코드는 계열로 접는다 — 그것은 우리가 고른 것이
# 아니라 프레임워크가 내는 것이고(메서드 불일치의 405 가 그렇다), 그때마다 어휘를 지어내면
# 생성 클라이언트가 아는 값의 집합이 조용히 자란다. 접는 규칙은 테스트가 고정한다.
_CODE_BY_STATUS = {
    401: ErrorCode.UNAUTHORIZED,
    404: ErrorCode.NOT_FOUND,
    422: ErrorCode.INVALID_REQUEST,
    500: ErrorCode.INTERNAL_ERROR,
}


def failure_for(error: Exception) -> _Failure:
    """예외를 상태 코드와 문구로 옮기는 표. 이 함수가 그 표의 유일한 자리다.

    갈래를 셋으로 나눠 두면 예외 하나를 더할 때 세 곳을 고쳐야 하므로 한 항목이 한 갈래다.
    부재(포트가 `None` 을 돌려준 것)는 라우트가 `HTTPException(404)` 로 말하고 그것이 첫 갈래로
    들어온다. `PluginError` 가 500 인 이유는 부재가 이미 404 로 갈려 남는 것이 "서버 디스크의
    파일이 깨졌다"뿐이고, 그것은 클라이언트가 재요청으로 고칠 수 있는 일이 아니기 때문이다.
    마지막 갈래만 문구를 덮는다 — 우리가 쓰지 않은 예외의 말은 내부 사정을 담는다.
    """
    match error:
        case StarletteHTTPException():
            return _Failure(
                status=error.status_code,
                message=str(error.detail),
                headers=error.headers,
            )
        case RequestValidationError():
            return _Failure(status=422, message=_INVALID_REQUEST, violations=_violations(error))
        case PluginError():
            return _Failure(status=500, message=str(error))
        case _:
            return _Failure(status=500, message=_INTERNAL)


def _code_for(status: int) -> ErrorCode:
    found = _CODE_BY_STATUS.get(status)
    if found is not None:
        return found
    return ErrorCode.INTERNAL_ERROR if status >= 500 else ErrorCode.INVALID_REQUEST


def _violations(error: RequestValidationError) -> tuple[Violation, ...]:
    details = _DETAILS.validate_python(error.errors())
    return tuple(
        Violation(field=".".join(str(part) for part in detail.loc), message=detail.msg)
        for detail in details
    )


def request_id_of(request: Request) -> str:
    """미들웨어가 심은 추적 식별자.

    `AssignRequestId` 가 최외곽이라 지금은 언제나 심겨 있다. 그래도 갈래가 있는 것은 scope 에서
    읽은 값이 문자열인지 타입이 모르기 때문이고, 빈 값을 봉투에 실으면 상관 키가 거짓이 되기
    때문이다.
    """
    found = request.scope.get(_REQUEST_ID_KEY)
    return found if isinstance(found, str) else _new_request_id()


def remember_failure(request: Request, detail: str) -> None:
    """이 요청이 왜 실패했는지 기록에 남길 문구를 적어 둔다(명령).

    실제 기록은 응답이 나갈 때 `AssignRequestId` 가 한 번 한다. 적어 두는 것과 기록하는 것을
    가른 이유는 실패 하나가 두 줄이 되지 않게 하기 위해서다.
    """
    request.scope[_FAILURE_KEY] = detail


def error_envelope(
    request: Request,
    *,
    status: int,
    message: str,
    violations: Sequence[Violation] = (),
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    """에러 봉투 하나(질의). 기록하지 않는다.

    헤더를 받는 이유는 상태 코드가 요구하는 헤더가 있기 때문이다 — 405 의 `Allow`, 401 의
    `WWW-Authenticate`. 봉투가 본문만 나르면 그것들이 응답에서 사라진다.
    """
    envelope = ErrorEnvelope(
        code=_code_for(status),
        message=message,
        violations=tuple(violations),
        request_id=request_id_of(request),
    )
    return JSONResponse(
        status_code=status,
        content=envelope.model_dump(mode="json"),
        headers=headers,
    )


class AssignRequestId(BaseHTTPMiddleware):
    """추적 식별자를 심고 응답에 실어 보내며, 실패 하나를 서버 기록에 한 줄 남긴다.

    이 미들웨어가 인증보다 바깥인 이유는 401 응답과 500 봉투가 같은 식별자를 들어야 하기
    때문이다. 등록된 예외 핸들러는 라우터 쪽(`ExceptionMiddleware`)에서 도는데, 거기 걸리지 않은
    예외는 여기까지 올라온다. 그것을 잡지 않으면 봉투가 아닌 기본 500 이 나가고 추적 식별자도
    없다.

    기록에 경로도 주체도 적지 않는다 — 누가 무엇을 조회했는지는 이 기능이 남기는 것이 아니고
    (감사 로그는 비목표다), 이 한 줄은 실패 하나의 상관 키다.
    """

    def __init__(self, app: ASGIApp, *, stderr: TextIO) -> None:
        super().__init__(app)
        self._stderr = stderr

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = _new_request_id()
        request.scope[_REQUEST_ID_KEY] = request_id
        response = await self._answer(request, call_next)
        response.headers[REQUEST_ID_HEADER] = request_id
        if response.status_code >= 400:
            detail = _failure_detail(request)
            status = response.status_code
            self._stderr.write(f"요청 실패: request_id={request_id} status={status} {detail}\n")
        return response

    async def _answer(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """정상 흐름과 예기치 않은 실패를 가른다(`CODING_STANDARDS.md` 의 에러 처리 분리)."""
        try:
            return await call_next(request)
        except Exception as error:
            remember_failure(request, _detail_of(error))
            return error_envelope(request, status=500, message=_INTERNAL)


def install_error_handlers(app: FastAPI) -> None:
    """예외를 상태 코드로 옮기는 표를 앱에 건다. 라우트가 각자 거는 자리를 두지 않는다."""

    async def handle(request: Request, error: Exception) -> Response:
        failure = failure_for(error)
        remember_failure(request, _detail_of(error))
        return error_envelope(
            request,
            status=failure.status,
            message=failure.message,
            violations=failure.violations,
            headers=failure.headers,
        )

    app.add_exception_handler(StarletteHTTPException, handle)
    app.add_exception_handler(RequestValidationError, handle)
    app.add_exception_handler(PluginError, handle)


def admin_router(*, health: Health) -> APIRouter:
    """관리 라우터. 지금은 `/health` 하나이고 데이터 라우트는 04·05·06 이 이 자리에 더한다.

    `/health` 가 주입받은 값을 그대로 돌려주는 것이 이 라우트의 전부다. 라우트가 상태를 직접
    읽으면 인증 없이 나가는 유일한 응답이 내부 구성을 알려 주는 창이 된다(ADR 0011).
    """
    router = APIRouter(
        responses={500: {"model": ErrorEnvelope, "description": "서버가 요청을 처리하지 못했다"}}
    )

    @router.get(
        "/health",
        operation_id="read_health",
        summary="살아 있는지만 답한다",
        response_model=Health,
    )
    def read_health() -> Health:
        return health

    return router


def _failure_detail(request: Request) -> str:
    """기록에 남길 문구(질의). 적어 둔 것이 없으면 상태 코드만 남는다."""
    found = request.scope.get(_FAILURE_KEY)
    return found if isinstance(found, str) else ""


def _detail_of(error: Exception) -> str:
    """서버 기록에만 가는 문구. 밖으로 나가는 `message` 와 가른 이유는 예기치 않은 실패의 원인을
    운영자는 봐야 하고 클라이언트는 보면 안 되기 때문이다."""
    return f"{type(error).__name__}: {error}"


def _new_request_id() -> str:
    """실행 식별자가 아니다. `Clock` 포트를 쓰지 않는 이유가 그것이다 — 이것은 요청 하나의 상관
    키이고 트레이스에 남지 않는다."""
    return uuid4().hex
