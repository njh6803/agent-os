"""POSIX 런처(`mcp_launcher.py`)가 프로세스 그룹의 우두머리가 아니면 서버를 띄우지 않는지 잰다
(명세 "Linux 런처"의 "그룹의 우두머리가 아니면", 사용자 스토리 29). POSIX 만이고, `full_stack.py`가
사본에서 부른다.

지금 폴더의 `src/agent_os/adapters/mcp_launcher.py`를 쓴다. 회차마다 이 프로브가 중간 프로세스를 새
세션으로 띄운다. 그래서 중간 프로세스가 그 그룹의 우두머리이고 이 프로브는 그 그룹 밖이다. 중간
프로세스는 자기 번호와 그룹 번호를 파일에 남긴 뒤 런처를 띄우고, 런처에는 자기 번호를
넘긴다(어댑터가 자기 번호를 넘기는 것과 같은 자리). 런처 뒤의 서버는 자기 그룹 번호를 표지 파일에
쓰고 끝나는 파이썬이다. 갈래는 둘이다.

- `member`: 중간 프로세스가 런처를 새 세션 없이 띄운다. 런처는 중간 프로세스의 그룹에 들어
  우두머리가 아니다. 중간 프로세스는 런처의 끝을 기다려 그 종료 코드를 찍고 0으로 끝난다.
- `leader`(양성 대조): 중간 프로세스가 런처를 새 세션으로 띄운다(상류가 어댑터 아래에서 하는 것과
  같다). 런처가 서버를 띄우고 서버가 끝나면 자기 그룹을 SIGKILL 로 끄므로 런처는 -9로 끝나고, 중간
  프로세스는 그 그룹 밖이라 0으로 끝난다.

기대는 `--expect`로 준다. `refused`(지금 런처)이면 `member`의 런처가 종료 코드 2로 끝나며 표준
에러에 "우두머리가 아니라"를 찍고, 서버의 표지가 없고, 중간 프로세스가 0으로 끝나야 한다.
`killed`(우두머리인지 보는 줄을 끈 사본)이면 `member`의 런처가 서버를 띄운 뒤 부른 쪽의 그룹을 꺼
중간 프로세스가 -9로 끝나고, 서버의 표지에 적힌 그룹이 중간 프로세스의 것이어야 한다. 이 대조로
거부가 그 검사 줄에서 온다는 것과, 그 줄이 없으면 부른 쪽의 그룹이 꺼진다는 것을 가른다. `leader`는
두 기대에서 같다.

표지(재려는 상황이 났다): 중간 프로세스가 런처를 띄우기 전에 자기가 그룹의 우두머리라는 것(그룹
번호가 자기 번호)을 남겼고, 런처가 돌았다는 흔적(런처의 "런처:" 문구나 서버의 표지)이 있는 것이다.
표지가 없는 회차는 측정이 아니라고 따로 세고, 하나라도 있거나 기대와 어긋나면 1로 끝난다. 다 맞으면
만든 임시 폴더를 지우고, 아니면 경로를 남긴다.

끄는 것은 런처가 자기 그룹에 보내는 SIGKILL 뿐이다. 중간 프로세스를 늘 새 세션으로 띄우므로 그
그룹에는 중간 프로세스와 런처와 서버만 든다. 이 프로브는 번호로 프로세스를 끄지 않는다. 중간
프로세스가 기한을 넘기면 `subprocess.run`이 그 프로세스만 끄고 예외로 멈춘다(아직 거두지 않은
자식이라 번호가 다른 프로세스에 넘어가지 않았다).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

LAUNCHER = Path("src/agent_os/adapters/mcp_launcher.py")
REFUSED = "우두머리가 아니라"
LAUNCHER_PREFIX = "런처:"
WAIT_SECONDS = 30.0
ROUNDS = 3
_SERVER = "import os, sys\nwith open(sys.argv[1], 'w') as f:\n    f.write(str(os.getpgrp()))\n"
# 자기 번호와 그룹 번호를 남기고 런처를 띄운다. member 이면 새 세션 없이, leader 이면 새 세션으로
# 띄운다. 런처의 끝을 기다려 그 종료 코드를 찍는다.
_MIDDLE = """
import os, subprocess, sys
launcher, err_path, group_path, case, *server = sys.argv[1:]
with open(group_path, "w") as file:
    file.write(f"{os.getpid()} {os.getpgrp()}")
with open(err_path, "wb") as err:
    child = subprocess.Popen(
        [sys.executable, "-I", launcher, str(os.getpid()), *server],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=err,
        start_new_session=case == "leader",
    )
print(child.wait())
"""


def _round(case: str, number: int, folder: Path, expect: str) -> dict[str, object]:
    marker = folder / f"{case}-{number}.server"
    err = folder / f"{case}-{number}.err"
    group = folder / f"{case}-{number}.group"
    middle = subprocess.run(
        [sys.executable, "-c", _MIDDLE, str(LAUNCHER.resolve()), str(err), str(group), case]
        + [sys.executable, "-c", _SERVER, str(marker)],
        capture_output=True,
        text=True,
        timeout=WAIT_SECONDS,
        start_new_session=True,
    )
    # 거부했으면 서버를 띄우지 않는다. 늦게 뜨는 서버를 놓치지 않게 한 번 더 기다린다.
    time.sleep(1)
    middle_pid, middle_group = (_text(group).split() + ["", ""])[:2]
    launcher_stderr = _text(err).strip()
    refused = REFUSED in launcher_stderr
    server = marker.exists()
    server_group = _text(marker).strip() or None
    launcher_exit = middle.stdout.strip() or None
    was_leader = bool(middle_pid) and middle_pid == middle_group
    record: dict[str, object] = {
        "case": case,
        "round": number,
        "middle_exit": middle.returncode,
        "launcher_exit": launcher_exit,
        "middle_was_leader": was_leader,
        "refused_message": refused,
        "server_started": server,
        "server_group": server_group,
        "middle_pid": middle_pid or None,
        "launcher_stderr": launcher_stderr,
    }
    ran = server or launcher_stderr.startswith(LAUNCHER_PREFIX)
    record["measured"] = was_leader and ran
    if case == "leader":
        record["as_expected"] = (
            middle.returncode == 0
            and launcher_exit == "-9"
            and server
            and server_group != middle_pid
            and not refused
        )
    elif expect == "refused":
        record["as_expected"] = (
            middle.returncode == 0 and launcher_exit == "2" and refused and not server
        )
    else:
        record["as_expected"] = (
            middle.returncode == -9 and server and server_group == middle_pid and not refused
        )
    return record


def _text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expect", choices=("refused", "killed"), required=True)
    options = parser.parse_args()
    if os.name != "posix":
        print("POSIX 에서만 돈다", file=sys.stderr)
        return 2
    folder = Path(tempfile.mkdtemp(prefix="not-leader-"))
    not_measured: list[str] = []
    unexpected: list[str] = []
    for case in ("member", "leader"):
        for number in range(1, ROUNDS + 1):
            record = _round(case, number, folder, options.expect)
            print(json.dumps(record, ensure_ascii=False))
            label = f"{case}-{number}"
            if not record["measured"]:
                not_measured.append(label)
            elif not record["as_expected"]:
                unexpected.append(label)
    ok = not not_measured and not unexpected
    if ok:
        shutil.rmtree(folder)
    summary = {
        "expect": options.expect,
        "not_measured": not_measured,
        "unexpected": unexpected,
        "folder": None if ok else str(folder),
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
