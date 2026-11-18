"""`serve` 의 대역. 환경 변수로 받은 주소와 조립 방식으로 앱을 만들어 `uvicorn.run` 으로 띄운다.

`run.py` 가 하위 프로세스로 띄워, 데이터베이스에 문제가 있을 때 uvicorn 이 표준 오류에 무엇을 찍고
어떤 종료 코드로 끝나는지를 본다. 측정의 셈은 `run.py` 가 한다. 이 파일은 도우미다.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from proto.apps import gate_app, lifespan_app  # noqa: E402
from proto.database import PostgresDatabase, parse_url  # noqa: E402


def main() -> int:
    url = parse_url(os.environ["PGF_URL"])
    if url is None:
        print("연결 문자열을 읽지 못했다", file=sys.stderr)
        return 1
    database = PostgresDatabase(
        url,
        retry_seconds=float(os.environ.get("PGF_RETRY", "0")),
        notice=lambda line: print(line, file=sys.stderr, flush=True),
    )
    build = gate_app if os.environ["PGF_VARIANT"] == "gate" else lifespan_app
    uvicorn.run(build(database), host="127.0.0.1", port=0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
