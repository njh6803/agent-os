"""tools/hook_probe_citing_doc.py 의 판정과 표지. main 은 stdin 과 임시 폴더를 바꿔 끼워 표지
길을 보고, 래퍼를 거친 실제 실행은 tools/run_hooks.py 의 표가 본다.

경로는 이 저장소의 명세(`.scratch/<slug>/spec.md`), ADR(`docs/adr/`), 서브에이전트 정의
(`.claude/agents/`) 자리다.
"""

from __future__ import annotations

import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

import pytest
from tools.hook_probe_citing_doc import (
    LEAD,
    TOOLS,
    HookPayload,
    claim_first,
    context_for,
    is_citing_doc,
    main,
    marker_name,
)
from tools.run_hooks import registered_matchers

ROOT = "C:\\project\\agent"
SPEC = ROOT + "\\.scratch\\design-card-build\\spec.md"
ADR = ROOT + "\\docs\\adr\\0036-x.md"
AGENT = ROOT + "\\.claude\\agents\\spec-reviewer.md"
# 대기열 540 의 첫 사례: 프로브가 pnpm 을 거쳐 견준 것을 셸 없이 띄우는 길로 넓혀 적었다.
CITING = "`.scratch/design-card-build/probes/vite_cli.mjs`로 셸 없이 띄워도 바이트까지 같았다."
PLAIN = "카드는 한 줄에 셋씩 놓는다."


def _edit(file_path: str, new_string: str = CITING) -> HookPayload:
    return {"tool_name": "Edit", "tool_input": {"file_path": file_path, "new_string": new_string}}


def _write(file_path: str, content: str = CITING) -> HookPayload:
    return {"tool_name": "Write", "tool_input": {"file_path": file_path, "content": content}}


def test_프로브를_드는_명세_편집은_셋째_항목을_짚는다() -> None:
    context = context_for(_edit(SPEC))
    assert context is not None
    assert context.startswith(LEAD)
    assert ".claude/rules/probes.md" in context
    assert "셋째 항목" in context
    assert "양성 대조" in context
    assert "다른 해석" in context


def test_알림은_잰_상황_밖으로_넓힌_문장을_짚는다() -> None:
    # 대기열 540 의 두 사례: 한 길에서 잰 것을 다른 길로, 잰 부분 집합에서 "~할 길이 없다" 로.
    context = context_for(_edit(SPEC))
    assert context is not None
    assert "README 행" in context
    assert "잰 범위" in context
    assert "길이 없다" in context
    assert "어림이라고 적는다" in context
    assert "`docs/agents/issue-tracker.md` 프로브와 근거 절" in context


def test_알림이_가리키는_절이_그_문서에_있다() -> None:
    # 문서와 절 이름을 알림에서 읽는다. 문서의 제목과 알림의 절 이름 어느 쪽이 바뀌어도 잡는다.
    context = context_for(_edit(SPEC))
    assert context is not None
    pointer = re.search(r"`(docs/[^`]+\.md)` (\S+(?: \S+)*?) 절이다", context)
    assert pointer is not None
    doc, section = pointer.groups()
    lines = (Path(__file__).resolve().parents[2] / doc).read_text(encoding="utf-8").splitlines()
    assert f"## {section}" in lines, f"{doc}: {section}"


def test_알림이_가리키는_규칙에_셋째_항목이_있다() -> None:
    rule = Path(__file__).resolve().parents[2] / ".claude" / "rules" / "probes.md"
    items = [
        line for line in rule.read_text(encoding="utf-8").splitlines() if line.startswith("- ")
    ]
    assert "양성 대조" in items[2]


def test_ADR_와_서브에이전트_정의도_알린다() -> None:
    assert context_for(_edit(ADR)) is not None
    assert context_for(_edit(AGENT)) is not None


def test_Write_는_content_를_본다() -> None:
    assert context_for(_write(SPEC)) is not None
    assert context_for(_write(SPEC, PLAIN)) is None


@pytest.mark.parametrize("cue", ["probes/", "프로브", "탐침", "PROBES/x.py"])
def test_프로브를_가리키는_낱말이_하나라도_있으면_알린다(cue: str) -> None:
    assert context_for(_edit(SPEC, f"앞 {cue} 뒤")) is not None


def test_프로브_낱말이_없는_편집은_지나간다() -> None:
    # 알림이 표지를 쓰므로, 프로브와 무관한 명세 편집이 세션의 한 번을 쓰지 않게 한다.
    for path in (SPEC, ADR, AGENT):
        assert context_for(_edit(path, PLAIN)) is None, path


def test_경로가_맞는_자리만_본다() -> None:
    assert is_citing_doc(SPEC)
    assert is_citing_doc(ADR)
    assert is_citing_doc(AGENT)
    # 슬래시 꼴, 워크트리 사본, 대소문자.
    assert is_citing_doc(SPEC.replace("\\", "/"))
    assert is_citing_doc(ROOT + "\\.claude\\worktrees\\x\\.claude\\agents\\y.md")
    assert is_citing_doc(ROOT + "\\.claude\\worktrees\\x\\docs\\adr\\0001-a.md")
    assert is_citing_doc(ROOT + "\\.Scratch\\x\\Spec.md")
    assert is_citing_doc(ROOT + "\\Docs\\ADR\\0001-a.md")


def test_다른_자리의_파일은_지나간다() -> None:
    for path in (
        # 프로브 README 는 hook_probe_conclusion 이 맡는다.
        ROOT + "\\.scratch\\harness\\probes\\README.md",
        # 명세가 아닌 .scratch 의 파일.
        ROOT + "\\.scratch\\design-card-build\\issues\\01-x.md",
        ROOT + "\\.scratch\\design-card-build\\design\\README.md",
        ROOT + "\\.scratch\\plan.md",
        ROOT + "\\.scratch\\spec.md",
        ROOT + "\\.scratch\\a\\b\\spec.md",
        ROOT + "\\spec.md",
        # ADR 색인과 마크다운이 아닌 파일.
        ROOT + "\\docs\\adr\\README.md",
        ROOT + "\\docs\\adr\\0001-a.txt",
        ROOT + "\\docs\\journal\\2026-11-01-01-x.md",
        ROOT + "\\docs\\other\\adr\\0001-a.md",
        # docs/agents 는 에이전트 문서 규약이지 서브에이전트 정의가 아니다.
        ROOT + "\\docs\\agents\\issue-tracker.md",
        # 서브에이전트 정의가 아닌 .claude 의 파일.
        ROOT + "\\.claude\\rules\\tools.md",
        ROOT + "\\.claude\\skills\\retro\\SKILL.md",
        ROOT + "\\.claude\\agents\\notes.txt",
        # 순서가 어긋난 토막.
        "C:\\agents\\.claude\\x.md",
        "",
    ):
        assert not is_citing_doc(path), path
        assert context_for(_edit(path)) is None, path


def test_다른_도구와_경로_없는_입력은_지나간다() -> None:
    read: HookPayload = {"tool_name": "Read", "tool_input": {"file_path": SPEC}}
    assert context_for(read) is None
    assert context_for({"tool_name": "Edit", "tool_input": {}}) is None
    assert context_for({"tool_name": "Edit"}) is None


@pytest.mark.parametrize(
    "tool_input",
    ["x", {"file_path": 1}, {"file_path": None}, {"file_path": SPEC, "new_string": 1}],
)
def test_꼴이_어긋난_입력은_예외_없이_지나간다(tool_input: object) -> None:
    # HookPayload 에 맞지 않는 꼴이라 main 처럼 JSON 에서 풀어 넘긴다.
    payload = json.loads(json.dumps({"tool_name": "Edit", "tool_input": tool_input}))
    assert context_for(payload) is None


def test_못_보는_것_Bash_로_고친_명세는_지나간다() -> None:
    # Bash 의 실제 입력은 명령 칸뿐이다. 이 훅의 등록 매처에도 Bash 가 없다.
    command = f"sed -i 's/a/probes\\/b/' '{SPEC}'"
    bash = {"tool_name": "Bash", "tool_input": {"command": command}}
    assert context_for(json.loads(json.dumps(bash))) is None


def test_못_보는_것_프로브를_이름_없이_옮긴_문장은_지나간다() -> None:
    # 프로브를 가리키는 낱말 없이 결과만 옮긴 문장은 이 훅이 알아보지 못한다.
    assert context_for(_edit(SPEC, "셸 없이 띄우는 길로 묶음과 장면이 모두 같았다.")) is None


def test_못_보는_것_넓힌_문장인지는_가르지_않는다() -> None:
    # 프로브를 잰 범위 안에서 그대로 옮긴 문장에도 알린다. 넓혔는지는 모델이 가른다.
    assert context_for(_edit(SPEC, "`probes/x.py`가 낸 값을 그대로 옮긴다: 3.")) is not None


def test_못_보는_것_Edit_의_old_string_은_보지_않는다() -> None:
    # 지운 글에 프로브가 있어도 더한 글에 없으면 지나간다.
    payload: HookPayload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": SPEC, "old_string": CITING, "new_string": PLAIN},
    }
    assert context_for(payload) is None


def test_못_보는_것_안_바뀐_기존_낱말에도_알린다() -> None:
    # 앵커가 긴 Edit 의 new_string 은 고치지 않은 프로브 문장도 담는다. 프로브와 상관없는 줄을
    # 고쳤는데도 알린다(거짓 양성). old_string 과 견주지 않는다.
    payload: HookPayload = {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": SPEC,
            "old_string": CITING + " 카드는 한 줄에 둘씩 놓는다.",
            "new_string": CITING + " " + PLAIN,
        },
    }
    assert context_for(payload) is not None


def test_알림은_프로브_규칙이_실려_있지_않을_수_있다고_알린다() -> None:
    # 규칙 파일의 paths 는 프로브 폴더라 명세를 고치는 컨텍스트에는 실리지 않는다.
    context = context_for(_edit(SPEC))
    assert context is not None
    assert "실려 있지 않을 수 있다" in context
    assert "Read" in context


def test_표지는_세션과_에이전트마다_한_번이다(tmp_path: Path) -> None:
    main_key = marker_name("s1", "")
    assert claim_first(main_key, tmp_path)
    assert not claim_first(main_key, tmp_path)
    assert claim_first(marker_name("s1", "agent-a"), tmp_path)
    assert claim_first(marker_name("s2", ""), tmp_path)


def test_표지_폴더를_만들지_못하면_알린다(tmp_path: Path) -> None:
    blocker = tmp_path / "file"
    blocker.write_text("", encoding="utf-8")
    # 디렉터리 자리에 파일이 있어 표지 폴더를 만들지 못한다.
    assert claim_first(marker_name("s1", ""), blocker / "state")
    # 표지 폴더 자리 자체가 파일이면 makedirs 가 FileExistsError 를 낸다. 이미 알린 것으로 읽지
    # 않는다.
    assert claim_first(marker_name("s1", ""), blocker)


def test_표지_파일을_만들지_못하면_알린다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def denied(*_args: object) -> int:
        raise PermissionError

    monkeypatch.setattr(os, "open", denied)
    assert claim_first(marker_name("s1", ""), tmp_path)
    assert claim_first(marker_name("s1", ""), tmp_path)


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


def _session(payload: HookPayload, agent_id: str = "") -> HookPayload:
    payload["session_id"] = "session-1"
    if agent_id:
        payload["agent_id"] = agent_id
    return payload


def test_main_은_세션과_에이전트마다_한_번_알린다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    assert LEAD in _run_main(monkeypatch, capsys, _session(_edit(SPEC)))
    assert _run_main(monkeypatch, capsys, _session(_edit(ADR))) == ""
    assert LEAD in _run_main(monkeypatch, capsys, _session(_edit(SPEC), "agent-a"))


def test_main_은_알리지_않는_편집에는_표지를_쓰지_않는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    assert _run_main(monkeypatch, capsys, _session(_edit(SPEC, PLAIN))) == ""
    assert _run_main(monkeypatch, capsys, _session(_edit(ROOT + "\\README.md"))) == ""
    assert LEAD in _run_main(monkeypatch, capsys, _session(_edit(SPEC)))


def test_main_은_세션을_모르면_표지_없이_호출마다_알린다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    assert LEAD in _run_main(monkeypatch, capsys, _edit(SPEC))
    assert LEAD in _run_main(monkeypatch, capsys, _edit(SPEC))
    assert list(tmp_path.iterdir()) == []


def test_main_은_임시_폴더가_없으면_호출마다_알린다(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def no_temp() -> str:
        raise FileNotFoundError("쓸 수 있는 임시 폴더가 없다")

    monkeypatch.setattr(tempfile, "gettempdir", no_temp)
    assert LEAD in _run_main(monkeypatch, capsys, _session(_edit(SPEC)))
    assert LEAD in _run_main(monkeypatch, capsys, _session(_edit(SPEC)))


def test_표지_폴더는_다른_훅과_겹치지_않는다() -> None:
    from tools import hook_journal_evidence, hook_probe_citing_doc, hook_probe_conclusion

    names = {
        hook_probe_citing_doc.STATE_DIR,
        hook_probe_conclusion.STATE_DIR,
        hook_journal_evidence.STATE_DIR,
    }
    assert len(names) == 3


def test_등록의_매처가_훅이_아는_도구와_같다() -> None:
    assert registered_matchers("hook_probe_citing_doc.py", "PostToolUse") == ["|".join(TOOLS)]
