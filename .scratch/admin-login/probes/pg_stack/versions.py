"""깔린 후보 패키지의 판, 라이선스 칸, 휠 태그, 타입 표지(`py.typed`)를 `RESULT <json>` 로 낸다.

깔린 배포판의 메타데이터에서 읽는다(PyPI 페이지가 아니다). 라이선스는 `License-Expression`, 없으면
`License` 의 첫 줄, 없으면 분류자(`License ::`)다. 윈도 호스트와 리눅스 컨테이너에서 같은 파일을
쓴다.
"""

from __future__ import annotations

import json
import sys
from importlib import metadata

PACKAGES = (
    "psycopg",
    "psycopg-binary",
    "psycopg-pool",
    "asyncpg",
    "asyncpg-stubs",
    "SQLAlchemy",
    "greenlet",
    "alembic",
    "Mako",
    "yoyo-migrations",
    "testcontainers",
    "docker",
    "pyright",
    "pytest",
    "pytest-asyncio",
    "pytest-xdist",
    "uvicorn",
    "fastapi",
    "anyio",
)


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
        "tags": tags[:3],
        "py_typed": any(item.name == "py.typed" for item in files),
        "stub_files": sum(1 for item in files if item.name.endswith(".pyi")),
    }


def main() -> int:
    print(f"RESULT {json.dumps({'python': sys.version.split()[0], 'platform': sys.platform})}")
    for name in PACKAGES:
        print(f"RESULT {json.dumps(describe(name), ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
