"""POSIX 런처 시제품(`mcp_launcher.py`)이, 자기를 띄운 프로세스가 런처가 뜨기 전에 이미 끝났으면
서버를 띄우지 않는지 잰다(명세 "Linux 런처"). POSIX 만이고, `full_stack.py`가 사본에서 부른다.

지금 폴더(사본의 루트)의 `src/agent_os/adapters/mcp_launcher.py`를 쓴다. 회차마다 중간 프로세스가
자식을 갈라 내고(`fork`), 그 자식이 새 세션을 연 뒤 런처로 바뀐다(`exec`). 런처에는 중간 프로세스의
번호를 넘긴다(어댑터가 자기 번호를 넘기는 것과 같은 자리). 런처 뒤의 서버는 표지 파일 하나를 만들고
끝나는 파이썬이다. 갈래는 둘이다.

- `died`: 중간 프로세스는 갈라 내자마자 끝난다. 자식은 자기 부모의 번호가 중간 프로세스의 것에서
  바뀐 것(입양되었다)을 본 뒤에 그 사실을 파일에 남기고 런처로 바뀐다. 그래서 런처가 뜰 때 넘겨받은
  번호의 프로세스는 이미 끝났다. 시간의 경주에 기대지 않는다.
- `alive`(양성 대조): 중간 프로세스는 자식이 끝나기를 기다려 그 종료 코드를 찍고, 자식은 곧바로
  런처로 바뀐다. 런처가 서버를 띄우고, 서버가 끝나면 그룹을 SIGKILL 로 끄므로 런처는 -9로 끝나고
  서버의 표지가 있다.

기대는 `--expect`로 준다. `refused`(지금 런처)이면 `died`의 런처가 표준 에러에 "이미 끝나"를 찍고
서버의 표지가 없어야 한다. `spawned`(`full_stack.py`의 `no_parent_watch` 사본, 부모와 견주는 두
자리를 지웠다)이면 `died`에도 서버의 표지가 생겨야 한다. 이 대조로 거부가 그 견줌에서 온다는 것을
가른다. 우두머리가 아니라서 띄우지 않은 것과는 런처의 문구로 가른다.

표지(재려는 상황이 났다): `died`는 자식이 부모가 바뀐 것을 본 뒤에 런처로 바뀌었다는 파일이다.
`alive`는 중간 프로세스가 런처의 끝을 기다려 종료 코드를 찍었고 런처가 돌았다는 흔적(서버의 표지나
런처의 문구)이 있는 것이다. 표지가 없는 회차는 측정이 아니라고 따로 세고, 하나라도 있거나 기대와
어긋나면 1로 끝난다. 다 맞으면 만든 임시 폴더를 지우고, 아니면 경로를 남긴다.
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
REFUSED = "이미 끝나"
LAUNCHER_PREFIX = "런처:"
WAIT_SECONDS = 30.0
ROUNDS = 3
_SERVER = "import sys; open(sys.argv[1], 'w').close()"
# 자식을 갈라 내고, 자식은 새 세션을 열고 표준 입출력을 바꾼 뒤 런처로 바뀐다. died 이면 자식이
# 부모가 바뀐 것을 본 뒤에 바뀌고 중간 프로세스는 곧바로 끝나며, alive 이면 중간 프로세스가 자식을
# 기다려 그 종료 코드를 찍는다.
_MIDDLE = """
import os, sys, time
launcher, err_path, gone_path, case, *server = sys.argv[1:]
middle = os.getpid()
child = os.fork()
if child == 0:
    try:
        os.setsid()
        null = os.open(os.devnull, os.O_RDWR)
        err = os.open(err_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
        os.dup2(null, 0)
        os.dup2(null, 1)
        os.dup2(err, 2)
        if case == "died":
            end = time.monotonic() + 10
            while os.getppid() == middle and time.monotonic() < end:
                time.sleep(0.01)
            if os.getppid() == middle:
                os._exit(3)
            open(gone_path, "w").close()
        os.execv(sys.executable, [sys.executable, "-I", launcher, str(middle), *server])
    finally:
        os._exit(127)
if case == "alive":
    print(os.waitstatus_to_exitcode(os.waitpid(child, 0)[1]))
"""


def _round(case: str, number: int, folder: Path, expect: str) -> dict[str, object]:
    marker = folder / f"{case}-{number}.server"
    err = folder / f"{case}-{number}.err"
    gone = folder / f"{case}-{number}.gone"
    middle = subprocess.run(
        [sys.executable, "-c", _MIDDLE, str(LAUNCHER.resolve()), str(err), str(gone), case]
        + [sys.executable, "-c", _SERVER, str(marker)],
        capture_output=True,
        text=True,
        timeout=WAIT_SECONDS,
    )
    end = time.monotonic() + WAIT_SECONDS
    while time.monotonic() < end and not marker.exists() and REFUSED not in _text(err):
        time.sleep(0.05)
    # 거부했으면 서버를 띄우지 않는다. 늦게 뜨는 서버를 놓치지 않게 한 번 더 기다린다.
    time.sleep(1)
    launcher_stderr = _text(err).strip()
    refused = REFUSED in launcher_stderr
    server = marker.exists()
    launcher_exit = middle.stdout.strip() or None
    record: dict[str, object] = {
        "case": case,
        "round": number,
        "middle_exit": middle.returncode,
        "launcher_exit": launcher_exit,
        "parent_gone_before_launch": gone.exists(),
        "refused_message": refused,
        "server_started": server,
        "launcher_stderr": launcher_stderr,
    }
    if case == "alive":
        ran = server or launcher_stderr.startswith(LAUNCHER_PREFIX)
        record["measured"] = launcher_exit is not None and ran
        record["as_expected"] = launcher_exit == "-9" and server and not refused
    elif expect == "refused":
        record["measured"] = gone.exists()
        record["as_expected"] = refused and not server
    else:
        record["measured"] = gone.exists()
        record["as_expected"] = server and not refused
    return record


def _text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expect", choices=("refused", "spawned"), required=True)
    options = parser.parse_args()
    if os.name != "posix":
        print("POSIX 에서만 돈다", file=sys.stderr)
        return 2
    folder = Path(tempfile.mkdtemp(prefix="stale-parent-"))
    not_measured: list[str] = []
    unexpected: list[str] = []
    for case in ("died", "alive"):
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
