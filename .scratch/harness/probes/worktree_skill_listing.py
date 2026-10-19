"""주 체크아웃 안의 워크트리(`.claude/worktrees/<이름>/`)에 든 프로젝트 스킬 사본이 언제 세션의 스킬
목록에 경로를 단 이름으로 섞이는지, 막는 설정이 있는지 잰다.

대기열 274 다. 2026-10-16 의 측정(일지 2026-10-16-01)은 72시간에 이 저장소의 세션 70개가 목록에
`.claude/worktrees/<이름>:<스킬>` 꼴의 이름을 실었다고 셌고(스크래치 스크립트), 기전을 몰라 이
프로브부터 두었다. 이 저장소의 모양을 임시 디렉터리에 흉내 낸다. 주 체크아웃 `outer` 에 스킬
`probe-skill` 과 `other-skill` 을 두고, `.gitignore` 에 든 워크트리 `outer/.claude/worktrees/inner`
를 꺼낸다. 워크트리는 커밋에서 꺼내므로 같은 스킬의 사본을 든다. 바깥에서 고치는 것은 `probe-skill`
하나이고, `other-skill` 은 바뀌지 않은 스킬도 함께 섞이는지 보려고 둔다. 견줄 폴더 둘을 더 둔다.
추적되는 보통 하위 폴더 `outer/pkg`(스킬 `pkg-skill`)와 `.gitignore` 에 든 보통 폴더
`outer/ignored`(스킬 `ignored-skill`, 커밋하지 않는다)다. 폴더마다 읽을 파일 `notes.txt` 가 있다.

갈래마다 임시 디렉터리를 새로 짓고 `claude -p` 를 한 턴 띄운다. 질문은 차례로 칠 도구 호출을 적고
다른 것은 하지 말라고 한다.
- `대조`: 주 체크아웃에서 `outer/notes.txt` 를 Read 한다.
- `하위읽기`: `outer/pkg/notes.txt` 를 Read 한다. 하위 폴더의 스킬을 읽기로 찾는 길이 있는지 보는
  양성 대조다. 이 갈래에서 `pkg-skill` 이 실리지 않으면 아래 읽기 갈래의 "섞이지 않았다"는 읽기로
  찾는 길이 없다는 뜻이라, 워크트리라서 빠졌다는 해석을 세우지 못한다.
- `무시읽기`: `outer/ignored/notes.txt` 를 Read 한다. 워크트리 갈래와 견주어 `.gitignore` 때문인지
  워크트리(`.git` 파일)라서인지 가른다.
- `워크트리읽기`: `outer/.claude/worktrees/inner/notes.txt` 를 Read 한다.
- `주스킬편집`: 주 체크아웃의 `probe-skill` 을 Edit 로 고치고 `outer/notes.txt` 를 Read 한다. 스킬
  파일이 바뀌어 목록을 다시 지을 때 워크트리 사본이 섞이는지 본다. 다른 세션이 주 체크아웃을 당긴
  것의 흉내다.
- `진입읽기`: `EnterWorktree(path)` 로 워크트리에 들어가 `inner/notes.txt` 를 Read 한다.
- `주바깥변경`: 세션이 Bash 로 `sleep` 을 치는 동안 프로브가 주 체크아웃의 `probe-skill` 을 바깥에서
  고치고, 세션은 그 뒤 `outer/notes.txt` 를 Read 한다. 다른 세션이 주 체크아웃을 당긴 것의 흉내다.
- `진입후바깥주변경`: 워크트리에 들어간 뒤 `주바깥변경` 과 같이 하고 `inner/notes.txt` 를 Read 한다.
  `enter_worktree_loading.py` 의 `주변경` 갈래와 같은 꼴이다. 처음에는 세션이 Edit 로 주 체크아웃을
  고치게 지었는데, 워크트리에 들어간 세션의 그 Edit 를 claude 2.1.303 이 "This session is isolated
  in the worktree <경로>. Edit the worktree copy of this file instead of the shared-checkout path."
  오류로 거부해(커밋하지 않은 첫 실행의 기록) 바깥에서 고치게 바꿨다.
- `워크트리읽기+무시안함`: `워크트리읽기` 와 같되 `.gitignore` 에 `/.claude/worktrees/` 를 두지
  않는다. `무시읽기` 와 견주어, 읽기로 섞이지 않은 것이 `.gitignore` 때문인지 워크트리(`.git`
  파일)라서인지 가른다.
- `워크트리시작`: 워크트리에서 세션을 시작해 `inner/notes.txt` 를 Read 한다. 앱이 워크트리에서 바로
  여는 세션의 흉내다.
- `워크트리시작후바깥주변경`: 워크트리에서 시작한 세션에 `주바깥변경` 과 같이 하고 `inner/notes.txt`
  를 Read 한다. 주 체크아웃에서 시작해 들어가는 대신 워크트리에서 바로 시작하면 섞이지 않는지 본다.
이름에 `+` 가 든 갈래는 앞 갈래와 같은 꼴에 주 체크아웃의 `.claude/settings.json` 을 둔 것이다
(`SETTINGS`). 후보는 `skillOverrides` 다. 공식 문서(skills, "Override skill visibility from
settings", 2026-10-19 원문을 내려받아 읽었다)는 키가 스킬 이름이고 값이 넷(`on`, `name-only`,
`user-invocable-only`, `off`)이며, 사용자·프로젝트·로컬 설정에서는 스킬 이름으로만 맞춘다고 적는다.
경로를 단 이름이 그 키로 맞는지와 별표가 통하는지는 적지 않아 갈래로 잰다. `도중로컬` 갈래는 세션이
이미 돌 때(Bash 호출이 찍힌 뒤) 주 체크아웃의 `.claude/settings.local.json` 에 키를 쓰고
`MIDWAY_WAIT` 초 뒤에 스킬을 고친다(`MIDWAY`). 훅이 `EnterWorktree` 뒤에 이름을 적는 처방이 서는지
보는 갈래다. 설정 갈래는 사본 둘 가운데 `probe-skill` 의 것만 끈다. 그래서 `other-skill` 의 사본이
추가분에 실리면 목록을 다시 지은 것이 보이고, 그 자리에 `probe-skill` 의 사본이 없으면 키가 먹은
것이다. `대조+프로젝트끔` 과 `대조+프로젝트끔로컬다른키` 는 시작 전에 프로젝트 설정으로
`other-skill` 을 끄고, 뒤의 것만 local 설정에 다른 키의 `skillOverrides` 를 둔다(`MERGE`). 뒤의 것의
첫 목록에도 `other-skill` 이 없으면 두 파일의 `skillOverrides` 가 합쳐진 것이고, 있으면 local 이
덮은 것이다. 앞의 것은 프로젝트 설정의 키가 먹는다는 양성 대조다. `진입후바깥주변경+훅` 은 흉내가
아니라 실제 훅 `tools/hook_worktree_skill_overrides.py` 를 주 체크아웃의 `.claude/settings.json` 에
PostToolUse `EnterWorktree` 로 등록하고, 그 세션의 환경에서 `CLAUDE_CODE_REMOTE` 를 벗긴다(훅이
클라우드 세션에서는 침묵한다). 바깥에서 주 체크아웃의 스킬을 고칠 때 워크트리에 새 스킬
`late-skill` 도 함께 만든다. 훅이 적기 전에 없던 스킬이라 꺼지지 않으므로, 그것이 추가분에 실리면
목록을 다시 지은 것이 보인다. 이 갈래는 끝난 뒤 주 체크아웃의 `.claude/settings.local.json` 에 훅이
적은 키가 있어야 측정이다.

판정은 세션 기록(`<설정 폴더>/projects/*/<세션 ID>.jsonl`)에서 한다. 스킬 목록은 `attachment` 의
`skill_listing` 첨부이고 `isInitial` 이 참이면 첫 목록, 거짓이면 추가분이다. 첨부의 `names` 에서
이름에 `WATCHED` 의 낱말이 든 것을 첨부마다 차례로 찍는다. 기대를 단언하지
않고 본 것을 찍는다. 갈래가 측정이 되려면 기록이 있고 첫 목록이 있으며, 질문이 시킨 도구 호출이 모두
그 대상(입력의 경로)으로 나고 그 결과가 오류가 아니어야 한다. Edit 갈래는 끝난 뒤 디스크의 주
체크아웃 스킬에 새 표지가 있어야 하고, 바깥에서 고치는 갈래는 세션의 Bash 호출이 원본에 찍힌 뒤에
고쳤어야 한다. 하나라도 어긋나면 그 갈래는 측정이 아니라고 찍는다. 이
클라우드 컨테이너에서는 자식 `claude -p` 가 부모의 세션 ID 를 물려받아 기록이 한 파일에
섞였다(2026-10-19 손으로 봤다). 그래서 갈래마다 `--session-id` 를 새로 준다.

못 보는 것: 데스크톱 앱의 세션은 재지 않는다(이 프로브는 `claude` CLI 다). Read 밖의 도구(Grep,
Glob, Bash)가 워크트리 파일에 닿는 길, 실제 `git pull`(프로브는 스킬 파일 하나를 바로 쓴다), 압축과
이어 하기 뒤의 목록은 재지 않는다. 갈래마다 한 회차다. 기록에 남은 첨부만 보므로, 모델에게 갔지만
기록에 남지 않은 목록이 있다면 놓친다.

돌리는 법:
`uv run python .scratch/harness/probes/worktree_skill_listing.py <출력 디렉터리> [갈래 ...]`. 갈래를
주지 않으면 모두 돈다. `claude` CLI 와 인증이 든다. 갈래마다 sonnet 세션 하나이고 넷씩 함께 띄운다.
임시 디렉터리의 상위 폴더(홈 폴더는 빼고)에 `.claude/` 가 있으면 섞이므로 돌리지 않고 2 로 끝난다.
갈래마다 stream-json 원본(`<갈래>.jsonl`)과 세션 기록 사본(`<갈래>.transcript.jsonl`)을 출력
디렉터리에 남기고 임시 디렉터리는 끝에 지운다. 종료 코드: 0 모든 갈래가 측정이다, 1 측정이 아닌
갈래가 있다, 2 출력 디렉터리를 주지 않았거나(이 독스트링을 찍는다) 상위 폴더에 `.claude/` 가
있거나 `claude` 를 찾지 못했거나 모르는 갈래를 주었다.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

WATCHED = ("probe-skill", "other-skill", "pkg-skill", "ignored-skill", "late-skill")
ROOT = Path(__file__).resolve().parents[3]
HOOK = ROOT / "tools" / "hook_worktree_skill_overrides.py"
OLD_MARK = "노을고래"
NEW_MARK = "한낮여우"
TIMEOUT = 300
POLL = 0.5
SLEEP = 20
PARALLEL = 4
FLAGS = [
    "-p",
    "--setting-sources",
    "project,local",
    "--strict-mcp-config",
    "--model",
    "sonnet",
    "--permission-mode",
    "bypassPermissions",
    "--output-format",
    "stream-json",
    "--verbose",
    "--tools",
    # 스킬 목록 첨부는 Skill 도구가 있을 때만 실렸다(Skill 을 뺀 첫 실행의 기록에 첨부가 없었다)
    "Read,Edit,EnterWorktree,Skill,Bash",
]
# 갈래 이름 → 주 체크아웃의 `.claude/settings.json`. 막는 설정의 후보다.
SETTINGS: dict[str, dict[str, object]] = {
    "진입후바깥주변경+정확한이름끔": {
        "skillOverrides": {".claude/worktrees/inner:probe-skill": "off"},
    },
    "진입후바깥주변경+별표이름끔": {
        "skillOverrides": {".claude/worktrees/*:probe-skill": "off"},
    },
}
# 갈래 이름 → 세션 도중에 쓰는 주 체크아웃의 `.claude/settings.local.json`. 훅이 `EnterWorktree`
# 뒤에 이름을 적는 처방의 흉내라, Bash 호출을 본 뒤 이 파일을 쓰고 `MIDWAY_WAIT` 초 뒤에 스킬을
# 고친다.
MIDWAY: dict[str, dict[str, object]] = {
    "진입후바깥주변경+도중로컬이름끔": {
        "skillOverrides": {".claude/worktrees/inner:probe-skill": "off"},
    },
}
MIDWAY_WAIT = 3
# 갈래 이름 → 시작 전에 쓰는 (`.claude/settings.json`, `.claude/settings.local.json`). 두 파일의
# `skillOverrides` 가 합쳐지는지, local 의 객체가 프로젝트의 것을 통째로 덮는지 가른다. 이 저장소의
# 프로젝트 설정에는 이미 `skillOverrides` 가 있어, local 에 그 키를 쓰는 처방이 그것을 지우면 안
# 된다.
MERGE: dict[str, tuple[dict[str, object], dict[str, object] | None]] = {
    "대조+프로젝트끔": ({"skillOverrides": {"other-skill": "off"}}, None),
    "대조+프로젝트끔로컬다른키": (
        {"skillOverrides": {"other-skill": "off"}},
        {"skillOverrides": {".claude/worktrees/inner:probe-skill": "off"}},
    ),
}


@dataclass(frozen=True)
class Layout:
    outer: Path
    inner: Path

    @property
    def skill(self) -> Path:
        return self.outer / ".claude" / "skills" / "probe-skill" / "SKILL.md"


@dataclass(frozen=True)
class Step:
    """질문이 시킬 도구 호출 하나. `target` 은 입력의 경로(`file_path` 나 `path`)이고 Bash 는
    없다."""

    tool: str
    target: Path | None


@dataclass(frozen=True)
class Arm:
    name: str
    steps: Callable[[Layout], list[Step]]
    start_in_inner: bool = False
    external_change: bool = False
    settings: dict[str, object] | None = None
    midway_local: dict[str, object] | None = None
    local: dict[str, object] | None = None
    worktrees_ignored: bool = True
    hook: bool = False


def _read(path: Callable[[Layout], Path]) -> Callable[[Layout], list[Step]]:
    return lambda lay: [Step("Read", path(lay))]


def _edit_main_then_read(path: Callable[[Layout], Path]) -> Callable[[Layout], list[Step]]:
    return lambda lay: [Step("Read", lay.skill), Step("Edit", lay.skill), Step("Read", path(lay))]


def _sleep_then_read(path: Callable[[Layout], Path]) -> Callable[[Layout], list[Step]]:
    return lambda lay: [Step("Bash", None), Step("Read", path(lay))]


def _enter_then(rest: Callable[[Layout], list[Step]]) -> Callable[[Layout], list[Step]]:
    return lambda lay: [Step("EnterWorktree", lay.inner), *rest(lay)]


def _outer_notes(lay: Layout) -> Path:
    return lay.outer / "notes.txt"


def _inner_notes(lay: Layout) -> Path:
    return lay.inner / "notes.txt"


ARMS: dict[str, Arm] = {
    arm.name: arm
    for arm in (
        Arm("대조", _read(_outer_notes)),
        Arm("하위읽기", _read(lambda lay: lay.outer / "pkg" / "notes.txt")),
        Arm("무시읽기", _read(lambda lay: lay.outer / "ignored" / "notes.txt")),
        Arm("워크트리읽기", _read(_inner_notes)),
        Arm("주스킬편집", _edit_main_then_read(_outer_notes)),
        Arm("진입읽기", _enter_then(_read(_inner_notes))),
        Arm("주바깥변경", _sleep_then_read(_outer_notes), external_change=True),
        Arm("진입후바깥주변경", _enter_then(_sleep_then_read(_inner_notes)), external_change=True),
        Arm(
            "워크트리시작후바깥주변경",
            _sleep_then_read(_inner_notes),
            start_in_inner=True,
            external_change=True,
        ),
        Arm("워크트리시작", _read(_inner_notes), start_in_inner=True),
    )
}
for _name, _settings in SETTINGS.items():
    _base = ARMS[_name.split("+")[0]]
    ARMS[_name] = Arm(
        _name,
        _base.steps,
        start_in_inner=_base.start_in_inner,
        external_change=_base.external_change,
        settings=_settings,
    )
for _name, _local in MIDWAY.items():
    _base = ARMS[_name.split("+")[0]]
    ARMS[_name] = Arm(
        _name,
        _base.steps,
        start_in_inner=_base.start_in_inner,
        external_change=_base.external_change,
        midway_local=_local,
    )
for _name, (_project, _start_local) in MERGE.items():
    _base = ARMS[_name.split("+")[0]]
    ARMS[_name] = Arm(
        _name,
        _base.steps,
        start_in_inner=_base.start_in_inner,
        external_change=_base.external_change,
        settings=_project,
        local=_start_local,
    )
ARMS["워크트리읽기+무시안함"] = Arm(
    "워크트리읽기+무시안함", _read(_inner_notes), worktrees_ignored=False
)
_HOOK_COMMAND = f'uv run --project "{ROOT}" --no-sync python "{HOOK}"'
ARMS["진입후바깥주변경+훅"] = Arm(
    "진입후바깥주변경+훅",
    _enter_then(_sleep_then_read(_inner_notes)),
    external_change=True,
    settings={
        "hooks": {
            "PostToolUse": [
                {
                    "matcher": "EnterWorktree",
                    "hooks": [{"type": "command", "command": _HOOK_COMMAND, "timeout": 60}],
                }
            ]
        }
    },
    hook=True,
)


def prompt_of(steps: list[Step]) -> str:
    lines = ["아래 도구 호출을 차례로 하나씩 한다. 다른 도구는 부르지 않고 다른 일은 하지 않는다."]
    for i, step in enumerate(steps, 1):
        if step.tool == "Read":
            lines.append(f"{i}) Read 로 {step.target} 를 읽는다.")
        elif step.tool == "Edit":
            lines.append(
                f"{i}) Edit 로 {step.target} 의 {OLD_MARK} 를 {NEW_MARK} 로 바꾼다"
                "(앞에서 읽은 파일이다)."
            )
        elif step.tool == "Bash":
            lines.append(f"{i}) Bash 로 sleep {SLEEP} 을 친다.")
        else:
            lines.append(f"{i}) EnterWorktree 를 path 인자 {step.target} 로 부른다.")
    lines.append("모두 마치면 '끝' 한 낱말만 답한다.")
    return "\n".join(lines)


def clean_env() -> dict[str, str]:
    """이 저장소를 가리키는 `GIT_*` 를 벗긴다. 남으면 임시 디렉터리의 git 이 이 저장소에 닿는다."""
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


def git(*args: str, cwd: Path) -> None:
    done = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False, env=clean_env()
    )
    if done.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} 실패({done.returncode}): {done.stderr.strip()}")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_skill(folder: Path, name: str, mark: str) -> None:
    write(
        folder / ".claude" / "skills" / name / "SKILL.md",
        f"---\nname: {name}\ndescription: 프로브용 스킬. 부르라고 하면 부른다.\n---\n\n"
        f"이 스킬의 표지 낱말은 {mark}다.\n",
    )


def layout(root: Path, arm: Arm) -> Layout:
    outer = root / "outer"
    outer.mkdir()
    git("init", "-q", "-b", "main", cwd=outer)
    worktrees = "/.claude/worktrees/\n" if arm.worktrees_ignored else ""
    write(outer / ".gitignore", f"{worktrees}/ignored/\n")
    write_skill(outer, "probe-skill", OLD_MARK)
    write_skill(outer, "other-skill", "들꽃사슴")
    write_skill(outer / "pkg", "pkg-skill", "솔바람")
    for folder in (outer, outer / "pkg"):
        write(folder / "notes.txt", "프로브가 읽게 하는 파일이다.\n")
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
    ignored = outer / "ignored"
    write_skill(ignored, "ignored-skill", "물안개")
    write(ignored / "notes.txt", "프로브가 읽게 하는 파일이다.\n")
    if arm.settings is not None:
        write(outer / ".claude" / "settings.json", json.dumps(arm.settings, ensure_ascii=False))
    if arm.local is not None:
        write(outer / ".claude" / "settings.local.json", json.dumps(arm.local, ensure_ascii=False))
    return Layout(outer, inner)


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


def config_dir() -> Path:
    configured = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(configured) if configured else Path.home() / ".claude"


def records(path: Path) -> list[dict[str, object]]:
    """JSON 줄의 객체. 풀지 못한 줄(끊긴 마지막 줄)은 건너뛴다."""
    out: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            value: object = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            out.append({str(k): v for k, v in value.items()})
    return out


def blocks(record: dict[str, object]) -> list[dict[str, object]]:
    message = record.get("message")
    if not isinstance(message, dict):
        return []
    content = message.get("content")
    if not isinstance(content, list):
        return []
    return [{str(k): v for k, v in b.items()} for b in content if isinstance(b, dict)]


def listings(transcript: list[dict[str, object]]) -> list[tuple[bool, list[str]]]:
    """스킬 목록 첨부마다 (첫 목록인가, 지켜보는 이름)."""
    out: list[tuple[bool, list[str]]] = []
    for record in transcript:
        attachment = record.get("attachment")
        if record.get("type") != "attachment" or not isinstance(attachment, dict):
            continue
        if attachment.get("type") != "skill_listing":
            continue
        names = attachment.get("names")
        found = [
            str(n)
            for n in (names if isinstance(names, list) else [])
            if any(w in str(n) for w in WATCHED)
        ]
        out.append((attachment.get("isInitial") is True, found))
    return out


def problems_of(transcript: list[dict[str, object]], steps: list[Step]) -> list[str]:
    """측정이 아닌 까닭. 비었으면 측정이다."""
    if not transcript:
        return ["세션 기록이 없다"]
    if not any(first for first, _ in listings(transcript)):
        return ["첫 스킬 목록이 없다"]
    calls: list[tuple[str, str, str]] = []
    results: dict[str, bool] = {}
    for record in transcript:
        for b in blocks(record):
            if b.get("type") == "tool_use":
                raw = b.get("input")
                given = raw if isinstance(raw, dict) else {}
                target = given.get("file_path") or given.get("path") or ""
                calls.append((str(b.get("id")), str(b.get("name")), str(target)))
            elif b.get("type") == "tool_result":
                results[str(b.get("tool_use_id"))] = b.get("is_error") is True
    problems: list[str] = []
    for step in steps:
        target = step.target
        hit = [
            c
            for c in calls
            if c[1] == step.tool and (target is None or Path(c[2]).resolve() == target.resolve())
        ]
        label = f"{step.tool} {target.name if target is not None else ''}".strip()
        if not hit:
            problems.append(f"{label} 호출이 없다")
        elif all(results.get(c[0], True) for c in hit):
            problems.append(f"{label} 결과가 오류이거나 없다")
    unexpected = [c for c in calls if c[1] not in {s.tool for s in steps}]
    if unexpected:
        problems.append(f"시키지 않은 도구 {sorted({c[1] for c in unexpected})}")
    return problems


def bash_started(raw: Path) -> bool:
    """stream-json 원본에 Bash 의 tool_use 가 찍혔는가."""
    return any(
        b.get("type") == "tool_use" and b.get("name") == "Bash"
        for record in records(raw)
        if record.get("type") == "assistant"
        for b in blocks(record)
    )


def drive(
    arm: Arm, lay: Layout, cwd: Path, raw: Path, claude: str, session: str, prompt: str
) -> bool | None:
    """`claude -p` 한 턴을 띄우고 끝을 기다린다. 바깥에서 고치는 갈래는 원본에 Bash 호출이 찍히면
    주 체크아웃의 스킬을 고친다. 고쳤는지를 돌려주고, 시간 안에 끝나지 않으면 None 이다. 출력은
    파이프가 아니라 파일로 받아, 손자 프로세스가 쥐어도 기다림이 막히지 않는다."""
    changed = False
    deadline = time.monotonic() + TIMEOUT
    env = clean_env()
    if arm.hook:
        env.pop("CLAUDE_CODE_REMOTE", None)
    with raw.open("w", encoding="utf-8") as sink:
        process = subprocess.Popen(
            [claude, "--session-id", session, *FLAGS],
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=sink,
            stderr=subprocess.STDOUT,
            env=env,
        )
        if process.stdin is not None:
            process.stdin.write(prompt.encode("utf-8"))
            process.stdin.close()
        while process.poll() is None:
            if time.monotonic() > deadline:
                process.kill()
                process.wait()
                return None
            if arm.external_change and not changed and bash_started(raw):
                if arm.midway_local is not None:
                    local = lay.outer / ".claude" / "settings.local.json"
                    write(local, json.dumps(arm.midway_local, ensure_ascii=False))
                    time.sleep(MIDWAY_WAIT)
                if arm.hook:
                    write_skill(lay.inner, "late-skill", "늦은별")
                text = lay.skill.read_text(encoding="utf-8")
                write(lay.skill, text.replace(OLD_MARK, NEW_MARK))
                changed = True
            time.sleep(POLL)
    return changed


def hook_wrote(lay: Layout) -> bool:
    """주 체크아웃의 local 설정에 훅이 적는 워크트리 사본의 키가 있는가."""
    local = lay.outer / ".claude" / "settings.local.json"
    if not local.is_file():
        return False
    value: object = json.loads(local.read_text(encoding="utf-8"))
    overrides = value.get("skillOverrides") if isinstance(value, dict) else None
    return isinstance(overrides, dict) and ".claude/worktrees/inner:probe-skill" in overrides


def run_arm(arm: Arm, out_dir: Path, claude: str) -> tuple[str, list[str], str]:
    """갈래 하나를 돌리고 (요약 줄들, 측정이 아닌 까닭, claude 판)을 돌려준다."""
    root = Path(tempfile.mkdtemp(prefix="wsl-"))
    try:
        lay = layout(root, arm)
        steps = arm.steps(lay)
        session = str(uuid.uuid4())
        raw = out_dir / f"{arm.name}.jsonl"
        cwd = lay.inner if arm.start_in_inner else lay.outer
        changed = drive(arm, lay, cwd, raw, claude, session, prompt_of(steps))
        if changed is None:
            return ("", [f"{TIMEOUT}초 안에 끝나지 않았다"], "")
        version = ""
        for record in records(raw):
            if record.get("type") == "system" and record.get("subtype") == "init":
                version = str(record.get("claude_code_version", ""))
        found = sorted((config_dir() / "projects").glob(f"*/{session}.jsonl"))
        transcript: list[dict[str, object]] = []
        if len(found) == 1:
            shutil.copyfile(found[0], out_dir / f"{arm.name}.transcript.jsonl")
            transcript = records(found[0])
        problems = problems_of(transcript, steps)
        if len(found) > 1:
            problems.append(f"세션 기록이 {len(found)}개다")
        if (
            any(s.tool == "Edit" for s in steps) or arm.external_change
        ) and NEW_MARK not in lay.skill.read_text(encoding="utf-8"):
            problems.append("주 체크아웃 스킬에 새 표지가 없다")
        if arm.external_change and not changed:
            problems.append("세션의 Bash 호출을 보기 전에 끝나 바깥에서 고치지 못했다")
        if arm.hook and not hook_wrote(lay):
            problems.append("훅이 local 설정에 키를 적지 않았다")
        lines = [
            f"  {'첫 목록' if first else '추가분'}: {', '.join(names) or '(지켜보는 이름 없음)'}"
            for first, names in listings(transcript)
        ]
        return ("\n".join(lines), problems, version)
    finally:
        remove_tree(root)


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    out_dir = Path(argv[0])
    chosen = argv[1:] or list(ARMS)
    unknown = [name for name in chosen if name not in ARMS]
    if unknown:
        print(f"모르는 갈래: {', '.join(unknown)}. 갈래는 {', '.join(ARMS)}", file=sys.stderr)
        return 2
    claude = shutil.which("claude")
    if claude is None:
        print("claude 를 찾지 못했다", file=sys.stderr)
        return 2
    mixed = ancestors_with_claude_dir(Path(tempfile.gettempdir()) / "x")
    if mixed:
        print(f"임시 디렉터리의 상위 폴더에 .claude/ 가 있다: {mixed}", file=sys.stderr)
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        futures = {name: pool.submit(run_arm, ARMS[name], out_dir, claude) for name in chosen}
    invalid = 0
    for name, future in futures.items():
        summary, problems, version = future.result()
        verdict = "측정" if not problems else "측정 아님: " + "; ".join(problems)
        print(f"[{name}] claude {version or '?'} · {verdict}")
        if summary:
            print(summary)
        invalid += bool(problems)
    print(f"갈래 {len(chosen)} · 측정 아님 {invalid}. 원본은 {out_dir}")
    return 1 if invalid else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
