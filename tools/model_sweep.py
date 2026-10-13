"""레벨 스윕의 갈래를 브랜치 이름으로 고른다(ADR 0029 이력 2026-10-13).

`uv run python tools/model_sweep.py <브랜치>`는 그 브랜치가 스윕하는 종류이고 기간 안이면 지시문의
"모델" 줄에 옮길 값을, 아니면 `스윕 밖`을 한 줄 찍는다. `next-session` 3단계가 결정표 칸이
`Opus 5.5 / xhigh`인 지시문을 쓸 때 부른다. 배정의 정의는 스윕 프로브의 사전
등록(`.scratch/harness/probes/model_sweep/README.md`)이 원천이고, 이 파일은 그것을 옮긴다.

- 종류: `feature/`는 구현, `chore/`와 `claude/`는 하네스다(소급 측정 사전 등록의 브랜치 종류).
  스윕을 멈춘 종류는 `SWEPT`에서 뺀다.
- 갈래: 이름을 UTF-8로 인코딩한 바이트의 SHA-256 첫 바이트가 짝수면 `BASE`, 홀수면 `COMPARISON`.
- 기간: `END`(UTC 날짜, 사전 등록의 끝) 전날까지. 그날부터는 `스윕 밖`을 찍고, stderr로 기간이
  끝났고 판정은 그 7일 뒤라고 알린다.

못 보는 것: 그 브랜치를 지시문으로 여는지, 결정표 칸이 무엇인지는 모른다. 부르는 쪽이 칸이 `BASE`일
때만 부른다. 이름을 갈래를 보고 바꿨는지도 모른다.

stdout과 stderr는 UTF-8로 찍는다. 부르는 셸에 `PYTHONUTF8`이 있다고 가정하지 않는다(윈도의 파이프는
cp949라 `스윕 밖`이 깨진다).

종료 코드: 0 갈래나 `스윕 밖`을 찍었다, 2 인자가 브랜치 하나가 아니다.
"""

from __future__ import annotations

import hashlib
import io
import sys
from datetime import UTC, date, datetime

BASE = "Opus 5.5 / xhigh"
COMPARISON = "Opus 5.5 / medium"
ARMS = (BASE, COMPARISON)
SWEPT: dict[str, tuple[str, ...]] = {"구현": ("feature/",), "하네스": ("chore/", "claude/")}
END = date(2026, 12, 8)
OUTSIDE = "스윕 밖"
PREREG = ".scratch/harness/probes/model_sweep/README.md"


def kind(branch: str) -> str | None:
    """스윕하는 종류면 그 이름, 아니면 None."""
    for name, prefixes in SWEPT.items():
        if branch.startswith(prefixes):
            return name
    return None


def assign(branch: str, today: date) -> str | None:
    """기간 안의 스윕하는 종류면 갈래의 값, 아니면 None."""
    if today >= END or kind(branch) is None:
        return None
    first = hashlib.sha256(branch.encode("utf-8")).digest()[0]
    return BASE if first % 2 == 0 else COMPARISON


def main(argv: list[str] | None = None, today: date | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("쓰는 법: uv run python tools/model_sweep.py <브랜치>", file=sys.stderr)
        return 2
    now = today if today is not None else datetime.now(UTC).date()
    value = assign(args[0], now)
    if value is None and now >= END and SWEPT:
        notice = f"스윕 기간이 {END.isoformat()}에 끝났다. 결정표 칸을 그대로 쓴다."
        print(f"{notice} 판정은 그 7일 뒤에 {PREREG} 대로 한다", file=sys.stderr)
    print(value if value is not None else OUTSIDE)
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
    sys.exit(main())
