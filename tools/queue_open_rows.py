"""열린 대기열 행을 회차, 날짜, 대상 파일로 세고, 닫힌 행까지 낱말로 찾는다(찾기는 끝의 절).

`next-session` 결정표의 하네스 chore 배치 조건(`.scratch/retro-queue.md`의 열린 항목 가운데 회차 3
이상인 것)과 retro 5단계의 만료(승인 칸의 가장 늦은 날짜로부터 14일)를 세는 자리다(ADR 0036). 같은
대상 파일이 셋 이상인 행은 2026-10-19까지 둘째 계기였고, 지금은 chore 를 고른 뒤 함께 묶을 행으로만
찍는다. 그 계기가 하네스 chore 뒤에 또 chore 를 불렀다. 세션마다 손이나 스크래치 스크립트로 세다가,
회차를 "무엇" 칸에 적은 옛 행(17)이 빠졌고(대기열 167, 일지 2026-10-07-12) 근거로 든 파일까지
대상으로 세어 `.claude/rules/tools.md`가 대상 아홉으로 나왔다(일지 2026-10-16-30).

판정.
- 행: `| N |`로 시작하는 줄이고, 이스케이프하지 않은 `|`로 칸을 가른다. 칸이 넷(#, 무엇, 어디로,
  승인)이 아니면 세지 않고 번호를 알리며 1로 끝난다. 조용히 빠지는 행이 이 도구가 막으려는 실패다.
- 닫힘: 무엇 칸이 취소선(`~~`, 앞의 굵게 `**`는 걷는다)으로 시작하면 닫힌 행이다. 부분 반영(141)은
  취소선이 없어 열린 행이다.
- 회차: `<수>회차`를 승인 칸에서 찾고, 없으면 무엇 칸, 그다음 어디로 칸에서 찾는다. 한 칸에 여럿이면
  가장 큰 것이다. 회차는 오르기만 하는데 옛 글이 남을 수 있어서다. 17은 무엇 칸에 `**근거 추가**`
  뒤로 `**3회차**`를 더했다.
- 대상과 인용: 어디로 칸의 코드 스팬 가운데 경로인 것(`/`가 들었거나 확장자가 붙은 파일 이름이고,
  공백·`{`·`<`·`$`가 없고 `-`·`/`로 시작하지 않는다. 옵션과 슬래시 명령을 뺀다)만 센다. 괄호 밖이면
  대상, 괄호 안이면 근거로 든 인용이다. 2026-10-16의 열린 행에서 `.claude/rules/tools.md`를 인용으로
  센 여섯 행은 모두 괄호 안에 그 경로를 든다. 코드 스팬 안의 괄호는 깊이를 바꾸지 않는다. 같은
  행에서 대상이면서 인용이면 대상으로만 센다.
- 사람 몫: 어디로 칸이 `사람 몫:`으로 시작하는 행. 앞의 굵게 표시(`**`)는 벗기고 본다. 사람이 할
  일을 세션마다 다시 보며 회차가 쌓여 chore 계기가 됐다(238, 11회차). 그래서 회차 3 이상에도
  만료에도 넣지 않고 따로 찍는다.
- 만료: 사람 몫도 회차 3 이상도 아닌 열린 행 가운데 승인 칸의 가장 늦은 날짜(승인 날짜와 일지
  파일명의 `YYYY-MM-DD`)가 기준일(`--today`, 기본 오늘)의 14일 전보다 이른 것. 회차 3 이상인 행은
  chore 가 반영할 때까지 남긴다(chore 는 기능의 마지막 티켓 뒤에만 열려 14일을 넘기기 쉽다). 날짜가
  없는 행은 따로 찍는다.
  만료는 고쳐졌다는 판정이 아니라 목록에서 내리는 것이다. 닫는 일과 다시 일어났을 때 잇는 일은 retro
  5단계가 한다.
- 같은 대상 파일은 파일 대상만 묶는다. `/`로 끝나는 디렉터리와 `*`가 든 패턴은 여러 파일을 담는
  그릇이라 묶으면 늘 셋을 넘는다(`tools/`가 여덟 행). 그것들은 따로 찍는다. 인용 경로도 행 번호와
  함께 늘 찍어, 아래 못 보는 것의 두 방향을 출력에서 사람이 가른다.

못 보는 것.
- 괄호 밖 본문의 인용은 대상으로 센다(286의 "`.claude/rules/tools.md`의 반박 시험을 거친다", 57의
  "…의 단독 실행 규약과 함께 본다"). 반대로 괄호 안의 대상은 인용으로 세어 대상 수에서 빠진다(141의
  "사용처(`tools/hook_pr_head_sync.py`, …)"). 둘 다 시험으로 고정했다.
- 고칠 파일이 아닌데 경로 모양인 것을 대상으로 센다. git이 만드는 `index.lock`(293), 훅이 지켜보는
  경로(227의 `docs/adr/`·`.scratch/retro-queue.md`)가 그렇다. 부분 반영 행(141)에서 이미 반영한 몫의
  대상도 그대로 센다.
- 같은 파일을 다른 이름으로 적은 것(`operations.md`와 `docs/constitution/operations.md`, 디렉터리
  `tools/`와 그 아래 파일)은 다른 대상이다.
- 결정표의 둘째 조건인 "사용자가 순서를 올린 항목"은 행에 표지가 없어 세지 않는다.
- 회차를 숫자 아닌 말("세 번째")로만 적은 행은 회차를 모른다고 센다.
- 승인 칸의 날짜는 회차가 아닌 일(부분 반영, 승인)의 날짜도 가장 늦은 날짜로 센다. 그래서 반영을
  적은 날이 늦으면 새 회차가 없어도 만료하지 않는다. 무엇·어디로 칸의 날짜는 보지 않는다. 둘 다
  시험으로 고정했다.
- 어디로 칸의 백틱이 홀수 개면 닫히지 않은 백틱 뒤의 경로를 세지 않는다. 2026-10-16의 대기열에는
  그런 행이 없다(PR 직전 버그 리뷰가 찾아봤다).

쓰임: `uv run python tools/queue_open_rows.py [--queue <경로> | --ref <커밋>] [--rows]
[--today YYYY-MM-DD]`. 기본은 지금
폴더의 `.scratch/retro-queue.md`라 저장소 루트에서 친다. `--ref`는 `git show <커밋>:<그 경로>`로
읽는다. 워크트리에서 병합한 뒤에는 `git fetch origin` 뒤 `--ref origin/main`으로 다른 PR이 더한
행까지 센다. `--rows`는 열린 행마다 회차와 대상·인용을 한 줄씩 더 찍는다. 종료 0은 모두 읽었다, 1은
칸이 넷이 아닌 행이 있다(그 행을 뺀 수다), 2는 인자가 틀렸거나 대기열을 읽지 못했다.

찾기: `uv run python tools/queue_open_rows.py [--queue <경로> | --ref <커밋>] --search <정규식>
[--search <정규식> ...]`. retro 5단계의 행 찾기(새 행을 쓰기 전에 같은 일을 다룬 행을 찾는다)가
쓴다. Grep 도구는 대기열의 긴 행을 `[Omitted long matching line]`으로만 내고, Bash 로 행을
열면(`grep`·`sed`·`cut`) 한 행 전체가 실려(일지 2026-10-22-16 의 306행은 4,079자다), 세션마다 맞은
행을 Read 로 다시 열거나 스크래치 스크립트를 지었다(대기열 425).
- 닫힌 행까지 `| N |`로 시작하는 줄의 원문 전체(번호 칸과 마크다운 표지까지)에 정규식을 맞추고,
  여럿이면 하나라도 맞은 행이다. 맞은 행마다 번호, 파일의 줄 번호(줄바꿈으로만 센다. Read 의
  `offset`이다), 열림·닫힘, 회차(위의 회차 판정), 무엇 칸의 머리, 승인 칸을 한 줄로 대기열의
  차례대로 찍는다. 기본 출력은 내지 않으므로 `--rows`·`--today`와 함께 주면 쓰임 오류다.
- 낱말은 정규식이다. `[`·`(`·`|`·`\\` 같은 문자는 정규식으로 읽혀, `[Omitted long matching line]`은
  문자 클래스라 거의 모든 행에 맞는다. 셸에서 따옴표 없이 주면 셸도 그 문자를 읽으므로, 공백과 그
  문자는 아무 글자에나 맞는 `.`으로 바꿔 준다. 맞은 행 수에는 상한이 없어, `tools/`처럼 넓은 낱말은
  수백 행을 낸다.
- 머리는 무엇 칸의 앞의 굵게·취소선 표지를 걷고 처음 닫는 표지(`**`, `~~`)까지이고
  `HEAD_CHARS`(120)자에서 자른다. 승인 칸은 첫 승인으로 시작해 회차와 닫힘을 뒤에 덧붙여 가는
  칸이라, 길면 앞 `APPROVAL_HEAD`(80)자(첫 승인)와 끝 `APPROVAL_TAIL`(160)자(가장 늦게 덧붙인 글의
  꼬리)를 남기고 가운데를 줄인다. 덧붙인 글이 길면 끝에 회차나 `**닫힘`의 시작이 들지 않으므로
  회차와 열림·닫힘은 칸 전체에서 판정해 따로 찍는다. 자르거나 줄였으면 그 글자 수를 적는다.
- 종료 0은 맞은 행을 모두 읽었다(맞은 행이 없어도 0이다), 1은 맞은 행 가운데 칸이 넷이 아닌 행이
  있다(그 행은 칸을 읽지 않고 번호와 줄만 찍고, 머리 줄에 그 수를 따로 센다), 2는 인자나 정규식이
  틀렸거나 대기열을 읽지 못했다.

찾기의 못 보는 것. 셋 다 시험으로 고정했다.
- 어디에 맞았는지는 찍지 않는다. 어디로 칸이나 잘린 자리에서만 맞은 행도 찍히지만 그 낱말은 출력에
  없다. 머리로 가리지 못하면 그 줄을 연다.
- 수를 찾으면 그 수를 품은 더 긴 수에도 맞는다(`425`가 `1425`에). `(?<!\\d)425(?!\\d)`로 좁힌다.
  `\\b`는 수와 한글 사이를 경계로 보지 않아 `425의`를 놓친다.
- `| N |`로 시작하지 않는 줄(붙여 쓴 칸 `|425|`, 들여 쓴 행, 본문)은 기본 출력처럼 행이 아니라 찾지
  않는다.
"""

from __future__ import annotations

import io
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from pathlib import Path

QUEUE = Path(".scratch/retro-queue.md")
MIN_ROUNDS = 3
MIN_ROWS = 3
EXPIRY_DAYS = 14
HUMAN = "사람 몫"
HUMAN_MARK = f"{HUMAN}:"
SHARED = f"{MIN_ROWS}개 행 이상"
HEAD_CHARS = 120
APPROVAL_HEAD = 80
APPROVAL_TAIL = 160
USAGE = (
    "쓰임: uv run python tools/queue_open_rows.py [--queue <경로> | --ref <커밋>] [--rows]"
    " [--today YYYY-MM-DD]\n"
    "      uv run python tools/queue_open_rows.py [--queue <경로> | --ref <커밋>]"
    " --search <정규식> [--search <정규식> ...]\n"
)
GIT_TIMEOUT = 30

ROW = re.compile(r"^\| (\d+) \|")
CELL_SPLIT = re.compile(r"(?<!\\)\|")
ROUND = re.compile(r"(\d+)회차")
DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")
FILE_NAME = re.compile(r"^[\w.-]+\.(md|py|toml|ya?ml|json|lock|ts|tsx|mjs|ps1|sh)$")
NOT_PATH = re.compile(r"[\s{<$]")
CELL_NAMES = ("무엇", "어디로", "승인")
ROUND_CELLS = ("승인", "무엇", "어디로")  # 회차를 찾는 차례


@dataclass(frozen=True)
class Row:
    """`round_cell` 은 회차를 찾은 칸의 이름이고, 회차를 모르면 None 이다. `last` 는 승인 칸의 가장
    늦은 날짜이고, `human` 은 어디로 칸이 `사람 몫:`으로 시작하는 행이다."""

    number: int
    rounds: int | None
    round_cell: str | None
    targets: tuple[str, ...]
    citations: tuple[str, ...]
    last: date | None = None
    human: bool = False


class HitState(Enum):
    """맞은 행의 상태. `BROKEN` 이면 칸이 넷이 아니라 나머지 칸을 읽지 않았다."""

    OPEN = "열림"
    CLOSED = "닫힘"
    BROKEN = "칸이 넷이 아니다"


@dataclass(frozen=True)
class Hit:
    """`--search` 에 맞은 행. `line` 은 대기열 파일의 줄 번호(1부터)이고, `head` 와 `approval` 은
    길이를 묶은 무엇 칸의 머리와 승인 칸이다."""

    number: int
    line: int
    state: HitState
    rounds: int | None = None
    head: str = ""
    approval: str = ""


def is_path(span: str) -> bool:
    if not span or NOT_PATH.search(span) or span.startswith(("-", "/")):
        return False
    return "/" in span or FILE_NAME.match(span) is not None


def is_file(path: str) -> bool:
    """디렉터리(`/`로 끝난다)도 패턴(`*`)도 아닌 경로."""
    return not path.endswith("/") and "*" not in path


def paths_in(where: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """어디로 칸의 경로를 (대상, 인용)으로 가른다. 괄호 깊이가 0이면 대상이다."""
    targets: list[str] = []
    citations: list[str] = []
    depth = 0
    index = 0
    while index < len(where):
        char = where[index]
        if char == "`":
            end = where.find("`", index + 1)
            if end == -1:
                break
            span = where[index + 1 : end]
            if is_path(span):
                (citations if depth else targets).append(span)
            index = end + 1
            continue
        if char == "(":
            depth += 1
        elif char == ")" and depth:
            depth -= 1
        index += 1
    kept = tuple(dict.fromkeys(targets))
    return kept, tuple(path for path in dict.fromkeys(citations) if path not in kept)


def _rounds(cells: dict[str, str]) -> tuple[int | None, str | None]:
    for name in ROUND_CELLS:
        found = [int(count) for count in ROUND.findall(cells[name])]
        if found:
            return max(found), name
    return None, None


def _is_closed(what: str) -> bool:
    return what.lstrip("*").startswith("~~")


def _last_date(approval: str) -> date | None:
    """승인 날짜와 일지 파일명(`YYYY-MM-DD-NN`)의 날짜 가운데 가장 늦은 것. 없는 날짜는 넘는다."""
    found: list[date] = []
    for text in DATE.findall(approval):
        try:
            found.append(date.fromisoformat(text))
        except ValueError:
            continue
    return max(found, default=None)


def _named(line: str) -> dict[str, str] | None:
    """행의 무엇·어디로·승인 칸. 칸이 넷이 아니면 None 이다."""
    parts = [part.strip() for part in CELL_SPLIT.split(line.strip())]
    cells = parts[1:-1] if parts[0] == "" and parts[-1] == "" else parts
    if len(cells) != 4:
        return None
    return dict(zip(CELL_NAMES, cells[1:], strict=True))


def read_rows(text: str) -> tuple[list[Row], list[int]]:
    """(열린 행, 칸이 넷이 아닌 행의 번호)."""
    rows: list[Row] = []
    broken: list[int] = []
    for line in text.splitlines():
        match = ROW.match(line)
        if not match:
            continue
        number = int(match.group(1))
        named = _named(line)
        if named is None:
            broken.append(number)
            continue
        if _is_closed(named["무엇"]):
            continue
        rounds, round_cell = _rounds(named)
        targets, citations = paths_in(named["어디로"])
        last = _last_date(named["승인"])
        human = named["어디로"].lstrip("*").startswith(HUMAN_MARK)
        rows.append(Row(number, rounds, round_cell, targets, citations, last, human))
    return rows, broken


def _head(what: str) -> str:
    """무엇 칸의 머리. 앞의 굵게·취소선 표지를 걷고 처음 닫는 표지(`**`, `~~`)까지다."""
    text = what.lstrip("*~")
    ends = [end for end in (text.find("**"), text.find("~~")) if end != -1]
    head = text[: min(ends, default=len(text))].strip()
    if len(head) <= HEAD_CHARS:
        return head
    return f"{head[:HEAD_CHARS]} …({len(head) - HEAD_CHARS}자 줄임)"


def _approval(approval: str) -> str:
    """승인 칸. 첫 승인으로 시작해 회차와 닫힘을 덧붙여 가는 칸이라 길면 앞과 끝을 남기고 가운데를
    줄인다."""
    cut = len(approval) - APPROVAL_HEAD - APPROVAL_TAIL
    if cut <= 0:
        return approval
    return f"{approval[:APPROVAL_HEAD]} …(가운데 {cut}자 줄임)… {approval[-APPROVAL_TAIL:]}"


def search(text: str, patterns: list[re.Pattern[str]]) -> list[Hit]:
    """닫힌 행까지, 행 원문에 `patterns` 가운데 하나라도 맞은 행을 대기열의 차례로."""
    hits: list[Hit] = []
    # 줄 번호를 Read 의 줄과 맞추려고 줄바꿈으로만 가른다. splitlines 는 U+2028 에서도 가른다
    for index, line in enumerate(text.split("\n"), start=1):
        match = ROW.match(line)
        if not match or not any(pattern.search(line) for pattern in patterns):
            continue
        number = int(match.group(1))
        named = _named(line)
        if named is None:
            hits.append(Hit(number, index, HitState.BROKEN))
            continue
        rounds, _ = _rounds(named)
        state = HitState.CLOSED if _is_closed(named["무엇"]) else HitState.OPEN
        head, approval = _head(named["무엇"]), _approval(named["승인"])
        hits.append(Hit(number, index, state, rounds=rounds, head=head, approval=approval))
    return hits


def _numbers(rows: list[Row]) -> str:
    return " ".join(str(row.number) for row in rows)


def _grouped(pairs: list[tuple[str, Row]]) -> dict[str, list[Row]]:
    grouped: defaultdict[str, list[Row]] = defaultdict(list)
    for path, row in pairs:
        grouped[path].append(row)
    return dict(sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])))


def by_target(rows: list[Row]) -> dict[str, list[Row]]:
    return _grouped([(target, row) for row in rows for target in row.targets])


def by_citation(rows: list[Row]) -> dict[str, list[Row]]:
    return _grouped([(cited, row) for row in rows for cited in row.citations])


def _row_line(row: Row) -> str:
    rounds = f"{row.rounds}회차({row.round_cell})" if row.rounds is not None else "회차 모름"
    targets = ", ".join(row.targets) or "(대상 경로 없음)"
    cited = f" / 인용: {', '.join(row.citations)}" if row.citations else ""
    return f"  {row.number} {rounds} 대상: {targets}{cited}"


def _groups(groups: dict[str, list[Row]]) -> list[str]:
    return [f"  `{path}`: {_numbers(group)}" for path, group in groups.items()]


def render(rows: list[Row], broken: list[int], today: date | None = None) -> str:
    """`today` 가 없으면 오늘(로컬 날짜)을 기준으로 만료를 판정한다."""
    out = [f"열린 행 {len(rows)}개"]
    counted = [row for row in rows if not row.human]
    ripe = sorted(
        (row for row in counted if row.rounds is not None and row.rounds >= MIN_ROUNDS),
        key=lambda row: (-(row.rounds or MIN_ROUNDS), row.number),
    )
    waiting = [row for row in counted if row not in ripe]
    listed = " ".join(f"{row.number}({row.rounds}회차)" for row in ripe)
    out.append(f"회차 {MIN_ROUNDS} 이상: {listed or '(없음)'}")
    humans = [row for row in rows if row.human]
    if humans:
        out.append(f"{HUMAN}(회차를 chore 계기로 세지 않고 만료하지 않는다): {_numbers(humans)}")
    day = today or datetime.now().astimezone().date()  # 이 기계의 시간대
    cutoff = day - timedelta(days=EXPIRY_DAYS)
    stale = sorted(
        (row for row in waiting if row.last is not None and row.last < cutoff),
        key=lambda row: (row.last or cutoff, row.number),
    )
    expired = " ".join(f"{row.number}({row.last})" for row in stale)
    out.append(f"만료할 행(승인 칸의 가장 늦은 날짜가 {cutoff} 전): {expired or '(없음)'}")
    undated = [row for row in waiting if row.last is None]  # 만료할 수 있는 행만 날짜가 필요하다
    if undated:
        out.append(f"날짜를 찾지 못한 행: {_numbers(undated)}")
    grouped = by_target(rows)
    shared = {
        path: group for path, group in grouped.items() if is_file(path) and len(group) >= MIN_ROWS
    }
    if shared:
        out.append(
            f"같은 대상 파일이 {SHARED}(chore 계기가 아니다. chore 를 고른 뒤 함께 묶을 행이다."
            " 행 원문으로 실제 대상인지 가른다):"
        )
        out.extend(_groups(shared))
    else:
        out.append(f"같은 대상 파일이 {SHARED}: (없음)")
    containers = {path: group for path, group in grouped.items() if not is_file(path)}
    if containers:
        out.append("디렉터리·패턴 대상(조건에 세지 않는다):")
        out.extend(_groups(containers))
    cited = by_citation(rows)
    if cited:
        out.append("괄호 안의 인용으로 센 경로(대상이면 위의 수에 더한다):")
        out.extend(_groups(cited))
    unknown = [row for row in rows if row.rounds is None]
    if unknown:
        out.append(f"회차를 찾지 못한 행: {_numbers(unknown)}")
    if broken:
        out.append(
            f"칸이 넷이 아닌 행: {' '.join(map(str, broken))} (세지 않았다. 표를 고치고 다시 센다)"
        )
    return "\n".join(out)


def render_rows(rows: list[Row]) -> str:
    """`--rows` 가 기본 출력 뒤에 붙이는 행마다·대상마다의 줄."""
    out = ["행마다:", *(_row_line(row) for row in rows), "대상마다:", *_groups(by_target(rows))]
    return "\n".join(out)


def _hit_line(hit: Hit) -> str:
    if hit.state is HitState.BROKEN:
        return f"  {hit.number} 줄 {hit.line} 칸이 넷이 아니다(칸을 읽지 않았다. 그 줄을 열어 본다)"
    rounds = f"{hit.rounds}회차" if hit.rounds is not None else "회차 모름"
    return (
        f"  {hit.number} 줄 {hit.line} {hit.state.value} {rounds}"
        f" 머리: {hit.head} / 승인: {hit.approval}"
    )


def render_hits(hits: list[Hit]) -> str:
    """`--search` 의 출력. 맞은 행마다 한 줄이다."""
    if not hits:
        return "맞은 행 없음"
    counts = [
        f"열린 행 {_count(hits, HitState.OPEN)}개",
        f"닫힌 행 {_count(hits, HitState.CLOSED)}개",
    ]
    broken = _count(hits, HitState.BROKEN)
    if broken:
        counts.append(f"칸이 넷이 아닌 행 {broken}개")
    head = (
        f"맞은 행 {len(hits)}개({', '.join(counts)})."
        " 같은 일로 보이는 행은 그 줄을 Read 로 연다(offset 에 줄, limit 에 1):"
    )
    return "\n".join([head, *(_hit_line(hit) for hit in hits)])


def _count(hits: list[Hit], state: HitState) -> int:
    return sum(hit.state is state for hit in hits)


def read_ref(ref: str) -> str:
    """`git show <ref>:<QUEUE>`. git 이 실패하거나 시간을 넘기면 OSError 로 올린다."""
    try:
        done = subprocess.run(
            ["git", "show", f"{ref}:{QUEUE.as_posix()}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIMEOUT,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise OSError(f"git show 가 {GIT_TIMEOUT}초 안에 끝나지 않았다") from error
    if done.returncode != 0:
        raise OSError(done.stderr.strip() or f"git show 가 {done.returncode}로 끝났다")
    return done.stdout


def main(argv: list[str]) -> int:
    path: Path | None = None
    ref: str | None = None
    today: date | None = None
    each = False
    patterns: list[re.Pattern[str]] = []
    args = list(argv)
    while args:
        arg = args.pop(0)
        if arg == "--rows":
            each = True
        elif arg == "--search" and args:
            source = args.pop(0)
            try:
                patterns.append(re.compile(source))
            except re.error as error:
                sys.stderr.write(f"정규식이 틀렸다: {source}: {error}\n{USAGE}")
                return 2
        elif arg == "--today" and args and today is None:
            try:
                today = date.fromisoformat(args.pop(0))
            except ValueError:
                sys.stderr.write(USAGE)
                return 2
        elif arg == "--queue" and args and ref is None:
            path = Path(args.pop(0))
        elif arg == "--ref" and args and path is None and not args[0].startswith("-"):
            # `-` 로 시작하면 git 이 옵션으로 읽는다(`--output=<경로>` 는 파일을 쓴다)
            ref = args.pop(0)
        else:
            sys.stderr.write(USAGE)
            return 2
    if patterns and (each or today is not None):
        sys.stderr.write(USAGE)  # 검색은 기본 출력을 내지 않아 그 옵션이 쓰일 자리가 없다
        return 2
    try:
        text = read_ref(ref) if ref is not None else (path or QUEUE).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        # 해독 실패를 놓치면 트레이스백의 종료 1이 "칸이 넷이 아닌 행" 과 섞인다
        sys.stderr.write(f"대기열을 읽지 못했다: {error}\n")
        return 2
    if patterns:
        hits = search(text, patterns)
        print(render_hits(hits))
        return 1 if any(hit.state is HitState.BROKEN for hit in hits) else 0
    rows, broken = read_rows(text)
    print(render(rows, broken, today))
    if each:
        print(render_rows(rows))
    return 1 if broken else 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
    raise SystemExit(main(sys.argv[1:]))
