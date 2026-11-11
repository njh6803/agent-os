"""tools/hook_pyright_unchecked_path.py 의 판정과 표지. main 은 stdin 과 임시 폴더를 바꿔 끼워
표지 길을 보고, 래퍼를 거친 실제 실행은 tools/run_hooks.py 의 표가 본다.

pyright 가 어느 경로를 분석하지 않는지는 이 브랜치에서 pyright 1.1.414 로 손으로 봤다
(`uv run pyright --outputjson <경로>` 의 `summary.filesAnalyzed`): 점 폴더, `node_modules`,
`__pycache__` 아래와 점으로 시작하는 파일 이름(`tests/.pp_dot_probe.py`)은 0, `include` 밖의
점 없는 폴더, 저장소 밖 파일, 저장소 밖 점 폴더 아래의 파일은 1 이었다.
"""

from __future__ import annotations

import io
import json
import sys
import tempfile
from pathlib import Path

import pytest
from tools.hook_pyright_unchecked_path import (
    BASH,
    LEAD,
    HookPayload,
    claim_first,
    context_for,
    find_root,
    main,
    marker_name,
    root_relative,
    unchecked_paths,
)
from tools.run_hooks import registered_matchers


def _bash(command: str, cwd: str | None = None) -> HookPayload:
    payload: HookPayload = {"tool_name": "Bash", "tool_input": {"command": command}}
    if cwd is not None:
        payload["cwd"] = cwd
    return payload


@pytest.mark.parametrize(
    "command",
    [
        # 대기열 431 의 사건 꼴: .scratch 아래 프로브를 uv run pyright 로 쳤다.
        "uv run pyright .scratch/harness/probes/x.py",
        "uv run pyright --outputjson .scratch/harness/probes/x.py",
        "pyright .scratch/x.py",
        "uv run python -m pyright .scratch/x.py",
        "uv run --project C:/p --no-sync python -m pyright .scratch/x.py",
        "uv run --env-file .env pyright .scratch/x.py",
        ".venv/Scripts/pyright.exe .scratch/x.py",
        "FOO=1 pyright .scratch/x.py",
        "uv run pyright ./.scratch/x.py",
        'uv run pyright ".scratch/x.py"',
        "uv run pyright '.scratch/x.py'",
        "uv run pyright .scratch\\x.py",
        "uv run pyright .scratch",
        "uv run pyright web/node_modules/x.py",
        "uv run pyright tools/__pycache__/x.py",
        "uv run pyright .claude/worktrees/w/tests/x.py",
        "uv run pyright tests/ok.py .scratch/x.py",
        "cd tools && uv run pyright .scratch/x.py | tail -3",
        "uv run pyright .scratch/x.py 2>&1",
        "uv run pyright .scratch/x.py > out.txt",
        "uv run pyright --pythonpath .venv/Scripts/python.exe .scratch/x.py",
        "uv run pyright --threads 4 .scratch/x.py",
        "uv run pyright -- .scratch/x.py",
    ],
)
def test_분석하지_않는_폴더_아래의_경로를_받으면_짚는다(command: str) -> None:
    assert unchecked_paths(command, None), command


@pytest.mark.parametrize(
    "command",
    [
        "uv run pyright",
        "uv run pyright .",
        "uv run pyright ..",
        "uv run pyright ./",
        "uv run pyright tests/tools/test_x.py",
        "uv run pyright src tests tools",
        "uv run pyright --outputjson tests/x.py",
        # include 밖이지만 점 없는 폴더는 명시하면 분석된다(손으로 봤다).
        "uv run pyright docs/x.py",
        "uv run pyright docs",
        "uv run pyright web/apps/x.py",
        "uv run pyright ../x.py",
        "uv run pyright ./tests/x.py",
        "uv run pyright tests/x.py.bak",
    ],
)
def test_분석되는_경로는_짚지_않는다(command: str) -> None:
    assert unchecked_paths(command, None) == [], command


def test_점으로_시작하는_파일_이름은_폴더가_아니어도_분석하지_않는다() -> None:
    # `.` 로 시작하는 성분이면 마지막 성분(파일 이름)도 pyright 의 `**/.*` 제외에 든다. 손으로
    # 봤다: `uv run pyright --outputjson tests/.pp_dot_probe.py` 의 `filesAnalyzed` 가 0 이었다.
    assert unchecked_paths("uv run pyright tests/.x.py", None) == ["tests/.x.py"]


@pytest.mark.parametrize(
    "command",
    [
        "uv run pyright tests/x.py > .scratch/out.json",
        "uv run pyright tests/x.py >> .scratch/out.json 2>&1",
        "uv run pyright tests/x.py 2> .scratch/err.txt",
        "uv run pyright tests/x.py &> .scratch/out.txt",
        "uv run pyright --pythonpath .venv/Scripts/python.exe tests/x.py",
        "uv run pyright --venvpath .venvs tests/x.py",
        # `pyright --help` 의 `-v,--venvpath` 와 `--createstub <IMPORT>` 도 값을 따로 받는다.
        "uv run pyright -v .venvs tests/x.py",
        "uv run pyright --createstub .scratch tests/x.py",
        "uv run pyright --level error tests/x.py",
    ],
)
def test_리다이렉트_대상과_옵션_값은_경로_인자가_아니다(command: str) -> None:
    assert unchecked_paths(command, None) == []


@pytest.mark.parametrize(
    "command",
    [
        "if true; then pyright .scratch/x.py; fi",
        "while true; do pyright .scratch/x.py; done",
        "! uv run pyright .scratch/x.py",
        "{ uv run pyright .scratch/x.py; }",
        "env -u FOO pyright .scratch/x.py",
        "uv tool run pyright .scratch/x.py",
    ],
)
def test_명령_낱말_앞의_셸_예약어와_래퍼_옵션_값은_건너뛰고_짚는다(command: str) -> None:
    assert unchecked_paths(command, None) == [".scratch/x.py"], command


@pytest.mark.parametrize(
    "command",
    [
        "uv run --directory sub pyright .scratch/x.py",
        "uv run --directory=sub pyright .scratch/x.py",
        "env -C sub pyright .scratch/x.py",
        "env --chdir sub pyright .scratch/x.py",
    ],
)
def test_작업_폴더를_바꾸는_래퍼_옵션이_앞에_있으면_판정하지_않는다(command: str) -> None:
    # 못 보는 것: 경로의 기준 폴더가 바뀌어 페이로드의 cwd 로는 읽을 수 없다.
    assert unchecked_paths(command, None) == [], command


@pytest.mark.parametrize(
    "command",
    [
        'uv run pyright "$f"',
        'uv run pyright "${DIR}/x.py"',
        "uv run pyright $(ls .scratch)",
        "uv run pyright `ls .scratch`",
        "(uv run pyright .scratch/x.py)",
    ],
)
def test_셸_변수와_명령_치환과_괄호가_든_인자는_판정하지_않는다(command: str) -> None:
    # 못 보는 것: 셸이 확장한 결과는 보지 못하고, 낱말에 `$`·백틱·괄호가 들면 건너뛴다. `(…)` 묶음의
    # 마지막 인자는 닫는 괄호가 붙어 건너뛴다.
    assert unchecked_paths(command, None) == [], command


def test_괄호_묶음_안의_호출은_마지막_인자만_건너뛰고_앞_인자는_본다() -> None:
    assert unchecked_paths("(uv run pyright .scratch/a.py tests/x.py)", None) == [".scratch/a.py"]


def test_글롭은_글자_그대로_읽는다() -> None:
    # 못 보는 것: 셸이 확장한 결과는 보지 못하고, 글롭은 글자 그대로 점 폴더로 읽어 짚는다.
    assert unchecked_paths("uv run pyright .scratch/*.py", None) == [".scratch/*.py"]


@pytest.mark.parametrize(
    "command",
    ["uv run pyright tests/x.py # .scratch/y.py", "uv run pyright # .scratch/y.py"],
)
def test_주석_뒤의_낱말은_경로_인자가_아니다(command: str) -> None:
    assert unchecked_paths(command, None) == []


def test_낱말_안의_샵은_주석이_아니다() -> None:
    assert unchecked_paths("uv run pyright .scratch/a#b.py", None) == [".scratch/a#b.py"]


def test_주석_글_안의_제어_연산자는_명령을_갈라_그_뒤를_명령으로_읽는다() -> None:
    # 못 보는 것(거짓 양성): 글 가르기가 주석 안의 `;` 에서 명령을 가른다.
    command = "uv run pyright tests/x.py # 끝; pyright .scratch/y.py"
    assert unchecked_paths(command, None) == [".scratch/y.py"]


def test_이스케이프한_공백이_든_경로는_갈라져_읽는다() -> None:
    # 못 보는 것: 백슬래시를 슬래시로 바꾸는 글 가르기가 `a\ b.py` 를 `a/` 와 `b.py` 로 가른다.
    assert unchecked_paths(r"uv run pyright .scratch/a\ b.py", None) == [".scratch/a/"]


@pytest.mark.parametrize(
    "command",
    [
        "uv run --foo bar pyright .scratch/x.py",
        "xargs pyright .scratch/x.py",
        'bash -c "pyright .scratch/x.py"',
    ],
)
def test_목록_밖의_래퍼_뒤의_pyright_는_보지_못한다(command: str) -> None:
    # 못 보는 것(거짓 음성): 낱말 앞이 래퍼 목록 밖이면 pyright 를 부른 명령으로 보지 않는다.
    assert unchecked_paths(command, None) == [], command


@pytest.mark.parametrize(
    "command", ["uv run pyright ~/.scratch/x.py", "uv run pyright ~/proj/.scratch/x.py"]
)
def test_홈_아래_경로는_판정하지_않는다(command: str) -> None:
    # `~` 는 셸이 홈으로 확장해 저장소 밖이다. 상대 경로로 읽으면 거짓 양성이 난다.
    assert unchecked_paths(command, None) == []


def test_알리는_경로만_돌려준다() -> None:
    assert unchecked_paths(
        "uv run pyright tests/ok.py .scratch/a.py docs/b.py .scratch/c.py", None
    ) == [
        ".scratch/a.py",
        ".scratch/c.py",
    ]


@pytest.mark.parametrize(
    "command",
    [
        "uv run pyright --project .scratch/p .scratch/x.py",
        "uv run pyright -p .scratch/p .scratch/x.py",
        "uv run pyright --project=.scratch/p .scratch/x.py",
    ],
)
def test_프로젝트_옵션을_쓰면_루트를_알_수_없어_판정을_건너뛴다(command: str) -> None:
    # 못 보는 것: 다른 프로젝트 설정을 쓰면 제외 규칙의 기준 폴더가 바뀐다.
    assert unchecked_paths(command, None) == []


@pytest.mark.parametrize(
    "command",
    [
        "grep pyright .scratch/x.py",
        "echo pyright .scratch/x.py",
        "cat .venv/Scripts/pyright.exe",
        'git commit -m "pyright .scratch/x.py"',
        "uv run pytest .scratch/x.py",
        "uv run ruff check .scratch/x.py",
        "pyrightx .scratch/x.py",
        "uv run pyright-langserver .scratch/x.py",
        "ls .scratch",
    ],
)
def test_pyright_가_명령_낱말이_아니면_짚지_않는다(command: str) -> None:
    assert unchecked_paths(command, None) == [], command


def test_명령_하나가_pyright_고_다른_하나가_아니면_pyright_쪽_인자만_본다() -> None:
    assert unchecked_paths("ls .scratch && uv run pyright tests/x.py", None) == []
    assert unchecked_paths("uv run pyright tests/x.py; ls .scratch", None) == []
    assert unchecked_paths("ls .scratch; uv run pyright .scratch/x.py", None) == [".scratch/x.py"]


def test_따옴표가_닫히지_않은_명령도_죽지_않는다() -> None:
    # `shlex` 가 실패하면 공백으로 나누고 따옴표를 벗겨 알리는 쪽으로 기운다.
    assert unchecked_paths('uv run pyright ".scratch/x.py', None) == [".scratch/x.py"]


def _project(tmp_path: Path, *parts: str) -> Path:
    """`[tool.pyright]` 가 든 pyproject 를 둔 프로젝트 루트."""
    root = tmp_path.joinpath(*parts)
    root.mkdir(parents=True)
    (root / "pyproject.toml").write_text('[tool.pyright]\ninclude = ["tests"]\n', encoding="utf-8")
    return root


def test_작업_폴더에서_위로_pyright_설정이_든_프로젝트_루트를_찾는다(tmp_path: Path) -> None:
    root = _project(tmp_path, "proj")
    deep = root / "tests" / "tools"
    deep.mkdir(parents=True)
    assert find_root(str(deep)) == root
    assert find_root(str(root)) == root


def test_pyright_설정이_없는_pyproject_는_루트가_아니다(tmp_path: Path) -> None:
    outer = _project(tmp_path, "outer")
    inner = outer / "inner"
    inner.mkdir()
    (inner / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
    assert find_root(str(inner)) == outer


def test_pyrightconfig_json_도_루트의_표지다(tmp_path: Path) -> None:
    root = tmp_path / "p"
    root.mkdir()
    (root / "pyrightconfig.json").write_text("{}", encoding="utf-8")
    assert find_root(str(root)) == root


def test_루트를_못_찾으면_None_이다(tmp_path: Path) -> None:
    lone = tmp_path / "lone"
    lone.mkdir()
    # tmp_path 의 위쪽에 pyright 설정이 있을 수 있으니 그 밖에서는 단언하지 않고, 없는 폴더만 본다.
    assert find_root(str(tmp_path / "없는-폴더")) is None
    assert find_root("") is None


def test_절대_경로는_루트_기준으로_바꿔_본다(tmp_path: Path) -> None:
    root = _project(tmp_path, "proj")
    cwd = str(root)
    base = root.as_posix()
    hit = f"{base}/.scratch/x.py"
    assert unchecked_paths(f'uv run pyright "{hit}"', cwd) == [hit]
    assert unchecked_paths(f'uv run pyright "{base}/tests/x.py"', cwd) == []


def test_루트가_점_폴더_아래여도_루트_기준으로만_본다(tmp_path: Path) -> None:
    # 이 저장소의 워크트리는 `.claude/worktrees/<이름>/` 아래라 절대 경로가 `.claude` 를 품는다.
    # 그 안의 tests 는 분석된다(손으로 봤다: 워크트리에서 `uv run pyright tests/_pp/a.py` 가 1).
    root = _project(tmp_path, ".claude", "worktrees", "w")
    cwd = str(root)
    base = root.as_posix()
    hit = f"{base}/.scratch/x.py"
    assert unchecked_paths(f'uv run pyright "{base}/tests/x.py"', cwd) == []
    assert unchecked_paths("uv run pyright tests/x.py", cwd) == []
    assert unchecked_paths(f'uv run pyright "{hit}"', cwd) == [hit]


def test_작업_폴더를_기준으로_상대_경로를_루트_기준으로_바꾼다(tmp_path: Path) -> None:
    root = _project(tmp_path, "proj")
    probes = root / ".scratch" / "probes"
    probes.mkdir(parents=True)
    tests = root / "tests"
    tests.mkdir()
    # 점 폴더 안에서 점 없는 이름을 줘도 루트 기준으로는 점 폴더 아래다.
    assert unchecked_paths("uv run pyright x.py", str(probes)) == ["x.py"]
    # 점 없는 폴더에서 점 폴더로 올라가는 경로.
    assert unchecked_paths("uv run pyright ../.scratch/x.py", str(tests)) == ["../.scratch/x.py"]
    assert unchecked_paths("uv run pyright x.py", str(tests)) == []
    # `.scratch/probes` 의 `..` 는 `.scratch` 라 `../tests` 는 `.scratch/tests` 이고, 점 폴더를
    # 벗어나려면 둘을 올라간다.
    assert unchecked_paths("uv run pyright ../tests/x.py", str(probes)) == ["../tests/x.py"]
    assert unchecked_paths("uv run pyright ../../tests/x.py", str(probes)) == []


@pytest.mark.parametrize(
    ("arg", "expected"),
    [
        pytest.param("/c/proj/.scratch/x.py", (".scratch", "x.py"), id="점-폴더"),
        pytest.param("/C/proj/tests/x.py", ("tests", "x.py"), id="대문자-드라이브"),
        pytest.param("/c/other/x.py", None, id="루트-밖"),
    ],
)
def test_Git_Bash_꼴_절대_경로는_드라이브_꼴로_바꿔_읽는다(
    arg: str, expected: tuple[str, ...] | None
) -> None:
    # Bash 도구가 주는 `/c/…` 꼴. `C:/` 로 바꿔 루트와 견준다. 루트는 드라이브 꼴로 직접 준다.
    assert root_relative(arg, None, Path("C:/proj")) == expected


def test_앞_명령의_cd_로_바뀐_작업_폴더는_보지_못한다(tmp_path: Path) -> None:
    # 못 보는 것(거짓 음성): 페이로드의 cwd 는 호출 앞의 작업 폴더라 `cd .scratch && …` 의 `x.py`
    # 는 루트 바로 아래의 `x.py` 로 읽는다.
    root = _project(tmp_path, "proj")
    (root / ".scratch").mkdir()
    assert unchecked_paths("cd .scratch && uv run pyright x.py", str(root)) == []


def test_루트_밖의_경로는_짚지_않는다(tmp_path: Path) -> None:
    # 못 보는 것: 저장소 밖 파일은 분석된다. 손으로 봤다: 저장소 밖 점 폴더 아래의 파일도
    # `filesAnalyzed` 가 1 이었다. 그래서 짚지 않는 쪽이 맞다.
    root = _project(tmp_path, "proj")
    outside = (tmp_path / ".hidden" / "x.py").as_posix()
    assert unchecked_paths(f'uv run pyright "{outside}"', str(root)) == []
    assert unchecked_paths("uv run pyright ../.hidden/x.py", str(root)) == []


def test_작업_폴더를_모르면_상대_경로를_글로만_본다() -> None:
    assert unchecked_paths("uv run pyright .scratch/x.py", None) == [".scratch/x.py"]
    # 루트를 모르면 절대 경로는 판정하지 않는다.
    assert unchecked_paths("uv run pyright C:/p/.scratch/x.py", None) == []
    assert unchecked_paths("uv run pyright /home/u/.scratch/x.py", None) == []


def test_알림은_알린_경로를_들고_사본을_점_없는_폴더에_두라고_한다() -> None:
    context = context_for(_bash("uv run pyright tests/ok.py .scratch/a.py"))
    assert context is not None
    assert context.startswith(LEAD)
    assert "`.scratch/a.py`" in context
    assert "tests/ok.py" not in context
    assert "`0 errors`" in context
    assert "tests/" in context
    assert "filesAnalyzed" in context
    assert "--outputjson" in context
    assert "docs/constitution/operations.md" in context


def test_알리지_않으면_None_이다() -> None:
    assert context_for(_bash("uv run pyright tests/x.py")) is None


def test_Bash_가_아니면_지나간다() -> None:
    for tool in ("PowerShell", "Write", "Edit", "Read"):
        payload: HookPayload = {
            "tool_name": tool,
            "tool_input": {"command": "uv run pyright .scratch/x.py"},
        }
        assert context_for(payload) is None, tool


@pytest.mark.parametrize(
    "raw",
    [
        {"tool_name": "Bash"},
        {"tool_name": "Bash", "tool_input": "uv run pyright .scratch/x.py"},
        {"tool_name": "Bash", "tool_input": {}},
        {"tool_name": "Bash", "tool_input": {"command": 3}},
        {"tool_name": "Bash", "tool_input": {"command": ["pyright", ".scratch/x.py"]}},
        {"tool_name": "Bash", "tool_input": {"command": ""}},
    ],
)
def test_페이로드의_꼴이_어긋나도_죽지_않는다(raw: object) -> None:
    # HookPayload 에 맞지 않는 꼴이라 main 처럼 JSON 에서 풀어 넘긴다.
    payload = json.loads(json.dumps(raw))
    assert context_for(payload) is None


def test_cwd_가_문자열이_아니면_글로만_본다() -> None:
    raw = {
        "tool_name": "Bash",
        "tool_input": {"command": "uv run pyright .scratch/x.py"},
        "cwd": 3,
    }
    payload = json.loads(json.dumps(raw))
    assert context_for(payload) is not None


def test_표지는_세션과_에이전트마다_한_번이다(tmp_path: Path) -> None:
    main_key = marker_name("s1", "")
    assert claim_first(main_key, tmp_path)
    assert not claim_first(main_key, tmp_path)
    assert claim_first(marker_name("s1", "agent-a"), tmp_path)
    assert claim_first(marker_name("s2", ""), tmp_path)


def test_표지_폴더를_만들지_못하면_알린다(tmp_path: Path) -> None:
    blocker = tmp_path / "file"
    blocker.write_text("", encoding="utf-8")
    assert claim_first(marker_name("s1", ""), blocker / "state")
    assert claim_first(marker_name("s1", ""), blocker)


def test_표지_파일을_만들지_못하면_알린다(tmp_path: Path) -> None:
    assert claim_first("없는-폴더/표지", tmp_path)


def _run_main(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], payload: HookPayload
) -> str:
    """main 을 한 번 돌려 알린 문장을, 알리지 않았으면 빈 문자열을 돌려준다."""
    stdin = io.TextIOWrapper(io.BytesIO(json.dumps(payload).encode("utf-8")), encoding="utf-8")
    monkeypatch.setattr(sys, "stdin", stdin)
    assert main() == 0
    out = capsys.readouterr().out
    if not out:
        return ""
    output = json.loads(out)["hookSpecificOutput"]
    assert output["hookEventName"] == "PostToolUse"
    context = output["additionalContext"]
    assert isinstance(context, str)
    return context


def _session(command: str, agent_id: str = "") -> HookPayload:
    payload = _bash(command)
    payload["session_id"] = "session-1"
    if agent_id:
        payload["agent_id"] = agent_id
    return payload


def test_main_은_세션과_에이전트마다_한_번_알린다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    command = "uv run pyright .scratch/x.py"
    assert LEAD in _run_main(monkeypatch, capsys, _session(command))
    assert _run_main(monkeypatch, capsys, _session(command)) == ""
    assert LEAD in _run_main(monkeypatch, capsys, _session(command, "agent-a"))


def test_main_은_짚지_않는_명령이면_표지를_쓰지_않는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    assert _run_main(monkeypatch, capsys, _session("uv run pyright tests/x.py")) == ""
    assert LEAD in _run_main(monkeypatch, capsys, _session("uv run pyright .scratch/x.py"))


def test_main_은_임시_폴더가_없으면_호출마다_알린다(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def no_temp() -> str:
        raise FileNotFoundError("쓸 수 있는 임시 폴더가 없다")

    monkeypatch.setattr(tempfile, "gettempdir", no_temp)
    command = "uv run pyright .scratch/x.py"
    assert LEAD in _run_main(monkeypatch, capsys, _session(command))
    assert LEAD in _run_main(monkeypatch, capsys, _session(command))


def test_표지_폴더가_다른_계기와_다르다() -> None:
    # 같은 세션의 두 계기가 한 표지를 나눠 쓰면 먼저 뜬 쪽이 다른 쪽을 끈다.
    from tools import hook_journal_evidence, hook_probe_conclusion, hook_pyright_unchecked_path

    states = {
        hook_journal_evidence.STATE_DIR,
        hook_probe_conclusion.STATE_DIR,
        hook_pyright_unchecked_path.STATE_DIR,
    }
    assert len(states) == 3


def test_등록의_매처가_훅이_아는_도구와_같다() -> None:
    assert registered_matchers("hook_pyright_unchecked_path.py", "PostToolUse") == [BASH]
