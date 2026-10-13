"""사람 몫 줄 검사. `KICKOFF.md`의 준비와 0~8단계마다 사람 몫 줄이 정해진 모양으로 있는지 본다.

킥오프의 진행 규율은 단계를 위에서 아래로 읽다가 사람 몫 줄에서 멈춘다(ADR 0028 "사람 몫"). 줄의
모양이 틀리면 그 일이 멈춤 없이 지나간다. 모양과 이 검사가 볼 것은 명세
`.scratch/kickoff-auto-flow/spec.md`의 "사람 몫 줄의 모양"과 "사람 몫 검사"다.

사람 몫 줄은 줄 머리(들여쓰기 없는 첫 칸)가 `사람 몫(결정): `, `사람 몫(허락): `,
`사람 몫(사람만): ` 가운데 하나이고 그 뒤에 내용이 있는 줄이다. 할 일이 없는 절에는 글자 그대로
`사람 몫: 없음` 한 줄을 둔다. 열 절은 `## 준비` 머리(뒤에 공백이나 마침표와 제목이 올 수 있고,
`## 준비물`은 아니다)의 절과 `## 0단계.`부터 `## 8단계.`까지의 머리의 절이다. 절은 그 머리에서 다음
`#`·`##` 머리까지다.

잡는 것:
- 열 절의 머리. 하나씩 이 차례로 있어야 한다. 하나도 맞지 않으면 파일을 잘못 가리킨 것이라 그것과
  닫히지 않은 펜스만 알린다(빈 범위의 초록은 판정이 아니다).
- 사람 몫 줄이 없는 절, 그리고 다른 사람 몫 줄과 한 절에 있는 `사람 몫: 없음`.
- 근사 모양. 줄 머리가 `사람`과 `몫`(사이의 공백은 없어도 된다)으로 시작하는데 위의 네 모양이 아닌
  줄이다. 갈래가 셋 밖이거나, 괄호나 콜론이 없거나, 콜론 뒤의 공백이 하나가 아니거나, 띄어 쓰지
  않았거나, 전각 괄호나 콜론을 썼거나, 내용이 비었다. 사람 몫으로 세지 않고 지나가게 두면 그 일이
  멈춤 없이 지나간다.
- 표지를 붙인 사람 몫 줄. 줄 머리의 목록 표지(`- `, `1. `), 인용 표지(`>`), 표의 첫 칸(`|`), 강조
  표지(`**`, `_`) 바로 뒤가 `사람`과 `몫`으로 시작하는 줄이다. 명세는 사람 몫 줄을 목록·표·인용 안에
  두지 않는다고 정했고, 이런 줄은 첫 칸이 아니라서 사람 몫으로 세어지지 않아 그 일이 멈춤 없이
  지나간다.
- `확인: ` 뒤에 확인이 없는 사람만 줄.
- 열 절 밖(머리말, 다른 절, 9단계 이후, 부록 목록)의 사람 몫 줄. 진행 규율은 거기로 가지 않는다.
- 닫히지 않은 펜스.

펜스는 CommonMark의 규칙으로 가른다. 들여쓰기 세 칸 이하의 백틱이나 틸드 셋 이상이 열고(백틱 펜스의
정보 문자열에는 백틱이 없다), 같은 문자로 연 길이 이상이고 그 뒤에 공백만 있는 줄이 닫는다. 펜스
안의 줄은 머리로도 사람 몫 줄로도 세지 않는다. 6단계의 펜스 안에 `## 심각도` 같은 줄이 있다. 단순히
펜스 줄마다 켜고 끄면 틸드 펜스나 4중 백틱 안의 3중 백틱에서 뒤집혀, 사람 몫 줄이 펜스 안으로
숨는다.

못 보는 것: 산문 속에 주어 없이 적힌 사람 몫, 줄이 가리키는 일이 정말 사람 몫인지, 갈래가 맞는지,
확인 명령이 옳은지, 줄이 그 일이 일어나는 차례에 있는지. 모두 뜻의 판단이라 런북을 고치는 사람과
리뷰가 본다. 표지 없이 들여 쓴 사람 몫 줄(목록 항목의 이어짐이든, 한 칸에서 세 칸 들여 쓴 최상위
문단이든)은 줄 머리가 첫 칸이 아니라서 사람 몫으로 세지 않고 모양도 보지 않는다. 목록 문맥을
따라가지 않아 둘을 가르지 못한다. 줄 머리가 아닌 자리(문장 가운데, 표의 둘째 칸부터)의 `사람 몫`
글자도 보지 않는다. 펜스 안에 들어간 사람 몫 줄도 세지 않으므로, 같은 절에 다른 사람 몫 줄이 있으면
조용히 지나간다(그 줄 하나뿐이면 줄이 없다고 잡힌다). 반대로 목록 항목이나 인용 바로 뒤에 빈 줄 없이
붙은 첫 칸의 줄은 CommonMark에서 그 항목의 게으른 이어짐(lazy continuation)이라 목록이나 인용
안인데, 이 검사는 사람 몫으로 센다. HTML 주석이나 HTML 블록 안의 첫 칸 줄도 화면에는 보이지 않지만
사람 몫으로 센다.

사용: `uv run python tools/check_human_share_lines.py [파일]`. 인자가 없으면 루트의 `KICKOFF.md`.
pytest의 저장소 상태 테스트(`tests/tools/test_check_human_share_lines.py`)가 돌리고, 따로 게이트를
두지 않는다(선례 `tools/check_adr_pointers.py`).
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KICKOFF = ROOT / "KICKOFF.md"
SECTION_KEYS = ("준비", *(f"{n}단계" for n in range(9)))
NONE_LINE = "사람 몫: 없음"

_SECTION = re.compile(r"## (?:(준비)(?=[\s.]|$)|([0-8]단계)\.)")
_BOUNDARY = re.compile(r" {0,3}#{1,2}(?:[ \t]|$)")
_SHARE = re.compile(r"사람 몫\((결정|허락|사람만)\): \S")
_NEAR = re.compile(r"사람\s*몫")
# 강조 표지는 소유 한정(`{1,2}+`)이다. 그냥 `{1,2}`면 `*`나 `_`만 길게 이어진 줄(구분선)을
# 1칸·2칸으로 나누는 길을 모두 되짚는다. 30자 안팎에서 1초에 가까웠고 글자마다 늘었다(PR 직전 리뷰가
# 손으로 봤다).
_MARKED = re.compile(
    r"[ \t]*(?:(?:[-*+]|\d{1,9}[.)])[ \t]+|>[ \t]*|\|[ \t]*|\*{1,2}+|_{1,2}+)+사람\s*몫"
)
_CONFIRM = re.compile(r"확인: \S")
_FENCE = re.compile(r" {0,3}(`{3,}|~{3,})(.*)")
_CLOSING = re.compile(r" {0,3}(`{3,}|~{3,})[ \t]*")

_NO_SECTIONS = "열 절의 머리가 하나도 없다 — 이 파일을 가리킨 것이 맞는지 본다"
_NEAR_SHAPE = "모양이 맞지 않는 사람 몫 줄이다(갈래, 괄호, 콜론과 그 뒤의 공백 하나, 내용을 본다)"
_MARKED_SHAPE = (
    "목록·인용·표·강조 표지를 붙인 사람 몫 줄이다(사람 몫 줄은 표지 없는 첫 칸의 문단 줄이다)"
)
_OUTSIDE = "열 절 밖의 사람 몫 줄이다"
_NO_CONFIRM = "사람만 줄에 `확인: `이 없다"
_NONE_NOT_ALONE = "`사람 몫: 없음`이 이 절의 유일한 사람 몫 줄이 아니다"
_UNCLOSED = "닫히지 않은 펜스다"


def _label(key: str) -> str:
    return "## 준비" if key == "준비" else f"## {key}."


def _opening(line: str) -> str | None:
    """펜스를 여는 줄이면 그 펜스 글자(`` ``` ``, `~~~~` 등)."""
    opening = _FENCE.fullmatch(line)
    if opening is None:
        return None
    fence, info = opening.group(1), opening.group(2)
    if fence[0] == "`" and "`" in info:
        return None
    return fence


def _closes(fence: str, line: str) -> bool:
    closing = _CLOSING.fullmatch(line)
    return closing is not None and closing.group(1).startswith(fence)


def _outside_fences(text: str) -> tuple[list[tuple[int, str]], int | None]:
    """펜스 밖의 (1부터 센 줄 번호, 줄)과, 닫히지 않은 펜스가 있으면 그것을 연 줄 번호."""
    kept: list[tuple[int, str]] = []
    fence = ""
    opened_at: int | None = None
    for number, line in enumerate(text.splitlines(), start=1):
        if fence:
            if _closes(fence, line):
                fence, opened_at = "", None
            continue
        opening = _opening(line)
        if opening is not None:
            fence, opened_at = opening, number
            continue
        kept.append((number, line))
    return kept, opened_at


def _section_key(line: str) -> str | None:
    found = _SECTION.match(line)
    if found is None:
        return None
    return found.group(1) or found.group(2)


def _headings(kept: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """펜스 밖의 줄에서 열 절의 머리를 (줄 번호, 열쇠)로 나온 차례대로."""
    return [(number, key) for number, line in kept if (key := _section_key(line)) is not None]


def sections_in(text: str) -> list[str]:
    """펜스 밖에서 찾은 열 절의 열쇠(`준비`, `0단계` …)를 나온 차례로."""
    kept, _ = _outside_fences(text)
    return [key for _, key in _headings(kept)]


def _heading_problems(headings: list[tuple[int, str]]) -> list[tuple[int, str]]:
    keys = [key for _, key in headings]
    found = [(0, f"머리가 없다 — `{_label(key)}`") for key in SECTION_KEYS if key not in keys]
    seen: set[str] = set()
    last = -1
    for number, key in headings:
        if key in seen:
            found.append((number, f"머리가 또 있다 — `{_label(key)}`"))
            continue
        seen.add(key)
        index = SECTION_KEYS.index(key)
        if index < last:
            before = _label(SECTION_KEYS[last])
            reason = f"머리의 차례가 어긋난다 — `{_label(key)}`가 `{before}` 뒤에 있다"
            found.append((number, reason))
        else:
            last = index
    return found


def _kind(line: str) -> str | None:
    """사람 몫 줄의 갈래(`결정`, `허락`, `사람만`, `없음`), 근사 모양이면 `근사`, 표지를 붙였으면
    `표지`, 아니면 None."""
    if line.rstrip() == NONE_LINE:
        return "없음"
    share = _SHARE.match(line)
    if share is not None:
        return share.group(1)
    if _NEAR.match(line):
        return "근사"
    if _MARKED.match(line):
        return "표지"
    return None


def problems_in(text: str) -> list[str]:
    """어긋남을 줄 번호 차례로 `줄: 이유`로 낸다. 파일 전체의 어긋남은 줄 0이다."""
    kept, unclosed = _outside_fences(text)
    found: list[tuple[int, str]] = []
    if unclosed is not None:
        found.append((unclosed, _UNCLOSED))
    headings = _headings(kept)
    if not headings:
        found.append((0, _NO_SECTIONS))
        return [f"{number}: {reason}" for number, reason in sorted(found)]
    found.extend(_heading_problems(headings))
    sections: list[tuple[int, str, list[tuple[int, str]]]] = []
    current: list[tuple[int, str]] | None = None
    for number, line in kept:
        if _BOUNDARY.match(line):
            key = _section_key(line)
            current = None
            if key is not None:
                current = []
                sections.append((number, key, current))
            continue
        kind = _kind(line)
        if kind is None:
            continue
        if kind == "근사":
            found.append((number, _NEAR_SHAPE))
        elif kind == "표지":
            found.append((number, _MARKED_SHAPE))
        elif current is None:
            found.append((number, _OUTSIDE))
        else:
            if kind == "사람만" and _CONFIRM.search(line) is None:
                found.append((number, _NO_CONFIRM))
            current.append((number, kind))
    for heading, key, shares in sections:
        if not shares:
            found.append((heading, f"이 절에 사람 몫 줄이 없다 — `{_label(key)}`"))
        elif len(shares) > 1:
            found.extend((number, _NONE_NOT_ALONE) for number, kind in shares if kind == "없음")
    return [f"{number}: {reason}" for number, reason in sorted(found)]


def main(path: Path = KICKOFF) -> int:
    """`path`를 판정한다. 어긋남이 있거나 파일이 없으면 1."""
    if not path.is_file():
        print(f"{path.as_posix()}가 없다 — 이 파일을 가리킨 것이 맞는지 본다")
        return 1
    problems = problems_in(path.read_text(encoding="utf-8"))
    for problem in problems:
        print(f"{path.name}:{problem}")
    return 1 if problems else 0


if __name__ == "__main__":
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8")
    sys.exit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else KICKOFF))
