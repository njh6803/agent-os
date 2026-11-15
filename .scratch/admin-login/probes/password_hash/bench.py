"""매개변수 줄마다 해시 한 번과 견줌 한 번에 걸리는 시간을 재서 `RESULT <json>` 줄로 낸다.

줄은 `rows.py` 의 것이고 후보 모듈(`store_scrypt.py`, `store_argon2.py`)을 거쳐 부른다. 회차마다
해시 한 번(`hash_ms`), 맞는 비밀번호로 견줌 한 번(`verify_ms`), 틀린 비밀번호로 견줌 한 번을 한다.
`genuine` 은 그 회차가 그 줄의 매개변수로 실제로 해시했다는 표지다(문자열의 머리가 그 매개변수이고
맞는 비밀번호만 통과한다). 셈과 표지의 판정은 `run.py` 가 한다. 요약 줄(headline)은 `--rounds` 번,
나머지 줄은 `--other-rounds` 번 돈다. 줄을 번갈아 돌아 한 줄의 회차가 한때에 몰리지 않게 한다.
"""

from __future__ import annotations

import argparse
import json
import time

from rows import PASSWORD, ROWS, WRONG, bind


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=10)
    parser.add_argument("--other-rounds", type=int, default=5)
    args = parser.parse_args()
    rounds: int = args.rounds
    other_rounds: int = args.other_rounds
    bound = [bind(row) for row in ROWS]
    for index in range(max(rounds, other_rounds)):
        for item in bound:
            if index >= (rounds if item.row.headline else other_rounds):
                continue
            started = time.perf_counter()
            stored = item.hash_password(PASSWORD)
            hashed = time.perf_counter()
            right = item.verify_password(stored, PASSWORD)
            verified = time.perf_counter()
            wrong = item.verify_password(stored, WRONG)
            result = {
                "kind": "bench",
                "key": item.row.key,
                "round": index + 1,
                "genuine": stored.startswith(item.prefix) and right and not wrong,
                "hash_ms": round((hashed - started) * 1000, 2),
                "verify_ms": round((verified - hashed) * 1000, 2),
            }
            print(f"RESULT {json.dumps(result, ensure_ascii=False)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
