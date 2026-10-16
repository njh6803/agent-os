"""tools/hook_session_usage.py — 세션 시작 훅이 계정을 장부에 남기고 새 요약을 한 번 보인다.

명세 `.scratch/token-usage/spec.md`의 "세션 시작 훅"과 Testing Decisions의 그 항목, 티켓 04다. CLI
는 실제로 부른다. 프로젝트 폴더는 `tmp_path` 의 임시 git 저장소이고, 홈(`USERPROFILE`·`HOME`)은 가짜
`.claude.json` 을 둔 임시 폴더라 이 저장소의 장부와 사람의 설정 파일에 닿지 않는다. 지금 시각에
기대는 판정(요약이 낡았는지, 표지의 지역 날짜)은 순수 함수에 시각을 줘서 본다.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tools.hook_session_usage import (
    GIT_TIMEOUT,
    HEADLESS_MARKER,
    RETRY_DELAY,
    Account,
    Notice,
    account_of,
    append,
    claim,
    common_dir_parent,
    read_account,
    shows_summary,
    summary_notice,
)
from tools.run_hooks import registered_hooks, registered_matchers
from tools.token_report import main as token_report
from tools.token_report import read_accounts

KST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / "tools" / "hook_session_usage.py"
SID = "aaaaaaaa-0000-0000-0000-000000000001"
UUID = "11111111-2222-3333-4444-555555555555"
EMAIL = "a@example.com"
# 가짜 `.claude.json` 의 다른 키. 훅이 이 값을 출력하거나 장부에 남기면 안 된다(대기열 272).
SECRET = "비밀-토큰-값-0000"

type Rec = dict[str, object]


def _저장소(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True)
    return repo


def _홈(tmp_path: Path, account: Rec | None = None) -> Path:
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    data: Rec = {
        "primaryApiKey": SECRET,
        "projects": {"C:/secret/place": {"history": [SECRET]}},
        "oauthAccount": account
        if account is not None
        else {"accountUuid": UUID, "emailAddress": EMAIL, "organizationName": SECRET},
    }
    (home / ".claude.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return home


def _훅(
    project: Path,
    home: Path,
    source: str = "startup",
    attended: str | None = "1",
    session: str = SID,
    *,
    project_dir: Path | None = None,
    headless: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """훅을 부른다. 페이로드의 `cwd` 는 `project` 다. `CLAUDE_PROJECT_DIR` 은 `project_dir` 이
    있으면 그것, 없으면 `project` 이고, `project_dir` 이 빈 경로(`Path()`)면 환경에서 뺀다."""
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"CLAUDE_CODE_SESSION_ATTENDED", "CLAUDE_PROJECT_DIR", HEADLESS_MARKER}
    }
    env.update(USERPROFILE=str(home), HOME=str(home))
    if project_dir != Path():
        env["CLAUDE_PROJECT_DIR"] = str(project_dir or project)
    if headless is not None:
        env[HEADLESS_MARKER] = headless
    if attended is not None:
        env["CLAUDE_CODE_SESSION_ATTENDED"] = attended
    payload = {
        "session_id": session,
        "hook_event_name": "SessionStart",
        "source": source,
        "cwd": str(project),
    }
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )


def _계정_줄(repo: Path) -> list[str]:
    path = repo / ".scratch" / "token-report" / "ledger" / "accounts.jsonl"
    return path.read_text(encoding="utf-8").splitlines()


def test_계정_기록_한_줄은_명세의_모양_그대로다(tmp_path: Path) -> None:
    """키의 차례까지 명세 "계정 기록의 줄"과 같다. `at` 은 UTC 의 ISO 8601 이고 끝이 `Z` 다."""
    repo = _저장소(tmp_path)

    process = _훅(repo, _홈(tmp_path), source="startup")

    assert process.returncode == 0, process.stderr
    [line] = _계정_줄(repo)
    matched = re.fullmatch(
        r'\{"v": 1, "at": "(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)", "session_id": "(.+)",'
        r' "source": "startup", "account_uuid": "(.+)", "email": "(.+)"\}',
        line,
    )
    assert matched is not None, line
    assert matched.groups()[1:] == (SID, UUID, EMAIL)


def test_git_공용_디렉터리는_절대_경로_한_줄일_때만_받는다() -> None:
    """git 2.31 전에는 `--path-format` 을 모르는 인자로 찍고 0 으로 끝나, 상대 경로 `.git` 이 함께
    나온다(PR 직전 버그 리뷰가 git 2.32 에 모르는 옵션을 줘 그 출력을 봤다). 그 부모(`.`)를 쓰면
    장부가 작업 폴더 아래에 쌓인다."""
    absolute = Path.cwd().anchor + "repo/.git"

    assert common_dir_parent(absolute + "\n") == Path(absolute).parent
    assert common_dir_parent("--path-format=absolute\n.git\n") is None
    assert common_dir_parent(".git\n") is None
    assert common_dir_parent("") is None


def test_덧붙인_줄이_사라졌으면_다시_덧붙인다(tmp_path: Path) -> None:
    """윈도의 덧붙이기는 끝으로 옮기기와 쓰기가 따로라, 함께 시작한 세션이 같은 자리에 써 한 줄이
    사라졌다(PR 직전 버그 리뷰가 훅 열여섯 개를 한꺼번에 풀어 열 번에 160줄 중 4줄이 사라진 것을
    봤다). 첫 쓰기가 남의 줄에 덮인 장면을, 첫 쓰기를 남의 줄로 바꿔 만든다."""
    path = tmp_path / "accounts.jsonl"
    writes: list[bytes] = []

    def 덮인다(fd: int, data: bytes) -> int:
        writes.append(data)
        return os.write(fd, b'{"other": 1}\n' if len(writes) == 1 else data)

    append(path, '{"mine": 1}', 덮인다)

    assert path.read_bytes() == b'{"other": 1}\n{"mine": 1}\n'
    assert len(writes) == 2


def test_장부의_줄_끝은_윈도에서도_LF다(tmp_path: Path) -> None:
    """읽는 쪽의 달 파일과 요약 파일도 LF 로 쓴다(`tools/token_report.py` 의 `write_atomic`). 텍스트
    모드로 열면 윈도의 CRT 가 `\\n` 을 `\\r\\n` 으로 바꾼다."""
    repo = _저장소(tmp_path)
    home = _홈(tmp_path)

    _훅(repo, home)
    _훅(repo, home, source="resume")

    data = (repo / ".scratch" / "token-report" / "ledger" / "accounts.jsonl").read_bytes()
    assert b"\r" not in data
    assert data.count(b"\n") == 2


def test_처음에_읽지_못한_claude_json은_짧게_기다려_한_번_다시_읽는다(tmp_path: Path) -> None:
    """Claude Code 가 그 파일을 다시 쓰는 도중이면 잘린 JSON 이 읽힌다. 기다리는 동안 파일이 다
    쓰인 장면을, 기다리는 함수가 파일을 마저 쓰게 해서 만든다."""
    home = _홈(tmp_path)
    path = home / ".claude.json"
    whole = path.read_text(encoding="utf-8")
    path.write_text(whole[: len(whole) // 2], encoding="utf-8")
    waits: list[float] = []

    def 기다린다(seconds: float) -> None:
        waits.append(seconds)
        path.write_text(whole, encoding="utf-8")

    assert read_account(path, 기다린다) == Account(UUID, EMAIL)
    assert waits == [RETRY_DELAY]


def test_다시_읽어도_못_읽으면_두_칸이_null이다(tmp_path: Path) -> None:
    path = tmp_path / ".claude.json"
    path.write_text('{"oauthAccount": {"accountUuid": ', encoding="utf-8")
    waits: list[float] = []

    assert read_account(path, waits.append) == Account(None, None)
    assert waits == [RETRY_DELAY]
    assert read_account(tmp_path / "없는.json", waits.append) == Account(None, None)


def test_읽었으면_기다리지_않는다(tmp_path: Path) -> None:
    waits: list[float] = []

    assert read_account(_홈(tmp_path) / ".claude.json", waits.append) == Account(UUID, EMAIL)
    assert waits == []


def test_계정_ID가_없으면_두_칸이_null이고_이메일만_없으면_이메일만_null이다() -> None:
    """읽는 쪽은 `account_uuid` 가 null 인 줄을 계정을 읽지 못한 줄로 본다(명세 "계정")."""
    assert account_of('{"oauthAccount": {"emailAddress": "a@example.com"}}') == Account(None, None)
    assert account_of('{"oauthAccount": {"accountUuid": "u1"}}') == Account("u1", None)
    assert account_of('{"oauthAccount": "x"}') == Account(None, None)
    assert account_of("[]") == Account(None, None)


# 요약의 판정(순수 함수)

SUMMARY = (
    "보고서 날짜: 2026-10-15\n"
    "환산 비용 $10.00 (a@example.com $8.00, 계정 모름 $2.00)\n"
    "경보 없음\n"
    "보고서: C:/repo/.scratch/token-report/daily/2026-10-15.md\n"
)
# 작업 스케줄러가 05:00 에 요약을 쓴 날의 지역 시각.
WRITTEN = datetime(2026, 10, 16, 5, 0, tzinfo=KST)


def test_새_요약은_보고서_날짜를_표지로_그대로_보인다() -> None:
    notice = summary_notice(SUMMARY, WRITTEN, WRITTEN + timedelta(hours=4))

    assert notice == Notice("summary-2026-10-15", SUMMARY.rstrip("\n"))


def test_보고서_날짜_줄을_읽지_못하면_보이지_않는다() -> None:
    now = WRITTEN + timedelta(hours=1)

    assert summary_notice("", WRITTEN, now) is None
    assert summary_notice("환산 비용 $1.00\n보고서 날짜: 2026-10-15\n", WRITTEN, now) is None
    assert summary_notice("보고서 날짜: 2026-13-40\n", WRITTEN, now) is None
    assert summary_notice("보고서 날짜 2026-10-15\n", WRITTEN, now) is None


def test_36시간까지는_낡지_않았고_넘으면_앞줄을_붙여_지역_날짜마다_한_번_보인다() -> None:
    """표지 이름에 지역 날짜를 더해, 갱신되지 않는 동안 하루 한 번 보인다. 지역 날짜는 UTC 가
    아니라 `now` 의 시간대의 날짜다(UTC 로는 아직 10-17 이 아니다)."""
    assert summary_notice(SUMMARY, WRITTEN, WRITTEN + timedelta(hours=36)) == Notice(
        "summary-2026-10-15", SUMMARY.rstrip("\n")
    )
    now = WRITTEN + timedelta(hours=43, minutes=30)  # 2026-10-18 00:30 KST, UTC 로는 10-17

    notice = summary_notice(SUMMARY, WRITTEN, now)

    assert notice is not None
    assert notice.marker == "summary-2026-10-15-stale-2026-10-18"
    first, *rest = notice.message.splitlines()
    assert "보고서가 43시간째 갱신되지 않았다" in first
    assert rest == SUMMARY.rstrip("\n").splitlines()


def test_요약은_시작한_세션에서만_보이고_헤드리스_세션은_가져가지_않는다() -> None:
    """헤드리스는 Claude Code 가 훅 환경에 준 `CLAUDE_CODE_SESSION_ATTENDED` 가 `0` 이거나, 카나리아
    도구가 붙인 표지 변수가 있는 세션이다(둘 다 쓰는 것은 사용자가 골랐다). 그 Claude Code 값이
    없으면 (그 변수가 없는 판) 대화형으로 보고, 표지 변수는 빈 값이면 없는 것으로 본다."""
    assert shows_summary("startup", "1", None)
    assert shows_summary("startup", None, None)
    assert shows_summary("startup", "1", "")
    assert not shows_summary("startup", "0", None)
    assert not shows_summary("startup", "1", "1")
    assert not shows_summary("startup", None, "1")
    for source in ("resume", "clear", "compact", "fork", None):
        assert not shows_summary(source, "1", None)


# 요약을 보이는 CLI


def _요약(repo: Path, text: str = SUMMARY, age: timedelta = timedelta(0)) -> Path:
    """주 체크아웃의 출력 폴더에 요약 파일을 쓰고 수정 시각을 지금보다 `age` 앞으로 둔다."""
    path = repo / ".scratch" / "token-report" / "summary.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    at = time.time() - age.total_seconds()
    os.utime(path, (at, at))
    return path


def _알림(process: subprocess.CompletedProcess[str]) -> str | None:
    """훅이 사람에게 낸 `systemMessage`. 출력이 없으면 None 이다. 모델에게 가는 칸은 없어야 한다."""
    assert process.returncode == 0, process.stderr
    if not process.stdout.strip():
        return None
    output = json.loads(process.stdout)
    assert set(output) == {"systemMessage"}, output
    message = output["systemMessage"]
    assert isinstance(message, str)
    return message


def test_새_요약_뒤_처음_시작한_세션만_요약을_보고_같은_보고서_날짜의_둘째는_침묵이다(
    tmp_path: Path,
) -> None:
    repo = _저장소(tmp_path)
    home = _홈(tmp_path)
    _요약(repo)

    assert _알림(_훅(repo, home)) == SUMMARY.rstrip("\n")
    assert _알림(_훅(repo, home, session="둘째")) is None
    assert (repo / ".scratch" / "token-report" / "shown" / "summary-2026-10-15").is_file()


def test_시작이_아닌_출처는_요약을_보이지_않고_표지도_가져가지_않는다(tmp_path: Path) -> None:
    repo = _저장소(tmp_path)
    home = _홈(tmp_path)
    _요약(repo)

    for source in ("resume", "clear", "compact", "fork"):
        assert _알림(_훅(repo, home, source=source)) is None

    assert _알림(_훅(repo, home)) == SUMMARY.rstrip("\n")


def test_05시_전에_연_세션이_있었어도_새_요약_뒤의_다음_시작은_보인다(tmp_path: Path) -> None:
    """00:00~04:59 에 연 세션은 전날 이미 본 요약(같은 보고서 날짜)이라 침묵하고, 05:00 의 새
    요약(다음 보고서 날짜)은 그 뒤 처음 시작한 세션이 본다(ADR 0033 이력 2026-10-16)."""
    repo = _저장소(tmp_path)
    home = _홈(tmp_path)
    _요약(repo, SUMMARY.replace("2026-10-15", "2026-10-14"))
    assert _알림(_훅(repo, home, session="전날")) is not None

    assert _알림(_훅(repo, home, session="자정_뒤")) is None
    _요약(repo)

    assert _알림(_훅(repo, home, session="05시_뒤")) == SUMMARY.rstrip("\n")


def test_낡은_요약은_앞줄을_붙여_보이고_같은_날의_둘째_시작은_침묵이다(tmp_path: Path) -> None:
    repo = _저장소(tmp_path)
    home = _홈(tmp_path)
    _요약(repo)
    assert _알림(_훅(repo, home, session="새_요약")) is not None
    _요약(repo, age=timedelta(hours=40, minutes=1))

    message = _알림(_훅(repo, home, session="낡은_뒤"))

    assert message is not None
    assert "보고서가 40시간째 갱신되지 않았다" in message.splitlines()[0]
    assert message.splitlines()[1:] == SUMMARY.rstrip("\n").splitlines()
    assert _알림(_훅(repo, home, session="같은_날")) is None


def test_PC를_막_켠_날의_낡은_요약_뒤에도_작업이_만든_새_요약은_다음_시작이_본다(
    tmp_path: Path,
) -> None:
    """못 보는 것: PC 가 36시간 넘게 꺼졌다 켜진 날 작업 스케줄러가 돌기 전에 연 첫 세션은 낡았다는
    앞줄과 옛 요약을 보고 그날의 낡은 요약 표지를 가져간다. 작업이 만든 새 요약은 보고서 날짜가 달라
    다음 시작이 본다."""
    repo = _저장소(tmp_path)
    home = _홈(tmp_path)
    _요약(repo, SUMMARY.replace("2026-10-15", "2026-10-13"), age=timedelta(hours=60))

    first = _알림(_훅(repo, home, session="켠_직후"))

    assert first is not None
    assert "PC 를 막 켰다면" in first.splitlines()[0]
    _요약(repo)
    assert _알림(_훅(repo, home, session="작업_뒤")) == SUMMARY.rstrip("\n")


def test_요약_파일이_없으면_침묵하고_계정은_남긴다(tmp_path: Path) -> None:
    repo = _저장소(tmp_path)

    assert _알림(_훅(repo, _홈(tmp_path))) is None
    assert len(_계정_줄(repo)) == 1


def test_헤드리스_세션은_계정만_남기고_요약의_표지를_가져가지_않는다(tmp_path: Path) -> None:
    repo = _저장소(tmp_path)
    home = _홈(tmp_path)
    _요약(repo)

    assert _알림(_훅(repo, home, attended="0", session="카나리아")) is None
    assert [json.loads(line)["session_id"] for line in _계정_줄(repo)] == ["카나리아"]
    assert not (repo / ".scratch" / "token-report" / "shown").exists()

    assert _알림(_훅(repo, home, session="사람")) == SUMMARY.rstrip("\n")


def test_ATTENDED_변수가_없는_판에서는_대화형으로_보고_요약을_보인다(tmp_path: Path) -> None:
    """못 보는 것: 그 변수가 없는 Claude Code 판에서는 카나리아 밖의 헤드리스 세션이 요약의 표지를
    가져간다."""
    repo = _저장소(tmp_path)
    _요약(repo)

    assert _알림(_훅(repo, _홈(tmp_path), attended=None)) == SUMMARY.rstrip("\n")


def test_카나리아의_표지가_있으면_ATTENDED가_없는_판에서도_표지를_가져가지_않는다(
    tmp_path: Path,
) -> None:
    """`tools/canary.py` 가 띄우는 세션의 환경에 붙인 표지 변수다. Claude Code 가 그 값을 바꾸거나
    없애도 카나리아는 걸러진다."""
    repo = _저장소(tmp_path)
    home = _홈(tmp_path)
    _요약(repo)

    assert _알림(_훅(repo, home, attended=None, headless="1", session="카나리아")) is None
    assert not (repo / ".scratch" / "token-report" / "shown").exists()
    assert len(_계정_줄(repo)) == 1

    assert _알림(_훅(repo, home, attended=None, session="사람")) == SUMMARY.rstrip("\n")


def test_사람이_보지_않아도_대화형으로_셈하는_세션은_표지를_가져간다(tmp_path: Path) -> None:
    """못 보는 것: `open-session` 이 연 데스크톱 세션도 Claude Code 가 `1` 을 준다. 훅은 사람이 그
    세션을 보는지 모른다."""
    repo = _저장소(tmp_path)
    home = _홈(tmp_path)
    _요약(repo)

    assert _알림(_훅(repo, home, attended="1", session="open_session_이_연_세션")) is not None
    assert _알림(_훅(repo, home, attended="1", session="사람이_연_세션")) is None


def test_표지를_만들지_못하면_보이지_않는다(tmp_path: Path) -> None:
    """못 보는 것: 출력 폴더에 쓸 수 없으면 요약을 놓친다. 표지 자리에 파일이 있어 폴더를 만들지
    못하는 장면이다."""
    blocked = tmp_path / "shown"
    blocked.write_text("", encoding="utf-8")

    assert not claim(blocked / "summary-2026-10-15")
    assert claim(tmp_path / "ok" / "summary-2026-10-15")
    assert not claim(tmp_path / "ok" / "summary-2026-10-15")


def test_같은_순간에_덧붙여_깨진_줄은_그_줄만_잃는다(tmp_path: Path) -> None:
    """못 보는 것: 함께 시작한 세션이 같은 자리에 덮어 깨진 줄이 남으면 읽는 쪽
    (`tools/token_report.py`)은 그 줄만 건너뛰고 훅은 그 뒤에 줄을 잇는다. 줄이 통째로 사라지는 길은
    `append` 가 다시 덧붙인다(위 시험)."""
    repo = _저장소(tmp_path)
    ledger = repo / ".scratch" / "token-report" / "ledger" / "accounts.jsonl"
    ledger.parent.mkdir(parents=True)
    ledger.write_bytes(b'{"v": 1, "at": "2026-10-15T00:00:00Z", "session_id": "mixed{"v": 1\n')

    _훅(repo, _홈(tmp_path))

    assert read_accounts(ledger) == {SID: EMAIL}


def test_CLI는_claude_json을_읽지_못해도_null_계정으로_한_줄을_남긴다(tmp_path: Path) -> None:
    repo = _저장소(tmp_path)
    home = tmp_path / "home"
    home.mkdir()

    process = _훅(repo, home, source="resume")

    assert process.returncode == 0, process.stderr
    [line] = _계정_줄(repo)
    assert json.loads(line)["source"] == "resume"
    assert (json.loads(line)["account_uuid"], json.loads(line)["email"]) == (None, None)


def test_fork도_새_세션_ID로_계정을_남긴다(tmp_path: Path) -> None:
    """`fork` 가 빠지면 갈라낸 세션이 "계정 모름"이 된다(명세 "훅")."""
    repo = _저장소(tmp_path)

    _훅(repo, _홈(tmp_path), source="fork", session="갈라낸_세션")

    [line] = _계정_줄(repo)
    assert json.loads(line) | {"at": ""} == {
        "v": 1,
        "at": "",
        "session_id": "갈라낸_세션",
        "source": "fork",
        "account_uuid": UUID,
        "email": EMAIL,
    }


def test_claude_json의_두_키_밖은_출력하지도_장부에_남기지도_않는다(tmp_path: Path) -> None:
    repo = _저장소(tmp_path)
    _요약(repo)

    process = _훅(repo, _홈(tmp_path))

    assert SECRET not in process.stdout + process.stderr
    ledger = repo / ".scratch" / "token-report" / "ledger"
    assert all(SECRET not in p.read_text(encoding="utf-8") for p in ledger.iterdir())
    assert "secret" not in "\n".join(_계정_줄(repo))


def test_워크트리에서_연_세션도_주_체크아웃의_장부에_쓴다(tmp_path: Path) -> None:
    repo = _저장소(tmp_path)
    identity = ["-c", "user.name=t", "-c", "user.email=t@localhost"]
    subprocess.run(
        ["git", "-C", str(repo), *identity, "commit", "-q", "--allow-empty", "-m", "x"],
        check=True,
        capture_output=True,
    )
    worktree = tmp_path / "wt"
    subprocess.run(
        ["git", "-C", str(repo), "worktree", "add", "-q", "-b", "x", str(worktree)],
        check=True,
        capture_output=True,
    )

    _훅(worktree, _홈(tmp_path))

    assert len(_계정_줄(repo)) == 1
    assert not (worktree / ".scratch").exists()


def test_CLAUDE_PROJECT_DIR이_없으면_페이로드의_cwd로_주_체크아웃을_찾는다(tmp_path: Path) -> None:
    repo = _저장소(tmp_path)

    _훅(repo, _홈(tmp_path), project_dir=Path())

    assert len(_계정_줄(repo)) == 1


def test_CLAUDE_PROJECT_DIR이_cwd보다_먼저다(tmp_path: Path) -> None:
    """`cwd` 는 Claude 가 `cd` 하면 따라 움직이고 `CLAUDE_PROJECT_DIR` 은 세션이 시작된 루트에
    머문다(`.claude/rules/tools.md` 의 디렉터리 고르기)."""
    repo = _저장소(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    subprocess.run(["git", "init", "-q", str(elsewhere)], check=True, capture_output=True)

    _훅(elsewhere, _홈(tmp_path), project_dir=repo)

    assert len(_계정_줄(repo)) == 1
    assert not (elsewhere / ".scratch").exists()


def test_장부를_쓰지_못해도_0으로_끝나고_요약은_따로_보인다(tmp_path: Path) -> None:
    """못 보는 것: 장부 폴더 자리에 파일이 있으면 그 세션의 계정 줄을 남기지 못한다. 세션 시작을
    깨지 않는다."""
    repo = _저장소(tmp_path)
    _요약(repo)
    (repo / ".scratch" / "token-report" / "ledger").write_text("", encoding="utf-8")

    message = _알림(_훅(repo, _홈(tmp_path)))

    assert message == SUMMARY.rstrip("\n")


def test_git_저장소_밖의_프로젝트에서는_아무것도_쓰지_않고_침묵한다(tmp_path: Path) -> None:
    """출력 폴더(주 체크아웃)를 찾지 못한다. 이 저장소 밖에서 연 세션은 애초에 이 훅이 돌지 않아
    보고서에 "계정 모름"으로 든다(아래 끝에서 끝까지)."""
    plain = tmp_path / "plain"
    plain.mkdir()

    process = _훅(plain, _홈(tmp_path))

    assert process.returncode == 0, process.stderr
    assert process.stdout == ""
    assert list(plain.iterdir()) == []


def test_등록은_SessionStart의_다섯_출처이고_시간_제한이_훅_안의_기다림보다_길다() -> None:
    registration = registered_hooks()["hook_session_usage.py"]

    assert registration.event == "SessionStart"
    assert registered_matchers("hook_session_usage.py", "SessionStart") == [
        "startup|resume|clear|compact|fork"
    ]
    assert registration.timeout > GIT_TIMEOUT + RETRY_DELAY


# 보고서 도구와 끝에서 끝까지


def _응답(mid: str, at: str) -> Rec:
    """`claude-opus-5-5` 입력 백만 토큰, $4.00 이다(tools/token_report.py 의 단가표)."""
    usage = {"input_tokens": 1_000_000, "output_tokens": 0}
    return {
        "type": "assistant",
        "timestamp": at,
        "isSidechain": False,
        "message": {"id": mid, "model": "claude-opus-5-5", "usage": usage, "content": []},
    }


def _기록(projects: Path, session: str, recs: list[Rec]) -> None:
    path = projects / "C--project-agent" / f"{session}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in recs), encoding="utf-8")


def _보고서(repo: Path, projects: Path) -> str:
    out = repo / ".scratch" / "token-report"
    args = ["daily", "--projects", str(projects), "--out", str(out)]
    assert token_report([*args, "--tz", "+09:00", "--today", "2026-10-16"]) == 0
    return (out / "daily" / "2026-10-15.md").read_text(encoding="utf-8")


def test_훅이_쓴_줄을_보고서_도구가_읽어_그_세션의_비용이_그_이메일로_든다(tmp_path: Path) -> None:
    """기록이 없는 세션(이 저장소 밖에서 연 세션, 훅을 들이기 전의 세션)은 "계정 모름"이다. 그
    보고서의 요약을 다음에 시작한 세션이 본다."""
    repo = _저장소(tmp_path)
    home = _홈(tmp_path)
    projects = tmp_path / "projects"
    _훅(repo, home, session=SID)
    _기록(projects, SID, [_응답("m1", "2026-10-15T00:00:00Z")])
    _기록(projects, "밖의_세션", [_응답("m2", "2026-10-15T01:00:00Z")])

    report = _보고서(repo, projects)

    assert f"| {EMAIL} | 4.00 | 50.0% | 1 |" in report
    assert "| 계정 모름 | 4.00 | 50.0% | 1 |" in report
    message = _알림(_훅(repo, home, session="다음_세션"))
    assert message is not None
    assert f"{EMAIL} $4.00" in message


def test_세션_도중에_계정을_바꾸면_그_뒤의_SessionStart가_세션_전체를_새_계정으로_옮긴다(
    tmp_path: Path,
) -> None:
    """못 보는 것: 계정은 세션마다 하나다(읽는 쪽은 null 이 아닌 마지막 줄을 쓴다). `/login` 은
    SessionStart 를 일으키지 않는다고 어림하므로, 바꾼 뒤 압축이나 이어 하기가 오지 않으면 세션
    전체가 옛 계정이고, 오면 바꾸기 전의 호출까지 새 계정으로 든다."""
    repo = _저장소(tmp_path)
    projects = tmp_path / "projects"
    _훅(repo, _홈(tmp_path), session=SID)
    _기록(projects, SID, [_응답("m1", "2026-10-15T00:00:00Z"), _응답("m2", "2026-10-15T02:00:00Z")])
    _홈(tmp_path, {"accountUuid": "u-새", "emailAddress": "b@example.com"})

    assert f"| {EMAIL} | 8.00 | 100.0% | 2 |" in _보고서(repo, projects)
    _훅(repo, _홈(tmp_path, {"accountUuid": "u-새", "emailAddress": "b@example.com"}), "compact")

    report = _보고서(repo, projects)

    assert "| b@example.com | 8.00 | 100.0% | 2 |" in report
    assert EMAIL not in report
