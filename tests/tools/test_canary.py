"""tools/canary.py 의 카나리아 러너.

러너는 가짜다. 이벤트는 2026-10-07 에 손으로 돌린 카나리아 둘(claude 2.1.291, `--output-format
stream-json --verbose`, 규칙은 `--tools Read`, 스킬은 `--tools Skill`)의 모양을 따른다. init
의 `tools`·`mcp_servers`, assistant 의 `tool_use`(`Read` 의 `file_path`, `Skill` 의 `skill`),
스킬 본문이 실린 user 의 `Base directory for this skill:` 줄, 마지막 `result` 다. `claude` 를
하위 프로세스로 부르는 실제 러너는 실제 실행으로 확인한다(`.claude/rules/tests.md`).
"""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

import pytest
from tools.canary import (
    Facts,
    RunResult,
    SpecError,
    command,
    judge,
    load_spec,
    main,
    prompt_for,
    read_facts,
    run_claude,
    target_problems,
)

_규칙_명세 = '''
kind = "rule"
question = """
Read 도구로 `{target}` 하나만 읽어라. 실린 지시에서 tools 의 식별자 언어를 옮겨라. 없으면 "없음".
"""
expect = ["식별자는 영문"]

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


def _init(tools: Sequence[str] = ("Read",), servers: Sequence[str] = ()) -> str:
    return _줄(
        {
            "type": "system",
            "subtype": "init",
            "tools": list(tools),
            "mcp_servers": [{"name": name, "status": "connected"} for name in servers],
        }
    )


def _도구(name: str, arguments: dict[str, object]) -> str:
    block: dict[str, object] = {"type": "tool_use", "name": name, "input": arguments}
    return _줄({"type": "assistant", "message": {"content": [block]}})


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


def test_규칙_대상_파일이_없으면_알린다(tmp_path: Path) -> None:
    spec = load_spec(_규칙_명세)

    assert any("없다" in problem for problem in target_problems(spec, spec.arm[1], tmp_path))


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


def _스킬_체크아웃(root: Path, 이름: str) -> Path:
    checkout = root / 이름
    (checkout / ".claude" / "skills" / "tidy-checkouts").mkdir(parents=True)
    return checkout


def _스킬_회차(checkout: Path, 답: str) -> list[str]:
    folder = checkout / ".claude" / "skills" / "tidy-checkouts"
    return [_init(("Skill",)), _스킬_부름("tidy-checkouts"), _스킬_본문(folder), _결과(답)]


def _스킬_실행(
    tmp_path: Path, 새_답: str, 옛_답: str, exit_code: int = 0
) -> tuple[int, list[str], _가짜]:
    spec_path = tmp_path / "canary.toml"
    spec_path.write_text(_스킬_명세, encoding="utf-8")
    새 = _스킬_체크아웃(tmp_path, "새")
    옛 = _스킬_체크아웃(tmp_path, "옛")
    가짜 = _가짜({"새": _스킬_회차(새, 새_답), "옛": _스킬_회차(옛, 옛_답)}, exit_code)
    printed: list[str] = []
    code = main(
        [str(spec_path), str(tmp_path / "out")], cwd=tmp_path, runner=가짜, out=printed.append
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
    code, printed, _ = _스킬_실행(tmp_path, "EnterWorktree", "EnterWorktree")

    assert code == 1
    assert any("옛" in line and "대조군" in line for line in printed)


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


def test_claude가_제한_시간을_넘기면_그_회차는_0이_아닌_코드로_남는다(tmp_path: Path) -> None:
    """실제 하위 프로세스로 잰다. 멈춘 세션 하나가 러너 전체를 붙잡지 않는다(PR #157 CodeRabbit)."""
    잠드는_명령 = [sys.executable, "-c", "import time; print('{}'); time.sleep(30)"]

    result = run_claude(잠드는_명령, tmp_path, "", timeout=1.0)

    assert result.exit_code != 0
    assert "시간" in result.stderr


@pytest.mark.parametrize("argv", [[], ["a.toml"], ["a.toml", "out", "더"]])
def test_인자가_둘이_아니면_사용법을_알리고_2다(tmp_path: Path, argv: list[str]) -> None:
    printed: list[str] = []

    assert main(argv, cwd=tmp_path, runner=_가짜({}), out=printed.append) == 2
    assert printed != []
