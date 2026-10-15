"""tools/sibling_overlap.py 검증. 순수 함수와, 임시 원격·클론·워크트리로 만든 형제를 지나는 main.

임시 원격은 로컬 경로라 github.com 이 아니어서, main 은 `gh` 를 부르지 않고 merge ref 로 열린
PR 을 가린다. `gh api` 의 길은 `gh_listing` 을 바꿔 끼운 테스트 하나와 실제 실행(일지
2026-10-07-10)이 본다.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

import pytest
from tools.sibling_overlap import (
    CONSTITUTION,
    JOURNAL_DIR,
    ON_FAILURE,
    ON_STUCK,
    QUEUE,
    Move,
    MoveError,
    MovePlan,
    Numbers,
    StuckMoveError,
    Survey,
    Verdict,
    apply_moves,
    behind_moves,
    canary_sources,
    clashes,
    closed_heads,
    dangling_cites,
    dangling_files,
    fresh,
    gh_pulls,
    github_repo,
    harness_files,
    highest_version,
    history_entries,
    is_behind,
    journal_day,
    main,
    moves,
    next_numbers,
    open_pulls,
    plan_moves,
    read_numbers,
    remote_head,
    renumber,
    reserved_version,
    rewrite,
    unbumped,
    uncanaried,
    unshared,
    vacating_first,
    worktrees,
)

from tools import sibling_overlap

TOOL = Path(__file__).resolve().parents[2] / "tools" / "sibling_overlap.py"
QUEUE_HEAD = "# 회고 반영 대기열\n\n| 번호 | 무엇 | 어디로 | 근거 |\n|---|---|---|---|\n"


def _번호(
    journals: dict[str, str] | None = None,
    adrs: dict[str, str] | None = None,
    rows: dict[int, str] | None = None,
    version: str | None = None,
) -> Numbers:
    return Numbers(journals or {}, adrs or {}, rows or {}, version)


def test_일지_ADR_대기열_헌법의_번호를_읽는다() -> None:
    numbers = read_numbers(
        ["2026-10-07-09-session-web-deps-hook.md", "2026-10-07-10-x.md"],
        ["0026-design-system.md", "README.md"],
        QUEUE_HEAD + "| 114 | 첫 줄 |\n| 115 | 둘째 줄 |\r\n",
        "**Version**: 3.0.18 | **Ratified**: 2026-09-19",
    )

    assert numbers.journals == {
        "2026-10-07-09": "2026-10-07-09-session-web-deps-hook.md",
        "2026-10-07-10": "2026-10-07-10-x.md",
    }
    assert numbers.adrs == {"0026": "0026-design-system.md"}
    assert numbers.rows == {114: "| 114 | 첫 줄 |", 115: "| 115 | 둘째 줄 |"}
    assert numbers.version == "3.0.18"


def test_규약_밖의_이름과_표의_머리는_번호가_아니다() -> None:
    numbers = read_numbers(
        ["2026-10-07-x.md", "README.md", "2026-10-07-09-a.txt"],
        ["README.md", "26-short.md"],
        QUEUE_HEAD + "본문 | 1 | 표가 아니다\n",
        "버전 없음",
    )

    assert numbers == _번호()


def test_새_번호는_아는_번호_어디에도_없는_것이다() -> None:
    theirs = _번호(
        {"2026-10-07-03": "2026-10-07-03-a.md", "2026-10-07-04": "2026-10-07-04-b.md"},
        {"0026": "0026-x.md", "0027": "0027-y.md"},
        {135: "| 135 | 가 |", 141: "| 141 | 나 |"},
        "3.0.17",
    )
    base = _번호({"2026-10-07-03": "2026-10-07-03-a.md"}, {"0026": "0026-x.md"}, {135: "| 135 |"})
    main_ = _번호({"2026-10-07-04": "2026-10-07-04-b.md"}, version="3.0.17")

    expected = _번호(adrs={"0027": "0027-y.md"}, rows={141: "| 141 | 나 |"})
    assert fresh(theirs, base, main_) == expected


def test_공유한_이력은_같은_번호에_같은_파일이나_같은_행이고_헌법_판은_가르지_않는다() -> None:
    ours = _번호(
        {"2026-10-07-05": "a.md", "2026-10-07-06": "ours.md"},
        {"0002": "0002-x.md"},
        {2: "| 2 | 같다 |", 3: "| 3 | 이쪽 |"},
        "1.0.1",
    )
    main_ = _번호(
        {"2026-10-07-05": "a.md", "2026-10-07-06": "main.md"},
        {"0002": "0002-x.md"},
        {2: "| 2 | 같다 |", 3: "| 3 | 그쪽 |"},
        "1.0.1",
    )

    expected = _번호({"2026-10-07-06": "ours.md"}, rows={3: "| 3 | 이쪽 |"}, version="1.0.1")
    assert unshared(ours, main_) == expected


def test_같은_번호에_다른_파일이나_다른_행이나_같은_판이면_겹침이다() -> None:
    ours = _번호(
        {"2026-10-07-10": "2026-10-07-10-ours.md"},
        {"0027": "0027-ours.md"},
        {141: "| 141 | 이 브랜치 |"},
        "3.0.19",
    )
    theirs = _번호(
        {"2026-10-07-10": "2026-10-07-10-theirs.md"},
        {"0027": "0027-theirs.md"},
        {141: "| 141 | 그쪽 |"},
        "3.0.19",
    )

    assert [(clash.kind, clash.key) for clash in clashes(ours, theirs)] == [
        ("일지", "2026-10-07-10"),
        ("ADR", "0027"),
        ("대기열", "141"),
        ("헌법", "3.0.19"),
    ]


def test_같은_파일과_같은_행과_다른_판은_겹침이_아니다() -> None:
    ours = _번호(
        {"2026-10-07-10": "2026-10-07-10-same.md"},
        {"0027": "0027-same.md"},
        {141: "| 141 | 같다 |"},
        "3.0.19",
    )
    theirs = _번호(
        {"2026-10-07-10": "2026-10-07-10-same.md", "2026-10-07-11": "2026-10-07-11-z.md"},
        {"0027": "0027-same.md"},
        {141: "| 141 | 같다 |", 142: "| 142 | 다르다 |"},
        "3.0.20",
    )

    assert clashes(ours, theirs) == []
    assert clashes(ours, _번호()) == []


def test_옮길_번호는_겹친_종류의_이_브랜치_새_번호_전부를_차례대로_형제_뒤에_붙인다() -> None:
    """일지 2026-10-07-09 의 실제 이동.

    이 브랜치 03~07·행 135~137, 열린 PR 03·135·136, main 04·137.
    """
    ours = _번호(
        {f"2026-10-07-0{n}": f"2026-10-07-0{n}-ours.md" for n in range(3, 8)},
        {"0027": "0027-ours.md"},
        {135: "a", 136: "b", 137: "c"},
        "3.0.18",
    )
    taken = [
        _번호({"2026-10-07-01": "x.md", "2026-10-07-02": "y.md", "2026-10-06-15": "z.md"}),
        _번호({"2026-10-07-03": "pr.md"}, rows={135: "p", 136: "q"}, version="3.0.17"),
        _번호({"2026-10-07-04": "main.md"}, {"0026": "a.md"}, {137: "m"}),
    ]
    found = clashes(ours, taken[1]) + clashes(ours, taken[2])

    assert moves(ours, taken, found) == [
        Move("일지", f"2026-10-07-0{old}", f"2026-10-07-0{old + 2}") for old in range(3, 8)
    ] + [Move("대기열", str(old), str(old + 3)) for old in (135, 136, 137)]


def test_옮길_번호는_자리가_그대로인_것을_빼고_ADR은_네_자리다() -> None:
    ours = _번호(adrs={"0002": "0002-ours.md", "0009": "0009-ours.md"})
    taken = [_번호(adrs={"0001": "a.md", "0002": "main.md", "0007": "b.md"})]

    assert moves(ours, taken, clashes(ours, taken[0])) == [Move("ADR", "0002", "0008")]


def test_다음_빈_일지는_그날의_가장_큰_순번_다음이고_대기열은_가장_큰_행_다음이다() -> None:
    """빈 사이 번호(02~06)는 고르지 않는다. 새 일지는 이름순으로 맨 뒤여야 한다."""
    numbers = [
        _번호(
            {"2026-10-12-01": "a.md", "2026-10-12-07": "b.md", "2026-10-13-02": "c.md"},
            rows={1: "x", 183: "y"},
        ),
        _번호({"2026-10-12-10": "d.md", "2026-10-11-20": "e.md"}, rows={182: "z"}),
    ]

    assert next_numbers(numbers, "2026-10-12") == ("2026-10-12-11", 184)
    assert next_numbers(numbers, "2026-10-14") == ("2026-10-14-01", 184)
    assert next_numbers([], "2026-10-12") == ("2026-10-12-01", 1)


def test_새_일지의_날짜는_오늘이되_main에_더_늦은_날짜의_일지가_있으면_그_날짜다() -> None:
    assert journal_day("2026-10-12", "2026-10-11-01") == "2026-10-12"
    assert journal_day("2026-10-12", "2026-10-13-02") == "2026-10-13"
    assert journal_day("2026-10-12", None) == "2026-10-12"


def test_새_일지_가운데_이름순_최신_것이_그쪽_최신_일지보다_앞이면_뒤처졌다() -> None:
    ours = _번호({"2026-10-07-20": "a.md", "2026-10-07-03": "b.md"})

    assert is_behind(ours, "2026-10-11-01")
    assert not is_behind(ours, "2026-10-07-20")  # 같은 순번은 겹침 대조가 본다
    assert not is_behind(ours, "2026-10-07-19")  # 03 이 앞이어도 최신 것(20)이 뒤다
    assert not is_behind(ours, None)
    assert not is_behind(_번호(), "2026-10-11-01")


def test_main보다_앞선_새_일지는_전부_그날의_형제_뒤로_옮긴다() -> None:
    """일지 2026-10-12-05 의 실제 이동(2026-10-07-20 을 닫는 날로)에 더 이른 새 일지를 더했다."""
    ours = _번호({"2026-10-07-20": "ours.md", "2026-10-07-03": "ours-early.md"})
    taken = [
        _번호({"2026-10-07-03": "pr.md", "2026-10-12-01": "x.md", "2026-10-12-04": "y.md"}),
        _번호({"2026-10-11-01": "main.md"}),
    ]

    assert behind_moves(ours, taken, "2026-10-12") == [
        Move("일지", "2026-10-07-03", "2026-10-12-05"),
        Move("일지", "2026-10-07-20", "2026-10-12-06"),
    ]


def test_GitHub_원격_URL에서_소유자와_저장소를_읽는다() -> None:
    assert github_repo("https://github.com/njh6803/agent-os") == ("njh6803", "agent-os")
    assert github_repo("https://github.com/njh6803/agent-os.git\n") == ("njh6803", "agent-os")
    assert github_repo("git@github.com:njh6803/agent-os.git") == ("njh6803", "agent-os")
    assert github_repo("/tmp/origin.git") is None
    assert github_repo("https://gitlab.com/a/b") is None


def test_gh_api_줄에서_열린_PR의_head를_읽는다() -> None:
    sha = "e358ad4daba191efbb550bf33cfba6018a17acaa"
    assert gh_pulls(f"158 {sha}\n\n잡음\n9 짧다\n") == {158: sha}


def test_열린_PR은_merge_ref가_있는_PR이다() -> None:
    listing = "\n".join(
        [
            "aaa\trefs/pull/157/head",
            "bbb\trefs/pull/158/head",
            "ccc\trefs/pull/158/merge",
            "ddd\trefs/pull/9/merge",
            "eee\trefs/heads/main",
        ]
    )

    assert open_pulls(listing) == {158: "bbb"}
    assert remote_head(listing, "main") == "eee"
    assert remote_head(listing, "topic") is None


def test_닫힌_PR은_head_ref가_있고_열린_PR이_아닌_것이다() -> None:
    """열린 PR 의 head 와 같은 커밋은 뺀다. 한 커밋을 head 로 든 닫힌 PR 이 여럿이면 큰 번호다."""
    listing = "\n".join(
        [
            "aaa\trefs/pull/157/head",
            "bbb\trefs/pull/158/head",
            "bbb\trefs/pull/158/merge",
            "bbb\trefs/pull/150/head",
            "ccc\trefs/pull/160/head",
            "ccc\trefs/pull/159/head",
            "ddd\trefs/pull/161/merge",
            "eee\trefs/heads/main",
            # ls-remote 와 gh api 사이에 head 가 움직인 열린 PR. 번호로 뺀다
            "ggg\trefs/pull/162/head",
        ]
    )

    assert closed_heads(listing, {158: "bbb", 162: "fff"}) == {"aaa": 157, "ccc": 160}


def test_가장_높은_헌법_판은_글자가_아니라_수로_견주고_그_판을_쓴_자리를_모두_든다() -> None:
    held = [("origin/main", "3.0.9"), ("PR #5", "3.0.10"), ("워크트리", None), ("PR #6", "3.0.10")]

    assert highest_version(held) == ("3.0.10", ["PR #5", "PR #6"])
    assert highest_version([("origin/main", "3.0.9"), ("PR #5", "2.10.0")]) == (
        "3.0.9",
        ["origin/main"],
    )
    assert highest_version([("PR #5", None)]) is None


def test_판을_올리지_않고_고친_헌법_파일은_원칙_스택_운영의_셋이다() -> None:
    """헌법 README(판 줄과 색인)와 셋 밖의 새 파일은 보지 않는다(못 보는 것)."""
    changed = frozenset(
        {
            "docs/constitution/operations.md",
            "docs/constitution/tech.md",
            "docs/constitution/README.md",
            "docs/constitution/new.md",
            "CLAUDE.md",
        }
    )

    assert unbumped(changed, _번호()) == [
        "docs/constitution/operations.md",
        "docs/constitution/tech.md",
    ]
    assert unbumped(changed, _번호(version="3.0.32")) == []
    principles = frozenset({"docs/constitution/principles.md"})
    assert unbumped(principles, _번호()) == ["docs/constitution/principles.md"]
    # 올림의 종류는 보지 않는다. 원칙을 바꾸고 patch 로 올려도 지나간다(못 보는 것)
    assert unbumped(principles, _번호(version="3.0.32")) == []
    readme_only = frozenset({"docs/constitution/README.md", "docs/constitution/new.md"})
    assert unbumped(readme_only, _번호()) == []


def test_워크트리_목록은_bare와_사라진_것을_빼고_경로와_HEAD를_준다() -> None:
    porcelain = "\n".join(
        [
            "worktree /repo",
            "HEAD 111",
            "branch refs/heads/main",
            "",
            "worktree /repo/.claude/worktrees/a",
            "HEAD 222",
            "detached",
            "",
            "worktree /repo/.claude/worktrees/gone",
            "HEAD 333",
            "branch refs/heads/gone",
            "prunable gitdir file points to non-existent location",
            "",
            "worktree /bare.git",
            "bare",
            "",
        ]
    )

    assert worktrees(porcelain) == [("/repo", "111"), ("/repo/.claude/worktrees/a", "222")]


def test_카나리아로_불러_보는_하네스_파일은_스킬_본문과_규칙과_서브에이전트다() -> None:
    """`CLAUDE.md`, 스킬 폴더의 `SKILL.md` 밖 파일, 훅 설정은 보지 않는다(못 보는 것)."""
    changed = [
        ".claude/skills/a/SKILL.md",
        ".claude/skills/a/notes.md",
        ".claude/skills/SKILL.md",
        ".claude/rules/tools.md",
        ".claude/agents/r.md",
        ".claude/settings.json",
        "CLAUDE.md",
        "docs/x.md",
    ]

    assert harness_files(changed) == [
        ".claude/agents/r.md",
        ".claude/rules/tools.md",
        ".claude/skills/a/SKILL.md",
    ]


def test_원천으로_든_카나리아_명세를_하나도_고치지_않은_하네스_파일만_알린다() -> None:
    """대기열 235. 못 보는 것: 같은 원천의 명세 하나만 고쳐도, 명세를 고친 뒤 하네스를 다시 고쳐도
    지나간다(둘 다 이 입력이다). 읽지 못한 명세는 원천이 없어 그것만 고쳐도 알린다."""
    skill, rule, agent = ".claude/skills/a/SKILL.md", ".claude/rules/r.md", ".claude/agents/b.md"
    specs: dict[str, str | None] = {
        "c/a1.toml": skill,
        "c/a2.toml": skill,
        "c/r.toml": rule,
        "c/broken.toml": None,
    }
    changed = frozenset({skill, rule, agent, "c/a2.toml", "c/broken.toml"})

    assert uncanaried([agent, rule, skill], changed, specs) == [
        (agent, []),
        (rule, ["c/r.toml"]),
    ]


def test_카나리아_명세의_원천을_읽고_읽지_못한_명세는_원천이_없다(tmp_path: Path) -> None:
    rule = ".claude/rules/x.md"
    _쓴다(
        tmp_path,
        {
            ".scratch/harness/probes/canary/a.toml": f'kind = "rule"\nsource = "{rule}"\n',
            ".scratch/design-refresh/probes/canary/b.toml": "source = [\n",
            ".scratch/harness/probes/canary/c.toml": "source = 3\n",
            ".scratch/harness/probes/other/d.toml": f'source = "{rule}"\n',
        },
    )

    assert canary_sources(tmp_path) == {
        ".scratch/design-refresh/probes/canary/b.toml": None,
        ".scratch/harness/probes/canary/a.toml": rule,
        ".scratch/harness/probes/canary/c.toml": None,
    }


# 아래 시험들이 없는 번호로 쓰는 일지 인용은 임시 저장소에는 없고 이 저장소에는 있는 번호다. 이
# 파일의 새 줄도 커밋 전의 이 도구가 대조한다(대기열 254)


def test_없는_일지_번호를_가리킨_인용을_나온_차례로_한_번씩_든다() -> None:
    """대기열 254: 짐작한 일지 번호를 카나리아 명세에 인용해 없는 일지를 가리킨 채 셀프 리뷰까지
    갔다(일지 2026-10-13-67). 목록 꼴(`·`)의 번호도 하나씩 본다."""
    text = (
        "일지 2026-10-07-05를 본다(일지 2026-10-07-01·2026-10-07-04)\r\n"
        "다시 일지 2026-10-07-05, 그리고 새 일지 2026-10-07-02\n"
    )

    # 있는 번호는 뜻이 다른 일지를 가리켜도 지나간다(못 보는 것)
    known = {"2026-10-07-01", "2026-10-07-02"}
    assert dangling_cites(text, known) == ["2026-10-07-05", "2026-10-07-04"]


def test_인용_블록과_코드와_merge_base나_main에_있던_줄의_일지_인용은_보지_않는다() -> None:
    """인용 블록은 사용자 프롬프트의 원문이고, 코드 스팬과 펜스는 옮기기 전의 옛 번호를 적은
    기록이나 도구의 출력이다. merge-base 나 main 의 판에 글자 그대로 있는 줄은 이 브랜치가 더한 줄이
    아니다. 펜스는 여는 줄과 같은 글자로 같거나 더 길게 닫고, 닫지 않으면 끝까지 간다."""
    text = (
        '> 사용자: "일지 2026-10-07-03의 다음부터"\n'
        "처음 받은 `일지 2026-10-07-04` 를 옮겼다\r\n"
        "````\n"
        "옮길 번호: 일지 2026-10-07-05 → 2026-10-07-06\n"
        "```\n"
        "일지 2026-10-07-03 은 더 짧은 펜스 줄 뒤에도 펜스 안이다\n"
        "````` 뒤에 글이 붙은 줄은 닫지 않는다\n"
        "~~~~\n"
        "일지 2026-10-07-07 은 아직 펜스 안이다\n"
        "`````\n"
        "옛 줄의 일지 2026-10-07-08\r\n"
        "~~~\n"
        "일지 2026-10-07-09\n"
    )

    assert dangling_cites(text, set(), frozenset({"옛 줄의 일지 2026-10-07-08"})) == []
    # 둘 줄이 아니면 펜스 밖의 같은 줄은 든다
    assert dangling_cites(text, set()) == ["2026-10-07-08"]


def test_낱말_없이_든_번호와_목록의_줄인_꼴은_보지_않고_시험_데이터의_번호는_든다() -> None:
    """못 보는 것. "일지" 낱말 없이 든 번호, 목록의 줄인 꼴(`·05`), 코드 스팬에 넣은 인용은
    지나간다. 거꾸로 일부러 없는 번호를 쓴 시험 데이터(문자열)도 인용으로 읽어 든다."""
    text = (
        "처음 2026-10-07-03 을 받았다. 일지 2026-10-07-01·05 를 본다. `일지 2026-10-07-04`\n"
        '    assert "일지 2026-10-07-06" in out\n'
    )

    assert dangling_cites(text, {"2026-10-07-01"}) == ["2026-10-07-06"]


def test_지운_파일과_UTF_8로_읽지_못하는_파일의_일지_인용은_보지_않는다(tmp_path: Path) -> None:
    """못 보는 것. 고친 파일 목록에 있어도 디스크에 없거나 글이 아니면 넘어간다. 줄을 가를 판이
    없으면 git 을 부르지 않는다."""
    (tmp_path / "a.md").write_bytes("일지 2026-10-07-05\n".encode("cp949"))
    _쓴다(tmp_path, {"b.md": "일지 2026-10-07-05\n"})

    found = dangling_files(tmp_path, (), ["a.md", "b.md", "gone.md"], {"2026-10-07-01"})

    assert found == [("b.md", ["2026-10-07-05"])]


RESERVED_MAIN = (
    "1.0.2는 스택의 문구다. 1.0.1은 함께 돌던 형제 브랜치(`topic`)가 먼저 매겨 비워 두었다."
    " 1.0.0은 처음이다."
)


def _이력(version: str, history: str) -> str:
    return _헌법(version) + f"\n{history}\n"


def test_main이_이_브랜치_몫으로_비워_둔_판에_이력_문단을_더했으면_그_판이다() -> None:
    """대기열 279: main 이 이 브랜치 몫으로 비워 둔 판(3.0.35)을 판 줄을 main 그대로 둔 이
    브랜치에서 알아보지 못해, 합칠 때마다 판을 올리지 않았다고 1로 끝났다(일지 2026-10-15-19). 이력
    문단은 판 머리(`<판>은`·`<판>는`)부터 다음 판 머리까지다."""
    main_text = _이력("1.0.2", RESERVED_MAIN)
    ours = _이력("1.0.2", RESERVED_MAIN.replace("1.0.0은", "1.0.1은 운영의 문구다. 1.0.0은"))

    assert reserved_version("topic", main_text, ours) == "1.0.1"
    # 다른 브랜치 몫이거나 분리 HEAD 면 올리지 않은 것이다
    assert reserved_version("other", main_text, ours) is None
    assert reserved_version(None, main_text, ours) is None
    # 그 판의 이력 문단을 더하지 않았으면 올리지 않은 것이다
    assert reserved_version("topic", main_text, main_text) is None
    # 비워 두지 않은 판에 더한 문단은 이 판정 밖이다(판 줄로 본다)
    other = _이력("1.0.2", RESERVED_MAIN.replace("1.0.0은", "1.0.3은 운영의 문구다. 1.0.0은"))
    assert reserved_version("topic", main_text, other) is None
    # 문단은 다음 판 머리에서 끝난다. 그 판의 문단이 main 에 이미 있으면 뒤의 문단만 고쳐도 더한
    # 것이 아니다
    done = RESERVED_MAIN.replace("1.0.0은", "1.0.1은 운영의 문구다. 1.0.0은")
    later = done.replace("처음이다", "처음의 판이다")
    assert reserved_version("topic", _이력("1.0.2", done), _이력("1.0.2", later)) is None
    # 둘 이상이면 가장 높은 판이다
    reserve = "1.0.3은 함께 돌던 형제 브랜치(`topic`)가 먼저 매겨 비워 두었다."
    twice = RESERVED_MAIN.replace("1.0.2는", f"1.0.4는 X다. {reserve} 1.0.2는")
    both = twice.replace("1.0.0은", "1.0.3은 A다. 1.0.1은 B다. 1.0.0은")
    assert reserved_version("topic", _이력("1.0.4", twice), _이력("1.0.4", both)) == "1.0.3"


def test_판_머리가_없는_README는_이력_문단도_비워_둔_판도_없다() -> None:
    """PR 직전 버그 축: 이 브랜치가 헌법 README 를 지웠거나 비우면 이력 문단을 가르다 ValueError 가
    나, 도구가 트레이스백과 함께 1(출력대로 고친다)로 끝났다."""
    assert history_entries("") == frozenset()
    assert reserved_version("topic", _이력("1.0.2", RESERVED_MAIN), "") is None


def test_비워_둔_문장_뒤에_이어진_다른_판의_본문만_고치면_더한_것이_아니다() -> None:
    """셀프 리뷰 표준 축: 헌법 README 에서 비워 둔 문장은 3.0.36 문단 중간에 끼어, 그 뒤의 3.0.36
    본문까지 한 문단으로 묶인다. 그 본문 한 낱말만 고쳐도 3.0.35 문단을 더한 것으로 셌다."""
    tail = "1.0.1은 함께 돌던 형제 브랜치(`topic`)가 먼저 매겨 비워 두었다. 1.0.2의 본문이 잇는다."
    main_text = _이력("1.0.2", f"1.0.2는 스택의 문구다. {tail} 1.0.0은 처음이다.")
    ours = main_text.replace("본문이 잇는다", "본문을 고쳤다")

    assert reserved_version("topic", main_text, ours) is None


def test_비워_둔_판은_그_꼴의_문장만_읽고_그_문장을_깨뜨려_고쳐도_더한_것으로_센다() -> None:
    """못 보는 것. 다른 꼴로 적은 예약은 읽지 않는다. 이 브랜치가 문단을 더하지 않고 비워 둔 문장을
    그 꼴이 깨지게 고쳐도 그 판의 문단을 더한 것으로 센다."""
    main_text = _이력("1.0.2", RESERVED_MAIN)
    reworded = _이력("1.0.2", RESERVED_MAIN.replace("먼저 매겨", "앞서 매겨"))

    assert reserved_version("topic", main_text, reworded) == "1.0.1"
    loose = _이력("1.0.2", "1.0.2는 스택의 문구다. 1.0.1은 형제 `topic` 몫으로 비웠다.")
    ours = loose.replace("1.0.1은 형제", "1.0.1은 운영의 문구다. 1.0.1은 형제")
    assert reserved_version("topic", loose, ours) is None


def test_옮길_번호대로_인용을_한_번에_바꾼다() -> None:
    """대기열 249. 차례대로 옮기는 사슬(03→05, 05→07)도 한 번에 바꿔 03 이 07 까지 가지 않는다."""
    plan = renumber(
        [
            Move("일지", "2026-10-07-03", "2026-10-07-05"),
            Move("일지", "2026-10-07-05", "2026-10-07-07"),
            Move("ADR", "0027", "0028"),
            Move("대기열", "135", "137"),
            Move("대기열", "136", "138"),
        ]
    )
    text = (
        "# 2026-10-07 (03) 제목\n"
        "일지 2026-10-07-03·2026-10-07-05, docs/journal/2026-10-07-05-b.md\r\n"
        "ADR 0027·0026, [0027](0027-x.md), docs/adr/0027-x.md\n"
        "(대기열 135·48·136, 대기열 136의 2회차)\n"
        "| 135 | 행 |\n"
    )
    expected = (
        "# 2026-10-07 (05) 제목\n"
        "일지 2026-10-07-05·2026-10-07-07, docs/journal/2026-10-07-07-b.md\r\n"
        "ADR 0028·0026, [0028](0028-x.md), docs/adr/0028-x.md\n"
        "(대기열 137·48·138, 대기열 138의 2회차)\n"
        "| 135 | 행 |\n"
    )

    assert rewrite(text, plan, "docs/journal/2026-10-07-03-a.md") == expected
    # 대기열 행의 머리는 대기열 파일에서만 바꾼다. 일지의 다른 표에도 `| 135 |` 꼴이 있다
    assert rewrite(text, plan, QUEUE) == expected.replace("| 135 |", "| 137 |")
    # 더 긴 수의 일부는 번호가 아니다
    longer = "2026-10-07-031, 대기열 1350, ADR 00271, 10027-x, v1.0027-x\n"
    assert rewrite(longer, plan, QUEUE) == longer


def test_인용_블록의_줄은_원문이라_옮기지_않는다() -> None:
    """일지는 사용자 프롬프트를 원문으로 인용한다(`> 사용자:`). 이 브랜치를 옮긴 첫 `--move` 가 그
    원문의 일지 번호를 새 번호로 바꿨다(일지 2026-10-15-15). 못 보는 것: `>` 없이 이어지는 줄은
    인용 블록이어도 옮긴다."""
    plan = renumber([Move("일지", "2026-10-07-03", "2026-10-07-05"), Move("대기열", "2", "3")])
    text = (
        '> 사용자: "일지 2026-10-07-03의 다음부터, 대기열 2를 닫는다"\n'
        "> 2026-10-07-03\n"
        "이어지는 줄 2026-10-07-03\n"
        "본문의 일지 2026-10-07-03, 인용 > 2026-10-07-03\n"
    )

    assert rewrite(text, plan, "docs/journal/2026-10-07-03-a.md") == (
        '> 사용자: "일지 2026-10-07-03의 다음부터, 대기열 2를 닫는다"\n'
        "> 2026-10-07-03\n"
        "이어지는 줄 2026-10-07-05\n"
        "본문의 일지 2026-10-07-05, 인용 > 2026-10-07-05\n"
    )


def test_줄인_인용과_조사는_옮기지_않고_같은_꼴이면_다른_뜻도_옮긴다() -> None:
    """못 보는 것. 줄인 꼴("일지 03"), 낱말 없이 든 번호, 번호 뒤의 조사는 그대로다. 같은 꼴이면
    형제의 같은 번호를 가리킨 인용도 이 브랜치의 번호로 읽어 옮긴다."""
    plan = renumber([Move("일지", "2026-10-07-03", "2026-10-07-05"), Move("대기열", "2", "3")])
    text = "일지 03, 새로 연 것은 2·5다. 대기열 2를 연다. 형제의 일지 2026-10-07-03 과 겹쳤다\n"

    assert rewrite(text, plan, "docs/journal/2026-10-07-03-a.md") == (
        "일지 03, 새로 연 것은 2·5다. 대기열 3를 연다. 형제의 일지 2026-10-07-05 과 겹쳤다\n"
    )


def test_옮기기는_코드_스팬과_펜스_안의_같은_꼴도_옮긴다() -> None:
    """못 보는 것. 파일 이름 인용(`docs/journal/…`)이 대개 코드 스팬 안에 있어 그 자리도 옮긴다.
    그래서 없는 일지 인용 판정이 기록의 자리로 안내한 코드 스팬 안의 이 브랜치 번호도 옮긴다."""
    plan = renumber([Move("일지", "2026-10-07-03", "2026-10-07-05")])
    text = "`docs/journal/2026-10-07-03-a.md`, 처음 `일지 2026-10-07-03`\n```\n2026-10-07-03\n```\n"

    assert rewrite(text, plan, "docs/journal/2026-10-07-03-a.md") == (
        "`docs/journal/2026-10-07-05-a.md`, 처음 `일지 2026-10-07-05`\n```\n2026-10-07-05\n```\n"
    )


def test_옮기기는_이_브랜치가_고친_글만_고치고_이름을_바꾸며_자리가_차_있으면_멈춘다(
    tmp_path: Path,
) -> None:
    journal = "docs/journal/2026-10-07-03-ours.md"
    files = {
        # 줄 끝은 바이트 그대로 둔다(`write_text` 는 윈도에서 줄 끝을 바꿔 바이트로 쓴다)
        journal: "# 2026-10-07 (03) 이쪽\r\nADR 0002, 대기열 2\r\n",
        "docs/adr/0002-ours.md": "번호 없는 글\n",
        ".scratch/retro-queue.md": "| 1 | 씨앗 |\n| 2 | 이쪽 |\n",
        # 둘 줄(`kept`)을 주지 않으면 merge-base 에 있던 줄도 옮긴다. CLI 는 merge-base 와 main 의
        # 줄을 준다
        "docs/notes.md": "merge-base 에 있던 줄의 대기열 2\n이 브랜치가 더한 줄\n",
        "README.md": "대기열 2\n",
    }
    for name, text in files.items():
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_bytes(text.encode("utf-8"))
    binary = b"\xff\xfe" + "대기열 2".encode()  # UTF-8 이 아니라 인용 꼴이 있어도 두는 파일
    (tmp_path / "logo.png").write_bytes(binary)
    ours = _번호({"2026-10-07-03": "2026-10-07-03-ours.md"}, {"0002": "0002-ours.md"}, {2: "x"})
    shifted = [
        Move("일지", "2026-10-07-03", "2026-10-07-04"),
        Move("ADR", "0002", "0003"),
        Move("대기열", "2", "3"),
    ]
    changed = [
        journal,
        "docs/adr/0002-ours.md",
        ".scratch/retro-queue.md",
        "docs/notes.md",
        "logo.png",
        "gone.md",
    ]

    plan = plan_moves(tmp_path, ours, shifted, changed)

    assert plan.renames == [
        (journal, "docs/journal/2026-10-07-04-ours.md"),
        ("docs/adr/0002-ours.md", "docs/adr/0003-ours.md"),
    ]
    moved_text = "# 2026-10-07 (04) 이쪽\r\nADR 0003, 대기열 3\r\n"
    assert plan.texts == {
        journal: moved_text,
        ".scratch/retro-queue.md": "| 1 | 씨앗 |\n| 3 | 이쪽 |\n",
        "docs/notes.md": "merge-base 에 있던 줄의 대기열 3\n이 브랜치가 더한 줄\n",
    }
    assert plan.originals == {path: files[path].encode() for path in plan.texts}

    apply_moves(tmp_path, plan)

    assert not (tmp_path / journal).exists()
    moved = tmp_path / "docs/journal/2026-10-07-04-ours.md"
    assert moved.read_bytes() == moved_text.encode("utf-8")
    assert (tmp_path / "docs/adr/0003-ours.md").read_bytes() == "번호 없는 글\n".encode()
    assert (tmp_path / "README.md").read_bytes() == "대기열 2\n".encode()
    assert (tmp_path / "logo.png").read_bytes() == binary

    blocked = _번호(adrs={"0003": "0003-ours.md"})
    (tmp_path / "docs/adr/0004-ours.md").mkdir()
    with pytest.raises(MoveError, match="docs/adr/0004-ours.md"):
        plan_moves(tmp_path, blocked, [Move("ADR", "0003", "0004")], ["docs/adr/0003-ours.md"])


def test_옮길_자리가_다른_옮길_파일이면_그_파일을_먼저_옮긴다(tmp_path: Path) -> None:
    """반박 검증(일지 2026-10-15-15): 같은 슬러그의 사슬 02-x, 03-x 를 03, 04 로 옮길 때 03-x 를
    "이미 무엇이 있다" 로 거절했다."""
    journals = {f"2026-10-07-0{n}": f"2026-10-07-0{n}-x.md" for n in (2, 3)}
    for name in journals.values():
        (tmp_path / JOURNAL_DIR).mkdir(parents=True, exist_ok=True)
        (tmp_path / JOURNAL_DIR / name).write_bytes(f"# {name}\n".encode())
    shifted = [
        Move("일지", "2026-10-07-02", "2026-10-07-03"),
        Move("일지", "2026-10-07-03", "2026-10-07-04"),
    ]

    plan = plan_moves(tmp_path, _번호(journals), shifted, [])

    assert plan.renames == [
        (f"{JOURNAL_DIR}/2026-10-07-03-x.md", f"{JOURNAL_DIR}/2026-10-07-04-x.md"),
        (f"{JOURNAL_DIR}/2026-10-07-02-x.md", f"{JOURNAL_DIR}/2026-10-07-03-x.md"),
    ]

    apply_moves(tmp_path, plan)

    assert sorted(path.name for path in (tmp_path / JOURNAL_DIR).iterdir()) == [
        "2026-10-07-03-x.md",
        "2026-10-07-04-x.md",
    ]
    first = (tmp_path / JOURNAL_DIR / "2026-10-07-03-x.md").read_bytes()
    assert first == b"# 2026-10-07-02-x.md\n"
    # 순환은 옮김에서 나오지 않지만, 들어오면 끝나지 않는 대신 멈춘다
    with pytest.raises(MoveError, match="서로 자리를 맞바꾸는"):
        vacating_first([("a.md", "b.md"), ("b.md", "a.md")])


def test_심볼릭_링크는_따라가_쓰지_않는다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """반박 검증(일지 2026-10-15-15): 이 브랜치의 변경에 든 링크를 따라가 저장소 밖의 파일을 고쳤다.

    링크를 만드는 권한이 없는 윈도에서도 돌도록 `is_symlink` 를 바꿔 끼운다.
    """
    (tmp_path / "link.md").write_bytes("대기열 2\n".encode())
    (tmp_path / "plain.md").write_bytes("대기열 2\n".encode())
    real = Path.is_symlink

    def 링크다(self: Path) -> bool:
        return self.name == "link.md" or real(self)

    monkeypatch.setattr(Path, "is_symlink", 링크다)

    plan = plan_moves(tmp_path, _번호(), [Move("대기열", "2", "3")], ["link.md", "plain.md"])

    assert list(plan.texts) == ["plain.md"]


def _옮길_파일들(root: Path) -> MovePlan:
    """옛 글 둘을 고치고 이름 둘을 바꾸는 계획. 둘째 이름은 없는 폴더로 가 바꾸다 멈춘다."""
    for name in ("a.md", "b.md"):
        (root / name).write_bytes(f"{name} 의 옛 글\r\n".encode())
    return MovePlan(
        renames=[("a.md", "a2.md"), ("b.md", "없는-폴더/b2.md")],
        texts={"a.md": "a 의 새 글\n", "b.md": "b 의 새 글\n"},
        originals={name: f"{name} 의 옛 글\r\n".encode() for name in ("a.md", "b.md")},
    )


def test_옮기다_멈추면_고친_것을_거꾸로_되돌린다(tmp_path: Path) -> None:
    """셀프 리뷰 표준 축의 Major: 되돌리지 않고 다시 치면 이미 옮긴 인용이 사슬을 따라 한 번 더
    옮겨진다."""
    plan = _옮길_파일들(tmp_path)

    with pytest.raises(MoveError, match="모두 되돌렸다") as raised:
        apply_moves(tmp_path, plan)

    assert not isinstance(raised.value, StuckMoveError)
    assert sorted(path.name for path in tmp_path.iterdir()) == ["a.md", "b.md"]
    for name in ("a.md", "b.md"):
        assert (tmp_path / name).read_bytes() == plan.originals[name]


def test_되돌리지_못하면_남은_것을_든다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """첫 이름 바꾸기만 되고 그 뒤의 이름 바꾸기(되돌리기 포함)가 모두 실패하는 디스크."""
    plan = _옮길_파일들(tmp_path)
    real = Path.rename
    calls: list[str] = []

    def 처음만_된다(self: Path, target: Path) -> Path:
        calls.append(self.name)
        if len(calls) > 1:
            raise PermissionError(f"{self.name} 을 쥔 프로세스가 있다")
        return real(self, target)

    monkeypatch.setattr(Path, "rename", 처음만_된다)

    with pytest.raises(StuckMoveError) as raised:
        apply_moves(tmp_path, plan)

    # a.md 는 a2.md 에서 돌아오지 못했고 그 글도 되쓰지 않았다(옛 이름에 쓰면 사본이 생긴다)
    assert "a2.md → a.md" in str(raised.value) and ", a.md" in str(raised.value)
    assert not (tmp_path / "a.md").exists()
    assert (tmp_path / "a2.md").read_bytes() == "a 의 새 글\n".encode()
    assert (tmp_path / "b.md").read_bytes() == plan.originals["b.md"]


def test_되돌리지_못한_파일의_옛_자리에_다른_것이_있어도_덮지_않는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """옛 자리가 비었으면 읽기가 실패해 되쓰지 않지만, 같은 슬러그의 사슬에서는 다른 옮길 파일이
    그 자리에 있을 수 있다. 그 위에 옛 바이트를 쓰면 남의 글을 덮는다."""
    plan = _옮길_파일들(tmp_path)
    real = Path.rename
    calls: list[str] = []
    other = "a.md 자리에 든 다른 파일\n".encode()

    def 처음만_되고_옛_자리가_찬다(self: Path, target: Path) -> Path:
        calls.append(self.name)
        if len(calls) > 1:
            if self.name == "a2.md":
                (tmp_path / "a.md").write_bytes(other)
            raise PermissionError(f"{self.name} 을 쥔 프로세스가 있다")
        return real(self, target)

    monkeypatch.setattr(Path, "rename", 처음만_되고_옛_자리가_찬다)

    with pytest.raises(StuckMoveError):
        apply_moves(tmp_path, plan)

    assert (tmp_path / "a.md").read_bytes() == other
    assert (tmp_path / "a2.md").read_bytes() == "a 의 새 글\n".encode()


def test_쓰다_멈춘_파일도_옛_바이트로_되돌린다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """PR 직전 버그 축의 Major: `write_bytes` 는 파일을 먼저 비우고 쓰는데, 쓰기를 마친 파일만
    되돌려 쓰다 멈춘 파일은 잘린 채 남고 "모두 되돌렸다" 로 끝났다. 미추적 파일이면 git 으로도
    되돌릴 수 없다."""
    plan = _옮길_파일들(tmp_path)
    real = Path.write_bytes
    failed: list[str] = []

    def b_는_쓰다_멈춘다(self: Path, data: bytes) -> int:
        if self.name == "b.md" and not failed:
            failed.append(self.name)
            real(self, data[:2])
            raise OSError(28, "디스크가 찼다")
        return real(self, data)

    monkeypatch.setattr(Path, "write_bytes", b_는_쓰다_멈춘다)

    with pytest.raises(MoveError, match="모두 되돌렸다") as raised:
        apply_moves(tmp_path, plan)

    assert failed == ["b.md"]
    assert not isinstance(raised.value, StuckMoveError)
    for name in ("a.md", "b.md"):
        assert (tmp_path / name).read_bytes() == plan.originals[name]


def test_열지도_못한_파일은_되쓰지_않아_남은_것으로_들지_않는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """쓰기 전에 되돌릴 목록에 올리므로, 열지도 못한 파일(그대로다)을 되쓰다 또 실패해 되돌리지
    못한 것으로 들면 안 된다."""
    plan = _옮길_파일들(tmp_path)
    real = Path.write_bytes

    def b_는_열지_못한다(self: Path, data: bytes) -> int:
        if self.name == "b.md":
            raise PermissionError("b.md 를 쥔 프로세스가 있다")
        return real(self, data)

    monkeypatch.setattr(Path, "write_bytes", b_는_열지_못한다)

    with pytest.raises(MoveError, match="모두 되돌렸다") as raised:
        apply_moves(tmp_path, plan)

    assert not isinstance(raised.value, StuckMoveError)
    for name in ("a.md", "b.md"):
        assert (tmp_path / name).read_bytes() == plan.originals[name]


def test_BOM으로_시작하는_일지도_머리_줄을_옮기고_BOM을_지킨다() -> None:
    """PR 직전 버그 축: BOM 이 `^` 를 막아 파일 이름과 본문 인용은 옮기고 머리 줄만 옛 번호에
    남았다."""
    plan = renumber([Move("일지", "2026-10-07-03", "2026-10-07-05")])
    bom = chr(0xFEFF)
    text = f"{bom}# 2026-10-07 (03) 제목\r\n2026-10-07-03\r\n"

    assert rewrite(text, plan, "docs/journal/2026-10-07-03-a.md") == (
        f"{bom}# 2026-10-07 (05) 제목\r\n2026-10-07-05\r\n"
    )


def test_merge_base나_main에_글자_그대로_있는_줄은_옮기지_않는다() -> None:
    """PR 직전 버그 축: main 을 합치다 같은 대기열 행 번호의 두 행을 남긴 채 옮기면 main 의 행
    머리와 색인 행까지 옮겨졌다. main 에 이미 있던 같은 번호의 참조는 상대를 가리킨다
    (`.claude/rules/adr.md`). 그 줄을 이 브랜치가 고쳤으면 글자가 달라져 옮긴다."""
    plan = renumber([Move("대기열", "256", "259"), Move("ADR", "0027", "0028")])
    main_row, main_index = "| 256 | main 의 행 |", "- [0027](0027-sibling.md) 형제"
    kept = frozenset({"| 255 | 씨앗 |", main_row, main_index})
    queue = f"| 255 | 씨앗 |\r\n{main_row}\r\n| 256 | 이쪽 행, ADR 0027 |\r\n"
    index = f"{main_index}\n- [0027](0027-ours.md) 이쪽\n- [0027](0027-sibling.md) 형제(고침)\n"

    assert rewrite(queue, plan, QUEUE, kept) == (
        f"| 255 | 씨앗 |\r\n{main_row}\r\n| 259 | 이쪽 행, ADR 0028 |\r\n"
    )
    assert rewrite(index, plan, "docs/adr/README.md", kept) == (
        f"{main_index}\n- [0028](0028-ours.md) 이쪽\n- [0028](0028-sibling.md) 형제(고침)\n"
    )


def test_되돌리지_못하면_move_를_다시_치지_말라고_한다(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def 멈춘다(start: Path, day: str) -> tuple[Survey, Verdict]:
        raise StuckMoveError("옮기다 멈췄고 되돌리지 못한 것이 있다: a2.md → a.md")

    monkeypatch.setattr(sibling_overlap, "_move_and_check", 멈춘다)

    code = main(["--move"], today=date(2026, 10, 7))

    err = capsys.readouterr().err
    assert code == 2
    assert "a2.md → a.md" in err
    assert ON_STUCK in err and ON_FAILURE not in err


# --- 임시 원격과 클론 ---------------------------------------------------------


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _쓴다(root: Path, files: dict[str, str]) -> None:
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _커밋한다(root: Path, files: dict[str, str], message: str) -> str:
    _쓴다(root, files)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", message)
    return _git(root, "rev-parse", "HEAD")


def _헌법(version: str) -> str:
    return f"# 헌법\n\n**Version**: {version} | **Ratified**: 2026-09-19\n"


SEED = {
    "docs/journal/2026-10-07-01-seed.md": "씨앗\n",
    "docs/adr/0001-seed.md": "씨앗\n",
    "docs/adr/README.md": "색인\n",
    ".scratch/retro-queue.md": QUEUE_HEAD + "| 1 | 씨앗 |\n",
    "docs/constitution/README.md": _헌법("1.0.0"),
    "docs/constitution/operations.md": "운영\n",
    "README.md": "읽어 보기\n",
    "CLAUDE.md": "지침\n",
}


def _원격과_클론(tmp_path: Path, seed: dict[str, str]) -> tuple[Path, Path, Path]:
    """(원격, 작업 클론, 원격에 밀어 넣는 다른 클론). 작업 클론은 씨앗 커밋의 `topic` 에 있다."""
    remote = tmp_path / "origin.git"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(remote))
    pusher = tmp_path / "pusher"
    _git(tmp_path, "clone", "-q", str(remote), str(pusher))
    _git(pusher, "checkout", "-q", "-b", "main")
    _커밋한다(pusher, seed, "씨앗")
    _git(pusher, "push", "-q", "origin", "main")
    work = tmp_path / "work"
    _git(tmp_path, "clone", "-q", str(remote), str(work))
    _git(work, "checkout", "-q", "-b", "topic")
    return remote, work, pusher


@pytest.fixture
def 저장소(tmp_path: Path) -> tuple[Path, Path, Path]:
    return _원격과_클론(tmp_path, SEED)


def _PR을_민다(pusher: Path, number: int, files: dict[str, str]) -> str:
    """origin/main 위에 커밋 하나를 지어 `refs/pull/<번호>/head` 로 민다. merge ref 는 없다."""
    _git(pusher, "checkout", "-q", "-b", f"pr{number}", "origin/main")
    sha = _커밋한다(pusher, files, f"PR {number}")
    _git(pusher, "push", "-q", "origin", f"{sha}:refs/pull/{number}/head")
    _git(pusher, "checkout", "-q", "main")
    return sha


def _연다(cwd: Path, number: int, sha: str) -> None:
    """GitHub 이 열린 PR 에 두는 merge ref 를 흉내 낸다. 판정에는 있는지만 쓰인다."""
    _git(cwd, "push", "-q", "origin", f"{sha}:refs/pull/{number}/merge")


def _워크트리의_PR을_민다(work: Path, name: str, number: int, files: dict[str, str]) -> Path:
    """origin/main 위의 형제 워크트리에 커밋해 `refs/pull/<번호>/head` 로 민다. merge ref 없이."""
    path = work.parent / name
    _git(work, "worktree", "add", "-q", "-b", name, str(path), "origin/main")
    sha = _커밋한다(path, files, f"PR {number}")
    _git(path, "push", "-q", "origin", f"{sha}:refs/pull/{number}/head")
    return path


def _CLI를_부른다(work: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), str(work)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_열린_PR과_겹치면_알리고_1로_끝나며_닫힌_PR은_보지_않는다(
    저장소: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    _, work, pusher = 저장소
    queue_pr = SEED[".scratch/retro-queue.md"] + "| 2 | 그쪽 행 |\n"
    pr5 = _PR을_민다(
        pusher,
        5,
        {
            "docs/journal/2026-10-07-02-pr.md": "그쪽\n",
            ".scratch/retro-queue.md": queue_pr,
            "docs/constitution/README.md": _헌법("1.0.1"),
            "CLAUDE.md": "그쪽 지침\n",
        },
    )
    _연다(pusher, 5, pr5)
    _PR을_민다(pusher, 4, {"docs/adr/0002-closed.md": "닫힘\n"})
    _쓴다(
        work,
        {
            "docs/journal/2026-10-07-02-ours.md": "이쪽\n",
            "docs/adr/0002-ours.md": "이쪽\n",
            ".scratch/retro-queue.md": SEED[".scratch/retro-queue.md"] + "| 2 | 이쪽 행 |\n",
            "docs/constitution/README.md": _헌법("1.0.1"),
            "CLAUDE.md": "이쪽 지침\n",
        },
    )

    code = main([str(work)])

    out = capsys.readouterr().out
    assert code == 1
    assert "열린 PR 을 읽은 길: merge ref" in out
    assert "이 브랜치의 새 번호: 일지 2026-10-07-02, ADR 0002, 대기열 2, 헌법 1.0.1" in out
    assert "PR #5 일지 2026-10-07-02" in out
    assert "2026-10-07-02-ours.md" in out and "2026-10-07-02-pr.md" in out
    assert "PR #5 대기열 2" in out
    assert "PR #5 헌법 1.0.1" in out
    assert "PR #4" not in out and "ADR 0002:" not in out
    assert "옮길 번호: 일지 2026-10-07-02 → 2026-10-07-03, 대기열 2 → 3\n" in out
    assert "PR #5: .scratch/retro-queue.md, CLAUDE.md, docs/constitution/README.md" in out


def test_gh_api가_읽은_열린_PR은_merge_ref가_없어도_형제다(
    저장소: tuple[Path, Path, Path],
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """열 때부터 충돌한 PR 처럼 merge ref 가 없어도, gh 가 열려 있다고 하면 대조한다.

    그 PR 의 head 에 선 형제 워크트리도 닫힌 PR 의 것으로 접지 않는다(대기열 194).
    """
    _, work, pusher = 저장소
    pr6 = _PR을_민다(pusher, 6, {"docs/adr/0002-pr.md": "그쪽\n", "README.md": "그쪽\n"})
    _쓴다(work, {"docs/adr/0002-ours.md": "이쪽\n", "README.md": "이쪽\n"})
    _git(work, "fetch", "-q", "origin", "refs/pull/6/head")
    sibling = work.parent / "pr6"
    _git(work, "worktree", "add", "-q", "-b", "pr6", str(sibling), pr6)

    def 깃허브다(url: str) -> tuple[str, str]:
        return ("o", "r")

    def gh_가_연다(root: Path, owner: str, repo: str) -> str:
        return f"6 {pr6}\n"

    monkeypatch.setattr(sibling_overlap, "github_repo", 깃허브다)
    monkeypatch.setattr(sibling_overlap, "gh_listing", gh_가_연다)

    code = main([str(work)])

    out = capsys.readouterr().out
    assert code == 1
    assert "열린 PR 을 읽은 길: gh api\n" in out
    assert "PR #6 ADR 0002: 이 브랜치 0002-ours.md, 그쪽 0002-pr.md" in out
    assert f"- 워크트리 {sibling.resolve()}: README.md\n" in out
    assert "닫힌 워크트리" not in out


def test_main이_이_브랜치_뒤에_들인_번호와_겹치면_CLI가_알린다(
    저장소: tuple[Path, Path, Path],
) -> None:
    _, work, pusher = 저장소
    _커밋한다(pusher, {"docs/adr/0002-main.md": "main\n"}, "main 이 나아간다")
    _git(pusher, "push", "-q", "origin", "main")
    pr9 = _PR을_민다(pusher, 9, {"docs/journal/2026-10-07-05-pr9.md": "새 main 위\n"})
    _연다(pusher, 9, pr9)
    _커밋한다(pusher, {"docs/adr/0003-main.md": "main\n"}, "main 이 PR #9 뒤로 더 나아간다")
    _git(pusher, "push", "-q", "origin", "main")
    _커밋한다(work, {"docs/adr/0002-ours.md": "이쪽\n"}, "이쪽")

    before = datetime.now().astimezone().date()
    result = _CLI를_부른다(work)
    after = datetime.now().astimezone().date()

    assert result.returncode == 1, result.stderr
    assert "origin/main ADR 0002: 이 브랜치 0002-ours.md, 그쪽 0002-main.md" in result.stdout
    # 새 main 위의 PR #9 는 main 의 번호를 되풀이하지 않는다
    assert result.stdout.count("ADR 0002:") == 1
    assert "옮길 번호: ADR 0002 → 0004\n" in result.stdout
    # 날짜를 주지 않으면 이 기계의 오늘이다(자정을 넘길 수 있어 앞뒤 둘). 임시 저장소에 그날 일지는
    # 없다
    lines = {f"다음 빈 번호(형제 포함): 일지 {day}-01, 대기열 2\n" for day in (before, after)}
    assert any(line in result.stdout for line in lines), result.stdout


def test_형제_워크트리의_커밋하지_않은_번호와_겹치면_알린다(
    저장소: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    _, work, _ = 저장소
    sibling = work.parent / "sibling"
    _git(work, "worktree", "add", "-q", "-b", "other", str(sibling), "origin/main")
    probe = ".scratch/새-프로브.md"  # 미추적이고, git 이 따옴표로 감싸는 이름이다
    _쓴다(sibling, {"docs/journal/2026-10-07-02-sibling.md": "형제\n", probe: "형제\n"})
    _쓴다(work, {"docs/journal/2026-10-07-02-ours.md": "이쪽\n", probe: "이쪽\n"})

    code = main([str(work)])

    out = capsys.readouterr().out
    assert code == 1
    assert f"워크트리 {sibling.resolve()} 일지 2026-10-07-02" in out
    assert f"워크트리 {sibling.resolve()}: {probe}\n" in out


def test_PR이_닫힌_형제_워크트리는_커밋하지_않은_변경만_견주고_형제_줄에서_접는다(
    저장소: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """대기열 194: squash 병합 뒤 남은 워크트리가 "함께 고친 파일" 을 채워 열린 PR 의 줄을 묻었다.

    임시 원격은 github.com 이 아니라 열린 PR 을 merge ref 로 가린다. 그래서 merge ref 없이 민 PR 이
    닫힌 PR 이다. 열 때부터 충돌해 merge ref 가 없는 열린 PR 의 워크트리도 접는다(못 보는 것).
    """
    _, work, pusher = 저장소
    _쓴다(work, {"README.md": "이쪽\n", "CLAUDE.md": "이쪽 지침\n"})
    merged = _워크트리의_PR을_민다(work, "merged", 3, {"README.md": "병합\n"})
    dirty = _워크트리의_PR을_민다(work, "dirty", 4, {"CLAUDE.md": "병합\n"})
    _쓴다(dirty, {"README.md": "커밋하지 않았다\n"})
    # 닫힌 PR 의 head 뒤에 커밋을 더한 워크트리는 접지 않는다. HEAD 가 같을 때만 접는다
    later = _워크트리의_PR을_민다(work, "later", 6, {"README.md": "닫힌 뒤\n"})
    _커밋한다(later, {"CLAUDE.md": "더 했다\n"}, "닫힌 뒤의 커밋")
    # head 까지 따라가지 않은 워크트리도 접지 않는다. 병합된 커밋이 나온다(못 보는 것)
    behind = _워크트리의_PR을_민다(work, "behind", 7, {"README.md": "앞 커밋\n"})
    pr7 = _커밋한다(behind, {"CLAUDE.md": "뒤 커밋\n"}, "PR 7 의 둘째 커밋")
    _git(behind, "push", "-q", "origin", f"+{pr7}:refs/pull/7/head")
    _git(behind, "reset", "-q", "--hard", "HEAD~1")
    pr5 = _PR을_민다(pusher, 5, {"README.md": "열림\n"})
    _연다(pusher, 5, pr5)

    code = main([str(work)])

    out = capsys.readouterr().out
    assert code == 0, out
    assert ", PR 이 닫힌 워크트리 2곳(커밋하지 않은 변경만 견준다)\n" in out
    assert str(merged.resolve()) not in out
    assert f"- 워크트리 {dirty.resolve()}(PR #4 닫힘): README.md\n" in out
    assert f"- 워크트리 {later.resolve()}: CLAUDE.md, README.md\n" in out
    assert f"- 워크트리 {behind.resolve()}: README.md\n" in out
    assert "- PR #5: README.md\n" in out


def test_PR이_닫힌_형제_워크트리의_번호는_접지_않고_대조한다(
    저장소: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """대기열 205 의 길: 받은 번호로 만든 일지 파일은 PR 이 닫힌 워크트리에 있어도 찬 번호다."""
    _, work, _ = 저장소
    closed = _워크트리의_PR을_민다(work, "closed", 3, {"README.md": "병합\n"})
    _쓴다(closed, {"docs/journal/2026-10-07-02-closed.md": "형제\n"})
    _쓴다(work, {"docs/journal/2026-10-07-02-ours.md": "이쪽\n"})

    code = main([str(work)], today=date(2026, 10, 7))

    out = capsys.readouterr().out
    assert code == 1, out
    assert f"워크트리 {closed.resolve()}(PR #3 닫힘) 일지 2026-10-07-02" in out


def test_형제가_쓴_가장_높은_헌법_판과_그_자리를_찍는다(
    저장소: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """대기열 199: 판을 올리기 전의 대조는 겹침을 못 알려, 올린 뒤에야 형제의 판과 겹친 것을 알았다.

    판은 고르지 않는다. 올림의 종류는 바뀐 내용이 정한다. 형제 워크트리는 커밋하지 않은 판도 본다.
    """
    _, work, pusher = 저장소
    pr5 = _PR을_민다(pusher, 5, {"docs/constitution/README.md": _헌법("1.0.10")})
    _연다(pusher, 5, pr5)
    sibling = work.parent / "sibling"
    _git(work, "worktree", "add", "-q", "-b", "other", str(sibling), "origin/main")
    _쓴다(sibling, {"docs/constitution/README.md": _헌법("1.0.9")})

    code = main([str(work)])

    out = capsys.readouterr().out
    assert code == 0, out
    assert "형제가 쓴 가장 높은 헌법 판: 1.0.10(PR #5). 판을 올리면 이보다 높게 고른다\n" in out

    _쓴다(sibling, {"docs/constitution/README.md": _헌법("1.1.0")})
    # 이 브랜치의 판이 형제의 판보다 낮아도 찍기만 한다(못 보는 것). 같은 판만 겹침이다
    _쓴다(work, {"docs/constitution/README.md": _헌법("1.0.11")})

    code = main([str(work)])

    out = capsys.readouterr().out
    assert code == 0, out
    assert f"형제가 쓴 가장 높은 헌법 판: 1.1.0(워크트리 {sibling.resolve()})." in out
    assert "이 브랜치의 새 번호: 헌법 1.0.11" in out


def test_헌법_파일을_고치고_판을_올리지_않으면_1로_끝나고_올리면_0이다(
    저장소: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """대기열 224: `operations.md` 를 고치고 판을 올리지 않은 것을 셀프 리뷰가 잡았다.

    헌법 파일은 어느 변경이든 판을 올린다(원칙 변경은 major, 절 추가는 minor, 문구 수정은 patch).
    """
    _, work, _ = 저장소
    _쓴다(work, {"docs/constitution/operations.md": "고친 운영\n"})

    code = main([str(work)])

    out = capsys.readouterr().out
    assert code == 1, out
    assert "번호 겹침 없음" in out
    unbumped_line = "헌법 파일을 고치고 판을 올리지 않았다: docs/constitution/operations.md."
    assert unbumped_line in out
    assert "옮길 번호" not in out

    _쓴다(work, {"docs/constitution/README.md": _헌법("1.0.1")})

    code = main([str(work)])

    out = capsys.readouterr().out
    assert code == 0, out
    assert "판을 올리지 않았다" not in out

    # 바꿨는지만 본다. merge-base 의 판보다 낮게 고쳐도 지나간다(못 보는 것)
    _쓴다(work, {"docs/constitution/README.md": _헌법("0.9.0")})

    code = main([str(work)])

    out = capsys.readouterr().out
    assert code == 0, out
    assert "판을 올리지 않았다" not in out


def test_이_브랜치에_새_번호가_없어도_형제를_넘은_다음_빈_번호를_찍는다(
    저장소: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """대기열 157·182 의 경위: 일지를 쓰기 전의 대조는 "새 번호 없음" 만 내 헛돌았다."""
    _, work, pusher = 저장소
    queue = SEED[".scratch/retro-queue.md"]
    pr5_files = {
        "docs/journal/2026-10-07-02-pr.md": "그쪽\n",
        ".scratch/retro-queue.md": queue + "| 2 | 그쪽 |\n",
    }
    pr5 = _PR을_민다(pusher, 5, pr5_files)
    _연다(pusher, 5, pr5)
    sibling = work.parent / "sibling"
    _git(work, "worktree", "add", "-q", "-b", "other", str(sibling), "origin/main")
    sibling_files = {
        "docs/journal/2026-10-07-03-sibling.md": "형제\n",
        ".scratch/retro-queue.md": queue + "| 3 | 형제 |\n",
    }
    _쓴다(sibling, sibling_files)

    code = main([str(work)], today=date(2026, 10, 7))

    out = capsys.readouterr().out
    assert code == 0
    assert "다음 빈 번호(형제 포함): 일지 2026-10-07-04, 대기열 4\n" in out
    assert "이 브랜치의 새 번호 없음" in out
    # 대기열 220: 번호를 받는 자리에서 바로 파일을 만들라고 한다. 그 안내가 next-session 에만 있었다
    reserve = "일지를 쓸 세션이면 다른 일보다 먼저 docs/journal/2026-10-07-04-<슬러그>.md 를"
    assert reserve in out
    # 2로 끝난 동안 스크래치에 둔 것은 번호를 받은 이 출력에서 옮기라고 한다(셀프 리뷰 명세 축)
    assert "2로 끝난 동안 스크래치 파일에 적어 둔 것이 있으면 만든 일지로 옮긴다" in out
    # 대기열 199: 판을 올리기 전에도 찍는다. 형제가 판을 올리지 않았으면 main 의 판이다
    assert "형제가 쓴 가장 높은 헌법 판: 1.0.0(origin/main)." in out

    # 받은 번호로 쓰면(next-session 1단계가 안내하는 길) 겹치지도 앞서지도 않는다
    ours_files = {
        "docs/journal/2026-10-07-04-ours.md": "이쪽\n",
        ".scratch/retro-queue.md": queue + "| 4 | 이쪽 |\n",
    }
    _쓴다(work, ours_files)

    code = main([str(work)], today=date(2026, 10, 7))

    out = capsys.readouterr().out
    assert code == 0, out
    assert "번호 겹침 없음" in out
    assert "앞서는 형제" not in out
    # 이 브랜치에 새 일지가 생기면 그 안내는 내지 않는다
    assert "일지를 쓸 세션이면" not in out


def test_새_일지가_main의_최신_일지보다_이름순으로_앞이면_1로_끝나고_닫는_날로_옮긴다(
    저장소: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """대기열 175 의 경위(일지 2026-10-12-05): 날짜를 넘긴 세션이 시작한 날짜로 일지를 썼다.

    이어서 main 을 들였으면 main 의 일지는 main 의 새 번호가 아니어도 견준다. 같은 일지가 열린
    PR 과도 겹치면 날짜 안의 겹침 이동은 내지 않는다. 내면 같은 일지를 두 자리로 옮기라고 한다.
    """
    _, work, pusher = 저장소
    _커밋한다(pusher, {"docs/journal/2026-10-11-01-main.md": "main\n"}, "main 이 나아간다")
    _git(pusher, "push", "-q", "origin", "main")
    _git(work, "pull", "-q", "--ff-only", "origin", "main")
    queue = SEED[".scratch/retro-queue.md"]
    ours_files = {
        "docs/journal/2026-10-07-20-ours.md": "이쪽\n",
        ".scratch/retro-queue.md": queue + "| 2 | 이쪽 |\n",
    }
    _쓴다(work, ours_files)

    code = main([str(work)], today=date(2026, 10, 12))

    # 겹침이 없어도 앞선 것만으로 1 이다
    out = capsys.readouterr().out
    assert code == 1
    assert "번호 겹침 없음" in out
    behind = "이 브랜치의 새 일지 2026-10-07-20 이 origin/main 의 최신 일지 2026-10-11-01 보다"
    assert behind + " 이름순으로 앞이다" in out
    assert "옮길 번호: 일지 2026-10-07-20 → 2026-10-12-01\n" in out
    assert "다음 빈 번호(형제 포함): 일지 2026-10-12-01, 대기열 3\n" in out

    # 새 main 위에 같은 일지·같은 대기열 행을 가진 PR 이 열린다
    pr9_files = {
        "docs/journal/2026-10-07-20-pr9.md": "그쪽\n",
        ".scratch/retro-queue.md": queue + "| 2 | 그쪽 |\n",
    }
    pr9 = _PR을_민다(pusher, 9, pr9_files)
    _연다(pusher, 9, pr9)

    code = main([str(work)], today=date(2026, 10, 12))

    out = capsys.readouterr().out
    assert code == 1
    assert "번호 겹침 2:" in out
    assert "옮길 번호: 일지 2026-10-07-20 → 2026-10-12-01, 대기열 2 → 3\n" in out
    # main 의 일지는 main 줄에만 나온다. 그 위의 PR #9 가 되풀이하지 않는다
    assert "앞서는 형제" not in out

    # "옮길 번호" 대로 옮기면(커밋 전 줄이 안내하는 길) 0 으로 끝난다
    (work / "docs/journal/2026-10-07-20-ours.md").unlink()
    moved = {
        "docs/journal/2026-10-12-01-ours.md": "이쪽\n",
        ".scratch/retro-queue.md": queue + "| 3 | 이쪽 |\n",
    }
    _쓴다(work, moved)

    code = main([str(work)], today=date(2026, 10, 12))

    out = capsys.readouterr().out
    assert code == 0, out
    assert "번호 겹침 없음" in out
    assert "최신 일지" not in out and "옮길 번호" not in out


def test_main에_같은_파일로_이미_든_일지는_새_일지가_아니다(
    저장소: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """쌓아 올린 아래 PR 이 squash 로 main 에 들어간 뒤 아직 main 을 들이지 않은 브랜치.

    아래 PR 의 일지·대기열 행은 merge-base 에 없어 이 브랜치의 새 번호로 읽히지만 main 과 같은
    파일·같은 행이라 공유한 이력이다. 새 일지로 세면 main 의 더 늦은 일지보다 앞이라며 1로 끝나고
    main 에 이미 있는 일지를 옮기라고 한다(PR 직전 버그 축).
    """
    _, work, pusher = 저장소
    queue = SEED[".scratch/retro-queue.md"] + "| 2 | 아래 PR |\n"
    below = {"docs/journal/2026-10-07-05-below.md": "아래\n", ".scratch/retro-queue.md": queue}
    _커밋한다(work, below, "아래 PR")
    _커밋한다(pusher, below, "아래 PR 을 squash 로 들인다")
    _커밋한다(pusher, {"docs/journal/2026-10-07-07-main.md": "main\n"}, "main 이 나아간다")
    _git(pusher, "push", "-q", "origin", "main")

    code = main([str(work)], today=date(2026, 10, 7))

    out = capsys.readouterr().out
    assert code == 0, out
    assert "이 브랜치의 새 번호 없음" in out
    assert "최신 일지" not in out and "옮길 번호" not in out
    assert "다음 빈 번호(형제 포함): 일지 2026-10-07-08, 대기열 3\n" in out


def test_열린_PR의_일지가_이름순으로_뒤면_알리기만_한다(
    저장소: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """그쪽이 먼저 병합되면 main 과의 대조가 잡으므로 종료 코드를 바꾸지 않는다."""
    _, work, pusher = 저장소
    pr8 = _PR을_민다(pusher, 8, {"docs/journal/2026-10-07-03-pr.md": "그쪽\n"})
    _연다(pusher, 8, pr8)
    queue = SEED[".scratch/retro-queue.md"] + "| 2 | 이쪽 |\n"
    _쓴다(work, {"docs/journal/2026-10-07-02-ours.md": "이쪽\n", ".scratch/retro-queue.md": queue})

    code = main([str(work)], today=date(2026, 10, 7))

    out = capsys.readouterr().out
    assert code == 0
    # 다음 빈 번호는 이 브랜치의 새 번호도 넘는다
    assert "다음 빈 번호(형제 포함): 일지 2026-10-07-04, 대기열 3\n" in out
    ahead = "이 브랜치의 새 일지 2026-10-07-02 를 이름순으로 앞서는 형제"
    ahead += "(그쪽이 먼저 병합되면 옮긴다, 종료 코드와 무관):\n"
    assert ahead + "- PR #8: 2026-10-07-03\n" in out
    assert "origin/main 의 최신 일지" not in out
    assert "옮길 번호" not in out


def test_이_브랜치의_PR과_겹치지_않는_PR은_번호_겹침이_아니고_0으로_끝난다(
    저장소: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    _, work, pusher = 저장소
    own = _커밋한다(work, {"docs/constitution/README.md": _헌법("1.0.1")}, "이쪽 PR")
    _git(work, "push", "-q", "origin", f"{own}:refs/pull/7/head")
    _연다(work, 7, own)
    _쓴다(work, {"docs/journal/2026-10-07-02-ours.md": "이쪽\n", "README.md": "이쪽\n"})
    pr8_files = {"docs/journal/2026-10-07-03-other.md": "그쪽\n", "README.md": "그쪽\n"}
    pr8 = _PR을_민다(pusher, 8, pr8_files)
    _연다(pusher, 8, pr8)

    code = main([str(work)])

    out = capsys.readouterr().out
    assert code == 0
    assert "번호 겹침 없음" in out
    assert "PR #7" not in out
    assert "PR #8: README.md" in out


def test_amend로_밀지_않은_이_브랜치의_PR은_형제가_아니다(
    저장소: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """원격 브랜치와 PR head 가 같고, 로컬은 amend 로 그 커밋을 버렸다(아직 강제 푸시 전)."""
    _, work, _ = 저장소
    own = _커밋한다(work, {"docs/constitution/README.md": _헌법("1.0.1")}, "이쪽 PR")
    _git(work, "push", "-q", "origin", "topic", f"{own}:refs/pull/7/head")
    _연다(work, 7, own)
    _git(work, "commit", "-q", "--amend", "-m", "이쪽 PR, 고친 메시지")

    code = main([str(work)])

    out = capsys.readouterr().out
    assert code == 0, out
    assert "PR #7" not in out


def test_얕은_클론에서_merge_base가_없는_PR은_고친_파일만_알_수_없다(
    저장소: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    remote, work, pusher = 저장소
    pr6 = _PR을_민다(pusher, 6, {"docs/journal/2026-10-07-02-pr.md": "그쪽\n"})
    _연다(pusher, 6, pr6)
    for n in range(3):
        _커밋한다(pusher, {"README.md": f"main {n}\n"}, f"main {n}")
    _git(pusher, "push", "-q", "origin", "main")
    shallow = work.parent / "shallow"
    _git(work.parent, "clone", "-q", "--depth", "1", f"file://{remote}", str(shallow))
    _git(shallow, "checkout", "-q", "-b", "topic")
    _쓴다(shallow, {"docs/journal/2026-10-07-02-ours.md": "이쪽\n"})

    code = main([str(shallow)])

    out = capsys.readouterr().out
    assert code == 1
    assert "PR #6 일지 2026-10-07-02" in out
    assert "- PR #6: 알 수 없다(merge-base 가 없다." in out


def test_merge_base에서_번호의_자리가_비면_2로_끝난다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    seed = {k: v for k, v in SEED.items() if k != "docs/constitution/README.md"}
    _, work, _ = _원격과_클론(tmp_path, seed)

    code = main([str(work)])

    captured = capsys.readouterr()
    assert code == 2
    assert "번호의 자리가 비었다: docs/constitution/README.md" in captured.err
    assert ON_FAILURE in captured.err


def test_원격을_읽지_못하면_2로_끝나고_까닭과_할_일을_알린다(
    저장소: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """대기열 251: 2일 때 할 일이 번호를 받는 두 스킬 가운데 하나에만 있었다."""
    _, work, _ = 저장소
    _git(work, "remote", "set-url", "origin", str(work.parent / "없는-원격.git"))

    code = main([str(work)])

    captured = capsys.readouterr()
    assert code == 2
    assert "ls-remote" in captured.err
    assert ON_FAILURE in captured.err
    assert "번호(일지 순번, ADR, 대기열 행, 헌법 판)를 손으로 고르지 않는다" in ON_FAILURE


@pytest.mark.parametrize("flag", ["-h", "--help"])
def test_도움말은_쓰임과_종료_코드를_찍고_0으로_끝난다(
    flag: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """대기열 251: `--help` 를 시작 경로로 읽어 "형제를 대조하지 못했다" 로 2를 냈다."""
    with pytest.raises(SystemExit) as raised:
        main([flag])

    captured = capsys.readouterr()
    assert raised.value.code == 0
    assert "--move" in captured.out and "종료 코드" in captured.out
    assert captured.err == ""


def test_도움말은_CLI에서도_0으로_끝난다() -> None:
    result = subprocess.run(
        [sys.executable, str(TOOL), "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        env={**os.environ, "PYTHONUTF8": "1"},
    )

    assert result.returncode == 0, result.stderr
    assert "uv run python tools/sibling_overlap.py" in result.stdout


def test_인자가_틀리면_2로_끝나고_할_일을_알린다(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        main(["--moev"])

    captured = capsys.readouterr()
    assert raised.value.code == 2
    assert "--moev" in captured.err
    assert ON_FAILURE in captured.err


CANARY = ".scratch/harness/probes/canary/x.toml"
SKILL = ".claude/skills/x/SKILL.md"


def test_바꾼_스킬의_카나리아_명세를_고치지_않으면_1로_끝나고_고치면_0이다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """대기열 235: `next-session` 을 바꾸고 카나리아를 돌리지 않은 채 셀프 리뷰 두 축과 PR 직전
    리뷰를 지났다(일지 2026-10-13-38)."""
    spec = f'kind = "skill"\nsource = "{SKILL}"\n'
    _, work, _ = _원격과_클론(tmp_path, {**SEED, SKILL: "옛 본문\n", CANARY: spec})
    _쓴다(work, {SKILL: "새 본문\n"})

    code = main([str(work)])

    out = capsys.readouterr().out
    assert code == 1, out
    assert "번호 겹침 없음" in out
    assert "카나리아 명세를 이 브랜치에서 고치지 않고 바꾼 하네스 파일" in out
    assert f"- {SKILL}: x.toml\n" in out
    # 계정 한도로 돌리지 못하는 갈래는 결과 줄을 고칠 수 없어, 이 알림이 남는다고 출력이 말한다
    assert "계정 한도로 돌리지 못하면 그 절의 계정 한도 항목대로 사전 확인만 돌리고" in out

    # 불러 본 뒤 명세의 최신 결과 줄을 고치면(operations.md 환경 규약 상세) 지나간다
    _쓴다(work, {CANARY: "# 최신 결과: 통과 4\n" + spec})

    code = main([str(work)])

    out = capsys.readouterr().out
    assert code == 0, out
    assert "카나리아 명세를" not in out

    # 지운 하네스 파일은 불러 볼 것이 없다
    _쓴다(work, {CANARY: spec})
    (work / SKILL).unlink()

    code = main([str(work)])

    out = capsys.readouterr().out
    assert code == 0, out
    assert "카나리아 명세를" not in out


def test_합치기를_커밋하기_전에도_main이_들여온_파일은_이_브랜치의_변경이_아니다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """main 을 합치다 충돌을 풀고 커밋하기 전에 친 대조가, merge-base 가 옛 자리라 main 이 고친
    규칙을 이 브랜치의 카나리아 누락으로, main 만 고친 파일을 함께 고친 파일로 알렸다(일지
    2026-10-15-15). 이 브랜치가 고친 스킬은 그대로 센다. 못 보는 것: 이 브랜치가 고쳤어도 main 과
    내용이 같아진 파일은 세지 않는다."""
    rule, same = ".claude/rules/x.md", ".claude/rules/y.md"
    spec = f'kind = "skill"\nsource = "{SKILL}"\n'
    seed = {**SEED, SKILL: "옛 본문\n", rule: "옛 규칙\n", same: "옛\n", CANARY: spec}
    _, work, pusher = _원격과_클론(tmp_path, seed)
    ours = {SKILL: "새 본문\n", "README.md": "이 브랜치\n", same: "같은 고침\n"}
    _커밋한다(work, ours, "이 브랜치")
    theirs = {rule: "main 의 규칙\n", "README.md": "main\n", "CLAUDE.md": "main\n"}
    _커밋한다(pusher, {**theirs, same: "같은 고침\n"}, "main")
    _git(pusher, "push", "-q", "origin", "main")
    _git(work, "fetch", "-q", "origin")
    with pytest.raises(subprocess.CalledProcessError):
        _git(work, "merge", "-q", "origin/main")  # README.md 가 충돌한다
    _쓴다(work, {"README.md": "둘 다\n"})
    _git(work, "add", "README.md")

    code = main([str(work)])

    out = capsys.readouterr().out
    assert code == 1, out
    assert f"- {SKILL}: x.toml\n" in out
    assert rule not in out
    assert same not in out
    assert "- origin/main: README.md\n" in out


def test_합치기를_커밋하기_전에도_main이_올린_헌법_판은_이_브랜치의_판이_아니다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """main 을 합치고 커밋하기 전에 친 대조가 main 이 올린 판을 이 브랜치의 새 판으로 읽어 main 과
    같은 판으로 겹쳤다고 1로 끝났다(일지 2026-10-15-15). 헌법 README 가 main 과 같으면 판은 main
    에서 들어온 것이다."""
    _, work, pusher = _원격과_클론(tmp_path, SEED)
    _커밋한다(work, {"README.md": "이 브랜치\n"}, "이 브랜치")
    _커밋한다(pusher, {"docs/constitution/README.md": _헌법("1.0.1")}, "main")
    _git(pusher, "push", "-q", "origin", "main")
    _git(work, "fetch", "-q", "origin")
    _git(work, "merge", "-q", "--no-commit", "--no-ff", "origin/main")

    code = main([str(work)])

    out = capsys.readouterr().out
    assert code == 0, out
    assert "이 브랜치의 새 번호 없음" in out
    assert "번호 겹침 없음" in out


def test_합치다_대기열_행이_겹쳐도_옮기기는_main의_행을_둔다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """PR 직전 버그 축: 양쪽이 같은 번호의 행을 더해 충돌을 풀고 두 행을 남긴 채 `--move` 를 치면
    main 의 행 머리까지 옮겨졌다. merge-base 와 main 의 판에 글자 그대로 있는 줄은 둔다."""
    queue = SEED[QUEUE]
    _, work, pusher = _원격과_클론(tmp_path, SEED)
    ours = {QUEUE: queue + "| 2 | 이쪽 |\n", "docs/notes.md": "대기열 2를 본다\n"}
    _커밋한다(work, ours, "이 브랜치")
    _커밋한다(pusher, {QUEUE: queue + "| 2 | main |\n"}, "main")
    _git(pusher, "push", "-q", "origin", "main")
    _git(work, "fetch", "-q", "origin")
    with pytest.raises(subprocess.CalledProcessError):
        _git(work, "merge", "-q", "origin/main")  # 대기열 끝이 충돌한다
    _쓴다(work, {QUEUE: queue + "| 2 | main |\n| 2 | 이쪽 |\n"})
    _git(work, "add", QUEUE)

    code = main([str(work), "--move"])

    out = capsys.readouterr().out
    assert code == 0, out
    assert "옮겼다: 대기열 2 → 3" in out
    assert (work / QUEUE).read_text(encoding="utf-8") == queue + "| 2 | main |\n| 3 | 이쪽 |\n"
    assert (work / "docs/notes.md").read_text(encoding="utf-8") == "대기열 3를 본다\n"


def test_옮기기를_고르면_옮길_번호대로_옮기고_다시_대조한다(
    저장소: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """대기열 249: 형제가 더 높은 번호를 들고 먼저 병합해 한 세션에서 번호를 두 번 옮기고, 그때마다
    인용(다섯에서 아홉)을 손으로 고쳤다(일지 2026-10-13-59·2026-10-13-61)."""
    _, work, pusher = 저장소
    queue = SEED[".scratch/retro-queue.md"]
    pr5_files = {
        "docs/journal/2026-10-07-02-pr.md": "# 2026-10-07 (02) 그쪽\n",
        ".scratch/retro-queue.md": queue + "| 2 | 그쪽 |\n",
    }
    pr5 = _PR을_민다(pusher, 5, pr5_files)
    _연다(pusher, 5, pr5)
    old = "docs/journal/2026-10-07-02-ours.md"
    _커밋한다(work, {old: "# 2026-10-07 (02) 이쪽\n\n대기열 2를 연다.\n"}, "일지")
    _쓴다(work, {".scratch/retro-queue.md": queue + "| 2 | 이쪽, 일지 2026-10-07-02 |\n"})

    code = main([str(work)], today=date(2026, 10, 7))

    out = capsys.readouterr().out
    assert code == 1, out
    assert "옮길 번호: 일지 2026-10-07-02 → 2026-10-07-03, 대기열 2 → 3\n" in out
    assert "`--move` 를 붙여 다시 치면" in out

    # 옮길 자리에 무엇이 있으면 아무것도 고치지 않고 2로 끝난다
    blocker = work / "docs/journal/2026-10-07-03-ours.md"
    blocker.mkdir()

    code = main([str(work), "--move"], today=date(2026, 10, 7))

    captured = capsys.readouterr()
    assert code == 2, captured.out
    assert "번호를 옮기지 못했다. 옮길 자리 docs/journal/2026-10-07-03-ours.md" in captured.err
    assert ON_FAILURE in captured.err
    journal_text = (work / old).read_text(encoding="utf-8")
    assert journal_text == "# 2026-10-07 (02) 이쪽\n\n대기열 2를 연다.\n"
    queue_text = (work / ".scratch/retro-queue.md").read_text(encoding="utf-8")
    assert queue_text == queue + "| 2 | 이쪽, 일지 2026-10-07-02 |\n"

    blocker.rmdir()

    code = main([str(work), "--move"], today=date(2026, 10, 7))

    out = capsys.readouterr().out
    assert code == 0, out
    assert out.startswith("옮겼다: 일지 2026-10-07-02 → 2026-10-07-03, 대기열 2 → 3.")
    renamed = f"이름을 바꾼 파일: {old} → docs/journal/2026-10-07-03-ours.md."
    assert renamed in out
    texts = "인용을 고친 파일: .scratch/retro-queue.md, docs/journal/2026-10-07-03-ours.md."
    assert texts in out
    assert "옛 이름의 지움까지 함께 스테이지한다(`git add -A`)" in out
    assert "번호 뒤의 조사는 옮기지 않았으니 손으로 본다" in out
    assert "번호 겹침 없음" in out and "옮길 번호" not in out
    assert not (work / old).exists()
    moved = (work / "docs/journal/2026-10-07-03-ours.md").read_text(encoding="utf-8")
    assert moved == "# 2026-10-07 (03) 이쪽\n\n대기열 3를 연다.\n"
    queue_text = (work / ".scratch/retro-queue.md").read_text(encoding="utf-8")
    assert queue_text == queue + "| 3 | 이쪽, 일지 2026-10-07-03 |\n"
    # 인덱스는 건드리지 않는다. 옛 일지가 인덱스에 남아도 대조는 작업 트리를 읽어 0이다(못 보는 것)
    assert old in _git(work, "ls-files")

    code = main([str(work), "--move"], today=date(2026, 10, 7))

    out = capsys.readouterr().out
    assert code == 0, out
    assert out.startswith("옮길 번호가 없어 옮기지 않았다\n")


def test_이_브랜치가_더한_줄의_일지_인용이_어디에도_없는_번호면_1로_끝난다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """대기열 254: `sibling_overlap.py` 를 치기 전에 짐작한 일지 번호를 인용했고 손으로 고쳤다(일지
    2026-10-13-66). main 에 있던 줄의 없는 번호는 이 브랜치가 더한 것이 아니라 알리지 않는다. 형제의
    일지는 커밋하지 않았어도 있는 번호다. 출력이 안내하는 길(다음 빈 번호로 일지 파일을 먼저
    만든다)을 밟으면 지나간다."""
    old = "옛 줄의 일지 2026-10-07-09\n"
    _, work, _ = _원격과_클론(tmp_path, {**SEED, "docs/notes.md": old})
    ours = "docs/journal/2026-10-07-02-ours.md"
    # 커밋 메시지의 인용은 보지 않는다(못 보는 것)
    journal = {ours: "# 2026-10-07 (02) 이쪽\n\n일지 2026-10-07-02를 쓴다\n"}
    _커밋한다(work, journal, "일지 2026-10-07-08 을 본다")
    _쓴다(work, {"docs/notes.md": old + "일지 2026-10-07-05와 일지 2026-10-07-01을 본다\n"})

    code = main([str(work)], today=date(2026, 10, 7))

    out = capsys.readouterr().out
    assert code == 1, out
    assert "번호 겹침 없음" in out
    assert "어디에도 없는 일지 번호를 가리킨 인용" in out
    assert "- docs/notes.md: 2026-10-07-05\n" in out
    assert "- docs/journal/" not in out
    assert "2026-10-07-08" not in out

    sibling = work.parent / "sibling"
    _git(work, "worktree", "add", "-q", "-b", "other", str(sibling), "origin/main")
    _쓴다(sibling, {"docs/journal/2026-10-07-05-sibling.md": "형제\n"})

    code = main([str(work)], today=date(2026, 10, 7))

    out = capsys.readouterr().out
    assert code == 0, out
    assert "어디에도 없는 일지" not in out
    assert "다음 빈 번호(형제 포함): 일지 2026-10-07-06," in out

    # 아직 만들지 않은 일지를 받은 번호로 먼저 인용하면 알리고, 그 번호로 파일을 만들면 지나간다
    notes = (work / "docs/notes.md").read_text(encoding="utf-8")
    _쓴다(work, {"docs/notes.md": notes + "다음은 일지 2026-10-07-06에 쓴다\n"})

    code = main([str(work)], today=date(2026, 10, 7))

    out = capsys.readouterr().out
    assert code == 1, out
    assert "- docs/notes.md: 2026-10-07-06\n" in out

    _쓴다(work, {"docs/journal/2026-10-07-06-next.md": "# 2026-10-07 (06) 다음\n"})

    code = main([str(work)], today=date(2026, 10, 7))

    out = capsys.readouterr().out
    assert code == 0, out
    assert "어디에도 없는 일지" not in out


def test_합치는_도중_main에서_들어온_줄의_일지_인용은_이_브랜치가_더한_줄이_아니다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """셀프 리뷰 명세 축: merge-base 에 없고 main 에만 있는 줄을 빼는 것을 고정한 시험이 없었다.
    main 을 합치다 충돌을 풀고 커밋하기 전에는 merge-base 가 옛 자리라, main 이 더한 줄이 이
    브랜치가 고친 파일에 섞인다."""
    _, work, pusher = _원격과_클론(tmp_path, SEED)
    _커밋한다(work, {"docs/notes.md": "이쪽\n"}, "이 브랜치")
    main_line = "main 이 옮겨 적은 옛 일지 2026-10-07-09\n"
    _커밋한다(pusher, {"docs/notes.md": main_line}, "main")
    _git(pusher, "push", "-q", "origin", "main")
    _git(work, "fetch", "-q", "origin")
    with pytest.raises(subprocess.CalledProcessError):
        _git(work, "merge", "-q", "origin/main")  # 둘 다 더한 docs/notes.md 가 충돌한다
    assert _git(work, "rev-parse", "-q", "--verify", "MERGE_HEAD")
    _쓴다(work, {"docs/notes.md": main_line + "이쪽\n"})
    _git(work, "add", "docs/notes.md")

    code = main([str(work)])

    out = capsys.readouterr().out
    assert code == 0, out
    assert "어디에도 없는 일지" not in out


def test_main이_이_브랜치_몫으로_비워_둔_헌법_판에_이력을_더했으면_판을_올린_것이다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """대기열 279: #243 이 3.0.35 를 이 브랜치 몫으로 비워 두었는데, 판 줄을 main 그대로 둔 이
    브랜치에 합칠 때마다 "헌법 파일을 고치고 판을 올리지 않았다" 로 1을 냈다(일지 2026-10-15-19).
    합치기를 커밋하기 전(판 줄이 main 과 같다)과 뒤(판 줄이 merge-base 와 같다)가 모두 그렇다."""
    seed = {**SEED, CONSTITUTION: _이력("1.0.0", "1.0.0은 처음이다.")}
    _, work, pusher = _원격과_클론(tmp_path, seed)
    ours = {
        "docs/constitution/operations.md": "고친 운영\n",
        CONSTITUTION: _이력("1.0.1", "1.0.1은 운영의 문구다. 1.0.0은 처음이다."),
    }
    _커밋한다(work, ours, "이 브랜치")
    _커밋한다(pusher, {CONSTITUTION: _이력("1.0.2", RESERVED_MAIN)}, "main")
    _git(pusher, "push", "-q", "origin", "main")
    _git(work, "fetch", "-q", "origin")
    with pytest.raises(subprocess.CalledProcessError):
        _git(work, "merge", "-q", "origin/main")  # 판 줄과 이력이 충돌한다
    assert _git(work, "rev-parse", "-q", "--verify", "MERGE_HEAD")
    merged = RESERVED_MAIN.replace("1.0.0은", "1.0.1은 운영의 문구다. 1.0.0은")
    _쓴다(work, {CONSTITUTION: _이력("1.0.2", merged)})
    _git(work, "add", CONSTITUTION)

    code = main([str(work)])

    out = capsys.readouterr().out
    assert code == 0, out
    assert "이 브랜치의 새 번호: 헌법 1.0.1\n" in out
    assert "올린 판으로 센 헌법 1.0.1: origin/main 의 이력이 이 브랜치 몫으로 비워 둔 판" in out
    assert "번호 겹침 없음" in out

    _git(work, "commit", "-q", "--no-edit")
    assert len(_git(work, "rev-list", "--parents", "-n", "1", "HEAD").split()) == 3  # 합치기 커밋

    code = main([str(work)])

    out = capsys.readouterr().out
    assert code == 0, out
    assert "판을 올리지 않았다" not in out
    assert "이 브랜치의 새 번호: 헌법 1.0.1\n" in out
