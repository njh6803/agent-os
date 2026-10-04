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

    없는 플러그인, 매니페스트 파싱 실패, 진입점 import 실패, 운영자 파일의 손상, 꺼진 플러그인, 이어
    갈 수 없는 앞 실행과 깨진 고리는 새 실행에서는 실행 식별자를 만들기 전에 나므로 트레이스가 없고,
    재개에서는 결정 이벤트를 쓰기 전에 나므로 트레이스가 그대로다. 읽을 수 없는 트레이스, 재개할 수
    없는 트레이스, 지금의 일시정지가 아닌 자리를 든 결정, 이어 쓸 수 없는 트레이스는 트레이스가 있는
    채로 난다(ADR 0012 의 2026-09-22 이력과 2026-09-23 이력 둘째, ADR 0014 의 2026-09-28 이력).

    하위 타입을 가르는 기준은 "깨졌나"다(ADR 0014 의 2026-09-26 이력). 대상이 없는 것(`Absent`)과
    대상의 상태나 주체가 요청을 허락하지 않는 것(`NotResumable`, `Disabled`, `DifferentPrincipal`,
    `NotContinuable`)은 하위 타입이고, 하위 타입을 뺀 뒤 남는 것이 서버의 구성이나 기록이 깨진
    것이다. 채널이 이것으로 실행 전 실패를 가르고 상태 코드로의 번역은 core 밖의 표 한 곳이 한다(ADR
    0014). core 는 상태 코드를 모른다. 기반 타입을 잡는 채널(CLI)은 하위 타입이 생겨도 바뀌지
    않는다.
    """


class Absent(PluginError):
    """요청이 이름을 댄 것이 없다. `run()` 이 받은 에이전트와 이어 갈 앞 실행, `resume()` 이 받은
    실행이다. 요청이 댄 앞 실행이 sdk 의 패턴을 어긴 것도 이것이다 — 런타임은 그런 이름의 트레이스를
    만들 수 없다.

    재개할 때 트레이스가 가리키는 에이전트가 없는 것과 이어 가기의 고리에서 만나는 실행이 없는 것은
    이것이 아니다. 이름을 댄 것이 요청이 아니라 서버가 가진 기록이고, 요청이 가리킨 실행은 있다(ADR
    0014 의 2026-09-24 이력, ADR 0022).
    """


class NotResumable(PluginError):
    """요청이 가리킨 실행이 있지만 재개할 수 없다. 뜻은 셋이고 메시지가 가른다.

    형식 1 트레이스이거나, 일시정지가 아니거나, 결정이 가리킨 자리가 지금의 일시정지가 아니다(ADR
    0014 와 그 2026-09-28 이력). 손상된 트레이스는 이것이 아니다. 실행의 상태가 아니라 기록이 깨진
    것이라 `PluginError` 그대로다.
    """


class DifferentPrincipal(PluginError):
    """요청이 가리킨 실행이 있지만 요청한 주체의 것이 아니다(ADR 0022·0023). 메시지가 실행을 든다.

    지금 던지는 자리는 이어 가기(`run(previous_run=)`) 하나다. 이어 가는 쪽의 주체가 앞 실행의
    `run_started` 주체와 다른 것이다. 결정의 주체 판정은 end-user-channel 기능이 같은 타입으로
    더하기로 했다(ADR 0009 의 2026-10-03 이력, ADR 0023). 손상된 트레이스의 주체는 믿을 수 없으므로
    손상(`PluginError` 그대로)이 이것보다 먼저이고, 이것이 끝나지 않음(`NotContinuable`)보다 먼저다
    — 최종 사용자 경로가 남의 실행을 없는 실행처럼 숨기려면 남의 실행의 상태가 먼저 드러나면 안
    된다. 메시지는 남의 주체 이름을 들지 않는다. 운영자 채널의 표는 409 로 옮기고, 최종 사용자
    경로의 404 와 CLI 의 진단은 그 기능이 더한다.
    """


class NotContinuable(PluginError):
    """요청이 가리킨 앞 실행이 있고 주체도 같지만 `run_finished` 로 끝나지 않아 이어 갈 수 없다.

    실패, 일시정지, 결말 없음이다(ADR 0022). 끝나지 않은 실행에는 출력이 없어 교환이 되지 않는다.
    메시지는 `run_status()` 로 파생한 상태를 든다 — 실패인지 일시정지인지에 따라 할 일이 다르다.
    `NotResumable` 을 쓰지 않는 이유는 그 이름과 독스트링이 재개를 말하기 때문이다. 이어 가기는
    재개가 아니다(용어집). 고리의 중간 실행이 끝나지 않은 것은 이것이 아니라 기록이 깨진 것이다.
    """


class Disabled(PluginError):
    """요청이 부른 플러그인이 있지만 운영자가 꺼 두었다(ADR 0017). 메시지가 종류와 이름을 든다.

    깨진 것이 아니라 운영자가 고른 상태다. 대상은 있지만 상태 때문에 요청을 허락하지 않으므로
    `NotResumable`·`NotContinuable`·`DifferentPrincipal` 과 같은 409 의 자리에 선다. 던지는 자리는
    `run()` 과 `resume()` 의 준비 단계이고, 요청한 에이전트, 재개할 실행의 트레이스가 가리키는
    에이전트, 그 에이전트가 쓰는 mcp 가 대상이다. 판정 순서와 그 이유는 `core/run.py` 의 `_prepare`.
    꺼진 것이 무엇인지는 `PluginSource.read_disabled()` 가 답한다.
    """


@dataclass(frozen=True)
class UnknownEvent:
    """이 런타임이 모르는 종류. 원문을 그대로 들고 있어 옛 도구가 새 트레이스를 지우지 않는다."""

    raw: str


# 트레이스 형식 버전의 집합. 2 부터 이벤트가 재개의 입력이 될 만큼 두껍다(ADR 0008, 0009). 3 은
# 시작 이벤트에 이어 간 앞 실행이 늘고 대화 요약 이벤트가 생긴 것이다(ADR 0022). 형식을 올린 이유는
# 옛 런타임이 형식 3 파일을 헤더에서 통째로 거부하게 하기 위해서다 — 이 목록에 없는 버전은 읽히지
# 않으므로 반쯤 읽고 잘못 재개할 길이 없다. 버전이 뜻하는 것은 이벤트의 내용이라 어댑터가 아니라
# 여기가 소유한다. 어댑터는 이것을 헤더에 쓴다.
type TraceSchemaVersion = Literal["1", "2", "3"]


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


@dataclass(frozen=True)
class PluginKey:
    """플러그인 하나를 가리키는 (종류, 이름). 켜고 끄는 키다(ADR 0017).

    매니페스트가 아니라 이것이 키인 이유는 매니페스트가 읽히지 않는 플러그인도 끌 수 있어야 하기
    때문이다. 이름이 `PluginName` 인 것은 패턴을 어긴 이름이 운영자 파일에 들 수 없어서다 —
    그런 파일은 손상이다. 디렉터리가 없는 이름(고아 항목)은 들 수 있다. 그것은 손상이 아니다.
    """

    kind: PluginKind
    name: PluginName


# 켜짐 쓰기의 결과. 부재를 예외가 아니라 값으로 말하는 것이 이 포트의 약속이고(ADR 0012 의
# 2026-09-26 이력), 손상과 쓰기 실패는 PluginError 다. 이미 그 상태였어도 `applied` 다 — 요청한
# 켜짐이 지금 상태라는 뜻이지 파일을 건드렸다는 뜻이 아니다.
type WriteOutcome = Literal["applied", "absent"]

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
    """매니페스트를 읽고 종류별로 열거하고 에이전트를 로드하며, 꺼진 것을 읽고 켜짐을 쓴다. 첫
    어댑터는 파일시스템(ADR 0003).

    부재는 None 이나 값으로, 실패(파싱, import, 운영자 파일의 손상, 쓰기 실패)는 PluginError 로
    말한다. 켜짐은 플러그인 루트의 운영자 파일이 들고 닿는 바깥 지점이 플러그인 디렉터리
    그대로라 새 포트가 아니라 이 포트의 메서드 둘이다(ADR 0017, ADR 0012 의 2026-09-26 이력).
    """

    def read_manifest(self, kind: PluginKind, name: PluginName) -> PluginManifest | None: ...

    def list_manifests(self, kind: PluginKind) -> Sequence[ManifestRow]:
        """종류 하나의 매니페스트를 전부. 파일시스템 배치가 종류별 디렉터리라 종류가 인자다.

        읽히는 것은 전부 돌아오고 읽히지 않는 것은 표지로 남는다. 없는 디렉터리는 빈 목록이다.
        """
        ...

    def load_agent(self, manifest: PluginManifest) -> BaseAgent: ...

    def read_disabled(self) -> frozenset[PluginKey]:
        """꺼진 (종류, 이름)의 집합을 한 번에. 운영자 파일이 없으면 빈 집합, 손상이면 PluginError.

        한 번에 읽는 이유는 둘이다. 관리 목록이 행마다 파일을 다시 읽지 않고, core 의 준비 단계가
        에이전트와 mcp 들을 같은 순간의 상태로 판정한다(준비 한 번에 한 번 읽는다).
        **동기다.** 준비 단계는 `resume()` 의 첫 걸음 안이고 그 첫 걸음에 `await` 가 없다는 것이
        동시 재개의 불변식이다(ADR 0014). 캐시하지 않는다 — 부를 때마다 읽으므로 손편집도 다음
        요청부터 효력이 난다.
        """
        ...

    def write_enabled(self, kind: PluginKind, name: PluginName, enabled: bool) -> WriteOutcome:
        """(종류, 이름) 하나의 켜짐을 쓴다. `enabled` 는 쓸 값이지 동작을 고르는 플래그가 아니다.

        부재는 값으로 말한다. 그 자리에 매니페스트 파일이 없으면 쓰지 않고 `absent` 다. 판정 대상은
        파일이 있느냐이지 읽히느냐가 아니라, 매니페스트가 읽히지 않는 플러그인도 끌 수 있다. 부재
        판정이 운영자 파일의 손상 판정보다 먼저이고, 손상 판정이 "바뀌는 것이 없다"는 판단보다
        먼저다(ADR 0017 의 2026-09-27 둘째 이력). 바뀌는 것이 없으면 파일을 건드리지 않는다. 이것도
        동기다 — 한 프로세스 안의 쓰기 둘을 이벤트 루프가 줄세운다는 전제가 여기에 기댄다.
        """
        ...


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
