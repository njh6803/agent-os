"""세션 기록에서 훅마다 알린 수와 막은 수를 센다.

retro가 새 훅·검사를 승인하기 전과 모델이 바뀐 뒤(`docs/model-selection.md` 4절)에 뺄 후보를 고르는
자리다(ADR 0036). 하네스는 더하는 장치만 있고 쓰이는지 재는 장치가 없었다. 훅 래퍼
(`tools/launch_hook.py`)에 기록을 더하지 않은 것은 래퍼가 훅의 출력을 바꾸지 않는다는 불변식
때문이고, Claude Code가 이미 세션 기록에 훅의 출력을 남기기 때문이다.

판정.
- 기록: `--projects`(기본 `~/.claude/projects`) 아래 이 저장소의 폴더, 곧 주 체크아웃의 경로로 지은
  이름(`--repo`)의 폴더와 그 이름 뒤에 `--claude-worktrees-`가 붙은 워크트리 폴더의 `*.jsonl` 전부다
  (서브에이전트 기록이 든 하위 폴더도 읽는다). 같은 `uuid`의 기록은 파일이 달라도 한 번 센다. 줄바꿈
  없는 마지막 줄은 쓰는 중일 수 있어 버린다.
- 훅 명령: `launch_hook.py <훅>`이거나, 래퍼 전의 등록 모양처럼 `tools/<훅>`을 바로 부르는 것이다.
- 알림: `hook_success` 첨부 가운데 명령이 훅 명령이고 stdout이 빈 글이 아닌 것. 이 첨부는 출력을 낸
  훅만 남는다. stderr만 낸 것(uv의 가상 환경 경고)과 래퍼가 훅을 돌리지 않고 지나간 알림(훅 파일이
  없다, 훅 이름 인자가 하나가 아니다. `launch_hook.skip_reason`의 두 문구)은 세지 않는다(2026-10-19
  이 PC의 기록에서 손으로 봤다).
- 막음: 도구 호출을 막은 훅은 첨부를 남기지 않고 도구 결과의
  `<이벤트>:<도구> hook error: <이유>`에만 이유가 남는다. 종료 코드 2로 막았으면 이유가
  `[<명령>]: `로 시작해 그 명령의 훅으로 센다. 아니면 이유에 든 글을 등록된 훅 파일의 문자열
  조각(독스트링을 뺀 문자열 상수와 f-문자열의 고정된 부분 가운데 `MIN_FRAGMENT`자 이상)과 견주어
  가장 긴 조각이 든 훅으로 센다. 가장 긴 조각이 두 훅에 같은 길이로 있으면 `AMBIGUOUS`, 든 조각이
  없으면 `UNKNOWN`이다. Stop 등이 막은 `hook_blocking_error` 첨부는 명령을 들어 그 명령의 훅으로
  센다.
- 창: 기록 시각의 UTC 날짜가 `--today`(기본 UTC 오늘)로 끝나는 `--days`(기본 28)일 안.
- 등록 훅: `<루트>/.claude/settings.json`의 명령에서 뽑는다. 들인 날은
  `git log --diff-filter=A`가 그 파일을 마지막으로 더한 커밋의 날짜다(지웠다가 다시 들인 훅은 다시
  들인 날이다).
- 뺄 후보: 창의 첫날보다 먼저 들였고 창 안에서 알리지도 막지도 않은 등록 훅. 창 안에 들인 훅과 들인
  날을 모르는 훅은 따로 적는다. 손상을 막는 훅은 0건이어도 남긴다. 그 판정은 retro 4단계가 한다.
  기록이 하나도 없거나 가장 이른 기록이 창의 첫날보다 늦으면 후보를 판정하지 않는다. 기록이 빈 날의
  발동은 0으로 보여 조용한 훅이 모두 후보가 된다.
- 읽는 사이 사라졌거나 열지 못한 기록 파일은 건너뛰고 머리 줄에 센다.

못 보는 것.
- 알림을 읽은 모델이 따랐는지는 모른다. 무시된 알림도 한 번으로 센다.
- 막는 훅의 이유가 그 훅 파일 밖(다른 모듈, 실행 중에 읽은 파일)의 글로만 지어지면 `UNKNOWN`이다.
  그래서 훅 페이로드 표의 막는 사례마다 그 이유를 이 도구가 그 훅으로 세는지 시험이 본다.
- 훅이 이유 문장을 바꾸면 그 전의 막음은 지금 파일의 조각과 맞지 않아 `UNKNOWN`이다. 2026-10-19 이
  PC의 기록에서 `hook_bash_python_stub`의 옛 이유(2026-09-22~09-28 판의 "Git Bash 의 python 은")
  24건이 그랬다.
- 이유에 다른 훅의 조각이 더 길게 인용되면 그 훅으로 센다.
- pre-commit과 CI의 검사는 세지 않는다(세션 기록에 없다). `tools/` 밖의 훅(플러그인 훅)의 알림도
  세지 않는다. 그 훅이나 앱이 도구 호출을 막은 것은 `UNKNOWN`으로 센다.
- 기록 보존 기한(Claude Code 의 `cleanupPeriodDays`, 기본 30일)보다 긴 창은 앞쪽이 비어 0으로 센다.
  그래서 가장 이른 기록 날짜를 함께 찍고, 그 날이 창의 첫날보다 늦으면 비어 있는 날 수를 적고 뺄
  후보는 판정하지 않는다.
- 카나리아 체크아웃(`<이름>-canary-*`)과 다른 PC의 기록은 읽지 않는다.
- 이름을 바꾼 훅은 새 이름을 더한 날을 들인 날로 본다. 옛 이름으로 지낸 날은 세지 않는다.

쓰임: `uv run python tools/hook_report.py [--days N] [--today YYYY-MM-DD] [--projects <폴더>]
[--repo <폴더 이름>] [--root <저장소 루트>]`. 기본 루트는 이 파일이 든 체크아웃이고, 기본 `--repo`는
그 체크아웃의 주 체크아웃 경로로 짓는다(`git rev-parse --git-common-dir`). 표준 라이브러리만 쓴다.
종료 0은 표를 냈다, 2는 인자가 틀렸거나(창이 날짜의 범위를 넘는 `--days` 도) settings.json·git을
읽지 못했다. 기록 파일을 모두 읽어 이 PC의 기록 4705개에서 한 번에 1분 남짓 걸렸다(2026-10-20, PR
직전 리뷰가 `time` 으로 한 번 손으로 쟀다. 다른 세션이 돌던 때다). Bash 도구로 칠 때는 `timeout` 을
300000으로 준다(기본 120초).
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

NOTICE = "알림"
BLOCK = "막음"
UNKNOWN = "(모름)"
AMBIGUOUS = "(여럿)"
MIN_FRAGMENT = 10
HEAD_WIDTH = 60
DEFAULT_DAYS = 28
GIT_TIMEOUT = 30
WORKTREE_INFIX = "--claude-worktrees-"
WRAPPER_NOTICES = ("launch_hook: 훅 파일이 없어", "launch_hook: 등록 명령의 훅 이름 인자가")
ROOT = Path(__file__).resolve().parent.parent

HOOK_COMMAND = re.compile(r"(?:launch_hook\.py\"?\s+|tools/)(hook_[A-Za-z0-9_]+\.py)")
COMMAND_HEAD = re.compile(r"^\[(.*?)\]: ", re.DOTALL)  # 종료 코드 2로 막은 이유의 머리
# 이벤트 이름(`PreToolUse`)과 도구 이름(`Bash`, `mcp__x__y`). `\w` 는 한글에도 맞아 쓰지 않는다
HOOK_ERROR = re.compile(r"^[A-Z][A-Za-z]+(?::[A-Za-z0-9_.-]+)? hook error: (.*)", re.DOTALL)

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None


@dataclass(frozen=True)
class Firing:
    """훅 한 번의 발동. `head` 는 막은 이유의 첫 줄 머리이고 알림이면 빈 글이다."""

    hook: str
    kind: str
    day: date
    head: str


@dataclass(frozen=True)
class Scan:
    """`broken` 은 JSON 객체로 읽지 못한 줄 수, `earliest` 는 시각이 든 기록 가운데 가장 이른
    날, `unreadable` 은 열지 못한 기록 파일 수(`files` 에 든다)다."""

    firings: tuple[Firing, ...]
    files: int
    broken: int
    earliest: date | None
    unreadable: int = 0


def folder_name_of(checkout: str) -> str:
    """Claude Code가 그 체크아웃의 세션 기록을 두는 폴더 이름. 영문자와 숫자 밖의 글자를 `-`로
    바꾼다(`tools/token_report.py` 의 같은 이름 함수와 같다)."""
    return re.sub(r"[^A-Za-z0-9]", "-", checkout)


def transcript_files(projects: Path, repo: str) -> list[Path]:
    folders = [projects / repo, *projects.glob(f"{repo}{WORKTREE_INFIX}*")]
    return sorted(path for folder in folders if folder.is_dir() for path in folder.rglob("*.jsonl"))


def _docstrings(tree: ast.Module) -> set[int]:
    """모듈·클래스·함수의 첫 문장이 문자열이면 그 노드의 id."""
    found: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                found.add(id(body[0].value))
    return found


def _fragments(source: str) -> frozenset[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return frozenset()
    skip = _docstrings(tree)
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skip:
            found.update(part.strip() for part in node.value.splitlines())
    return frozenset(part for part in found if len(part) >= MIN_FRAGMENT)


def fingerprints(tools: Path, hooks: Iterable[str]) -> dict[str, frozenset[str]]:
    """훅마다 막은 이유를 알아볼 문자열 조각. 파일이 없거나 읽지 못하면 빈 집합이다. f-문자열의
    고정된 부분도 `ast.Constant` 라 함께 든다."""
    prints: dict[str, frozenset[str]] = {}
    for hook in hooks:
        try:
            prints[hook] = _fragments((tools / hook).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            prints[hook] = frozenset()
    return prints


def blocking_hook(reason: str, prints: Mapping[str, frozenset[str]]) -> str:
    best = 0
    owners: list[str] = []
    for hook, parts in prints.items():
        length = max((len(part) for part in parts if part in reason), default=0)
        if length > best:
            best, owners = length, [hook]
        elif length == best and length:
            owners.append(hook)
    if not owners:
        return UNKNOWN
    return owners[0] if len(owners) == 1 else AMBIGUOUS


def _obj(value: Json) -> dict[str, Json]:
    return value if isinstance(value, dict) else {}


def _list(value: Json) -> list[Json]:
    return value if isinstance(value, list) else []


def _str(value: Json) -> str:
    return value if isinstance(value, str) else ""


def _parse_json(text: str) -> Json:
    # `json.loads` 의 반환형은 Any 라, 여기서 `Json` 으로 받아 뒤의 좁히기가 타입 검사를 지나게
    # 한다.
    return json.loads(text)


def _day(value: Json) -> date | None:
    try:
        moment = datetime.fromisoformat(_str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return moment.astimezone(UTC).date() if moment.tzinfo is not None else None


def _head(reason: str) -> str:
    return (reason.strip().splitlines() or [""])[0][:HEAD_WIDTH]


def _hook_of(command: str) -> str | None:
    match = HOOK_COMMAND.search(command)
    return match.group(1) if match else None


def _is_notice(stdout: str) -> bool:
    """래퍼는 처음부터 한글을 이스케이프하지 않고 냈다(`ensure_ascii=False`)."""
    return bool(stdout.strip()) and not any(notice in stdout for notice in WRAPPER_NOTICES)


def _result_texts(record: dict[str, Json]) -> list[str]:
    """사용자 기록의 도구 결과 글. 글 조각의 목록이면 이어 붙인다."""
    texts: list[str] = []
    for block in _list(_obj(record.get("message")).get("content")):
        part = _obj(block)
        if part.get("type") != "tool_result":
            continue
        content = part.get("content")
        if isinstance(content, str):
            texts.append(content)
        else:
            texts.append("".join(_str(_obj(item).get("text")) for item in _list(content)))
    return texts


def _record_firings(
    record: dict[str, Json], prints: Mapping[str, frozenset[str]]
) -> list[tuple[str, str, str]]:
    """기록 하나의 (훅, 종류, 이유 머리) 들."""
    attachment = _obj(record.get("attachment"))
    kind = attachment.get("type")
    if kind == "hook_success":
        hook = _hook_of(_str(attachment.get("command")))
        if hook is not None and _is_notice(_str(attachment.get("stdout"))):
            return [(hook, NOTICE, "")]
        return []
    if kind == "hook_blocking_error":
        error = _obj(attachment.get("blockingError"))
        reason = _str(error.get("blockingError"))
        hook = _hook_of(_str(error.get("command"))) or blocking_hook(reason, prints)
        return [(hook, BLOCK, _head(reason))]
    if record.get("type") != "user":
        return []
    found: list[tuple[str, str, str]] = []
    for text in _result_texts(record):
        match = HOOK_ERROR.match(text)
        if not match:
            continue
        reason = match.group(1)
        head = COMMAND_HEAD.match(reason)
        hook = _hook_of(head.group(1)) if head else None
        body = reason[head.end() :] if head else reason
        found.append((hook or blocking_hook(body, prints), BLOCK, _head(body)))
    return found


def scan(files: Iterable[Path], prints: Mapping[str, frozenset[str]]) -> Scan:
    firings: list[Firing] = []
    seen: set[str] = set()
    broken = 0
    count = 0
    unreadable = 0
    earliest: date | None = None
    for path in files:
        count += 1
        try:
            parts = path.read_bytes().split(b"\n")
        except OSError:  # 도는 동안 다른 세션이 기한 지난 기록을 지웠다
            unreadable += 1
            continue
        parts.pop()
        for raw in parts:
            if not raw.strip():
                continue
            try:
                record = _parse_json(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                broken += 1
                continue
            if not isinstance(record, dict):
                broken += 1
                continue
            uuid = _str(record.get("uuid"))
            if uuid and uuid in seen:
                continue
            seen.add(uuid)
            day = _day(record.get("timestamp"))
            if day is None:
                continue
            earliest = day if earliest is None else min(earliest, day)
            for hook, kind, head in _record_firings(record, prints):
                firings.append(Firing(hook, kind, day, head))
    return Scan(tuple(firings), count, broken, earliest, unreadable)


def registered_hooks(settings: str) -> list[str]:
    """settings.json 글의 명령 가운데 훅 명령의 훅 이름. ValueError 는 JSON 이 아닐 때다."""
    found: set[str] = set()
    for groups in _obj(_obj(_parse_json(settings)).get("hooks")).values():
        for group in _list(groups):
            for entry in _list(_obj(group).get("hooks")):
                hook = _hook_of(_str(_obj(entry).get("command")))
                if hook is not None:
                    found.add(hook)
    return sorted(found)


def _git(root: Path, *args: str) -> str:
    """git 출력. 실패하거나 시간을 넘기면 OSError 로 올린다."""
    try:
        done = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIMEOUT,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise OSError(f"git {args[0]} 이 {GIT_TIMEOUT}초 안에 끝나지 않았다") from error
    if done.returncode != 0:
        raise OSError(done.stderr.strip() or f"git {args[0]} 이 {done.returncode}로 끝났다")
    return done.stdout


def introduced_dates(root: Path, hooks: Iterable[str]) -> dict[str, date]:
    """훅 파일을 마지막으로 더한 커밋의 날짜. 지웠다가 다시 들인 훅은 다시 들인 날부터 센다. 기록에
    없는 훅(커밋하지 않은 새 훅)은 빠진다."""
    wanted = {f"tools/{hook}": hook for hook in hooks}
    if not wanted:
        return {}
    log = _git(root, "log", "--diff-filter=A", "--name-only", "--format=@%cs", "--", *wanted)
    dates: dict[str, date] = {}
    current: date | None = None
    for line in log.splitlines():
        if line.startswith("@"):
            current = date.fromisoformat(line[1:])
        elif current is not None and line in wanted:
            # 기록은 새것부터라 처음 것이 마지막에 더한 날이다
            dates.setdefault(wanted[line], current)
    return dates


def _listed(hooks: Iterable[str], introduced: Mapping[str, date]) -> str:
    text = ", ".join(f"{hook}({introduced[hook].isoformat()} 들임)" for hook in hooks)
    return text or "(없음)"


def render(
    result: Scan, hooks: Sequence[str], introduced: Mapping[str, date], today: date, days: int
) -> str:
    start = today - timedelta(days=days - 1)
    inside = [firing for firing in result.firings if start <= firing.day <= today]
    earliest = result.earliest.isoformat() if result.earliest else "없음"
    unopened = f", 읽지 못한 파일 {result.unreadable}개" if result.unreadable else ""
    out = [
        f"훅 발동 {start.isoformat()} ~ {today.isoformat()} ({days}일, UTC 날짜). 기록 파일"
        f" {result.files}개, 읽지 못한 줄 {result.broken}개{unopened}, 가장 이른 기록 {earliest}.",
    ]
    if result.earliest is not None and result.earliest > start:
        gap = (result.earliest - start).days
        out.append(f"가장 이른 기록이 {earliest} 이라 창의 앞 {gap}일은 기록이 없다.")
    counts: defaultdict[str, Counter[str]] = defaultdict(Counter)
    active_days: defaultdict[str, set[date]] = defaultdict(set)
    for firing in inside:
        if firing.hook in (UNKNOWN, AMBIGUOUS):
            continue
        counts[firing.hook][firing.kind] += 1
        active_days[firing.hook].add(firing.day)
    out += ["", "| 훅 | 알림 | 막음 | 발동한 날 | 마지막 |", "|---|---|---|---|---|"]
    ranked = sorted(counts, key=lambda hook: (-sum(counts[hook].values()), hook))
    for hook in ranked:
        mark = "" if hook in hooks else " (등록 안 됨)"
        last = max(active_days[hook]).isoformat()
        notices, blocks = counts[hook][NOTICE], counts[hook][BLOCK]
        out.append(f"| {hook}{mark} | {notices} | {blocks} | {len(active_days[hook])} | {last} |")
    quiet = [hook for hook in hooks if hook not in counts]
    old = [hook for hook in quiet if hook in introduced and introduced[hook] < start]
    young = [hook for hook in quiet if hook in introduced and introduced[hook] >= start]
    undated = [hook for hook in quiet if hook not in introduced]
    # 기록이 비어 있는 날에는 발동했어도 0으로 보여, 조용한 훅을 모두 후보로 낸다
    if result.earliest is None:
        verdict = "판정하지 않는다(기록이 없다. `--projects`·`--repo` 를 본다)"
    elif result.earliest > start:
        verdict = (
            f"판정하지 않는다(창의 앞 {(result.earliest - start).days}일에 기록이 없다."
            " `--days` 를 줄여 다시 돌린다)"
        )
    else:
        verdict = _listed(old, introduced)
    out += [
        "",
        f"뺄 후보: {verdict}",
        "  (창보다 먼저 들였고 창 안에서 알리지도 막지도 않았다. 손상을 막는 훅은 0건이어도 남긴다."
        " 판정은 retro 4단계)",
        f"아직 판단하지 않는 훅(창 안에 들였다): {_listed(young, introduced)}",
    ]
    if undated:
        out.append(f"들인 날을 모르는 훅: {', '.join(undated)}")
    unattributed = [firing for firing in inside if firing.hook in (UNKNOWN, AMBIGUOUS)]
    if unattributed:
        out.append(f"어느 훅인지 가르지 못한 막음 {len(unattributed)}건(이유의 머리마다):")
        heads = Counter((firing.hook, firing.head) for firing in unattributed)
        for (hook, head), number in heads.most_common():
            out.append(f"  {number}건 {hook} {head}")
    return "\n".join(out)


def _positive(text: str) -> int:
    try:
        value = int(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"양의 정수다: {text}") from error
    if value < 1:
        raise argparse.ArgumentTypeError(f"양의 정수다: {text}")
    return value


def _date_of(text: str) -> date:
    try:
        return date.fromisoformat(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"날짜는 YYYY-MM-DD다: {text}") from error


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hook_report.py", description="훅마다 알린 수와 막은 수. 자세한 것은 독스트링."
    )
    parser.add_argument("--days", type=_positive, default=DEFAULT_DAYS, help="창의 날 수")
    parser.add_argument("--today", type=_date_of, help="창의 끝 날 YYYY-MM-DD(기본 UTC 오늘)")
    parser.add_argument("--projects", type=Path, help="세션 기록 폴더(기본 ~/.claude/projects)")
    parser.add_argument(
        "--repo", help="이 저장소의 기록 폴더 이름(기본 주 체크아웃의 경로로 짓는다)"
    )
    parser.add_argument(
        "--root", type=Path, default=ROOT, help="settings.json 과 git 의 저장소 루트"
    )
    return parser


def main(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    root: Path = args.root
    days: int = args.days
    today: date = args.today or datetime.now(UTC).date()
    if days - 1 > (today - date.min).days:  # 기록을 다 읽은 뒤 창을 계산하다 넘치지 않게
        sys.stderr.write(f"창이 날짜의 범위를 넘는다: --days {days}\n")
        return 2
    projects: Path = args.projects or Path.home() / ".claude" / "projects"
    try:
        hooks = registered_hooks((root / ".claude" / "settings.json").read_text(encoding="utf-8"))
        repo: str = args.repo or folder_name_of(
            str(
                Path(
                    _git(root, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()
                ).parent
            )
        )
        introduced = introduced_dates(root, hooks)
    except (OSError, UnicodeDecodeError, ValueError) as error:
        sys.stderr.write(f"settings.json 이나 git 을 읽지 못했다: {error}\n")
        return 2
    prints = fingerprints(root / "tools", hooks)
    print(render(scan(transcript_files(projects, repo), prints), hooks, introduced, today, days))
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
    raise SystemExit(main(sys.argv[1:]))
