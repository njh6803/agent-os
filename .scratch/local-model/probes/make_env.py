"""프로브가 돌 가상 환경 하나를 만든다. 저장소 락의 판 위에 `langchain-openai`를 얹은 환경이다.

저장소의 `.venv`, `pyproject.toml`, `uv.lock`은 건드리지 않는다. 환경은 인자로 받은 디렉터리 아래
`.venv`에 둔다. pyright 의 `venv` 설정이 `.venv`라 `--venvpath <디렉터리>`로 넘기면 그 환경을
읽는다(`check_adapter_types.py`). 이미 있는 환경은 지우지 않고 그 위에 다시 설치한다. 그래서 인자가
이 저장소 안이거나 `pyproject.toml`이 있는 디렉터리(다른 체크아웃의 루트)면 아무것도 하지 않고 2 로
끝난다. 그 자리의 `.venv`는 그 프로젝트의 환경이라 거기에 얹으면 약속과 달리 저장소의 환경이 바뀐다.
같은 까닭으로, 이미 있는 `.venv`에 이 프로브가 만들며 심은 표지 파일(`MARKER`)이 없어도 2 로 끝난다
(홈 디렉터리나 `requirements.txt`만 쓰는 프로젝트나 사용자가 따로 만든 `.venv`를 지나치지 않는다).

    uv run python .scratch/local-model/probes/make_env.py <환경 루트>

하는 일:
1. `uv export --frozen`으로 락의 판을 둘로 뽑는다. 런타임 의존만(`locked-runtime.txt`, 설치할 것)과
   개발 그룹까지 전부(`locked-all.txt`, 제약). `--frozen`이라 락을 다시 풀지 않는다.
2. `uv venv`로 `<환경 루트>/.venv`를 만든다(없을 때만).
3. `uv pip install -r locked-runtime.txt -c locked-all.txt langchain-openai==<판>`.
4. 깔린 것을 락과 견줘 JSON 한 줄로 찍는다. `new`는 락에 없던 패키지(얹으며 새로 든 것), `moved`는
   락의 판과 다르게 깔린 패키지다. `moved`가 비지 않으면 락 위에 얹은 환경이 아니라 1 로 끝난다.

`uv run --with "langchain-openai==1.6.2"`로 얹는 길은 이 PC(uv 0.10.8, Windows)에서 jsonpointer
3.1.1 의 바퀴를 임시 환경에 깔다 실패해 쓰지 못했다(README 의 "돌리는 법").
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TARGET = "langchain-openai==1.6.2"
MARKER = ".agent-os-local-model-probe"  # 이 프로브가 만든 `.venv`에만 심는 빈 파일
CALL_TIMEOUT = 600.0
PINNED = re.compile(r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)==(?P<version>[^\s;]+)")


def interpreter(env: Path) -> Path:
    windows = env / "Scripts" / "python.exe"
    return windows if windows.exists() else env / "bin" / "python"


def canonical(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def uv(*arguments: str) -> str:
    done = subprocess.run(
        ["uv", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=CALL_TIMEOUT,
    )
    return done.stdout


def export(path: Path, *flags: str) -> dict[str, str]:
    uv("export", "--frozen", "--no-emit-project", "--no-hashes", "-q", *flags, "-o", str(path))
    pins: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = PINNED.match(line.strip())
        if match is not None:
            pins[canonical(match["name"])] = match["version"]
    return pins


def main() -> int:
    if len(sys.argv) != 2:
        print("인자: <환경 루트>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    if root.is_relative_to(ROOT) or (root / "pyproject.toml").exists():
        # 그 자리의 `.venv`는 그 프로젝트의 환경이다. 거기에 얹으면 저장소의 환경이 바뀐다.
        print("환경 루트는 저장소 밖이고 pyproject.toml 이 없는 디렉터리여야 한다", file=sys.stderr)
        return 2
    root.mkdir(parents=True, exist_ok=True)
    runtime = root / "locked-runtime.txt"
    everything = root / "locked-all.txt"
    export(runtime, "--no-dev")
    locked = export(everything)
    env = root / ".venv"
    if env.exists() and not (env / MARKER).exists():
        # 이 프로브가 만들지 않은 환경이다. 거기에 락의 판을 얹으면 남의 환경이 바뀐다.
        print("이 프로브가 만들지 않은 .venv 가 있다", file=sys.stderr)
        return 2
    if not interpreter(env).exists():
        uv("venv", "-q", "--python", "3.12", str(env))
        (env / MARKER).touch()
    python = str(interpreter(env))
    pins = ("-r", str(runtime), "-c", str(everything))
    uv("pip", "install", "-q", "--python", python, *pins, TARGET)
    listed = json.loads(uv("pip", "list", "--python", python, "--format", "json"))
    installed = {canonical(item["name"]): str(item["version"]) for item in listed}
    new = {name: version for name, version in sorted(installed.items()) if name not in locked}
    moved = {
        name: {"locked": locked[name], "installed": version}
        for name, version in sorted(installed.items())
        if name in locked and locked[name] != version
    }
    report = {
        "interpreter": python,
        "target": TARGET,
        "installed": len(installed),
        "new": new,
        "moved": moved,
    }
    print(json.dumps(report, ensure_ascii=False))
    return 1 if moved else 0


if __name__ == "__main__":
    raise SystemExit(main())
