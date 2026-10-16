"""PostToolUse 훅(Write|Edit). 일지를 단계를 닫는 모양으로 갱신하면 retro 계기를, 새 일지 파일의
순번이 다음 빈 번호와 다르면 그 번호를 컨텍스트에 넣는다.

계기는 retro 스킬 설명("일지의 '다음' 절을 갱신하며 단계를 닫을 때")에 지침으로 있었는데
2026-09-21 세션에서 에이전트가 일지를 쓰고도 돌리지 않았다. 지침이 어겨졌으니 훅이다(CLAUDE.md
교정 루프). stdin 으로 훅 JSON 을 받고, 경로가 docs/journal/*.md 이면 additionalContext 를 낸다.

발동 조건은 넷이다. 쓴 본문 — Write 의 `content` 나 Edit 의 `new_string` — 이 줄 머리의 `## 다음`
제목을 담고, 그 절(다음 `#`·`##` 제목 전까지)에 자리 표시가 아닌 줄이 있고, Edit 이면 그 절이
`old_string` 의 절과 다르고, 쓰기 뒤의 일지 파일에 자리 표시가 아닌 `## 회고` 절이 아직 없을 때.
대기열 28(사용자 승인 2026-09-24)은 Write 를 무조건 계기로 두었는데, 세션 첫머리에 일지를 새로 쓰는
Write 는 단계를 닫는 것이 아니라 좁혔다(PR #91 리뷰). 경로만 보던 동안 인용 하나를 고친 Edit 마다
계기가 울렸다(대기열 28 의 5회차와 일지 2026-09-27-01·02 의 둘). 세션이 그것을 무시하는 법을
배우고, 무시하는 습관은 진짜 계기도 무시하게 만든다. 뒤의 세 조건도 같은 이유다. 부분 문자열로 보던
동안 일지 산문의 코드 스팬 `` `## 다음` `` 에 울렸다(대기열 74). 괄호 한 줄짜리 자리 표시로 절을
먼저 두자 울렸고, 회고를 그 절 앞에 적어 넣는 Edit — 절은 old_string 과 new_string 에 그대로 있다 —
에 다시 울렸다(대기열 62). retro 를 먼저 돌고 "다음" 을 적은 편집에도 울렸다(일지 2026-09-30-02,
2026-10-01-03). 회고 절은 retro 가 돈 흔적이라, 그것이 있으면 단계는 이미 닫혔다(사용자 결정
2026-10-01, 일지 2026-10-01-04).
못 보는 것: `## 다음` 제목 아래 불릿만 고친 Edit(제목이 new_string 에 없다). 그것은 절을 새로 쓴
것이 아니라 손본 것이라 계기가 아니다. 괄호 한 쌍으로 감싼 한 줄 밖의 자리 표시("TBD", "…", 번호
목록, 두 줄에 걸친 괄호, 괄호 안의 괄호)는 내용으로 본다. 펜스 코드 블록을 가리지 않는다 — 펜스 안의
`## 다음` 줄은 제목으로, 절 안 펜스의 `#`·`##` 줄은 절의 끝으로 본다. 기존 절을 그대로 둔 채 파일
전체를 다시 쓴 Write 에는 울린다(Write 의 입력에는 앞 내용이 없다). retro 를 돌았어도 회고 절을
적기 전에 "다음" 을 쓰면 울린다. 한 일지에 두 단계를 닫으면 둘째에는 울리지 않는다(첫 회고 절이
있다). 일지 파일을 읽지 못하면 회고 절이 없는 것으로 본다.

순번 대조(대기열 232). 일지 파일을 `docs/journal/` 의 마지막 번호를 보고 고른 번호로 만들었다가,
커밋 직전 `tools/sibling_overlap.py` 가 형제와의 겹침을 알려 번호와 그 번호를 든 인용을 옮겼다(일지
2026-10-13-33·2026-10-13-54). 번호를 그 도구에서 먼저 받으라는 문장은 `next-session` 1단계와 그
도구의 출력에만 있어, 구현 중에 일지를 만드는 때에는 읽히지 않았다. 그래서 새 일지를 만든 Write 에
그 도구를 자식으로 돌려 대 본다. 새 파일인지는 Write 결과의 `type` 이 `create` 인지로
가른다(덮어쓰면 `update`, Edit 의 결과에는 그 값이 없다. 2026-10-16 claude 2.1.300,
`.scratch/harness/probes/journal_number_hook/run.py` 의 A). 도구는 이 훅과 같은 `tools/` 의 것을
일지가 든 폴더를 인자로 주어 돌린다. 훅이 읽는 출력의 꼴과 도구가 내는 꼴이 한 체크아웃의 것이어야
갈리지 않는다. 만든 파일은 도구가 이 브랜치의 새 일지로 세므로, 맞는 순번이면 출력의 `이 브랜치의
새 번호` 줄에 그 순번이 있고 다음 빈 번호가 그 바로 다음이다. 그렇지 않으면 알린다. 만든 순번이
출력의 옮길 번호에 들었으면(형제와 겹쳤거나 main 의 최신 일지보다 이름순으로 앞이다) 도구가 고른 새
번호와 `--move` 를, 아니면 다음 빈 번호를 든다. 뒤의 갈래는 셋이다. 날짜가 다르거나, 둘 이상
앞이거나, 새 번호 줄에 없다. 마지막은 merge-base 나 main 의 일지가 이미 쓴 순번이다. 도구는 그것을
새로 매긴 번호로 세지 않아 겹침으로도 알리지 않고, 다음 빈 번호가 마침 그 바로 다음일 수 있다(실제
도구로 돈 테스트가 첫 판에서 잡았다). 도구를 띄우지 못했거나, 시간을 넘겼거나, 2로 끝났거나,
출력에서 두 줄을 읽지 못하면 대 보지 못했다고 알리고 칠 명령과 손으로 대 볼 세 줄을 준다. 침묵하면
훅이 없던 때와 같다. 옮기라고 알릴 때는 옛 파일의 이름을 바꾸라고 함께 안내한다. Write 로 새 이름을
만들고 옛 파일을 남기면 옛 파일이 그 번호를 쥐어 이 계기가 다음 번호를 다시 알렸다(셀프 리뷰 명세
축이 손으로 봤다). 도구는 이 PC 의 이 워크트리에서 한 번에 9~11초가 걸렸다(2026-10-16, 형제
워크트리가 스물 남짓일 때 `time` 으로 세 번 손으로 쟀다). 그래서 자식의 시간 제한은 40초이고 등록의
제한은 45초다. 자식의 출력은 파이프가 아니라 임시 파일로 받는다. 도구가 띄운 fetch 의 손자
프로세스가 파이프를 쥐면 시간 제한에서 끊기지 않는다(`.claude/rules/tools.md`).
못 보는 것(순번 대조): 빈 사이를 건너뛴 큰 순번(만든 파일이 그 날짜의 가장 큰 순번이면 그 앞이
비었는지 출력으로 가를 수 없다), 이 브랜치가 같은 순번의 새 일지를 둘 만든 것(도구가 순번을 열쇠로
읽어 둘이 하나로 접힌다. 같은 날의 순번 겹침은 `tests/test_journal_names.py` 가 커밋 전에 본다),
Write 가 아닌 길로 만든 일지(Bash 의 `cat >`·`mv`·`git mv`, PowerShell), 이미 있는 경로를 덮어쓴
Write(`update`), 대조 뒤에 다른 세션이 같은 번호를 쓰는 것(커밋 직전의 대조가 잡는다), 계기를 읽기
전에 컨텍스트가 압축되어 알림이 사라진 것, 도구 자신의 못 보는 것.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path, PurePath
from typing import IO, NamedTuple, TypedDict

JOURNAL_PARTS = ("docs", "journal")
# 줄 머리의 제목만. 산문의 코드 스팬 `## 다음` 은 제목이 아니다(대기열 74).
CLOSING_HEADING = re.compile(r"^## 다음[ \t\r]*$", re.MULTILINE)
# `## 회고` 와 `## 회고 (2026-09-21, 슬라이스를 닫은 뒤)` 같은 덧붙인 제목.
RETRO_HEADING = re.compile(r"^## 회고(?:[ \t].*)?\r?$", re.MULTILINE)
# 절은 다음 `#`·`##` 제목에서 끝난다. `###` 는 절 안이다.
SECTION_END = re.compile(r"^#{1,2} ", re.MULTILINE)
# 괄호 한 쌍으로 감싼 한 줄(불릿이어도). "(회고 뒤에 채운다)" 같은 자리 표시다(대기열 62).
# 안에 괄호가 또 있으면 `(web-admin) 04 가 다음이다 (05~08)` 같은 내용일 수 있다.
PLACEHOLDER = re.compile(r"^(?:[-*] +)?[(（][^()（）]*[)）]$")

# 순번 대조(대기열 232). 도구는 이 훅과 같은 체크아웃의 것이다.
SIBLING_OVERLAP = Path(__file__).resolve().parent / "sibling_overlap.py"
OVERLAP_COMMAND = "uv run python tools/sibling_overlap.py"
OVERLAP_TIMEOUT = 40.0
JOURNAL_KEY = re.compile(r"^(\d{4}-\d{2}-\d{2})-(\d{2})-.+\.md$")
# 도구 출력의 두 줄(`tools/sibling_overlap.py` 의 `render`). 꼴이 바뀌면 테스트의 실제 실행이
# 갈린다.
NEXT_LINE = re.compile(r"^다음 빈 번호\(형제 포함\): 일지 (\d{4}-\d{2}-\d{2}-\d{2}),", re.MULTILINE)
MOVES_LINE = re.compile(r"^옮길 번호: (.+)$", re.MULTILINE)
OURS_LINE = re.compile(r"^이 브랜치의 새 번호(?:: (.+)| 없음)$", re.MULTILINE)
OURS_JOURNAL = re.compile(r"일지 (\d{4}-\d{2}-\d{2}-\d{2})")
JOURNAL_MOVE = re.compile(r"일지 (\d{4}-\d{2}-\d{2}-\d{2}) → (\d{4}-\d{2}-\d{2}-\d{2})")
_REPO_LOCATION_VARS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE")


class ToolInput(TypedDict, total=False):
    file_path: str
    content: str
    old_string: str
    new_string: str


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분."""

    tool_name: str
    tool_input: ToolInput
    tool_response: dict[str, object]
    cwd: str


class Overlap(NamedTuple):
    """`tools/sibling_overlap.py` 한 번의 종료 코드와 출력."""

    code: int
    stdout: str
    stderr: str


class JournalNumbers(NamedTuple):
    """도구 출력에서 읽은 일지 순번들(`YYYY-MM-DD-NN`). 다음 빈 번호, 이 브랜치의 새 번호, 옮길
    번호(옛 순번 → 새 순번)다."""

    following: str
    fresh: frozenset[str]
    moves: dict[str, str]


class Unreadable(NamedTuple):
    """도구 출력에서 일지 순번을 읽지 못한 까닭."""

    reason: str


CONTEXT = (
    "docs/journal/ 의 일지를 단계를 닫는 모양으로 갱신했다('다음' 절을 새로 썼다). "
    "retro 스킬의 계기다. 사용자에게 묻지 말고 Skill 도구로 retro 를 지금 돌린다."
)
NUMBER_LEAD = "새 일지 파일의 순번이 `tools/sibling_overlap.py` 의 다음 빈 번호와 다르다."
# 옮길 때의 길. Write 로 새 이름을 만들고 옛 파일을 남기면, 옛 파일이 그 번호를 쥔 채라 이 훅이 그
# 다음 번호를 다시 알린다(셀프 리뷰 명세 축이 손으로 봤다)
RENAME_NOTE = (
    "옮길 때는 옛 파일의 이름을 바꾼다(`mv <옛> <새>`). Write 로 새 이름을 만들고 옛 파일을 남기면"
    " 옛 파일이 그 번호를 쥐어 이 계기가 다음 번호를 다시 알린다."
)


def is_journal(file_path: str) -> bool:
    """docs/journal/<name>.md 인가."""
    path = PurePath(file_path.replace("\\", "/"))
    parts = path.parts
    if path.suffix != ".md" or len(parts) < 3:
        return False
    return tuple(parts[-3:-1]) == JOURNAL_PARTS


def _body_after(text: str, start: int) -> str:
    """`start`(제목 줄 끝)부터 다음 `#`·`##` 제목 전까지. 앞뒤 공백은 벗긴다."""
    rest = text[start:]
    end = SECTION_END.search(rest)
    return (rest[: end.start()] if end else rest).strip()


def section_body(text: str, heading: re.Pattern[str]) -> str | None:
    """`heading` 의 첫 절의 본문. 제목이 없으면 None."""
    found = heading.search(text)
    return None if found is None else _body_after(text, found.end())


def is_written(body: str) -> bool:
    """절에 자리 표시가 아닌 줄이 하나라도 있는가."""
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    return any(not PLACEHOLDER.match(line) for line in lines)


def retro_recorded(journal: str) -> bool:
    """자리 표시가 아닌 회고 절이 하나라도 있는가. 날짜를 붙인 회고 절이 더해질 수 있어 첫 절만
    보지 않는다."""
    return any(
        is_written(_body_after(journal, found.end())) for found in RETRO_HEADING.finditer(journal)
    )


def context_for(
    tool_name: str,
    file_path: str,
    text: str | None,
    previous: str | None = None,
    journal: str | None = None,
) -> str | None:
    """단계를 닫는 일지 갱신이면 컨텍스트 문장, 아니면 None. `text` 는 Write 의 content 나 Edit 의
    new_string, `previous` 는 Edit 의 old_string, `journal` 은 쓰기 뒤의 일지 전체다."""
    if not is_journal(file_path) or tool_name not in ("Write", "Edit") or text is None:
        return None
    closing = section_body(text, CLOSING_HEADING)
    if closing is None or not is_written(closing):
        return None
    if previous is not None and section_body(previous, CLOSING_HEADING) == closing:
        return None
    if journal is not None and retro_recorded(journal):
        return None
    return CONTEXT


def read_journal(file_path: str) -> str | None:
    """쓰기 뒤의 일지 전체. 읽지 못하면 None 이다."""
    try:
        return Path(file_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def created_journal(tool_name: str, file_path: str, response: Mapping[str, object] | None) -> bool:
    """새 일지 파일을 만든 Write 인가. 결과의 `type` 이 `create` 다."""
    return (
        tool_name == "Write"
        and is_journal(file_path)
        and response is not None
        and response.get("type") == "create"
    )


def _environment() -> dict[str, str]:
    """저장소를 가리키는 `GIT_*` 를 벗기고, 자격 증명을 묻느라 멈추지 않게 하고, 출력을 UTF-8 로
    내게 한다. 훅 환경에 `PYTHONUTF8` 이 있다고 가정하지 않는다(`.claude/rules/tools.md`)."""
    environment = {k: v for k, v in os.environ.items() if k not in _REPO_LOCATION_VARS}
    environment["GIT_TERMINAL_PROMPT"] = "0"
    environment["PYTHONIOENCODING"] = "utf-8"
    return environment


def run_overlap(directory: Path) -> Overlap | None:
    """`directory` 가 든 저장소에서 도구를 돌린다. 띄우지 못하거나 시간을 넘기면 None.

    출력은 임시 파일로 받는다. 파이프면 도구가 띄운 fetch 의 손자 프로세스가 쥐어 시간 제한에서
    끊기지 않는다(`.claude/rules/tools.md`)."""
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        code = _launch_overlap(directory, out, err)
        if code is None:
            return None
        out.seek(0)
        err.seek(0)
        # 윈도에서 파일로 받은 print 는 줄 끝이 CRLF 다. 줄 끝 `$` 가 CR 앞에서 멈추지 않는다
        stdout = out.read().decode("utf-8", "replace").replace("\r\n", "\n")
        stderr = err.read().decode("utf-8", "replace").replace("\r\n", "\n")
    return Overlap(code, stdout, stderr)


def _launch_overlap(directory: Path, out: IO[bytes], err: IO[bytes]) -> int | None:
    """도구의 종료 코드. 띄우지 못하거나 `OVERLAP_TIMEOUT` 을 넘기면 None."""
    try:
        result = subprocess.run(
            [sys.executable, str(SIBLING_OVERLAP), str(directory)],
            cwd=directory,
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=err,
            env=_environment(),
            timeout=OVERLAP_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.returncode


def _unchecked(name: str, reason: str) -> str:
    """대 보지 못했을 때의 계기. 손으로 대 볼 때도 세 줄을 함께 본다. 다음 빈 번호만 보면 main 에
    이미 있는 순번에서 그 번호가 마침 바로 다음이라 맞다고 판정한다(셀프 리뷰 두 축)."""
    return (
        f"새 일지 `{name}` 를 만들었는데 그 순번을 `tools/sibling_overlap.py` 의 다음 빈 번호와"
        f" 대 보지 못했다({reason}). `{OVERLAP_COMMAND}` 를 쳐서 셋을 본다. `이 브랜치의 새 번호`"
        " 줄에 이 파일의 순번이 있고, `옮길 번호` 줄에 그 순번이 없고, `다음 빈 번호` 줄의 일지"
        " 순번이 그 바로 다음이면 맞다. 아니면 `옮길 번호`(없으면 `다음 빈 번호`)로 옮긴다"
        f"(대기열 232). {RENAME_NOTE}"
    )


def read_numbers(stdout: str) -> JournalNumbers | Unreadable:
    """도구 출력의 다음 빈 번호·이 브랜치의 새 번호·옮길 번호 줄. 앞의 두 줄 가운데 하나를 읽지
    못하면 그 까닭이다."""
    found = NEXT_LINE.search(stdout)
    if found is None:
        return Unreadable("출력에서 다음 빈 번호를 읽지 못했다")
    ours = OURS_LINE.search(stdout)
    if ours is None:
        return Unreadable("출력에서 이 브랜치의 새 번호를 읽지 못했다")
    moves: dict[str, str] = {}
    for line in MOVES_LINE.findall(stdout):
        moves.update(JOURNAL_MOVE.findall(line))
    fresh = frozenset(OURS_JOURNAL.findall(ours.group(1) or ""))
    return JournalNumbers(found.group(1), fresh, moves)


def _is_next(current: str, numbers: JournalNumbers) -> bool:
    """`current` 가 이 브랜치의 새 번호이고 다음 빈 번호가 같은 날의 바로 다음 순번인가. 새 번호에
    없으면 merge-base 나 main 의 일지가 이미 쓴 순번이다. 도구는 그것을 새 일지로 세지 않아, 다음 빈
    번호가 마침 그 바로 다음일 수 있다."""
    following = numbers.following
    return (
        current in numbers.fresh
        and current[:10] == following[:10]
        and int(current[11:]) + 1 == int(following[11:])
    )


def _misnamed(name: str, following: str) -> str:
    return (
        f"{NUMBER_LEAD} 만든 파일 `{name}` 의 이름이 `YYYY-MM-DD-NN-<슬러그>.md` 꼴이 아니다."
        f" 다음 빈 번호는 {following} 다. 그 번호로 파일 이름과 머리 줄을 바꾼다(대기열 232)."
        f" {RENAME_NOTE}"
    )


def _move_notice(name: str, current: str, target: str) -> str:
    """순번 `current` 로 만든 일지를 `target` 으로 옮기라는 문장."""
    return (
        f"{NUMBER_LEAD} 만든 파일은 `{name}`(순번 {current})이고 옮길 번호는 {target} 다."
        f" 파일 이름의 순번과 머리 줄(`# {target[:10]} ({target[11:]})`)을 {target} 으로"
        " 바꾸고, 이 순번을 든 인용이 있으면 함께 고친다. 번호는 손으로 고르지"
        f" 않는다(대기열 232). {RENAME_NOTE}"
    )


# 도구의 옮길 번호에 든 순번이면 `--move` 가 옮긴다
MOVE_NOTE = (
    " 형제와 겹쳤거나 main 의 최신 일지보다 이름순으로 앞이라, `"
    f"{OVERLAP_COMMAND} --move` 가 이름과 머리 줄, 인용을 함께 옮긴다."
)


def number_context(file_path: str, overlap: Overlap | None) -> str | None:
    """새 일지의 순번이 도구의 다음 빈 번호와 다르면 알릴 문장, 같으면 None. 대 보지 못하면 그
    까닭과 칠 명령이다."""
    name = PurePath(file_path.replace("\\", "/")).name
    if overlap is None:
        return _unchecked(name, f"도구를 띄우지 못했거나 {OVERLAP_TIMEOUT:.0f}초를 넘겼다")
    if overlap.code not in (0, 1):
        first = next((line for line in overlap.stderr.splitlines() if line.strip()), "")
        return _unchecked(name, f"종료 {overlap.code}: {first.strip()}")
    numbers = read_numbers(overlap.stdout)
    if isinstance(numbers, Unreadable):
        return _unchecked(name, numbers.reason)
    key = JOURNAL_KEY.match(name)
    if key is None:
        return _misnamed(name, numbers.following)
    current = f"{key.group(1)}-{key.group(2)}"
    moved = numbers.moves.get(current)
    if moved is not None:
        return _move_notice(name, current, moved) + MOVE_NOTE
    if _is_next(current, numbers):
        return None
    return _move_notice(name, current, numbers.following)


def _resolved(file_path: str, cwd: str | None) -> Path:
    path = Path(file_path)
    return path if path.is_absolute() or cwd is None else Path(cwd) / path


def main() -> int:
    payload: HookPayload = json.load(sys.stdin.buffer)
    tool_input = payload.get("tool_input", {})
    file_path = tool_input.get("file_path")
    if file_path is None:
        return 0
    tool_name = payload.get("tool_name", "")
    if tool_name == "Write":
        text, previous = tool_input.get("content"), None
    else:
        text, previous = tool_input.get("new_string"), tool_input.get("old_string")
    # 일지가 아닌 파일은 읽지 않는다. context_for 도 같은 조건으로 거르지만 읽기가 그보다 먼저다.
    journal = read_journal(file_path) if is_journal(file_path) else None
    contexts = [context_for(tool_name, file_path, text, previous, journal)]
    if created_journal(tool_name, file_path, payload.get("tool_response")):
        directory = _resolved(file_path, payload.get("cwd")).parent
        contexts.append(number_context(file_path, run_overlap(directory)))
    context = "\n\n".join(item for item in contexts if item is not None)
    if not context:
        return 0
    print(
        json.dumps(
            {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": context}}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
