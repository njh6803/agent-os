"""레벨 스윕의 갈래를 브랜치 이름으로 고른다(ADR 0029 이력 2026-10-13).

`uv run python tools/model_sweep.py <브랜치>`는 그 브랜치가 스윕하는 종류이고 기간 안이면 지시문의
"모델" 줄에 옮길 값을, 아니면 `스윕 밖`을 한 줄 찍는다. `next-session` 의 `directive.md` 가 결정표
칸이 `Opus 5.5 / xhigh`인 지시문을 쓸 때 부른다. 배정의 정의는 스윕 프로브의 사전
등록(`.scratch/harness/probes/model_sweep/README.md`)이 원천이고, 이 파일은 그것을 옮긴다.

- 종류: `feature/`는 구현, `chore/`와 `claude/`는 하네스다(소급 측정 사전 등록의 브랜치 종류).
  스윕을 멈춘 종류는 `SWEPT`에서 뺀다.
- 갈래: 이름을 UTF-8로 인코딩한 바이트의 SHA-256 첫 바이트가 짝수면 `BASE`, 홀수면 `COMPARISON`.
  `arm`이 이 배정이고, 스윕의 판정(`tools/model_sweep_judge.py`)도 이것을 가져다 쓴다.
- 종류와 접두사는 사전 등록 절이 원천이다. `prereg_section`이 README에서 그 절을 떼고
  `prereg_kinds`가 그 절에서 읽는다. 테스트가 `SWEPT`를 그것과 대 본다(멈춘 종류가 빠지는 것만
  허용한다).
- 기간: `END`(UTC 날짜, 사전 등록의 끝) 전날까지. 그날부터는 `스윕 밖`을 찍고, 스윕하는 종류의
  브랜치면 stderr로 기간이 끝났고 판정은 그 7일 뒤라고 알린다.

못 보는 것: 그 브랜치를 지시문으로 여는지, 결정표 칸이 무엇인지는 모른다. 부르는 쪽이 칸이 `BASE`일
때만 부른다. 이름을 갈래를 보고 바꿨는지도 모른다.

stdout과 stderr는 UTF-8로 찍는다. 부르는 셸에 `PYTHONUTF8`이 있다고 가정하지 않는다(윈도의 파이프는
cp949라 `스윕 밖`이 깨진다).

종료 코드: 0 갈래나 `스윕 밖`을 찍었다, 2 인자가 브랜치 하나가 아니다.
"""

from __future__ import annotations

import hashlib
import io
import re
import sys
from datetime import UTC, date, datetime

BASE = "Opus 5.5 / xhigh"
COMPARISON = "Opus 5.5 / medium"
ARMS = (BASE, COMPARISON)
SWEPT: dict[str, tuple[str, ...]] = {"구현": ("feature/",), "하네스": ("chore/", "claude/")}
END = date(2026, 12, 8)
OUTSIDE = "스윕 밖"
PREREG = ".scratch/harness/probes/model_sweep/README.md"
PREREG_START, PREREG_END = "<!-- 사전 등록 시작 -->", "<!-- 사전 등록 끝 -->"


def kind(branch: str, table: dict[str, tuple[str, ...]] | None = None) -> str | None:
    """`table`(기본 `SWEPT`)의 종류면 그 이름, 아니면 None. 스윕의 판정은 사전 등록에서 읽은 표를
    넘긴다."""
    for name, prefixes in (SWEPT if table is None else table).items():
        if branch.startswith(prefixes):
            return name
    return None


def arm(branch: str) -> str:
    """이름만으로 정해지는 배정. 기간과 종류를 보지 않는다(스윕의 판정이 끝 뒤에 쓴다)."""
    first = hashlib.sha256(branch.encode("utf-8")).digest()[0]
    return BASE if first % 2 == 0 else COMPARISON


def assign(branch: str, today: date) -> str | None:
    """기간 안의 스윕하는 종류면 갈래의 값, 아니면 None."""
    if today >= END or kind(branch) is None:
        return None
    return arm(branch)


def prereg_section(text: str) -> str:
    """README에서 두 표지 사이의 사전 등록 절. 표지가 하나라도 없으면 빈 문자열이다. 스윕 프로브와
    소급 측정 프로브의 README가 같은 표지를 쓴다."""
    if PREREG_START not in text or PREREG_END not in text:
        return ""
    return text.split(PREREG_START, 1)[1].split(PREREG_END, 1)[0]


def prereg_kinds(section: str) -> dict[str, tuple[str, ...]]:
    """사전 등록 절의 "스윕하는 종류는 …" 줄에서 종류마다 백틱으로 적은 접두사를 읽는다.

    그 절은 해시로 고정되어 있어 읽은 값도 바뀌지 않는다. 테스트가 `SWEPT`를 이 값과 대 보고,
    스윕의 판정이 `SWEPT`에서 빠진 종류를 사람이 멈춘 것으로 본다. 줄이 없으면 빈 사전이다.
    """
    line = next((ln for ln in section.splitlines() if "스윕하는 종류는" in ln), "")
    found: dict[str, tuple[str, ...]] = {}
    for name, inner in re.findall(r"(\w+)\(((?:`[^`]+`(?:, )?)+)\)", line):
        found[name] = tuple(re.findall(r"`([^`]+)`", inner))
    return found


def sweep_problems(
    swept: dict[str, tuple[str, ...]], registered: dict[str, tuple[str, ...]]
) -> list[str]:
    """`swept`가 사전 등록의 종류와 어긋난 곳. 종류가 빠진 것(사람이 멈춘 것)은 어긋남이 아니다."""
    return [
        f"SWEPT 의 {name}{prefixes} 이 사전 등록의 {registered.get(name)} 과 다르다"
        for name, prefixes in swept.items()
        if registered.get(name) != prefixes
    ]


def main(argv: list[str] | None = None, today: date | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("쓰는 법: uv run python tools/model_sweep.py <브랜치>", file=sys.stderr)
        return 2
    now = today if today is not None else datetime.now(UTC).date()
    value = assign(args[0], now)
    if now >= END and kind(args[0]) is not None:
        notice = f"스윕 기간이 {END.isoformat()}에 끝났다. 결정표 칸을 그대로 쓴다."
        print(f"{notice} 판정은 그 7일 뒤에 {PREREG} 대로 한다", file=sys.stderr)
    print(value if value is not None else OUTSIDE)
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
    sys.exit(main())
