"""`tools/check_ticket.py` 를 임시 저장소의 진짜 `git commit` 으로 잰다.

임시 저장소(맨 원격 하나와 그 main)를 만들고, pre-commit 자리에 이 검사를 부르는 짧은 심을 두어
막힘과 지남, 막을 때의 글을 본다. 진짜 pre-commit 을 거쳐야 보이는 둘(스테이지하지 않은 고침을
치우는 것, 일부 파일만 커밋할 때의 임시 색인이 러너를 거쳐 검사에 닿는 것)은 임시 저장소에
pre-commit 을 깔고 러너의 `run` 으로 이 검사 하나를 부르는 설정으로 본다(명세
`.scratch/ticket-for-every-pr/spec.md` "이음매").
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
from tools.run_hooks import REPO_LOCATION_VARS

ROOT = Path(__file__).resolve().parents[2]
CHECK = ROOT / "tools" / "check_ticket.py"
_IDENTITY = ("-c", "user.name=t", "-c", "user.email=t@example.com")
_TIMEOUT = 120

NUMBER_COMMAND = "uv run python tools/sibling_overlap.py"
BRANCH_COMMAND = "git branch -m"
CONVENTION = "docs/agents/issue-tracker.md"
NOTICE = "in-progress"

READY = "# 02: 일\n\n**Status:** ready-for-agent\n"
SEED = {
    "README.md": "읽어 보기\n",
    "tools/a.py": "A = 1\n",
    "docs/journal/2026-01-01-01-seed.md": "씨앗\n",
    ".scratch/feat/issues/02-thing.md": READY,
    ".scratch/harness/issues/001-old.md": "# 001: 옛 일\n\n**Status:** done\n",
}
# 브랜치를 딴 자리의 트리에 이 파일이 있으면 규약 뒤의 브랜치다. 내용은 보지 않는다
CHECK_MARK = {"tools/check_ticket.py": "# 검사 자리\n"}


@dataclass
class Repo:
    tmp: Path
    work: Path
    pusher: Path | None
    env: dict[str, str]

    def git(self, *args: str, cwd: Path | None = None, check: bool = True) -> str:
        result = subprocess.run(
            ["git", *_IDENTITY, *args],
            cwd=cwd or self.work,
            env=self.env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=_TIMEOUT,
            check=False,
        )
        if check and result.returncode != 0:
            raise AssertionError(f"git {' '.join(args)}: {result.stdout}{result.stderr}")
        return result.stdout.strip()

    def write(self, files: dict[str, str], cwd: Path | None = None) -> None:
        for name, text in files.items():
            path = (cwd or self.work) / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")

    def commit(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        """진짜 커밋. 훅이 막으면 0이 아닌 코드로 돌아온다."""
        return subprocess.run(
            ["git", *_IDENTITY, "commit", "-q", *args],
            cwd=cwd or self.work,
            env=self.env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=_TIMEOUT,
            check=False,
        )

    def stage_commit(
        self, files: dict[str, str], cwd: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        self.write(files, cwd)
        self.git("add", "-A", cwd=cwd)
        return self.commit("-m", "x", cwd=cwd)

    def push_main(self, files: dict[str, str]) -> None:
        """원격의 main 에 커밋 하나를 더하고 작업 클론이 가져온다."""
        assert self.pusher is not None
        self.write(files, self.pusher)
        self.git("add", "-A", cwd=self.pusher)
        self.git("commit", "-q", "-m", "main", cwd=self.pusher)
        self.git("push", "-q", "origin", "main", cwd=self.pusher)
        self.git("fetch", "-q", "origin")


def _env(tmp_path: Path) -> dict[str, str]:
    """저장소를 가리키는 변수를 벗기고 사용자·시스템 설정을 끊는다(사용자의 `core.hooksPath` 등)."""
    env = {k: v for k, v in os.environ.items() if k not in REPO_LOCATION_VARS}
    empty = tmp_path / "gitconfig"
    empty.write_text("", encoding="utf-8")
    env["GIT_CONFIG_GLOBAL"] = str(empty)
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["PRE_COMMIT_HOME"] = str(tmp_path / "pre-commit-home")
    return env


def _shim(repo: Repo) -> None:
    """pre-commit 자리에 이 검사를 바로 부르는 심. 리눅스의 git 은 실행 권한이 없는 훅을
    건너뛴다."""
    hooks = repo.tmp / "hooks"
    hooks.mkdir(exist_ok=True)
    shim = hooks / "pre-commit"
    shim.write_text(
        f'#!/bin/sh\nexec "{Path(sys.executable).as_posix()}" "{CHECK.as_posix()}"\n',
        encoding="utf-8",
        newline="\n",
    )
    shim.chmod(0o755)
    repo.git("config", "core.hooksPath", hooks.as_posix())


def _repo(tmp_path: Path, seed: dict[str, str], *, hook: bool = True) -> Repo:
    """원격과 그 main, 작업 클론. 작업 클론은 main 에 있다."""
    env = _env(tmp_path)
    remote = tmp_path / "origin.git"
    repo = Repo(tmp_path, tmp_path / "work", tmp_path / "pusher", env)
    repo.git("init", "-q", "--bare", "-b", "main", str(remote), cwd=tmp_path)
    repo.git("init", "-q", "-b", "main", str(repo.pusher), cwd=tmp_path)
    repo.git("remote", "add", "origin", str(remote), cwd=repo.pusher)
    repo.write(seed, repo.pusher)
    repo.git("add", "-A", cwd=repo.pusher)
    repo.git("commit", "-q", "-m", "씨앗", cwd=repo.pusher)
    repo.git("push", "-q", "origin", "main", cwd=repo.pusher)
    repo.git("clone", "-q", str(remote), str(repo.work), cwd=tmp_path)
    if hook:
        _shim(repo)
    return repo


@pytest.fixture
def 저장소(tmp_path: Path) -> Repo:
    """검사가 든 main 에서 딴 저장소."""
    return _repo(tmp_path, {**SEED, **CHECK_MARK})


BLOCKED = "커밋을 막았다"


def _막혔다(result: subprocess.CompletedProcess[str]) -> str:
    """판정 7 로 막혔다. git 이 실패해 2 로 끝난 것은 막힘으로 세지 않는다."""
    out = result.stdout + result.stderr
    assert result.returncode != 0, f"지나면 안 된다: {out}"
    assert BLOCKED in out, f"막는 글이 아니다: {out}"
    return out


def _지났다(result: subprocess.CompletedProcess[str]) -> str:
    assert result.returncode == 0, f"막히면 안 된다: {result.stdout}{result.stderr}"
    return result.stdout + result.stderr


# --- 면제 모양 -------------------------------------------------------------------


def test_면제_모양만_바꾼_커밋은_지난다(저장소: Repo) -> None:
    저장소.git("switch", "-q", "-c", "docs/design")
    _지났다(
        저장소.stage_commit(
            {
                "docs/journal/2026-01-02-01-x.md": "일지\n",
                ".scratch/retro-queue.md": "대기열\n",
                "docs/adr/0002-x.md": "결정\n",
                "docs/adr/README.md": "색인\n",
                "CONTEXT.md": "용어\n",
                ".scratch/plan.md": "계획\n",
                "docs/PRD.md": "범위\n",
                "docs/constitution/tech.md": "스택\n",
                "docs/constitution/README.md": "판\n",
                ".scratch/feat/spec.md": "명세\n",
                ".scratch/feat/issues/03-next.md": READY,
                ".scratch/feat/probes/deep/p.py": "P = 1\n",
                ".scratch/feat/design/a.html": "<p>화면</p>\n",
            }
        )
    )


@pytest.mark.parametrize(
    "path",
    [".scratch/harness/spec.md", ".scratch/harness/probes/p.py", ".scratch/feat/design.md"],
)
def test_면제_모양_밖의_scratch_파일을_섞으면_막는다(저장소: Repo, path: str) -> None:
    저장소.git("switch", "-q", "-c", "docs/design")
    out = _막혔다(저장소.stage_commit({"docs/journal/2026-01-02-01-x.md": "일지\n", path: "x\n"}))
    assert path in out


def test_이름_바꾸기는_지운_것과_더한_것으로_센다(저장소: Repo) -> None:
    저장소.git("switch", "-q", "-c", "docs/design")
    저장소.git("mv", "tools/a.py", "docs/journal/2026-01-02-01-a.md")
    out = _막혔다(저장소.commit("-m", "x"))
    assert "tools/a.py" in out


# --- 티켓 모양 브랜치 --------------------------------------------------------------


def test_chore_브랜치가_그_티켓을_실으면_지난다(저장소: Repo) -> None:
    저장소.git("switch", "-q", "-c", "chore/002-thing")
    _지났다(
        저장소.stage_commit(
            {".scratch/harness/issues/002-thing.md": "# 002\n", "tools/b.py": "B = 1\n"}
        )
    )


def test_chore_브랜치가_티켓을_빠뜨리면_막고_할_일을_든다(저장소: Repo) -> None:
    저장소.git("switch", "-q", "-c", "chore/002-thing")
    out = _막혔다(저장소.stage_commit({"tools/b.py": "B = 1\n"}))
    assert "tools/b.py" in out
    assert ".scratch/harness/issues/002-thing.md" in out
    assert NUMBER_COMMAND in out
    assert BRANCH_COMMAND in out
    assert CONVENTION in out


def test_다른_번호의_티켓은_가리키지_않는다(저장소: Repo) -> None:
    저장소.git("switch", "-q", "-c", "chore/002-thing")
    _막혔다(
        저장소.stage_commit(
            {".scratch/harness/issues/003-thing.md": "# 003\n", "tools/b.py": "B = 1\n"}
        )
    )


def test_지운_티켓은_가리키지_않는다(저장소: Repo) -> None:
    저장소.git("switch", "-q", "-c", "feature/02-thing")
    저장소.git("rm", "-q", ".scratch/feat/issues/02-thing.md")
    저장소.write({"tools/b.py": "B = 1\n"})
    저장소.git("add", "-A")
    _막혔다(저장소.commit("-m", "x"))


def test_feature_브랜치는_어느_기능_폴더의_같은_이름_티켓으로도_지난다(저장소: Repo) -> None:
    저장소.git("switch", "-q", "-c", "feature/05-other")
    _지났다(
        저장소.stage_commit(
            {".scratch/elsewhere/issues/05-other.md": READY, "tools/b.py": "B = 1\n"}
        )
    )


def test_docs_브랜치는_harness_티켓을_하나라도_실으면_지난다(저장소: Repo) -> None:
    저장소.git("switch", "-q", "-c", "docs/retro")
    _지났다(
        저장소.stage_commit(
            {".scratch/harness/issues/009-anything.md": "# 009\n", "tools/b.py": "B = 1\n"}
        )
    )


def test_docs_브랜치는_이미_있는_harness_티켓을_고치기만_해도_지난다(저장소: Repo) -> None:
    # 못 보는 것: 회고 반영이 아닌 일을 실어도 지난다
    저장소.git("switch", "-q", "-c", "docs/retro")
    _지났다(
        저장소.stage_commit(
            {".scratch/harness/issues/001-old.md": "# 001: 고쳤다\n", "tools/b.py": "B = 1\n"}
        )
    )


@pytest.mark.parametrize(
    "path",
    [
        ".scratch/harness/issues/README.md",
        ".scratch/harness/issues/sub/009-x.md",
        ".scratch/harness/issues/009-x.txt",
        ".scratch/harness/issues/09-x.md",
    ],
)
def test_docs_브랜치는_harness_티켓_모양이_아닌_파일로는_지나지_않는다(
    저장소: Repo, path: str
) -> None:
    저장소.git("switch", "-q", "-c", "docs/retro")
    _막혔다(저장소.stage_commit({path: "x\n", "tools/b.py": "B = 1\n"}))


def test_면제_밖_파일이_열_개를_넘으면_나머지_수를_든다(저장소: Repo) -> None:
    저장소.git("switch", "-q", "-c", "docs/many")
    out = _막혔다(저장소.stage_commit({f"tools/m{i:02}.py": "M = 1\n" for i in range(12)}))
    assert "tools/m09.py" in out
    assert "tools/m10.py" not in out
    assert "그 밖에 2개" in out


def test_앱_워크트리_모양의_브랜치는_막는다(저장소: Repo) -> None:
    저장소.git("switch", "-q", "-c", "claude/happy-dijkstra")
    out = _막혔다(저장소.stage_commit({"tools/b.py": "B = 1\n"}))
    assert NUMBER_COMMAND in out and BRANCH_COMMAND in out


# --- 디스크에는 있는데 커밋에 들지 않은 티켓 -----------------------------------------------


def test_고치지_않은_ready_for_agent_티켓은_알린다(저장소: Repo) -> None:
    저장소.git("switch", "-q", "-c", "feature/02-thing")
    out = _막혔다(저장소.stage_commit({"tools/a.py": "A = 2\n"}))
    assert ".scratch/feat/issues/02-thing.md" in out
    assert NOTICE in out


def test_한_번도_add하지_않은_새_티켓은_알린다(저장소: Repo) -> None:
    저장소.git("switch", "-q", "-c", "chore/002-new")
    저장소.write({".scratch/harness/issues/002-new.md": "# 002\n", "tools/a.py": "A = 2\n"})
    저장소.git("add", "tools/a.py")
    out = _막혔다(저장소.commit("-m", "x"))
    assert ".scratch/harness/issues/002-new.md" in out
    assert NOTICE in out


# --- 커밋의 길 -------------------------------------------------------------------


def test_일부_파일만_커밋하면_그_커밋에_들_것만_본다(저장소: Repo) -> None:
    저장소.git("switch", "-q", "-c", "feature/02-thing")
    ticket = ".scratch/feat/issues/02-thing.md"
    저장소.write({ticket: READY.replace("ready-for-agent", "in-progress"), "tools/a.py": "A = 2\n"})
    # 색인에는 티켓이 있지만 `git commit <경로>` 는 HEAD 에 그 경로만 얹은 임시 색인으로 커밋한다
    저장소.git("add", ticket)
    _막혔다(저장소.commit("-m", "x", "--", "tools/a.py"))
    _지났다(저장소.commit("-m", "x", "--", "tools/a.py", ticket))


def test_a_옵션은_고친_추적_파일을_모두_본다(저장소: Repo) -> None:
    저장소.git("switch", "-q", "-c", "feature/02-thing")
    저장소.write({"tools/a.py": "A = 2\n"})
    _막혔다(저장소.commit("-a", "-m", "x"))
    저장소.write(
        {".scratch/feat/issues/02-thing.md": READY.replace("ready-for-agent", "in-progress")}
    )
    _지났다(저장소.commit("-a", "-m", "x"))


def test_amend는_merge_base에서_고친_색인까지를_본다(저장소: Repo) -> None:
    저장소.git("switch", "-q", "-c", "chore/002-thing")
    ticket = ".scratch/harness/issues/002-thing.md"
    _지났다(저장소.stage_commit({ticket: "# 002\n", "tools/b.py": "B = 1\n"}))
    저장소.write({"tools/b.py": "B = 2\n"})
    _지났다(저장소.commit("-a", "--amend", "--no-edit"))
    저장소.git("rm", "-q", "--cached", ticket)
    _막혔다(저장소.commit("--amend", "--no-edit"))


# --- 지나는 자리 -----------------------------------------------------------------


def test_분리_HEAD는_지난다(저장소: Repo) -> None:
    저장소.git("switch", "-q", "--detach")
    _지났다(저장소.stage_commit({"tools/b.py": "B = 1\n"}))


def test_main은_지난다(저장소: Repo) -> None:
    _지났다(저장소.stage_commit({"tools/b.py": "B = 1\n"}))


def test_origin_main이_없으면_알리고_지난다(tmp_path: Path) -> None:
    repo = Repo(tmp_path, tmp_path / "solo", None, _env(tmp_path))
    repo.git("init", "-q", "-b", "main", str(repo.work), cwd=tmp_path)
    repo.write({**SEED, **CHECK_MARK})
    repo.git("add", "-A")
    repo.git("commit", "-q", "-m", "씨앗")
    _shim(repo)
    repo.git("switch", "-q", "-c", "topic")
    out = _지났다(repo.stage_commit({"tools/b.py": "B = 1\n"}))
    assert "origin/main" in out


def test_얕은_클론에서_merge_base가_없으면_알리고_지난다(저장소: Repo) -> None:
    """딴 자리가 깊이 밖이면 공통 조상이 없어 보인다. 빈 트리에서 세면 C 가 저장소 전체가 된다."""
    assert 저장소.pusher is not None
    저장소.git("switch", "-q", "-c", "chore/002-thing", cwd=저장소.pusher)
    저장소.write({"tools/b.py": "B = 1\n"}, 저장소.pusher)
    저장소.git("add", "-A", cwd=저장소.pusher)
    저장소.git("commit", "-q", "-m", "가지", cwd=저장소.pusher)
    저장소.git("push", "-q", "origin", "chore/002-thing", cwd=저장소.pusher)
    저장소.git("switch", "-q", "main", cwd=저장소.pusher)
    저장소.push_main({"docs/journal/2026-01-02-01-main.md": "main\n"})
    shallow = 저장소.tmp / "shallow"
    remote = (저장소.tmp / "origin.git").as_uri()
    저장소.git("clone", "-q", "--depth", "1", "--no-single-branch", remote, str(shallow))
    repo = Repo(저장소.tmp, shallow, None, 저장소.env)
    _shim(repo)
    repo.git("switch", "-q", "chore/002-thing")
    _지났다(repo.stage_commit({"docs/journal/2026-01-03-01-x.md": "x\n"}))
    result = _바로(repo)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "얕은 클론" in result.stdout


def test_고아_브랜치는_첫_커밋만_지나고_그_뒤는_뿌리의_트리로_판정을_받는다(저장소: Repo) -> None:
    # 못 보는 것: 첫 커밋은 HEAD 가 없어 지난다. `--orphan` 은 색인을 두어 뿌리가 검사를 든다
    저장소.git("checkout", "-q", "--orphan", "orphan-topic")
    out = _지났다(저장소.stage_commit({"tools/b.py": "B = 1\n"}))
    assert "HEAD" in out
    _막혔다(저장소.stage_commit({"tools/c.py": "C = 1\n"}))


def test_색인을_비우고_만든_고아_브랜치는_규약_전으로_지난다(저장소: Repo) -> None:
    # 못 보는 것: 뿌리의 트리에 이 검사가 없다
    저장소.git("checkout", "-q", "--orphan", "orphan-topic")
    저장소.git("rm", "-r", "-q", "--cached", ".")
    저장소.write({"tools/b.py": "B = 1\n"})
    저장소.git("add", "tools/b.py")
    _지났다(저장소.commit("-m", "x"))
    out = _지났다(저장소.stage_commit({"tools/c.py": "C = 1\n"}))
    assert "규약 전" in out


def test_고아_역사를_합친_보통_브랜치는_판정을_받는다(저장소: Repo) -> None:
    저장소.git("checkout", "-q", "--orphan", "orphan-topic")
    _지났다(저장소.stage_commit({"tools/b.py": "B = 1\n"}))
    저장소.git("switch", "-q", "-c", "docs/x", "origin/main")
    저장소.git(
        "merge", "-q", "--no-edit", "--allow-unrelated-histories", "-X", "ours", "orphan-topic"
    )
    _막혔다(저장소.stage_commit({"tools/c.py": "C = 1\n"}))


# --- 전환 -----------------------------------------------------------------------


@pytest.fixture
def 규약_전_브랜치(tmp_path: Path) -> Repo:
    """검사가 없던 main 에서 딴 `topic`. 그 뒤 원격의 main 에 검사가 들어왔다."""
    repo = _repo(tmp_path, SEED)
    repo.git("switch", "-q", "-c", "topic")
    repo.push_main(CHECK_MARK)
    return repo


def test_규약_전_브랜치는_지나고_main을_합친_뒤에도_지난다(규약_전_브랜치: Repo) -> None:
    out = _지났다(규약_전_브랜치.stage_commit({"tools/b.py": "B = 1\n"}))
    assert "규약 전" in out
    규약_전_브랜치.git("merge", "-q", "--no-edit", "origin/main")
    _지났다(규약_전_브랜치.stage_commit({"tools/c.py": "C = 1\n"}))


def test_자기_커밋이_없는_규약_전_브랜치는_HEAD를_딴_자리로_본다(규약_전_브랜치: Repo) -> None:
    out = _지났다(규약_전_브랜치.stage_commit({"tools/b.py": "B = 1\n"}))
    assert "규약 전" in out


def test_규약_전_브랜치를_rebase하면_판정을_받는다(규약_전_브랜치: Repo) -> None:
    _지났다(규약_전_브랜치.stage_commit({"tools/b.py": "B = 1\n"}))
    규약_전_브랜치.git("rebase", "-q", "origin/main")
    _막혔다(규약_전_브랜치.stage_commit({"tools/c.py": "C = 1\n"}))


def test_첫_자기_커밋은_날짜가_아니라_위상_순서로_고른다(규약_전_브랜치: Repo) -> None:
    # 이 티켓의 브랜치처럼 규약 전 브랜치가 첫 커밋에서 검사를 더했다. 둘째 커밋의 날짜가 더 이르면
    # 날짜로 고른 "첫 커밋" 은 둘째이고, 그 부모 트리에는 검사가 있어 막힌다
    _지났다(규약_전_브랜치.stage_commit(CHECK_MARK))
    early = "2020-01-01T00:00:00+0000"
    규약_전_브랜치.env["GIT_COMMITTER_DATE"] = early
    규약_전_브랜치.env["GIT_AUTHOR_DATE"] = early
    _지났다(규약_전_브랜치.stage_commit({"tools/b.py": "B = 1\n"}))
    del 규약_전_브랜치.env["GIT_COMMITTER_DATE"], 규약_전_브랜치.env["GIT_AUTHOR_DATE"]
    _지났다(규약_전_브랜치.stage_commit({"tools/c.py": "C = 1\n"}))


# --- 병합 -----------------------------------------------------------------------

JOURNAL = "docs/journal/2026-01-01-01-seed.md"


@pytest.mark.parametrize("place", ["클론", "링크드_워크트리"])
def test_충돌을_풀고_친_병합_커밋은_main이_들여온_파일을_세지_않는다(
    저장소: Repo, place: str
) -> None:
    if place == "클론":
        where = 저장소.work
        저장소.git("switch", "-q", "-c", "docs/journal-only")
    else:
        where = 저장소.tmp / "linked"
        저장소.git("worktree", "add", "-q", "-b", "docs/journal-only", str(where), "origin/main")
    _지났다(저장소.stage_commit({JOURNAL: "브랜치\n"}, cwd=where))
    저장소.push_main({JOURNAL: "main\n", "tools/new.py": "N = 1\n"})
    merged = subprocess.run(
        ["git", *_IDENTITY, "merge", "-q", "--no-edit", "origin/main"],
        cwd=where,
        env=저장소.env,
        capture_output=True,
        timeout=_TIMEOUT,
        check=False,
    )
    assert merged.returncode != 0, "충돌이 나야 한다"
    저장소.write({JOURNAL: "풀었다\n"}, cwd=where)
    저장소.git("add", JOURNAL, cwd=where)
    _지났다(저장소.commit("--no-edit", cwd=where))


def test_충돌_없는_병합은_훅이_돌지_않아_지난다(저장소: Repo) -> None:
    저장소.git("switch", "-q", "-c", "docs/journal-only")
    _지났다(저장소.stage_commit({"docs/journal/2026-01-02-01-x.md": "일지\n"}))
    저장소.push_main({"tools/new.py": "N = 1\n"})
    저장소.git("merge", "-q", "--no-edit", "origin/main")
    assert (저장소.work / "tools" / "new.py").is_file()


def test_워크트리에서의_커밋도_판정한다(저장소: Repo) -> None:
    where = 저장소.tmp / "linked"
    저장소.git("worktree", "add", "-q", "-b", "chore/002-thing", str(where), "origin/main")
    _막혔다(저장소.stage_commit({"tools/b.py": "B = 1\n"}, cwd=where))
    _지났다(저장소.stage_commit({".scratch/harness/issues/002-thing.md": "# 002\n"}, cwd=where))


# --- 바로 친다 -------------------------------------------------------------------


def _바로(repo: Repo) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECK)],
        cwd=repo.work,
        env=repo.env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=_TIMEOUT,
        check=False,
    )


def test_바로_치면_지금_색인으로_판정한다(저장소: Repo) -> None:
    저장소.git("switch", "-q", "-c", "chore/002-thing")
    저장소.write({"tools/b.py": "B = 1\n"})
    저장소.git("add", "-A")
    result = _바로(저장소)
    assert result.returncode == 1
    assert ".scratch/harness/issues/002-thing.md" in result.stderr


def test_저장소가_아닌_폴더에서는_git_실패로_2를_낸다(tmp_path: Path) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()
    env = {**_env(tmp_path), "GIT_CEILING_DIRECTORIES": str(tmp_path)}
    result = _바로(Repo(tmp_path, plain, None, env))
    assert result.returncode == 2, result.stdout + result.stderr
    assert "symbolic-ref" in result.stderr


def test_바로_치면_전환의_한_줄이_보인다(규약_전_브랜치: Repo) -> None:
    result = _바로(규약_전_브랜치)
    assert result.returncode == 0
    assert "규약 전" in result.stdout


# --- 진짜 pre-commit ------------------------------------------------------------

_ENTRY = """\
import os
import sys
from pathlib import Path

sys.path.insert(0, {root!r})
from tools.run_checks import Check, run

checks = [Check("check-ticket", (sys.executable, {check!r}))]
sys.exit(run(checks, os.environ, Path.cwd(), sys.stdout.buffer))
"""


@pytest.fixture
def pre_commit_저장소(tmp_path: Path) -> Repo:
    """pre-commit 을 깐 저장소. 그 설정은 러너의 `run` 에 이 검사 하나와 임시 저장소를 넘긴다.

    러너의 `main` 은 작업 폴더를 이 저장소의 루트로 고정해 임시 저장소가 아니라 이 저장소를
    판정한다.
    """
    entry = tmp_path / "entry.py"
    entry.write_text(
        _ENTRY.format(root=str(ROOT), check=str(CHECK)), encoding="utf-8", newline="\n"
    )
    python = Path(sys.executable).as_posix()
    config = (
        "repos:\n"
        "  - repo: local\n"
        "    hooks:\n"
        "      - id: ticket-runner\n"
        "        name: ticket-runner\n"
        f'        entry: \'"{python}" "{entry.as_posix()}"\'\n'
        "        language: system\n"
        "        always_run: true\n"
        "        pass_filenames: false\n"
    )
    repo = _repo(tmp_path, {**SEED, **CHECK_MARK, ".pre-commit-config.yaml": config}, hook=False)
    installed = subprocess.run(
        [sys.executable, "-m", "pre_commit", "install"],
        cwd=repo.work,
        env=repo.env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=_TIMEOUT,
        check=False,
    )
    assert installed.returncode == 0, installed.stdout + installed.stderr
    return repo


def test_진짜_pre_commit에서_고치고_스테이지하지_않은_티켓은_알린다(
    pre_commit_저장소: Repo,
) -> None:
    repo = pre_commit_저장소
    repo.git("switch", "-q", "-c", "feature/02-thing")
    ticket = ".scratch/feat/issues/02-thing.md"
    repo.write({ticket: READY.replace("ready-for-agent", "in-progress"), "tools/a.py": "A = 2\n"})
    repo.git("add", "tools/a.py")
    out = _막혔다(repo.commit("-m", "x"))
    assert "check-ticket" in out
    assert ticket in out and NOTICE in out
    # pre-commit 이 치운 고침을 되돌려 놓았다
    assert "in-progress" in (repo.work / ticket).read_text(encoding="utf-8")


def test_진짜_pre_commit에서_일부_파일_커밋은_임시_색인을_본다(pre_commit_저장소: Repo) -> None:
    repo = pre_commit_저장소
    repo.git("switch", "-q", "-c", "feature/02-thing")
    ticket = ".scratch/feat/issues/02-thing.md"
    repo.write({ticket: READY.replace("ready-for-agent", "in-progress"), "tools/a.py": "A = 2\n"})
    repo.git("add", ticket)
    _막혔다(repo.commit("-m", "x", "--", "tools/a.py"))
    _지났다(repo.commit("-m", "x", "--", "tools/a.py", ticket))
