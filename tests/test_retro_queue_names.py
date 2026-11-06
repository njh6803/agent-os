"""회고 반영 대기열 항목 파일의 판정자. 옛 표 파일은 없고, 항목은 모양과 이름을 지킨다.

대기열은 `.scratch/retro-queue/` 폴더의 항목 파일이다(ADR 0045 결정 1). 두 브랜치가 서로 다른 항목을
더하면 부딪히지 않는 것이 이 구조의 이유인데, 옛 스킬 사본을 실은 세션이 옛 표 파일
`.scratch/retro-queue.md`를 다시 만들거나 번호를 이어 `0582.md`·`582.md`를 만들면 그 이점이 조용히
깨진다. CI 는 PR 의 병합 커밋에서 돌고 main 보호가 strict 라, 나중에 병합되는 PR 은 main 을 들인
뒤의 CI 에서 이 테스트에 걸린다. 일지와 티켓의 같은 자리는 `tests/test_journal_names.py`와
`tests/test_harness_ticket_names.py`가 본다.

막지 못하는 것: 관리자 우회 병합과 main 직접 푸시. 그 뒤로는 main 의 push CI 와 뒤따르는 PR 이 모두
이 테스트에서 빨갛다.
못 보는 것: 항목의 모양과 이름은 `.scratch/retro-queue/` 바로 아래의 `.md`만 본다. 하위 폴더와 다른
확장자는 항목으로 읽지 않고, 대신 `stray_problems`가 그런 것이 폴더에 있는 것을 따로 잡는다. 항목
안의 첫 줄 머리 글, 어디로·승인 줄의 값, 번호의 빠짐과 차례, 같은 일을 다룬
항목이 둘인 것.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

import pytest
from tools.queue_open_rows import QUEUE, label_problem, main, read_folder

# 이 PR이 마지막으로 origin/main을 합친 때 옛 표의 가장 큰 번호. main을 다시 합치면 그때의 값으로
# 옮긴다.
MAX_OLD_NUMBER = 581

ROOT = Path(__file__).resolve().parent.parent
OLD_FILE = ROOT / ".scratch" / "retro-queue.md"
FOLDER = ROOT / QUEUE
README = ".scratch/retro-queue/README.md"
_OLD_NAME = re.compile(r"(?P<number>\d{4})\.md")
_SLUG_NAME = re.compile(r"[a-z][a-z0-9-]*\.md")


def old_file_problems(old_file: Path) -> list[str]:
    """옛 표 파일이 있는 것."""
    if not old_file.exists():
        return []
    return [
        f".scratch/retro-queue.md가 있다. 대기열은 .scratch/retro-queue/ 폴더의 항목 파일이다. "
        "이 파일에 적은 변경은 항목 파일로 옮겨 적고 옛 파일을 지운다. "
        f"파일 모양과 제목 규칙은 {README}에 있다."
    ]


def label_problems(files: dict[str, str]) -> list[str]:
    """첫 줄 뒤에 `**상태:**`, `**어디로:**`, `**승인:**` 줄이 이 차례로 없는 항목."""
    problems: list[str] = []
    for name, text in sorted(files.items()):
        reason = label_problem(name, text)
        if reason is not None:
            problems.append(
                f"{QUEUE.as_posix()}/{name}: {reason}. 항목 파일은 첫 줄 `# <ID>: <머리>` 뒤에 "
                "`**상태:**`, `**어디로:**`, `**승인:**` 줄이 이 차례로 있어야 한다. "
                f"파일 모양은 {README}에 있다."
            )
    return problems


def name_problems(names: Iterable[str]) -> list[str]:
    """이름이 상수 이하인 네 자리 숫자도 영어 소문자로 시작하는 제목도 아닌 것."""
    problems: list[str] = []
    for name in sorted(names):
        old = _OLD_NAME.fullmatch(name)
        if _SLUG_NAME.fullmatch(name) or (old and int(old["number"]) <= MAX_OLD_NUMBER):
            continue
        problems.append(
            f"{QUEUE.as_posix()}/{name}: 항목 이름이 규칙 밖이다. 옛 번호는 네 자리로 채운 "
            f"{MAX_OLD_NUMBER:04d} 이하(MAX_OLD_NUMBER = {MAX_OLD_NUMBER})이고, 새 항목은 영어 "
            f"소문자로 시작하는 제목(영어 소문자·숫자·하이픈)이다. 제목 규칙은 {README}에 있다."
        )
    return problems


def stray_problems(folder: Path) -> list[str]:
    """폴더 바로 아래에 `README.md`도 항목 파일도 아닌 것(하위 폴더, 다른 확장자, 대문자 확장자)."""
    problems: list[str] = []
    for entry in sorted(folder.iterdir(), key=lambda p: p.name):
        if entry.is_file() and (entry.name == "README.md" or entry.suffix == ".md"):
            continue
        problems.append(
            f"{QUEUE.as_posix()}/{entry.name}: 항목 파일이 아닌 것이 폴더에 있다. 이 폴더에는 "
            f"`README.md`와 `<ID>.md` 항목 파일만 둔다. 이름 규칙은 {README}에 있다."
        )
    return problems


def test_옛_대기열_파일이_없다() -> None:
    assert old_file_problems(OLD_FILE) == []


def test_이_저장소의_대기열_폴더에는_항목_파일과_README만_있다() -> None:
    assert any(FOLDER.iterdir()), "폴더가 비었다. 경로가 틀렸을 수 있다"
    assert stray_problems(FOLDER) == []


def test_이_저장소의_대기열_항목은_모두_라벨_줄_셋을_갖는다() -> None:
    files = read_folder(FOLDER)
    assert files, "항목 파일이 하나도 없다. 폴더 경로가 틀렸을 수 있다"
    assert label_problems(files) == []


def test_이_저장소의_대기열을_도구로_빠짐없이_읽는다(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--queue", str(FOLDER)]) == 0
    first = capsys.readouterr().out.splitlines()[0]
    match = re.fullmatch(r"열린 항목 (\d+)개", first)
    assert match is not None, first
    assert int(match[1]) >= 1, "열린 항목이 하나도 없다. 경로나 상태 판정이 틀렸을 수 있다"


def test_이_저장소의_대기열_항목_이름은_규칙_안이다() -> None:
    names = list(read_folder(FOLDER))
    assert names, "항목 파일이 하나도 없다. 폴더 경로가 틀렸을 수 있다"
    assert name_problems(names) == []


def test_옛_대기열_파일이_있으면_잡는다_실패_문장은_할_일과_README를_든다(tmp_path: Path) -> None:
    old_file = tmp_path / "retro-queue.md"
    assert old_file_problems(old_file) == []
    old_file.write_text("| # | 무엇 | 어디로 | 승인 |\n", encoding="utf-8")
    (problem,) = old_file_problems(old_file)
    assert ".scratch/retro-queue.md가 있다" in problem
    assert ".scratch/retro-queue/ 폴더의 항목 파일" in problem
    assert "항목 파일로 옮겨 적고 옛 파일을 지운다" in problem
    assert README in problem


def test_라벨_줄이_빠진_항목을_잡는다_경로와_빠진_줄과_README를_든다(tmp_path: Path) -> None:
    good = "# 0001: 일\n\n**상태:** 열림\n**어디로:** `a.md`\n**승인:** 1회차\n"
    (tmp_path / "0001.md").write_text(good, encoding="utf-8")
    (tmp_path / "0002.md").write_text(
        "# 0002: 일\n\n**어디로:** `a.md`\n**승인:** 1회차\n", "utf-8"
    )
    (tmp_path / "README.md").write_text("# 규칙\n", encoding="utf-8")
    assert label_problems(read_folder(tmp_path))[0].startswith(".scratch/retro-queue/0002.md: ")
    (problem,) = label_problems(read_folder(tmp_path))
    assert "빠진 줄: **상태:**" in problem
    assert README in problem
    assert label_problems({"0001.md": good}) == []


def test_규칙_밖의_항목_이름을_잡는다_경로와_상수와_README를_든다() -> None:
    bad = ["0582.md", "582.md", "0001x.md", "Alpha.md", "9slug.md", "a_b.md", "-a.md", "0001.txt"]
    problems = name_problems(bad)
    assert len(problems) == len(bad)
    for name in bad:
        assert any(p.startswith(f".scratch/retro-queue/{name}: ") for p in problems), name
    for problem in problems:
        assert "MAX_OLD_NUMBER = 581" in problem
        assert README in problem


def test_폴더의_잔여물을_잡는다_하위_폴더와_다른_확장자와_대문자_확장자(tmp_path: Path) -> None:
    (tmp_path / "0001.md").write_text("# 0001: 일\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# 규칙\n", encoding="utf-8")
    assert stray_problems(tmp_path) == []
    (tmp_path / "0582.txt").write_text("x", encoding="utf-8")
    (tmp_path / "0583.MD").write_text("x", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    problems = stray_problems(tmp_path)
    assert len(problems) == 3
    for name in ("0582.txt", "0583.MD", "sub"):
        assert any(p.startswith(f".scratch/retro-queue/{name}: ") for p in problems), name


def test_규칙_안의_항목_이름은_지나간다() -> None:
    ok = ["0001.md", "0581.md", "coderabbit-inline-size.md", "a.md", "retro-v2.md", "a1-b2.md"]
    assert name_problems(ok) == []
