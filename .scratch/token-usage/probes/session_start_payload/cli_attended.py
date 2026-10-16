"""Claude Code 실행 파일에서 훅 환경의 `CLAUDE_CODE_SESSION_ATTENDED` 를 정하는 코드를 찾아 찍는다.

`run.sh` 의 두 갈래에서 이 변수가 갈렸다(헤드리스 0, 대화형 1). 데스크톱 세션의 훅이 받는 값은
그 갈래로 재지 못해, 그 값을 정하는 코드를 읽는다. 읽기만 한다. 실행 파일은 축약된 JS 를 품고
있어 이름(`mVe`, `_Z` 따위)이 판마다 바뀌므로, 모양으로 찾아 이름을 뽑은 뒤 그 이름으로 다시 찾는다.

먼저 실행 파일에 든 판(`// Version: X`)을 찍는다. 표지는 다섯이다. 하나라도 없으면 1로
끝난다(`.claude/rules/probes.md`의 첫 항목).
1. 자식 환경을 짓는 함수: `CLAUDE_CODE_SESSION_ATTENDED:<판정>()?"1":"0"`
2. 그 판정 함수의 본문 전체: `CLAUDE_CODE_SESSION_KIND` 가 `bg`·`daemon`·`daemon-worker` 이거나 또
   하나의 함수가 값을 내면 거짓, 대화형이면 참, 아니면 자식 세션이 아니면서 진입점이 목록에 있을 때
   참. 사이에 다른 문장이 없어야 맞는다
3. 훅 명령을 띄우는 자리: 그 함수를 펼친 뒤 `CLAUDE_PROJECT_DIR` 을 더한다
4. 셸 도구가 명령을 띄우는 자리: 그 함수를 `{sessionId:…}` 인자로 펼친다
5. 판정이 읽는 두 값의 출처: 대화형은 시작 인자로, 자식 세션은 시작할 때의 환경
   `CLAUDE_CODE_CHILD_SESSION` 으로 정한다

쓰는 법: 저장소 루트에서 `uv run python <이 파일> <claude.exe>`. 데스크톱 앱의 CLI 는 그 세션의
환경 `CLAUDE_CODE_EXECPATH` 가 가리킨다.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

NAME = rb"[A-Za-z_$][\w$]*"
VERSION = re.compile(rb"// Version: ([0-9]+\.[0-9]+\.[0-9]+)")
BUILDER = re.compile(
    rb"function ("
    + NAME
    + rb")\(e\)\{let n=\{CLAUDECODE:\"1\",CLAUDE_CODE_SESSION_ID:e\.sessionId,"
    + rb"CLAUDE_CODE_CHILD_SESSION:\"1\",CLAUDE_CODE_SESSION_ATTENDED:("
    + NAME
    + rb")\(\)\?\"1\":\"0\""
)
# 표지 2·5 는 사이에 다른 문장이 끼면 맞지 않게 실제 모양을 글자 그대로 적는다. 첫 판은 그 사이를
# `.{0,200}?` 로 두어, 대화형 판정 앞에 다른 조기 반환이 끼어도 맞았다(PR #277 CodeRabbit).
ORIGIN = re.compile(
    rb"setInteractive\(!"
    + NAME
    + rb"\),"
    + NAME
    + rb"\.setSpawnedByAttendedSession\(a\.CLAUDE_CODE_SESSION_ATTENDED\),"
    + NAME
    + rb"\.setEntrypoint\(a\.CLAUDE_CODE_ENTRYPOINT\),"
    + NAME
    + rb"\.setChildSession\(Boolean\(a\.CLAUDE_CODE_CHILD_SESSION\)\)"
)
SPAN = 400


def show(data: bytes, start: int, end: int) -> str:
    return data[max(0, start - SPAN) : end + SPAN].decode("utf-8", "replace").replace("\n", " ")


def markers(builder: bytes, judge: bytes) -> list[tuple[str, re.Pattern[bytes]]]:
    """표지 2~5 의 이름과 패턴. 표지 1 에서 뽑은 함수 이름으로 짓는다."""
    return [
        (
            "표지 2 판정 함수(앞에 진입점 목록)",
            re.compile(
                rb"function "
                + re.escape(judge)
                + rb"\(\)\{let e=a\.CLAUDE_CODE_SESSION_KIND;"
                + rb'if\(e==="bg"\|\|e==="daemon"\|\|e==="daemon-worker"\|\|'
                + NAME
                + rb"\(\)!==void 0\)return!1;let t="
                + NAME
                + rb"\(\);if\(t\.interactive\)return!0;"
                + rb"return!t\.childSession&&t\.entrypoint!==void 0&&"
                + NAME
                + rb"\.has\(t\.entrypoint\)\}"
            ),
        ),
        (
            "표지 3 훅 명령을 띄우는 자리",
            re.compile(
                rb"\.\.\." + re.escape(builder) + rb"\(" + NAME + rb"\),CLAUDE_PROJECT_DIR:"
            ),
        ),
        (
            "표지 4 셸 도구가 명령을 띄우는 자리",
            re.compile(rb"\.\.\." + re.escape(builder) + rb"\(\{sessionId:"),
        ),
        ("표지 5 대화형과 자식 세션의 출처", ORIGIN),
    ]


def main() -> int:
    data = Path(sys.argv[1]).read_bytes()
    version = VERSION.search(data)
    print(f"판: {version.group(1).decode() if version else '모름'}")
    builder = BUILDER.search(data)
    if builder is None:
        print("표지 1 없음: 자식 환경을 짓는 함수를 찾지 못했다")
        return 1
    builder_name, judge_name = builder.group(1), builder.group(2)
    print(f"== 표지 1 자식 환경 함수 {builder_name.decode()}, 판정 {judge_name.decode()}")
    print(show(data, builder.start(), builder.end()))
    missing = 0
    for label, pattern in markers(builder_name, judge_name):
        found = pattern.search(data)
        if found is None:
            print(f"{label} 없음")
            missing += 1
            continue
        print(f"== {label}")
        print(show(data, found.start(), found.end()))
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
