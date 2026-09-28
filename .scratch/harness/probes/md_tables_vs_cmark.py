"""tools/check_md_tables.py 와 cmark-gfm 의 차분 대조. 같은 문서를 둘에 넣고 표의 모양을 비교한다.

돌리는 법(저장소 루트에서):
    PYTHONUTF8=1 uv run --with cmarkgfm python .scratch/harness/probes/md_tables_vs_cmark.py
    ... --fuzz 60000 --seed 7     무작위 문서 수와 씨앗(기본 20000, 1). --show 는 찍을 어긋남 수

cmarkgfm 은 프로젝트 의존성이 아니다. `--with` 가 uv 의 일회용 환경에만 넣는다. GitHub 은
cmark-gfm 으로 렌더하고 각주를 켠다 — 적대 검증의 반박자들이 `gh api markdown -f mode=gfm` 과
cmarkgfm 0.29.0.gfm.13 의 출력이 같음을 확인했다. 그래서 여기서도 각주를 켠다.

대조하는 것 셋.
1. 표마다 끝 줄과 본문 행의 줄 번호. cmark 는 `data-sourcepos` 로 준다. 머리 행 앞에 문단이
   있으면 cmark 는 그 문단을 0:0 으로, 표를 문단의 첫 줄부터로 내므로 표 시작 줄은 쓰지 않는다.
   끝 줄과 본문 행이 같으면 구분 행도 같다. 참조되지 않은 각주 정의는 cmark 가 렌더하지 않으므로
   앞에 참조 문단을 붙여 살린다.
2. 한 줄의 칸 수(`row_cells`). cmark 는 칸을 채우거나 버려 렌더하므로 칸 수를 직접 주지 않는다.
   그 줄을 머리 행으로, 칸 k 개짜리 구분 행을 붙여 표가 되는 k 를 찾는다.
3. 대상은 저장소의 추적 마크다운 전부와 무작위 문서다. 무작위 문서는 조각 하나~셋을 잇고, 조각의
   3/4 은 표 덩어리다 — 컨테이너(인용·목록·각주) 안에 머리 행·구분 행·본문 행을 두고, 이어지는
   줄을 가끔 게으른 줄이나 더 들여쓴 줄로 흔들고, 끊는 블록을 섞는다. 나머지 조각은 블록 줄을
   무작위로 잇는다. 개행은 LF·CRLF·CR 이고 가끔 BOM 을 붙인다. 어긋나면 줄을 하나씩 빼 가며 줄인
   문서를 찍는다.

대조하지 않는 것: 검사의 알림 자체(표가 끊긴 줄, 표가 못 된 머리 행). cmark 는 그것을 따로 내지
않는다. 그 규칙은 테스트가 고정한다.

2026-09-29 기록: 씨앗 7·8·9 에서 각 6만 문서(표가 생긴 문서 약 2만 9천, 본문 행 약 4만 1천씩)와
칸 수 1만 5천 줄씩, 어긋남 0. 거기까지 오며 찾은 다섯 — cmark 의 버릇 셋(게으른 줄의 앞 공백이
머리 행의 빈 칸이 된다, 표 시도가 실패한 문단은 다시 표를 열지 않는다, 목록 표식 뒤의 수직 탭·폼
피드는 여백이 아니다)과 GitHub 이 켠 기능 둘(각주 정의, 참조 정의만의 문단 아래 밑줄) — 은 검사
코드의 주석에 있다.

종료 코드: 어긋남 0 이면 0, 아니면 1.

비 ASCII 문자는 chr() 로 만든다. 이 파일을 쓰던 편집 도구가 역슬래시-u 이스케이프를 날것으로
저장했다(대기열 22 와 같은 사고).
"""

from __future__ import annotations

import argparse
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import cmarkgfm  # noqa: E402
from cmarkgfm.cmark import Options  # noqa: E402
from tools.check_md_tables import parse, row_cells, tracked_markdown  # noqa: E402

BOM = chr(0xFEFF)
WIDE = chr(0x3000)
NBSP = chr(0x00A0)

_TABLE = re.compile(r'<table data-sourcepos="\d+:\d+-(\d+):\d+">(.*?)</table>', re.S)
_BODY = re.compile(r"<tbody>(.*?)</tbody>", re.S)
_ROW = re.compile(r'<tr data-sourcepos="(\d+):')
_FOOTNOTE_LABEL = re.compile(r"\[\^([^\] \r\n\x00\t]+)\]:")

# GitHub 처럼 각주를 켠다.
OPTIONS = Options.CMARK_OPT_SOURCEPOS | Options.CMARK_OPT_FOOTNOTES

Shape = list[tuple[int, list[int]]]


def cmark_shape(text: str) -> Shape:
    """cmark 가 만드는 표. 참조되지 않은 각주 정의를 살리려고 앞에 참조 문단 두 줄을 붙인다.

    붙인 두 줄만큼 줄 번호를 되돌린다. 각주 안의 표는 HTML 끝에 오므로 정렬해 비교한다.
    """
    labels = sorted(set(_FOOTNOTE_LABEL.findall(text)))
    shift = 0
    if labels:
        bom = BOM if text.startswith(BOM) else ""
        references = "".join(f"[^{label}]" for label in labels)
        text = bom + "x" + references + "\n\n" + text.removeprefix(bom)
        shift = 2
    html = cmarkgfm.github_flavored_markdown_to_html(text, options=OPTIONS)
    shape: Shape = []
    for table in _TABLE.finditer(html):
        body = _BODY.search(table.group(2))
        rows = [int(line) - shift for line in _ROW.findall(body.group(1))] if body else []
        shape.append((int(table.group(1)) - shift, rows))
    return sorted(shape)


def model_shape(text: str) -> Shape:
    tables, _ = parse(text)
    shape: Shape = []
    for table in tables:
        rows = [row.line for row in table.rows]
        shape.append((rows[-1] if rows else table.delimiter_line, rows))
    return sorted(shape)


def cmark_cells(content: str) -> int:
    for count in range(1, 16):
        delimiter = "|" + "|".join(["-"] * count) + "|"
        if "<table>" in cmarkgfm.github_flavored_markdown_to_html(f"{content}\n{delimiter}\n"):
            return count
    return 0


_CELL_ALPHABET = ["|", "|", "\\", "`", " ", "a", "\t", "\v", ":", "-", WIDE, NBSP, "x"]
_CELLS = ["a", "b", "`x|y`", "x\\|y", "x\\\\|y", "", " ", "<b>q</b>"]


def random_content(rng: random.Random) -> str:
    head = rng.choice(["|", "x", "y", "\\", ":", "`a"])
    return head + "".join(rng.choice(_CELL_ALPHABET) for _ in range(rng.randint(0, 10)))


def random_row(rng: random.Random, cells: int) -> str:
    row = " | ".join(rng.choice(_CELLS) for _ in range(cells))
    lead = rng.choice(["| ", "|", ""])
    tail = rng.choice([" |", "|", "", " | "])
    return lead + row + tail


def random_delimiter(rng: random.Random, cells: int) -> str:
    markers = [rng.choice(["---", ":--", "--:", ":-:", "-", " --- "]) for _ in range(cells)]
    row = rng.choice(["|", " | "]).join(markers)
    lead = rng.choice(["| ", "|", ""])
    tail = rng.choice([" |", "|", ""])
    line = lead + row + tail
    if rng.random() < 0.05:
        line = line.replace(" ", rng.choice([WIDE, NBSP, "\v"]), 1)
    return line


_BLOCK_LINES = [
    "text", "a | b", "`x|y`", "<b>x</b> | 2", "< 3 | 2", "- item", "* item", "+ item", "1. item",
    "2) item", "10. item", "1) item", "-", "> quote", ">", "# head", "## h | x", "#", "#no",
    "####### x", "---", "***", "===", "- - -", "* * *", "_ _ _", "```", "~~~", "```js", "````",
    "```` x", "~~~ `x`", "``` `x`", "<!--", "-->", "<!-- c -->", "<div>", "</div>",
    '<div class="x">', "<a href='x'>", "</a>", "<b>", "<p/>", "<p>", "<pre>", "</pre>",
    "<script>", "</script>", "<textarea>", "</textarea>", "<!DOCTYPE html>", "<!doctype html>",
    "<![CDATA[", "]]>", "<?x", "?>", "|", "||", "| |", "", "", "", WIDE, "text\f", "\f| a |",
    "[^1]: note", "[^n]: x | y", "[a]: /url",
]  # fmt: skip
_PREFIXES = [
    "", "", "", "", "> ", ">", "- ", "1. ", "  ", "> > ", "- > ", "    - ", "1.  ", "-    ",
    "-      ", "  - ", "   ", "* ", "10) ",
]  # fmt: skip
_INDENTS = ["", "", "", " ", "  ", "   ", "    ", "      ", "\t", "  \t"]


def random_line(rng: random.Random) -> str:
    roll = rng.random()
    cells = rng.randint(1, 3)
    if roll < 0.35:
        body = random_row(rng, cells)
    elif roll < 0.55:
        body = random_delimiter(rng, cells)
    else:
        body = rng.choice(_BLOCK_LINES)
    return rng.choice(_PREFIXES) + rng.choice(_INDENTS) + body


# 표 덩어리의 컨테이너. (첫 줄 머리, 이어지는 줄 머리). 이어지는 줄은 가끔 흔들어 게으른 줄·
# 들여쓴 줄을 만든다.
_CONTAINERS = [
    ("", ""), ("", ""), ("> ", "> "), (">", ">"), ("- ", "  "), ("1. ", "   "), ("10) ", "    "),
    ("> - ", ">   "), ("- > ", "  > "), ("    - ", "      "), ("[^n]: ", "    "), ("  ", "  "),
    ("-    ", "     "), ("* ", "  "),
]  # fmt: skip
_INTERRUPTS = [
    "- item", "1. item", "2. item", "# head", "> q", "```", "<div>", "<b>", "<!-- c -->", "|",
    WIDE, "    code", "---", "***", "text", "[^1]: note", "[a]: /url",
]  # fmt: skip


def random_table_block(rng: random.Random) -> list[str]:
    head, tail = rng.choice(_CONTAINERS)
    cells = rng.randint(1, 4)
    header = random_row(rng, cells) if rng.random() < 0.9 else rng.choice(["text", "a", "x | y"])
    delimiter_cells = cells if rng.random() < 0.8 else rng.randint(1, 4)
    body = [header, random_delimiter(rng, delimiter_cells)]
    for _ in range(rng.randint(0, 4)):
        roll = rng.random()
        if roll < 0.7:
            body.append(random_row(rng, max(1, cells + rng.choice([0, 0, 0, 1, -1]))))
        elif roll < 0.8:
            body.append(random_delimiter(rng, cells))
        else:
            body.append(rng.choice(_INTERRUPTS))
    before = [random_line(rng) for _ in range(rng.choice([0, 0, 1, 2]))]
    if before and rng.random() < 0.5:
        before.append("")
    lines = [*before]
    for index, text in enumerate(body):
        prefix = head if index == 0 else tail
        roll = rng.random()
        if index > 0 and roll < 0.08:
            prefix = ""
        elif index > 0 and roll < 0.14:
            prefix = prefix + rng.choice([" ", "  ", "    ", "\t"])
        lines.append(prefix + text)
    after = [random_line(rng) for _ in range(rng.choice([0, 0, 1, 2]))]
    if after and rng.random() < 0.5:
        after.insert(0, "")
    return lines + after


def random_document(rng: random.Random) -> str:
    newline = rng.choice(["\n", "\n", "\n", "\r\n", "\r"])
    bom = BOM if rng.random() < 0.05 else ""
    lines: list[str] = []
    for _ in range(rng.randint(1, 3)):
        if rng.random() < 0.75:
            lines.extend(random_table_block(rng))
        else:
            lines.extend(random_line(rng) for _ in range(rng.randint(1, 6)))
        if rng.random() < 0.6:
            lines.append("")
    # 각주 이름을 문서 안에서 겹치지 않게 한다. 같은 이름의 둘째 정의는 cmark 가 렌더하지 않는다
    # (검사는 그 안의 표도 본다 — 검사 독스트링의 못 보는 것).
    counter = iter(range(1, 1000))
    text = newline.join(lines)
    text = re.sub(r"\[\^[^\]]+\]:", lambda _: f"[^f{next(counter)}]:", text)
    return bom + text + newline


def shrink(text: str) -> str:
    newline = "\r\n" if "\r\n" in text else "\r" if "\r" in text else "\n"
    lines = text.split(newline)
    changed = True
    while changed:
        changed = False
        for index in range(len(lines)):
            candidate = newline.join(lines[:index] + lines[index + 1 :])
            if cmark_shape(candidate) != model_shape(candidate):
                lines = lines[:index] + lines[index + 1 :]
                changed = True
                break
    return newline.join(lines)


def main() -> int:
    arguments = argparse.ArgumentParser()
    arguments.add_argument("--fuzz", type=int, default=20000)
    arguments.add_argument("--seed", type=int, default=1)
    arguments.add_argument("--show", type=int, default=15)
    options = arguments.parse_args()
    rng = random.Random(options.seed)

    file_misses: list[str] = []
    files = tracked_markdown(ROOT)
    for path in files:
        text = path.read_text(encoding="utf-8")
        if cmark_shape(text) != model_shape(text):
            file_misses.append(path.relative_to(ROOT).as_posix())
    print(f"저장소 마크다운 {len(files)}개, 표 모양 어긋남 {len(file_misses)}개")
    for name in file_misses:
        print("  ", name)

    cell_misses: dict[str, tuple[int, int]] = {}
    for _ in range(options.fuzz // 4):
        content = random_content(rng)
        expected, actual = cmark_cells(content), row_cells(content.expandtabs(4))
        if expected != actual:
            cell_misses[content] = (expected, actual)
    print(f"칸 수 {options.fuzz // 4}줄, 어긋남 {len(cell_misses)}줄")
    for content, (expected, actual) in list(cell_misses.items())[: options.show]:
        print(f"   {content!r}: cmark {expected}, 검사 {actual}")

    shape_misses: dict[str, tuple[Shape, Shape]] = {}
    with_table = rows = 0
    for _ in range(options.fuzz):
        text = random_document(rng)
        expected = cmark_shape(text)
        with_table += bool(expected)
        rows += sum(len(body) for _, body in expected)
        if expected != model_shape(text):
            small = shrink(text)
            shape_misses.setdefault(small, (cmark_shape(small), model_shape(small)))
    print(
        f"무작위 문서 {options.fuzz}개(표가 생긴 문서 {with_table}개, 본문 행 {rows}개), "
        f"표 모양 어긋남 {len(shape_misses)}가지(줄인 문서 기준)"
    )
    ordered = sorted(shape_misses.items(), key=lambda item: len(item[0]))
    for text, (expected, actual) in ordered[: options.show]:
        print(f"   {text!r}\n      cmark {expected}\n      검사  {actual}")
    return 1 if file_misses or cell_misses or shape_misses else 0


if __name__ == "__main__":
    raise SystemExit(main())
