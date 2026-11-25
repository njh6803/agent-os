"""오류 봉투와 추적 식별자, 예외를 상태 코드로 옮기는 표(ADR 0064).

`agent_os.http.errors` 의 사본이고 봉투의 네 필드 `{code, message, violations, request_id}` 가 같다.
두 설치 묶음은 서로를 import 하지 않으므로 사본을 둔다. 사본은 위젯 관리 서버가 쓰는 만큼만 든다.
면이 하나이고 core 의 예외가 없어, 표는 예외 셋(프레임워크의 HTTP 예외, 요청 검증 오류, 그 밖)만
가른다. `code` 의 어휘는 `invalid_request` 422, `not_found` 404, `internal_error` 500 이고 표 안의
상태 코드와 1:1 이다. 표 밖의 상태 코드는 계열로 접는다(5xx 는 `internal_error`, 그 밖의 4xx 는
`invalid_request`). portal-admin 이 401, 409 같은 갈래를 더할 때 어휘를 늘리고, 그 값은 Agent OS 의
같은 상태 코드의 값과 같은 글자로 둔다.

**실패 하나가 기록 한 줄이다.** 봉투를 만드는 것과 기록하는 것을 가른다. 봉투 만들기는 질의라
부수효과가 없고, 기록은 `AssignRequestId` 가 응답이 나갈 때 한 번 한다. 기록에는 경로도 사이트
이름도 적지 않는다. 사이트 이름은 누구나 고를 수 있는 값이라, 적으면 기록에 남이 적은 글이 들어간다.

**계약에 박히는 모델의 독스트링은 한 줄로 쓰고 논증은 `#` 주석에 둔다.** pydantic 이 클래스
독스트링을 스키마의 `description` 으로 그대로 싣고 그것이 계약 파일에 들어간다.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import TextIO
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, TypeAdapter
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

REQUEST_ID_HEADER = "X-Request-Id"
INVALID_REQUEST_MESSAGE = "요청의 형식이 올바르지 않다"
# 없다는 것의 문구. 계약의 404 설명이고 404 는 전부 이 문구 하나다. 등록되지 않은 이름과 꼴이 틀린
# 이름과 라우터가 찾지 못한 경로가 글자까지 같아야 위젯이 갈래를 가르지 못한다. Agent OS 의 최종
# 사용자 면이 쓰는 고정 문구와 같다.
NOT_FOUND_MESSAGE = "찾는 것이 없다"
# 예기치 않은 실패의 문구. 원인은 서버 기록에만 남는다. 밖으로 내면 내부 사정이 함께 나간다.
INTERNAL_MESSAGE = "서버가 요청을 처리하지 못했다"

# 추적 식별자와 기록에 남길 문구를 담는 ASGI scope 의 키. 미들웨어와 예외 핸들러가 이것으로 만나,
# 헤더와 봉투가 같은 값을 쓰고 실패 하나가 한 줄만 남는다. 남의 키와 부딪히지 않게 패키지 이름을
# 앞에 둔다.
_REQUEST_ID_KEY = "widget_admin.request_id"
_FAILURE_KEY = "widget_admin.failure_detail"


# StrEnum 인 이유는 생성 클라이언트가 이름 있는 타입을 받기 위해서다. 값이 늘면 계약 파일이
# 바뀌므로 어휘를 늘리는 것은 계약 변경이다.
class ErrorCode(StrEnum):
    """에러 봉투의 어휘. 표 안의 상태 코드와 1:1 이다."""

    INVALID_REQUEST = "invalid_request"
    NOT_FOUND = "not_found"
    INTERNAL_ERROR = "internal_error"


class Violation(BaseModel):
    """형식 오류 하나. field 는 `query.limit` 처럼 점으로 이은 경로 문자열이다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    field: str
    message: str


# violations 에 기본값을 두지 않는 이유는 그것이 곧 스키마의 required 에서 빠지는 것이라, 서버는
# 언제나 넷을 싣는데 생성 클라이언트는 선택 필드로 받게 되기 때문이다. 봉투를 만드는 자리가 한
# 곳이라 비용이 없다. request_id 가 본문에 있는 것은 성공 응답을 감싸지 않기로 한 결과다. 성공
# 쪽에서는 그 값이 헤더로만 나간다.
class ErrorEnvelope(BaseModel):
    """에러 응답의 모양. 성공 응답은 이것으로 감싸지 않는다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: ErrorCode
    message: str
    violations: tuple[Violation, ...]
    request_id: str


class _ErrorDetail(BaseModel):
    """FastAPI 검증 오류 하나에서 읽는 것. 나머지 필드는 봉투에 싣지 않는다.

    pydantic 으로 다시 읽는 이유는 `RequestValidationError.errors()` 의 항목이 느슨한 타입이라
    손으로 좁히면 그 자리가 곧 타입 우회가 되기 때문이다.
    """

    model_config = ConfigDict(extra="ignore", frozen=True)

    loc: tuple[str | int, ...] = ()
    msg: str = ""


_DETAILS = TypeAdapter[tuple[_ErrorDetail, ...]](tuple[_ErrorDetail, ...])


@dataclass(frozen=True)
class _Failure:
    """예외 하나가 밖에서 어떻게 보이는가. 상태 코드와 문구와 형식 오류와 헤더가 한 항목이다.

    헤더가 여기 있는 이유는 상태 코드가 요구하는 헤더가 있기 때문이다. 405 의 `Allow` 는 라우터가
    예외에 붙여 주는데, 봉투를 새 응답으로 만들면서 버리면 RFC 9110 이 요구하는 것을 잃는다.
    """

    status: int
    message: str
    violations: tuple[Violation, ...] = ()
    headers: Mapping[str, str] | None = None


_CODE_BY_STATUS = {
    404: ErrorCode.NOT_FOUND,
    422: ErrorCode.INVALID_REQUEST,
    500: ErrorCode.INTERNAL_ERROR,
}


def failure_for(error: Exception) -> _Failure:
    """예외를 상태 코드와 문구로 옮기는 표. 이 함수가 그 표의 유일한 자리다.

    라우트는 상태 코드를 스스로 정하지 않는다. 없는 것은 라우트가 `HTTPException(404)` 로 말하고
    그것이 첫 갈래로 들어온다. 라우터가 내는 404(경로 없음)와 405(메서드 불일치)도 같은 갈래다. 404
    는 어디서 났든 고정 문구 하나다. 그 밖의 예외는 500 이고 문구는 고정이다. 원인은 기록에만 간다.
    """
    match error:
        case StarletteHTTPException():
            status = error.status_code
            message = NOT_FOUND_MESSAGE if status == 404 else str(error.detail)
            return _Failure(status=status, message=message, headers=error.headers)
        case RequestValidationError():
            return _Failure(
                status=422, message=INVALID_REQUEST_MESSAGE, violations=_violations(error)
            )
        case _:
            return _Failure(status=500, message=INTERNAL_MESSAGE)


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

    `AssignRequestId` 가 최외곽이라 지금은 언제나 심겨 있다. 그래도 갈래가 있는 것은 scope 에서 읽은
    값이 문자열인지 타입이 모르기 때문이고, 빈 값을 봉투에 실으면 상관 키가 거짓이 되기 때문이다.
    """
    found = request.scope.get(_REQUEST_ID_KEY)
    return found if isinstance(found, str) else _new_request_id()


def remember_failure(request: Request, detail: str) -> None:
    """이 요청이 왜 실패했는지 기록에 남길 문구를 적어 둔다(명령).

    실제 기록은 응답이 나갈 때 `AssignRequestId` 가 한 번 한다. 적어 두는 것과 기록하는 것을 가른
    이유는 실패 하나가 두 줄이 되지 않게 하기 위해서다.
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
    """에러 봉투 하나(질의). 기록하지 않는다. 405 의 `Allow` 같은 상태 코드가 요구하는 헤더를
    받는다."""
    envelope = ErrorEnvelope(
        code=_code_for(status),
        message=message,
        violations=tuple(violations),
        request_id=request_id_of(request),
    )
    return JSONResponse(
        status_code=status, content=envelope.model_dump(mode="json"), headers=headers
    )


class AssignRequestId(BaseHTTPMiddleware):
    """추적 식별자를 심고 응답에 실어 보내며, 실패 하나를 서버 기록에 한 줄 남긴다.

    이 미들웨어가 앱에 거는 것 가운데 가장 바깥인 이유는 모든 응답이 같은 식별자를 들어야 하기
    때문이다. 기록에 경로도 사이트 이름도 적지 않는다. 이 한 줄은 실패 하나의 상관 키다. 핸들러가
    놓친 예외를 봉투로 바꾸는 일은 여기가 아니라 `CatchUnexpected` 다. 둘이 한 미들웨어면 그 변환이
    머리를 다는 미들웨어보다 바깥에 서서 예기치 않은 500 에 머리가 붙지 않는다.
    """

    def __init__(self, app: ASGIApp, *, stderr: TextIO) -> None:
        super().__init__(app)
        self._stderr = stderr

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = _new_request_id()
        request.scope[_REQUEST_ID_KEY] = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        if response.status_code >= 400:
            detail = _failure_detail(request)
            status = response.status_code
            self._stderr.write(f"요청 실패: request_id={request_id} status={status} {detail}\n")
        return response


class CatchUnexpected(BaseHTTPMiddleware):
    """핸들러가 놓친 예외를 봉투로 바꿔 답한다.

    등록된 예외 핸들러는 라우터 쪽에서 도는데, 거기 걸리지 않은 예외는 여기까지 올라온다. 잡지
    않으면 봉투가 아닌 기본 500 이 나가고 추적 식별자도 없다. 자리는 머리를 다는 미들웨어의
    안쪽이다. 여기서도 `failure_for()` 를 지나는 이유는 표가 한 곳이어야 하기 때문이다.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except Exception as error:
            return _answered(request, error)


def install_error_handlers(app: FastAPI) -> None:
    """예외를 상태 코드로 옮기는 표를 앱에 건다. 라우트가 각자 거는 자리를 두지 않는다."""

    async def handle(request: Request, error: Exception) -> Response:
        return _answered(request, error)

    app.add_exception_handler(StarletteHTTPException, handle)
    app.add_exception_handler(RequestValidationError, handle)


def _answered(request: Request, error: Exception) -> JSONResponse:
    """예외 하나를 표에 넣어 봉투로 답하고 기록할 문구를 적어 둔다. 핸들러와 미들웨어가 같이
    쓴다."""
    failure = failure_for(error)
    remember_failure(request, _detail_of(error, failure))
    return error_envelope(
        request,
        status=failure.status,
        message=failure.message,
        violations=failure.violations,
        headers=failure.headers,
    )


def _failure_detail(request: Request) -> str:
    """기록에 남길 문구(질의). 적어 둔 것이 없으면 상태 코드만 남는다."""
    found = request.scope.get(_FAILURE_KEY)
    return found if isinstance(found, str) else ""


def _detail_of(error: Exception, failure: _Failure) -> str:
    """서버 기록에만 가는 문구(질의). 밖으로 나가는 `message` 와 가른 이유는 예기치 않은 실패의
    원인을 운영자는 봐야 하고 클라이언트는 보면 안 되기 때문이다.

    형식 오류는 위치와 문구만 싣는다. 검증 오류의 문자열은 받은 값을 되울리기 때문이다. 그 밖의
    예외는 글을 싣지 않고 원인 사슬의 클래스 이름만 싣는다. 드라이버와 서버가 낸 글에는 질의 문장과
    주소의 조각이 섞일 수 있고, 여러 줄이라 실패 하나가 기록 한 줄이라는 약속도 깬다.
    """
    name = type(error).__name__
    if failure.violations:
        return f"{name}: " + "; ".join(f"{v.field}: {v.message}" for v in failure.violations)
    if isinstance(error, StarletteHTTPException):
        return f"{name}: {error.detail}"
    return " <- ".join(type(item).__name__ for item in _chain(error))


def _chain(error: BaseException) -> list[BaseException]:
    """예외와 그 원인들(질의). 감싼 예외 안의 드라이버 예외까지 따라간다."""
    seen: list[BaseException] = []
    current: BaseException | None = error
    while current is not None and all(current is not item for item in seen):
        seen.append(current)
        current = current.__cause__ or current.__context__
    return seen


def _new_request_id() -> str:
    """요청 하나의 상관 키다. 위젯 설정의 어느 값과도 관계가 없다."""
    return uuid4().hex
