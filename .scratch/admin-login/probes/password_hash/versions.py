"""깔린 패키지의 판, 라이선스 칸, 휠 태그, 타입 표지(`py.typed`)를 `RESULT <json>` 로 낸다.

깔린 배포판의 메타데이터에서 읽는다(PyPI 페이지가 아니다). 라이선스는 `License-Expression`, 없으면
`License` 의 첫 줄, 없으면 분류자(`License ::`)다. 첫 줄은 그 환경이다. 파이썬과 OpenSSL 의 판,
`hashlib.scrypt` 가 있는지, Argon2 알고리즘의 판 번호, 경로에서 찾은 C 컴파일러다. 컴파일러가 없는
환경에 깔려 있으면 휠로 깔린 것이다. 윈도 호스트와 리눅스 컨테이너에서 같은 파일을 쓴다(선례
`../pg_stack/versions.py`).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import ssl
import sys
from importlib import metadata

from argon2 import low_level

PACKAGES = (
    "argon2-cffi",
    "argon2-cffi-bindings",
    "cffi",
    "pycparser",
    "anyio",
    "pyright",
)
COMPILERS = ("cc", "gcc", "clang", "cl")


def license_of(dist: metadata.Distribution) -> str:
    expression = dist.metadata.get("License-Expression")
    if expression:
        return expression
    text = dist.metadata.get("License")
    if text:
        return text.strip().splitlines()[0][:80]
    classifiers = dist.metadata.get_all("Classifier") or []
    found = [item.split("::")[-1].strip() for item in classifiers if item.startswith("License ::")]
    return "; ".join(found) or "(메타데이터에 없음)"


def describe(name: str) -> dict[str, str | bool | int | list[str]]:
    try:
        dist = metadata.distribution(name)
    except metadata.PackageNotFoundError:
        return {"name": name, "installed": False}
    files = dist.files or []
    wheel = next((item for item in files if item.name == "WHEEL"), None)
    tags = (
        [line.removeprefix("Tag: ") for line in wheel.read_text().splitlines() if "Tag: " in line]
        if wheel is not None
        else []
    )
    return {
        "name": name,
        "installed": True,
        "version": dist.version,
        "license": license_of(dist),
        "license_files": [str(item) for item in files if "licenses" in item.parts],
        "tags": tags[:3],
        "py_typed": [str(item) for item in files if item.name == "py.typed"],
        "requires": dist.requires or [],
    }


def main() -> int:
    environment = {
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "openssl": ssl.OPENSSL_VERSION,
        "hashlib_scrypt": hasattr(hashlib, "scrypt"),
        # `low_level.ARGON2_VERSION` 은 pyright 에 Unknown 이라(`friction_argon2_low_level.py`)
        # 이름으로 꺼낸다.
        "argon2_version_number": vars(low_level).get("ARGON2_VERSION"),
        "compilers": {name: shutil.which(name) for name in COMPILERS},
    }
    print(f"RESULT {json.dumps(environment, ensure_ascii=False)}", flush=True)
    for name in PACKAGES:
        print(f"RESULT {json.dumps(describe(name), ensure_ascii=False)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
