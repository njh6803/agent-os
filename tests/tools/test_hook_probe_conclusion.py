"""tools/hook_probe_conclusion.py 의 판정과 표지. main 은 stdin 과 임시 폴더를 바꿔 끼워 표지
길을 보고, 래퍼를 거친 실제 실행은 tools/run_hooks.py 의 표가 본다.

경로는 이 저장소의 프로브 README 자리다(`docs/agents/issue-tracker.md` 의 프로브와 근거 절).
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
from tools.hook_probe_conclusion import (
    LEAD,
    TOOLS,
    HookPayload,
    claim_first,
    context_for,
    is_probe_readme,
    main,
    marker_name,
)
from tools.run_hooks import registered_matchers

ROOT = "C:\\project\\agent"
README = ROOT + "\\.scratch\\harness\\probes\\README.md"


def _edit(file_path: str) -> HookPayload:
    return {"tool_name": "Edit", "tool_input": {"file_path": file_path}}


def test_프로브_README_를_고치면_셋째_항목을_짚는다() -> None:
    context = context_for(_edit(README))
    assert context is not None
    assert context.startswith(LEAD)
    assert ".claude/rules/probes.md" in context
    assert "양성 대조" in context
    assert "다른 해석" in context


def test_프로브_README_를_고치면_근거의_종류와_결과를_본_뒤_바꾼_기준을_짚는다() -> None:
    # 대기열 421: 손으로 본 결과를 탐침의 결과 사이에 측정처럼 적었고, 결과를 본 뒤 바꾼 기준을
    # 밝히지 않았다.
    context = context_for(_edit(README))
    assert context is not None
    # "어림" 만으로는 첫째 몫의 "어림이라고 적는다" 에도 맞아, 둘째 몫에만 있는 꼴로 본다.
    for kind in ("탐침이 단언하거나 찍은 것", "저장한 원본을 손으로 본 것", "어림인가"):
        assert kind in context, kind
    assert "커밋하지 않은 스크립트나 사본으로 돌린 것도 손으로 본 것" in context
    assert "손으로 본 것은 그 명령과 함께 적는다" in context
    assert "손으로 본 쪽에 그렇다고 붙인다" in context
    assert "결과를 본 뒤 판정 기준" in context
    assert "바꾼 기준과 그 까닭" in context
    assert "코드 읽기와 웹 요약까지 든 근거의 갈래 전체" in context
    assert "`docs/agents/issue-tracker.md` 프로브와 근거 절" in context


def test_알림이_가리키는_절이_그_문서에_있다() -> None:
    # 문서와 절 이름을 알림에서 읽는다. 문서의 제목과 알림의 절 이름 어느 쪽이 바뀌어도 잡는다.
    context = context_for(_edit(README))
    assert context is not None
    pointer = re.search(r"`(docs/[^`]+\.md)` (\S+(?: \S+)*?) 절이다", context)
    assert pointer is not None
    doc, section = pointer.groups()
    lines = (Path(__file__).resolve().parents[2] / doc).read_text(encoding="utf-8").splitlines()
    assert f"## {section}" in lines, f"{doc}: {section}"


def test_Write_도_알린다() -> None:
    payload: HookPayload = {"tool_name": "Write", "tool_input": {"file_path": README}}
    assert context_for(payload) is not None


def test_하위_폴더와_워크트리_사본과_슬래시_꼴도_프로브_README_다() -> None:
    # 여러 파일로 된 프로브는 제 폴더에 README 를 둔다(`.scratch/harness/probes/session_cost/`).
    assert is_probe_readme(ROOT + "\\.scratch\\harness\\probes\\session_cost\\README.md")
    worktree = ROOT + "\\.claude\\worktrees\\x\\.scratch\\token-usage\\probes\\README.md"
    assert is_probe_readme(worktree)
    assert is_probe_readme(README.replace("\\", "/"))
    assert is_probe_readme(".scratch/conversation/probes/README.md")


def test_루트가_아닌_자리의_scratch_도_프로브_README_로_본다() -> None:
    # 못 보는 것이 아니라 넓은 쪽: 규칙의 `paths` 는 루트의 `.scratch` 만 잡지만 훅은 토막만 본다.
    assert is_probe_readme(ROOT + "\\docs\\.scratch\\x\\probes\\README.md")


def test_대소문자가_다른_이름도_프로브_README_다() -> None:
    assert is_probe_readme(ROOT + "\\.Scratch\\harness\\Probes\\Readme.md")


def test_프로브_README_가_아닌_파일은_지나간다() -> None:
    for path in (
        ROOT + "\\.scratch\\harness\\probes\\guard_hooks_time.py",
        ROOT + "\\.scratch\\harness\\probes\\notes.md",
        # probes 가 아닌 폴더의 README(디자인 산출물 표).
        ROOT + "\\.scratch\\design-system\\design\\README.md",
        ROOT + "\\.scratch\\harness\\README.md",
        # .scratch 밖의 probes.
        ROOT + "\\web\\probes\\README.md",
        ROOT + "\\README.md",
        ROOT + "\\.scratch\\harness\\probes\\README.md.bak",
        # probes 가 .scratch 보다 앞이다.
        "C:\\probes\\.scratch\\x\\README.md",
        "",
    ):
        assert not is_probe_readme(path), path


def test_다른_도구와_경로_없는_입력은_지나간다() -> None:
    read: HookPayload = {"tool_name": "Read", "tool_input": {"file_path": README}}
    assert context_for(read) is None
    assert context_for({"tool_name": "Edit", "tool_input": {}}) is None
    assert context_for({"tool_name": "Edit"}) is None


@pytest.mark.parametrize("tool_input", ["x", {"file_path": 1}, {"file_path": None}])
def test_꼴이_어긋난_입력은_예외_없이_지나간다(tool_input: object) -> None:
    # HookPayload 에 맞지 않는 꼴이라 main 처럼 JSON 에서 풀어 넘긴다.
    payload = json.loads(json.dumps({"tool_name": "Edit", "tool_input": tool_input}))
    assert context_for(payload) is None


def test_못_보는_것_Bash_로_고친_README_는_지나간다() -> None:
    # Bash 의 실제 입력은 명령 칸뿐이다. 이 훅의 등록 매처에도 Bash 가 없다. HookPayload 에 없는
    # 칸(command)을 실으려고 main 처럼 JSON 에서 풀어 넘긴다.
    command = f"sed -i 's/a/b/' '{README}'"
    bash = {"tool_name": "Bash", "tool_input": {"command": command}}
    assert context_for(json.loads(json.dumps(bash))) is None


def test_못_보는_것_README_밖에_적은_결과와_결론은_지나간다() -> None:
    for path in (
        ROOT + "\\.claude\\rules\\tools.md",
        ROOT + "\\docs\\adr\\0036-x.md",
        ROOT + "\\.scratch\\harness\\probes\\choice_facts\\probe.py",
        # 대기열 421 의 세 사례가 README 밖에서 근거의 종류를 어긴 자리.
        ROOT + "\\tools\\hook_choice_facts.py",
        ROOT + "\\.scratch\\model-rerun\\spec.md",
        ROOT + "\\.scratch\\design-reverse-sync\\probes\\contrast_module_mutations.toml",
    ):
        assert context_for(_edit(path)) is None, path


def test_못_보는_것_결과도_결론도_아닌_편집에도_알린다() -> None:
    # 변이 수만 고친 행이어도 경로가 맞으면 알린다. 결과나 결론인지는 모델이 가른다. HookPayload 에
    # 없는 칸(old_string·new_string)을 실으려고 main 처럼 JSON 에서 풀어 넘긴다.
    payload = json.loads(
        json.dumps(
            {
                "tool_name": "Edit",
                "tool_input": {"file_path": README, "old_string": "변이 7", "new_string": "변이 8"},
            }
        )
    )
    assert context_for(payload) is not None


def test_못_보는_것_근거를_이미_밝힌_결과에도_알린다() -> None:
    # 근거의 종류를 밝혔는지는 판정하지 않는다. 경로가 맞으면 알린다. 칸을 싣는 까닭은 위 시험과
    # 같다.
    payload = json.loads(
        json.dumps(
            {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": README,
                    "old_string": "| C | 옮겼다 |",
                    "new_string": "| C | 옮겼다(저장한 원본을 손으로 봤다) |",
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
    assert LEAD in _run_main(monkeypatch, capsys, _session_edit(README))
    assert _run_main(monkeypatch, capsys, _session_edit(README)) == ""
    assert LEAD in _run_main(monkeypatch, capsys, _session_edit(README, "agent-a"))


def test_main_은_프로브_README_가_아니면_표지를_쓰지_않는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    assert _run_main(monkeypatch, capsys, _session_edit(ROOT + "\\README.md")) == ""
    assert LEAD in _run_main(monkeypatch, capsys, _session_edit(README))


def test_못_보는_것_한_번_알린_뒤의_결과와_결론은_지나간다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # 결과도 결론도 아닌 편집(변이 수)으로 알림을 넘기면, 같은 세션의 뒤 결과·결론 편집은 알림을
    # 받지 못한다.
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    assert LEAD in _run_main(monkeypatch, capsys, _session_edit(README))
    other = ROOT + "\\.scratch\\token-usage\\probes\\README.md"
    assert _run_main(monkeypatch, capsys, _session_edit(other)) == ""


def test_main_은_임시_폴더가_없으면_호출마다_알린다(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def no_temp() -> str:
        raise FileNotFoundError("쓸 수 있는 임시 폴더가 없다")

    monkeypatch.setattr(tempfile, "gettempdir", no_temp)
    assert LEAD in _run_main(monkeypatch, capsys, _session_edit(README))
    assert LEAD in _run_main(monkeypatch, capsys, _session_edit(README))


def test_등록의_매처가_훅이_아는_도구와_같다() -> None:
    assert registered_matchers("hook_probe_conclusion.py", "PostToolUse") == ["|".join(TOOLS)]
