"""HTTP 표면의 에러. 에러 봉투와 예외를 상태 코드로 옮기는 표가 여기 한 곳에 있다(ADR 0016).

관리와 채널이 같은 계약 파일에 같은 에러 모양으로 실리므로 봉투는 한 벌이다. 둘이면 컴포넌트 이름이
부딪히거나 언젠가 어긋난다. 성공 응답은 봉투로 감싸지 않는다. 생값이고 추적 식별자는
`X-Request-Id` 헤더로 나간다. 에러만 봉투이고 `code` 어휘는 상태 코드와 1:1 이다(ADR 0010). 표가
라우트마다 흩어지면 새 라우트가 같은 예외에 다른 답을 하므로 한 곳이고, `core` 의 예외는 상태
코드를 모른다.

**표는 면을 인자로 받는다**(ADR 0023 과 그 2026-10-05 이력). 운영자 면(관리와 `/runs`)은 원문을
싣고, 최종 사용자 면은 남의 실행이 있다는 것과 내부 사정을 드러내지 않게 덮는다. 덮는 것도 이 표
안이라 예외 하나를 두 면이 다르게 번역하는 자리가 하나다. 서버 기록은 덮기 전의 것을 남긴다.

**실패 하나가 기록 한 줄이다.** 봉투를 만드는 것과 기록하는 것을 가른다 — 봉투 만들기는 질의라
부수효과가 없고, 기록은 `AssignRequestId` 가 응답이 나갈 때 한 번 한다. 부르는 쪽은
`remember_failure()` 로 남길 문구를 적어 둘 뿐이다. 둘을 한 함수에 두면 봉투만 필요한 호출자가
모르는 사이에 기록을 남긴다(`CODING_STANDARDS.md` 의 CQS).

**계약에 박히는 모델의 독스트링은 한 줄로 쓰고 논증은 `#` 주석에 둔다.** pydantic 이 클래스
독스트링을 스키마의 `description` 으로 그대로 싣고 그것이 `openapi.json` 에 들어가 생성 클라이언트가
읽는다. 그러지 않으면 주석을 다듬는 것이 계약 변경으로 보인다.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import TextIO
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, TypeAdapter
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from agent_os.core.ports import (
    Absent,
    DifferentPrincipal,
    Disabled,
    NotContinuable,
    NotResumable,
    PluginError,
)
from agent_os.http.paths import is_under

REQUEST_ID_HEADER = "X-Request-Id"
UNAUTHORIZED_MESSAGE = "토큰이 없거나 틀리다"
INVALID_REQUEST_MESSAGE = "요청의 형식이 올바르지 않다"
# 예기치 않은 실패의 문구. 원인은 서버 기록에만 남는다 — 밖으로 내면 내부 사정이 함께 나간다.
INTERNAL_MESSAGE = "서버가 요청을 처리하지 못했다"
# 없다는 것의 문구. 계약의 404 설명이고, 최종 사용자 면의 404 는 전부 이 문구 하나다 — 덮인 404 와
# 본래의 404 가 메시지로 갈리면 덮은 뜻이 없고, 표는 요청이 댄 식별자를 모르므로 본래 메시지를 지어
# 맞출 수 없다.
NOT_FOUND_MESSAGE = "찾는 것이 없다"
# 최종 사용자 면에서 운영자가 꺼 둔 것을 부른 409 의 문구. 꺼진 것의 종류도 이름도 들지 않는다 —
# 일시적인 것(409)과 영구적인 것(404)만 가른다(ADR 0017 의 2026-10-03 이력). 계약의 설명은 공유 409
# 설명 그대로다.
UNAVAILABLE_MESSAGE = "에이전트를 지금 쓸 수 없다"

# 추적 식별자와 기록에 남길 문구를 담는 ASGI scope 의 키. 미들웨어와 예외 핸들러가 이것으로
# 만나, 헤더와 봉투가 같은 값을 쓰고 실패 하나가 한 줄만 남는다. 남의 키와 부딪히지 않게
# 패키지 이름을 앞에 둔다.
_REQUEST_ID_KEY = "agent_os.request_id"
_FAILURE_KEY = "agent_os.failure_detail"


# StrEnum 인 이유는 생성 클라이언트가 이름 있는 타입을 받기 위해서다(ADR 0008 이 같은 이유로
# 골랐다). 값이 늘면 openapi.json 이 바뀌므로 어휘를 늘리는 것은 계약 변경이다. 어휘는 여섯이다.
# conflict 는 대상이 있지만 그 상태나 주체가 요청을 허락하지 않는 409 다. 표가 재개 불가
# (`NotResumable`), 꺼진 플러그인(`Disabled`), 다른 주체(`DifferentPrincipal`, 운영자 면), 이어 갈
# 수 없음(`NotContinuable`)을 거기로 옮기고, 관리 라우트는 내지 않는다(ADR 0010 의 2026-09-24·
# 2026-09-26 이력, ADR 0017, ADR 0022). 여섯째인 too_many_requests 는 요청하는 쪽의 상한에 걸린
# 429 다 — 대상의 상태가 아니라 요청하는 쪽의 사정이라 409 의 뜻이 맞지 않는다(ADR 0023, ADR 0010
# 의 2026-10-03 이력). 최종 사용자 면의 라우트가 계약에 적고, 관리 라우트도 운영자 채널도 내지
# 않는다.
class ErrorCode(StrEnum):
    """에러 봉투의 어휘. 상태 코드와 1:1 이다."""

    UNAUTHORIZED = "unauthorized"
    INVALID_REQUEST = "invalid_request"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    TOO_MANY_REQUESTS = "too_many_requests"
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
    409: ErrorCode.CONFLICT,
    422: ErrorCode.INVALID_REQUEST,
    429: ErrorCode.TOO_MANY_REQUESTS,
    500: ErrorCode.INTERNAL_ERROR,
}


class Surface(Enum):
    """요청이 어느 면의 것인가. 표가 같은 예외를 면마다 다르게 번역한다(ADR 0023).

    운영자 면(관리와 `/runs`)은 원문 그대로다. 최종 사용자 면은 둘로 갈린다 — 실행을 일으키는 시작
    경로와, 있는 실행을 가리키는 경로(결정, 구독)다. 둘이 가르는 것은 하위 타입이 아닌
    `PluginError`(기록이나 구성이 깨진 것) 하나다. 실행을 가리키는 경로에서 그것을 그대로 내면
    손상된 남의 트레이스가 있다는 것이 드러난다. 그래서 그 경로에서는 구성 오류도 404 가 되고 원인은
    서버 기록에 남는다(ADR 0023 의 2026-10-05 이력). 불리언 둘이 아니라 열거 하나인 이유는
    `CODING_STANDARDS.md` 의 불리언 플래그 인자다.
    """

    OPERATOR = "operator"
    END_USER_START = "end_user_start"
    END_USER_RUN = "end_user_run"


@dataclass(frozen=True)
class EndUserPaths:
    """최종 사용자 면이 서는 자리. 조립 층이 채널의 접두사와 시작 경로를 넘긴다.

    면은 요청의 경로로 정한다. 접두사 비교는 인증 표와 같은 `is_under` 하나라, 서명 토큰으로 열린
    경로와 최종 사용자 면으로 번역되는 경로가 갈리지 않는다. 시작 경로는 정확히 같은지만 본다 —
    실행을 가리키는 경로는 그 아래에 서므로 접두사로 보면 둘이 섞인다.
    """

    prefix: str
    start: str

    def surface_of(self, path: str) -> Surface:
        """경로 하나의 면(질의)."""
        if not is_under(path, self.prefix):
            return Surface.OPERATOR
        return Surface.END_USER_START if path == self.start else Surface.END_USER_RUN


def failure_for(error: Exception, surface: Surface) -> _Failure:
    """예외를 상태 코드와 문구로 옮기는 표. 이 함수가 그 표의 유일한 자리다.

    갈래를 셋으로 나눠 두면 예외 하나를 더할 때 세 곳을 고쳐야 하므로 한 항목이 한 갈래다.
    관리 쪽 부재(포트가 `None` 을 돌려준 것)는 라우트가 `HTTPException(404)` 로 말하고 그것이 첫
    갈래로 들어온다. core 의 실행 전 실패는 타입으로 갈려 오고 여기가 MRO 로 옮긴다(ADR 0014) —
    부재 404, 재개 불가 409, 꺼짐 409, 다른 주체 409, 이어 갈 수 없음 409, 그 밖의 `PluginError`
    500. 하위 타입의 갈래가 기반 타입보다 먼저여야 한다. 뒤집히면 전부 500 이 된다. 기준은
    "깨졌나"다(ADR 0014 의 2026-09-26 이력) — 4xx 는 대상이 없거나 대상의 상태나 주체가 요청을
    허락하지 않는 것이고, `PluginError` 가 500 인 이유는 하위 타입 다섯을 뺀 뒤 남는 것이 "서버의
    구성이나 기록이 깨졌다"뿐이기 때문이다. 마지막 갈래만 문구를 덮는다 — 우리가 쓰지 않은 예외의
    말은 내부 사정을 담는다.

    최종 사용자 면은 그 위에서 덮는다(ADR 0023 과 그 2026-10-05 이력). 404 는 전부 고정 문구 하나다.
    다른 주체(409)는 없는 실행과 같은 404 다. 실행을 가리키는 경로의 하위 타입이 아닌
    `PluginError`(500, 기록이나 구성이 깨진 것)도 404 다 — 손상이 주체 판정보다 앞이라(core) 남의
    손상된 실행이 500 으로 그 존재를 드러내기 때문이고, 구성 오류까지 404 가 되는 것이 그 대가다.
    시작 경로의 그것은 500 이되 고정 문구다. 꺼짐(409)은 종류와 이름 없는 고정 문구다. 재개 불가와
    이어 갈 수 없음은 자기 실행의 상태라 메시지 그대로다.
    """
    operator = surface is Surface.OPERATOR
    match error:
        case StarletteHTTPException():
            status = error.status_code
            detail = str(error.detail)
            return _Failure(
                status=status,
                message=detail if operator or status != 404 else NOT_FOUND_MESSAGE,
                headers=error.headers,
            )
        case RequestValidationError():
            return _Failure(
                status=422, message=INVALID_REQUEST_MESSAGE, violations=_violations(error)
            )
        case Absent():
            return _Failure(status=404, message=str(error) if operator else NOT_FOUND_MESSAGE)
        case DifferentPrincipal():
            if operator:
                return _Failure(status=409, message=str(error))
            return _Failure(status=404, message=NOT_FOUND_MESSAGE)
        case Disabled():
            return _Failure(status=409, message=str(error) if operator else UNAVAILABLE_MESSAGE)
        case NotResumable() | NotContinuable():
            return _Failure(status=409, message=str(error))
        case PluginError():
            match surface:
                case Surface.OPERATOR:
                    return _Failure(status=500, message=str(error))
                case Surface.END_USER_START:
                    return _Failure(status=500, message=INTERNAL_MESSAGE)
                case Surface.END_USER_RUN:
                    return _Failure(status=404, message=NOT_FOUND_MESSAGE)
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

    이 미들웨어가 앱에 거는 것 가운데 가장 바깥인 이유는 모든 응답이 같은 식별자를 들어야 하기
    때문이다 — 인증이 낸 401, 표가 낸 봉투, CORS 미들웨어가 직접 답한 preflight 까지. 봉투를 만드는
    자리는 이보다 안쪽이고 봉투의 `request_id` 는 여기서 심은 값을 읽는다.

    기록에 경로도 주체도 적지 않는다 — 누가 무엇을 조회했는지는 이 기능이 남기는 것이 아니고
    (감사 로그는 비목표다), 이 한 줄은 실패 하나의 상관 키다. 적어 둔 문구가 없는 실패(CORS
    미들웨어가 답한 preflight 의 400)는 상태 코드만 남는다.

    핸들러가 놓친 예외를 봉투로 바꾸는 일은 여기가 아니라 `CatchUnexpected` 다. 둘이 한
    미들웨어면 그 변환이 CORS 보다 바깥에 서서 최종 사용자 면의 예기치 않은 500 에 CORS 헤더가
    붙지 않는다(end-user-channel 명세 "CORS", `cors_scoped.py` 사례 7 과 대조군 7').
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
    """핸들러가 놓친 예외를 그 요청의 면으로 번역해 봉투로 답한다.

    등록된 예외 핸들러는 라우터 쪽(`ExceptionMiddleware`)에서 도는데, 거기 걸리지 않은 예외는
    여기까지 올라온다. 그것을 잡지 않으면 봉투가 아닌 기본 500 이 나가고 추적 식별자도 없다.
    예기치 않은 예외는 어느 면에서나 같은 고정 문구지만, 핸들러를 비켜 온 `PluginError` 가 최종
    사용자 면에서 원문으로 나가지 않게 면을 넘긴다.

    자리는 인증의 바깥이고 CORS 의 안쪽이다. 최종 사용자 접두사에서 CORS 가 이것을 감싸야 그 500
    에도 CORS 헤더가 붙는다. 운영자 면에서는 식별자 심기와 인증 사이, 갈라지기 전과 같은 자리다.

    여기서도 `failure_for()` 를 지나는 이유는 표가 한 곳이어야 하기 때문이다. 이 자리에서 500 을
    직접 만들면 "예상 밖 예외는 500" 이 두 곳에 있게 되고, 표의 마지막 갈래는 아무도 가지 않는
    죽은 코드가 된다(PR 봇 둘이 같은 자리에 닿았다).
    """

    def __init__(self, app: ASGIApp, *, end_user: EndUserPaths) -> None:
        super().__init__(app)
        self._end_user = end_user

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except Exception as error:
            return _answered(request, error, self._end_user.surface_of(request.url.path))


def install_error_handlers(app: FastAPI, *, end_user: EndUserPaths) -> None:
    """예외를 상태 코드로 옮기는 표를 앱에 건다. 라우트가 각자 거는 자리를 두지 않는다.

    `PluginError` 하나를 걸면 하위 타입도 여기로 온다. 핸들러를 찾는 것이 예외의 MRO 를 따라서다.
    면은 요청의 경로로 정한다. 라우트는 상태 코드도 면도 스스로 정하지 않는다.
    """

    async def handle(request: Request, error: Exception) -> Response:
        return _answered(request, error, end_user.surface_of(request.url.path))

    app.add_exception_handler(StarletteHTTPException, handle)
    app.add_exception_handler(RequestValidationError, handle)
    app.add_exception_handler(PluginError, handle)


def _answered(request: Request, error: Exception, surface: Surface) -> JSONResponse:
    """예외 하나를 표에 넣어 봉투로 답하고 기록할 문구를 적어 둔다. 핸들러와 미들웨어가 같이 쓴다.

    표를 지나는 자리가 이 하나다. 기록은 덮기 전의 것(운영자 면의 번역)을 남긴다 — 최종 사용자 면이
    404 로 덮은 500 의 원인을 운영자가 그 추적 식별자로 찾아야 한다(스토리 52). 덮어 상태 코드가
    바뀌었으면 원래 상태 코드도 적는다. 응답의 상태 코드는 기록 줄의 앞에 따로 실린다.
    """
    shown = failure_for(error, surface)
    original = failure_for(error, Surface.OPERATOR)
    detail = _detail_of(error, original)
    if original.status != shown.status:
        detail = f"원래 상태 {original.status} {detail}"
    remember_failure(request, detail)
    return _enveloped(request, shown)


def _enveloped(request: Request, failure: _Failure) -> JSONResponse:
    """표가 정한 것을 봉투로 펼친다(질의). 기록은 부르는 쪽이 먼저 적어 둔다."""
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

    형식 오류는 위치와 문구만 싣는다. 검증 오류의 문자열은 받은 값을 되울리는데, 채널의 본문은
    사람이 쓴 요청 문자열이다(원칙 V). 표가 뽑은 `violations` 그대로라 기록과 응답이 같은 말을 한다.
    """
    name = type(error).__name__
    if failure.violations:
        return f"{name}: " + "; ".join(f"{v.field}: {v.message}" for v in failure.violations)
    return f"{name}: {error}"


def _new_request_id() -> str:
    """실행 식별자가 아니다. `Clock` 포트를 쓰지 않는 이유가 그것이다 — 이것은 요청 하나의 상관
    키이고 트레이스에 남지 않는다."""
    return uuid4().hex
