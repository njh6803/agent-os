"""pyright 를 이 프로브 폴더의 설정(strict, 3.12)으로 돌려 그 JSON 출력을 그대로 낸다.

가져오기는 `--interpreter`(없으면 이 스크립트를 띄운 `sys.executable`)의 경로로 푼다. pyright 에는
그것을 `--pythonpath` 로 넘긴다. 그래서 후보 패키지를 깐 환경의 파이썬으로 띄우면 저장소 잠금의
pyright 와 후보 패키지가 함께 보인다. 설정 파일에 `venv` 를 적지 않은 것은 그것이 `--pythonpath` 를
덮기 때문이다(`docs/constitution/operations.md` 환경 규약 상세). 나머지 인자는 pyright 에 그대로
넘긴다(예 `--pythonplatform Linux`). 측정의 셈은 `run.py` 가 한다. 이 파일은 도우미다(선례
`../pg_stack/typecheck.py`).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--interpreter", default=sys.executable)
    args, extra = parser.parse_known_args()
    interpreter: str = args.interpreter
    argv = [sys.executable, "-m", "pyright", "--outputjson", "-p", str(HERE)]
    done = subprocess.run(
        [*argv, "--pythonpath", interpreter, *extra],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
        check=False,
    )
    sys.stdout.write(done.stdout)
    sys.stderr.write(done.stderr)
    return done.returncode


if __name__ == "__main__":
    raise SystemExit(main())
