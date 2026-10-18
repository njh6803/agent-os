"""SessionStart 훅(startup|resume|clear|compact|fork). 세션의 계정을 장부에 남기고, 새 일간 보고서가
생긴 뒤 처음 시작한 세션에 요약을 한 번 보인다.

ADR 0033(이력 2026-10-16 "요약은 새 보고서 뒤 처음 시작한 세션에 보이고 클라우드 세션은 인계하지
않는다"), 명세 `.scratch/token-usage/spec.md` 의 "세션 시작 훅", 티켓 04 다. 장부와 요약 파일을 쓰고
읽는 쪽은 `tools/token_report.py` 이고, 두 쪽이 다른 티켓이라 줄과 첫 줄의 모양을 명세가 글자로
정했다.

계정 기록. 매번 출력 폴더의 `ledger/accounts.jsonl` 에 한 줄을 덧붙인다(`account_line`, 명세 "계정
기록의 줄"). 계정은 `~/.claude.json` 의 `oauthAccount.accountUuid` 와 `oauthAccount.emailAddress`
다. Claude Code 가 그 파일을 다시 쓰는 도중이라 읽지 못하면 `RETRY_DELAY` 초 기다려 한 번 다시 읽고,
그래도 못 읽거나 계정 ID 가 없으면 두 칸이 null 이다. 그 파일의 다른 키는 출력하지도 장부에 남기지도
않는다(대기열 272). 파이썬 안에서 읽으므로 설정 파일을 출력하는 호출을 막는
`hook_user_settings_read` 에 걸리지 않는다. `fork` 는 갈라낸 세션이 새 세션 ID 로 오는 출처라 빠지면
그 세션이 "계정 모름"이 된다(공식 hooks 문서의 SessionStart 매처 표, 명세 검토가 2026-10-16 에
읽었다).

출력 폴더. `CLAUDE_PROJECT_DIR`(없으면 페이로드의 `cwd`)의 git 공용 디렉터리의 부모(주 체크아웃)
아래 `.scratch/token-report/` 다. 워크트리에서 시작한 세션도 같은 곳에 쓴다. git 저장소가 아니면
아무것도 하지 않는다. `git rev-parse --path-format=absolute` 를 쓰므로 git 2.31 이상이어야
한다. 그보다 낮으면 git 이 그 옵션을 모르는 인자로 찍고 0 으로 끝나 상대 경로가 함께 나오므로,
출력이 절대 경로 한 줄이 아니면 저장소가 아닌 것으로 본다(`common_dir_parent`).
`tools/token_report.py` 의 `main_checkout` 도 같은 인자를 쓰고 그 확인이 없다(티켓 02 의 도구라
고치지 않았다).

요약. 출처가 `startup` 이고 헤드리스가 아닌 세션에서만 낸다(`shows_summary`). 요약 파일
`summary.txt` 의 첫 줄 `보고서 날짜: YYYY-MM-DD` 를 읽어, `shown/summary-<보고서 날짜>` 표지를
`O_EXCL` 로 처음 만든 호출만 요약을 `systemMessage` 로 사람에게 보인다(`summary_notice`, `claim`).
표지를 달력 날짜가 아니라 보고서 날짜로 거는 것은 08:00 의 작업 스케줄러보다 먼저 연 세션이 그날의
몫을 가져가지 않게 하기 위해서다. 요약 파일의 수정 시각이 36시간보다 오래됐으면 갱신되지 않았다는
앞줄을 붙이고 표지에 지역 날짜를 더해(`-stale-<지역 날짜>`) 갱신되지 않는 동안 하루 한 번 보인다.
요약 파일이 없거나 첫 줄을 읽지 못하면 아무것도 보이지 않는다. 표지는 지우지 않아 보고서 날짜마다
빈 파일 하나가(낡은 동안에는 지역 날짜마다 하나가 더) 쌓인다. 모델에게 가는 `additionalContext` 는
내지 않는다. `systemMessage` 가 세션 컨텍스트에 들지 않는지는 이 훅이 주 체크아웃에서 돌아야 재므로
티켓 09 가 본다.

헤드리스 세션. Claude Code 가 훅 환경에 주는 `CLAUDE_CODE_SESSION_ATTENDED` 가 `0` 이거나,
`tools/canary.py` 가 띄우는 세션의 환경에 붙인 표지 변수(`HEADLESS_MARKER`)가 있으면 헤드리스로 보고
계정만 남긴다(`shows_summary`). 둘 다 쓰는 것은 사용자가 골랐다(일지 2026-10-16-66). 앞의 것은
문서에 없는 내부 값이라 판이 바뀌면 이름이 바뀌거나 사라질 수 있고, 그때도 뒤의 것이 카나리아를
거른다. 그 표지 이름은 카나리아 도구가 따로 적고 시험이 두 이름을 대조한다(훅은 다른 도구를 import
하지 않는다). 앞의 것은 `.scratch/token-usage/probes/session_start_payload/` 에서 쟀다. 데스크톱
세션 안에서 띄운 `claude -p` 의 훅은 `0` 을, 터미널의 대화형 `claude` 의 훅은 `1` 을
받았다(`start.jsonl`). 페이로드에는 대화형을 가를 칸이 없었다(`model` 은 헤드리스에만 없었지만
데스크톱 세션의 페이로드는 재지 못해 쓰지 않는다). Claude Code 2.1.295·2.1.300 의 코드를
읽었다(`cli_attended.py` 가 찾는 표지들). 셸 도구와 훅의 환경을 같은 함수로 짓고, 그 값은 세션
종류(`CLAUDE_CODE_SESSION_KIND`)가 백그라운드·데몬이거나 판정 함수가 먼저 보는 조건 하나(축약된
이름이라 무엇인지 읽지 못했다)가 서면 `0`, 아니면 "대화형이거나, 시작할 때
`CLAUDE_CODE_CHILD_SESSION` 이 없었고 진입점이 데스크톱·VS Code 같은 목록에 있다"일 때 `1` 이다.
세션 안에서 띄운 `claude -p`(카나리아 등)는 부모에게서 `CLAUDE_CODE_CHILD_SESSION` 을 물려받아 자식
세션이다. 데스크톱 세션의 훅이 받는 값은 훅으로 재지 않았고, 이 코드와 그 세션의 셸이 `1` 을 받은
것으로 셈했다. `CLAUDE_CODE_ENTRYPOINT` 로는 가르지 못한다(`claude -p` 가 `claude-desktop` 을
물려받았다, `tools/hook_stop_korean.py` 독스트링).

못 보는 것:
- 세션 도중에 바꾼 계정. 읽는 쪽은 세션마다 null 이 아닌 마지막 줄의 계정 하나를 쓴다. `/login` 은
  SessionStart 를 일으키지 않는다고 어림하므로, 바꾼 뒤 같은 세션 ID 의 SessionStart(이어 하기와
  압축이 그렇다고 어림한다. `/clear` 가 새 ID 로 오는지는 재지 않았다)가 오지 않으면 세션 전체가 옛
  계정으로, 오면 바꾸기 전의 호출까지 새 계정으로 든다.
- 이 저장소 밖에서 연 세션. 프로젝트 설정의 훅이라 돌지 않아 보고서에 "계정 모름"으로 든다. git
  저장소가 아닌 프로젝트 폴더에서 돌면 아무것도 쓰지 않는다.
- `CLAUDE_CODE_SESSION_ATTENDED` 가 없는 Claude Code 판. 대화형으로 보아 카나리아 밖의 헤드리스
  세션은 요약의 표지를 가져간다(카나리아는 표지 변수로 걸러진다). 사람이 보지 않는데 대화형으로
  셈하는 세션(`open-session` 이 연 데스크톱 세션, 진입점을 손으로 목록의 것으로 준 자식 아닌
  `claude -p`)도 그렇다.
- PC 가 36시간 넘게 꺼졌다 켜진 날 작업 스케줄러가 돌기 전에 연 첫 세션. 낡았다는 앞줄과 옛 요약을
  보이고 그날의 낡은 요약 표지를 가져간다. 작업이 돈 뒤의 새 요약은 보고서 날짜가 달라 다음 시작이
  본다.
- 두 세션이 같은 순간에 덧붙인 줄. 윈도의 덧붙이기는 같은 자리에 덮여 한 줄을 잃을 수 있고, 쓴
  뒤 끝을 읽어 다시 덧붙이는 것(`append`)도 세 번 모두 덮이면 그 세션은 "계정 모름"이 된다. 덮이며
  깨진 줄이 남으면 읽는 쪽은 그 줄만 건너뛴다(PR 직전 리뷰의 재현에서는 깨진 줄이 없었다).
- 표지를 만들지 못한 때(출력 폴더에 쓸 수 없다). 요약을 보이지 않는다. 세션마다 거듭 보이는 것보다
  놓치는 것이 낫다.
- 장부를 쓰지 못한 때(장부 폴더 자리에 파일이 있는 등). 그 세션의 계정 줄을 남기지 않고 지나가며,
  요약은 따로 판정한다. 세션 시작을 깨지 않는다.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import NamedTuple, TypedDict

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None

FORMAT = 1
GIT_TIMEOUT = 5.0
RETRY_DELAY = 0.2
APPEND_TRIES = 3
# 덧붙인 줄이 남았는지 볼 파일 끝. 한 줄은 수백 바이트이고 함께 시작하는 세션은 많아야 열 남짓이다.
TAIL_BYTES = 64 * 1024
SUMMARY_SOURCE = "startup"
STALE_AFTER = timedelta(hours=36)
DATE_LINE = re.compile(r"보고서 날짜: ([0-9]{4}-[0-9]{2}-[0-9]{2})")
REPORT_DIR = Path(".scratch") / "token-report"
ACCOUNTS = Path("ledger") / "accounts.jsonl"
SUMMARY = "summary.txt"
SHOWN = "shown"
# `tools/canary.py` 의 `HEADLESS_ENV` 와 같은 이름이다. 시험이 대조한다.
HEADLESS_MARKER = "AGENT_OS_HEADLESS"
# 윈도의 `os.open` 은 이것이 없으면 텍스트 모드다. 다른 OS 에는 없다.
_BINARY = os.O_BINARY if sys.platform == "win32" else 0


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 SessionStart 입력 중 이 훅이 읽는 부분."""

    session_id: str
    source: str
    cwd: str


class Account(NamedTuple):
    uuid: str | None
    email: str | None


def _parse(text: str) -> Json:
    return json.loads(text)


def account_of(text: str) -> Account:
    """`~/.claude.json` 의 글에서 `oauthAccount` 의 두 키만 고른다. 계정 ID 가 없으면 이메일도
    버린다 — 읽는 쪽은 `account_uuid` 가 null 인 줄을 계정을 읽지 못한 줄로 본다. JSON 이 아니면
    ValueError."""
    data = _parse(text)
    account = data.get("oauthAccount") if isinstance(data, dict) else None
    if not isinstance(account, dict):
        return Account(None, None)
    uuid = _text(account.get("accountUuid"))
    if uuid is None:
        return Account(None, None)
    return Account(uuid, _text(account.get("emailAddress")))


def read_account(path: Path, sleep: Callable[[float], None] = time.sleep) -> Account:
    """`path`(`~/.claude.json`)의 계정. 읽지 못하면 `RETRY_DELAY` 초 기다려 한 번 다시 읽고, 그래도
    못 읽으면 두 칸이 None 이다."""
    for attempt in range(2):
        try:
            return account_of(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            if attempt == 0:
                sleep(RETRY_DELAY)
    return Account(None, None)


def account_line(session: str, source: str | None, account: Account, at: datetime) -> str:
    """계정 기록의 한 줄(명세 "계정 기록의 줄"). 줄바꿈은 붙이지 않는다."""
    line = {
        "v": FORMAT,
        "at": at.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session_id": session,
        "source": source,
        "account_uuid": account.uuid,
        "email": account.email,
    }
    return json.dumps(line, ensure_ascii=False)


def append(path: Path, line: str, write: Callable[[int, bytes], int] = os.write) -> None:
    """`line` 에 줄바꿈을 붙여 쓰기 하나로 덧붙이고, 파일 끝(`TAIL_BYTES`)에 그 줄이 없으면 다시
    덧붙인다(`APPEND_TRIES` 번까지). 윈도의 덧붙이기는 끝으로 옮기기와 쓰기가 따로라 함께 시작한
    세션이 같은 자리에 써 한 줄이 사라졌다(PR 직전 버그 리뷰가 훅 열여섯 개를 한꺼번에 풀어 열 번에
    160줄 중 4줄을 봤다). 같은 줄이 두 번 들어도 읽는 쪽에는 같다. 윈도에서는 `O_BINARY` 로 열어 줄
    끝이 LF 다. 그것 없이 연 `os.open` 은 윈도의 CRT 가 텍스트 모드로 열어 `\\n` 을 `\\r\\n` 으로
    바꿨다(셀프 리뷰가 이 PC 에서 바이트로 봤다). 쓰지 못하면 그대로 지나간다 — 세션 시작을 깨지
    않는다."""
    data = (line + "\n").encode("utf-8")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        _append_until_seen(path, data, write)
    except OSError:
        return


def _append_until_seen(path: Path, data: bytes, write: Callable[[int, bytes], int]) -> None:
    """`data` 를 쓰기 하나로 덧붙이고 파일 끝에 보이면 멈춘다. `APPEND_TRIES` 번까지 되풀이한다."""
    for _ in range(APPEND_TRIES):
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | _BINARY)
        try:
            write(fd, data)
        finally:
            os.close(fd)
        if data in _tail(path):
            return


def _tail(path: Path) -> bytes:
    """파일 끝의 `TAIL_BYTES` 바이트."""
    with path.open("rb") as fh:
        fh.seek(max(0, path.stat().st_size - TAIL_BYTES))
        return fh.read()


class Notice(NamedTuple):
    """사람에게 보일 요약. `marker` 는 표지 파일의 이름이다."""

    marker: str
    message: str


def shows_summary(source: str | None, attended: str | None, marker: str | None) -> bool:
    """요약을 보일 수 있는 세션인지. 시작한(`startup`) 세션이고 헤드리스가 아니어야 한다.

    `attended` 는 Claude Code 가 훅 환경에 주는 `CLAUDE_CODE_SESSION_ATTENDED` 다. `0` 이면
    헤드리스이고, 없으면 대화형으로 본다. `marker` 는 카나리아 도구가 붙인 표지 변수
    (`HEADLESS_MARKER`)의 값이고, 비지 않았으면 헤드리스다."""
    return source == SUMMARY_SOURCE and attended != "0" and not marker


def summary_notice(text: str, modified: datetime, now: datetime) -> Notice | None:
    """요약 파일의 글과 수정 시각으로 낼 알림. 첫 줄 `보고서 날짜: YYYY-MM-DD` 를 읽지 못하면 None.

    표지는 보고서 날짜로 건다. 수정 시각이 `STALE_AFTER` 보다 오래됐으면 갱신되지 않았다는 앞줄을
    붙이고 표지에 `now` 의 지역 날짜를 더한다. `now` 는 지역 시간대를 든 시각이다."""
    lines = text.splitlines()
    matched = DATE_LINE.fullmatch(lines[0]) if lines else None
    if matched is None:
        return None
    try:
        report = date.fromisoformat(matched.group(1))
    except ValueError:
        return None
    body = text.rstrip("\n")
    age = now - modified
    if age <= STALE_AFTER:
        return Notice(f"summary-{report.isoformat()}", body)
    hours = int(age.total_seconds() // 3600)
    head = (
        f"보고서가 {hours}시간째 갱신되지 않았다. PC 를 막 켰다면 작업 스케줄러가 곧 새로 만들고,"
        " 아니면 작업 스케줄러가 `tools/token_report.py daily` 를 돌리는지 본다."
    )
    return Notice(f"summary-{report.isoformat()}-stale-{now.date().isoformat()}", f"{head}\n{body}")


def pending_notice(out: Path, now: datetime) -> Notice | None:
    """출력 폴더의 요약 파일로 낼 알림. 파일이 없거나 읽지 못하면 None 이다."""
    path = out / SUMMARY
    try:
        text = path.read_text(encoding="utf-8")
        modified = datetime.fromtimestamp(path.stat().st_mtime, UTC)
    except (OSError, ValueError):
        return None
    return summary_notice(text, modified, now)


def claim(marker: Path) -> bool:
    """표지 파일을 이 호출이 처음 만들었으면 True. 이미 있거나 만들지 못하면 False 다.

    묻기와 기록을 `O_EXCL` 생성 하나로 겸해, 함께 열린 세션 둘이 함께 처음이라고 보지 않는다.
    만들지 못하면 보이지 않는다. 세션마다 거듭 보이는 것보다 놓치는 것이 낫다."""
    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        os.close(os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except OSError:
        return False
    return True


def main_checkout(project: str) -> Path | None:
    """`project` 의 git 공용 디렉터리의 부모. git 저장소가 아니면 None 이다."""
    try:
        done = subprocess.run(
            ["git", "-C", project, "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True,
            encoding="utf-8",
            timeout=GIT_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if done.returncode != 0:
        return None
    return common_dir_parent(done.stdout)


def common_dir_parent(stdout: str) -> Path | None:
    """`git rev-parse --path-format=absolute --git-common-dir` 의 출력에서 공용 디렉터리의 부모.
    절대 경로 한 줄이 아니면 None 이다. git 2.31 전에는 그 옵션을 모르는 인자로 찍고 0 으로 끝나
    상대 경로가 함께 나왔다(PR 직전 버그 리뷰가 git 2.32 에 모르는 옵션을 줘 봤다)."""
    lines = stdout.splitlines()
    if len(lines) != 1 or not Path(lines[0]).is_absolute():
        return None
    return Path(lines[0]).parent


def _text(value: object) -> str | None:
    return value if isinstance(value, str) else None


def main() -> int:
    payload: HookPayload = json.load(sys.stdin.buffer)
    project = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()
    checkout = main_checkout(project)
    if checkout is None:
        return 0
    out = checkout / REPORT_DIR
    source = _text(payload.get("source"))
    session = _text(payload.get("session_id"))
    if session is not None:
        account = read_account(Path.home() / ".claude.json")
        append(out / ACCOUNTS, account_line(session, source, account, datetime.now(UTC)))
    attended = os.environ.get("CLAUDE_CODE_SESSION_ATTENDED")
    if not shows_summary(source, attended, os.environ.get(HEADLESS_MARKER)):
        return 0
    notice = pending_notice(out, datetime.now().astimezone())
    if notice is not None and claim(out / SHOWN / notice.marker):
        sys.stdout.buffer.write(json.dumps({"systemMessage": notice.message}).encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
