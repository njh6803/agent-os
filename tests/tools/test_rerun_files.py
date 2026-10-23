"""tools/rerun_files.py 검증. 과제 목록과 회차 기록의 꼴, `records/`의 파일 이름, 회차 폴더 이름과
다음 회차 번호, 숨은 시험 파일 꺼내기, 판정이 읽는 칸, 그리고 이 모듈이 하위 프로세스를 부르는
모듈을 끌어오지 않는지.

꼴을 깨는 사례는 쓰는 함수가 낸 글을 `Json`으로 풀어 한 칸만 바꾼 뒤 읽기에 넘긴다(`_바꿔`).
"""

from __future__ import annotations

import ast
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import IO

import pytest
from tools.rerun_files import (
    ARMS,
    CALL_FIRST,
    CALL_HANDOFF,
    CALL_INTERVENTION,
    CAP_REASONS,
    END_CAPPED,
    END_DONE,
    END_NOT_MEASURED,
    GATE_COMMANDS,
    LIST_MAIN,
    LIST_PILOT,
    NOT_MEASURED_REASONS,
    RULE_BRANCH,
    RULE_NONE,
    SETUP_COMMANDS,
    SHAPE_VERSION,
    TIER_PILOT,
    TIER_SMALL,
    Call,
    End,
    Gate,
    Hidden,
    Hit,
    LineCount,
    ModelUsage,
    Outcome,
    Record,
    ResultEvent,
    Session,
    SetupFailure,
    ShapeError,
    Spend,
    Substitute,
    Task,
    TaskList,
    Tokens,
    Window,
    arm_label,
    dumps_record,
    dumps_task_list,
    hidden_test_file,
    hidden_test_files,
    is_support_file,
    is_test_file,
    judge_view,
    next_round_no,
    parse_record,
    parse_round_dir_name,
    parse_task_list,
    read_judge_view,
    read_record,
    read_task_list,
    record_file_name,
    round_dir_name,
    write_record,
    write_task_list,
)

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None

B = "a" * 40
M = "b" * 40
SID = "0f8e2c1a-1b2c-4d3e-8f90-123456789abc"


def _과제(**바꿀: object) -> Task:
    기본 = Task(
        task_id="model-rerun-01",
        ticket=".scratch/model-rerun/issues/01-rerun-file-shapes.md",
        base=B,
        merge=M,
        branch="feature/01-rerun-file-shapes",
        tier=TIER_SMALL,
        size=7,
        order=0,
        pilot=False,
        pr_cost_usd=12.5,
        round_cap_usd=40.0,
        hidden_tests=(
            "tests/tools/test_rerun_files.py::test_a",
            "tests/tools/test_rerun_files.py::test_b[x-1]",
            "tests/tools/test_other.py::TestC::test_c",
        ),
        support_files=("tests/conftest.py",),
        original_model_effort="claude-opus-5-5/xhigh",
        arm_plan=("C", "A", "E", "B", "D"),
    )
    return replace(기본, **바꿀)


def _목록(*과제들: Task, kind: str = LIST_MAIN) -> TaskList:
    return TaskList(kind=kind, tasks=과제들 or (_과제(),))


def _세션() -> Session:
    return Session(
        session_id=SID,
        calls=(
            Call(
                kind=CALL_FIRST,
                budget_usd=40.0,
                exit_code=0,
                results=(
                    ResultEvent(
                        index=0, subtype="success", terminal_reason="completed", num_turns=12
                    ),
                    ResultEvent(index=1, subtype="success", terminal_reason=None, num_turns=None),
                ),
                has_directive=False,
                ends_with_question=True,
                kill_skipped=False,
            ),
            Call(
                kind=CALL_INTERVENTION,
                budget_usd=31.25,
                exit_code=None,
                results=(),
                has_directive=False,
                ends_with_question=False,
                kill_skipped=True,
            ),
        ),
        cost_usd=8.75,
        cost_substituted=True,
        runner_killed=True,
        model_usage=(
            ModelUsage(
                model="claude-opus-5-5",
                input_tokens=8,
                output_tokens=257,
                cache_read_tokens=61919,
                cache_write_tokens=7091,
                thinking_tokens=0,
                cost_usd=0.0371419,
            ),
        ),
        main_lines=(
            LineCount(model="claude-opus-5-5", effort="medium", lines=30),
            LineCount(model="<synthetic>", effort=None, lines=1),
        ),
        subagent_lines=(LineCount(model="claude-sonnet-5-5", effort="low", lines=4),),
    )


def _기록(**바꿀: object) -> Record:
    기본 = Record(
        task_id="model-rerun-01",
        arm="C",
        round_no=2,
        condition_version=1,
        pilot=False,
        round_dir_name="",
        claude_version="2.1.302 (Claude Code)",
        account="njh6803",
        env_names=("PATH", "ProgramFiles(x86)", "GH_CONFIG_DIR"),
        init_tools=("Bash", "Read", "mcp__x__y"),
        sessions=(_세션(),),
        handoffs=1,
        interventions=1,
        asked_at_end=True,
        end=End(kind=END_DONE, reason=None, resets_at=None),
        outcome=Outcome(
            commit=M,
            rule=RULE_BRANCH,
            commits_after_base=3,
            setup_failure=None,
            gates=(
                Gate(command=GATE_COMMANDS[0], exit_code=0, timed_out=False),
                Gate(command=GATE_COMMANDS[1], exit_code=1, timed_out=False),
                Gate(command=GATE_COMMANDS[2], exit_code=None, timed_out=True),
            ),
            hidden=Hidden(passed=2, total=3, failed=("tests/tools/test_other.py::TestC::test_c",)),
        ),
        spend=Spend(
            claude_code_usd=8.75,
            official_usd=9.5,
            tokens=Tokens(input=10, output=20, cache_read=30, cache_write=40, thinking=None),
            substitutes=(
                Substitute(
                    model="claude-haiku-5-5",
                    tokens=Tokens(input=1, output=2, cache_read=3, cache_write=4, thinking=None),
                ),
            ),
            wall_seconds=1234.5,
            denied_calls=2,
            utilization_start=(Window(window="five_hour", utilization=0.01),),
            utilization_end=(
                Window(window="five_hour", utilization=0.2),
                Window(window="seven_day", utilization=0.97),
            ),
            contamination=(Hit(pattern="낱말-gh", tool="Bash"),),
            model_mismatch=(LineCount(model="claude-haiku-5-5", effort=None, lines=3),),
        ),
    )
    기록 = replace(기본, **바꿀)
    if "round_dir_name" in 바꿀:
        return 기록
    폴더 = round_dir_name(기록.task_id, 기록.arm, 기록.round_no, "a1b2c3")
    return replace(기록, round_dir_name=폴더)


def _초록_게이트() -> tuple[Gate, ...]:
    return tuple(Gate(command=c, exit_code=0, timed_out=False) for c in GATE_COMMANDS)


def _측정아님(reason: str, resets_at: int | None = None) -> Record:
    return _기록(
        sessions=(),
        handoffs=0,
        interventions=0,
        asked_at_end=False,
        end=End(kind=END_NOT_MEASURED, reason=reason, resets_at=resets_at),
        outcome=Outcome(
            commit=None,
            rule=None,
            commits_after_base=None,
            setup_failure=None,
            gates=None,
            hidden=None,
        ),
    )


def _풀기(text: str) -> Json:
    값: Json = json.loads(text)
    return 값


def _내려가(뿌리: Json, 길: tuple[str | int, ...]) -> Json:
    자리 = 뿌리
    for 조각 in 길:
        if isinstance(자리, dict) and isinstance(조각, str):
            자리 = 자리[조각]
        elif isinstance(자리, list) and isinstance(조각, int):
            자리 = 자리[조각]
        else:
            raise AssertionError(f"길이 맞지 않는다: {길}")
    return 자리


def _바꿔(text: str, 길: tuple[str | int, ...], 값: Json) -> str:
    """`길`을 따라 내려가 마지막 칸을 `값`으로 바꾼 글을 낸다."""
    뿌리 = _풀기(text)
    자리 = _내려가(뿌리, 길[:-1])
    끝 = 길[-1]
    if isinstance(자리, dict) and isinstance(끝, str):
        자리[끝] = 값
    elif isinstance(자리, list) and isinstance(끝, int):
        자리[끝] = 값
    else:
        raise AssertionError(f"길이 맞지 않는다: {길}")
    return json.dumps(뿌리, ensure_ascii=False)


def _지워(text: str, 길: tuple[str | int, ...]) -> str:
    """`길`을 따라 내려가 마지막 키를 지운 글을 낸다."""
    뿌리 = _풀기(text)
    자리 = _내려가(뿌리, 길[:-1])
    끝 = 길[-1]
    if not (isinstance(자리, dict) and isinstance(끝, str)):
        raise AssertionError(f"길이 맞지 않는다: {길}")
    del 자리[끝]
    return json.dumps(뿌리, ensure_ascii=False)


# --- 갈래 ---


def test_갈래_다섯의_모델과_노력은_설계_4절이다() -> None:
    표 = {a.name: (a.model, a.effort) for a in ARMS}
    assert 표 == {
        "A": ("claude-opus-5-5", "xhigh"),
        "B": ("claude-opus-5-5", "high"),
        "C": ("claude-opus-5-5", "medium"),
        "D": ("claude-sonnet-5-5", "high"),
        "E": ("claude-sonnet-5-5", "medium"),
    }


def test_지시문의_모델_줄은_사람의_이름이다() -> None:
    assert arm_label("A") == "Opus 5.5 / xhigh"
    assert arm_label("E") == "Sonnet 5.5 / medium"
    with pytest.raises(KeyError):
        arm_label("F")


# --- 쓰고 다시 읽기 ---


def test_과제_목록을_쓰고_다시_읽으면_같다(tmp_path: Path) -> None:
    본 = _목록(_과제(), _과제(task_id="other-slug-12", order=1, arm_plan=("A", "A")))
    파일럿 = _목록(
        _과제(pilot=True, tier=TIER_PILOT, original_model_effort=None, support_files=()),
        kind=LIST_PILOT,
    )
    for 목록 in (본, 파일럿):
        경로 = tmp_path / f"{목록.kind}.json"
        write_task_list(경로, 목록)
        assert read_task_list(경로) == 목록
        assert parse_task_list(dumps_task_list(목록)) == 목록


def test_회차_기록을_쓰고_다시_읽으면_같다(tmp_path: Path) -> None:
    for 기록 in (_기록(), _측정아님("한도", resets_at=1792962000), _측정아님("중단")):
        폴더 = tmp_path / str(id(기록))
        폴더.mkdir()
        경로 = write_record(폴더, 기록)
        assert 경로.name == record_file_name(기록.task_id, 기록.arm, 기록.round_no)
        assert read_record(경로) == 기록
        assert parse_record(dumps_record(기록)) == 기록


def test_두_파일_모두_꼴_판을_맨_위에_든다() -> None:
    for 글 in (dumps_task_list(_목록()), dumps_record(_기록())):
        값 = _풀기(글)
        assert isinstance(값, dict)
        assert next(iter(값)) == "shape_version"
        assert 값["shape_version"] == SHAPE_VERSION


def test_쓰는_함수는_읽기가_거부할_값을_쓰지_않는다(tmp_path: Path) -> None:
    틀린 = _기록(end=End(kind=END_DONE, reason="한도", resets_at=None))
    with pytest.raises(ShapeError, match="하위 이유"):
        write_record(tmp_path, 틀린)
    assert list(tmp_path.iterdir()) == []
    with pytest.raises(ShapeError, match="파일럿"):
        write_task_list(tmp_path / "x.json", _목록(_과제(pilot=True, tier=TIER_PILOT)))
    assert list(tmp_path.iterdir()) == []


# --- 꼴을 깨는 값 ---


@pytest.mark.parametrize("판", [0, 2, "1", True, 1.0])
def test_모르는_판은_거부한다(판: Json) -> None:
    with pytest.raises(ShapeError, match="판"):
        parse_task_list(_바꿔(dumps_task_list(_목록()), ("shape_version",), 판))
    with pytest.raises(ShapeError, match="판"):
        parse_record(_바꿔(dumps_record(_기록()), ("shape_version",), 판))


@pytest.mark.parametrize(
    "길",
    [
        ("kind",),
        ("tasks", 0, "arm_plan"),
        ("tasks", 0, "original_model_effort"),
    ],
)
def test_과제_목록의_빠진_키는_거부한다(길: tuple[str | int, ...]) -> None:
    with pytest.raises(ShapeError, match="빠진 키"):
        parse_task_list(_지워(dumps_task_list(_목록()), 길))


@pytest.mark.parametrize(
    "길",
    [
        ("end",),
        ("end", "resets_at"),
        ("outcome", "gates"),
        ("sessions", 0, "calls", 0, "results", 0, "terminal_reason"),
        ("spend", "tokens", "thinking"),
    ],
)
def test_회차_기록의_빠진_키는_거부한다(길: tuple[str | int, ...]) -> None:
    with pytest.raises(ShapeError, match="빠진 키"):
        parse_record(_지워(dumps_record(_기록()), 길))


@pytest.mark.parametrize(
    ("길", "값"),
    [
        (("tasks", 0, "size"), "7"),
        (("tasks", 0, "size"), True),
        (("tasks", 0, "size"), 7.0),
        (("tasks", 0, "pilot"), 0),
        (("tasks", 0, "pr_cost_usd"), "12.5"),
        (("tasks", 0, "pr_cost_usd"), float("nan")),
        (("tasks", 0, "round_cap_usd"), float("inf")),
        (("tasks", 0, "round_cap_usd"), 10**400),
        (("tasks", 0, "hidden_tests"), "tests/a.py::t"),
        (("tasks", 0, "base"), "abc"),
        (("tasks", 0, "tier"), "거대"),
        (("tasks", 0, "arm_plan"), ["F"]),
        (("tasks", 0, "arm_plan"), []),
        (("tasks", 0, "task_id"), "model-rerun"),
        (("tasks", 0, "task_id"), "model-rerun-١٢"),
        (("kind",), "예비"),
    ],
)
def test_과제_목록의_형이_다른_값은_거부한다(길: tuple[str | int, ...], 값: Json) -> None:
    with pytest.raises(ShapeError, match=str(길[-1])):
        parse_task_list(_바꿔(dumps_task_list(_목록()), 길, 값))


@pytest.mark.parametrize(
    ("길", "값"),
    [
        (("round_no",), "2"),
        (("round_no",), 0),
        (("arm",), "F"),
        (("pilot",), "false"),
        (("sessions", 0, "cost_usd"), "8.75"),
        (("sessions", 0, "calls", 0, "kind"), "둘째"),
        (("sessions", 0, "calls", 0, "exit_code"), 1.5),
        (("sessions", 0, "session_id"), "not-a-uuid"),
        (("env_names",), ["PATH", "GH TOKEN=abc"]),
        (("spend", "contamination", 0, "tool"), "Bash -c gh api"),
        (("spend", "tokens", "input"), -1),
        (("spend", "official_usd"), float("nan")),
        (("spend", "claude_code_usd"), float("inf")),
        (("end", "resets_at"), "1792962000"),
        (("task_id",), "model-rerun-١٢"),
        (("account",), "njh6803@example.com"),
        (("init_tools",), ["Bash", "https://evil.example/x"]),
        (("init_tools",), ["Bash", "C:/Users/me/.ssh/id_rsa"]),
        (("spend", "contamination", 0, "tool"), "모델이쓴글"),
        (("spend", "contamination", 0, "pattern"), "a b"),
        (("spend", "substitutes", 0, "model"), "gpt-x"),
        (("spend", "utilization_end", 0, "window"), "five hour"),
        (("sessions", 0, "calls", 0, "results", 0, "subtype"), "error: 글"),
        (("sessions", 0, "main_lines", 0, "effort"), "x=1"),
        (("claude_version",), "2.1.302\n글"),
        (("round_dir_name",), 'model-rerun-01-C-2-a"b'),
        (("round_dir_name",), "model-rerun-01-C-2-a\tb"),
    ],
)
def test_회차_기록의_형이_다른_값은_거부한다(길: tuple[str | int, ...], 값: Json) -> None:
    with pytest.raises(ShapeError, match=str(길[-1])):
        parse_record(_바꿔(dumps_record(_기록()), 길, 값))


def test_모르는_키는_거부한다() -> None:
    목록 = _풀기(dumps_task_list(_목록()))
    assert isinstance(목록, dict)
    목록["extra"] = 1
    with pytest.raises(ShapeError, match="모르는 키"):
        parse_task_list(json.dumps(목록))
    with pytest.raises(ShapeError, match="모르는 키"):
        parse_record(
            _바꿔(dumps_record(_기록()), ("sessions", 0, "calls", 0, "prompt"), "모델이 쓴 글")
        )


def test_JSON_이_아니거나_맨_위가_객체가_아니면_거부한다() -> None:
    사례 = (
        ("{", "JSON이 아니다"),
        ("[" * 100000, "JSON이 아니다"),
        ('{"shape_version": ' + "1" * 5000 + "}", "JSON이 아니다"),
        ("[]", "객체"),
        ("null", "객체"),
    )
    for 글, 까닭 in 사례:
        with pytest.raises(ShapeError, match=까닭):
            parse_task_list(글)
        with pytest.raises(ShapeError, match=까닭):
            parse_record(글)


def test_쓰기는_유한하지_않은_수를_ShapeError_로_거부한다(tmp_path: Path) -> None:
    기록 = _기록()
    나쁜_기록 = replace(기록, spend=replace(기록.spend, official_usd=float("nan")))
    with pytest.raises(ShapeError, match="유한"):
        dumps_record(나쁜_기록)
    with pytest.raises(ShapeError, match="유한"):
        write_record(tmp_path, 나쁜_기록)
    assert list(tmp_path.iterdir()) == []
    목록 = _목록()
    나쁜_목록 = replace(목록, tasks=(replace(목록.tasks[0], round_cap_usd=float("inf")),))
    with pytest.raises(ShapeError, match="유한"):
        dumps_task_list(나쁜_목록)


def test_UTF_8_이_아닌_파일은_거부한다(tmp_path: Path) -> None:
    경로 = tmp_path / "x.json"
    경로.write_bytes(b"\xff\xfe{")
    with pytest.raises(ShapeError, match="UTF-8"):
        read_task_list(경로)
    with pytest.raises(ShapeError, match="UTF-8"):
        read_record(경로)


# --- 과제 목록의 규칙 ---


def test_파일럿_목록에_든_본_측정_과제는_거부한다() -> None:
    with pytest.raises(ShapeError, match="파일럿"):
        parse_task_list(_바꿔(dumps_task_list(_목록()), ("kind",), LIST_PILOT))
    파일럿 = dumps_task_list(_목록(_과제(pilot=True, tier=TIER_PILOT), kind=LIST_PILOT))
    with pytest.raises(ShapeError, match="파일럿"):
        parse_task_list(_바꿔(파일럿, ("kind",), LIST_MAIN))


def test_파일럿_과제의_층은_파일럿이다() -> None:
    파일럿 = dumps_task_list(_목록(_과제(pilot=True, tier=TIER_PILOT), kind=LIST_PILOT))
    with pytest.raises(ShapeError, match="층"):
        parse_task_list(_바꿔(파일럿, ("tasks", 0, "tier"), TIER_SMALL))
    with pytest.raises(ShapeError, match="층"):
        parse_task_list(_바꿔(dumps_task_list(_목록()), ("tasks", 0, "tier"), TIER_PILOT))


def test_겹친_과제_id_와_실행_차례는_거부한다() -> None:
    둘 = dumps_task_list(_목록(_과제(), _과제(task_id="x-02", order=1)))
    with pytest.raises(ShapeError, match="과제 id"):
        parse_task_list(_바꿔(둘, ("tasks", 1, "task_id"), "model-rerun-01"))
    with pytest.raises(ShapeError, match="실행 차례"):
        parse_task_list(_바꿔(둘, ("tasks", 1, "order"), 0))


def test_갈래_계획에_같은_갈래가_두_번_들_수_있다() -> None:
    목록 = _목록(_과제(arm_plan=("A", "A", "E")))
    assert parse_task_list(dumps_task_list(목록)).tasks[0].arm_plan == ("A", "A", "E")


# --- 숨은 시험 파일 ---


def test_노드_ID_에서_숨은_시험_파일을_꺼낸다() -> None:
    assert hidden_test_file("tests/tools/test_x.py::test_a") == "tests/tools/test_x.py"
    assert hidden_test_file("tests/tools/test_x.py::TestC::test_m[1-2]") == "tests/tools/test_x.py"
    assert hidden_test_file("tests/test_y.py::test_p[a::b]") == "tests/test_y.py"
    with pytest.raises(ShapeError, match="노드 ID"):
        hidden_test_file("tests/test_y.py")


def test_과제의_숨은_시험_파일은_겹치지_않고_처음_나온_차례다() -> None:
    assert hidden_test_files(_과제()) == (
        "tests/tools/test_rerun_files.py",
        "tests/tools/test_other.py",
    )


def test_숨은_시험_ID_가_노드_ID_가_아니면_목록_읽기가_거부한다() -> None:
    글 = _바꿔(dumps_task_list(_목록()), ("tasks", 0, "hidden_tests"), ["tests/a.py"])
    with pytest.raises(ShapeError, match="노드 ID"):
        parse_task_list(글)


@pytest.mark.parametrize(
    ("노드", "까닭"),
    [
        ("C:/x/tests/test_a.py::test_a", "드라이브 문자"),
        ("/tmp/tests/test_a.py::test_a", "절대 경로"),
        ("tests/../src/test_a.py::test_a", "위로 가는 조각"),
        ("tests/./test_a.py::test_a", "제자리 조각"),
        ("tests\\test_a.py::test_a", "역슬래시"),
        ("src/test_a.py::test_a", "tests 밖"),
        ("tests/helpers.py::test_a", "test_ 로 시작하지 않는 파일"),
        ("tests/test_a.txt::test_a", "파이썬 파일이 아니다"),
        ("tests//test_a.py::test_a", "빈 조각"),
        ("tests/test_a.py::test_a\n", "줄바꿈"),
        ("tests/test_a.py::test_a[\u2028]", "줄 구분 문자"),
        ("tests/te\nst_a.py::test_a", "파일 부분의 줄바꿈"),
    ],
)
def test_숨은_시험의_파일_부분은_tests_아래_상대_경로만_받는다(노드: str, 까닭: str) -> None:
    with pytest.raises(ShapeError, match="노드 ID"):
        hidden_test_file(노드)
    글 = _바꿔(dumps_task_list(_목록()), ("tasks", 0, "hidden_tests"), [노드])
    with pytest.raises(ShapeError, match="노드 ID"):
        parse_task_list(글)


@pytest.mark.parametrize(
    "경로",
    [
        "tests/conftest.py",
        "tests/tools/helpers.py",
        "tests/tools/_fixture-data.py",
        "conftest.py",
        "src/agent_os/conftest.py",
    ],
)
def test_시험_지원_파일은_conftest_와_tests_아래_시험_아닌_파이썬_파일이다(경로: str) -> None:
    assert is_support_file(경로)
    글 = _바꿔(dumps_task_list(_목록()), ("tasks", 0, "support_files"), [경로])
    assert parse_task_list(글).tasks[0].support_files == (경로,)


@pytest.mark.parametrize(
    ("경로", "까닭"),
    [
        ("tests/test_a.py", "시험 파일"),
        ("src/agent_os/helpers.py", "tests 밖의 conftest 아닌 파일"),
        ("tests/data.json", "파이썬 파일이 아니다"),
        ("/abs/tests/conftest.py", "절대 경로"),
        ("C:/x/tests/conftest.py", "드라이브 문자"),
        ("tests/../conftest.py", "위로 가는 조각"),
        ("tests\\conftest.py", "역슬래시"),
        ("tests/.hidden/conftest.py", "점으로 시작하는 조각"),
        ("tests/con\ntest.py", "줄바꿈"),
        ("tests/conftest\u2029.py", "문단 구분 문자"),
    ],
)
def test_시험_지원_파일_칸은_허용_꼴_밖을_거부한다(경로: str, 까닭: str) -> None:
    assert not is_support_file(경로)
    글 = _바꿔(dumps_task_list(_목록()), ("tasks", 0, "support_files"), [경로])
    with pytest.raises(ShapeError, match="support_files"):
        parse_task_list(글)


def test_시험_파일은_tests_아래_test_로_시작하는_py_뿐이다() -> None:
    assert is_test_file("tests/test_a.py")
    assert is_test_file("tests/tools/test_rerun-x.py")
    assert not is_test_file("tests/conftest.py")
    assert not is_test_file("test_a.py")
    assert not is_test_file("tests/../tests/test_a.py")
    # 못 보는 것: pytest 설정이 더 모으는 `*_test.py` 는 지원 파일이다
    assert not is_test_file("tests/a_test.py")
    assert is_support_file("tests/a_test.py")


# --- 끝 ---


def test_끝의_종류와_하위_이유의_모임() -> None:
    assert CAP_REASONS == ("개입", "세션", "예산", "시간")
    assert NOT_MEASURED_REASONS == ("한도", "오염", "모델", "설정", "준비", "호출", "중단")


@pytest.mark.parametrize(
    ("kind", "reason", "까닭"),
    [
        (END_DONE, "개입", "하위 이유"),
        (END_CAPPED, None, "하위 이유"),
        (END_CAPPED, "한도", "하위 이유"),
        (END_NOT_MEASURED, "예산", "하위 이유"),
        (END_NOT_MEASURED, None, "하위 이유"),
        ("멈춤", None, "end.kind"),
    ],
)
def test_종류와_맞지_않는_하위_이유는_거부한다(kind: str, reason: str | None, 까닭: str) -> None:
    # 끝남은 결과 커밋이 있는 기록에서, 그 밖은 결과가 빈 기록에서 바꿔 다른 거부가 먼저 걸리지 않게
    # 한다.
    기록 = _기록() if kind == END_DONE else _측정아님("한도")
    글 = _바꿔(dumps_record(기록), ("end", "kind"), kind)
    with pytest.raises(ShapeError, match=까닭):
        parse_record(_바꿔(글, ("end", "reason"), reason))


def test_호출의_종류는_첫_인계_개입이다() -> None:
    assert (CALL_FIRST, CALL_HANDOFF, CALL_INTERVENTION) == ("첫", "인계", "개입")
    인계 = replace(_세션().calls[0], kind=CALL_HANDOFF)
    기록 = _기록(sessions=(replace(_세션(), calls=(인계,)),))
    assert parse_record(dumps_record(기록)).sessions[0].calls[0].kind == CALL_HANDOFF


def test_하위_이유_중단을_받는다() -> None:
    assert parse_record(dumps_record(_측정아님("중단"))).end.reason == "중단"


def test_풀리는_시각을_모르는_한도는_빈_값이고_0_과_가른다() -> None:
    모름 = parse_record(dumps_record(_측정아님("한도")))
    영 = parse_record(dumps_record(_측정아님("한도", resets_at=0)))
    assert 모름.end.resets_at is None
    assert 영.end.resets_at == 0


def test_한도가_아닌_끝에는_resetsAt_이_없다() -> None:
    with pytest.raises(ShapeError, match="resets_at"):
        parse_record(_바꿔(dumps_record(_측정아님("오염")), ("end", "resets_at"), 1))


# --- 결과의 빈 값 ---


def test_돌지_않은_몫은_빈_값이고_0_과_가른다() -> None:
    읽은 = parse_record(dumps_record(_측정아님("준비")))
    assert 읽은.outcome.commit is None
    assert 읽은.outcome.gates is None
    assert 읽은.outcome.hidden is None
    영 = _기록(
        outcome=replace(
            _기록().outcome,
            gates=_초록_게이트(),
            hidden=Hidden(passed=0, total=0, failed=()),
        )
    )
    읽은영 = parse_record(dumps_record(영))
    assert 읽은영.outcome.gates is not None
    assert 읽은영.outcome.gates[0].exit_code == 0
    assert 읽은영.outcome.hidden == Hidden(passed=0, total=0, failed=())


def test_끝남이_아닌_회차에는_게이트와_숨은_시험이_없다() -> None:
    끝: Json = {"kind": END_CAPPED, "reason": "시간", "resets_at": None}
    with pytest.raises(ShapeError, match="끝남"):
        parse_record(_바꿔(dumps_record(_기록()), ("end",), 끝))


def test_결과_작업_트리의_준비가_실패하면_게이트와_숨은_시험이_없다() -> None:
    실패 = SetupFailure(command=SETUP_COMMANDS[0], exit_code=2)
    좋은 = _기록(outcome=replace(_기록().outcome, setup_failure=실패, gates=None, hidden=None))
    assert parse_record(dumps_record(좋은)).outcome.setup_failure == 실패
    with pytest.raises(ShapeError, match="setup_failure.command"):
        parse_record(
            _바꿔(dumps_record(좋은), ("outcome", "setup_failure", "command"), "uv sync; rm")
        )
    실패_칸: Json = {"command": SETUP_COMMANDS[0], "exit_code": 2}
    with pytest.raises(ShapeError, match="준비가 실패한"):
        parse_record(_바꿔(dumps_record(_기록()), ("outcome", "setup_failure"), 실패_칸))


def test_결과_커밋과_고른_규칙이_맞아야_한다() -> None:
    with pytest.raises(ShapeError, match="규칙"):
        parse_record(_바꿔(dumps_record(_기록()), ("outcome", "rule"), RULE_NONE))
    커밋_없음 = _바꿔(dumps_record(_기록()), ("outcome", "commit"), None)
    with pytest.raises(ShapeError, match="준비·게이트"):
        parse_record(_바꿔(커밋_없음, ("outcome", "rule"), RULE_NONE))


def test_끝남인_회차에는_결과_커밋이_있다() -> None:
    글 = dumps_record(_측정아님("한도"))
    글 = _바꿔(글, ("end",), {"kind": END_DONE, "reason": None, "resets_at": None})
    with pytest.raises(ShapeError, match="끝남.*결과 커밋"):
        parse_record(글)


def _게이트_칸(*명령: str) -> Json:
    return [{"command": c, "exit_code": 0, "timed_out": False} for c in 명령]


@pytest.mark.parametrize(
    "게이트",
    [
        _게이트_칸(),
        _게이트_칸(*GATE_COMMANDS[:2]),
        _게이트_칸(*reversed(GATE_COMMANDS)),
        _게이트_칸("true"),
    ],
)
def test_게이트는_정해진_셋이_이_차례로_든다(게이트: Json) -> None:
    with pytest.raises(ShapeError, match="gates"):
        parse_record(_바꿔(dumps_record(_기록()), ("outcome", "gates"), 게이트))


def test_실패한_숨은_시험_노드는_겹치지_않는다() -> None:
    숨은: Json = {"passed": 1, "total": 3, "failed": ["tests/test_a.py::t", "tests/test_a.py::t"]}
    with pytest.raises(ShapeError, match="겹친다"):
        parse_record(_바꿔(dumps_record(_기록()), ("outcome", "hidden"), 숨은))


@pytest.mark.parametrize(
    ("노드", "까닭"),
    [
        ("tests/a.py", "노드 ID"),
        ("tests/test_a.py::t\n글", "failed"),
        ("tests/test_a.py::t\t글", "failed"),
    ],
)
def test_실패한_숨은_시험은_노드_ID_꼴이고_제어_문자가_없다(노드: str, 까닭: str) -> None:
    숨은: Json = {"passed": 2, "total": 3, "failed": [노드]}
    with pytest.raises(ShapeError, match=까닭):
        parse_record(_바꿔(dumps_record(_기록()), ("outcome", "hidden"), 숨은))


# 손으로 고른 목록이 아니라 str.splitlines 가 줄을 끊는 문자 전부다.
_줄을_끊는_문자 = [
    chr(c) for c in range(sys.maxunicode + 1) if len(f"a{chr(c)}b".splitlines()) == 2
]


@pytest.mark.parametrize("문자", _줄을_끊는_문자, ids=ascii)
def test_회차_폴더_이름과_실패_노드는_줄을_끊는_문자를_모두_거부한다(문자: str) -> None:
    폴더 = f"model-rerun-01-C-2-a1{문자}b2"
    with pytest.raises(ShapeError, match="round_dir_name"):
        parse_record(_바꿔(dumps_record(_기록()), ("round_dir_name",), 폴더))
    숨은: Json = {"passed": 2, "total": 3, "failed": [f"tests/test_a.py::t{문자}글"]}
    with pytest.raises(ShapeError, match="failed"):
        parse_record(_바꿔(dumps_record(_기록()), ("outcome", "hidden"), 숨은))


def test_숨은_시험의_통과_수와_실패_노드_수의_합이_전체다() -> None:
    with pytest.raises(ShapeError, match="전체 수"):
        parse_record(_바꿔(dumps_record(_기록()), ("outcome", "hidden", "passed"), 3))


@pytest.mark.parametrize(
    "폴더",
    [
        "model-rerun-01-C-3-a1b2c3",
        "model-rerun-01-A-2-a1b2c3",
        "other-01-C-2-a1b2c3",
        "note",
    ],
)
def test_회차_폴더_이름은_이_회차의_폴더다(폴더: str) -> None:
    with pytest.raises(ShapeError, match="폴더 이름"):
        parse_record(_바꿔(dumps_record(_기록()), ("round_dir_name",), 폴더))


@pytest.mark.parametrize(
    "폴더",
    [
        "D:/rerun/model-rerun-01-C-2-a1b2c3",
        "E:\\r\\model-rerun-01-C-2-ff",
        "/model-rerun-01-C-2-ff",
    ],
)
def test_회차_폴더_칸은_사람이_준_뿌리_경로를_받지_않는다(폴더: str) -> None:
    with pytest.raises(ShapeError, match="폴더 이름"):
        parse_record(_바꿔(dumps_record(_기록()), ("round_dir_name",), 폴더))


# --- records/ 의 파일 이름과 덮어쓰기 ---


def test_기록_파일_이름은_과제_갈래_회차_번호에서_난다() -> None:
    assert record_file_name("model-rerun-01", "C", 2) == "model-rerun-01-C-2.json"
    with pytest.raises(ShapeError, match="갈래"):
        record_file_name("model-rerun-01", "F", 2)
    with pytest.raises(ShapeError, match="회차 번호"):
        record_file_name("model-rerun-01", "C", 0)


def test_이미_있는_기록_파일은_덮지_않는다(tmp_path: Path) -> None:
    경로 = write_record(tmp_path, _기록())
    처음 = 경로.read_bytes()
    with pytest.raises(FileExistsError):
        write_record(tmp_path, _기록(condition_version=2, interventions=2))
    assert 경로.read_bytes() == 처음


def test_링크한_뒤_임시_파일을_지우기_전에_같은_회차를_다시_써도_기록이_덮이지_않는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # 같은 프로세스의 두 스레드가 같은 회차를 쓰는 틈을 차례로 흉내 낸다. 첫 쓰기의 임시 파일이
    # 남은 채 둘째 쓰기가 같은 이름을 "w"로 열면, 하드 링크라 이미 붙은 기록이 잘리고 덮인다.
    def 지우지_않는다(self: Path, *, missing_ok: bool = False) -> None:
        return None

    monkeypatch.setattr(Path, "unlink", 지우지_않는다)
    경로 = write_record(tmp_path, _기록())
    처음 = 경로.read_bytes()
    with pytest.raises(FileExistsError):
        write_record(tmp_path, _기록(interventions=2))
    assert 경로.read_bytes() == 처음


class _반쯤_쓰고_멈춘다:
    """디스크가 찬 것처럼 받은 글의 절반만 쓰고 `OSError`를 낸다."""

    def __init__(self, f: IO[str]) -> None:
        self.f = f

    def __enter__(self) -> _반쯤_쓰고_멈춘다:
        return self

    def __exit__(self, *_: object) -> None:
        self.f.close()

    def write(self, s: str) -> int:
        self.f.write(s[: len(s) // 2])
        self.f.flush()
        raise OSError("디스크가 찼다")


def test_쓰다_실패하면_기록_파일이_남지_않고_다시_쓸_수_있다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    진짜_open = Path.open

    def 고장난_open(
        self: Path, mode: str = "r", *, encoding: str | None = None, newline: str | None = None
    ) -> _반쯤_쓰고_멈춘다:
        return _반쯤_쓰고_멈춘다(진짜_open(self, mode, encoding=encoding, newline=newline))

    monkeypatch.setattr(Path, "open", 고장난_open)
    with pytest.raises(OSError, match="디스크가 찼다"):
        write_record(tmp_path, _기록())
    monkeypatch.undo()
    assert list(tmp_path.iterdir()) == []
    assert read_record(write_record(tmp_path, _기록())) == _기록()


# --- 회차 폴더 이름과 다음 회차 번호 ---


def test_회차_폴더_이름을_짓고_푼다() -> None:
    이름 = round_dir_name("model-rerun-01", "C", 3, "a1b2c3")
    assert 이름 == "model-rerun-01-C-3-a1b2c3"
    풀린 = parse_round_dir_name(이름)
    assert 풀린 is not None
    assert (풀린.task_id, 풀린.arm, 풀린.round_no, 풀린.token) == (
        "model-rerun-01",
        "C",
        3,
        "a1b2c3",
    )


@pytest.mark.parametrize(
    "이름",
    [
        "model-rerun-01-C-3",
        "model-rerun-01-F-3-a1b2c3",
        "model-rerun-01-C-x-a1b2c3",
        ".tidy-trash",
        "C-3-a1",
    ],
)
def test_회차_폴더가_아닌_이름은_풀지_않는다(이름: str) -> None:
    assert parse_round_dir_name(이름) is None


def test_회차_폴더_이름의_난수는_정해진_꼴이다() -> None:
    with pytest.raises(ShapeError, match="난수"):
        round_dir_name("model-rerun-01", "C", 3, "a-b")


def test_다음_회차_번호는_조건_판을_넘어_이어진다(tmp_path: Path) -> None:
    write_record(tmp_path, _기록(round_no=1, condition_version=1))
    write_record(tmp_path, _기록(round_no=2, condition_version=2))
    write_record(tmp_path, _기록(arm="A", round_no=5))
    write_record(tmp_path, _기록(task_id="x-model-rerun-01", round_no=9))
    이름들 = [p.name for p in tmp_path.iterdir()]
    assert next_round_no("model-rerun-01", "C", 이름들, []) == 3
    assert next_round_no("model-rerun-01", "B", 이름들, []) == 1
    assert next_round_no("rerun-01", "C", 이름들, []) == 1


def test_다음_회차_번호는_기록이_없는_회차_폴더를_비켜_간다() -> None:
    기록들 = ["model-rerun-01-C-1.json", "README.md"]
    폴더들 = [
        "model-rerun-01-C-4-ffffff",
        "model-rerun-01-C-2-000000",
        "other",
        "model-rerun-01-A-7-abcdef",
    ]
    assert next_round_no("model-rerun-01", "C", 기록들, 폴더들) == 5


# --- 판정이 읽는 칸 ---


def test_판정이_읽는_칸을_모은다(tmp_path: Path) -> None:
    경로 = write_record(tmp_path, _기록())
    본 = read_judge_view(경로)
    assert 본 == judge_view(_기록())
    assert (본.task_id, 본.arm, 본.round_no, 본.pilot) == ("model-rerun-01", "C", 2, False)
    assert (본.condition_version, 본.claude_version) == (1, "2.1.302 (Claude Code)")
    assert 본.end == End(kind=END_DONE, reason=None, resets_at=None)
    assert 본.gates_green is False
    assert 본.hidden_passed is False
    assert (본.cost_claude_code_usd, 본.cost_official_usd) == (8.75, 9.5)
    assert (본.interventions, 본.asked_at_end) == (1, True)
    assert 본.cost_substituted is True
    assert 본.official_substituted is True
    assert 본.setup_failed is False
    assert 본.tokens == Tokens(input=10, output=20, cache_read=30, cache_write=40, thinking=None)
    assert (본.wall_seconds, 본.denied_calls) == (1234.5, 2)
    assert 본.utilization_end[1] == Window(window="seven_day", utilization=0.97)


def test_판정이_읽는_게이트와_숨은_시험은_돌지_않았으면_빈_값이다() -> None:
    본 = judge_view(_측정아님("한도"))
    assert 본.gates_green is None
    assert 본.hidden_passed is None
    초록 = judge_view(
        _기록(
            outcome=replace(
                _기록().outcome,
                gates=_초록_게이트(),
                hidden=Hidden(passed=3, total=3, failed=()),
            )
        )
    )
    assert 초록.gates_green is True
    assert 초록.hidden_passed is True
    빈 = judge_view(
        _기록(outcome=replace(_기록().outcome, hidden=Hidden(passed=0, total=0, failed=())))
    )
    assert 빈.hidden_passed is False


# --- 하위 프로세스를 끌어오지 않는다 ---

_허용_import = {
    "__future__",
    "dataclasses",
    "json",
    "math",
    "os",
    "re",
    "pathlib",
    "collections.abc",
}


def test_이_모듈은_표준_라이브러리의_정해진_모듈만_import_한다() -> None:
    원본 = Path(__file__).resolve().parents[2] / "tools" / "rerun_files.py"
    나무 = ast.parse(원본.read_text(encoding="utf-8"))
    든 = set[str]()
    for 마디 in ast.walk(나무):
        if isinstance(마디, ast.Import):
            든.update(a.name for a in 마디.names)
        elif isinstance(마디, ast.ImportFrom):
            든.add("." * 마디.level + (마디.module or ""))
    assert 든 <= _허용_import, 든 - _허용_import
    assert "subprocess" not in 든
    # os 는 통째로 허용했으므로 쓰는 이름을 좁힌다(os.system 같은 하위 프로세스 길을 막는다).
    os_이름 = {
        마디.attr
        for 마디 in ast.walk(나무)
        if isinstance(마디, ast.Attribute)
        and isinstance(마디.value, ast.Name)
        and 마디.value.id == "os"
    }
    assert os_이름 <= {"getpid", "urandom", "link"}, os_이름
    assert all(
        m in sys.stdlib_module_names or m.split(".")[0] in sys.stdlib_module_names for m in 든
    )
