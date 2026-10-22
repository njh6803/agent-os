"""tools/hook_handoff.py 와 tools/hook_handoff_notice.py — 단계 경계의 인계 지시와 Stop 의 사람
알림.

두 훅은 서로 import 하지 않아 문턱·세션 컨텍스트 셈·표지 이름을 따로 둔다. 같은지는 아래
`test_두_훅의_문턱과_셈과_표지_이름이_같다` 가 본다. stdin 을 읽는 main 은 임시 디렉터리를 환경으로
준 자식으로 돌려 본다(선례 tests/tools/test_launch_hook.py). 등록 모양과 표의 실제 입력은
tools/run_hooks.py 가 pre-commit 에서 잰다.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypedDict

import pytest
from tests.tools import gh_api_cases
from tools.hook_handoff import (
    MCP_CREATE_TOOLS,
    SECTION,
    SKILL_PATH,
    SKILL_RELATIVE,
    THRESHOLD,
    HookPayload,
    boundary_of,
    context_for,
    handoff_context,
    skill_for,
)
from tools.hook_handoff_notice import claim_first, notice_for
from tools.hook_pr_next_session import MCP_TOOLS
from tools.run_hooks import ROOT, hook_environment, registered_matchers

from tools import hook_handoff, hook_handoff_notice

HANDOFF = ROOT / "tools" / "hook_handoff.py"
NOTICE = ROOT / "tools" / "hook_handoff_notice.py"


class _Specific(TypedDict, total=False):
    hookEventName: str
    additionalContext: str


class _Output(TypedDict, total=False):
    systemMessage: str
    hookSpecificOutput: _Specific


def _응답(tokens: int, *, model: str = "claude-opus-5-5", sidechain: bool = False) -> str:
    """세 입력 토큰의 합이 `tokens` 인 assistant 기록 한 줄. 실제 기록처럼 usage 가 message 안에
    있다."""
    record = {
        "type": "assistant",
        "isSidechain": sidechain,
        "message": {
            "id": "msg_x",
            "model": model,
            "content": [{"type": "tool_use", "id": "toolu_x", "name": "Bash"}],
            "usage": {
                "input_tokens": 2,
                "cache_creation_input_tokens": 1000,
                "cache_read_input_tokens": tokens - 1002,
                "output_tokens": 300,
            },
        },
    }
    return json.dumps(record)


_압축_경계 = json.dumps(
    {
        "type": "system",
        "subtype": "compact_boundary",
        "isSidechain": False,
        "content": "Conversation compacted",
        "compactMetadata": {"trigger": "auto", "preTokens": 400000},
    }
)
_도구_결과 = json.dumps({"type": "user", "message": {"role": "user", "content": "ok"}})


def _트랜스크립트(path: Path, lines: Sequence[str]) -> Path:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return path


def _페이로드(transcript: Path, tool_name: str = "Bash", **tool_input: str) -> HookPayload:
    inputs: dict[str, object] = dict(tool_input)
    return {
        "session_id": "s-1",
        "transcript_path": transcript.as_posix(),
        "tool_name": tool_name,
        "tool_input": inputs,
    }


def _돌린다(
    script: Path, payload: Mapping[str, object], temp: Path, **env: str
) -> subprocess.CompletedProcess[bytes]:
    environment = hook_environment()
    environment.update({name: str(temp) for name in ("TMPDIR", "TEMP", "TMP")})
    environment.update(env)
    return subprocess.run(
        [sys.executable, str(script)],
        input=json.dumps(payload).encode(),
        capture_output=True,
        env=environment,
        check=False,
        timeout=60,
    )


def _출력(launched: subprocess.CompletedProcess[bytes]) -> _Output | None:
    assert launched.returncode == 0, launched.stderr.decode(errors="replace")
    if not launched.stdout.strip():
        return None
    parsed: _Output = json.loads(launched.stdout)
    return parsed


# --- 경계 판정 ---


def test_셀프_리뷰_직전은_code_review_스킬의_두_이름_모양이다() -> None:
    for name in (
        "code-review",
        "/code-review",
        ".claude:code-review",
        ".claude/worktrees/05-x:code-review",
        ".claude\\worktrees\\05-x:code-review",
    ):
        assert boundary_of("Skill", {"skill": name}) == "셀프 리뷰 직전", name


def test_code_review_가_아닌_스킬과_플러그인의_code_review_는_경계가_아니다() -> None:
    for name in ("tdd", "next-session", "code-review:code-review", "coderabbit:code-review"):
        assert boundary_of("Skill", {"skill": name}) is None, name


def test_명령_위치의_git_commit_은_커밋_뒤다() -> None:
    for command in (
        "git commit -F msg.txt",
        "git add -A && git commit -m x",
        "git -c core.longpaths=true commit -F m.txt",
        "git -C C:/project/agent commit -F m.txt",
        "git --no-pager commit --amend --no-edit",
    ):
        assert boundary_of("Bash", {"command": command}) == "커밋 뒤", command
    assert boundary_of("PowerShell", {"command": "git commit -F m.txt"}) == "커밋 뒤"


def test_커밋하지_않는_git_commit_과_배관과_데이터는_경계가_아니다() -> None:
    for command in (
        "git commit --dry-run",
        "git commit --help",
        "git commit -h",
        "git commit-tree HEAD^{tree}",
        "git commit-graph write",
        "echo 'git commit -m x'",
        "cat <<'EOF'\ngit commit -m x\nEOF",
        "git log --oneline",
    ):
        assert boundary_of("Bash", {"command": command}) is None, command


def test_PR_만들기는_셸과_MCP_모두_PR_연_뒤다() -> None:
    assert boundary_of("Bash", {"command": "gh pr create --title x --body-file b.md"}) == "PR 연 뒤"
    for tool in MCP_CREATE_TOOLS:
        assert boundary_of(tool, {"title": "x"}) == "PR 연 뒤", tool


def test_PR_병합과_보기는_경계가_아니다() -> None:
    for command in (
        "gh pr merge 3 --squash",
        "gh pr view --json state",
        "gh pr checks",
        "gh pr create --help",
        "gh pr create -h",
    ):
        assert boundary_of("Bash", {"command": command}) is None, command
    assert boundary_of("mcp__plugin_github_github__merge_pull_request", {}) is None


def test_저장소_옵션과_별칭과_경로_인자가_낀_명령도_경계다() -> None:
    """`--git-dir=`·`--work-tree=`, `gh -R`, `gh pr new`(create 의 별칭), `--` 뒤의 경로 `-h`."""
    for command, boundary in (
        ("git --git-dir=.git commit -m x", "커밋 뒤"),
        ("git --work-tree=. --git-dir=.git commit -m x", "커밋 뒤"),
        ("git commit -m x -- path -h", "커밋 뒤"),
        ("gh -R owner/repo pr create -t x", "PR 연 뒤"),
        ("gh --repo owner/repo pr create -t x", "PR 연 뒤"),
        ("gh pr new -t x", "PR 연 뒤"),
    ):
        assert boundary_of("Bash", {"command": command}) == boundary, command


def test_gh_api_로_pulls_에_POST_하면_PR_연_뒤다() -> None:
    """`hook_pr_next_session` 과 같은 판정이고 같은 표를 쓴다(대기열 408,
    `tests/tools/gh_api_cases.py`)."""
    for command in gh_api_cases.OPENS:
        assert boundary_of("Bash", {"command": command}) == "PR 연 뒤", command
    # 표의 `git commit -m "gh api …"` 는 이 훅에서 커밋 뒤라, PR 연 뒤가 아닌지만 본다
    for command in gh_api_cases.NOT_OPENS:
        assert boundary_of("Bash", {"command": command}) != "PR 연 뒤", command


def test_못_보는_것_GraphQL_과_변수_엔드포인트의_PR_만들기는_경계가_아니다() -> None:
    """거짓 음성이다. `gh api graphql` 의 `createPullRequest` 와 변수로 준 엔드포인트는 보지
    않는다."""
    for command in gh_api_cases.BLIND:
        assert boundary_of("Bash", {"command": command}) is None, command


def test_명령_앞의_래퍼와_경로로_부른_git_과_인용_없는_옵션_값은_보지_못한다() -> None:
    """못 보는 것의 거짓 음성. 셸 문법 밖의 명령 위치와 인용 없는 `-h` 메시지를 가르지 않는다."""
    for command in (
        "time git commit -m x",
        "env A=1 git commit -m x",
        "sudo git commit -m x",
        "! git commit -m x",
        "/usr/bin/git commit -m x",
        "git commit -m -h",
    ):
        assert boundary_of("Bash", {"command": command}) is None, command


def test_줄인_옵션과_줄_잇기_뒤의_도움말은_경계로_센다() -> None:
    """못 보는 것의 거짓 양성. git 은 `--dry` 를 `--dry-run` 으로 받고, 줄 잇기 뒤의 `-h` 도
    도움말이다."""
    for command in ("git commit --dry", "git commit \\\n  -h"):
        assert boundary_of("Bash", {"command": command}) == "커밋 뒤", command


def test_커밋과_PR_의_문장은_성공했는지를_모델에게_미룬다() -> None:
    """못 보는 것: 실패한 커밋과 PR 만들기도 경계로 센다. 문장이 "성공했으면"으로 미룬다."""
    for boundary in ("커밋 뒤", "PR 연 뒤"):
        assert "성공했으면" in context_for(boundary, 210_000), boundary
    assert "성공했으면" not in context_for("셀프 리뷰 직전", 210_000)


def test_MCP_만들기_도구는_hook_pr_next_session_의_만들기와_매처에_든_이름이다() -> None:
    creates = {name for name, action in MCP_TOOLS.items() if action == "create"}

    matchers = registered_matchers("hook_handoff.py", "PostToolUse")

    assert set(MCP_CREATE_TOOLS) == creates
    assert len(matchers) == 1
    assert set(matchers[0].split("|")) == set(MCP_CREATE_TOOLS) | {"Bash", "PowerShell", "Skill"}


def test_Stop_알림_훅은_매처_없이_Stop_에만_등록된다() -> None:
    assert registered_matchers("hook_handoff_notice.py", "Stop") == [""]
    assert registered_matchers("hook_handoff.py", "Stop") == []


# --- 세션 컨텍스트와 침묵 ---


def test_문턱_위의_경계는_크기와_문턱과_경계와_스킬_경로를_든_인계_문장이다(tmp_path: Path) -> None:
    transcript = _트랜스크립트(tmp_path / "t.jsonl", [_도구_결과, _응답(250_000)])

    context = handoff_context(_페이로드(transcript, command="git commit -F m.txt"), {})

    assert context is not None
    assert "250,000" in context
    assert "200,000" in context
    assert "`커밋 뒤`" in context
    assert SKILL_PATH.as_posix() in context
    assert "Read" in context


def test_문턱_아래의_커밋은_침묵이다(tmp_path: Path) -> None:
    transcript = _트랜스크립트(tmp_path / "t.jsonl", [_응답(THRESHOLD - 1)])

    assert handoff_context(_페이로드(transcript, command="git commit -F m.txt"), {}) is None


def test_세션_컨텍스트는_메인_세션의_마지막_실제_응답이다(tmp_path: Path) -> None:
    """사이드체인과 `<synthetic>` 기록은 세지 않는다. 앞의 큰 응답이 아니라 마지막 응답을 본다."""
    transcript = _트랜스크립트(
        tmp_path / "t.jsonl",
        [
            _응답(300_000),
            _응답(150_000),
            _응답(900_000, sidechain=True),
            _응답(0, model="<synthetic>"),
            _도구_결과,
        ],
    )

    assert handoff_context(_페이로드(transcript, command="git commit -F m.txt"), {}) is None


def test_마지막_응답_뒤에_압축_경계가_있으면_압축_전의_값이라_침묵이다(tmp_path: Path) -> None:
    transcript = _트랜스크립트(tmp_path / "t.jsonl", [_응답(390_000), _압축_경계])

    assert handoff_context(_페이로드(transcript, command="git commit -F m.txt"), {}) is None


def test_압축_뒤의_응답이_문턱을_넘으면_다시_인계_문장이다(tmp_path: Path) -> None:
    transcript = _트랜스크립트(tmp_path / "t.jsonl", [_응답(390_000), _압축_경계, _응답(210_000)])

    assert handoff_context(_페이로드(transcript, command="git commit -F m.txt"), {}) is not None


def test_끝부분에_모델_응답이_없으면_침묵이다(tmp_path: Path) -> None:
    """2MiB 밖으로 밀려난 응답은 보지 못한다(못 보는 것)."""
    filler = json.dumps({"type": "user", "message": {"content": "가" * 1000}})
    lines = [_응답(300_000), *([filler] * 800)]
    transcript = _트랜스크립트(tmp_path / "t.jsonl", lines)
    assert transcript.stat().st_size > hook_handoff.TAIL_BYTES

    assert handoff_context(_페이로드(transcript, command="git commit -F m.txt"), {}) is None


def test_서브에이전트와_클라우드_세션은_침묵이다(tmp_path: Path) -> None:
    transcript = _트랜스크립트(tmp_path / "t.jsonl", [_응답(250_000)])
    payload = _페이로드(transcript, command="git commit -F m.txt")

    assert handoff_context({**payload, "agent_id": "a1"}, {}) is None
    assert handoff_context(payload, {"CLAUDE_CODE_REMOTE": "true"}) is None
    assert handoff_context(payload, {"CLAUDE_CODE_REMOTE": "false"}) is not None


def test_경계가_아닌_호출은_트랜스크립트를_열지_않는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened: list[Path] = []

    def 기록한다(path: Path, limit: int) -> list[str]:
        opened.append(path)
        return []

    monkeypatch.setattr(hook_handoff, "tail_lines", 기록한다)
    transcript = tmp_path / "t.jsonl"

    assert handoff_context(_페이로드(transcript, command="git status"), {}) is None
    assert handoff_context(_페이로드(transcript, "Skill", skill="tdd"), {}) is None
    assert opened == []
    handoff_context(_페이로드(transcript, command="git commit -F m.txt"), {})
    assert opened == [transcript]


def test_다른_저장소의_커밋도_경계로_센다(tmp_path: Path) -> None:
    """못 보는 것의 거짓 양성: `git -C <임시 저장소> commit` 도 인계 문장이다."""
    transcript = _트랜스크립트(tmp_path / "t.jsonl", [_응답(250_000)])
    payload = _페이로드(transcript, command=f"git -C {tmp_path.as_posix()}/other commit -m x")

    assert handoff_context(payload, {}) is not None


def test_별칭과_스크립트_안의_커밋은_보지_못한다(tmp_path: Path) -> None:
    """못 보는 것의 거짓 음성: 명령 위치에 `git commit` 이 없다."""
    transcript = _트랜스크립트(tmp_path / "t.jsonl", [_응답(250_000)])

    for command in ("git ci -m x", "bash tools/commit.sh", "uv run python tools/commit.py"):
        assert handoff_context(_페이로드(transcript, command=command), {}) is None, command


def test_병렬_호출의_앞쪽은_아직_기록되지_않은_응답_대신_그_앞의_응답을_읽는다(
    tmp_path: Path,
) -> None:
    """못 보는 것: 경계를 낸 응답(25만)이 아직 쓰이지 않았으면 그 앞의 응답(19만)으로 재 침묵한다.
    다음 경계가 받는다."""
    transcript = _트랜스크립트(tmp_path / "t.jsonl", [_응답(190_000), _도구_결과])

    assert handoff_context(_페이로드(transcript, command="git commit -F m.txt"), {}) is None


def test_날것_줄_구분_문자가_든_기록도_한_줄로_읽는다(tmp_path: Path) -> None:
    """JSONL 은 줄바꿈(LF)으로만 가른다. `splitlines` 는 U+2028·U+0085 에서도 갈라, 그 문자를
    날것으로 담은 마지막 응답을 버리고 앞의 작은 응답을 읽었다(PR 직전 버그 리뷰)."""
    separator = chr(0x2028)
    big = json.loads(_응답(250_000))
    big["message"]["content"] = [{"type": "text", "text": f"a{separator}b{chr(0x85)}c"}]
    raw = json.dumps(big, ensure_ascii=False)
    assert separator in raw
    transcript = _트랜스크립트(tmp_path / "t.jsonl", [_응답(120_000), raw])

    assert hook_handoff.tail_lines(transcript, 1024 * 1024)[-1] == raw
    assert hook_handoff_notice.tail_lines(transcript, 1024 * 1024)[-1] == raw
    assert handoff_context(_페이로드(transcript, command="git commit -F m.txt"), {}) is not None


def test_깨진_기록은_예외_없이_넘긴다() -> None:
    """문자열 message, 목록 usage, 문자열 토큰. 훅이 1로 끝나면 사람에게 오류만 보인다."""
    lines = [
        json.dumps({"type": "assistant", "message": "x"}),
        json.dumps({"type": "assistant", "message": {"model": "m", "usage": [1, 2]}}),
        json.dumps(
            {
                "type": "assistant",
                "message": {
                    "model": "m",
                    "usage": {"input_tokens": "9", "cache_read_input_tokens": 5},
                },
            }
        ),
    ]

    assert hook_handoff.session_context(lines) == 5
    assert hook_handoff_notice.session_context(lines) == 5


# --- 문장 ---


def test_셀프_리뷰_직전의_문장은_리뷰_단계를_밟지_말라고_한다() -> None:
    context = context_for("셀프 리뷰 직전", 210_000)

    assert "`셀프 리뷰 직전`" in context
    assert "code-review" in context
    assert "밟지 않는다" in context


def test_PR_연_뒤의_문장은_봇_회차와_병합도_넘기고_PR_계기보다_앞선다고_한다() -> None:
    context = context_for("PR 연 뒤", 210_000)

    assert "봇 회차와 병합" in context
    assert "hook_pr_next_session" in context
    assert "앞선다" in context


def test_문장은_Skill_도구로_부르지_말고_Read_로_열라고_한다() -> None:
    for boundary in ("셀프 리뷰 직전", "커밋 뒤", "PR 연 뒤"):
        context = context_for(boundary, 210_000)
        assert "Read 도구로 연다" in context, boundary
        assert "Skill 도구로 부르지 않는다" in context, boundary
        assert "인계 줄" in context, boundary


def test_훅과_같은_체크아웃의_next_session_에_인계_절이_있다() -> None:
    assert SKILL_PATH == ROOT / ".claude" / "skills" / "next-session" / "SKILL.md"
    assert SECTION in SKILL_PATH.read_text(encoding="utf-8").splitlines()


def _사본을_둔다(checkout: Path, *, section: bool) -> Path:
    skill = checkout / SKILL_RELATIVE
    skill.parent.mkdir(parents=True)
    body = f"# next-session\n\n{SECTION}\n" if section else "# next-session\n"
    skill.write_text(body, encoding="utf-8")
    return skill


def test_작업_폴더의_사본에_인계_절이_있으면_그_사본을_가리킨다(tmp_path: Path) -> None:
    """기본 권한 모드의 워크트리 세션이 주 체크아웃의 사본을 Read 하면 승인을 물었다
    (`.scratch/token-usage/probes/handoff_reach.py` 의 C). 작업 폴더 안의 사본은 묻지 않는다."""
    worktree = tmp_path / "main" / ".claude" / "worktrees" / "05-x"
    _사본을_둔다(tmp_path / "main", section=True)
    own = _사본을_둔다(worktree, section=True)
    (worktree / "tools").mkdir()

    assert skill_for(str(worktree)) == own
    assert skill_for(str(worktree / "tools")) == own
    assert f"`{own.as_posix()}`" in context_for("커밋 뒤", 210_000, skill_for(str(worktree)))


def test_작업_폴더의_사본에_인계_절이_없으면_훅의_사본을_가리키고_더_올라가지_않는다(
    tmp_path: Path,
) -> None:
    """옛 워크트리는 주 체크아웃 아래에 있다. 올라가 주 체크아웃의 사본을 고르지 않는다."""
    worktree = tmp_path / "main" / ".claude" / "worktrees" / "old"
    _사본을_둔다(tmp_path / "main", section=True)
    _사본을_둔다(worktree, section=False)

    assert skill_for(str(worktree)) == SKILL_PATH


def test_cwd_가_없거나_사본이_없으면_훅의_사본을_가리킨다(tmp_path: Path) -> None:
    assert skill_for(None) == SKILL_PATH
    assert skill_for(str(tmp_path / "nowhere")) == SKILL_PATH


def test_상대_경로의_cwd_는_고르지_않는다() -> None:
    """드라이브만 남은 `C:` 와 상대 경로는 훅의 작업 폴더에 기댄다."""
    for cwd in ("C:", ".", "tools"):
        assert skill_for(cwd) == SKILL_PATH, cwd


def test_다른_저장소의_사본에_인계_절이_있으면_그것을_가리킨다(tmp_path: Path) -> None:
    """못 보는 것: `cwd` 가 다른 저장소여도 그 사본에 인계 절이 있으면 고른다."""
    other = _사본을_둔다(tmp_path / "other-repo", section=True)

    assert skill_for(str(tmp_path / "other-repo")) == other


# --- Stop 알림과 표지(main 을 자식으로 돌린다) ---


def test_Stop_알림은_한_번만_사람에게_낸다(tmp_path: Path) -> None:
    transcript = _트랜스크립트(tmp_path / "t.jsonl", [_응답(230_000)])
    payload = {"session_id": "s-1", "hook_event_name": "Stop", "transcript_path": str(transcript)}
    temp = tmp_path / "temp"
    temp.mkdir()

    first = _출력(_돌린다(NOTICE, payload, temp))
    second = _출력(_돌린다(NOTICE, payload, temp))

    assert first is not None
    assert "hookSpecificOutput" not in first
    assert "230,000" in first.get("systemMessage", "")
    assert second is None


def test_Stop_알림은_문턱_아래면_침묵이고_표지를_남기지_않는다(tmp_path: Path) -> None:
    payload = {
        "session_id": "s-1",
        "hook_event_name": "Stop",
        "transcript_path": str(_트랜스크립트(tmp_path / "t.jsonl", [_응답(120_000)])),
    }
    temp = tmp_path / "temp"
    temp.mkdir()

    assert _출력(_돌린다(NOTICE, payload, temp)) is None
    assert not (temp / hook_handoff_notice.STATE_DIR).exists() or not any(
        (temp / hook_handoff_notice.STATE_DIR).iterdir()
    )


def test_인계를_지시한_세션의_Stop_은_침묵이다(tmp_path: Path) -> None:
    transcript = _트랜스크립트(tmp_path / "t.jsonl", [_응답(230_000)])
    temp = tmp_path / "temp"
    temp.mkdir()

    handed = _출력(_돌린다(HANDOFF, _페이로드(transcript, command="git commit -F m.txt"), temp))
    stop = {"session_id": "s-1", "hook_event_name": "Stop", "transcript_path": str(transcript)}

    assert handed is not None
    assert "additionalContext" in handed.get("hookSpecificOutput", {})
    assert _출력(_돌린다(NOTICE, stop, temp)) is None


def test_Stop_알림이_난_뒤의_경계에서도_인계_지시는_난다(tmp_path: Path) -> None:
    transcript = _트랜스크립트(tmp_path / "t.jsonl", [_응답(230_000)])
    temp = tmp_path / "temp"
    temp.mkdir()
    stop = {"session_id": "s-1", "hook_event_name": "Stop", "transcript_path": str(transcript)}

    assert _출력(_돌린다(NOTICE, stop, temp)) is not None
    handed = _출력(_돌린다(HANDOFF, _페이로드(transcript, command="git commit -F m.txt"), temp))
    again = _출력(_돌린다(HANDOFF, _페이로드(transcript, command="gh pr create -t x"), temp))

    assert handed is not None
    assert again is not None
    assert handed.get("hookSpecificOutput", {}).get("hookEventName") == "PostToolUse"


def _표지_자리를_막는다(tmp_path: Path) -> Path:
    """표지 폴더 자리에 파일을 둔 임시 폴더. 임시 폴더 자체를 파일로 주면 `tempfile` 이 다른 후보로
    넘어가 표지를 쓴다(손으로 봤다). 선례는 tests/tools/test_launch_hook.py 다."""
    temp = tmp_path / "temp"
    temp.mkdir()
    (temp / hook_handoff_notice.STATE_DIR).write_text("폴더가 아니다", encoding="utf-8")
    return temp


def test_표지를_쓰지_못하면_Stop_알림은_침묵이다(tmp_path: Path) -> None:
    transcript = _트랜스크립트(tmp_path / "t.jsonl", [_응답(230_000)])
    stop = {"session_id": "s-1", "hook_event_name": "Stop", "transcript_path": str(transcript)}

    assert _출력(_돌린다(NOTICE, stop, _표지_자리를_막는다(tmp_path))) is None


def test_표지를_쓰지_못해도_인계_지시는_난다(tmp_path: Path) -> None:
    transcript = _트랜스크립트(tmp_path / "t.jsonl", [_응답(230_000)])
    payload = _페이로드(transcript, command="git commit -F m.txt")

    assert _출력(_돌린다(HANDOFF, payload, _표지_자리를_막는다(tmp_path))) is not None


def test_쓸_수_있는_임시_폴더가_없으면_처음이라고_보지_않는다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """표지 폴더 자리의 파일은 makedirs 가 FileExistsError 로 알려 "이미 있다"와 같은 갈래로
    떨어진다. 다른 OSError(후보가 모두 막힌 임시 폴더의 FileNotFoundError)도 알리지 않는 쪽이어야
    한다. `launch_hook` 은 반대로 알린다 — 이 훅은 거듭 보이는 것보다 놓치는 것이 낫다."""

    def no_usable_temp() -> str:
        raise FileNotFoundError("No usable temporary directory found")

    monkeypatch.setattr(tempfile, "gettempdir", no_usable_temp)

    assert claim_first("s-1") is False


def test_세션을_모르면_Stop_알림은_침묵이다(tmp_path: Path) -> None:
    transcript = _트랜스크립트(tmp_path / "t.jsonl", [_응답(230_000)])
    temp = tmp_path / "temp"
    temp.mkdir()

    assert _출력(_돌린다(NOTICE, {"transcript_path": str(transcript)}, temp)) is None


def test_클라우드_세션과_서브에이전트의_Stop_은_침묵이다(tmp_path: Path) -> None:
    transcript = _트랜스크립트(tmp_path / "t.jsonl", [_응답(230_000)])
    temp = tmp_path / "temp"
    temp.mkdir()
    stop = {"session_id": "s-1", "hook_event_name": "Stop", "transcript_path": str(transcript)}

    assert _출력(_돌린다(NOTICE, stop, temp, CLAUDE_CODE_REMOTE="true")) is None
    assert _출력(_돌린다(NOTICE, {**stop, "agent_id": "a1"}, temp)) is None
    assert (
        _출력(
            _돌린다(
                HANDOFF,
                _페이로드(transcript, command="git commit -F m"),
                temp,
                CLAUDE_CODE_REMOTE="true",
            )
        )
        is None
    )


def test_Stop_알림은_다음_경계에서_넘어가고_넘기지_않는_때를_적는다() -> None:
    notice = notice_for(230_000)

    assert "230,000" in notice
    assert "셀프 리뷰 직전, 커밋 뒤, PR 연 뒤" in notice
    assert "새 세션" in notice
    assert "끝나" in notice
    assert "같은 경계" in notice
    # 다른 세션이 연 곁 세션도 넘기지 않는다(대기열 328).
    assert "곁 세션" in notice


def test_Stop_알림은_경계가_없는_일은_압축되니_새_세션에서_시키라고_적는다() -> None:
    notice = notice_for(230_000)

    assert "단계 경계가 없는 일" in notice
    # 티켓 뒤에 받은 요청도 커밋하면 경계라(`boundary_of`) 괄호는 일의 종류가 아니라 조건을 든다.
    assert "셀프 리뷰·커밋·PR 없이 끝나는" in notice
    assert "압축" in notice
    assert "새 세션에서 시킨다" in notice
    assert "티켓 작업 중이면 그대로 둔다" in notice
    # 자동 압축 창은 저장소 밖 사용자 설정이라 그 값을 문장에 박지 않는다.
    assert "400,000" not in notice
    assert "40만" not in notice


# --- 두 훅의 같음 ---


def test_두_훅의_문턱과_셈과_표지_이름이_같다(tmp_path: Path) -> None:
    """훅은 서로 import 하지 않는다. 한쪽만 고치면 여기서 빨갛다."""
    assert hook_handoff.THRESHOLD == hook_handoff_notice.THRESHOLD == 200_000
    assert hook_handoff.TAIL_BYTES == hook_handoff_notice.TAIL_BYTES
    assert hook_handoff.STATE_DIR == hook_handoff_notice.STATE_DIR
    assert hook_handoff.marker_name("s-1") == hook_handoff_notice.marker_name("s-1")
    samples = [
        [_응답(250_000)],
        [_응답(250_000), _압축_경계],
        [_응답(300_000), _응답(900_000, sidechain=True), _응답(0, model="<synthetic>")],
        [_도구_결과],
        ["{깨진 줄", _응답(201_000)],
    ]
    for lines in samples:
        assert hook_handoff.session_context(lines) == hook_handoff_notice.session_context(lines)
