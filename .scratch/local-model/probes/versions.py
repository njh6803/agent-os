"""프로브가 돈 환경의 판을 JSON 한 줄로 찍는다(측정이 아니다). `openai_compat.py`가 첫 줄에 찍는다.

    <환경의 파이썬> .scratch/local-model/probes/versions.py

패키지가 깔린 자리(`where`)도 찍는다. 프로브가 `make_env.py`로 만든 환경의 것을 읽었는지, 저장소
`.venv`의 것을 읽었는지 가르려는 것이다. openai SDK 3.49.0 의 HTTP 층은 httpx 가 아니라 httpx2 다
(`openai_compat.py`의 실패 사례에서 예외의 원인 사슬이 `httpx2`·`httpcore2`의 형식이다).
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
import json
import platform
import sys

DISTRIBUTIONS = (
    "langchain-openai",
    "openai",
    "langchain-core",
    "langchain-anthropic",
    "httpx2",
    "httpcore2",
    "httpx",
    "httpcore",
    "h11",
    "anyio",
    "pydantic",
    "pydantic-core",
    "tiktoken",
    "regex",
    "jiter",
    "distro",
    "sniffio",
    "tqdm",
    "langsmith",
)
MODULES = ("langchain_openai", "openai", "langchain_core", "httpx2", "pydantic")


def versions() -> dict[str, str]:
    found: dict[str, str] = {}
    for name in DISTRIBUTIONS:
        try:
            found[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            found[name] = "없음"
    return found


def where() -> dict[str, str]:
    found: dict[str, str] = {}
    for name in MODULES:
        spec = importlib.util.find_spec(name)
        found[name] = "없음" if spec is None or spec.origin is None else spec.origin
    return found


def environment() -> dict[str, object]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "prefix": sys.prefix,
        "versions": versions(),
        "where": where(),
    }


if __name__ == "__main__":
    print(json.dumps(environment(), ensure_ascii=False))
