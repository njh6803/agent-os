"""짧은 동기 재시도가 교체·읽기 경합을 없애나.
같은 프로세스의 두 스레드, 그리고 다른 프로세스의 읽기."""

import collections
import os
import subprocess
import sys
import tempfile
import threading
import time
import tomllib
from pathlib import Path

DELAYS = (0.001, 0.002, 0.004, 0.008, 0.016)  # 합 31ms, 시도 6번


def retrying(action):
    for delay in (*DELAYS, None):
        try:
            return action(), DELAYS.index(delay) if delay is not None else len(DELAYS)
        except PermissionError:
            if delay is None:
                raise
            time.sleep(delay)


d = Path(tempfile.mkdtemp())
target = d / "disabled.toml"
target.write_text('schema_version = "1"\nagent = []\n', encoding="utf-8")


def read():
    with open(target, "rb") as f:
        return tomllib.load(f)


def write(i):
    tmp = d / f"disabled.toml.{i}.tmp"
    tmp.write_text(f'schema_version = "1"\nagent = ["a{i}"]\n', encoding="utf-8")
    try:
        retrying(lambda: os.replace(tmp, target))
    finally:
        tmp.unlink(missing_ok=True)


# (1) 스레드 경합
stop = threading.Event()
reads = collections.Counter()
writes = collections.Counter()
retries = collections.Counter()


def reader():
    while not stop.is_set():
        try:
            _, n = retrying(read)
            reads["ok"] += 1
            retries[f"read_retry_{n}"] += 1 if n else 0
        except OSError as e:
            reads[type(e).__name__] += 1


r = threading.Thread(target=reader)
r.start()
start = time.perf_counter()
for i in range(2000):
    try:
        write(i)
        writes["ok"] += 1
    except OSError as e:
        writes[type(e).__name__] += 1
stop.set()
r.join()
print(
    f"(1) thread race {time.perf_counter() - start:.2f}s writes={dict(writes)} reads={dict(reads)}"
)
print("    nonzero retries:", {k: v for k, v in retries.items() if v})

# (2) 다른 프로세스가 읽기를 쉬지 않고 돌린다
code = (
    "import tomllib,sys,collections,time\n"
    f"p=r'{target}'\n"
    "c=collections.Counter(); end=time.time()+3\n"
    "while time.time()<end:\n"
    "    try:\n"
    "        f=open(p,'rb'); tomllib.load(f); f.close(); c['ok']+=1\n"
    "    except PermissionError: c['perm']+=1\n"
    "print(dict(c))\n"
)
child = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
w = collections.Counter()
t0 = time.time()
i = 5000
while time.time() - t0 < 2.5:
    try:
        write(i)
        w["ok"] += 1
    except OSError as e:
        w[type(e).__name__] += 1
    i += 1
print(
    "(2) other-process reader (no retry there):",
    child.communicate()[0].strip(),
    "writer(with retry):",
    dict(w),
)

# (3) 오래 쥔 핸들: 재시도가 다하면 PermissionError 이고 옛 파일이 남는다
target.write_text('schema_version = "1"\nagent = ["old"]\n', encoding="utf-8")
opened = threading.Event()
release = threading.Event()


def hold():
    with open(target, "rb"):
        opened.set()
        release.wait()


h = threading.Thread(target=hold)
h.start()
opened.wait()
t0 = time.perf_counter()
try:
    write(99999)
    print("(3) unexpected ok")
except PermissionError:
    print(
        f"(3) held handle -> PermissionError after"
        f" {1000 * (time.perf_counter() - t0):.1f}ms; content:",
        target.read_text(encoding="utf-8").replace("\n", " | "),
    )
release.set()
h.join()
print("leftover tmp:", sorted(p.name for p in d.iterdir() if p.name != "disabled.toml"))
