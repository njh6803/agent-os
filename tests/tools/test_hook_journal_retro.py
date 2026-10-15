"""tools/hook_journal_retro.py 의 순수 함수. stdin 을 읽는 main 은 실제 실행으로 확인한다.

발동 조건은 대기열 28 의 것을 좁힌 것이다 — Write 의 content 나 Edit 의 new_string 이 `## 다음` 을
담을 때. 경로만 보던 동안 인용 하나를 고친 Edit 마다 계기가 울렸다(대기열 28 의 5회차와 일지 둘).
그 뒤 대기열 62·74 로 더 좁혔다. 제목은 줄 머리의 것만이고, 절이 비었거나 자리 표시뿐이거나 Edit 가
앞뒤에 같은 절을 옮겼을 뿐이거나 일지에 회고 절이 이미 있으면 단계를 닫은 것이 아니다.

새 일지 파일의 순번 대조(대기열 232)는 `tools/sibling_overlap.py` 의 출력을 읽는다. 판정은 출력
글로 재고, 출력의 꼴이 훅이 읽는 꼴과 같은지는 임시 저장소에서 그 도구를 실제로 돌려 본다.
"""

from __future__ import annotations

import os
import subprocess
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest
from tools.hook_journal_retro import (
    CLOSING_HEADING,
    NUMBER_LEAD,
    Overlap,
    context_for,
    created_journal,
    is_journal,
    number_context,
    read_journal,
    run_overlap,
    section_body,
)
from tools.run_hooks import journal_repository

JOURNAL = "C:\\project\\agent\\docs\\journal\\2026-09-21-first-slice.md"
NEW = "C:\\x\\docs\\journal\\2026-10-07-03-hooks.md"


def _output(following: str, ours: str | None = "2026-10-07-03") -> str:
    """도구 출력의 두 줄(`tools/sibling_overlap.py` 의 `render`). `ours` 는 이 브랜치의 새 일지
    순번이고, None 이면 새 번호가 없다."""
    mine = f"이 브랜치의 새 번호: 일지 {ours}, 대기열 281" if ours else "이 브랜치의 새 번호 없음"
    return f"다음 빈 번호(형제 포함): 일지 {following}, 대기열 282\n{mine}\n"


def test_다음_절을_담은_Write_는_retro_계기_문장을_돌려준다() -> None:
    context = context_for("Write", JOURNAL, "# 일지\n\n## 다음\n\n- web-admin 설계")

    assert context is not None
    assert "retro" in context


def test_다음_절이_없는_Write_는_계기가_아니다() -> None:
    """세션 첫머리에 일지를 새로 쓰는 Write 는 단계를 닫는 것이 아니다(PR #91 리뷰)."""
    assert context_for("Write", JOURNAL, "# 일지\n\n## 감사\n") is None
    assert context_for("Write", JOURNAL, None) is None


def test_다음_절을_담은_Edit_도_계기다() -> None:
    assert context_for("Edit", JOURNAL, "## 다음\n\n- web-admin 설계") is not None


def test_다음_절을_건드리지_않은_Edit_는_계기가_아니다() -> None:
    """인용 하나를 원문으로 고친 Edit 에 계기가 울리던 자리다(대기열 28, 5회차)."""
    assert context_for("Edit", JOURNAL, '"화면이 없어도 시스템이 돌고"') is None
    assert context_for("Edit", JOURNAL, None) is None


def test_산문의_코드_스팬_속_다음_은_제목이_아니다() -> None:
    """일지 2026-10-01-02 의 한 줄이 부분 문자열 검사에 걸렸다(대기열 74)."""
    prose = (
        "# 일지\n\n## 잰 것\n\n- 임시 일지에\n"
        "  `## 다음`을 Write로, 이어서 Edit로 쓰자 둘 다 문구가 이 세션에 닿았다\n"
    )

    assert context_for("Write", JOURNAL, prose) is None
    assert context_for("Edit", JOURNAL, "`## 다음`을 Write로 쓰자") is None


def test_제목_줄_끝의_공백과_CR_은_제목이다() -> None:
    assert context_for("Write", JOURNAL, "# 일지\n\n## 다음  \n\n- web-admin 설계") is not None
    assert context_for("Write", JOURNAL, "# 일지\r\n\r\n## 다음\r\n\r\n- web-admin\r\n") is not None


@pytest.mark.parametrize(
    "본문",
    [
        pytest.param("# 일지\n\n## 다음\n", id="제목만"),
        pytest.param("# 일지\n\n## 다음\n\n\n", id="빈_줄뿐"),
        pytest.param("# 일지\n\n## 다음\n\n(회고 뒤에 채운다)\n", id="괄호_한_줄"),
        pytest.param("# 일지\n\n## 다음\n\n- (회고 뒤에 채운다)\n", id="불릿_괄호"),
        pytest.param("# 일지\n\n## 다음\n\n（회고 뒤에）\n", id="전각_괄호"),
    ],
)
def test_비었거나_자리_표시뿐인_다음_절은_계기가_아니다(본문: str) -> None:
    """자리 표시로 절을 먼저 두자 단계를 닫은 것으로 보고 retro 를 요구했다(대기열 62). 원래의 자리
    표시 문구는 남지 않아 여기 문구는 행의 "괄호 한 줄짜리" 를 따라 지었다."""
    assert context_for("Write", JOURNAL, 본문) is None


@pytest.mark.parametrize(
    "줄",
    [
        pytest.param("(04 가 먼저다) 05 는 03 과 04 를 기다린다", id="괄호로_닫히지_않는다"),
        pytest.param("(web-admin) 04 가 다음이다 (05~08 의 임계 경로)", id="괄호_둘"),
    ],
)
def test_괄호_한_쌍으로_감싼_한_줄이_아니면_내용이다(줄: str) -> None:
    assert context_for("Write", JOURNAL, f"# 일지\n\n## 다음\n\n{줄}\n") is not None


@pytest.mark.parametrize("줄", ["TBD", "…", "1. (채운다)"])
def test_못_보는_것_괄호_한_쌍_밖의_자리_표시는_내용으로_본다(줄: str) -> None:
    assert context_for("Write", JOURNAL, f"# 일지\n\n## 다음\n\n{줄}\n") is not None


def test_못_보는_것_펜스를_가리지_않는다() -> None:
    """펜스 안의 `## 다음` 은 제목으로, 절 안 펜스의 `# ` 줄은 절의 끝으로 본다."""
    in_fence = "# 일지\n\n```md\n## 다음\n\n- 예시\n```\n"
    comment_in_fence = "## 다음\n\n```sh\n# 주석\n- a\n```\n"

    assert section_body(in_fence, CLOSING_HEADING) == "- 예시\n```"
    assert section_body(comment_in_fence, CLOSING_HEADING) == "```sh"


def test_다음_절은_뒤의_제목에서_끝난다() -> None:
    """뒤 절의 줄은 이 절의 내용이 아니다. 하위 제목(`###`)은 절 안이다."""
    assert context_for("Write", JOURNAL, "## 다음\n\n(채운다)\n\n## 부록\n\n- 표") is None
    assert context_for("Write", JOURNAL, "## 다음\n\n(채운다)\n\n# 끝\n\n- 표") is None
    assert context_for("Write", JOURNAL, "## 다음\n\n### 남은 것\n\n- 04") is not None


def test_자리_표시를_채운_Edit_는_계기다() -> None:
    assert (
        context_for(
            "Edit",
            JOURNAL,
            "## 다음\n\n- web-admin의 04가 다음이다.",
            "## 다음\n\n(회고 뒤에 채운다)",
        )
        is not None
    )


def test_다음_절을_그대로_옮긴_Edit_는_계기가_아니다() -> None:
    """회고를 "다음" 앞에 적어 넣는 Edit 는 흔히 그 절을 닻으로 old_string 에 담고 new_string 에
    그대로 옮긴다. 절은 그대로라 단계를 다시 닫은 것이 아니다(대기열 62, 둘째 울림). 끝 줄바꿈의
    차이는 같은 절이다."""
    old = "## 다음\n\n- web-admin의 04가 다음이다.\n"
    new = "## 회고\n\n- 62(새로)\n\n## 다음\n\n- web-admin의 04가 다음이다."

    assert context_for("Edit", JOURNAL, new, old) is None


def test_다음_절을_고친_Edit_는_계기다() -> None:
    old = "## 다음\n\n- web-admin의 04가 다음이다."
    new = "## 다음\n\n- web-admin의 05가 다음이다."

    assert context_for("Edit", JOURNAL, new, old) is not None


@pytest.mark.parametrize(
    "제목",
    ["## 회고", "## 회고 (2026-09-21, 슬라이스를 닫은 뒤)", "## 회고\r"],
)
def test_일지에_회고_절이_이미_있으면_계기가_아니다(제목: str) -> None:
    """retro 를 먼저 돌고 "다음" 을 적은 편집에도 울렸다(일지 2026-09-30-02, 2026-10-01-03). 회고
    절은 retro 가 돈 흔적이다(사용자 결정 2026-10-01)."""
    closing = "## 다음\n\n- web-admin의 04가 다음이다.\n"
    journal = f"# 일지\n\n{제목}\n\n- 62(새로)\n\n{closing}"

    assert context_for("Edit", JOURNAL, closing, None, journal) is None
    assert context_for("Write", JOURNAL, journal, None, journal) is None


def test_회고_절이_여럿이면_하나라도_쓴_것이_있으면_계기가_아니다() -> None:
    """첫 절이 자리 표시뿐이고 뒤의 날짜 붙은 절에 내용이 있는 일지(PR #113 CodeRabbit)."""
    journal = (
        "# 일지\n\n## 회고\n\n(retro 뒤에)\n\n## 한 것\n\n- 04\n\n"
        "## 회고 (2026-10-01, 단계를 닫은 뒤)\n\n- 62(새로)\n\n## 다음\n\n- 05\n"
    )

    assert context_for("Edit", JOURNAL, "## 다음\n\n- 05", None, journal) is None


@pytest.mark.parametrize(
    "일지",
    [
        pytest.param("# 일지\n\n## 회고\n\n## 다음\n\n- 04\n", id="빈_회고_절"),
        pytest.param("# 일지\n\n## 회고\n\n(retro 뒤에)\n\n## 다음\n\n- 04\n", id="자리_표시"),
        pytest.param(
            "# 일지\n\n## 한 것\n\n- `## 회고` 는 아직이다\n\n## 다음\n\n- 04\n", id="코드_스팬"
        ),
        pytest.param("# 일지\n\n## 회고록\n\n- 읽은 것\n\n## 다음\n\n- 04\n", id="다른_제목"),
    ],
)
def test_쓴_회고_절이_없는_일지는_계기다(일지: str) -> None:
    assert context_for("Edit", JOURNAL, "## 다음\n\n- 04", None, 일지) is not None


def test_일지를_읽지_못하면_None_이다(tmp_path: Path) -> None:
    """None 이면 회고 절이 없는 것으로 판정한다(위의 일지 없는 사례들)."""
    journal = tmp_path / "docs" / "journal" / "2026-10-01-04-x.md"
    journal.parent.mkdir(parents=True)

    assert read_journal(str(journal)) is None
    journal.write_bytes(b"## \xff\n")
    assert read_journal(str(journal)) is None
    journal.write_text("## 회고\n\n- 62\n", encoding="utf-8")
    assert read_journal(str(journal)) == "## 회고\n\n- 62\n"


def test_일지가_아닌_파일은_도구가_무엇이든_None이다() -> None:
    assert context_for("Write", "docs/adr/0008-x.md", None) is None
    assert context_for("Edit", "docs/adr/0008-x.md", "## 다음") is None
    assert not is_journal("docs/journal/notes.txt")
    assert not is_journal("journal/2026-09-21.md")


def test_새_일지를_만든_Write_만_순번을_대_본다() -> None:
    """Write 의 결과 `type` 이 새 파일과 덮어쓰기를 가른다. Edit 의 결과에는 그 값이 없다(2026-10-16
    claude 2.1.300, `.scratch/harness/probes/journal_number_hook/run.py` 의 A)."""
    assert created_journal("Write", NEW, {"type": "create", "originalFile": None})
    assert not created_journal("Write", NEW, {"type": "update", "originalFile": "# x\n"})
    assert not created_journal("Edit", NEW, {"filePath": NEW, "originalFile": "# x\n"})
    assert not created_journal("Write", "C:\\x\\docs\\adr\\0034-x.md", {"type": "create"})
    assert not created_journal("Write", NEW, None)
    assert not created_journal("Write", NEW, {})


def test_다음_빈_번호의_바로_앞_순번이면_알리지_않는다() -> None:
    """만든 파일은 도구가 이 브랜치의 새 일지로 세므로, 맞는 순번이면 다음 빈 번호가 그 다음이다."""
    assert number_context(NEW, Overlap(0, _output("2026-10-07-04"), "")) is None


def test_형제와_겹친_순번은_도구가_옮길_번호와_move_를_알린다() -> None:
    """`ls` 로 고른 번호가 형제의 일지와 겹쳤다(대기열 232, 일지 2026-10-13-33)."""
    moves = "옮길 번호: 일지 2026-10-07-03 → 2026-10-07-05, 대기열 280 → 282\n"

    context = number_context(NEW, Overlap(1, _output("2026-10-07-06") + moves, ""))

    assert context is not None
    assert context.startswith(NUMBER_LEAD)
    assert "2026-10-07-05" in context
    assert "--move" in context
    assert "mv <옛> <새>" in context, "Write 로 새로 만들면 옛 파일이 번호를 쥐어 다시 알린다"


@pytest.mark.parametrize(
    ("파일", "다음", "새_번호"),
    [
        pytest.param(
            "2026-10-06-01-hooks.md", "2026-10-07-02", "2026-10-07-02", id="날짜가_다르다"
        ),
        pytest.param("2026-10-07-01-hooks.md", "2026-10-07-05", "2026-10-07-05", id="둘_이상_앞"),
    ],
)
def test_다음_빈_번호와_다르면_그_번호를_알린다(파일: str, 다음: str, 새_번호: str) -> None:
    """날짜를 넘긴 세션이 시작한 날짜로 쓴 일지(일지 2026-10-12-05)와, 이름순으로 뒤인 형제의 일지를
    두고 앞 번호를 고른 일지. 둘 다 도구의 옮길 번호에는 들지 않는다."""
    key = 파일[:13]
    context = number_context(f"C:\\x\\docs\\journal\\{파일}", Overlap(0, _output(다음, key), ""))

    assert context is not None
    assert context.startswith(NUMBER_LEAD)
    assert 새_번호 in context
    assert "--move" not in context


def test_이미_있는_순번은_새_번호에_없어_다음_빈_번호를_알린다() -> None:
    """merge-base 나 main 에 같은 순번의 일지가 있으면 도구는 만든 파일을 새 일지로 세지 않는다.
    그래서 다음 빈 번호가 마침 그 바로 다음이 된다(실제 도구로 돌린 아래 테스트가 잡았다)."""
    output = _output("2026-10-07-04", None)

    context = number_context("C:\\x\\docs\\journal\\2026-10-07-03-hooks.md", Overlap(0, output, ""))

    assert context is not None
    assert "2026-10-07-04" in context
    assert "--move" not in context


def test_못_보는_것_빈_사이를_건너뛴_큰_순번은_지나간다() -> None:
    """만든 파일이 그 날짜의 가장 큰 순번이면, 그 앞이 비었는지 도구의 출력으로는 가를 수 없다."""
    name = "C:\\x\\docs\\journal\\2026-10-07-09-hooks.md"

    assert number_context(name, Overlap(0, _output("2026-10-07-10", "2026-10-07-09"), "")) is None


def test_순번_꼴이_아닌_일지_이름은_다음_빈_번호를_알린다() -> None:
    context = number_context(
        "C:\\x\\docs\\journal\\notes.md", Overlap(0, _output("2026-10-07-04", None), "")
    )

    assert context is not None
    assert context.startswith(NUMBER_LEAD)
    assert "2026-10-07-04" in context


@pytest.mark.parametrize(
    ("대조", "조각"),
    [
        pytest.param(None, "띄우지 못했거나", id="띄우지_못함"),
        pytest.param(
            Overlap(2, "", "형제를 대조하지 못했다. git fetch\n할 일: …\n"),
            "git fetch",
            id="종료_2",
        ),
        pytest.param(Overlap(0, "번호 겹침 없음\n", ""), "읽지 못했다", id="다음_줄_없음"),
        pytest.param(
            Overlap(0, "다음 빈 번호(형제 포함): 일지 2026-10-07-04, 대기열 281\n", ""),
            "읽지 못했다",
            id="새_번호_줄_없음",
        ),
    ],
)
def test_대조하지_못하면_손으로_치라는_계기를_낸다(대조: Overlap | None, 조각: str) -> None:
    """번호를 대 보지 못한 채 침묵하면 훅이 없던 때와 같다. 실패를 알리고 칠 명령을 준다."""
    context = number_context(NEW, 대조)

    assert context is not None
    assert "대 보지 못했다" in context
    assert 조각 in context
    assert "uv run python tools/sibling_overlap.py" in context


def _git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True, timeout=60)


def _today() -> date:
    return datetime.now().astimezone().date()


def _write_journal(folder: Path, day: date, number: str, slug: str) -> Path:
    journal = folder / "docs" / "journal" / f"{day.isoformat()}-{number}-{slug}.md"
    journal.write_text(f"# {day.isoformat()} ({number}) {slug}\n", encoding="utf-8")
    return journal


@pytest.mark.parametrize(
    ("하루_앞", "순번", "형제", "새_번호", "옮긴다"),
    [
        pytest.param(False, "02", None, None, False, id="다음_빈_번호"),
        pytest.param(False, "01", None, "02", False, id="main_에_있는_순번"),
        pytest.param(False, "02", "02", "03", True, id="형제_워크트리와_겹침"),
        pytest.param(True, "05", None, "02", True, id="main_의_최신_일지보다_앞선_날짜"),
    ],
)
def test_실제_도구의_출력을_읽어_순번을_가른다(
    tmp_path: Path, 하루_앞: bool, 순번: str, 형제: str | None, 새_번호: str | None, 옮긴다: bool
) -> None:
    """훅이 읽는 출력의 꼴(`다음 빈 번호`·`이 브랜치의 새 번호`·`옮길 번호` 줄)이 도구가 내는 꼴과
    같은지 본다. 형제는 커밋하지 않은 일지를 든 형제 워크트리다. 날짜를 넘긴 세션이 시작한 날짜로 쓴
    일지(일지 2026-10-12-05)는 main 의 오늘 일지보다 이름순으로 앞이다. 자식의 stdout 은 파일로
    받고 UTF-8 로 내게 하므로, 한글 줄이 깨지면 다음 빈 번호를 읽지 못해 실패 계기로 갈린다."""
    today = _today()
    repo = journal_repository(tmp_path, today.isoformat())
    if 형제 is not None:
        sibling = tmp_path / "sibling"
        _git("-C", str(repo), "worktree", "add", "-q", "-b", "chore/sibling", str(sibling), "main")
        _write_journal(sibling, today, 형제, "sibling")
    day = today - timedelta(days=1) if 하루_앞 else today
    journal = _write_journal(repo, day, 순번, "x")

    overlap = run_overlap(journal.parent)
    context = number_context(str(journal), overlap)

    assert overlap is not None, "도구를 띄우지 못했다"
    if 새_번호 is None:
        assert context is None, context
        return
    assert context is not None, overlap.stdout
    assert context.startswith(NUMBER_LEAD)
    assert f"{today.isoformat()}-{새_번호}" in context
    assert ("--move" in context) is 옮긴다


def test_못_보는_것_같은_순번의_새_일지_둘은_하나로_접혀_지나간다(tmp_path: Path) -> None:
    """거짓 음성이다. 도구가 순번을 열쇠로 읽어 둘이 하나로 접힌다. 같은 날의 순번 겹침은
    `tests/test_journal_names.py` 가 커밋 전에 본다."""
    today = _today()
    repo = journal_repository(tmp_path, today.isoformat())
    _write_journal(repo, today, "02", "a")
    journal = _write_journal(repo, today, "02", "x")

    assert number_context(str(journal), run_overlap(journal.parent)) is None


def test_대조_자식은_PYTHONUTF8_없이도_UTF8_로_낸다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """훅 환경에 `PYTHONUTF8` 이 있다고 가정하지 않는다(`.claude/rules/tools.md`)."""
    monkeypatch.delenv("PYTHONUTF8", raising=False)
    monkeypatch.delenv("PYTHONIOENCODING", raising=False)
    assert "PYTHONUTF8" not in os.environ
    repo = journal_repository(tmp_path, _today().isoformat())

    overlap = run_overlap(repo / "docs" / "journal")

    assert overlap is not None
    assert "다음 빈 번호(형제 포함)" in overlap.stdout
