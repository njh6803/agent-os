"""tools/canary.py 의 카나리아 러너.

러너는 가짜다. 이벤트는 2026-10-07 에 손으로 돌린 카나리아 둘(claude 2.1.291, `--output-format
stream-json --verbose`, 규칙은 `--tools Read`, 스킬은 `--tools Skill`)의 모양을 따른다. init
의 `tools`·`mcp_servers`, assistant 의 `tool_use`(`Read` 의 `file_path`, `Skill` 의 `skill`),
스킬 본문이 실린 user 의 `Base directory for this skill:` 줄, 마지막 `result` 다. 에이전트
갈래의 이벤트는 2026-10-12 에 손으로 돌린 spec-reviewer 탐침(claude 2.1.292, 일지
2026-10-12-02)이 본 것을 따른다. init 의 `agents` 와 `Task` 로 찍힌 Agent, 서브에이전트의
`parent_tool_use_id`, Agent 결과의 `tool_use_result`(`status`, `totalToolUseCount`)다. `claude` 를
하위 프로세스로 부르는 실제 러너는 실제 실행으로 확인한다(`.claude/rules/tests.md`).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import replace
from pathlib import Path

import pytest
from tools.canary import (
    AgentOutcome,
    Facts,
    GitView,
    RunResult,
    SpecError,
    agent_problems,
    ancestor_problems,
    command,
    git_view,
    head_commit,
    judge,
    load_spec,
    main,
    mixed_none,
    prompt_for,
    read_facts,
    run_claude,
    source_problems,
    target_problems,
    view_problems,
)

_규칙_명세 = '''
kind = "rule"
question = """
Read 도구로 `{target}` 하나만 읽어라. 실린 지시에서 tools 의 식별자 언어를 옮겨라. 없으면 "없음".
"""
expect = ["식별자는 영문"]
source = ".claude/rules/tools.md"

[[arm]]
name = "실험군"
role = "experiment"
target = "tools/hook_env_read.py"

[[arm]]
name = "대조군"
role = "control"
target = "README.md"
'''

_스킬_명세 = """
kind = "skill"
question = "tidy-checkouts 스킬을 불러 부르는 곳 절의 도구 이름을 옮겨라. 없으면 \\"없음\\"."
expect = ["EnterWorktree"]
source = ".claude/skills/tidy-checkouts/SKILL.md"
skill = "tidy-checkouts"

[[arm]]
name = "새"
role = "experiment"
checkout = "새"

[[arm]]
name = "옛"
role = "control"
checkout = "옛"
"""


def _줄(event: dict[str, object]) -> str:
    return json.dumps(event, ensure_ascii=False)


def _init(
    tools: Sequence[str] = ("Read",), servers: Sequence[str] = (), agents: Sequence[str] = ()
) -> str:
    return _줄(
        {
            "type": "system",
            "subtype": "init",
            "tools": list(tools),
            "mcp_servers": [{"name": name, "status": "connected"} for name in servers],
            "agents": list(agents),
        }
    )


def _도구(name: str, arguments: dict[str, object], call_id: str = "toolu_0") -> str:
    block: dict[str, object] = {"type": "tool_use", "id": call_id, "name": name, "input": arguments}
    return _줄({"type": "assistant", "message": {"content": [block]}, "parent_tool_use_id": None})


def _읽기(path: Path | str) -> str:
    return _도구("Read", {"file_path": str(path)})


def _스킬_부름(name: str) -> str:
    return _도구("Skill", {"skill": name})


def _스킬_본문(folder: Path) -> str:
    text = f"Base directory for this skill: {folder}\n\n# 체크아웃 정리\n"
    return _줄({"type": "user", "message": {"content": [{"type": "text", "text": text}]}})


def _결과(text: str, subtype: str = "success", is_error: bool = False) -> str:
    return _줄({"type": "result", "subtype": subtype, "is_error": is_error, "result": text})


def _사실(
    *,
    tools: tuple[str, ...] | None = ("Read",),
    servers: tuple[str, ...] = (),
    reads: tuple[str, ...] = (),
    skills: tuple[str, ...] = (),
    skill_dirs: tuple[str, ...] = (),
    answer: str | None = "식별자는 영문, 문자열은 한국어",
    error: str | None = None,
) -> Facts:
    return Facts(tools, servers, reads, skills, skill_dirs, answer, error)


# 명세


def test_규칙_명세를_읽고_회차의_기본값은_실험군_셋_대조군_하나다() -> None:
    spec = load_spec(_규칙_명세)

    assert spec.kind == "rule"
    assert spec.model == "sonnet"
    assert [(arm.name, arm.role, arm.checkout, arm.times) for arm in spec.arm] == [
        ("실험군", "experiment", ".", 3),
        ("대조군", "control", ".", 1),
    ]


def test_회차를_주면_기본값_대신_그것을_쓴다() -> None:
    spec = load_spec(_규칙_명세.replace('role = "control"', 'role = "control"\nruns = 2'))

    assert [arm.times for arm in spec.arm] == [3, 2]


@pytest.mark.parametrize("빼는_역할", ["experiment", "control"])
def test_실험군이나_대조군이_없으면_명세_오류다(빼는_역할: str) -> None:
    남는_역할 = "control" if 빼는_역할 == "experiment" else "experiment"
    text = _규칙_명세.replace(f'role = "{빼는_역할}"', f'role = "{남는_역할}"')

    with pytest.raises(SpecError, match="실험군과 대조군"):
        load_spec(text)


def test_규칙_갈래에_대상이_없으면_명세_오류다() -> None:
    with pytest.raises(SpecError, match="target"):
        load_spec(_규칙_명세.replace('target = "README.md"\n', ""))


def test_규칙_질문에_대상_자리가_없으면_명세_오류다() -> None:
    with pytest.raises(SpecError, match="{target}"):
        load_spec(_규칙_명세.replace("`{target}`", "그 파일"))


def test_스킬_갈래에_대상을_주면_명세_오류다() -> None:
    text = _스킬_명세.replace('checkout = "옛"', 'checkout = "옛"\ntarget = "README.md"')

    with pytest.raises(SpecError, match="target"):
        load_spec(text)


def test_규칙_명세에_스킬을_주면_명세_오류다() -> None:
    with pytest.raises(SpecError, match="skill"):
        load_spec(
            _규칙_명세.replace(
                'expect = ["식별자는 영문"]', 'expect = ["식별자는 영문"]\nskill = "x"'
            )
        )


@pytest.mark.parametrize("이름", ["실험군", "a/b", "a\\b", "a:b", ""])
def test_갈래_이름이_겹치거나_경로_문자가_들면_명세_오류다(이름: str) -> None:
    with pytest.raises(SpecError):
        load_spec(_규칙_명세.replace('name = "대조군"', f'name = "{이름}"'.replace("\\", "\\\\")))


@pytest.mark.parametrize("카나리아", ["[]", '[""]', '["  "]'])
def test_카나리아가_비면_명세_오류다(카나리아: str) -> None:
    with pytest.raises(SpecError):
        load_spec(_규칙_명세.replace('["식별자는 영문"]', 카나리아))


def test_질문이_카나리아를_드러내면_명세_오류다() -> None:
    text = _규칙_명세.replace("tools 의 식별자 언어를 옮겨라", "`식별자는\n영문` 이 있는지 보라")

    with pytest.raises(SpecError, match="드러낸다"):
        load_spec(text)


def test_TOML이_틀리거나_모르는_칸이_있으면_명세_오류다() -> None:
    with pytest.raises(SpecError):
        load_spec("kind = ")
    with pytest.raises(SpecError):
        load_spec(_규칙_명세.replace('kind = "rule"', 'kind = "rule"\ndisallowed = "Read"'))


# 명령과 질문


def test_명령은_사용자_설정과_커넥터를_빼고_도구_하나로_좁히며_읽기_거부를_두지_않는다() -> None:
    rule = command(load_spec(_규칙_명세))
    skill = command(load_spec(_스킬_명세))

    assert rule[:2] == ["claude", "-p"]
    for flags in (["--setting-sources", "project,local"], ["--strict-mcp-config"]):
        assert any(rule[i : i + len(flags)] == flags for i in range(len(rule)))
    assert rule[rule.index("--model") + 1] == "sonnet"
    assert rule[rule.index("--tools") + 1] == "Read"
    assert skill[skill.index("--tools") + 1] == "Skill"
    assert rule[rule.index("--output-format") + 1] == "stream-json"
    assert "--verbose" in rule
    assert not any("disallowed" in part for part in rule)


def test_질문은_인자가_아니라_stdin으로_가고_대상_자리는_갈래의_대상으로_바뀐다() -> None:
    spec = load_spec(_규칙_명세)

    assert all("{target}" not in part and "Read 도구로" not in part for part in command(spec))
    assert "`tools/hook_env_read.py` 하나만" in prompt_for(spec, spec.arm[0])
    assert "`README.md` 하나만" in prompt_for(spec, spec.arm[1])


# 이벤트에서 사실 뽑기


def test_init의_도구와_서버_Read와_Skill_호출_스킬_위치_답을_뽑는다(tmp_path: Path) -> None:
    lines = [
        _init(("Read", "Skill"), ("Slack",)),
        _줄({"type": "rate_limit_event"}),
        _읽기(tmp_path / "a.py"),
        _스킬_부름("tidy-checkouts"),
        _스킬_본문(tmp_path / ".claude" / "skills" / "tidy-checkouts"),
        _줄({"type": "assistant", "message": {"content": [{"type": "text", "text": "중간"}]}}),
        _결과("EnterWorktree"),
    ]

    facts = read_facts(lines)

    assert facts == Facts(
        tools=("Read", "Skill"),
        servers=("Slack",),
        reads=(str(tmp_path / "a.py"),),
        skills=("tidy-checkouts",),
        skill_dirs=(str(tmp_path / ".claude" / "skills" / "tidy-checkouts"),),
        answer="EnterWorktree",
        error=None,
        calls=("Read", "Skill"),
    )


def test_JSON이_아닌_줄과_잘린_마지막_줄은_건너뛴다() -> None:
    facts = read_facts(["", "경고 한 줄", _init(), _결과("없음"), '{"type": "assi'])

    assert facts.tools == ("Read",)
    assert facts.answer == "없음"


def test_init이_없으면_도구는_None이다() -> None:
    assert read_facts([_결과("없음")]).tools is None


@pytest.mark.parametrize(("subtype", "is_error"), [("error_max_turns", False), ("success", True)])
def test_결과가_오류면_답_대신_오류를_적는다(subtype: str, is_error: bool) -> None:
    facts = read_facts([_init(), _결과("멈췄다", subtype, is_error)])

    assert facts.answer is None
    assert facts.error is not None and subtype in facts.error


def test_읽는_이벤트의_모양이_어긋나면_그_줄을_남기고_사실로_쓰지_않는다(tmp_path: Path) -> None:
    """모양이 어긋난 Read 를 조용히 건너뛰면 대상 밖 Read 를 놓쳐 거짓 통과가 난다(PR #157 리뷰)."""
    bad_read: dict[str, object] = {"type": "tool_use", "name": "Read", "input": "a.py"}
    lines = [
        _init(),
        _줄({"type": "assistant", "message": {"content": [bad_read]}}),
        _줄({"type": "result", "subtype": "success", "is_error": False, "result": 3}),
        _줄({"type": "system", "subtype": "init", "tools": "Read"}),
    ]

    facts = read_facts(lines)

    assert [line.split("번째", 1)[0] for line in facts.malformed] == ["2", "3", "4"]
    assert facts.reads == ()
    assert facts.answer is None
    assert facts.tools == ("Read",)


def test_읽지_않는_이벤트의_모양은_보지_않는다() -> None:
    odd: dict[str, object] = {"type": "rate_limit_event", "message": 3, "tools": "x"}
    facts = read_facts([_init(), _줄(odd), _결과("없음")])

    assert facts.malformed == ()
    assert facts.answer == "없음"


# 판정


def _규칙_판정(facts: Facts, checkout: Path, 갈래: int = 0) -> list[str]:
    spec = load_spec(_규칙_명세)
    return judge(spec, spec.arm[갈래], facts, checkout)


def test_규칙_실험군이_대상만_읽고_카나리아를_답하면_통과다(tmp_path: Path) -> None:
    facts = _사실(reads=(str(tmp_path / "tools" / "hook_env_read.py"),))

    assert _규칙_판정(facts, tmp_path) == []


def test_Read의_경로가_상대_경로여도_체크아웃_기준으로_대상과_견준다(tmp_path: Path) -> None:
    facts = _사실(reads=("tools/hook_env_read.py",))

    assert _규칙_판정(facts, tmp_path) == []


@pytest.mark.parametrize("답", ["없음", "없음.", "`없음`", '"없음"', "**없음**\n"])
def test_실험군이_없음이면_실패다(tmp_path: Path, 답: str) -> None:
    facts = _사실(reads=(str(tmp_path / "tools" / "hook_env_read.py"),), answer=답)

    assert any("없음" in reason for reason in _규칙_판정(facts, tmp_path))


def test_실험군_답에_카나리아가_없으면_실패다(tmp_path: Path) -> None:
    facts = _사실(reads=(str(tmp_path / "tools" / "hook_env_read.py"),), answer="영어로 쓴다")

    assert any("식별자는 영문" in reason for reason in _규칙_판정(facts, tmp_path))


def test_대상_밖의_파일을_읽으면_실패다(tmp_path: Path) -> None:
    대상 = str(tmp_path / "tools" / "hook_env_read.py")
    규칙 = str(tmp_path / ".claude" / "rules" / "tools.md")

    reasons = _규칙_판정(_사실(reads=(대상, 규칙)), tmp_path)

    assert any("tools.md" in reason for reason in reasons)


def test_Read를_부르지_않은_규칙_회차는_실패다(tmp_path: Path) -> None:
    assert any("Read" in reason for reason in _규칙_판정(_사실(reads=()), tmp_path))


@pytest.mark.parametrize("답", ["없음", "tools 의 언어를 정한 지시는 옛 사본에도 없다"])
def test_대조군은_답에_카나리아가_없으면_통과다(tmp_path: Path, 답: str) -> None:
    facts = _사실(reads=(str(tmp_path / "README.md"),), answer=답)

    assert _규칙_판정(facts, tmp_path, 갈래=1) == []


def test_대조군_답에_카나리아가_있으면_실패다(tmp_path: Path) -> None:
    facts = _사실(reads=(str(tmp_path / "README.md"),))

    assert any("대조군" in reason for reason in _규칙_판정(facts, tmp_path, 갈래=1))


# "없음" 섞임(대기열 212)


def _섞임(답: str | None, 갈래: int = 0, 명세: str = _규칙_명세) -> bool:
    spec = load_spec(명세)
    return mixed_none(spec, spec.arm[갈래], _사실(answer=답))


@pytest.mark.parametrize(
    "답",
    [
        "1. 없음\n2. 식별자는 영문, 문자열은 한국어",
        "**없음**. 다만 다른 절에 `식별자는 영문`이 있다",
    ],
)
def test_카나리아를_모두_담은_실험군_답에_없음이_섞이면_표시한다(답: str) -> None:
    assert _섞임(답)


@pytest.mark.parametrize("답", ["식별자는 영문, 문자열은 한국어", "없음", "**없음**\n"])
def test_없음이_섞이지_않았거나_답_전체가_없음이면_표시하지_않는다(답: str) -> None:
    """답 전체가 "없음"이면 판정이 실패로 센다. 표시는 통과 가운데 섞인 것만 가린다."""
    assert not _섞임(답)


def test_대조군의_없음과_답이_없는_회차는_표시하지_않는다() -> None:
    assert not _섞임("1. 없음\n2. 옛 지시", 갈래=1)
    assert not _섞임(None)


def test_카나리아_안의_없음은_섞임으로_보지_않는다() -> None:
    명세 = _규칙_명세.replace('expect = ["식별자는 영문"]', 'expect = ["지적 `없음`"]')

    assert not _섞임("리뷰는 `지적 없음`으로 닫는다", 명세=명세)
    assert _섞임("1. 없음\n2. 리뷰는 지적 없음으로 닫는다", 명세=명세)


def test_한_카나리아가_다른_카나리아를_품어도_긴_것부터_지워_섞임으로_보지_않는다() -> None:
    명세 = _규칙_명세.replace(
        'expect = ["식별자는 영문"]', 'expect = ["식별자는 영문", "식별자는 영문, 지적 없음"]'
    )

    assert not _섞임("식별자는 영문, 지적 없음", 명세=명세)


def test_없다_같은_다른_꼴은_섞임으로_보지_않고_지나간다() -> None:
    """못 보는 것: 글자 "없음"만 본다. 한 물음에 "없다"고 답한 회차는 표시하지 않는다."""
    assert not _섞임("1. 그런 문장은 없다\n2. 식별자는 영문")


def test_옮긴_본문에_든_없음도_표시한다() -> None:
    """거짓 양성: 물음에 "없음"이라 답하지 않고 본문을 옮겼어도 그 본문에 "없음"이 들면 표시한다."""
    assert _섞임("식별자는 영문이고, 예외가 없음을 확인한다")


@pytest.mark.parametrize(
    ("tools", "servers"),
    [(("Read", "Skill"), ()), (("Skill",), ()), (("Read",), ("Slack",))],
)
def test_도구가_그_하나가_아니거나_MCP_서버가_실리면_실패다(
    tmp_path: Path, tools: tuple[str, ...], servers: tuple[str, ...]
) -> None:
    facts = _사실(
        tools=tools, servers=servers, reads=(str(tmp_path / "tools" / "hook_env_read.py"),)
    )

    assert _규칙_판정(facts, tmp_path) != []


def test_init이_없거나_세션이_답을_내지_못하면_실패다(tmp_path: Path) -> None:
    대상 = (str(tmp_path / "tools" / "hook_env_read.py"),)

    assert any("init" in reason for reason in _규칙_판정(_사실(tools=None, reads=대상), tmp_path))
    오류 = _사실(reads=대상, answer=None, error="error_max_turns: 멈췄다")
    assert any("error_max_turns" in reason for reason in _규칙_판정(오류, tmp_path))


def test_모양이_어긋난_줄이_있으면_실패다(tmp_path: Path) -> None:
    facts = replace(
        _사실(reads=(str(tmp_path / "tools" / "hook_env_read.py"),)),
        malformed=("2번째 줄(assistant): message.content.0.input",),
    )

    assert any("모양" in reason for reason in _규칙_판정(facts, tmp_path))


def _스킬_판정(facts: Facts, checkout: Path) -> list[str]:
    spec = load_spec(_스킬_명세)
    return judge(spec, spec.arm[0], facts, checkout)


def _스킬_사실(checkout: Path, **바꿀: object) -> Facts:
    folder = str(checkout / ".claude" / "skills" / "tidy-checkouts")
    facts = _사실(
        tools=("Skill",), skills=("tidy-checkouts",), skill_dirs=(folder,), answer="EnterWorktree"
    )
    return replace(facts, **바꿀)


def test_스킬_실험군이_그_스킬을_이_체크아웃에서_싣고_카나리아를_답하면_통과다(
    tmp_path: Path,
) -> None:
    assert _스킬_판정(_스킬_사실(tmp_path), tmp_path) == []


def test_스킬을_부르지_않았으면_실패다(tmp_path: Path) -> None:
    """자리 줄은 두고 호출만 뺀다. 둘을 함께 빼면 자리 줄 판정만으로 빨강이 나 변이가 살아남았다."""
    facts = _스킬_사실(tmp_path, skills=())

    assert any("부르지 않았다" in reason for reason in _스킬_판정(facts, tmp_path))


def test_다른_체크아웃의_사본이_실리면_실패다(tmp_path: Path) -> None:
    """워크트리는 주 체크아웃 안에 있어 접두사 비교로는 가를 수 없다. 자리가 정확히 같아야 한다."""
    주 = tmp_path
    워크트리 = tmp_path / ".claude" / "worktrees" / "x"
    facts = _스킬_사실(주, skill_dirs=(str(워크트리 / ".claude" / "skills" / "tidy-checkouts"),))

    assert any("사본" in reason for reason in _스킬_판정(facts, 주))


@pytest.mark.parametrize("다른_스킬", [False, True])
def test_실험군이_스킬을_불렀어도_그_스킬이_실린_자리가_없으면_실패다(
    tmp_path: Path, 다른_스킬: bool
) -> None:
    """자리 줄을 뽑지 못하면 자리 판정이 조용히 빈다. 실험군은 그 스킬의 자리가 있어야 한다."""
    folders = (str(tmp_path / ".claude" / "skills" / "grilling"),) if 다른_스킬 else ()
    facts = _스킬_사실(tmp_path, skill_dirs=folders)

    assert any("자리" in reason for reason in _스킬_판정(facts, tmp_path))


def test_대조군은_스킬을_부르지_않아도_된다_새_스킬은_옛_사본에_없다(tmp_path: Path) -> None:
    spec = load_spec(_스킬_명세)
    facts = _스킬_사실(tmp_path, skills=(), skill_dirs=(), answer="없음")

    assert judge(spec, spec.arm[1], facts, tmp_path) == []


def test_대조군이_스킬을_불렀으면_그_체크아웃의_사본이어야_한다(tmp_path: Path) -> None:
    spec = load_spec(_스킬_명세)
    워크트리 = tmp_path / ".claude" / "worktrees" / "x"
    folder = str(워크트리 / ".claude" / "skills" / "tidy-checkouts")
    facts = _스킬_사실(tmp_path, skill_dirs=(folder,), answer="없음")

    assert any("사본" in reason for reason in judge(spec, spec.arm[1], facts, tmp_path))


def test_skill을_주지_않은_스킬_명세는_자리_줄이_없어도_통과다(tmp_path: Path) -> None:
    """슬래시 명령 길이다. 본문이 프롬프트에 펼쳐져 Skill 호출도 자리 줄도 남지 않는다."""
    spec = load_spec(_스킬_명세.replace('skill = "tidy-checkouts"\n', ""))
    facts = _스킬_사실(tmp_path, skills=(), skill_dirs=())

    assert judge(spec, spec.arm[0], facts, tmp_path) == []


def test_카나리아_대조는_백틱과_강조와_줄바꿈을_무시한다(tmp_path: Path) -> None:
    """표시가 카나리아 안쪽에 들어야 걷지 않을 때 어긋난다. 바깥에만 두면 변이가 살아남았다."""
    facts = _사실(
        reads=(str(tmp_path / "tools" / "hook_env_read.py"),),
        answer="> `tools/`의 **식별자는\n`영문`**, 문자열은 한국어다.",
    )

    assert _규칙_판정(facts, tmp_path) == []


def test_카나리아가_규칙_대상_파일에_있으면_답이_파일에서_올_수_있어_알린다(tmp_path: Path) -> None:
    spec = load_spec(_규칙_명세)
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "hook_env_read.py").write_text("# 식별자는 `영문`\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("안내\n", encoding="utf-8")

    assert target_problems(spec, spec.arm[0], tmp_path) != []
    assert target_problems(spec, spec.arm[1], tmp_path) == []


def test_실험군_사본의_원천에_카나리아가_없으면_알린다(tmp_path: Path) -> None:
    """질문이 원천에 없는 것을 물으면 맞는 답 "없음"을 실패로 잘못 읽는다(대기열 133)."""
    spec = load_spec(_스킬_명세)
    places = {"새": _스킬_체크아웃(tmp_path, "새", _옛_본문), "옛": _스킬_체크아웃(tmp_path, "옛")}

    problems = source_problems(spec, places)

    assert any(p.startswith("새") and "EnterWorktree" in p for p in problems)


def test_실험군_사본에_원천_파일이_없으면_알린다(tmp_path: Path) -> None:
    spec = load_spec(_스킬_명세)
    (tmp_path / "새").mkdir()
    places = {"새": tmp_path / "새", "옛": _스킬_체크아웃(tmp_path, "옛")}

    assert any(p.startswith("새") and "없다" in p for p in source_problems(spec, places))


def test_체크아웃이_다른_대조군_사본에_카나리아가_있으면_알린다(tmp_path: Path) -> None:
    spec = load_spec(_스킬_명세)
    places = {"새": _스킬_체크아웃(tmp_path, "새"), "옛": _스킬_체크아웃(tmp_path, "옛", _새_본문)}

    assert any(p.startswith("옛") and "EnterWorktree" in p for p in source_problems(spec, places))


def test_대조군_사본에_원천_파일이_없으면_새_스킬이라_괜찮다(tmp_path: Path) -> None:
    spec = load_spec(_스킬_명세)
    (tmp_path / "옛").mkdir()
    places = {"새": _스킬_체크아웃(tmp_path, "새"), "옛": tmp_path / "옛"}

    assert source_problems(spec, places) == []


def test_체크아웃이_같은_대조군은_원천을_다시_보지_않는다(tmp_path: Path) -> None:
    """규칙의 대조군은 같은 체크아웃의 paths 밖 파일을 읽는다. 원천은 새 사본 그대로다."""
    spec = load_spec(_규칙_명세)
    rules = tmp_path / ".claude" / "rules"
    rules.mkdir(parents=True)
    (rules / "tools.md").write_text("`tools/`의 **식별자는 영문**이다.\n", encoding="utf-8")

    assert source_problems(spec, {"실험군": tmp_path, "대조군": tmp_path}) == []


def test_스킬_명세에서_같은_체크아웃의_대조군은_새_사본이라_알린다(tmp_path: Path) -> None:
    """같은 체크아웃의 면제는 규칙에만 건다. 스킬의 대조군은 바뀌기 전 사본이어야 한다."""
    spec = load_spec(_스킬_명세)
    새 = _스킬_체크아웃(tmp_path, "새")

    problems = source_problems(spec, {"새": 새, "옛": 새})

    assert any(p.startswith("옛") and "새 사본" in p for p in problems)


def test_대조군_메시지는_카나리아가_바뀐_본문에만_있는_글이_아닐_수도_있다고_알린다(
    tmp_path: Path,
) -> None:
    """옛 사본의 다른 절에 같은 낱말이 있어도 막힌다. 원인이 둘이라 둘 다 적는다."""
    spec = load_spec(_스킬_명세)
    옛_본문 = _옛_본문 + "\n## 잠금\n\n`EnterWorktree` 이름이 잠금 사유에 든다.\n"
    places = {"새": _스킬_체크아웃(tmp_path, "새"), "옛": _스킬_체크아웃(tmp_path, "옛", 옛_본문)}

    problems = source_problems(spec, places)

    assert any(p.startswith("옛") and "바뀐 본문에만" in p for p in problems)


def test_skill을_주지_않은_슬래시_명령_명세도_원천을_본다(tmp_path: Path) -> None:
    """대기열 133의 사건이 난 길이다. 본문이 프롬프트에 펼쳐지는 스킬도 원천은 파일에 있다."""
    spec = load_spec(_스킬_명세.replace('skill = "tidy-checkouts"\n', ""))
    places = {"새": _스킬_체크아웃(tmp_path, "새", _옛_본문), "옛": _스킬_체크아웃(tmp_path, "옛")}

    assert any(p.startswith("새") and "EnterWorktree" in p for p in source_problems(spec, places))


def test_원천을_읽지_못하면_알린다(tmp_path: Path) -> None:
    spec = load_spec(_스킬_명세)
    새 = tmp_path / "새"
    (새 / ".claude" / "skills" / "tidy-checkouts" / "SKILL.md").mkdir(parents=True)
    places = {"새": 새, "옛": _스킬_체크아웃(tmp_path, "옛")}

    assert any(p.startswith("새") and "읽지 못했다" in p for p in source_problems(spec, places))


def test_원천_칸이_없으면_명세_오류다() -> None:
    with pytest.raises(SpecError, match="source"):
        load_spec(_규칙_명세.replace('source = ".claude/rules/tools.md"\n', ""))


def test_규칙_대상_파일이_없으면_알린다(tmp_path: Path) -> None:
    spec = load_spec(_규칙_명세)

    assert any("없다" in problem for problem in target_problems(spec, spec.arm[1], tmp_path))


# 에이전트 갈래

_에이전트_명세 = """
kind = "agent"
agent = "spec-reviewer"
agent_tools = ["Read", "Grep"]
question = "spec-reviewer 를 Agent 로 한 번 불러 체크리스트 6번의 끝 문장을 옮기게 하라."
expect = ["이음매로 잰다"]
source = ".claude/agents/spec-reviewer.md"

[[arm]]
name = "새"
role = "experiment"
checkout = "새"

[[arm]]
name = "옛"
role = "control"
checkout = "옛"
"""

_부른_id = "toolu_agent"


def _에이전트_부름(name: str = "Agent") -> str:
    arguments: dict[str, object] = {"subagent_type": "spec-reviewer", "prompt": "옮겨라"}
    return _도구(name, arguments, _부른_id)


def _에이전트_결과(outcome: object, call_id: str = _부른_id) -> str:
    block = {
        "type": "tool_result",
        "tool_use_id": call_id,
        "content": [{"type": "text", "text": "끝"}],
    }
    event: dict[str, object] = {
        "type": "user",
        "message": {"content": [block]},
        "parent_tool_use_id": None,
        "tool_use_result": outcome,
    }
    return _줄(event)


def _끝남(tool_uses: int | None = 0, status: str = "completed") -> dict[str, object]:
    outcome: dict[str, object] = {"status": status, "agentType": "spec-reviewer"}
    if tool_uses is not None:
        outcome["totalToolUseCount"] = tool_uses
    return outcome


def _서브(*blocks: dict[str, object]) -> str:
    """서브에이전트의 assistant 이벤트. 본 세션의 Agent 호출 id 를 `parent_tool_use_id` 로 단다."""
    return _줄(
        {"type": "assistant", "message": {"content": list(blocks)}, "parent_tool_use_id": _부른_id}
    )


def _글(text: str) -> dict[str, object]:
    return {"type": "text", "text": text}


def _서브_읽기() -> dict[str, object]:
    return {"type": "tool_use", "id": "toolu_sub", "name": "Read", "input": {"file_path": "x.md"}}


def _에이전트_사실(**바꿀: object) -> Facts:
    facts = replace(
        _사실(tools=("Agent", "Read", "Grep"), answer="> 6. **이음매로 잰다**."),
        agents=("spec-reviewer", "Explore"),
        calls=("Agent(spec-reviewer)",),
        outcomes=(AgentOutcome("spec-reviewer", "completed", 0),),
    )
    return replace(facts, **바꿀)


def _에이전트_판정(facts: Facts, checkout: Path, 갈래: int = 0) -> list[str]:
    spec = load_spec(_에이전트_명세)
    return judge(spec, spec.arm[갈래], facts, checkout)


def test_에이전트_명세를_읽는다() -> None:
    spec = load_spec(_에이전트_명세)

    assert (spec.kind, spec.agent, spec.agent_tools) == ("agent", "spec-reviewer", ["Read", "Grep"])


@pytest.mark.parametrize("뺄_줄", ['agent = "spec-reviewer"\n', 'agent_tools = ["Read", "Grep"]\n'])
def test_에이전트_명세에_에이전트나_그_도구가_없으면_명세_오류다(뺄_줄: str) -> None:
    with pytest.raises(SpecError, match="agent_tools"):
        load_spec(_에이전트_명세.replace(뺄_줄, ""))


@pytest.mark.parametrize("도구", ['["Agent", "Read"]', '["Task"]', "[]", '[""]'])
def test_에이전트_도구가_비었거나_Agent를_넣으면_명세_오류다(도구: str) -> None:
    """agent_tools 는 정의의 도구다. 본 세션의 Agent 는 러너가 더한다."""
    with pytest.raises(SpecError, match="agent_tools"):
        load_spec(_에이전트_명세.replace('["Read", "Grep"]', 도구))


def test_에이전트_갈래에_대상이나_스킬을_주면_명세_오류다() -> None:
    with pytest.raises(SpecError, match="target"):
        load_spec(
            _에이전트_명세.replace('checkout = "옛"', 'checkout = "옛"\ntarget = "README.md"')
        )
    with pytest.raises(SpecError, match="skill"):
        load_spec(_에이전트_명세.replace('kind = "agent"', 'kind = "agent"\nskill = "x"'))


@pytest.mark.parametrize("명세", [_규칙_명세, _스킬_명세])
@pytest.mark.parametrize("칸", ['agent = "x"', 'agent_tools = ["Read"]'])
def test_규칙과_스킬_명세에_에이전트_칸을_주면_명세_오류다(명세: str, 칸: str) -> None:
    with pytest.raises(SpecError, match="kind 가 agent"):
        load_spec(명세.replace("\n[[arm]]", f"\n{칸}\n\n[[arm]]", 1))


def test_에이전트_명령은_Agent와_정의의_도구로_좁힌다() -> None:
    """본 세션을 Agent 하나로 좁히자 서브에이전트가 도구 0개로 거부됐다(일지 2026-10-12-02)."""
    args = command(load_spec(_에이전트_명세))

    assert args[args.index("--tools") + 1] == "Agent,Read,Grep"
    assert "--strict-mcp-config" in args


def test_본_세션의_호출과_서브에이전트의_이벤트를_가른다() -> None:
    """서브에이전트의 Read 는 본 세션의 읽기가 아니다. init 은 Agent 를 옛 이름 Task 로 찍는다."""
    lines = [
        _init(("Task", "Read", "Grep"), agents=("spec-reviewer", "Explore")),
        _에이전트_부름(),
        _서브(_글("읽겠다"), _서브_읽기()),
        _서브(_글("이음매로 잰다")),
        _에이전트_결과(_끝남(1)),
        _결과("이음매로 잰다"),
    ]

    facts = read_facts(lines)

    assert facts.tools == ("Agent", "Read", "Grep")
    assert facts.agents == ("spec-reviewer", "Explore")
    assert facts.calls == ("Agent(spec-reviewer)",)
    assert facts.reads == ()
    assert (facts.sub_turns, facts.sub_calls) == (2, ("Read",))
    assert facts.outcomes == (AgentOutcome("spec-reviewer", "completed", 1),)
    assert facts.answer == "이음매로 잰다"


def test_Task로_찍힌_호출도_Agent로_읽는다() -> None:
    facts = read_facts([_init(("Task",)), _에이전트_부름("Task"), _에이전트_결과(_끝남())])

    assert facts.calls == ("Agent(spec-reviewer)",)
    assert facts.outcomes == (AgentOutcome("spec-reviewer", "completed", 0),)


def test_에이전트_결과가_문자열이면_오류로_남긴다() -> None:
    """도구 0개로 거부된 회차의 모양이다. 완료가 아니므로 돈 근거가 되지 않는다."""
    거부 = "Agent 'spec-reviewer' would be spawned with zero tools — refusing."

    facts = read_facts([_init(("Task",)), _에이전트_부름(), _에이전트_결과(거부)])

    assert len(facts.outcomes) == 1
    assert facts.outcomes[0].status.startswith("오류") and "zero tools" in facts.outcomes[0].status
    assert facts.malformed == ()


@pytest.mark.parametrize(
    "결과", [None, {"status": 3}, {"status": "completed", "totalToolUseCount": "많이"}]
)
def test_에이전트_결과의_모양이_어긋나면_그_줄을_남긴다(결과: object) -> None:
    facts = read_facts([_init(("Task",)), _에이전트_부름(), _에이전트_결과(결과)])

    assert facts.outcomes == ()
    assert [line.split("번째", 1)[0] for line in facts.malformed] == ["3"]


def test_거부된_회차의_넘긴_프롬프트는_서브에이전트가_돈_근거가_아니다(tmp_path: Path) -> None:
    """첫 판의 거짓 통과 자리다. 프롬프트는 `parent_tool_use_id` 를 단 user 이벤트로 찍혔다."""
    넘긴_프롬프트: dict[str, object] = {
        "type": "user",
        "message": {"content": "옮겨라"},
        "parent_tool_use_id": _부른_id,
    }
    거부 = "Agent 'spec-reviewer' would be spawned with zero tools — refusing."
    lines = [
        _init(("Task", "Read", "Grep"), agents=("spec-reviewer",)),
        _에이전트_부름(),
        _줄(넘긴_프롬프트),
        _에이전트_결과(거부),
        _결과("> 6. 이음매로 잰다"),
    ]

    facts = read_facts(lines)

    assert facts.sub_turns == 0
    assert any("근거" in reason for reason in _에이전트_판정(facts, tmp_path))


def test_결과_이벤트가_둘이면_답은_마지막_것이다() -> None:
    """백그라운드로 띄우면 본 세션이 먼저 한 번 답하고, 서브에이전트가 끝난 뒤 다시 답한다."""
    lines = [
        _init(("Task", "Read", "Grep"), agents=("spec-reviewer",)),
        _에이전트_부름(),
        _에이전트_결과(_끝남(None, "async_launched")),
        _결과("아직 끝나지 않아 답이 없다"),
        _서브(_글("이음매로 잰다")),
        _결과("이음매로 잰다"),
    ]

    assert read_facts(lines).answer == "이음매로 잰다"


def test_에이전트가_아닌_도구의_결과는_보지_않는다(tmp_path: Path) -> None:
    """규칙 회차의 Read 결과는 어떤 모양이든 사실도 어긋난 줄도 아니다."""
    읽은_결과 = _에이전트_결과("파일 내용", call_id="toolu_0")

    facts = read_facts([_init(), _읽기(tmp_path / "a.py"), 읽은_결과, _결과("없음")])

    assert facts.outcomes == ()
    assert facts.malformed == ()


def test_에이전트_실험군이_앞쪽으로_돌아_도구_없이_카나리아를_답하면_통과다(tmp_path: Path) -> None:
    """앞쪽 실행은 서브에이전트의 마지막 텍스트 답이 찍히지 않아 결과의 상태가 근거다."""
    assert _에이전트_판정(_에이전트_사실(), tmp_path) == []


def test_에이전트_실험군이_백그라운드로_돌아_도구_없이_답하면_통과다(tmp_path: Path) -> None:
    """백그라운드면 결과는 async_launched 이고 서브에이전트의 assistant 이벤트가 근거다."""
    launched = (AgentOutcome("spec-reviewer", "async_launched", None),)

    assert _에이전트_판정(_에이전트_사실(outcomes=launched, sub_turns=1), tmp_path) == []


def test_init의_도구는_Agent와_그_도구여야_하고_순서는_따지지_않는다(tmp_path: Path) -> None:
    assert _에이전트_판정(_에이전트_사실(tools=("Grep", "Agent", "Read")), tmp_path) == []
    reasons = _에이전트_판정(_에이전트_사실(tools=("Agent", "Read")), tmp_path)
    assert any("도구가" in reason for reason in reasons)


@pytest.mark.parametrize(
    "outcomes",
    [
        (),
        (AgentOutcome("spec-reviewer", "오류: zero tools — refusing", None),),
        (AgentOutcome("spec-reviewer", "failed", 0),),
        (AgentOutcome("spec-reviewer", "async_launched", None),),
        (AgentOutcome("Explore", "completed", 0),),
    ],
)
def test_서브에이전트가_돈_근거가_없으면_실패다(
    tmp_path: Path, outcomes: tuple[AgentOutcome, ...]
) -> None:
    """넘긴 프롬프트만 찍히고 서브에이전트가 돌지 않으면 도구 판정이 비어 통과할 수 있다."""
    reasons = _에이전트_판정(_에이전트_사실(outcomes=outcomes, sub_turns=0), tmp_path)

    assert any("근거" in reason for reason in reasons)


@pytest.mark.parametrize(
    "바꿀",
    [
        {"sub_turns": 1, "sub_calls": ("Read",)},
        {"outcomes": (AgentOutcome("spec-reviewer", "completed", 1),)},
        {"outcomes": (AgentOutcome("spec-reviewer", "completed", None),)},
    ],
)
def test_서브에이전트가_도구를_부르면_실패다(tmp_path: Path, 바꿀: dict[str, object]) -> None:
    """정의를 읽어 옮긴 답은 실린 지시가 아니다. 앞쪽 실행은 결과의 도구 횟수로만 보인다."""
    reasons = _에이전트_판정(_에이전트_사실(**바꿀), tmp_path)

    assert any("도구를 불렀다" in reason for reason in reasons)


@pytest.mark.parametrize(
    "calls", [("Agent(spec-reviewer)", "Read"), ("Agent(Explore)", "Agent(spec-reviewer)")]
)
def test_본_세션이_그_에이전트를_부르는_것_밖의_도구를_쓰면_실패다(
    tmp_path: Path, calls: tuple[str, ...]
) -> None:
    """본 세션이나 다른 서브에이전트가 정의를 읽어 옮겨도 카나리아는 맞는다(일지 2026-10-12-02)."""
    reasons = _에이전트_판정(_에이전트_사실(calls=calls), tmp_path)

    assert any("밖의" in reason for reason in reasons)


@pytest.mark.parametrize("calls", [(), ("Agent(spec-reviewer)", "Agent(spec-reviewer)")])
def test_그_에이전트를_한_번_부르지_않으면_실패다(tmp_path: Path, calls: tuple[str, ...]) -> None:
    reasons = _에이전트_판정(_에이전트_사실(calls=calls), tmp_path)

    assert any("한 번" in reason for reason in reasons)


def test_실험군_init에_그_에이전트가_없으면_실패다(tmp_path: Path) -> None:
    reasons = _에이전트_판정(_에이전트_사실(agents=("Explore",)), tmp_path)

    assert any("agents" in reason for reason in reasons)


def test_사본에_정의가_없는_대조군은_그_에이전트를_부르지_않아도_된다(tmp_path: Path) -> None:
    """새 서브에이전트는 옛 사본에 없다(대기열 153 의 첫 사건)."""
    facts = _에이전트_사실(agents=("Explore",), calls=(), outcomes=(), answer="없음")

    assert _에이전트_판정(facts, tmp_path, 갈래=1) == []


def test_사본에_정의가_있는_대조군은_그_에이전트가_실려_돌아야_한다(tmp_path: Path) -> None:
    """정의가 있는데 실리지 않은 대조군이 부르지 않고 "없음"만 답하면 질문을 시험하지 못한다."""
    옛 = _에이전트_체크아웃(tmp_path, "옛")
    facts = _에이전트_사실(agents=("Explore",), calls=(), outcomes=(), answer="없음")

    reasons = _에이전트_판정(facts, 옛, 갈래=1)

    assert any("agents" in reason for reason in reasons)
    assert any("한 번" in reason for reason in reasons)
    assert any("근거" in reason for reason in reasons)


def test_대조군도_그_에이전트가_실렸으면_한_번_불러_돌아야_한다(tmp_path: Path) -> None:
    """옛 정의가 실린 대조군은 서브에이전트가 옛 지시로 답해야 질문이 흘리지 않았다는 뜻이 선다."""
    reasons = _에이전트_판정(_에이전트_사실(calls=(), outcomes=(), answer="없음"), tmp_path, 갈래=1)

    assert any("한 번" in reason for reason in reasons)
    assert any("근거" in reason for reason in reasons)


def test_대조군도_본_세션이_에이전트_밖의_도구를_쓰면_실패다(tmp_path: Path) -> None:
    facts = _에이전트_사실(agents=(), calls=("Read",), outcomes=(), answer="없음")

    assert any("밖의" in reason for reason in _에이전트_판정(facts, tmp_path, 갈래=1))


def test_에이전트_대조군_답에_카나리아가_있으면_실패다(tmp_path: Path) -> None:
    assert any("대조군" in reason for reason in _에이전트_판정(_에이전트_사실(), tmp_path, 갈래=1))


_정의 = (
    "---\nname: spec-reviewer\ndescription: 검토한다\ntools: Read, Grep\n---\n\n6. 이음매로 잰다.\n"
)


def _에이전트_체크아웃(root: Path, 이름: str, 정의: str | None = _정의) -> Path:
    checkout = root / 이름
    folder = checkout / ".claude" / "agents"
    folder.mkdir(parents=True)
    if 정의 is not None:
        (folder / "spec-reviewer.md").write_text(정의, encoding="utf-8")
    return checkout


def test_에이전트_정의가_명세와_맞으면_알리지_않고_도구_순서는_따지지_않는다(
    tmp_path: Path,
) -> None:
    spec = load_spec(_에이전트_명세)
    places = {
        "새": _에이전트_체크아웃(tmp_path, "새", _정의.replace("Read, Grep", "Grep, Read")),
        "옛": _에이전트_체크아웃(tmp_path, "옛", None),
    }

    assert agent_problems(spec, places) == []


@pytest.mark.parametrize(
    ("바꿀", "표지"),
    [
        (("name: spec-reviewer", "name: other"), "name"),
        (("tools: Read, Grep", "tools: Read"), "tools"),
        (("tools: Read, Grep\n", ""), "tools"),
        (("---\nname", "name"), "머리말"),
    ],
)
def test_에이전트_실험군_정의가_명세와_다르면_알린다(
    tmp_path: Path, 바꿀: tuple[str, str], 표지: str
) -> None:
    """정의와 명세가 어긋나면 회차가 헛돈다. 돌리기 전에 막는다."""
    spec = load_spec(_에이전트_명세)
    places = {
        "새": _에이전트_체크아웃(tmp_path, "새", _정의.replace(*바꿀, 1)),
        "옛": _에이전트_체크아웃(tmp_path, "옛", None),
    }

    assert any(p.startswith("새") and 표지 in p for p in agent_problems(spec, places))


def test_대조군의_정의는_보지_않는다(tmp_path: Path) -> None:
    """옛 사본의 정의는 없거나 달라도 된다. 실렸는지는 init 의 agents 로 판정이 가른다."""
    spec = load_spec(_에이전트_명세)
    places = {
        "새": _에이전트_체크아웃(tmp_path, "새"),
        "옛": _에이전트_체크아웃(tmp_path, "옛", _정의.replace("Read, Grep", "Bash")),
    }

    assert agent_problems(spec, places) == []


# 상위 폴더의 CLAUDE.md(대기열 171)


def _절대_gitdir(gitdir: Path, checkout: Path) -> str:
    return gitdir.as_posix()


def _상대_gitdir(gitdir: Path, checkout: Path) -> str:
    return Path(os.path.relpath(gitdir, checkout)).as_posix()


def _연결된_워크트리(main_root: Path, 이름: str, 가리킴: Callable[[Path, Path], str]) -> Path:
    """`git worktree add` 가 남기는 모양. `.git` 은 주 저장소 안의 워크트리 자리를 가리킨다."""
    gitdir = main_root / ".git" / "worktrees" / 이름
    gitdir.mkdir(parents=True)
    checkout = main_root / ".claude" / "worktrees" / 이름
    checkout.mkdir(parents=True)
    (checkout / ".git").write_text(f"gitdir: {가리킴(gitdir, checkout)}\n", encoding="utf-8")
    return checkout


def test_상위_폴더의_CLAUDE_md에_카나리아가_있으면_갈래마다_알린다(tmp_path: Path) -> None:
    """상위 폴더의 CLAUDE.md 도 세션에 실린다(claude_md_parent.py). 대조군이면 답을 흘리고,
    실험군이면 통과가 그 파일에서 왔을 수 있다."""
    spec = load_spec(_스킬_명세)
    (tmp_path / "CLAUDE.md").write_text("`EnterWorktree` 를 먼저 부른다\n", encoding="utf-8")
    places = {"새": _스킬_체크아웃(tmp_path, "새"), "옛": _스킬_체크아웃(tmp_path, "옛")}

    problems = ancestor_problems(spec, places)

    assert [problem.split(":", 1)[0] for problem in problems] == ["새", "옛"]
    assert all(str(tmp_path / "CLAUDE.md") in problem for problem in problems)


def test_규칙_명세도_같은_체크아웃의_두_갈래에_상위_폴더_확인을_건다(tmp_path: Path) -> None:
    """확인은 kind 와 무관하다. 규칙의 대조군은 실험군과 같은 체크아웃이라 같은 상위 파일이
    실린다."""
    spec = load_spec(_규칙_명세)
    (tmp_path / "CLAUDE.md").write_text("`tools/`의 식별자는 영문이다\n", encoding="utf-8")
    checkout = tmp_path / "저장소"
    checkout.mkdir()

    problems = ancestor_problems(spec, {"실험군": checkout, "대조군": checkout})

    assert [problem.split(":", 1)[0] for problem in problems] == ["실험군", "대조군"]


def test_상위_폴더의_CLAUDE_md에_카나리아가_없으면_알리지_않는다(tmp_path: Path) -> None:
    spec = load_spec(_스킬_명세)
    (tmp_path / "CLAUDE.md").write_text("다른 지시\n", encoding="utf-8")
    places = {"새": _스킬_체크아웃(tmp_path, "새"), "옛": _스킬_체크아웃(tmp_path, "옛")}

    assert ancestor_problems(spec, places) == []


@pytest.mark.parametrize("가리킴", [_절대_gitdir, _상대_gitdir])
def test_연결된_워크트리는_주_워크트리_루트의_CLAUDE_md를_건너뛰고_그_위는_본다(
    tmp_path: Path, 가리킴: Callable[[Path, Path], str]
) -> None:
    """근거는 claude_md_parent.py 다."""
    spec = load_spec(_스킬_명세)
    주 = tmp_path / "agent"
    주.mkdir()
    (주 / "CLAUDE.md").write_text("`EnterWorktree`\n", encoding="utf-8")
    places = {"새": _스킬_체크아웃(tmp_path, "새"), "옛": _연결된_워크트리(주, "옛", 가리킴)}

    assert ancestor_problems(spec, places) == []

    (tmp_path / "CLAUDE.md").write_text("`EnterWorktree`\n", encoding="utf-8")
    problems = ancestor_problems(spec, places)

    assert any(p.startswith("옛") and str(tmp_path / "CLAUDE.md") in p for p in problems)
    assert not any(str(주 / "CLAUDE.md") in problem for problem in problems)


def test_워크트리가_아닌_하위_폴더는_주_저장소의_CLAUDE_md도_본다(tmp_path: Path) -> None:
    """git 루트에서 멈추지 않는다(claude_md_parent.py)."""
    spec = load_spec(_스킬_명세)
    주 = tmp_path / "agent"
    (주 / ".git").mkdir(parents=True)
    (주 / "CLAUDE.md").write_text("`EnterWorktree`\n", encoding="utf-8")
    places = {"새": _스킬_체크아웃(tmp_path, "새"), "옛": _스킬_체크아웃(주, "옛")}

    problems = ancestor_problems(spec, places)

    assert any(p.startswith("옛") and str(주 / "CLAUDE.md") in p for p in problems)


# 세션에 실리는 git 상태


def _커밋(repo: Path, 제목: str) -> None:
    identity = ("-c", "user.name=t", "-c", "user.email=t@example.com")
    _git(repo, *identity, "commit", "-q", "--allow-empty", "-m", 제목)


def test_git_상태는_바뀐_경로와_지금_브랜치와_최근_커밋_다섯의_제목이다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """실제 git 으로 잰다. 추적하지 않는 폴더는 세션의 블록처럼 폴더 이름만 든다
    (`canary_git_status.py`). 이름을 바꾼 것의 앞뒤 둘과 따옴표·8진 이스케이프 없는 한글 경로는
    세션이 보는 꼴을 재지 않고 더 막는 쪽으로 고른 것이다(러너 독스트링의 못 보는 것)."""
    repo = _저장소(tmp_path, monkeypatch)
    (repo / "고칠.md").write_text("처음\n", encoding="utf-8")
    (repo / "옮길.md").write_text("옮긴다\n", encoding="utf-8")
    _git(repo, "add", ".")
    _커밋(repo, "제목 c1")
    _git(repo, "switch", "-q", "-c", "chore/표지-브랜치")
    for 차례 in range(2, 8):
        _커밋(repo, f"제목 c{차례}")
    (repo / "고칠.md").write_text("고침\n", encoding="utf-8")
    _git(repo, "mv", "옮길.md", "옮긴.md")
    (repo / "추적하지_않는.md").write_text("새\n", encoding="utf-8")
    (repo / "새_폴더").mkdir()
    (repo / "새_폴더" / "안쪽.md").write_text("안\n", encoding="utf-8")

    view = git_view(repo)

    assert view is not None
    assert sorted(view.paths) == sorted(
        ["고칠.md", "옮긴.md", "옮길.md", "추적하지_않는.md", "새_폴더/"]
    )
    assert view.branch == "chore/표지-브랜치"
    assert view.subjects == ("제목 c7", "제목 c6", "제목 c5", "제목 c4", "제목 c3")


def test_저장소_밖의_git_상태는_비었다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """세션의 컨텍스트에도 git 상태 블록이 없다(`canary_git_status.py` 의 보통 폴더)."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    밖 = tmp_path / "밖"
    밖.mkdir()
    (밖 / "EnterWorktree.md").write_text("새\n", encoding="utf-8")

    assert git_view(밖) == GitView()


def test_커밋이_없는_저장소는_제목이_없고_분리_HEAD는_브랜치가_없다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _저장소(tmp_path, monkeypatch)
    (repo / "새.md").write_text("새\n", encoding="utf-8")

    빈 = git_view(repo)
    _git(repo, "add", ".")
    _커밋(repo, "첫")
    _git(repo, "switch", "-q", "--detach")
    분리 = git_view(repo)

    assert 빈 is not None
    assert 빈.paths == ("새.md",)
    assert 빈.subjects == ()
    assert 분리 == GitView((), "", ("첫",))


@pytest.mark.parametrize("멈출_명령", ["status", "branch", "log"])
def test_git이_하나라도_제한_시간을_넘기면_git_상태는_None이다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, 멈출_명령: str
) -> None:
    def 멈추는_git(args: Sequence[str], **_: object) -> subprocess.CompletedProcess[bytes]:
        if args[3] == 멈출_명령:  # git -C <체크아웃> <명령>
            raise subprocess.TimeoutExpired(args, 30.0)
        return subprocess.CompletedProcess(args, 0, b"", b"")

    monkeypatch.setattr(subprocess, "run", 멈추는_git)

    assert git_view(tmp_path) is None


def test_git을_띄우지_못하면_git_상태는_None이다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def 없는_곳(name: str) -> str:
        return str(tmp_path / f"없는-{name}")

    monkeypatch.setattr(shutil, "which", 없는_곳)

    assert git_view(tmp_path) is None


class _가짜_상태:
    """체크아웃 폴더 이름마다 정한 git 상태를 돌려주고 읽은 폴더를 적는다."""

    def __init__(self, 상태들: dict[str, GitView | None]) -> None:
        self.상태들 = 상태들
        self.읽은: list[str] = []

    def __call__(self, checkout: Path) -> GitView | None:
        self.읽은.append(checkout.name)
        return self.상태들[checkout.name]


_훅_명세 = _스킬_명세.replace('expect = ["EnterWorktree"]', 'expect = ["`hook_push_behind_main`"]')


@pytest.mark.parametrize(
    ("상태", "자리"),
    [
        (GitView(paths=("README.md", "tools/hook_push_behind_main.py")), "바뀐 경로"),
        (GitView(branch="chore/hook_push_behind_main"), "브랜치"),
        (
            GitView(subjects=("chore: 다른 것", "feat: hook_push_behind_main 을 더한다")),
            "커밋 제목",
        ),
    ],
)
def test_세션에_실리는_git_상태에_카나리아가_있으면_그_갈래와_자리를_알린다(
    tmp_path: Path, 상태: GitView, 자리: str
) -> None:
    """대기열 243 의 사건: 커밋하지 않은 훅 파일의 이름이 대조군 답에 샜다. 백틱은 걷고 견준다."""
    spec = load_spec(_훅_명세)
    places = {"새": _스킬_체크아웃(tmp_path, "새"), "옛": _스킬_체크아웃(tmp_path, "옛")}

    problems = view_problems(spec, places, _가짜_상태({"새": GitView(), "옛": 상태}))

    assert len(problems) == 1
    assert problems[0].startswith("옛: ")
    assert f"git 상태의 {자리} " in problems[0]
    assert "hook_push_behind_main" in problems[0]


def test_git_상태에_카나리아가_없으면_알리지_않는다(tmp_path: Path) -> None:
    spec = load_spec(_훅_명세)
    places = {"새": _스킬_체크아웃(tmp_path, "새"), "옛": _스킬_체크아웃(tmp_path, "옛")}
    상태 = GitView(("tools/hook_env_read.py",), "chore/push", ("feat: 훅을 더한다",))

    assert view_problems(spec, places, _가짜_상태({"새": 상태, "옛": 상태})) == []


def test_git_상태를_읽지_못하면_확인이_비지_않게_그_갈래를_막는다(tmp_path: Path) -> None:
    spec = load_spec(_훅_명세)
    places = {"새": _스킬_체크아웃(tmp_path, "새"), "옛": _스킬_체크아웃(tmp_path, "옛")}

    problems = view_problems(spec, places, _가짜_상태({"새": GitView(), "옛": None}))

    assert len(problems) == 1
    assert problems[0].startswith("옛: ")
    assert "읽지 못했다" in problems[0]


def test_같은_체크아웃의_git_상태는_한_번만_읽고_갈래마다_알린다(tmp_path: Path) -> None:
    spec = load_spec(_규칙_명세)
    places = {"실험군": tmp_path, "대조군": tmp_path}
    상태 = _가짜_상태({tmp_path.name: GitView(paths=("식별자는 영문.md",))})

    problems = view_problems(spec, places, 상태)

    assert 상태.읽은 == [tmp_path.name]
    assert [problem.split(":")[0] for problem in problems] == ["실험군", "대조군"]


def test_체크아웃이_없는_갈래의_git_상태는_읽지_않는다(tmp_path: Path) -> None:
    spec = load_spec(_훅_명세)
    places = {"새": _스킬_체크아웃(tmp_path, "새"), "옛": tmp_path / "옛"}
    상태 = _가짜_상태({"새": GitView()})

    assert view_problems(spec, places, 상태) == []
    assert 상태.읽은 == ["새"]


@pytest.mark.parametrize("명세", [_규칙_명세, _스킬_명세, _에이전트_명세])
def test_git_상태는_명세의_종류와_상관없이_갈래마다_본다(tmp_path: Path, 명세: str) -> None:
    """못 보는 것. 스킬·서브에이전트 명령의 세션에 실리는지는 재지 않았고 규칙 명령과 같다고 보고
    본다."""
    spec = load_spec(명세)
    places: dict[str, Path] = {}
    for arm in spec.arm:
        places[arm.name] = tmp_path / f"갈래-{len(places)}"
        places[arm.name].mkdir()
    상태 = GitView(paths=(f"{spec.expect[0]}.md",))

    problems = view_problems(spec, places, lambda _: 상태)

    assert [problem.split(":")[0] for problem in problems] == [arm.name for arm in spec.arm]


def test_주_브랜치와_git_사용자_이름은_견주지_않는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """못 보는 것(지나간다). 세션의 블록에는 둘도 실리지만(`canary_git_status.py`) 읽지 않는다."""
    repo = _저장소(tmp_path, monkeypatch)
    _git(repo, "config", "user.name", "사용자-표지")
    _커밋(repo, "첫")
    _git(repo, "branch", "주가지-표지")
    _git(repo, "switch", "-q", "-c", "feat/다른")
    spec = load_spec(_스킬_명세.replace('["EnterWorktree"]', '["사용자-표지", "주가지-표지"]'))

    problems = view_problems(spec, {"새": repo, "옛": repo}, git_view)

    assert problems == []


def test_세션이_자를_만큼_긴_상태도_끝까지_견주어_막는다(tmp_path: Path) -> None:
    """못 보는 것(막는다). 세션은 긴 상태를 자르지만 이 확인은 자르지 않는다."""
    spec = load_spec(_훅_명세)
    places = {"새": _스킬_체크아웃(tmp_path, "새"), "옛": _스킬_체크아웃(tmp_path, "옛")}
    긴_경로들 = tuple(f"web/src/긴-폴더-{차례:03d}/파일.ts" for 차례 in range(200))
    상태 = GitView(paths=(*긴_경로들, "tools/hook_push_behind_main.py"))

    problems = view_problems(spec, places, _가짜_상태({"새": GitView(), "옛": 상태}))

    assert sum(len(path) for path in 상태.paths) > 2000
    assert len(problems) == 1
    assert "tools/hook_push_behind_main.py" in problems[0]


# 실행


class _가짜:
    """체크아웃 폴더 이름마다 정한 이벤트를 돌려주고 받은 호출을 적는다."""

    def __init__(self, 답들: dict[str, list[str]], exit_code: int = 0) -> None:
        self.답들 = 답들
        self.exit_code = exit_code
        self.호출: list[tuple[list[str], Path, str]] = []

    def __call__(self, args: Sequence[str], cwd: Path, stdin: str) -> RunResult:
        self.호출.append((list(args), cwd, stdin))
        return RunResult(self.exit_code, "\n".join(self.답들[cwd.name]) + "\n", "")


_새_본문 = "## 부르는 곳\n\n새 세션이 첫 턴에 `EnterWorktree`보다 먼저 부른다.\n"
_옛_본문 = "## 부르는 곳\n\n사람이 아무 때나 친다.\n"


def _스킬_체크아웃(root: Path, 이름: str, 본문: str | None = None) -> Path:
    """`SKILL.md` 를 둔 체크아웃. 본문을 주지 않으면 "새" 만 카나리아가 든 새 사본이다."""
    checkout = root / 이름
    folder = checkout / ".claude" / "skills" / "tidy-checkouts"
    folder.mkdir(parents=True)
    text = 본문 if 본문 is not None else (_새_본문 if 이름 == "새" else _옛_본문)
    (folder / "SKILL.md").write_text(text, encoding="utf-8")
    return checkout


def _스킬_회차(checkout: Path, 답: str) -> list[str]:
    folder = checkout / ".claude" / "skills" / "tidy-checkouts"
    return [_init(("Skill",)), _스킬_부름("tidy-checkouts"), _스킬_본문(folder), _결과(답)]


class _가짜_커밋:
    """체크아웃 폴더 이름마다 부를 때마다 차례로 커밋을 돌려준다. 다 쓰면 마지막 것을 되풀이한다."""

    def __init__(self, 커밋들: dict[str, list[str | None]]) -> None:
        self.커밋들 = 커밋들
        self.부른_수: dict[str, int] = {}

    def __call__(self, checkout: Path) -> str | None:
        차례 = self.부른_수.get(checkout.name, 0)
        self.부른_수[checkout.name] = 차례 + 1
        커밋들 = self.커밋들[checkout.name]
        return 커밋들[min(차례, len(커밋들) - 1)]


def _스킬_실행(
    tmp_path: Path,
    새_답: str,
    옛_답: str,
    exit_code: int = 0,
    commit: _가짜_커밋 | None = None,
) -> tuple[int, list[str], _가짜]:
    spec_path = tmp_path / "canary.toml"
    spec_path.write_text(_스킬_명세, encoding="utf-8")
    새 = _스킬_체크아웃(tmp_path, "새")
    옛 = _스킬_체크아웃(tmp_path, "옛")
    가짜 = _가짜({"새": _스킬_회차(새, 새_답), "옛": _스킬_회차(옛, 옛_답)}, exit_code)
    printed: list[str] = []
    code = main(
        [str(spec_path), str(tmp_path / "out")],
        cwd=tmp_path,
        runner=가짜,
        out=printed.append,
        commit=commit or _가짜_커밋({"새": ["aaa1111"], "옛": ["bbb2222"]}),
    )
    return code, printed, 가짜


def test_모두_통과하면_0이고_갈래마다_회차를_돌려_원본을_남긴다(tmp_path: Path) -> None:
    code, printed, 가짜 = _스킬_실행(tmp_path, "EnterWorktree", "없음")

    assert code == 0
    assert sorted((cwd.name, stdin) for _, cwd, stdin in 가짜.호출) == [
        ("새", load_spec(_스킬_명세).question)
    ] * 3 + [("옛", load_spec(_스킬_명세).question)]
    names = sorted(path.name for path in (tmp_path / "out").iterdir())
    assert names == [
        "새-1.err",
        "새-1.jsonl",
        "새-2.err",
        "새-2.jsonl",
        "새-3.err",
        "새-3.jsonl",
        "옛-1.err",
        "옛-1.jsonl",
    ]
    assert "EnterWorktree" in (tmp_path / "out" / "새-2.jsonl").read_text(encoding="utf-8")
    assert any("통과 4" in line for line in printed)


def test_하나라도_실패하면_1이고_그_회차와_이유를_찍는다(tmp_path: Path) -> None:
    code, printed, _ = _스킬_실행(tmp_path, "EnterWorktree", "옛 줄\nEnterWorktree 를 부른다")

    assert code == 1
    assert any("옛" in line and "대조군" in line for line in printed)
    assert "    EnterWorktree 를 부른다" in printed


def test_답은_자르지_않고_줄마다_들여_찍는다(tmp_path: Path) -> None:
    긴_줄 = "EnterWorktree 보다 먼저 " + "가" * 300

    code, printed, _ = _스킬_실행(tmp_path, f"1. 없음\n\n2. {긴_줄}", "없음")

    assert code == 0
    assert printed.count(f"    2. {긴_줄}") == 3
    assert printed.count("    1. 없음") == 3
    assert printed.count("    없음") == 1
    assert not any("…" in line for line in printed)


def test_없음이_섞인_통과는_판정_줄과_요약에_표시하되_종료_코드는_0이다(tmp_path: Path) -> None:
    code, printed, _ = _스킬_실행(tmp_path, "1. 없음\n2. EnterWorktree", "없음")

    assert code == 0
    marked = [line for line in printed if line.startswith('[통과·"없음" 섞임]')]
    assert len(marked) == 3
    assert all("새(실험군)" in line for line in marked)
    assert any(line.startswith('통과 4 · 실패 0 · "없음" 섞인 통과 3') for line in printed)


def test_섞이지_않은_통과와_실패한_회차는_표시하지_않고_요약에_섞임_0을_찍는다(
    tmp_path: Path,
) -> None:
    (tmp_path / "깨끗").mkdir()
    (tmp_path / "실패").mkdir()
    _, 깨끗한, _ = _스킬_실행(tmp_path / "깨끗", "EnterWorktree", "없음")
    code, 실패한, _ = _스킬_실행(tmp_path / "실패", "1. 없음\n2. 사람이 친다", "없음")

    assert code == 1
    for printed in (깨끗한, 실패한):
        assert not any("섞임]" in line for line in printed)
        assert any('"없음" 섞인 통과 0' in line for line in printed)


def _판정_줄(printed: list[str], 갈래: str) -> list[str]:
    return [line for line in printed if line.startswith("[") and f"{갈래}(" in line]


def test_갈래마다_체크아웃의_커밋을_회차_줄과_요약에_찍는다(tmp_path: Path) -> None:
    code, printed, _ = _스킬_실행(tmp_path, "EnterWorktree", "없음")

    assert code == 0
    assert len(_판정_줄(printed, "새")) == 3
    assert all(line.endswith(" · 커밋 aaa1111") for line in _판정_줄(printed, "새"))
    assert [line.endswith(" · 커밋 bbb2222") for line in _판정_줄(printed, "옛")] == [True]
    assert "갈래: 새(실험군) 커밋 aaa1111 · 옛(대조군) 커밋 bbb2222" in printed


def test_도는_동안_커밋이_움직이면_앞뒤를_찍는다(tmp_path: Path) -> None:
    commit = _가짜_커밋({"새": ["aaa1111"], "옛": ["bbb2222", "ccc3333"]})

    _, printed, _ = _스킬_실행(tmp_path, "EnterWorktree", "없음", commit=commit)

    moved = "커밋 bbb2222 → ccc3333(도는 동안 움직였다)"
    assert [line.endswith(moved) for line in _판정_줄(printed, "옛")] == [True]
    assert f"갈래: 새(실험군) 커밋 aaa1111 · 옛(대조군) {moved}" in printed
    assert commit.부른_수 == {"새": 2, "옛": 2}


@pytest.mark.parametrize(
    ("앞뒤", "적힌"),
    [
        ([None], "커밋 모름"),
        ([None, "ccc3333"], "커밋 모름 → ccc3333(한쪽을 읽지 못해 움직였는지 모른다)"),
        (["bbb2222", None], "커밋 bbb2222 → 모름(한쪽을 읽지 못해 움직였는지 모른다)"),
    ],
)
def test_커밋을_읽지_못하면_모른다고_찍고_한쪽만_읽었으면_움직였다고_하지_않는다(
    tmp_path: Path, 앞뒤: list[str | None], 적힌: str
) -> None:
    commit = _가짜_커밋({"새": ["aaa1111"], "옛": 앞뒤})

    _, printed, _ = _스킬_실행(tmp_path, "EnterWorktree", "없음", commit=commit)

    assert [line.endswith(f" · {적힌}") for line in _판정_줄(printed, "옛")] == [True]
    assert f"갈래: 새(실험군) 커밋 aaa1111 · 옛(대조군) {적힌}" in printed


def test_빈_답은_비었다고_찍는다(tmp_path: Path) -> None:
    code, printed, _ = _스킬_실행(tmp_path, "EnterWorktree", "")

    assert code == 0
    assert printed.count("  답: (비었다)") == 1


def test_공백뿐인_답도_비었다고_찍는다(tmp_path: Path) -> None:
    code, printed, _ = _스킬_실행(tmp_path, "EnterWorktree", "  \n \n")

    assert code == 0
    assert printed.count("  답: (비었다)") == 1


def _저장소(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """`tmp_path/repo` 에 빈 저장소를 만든다. `tmp_path` 위의 저장소는 git 이 찾지 않게 막는다."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    return repo


def test_HEAD_커밋은_git의_짧은_꼴이고_하위_폴더는_그_저장소의_것이며_저장소_밖은_None이다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """실제 git 으로 잰다. 못 보는 것: 커밋하지 않은 변경이 있어도 `HEAD` 만 찍는다."""
    repo = _저장소(tmp_path, monkeypatch)
    (repo / "a.md").write_bytes(b"a\n")
    _git(repo, "add", ".")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-m", "a")
    short = _git(repo, "rev-parse", "--short", "HEAD")
    (repo / "a.md").write_bytes(b"b\n")
    (repo / "하위").mkdir()
    빈 = tmp_path / "빈"
    빈.mkdir()

    assert head_commit(repo) == short
    assert head_commit(repo / "하위") == short
    assert head_commit(빈) is None
    assert head_commit(tmp_path / "없는") is None


def test_커밋이_없는_저장소의_커밋은_None이다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert head_commit(_저장소(tmp_path, monkeypatch)) is None


def test_git을_띄우지_못하면_커밋은_None이다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def 없는_곳(name: str) -> str:
        return str(tmp_path / f"없는-{name}")

    monkeypatch.setattr(shutil, "which", 없는_곳)

    assert head_commit(tmp_path) is None


def test_git이_제한_시간을_넘기면_커밋은_None이다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def 멈춘_git(args: Sequence[str], **_: object) -> subprocess.CompletedProcess[bytes]:
        raise subprocess.TimeoutExpired(args, 30.0)

    monkeypatch.setattr(subprocess, "run", 멈춘_git)

    assert head_commit(tmp_path) is None


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True, encoding="utf-8"
    )
    return result.stdout.strip()


def test_claude가_0이_아닌_코드로_끝나면_그_회차는_실패다(tmp_path: Path) -> None:
    code, printed, _ = _스킬_실행(tmp_path, "EnterWorktree", "없음", exit_code=1)

    assert code == 1
    assert any("종료 코드 1" in line for line in printed)


def test_명세_오류면_아무것도_돌리지_않고_2다(tmp_path: Path) -> None:
    spec_path = tmp_path / "canary.toml"
    spec_path.write_text("kind = ", encoding="utf-8")
    가짜 = _가짜({})
    printed: list[str] = []

    assert (
        main([str(spec_path), str(tmp_path / "out")], cwd=tmp_path, runner=가짜, out=printed.append)
        == 2
    )
    assert 가짜.호출 == []


def test_카나리아가_규칙_대상_파일에_있으면_돌리지_않고_2다(tmp_path: Path) -> None:
    spec_path = tmp_path / "canary.toml"
    spec_path.write_text(_규칙_명세, encoding="utf-8")
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "hook_env_read.py").write_text("# 식별자는 영문\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("안내\n", encoding="utf-8")
    가짜 = _가짜({})
    printed: list[str] = []

    assert (
        main([str(spec_path), str(tmp_path / "out")], cwd=tmp_path, runner=가짜, out=printed.append)
        == 2
    )
    assert 가짜.호출 == []
    assert any("hook_env_read.py" in line for line in printed)


def test_갈래의_체크아웃이_없으면_돌리지_않고_2다(tmp_path: Path) -> None:
    spec_path = tmp_path / "canary.toml"
    spec_path.write_text(_스킬_명세, encoding="utf-8")
    _스킬_체크아웃(tmp_path, "새")
    가짜 = _가짜({})
    printed: list[str] = []

    assert (
        main([str(spec_path), str(tmp_path / "out")], cwd=tmp_path, runner=가짜, out=printed.append)
        == 2
    )
    assert 가짜.호출 == []
    assert any("옛" in line for line in printed)


def test_claude를_띄우지_못하면_3이고_원인을_찍는다(tmp_path: Path) -> None:
    spec_path = tmp_path / "canary.toml"
    spec_path.write_text(_스킬_명세, encoding="utf-8")
    _스킬_체크아웃(tmp_path, "새")
    _스킬_체크아웃(tmp_path, "옛")
    printed: list[str] = []

    def 없는_claude(args: Sequence[str], cwd: Path, stdin: str) -> RunResult:
        raise FileNotFoundError(f"{args[0]} 없음")

    code = main(
        [str(spec_path), str(tmp_path / "out")],
        cwd=tmp_path,
        runner=없는_claude,
        out=printed.append,
    )

    assert code == 3
    assert any("claude 없음" in line for line in printed)


def test_원천이_어긋나면_돌리지_않고_2다(tmp_path: Path) -> None:
    spec_path = tmp_path / "canary.toml"
    spec_path.write_text(_스킬_명세, encoding="utf-8")
    _스킬_체크아웃(tmp_path, "새", _옛_본문)
    _스킬_체크아웃(tmp_path, "옛")
    가짜 = _가짜({})
    printed: list[str] = []

    code = main(
        [str(spec_path), str(tmp_path / "out")], cwd=tmp_path, runner=가짜, out=printed.append
    )

    assert code == 2
    assert 가짜.호출 == []
    assert any("원천" in line for line in printed)


def test_출력_디렉터리를_만들지_못하면_3이다(tmp_path: Path) -> None:
    spec_path = tmp_path / "canary.toml"
    spec_path.write_text(_스킬_명세, encoding="utf-8")
    _스킬_체크아웃(tmp_path, "새")
    _스킬_체크아웃(tmp_path, "옛")
    (tmp_path / "out").write_text("디렉터리가 아니다", encoding="utf-8")
    가짜 = _가짜({})
    printed: list[str] = []

    code = main(
        [str(spec_path), str(tmp_path / "out")], cwd=tmp_path, runner=가짜, out=printed.append
    )

    assert code == 3
    assert 가짜.호출 == []
    assert any("출력" in line for line in printed)


def test_원본을_쓰지_못하면_3이다(tmp_path: Path) -> None:
    """회차는 돌았지만 원본 자리를 폴더로 막아 쓰기가 실패한다. 종료 코드 표 밖으로 새지 않는다."""
    spec_path = tmp_path / "canary.toml"
    spec_path.write_text(_스킬_명세, encoding="utf-8")
    새 = _스킬_체크아웃(tmp_path, "새")
    옛 = _스킬_체크아웃(tmp_path, "옛")
    (tmp_path / "out" / "새-1.jsonl").mkdir(parents=True)
    가짜 = _가짜({"새": _스킬_회차(새, "EnterWorktree"), "옛": _스킬_회차(옛, "없음")})
    printed: list[str] = []

    code = main(
        [str(spec_path), str(tmp_path / "out")], cwd=tmp_path, runner=가짜, out=printed.append
    )

    assert code == 3
    assert any("원본" in line for line in printed)


def test_claude가_제한_시간을_넘기면_그_회차는_0이_아닌_코드로_남는다(tmp_path: Path) -> None:
    """실제 하위 프로세스로 잰다. 멈춘 세션 하나가 러너 전체를 붙잡지 않는다(PR #157 CodeRabbit)."""
    잠드는_명령 = [sys.executable, "-c", "import time; print('{}'); time.sleep(30)"]

    result = run_claude(잠드는_명령, tmp_path, "", timeout=1.0)

    assert result.exit_code != 0
    assert "시간" in result.stderr


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["a.toml"],
        ["a.toml", "out", "더"],
        ["--preflight"],
        ["--control-commit", "abc1234", "a.toml"],
        ["--control-commit", "a.toml", "out"],
        ["a.toml", "out", "--control-commit", "abc1234"],
    ],
)
def test_인자가_맞지_않으면_사용법을_알리고_2다(tmp_path: Path, argv: list[str]) -> None:
    printed: list[str] = []

    assert main(argv, cwd=tmp_path, runner=_가짜({}), out=printed.append) == 2
    assert printed != []


@pytest.mark.parametrize("깃발", ["--preflight", "--out"])
def test_깃발을_뒤에_두면_출력_디렉터리로_삼지_않고_사용법을_알린다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, 깃발: str
) -> None:
    """출력 디렉터리는 프로세스의 작업 폴더 기준이라 그 자리를 `tmp_path` 로 옮겨 본다.

    `--preflight` 만이 아니라 `--` 로 시작하는 인자를 모두 막는다.
    """
    monkeypatch.chdir(tmp_path)
    spec_path = tmp_path / "canary.toml"
    spec_path.write_text(_스킬_명세, encoding="utf-8")
    _스킬_체크아웃(tmp_path, "새")
    _스킬_체크아웃(tmp_path, "옛")
    가짜 = _가짜({})
    printed: list[str] = []

    code = main([str(spec_path), 깃발], cwd=tmp_path, runner=가짜, out=printed.append)

    assert code == 2
    assert 가짜.호출 == []
    assert not (tmp_path / 깃발).exists()
    assert any("사용:" in line for line in printed)


# 사전 확인


def _사전_확인(
    tmp_path: Path, *명세들: Path, view: Callable[[Path], GitView | None] = git_view
) -> tuple[int, list[str], _가짜]:
    가짜 = _가짜({})
    printed: list[str] = []
    argv = ["--preflight", *(str(path) for path in 명세들)]
    return main(argv, cwd=tmp_path, runner=가짜, out=printed.append, view=view), printed, 가짜


def test_사전_확인은_claude를_띄우지_않고_출력도_남기지_않으며_통과하면_0이다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """출력 디렉터리는 프로세스의 작업 폴더 기준이라 그 자리도 `tmp_path` 로 옮겨 트리 전체를
    견준다."""
    monkeypatch.chdir(tmp_path)
    spec_path = tmp_path / "canary.toml"
    spec_path.write_text(_스킬_명세, encoding="utf-8")
    _스킬_체크아웃(tmp_path, "새")
    _스킬_체크아웃(tmp_path, "옛")
    before = sorted(tmp_path.rglob("*"))

    code, printed, 가짜 = _사전_확인(tmp_path, spec_path)

    assert code == 0
    assert 가짜.호출 == []
    assert sorted(tmp_path.rglob("*")) == before
    assert any("[통과]" in line and "canary.toml" in line for line in printed)


def test_사전_확인_깃발은_리스트가_아닌_시퀀스에서도_알아본다(tmp_path: Path) -> None:
    """`main` 은 `Sequence[str]` 를 받는다. 리스트만 깃발로 알아보면 튜플은 사용법으로 떨어진다."""
    spec_path = tmp_path / "canary.toml"
    spec_path.write_text(_스킬_명세, encoding="utf-8")
    _스킬_체크아웃(tmp_path, "새")
    _스킬_체크아웃(tmp_path, "옛")
    printed: list[str] = []

    code = main(("--preflight", str(spec_path)), cwd=tmp_path, runner=_가짜({}), out=printed.append)

    assert code == 0
    assert any("[통과]" in line for line in printed)


def test_사전_확인은_명세마다_판정하고_하나라도_어긋나면_2다(tmp_path: Path) -> None:
    """명세 여럿을 한 명령으로 받는다. 워크트리 가드가 명세마다 도는 반복문을 거부한다(대기열
    120)."""
    맞는_명세 = tmp_path / "맞는.toml"
    맞는_명세.write_text(_스킬_명세, encoding="utf-8")
    틀린_명세 = tmp_path / "틀린.toml"
    틀린_명세.write_text(_스킬_명세.replace('"EnterWorktree"', '"없는 카나리아"'), encoding="utf-8")
    깨진_명세 = tmp_path / "깨진.toml"
    깨진_명세.write_text("kind = ", encoding="utf-8")
    _스킬_체크아웃(tmp_path, "새")
    _스킬_체크아웃(tmp_path, "옛")

    code, printed, 가짜 = _사전_확인(tmp_path, 맞는_명세, 틀린_명세, 깨진_명세)

    assert code == 2
    assert 가짜.호출 == []
    assert any("[통과]" in line and "맞는.toml" in line for line in printed)
    assert any("[실패]" in line and "틀린.toml" in line for line in printed)
    assert any("원천" in line and "없는 카나리아" in line for line in printed)
    assert any("[실패]" in line and "깨진.toml" in line for line in printed)
    assert any("명세 오류" in line for line in printed)


def test_사전_확인은_원천이_실리는지_보지_않는다(tmp_path: Path) -> None:
    """못 보는 것. 원천의 `paths` 가 실험군의 대상을 덮지 않아 규칙이 실리지 않을 원천도 지나간다.

    실린다는 근거는 같은 명세가 앞서 `claude` 로 통과한 것이다. 그 뒤 머리말을 고쳤으면 다시 돌린다.
    """
    spec_path = tmp_path / "canary.toml"
    spec_path.write_text(_규칙_명세, encoding="utf-8")
    (tmp_path / ".claude" / "rules").mkdir(parents=True)
    (tmp_path / ".claude" / "rules" / "tools.md").write_text(
        '---\npaths:\n  - "docs/**"\n---\n\n식별자는 영문이다\n', encoding="utf-8"
    )
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "hook_env_read.py").write_text("# 훅\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("안내\n", encoding="utf-8")

    code, _, 가짜 = _사전_확인(tmp_path, spec_path)

    assert code == 0
    assert 가짜.호출 == []


def _에이전트_회차(답: str, agents: Sequence[str] = ("spec-reviewer",)) -> list[str]:
    return [
        _init(("Task", "Read", "Grep"), agents=agents),
        _에이전트_부름(),
        _에이전트_결과(_끝남()),
        _결과(답),
    ]


def _에이전트_실행(tmp_path: Path, 정의: str = _정의) -> tuple[int, list[str], _가짜]:
    spec_path = tmp_path / "canary.toml"
    spec_path.write_text(_에이전트_명세, encoding="utf-8")
    _에이전트_체크아웃(tmp_path, "새", 정의)
    _에이전트_체크아웃(tmp_path, "옛", None)
    회차들 = {"새": _에이전트_회차("6. 이음매로 잰다."), "옛": _에이전트_회차("없음", agents=())}
    가짜 = _가짜(회차들)
    printed: list[str] = []
    code = main(
        [str(spec_path), str(tmp_path / "out")], cwd=tmp_path, runner=가짜, out=printed.append
    )
    return code, printed, 가짜


def test_에이전트_명세를_끝까지_돌린다(tmp_path: Path) -> None:
    code, printed, 가짜 = _에이전트_실행(tmp_path)

    assert code == 0
    assert [args[args.index("--tools") + 1] for args, _, _ in 가짜.호출] == ["Agent,Read,Grep"] * 4
    assert any("통과 4" in line for line in printed)


def test_에이전트_정의가_어긋나면_돌리지_않고_2다(tmp_path: Path) -> None:
    code, printed, 가짜 = _에이전트_실행(tmp_path, _정의.replace("Read, Grep", "Read"))

    assert code == 2
    assert 가짜.호출 == []
    assert any("tools" in line for line in printed)


def test_상위_폴더에_카나리아가_있으면_돌리지_않고_2다(tmp_path: Path) -> None:
    spec_path = tmp_path / "canary.toml"
    spec_path.write_text(_스킬_명세, encoding="utf-8")
    _스킬_체크아웃(tmp_path, "새")
    _스킬_체크아웃(tmp_path, "옛")
    (tmp_path / "CLAUDE.md").write_text("`EnterWorktree` 를 먼저 부른다\n", encoding="utf-8")
    가짜 = _가짜({})
    printed: list[str] = []

    code = main(
        [str(spec_path), str(tmp_path / "out")], cwd=tmp_path, runner=가짜, out=printed.append
    )

    assert code == 2
    assert 가짜.호출 == []
    assert any("상위 폴더" in line for line in printed)


def test_세션에_실리는_git_상태에_카나리아가_있으면_돌리지_않고_2다(tmp_path: Path) -> None:
    spec_path = tmp_path / "canary.toml"
    spec_path.write_text(_스킬_명세, encoding="utf-8")
    _스킬_체크아웃(tmp_path, "새")
    _스킬_체크아웃(tmp_path, "옛")
    상태 = _가짜_상태({"새": GitView(), "옛": GitView(paths=("EnterWorktree.md",))})
    가짜 = _가짜({})
    printed: list[str] = []

    code = main(
        [str(spec_path), str(tmp_path / "out")],
        cwd=tmp_path,
        runner=가짜,
        out=printed.append,
        view=상태,
    )

    assert code == 2
    assert 가짜.호출 == []
    assert any("git 상태" in line and "EnterWorktree.md" in line for line in printed)
    assert not (tmp_path / "out").exists()


def test_사전_확인도_git_상태를_본다(tmp_path: Path) -> None:
    spec_path = tmp_path / "canary.toml"
    spec_path.write_text(_스킬_명세, encoding="utf-8")
    _스킬_체크아웃(tmp_path, "새")
    _스킬_체크아웃(tmp_path, "옛")
    상태 = _가짜_상태({"새": GitView(branch="feat/EnterWorktree"), "옛": GitView()})

    code, printed, 가짜 = _사전_확인(tmp_path, spec_path, view=상태)

    assert code == 2
    assert 가짜.호출 == []
    assert any("[실패]" in line for line in printed)
    assert any("브랜치 feat/EnterWorktree" in line for line in printed)


@pytest.mark.parametrize(
    "argv",
    [
        ["--preflight", "a.toml", "--out"],
        ["--preflight", "--control-commit", "-x", "a.toml"],
        ["--preflight", "--control-commit", "abc1234"],
        ["--preflight", "a.toml", "--control-commit", "abc1234"],
    ],
)
def test_사전_확인에_깃발을_섞거나_자리를_틀리면_명세로_읽지_않고_사용법을_알린다(
    tmp_path: Path, argv: list[str]
) -> None:
    printed: list[str] = []

    assert main(argv, cwd=tmp_path, runner=_가짜({}), out=printed.append) == 2
    assert any("사용:" in line for line in printed)
    assert not any("사전 확인 통과" in line for line in printed)


def test_상태는_돌리기_전에_체크아웃마다_한_번만_읽는다(tmp_path: Path) -> None:
    """못 보는 것. 회차가 도는 동안(출력 디렉터리를 만든 뒤 등)의 변화는 다시 읽지 않는다."""
    spec_path = tmp_path / "canary.toml"
    spec_path.write_text(_스킬_명세, encoding="utf-8")
    새 = _스킬_체크아웃(tmp_path, "새")
    옛 = _스킬_체크아웃(tmp_path, "옛")
    상태 = _가짜_상태({"새": GitView(), "옛": GitView()})
    가짜 = _가짜({"새": _스킬_회차(새, "EnterWorktree"), "옛": _스킬_회차(옛, "없음")})
    printed: list[str] = []

    code = main(
        [str(spec_path), str(tmp_path / "out")],
        cwd=tmp_path,
        runner=가짜,
        out=printed.append,
        view=상태,
    )

    assert code == 0
    assert len(가짜.호출) == 4
    assert 상태.읽은 == ["새", "옛"]


# 대조군 커밋


_대조군_커밋_명세 = """
kind = "skill"
question = "tidy-checkouts 스킬을 불러 부르는 곳 절의 도구 이름을 옮겨라. 없으면 \\"없음\\"."
expect = ["EnterWorktree"]
source = ".claude/skills/tidy-checkouts/SKILL.md"
skill = "tidy-checkouts"

[[arm]]
name = "새"
role = "experiment"

[[arm]]
name = "옛"
role = "control"
checkout = "없는-옛-판"
"""


def _두_판_저장소(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str, str]:
    """옛 판(카나리아 없음)과 새 판(카나리아 있음)을 차례로 커밋한 저장소와 두 커밋."""
    repo = _저장소(tmp_path, monkeypatch)
    skill = repo / ".claude" / "skills" / "tidy-checkouts" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(_옛_본문, encoding="utf-8")
    _git(repo, "add", ".")
    _커밋(repo, "옛 판")
    옛 = _git(repo, "rev-parse", "HEAD")
    skill.write_text(_새_본문, encoding="utf-8")
    _git(repo, "add", ".")
    _커밋(repo, "새 판")
    return repo, 옛, _git(repo, "rev-parse", "HEAD")


def _정한_임시(monkeypatch: pytest.MonkeyPatch, 자리: Path) -> list[str]:
    """`tempfile.mkdtemp` 가 `자리` 를 만들어 돌려주게 한다. 받은 prefix 를 적는다."""
    받은: list[str] = []

    def 만든다(prefix: str | None = None, **_: object) -> str:
        받은.append(prefix or "")
        자리.mkdir()
        return str(자리)

    monkeypatch.setattr(tempfile, "mkdtemp", 만든다)
    return 받은


class _사본을_읽는_가짜:
    """회차마다 그 체크아웃의 스킬 사본을 읽어 답하고, 돌던 때의 자리·본문·브랜치를 적는다."""

    def __init__(self) -> None:
        self.본_것: list[tuple[Path, str, str]] = []

    def __call__(self, args: Sequence[str], cwd: Path, stdin: str) -> RunResult:
        본문 = (cwd / ".claude" / "skills" / "tidy-checkouts" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.본_것.append((cwd, 본문, _git(cwd, "branch", "--show-current")))
        답 = "EnterWorktree" if "EnterWorktree" in 본문 else "없음"
        return RunResult(0, "\n".join(_스킬_회차(cwd, 답)) + "\n", "")


def _대조군_커밋_실행(
    tmp_path: Path, repo: Path, 커밋: str, runner: Callable[[Sequence[str], Path, str], RunResult]
) -> tuple[int, list[str]]:
    spec_path = tmp_path / "canary.toml"
    spec_path.write_text(_대조군_커밋_명세, encoding="utf-8")
    printed: list[str] = []
    argv = ["--control-commit", 커밋, str(spec_path), str(tmp_path / "out")]
    return main(argv, cwd=repo, runner=runner, out=printed.append), printed


def _워크트리들(repo: Path) -> list[str]:
    listed = _git(repo, "worktree", "list", "--porcelain")
    return [
        line.removeprefix("worktree ")
        for line in listed.splitlines()
        if line.startswith("worktree ")
    ]


def test_대조군_커밋을_임시_워크트리로_꺼내_대조군만_돌리고_끝나면_걷는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """실제 git 으로 잰다. 명세의 대조군 `checkout` 은 없는 폴더라 쓰였으면 돌리기 전에 막힌다.

    대조군 회차는 옛 판의 사본을 분리 HEAD 로 읽고, 실험군 회차는 부른 체크아웃을 읽는다. 끝나면
    워크트리 등록과 폴더, 그것을 담은 임시 폴더가 모두 없고 브랜치도 늘지 않는다.
    """
    repo, 옛, _ = _두_판_저장소(tmp_path, monkeypatch)
    임시 = tmp_path / "임시"
    받은 = _정한_임시(monkeypatch, 임시)
    브랜치들 = _git(repo, "branch", "--format=%(refname:short)")
    가짜 = _사본을_읽는_가짜()

    code, printed = _대조군_커밋_실행(tmp_path, repo, 옛[:7], 가짜)

    assert code == 0
    assert 받은 == ["canary-control-"]
    대조군 = [(cwd, 본문, 브랜치) for cwd, 본문, 브랜치 in 가짜.본_것 if cwd != repo]
    assert 대조군 == [(임시 / 옛[:7], _옛_본문, "")]
    assert sorted(본문 for cwd, 본문, _ in 가짜.본_것 if cwd == repo) == [_새_본문] * 3
    assert not 임시.exists()
    assert _워크트리들(repo) == [_git(repo, "rev-parse", "--show-toplevel")]
    assert _git(repo, "branch", "--format=%(refname:short)") == 브랜치들
    assert any(line.startswith(f"대조군 체크아웃: {임시 / 옛[:7]}") for line in printed)
    짧은 = _git(repo, "rev-parse", "--short", 옛)
    assert any(line.startswith("갈래: ") and f"옛(대조군) 커밋 {짧은}" in line for line in printed)


def test_꺼낸_대조군만_걷고_부른_체크아웃과_다른_워크트리의_커밋하지_않은_파일은_남긴다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """지우는 길의 반박(`.claude/rules/tools.md`). 회차 세션이 꺼낸 자리에 추적하지 않는 파일과
    `.venv` 를 남겨도 `--force` 가 그 자리만 걷고, 부른 체크아웃과 같은 저장소의 다른 워크트리는
    건드리지 않는다."""
    repo, 옛, _ = _두_판_저장소(tmp_path, monkeypatch)
    (repo / "고치던.md").write_text("커밋하지 않았다\n", encoding="utf-8")
    옆 = tmp_path / "옆"
    _git(repo, "worktree", "add", "-q", "--detach", str(옆), 옛)
    (옆 / "옆에서_고치던.md").write_text("커밋하지 않았다\n", encoding="utf-8")
    임시 = tmp_path / "임시"
    _정한_임시(monkeypatch, 임시)
    읽는_가짜 = _사본을_읽는_가짜()

    def 흘리는_가짜(args: Sequence[str], cwd: Path, stdin: str) -> RunResult:
        if cwd != repo:
            (cwd / "세션이_남긴.md").write_text("남김\n", encoding="utf-8")
            (cwd / ".venv" / "Lib").mkdir(parents=True)
            (cwd / ".venv" / "Lib" / "모듈.pyd").write_bytes(b"x")
        return 읽는_가짜(args, cwd, stdin)

    code, _ = _대조군_커밋_실행(tmp_path, repo, 옛, 흘리는_가짜)

    assert code == 0
    assert not 임시.exists()
    assert (repo / "고치던.md").read_text(encoding="utf-8") == "커밋하지 않았다\n"
    assert (옆 / "옆에서_고치던.md").read_text(encoding="utf-8") == "커밋하지 않았다\n"
    assert len(_워크트리들(repo)) == 2


def test_돌리기_전_확인에서_막혀도_꺼낸_대조군을_걷는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """대조군으로 새 판을 주면 대조군 사본의 원천에 카나리아가 있어 돌리지 않는다."""
    repo, _, 새 = _두_판_저장소(tmp_path, monkeypatch)
    임시 = tmp_path / "임시"
    _정한_임시(monkeypatch, 임시)
    가짜 = _사본을_읽는_가짜()

    code, printed = _대조군_커밋_실행(tmp_path, repo, 새, 가짜)

    assert code == 2
    assert 가짜.본_것 == []
    assert any("대조군 사본의 원천" in line for line in printed)
    assert not 임시.exists()
    assert len(_워크트리들(repo)) == 1


def test_claude를_띄우지_못해도_꺼낸_대조군을_걷는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, 옛, _ = _두_판_저장소(tmp_path, monkeypatch)
    임시 = tmp_path / "임시"
    _정한_임시(monkeypatch, 임시)

    def 없는_claude(args: Sequence[str], cwd: Path, stdin: str) -> RunResult:
        raise FileNotFoundError("claude 없음")

    code, printed = _대조군_커밋_실행(tmp_path, repo, 옛, 없는_claude)

    assert code == 3
    assert any("claude 없음" in line for line in printed)
    assert not 임시.exists()
    assert len(_워크트리들(repo)) == 1


def test_꺼낸_대조군을_걷지_못하면_자리와_걷는_명령을_찍고_종료_코드는_판정대로다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """회차 도중 그 워크트리를 잠가 `git worktree remove --force` 한 번이 거부하게 한다.

    찍은 안내(잠겼으면 `--force` 를 두 번, 그다음 임시 폴더를 지운다)를 그대로 밟아 걷힌다.
    """
    repo, 옛, _ = _두_판_저장소(tmp_path, monkeypatch)
    임시 = tmp_path / "임시"
    _정한_임시(monkeypatch, 임시)
    읽는_가짜 = _사본을_읽는_가짜()

    def 잠그는_가짜(args: Sequence[str], cwd: Path, stdin: str) -> RunResult:
        if cwd != repo:
            _git(repo, "worktree", "lock", str(cwd))
        return 읽는_가짜(args, cwd, stdin)

    code, printed = _대조군_커밋_실행(tmp_path, repo, 옛, 잠그는_가짜)
    자리 = 임시 / 옛[:7]
    남은 = 자리.exists()
    _git(repo, "worktree", "remove", "--force", "--force", str(자리))
    임시.rmdir()

    assert code == 0
    assert 남은
    assert len(_워크트리들(repo)) == 1
    assert any(
        line.startswith(f"임시 워크트리를 걷지 못했다: {자리}")
        and f"git worktree remove --force {자리}" in line
        and "--force 를 두 번" in line
        and f"{임시} 를 지운다" in line
        and "주 체크아웃 세션" in line
        for line in printed
    )


@pytest.mark.parametrize("커밋", ["0000000", "없는-커밋"])
def test_대조군_커밋을_찾지_못하면_아무것도_만들지_않고_2다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, 커밋: str
) -> None:
    repo, _, _ = _두_판_저장소(tmp_path, monkeypatch)
    받은 = _정한_임시(monkeypatch, tmp_path / "임시")
    가짜 = _사본을_읽는_가짜()

    code, printed = _대조군_커밋_실행(tmp_path, repo, 커밋, 가짜)

    assert code == 2
    assert 받은 == []
    assert 가짜.본_것 == []
    assert any("찾지 못했다" in line and 커밋 in line for line in printed)


@pytest.mark.parametrize("커밋", ["-x", "--all"])
def test_대조군_커밋이_깃발처럼_보이면_git에_넘기지_않고_사용법을_알린다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, 커밋: str
) -> None:
    repo, _, _ = _두_판_저장소(tmp_path, monkeypatch)
    받은 = _정한_임시(monkeypatch, tmp_path / "임시")

    code, printed = _대조군_커밋_실행(tmp_path, repo, 커밋, _사본을_읽는_가짜())

    assert code == 2
    assert 받은 == []
    assert any("사용:" in line for line in printed)


def test_꺼낼_자리에_이미_무엇이_있으면_지우지_않고_3이다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """git 이 거부한 자리는 이 도구가 꺼낸 것인지 몰라 건드리지 않는다."""
    repo, 옛, _ = _두_판_저장소(tmp_path, monkeypatch)
    임시 = tmp_path / "임시"

    def 차_있는_자리(prefix: str | None = None, **_: object) -> str:
        (임시 / 옛[:7]).mkdir(parents=True)
        (임시 / 옛[:7] / "사람의.md").write_text("지우면 안 된다\n", encoding="utf-8")
        return str(임시)

    monkeypatch.setattr(tempfile, "mkdtemp", 차_있는_자리)
    가짜 = _사본을_읽는_가짜()

    code, printed = _대조군_커밋_실행(tmp_path, repo, 옛, 가짜)

    assert code == 3
    assert 가짜.본_것 == []
    assert (임시 / 옛[:7] / "사람의.md").read_text(encoding="utf-8") == "지우면 안 된다\n"
    assert any("꺼내지 못했다" in line for line in printed)
    assert any(line.startswith(f"임시 폴더 {임시} 가 남았다") for line in printed)
    assert len(_워크트리들(repo)) == 1


def test_꺼내기가_제한_시간을_넘기면_반쯤_꺼낸_자리를_걷고_3이다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """git 을 가짜로 둔다. 제한 시간을 넘긴 add 가 자리를 반쯤 만들고, 러너는 그 자리를 걷는다."""
    임시 = tmp_path / "임시"
    _정한_임시(monkeypatch, 임시)
    부른: list[list[str]] = []
    sha = "abcdef0123456789abcdef0123456789abcdef01"

    def 가짜_git(args: Sequence[str], **_: object) -> subprocess.CompletedProcess[bytes]:
        부른.append(list(args[3:]))
        if "add" in args:
            (임시 / sha[:7] / "반쯤").mkdir(parents=True)
            raise subprocess.TimeoutExpired(args, 300.0)
        if "remove" in args:
            shutil.rmtree(임시 / sha[:7])
        return subprocess.CompletedProcess(args, 0, f"{sha}\n".encode(), b"")

    monkeypatch.setattr(subprocess, "run", 가짜_git)
    spec_path = tmp_path / "canary.toml"
    spec_path.write_text(_대조군_커밋_명세, encoding="utf-8")
    printed: list[str] = []
    argv = ["--control-commit", "abcdef0", str(spec_path), str(tmp_path / "out")]

    code = main(argv, cwd=tmp_path, runner=_사본을_읽는_가짜(), out=printed.append)

    assert code == 3
    자리 = str(임시 / sha[:7])
    긴_경로 = ["-c", "core.longpaths=true", "worktree"]
    assert [*긴_경로, "add", "--detach", 자리, sha] in 부른
    assert [*긴_경로, "remove", "--force", "--force", 자리] in 부른
    assert not 임시.exists()
    assert any("제한 시간" in line for line in printed)


@pytest.mark.parametrize(
    ("판", "기대", "표지"), [("옛", 0, "[통과]"), ("새", 2, "대조군 사본의 원천")]
)
def test_사전_확인도_대조군_커밋을_꺼내_보고_걷는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, 판: str, 기대: int, 표지: str
) -> None:
    """커밋 대조군으로 통과한 명세를 문구만 고친 뒤 갈음하는 길. 명세의 대조군 `checkout` 은 없는
    폴더라, 인자 없이는 "체크아웃이 없다"로 막힌다."""
    repo, 옛, 새 = _두_판_저장소(tmp_path, monkeypatch)
    임시 = tmp_path / "임시"
    _정한_임시(monkeypatch, 임시)
    spec_path = tmp_path / "canary.toml"
    spec_path.write_text(_대조군_커밋_명세, encoding="utf-8")
    가짜 = _가짜({})
    printed: list[str] = []
    argv = ["--preflight", "--control-commit", 옛 if 판 == "옛" else 새, str(spec_path)]

    code = main(argv, cwd=repo, runner=가짜, out=printed.append)

    assert code == 기대
    assert 가짜.호출 == []
    assert any(표지 in line for line in printed)
    assert any(line.startswith(f"대조군 체크아웃: {임시}") for line in printed)
    assert not 임시.exists()
    assert len(_워크트리들(repo)) == 1
    assert not (tmp_path / "out").exists()


def test_강제로_끝난_실행은_꺼낸_대조군을_걷지_못하고_시작_줄이_그_자리를_찍는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """못 보는 것(지나간다). 꺼낸 뒤 하위 프로세스가 `os._exit` 로 끝나면 kill 처럼 걷는 길이 돌지
    않아 자리와 등록이 남는다. 시작 줄이 그 자리를 찍는다."""
    repo, 옛, _ = _두_판_저장소(tmp_path, monkeypatch)
    임시 = tmp_path / "임시"
    script = tmp_path / "끊김.py"
    script.write_text(
        "import os, sys, tempfile\n"
        "from pathlib import Path\n"
        f"sys.path.insert(0, {str(Path(__file__).resolve().parents[2])!r})\n"
        "from tools.canary import control_checkout\n"
        f"tempfile.mkdtemp = lambda prefix=None: Path({str(임시)!r}).mkdir() or {str(임시)!r}\n"
        f"with control_checkout(Path({str(repo)!r}), {옛!r}, print):\n"
        "    sys.stdout.flush()\n"
        "    os._exit(0)\n",
        encoding="utf-8",
    )
    environment = {**os.environ, "PYTHONUTF8": "1"}

    done = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=120,
        env=environment,
    )
    자리 = 임시 / 옛[:7]
    남은 = 자리.exists()
    등록 = len(_워크트리들(repo))
    _git(repo, "worktree", "remove", "--force", str(자리))

    assert done.returncode == 0, done.stderr
    assert f"대조군 체크아웃: {자리}" in done.stdout
    assert 남은
    assert 등록 == 2
