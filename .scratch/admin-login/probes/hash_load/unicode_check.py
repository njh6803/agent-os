"""항목 4. 비밀번호의 유니코드 처리. NFKC 정규화, 글자 수의 세는 법, 규칙의 판정, 해시의 왕복.

입력마다 낸다. 정규화 앞과 뒤의 코드 포인트 수, UTF-8 바이트 수, UTF-16 단위 수(브라우저의
`String.length` 가 세는 단위), 규칙 판정 두 가지 해석, 해시의 왕복.

규칙 판정의 두 해석(ADR 0062 "비밀번호 규칙"의 낱말을 어떻게 읽는가).
- `ascii`: 영문 대문자는 `A`~`Z`, 숫자는 `0`~`9`, 특수문자는 ASCII 영문자와 숫자가 아닌 모든 글자
  (한글, 공백, 이모지도 든다).
- `unicode`: 대문자는 `str.isupper`, 숫자는 `str.isdigit`, 특수문자는 `str.isalnum` 이 거짓인 글자.
둘 다 길이는 코드 포인트로 8 이상 128 이하다.

해시의 왕복. 정규화한 글로 해시를 만들고, 같은 글이 통과하고(참) 끝에 한 글자 더한 글이 걸리는지
(거짓) 본다. 그 둘이 재려는 상황(해시와 견줌이 실제로 돌았다)의 표지다. 정규화 앞의 글이 다르면 그
글이 정규화한 글의 저장 값을 통과하는지도 본다. 해시가 예외로 끝나면 예외의 종류를 적는다.

`RESULT <json>` 한 줄. 판정은 `run.py` 다.
"""

from __future__ import annotations

import json
import sys
import time
import unicodedata

from argon2.exceptions import VerifyMismatchError
from common import hasher

LOW, HIGH = 8, 128


def cases() -> list[tuple[str, str]]:
    return [
        ("전각 영문·숫자·기호", "Ａｂｃｄ１２３！"),
        ("합자 ﬁ(U+FB01)", "ﬁle-Pass1"),
        ("한글 NFD(자모 셋)", unicodedata.normalize("NFD", "각Pass1!")),
        ("한글 NFC", "각Pass1!"),
        ("결합 문자 e+U+0301", "Café-Pass1"),
        ("미리 조합된 é(U+00E9)", "Café-Pass1"),
        ("켈빈 기호 U+212A", "Kelvin-pass1"),
        ("옹스트롬 기호 U+212B", "Ångstrom-1"),
        ("위 첨자 ²", "Pass²word!"),
        ("로마 숫자 Ⅷ(U+2167)", "pass-Ⅷ-word"),
        ("U+FDFA 일곱 개", "Aa1!" + "ﷺ" * 7),
        ("4바이트 글자로 128 자", "A1!" + "\U0001f600" * 125),
        ("4바이트 글자로 129 자", "A1!" + "\U0001f600" * 126),
        ("ASCII 128 자", "A1!" + "a" * 125),
        ("한글이 특수문자 자리", "비밀번호Pass1"),
        ("공백과 NUL", "Pass 1\x00word"),
        ("짝 없는 서로게이트(JSON 의 \\ud800)", json.loads('"Pass1!A\\ud800"')),
    ]


def utf8_bytes(text: str) -> int | None:
    try:
        return len(text.encode("utf-8"))
    except UnicodeEncodeError:
        return None


def utf16_units(text: str) -> int:
    return len(text.encode("utf-16-le", errors="surrogatepass")) // 2


def rule(text: str, reading: str) -> dict[str, bool]:
    if reading == "ascii":
        upper = any("A" <= c <= "Z" for c in text)
        digit = any("0" <= c <= "9" for c in text)
        special = any(not (c.isascii() and c.isalnum()) for c in text)
    else:
        upper = any(c.isupper() for c in text)
        digit = any(c.isdigit() for c in text)
        special = any(not c.isalnum() for c in text)
    length = LOW <= len(text) <= HIGH
    return {
        "length": length,
        "upper": upper,
        "digit": digit,
        "special": special,
        "pass": length and upper and digit and special,
    }


def check(stored: str, password: str) -> bool:
    try:
        return hasher().verify(stored, password)
    except VerifyMismatchError:
        return False


def round_trip(original: str, normal: str) -> dict[str, object]:
    ph = hasher()
    try:
        started = time.perf_counter()
        stored = ph.hash(normal)
        seconds = time.perf_counter() - started
    except Exception as error:  # 예외의 종류가 결과다
        return {"hash_error": type(error).__name__, "hash_error_text": str(error)[:120]}
    found: dict[str, object] = {
        "hash_seconds": seconds,
        "same": check(stored, normal),
        "plus_one": check(stored, normal + "x"),
        "minus_last": check(stored, normal[:-1]),
    }
    if original != normal:
        found["original_against_normal"] = check(stored, original)
    if "\x00" in normal:
        found["before_nul"] = check(stored, normal.split("\x00")[0])
    return found


def main() -> int:
    rows: list[dict[str, object]] = []
    for label, original in cases():
        normal = unicodedata.normalize("NFKC", original)
        rows.append(
            {
                "label": label,
                "original": ascii(original),
                "normal": ascii(normal),
                "changed": normal != original,
                "code_points": [len(original), len(normal)],
                "utf8_bytes": [utf8_bytes(original), utf8_bytes(normal)],
                "utf16_units": [utf16_units(original), utf16_units(normal)],
                "rule_ascii": [rule(original, "ascii"), rule(normal, "ascii")],
                "rule_unicode": [rule(original, "unicode"), rule(normal, "unicode")],
                "round_trip": round_trip(original, normal),
            }
        )
    result = {
        "kind": "unicode",
        "platform": sys.platform,
        "unidata_version": unicodedata.unidata_version,
        "rows": rows,
    }
    print(f"RESULT {json.dumps(result)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
