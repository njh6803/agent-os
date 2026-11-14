"""release-image 명세가 결정을 내리려고, web 쪽 컨테이너 이미지 셋(관리 화면, 위젯, 위젯 미리보기
페이지)의 사실을 리눅스 컨테이너에서 잰다. 결정은 하지 않고 회차마다 본 것을 한 줄씩 낸다.

저장소 루트에서

    uv run python .scratch/release-image/probes/web_images/run.py --sections build
    uv run python .scratch/release-image/probes/web_images/run.py --sections <이름,이름,...>
        [--rounds <되풀이 수>] [--work <원본 출력을 둘 폴더>]

필요한 것. 도는 Docker 데몬(리눅스 컨테이너, BuildKit), build 단계에는 Docker Hub 와 npm
레지스트리에 닿는 네트워크. build 밖의 단계는 build 가 지어 둔 이미지(ri-web-img:<단계>)만 쓴다.
호스트 포트는 열지 않는다. 세 프로세스가 컨테이너 안의 루프백에만 묶이므로 요청은 모두 docker exec
로 컨테이너 안에서 건다(fetch.mjs). 띄운 컨테이너, 볼륨, 네트워크에는 라벨 ri-web-probe 를 달고,
시작할 때와 끝날 때 그 라벨이 붙은 것만 지운다. 이미지는 남긴다. 모든 명령의 원본 출력은
--work(없으면 시스템 임시 폴더) 아래 raw.log 에, 회차의 값은 results.jsonl 에 남는다.

표지. 회차마다 "재려는 상황이 실제로 났다"는 관찰을 본 뒤에만 측정으로 센다. 성공을 기대하는 회차는
응답의 상태 200 과 그 회차의 입력에서만 나오는 글(사이트 파일의 허용 출처, 가짜 상류의 토큰)을,
실패를 기대하는 회차는 종료 코드가 아니라 그 까닭의 문구를 본다. 섹션마다의 표지는 섹션 함수의
독스트링에 있다. 시간은 다른 세션이 같은 Docker 데몬을 쓰는 PC 에서 잰 값이라 범위로만 읽는다.

못 보는 것. 리눅스 호스트의 Docker Engine(이 스크립트가 돈 곳은 윈도의 Docker Desktop, WSL2
커널이다), 호스트 폴더를 붙이는 바인드 마운트의 소유자와 모드(이름 붙은 볼륨만 쓴다), 다른
컨테이너에서 오는 요청(루프백 규칙의 예외는 티켓이 짓는다), 브라우저. 결과는 같은 폴더의 README.md
에 있다.
"""

from __future__ import annotations

import argparse
import json
import re
import secrets
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds  # noqa: E402

WEB = ROOT / "web"
LABEL = "ri-web-probe"
REPO = "ri-web-img"
NODE_USER = "1000:1000"
ORIGIN_A = "https://probe-a.example"
ORIGIN_B = "https://probe-b.example"
CHARS_A = "771133"
CHARS_B = "583927"
SITE_A = "/probe/sites_a.toml"
SITE_B = "/probe/sites_b.toml"
WIDGET_URL = "http://127.0.0.1:3000/widget"
ELEMENT_URL = "http://127.0.0.1:3000/widget/element.js"
# Dockerfile 의 단계. 차례대로 짓는다(앞 단계의 층을 뒤 단계가 다시 쓴다).
TARGETS = (
    "base",
    "deps-full",
    "deps-full-homecache",
    "deps-widget-filter",
    "deps-widget-prod",
    "deps-widget-lean",
    "deps-admin-prod",
    "deps-portal-prod",
    "widget-full",
    "widget-full-nonroot",
    "widget-full-typegen",
    "widget-filter",
    "widget-prod",
    "widget-lean-withtests",
    "widget-lean",
    "widget-lean-typegen",
    "widget-lean-notc",
    "admin-src",
    "admin-full",
    "admin-prod",
    "admin-exception",
    "admin-standalone",
    "portal-prod",
    "portal-full",
)

_work: list[Path] = []
_token = secrets.token_hex(3)
_serial = [0]

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None


def raw(title: str, text: str) -> None:
    if _work:
        with (_work[0] / "raw.log").open("a", encoding="utf-8") as out:
            out.write(f"\n===== {time.strftime('%H:%M:%S')} {title}\n{text}\n")


def note(label: str, values: Mapping[str, Json]) -> None:
    """회차의 값을 화면에 한 줄로 찍고 results.jsonl 에 남긴다."""
    print(f"  {label}: " + ", ".join(f"{key}={value}" for key, value in values.items()), flush=True)
    if _work:
        with (_work[0] / "results.jsonl").open("a", encoding="utf-8") as out:
            out.write(json.dumps({"label": label, **values}, ensure_ascii=False) + "\n")


def parse(text: str) -> Json:
    try:
        parsed: Json = json.loads(text)
    except ValueError:
        return None
    return parsed


def as_map(value: Json) -> dict[str, Json]:
    return value if isinstance(value, dict) else {}


def as_list(value: Json) -> list[Json]:
    return value if isinstance(value, list) else []


def as_text(value: Json) -> str:
    return value if isinstance(value, str) else ""


def as_int(value: Json) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def dig(value: Json, *keys: str | int) -> Json:
    for key in keys:
        if isinstance(key, int):
            items = as_list(value)
            value = items[key] if -len(items) <= key < len(items) else None
        else:
            value = as_map(value).get(key)
    return value


@dataclass(frozen=True)
class Done:
    code: int
    out: str
    err: str
    seconds: float

    @property
    def text(self) -> str:
        return self.out + self.err


def run(argv: Sequence[str], *, timeout: float = 300, quiet: bool = False) -> Done:
    """명령 하나. 표준 입력은 닫힌 파이프다. 시간을 넘기면 종료 코드 -1."""
    started = time.monotonic()
    try:
        completed = subprocess.run(
            list(argv),
            cwd=HERE,
            input="",
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        done = Done(-1, "", f"{timeout:.0f}초 안에 끝나지 않았다", time.monotonic() - started)
    else:
        done = Done(
            completed.returncode, completed.stdout, completed.stderr, time.monotonic() - started
        )
    if not quiet:
        raw(" ".join(argv), f"exit={done.code}\n--- stdout\n{done.out}\n--- stderr\n{done.err}")
    return done


def docker(*args: str, timeout: float = 300, quiet: bool = False) -> Done:
    return run(["docker", *args], timeout=timeout, quiet=quiet)


def image(target: str) -> str:
    return f"{REPO}:{target}"


def fresh(kind: str) -> str:
    """이 실행이 만드는 컨테이너·볼륨·네트워크의 이름. 실행마다 토큰이 다르다."""
    _serial[0] += 1
    return f"ri-web-p-{_token}-{kind}-{_serial[0]}"


def sweep() -> None:
    """라벨이 붙은 컨테이너, 볼륨, 네트워크만 지운다. 다른 세션의 것은 건드리지 않는다."""
    for kind, lister, remover in (
        ("container", ("ps", "-aq"), ("rm", "-f", "-v")),
        ("volume", ("volume", "ls", "-q"), ("volume", "rm", "-f")),
        ("network", ("network", "ls", "-q"), ("network", "rm")),
    ):
        listed = docker(*lister, "--filter", f"label={LABEL}", timeout=60)
        ids = listed.out.split()
        if listed.code == 0 and ids:
            removed = docker(*remover, *ids, timeout=180)
            raw(f"sweep {kind}", f"{len(ids)}개, exit={removed.code}")


# ---------------------------------------------------------------------------------------------
# 컨테이너를 다루는 도우미


def start(
    target: str,
    *options: str,
    command: Sequence[str] = (),
    env: Mapping[str, str] | None = None,
    kind: str = "c",
) -> str:
    """컨테이너를 뒤에서 띄우고 이름을 낸다. 띄우지 못하면 예외다(그 회차는 측정이 아니다)."""
    name = fresh(kind)
    envs = [item for key, value in (env or {}).items() for item in ("-e", f"{key}={value}")]
    done = docker(
        "run", "-d", "--name", name, "--label", LABEL, *envs, *options, image(target), *command
    )
    if done.code != 0:
        raise RuntimeError(f"docker run 실패: {tail(done.text)}")
    return name


def tail(text: str, count: int = 3) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " / ".join(lines[-count:])


def logs(name: str) -> str:
    return docker("logs", name, timeout=60, quiet=True).text


def state(name: str) -> dict[str, Json]:
    done = docker("inspect", name, timeout=60, quiet=True)
    return as_map(dig(parse(done.out), 0, "State"))


def running(name: str) -> bool:
    return dig(state(name), "Running") is True


def until(name: str, needles: Sequence[str], *, timeout: float, count: int = 1) -> str:
    """기록에 needles 가운데 하나가 count 번 나오거나 컨테이너가 끝날 때까지 기다리고 기록을
    낸다."""
    deadline = time.monotonic() + timeout
    while True:
        text = logs(name)
        if any(text.count(needle) >= count for needle in needles):
            break
        if not running(name) or time.monotonic() > deadline:
            text = logs(name)
            break
        time.sleep(0.5)
    raw(f"logs {name}", text)
    return text


def epoch(stamp: str) -> float:
    """docker inspect 의 시각(나노초까지, Z 나 +hh:mm)을 epoch 초로. 읽지 못하면 0."""
    match = re.fullmatch(
        r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d+))?(Z|[+-]\d\d:\d\d)", stamp.strip()
    )
    if match is None:
        return 0.0
    zone = "+00:00" if match[3] == "Z" else match[3]
    whole = datetime.fromisoformat(match[1] + zone).timestamp()
    return whole + float(f"0.{match[2] or '0'}")


def stamp_of(text: str, mark: str, *, last: bool = False) -> float:
    """기록의 `RI_PROBE <mark> ... t=<epoch 초>` 줄에서 시각을 읽는다. 없으면 0."""
    found = re.findall(rf"RI_PROBE {re.escape(mark)}\b[^\n]*?\bt=(\d+\.\d+)", text)
    if not found:
        return 0.0
    return float(found[-1] if last else found[0])


def first_ok(text: str, *, last: bool = False) -> float:
    found = re.findall(r"RI_PROBE first-ok epoch_ms=(\d+)", text)
    if not found:
        return 0.0
    return int(found[-1] if last else found[0]) / 1000


def fetch(
    name: str,
    url: str,
    *,
    needles: Sequence[str] = (),
    headers: Sequence[str] = (),
    stream: bool = False,
) -> dict[str, Json]:
    """컨테이너 안에서 요청 하나를 건다(fetch.mjs). 본 것을 JSON 으로 받는다."""
    argv = ["exec", name, "node", "/probe/fetch.mjs", url]
    for needle in needles:
        argv += ["--needle", needle]
    for header in headers:
        argv += ["--header", header]
    if stream:
        argv.append("--stream")
    done = docker(*argv, timeout=60)
    return as_map(parse(done.out.strip().splitlines()[-1] if done.out.strip() else ""))


def serving(name: str, url: str, *, timeout: float) -> dict[str, Json]:
    """url 이 200 으로 답하거나 컨테이너가 끝날 때까지 기다린다. 마지막으로 본 응답을 낸다."""
    deadline = time.monotonic() + timeout
    seen: dict[str, Json] = {}
    while time.monotonic() < deadline:
        seen = fetch(name, url)
        if seen.get("status") == 200 or not running(name):
            break
        time.sleep(0.5)
    return seen


def shell(name: str, script: str, *, user: str | None = None) -> Done:
    """컨테이너 안에서 sh 스크립트 한 줄을 돈다."""
    who = ["--user", user] if user else []
    return docker("exec", *who, name, "sh", "-c", script, timeout=60)


def listening(name: str) -> list[str]:
    """컨테이너의 네트워크 이름공간에서 듣는 TCP 소켓의 주소(/proc/net/tcp 와 tcp6 의 상태 0A)."""
    done = shell(name, "cat /proc/net/tcp /proc/net/tcp6 2>/dev/null")
    found: list[str] = []
    for line in done.out.splitlines():
        fields = line.split()
        if len(fields) < 4 or fields[3] != "0A":
            continue
        address, _, port = fields[1].partition(":")
        if len(address) == 8:
            host = ".".join(str(byte) for byte in reversed(bytes.fromhex(address)))
        else:
            words = [bytes.fromhex(address[i : i + 8])[::-1].hex() for i in range(0, 32, 8)]
            host = "[" + ":".join("".join(words)[i : i + 4] for i in range(0, 32, 4)) + "]"
        found.append(f"{host}:{int(port, 16)}")
    return sorted(set(found))


def processes(name: str) -> list[tuple[int, int, str, str]]:
    """컨테이너 안 프로세스의 (pid, ppid, 상태, comm). ps 가 없는 이미지라 /proc 을 읽는다."""
    script = (
        'for p in /proc/[0-9]*; do s=$(cat "$p/stat" 2>/dev/null) || continue; '
        'echo "RI_PROC ${s##*) } |$(cat "$p/comm" 2>/dev/null)| ${p#/proc/}"; done'
    )
    found: list[tuple[int, int, str, str]] = []
    for line in shell(name, script).out.splitlines():
        match = re.fullmatch(r"RI_PROC (\S) (\d+) .*\|(.*)\| (\d+)", line.strip())
        if match is not None:
            found.append((int(match[4]), int(match[2]), match[1], match[3]))
    return found


def size_mb(target: str) -> float:
    done = docker("image", "inspect", "-f", "{{.Size}}", image(target), timeout=60)
    return round(int(done.out.strip() or "0") / 1024 / 1024, 1)


def seconds(value: float) -> float:
    return round(value, 1)


def line_value(text: str, mark: str) -> str:
    """기록의 마지막 `RI_PROBE <mark> <값>` 줄의 값. 없으면 빈 글."""
    found = re.findall(rf"RI_PROBE {re.escape(mark)} ([^\n]*)", text)
    return found[-1].strip() if found else ""


def duration(text: str, label: str) -> float | None:
    """Next 기록의 `<label> 1.2s`·`<label> 340ms` 꼴의 마지막 값(초). 없으면 None."""
    found = re.findall(rf"{re.escape(label)} ([\d.]+)(ms|s)\b", text)
    if not found:
        return None
    value, unit = found[-1]
    return round(float(value) / (1000 if unit == "ms" else 1), 2)


def finished(name: str, *, timeout: float) -> dict[str, Json]:
    """컨테이너가 끝날 때까지(또는 timeout 까지) 기다리고 State 를 낸다."""
    deadline = time.monotonic() + timeout
    while running(name) and time.monotonic() < deadline:
        time.sleep(0.5)
    return state(name)


def lifetime(found: Mapping[str, Json]) -> float:
    """State 의 StartedAt 에서 FinishedAt 까지(초)."""
    begin = epoch(as_text(found.get("StartedAt")))
    end = epoch(as_text(found.get("FinishedAt")))
    return seconds(end - begin) if begin and end else 0.0


def started_at(name: str) -> float:
    return epoch(as_text(state(name).get("StartedAt")))


def load(name: str) -> dict[str, Json]:
    """그때의 부하. 컨테이너 안의 /proc/loadavg 는 WSL2 VM 전체의 1분 평균이다. others 는 이 프로브
    밖에서 도는 컨테이너 수다(다른 세션의 이미지 빌드는 컨테이너로 보이지 않아 loadavg 로만
    잡힌다)."""
    average = shell(name, "cat /proc/loadavg").out.split()
    names = docker("ps", "--format", "{{.Names}}", timeout=60, quiet=True).out.split()
    return {
        "loadavg1": average[0] if average else "",
        "others": len([item for item in names if not item.startswith("ri-web-")]),
    }


def health_options(url: str, *, start_period: str = "600s", retries: int = 3) -> list[str]:
    """상태 확인 명령 후보. 이미지에 curl·wget 이 없어 node 의 fetch 로 건다. 200~299 면 0, 아니면
    1."""
    script = f"fetch('{url}').then(r=>process.exit(r.ok?0:1),()=>process.exit(1))"
    return [
        "--health-cmd",
        f'node -e "{script}"',
        "--health-interval",
        "2s",
        "--health-start-period",
        start_period,
        "--health-start-interval",
        "1s",
        "--health-timeout",
        "5s",
        "--health-retries",
        str(retries),
    ]


def health(name: str) -> dict[str, Json]:
    """Health 의 상태, 마지막 확인의 종료 코드(확인이 없으면 -1), 남은 기록(Docker 는 다섯 개만
    둔다)의 확인마다 걸린 ms."""
    found = as_map(state(name).get("Health"))
    entries = [as_map(item) for item in as_list(found.get("Log"))]
    last = entries[-1] if entries else {}
    took: list[Json] = [
        round((epoch(as_text(item.get("End"))) - epoch(as_text(item.get("Start")))) * 1000)
        for item in entries
        if item.get("End")
    ]
    return {
        "status": as_text(found.get("Status")),
        "last_exit": as_int(last.get("ExitCode")) if last else -1,
        "checks_ms": took,
    }


def wait_health(name: str, want: str, *, timeout: float) -> dict[str, Json]:
    deadline = time.monotonic() + timeout
    seen = health(name)
    while seen.get("status") != want and time.monotonic() < deadline:
        time.sleep(0.5)
        seen = health(name)
    return seen


def stop(name: str, *, grace: int = 10) -> dict[str, Json]:
    """docker stop -t <grace> 의 걸린 시간과 종료 코드. 멈추기 전의 pid 1 과 좀비 수를 함께
    적는다."""
    before = processes(name)
    begin = time.monotonic()
    done = docker("stop", "-t", str(grace), name, timeout=grace + 60)
    took = time.monotonic() - begin
    after = state(name)
    return {
        "pid1": next((comm for pid, _, _, comm in before if pid == 1), ""),
        "zombies": len([item for item in before if item[2] == "Z"]),
        "zombie_list": zombie_list(before),
        "stop_s": round(took, 2),
        "stop_exit": done.code,
        "exit_code": as_int(after.get("ExitCode")),
        "running_after": after.get("Running") is True,
    }


def zombie_list(found: Sequence[tuple[int, int, str, str]]) -> str:
    """좀비(Z)마다 `pid<-부모 pid:comm`."""
    return " ".join(f"{pid}<-{ppid}:{comm}" for pid, ppid, kind, comm in found if kind == "Z")


def stopped_cleanly(values: Mapping[str, Json]) -> bool:
    """stop 의 표지. 멈추기 전에 pid 1 이 보였고(돌고 있었다) 멈춘 뒤에는 돌지 않는다."""
    return (
        values.get("pid1") != ""
        and values.get("running_after") is False
        and (values.get("stop_exit") == 0)
    )


def written(name: str, app: str) -> list[str]:
    """docker diff 의 바뀐 자리. 다른 자리의 조상인 폴더는 빼고, app 아래는 두 단계(.next 는 한
    단계), 그 밖은 세 단계까지 줄여 모은다."""
    paths = [line[2:] for line in docker("diff", name, timeout=60).out.splitlines() if line[2:]]
    leaves = [path for path in paths if not any(other.startswith(path + "/") for other in paths)]
    found: set[str] = set()
    for path in leaves:
        if path.startswith(app + "/"):
            parts = path[len(app) + 1 :].split("/")
            found.add("<app>/" + "/".join(parts[: 1 if parts[0] == ".next" else 2]))
        else:
            found.add("/" + "/".join(path.strip("/").split("/")[:3]))
    return sorted(found)


def read_only(name: str) -> bool:
    """루트 파일 시스템이 읽기 전용인지(쓰기 시도가 그 까닭으로 실패하는지)."""
    done = shell(name, "touch /ri-web-write-test 2>&1; echo rc=$?")
    return "Read-only file system" in done.out


# ---------------------------------------------------------------------------------------------
# build: 이미지를 짓고 크기와 판을 적는다


def section_build(rounds: Rounds, _repeat: int) -> None:
    """Dockerfile 의 단계를 차례로 짓는다. 표지는 docker build 가 0 으로 끝나고 그 태그의 이미지가
    크기를 내는 것이다. 걸린 시간은 층 캐시가 있으면 0 에 가까워 빌드 시간의 근거가 아니다(빌드
    시간은 admin-time 과 widget-time 이 컨테이너 안에서 잰다). widget-lean 은 잠금 파일을 얼리지
    않고 설치하므로 next·typescript·vite 의 판이 widget-full 과 같은지도 표지로 본다."""
    for target in TARGETS:
        with rounds.round(f"build {target}") as current:
            done = docker(
                "build",
                "--progress",
                "plain",
                "-f",
                str(HERE / "Dockerfile"),
                "--build-context",
                f"probe={HERE}",
                "--target",
                target,
                "-t",
                image(target),
                str(WEB),
                timeout=1800,
            )
            size = size_mb(target) if done.code == 0 else 0.0
            note(
                f"build {target}",
                {"exit": done.code, "seconds": seconds(done.seconds), "size_mb": size},
            )
            if done.code != 0:
                note(f"build {target} 끝줄", {"tail": tail(done.text, 6)})
            built = done.code == 0 and size > 0
            current.mark(measured=built, result="지어졌다" if built else "짓지 못했다")
    with rounds.round("build 판") as current:
        found = {target: versions(target) for target in ("widget-full", "widget-lean")}
        info = docker("version", "--format", "{{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}")
        kernel = docker("info", "--format", "{{.KernelVersion}} cgroup v{{.CgroupVersion}}")
        note("판", {"docker": info.out.strip(), "kernel": kernel.out.strip(), **found})
        same = found["widget-full"] == found["widget-lean"] and "next=16." in found["widget-full"]
        current.mark(measured=same, result="widget-lean 의 판이 widget-full 과 같다")
    with rounds.round("build pnpm 메타데이터 캐시") as current:
        # 표지는 캐시 마운트로 뺀 갈래에는 그 폴더가 비고(0), 빼지 않은 갈래에는 수백 MB 가 있는
        # 것이다.
        sizes = {target: home_cache_mb(target) for target in ("deps-full", "deps-full-homecache")}
        note("pnpm 메타데이터 캐시(MB)", dict(sizes))
        split = sizes["deps-full"] == 0 and sizes["deps-full-homecache"] > 50
        current.mark(measured=split, result="캐시 마운트로 빼지 않으면 이미지에 얹힌다")


def home_cache_mb(target: str) -> int:
    script = "du -sm /root/.cache/pnpm 2>/dev/null | cut -f1"
    done = docker("run", "--rm", "--entrypoint", "sh", image(target), "-c", script, timeout=120)
    return int(done.out.strip() or "0")


def versions(target: str) -> str:
    script = (
        "echo node=$(node --version) pnpm=$(pnpm --version); "
        "for name in next typescript vite; do "
        "echo $name=$(node -p \"require('$name/package.json').version\"); done"
    )
    done = docker("run", "--rm", "--entrypoint", "sh", image(target), "-c", script, timeout=120)
    return " ".join(done.out.split())


# ---------------------------------------------------------------------------------------------
# 관리 화면

ADMIN_URL = "http://127.0.0.1:3000/"
ADMIN_TITLE = "관리 화면"
ADMIN_BUILD = (
    'echo "RI_PROBE build-begin t=$(date +%s.%N)"; node node_modules/next/dist/bin/next build; '
    'code=$?; echo "RI_PROBE build-exit code=$code t=$(date +%s.%N)"; '
    'echo "RI_PROBE memory.peak $(cat /sys/fs/cgroup/memory.peak)"; exit $code'
)
MANIFEST = (
    'require("./.next/routes-manifest.json").rewrites.afterFiles'
    '.map((rule) => rule.destination).join(" ")'
)


def admin(
    target: str,
    *options: str,
    env: Mapping[str, str] | None = None,
    url: str = ADMIN_URL,
    command: Sequence[str] = (),
    waiter: bool = True,
) -> tuple[str, str, dict[str, Json]]:
    """관리 화면 컨테이너를 uid 1000 으로 띄워 url 의 첫 200 을 기다린다. (이름, 기록, url 의
    응답). waiter 면 컨테이너 안의 wait.mjs 가 첫 200 의 시각을 찍고, 아니면 바깥에서 docker exec
    로 기다린다(wait.mjs 가 서비스의 자식 좀비로 남지 않게. zombie 섹션)."""
    name = start(
        target,
        "--user",
        NODE_USER,
        *options,
        env={**({"RI_PROBE_WAIT_URL": url} if waiter else {}), **(env or {})},
        command=command,
        kind="a",
    )
    if waiter:
        text = until(name, ["RI_PROBE first-ok"], timeout=120)
        ready = bool(first_ok(text))
    else:
        ready = serving(name, url, timeout=120).get("status") == 200
        text = logs(name)
    page = fetch(name, url, needles=[ADMIN_TITLE]) if ready else {}
    return name, text, page


def admin_up(page: dict[str, Json]) -> bool:
    """관리 화면이 섰다는 표지. 상태 200 과 첫 화면의 제목."""
    return page.get("status") == 200 and dig(page, "needles", ADMIN_TITLE) is True


def baked(target: str) -> str:
    """이미지의 빌드 산출물(routes-manifest.json)에 든 중계 대상. 서버를 띄우지 않고 읽는다."""
    done = docker(
        "run", "--rm", "--label", LABEL, "--entrypoint", "node", image(target), "-p", MANIFEST
    )
    return done.out.strip()


def stub(name: str, host: str, port: int, token: str) -> dict[str, Json]:
    """컨테이너 안에 가짜 상류를 띄우고 그 /ping 이 토큰으로 답할 때까지 기다린다(마지막 응답)."""
    docker("exec", "-d", name, "node", "/probe/upstream-stub.mjs", host, str(port), token)
    deadline = time.monotonic() + 30
    seen: dict[str, Json] = {}
    while time.monotonic() < deadline:
        seen = fetch(name, f"http://{host}:{port}/ping", needles=[token])
        if dig(seen, "needles", token) is True:
            break
        time.sleep(0.5)
    return seen


def section_admin_time(rounds: Rounds, repeat: int) -> None:
    """관리 화면의 빌드 시간과 시작 시간. 빌드는 admin-src(빌드 전의 나무, root)에서 next build 를
    돌려 빌드의 처음과 끝 시각과 cgroup 의 memory.peak 를 읽는다. 표지는 next build 가 0 으로 끝나고
    경로 표(Route (app))를 찍은 것이다. 시작은 세 갈래(admin-full, admin-prod, admin-standalone)를
    uid 1000 으로 띄워 컨테이너 시작에서 첫 200 까지를 잰다. 표지는 첫 화면의 상태 200 과 제목이다.
    standalone 은 HOSTNAME=127.0.0.1 을 준다(주지 않으면 컨테이너 주소에 묶인다, admin-standalone
    섹션)."""
    count = min(repeat, 2)
    for index in range(count):
        with rounds.round(f"admin-build #{index + 1}") as current:
            name = start("admin-src", command=("sh", "-c", ADMIN_BUILD), kind="b")
            found = finished(name, timeout=900)
            text = logs(name)
            raw(f"logs {name}", text)
            took = stamp_of(text, "build-exit") - stamp_of(text, "build-begin")
            peak = line_value(text, "memory.peak")
            note(
                f"admin-build #{index + 1}",
                {
                    "exit": as_int(found.get("ExitCode")),
                    "build_s": seconds(took),
                    "compile_s": duration(text, "Compiled successfully in"),
                    "peak_mib": round(int(peak) / 2**20) if peak.isdigit() else None,
                    **load_of(name),
                },
            )
            built = "RI_PROBE build-exit code=0" in text and "Route (app)" in text
            current.mark(measured=built, result="지었다")
            docker("rm", "-f", name, timeout=60)
    for target, env in (
        ("admin-full", {}),
        ("admin-prod", {}),
        ("admin-standalone", {"HOSTNAME": "127.0.0.1"}),
    ):
        for index in range(count):
            with rounds.round(f"admin-start {target} #{index + 1}") as current:
                name, text, page = admin(target, env=env)
                memory = shell(name, "cat /sys/fs/cgroup/memory.current").out.strip()
                note(
                    f"admin-start {target} #{index + 1}",
                    {
                        "total_s": round(first_ok(text) - started_at(name), 2),
                        "ready_s": duration(text, "Ready in"),
                        "memory_mib": round(int(memory) / 2**20) if memory.isdigit() else None,
                        "status": page.get("status"),
                    },
                )
                current.mark(measured=admin_up(page), result="섰다")
                docker("rm", "-f", name, timeout=60)


def load_of(name: str) -> dict[str, Json]:
    """끝난 컨테이너에는 exec 할 수 없어, 빌드 회차의 부하는 이 프로브 밖 컨테이너 수만 적는다."""
    names = docker("ps", "--format", "{{.Names}}", timeout=60, quiet=True).out.split()
    del name
    return {"others": len([item for item in names if not item.startswith("ri-web-")])}


def section_admin_reject(rounds: Rounds, _repeat: int) -> None:
    """AGENT_OS_UPSTREAM 에 루프백이 아닌 호스트를 주면 어디서 어떻게 거부되는지. 표지는 거부 문구의
    `받은 값: <호스트>` 와 그 자리의 머리(빌드면 `Build error occurred`, 시작이면 `Failed to load
    next.config.ts`)다. 시작 회차는 Next 의 Ready 줄이 거부보다 먼저 찍혔는지를 결과로 가른다. 양성
    대조(기본값으로는 지어지고 선다)는 admin-time 이다. standalone 은 시작 때 next.config.ts 를 읽지
    않아 거부 없이 서는지와, 그때 중계 대상이 빌드 때 값인지를 본다."""
    with rounds.round("admin-reject 빌드 때 http://serve:8000") as current:
        name = start(
            "admin-src",
            env={"AGENT_OS_UPSTREAM": "http://serve:8000"},
            command=("node", "node_modules/next/dist/bin/next", "build"),
            kind="r",
        )
        found = finished(name, timeout=300)
        text = logs(name)
        raw(f"logs {name}", text)
        note("admin-reject 빌드 때", {"exit": as_int(found.get("ExitCode")), "tail": tail(text, 5)})
        refused = "받은 값: serve" in text and "Build error occurred" in text
        current.mark(
            measured=refused and as_int(found.get("ExitCode")) != 0, result="빌드가 거부했다"
        )
    for host in ("serve", "localhost"):
        with rounds.round(f"admin-reject 시작 때 http://{host}:8000") as current:
            name = start(
                "admin-full",
                "--user",
                NODE_USER,
                env={"AGENT_OS_UPSTREAM": f"http://{host}:8000"},
                kind="r",
            )
            found = finished(name, timeout=120)
            text = logs(name)
            raw(f"logs {name}", text)
            refusal = text.find(f"받은 값: {host}")
            ready = text.find("Ready in")
            note(
                f"admin-reject 시작 때 {host}",
                {
                    "exit": as_int(found.get("ExitCode")),
                    "lifetime_s": lifetime(found),
                    "ready_before_refusal": 0 <= ready < refusal,
                },
            )
            refused = refusal >= 0 and "Failed to load next.config.ts" in text
            current.mark(
                measured=refused and as_int(found.get("ExitCode")) != 0,
                result="Ready 를 찍은 뒤 거부했다"
                if 0 <= ready < refusal
                else "Ready 전에 거부했다",
            )
    with rounds.round("admin-reject standalone 시작 때 http://serve:8000") as current:
        name, text, page = admin(
            "admin-standalone",
            env={"HOSTNAME": "127.0.0.1", "AGENT_OS_UPSTREAM": "http://serve:8000"},
        )
        destination = docker("exec", name, "node", "-p", MANIFEST).out.strip()
        note("admin-reject standalone", {"status": page.get("status"), "destination": destination})
        current.mark(
            measured=admin_up(page)
            and "받은 값" not in text
            and destination == "http://127.0.0.1:8000/:path*",
            result="거부 없이 섰고 중계 대상은 빌드 때 값이다",
        )
        docker("rm", "-f", name, timeout=60)


def section_admin_upstream(rounds: Rounds, _repeat: int) -> None:
    """상류가 빌드 산출물에 굳는지와, 다른 컨테이너의 상류로 중계하는 길. 표지는 회차마다 가짜
    상류가 답한 토큰이다(upstream-stub.mjs 가 /ping 에 토큰과 받은 Authorization 을 싣는다).
    - 굳은 값: admin-full 과 admin-exception 의 routes-manifest.json 에 든 중계 대상.
    - 시작 때 환경 변수: admin-full 을 AGENT_OS_UPSTREAM=http://127.0.0.1:9999 로 띄우고 컨테이너
      안에 8000(built)과 9999(startenv) 두 가짜 상류를 둔다. 9999 가 직접은 답한다는 것이 양성
      대조다.
    - 예외 판: 사용자 정의 네트워크에 별칭 serve 의 가짜 상류 컨테이너를 두고 admin-exception 으로
      /api/ping(토큰과 Authorization)과 /api/sse(이벤트 넷이 생기는 대로 오는지)를 건다. 같은
      네트워크의 admin-full 은 닿지 않는 것(500)이 대조다.
    - 시작 때 바꿔 넣기: 그 admin-full 의 routes-manifest.json 을 root 로 바꿔 쓰고 다시 띄운다."""
    with rounds.round("admin-upstream 빌드 산출물에 굳은 값") as current:
        found = {target: baked(target) for target in ("admin-full", "admin-exception")}
        note("admin-upstream 굳은 값", dict(found))
        current.mark(
            measured=found["admin-full"] == "http://127.0.0.1:8000/:path*"
            and found["admin-exception"] == "http://serve:8000/:path*",
            result="빌드 때 값이 산출물에 있다",
        )
    with rounds.round("admin-upstream 시작 때 환경 변수") as current:
        name, _, page = admin("admin-full", env={"AGENT_OS_UPSTREAM": "http://127.0.0.1:9999"})
        stub(name, "127.0.0.1", 8000, "built")
        direct = stub(name, "127.0.0.1", 9999, "startenv")
        relayed = fetch(name, "http://127.0.0.1:3000/api/ping", needles=["built", "startenv"])
        note(
            "admin-upstream 시작 때 환경 변수",
            {
                "direct_9999": dig(direct, "needles", "startenv"),
                "status": relayed.get("status"),
                "built": dig(relayed, "needles", "built"),
                "startenv": dig(relayed, "needles", "startenv"),
            },
        )
        answered = admin_up(page) and dig(direct, "needles", "startenv") is True
        current.mark(
            measured=answered and relayed.get("status") == 200,
            result="빌드 때 값으로 중계했다"
            if dig(relayed, "needles", "built") is True
            else "시작 때 값으로 중계했다",
        )
        docker("rm", "-f", name, timeout=60)
    network = fresh("net")
    docker("network", "create", "--label", LABEL, network, timeout=60)
    start(
        "admin-src",
        "--network",
        network,
        "--network-alias",
        "serve",
        "--entrypoint",
        "node",
        command=("/probe/upstream-stub.mjs", "0.0.0.0", "8000", "other-container"),
        kind="s",
    )
    with rounds.round("admin-upstream 예외 판이 다른 컨테이너로 중계") as current:
        name, _, page = admin("admin-exception", "--network", network)
        ping = fetch(
            name,
            "http://127.0.0.1:3000/api/ping",
            needles=["other-container", "probe-token-1"],
            headers=["Authorization: Bearer probe-token-1"],
        )
        sse = fetch(
            name, "http://127.0.0.1:3000/api/sse", needles=["other-container-4"], stream=True
        )
        arrivals = [as_int(dig(item, "ms")) for item in as_list(sse.get("arrivals"))]
        spread = arrivals[-1] - arrivals[0] if len(arrivals) > 1 else 0
        note(
            "admin-upstream 예외 판",
            {
                "ping": ping.get("status"),
                "token": dig(ping, "needles", "other-container"),
                "authorization": dig(ping, "needles", "probe-token-1"),
                "sse_arrivals_ms": " ".join(str(item) for item in arrivals),
            },
        )
        relayed = ping.get("status") == 200 and dig(ping, "needles", "other-container") is True
        streamed = dig(sse, "needles", "other-container-4") is True and len(arrivals) == 4
        current.mark(
            measured=admin_up(page) and relayed and streamed and spread >= 1000,
            result="중계했고 Authorization 이 넘어갔다"
            if dig(ping, "needles", "probe-token-1") is True
            else "중계했고 Authorization 이 넘어가지 않았다",
        )
        docker("rm", "-f", name, timeout=60)
    with rounds.round("admin-upstream 기본 판은 다른 컨테이너에 닿지 않는다(대조)") as current:
        name, _, page = admin("admin-full", "--network", network)
        ping = fetch(name, "http://127.0.0.1:3000/api/ping", needles=["other-container"])
        note("admin-upstream 대조", {"ping": ping.get("status")})
        current.mark(
            measured=admin_up(page)
            and ping.get("status") == 500
            and dig(ping, "needles", "other-container") is False,
            result="500",
        )
    with rounds.round("admin-upstream 시작 때 산출물을 바꿔 넣기") as current:
        sed = docker(
            "exec",
            "-u",
            "0",
            name,
            "sed",
            "-i",
            "s#http://127.0.0.1:8000#http://serve:8000#g",
            ".next/routes-manifest.json",
        )
        docker("restart", "-t", "10", name, timeout=120)
        text = until(name, ["RI_PROBE first-ok"], timeout=120, count=2)
        destination = docker("exec", name, "node", "-p", MANIFEST).out.strip()
        ping = fetch(name, "http://127.0.0.1:3000/api/ping", needles=["other-container"])
        note(
            "admin-upstream 바꿔 넣기",
            {"sed": sed.code, "destination": destination, "ping": ping.get("status")},
        )
        current.mark(
            measured=text.count("RI_PROBE first-ok") >= 2
            and destination == "http://serve:8000/:path*"
            and ping.get("status") == 200
            and dig(ping, "needles", "other-container") is True,
            result="다른 컨테이너로 중계했다",
        )


def section_admin_standalone(rounds: Rounds, _repeat: int) -> None:
    """output: "standalone" 의 server.js 가 듣는 주소. 표지는 /proc/net/tcp 의 듣는 소켓과, 그
    주소로 건 요청의 200(그리고 다른 주소로 건 요청의 연결 거부)이다. Docker 는 HOSTNAME 에 컨테이너
    ID 를 넣는다."""
    with rounds.round("admin-standalone HOSTNAME 을 주지 않음") as current:
        name = start("admin-standalone", "--user", NODE_USER, kind="t")
        text = until(name, ["Ready in"], timeout=60)
        address = docker(
            "inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", name
        ).out.strip()
        bound = listening(name)
        loop = fetch(name, ADMIN_URL)
        outer = fetch(name, f"http://{address}:3000/", needles=[ADMIN_TITLE])
        hostname = re.search(r"hostname_env=(\S+)", text)
        note(
            "admin-standalone 기본",
            {
                "hostname_env": hostname[1] if hostname else "",
                "listening": " ".join(bound),
                "loopback": loop.get("error") or loop.get("status"),
                "container_ip": outer.get("status"),
            },
        )
        current.mark(
            measured=bound == [f"{address}:3000"]
            and loop.get("error") == "ECONNREFUSED"
            and admin_up(outer),
            result="컨테이너 주소에 묶였다",
        )
    with rounds.round("admin-standalone HOSTNAME=127.0.0.1") as current:
        name, _, page = admin("admin-standalone", env={"HOSTNAME": "127.0.0.1"})
        bound = listening(name)
        note("admin-standalone HOSTNAME=127.0.0.1", {"listening": " ".join(bound)})
        current.mark(
            measured=admin_up(page) and bound == ["127.0.0.1:3000"], result="루프백에 묶였다"
        )


def section_common_env(rounds: Rounds, _repeat: int) -> None:
    """HOSTNAME·PORT 환경 변수를 시작 래퍼가 어떻게 읽는지. 관리 화면(admin-full)으로 본다. 표지는
    진입 표지 줄에 찍힌 그 값과 /proc/net/tcp 의 듣는 소켓이다. HOSTNAME 회차는 이미지의 명령
    (--hostname 127.0.0.1 --port 3000)에 환경 변수를 더한 것이고, PORT 회차는 래퍼에 --hostname 도
    --port 도 주지 않는다. 위젯은 widget-time 이 듣는 소켓을 적고(진입 스크립트가 --hostname 을
    넘긴다), portal 은 portal 섹션이 본다."""
    with rounds.round("common-env 관리 화면 HOSTNAME=0.0.0.0") as current:
        name, text, page = admin("admin-full", env={"HOSTNAME": "0.0.0.0"})
        bound = listening(name)
        note("common-env HOSTNAME", {"listening": " ".join(bound)})
        current.mark(
            measured=admin_up(page) and "hostname_env=0.0.0.0" in text,
            result=f"{' '.join(bound)} 에 섰다",
        )
    with rounds.round("common-env 관리 화면 --port 없이 PORT=3005") as current:
        name, text, page = admin(
            "admin-full",
            env={"PORT": "3005"},
            url="http://127.0.0.1:3005/",
            command=("node", "tools/start.ts", "start"),
        )
        bound = listening(name)
        note("common-env PORT", {"listening": " ".join(bound)})
        current.mark(
            measured=admin_up(page) and "port_env=3005" in text,
            result=f"{' '.join(bound)} 에 섰다",
        )


def section_common_health(rounds: Rounds, _repeat: int) -> None:
    """상태 확인 명령 후보(node -e 의 fetch)가 정상과 비정상을 가르는지. 관리 화면에 / 를 거는 것과
    듣지 않는 포트에 거는 것(대조)을 같은 이미지로 띄워 Docker 의 Health 상태가 healthy 와 unhealthy
    로 갈리는지 본다. 표지는 그 상태와, 그 컨테이너의 / 가 실제로 200 인 것이다. 확인 한 번의 걸린
    시간은 Health 기록의 Start·End 다. 위젯은 widget-time, portal 은 portal 섹션이 본다."""
    for label, url, want in (
        ("관리 화면 /", ADMIN_URL, "healthy"),
        ("관리 화면 듣지 않는 포트(대조)", "http://127.0.0.1:3999/", "unhealthy"),
    ):
        with rounds.round(f"common-health {label}") as current:
            name, _, page = admin("admin-full", *health_options(url, start_period="0s", retries=2))
            seen = wait_health(name, want, timeout=60)
            note(f"common-health {label}", dict(seen))
            current.mark(
                measured=admin_up(page) and seen.get("status") == want, result=str(seen["status"])
            )
            docker("rm", "-f", name, timeout=60)


def section_common_readonly(rounds: Rounds, _repeat: int) -> None:
    """읽기 전용 루트 파일 시스템(--read-only)에서 관리 화면이 서는지. 표지는 쓰기 시도가
    `Read-only file system` 으로 실패하는 것(양성 대조)과 첫 화면·/runs 의 200 이다. 위젯은
    widget-user, portal 은 portal 섹션이 본다."""
    for target, env in (
        ("admin-full", {}),
        ("admin-prod", {}),
        ("admin-standalone", {"HOSTNAME": "127.0.0.1"}),
    ):
        with rounds.round(f"common-readonly {target}") as current:
            name, _, page = admin(target, "--read-only", env=env)
            runs = fetch(name, "http://127.0.0.1:3000/runs")
            locked = read_only(name)
            note(f"common-readonly {target}", {"runs": runs.get("status"), "read_only": locked})
            current.mark(
                measured=locked and admin_up(page) and runs.get("status") == 200,
                result="읽기 전용으로 섰다",
            )
            docker("rm", "-f", name, timeout=60)


def section_common_stop(rounds: Rounds, repeat: int) -> None:
    """docker stop -t 10 의 걸린 시간과 종료 코드, --init 유무. 표지는 멈추기 전에 돌고 있었고(pid 1
    이 보였다) 멈춘 뒤 돌지 않는 것이다. 관리 화면 둘(next start, standalone 의 server.js)과 빌드
    중인 위젯을 본다. 서비스 중인 위젯은 widget-time, portal 은 portal 섹션이 본다. 빌드 중인 위젯은
    빌드가 시작되고 5초 뒤에 멈추고, 그때 아직 빌드가 끝나지 않았다는 것(build-exit 줄이 없다)을 더
    본다."""
    count = min(repeat, 2)
    for target, env in (("admin-full", {}), ("admin-standalone", {"HOSTNAME": "127.0.0.1"})):
        for init in ((), ("--init",)):
            for index in range(1 if init else count):
                label = f"common-stop {target} {'--init' if init else 'init 없음'} #{index + 1}"
                with rounds.round(label) as current:
                    name, _, page = admin(target, *init, env=env)
                    values = stop(name)
                    note(label, values)
                    current.mark(
                        measured=admin_up(page) and stopped_cleanly(values),
                        result=f"종료 코드 {values['exit_code']}",
                    )
    for init in ((), ("--init",)):
        label = f"common-stop 빌드 중인 위젯 {'--init' if init else 'init 없음'}"
        with rounds.round(label) as current:
            name = start(WIDGET, "--user", NODE_USER, *init, env=widget_env(), kind="w")
            until(name, ["RI_PROBE build-start"], timeout=60)
            time.sleep(5)
            building = "RI_PROBE build-exit" not in logs(name)
            values = stop(name)
            note(label, {**values, "building": building})
            current.mark(
                measured=building and stopped_cleanly(values),
                result=f"종료 코드 {values['exit_code']}",
            )


# ---------------------------------------------------------------------------------------------
# 위젯 미리보기 페이지(portal)

PORTAL_HEALTH = "http://127.0.0.1:3100/portal/health"


def section_portal(rounds: Rounds, repeat: int) -> None:
    """portal 을 띄우는 요건. portal-fixture.mjs 가 root 로 이름 붙은 볼륨에 설정·사이트 파일·개인
    키를 만든다(키는 0600, root 소유).
    - root 의 키를 uid 1000 이 읽는다: 표지는 `portal.private_key: 읽지 못한다` 와 0 아닌 종료.
    - 키를 uid 1000 소유로 바꾼 뒤 --network none, --read-only, 볼륨 :ro, -e PORT=4555 -e
      HOSTNAME=0.0.0.0 으로 띄운다: 표지는 시작 줄(`에 섰다. 사이트 1개.`), /portal/health 의 200 과
      `"status":"ok"`, 네트워크 장치가 lo 뿐인 것, 쓰기가 `Read-only file system` 으로 실패하는 것.
      듣는 소켓(설정의 127.0.0.1:3100 인지)과 시작 시간, 상태 확인, docker stop 을 함께 적는다.
    - uid 1000 이 빈 새 볼륨에 tools/make-key.ts 로 키를 만든다: 표지는
      `개인 키를 쓰지 못했다(EACCES)`."""
    volume = fresh("v")
    docker("volume", "create", "--label", LABEL, volume, timeout=60)
    made = docker(
        "run", "--rm", "--label", LABEL, "-v", f"{volume}:/cfg", "--entrypoint", "node",
        image("portal-prod"), "/probe/portal-fixture.mjs", "/cfg", "3100",
    )  # fmt: skip
    with rounds.round("portal root 가 만든 키를 uid 1000 이 읽는다") as current:
        name = start("portal-prod", "--user", NODE_USER, "-v", f"{volume}:/cfg:ro", kind="p")
        found = finished(name, timeout=120)
        text = logs(name)
        raw(f"logs {name}", text)
        note(
            "portal root 키", {"fixture": tail(made.out, 1), "exit": as_int(found.get("ExitCode"))}
        )
        current.mark(
            measured="/cfg/keys/portal.pem=0:0:600" in made.out
            and "portal.private_key: 읽지 못한다" in text
            and as_int(found.get("ExitCode")) != 0,
            result="읽지 못해 멈췄다",
        )
    docker(
        "run", "--rm", "--label", LABEL, "-v", f"{volume}:/cfg", "--entrypoint", "chown",
        image("portal-prod"), "1000:1000", "/cfg/keys/portal.pem",
    )  # fmt: skip
    for index in range(min(repeat, 3)):
        label = f"portal 선다 #{index + 1}"
        init = ("--init",) if index == 1 else ()
        with rounds.round(label) as current:
            name = start(
                "portal-prod", "--user", NODE_USER, "--network", "none", "--read-only",
                "-v", f"{volume}:/cfg:ro", *init,
                *health_options(PORTAL_HEALTH, start_period="60s"),
                env={"PORT": "4555", "HOSTNAME": "0.0.0.0", "RI_PROBE_WAIT_URL": PORTAL_HEALTH},
                kind="p",
            )  # fmt: skip
            text = until(name, ["RI_PROBE first-ok"], timeout=120)
            answer = fetch(name, PORTAL_HEALTH, needles=['"status":"ok"'])
            bound = listening(name)
            devices = shell(name, "ls /sys/class/net").out.split()
            locked = read_only(name)
            memory = shell(name, "cat /sys/fs/cgroup/memory.current").out.strip()
            note(
                label,
                {
                    "total_s": round(first_ok(text) - started_at(name), 2)
                    if first_ok(text)
                    else None,
                    "listening": " ".join(bound),
                    "devices": " ".join(devices),
                    "memory_mib": round(int(memory) / 2**20) if memory.isdigit() else None,
                    "written": " ".join(written(name, "/app/web/apps/portal")),
                },
            )
            current.mark(
                measured="에 섰다. 사이트 1개." in text
                and answer.get("status") == 200
                and dig(answer, "needles", '"status":"ok"') is True
                and devices == ["lo"]
                and locked,
                result=f"{' '.join(bound)} 에 섰다",
            )
        with rounds.round(f"portal 상태 확인 #{index + 1}") as current:
            seen = wait_health(name, "healthy", timeout=60)
            note(f"portal 상태 확인 #{index + 1}", dict(seen))
            current.mark(
                measured=seen.get("status") == "healthy" and seen.get("last_exit") == 0,
                result="healthy",
            )
        with rounds.round(
            f"portal stop #{index + 1} {'--init' if init else 'init 없음'}"
        ) as current:
            values = stop(name)
            note(f"portal stop #{index + 1}", values)
            current.mark(
                measured=stopped_cleanly(values), result=f"종료 코드 {values['exit_code']}"
            )
    with rounds.round("portal uid 1000 이 새 볼륨에 키를 만든다") as current:
        keys = fresh("v")
        docker("volume", "create", "--label", LABEL, keys, timeout=60)
        done = docker(
            "run", "--rm", "--label", LABEL, "--user", NODE_USER, "-v", f"{keys}:/keys",
            "--entrypoint", "node", image("portal-prod"), "--disable-warning=ExperimentalWarning",
            "tools/make-key.ts", "--private-key", "/keys/portal.pem", "--kid", "probe-1",
        )  # fmt: skip
        note("portal make-key uid 1000", {"exit": done.code, "tail": tail(done.text, 2)})
        current.mark(
            measured="개인 키를 쓰지 못했다(EACCES)" in done.text and done.code != 0,
            result="EACCES 로 멈췄다",
        )


# ---------------------------------------------------------------------------------------------
# 위젯

WIDGET = "widget-lean-typegen"
APP = "/app/web/apps/widget"
LIMITS = {"2g": 2 * 2**30, "1g": 2**30, "768m": 768 * 2**20, "512m": 512 * 2**20}


@dataclass(frozen=True)
class Seen:
    """위젯 컨테이너 하나에서 본 것. served 는 첫 200 과 그 회차 사이트 파일의 표지를 본 것이다."""

    name: str
    text: str
    values: dict[str, Json]
    served: bool


def widget_env(site: str | None = SITE_A, *, telemetry: bool = False) -> dict[str, str]:
    env = {"RI_PROBE_WAIT_URL": WIDGET_URL}
    if site is not None:
        env["AGENT_OS_SITE_FILE"] = site
    if not telemetry:
        env["NEXT_TELEMETRY_DISABLED"] = "1"
    return env


def mid_build(name: str) -> dict[str, Json]:
    """빌드 중의 부하와 상태 확인. 확인이 몇 번 돌도록 빌드가 시작되고 6초 뒤에 본다."""
    time.sleep(6)
    seen = health(name)
    return {
        **{f"mid_{key}": value for key, value in load(name).items()},
        "mid_building": "RI_PROBE build-exit" not in logs(name),
        "mid_health_status": seen["status"],
        "mid_health_last_exit": seen["last_exit"],
    }


def widget_values(name: str, text: str) -> dict[str, Json]:
    """위젯 진입 스크립트의 RI_PROBE 줄과 Next 기록에서 시간과 메모리를 읽는다. 다시 띄운 컨테이너는
    마지막 실행의 값이다."""
    begin = started_at(name)
    build_start = stamp_of(text, "build-start", last=True)
    build_exit = stamp_of(text, "build-exit", last=True)
    exec_at = stamp_of(text, "start-exec", last=True)
    ok = first_ok(text, last=True)
    codes = re.findall(r"RI_PROBE build-exit code=(\d+)", text)
    peak = line_value(text, "memory.peak")
    kills = re.findall(r"\boom_kill (\d+)", line_value(text, "memory.events"))
    return {
        "build_exit": int(codes[-1]) if codes else None,
        "build_s": seconds(build_exit - build_start) if build_exit and build_start else None,
        "compile_s": duration(text, "Compiled successfully in"),
        "typescript_s": duration(text, "Finished TypeScript in"),
        "ready_s": duration(text, "Ready in"),
        "serve_s": round(ok - exec_at, 2) if ok and exec_at else None,
        "total_s": seconds(ok - begin) if ok and begin else None,
        "peak_mib": round(int(peak) / 2**20) if peak.isdigit() else None,
        "memory_max": line_value(text, "memory.max"),
        "oom_kill": int(kills[-1]) if kills else None,
    }


def widget(
    target: str,
    *options: str,
    env: Mapping[str, str],
    origin: str = ORIGIN_A,
    chars: str = CHARS_A,
    timeout: float = 900,
) -> Seen:
    """위젯 컨테이너를 띄워 빌드와 첫 200 을 기다리고 응답의 표지를 본다. 빌드가 시작되면 한 번
    mid_build 를 부른다. 컨테이너는 남긴다(부른 쪽이 멈추고, 남은 것은 sweep 이 지운다)."""
    name = start(target, *options, env=env, kind="w")
    early: dict[str, Json] = {}
    if "RI_PROBE build-start" in until(name, ["RI_PROBE build-start"], timeout=120):
        early = mid_build(name)
    text = until(name, ["RI_PROBE first-ok"], timeout=timeout)
    values = {**widget_values(name, text), **early}
    served = False
    if first_ok(text, last=True):
        page = fetch(name, WIDGET_URL)
        element = fetch(name, ELEMENT_URL, needles=[chars] if chars else [])
        csp = as_text(dig(page, "headers", "content-security-policy"))
        values["csp"] = csp
        served = (
            page.get("status") == 200
            and element.get("status") == 200
            and origin in csp
            and (not chars or dig(element, "needles", chars) is True)
        )
    return Seen(name, text, values, served)


def fresh_build(seen: Seen) -> bool:
    """앞 빌드 산출물 없이 빌드해 0 으로 끝났다."""
    return "RI_PROBE prior-build absent" in seen.text and seen.values.get("build_exit") == 0


def widget_round(
    rounds: Rounds,
    label: str,
    target: str,
    options: Sequence[str],
    *,
    follow: bool = True,
    expect: str = "",
) -> None:
    """위젯 빌드 회차 하나. follow 면 같은 컨테이너로 상태 확인과 docker stop 회차를 잇는다. expect
    는 그 갈래에서만 나와야 하는 기록의 글이다."""
    extra = health_options(WIDGET_URL) if follow else []
    # 회차가 예외로 끝나면 Rounds 가 삼켜 seen 이 비고, 뒤 회차를 잇지 않는다.
    kept: list[Seen] = []
    with rounds.round(f"widget-time {label}") as current:
        first = widget(target, "--user", NODE_USER, *options, *extra, env=widget_env())
        kept.append(first)
        note(f"widget-time {label}", {**first.values, "listening": " ".join(listening(first.name))})
        current.mark(
            measured=first.served and fresh_build(first) and (not expect or expect in first.text),
            result="빌드하고 섰다",
        )
    if not kept or not kept[0].served:
        return
    seen = kept[0]
    if follow:
        with rounds.round(f"widget-health {label}") as current:
            after = wait_health(seen.name, "healthy", timeout=60)
            note(f"widget-health {label}", dict(after))
            during = (
                seen.values.get("mid_building") is True
                and seen.values.get("mid_health_status") == "starting"
                and seen.values.get("mid_health_last_exit") == 1
            )
            current.mark(
                measured=during and after.get("status") == "healthy" and after["last_exit"] == 0,
                result="빌드 중에는 1, 선 뒤에는 0",
            )
        with rounds.round(f"widget-stop {label}") as current:
            values = stop(seen.name)
            note(f"widget-stop {label}", values)
            current.mark(
                measured=stopped_cleanly(values), result=f"종료 코드 {values['exit_code']}"
            )
    docker("rm", "-f", seen.name, timeout=60)


def section_widget_time(rounds: Rounds, repeat: int) -> None:
    """위젯 컨테이너가 뜰 때 하는 빌드의 시간과 메모리(widget-lean-typegen, uid 1000). 표지는 앞
    빌드 산출물 없이(prior-build absent) 빌드가 0 으로 끝나고, 첫 200 을 받고, 응답의 CSP 에 사이트
    파일 A 의 허용 출처가, element.js 에 A 의 request_chars(771133)가 실린 것이다. 같은 컨테이너로
    상태 확인 명령(빌드 중에는 1, 선 뒤에는 0 인지)과 docker stop(좀비 수 포함)을 잇는다. --init 한
    갈래, --cpus 2 한 갈래, 타입 검사를 건너뛴 판(widget-lean-notc) 두 갈래를 더한다. notc 의 표지는
    Next 가 타입 검사를 건너뛴다고 찍은 줄이다."""
    for index in range(repeat):
        widget_round(rounds, f"#{index + 1}", WIDGET, ())
    widget_round(rounds, "--init", WIDGET, ("--init",))
    widget_round(rounds, "--cpus 2", WIDGET, ("--cpus", "2"), follow=False)
    for index in range(2):
        widget_round(
            rounds,
            f"notc #{index + 1}",
            "widget-lean-notc",
            (),
            follow=False,
            expect="Skipping validation of types",
        )


def section_widget_memory(rounds: Rounds, _repeat: int) -> None:
    """--memory 제한 단계(스왑 없이 --memory-swap 을 같게). 제한마다 한 번. 표지는 cgroup 의
    memory.max 가 준 제한과 같은 것에 더해, 성공이면 widget-time 과 같은 응답의 표지, 실패면
    memory.events 의 oom_kill 이 1 이상인 것이다. 둘 다 아니면 측정이 아니다."""
    for limit, size in LIMITS.items():
        with rounds.round(f"widget-memory {limit}") as current:
            seen = widget(
                WIDGET, "--user", NODE_USER, "--memory", limit, "--memory-swap", limit,
                env=widget_env(), timeout=420,
            )  # fmt: skip
            oom_killed = state(seen.name).get("OOMKilled") is True
            killed = as_int(seen.values.get("oom_kill")) > 0 or oom_killed
            note(
                f"widget-memory {limit}",
                {
                    **seen.values,
                    "state_oom_killed": oom_killed,
                    "tail": "" if seen.served else tail(seen.text, 4),
                },
            )
            limited = seen.values.get("memory_max") == str(size)
            current.mark(
                measured=limited and ((seen.served and fresh_build(seen)) or killed),
                result="빌드하고 섰다" if seen.served else "OOM 으로 빌드가 죽었다",
            )
            docker("rm", "-f", seen.name, timeout=60)


NETCHECK = (
    "const s=require('net').connect({host:'1.1.1.1',port:443,timeout:4000});"
    "s.on('connect',()=>{console.log('RI_NET open');process.exit(0)});"
    "s.on('timeout',()=>{console.log('RI_NET timeout');process.exit(0)});"
    "s.on('error',(e)=>{console.log('RI_NET closed '+e.code);process.exit(0)})"
)


def outside(name: str) -> str:
    """컨테이너 안에서 바깥(1.1.1.1:443)에 TCP 를 열어 본다. open, timeout, closed <코드>."""
    found = re.search(r"RI_NET (.+)", docker("exec", name, "node", "-e", NETCHECK, timeout=60).out)
    return found[1].strip() if found else ""


TELEMETRY_NOTICE = "Attention: Next.js now collects completely anonymous telemetry"


def section_widget_network(rounds: Rounds, _repeat: int) -> None:
    """--network none 에서 빌드하고 서는지. 먼저 바탕 이미지를 기본 브리지와 none 으로 띄워 바깥
    연결 시험이 open 과 closed 를 가르는지 본다(양성 대조). 빌드 회차의 표지는 네트워크 장치가 lo
    뿐이고 바깥 연결이 닫혔으며 widget-time 과 같은 응답의 표지를 본 것, 그리고 텔레메트리 안내
    줄(Attention: ...)이 켠 갈래에만 찍힌 것이다. 컨테이너 안의 `next telemetry status` 는 켠 빌드
    뒤에도 Disabled 를 답해 (손으로 봤다) 표지로 쓰지 않는다."""
    for network in ("bridge", "none"):
        with rounds.round(f"widget-network 대조 {network}") as current:
            name = start("base", "--network", network, command=("sleep", "120"), kind="n")
            seen = outside(name)
            note(f"widget-network 대조 {network}", {"outside": seen})
            expected = "open" if network == "bridge" else "closed"
            current.mark(measured=seen.startswith(expected), result=seen)
            docker("rm", "-f", name, timeout=60)
    for label, telemetry in (("끔 #1", False), ("끔 #2", False), ("켬", True)):
        with rounds.round(f"widget-network none 텔레메트리 {label}") as current:
            seen = widget(
                WIDGET,
                "--user",
                NODE_USER,
                "--network",
                "none",
                env=widget_env(telemetry=telemetry),
            )
            devices = shell(seen.name, "ls /sys/class/net").out.split()
            closed = outside(seen.name)
            notice = TELEMETRY_NOTICE in seen.text
            note(
                f"widget-network none 텔레메트리 {label}",
                {
                    **seen.values,
                    "devices": " ".join(devices),
                    "outside": closed,
                    "telemetry_notice": notice,
                    "written_outside_app": " ".join(
                        item for item in written(seen.name, APP) if not item.startswith("<app>")
                    ),
                },
            )
            isolated = devices == ["lo"] and closed.startswith("closed")
            current.mark(
                measured=seen.served and fresh_build(seen) and isolated and notice == telemetry,
                result="빌드하고 섰다",
            )
            docker("rm", "-f", seen.name, timeout=60)


def exits(target: str, *options: str, env: Mapping[str, str]) -> tuple[str, dict[str, Json]]:
    """끝날 것으로 기대하는 컨테이너를 띄우고 끝날 때까지 기다린다. (기록, State)."""
    name = start(target, *options, env=env, kind="x")
    found = finished(name, timeout=240)
    text = logs(name)
    raw(f"logs {name}", text)
    return text, found


def section_widget_user(rounds: Rounds, _repeat: int) -> None:
    """root 아닌 사용자로 빌드할 때 쓰는 자리.
    - root 로 띄워 docker diff 로 쓰는 자리를 모은다. 표지는 widget-time 과 같은 응답의 표지와, 바뀐
      자리에 .next 와 public/element.js 가 든 것이다.
    - 쓰는 자리를 만들지 않은 root 소유 나무(widget-full)를 uid 1000 으로: 표지는 public/fonts 를
      만들지 못한 EACCES 문구.
    - widget-lean-typegen(.next 와 public 이 uid 1000 소유)을 다른 uid(12345)로: 표지는 EACCES 문구.
    - widget-lean-typegen 을 uid 1000, --read-only 로, .next 와 public 만 uid 1000 의 tmpfs 로 준다.
      표지는 쓰기 시도가 `Read-only file system` 으로 실패하는 것과 widget-time 과 같은 응답의
      표지다."""
    with rounds.round("widget-user root 가 쓰는 자리") as current:
        seen = widget(WIDGET, "--user", "0:0", env=widget_env())
        places = written(seen.name, APP)
        note("widget-user root", {"written": " ".join(places)})
        current.mark(
            measured=seen.served
            and fresh_build(seen)
            and "<app>/.next" in places
            and "<app>/public/element.js" in places,
            result="빌드하고 섰다",
        )
        docker("rm", "-f", seen.name, timeout=60)
    denied = "EACCES: permission denied, mkdir '/app/web/apps/widget/public/fonts'"
    for label, target, user, needle in (
        ("root 소유 나무를 uid 1000 으로", "widget-full", NODE_USER, denied),
        ("uid 1000 소유 자리를 uid 12345 로", WIDGET, "12345:12345", "EACCES: permission denied"),
    ):
        with rounds.round(f"widget-user {label}") as current:
            text, found = exits(target, "--user", user, env=widget_env())
            line = next((item for item in text.splitlines() if "EACCES" in item), "")
            note(
                f"widget-user {label}",
                {
                    "exit": as_int(found.get("ExitCode")),
                    "lifetime_s": lifetime(found),
                    "line": line,
                },
            )
            current.mark(
                measured=needle in text and as_int(found.get("ExitCode")) != 0,
                result="EACCES 로 멈췄다",
            )
    with rounds.round("widget-user --read-only 와 .next·public tmpfs") as current:
        seen = widget(
            WIDGET, "--user", NODE_USER, "--read-only",
            "--tmpfs", f"{APP}/.next:uid=1000,gid=1000",
            "--tmpfs", f"{APP}/public:uid=1000,gid=1000",
            env=widget_env(),
        )  # fmt: skip
        locked = read_only(seen.name)
        note(
            "widget-user --read-only",
            {**seen.values, "read_only": locked, "tail": "" if seen.served else tail(seen.text, 4)},
        )
        current.mark(measured=locked and seen.served and fresh_build(seen), result="빌드하고 섰다")
        docker("rm", "-f", seen.name, timeout=60)


def section_widget_sitefile(rounds: Rounds, _repeat: int) -> None:
    """사이트 파일이 없거나 깨졌을 때(uid 1000). 실패를 기대하는 회차의 표지는 그 경우에서만 나오는
    진단 문구와 0 아닌 종료다. 읽을 수 없는 파일은 root 소유 0600 사본을 이름 붙은 볼륨에 둔다.
    변수를 주지 않은 회차는 실패하지 않고 서는지를 보며, 표지는 CSP 가 frame-ancestors 'none' 인
    것이다."""
    volume = fresh("v")
    docker("volume", "create", "--label", LABEL, volume, timeout=60)
    docker(
        "run", "--rm", "--label", LABEL, "-v", f"{volume}:/cfg", "--entrypoint", "sh",
        image(WIDGET), "-c", "cp /probe/sites_a.toml /cfg/sites.toml && chmod 0600 /cfg/sites.toml",
    )  # fmt: skip
    cases: tuple[tuple[str, str, tuple[str, ...], tuple[str, ...]], ...] = (
        (
            "없는 파일",
            "/probe/none.toml",
            (),
            ("/probe/none.toml 을 받아들일 수 없다", "파일이 없다"),
        ),
        ("빈 값", "", (), ("AGENT_OS_SITE_FILE 가 비었다",)),
        ("디렉터리", "/probe", (), ("/probe 을 받아들일 수 없다", "EISDIR")),
        (
            "깨진 파일",
            "/probe/sites_broken.toml",
            (),
            ("sites[0].unknown_probe_key: 모르는 키다", "sites[0].issuer: 빠졌다"),
        ),
        (
            "읽을 수 없는 파일",
            "/cfg/sites.toml",
            ("-v", f"{volume}:/cfg:ro"),
            ("/cfg/sites.toml 을 받아들일 수 없다", "EACCES"),
        ),
    )
    for label, path, options, needles in cases:
        with rounds.round(f"widget-sitefile {label}") as current:
            text, found = exits(WIDGET, "--user", NODE_USER, *options, env=widget_env(site=path))
            lines = [item.strip() for item in text.splitlines() if any(n in item for n in needles)]
            note(
                f"widget-sitefile {label}",
                {
                    "exit": as_int(found.get("ExitCode")),
                    "lifetime_s": lifetime(found),
                    "lines": " / ".join(lines),
                },
            )
            current.mark(
                measured=all(needle in text for needle in needles)
                and as_int(found.get("ExitCode")) != 0,
                result=f"종료 코드 {as_int(found.get('ExitCode'))}로 멈췄다",
            )
    with rounds.round("widget-sitefile 변수 없음") as current:
        seen = widget(
            WIDGET, "--user", NODE_USER, env=widget_env(site=None), origin="'none'", chars=""
        )
        note("widget-sitefile 변수 없음", {"csp": seen.values.get("csp")})
        current.mark(
            measured=seen.served and seen.values.get("csp") == "frame-ancestors 'none'",
            result="frame-ancestors 'none' 으로 섰다",
        )
        docker("rm", "-f", seen.name, timeout=60)


def section_zombie(rounds: Rounds, repeat: int) -> None:
    """init 없이 뜬 pid 1 이 고아를 거두는지. 서비스가 선 뒤 5초를 두고 /proc 에서 좀비(Z)와 그
    부모를 센다. 다른 섹션이 컨테이너 안에서 첫 200 을 기다리는 wait.mjs 는 진입 스크립트의
    자식이라, 진입이 exec 로 서비스로 갈아탄 뒤 wait.mjs 가 끝나면 그 서비스의 자식 좀비가 된다(그
    섹션들의 좀비 수에 든다). 그래서 이 섹션은 wait.mjs 없이 띄우고 바깥에서 docker exec 로 첫 200
    을 기다린다. 관리 화면을 wait.mjs 와 함께 띄운 갈래가 양성 대조다(센 값이 좀비 하나를 잡아야
    한다). 갈래마다 repeat 번. 표지는 서비스의 200 과 /proc 목록에서 pid 1 을 본 것이다."""
    branches = (
        ("관리 화면 wait.mjs 와 함께(대조)", "admin", (), True),
        ("관리 화면", "admin", (), False),
        ("위젯", "widget", (), False),
        ("위젯 --init", "widget", ("--init",), False),
    )
    for index in range(repeat):
        for label, kind, init, waiter in branches:
            zombie_round(rounds, f"{label} #{index + 1}", kind, init, waiter=waiter)


def zombie_round(
    rounds: Rounds, label: str, kind: str, init: Sequence[str], *, waiter: bool
) -> None:
    """zombie 섹션의 회차 하나."""
    with rounds.round(f"zombie {label}") as current:
        if kind == "admin":
            name, _, page = admin("admin-full", *init, waiter=waiter)
            up = admin_up(page)
        else:
            env = {key: value for key, value in widget_env().items() if key != "RI_PROBE_WAIT_URL"}
            name = start(WIDGET, "--user", NODE_USER, *init, env=env, kind="z")
            until(name, ["RI_PROBE start-exec"], timeout=900)
            up = serving(name, WIDGET_URL, timeout=120).get("status") == 200
        time.sleep(5)
        found = processes(name)
        pid1 = next((comm for pid, _, _, comm in found if pid == 1), "")
        zombies = [item for item in found if item[2] == "Z"]
        note(
            f"zombie {label}",
            {"pid1": pid1, "zombies": len(zombies), "zombie_list": zombie_list(found)},
        )
        current.mark(measured=up and pid1 != "", result=f"좀비 {len(zombies)}")
        docker("rm", "-f", name, timeout=60)


def section_widget_reflect(rounds: Rounds, _repeat: int) -> None:
    """사이트 파일을 바꾸고 같은 컨테이너를 다시 띄우면(docker restart) 반영되는지. 이름 붙은 볼륨에
    A 를 두고 띄운 뒤 볼륨의 파일을 B 로 바꿔 restart 한다. 표지는 처음 실행이 A 의 표지를, 다시
    띄운 실행이 B 의 표지(허용 출처, request_chars 583927)를 내고 A 의 request_chars(771133)는 내지
    않는 것이다. 다시 띄울 때 앞 빌드 산출물이 남았는지(prior-build present)와 두 번째 빌드 시간을
    적는다."""
    volume = fresh("v")
    docker("volume", "create", "--label", LABEL, volume, timeout=60)
    copy = ("run", "--rm", "--label", LABEL, "-v", f"{volume}:/cfg", "--entrypoint", "sh")
    script = "cp /probe/{0} /cfg/sites.toml && chmod 0644 /cfg/sites.toml"
    docker(*copy, image(WIDGET), "-c", script.format("sites_a.toml"))
    # 회차가 예외로 끝나면 Rounds 가 삼켜 kept 가 비고, 다시 띄우는 회차를 잇지 않는다.
    kept: list[Seen] = []
    with rounds.round("widget-reflect 처음(A)") as current:
        first = widget(
            WIDGET, "--user", NODE_USER, "-v", f"{volume}:/cfg:ro",
            env=widget_env(site="/cfg/sites.toml"),
        )  # fmt: skip
        kept.append(first)
        note("widget-reflect 처음", first.values)
        current.mark(measured=first.served and fresh_build(first), result="A 로 섰다")
    if not kept or not kept[0].served:
        return
    seen = kept[0]
    with rounds.round("widget-reflect 파일을 B 로 바꾸고 restart") as current:
        docker(*copy, image(WIDGET), "-c", script.format("sites_b.toml"))
        docker("restart", "-t", "10", seen.name, timeout=120)
        text = until(seen.name, ["RI_PROBE first-ok"], timeout=900, count=2)
        page = fetch(seen.name, WIDGET_URL)
        element = fetch(seen.name, ELEMENT_URL, needles=[CHARS_B, CHARS_A])
        csp = as_text(dig(page, "headers", "content-security-policy"))
        present = "RI_PROBE prior-build present" in text
        note(
            "widget-reflect restart",
            {**widget_values(seen.name, text), "csp": csp, "prior_build_present": present},
        )
        current.mark(
            measured=text.count("RI_PROBE first-ok") >= 2
            and ORIGIN_B in csp
            and dig(element, "needles", CHARS_B) is True
            and dig(element, "needles", CHARS_A) is False,
            result="B 로 다시 빌드하고 섰다",
        )


# ---------------------------------------------------------------------------------------------

SECTIONS: dict[str, Callable[[Rounds, int], None]] = {
    "build": section_build,
    "admin-time": section_admin_time,
    "admin-reject": section_admin_reject,
    "admin-upstream": section_admin_upstream,
    "admin-standalone": section_admin_standalone,
    "common-env": section_common_env,
    "common-health": section_common_health,
    "common-readonly": section_common_readonly,
    "common-stop": section_common_stop,
    "portal": section_portal,
    "widget-time": section_widget_time,
    "widget-memory": section_widget_memory,
    "widget-network": section_widget_network,
    "widget-user": section_widget_user,
    "widget-sitefile": section_widget_sitefile,
    "widget-reflect": section_widget_reflect,
    "zombie": section_zombie,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sections", default="build")
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--work", type=Path, default=None)
    args = parser.parse_args()
    names = [name.strip() for name in str(args.sections).split(",") if name.strip()]
    unknown = [name for name in names if name not in SECTIONS]
    if unknown:
        print(f"모르는 섹션: {unknown}. 아는 섹션: {', '.join(SECTIONS)}")
        return 2
    work = args.work or Path(tempfile.mkdtemp(prefix="ri-web-images-"))
    work.mkdir(parents=True, exist_ok=True)
    _work.append(work)
    print(f"원본 출력: {work}", flush=True)
    sweep()
    rounds = Rounds()
    try:
        for name in names:
            print(f"== {name}", flush=True)
            before = len(rounds.entries)
            SECTIONS[name](rounds, int(args.rounds))
            for entry in rounds.entries[before:]:
                flag = "측정" if entry.measured else "측정 아님"
                print(f"  [{flag}] {entry.label}: {entry.result}", flush=True)
    finally:
        sweep()
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    sys.exit(main())
