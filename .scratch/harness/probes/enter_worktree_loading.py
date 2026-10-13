"""주 체크아웃에서 시작해 `EnterWorktree` 로 들어간 세션이 스킬과 서브에이전트 정의를 어느 사본에서
싣는지 잰다.

대기열 189 다. `docs/constitution/operations.md` 환경 규약 상세의 모드 표가 근거로 든다. 이 저장소의
모양(워크트리가 주 체크아웃 안의 `.claude/worktrees/` 에 있고 그 폴더가 `.gitignore` 에 있다)을 임시
디렉터리에 흉내 낸다. 주 체크아웃 `outer` 와 그 워크트리 `outer/.claude/worktrees/inner` 에 같은
이름의 스킬(`probe-skill`)과 서브에이전트 정의(`probe-agent`)를 두고, 판마다 표지 낱말을 다르게
한다.
- 스킬: 주 체크아웃 커밋 노을고래, 워크트리(꺼낸 뒤 고친다. 커밋하지 않는다) 새벽수달, 주 체크아웃을
  바깥에서 바꾼 판 한낮여우, 워크트리를 고친 판 은빛참새.
- 서브에이전트 정의: 같은 차례로 가을사슴, 별빛두더지, 겨울솔개, 봄비개구리.

갈래마다 `claude -p` 하나를 `--input-format stream-json` 으로 띄워 턴을 나눠 보낸다. 첫 턴은 모든
갈래가 같다. `EnterWorktree(path)` 로 워크트리에 들어가 Skill 도구로 `probe-skill` 을 부르고, Agent
도구로 `probe-agent` 에게 표지 낱말을 묻고, 스킬 목록에서 이름에 `probe-skill` 이 든 것을 옮긴다. 그
뒤 갈래마다 하나를 하고 5초 기다린 뒤 같은 물음(측정 턴)을 다시 보낸다. 측정 턴은 목록에 이름이
여럿이면 그 이름마다 Skill 을 부른다.
- `대조`: 아무것도 바꾸지 않는다. 사람의 다음 메시지만으로 목록이 바뀌는지 가른다.
- `주변경`: 프로브가 주 체크아웃의 스킬과 정의를 함께 바꾼다. 다른 세션이 주 체크아웃을 당긴 것의
  흉내이고, 파일을 바로 쓸 뿐 git 으로 당기지는 않는다.
- `안편집`: 세션이 둘째 턴에 Read 와 Edit 로 워크트리 사본 둘을 고치고, 셋째 턴이 측정 턴이다. Edit
  결과가 오류이거나, 사본 둘마다 그 파일을 겨눈 Edit 가 새 표지를 쓰지 않았으면 편집이 났다는 표지가
  없어 무효다. `.claude/` 아래 쓰기는 `acceptEdits` 로 띄우면
  승인을 묻다 거부됐다(커밋하지 않은 앞 판의 실행). 그래서 `bypassPermissions` 로 띄우고 도구는
  `--tools` 로 여섯만 둔다.
- `안바깥편집`: 프로브가 워크트리 사본 둘을 바깥에서 고친다.

판정은 원본에서 한다. 스킬은 Skill 이 실은 메시지의 `Base directory for this skill:` 줄과 그 본문의
표지 낱말, 정의는 Agent 결과에 든 표지 낱말이다. 이미 실린 스킬을 바뀌지 않은 채 다시 부르면 결과가
`Launching skill` 뿐이고 본문을 다시 싣지 않아(첫 실행의 `대조` 갈래), 그 호출은 `다시 싣지 않음`
으로 찍는다. 목록은 원본 이벤트에 없어 모델이 옮긴 답을 찍는다. 측정 턴에 Read·Edit 를 불렀거나(답이
파일을 읽은 데서 왔을 수 있다), 서브에이전트가 도구를 불렀거나, Skill 을 부르지 않았거나, Agent
결과가 없거나, 첫 턴에 기준 폴더 줄이 없거나 `EnterWorktree` 가 오류였으면 그 턴은 측정이 아니라고
찍는다. 기대를 단언하지 않고 본 것을 찍는다. 결과 이벤트는 `type` 이 첫 키가 아니라 줄을 풀어서
알아본다.

못 보는 것: 데스크톱 앱의 세션은 재지 않는다(이 프로브는 `claude` CLI 다). 목록의 변화는 모델의
답이라 모델이 옮기지 않은 이름은 보이지 않는다. 5초 안에 오지 않는 늦은 다시 읽기는 놓친다. 갈래마다
한 회차이고, 스킬과 정의 가운데 한쪽 폴더만 바뀐 경우는 가르지 않는다.

돌리는 법: `uv run python .scratch/harness/probes/enter_worktree_loading.py <출력 디렉터리>`.
`claude` CLI 와 인증이 든다. 갈래마다 sonnet 세션이 하나이고(서브에이전트 호출이 둘씩 더 있다) 모두
넷이다. 임시 디렉터리의 상위 폴더(홈 폴더는 빼고)에 `.claude/` 가 있으면 섞이므로 돌리지 않고 2 로
끝난다. 갈래마다 stream-json 원본(`.jsonl`)을 출력 디렉터리에 남기고 임시 디렉터리는 끝에 지운다.
종료 코드: 0 측정 턴이 모두 측정이 되고 편집 턴의 편집이 났다, 1 측정이 아닌 턴이나 편집이 나지
않은 편집 턴이 있다, 2 임시 디렉터리의 상위 폴더에 `.claude/` 가 있다.
"""

import json
import os
import queue
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

SKILL_MARKS = {"주": "노을고래", "안": "새벽수달", "주새판": "한낮여우", "안새판": "은빛참새"}
AGENT_MARKS = {"주": "가을사슴", "안": "별빛두더지", "주새판": "겨울솔개", "안새판": "봄비개구리"}
BRANCHES = ("대조", "주변경", "안편집", "안바깥편집")
COMMAND = [
    "claude",
    "-p",
    "--setting-sources",
    "project,local",
    "--strict-mcp-config",
    "--model",
    "sonnet",
    "--permission-mode",
    "bypassPermissions",
    "--tools",
    "EnterWorktree,Skill,Agent,Read,Edit,ToolSearch",
    "--input-format",
    "stream-json",
    "--output-format",
    "stream-json",
    "--verbose",
]
TIMEOUT = 600
SETTLE = 5
MEASURE = (
    "Skill 도구로 스킬을 부르고, Agent 도구로 서브에이전트에게 묻고, 스킬 목록을 옮긴다. "
    "파일을 읽거나 고치지 마라. 1) 지금 네 스킬 목록에서 이름에 probe-skill 이 든 스킬을 "
    "이름 그대로 모두 찾아 각각 Skill 도구로 한 번씩 부른다. 2) Agent 도구로 subagent_type 이 "
    "probe-agent 인 서브에이전트에게 '네 지시에 적힌 표지 낱말 하나만 답하라. 도구를 쓰지 "
    "마라.'라고 묻는다. 3) 답에 다음 셋을 적는다. 스킬 목록에서 이름에 probe-skill 이 든 "
    "이름 전부(글자 그대로), 부른 스킬마다 그 본문의 표지 낱말, 서브에이전트가 답한 표지 낱말."
)


def first_turn(inner: Path) -> str:
    return (
        f"EnterWorktree 도구를 path 인자 {inner} 로 불러 그 워크트리에 들어간다. 그 뒤 " + MEASURE
    )


def edit_turn(inner: Path) -> str:
    skill = inner / ".claude" / "skills" / "probe-skill" / "SKILL.md"
    agent = inner / ".claude" / "agents" / "probe-agent.md"
    return (
        f"Read 로 {skill} 와 {agent} 를 읽고, Edit 로 두 파일의 표지 낱말을 바꾼다. 앞 파일은 "
        f"{SKILL_MARKS['안']} 을 {SKILL_MARKS['안새판']} 으로, 뒤 파일은 {AGENT_MARKS['안']} 을 "
        f"{AGENT_MARKS['안새판']} 으로. 다른 것은 하지 마라."
    )


def clean_env() -> dict[str, str]:
    """이 저장소를 가리키는 `GIT_*` 를 벗긴다. 남으면 임시 디렉터리의 git 이 이 저장소에 닿는다."""
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


def git(*args: str, cwd: Path) -> None:
    done = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False, env=clean_env()
    )
    if done.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} 실패({done.returncode}): {done.stderr.strip()}")


def write_skill(checkout: Path, mark: str) -> None:
    folder = checkout / ".claude" / "skills" / "probe-skill"
    folder.mkdir(parents=True, exist_ok=True)
    text = (
        "---\nname: probe-skill\ndescription: 프로브용 스킬. 부르라고 하면 부른다.\n---\n\n"
        f"이 스킬의 표지 낱말은 {mark}다.\n"
    )
    (folder / "SKILL.md").write_text(text, encoding="utf-8", newline="\n")


def write_agent(checkout: Path, mark: str) -> None:
    folder = checkout / ".claude" / "agents"
    folder.mkdir(parents=True, exist_ok=True)
    text = (
        "---\nname: probe-agent\ndescription: 프로브용 서브에이전트. 표지 낱말을 묻는다.\n"
        "tools: Read\n---\n\n"
        f"너의 표지 낱말은 {mark}다. 표지 낱말을 물으면 도구를 쓰지 말고 그 낱말 하나만 "
        "답한다.\n"
    )
    (folder / "probe-agent.md").write_text(text, encoding="utf-8", newline="\n")


def layout(root: Path) -> tuple[Path, Path]:
    outer = root / "outer"
    outer.mkdir()
    git("init", "-q", "-b", "main", cwd=outer)
    (outer / ".gitignore").write_text("/.claude/worktrees/\n", encoding="utf-8", newline="\n")
    write_skill(outer, SKILL_MARKS["주"])
    write_agent(outer, AGENT_MARKS["주"])
    git("add", ".", cwd=outer)
    git(
        "-c",
        "user.name=probe",
        "-c",
        "user.email=probe@invalid",
        "commit",
        "-qm",
        "init",
        cwd=outer,
    )
    inner = outer / ".claude" / "worktrees" / "inner"
    git("worktree", "add", "-q", "-b", "inner", str(inner), cwd=outer)
    write_skill(inner, SKILL_MARKS["안"])
    write_agent(inner, AGENT_MARKS["안"])
    return outer, inner


def remove_tree(root: Path) -> None:
    """임시 디렉터리를 지운다. 윈도에서는 `.git/objects` 의 읽기 전용 파일이 지우기를 막아, 쓰기를
    풀고 한 번 더 지운다."""

    def writable_retry(function: Callable[[str], object], path: str, _error: BaseException) -> None:
        os.chmod(path, stat.S_IWRITE)
        function(path)

    shutil.rmtree(root, onexc=writable_retry)


def ancestors_with_claude_dir(path: Path) -> list[Path]:
    """홈 폴더를 뺀 상위 폴더의 `.claude/`. 홈의 것은 사용자 설정이고 `--setting-sources` 가
    뺀다."""
    return [
        parent / ".claude"
        for parent in path.parents
        if parent != Path.home() and (parent / ".claude").is_dir()
    ]


def user_line(text: str) -> bytes:
    message = {"type": "user", "message": {"role": "user", "content": text}}
    return (json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8")


def drive(branch: str, outer: Path, inner: Path) -> str:
    """갈래 하나를 돌려 stream-json 원본을 돌려준다. 턴마다 결과 이벤트를 기다린 뒤 다음 턴을
    보낸다. 제한 시간을 넘기면 그때까지의 출력이라 뒤 턴이 없어 측정이 아니라고 찍힌다."""
    executable = shutil.which(COMMAND[0]) or COMMAND[0]
    process = subprocess.Popen(
        [executable, *COMMAND[1:]],
        cwd=outer,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env=clean_env(),
    )
    stdin, stdout = process.stdin, process.stdout
    assert stdin is not None and stdout is not None
    # 읽기를 스레드에 두어야 출력이 멎어도 제한 시간이 걸린다. 결과 이벤트는 `type` 이 첫 키가
    # 아니라(첫 키가 `duration_api_ms` 였다) 줄 머리가 아니라 풀어서 알아본다.
    pending: queue.Queue[str | None] = queue.Queue()

    def pump() -> None:
        for raw in iter(stdout.readline, b""):
            pending.put(raw.decode("utf-8", errors="replace"))
        pending.put(None)

    threading.Thread(target=pump, daemon=True).start()
    lines: list[str] = []
    deadline = time.monotonic() + TIMEOUT

    def send_and_wait(text: str) -> bool:
        stdin.write(user_line(text))
        stdin.flush()
        while (left := deadline - time.monotonic()) > 0:
            try:
                line = pending.get(timeout=min(left, 5))
            except queue.Empty:
                continue
            if line is None:
                return False
            lines.append(line)
            if event_type(line) == "result":
                return True
        return False

    def change_outer() -> None:
        write_skill(outer, SKILL_MARKS["주새판"])
        write_agent(outer, AGENT_MARKS["주새판"])

    def change_inner() -> None:
        write_skill(inner, SKILL_MARKS["안새판"])
        write_agent(inner, AGENT_MARKS["안새판"])

    turns: list[Callable[[], None] | str] = [first_turn(inner)]
    if branch == "주변경":
        turns.append(change_outer)
    elif branch == "안편집":
        turns.append(edit_turn(inner))
    elif branch == "안바깥편집":
        turns.append(change_inner)
    turns.append(MEASURE)
    try:
        for turn in turns:
            if isinstance(turn, str):
                if not send_and_wait(turn):
                    break
            else:
                turn()
            time.sleep(SETTLE)
    finally:
        stdin.close()
        try:
            process.wait(timeout=60)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    while (line := pending.get()) is not None:
        lines.append(line)
    return "".join(lines)


def event_type(line: str) -> str | None:
    if not line.lstrip().startswith("{"):
        return None
    try:
        event = json.loads(line)
    except ValueError:  # 제한 시간에 끊기면 마지막 줄이 잘린다
        return None
    return event.get("type") if isinstance(event, dict) else None


@dataclass
class Turn:
    """턴 하나에서 본 것."""

    tools: list[str] = field(default_factory=list)
    sub_tools: int = 0
    worktree_error: bool | None = None
    skill_dirs: list[str] = field(default_factory=list)
    skill_marks: list[str] = field(default_factory=list)
    agent_marks: list[str] = field(default_factory=list)
    agent_answered: bool = False
    edit_errors: int = 0
    edits: list[tuple[str, str]] = field(default_factory=list)  # (file_path, new_string)
    answer: str | None = None


def marks_in(text: str, marks: dict[str, str]) -> list[str]:
    return [name for name, mark in marks.items() if mark in text]


def text_of(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(text_of(part) for part in content)
    if isinstance(content, dict):
        return text_of(content.get("text", "")) + text_of(content.get("content", ""))
    return ""


def turns_of(raw: str) -> list[Turn]:
    turns = [Turn()]
    names: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.lstrip().startswith("{"):
            continue
        try:
            event = json.loads(line)
        except ValueError:  # 제한 시간에 끊기면 마지막 줄이 잘린다
            continue
        turn = turns[-1]
        kind = event.get("type")
        message = event.get("message")
        content = message.get("content", []) if isinstance(message, dict) else []
        if kind == "assistant":
            for block in content if isinstance(content, list) else []:
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                if event.get("parent_tool_use_id"):
                    turn.sub_tools += 1
                    continue
                names[block.get("id", "")] = block.get("name", "")
                turn.tools.append(block.get("name", ""))
                if block.get("name") == "Edit":
                    given = block.get("input", {})
                    turn.edits.append(
                        (str(given.get("file_path", "")), str(given.get("new_string", "")))
                    )
        elif kind == "user" and not event.get("parent_tool_use_id"):
            for block in content if isinstance(content, list) else [content]:
                text = text_of(block)
                if "Base directory for this skill:" in text:
                    head = text.split("Base directory for this skill:", 1)[1].strip()
                    turn.skill_dirs.append(head.splitlines()[0] if head else "")
                    turn.skill_marks += marks_in(text, SKILL_MARKS)
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    name = names.get(block.get("tool_use_id", ""), "")
                    if name == "Agent":
                        turn.agent_answered = True
                        turn.agent_marks += marks_in(text, AGENT_MARKS)
                    if name == "EnterWorktree":
                        turn.worktree_error = bool(block.get("is_error"))
                    if name == "Edit" and block.get("is_error"):
                        turn.edit_errors += 1
        elif kind == "result":
            ok = event.get("subtype") == "success" and not event.get("is_error")
            turn.answer = event.get("result") if ok else None
            turns.append(Turn())
    return turns[:-1]


def measured(turn: Turn, first: bool) -> bool:
    """측정 턴인지. 바뀌지 않은 스킬을 다시 부르면 본문을 다시 싣지 않아(`Launching skill` 만
    온다) 기준 폴더 줄은 첫 턴에만 요구하고, 뒤 턴은 Skill 을 불렀는지만 본다."""
    if first and (turn.worktree_error is not False or not turn.skill_dirs):
        return False
    if "Read" in turn.tools or "Edit" in turn.tools or turn.sub_tools:
        return False
    return "Skill" in turn.tools and turn.agent_answered and turn.answer is not None


def edited(turn: Turn) -> bool:
    """편집 턴에서 편집이 실제로 났는지. Edit 결과에 오류가 없고, 워크트리 사본 둘마다 그 파일을
    겨눈 Edit 가 새 표지를 썼다."""
    targets = {
        "inner/.claude/skills/probe-skill/SKILL.md": SKILL_MARKS["안새판"],
        "inner/.claude/agents/probe-agent.md": AGENT_MARKS["안새판"],
    }
    hit = {
        suffix
        for path, new in turn.edits
        for suffix, mark in targets.items()
        if path.replace("\\", "/").endswith(suffix) and mark in new
    }
    return turn.edit_errors == 0 and hit == set(targets)


def main(out: Path) -> int:
    temp = Path(tempfile.gettempdir())
    stray = ancestors_with_claude_dir(temp / "x")
    if stray:
        print("임시 디렉터리의 상위 폴더에 .claude/ 가 있어 섞인다:", *stray, sep="\n  ")
        return 2
    out.mkdir(parents=True, exist_ok=True)
    roots = {branch: Path(tempfile.mkdtemp(prefix="enter-worktree-")) for branch in BRANCHES}
    try:
        places = {branch: layout(roots[branch]) for branch in BRANCHES}
        with ThreadPoolExecutor(max_workers=len(BRANCHES)) as pool:
            raws = list(pool.map(lambda branch: drive(branch, *places[branch]), BRANCHES))
    finally:
        for root in roots.values():
            try:
                remove_tree(root)
            except OSError as error:
                print(f"임시 디렉터리를 다 지우지 못했다: {root} ({error})")
    for branch, raw in zip(BRANCHES, raws, strict=True):
        (out / f"{branch}.jsonl").write_text(raw, encoding="utf-8", newline="\n")
    invalid = 0
    for branch, raw in zip(BRANCHES, raws, strict=True):
        turns = turns_of(raw)
        expected = 3 if branch == "안편집" else 2
        if len(turns) < expected:
            invalid += 1
            print(f"[무효] {branch} 턴 {len(turns)}개만 끝났다(기대 {expected})")
        for index, turn in enumerate(turns):
            if branch == "안편집" and index == 1:
                done = edited(turn)
                invalid += not done
                print(
                    f"[{'편집' if done else '무효'}] {branch}-{index + 1} 도구 {turn.tools} "
                    f"Edit 오류 {turn.edit_errors}"
                )
                continue
            valid = measured(turn, first=index == 0)
            invalid += not valid
            dirs = ["주" if "worktrees" not in d else "안" for d in turn.skill_dirs]
            dirs += ["다시 싣지 않음"] * (turn.tools.count("Skill") - len(turn.skill_dirs))
            print(
                f"[{'측정' if valid else '무효'}] {branch}-{index + 1} 도구 {turn.tools} "
                f"서브 도구 {turn.sub_tools} · 스킬 기준 폴더 {dirs} 표지 {turn.skill_marks} · "
                f"정의 표지 {turn.agent_marks}"
            )
            print("  답:", " ".join((turn.answer or "결과 없음").split()))
    return 1 if invalid else 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1])))
