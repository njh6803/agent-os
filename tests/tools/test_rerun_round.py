"""tools/rerun_round.py 검증. 회차의 자리(티켓 04): 뿌리와 설정 폴더의 검사, 상위의 `.claude/`와
`CLAUDE.md`, 회차 폴더와 표지, B까지만 든 bare와 클론, 준비, 막는 규칙, 세션 환경, 회차 폴더 지우기.

git 을 띄우는 사례는 임시 저장소로 돈다. `tests/conftest.py`가 저장소를 가리키는 `GIT_*`를 이미
벗겼고, 그 값을 일부러 넣는 사례는 임시 원본 저장소를 가리키게 한다.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import time
from pathlib import Path, PurePosixPath, PureWindowsPath

import pytest
from tools.rerun_files import (
    END_NOT_MEASURED,
    SETUP_COMMANDS,
    End,
    Outcome,
    Record,
    ShapeError,
    Spend,
    Tokens,
    read_record,
    record_file_name,
    round_dir_name,
    write_record,
)
from tools.rerun_round import (
    ALLOWED_ENV,
    BLOCKED_TOOLS,
    CONFIG_DIR_VAR,
    FIXED_DENY_RULES,
    GH_CONFIG_VAR,
    MARKER,
    RUNNER_SET_ENV,
    SETUP_ARGV,
    CloneError,
    PlaceError,
    Removal,
    RoundDir,
    SetupEnd,
    SetupFailed,
    build_clone,
    check_clone,
    checked_place,
    checked_root,
    claude_files_above,
    create_round_dir,
    deny_heads,
    deny_rules,
    main,
    main_checkout,
    prepare_round,
    remove_round_dirs,
    root_heads,
    run_setup,
    session_env,
    unrecorded_round_dirs,
    without_venv_dirs,
    write_deny_rules,
)
from tools.tidy_checkouts import delete_path, long_path

from tools import rerun_round

TASK = "model-rerun-04"
GIT_TIMEOUT = 60


def _git(cwd: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@invalid", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=GIT_TIMEOUT,
    )
    assert done.returncode == 0, f"git {args}: {done.stderr}"
    return done.stdout.strip()


def _commit(repo: Path, name: str, text: str) -> str:
    (repo / name).parent.mkdir(parents=True, exist_ok=True)
    (repo / name).write_text(text, encoding="utf-8", newline="\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", name)
    return _git(repo, "rev-parse", "HEAD")


def _원본(at: Path) -> tuple[Path, str, str]:
    """B와 M이 있는 원본 저장소. M에는 태그가, B 뒤와 M 뒤에는 다른 브랜치가 있다. M 뒤의 커밋은 M을
    조상으로 가지므로, 클론에 M이 닿지 않는다는 단언이 그 브랜치까지 덮는다."""
    repo = at / "원본"
    repo.mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    _commit(repo, "README.md", "처음\n")
    _commit(repo, ".claude/settings.json", '{"enabledPlugins": {"p@m": true}}\n')
    b = _commit(repo, "tools/a.py", "A = 1\n")
    _git(repo, "checkout", "-qb", "feature/04-x")
    _commit(repo, "tools/b.py", "B = 2\n")
    _git(repo, "checkout", "-q", "main")
    m = _commit(repo, "tools/a.py", "A = 2\n")
    _git(repo, "tag", "-a", "v1", "-m", "v1")
    _git(repo, "tag", "가벼운")
    _git(repo, "checkout", "-qb", "feature/04-after-m")
    _commit(repo, "tools/c.py", "C = 3\n")
    _git(repo, "checkout", "-q", "main")
    return repo, b, m


@pytest.fixture(scope="module")
def 원본(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, str, str]:
    return _원본(tmp_path_factory.mktemp("원본"))


def _바깥_링크(링크: Path, 대상: Path) -> None:
    """`링크`에 `대상` 폴더를 가리키는 링크를 만든다. 윈도는 권한 없이 만들 수 있는 junction이다."""
    링크.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(링크), str(대상)],
            check=True,
            capture_output=True,
            timeout=GIT_TIMEOUT,
        )
    else:
        링크.symlink_to(대상, target_is_directory=True)


def _기록(dir_name: str, task_id: str = TASK, arm: str = "A", round_no: int = 1) -> Record:
    """지우기가 읽는 최소한의 회차 기록(측정 아님, 중단)."""
    zero = Tokens(input=None, output=None, cache_read=None, cache_write=None, thinking=None)
    return Record(
        task_id=task_id,
        arm=arm,
        round_no=round_no,
        condition_version=1,
        pilot=True,
        round_dir_name=dir_name,
        claude_version=None,
        account="njh6803",
        env_names=(),
        init_tools=(),
        sessions=(),
        handoffs=0,
        interventions=0,
        asked_at_end=False,
        end=End(kind=END_NOT_MEASURED, reason="중단", resets_at=None),
        outcome=Outcome(
            commit=None,
            rule=None,
            commits_after_base=None,
            setup_failure=None,
            gates=None,
            hidden=None,
        ),
        spend=Spend(
            claude_code_usd=0.0,
            official_usd=0.0,
            other_usd=0.0,
            tokens=zero,
            substitutes=(),
            wall_seconds=0.0,
            denied_calls=0,
            utilization_start=(),
            utilization_end=(),
            contamination=(),
            model_mismatch=(),
        ),
    )


def _기록된_회차(root: Path, records: Path, token: str, round_no: int = 1) -> RoundDir:
    place = create_round_dir(root, TASK, "A", round_no, token=token)
    records.mkdir(parents=True, exist_ok=True)
    write_record(records, _기록(place.name, round_no=round_no))
    return place


# --- 뿌리와 설정 폴더 ---


def _금지(tmp_path: Path) -> tuple[Path, Path]:
    main_dir = tmp_path / "agent"
    claude = tmp_path / "home" / ".claude"
    main_dir.mkdir()
    claude.mkdir(parents=True)
    return main_dir, claude


def _자리(text: str, main_dir: Path, claude: Path, what: str = "뿌리") -> Path:
    return checked_place(text, what, main_checkout=main_dir, user_claude=claude)


@pytest.mark.parametrize("text", ["rerun", "./rerun", "rerun/깊이", "~/rerun", "\\\\?\\C:\\rerun"])
def test_상대_경로_뿌리는_멈춘다(tmp_path: Path, text: str) -> None:
    with pytest.raises(PlaceError, match="절대 경로"):
        _자리(text, *_금지(tmp_path))


@pytest.mark.parametrize(
    "text",
    [
        "\\\\?/C:/rerun",
        "/\\?\\C:\\rerun",
        "\\\\localhost\\C$\\rerun",
        "//localhost/C$/rerun",
        "//rerun",
    ],
)
def test_구분자_둘로_시작하는_장치와_UNC_경로는_멈춘다(tmp_path: Path, text: str) -> None:
    """섞인 접두와 관리 공유는 realpath 를 거쳐도 주 체크아웃과 같은 조각으로 풀리지 않는다."""
    with pytest.raises(PlaceError, match="절대 경로"):
        _자리(text, *_금지(tmp_path))


def test_주_체크아웃과_그_아래는_멈춘다(tmp_path: Path) -> None:
    main_dir, claude = _금지(tmp_path)
    for text in (str(main_dir), str(main_dir / "rerun"), str(main_dir / "a" / "b")):
        with pytest.raises(PlaceError, match="주 체크아웃"):
            _자리(text, main_dir, claude)


def test_대소문자와_구분자만_다른_주_체크아웃도_멈춘다(tmp_path: Path) -> None:
    """있는 폴더는 윈도의 realpath 가 실제 이름으로 바꿔 주므로, 아직 없는 머리로도 본다."""
    main_dir, claude = _금지(tmp_path)
    for head in (main_dir, tmp_path / "Agent-Missing"):
        text = str(head / "rerun").swapcase()
        if sys.platform == "win32":
            text = text.replace("\\", "/")
        with pytest.raises(PlaceError, match="주 체크아웃"):
            _자리(text, head, claude)


def test_이웃_이름은_받는다(tmp_path: Path) -> None:
    main_dir, claude = _금지(tmp_path)
    for text in (str(tmp_path / "agent-rerun"), str(tmp_path / "home" / ".claude-rerun")):
        assert _자리(text, main_dir, claude) == Path(text)


def test_사용자_claude와_그_아래는_멈춘다(tmp_path: Path) -> None:
    main_dir, claude = _금지(tmp_path)
    for text in (str(claude), str(claude / "projects")):
        with pytest.raises(PlaceError, match=r"~/\.claude"):
            _자리(text, main_dir, claude, "설정 폴더")


def test_주_체크아웃을_가리키는_링크_아래도_멈춘다(tmp_path: Path) -> None:
    main_dir, claude = _금지(tmp_path)
    _바깥_링크(tmp_path / "링크", main_dir)
    with pytest.raises(PlaceError, match="주 체크아웃"):
        _자리(str(tmp_path / "링크" / "rerun"), main_dir, claude)


def test_주_체크아웃_안의_링크를_거쳐_밖을_가리키는_뿌리도_멈춘다(tmp_path: Path) -> None:
    """글자 그대로의 상위에 주 체크아웃이 든다. 링크를 푼 꼴만 보면 지나간다."""
    main_dir, claude = _금지(tmp_path)
    outside = tmp_path / "바깥"
    outside.mkdir()
    _바깥_링크(main_dir / "밖으로", outside)
    with pytest.raises(PlaceError, match="주 체크아웃"):
        _자리(str(main_dir / "밖으로" / "rerun"), main_dir, claude)


def test_윈도가_끝의_점을_떼는_이름은_윈도에서_멈춘다(tmp_path: Path) -> None:
    """윈도는 `agent.`를 `agent`로 읽는다. 리눅스에서는 다른 폴더라 받는다. 있는 폴더는 윈도의
    realpath 가 실제 이름으로 바꿔 주므로, 아직 없는 머리로도 본다."""
    main_dir, claude = _금지(tmp_path)
    for head in (main_dir, tmp_path / "없는체크아웃"):
        text = str(head) + "." + os.sep + "rerun"
        if sys.platform == "win32":
            with pytest.raises(PlaceError, match="주 체크아웃"):
                _자리(text, head, claude)
        else:
            assert _자리(text, head, claude) == Path(text)


def test_가운데_조각_끝의_공백과_점_둘은_윈도에서_자식과_상관없이_막는_쪽으로_틀린다(
    tmp_path: Path,
) -> None:
    """못 보는 것: 윈도에서 `agent \\rerun`·`agent..\\rerun`은 이름이 다른 폴더를 열지만, 그 경로가
    없으면 `realpath`가 부모 쪽으로 풀며 그 조각을 마지막 조각처럼 열어 끝을 떼므로 `agent` 아래로
    읽어 막는다. `agent` 아래에 같은 이름의 자식이 있든 없든 같다. 리눅스에서는 이름이 다른 폴더라
    받는다."""
    main_dir, claude = _금지(tmp_path)
    (main_dir / "있음").mkdir()
    for tail in (" ", ".."):
        for child in ("rerun", "있음"):
            text = str(main_dir) + tail + os.sep + child
            if sys.platform == "win32":
                with pytest.raises(PlaceError, match="주 체크아웃"):
                    _자리(text, main_dir, claude)
            else:
                assert _자리(text, main_dir, claude) == Path(text)


def test_가운데_조각_끝의_공백과_점_둘은_그_경로가_있으면_다른_폴더라_받는다(
    tmp_path: Path,
) -> None:
    """윈도도 가운데 조각에서는 끝의 공백과 점 둘을 떼지 않아 `agent \\rerun`·`agent..\\rerun`은
    이름이 다른 폴더를 연다. 그 경로가 있으면 `realpath`가 그대로 풀어 받는다. 그런 이름의 폴더는
    `\\\\?\\` 경로로 만들고 지운다. 윈도의 보통 경로로는 마지막 조각의 끝이 떼여 `agent`를
    가리킨다."""
    main_dir, claude = _금지(tmp_path)
    for tail in (" ", ".."):
        other = Path(str(main_dir) + tail)
        text = str(other) + os.sep + "rerun"
        os.makedirs(long_path(text))
        try:
            assert _자리(text, main_dir, claude) == Path(text)
        finally:
            delete_path(other)


def test_역슬래시는_리눅스에서도_구분자로_읽어_막는_쪽으로_틀린다(tmp_path: Path) -> None:
    """못 보는 것: 리눅스에서 `agent\\rerun`은 주 체크아웃 옆의 한 이름이지만 그 아래로 읽는다."""
    main_dir, claude = _금지(tmp_path)
    with pytest.raises(PlaceError, match="주 체크아웃"):
        _자리(str(main_dir) + "\\rerun", main_dir, claude)


def test_상위의_claude_폴더와_claude_md를_찾는다(tmp_path: Path) -> None:
    (tmp_path / "a" / ".claude").mkdir(parents=True)
    (tmp_path / "a" / "b").mkdir()
    (tmp_path / "a" / "b" / "CLAUDE.md").write_text("상위\n", encoding="utf-8")
    (tmp_path / "CLAUDE.local.md").write_text("상위\n", encoding="utf-8")
    found = claude_files_above(tmp_path / "a" / "b" / "rerun", home=Path.home())
    assert set(found) >= {
        tmp_path / "a" / ".claude",
        tmp_path / "a" / "b" / "CLAUDE.md",
        tmp_path / "CLAUDE.local.md",
    }


def test_홈의_claude_폴더는_세지_않고_홈의_claude_md는_센다(tmp_path: Path) -> None:
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    (home / "rerun" / ".claude").mkdir(parents=True)
    found = claude_files_above(home / "rerun" / "x", home=home)
    assert home / "rerun" / ".claude" in found
    assert home / ".claude" not in found
    (home / "CLAUDE.md").write_text("홈\n", encoding="utf-8")
    assert home / "CLAUDE.md" in claude_files_above(home / "rerun" / "x", home=home)


def test_뿌리_검사는_상위의_claude_폴더에서_멈춘다(tmp_path: Path) -> None:
    main_dir = tmp_path / "agent"
    main_dir.mkdir()
    (tmp_path / "위" / ".claude").mkdir(parents=True)
    with pytest.raises(PlaceError, match=r"\.claude"):
        checked_root(str(tmp_path / "위" / "rerun"), main_checkout=main_dir, home=Path.home())
    root = checked_root(str(tmp_path / "옆" / "rerun"), main_checkout=main_dir, home=Path.home())
    assert root == tmp_path / "옆" / "rerun"


def test_뿌리를_본_뒤_상위에_생긴_claude_폴더는_다시_보지_않는다(tmp_path: Path) -> None:
    """못 보는 것: 회차 폴더 만들기는 뿌리의 상위를 다시 보지 않는다."""
    main_dir = tmp_path / "agent"
    main_dir.mkdir()
    root = checked_root(str(tmp_path / "위" / "rerun"), main_checkout=main_dir, home=Path.home())
    (tmp_path / "위" / ".claude").mkdir(parents=True)
    place = create_round_dir(root, TASK, "A", 1, token="y4")
    assert tmp_path / "위" / ".claude" in claude_files_above(place.path, home=Path.home())
    assert (place.path / MARKER).exists()


def test_주_체크아웃은_worktree_목록의_첫_줄이다(tmp_path: Path) -> None:
    repo = tmp_path / "주"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _commit(repo, "a.txt", "a\n")
    _git(repo, "worktree", "add", "-q", str(tmp_path / "가지"), "-b", "가지")
    found = main_checkout(tmp_path / "가지")
    assert os.path.normcase(found.resolve()) == os.path.normcase(repo.resolve())


# --- 회차 폴더와 표지 ---


def test_회차_폴더는_정해진_이름이고_표지와_빈_폴더가_든다(tmp_path: Path) -> None:
    place = create_round_dir(tmp_path / "뿌리", TASK, "B", 3, token="ab12")
    assert place.path == tmp_path / "뿌리" / f"{TASK}-B-3-ab12"
    assert place.name == f"{TASK}-B-3-ab12"
    assert (place.path / MARKER).read_text(encoding="utf-8") == place.name
    assert place.gh_config.is_dir()
    assert not any(place.gh_config.iterdir())
    assert place.stream.is_dir()
    assert not place.clone.exists()
    assert not place.bare.exists()


def test_회차마다_경로가_다르다(tmp_path: Path) -> None:
    one = create_round_dir(tmp_path, TASK, "A", 1)
    two = create_round_dir(tmp_path, TASK, "A", 1)
    assert one.path != two.path
    assert one.path.parent == two.path.parent == tmp_path


def test_호출의_수는_덧붙인_세션_id_의_줄_수이고_파일이_없으면_0이다(tmp_path: Path) -> None:
    place = create_round_dir(tmp_path, TASK, "A", 1, token="n1")
    assert place.call_count() == 0, "파일이 없는데 호출을 셌다"
    place.append_session_id("s-1")
    place.append_session_id("s-1")  # 이어 부른 호출도 한 줄이다
    assert place.call_count() == 2, "덧붙인 줄과 호출의 수가 다르다"


def test_이미_있는_회차_폴더는_덮지_않고_실패한다(tmp_path: Path) -> None:
    place = create_round_dir(tmp_path, TASK, "A", 1, token="x1")
    (place.path / "남길것.txt").write_text("그대로\n", encoding="utf-8")
    with pytest.raises(FileExistsError):
        create_round_dir(tmp_path, TASK, "A", 1, token="x1")
    assert (place.path / "남길것.txt").read_text(encoding="utf-8") == "그대로\n"
    assert sorted(p.name for p in place.path.iterdir()) == sorted(
        [MARKER, "남길것.txt", place.gh_config.name, place.stream.name]
    )


# --- bare와 클론 ---


def _refs(repo: Path) -> dict[str, str]:
    out = _git(repo, "for-each-ref", "--format=%(refname) %(objectname)")
    return dict(line.split(" ", 1) for line in out.splitlines())


def test_클론에는_B까지의_이력만_있고_origin은_bare다(
    tmp_path: Path, 원본: tuple[Path, str, str]
) -> None:
    repo, b, m = 원본
    place = create_round_dir(tmp_path, TASK, "A", 1, token="c1")
    build_clone(repo, b, m, place)
    clone_refs = _refs(place.clone)
    assert clone_refs and set(clone_refs.values()) == {b}
    assert _refs(place.bare) == {"refs/heads/main": b}
    for where in (place.clone, place.bare):
        assert m not in _git(where, "rev-list", "--all").split()
        assert _git(where, "tag") == ""
    assert _git(place.clone, "rev-parse", "HEAD") == b
    assert _git(place.clone, "branch", "--show-current") == "main"
    origin = _git(place.clone, "remote", "get-url", "origin")
    assert os.path.normcase(Path(origin).resolve()) == os.path.normcase(place.bare.resolve())
    assert _git(place.clone, "remote") == "origin"


def test_원본에_저장소_위치_변수가_있어도_원본을_건드리지_않는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """pre-commit 아래에서 git이 내보내는 `GIT_DIR`·`GIT_INDEX_FILE`이 남으면 `git init`이 그
    저장소를 재초기화한다(`.claude/rules/tools.md`의 pre-commit 항목)."""
    repo, b, m = _원본(tmp_path / "따로")
    before = (_refs(repo), _git(repo, "config", "--get", "core.bare"))
    monkeypatch.setenv("GIT_DIR", str(repo / ".git"))
    monkeypatch.setenv("GIT_INDEX_FILE", str(repo / ".git" / "index"))
    monkeypatch.setenv("GIT_WORK_TREE", str(repo))
    place = create_round_dir(tmp_path, TASK, "A", 1, token="e1")
    build_clone(repo, b, m, place)
    monkeypatch.delenv("GIT_DIR")
    monkeypatch.delenv("GIT_INDEX_FILE")
    monkeypatch.delenv("GIT_WORK_TREE")
    assert (_refs(repo), _git(repo, "config", "--get", "core.bare")) == before
    assert set(_refs(place.clone).values()) == {b}


def test_원본의_설정과_훅이_있어도_B만_origin으로_민다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """원본 설정이 태그를 따라 밀고(`push.followTags`, B에 단 주석 태그), 사용자 설정이 원격 이름을
    바꾸고(`clone.defaultRemoteName`), 원본의 pre-push 훅이 막아도 B만 `origin`의 `main`으로
    간다."""
    repo, b, m = _원본(tmp_path / "따로")
    _git(repo, "tag", "-a", "b-태그", "-m", "B", b)
    _git(repo, "config", "push.followTags", "true")
    hooks = repo / ".git" / "hooks"
    ran = tmp_path / "hook-ran"
    hook = hooks / "pre-push"
    hook.write_text(
        f"#!/bin/sh\necho ran > '{ran.as_posix()}'\nexit 1\n", encoding="utf-8", newline="\n"
    )
    hook.chmod(0o755)
    _git(repo, "config", "core.hooksPath", hooks.as_posix())
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "clone.defaultRemoteName")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "upstream")
    place = create_round_dir(tmp_path, TASK, "A", 1, token="o1")
    build_clone(repo, b, m, place)
    assert not ran.exists()
    for where in (place.clone, place.bare):
        assert _git(where, "tag") == ""
    assert _git(place.clone, "remote") == "origin"


def test_다른_ref가_있는_클론은_대_보기에서_멈춘다(
    tmp_path: Path, 원본: tuple[Path, str, str]
) -> None:
    repo, b, m = 원본
    place = create_round_dir(tmp_path, TASK, "A", 1, token="v1")
    build_clone(repo, b, m, place)
    _git(place.clone, "branch", "옛것", "HEAD~1")
    with pytest.raises(CloneError, match="refs/heads/옛것"):
        check_clone(place, b, m)


def test_M이_들어온_클론은_대_보기에서_멈춘다(tmp_path: Path, 원본: tuple[Path, str, str]) -> None:
    repo, b, m = 원본
    place = create_round_dir(tmp_path, TASK, "A", 1, token="v2")
    build_clone(repo, b, m, place)
    _git(place.clone, "fetch", "-q", "--no-tags", str(repo), "main:refs/tmp/m")
    with pytest.raises(CloneError, match="refs/tmp/m"):
        check_clone(place, b, m)
    _git(place.clone, "update-ref", "-d", "refs/tmp/m")
    with pytest.raises(CloneError, match="M 개체"):
        check_clone(place, b, m)


def test_M이_들어온_bare도_대_보기에서_멈춘다(tmp_path: Path, 원본: tuple[Path, str, str]) -> None:
    repo, b, m = 원본
    place = create_round_dir(tmp_path, TASK, "A", 1, token="v3")
    build_clone(repo, b, m, place)
    _git(place.bare, "fetch", "-q", "--no-tags", str(repo), "main:refs/tmp/m")
    _git(place.bare, "update-ref", "-d", "refs/tmp/m")
    with pytest.raises(CloneError, match="M 개체"):
        check_clone(place, b, m)


# --- 막는 규칙 ---


def test_막는_규칙의_경로는_권한_규칙의_절대_경로_꼴이다() -> None:
    rules = deny_rules((PureWindowsPath("C:/project/agent"), PurePosixPath("/home/u/.claude")))
    for tool in ("Read", "Edit", "Write"):
        assert f"{tool}(//c/project/agent/**)" in rules
        assert f"{tool}(//home/u/.claude/**)" in rules


def test_막는_규칙에_명세의_목록이_모두_든다() -> None:
    rules = deny_rules((PureWindowsPath("C:/project/agent"),))
    expected = {
        "Bash(gh:*)",
        "Bash(git push:*)",
        "Skill(open-session)",
        "Bash(*open_session.ps1*)",
        "Bash(*claude://*)",
        "WebFetch",
        "WebSearch",
        "SendMessage",
        "ListAgents",
        "RemoteTrigger",
        "PushNotification",
        "DesignSync",
        "CronCreate",
        "ScheduleWakeup",
    }
    assert expected <= set(rules)
    assert set(FIXED_DENY_RULES) | set(BLOCKED_TOOLS) == expected
    assert len(rules) == len(set(rules))


def test_막는_규칙은_회차_폴더의_파일에_쓰고_클론은_그대로_둔다(
    tmp_path: Path, 원본: tuple[Path, str, str]
) -> None:
    """클론의 `settings.local.json`에 두면 B의 지침 검사가 주 체크아웃의 local 가드로 잡아, 세션의
    pre-commit 과 게이트가 빨갰다(파일럿 첫 실행, 일지 2026-10-28-10)."""
    repo, b, m = 원본
    place = create_round_dir(tmp_path, TASK, "A", 1, token="r1")
    build_clone(repo, b, m, place)
    settings = place.clone / ".claude" / "settings.json"
    before = settings.read_bytes()
    write_deny_rules(place, ["Bash(gh:*)", "WebFetch"])
    written = json.loads(place.deny_settings.read_text("utf-8"))
    assert written == {"permissions": {"deny": ["Bash(gh:*)", "WebFetch"]}}
    assert place.deny_settings.parent == place.path
    assert not os.path.lexists(place.clone / ".claude" / "settings.local.json")
    assert settings.read_bytes() == before
    # 사용자의 전역 무시 파일 없이도 세션의 `git status`가 비었다. HOME 을 바꾸면 전역
    # `core.autocrlf`까지 빠져 줄 끝 차이가 바뀐 파일로 보이므로 무시 파일만 덮는다.
    empty = tmp_path / "빈무시"
    empty.write_text("", encoding="utf-8")
    status = subprocess.run(
        ["git", "-c", f"core.excludesFile={empty}", "status", "--porcelain", "-uall"],
        cwd=place.clone,
        capture_output=True,
        text=True,
        check=True,
        timeout=GIT_TIMEOUT,
    )
    assert status.stdout == ""


def test_막는_규칙의_경로는_주_체크아웃과_사용자_claude의_두_꼴이다(tmp_path: Path) -> None:
    main_dir = tmp_path / "agent"
    main_dir.mkdir()
    _바깥_링크(tmp_path / "링크", main_dir)
    heads = deny_heads(tmp_path / "링크", home=tmp_path / "home")
    assert tmp_path / "링크" in heads
    assert Path(os.path.realpath(main_dir)) in heads
    assert tmp_path / "home" / ".claude" in heads
    assert len(heads) == len(set(heads))


def test_뿌리_규칙은_바로_아래의_점이_든_이름만_편집과_쓰기를_막는다() -> None:
    """`<뿌리>/*`는 회차 폴더에도 맞아 클론 쓰기까지 막았다(`deny_shapes/root_shape.py`)."""
    rules = deny_rules(
        (PureWindowsPath("C:/project/agent"),), roots=(PureWindowsPath("C:/Users/u/rounds"),)
    )
    root_rules = [r for r in rules if "rounds" in r]
    assert root_rules == ["Edit(//c/Users/u/rounds/*.*)", "Write(//c/Users/u/rounds/*.*)"]
    assert rules.index("Write(//c/project/agent/**)") < rules.index(root_rules[0])
    assert rules[-len(BLOCKED_TOOLS) :] == list(BLOCKED_TOOLS)


def test_회차_폴더_이름에는_점이_없어_뿌리_규칙에_맞지_않는다(tmp_path: Path) -> None:
    """뿌리 규칙 `*.*`가 회차 폴더에 맞으면 그 안의 클론 쓰기가 막힌다."""
    place = create_round_dir(tmp_path / "rounds", "end-user-continuation-03", "E", 12, token="ab9")
    assert "." not in place.name
    # 이름의 조각마다 점을 받지 않는다. 받게 바뀌면 `*.*`가 회차 폴더에 맞을 수 있다
    for task_id, token in (("a.b-03", "ab9"), ("end-user-continuation-03", "a.b")):
        with pytest.raises(ShapeError):
            round_dir_name(task_id, "E", 1, token)


def test_뿌리_꼴은_링크를_푼_꼴이_다르면_그것도_든다(tmp_path: Path) -> None:
    real = tmp_path / "진짜뿌리"
    real.mkdir()
    _바깥_링크(tmp_path / "링크뿌리", real)
    heads = root_heads(tmp_path / "링크뿌리")
    assert heads[0] == Path(os.path.abspath(tmp_path / "링크뿌리"))
    assert Path(os.path.realpath(real)) in heads
    assert len(heads) == len(set(heads))


def test_막는_규칙은_같은_뿌리의_다른_회차_폴더를_막지_않는다(tmp_path: Path) -> None:
    """못 보는 것: 함께 도는 갈래의 회차 폴더는 막는 규칙에 들지 않는다(09가 오염으로 볼지
    정한다)."""
    other = create_round_dir(tmp_path / "회차뿌리", TASK, "B", 1, token="y5")
    rules = deny_rules(
        deny_heads(tmp_path / "agent", home=tmp_path / "home"),
        roots=root_heads(tmp_path / "회차뿌리"),
    )
    assert [r for r in rules if other.name in r] == []
    # 뿌리에 걸린 규칙은 바로 아래 점이 든 이름의 편집·쓰기뿐이다(읽기는 막지 않는다)
    assert {r.split("(", 1)[0] for r in rules if "회차뿌리" in r} == {"Edit", "Write"}
    assert all(r.endswith("/*.*)") for r in rules if "회차뿌리" in r)
    assert any("agent" in r for r in rules)


def test_이미_있는_규칙_파일은_덮지_않고_멈춘다(tmp_path: Path) -> None:
    place = create_round_dir(tmp_path, TASK, "A", 1, token="r2")
    place.deny_settings.write_text("{}\n", encoding="utf-8")
    with pytest.raises(CloneError, match=r"deny-settings\.json"):
        write_deny_rules(place, ["WebFetch"])
    assert place.deny_settings.read_text("utf-8") == "{}\n"


# --- 준비 ---


def _명령(code: str) -> tuple[str, ...]:
    return (sys.executable, "-c", code)


def _준비_환경() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def test_실제_준비_명령은_명세의_셋이다() -> None:
    assert [" ".join(argv) for argv in SETUP_ARGV] == [
        "uv sync",
        "pnpm -C web install --frozen-lockfile",
        "uv run pre-commit install",
    ]
    assert tuple(" ".join(argv) for argv in SETUP_ARGV) == SETUP_COMMANDS


def test_준비_명령은_클론에서_차례로_돈다(tmp_path: Path) -> None:
    commands = [
        _명령("open('하나.txt', 'w').write('1')"),
        _명령("import os; assert os.path.exists('하나.txt'); open('둘.txt', 'w').write('2')"),
    ]
    done = run_setup(tmp_path, commands, env=_준비_환경(), log=tmp_path / "준비.log", timeout=60)
    assert done.failed is None
    assert (tmp_path / "하나.txt").exists() and (tmp_path / "둘.txt").exists()


def test_준비가_실패하면_남은_명령을_돌리지_않고_어느_명령이_몇으로_끝났는지_낸다(
    tmp_path: Path,
) -> None:
    second = _명령("import sys; sys.exit(3)")
    commands = [_명령("pass"), second, _명령("open('셋.txt', 'w').write('3')")]
    done = run_setup(tmp_path, commands, env=_준비_환경(), log=tmp_path / "준비.log", timeout=60)
    assert done.failed is not None
    assert (done.failed.index, done.failed.command, done.failed.end, done.failed.exit_code) == (
        1,
        " ".join(second),
        SetupEnd.EXITED,
        3,
    )
    assert not (tmp_path / "셋.txt").exists()


def test_준비가_시간을_넘기면_종료_코드_없이_실패다(tmp_path: Path) -> None:
    commands = [_명령("import time; time.sleep(30)"), _명령("open('뒤.txt', 'w').write('x')")]
    started = time.monotonic()
    done = run_setup(tmp_path, commands, env=_준비_환경(), log=tmp_path / "준비.log", timeout=0.5)
    assert time.monotonic() - started < 20
    assert done.failed is not None
    assert (done.failed.index, done.failed.end, done.failed.exit_code) == (
        0,
        SetupEnd.TIMED_OUT,
        None,
    )
    assert not (tmp_path / "뒤.txt").exists()


def test_찾지_못한_준비_명령도_실패다(tmp_path: Path) -> None:
    commands = [("없는-명령-04-round-clone",)]
    done = run_setup(tmp_path, commands, env=_준비_환경(), log=tmp_path / "준비.log", timeout=60)
    assert done.failed is not None
    assert (done.failed.index, done.failed.end, done.failed.exit_code) == (
        0,
        SetupEnd.NOT_STARTED,
        None,
    )


@pytest.mark.parametrize(
    ("end", "exit_code"),
    [
        (SetupEnd.EXITED, None),
        (SetupEnd.EXITED, 0),
        (SetupEnd.TIMED_OUT, 1),
        (SetupEnd.NOT_STARTED, 1),
    ],
)
def test_준비_실패의_종료_코드는_끝까지_돈_명령에만_있고_0이_아니다(
    end: SetupEnd, exit_code: int | None
) -> None:
    with pytest.raises(ValueError, match="종료 코드"):
        SetupFailed(0, "uv sync", end, exit_code)


def test_준비_시간은_회차의_벽시계에_들지_않는다(tmp_path: Path) -> None:
    before = time.monotonic()
    done = run_setup(
        tmp_path,
        [_명령("import time; time.sleep(0.4)")],
        env=_준비_환경(),
        log=tmp_path / "준비.log",
        timeout=60,
    )
    assert done.failed is None
    assert done.wall_clock_from - before >= 0.4


def test_준비의_출력은_로그_파일에_남는다(tmp_path: Path) -> None:
    log = tmp_path / "준비.log"
    run_setup(tmp_path, [_명령("print('준비-표지')")], env=_준비_환경(), log=log, timeout=60)
    assert "준비-표지" in log.read_text(encoding="utf-8", errors="replace")


def test_준비의_git은_저장소_위치_변수를_물려받지_않는다(
    tmp_path: Path, 원본: tuple[Path, str, str]
) -> None:
    repo, b, m = 원본
    place = create_round_dir(tmp_path, TASK, "A", 1, token="s1")
    build_clone(repo, b, m, place)
    env = {**_준비_환경(), "GIT_DIR": str(repo / ".git"), "GIT_WORK_TREE": str(repo)}
    code = (
        "import subprocess; "
        "out = subprocess.run(['git', 'rev-parse', '--absolute-git-dir'], capture_output=True, "
        "text=True, timeout=60).stdout; open('git-dir.txt', 'w').write(out)"
    )
    done = run_setup(place.clone, [_명령(code)], env=env, log=place.path / "준비.log", timeout=60)
    assert done.failed is None
    found = (place.clone / "git-dir.txt").read_text().strip()
    assert os.path.normcase(Path(found).resolve()) == os.path.normcase(
        (place.clone / ".git").resolve()
    )


def test_회차_준비는_클론과_막는_규칙과_준비를_차례로_한다(
    tmp_path: Path, 원본: tuple[Path, str, str]
) -> None:
    repo, b, m = 원본
    place = create_round_dir(tmp_path, TASK, "A", 1, token="p1")
    before = time.monotonic()
    done = prepare_round(
        place,
        source=repo,
        base=b,
        merge=m,
        rules=["WebFetch"],
        setup=[_명령("import time; open('준비됨.txt', 'w').write('1'); time.sleep(0.2)")],
        env=_준비_환경(),
        timeout=60,
    )
    assert done.failed is None
    assert done.wall_clock_from - before >= 0.2
    assert (place.clone / "준비됨.txt").exists()
    written = json.loads(place.deny_settings.read_text("utf-8"))
    assert written["permissions"]["deny"] == ["WebFetch"]
    assert set(_refs(place.clone).values()) == {b}


# --- 환경 ---


def test_세션_환경은_허용_목록과_러너가_짓는_셋뿐이다(tmp_path: Path) -> None:
    place = create_round_dir(tmp_path, TASK, "A", 1, token="n1")
    parent = {
        "PATH": "/bin",
        "HOME": "/home/u",
        "UV_CACHE_DIR": "/cache/uv",
        "GH_TOKEN": "ghp_가짜토큰",
        "GITHUB_TOKEN": "가짜",
        "ANTHROPIC_API_KEY": "sk-가짜",
        "CLAUDE_CONFIG_DIR": "/옛/설정",
        "VIRTUAL_ENV": "/러너/.venv",
        "GIT_DIR": "/러너/.git",
    }
    env = session_env(parent, config_dir="C:/Users/User/.claude-rerun", round_dir=place)
    inherited = {n for n in ALLOWED_ENV if n in parent and n not in RUNNER_SET_ENV}
    assert set(env) == inherited | set(RUNNER_SET_ENV)
    assert set(env) <= set(ALLOWED_ENV) | {GH_CONFIG_VAR}
    assert GH_CONFIG_VAR in RUNNER_SET_ENV and CONFIG_DIR_VAR in RUNNER_SET_ENV
    assert env[CONFIG_DIR_VAR] == "C:/Users/User/.claude-rerun"
    assert env["DISABLE_AUTOUPDATER"] == "1"
    assert env[GH_CONFIG_VAR] == str(place.gh_config)
    assert env["PATH"] == "/bin"
    assert "ghp_가짜토큰" not in env.values()


def test_세션의_PATH_에서_가상_환경의_실행_폴더를_뺀다(tmp_path: Path) -> None:
    """러너를 주 체크아웃에서 `uv run` 으로 띄우면 그 `.venv` 의 실행 폴더가 `PATH` 맨 앞에 와서,
    세션의 맨 `pytest` 가 클론이 아니라 주 체크아웃의 환경과 코드로 돈다(04 의 메모)."""
    venv = tmp_path / "주" / ".venv"
    scripts = venv / ("Scripts" if os.name == "nt" else "bin")
    scripts.mkdir(parents=True)
    (venv / "pyvenv.cfg").write_text("home = x\n", encoding="utf-8")
    plain = tmp_path / "bin"
    plain.mkdir()
    place = create_round_dir(tmp_path / "뿌리", TASK, "A", 1, token="n3")
    parent = {"PATH": os.pathsep.join([str(scripts), str(plain), "", str(scripts) + os.sep])}

    env = session_env(parent, config_dir="C:/설정", round_dir=place)

    assert env["PATH"].split(os.pathsep) == [str(plain), ""]


def test_PATH_의_상대_조각과_루트는_작업_폴더의_pyvenv_cfg_와_견주지_않는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "pyvenv.cfg").write_text("home = x\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    root = os.path.abspath(os.sep)
    parts = ["Scripts", "bin", "x", ".", os.sep, root]

    assert without_venv_dirs(os.pathsep.join(parts)).split(os.pathsep) == parts


def test_부모_환경의_가짜_gh_토큰은_넘어가지_않는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GH_TOKEN", "ghp_가짜토큰")
    place = create_round_dir(tmp_path, TASK, "A", 1, token="n2")
    env = session_env(os.environ, config_dir=str(tmp_path / "설정"), round_dir=place)
    assert "GH_TOKEN" not in env
    assert set(env) <= set(ALLOWED_ENV) | {GH_CONFIG_VAR}
    assert "PATH" in env


def test_허용_목록에는_명세의_이름이_든다() -> None:
    assert {
        "USERNAME",
        "USERDOMAIN",
        "COMPUTERNAME",
        "NUMBER_OF_PROCESSORS",
        "OS",
        "PROCESSOR_ARCHITECTURE",
        "PROCESSOR_IDENTIFIER",
        "PROCESSOR_LEVEL",
        "PROCESSOR_REVISION",
        "ALLUSERSPROFILE",
        "PUBLIC",
        "CommonProgramFiles",
        "CommonProgramFiles(x86)",
        "CommonProgramW6432",
        "ProgramW6432",
        "PSModulePath",
        "PATH",
        "SYSTEMROOT",
        "USERPROFILE",
        "HOME",
        "TEMP",
        "TMP",
        "PATHEXT",
        "SystemDrive",
        "WINDIR",
        "COMSPEC",
        "HOMEDRIVE",
        "HOMEPATH",
        "APPDATA",
        "LOCALAPPDATA",
        "PROGRAMDATA",
        "ProgramFiles",
        "ProgramFiles(x86)",
        "UV_CACHE_DIR",
        "UV_PYTHON_INSTALL_DIR",
        "PNPM_HOME",
        "XDG_CACHE_HOME",
        "CLAUDE_CONFIG_DIR",
        "DISABLE_AUTOUPDATER",
    } == set(ALLOWED_ENV)
    assert "GH_CONFIG_DIR" == GH_CONFIG_VAR


# --- 회차 폴더 지우기 ---


def _지우기(root: Path, records: Path) -> Removal:
    """있는 뿌리에서 지우고 보고를 낸다. 없는 뿌리의 `None`은 따로 본다."""
    report = remove_round_dirs(root, records)
    assert report is not None, f"뿌리가 없다고 읽었다: {root}"
    return report


def test_기록이_있는_회차_폴더만_지우고_나머지는_이름을_보고한다(tmp_path: Path) -> None:
    root = tmp_path / "뿌리"
    records = tmp_path / "records"
    done = _기록된_회차(root, records, "d1")
    waiting = create_round_dir(root, TASK, "A", 2, token="d2")
    plain = root / "표지없음"
    plain.mkdir()
    (plain / "남길것.txt").write_text("그대로\n", encoding="utf-8")
    (root / "파일.txt").write_text("그대로\n", encoding="utf-8")
    report = _지우기(root, records)
    assert report.removed == [done.name]
    assert not done.path.exists()
    assert report.no_record == [waiting.name]
    assert (waiting.path / MARKER).exists()
    assert sorted(report.not_round) == ["파일.txt", "표지없음"]
    assert (plain / "남길것.txt").read_text(encoding="utf-8") == "그대로\n"
    assert report.failed == []


def test_기록_없는_회차_폴더는_지우기의_기록_없음과_같은_판정이다(tmp_path: Path) -> None:
    root = tmp_path / "뿌리"
    records = tmp_path / "records"
    _기록된_회차(root, records, "u1")
    waiting = create_round_dir(root, TASK, "A", 2, token="u2")
    other = create_round_dir(root, TASK, "B", 1, token="u3")
    (root / "표지없음").mkdir()
    (root / "파일.txt").write_text("그대로\n", encoding="utf-8")
    found = unrecorded_round_dirs(root, records)
    assert [p.name for p in found] == sorted([waiting.name, other.name])
    assert [p.path for p in found] == [root / p.name for p in found]
    assert unrecorded_round_dirs(tmp_path / "없음", records) == []


def test_기록의_폴더_이름이_다르면_지우지_않는다(tmp_path: Path) -> None:
    root = tmp_path / "뿌리"
    records = tmp_path / "records"
    records.mkdir()
    place = create_round_dir(root, TASK, "A", 1, token="f1")
    write_record(records, _기록(f"{TASK}-A-1-zz9"))
    report = _지우기(root, records)
    assert report.removed == []
    assert report.no_record == [place.name]
    assert place.path.exists()


def test_읽지_못하는_기록이면_지우지_않는다(tmp_path: Path) -> None:
    root = tmp_path / "뿌리"
    records = tmp_path / "records"
    records.mkdir()
    place = create_round_dir(root, TASK, "A", 1, token="f2")
    (records / record_file_name(TASK, "A", 1)).write_text("{}", encoding="utf-8")
    report = _지우기(root, records)
    assert report.no_record == [place.name]
    assert place.path.exists()


def test_표지의_내용이_폴더_이름이_아니거나_표지가_폴더면_회차_폴더가_아니다(
    tmp_path: Path,
) -> None:
    root = tmp_path / "뿌리"
    records = tmp_path / "records"
    other = _기록된_회차(root, records, "g1")
    wrong = _기록된_회차(root, records, "g2", round_no=2)
    (wrong.path / MARKER).write_text(other.name, encoding="utf-8")
    folder = _기록된_회차(root, records, "g3", round_no=3)
    (folder.path / MARKER).unlink()
    (folder.path / MARKER).mkdir()
    report = _지우기(root, records)
    assert report.removed == [other.name]
    assert report.not_round == sorted([wrong.name, folder.name])
    assert wrong.path.exists() and folder.path.exists()


def test_회차_폴더_안의_링크는_링크만_끊고_바깥_파일은_남긴다(tmp_path: Path) -> None:
    root = tmp_path / "뿌리"
    records = tmp_path / "records"
    outside = tmp_path / "바깥"
    outside.mkdir()
    (outside / "남을것.txt").write_text("바깥\n", encoding="utf-8")
    place = _기록된_회차(root, records, "h1")
    _바깥_링크(place.path / "clone" / "node_modules" / "링크", outside)
    report = _지우기(root, records)
    assert report.removed == [place.name]
    assert not place.path.exists()
    assert (outside / "남을것.txt").read_text(encoding="utf-8") == "바깥\n"


def test_뿌리_바로_아래의_링크는_따라가지도_끊지도_않는다(tmp_path: Path) -> None:
    elsewhere = tmp_path / "다른뿌리"
    records = tmp_path / "records"
    target = _기록된_회차(elsewhere, records, "i1")
    root = tmp_path / "뿌리"
    root.mkdir()
    _바깥_링크(root / target.name, target.path)
    report = _지우기(root, records)
    assert report.removed == []
    assert report.not_round == [target.name]
    assert (target.path / MARKER).exists()
    assert (root / target.name).exists()


def test_읽기_전용_파일과_git_저장소가_든_회차_폴더도_지운다(
    tmp_path: Path, 원본: tuple[Path, str, str]
) -> None:
    repo, b, m = 원본
    root = tmp_path / "뿌리"
    records = tmp_path / "records"
    place = _기록된_회차(root, records, "j1")
    build_clone(repo, b, m, place)
    locked = place.path / "읽기전용.txt"
    locked.write_text("x\n", encoding="utf-8")
    locked.chmod(0o444)
    report = _지우기(root, records)
    assert report.removed == [place.name]
    assert not place.path.exists()


def test_뿌리로_준_홈에서도_회차_폴더만_지운다(tmp_path: Path) -> None:
    home = tmp_path / "home"
    records = tmp_path / "records"
    (home / ".claude" / "projects").mkdir(parents=True)
    (home / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    (home / "문서").mkdir()
    (home / "문서" / "중요.txt").write_text("중요\n", encoding="utf-8")
    place = _기록된_회차(home, records, "k1")
    report = _지우기(home, records)
    assert report.removed == [place.name]
    assert (home / ".claude" / "settings.json").exists()
    assert (home / "문서" / "중요.txt").read_text(encoding="utf-8") == "중요\n"
    assert sorted(report.not_round) == [".claude", "문서"]


def _글자_그대로(path: Path) -> str:
    if sys.platform == "win32":
        return "\\\\?\\" + str(path)
    return str(path)


def test_윈도가_접는_끝의_점이_든_이름은_다른_폴더로_본다(tmp_path: Path) -> None:
    """`x.`는 윈도에서 `\\\\?\\` 없이는 `x`로 읽힌다. 지우기는 그 둘을 섞지 않는다."""
    root = tmp_path / "뿌리"
    records = tmp_path / "records"
    place = _기록된_회차(root, records, "l1")
    dotted = _글자_그대로(root / (place.name + "."))
    os.mkdir(dotted)
    with open(os.path.join(dotted, MARKER), "w", encoding="utf-8") as f:
        f.write(place.name + ".")
    with open(os.path.join(dotted, "남길것.txt"), "w", encoding="utf-8") as f:
        f.write("그대로\n")
    report = _지우기(root, records)
    assert report.removed == [place.name]
    assert report.not_round == [place.name + "."]
    with open(os.path.join(dotted, "남길것.txt"), encoding="utf-8") as f:
        assert f.read() == "그대로\n"


def test_지우다_막히면_표지를_남겨_다시_지울_수_있다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "뿌리"
    records = tmp_path / "records"
    place = _기록된_회차(root, records, "m1")
    (place.path / "막힘").mkdir()

    def blocked(path: Path) -> None:
        if path.name == "막힘":
            raise PermissionError("다른 프로세스가 쥐었다")
        delete_path(path)

    monkeypatch.setattr(rerun_round, "delete_path", blocked)
    report = _지우기(root, records)
    assert report.removed == []
    assert [name for name, _ in report.failed] == [place.name]
    assert report.failed[0][1] == "PermissionError: 다른 프로세스가 쥐었다"
    assert (place.path / MARKER).exists()
    monkeypatch.undo()
    assert _지우기(root, records).removed == [place.name]


def test_링크를_찾다_막힌_회차_폴더만_실패로_알리고_다음_폴더는_지운다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """링크를 찾는 걸음(`cut_links`)이 항목을 판정하다 OSError를 내는 길을 흉내 낸다. 새 회차
    폴더에는 링크가 없으니 막지 않는 폴더에서는 끊지 못한 것이 없다고 돌려준다."""
    root = tmp_path / "뿌리"
    records = tmp_path / "records"
    stuck = _기록된_회차(root, records, "k1", round_no=1)
    next_one = _기록된_회차(root, records, "k2", round_no=2)

    def blocked(folder: str) -> list[str]:
        if os.path.basename(folder) == stuck.name:
            raise PermissionError(5, "항목을 판정하지 못했다")
        return []

    monkeypatch.setattr(rerun_round, "cut_links", blocked)
    report = _지우기(root, records)
    assert [name for name, _ in report.failed] == [stuck.name]
    assert "PermissionError" in report.failed[0][1]
    assert (stuck.path / MARKER).exists()
    assert report.removed == [next_one.name]
    assert not next_one.path.exists()


def test_대소문자만_다른_표지는_표지가_아니다(tmp_path: Path) -> None:
    """윈도는 표지를 열 때 대소문자를 가리지 않는다. 지울 때 맨 끝에 남길 표지는 글자 그대로의
    이름으로 고르므로, 둘이 어긋나면 표지를 먼저 지워 막혔을 때 다시 부를 수 없다."""
    root = tmp_path / "뿌리"
    records = tmp_path / "records"
    place = _기록된_회차(root, records, "u1")
    os.rename(place.path / MARKER, place.path / MARKER.upper())
    report = _지우기(root, records)
    assert report.not_round == [place.name]
    assert (place.path / MARKER.upper()).exists()


def test_마지막_폴더_지우기가_막히면_표지를_다시_심어_다시_지울_수_있다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """다른 프로세스가 회차 폴더를 작업 디렉터리로 쥐면 윈도에서는 안을 다 지운 뒤 rmdir 만
    막힌다."""
    root = tmp_path / "뿌리"
    records = tmp_path / "records"
    place = _기록된_회차(root, records, "w1")
    real = os.rmdir

    def blocked(path: str, *, dir_fd: int | None = None) -> None:
        if os.path.basename(path) == place.name:
            raise PermissionError(32, "다른 프로세스가 쥐었다")
        real(path, dir_fd=dir_fd)

    monkeypatch.setattr(os, "rmdir", blocked)
    report = _지우기(root, records)
    assert [name for name, _ in report.failed] == [place.name]
    assert (place.path / MARKER).read_text(encoding="utf-8") == place.name
    monkeypatch.undo()
    assert _지우기(root, records).removed == [place.name]
    assert not place.path.exists()


def test_읽기_전용_특성이_붙은_회차_폴더도_지운다(tmp_path: Path) -> None:
    """윈도의 폴더 읽기 전용 특성은 rmdir 를 막는다. 리눅스에는 이 특성이 없어 그대로 지운다."""
    root = tmp_path / "뿌리"
    records = tmp_path / "records"
    place = _기록된_회차(root, records, "w2")
    if sys.platform == "win32":
        os.chmod(place.path, stat.S_IREAD)
        assert os.stat(place.path).st_file_attributes & stat.FILE_ATTRIBUTE_READONLY
    assert _지우기(root, records).removed == [place.name]
    assert not place.path.exists()


def test_판정_뒤_링크로_바뀐_회차_폴더는_지우지_않는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """판정과 지우기 사이에 폴더를 옮기고 그 이름에 바깥을 가리키는 링크를 놓는 경쟁을 흉내 낸다."""
    root = tmp_path / "뿌리"
    records = tmp_path / "records"
    place = _기록된_회차(root, records, "w3")
    outside = tmp_path / "바깥"
    outside.mkdir()
    (outside / "남을것.txt").write_text("바깥\n", encoding="utf-8")

    def swapped(path: Path) -> Record:
        record = read_record(path)
        os.rename(place.path, tmp_path / "옮긴것")
        _바깥_링크(place.path, outside)
        return record

    monkeypatch.setattr(rerun_round, "read_record", swapped)
    report = _지우기(root, records)
    assert [name for name, _ in report.failed] == [place.name]
    # 링크 끊기(`cut_links`)도 뿌리가 링크면 멈추므로, 지우기 직전의 확인이 막았는지는 까닭으로 본다
    assert "판정한 뒤 링크로 바뀌어" in report.failed[0][1]
    assert (outside / "남을것.txt").read_text(encoding="utf-8") == "바깥\n"
    assert os.path.lexists(place.path)


def test_끊지_못한_링크가_있으면_끊을_수_있던_링크만_끊고_아무것도_지우지_않는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """남길 파일 이름은 `clone`보다 앞서 정렬되게 지어, 멈추지 않으면 먼저 지워지게 한다."""
    root = tmp_path / "뿌리"
    records = tmp_path / "records"
    outside = tmp_path / "바깥"
    outside.mkdir()
    (outside / "남을것.txt").write_text("바깥\n", encoding="utf-8")
    place = _기록된_회차(root, records, "w4")
    _바깥_링크(place.path / "끊을링크", outside)
    _바깥_링크(place.path / "clone" / "막힌링크", outside)
    kept = place.path / "a-남길것.txt"
    kept.write_text("그대로\n", encoding="utf-8")
    real = os.unlink

    def blocked(path: str, *, dir_fd: int | None = None) -> None:
        if os.path.basename(path) == "막힌링크":
            raise PermissionError(5, "끊지 못했다")
        real(path, dir_fd=dir_fd)

    monkeypatch.setattr(os, "unlink", blocked)
    report = _지우기(root, records)
    assert [name for name, _ in report.failed] == [place.name]
    assert kept.exists()
    assert "끊지 못한 링크" in report.failed[0][1]
    assert not os.path.lexists(place.path / "끊을링크")
    assert (place.path / MARKER).exists()
    monkeypatch.undo()
    assert _지우기(root, records).removed == [place.name]
    assert (outside / "남을것.txt").read_text(encoding="utf-8") == "바깥\n"


def test_파일인_뿌리는_멈춘다(tmp_path: Path) -> None:
    root = tmp_path / "뿌리.txt"
    root.write_text("", encoding="utf-8")
    with pytest.raises(PlaceError, match="폴더가 아니다"):
        _지우기(root, tmp_path / "records")
    assert main(["remove", str(root), "--records", str(tmp_path / "records")]) == 2


def test_읽지_못하는_뿌리는_멈춘다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "뿌리"
    root.mkdir()

    def denied(path: str) -> None:
        raise PermissionError(13, "읽기 거부", path)

    monkeypatch.setattr(os, "scandir", denied)
    with pytest.raises(PlaceError, match="뿌리를 읽지 못했다"):
        _지우기(root, tmp_path / "records")
    assert main(["remove", str(root), "--records", str(tmp_path / "records")]) == 2


def test_뿌리_자체가_링크면_따라가_그_안의_회차_폴더를_지운다(tmp_path: Path) -> None:
    """못 보는 것: 뿌리 자체의 링크는 따라간다(명령 줄은 링크를 푼 꼴도 머리 견줌을 거친다)."""
    real = tmp_path / "진짜뿌리"
    records = tmp_path / "records"
    place = _기록된_회차(real, records, "y1")
    _바깥_링크(tmp_path / "링크뿌리", real)
    assert _지우기(tmp_path / "링크뿌리", records).removed == [place.name]
    assert not place.path.exists()


def test_records가_링크면_따라가_기록을_읽는다(tmp_path: Path) -> None:
    """못 보는 것: `records/`의 링크도 따라간다."""
    root = tmp_path / "뿌리"
    real_records = tmp_path / "진짜기록"
    place = _기록된_회차(root, real_records, "y2")
    _바깥_링크(tmp_path / "링크기록", real_records)
    assert _지우기(root, tmp_path / "링크기록").removed == [place.name]


def test_바깥_파일의_하드_링크를_지우면_윈도에서만_그_읽기_전용_특성이_풀린다(
    tmp_path: Path,
) -> None:
    """못 보는 것: 윈도는 읽기 전용 파일을 특성을 풀고 지워, 같은 파일인 바깥 하드 링크도 풀린다.
    리눅스는 쓰기 가능한 폴더 안의 읽기 전용 파일을 풀지 않고 지운다. 내용은 어느 쪽이든 남는다."""
    root = tmp_path / "뿌리"
    records = tmp_path / "records"
    outside = tmp_path / "캐시.txt"
    outside.write_text("캐시\n", encoding="utf-8")
    outside.chmod(stat.S_IREAD)
    place = _기록된_회차(root, records, "y3")
    os.link(outside, place.path / "링크된.txt")
    try:
        assert _지우기(root, records).removed == [place.name]
        assert outside.read_text(encoding="utf-8") == "캐시\n"
        assert bool(os.stat(outside).st_mode & stat.S_IWRITE) == (sys.platform == "win32")
    finally:
        outside.chmod(stat.S_IREAD | stat.S_IWRITE)


def test_없는_뿌리는_보고가_없다(tmp_path: Path) -> None:
    assert remove_round_dirs(tmp_path / "없음", tmp_path / "records") is None


# --- 명령 줄 ---


def test_지우기_명령은_상대_경로_뿌리에서_아무것도_하지_않고_2로_끝난다(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["remove", "rerun"]) == 2
    assert "절대 경로" in capsys.readouterr().err


def test_지우기_명령은_없는_뿌리를_알리고_0으로_끝난다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """뿌리를 잘못 친 것이 아무 출력 없이 성공처럼 보이지 않게 한다."""
    root = tmp_path / "없음"
    assert main(["remove", str(root), "--records", str(tmp_path / "records")]) == 0
    assert f"뿌리가 없어 지울 것이 없다: {root}" in capsys.readouterr().err


def test_지우기_명령은_대상을_잃은_링크_뿌리를_없는_뿌리로_알린다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """뿌리의 이름은 있어도 그 링크가 가리키던 폴더가 없으면 읽을 것이 없는 뿌리다."""
    target = tmp_path / "대상"
    target.mkdir()
    root = tmp_path / "링크뿌리"
    _바깥_링크(root, target)
    target.rmdir()
    assert main(["remove", str(root), "--records", str(tmp_path / "records")]) == 0
    assert f"뿌리가 없어 지울 것이 없다: {root}" in capsys.readouterr().err


def test_지우기_명령은_없다고_가를_수_없는_뿌리에서_2로_끝난다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """모든 오류를 없음으로 읽으면 읽지 못한 뿌리가 없는 뿌리처럼 0으로 끝난다. 윈도는 이름에 쓸 수
    없는 글자로, 리눅스는 파일 아래의 경로로 본다."""
    (tmp_path / "파일").write_text("", encoding="utf-8")
    if sys.platform == "win32":
        root, why = tmp_path / "a<b", "뿌리를 읽지 못했다"
    else:
        root, why = tmp_path / "파일" / "아래", "뿌리가 폴더가 아니다"
    assert main(["remove", str(root), "--records", str(tmp_path / "records")]) == 2
    assert f"끝: {why}: {root}" in capsys.readouterr().err


def test_지우기_명령은_지운_것과_남긴_것을_찍는다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "뿌리"
    records = tmp_path / "records"
    done = _기록된_회차(root, records, "q1")
    waiting = create_round_dir(root, TASK, "A", 2, token="q2")
    assert main(["remove", str(root), "--records", str(records)]) == 0
    out = capsys.readouterr().out
    assert f"지웠다: {done.name}" in out
    assert f"기록이 없어 남겼다: {waiting.name}" in out
    assert not done.path.exists()


def test_지우기_명령을_프로세스로_부른다(tmp_path: Path) -> None:
    root = tmp_path / "뿌리"
    records = tmp_path / "records"
    done = _기록된_회차(root, records, "t1")
    checkout = Path(rerun_round.__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-m", "tools.rerun_round", "remove", str(root), "--records", str(records)],
        cwd=checkout,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert f"지웠다: {done.name}" in result.stdout
    assert not done.path.exists()


def test_지우기_명령은_utf8_모드가_없어도_cp949_밖의_이름을_찍는다(tmp_path: Path) -> None:
    """윈도의 파이프는 PYTHONUTF8·PYTHONIOENCODING 이 없으면 로캘의 인코딩(이 PC 는 cp949)이라,
    출력을 UTF-8로 고정하지 않으면 이름을 찍다 `UnicodeEncodeError`로 끝난다. UTF-8 모드는 0으로
    꺼 둔다."""
    root = tmp_path / "뿌리"
    (root / "남길😀").mkdir(parents=True)
    checkout = Path(rerun_round.__file__).resolve().parents[1]
    env = {k: v for k, v in os.environ.items() if k != "PYTHONIOENCODING"}
    result = subprocess.run(
        [sys.executable, "-m", "tools.rerun_round", "remove", str(root)],
        cwd=checkout,
        capture_output=True,
        env={**env, "PYTHONUTF8": "0"},
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    assert "회차 폴더가 아니라 남겼다: 남길😀" in result.stdout.decode("utf-8")
