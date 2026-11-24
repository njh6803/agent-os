"""uv 워크스페이스로 설치 묶음을 둘(`agent-os`, `widget-admin`)로 나눌 때 검사 도구, 시험, 명령,
이미지 빌드가 서는지 잰다. 명세 `.scratch/widget-admin-server/spec.md` 가 근거로 든다.

사본 나무. 저장소의 기준 커밋(`BASE_COMMIT`, 명세를 쓴 브랜치의 기준인 origin/dev 의
`7770ac0c1`)을 `git archive` 로 빈 폴더에 풀고, 이 폴더의 `member/` 를
`widget-admin/` 에, `tests/` 를 `tests/widget_admin/` 에, `images/` 를 `probe-images/` 에
옮긴다(`.tmpl` 을 뗀다). 장난감 파일을 `.tmpl` 로 두는 까닭은 저장소의 ruff 가 이 폴더를 볼 때
`widget_admin` 을 첫째 묶음으로 알지 못해 import 순서 판정이 사본 나무와 갈리기 때문이다. 루트
`pyproject.toml` 은 갈래마다 원본에서 다시 지어 쓴다(`Tree.configure`). `HEAD` 가 아니라 기준 커밋을
푸는 까닭은, 구현 티켓이 루트 `pyproject.toml` 에 워크스페이스를 들인 뒤에 다시 돌려도 사본 나무가
고치기 전의 판에서 시작해 대조 갈래가 서게 하려는 것이다. 고치는 자리는 여섯이다.
워크스페이스 멤버와 원천, 개발 묶음의 멤버, ruff 의 `src`, pyright 의 `include` 와 `extraPaths`
(루트의 `src` 와 멤버의 `src` 를 함께 적는다), import-linter 의 `root_packages` 와 독립 계약.

갈래. `sync` 는 개발 묶음에 멤버를 넣지 않은 대조(CI 꼴 `uv sync --frozen` 뒤 멤버가 없는지,
`--all-packages` 면 있는지)와 넣은 판(잠금의 차이, `uv lock --check`, `uv sync --frozen` 뒤 멤버가
있는지)이다. `tools` 는 넣은 판에서 ruff 둘, pyright(러너처럼 리눅스 플랫폼으로도 한 번 더),
import-linter, 타입 우회 검사를 돌고, 각각에 양성 대조(심은 오류를 잡는지)를 두며, ruff 의 `src` 와
pyright 의 `include` 에는 멤버를 넣지 않은 대조를, pyright 의 `extraPaths` 에는 적지 않은 대조와
멤버만 적은 대조를 둔다. ruff 는 `-v` 가 찍는 묶음 판정 줄
(`Categorized 'widget_admin…' as …`)로 `widget_admin` 이 어느 묶음에 왜 들었는지를 본다. `pytest` 는
위젯 시험이 공유 도우미로 `widget_admin` 접두의 데이터베이스를 받는지, agent_os 의 데이터베이스
시험과 한 실행(`-n 2`)에 함께 도는지, 판 번호 시험이 그대로인지다. `command` 는 e2e 준비처럼 임시
폴더에서 `python -m widget_admin.main migrate` 와 `widget-admin migrate` 가 도는지다. `images` 는
위젯 관리 서버 이미지(멤버 하나만 깔고 판 번호를 넣는다)와 serve 이미지의 파이썬 단계(지금 꼴의
대조와 멤버의 `pyproject.toml` 을 들인 판)를 짓고 안을 본다.

표지. 회차마다 재려는 상황이 났다는 관찰(출력의 집계 줄, 심은 파일의 경로, 찍은 데이터베이스 이름,
`PROBE-` 로 시작하는 줄)을 보고 `Rounds` 로 센다. 표지가 없는 회차가 있으면 1 로 끝난다.

쓰임. 저장소 루트에서
    uv run python .scratch/widget-admin-server/probes/uv_workspace/run.py <없거나 빈 폴더의 절대
    경로>
`--sections sync,tools` 처럼 고를 수 있다(`sync` 가 뒤의 갈래가 쓰는 가상 환경을 짓는다). 테스트
컨테이너(`docker compose -f compose.test.yaml up -d --wait`)와 도는 Docker 데몬이 있어야 한다. 이
프로브는 폴더를 지우지 않는다. 다 본 사본 나무는 손으로 지운다. 명령의 출력은 사본 나무의
`.probe-logs/` 에 남는다.

못 보는 것. CI 의 리눅스와 CI 가 받는 uv 판(`setup-uv` 에 판을 적지 않았다), pre-commit 러너
(`tools/run_checks.py`)를 통째로 도는 것, 출시 도구(`tools/release.py`, `tools/release_ci.py`,
bake)는 돌리지 않는다. 장난감은 명세가 정할 표와 경로의 모양을 따르지 않는다.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from pathlib import Path
from urllib.parse import urlsplit

REPO = Path(__file__).resolve().parents[4]
BASE_COMMIT = "7770ac0c12a061b5dd47149f9989c8af6efc9330"
sys.path.insert(0, str(REPO))

from tools.probe_kit import Rounds  # noqa: E402

HERE = Path(__file__).resolve().parent
APP_VERSION = "0.1.0-rc.1"
TIMEOUT = 900.0
SECTIONS = ("sync", "tools", "pytest", "command", "images")
CONTRACT = "agent_os and widget_admin are independent (ADR 0064)"
UV_IMAGE = (
    "ghcr.io/astral-sh/uv@sha256:5cc1805e2426484abca4ad46ea783bab281fdb225fd82d8ce6d66a81254bac85"
)
PYTHON_IMAGE = "python@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b"
TAIL = f"""
[[tool.importlinter.contracts]]
name = "{CONTRACT}"
type = "independence"
modules = ["agent_os", "widget_admin"]

[tool.uv.workspace]
members = ["widget-admin"]

[tool.uv.sources]
widget-admin = {{ workspace = true }}
"""
IMAGE_CHECK = """
import importlib.metadata as m, importlib.util as u, json, os, sys
found = {}
for name in ("agent-os", "widget-admin"):
    try:
        found[name] = m.version(name)
    except m.PackageNotFoundError:
        found[name] = None
found["agent_os"] = u.find_spec("agent_os") is not None
found["widget_admin"] = u.find_spec("widget_admin") is not None
found["langchain_core"] = u.find_spec("langchain_core") is not None
found["dists"] = len(list(m.distributions()))
found["widget_admin_script"] = os.path.exists(os.path.join(sys.prefix, "bin", "widget-admin"))
if found["widget_admin"]:
    from widget_admin.database import revisions
    found["revisions"] = revisions()
print("PROBE-CHECK " + json.dumps(found, sort_keys=True))
"""
SPEC_CHECK = (
    "import importlib.util as u; s = u.find_spec('widget_admin'); "
    "print('PROBE-SPEC', s.origin if s else None)"
)


class Tree:
    """사본 나무 하나와 그 안에서 명령을 치는 길."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.logs = root / ".probe-logs"
        self.count = 0
        self.original = ""

    def run(
        self,
        label: str,
        args: list[str],
        *,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        merged = {**os.environ, "PYTHONUTF8": "1", **(env or {})}
        # 저장소의 가상 환경을 가리키는 값이 사본 나무의 uv 와 파이썬에 새지 않게 한다
        merged.pop("VIRTUAL_ENV", None)
        found = subprocess.run(
            args,
            cwd=cwd or self.root,
            env=merged,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIMEOUT,
            check=False,
        )
        self.count += 1
        self.logs.mkdir(exist_ok=True)
        log = self.logs / f"{self.count:02d}-{label}.log"
        log.write_text(
            f"$ {' '.join(args)}\n종료 {found.returncode}\n--- stdout\n{found.stdout}"
            f"\n--- stderr\n{found.stderr}",
            encoding="utf-8",
        )
        return found

    def python(self) -> Path:
        windows = self.root / ".venv" / "Scripts" / "python.exe"
        return windows if windows.exists() else self.root / ".venv" / "bin" / "python"

    def script(self, name: str) -> Path:
        windows = self.root / ".venv" / "Scripts" / f"{name}.exe"
        return windows if windows.exists() else self.root / ".venv" / "bin" / name

    def configure(
        self,
        *,
        dev_member: bool = True,
        ruff_src: bool = True,
        pyright_include: bool = True,
        pyright_extra_paths: tuple[str, ...] = ("src", "widget-admin/src"),
    ) -> None:
        text = self.original
        if dev_member:
            text = _once(
                text,
                '    "pytest-xdist>=3.8.0",\n]',
                '    "pytest-xdist>=3.8.0",\n    "widget-admin",\n]',
            )
        if ruff_src:
            text = _once(
                text, 'src = ["src", "tests"]', 'src = ["src", "widget-admin/src", "tests"]'
            )
        if pyright_include:
            text = _once(
                text,
                'include = ["src", "tests", "tools"]',
                'include = ["src", "widget-admin/src", "tests", "tools"]',
            )
        if pyright_extra_paths:
            # pyright 는 extraPaths 가 없을 때만 루트의 `src` 를 저절로 제 코드의 자리로 찾는다.
            # 멤버의 `src` 는 적어 주지 않으면 설치된 라이브러리로 읽어 strict 의
            # reportMissingTypeStubs 를 내고, 멤버만 적으면 이번에는 agent_os 가 그렇게 된다
            listed = ", ".join(f'"{path}"' for path in pyright_extra_paths)
            text = _once(
                text,
                'typeCheckingMode = "strict"\n',
                f'typeCheckingMode = "strict"\nextraPaths = [{listed}]\n',
            )
        text = _once(
            text, 'root_packages = ["agent_os"]', 'root_packages = ["agent_os", "widget_admin"]'
        )
        with (self.root / "pyproject.toml").open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(text + TAIL)

    def plant(self, relative: str, body: str) -> Path:
        path = self.root / relative
        path.write_text(body, encoding="utf-8")
        return path


def _once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"pyproject.toml 에서 {old!r} 가 한 번이 아니다")
    return text.replace(old, new)


def _packages(lock_text: str) -> set[tuple[str, str]]:
    document = tomllib.loads(lock_text)
    return {(str(item["name"]), str(item.get("version", ""))) for item in document["package"]}


def _spec_line(output: str) -> str | None:
    for line in output.splitlines():
        if line.startswith("PROBE-SPEC "):
            return line.removeprefix("PROBE-SPEC ")
    return None


def _check_line(output: str) -> dict[str, object] | None:
    for line in output.splitlines():
        if line.startswith("PROBE-CHECK "):
            loaded: object = json.loads(line.removeprefix("PROBE-CHECK "))
            if isinstance(loaded, dict):
                return {str(key): value for key, value in loaded.items()}
    return None


def _pyright_diagnostics(output: str) -> tuple[int, list[str], list[str]] | None:
    """`--outputjson` 의 오류 수, 진단마다 `파일:규칙`, 진단의 문구. JSON 이 아니면 None."""
    start = output.find("{")
    if start < 0:
        return None
    loaded: object = json.loads(output[start:])
    if not isinstance(loaded, dict):
        return None
    summary = loaded.get("summary")
    diagnostics = loaded.get("generalDiagnostics")
    if not isinstance(summary, dict) or not isinstance(diagnostics, list):
        return None
    errors = summary.get("errorCount")
    found: list[str] = []
    messages: list[str] = []
    for item in diagnostics:
        if isinstance(item, dict):
            found.append(f"{item.get('file')}:{item.get('rule')}")
            messages.append(str(item.get("message")))
    return (errors if isinstance(errors, int) else -1), found, messages


def _categories(output: str, module: str) -> list[str]:
    """ruff `-v` 가 찍는 isort 묶음 판정 줄에서 `module` 의 묶음과 근거(`as ...` 뒤).

    줄의 모양은 `Categorized 'widget_admin.app' as Known(FirstParty) (SourceMatch("..."))` 다
    (ruff 0.16.8 의 출력을 사본 나무에서 손으로 봤다).
    """
    marker = f"Categorized '{module}"
    found: set[str] = set()
    for line in output.splitlines():
        at = line.find(marker)
        if at >= 0:
            rest = line[at + len(marker) :]
            found.add(rest[rest.find(" as ") + 4 :] if " as " in rest else rest)
    return sorted(found)


def build_tree(target: Path) -> Tree:
    if not target.is_absolute():
        raise SystemExit(f"사본 나무의 자리는 절대 경로여야 한다: {target}")
    if target.exists() and any(target.iterdir()):
        raise SystemExit(f"사본 나무의 자리가 비어 있지 않다(이 프로브는 지우지 않는다): {target}")
    target.mkdir(parents=True, exist_ok=True)
    archive = subprocess.run(
        ["git", "-C", str(REPO), "archive", "--format=tar", BASE_COMMIT],
        capture_output=True,
        timeout=300,
        check=True,
    )
    with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as bundle:
        bundle.extractall(target, filter="data")
    for source, place in (("member", "widget-admin"), ("tests", "tests/widget_admin")):
        for path in (HERE / source).rglob("*.tmpl"):
            relative = path.relative_to(HERE / source).with_suffix("")
            destination = target / place / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
    shutil.copytree(HERE / "images", target / "probe-images")
    tree = Tree(target)
    tree.original = (target / "pyproject.toml").read_text(encoding="utf-8")
    return tree


def sync_section(tree: Tree, rounds: Rounds) -> None:
    original_lock = (tree.root / "uv.lock").read_text(encoding="utf-8")

    with rounds.round("대조: 개발 묶음에 멤버를 넣지 않고 uv sync --frozen") as current:
        tree.configure(dev_member=False)
        locked = tree.run("lock-control", ["uv", "lock"])
        synced = tree.run("sync-control", ["uv", "sync", "--frozen"])
        spec = _spec_line(tree.run("spec-control", [str(tree.python()), "-c", SPEC_CHECK]).stdout)
        current.mark(
            measured=locked.returncode == 0 and synced.returncode == 0 and spec is not None,
            result=f"widget_admin 자리 {spec}",
        )

    with rounds.round("대조: 같은 설정에서 uv sync --frozen --all-packages") as current:
        synced = tree.run("sync-all", ["uv", "sync", "--frozen", "--all-packages"])
        spec = _spec_line(tree.run("spec-all", [str(tree.python()), "-c", SPEC_CHECK]).stdout)
        current.mark(
            measured=synced.returncode == 0 and spec is not None,
            result=f"widget_admin 자리 {'멤버의 src' if spec and 'widget-admin' in spec else spec}",
        )

    with rounds.round("잠금: 개발 묶음에 멤버를 넣고 uv lock") as current:
        tree.configure()
        locked = tree.run("lock", ["uv", "lock"])
        new_lock = (tree.root / "uv.lock").read_text(encoding="utf-8")
        added = sorted(_packages(new_lock) - _packages(original_lock))
        removed = sorted(_packages(original_lock) - _packages(new_lock))
        members = tomllib.loads(new_lock).get("manifest", {}).get("members")
        current.mark(
            measured=locked.returncode == 0 and ("widget-admin", "0.0.0") in added,
            result=f"더해진 {added}, 빠진 {removed}, manifest.members {members}",
        )

    with rounds.round("잠금 검사: uv lock --check") as current:
        checked = tree.run("lock-check", ["uv", "lock", "--check"])
        current.mark(
            measured="Resolved" in checked.stderr + checked.stdout,
            result=f"종료 {checked.returncode}",
        )

    with rounds.round("CI 꼴: uv sync --frozen 뒤 멤버") as current:
        synced = tree.run("sync", ["uv", "sync", "--frozen"])
        spec = _spec_line(tree.run("spec", [str(tree.python()), "-c", SPEC_CHECK]).stdout)
        script = tree.script("widget-admin").exists()
        current.mark(
            measured=synced.returncode == 0 and spec is not None,
            result=(
                f"widget_admin 자리 {'멤버의 src' if spec and 'widget-admin' in spec else spec},"
                f" widget-admin 명령 {'있음' if script else '없음'}"
            ),
        )


def tools_section(tree: Tree, rounds: Rounds) -> None:
    with rounds.round("ruff check .") as current:
        found = tree.run("ruff-check", ["uv", "run", "ruff", "check", "."])
        current.mark(
            measured="All checks passed!" in found.stdout or "Found" in found.stdout,
            result=f"종료 {found.returncode}",
        )

    with rounds.round("ruff format --check .") as current:
        found = tree.run("ruff-format", ["uv", "run", "ruff", "format", "--check", "."])
        current.mark(
            measured="already formatted" in found.stdout, result=f"종료 {found.returncode}"
        )

    toy = "tests/widget_admin/test_settings.py"
    for label, ruff_src in (
        ("ruff 의 묶음 판정: src 에 멤버를 넣은 판", True),
        ("대조: ruff 의 src 에 멤버를 넣지 않으면", False),
    ):
        with rounds.round(label) as current:
            tree.configure(ruff_src=ruff_src)
            # 캐시가 맞으면 ruff 는 그 파일을 다시 판정하지 않아 묶음 판정 줄을 찍지 않는다
            found = tree.run(
                "ruff-categories",
                ["uv", "run", "--frozen", "ruff", "check", "--no-cache", "-v", toy],
            )
            tree.configure()
            categories = _categories(found.stdout + found.stderr, "widget_admin")
            unsorted = "unsorted-imports" in found.stdout
            current.mark(
                measured=bool(categories),
                result=f"widget_admin 의 묶음 {categories}, import 순서 지적 {unsorted}",
            )

    for label, extra in (
        ("pyright", []),
        ("pyright --pythonplatform Linux", ["--pythonplatform", "Linux"]),
    ):
        with rounds.round(label) as current:
            found = tree.run("pyright", ["uv", "run", "pyright", "--outputjson", *extra])
            parsed = _pyright_diagnostics(found.stdout)
            current.mark(
                measured=parsed is not None,
                result=f"오류 {parsed[0]}, 진단 {parsed[1][:5]}" if parsed else "",
            )

    for label, extra_paths, module in (
        ("대조: pyright 의 extraPaths 를 적지 않으면", (), "widget_admin"),
        ("대조: pyright 의 extraPaths 에 멤버만 적으면", ("widget-admin/src",), "agent_os"),
    ):
        with rounds.round(label) as current:
            tree.configure(pyright_extra_paths=extra_paths)
            found = tree.run(
                "pyright-extra-control", ["uv", "run", "--frozen", "pyright", "--outputjson"]
            )
            tree.configure()
            parsed = _pyright_diagnostics(found.stdout)
            stubs = (
                [text for text in parsed[2] if f'Stub file not found for "{module}' in text]
                if parsed
                else []
            )
            errors = parsed[0] if parsed else None
            current.mark(
                measured=bool(stubs),
                result=f"오류 {errors}, {module} 의 스텁 없음 진단 {len(stubs)}",
            )

    planted_error = tree.plant(
        "widget-admin/src/widget_admin/planted_error.py", 'value: int = "글"\n'
    )
    with rounds.round("pyright 양성 대조: 멤버에 심은 타입 오류") as current:
        found = tree.run("pyright-planted", ["uv", "run", "pyright", "--outputjson"])
        parsed = _pyright_diagnostics(found.stdout)
        hits = [item for item in parsed[1] if "planted_error.py" in item] if parsed else []
        current.mark(measured=bool(hits), result=f"잡은 진단 {hits}")

    with rounds.round("대조: pyright 의 include 에 멤버를 넣지 않으면") as current:
        tree.configure(pyright_include=False)
        found = tree.run("pyright-control", ["uv", "run", "--frozen", "pyright", "--outputjson"])
        tree.configure()
        parsed = _pyright_diagnostics(found.stdout)
        hits = [item for item in parsed[1] if "planted_error.py" in item] if parsed else []
        caught = "잡았다" if hits else "못 잡았다"
        current.mark(
            measured=parsed is not None,
            result=f"심은 오류 {caught}, 오류 {parsed[0] if parsed else None}",
        )
    planted_error.unlink()

    with rounds.round("lint-imports") as current:
        found = tree.run("lint-imports", ["uv", "run", "lint-imports"])
        kept = [line for line in found.stdout.splitlines() if line.startswith("Contracts:")]
        current.mark(
            measured=bool(kept) and f"{CONTRACT} KEPT" in found.stdout,
            result=f"종료 {found.returncode}, {kept}",
        )

    for label, relative, body, edge in (
        (
            "lint-imports 양성 대조: 멤버가 agent_os 를 import",
            "widget-admin/src/widget_admin/planted_import.py",
            "import agent_os  # noqa: F401\n",
            "widget_admin.planted_import -> agent_os",
        ),
        (
            "lint-imports 양성 대조: agent_os 가 멤버를 import",
            "src/agent_os/planted_import.py",
            "import widget_admin  # noqa: F401\n",
            "agent_os.planted_import -> widget_admin",
        ),
    ):
        planted = tree.plant(relative, body)
        with rounds.round(label) as current:
            found = tree.run("lint-imports-planted", ["uv", "run", "lint-imports"])
            current.mark(
                measured=f"{CONTRACT} BROKEN" in found.stdout and edge in found.stdout,
                result=f"종료 {found.returncode}",
            )
        planted.unlink()

    with rounds.round("타입 우회 검사") as current:
        found = tree.run("escapes", ["uv", "run", "python", "tools/check_type_escapes.py"])
        current.mark(measured=found.returncode == 0 and found.stdout.strip() == "", result="0건")

    planted = tree.plant(
        "widget-admin/src/widget_admin/planted_escape.py",
        "from typing import Any\n\nvalue: Any = 1\n",
    )
    with rounds.round("타입 우회 검사 양성 대조: 멤버에 심은 Any") as current:
        found = tree.run("escapes-planted", ["uv", "run", "python", "tools/check_type_escapes.py"])
        hits = [
            line
            for line in found.stdout.splitlines()
            if line.startswith("widget-admin/src/widget_admin/planted_escape.py:")
        ]
        current.mark(measured=bool(hits), result=f"잡은 줄 {len(hits)}")
    planted.unlink()


def pytest_section(tree: Tree, rounds: Rounds) -> None:
    pytest = ["uv", "run", "pytest", "-q", "-p", "no:cacheprovider"]
    with rounds.round("pytest: 위젯 시험이 공유 도우미로 데이터베이스를 받는다") as current:
        found = tree.run("pytest-widget", [*pytest, "-s", "tests/widget_admin"])
        names = [line.split()[1] for line in found.stdout.splitlines() if "PROBE-DATABASE" in line]
        current.mark(
            measured=bool(names) and "1 passed" in found.stdout,
            result=f"이름의 머리 {[name[:18] for name in names]}",
        )

    with rounds.round(
        "pytest: 위젯 시험과 agent_os 의 데이터베이스 시험을 한 실행에 -n 2"
    ) as current:
        found = tree.run(
            "pytest-both",
            [*pytest, "-n", "2", "tests/widget_admin", "tests/test_migrate_command.py"],
        )
        tail = found.stdout.strip().splitlines()[-1:] if found.stdout.strip() else []
        current.mark(
            measured=bool(tail) and "passed" in tail[0],
            result=f"종료 {found.returncode}, {tail}",
        )

    with rounds.round("pytest: 판 번호 시험") as current:
        found = tree.run("pytest-version", [*pytest, "tests/test_repo_version.py"])
        lock = tomllib.loads((tree.root / "uv.lock").read_text(encoding="utf-8"))
        own = [
            (item["name"], item["version"])
            for item in lock["package"]
            if item["name"] in ("agent-os", "widget-admin")
        ]
        current.mark(measured="3 passed" in found.stdout, result=f"잠금의 자기 항목 {own}")


def command_section(tree: Tree, rounds: Rounds) -> None:
    created = tree.run(
        "database-create",
        ["uv", "run", "python", "tools/database_for_tests.py", "create", "widget_admin"],
    )
    address = created.stdout.strip()
    name = urlsplit(address).path.lstrip("/") if created.returncode == 0 else ""
    work = Path(tempfile.mkdtemp(prefix="uv_workspace_probe_cwd_"))
    env = {"WIDGET_ADMIN_DATABASE_URL": address}
    for label, args in (
        (
            "임시 폴더에서 python -m widget_admin.main migrate",
            [str(tree.python()), "-m", "widget_admin.main", "migrate"],
        ),
        (
            "임시 폴더에서 widget-admin migrate(두 번째)",
            [str(tree.script("widget-admin")), "migrate"],
        ),
    ):
        with rounds.round(label) as current:
            if name == "":
                raise RuntimeError("테스트 데이터베이스를 만들지 못했다")
            found = tree.run("migrate", args, cwd=work, env=env)
            current.mark(measured="표를 올렸다" in found.stdout, result=f"종료 {found.returncode}")
    if name != "":
        tree.run(
            "database-drop", ["uv", "run", "python", "tools/database_for_tests.py", "drop", name]
        )
    work.rmdir()


def _build(tree: Tree, label: str, dockerfile: str, tag: str) -> tuple[bool, str]:
    tree.run(f"rmi-{label}", ["docker", "image", "rm", "-f", tag])
    built = tree.run(
        f"build-{label}",
        [
            "docker",
            "build",
            "--progress=plain",
            "-f",
            f"probe-images/{dockerfile}",
            "--build-arg",
            f"APP_VERSION={APP_VERSION}",
            "-t",
            tag,
            ".",
        ],
    )
    present = tree.run(f"inspect-{label}", ["docker", "image", "inspect", tag]).returncode == 0
    return built.returncode == 0 and present, built.stdout + built.stderr


def _inside(tree: Tree, label: str, tag: str) -> dict[str, object] | None:
    found = tree.run(
        f"check-{label}",
        ["docker", "run", "--rm", "--entrypoint", "/app/.venv/bin/python", tag, "-c", IMAGE_CHECK],
    )
    return _check_line(found.stdout)


def _size(tree: Tree, tag: str) -> str:
    found = tree.run("size", ["docker", "image", "inspect", "--format", "{{.Size}}", tag])
    text = found.stdout.strip()
    return f"{int(text) / 1_000_000:.0f}MB" if text.isdigit() else "?"


def images_section(tree: Tree, rounds: Rounds) -> None:
    widget = "uv-workspace-probe/widget-admin:probe"
    serve = "uv-workspace-probe/serve-sync:probe"
    control = "uv-workspace-probe/serve-sync-without-member:probe"

    with rounds.round("이미지: 위젯 관리 서버(멤버 하나, 판 번호)") as current:
        ok, output = _build(tree, "widget", "widget-admin.Dockerfile", widget)
        inside = _inside(tree, "widget", widget) if ok else None
        current.mark(
            measured=inside is not None, result=f"안 {inside}" if inside else output[-400:]
        )

    with rounds.round("대조 이미지: serve 파이썬 단계, 루트 파일만(지금 꼴)") as current:
        ok, output = _build(tree, "control", "serve-sync-without-member.Dockerfile", control)
        mentioned = [line.strip() for line in output.splitlines() if "widget-admin" in line]
        current.mark(
            measured=ok or bool(mentioned),
            result="지었다" if ok else f"실패, 멤버를 든 줄 {mentioned[-2:]}",
        )

    with rounds.round("이미지: serve 파이썬 단계, 멤버 pyproject 를 들이면") as current:
        ok, output = _build(tree, "serve", "serve-sync.Dockerfile", serve)
        inside = _inside(tree, "serve", serve) if ok else None
        current.mark(
            measured=inside is not None, result=f"안 {inside}" if inside else output[-400:]
        )

    with rounds.round("이미지 크기") as current:
        tree.run("pull-python", ["docker", "pull", PYTHON_IMAGE])
        sizes = {
            "python": _size(tree, PYTHON_IMAGE),
            "widget": _size(tree, widget),
            "serve": _size(tree, serve),
        }
        current.mark(measured="?" not in sizes.values(), result=f"{sizes}")


def versions(tree: Tree) -> str:
    names = ["pyright", "ruff", "import-linter", "pytest", "pytest-xdist", "sqlalchemy", "alembic"]
    code = f"import importlib.metadata as m; print({{n: m.version(n) for n in {names!r}}})"
    local_uv = tree.run("uv-version", ["uv", "--version"]).stdout.strip()
    image_uv = tree.run("uv-image-version", ["docker", "run", "--rm", UV_IMAGE, "--version"])
    tools = tree.run("tool-versions", [str(tree.python()), "-c", code]).stdout.strip()
    return f"로컬 {local_uv}, 이미지 {image_uv.stdout.strip()}, {tools}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tree", type=Path)
    parser.add_argument("--sections", default=",".join(SECTIONS))
    options = parser.parse_args()
    chosen = [name.strip() for name in str(options.sections).split(",") if name.strip()]
    unknown = [name for name in chosen if name not in SECTIONS]
    if unknown:
        raise SystemExit(f"모르는 갈래: {unknown}")
    tree = build_tree(Path(options.tree))
    rounds = Rounds()
    sections = {
        "sync": sync_section,
        "tools": tools_section,
        "pytest": pytest_section,
        "command": command_section,
        "images": images_section,
    }
    if "sync" not in chosen:
        tree.configure()
        tree.run("lock", ["uv", "lock"])
        tree.run("sync", ["uv", "sync", "--frozen"])
    for name in chosen:
        sections[name](tree, rounds)
    print(versions(tree))
    for entry in rounds.entries:
        print(f"- {entry.label}: {'측정' if entry.measured else '측정 아님'}, {entry.result}")
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
