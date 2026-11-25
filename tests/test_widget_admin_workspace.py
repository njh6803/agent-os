"""둘째 설치 묶음 `widget-admin` 이 루트 `pyproject.toml` 의 여섯 자리에 모두 올라 있는가(ADR 0064).

여섯 자리 가운데 하나라도 빠지면 조용히 틀린다. 멤버 선언이 없으면 묶음이 서지 않고, 개발 묶음의
줄이 없으면 `uv sync --frozen` 이 멤버를 깔지 않아 CI 와 러너의 검사가 멤버를 보지 못한다. ruff 의
`src` 가 없으면 import 정렬이 멤버를 제 것이 아닌 패키지로 읽고, pyright 의 `include` 가 없으면
멤버의 코드는 타입 검사를 받지 않으며, `extraPaths` 가 한쪽만 있으면 다른 패키지의 import 마다
스텁 없음이 난다. import-linter 의 두 설정이 없으면 두 패키지가 서로를 import 해도 빨개지지 않는다.

저장소 상태를 재는 시험이다(`.claude/rules/tests.md`). 이 저장소가 지금 통과함을 재는 시험 하나와,
위반을 잡는지 보는 변이 시험이다. 변이는 읽은 글에서 한 자리를 바꾼 사본을 같은 읽기 함수에 넣어
본다. 읽는 함수가 비어 읽으면 위반 0 으로 조용히 초록이 되므로 이 저장소의 시험이 읽은 값이 비지
않았음도 단언한다.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

ROOT = Path(__file__).resolve().parent.parent


class _Reading(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)


class _Workspace(_Reading):
    members: tuple[str, ...] = ()


class _Uv(_Reading):
    workspace: _Workspace = _Workspace()
    sources: dict[str, dict[str, bool]] = {}


class _Ruff(_Reading):
    src: tuple[str, ...] = ()


class _Pyright(_Reading):
    include: tuple[str, ...] = ()
    extra_paths: tuple[str, ...] = Field(default=(), alias="extraPaths")


class _Contract(_Reading):
    type: str = ""
    modules: tuple[str, ...] = ()


class _ImportLinter(_Reading):
    root_packages: tuple[str, ...] = ()
    contracts: tuple[_Contract, ...] = ()


class _Tool(_Reading):
    uv: _Uv = _Uv()
    ruff: _Ruff = _Ruff()
    pyright: _Pyright = _Pyright()
    importlinter: _ImportLinter = _ImportLinter()


class _Root(_Reading):
    tool: _Tool = _Tool()
    dependency_groups: dict[str, tuple[str, ...]] = Field(default={}, alias="dependency-groups")


_ROOT = TypeAdapter(_Root)

PACKAGE = "widget-admin"
SOURCE = "widget-admin/src"


def read_root(text: str) -> _Root:
    """루트 `pyproject.toml` 의 글에서 이 시험이 보는 자리만 읽는다(질의)."""
    return _ROOT.validate_python(tomllib.loads(text))


def workspace_problems(text: str) -> list[str]:
    """여섯 자리 가운데 빠진 곳의 까닭들(질의). 비어 있으면 모두 올라 있다.

    여섯 자리는 멤버 선언과 소스 표(둘이 한 자리), 개발 묶음, ruff 의 `src`, pyright 의 `include`,
    pyright 의 `extraPaths`, import-linter 의 두 설정(루트 패키지와 독립 계약)이고, 아래는 그것을
    여덟 항목으로 나누어 본다.
    """
    root = read_root(text)
    tool = root.tool
    problems: list[str] = []
    if PACKAGE not in tool.uv.workspace.members:
        problems.append("[tool.uv.workspace] 의 members 에 widget-admin 이 없다")
    if tool.uv.sources.get(PACKAGE) != {"workspace": True}:
        problems.append("[tool.uv.sources] 에 widget-admin = { workspace = true } 가 없다")
    if PACKAGE not in root.dependency_groups.get("dev", ()):
        problems.append("[dependency-groups] 의 dev 에 widget-admin 이 없다")
    if SOURCE not in tool.ruff.src:
        problems.append("[tool.ruff] 의 src 에 widget-admin/src 가 없다")
    if SOURCE not in tool.pyright.include:
        problems.append("[tool.pyright] 의 include 에 widget-admin/src 가 없다")
    if not {"src", SOURCE} <= set(tool.pyright.extra_paths):
        problems.append("[tool.pyright] 의 extraPaths 에 src 와 widget-admin/src 둘이 없다")
    if not {"agent_os", "widget_admin"} <= set(tool.importlinter.root_packages):
        problems.append("[tool.importlinter] 의 root_packages 에 두 패키지가 없다")
    independence = [c for c in tool.importlinter.contracts if c.type == "independence"]
    if not any(c.modules == ("agent_os", "widget_admin") for c in independence):
        problems.append("import-linter 에 agent_os 와 widget_admin 의 independence 계약이 없다")
    return problems


def _root_text() -> str:
    return (ROOT / "pyproject.toml").read_text(encoding="utf-8")


def test_이_저장소의_루트_pyproject는_위젯_관리_묶음을_여섯_자리에_올렸다() -> None:
    text = _root_text()
    root = read_root(text)

    # 읽은 값이 비면 위반 0 으로 조용히 초록이 된다. 읽었다는 것을 먼저 본다.
    assert root.tool.uv.workspace.members
    assert root.tool.importlinter.contracts
    assert workspace_problems(text) == []


def test_위젯_관리_묶음의_폴더와_패키지가_있다() -> None:
    assert (ROOT / "widget-admin" / "pyproject.toml").is_file()
    assert (ROOT / "widget-admin" / "src" / "widget_admin" / "__init__.py").is_file()


# 글에서 바꿀 한 자리와 그 자리를 잡는 까닭. 바꾸는 글은 이 저장소의 루트 `pyproject.toml` 에 그대로
# 있어야 하고, 없으면 변이가 아무것도 바꾸지 않은 채 초록이 되므로 시험이 먼저 그것을 본다.
MUTATIONS = {
    "멤버 선언": (
        'members = ["widget-admin"]',
        "members = []",
        "[tool.uv.workspace] 의 members 에 widget-admin 이 없다",
    ),
    "소스 표": (
        "widget-admin = { workspace = true }",
        "",
        "[tool.uv.sources] 에 widget-admin = { workspace = true } 가 없다",
    ),
    "개발 묶음의 줄": (
        '    "widget-admin",\n]',
        "]",
        "[dependency-groups] 의 dev 에 widget-admin 이 없다",
    ),
    "ruff 의 src": (
        'src = ["src", "tests", "widget-admin/src"]',
        'src = ["src", "tests"]',
        "[tool.ruff] 의 src 에 widget-admin/src 가 없다",
    ),
    "pyright 의 include": (
        'include = ["src", "widget-admin/src", "tests", "tools"]',
        'include = ["src", "tests", "tools"]',
        "[tool.pyright] 의 include 에 widget-admin/src 가 없다",
    ),
    "pyright 의 extraPaths 의 멤버": (
        'extraPaths = ["src", "widget-admin/src"]',
        'extraPaths = ["src"]',
        "[tool.pyright] 의 extraPaths 에 src 와 widget-admin/src 둘이 없다",
    ),
    "pyright 의 extraPaths 의 루트": (
        'extraPaths = ["src", "widget-admin/src"]',
        'extraPaths = ["widget-admin/src"]',
        "[tool.pyright] 의 extraPaths 에 src 와 widget-admin/src 둘이 없다",
    ),
    "import-linter 의 루트 패키지": (
        'root_packages = ["agent_os", "widget_admin"]',
        'root_packages = ["agent_os"]',
        "[tool.importlinter] 의 root_packages 에 두 패키지가 없다",
    ),
    "독립 계약의 종류": (
        'type = "independence"',
        'type = "forbidden"',
        "import-linter 에 agent_os 와 widget_admin 의 independence 계약이 없다",
    ),
    "독립 계약의 대상": (
        'modules = ["agent_os", "widget_admin"]',
        'modules = ["agent_os"]',
        "import-linter 에 agent_os 와 widget_admin 의 independence 계약이 없다",
    ),
}


@pytest.mark.parametrize("name", MUTATIONS)
def test_한_자리를_바꾼_사본은_그_자리만_잡는다(name: str) -> None:
    old, new, problem = MUTATIONS[name]
    text = _root_text()
    assert text.count(old) == 1, f"바꿀 글이 루트 pyproject.toml 에 하나가 아니다: {old}"

    assert workspace_problems(text.replace(old, new)) == [problem]
