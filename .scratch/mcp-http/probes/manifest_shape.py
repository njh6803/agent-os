"""`[server]` 표를 `transport` 로 가르는 판별 유니온이 pydantic 에서 어떻게 읽히고, 그 JSON 스키마가
openapi-typescript 와 tsc 를 지나 좁혀지는지를 소비 지점까지 잰다.

두 갈래를 견준다. `field` 는 `Field(discriminator="transport")`(pydantic 의 보통 판별자)이고,
`callable` 은 `transport` 가 없으면 `"stdio"` 로 읽는 호출 가능 `Discriminator` 다. 지금의
매니페스트는 `transport` 칸이 없으므로(stdio 하나), 칸이 없을 때 stdio 로 읽혀야 옛 파일이 그대로
읽힌다(ADR 0049 의 매니페스트 항목).

읽기 사례(두 갈래 모두): 칸 없음, http 모양, http 에 command 를 섞음, 모르는 값, stdio 에 url 을
섞음, stdio 에 command 없음. 표지는 받아들인 사례는 읽힌 모델의 종류이고, 거부 사례는
`ValidationError` 의 오류에 기대한 자리와 까닭의 쌍(`REJECTED`)이 있는 것이다. 스키마 사례의 표지는
`server` 의 갈래가 `StdioServer` 와 `HttpServer` 를 가리키는 `$ref` 둘인 것이다(`anyOf [X, null]`
처럼 수만 둘인 모양은 표지가 아니다).

소비 지점: `_MANIFEST_CONFIG` 와 같은 설정(`extra="forbid"`, `frozen`, 직렬화 기본값 required)의
모델을 FastAPI 응답 모델로 둔 앱에서 `app.openapi()` 를 뽑고(`tools/export_openapi.py` 의 모양), 그
JSON 을 openapi-typescript 7.13.0 CLI 로 TS 타입으로 만들고, `transport` 로 좁히는 소비 코드와
좁히지 않고 `url` 을 읽는 소비 코드(양성 대조)를 tsc 5.9.3 `--strict` 로 검사한다. 표지는 좁힌
코드가 0 으로 끝나고 좁히지 않은 코드가 TS2339 로 끝나는 것이다. 도구는 `--node-modules` 로
받는다(기본은 저장소의 `web/node_modules`. 워크트리에 없으면 주 체크아웃의 것을 준다).

돌리는 명령은 같은 폴더의 `README.md`에 있다.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Discriminator, Field, Tag, ValidationError

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from tools.probe_kit import Rounds  # noqa: E402

_CONFIG = ConfigDict(extra="forbid", frozen=True, json_schema_serialization_defaults_required=True)


class StdioServer(BaseModel):
    """stdio 로 띄우는 서버."""

    model_config = _CONFIG
    transport: Literal["stdio"] = "stdio"
    command: str
    args: tuple[str, ...] = ()
    secret_args: Mapping[str, tuple[str, ...]] = {}


class HttpServer(BaseModel):
    """주소로 붙는 서버."""

    model_config = _CONFIG
    transport: Literal["http"]
    url: str
    headers: Mapping[str, str] = {}
    secret_args: Mapping[str, tuple[str, ...]] = {}


def _transport_of(value: object) -> str:
    if isinstance(value, Mapping):
        tag = value.get("transport", "stdio")
        return str(tag) if isinstance(tag, str) else "unknown"
    tag = getattr(value, "transport", "stdio")
    return str(tag)


FieldUnion = Annotated[StdioServer | HttpServer, Field(discriminator="transport")]
CallableUnion = Annotated[
    Annotated[StdioServer, Tag("stdio")] | Annotated[HttpServer, Tag("http")],
    Discriminator(_transport_of),
]


class ManifestField(BaseModel):
    """`Field(discriminator=)` 갈래의 매니페스트."""

    model_config = _CONFIG
    name: str
    server: FieldUnion | None = None


class ManifestCallable(BaseModel):
    """호출 가능 `Discriminator` 갈래의 매니페스트."""

    model_config = _CONFIG
    name: str
    server: CallableUnion | None = None


BRANCHES: dict[str, type[ManifestField] | type[ManifestCallable]] = {
    "field": ManifestField,
    "callable": ManifestCallable,
}
INPUTS: dict[str, dict[str, object]] = {
    "omitted": {"command": "npx", "args": ["-y", "pkg"]},
    "http": {
        "transport": "http",
        "url": "http://127.0.0.1:8000/mcp",
        "headers": {"Authorization": "TOKEN"},
    },
    "http_with_command": {
        "transport": "http",
        "url": "http://127.0.0.1:8000/mcp",
        "command": "npx",
    },
    "unknown": {"transport": "grpc", "url": "http://127.0.0.1:8000/mcp"},
    "stdio_with_url": {"transport": "stdio", "command": "npx", "url": "http://127.0.0.1:8000/mcp"},
    "stdio_without_command": {"transport": "stdio", "args": ["-y", "pkg"]},
}
# 받아들여야 할 입력이 읽힐 모델의 이름. 없으면 거부를 기대한다.
ACCEPTED: dict[str, dict[str, str]] = {
    "field": {"http": "HttpServer"},
    "callable": {"omitted": "StdioServer", "http": "HttpServer"},
}
# 거부를 기대하는 입력이 거부될 자리(`loc` 를 점으로 이은 것)와 까닭(pydantic 의 `type`). 두 갈래가
# 같고, `omitted` 는 `field` 갈래에서만 거부된다. 이 쌍이 오류에 있어야 측정이다. 어떤 검증 오류든
# 세면 입력 오타 같은 엉뚱한 까닭의 거부도 측정이 된다(PR 직전 리뷰가 짚었다).
REJECTED: dict[str, tuple[str, str]] = {
    "omitted": ("server", "union_tag_not_found"),
    "http_with_command": ("server.http.command", "extra_forbidden"),
    "unknown": ("server", "union_tag_invalid"),
    "stdio_with_url": ("server.stdio.url", "extra_forbidden"),
    "stdio_without_command": ("server.stdio.command", "missing"),
}
GOOD_CONSUMER = """import type { components } from "./openapi";
type Server = NonNullable<components["schemas"]["{manifest}"]["server"]>;
export function where(server: Server): string {
  if (server.transport === "http") {
    return server.url;
  }
  return server.command;
}
"""
BAD_CONSUMER = """import type { components } from "./openapi";
type Server = NonNullable<components["schemas"]["{manifest}"]["server"]>;
export function where(server: Server): string {
  return server.url;
}
"""


def read_case(rounds: Rounds, branch: str, name: str) -> None:
    model = BRANCHES[branch]
    with rounds.round(f"read:{branch}:{name}") as current:
        try:
            parsed = model.model_validate({"name": "demo", "server": INPUTS[name]})
        except ValidationError as error:
            errors = error.errors()
            locations = [".".join(str(part) for part in item["loc"]) for item in errors]
            kinds = [item["type"] for item in errors]
            detail = {"locations": locations, "types": kinds, "message": str(error)[:300]}
            print(json.dumps({"case": f"read:{branch}:{name}", **detail}, ensure_ascii=False))
            expected = REJECTED.get(name) if name not in ACCEPTED[branch] else None
            seen = set(zip(locations, kinds, strict=True))
            current.mark(
                measured=expected is not None and expected in seen,
                result=f"rejected {locations} {kinds} expected={expected}",
            )
            return
        kind = type(parsed.server).__name__
        print(
            json.dumps(
                {"case": f"read:{branch}:{name}", "parsed": kind, "dump": parsed.model_dump()}
            )
        )
        expected = ACCEPTED[branch].get(name)
        current.mark(measured=expected is not None, result=f"accepted {kind} expected={expected}")


def openapi_of(model: type[BaseModel]) -> dict[str, object]:
    app = FastAPI()

    def handler() -> None:  # 응답 모델은 `response_model` 인자가 정한다
        raise NotImplementedError

    app.get("/manifest", response_model=model)(handler)
    return app.openapi()


def _union(server: object) -> dict[str, object]:
    """두 모양을 가르는 `oneOf` 를 든 스키마 조각. `server` 자체이거나, `server` 가 선택 칸이라 null
    과 나란히 `anyOf` 에 든 갈래다. 없으면 빈 표."""
    if not isinstance(server, dict):
        return {}
    if "oneOf" in server:
        return server
    nullable = server.get("anyOf")
    if isinstance(nullable, list):
        for variant in nullable:
            if isinstance(variant, dict) and "oneOf" in variant:
                return variant
    return {}


def _variant_names(union: Mapping[str, object]) -> list[str]:
    """`oneOf` 갈래가 가리키는 스키마 이름을 정렬해 돌려준다. `$ref` 가 아닌 갈래는 뺀다."""
    variants = union.get("oneOf")
    if not isinstance(variants, list):
        return []
    names: list[str] = []
    for variant in variants:
        if isinstance(variant, dict):
            ref = variant.get("$ref")
            if isinstance(ref, str):
                names.append(ref.rsplit("/", 1)[-1])
    return sorted(names)


def schema_case(rounds: Rounds, branch: str, work: Path) -> Path:
    """스키마를 뽑아 적고 모양을 기록한다. 계약 파일의 경로를 돌려준다."""
    model = BRANCHES[branch]
    contract = work / f"openapi-{branch}.json"
    with rounds.round(f"schema:{branch}") as current:
        document = openapi_of(model)
        contract.write_text(json.dumps(document, indent=2, sort_keys=True), encoding="utf-8")
        schemas = document["components"]["schemas"]
        server = schemas[model.__name__]["properties"]["server"]
        union = _union(server)
        facts = {
            "server_keys": sorted(server),
            "discriminator": union.get("discriminator"),
            "variants": union.get("oneOf"),
            "nullable": server.get("anyOf"),
            "stdio_required": schemas["StdioServer"].get("required"),
            "http_required": schemas["HttpServer"].get("required"),
            "url_schema": schemas["HttpServer"]["properties"]["url"],
            "headers_schema": schemas["HttpServer"]["properties"]["headers"],
        }
        print(json.dumps({"case": f"schema:{branch}", **facts}, ensure_ascii=False))
        current.mark(
            measured=_variant_names(union) == ["HttpServer", "StdioServer"],
            result=f"keys={facts['server_keys']} discriminator={facts['discriminator'] is not None}"
            f" transport_required={'transport' in (facts['stdio_required'] or [])}",
        )
    return contract


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )


def consumer_case(
    rounds: Rounds, branch: str, contract: Path, node_modules: Path, work: Path
) -> None:
    folder = work / f"ts-{branch}"
    folder.mkdir()
    cli = node_modules / "openapi-typescript" / "bin" / "cli.js"
    tsc = node_modules / "typescript" / "bin" / "tsc"
    manifest = BRANCHES[branch].__name__
    with rounds.round(f"consumer:{branch}") as current:
        generated = _run(
            ["node", str(cli), str(contract), "-o", str(folder / "openapi.ts")], folder
        )
        if generated.returncode != 0:
            current.mark(
                measured=False, result=f"openapi-typescript 실패: {generated.stderr[:200]}"
            )
            return
        types = (folder / "openapi.ts").read_text(encoding="utf-8")
        (folder / "good.ts").write_text(
            GOOD_CONSUMER.replace("{manifest}", manifest), encoding="utf-8"
        )
        (folder / "bad.ts").write_text(
            BAD_CONSUMER.replace("{manifest}", manifest), encoding="utf-8"
        )
        flags = [
            "--noEmit",
            "--strict",
            "--target",
            "es2022",
            "--module",
            "esnext",
            "--moduleResolution",
            "bundler",
            "--skipLibCheck",
        ]
        good = _run(["node", str(tsc), *flags, "good.ts"], folder)
        bad = _run(["node", str(tsc), *flags, "bad.ts"], folder)
        facts = {
            "transport_literals": sorted(
                {line.strip() for line in types.splitlines() if "transport:" in line}
            ),
            "good_exit": good.returncode,
            "good_output": (good.stdout + good.stderr)[:300],
            "bad_exit": bad.returncode,
            "bad_output": (bad.stdout + bad.stderr)[:300],
        }
        print(json.dumps({"case": f"consumer:{branch}", **facts}, ensure_ascii=False))
        bad_marked = bad.returncode != 0 and "TS2339" in bad.stdout + bad.stderr
        current.mark(
            measured=bad_marked and good.returncode == 0,
            result=f"good={good.returncode} bad=TS2339 literals={facts['transport_literals']}",
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--node-modules", type=Path, default=ROOT / "web" / "node_modules")
    parser.add_argument("--branch", choices=tuple(BRANCHES), action="append")
    options = parser.parse_args()
    branches: list[str] = options.branch or list(BRANCHES)
    header = {
        "pydantic": importlib.metadata.version("pydantic"),
        "fastapi": importlib.metadata.version("fastapi"),
        "python": sys.version.split()[0],
        "node_modules": str(options.node_modules),
    }
    print(json.dumps(header, ensure_ascii=False))
    rounds = Rounds()
    work = Path(tempfile.mkdtemp(prefix="mcp-http-manifest-"))
    steps: list[Callable[[], None]] = []
    for branch in branches:
        for name in INPUTS:
            read_case(rounds, branch, name)
        contract = schema_case(rounds, branch, work)
        steps.append(
            lambda b=branch, c=contract: consumer_case(rounds, b, c, options.node_modules, work)
        )
    for step in steps:
        step()
    print(json.dumps({"work": str(work)}))
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    sys.exit(main())
