"""실제 어댑터로 재시도 상한을 잰다(plugin-toggle 티켓 01, ADR 0017 의 2026-09-27 첫 이력).

읽기 스레드가 쉬지 않고 read_disabled() 를 부르고, 쓰기 스레드가 쉬지 않고 write_enabled() 로
켜고 끈다. 각각 몇 번 성공했고 몇 번 PluginError 였는지, 성공까지 쓰인 재시도 단계의 분포를 센다.
인자: 초(기본 3), 재시도 간격 목록(기본 어댑터의 것. "none" 이면 재시도 없음).
"""

import sys
import threading
import time
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

import agent_os.adapters.filesystem as fs
from agent_os.core.ports import PluginError
from agent_os.sdk import PluginKind, PluginName

seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
if len(sys.argv) > 2:
    fs._RETRY_DELAYS = (
        () if sys.argv[2] == "none" else tuple(float(x) for x in sys.argv[2].split(","))
    )

# 재시도 깊이를 세려고 어댑터가 부르는 sleep 을 감싼다. 한 시도(스레드별) 안에서 몇 번 잤는지.
local = threading.local()
original_sleep = fs.time.sleep


def counting_sleep(delay: float) -> None:
    local.depth = getattr(local, "depth", 0) + 1
    original_sleep(delay)


fs.time.sleep = counting_sleep

with TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / "agents" / "calc").mkdir(parents=True)
    (root / "agents" / "calc" / "plugin.toml").write_text(
        'schema_version = "1"\nkind = "agent"\nname = "calc"\n'
        'version = "0.1.0"\nentrypoint = "a:A"\n',
        encoding="utf-8",
    )
    plugins = fs.FilesystemPlugins(root)
    plugins.write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=False)
    stop = threading.Event()
    stats = {"read_ok": 0, "read_fail": 0, "write_ok": 0, "write_fail": 0}
    read_depth: Counter[int] = Counter()
    write_depth: Counter[int] = Counter()
    lock = threading.Lock()

    def reader() -> None:
        while not stop.is_set():
            local.depth = 0
            try:
                plugins.read_disabled()
                ok = True
            except PluginError:
                ok = False
            with lock:
                stats["read_ok" if ok else "read_fail"] += 1
                read_depth[local.depth] += 1

    def writer() -> None:
        enabled = True
        while not stop.is_set():
            local.depth = 0
            try:
                plugins.write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=enabled)
                ok = True
            except PluginError:
                ok = False
            with lock:
                stats["write_ok" if ok else "write_fail"] += 1
                write_depth[local.depth] += 1
            enabled = not enabled

    threads = [threading.Thread(target=reader), threading.Thread(target=writer)]
    for t in threads:
        t.start()
    time.sleep(seconds)
    stop.set()
    for t in threads:
        t.join()

print(f"delays={fs._RETRY_DELAYS} seconds={seconds}")
print(stats)
print("read retry depth:", dict(sorted(read_depth.items())))
print("write retry depth:", dict(sorted(write_depth.items())))
