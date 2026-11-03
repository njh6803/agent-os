"""SKILL.md 의 머리말을 본문에서 떼는 규칙(줄 단위 `---` 가르기)을 재는 탐침. 명세가 근거로 든다.

재는 것은 셋이다. (1) 양성 대조 — 파일 전체를 `yaml.safe_load` 에 그대로 넘기면 둘째 `---` 가 둘째
문서의 시작이라 `yaml.YAMLError` 로 거부된다. 그래서 YAML 에 넘기기 전에 머리말을 떼는 자리가 있어야
한다. (2) 명세가 정한 줄 단위 규칙(아래 `split_front_matter`)이 입력 모양마다 기대한 머리말과 본문을
내는지. LF, CRLF, 본문 안의 `---` 줄, 머리말 값 안의 `---`(줄 가운데), 본문 없음, 닫는 줄 없음,
`---` 로 시작하지 않음(BOM, 앞의 빈 줄), 빈 머리말. (3) 갈래 — Agent Skills 의 참조 구현
(`skills-ref` 의 `parser.py`, github `agentskills/agentskills` main, 2026-11-03 에 원문을 읽었다)이
쓰는 `text.split("---", 2)` 는 줄이 아니라 글자 열에서 가르므로 머리말 값 안의 `---` 에서 머리말을
끊는다. 같은 입력에 줄 단위 규칙이 바르게 읽는 것을 보여 두 규칙을 가른다. 그리고 YAML 자체가 머리말
안의 `---` 줄(열 0)을 문서 시작으로 읽어 거부하므로, 줄 단위 규칙이 닫는 줄로 삼는 `---` 줄이 머리말
안에 있을 수 없다는 것도 본다(줄 규칙이 잃는 입력이 없다는 근거). 그 줄이 설 수 있는 자리 셋 —
큰따옴표 스칼라 안, 블록 스칼라(`|`) 안, 평문 스칼라의 이어지는 줄 — 을 갈래로 둔다. 어느 자리든
거부되는 까닭은 PyYAML 스캐너가 토큰을 읽기 전에 열 0의 `---` 뒤에 공백·줄 바꿈·끝이 오면 문서
시작으로 보기 때문이다(설치된 6.0.3의 `yaml/scanner.py` `check_document_start`. 코드를 읽었다). 세
갈래 밖의 자리(주석 줄은 `#`으로 시작해 `---` 그대로일 수 없다)는 재지 않았다. 세 자리마다 `---`
줄만 뺀 같은 모양이 받아들여지는 대조를 두어, 거부의 까닭이 그 줄이지 둘러싼 모양이 아님을 가른다
(평문 스칼라의 이어지는 줄은 들여쓰기가 있어야 이어지므로 대조는 들여쓴 줄이고, 거부 입력은 그
들여쓴 줄 앞에 `---` 줄을 둔 것이라 둘은 그 줄만 다르다). (4) 파일에서 읽는 길 — 어댑터가
매니페스트를 읽는 길(`Path.read_text(encoding="utf-8")`. `adapters/filesystem.py` 의 `_parse`,
코드를 읽었다)로 CRLF 파일을 읽으면 파이썬의 보편 줄 바꿈이 `\r\n` 을 `\n` 으로 바꿔 글에 `\r` 이
없고, 같은 파일을 `read_bytes().decode("utf-8")` 로 읽으면 `\r\n` 이 남는다. BOM 파일은 `utf-8` 로
읽으면 U+FEFF 가 첫 글자로 남아 규칙이 거부한다. 첫 줄 끝의 `\r` 이 둘인 파일과 홀로 선 `\r`(옛
Mac)뿐인 파일은 그 길이 `\r` 을 모두 `\n` 으로 바꿔 받아들여진다(글을 직접 넘기면 둘 다
"시작하지"로 거부된다). 매니페스트 쪽의 같은 입력(BOM 뒤의 TOML)은 `tomllib` 이 거부한다.

표지. 양성 대조는 `yaml.YAMLError` 의 하위 타입이 났을 때만 측정이다. 규칙 회차는 뗀 머리말을
`yaml.safe_load` 로 읽은 값과 본문이 기대한 것과 글자 그대로 같을 때만, 거부 회차는 기대한 예외와
문구가 났을 때만 측정이다. 갈래 회차는 참조 구현의 가르기가 기대한 틀린 자리에서 끊겼을 때만, 세
자리 회차는 기대한 클래스(큰따옴표는 `ScannerError`, 블록과 평문은 `ComposerError`)의 예외가 났을
때만, 그 대조는 `description` 이 기대한 값일 때만 측정이다. 참조 구현 갈래는 끊긴 자리와 YAML 이
낸 값이 모두 기대와 같을 때만이다. 파일 회차는 두 읽기의 글이 `\r` 의 있고 없음에서 기대와 같을
때, BOM 파일은 규칙이 "시작하지"로 거부할 때, `\r` 둘과 홀로 선 `\r` 의 파일은 읽은 글에 `\r` 이
없고 규칙이 기대한 머리말과 본문을 낼 때(글을 직접 넘긴 대조는 "시작하지"로 거부할 때),
`tomllib` 은 `TOMLDecodeError` 일 때만 측정이다. 같지 않거나 다른 예외로 끝나면 측정이 아니다.

전제와 못 보는 것. 규칙의 구현은 이 파일의 `split_front_matter` 이고 명세의 글과 같아야 한다. 구현
티켓이 sdk 에 두는 함수가 이것과 같은지는 그 티켓의 시험이 같은 사례로 잰다. 잰 것은 가르기까지이고
칸의 검증(이름 패턴, 문자열 여부)은 `frontmatter_values.py` 가 잰다. 둘째 판(셀프 리뷰 뒤)이
바꾼 것 셋: 첫 판은 표지 줄의 `\r` 을 `rstrip` 으로 떼어 둘 이상도 뗐는데 규칙은 "하나"라 정확히
하나만 떼게 고치고 `---\r\r` 로 시작하는 입력을 거부 회차로 더했다. 세 자리 회차는 첫 판이
`YAMLError` 하위인지만 봐서 README 가 적은 클래스를 단언하지 않았고, 그 줄만 뺀 대조도 없었다.
파일에서 읽는 길은 첫 판이 재지 않았다. 셋째 판(PR 직전 리뷰 뒤)이 바꾼 것 셋: 평문 갈래의 거부
입력이 대조와 들여쓰기까지 달라 `---` 줄만 다른 쌍이 아니었던 것을 맞췄다. 참조 구현 갈래가 끊긴
자리만 보고 YAML 이 낸 값은 단언하지 않던 것을 값까지 단언하게 했다. 줄 끝 `\r` 둘과 홀로 선
`\r`(옛 Mac)의 파일을 어댑터의 길로 읽는 회차를 더했다(둘째 판까지 홀로 선 `\r` 은 넣지 않았다).

돌리는 법: 저장소 루트에서
`PYTHONUTF8=1 uv run python .scratch/skill-plugin/probes/frontmatter_split.py`
"""

from __future__ import annotations

import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402
from tools.probe_kit import Rounds  # noqa: E402

MARKER = "---"
BOM = chr(0xFEFF)


def _is_marker(line: str) -> bool:
    """줄 끝의 `\\r` 하나만 떼고 `---` 그대로인지 본다. `\\r` 이 둘이면 표지 줄이 아니다."""
    if line.endswith("\r"):
        line = line[:-1]
    return line == MARKER


def split_front_matter(text: str) -> tuple[str, str]:
    """명세의 규칙. 첫 줄이 `---` 그대로여야 하고, 그 뒤 처음 나오는 `---` 그대로인 줄이 닫는
    줄이다.

    줄은 `\\n` 으로 가르고 줄 끝의 `\\r` 하나는 뗀다(CRLF). 머리말은 두 줄 사이의 글이고 본문은 닫는
    줄의 줄 바꿈 뒤의 글 그대로다(앞뒤를 다듬지 않는다). 닫는 줄이 없거나 첫 줄이 `---` 가 아니면
    `ValueError` 다.
    """
    lines = text.split("\n")
    if not _is_marker(lines[0]):
        raise ValueError("머리말로 시작하지 않는다: 첫 줄이 --- 가 아니다")
    for index in range(1, len(lines)):
        if _is_marker(lines[index]):
            head = "\n".join(lines[1:index])
            body_start = sum(len(line) + 1 for line in lines[: index + 1])
            return head, text[body_start:]
    raise ValueError("머리말이 닫히지 않았다: --- 줄이 없다")


HEAD = {"name": "pdf-processing", "description": "PDF 를 다룬다"}

ACCEPTED: list[tuple[str, str, str]] = [
    (
        "LF 와 본문",
        "---\nname: pdf-processing\ndescription: PDF 를 다룬다\n---\n# 제목\n\n본문이다.\n",
        "# 제목\n\n본문이다.\n",
    ),
    (
        "CRLF 와 본문",
        "---\r\nname: pdf-processing\r\ndescription: PDF 를 다룬다\r\n---\r\n"
        "# 제목\r\n본문이다.\r\n",
        "# 제목\r\n본문이다.\r\n",
    ),
    (
        "본문 안의 --- 줄은 본문에 남는다",
        "---\nname: pdf-processing\ndescription: PDF 를 다룬다\n---\n앞\n---\n뒤\n",
        "앞\n---\n뒤\n",
    ),
    (
        "본문이 없다(닫는 줄로 끝남)",
        "---\nname: pdf-processing\ndescription: PDF 를 다룬다\n---\n",
        "",
    ),
    (
        "본문이 없다(닫는 줄 뒤 줄 바꿈도 없음)",
        "---\nname: pdf-processing\ndescription: PDF 를 다룬다\n---",
        "",
    ),
]

MID_LINE = "---\nname: pdf-processing\ndescription: 가 --- 나\n---\n본문\n"

REJECTED: list[tuple[str, str, str]] = [
    ("닫는 줄이 없다", "---\nname: pdf-processing\ndescription: PDF\n본문\n", "닫히지 않았다"),
    ("BOM 으로 시작한다", BOM + "---\nname: pdf-processing\ndescription: PDF\n---\n", "시작하지"),
    ("앞에 빈 줄이 있다", "\n---\nname: pdf-processing\ndescription: PDF\n---\n", "시작하지"),
    ("머리말 없이 본문뿐이다", "# 제목\n본문\n", "시작하지"),
    ("첫 줄 끝에 \\r 이 둘", "---\r\r\nname: pdf-processing\ndescription: PDF\n---\n", "시작하지"),
]

EMPTY_HEAD = "---\n---\n본문\n"
MARKER_IN_QUOTED = 'name: pdf-processing\ndescription: "앞\n---\n뒤"\n'
MARKER_IN_BLOCK = "name: pdf-processing\ndescription: |\n  앞\n---\n  뒤\n"
MARKER_IN_PLAIN = "name: pdf-processing\ndescription: 앞\n---\n  뒤\n"
# (자리, 입력, 기대한 YAMLError 하위 클래스 이름)
MARKER_INSIDE: list[tuple[str, str, str]] = [
    ("큰따옴표 스칼라 안", MARKER_IN_QUOTED, "ScannerError"),
    ("블록 스칼라 안", MARKER_IN_BLOCK, "ComposerError"),
    ("평문 스칼라의 이어지는 줄", MARKER_IN_PLAIN, "ComposerError"),
]
# 같은 자리에서 --- 줄만 뺀 모양과 기대한 description (대조)
WITHOUT_MARKER: list[tuple[str, str, str]] = [
    ("큰따옴표 스칼라 안", 'name: pdf-processing\ndescription: "앞\n뒤"\n', "앞 뒤"),
    ("블록 스칼라 안", "name: pdf-processing\ndescription: |\n  앞\n  뒤\n", "앞\n뒤\n"),
    ("평문 스칼라의 이어지는 줄", "name: pdf-processing\ndescription: 앞\n  뒤\n", "앞 뒤"),
]

CRLF_FILE = ACCEPTED[1][1]
BOM_FILE = REJECTED[1][1]
BOM_TOML = BOM + 'schema_version = "1"\n'
CRCR_FILE = REJECTED[4][1]
CR_FILE = "---\rname: pdf-processing\rdescription: PDF\r---\r본문\r"
# REJECTED 와 CR_FILE 의 머리말은 description 이 짧은 "PDF" 다
SHORT_HEAD = {"name": "pdf-processing", "description": "PDF"}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    rounds = Rounds()

    with rounds.round("양성 대조: 파일 전체를 YAML 로 읽으면 거부") as current:
        try:
            yaml.safe_load(ACCEPTED[0][1])
        except yaml.YAMLError as error:
            current.mark(measured=True, result=f"거부 {type(error).__name__}")

    for label, text, body in ACCEPTED:
        with rounds.round(f"규칙: {label}") as current:
            head, rest = split_front_matter(text)
            if yaml.safe_load(head) == HEAD and rest == body:
                current.mark(measured=True, result="머리말과 본문이 기대한 그대로")

    with rounds.round("규칙: 머리말 값 안의 ---(줄 가운데)는 값에 남는다") as current:
        head, rest = split_front_matter(MID_LINE)
        if yaml.safe_load(head) == {"name": "pdf-processing", "description": "가 --- 나"}:
            if rest == "본문\n":
                current.mark(measured=True, result="값 '가 --- 나' 그대로, 본문 그대로")

    for label, text, marker in REJECTED:
        with rounds.round(f"거부: {label}") as current:
            try:
                split_front_matter(text)
            except ValueError as error:
                if marker in str(error):
                    current.mark(measured=True, result=f"ValueError '{error}'")

    with rounds.round(
        "규칙: 빈 머리말은 YAML 이 None 을 준다(맵이 아님으로 거부할 자리)"
    ) as current:
        head, rest = split_front_matter(EMPTY_HEAD)
        parsed = yaml.safe_load(head)
        if head == "" and parsed is None and rest == "본문\n":
            current.mark(measured=True, result="머리말 '' → None, 본문 그대로")

    with rounds.round("갈래: 참조 구현의 split('---', 2) 는 값 안의 --- 에서 끊는다") as current:
        parts = MID_LINE.split(MARKER, 2)
        head_by_split = parts[1]
        try:
            parsed = yaml.safe_load(head_by_split)
        except yaml.YAMLError as error:
            parsed = type(error).__name__
        expected_by_split = {"name": "pdf-processing", "description": "가"}
        if (
            head_by_split == "\nname: pdf-processing\ndescription: 가 "
            and parsed == expected_by_split
        ):
            current.mark(measured=True, result=f"머리말이 '가 ' 에서 끊김, YAML 결과 {parsed!r}")

    for label, text, expected in MARKER_INSIDE:
        with rounds.round(
            f"갈래: 머리말 안의 --- 줄(열 0)은 YAML 자체가 거부한다: {label}"
        ) as current:
            try:
                yaml.safe_load(text)
            except yaml.YAMLError as error:
                if type(error).__name__ == expected:
                    current.mark(measured=True, result=f"거부 {expected}")

    for label, text, description in WITHOUT_MARKER:
        with rounds.round(f"대조: --- 줄만 뺀 같은 자리는 받아들여진다: {label}") as current:
            parsed = yaml.safe_load(text)
            if parsed == {"name": "pdf-processing", "description": description}:
                current.mark(measured=True, result=f"description {description!r}")

    with tempfile.TemporaryDirectory() as directory:
        crlf_path = Path(directory) / "crlf.md"
        crlf_path.write_bytes(CRLF_FILE.encode("utf-8"))
        bom_path = Path(directory) / "bom.md"
        bom_path.write_bytes(BOM_FILE.encode("utf-8"))

        with rounds.round(
            "파일: CRLF 파일을 어댑터의 길(read_text)로 읽으면 LF 가 되고 bytes 로 읽으면 남는다"
        ) as current:
            text_mode = crlf_path.read_text(encoding="utf-8")
            bytes_mode = crlf_path.read_bytes().decode("utf-8")
            if "\r" not in text_mode and "\r\n" in bytes_mode:
                head, rest = split_front_matter(text_mode)
                if yaml.safe_load(head) == HEAD and rest == "# 제목\n본문이다.\n":
                    current.mark(measured=True, result="read_text 는 LF, bytes 는 CRLF 그대로")

        with rounds.round(
            "파일: BOM 파일을 utf-8 로 읽으면 BOM 이 남아 규칙이 거부한다"
        ) as current:
            text_mode = bom_path.read_text(encoding="utf-8")
            if text_mode.startswith(BOM):
                try:
                    split_front_matter(text_mode)
                except ValueError as error:
                    if "시작하지" in str(error):
                        current.mark(measured=True, result=f"U+FEFF 남음, ValueError '{error}'")

        crcr_path = Path(directory) / "crcr.md"
        crcr_path.write_bytes(CRCR_FILE.encode("utf-8"))
        cr_path = Path(directory) / "cr.md"
        cr_path.write_bytes(CR_FILE.encode("utf-8"))

        with rounds.round(
            "파일: 첫 줄 끝 \\r 둘인 파일은 어댑터의 길로 읽으면 \\r 이 사라져 받아들여진다"
        ) as current:
            text_mode = crcr_path.read_text(encoding="utf-8")
            if "\r" not in text_mode and text_mode.startswith("---\n\n"):
                head, rest = split_front_matter(text_mode)
                if yaml.safe_load(head) == SHORT_HEAD and rest == "":
                    current.mark(measured=True, result="'---\\n\\n' 으로 시작, 머리말 그대로")

        with rounds.round(
            "파일: 홀로 선 \\r(옛 Mac) 파일은 어댑터의 길로 읽으면 \\n 이 되어 받아들여진다"
        ) as current:
            text_mode = cr_path.read_text(encoding="utf-8")
            if "\r" not in text_mode:
                head, rest = split_front_matter(text_mode)
                if yaml.safe_load(head) == SHORT_HEAD and rest == "본문\n":
                    current.mark(measured=True, result="\\r 이 모두 \\n, 머리말과 본문 그대로")

    with rounds.round(
        "대조: 홀로 선 \\r 의 글을 직접 넘기면 첫 줄이 --- 가 아니라 거부"
    ) as current:
        try:
            split_front_matter(CR_FILE)
        except ValueError as error:
            if "시작하지" in str(error):
                current.mark(measured=True, result=f"ValueError '{error}'")

    with rounds.round(
        "대조: BOM 뒤의 TOML 은 tomllib 이 거부한다(매니페스트의 같은 입력)"
    ) as current:
        try:
            tomllib.loads(BOM_TOML)
        except tomllib.TOMLDecodeError as error:
            current.mark(measured=True, result=f"거부 TOMLDecodeError '{error}'")

    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
