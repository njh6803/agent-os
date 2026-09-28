"""읽는 쪽이 다른 프로세스일 때: 교체와 겹친 읽기가 무엇을 겪나."""

import collections
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

READER = r"""
import collections, sys, time, tomllib
target, until = sys.argv[1], float(sys.argv[2])
c = collections.Counter()
while time.time() < until:
    try:
        with open(target, "rb") as f:
            tomllib.load(f)
        c["ok"] += 1
    except OSError as e:
        c[f"{type(e).__name__}/{getattr(e, 'winerror', None)}"] += 1
print(dict(c))
"""
d = Path(tempfile.mkdtemp())
target = d / "disabled.toml"
target.write_text('schema_version = "1"\n', encoding="utf-8")
until = time.time() + 3.0
child = subprocess.Popen(
    [sys.executable, "-c", READER, str(target), str(until)], stdout=subprocess.PIPE, text=True
)
time.sleep(0.5)
w = collections.Counter()
i = 0
while time.time() < until - 0.2:
    tmp = d / f"t{i}.tmp"
    i += 1
    tmp.write_text(f'schema_version = "1"\nagent = ["a{i}"]\n', encoding="utf-8")
    try:
        os.replace(tmp, target)
        w["ok"] += 1
    except OSError as e:
        tmp.unlink(missing_ok=True)
        w[f"{type(e).__name__}/{getattr(e, 'winerror', None)}"] += 1
print("writer:", dict(w))
print("reader (other process):", child.communicate()[0].strip())
