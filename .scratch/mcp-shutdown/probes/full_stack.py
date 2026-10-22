"""저장소 사본에 mcp 2.3.0 시제품(`prototype/`)을 얹어 검사와 테스트가 지나는지 잰다(소비 지점까지).

하는 일:
1. 원본 저장소(기본은 이 파일에서 세 단계 위)의 파이썬 프로젝트 파일을 임시 폴더로 복사한다.
2. `prototype/` 아래 파일을 같은 상대 경로로 덮는다(어댑터, 런처, 픽스처 서버, 가짜 프로세스,
   CLI 처리기, 테스트).
3. `pyproject.toml`의 의존성 `langchain-mcp-adapters>=0.1`을 `mcp>=2.3,<3`으로, import-linter 금지
   목록의 `langchain_mcp_adapters`를 `mcp`로 바꾼다(ADR 0034).
4. `uv lock`, `uv sync` 뒤 시제품 파일의 ruff 둘(검사와 서식), pyright, 타입 우회 검사,
   lint-imports, pytest(`tests/adapters`·`tests/core`·`tests/channel`)를 돌리고, MCP 어댑터와 CLI
   처리기의 테스트 파일만 한 번 더 돌려 테스트마다 걸린 시간(`--durations=0`)을 찍는다. 끝으로
   core 에 시제품 어댑터를 물린 `write_failure.py --expect closed`를, POSIX 에서는 런처가 뜨기
   전에 부모가 끝난 회차를 만드는 `stale_parent.py --expect refused`와 런처를 그룹의 우두머리가
   아니게 띄우는 `not_leader.py --expect refused`를 돌린다.
5. 대조군을 돈다. 두 OS 에서 CLI 처리기를 `asyncio.run` 그대로로 바꾼 사본의 처리기 테스트와
   어댑터가 그룹에 싸인 예외를 벗기지 않게 바꾼 사본의 해당 테스트(이름에 "연결_안"이나
   "뜨자마자")와 `write_failure.py --expect escaped`를, POSIX 에서는 어댑터가 런처를 쓰지 않게
   바꾼 사본과 런처가 부모를 보지 않게 바꾼 사본과 런처가 우두머리인지 보지 않게 바꾼 사본의 닫기
   테스트(이름에 "내려간다")를 돌려 빨강이 기대한 테스트에서 기대한 까닭으로 나는지 본다(우두머리를
   보지 않는 사본은 빨강이 없어야 한다). 부모를 보지 않는 사본에서는 `stale_parent.py --expect
   spawned`를, 우두머리를 보지 않는 사본에서는 `not_leader.py --expect killed`를 돈다.
6. 어긋난 단계가 없으면 만든 임시 폴더(사본과 대조군 사본, `.venv` 포함 수백 MB)를 지운다. 있으면
   살펴보도록 남기고 마지막 줄에 경로를 찍는다.

표지: 본 단계와 프로브(POSIX 는 셋, 아니면 `write_failure.py` 하나)는 모두 0으로 끝나야
하고(프로브는 표지와 기대를 스스로 본다),
대조군의 테스트는 기대한 테스트만 실패하며 각 실패의 요약 줄(`-rf`)에 기대한 문구가 있어야 한다.
그리고 pytest 의 종료 코드가 실패를 기대하면 1, 빨강이 없어야 하면(우두머리 검사를 뺀 사본) 0이어야
한다. 실패 줄만 세면 수집 오류(2)나 고른 테스트가 없는 회차(5)도 빨강이 없는 것으로 보인다(셀프
리뷰). 런처 없음은 자식을 남기는 서버와 프로세스가 죽는 사례, 부모를 보지 않음은 프로세스가 죽는
사례이고 문구는 하트비트 단언의 것이다. 처리기 없음은 두 사례이고 문구는 한 번이면 중단의 한 줄, 두
번이면 자식이 끝나지 않았다는 것이다. 벗기지 않음은 연결 안의 세 사례와 뜨자마자 끝나는 서버이고
문구는 pytest 가 하나만 든 그룹을 적는 꼴과 그룹 동일성 단언의 것이다. 문구는 그 사본을 손으로 돌려
실패 출력을 본 뒤 골랐다. 첫 판은 실패한 테스트의 이름만 봐서 엉뚱한 까닭의 실패도 기대와
맞았다(셀프 리뷰). 어긋나면 종료 코드 1이다. 네트워크로 패키지를 받는다. 돌리는 명령은 `README.md`에
있다.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROTOTYPE = HERE / "prototype"
COPIED = (
    "pyproject.toml",
    "uv.lock",
    "README.md",
    "openapi.json",
    "src",
    "tests",
    "tools",
    "plugins",
)
IGNORED = shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc")
TAIL_LINES = 24
CLOSING = "내려간다"
GROWING = "하트비트가 자란다"
INTERRUPT_TEST = "tests/channel/cli/test_interrupt.py"
# 대조군마다 빨개질 테스트와 그 실패의 요약 줄에 있어야 할 문구.
EXPECTED_RED = {
    "no_cli_handler": {
        "test_Ctrl_C_를_한_번_누르면_서버를_닫고_중단으로_끝난다": "실행을 중단했다",
        "test_닫는_도중에_한_번_더_누르면_닫기를_기다리지_않고_끝난다": "30초 안에 끝나지 않았다",
    },
    "no_launcher": {
        "test_스스로_끝나며_자식을_남기는_서버를_닫으면_그_자식도_내려간다": GROWING,
        "test_연결을_연_프로세스가_갑자기_죽어도_서버가_내려간다": GROWING,
    },
    "no_parent_watch": {"test_연결을_연_프로세스가_갑자기_죽어도_서버가_내려간다": GROWING},
    # 상류는 런처를 늘 새 세션으로 띄우므로 이 검사를 꺼도 닫기 테스트는 빨개지지 않는다.
    "no_leader_check": {},
    "no_unwrap": {
        "test_뜨자마자_끝나는_서버는_서버_이름을_든_연결_오류다": (
            "Connection closed') [single exception in ExceptionGroup]"
        ),
        "test_연결_안에서_난_예외는_감싸이지_않고_나오며_서버가_내려간다": (
            "_본문의_예외() [single exception in ExceptionGroup]"
        ),
        "test_연결_안에서_던진_예외_그룹은_그_그룹_그대로_나온다": (
            "assert ExceptionGroup('unhandled errors in a TaskGroup'"
        ),
        "test_연결_안의_yield_에_멈춘_제너레이터는_예외_없이_닫힌다": (
            "GeneratorExit() [single exception in BaseExceptionGroup]"
        ),
    },
}
POSIX_VARIANTS = {"no_launcher", "no_parent_watch", "no_leader_check"}
WRITE_FAILURE = ["uv", "run", "python", str(HERE / "write_failure.py"), "--expect"]
STALE_PARENT = ["uv", "run", "python", str(HERE / "stale_parent.py"), "--expect"]
NOT_LEADER = ["uv", "run", "python", str(HERE / "not_leader.py"), "--expect"]
UNWRAPPED = "연결_안 or 뜨자마자"


def _copy(source: Path, target: Path) -> None:
    for name in COPIED:
        path = source / name
        if path.is_dir():
            shutil.copytree(path, target / name, ignore=IGNORED)
        else:
            shutil.copy2(path, target / name)
    for path in PROTOTYPE.rglob("*.py"):
        destination = target / path.relative_to(PROTOTYPE)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)


def _replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"{path} 에 바꿀 글이 없다: {old!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def _run(name: str, command: list[str], cwd: Path, timeout: int) -> dict[str, object]:
    started = time.monotonic()
    # pytest 는 터미널이 아니면 80칸으로 보고 실패 요약 줄을 그 폭에서 자른다. 한글 테스트
    # 이름만으로 그 폭을 넘어 까닭이 통째로 빠졌다(첫 회차). 넓혀서 까닭까지 받는다.
    env = dict(os.environ, PYTHONUTF8="1", UV_PYTHON_DOWNLOADS="never", COLUMNS="1000")
    env.pop("VIRTUAL_ENV", None)
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    lines = (completed.stdout + completed.stderr).splitlines()
    failed = re.findall(r"^FAILED \S+::(\S+)(?: - (.*))?$", "\n".join(lines), re.MULTILINE)
    return {
        "step": name,
        "exit": completed.returncode,
        "seconds": round(time.monotonic() - started, 1),
        "failed": {test: reason for test, reason in failed},
        "durations": re.findall(r"^\s*([\d.]+s \w+)\s+\S+::(\S+)", "\n".join(lines), re.MULTILINE),
        # 표준 출력의 JSON 줄(`write_failure.py`의 사례 기록). 꼬리는 표준 에러가 뒤에 붙어 밀린다.
        "records": [line for line in completed.stdout.splitlines() if line.startswith("{")],
        "tail": lines[-TAIL_LINES:],
    }


def _variant(copy: Path, name: str) -> Path:
    """대조군 사본. 본 사본을 옮겨 쓰지 않도록 따로 복사해 고친다."""
    target = copy.parent / f"{copy.name}-{name}"
    shutil.copytree(copy, target, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    if name == "no_cli_handler":
        _replace(
            target / "src/agent_os/channel/cli/interrupt.py",
            '    """`asyncio.run(main())`과 같되 Ctrl+C 를 직접 받는다."""\n',
            '    """`asyncio.run(main())`과 같되 Ctrl+C 를 직접 받는다."""\n'
            "    return asyncio.run(main())\n",
        )
    elif name == "no_launcher":
        _replace(
            target / "src/agent_os/adapters/mcp.py",
            'if sys.platform == "win32":\n        return StdioServerParameters',
            "if True:\n        return StdioServerParameters",
        )
    elif name == "no_unwrap":
        _replace(
            target / "src/agent_os/adapters/mcp.py",
            "unwrapped = escaped.unwrap(group)",
            "unwrapped = None",
        )
    elif name == "no_leader_check":
        _replace(
            target / "src/agent_os/adapters/mcp_launcher.py",
            "if os.getpgrp() != os.getpid():",
            "if False:",
        )
    else:
        _replace(
            target / "src/agent_os/adapters/mcp_launcher.py",
            "if os.getppid() != parent:",
            "if False:",
        )
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=HERE.parents[2])
    options = parser.parse_args()
    copy = Path(tempfile.mkdtemp(prefix="mcp-full-stack-")) / "repo"
    copy.mkdir()
    _copy(options.source.resolve(), copy)
    _replace(copy / "pyproject.toml", '"langchain-mcp-adapters>=0.1",', '"mcp>=2.3,<3",')
    _replace(copy / "pyproject.toml", '"langchain_mcp_adapters"]', '"mcp"]')
    print(json.dumps({"platform": platform.platform(), "python": platform.python_version()}))
    prototype = sorted(path.relative_to(PROTOTYPE).as_posix() for path in PROTOTYPE.rglob("*.py"))
    steps = [
        ("uv lock", ["uv", "lock"], 600),
        ("uv sync", ["uv", "sync"], 900),
        ("versions", ["uv", "run", "python", "-c", _VERSIONS], 120),
        ("ruff check", ["uv", "run", "ruff", "check", *prototype], 300),
        ("ruff format", ["uv", "run", "ruff", "format", "--check", *prototype], 300),
        ("pyright", ["uv", "run", "pyright"], 900),
        ("type escapes", ["uv", "run", "python", "tools/check_type_escapes.py"], 300),
        ("lint-imports", ["uv", "run", "lint-imports"], 300),
        (
            "pytest",
            ["uv", "run", "pytest", "-q", "-rf", "-p", "no:cacheprovider"]
            + ["tests/adapters", "tests/core", "tests/channel"],
            2400,
        ),
        (
            "durations",
            ["uv", "run", "pytest", "-q", "-p", "no:cacheprovider", "--durations=0"]
            + ["tests/adapters/test_mcp.py", INTERRUPT_TEST],
            600,
        ),
        ("write failure", [*WRITE_FAILURE, "closed"], 600),
    ]
    if os.name == "posix":
        steps.append(("stale parent", [*STALE_PARENT, "refused"], 300))
        steps.append(("not leader", [*NOT_LEADER, "refused"], 300))
    bad: list[str] = []
    for name, command, timeout in steps:
        result = _run(name, command, copy, timeout)
        print(json.dumps(result, ensure_ascii=False))
        if result["exit"] != 0:
            bad.append(name)
    for variant, expected in EXPECTED_RED.items():
        if variant in POSIX_VARIANTS and os.name != "posix":
            continue
        target = _variant(copy, variant)
        _run(f"{variant}: uv sync", ["uv", "sync"], target, 900)
        pytest = ["uv", "run", "pytest", "-q", "-rf", "-p", "no:cacheprovider"]
        if variant == "no_cli_handler":
            selected = [INTERRUPT_TEST]
        elif variant == "no_unwrap":
            selected = ["tests/adapters/test_mcp.py", "-k", UNWRAPPED]
        else:
            selected = ["tests/adapters/test_mcp.py", "-k", CLOSING]
        result = _run(f"{variant}: pytest", [*pytest, *selected], target, 600)
        result["expected_failed"] = expected
        print(json.dumps(result, ensure_ascii=False))
        if not _as_expected(result["exit"], result["failed"], expected):
            bad.append(variant)
        if variant == "no_unwrap":
            # 벗기지 않으면 결말을 쓴 실행이 그룹을 올리는지 core 에서 본다(양성 대조).
            result = _run(f"{variant}: write failure", [*WRITE_FAILURE, "escaped"], target, 600)
            print(json.dumps(result, ensure_ascii=False))
            if result["exit"] != 0:
                bad.append(f"{variant}: write failure")
        if variant == "no_parent_watch":
            # 견줌을 지우면 부모가 이미 끝난 회차에도 서버가 뜨는지 본다(양성 대조).
            result = _run(f"{variant}: stale parent", [*STALE_PARENT, "spawned"], target, 300)
            print(json.dumps(result, ensure_ascii=False))
            if result["exit"] != 0:
                bad.append(f"{variant}: stale parent")
        if variant == "no_leader_check":
            # 검사를 끄면 우두머리가 아닌 런처가 부른 쪽의 그룹을 끄는지 본다(양성 대조).
            result = _run(f"{variant}: not leader", [*NOT_LEADER, "killed"], target, 300)
            print(json.dumps(result, ensure_ascii=False))
            if result["exit"] != 0:
                bad.append(f"{variant}: not leader")
    summary: dict[str, object] = {"copy": str(copy), "unexpected": bad, "removed": False}
    if not bad:
        try:
            shutil.rmtree(copy.parent)
            summary["removed"] = True
        except OSError as error:
            summary["remove_error"] = f"{type(error).__name__}: {error}"
    print(json.dumps(summary, ensure_ascii=False))
    return 1 if bad else 0


def _as_expected(exit_code: object, failed: object, expected: dict[str, str]) -> bool:
    """테스트가 돌았고(pytest 의 종료 코드가 실패를 기대하면 1, 아니면 0), 기대한 테스트만
    실패했으며, 실패마다 요약 줄에 기대한 문구가 있다."""
    if exit_code != (1 if expected else 0):
        return False
    if not isinstance(failed, dict) or set(failed) != set(expected):
        return False
    return all(expected[test] in str(failed[test] or "") for test in expected)


_VERSIONS = (
    "import importlib.metadata as m; "
    "print({n: m.version(n) for n in ('mcp', 'mcp-types', 'anyio', 'pydantic', 'pyright')})"
)


if __name__ == "__main__":
    sys.exit(main())
