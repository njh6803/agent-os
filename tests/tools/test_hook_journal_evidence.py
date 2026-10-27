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
    BASH,
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


def _bash(command: str, tool: str = "Bash") -> HookPayload:
    return {"tool_name": tool, "tool_input": {"command": command}}


REL = "docs/journal/2026-10-26-03-x.md"


@pytest.mark.parametrize(
    "command",
    [
        # 대기열 501 의 꼴: heredoc 으로 덧붙였다.
        f"cat >> {REL} <<'EOF'\n- 러너의 git 2.56\nEOF",
        f"cat >> '{JOURNAL}' <<'EOF'\nx\nEOF",
        f'echo x > "{REL}"',
        f"printf 'x\\n' 1>>{REL}",
        f"echo x | tee -a {REL}",
        f"echo x | tee {REL} >/dev/null",
        f"sed -i 's/a/b/' {REL}",
        f"sed -E -i.bak 's/a/b/' {REL}",
        f"sed --in-place 's/a/b/' {REL}",
        f"uv run python - <<'EOF'\nfrom pathlib import Path\nPath('{REL}').write_text('x')\nEOF",
        f"uv run python -c \"open('{REL}', 'a').write('x')\"",
        f"cd /c/project/agent && cat >> {REL} <<'EOF'\nx\nEOF",
        f"echo x 2>{REL}",
        f"echo x &> {REL}",
        f"echo x >| {REL}",
        f"echo x >& {REL}",
        f"echo x >> ./{REL}",
        f"sed -Ei 's/a/b/' {REL}",
        f"sed {REL} -i 's/a/b/'",
        f"sed -i s/a/b/ /tmp/other.md {REL}",
        f"echo x | tee '{REL}'",
        f"python3.12 -c \"open('{REL}', 'w')\"",
        f"py -c \"open('{REL}', 'a')\"",
        f"uv run python -c \"f = open('{REL}', 'ab')\"",
        f"uv run python -c \"f = open('{REL}', 'r+')\"",
        f"uv run python -c \"open('{REL}', mode='w')\"",
        f"uv run python -c \"from pathlib import Path; Path('{REL}').write_bytes(b'x')\"",
        f"uv run python -c \"open('{REL}', 'a').writelines(['x'])\"",
        f"echo x | sudo tee -a {REL}",
    ],
)
def test_Bash_가_일지를_쓰면_알린다(command: str) -> None:
    context = context_for(_bash(command))
    assert context is not None
    assert context.startswith(LEAD)


@pytest.mark.parametrize(
    "command",
    [
        f"cat {REL}",
        f"sed -n 1,5p {REL}",
        # 인용 부호 안이나 첫 낱말이 아닌 자리의 `-i`·`tee` 는 쓰기가 아니다.
        f"sed -n '/ -i/p' {REL}",
        f'sed -n "s/a -i/b/p" {REL}',
        f"grep tee {REL}",
        f"grep -n 다음 {REL}",
        f"git add {REL}",
        f"wc -l < {REL}",
        f"cat {REL} > /tmp/copy.md",
        f"cat {REL} | tee /tmp/copy.md",
        f"echo x | tee /tmp/a.md; cat {REL}",
        f"sed -i 's/a/b/' /tmp/a.md && cat {REL}",
        f"uv run python tools/sibling_overlap.py > /tmp/so.log 2>&1; ls {REL}",
        f"uv run python - <<'EOF'\nprint(open('{REL}').read())\nEOF",
        f"uv run python -c \"print(open('{REL}', 'rb').read())\"",
        "echo x >> docs/adr/0036-x.md",
        "echo x >> docs/journal/notes.txt",
        "echo x >> mydocs/journal/2026-10-26-03-x.md",
        "",
    ],
)
def test_Bash_가_일지를_읽기만_하거나_일지_밖을_쓰면_지나간다(command: str) -> None:
    assert context_for(_bash(command)) is None


def test_못_보는_것_변수에_든_일지_경로는_지나간다() -> None:
    # 경로를 명령 글에서만 찾는다. 셸이 펼칠 값은 모른다.
    assert context_for(_bash(f"f={REL}; cat >> \"$f\" <<'EOF'\nx\nEOF")) is None


def test_못_보는_것_cp_mv_로_만든_일지는_지나간다() -> None:
    assert context_for(_bash(f"cp /tmp/draft.md {REL}")) is None
    assert context_for(_bash(f"mv /tmp/draft.md {REL}")) is None


def test_못_보는_것_인자로_경로를_받아_쓰는_스크립트는_지나간다() -> None:
    # python 은 명령 글에 쓰기 낱말이 있어야 쓴다고 본다. 스크립트 파일 안의 쓰기는 읽지 않는다.
    assert context_for(_bash(f"uv run python tools/append.py {REL}")) is None


def test_못_보는_것_앞에_낱말이_붙은_tee_sed_와_다른_제자리_편집은_지나간다() -> None:
    # 단순 명령의 첫 낱말만 본다(`sudo` 하나는 건너뛴다).
    for command in (
        f"echo x | sudo -u x tee {REL}",
        f"echo a | xargs sed -i 's/a/b/' {REL}",
        f"awk -i inplace '{{print}}' {REL}",
        f"perl -i -pe 's/a/b/' {REL}",
    ):
        assert context_for(_bash(command)) is None, command


def test_못_보는_것_쓰기_낱말_밖의_길로_쓰는_python_은_지나간다() -> None:
    for command in (
        f"uv run python -c \"import shutil; shutil.copy('/tmp/a.md', '{REL}')\"",
        f"uv run python -c \"import os; os.replace('/tmp/a.md', '{REL}')\"",
    ):
        assert context_for(_bash(command)) is None, command


def test_못_보는_것_python_이_다른_파일을_쓰고_일지는_읽기만_해도_알린다() -> None:
    # 거짓 양성. 쓰기 낱말이 명령 어디에 있든 python 이 일지를 쓴다고 본다.
    command = (
        f"uv run python - <<'EOF'\ntext = open('{REL}').read()\n"
        "open('/tmp/copy.md', 'w').write(text)\nEOF"
    )
    assert context_for(_bash(command)) is not None


def test_못_보는_것_PowerShell_로_고친_일지는_지나간다() -> None:
    # 등록 매처에도 PowerShell 이 없다.
    assert context_for(_bash(f"Add-Content {REL} 'x'", tool="PowerShell")) is None


def test_못_보는_것_쓰는_꼴을_글로만_든_명령에도_알린다() -> None:
    # 거짓 양성. 커밋 메시지의 heredoc 본문이 쓰는 꼴을 인용해도 명령 글에서만 가르므로 알린다.
    command = f"git commit -F - <<'EOF'\nfix: `cat >> {REL}` 꼴을 본다\nEOF"
    assert context_for(_bash(command)) is not None


def test_Bash_와_Write_가_표지를_같이_쓴다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    bash = _bash(f"cat >> {REL} <<'EOF'\nx\nEOF")
    bash["session_id"] = "session-1"
    assert LEAD in _run_main(monkeypatch, capsys, bash)
    assert _run_main(monkeypatch, capsys, _session_edit(JOURNAL)) == ""
    assert _run_main(monkeypatch, capsys, bash) == ""


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
    assert registered_matchers("hook_journal_evidence.py", "PostToolUse") == [
        "|".join(TOOLS),
        BASH,
    ]
