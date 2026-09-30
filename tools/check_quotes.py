"""바뀐 마크다운의 긴 따옴표 인용을 저장소와 대조한다. 경고만 하고 막지 않는다(대기열 42).

같은 PR 안에서 문장을 고치고 그 문장의 인용 둘을 옛 문구대로 둔 것을 리뷰가 잡았다(2026-09-28
하네스 감사, 대기열 20 의 가족). 20자 이상의 큰따옴표 인용을 뽑아 저장소의 텍스트 파일 전체(TS·JS
포함, 대기열 66)에서 글자 그대로 세고, 인용 자신뿐이면(두 번째 자리가 없으면) 경고한다. `ADR NNNN`
가까이의 인용은 그 ADR 파일 전문(제목만이 아니라)에서 찾고, 없으면 저장소로 돌아가 본다. 거짓
양성(번역·요약 인용, 저장소 밖 원문)이 있어 막지 않고 경고만 낸다. `>` 인용문 줄과 코드 스팬·펜스
안은 보지 않는다. `한 줄 후보: "…"`·`한 구절: "…"`·`문구 후보: "…"` 처럼 제안 표지 바로 뒤의
따옴표도 보지 않는다 — 대기열과 일지의 제안은 아직 어디에도 없는 문장이다(대기열 51). `옛 문구:`·
`로그의 한 줄:` 처럼 있는 글을 가리키는 표지 뒤는 본다. 따옴표의 짝은 줄이 아니라 문단·목록 항목
안에서 짓는다 — 줄마다 지으면 줄을 넘는 인용의 닫는 따옴표가 같은 줄의 다음 인용과 짝지어져 사이의
산문을 인용으로 잡았다(대기열 67).
pre-commit 이 바뀐 .md 를 넘기고 `verbose: true` 로 출력을 보인다. 기본은 작업 트리가 HEAD 에 더한
줄만 본다 — 파일 전체를 보면 옛 인용(대기열의 한 줄 후보, 런북의 프롬프트 예시)이 대기열 파일
하나에서만 서른 건 남짓 울려 경고를 무시하게 된다(2026-09-28 실측). `--all-lines` 로 전체를 본다.
인자가 없으면 추적되는 .md 전부가 대상이고, `.claude/skills/` 의 사본은 어느 모드에서든 뺀다 —
남이 쓴 영문 인용이 원문 없이 많다. 경고가 없어도 본 인용 수를 찍는다 — 무출력 초록은 "다
맞았다"와 "아무것도 안 봤다"를 가르지 못했다(대기열 55).
못 보는 것: 20자 미만의 인용, 홑따옴표·꺾쇠 인용, 줄바꿈을 넘는 인용(같은 묶음 안이면 짝만
맞추고 대조하지 않는다), 제안 표지 뒤에 적은 실제 원문의 인용(`스킬에 한 줄: "…"` 이 이미 있는 줄일
때), 짝 없는 따옴표(인치 표시 등) 뒤의 같은 묶음 — 짝이 뒤집혀 진짜 인용을 놓치거나 사이의 산문을
잡는다, 묶음 경계가 CommonMark 와 어긋나는 자리 — 문단 중간에서 `42. `·`| ` 로 시작하는 줄은 새
묶음을 열고 줄을 넘는 코드 스팬과 HTML 블록은 모르므로, 그 자리를 넘는 인용은 짝이 뒤집힌다,
기본 모드에서 바뀐 파일의 바뀌지 않은 줄에 있는 인용,
같은 틀린 인용이 두 곳에 있는 것(둘이 서로를 세어 준다), 원문이 저장소 밖인 인용(경고가 거짓
양성이다), 마크다운 밖의 인용, 원문이 바뀐 뒤 인용만 옛 문구인 것 중 옛 문구가 다른 기록(일지)에
남아 있는 것.
"""

from __future__ import annotations

import io
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT_SUFFIXES = frozenset(
    {".md", ".py", ".toml", ".json", ".yaml", ".yml", ".txt", ".ps1", ".sh"}
    | {".ts", ".tsx", ".mjs", ".js"}
)
SKIPPED_PREFIXES = (".claude/skills/",)
MIN_LENGTH = 20
ADR_MIN_LENGTH = 6  # ADR 가까이의 인용은 짧은 이력 제목도 대조한다
# 닫는 펜스는 여는 것과 같은 글자로 같거나 더 길다(CommonMark). ```` 로 ``` 를 닫을 수 있다.
_FENCE = re.compile(
    r"^[ \t]*(?:[-*+]\s+)?(?P<fence>`{3,}|~{3,})(?![`~]).*?^[ \t]*(?P=fence)[`~]*[ \t]*$",
    re.M | re.S,
)
_OPEN_FENCE = re.compile(
    r"^[ \t]*(?:[-*+]\s+)?(?:`{3,}|~{3,}).*\Z", re.M | re.S
)  # 닫히지 않은 펜스
_CODE_SPAN = re.compile(r"`[^`\n]+`")
_MARKER = r"(?:[-*+]|\d+[.)])"  # 목록 표지. CommonMark 는 번호 뒤에 `.` 과 `)` 를 둘 다 받는다
_LIST_MARKER = re.compile(rf"^[ \t]*{_MARKER}\s+")
# 짝을 짓는 묶음을 새로 여는 줄 — 목록 표지, 제목, 표 행, 인용문. 빈 줄도 연다.
_BLOCK_START = re.compile(rf"^[ \t]*(?:{_MARKER}\s|#{{1,6}}\s|\||>)")
# 그 줄에서 묶음이 끝나는 줄 — ATX 제목과 표 행은 한 줄이고, setext 밑줄과 가로줄은 문단을 닫는다.
_BLOCK_END = re.compile(r"^[ \t]*(?:#{1,6}\s|\||(?:=+|-+|\*{3,}|_{3,})[ \t]*$)")
# 한 묶음 안에서 짝짓는다. 본문이 줄바꿈을 품으면 줄을 넘는 인용이다.
_QUOTE = re.compile(r"[\"“]([^\"”]*)[\"”]")
# `ADR 0012("길은 셋이고 …")`, `ADR 0009의 2026-09-22 이력 "…"`. 인용은 그 ADR 파일에 있어야 한다.
# 여는 따옴표 앞 같은 줄에서 찾는다. 창은 25자이고 다른 `ADR` 을 넘지 않는다 — 넓으면 무관한 인용을
# 그 ADR 것으로 돌린다.
_ADR_BEFORE = re.compile(r"ADR\s*(\d{4})(?:(?!ADR)[^\"“\n]){0,25}\Z")
# 여는 따옴표 바로 앞의 제안 표지. `한 줄:`, `한 구절 후보:`, `한 구절 더:`, `한 줄의 문구:`,
# `문구 후보:`. `옛 문구:`·`로그의 한 줄:` 은 있는 글을 가리키는 표지라 뺀다 — 그 뒤의 인용이
# 바로 이 검사의 대상이다(셀프 리뷰 표준 축).
_PROPOSAL = re.compile(
    r"(?:(?<!의\s)한\s*(?:줄|구절)(?:의\s*문구)?|문구\s*후보)(?:\s*(?:후보|더))?\s*[:：]\s*\Z"
)
_ELLIPSIS = re.compile(r"…|\.\.\.")
_EXCLUDED_DIRS = frozenset({".git", ".venv", "node_modules", "worktrees", "__pycache__"})


@dataclass(frozen=True)
class Quote:
    line: int
    text: str
    adr: str | None  # 가까이 적힌 ADR 번호. 있으면 그 파일에서 찾는다


def normalize(text: str) -> str:
    """대조 전에 양쪽에서 벗기는 것 — 백틱과 강조 별표.

    인용은 원문의 코드 스팬·강조를 지우거나 더한다.
    """
    return text.replace("`", "").replace("*", "")


def _blank_code(markdown: str) -> str:
    """펜스는 줄 수만 남기고 비운다. 코드 스팬 안의 따옴표는 지운다."""
    text = _FENCE.sub(lambda m: "\n" * m.group(0).count("\n"), markdown)
    text = _OPEN_FENCE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    return _CODE_SPAN.sub(lambda m: re.sub(r"[\"“”']", "", m.group(0)), text)


def _blocks(markdown: str) -> list[list[tuple[int, str]]]:
    """따옴표의 짝을 짓는 묶음 — 문단과 목록 항목. 줄은 (원문 줄 번호, 벗긴 산문)이다.

    `>` 인용문은 뺀다. `>` 없이 이어진 게으른 줄도 CommonMark 에서는 그 인용문의 문단이라 함께
    뺀다. 묶음을 문단보다 좁게(목록 항목, 제목, 표 행마다) 잡는 것은 짝 없는 따옴표 하나가 뒤집는
    범위를 그 묶음으로 줄이려는 것이다.
    """
    blocks: list[list[tuple[int, str]]] = []
    current: list[tuple[int, str]] = []
    in_quote = False
    for number, line in enumerate(_blank_code(markdown).splitlines(), 1):
        blank = not line.strip()
        if blank or _BLOCK_START.match(line):
            if current:
                blocks.append(current)
            current = []
            in_quote = not blank and _LIST_MARKER.sub("", line).lstrip().startswith(">")
        if blank or in_quote:
            continue
        current.append((number, normalize(line)))
        if _BLOCK_END.match(line):
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def _clean(text: str) -> str | None:
    """인용 본문. 앞뒤 생략 부호를 떼고, 따옴표 쌍이 어긋나 잡힌 조각(닫는 표 뒤부터)은 버린다."""
    text = text.strip().strip("….").strip()
    if not text or text[0] in ")]},.;:" or text[-1] in "([{":
        return None
    return text


def _as_quote(number: int, raw: str, before: str) -> Quote | None:
    """따옴표 한 쌍을 대조할 인용으로 정한다. `before` 는 여는 따옴표 앞의 같은 줄이다.

    제안 표지 뒤이거나 짝이 어긋난 조각이거나 짧으면 None. ADR 가까이면 그 ADR 에서 찾는다.
    """
    body = _clean(raw)
    if body is None or _PROPOSAL.search(before):
        return None
    adr = _ADR_BEFORE.search(before)
    if adr is not None and len(body) >= ADR_MIN_LENGTH:
        return Quote(number, body, adr.group(1))
    return Quote(number, body, None) if len(body) >= MIN_LENGTH else None


def quotes_in(markdown: str) -> list[Quote]:
    """산문의 큰따옴표 인용. 펜스·코드 스팬·`>` 줄과 제안 표지 뒤는 뺀다.

    줄 번호는 원문 기준이다.
    """
    quotes: list[Quote] = []
    for block in _blocks(markdown):
        text = "\n".join(line for _, line in block)
        for match in _QUOTE.finditer(text):
            if "\n" in match.group(1):
                continue  # 줄을 넘는 인용. 짝만 소비하고 대조하지 않는다
            start = match.start()
            number = block[text.count("\n", 0, start)][0]
            before = text[text.rfind("\n", 0, start) + 1 : start]
            quote = _as_quote(number, match.group(1), before)
            if quote is not None:
                quotes.append(quote)
    return quotes


def tracked_text_files(root: Path = ROOT) -> list[Path]:
    """git 이 추적하는 텍스트 파일. 저장소가 아니면(테스트) 트리를 걷는다."""
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"], capture_output=True, check=False
    )
    if result.returncode == 0:
        names = result.stdout.decode("utf-8", "replace").split("\0")
        return [
            (root / name).resolve() for name in names if name and Path(name).suffix in TEXT_SUFFIXES
        ]
    return [
        path
        for path in root.rglob("*")
        if path.suffix in TEXT_SUFFIXES and not _EXCLUDED_DIRS.intersection(path.parts)
    ]


def load_corpus(root: Path = ROOT) -> dict[Path, str]:
    corpus: dict[Path, str] = {}
    for path in tracked_text_files(root):
        try:
            corpus[path] = normalize(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
    return corpus


def adr_text(number: str, root: Path = ROOT) -> str | None:
    matches = sorted((root / "docs" / "adr").glob(f"{number}-*.md"))
    return normalize(matches[0].read_text(encoding="utf-8")) if matches else None


_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", re.M)


def added_lines_from_diff(diff: str) -> set[int]:
    """unified diff(-U0) 의 헝크 머리에서 새 파일 쪽 줄 번호들."""
    lines: set[int] = set()
    for match in _HUNK.finditer(diff):
        start = int(match.group(1))
        count = int(match.group(2)) if match.group(2) is not None else 1
        lines.update(range(start, start + count))
    return lines


def added_lines(path: Path, root: Path = ROOT) -> set[int] | None:
    """작업 트리가 HEAD 에 더한 줄들. git 이 없거나 diff 가 비면 None(전체를 본다).

    스테이지 여부와 상관없이 작업 트리를 본다. 검사가 읽는 것이 작업 트리라 줄 번호도 거기
    맞는다. pre-commit 은 스테이지하지 않은 변경을 치워 두고 돌므로 커밋 때는 스테이지된 줄과
    같다. 스테이지된 줄(`diff --cached`)만 보던 때는 부분 스테이지된 파일의 나머지 편집을 손으로
    넘겨도 조용히 건너뛰었다(대기열 55). diff 가 빈 것은 추적하지 않는 새 파일이나 바뀌지 않은
    파일을 넘긴 경우다. 그때 아무것도 보지 않으면 검사가 조용히 빈 것이 되므로 전체를 본다. HEAD 가
    없어도 전체다.
    """
    result = subprocess.run(
        ["git", "-C", str(root), "diff", "HEAD", "-U0", "--no-color", "--", str(path)],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return added_lines_from_diff(result.stdout.decode("utf-8", "replace"))


LineFilter = Callable[[Path], "set[int] | None"]


@dataclass(frozen=True)
class Report:
    """무엇을 봤는지까지 센다 — 무출력 초록은 "다 맞았다"와 "안 봤다"를 가르지 못했다(대기열 55)."""

    warnings: list[str]
    files_read: int  # 넘긴 파일 중 실제로 읽은 것. 뺀 사본과 없는 파일은 세지 않는다
    files_whole: int  # 그중 줄 필터 없이 전체를 본 것(diff 가 비었거나 `--all-lines`)
    quotes_checked: int  # 줄 필터를 지나 대조한 인용 수


def check(files: list[Path], root: Path = ROOT, line_filter: LineFilter | None = None) -> Report:
    """파일들의 인용 중 원문을 찾지 못한 것(파일:줄: 인용 — 이유)과 본 범위.

    `line_filter` 가 파일마다 볼 줄 번호들을 주면 그 줄의 인용만 본다(pre-commit 은
    `added_lines`). 옛 줄의 인용은 그 줄이 들어올 때 봤거나 이 검사 전의 것이라, 커밋마다
    다시 경고하면 경고를 무시하는 습관만 만든다. 필터가 None 을 주면 그 파일은 전체를 본다.
    """
    corpus = load_corpus(root)
    warnings: list[str] = []
    files_read = files_whole = quotes_checked = 0
    for path in files:
        relative = _relative(path, root)
        if relative.startswith(SKIPPED_PREFIXES):
            continue
        try:
            markdown = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        # 추적되지 않은 새 파일도 자기 자리를 센다. 키는 resolve 한 것 — 상대 경로로 넘어온 추적
        # 파일이 다른 키로 한 번 더 들어가면 모든 인용이 두 번 세어져 검사가 조용히 빈다.
        corpus.setdefault(path.resolve(), normalize(markdown))
        allowed = line_filter(path) if line_filter is not None else None
        files_read += 1
        if allowed is None:
            files_whole += 1
        for quote in quotes_in(markdown):
            if allowed is not None and quote.line not in allowed:
                continue
            quotes_checked += 1
            shown = quote.text if len(quote.text) <= 60 else quote.text[:57] + "…"
            where = f'{relative}:{quote.line}: "{shown}"'
            if quote.adr is not None:
                text = adr_text(quote.adr, root)
                if text is not None and _contains(text, quote.text):
                    continue
                if _found_elsewhere(quote.text, corpus):
                    continue  # 그 ADR 것이 아니라 가까이 적혔을 뿐인 인용
                if text is None:
                    warnings.append(f"{where} — ADR {quote.adr} 파일이 없다")
                else:
                    warnings.append(f"{where} — ADR {quote.adr} 에 이 문구가 글자 그대로 없다")
                continue
            if not _found_elsewhere(quote.text, corpus):
                warnings.append(
                    f"{where} — 저장소의 다른 자리에 글자 그대로 없다. 원문을 다시 열어 그대로 "
                    "옮기거나 따옴표를 뗀다(대기열 42). 아직 없는 제안 문장이면 `한 줄 후보:` "
                    "같은 표지 바로 뒤에 둔다(대기열 51)"
                )
    return Report(warnings, files_read, files_whole, quotes_checked)


def _pieces(quote: str) -> list[str]:
    """가운데가 생략(`…`)된 인용의 조각들. 생략이 없으면 하나."""
    return [piece.strip() for piece in _ELLIPSIS.split(quote) if piece.strip()]


def _contains(text: str, quote: str) -> bool:
    return all(piece in text for piece in _pieces(quote))


def _found_elsewhere(quote: str, corpus: dict[Path, str]) -> bool:
    """인용 자신 말고 한 자리 더 있는가. 조각마다 두 번째 자리를 센다(인용 파일에도 조각은 있다)."""
    return all(sum(text.count(piece) for text in corpus.values()) >= 2 for piece in _pieces(quote))


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def default_files(root: Path = ROOT) -> list[Path]:
    return [
        path
        for path in tracked_text_files(root)
        if path.suffix == ".md" and not _relative(path, root).startswith(SKIPPED_PREFIXES)
    ]


def main(argv: list[str]) -> int:
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8")
    all_lines = "--all-lines" in argv
    files = [Path(arg) for arg in argv if arg != "--all-lines"] or default_files()
    report = check(files, line_filter=None if all_lines else added_lines)
    for warning in report.warnings:
        print(warning)
    scope = (
        f"파일 {report.files_read}개(그중 전체를 본 것 {report.files_whole}개)에서 "
        f"인용 {report.quotes_checked}건"
    )
    if report.warnings:
        print(
            f"인용 대조 경고 {len(report.warnings)}건({scope} 중). 막지 않는다 — "
            "원문과 다른 인용인지 하나씩 본다."
        )
    else:
        print(f"인용 대조: {scope}을 봤다. 경고 없음.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
