"""CLI 표면. 모델도 도구도 쓰지 않는 픽스처 에이전트로 main() 을 불러 표면을 본다.

표준 출력, 표준 에러, 종료 코드, 트레이스 파일을 본다.
픽스처 에이전트는 tmp_path 아래 plugins/ 에 쓰고 저장소의 plugins/ 에 두지 않는다.
llm 마커가 붙은 마지막 테스트만 실제 CLI 프로세스를 띄운다. 바깥 이음매다.
"""

import getpass
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from agent_os.adapters.jsonl import JsonlTrace
from agent_os.channel.cli.main import EXIT_PAUSED
from agent_os.core.ports import Trace, UnknownEvent
from agent_os.main import main
from agent_os.sdk import ApprovalGranted, LlmCalled, RunId, RunPaused, RunStarted, ToolCalled

REPO_ROOT = Path(__file__).resolve().parents[1]
MCP_FIXTURE_SERVER = REPO_ROOT / "tests" / "adapters" / "mcp_fixture_server.py"

MANIFEST = (
    'schema_version = "1"\nkind = "agent"\nname = "{name}"\nversion = "0.1.0"\n'
    'entrypoint = "agent:Agent"\n'
)

GATED_MANIFEST = MANIFEST.format(name="gated") + 'mcp = ["fixture"]\nrequires_approval = ["add"]\n'

# 진짜 stdio 서버(tests/adapters/mcp_fixture_server.py). 경로는 TOML 기본 문자열이라 슬래시로 쓴다.
MCP_MANIFEST = (
    'schema_version = "1"\nkind = "mcp"\nname = "{name}"\nversion = "0.1.0"\n'
    f'[server]\ncommand = "{Path(sys.executable).as_posix()}"\n'
    f'args = ["{MCP_FIXTURE_SERVER.as_posix()}"]\n'
)

ECHO_SRC = """
from collections.abc import AsyncIterator

from agent_os.sdk import AgentContext, Event, RunFinished


class Agent:
    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=f"echo:{request}")
"""

BOOM_SRC = """
from collections.abc import AsyncIterator

from agent_os.sdk import AgentContext, Event, RunFinished


class Agent:
    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        raise RuntimeError("kaboom")
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output="unreachable")
"""


GATED_SRC = """
from collections.abc import AsyncIterator

from agent_os.sdk import AgentContext, Event, RunFinished


class Agent:
    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        total = await ctx.tool("add", a=2, b=3)
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=total)
"""


def _write_plugin(root: Path, name: str, source: str, manifest: str | None = None) -> None:
    directory = root / "plugins" / "agents" / name
    directory.mkdir(parents=True)
    (directory / "plugin.toml").write_text(
        MANIFEST.format(name=name) if manifest is None else manifest, encoding="utf-8"
    )
    (directory / "agent.py").write_text(source, encoding="utf-8")


def _write_mcp_plugin(root: Path, name: str) -> None:
    directory = root / "plugins" / "mcp" / name
    directory.mkdir(parents=True)
    (directory / "plugin.toml").write_text(MCP_MANIFEST.format(name=name), encoding="utf-8")


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    _write_plugin(tmp_path, "echo", ECHO_SRC)
    _write_plugin(tmp_path, "boom", BOOM_SRC)
    return tmp_path


def _trace_files(directory: Path) -> list[Path]:
    return sorted(directory.iterdir()) if directory.is_dir() else []


def _read(trace_file: Path) -> Trace:
    """CLI 가 남긴 파일을 같은 어댑터로 읽는다. 파일이 있는데 None 이면 어댑터의 결함이다."""
    trace = JsonlTrace(trace_file.parent).read(RunId(trace_file.stem))
    assert trace is not None
    return trace


def test_표준_출력에는_출력_문자열만_나오고_성공하면_표준_에러는_비어_있다(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["run", "echo", "hi", "--traces", "t"])

    out, err = capsys.readouterr()
    assert code == 0
    assert out == "echo:hi\n"
    assert err == ""


def test_진행_표시를_켜면_이벤트가_한_줄에_하나씩_트레이스와_같은_직렬화로_표준_에러에_나온다(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    main(["run", "echo", "hi", "--traces", "t", "--verbose"])

    out, err = capsys.readouterr()
    lines = err.splitlines()
    assert out == "echo:hi\n"
    assert [json.loads(line)["type"] for line in lines] == ["run_started", "run_finished"]
    (trace_file,) = _trace_files(workspace / "t")
    assert trace_file.read_text(encoding="utf-8").splitlines()[1:] == lines


def test_실패는_진행_표시를_끈_채로도_원인이_표준_에러에_남고_종료_코드가_1이다(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["run", "boom", "hi", "--traces", "t"])

    out, err = capsys.readouterr()
    assert code == 1
    assert out == ""
    assert "kaboom" in err
    (trace_file,) = _trace_files(workspace / "t")
    assert [e.type for e in _read(trace_file).events if not isinstance(e, UnknownEvent)] == [
        "run_started",
        "run_failed",
    ]


def test_주체가_OS_사용자_이름으로_채워진다(workspace: Path) -> None:
    main(["run", "echo", "hi", "--traces", "t"])

    (trace_file,) = _trace_files(workspace / "t")
    started = _read(trace_file).events[0]
    assert isinstance(started, RunStarted)
    assert started.principal == getpass.getuser()


def test_지정한_트레이스_디렉터리에_실행_식별자_이름의_파일이_생긴다(workspace: Path) -> None:
    main(["run", "echo", "hi", "--traces", "t"])

    (trace_file,) = _trace_files(workspace / "t")
    assert trace_file.suffix == ".jsonl"
    assert _read(trace_file).run_id == trace_file.stem


def test_트레이스_디렉터리를_지정하지_않으면_작업_디렉터리의_traces_아래에_쌓인다(
    workspace: Path,
) -> None:
    main(["run", "echo", "hi"])

    assert len(_trace_files(workspace / "traces")) == 1


@pytest.mark.parametrize(
    ("name", "manifest", "source", "clue"),
    [
        ("nope", None, None, "nope"),
        ("badtoml", "kind = = agent\n", ECHO_SRC, "badtoml"),
        (
            "oldver",
            MANIFEST.format(name="oldver").replace('"1"', '"9"'),
            ECHO_SRC,
            "schema_version",
        ),
        ("broken", None, "def (\n", "broken"),
        ("nomcp", MANIFEST.format(name="nomcp") + 'mcp = ["ghost"]\n', ECHO_SRC, "ghost"),
    ],
    ids=[
        "없는 에이전트",
        "매니페스트 파싱 실패",
        "모르는 형식 버전",
        "진입점 import 실패",
        "없는 mcp 이름",
    ],
)
def test_실행_전_오류는_무엇이_잘못됐는지_적고_종료_코드_1이며_트레이스를_남기지_않는다(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    name: str,
    manifest: str | None,
    source: str | None,
    clue: str,
) -> None:
    monkeypatch.chdir(tmp_path)
    if source is not None:
        _write_plugin(tmp_path, name, source, manifest)

    code = main(["run", name, "hi", "--traces", "t"])

    out, err = capsys.readouterr()
    assert code == 1
    assert out == ""
    assert clue in err
    assert _trace_files(tmp_path / "t") == []


def test_빈_모델_지정은_실행_전에_진단을_적고_종료_코드_1이다(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["run", "echo", "hi", "--traces", "t", "--model", ""])

    out, err = capsys.readouterr()
    assert code == 1
    assert out == ""
    assert "모델 이름" in err
    assert _trace_files(workspace / "t") == []


@pytest.mark.llm
def test_calc_에이전트가_실제_모델로_답하고_트레이스에_모델_호출이_남는다(tmp_path: Path) -> None:
    """바깥 이음매. 실제 CLI 프로세스와 실제 Anthropic 호출. 트레이스는 tmp_path 에 남긴다."""
    assert "ANTHROPIC_API_KEY" in os.environ, "ANTHROPIC_API_KEY 가 없다. .env 를 확인한다"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_os.main",
            "run",
            "calc",
            "2 더하기 2는?",
            "--traces",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "4" in result.stdout
    (trace_file,) = _trace_files(tmp_path)
    events = [e for e in _read(trace_file).events if not isinstance(e, UnknownEvent)]
    types = [e.type for e in events]
    assert "llm_called" in types
    assert "tool_called" in types
    assert types[-1] == "run_finished"
    # 재개의 입력이 되는 필드가 관찰이 아니라 실제 실행에서 차 있는지(ADR 0009).
    tool_calls = [e for e in events if isinstance(e, ToolCalled)]
    assert any(e.tool_calls for e in events if isinstance(e, LlmCalled))
    assert any(e.args for e in tool_calls)
    assert any(e.content for e in tool_calls)


def test_승인_대상에서_멈추면_실행_식별자와_승인_요청이_표준_출력에_찍히고_전용_종료_코드다(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """모델은 안 쓰고 도구는 진짜 stdio 서버다. 게이트가 도구 앞에서 멈추므로 도구는 안 불린다."""
    _write_mcp_plugin(workspace, "fixture")
    _write_plugin(workspace, "gated", GATED_SRC, GATED_MANIFEST)

    code = main(["run", "gated", "hi", "--traces", "t"])

    out, err = capsys.readouterr()
    (trace_file,) = _trace_files(workspace / "t")
    assert code == EXIT_PAUSED
    assert code not in (0, 1)
    assert trace_file.stem in out
    assert "add" in out
    assert '"a": 2' in out
    assert '"b": 3' in out
    assert f"agent-os resume {trace_file.stem} --approve" in out
    assert err == ""
    events = [e for e in _read(trace_file).events if not isinstance(e, UnknownEvent)]
    assert [e.type for e in events] == ["run_started", "run_paused"]
    assert isinstance(events[-1], RunPaused)
    assert events[-1].args == {"a": 2, "b": 3}


def test_승인하고_재개하면_멈췄던_도구가_실제로_불리고_실행이_끝난다(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """멈출 때와 재개할 때가 다른 호출이다. 프로세스 경계를 증명하는 것은 티켓 06 이다."""
    _write_mcp_plugin(workspace, "fixture")
    _write_plugin(workspace, "gated", GATED_SRC, GATED_MANIFEST)
    paused = main(["run", "gated", "hi", "--traces", "t"])
    (trace_file,) = _trace_files(workspace / "t")
    capsys.readouterr()

    code = main(["resume", trace_file.stem, "--approve", "--traces", "t"])

    out, err = capsys.readouterr()
    assert paused == EXIT_PAUSED
    assert code == 0
    assert out == "5\n"
    assert err == ""
    events = [e for e in _read(trace_file).events if not isinstance(e, UnknownEvent)]
    assert [e.type for e in events] == [
        "run_started",
        "run_paused",
        "approval_granted",
        "run_resumed",
        "tool_called",
        "run_finished",
    ]


def test_승인자가_OS_사용자_이름으로_채워진다(workspace: Path) -> None:
    """승인자는 필수다. 나중에 누가 허락했는지 물을 때 답이 있어야 한다."""
    _write_mcp_plugin(workspace, "fixture")
    _write_plugin(workspace, "gated", GATED_SRC, GATED_MANIFEST)
    main(["run", "gated", "hi", "--traces", "t"])
    (trace_file,) = _trace_files(workspace / "t")

    main(["resume", trace_file.stem, "--approve", "--traces", "t"])

    granted = [e for e in _read(trace_file).events if isinstance(e, ApprovalGranted)]
    assert [e.approver for e in granted] == [getpass.getuser()]


def test_재개할_수_없는_실행은_진단을_적고_종료_코드_1이며_트레이스를_남기지_않는다(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["resume", "없는-실행", "--approve", "--traces", "t"])

    out, err = capsys.readouterr()
    assert code == 1
    assert out == ""
    assert "없는-실행" in err
    assert _trace_files(workspace / "t") == []


def _guidance(out: str) -> list[str]:
    """일시정지 출력이 안내한 재개 명령을 셸이 읽듯 인자로 쪼갠다."""
    line = next(line for line in out.splitlines() if line.startswith("승인: agent-os "))
    return shlex.split(line.removeprefix("승인: agent-os "))


def test_안내된_재개_명령을_그대로_실행하면_재개된다(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """안내가 작동하지 않으면 안내가 아니다. 공백이 있는 트레이스 경로까지 그대로 복사된다."""
    _write_mcp_plugin(workspace, "fixture")
    _write_plugin(workspace, "gated", GATED_SRC, GATED_MANIFEST)
    paused = main(["run", "gated", "hi", "--traces", "out dir"])
    argv = _guidance(capsys.readouterr().out)

    code = main(argv)

    assert paused == EXIT_PAUSED
    assert code == 0
    assert capsys.readouterr().out == "5\n"


def test_기본_트레이스_디렉터리면_안내_명령에_경로가_붙지_않는다(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_mcp_plugin(workspace, "fixture")
    _write_plugin(workspace, "gated", GATED_SRC, GATED_MANIFEST)

    main(["run", "gated", "hi"])

    argv = _guidance(capsys.readouterr().out)
    assert "--traces" not in argv
