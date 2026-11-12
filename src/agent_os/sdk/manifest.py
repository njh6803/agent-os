"""플러그인 매니페스트. plugin.toml 하나에 schema_version과 kind가 있다.

디스크에 남는 형식이라 바꾸면 ADR을 남긴다(헌법 "플러그인 모델", ADR 0008).
schema_version을 올리면 ADR 0008의 이력에 쌓는다.
"""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from enum import StrEnum
from typing import Annotated, Literal, Self, TypeGuard
from urllib.parse import urlsplit

from pydantic import (
    BaseModel,
    ConfigDict,
    Discriminator,
    Field,
    StringConstraints,
    Tag,
    field_validator,
    model_validator,
)

from agent_os.sdk.ids import PLUGIN_NAME_PATTERN, PluginName


# skill은 공통 넷만 가지고 종류별 칸이 없다. 에이전트가 매니페스트의 `skills` 로 이름을 골라 쓴다
# (ADR 0041). 이 타입은 관리 API 계약에도 박히므로 진행 상태는 독스트링이 아니라 여기 둔다.
# 독스트링이 곧 openapi.json 의 설명이다.
class PluginKind(StrEnum):
    """플러그인의 종류. 값은 넷이다."""

    AGENT = "agent"
    MCP = "mcp"
    SKILL = "skill"
    MODEL = "model"


# 닫힌 열거인 이유는 모르는 제공사를 읽는 단계에서 거부하고, 값을 하나 더하는 것이 가산 변경이
# 되게 하기 위해서다. 이름 있는 정의로 openapi.json 에 서야 생성 클라이언트가 재사용한다(ADR 0008).
class ModelProvider(StrEnum):
    """모델 플러그인의 제공사."""

    ANTHROPIC = "anthropic"
    OPENAI_COMPATIBLE = "openai-compatible"


_ENTRYPOINT = r"^[A-Za-z_][\w.]*:[A-Za-z_]\w*$"

# 매니페스트는 관리 API 의 응답 타입 그대로다(ADR 0010 의 2026-09-23 이력). 직렬화하면 필드가 언제나
# 전부 실리는데 pydantic 은 기본값 있는 필드를 JSON 스키마의 required 에서 빼므로, 그대로 두면
# openapi.json 에서 생성한 클라이언트가 requires_approval 같은 필드를 선택으로 받는다. 이 설정이
# 바꾸는 것은 직렬화 쪽 JSON 스키마뿐이고 디스크 형식도 검증도 그대로다.
_MANIFEST_CONFIG = ConfigDict(
    extra="forbid",
    frozen=True,
    json_schema_serialization_defaults_required=True,
)


# 헤더 이름은 RFC 9110 의 토큰 문자(특수 기호 열다섯, 글자, 숫자)만 받고, 환경 변수 이름은
# 글자·숫자· 밑줄만 받는다. 패턴을 타입의 제약으로 거는 이유는 `skills` 칸과 같다. 그래야
# openapi.json 의 `patternProperties` 에 같은 규칙이 실려 계약이 그것을 드러낸다(ADR 0049). 공백이나
# 콜론이 든 이름을 httpx2 는 요청을 만들 때 거부하지 않고 그대로 싣는다.
_HeaderName = Annotated[str, StringConstraints(pattern=r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")]
_EnvName = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_]+$")]

# 라이브러리나 HTTP 가 스스로 정하는 헤더 이름(소문자). 클라이언트의 기본 헤더는 요청마다의 헤더보다
# 먼저 합쳐져 mcp 가 요청마다 싣는 이름은 매니페스트의 값을 조용히 덮고, `Host` 는 요청을 다른
# 호스트 이름으로 보낸다. 받았다가 나중에 막으면 있던 매니페스트가 깨지므로 지금 막는다. 연결 계층의
# 이름(`upgrade`, `te`, `trailer`, `keep-alive`, `proxy-authorization`)도 같은 까닭으로 막는다. 앞의
# 넷은 연결마다 뜻이 있어 원격 서버에 기본 헤더로 실을 것이 아니고, `proxy-authorization` 은
# 프록시에게 줄 자격이 원격 서버로 새는 길이다. `cookie` 는 막지 않는다. 쿠키로 인증하는 서버가 있고
# httpx2 는 그 헤더를 쿠키 저장소와 합쳐 보낼 뿐 연결을 바꾸지 않는다(어림. 02 가 접속을 만들며
# 코드를 읽고 정했다).
_RESERVED_HEADERS = frozenset(
    {
        "host",
        "content-length",
        "transfer-encoding",
        "connection",
        "upgrade",
        "te",
        "trailer",
        "keep-alive",
        "proxy-authorization",
        "accept",
        "content-type",
        "mcp-session-id",
        "mcp-protocol-version",
        "last-event-id",
    }
)


def _check_http_address(value: str, field: str) -> str:
    """원격 MCP 서버의 `url` 과 모델 서버의 `base_url` 이 나눠 쓰는 주소 검사 넷.

    문구는 칸 이름만 다르고 적은 값을 되울리지 않는다. 매니페스트를 읽지 못한 문구가 운영자 면에
    나가기 때문이다(헌법 원칙 V). 파서의 오류 문구는 대괄호 안의 호스트를 되울리므로 예외를 이
    함수 밖으로 잇지 않고 고정 문구로 바꾼다.
    """
    try:
        parts = urlsplit(value)
    except ValueError:
        parts = None
    if parts is None:
        raise ValueError(f"{field} 이 주소 모양이 아니다")
    if parts.scheme not in ("http", "https"):
        raise ValueError(f"{field} 은 http 나 https 주소여야 한다")
    if "@" in parts.netloc:
        raise ValueError(f"{field} 에 사용자 정보를 적을 수 없다")
    if not parts.hostname:
        raise ValueError(f"{field} 에 호스트가 있어야 한다")
    return value


class StdioServer(BaseModel):
    """mcp 플러그인이 띄우는 stdio 서버의 실행 정보."""

    model_config = _MANIFEST_CONFIG

    # 기본값이 `"stdio"` 인 이유는 `transport` 가 없는 지금의 매니페스트가 그대로 읽히게 하기
    # 위해서다.
    transport: Literal["stdio"] = "stdio"
    command: str
    args: tuple[str, ...] = ()
    # 도구 이름 -> 트레이스에 마스킹해 쓸 인자 이름들(ADR 0009). 도구별인 이유는 금지 규칙을
    # 매니페스트만으로 판정하려면 도구 단위여야 하기 때문이다. 어느 도구가 어느 서버의
    # 것인지는 MCP 에 붙어야 알 수 있어서, 평면 목록으로는 정적 판정이 성립하지 않는다. 두 모양이
    # 같이 쓰므로 `HttpServer` 도 같은 칸을 선언한다.
    secret_args: Mapping[str, tuple[str, ...]] = {}


class HttpServer(BaseModel):
    """mcp 플러그인이 주소로 붙는 원격 서버의 정보."""

    model_config = _MANIFEST_CONFIG

    transport: Literal["http"]
    # 문자열 그대로 보관한다. `AnyHttpUrl` 은 빈 경로에 `/` 를 붙이고 호스트를 소문자로 바꿔, 관리
    # API 응답이 파일에 적은 글자와 달라진다. 쿼리 문자열과 조각은 막지 않는다(ADR 0049 Consequences
    # "문구에 실리는 것과 실리지 않는 것").
    url: str
    # 헤더 이름 -> 값을 읽을 환경 변수 이름. 값은 매니페스트에 없다(ADR 0009).
    headers: Mapping[_HeaderName, _EnvName] = {}
    secret_args: Mapping[str, tuple[str, ...]] = {}

    # 아래 두 검증자의 문구는 `url` 의 글자와 환경 변수 이름을 되울리지 않는다. 매니페스트를 읽지
    # 못한 문구가 운영자 면에 나가기 때문이다(헌법 원칙 V). 헤더 이름은 비밀이 아니라 문구에 싣는다.
    # 검증자는 필드 검증 뒤에 돌아 헤더 이름이 패턴을 지난 값이다. 주소 검사는 모델 서버의
    # `base_url` 과 나눠 쓴다(`_check_http_address`).
    @field_validator("url")
    @classmethod
    def _url_is_plain_http(cls, value: str) -> str:
        return _check_http_address(value, "url")

    @field_validator("headers")
    @classmethod
    def _header_names_are_distinct_and_not_reserved(
        cls, value: Mapping[str, str]
    ) -> Mapping[str, str]:
        seen: set[str] = set()
        for name in value:
            lowered = name.lower()
            if lowered in _RESERVED_HEADERS:
                raise ValueError(f"헤더 이름을 적을 수 없다: {name}")
            # HTTP 헤더 이름은 대소문자를 가리지 않아 한 헤더에 값 둘이 실린다. TOML 은 막지 않는다.
            if lowered in seen:
                raise ValueError(f"대소문자만 다른 헤더 이름이 둘이다: {name}")
            seen.add(lowered)
        return value


def _is_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    """isinstance 로 좁히면 pyright 가 키와 값을 Unknown 으로 둔다. 여기서 명시한다."""
    return isinstance(value, Mapping)


def _transport_of(value: object) -> str | None:
    """`transport` 가 없으면 `"stdio"` 로 읽는다. 보통 판별자(`Field(discriminator=)`)는 칸이 없는
    입력을 `union_tag_not_found` 로 거부해 지금의 매니페스트가 모두 깨진다. 문자열이 아닌 값은
    태그가 없는 것으로 넘겨 pydantic 이 거부하게 한다."""
    if _is_mapping(value):
        tag = value.get("transport", "stdio")
        return tag if isinstance(tag, str) else None
    tag = getattr(value, "transport", "stdio")
    return tag if isinstance(tag, str) else None


# 호출할 수 없는 별칭이다. 모델을 만드는 곳은 `StdioServer(...)`·`HttpServer(...)` 이고, 읽는 쪽은
# 모양을 좁혀(`isinstance`) 칸을 읽는다. 호출 가능 판별자라 openapi.json 의 `oneOf` 에
# `discriminator.mapping` 은 없다.
McpServer = Annotated[
    Annotated[StdioServer, Tag("stdio")] | Annotated[HttpServer, Tag("http")],
    Discriminator(_transport_of),
]


class PluginManifest(BaseModel):
    """플러그인 하나의 매니페스트. plugin.toml 하나를 옮긴 것이다."""

    model_config = _MANIFEST_CONFIG

    schema_version: Literal["1"]
    kind: PluginKind
    name: PluginName = Field(pattern=PLUGIN_NAME_PATTERN)
    version: str
    entrypoint: str | None = Field(default=None, pattern=_ENTRYPOINT)
    # 에이전트만. 쓸 mcp 플러그인 이름. 비어 있으면 도구가 없다(ADR 0002)
    mcp: tuple[PluginName, ...] = ()
    # 에이전트만. 승인 없이는 부를 수 없는 도구 이름. 비어 있으면 지금까지와 같다(ADR 0009).
    # 같은 일을 할 수 있는 도구는 전부 여기 들어가야 한다. 모델이 다른 도구로 우회하는 것은
    # 거부가 아니라 이 목록이 막는다.
    requires_approval: tuple[str, ...] = ()
    # 에이전트만. 대화에서 이 에이전트가 받는 원문 교환(가장 가까운 자기 대화 요약 뒤의 요청과
    # 출력)의 글자 수 한도. 이어 가기에서 넘으면 런타임이 에이전트를 부르기 전에 앞 요약과 오래된
    # 교환을 새 요약에 접는다(계기, 범위, 실패는 core/continuation.py. ADR 0022, ADR 0008 의
    # 2026-10-03 이력). 없음이 기본이고 숫자 기본값을 두지 않는다 — 두면 그 숫자가 직렬화 스키마와
    # 관리 API 의 매니페스트 응답에 박혀 기본값을 바꾸는 것이 계약 변경이 된다. 없음을 기본 한도
    # (core 의 DEFAULT_CONVERSATION_LIMIT)로 읽는 것은 core 의 몫이다(루프 상한과 같은 자리).
    # strict 인 이유는 lax 검증이 TOML 의 true 를 1 로, "300" 을 300 으로, 2.0 을 2 로 받기
    # 때문이다. 0 을 받으면 모든 이어 가기가 요약되고 원문이 남지 않는다.
    conversation_limit: int | None = Field(default=None, strict=True, ge=1)
    # 에이전트만. `ctx.llm()` 한 번의 루프가 도는 턴의 끝과 실행 하나가 도구를 부르는 횟수의 끝(ADR
    # 0052). 둘 다 `conversation_limit` 과 같은 모양이다 — 없음이 기본이고 숫자 기본값을 두지
    # 않으며(두면 그 숫자가 직렬화 스키마와 관리 API 의 응답에 박힌다), strict 인 이유도 같다(`true`
    # 를 1 로, `"3"` 을 3 으로, `2.0` 을 2 로 받는다). 없음을 턴의 10과 도구 호출의 끝 없음으로 읽는
    # 것은 core 의 몫이다. 턴의 끝이 10을 넘는지도 sdk 가 보지 않는다 — 10이 sdk 와 core 두 곳에
    # 적히고 `openapi.json` 에 최댓값으로 실려 상한을 올리는 결정이 계약 변경이 되기 때문이다. 두 칸
    # 사이의 관계도 검사하지 않는다.
    max_turns: int | None = Field(default=None, strict=True, ge=1)
    max_tool_calls: int | None = Field(default=None, strict=True, ge=1)
    # 에이전트만. 쓸 모델 플러그인의 이름. 없음이 기본이고 없음은 기본 모델을 쓰겠다는 뜻이다
    # (ADR 0040). 패턴은 여기서 걸어 읽는 단계가 거부한다. 그 이름의 모델 플러그인이 실재하는지는
    # 매니페스트만으로 알 수 없어 sdk가 보지 않는다.
    model: PluginName | None = Field(default=None, pattern=PLUGIN_NAME_PATTERN)
    # 에이전트만. 쓸 스킬 플러그인의 이름들이고 적은 순서를 지킨다. 비어 있는 것이 기본이다(ADR
    # 0041). 원소마다 패턴을 거는 이유는 `PluginName` 이 패턴을 들지 않는 NewType 이라 `mcp` 칸처럼
    # 선언하면 `../../evil` 을 받기 때문이다. 이름은 파일 경로로 조립되고 openapi.json 의 `items` 에
    # 패턴이 실려야 계약이 같은 규칙을 드러낸다. 가리키는 스킬 플러그인이 실재하는지는
    # 매니페스트만으로 알 수 없어 sdk가 보지 않는다.
    skills: tuple[Annotated[PluginName, Field(pattern=PLUGIN_NAME_PATTERN)], ...] = ()
    # 모델만. 제공사와 모델 id 는 필수이고 아래 둘은 선택이다. 선택 둘에 숫자 기본값을 두지 않는
    # 이유는 `conversation_limit` 과 같다 — 두면 그 숫자가 직렬화 스키마와 관리 API 의 응답에
    # 박힌다. 없을 때의 값은 sdk가 정하지 않는다. 필수 둘이 기본값 없음(None)인 것은 직렬화 스키마를
    # 다른 종류와 같은 모양으로 두기 위해서이고, 종류가 모델이면 아래 검증자가 둘이 있음을 보장한다.
    provider: ModelProvider | None = None
    model_id: str | None = Field(default=None, min_length=1)
    # strict 인 이유는 `conversation_limit` 과 같다(`true` 를 1 로, `"16"` 을 16 으로 받는다)
    max_tokens: int | None = Field(default=None, strict=True, ge=1)
    # strict 여도 TOML 의 정수 `0`·`1` 은 실수 `0.0`·`1.0` 으로 받아들여진다. 불린과 문자열은
    # 거부된다.
    temperature: float | None = Field(default=None, strict=True, ge=0, le=1)
    # 모델만, 제공사가 openai-compatible 일 때만(ADR 0057). 모델 서버의 주소와 키를 읽을 환경 변수의
    # 이름이다. 둘 다 선택이고 기본은 없음이라 `schema_version` 은 "1" 그대로다. 설명은 계약
    # (`openapi.json`)에 실리므로 한 줄로 쓰고 논증은 여기 둔다. `base_url` 은 글자 그대로 보관한다
    # (`AnyHttpUrl` 은 호스트를 소문자로 바꾸고 빈 경로에 `/` 를 붙여 관리 API 응답이 파일에 적은
    # 글자와 달라진다). `api_key_env` 는 값이 아니라 이름이라 관리 API 응답에 실려도 비밀이 새지
    # 않는다(원칙 V). 이 값의 모델은 읽히고 관리 API 에 보이지만 모델 서버에 붙는 동작은 아직
    # 없다. 그 모델로 실행을 치면 실행 전 구성 오류로 끝난다(`adapters/models.py`).
    base_url: str | None = Field(
        default=None,
        description=(
            "모델 서버의 API 뿌리까지 적은 주소. vLLM이면 /v1 까지 적고 그 뒤에 "
            "chat/completions 가 붙으며 끝의 / 는 있어도 없어도 같다."
        ),
    )
    api_key_env: _EnvName | None = Field(
        default=None,
        description="키 값이 아니라 런타임이 호출 때 읽을 환경 변수의 이름.",
    )
    # mcp만
    server: McpServer | None = None

    @field_validator("base_url")
    @classmethod
    def _base_url_is_plain_http_without_query(cls, value: str | None) -> str | None:
        if value is None:
            return None
        _check_http_address(value, "base_url")
        # 쿼리가 든 주소는 라이브러리가 쿼리 뒤에 경로를 붙여 요청 줄이 깨지고, 그 주소는 401의 원인
        # 예외 글과 로거의 INFO 줄에 쿼리째 실린다(ADR 0057 의 2026-11-12 이력). 조각은 네트워크로
        # 나가지 않아 받는다. 조각을 떼고 `?` 를 보는 것은 빈 쿼리(`…/v1?`)도 막기 위해서다.
        if "?" in value.partition("#")[0]:
            raise ValueError("base_url 에 쿼리 문자열을 적을 수 없다")
        return value

    @model_validator(mode="after")
    def _fields_belong_to_their_kind(self) -> Self:
        if self.kind is PluginKind.AGENT:
            if self.entrypoint is None:
                raise ValueError("agent 플러그인은 entrypoint가 필요하다 (모듈:속성)")
        elif self.entrypoint is not None:
            raise ValueError(f"{self.kind} 플러그인은 entrypoint를 갖지 않는다")
        if self.kind is not PluginKind.AGENT and "mcp" in self.model_fields_set:
            raise ValueError(f"{self.kind} 플러그인은 mcp 목록을 갖지 않는다")
        if self.kind is not PluginKind.AGENT and "requires_approval" in self.model_fields_set:
            raise ValueError(f"{self.kind} 플러그인은 requires_approval 목록을 갖지 않는다")
        if self.kind is not PluginKind.AGENT and "conversation_limit" in self.model_fields_set:
            raise ValueError(f"{self.kind} 플러그인은 conversation_limit 을 갖지 않는다")
        if self.kind is not PluginKind.AGENT and "max_turns" in self.model_fields_set:
            raise ValueError(f"{self.kind} 플러그인은 max_turns 를 갖지 않는다")
        if self.kind is not PluginKind.AGENT and "max_tool_calls" in self.model_fields_set:
            raise ValueError(f"{self.kind} 플러그인은 max_tool_calls 를 갖지 않는다")
        if self.kind is not PluginKind.AGENT and "skills" in self.model_fields_set:
            raise ValueError(f"{self.kind} 플러그인은 skills 를 갖지 않는다")
        # 이 검증자는 필드 검증 뒤에 돌아 이름이 패턴을 지난 값이다. 어긴 값이 문구에 실리지 않는다.
        # 조용히 합치지 않는 이유는 오타가 숨고 열이 적은 순서와 달라지기 때문이다.
        seen: set[str] = set()
        for name in self.skills:
            if name in seen:
                raise ValueError(f"agent 플러그인의 skills 에 같은 이름이 두 번 있다: {name}")
            seen.add(name)
        if self.kind is PluginKind.MODEL:
            if self.provider is None:
                raise ValueError("model 플러그인은 provider가 필요하다")
            if self.model_id is None:
                raise ValueError("model 플러그인은 model_id가 필요하다")
            # 제공사에 맞지 않는 칸은 "적었는가"로 판정한다. 문구가 싣는 것은 칸 이름과 닫힌 열거를
            # 지난 제공사 값뿐이다.
            subject = f"provider 가 {self.provider} 인 model 플러그인은"
            match self.provider:
                case ModelProvider.OPENAI_COMPATIBLE:
                    if self.base_url is None:
                        raise ValueError(f"{subject} base_url 이 필요하다")
                case ModelProvider.ANTHROPIC:
                    for field in ("base_url", "api_key_env"):
                        if field in self.model_fields_set:
                            raise ValueError(f"{subject} {field} 을 갖지 않는다")
        else:
            for field in (
                "provider",
                "model_id",
                "max_tokens",
                "temperature",
                "base_url",
                "api_key_env",
            ):
                if field in self.model_fields_set:
                    raise ValueError(f"{self.kind} 플러그인은 {field} 을 갖지 않는다")
        if self.kind is not PluginKind.AGENT and "model" in self.model_fields_set:
            raise ValueError(f"{self.kind} 플러그인은 model 을 갖지 않는다")
        if self.kind is PluginKind.MCP:
            if self.server is None:
                raise ValueError(
                    "mcp 플러그인은 [server] 표가 필요하다 "
                    '(command, args 또는 transport = "http", url)'
                )
        elif self.server is not None:
            raise ValueError(f"{self.kind} 플러그인은 [server] 표를 갖지 않는다")
        return self


def parse_manifest(text: str) -> PluginManifest:
    return PluginManifest.model_validate(tomllib.loads(text))


def secret_args_by_tool(servers: Mapping[PluginName, McpServer]) -> Mapping[str, tuple[str, ...]]:
    """도구 이름 -> 마스킹할 인자 이름들. 서버를 가로질러 평평하다.

    빈 선언은 마스킹이 아니므로 뺀다. 가릴 인자가 없는 도구는 금지 규칙에도 걸리지 않고
    마스킹 조회에서도 원문을 돌려주므로, 두 쓰임이 같은 규칙을 본다.
    """
    return {
        tool: names
        for server in servers.values()
        for tool, names in server.secret_args.items()
        if names
    }


def approval_conflicts(
    agent: PluginManifest, servers: Mapping[PluginName, McpServer]
) -> tuple[str, ...]:
    """마스킹과 승인이 함께 걸린 도구 이름들. 비어 있으면 정책이 성립한다(ADR 0009).

    마스킹된 인자는 복원할 수 없어, 승인받아 실제로 실행되는 그 호출이 마스킹된 값을 보내게
    된다. 둘 다 매니페스트에 적히므로 실행 식별자가 생기기 전에 정적으로 판정된다. 거부는
    이 질의를 부르는 쪽이 한다. sdk 는 core 의 구성 오류 타입을 모르기 때문이다.
    """
    masked = secret_args_by_tool(servers)
    return tuple(tool for tool in agent.requires_approval if tool in masked)
