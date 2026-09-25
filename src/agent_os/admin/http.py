"""관리 API 의 라우터와 관리에만 있는 응답 모델. 에러 봉투와 상태 코드 표는 `agent_os.http` 에 있다.

라우트를 더하는 자리는 `admin_router()` 다. 데이터 라우트가 부재를 말하는 방법은
`HTTPException(404)` 이고 그것도 `agent_os.http.errors` 의 표를 지난다. 관리 라우트는 409 를 내지
않는다 — 관리는 실행을 일으키지 않아 재개할 수 없는 상태를 만날 일이 없다.

응답 모델의 독스트링은 한 줄이고 논증은 `#` 주석에 둔다. 라우트는 `operation_id` 를 손으로 준다.
이유는 `agent_os.http.errors` 와 `agent_os.http.routes` 에 있다.
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict

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
    PluginSource,
    RunStatus,
    TraceStore,
)
from agent_os.http.routes import documented_errors
from agent_os.sdk import (
    PLUGIN_NAME_PATTERN,
    RUN_ID_PATTERN,
    PluginKind,
    PluginManifest,
    PluginName,
    RunId,
)


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


def admin_router(*, health: Health, plugins: PluginSource, trace: TraceStore) -> APIRouter:
    """관리 라우터. 데이터 라우트는 이 자리에 더한다.

    `/health` 가 주입받은 값을 그대로 돌려주는 것이 이 라우트의 전부다. 라우트가 상태를 직접
    읽으면 인증 없이 나가는 유일한 응답이 내부 구성을 알려 주는 창이 된다(ADR 0011).
    """
    router = APIRouter(responses=documented_errors(500))

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
        responses=documented_errors(401),
    )
    def list_plugins() -> list[PluginRow]:
        return [_plugin_row(row) for kind in PluginKind for row in plugins.list_manifests(kind)]

    # `{name}` 은 `plugins/{kind}/{name}/plugin.toml` 로 조립되므로 포트에 닿기 전에 sdk 의 패턴을
    # 지나야 한다(스토리 43). 변환기가 `verbatim` 인 이유는 `agent_os.http.routes` 에 있다. 계약의
    # 경로는 변환기 없이 `/plugins/{kind}/{name}` 그대로다.
    @router.get(
        "/plugins/{kind}/{name:verbatim}",
        operation_id="read_plugin",
        summary="플러그인 하나의 매니페스트를 통째로",
        responses=documented_errors(401, 404, 422),
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
        responses=documented_errors(401, 422),
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
        responses=documented_errors(401, 404, 422),
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


def _plugin_row(row: ManifestRow) -> PluginRow:
    """포트의 행을 응답의 행으로(질의). 매니페스트는 그대로이고 표지만 HTTP 의 모양으로 옮긴다."""
    if isinstance(row, PluginManifest):
        return row
    return UnreadableManifest(kind=row.kind, name=row.name, reason=row.reason)
