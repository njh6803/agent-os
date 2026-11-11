"""`tools/morning_sources.py` 가 통합 브랜치를 `tools/base_rule.py` 의 규칙으로 고르는지 본다.

`origin/dev` 가 없으면 지금까지처럼 `origin/main` 을 읽고, 있으면 `origin/dev` 를 읽는다. 보고에는
작업 브랜치가 없어 hotfix 가 아닌 쪽의 기준이 통합 브랜치다.
"""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path

import pytest

from tools import morning_sources

_IDENTITY = ("-c", "user.name=t", "-c", "user.email=t@example.com")


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *_IDENTITY, "-C", str(repo), *args],
        check=True,
        capture_output=True,
        timeout=60,
    )


def _repository(tmp_path: Path, *, with_dev: bool) -> Path:
    """main 에 `a.txt` 가 있고, dev 가 있으면 dev 에는 `b.txt` 가 더 있는 저장소."""
    repo = tmp_path / "repo"
    _git(tmp_path, "init", "-q", "-b", "main", str(repo))
    (repo / "a.txt").write_text("main\n", encoding="utf-8")
    _git(repo, "add", "a.txt")
    _git(repo, "commit", "-q", "-m", "씨앗")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    if with_dev:
        (repo / "b.txt").write_text("dev\n", encoding="utf-8")
        _git(repo, "add", "b.txt")
        _git(repo, "commit", "-q", "-m", "dev 가 나아간다")
        _git(repo, "update-ref", "refs/remotes/origin/dev", "HEAD")
    return repo


def test_dev_추적_ref_가_없으면_통합_브랜치는_origin_main_이다(tmp_path: Path) -> None:
    repo = _repository(tmp_path, with_dev=False)
    assert morning_sources.integration_ref(repo) == "origin/main"
    assert morning_sources.main_text(repo, "a.txt") == "main\n"


def test_dev_추적_ref_가_있으면_통합_브랜치는_origin_dev_이다(tmp_path: Path) -> None:
    repo = _repository(tmp_path, with_dev=True)
    assert morning_sources.integration_ref(repo) == "origin/dev"
    # dev 에만 있는 파일이 읽힌다. main 을 읽었다면 None 이다
    assert morning_sources.main_text(repo, "b.txt") == "dev\n"


def test_반박_상대_경로의_root_로도_대기열을_통합_브랜치에서_읽는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """PR 봇 첫 회차의 Minor. 작업 폴더를 `root` 로 옮긴 뒤에 통합 ref 를 정하면 상대 `root` 가 한
    번 더 겹쳐 git 이 실패하고, 규칙이 `origin/main` 으로 돌아가 dev 에만 있는 대기열 항목을
    놓친다."""
    repo = _repository(tmp_path, with_dev=True)
    queue = repo / ".scratch" / "retro-queue"
    queue.mkdir(parents=True)
    (queue / "dev-only.md").write_text("dev 에만 있다\n", encoding="utf-8")
    _git(repo, "add", "-f", ".scratch")
    _git(repo, "commit", "-q", "-m", "dev 대기열")
    _git(repo, "update-ref", "refs/remotes/origin/dev", "HEAD")
    monkeypatch.chdir(tmp_path)

    assert morning_sources.main_queue(Path("repo")) == {"dev-only.md": "dev 에만 있다\n"}


@pytest.mark.parametrize(("with_dev", "expected"), [(False, "main"), (True, "dev")])
def test_CI_는_통합_브랜치의_이름으로_gh_를_부른다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, with_dev: bool, expected: str
) -> None:
    calls: list[list[str]] = []

    def fake(args: Sequence[str], _cwd: Path) -> list[object]:
        calls.append(list(args))
        return []

    monkeypatch.setattr(morning_sources, "_gh_json", fake)
    morning_sources.ci_runs(_repository(tmp_path, with_dev=with_dev))
    assert calls, "gh 를 부르지 않았다"
    args = calls[0]
    assert args[args.index("--branch") + 1] == expected
