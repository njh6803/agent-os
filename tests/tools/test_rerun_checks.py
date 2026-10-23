"""tools/rerun_checks.py: 회차를 열기 전의 계정·설정과 호출마다의 설정·모델·오염·한도.

값만 받는 판정은 지은 값으로 본다. 계정은 가짜 `claude`(`tests/tools/fake_claude.py`)의
`auth status`로, 호출마다의 판정(`Screen`)은 지은 원본 줄과 설정 폴더에 쓴 세션 기록 파일로 본다.
허용 밖의 init 에서 호출을 끄는 것과 한도의 끝은 가짜와 B 하나뿐인 임시 클론으로 회차 고리를
실제로 돈다(`tests/tools/test_rerun_continue.py`와 같은 틀).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path

import pytest
from tests.tools import fake_claude as fake
from tools.proc_command_line import CommandLineReader, command_line
from tools.rerun_checks import (
    BLOCKED_TOOL,
    BUILTIN_PLUGINS,
    CLAUDE_LINK,
    CODE_REVIEW_MODEL,
    CONFIG_FOLDER,
    GH_WORD,
    GITHUB,
    GITHUBUSERCONTENT,
    HAIKU,
    MAIN_CHECKOUT,
    OPEN_SESSION_SCRIPT,
    OPEN_SESSION_SKILL,
    OTHER_ROUND,
    PATTERN_NAMES,
    REASON_CONTAMINATION,
    REASON_MODEL,
    REASON_SETTINGS,
    REPOSITORY,
    UNKNOWN_TOOL,
    USER_CLAUDE,
    Limit,
    Screen,
    Watched,
    account_problem,
    agent_model,
    allowed_plugins,
    before_round,
    command_patterns,
    enabled_plugins,
    harness_models,
    init_problem,
    limit_of,
    model_mismatch,
    path_patterns,
    resolve_model,
    screen_for,
    settings_env_problem,
    watched_from,
    watched_paths,
    windows_of,
)
from tools.rerun_continue import run_sessions
from tools.rerun_files import (
    ARMS,
    END_NOT_MEASURED,
    NOT_MEASURED_REASONS,
    OPUS,
    REASON_LIMIT,
    SONNET,
    End,
    Hit,
    Json,
    LineCount,
    Task,
    Tokens,
    Window,
    read_record,
    write_record,
)
from tools.rerun_round import RoundDir, create_round_dir, session_env
from tools.rerun_session import (
    SYNTHETIC,
    CallRun,
    Continued,
    Drove,
    Elsewhere,
    Launched,
    Stop,
    directive,
    outcome_of,
    pick_result_commit,
    round_record,
    session_record,
    summarize_call,
)
from tools.run_hooks import REPO_LOCATION_VARS

from tools import rerun_checks

ROOT = Path(__file__).resolve().parents[2]
ARM = ARMS[0]  # Opus xhigh
ACCOUNT = "njh6803"
TASK = Task(
    task_id="rerun-x-03",
    ticket=".scratch/rerun-x/issues/03-thing.md",
    base="b" * 40,  # 회고리를 도는 시험마다 클론의 B 로 바꾼다
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
S1 = "00000000-0000-4000-8000-000000000001"
S2 = "00000000-0000-4000-8000-000000000002"
SLUG = "own-slug"
PYRIGHT = "pyright-lsp@claude-plugins-official"


def _line(event: Json) -> str:
    return json.dumps(event, ensure_ascii=False) + "\n"


def _launched(events: Sequence[Json], *, session_id: str = S1) -> Launched:
    lines = tuple(_line(e) for e in events)
    return Launched(
        session_id=session_id,
        budget_usd=40.0,
        stream_file=Path("01.jsonl"),
        drove=Drove(lines=lines, exit_code=0, stop=Stop.EXITED),
        summary=summarize_call(lines),
    )


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


@dataclass(frozen=True)
class Room:
    """시험 하나의 자리. 회차 폴더와 설정 폴더, 주 체크아웃과 홈의 대역."""

    place: RoundDir
    config: Path
    main: Path
    home: Path
    task: Task

    def screen(self) -> Screen:
        return screen_for(
            self.place, ARM, config_dir=self.config, main_checkout=self.main, home=self.home
        )


def _room(
    tmp_path: Path,
    *,
    settings: Json = None,
    agents: Mapping[str, str] | None = None,
    git: bool = False,
) -> Room:
    place = create_round_dir(tmp_path / "뿌리", TASK.task_id, ARM.name, 1, token="t1")
    place.clone.mkdir()
    if settings is not None:
        (place.clone / ".claude").mkdir(exist_ok=True)
        (place.clone / ".claude" / "settings.json").write_text(json.dumps(settings), "utf-8")
    for name, text in (agents or {}).items():
        (place.clone / ".claude" / "agents").mkdir(parents=True, exist_ok=True)
        (place.clone / ".claude" / "agents" / name).write_text(text, "utf-8")
    task = TASK
    if git:
        _git(place.clone, "init", "-q", "-b", "main")
        _git(place.clone, "commit", "-q", "--allow-empty", "-m", "B")
        task = replace(TASK, base=_git(place.clone, "rev-parse", "HEAD").strip())
    main = tmp_path / "agent"
    main.mkdir()
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    config = tmp_path / "설정"
    config.mkdir()
    return Room(place=place, config=config, main=main, home=home, task=task)


def _ids(*ids: str) -> Callable[[], str]:
    it: Iterator[str] = iter(ids)
    return lambda: next(it)


def _run(
    room: Room,
    *,
    ids: Sequence[str],
    read_command_line: CommandLineReader = command_line,
) -> tuple[Continued, Screen]:
    screen = room.screen()
    got = run_sessions(
        room.place,
        room.task,
        claude=fake.claude(),
        arm=ARM,
        env=session_env(os.environ, config_dir=str(room.config), round_dir=room.place),
        directive_text=directive(room.task, ARM, "그것을 짓는다"),
        wall_clock_from=time.monotonic(),
        screen=screen,
        watch=screen.watch,
        read_command_line=read_command_line,
        make_session_id=_ids(*ids),
    )
    return got, screen


def _alive(pid: int, marker: str) -> bool:
    argv = command_line(pid)
    return argv is not None and marker in argv


def _gone(pid: int, marker: str) -> bool:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if not _alive(pid, marker):
            return True
        time.sleep(0.2)
    return False


def _pid(entry: dict[str, Json]) -> int:
    pid = entry["pid"]
    assert isinstance(pid, int)
    return pid


def _transcript(
    config: Path,
    session_id: str,
    main: Sequence[Json],
    side: Mapping[str, Sequence[Json]] | None = None,
) -> None:
    """세션 기록 파일을 쓴다. 폴더 이름은 `SLUG`다(러너는 세션 id 로 찾는다)."""
    folder = config / "projects" / SLUG
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{session_id}.jsonl").write_text("".join(_line(m) for m in main), "utf-8")
    for name, lines in (side or {}).items():
        sub = folder / session_id / "subagents"
        sub.mkdir(parents=True, exist_ok=True)
        (sub / f"{name}.jsonl").write_text("".join(_line(m) for m in lines), "utf-8")


def _arm_lines(n: int) -> list[Json]:
    return [fake.transcript_line(ARM.model, ARM.effort, f"msg_{i}") for i in range(n)]


def _use(
    name: str, tool_input: Mapping[str, Json], use_id: str = "toolu_1", parent: str | None = None
) -> Json:
    return fake.tool_use_event(name, tool_input, use_id=use_id, parent=parent)


def _hits(room: Room, *events: Json) -> tuple[Hit, ...]:
    screen = room.screen()
    screen(_launched([fake.init_event(), *events]))
    return screen.findings().contamination


# --- 계정과 설정 폴더 ---


def _status(**fields: Json) -> str:
    base: dict[str, Json] = {
        "loggedIn": True,
        "email": "njh6803@example.com",
        "configDirectory": "D:\\rerun-config",
    }
    base.update(fields)
    return json.dumps({k: v for k, v in base.items() if v is not None})


@pytest.mark.parametrize(
    ("stdout", "ok"),
    [
        (_status(), True),
        (_status(loggedIn=False, email=None), False),  # 로그아웃이면 email 이 없다
        (_status(loggedIn="true"), False),
        (_status(email="other@example.com"), False),
        (_status(email="njh6803.x@example.com"), False),
        (_status(email="njh6803"), False),  # 주소의 꼴이 아니다
        (_status(configDirectory="D:/rerun-config"), False),  # 슬래시만 다르다
        (_status(configDirectory="d:\\rerun-config"), False),  # 대소문자만 다르다
        (_status(configDirectory=None), False),
        ("로그인하지 않았다", False),
        ("[]", False),
        ("", False),
    ],
)
def test_계정은_로그인과_계정_이름과_글자_그대로의_설정_폴더가_모두_맞아야_지난다(
    stdout: str, *, ok: bool
) -> None:
    got = account_problem(stdout, account=ACCOUNT, config_dir="D:\\rerun-config")
    assert (got is None) is ok, got


def test_계정_확인의_까닭에_이메일을_싣지_않는다() -> None:
    got = account_problem(
        _status(email="someone.secret@example.com"), account=ACCOUNT, config_dir="D:\\rerun-config"
    )
    assert got is not None
    assert "someone" not in got and "example.com" not in got


def _env(config: Path) -> dict[str, str]:
    return {**os.environ, "CLAUDE_CONFIG_DIR": str(config)}


SETTINGS_END = End(END_NOT_MEASURED, REASON_SETTINGS, None)


def test_가짜가_로그아웃이면_종료_1이어도_JSON을_풀어_회차를_열지_않는다(tmp_path: Path) -> None:
    config = tmp_path / "설정"
    fake.write_script(config, logged_in=False)
    got = before_round(fake.claude(), env=_env(config), cwd=tmp_path, account=ACCOUNT)
    # 계정 불일치는 회차를 열지 않아 기록이 없다(명세 "클론과 설정 폴더"의 계정)
    assert got is not None and "loggedIn" in got.why and got.end is None


@pytest.mark.parametrize(
    "script",
    [
        {"email": "other@example.com"},
        {"config_directory": "슬래시만 다른 폴더"},  # 시험에서 넘긴 글과 다른 글로 바꾼다
        {"config_directory": "대소문자만 다른 폴더"},
    ],
    ids=["다른_계정", "슬래시만_다른_configDirectory", "대소문자만_다른_configDirectory"],
)
def test_다른_계정과_글자가_다른_설정_폴더는_회차를_열지_않는다(
    tmp_path: Path, script: dict[str, str]
) -> None:
    config = tmp_path / "Config"
    if script.get("config_directory") == "슬래시만 다른 폴더":
        script = {"config_directory": str(config).replace(os.sep, "/" if os.sep == "\\" else "//")}
    elif script.get("config_directory") == "대소문자만 다른 폴더":
        script = {"config_directory": str(config).replace("Config", "config")}
    fake.write_script(
        config,
        email=script.get("email", "njh6803@example.com"),
        config_directory=script.get("config_directory"),
    )
    got = before_round(fake.claude(), env=_env(config), cwd=tmp_path, account=ACCOUNT)
    assert got is not None and got.end is None


def test_맞는_계정과_env_없는_설정이면_회차를_연다(tmp_path: Path) -> None:
    config = tmp_path / "설정"
    fake.write_script(config)
    (config / "settings.json").write_text('{"autoCompactWindow": 400000}', "utf-8")
    assert before_round(fake.claude(), env=_env(config), cwd=tmp_path, account=ACCOUNT) is None


@pytest.mark.parametrize(
    ("text", "marker"),
    [
        ('{"env": {"GH_TOKEN": "x"}}', "env"),
        ("{", "JSON"),
        (None, "읽지 못했다"),  # 파일이 아니라 폴더다
    ],
    ids=["env_키", "JSON_아님", "읽지_못함"],
)
def test_설정_폴더의_settings_json이_틀리면_회차를_열지_않고_측정_아님_설정으로_적는다(
    tmp_path: Path, text: str | None, marker: str
) -> None:
    config = tmp_path / "설정"
    fake.write_script(config)
    if text is None:
        (config / "settings.json").mkdir()
    else:
        (config / "settings.json").write_text(text, "utf-8")
    got = before_round(fake.claude(), env=_env(config), cwd=tmp_path, account=ACCOUNT)
    # 설정 폴더의 잘못은 init 의 것처럼 측정 아님(설정)으로 적는다(명세 "설정 폴더의 설정")
    assert got is not None and got.end == SETTINGS_END, got
    assert marker in got.why and "GH_TOKEN" not in got.why


@pytest.mark.parametrize(
    ("text", "ok"),
    [
        (None, True),  # 파일이 없다
        ("{}", True),
        ('\ufeff{"theme": "dark"}', True),
        ('{"env": {}}', False),
        ('{"theme": "dark", "env": {"A": "1"}}', False),
        ("[]", False),
        ("{", False),
    ],
)
def test_settings_json은_env_키가_없는_JSON_객체여야_지난다(text: str | None, *, ok: bool) -> None:
    assert (settings_env_problem(text) is None) is ok


def test_세션_환경에_설정_폴더가_없으면_회차를_열지_않는다(tmp_path: Path) -> None:
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CONFIG_DIR"}
    got = before_round(fake.claude(), env=env, cwd=tmp_path, account=ACCOUNT)
    assert got is not None and got.end is None


def test_auth_status가_시간을_넘기면_까닭을_낸다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(rerun_checks, "AUTH_TIMEOUT", 0.5)
    sleeper = [sys.executable, "-c", "import time; time.sleep(30)"]
    started = time.monotonic()
    got = before_round(sleeper, env=_env(tmp_path), cwd=tmp_path, account=ACCOUNT)
    assert got is not None and got.end is None and time.monotonic() - started < 25


# --- init 의 설정 ---


def _builtin(name: str) -> Json:
    return {"name": name, "path": "builtin", "source": f"{name}@builtin"}


ALLOWED = frozenset({*(f"{p}@builtin" for p in BUILTIN_PLUGINS), PYRIGHT})


@pytest.mark.parametrize(
    ("plugins", "servers", "ok"),
    [
        ([_builtin(p) for p in BUILTIN_PLUGINS], [], True),
        ([], [], True),
        ([{"name": "pyright-lsp", "source": PYRIGHT}], [], True),
        ([_builtin("cc-plugin-agents-md")], [{"name": "github", "status": "connected"}], False),
        ([{"name": "github", "source": "github@claude-plugins-official"}], [], False),
        ([{"name": "pyright-lsp", "source": "pyright-lsp@다른-마켓"}], [], False),
        ([_builtin("cc-plugin-다른-것")], [], False),
        (["cc-plugin-telemetry"], [], True),  # 글만 든 항목은 이름으로 견준다
        ([3], [], False),
    ],
)
def test_init은_빈_mcp_servers와_허용_모임_안의_플러그인만_지난다(
    plugins: list[Json], servers: list[Json], *, ok: bool
) -> None:
    event: dict[str, Json] = {
        "type": "system",
        "subtype": "init",
        "plugins": plugins,
        "mcp_servers": servers,
    }
    assert init_problem(event, ALLOWED) is not ok


def test_칸이_목록이_아닌_init은_허용_밖이다() -> None:
    assert init_problem({"type": "system", "subtype": "init", "plugins": []}, ALLOWED)
    assert init_problem({"type": "system", "subtype": "init", "mcp_servers": []}, ALLOWED)


def test_source가_없는_플러그인은_이름을_허용_키의_골뱅이_앞과_견준다() -> None:
    """못 보는 것: 마켓 플러그인이 init 에 실리는 꼴은 재지 않았다. `source`가 없으면 이름만
    견주어, 다른 마켓의 같은 이름 플러그인을 지나보낸다."""
    event: dict[str, Json] = {
        "type": "system",
        "subtype": "init",
        "plugins": [{"name": "pyright-lsp"}],
        "mcp_servers": [],
    }
    assert not init_problem(event, ALLOWED)


def test_허용_모임은_내장_셋과_클론의_settings_json이_켠_플러그인이다(tmp_path: Path) -> None:
    room = _room(tmp_path, settings={"enabledPlugins": {PYRIGHT: True, "x@y": False, "z@w": 1}})
    assert allowed_plugins(room.place.clone) == ALLOWED
    assert enabled_plugins(None) == () and enabled_plugins("{") == ()
    assert enabled_plugins('{"enabledPlugins": []}') == ()


def test_이_저장소의_프로젝트_설정이_켠_플러그인은_pyright_lsp_하나다() -> None:
    text = (ROOT / ".claude" / "settings.json").read_text(encoding="utf-8")
    assert enabled_plugins(text) == (PYRIGHT,)


def test_허용_밖_init을_받으면_그_줄에서_호출을_끄고_측정_아님_설정이다(tmp_path: Path) -> None:
    room = _room(tmp_path, git=True)
    other: Json = {"name": "github", "path": "x", "source": "github@claude-plugins-official"}
    fake.write_script(
        room.config,
        calls=[fake.call([fake.init_event(extra_plugins=[other])], child=600, hang=600)],
    )
    started = time.monotonic()

    got, _ = _run(room, ids=[S1])

    assert time.monotonic() - started < 300, "init 에서 끄지 않고 기다렸다"
    assert got.end == End(END_NOT_MEASURED, REASON_SETTINGS, None)
    [run] = got.runs
    assert run.launched.drove.stop is Stop.HALTED_KILLED
    [call] = fake.read_calls(room.config)
    [child] = fake.read_children(room.config)
    assert _gone(_pid(call), S1) and _gone(_pid(child), S1)
    assert session_record(S1, got.runs, room.config).runner_killed


def test_둘째_호출의_init도_허용_모임과_견준다(tmp_path: Path) -> None:
    room = _room(tmp_path)
    screen = room.screen()
    assert screen(_launched([fake.init_event(), fake.result_event(0.1, "글")])) is None
    later = fake.init_event(mcp_servers=["github"])
    assert screen(_launched([later], session_id=S2)) == End(END_NOT_MEASURED, REASON_SETTINGS, None)
    assert screen.watch(_line(later)) and not screen.watch(_line(fake.init_event()))
    assert not screen.watch("init 이 아닌 줄\n")


# --- 모델 ---


@pytest.mark.parametrize(
    ("value", "want"),
    [
        (None, OPUS),
        ("", OPUS),
        ("inherit", OPUS),
        ("sonnet", SONNET),
        ("Haiku", HAIKU),
        ("opus", OPUS),
        (" claude-sonnet-5-5 ", SONNET),
        ("claude-haiku-4-5", "claude-haiku-4-5"),
        ("<synthetic>", None),
        ("빠른 것", None),
        (3, None),
    ],
)
def test_별칭과_inherit와_빈_값은_전체_이름으로_푼다(value: Json, want: str | None) -> None:
    assert resolve_model(value, ARM) == want


@pytest.mark.parametrize(
    ("text", "want"),
    [
        ("---\nname: x\nmodel: sonnet\n---\n본문 model: opus\n", "sonnet"),
        ("---\r\nmodel: 'haiku'\r\n---\r\n", "haiku"),
        ('\ufeff---\nmodel: "inherit"\n---\n', "inherit"),
        ("---\nname: x\n---\nmodel: opus\n", None),  # 머리말 밖
        ("model: opus\n", None),
    ],
)
def test_에이전트_파일은_머리말의_model_값을_읽는다(text: str, want: str | None) -> None:
    assert agent_model(text) == want


def test_하네스_모델은_클론의_에이전트_파일과_code_review의_sonnet이다(tmp_path: Path) -> None:
    room = _room(
        tmp_path,
        agents={
            "a.md": "---\nname: a\nmodel: haiku\n---\n",
            "b.md": "---\nname: b\n---\n",  # 모델이 없으면 갈래의 모델로 돈다
            "c.txt": "---\nmodel: claude-x-1\n---\n",
        },
    )
    assert harness_models(room.place.clone, ARM) == frozenset({HAIKU, OPUS, SONNET})


def test_이_저장소의_code_review는_표준_축에_sonnet을_준다() -> None:
    skill = (ROOT / ".claude" / "skills" / "code-review" / "SKILL.md").read_text(encoding="utf-8")
    assert f"`model: {CODE_REVIEW_MODEL}`" in skill


def test_본_세션은_synthetic을_뺀_줄이_모두_갈래의_모델과_노력이어야_한다() -> None:
    main = (
        LineCount(OPUS, "xhigh", 5),
        LineCount("<synthetic>", None, 1),
        LineCount("<synthetic>", "xhigh", 1),
    )
    assert model_mismatch(main, (), arm=ARM, allowed=()) == ()
    off = (
        *main,
        LineCount(OPUS, "high", 2),
        LineCount(SONNET, "xhigh", 1),
        LineCount(OPUS, None, 1),
    )
    assert model_mismatch(off, (), arm=ARM, allowed=()) == (
        LineCount(OPUS, None, 1),
        LineCount(OPUS, "high", 2),
        LineCount(SONNET, "xhigh", 1),
    )


def test_서브에이전트는_허용_모임_밖의_모델만_세고_노력은_보지_않는다() -> None:
    side = (
        LineCount(OPUS, "low", 3),  # 갈래의 모델. 노력은 보지 않는다
        LineCount(HAIKU, "low", 2),
        LineCount(HAIKU, None, 1),
        LineCount(SONNET, "high", 4),
        LineCount(SYNTHETIC, None, 5),  # 응답이 아닌 줄은 세지 않는다
    )
    assert model_mismatch((), side, arm=ARM, allowed={SONNET}) == (LineCount(HAIKU, None, 3),)
    assert model_mismatch((), side, arm=ARM, allowed={SONNET, HAIKU}) == ()


def test_Agent_입력으로_고른_모델의_서브에이전트는_지난다(tmp_path: Path) -> None:
    room = _room(tmp_path)
    _transcript(
        room.config,
        S1,
        _arm_lines(2),
        {"a": [fake.transcript_line(HAIKU, "low"), fake.synthetic_line()]},
    )
    chose = _use("Agent", {"description": "x", "prompt": "y", "model": "haiku"}, "toolu_a")

    screen = room.screen()
    assert screen(_launched([fake.init_event(), chose])) is None
    assert screen.findings().model_mismatch == ()


def test_Agent_입력으로_고른_모델은_그_세션의_서브에이전트만_지난다(tmp_path: Path) -> None:
    # 티켓 09: "그 세션이 Agent 도구 입력의 `model`로 직접 고른 모델". 인계 뒤 세션은 앞 세션이
    # 고른 모델을 물려받지 않는다
    room = _room(tmp_path)
    _transcript(room.config, S1, _arm_lines(1), {"a": [fake.transcript_line(HAIKU, "low")]})
    _transcript(room.config, S2, _arm_lines(1), {"b": [fake.transcript_line(HAIKU, "low")]})
    chose = _use("Agent", {"description": "x", "prompt": "y", "model": "haiku"}, "toolu_a")
    screen = room.screen()

    assert screen(_launched([fake.init_event(), chose], session_id=S1)) is None
    got = screen(_launched([fake.init_event()], session_id=S2))

    assert got == End(END_NOT_MEASURED, REASON_MODEL, None)
    assert screen.findings().model_mismatch == (LineCount(HAIKU, None, 1),)


def test_하네스와_갈래_밖의_서브에이전트_모델이나_다른_노력은_측정_아님_모델과_줄_수다(
    tmp_path: Path,
) -> None:
    # 못 보는 것: 내장 에이전트를 `model` 없이 불러 허용 밖의 모델(haiku)로 돈 줄도
    # 건다(거짓 양성 쪽)
    room = _room(tmp_path)
    _transcript(
        room.config,
        S1,
        [*_arm_lines(2), fake.transcript_line(OPUS, "high")],
        {"a": [fake.transcript_line(HAIKU, "low"), fake.transcript_line(HAIKU, "low", "m2")]},
    )
    screen = room.screen()

    assert screen(_launched([fake.init_event()])) == End(END_NOT_MEASURED, REASON_MODEL, None)
    assert screen.findings().model_mismatch == (
        LineCount(HAIKU, None, 2),
        LineCount(OPUS, "high", 1),
    )


def test_하네스_에이전트의_모델은_지난다(tmp_path: Path) -> None:
    room = _room(tmp_path, agents={"r.md": "---\nname: r\nmodel: haiku\n---\n"})
    _transcript(room.config, S1, _arm_lines(1), {"r": [fake.transcript_line(HAIKU, "high")]})
    assert room.screen()(_launched([fake.init_event()])) is None


# --- 오염: 셸 명령 ---


@pytest.mark.parametrize(
    ("command", "want"),
    [
        ("xargs gh pr list", (GH_WORD,)),
        ('bash -c "gh api repos"', (GH_WORD,)),
        ("GH api user", (GH_WORD,)),
        (
            'uv run python - <<\'EOF\'\nimport subprocess\nsubprocess.run(["gh", "api", "x"])\nEOF',
            (GH_WORD,),
        ),
        ("bash <<'EOF'\ngh api user\nEOF", (GH_WORD,)),
        ("git log --oneline | grep 'high '", ()),
        ("ls tools/gh_run_summary.py", ()),  # 뒤가 낱말 글자다
        ("echo high-level", ()),
        ("curl https://github.com/x", (GITHUB,)),
        ("curl https://raw.githubusercontent.com/x", (GITHUBUSERCONTENT,)),
        ("git clone NJH6803/Agent-OS", (REPOSITORY,)),
        ("gh repo view njh6803/agent-os", (REPOSITORY, GH_WORD)),
        ("pwsh -File tools/open_session.ps1", (OPEN_SESSION_SCRIPT,)),
        ("start claude://open?x", (CLAUDE_LINK,)),
        ("git commit -m 'see github.com'", (GITHUB,)),  # 주소는 메시지도 본다
    ],
)
def test_셸_명령에서_주소와_낱말_gh와_세션을_여는_꼴을_찾는다(
    command: str, want: tuple[str, ...]
) -> None:
    assert command_patterns(command) == want


@pytest.mark.parametrize(
    "command",
    [
        "git commit -m 'gh 호출을 고친다'",
        "git commit -m x -m 'uses gh'",  # -m 여럿
        "git commit -am 'gh'",  # 붙인 옵션
        "git commit -m'fix gh'",  # 붙인 값
        "git commit --message='fix gh'",
        "git commit --message 'fix gh'",
        "git commit --mes 'fix gh'",  # 긴 옵션의 줄임
        "git -C sub -c user.name=x commit -m 'gh'",
        "GIT_AUTHOR_NAME=x git commit -m 'gh'",
        "git commit -Fmsg.txt -m 'gh'",  # -F <파일>의 값은 파일이다
        "git commit -F - <<'EOF'\nfix gh\nEOF",
        "git commit -F - <<EOF\nfix gh\nEOF",
        "git commit --file=- <<'EOF'\nfix gh\nEOF",
        "git commit -F- <<-'EOF'\n\tfix gh\n\tEOF",
        "git commit -m \"$(cat <<'EOF'\nfix gh\n\nCo-Authored-By: x\nEOF\n)\"",
        "git add . && git commit -m \"$(cat <<'EOF'\nfix gh\nEOF\n)\" && git log -1",
        'git commit -m "$(cat <<EOF\nfix gh\nEOF\n)"',  # 따옴표 없는 구분자도 치환이 없으면
        "git commit -m @'\nfix gh\n'@",  # PowerShell here-string 도 따옴표로 읽힌다
        "{ git commit -m 'gh'; }",  # 명령 앞의 셸 예약어
        "if git commit -m 'gh'; then echo ok; fi",
        "! git commit -m gh",
        "time GIT_AUTHOR_NAME=x git commit -m gh",
    ],
)
def test_git_commit의_메시지_안의_gh는_걸리지_않는다(command: str) -> None:
    assert GH_WORD not in command_patterns(command)


@pytest.mark.parametrize(
    "command",
    [
        "git commit -m x && gh pr create",
        "git commit -m x -- gh",  # `--` 뒤는 경로다
        "git commit -- -m gh",  # `--` 뒤의 `-m`도 경로다
        "git commit -F -m gh",  # -F 의 값이 `-m`이고 gh 는 경로다
        'git commit -m "$(gh api user)"',  # 명령 치환은 돈다
        "git commit -F - <<EOF\n$(gh api user)\nEOF",  # 따옴표 없는 구분자의 본문은 치환이 돈다
        'git commit -m "$(cat <<EOF\n$(gh api user)\nEOF\n)"',
        "git commit -m 'gh",  # 짝 없는 따옴표는 떼지 않고 본다
        "git push gh main",
    ],
)
def test_메시지가_아니거나_명령이_되는_gh는_걸린다(command: str) -> None:
    assert GH_WORD in command_patterns(command)


@pytest.mark.parametrize(
    "command",
    [
        "cat <<'EOF' | git commit -F -\nfix gh\nEOF",  # heredoc 이 앞 명령(`cat`)의 것이다
        "echo 'fix gh' | git commit -F -",  # 다른 명령의 출력을 파이프로 받았다
        "git commit -F - <<< 'fix gh'",  # here-string
        "git commit -m '$(gh)'",  # 따옴표를 벗긴 뒤 보므로 작은따옴표 안의 `$(`도 치환으로 읽는다
        "env git commit -m 'fix gh'",  # 명령 앞의 래퍼
        "command git commit -m 'fix gh'",
    ],
)
def test_떼기가_나열한_길_밖으로_넘긴_메시지는_떼지_않는다(command: str) -> None:
    """못 보는 것(거짓 양성): 모듈 독스트링의 커밋 메시지 떼기가 나열한 길 밖의 메시지다."""
    assert GH_WORD in command_patterns(command)


# --- 오염: 경로 ---

W = watched_from(
    main_checkout=["C:\\project\\agent"],
    home=["C:\\Users\\User"],
    user_claude=["C:\\Users\\User\\.claude"],
    root=["D:\\rerun"],
    round_name="rerun-x-03-a-1-t1",
    config=["D:\\cfg"],
)
# 설정 폴더와 뿌리가 홈 아래에 있는 자리
UNDER_HOME = watched_from(
    main_checkout=["C:\\project\\agent"],
    home=["C:\\Users\\User"],
    user_claude=["C:\\Users\\User\\.claude"],
    root=["C:\\Users\\User\\rerun"],
    round_name="rerun-x-03-a-1-t1",
    config=["C:\\Users\\User\\.claude-rerun"],
)


@pytest.mark.parametrize(
    ("text", "want"),
    [
        ("C:\\project\\agent\\tools\\x.py", (MAIN_CHECKOUT,)),
        ("c:/PROJECT/agent", (MAIN_CHECKOUT,)),
        ("/c/project/agent/x", (MAIN_CHECKOUT,)),
        ("cat '/c/Project/Agent'", (MAIN_CHECKOUT,)),
        ("ls C:/project/agent;ls", (MAIN_CHECKOUT,)),
        ("C://project//agent/x", (MAIN_CHECKOUT,)),
        ("C:/project/agent-rerun/x", ()),
        ("C:/project/agent.git", ()),
        ("C:\\Users\\User\\.claude\\settings.json", (USER_CLAUDE,)),
        ("/c/users/user/.claude", (USER_CLAUDE,)),
        ("cat ~/.claude/projects/x.jsonl", (USER_CLAUDE,)),
        ('ls "$HOME/.claude"', (USER_CLAUDE,)),
        ("type %USERPROFILE%\\.claude\\x", (USER_CLAUDE,)),
        ("gci $env:USERPROFILE\\.claude", (USER_CLAUDE,)),
        ("cat ~/.claude-rerun/x", ()),
        ("cat ~/.claude.json", ()),
        ("cat ~/.claude{,.bak}/settings.json", (USER_CLAUDE,)),  # 중괄호 확장
        ("cat ${X:-~/.claude}/settings.json", (USER_CLAUDE,)),
        ("cat ~/.claude[a]", ()),  # 대괄호 glob 은 한 글자에 맞아 이웃 이름(`~/.claudea`)이다
        ("D:/rerun/rerun-x-03-a-1-t1/clone/x.py", ()),  # 자기 회차 폴더
        ("D:/rerun/rerun-x-03-b-1-t2/clone/x.py", (OTHER_ROUND,)),
        ("ls D:\\rerun", (OTHER_ROUND,)),
        ("ls D:/rerun/*/stream", (OTHER_ROUND,)),
        ("D:/rerun/rerun-x-03-a-1-t1-x/y", (OTHER_ROUND,)),
        ("D:/rerun-old/x", ()),
        ("D:/cfg/projects/own-slug/memory/MEMORY.md", ()),  # 자기 세션 기록 폴더
        ("D:/cfg/projects/other-slug/x.jsonl", (CONFIG_FOLDER,)),
        ("D:/cfg/projects", (CONFIG_FOLDER,)),
        ("D:/cfg/settings.json", (CONFIG_FOLDER,)),
        ("cat $CLAUDE_CONFIG_DIR/projects/x/y.jsonl", (CONFIG_FOLDER,)),
    ],
)
def test_경로는_대소문자와_구분자를_가리지_않고_조각_경계로_견준다(
    text: str, want: tuple[str, ...]
) -> None:
    assert path_patterns(text, W, own_slugs=frozenset({SLUG})) == want


@pytest.mark.parametrize(
    ("text", "want"),
    [
        ("ls ~/.claude-rerun/projects", (CONFIG_FOLDER,)),
        ('ls "$HOME/.claude-rerun/projects/other-slug"', (CONFIG_FOLDER,)),
        ("cat ~/.claude-rerun/projects/own-slug/memory/MEMORY.md", ()),  # 자기 세션 기록 폴더
        ("cat %USERPROFILE%\\rerun\\rerun-x-03-b-1-t2\\stream", (OTHER_ROUND,)),
        ("cat ~/rerun/rerun-x-03-a-1-t1/clone/x.py", ()),  # 자기 회차 폴더
        ("cat ~/.claude/x", (USER_CLAUDE,)),
    ],
)
def test_홈_아래의_찾는_경로는_홈을_대신하는_이름으로_적은_꼴도_본다(
    text: str, want: tuple[str, ...]
) -> None:
    assert path_patterns(text, UNDER_HOME, own_slugs=frozenset({SLUG})) == want


def test_셸이_풀어야_나오는_경로는_보지_않는다() -> None:
    """못 보는 것(거짓 음성): 대신하는 이름으로 적은 꼴 밖의 변수, glob, 절대 경로 안의 `..`는
    풀지 않는다."""
    assert path_patterns("d=~; cat $d/.claude/x", W) == ()
    assert path_patterns("cat ~/.cl*/settings.json", W) == ()
    assert path_patterns("cat D:/rerun/rerun-x-03-a-1-t1/../rerun-x-03-b-1-t2/x", W) == ()


def test_절대_경로_안의_점_조각은_정리하지_않아_다른_회차로_걸린다() -> None:
    """못 보는 것(거짓 양성): `<뿌리>/./<자기 회차>`의 `.`를 회차 폴더 이름으로 읽는다."""
    assert path_patterns("cat D:/rerun/./rerun-x-03-a-1-t1/x", W) == (OTHER_ROUND,)


def _link(link: Path, target: Path) -> None:
    """`link`에 `target` 폴더를 가리키는 링크를 만든다. 윈도는 권한 없이 만들 수 있는 junction
    이다."""
    if sys.platform == "win32":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            check=True,
            capture_output=True,
            timeout=60,
        )
    else:
        link.symlink_to(target, target_is_directory=True)


def test_링크를_푼_꼴도_찾는다(tmp_path: Path) -> None:
    room = _room(tmp_path)
    _link(tmp_path / "링크", room.main)
    watched = watched_paths(
        main_checkout=tmp_path / "링크", home=room.home, place=room.place, config_dir=room.config
    )
    real = Path(os.path.realpath(room.main))
    assert path_patterns(str(real / "x.py"), watched) == (MAIN_CHECKOUT,)
    assert path_patterns(str(tmp_path / "링크" / "x.py"), watched) == (MAIN_CHECKOUT,)


def test_경로_칸의_상대_경로는_클론에서_풀어_보고_셸의_상대_경로는_풀지_않는다(
    tmp_path: Path,
) -> None:
    room = _room(tmp_path)
    other = create_round_dir(tmp_path / "뿌리", TASK.task_id, "B", 1, token="t2")
    rel = f"../../{other.name}/clone/x.py"
    assert _hits(room, _use("Read", {"file_path": rel})) == (Hit(OTHER_ROUND, "Read"),)
    # 못 보는 것(거짓 음성): 셸 명령의 상대 경로는 작업 폴더를 모른다
    assert _hits(room, _use("Bash", {"command": f"cat {rel}"})) == ()


# --- 오염: 도구마다 ---


def test_모든_도구_입력의_경로_값을_보고_글_칸은_보지_않는다(tmp_path: Path) -> None:
    room = _room(tmp_path)
    main = str(room.main)
    claude = str(room.home / ".claude")
    assert _hits(
        room,
        _use("Read", {"file_path": f"{main}/x.py"}, "t1"),
        _use("Glob", {"pattern": "**/*.md", "path": claude}, "t2"),
        _use("Grep", {"pattern": main, "path": "."}, "t3"),  # 찾는 글은 경로가 아니다
        _use("Agent", {"description": main, "prompt": f"{main} 을 읽어라"}, "t4"),
        _use("Edit", {"file_path": "a.py", "old_string": main, "new_string": main}, "t5"),
        _use("Bash", {"command": "ls", "description": main}, "t6"),
    ) == (Hit(MAIN_CHECKOUT, "Read"), Hit(USER_CLAUDE, "Glob"))


def test_막은_바깥_도구와_open_session_스킬을_찾는다(tmp_path: Path) -> None:
    room = _room(tmp_path)
    assert _hits(
        room,
        _use("WebFetch", {"url": "https://example.com", "prompt": "x"}, "t1"),
        _use("SendMessage", {"to": "x", "message": "y"}, "t2"),
        _use("Skill", {"skill": "open-session"}, "t3"),
        _use("Skill", {"skill": "/open-session"}, "t4"),
        _use("Skill", {"skill": ".claude/worktrees/x:open-session"}, "t5"),
        _use("Skill", {"skill": "implement", "args": "x"}, "t6"),
    ) == (
        Hit(BLOCKED_TOOL, "WebFetch"),
        Hit(BLOCKED_TOOL, "SendMessage"),
        Hit(OPEN_SESSION_SKILL, "Skill"),
    )


@pytest.mark.parametrize(
    ("skill", "hit"),
    [
        ("open-session", True),
        ("/open-session", True),
        (".claude/worktrees/x:open-session", True),  # 워크트리 세션이 부르는 이름
        (" Open-Session ", True),
        ("open-session-x", False),
        ("implement", False),
    ],
)
def test_Skill_이름은_앞의_슬래시와_콜론_앞을_떼고_견준다(
    tmp_path: Path, skill: str, *, hit: bool
) -> None:
    got = _hits(_room(tmp_path), _use("Skill", {"skill": skill}))
    assert got == ((Hit(OPEN_SESSION_SKILL, "Skill"),) if hit else ())


SIX = {
    "url": "https://github.com/x https://raw.githubusercontent.com/njh6803/agent-os/x",
    "prompt": "gh 로 open_session.ps1 과 claude://open 을 찾는다",
}
SIX_HITS = (GITHUB, GITHUBUSERCONTENT, REPOSITORY, GH_WORD, OPEN_SESSION_SCRIPT, CLAUDE_LINK)


def test_웹_도구의_입력은_여섯_꼴을_모두_찾는다(tmp_path: Path) -> None:
    room = _room(tmp_path)
    got = _hits(room, _use("WebFetch", SIX))
    assert got == tuple(Hit(p, "WebFetch") for p in (BLOCKED_TOOL, *SIX_HITS))


def test_Monitor의_웹소켓_입력은_웹_도구처럼_여섯_꼴을_찾는다(tmp_path: Path) -> None:
    room = _room(tmp_path)
    ws: dict[str, Json] = {"url": SIX["url"], "protocols": [SIX["prompt"]]}
    got = _hits(room, _use("Monitor", {"ws": ws, "description": "x", "timeout_ms": 1000}))
    assert got == tuple(Hit(p, "Monitor") for p in SIX_HITS)


@pytest.mark.parametrize(
    ("tool", "target", "hit"),
    [
        ("Write", "tools/x.py", True),
        ("Write", "docs/journal/x.md", False),
        ("Write", "README.MD", False),
        ("Write", "tests/tools/test_x.py", False),
        ("Write", "{clone}/tests/x.py", False),
        ("Write", "{clone}/tools/x.py", True),
        ("Write", "{bash_clone}/tests/x.py", False),  # Git Bash 의 `/c/` 꼴
        ("Write", "{bash_clone}/tools/x.py", True),
        ("Write", "tests/../tools/x.py", True),
        ("Write", "../outside.py", True),  # 클론 밖
        ("Edit", "tools/x.py", True),
        ("NotebookEdit", "tools/x.ipynb", True),
        ("NotebookEdit", "tests/x.ipynb", False),
    ],
)
def test_쓰기_내용은_md도_tests도_아닐_때만_주소_셋을_찾는다(
    tmp_path: Path, tool: str, target: str, *, hit: bool
) -> None:
    room = _room(tmp_path)
    clone = str(room.place.clone).replace("\\", "/")
    drive = clone[:2]  # 리눅스에서는 드라이브가 없어 `/c/` 꼴이 없으니 그대로 둔다
    bash_clone = f"/{drive[0].lower()}{clone[2:]}" if drive[1:] == ":" else clone
    target = target.replace("{clone}", clone).replace("{bash_clone}", bash_clone)
    body = "url = 'https://github.com/x'  # gh 를 부른다"
    inputs: dict[str, dict[str, Json]] = {
        "Write": {"file_path": target, "content": body},
        "Edit": {"file_path": target, "old_string": "a", "new_string": body},
        "NotebookEdit": {"notebook_path": target, "new_source": body},
    }
    assert _hits(room, _use(tool, inputs[tool])) == ((Hit(GITHUB, tool),) if hit else ())


def test_서브에이전트의_도구_입력도_보고_거부된_호출은_빼고_거부_수로_센다(tmp_path: Path) -> None:
    room = _room(tmp_path)
    screen = room.screen()
    first = _use("Bash", {"command": "gh --version"}, "toolu_a")
    second = _use("Bash", {"command": "gh api user"}, "toolu_b", parent="toolu_p")
    side = _use("Bash", {"command": "curl https://github.com/x"}, "toolu_c", parent="toolu_p")
    events: list[Json] = [
        fake.init_event(),
        first,
        second,
        side,
        fake.result_event(0.1, None, denials=[fake.denial("Bash", "toolu_a", {"command": "x"})]),
        fake.result_event(0.2, "글", denials=[fake.denial("Bash", "toolu_b", {"command": "x"})]),
    ]

    end = screen(_launched(events))

    assert end == End(END_NOT_MEASURED, REASON_CONTAMINATION, None)
    found = screen.findings()
    assert found.contamination == (Hit(GITHUB, "Bash"),)
    assert found.denied_calls == 2


def test_거부만_있으면_오염이_아니다(tmp_path: Path) -> None:
    room = _room(tmp_path)
    screen = room.screen()
    use = _use("Bash", {"command": "git push origin main"}, "toolu_a")
    denied = fake.denial("Bash", "toolu_a", {"command": "git push origin main"})
    end = screen(
        _launched([fake.init_event(), use, fake.result_event(0.1, "글", denials=[denied])])
    )
    assert end is None and screen.findings().denied_calls == 1


def test_도구_이름은_init_목록이나_아는_이름일_때만_옮긴다(tmp_path: Path) -> None:
    room = _room(tmp_path)
    main = str(room.main)
    assert _hits(
        room,
        _use("mcp__x__read", {"path": main}, "t1"),
        _use("Read", {"file_path": main}, "t2"),
    ) == (Hit(MAIN_CHECKOUT, UNKNOWN_TOOL), Hit(MAIN_CHECKOUT, "Read"))
    screen = room.screen()
    screen(
        _launched(
            [
                fake.init_event(tools=[*fake.TOOLS, "mcp__x__read"]),
                _use("mcp__x__read", {"path": main}),
            ]
        )
    )
    assert screen.findings().contamination == (Hit(MAIN_CHECKOUT, "mcp__x__read"),)


def test_꼴_이름은_이름이_있는_상수이고_서로_다르다() -> None:
    named = {
        *SIX_HITS,
        MAIN_CHECKOUT,
        USER_CLAUDE,
        OTHER_ROUND,
        CONFIG_FOLDER,
        BLOCKED_TOOL,
        OPEN_SESSION_SKILL,
    }
    assert len(PATTERN_NAMES) == len(named) and set(PATTERN_NAMES) == named


def test_기록에는_꼴_이름과_도구_이름만_남고_입력의_글은_남지_않는다(tmp_path: Path) -> None:
    room = _room(tmp_path)
    secret = "SECRET-xyz-7"
    main = str(room.main)
    nasty = [
        _use("Bash", {"command": f'echo "$(cat {secret})" && gh api {secret}'}, "t1"),
        _use("Bash", {"command": f"cat <<'EOF'\n{secret} github.com\nEOF\ncat {main}"}, "t2"),
        _use("PowerShell", {"command": f"$x = @'\n{secret}\n'@; gh `\n {secret}"}, "t3"),
        _use("Write", {"file_path": "x.py", "content": f"'{secret}' github.com"}, "t4"),
        _use("Read", {"file_path": f"{main}/{secret}"}, "t5"),
        _use("Skill", {"skill": "open-session", "args": secret}, "t6"),
    ]
    screen = room.screen()
    launched = _launched([fake.init_event(), *nasty, fake.result_event(0.1, secret)])
    end = screen(launched)
    found = screen.findings()
    assert end is not None and found.contamination
    record = round_record(
        room.place,
        room.task,
        condition_version=1,
        claude_version=None,
        account=ACCOUNT,
        env={},
        continued=Continued(
            runs=(CallRun("첫", launched, has_directive=False, ends_with_question=False),),
            handoffs=0,
            interventions=0,
            asked_at_end=False,
            end=end,
        ),
        config_dir=room.config,
        outcome=outcome_of(pick_result_commit({}, room.task.branch)),
        wall_clock_from=0.0,
        now=1.0,
        elsewhere=Elsewhere(
            official_usd=0.0,
            tokens=Tokens(
                input=None, output=None, cache_read=None, cache_write=None, thinking=None
            ),
            substitutes=(),
            denied_calls=found.denied_calls,
            utilization_start=found.utilization_start,
            utilization_end=found.utilization_end,
            contamination=found.contamination,
            model_mismatch=found.model_mismatch,
        ),
    )
    records = tmp_path / "records"
    records.mkdir()
    written = write_record(records, record)
    assert secret not in written.read_text(encoding="utf-8")
    assert {h.pattern for h in read_record(written).spend.contamination} <= set(PATTERN_NAMES)


# --- 한도 ---


def _rejected(resets: Json = 1792962000, *, drop: bool = False) -> dict[str, Json]:
    event = fake.rate_limit_event("rejected")
    info = event["rate_limit_info"]
    assert isinstance(info, dict)
    if drop:
        del info["resetsAt"]
    else:
        info["resetsAt"] = resets
    return event


@pytest.mark.parametrize(
    ("events", "want"),
    [
        ([_rejected()], Limit(1792962000)),
        ([_rejected(1792962000.2)], Limit(1792962001)),
        ([_rejected(None)], Limit(None)),
        ([_rejected(drop=True)], Limit(None)),
        ([_rejected("1792962000")], Limit(None)),
        ([_rejected(resets=True)], Limit(None)),
        ([_rejected(1e300)], Limit(None)),
        ([_rejected(-5)], Limit(None)),
        ([fake.limit_result()], Limit(None)),  # api_error 만 있으면 시각을 모른다
        ([fake.limit_result(), _rejected()], Limit(1792962000)),
        ([_rejected(100), _rejected(200)], Limit(200)),
        ([_rejected(100), _rejected(None)], Limit(None)),
        ([fake.rate_limit_event("allowed_warning")], None),
        ([fake.rate_limit_event("allowed")], None),
        ([], None),
    ],
)
def test_한도_표지는_거절과_usage_limit_reached이고_읽지_못한_시각은_비운다(
    events: list[dict[str, Json]], want: Limit | None
) -> None:
    assert limit_of(events) == want


def test_사용률은_창마다_읽고_창이_없으면_한도의_종류로_읽는다() -> None:
    assert windows_of(fake.rate_limit_event(five_hour=0.2, seven_day=0.9)) == (
        Window("five_hour", 0.2),
        Window("seven_day", 0.9),
    )
    bare: dict[str, Json] = {
        "type": "rate_limit_event",
        "rate_limit_info": {"rateLimitType": "seven_day", "utilization": 0.5},
    }
    assert windows_of(bare) == (Window("seven_day", 0.5),)
    odd: dict[str, Json] = {
        "type": "rate_limit_event",
        "rate_limit_info": {
            "unifiedWindows": {"Five Hour": {"utilization": 0.1}, "x": {"utilization": "0.2"}},
            "rateLimitType": "seven_day",
            "utilization": True,
        },
    }
    assert windows_of(odd) == ()
    assert windows_of(fake.init_event()) == ()


def test_회차의_첫과_끝의_사용률을_창마다_적고_경고는_기록만_한다(tmp_path: Path) -> None:
    room = _room(tmp_path)
    screen = room.screen()
    first = fake.rate_limit_event("allowed_warning", five_hour=0.1, seven_day=0.97)
    middle = fake.rate_limit_event("allowed_warning", five_hour=0.2, seven_day=0.98)
    last = fake.rate_limit_event("allowed", five_hour=0.3, seven_day=0.99)
    assert screen(_launched([fake.init_event(), first, middle])) is None
    assert screen(_launched([last], session_id=S2)) is None
    found = screen.findings()
    assert found.utilization_start == (Window("five_hour", 0.1), Window("seven_day", 0.97))
    assert found.utilization_end == (Window("five_hour", 0.3), Window("seven_day", 0.99))


def test_한도가_든_호출은_결과가_없어도_측정_아님_한도와_풀리는_시각이다(tmp_path: Path) -> None:
    room = _room(tmp_path, git=True)
    fake.write_script(
        room.config,
        calls=[
            fake.call([fake.init_event(), fake.rate_limit_event("rejected", resets_at=1792962000)])
        ],
    )
    got, _ = _run(room, ids=[S1])
    assert got.end == End(END_NOT_MEASURED, REASON_LIMIT, 1792962000)


def test_결과의_api_error만_있는_한도는_풀리는_시각을_비운다(tmp_path: Path) -> None:
    room = _room(tmp_path, git=True)
    fake.write_script(room.config, calls=[fake.call([fake.init_event(), fake.limit_result()])])
    got, _ = _run(room, ids=[S1])
    assert got.end == End(END_NOT_MEASURED, REASON_LIMIT, None)


# --- 끝의 차례와 이유 ---


def test_끝의_이유는_기록이_받는_이유다() -> None:
    for reason in (REASON_SETTINGS, REASON_MODEL, REASON_CONTAMINATION, REASON_LIMIT):
        assert reason in NOT_MEASURED_REASONS


def test_여럿이_걸리면_설정_모델_오염_한도의_차례로_끝을_낸다(tmp_path: Path) -> None:
    room = _room(tmp_path)
    _transcript(room.config, S1, [fake.transcript_line(OPUS, "low")])
    bad_init = fake.init_event(mcp_servers=["github"])
    dirty = _use("Bash", {"command": "gh api"})
    limit = fake.rate_limit_event("rejected")
    assert room.screen()(_launched([bad_init, dirty, limit])) == End(
        END_NOT_MEASURED, REASON_SETTINGS, None
    )
    assert room.screen()(_launched([fake.init_event(), dirty, limit])) == End(
        END_NOT_MEASURED, REASON_MODEL, None
    )
    _transcript(room.config, S1, _arm_lines(1))
    assert room.screen()(_launched([fake.init_event(), dirty, limit])) == End(
        END_NOT_MEASURED, REASON_CONTAMINATION, None
    )
    assert room.screen()(_launched([fake.init_event(), limit])) == End(
        END_NOT_MEASURED, REASON_LIMIT, 1792962000
    )


def test_screen_for는_클론의_설정과_에이전트_파일을_읽고_뿌리와_설정_폴더를_본다(
    tmp_path: Path,
) -> None:
    room = _room(
        tmp_path,
        settings={"enabledPlugins": {PYRIGHT: True}},
        agents={"r.md": "---\nmodel: haiku\n---\n"},
    )
    watched: Watched = watched_paths(
        main_checkout=room.main, home=room.home, place=room.place, config_dir=room.config
    )
    other = create_round_dir(tmp_path / "뿌리", TASK.task_id, "B", 1, token="t2")
    assert path_patterns(str(other.clone), watched) == (OTHER_ROUND,)
    assert path_patterns(str(room.place.clone), watched) == ()
    assert path_patterns(str(room.config / "settings.json"), watched) == (CONFIG_FOLDER,)
    pyright: Json = {"name": "pyright-lsp", "source": PYRIGHT}
    assert not room.screen().watch(_line(fake.init_event(extra_plugins=[pyright])))
