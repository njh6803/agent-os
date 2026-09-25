"""core가 프로세스 밖과 닿는 포트. 닫힌 목록 다섯이고 늘리려면 ADR이 필요하다.

표는 `.claude/rules/core.md`. 어댑터는 이것을 상속하지 않고 시그니처로 만족한다.
ChatModel만 예외로 langchain-core의 추상 클래스 자체가 포트다. 루프가 그 위에서 돌기 때문이다.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal, Protocol

from langchain_core.language_models import BaseChatModel

from agent_os.sdk import (
    AgentName,
    BaseAgent,
    Event,
    Json,
    McpServer,
    PluginKind,
    PluginManifest,
    PluginName,
    Principal,
    RunFailed,
    RunFinished,
    RunId,
    RunPaused,
)

# 모델 호출. 첫 어댑터는 langchain-anthropic의 ChatAnthropic이고 main.py가 만든다.
type ChatModel = BaseChatModel


class PluginError(Exception):
    """구성 오류이거나 트레이스를 읽거나 이어 쓸 수 없다는 것. 채널은 진단만 적고 끝낸다.

    없는 플러그인, 매니페스트 파싱 실패, 진입점 import 실패는 실행 식별자를 만들기 전에 나므로
    트레이스가 없다. 읽을 수 없는 트레이스, 재개할 수 없는 트레이스, 이어 쓸 수 없는 트레이스는
    트레이스가 있는 채로 난다(ADR 0012 의 2026-09-22 이력과 2026-09-23 이력 둘째).

    그 가운데 요청을 고쳐서 풀리는 둘은 하위 타입이다 — `Absent` 와 `NotResumable`. 채널이 이것으로
    실행 전 실패를 가르고 상태 코드로의 번역은 core 밖의 표 한 곳이 한다(ADR 0014). core 는 상태
    코드를 모른다.
    기반 타입을 잡는 채널(CLI)은 하위 타입이 생겨도 바뀌지 않는다.
    """


class Absent(PluginError):
    """요청이 이름을 댄 것이 없다. `run()` 이 받은 에이전트와 `resume()` 이 받은 실행이다.

    재개할 때 트레이스가 가리키는 에이전트가 없는 것은 이것이 아니다. 이름을 댄 것이 요청이 아니라
    서버가 가진 기록이고, 요청이 가리킨 실행은 있다(ADR 0014 의 2026-09-24 이력).
    """


class NotResumable(PluginError):
    """요청이 가리킨 실행이 있지만 재개할 수 없다. 일시정지가 아니거나 형식 1 트레이스다.

    손상된 트레이스는 이것이 아니다. 실행의 상태가 아니라 기록이 깨진 것이라 `PluginError` 그대로다.
    """


@dataclass(frozen=True)
class UnknownEvent:
    """이 런타임이 모르는 종류. 원문을 그대로 들고 있어 옛 도구가 새 트레이스를 지우지 않는다."""

    raw: str


# 트레이스 형식 버전의 집합. 2 부터 이벤트가 재개의 입력이 될 만큼 두껍다(ADR 0008, 0009).
# 버전이 뜻하는 것은 이벤트의 내용이라 어댑터가 아니라 여기가 소유한다. 어댑터는 이것을 헤더에 쓴다.
type TraceSchemaVersion = Literal["1", "2"]


@dataclass(frozen=True)
class Trace:
    """한 실행의 트레이스. 이벤트는 쓴 순서 그대로다.

    schema_version 은 저장소가 그 실행을 쓸 때의 형식 버전이다. 버전 1 은 재개의 입력이 되는
    필드가 비어 있어 읽을 수는 있지만 재개할 수 없다(ADR 0009). 그 판정은 재개 진입점이 한다.
    """

    run_id: RunId
    schema_version: TraceSchemaVersion
    events: tuple[Event | UnknownEvent, ...]


# 실행 상태의 와이어 값 넷(ADR 0012). 넷째를 "실행 중"이라 부르지 않는 이유는 트레이스만으로는
# 증명할 수 없는 주장이기 때문이다. 프로세스가 죽어 사라진 실행도 끝 이벤트 없이 똑같이 보인다.
type RunStatus = Literal["paused", "finished", "failed", "unfinished"]


@dataclass(frozen=True)
class RunSummary:
    """목록에서 보이는 한 실행의 개요. 필드 일곱이고 전부 트레이스에서 파생된다(ADR 0012 이력).

    프롬프트, 토큰 수, 출력, 이벤트는 여기 없다. 목록은 개요를 보는 자리이지 내용을 읽는 자리가
    아니고, 목록 응답 하나가 모든 실행의 내용을 나르면 안 된다. 상태는 어디에도 저장하지 않는다.
    """

    run_id: RunId
    status: RunStatus
    schema_version: TraceSchemaVersion
    started_at: datetime
    last_at: datetime
    agent: AgentName
    principal: Principal


@dataclass(frozen=True)
class UnreadableTrace:
    """읽히지 않는 트레이스가 목록에서 요약 자리에 대신 세우는 표지(ADR 0012 이력).

    실행 식별자는 파일 이름에서 나오므로 확실하고, 나머지 여섯은 헤더와 이벤트에서 와 알 수 없다.
    부분 요약을 두지 않는 이유가 그것이다 — 필드를 선택으로 만들면 읽히는 행의 타입까지 약해지고,
    실행 상태에 다섯째 값을 두면 "값은 넷"을 개정하는 것이 된다. 표지는 요약이 아닌 다른 것이다.
    """

    run_id: RunId
    reason: str


@dataclass(frozen=True)
class UnreadableManifest:
    """매니페스트로 읽히지 않는 것이 목록에서 대신 세우는 표지. 선례는 위의 UnknownEvent 다.

    조용히 빼지도 않고 목록 전체를 실패시키지도 않는 이유, 단건이 그대로 PluginError 인 이유는
    ADR 0012 의 2026-09-22 이력에 있다.

    name 이 PluginName 이 아니라 str 인 것은 이 표지가 서는 경우 중 하나가 "디렉터리 이름이 플러그인
    이름의 패턴을 어긴다" 이기 때문이다. 유효한 이름이 아닌 값을 유효한 이름의 타입에 담으면 그
    타입이 뜻하는 것이 거짓이 된다. 이 이름으로 단건을 물으면 형식 위반이라 포트에 닿기 전에
    끝나지만, 표지는 이미 종류와 이름과 이유를 다 들고 있어 되물을 필요가 없다.
    """

    kind: PluginKind
    name: str
    reason: str


# 목록의 행. 읽힌 것과 표지가 같은 열에 산다.
type RunRow = RunSummary | UnreadableTrace
type ManifestRow = PluginManifest | UnreadableManifest

# 목록의 기본 개수와 상한. 상한이 있어야 하는 이유는 첫 어댑터가 디렉터리를 훑어 전부 만든 뒤
# 자르기 때문이다 — 없으면 요청 하나가 "실행이 쌓여도 목록 응답이 그만큼 커지지 않는다"를
# 무력화한다. 두 숫자는 계약이라 openapi.json 에 박히고, 질의 검증도 이것을 읽는다.
# 상한이 막는 것은 응답 크기까지다. 스캔 비용은 저장소의 실행 개수에 비례하고 limit 이 그것을
# 줄이지 않으므로(자르는 것이 전부 만든 뒤다) 색인이 붙을 때까지 그렇다.
DEFAULT_LIMIT = 50
MAX_LIMIT = 200

# 시작 시각이 없는 행(표지)을 정렬 키에 앉히는 자리. 값 자체는 비교에만 쓰이고 밖으로 나가지 않는다.
_NO_START = datetime.min.replace(tzinfo=UTC)


@dataclass(frozen=True)
class Cursor:
    """목록의 정렬 키 하나. 오프셋이 아니라 키 그대로다(ADR 0012).

    오프셋을 쓰지 않는 이유는 트레이스가 계속 추가되는 디렉터리라 새 실행이 생길 때마다 페이지가
    밀리기 때문이다. 시작 시각이 없는 것은 표지뿐이고 그것은 실행 식별자로만 갈린다.
    """

    started_at: datetime | None
    run_id: RunId


def run_status(last: Event | UnknownEvent) -> RunStatus:
    """마지막 이벤트 하나로 실행 상태를 파생한다. 규칙이 사는 유일한 자리다(ADR 0012).

    관리와 채널과 CLI가 각자 다시 구현하면 셋이 다르게 대답한다. 모르는 종류여도 결말 없음인 것은
    파생 규칙을 문자 그대로 적용한 결과다 — 그 줄은 읽혔으므로 표지가 아니라 요약이고, 다섯째
    상태 값을 만들지 않는다.
    """
    match last:
        case RunPaused():
            return "paused"
        case RunFinished():
            return "finished"
        case RunFailed():
            return "failed"
        case _:
            return "unfinished"


def cursor_of(row: RunRow) -> Cursor:
    """행 하나의 정렬 키. 다음 쪽을 물을 때 그대로 after 가 된다."""
    if isinstance(row, UnreadableTrace):
        return Cursor(started_at=None, run_id=row.run_id)
    return Cursor(started_at=row.started_at, run_id=row.run_id)


def order_key(cursor: Cursor) -> tuple[bool, datetime, RunId]:
    """내림차순으로 정렬할 때의 비교 키. 정렬과 커서 비교가 같은 것을 보게 하려고 함수 하나다.

    내림차순이라 시작 시각이 있는 행이 먼저이고, 시각이 역순이며, 동률은 실행 식별자로 갈린다.
    표지는 시각이 없어 맨 뒤에 모이고 그 안에서도 식별자로 갈리므로 열 전체가 전순서다. 커서가
    어느 행이든 가리킬 수 있어야 페이지가 겹치지도 빠지지도 않는다.
    """
    at = cursor.started_at
    return (at is not None, at if at is not None else _NO_START, cursor.run_id)


class TraceStore(Protocol):
    """이벤트를 쓰고 한 실행의 트레이스를 읽고 실행들을 열거한다. 첫 어댑터는 JSONL 파일.

    쓰는 곳과 읽는 곳이 항상 같다는 사실을 이 타입 하나가 강제한다(ADR 0009). 부재는 None.
    """

    def write(self, event: Event) -> None: ...

    def read(self, run_id: RunId) -> Trace | None: ...

    def list(
        self,
        *,
        status: RunStatus | None = None,
        limit: int | None = None,
        after: Cursor | None = None,
    ) -> Sequence[RunRow]:
        """실행 요약을 시작 시각 역순으로. 트레이스 전체가 아니다(ADR 0012).

        요약을 돌려주는 이유는 상태 파생 규칙의 소유권이다. run_id 만 돌려주면 부르는 쪽이 각
        실행을 다시 읽어(N+1) 상태를 직접 파생시켜야 하고 그 규칙이 core 밖으로 샌다.

        셋 다 선택이다. status 는 그 상태의 실행만 남기고(표지는 상태가 없어 함께 빠진다), after
        는 그 키 다음부터 준다. limit 은 개수를 자르며 없으면 DEFAULT_LIMIT 이고, **1 과
        MAX_LIMIT 사이가 아니면 ValueError 다.** 조용히 clamp 하지 않는 이유는 그것이 상한을
        요구한 이유를 무력화하는 요청을 성공으로 만들기 때문이고, PluginError 가 아닌 이유는 이것이
        디스크 손상이 아니라 부르는 쪽의 오류라서 HTTP 에서 500 이 아니라 422 로 갈려야 하기
        때문이다. 첫 어댑터는 디렉터리를 훑어 전부 만든 뒤 자르지만 시그니처가 이미 필터를 받으므로
        색인을 붙일 때 어댑터만 바뀐다.
        """
        ...


class PluginSource(Protocol):
    """매니페스트를 읽고 종류별로 열거하고 에이전트를 로드한다. 첫 어댑터는 파일시스템(ADR 0003).

    부재는 None, 실패(파싱, import)는 PluginError.
    """

    def read_manifest(self, kind: PluginKind, name: PluginName) -> PluginManifest | None: ...

    def list_manifests(self, kind: PluginKind) -> Sequence[ManifestRow]:
        """종류 하나의 매니페스트를 전부. 파일시스템 배치가 종류별 디렉터리라 종류가 인자다.

        읽히는 것은 전부 돌아오고 읽히지 않는 것은 표지로 남는다. 없는 디렉터리는 빈 목록이다.
        """
        ...

    def load_agent(self, manifest: PluginManifest) -> BaseAgent: ...


class Clock(Protocol):
    """현재 시각(UTC)과 실행 식별자. 첫 어댑터는 시스템 시계와 uuid4."""

    def now(self) -> datetime: ...

    def new_run_id(self) -> RunId: ...


@dataclass(frozen=True)
class ToolSpec:
    """모델에게 붙일 도구 하나. input_schema 는 JSON Schema."""

    name: str
    description: str
    input_schema: Mapping[str, Json]


@dataclass(frozen=True)
class ToolResult:
    """도구가 돌려준 것. ok 가 거짓이면 content 는 에러 내용이다."""

    ok: bool
    content: str


class ToolConnection(Protocol):
    """ToolSource 가 연 연결. 도구 목록을 주고 도구를 부른다."""

    def tools(self) -> Sequence[ToolSpec]: ...

    async def call(self, name: str, args: Mapping[str, Json]) -> ToolResult: ...


class ToolSource(Protocol):
    """서버 명세를 받아 도구를 연결한다. 시작과 종료의 수명이 있다. 첫 어댑터는 MCP stdio.

    connect 가 실패하면(서버 기동 실패) 실행은 run_failed 로 끝난다. 비어 있으면 도구 없이 연다.
    """

    def connect(
        self, servers: Mapping[PluginName, McpServer]
    ) -> AbstractAsyncContextManager[ToolConnection]: ...
