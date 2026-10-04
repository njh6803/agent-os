"""JWT 후보 라이브러리마다 빈 가상 환경을 하나씩 만들고 그 후보만 설치한다.

저장소의 `.venv`와 `uv.lock`은 건드리지 않는다. 환경은 인자로 받은 디렉터리 아래
`<후보>/.venv`에 둔다. pyright 의 `venv` 설정이 `.venv`라 `--venvpath <디렉터리>/<후보>`로
넘기면 그 환경을 읽는다(`check_types.py`).

    PYTHONUTF8=1 uv run python .scratch/web-widget/probes/jwt_verify/make_envs.py <환경 루트>
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# 잰 판. 전이 의존성은 고정하지 않는다 — 설치하면 무엇이 따라오는지가 측정 대상이다(deps.py).
CANDIDATES: dict[str, list[str]] = {
    "pyjwt": ["pyjwt[crypto]==2.15.1"],
    "joserfc": ["joserfc==1.7.5"],
    "jwcrypto": ["jwcrypto==1.6.1"],
}


def interpreter(env: Path) -> Path:
    windows = env / "Scripts" / "python.exe"
    return windows if windows.exists() else env / "bin" / "python"


def main() -> int:
    if len(sys.argv) != 2:
        print("인자: <환경 루트>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    for name, specs in CANDIDATES.items():
        env = root / name / ".venv"
        subprocess.run(["uv", "venv", "-q", "--python", "3.12", str(env)], check=True)
        subprocess.run(
            ["uv", "pip", "install", "-q", "--python", str(interpreter(env)), *specs],
            check=True,
        )
        print(f"{name}: {interpreter(env)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
