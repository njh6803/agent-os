"""원칙 IV: 플러그인은 `agent_os.sdk` 만 import 한다. 이 테스트가 그 절의 판정자다.

import-linter 는 `root_packages`(`agent_os`) 안만 보고, 플러그인은 합성 이름
`agent_os_plugins.<name>.<module>` 로 동적 로드되어 그 그래프에 없다. 그래서 헌법이
"import-linter 가 판정한다" 고 적은 자리 중 이 절은 2026-09-28 까지 아무것도 재지 않았다
(하네스 감사, ADR 0018). 판정은 AST 다 — 플러그인을 import 하면 그 코드가 실행된다.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGINS = ROOT / "plugins"
ALLOWED = "agent_os.sdk"


def agent_os_imports(source: str) -> list[str]:
    """소스가 import 하는 `agent_os` 아래 모듈들. `from agent_os import sdk` 는 `agent_os.sdk`."""
    names: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.extend(a.name for a in node.names if a.name.split(".")[0] == "agent_os")
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module is not None:
            if node.module == "agent_os":
                names.extend(f"agent_os.{a.name}" for a in node.names)
            elif node.module.split(".")[0] == "agent_os":
                names.append(node.module)
    return names


def violations(paths: Iterable[Path]) -> list[tuple[Path, str]]:
    """(파일, 모듈) 중 `agent_os.sdk` 와 그 하위가 아닌 것."""
    found: list[tuple[Path, str]] = []
    for path in paths:
        for name in agent_os_imports(path.read_text(encoding="utf-8")):
            if name != ALLOWED and not name.startswith(ALLOWED + "."):
                found.append((path, name))
    return found


def _plugin_sources() -> list[Path]:
    return sorted(PLUGINS.rglob("*.py"))


def test_플러그인_파일을_하나는_읽는다() -> None:
    """읽은 것이 없는데 위반 0 으로 초록이 되는 것을 막는다(test_manifest.py 와 같은 장치)."""
    assert _plugin_sources()


def test_플러그인은_sdk만_import한다() -> None:
    assert violations(_plugin_sources()) == []


def test_판정자가_core_와_adapters_import_를_잡는다(tmp_path: Path) -> None:
    """변이. 이 테스트가 없으면 위의 초록이 무엇을 재는지 아무도 모른다."""
    path = tmp_path / "agent.py"
    path.write_text(
        "from agent_os.sdk import AgentContext, Event\n"
        "from agent_os import sdk\n"
        "from agent_os.core.run import run\n"
        "import agent_os.adapters.jsonl\n"
        "import json\n",
        encoding="utf-8",
    )

    assert [name for _, name in violations([path])] == [
        "agent_os.core.run",
        "agent_os.adapters.jsonl",
    ]
