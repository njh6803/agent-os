"""한 호출에 적용되는 규칙을 내는 순수 함수(ADR 0044 "집행의 차례").

규칙 값(`Rule`·`RuleSet`·`Rules`)은 `core/ports.py` 에 있고, 파일을 읽어 그 값으로 바꾸는 것은
어댑터의 몫이다. 여기는 값만 받아 값만 돌려준다. 언제 이 함수를 부르는지는 호출하는 쪽이 정한다.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable, Sequence

from agent_os.core.ports import Rule, Rules, RuleSet, ToolSpec
from agent_os.sdk import AppliedRule, PluginName


def applied_rule(
    rules: Rules,
    *,
    agent: PluginName,
    server: PluginName,
    tool: str,
    requires_approval: bool,
) -> AppliedRule:
    """(에이전트, 서버 플러그인, 도구) 한 호출에 적용되는 규칙 하나.

    차례는 운영자의 deny → 저자의 `requires_approval` → 운영자의 ask → 운영자의 allow → 아니면
    `default` 다. 공통 표와 에이전트 표는 목록 종류마다 합집합이라 어느 표에 적혔는지는 차례에 들지
    않는다. 그래서 공통 표의 deny 를 에이전트 표의 allow 가 풀지 못하고 그 반대도 같다. 도구는
    `ToolSpec` 이 아니라 서버 이름과 도구 이름의 쌍으로 받는다 — 서버 칸은 연결이 낸 명세에만 있어,
    명세를 받으면 연결이 서기 전의 판정이 이 함수를 쓰지 못한다. `requires_approval` 은 저자가
    매니페스트에 적은 승인 요구가 이 도구를 가리키는지이고, 저자의 승인 요구를 빼고 차례를 보려는
    쪽은 거짓을 넘긴다.
    """
    tables = _tables_for(rules, agent)
    if _any_matches((table.deny for table in tables), server, tool):
        return "deny"
    if requires_approval:
        return "requires_approval"
    if _any_matches((table.ask for table in tables), server, tool):
        return "ask"
    if _any_matches((table.allow for table in tables), server, tool):
        return "allow"
    return "default"


def unresolved_rule_lines(
    rules: Rules,
    *,
    agent: PluginName,
    servers: Collection[PluginName],
    specs: Sequence[ToolSpec],
) -> tuple[str, ...]:
    """그 에이전트의 표에 적힌 줄 가운데 연결에 실재하지 않는 것의 자리(질의).

    근거는 ADR 0044 이력 "그 에이전트의 표는 연결 뒤 대 본다"이다. 자리는
    `agents.<에이전트>.<deny·ask·allow>.<번호>` 이고 deny, ask, allow의 차례에 번호 순이다. 줄의
    글자는 싣지 않는다 — 맨 도구 이름 자리에는 어떤 글자든 들 수 있어 운영자가 잘못 적은 비밀이
    문구와 트레이스에 남을 수 있다(원칙 V). 번호를 모르는 값은 번호 없이 목록까지만 든다.

    `servers` 는 에이전트 매니페스트의 `mcp` 이고 `specs` 는 deny 로 빼기 전의 연결 전체다. 공통
    표는 여러 에이전트에 걸쳐 한 실행에서 다 대 볼 수 없어 보지 않는다. 도구 이름에 `*` 가 든 줄은
    도구가 지금 없어도 뜻이 있어 도구를 대 보지 않고, 서버가 든 줄은 그 서버가 `mcp` 에 있는지만
    본다.
    """
    own = rules.agents.get(agent)
    if own is None:
        return ()
    columns = (("deny", own.deny), ("ask", own.ask), ("allow", own.allow))
    return tuple(
        _place(agent, kind, rule)
        for kind, lines in columns
        for rule in sorted(lines, key=_position_of)
        if not _is_present(rule, servers, specs)
    )


def _position_of(rule: Rule) -> int:
    return -1 if rule.position is None else rule.position


def _place(agent: PluginName, kind: str, rule: Rule) -> str:
    place = f"agents.{agent}.{kind}"
    return place if rule.position is None else f"{place}.{rule.position}"


def _is_present(rule: Rule, servers: Collection[PluginName], specs: Sequence[ToolSpec]) -> bool:
    if rule.tool is not None and "*" in rule.tool:
        return rule.server is None or rule.server in servers
    if rule.tool is None:
        return rule.server in servers
    if rule.server is None:
        return any(spec.name == rule.tool for spec in specs)
    return any(spec.server == rule.server and spec.name == rule.tool for spec in specs)


def _tables_for(rules: Rules, agent: PluginName) -> tuple[RuleSet, ...]:
    """그 에이전트에 걸리는 표들(질의). 공통 표와, 있으면 그 에이전트의 표다."""
    own = rules.agents.get(agent)
    return (rules.common,) if own is None else (rules.common, own)


def _any_matches(columns: Iterable[frozenset[Rule]], server: PluginName, tool: str) -> bool:
    return any(rule.matches(server=server, tool=tool) for column in columns for rule in column)
