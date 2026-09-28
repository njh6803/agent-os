"""잠긴 의존성 위에서 fastapi 만 바꿔 가며 채널 테스트가 서는 가장 낮은 버전을 찾는다."""

import json
import os
import subprocess
import sys
import urllib.request

SCRATCH = (
    "C:/Users/User/AppData/Local/Temp/claude/C--project-agent/"
    "67e6158e-290d-46fe-bab2-fa1688ab4776/scratchpad"
)
PYTHON = f"{SCRATCH}/bisect/Scripts/python.exe"
ROOT = "C:/project/agent"


def versions() -> list[str]:
    with urllib.request.urlopen("https://pypi.org/pypi/fastapi/json", timeout=30) as response:
        releases = json.load(response)["releases"]
    wanted = []
    for version in releases:
        parts = version.split(".")
        if len(parts) == 3 and all(p.isdigit() for p in parts):
            key = tuple(int(p) for p in parts)
            if (0, 135, 0) <= key <= (0, 141, 1):
                wanted.append((key, version))
    return [version for _, version in sorted(wanted)]


def passes(version: str) -> tuple[bool, str]:
    subprocess.run(
        ["uv", "pip", "install", "-q", "--python", PYTHON, "--no-deps", f"fastapi=={version}"],
        check=True,
    )
    result = subprocess.run(
        [
            PYTHON,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "tests/channel/http",
            "tests/test_server.py",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
        timeout=600,
    )
    return result.returncode == 0, result.stdout.strip().splitlines()[-1]


def main() -> int:
    for version in versions():
        ok, summary = passes(version)
        print(f"{version}: {'초록' if ok else '빨강'} ({summary})", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
