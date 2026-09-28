"""바뀐 마크다운의 긴 따옴표 인용을 저장소와 대조한다. 경고만 하고 막지 않는다(대기열 42).

같은 PR 안에서 문장을 고치고 그 문장의 인용 둘을 옛 문구대로 둔 것을 리뷰가 잡았다(2026-09-28
하네스 감사, 대기열 20 의 가족). 20자 이상의 큰따옴표 인용을 뽑아 저장소의 텍스트 파일 전체에서
글자 그대로 세고, 인용 자신뿐이면(두 번째 자리가 없으면) 경고한다. `ADR NNNN` 가까이의 인용은 그
ADR 파일 전문(제목만이 아니라)에서 찾고, 없으면 저장소로 돌아가 본다. 거짓 양성(번역·요약 인용,
저장소 밖 원문)이 있어 막지 않고 경고만 낸다. `>` 인용문 줄과 코드 스팬·펜스 안은 보지 않는다.
pre-commit 이 바뀐 .md 를 넘기고 `verbose: true` 로 출력을 보인다. 기본은 스테이지된 diff 가 더한
줄만 본다 — 파일 전체를 보면 옛 인용(대기열의 한 줄 후보, 런북의 프롬프트 예시)이 대기열 파일
하나에서만 서른 건 남짓 울려 경고를 무시하게 된다(2026-09-28 실측). `--all-lines` 로 전체를 본다.
인자가 없으면 추적되는 .md 전부가 대상이고, `.claude/skills/` 의 사본은 어느 모드에서든 뺀다 —
남이 쓴 영문 인용이 원문 없이 많다.
못 보는 것: 20자 미만의 인용, 홑따옴표·꺾쇠 인용, 줄바꿈을 넘는 인용, 기본 모드에서 바뀐 파일의
바뀌지 않은 줄에 있는 인용, 같은 틀린 인용이 두 곳에 있는 것(둘이 서로를 세어 준다), 원문이
저장소 밖인 인용(경고가 거짓 양성이다), 마크다운 밖의 인용, 원문이 바뀐 뒤 인용만 옛 문구인 것 중
옛 문구가 다른 기록(일지)에 남아 있는 것.
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
TEXT_SUFFIXES = frozenset({".md", ".py", ".toml", ".json", ".yaml", ".yml", ".txt", ".ps1", ".sh"})
SKIPPED_PREFIXES = (".claude/skills/",)
MIN_LENGTH = 20
_FENCE = re.compile(r"^[ \t]*(?:[-*+]\s+)?(`{3,}|~{3,}).*?^[ \t]*\1[ \t]*$", re.M | re.S)
_OPEN_FENCE = re.compile(
    r"^[ \t]*(?:[-*+]\s+)?(?:`{3,}|~{3,}).*\Z", re.M | re.S
)  # 닫히지 않은 펜스
_CODE_SPAN = re.compile(r"`[^`\n]+`")
_LIST_MARKER = re.compile(r"^[ \t]*(?:[-*+]|\d+\.)\s+")
_QUOTE = re.compile(r"[\"“]([^\"”\n]+)[\"”]")
# `ADR 0012("길은 셋이고 …")`, `ADR 0009의 2026-09-22 이력 "…"`. 인용은 그 ADR 파일에 있어야 한다.
# 창은 25자이고 다른 `ADR` 을 넘지 않는다 — 넓으면 무관한 인용을 그 ADR 것으로 돌린다.
_NEAR_ADR = re.compile(r"ADR\s*(\d{4})(?:(?!ADR)[^\"“\n]){0,25}?[\"“]([^\"”\n]{6,})[\"”]")
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


def _prose(markdown: str) -> str:
    """펜스는 줄 수만 남기고 비운다. 코드 스팬 안의 따옴표는 지우고 백틱은 벗긴다."""
    text = _FENCE.sub(lambda m: "\n" * m.group(0).count("\n"), markdown)
    text = _OPEN_FENCE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    text = _CODE_SPAN.sub(lambda m: re.sub(r"[\"“”']", "", m.group(0)), text)
    return normalize(text)


def _clean(text: str) -> str | None:
    """인용 본문. 앞뒤 생략 부호를 떼고, 따옴표 쌍이 어긋나 잡힌 조각(닫는 표 뒤부터)은 버린다."""
    text = text.strip().strip("….").strip()
    if not text or text[0] in ")]},.;:" or text[-1] in "([{":
        return None
    return text


def quotes_in(markdown: str) -> list[Quote]:
    """산문의 큰따옴표 인용. 펜스·코드 스팬·`>` 줄은 뺀다. 줄 번호는 원문 기준이다."""
    quotes: list[Quote] = []
    for number, line in enumerate(_prose(markdown).splitlines(), 1):
        if _LIST_MARKER.sub("", line).lstrip().startswith(">"):
            continue
        near_adr: dict[str, str] = {}
        for match in _NEAR_ADR.finditer(line):
            text = _clean(match.group(2))
            if text is not None:
                near_adr[text] = match.group(1)
        for text, adr in near_adr.items():
            quotes.append(Quote(number, text, adr))
        for match in _QUOTE.finditer(line):
            text = _clean(match.group(1))
            if text is None or text in near_adr or len(text) < MIN_LENGTH:
                continue
            quotes.append(Quote(number, text, None))
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


def staged_added_lines(path: Path, root: Path = ROOT) -> set[int] | None:
    """스테이지된 diff 가 더한 줄들. git 이 없거나 diff 가 비면 None(전체를 본다).

    diff 가 빈 것은 pre-commit 밖에서 스테이지하지 않은 파일을 손으로 넘긴 경우다. 그때 아무것도
    보지 않으면 검사가 조용히 빈 것이 되므로 전체를 본다. `pre-commit run --all-files` 도 같다.
    """
    result = subprocess.run(
        ["git", "-C", str(root), "diff", "--cached", "-U0", "--no-color", "--", str(path)],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return added_lines_from_diff(result.stdout.decode("utf-8", "replace"))


LineFilter = Callable[[Path], "set[int] | None"]


def warnings_for(
    files: list[Path], root: Path = ROOT, line_filter: LineFilter | None = None
) -> list[str]:
    """파일들의 인용 중 원문을 찾지 못한 것. 파일:줄: 인용 — 이유.

    `line_filter` 가 파일마다 볼 줄 번호들을 주면 그 줄의 인용만 본다(pre-commit 은
    `staged_added_lines`). 옛 줄의 인용은 그 줄이 들어올 때 봤거나 이 검사 전의 것이라, 커밋마다
    다시 경고하면 경고를 무시하는 습관만 만든다. 필터가 None 을 주면 그 파일은 전체를 본다.
    """
    corpus = load_corpus(root)
    warnings: list[str] = []
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
        for quote in quotes_in(markdown):
            if allowed is not None and quote.line not in allowed:
                continue
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
                    "옮기거나 따옴표를 뗀다(대기열 42)"
                )
    return warnings


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
    warnings = warnings_for(files, line_filter=None if all_lines else staged_added_lines)
    for warning in warnings:
        print(warning)
    if warnings:
        print(f"인용 대조 경고 {len(warnings)}건. 막지 않는다 — 원문과 다른 인용인지 하나씩 본다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
