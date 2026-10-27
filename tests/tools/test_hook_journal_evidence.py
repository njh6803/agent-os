"""tools/hook_journal_evidence.py 의 판정과 표지. main 은 stdin 과 임시 폴더를 바꿔 끼워 표지
길을 보고, 래퍼를 거친 실제 실행은 tools/run_hooks.py 의 표가 본다.

경로는 이 저장소의 일지 자리(`docs/journal/<이름>.md`)다.
"""

from __future__ import annotations

import io
import json
import re
import sys
import tempfile
from pathlib import Path

import pytest
from tools.hook_journal_evidence import (
    LEAD,
    TOOLS,
    HookPayload,
    claim_first,
    context_for,
    is_journal,
    main,
    marker_name,
)
from tools.run_hooks import registered_matchers

ROOT = "C:\\project\\agent"
JOURNAL = ROOT + "\\docs\\journal\\2026-10-26-03-x.md"


def _edit(file_path: str) -> HookPayload:
    return {"tool_name": "Edit", "tool_input": {"file_path": file_path}}


def test_일지를_고치면_결과_문장마다_근거의_종류를_밝히라고_짚는다() -> None:
    # 대기열 445: 일지가 캔버스를 렌더하지 않은 채 지침의 문장을 관찰처럼 적었다.
    context = context_for(_edit(JOURNAL))
    assert context is not None
    assert context.startswith(LEAD)
    for kind in ("탐침이 단언하거나 찍은 것", "손으로 본 것", "코드를 읽은 것", "어림"):
        assert kind in context, kind
    assert "손으로 본 것은 그 명령과 함께 적는다" in context
    assert "문서에서 읽은 것은 그 문서를 출처로 적는다" in context
    assert "보지 않은 것을 본 것처럼" in context
    assert "`docs/agents/issue-tracker.md` 프로브와 근거 절" in context


def test_알림이_가리키는_절이_그_문서에_있다() -> None:
    # 문서와 절 이름을 알림에서 읽는다. 문서의 제목과 알림의 절 이름 어느 쪽이 바뀌어도 잡는다.
    context = context_for(_edit(JOURNAL))
    assert context is not None
    pointer = re.search(r"`(docs/[^`]+\.md)` (\S+(?: \S+)*?) 절이다", context)
    assert pointer is not None
    doc, section = pointer.groups()
    lines = (Path(__file__).resolve().parents[2] / doc).read_text(encoding="utf-8").splitlines()
    assert f"## {section}" in lines, f"{doc}: {section}"


def test_Write_도_알린다() -> None:
    payload: HookPayload = {"tool_name": "Write", "tool_input": {"file_path": JOURNAL}}
    assert context_for(payload) is not None


def test_워크트리_사본과_슬래시_꼴도_일지다() -> None:
    assert is_journal(ROOT + "\\.claude\\worktrees\\x\\docs\\journal\\2026-10-26-01-y.md")
    assert is_journal(JOURNAL.replace("\\", "/"))
    assert is_journal("docs/journal/2026-10-26-01-y.md")


def test_일지가_아닌_파일은_지나간다() -> None:
    for path in (
        ROOT + "\\docs\\journal\\notes.txt",
        ROOT + "\\docs\\journal\\2026-10-26-01-y.md.bak",
        # 일지 폴더 아래 하위 폴더.
        ROOT + "\\docs\\journal\\old\\2026-10-26-01-y.md",
        ROOT + "\\docs\\adr\\0036-x.md",
        ROOT + "\\journal\\2026-10-26-01-y.md",
        ROOT + "\\.scratch\\harness\\probes\\README.md",
        "",
    ):
        assert not is_journal(path), path


def test_다른_도구와_경로_없는_입력은_지나간다() -> None:
    read: HookPayload = {"tool_name": "Read", "tool_input": {"file_path": JOURNAL}}
    assert context_for(read) is None
    assert context_for({"tool_name": "Edit", "tool_input": {}}) is None
    assert context_for({"tool_name": "Edit"}) is None


@pytest.mark.parametrize("tool_input", ["x", {"file_path": 1}, {"file_path": None}])
def test_꼴이_어긋난_입력은_예외_없이_지나간다(tool_input: object) -> None:
    # HookPayload 에 맞지 않는 꼴이라 main 처럼 JSON 에서 풀어 넘긴다.
    payload = json.loads(json.dumps({"tool_name": "Edit", "tool_input": tool_input}))
    assert context_for(payload) is None


def test_못_보는_것_Bash_로_고친_일지는_지나간다() -> None:
    # Bash 의 실제 입력은 명령 칸뿐이고 등록 매처에도 Bash 가 없다. HookPayload 에 없는 칸을
    # 실으려고 main 처럼 JSON 에서 풀어 넘긴다.
    bash = {"tool_name": "Bash", "tool_input": {"command": f"cat >> '{JOURNAL}' <<'EOF'\nx\nEOF"}}
    assert context_for(json.loads(json.dumps(bash))) is None


def test_못_보는_것_대소문자가_다른_경로는_지나간다() -> None:
    # `hook_journal_retro` 의 `is_journal` 과 같이 대소문자를 가린다. 윈도에서 `Docs\Journal` 로
    # 연 일지에는 알리지 않는다.
    assert not is_journal(ROOT + "\\Docs\\Journal\\2026-10-26-01-y.md")
    assert not is_journal(ROOT + "\\docs\\journal\\2026-10-26-01-y.MD")


def test_못_보는_것_결과가_없는_편집에도_알린다() -> None:
    # 머리 한 줄만 쓴 새 일지도 경로가 맞으면 알린다. 결과 문장인지는 모델이 가른다.
    payload = json.loads(
        json.dumps(
            {
                "tool_name": "Write",
                "tool_input": {"file_path": JOURNAL, "content": "# 2026-10-26 (03) x\n"},
            }
        )
    )
    assert context_for(payload) is not None


def test_못_보는_것_근거를_이미_밝힌_문장에도_알린다() -> None:
    payload = json.loads(
        json.dumps(
            {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": JOURNAL,
                    "old_string": "- 초록이다",
                    "new_string": "- 초록이다(`uv run pytest -q` 로 손으로 봤다)",
                },
            }
        )
    )
    assert context_for(payload) is not None


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


def test_표지_파일을_만들지_못하면_알린다(tmp_path: Path) -> None:
    # 폴더는 있고 표지 이름의 부모가 없어 `os.open` 이 FileExistsError 가 아닌 OSError 로 끝나는
    # 갈래다.
    assert claim_first("없는-폴더/표지", tmp_path)


def _run_main(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], payload: HookPayload
) -> str:
    """main 을 한 번 돌려 알린 문장을, 알리지 않았으면 빈 문자열을 돌려준다."""
    stdin = io.TextIOWrapper(io.BytesIO(json.dumps(payload).encode("utf-8")), encoding="utf-8")
    monkeypatch.setattr(sys, "stdin", stdin)
    assert main() == 0
    out = capsys.readouterr().out
    if not out:
        return ""
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert isinstance(context, str)
    return context


def _session_edit(file_path: str, agent_id: str = "") -> HookPayload:
    payload = _edit(file_path)
    payload["session_id"] = "session-1"
    if agent_id:
        payload["agent_id"] = agent_id
    return payload


def test_main_은_세션과_에이전트마다_한_번_알린다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    assert LEAD in _run_main(monkeypatch, capsys, _session_edit(JOURNAL))
    assert _run_main(monkeypatch, capsys, _session_edit(JOURNAL)) == ""
    assert LEAD in _run_main(monkeypatch, capsys, _session_edit(JOURNAL, "agent-a"))


def test_main_은_일지가_아니면_표지를_쓰지_않는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    assert _run_main(monkeypatch, capsys, _session_edit(ROOT + "\\README.md")) == ""
    assert LEAD in _run_main(monkeypatch, capsys, _session_edit(JOURNAL))


def test_못_보는_것_한_번_알린_뒤의_결과_문장은_지나간다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # 세션 첫머리에 머리 한 줄로 일지를 만들면 알림이 그때 쓰이고, 단계를 닫으며 적는 결과
    # 문장에는 다시 알리지 않는다.
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    assert LEAD in _run_main(monkeypatch, capsys, _session_edit(JOURNAL))
    other = ROOT + "\\docs\\journal\\2026-10-26-04-y.md"
    assert _run_main(monkeypatch, capsys, _session_edit(other)) == ""


def test_main_은_임시_폴더가_없으면_호출마다_알린다(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def no_temp() -> str:
        raise FileNotFoundError("쓸 수 있는 임시 폴더가 없다")

    monkeypatch.setattr(tempfile, "gettempdir", no_temp)
    assert LEAD in _run_main(monkeypatch, capsys, _session_edit(JOURNAL))
    assert LEAD in _run_main(monkeypatch, capsys, _session_edit(JOURNAL))


def test_표지_폴더가_프로브_README_계기와_다르다() -> None:
    # 같은 세션의 두 계기가 한 표지를 나눠 쓰면 먼저 뜬 쪽이 다른 쪽을 끈다.
    from tools import hook_journal_evidence, hook_probe_conclusion

    assert hook_journal_evidence.STATE_DIR != hook_probe_conclusion.STATE_DIR


def test_등록의_매처가_훅이_아는_도구와_같다() -> None:
    assert registered_matchers("hook_journal_evidence.py", "PostToolUse") == ["|".join(TOOLS)]
