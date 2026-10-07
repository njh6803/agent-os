"""tools/sibling_overlap.py 검증. 순수 함수와, 임시 원격·클론·워크트리로 만든 형제를 지나는 main.

임시 원격은 로컬 경로라 github.com 이 아니어서, main 은 `gh` 를 부르지 않고 merge ref 로 열린
PR 을 가린다. `gh api` 의 길은 `gh_listing` 을 바꿔 끼운 테스트 하나와 실제 실행(일지
2026-10-07-10)이 본다.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from tools.sibling_overlap import (
    Move,
    Numbers,
    clashes,
    fresh,
    gh_pulls,
    github_repo,
    main,
    moves,
    open_pulls,
    read_numbers,
    remote_head,
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
    """열 때부터 충돌한 PR 처럼 merge ref 가 없어도, gh 가 열려 있다고 하면 대조한다."""
    _, work, pusher = 저장소
    pr6 = _PR을_민다(pusher, 6, {"docs/adr/0002-pr.md": "그쪽\n"})
    _쓴다(work, {"docs/adr/0002-ours.md": "이쪽\n"})

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

    result = _CLI를_부른다(work)

    assert result.returncode == 1, result.stderr
    assert "origin/main ADR 0002: 이 브랜치 0002-ours.md, 그쪽 0002-main.md" in result.stdout
    # 새 main 위의 PR #9 는 main 의 번호를 되풀이하지 않는다
    assert result.stdout.count("ADR 0002:") == 1
    assert "옮길 번호: ADR 0002 → 0004\n" in result.stdout


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


def test_원격을_읽지_못하면_2로_끝나고_까닭을_알린다(
    저장소: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    _, work, _ = 저장소
    _git(work, "remote", "set-url", "origin", str(work.parent / "없는-원격.git"))

    code = main([str(work)])

    captured = capsys.readouterr()
    assert code == 2
    assert "ls-remote" in captured.err
