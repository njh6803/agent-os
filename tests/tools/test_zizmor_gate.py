"""워크플로 하드닝의 판정자 zizmor 가 실제로 잡는지 본다(ADR 0027).

게이트는 `tools/run_checks.py` 의 `CHECKS` 와 CI `python` 잡이 같은 명령으로 돈다. 여기서는 그
명령의 인자를 저장소 워크플로와 설정의 사본에 돌려, 체크아웃에서 `persist-credentials: false` 를
지우면 artipacked 가, 서드파티 액션을 해시 대신 태그로 가져오면 unpinned-uses 가 그 줄을 가리키며
실패하는지 단언한다. zizmor 를 올리거나 `.github/zizmor.yml` 을 바꿔 artipacked 가 꺼지거나
unpinned-uses 정책이 서드파티까지 넓어지면 여기가 빨갛다.

못 보는 것: 그 둘 밖의 감사(template-injection 등)가 꺼지는 것, `actions/*` 의 정책이 넓어지는 것
(`ref-pin` 을 `any` 로), 온라인 감사(ADR 0027 이 끈다). 사본에는 워크플로와 설정만 옮기므로, 저장소
루트에서만 거두는 입력(`.pre-commit-config.yaml`)의 변이는 보지 않는다.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from tools.run_checks import CHECKS

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
CONFIG = ROOT / ".github" / "zizmor.yml"
PERSIST = re.compile(r"^\s*persist-credentials:\s*false\s*$")
CHECKOUT = re.compile(r"^\s*(?:-\s+)?uses:\s*actions/checkout@")
# 서드파티 액션의 해시 고정: `uses: 소유자/저장소@<40자 해시> # v판`
HASH_PIN = re.compile(r"^(\s*(?:-\s+)?uses:\s*)([\w.-]+/[\w.-]+)@[0-9a-f]{40}\s+#\s*(v\S+)\s*$")

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None


def _gate_args() -> list[str]:
    """게이트 명령에서 `uv run zizmor` 뒤의 인자."""
    (check,) = [check for check in CHECKS if check.id == "zizmor"]
    assert check.command[:3] == ("uv", "run", "zizmor"), check.command
    return list(check.command[3:])


def _at(node: Json, *path: str | int) -> Json:
    for key in path:
        if isinstance(key, str):
            assert isinstance(node, dict), (key, node)
            node = node[key]
        else:
            assert isinstance(node, list), (key, node)
            node = node[key]
    return node


def _findings(stdout: str) -> list[tuple[str, str, int]]:
    """zizmor 의 JSON 출력에서 (감사 id, 파일 이름, 0부터 센 줄)을 주 위치마다 하나씩 뽑는다."""
    parsed: Json = json.loads(stdout) if stdout.strip() else []
    assert isinstance(parsed, list), stdout
    found: list[tuple[str, str, int]] = []
    for finding in parsed:
        ident = _at(finding, "ident")
        locations = _at(finding, "locations")
        assert isinstance(ident, str) and isinstance(locations, list)
        for location in locations:
            if _at(location, "symbolic", "kind") != "Primary":
                continue
            path = _at(location, "symbolic", "key", "Local", "verbatim_path")
            row = _at(location, "concrete", "location", "start_point", "row")
            assert isinstance(path, str) and isinstance(row, int)
            found.append((ident, path.replace("\\", "/").rsplit("/", 1)[-1], row))
    return found


def _zizmor(tree: Path) -> tuple[int, list[tuple[str, str, int]], str]:
    """게이트의 인자에 JSON 출력을 더해 tree 에서 돌린다. 종료 코드, 발견, stderr."""
    executable = shutil.which("zizmor")
    assert executable is not None, "zizmor 가 PATH 에 없다. uv sync 로 dev 의존성을 깐다"
    process = subprocess.run(
        [executable, "--format", "json", *_gate_args()],
        cwd=tree,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    return process.returncode, _findings(process.stdout), process.stderr


def _copy(tmp_path: Path) -> Path:
    """저장소의 워크플로와 zizmor 설정을 tmp_path/.github 아래로 옮긴다."""
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    shutil.copy(CONFIG, tmp_path / ".github" / "zizmor.yml")
    for path in WORKFLOWS.glob("*.yml"):
        shutil.copy(path, workflows / path.name)
    return tmp_path


def _lines(name: str) -> list[str]:
    return (WORKFLOWS / name).read_text(encoding="utf-8").splitlines(keepends=True)


def _cases(pattern: re.Pattern[str]) -> list[tuple[str, int]]:
    return [
        (path.name, index)
        for path in sorted(WORKFLOWS.glob("*.yml"))
        for index, line in enumerate(_lines(path.name))
        if pattern.match(line)
    ]


def _drop(lines: list[str], index: int) -> list[str]:
    """index 줄을 지우고, 그래서 빈 매핑이 된 바로 위의 `with:` 도 지운다."""
    out = lines[:index] + lines[index + 1 :]
    above = index - 1
    if above >= 0 and out[above].strip() == "with:":
        indent = len(out[above]) - len(out[above].lstrip())
        below = out[above + 1] if above + 1 < len(out) else ""
        if not below.strip() or len(below) - len(below.lstrip()) <= indent:
            del out[above]
    return out


def test_게이트는_오프라인이고_설정을_명시하며_CI_python_잡이_같은_명령을_돈다() -> None:
    """온라인 감사는 바깥의 공지에 따라 판정이 바뀌고, 로컬에는 토큰이 없을 수 있다(ADR 0027).

    설정의 자동 탐색은 `.git` 디렉터리를 찾아 올라가, 워크트리(`.git` 이 파일)에서 주 체크아웃의
    설정을 읽었다. 그래서 `--config` 로 가리킨다.
    """
    args = _gate_args()
    assert "--offline" in args
    assert "--strict-collection" in args
    assert args[args.index("--config") + 1] == ".github/zizmor.yml"
    (check,) = [check for check in CHECKS if check.id == "zizmor"]
    ci = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    assert f"- run: {' '.join(check.command)}" in [line.strip() for line in ci.splitlines()]


def test_이_저장소의_워크플로는_모두_거둬지고_게이트를_지난다() -> None:
    """저장소 루트에서 게이트 그대로 돈다. 거둔 입력에 워크플로가 하나라도 빠지면 빨갛다."""
    code, findings, stderr = _zizmor(ROOT)

    assert code == 0, (findings, stderr)
    assert findings == []
    names = sorted(path.name for path in WORKFLOWS.glob("*.yml"))
    assert names
    for name in names:
        assert re.search(rf"completed \S*workflows[\\/]{re.escape(name)}\b", stderr), name


@pytest.mark.parametrize(("name", "index"), _cases(PERSIST))
def test_체크아웃에서_persist_credentials_를_지우면_artipacked_로_실패한다(
    tmp_path: Path, name: str, index: int
) -> None:
    """zizmor 는 단계의 시작 줄(`- name:` 이 앞서면 그 줄)을 가리킨다."""
    tree = _copy(tmp_path)
    lines = _lines(name)
    uses = max(i for i in range(index) if CHECKOUT.match(lines[i]))
    step = max(i for i in range(uses + 1) if lines[i].lstrip().startswith("- "))
    (tree / ".github" / "workflows" / name).write_text("".join(_drop(lines, index)), "utf-8")

    code, findings, stderr = _zizmor(tree)

    assert code != 0, stderr
    assert findings == [("artipacked", name, step)]


def test_자격_증명이_필요한_체크아웃은_그_줄의_무시_주석으로_지난다(tmp_path: Path) -> None:
    """ADR 0027 과 `ci.yml` 머리 주석이 안내하는 예외의 길. 주석은 `uses:` 줄 끝에 둔다."""
    tree = _copy(tmp_path)
    name, index = _cases(PERSIST)[0]
    lines = _lines(name)
    uses = max(i for i in range(index) if CHECKOUT.match(lines[i]))
    lines[uses] = lines[uses].rstrip("\n") + "  # zizmor: ignore[artipacked] 이 잡은 push 한다\n"
    (tree / ".github" / "workflows" / name).write_text("".join(_drop(lines, index)), "utf-8")

    code, findings, stderr = _zizmor(tree)

    assert code == 0, (findings, stderr)
    assert findings == []


@pytest.mark.parametrize(("name", "index"), _cases(HASH_PIN))
def test_서드파티_액션을_태그로_가져오면_unpinned_uses_로_실패한다(
    tmp_path: Path, name: str, index: int
) -> None:
    """`actions/*` 는 태그를 허용한다. 저장소의 체크아웃(`@v4` 등)은 위 저장소 테스트가 지난다."""
    tree = _copy(tmp_path)
    lines = _lines(name)
    match = HASH_PIN.match(lines[index])
    assert match is not None
    prefix, action, version = match.groups()
    lines[index] = f"{prefix}{action}@{version.split('.')[0]}\n"
    (tree / ".github" / "workflows" / name).write_text("".join(lines), "utf-8")

    code, findings, stderr = _zizmor(tree)

    assert code != 0, stderr
    assert findings == [("unpinned-uses", name, index)]


def test_YAML_이_깨진_워크플로를_건너뛰지_않고_실패한다(tmp_path: Path) -> None:
    """zizmor 의 기본값은 깨진 입력을 경고만 하고 건너뛰어, 다른 워크플로가 깨끗하면 종료 0 이다."""
    tree = _copy(tmp_path)
    (tree / ".github" / "workflows" / "broken.yml").write_text(
        "on: push\njobs:\n  a:\n    steps:\n      - with: [\n", "utf-8"
    )

    code, _, stderr = _zizmor(tree)

    assert code != 0
    assert "invalid YAML syntax" in stderr
