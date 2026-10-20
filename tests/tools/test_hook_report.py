"""tools/hook_report.py 검증.

기록의 모양은 이 PC의 세션 기록에서 손으로 본 것을 줄여 옮겼다(2026-10-19). 출력을 낸 훅만
`hook_success` 첨부를 남기고, 그 가운데에는 uv 의 가상 환경 경고(stderr)만 든 것도 섞인다. 도구
호출을 막은 훅은 첨부를 남기지 않고 도구 결과의 `<이벤트>:<도구> hook error: <이유>` 에만 이유가
남는다. Stop 훅이 막으면 `hook_blocking_error` 첨부가 이유와 명령을 함께 든다.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

from tools.hook_report import (
    AMBIGUOUS,
    BLOCK,
    NOTICE,
    UNKNOWN,
    Firing,
    Scan,
    blocking_hook,
    fingerprints,
    folder_name_of,
    introduced_dates,
    main_checkout_folder,
    registered_hooks,
    render,
    scan,
    transcript_files,
)
from tools.launch_hook import notice, skip_reason
from tools.run_hooks import create_fixtures, hook_environment, load_cases, message_of, substitute

ROOT = Path(__file__).resolve().parents[2]
TODAY = date(2026, 10, 19)
REPO = "C--project-agent"
LAUNCH = (
    'uv run --project "${CLAUDE_PROJECT_DIR}" --no-sync python '
    '"${CLAUDE_PROJECT_DIR}/tools/launch_hook.py" '
)
ENV_REASON = "`.env` 는 비밀이라 도구 출력에 싣지 않는다"

type Record = dict[str, object]


def _notice(
    hook: str,
    stdout: str,
    uuid: str,
    when: str = "2026-10-18T01:00:00.000Z",
    *,
    stderr: str = "",
    command: str | None = None,
) -> Record:
    return {
        "type": "attachment",
        "uuid": uuid,
        "timestamp": when,
        "attachment": {
            "type": "hook_success",
            "hookName": "PostToolUse:Edit",
            "hookEvent": "PostToolUse",
            "command": LAUNCH + hook if command is None else command,
            "stdout": stdout,
            "stderr": stderr,
            "exitCode": 0,
            "content": "",
        },
    }


def _denied(
    content: str | list[dict[str, str]], uuid: str, when: str = "2026-10-18T02:00:00.000Z"
) -> Record:
    """`content` 가 글이면 훅 오류의 머리를 붙인 도구 결과이고, 목록이면 그대로 싣는다."""
    body = f"PreToolUse:Bash hook error: {content}" if isinstance(content, str) else content
    return {
        "type": "user",
        "uuid": uuid,
        "timestamp": when,
        "message": {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": "toolu_1", "content": body, "is_error": True}
            ],
        },
    }


def _plain_result(text: str, uuid: str) -> Record:
    return {
        "type": "user",
        "uuid": uuid,
        "timestamp": "2026-10-18T02:00:00.000Z",
        "message": {"role": "user", "content": [{"type": "tool_result", "content": text}]},
    }


def _stopped(hook: str, reason: str, uuid: str) -> Record:
    return {
        "type": "attachment",
        "uuid": uuid,
        "timestamp": "2026-10-18T03:00:00.000Z",
        "attachment": {
            "type": "hook_blocking_error",
            "hookName": "Stop",
            "hookEvent": "Stop",
            "blockingError": {"blockingError": reason, "command": LAUNCH + hook},
        },
    }


def _write(path: Path, *records: Record) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records)
    path.write_text(lines, encoding="utf-8")
    return path


def _context(text: str) -> str:
    """훅이 내는 꼴 그대로 한글을 `\\uXXXX` 로 이스케이프한 계기."""
    output = {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": text}}
    return json.dumps(output)


def _tools(root: Path, sources: dict[str, str]) -> Path:
    tools = root / "tools"
    tools.mkdir(parents=True, exist_ok=True)
    for name, source in sources.items():
        (tools / name).write_text(source, encoding="utf-8")
    return tools


def _counts(result: Scan) -> dict[tuple[str, str], int]:
    counts: dict[tuple[str, str], int] = {}
    for firing in result.firings:
        key = (firing.hook, firing.kind)
        counts[key] = counts.get(key, 0) + 1
    return counts


def test_폴더_이름은_영문자와_숫자_밖의_글자를_대시로_바꾼다() -> None:
    assert folder_name_of("C:\\project\\agent") == REPO
    assert folder_name_of("C:/project/agent") == REPO


def test_주_체크아웃과_그_워크트리의_기록만_읽고_서브에이전트_기록도_읽는다(
    tmp_path: Path,
) -> None:
    main = _write(tmp_path / REPO / "s.jsonl")
    worktree = _write(tmp_path / f"{REPO}--claude-worktrees-x" / "s.jsonl")
    sub = _write(tmp_path / f"{REPO}--claude-worktrees-x" / "s" / "subagents" / "a.jsonl")
    _write(tmp_path / f"{REPO}-runtime-platform" / "s.jsonl")
    _write(tmp_path / f"{REPO}-canary-02b21d0" / "s.jsonl")
    _write(tmp_path / f"C--Users-User-AppData-Local-Temp-claude-{REPO}-x" / "s.jsonl")
    assert sorted(transcript_files(tmp_path, REPO)) == sorted([main, worktree, sub])


def test_알림은_stdout을_낸_hook_success만_세고_stderr만_낸_것은_세지_않는다(
    tmp_path: Path,
) -> None:
    warning = "warning: `VIRTUAL_ENV=...` does not match the project environment path"
    path = _write(
        tmp_path / "s.jsonl",
        _notice("hook_a.py", _context("고쳐라"), "u1"),
        _notice("hook_b.py", "", "u2", stderr=warning),
    )
    assert _counts(scan([path], {})) == {("hook_a.py", NOTICE): 1}


def test_래퍼가_훅_파일이_없어_지나간_알림은_세지_않는다(tmp_path: Path) -> None:
    absent = json.dumps(
        {"systemMessage": "launch_hook: 훅 파일이 없어 돌리지 않고 지나갔다: tools/hook_a.py."},
        ensure_ascii=False,
    )
    path = _write(tmp_path / "s.jsonl", _notice("hook_a.py", absent, "u1"))
    assert scan([path], {}).firings == ()


def test_래퍼가_인자가_틀려_지나간_알림도_세지_않는다(tmp_path: Path) -> None:
    """표준 축 리뷰: 래퍼가 지나가며 내는 문구는 둘인데(`launch_hook.skip_reason`) 하나만 걸렀다."""
    wrong = json.dumps(
        {
            "systemMessage": "launch_hook: 등록 명령의 훅 이름 인자가 하나가 아니라(['a', 'b'])"
            " 아무 훅도 돌리지 않고 지나갔다."
        },
        ensure_ascii=False,
    )
    path = _write(tmp_path / "s.jsonl", _notice("hook_a.py", wrong, "u1"))
    assert scan([path], {}).firings == ()


def test_래퍼가_지나가며_내는_실제_출력은_세지_않는다(tmp_path: Path) -> None:
    """PR 직전 버그 축: 위 두 시험은 문구를 손으로 옮겨, `launch_hook.skip_reason` 의 문구가
    바뀌어도 초록이었다. 래퍼의 함수로 지은 출력을 넣는다."""
    strings = {"hook_event_name": "PostToolUse"}
    outputs = [
        notice(skip_reason(argv), strings)
        for argv in (["launch_hook.py"], ["launch_hook.py", "hook_a.py"])
    ]
    records = [_notice("hook_a.py", out, f"u{i}") for i, out in enumerate(outputs)]
    assert scan([_write(tmp_path / "s.jsonl", *records)], {}).firings == ()


def test_읽는_사이_사라진_기록_파일은_건너뛰고_읽지_못한_파일로_센다(tmp_path: Path) -> None:
    """PR 직전 버그 축: 도는 동안 다른 세션이 기한 지난 기록을 지우면 트레이스백으로 끝났다."""
    path = _write(tmp_path / "s.jsonl", _notice("hook_a.py", _context("고쳐라"), "u1"))
    result = scan([tmp_path / "gone.jsonl", path], {})
    assert _counts(result) == {("hook_a.py", NOTICE): 1}
    assert result.unreadable == 1
    out = render(result, [], {}, TODAY, 28)
    assert "읽지 못한 파일 1개" in out


def test_tools_밖의_훅_명령의_알림은_세지_않는다(tmp_path: Path) -> None:
    plugin = 'bash "${CLAUDE_PLUGIN_ROOT}/hooks/security.sh" hook_a.py'
    path = _write(tmp_path / "s.jsonl", _notice("hook_a.py", _context("x"), "u1", command=plugin))
    assert scan([path], {}).firings == ()


def test_래퍼_전의_등록_모양으로_부른_훅의_알림도_그_훅으로_센다(tmp_path: Path) -> None:
    old = "uv run --no-sync python tools/hook_a.py"
    path = _write(tmp_path / "s.jsonl", _notice("hook_a.py", _context("x"), "u1", command=old))
    assert _counts(scan([path], {})) == {("hook_a.py", NOTICE): 1}


def test_같은_uuid는_파일이_달라도_한_번만_센다(tmp_path: Path) -> None:
    record = _notice("hook_a.py", _context("고쳐라"), "same")
    first = _write(tmp_path / "a.jsonl", record)
    second = _write(tmp_path / "b.jsonl", record)
    assert _counts(scan([first, second], {})) == {("hook_a.py", NOTICE): 1}


def test_발동한_날은_기록_시각의_UTC_날짜다(tmp_path: Path) -> None:
    late = _notice("hook_a.py", _context("x"), "u1", "2026-10-18T23:30:00Z")
    seoul = _notice("hook_a.py", _context("x"), "u2", "2026-10-19T08:30:00+09:00")
    path = _write(tmp_path / "s.jsonl", late, seoul)
    days = [firing.day for firing in scan([path], {}).firings]
    assert days == [date(2026, 10, 18), date(2026, 10, 18)]


def test_도구를_막은_이유는_가장_긴_조각이_든_훅으로_센다(tmp_path: Path) -> None:
    tools = _tools(
        tmp_path,
        {
            "hook_env.py": f'REASON = "{ENV_REASON}"\n',
            "hook_cd.py": (
                "def reason(cmd):\n"
                '    return f"`{cmd}` 가 셸의 작업 폴더를 바꾼다. 절대 경로를 쓴다"\n'
            ),
            "hook_quote.py": 'REASON = "비밀이라 도구 출력에"\n',
        },
    )
    prints = fingerprints(tools, ["hook_env.py", "hook_cd.py", "hook_quote.py"])
    assert blocking_hook(f"`cat .env`: {ENV_REASON}", prints) == "hook_env.py"
    cd_reason = "`cd x` 가 셸의 작업 폴더를 바꾼다. 절대 경로를 쓴다"
    assert blocking_hook(cd_reason, prints) == "hook_cd.py"


def test_어느_훅의_조각도_없는_이유는_모름으로_센다(tmp_path: Path) -> None:
    tools = _tools(tmp_path, {"hook_env.py": f'REASON = "{ENV_REASON}"\n'})
    prints = fingerprints(tools, ["hook_env.py", "hook_gone.py"])
    assert prints["hook_gone.py"] == frozenset()
    assert blocking_hook("플러그인 훅이 막았다", prints) == UNKNOWN


def test_같은_길이의_조각이_두_훅에_있으면_여럿으로_센다(tmp_path: Path) -> None:
    shared = 'REASON = "같은 문장을 두 훅이 함께 쓴다"\n'
    tools = _tools(tmp_path, {"hook_a.py": shared, "hook_b.py": shared})
    prints = fingerprints(tools, ["hook_a.py", "hook_b.py"])
    assert blocking_hook("같은 문장을 두 훅이 함께 쓴다", prints) == AMBIGUOUS


def test_짧은_문자열과_독스트링은_조각으로_쓰지_않는다(tmp_path: Path) -> None:
    """독스트링은 다른 훅의 이유를 인용할 수 있어 조각에서 뺀다."""
    source = f'"""이 훅은 {ENV_REASON} 같은 이유를 낸다."""\n\nKEY = "Bash"\nPATTERN = "deny"\n'
    tools = _tools(tmp_path, {"hook_a.py": source})
    assert fingerprints(tools, ["hook_a.py"])["hook_a.py"] == frozenset()


def test_막은_기록을_훅과_이유의_머리로_센다(tmp_path: Path) -> None:
    tools = _tools(tmp_path, {"hook_env.py": f'REASON = "{ENV_REASON}"\n'})
    prints = fingerprints(tools, ["hook_env.py"])
    path = _write(
        tmp_path / "s.jsonl",
        _denied(ENV_REASON, "u1"),
        _denied("다른 플러그인이 막았다\n둘째 줄", "u2"),
        _stopped("hook_stop.py", "한국어로 다시 쓴다", "u3"),
    )
    result = scan([path], prints)
    assert _counts(result) == {
        ("hook_env.py", BLOCK): 1,
        (UNKNOWN, BLOCK): 1,
        ("hook_stop.py", BLOCK): 1,
    }
    unknown = [firing for firing in result.firings if firing.hook == UNKNOWN]
    assert unknown[0].head == "다른 플러그인이 막았다"


def test_종료_코드_2로_막은_이유는_머리의_명령으로_훅을_고르고_머리_뒤를_적는다(
    tmp_path: Path,
) -> None:
    """두 훅이 같은 조각을 써도 머리의 명령이 훅을 정한다. 훅이 아닌 명령이면 조각으로 고른다."""
    shared = f'REASON = "{ENV_REASON}"\n'
    tools = _tools(tmp_path, {"hook_a.py": shared, "hook_b.py": shared})
    prints = fingerprints(tools, ["hook_a.py", "hook_b.py"])
    exit2 = f"[{LAUNCH}hook_b.py]: {ENV_REASON}\n둘째 줄"
    other = f'[bash "${{CLAUDE_PLUGIN_ROOT}}/x.sh"]: {ENV_REASON}'
    path = _write(tmp_path / "s.jsonl", _denied(exit2, "u1"), _denied(other, "u2"))
    result = scan([path], prints)
    assert result.firings == (
        Firing("hook_b.py", BLOCK, date(2026, 10, 18), ENV_REASON),
        Firing(AMBIGUOUS, BLOCK, date(2026, 10, 18), ENV_REASON),
    )


def test_도구_결과가_글_조각의_목록이어도_막은_이유를_읽는다(tmp_path: Path) -> None:
    blocks = [{"type": "text", "text": "PreToolUse:Grep hook error: 막았다"}]
    path = _write(tmp_path / "s.jsonl", _denied(blocks, "u1"))
    assert _counts(scan([path], {})) == {(UNKNOWN, BLOCK): 1}


def test_훅_오류로_시작하지_않는_도구_결과는_세지_않는다(tmp_path: Path) -> None:
    path = _write(tmp_path / "s.jsonl", _plain_result("출력에 hook error: 가 든다", "u1"))
    assert scan([path], {}).firings == ()


def test_읽지_못한_줄은_세고_건너뛰며_끝의_쓰다_만_줄은_버린다(tmp_path: Path) -> None:
    path = tmp_path / "s.jsonl"
    record = json.dumps(_notice("hook_a.py", _context("x"), "u1"), ensure_ascii=False)
    path.write_text(f'not json\n[1, 2]\n{record}\n{{"type": "attach', encoding="utf-8")
    result = scan([path], {})
    assert result.broken == 2
    assert _counts(result) == {("hook_a.py", NOTICE): 1}


def test_가장_이른_기록_날짜는_훅_밖의_기록까지_본다(tmp_path: Path) -> None:
    early: Record = {"type": "user", "uuid": "e", "timestamp": "2026-09-20T00:00:00Z"}
    path = _write(tmp_path / "s.jsonl", early, _notice("hook_a.py", _context("x"), "u1"))
    assert scan([path], {}).earliest == date(2026, 9, 20)


def test_등록된_훅은_launch_hook_명령에서_뽑고_다른_명령은_뺀다() -> None:
    def entry(command: str) -> dict[str, object]:
        return {"hooks": [{"type": "command", "command": command}]}

    settings = {
        "hooks": {
            "PreToolUse": [entry(LAUNCH + "hook_b.py"), entry(LAUNCH + "hook_a.py")],
            "Stop": [entry(LAUNCH + "hook_a.py")],
            "SessionStart": [entry("echo hi")],
        }
    }
    assert registered_hooks(json.dumps(settings)) == ["hook_a.py", "hook_b.py"]


def _firing(hook: str, kind: str, day: date) -> Firing:
    return Firing(hook, kind, day, "")


def test_표는_창_안의_알림과_막음을_훅마다_센다() -> None:
    result = Scan(
        (
            _firing("hook_a.py", NOTICE, date(2026, 10, 18)),
            _firing("hook_a.py", NOTICE, date(2026, 10, 18)),
            _firing("hook_a.py", BLOCK, date(2026, 10, 1)),
            _firing("hook_a.py", NOTICE, date(2026, 9, 1)),
            _firing("hook_gone.py", BLOCK, date(2026, 10, 2)),
        ),
        files=1,
        broken=0,
        earliest=date(2026, 9, 1),
    )
    out = render(result, ["hook_a.py"], {"hook_a.py": date(2026, 9, 1)}, TODAY, 28)
    assert "2026-09-22 ~ 2026-10-19" in out
    assert "| hook_a.py | 2 | 1 | 2 | 2026-10-18 |" in out
    assert "| hook_gone.py (등록 안 됨) | 0 | 1 | 1 | 2026-10-02 |" in out


def test_창보다_먼저_들였고_창_안에서_발동이_없는_훅을_뺄_후보로_적는다() -> None:
    result = Scan((_firing("hook_a.py", NOTICE, date(2026, 10, 18)),), 1, 0, date(2026, 9, 1))
    introduced = {
        "hook_a.py": date(2026, 9, 1),
        "hook_quiet.py": date(2026, 9, 1),
        "hook_young.py": date(2026, 10, 10),
    }
    out = render(result, ["hook_a.py", "hook_quiet.py", "hook_young.py"], introduced, TODAY, 28)
    lines = out.splitlines()
    candidates = next(line for line in lines if line.startswith("뺄 후보"))
    young = next(line for line in lines if line.startswith("아직 판단하지 않는 훅"))
    assert candidates == "뺄 후보: hook_quiet.py(2026-09-01 들임)"
    assert "hook_young.py(2026-10-10 들임)" in young


def test_들인_날을_모르는_훅은_후보에_넣지_않고_따로_적는다() -> None:
    out = render(Scan((), 1, 0, date(2026, 9, 1)), ["hook_new.py"], {}, TODAY, 28)
    assert "들인 날을 모르는 훅: hook_new.py" in out
    assert "뺄 후보: (없음)" in out


def test_가장_이른_기록이_창의_첫날보다_늦으면_앞쪽이_비었다고_적고_뺄_후보를_내지_않는다() -> None:
    """PR 직전 버그 축: 앞쪽이 빈 창에서도 조용한 훅을 모두 뺄 후보로 냈다."""
    result = Scan((), 1, 0, date(2026, 10, 1))
    out = render(result, ["hook_a.py"], {"hook_a.py": date(2026, 9, 1)}, TODAY, 28)
    assert "가장 이른 기록이 2026-10-01 이라 창의 앞 9일은 기록이 없다" in out
    assert "뺄 후보: 판정하지 않는다(창의 앞 9일에 기록이 없다" in out
    assert "hook_a.py(2026-09-01 들임)" not in out


def test_기록이_하나도_없으면_뺄_후보를_내지_않는다() -> None:
    """PR 직전 버그 축: 틀린 `--projects`·`--repo` 에서 등록 훅이 모두 뺄 후보로 나왔다."""
    out = render(Scan((), 0, 0, None), ["hook_a.py"], {"hook_a.py": date(2026, 9, 1)}, TODAY, 28)
    assert "뺄 후보: 판정하지 않는다(기록이 없다" in out
    assert "hook_a.py(2026-09-01 들임)" not in out


def test_모름과_여럿으로_센_막음은_이유의_머리와_함께_적는다() -> None:
    result = Scan(
        (
            Firing(UNKNOWN, BLOCK, date(2026, 10, 18), "플러그인이 막았다"),
            Firing(UNKNOWN, BLOCK, date(2026, 10, 18), "플러그인이 막았다"),
            Firing(AMBIGUOUS, BLOCK, date(2026, 10, 18), "같은 문장"),
        ),
        1,
        0,
        date(2026, 9, 1),
    )
    out = render(result, [], {}, TODAY, 28)
    assert f"| {UNKNOWN}" not in out
    assert f"| {AMBIGUOUS}" not in out
    assert "어느 훅인지 가르지 못한 막음 3건" in out
    assert "2건 (모름) 플러그인이 막았다" in out
    assert "1건 (여럿) 같은 문장" in out


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/hook_report.py", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=120,
    )


def _hook_repository(root: Path, hooks: list[str]) -> None:
    """`hooks` 를 래퍼 모양으로 등록하고 2026-09-01 에 커밋한 임시 저장소."""
    _tools(root, dict.fromkeys(hooks, ""))
    commands = [{"type": "command", "command": LAUNCH + hook} for hook in hooks]
    (root / ".claude").mkdir()
    settings = json.dumps({"hooks": {"PostToolUse": [{"hooks": commands}]}})
    (root / ".claude" / "settings.json").write_text(settings, encoding="utf-8")
    _git(root, "init", "-q")
    _commit(root, "2026-09-01")


def _commit(root: Path, day: str) -> None:
    """작업 트리 전부를 `day` 의 커밋 날짜로 커밋한다."""
    _git(root, "add", "-A")
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", day],
        cwd=root,
        check=True,
        capture_output=True,
        env={**hook_environment(), "GIT_COMMITTER_DATE": f"{day}T00:00:00Z"},
    )


def test_워크트리에서도_주_체크아웃의_기록_폴더_이름을_짓는다(tmp_path: Path) -> None:
    main = tmp_path / "main"
    main.mkdir()
    _hook_repository(main, [])
    _git(main, "worktree", "add", "-q", str(tmp_path / "wt"))
    folder = main_checkout_folder(main)
    assert folder.endswith("-main")
    assert main_checkout_folder(tmp_path / "wt") == folder


def test_지웠다가_다시_들인_훅은_다시_들인_날부터_센다(tmp_path: Path) -> None:
    _hook_repository(tmp_path, ["hook_a.py", "hook_b.py"])
    (tmp_path / "tools" / "hook_a.py").unlink()
    _commit(tmp_path, "2026-09-05")
    (tmp_path / "tools" / "hook_a.py").write_text("", encoding="utf-8")
    _commit(tmp_path, "2026-10-10")
    assert introduced_dates(tmp_path, ["hook_a.py", "hook_b.py", "hook_new.py"]) == {
        "hook_a.py": date(2026, 10, 10),
        "hook_b.py": date(2026, 9, 1),
    }


def test_못_보는_것_이름을_바꾼_훅은_새_이름을_더한_날부터_센다(tmp_path: Path) -> None:
    _hook_repository(tmp_path, ["hook_old.py"])
    source = 'REASON = "이름을 바꿔도 같은 훅이다"\n'
    (tmp_path / "tools" / "hook_old.py").write_text(source, encoding="utf-8")
    _commit(tmp_path, "2026-09-02")
    _git(tmp_path, "mv", "tools/hook_old.py", "tools/hook_renamed.py")
    _commit(tmp_path, "2026-10-10")
    assert introduced_dates(tmp_path, ["hook_renamed.py"]) == {
        "hook_renamed.py": date(2026, 10, 10)
    }


def test_main을_실제로_불러_임시_저장소의_표와_뺄_후보를_찍는다(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _hook_repository(root, ["hook_a.py", "hook_quiet.py"])
    projects = tmp_path / "projects"
    _write(
        projects / "R" / "s.jsonl",
        _notice("hook_a.py", "", "u0", "2026-09-20T00:00:00.000Z"),  # 창 앞의 기록
        _notice("hook_a.py", _context("고쳐라"), "u1"),
    )
    done = _run(
        *("--projects", str(projects), "--repo", "R"),
        *("--root", str(root), "--today", "2026-10-19"),
    )
    assert done.returncode == 0, done.stderr
    assert "| hook_a.py | 1 | 0 | 1 | 2026-10-18 |" in done.stdout
    assert "뺄 후보: hook_quiet.py(2026-09-01 들임)" in done.stdout


def test_main은_인자가_틀리면_까닭을_내고_2로_끝난다() -> None:
    days = _run("--days", "0")
    assert days.returncode == 2
    assert "양의 정수다: 0" in days.stderr
    today = _run("--today", "어제")
    assert today.returncode == 2
    assert "날짜는 YYYY-MM-DD다: 어제" in today.stderr
    # PR 직전 버그 축: 기록을 다 읽은 뒤 창을 계산하다 OverflowError 트레이스백으로 끝났다
    wide = _run("--days", "99999999")
    assert wide.returncode == 2
    assert "창이 날짜의 범위를 넘는다" in wide.stderr


def test_main은_settings를_읽지_못하면_2로_끝난다(tmp_path: Path) -> None:
    done = _run("--projects", str(tmp_path), "--repo", "R", "--root", str(tmp_path))
    assert done.returncode == 2
    assert "settings.json" in done.stderr


def test_이_저장소의_등록_훅을_스물_넘게_읽고_모두_tools에_있다() -> None:
    hooks = registered_hooks((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert len(hooks) > 20
    assert [hook for hook in hooks if not (ROOT / "tools" / hook).is_file()] == []


def test_이_저장소의_막는_사례마다_훅이_낸_이유를_그_훅으로_센다(tmp_path: Path) -> None:
    """훅 페이로드 표에서 훅마다 처음 나오는 deny·block 사례를 실제로 돌려, 그 이유를 이 도구가
    그 훅으로 세는지 본다. 막는 훅을 새로 들이거나 이유를 바꿔 조각이 겹치거나 짧아지면 여기서
    빨개진다. 커밋이 도는 동안만 있는 자리표시자(`${COMMITTING_REPO}`)와 `env` 를 쓰는 사례는
    빼고, 남은 사례가 막는 훅 열 개 이상을 덮는지 단언한다."""
    hooks = registered_hooks((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    prints = fingerprints(ROOT / "tools", hooks)
    replacements = create_fixtures(tmp_path)
    seen: set[str] = set()
    wrong: list[str] = []
    for case in load_cases():
        blocking = case.expect in ("deny", "block")
        skipped = case.env or "COMMITTING_REPO" in str(case.payload)
        if not blocking or skipped or case.hook in seen:
            continue
        seen.add(case.hook)
        done = subprocess.run(
            [sys.executable, str(ROOT / "tools" / case.hook)],
            input=json.dumps(substitute(case.payload, replacements)).encode("utf-8"),
            capture_output=True,
            env=hook_environment(),
            cwd=ROOT,
            check=False,
            timeout=120,
        )
        stdout = done.stdout.decode("utf-8", "replace")
        reason = message_of(done.returncode, stdout, done.stderr.decode("utf-8", "replace"))
        counted = blocking_hook(reason, prints)
        if counted != case.hook:
            wrong.append(f"{case.hook} ({case.note}) → {counted}: {reason[:80]}")
    assert wrong == []
    assert len(seen) >= 10
