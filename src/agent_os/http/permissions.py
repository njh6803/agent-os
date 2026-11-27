"""권한 표와 그 검사. 운영자 오퍼레이션마다 필요한 권한을 `operationId` 로 적고, 요청한 계정의
단계가 그 권한을 가지는지 본다(ADR 0062 결정 "두 단계와 권한 표", 명세 admin-login "권한 표").

**권한은 다섯이고 단계가 가진 것을 정한다.** 시스템 관리자는 다섯 모두를, 관리자는 계정을 다루는
권한(`manage_accounts`)만 뺀 넷을 가진다. 공유 토큰으로 온 요청(공유 토큰을 걷기 전까지 함께 받는
기간)은 계정이 없지만 같은 넷을 가진 것으로 본다. 계정을 다루는 일은 계정으로만 하게 하려는 것이다.

**표의 값은 셋 가운데 하나다.** 로그인 없이 연다(`Open`), 로그인만 요구한다(`LoginOnly`), 권한
하나를 요구한다(`Permission`). 앞의 둘은 권한을 보지 않는다. 로그인 여부는 인증 미들웨어가 라우팅
전에 이미 가렸다(`PUBLIC_PATHS`, `LOGIN_ONLY_PATHS`). 표가 그것을 다시 적는 까닭은 계약의 모든
운영자 오퍼레이션이 표에 한 줄씩 있다는 전수 검사 하나가 "권한을 정하지 않은 경로"를 잡게 하려는
것이다.

**검사는 운영자 경로의 라우터들에 건 의존성 하나다.** 미들웨어는 경로를 찾기 전에 돌아 `operationId`
를 모른다. 의존성은 경로를 찾은 뒤에 돌아 그 요청의 라우트에서 `operationId` 를 읽는다. FastAPI 는
라우터에 건 의존성을 경로 파라미터와 질의와 본문의 형식 검사보다 먼저 푼다. 그래서 권한이 모자란
계정은 JSON 으로 읽히는 본문이 틀렸어도 422 가 아니라 403 을 받는다. 다만 본문이 JSON 으로 읽히지
않으면 FastAPI 가 의존성을 풀기 전에 422(`json_invalid`)를 낸다. 이 순서의 예외는 받아들인 것이다
(명세 "요청을 판정하는 차례"의 5와 6).

**표에 없는 오퍼레이션은 열린 것으로 읽지 않는다.** 그 경로에 닿으면 500 이다. 조립의 결함이고,
새 경로가 권한 없이 열리는 쪽보다 닫히는 쪽이 낫다. 전수 검사가 먼저 잡는다.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum

from fastapi import Depends, HTTPException, Request
from fastapi.params import Depends as DependsMarker
from fastapi.routing import APIRoute

from agent_os.http.accounts import Tier
from agent_os.http.auth import operator_of

# 로그인한 계정의 단계가 요구한 권한을 갖지 못했을 때의 403 문구. 고정이고 어느 권한이 모자랐는지
# 싣지 않는다(명세 "로그인하지 않은 요청의 응답"). 요청 출처를 받지 않는 403 의 문구와 다르다.
FORBIDDEN_FOR_ACCOUNT_MESSAGE = "이 계정으로는 할 수 없다"


class Permission(StrEnum):
    """운영자가 할 수 있는 일의 다섯 갈래. 값은 계약과 코드가 같이 쓰는 이름이다."""

    VIEW = "view"
    TOGGLE_PLUGINS = "toggle_plugins"
    START_RUNS = "start_runs"
    DECIDE = "decide"
    MANAGE_ACCOUNTS = "manage_accounts"


@dataclass(frozen=True)
class Open:
    """로그인 없이 여는 오퍼레이션. 권한을 보지 않는다."""


@dataclass(frozen=True)
class LoginOnly:
    """로그인만 요구하는 오퍼레이션. 단계에 따른 권한은 보지 않는다."""


type Requirement = Open | LoginOnly | Permission

# 단계마다 가진 권한. 역할 기능(admin-roles)이 오면 계정에 붙은 역할에서 읽게 바꾸고 표와 검사하는
# 자리는 그대로 쓴다.
TIER_PERMISSIONS: Mapping[Tier, frozenset[Permission]] = {
    "system_admin": frozenset(Permission),
    "admin": frozenset(Permission) - {Permission.MANAGE_ACCOUNTS},
}

# 공유 토큰으로 온 요청이 가진 권한. 지금 공유 토큰이 여는 일이 모두 이 넷 안에 든다.
SHARED_TOKEN_PERMISSIONS: frozenset[Permission] = frozenset(Permission) - {
    Permission.MANAGE_ACCOUNTS
}

# 계약의 운영자 오퍼레이션(최종 사용자 경로와 `/health` 를 뺀 것)이 `operationId` 마다 한 줄씩이다.
# 오퍼레이션을 더하는 티켓이 그 줄을 더한다. 전수 검사(`tests/test_permissions.py`)가 계약과 이 표가
# 같은 집합인지 본다.
PERMISSION_TABLE: Mapping[str, Requirement] = {
    "log_in": Open(),
    "refresh_login": Open(),
    "get_setup": Open(),
    "set_password_by_link": Open(),
    "log_out": LoginOnly(),
    "get_me": LoginOnly(),
    "change_my_password": LoginOnly(),
    "list_accounts": Permission.MANAGE_ACCOUNTS,
    "create_account": Permission.MANAGE_ACCOUNTS,
    "create_password_link": Permission.MANAGE_ACCOUNTS,
    "set_account_active": Permission.MANAGE_ACCOUNTS,
    "unlock_account": Permission.MANAGE_ACCOUNTS,
    "list_plugins": Permission.VIEW,
    "read_plugin": Permission.VIEW,
    "list_traces": Permission.VIEW,
    "read_trace": Permission.VIEW,
    "list_conversations": Permission.VIEW,
    "check_connection": Permission.VIEW,
    "check_connection_by_launching": Permission.TOGGLE_PLUGINS,
    "set_plugin_enabled": Permission.TOGGLE_PLUGINS,
    "start_run": Permission.START_RUNS,
    "continue_run": Permission.START_RUNS,
    "decide_approval": Permission.DECIDE,
}


def permission_check(table: Mapping[str, Requirement]) -> Callable[[Request], None]:
    """표대로 요청을 가르는 의존성(질의 아님: 모자라면 403 을 던진다).

    표를 인자로 받는 까닭은 시험이 `manage_accounts` 를 요구하는 줄을 넣은 표로 이 동작을 따로
    재기 위해서다. 조립은 `PERMISSION_TABLE` 로 만든 `require_permission` 하나를 쓴다.
    """

    def check(request: Request) -> None:
        route = request.scope.get("route")
        operation_id = route.operation_id if isinstance(route, APIRoute) else None
        requirement = None if operation_id is None else table.get(operation_id)
        if requirement is None:
            # 표에 없는 오퍼레이션을 열린 것으로 읽지 않는다. 조립의 결함이라 500 이다
            raise LookupError(f"권한 표에 없는 오퍼레이션이다: {operation_id}")
        match requirement:
            case Open() | LoginOnly():
                return
            case Permission() as needed:
                if needed not in _granted(request):
                    raise HTTPException(status_code=403, detail=FORBIDDEN_FOR_ACCOUNT_MESSAGE)

    return check


def _granted(request: Request) -> frozenset[Permission]:
    """요청을 보낸 쪽이 가진 권한(질의). 쿠키로 로그인했으면 그 계정의 단계가, 아니면 공유 토큰이다.

    인증 미들웨어가 짧은 JWT 를 검증했을 때만 로그인이 요청에 심긴다. 계정이 없는 요청이 이 자리에
    닿으면 공유 토큰이 맞아서 지난 것이다(맞지 않았으면 401 이 먼저 나갔다).
    """
    claims = operator_of(request)
    return SHARED_TOKEN_PERMISSIONS if claims is None else TIER_PERMISSIONS[claims.tier]


# 운영자 경로의 라우터가 `dependencies=[REQUIRE_PERMISSION]` 로 건다. 라우트마다 걸지 않는다 — 걸지
# 않은 라우트가 곧 권한 없이 열린 경로가 된다.
REQUIRE_PERMISSION: DependsMarker = Depends(permission_check(PERMISSION_TABLE))
