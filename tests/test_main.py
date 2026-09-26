"""CLI 표면. 모델도 도구도 쓰지 않는 픽스처 에이전트로 main() 을 불러 표면을 본다.

표준 출력, 표준 에러, 종료 코드, 트레이스 파일을 본다.
픽스처 에이전트는 tmp_path 아래 plugins/ 에 쓰고 저장소의 plugins/ 에 두지 않는다.
llm 마커가 붙은 셋만 실제 프로세스를 띄운다 — CLI 둘과 serve 하나. 바깥 이음매다.
"""

import getpass
import json
import os
import re
import secrets
import shlex
import subprocess
import sys
import time
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from pathlib import Path

import pytest
import uvicorn
from fastapi import FastAPI
from fastapi.sse import KEEPALIVE_COMMENT
from httpx import ASGITransport, AsyncClient, Client, Timeout
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel

from agent_os import main as main_module
from agent_os.adapters.anthropic import DEFAULT_MODEL, MODEL_ENV
from agent_os.adapters.jsonl import JsonlTrace
from agent_os.channel.cli.main import DEFAULT_HOST, EXIT_PAUSED
from agent_os.core.ports import ChatModel, Trace, UnknownEvent
from agent_os.main import ADMIN_TOKEN_ENV, CHANNEL_TOKEN_ENV, main
from agent_os.sdk import (
    ApprovalDenied,
    ApprovalGranted,
    Json,
    LlmCalled,
    RunId,
    RunPaused,
    RunStarted,
    ToolCalled,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MCP_FIXTURE_SERVER = REPO_ROOT / "tests" / "adapters" / "mcp_fixture_server.py"

MANIFEST = (
    'schema_version = "1"\nkind = "agent"\nname = "{name}"\nversion = "0.1.0"\n'
    'entrypoint = "agent:Agent"\n'
)


def _gated_manifest(name: str) -> str:
    """fixture 서버를 쓰고 그 서버의 add 를 승인 대상으로 두는 에이전트 매니페스트."""
    return MANIFEST.format(name=name) + 'mcp = ["fixture"]\nrequires_approval = ["add"]\n'


GATED_MANIFEST = _gated_manifest("gated")

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


EXCUSING_MANIFEST = _gated_manifest("excusing")

# 거부당하면 사용자에게 왜 못 했는지 말하고 정상적으로 끝맺는 에이전트. gated 와 도구도 정책도 같다.
EXCUSING_SRC = """
from collections.abc import AsyncIterator

from agent_os.sdk import AgentContext, Event, RunFinished, ToolError


class Agent:
    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        try:
            total = await ctx.tool("add", a=2, b=3)
        except ToolError as error:
            total = f"못 했습니다: {error}"
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=total)
"""


GATEDCALC_MANIFEST = _gated_manifest("gatedcalc")

# 도구를 고르는 것이 게이트도 에이전트도 아니라 실제 모델인 유일한 픽스처. 프롬프트가 도구를
# 강제하는 것은 모델이 2+3 을 암산해 버리면 승인 대상에 닿지 않아 잴 것이 없어지기 때문이다.
GATEDCALC_SRC = """
from collections.abc import AsyncIterator

from agent_os.sdk import AgentContext, Event, RunFinished

PROMPT = "계산 요청이다. 반드시 add 도구로 계산한다. 최종 답만 짧게 답한다. 요청: {request}"


class Agent:
    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        output = await ctx.llm(PROMPT.format(request=request))
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=output)
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


def _cli(argv: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    """실제 CLI 프로세스 하나를 띄우고 끝날 때까지 기다린다. 돌아오면 그 프로세스는 죽어 있다."""
    return _python(["-m", "agent_os.main", *argv], cwd=cwd)


def _python(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    """이 환경의 파이썬 프로세스 하나를 띄우고 끝날 때까지 기다린다."""
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=_env(),
        check=False,
    )


def _env() -> dict[str, str]:
    """이 환경의 파이썬 자식 프로세스가 받는 환경. 한국어 출력이 cp949 로 깨지지 않게 UTF-8 을
    강제한다(CLAUDE.md 환경 함정)."""
    return {**os.environ, "PYTHONUTF8": "1"}


def test_모듈로_실행하면_패키지_안의_http_층이_표준_라이브러리를_가리지_않는다(
    tmp_path: Path,
) -> None:
    """`-m` 은 작업 디렉터리를 `sys.path` 첫머리에 둔다. `agent_os.http` 에는 절대 import 로만
    닿는다. 콘솔 스크립트(`agent-os`)도 같은 import 라 이 길과 같다."""
    result = _cli(["--help"], cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    assert "agent-os" in result.stdout


def test_패키지_안의_파일을_스크립트로_실행하면_이유와_처방을_말하고_끝난다(tmp_path: Path) -> None:
    """스크립트 실행은 그 파일의 디렉터리를 `sys.path` 첫머리에 두어 `agent_os/http/` 가 표준
    라이브러리 `http` 자리에 들어온다. 그대로면 `No module named 'http.client'` 로 죽고 원인이
    보이지 않는다. 층이 그것을 알아채고 막는다(ADR 0016 의 2026-09-25 이력)."""
    result = _python([str(REPO_ROOT / "src" / "agent_os" / "main.py"), "--help"], cwd=tmp_path)

    assert result.returncode != 0
    assert "표준 라이브러리" in result.stderr
    assert "python -m agent_os.main" in result.stderr


@pytest.mark.llm
def test_calc_에이전트가_실제_모델로_답하고_트레이스에_모델_호출이_남는다(tmp_path: Path) -> None:
    """바깥 이음매. 실제 CLI 프로세스와 실제 Anthropic 호출. 트레이스는 tmp_path 에 남긴다."""
    assert "ANTHROPIC_API_KEY" in os.environ, "ANTHROPIC_API_KEY 가 없다. .env 를 확인한다"

    result = _cli(["run", "calc", "2 더하기 2는?", "--traces", str(tmp_path)], cwd=REPO_ROOT)

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
    assert f"agent-os resume {trace_file.stem} --traces t --approve" in out
    assert f"agent-os resume {trace_file.stem} --traces t --deny --reason" in out
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


def _guidance(out: str, label: str = "승인") -> list[str]:
    """일시정지 출력이 안내한 재개 명령을 셸이 읽듯 인자로 쪼갠다. 안내 줄은 승인과 거부 둘이다."""
    prefix = f"{label}: agent-os "
    line = next(line for line in out.splitlines() if line.startswith(prefix))
    return shlex.split(line.removeprefix(prefix))


def test_안내된_재개_명령을_그대로_실행하면_재개된다(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """안내가 작동하지 않으면 안내가 아니다.

    경로에 공백과 `$` 를 함께 두는 것은, 셸이 한 인자로 읽으면서 확장도 하지 않아야 왕복이
    성립하기 때문이다. 큰따옴표로 감싸기만 하면 `$out` 이 빈 문자열로 확장돼 다른 디렉터리를 읽는다.
    """
    _write_mcp_plugin(workspace, "fixture")
    _write_plugin(workspace, "gated", GATED_SRC, GATED_MANIFEST)
    paused = main(["run", "gated", "hi", "--traces", "$out dir"])
    argv = _guidance(capsys.readouterr().out)

    code = main(argv)

    assert paused == EXIT_PAUSED
    assert "$out dir" in argv
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


def test_거부하면_도구가_불리지_않고_에이전트가_사유를_담아_정상으로_끝난다(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """거부는 에러가 아니라 답이다. 실행은 성공으로 끝나고 거부가 승인자와 사유와 함께 남는다."""
    _write_mcp_plugin(workspace, "fixture")
    _write_plugin(workspace, "excusing", EXCUSING_SRC, EXCUSING_MANIFEST)
    paused = main(["run", "excusing", "hi", "--traces", "t"])
    (trace_file,) = _trace_files(workspace / "t")
    capsys.readouterr()

    argv = ["resume", trace_file.stem, "--deny", "--reason", "지금은 안 된다", "--traces", "t"]
    code = main(argv)

    out, err = capsys.readouterr()
    assert paused == EXIT_PAUSED
    assert code == 0
    assert out.startswith("못 했습니다")
    assert "지금은 안 된다" in out
    assert "5" not in out  # 실제 도구가 불렸다면 2+3 의 답이 나온다
    assert err == ""
    events = [e for e in _read(trace_file).events if not isinstance(e, UnknownEvent)]
    assert [e.type for e in events] == [
        "run_started",
        "run_paused",
        "approval_denied",
        "run_resumed",
        "tool_called",
        "run_finished",
    ]
    assert isinstance(events[2], ApprovalDenied)
    assert events[2].approver == getpass.getuser()
    assert events[2].reason == "지금은 안 된다"
    assert isinstance(events[4], ToolCalled)
    assert events[4].ok is False


def test_멈추면_거부_명령도_함께_안내된다(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_mcp_plugin(workspace, "fixture")
    _write_plugin(workspace, "gated", GATED_SRC, GATED_MANIFEST)

    main(["run", "gated", "hi", "--traces", "t"])

    argv = _guidance(capsys.readouterr().out, "거부")
    assert argv[:2] == ["resume", _trace_files(workspace / "t")[0].stem]
    assert "--deny" in argv
    assert "--reason" in argv


def test_안내된_거부_명령은_사유를_이어_적어야_성립하고_그대로_치면_진단이다(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """자리표시자를 두면 그대로 친 것이 진짜 사유로 남는다. 사유 없는 거부는 안내로도 못 만든다."""
    _write_mcp_plugin(workspace, "fixture")
    _write_plugin(workspace, "excusing", EXCUSING_SRC, EXCUSING_MANIFEST)
    paused = main(["run", "excusing", "hi", "--traces", "$out dir"])
    argv = _guidance(capsys.readouterr().out, "거부")

    with pytest.raises(SystemExit) as verbatim:
        main(argv)
    code = main([*argv, "지금은 안 된다"])

    assert paused == EXIT_PAUSED
    assert "$out dir" in argv
    assert argv[-1] == "--reason"
    assert verbatim.value.code == 2
    assert code == 0
    assert capsys.readouterr().out.startswith("못 했습니다")
    (trace_file,) = _trace_files(workspace / "$out dir")
    denied = [e for e in _read(trace_file).events if isinstance(e, ApprovalDenied)]
    assert [e.reason for e in denied] == ["지금은 안 된다"]


def test_없는_실행_식별자는_거부로도_진단을_적고_트레이스를_남기지_않는다(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["resume", "없는-실행", "--deny", "--reason", "x", "--traces", "t"])

    out, err = capsys.readouterr()
    assert code == 1
    assert out == ""
    assert "없는-실행" in err
    assert _trace_files(workspace / "t") == []


@pytest.mark.llm
def test_멈춘_실행은_그_프로세스가_끝난_뒤_다른_프로세스가_재개해_끝까지_간다(
    tmp_path: Path,
) -> None:
    """이 기능의 존재 이유. 가짜 포트로 증명할 수 없는 주장 하나를 실물로 잰다.

    일시정지는 프로세스보다 오래 산다. 첫 프로세스는 승인 대상 앞에서 끝나고, 재개는 그 프로세스가
    죽은 뒤에 시작한다 — `subprocess.run` 이 종료를 기다리므로 둘째가 뜰 때 첫째는 이미 없다.
    프로세스 안에서 `await` 로 기다리는 설계를 버린 이유가 여기 있다(ADR 0009).

    실제 모델과 실제 stdio 서버를 프로세스 둘에서 쓴다. 둘은 같은 plugins 디렉터리와 같은 트레이스를
    읽고, 재개 명령은 일시정지가 안내한 줄 그대로다. 안내가 프로세스 경계 너머에서도 작동한다.
    """
    assert "ANTHROPIC_API_KEY" in os.environ, "ANTHROPIC_API_KEY 가 없다. .env 를 확인한다"
    _write_mcp_plugin(tmp_path, "fixture")
    _write_plugin(tmp_path, "gatedcalc", GATEDCALC_SRC, GATEDCALC_MANIFEST)

    paused = _cli(["run", "gatedcalc", "2 더하기 3은?", "--traces", "t"], cwd=tmp_path)
    # 여기서 먼저 단언한다. 멈추지 못한 첫 프로세스에서 안내 줄을 찾으면 그 진단이 표준 에러가
    # 아니라 `_guidance` 의 StopIteration 이 되어, 가장 흔한 실패 모드의 원인을 못 보게 된다.
    assert paused.returncode == EXIT_PAUSED, paused.stderr
    resumed = _cli(_guidance(paused.stdout), cwd=tmp_path)

    assert "add" in paused.stdout
    assert resumed.returncode == 0, resumed.stderr
    assert "5" in resumed.stdout
    (trace_file,) = _trace_files(tmp_path / "t")  # 재개가 끼어도 실행 하나에 파일 하나다
    events = [e for e in _read(trace_file).events if not isinstance(e, UnknownEvent)]
    types = [e.type for e in events]
    boundaries = ("run_paused", "approval_granted", "run_resumed")
    assert types[0] == "run_started"
    assert types.count("run_started") == 1  # 재개는 새 실행이 아니라 같은 실행이다(ADR 0009)
    assert [t for t in types if t in boundaries] == list(boundaries)
    assert types[-1] == "run_finished"
    # 승인받은 그 호출이 둘째 프로세스에서 실제로 일어났다. 첫째는 도구를 부르지 않고 끝났다.
    assert [(e.tool, e.ok) for e in events if isinstance(e, ToolCalled)] == [("add", True)]
    assert types.index("tool_called") > types.index("run_resumed")


@pytest.fixture
def uvicorn_calls(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, object]]:
    """uvicorn 이 무엇을 받았는지 기록한다. 포트는 열리지 않는다.

    구성 오류는 서버가 서기 전에 끝나므로 그때 이 목록은 비어 있어야 한다. 검사 순서가 뒤집히면
    운영자는 진단 대신 401 을 보게 되는데, 그것이 ADR 0011 이 막으려던 바로 그 실패다.

    uvicorn 이 실제로 포트를 여는 것은 기본 스위트가 증명하지 않고 `-m llm` 의 실제 serve 테스트가
    잰다. 여기서 재는 것은 그 앞까지다 — 판정이 막았나 지나갔나, 지나갔다면 무엇을 들려 보냈나.
    """
    calls: list[dict[str, object]] = []

    def _record(app: object, **kwargs: object) -> None:
        calls.append({"app": app, **kwargs})

    monkeypatch.setattr(uvicorn, "run", _record)
    return calls


ADMIN_TOKEN = "adm1n-t0ken"
CHANNEL_TOKEN = "channel-t0ken"


@pytest.fixture
def tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    """두 토큰을 모두 갖춘 구성. 구성 오류 하나를 재는 테스트는 이것을 깔고 하나만 어긋낸다 —
    다른 오류가 섞이면 그 진단이 우연히 단언을 채운다."""
    monkeypatch.setenv(ADMIN_TOKEN_ENV, ADMIN_TOKEN)
    monkeypatch.setenv(CHANNEL_TOKEN_ENV, CHANNEL_TOKEN)


@pytest.mark.parametrize("env", [ADMIN_TOKEN_ENV, CHANNEL_TOKEN_ENV], ids=["관리", "채널"])
@pytest.mark.usefixtures("tokens")
def test_토큰_환경변수가_없으면_서버가_뜨지_않고_진단과_종료_코드_1이다(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    uvicorn_calls: list[dict[str, object]],
    env: str,
) -> None:
    """채널 토큰도 관리 토큰과 같은 fail-closed 다(ADR 0015). 채널만 끄고 관리만 세우지 않는다 —
    기능이 구성에 따라 조용히 사라진다."""
    monkeypatch.delenv(env)

    code = main(["serve"])

    out, err = capsys.readouterr()
    assert code == 1
    assert out == ""
    assert env in err
    assert uvicorn_calls == []


@pytest.mark.parametrize("env", [ADMIN_TOKEN_ENV, CHANNEL_TOKEN_ENV], ids=["관리", "채널"])
@pytest.mark.parametrize("token", ["", "   "], ids=["빈 문자열", "공백만"])
@pytest.mark.usefixtures("tokens")
def test_비어_있는_토큰은_없는_것과_같이_거부한다(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    uvicorn_calls: list[dict[str, object]],
    env: str,
    token: str,
) -> None:
    """환경변수 하나의 오타가 "설정했다고 믿는 서버"를 만드는 것을 막는다.

    공백만 있는 값이 지나가면 그 서버는 아무도 모르는 토큰을 요구하며 서 있게 된다. 공백뿐인
    거부 사유를 없는 것으로 보는 `_decision` 과 같은 판단이다.
    """
    monkeypatch.setenv(env, token)

    code = main(["serve"])

    _, err = capsys.readouterr()
    assert code == 1
    assert env in err
    assert uvicorn_calls == []


def test_두_토큰이_같으면_서버가_뜨지_않고_진단이_그_값을_싣지_않는다(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    uvicorn_calls: list[dict[str, object]],
) -> None:
    """같은 값이면 분리가 무효인데 요청 시점에는 그것을 알아챌 길이 없다(스토리 42). 둘 다 있으니
    두 이름이 함께 나오는 진단은 이것 하나다."""
    monkeypatch.setenv(ADMIN_TOKEN_ENV, "같은-XYZZY-값")
    monkeypatch.setenv(CHANNEL_TOKEN_ENV, "같은-XYZZY-값")

    code = main(["serve"])

    out, err = capsys.readouterr()
    assert code == 1
    assert ADMIN_TOKEN_ENV in err
    assert CHANNEL_TOKEN_ENV in err
    assert "XYZZY" not in out + err
    assert uvicorn_calls == []


@pytest.mark.usefixtures("tokens")
def test_루프백이_아닌_호스트는_서버가_뜨지_않고_진단이_SSH_포트_포워딩을_안내한다(
    capsys: pytest.CaptureFixture[str],
    uvicorn_calls: list[dict[str, object]],
) -> None:
    """막는 데서 끝나면 운영자는 원격에서 볼 길을 잃는다. 대안이 진단 안에 있어야 한다(ADR 0011)."""
    code = main(["serve", "--host", "0.0.0.0"])

    out, err = capsys.readouterr()
    assert code == 1
    assert out == ""
    assert "0.0.0.0" in err
    assert "ssh" in err.lower()
    assert uvicorn_calls == []


@pytest.mark.usefixtures("tokens")
def test_허용되는_루프백_주소_둘이_진단에_그대로_적혀_있다(
    capsys: pytest.CaptureFixture[str],
    uvicorn_calls: list[dict[str, object]],
) -> None:
    """무엇이 허용되는지 적지 않으면 `--host localhost` 를 친 운영자가 빠져나올 길이 없다."""
    main(["serve", "--host", "localhost"])

    _, err = capsys.readouterr()
    # 기댓값을 리터럴로 적는다. LOOPBACK_HOSTS 로 도는 단언은 그 열이 비는 날 조용히 통과한다.
    assert "127.0.0.1" in err
    assert "::1" in err


def test_구성_오류_셋은_한꺼번에_나온다(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    uvicorn_calls: list[dict[str, object]],
) -> None:
    """하나씩 내면 운영자가 고치고 다시 치고 또 막힌다. 시작 자리의 판정은 한 번에 끝낸다."""
    monkeypatch.delenv(ADMIN_TOKEN_ENV, raising=False)
    monkeypatch.delenv(CHANNEL_TOKEN_ENV, raising=False)

    code = main(["serve", "--host", "0.0.0.0"])

    _, err = capsys.readouterr()
    assert code == 1
    assert ADMIN_TOKEN_ENV in err
    assert CHANNEL_TOKEN_ENV in err
    assert "0.0.0.0" in err
    assert uvicorn_calls == []


def test_진단에_토큰_값이_실리지_않는다(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    uvicorn_calls: list[dict[str, object]],
) -> None:
    """원칙 V. 구성을 되읊는 진단은 비밀을 같이 되읊는다."""
    monkeypatch.setenv(ADMIN_TOKEN_ENV, "비밀-XYZZY-42")
    monkeypatch.setenv(CHANNEL_TOKEN_ENV, "비밀-PLUGH-7")

    main(["serve", "--host", "0.0.0.0"])

    out, err = capsys.readouterr()
    assert "XYZZY" not in out + err
    assert "PLUGH" not in out + err


@pytest.mark.parametrize(
    ("argv", "expected_host"),
    [(["serve"], DEFAULT_HOST), (["serve", "--host", "::1"], "::1")],
    ids=["기본 호스트", "다른 루프백"],
)
@pytest.mark.usefixtures("workspace", "tokens")
def test_토큰과_루프백이_갖춰지면_판정을_지나_그_주소와_포트로_서버를_세운다(
    uvicorn_calls: list[dict[str, object]],
    argv: list[str],
    expected_host: str,
) -> None:
    """실패 경로만 재면 판정이 늘 막는 회귀가 초록으로 지나가고 `serve` 는 영영 뜨지 않는다.

    기본 스위트가 면제한 것은 좁다 — uvicorn 이 **포트를 실제로 여는 것**이고 그것은 `-m llm` 이
    잰다. 갖춰진 구성이 판정을 통과하는지는 면제 대상이 아니고, 기본값이 자기 정책에 막히지 않는다는
    것도 여기서 닫힌다.
    """
    code = main([*argv, "--port", "9999"])

    assert code == 0
    assert [(call["host"], call["port"]) for call in uvicorn_calls] == [(expected_host, 9999)]


@pytest.mark.usefixtures("workspace", "tokens")
async def test_통과하면_세운_앱이_두_토큰을_제자리에_받는다(
    uvicorn_calls: list[dict[str, object]],
) -> None:
    """환경변수 둘이 `create_app` 의 두 자리로 엇갈리지 않고 들어간다. 엇갈리면 운영자가 위젯에 준
    토큰이 트레이스를 읽는다. 무엇을 넘겼는지를 인자로 재지 않고 세운 앱의 답으로 잰다 — 404 는
    미들웨어를 지나 라우팅까지 갔다는 뜻이다."""
    main(["serve"])
    (call,) = uvicorn_calls
    app = call["app"]
    assert isinstance(app, FastAPI)
    admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    channel = {"Authorization": f"Bearer {CHANNEL_TOKEN}"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://serve.test"
    ) as client:
        assert (await client.get("/unrouted", headers=admin)).status_code == 404
        assert (await client.get("/unrouted", headers=channel)).status_code == 401
        assert (await client.get("/runs/unrouted", headers=channel)).status_code == 404
        assert (await client.get("/runs/unrouted", headers=admin)).status_code == 401


@pytest.fixture
def model_names(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """`serve` 가 모델 어댑터를 몇 번, 어떤 이름으로 만들었는지 기록한다. 모델은 부르지 않는다."""
    names: list[str] = []

    def _record(name: str) -> ChatModel:
        names.append(name)
        return GenericFakeChatModel(messages=iter(()))

    monkeypatch.setattr(main_module, "anthropic_chat_model", _record)
    return names


@pytest.mark.usefixtures("workspace", "tokens")
def test_serve_는_모델을_시작_때_한_번_플래그_환경변수_기본값_순으로_푼다(
    monkeypatch: pytest.MonkeyPatch,
    uvicorn_calls: list[dict[str, object]],
    model_names: list[str],
) -> None:
    """두 채널이 같은 모델로 돈다고 믿을 수 있게 CLI 와 같은 규칙이다(스토리 40). 요청마다 고르지
    않는다(스토리 23)."""
    monkeypatch.setenv(MODEL_ENV, "from-env")

    main(["serve", "--model", "from-flag"])
    main(["serve"])
    monkeypatch.delenv(MODEL_ENV)
    main(["serve"])

    assert model_names == ["from-flag", "from-env", DEFAULT_MODEL]
    assert len(uvicorn_calls) == 3


def test_빈_모델_지정도_다른_구성_오류와_한꺼번에_나온다(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    uvicorn_calls: list[dict[str, object]],
) -> None:
    """모델을 시작 때 푸는 순간 빈 지정도 시작 자리의 구성 오류다(스토리 43)."""
    monkeypatch.delenv(ADMIN_TOKEN_ENV, raising=False)
    monkeypatch.delenv(CHANNEL_TOKEN_ENV, raising=False)

    code = main(["serve", "--host", "0.0.0.0", "--model", ""])

    _, err = capsys.readouterr()
    assert code == 1
    assert "모델 이름" in err
    assert ADMIN_TOKEN_ENV in err
    assert CHANNEL_TOKEN_ENV in err
    assert "0.0.0.0" in err
    assert uvicorn_calls == []


@pytest.mark.usefixtures("workspace", "tokens")
def test_API_키는_시작_때_보지_않는다(
    monkeypatch: pytest.MonkeyPatch, uvicorn_calls: list[dict[str, object]]
) -> None:
    """CLI 와 같이 실행 안의 run_failed 로 드러난다(ADR 0014). 키가 없다고 서버가 안 서면 관리
    API 까지 함께 막힌다."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    code = main(["serve"])

    assert code == 0
    assert len(uvicorn_calls) == 1


@pytest.mark.usefixtures("workspace", "tokens")
def test_serve_가_연결이_남은_실행을_제한_없이_기다리지_않게_uvicorn_에_유예를_넘긴다(
    uvicorn_calls: list[dict[str, object]],
) -> None:
    """uvicorn 의 기본값은 연결이 전부 끝날 때까지 앱의 수명을 닫지 않는다. 멈추라는 명령이 실행
    하나가 끝나기를 제한 없이 기다리는 모양이다(ADR 0014 의 2026-09-24 이력). 그 순서는 앱의 수명을
    직접 닫는 테스트로 잴 수 없어 넘긴 값을 판정한다."""
    main(["serve"])

    (call,) = uvicorn_calls
    grace = call["timeout_graceful_shutdown"]
    assert isinstance(grace, int | float)
    assert grace > 0


def _events(stream: str) -> list[Mapping[str, Json]]:
    """SSE 본문의 이벤트들. 프레임은 빈 줄로 갈리고 값은 `data: ` 뒤의 JSON 하나다.

    keepalive 주석(`: ping`)은 이벤트가 아니라 건너뛴다. 모델이 keepalive 간격보다 오래 조용한
    날에만 끼므로, 건너뛰지 않으면 그날만 빨개진다.
    """
    blocks = [block for block in stream.split("\n\n") if block and not block.startswith(":")]
    return [json.loads(block.removeprefix("data: ")) for block in blocks]


def test_스트림을_가를_때_keepalive_주석은_이벤트로_읽지_않는다() -> None:
    """실제 serve 테스트가 기대는 자리(티켓 05). 주석은 모델이 오래 조용한 날에만 끼므로 그날을
    기다리지 않고 FastAPI 가 보내는 그 바이트로 여기서 잰다."""
    started, paused = 'data: {"type": "run_started"}\n\n', 'data: {"type": "run_paused"}\n\n'
    ping = KEEPALIVE_COMMENT.decode()

    events = _events(started + ping + ping + paused)

    assert [event["type"] for event in events] == ["run_started", "run_paused"]


@pytest.mark.usefixtures("tokens")
async def test_serve_가_세운_앱으로_실행하면_주체가_OS_사용자이고_트레이스가_그_디렉터리에_남는다(
    workspace: Path, uvicorn_calls: list[dict[str, object]]
) -> None:
    """신원의 출처를 정하는 것은 조립이다(ADR 0015). 채널이 스스로 OS 사용자를 읽지 않는다. 실행
    하나가 도구 포트와 시계와 트레이스 포트를 모두 지나므로 `serve` 가 그것들을 만들어 넘겼다는
    것도 함께 잰다. 무엇을 넘겼는지를 인자로 재지 않고 세운 앱의 답으로 잰다."""
    main(["serve", "--traces", "t"])
    (call,) = uvicorn_calls
    app = call["app"]
    assert isinstance(app, FastAPI)
    channel = {"Authorization": f"Bearer {CHANNEL_TOKEN}"}

    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://serve.test") as client,
    ):
        response = await client.post(
            "/runs", json={"agent": "echo", "request": "hi"}, headers=channel
        )

    events = _events(response.text)
    assert [event["type"] for event in events] == ["run_started", "run_finished"]
    assert events[0]["principal"] == getpass.getuser()
    (trace_file,) = _trace_files(workspace / "t")
    assert trace_file.stem == events[0]["run_id"]


# uvicorn 이 빈 포트를 고른 뒤 찍는 기동 줄. 앱의 수명이 열리고 소켓이 듣기 시작한 뒤에 나온다.
LISTENING = re.compile(r"Uvicorn running on (http://\S+)")
# 실제 serve 가 설 때까지 기다리는 상한. 대부분은 import 시간이다.
STARTUP_SECONDS = 30
# 읽기 상한은 keepalive 간격(FastAPI 기본 15초)보다 길면 된다. 모델이 오래 조용해도 ping 이 읽기를
# 깨운다. 조각 사이만 재므로 전체 상한은 따로 `_post_stream` 이 본다.
STREAM_TIMEOUT = Timeout(10.0, read=60.0)
# 요청 하나가 결말까지 가는 상한. 모델 호출 둘과 도구 호출 하나가 넉넉히 들어가는 길이다.
STREAM_SECONDS = 120


@contextmanager
def _serving(root: Path, *, admin_token: str, channel_token: str) -> Generator[str]:
    """실제 `serve` 프로세스 하나를 빈 포트에 띄우고 요청을 받을 수 있게 되면 그 주소를 준다.

    포트는 `--port 0` 으로 uvicorn 이 고르고 그 기동 줄에서 읽는다. 읽은 순간 서버가 서 있으므로
    설 때까지 헬스 체크를 되풀이할 까닭도, 미리 고른 포트를 남이 먼저 가져갈 틈도 없다. 대가는
    uvicorn 의 기동 문구에 기대는 것이고, 문구가 바뀌면 서지 않았다는 실패가 된다.

    출력은 파이프가 아니라 파일로 받는다. 비우는 쪽이 없는 파이프는 차면 서버를 쓰기에서 세운다.
    나갈 때 프로세스를 거두고 로그를 표준 에러로 옮긴다. pytest 는 실패한 테스트의 캡처만 보여
    주므로 서버 쪽 원인이 실패와 함께 보이고 초록에서는 조용하다. 도구 서버도 serve 와 함께
    끝난다 — 모델 호출 도중에 실패시킨 변이에서도 남은 프로세스가 없었다(티켓 05).
    """
    log = root / "serve.log"
    env = _env() | {ADMIN_TOKEN_ENV: admin_token, CHANNEL_TOKEN_ENV: channel_token}
    argv = [sys.executable, "-m", "agent_os.main", "serve", "--port", "0", "--traces", "t"]
    with log.open("w", encoding="utf-8") as sink:
        process = subprocess.Popen(argv, cwd=root, stdout=sink, stderr=sink, env=env)
        try:
            yield _wait_for_address(process, log)
        finally:
            _stop(process)
            sys.stderr.write(log.read_text(encoding="utf-8", errors="replace"))


def _wait_for_address(process: subprocess.Popen[bytes], log: Path) -> str:
    """기동 줄이 찍히면 그 주소. 그 전에 프로세스가 끝나거나 상한을 넘기면 실패한다."""
    deadline = time.monotonic() + STARTUP_SECONDS
    while time.monotonic() < deadline:
        listening = LISTENING.search(log.read_text(encoding="utf-8", errors="replace"))
        if listening is not None:
            return listening.group(1)
        if process.poll() is not None:
            break
        time.sleep(0.05)
    pytest.fail("serve 가 서지 않았다. 서버 로그는 캡처된 표준 에러에 있다")


def _stop(process: subprocess.Popen[bytes]) -> None:
    """거두고 끝날 때까지 기다린다. 멈추라는 신호에 제때 답하지 않으면 죽인다."""
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def _post_stream(client: Client, url: str, body: Mapping[str, Json]) -> str:
    """POST 하나의 SSE 본문을 결말까지. 200 이 아니면 그 봉투를 싣고 실패한다.

    읽기 상한은 조각 사이만 재서, 모델 호출이 멈춰도 keepalive 가 오는 한 끝나지 않는다. 그래서
    조각이 올 때마다 전체 상한을 보고 넘으면 받은 데까지 싣고 실패한다 — 그래야 `_serving` 의
    정리까지 간다. keepalive 가 간격마다 오므로 상한을 넘긴 뒤 늦어도 그만큼 안에 알아챈다.
    """
    deadline = time.monotonic() + STREAM_SECONDS
    with client.stream("POST", url, json=body) as response:
        if response.status_code != 200:
            response.read()
            pytest.fail(f"{url} 이 {response.status_code} 로 답했다: {response.text}")
        chunks: list[str] = []
        for chunk in response.iter_text():
            chunks.append(chunk)
            if time.monotonic() > deadline:
                pytest.fail(
                    f"{url} 의 스트림이 {STREAM_SECONDS}초 안에 끝나지 않았다:\n{''.join(chunks)}"
                )
        return "".join(chunks)


@pytest.mark.llm
def test_실제_serve_에서_HTTP_로_일으킨_실행이_승인_대상에서_멈추고_HTTP_승인으로_끝까지_간다(
    tmp_path: Path,
) -> None:
    """바깥 이음매. 가짜로 증명할 수 없는 것만 잰다 — `main.py` 의 조립, uvicorn 이 실제 소켓으로
    SSE 를 흘리는 것, 실제 모델이 채널을 지나는 것, 멈춘 실행이 요청을 건너 트레이스로 재개되는 것.

    `gatedcalc` 와 실제 stdio 서버는 프로세스를 넘는 CLI 테스트와 같다. 다른 것은 면 하나다 —
    실행을 일으키고 결정을 내는 것이 셸이 아니라 HTTP 요청 둘이다.
    """
    assert "ANTHROPIC_API_KEY" in os.environ, "ANTHROPIC_API_KEY 가 없다. .env 를 확인한다"
    _write_mcp_plugin(tmp_path, "fixture")
    _write_plugin(tmp_path, "gatedcalc", GATEDCALC_SRC, GATEDCALC_MANIFEST)
    # 소켓이 듣는 동안 같은 기계의 다른 프로세스가 짐작할 수 없는 값. 둘이 달라야 선다(ADR 0015).
    admin_token, channel_token = secrets.token_urlsafe(), secrets.token_urlsafe()

    with (
        _serving(tmp_path, admin_token=admin_token, channel_token=channel_token) as address,
        Client(
            base_url=address,
            headers={"Authorization": f"Bearer {channel_token}"},
            timeout=STREAM_TIMEOUT,
            trust_env=False,  # 루프백을 재는 테스트라 환경의 프록시를 따르지 않는다
        ) as client,
    ):
        paused = _post_stream(client, "/runs", {"agent": "gatedcalc", "request": "2 더하기 3은?"})
        # 여기서 먼저 단언한다. 멈추지 못한 스트림의 식별자로 승인을 보내면 그 409 가 원인을 가린다.
        paused_stream = _events(paused)
        assert paused_stream[-1]["type"] == "run_paused", paused
        run_id = paused_stream[0]["run_id"]
        resumed = _post_stream(client, f"/runs/{run_id}/approval", {"decision": "approve"})

    assert paused_stream[0]["type"] == "run_started"
    assert paused_stream[-1]["tool"] == "add"
    resumed_stream = _events(resumed)
    assert [event["type"] for event in resumed_stream[:2]] == ["approval_granted", "run_resumed"]
    assert resumed_stream[-1]["type"] == "run_finished", resumed
    assert "5" in str(resumed_stream[-1]["output"])
    (trace_file,) = _trace_files(tmp_path / "t")  # 재개가 끼어도 실행 하나에 파일 하나다
    assert trace_file.stem == run_id
    events = [e for e in _read(trace_file).events if not isinstance(e, UnknownEvent)]
    types = [e.type for e in events]
    # 두 스트림을 이으면 그 실행의 트레이스다. 재개 스트림은 재생된 사실을 내지 않는다(ADR 0009).
    assert [event["type"] for event in [*paused_stream, *resumed_stream]] == types
    assert types.count("run_started") == 1  # 재개는 새 실행이 아니라 같은 실행이다
    boundaries = ("approval_granted", "run_resumed", "tool_called")
    assert [t for t in types if t in boundaries] == list(boundaries)
    assert [(e.tool, e.ok) for e in events if isinstance(e, ToolCalled)] == [("add", True)]


def test_플러그인_루트를_지정하면_작업_디렉터리의_plugins_가_아니라_거기서_읽는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """하드코딩된 플러그인 루트가 풀렸다는 것. 지정하지 않으면 못 찾는 자리에만 에이전트를 둔다."""
    monkeypatch.chdir(tmp_path)
    _write_plugin(tmp_path / "custom", "echo", ECHO_SRC)

    found = main(["run", "echo", "hi", "--traces", "t", "--plugins-root", "custom/plugins"])
    out, _ = capsys.readouterr()
    missed = main(["run", "echo", "hi", "--traces", "t"])

    assert found == 0
    assert out == "echo:hi\n"
    assert missed == 1


def test_플러그인_루트를_지정했으면_안내된_재개_명령이_그것을_물려받는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """안내가 작동하지 않으면 안내가 아니다. 재개도 같은 디렉터리에서 에이전트를 찾아야 한다."""
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "custom"
    _write_mcp_plugin(root, "fixture")
    _write_plugin(root, "gated", GATED_SRC, GATED_MANIFEST)

    paused = main(["run", "gated", "hi", "--traces", "t", "--plugins-root", "custom/plugins"])
    argv = _guidance(capsys.readouterr().out)
    code = main(argv)

    assert paused == EXIT_PAUSED
    assert "--plugins-root" in argv
    assert code == 0
    assert capsys.readouterr().out == "5\n"
