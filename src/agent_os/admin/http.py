"""관리 API 의 라우터와 관리에만 있는 응답 모델. 에러 봉투와 상태 코드 표는 `agent_os.http` 에 있다.

라우트를 더하는 자리는 `admin_router()` 다. 데이터 라우트가 부재를 말하는 방법은
`HTTPException(404)` 이고 그것도 `agent_os.http.errors` 의 표를 지난다. 관리 라우트는 409 를 내지
않는다 — 관리는 실행을 일으키지 않아 재개할 수 없는 상태를 만날 일이 없고, 켜고 끄는 라우트는
꺼진 것을 거부하지 않는다.

**쓰기 라우트는 `async def` 이고 포트의 쓰기를 이벤트 루프에서 직접 부른다.** 조회 라우트는 동기
`def` 라 FastAPI 가 워커 스레드에서 돌린다. 쓰기까지 그렇게 두면 읽고 고치고 쓰기 둘이 스레드에서
겹쳐 갱신 하나가 사라진다. "한 프로세스 안의 쓰기 둘은 이벤트 루프가 줄세운다"(ADR 0017)는 쓰기가
루프 위에 있을 때만 참이다. 대가는 그 요청이 디스크에 닿는 동안 루프가 멈추는 것이고, 운영자 파일은
작다.

응답 모델의 독스트링은 한 줄이고 논증은 `#` 주석에 둔다. 라우트는 `operation_id` 를 손으로 준다.
이유는 `agent_os.http.errors` 와 `agent_os.http.routes` 에 있다.
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Path, Query, Response
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field, StrictBool

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
    PluginKey,
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


# 플러그인 목록의 행 둘. 겉은 종류·이름·켜짐이고 안에 매니페스트나 이유 하나가 붙는다(ADR 0010 의
# 2026-09-26 이력). 켜짐이 매니페스트 안이 아니라 겉에 있는 이유는 그것이 개발자가 적은 것이 아니라
# 운영자가 고른 것이기 때문이다(ADR 0017). 매니페스트는 sdk 의 것 그대로라 필드 목록이 두 곳이
# 되지 않는다. 판별자가 없고 required 필드(`manifest` 와 `reason`)로 갈리며 기본값이 없어 계약에서
# 전부 required 다. 읽히는 행의 이름이 sdk 의 패턴을 스키마에 싣는 것은 목록에서 얻은 이름을 켜고
# 끄는 경로에 그대로 넘기게 하려는 것이다. 표지 행의 이름이 `str` 인 이유는 core 의 표지와 같다 —
# 디렉터리 이름이 패턴을 어긴 것이 표지가 서는 경우 하나다. 그 표지는 용어집의 "읽을 수 없는
# 매니페스트"이고 이 행은 그 표지에 켜짐을 더한 플러그인 목록의 표지(placeholder)라 이름이 다르다.
class Plugin(BaseModel):
    """등록된 플러그인 하나. 종류와 이름과 켜짐, 그리고 매니페스트 통째로다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: PluginKind
    name: PluginName = Field(pattern=PLUGIN_NAME_PATTERN)
    enabled: bool
    manifest: PluginManifest


class PluginPlaceholder(BaseModel):
    """매니페스트로 읽히지 않는 플러그인의 자리에 서는 표지. 종류와 이름과 켜짐과 이유를 든다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: PluginKind
    name: str
    enabled: bool
    reason: str


# 별칭에 이름을 주는 이유는 생성 클라이언트가 익명 유니온 대신 이 이름을 받게 하기 위해서다.
type PluginRow = Plugin | PluginPlaceholder


# 계약에 박히는 요청 본문이다. 채널의 본문과 같은 규칙으로 기본값 있는 필드를 두지 않고 추가 필드는
# 422 다 — 보낸 쪽이 자기 값이 쓰였다고 믿게 두지 않는다. 불린 하나가 아니라 객체인 이유는 필드를
# 더하는 날 가산 변경으로 남기 위해서다(ADR 0010 의 2026-09-26 이력). `StrictBool` 인 이유는
# pydantic 의 `bool` 이 본문에서 `"false"`, `0`, `"no"` 를 거짓으로 받기 때문이다. 계약은 `boolean`
# 이라고 적는데 문자열이 켜짐을 정하게 된다. 계약의 스키마는 그대로 `boolean` 이다.
class SetEnabled(BaseModel):
    """켜짐 하나를 쓰는 요청. 거짓이면 끄고 참이면 켠다. 이미 그 상태여도 성공이다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: StrictBool


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

    # 두 조회 라우트는 매니페스트를 통째로 내보내므로 mcp 매니페스트의 command 와 args 도 나간다.
    # 가리지 않는 것이 결정이고 경계는 인증이다(ADR 0009 의 2026-09-22 이력, 네 번째 열린 문제).
    # MCP 서버에는 붙지 않는다 — 이 라우터는 도구 포트를 받지 않는다. 꺼진 집합은 요청 하나에 한 번
    # 읽고, 운영자 파일이 깨지면 목록 전체가 500 이다. 행마다 "알 수 없음"을 실으면 행의 타입이
    # 약해진다(ADR 0017).
    @router.get(
        "/plugins",
        operation_id="list_plugins",
        summary="등록된 플러그인 전부를 종류를 가리지 않고 켜짐과 함께 한 목록으로",
        responses=documented_errors(401),
    )
    def list_plugins() -> list[PluginRow]:
        disabled = plugins.read_disabled()
        return [
            _plugin_row(row, disabled)
            for kind in PluginKind
            for row in plugins.list_manifests(kind)
        ]

    # `{name}` 은 `plugins/{kind}/{name}/plugin.toml` 로 조립되므로 포트에 닿기 전에 sdk 의 패턴을
    # 지나야 한다(스토리 43). 변환기가 `verbatim` 인 이유는 `agent_os.http.routes` 에 있다. 계약의
    # 경로는 변환기 없이 `/plugins/{kind}/{name}` 그대로다. 판정 순서는 부재(404) → 깨진 매니페스트
    # (500) → 운영자 파일의 손상(500)이다. 운영자 파일이 깨졌어도 없는 이름은 404 다(ADR 0017 의
    # 2026-09-27 둘째 이력).
    @router.get(
        "/plugins/{kind}/{name:verbatim}",
        operation_id="read_plugin",
        summary="플러그인 하나를 켜짐과 매니페스트 통째로를 든 행으로",
        responses=documented_errors(401, 404, 422),
    )
    def read_plugin(
        kind: PluginKind, name: Annotated[str, Path(pattern=PLUGIN_NAME_PATTERN)]
    ) -> Plugin:
        manifest = plugins.read_manifest(kind, PluginName(name))
        if manifest is None:
            raise _absent(kind, name)
        disabled = plugins.read_disabled()
        return Plugin(
            kind=kind,
            name=PluginName(name),
            enabled=not _is_disabled(disabled, kind, name),
            manifest=manifest,
        )

    # 관리의 첫 쓰기 경로(ADR 0010 의 2026-09-26 이력). 멱등한 PUT 하나이고 답은 본문 없는 204 다 —
    # 갱신된 행을 돌려주면 깨진 매니페스트를 끈 직후의 응답이 표지가 되어 단건 조회(500)와 모양이
    # 갈린다. 부재 판정은 포트가 하고 값으로 돌려주므로 운영자 파일이 깨졌어도 없는 이름은 404 다.
    # 손상과 쓰기 실패는 포트의 PluginError 가 표를 지나 500 이다. `{name:verbatim}` 이 슬래시까지
    # 잡으므로 GET `.../calc/enabled` 는 단건 조회에 이름 `calc/enabled` 로 맞은 뒤 패턴이 422 로
    # 거르고, 이 경로의 이름은 리터럴 `/enabled` 앞까지다. `async def` 인 이유는 모듈 독스트링.
    @router.put(
        "/plugins/{kind}/{name:verbatim}/enabled",
        operation_id="set_plugin_enabled",
        summary="플러그인 하나를 켜거나 끈다",
        status_code=204,
        response_class=Response,
        responses=documented_errors(401, 404, 422),
    )
    async def set_plugin_enabled(
        kind: PluginKind,
        name: Annotated[str, Path(pattern=PLUGIN_NAME_PATTERN)],
        body: SetEnabled,
    ) -> Response:
        written = plugins.write_enabled(kind, PluginName(name), body.enabled)
        if written == "absent":
            raise _absent(kind, name)
        return Response(status_code=204)

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


def _absent(kind: PluginKind, name: str) -> HTTPException:
    """플러그인 부재의 404(질의). 단건 조회와 켜고 끄기가 같은 말을 한다."""
    return HTTPException(status_code=404, detail=f"{kind} 종류에 {name} 플러그인이 없다")


def _plugin_row(row: ManifestRow, disabled: frozenset[PluginKey]) -> PluginRow:
    """포트의 행을 응답의 행으로(질의). 매니페스트는 그대로 담고 켜짐은 꺼진 집합에서 온다."""
    enabled = not _is_disabled(disabled, row.kind, row.name)
    if isinstance(row, PluginManifest):
        return Plugin(kind=row.kind, name=row.name, enabled=enabled, manifest=row)
    return PluginPlaceholder(kind=row.kind, name=row.name, enabled=enabled, reason=row.reason)


def _is_disabled(disabled: frozenset[PluginKey], kind: PluginKind, name: str) -> bool:
    """(종류, 이름)이 꺼진 집합에 드는가(질의). 이름을 `PluginName` 으로 감싸 견주지 않는다.

    표지의 이름은 패턴을 어긴 디렉터리 이름일 수 있고, 유효한 이름이 아닌 값을 유효한 이름의 타입에
    담으면 그 타입이 뜻하는 것이 거짓이 된다(`.claude/rules/core.md`). 그런 이름은 운영자 파일에 들
    수 없으므로 어차피 언제나 켜짐이다.
    """
    return any(key.kind is kind and key.name == name for key in disabled)
