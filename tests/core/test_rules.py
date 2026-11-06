"""규칙 값과 적용 규칙을 내는 순수 함수. 파일도 런타임도 없이 값만 넣고 값을 본다.

세 꼴의 맞음, 공통 표와 에이전트 표의 합집합, 차례 다섯의 각 갈래를 잰다(approval-rules 명세
"핵심의 규칙 값과 포트 메서드", ADR 0044 "집행의 차례").
"""

import pytest

from agent_os.core.ports import Rule, Rules, RuleSet
from agent_os.core.rules import applied_rule
from agent_os.sdk import AppliedRule, PluginName

EVERYTHING = PluginName("everything")
OTHER_SERVER = PluginName("other-server")
CALC = PluginName("calc")
OTHER_AGENT = PluginName("other")


def _bare(tool: str) -> Rule:
    return Rule(server=None, tool=tool)


def _whole(server: PluginName) -> Rule:
    return Rule(server=server, tool=None)


def _one(server: PluginName, tool: str) -> Rule:
    return Rule(server=server, tool=tool)


def _set(
    *,
    deny: tuple[Rule, ...] = (),
    ask: tuple[Rule, ...] = (),
    allow: tuple[Rule, ...] = (),
) -> RuleSet:
    return RuleSet(deny=frozenset(deny), ask=frozenset(ask), allow=frozenset(allow))


def _applied(
    rules: Rules,
    *,
    agent: PluginName = CALC,
    server: PluginName = EVERYTHING,
    tool: str = "add",
    requires_approval: bool = False,
) -> AppliedRule:
    return applied_rule(
        rules, agent=agent, server=server, tool=tool, requires_approval=requires_approval
    )


def test_둘_다_없는_규칙은_만들_수_없다() -> None:
    """서버도 도구도 없는 규칙은 어느 호출에나 맞는 규칙이 된다. 만들 길을 막는다."""
    with pytest.raises(ValueError, match="서버나 도구"):
        Rule(server=None, tool=None)


# 세 꼴의 맞음과 안 맞음. (규칙, 서버, 도구, 맞는가)
MATCHES = (
    pytest.param(_bare("add"), EVERYTHING, "add", True, id="맨 이름-그 이름"),
    pytest.param(_bare("add"), OTHER_SERVER, "add", True, id="맨 이름-다른 서버의 그 이름"),
    pytest.param(_bare("add"), EVERYTHING, "sub", False, id="맨 이름-다른 이름"),
    pytest.param(_whole(EVERYTHING), EVERYTHING, "add", True, id="서버 전체-그 서버의 도구"),
    pytest.param(_whole(EVERYTHING), EVERYTHING, "sub", True, id="서버 전체-그 서버의 다른 도구"),
    pytest.param(_whole(EVERYTHING), OTHER_SERVER, "add", False, id="서버 전체-다른 서버"),
    pytest.param(_one(EVERYTHING, "add"), EVERYTHING, "add", True, id="묶인 도구-그 이름"),
    pytest.param(_one(EVERYTHING, "add"), OTHER_SERVER, "add", False, id="묶인 도구-다른 서버"),
    pytest.param(_one(EVERYTHING, "add"), EVERYTHING, "sub", False, id="묶인 도구-다른 이름"),
    # 도구 이름의 `*` 는 아무 글자열(빈 것 포함)에 맞고, 패턴은 도구 이름 전체에 맞아야 한다.
    pytest.param(_bare("*"), EVERYTHING, "add", True, id="맨 별표-어느 도구"),
    pytest.param(_bare("*"), OTHER_SERVER, "sub", True, id="맨 별표-다른 서버의 도구"),
    pytest.param(_bare("send_*"), EVERYTHING, "send_mail", True, id="접두 패턴-맞는 이름"),
    pytest.param(_bare("send_*"), EVERYTHING, "send_", True, id="접두 패턴-별표가 빈 글자열"),
    pytest.param(_bare("send_*"), EVERYTHING, "resend_mail", False, id="접두 패턴-앞이 다른 이름"),
    pytest.param(_bare("send_*"), EVERYTHING, "sendmail", False, id="접두 패턴-밑줄이 없는 이름"),
    pytest.param(_bare("*_mail"), EVERYTHING, "send_mail", True, id="접미 패턴-맞는 이름"),
    pytest.param(_bare("*_mail"), EVERYTHING, "mail_send", False, id="접미 패턴-뒤가 다른 이름"),
    pytest.param(_bare("a*b*c"), EVERYTHING, "aXbYc", True, id="별표 둘-맞는 이름"),
    pytest.param(_bare("a*b*c"), EVERYTHING, "aXcYb", False, id="별표 둘-순서가 다른 이름"),
    pytest.param(_bare("a.b"), EVERYTHING, "aXb", False, id="점은 글자 그대로다"),
    pytest.param(_bare("a.b"), EVERYTHING, "a.b", True, id="점이 든 이름"),
    # 개행이 든 이름에도 `*` 가 맞아야 deny 가 그 이름 앞에서 조용히 새지 않는다.
    pytest.param(_bare("*"), EVERYTHING, "a\nb", True, id="맨 별표-개행이 든 이름"),
    pytest.param(_bare("add"), EVERYTHING, "add_more", False, id="별표 없는 이름-더 긴 이름"),
    pytest.param(_bare("*_mail"), EVERYTHING, "send_mail_log", False, id="접미 패턴-더 긴 이름"),
    pytest.param(_one(EVERYTHING, "get_*"), EVERYTHING, "get_user", True, id="묶인 패턴-그 서버"),
    pytest.param(
        _one(EVERYTHING, "get_*"), OTHER_SERVER, "get_user", False, id="묶인 패턴-다른 서버"
    ),
    pytest.param(
        _one(EVERYTHING, "get_*"), EVERYTHING, "set_user", False, id="묶인 패턴-다른 이름"
    ),
)


@pytest.mark.parametrize(("rule", "server", "tool", "expected"), MATCHES)
def test_규칙은_세_꼴과_별표_패턴대로_도구에_맞거나_안_맞는다(
    rule: Rule, server: PluginName, tool: str, *, expected: bool
) -> None:
    assert rule.matches(server=server, tool=tool) is expected


def test_이름이_별표인_도구에도_서버_전체_규칙과_맨_별표는_맞는다() -> None:
    """콜론 뒤의 `*`는 언제나 서버의 모든 도구이고, 맨 `*`는 모든 서버의 모든 도구다. 이름이 `*`인
    도구가 있어도(MCP 규약 밖이다) 패턴 `*`가 아무 글자열에 맞으므로 그 도구에도 맞는다."""
    assert _whole(EVERYTHING).matches(server=EVERYTHING, tool="*")
    assert _bare("*").matches(server=EVERYTHING, tool="*")


def test_아무_규칙도_없으면_기본이다() -> None:
    assert _applied(Rules()) == "default"


def test_deny에_맞으면_deny다() -> None:
    rules = Rules(common=_set(deny=(_one(EVERYTHING, "add"),)))

    assert _applied(rules) == "deny"


def test_ask에_맞으면_ask다() -> None:
    rules = Rules(common=_set(ask=(_one(EVERYTHING, "add"),)))

    assert _applied(rules) == "ask"


def test_allow에_맞으면_allow다() -> None:
    rules = Rules(common=_set(allow=(_whole(EVERYTHING),)))

    assert _applied(rules) == "allow"


def test_저자의_승인_요구는_규칙이_없어도_requires_approval이다() -> None:
    assert _applied(Rules(), requires_approval=True) == "requires_approval"


def test_저자의_승인_요구는_운영자의_allow가_풀지_못한다() -> None:
    """저자가 승인을 요구한 도구를 운영자가 allow 로 열 수 없다. 열쇠가 둘이 아니다."""
    rules = Rules(common=_set(allow=(_whole(EVERYTHING),)))

    assert _applied(rules, requires_approval=True) == "requires_approval"


def test_저자의_승인_요구는_운영자의_ask보다_앞이다() -> None:
    rules = Rules(common=_set(ask=(_one(EVERYTHING, "add"),)))

    assert _applied(rules, requires_approval=True) == "requires_approval"


def test_운영자의_deny는_저자의_승인_요구보다_앞이다() -> None:
    rules = Rules(common=_set(deny=(_one(EVERYTHING, "add"),)))

    assert _applied(rules, requires_approval=True) == "deny"


def test_ask는_allow보다_앞이다() -> None:
    rules = Rules(common=_set(ask=(_one(EVERYTHING, "add"),), allow=(_whole(EVERYTHING),)))

    assert _applied(rules) == "ask"


def test_deny는_ask와_allow보다_앞이다() -> None:
    rules = Rules(
        common=_set(
            deny=(_one(EVERYTHING, "add"),),
            ask=(_one(EVERYTHING, "add"),),
            allow=(_one(EVERYTHING, "add"),),
        )
    )

    assert _applied(rules) == "deny"


def test_같은_도구가_deny와_allow에_함께_적혀도_deny다() -> None:
    """거부하지 않는 것이다. 차례가 deny 를 먼저 보므로 뜻이 하나다."""
    rules = Rules(common=_set(deny=(_bare("add"),), allow=(_one(EVERYTHING, "add"),)))

    assert _applied(rules) == "deny"


def test_deny는_맨_이름으로도_서버_전체로도_걸린다() -> None:
    assert _applied(Rules(common=_set(deny=(_bare("add"),)))) == "deny"
    assert _applied(Rules(common=_set(deny=(_whole(EVERYTHING),)))) == "deny"


def test_그_에이전트의_표에_적힌_규칙이_걸린다() -> None:
    """양성 대조. 다음 시험의 같은 줄을 calc 의 표에 두면 걸린다."""
    rules = Rules(agents={CALC: _set(deny=(_one(EVERYTHING, "add"),))})

    assert _applied(rules, agent=CALC) == "deny"


def test_다른_에이전트의_표에_적힌_규칙은_걸리지_않는다() -> None:
    """스토리 2 의 "그 에이전트에만 걸린다". `[agents.other] deny` 는 calc 의 호출에 닿지 않는다."""
    rules = Rules(agents={OTHER_AGENT: _set(deny=(_one(EVERYTHING, "add"),))})

    assert _applied(rules, agent=CALC) == "default"
    assert _applied(rules, agent=OTHER_AGENT) == "deny"


def test_공통_표와_에이전트_표는_목록_종류마다_합집합이다() -> None:
    rules = Rules(
        common=_set(deny=(_one(EVERYTHING, "add"),)),
        agents={CALC: _set(ask=(_one(EVERYTHING, "sub"),))},
    )

    assert _applied(rules, tool="add") == "deny"
    assert _applied(rules, tool="sub") == "ask"
    assert _applied(rules, tool="mul") == "default"


def test_공통_표의_deny를_에이전트_표의_allow가_풀지_못한다() -> None:
    """공통 표가 배치의 하한이다. 가까운 표가 이기지 않는다."""
    rules = Rules(
        common=_set(deny=(_one(EVERYTHING, "add"),)),
        agents={CALC: _set(allow=(_one(EVERYTHING, "add"),))},
    )

    assert _applied(rules) == "deny"


def test_에이전트_표의_deny를_공통_표의_allow가_풀지_못한다() -> None:
    rules = Rules(
        common=_set(allow=(_whole(EVERYTHING),)),
        agents={CALC: _set(deny=(_one(EVERYTHING, "add"),))},
    )

    assert _applied(rules) == "deny"


def test_공통_표의_ask를_에이전트_표의_allow가_풀지_못한다() -> None:
    rules = Rules(
        common=_set(ask=(_one(EVERYTHING, "add"),)),
        agents={CALC: _set(allow=(_one(EVERYTHING, "add"),))},
    )

    assert _applied(rules) == "ask"


def test_규칙_값은_받은_표를_복사해_들어서_나중에_바뀐_원본을_보지_않는다() -> None:
    """어댑터가 넘긴 지도를 나중에 고쳐도 읽은 규칙이 바뀌지 않는다. 불변 값이라는 약속이다."""
    source = {CALC: _set()}
    rules = Rules(agents=source)

    source[OTHER_AGENT] = _set(deny=(_bare("add"),))

    assert OTHER_AGENT not in rules.agents
