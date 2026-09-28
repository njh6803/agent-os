"""윈도우: 다른 핸들이 연 파일을 os.replace 로 교체하면? 읽는 쪽은 교체 중에 실패하나?"""

import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

d = Path(tempfile.mkdtemp())
target = d / "disabled.toml"
target.write_text('schema_version = "1"\n', encoding="utf-8")


def replace_once(content: str) -> str:
    tmp = d / "disabled.toml.tmp"
    tmp.write_text(content, encoding="utf-8")
    try:
        os.replace(tmp, target)
        return "ok"
    except OSError as e:
        tmp.unlink(missing_ok=True)
        return f"{type(e).__name__} winerror={getattr(e, 'winerror', None)}"


# (a) 같은 프로세스의 다른 스레드가 연 채로
opened = threading.Event()
release = threading.Event()


def hold():
    with open(target, "rb"):
        opened.set()
        release.wait()


t = threading.Thread(target=hold)
t.start()
opened.wait()
print(
    "(a) same process, other thread holds:", replace_once('schema_version = "1"\nagent = ["a"]\n')
)
release.set()
t.join()
print("    content after:", target.read_text(encoding="utf-8").replace("\n", " | "))

# (b) 다른 프로세스가 연 채로
child = subprocess.Popen(
    [
        sys.executable,
        "-c",
        f"f=open(r'{target}','rb'); import sys; print('open', flush=True); sys.stdin.read()",
    ],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
)
assert child.stdout.readline().strip() == "open"
print("(b) other process holds:", replace_once('schema_version = "1"\nagent = ["b"]\n'))
child.stdin.close()
child.wait()
print("    content after:", target.read_text(encoding="utf-8").replace("\n", " | "))
