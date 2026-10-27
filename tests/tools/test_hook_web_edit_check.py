"""tools/hook_web_edit_check.py 의 판정과 표지. 작업 트리는 임시 폴더에 `.git` 과 `HEAD` 를 손으로
두거나 실제 git 으로 만든다(훅은 git 을 띄우지 않고 그 파일만 읽는다). main 은 stdin 과 임시 폴더를
바꿔 끼워 표지 길을 보고, 래퍼를 거친 실제 실행은 tools/run_hooks.py 의 표가 본다.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from tools.hook_web_edit_check import (
    FOUND_SECTION,
    LEAD,
    MAIN_CONTEXT,
    SKILL,
    SUBAGENT_CONTEXT,
    SUBAGENT_LEAD,
    SUBAGENT_REPORT,
    TICKETS,
    TOOLS,
    branch_of,
    checkout_of,
    claim_first,
    is_import_session,
    is_screen_code,
    main,
    marker_name,
    output_for,
)
from tools.run_hooks import registered_matchers

REPO_ROOT = Path(__file__).parents[2]
ROOT = "C:\\project\\agent"
# 고를 수 있는 답의 라벨. 알림이 풀어 쓰지 않고 스킬의 "찾았을 때" 절을 가리키기만 하는지 본다.
CHOICE_LABELS = ("먼저 들인다", "덮어쓴다", "계속한다")


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


def _작업_트리(root: Path, branch: str = "main") -> Path:
    """`.git` 폴더와 그 `HEAD` 만 둔 작업 트리. 훅이 읽는 것은 그 둘뿐이다."""
    (root / ".git").mkdir(parents=True)
    (root / ".git" / "HEAD").write_text(f"ref: refs/heads/{branch}\n", encoding="utf-8")
    return root


def _티켓을_둔다(root: Path, stem: str, feature: str = "design-reverse-sync") -> None:
    folder = root / ".scratch" / feature / "issues"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{stem}.md").write_text("# 티켓\n", encoding="utf-8")


def _입력(file_path: str, tool: str = "Write", **extra: str) -> bytes:
    payload: dict[str, object] = {"tool_name": tool, "tool_input": {"file_path": file_path}}
    payload.update(extra)
    return json.dumps(payload).encode("utf-8")


def _알림(output: str | None) -> str:
    """훅 출력의 additionalContext. 침묵이면 빈 문자열."""
    if output is None:
        return ""
    data = json.loads(output)
    assert data["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    context = data["hookSpecificOutput"]["additionalContext"]
    assert isinstance(context, str)
    return context


def _ui(root: Path) -> str:
    return str(root / "web" / "packages" / "ui" / "src" / "styles" / "theme.css")


# --- 경로 ---


def test_패키지_아래_Write_는_알린다(tmp_path: Path) -> None:
    root = _작업_트리(tmp_path / "repo")
    context = _알림(output_for(_입력(_ui(root)), tmp_path / "state"))
    assert context.startswith(LEAD)


def test_앱_아래_Edit_도_알린다(tmp_path: Path) -> None:
    root = _작업_트리(tmp_path / "repo")
    path = str(root / "web" / "apps" / "admin" / "src" / "App.tsx")
    assert LEAD in _알림(output_for(_입력(path, "Edit"), tmp_path / "state"))


def test_화면_코드의_경로_꼴() -> None:
    assert is_screen_code(ROOT + "\\web\\packages\\ui\\src\\components\\atoms\\Button.tsx")
    assert is_screen_code(ROOT + "\\web\\apps\\widget\\index.html")
    assert is_screen_code("C:/project/agent/web/apps/admin/src/main.tsx")
    assert is_screen_code(ROOT + "\\.claude\\worktrees\\02-x\\web\\packages\\ui\\theme.css")


def test_web_tools_와_다른_web_아래는_침묵한다(tmp_path: Path) -> None:
    root = _작업_트리(tmp_path / "repo")
    path = str(root / "web" / "tools" / "sync-design-system" / "check.ts")
    assert output_for(_입력(path, "Edit"), tmp_path / "state") is None
    assert not is_screen_code(ROOT + "\\web\\packages\\api-client\\src\\client.ts")
    assert not is_screen_code(ROOT + "\\web\\package.json")
    assert not is_screen_code(ROOT + "\\web\\apps\\README.md")


def test_폴더로_끝나는_경로는_화면_코드가_아니다() -> None:
    assert not is_screen_code(ROOT + "\\web\\packages\\ui")
    assert not is_screen_code(ROOT + "\\web\\apps\\admin")


def test_점과_점점_토막을_접은_경로로_판정한다() -> None:
    assert not is_screen_code(ROOT + "\\web\\packages\\ui\\..\\api-client\\a.ts")
    assert not is_screen_code(ROOT + "\\web\\apps\\..\\tools\\a.ts")
    assert is_screen_code(ROOT + "\\web\\tools\\..\\apps\\admin\\a.ts")
    assert is_screen_code(ROOT + "\\web\\.\\packages\\ui\\a.ts")


def test_대소문자가_다른_폴더_이름도_화면_코드다() -> None:
    assert is_screen_code(ROOT + "\\Web\\Packages\\UI\\src\\a.ts")
    assert is_screen_code(ROOT + "\\WEB\\APPS\\Admin\\a.ts")


def test_다른_도구와_경로_없는_입력은_침묵한다(tmp_path: Path) -> None:
    root = _작업_트리(tmp_path / "repo")
    assert output_for(_입력(_ui(root), "Read"), tmp_path / "state") is None
    assert output_for(b'{"tool_name": "Write", "tool_input": {}}', tmp_path / "state") is None
    assert output_for(b'{"tool_name": "Write"}', tmp_path / "state") is None


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"not json",
        b"\xff\xfe",
        b"\xc3\x28",
        b"[]",
        b'"Write"',
        b'{"tool_name": "Write", "tool_input": "x"}',
        b'{"tool_name": "Write", "tool_input": {"file_path": 1}}',
        b'{"tool_name": "Write", "tool_input": {"file_path": null}}',
        b'{"tool_name": ["Write"], "tool_input": {"file_path": "web/apps/a/b.ts"}}',
        b"[" * 200_000,
    ],
    ids=[
        "빈_입력",
        "JSON_아님",
        "BOM_뿐",
        "UTF8_아님",
        "배열",
        "문자열",
        "입력이_문자열",
        "경로가_수",
        "경로가_null",
        "도구가_배열",
        "깊은_중첩",
    ],
)
def test_꼴이_어긋난_입력은_예외_없이_침묵한다(tmp_path: Path, raw: bytes) -> None:
    assert output_for(raw, tmp_path / "state") is None


# --- 표지 ---


def test_같은_세션의_둘째_쓰기는_침묵한다(tmp_path: Path) -> None:
    root = _작업_트리(tmp_path / "repo")
    state = tmp_path / "state"
    first = _입력(_ui(root), session_id="s1")
    second = _입력(str(root / "web" / "apps" / "admin" / "a.tsx"), "Edit", session_id="s1")
    assert LEAD in _알림(output_for(first, state))
    assert output_for(second, state) is None


def test_세션과_에이전트마다_따로_판정한다(tmp_path: Path) -> None:
    root = _작업_트리(tmp_path / "repo")
    state = tmp_path / "state"
    assert LEAD in _알림(output_for(_입력(_ui(root), session_id="s1"), state))
    assert SUBAGENT_LEAD in _알림(
        output_for(_입력(_ui(root), session_id="s1", agent_id="a"), state)
    )
    assert LEAD in _알림(output_for(_입력(_ui(root), session_id="s2"), state))


def test_경로가_맞지_않은_쓰기는_표지를_남기지_않는다(tmp_path: Path) -> None:
    root = _작업_트리(tmp_path / "repo")
    state = tmp_path / "state"
    tools = str(root / "web" / "tools" / "a.ts")
    assert output_for(_입력(tools, session_id="s1"), state) is None
    assert LEAD in _알림(output_for(_입력(_ui(root), session_id="s1"), state))


def test_표지는_세션과_에이전트마다_한_번이다(tmp_path: Path) -> None:
    main_key = marker_name("s1", "")
    assert claim_first(main_key, tmp_path)
    assert not claim_first(main_key, tmp_path)
    assert claim_first(marker_name("s1", "agent-a"), tmp_path)
    assert claim_first(marker_name("s2", ""), tmp_path)


def test_표지_폴더를_만들지_못하면_알린다(tmp_path: Path) -> None:
    blocker = tmp_path / "file"
    blocker.write_text("", encoding="utf-8")
    assert claim_first(marker_name("s1", ""), blocker / "state")
    assert claim_first(marker_name("s1", ""), blocker)


def test_표지_파일을_만들지_못하면_알린다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def denied(*_args: object) -> int:
        raise PermissionError

    monkeypatch.setattr(os, "open", denied)
    assert claim_first(marker_name("s1", ""), tmp_path)
    assert claim_first(marker_name("s1", ""), tmp_path)


def test_세션을_모르면_호출마다_알린다(tmp_path: Path) -> None:
    root = _작업_트리(tmp_path / "repo")
    state = tmp_path / "state"
    assert LEAD in _알림(output_for(_입력(_ui(root)), state))
    assert LEAD in _알림(output_for(_입력(_ui(root)), state))


def test_표지_폴더가_없으면_호출마다_알린다(tmp_path: Path) -> None:
    root = _작업_트리(tmp_path / "repo")
    assert LEAD in _알림(output_for(_입력(_ui(root), session_id="s1"), None))
    assert LEAD in _알림(output_for(_입력(_ui(root), session_id="s1"), None))


# --- 브랜치 ---


def test_들이기_티켓_브랜치에서는_침묵한다(tmp_path: Path) -> None:
    root = _작업_트리(tmp_path / "repo", "feature/11-web-edit-teal-gray-50")
    _티켓을_둔다(root, "11-web-edit-teal-gray-50")
    assert output_for(_입력(_ui(root), session_id="s1"), tmp_path / "state") is None


def test_이_기능의_구현_티켓_브랜치에서도_침묵한다(tmp_path: Path) -> None:
    root = _작업_트리(tmp_path / "repo", "feature/09-web-edit-hook")
    _티켓을_둔다(root, "09-web-edit-hook")
    assert output_for(_입력(_ui(root)), tmp_path / "state") is None


def test_들이기_티켓_브랜치에서_침묵한_뒤의_둘째_쓰기는_다시_판정하지_않는다(
    tmp_path: Path,
) -> None:
    root = _작업_트리(tmp_path / "repo", "feature/11-web-edit-x")
    _티켓을_둔다(root, "11-web-edit-x")
    state = tmp_path / "state"
    assert output_for(_입력(_ui(root), session_id="s1"), state) is None
    # 다시 판정하면 알릴 상태로 바꾼다. 표지가 판정을 한 번으로 묶어 침묵이 남는다.
    (root / TICKETS / "11-web-edit-x.md").unlink()
    assert output_for(_입력(_ui(root), "Edit", session_id="s1"), state) is None


def test_티켓_파일이_없는_feature_브랜치는_알린다(tmp_path: Path) -> None:
    root = _작업_트리(tmp_path / "repo", "feature/11-web-edit-x")
    assert LEAD in _알림(output_for(_입력(_ui(root)), tmp_path / "state"))


def test_다른_기능의_티켓_브랜치는_알린다(tmp_path: Path) -> None:
    root = _작업_트리(tmp_path / "repo", "feature/01-ui-settings-icon-password-widths")
    _티켓을_둔다(root, "01-ui-settings-icon-password-widths", feature="admin-style")
    assert LEAD in _알림(output_for(_입력(_ui(root)), tmp_path / "state"))


@pytest.mark.parametrize(
    "branch",
    ["main", "chore/011-x", "feature/x", "feature/09-x/y", "docs/09-web-edit-hook"],
)
def test_티켓_꼴이_아닌_브랜치는_들이기가_아니다(tmp_path: Path, branch: str) -> None:
    root = _작업_트리(tmp_path / "repo", branch)
    _티켓을_둔다(root, "09-web-edit-hook")
    _티켓을_둔다(root, "x")
    # `feature/09-x/y` 의 앞머리만 맞추면 이 티켓을 찾는다.
    _티켓을_둔다(root, "09-x")
    assert not is_import_session(root, branch)


def test_워크트리의_git_파일을_따라_브랜치를_읽는다(tmp_path: Path) -> None:
    main_checkout = tmp_path / "repo"
    main_checkout.mkdir()
    _git(main_checkout, "init", "-q", "-b", "main")
    _git(main_checkout, "commit", "-q", "--allow-empty", "-m", "처음")
    worktree = tmp_path / "side"
    _git(main_checkout, "worktree", "add", "-q", "-b", "feature/11-web-edit-x", str(worktree))
    _티켓을_둔다(worktree, "11-web-edit-x")

    assert (worktree / ".git").is_file()
    assert branch_of(worktree) == "feature/11-web-edit-x"
    assert branch_of(main_checkout) == "main"
    assert output_for(_입력(_ui(worktree)), tmp_path / "state") is None
    assert LEAD in _알림(output_for(_입력(_ui(main_checkout)), tmp_path / "state"))


def test_git_파일의_상대_경로는_그_작업_트리에서_푼다(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    (real / "HEAD").write_text("ref: refs/heads/feature/11-x\n", encoding="utf-8")
    worktree = tmp_path / "co"
    worktree.mkdir()
    (worktree / ".git").write_text("gitdir: ../real\n", encoding="utf-8")

    assert branch_of(worktree) == "feature/11-x"


def test_작업_트리는_고친_파일의_폴더에서_위로_찾는다(tmp_path: Path) -> None:
    root = _작업_트리(tmp_path / "repo")
    deep = root / "web" / "packages" / "ui" / "src" / "new-folder"
    assert checkout_of(str(deep)) == root
    assert checkout_of(str(tmp_path / "elsewhere")) is None


def test_상대_경로는_페이로드의_cwd_에서_푼다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _작업_트리(tmp_path / "repo", "feature/11-web-edit-x")
    _티켓을_둔다(root, "11-web-edit-x")
    # 이 프로세스의 작업 폴더는 작업 트리 밖으로 옮긴다. 저장소 뿌리에서 돌면 그 체크아웃의 브랜치와
    # 티켓이 판정에 들어, cwd 를 무시해도 이 저장소의 티켓 브랜치에서는 침묵한다.
    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.chdir(outside)
    relative = "web/packages/ui/src/a.ts"
    assert output_for(_입력(relative, cwd=str(root)), tmp_path / "state") is None


@pytest.mark.parametrize(
    "head",
    ["0123456789abcdef0123456789abcdef01234567\n", "", "ref: refs/remotes/origin/x\n"],
    ids=["분리_HEAD", "빈_HEAD", "브랜치가_아닌_참조"],
)
def test_브랜치를_읽지_못하면_알린다(tmp_path: Path, head: str) -> None:
    root = _작업_트리(tmp_path / "repo")
    (root / ".git" / "HEAD").write_text(head, encoding="utf-8")
    assert branch_of(root) is None
    assert LEAD in _알림(output_for(_입력(_ui(root)), tmp_path / "state"))


def test_HEAD_가_없거나_git_파일이_모르는_꼴이면_알린다(tmp_path: Path) -> None:
    no_head = tmp_path / "no-head"
    (no_head / ".git").mkdir(parents=True)
    odd = tmp_path / "odd"
    odd.mkdir()
    (odd / ".git").write_text("not a gitdir line\n", encoding="utf-8")
    for root in (no_head, odd):
        assert branch_of(root) is None
        assert LEAD in _알림(output_for(_입력(_ui(root)), tmp_path / "state"))


def test_git_파일의_gitdir_에_NUL_이_있으면_알린다(tmp_path: Path) -> None:
    root = tmp_path / "co"
    root.mkdir()
    (root / ".git").write_text("gitdir: a\0b\n", encoding="utf-8")
    assert branch_of(root) is None
    assert LEAD in _알림(output_for(_입력(_ui(root)), tmp_path / "state"))


def test_작업_트리를_찾지_못하면_알린다(tmp_path: Path) -> None:
    path = str(tmp_path / "loose" / "web" / "apps" / "admin" / "a.tsx")
    assert LEAD in _알림(output_for(_입력(path), tmp_path / "state"))


def test_HEAD_의_ref_뒤_공백은_git_처럼_넘는다(tmp_path: Path) -> None:
    root = _작업_트리(tmp_path / "repo")
    (root / ".git" / "HEAD").write_text("ref:\trefs/heads/feature/11-x\n", encoding="utf-8")
    assert branch_of(root) == "feature/11-x"


# --- 알림 ---


def test_서브에이전트에는_끝_보고에_적을_것을_알린다(tmp_path: Path) -> None:
    root = _작업_트리(tmp_path / "repo")
    context = _알림(output_for(_입력(_ui(root), agent_id="a1"), tmp_path / "state"))
    assert context.startswith(SUBAGENT_LEAD)
    assert SUBAGENT_REPORT in context
    assert "끝 보고 첫머리" in context
    assert "확인을 하지 않는다" in context
    assert LEAD not in context


def test_빈_agent_id_는_메인_세션이다(tmp_path: Path) -> None:
    root = _작업_트리(tmp_path / "repo")
    assert LEAD in _알림(output_for(_입력(_ui(root), agent_id=""), tmp_path / "state"))


def test_메인_세션에는_고친_파일을_두고_확인을_부르라고_알린다() -> None:
    assert "방금 고친 파일은 그대로 두고" in MAIN_CONTEXT
    assert "화면을 더 고치기 전에" in MAIN_CONTEXT
    assert f"Skill 도구로 `{SKILL}`" in MAIN_CONTEXT
    assert f"/{SKILL} 확인" in MAIN_CONTEXT


@pytest.mark.parametrize(
    "context",
    [MAIN_CONTEXT, SUBAGENT_CONTEXT],
    ids=["메인", "서브에이전트"],
)
def test_알림은_선택지를_풀어_쓰지_않고_찾았을_때_절을_가리킨다(context: str) -> None:
    assert f'"{FOUND_SECTION}"' in context
    for label in CHOICE_LABELS:
        assert label not in context


def test_가리키는_스킬과_절이_저장소에_있다() -> None:
    skill = REPO_ROOT / ".claude" / "skills" / SKILL / "SKILL.md"
    lines = skill.read_text(encoding="utf-8").splitlines()
    assert f"name: {SKILL}" in lines, skill
    assert f"## {FOUND_SECTION}" in lines, skill


def test_티켓_폴더는_이_기능의_것이다() -> None:
    assert (REPO_ROOT / TICKETS / "09-web-edit-hook.md").is_file()


# --- 못 보는 것 ---


def test_못_보는_것_Bash_로_고친_화면_파일은_지나간다(tmp_path: Path) -> None:
    # 이 훅은 편집 도구에만 붙는다. 등록 매처에도 Bash 가 없다.
    root = _작업_트리(tmp_path / "repo")
    command = f"sed -i 's/a/b/' '{_ui(root)}'"
    raw = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}).encode("utf-8")
    assert output_for(raw, tmp_path / "state") is None


@pytest.mark.parametrize(
    "relative",
    ["src/agent_os/server.py", "openapi.json", "web/packages/api-client/src/widget.ts"],
)
def test_못_보는_것_web_밖에서_화면에_닿는_파일은_지나간다(tmp_path: Path, relative: str) -> None:
    root = _작업_트리(tmp_path / "repo")
    assert output_for(_입력(str(root / relative)), tmp_path / "state") is None


def test_못_보는_것_침묵한_뒤_브랜치를_바꾼_세션의_쓰기는_지나간다(tmp_path: Path) -> None:
    root = _작업_트리(tmp_path / "repo", "feature/11-web-edit-x")
    _티켓을_둔다(root, "11-web-edit-x")
    state = tmp_path / "state"
    assert output_for(_입력(_ui(root), session_id="s1"), state) is None
    (root / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    assert output_for(_입력(_ui(root), session_id="s1"), state) is None


def test_못_보는_것_이미_확인을_부른_세션에도_한_번_알린다(tmp_path: Path) -> None:
    # 이 훅은 그 세션이 확인을 불렀는지 모른다. 표지가 없으면 확인 뒤의 첫 쓰기에도 알리고, 문장이
    # 이미 했으면 무시하라고 든다.
    root = _작업_트리(tmp_path / "repo")
    context = _알림(output_for(_입력(_ui(root), session_id="s1"), tmp_path / "state"))
    assert "이미 그 확인을 했으면 이 알림은 무시한다" in context


def test_못_보는_것_한_번_알린_뒤에는_같은_세션에_다시_알리지_않는다(tmp_path: Path) -> None:
    # 컨텍스트 압축이나 이어 하기로 알림 문장이 사라져도 세션 ID 가 같으면 표지가 남아 있다.
    root = _작업_트리(tmp_path / "repo")
    state = tmp_path / "state"
    assert LEAD in _알림(output_for(_입력(_ui(root), session_id="s1"), state))
    resumed = _입력(str(root / "web" / "apps" / "widget" / "src" / "a.tsx"), session_id="s1")
    assert output_for(resumed, state) is None


def test_못_보는_것_저장소_뿌리의_web_인지_가르지_않는다(tmp_path: Path) -> None:
    root = _작업_트리(tmp_path / "repo")
    path = str(root / "docs" / "notes" / "web" / "apps" / "x" / "a.md")
    assert LEAD in _알림(output_for(_입력(path), tmp_path / "state"))


# --- main 과 등록 ---


def _run_main(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], raw: bytes
) -> str:
    """main 을 한 번 돌려 알린 문장을, 알리지 않았으면 빈 문자열을 돌려준다."""
    stdin = io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8")
    monkeypatch.setattr(sys, "stdin", stdin)
    assert main() == 0
    out = capsys.readouterr().out
    return _알림(out) if out else ""


def test_main_은_임시_폴더에_표지를_두고_세션마다_한_번_알린다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path / "temp"))
    root = _작업_트리(tmp_path / "repo")
    raw = _입력(_ui(root), session_id="session-1")
    assert LEAD in _run_main(monkeypatch, capsys, raw)
    assert _run_main(monkeypatch, capsys, raw) == ""
    assert any((tmp_path / "temp").rglob("*"))


def test_main_은_임시_폴더가_없으면_호출마다_알린다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def no_temp() -> str:
        raise FileNotFoundError("쓸 수 있는 임시 폴더가 없다")

    monkeypatch.setattr(tempfile, "gettempdir", no_temp)
    root = _작업_트리(tmp_path / "repo")
    raw = _입력(_ui(root), session_id="session-1")
    assert LEAD in _run_main(monkeypatch, capsys, raw)
    assert LEAD in _run_main(monkeypatch, capsys, raw)


def test_main_은_꼴이_어긋난_입력에_0으로_침묵한다(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _run_main(monkeypatch, capsys, b"not json") == ""


def test_등록의_매처가_훅이_아는_도구와_같다() -> None:
    assert registered_matchers("hook_web_edit_check.py", "PostToolUse") == ["|".join(TOOLS)]
