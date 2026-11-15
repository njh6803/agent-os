"""`hashlib.scrypt` 의 `maxmem`. 기본값이 어느 매개변수를 거부하는지와 통과하는 가장 작은 값을 잰다.

`RESULT <json>` 줄을 낸다. 셈과 표지의 판정은 `run.py` 가 한다.
  default  scrypt 줄마다 `maxmem` 을 주지 않고 한 번, `128·r·(N+p+2)` 를 주고 한 번, 그보다 1 작은
           값을 주고 한 번 부른다. 같은 매개변수가 충분한 `maxmem` 에서 통과해야 기본값의 거부가
           매개변수 탓이 아니라 한도 탓이다. 대조 줄 `N=2^14,r=8,p=1` 은 기본값에서 통과하는 쪽이다.
  least    요약 줄(N=2^17, r=8, p=1)이 통과하는 가장 작은 `maxmem` 을 이분법으로 찾는다. 식에
           기대지 않고 찾은 값이 식과 같은지를 본다.
  limit    기본 한도의 자리. N=2 로 두고 r 을 키워 요구량이 640 바이트씩 늘게 하면, 32 MiB 바로
           아래(r=52428)와 바로 위(r=52429)에서 통과와 거부가 갈리는지 본다.
  ceiling  `maxmem` 인자가 받는 가장 큰 값. 2^31-1 과 2^31 을 넘긴다.
"""

from __future__ import annotations

import hashlib
import json
import ssl
import sys

from rows import ROWS, Row

SALT = b"salt-of-16-bytes"
CONTROL = Row("scrypt", "N=2^14,r=8,p=1", "대조", (14, 8, 1))


def attempt(log_n: int, r: int, p: int, maxmem: int | None) -> str:
    try:
        if maxmem is None:
            hashlib.scrypt(b"sample", salt=SALT, n=1 << log_n, r=r, p=p, dklen=32)
        else:
            hashlib.scrypt(b"sample", salt=SALT, n=1 << log_n, r=r, p=p, maxmem=maxmem, dklen=32)
    except Exception as error:  # 거부의 종류와 문구가 결과다
        return f"{type(error).__name__}: {error}"
    return "ok"


def needed(log_n: int, r: int, p: int) -> int:
    return 128 * r * ((1 << log_n) + p + 2)


def emit(result: dict[str, object]) -> None:
    print(f"RESULT {json.dumps(result, ensure_ascii=False)}", flush=True)


def least(log_n: int, r: int, p: int) -> tuple[int, int]:
    """통과하는 가장 작은 `maxmem` 과 부른 횟수. 1 은 거부, 2^31-1 은 통과라는 데서 시작한다."""
    low, high, calls = 1, 2**31 - 1, 0
    while high - low > 1:
        middle = (low + high) // 2
        calls += 1
        if attempt(log_n, r, p, middle) == "ok":
            high = middle
        else:
            low = middle
    return high, calls


def main() -> int:
    emit({"kind": "openssl", "version": ssl.OPENSSL_VERSION, "platform": sys.platform})
    for row in (*(row for row in ROWS if row.candidate == "scrypt"), CONTROL):
        log_n, r, p = row.numbers
        formula = needed(log_n, r, p)
        emit(
            {
                "kind": "default",
                "label": row.label,
                "formula": formula,
                "default": attempt(log_n, r, p, None),
                "at_formula": attempt(log_n, r, p, formula),
                "below_formula": attempt(log_n, r, p, formula - 1),
            }
        )
    head = next(row for row in ROWS if row.candidate == "scrypt" and row.headline)
    log_n, r, p = head.numbers
    ends = [attempt(log_n, r, p, 1), attempt(log_n, r, p, 2**31 - 1)]
    found, calls = least(log_n, r, p)
    emit(
        {
            "kind": "least",
            "label": head.label,
            "ends": ends,
            "least": found,
            "calls": calls,
            "formula": needed(log_n, r, p),
        }
    )
    emit(
        {
            "kind": "limit",
            "passes_bytes": needed(1, 52428, 1),
            "passes": attempt(1, 52428, 1, None),
            "refused_bytes": needed(1, 52429, 1),
            "refused": attempt(1, 52429, 1, None),
        }
    )
    emit(
        {
            "kind": "ceiling",
            "at_2_31_minus_1": attempt(1, 8, 1, 2**31 - 1),
            "at_2_31": attempt(1, 8, 1, 2**31),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
