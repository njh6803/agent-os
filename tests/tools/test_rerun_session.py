"""tools/rerun_session.py: 회차의 세션 하나를 가짜 claude 로 띄우고 회차 기록을 짓는다.

가짜는 `tests/tools/fake_claude.py`이고 `sys.executable`로 띄워 리눅스 CI 에서도 돈다. 첫 줄의 틀은
`tools/open_session.ps1`의 `Convert-StartLine`을 pwsh 로 불러 견준다(pwsh 가 없으면 실패한다,
`.claude/rules/tests.md`).
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

import pytest
from tests.tools import fake_claude as fake
from tools.rerun_files import (
    ARMS,
    CALL_FIRST,
    END_DONE,
    RULE_BRANCH,
    RULE_NONE,
    RULE_ONLY,
    End,
    Json,
    LineCount,
    Task,
    Tokens,
    arm_label,
    read_record,
    write_record,
)
from tools.rerun_round import ROOT, RoundDir, create_round_dir, session_env
from tools.rerun_session import (
    CallRun,
    Elsewhere,
    Launched,
    budget_text,
    call_record,
    claude_version,
    count_lines,
    directive,
    drive,
    first_message,
    launch,
    local_branches,
    new_session_id,
    outcome_of,
    pick_result_commit,
    result_text,
    round_record,
    session_command,
    session_cost,
    start_line,
    summarize_call,
    ticket_title,
    transcript_counts,
)
from tools.run_hooks import REPO_LOCATION_VARS

PROBE = ROOT / ".scratch" / "model-rerun" / "probes" / "headless_flags" / "2026-10-22"
TICKET = ".scratch/rerun-x/issues/03-thing.md"
TASK = Task(
    task_id="rerun-x-03",
    ticket=TICKET,
    base="b" * 40,
    merge="c" * 40,
    branch="feature/03-thing",
    tier="작은",
    size=4,
    order=0,
    pilot=False,
    pr_cost_usd=10.0,
    round_cap_usd=40.0,
    hidden_tests=("tests/test_x.py::test_a",),
    support_files=(),
    original_model_effort=None,
    arm_plan=("A",),
)
ARM = ARMS[0]
NOTHING = Elsewhere(
    official_usd=0.0,
    tokens=Tokens(input=None, output=None, cache_read=None, cache_write=None, thinking=None),
    substitutes=(),
    denied_calls=0,
    utilization_start=(),
    utilization_end=(),
    contamination=(),
    model_mismatch=(),
)


def _round(tmp_path: Path, token: str = "t1") -> RoundDir:
    place = create_round_dir(tmp_path / "뿌리", TASK.task_id, ARM.name, 1, token=token)
    place.clone.mkdir()
    return place


def _env(place: RoundDir, config: Path) -> dict[str, str]:
    return session_env(os.environ, config_dir=str(config), round_dir=place)


def _launch(place: RoundDir, config: Path, *, timeout: float = 60.0, sid: str = "") -> Launched:
    return launch(
        place,
        claude=fake.claude(),
        arm=ARM,
        env=_env(place, config),
        ticket=TICKET,
        directive_text=directive(TASK, ARM, "그것을 짓는다"),
        budget_usd=12.345,
        timeout=timeout,
        session_id=(lambda: sid) if sid else new_session_id,
    )


def _jsonl(*events: object) -> list[str]:
    return [json.dumps(e, ensure_ascii=False) + "\n" for e in events]


# --- 첫 메시지와 지시문 ---

# `open_session.ps1`의 AST 에서 함수 하나만 떼어 부른다. 스크립트 몸(UIAutomation)은 돌지 않는다.
_PWSH_START_LINE = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$parser = [System.Management.Automation.Language.Parser]
$ast = $parser::ParseFile($env:OPEN_SESSION, [ref]$null, [ref]$null)
$kind = [System.Management.Automation.Language.FunctionDefinitionAst]
$f = $ast.Find({ param($n) $n -is $kind -and $n.Name -eq 'Convert-StartLine' }, $true)
. ([scriptblock]::Create($f.Extent.Text))
[Console]::Out.Write((Convert-StartLine $env:START_LINE $env:START_ROOT))
"""


def test_첫_줄의_틀은_open_session_ps1_의_Convert_StartLine_과_같다(tmp_path: Path) -> None:
    root = tmp_path / "클론 자리"
    (root / ".claude" / "skills" / "implement").mkdir(parents=True)
    (root / ".claude" / "skills" / "implement" / "SKILL.md").write_text("# x\n", encoding="utf-8")
    env = {
        **os.environ,
        "OPEN_SESSION": str(ROOT / "tools" / "open_session.ps1"),
        "START_LINE": f"/implement {TICKET}",
        "START_ROOT": str(root),
    }
    try:
        done = subprocess.run(
            ["pwsh", "-NoProfile", "-NonInteractive", "-Command", _PWSH_START_LINE],
            env=env,
            capture_output=True,
            timeout=120,
            check=False,
        )
    except FileNotFoundError:
        pytest.fail("pwsh 가 없다. 이 시험은 PowerShell 7 로 스크립트의 함수를 부른다")

    assert done.returncode == 0, done.stderr.decode("utf-8", "replace")
    assert done.stdout.decode("utf-8") == start_line(str(root), TICKET)


def test_지시문은_명세의_틀이고_다섯_갈래는_모델_줄만_다르다() -> None:
    texts = [directive(TASK, arm, "그것을 짓는다") for arm in ARMS]

    assert texts[0].splitlines() == [
        f"다음 작업: {TICKET}. 그것을 짓는다",
        "다음 단계: 구현",
        "어디서: 새 세션",
        f"시작 프롬프트: /implement {TICKET}",
        "브랜치: feature/03-thing",
        "모델: Opus 5.5 / xhigh",
        "읽을 것: 없음",
        "이어받을 상태: 없음",
        "확인할 선행 조건: 없음",
        "이번 요청 범위: 구현·리뷰·커밋까지",
    ]
    for arm, text in zip(ARMS, texts, strict=True):
        differ = [
            (a, b) for a, b in zip(texts[0].splitlines(), text.splitlines(), strict=True) if a != b
        ]
        assert differ == (
            [] if arm is ARMS[0] else [("모델: Opus 5.5 / xhigh", f"모델: {arm_label(arm.name)}")]
        )
    assert "워크트리" not in texts[0]


@pytest.mark.parametrize(
    ("text", "title"),
    [
        ("# 03: 그것을 짓는다 — 길게\n\n본문", "그것을 짓는다 — 길게"),
        ("머리말\n# 그냥 제목\n", "그냥 제목"),
        ("#  12:   띄어 쓴 머리\n", "띄어 쓴 머리"),
    ],
)
def test_제목은_첫_제목_줄에서_머리를_뗀_글이다(text: str, title: str) -> None:
    assert ticket_title(text) == title


def test_제목_줄이_없는_티켓은_거부한다() -> None:
    with pytest.raises(ValueError, match="제목 줄"):
        ticket_title("## 둘째 수준만\n본문\n")


def test_첫_메시지는_첫_줄_빈_줄_지시문이다() -> None:
    text = directive(TASK, ARM, "제목")
    message = first_message("C:/클론", TICKET, text)

    assert message == f"{start_line('C:/클론', TICKET)}\n\n{text}"
    assert "`C:/클론`" in message.splitlines()[0]


# --- 띄우기 ---


def test_명령은_설계의_것에_세션_id_와_남은_예산을_붙이고_모델은_전체_이름이다() -> None:
    command = session_command(["claude.exe"], ARMS[3], "s-1", 7.019)

    assert command == [
        "claude.exe",
        "-p",
        "--model",
        "claude-sonnet-5-5",
        "--effort",
        "high",
        "--permission-mode",
        "auto",
        "--setting-sources",
        "user,project,local",
        "--strict-mcp-config",
        "--output-format",
        "stream-json",
        "--verbose",
        "--session-id",
        "s-1",
        "--max-budget-usd",
        "7.01",
    ]


@pytest.mark.parametrize(
    ("usd", "text"),
    [
        (0.29, "0.29"),  # `math.floor(0.29 * 100)`은 28이다
        (0.57, "0.57"),
        (1.15, "1.15"),
        (12.345, "12.34"),
        (7.019, "7.01"),
        (0.0, "0.00"),
        (-0.0, "0.00"),
        (-0.004, "0.00"),
        (-3.0, "0.00"),
    ],
)
def test_예산은_센트_아래만_버리고_다시_넣어도_같다(usd: float, text: str) -> None:
    assert budget_text(usd) == text
    assert budget_text(float(text)) == text
    assert session_command(["c"], ARM, "s", float(text))[-1] == text


def test_가짜가_받은_인자_표준_입력_환경과_작업_폴더(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GH_TOKEN", "ghp_가짜토큰")
    place = _round(tmp_path)
    config = tmp_path / "설정"
    fake.write_script(config, calls=[fake.call(_events_done(0.4))])

    got = _launch(place, config)

    [seen] = fake.read_calls(config)
    argv = seen["argv"]
    assert isinstance(argv, list)
    assert argv[argv.index("--model") + 1] == "claude-opus-5-5"
    assert argv[argv.index("--effort") + 1] == "xhigh"
    assert argv[argv.index("--session-id") + 1] == got.session_id
    assert argv[argv.index("--max-budget-usd") + 1] == "12.34"
    assert got.budget_usd == 12.34
    stdin = seen["stdin"]
    assert isinstance(stdin, str)
    assert stdin == first_message(str(place.clone), TICKET, directive(TASK, ARM, "그것을 짓는다"))
    # 첫 줄의 연 저장소는 넘긴 작업 폴더의 글 그대로이고, 가짜가 본 작업 폴더도 그 폴더다.
    assert f"`{place.clone}`" in stdin.splitlines()[0]
    cwd = seen["cwd"]
    assert isinstance(cwd, str)
    assert cwd.replace("\\", "/").casefold() == str(place.clone).replace("\\", "/").casefold()
    # 윈도의 자식은 환경 변수 이름을 대문자로 본다(`os.environ`). 리눅스 CI에서는 넘기지 않은
    # `LC_CTYPE`이 가짜의 환경에 더 있었다. `LANG`·`LC_ALL`이 없어 로캘이 C인 파이썬이 PEP 538의
    # 로캘 강제로 더한 것으로 읽었다(재지 않았다). 시험이 보려는 것은 러너가 넘긴 이름이므로
    # 넘기지 않은 그 이름만 뺀다.
    names = seen["env"]
    assert isinstance(names, list)
    expected = sorted(n.upper() for n in _env(place, config))
    added = {"LC_CTYPE"} - set(expected)
    assert sorted(str(n).upper() for n in names if str(n).upper() not in added) == expected
    assert "GH_TOKEN" not in names
    assert got.drove.exit_code == 0 and not got.drove.timed_out


def test_띄우기_전에_세션_id_를_회차_폴더의_파일에_덧붙인다(tmp_path: Path) -> None:
    place = _round(tmp_path)
    place.session_ids.write_text("앞선-세션\n", encoding="utf-8")

    with pytest.raises(OSError):  # 띄울 실행 파일이 없어도 세션 id 는 이미 적혀 있다
        launch(
            place,
            claude=[str(tmp_path / "없는-claude")],
            arm=ARM,
            env=_env(place, tmp_path / "설정"),
            ticket=TICKET,
            directive_text="지시문",
            budget_usd=5.0,
            timeout=10.0,
            session_id=lambda: "새-세션",
        )

    assert place.session_ids.name == "session-ids.txt"
    assert place.session_ids.read_text(encoding="utf-8").splitlines() == ["앞선-세션", "새-세션"]


def test_원본_줄은_회차_폴더의_stream_에_받은_그대로_남는다(tmp_path: Path) -> None:
    place = _round(tmp_path)
    config = tmp_path / "설정"
    fake.write_script(config, calls=[fake.call([*_events_done(0.4), "풀지 못한 줄"])])

    got = _launch(place, config, sid="11111111-2222-4333-8444-555555555555")

    assert got.stream_file.parent == place.stream
    assert got.stream_file.name == "01-11111111-2222-4333-8444-555555555555.jsonl"
    assert got.stream_file.read_text(encoding="utf-8") == "".join(got.drove.lines)
    assert got.drove.lines[-1] == "풀지 못한 줄\n"


def test_시간_제한을_넘긴_호출은_끄고_종료_코드를_비운다(tmp_path: Path) -> None:
    place = _round(tmp_path)
    config = tmp_path / "설정"
    # 가짜는 init 을 낸 뒤 멈춘다. 기한은 부하가 큰 때도 가짜가 init 을 낼 만큼 둔다.
    fake.write_script(config, calls=[fake.call([fake.init_event()], hang=600)])
    started = time.monotonic()

    got = _launch(place, config, timeout=20.0)

    assert got.drove.timed_out
    assert got.drove.exit_code is None
    assert got.summary.init is not None  # 끄기 전에 받은 줄은 남는다
    assert time.monotonic() - started < 200


def test_손자가_출력을_쥐어도_스스로_끝난_호출은_끈_호출이_아니다(tmp_path: Path) -> None:
    place = _round(tmp_path)
    config = tmp_path / "설정"
    # 손자는 호출의 시간 제한보다 오래 출력을 쥔다. 옛 판은 EOF 를 마감까지 기다려 끈 호출로 적었다.
    # 끝난 자식을 알아보면 한 번 읽는 몫과 drain 만 기다린다(홀로 돌면 약 15초).
    fake.write_script(config, calls=[fake.call(_events_done(0.4), linger=150)])
    started = time.monotonic()

    got = _launch(place, config, timeout=120.0)

    assert not got.drove.timed_out
    assert got.drove.exit_code == 0
    assert got.summary.results  # 끝나기 전에 낸 줄은 받았다
    assert time.monotonic() - started < 90


def test_마감에_닿았을_때_이미_끝난_자식은_끈_호출이_아니다(tmp_path: Path) -> None:
    place = _round(tmp_path)
    config = tmp_path / "설정"
    fake.write_script(config, calls=[fake.call(_events_done(0.4), linger=60)])
    ticks = iter([0.0])

    def clock() -> float:  # 마감을 잡는 첫 부름 뒤에는 자식이 끝날 만큼 쉬고 마감을 넘긴다
        first = next(ticks, None)
        if first is not None:
            return first
        time.sleep(15)
        return 1e9

    got = drive(
        session_command(fake.claude(), ARM, "s-1", 1.0),
        cwd=str(place.clone),
        env=_env(place, config),
        message="메시지",
        stream_file=place.stream / "01-s-1.jsonl",
        timeout=10.0,
        clock=clock,
    )

    assert not got.timed_out
    assert got.exit_code == 0


def test_기록_파일을_열지_못하면_띄운_자식을_끄고_예외를_올린다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    place = _round(tmp_path)
    config = tmp_path / "설정"
    fake.write_script(config, calls=[fake.call([fake.init_event()], hang=600)])
    started: list[subprocess.Popen[bytes]] = []

    class Recording(subprocess.Popen[bytes]):
        def __init__(
            self,
            args: list[str],
            *,
            cwd: str,
            env: dict[str, str],
            stdin: int,
            stdout: int,
            stderr: int,
        ) -> None:
            super().__init__(args, cwd=cwd, env=env, stdin=stdin, stdout=stdout, stderr=stderr)
            started.append(self)

    monkeypatch.setattr(subprocess, "Popen", Recording)
    try:
        with pytest.raises(FileNotFoundError):
            drive(
                session_command(fake.claude(), ARM, "s-1", 1.0),
                cwd=str(place.clone),
                env=_env(place, config),
                message="메시지",
                stream_file=place.stream / "없는-폴더" / "01-s-1.jsonl",
                timeout=600.0,
            )
        assert len(started) == 1
        assert started[0].poll() is not None  # 가짜는 600초를 멈추려 했다
    finally:
        for process in started:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=60)


def test_0_이_아닌_종료_코드는_그대로_호출의_칸에_든다(tmp_path: Path) -> None:
    place = _round(tmp_path)
    config = tmp_path / "설정"
    fake.write_script(config, calls=[fake.call(_events_done(0.4), exit_code=3)])

    got = _launch(place, config)

    assert got.drove.exit_code == 3 and not got.drove.timed_out
    assert got.summary.results  # 결과 이벤트를 낸 뒤 3으로 끝났다
    made = call_record(CallRun(CALL_FIRST, got, has_directive=False, ends_with_question=False))
    assert made.exit_code == 3


# --- 요약 ---


def _events_done(cost: float, text: str = "끝냈다") -> list[Json]:
    return [
        fake.init_event(),
        fake.assistant_event("claude-opus-5-5", "모델의 글", tool_input={"command": "입력글"}),
        fake.result_event(cost, text, usage=fake.model_usage("claude-opus-5-5", cost=cost)),
    ]


def test_세션_비용은_결과_이벤트의_합이_아니라_마지막_값이다() -> None:
    first = summarize_call(
        _jsonl(
            {**fake.result_event(0.5, "하나", index=0), "session_id": "s"},
            {**fake.result_event(0.8, "둘", index=1), "session_id": "s"},
        )
    )
    resumed = summarize_call(
        _jsonl(
            {
                **fake.result_event(1.2, "셋", usage=fake.model_usage("claude-opus-5-5", cost=1.2)),
                "session_id": "s",
            },
            {**fake.result_event(9.0, "남의 것"), "session_id": "다른"},
        )
    )

    cost, usage = session_cost([*first.results, *resumed.results], "s")

    assert cost == 1.2
    assert [u.model for u in usage] == ["claude-opus-5-5"] and usage[0].cost_usd == 1.2


def test_빈_마지막_글을_건너뛴_결과_글과_누적_비용을_커밋한_원본에서_읽는다() -> None:
    lines = (PROBE / "서브-2.jsonl").read_text(encoding="utf-8").splitlines(keepends=True)

    summary = summarize_call(lines)

    assert [r.text for r in summary.results][-1] == ""
    assert result_text(summary.results) == "노을고래"
    assert len(summary.results) == 3
    cost, _ = session_cost(summary.results, "46b6b50e-5ebb-4ecb-afda-59fe2d6ca213")
    assert cost == pytest.approx(0.039455729999999994)
    assert summary.non_events == 0 and summary.events == len(lines)


def test_공백만_든_글도_빈_글로_건너뛴다() -> None:
    summary = summarize_call(_jsonl(fake.result_event(0.1, "앞 글"), fake.result_event(0.1, " \n")))

    assert result_text(summary.results) == "앞 글"


def test_풀지_못한_줄은_이벤트로_세지_않는다() -> None:
    lines = [
        *_jsonl(fake.init_event()),
        '{"type": "result", "잘린',
        "글 줄\n",
        "[1, 2]\n",
        '{"type": 3}\n',
        # 푸는 쪽의 재귀 한도를 넘는 중첩
        '{"type": "x", "a": ' + "[" * 100_000 + "]" * 100_000 + "}\n",
        "\n",
        *_jsonl(fake.result_event(0.2, "끝")),
    ]

    summary = summarize_call(lines)

    assert summary.events == 2
    assert summary.non_events == 5
    assert [r.text for r in summary.results] == ["끝"]


def test_init_의_도구_플러그인_MCP_와_판을_옮긴다() -> None:
    init = fake.init_event(tools=("Bash", "Read"), mcp_servers=("github",), version="2.1.302")

    summary = summarize_call(_jsonl(init, fake.init_event(tools=("뒤",))))

    assert summary.init is not None
    assert summary.init.tools == ("Bash", "Read")
    assert summary.init.plugins == fake.BUILTIN_PLUGINS
    assert summary.init.mcp_servers == ("github",)
    assert summary.init.version == "2.1.302"


# --- 세션 기록 파일 ---


def test_세션_id_로_찾은_기록_파일에서_synthetic_을_뺀_모델과_노력을_센다(tmp_path: Path) -> None:
    place = _round(tmp_path)
    config = tmp_path / "설정"
    sid = "22222222-2222-4333-8444-555555555555"
    main = [fake.transcript_line("claude-opus-5-5", "xhigh", f"m{i}") for i in range(3)]
    main.append(fake.synthetic_line())
    side = {"agent-a1": [fake.transcript_line("claude-sonnet-5-5", "high")] * 2}
    fake.write_script(config, calls=[fake.call(_events_done(0.3), main=main, subagents=side)])
    # 다른 세션의 기록은 세지 않는다.
    other = config / "projects" / "다른-폴더" / "33333333-2222-4333-8444-555555555555.jsonl"
    other.parent.mkdir(parents=True)
    other.write_text(json.dumps(fake.transcript_line("claude-haiku-5-5", "low")) + "\n", "utf-8")

    _launch(place, config, sid=sid)
    got_main, got_side = transcript_counts(config, sid)

    assert got_main == (LineCount(model="claude-opus-5-5", effort="xhigh", lines=3),)
    assert got_side == (LineCount(model="claude-sonnet-5-5", effort="high", lines=2),)


def test_글_안의_U2028_은_기록_줄을_가르지_않는다(tmp_path: Path) -> None:
    """Node 의 `JSON.stringify` 는 U+2028·U+2029 를 이스케이프하지 않는다. 기록은 `\\n` 으로만
    가른다."""
    config = tmp_path / "설정"
    sid = "44444444-2222-4333-8444-555555555555"
    path = config / "projects" / "클론" / f"{sid}.jsonl"
    path.parent.mkdir(parents=True)
    text = "앞" + chr(0x2028) + "가운데" + chr(0x2029) + "뒤" + chr(0x85) + "끝"
    line = fake.transcript_line("claude-opus-5-5", "xhigh", text)
    path.write_text(json.dumps(line, ensure_ascii=False) + "\n", "utf-8")

    got_main, _ = transcript_counts(config, sid)

    assert got_main == (LineCount(model="claude-opus-5-5", effort="xhigh", lines=1),)


def test_노력이_없는_보통_줄은_노력_없음으로_센다() -> None:
    lines = [json.dumps(fake.transcript_line("claude-haiku-5-5", None)), "깨진 줄"]

    assert count_lines(lines) == (LineCount(model="claude-haiku-5-5", effort=None, lines=1),)


def test_가짜_기록의_꼴로_센_수가_커밋한_요약의_transcript_칸과_같다() -> None:
    """`모양`의 실제 기록은 `low` 다섯, `claude-sonnet-5-5` 다섯이었다. 러너와 가짜가 같은 틀린 꼴로
    맞는 순환은 파일럿(11)이 실제 회차의 기록 수로 깬다."""
    transcript = _o(_summary("모양")["transcript"])
    [(effort, n)] = _o(transcript["effort"]).items()
    [(model, m)] = _o(transcript["model"]).items()
    assert isinstance(n, int) and isinstance(m, int)
    lines = [json.dumps(fake.transcript_line(model, effort, f"m{i}")) for i in range(n)]

    assert count_lines(lines) == (LineCount(model=model, effort=effort, lines=m),)


# --- 가짜의 꼴 ---


def _o(v: Json) -> dict[str, Json]:
    assert isinstance(v, dict), v
    return v


def _l(v: Json) -> list[Json]:
    assert isinstance(v, list), v
    return v


def _load(text: str) -> Json:
    # `json.loads`의 반환형은 Any라 `Json`으로 받아 뒤의 좁히기가 타입 검사를 지나게 한다.
    return json.loads(text)


def _summary(name: str) -> dict[str, Json]:
    return _o(_load((PROBE / f"{name}.summary.json").read_text("utf-8")))


def test_가짜_각본의_이벤트_꼴은_커밋한_프로브_결과의_꼴이다() -> None:
    shape = _summary("모양")
    budget = _summary("예산")
    result_keys = set(_l(shape["result_keys"]))
    budget_keys = set(_l(budget["result_keys"]))

    assert set(fake.result_event(0.1, "글")) <= result_keys
    made = fake.budget_result(0.1)
    assert set(made) <= budget_keys
    assert "result" not in made and "result" not in budget_keys
    real_budget = _o(_l(budget["results"])[0])
    assert (made["subtype"], made["terminal_reason"]) == (
        real_budget["subtype"],
        real_budget["terminal_reason"],
    )
    assert set(fake.init_event()) <= set(_l(shape["init_keys"]))
    [real_entry] = _o(shape["model_usage"]).values()
    [made_entry] = fake.model_usage("claude-sonnet-5-5", cost=0.1).values()
    assert set(_o(made_entry)) == set(_o(real_entry))
    plugins = _l(_o(shape["init"])["plugins"])
    assert [_o(p)["name"] for p in plugins] == list(fake.BUILTIN_PLUGINS)


def test_가짜의_한도_이벤트_꼴은_원본과_카나리아_시험의_꼴이다() -> None:
    real = [
        _o(_load(line))
        for line in (PROBE / "서브-2.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    [warning] = [e for e in real if e["type"] == "rate_limit_event"]
    made = fake.rate_limit_event()
    real_info = _o(warning["rate_limit_info"])
    made_info = _o(made["rate_limit_info"])

    assert set(made) <= set(warning) | {"session_id"}
    assert set(made_info) <= set(real_info)
    assert set(_o(made_info["unifiedWindows"])) == set(_o(real_info["unifiedWindows"]))
    canary = (ROOT / "tests" / "tools" / "test_canary.py").read_text(encoding="utf-8")
    assert '"status": "rejected"' in canary and '"api_error": "usage_limit_reached"' in canary
    assert fake.limit_result()["api_error"] == "usage_limit_reached"
    assert _o(fake.rate_limit_event("rejected")["rate_limit_info"])["status"] == "rejected"


def test_가짜는_세션_밖의_부름을_각본대로_답한다(tmp_path: Path) -> None:
    config = tmp_path / "설정"
    fake.write_script(config, version="2.1.302 (Claude Code)")
    env = {**os.environ, "CLAUDE_CONFIG_DIR": str(config)}

    def run(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [*fake.claude(), *args],
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
            check=False,
        )

    status = run("auth", "status", "--json")
    assert status.returncode == 0
    assert json.loads(status.stdout) == {
        "loggedIn": True,
        "email": "njh6803@example.com",
        "configDirectory": str(config),
    }
    assert claude_version(fake.claude(), env=env, cwd=tmp_path) == "2.1.302 (Claude Code)"

    fake.write_script(config, logged_in=False)
    out = run("auth", "status", "--json")
    assert out.returncode == 1
    assert "email" not in json.loads(out.stdout)


def test_판의_꼴이_아닌_답은_판을_비운다(tmp_path: Path) -> None:
    config = tmp_path / "설정"
    fake.write_script(config, version="모르는 답")
    env = {**os.environ, "CLAUDE_CONFIG_DIR": str(config)}

    assert claude_version(fake.claude(), env=env, cwd=tmp_path) is None
    assert claude_version([str(tmp_path / "없음")], env=env, cwd=tmp_path) is None


def test_가짜는_세션_id_마다_다른_각본을_고르고_커밋을_남긴다(tmp_path: Path) -> None:
    place = _round(tmp_path)
    _git_init(place.clone)
    config = tmp_path / "설정"
    sid = "44444444-2222-4333-8444-555555555555"
    fake.write_script(
        config,
        calls=[fake.call([fake.result_event(0.1, "차례의 각본")])],
        sessions={
            sid: [
                fake.call(
                    [fake.result_event(0.2, "세션의 각본")],
                    git=[
                        ["switch", "-c", "feature/03-thing"],
                        ["commit", "--allow-empty", "-m", "x"],
                    ],
                )
            ]
        },
    )

    got = _launch(place, config, sid=sid)

    assert result_text(got.summary.results) == "세션의 각본"
    branches = local_branches(place.clone, _head(place.clone, "main"))
    assert set(branches) == {"feature/03-thing"} and branches["feature/03-thing"][1] == 1


# --- 결과 커밋 ---


def _git(cwd: Path, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if k not in REPO_LOCATION_VARS}
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    ).stdout


def _git_init(repo: Path) -> None:
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "B")


def _head(repo: Path, ref: str = "HEAD") -> str:
    return _git(repo, "rev-parse", ref).strip()


def test_결과_커밋의_세_규칙() -> None:
    tip = "1" * 40
    other = "2" * 40

    assert pick_result_commit({"feature/x": (tip, 0), "fix/y": (other, 2)}, "feature/x") == (
        pick_result_commit({"feature/x": (tip, 0)}, "feature/x")
    )
    picked = pick_result_commit({"feature/x": (tip, 0), "fix/y": (other, 2)}, "feature/x")
    assert (picked.commit, picked.rule, picked.commits_after_base) == (tip, RULE_BRANCH, 0)
    only = pick_result_commit({"fix/y": (other, 2), "옛": (tip, 0)}, "feature/x")
    assert (only.commit, only.rule, only.commits_after_base) == (other, RULE_ONLY, 2)
    two = pick_result_commit({"a": (tip, 1), "b": (other, 3)}, "feature/x")
    assert (two.commit, two.rule, two.commits_after_base) == (None, RULE_NONE, None)
    none = pick_result_commit({"a": (tip, 0)}, "feature/x")
    assert (none.commit, none.rule) == (None, RULE_NONE)


def test_클론의_로컬_브랜치는_main_을_빼고_B_뒤_커밋_수를_센다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "클론"
    repo.mkdir()
    _git_init(repo)
    base = _head(repo)
    _git(repo, "switch", "-q", "-c", "feature/03-thing")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "1")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "2")
    tip = _head(repo)
    _git(repo, "branch", "멈춘", base)
    _git(repo, "switch", "-q", "main")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "main 위")
    # pre-commit 아래의 git 이 내보내는 값이 남아도 클론을 본다.
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "남의.git"))
    monkeypatch.setenv("GIT_INDEX_FILE", str(tmp_path / "남의.index"))

    branches = local_branches(repo, base)

    assert branches == {"feature/03-thing": (tip, 2), "멈춘": (base, 0)}
    picked = pick_result_commit(branches, "feature/03-thing")
    outcome = outcome_of(picked)
    assert (outcome.commit, outcome.rule, outcome.commits_after_base) == (tip, RULE_BRANCH, 2)
    assert outcome.gates is None and outcome.hidden is None and outcome.setup_failure is None


# --- 회차 기록 ---


def test_회차_기록은_정해진_칸만_남기고_모델의_글과_도구_입력이_없다(tmp_path: Path) -> None:
    place = _round(tmp_path)
    config = tmp_path / "설정"
    sid = "55555555-2222-4333-8444-555555555555"
    events = [
        fake.init_event(tools=("Bash", "Read", "Write")),
        fake.assistant_event("claude-opus-5-5", "비밀글123", tool_input={"command": "입력글456"}),
        fake.result_event(0.5, "중간글", index=0, num_turns=3),
        fake.result_event(
            0.9,
            "결과글789",
            index=1,
            num_turns=1,
            usage=fake.model_usage("claude-opus-5-5", cost=0.9),
        ),
    ]
    main = [fake.transcript_line("claude-opus-5-5", "xhigh")]
    fake.write_script(config, calls=[fake.call(events, main=main)])
    env = _env(place, config)
    got = _launch(place, config, sid=sid)

    record = round_record(
        place,
        TASK,
        condition_version=1,
        claude_version=claude_version(fake.claude(), env=env, cwd=place.clone),
        account="njh6803",
        env=env,
        runs=[CallRun(CALL_FIRST, got, has_directive=False, ends_with_question=False)],
        config_dir=config,
        handoffs=0,
        interventions=0,
        asked_at_end=False,
        end=End(kind=END_DONE, reason=None, resets_at=None),
        outcome=outcome_of(pick_result_commit({"feature/03-thing": ("d" * 40, 2)}, TASK.branch)),
        wall_clock_from=100.0,
        now=163.456,
        elsewhere=NOTHING,
    )
    records = tmp_path / "records"
    records.mkdir()
    path = write_record(records, record)

    text = path.read_text(encoding="utf-8")
    for leaked in ("비밀글123", "입력글456", "결과글789", "중간글", str(tmp_path), "ghp_"):
        assert leaked not in text
    back = read_record(path)
    assert back.round_dir_name == place.name and back.arm == "A" and back.round_no == 1
    assert back.claude_version == "2.1.302 (Claude Code)"
    assert back.account == "njh6803"
    assert back.env_names == tuple(sorted(env))
    assert back.init_tools == ("Bash", "Read", "Write")
    [session] = back.sessions
    assert session.session_id == sid
    assert session.cost_usd == 0.9
    assert [u.model for u in session.model_usage] == ["claude-opus-5-5"]
    assert session.main_lines == (LineCount(model="claude-opus-5-5", effort="xhigh", lines=1),)
    [made] = session.calls
    assert made.kind == CALL_FIRST and made.budget_usd == 12.34 and made.exit_code == 0
    assert [(r.index, r.subtype, r.terminal_reason, r.num_turns) for r in made.results] == [
        (0, "success", "completed", 3),
        (1, "success", "completed", 1),
    ]
    assert back.spend.claude_code_usd == 0.9
    assert back.spend.wall_seconds == 63.46
    assert back.outcome.commit == "d" * 40 and back.outcome.rule == RULE_BRANCH


def test_꼴_밖의_subtype_과_끝난_까닭은_기록이_받는_꼴로_적는다(tmp_path: Path) -> None:
    place = _round(tmp_path)
    config = tmp_path / "설정"
    odd = {**fake.result_event(0.1, "글", terminal_reason="Weird-Reason"), "subtype": "Odd Kind"}
    fake.write_script(config, calls=[fake.call([odd])])
    got = _launch(place, config)

    record = round_record(
        place,
        TASK,
        condition_version=1,
        claude_version=None,
        account="njh6803",
        env={},
        runs=[CallRun(CALL_FIRST, got, has_directive=False, ends_with_question=False)],
        config_dir=config,
        handoffs=0,
        interventions=0,
        asked_at_end=False,
        end=End(kind="측정 아님", reason="호출", resets_at=None),
        outcome=outcome_of(pick_result_commit({}, TASK.branch)),
        wall_clock_from=0.0,
        now=1.0,
        elsewhere=NOTHING,
    )
    records = tmp_path / "records"
    records.mkdir()
    back = read_record(write_record(records, record))

    [result] = back.sessions[0].calls[0].results
    assert (result.subtype, result.terminal_reason) == ("unknown", None)


def test_다른_과제의_회차_폴더로는_기록을_짓지_않는다(tmp_path: Path) -> None:
    place = create_round_dir(tmp_path / "뿌리", "other-01", "A", 1, token="z")

    with pytest.raises(ValueError, match="회차 폴더가 아니다"):
        round_record(
            place,
            TASK,
            condition_version=1,
            claude_version=None,
            account="njh6803",
            env={},
            runs=[],
            config_dir=tmp_path,
            handoffs=0,
            interventions=0,
            asked_at_end=False,
            end=End(kind="측정 아님", reason="호출", resets_at=None),
            outcome=outcome_of(pick_result_commit({}, TASK.branch)),
            wall_clock_from=0.0,
            now=1.0,
            elsewhere=NOTHING,
        )
