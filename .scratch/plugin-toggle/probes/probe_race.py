"""교체하는 쪽과 읽는 쪽이 같은 순간에 닿으면 각자 무엇을 겪나(같은 프로세스의 두 스레드)."""

import collections
import os
import tempfile
import threading
import time
import tomllib
from pathlib import Path

d = Path(tempfile.mkdtemp())
target = d / "disabled.toml"
target.write_text('schema_version = "1"\nagent = []\n', encoding="utf-8")
stop = threading.Event()
reads = collections.Counter()
writes = collections.Counter()


def reader():
    while not stop.is_set():
        try:
            with open(target, "rb") as f:
                tomllib.load(f)
            reads["ok"] += 1
        except OSError as e:
            reads[f"{type(e).__name__}/{getattr(e, 'winerror', None)}"] += 1


def writer(n: int):
    for i in range(n):
        tmp = d / f"disabled.toml.{i}.tmp"
        tmp.write_text(f'schema_version = "1"\nagent = ["a{i}"]\n', encoding="utf-8")
        try:
            os.replace(tmp, target)
            writes["ok"] += 1
        except OSError as e:
            tmp.unlink(missing_ok=True)
            writes[f"{type(e).__name__}/{getattr(e, 'winerror', None)}"] += 1


r = threading.Thread(target=reader)
r.start()
start = time.perf_counter()
writer(2000)
stop.set()
r.join()
print(f"{time.perf_counter() - start:.2f}s writes={dict(writes)} reads={dict(reads)}")
print("leftover tmp:", sorted(p.name for p in d.iterdir() if p.name != "disabled.toml"))
