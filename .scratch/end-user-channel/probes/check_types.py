"""`sse_id_frames.py` 의 모양 B·C·E 가 저장소의 pyright strict 와 타입 우회 검사를 지나는지.

pyright 는 `[tool.pyright].include` 밖을 검사 없이 "0 errors" 로 지나므로
(`docs/constitution/operations.md` 환경 규약 상세) 검사하는 동안만
`tests/_probe_end_user_*.py` 를 만들고 지운다. 모양 B(주해는 항목 유니온, yield 는
`ServerSentEvent`)는 오류가 나야 하고(대조군), 모양 C(`SkipJsonSchema` 로 멤버를 더한 유니온
별칭)와 E(같은 유니온을 별칭 없이)는 0 이어야 한다. 대조군이 오류를 내지 않으면 pyright 가 파일을
읽지 않은 것이다. 타입 우회 검사는 저장소 루트를 받아 `include` 디렉터리를 훑으므로 그 안의 프로브
파일도 본다.

    PYTHONUTF8=1 uv run python .scratch/end-user-channel/probes/check_types.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TESTS = ROOT / "tests"

COMMON = """
from collections.abc import AsyncIterator
from typing import Annotated, Literal

from fastapi.sse import ServerSentEvent
from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema


class Started(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    type: Literal["started"] = "started"
    run_id: str


class Finished(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    type: Literal["finished"] = "finished"
    output: str


type EndUserItem = Annotated[Started | Finished, Field(discriminator="type")]
type EndUserFrame = EndUserItem | SkipJsonSchema[ServerSentEvent]
"""

SHAPE_B = (
    COMMON
    + """

async def shape_b() -> AsyncIterator[EndUserItem]:
    yield ServerSentEvent(data=Started(run_id="r1"), id="0")  # 기대: 오류
"""
)

SHAPE_C = (
    COMMON
    + """

async def shape_c() -> AsyncIterator[EndUserFrame]:
    yield ServerSentEvent(data=Started(run_id="r1"), id="0")
    yield Finished(output="맨 항목")
"""
)

SHAPE_E = (
    COMMON
    + """

async def shape_e() -> AsyncIterator[EndUserItem | SkipJsonSchema[ServerSentEvent]]:
    yield ServerSentEvent(data=Started(run_id="r1"), id="0")
    yield Finished(output="맨 항목")
"""
)


def run_pyright(target: Path) -> tuple[int, int]:
    """(분석한 파일 수, 오류 수)."""
    result = subprocess.run(
        ["uv", "run", "pyright", "--outputjson", str(target)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=ROOT,
        check=False,
    )
    report = json.loads(result.stdout)
    for diagnostic in report["generalDiagnostics"]:
        print(f"  {diagnostic['severity']}: {diagnostic['message']}")
    return report["summary"]["filesAnalyzed"], report["summary"]["errorCount"]


def run_escapes() -> int:
    """타입 우회 검사는 저장소 루트를 받아 `include` 디렉터리를 훑는다. 그 안에 프로브가 있다."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_type_escapes.py"), str(ROOT)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=ROOT,
        check=False,
    )
    return result.returncode


def main() -> None:
    for name, source in (("b", SHAPE_B), ("c", SHAPE_C), ("e", SHAPE_E)):
        target = TESTS / f"_probe_end_user_{name}.py"
        target.write_text(source, encoding="utf-8")
        try:
            analyzed, errors = run_pyright(target)
            escapes = run_escapes()
            print(
                f"모양 {name.upper()}: 분석 {analyzed} 파일, pyright 오류 {errors}, "
                f"타입 우회 검사 종료 {escapes}"
            )
        finally:
            target.unlink()


if __name__ == "__main__":
    main()
