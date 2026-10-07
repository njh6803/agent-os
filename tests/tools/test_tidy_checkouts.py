"""tools/tidy_checkouts.py 의 판정과 삭제.

판정은 순수 함수로, 배관(`main`)은 임시 저장소의 실제 git 워크트리로 잰다. `gh` 와 잠금 pid 는
가짜로 준다. 윈도에서 다른 프로세스가 워크트리를 쥐었을 때의 실제 동작(이름 바꾸기가 막히는지,
git 이 지우다 만 폴더를 남기는지)은 CI(우분투)에서 재지 못해 `.scratch/harness/probes/
worktree_occupancy.py` 가 잰다. 여기서는 그 실패를 가짜 `rename`·`delete`·`git` 으로 넣는다.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

import pytest
from tools.tidy_checkouts import (
    Facts,
    Ops,
    ToolError,
    Worktree,
    delete_path,
    hold_for_strangers,
    judge,
    judge_branch,
    lock_pid,
    main,
    parse_merged,
    parse_worktrees,
    process_alive,
    real_git,
    tasklist_has,
    unrecreatable,
)

_HEAD = "b" * 40
_OLD = "a" * 40
_TOOL = Path(__file__).resolve().parents[2] / "tools" / "tidy_checkouts.py"


_WT = Worktree("C:/repo/.claude/worktrees/x", _HEAD, "chore/x")
_FACTS = Facts(
    exists=True,
    toplevel="C:/repo/.claude/worktrees/x",
    status="",
    status_err="",
    ignored=(),
    settings_same=True,
)


_MERGED = {"chore/x": frozenset({_HEAD})}


def _죽었다(_pid: int) -> bool:
    return False


def _살았다(_pid: int) -> bool:
    return True


# --- 읽기 ---------------------------------------------------------------------------------------


def test_워크트리_목록의_porcelain_을_읽는다() -> None:
    porcelain = (
        "worktree C:/repo\nHEAD " + _OLD + "\nbranch refs/heads/main\n\n"
        "worktree C:/repo/.claude/worktrees/a\nHEAD " + _HEAD + "\nbranch refs/heads/chore/a\n"
        "locked claude session a (pid 42)\n\n"
        "worktree C:/repo/.claude/worktrees/b\nHEAD " + _HEAD + "\ndetached\n\n"
        "worktree C:/repo/.claude/worktrees/c\nHEAD " + _HEAD + "\nbranch refs/heads/chore/c\n"
        "locked\nprunable gitdir file points to non-existent location\n\n"
    )
    assert parse_worktrees(porcelain) == [
        Worktree("C:/repo", _OLD, "main"),
        Worktree("C:/repo/.claude/worktrees/a", _HEAD, "chore/a", "claude session a (pid 42)"),
        Worktree("C:/repo/.claude/worktrees/b", _HEAD, None),
        Worktree("C:/repo/.claude/worktrees/c", _HEAD, "chore/c", "", prunable=True),
    ]


def test_잠금_사유에서_pid_를_읽는다() -> None:
    assert lock_pid("claude session 01-tokens (pid 29908)") == 29908
    assert lock_pid("") is None
    assert lock_pid("사람이 잠갔다") is None
    assert lock_pid("claude session a (pid 1) 덧붙임") is None


def test_병합된_PR_목록을_브랜치마다_머리의_집합으로_읽는다() -> None:
    text = (
        '[{"headRefName": "chore/a", "headRefOid": "' + _HEAD + '"},'
        ' {"headRefName": "chore/a", "headRefOid": "' + _OLD + '"},'
        ' {"headRefName": "chore/b", "headRefOid": "' + _OLD + '"}]'
    )
    assert parse_merged(text) == {
        "chore/a": frozenset({_HEAD, _OLD}),
        "chore/b": frozenset({_OLD}),
    }


@pytest.mark.parametrize(
    "text",
    [
        '{"headRefName": "a"}',
        "1",
        '[{"headRefName": 1, "headRefOid": "x"}]',
        '[{"headRefName": "a"}]',
        "[1]",
        "아님",
    ],
)
def test_병합된_PR_목록의_모양이_어긋나면_멈춘다(text: str) -> None:
    with pytest.raises(ValueError):
        parse_merged(text)


def test_tasklist_의_CSV_에서_pid_칸만_본다() -> None:
    output = '"claude.exe","29908","Console","1","123,456 K"\n'
    assert tasklist_has(output, 29908)
    assert not tasklist_has(output, 2990)
    assert not tasklist_has("정보: 지정된 조건에 맞는 작업이 실행되고 있지 않습니다.\n", 29908)


# --- 판정 2: 다시 만들 수 있는 무시된 것 ----------------------------------------------------------


def test_다시_만들_수_있는_무시된_것만_지나간다() -> None:
    entries = [
        ".venv/",
        "src/agent_os/__pycache__/",
        ".pytest_cache/",
        ".ruff_cache/",
        ".import_linter_cache/",
        ".grimp_cache/",
        "web/node_modules/",
        "web/apps/admin/.next/",
        "web/apps/admin/next-env.d.ts",
        "web/packages/ui/visual/test-results/",
        "web/apps/admin/playwright-report/",
        "web/apps/admin/blob-report/",
        "web/apps/admin/coverage/",
        "web/packages/ui/dist/",
        "web/packages/ui/storybook-static/",
        ".claude/settings.local.json",
    ]
    assert unrecreatable(entries, settings_same=True) == []


def test_다시_만들_수_없는_무시된_것을_돌려준다() -> None:
    entries = [".env", "traces/", ".claude/plans/", "web/apps/admin/dist/", ".venv/", "x.pyc"]
    assert unrecreatable(entries, settings_same=True) == [
        ".env",
        "traces/",
        ".claude/plans/",
        "web/apps/admin/dist/",
        "x.pyc",
    ]


def test_루트와_다른_설정_파일은_다시_만들_수_없다() -> None:
    assert unrecreatable([".claude/settings.local.json"], settings_same=False) == [
        ".claude/settings.local.json"
    ]


def test_같은_이름의_파일은_다시_만들_수_있는_폴더가_아니다() -> None:
    assert unrecreatable([".venv", "node_modules"], settings_same=True) == [".venv", "node_modules"]


# --- 판정 ---------------------------------------------------------------------------------------


def test_모두_맞으면_지운다() -> None:
    verdict = judge(_WT, _FACTS, _MERGED, (), _죽었다)
    assert verdict.action == "delete"
    assert (verdict.branch, verdict.head, verdict.unlock) == ("chore/x", _HEAD, False)


def test_prunable_은_사람에게_넘긴다() -> None:
    verdict = judge(replace(_WT, prunable=True), _FACTS, _MERGED, (), _죽었다)
    assert verdict.action == "human"
    assert "prunable" in verdict.reason


def test_폴더가_없으면_사람에게_넘긴다() -> None:
    assert judge(_WT, replace(_FACTS, exists=False), _MERGED, (), _죽었다).action == "human"


def test_git_이_다른_저장소를_읽으면_사람에게_넘긴다() -> None:
    root = judge(_WT, replace(_FACTS, toplevel="C:/repo"), _MERGED, (), _죽었다)
    assert root.action == "human"
    assert "C:/repo" in root.reason
    assert judge(_WT, replace(_FACTS, toplevel=None), _MERGED, (), _죽었다).action == "human"


def test_toplevel_은_구분자와_대소문자를_가리지_않고_견준다() -> None:
    if sys.platform != "win32":
        facts = replace(_FACTS, toplevel="C:/repo/.claude/worktrees/x/")
    else:
        facts = replace(_FACTS, toplevel="c:\\repo\\.claude\\worktrees\\X")
    assert judge(_WT, facts, _MERGED, (), _죽었다).action == "delete"


def test_분리_HEAD_는_사람에게_넘긴다() -> None:
    assert judge(replace(_WT, branch=None), _FACTS, _MERGED, (), _죽었다).action == "human"


def test_병합된_PR_이_없으면_남긴다() -> None:
    verdict = judge(_WT, _FACTS, {}, (), _죽었다)
    assert verdict.action == "keep"
    assert "병합된 PR" in verdict.reason


def test_병합된_PR_의_머리가_브랜치_끝과_다르면_사람에게_넘긴다() -> None:
    verdict = judge(_WT, _FACTS, {"chore/x": frozenset({_OLD})}, (), _죽었다)
    assert verdict.action == "human"


def test_바뀐_파일이_있으면_남긴다() -> None:
    assert judge(_WT, replace(_FACTS, status="?? new.py\0"), _MERGED, (), _죽었다).action == "keep"


def test_status_가_경고를_내면_남긴다() -> None:
    warned = replace(_FACTS, status_err="warning: could not open directory 'x/': Filename too long")
    assert judge(_WT, warned, _MERGED, (), _죽었다).action == "keep"


def test_다시_만들_수_없는_무시된_것이_있으면_남긴다() -> None:
    verdict = judge(_WT, replace(_FACTS, ignored=(".venv/", ".env")), _MERGED, (), _죽었다)
    assert verdict.action == "keep"
    assert ".env" in verdict.reason


def test_설정_파일이_루트와_다르면_남긴다() -> None:
    facts = replace(_FACTS, ignored=(".claude/settings.local.json",), settings_same=False)
    assert judge(_WT, facts, _MERGED, (), _죽었다).action == "keep"


def test_그_브랜치가_제목인_세션이_돌면_남긴다() -> None:
    verdict = judge(_WT, _FACTS, _MERGED, ("chore/x",), _죽었다)
    assert verdict.action == "keep"


def test_잠금_pid_가_살아_있으면_남긴다() -> None:
    locked = replace(_WT, locked="claude session x (pid 7)")
    verdict = judge(locked, _FACTS, _MERGED, (), _살았다)
    assert verdict.action == "keep"
    assert "7" in verdict.reason
    assert "claude session x" in verdict.reason


def test_잠금_pid_가_죽었으면_풀고_지운다() -> None:
    locked = replace(_WT, locked="claude session x (pid 7)")
    verdict = judge(locked, _FACTS, _MERGED, (), _죽었다)
    assert (verdict.action, verdict.unlock) == ("delete", True)


def test_잠금_사유에_pid_가_없으면_사람에게_넘긴다() -> None:
    assert judge(replace(_WT, locked=""), _FACTS, _MERGED, (), _죽었다).action == "human"


def test_제목이_어느_브랜치와도_맞지_않는_세션이_돌면_지울_것을_사람에게_넘긴다() -> None:
    delete = judge(_WT, _FACTS, _MERGED, (), _죽었다)
    keep = judge(_WT, _FACTS, {}, (), _죽었다)
    held = hold_for_strangers([delete, keep], ("앱이 지은 이름",), {"main", "chore/x"})
    assert [verdict.action for verdict in held] == ["hold", "keep"]
    assert "앱이 지은 이름" in held[0].reason


def test_제목이_체크아웃된_브랜치면_다른_워크트리는_그대로다() -> None:
    delete = judge(_WT, _FACTS, _MERGED, (), _죽었다)
    assert hold_for_strangers([delete], ("main",), {"main", "chore/x"}) == [delete]


def test_체크아웃되지_않은_브랜치는_병합된_PR_머리와_같을_때만_지운다() -> None:
    assert judge_branch("chore/x", _HEAD, _MERGED).action == "delete"
    assert judge_branch("chore/x", _OLD, _MERGED).action == "human"
    assert judge_branch("chore/y", _HEAD, _MERGED).action == "keep"


# --- 앞지우기 -----------------------------------------------------------------------------------


def _link(link: Path, target: Path) -> None:
    """디렉터리 링크. 윈도는 권한 없이 만드는 정션, 나머지는 심볼릭 링크."""
    if sys.platform == "win32":
        import _winapi

        _winapi.CreateJunction(str(target), str(link))
    else:
        link.symlink_to(target, target_is_directory=True)


def test_앞지우기는_트리_밖을_가리키는_링크를_따라가지_않는다(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.txt").write_text("남는다", encoding="utf-8")
    tree = tmp_path / "node_modules"
    (tree / "pkg").mkdir(parents=True)
    (tree / "pkg" / "index.js").write_text("x", encoding="utf-8")
    _link(tree / "linked", outside)
    delete_path(tree)
    assert not tree.exists()
    assert (outside / "keep.txt").read_text(encoding="utf-8") == "남는다"


def test_앞지우기는_링크_자체만_지운다(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.txt").write_text("남는다", encoding="utf-8")
    _link(tmp_path / "node_modules", outside)
    delete_path(tmp_path / "node_modules")
    assert not os.path.lexists(tmp_path / "node_modules")
    assert (outside / "keep.txt").exists()


def test_앞지우기는_읽기_전용_파일도_지운다(tmp_path: Path) -> None:
    tree = tmp_path / ".venv"
    tree.mkdir()
    readonly = tree / "locked.txt"
    readonly.write_text("x", encoding="utf-8")
    readonly.chmod(0o444)
    delete_path(tree)
    assert not tree.exists()


def test_앞지우기는_파일_하나도_지운다(tmp_path: Path) -> None:
    single = tmp_path / "next-env.d.ts"
    single.write_text("x", encoding="utf-8")
    delete_path(single)
    assert not single.exists()


def test_도구는_표준_라이브러리만_import_한다() -> None:
    """uv 의 `.venv` 는 캐시에서 하드링크로 채워져, 도구가 서드파티 확장 모듈(pydantic 의 `.pyd`)을
    싣으면 지울 워크트리의 같은 파일을 도구 자신이 쥔다(프로브의 E 갈래)."""
    tree = ast.parse(_TOOL.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None and node.level == 0:
            modules.add(node.module.split(".")[0])
    assert modules, "import 를 하나도 읽지 못했다"
    assert modules - set(sys.stdlib_module_names) - {"__future__"} == set()


# --- 배관: 실제 git 워크트리 ----------------------------------------------------------------------

_IDENTITY = ("-c", "user.name=t", "-c", "user.email=t@example.com")


def _git(*args: str, cwd: Path) -> str:
    result = real_git(list(args), cwd)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git("init", "-b", "main", cwd=root)
    ignore = ".venv/\nnode_modules/\n.env\n/.claude/worktrees/\n.claude/settings.local.json\n"
    (root / ".gitignore").write_text(ignore, encoding="utf-8")
    (root / "README.md").write_text("repo\n", encoding="utf-8")
    _git("add", ".", cwd=root)
    _git(*_IDENTITY, "commit", "-m", "init", cwd=root)
    return root


def test_git_은_색인을_잠그지_않는_환경으로_돈다(repo: Path) -> None:
    alias = "alias.optional-locks=!echo locks=$GIT_OPTIONAL_LOCKS"
    assert _git("-c", alias, "optional-locks", cwd=repo) == "locks=0"


def _add(root: Path, name: str) -> tuple[Path, str]:
    path = root / ".claude" / "worktrees" / name
    _git("worktree", "add", "-b", f"chore/{name}", str(path), cwd=root)
    (path / ".venv" / "Lib").mkdir(parents=True)
    (path / ".venv" / "Lib" / "mod.py").write_text("x", encoding="utf-8")
    (path / "node_modules" / "pkg").mkdir(parents=True)
    (path / "node_modules" / "pkg" / "index.js").write_text("x", encoding="utf-8")
    return path, _git("rev-parse", "HEAD", cwd=path)


def _registered(root: Path, path: Path) -> bool:
    listing = parse_worktrees(_git("worktree", "list", "--porcelain", cwd=root) + "\n")
    return any(os.path.samefile(w.path, path) for w in listing if os.path.exists(w.path))


def _ops(merged: dict[str, frozenset[str]]) -> Ops:
    def merged_source(_root: Path) -> dict[str, frozenset[str]]:
        return merged

    return Ops(merged=merged_source, pid_alive=_죽었다)


def test_judge_는_지울_후보와_명령을_찍는다(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path, head = _add(repo, "done")
    _add(repo, "open")
    code = main(["judge"], cwd=repo, ops=_ops({"chore/done": frozenset({head})}))
    out = capsys.readouterr().out
    assert code == 0, out
    lines = out.splitlines()
    done = next(line for line in lines if "done" in line)
    assert done.startswith("지운다")
    assert f'remove "{path.as_posix()}" chore/done {head}' in done
    opened = next(line for line in lines if "/open" in line)
    assert opened.startswith("남긴다")


def test_judge_는_실행_중인_세션의_제목을_받는다(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _, head = _add(repo, "done")
    merged = {"chore/done": frozenset({head})}
    assert main(["judge", "--running", "chore/done"], cwd=repo, ops=_ops(merged)) == 0
    assert next(line for line in capsys.readouterr().out.splitlines() if "done" in line).startswith(
        "남긴다"
    )


def test_judge_는_제목_모를_세션_때문에_넘긴_후보에_명령을_붙인다(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path, head = _add(repo, "done")
    merged = {"chore/done": frozenset({head})}
    assert main(["judge", "--running", "앱이 지은 이름"], cwd=repo, ops=_ops(merged)) == 0
    done = next(line for line in capsys.readouterr().out.splitlines() if "done" in line)
    assert done.startswith("넘긴다")
    assert "앱이 지은 이름" in done
    assert f'승인하면 → uv run python tools/tidy_checkouts.py remove "{path.as_posix()}"' in done


def test_judge_는_등록_없는_워크트리_폴더를_넘긴다(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    stray = repo / ".claude" / "worktrees" / "stray"
    stray.mkdir(parents=True)
    assert main(["judge"], cwd=repo, ops=_ops({})) == 0
    stray_line = next(line for line in capsys.readouterr().out.splitlines() if "stray" in line)
    assert stray_line.startswith("넘긴다")


def test_judge_는_체크아웃되지_않은_병합된_브랜치를_찍는다(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _git("branch", "chore/loose", cwd=repo)
    tip = _git("rev-parse", "chore/loose", cwd=repo)
    assert main(["judge"], cwd=repo, ops=_ops({"chore/loose": frozenset({tip})})) == 0
    loose = next(line for line in capsys.readouterr().out.splitlines() if "chore/loose" in line)
    assert loose.startswith("브랜치를 지운다")
    assert f"remove-branch chore/loose {tip}" in loose


def test_judge_는_셸이_풀_글자가_든_브랜치에_명령을_찍지_않는다(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """git 은 브랜치 이름에 `;` 를 허락하고, 에이전트는 찍힌 명령을 셸에 그대로 친다."""
    _git("branch", "chore/a;b", cwd=repo)
    tip = _git("rev-parse", "chore/a;b", cwd=repo)
    assert main(["judge"], cwd=repo, ops=_ops({"chore/a;b": frozenset({tip})})) == 0
    line = next(line for line in capsys.readouterr().out.splitlines() if "chore/a;b" in line)
    assert line.startswith("브랜치를 넘긴다")
    assert "remove-branch" not in line


def test_워크트리에서_부르면_아무것도_하지_않고_2로_끝난다(repo: Path) -> None:
    path, head = _add(repo, "done")
    merged = {"chore/done": frozenset({head})}
    assert main(["judge"], cwd=path, ops=_ops(merged)) == 2
    assert main(["remove", str(path), "chore/done", head], cwd=path, ops=_ops(merged)) == 2
    assert path.exists()


def test_지우다_만_워크트리_폴더_안에서_부르면_2로_끝난다(repo: Path) -> None:
    stray = repo / ".claude" / "worktrees" / "stray"
    stray.mkdir(parents=True)
    assert main(["judge"], cwd=stray, ops=_ops({})) == 2


def test_judge_는_체크아웃된_브랜치를_브랜치_줄로_찍지_않는다(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _, head = _add(repo, "done")
    main_tip = _git("rev-parse", "main", cwd=repo)
    merged = {"chore/done": frozenset({head}), "main": frozenset({main_tip})}
    assert main(["judge"], cwd=repo, ops=_ops(merged)) == 0
    lines = capsys.readouterr().out.splitlines()
    branch_lines = [line for line in lines if line.startswith("브랜치")]
    assert not any("chore/done" in line or " main " in line for line in branch_lines)


def test_gh_가_실패하면_3으로_끝난다(repo: Path) -> None:
    def failing(_root: Path) -> dict[str, frozenset[str]]:
        raise ToolError("gh pr list 가 1 로 끝났다")

    assert main(["judge"], cwd=repo, ops=Ops(merged=failing, pid_alive=_죽었다)) == 3


def test_살아_있는_pid_와_끝난_pid_를_가른다() -> None:
    assert process_alive(os.getpid())
    finished = subprocess.run(
        [sys.executable, "-c", "import os; print(os.getpid())"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert not process_alive(int(finished.stdout))


def test_remove_는_무시된_것을_먼저_지우고_워크트리와_브랜치를_지운다(repo: Path) -> None:
    path, head = _add(repo, "done")
    order: list[str] = []
    base = Ops()

    def delete(target: Path) -> None:
        order.append(target.name)
        assert (path / ".git").exists(), "앞지우기는 git 보다 먼저다"
        base.delete(target)

    def git(args: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        if list(args[:2]) == ["worktree", "remove"]:
            order.append("git")
        return real_git(args, cwd)

    ops = replace(_ops({"chore/done": frozenset({head})}), delete=delete, git=git)
    assert main(["remove", path.as_posix(), "chore/done", head], cwd=repo, ops=ops) == 0
    assert sorted(order[:2]) == [".venv", "node_modules"]
    assert order[2:] == ["git"]
    assert not path.exists()
    assert _git("branch", "--list", "chore/done", cwd=repo) == ""


def test_remove_는_judge_뒤에_바뀌었으면_손대지_않는다(repo: Path) -> None:
    path, head = _add(repo, "done")
    merged = {"chore/done": frozenset({head})}
    assert main(["remove", str(path), "chore/done", _OLD], cwd=repo, ops=_ops(merged)) == 1
    assert main(["remove", str(path), "chore/other", head], cwd=repo, ops=_ops(merged)) == 1
    unknown = str(repo / ".claude" / "worktrees" / "nope")
    assert main(["remove", unknown, "chore/done", head], cwd=repo, ops=_ops(merged)) == 1
    assert (path / ".venv").exists()
    assert _registered(repo, path)


def test_remove_는_탐침_자리가_이미_있으면_손대지_않는다(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """윈도는 있는 폴더 위로 이름을 바꾸지 못해 탐침이 막힌 것으로도 1이 나므로 이유까지 본다.
    리눅스의 `rename` 은 빈 폴더를 덮어쓴다."""
    path, head = _add(repo, "done")
    path.with_name("done.tidy-probe").mkdir()
    merged = {"chore/done": frozenset({head})}
    assert main(["remove", str(path), "chore/done", head], cwd=repo, ops=_ops(merged)) == 1
    assert "탐침 자리" in capsys.readouterr().out
    assert (path / ".venv").exists()


def test_remove_는_다시_판정해_어긋나면_손대지_않는다(repo: Path) -> None:
    """후보가 아니면 탐침(폴더 이름 바꾸기)도 하지 않는다. 앞지우기 직전의 재판정과 따로 잰다."""
    path, head = _add(repo, "done")
    (path / "new.py").write_text("x", encoding="utf-8")
    renamed: list[str] = []

    def spy(src: str, dst: str) -> None:
        renamed.append(dst)
        os.rename(src, dst)

    ops = replace(_ops({"chore/done": frozenset({head})}), rename=spy)
    assert main(["remove", str(path), "chore/done", head], cwd=repo, ops=ops) == 1
    assert renamed == []
    assert (path / ".venv").exists()


def test_remove_는_이름_바꾸기가_막히면_손대지_않는다(repo: Path) -> None:
    path, head = _add(repo, "done")

    def held(_src: str, _dst: str) -> None:
        raise PermissionError(13, "액세스가 거부되었습니다")

    ops = replace(_ops({"chore/done": frozenset({head})}), rename=held)
    assert main(["remove", str(path), "chore/done", head], cwd=repo, ops=ops) == 1
    assert (path / ".venv" / "Lib" / "mod.py").exists()
    assert (path / ".git").exists()
    assert _registered(repo, path)


def test_remove_는_이름을_되돌리지_못하면_3으로_멈춘다(repo: Path) -> None:
    path, head = _add(repo, "done")
    calls: list[str] = []

    def once(src: str, dst: str) -> None:
        calls.append(dst)
        if len(calls) == 2:
            raise PermissionError(13, "액세스가 거부되었습니다")
        os.rename(src, dst)

    ops = replace(_ops({"chore/done": frozenset({head})}), rename=once)
    try:
        assert main(["remove", str(path), "chore/done", head], cwd=repo, ops=ops) == 3
    finally:
        aside = Path(calls[0])
        if aside.exists():
            os.rename(aside, path)
    assert _git("branch", "--list", "chore/done", cwd=repo) != ""


def test_remove_는_앞지우기가_막히면_등록과_git_을_남기고_1로_끝난다(repo: Path) -> None:
    path, head = _add(repo, "done")

    def blocked(_target: Path) -> None:
        raise PermissionError(13, "액세스가 거부되었습니다")

    ops = replace(_ops({"chore/done": frozenset({head})}), delete=blocked)
    assert main(["remove", str(path), "chore/done", head], cwd=repo, ops=ops) == 1
    assert (path / ".git").exists()
    assert _registered(repo, path)
    assert _git("branch", "--list", "chore/done", cwd=repo) != ""


def test_remove_는_git_이_지우다_실패하면_브랜치를_남기고_3으로_멈춘다(repo: Path) -> None:
    path, head = _add(repo, "done")

    def failing(args: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        if list(args[:2]) == ["worktree", "remove"]:
            return subprocess.CompletedProcess(list(args), 255, "", "error: failed to delete")
        return real_git(args, cwd)

    ops = replace(_ops({"chore/done": frozenset({head})}), git=failing)
    assert main(["remove", str(path), "chore/done", head], cwd=repo, ops=ops) == 3
    assert _git("branch", "--list", "chore/done", cwd=repo) != ""


def test_remove_는_죽은_잠금을_풀고_지운다(repo: Path) -> None:
    path, head = _add(repo, "done")
    _git("worktree", "lock", "--reason", "claude session done (pid 999999)", str(path), cwd=repo)
    merged = {"chore/done": frozenset({head})}
    assert main(["remove", str(path), "chore/done", head], cwd=repo, ops=_ops(merged)) == 0
    assert not path.exists()


def test_remove_는_탐침이_막히면_죽은_잠금도_풀지_않는다(repo: Path) -> None:
    path, head = _add(repo, "done")
    _git("worktree", "lock", "--reason", "claude session done (pid 999999)", str(path), cwd=repo)

    def held(_src: str, _dst: str) -> None:
        raise PermissionError(13, "액세스가 거부되었습니다")

    ops = replace(_ops({"chore/done": frozenset({head})}), rename=held)
    assert main(["remove", str(path), "chore/done", head], cwd=repo, ops=ops) == 1
    listing = parse_worktrees(_git("worktree", "list", "--porcelain", cwd=repo) + "\n")
    done = next(w for w in listing if w.branch == "chore/done")
    assert done.locked == "claude session done (pid 999999)"


def test_remove_는_앞지우기_직전에_멈추면_죽은_잠금도_풀지_않는다(repo: Path) -> None:
    """PR #163 claude-review: 잠금을 푼 뒤에 재판정이 멈추면 '바꾼 것 없음'이 거짓이 된다."""
    path, head = _add(repo, "done")
    _git("worktree", "lock", "--reason", "claude session done (pid 999999)", str(path), cwd=repo)

    def rename_then_write(src: str, dst: str) -> None:
        os.rename(src, dst)
        if Path(dst).name == "done":
            (path / ".env").write_text("SECRET=x\n", encoding="utf-8")

    ops = replace(_ops({"chore/done": frozenset({head})}), rename=rename_then_write)
    assert main(["remove", str(path), "chore/done", head], cwd=repo, ops=ops) == 1
    listing = parse_worktrees(_git("worktree", "list", "--porcelain", cwd=repo) + "\n")
    done = next(w for w in listing if w.branch == "chore/done")
    assert done.locked == "claude session done (pid 999999)"


def test_remove_는_판정_뒤에_생긴_무시된_파일을_지우지_않고_멈춘다(repo: Path) -> None:
    """판정과 앞지우기 사이(탐침 동안)에 `.env` 가 생긴 경우다."""
    path, head = _add(repo, "done")

    def rename_then_write(src: str, dst: str) -> None:
        os.rename(src, dst)
        if Path(dst).name == "done":
            (path / ".env").write_text("SECRET=x\n", encoding="utf-8")

    ops = replace(_ops({"chore/done": frozenset({head})}), rename=rename_then_write)
    assert main(["remove", str(path), "chore/done", head], cwd=repo, ops=ops) == 1
    assert (path / ".env").exists()
    assert (path / ".venv" / "Lib" / "mod.py").exists()
    assert _registered(repo, path)


def test_remove_는_브랜치를_지우지_못하면_워크트리만_지우고_1로_끝난다(repo: Path) -> None:
    path, head = _add(repo, "done")

    def failing(args: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        if list(args[:1]) == ["branch"]:
            return subprocess.CompletedProcess(list(args), 1, "", "error: branch is locked")
        return real_git(args, cwd)

    ops = replace(_ops({"chore/done": frozenset({head})}), git=failing)
    assert main(["remove", str(path), "chore/done", head], cwd=repo, ops=ops) == 1
    assert not path.exists()
    assert _git("branch", "--list", "chore/done", cwd=repo) != ""


def test_remove_branch_는_다시_보고_지운다(repo: Path) -> None:
    _git("branch", "chore/loose", cwd=repo)
    tip = _git("rev-parse", "chore/loose", cwd=repo)
    merged = {"chore/loose": frozenset({tip})}
    # 옛 머리도 병합된 PR 에 있어야 재확인이 판정 1과 따로 잰다
    both = {"chore/loose": frozenset({tip, _OLD})}
    assert main(["remove-branch", "chore/loose", _OLD], cwd=repo, ops=_ops(both)) == 1
    assert main(["remove-branch", "chore/loose", tip], cwd=repo, ops=_ops({})) == 1
    assert main(["remove-branch", "chore/loose", tip], cwd=repo, ops=_ops(merged)) == 0
    assert _git("branch", "--list", "chore/loose", cwd=repo) == ""


def test_remove_branch_는_체크아웃된_브랜치를_지우지_않는다(repo: Path) -> None:
    _, head = _add(repo, "done")
    merged = {"chore/done": frozenset({head})}
    assert main(["remove-branch", "chore/done", head], cwd=repo, ops=_ops(merged)) == 1


def test_CLI_를_하위_프로세스로_부르면_인자_오류에_2로_끝난다() -> None:
    result = subprocess.run(
        [sys.executable, str(_TOOL), "remove"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode == 2
    assert "usage" in result.stderr
