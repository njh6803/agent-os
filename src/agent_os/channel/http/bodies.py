"""채널의 요청 본문. 운영자 채널(`/runs`)과 최종 사용자 면이 같은 모델을 쓴다(ADR 0014·0023).

계약에 박히는 모델이라 독스트링은 한 줄이고 논증은 `#` 주석에 둔다(`.claude/rules/http.md`). 최종
사용자 면이 새 본문 컴포넌트를 두지 않는 것은 명세가 정했다 — 시작은 `StartRun`, 결정은 `Decision`
그대로이고 주체와 승인자는 본문이 아니라 검증된 신원에서 온다(ADR 0015·0023).
"""

from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from agent_os.core.run import Approve as CoreApprove
from agent_os.core.run import Deny as CoreDeny
from agent_os.sdk import PLUGIN_NAME_PATTERN, AgentName


# 계약에 박히는 요청 본문이다. 기본값 있는 필드를 두지 않는다 — 기본값이 있으면 그 필드는 계약에서
# 선택이 된다. 이벤트와 매니페스트가 켜 둔 `json_schema_serialization_defaults_required` 는 직렬화
# 스키마에만 걸리고 요청 본문은 검증 스키마로 실린다(명세 검토의 프로브). 추가 필드는 무시하지
# 않고 422 다. 주체와 승인자와 모델이 그런 필드이고, 보낸 쪽이 자기 값이 쓰였다고 믿게 두지
# 않는다(ADR 0015). `agent` 는 `plugins/agents/{agent}/plugin.toml` 로 조립되는 원격 입력이라 sdk
# 의 패턴을 포트에 닿기 전에 지난다. `request` 는 문자열이면 된다 — CLI 가 받는 것과 같다.
class StartRun(BaseModel):
    """실행 하나를 일으키는 요청. 등록된 에이전트의 이름과 요청 문자열이다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    agent: Annotated[AgentName, Field(pattern=PLUGIN_NAME_PATTERN)]
    request: str


# 결정이 답하는 일시정지의 자리. 두 멤버에 같은 이름과 같은 스키마로 실린다(ADR 0014 의
# 2026-09-28 이력). 기본값이 없다 — 있으면 그 값이 곧 "지금의 일시정지"라 오래된 화면의 결정이 다시
# 받아들여진다. `strict` 인 이유는 lax 검증이면 문자열 `"2"`, 실수 `2.0`, 불린 `true` 가 모두
# 정수로 읽히기 때문이다(`true` 는 1). 계약이 `integer` 라 적는데 문자열이 자리를 정하면 안 되고,
# 스키마는 lax 와 같다(명세 검토의 프로브, 선례는 관리의 `_CursorWire`). 이름을 `…_at` 으로 짓지
# 않은 것은 시각으로 읽히기 때문이다. 필드에는 독스트링을 둘 자리가 없어 계약의 설명이
# `description` 에 있다. `type` 별칭으로 쓰지 않는 이유는 관리의 `_WireRunId` 와 같다 — pydantic 이
# 이름 있는 스키마로 떼어 낸다.
_PauseIndex = Annotated[
    int,
    Field(
        ge=0,
        strict=True,
        description=(
            "이 결정이 답하는 run_paused 이벤트가 트레이스 상세 events 에서 서는 0부터 센 인덱스. "
            "최종 사용자 스트림에서는 일시정지 항목의 id 다. 지금의 일시정지가 아니면 409 다"
        ),
    ),
]


# 결정 본문의 멤버 둘과 그 유니온. 이름이 core 의 `Approve`·`Deny`·`Decision` 과 같다. 용어집의
# 결정은 "허가이거나, 사유를 붙인 거부"이고 이것과 core 의 것은 같은 개념의 두 모양(와이어와 core
# 의 값)이라, 관리의 `Trace`·`RunSummary` 가 core 의 것과 이름이 같은 선례를 따른다. core 쪽은 이
# 모듈에서 별칭으로 부른다. 이벤트 컴포넌트(`ApprovalGranted`·`ApprovalDenied`)와 같은 이름을 쓰지
# 않는 이유는 그러면 계약의 이벤트 컴포넌트가 입력과 출력으로 갈라지기 때문이다(명세 검토의 프로브).
#
# 판별자에도 기본값을 두지 않는다. 요청 본문은 검증 스키마로 실려 기본값이 곧 계약의 "선택"이
# 되는데 서버는 판별자 없는 본문을 거부한다(`StartRun` 과 같은 규칙). 추가 필드는 422 다 — 승인에
# 붙은 사유가 조용히 버려지지 않고, 승인자는 본문이 아니라 운영자 채널에서는 조립이 넘긴 주체,
# 최종 사용자 면에서는 서명 토큰이 정한 주체다(ADR 0015·0023).
class Approve(BaseModel):
    """허가. 멈춘 도구 호출이 실제로 실행된다. 사유를 담을 자리가 없다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    decision: Literal["approve"]
    pause_index: _PauseIndex

    def to_core(self) -> CoreApprove:
        """core 가 받는 결정(질의)."""
        return CoreApprove()


def _trimmed(reason: str) -> str:
    """거부 사유를 CLI 와 같은 규칙(파이썬 `str.strip`)으로 다듬는다. 다듬어 비면 형식 오류다.

    pydantic 의 `strip_whitespace` 를 쓰지 않는 이유는 그 다듬기(rust)가 U+001C~U+001F 를 공백으로
    보지 않아서다. 그러면 그 문자만 든 사유가 검증을 지나 core 의 `Deny` 에서 막혀 422 가 아니라
    고정 문구의 500 이 되고, 앞뒤에 붙은 것은 CLI 와 다르게 기록된다. 두 경우를 채널 테스트가 잰다.
    """
    trimmed = reason.strip()
    if not trimmed:
        raise ValueError("거부에는 공백이 아닌 사유가 있어야 한다")
    return trimmed


# 사유는 앞뒤 공백을 다듬어 기록한다. CLI 의 결정 해석이 다듬은 사유를 넘기므로 두 채널에서 같은
# 결정이 같게 기록된다(스토리 27). 다듬은 뒤 비면 422 이고 core 의 `Deny` 가 한 번 더 막는다.
# `min_length` 는 계약에 "비어 있지 않다"를 적는 자리이고 판정은 `_trimmed` 가 한다.
class Deny(BaseModel):
    """거부. 도구를 부르지 않고 사유를 모델에 되돌린다. 사유는 비어 있을 수 없다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    decision: Literal["deny"]
    reason: Annotated[str, Field(min_length=1), AfterValidator(_trimmed)]
    pause_index: _PauseIndex

    def to_core(self) -> CoreDeny:
        """core 가 받는 결정(질의)."""
        return CoreDeny(reason=self.reason)


# 판별자 `decision` 의 유니온이라 허가와 거부가 같은 모양의 선택 필드로 섞이지 않는다(ADR 0014).
# 계약에 `Decision` 이라는 이름 있는 타입이 서려면 라우트가 이것을 `Body()` 로 받아야 한다 — 별칭을
# 그대로 받으면 FastAPI 가 본문을 `Body` 라는 제목의 익명 유니온으로 인라인한다. 계약 이름 테스트가
# 그것을 잡는다. 422 의 `violations` 경로 모양은 `.claude/rules/http.md`.
type Decision = Annotated[Approve | Deny, Field(discriminator="decision")]
