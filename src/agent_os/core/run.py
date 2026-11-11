"""주 이음매. 에이전트를 돌려 이벤트를 내는 async generator 둘, run() 과 resume().

로더, 루프, 도구 연결, 승인 게이트, 재생, 트레이스 기록, 실패 정책이 전부 이 아래에 있어서 기본
스위트가 이 지점 하나를 민다. run_started, run_paused, approval_granted, approval_denied,
run_resumed, run_failed 는 런타임이 내고, 에이전트는 run_finished 하나를 마지막에 낸다.
conversation_summarized 는 런타임이 이어 가기에서 원문 교환이 글자 수 한도나 교환 수 기준을 넘었을
때 에이전트를 부르기 전에 낸다(계기, 범위, 실패는 core/continuation.py). 에이전트가 낸 다른 이벤트는
통과하되 런타임만 내는 둘, conversation_summarized 와 run_failed 는 예외다 — 에이전트가 내면 그
실행은 런타임의 run_failed 로 끝나고 에이전트의 제너레이터는 그 자리에서 닫힌다. 앞의 것은 다음
실행의 거슬러 읽기가 트레이스에서 읽는 입력이고(ADR 0022), 뒤의 것은 결말이라 런타임이 쓰는 하나여야
하며 원인이 든 실패는 런타임만 낸다(ADR 0031). tool_called 와 run_paused 도 적용 규칙·서버 칸
(rule, server)을 채우면 같은 길로 끝난다(ADR 0044). 이유는 `_reject_runtime_only`. 거부는 실행을
끝내지 않는다. 거부된 도구 호출은 불리지 않고 tool_called(ok=false) 로 사유가 모델에게 돌아가며,
에이전트가 정상적으로 끝맺는다(ADR 0009). 매니페스트의 두 끝(max_turns, max_tool_calls)도 여기서
집행한다 — 턴의 끝은 루프가, 도구 호출의 끝은 도구를 부르는 자리가 지키고, 끝을 넘은 호출은 규칙이
정한 것이 아니라 rule 을 비운 같은 거부다(ADR 0052). 게이트는 도구를 부르는 한
자리(`_Context._call`)이고, 운영자의 규칙 파일(rules.toml)이 그 자리에서 도구 호출마다 집행된다.
deny 는 거부로 기록하고, 저자의 requires_approval 과 ask 와 어디에도 맞지 않는 default 는 일시정지,
allow 만 곧바로 부른다(ADR 0044). 규칙이 도구를 묻게 둘 수 있는 도구에는 마스킹된 인자가 없어야
하고(실행 전), 에이전트 표가 적은 줄은 연결에 실재해야 하며(연결 직후), 재개는 멈춘 도구를 낸
서버까지 대 본다(재개 뒤 첫 호출).

이어 가기는 run() 의 키워드 인자 previous_run 이다(ADR 0022). 재개와 달리 입력이 run() 의 것에 앞
실행 하나가 더해진 것이라 함수를 따로 두지 않는다. 없음(None)은 새 대화라는 뜻 하나뿐이고 고리를
짐작하는 기본값이 없다. 이어 간 실행은 새 실행 식별자와 새 트레이스 파일을 갖고 run_started 에 앞
실행과 바로가기를 적는다. 바로가기는 이 자리 하나가 지어(새 대화는 빈 지도, 이어 가기는 앞 실행의
지도에 앞 실행 자신을 덮어 쓴 것, 옛 대화는 없음) 운영자 채널, CLI, 최종 사용자 경로가 같은 지도를
쓴다. 에이전트는 고리에서 자기가 처리한 교환과 자기 대화 요약만 컨텍스트 멤버로 받고, 거슬러 읽기는
지도를 따라 그 에이전트의 실행만 읽는다(`continuation.py`).

resume() 이 run() 의 인자가 아닌 이유는 입력이 실제로 다르기 때문이다. 재개는 에이전트 이름,
요청, 주체를 받지 않고 트레이스의 run_started 에서 읽는다. 하나로 합치면 "재개일 때는 이 인자
셋이 무시된다"는, 타입으로 막을 수 없는 규칙을 문서로 적어야 한다(ADR 0009). 내부는 몸통(`_Body`)을
공유하고 갈리는 것은 이벤트를 어디서 얻나(재생이냐 실제 호출이냐)와 무엇을 트레이스에 쓰나뿐이다.

재생 구간에서 생긴 사실은 트레이스에 다시 쓰지 않는다. 이미 거기 있기 때문이고, 에이전트가 낸
것도 마찬가지다. 기준은 "재생 구간인가"가 아니라 "이미 트레이스에 있는가"라서, 재생 구간에서
처음 생긴 사실인 대조 불일치의 run_failed 는 쓴다. 사실이 한 번씩만 남는다.

실행 전과 실행 중의 경계: 없는 플러그인, 매니페스트 오류, 진입점 import 실패, 없는 mcp 이름,
없거나 읽히지 않는 모델 매니페스트, 없거나 읽히지 않는 스킬 매니페스트와 스킬 문서, 모델 만들기의
실패(모델 소스가 거부한 매니페스트), 마스킹과 승인이 겹치는 도구와 마스킹된 인자가 있는데 규칙이
묻게 두는 도구, 운영자 파일의 손상, 운영자가 끈
에이전트나 mcp나 모델이나 스킬, 이어 갈 수 없는 앞 실행(없음, 손상, 다른 주체, 끝나지 않음)과 깨진
고리는 실행 식별자를 만들기 전에 PluginError 로 끝나 트레이스가 없다. 재개할 수 없는 트레이스(없음,
손상, 다른 주체, 열 에이전트 밖, 형식 1, 일시정지 아님)와 지금의 일시정지를 가리키지 않는 결정(자리
어긋남)도 같은 자리의 PluginError 다. 재개에서는 위의 것이 전부(꺼짐과 운영자 파일의 손상, 깨진
고리도) 결정 이벤트를 쓰기 전에 나 트레이스가 그대로다. 저장소가 결정 이벤트를 이어 쓰지 못해도
PluginError 이고 도구를 부르지 않는다(ADR 0012 이력). 하위 타입을 가르는 기준은 "깨졌나"다 — 대상이
없거나 대상의 상태나 주체가 요청을 허락하지 않는 것이 4xx 를 내는 하위 타입이고 그 밖의 것은 서버의
구성이나 기록이 깨진 것이다(ADR 0014 의 2026-09-26 이력). 깨진 것 가운데 요청이 가리킨 실행을 그
주체와 견주기 전에 만난 손상만 TraceDamagedBeforePrincipal 로 따로 선다(`before_principal`, ADR 0023
의 2026-10-16 이력). 요청이 댄 에이전트나 실행이나 이어 갈 앞 실행이 없거나, 호출자가 볼 수 있는
에이전트의 집합 밖이면 Absent, 실행이 형식 1 이거나 일시정지가 아니거나 결정이 가리킨 자리가 지금의
일시정지가 아니면 NotResumable(ADR 0014 와 그 2026-09-28 이력), 요청이 부른 에이전트나 그것이 쓰는
mcp 나 모델이나 스킬을 운영자가 꺼 두었으면 Disabled(ADR 0017, ADR 0040, ADR 0041), 결정하는 쪽이 그
실행의 주체가 아니거나 앞 실행이 다른 주체의 것이면 DifferentPrincipal, 앞 실행이 run_finished 로
끝나지 않았으면 NotContinuable 이다(ADR 0022·0023). 재개할 실행의 트레이스가 가리키는 에이전트가
없는 것과 고리에서 만나는 실행이 없거나 깨진 것은 요청이 아니라 서버의 기록이 댄 것이라 기록과
구성이 어긋난 것, 곧 기반 타입 PluginError 그대로다. 판정 순서는 부재 → 깨짐 → 꺼짐 → 진입점 import
→ 모델 만들기다. 그 이유는 `_prepare`. 이어 가기는 그 앞에 앞 실행(없음 → 손상 → 다른 주체 → 끝나지
않음)과 고리의 판정이 선다. 그 이유는 core/continuation.py 다. 재개는 그 앞에 트레이스 판정(없음 →
손상 → 다른 주체 → 열 에이전트 밖 → 형식 1 → 일시정지 아님 → 자리 어긋남)과 고리가 선다. 그 이유는
`_read_paused` 와 `read_own_run` 이다. 요약이 실패한 실행은 run_started 뒤에 run_failed 로 끝나고
에이전트를 부르지 않는다. MCP 서버 기동 실패부터는 실행 안이라 run_failed 로 끝나고 트레이스가
남는다. 매니페스트가 가리키는 도구와 인자의 실재는 도구 목록이 연결 뒤에야 나오므로 연결 직후에
검사하고, 어긋나면 실행 안의 실패다(ADR 0009). 규칙 파일의 에이전트 표가 적은 줄이 연결에 없는
것도 같은 자리의 같은 실패다(ADR 0044). 그 검사는 재개에서도 같은 자리에서 돈다.

실행 타임아웃(ADR 0014 의 2026-10-05 이력 "실행에 타임아웃이 생긴다"): 시작 이벤트(재개에서는 결정
이벤트)를 쓴 뒤 정한 시간 안에 결말이 나지 않으면 run_failed("실행이 N초 안에 끝나지 않았다")로
끝난다. 자리는 진입점 둘이고, 진입점이 `anyio.move_on_after` 를 열어 몸통(`_Body`) 하나를 감싼다
— 몸통은 이어 가기의 요약 호출부터 결말까지다. 기한이 오면 취소가 안쪽 await 에 들어가고, 취소는
BaseException 이라 몸통과 요약의 `except Exception` 을 지나쳐 범위가 받는다. 진입점은 범위가 실제로
취소를 받았는지(`cancelled_caught`)로 기한을 본다 — 예외의 타입으로 보면 디스크나 네트워크
드라이브가 낸 `TimeoutError`(ETIMEDOUT)도 기한으로 읽힌다. 그 TimeoutError 는 다른 예외와 같다 —
몸통이 받는 자리(연결, 에이전트, 결말 전 쓰기)에서는 그 자리의 원인이고, 몸통이 받지 않는 자리(요약
이벤트 쓰기, 결말 쓰기)에서는 결말 없이 올라온다.
기한이면 몸통에게 결말을 묻고(`_Body.deadline_failure`) 이미 썼으면 아무것도, 붙잡은 실패가 있으면
그것을, 아니면 시간 초과를 쓴다. 그래서 요약 중이었어도 같은 메시지이고, 결말을 쓴 뒤 도구 연결을
닫다 기한이 와도 결말이 둘이 되지 않는다. 부르던 도구는 취소되어 tool_called 가 없고, 그때까지 쌓인
런타임 이벤트(재개 이벤트 따위)는 결말 앞에 흘린다. 테스트가 기한을 떨어뜨린 자리는 요약 호출, 모델
호출, 도구 호출, 도구 연결의 닫기이고 도구 연결을 여는 자리는 같은 모양이라는 어림이다. 재개마다
다시 센다 — 멈춰 있는 시간은 세지 않는다(ADR 0009). 기한은 시계 포트가 아니라 이벤트 루프의 시계로
센다. 범위와 몸통이 에이전트를 돌리는 태스크 그룹(ADR 0039)이 yield 를 건너므로 부르는 쪽은 이벤트
사이에 await 하지 않는다 — 도구 연결의 취소 범위가 이미 요구하던 것이다(`.claude/rules/channel.md`).

실패 원인(ADR 0031, end-user-continuation 명세 "실패 원인"): 런타임이 쓰는 run_failed 는 모두
원인 아홉 가운데 하나를 들고, 원인은 실패가 처음 생긴 자리로 정한다. 요약 호출은 대화 요약, 기한은
시간 초과다(요약 도중이어도). 몸통이 실패를 받는 자리는 닫힌 열거(`_Site`: 연결, 에이전트, 연결 안의
나머지, 결말 전 쓰기)이고 자리에서 원인으로 가는 갈래(`_cause_at`)에 기본 갈래가 없다. 에이전트
자리의 예외는 런타임이 에이전트에게 던진 그 객체(`_Thrown`)면 던진 자리의 원인이고 아니면 에이전트
코드다 — 타입이 아니라 동일성으로 가른다. 런타임이 에이전트에게 던지는 예외를 더하는 변경은 던지는
자리의 기억과 그 원인을 단언하는 테스트를 함께 더한다. 타입 검사가 보지 못하는 빠짐은 그것 하나다.
먼저 난 실패가 결말이다 — 에이전트 몫의 실패와 선언 확인의 실패는 도구 연결을 닫기 전에
붙잡고(`_Body._hold`), 런타임이 에이전트 자리에서 던진 실패는 에이전트를 닫기 전에 붙잡는다. 닫기의
예외와 닫는 도중의 기한은 그것을 바꾸지 못한다. 결말을 쓴 뒤 닫기가 실패하면 run_failed 를
덧붙이지 않는다(대가는 `_Body._connected`). 결말 전 쓰기가 한 번 실패한 실행은 뒤의 run_failed 가
그 밖을 든다 — 일시정지를 쓰지 못한 실행도 멈춘 것이 아니라 그렇다. run_failed 까지 쓰지 못하면
원인도 결말도 없이 예외가 올라온다.
"""

from __future__ import annotations

from collections.abc import (
    AsyncGenerator,
    AsyncIterator,
    Awaitable,
    Callable,
    Generator,
    Mapping,
    Sequence,
)
from contextlib import aclosing, asynccontextmanager, contextmanager, suppress
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, NoReturn, TypeGuard, assert_never, get_args

import anyio
import anyio.to_thread
from anyio.streams.memory import MemoryObjectSendStream
from langchain_core.messages import AIMessage, BaseMessage

from agent_os.core.continuation import (
    NEW_CONVERSATION,
    Fold,
    Link,
    before_principal,
    check_record_rules,
    gather_continued,
    limit_of,
    link_of,
    plan_fold,
    resumed_conversation,
    summarize,
)
from agent_os.core.loop import MAX_TURNS, LoopLimitExceeded, ModelCaller, model_caller, run_loop
from agent_os.core.model import ModelReply, message_from, reply_from
from agent_os.core.ports import (
    Absent,
    ChatModel,
    Clock,
    DifferentPrincipal,
    Disabled,
    ModelSource,
    NotResumable,
    PluginError,
    PluginKey,
    PluginSource,
    Rules,
    ToolConnection,
    ToolResult,
    ToolSource,
    ToolSpec,
    TraceSchemaVersion,
    TraceStore,
)
from agent_os.core.replay import Mismatch, Record, Replay
from agent_os.core.rules import applied_rule, unresolved_rule_lines
from agent_os.sdk import (
    AgentName,
    AppliedRule,
    ApprovalDenied,
    ApprovalGranted,
    BaseAgent,
    BaseEvent,
    Conversation,
    ConversationSummarized,
    Event,
    FailureCause,
    Json,
    LlmCalled,
    McpServer,
    PluginKind,
    PluginManifest,
    PluginName,
    Principal,
    RunFailed,
    RunFinished,
    RunId,
    RunPaused,
    RunResumed,
    RunStarted,
    Skill,
    ToolCall,
    ToolCalled,
    ToolError,
    approval_conflicts,
    secret_args_by_tool,
)

MASKED = "***"

# 재개할 수 있는 트레이스 형식. 1 은 재개의 입력이 되는 필드가 비어 있어 읽기만 된다(ADR 0009).
# 어댑터가 쓸 때 붙이는 버전과 뜻이 달라 따로 둔다. 형식이 늘면 여기에 받아들일 것을 더한다. 2 와 3
# 의 차이는 시작 이벤트의 앞 실행과 대화 요약 이벤트뿐이라 둘 다 재개한다(ADR 0022). 이어 가기는
# 형식을 가리지 않는다 — 앞 실행을 재개하는 것이 아니라 읽는 것이고 필요한 것은 형식 1 에도 있다.
RESUMABLE: tuple[TraceSchemaVersion, ...] = ("2", "3")

# 실행 하나가 시작 이벤트(재개에서는 결정 이벤트)를 쓴 뒤 결말까지 갈 수 있는 시간(초). `run()`·
# `resume()` 이 타임아웃을 받지 않으면 이것이다. 루프 상한(`MAX_TURNS`)과 기본 대화 한도처럼 core 가
# 소유하고 `serve` 의 인자는 기본값을 따로 두지 않는다 — 600 이 서는 자리가 하나다(명세 검토). 루프
# 상한 10턴에 모델 호출 수십 초를 곱한 어림이다(end-user-channel 명세 "실행 타임아웃").
DEFAULT_RUN_TIMEOUT_SECONDS = 600

# 재생 기록 열에 들지 않는 이벤트. 경계 이벤트(실행의 시작과 재개의 경계를 표시하는 것들)는 재생할
# 사실이 아니고, 대화 요약은 에이전트가 부른 호출이 아니라 런타임이 에이전트를 부르기 전에 한 것이라
# 재개가 모델을 다시 부르지 않고 트레이스에서 읽는다(ADR 0022). 들면 재개의 모델 대조가 LlmCalled 가
# 아닌 기록을 받아 Mismatch 다. 나머지는 런타임의 모델·도구 호출과 에이전트가 낸 것이고, 트레이스만
# 보고는 둘을 구분할 수 없어 함께 센다.
_NOT_REPLAYED = (
    RunStarted,
    RunPaused,
    ApprovalGranted,
    ApprovalDenied,
    RunResumed,
    ConversationSummarized,
)

# sdk 의 이벤트 종류들. `Event` 는 판별자가 붙은 Annotated 합이라 isinstance 에 바로 쓸 수 없어 그
# 합에서 꺼낸다. 에이전트가 이벤트가 아닌 값을 냈는지 보는 데만 쓴다(`_reject_stray`).
_EVENT_KINDS: tuple[type[BaseEvent], ...] = get_args(get_args(Event)[0])

_NO_FINISH = "에이전트가 run_finished 없이 끝났다"

# 몸통이 실패를 받는 자리. 닫힌 열거다 — 도구 연결(연결에 들어가는 동안과 선언 확인),
# 에이전트(에이전트의 순회에서 빠져나온 예외), 연결 안의 나머지(그 둘 밖에서 연결 안의 몫이
# 런타임 자신의 예외로 끝난 것, 이를테면 컨텍스트를 만들다 터진 것), 결말 전의 트레이스 쓰기.
# 요약과 기한은 따로 선 자리라 여기 없고, 도구 연결의 닫기는 자리가 아니다(연결 안의 몫이 끝나면
# 결말을 붙잡았거나 이미 썼으므로 버린다).
# 자리에서 원인으로 가는 갈래는 `_cause_at` 하나이고 기본 갈래가 없어, 자리를 더하면 원인을 정하지
# 않은 갈래가 타입 검사에서 빨개진다 — 그것이 실패 원인의 목록을 다시 볼 계기다(ADR 0031,
# end-user-continuation 명세 "실패 원인").
type _Site = Literal["connection", "agent", "inside", "write"]


class _Thrown:
    """런타임이 이 실행 안에서 에이전트에게 던진 예외와 그 원인. 몸통과 수명이 같다.

    에이전트에서 빠져나온 예외가 여기 든 객체 그 자체(`is`)면 그 원인이고 아니면 에이전트 코드다.
    잡아 그대로 다시 던지면 같은 객체라 원인이 남고, 감싸거나 다른 예외로 바꾸거나 예외 그룹에
    넣으면 에이전트 코드다. `asyncio.TaskGroup` 안에서 불러 그룹으로 올라온 것도 그렇다 — 그룹을
    고른 것은 에이전트다. 타입으로 가르지 않는 이유는 `ToolError` 가 sdk 의 공개 타입이라
    에이전트가 스스로 던질 수 있어서이고, 마지막 하나가 아니라 전부를 드는 이유는
    앞서 받은 예외를 나중에 다시 던지는 에이전트가 있어서다. 에이전트가 받는 예외를 런타임의 새
    타입으로 감싸지 않는다 — 에이전트가 잡는 이름이 바뀐다.

    타입 검사가 보지 못하는 것: 에이전트 자리 안에서 런타임이 새로 던지는 예외를 던지는 자리에서
    여기 기억하지 않으면 그 예외는 에이전트 코드로 간다. 그래서 런타임이 에이전트에게 던지는 예외를
    더하는 변경은 여기의 기억과 그 원인을 단언하는 테스트를 함께 더한다. 트레이스백을 붙잡는 비용은
    재지 않았고, 실행이 끝나면 버린다.
    """

    def __init__(self) -> None:
        self._thrown: list[tuple[Exception, FailureCause]] = []

    def remember[E: Exception](self, error: E, cause: FailureCause) -> E:
        """던질 예외를 원인과 함께 적고 그대로 돌려준다. 이미 적힌 객체면 처음의 원인이 남는다."""
        if self.cause_of(error) is None:
            self._thrown.append((error, cause))
        return error

    @contextmanager
    def blamed(self, cause: FailureCause) -> Generator[None]:
        """이 안에서 나는 예외를 그 원인으로 적고 그 객체를 그대로 올린다."""
        try:
            yield
        except Exception as error:
            self.remember(error, cause)
            raise

    def cause_of(self, error: BaseException) -> FailureCause | None:
        return next((cause for thrown, cause in self._thrown if thrown is error), None)


def _cause_at(site: _Site, error: Exception, thrown: _Thrown) -> FailureCause:
    """몸통이 받은 실패의 원인. 자리마다 갈래 하나이고 기본 갈래가 없다(`_Site` 의 주석)."""
    match site:
        case "connection":
            return "tool_connection"
        case "agent":
            return thrown.cause_of(error) or "agent_code"
        case "inside" | "write":
            return "other"
        case _:
            assert_never(site)


@dataclass(frozen=True)
class Approve:
    """승인. 멈췄던 도구 호출이 실제로 실행된다."""


@dataclass(frozen=True)
class Deny:
    """거부. 도구를 부르지 않고 사유를 실패한 도구 결과로 모델에 되돌린다(ADR 0009).

    사유가 필수인 것은 ApprovalDenied.reason 이 필수 필드이기 때문이다. 선택으로 두면 채널이 빈
    문자열을 지어내 사유 없는 거부가 기본값으로 굳는다. 승인자를 필수로 만든 논증과 같다.
    """

    reason: str

    def __post_init__(self) -> None:
        """빈 사유는 여기서 막는다. 채널마다 검사하면 다음 채널이 올 때 fail-open 이 다시 열린다."""
        if not self.reason.strip():
            raise ValueError("거부에는 사유가 있어야 한다")


# 승인자가 내린 결정. 게이트가 도구 하나를 판정하는 데 한 번 쓰인다. 거부도 한 번만 쓰이므로,
# 거부 뒤 승인 대상을 또 만나면 다시 멈춘다. 한 번의 거부가 뒤의 것까지 막아 주지 않는다.
type Decision = Approve | Deny


@dataclass(frozen=True)
class _Verdict:
    """결정과 그것이 판정하는 호출. 사람이 승인하거나 거부한 것은 일시정지가 보여 준 그 호출이다.

    그 일시정지는 결정이 자리로 가리킨 것이고, 첫 걸음이 그것이 지금의 일시정지인지 이미 확인했다.
    자리가 없으면 결정은 트레이스 끝의 일시정지에 묶여, 사람이 본 화면이 그것보다 오래될 때 본 적
    없는 호출을 판정한다(ADR 0014 의 2026-09-28 이력).

    재개 뒤 첫 실제 호출이 멈춘 것과 다르면 결정을 적용하지 않고 실패로 끝낸다. 재생 대조는
    기록이 있는 구간만 보므로, 기록 끝 이후에 바뀐 에이전트(다른 도구를 부른다)나 매니페스트(그
    도구가 승인 대상에서 빠졌다)는 여기서 잡는다. 정책이 아니라 호출에 묶여야 "사람이 승인한 것과
    실제로 실행되는 것"이 같다(ADR 0009 와 그 2026-09-22 이력, 티켓 05).
    """

    decision: Decision
    paused: RunPaused


@dataclass(frozen=True)
class _Policy:
    """한 실행의 도구별 가드레일. 마스킹과 승인이 늘 함께 다녀서 한 덩어리다.

    `secrets` 와 `approvals` 는 매니페스트가 정한 것이고, `rules` 는 준비할 때 읽은 운영자의 규칙
    파일이다. `agent` 는 그 규칙의 에이전트 표를 고르는 이름이다. 셋을 한 덩어리로 들어 컨텍스트가
    적용 규칙을 내는 한 자리(`_Context._rule_of`)에서 모델 목록 거르기와 게이트가 같은 값을 쓴다.
    """

    secrets: Mapping[str, tuple[str, ...]]
    approvals: frozenset[str]
    rules: Rules
    agent: PluginName


@dataclass(frozen=True)
class _Limits:
    """이 실행에 걸린 두 끝(ADR 0052). 없음을 읽는 것은 core 의 몫이라 여기서 푼다.

    `turns` 는 매니페스트의 `max_turns` 이고 없으면 core 의 `MAX_TURNS` 다. `tool_calls` 는
    매니페스트의 `max_tool_calls` 이고 없으면 끝이 없다(없음). 재개도 준비를 다시 지나므로 멈춘 사이
    고친 값으로 돈다.
    """

    turns: int
    tool_calls: int | None


@dataclass(frozen=True)
class _Prepared:
    """실행 식별자가 생기기 전에 확정되는 것. run() 과 resume() 이 같은 준비를 거친다."""

    servers: Mapping[PluginName, McpServer]
    policy: _Policy
    instance: BaseAgent
    model: ChatModel
    skills: tuple[Skill, ...]
    limits: _Limits


# 에이전트 태스크가 몸통에 울리는 초인종은 다음을 청하는 신호(`anyio.Event`) 하나다. 이벤트는 싣지
# 않는다 — 컨텍스트의 `_pending` 에 있고 몸통이 꺼낸다. 흐름에 실은 항목은 받는 쪽이 깨어나기 전에
# asyncio 의 날 취소로 끝나면 사라지지만, 줄에 남은 이벤트는 몸통이 끝날 때의 정리(`_attend` 의
# finally)가 받는다(ADR 0039 의 거부한 안 넷째). 끝남은 초인종 줄을 닫는 것이다.
type _Ring = anyio.Event


class _AgentTask:
    """몸통이 띄운 에이전트 태스크. 에이전트의 몫을 돌리고 끝나면 초인종 줄을 닫는다.

    취소가 아닌 예외는 붙잡아 그 객체 그대로 `error` 에 든다. 몸통이 태스크 그룹 밖에서 다시
    던지므로 런타임이 던진 예외의 동일성 판정(`_Thrown`)이 그대로 서고, 일시정지 신호도 이 길로
    몸통에 닿는다. 그룹 안에서 빠져나가면 anyio 가 예외 그룹으로 감싸 받는 자리의 타입 판정이
    깨진다. 취소는 붙잡지 않는다 — 그룹을 취소한 쪽의 것이다.
    """

    def __init__(
        self, feed: Callable[[], Awaitable[None]], bell: MemoryObjectSendStream[_Ring]
    ) -> None:
        self._feed = feed
        self._bell = bell
        self.error: BaseException | None = None

    async def run(self) -> None:
        async with self._bell:
            try:
                await self._feed()
            except anyio.get_cancelled_exc_class():
                raise
            except BaseException as error:
                self.error = error


class _Paused(BaseException):
    """게이트가 실행을 멈추는 신호. 에이전트의 제너레이터를 지나 실행 조립부까지 올라간다.

    Exception 이 아닌 이유는 플러그인이 `except Exception` 으로 삼키면 가드레일이 아니기 때문이다.
    에이전트 코드는 신뢰 경계 밖이다. 그래도 삼키면 컨텍스트가 그 뒤의 어떤 호출도 하지 않는다.
    """


def _mask(
    tool: str, args: Mapping[str, Json], secrets: Mapping[str, tuple[str, ...]]
) -> Mapping[str, Json]:
    """선언된 인자를 가려 이벤트에 담는다. 실제 도구 호출에는 진짜 값이 그대로 간다.

    마스킹하는 자리가 core 이고 트레이스 어댑터가 아닌 이유는, 원칙 V 가 금하는 것이 파일이
    아니라 이벤트이고 secret_args 를 아는 것도 core 이기 때문이다(ADR 0009).
    """
    names = secrets.get(tool, ())
    if not names:
        return args
    return {key: MASKED if key in names else value for key, value in args.items()}


def _reject_masked_args(
    tool: str, args: Mapping[str, Json], secrets: Mapping[str, tuple[str, ...]]
) -> None:
    """마스킹된 값이 실제 도구에 가려는 것을 막는다. 재생이 만드는 유일한 새 노출이다.

    ADR 0009 는 "재생 구간에서 도구 인자는 쓰이지 않고 결과만 필요하다"고 보았지만, 한 모델 턴에
    승인 대상 뒤로 마스킹된 도구가 오면 그 호출은 재개 뒤 실제로 실행되고 인자는 재생된 모델
    응답에서 온 마스킹된 값이다. 조용히 망가진 호출을 보내느니 실패로 끝낸다.
    """
    leaked = [name for name in secrets.get(tool, ()) if args.get(name) == MASKED]
    if leaked:
        raise ValueError(f"마스킹된 인자를 실제 도구에 보낼 수 없다: {tool} 의 {', '.join(leaked)}")


class _Context:
    """AgentContext 를 시그니처로 만족한다. 루프 안에서 생긴 이벤트를 순서대로 쌓아 둔다.

    도구 호출은 루프에서 오든 에이전트가 직접 부르든 _call 하나를 지나고, 모델 호출은 _ask 하나를
    지난다. 게이트, 마스킹, 기록, 재생이 그 두 자리에 있어서 경로를 바꿔 빠져나갈 수 없다(ADR 0009).
    """

    def __init__(
        self,
        started: RunStarted,
        clock: Clock,
        model: ChatModel,
        tools: ToolConnection,
        policy: _Policy,
        replay: Replay,
        verdict: _Verdict | None,
        conversation: Conversation,
        skills: tuple[Skill, ...],
        thrown: _Thrown,
        limits: _Limits,
    ) -> None:
        self.run_id = started.run_id
        self._thrown = thrown
        self._limits = limits
        # 도구를 부르는 한 자리에 들어온 시도의 수. 실행 하나의 컨텍스트가 처음부터 다시 세므로
        # 재개한 실행에서는 재생된 호출도 처음과 같은 번호로 센다(`_call`).
        self._attempts = 0
        self.conversation = conversation
        self.skills = skills
        self._started_at = started.ts
        self._paused = False
        self._resumed = False
        self._clock = clock
        self._model = model
        self._tools = tools
        self._policy = policy
        self._replay = replay
        self._verdict = verdict
        self._pending: list[Event] = []
        self._bell: MemoryObjectSendStream[_Ring] | None = None

    def bind(self, bell: MemoryObjectSendStream[_Ring]) -> None:
        """몸통이 에이전트 태스크를 띄우기 전에 초인종을 건넨다."""
        self._bell = bell

    def queue(self, event: Event) -> None:
        """에이전트가 낸 이벤트를 런타임 이벤트와 같은 줄에 세운다. 에이전트 태스크가 부른다."""
        self._pending.append(event)

    async def release(self) -> None:
        """쌓인 이벤트가 있으면 몸통을 깨우고, 몸통이 그것을 흘린 뒤 다음을 청할 때까지 기다린다.

        이벤트는 `_pending` 에 남아 있고 몸통이 꺼낸다. 이 자리에서 취소를 받아도 꺼내지 않은 것은
        `_attend` 의 finally 가 흘린다.
        """
        if not self._pending or self._bell is None:
            return
        proceed = anyio.Event()
        await self._bell.send(proceed)
        await proceed.wait()

    @property
    def paused(self) -> bool:
        """조립부가 읽는다. 플러그인이 되돌릴 수 없도록 읽기 전용이다."""
        return self._paused

    @property
    def replaying(self) -> bool:
        """재생 구간인가. 여기서 에이전트가 낸 이벤트는 이미 트레이스에 있어 다시 흘리지 않는다."""
        return self._replay.resuming and not self._resumed

    def now(self) -> datetime:
        """에이전트의 시계. 재개 이벤트 전에는 실행의 시작 시각이다.

        처음 실행 전체가 나중에 재생될 구간이므로 처음부터 고정한다. 그래야 프롬프트에 날짜를
        넣는 평범한 에이전트가 시각 때문에 재개 불가가 되지 않는다(ADR 0009, 사용자 스토리 8).
        시계 읽기를 따로 기록하지 않고도 결정적이다.

        런타임이 자기 이벤트에 찍는 시각은 이것이 아니라 실제 시각이다. 그쪽은 대조 대상이
        아니라 관찰용이고, 얼리면 한 실행의 트레이스가 전부 같은 시각이 되어 쓸모를 잃는다.
        """
        return self._clock.now() if self._resumed else self._started_at

    async def llm(self, prompt: str) -> str:
        """프롬프트와 "첫 턴인가"는 이 호출의 클로저가 들고 있다.

        인스턴스에 두면 에이전트가 llm() 을 겹쳐 부를 때 서로 덮어써 대조가 엉뚱해진다.

        모델에 붙이는 도구 목록은 연결의 목록에서 운영자의 deny 에 맞는 도구를 뺀 것이다. 저자의
        승인 요구와 ask 에 맞는 도구는 그대로 붙는다. 거르는 판정은 게이트와 같은 적용 규칙 함수
        (`_rule_of`)가 내서 두 자리가 다른 판단을 하지 않는다. 목록이 비면 도구 없는 모델을 부른다.

        모델에 도구를 붙이는 것은 루프 밖이지만 모델에 닿는 몫이라 모델 호출의 실패다. 루프
        상한의 예외는 `run_loop` 가 내고, 그 안에서 도는 것은 런타임의 클로저뿐이라 여기서 받은 그
        예외는 언제나 런타임의 것이다.
        """
        self._stay_paused()
        specs = [spec for spec in self._tools.tools() if self._rule_of(spec) != "deny"]
        with self._thrown.blamed("model_call"):
            invoke = model_caller(self._model, specs)
        first = True

        async def ask(messages: Sequence[BaseMessage]) -> AIMessage:
            nonlocal first
            turn, first = prompt if first else "", False
            return await self._ask(invoke, messages, turn)

        try:
            return await run_loop(ask, prompt, call=self._call, max_turns=self._limits.turns)
        except LoopLimitExceeded as error:
            self._thrown.remember(error, "loop_limit")
            raise

    async def tool(self, name: str, **args: Json) -> str:
        """도구가 ok=false 를 돌려주든 예외를 던지든 거부됐든 에이전트에게는 같은 ToolError 다."""
        result = await self._call(name, args)
        if not result.ok:
            raise self._thrown.remember(ToolError(result.content), "tool_failure")
        return result.content

    def take_events(self) -> list[Event]:
        """쌓인 이벤트를 비우며 돌려준다. 호출 안의 이벤트가 에이전트의 다음 이벤트보다 앞선다."""
        taken, self._pending = self._pending, []
        return taken

    def replay_event(self, event: Event) -> None:
        """재생 구간에서 에이전트가 낸 이벤트를 기록과 맞춰 소비한다. 조립부가 부른다.

        몸통이 에이전트 밖에서 내는 실패이지만 어긋남은 재개 대조다.
        """
        with self._thrown.blamed("resume_mismatch"):
            self._replay.take_agent_event(event)

    async def _ask(
        self, invoke: ModelCaller, messages: Sequence[BaseMessage], prompt: str
    ) -> AIMessage:
        """모델 한 턴. 재생 구간이면 기록을 되살리고 포트를 건드리지 않는다.

        prompt 는 루프의 첫 턴에만 차 있고 둘째 턴부터는 빈 문자열이다. 둘째 턴부터의 입력은
        기록에서 파생되므로 같은 값을 턴마다 되풀이해 적지 않는다(ADR 0009 의 2026-09-22 이력).
        """
        with self._thrown.blamed("resume_mismatch"):
            replayed = self._replay.take_model(prompt)
        if replayed is not None:
            return message_from(replayed)
        if self._verdict is not None:
            mismatch = Mismatch(
                f"멈춘 도구 호출 {self._verdict.paused.tool} 대신 모델을 부르려 했다. "
                "에이전트가 바뀌었다"
            )
            raise self._thrown.remember(mismatch, "resume_mismatch")
        self._resume()
        await self.release()
        with self._thrown.blamed("model_call"):
            message = await invoke(messages)
            self._record_model_call(reply_from(message), prompt)
        await self.release()
        return message

    async def _call(self, name: str, args: Mapping[str, Json]) -> ToolResult:
        """도구 하나. 재생 구간이면 기록된 결과를 돌려주고 게이트도 지나지 않는다.

        재생 구간에서 게이트를 다시 걸지 않는 이유는, 기록된 성공 또는 실패 결과를 돌려주고 도구를
        다시 부르지 않기 때문이다. 거부된 호출도 실패로 기록되어 같은 길로 되살아난다. 재생이 끝난
        뒤 첫 실제 호출은 멈췄던 그 호출이어야 하고, 결정은 그 호출에만 적용된다.

        대조가 소비보다 앞이다. Mismatch 는 Exception 이라 에이전트가 삼키고 다시 부를 수 있는데,
        먼저 소비하면 그때 결정이 사라져 거부한 호출이 정책이 풀린 도구로 실행될 수 있다.

        셈은 이 자리의 맨 앞, 실행이 이미 멈췄는지를 본 바로 뒤이자 재생된 기록을 찾기 전에 올린다.
        그래서 결말이 무엇이든(성공, 도구의 실패, 연결에 없는 이름, 운영자의 deny, 승인자의 거부, 끝
        넘음) 시도 하나가 한 번이고, 재생된 호출도 처음과 같은 번호로 다시 세어지며, 멈춘 호출은
        재개 뒤 같은 번호로 한 번만 세어진다. 이미 멈춘 실행에서 더 부른 호출은 세지 않는다(ADR
        0052).

        재생이 끝난 뒤의 차례는 다음과 같다(ADR 0044 "집행의 차례").
        0. 도구 호출의 끝(`max_tool_calls`)을 넘은 번호면 이름도 규칙도 보지 않고 거부한다. 결정이
           있었으면 이미 소비되어 버려졌고 승인이어도 부르지 않는다. 승인 대상이어도 멈추지 않아서
           질문한 사람이 쓸모없는 승인을 하지 않는다. 재생된 호출은 이 판정을 지나지 않는다 —
           재생은 기록을 되살리는 것이고 다시 판정하는 것이 아니다. `rule` 은 비운다(규칙이 정한
           것이 아니다). 끝을 적지 않은 에이전트는 이 판정을 지나지 않는다.
        1. 연결 목록에 없는 이름이면 게이트에 들지 않고 거부한다(`rule` 없음). 결정이 있었으면 이미
           소비되어 버려졌다.
        2. 운영자의 deny 에 맞으면 부르지 않고 거부한다. 결정이 있어도 같다 — 승인자가 승인해도
           멈춘 사이 deny 가 된 도구는 불리지 않는다.
        3. 저자의 승인 요구, 운영자의 ask, 적힌 규칙 없음이면 결정이 없을 때 멈춘다. 결정이 있으면
           승인은 부르고 거부는 부르지 않는다.
        4. 운영자의 allow 이면 결정이 없을 때 묻지 않고 부른다. 결정이 있으면(멈춘 사이 ask 가
           allow 로 바뀐 재개) 3 과 같이 결정을 적용한다.
        결정이 적용된 호출의 `rule` 은 그 호출을 멈춘 `run_paused.rule` 이다.
        """
        self._stay_paused()
        self._attempts += 1
        masked = _mask(name, args, self._policy.secrets)
        with self._thrown.blamed("resume_mismatch"):
            replayed = self._replay.take_tool(name, masked)
        if replayed is not None:
            return ToolResult(ok=replayed.ok, content=replayed.content)
        spec = self._connected_spec(name)
        if self._verdict is not None:
            with self._thrown.blamed("resume_mismatch"):
                _require_paused_call(self._verdict.paused, name, masked, spec)
        verdict = self._take_verdict()
        self._resume()
        ceiling = self._limits.tool_calls
        if ceiling is not None and self._attempts > ceiling:
            return await self._refuse(
                name,
                masked,
                f"도구 호출 횟수를 넘었다: 이 실행은 도구를 {ceiling}번까지 부른다",
                rule=None,
            )
        if spec is None:
            return await self._refuse(name, masked, f"도구가 없다: {name}", rule=None)
        rule = self._rule_of(spec)
        if rule == "deny":
            return await self._refuse(
                name, masked, f"운영자가 거부했다: {spec.server}:{name}", rule="deny"
            )
        recorded = rule
        if verdict is None:
            if rule != "allow":
                self._pause(name, masked, rule, spec.server)
        else:
            # 결정의 종류마다 갈래가 있어야 한다. 폴스루로 승인하면 새 결정이 조용히 승인으로 돈다.
            # 이 기능 전에 멈춘 기록에는 까닭 칸이 없다. 그때 멈추는 까닭은 저자의 승인 요구
            # 하나뿐이었다.
            recorded = verdict.paused.rule or "requires_approval"
            match verdict.decision:
                case Deny(reason=reason):
                    return await self._refuse(
                        name, masked, f"승인자가 거부했다: {reason}", rule=recorded
                    )
                case Approve():
                    pass
                case _:
                    assert_never(verdict.decision)
        await self.release()
        with self._thrown.blamed("resume_mismatch"):
            _reject_masked_args(name, args, self._policy.secrets)
        result = await _call_safely(self._tools, name, args)
        self._record_tool_call(name, masked, result, recorded)
        await self.release()
        return result

    def _take_verdict(self) -> _Verdict | None:
        """결정 하나는 도구 하나만 판정한다. 그래서 둘째 승인 대상에서 다시 멈춘다."""
        verdict, self._verdict = self._verdict, None
        return verdict

    def _connected_spec(self, name: str) -> ToolSpec | None:
        """연결 목록의 그 이름의 명세(질의). 없으면 연결에 없는 이름이다."""
        return next((spec for spec in self._tools.tools() if spec.name == name), None)

    def _rule_of(self, spec: ToolSpec) -> AppliedRule:
        """그 도구에 적용되는 규칙 하나(질의). 모델 목록 거르기와 게이트가 이 한 자리를 쓴다.

        차례와 표의 합집합은 `applied_rule` 이 소유한다. 여기서 정하는 것은 입력뿐이다 — 도구를 낸
        서버는 연결이 낸 명세에서, 저자의 승인 요구는 이 실행의 매니페스트에서 온다.
        """
        policy = self._policy
        return applied_rule(
            policy.rules,
            agent=policy.agent,
            server=spec.server,
            tool=spec.name,
            requires_approval=spec.name in policy.approvals,
        )

    async def _refuse(
        self, name: str, masked: Mapping[str, Json], content: str, *, rule: AppliedRule | None
    ) -> ToolResult:
        """거부는 실행을 끝내지 않는다. 도구를 부르지 않은 채 실패한 결과로 기록해 돌려준다.

        이미 있는 도구 실패 경로 그대로다. 루프는 사유를 모델에 되돌려 계속하고, 직접 부른
        에이전트는 ToolError 로 받아 이름으로 잡는다(ADR 0009). 기록이 남으므로 다음 재생에서도
        이 호출은 실패로 되살아나고 실제로 불리지 않는다. 뒤의 승인이 앞의 거부를 뒤집지 않는다.
        거부의 주인은 넷이다 — 승인자, 운영자의 deny, 연결에 없는 이름, 도구 호출의 끝 넘음. 문구와
        `rule` 이 가른다. 뒤의 둘은 `rule` 이 비어 있고 문구의 머리(`도구가 없다`, `도구 호출 횟수를
        넘었다`)가 가른다.
        """
        result = ToolResult(ok=False, content=content)
        self._record_tool_call(name, masked, result, rule)
        await self.release()
        return result

    def _resume(self) -> None:
        """재생 구간이 끝나는 자리. 실제 실행은 여기서부터이고 시계도 여기서 움직인다."""
        if self._resumed or not self._replay.resuming:
            return
        self._resumed = True
        self._pending.append(RunResumed(run_id=self.run_id, ts=self._clock.now()))

    def _pause(
        self, name: str, masked: Mapping[str, Json], rule: AppliedRule, server: PluginName
    ) -> NoReturn:
        """도구를 부르지 않은 채 일시정지를 기록하고 실행을 끝낸다.

        까닭(`rule`)과 멈춘 도구의 서버를 일시정지에 싣는다. 재개가 결정을 적용한 호출의 `rule` 을
        이 까닭으로 기록하고, 승인자는 그 칸으로 왜 물었는지 본다(ADR 0044 "기록").
        """
        self._pending.append(
            RunPaused(
                run_id=self.run_id,
                ts=self._clock.now(),
                tool=name,
                args=masked,
                rule=rule,
                server=server,
            )
        )
        self._paused = True
        raise _Paused()

    def _stay_paused(self) -> None:
        """멈춘 뒤에는 모델도 도구도 부르지 않는다. 신호를 삼킨 에이전트가 이어 가지 못하게."""
        if self._paused:
            raise _Paused()

    def _record_model_call(self, reply: ModelReply, prompt: str) -> None:
        self._pending.append(
            LlmCalled(
                run_id=self.run_id,
                ts=self._clock.now(),
                model=reply.model,
                input_tokens=reply.input_tokens,
                output_tokens=reply.output_tokens,
                prompt=prompt,
                text=reply.text,
                tool_calls=tuple(
                    ToolCall(
                        id=call.id,
                        name=call.name,
                        args=_mask(call.name, call.args, self._policy.secrets),
                    )
                    for call in reply.tool_calls
                ),
            )
        )

    def _record_tool_call(
        self,
        name: str,
        masked: Mapping[str, Json],
        result: ToolResult,
        rule: AppliedRule | None,
    ) -> None:
        """`rule` 은 그 호출을 정한 규칙이다. 연결에 없는 이름은 정한 규칙이 없어 없음이다."""
        self._pending.append(
            ToolCalled(
                run_id=self.run_id,
                ts=self._clock.now(),
                tool=name,
                ok=result.ok,
                args=masked,
                content=result.content,
                rule=rule,
            )
        )


async def run(
    agent: AgentName,
    request: str,
    principal: Principal,
    *,
    previous_run: RunId | None = None,
    visible_agents: frozenset[AgentName] | None = None,
    timeout_seconds: float | None = None,
    default_model: PluginName,
    plugins: PluginSource,
    models: ModelSource,
    tools: ToolSource,
    trace: TraceStore,
    clock: Clock,
) -> AsyncIterator[Event]:
    """새 실행 하나. `previous_run` 을 주면 그 끝난 실행을 이어 간다(ADR 0022).

    `default_model` 은 에이전트가 매니페스트에 `model` 을 적지 않았을 때 쓰는 모델 플러그인의
    이름이다 (ADR 0040). 필수 키워드 인자이고 core 는 이름을 짓지 않는다. 이름의 문자 집합은 부르는
    쪽(조립)이 `is_plugin_name` 으로 걸러 감싼다. 모델은 준비마다 모델 소스가 그 이름의 매니페스트로
    새로 만든다(`_prepare`).

    이어 가기의 판정은 준비보다 앞이다 — 앞 실행(없음 → 손상 → 다른 주체 → 끝나지 않음), 고리,
    그다음 준비(부재 → 깨짐 → 꺼짐 → import → 모델 만들기). 재개가 트레이스 판정을 준비보다 앞에
    두는 것과 같은 모양이고, 꺼진 에이전트로 이어 가려는 요청도 고리를 다 읽은 뒤에 거절되는 비용이
    있다. 전부 실행 식별자를 만들기 전이라 거절된 이어 가기는 트레이스를 남기지 않는다. 이어 가기의
    판정 전부(앞 실행과 고리)는 한 번의 스레드 호출로 이벤트 루프 밖에서 돌아 긴 고리가 루프를 막지
    않고, 판정 순서와 예외는 그대로 올라온다. 취소가 오면 그 읽기가 끝나기를 기다린다(anyio 의
    기본값). 그 시간은 실행 타임아웃 밖이고 읽기 상한(`READ_CAP`)이 묶는다. 재개의 거슬러 읽기는
    루프 위에 남는다 (`.claude/rules/core.md` 의 이어 가기 항목, end-user-continuation 명세 "거슬러
    읽기의 상한과 자리").

    `visible_agents` 는 호출자가 볼 수 있는 에이전트의 집합이고 없음은 전부다(ADR 0023 의
    2026-10-05 이력). 최종 사용자 경로가 그 사이트의 열 에이전트 목록을 넘긴다. 요청이 댄 에이전트가
    집합 밖이면 없는 에이전트와 글자 그대로 같은 `Absent` 이고 매니페스트를 읽기 전이다 — 목록
    밖인지 꺼졌는지 있는지가 드러나지 않는다. 이어 가기에서도 요청한 에이전트만 본다. 앞 실행의
    에이전트가 집합 밖이어도 그 교환은 어차피 넘어가지 않는다(ADR 0022).

    `timeout_seconds` 는 시작 이벤트를 쓴 뒤 결말까지의 시간(초)이고 없음은
    `DEFAULT_RUN_TIMEOUT_SECONDS` 다. 운영자 채널과 최종 사용자 경로는 `serve` 가 받은 값을, CLI 는
    없음을 넘긴다. 범위와 실패 정책은 모듈 독스트링이다.
    """
    continued = (
        None
        if previous_run is None
        else await anyio.to_thread.run_sync(gather_continued, trace, previous_run, agent, principal)
    )
    if visible_agents is not None and agent not in visible_agents:
        raise Absent(_no_agent(agent))
    manifest = _requested_manifest(plugins, agent)
    prepared = _prepare(plugins, models, manifest, default_model)
    gathered = None if continued is None else continued.gathered
    fold = None if gathered is None else plan_fold(gathered, limit_of(manifest))
    run_id = clock.new_run_id()
    started = RunStarted(
        run_id=run_id,
        ts=clock.now(),
        agent=agent,
        request=request,
        principal=principal,
        previous_run=previous_run,
        shortcuts={} if continued is None else continued.shortcuts,
    )
    trace.write(started)
    yield started
    if fold is not None:
        conversation: Conversation | Fold = fold
    else:
        conversation = NEW_CONVERSATION if gathered is None else gathered.conversation()
    body = _Body(
        prepared,
        started,
        replay=Replay.nothing(),
        verdict=None,
        conversation=conversation,
        tools=tools,
        trace=trace,
        clock=clock,
    )
    seconds = _timeout_of(timeout_seconds)
    with anyio.move_on_after(seconds) as deadline:
        # 몸통을 이 자리에서 닫는다. 소비자가 스트림을 닫으면 그 예외가 이 yield 에 드는데, 몸통이
        # 태스크 그룹 안의 yield 에 멈춘 채 남으면 기한의 범위를 나가는 자리에서 anyio 가 거부한다.
        async with aclosing(body.events()) as events:
            async for event in events:
                yield event
    if deadline.cancelled_caught:
        failure = body.deadline_failure(seconds)
        if failure is not None:
            trace.write(failure)
            yield failure


async def resume(
    run_id: RunId,
    pause_index: int,
    decision: Decision,
    approver: Principal,
    *,
    visible_agents: frozenset[AgentName] | None = None,
    timeout_seconds: float | None = None,
    default_model: PluginName,
    plugins: PluginSource,
    models: ModelSource,
    tools: ToolSource,
    trace: TraceStore,
    clock: Clock,
) -> AsyncIterator[Event]:
    """같은 실행을 이어 간다. 새 실행이 아니라 run_id 도 트레이스 파일도 하나다.

    모델은 기록된 에이전트의 매니페스트를 지금 디스크에서 읽어 `run()` 과 같은 순서의 준비로 새로
    만든다. 그래서 멈춘 사이 모델 파일을 고치거나 모델을 껐으면 재개가 그것을 듣는다(ADR 0040).
    만들기도 첫 걸음 안이라 모델 소스의 메서드가 동기다.

    에이전트 이름과 요청은 트레이스의 시작 이벤트에서 읽는다. 결정이 트레이스에 먼저 기록된 뒤
    재생이 시작되므로, 재생이 무엇을 하든 누가 허락했는지, 누가 왜 막았는지는 남는다.

    `pause_index` 는 결정이 답하는 `run_paused` 가 트레이스에서 서는 0부터 센 자리다(ADR 0014 의
    2026-09-28 이력). 결정 값(`Approve`·`Deny`)이 아니라 따로 받는 이유는 그것이 결정의 내용이
    아니라 결정이 답하는 일시정지를 가리키는 주소라서다. 실행 식별자와 함께 "어느 실행의 어느
    일시정지"를 이루고, 게이트는 그것을 쓰지 않는다. 기본값이 없다 — 있으면 그 값이 곧 지금의
    일시정지라 오래된 결정이 승인자가 본 적 없는 호출을 실행한다(fail-open, ADR 0011 의 논증).

    첫 걸음(트레이스 읽기, 일시정지와 자리 확인, 결정 쓰기)에 await 가 없다. 같은 실행에 동시에 온
    둘째 결정이 마지막 이벤트를 결정으로 읽어 재개 불가가 되는 것이 이것 하나에 기댄다(ADR 0014).
    읽기나 쓰기를 비동기로 바꾸거나 스레드로 보내면 승인된 도구가 두 번 실행된다. HTTP 채널의 동시
    재개 테스트가 그것을 고정한다. 둘 사이의 준비(꺼진 집합 읽기를 포함한다)도 첫 걸음 안이라 포트의
    그 읽기가 동기다(ADR 0017). 준비에서 막히면 결정을 쓰기 전이라 실행은 일시정지 그대로다.

    이어 간 실행의 재개는 시작 이벤트의 앞 실행에서 다시 거슬러 읽어 처음과 같은 멤버를 준다(ADR
    0022). 그것도 첫 걸음 안이고 트레이스 판정 뒤, 준비 앞이다. 고리가 깨졌으면 결정 이벤트를 쓰기
    전에 PluginError 라 실행은 일시정지 그대로다 — 멈춘 사이 거슬러 읽는 범위의 트레이스를 지우면
    그렇고, 그보다 오래된 트레이스를 지우면 재개가 그대로 선다. 고리의 주체 비교 대상은 멈춘 실행의
    `run_started` 주체다.

    결정은 그 실행의 주체만 내린다(ADR 0009 의 2026-10-03 이력). 승인자가 멈춘 실행의 `run_started`
    주체와 다르면 `DifferentPrincipal` 이고, 트레이스가 가리키는 에이전트가 `visible_agents` 밖이면
    없는 실행과 같은 `Absent` 다. 둘 다 첫 걸음의 자기 실행 읽기(`read_own_run`)가 이미 읽은 값으로
    하고 결정 이벤트를 쓰기 전이다.

    `timeout_seconds` 는 결정 이벤트를 쓴 뒤 결말까지의 시간이고 `run()` 과 같다. 재개마다 처음부터
    센다 — 멈춰 있던 시간도, 멈추기 전에 쓴 시간도 들지 않는다.
    """
    resumption = _read_paused(trace, run_id, pause_index, approver, visible_agents)
    prepared = _prepare(
        plugins, models, _recorded_manifest(plugins, resumption.started), default_model
    )
    decided = _decision_event(run_id, decision, approver, clock)
    trace.write(decided)
    yield decided
    body = _Body(
        prepared,
        resumption.started,
        replay=Replay.of(resumption.records),
        verdict=_Verdict(decision, resumption.paused),
        conversation=resumption.conversation,
        tools=tools,
        trace=trace,
        clock=clock,
    )
    seconds = _timeout_of(timeout_seconds)
    with anyio.move_on_after(seconds) as deadline:
        # 몸통을 이 자리에서 닫는다. 소비자가 스트림을 닫으면 그 예외가 이 yield 에 드는데, 몸통이
        # 태스크 그룹 안의 yield 에 멈춘 채 남으면 기한의 범위를 나가는 자리에서 anyio 가 거부한다.
        async with aclosing(body.events()) as events:
            async for event in events:
                yield event
    if deadline.cancelled_caught:
        failure = body.deadline_failure(seconds)
        if failure is not None:
            trace.write(failure)
            yield failure


class _Body:
    """실행의 몸통. 시작 이벤트(재개에서는 결정 이벤트) 뒤부터 결말까지이고 run() 과 resume() 이
    공유한다.

    이어 가기에서 원문이 글자 수 한도나 교환 수 기준을 넘었으면(`Fold`) 먼저 요약하고, 도구를 연결한
    채 에이전트를 돌리고, 결말을 붙인다. 진입점의 실행 타임아웃이 이것 하나를 감싼다. 기한이 몸통을
    끊으면 진입점은 `deadline_failure` 로 결말이 이미 정해졌는지 묻는다 — 그 판정이 몸통 안에 있는
    이유는 이벤트의 종류로 정할 수 없어서다(아래 `_paused` 의 주석).
    """

    def __init__(
        self,
        prepared: _Prepared,
        started: RunStarted,
        *,
        replay: Replay,
        verdict: _Verdict | None,
        conversation: Conversation | Fold,
        tools: ToolSource,
        trace: TraceStore,
        clock: Clock,
    ) -> None:
        self._prepared = prepared
        self._started = started
        self._replay = replay
        self._verdict = verdict
        self._conversation = conversation
        self._model = prepared.model
        self._tools = tools
        self._trace = trace
        self._clock = clock
        # 런타임이 실제로 게이트에서 멈췄는가. 이벤트 종류로 판정하지 않는 이유는 에이전트가
        # run_paused 를 지어내 yield 할 수 있기 때문이다. 에이전트는 신뢰 경계 밖이다.
        self._paused = False
        # 결말을 썼는가. 몸통이 run_failed 를 썼거나, 런타임이 멈췄거나, 에이전트가 run_finished 를
        # 마지막으로 내고 돌아왔다. 그 뒤에 남는 것은 도구 연결의 정리뿐이고, 그 정리의 예외도
        # 기한도 아무것도 덧붙이지 않는다.
        self._settled = False
        # 쓸 결말을 붙잡았는가. 에이전트 몫의 실패와 선언 확인의 실패를 도구 연결을 닫기 전에
        # 붙잡아, 닫은 뒤에 쓴다. 먼저 붙잡은 것이 이긴다. `_settled` 와 한 표지로 합치지 않는
        # 이유는, 붙잡은 실패를 쓰기 전(닫는 도중)에 기한이 오면 진입점이 시간 초과 대신 이것을 써야
        # 해서다.
        self._held: RunFailed | None = None
        # 런타임이 에이전트에게 던진 예외. 원인을 가르는 데 쓴다(`_Thrown`).
        self._thrown = _Thrown()
        # 몸통이 트레이스에 쓴 마지막 이벤트. 결말 없이 돌아왔는지를 이것으로 본다.
        self._last: Event | None = None

    def deadline_failure(self, seconds: float) -> RunFailed | None:
        """기한이 몸통을 끊은 실행의 결말(질의). 결말을 이미 썼으면 없음이다.

        결말을 쓴 뒤 도구 연결을 닫는 데 기한이 지난 것은 실행이 시간 안에 끝나지 않은 것이
        아니다 — 범위는 결말까지다. 덧붙이면 결말이 둘이 되고 멈춘 실행은 재개할 수 없게 된다.
        붙잡은 실패가 있으면(그 뒤 닫는 도중에 기한이 왔다) 결말은 그것이다 — 먼저 난 실패가
        결말이다. 에이전트가 결말 모양의 이벤트(지어낸 run_paused, 아직 돌아오지 않은 채 낸
        run_finished)를 낸 뒤에 걸린 것은 결말이 정해지지 않은 것이라 실패로 끝낸다. 몸통의 끝
        판정과 같은 기준이다.
        """
        if self._settled:
            return None
        if self._held is not None:
            return self._held
        error = f"실행이 {seconds:g}초 안에 끝나지 않았다"
        return RunFailed(
            run_id=self._started.run_id, ts=self._clock.now(), error=error, cause="timeout"
        )

    async def events(self) -> AsyncGenerator[Event]:
        """요약(필요하면)과 에이전트의 이벤트와 결말. 런타임이 내는 것은 트레이스에 쓴 뒤에 낸다."""
        conversation = self._conversation
        if isinstance(conversation, Fold):
            run_id = self._started.run_id
            outcome = await _summary_outcome(self._model, conversation, run_id, self._clock)
            yield self._emit(outcome)
            if isinstance(outcome, RunFailed):
                self._settled = True
                return
            conversation = conversation.conversation(outcome.summary)
        async with aclosing(self._drive(conversation)) as driven:
            async for event in driven:
                yield event

    def _emit(self, event: Event) -> Event:
        self._trace.write(event)
        return event

    def _hold(self, error: Exception, site: _Site) -> None:
        """자리에서 받은 실패를 쓸 결말로 붙잡는다. 메시지와 원인이 함께 그 실패의 것이다."""
        self._hold_failure(_describe(error), _cause_at(site, error, self._thrown))

    @contextmanager
    def _holding(self, site: _Site, ctx: _Context | None = None) -> Generator[None]:
        """이 안에서 빠져나온 예외를 그 자리의 실패로 붙잡고 그대로 올린다. 멈춘 실행이면 붙잡지
        않는다 — 신호를 감싸 올린 예외는 실패가 아니다."""
        try:
            yield
        except Exception as error:
            if ctx is None or not ctx.paused:
                self._hold(error, site)
            raise

    def _hold_failure(self, error: str, cause: FailureCause) -> None:
        """먼저 붙잡은 것이 이기고, 결말을 이미 썼으면 붙잡지 않는다 — 뒤따른 실패는 버린다."""
        if self._held is None and not self._settled:
            self._held = RunFailed(
                run_id=self._started.run_id, ts=self._clock.now(), error=error, cause=cause
            )

    def _write_held(self) -> RunFailed | None:
        """붙잡은 결말을 쓴다. 쓸 것이 없거나 이미 썼으면 없음이다. 쓰기가 실패하면 결말
        없음이다."""
        held = self._held
        if held is None or self._settled:
            return None
        self._settled = True
        self._trace.write(held)
        return held

    async def _drive(self, conversation: Conversation) -> AsyncGenerator[Event]:
        """도구를 연결한 채 에이전트를 돌리고 결말을 붙인다."""
        # 안쪽 제너레이터를 여기서 닫는다. 트레이스 쓰기가 실패하면 예외가 이 몸통에서 나고, 그때
        # 안쪽은 도구 연결 안의 yield 에 멈춰 있다. 가비지 수집에 맡기면 다른 태스크가 그것을 닫아
        # MCP 어댑터의 anyio 취소 범위가 깨진다 — 연결은 연 태스크가 닫아야 한다(http-channel 티켓
        # 03).
        async with aclosing(self._connected(conversation)) as executed:
            try:
                async for event in executed:
                    self._last = event
                    yield self._emit(event)
            except Exception as error:
                # 결말 전의 트레이스 쓰기가 실패했다(그 밖). 닫기의 예외는 `_connected` 가 버려
                # 여기 오지 않는다. 붙잡은 실패가 있으면 그것이 먼저다. 멈춘 실행이면 실패한 것은
                # 일시정지까지의 쓰기다 — 일시정지는 쌓인 이벤트의 마지막이라 트레이스에 없고,
                # 결말은 아직 정해지지 않았다.
                if self._paused:
                    self._settled = False
                self._hold(error, "write")
                failed = self._write_held()
                if failed is not None:
                    yield failed
                return
        failed = self._write_held()
        if failed is not None:
            yield failed

    async def _connected(self, conversation: Conversation) -> AsyncGenerator[Event]:
        """도구 연결을 열고 그 안의 몫을 흘린 뒤 닫는다. 실패는 닫기 전에 붙잡혀 있다.

        연결에 들어가는 동안의 예외는 도구 연결이다. 연결 안의 몫이 제 자리 밖의 예외로 끝나면 그
        밖으로 붙잡는다. 그래서 들어간 뒤 연결을 나오며 난 예외는 닫기의 것이고, 그때는 결말을
        붙잡았거나 이미 썼으므로 버린다 — 먼저 난 실패가 결말이다. 닫기가 도는 취소를 다른 예외로
        덮었으면 그 취소를 다시 던진다(기한이 먼저다). 결말을 쓴 뒤의 닫기 실패는 그래서
        트레이스에도 서버 기록에도 흔적이 없다. 채널의 서버 기록 길로
        올리려면 결말을 쓴 뒤 다시 던져야 해 CLI 의 종료 코드와 멈춘 실행의 선례(닫기의 예외를
        버린다)가 갈린다(명세 "먼저 난 실패", PR 직전 리뷰). 상류의 닫기는 서버를 끄는 일을 보호된
        `finally` 에서 먼저 하고 그 뒤에 자기 취소 범위를 나간다(mcp 2.3.0 `client/stdio.py` 의
        `stdio_client`, 코드를 읽었다). 프로브는 닫기를 연 태스크가 아닌 태스크에서 해 범위를 나가는
        자리의 예외를 냈고, 그 예외로 끝난 닫기 뒤에도 서버는 내려갔다
        (`.scratch/mcp-shutdown/spec.md` 의 "결말 뒤 닫기의 예외", 프로브 `close_paths.py` 의
        `close_fails`). core 는 연결을 연 태스크에서 닫으므로 그 길을 밟지 않고, 다른 까닭으로 끝난
        닫기는 재지 않았다.
        """
        try:
            async with self._tools.connect(self._prepared.servers) as connection:
                # 연결 안의 몫을 이 자리에서 닫는다. 몸통이 이것을 닫는 까닭과 같다.
                async with aclosing(self._attend(connection, conversation)) as attended:
                    with self._holding("inside"):
                        async for event in attended:
                            yield event
        except Exception as error:
            # 닫기의 정리 코드가 기한(이나 바깥)의 취소를 다른 예외로 덮었으면 그 취소가 먼저다.
            # 다시 던져 진입점의 범위가 받게 한다 — 삼키면 기한이 닫기의 예외로 읽힌다.
            cancelled = _cancellation_under(error)
            if cancelled is not None:
                raise cancelled from None
            # 그 밖에 들어간 뒤의 예외면 결말을 이미 붙잡았거나 썼으므로 `_hold` 가 버린다.
            self._hold(error, "connection")

    async def _attend(
        self, connection: ToolConnection, conversation: Conversation
    ) -> AsyncGenerator[Event]:
        """연결 안의 몫. 선언을 확인하고 에이전트를 돌리며, 실패해도 그때까지 쌓인 이벤트를 흘린다.

        일시정지는 실패가 아니다. 신호를 여기서 받아 연결을 정상으로 닫고, 쌓인 이벤트의 끝에
        run_paused 가 있다. 에이전트가 신호를 삼키고 이어 가도 그 뒤의 이벤트는 통과시키지 않고,
        신호를 다른 예외로 감싸 올려도 멈춘 실행에 run_failed 가 덧붙지 않는다. 선언 확인의 실패도
        연결 안에서 나므로 에이전트 몫의 실패처럼 붙잡는다 — 그러지 않으면 뒤의 닫기 예외가 빠져나와
        먼저 난 실패가 그 자리에서만 서지 않는다.
        """
        prepared = self._prepared
        try:
            specs = connection.tools()
            _reject_unknown_declarations(prepared.policy, specs)
            _reject_unknown_rule_lines(prepared, specs)
        except Exception as error:
            self._hold(error, "connection")
            return
        ctx = _Context(
            self._started,
            self._clock,
            self._model,
            connection,
            prepared.policy,
            self._replay,
            self._verdict,
            conversation,
            prepared.skills,
            self._thrown,
            prepared.limits,
        )
        try:
            # 중계를 이 자리에서 닫는다. 몸통이 안쪽 제너레이터를 닫는 까닭과 같다.
            async with aclosing(self._relay(prepared.instance, ctx)) as relayed:
                async for event in relayed:
                    yield event
        except _Paused:
            pass
        except Exception as error:
            if not ctx.paused:
                self._hold(error, "agent")
        finally:
            self._paused = ctx.paused
            # 일시정지가 기록되면 결말이 정해진 것이다. 에이전트의 정리 코드(`_closing`)가 기다리는
            # 동안 기한이 와 이 자리를 예외로 지나가도 실패를 덧붙이지 않는다.
            self._settled = self._settled or ctx.paused
            for pending in ctx.take_events():
                yield pending
        # 에이전트의 몫이 끝났다. 여기서부터는 도구 연결의 정리뿐이다. 마지막 이벤트가 run_finished
        # 가 아니면 결말은 실패이고, 붙잡아 두었다가 닫은 뒤에 쓴다.
        finished = isinstance(self._last, RunFinished)
        if not self._paused and not finished:
            self._hold_failure(_NO_FINISH, "agent_code")
        self._settled = self._settled or (finished and self._held is None)

    async def _relay(self, agent: BaseAgent, ctx: _Context) -> AsyncGenerator[Event]:
        """에이전트를 제 태스크에서 돌리고, 초인종이 울릴 때마다 쌓인 이벤트를 흘린다(ADR 0039).

        에이전트 태스크와 몸통은 맞물려 한 번에 한쪽만 움직인다. 에이전트 태스크는 이벤트를 쌓고
        울린 뒤 몸통이 그것을 흘리고 다음을 청할 때까지 기다리고, 몸통은 울림을 기다리는 동안만
        쉰다. 그래서 역압이 그대로이고, 도구를 요청한 모델 호출의 이벤트는 그 도구를 부르기 전에
        트레이스에 쓰인다. 함께 부른 호출(`asyncio.gather`)은 맞물림의 기다림 밖에서 겹쳐 돌아, 그
        호출들 사이에는 이 순서가 서지 않는다.

        몸통 자신의 예외(트레이스 쓰기가 실패해 바깥이 닫으며 넣은 `GeneratorExit`, 소비자가
        스트림을 닫음)는 그룹 안에서 붙잡아 그룹을 취소하고, 에이전트 태스크가 정리를 마치기를
        기다린 뒤 그룹 밖에서 다시 던진다 — 그룹 안에서 나가면 anyio 가 예외 그룹으로 감싼다. 그래서
        버려진 실행의 에이전트는 기다리던 자리에서 취소된다. 몸통의 예외가 에이전트 태스크의 것보다
        먼저다. 남은 이벤트(멈춘 실행의 run_paused 따위)는 `_attend` 의 finally 가 흘린다.
        """
        bell, rings = anyio.create_memory_object_stream[_Ring]()
        ctx.bind(bell)
        task = _AgentTask(lambda: self._feed(agent, ctx), bell)
        failure: BaseException | None = None
        async with anyio.create_task_group() as group, rings:
            group.start_soon(task.run)
            try:
                async for ring in rings:
                    for pending in ctx.take_events():
                        yield pending
                    ring.set()
            except BaseException as error:
                if isinstance(error, anyio.get_cancelled_exc_class()):
                    raise
                group.cancel_scope.cancel()
                failure = error
        if failure is None:
            failure = task.error
        if failure is not None:
            raise failure

    async def _feed(self, agent: BaseAgent, ctx: _Context) -> None:
        """에이전트가 낸 이벤트를 줄에 세우고 몸통을 깨운다. 호출 안의 이벤트는 컨텍스트가 기록하는
        자리에서 같은 줄에 세우고 그 뒤의 `release()` 가 깨운다. 일시정지(`_pause`)는 깨우지 않고
        신호를 던지며, 세워 둔 `run_paused` 는 `_attend` 의 finally 가 흘린다.

        일시정지가 기록되면 에이전트가 신호를 삼키고 이어 가도 그 뒤의 이벤트를 통과시키지 않는다.
        재생 구간에서 에이전트가 낸 이벤트는 기록과 맞춰 소비하고 흘리지 않는다.
        """
        run_id = self._started.run_id
        async with _closing(agent.run(self._started.request, ctx)) as from_agent:
            # 에이전트를 닫기 전에 붙잡는다. 닫기가 에이전트의 정리 코드를 기다리는 동안 기한이 와도
            # 먼저 난 실패가 결말이다 — 도구 연결의 닫기와 같은 기준이다.
            with self._holding("agent", ctx):
                async for event in from_agent:
                    if ctx.paused:
                        return
                    _reject_stray(event)
                    _reject_runtime_only(event, run_id)
                    if ctx.replaying:
                        ctx.replay_event(event)
                        continue
                    ctx.queue(event)
                    await ctx.release()


@asynccontextmanager
async def _closing(events: AsyncIterator[Event]) -> AsyncGenerator[AsyncIterator[Event]]:
    """에이전트가 낸 이벤트의 순회. 나올 때 에이전트의 제너레이터를 그 자리에서 닫는다.

    런타임이 그 순회 안에서 예외를 던지거나 일시정지로 빠져나가면 제너레이터는 yield 에 멈춘 채
    남고, 가비지 수집이 나중에 다른 태스크에서 그것을 닫는다(PEP 525) — 에이전트가 anyio 취소
    범위를 쥐고 있으면 그 자리에서 깨진다. 몸통이 안쪽 제너레이터를 `aclosing` 으로 닫는 까닭과
    같다. sdk 의 `BaseAgent.run` 은 `AsyncIterator` 를 돌려준다고만 약속하므로 닫을 것이 있는
    제너레이터일 때만 닫는다.

    먼저 난 것이 이긴다. 런타임이 실패를 들고 나오는 중에 에이전트의 정리 코드가 다른 예외를
    내면(`finally` 의 예외, `GeneratorExit` 을 잡고 다시 yield) 그 예외는 뒤따른 것이라 버린다 —
    덮으면 실패의 메시지가 그 정리 코드의 것이 된다. 취소와 일시정지 신호는 `Exception` 이 아니라
    버리지 않는다. 못 보는 것: 정리 코드가 승인 대상을 부르면 게이트가 그 자리에서 일시정지를
    기록하므로, 들고 나오던 실패가 있어도 실행은 멈춘 채 끝난다(재개하면 그 실패의 자리에서 다시
    실패한다).
    """
    try:
        yield events
    except BaseException:
        if isinstance(events, AsyncGenerator):
            with suppress(Exception):
                await events.aclose()
        raise
    else:
        if isinstance(events, AsyncGenerator):
            await events.aclose()


def _reject_stray(value: object) -> None:
    """에이전트가 sdk 의 이벤트가 아닌 값을 냈으면 쓰기 전에 실패로 끝낸다(에이전트 코드).

    sdk 의 시그니처는 이벤트만 허락하지만 플러그인은 로더를 지나 타입 검사 밖에서 온다. 여기서 보지
    않으면 그 값은 트레이스 쓰기에서 터져 결말 전 쓰기의 실패(그 밖)와 갈리지 않는다. 인자가
    `object` 인 것은 이벤트로 적힌 값을 다시 보는 검사가 타입 검사에서 쓸모없는 검사로 보이지 않게
    하려는 것이다.
    """
    if not isinstance(value, _EVENT_KINDS):
        raise TypeError(f"에이전트가 sdk 의 이벤트가 아닌 값을 냈다: {type(value).__name__}")


def _reject_runtime_only(event: Event, run_id: RunId) -> None:
    """에이전트가 낸 이벤트가 런타임만 내는 종류면 실패로 끝낸다. 재생 구간에서도 같다.

    대화 요약은 다음 실행의 거슬러 읽기가 트레이스에서 읽는 입력이라, 에이전트가 지어낸 것이
    통과하면 런타임의 것과 가를 수 없고 그 실행을 지나는 모든 이어 가기가 영구히 깨진다(ADR 0022).
    실패는 결말이라 런타임이 쓰는 하나여야 하고, 원인이 든 실패는 런타임만 낸다(ADR 0031). 원인 없는
    것도 통과시키지 않는다 — 통과시키면 그 뒤 결말 없이 돌아온 에이전트에 런타임이 실패를 하나 더 써
    실패가 둘이 되고, 그 뒤 끝남을 내면 실패를 보인 실행이 끝남이 된다. 메시지는 에이전트가 적은
    글을 든다. 실패하려는 에이전트는 예외를 던지면 같은 결과를 얻는다.

    도구 호출과 일시정지의 적용 규칙·서버 칸(`tool_called.rule`, `run_paused.rule`,
    `run_paused.server`) 은 런타임만 쓴다. 에이전트의 기록이 운영자의 규칙을 사칭하면 트레이스를
    읽는 운영자가 가를 수 없기 때문이다(ADR 0044). 칸이 비어 있는 이벤트는 지금처럼 통과한다. 칸을
    채운 `run_paused` 는 지어낸 일시정지를 멈춘 것으로 치지 않는 길보다 먼저 여기서 끝난다.
    에이전트가 채운 칸이 트레이스에 남으면 그 트레이스의 재개가 재생 구간에서 `agent_code` 로
    끝나므로 쓰기 전에 막는다.
    """
    match event:
        case ConversationSummarized():
            raise RuntimeError(f"에이전트는 대화 요약 이벤트를 낼 수 없다: {run_id}")
        case RunFailed(error=error):
            raise RuntimeError(f"에이전트는 실패 이벤트를 낼 수 없다: {error}")
        case ToolCalled(rule=rule) if rule is not None:
            raise RuntimeError(f"에이전트는 tool_called 의 rule 칸을 채울 수 없다: {event.tool}")
        case RunPaused(rule=rule) if rule is not None:
            raise RuntimeError(f"에이전트는 run_paused 의 rule 칸을 채울 수 없다: {event.tool}")
        case RunPaused(server=server) if server is not None:
            raise RuntimeError(f"에이전트는 run_paused 의 server 칸을 채울 수 없다: {event.tool}")
        case _:
            return


async def _summary_outcome(
    model: ChatModel, fold: Fold, run_id: RunId, clock: Clock
) -> ConversationSummarized | RunFailed:
    """요약 이벤트, 또는 요약이 실패한 실행의 결말. 에이전트를 부르기 전, 시작 이벤트 바로 뒤다.

    실패(모델 예외, 빈 요약 글)는 요약 이벤트 없이 run_failed 이고 도구도 연결하지 않는다. 다시
    시도하지도 원문으로 진행하지도 않는다 — 같은 앞 실행으로 다시 이어 가는 것이 곧 다시 시도다
    (ADR 0022, core/continuation.py).
    """
    try:
        return await summarize(model, fold, run_id, clock)
    except Exception as error:
        return RunFailed(
            run_id=run_id,
            ts=clock.now(),
            error=f"대화 요약이 실패했다: {_describe(error)}",
            cause="conversation_summary",
        )


def _timeout_of(timeout_seconds: float | None) -> float:
    """받은 타임아웃, 없으면 core 의 기본값. 상수를 부를 때 읽는다."""
    return DEFAULT_RUN_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds


def _decision_event(
    run_id: RunId, decision: Decision, approver: Principal, clock: Clock
) -> ApprovalGranted | ApprovalDenied:
    """결정을 트레이스에 남는 이벤트로. 승인과 거부가 별도 클래스인 이유는 sdk 의 events.py."""
    match decision:
        case Deny(reason=reason):
            return ApprovalDenied(run_id=run_id, ts=clock.now(), approver=approver, reason=reason)
        case Approve():
            return ApprovalGranted(run_id=run_id, ts=clock.now(), approver=approver)
        case _:
            assert_never(decision)


def _prepare(
    plugins: PluginSource,
    models: ModelSource,
    manifest: PluginManifest,
    default_model: PluginName,
) -> _Prepared:
    """실행 식별자가 생기기 전에 끝나는 검사들. 여기서 나는 오류는 트레이스가 없다.

    에이전트의 매니페스트는 부르는 쪽이 읽어 넘긴다. 없을 때의 뜻이 `run()` 과 `resume()` 에서
    다르기 때문이다(`_requested_manifest`, `_recorded_manifest`).

    순서가 의도다. 깨짐(턴의 끝이 10을 넘음. 에이전트 매니페스트만으로 판정되어 맨 앞이다 — 부재
    다음이고 mcp 의 깨짐보다 앞이며 꺼진 에이전트여도 먼저 난다(ADR 0052). mcp 들, 마스킹과 승인의
    충돌, 모델의 없음과 읽히지 않음, 스킬의 없음과 읽히지 않음, 운영자 파일의 손상. 규칙 파일을 꺼진
    집합보다 먼저 읽는다. 마스킹과 묻는 규칙의 충돌은 규칙 파일을 읽은 뒤에 보므로 이 묶음에서
    마지막이다)을 다 본 뒤에 꺼짐(에이전트, mcp, 모델, 스킬)을 보고, 진입점 import 는 꺼짐보다 뒤,
    모델 만들기는 import 뒤다. 깨진 것이 먼저 보여야 운영자가 다시 켜기 전에
    고칠 것을 알고, import 실패를 판정하려면 플러그인 코드를 실행해야 하는데 꺼진 에이전트는 그
    코드를 돌리지 않는다(ADR 0017, plugin-toggle 명세의 "core — 준비 단계의 판정"). 깨짐과 꺼짐이
    같은 순서(에이전트 → mcp → 모델 → 스킬) 하나다(ADR 0040, ADR 0041). 모델 만들기가 마지막인
    이유는 만들기가 키도 네트워크도 요구하지 않아 실패하는 것이 모델 소스가 거부하는 모양의
    매니페스트뿐이고(model-plugin 명세의 프로브가 잰 것은 키와 네트워크가 필요 없다는 것까지다),
    꺼진 에이전트를 import 하지 않는다는 지금의 불변식을 그대로 두기 위해서다.

    모델의 이름은 에이전트 매니페스트의 `model`, 없으면 `default_model` 이다. 모델 매니페스트는 준비
    한 번에 한 번 읽고 만든 모델을 캐시하지 않는다 — 실행마다 새로 만들어야 운영자가 파일을 고친
    것이 다음 실행부터 듣는다(ADR 0040). 스킬도 같다. 에이전트의 `skills` 에 적힌 이름마다 준비
    한 번에 매니페스트와 스킬 문서를 한 번씩 읽어 `ctx.skills` 로 넘기고 캐시하지 않는다. 읽기가
    동기라 재개의 첫 걸음에 `await` 가 없다는 불변식이 그대로다(ADR 0041).
    """
    limits = _resolve_limits(manifest)
    servers = _resolve_servers(plugins, manifest)
    _reject_masked_approvals(manifest, servers)
    model_name = default_model if manifest.model is None else manifest.model
    model_manifest = _resolve_model(plugins, manifest, model_name)
    skills = _resolve_skills(plugins, manifest)
    rules = plugins.read_rules()
    disabled = plugins.read_disabled()
    _reject_masked_asks(manifest, servers, rules)
    _reject_disabled(disabled, manifest, model_name)
    instance = plugins.load_agent(manifest)
    return _Prepared(
        servers=servers,
        policy=_Policy(
            secrets=secret_args_by_tool(servers),
            approvals=frozenset(manifest.requires_approval),
            rules=rules,
            agent=manifest.name,
        ),
        instance=instance,
        model=models.build(model_manifest),
        skills=skills,
        limits=limits,
    )


def _resolve_limits(manifest: PluginManifest) -> _Limits:
    """에이전트 매니페스트의 두 끝을 이 실행의 값으로 읽는다. 깨짐 묶음의 맨 앞이다(ADR 0052).

    턴의 끝이 10을 넘으면 그 에이전트의 실행을 시작하지 않는다. 낮추기만 하고 올리지 않는 것이 이
    끝의 뜻이라(ADR 0009가 올리는 것을 별도 결정으로 남겼다), 적은 값이 조용히 무시되지 않게
    거부한다. 에이전트 매니페스트만으로 판정되어 다른 플러그인을 읽기 전에 서고, 꺼진 에이전트여도
    깨짐이 먼저 라는 순서의 원칙대로 이 거부가 먼저 난다. 문구는 플러그인 이름 패턴을 지난 에이전트
    이름과 core 의 10만 싣고 적힌 값은 되울리지 않는다. 없음은 턴의 10과 도구 호출의 끝 없음으로
    읽는다.
    """
    if manifest.max_turns is not None and manifest.max_turns > MAX_TURNS:
        raise PluginError(
            f"에이전트 {manifest.name} 의 max_turns 가 루프 상한 {MAX_TURNS} 을 넘는다"
        )
    return _Limits(
        turns=MAX_TURNS if manifest.max_turns is None else manifest.max_turns,
        tool_calls=manifest.max_tool_calls,
    )


def _require_paused_call(
    paused: RunPaused, name: str, masked: Mapping[str, Json], connected: ToolSpec | None
) -> None:
    """재개 뒤 첫 실제 도구 호출이 멈춘 그 호출인지. 인자는 마스킹된 것끼리 비교한다.

    도구 이름과 인자에 더해 서버도 본다. 승인은 운영자가 본 그 서버의 그 도구에만 적용된다 — 멈춘
    사이 같은 이름의 도구가 다른 서버에서 오는 길을 막는다(ADR 0009 의 2026-11-05 둘째 이력). 서버를
    대 보는 것은 멈춤 기록에 서버가 있고 지금 연결에 그 이름의 도구가 있을 때만이다. 멈춘 사이 그
    서버가 매니페스트에서 빠져 이름의 도구가 없으면 여기서 불일치로 끝내지 않는다. 대 볼 서버가
    없고, 그 호출은 연결에 없는 이름의 거부가 결정을 소비하며 거부하기 때문이다. 이 기능 전에 멈춘
    기록에는 서버가 없어 이름과 인자만 본다.
    """
    server_differs = (
        paused.server is not None and connected is not None and paused.server != connected.server
    )
    if paused.tool != name or dict(paused.args) != dict(masked) or server_differs:
        stopped = _labelled(paused.server, paused.tool)
        now = _labelled(None if connected is None else connected.server, name)
        raise Mismatch(
            f"재개 뒤 첫 호출이 멈춘 자리와 다르다. 멈춘 것은 도구 {stopped} "
            f"{dict(paused.args)}, 지금 {now} {dict(masked)}. 결정을 적용하지 않는다"
        )


def _labelled(server: str | None, tool: str) -> str:
    """문구에 쓰는 `<서버>:<도구>`. 서버를 모르는 쪽은 `(서버 없음)` 이다."""
    return f"{'(서버 없음)' if server is None else server}:{tool}"


@dataclass(frozen=True)
class _Resumption:
    """재개의 입력. 멈춘 실행의 시작 이벤트, 결정이 답하는 일시정지, 재생 기록, 처음과 같은 멤버.
    거슬러 읽기의 표현(`Link`)은 `_read_paused` 안에서 끝나고 실행을 모는 쪽으로 새지 않는다."""

    started: RunStarted
    paused: RunPaused
    records: tuple[Record, ...]
    conversation: Conversation


@dataclass(frozen=True)
class OwnTrace:
    """자기 실행 읽기가 돌려주는 것. 저장소의 형식 버전과, 손상·주체·열 에이전트의 판정을 지난 실행
    하나의 이벤트 열. 형식 1 과 일시정지 아님은 거르지 않는다 — 그 판정은 재개의 것이고 구독은
    읽기다. 거슬러 읽기의 표현(`Link`)은 들지 않는다. 그것은 재개가 core 안에서 받고(`_own_link`)
    이것을 부르는 채널로 새지 않는다."""

    schema_version: TraceSchemaVersion
    events: tuple[Event, ...]


def read_own_run(
    trace: TraceStore,
    run_id: RunId,
    principal: Principal,
    visible_agents: frozenset[AgentName] | None,
) -> OwnTrace:
    """요청한 주체가 볼 수 있는 자기 실행 하나를 읽는다. 재개의 첫 걸음과 같은 판정(`_own_link`)이고
    구독(채널)이 이것을 부른다.

    판정 순서는 없음(`Absent`) → 손상(`TraceDamagedBeforePrincipal`) → 다른 주체
    (`DifferentPrincipal`) → 열 에이전트 밖(`Absent`)이다(ADR 0014 의 2026-10-05 이력). 손상은
    재개가 손상이라 부르던 것 그대로다 — 어댑터가 감싼 읽기 실패, 단건 읽기(`link_of`: 모르는 종류,
    빈 트레이스, 식별자 어긋남, 시작 이벤트로 열리지 않음)와 기록 규칙(`check_record_rules`: 앞 실행
    필드의 패턴, 요약 이벤트의 자리와 개수). 손상이 주체보다 앞인 이유는 손상된 트레이스의 주체를
    믿을 수 없어서이고, 그래서 최종 사용자 면이 그것을 없는 실행처럼 덮는다(ADR 0023 의 2026-10-16
    이력). 주체와 열 에이전트는 최종 사용자 면에서 둘 다 404 라 순서가 노출을 바꾸지 않는다.
    열 에이전트 밖의 메시지는 없는 실행의 것과 글자 그대로 같고, 다른 주체의 메시지는 실행을 들되
    그 실행의 주체 이름을 들지 않는다.

    동기이고 await 가 없다. 재개의 첫 걸음과 구독의 한 걸음(트레이스 읽기와 등록부 보기)이 여기에
    기댄다(ADR 0014). 이어 가기의 `gather_continued` 와는 나누지 않는다 — 이어 가기는 앞 실행 자신의
    기록 규칙을 주체·끝남 뒤에 보므로, 이것을 쓰면 그 결정된 순서가 바뀐다.
    """
    schema_version, link = _own_link(trace, run_id, principal, visible_agents)
    return OwnTrace(schema_version=schema_version, events=link.events)


def _own_link(
    trace: TraceStore,
    run_id: RunId,
    principal: Principal,
    visible_agents: frozenset[AgentName] | None,
) -> tuple[TraceSchemaVersion, Link]:
    """자기 실행 읽기의 판정 자체(판정 순서는 `read_own_run`). 재개는 거슬러 읽기의 표현이 필요해
    이것을 직접 부르고, 채널은 이벤트 열만 받는 `read_own_run` 을 부른다. 손상은 주인을 확인하기
    전의 것이라 하위 타입이고(이유는 `TraceDamagedBeforePrincipal`, 감싸는 것은 `before_principal`),
    없음은 손상이 아니라 그 사이에 선다."""
    with before_principal():
        stored = trace.read(run_id)
    if stored is None:
        raise Absent(_no_run(run_id))
    with before_principal():
        link = link_of(stored, run_id)
        check_record_rules(link)
    if link.started.principal != principal:
        raise DifferentPrincipal(f"실행 {run_id} 은 요청한 주체의 실행이 아니다")
    if visible_agents is not None and link.started.agent not in visible_agents:
        raise Absent(_no_run(run_id))
    return stored.schema_version, link


def _no_run(run_id: RunId) -> str:
    """없는 실행의 메시지. 열 에이전트 밖의 실행도 글자 그대로 이것이다."""
    return f"그런 실행이 없다: {run_id}"


def _no_agent(agent: AgentName) -> str:
    """없는 에이전트의 메시지. 열 에이전트 밖의 에이전트도 글자 그대로 이것이다."""
    return f"에이전트 플러그인이 없다: {agent}"


def _read_paused(
    trace: TraceStore,
    run_id: RunId,
    pause_index: int,
    approver: Principal,
    visible_agents: frozenset[AgentName] | None,
) -> _Resumption:
    """재개의 입력을 읽고 재개할 수 없는 것을 거부한다. 트레이스를 신뢰하는 유일한 자리다.

    멈춘 실행의 시작 이벤트, 결정이 가리킨 일시정지(결정이 묶이는 호출), 재생 기록, 시작 이벤트의 앞
    실행에서 다시 거슬러 읽은 멤버를 돌려준다. 판정 순서는 자기 실행 읽기(없음 → 손상 → 다른 주체 →
    열 에이전트 밖) → 형식 1 → 일시정지 아님 → 자리 어긋남 → 고리다(ADR 0014 의 2026-10-05 이력).
    다른 주체가 형식 1·일시정지 아님·자리 어긋남보다 앞인 이유는 최종 사용자 면이 남의 실행을 없는
    실행처럼 숨기려면 남의 실행의 상태가 먼저 드러나면 안 되기 때문이다. 형식 1 이 손상 뒤인 것은
    형식 1 트레이스의 주체도 읽어야 해서다. 손상된 형식 1 트레이스에 온 결정이 재개 불가가 아니라
    깨진 기록인 것이 그 대가다. 손상에는 고리의 실행에 거는 기록 규칙도 든다 — 자기 트레이스에만
    빼는 이유가 없다(ADR 0022). 일시정지 아님이 자리보다 먼저라, 같은 자리를 든 결정 둘이
    동시에 오면 둘째는 "지나간 자리"가 아니라 "일시정지 아님"을 듣는다.

    자리로 이벤트를 꺼내지 않고 마지막 이벤트의 자리와 같은지만 본다. 꺼내면 파이썬의 음수 인덱스
    `-1` 이 마지막 이벤트에 맞는다. 같은지만 보면 음수는 언제나 어긋남이다. 채널이 음수를 형식
    오류로 막아도 여기서 그것을 믿지 않는다. 모르는 종류의 이벤트는 손상에서 이미 거부되므로 여기서
    세는 자리는 트레이스 상세 `events` 의 인덱스와 같다.
    """
    schema_version, link = _own_link(trace, run_id, approver, visible_agents)
    if schema_version not in RESUMABLE:
        raise NotResumable(
            f"형식 {schema_version} 트레이스는 읽을 수는 있어도 재개할 수 없다: {run_id}"
        )
    paused = link.last
    if not isinstance(paused, RunPaused):
        raise NotResumable(f"일시정지 상태가 아니라 재개할 수 없다: {run_id}")
    current = len(link.events) - 1
    if pause_index != current:
        raise NotResumable(
            f"결정이 가리킨 자리 {pause_index} 는 지금의 일시정지(자리 {current})가 아니라 "
            f"재개할 수 없다: {run_id}"
        )
    records = tuple(e for e in link.events if not isinstance(e, _NOT_REPLAYED))
    return _Resumption(
        started=link.started,
        paused=paused,
        records=records,
        conversation=resumed_conversation(trace, link),
    )


def _requested_manifest(plugins: PluginSource, agent: AgentName) -> PluginManifest:
    """요청이 이름을 댄 에이전트. 없으면 부재다."""
    manifest = plugins.read_manifest(PluginKind.AGENT, PluginName(agent))
    if manifest is None:
        raise Absent(_no_agent(agent))
    return manifest


def _recorded_manifest(plugins: PluginSource, started: RunStarted) -> PluginManifest:
    """재개할 실행의 트레이스가 가리키는 에이전트. 없으면 부재가 아니라 구성 오류다.

    이름을 댄 것이 요청이 아니라 서버가 가진 기록이고, 요청이 가리킨 실행은 있다. 기록과 구성이
    어긋난 것, 곧 깨진 것이라 부재로 말하면 식별자를 잘못 적었다고 믿게 된다(ADR 0014 의
    2026-09-24·2026-09-26 이력). 에이전트가 가리키는 mcp 플러그인이 없을 때와 같은 모양이다.
    """
    manifest = plugins.read_manifest(PluginKind.AGENT, PluginName(started.agent))
    if manifest is None:
        raise PluginError(f"실행 {started.run_id} 의 에이전트 플러그인이 없다: {started.agent}")
    return manifest


def _resolve_servers(
    plugins: PluginSource, manifest: PluginManifest
) -> dict[PluginName, McpServer]:
    """매니페스트가 지정한 mcp 플러그인만. 비어 있으면 도구가 없다(ADR 0002)."""
    servers: dict[PluginName, McpServer] = {}
    for name in manifest.mcp:
        mcp = plugins.read_manifest(PluginKind.MCP, name)
        if mcp is None or mcp.server is None:
            raise PluginError(f"에이전트 {manifest.name} 이 지정한 mcp 플러그인이 없다: {name}")
        servers[name] = mcp.server
    return servers


def _resolve_model(
    plugins: PluginSource, manifest: PluginManifest, name: PluginName
) -> PluginManifest:
    """에이전트가 쓰는 모델의 매니페스트. 없으면 구성 오류다(mcp 의 없음과 같은 꼴).

    문구는 누구의 지정인지를 든다. 에이전트가 적은 모델이면 그 에이전트를, 아니면 기본 모델이라고
    적는다. 읽히지 않음은 어댑터의 `PluginError` 가 그대로 올라온다. 종류를 거르는 것은 단건 읽기
    (`read_manifest(MODEL, …)`)이고 여기서 칸을 꺼내 쓰거나 종류를 다시 보지 않는다.
    """
    found = plugins.read_manifest(PluginKind.MODEL, name)
    if found is not None:
        return found
    if manifest.model is not None:
        raise PluginError(f"에이전트 {manifest.name} 이 지정한 model 플러그인이 없다: {name}")
    raise PluginError(f"기본 모델 플러그인이 없다: {name}")


def _resolve_skills(plugins: PluginSource, manifest: PluginManifest) -> tuple[Skill, ...]:
    """에이전트가 고른 스킬의 문서를 매니페스트에 적힌 순서대로. 비어 있으면 빈 열이다(ADR 0041).

    이름마다 매니페스트 → 스킬 문서 순으로 한 번씩 읽고, 한 이름을 끝낸 뒤 다음 이름으로 간다.
    매니페스트가 없으면 스킬 문서를 읽지 않는다. 문구는 누구의 지정인지를 들고, 읽히지 않음과 이름
    어긋남은 어댑터의 `PluginError` 가 그대로 올라온다. 문구가 싣는 것은 패턴을 지난 이름뿐이다.

    `read_skill` 에 넘기는 이름은 에이전트 매니페스트의 `skills` 칸에서 온다. 그 칸은 읽는 단계에서
    원소마다 플러그인 이름 패턴을 지났으므로(`PluginManifest.skills`) 여기서 다시 거르지 않는다.
    어댑터가 `read_manifest` 처럼 이름을 스스로 검증하지 않는 대신 호출부가 패턴을 지난 값만 넘기는
    규약이다. 받는 것은 `PluginError` 뿐이고(경로 존재 확인의 `OSError` 는 예외로 감싸지 않고
    올라온다, 대기열 572) 머리말의 `ValidationError` 는 어댑터가 이미 값 없는 문구로 바꾼다.
    """
    skills: list[Skill] = []
    for name in manifest.skills:
        if plugins.read_manifest(PluginKind.SKILL, name) is None:
            raise PluginError(f"에이전트 {manifest.name} 이 지정한 skill 플러그인이 없다: {name}")
        skill = plugins.read_skill(name)
        if skill is None:
            raise PluginError(
                f"에이전트 {manifest.name} 이 지정한 skill 플러그인에 SKILL.md 가 없다: {name}"
            )
        skills.append(skill)
    return tuple(skills)


def _reject_masked_approvals(
    manifest: PluginManifest, servers: Mapping[PluginName, McpServer]
) -> None:
    """금지 규칙을 실행 식별자가 생기기 전에 거부로 바꾼다. 이유는 sdk 의 approval_conflicts."""
    conflicts = approval_conflicts(manifest, servers)
    if conflicts:
        raise PluginError(
            f"마스킹된 인자를 가진 도구는 승인 대상이 될 수 없다: {', '.join(conflicts)}"
        )


def _reject_masked_asks(
    manifest: PluginManifest, servers: Mapping[PluginName, McpServer], rules: Rules
) -> None:
    """마스킹할 인자가 있는 도구를 규칙이 묻게 두면 실행 전에 거부한다(스토리 11).

    저자의 승인 요구와 같은 충돌이다 — 재생한 모델 응답의 인자는 마스킹된 값이라 승인 뒤 실제 호출이
    그 값을 보내게 된다. 기본이 묻는다가 되어 운영자의 ask 와 적힌 규칙 없음도 같은 도구를 멈추게
    하므로, 저자의 승인 요구를 뺀 차례로 적용 규칙을 내어 `ask` 나 `default` 면 거부한다(그 겹침은
    `_reject_masked_approvals` 가 이미 거부했다). deny 는 불리지 않고 allow 는 묻지 않아 충돌이
    아니다. 도구가 어느 서버의 것인지는 매니페스트만으로 알아 연결이 서기 전에 판정한다.
    """
    conflicts = [
        f"{server}:{tool}"
        for server, mcp in servers.items()
        for tool, names in mcp.secret_args.items()
        if names
        and applied_rule(
            rules, agent=manifest.name, server=server, tool=tool, requires_approval=False
        )
        in ("ask", "default")
    ]
    if conflicts:
        raise PluginError(
            "마스킹된 인자를 가진 도구는 묻는 규칙에 걸릴 수 없다: "
            f"{', '.join(conflicts)} (규칙 파일에 allow 나 deny 를 적는다)"
        )


def _reject_disabled(
    disabled: frozenset[PluginKey], manifest: PluginManifest, model_name: PluginName
) -> None:
    """운영자가 끈 것을 부른 실행을 거부한다. 에이전트가 먼저, mcp 와 스킬은 매니페스트에 적힌
    순서이고 모델이 mcp 뒤, 스킬이 마지막이다.

    꺼진 집합은 부르는 쪽이 한 번 읽어 넘긴다. 에이전트와 mcp 들과 모델과 스킬들을 같은 순간의
    상태로 판정하기 위해서다(ADR 0012 의 2026-09-26 이력). 메시지는 꺼진 것의 종류와 이름이다 —
    켜진 에이전트가 꺼진 mcp 나 모델이나 스킬 때문에 거부되면 운영자에게 켜 달라고 할 것이 그 mcp 나
    모델이나 스킬이기 때문이다. 기본 모델이 꺼진 것도 그것을 쓰는 실행의 거부다. 이 순서는
    깨짐의 순서(mcp → 모델 → 스킬)와 같다.
    """
    agent = PluginKey(kind=PluginKind.AGENT, name=manifest.name)
    if agent in disabled:
        raise Disabled(f"꺼진 플러그인이다: {agent.kind} {agent.name}")
    for name in manifest.mcp:
        mcp = PluginKey(kind=PluginKind.MCP, name=name)
        if mcp in disabled:
            raise Disabled(
                f"꺼진 플러그인이다: {mcp.kind} {mcp.name} (에이전트 {manifest.name} 이 쓴다)"
            )
    model = PluginKey(kind=PluginKind.MODEL, name=model_name)
    if model in disabled:
        raise Disabled(
            f"꺼진 플러그인이다: {model.kind} {model.name} (에이전트 {manifest.name} 이 쓴다)"
        )
    for name in manifest.skills:
        skill = PluginKey(kind=PluginKind.SKILL, name=name)
        if skill in disabled:
            raise Disabled(
                f"꺼진 플러그인이다: {skill.kind} {skill.name} (에이전트 {manifest.name} 이 쓴다)"
            )


def _reject_unknown_declarations(policy: _Policy, specs: Sequence[ToolSpec]) -> None:
    """매니페스트가 가리키는 도구와 인자가 실재하는지. 도구 목록이 연결 뒤에 나와 여기가 첫 자리다.

    오타나 중첩 프로퍼티가 게이트나 마스킹을 조용히 끄는 fail-open 을 막는다(ADR 0009 와 그
    2026-09-21 이력). 실행 안이라 run_failed 로 끝나고 트레이스가 남는다. 재개에서도 같은
    자리에서 도므로, 승인을 기다리는 사이 매니페스트가 바뀌었으면 여기서 먼저 걸린다.
    """
    params = {spec.name: _param_names(spec) for spec in specs}
    for tool in policy.approvals:
        if tool not in params:
            raise LookupError(f"requires_approval 이 가리키는 도구가 없다: {tool}")
    for tool, names in policy.secrets.items():
        if tool not in params:
            raise LookupError(f"secret_args 가 가리키는 도구가 없다: {tool}")
        for name in names:
            if name not in params[tool]:
                raise LookupError(f"secret_args 가 가리키는 인자가 도구 {tool} 에 없다: {name}")


def _reject_unknown_rule_lines(prepared: _Prepared, specs: Sequence[ToolSpec]) -> None:
    """그 에이전트의 표에 적힌 줄이 연결에 실재하는지(스토리 6). 저자의 승인 요구 검사 바로 뒤다.

    deny 의 오타가 같은 도구에 맞는 공통 allow 뒤에 숨어 그 도구를 묻지 않고 돌리는 길을 막는다.
    deny 로 빼기 전의 전체 목록에 대고, 어긋난 줄은 글자가 아니라 자리로 모두 알린다(글자는 운영자가
    잘못 적은 비밀일 수 있다, 원칙 V). 공통 표는 모양만 본다. 판정은 `unresolved_rule_lines` 의
    몫이다.
    """
    policy = prepared.policy
    missing = unresolved_rule_lines(
        policy.rules, agent=policy.agent, servers=tuple(prepared.servers), specs=specs
    )
    if missing:
        raise LookupError(
            "규칙 파일의 에이전트 표가 가리키는 도구가 없다: "
            f"{policy.agent} 의 {', '.join(missing)}"
        )


def _param_names(spec: ToolSpec) -> frozenset[str]:
    """JSON Schema 의 properties 키. 없으면 이름 있는 인자가 없는 도구다."""
    properties = spec.input_schema.get("properties")
    return frozenset(properties) if isinstance(properties, dict) else frozenset()


async def _call_safely(tools: ToolConnection, name: str, args: Mapping[str, Json]) -> ToolResult:
    """도구가 예외를 내도 실행은 죽지 않는다. 에러 내용을 결과로 바꿔 모델이 알게 한다."""
    try:
        return await tools.call(name, args)
    except Exception as error:
        return ToolResult(ok=False, content=_describe(error))


def _cancellation_under(error: BaseException) -> BaseException | None:
    """`error` 가 덮은 취소. 정리 코드(`finally`, `__aexit__`)가 도는 취소 중에 다른 예외를 내면
    파이썬은 취소를 그 예외의 문맥(`__context__`)에 남긴다."""
    cancelled = anyio.get_cancelled_exc_class()
    seen: set[int] = set()
    current = error.__context__
    while current is not None and id(current) not in seen:
        if isinstance(current, cancelled):
            return current
        seen.add(id(current))
        current = current.__context__
    return None


def _describe(error: BaseException) -> str:
    """ExceptionGroup 은 겉만 보면 원인을 알 수 없어서 안의 예외를 펼친다."""
    if _is_group(error):
        inner = "; ".join(_describe(e) for e in error.exceptions)
        return f"{type(error).__name__}[{inner}]"
    return f"{type(error).__name__}: {error}"


def _is_group(error: BaseException) -> TypeGuard[BaseExceptionGroup[BaseException]]:
    """isinstance 로 좁히면 pyright 가 타입 인자를 Unknown 으로 둔다. 여기서 명시한다."""
    return isinstance(error, BaseExceptionGroup)
