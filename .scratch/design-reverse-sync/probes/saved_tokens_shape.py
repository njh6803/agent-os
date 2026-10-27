"""디자인 시스템 아티팩트의 페이지가 저장한 `tokens.json` 의 꼴이 02 의 저장본과 같은지 잰다(티켓 10
의 결과 10).

꼴은 자리(키를 따라 내려간 경로, 배열은 `[]`, 색 값 객체의 키는 테마 이름이라 `<테마>` 하나로
접는다)마다 그 자리에 나온 값의 타입 모음이다. 실험군은 티켓 10 이 받은
저장본(`received/tokens-1793126431-7500.json`, 판 `1793126431-7500`)과 02 가 임시 아티팩트에서 받은
저장본(`page-saved-tokens.json`)이다. 양성 대조는 02 가 같은 아티팩트에 올린, 페이지가 저장하기 전의
파일(`uploaded-tokens.json`)과 02 의 저장본이다. 페이지가 저장하며 꼴을 바꾸므로(반투명 값의 객체화,
굵기의 문자열화, 빈 칸 채우기) 이 비교가 그 차이를 내야 실험군의 "다른 자리 0" 이 꼴이 같다는 뜻이
된다. 02 의 두 파일은 `FIXTURE_COMMIT` 에서 꺼낸다(`.claude/rules/probes.md` 의 스냅샷 항목).

표지는 둘이다. 받은 파일의 sha256 이 티켓이 적은 값이다(재려는 파일을 읽었다). 양성 대조의 다른
자리가 하나 이상이다(비교가 페이지의 꼴 바꿈을 가른다). 둘 가운데 하나라도 없으면 측정이 아니라 종료
코드 1 이다. 결과는 JSON 한 줄이고, 실험군의 다른 자리 수는 판정하지 않고 찍는다.

못 보는 것: 꼴만 보고 값은 보지 않는다(값의 차이는 확인 명령의 맞대기가 본다). 다른 형식 판의
페이지가 저장한 꼴은 이 두 판(02 의 형식 판 `1792632348-7c2b`, 티켓 10 의 실제 아티팩트) 밖이다.

저장소 루트에서 돈다: uv run python .scratch/design-reverse-sync/probes/saved_tokens_shape.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

RECEIVED = Path(".scratch/design-reverse-sync/probes/received/tokens-1793126431-7500.json")
RECEIVED_SHA256 = "f8e91e9841425744d00b29acc53d837923b5bfeff4c90ab061c0d33d44866df1"
FIXTURE_COMMIT = "71433a0d"
FIXTURES = "web/tools/sync-design-system/fixtures"

Shape = dict[str, set[str]]


def kind(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int | float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "list"
    return "object"


def walk(value: object, path: str, out: Shape) -> None:
    out.setdefault(path, set()).add(kind(value))
    if isinstance(value, dict):
        themes = path.endswith(".value")
        for key, item in value.items():
            walk(item, f"{path}.{'<테마>' if themes else key}", out)
    elif isinstance(value, list):
        for item in value:
            walk(item, f"{path}[]", out)


def shape(text: str) -> Shape:
    out: Shape = defaultdict(set)
    walk(json.loads(text), "", out)
    return dict(out)


def differing(left: Shape, right: Shape) -> list[str]:
    return sorted(path for path in left.keys() | right.keys() if left.get(path) != right.get(path))


def fixture(name: str) -> str:
    return subprocess.run(
        ["git", "show", f"{FIXTURE_COMMIT}:{FIXTURES}/{name}"],
        capture_output=True,
        check=True,
        encoding="utf-8",
        timeout=30,
    ).stdout


def main() -> int:
    received = RECEIVED.read_bytes()
    sha_ok = hashlib.sha256(received).hexdigest() == RECEIVED_SHA256
    saved = shape(fixture("page-saved-tokens.json"))
    experiment = differing(shape(received.decode("utf-8")), saved)
    control = differing(shape(fixture("uploaded-tokens.json")), saved)
    measured = sha_ok and len(control) > 0
    print(
        json.dumps(
            {
                "measured": measured,
                "received_sha256_ok": sha_ok,
                "paths_02_saved": len(saved),
                "experiment_differing": experiment,
                "control_differing": control,
            },
            ensure_ascii=False,
        )
    )
    return 0 if measured else 1


if __name__ == "__main__":
    sys.exit(main())
