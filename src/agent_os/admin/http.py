"""관리 API 의 HTTP 표면. 에러 봉투와 예외를 상태 코드로 옮기는 표가 여기 한 곳에 있다.

성공 응답은 봉투로 감싸지 않는다. 생값이고 추적 식별자는 `X-Request-Id` 헤더로 나간다. 에러만
봉투이고 `code` 어휘는 상태 코드와 1:1 인 넷이다(ADR 0010). 표가 라우트마다 흩어지면 새 라우트가
같은 예외에 다른 답을 하므로 한 곳이고, `core` 의 예외는 상태 코드를 모른다.

라우트를 더하는 자리는 `admin_router()` 다. 데이터 라우트가 부재를 말하는 방법은
`HTTPException(404)` 이고 그것도 이 표를 지난다.

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
from typing import Annotated, Literal, TextIO
from uuid import uuid4

from fastapi import APIRouter, FastAPI, HTTPException, Path, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, TypeAdapter
from starlette.convertors import Convertor, register_url_convertor
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from agent_os.admin.traces import (
    CURSOR_PATTERN,
    Trace,
    TracePage,
    decode_cursor,
    trace_detail,
    trace_page,
)
from agent_os.core.ports import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    Cursor,
    ManifestRow,
    PluginError,
    PluginSource,
    RunStatus,
    TraceStore,
)
from agent_os.sdk import (
    PLUGIN_NAME_PATTERN,
    RUN_ID_PATTERN,
    PluginKind,
    PluginManifest,
    PluginName,
    RunId,
)

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

# 계약에 적는 에러와 그 설명. 라우트가 자기 `responses` 에 적는다. 401 은 미들웨어가 내는 것이라
# 프레임워크가 스키마에 넣어 주지 않고, 422 는 적지 않으면 FastAPI 가 제 모양
# (`HTTPValidationError`)을 붙여 계약이 봉투가 아닌 것을 약속하게 된다. 500 은 라우터가 건다.
_DOCUMENTED_ERRORS: Mapping[int, str] = {
    401: UNAUTHORIZED_MESSAGE,
    404: "찾는 것이 없다",
    422: _INVALID_REQUEST,
    500: _INTERNAL,
}


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


# core 의 표지(`ports.UnreadableManifest`)를 HTTP 로 옮긴 모양이다. 따로 두는 이유는 core 의
# 독스트링이 논증이라 그대로 계약의 description 이 되면 주석을 다듬는 것이 계약 변경으로 보이기
# 때문이다. 필드는 셋 그대로이고 이름이 PluginName 이 아닌 이유도 core 의 것과 같다 — 이 표지가
# 서는 경우 하나가 디렉터리 이름이 패턴을 어기는 것이다.
class UnreadableManifest(BaseModel):
    """매니페스트로 읽히지 않는 것의 표지. 종류와 이름과 이유를 든다. 매니페스트가 아니다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: PluginKind
    name: str
    reason: str


# 플러그인 목록의 행. 매니페스트는 sdk 의 것 그대로다(ADR 0010 의 2026-09-23 이력). 판별자가 없고
# required 필드로 갈린다 — 표지만 reason 을, 매니페스트만 schema_version 과 version 을 든다.
# 별칭에 이름을 주는 이유는 생성 클라이언트가 익명 유니온 대신 이 이름을 받게 하기 위해서다.
type PluginRow = PluginManifest | UnreadableManifest


class _Verbatim(Convertor[str]):
    """경로 파라미터 자리에 온 것을 슬래시와 개행까지 통째로 잡는다. 판정은 패턴이 한다.

    파일 경로로 조립되는 식별자는 이것으로 받는다. 기본 변환기(`[^/]+`)는 서버가 `%2F` 를 디코딩한
    `/` 앞에서 끊고, `path` 변환기(`.*`)는 개행을 넘지 못하는데 라우팅 정규식이 파이썬 `re` 라
    `$` 가 마지막 개행 앞에서도 맞는다. 어느 쪽이든 형식 위반이 422 가 아니라 라우팅 404 가 되거나
    개행이 떼어진 채 유효한 이름으로 읽힌다. 라우트가 맞은 뒤 패턴이 유일한 판정자여야 한다.
    """

    regex = r"[\s\S]*"

    def convert(self, value: str) -> str:
        return value

    def to_string(self, value: str) -> str:
        return value


# Starlette 의 공개 확장점이고 프로세스 전역 표에 키 하나를 둔다. 상태가 없고 같은 키로 다시 불러도
# 같은 것이 들어가므로, import 시점의 부수효과가 테스트와 앱 조립에 새는 것이 없다.
register_url_convertor("verbatim", _Verbatim())


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
        """정상 흐름과 예기치 않은 실패를 가른다(`CODING_STANDARDS.md` 의 에러 처리 분리).

        여기서도 `failure_for()` 를 지나는 이유는 표가 한 곳이어야 하기 때문이다. 이 자리에서
        500 을 직접 만들면 "예상 밖 예외는 500" 이 두 곳에 있게 되고, 표의 마지막 갈래는 아무도
        가지 않는 죽은 코드가 된다(PR 봇 둘이 같은 자리에 닿았다).
        """
        try:
            return await call_next(request)
        except Exception as error:
            remember_failure(request, _detail_of(error))
            return _enveloped(request, failure_for(error))


def install_error_handlers(app: FastAPI) -> None:
    """예외를 상태 코드로 옮기는 표를 앱에 건다. 라우트가 각자 거는 자리를 두지 않는다."""

    async def handle(request: Request, error: Exception) -> Response:
        remember_failure(request, _detail_of(error))
        return _enveloped(request, failure_for(error))

    app.add_exception_handler(StarletteHTTPException, handle)
    app.add_exception_handler(RequestValidationError, handle)
    app.add_exception_handler(PluginError, handle)


def admin_router(*, health: Health, plugins: PluginSource, trace: TraceStore) -> APIRouter:
    """관리 라우터. 데이터 라우트는 이 자리에 더한다.

    `/health` 가 주입받은 값을 그대로 돌려주는 것이 이 라우트의 전부다. 라우트가 상태를 직접
    읽으면 인증 없이 나가는 유일한 응답이 내부 구성을 알려 주는 창이 된다(ADR 0011).
    """
    router = APIRouter(responses=_documented_errors(500))

    @router.get(
        "/health",
        operation_id="read_health",
        summary="살아 있는지만 답한다",
        response_model=Health,
    )
    def read_health() -> Health:
        return health

    # 두 플러그인 라우트는 매니페스트를 통째로 내보내므로 mcp 매니페스트의 command 와 args 도
    # 나간다. 가리지 않는 것이 결정이고 경계는 인증이다(ADR 0009 의 2026-09-22 이력, 네 번째 열린
    # 문제). MCP 서버에는 붙지 않는다 — 이 라우터는 도구 포트를 받지 않는다.
    @router.get(
        "/plugins",
        operation_id="list_plugins",
        summary="등록된 플러그인 전부를 종류를 가리지 않고 한 목록으로",
        responses=_documented_errors(401),
    )
    def list_plugins() -> list[PluginRow]:
        return [_plugin_row(row) for kind in PluginKind for row in plugins.list_manifests(kind)]

    # `{name}` 은 `plugins/{kind}/{name}/plugin.toml` 로 조립되므로 포트에 닿기 전에 sdk 의 패턴을
    # 지나야 한다(스토리 43). 변환기가 `verbatim` 인 이유는 `_Verbatim` 에 있다. 계약의 경로는
    # 변환기 없이 `/plugins/{kind}/{name}` 그대로다.
    @router.get(
        "/plugins/{kind}/{name:verbatim}",
        operation_id="read_plugin",
        summary="플러그인 하나의 매니페스트를 통째로",
        responses=_documented_errors(401, 404, 422),
    )
    def read_plugin(
        kind: PluginKind, name: Annotated[str, Path(pattern=PLUGIN_NAME_PATTERN)]
    ) -> PluginManifest:
        manifest = plugins.read_manifest(kind, PluginName(name))
        if manifest is None:
            raise HTTPException(status_code=404, detail=f"{kind} 종류에 {name} 플러그인이 없다")
        return manifest

    # 질의 셋을 포트에 그대로 넘긴다. 멈춘 실행 목록이 `?status=paused` 이고 별도 경로가 없는
    # 이유는 상태가 요약의 한 필드이지 다른 자원이 아니기 때문이다(ADR 0012). `limit` 의 기본값과
    # 상한은 core 의 숫자이고 없으면 포트가 기본값을 받는다. `after` 는 문자 집합과 길이를 FastAPI
    # 가, 해독을 `_decode_after()` 가 포트에 닿기 전에 본다.
    @router.get(
        "/traces",
        operation_id="list_traces",
        summary="지나간 실행의 요약을 최근 것부터 한 쪽씩",
        responses=_documented_errors(401, 422),
    )
    def list_traces(
        status: Annotated[
            RunStatus | None, Query(description="없으면 전부다. paused 가 곧 멈춘 실행 목록이다")
        ] = None,
        limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
        after: Annotated[
            str | None,
            Query(pattern=CURSOR_PATTERN, description="앞 쪽의 next_cursor 를 그대로 넘긴다"),
        ] = None,
    ) -> TracePage:
        rows = trace.list(status=status, limit=limit, after=_decode_after(after))
        return trace_page(rows, limit=limit)

    # `{run_id}` 는 `traces/{run_id}.jsonl` 로 조립되므로 `{name}` 과 같이 포트에 닿기 전에 sdk 의
    # 패턴을 지나야 한다. 목록이 내는 식별자에 거는 것과 같은 패턴이라 목록에서 얻은 것을 그대로
    # 넘길 수 있다. 부재는 404 이고 읽을 수 없는 파일은 포트의 PluginError 가 표를 지나 500 이 된다
    # (ADR 0012 의 2026-09-22 이력). 쓰는 중인 파일은 어댑터가 그 앞 줄까지 돌려주므로 200 이다.
    @router.get(
        "/traces/{run_id:verbatim}",
        operation_id="read_trace",
        summary="한 실행의 이벤트 전부를 쓴 순서 그대로",
        responses=_documented_errors(401, 404, 422),
    )
    def read_trace(run_id: Annotated[str, Path(pattern=RUN_ID_PATTERN)]) -> Trace:
        found = trace.read(RunId(run_id))
        if found is None:
            raise HTTPException(status_code=404, detail=f"{run_id} 실행의 트레이스가 없다")
        return trace_detail(found)

    return router


def _decode_after(text: str | None) -> Cursor | None:
    """질의의 커서를 정렬 키로(질의). 해독되지 않으면 FastAPI 의 검증 오류와 같은 모양으로 던진다.

    같은 모양으로 던지는 이유는 문자 집합에서 걸리든 해독에서 걸리든 클라이언트가 같은 422 와 같은
    `query.after` 를 받아야 하기 때문이다. 표(`failure_for()`)는 그대로 한 곳이다. `Query` 에
    검증기를 달아 `Cursor` 로 바꾸지 않는 이유는 그러면 `str` 로 선언한 파라미터에 다른 타입이
    들어와 선언이 거짓이 되기 때문이다 — 스키마가 문자열이어야 하므로 선언을 바꿀 수도 없다.
    """
    if text is None:
        return None
    try:
        return decode_cursor(text)
    except ValueError as error:
        detail = {"type": "value_error", "loc": ("query", "after"), "msg": str(error)}
        raise RequestValidationError([detail]) from error


def _documented_errors(*statuses: int) -> dict[int | str, dict[str, object]]:
    """라우트의 `responses` 에 적을 에러 응답들(질의). 모양은 언제나 봉투다."""
    return {
        status: {"model": ErrorEnvelope, "description": _DOCUMENTED_ERRORS[status]}
        for status in statuses
    }


def _plugin_row(row: ManifestRow) -> PluginRow:
    """포트의 행을 응답의 행으로(질의). 매니페스트는 그대로이고 표지만 HTTP 의 모양으로 옮긴다."""
    if isinstance(row, PluginManifest):
        return row
    return UnreadableManifest(kind=row.kind, name=row.name, reason=row.reason)


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


def _detail_of(error: Exception) -> str:
    """서버 기록에만 가는 문구. 밖으로 나가는 `message` 와 가른 이유는 예기치 않은 실패의 원인을
    운영자는 봐야 하고 클라이언트는 보면 안 되기 때문이다."""
    return f"{type(error).__name__}: {error}"


def _new_request_id() -> str:
    """실행 식별자가 아니다. `Clock` 포트를 쓰지 않는 이유가 그것이다 — 이것은 요청 하나의 상관
    키이고 트레이스에 남지 않는다."""
    return uuid4().hex
