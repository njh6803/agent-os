"""파일시스템 PluginSource. 디렉터리에 놓는 것만으로 등록이 끝나는지, 운영자 파일이 켜짐을 드는지.

앞부분은 매니페스트와 진입점, 뒷부분(`# 운영자 파일` 아래)은 플러그인 루트의 `disabled.toml` 이다
(ADR 0017). 진짜 디렉터리에 진짜 파일을 쓴다.
"""

import dataclasses
import os
import re
import subprocess
import sys
import threading
import time
import tomllib
import traceback
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

import pytest

from agent_os.adapters.filesystem import FilesystemPlugins
from agent_os.core.ports import (
    ManifestRow,
    PluginError,
    PluginKey,
    PluginSource,
    Rule,
    Rules,
    RuleSet,
    UnreadableManifest,
)
from agent_os.sdk import (
    AgentContext,
    BaseAgent,
    Conversation,
    Event,
    ModelProvider,
    PluginKind,
    PluginManifest,
    PluginName,
    RunFinished,
    RunId,
    Skill,
)

AGENT_SRC = """
from collections.abc import AsyncIterator

from agent_os.sdk import AgentContext, Event, RunFinished


class Agent:
    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output="{tag}")
"""


def _manifest(kind: str, name: str, extra: str = "") -> str:
    return f'schema_version = "1"\nkind = "{kind}"\nname = "{name}"\nversion = "0.1.0"\n{extra}'


def _write_agent(root: Path, name: str, source: str = AGENT_SRC) -> Path:
    directory = root / "agents" / name
    directory.mkdir(parents=True)
    (directory / "plugin.toml").write_text(
        _manifest("agent", name, 'entrypoint = "agent:Agent"\n'), encoding="utf-8"
    )
    (directory / "agent.py").write_text(source.replace("{tag}", name), encoding="utf-8")
    return directory


def _write_mcp(root: Path, name: str) -> None:
    directory = root / "mcp" / name
    directory.mkdir(parents=True)
    (directory / "plugin.toml").write_text(
        _manifest("mcp", name, '[server]\ncommand = "npx"\nargs = ["-y", "server"]\n'),
        encoding="utf-8",
    )


class FakeContext:
    run_id = RunId("r1")
    conversation = Conversation(summary=None, exchanges=())
    skills: tuple[Skill, ...] = ()

    def now(self) -> datetime:
        return datetime(2026, 9, 21, tzinfo=UTC)

    async def llm(self, prompt: str) -> str:
        return "unused"

    async def tool(self, name: str, **args: object) -> str:
        return "unused"


async def _output_of(agent: BaseAgent) -> str:
    ctx: AgentContext = FakeContext()
    events: list[Event] = [event async for event in agent.run("hi", ctx)]
    assert isinstance(events[-1], RunFinished)
    return events[-1].output


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return tmp_path


def test_에이전트_매니페스트를_디렉터리에서_읽는다(root: Path) -> None:
    _write_agent(root, "calc")
    plugins: PluginSource = FilesystemPlugins(root)

    manifest = plugins.read_manifest(PluginKind.AGENT, PluginName("calc"))

    assert manifest is not None
    assert manifest.name == "calc"
    assert manifest.entrypoint == "agent:Agent"


def test_없는_플러그인은_None이다(root: Path) -> None:
    plugins: PluginSource = FilesystemPlugins(root)

    assert plugins.read_manifest(PluginKind.AGENT, PluginName("nope")) is None


def test_디렉터리와_kind가_어긋나면_에러다(root: Path) -> None:
    directory = root / "agents" / "odd"
    directory.mkdir(parents=True)
    (directory / "plugin.toml").write_text(
        _manifest("mcp", "odd", '[server]\ncommand = "x"\n'), encoding="utf-8"
    )
    plugins: PluginSource = FilesystemPlugins(root)

    with pytest.raises(PluginError, match="kind"):
        plugins.read_manifest(PluginKind.AGENT, PluginName("odd"))


def test_매니페스트_파싱_실패는_무엇이_잘못됐는지_담은_에러다(root: Path) -> None:
    directory = root / "agents" / "bad"
    directory.mkdir(parents=True)
    (directory / "plugin.toml").write_text(
        _manifest("agent", "bad", 'entrypoint = "agent:Agent"\n').replace(
            'schema_version = "1"', 'schema_version = "9"'
        ),
        encoding="utf-8",
    )
    plugins: PluginSource = FilesystemPlugins(root)

    with pytest.raises(PluginError, match="schema_version"):
        plugins.read_manifest(PluginKind.AGENT, PluginName("bad"))


async def test_진입점을_로드하면_에이전트가_돈다(root: Path) -> None:
    _write_agent(root, "calc")
    plugins: PluginSource = FilesystemPlugins(root)
    manifest = plugins.read_manifest(PluginKind.AGENT, PluginName("calc"))
    assert manifest is not None

    agent = plugins.load_agent(manifest)

    assert await _output_of(agent) == "calc"


async def test_같은_파일명을_가진_플러그인_둘이_서로_덮어쓰지_않는다(root: Path) -> None:
    _write_agent(root, "alpha")
    _write_agent(root, "beta")
    plugins: PluginSource = FilesystemPlugins(root)
    alpha = plugins.read_manifest(PluginKind.AGENT, PluginName("alpha"))
    beta = plugins.read_manifest(PluginKind.AGENT, PluginName("beta"))
    assert alpha is not None and beta is not None

    outputs = [await _output_of(plugins.load_agent(m)) for m in (alpha, beta, alpha)]

    assert outputs == ["alpha", "beta", "alpha"]


def test_진입점_속성이_없으면_에러다(root: Path) -> None:
    _write_agent(root, "noattr", source="x = 1\n")
    plugins: PluginSource = FilesystemPlugins(root)
    manifest = plugins.read_manifest(PluginKind.AGENT, PluginName("noattr"))
    assert manifest is not None

    with pytest.raises(PluginError, match="Agent"):
        plugins.load_agent(manifest)


def test_진입점_import가_실패하면_에러다(root: Path) -> None:
    _write_agent(root, "broken", source="def (\n")
    plugins: PluginSource = FilesystemPlugins(root)
    manifest = plugins.read_manifest(PluginKind.AGENT, PluginName("broken"))
    assert manifest is not None

    with pytest.raises(PluginError, match="broken"):
        plugins.load_agent(manifest)


def test_mcp_매니페스트는_서버_실행_정보를_돌려준다(root: Path) -> None:
    _write_mcp(root, "everything")
    plugins: PluginSource = FilesystemPlugins(root)

    manifest = plugins.read_manifest(PluginKind.MCP, PluginName("everything"))

    assert manifest is not None
    assert manifest.server is not None
    assert manifest.server.command == "npx"
    assert plugins.read_manifest(PluginKind.MCP, PluginName("missing")) is None


def test_디렉터리와_name이_어긋나면_에러다(root: Path) -> None:
    directory = root / "agents" / "outer"
    directory.mkdir(parents=True)
    (directory / "plugin.toml").write_text(
        _manifest("agent", "inner", 'entrypoint = "agent:Agent"\n'), encoding="utf-8"
    )
    plugins: PluginSource = FilesystemPlugins(root)

    with pytest.raises(PluginError, match="name"):
        plugins.read_manifest(PluginKind.AGENT, PluginName("outer"))


# 스킬 문서 — `read_skill` 은 `skills/<이름>/SKILL.md` 를 매니페스트와 같은 길로 읽는다(ADR 0041)

SKILL_SECRET = "sk-ant-api03-PLANTED-SKILL-SECRET"
SKILL_HEAD = "name: pdf-processing\ndescription: PDF 를 다룬다\n"


def _skill_document(head: str = SKILL_HEAD, body: str = "본문\n") -> str:
    return f"---\n{head}---\n{body}"


def _write_skill(
    root: Path, name: str, document: str | bytes | None, *, manifest: bool = True
) -> Path:
    """스킬 폴더 하나. 문서는 바이트로 쓴다(줄 끝과 BOM을 그대로 두려고). 돌려주는 것은 문서의
    경로다."""
    directory = root / "skills" / name
    directory.mkdir(parents=True)
    if manifest:
        (directory / "plugin.toml").write_text(_manifest("skill", name), encoding="utf-8")
    path = directory / "SKILL.md"
    if document is not None:
        path.write_bytes(document.encode("utf-8") if isinstance(document, str) else document)
    return path


def test_스킬_문서를_읽어_값으로_돌려준다(root: Path) -> None:
    _write_skill(root, "pdf-processing", _skill_document(body="# 제목\n\n본문이다.\n"))
    plugins: PluginSource = FilesystemPlugins(root)

    skill = plugins.read_skill(PluginName("pdf-processing"))

    assert skill == Skill(
        name=PluginName("pdf-processing"), description="PDF 를 다룬다", body="# 제목\n\n본문이다.\n"
    )


def test_스킬_문서가_없으면_None이다(root: Path) -> None:
    _write_skill(root, "pdf-processing", None)
    plugins: PluginSource = FilesystemPlugins(root)

    assert plugins.read_skill(PluginName("pdf-processing")) is None


def test_스킬_폴더가_없어도_None이다(root: Path) -> None:
    plugins: PluginSource = FilesystemPlugins(root)

    assert plugins.read_skill(PluginName("nope")) is None


def test_머리말의_name이_폴더_이름과_다르면_에러이고_가리킨_스킬의_파일을_읽지_않는다(
    root: Path,
) -> None:
    _write_skill(root, "pdf-processing", _skill_document())
    outer = _write_skill(
        root, "outer", _skill_document("name: pdf-processing\ndescription: 바깥 자리다\n")
    )
    plugins: PluginSource = FilesystemPlugins(root)

    with pytest.raises(PluginError) as raised:
        plugins.read_skill(PluginName("outer"))

    assert str(raised.value) == (
        f"디렉터리와 머리말의 name이 어긋난다: {outer} 는 outer 자리인데 pdf-processing"
    )


def test_CRLF_파일의_본문은_LF로_읽힌다(root: Path) -> None:
    # 텍스트 모드 읽기가 줄 끝을 \n 으로 바꾼다(매니페스트와 같은 길).
    document = _skill_document(body="# 제목\n본문이다.\n").replace("\n", "\r\n")
    _write_skill(root, "pdf-processing", document)
    plugins: PluginSource = FilesystemPlugins(root)

    skill = plugins.read_skill(PluginName("pdf-processing"))

    assert skill is not None
    assert skill.body == "# 제목\n본문이다.\n"


def test_홀로_선_CR_파일도_텍스트_모드_읽기가_LF로_바꿔_받아들인다(root: Path) -> None:
    # 글을 직접 넘기면 거부되는 입력이다. 어댑터 경로에서는 그 거부를 기대하지 않는다.
    _write_skill(root, "pdf-processing", _skill_document(body="본문\n").replace("\n", "\r"))
    plugins: PluginSource = FilesystemPlugins(root)

    skill = plugins.read_skill(PluginName("pdf-processing"))

    assert skill is not None
    assert skill.body == "본문\n"


def test_BOM으로_시작하는_스킬_문서는_머리말로_시작하지_않아_에러다(root: Path) -> None:
    path = _write_skill(root, "pdf-processing", chr(0xFEFF) + _skill_document())
    plugins: PluginSource = FilesystemPlugins(root)

    with pytest.raises(PluginError) as raised:
        plugins.read_skill(PluginName("pdf-processing"))

    assert str(raised.value).splitlines()[0] == f"스킬 문서를 읽을 수 없다: {path}"
    assert "머리말로 시작하지 않는다" in str(raised.value)


def test_UTF_8이_아닌_스킬_문서는_에러다(root: Path) -> None:
    path = _write_skill(root, "pdf-processing", b"---\nname: pdf-processing\n\xff\xfe\n---\n")
    plugins: PluginSource = FilesystemPlugins(root)

    with pytest.raises(PluginError) as raised:
        plugins.read_skill(PluginName("pdf-processing"))

    assert str(raised.value).splitlines()[0] == f"스킬 문서를 읽을 수 없다: {path}"
    assert "utf-8" in str(raised.value)


def test_닫히지_않은_따옴표_뒤의_값은_스킬을_읽지_못한_문구에_나오지_않는다(root: Path) -> None:
    head = f'{SKILL_HEAD}extra: "{SKILL_SECRET}\n'
    path = _write_skill(root, "pdf-processing", _skill_document(head))
    assert SKILL_SECRET in path.read_text(encoding="utf-8")
    plugins: PluginSource = FilesystemPlugins(root)

    with pytest.raises(PluginError) as raised:
        plugins.read_skill(PluginName("pdf-processing"))

    message = str(raised.value)
    assert message.splitlines()[0] == f"스킬 문서를 읽을 수 없다: {path}"
    assert re.search(r"ScannerError \(줄 \d+, 칸 \d+\)", message)
    assert SKILL_SECRET not in message


def test_칸에_잘못_적은_값은_스킬_문구에도_예외_사슬에도_남지_않는다(root: Path) -> None:
    head = f"name: pdf-processing\ndescription: [{SKILL_SECRET}]\n"
    path = _write_skill(root, "pdf-processing", _skill_document(head))
    plugins: PluginSource = FilesystemPlugins(root)

    with pytest.raises(PluginError) as raised:
        plugins.read_skill(PluginName("pdf-processing"))

    message = str(raised.value)
    assert message.splitlines()[0] == f"스킬 문서를 읽을 수 없다: {path}"
    assert "string_type (description)" in message
    assert SKILL_SECRET not in message
    # 원인을 이으면 트레이스백 출력에 pydantic 의 str(입력 값 포함)이 실린다.
    assert raised.value.__cause__ is None
    assert raised.value.__context__ is None
    assert SKILL_SECRET not in "".join(traceback.format_exception(raised.value))


def test_같은_이름을_두_번_읽는_사이_파일을_고치면_둘째가_고친_글을_돌려준다(root: Path) -> None:
    path = _write_skill(root, "pdf-processing", _skill_document(body="처음\n"))
    plugins: PluginSource = FilesystemPlugins(root)
    first = plugins.read_skill(PluginName("pdf-processing"))

    path.write_text(_skill_document(body="고침\n"), encoding="utf-8")
    second = plugins.read_skill(PluginName("pdf-processing"))

    assert first is not None
    assert second is not None
    assert (first.body, second.body) == ("처음\n", "고침\n")


def test_스킬_문서가_없거나_깨진_폴더도_목록의_보통_행이다(root: Path) -> None:
    # 목록은 매니페스트만 읽는다. 문서의 깨짐은 그 스킬을 고른 에이전트의 실행 전에 드러난다.
    _write_skill(root, "no-document", None)
    _write_skill(root, "broken-document", "머리말 없이 본문뿐이다\n")
    plugins: PluginSource = FilesystemPlugins(root)

    rows = plugins.list_manifests(PluginKind.SKILL)

    assert _names(rows) == ["broken-document", "no-document"]
    assert all(isinstance(row, PluginManifest) for row in rows)


def _names(rows: Sequence[ManifestRow]) -> list[str]:
    return [row.name for row in rows]


def test_종류_하나의_매니페스트를_전부_돌려준다(root: Path) -> None:
    _write_agent(root, "alpha")
    _write_agent(root, "beta")
    _write_mcp(root, "everything")
    plugins: PluginSource = FilesystemPlugins(root)

    rows = plugins.list_manifests(PluginKind.AGENT)

    assert _names(rows) == ["alpha", "beta"]
    assert all(isinstance(row, PluginManifest) for row in rows)


def test_빈_디렉터리와_없는_디렉터리가_빈_목록이다(root: Path) -> None:
    (root / "models").mkdir()
    plugins: PluginSource = FilesystemPlugins(root)

    assert plugins.list_manifests(PluginKind.MODEL) == ()
    assert plugins.list_manifests(PluginKind.SKILL) == ()


def _write_broken(root: Path) -> None:
    """읽히지 않는 모양 셋. 매니페스트는 사람이 손으로 쓰는 파일이라 깨지는 것이 예상된 경로다."""
    for name, text in (
        ("badversion", _manifest("agent", "badversion").replace('"1"', '"9"')),
        ("nokind", 'schema_version = "1"\nname = "nokind"\nversion = "0.1.0"\n'),
        ("wrongkind", _manifest("mcp", "wrongkind", '[server]\ncommand = "x"\n')),
    ):
        directory = root / "agents" / name
        directory.mkdir(parents=True)
        (directory / "plugin.toml").write_text(text, encoding="utf-8")


def test_깨진_매니페스트가_섞여도_읽히는_것은_전부_돌아오고_깨진_것은_표지다(root: Path) -> None:
    """깨진 하나가 전부를 가리면 무엇이 살아 있는지조차 알 수 없다. 표지가 이름과 이유를 든다."""
    _write_agent(root, "alpha")
    _write_broken(root)
    plugins: PluginSource = FilesystemPlugins(root)

    rows = plugins.list_manifests(PluginKind.AGENT)

    assert _names(rows) == ["alpha", "badversion", "nokind", "wrongkind"]
    assert isinstance(rows[0], PluginManifest)
    broken = rows[1:]
    assert all(isinstance(row, UnreadableManifest) for row in broken)
    assert all(
        isinstance(row, UnreadableManifest)
        and row.kind is PluginKind.AGENT
        and row.name in row.reason
        for row in broken
    )


def test_열_수_없는_매니페스트가_있어도_목록이_살아남는다(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """권한 오류와 경쟁 삭제는 OSError 이고 ValueError 가 아니다. 포장하지 않으면 매니페스트
    하나가 목록 전체를 가리는데 그것이 ADR 0012 이력이 막으려 한 모양이다.

    실제 권한 오류를 이식성 있게 만들 수 없어 읽기만 주입한다. 보는 것은 바깥 행동 그대로다 —
    목록이 살아남고 그 자리에 표지가 서는 것.
    """
    _write_agent(root, "alpha")
    _write_agent(root, "locked")
    original = Path.read_text

    def refuse(self: Path, encoding: str | None = None, errors: str | None = None) -> str:
        if self.parent.name == "locked":
            raise PermissionError(13, "권한이 없다")
        return original(self, encoding, errors)

    monkeypatch.setattr(Path, "read_text", refuse)
    plugins: PluginSource = FilesystemPlugins(root)

    rows = plugins.list_manifests(PluginKind.AGENT)

    assert _names(rows) == ["alpha", "locked"]
    assert isinstance(rows[0], PluginManifest)
    assert isinstance(rows[1], UnreadableManifest)
    assert "권한" in rows[1].reason


def test_같은_깨진_파일을_단건으로_읽으면_PluginError다(root: Path) -> None:
    """목록과 단건의 비대칭이 의도다. 문서에만 두면 다음 사람이 일관성 결함으로 보고 고친다."""
    _write_broken(root)
    plugins: PluginSource = FilesystemPlugins(root)

    for name in ("badversion", "nokind", "wrongkind"):
        with pytest.raises(PluginError, match=name):
            plugins.read_manifest(PluginKind.AGENT, PluginName(name))


def _write_model(root: Path, name: str, extra: str) -> None:
    directory = root / "models" / name
    directory.mkdir(parents=True)
    (directory / "plugin.toml").write_text(_manifest("model", name, extra), encoding="utf-8")


def test_모델_매니페스트는_제공사와_파라미터를_싣고_읽힌다(root: Path) -> None:
    _write_model(
        root, "opus", 'provider = "anthropic"\nmodel_id = "claude-opus-5"\nmax_tokens = 16000\n'
    )
    plugins: PluginSource = FilesystemPlugins(root)

    manifest = plugins.read_manifest(PluginKind.MODEL, PluginName("opus"))

    assert manifest is not None
    assert manifest.provider is ModelProvider.ANTHROPIC
    assert manifest.model_id == "claude-opus-5"
    assert manifest.max_tokens == 16000
    assert manifest.temperature is None


def test_공통_넷만_적은_옛_모델_파일은_목록에서_그_행만_표지이고_단건으로는_PluginError다(
    root: Path,
) -> None:
    """등록했다고 믿는 것과 실제가 어긋나지 않게 조용히 무시하지 않는다(스토리 9). 같은 종류의
    읽히는 모델은 그대로 오고 목록 전체가 실패하지 않는다."""
    _write_model(root, "good", 'provider = "anthropic"\nmodel_id = "claude-opus-5"\n')
    _write_model(root, "old", "")
    plugins: PluginSource = FilesystemPlugins(root)

    rows = plugins.list_manifests(PluginKind.MODEL)

    assert _names(rows) == ["good", "old"]
    assert isinstance(rows[0], PluginManifest)
    assert isinstance(rows[1], UnreadableManifest)
    assert "provider" in rows[1].reason
    with pytest.raises(PluginError, match="provider"):
        plugins.read_manifest(PluginKind.MODEL, PluginName("old"))


PLANTED_SECRET = "sk-ant-api03-PLANTED-SECRET-VALUE"


def _write_planted(root: Path, kind: PluginKind) -> Path:
    """운영자가 칸을 잘못 적어 키처럼 생긴 값을 심은 매니페스트 하나. 어느 종류든 모르는 칸을
    거부하므로 같은 거부가 선다. 심은 줄은 표 앞에 와야 해서 `_manifest` 의 `extra` 맨 앞에 둔다.
    """
    directory = root / _KIND_DIRECTORY[kind] / "planted"
    directory.mkdir(parents=True)
    path = directory / "plugin.toml"
    extra = f'api_key = "{PLANTED_SECRET}"\n' + _KIND_EXTRA[kind]
    path.write_text(_manifest(kind.value, "planted", extra), encoding="utf-8")
    return path


@pytest.mark.parametrize("kind", [PluginKind.AGENT, PluginKind.MCP, PluginKind.MODEL])
def test_칸에_잘못_적은_값은_매니페스트를_읽지_못한_문구에_다시_나오지_않는다(
    root: Path, kind: PluginKind
) -> None:
    """모델 파일에 `api_key = "sk-ant-…"` 를 적은 운영자의 비밀이 목록 표지와 단건 오류로 새지
    않는다. 문구에는 파일 경로와 칸 이름과 오류 종류만 남아 운영자는 여전히 무엇이 틀렸는지 안다.

    HTTP 면은 이 문구를 그대로 낸다(운영자 면의 500 봉투와 서버 기록 한 줄은 오류 문구 그대로이고
    최종 사용자 면은 고정 문구다). 그래서 따로 시험하지 않고 어댑터 한 곳에서 닫는다.
    """
    manifest_path = _write_planted(root, kind)
    assert PLANTED_SECRET in manifest_path.read_text(encoding="utf-8")
    plugins: PluginSource = FilesystemPlugins(root)

    with pytest.raises(PluginError) as raised:
        plugins.read_manifest(kind, PluginName("planted"))
    row = plugins.list_manifests(kind)[0]

    assert isinstance(row, UnreadableManifest)
    for message in (str(raised.value), row.reason):
        assert PLANTED_SECRET not in message
        assert str(manifest_path) in message
        assert "api_key" in message
        assert "extra_forbidden" in message


def test_플러그인_이름_패턴을_어기는_디렉터리도_표지로_남는다(root: Path) -> None:
    """조용히 빼면 등록했다고 믿는 것과 실제가 어긋난다. 대소문자 오해가 가장 흔한 모양이다.

    런타임은 이 디렉터리를 로드할 수 없지만 표지가 종류와 이름과 이유를 들어, 단건 조회가 줄 것을
    이미 전부 담는다. 트레이스 쪽과 갈리는 것이 의도다 — 그 표지는 실행 식별자 하나만 든다.
    """
    _write_agent(root, "alpha")
    odd = ("MyAgent", "두 낱말", "a", "-앞이하이픈")
    for name in odd:
        directory = root / "agents" / name
        directory.mkdir(parents=True)
        (directory / "plugin.toml").write_text(_manifest("agent", "alpha"), encoding="utf-8")
    plugins: PluginSource = FilesystemPlugins(root)

    rows = plugins.list_manifests(PluginKind.AGENT)

    assert sorted(_names(rows)) == sorted(["alpha", *odd])
    readable = [row for row in rows if isinstance(row, PluginManifest)]
    assert _names(readable) == ["alpha"]
    assert all(
        isinstance(row, UnreadableManifest) and "패턴" in row.reason
        for row in rows
        if row.name in odd
    )


def _write_skills_agent(root: Path, name: str, skills: str) -> None:
    directory = root / "agents" / name
    directory.mkdir(parents=True)
    extra = f'entrypoint = "agent:Agent"\nskills = {skills}\n'
    (directory / "plugin.toml").write_text(_manifest("agent", name, extra), encoding="utf-8")


def test_skills는_적은_순서로_읽히고_패턴을_어기면_그_행만_표지다(root: Path) -> None:
    """목록 전체가 실패하지 않는다. 표지의 문구에는 어긴 값이 실리지 않고 칸 이름과 오류 종류가
    남는다(`../../evil` 은 파일 경로로 조립될 수 있는 값이다)."""
    _write_skills_agent(root, "good", '["zeta-skill", "alpha-skill"]')
    _write_skills_agent(root, "bad", '["../../evil"]')
    plugins: PluginSource = FilesystemPlugins(root)

    rows = plugins.list_manifests(PluginKind.AGENT)

    assert _names(rows) == ["bad", "good"]
    bad, good = rows
    assert isinstance(good, PluginManifest)
    assert good.skills == ("zeta-skill", "alpha-skill")
    assert isinstance(bad, UnreadableManifest)
    assert "skills" in bad.reason
    assert "string_pattern_mismatch" in bad.reason
    assert "../../evil" not in bad.reason
    with pytest.raises(PluginError, match="skills"):
        plugins.read_manifest(PluginKind.AGENT, PluginName("bad"))


# 운영자 파일 — 켜짐은 플러그인 루트의 disabled.toml 이 든다(ADR 0017, plugin-toggle 티켓 01)

DISABLED = "disabled.toml"
# API 가 쓰는 정규형. 종류 넷이 모두, 이름순으로, 중복 없이. 아무것도 꺼지지 않은 파일이 이것이다.
CANONICAL_EMPTY = 'schema_version = "1"\nagent = []\nmcp = []\nskill = []\nmodel = []\n'
_KIND_DIRECTORY = {
    PluginKind.AGENT: "agents",
    PluginKind.MCP: "mcp",
    PluginKind.SKILL: "skills",
    PluginKind.MODEL: "models",
}
_KIND_EXTRA = {
    PluginKind.AGENT: 'entrypoint = "agent:Agent"\n',
    PluginKind.MCP: '[server]\ncommand = "npx"\n',
    PluginKind.SKILL: "",
    PluginKind.MODEL: 'provider = "anthropic"\nmodel_id = "claude-opus-5"\n',
}


def _key(kind: PluginKind, name: str) -> PluginKey:
    return PluginKey(kind=kind, name=PluginName(name))


def _write_plugin(root: Path, kind: PluginKind, name: str) -> None:
    """종류를 가리지 않고 매니페스트 하나. 켜고 끄는 키는 매니페스트의 내용이 아니라 그 파일의
    존재다."""
    directory = root / _KIND_DIRECTORY[kind] / name
    directory.mkdir(parents=True)
    (directory / "plugin.toml").write_text(
        _manifest(kind.value, name, _KIND_EXTRA[kind]), encoding="utf-8"
    )


def _operator_file(root: Path, text: str) -> Path:
    path = root / DISABLED
    path.write_text(text, encoding="utf-8")
    return path


def _loaded(root: Path) -> dict[str, object]:
    """쓴 파일을 표준 라이브러리로 읽은 값. 쓰기 코드가 맞게 쓰는지는 이것이 판정한다(ADR 0017)."""
    return tomllib.loads((root / DISABLED).read_text(encoding="utf-8"))


def _root_entries(root: Path) -> set[str]:
    """플러그인 루트에 있는 것. 임시 파일이 남았는지 보는 자리다."""
    return {child.name for child in root.iterdir()}


def _plugins(root: Path) -> PluginSource:
    return FilesystemPlugins(root)


def test_운영자_파일이_없으면_꺼진_것이_없다(root: Path) -> None:
    """기본은 켜짐이고 파일에는 끈 것만 적는다(ADR 0017). 새 에이전트를 넣을 때 켜는 단계가 없다
    (스토리 19)."""
    _write_agent(root, "calc")

    assert _plugins(root).read_disabled() == frozenset()


def test_운영자_파일의_이름_배열이_꺼진_집합이고_빠진_키는_빈_목록이며_중복은_하나로_합친다(
    root: Path,
) -> None:
    """손으로 적은 파일에서 키가 빠지거나 이름이 겹쳐도 뜻이 하나로만 읽힌다(스토리 24)."""
    _operator_file(root, 'schema_version = "1"\nagent = ["calc", "calc"]\nmcp = ["everything"]\n')

    assert _plugins(root).read_disabled() == {
        _key(PluginKind.AGENT, "calc"),
        _key(PluginKind.MCP, "everything"),
    }


def test_운영자_파일의_종류_키가_플러그인_종류의_값_넷이다(root: Path) -> None:
    """키 이름은 `PluginKind` 의 값과 같다(ADR 0017). 종류마다 하나씩 끄면 넷이 전부 읽힌다."""
    _operator_file(
        root,
        'schema_version = "1"\nagent = ["a1"]\nmcp = ["m1"]\nskill = ["s1"]\nmodel = ["d1"]\n',
    )

    assert _plugins(root).read_disabled() == {
        _key(PluginKind.AGENT, "a1"),
        _key(PluginKind.MCP, "m1"),
        _key(PluginKind.SKILL, "s1"),
        _key(PluginKind.MODEL, "d1"),
    }


# 손상의 모양. 매니페스트에서 여는 것부터 검증까지를 PluginError 로 바꾸는 선례와 같다.
CORRUPT = (
    pytest.param('schema_version = "1"\nagent = [', id="문법 오류"),
    pytest.param("", id="빈 파일"),
    pytest.param('agent = ["calc"]\n', id="형식 버전이 없음"),
    pytest.param('schema_version = "2"\nagent = ["calc"]\n', id="모르는 형식 버전"),
    pytest.param('schema_version = "1"\nagents = ["calc"]\n', id="모르는 키"),
    pytest.param('schema_version = "1"\nagent = ["MyAgent"]\n', id="패턴을 어긴 이름"),
    pytest.param('schema_version = "1"\nagent = "calc"\n', id="배열이 아닌 값"),
    pytest.param('schema_version = "1"\nagent = [1]\n', id="문자열이 아닌 원소"),
)


@pytest.mark.parametrize("text", CORRUPT)
def test_운영자_파일의_손상은_PluginError이고_메시지에_파일_경로가_있다(
    root: Path, text: str
) -> None:
    """무엇이 꺼져 있는지 모르는 채 돌리면 끈 것이 돈다(스토리 20·21). 빈 파일도 손상이다 — 형식
    버전이 없는 파일을 "아무것도 꺼지지 않았다"로 읽으면 잘린 파일이 끈 것을 전부 켠다(스토리
    23)."""
    path = _operator_file(root, text)

    with pytest.raises(PluginError, match=re.escape(str(path))):
        _plugins(root).read_disabled()


def test_UTF_8로_읽지_못하는_운영자_파일도_손상이다(root: Path) -> None:
    path = root / DISABLED
    path.write_bytes(b'schema_version = "1"\nagent = ["\xff"]\n')

    with pytest.raises(PluginError, match=re.escape(str(path))):
        _plugins(root).read_disabled()


def test_디렉터리가_없는_이름은_손상이_아니라_꺼진_집합에_든다(root: Path) -> None:
    """지운 플러그인의 이름이 남아도 에러가 아니다. 같은 이름이 다시 들어오면 꺼진 채로 오는 것이
    안전한 쪽이다(스토리 15)."""
    _operator_file(root, 'schema_version = "1"\nagent = ["ghost"]\n')

    assert _plugins(root).read_disabled() == {_key(PluginKind.AGENT, "ghost")}


def test_끄면_파일이_생기고_켜면_그_이름이_빠지며_마지막_것을_켜도_파일은_남고_네_배열이_빈다(
    root: Path,
) -> None:
    """끈 것은 지운 것이 아니라 같은 길로 되돌린다(스토리 1·2). 파일을 지우면 쓰기 말고 삭제라는
    둘째 경로가 생기므로 남긴다. 성공 뒤에 임시 파일이 남지 않는다."""
    _write_agent(root, "calc")
    plugins = _plugins(root)

    disabled = plugins.write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=False)
    written = _loaded(root)
    enabled = plugins.write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=True)

    assert disabled == "applied"
    assert written == {
        "schema_version": "1",
        "agent": ["calc"],
        "mcp": [],
        "skill": [],
        "model": [],
    }
    assert enabled == "applied"
    assert _loaded(root) == {
        "schema_version": "1",
        "agent": [],
        "mcp": [],
        "skill": [],
        "model": [],
    }
    assert plugins.read_disabled() == frozenset()
    assert _root_entries(root) == {"agents", DISABLED}


def test_쓴_파일은_정규형이라_종류_넷이_모두_있고_이름순이며_중복이_없고_주석이_사라진다(
    root: Path,
) -> None:
    """git 의 변경이 켜고 끈 것만 보여야 한다(스토리 25). 주석을 남기려면 손으로 고친다(스토리
    26)."""
    for name in ("alpha", "beta", "gamma"):
        _write_agent(root, name)
    _write_mcp(root, "everything")
    _operator_file(
        root,
        "# 손으로 적었다\n"
        'mcp = ["everything"]\n'
        'schema_version = "1"\n'
        'agent = ["gamma", "alpha", "gamma"]\n',
    )

    _plugins(root).write_enabled(PluginKind.AGENT, PluginName("beta"), enabled=False)

    assert (root / DISABLED).read_text(encoding="utf-8") == (
        'schema_version = "1"\n'
        'agent = ["alpha", "beta", "gamma"]\n'
        'mcp = ["everything"]\n'
        "skill = []\n"
        "model = []\n"
    )


# 왕복의 집합들. 빈 것, 종류마다 하나, 패턴의 경계 문자를 쓴 이름.
LONGEST = "a" + "z" * 62
ROUND_TRIPS = (
    pytest.param((), id="빈 집합"),
    pytest.param(
        (
            (PluginKind.AGENT, "calc"),
            (PluginKind.MCP, "everything"),
            (PluginKind.SKILL, "summarize"),
            (PluginKind.MODEL, "sonnet"),
        ),
        id="종류마다 하나",
    ),
    pytest.param(
        ((PluginKind.AGENT, "ab"), (PluginKind.AGENT, "a0-9-z"), (PluginKind.AGENT, LONGEST)),
        id="패턴의 경계 문자",
    ),
)


@pytest.mark.parametrize("keys", ROUND_TRIPS)
def test_쓴_파일을_tomllib으로_읽으면_쓴_집합_그대로다(
    root: Path, keys: Sequence[tuple[PluginKind, str]]
) -> None:
    """쓰기 코드는 직접 짜고 맞게 쓰는지는 표준 라이브러리가 판정한다(ADR 0017). 쓰기 의존성을
    들이지 않는다."""
    _write_agent(root, "seed")
    for kind, name in keys:
        _write_plugin(root, kind, name)
    plugins = _plugins(root)
    for kind, name in keys:
        plugins.write_enabled(kind, PluginName(name), enabled=False)
    # 빈 집합에도 파일이 서게 하려고 하나를 껐다 켠다. 켜도 파일은 남는다.
    plugins.write_enabled(PluginKind.AGENT, PluginName("seed"), enabled=False)
    plugins.write_enabled(PluginKind.AGENT, PluginName("seed"), enabled=True)

    loaded = _loaded(root)

    assert loaded == {
        "schema_version": "1",
        **{kind.value: sorted(name for k, name in keys if k is kind) for kind in PluginKind},
    }
    assert plugins.read_disabled() == {_key(kind, name) for kind, name in keys}


def test_쓰기가_고아_항목을_지우지_않는다(root: Path) -> None:
    """디렉터리가 없는 이름은 손편집으로만 지운다(스토리 16). 그 이름의 PUT 은 부재라 켤 수 없다."""
    _write_agent(root, "calc")
    _operator_file(root, 'schema_version = "1"\nagent = ["ghost"]\n')

    _plugins(root).write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=False)

    assert _loaded(root)["agent"] == ["calc", "ghost"]


def test_없는_이름에_쓰면_부재를_값으로_돌려주고_파일은_바이트_그대로다(root: Path) -> None:
    """오타로 지은 이름이 파일에 쌓이면 안 된다(스토리 5). 없었으면 여전히 없다."""
    _write_agent(root, "calc")
    plugins = _plugins(root)

    before_file = plugins.write_enabled(PluginKind.AGENT, PluginName("nope"), enabled=False)
    assert before_file == "absent"
    assert not (root / DISABLED).exists()

    path = _operator_file(root, "# 주석\nschema_version = \"1\"\nagent = ['calc']\n")
    original = path.read_bytes()
    other_kind = plugins.write_enabled(PluginKind.MCP, PluginName("calc"), enabled=False)

    assert other_kind == "absent"
    assert path.read_bytes() == original


def test_운영자_파일이_깨졌어도_없는_이름은_부재다(root: Path) -> None:
    """부재 판정이 먼저다(ADR 0017 의 2026-09-27 둘째 이력). 없는 이름을 두고 파일이 깨졌다고
    답하면 운영자는 이름이 맞다고 믿은 채 파일을 고치러 간다."""
    _write_agent(root, "calc")
    path = _operator_file(root, "not toml at all ][")
    original = path.read_bytes()

    outcome = _plugins(root).write_enabled(PluginKind.AGENT, PluginName("nope"), enabled=False)

    assert outcome == "absent"
    assert path.read_bytes() == original


def test_매니페스트가_깨진_플러그인에도_쓸_수_있다(root: Path) -> None:
    """고칠 때까지 런타임이 부르지 않게 하려는 것이 끄는 이유일 수 있다(스토리 6). 판정 대상은
    파일이 있느냐이지 읽히느냐가 아니다."""
    _write_broken(root)

    outcome = _plugins(root).write_enabled(
        PluginKind.AGENT, PluginName("badversion"), enabled=False
    )

    assert outcome == "applied"
    assert _loaded(root)["agent"] == ["badversion"]


def test_깨진_파일에_쓰면_PluginError이고_파일이_바이트_그대로다_바뀌는_것이_없는_쓰기도_같다(
    root: Path,
) -> None:
    """덮어쓰면 끈 것이 조용히 켜질 수 있다(스토리 22). 손상 판정이 "바뀌는 것이 없다"는 판단보다
    먼저라 켜진 것을 켜는 요청도 거부한다."""
    _write_agent(root, "calc")
    path = _operator_file(root, 'schema_version = "1"\nagent = "calc"\n')
    original = path.read_bytes()
    plugins = _plugins(root)

    with pytest.raises(PluginError, match=re.escape(str(path))):
        plugins.write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=False)
    with pytest.raises(PluginError, match=re.escape(str(path))):
        plugins.write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=True)

    assert path.read_bytes() == original
    assert _root_entries(root) == {"agents", DISABLED}


def test_바뀌는_것이_없는_쓰기는_파일을_건드리지_않는다(root: Path) -> None:
    """주석이 이유 없이 사라지거나 없던 파일이 생기면 안 된다(스토리 27). 이미 꺼진 것을 끄고 켜진
    것을 켜는 것이 그렇다."""
    _write_agent(root, "calc")
    _write_agent(root, "echo")
    plugins = _plugins(root)

    assert plugins.write_enabled(PluginKind.AGENT, PluginName("echo"), enabled=True) == "applied"
    assert not (root / DISABLED).exists()

    path = _operator_file(root, '# 주석\nschema_version = "1"\nagent = ["calc"]\n')
    original = path.read_bytes()
    assert plugins.write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=False) == "applied"
    assert plugins.write_enabled(PluginKind.AGENT, PluginName("echo"), enabled=True) == "applied"

    assert path.read_bytes() == original


@dataclasses.dataclass
class Injected:
    """주입한 실패의 기록. 몇 번 거절했는지가 곧 재시도가 실제로 돌았다는 증거다."""

    refusals: int = 0


def _refuse_reads(
    monkeypatch: pytest.MonkeyPatch, *, error: OSError, times: int | None, name: str = DISABLED
) -> Injected:
    """운영자 파일 읽기를 times 번(None 이면 끝까지) 거절한다. 매니페스트 읽기는 건드리지 않는다.

    name 이 거절할 파일이다. 기본은 꺼진 집합의 파일이고 규칙 파일 시험은 그 이름을 준다."""
    injected = Injected()
    original = Path.read_text

    def refuse(self: Path, encoding: str | None = None, errors: str | None = None) -> str:
        if self.name == name and (times is None or injected.refusals < times):
            injected.refusals += 1
            raise error
        return original(self, encoding, errors)

    monkeypatch.setattr(Path, "read_text", refuse)
    return injected


def _refuse_replaces(
    monkeypatch: pytest.MonkeyPatch, *, error: OSError, times: int | None
) -> Injected:
    """임시 파일을 운영자 파일로 바꾸는 교체를 times 번(None 이면 끝까지) 거절한다."""
    injected = Injected()
    original = os.replace

    def refuse(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        if times is None or injected.refusals < times:
            injected.refusals += 1
            raise error
        original(src, dst)

    monkeypatch.setattr(os, "replace", refuse)
    return injected


def test_읽기가_PermissionError를_몇_번_받다_성공하면_집합을_돌려준다(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """윈도우에서 교체되는 순간 여는 읽기가 그렇다. 상한 안에서 풀리면 500 이 아니다(ADR 0017 의
    2026-09-27 첫 이력)."""
    _operator_file(root, 'schema_version = "1"\nagent = ["calc"]\n')
    injected = _refuse_reads(
        monkeypatch, error=PermissionError(13, "다른 핸들이 쥐고 있다"), times=3
    )

    assert _plugins(root).read_disabled() == {_key(PluginKind.AGENT, "calc")}
    assert injected.refusals == 3


def test_읽기가_끝까지_PermissionError면_PluginError이고_메시지에_경로가_있다(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """오래 쥔 핸들 앞에서는 상한을 넘긴 뒤 규칙 그대로다. 다시 시도하긴 했다는 것을 거절 횟수가
    말한다."""
    path = _operator_file(root, 'schema_version = "1"\nagent = ["calc"]\n')
    injected = _refuse_reads(
        monkeypatch, error=PermissionError(13, "다른 핸들이 쥐고 있다"), times=None
    )

    with pytest.raises(PluginError, match=re.escape(str(path))):
        _plugins(root).read_disabled()
    assert injected.refusals >= 2


def test_PermissionError가_아닌_열기_실패는_다시_시도하지_않고_바로_PluginError다(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """다시 시도하는 것은 PermissionError 하나다. 끊긴 드라이브는 다시 읽어도 같다."""
    path = _operator_file(root, 'schema_version = "1"\nagent = ["calc"]\n')
    injected = _refuse_reads(monkeypatch, error=OSError(5, "입출력 오류"), times=None)

    with pytest.raises(PluginError, match=re.escape(str(path))):
        _plugins(root).read_disabled()
    assert injected.refusals == 1


def test_교체가_PermissionError를_몇_번_받다_성공하면_파일이_바뀌고_임시_파일이_없다(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """윈도우에서 다른 핸들이 연 파일을 교체할 때가 그렇다. 관리의 GET 이 스레드풀에서 읽는 사이
    PUT 이 쓰면 `serve` 하나 안에서도 부딪힌다(ADR 0017 의 2026-09-27 첫 이력)."""
    _write_agent(root, "calc")
    _operator_file(root, CANONICAL_EMPTY)
    injected = _refuse_replaces(
        monkeypatch, error=PermissionError(13, "다른 핸들이 쥐고 있다"), times=3
    )

    outcome = _plugins(root).write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=False)

    assert outcome == "applied"
    assert injected.refusals == 3
    assert _loaded(root)["agent"] == ["calc"]
    assert _root_entries(root) == {"agents", DISABLED}


def test_교체가_끝까지_PermissionError면_PluginError이고_옛_파일이_그대로이며_임시_파일이_없다(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """실패한 쓰기가 켜짐을 바꾸면 안 된다(스토리 29). 옛 파일은 바이트 그대로이고, 임시 파일이
    남으면 다음 사람이 무엇인지 모른다."""
    _write_agent(root, "calc")
    path = _operator_file(root, CANONICAL_EMPTY)
    original = path.read_bytes()
    injected = _refuse_replaces(
        monkeypatch, error=PermissionError(13, "다른 핸들이 쥐고 있다"), times=None
    )

    with pytest.raises(PluginError, match=re.escape(str(path))):
        _plugins(root).write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=False)

    assert injected.refusals >= 2
    assert path.read_bytes() == original
    assert _root_entries(root) == {"agents", DISABLED}


def test_PermissionError가_아닌_쓰기_실패는_다시_시도하지_않고_PluginError이며_옛_파일이_그대로다(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """가득 찬 디스크는 다시 써도 같다. 옛 파일은 그대로이고 임시 파일도 남지 않는다."""
    _write_agent(root, "calc")
    path = _operator_file(root, CANONICAL_EMPTY)
    original = path.read_bytes()
    injected = _refuse_replaces(monkeypatch, error=OSError(28, "디스크가 가득 찼다"), times=None)

    with pytest.raises(PluginError, match=re.escape(str(path))):
        _plugins(root).write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=False)

    assert injected.refusals == 1
    assert path.read_bytes() == original
    assert _root_entries(root) == {"agents", DISABLED}


# 실제 핸들로 재는 넷. 윈도우에서는 다른 핸들이 연 파일의 교체와, 교체되는 순간 여는 읽기가
# PermissionError 라서(ADR 0017 의 2026-09-27 첫 이력) 이 넷이 재시도를 실제로 지난다. 윈도우가 아닌
# 러너에서는 교체가 원자적이라 그 오류가 없고, 같은 단언이 "열린 채 읽는 쪽이 있어도 교체가 막히지
# 않는다"와 "교체되는 도중에도 읽기는 언제나 완전한 집합 하나를 본다"를 잰다. skip 하지 않는다.
# 교체하는 쪽도 실제 어댑터다. ADR 의 실측이 그 조건이고, 쉬지 않고 `os.replace` 만 도는 쓰기는 읽기
# 여섯 시도가 전부 교체 창에 걸릴 만큼 잦아 실제 쓰기의 모양이 아니다(그렇게 쟀을 때 한 번
# 빨개졌다).
HOLD_SECONDS = 0.004
TOGGLE_SECONDS = 0.3
# 읽기 재시도의 설계 상한(ADR 0017 의 2026-09-27 첫 이력, 1·2·4·8·16ms 의 합). 어댑터의
# `_RETRY_DELAYS` 를 읽지 않고 따로 둔다. 읽으면 재시도를 없애는 회귀가 판정의 문턱까지 0 으로
# 만들어 지나간다. 상한의 크기 자체는 이 문턱이 못 박지 않는다(재시도 사이를 줄여도 막힘이 그 안에
# 풀리면 초록이다). 쓰는 곳은 `_read_while_past_cap` 이다.
RETRY_CAP_SECONDS = 0.031
CALC_DISABLED = 'schema_version = "1"\nagent = ["calc"]\n'
# 다른 프로세스가 파일을 연 채 잠깐 쥔다. 열었다는 신호를 표준 출력으로 보낸다.
HOLDER = """
import sys, time
with open(sys.argv[1], "rb"):
    print("opened", flush=True)
    time.sleep(float(sys.argv[2]))
"""
# 다른 프로세스가 실제 어댑터로 calc 를 켜고 끈다. 자기 쓰기가 상한을 넘겨 PluginError 면 세고
# 계속한다 — ADR 0017 이 받아들인 것이고, 재는 것은 그쪽이 아니라 이쪽의 읽기다. 센 수는 마지막 줄로
# 나가고 종료 코드 0 이 예기치 않은 예외 없이 끝났다는 뜻이다.
TOGGLER = """
import sys, time
from pathlib import Path
from agent_os.adapters.filesystem import FilesystemPlugins
from agent_os.core.ports import PluginError
from agent_os.sdk import PluginKind, PluginName
plugins = FilesystemPlugins(Path(sys.argv[1]))
deadline = time.monotonic() + float(sys.argv[2])
print("started", flush=True)
enabled = True
capped = 0
while time.monotonic() < deadline:
    try:
        plugins.write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=enabled)
    except PluginError:
        capped += 1
    enabled = not enabled
print(capped, flush=True)
"""


def _toggle(root: Path, seconds: float) -> int:
    """같은 프로세스의 다른 스레드가 실제 어댑터로 calc 를 켜고 끈다. 위 TOGGLER 와 같은 일이다.

    돌려주는 것은 상한을 넘긴 쓰기의 수다. 단언하지 않고 세기만 한다 — 재는 것은 이쪽의 읽기다.
    """
    plugins = _plugins(root)
    deadline = time.monotonic() + seconds
    enabled = True
    capped = 0
    while time.monotonic() < deadline:
        try:
            plugins.write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=enabled)
        except PluginError:
            capped += 1
        enabled = not enabled
    return capped


# 켜고 끄는 동안 읽기가 볼 수 있는 상태 둘. 파일은 늘 있고 마지막 것을 켜도 남는다.
TOGGLED_STATES: set[frozenset[PluginKey]] = {
    frozenset(),
    frozenset({_key(PluginKind.AGENT, "calc")}),
}


def _assert_replaced_under_hold(root: Path, outcome: str) -> None:
    assert outcome == "applied"
    assert _loaded(root)["agent"] == ["calc"]
    assert _root_entries(root) == {"agents", DISABLED}


def test_다른_스레드가_운영자_파일을_연_채여도_교체가_재시도_안에서_성공한다(root: Path) -> None:
    """관리의 GET 은 스레드풀에서 읽고 PUT 은 이벤트 루프에서 쓴다. 그 핸들이 상한 안에 닫히면
    쓰기가 성공해야 한다."""
    _write_agent(root, "calc")
    path = _operator_file(root, CANONICAL_EMPTY)
    opened = threading.Event()

    def hold() -> None:
        with path.open("rb"):
            opened.set()
            time.sleep(HOLD_SECONDS)

    holder = threading.Thread(target=hold)
    holder.start()
    opened.wait()
    outcome = _plugins(root).write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=False)
    holder.join()

    _assert_replaced_under_hold(root, outcome)


def test_다른_프로세스가_운영자_파일을_연_채여도_교체가_재시도_안에서_성공한다(root: Path) -> None:
    """손편집기나 다른 `serve` 가 잠깐 연 것이다."""
    _write_agent(root, "calc")
    path = _operator_file(root, CANONICAL_EMPTY)
    holder = subprocess.Popen(
        [sys.executable, "-c", HOLDER, str(path), str(HOLD_SECONDS)],
        stdout=subprocess.PIPE,
        text=True,
    )
    assert holder.stdout is not None
    assert holder.stdout.readline().strip() == "opened"
    outcome = _plugins(root).write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=False)
    holder.wait(timeout=10)

    _assert_replaced_under_hold(root, outcome)


def _read_while(plugins: PluginSource, running: Callable[[], bool]) -> set[frozenset[PluginKey]]:
    """교체가 도는 동안 쉬지 않고 읽는다. 한 번이라도 PluginError 면 이 함수가 그대로 던진다."""
    seen: set[frozenset[PluginKey]] = set()
    while True:
        seen.add(plugins.read_disabled())
        if not running():
            return seen


class _DisabledReader(Protocol):
    def read_disabled(self) -> frozenset[PluginKey]: ...


def _read_while_past_cap(
    plugins: _DisabledReader,
    running: Callable[[], bool],
    clock: Callable[[], float] = time.perf_counter,
) -> set[frozenset[PluginKey]]:
    """`_read_while` 와 같되, 재시도 상한을 다 쓰고도 파일이 잠겨 난 PluginError 는 넘어간다.

    상한을 넘기면 PluginError 인 것이 ADR 0017 이 받아들인 동작이다. 넘기는 것은 둘을 모두 갖춘
    것뿐이다. 까닭(`__cause__`)이 `PermissionError` 이고, 상한을 다 쓴 뒤에 났다. 상한을 다 쓰기
    전에 난 것은 재시도가 없거나 짧아진 것이고, 다른 까닭(반쪽 파일을 읽은 손상 등)은 시간과
    상관없이 빨강이라 그대로 던진다. 시간으로 가르려면 다섯 번 쉰 합이 31ms 보다 짧게 끝나는 일이
    없어야 하고, 그것은 `.scratch/harness/probes/precommit_xdist/retry_sleep_floor.py` 가 잰다(ADR
    0035 의 2026-10-17 이력). clock 은 판정 시험이 경과 시간을 정하려고 바꾼다.
    """
    seen: set[frozenset[PluginKey]] = set()
    while True:
        started = clock()
        try:
            seen.add(plugins.read_disabled())
        except PluginError as error:
            locked = isinstance(error.__cause__, PermissionError)
            if not locked or clock() - started < RETRY_CAP_SECONDS:
                raise
        if not running():
            return seen


# 위 판정이 넘기는 범위를 못 박는다. 실제 교체로는 상한 전의 실패도, 상한 뒤의 손상도 마음대로 만들
# 수 없어(부하가 없으면 막힘이 상한 안에 풀린다) 바로 실패하는 가짜와 가짜 시계로 부른다. 실제로
# 쉬게 하면 부하 아래에서는 0초를 쉬어도 상한을 넘길 수 있어 판정 시험이 흔들린다.
@dataclasses.dataclass(frozen=True)
class _FailingReader:
    """`read_disabled` 가 cause 를 까닭으로 PluginError 를 바로 던진다."""

    cause: Exception

    def read_disabled(self) -> frozenset[PluginKey]:
        raise PluginError("가짜 실패") from self.cause


def _clock_after(elapsed: float) -> Callable[[], float]:
    """처음 읽으면 0, 다음에 읽으면 elapsed 인 시계다. 판정은 읽기 한 번에 시계를 두 번 읽는다."""
    return iter((0.0, elapsed)).__next__


def test_상한을_다_쓴_뒤의_잠김_PluginError_는_판정이_넘어간다() -> None:
    locked = _FailingReader(PermissionError(13, "잠김"))

    assert _read_while_past_cap(locked, lambda: False, _clock_after(RETRY_CAP_SECONDS)) == set()


def test_상한_전의_잠김_PluginError_는_판정이_던진다() -> None:
    locked = _FailingReader(PermissionError(13, "잠김"))

    with pytest.raises(PluginError, match="가짜 실패"):
        _read_while_past_cap(locked, lambda: False, _clock_after(RETRY_CAP_SECONDS - 0.001))


def test_상한을_다_쓴_뒤라도_잠김이_아닌_PluginError_는_판정이_던진다() -> None:
    broken = _FailingReader(ValueError("반쪽 파일"))

    with pytest.raises(PluginError, match="가짜 실패"):
        _read_while_past_cap(broken, lambda: False, _clock_after(RETRY_CAP_SECONDS + 0.01))


def test_다른_스레드가_교체하는_동안의_읽기가_재시도_안에서_성공한다(root: Path) -> None:
    """읽기는 언제나 두 상태 가운데 하나를 본다. 반쪽 파일도, 500 도 없다. 관리의 GET 이
    스레드풀에서 읽는 사이 PUT 이 루프에서 쓰는 모양이다."""
    _write_agent(root, "calc")
    _operator_file(root, CALC_DISABLED)

    with ThreadPoolExecutor(max_workers=1) as pool:
        toggling = pool.submit(_toggle, root, TOGGLE_SECONDS)
        seen = _read_while(_plugins(root), lambda: not toggling.done())
    toggling.result()

    assert seen == TOGGLED_STATES


def test_다른_프로세스가_교체하는_동안의_읽기가_재시도_안에서_성공한다(root: Path) -> None:
    """다른 `serve` 나 스크립트가 같은 파일을 쓰는 것이다. 나중에 쓴 쪽이 이기지만(스토리 44) 읽기는
    어느 쪽이든 완전한 파일을 본다.

    부하 아래에서는 다른 프로세스의 교체 하나가 상한보다 오래 파일을 쥐어, 읽기가 상한을 다 쓰고도
    PluginError 다. ADR 0017 이 받아들인 동작이라 그것은 넘어가고, 그 밖의 PluginError(상한 전의
    것, 잠김이 아닌 까닭의 것)는 빨강이다. xdist 로 나눠 도는 pre-commit 에서 두 번 빨갰고, 실패의
    모양이 남은 한 번이 이것이었다. 재현과 원인은 ADR 0035 의 2026-10-17 이력이다.
    """
    _write_agent(root, "calc")
    _operator_file(root, CALC_DISABLED)
    toggler = subprocess.Popen(
        [sys.executable, "-c", TOGGLER, str(root), str(TOGGLE_SECONDS)],
        stdout=subprocess.PIPE,
        text=True,
    )
    assert toggler.stdout is not None
    assert toggler.stdout.readline().strip() == "started"

    seen = _read_while_past_cap(_plugins(root), lambda: toggler.poll() is None)

    assert toggler.wait(timeout=10) == 0
    assert seen == TOGGLED_STATES


# 규칙 파일 — 승인 규칙은 플러그인 루트의 rules.toml 이 든다(ADR 0044, approval-rules 티켓 02)

RULES = "rules.toml"


def _rules_file(root: Path, text: str) -> Path:
    path = root / RULES
    path.write_text(text, encoding="utf-8")
    return path


def _one(server: str, tool: str) -> Rule:
    return Rule(server=PluginName(server), tool=tool)


def _whole(server: str) -> Rule:
    return Rule(server=PluginName(server), tool=None)


def _bare(tool: str) -> Rule:
    return Rule(server=None, tool=tool)


def _rule_set(
    *,
    deny: tuple[Rule, ...] = (),
    ask: tuple[Rule, ...] = (),
    allow: tuple[Rule, ...] = (),
) -> RuleSet:
    return RuleSet(deny=frozenset(deny), ask=frozenset(ask), allow=frozenset(allow))


def test_규칙_파일이_없으면_빈_규칙이다(root: Path) -> None:
    """파일이 없는 것은 규칙이 없는 것이다. 공통 표가 비고 에이전트 표가 없다."""
    rules = _plugins(root).read_rules()

    assert rules == Rules()
    assert rules.common == _rule_set()
    assert dict(rules.agents) == {}


def test_규칙_파일의_공통_표와_에이전트_표와_세_꼴의_줄이_규칙_값으로_읽힌다(root: Path) -> None:
    """맨 이름은 서버 없음, `서버:*`는 도구 없음, `서버:도구`는 둘 다 있음이다. 어댑터가 문자열을
    값으로 바꿔 넘기므로 `everything:*` 가 도구 없는 규칙으로 읽히는 것을 여기서 본다."""
    _rules_file(
        root,
        'schema_version = "1"\n'
        "[common]\n"
        'deny = ["everything:send_mail", "rm"]\n'
        'ask = ["everything:write_file"]\n'
        'allow = ["everything:*"]\n'
        "[agents.calc]\n"
        'allow = ["everything:add"]\n',
    )

    assert _plugins(root).read_rules() == Rules(
        common=_rule_set(
            deny=(_one("everything", "send_mail"), _bare("rm")),
            ask=(_one("everything", "write_file"),),
            allow=(_whole("everything"),),
        ),
        agents={PluginName("calc"): _rule_set(allow=(_one("everything", "add"),))},
    )


def test_규칙_파일을_읽을_때마다_디스크를_다시_읽어_고친_규칙이_둘째_읽기에_보인다(
    root: Path,
) -> None:
    """캐시하지 않는다. 운영자가 손으로 고친 것이 다음 읽기부터 듣는다."""
    _rules_file(root, 'schema_version = "1"\n[common]\ndeny = ["rm"]\n')
    plugins = _plugins(root)

    first = plugins.read_rules()
    _rules_file(root, 'schema_version = "1"\n[common]\nask = ["rm"]\n')
    second = plugins.read_rules()

    assert first.common == _rule_set(deny=(_bare("rm"),))
    assert second.common == _rule_set(ask=(_bare("rm"),))


def test_규칙_파일의_읽기도_PermissionError를_몇_번_받다_성공하면_규칙을_돌려준다(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """꺼진 집합의 읽기와 같은 재시도를 지난다(ADR 0017 의 2026-09-27 첫 이력)."""
    _rules_file(root, 'schema_version = "1"\n[common]\ndeny = ["rm"]\n')
    injected = _refuse_reads(
        monkeypatch, error=PermissionError(13, "다른 핸들이 쥐고 있다"), times=3, name=RULES
    )

    assert _plugins(root).read_rules().common == _rule_set(deny=(_bare("rm"),))
    assert injected.refusals == 3


def test_규칙_파일의_읽기가_끝까지_PermissionError면_읽을_수_없다는_PluginError다(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _rules_file(root, 'schema_version = "1"\n')
    _refuse_reads(
        monkeypatch, error=PermissionError(13, "다른 핸들이 쥐고 있다"), times=None, name=RULES
    )

    with pytest.raises(PluginError) as caught:
        _plugins(root).read_rules()

    assert str(caught.value).startswith(f"운영자 파일을 읽을 수 없다: {path}\n")


def test_UTF_8이_아닌_규칙_파일은_읽을_수_없다는_PluginError다(root: Path) -> None:
    path = root / RULES
    path.write_bytes(b'schema_version = "1"\n[common]\ndeny = ["\xff"]\n')

    with pytest.raises(PluginError) as caught:
        _plugins(root).read_rules()

    assert str(caught.value).startswith(f"운영자 파일을 읽을 수 없다: {path}\n")


# 거부하지 않는 것. 효과가 같거나 포함 관계이거나 차례가 뜻을 하나로 만든다.
ACCEPTED = (
    pytest.param('schema_version = "1"\n', Rules(), id="표가 하나도 없다"),
    pytest.param(
        'schema_version = "1"\n[common]\n[agents.calc]\n',
        Rules(agents={PluginName("calc"): _rule_set()}),
        id="세 배열이 모두 없다",
    ),
    pytest.param(
        'schema_version = "1"\n[common]\ndeny = ["rm", "rm"]\n',
        Rules(common=_rule_set(deny=(_bare("rm"),))),
        id="한 배열 안의 같은 줄 둘",
    ),
    pytest.param(
        'schema_version = "1"\n[common]\nask = ["everything:*", "everything:add"]\n',
        Rules(common=_rule_set(ask=(_whole("everything"), _one("everything", "add")))),
        id="서로 겹치는 줄",
    ),
    pytest.param(
        'schema_version = "1"\n[common]\ndeny = ["everything:add"]\nallow = ["everything:add"]\n',
        Rules(
            common=_rule_set(deny=(_one("everything", "add"),), allow=(_one("everything", "add"),))
        ),
        id="같은 도구가 deny 와 allow 에 함께",
    ),
    pytest.param(
        'schema_version = "1"\n[agents.ghost]\ndeny = ["rm"]\n',
        Rules(agents={PluginName("ghost"): _rule_set(deny=(_bare("rm"),))}),
        id="실재하지 않는 에이전트의 표",
    ),
    pytest.param(
        'schema_version = "1"\n[common]\ndeny = ["send.mail-2"]\n',
        Rules(common=_rule_set(deny=(_bare("send.mail-2"),))),
        id="점과 하이픈이 든 도구 이름",
    ),
    # 도구 이름의 별표는 패턴이다(Claude Code 와 같다). 막는 deny 와 묻는 ask 는 맨 이름도 받고,
    # allow 는 서버를 붙인 꼴의 도구 칸에서만 받는다.
    pytest.param(
        'schema_version = "1"\n[common]\ndeny = ["*", "send_*"]\n',
        Rules(common=_rule_set(deny=(_bare("*"), _bare("send_*")))),
        id="deny 의 맨 별표와 접두 패턴",
    ),
    pytest.param(
        'schema_version = "1"\n[agents.calc]\nask = ["*_mail", "everything:get_*"]\n',
        Rules(
            agents={
                PluginName("calc"): _rule_set(ask=(_bare("*_mail"), _one("everything", "get_*")))
            }
        ),
        id="ask 의 접미 패턴과 서버에 묶인 패턴",
    ),
    pytest.param(
        'schema_version = "1"\n[common]\nallow = ["everything:get_*"]\n',
        Rules(common=_rule_set(allow=(_one("everything", "get_*"),))),
        id="allow 의 서버에 묶인 패턴",
    ),
)


@pytest.mark.parametrize(("text", "expected"), ACCEPTED)
def test_규칙_파일이_받아들이는_모양은_거부하지_않고_그대로_읽는다(
    root: Path, text: str, expected: Rules
) -> None:
    _rules_file(root, text)

    assert _plugins(root).read_rules() == expected


def test_읽은_규칙은_자기_배열에서_몇째_줄인지를_든다(root: Path) -> None:
    """에이전트 표의 검사가 어긋난 줄을 `agents.calc.deny.2` 로 가리키려면 줄의 자리가 값에 남아야
    한다. 자리는 같음의 판정에 들지 않는다(앞 시험들이 `==` 로 읽은 규칙을 견준다)."""
    _rules_file(
        root,
        'schema_version = "1"\n'
        "[agents.calc]\n"
        'deny = ["rm", "everything:send_mail", "snd_*"]\n'
        'allow = ["everything:*"]\n',
    )

    calc = _plugins(root).read_rules().agents[PluginName("calc")]

    assert {rule.position: rule.tool for rule in calc.deny} == {
        0: "rm",
        1: "send_mail",
        2: "snd_*",
    }
    assert [rule.position for rule in calc.allow] == [0]


def test_한_배열_안의_같은_줄_둘은_하나로_합쳐지고_자리는_앞선_줄의_것이다(root: Path) -> None:
    _rules_file(root, 'schema_version = "1"\n[common]\ndeny = ["rm", "ls", "rm"]\n')

    deny = _plugins(root).read_rules().common.deny

    assert {rule.position: rule.tool for rule in deny} == {0: "rm", 1: "ls"}


# 깨진 파일. (본문, 문구에 들어야 할 칸의 자리, 오류 종류)
BROKEN_RULES = (
    pytest.param('[common]\ndeny = ["rm"]\n', "schema_version", "missing", id="형식 버전이 없다"),
    pytest.param('schema_version = "2"\n', "schema_version", "literal_error", id="모르는 버전"),
    pytest.param(
        'schema_version = "1"\n[common]\nallow = ["add"]\n',
        "common.allow.0",
        "string_pattern_mismatch",
        id="공통 표 allow 의 맨 이름",
    ),
    pytest.param(
        'schema_version = "1"\n[agents.calc]\nallow = ["everything:add", "add"]\n',
        "agents.calc.allow.1",
        "string_pattern_mismatch",
        id="에이전트 표 allow 의 맨 이름",
    ),
    pytest.param(
        'schema_version = "1"\n[common]\ndeny = ["a:b:c"]\n',
        "common.deny.0",
        "string_pattern_mismatch",
        id="콜론 둘",
    ),
    pytest.param(
        'schema_version = "1"\n[common]\ndeny = [":add"]\n',
        "common.deny.0",
        "string_pattern_mismatch",
        id="서버 조각이 비었다",
    ),
    pytest.param(
        'schema_version = "1"\n[common]\nask = ["everything:"]\n',
        "common.ask.0",
        "string_pattern_mismatch",
        id="도구 조각이 비었다",
    ),
    pytest.param(
        'schema_version = "1"\n[common]\ndeny = ["send mail"]\n',
        "common.deny.0",
        "string_pattern_mismatch",
        id="공백이 든 맨 이름",
    ),
    pytest.param(
        'schema_version = "1"\n[common]\ndeny = ["everything: add"]\n',
        "common.deny.0",
        "string_pattern_mismatch",
        id="공백이 든 서버에 묶인 도구",
    ),
    pytest.param(
        'schema_version = "1"\n[common]\ndeny = [""]\n',
        "common.deny.0",
        "string_pattern_mismatch",
        id="빈 줄",
    ),
    # 별표는 도구 이름의 패턴이다. 서버 칸은 패턴이 아니라 플러그인 이름이고, 열어 주는 allow 는
    # 맨 이름(별표 포함)을 받지 않는다.
    pytest.param(
        'schema_version = "1"\n[common]\nallow = ["*"]\n',
        "common.allow.0",
        "string_pattern_mismatch",
        id="allow 의 맨 별표",
    ),
    pytest.param(
        'schema_version = "1"\n[agents.calc]\nallow = ["send_*"]\n',
        "agents.calc.allow.0",
        "string_pattern_mismatch",
        id="allow 의 맨 접두 패턴",
    ),
    pytest.param(
        'schema_version = "1"\n[common]\ndeny = ["*:add"]\n',
        "common.deny.0",
        "string_pattern_mismatch",
        id="서버 칸의 별표",
    ),
    pytest.param(
        'schema_version = "1"\n[common]\nask = ["every*:add"]\n',
        "common.ask.0",
        "string_pattern_mismatch",
        id="서버 칸 안의 별표",
    ),
    pytest.param(
        'schema_version = "1"\n[common]\ndeny = ["Every_Thing:add"]\n',
        "common.deny.0",
        "string_pattern_mismatch",
        id="플러그인 이름 패턴을 어긴 서버",
    ),
    pytest.param(
        'schema_version = "1"\n[common]\ndeny = "rm"\n',
        "common.deny",
        "tuple_type",
        id="배열이 아닌 값",
    ),
    pytest.param(
        'schema_version = "1"\n[common]\ndeny = [1]\n',
        "common.deny.0",
        "string_type",
        id="문자열이 아닌 원소",
    ),
    pytest.param(
        'schema_version = "1"\nagent = ["calc"]\n',
        "agent",
        "extra_forbidden",
        id="맨 위의 모르는 키",
    ),
    pytest.param(
        'schema_version = "1"\n[common]\nforbid = ["rm"]\n',
        "common.forbid",
        "extra_forbidden",
        id="공통 표의 모르는 키",
    ),
    pytest.param(
        'schema_version = "1"\n[agents.calc]\ndisallow = ["rm"]\n',
        "agents.calc.disallow",
        "extra_forbidden",
        id="에이전트 표의 모르는 키",
    ),
    pytest.param(
        'schema_version = "1"\n[agent.calc]\ndeny = ["rm"]\n',
        "agent",
        "extra_forbidden",
        id="단수 agent 표",
    ),
    pytest.param(
        'schema_version = "1"\n[agents.MyAgent]\ndeny = ["rm"]\n',
        "agents.MyAgent.[key]",
        "string_pattern_mismatch",
        id="패턴을 어긴 에이전트 이름",
    ),
)


@pytest.mark.parametrize(("text", "place", "kind"), BROKEN_RULES)
def test_깨진_규칙_파일은_경로와_칸의_자리와_오류_종류를_든_PluginError다(
    root: Path, text: str, place: str, kind: str
) -> None:
    """실패를 기대하는 시험은 까닭을 단언한다. 자리와 종류가 문구에 든다."""
    path = _rules_file(root, text)

    with pytest.raises(PluginError) as caught:
        _plugins(root).read_rules()

    message = str(caught.value)
    assert message.startswith(f"운영자 파일이 깨졌다: {path}\n")
    assert f"{kind} ({place})" in message


@pytest.mark.parametrize(
    "text",
    (
        pytest.param('schema_version = "1"\n[common\n', id="표 머리가 닫히지 않았다"),
        pytest.param("", id="빈 파일"),
        pytest.param('schema_version = "1"\n[common]\ndeny = ["rm"\n', id="배열이 닫히지 않았다"),
        pytest.param('schema_version = "1"\n[common]\n[common]\n', id="표를 두 번 선언했다"),
    ),
)
def test_문법이_틀린_규칙_파일도_깨졌다는_PluginError다(root: Path, text: str) -> None:
    path = _rules_file(root, text)

    with pytest.raises(PluginError) as caught:
        _plugins(root).read_rules()

    assert str(caught.value).startswith(f"운영자 파일이 깨졌다: {path}\n")


def test_깨짐_문구는_모르는_키에_심은_값을_싣지_않는다(root: Path) -> None:
    """원칙 V. pydantic 의 `extra_forbidden` 문구는 값을 `input_value` 로 싣는다. 이 문구는 운영자
    면 500 봉투와 서버 기록으로 나간다. 칸의 이름(키)은 운영자가 어느 칸이 틀렸는지 알려고
    싣는다."""
    secret = "sk-ant-api03-SECRET"
    _rules_file(root, f'schema_version = "1"\n[agents.calc]\napi_key = "{secret}"\n')

    with pytest.raises(PluginError) as caught:
        _plugins(root).read_rules()

    assert "agents.calc.api_key" in str(caught.value)
    assert secret not in str(caught.value)


def test_깨짐_문구는_패턴을_어긴_규칙_줄의_값을_싣지_않는다(root: Path) -> None:
    """allow 의 맨 이름 같은 패턴 위반은 자리(`agents.calc.allow.0`)와 종류로 드러나고 그 줄의 값은
    싣지 않는다."""
    _rules_file(root, 'schema_version = "1"\n[agents.calc]\nallow = ["hunter2-token"]\n')

    with pytest.raises(PluginError) as caught:
        _plugins(root).read_rules()

    assert "string_pattern_mismatch (agents.calc.allow.0)" in str(caught.value)
    assert "hunter2-token" not in str(caught.value)


def test_깨짐의_PluginError는_검증_오류를_원인으로_잇지_않는다(root: Path) -> None:
    """`from error` 로 이으면 `ValidationError` 가 `__cause__` 에 남아 트레이스백 출력에 입력 값이
    실린다. 문구를 값 없이 만들어도 그 길이 열려 있으면 값이 샌다."""
    _rules_file(root, 'schema_version = "1"\n[agents.calc]\napi_key = "sk-ant-SECRET"\n')

    with pytest.raises(PluginError) as caught:
        _plugins(root).read_rules()

    printed = "".join(traceback.format_exception(caught.value))
    assert caught.value.__cause__ is None
    assert "sk-ant-SECRET" not in printed


def test_규칙_파일의_깨짐은_꺼진_집합을_읽는_길에_닿지_않는다(root: Path) -> None:
    """두 운영자 파일은 서로의 읽기를 막지 않는다. 파일 하나의 손상은 그 파일을 읽는 길에서만
    드러난다."""
    _rules_file(root, "깨진 파일")
    _operator_file(root, 'schema_version = "1"\nagent = ["calc"]\n')

    assert _plugins(root).read_disabled() == {_key(PluginKind.AGENT, "calc")}


def test_꺼진_집합의_깨짐_문구는_검증_오류_전문을_싣는_그대로다(root: Path) -> None:
    """`disabled.toml` 의 문구는 이 기능이 바꾸지 않는다. 규칙 파일의 문구만 값을 벗긴다. 이 틈
    (원칙 V, `adapters.md` 의 닫지 않은 잔여)을 닫는 변경은 이 시험을 값이 없는 쪽으로 뒤집는다."""
    _operator_file(root, 'schema_version = "1"\nunknown = "sk-ant-SECRET"\n')

    with pytest.raises(PluginError, match="sk-ant-SECRET"):
        _plugins(root).read_disabled()
