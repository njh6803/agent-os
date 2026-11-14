"""release-image serve 이미지 프로브. 명세가 정할 `serve` 컨테이너 이미지의 모양을 본다.

결정하지 않고 본 것만 낸다. 회차마다 재려는 상황이 그 회차에 났다는 표지를 보고
`tools/probe_kit.py` 의 `Rounds` 로 센다. 표지 없는 회차가 하나라도 있으면 종료 코드가 1 이다.
컨테이너 안의 일은 같은 폴더의 `inside.py` 를 `python -` 의 표준 입력으로 넘겨 하고, 그 마지막 줄
`RESULT <json>` 을 읽는다.

항목(`--items 1,4` 로 고른다). 결과의 뜻은 README 의 결과 절이 적는다.
  1 판 번호. Dockerfile.version 의 타깃을 마지막 단계만 캐시를 버려 짓는다. 성공을 기대한 갈래의
    표지는 uv 의 설치 줄(`+ agent-os==`)의 판이 넘긴 판의 정규화 꼴인 것과 빌드 기록의 고친 줄(동적
    판 갈래는 다시 잠그기 줄)이고, 실패를 기대한 갈래의 표지는 오류 문구다. 지은 이미지에서 판이
    보이는 자리 넷을 읽고, 몇 갈래는 serve 를 띄워 `/openapi.json` 의 `info.version` 을 읽는다.
  2 바탕 후보 셋(`Dockerfile` 의 deb-py, deb-node, alpine). `--no-cache` 로 지은 시간과 크기와 짓기
    직전의 부하. 표지는 빌드 기록의 `naming to` 줄이다. 지은 이미지마다 판, serve 의 `/health`, 실행
    파일 이름으로 띄운 MCP 서버의 `initialize` 답, 판을 넣는 sed 의 `0,/re/` 주소가 그 바탕에서
    듣는지를 본다(`--builds 0` 이면 짓지 않고 지어 둔 이미지만 본다).
  3 사용자. 이미지의 사용자, passwd 항목이 없는 uid, 그 uid 에 USER 를 준 것으로 serve 를 띄운다.
    표지는 섰으면 실행의 `run_started.principal`, 서지 못했으면 로그의 `getpwuid()` 줄이다.
  4 예시 MCP 서버. `--network none` 에서 npx 의 꼴들과 실행 파일 이름으로 `initialize` 를 보낸다.
    네트워크가 없다는 표지는 레지스트리에 TCP 로 닿지 않는 것, 답의 표지는 serverInfo 다. 네트워크가
    있을 때 npm 의 http 기록에 패키지 조회가 찍히는지와, 실제 serve 에서 지금 매니페스트와 실행 파일
    이름의 매니페스트로 실행 하나씩을 본다.
  5 쓰는 자리. 호스트 엔진에서 흐름 하나를 돈 뒤 `docker diff` 로 이미지 밖에 쓴 자리를 모으고, 같은
    흐름을 `--read-only` 로 다시 돈다. 바이트코드를 미리 만들지 않은 이미지와 시제품(uid 10001,
    root)에서 `agent-os --version` 이 새로 쓰는 `__pycache__` 를 센다. Docker-in-Docker(리눅스
    엔진)에서 다른 uid 가 가진 폴더의 바인드 마운트와 그 대조군으로 끄기(`disabled.toml`)와
    실행(트레이스)을 해 본다.
  6 첫 채움(Docker-in-Docker). 빈 이름 있는 볼륨과 root 소유로 바꾼 이미지의 대조군, 빈 바인드
    마운트, 내용이 있는 볼륨에 다음 판 이미지와 그 양성 대조(빈 볼륨에 다음 판 이미지).
  7 init 과 종료. tini, `docker run --init`, init 없음, 셸 감싸기(대조군)를 견준다. 표지는 pid 1 의
    명령줄이다. MCP 실행 뒤의 좀비 수, 고아 프로세스가 거둬지는지, `docker stop` 의 시간과 종료
    코드. 끝으로 SIGTERM 처리기가 없는 pid 1 에 `docker stop`(`-t` 없음과 `-t 10`)을 걸어 엔진이
    SIGKILL 까지 기다리는 시간을 본다.
  8 상태 확인. serve 가 127.0.0.1 에 묶인 채 한 줄 명령이 정상(포트 8000)과 비정상(8001)을
    가르는지와 `--health-cmd` 가 healthy·unhealthy 에 닿는 시간.

자원. 만드는 것의 이름은 `ri-serve-` 로 시작한다. 컨테이너와 볼륨은 실행마다 `ri-serve-<토큰>-` 이고
끝에서(예외가 나도) 그 접두로 찾아 지운다. Docker-in-Docker 안의 것은 그 컨테이너와 익명 볼륨을
지우면 함께 없어진다. 이미지는 남긴다. 호스트 포트는 쓰지 않는다(요청은 컨테이너 안에서 한다).
관리·채널 토큰은 실행마다 무작위이고 명령줄과 원본 기록에 값을 싣지 않는다(`-e 이름` 으로 넘긴다).

못 보는 것.
- 레지스트리에서 받는 시간과 압축된 크기. 빌드는 받아 둔 바탕 이미지로 하고 크기는 엔진의 풀린
  크기다.
- 다른 측정 세션이 같은 데몬을 쓴다. 시간은 범위로 읽고 그때의 부하를 함께 낸다.
- Docker Desktop 의 윈도 폴더 바인드 마운트. 리눅스의 소유권은 Docker-in-Docker 로 본다.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import time
from collections import Counter
from collections.abc import Generator, Sequence
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds, Slot  # noqa: E402

INSIDE = (HERE / "inside.py").read_text(encoding="utf-8")
PY = "/app/.venv/bin/python"
ADMIN = "AGENT_OS_ADMIN_TOKEN"
CHANNEL = "AGENT_OS_CHANNEL_TOKEN"
PACKAGE = "@modelcontextprotocol/server-everything"
PINNED = f"{PACKAGE}@2.3.0"
RC = "0.1.0-rc.1"
# 2026-11-13 이 PC 에 이미 있던 이미지다(다른 측정 세션이 받았다).
DIND_IMAGE = "docker:29.9.2-dind"
PROTO = "ri-serve-proto"
LOCAL = "ri-serve-proto-local"
ROOTOWNED = "ri-serve-proto-rootowned"
V2 = "ri-serve-proto-v2"
DERIVED = {LOCAL: "local-npm", ROOTOWNED: "rootowned", V2: "plugins-v2"}
MANIFEST = "/app/plugins/mcp/everything/plugin.toml"
SERVE = (
    "agent-os",
    "serve",
    "--plugins-root",
    "/app/plugins",
    "--traces",
    "/data/traces",
    "--model",
    "claude-opus-5",
)
DIRECT = ("mcp-server-everything", "[]")
LOCK_ERROR = "needs to be updated, but `--locked` was provided"
UNSET_ERROR = "environment variable `AGENT_OS_VERSION` is not set"
EDIT_LINE = re.compile(r'\d+:version = "([^"]*)"')
LOCK_LINE = re.compile(r'\d+-version = "([^"]*)"')
INSTALL_LINE = re.compile(r"\+ agent-os==(\S+)")
REVISION_LINE = re.compile(r"([<>]) revision = (\d+)")
FETCH_LINE = re.compile(r"GET (\d+) https://registry\.npmjs\.org(\S*)(?: \d+ms)?(?: \(([^)]*)\))?")
HEALTH_PY = (
    "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen("
    "'http://127.0.0.1:{port}/health', timeout=4).status == 200 else 1)"
)
HEALTH_NODE = (
    "fetch('http://127.0.0.1:{port}/health')"
    ".then(r => process.exit(r.ok ? 0 : 1), () => process.exit(1))"
)

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None

_raw: list[Path] = []


def raw(title: str, text: str) -> None:
    if _raw:
        with _raw[0].open("a", encoding="utf-8") as out:
            out.write(f"\n===== {time.strftime('%H:%M:%S')} {title}\n{text}\n")


def parse(text: str) -> Json:
    try:
        parsed: Json = json.loads(text)
    except ValueError:
        return None
    return parsed


def as_list(value: Json) -> list[Json]:
    return value if isinstance(value, list) else []


def as_text(value: Json) -> str:
    return value if isinstance(value, str) else ""


def dig(value: Json, *keys: str) -> Json:
    for key in keys:
        value = value.get(key) if isinstance(value, dict) else None
    return value


def tail(text: str, count: int = 2) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " / ".join(lines[-count:])[:300]


def line_with(text: str, phrase: str) -> str:
    """phrase 가 든 첫 줄. BuildKit 의 줄 머리(`#15 0.31 `)는 뗀다."""
    for line in text.splitlines():
        if phrase in line:
            return re.sub(r"^#\d+ [\d.]+ ", "", line.strip())[:240]
    return ""


@dataclass(frozen=True)
class Done:
    code: int
    out: str
    err: str
    seconds: float

    @property
    def text(self) -> str:
        return f"{self.out}\n{self.err}"


def run(argv: Sequence[str], *, stdin: str | None = None, timeout: float = 240) -> Done:
    """명령 하나. 표준 입력은 늘 닫힌 파이프다. 시간을 넘기면 종료 코드 -1 이다."""
    started = time.monotonic()
    try:
        completed = subprocess.run(
            list(argv),
            input=stdin or "",
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        done = Done(
            -1, "", f"{timeout:.0f}초 안에 끝나지 않았다", round(time.monotonic() - started, 2)
        )
    else:
        seconds = round(time.monotonic() - started, 2)
        done = Done(completed.returncode, completed.stdout, completed.stderr, seconds)
    head = f"exit={done.code} seconds={done.seconds}"
    raw(" ".join(argv), f"{head}\n--- stdout\n{done.out}\n--- stderr\n{done.err}")
    return done


@dataclass(frozen=True)
class Docker:
    """docker 명령의 앞부분. 호스트 엔진은 `docker`, Docker-in-Docker 는 그 안의 `docker` 다."""

    prefix: tuple[str, ...]

    def __call__(self, *args: str, stdin: str | None = None, timeout: float = 240) -> Done:
        return run([*self.prefix, *args], stdin=stdin, timeout=timeout)


HOST = Docker(("docker",))


@dataclass
class Context:
    token: str
    rounds: Rounds
    serial: int = 0

    def name(self, label: str) -> str:
        self.serial += 1
        return f"ri-serve-{self.token}-{label}-{self.serial}"


@contextmanager
def case(ctx: Context, label: str) -> Generator[Slot]:
    """회차 하나를 세고 끝나면 한 줄로 낸다."""
    with ctx.rounds.round(label) as slot:
        yield slot
    entry = ctx.rounds.entries[-1]
    verdict = "측정" if entry.measured else "측정 아님"
    print(f"- [{verdict}] {entry.label} => {entry.result}", flush=True)


def result_of(done: Done) -> Json:
    for line in reversed(done.out.splitlines()):
        if line.startswith("RESULT "):
            return parse(line.removeprefix("RESULT "))
    return None


def helper(docker: Docker, container: str, *args: str, timeout: float = 120) -> Json:
    """도는 컨테이너 안에서 inside.py 명령 하나."""
    done = docker("exec", "-i", container, PY, "-", *args, stdin=INSIDE, timeout=timeout)
    return result_of(done)


def helper_once(
    docker: Docker, name: str, image: str, options: Sequence[str], *args: str, timeout: float = 180
) -> Json:
    """새 컨테이너 하나에서 inside.py 명령 하나. 끝나면 지워진다(`--rm`)."""
    argv = ["run", "--rm", "-i", "--name", name, *options, "--entrypoint", PY, image, "-", *args]
    return result_of(docker(*argv, stdin=INSIDE, timeout=timeout))


@dataclass(frozen=True)
class Serve:
    """띄운 serve 하나. state 는 ready(`/health` 200), exited, timeout, not-created 가운데 하나."""

    docker: Docker
    name: str
    state: str
    ready: float | None
    logs: str


def serve(
    ctx: Context,
    docker: Docker,
    label: str,
    image: str,
    options: Sequence[str] = (),
    command: Sequence[str] = SERVE,
    *,
    wait: float = 60,
) -> Serve:
    """serve 를 띄우고 `/health` 가 200 이 되거나 컨테이너가 끝나거나 wait 초가 지날 때까지 본다.
    ready 는 `docker run -d` 가 돌아온 뒤 첫 200 까지의 초다(엿보는 간격이 0.5초 남짓이다)."""
    name = ctx.name(label)
    head = ("run", "-d", "--name", name, "-e", ADMIN, "-e", CHANNEL)
    started = docker(*head, *options, image, *command)
    if started.code != 0:
        return Serve(docker, name, "not-created", None, started.err.strip())
    begin = time.monotonic()
    while time.monotonic() - begin < wait:
        reply = helper(docker, name, "http", "GET", "/health", "-", "-", timeout=30)
        if dig(reply, "status") == 200:
            return Serve(docker, name, "ready", round(time.monotonic() - begin, 1), "")
        if docker("inspect", "-f", "{{.State.Running}}", name).out.strip() != "true":
            return Serve(docker, name, "exited", None, logs_of(docker, name))
        time.sleep(0.5)
    return Serve(docker, name, "timeout", None, logs_of(docker, name))


def logs_of(docker: Docker, name: str) -> str:
    done = docker("logs", "--tail", "80", name)
    return f"{done.out}\n{done.err}".strip()


def exit_code_of(docker: Docker, name: str) -> str:
    return docker("inspect", "-f", "{{.State.ExitCode}}", name).out.strip()


def remove(docker: Docker, *names: str) -> None:
    docker("rm", "-f", "-v", *names)


@dataclass(frozen=True)
class Outcome:
    status: Json
    types: list[str]
    principal: str
    cause: str
    error: str
    seconds: Json

    @property
    def failed(self) -> bool:
        return "run_failed" in self.types

    def brief(self) -> str:
        kinds = "·".join(self.types) or f"이벤트 없음(상태 {self.status})"
        cause = f", 원인 {self.cause}" if self.cause else ""
        return f"{kinds}{cause}, {self.seconds}초"


def run_agent(docker: Docker, name: str, *, seconds: float = 60) -> Outcome:
    """채널로 calc 에이전트 실행 하나. 이벤트 스트림을 끝까지(또는 seconds 초까지) 읽는다."""
    body = json.dumps({"agent": "calc", "request": "1+1"})
    reply = helper(docker, name, "sse", "/runs", CHANNEL, body, str(seconds), timeout=seconds + 60)
    events = as_list(dig(reply, "events"))
    started = next((event for event in events if dig(event, "type") == "run_started"), None)
    failed = next((event for event in events if dig(event, "type") == "run_failed"), None)
    return Outcome(
        dig(reply, "status"),
        [as_text(dig(event, "type")) for event in events],
        as_text(dig(started, "principal")),
        as_text(dig(failed, "cause")),
        as_text(dig(failed, "error"))[:200],
        dig(reply, "seconds"),
    )


def put_enabled(docker: Docker, name: str, *, enabled: bool) -> Json:
    body = json.dumps({"enabled": enabled})
    path = "/plugins/skill/cite-sources/enabled"
    return helper(docker, name, "http", "PUT", path, ADMIN, body)


def status_brief(reply: Json) -> str:
    status = dig(reply, "status")
    body = as_text(dig(reply, "body")).replace("\n", " ")[:220]
    return f"{status}" if status in (200, 204) or not body else f"{status} `{body}`"


def build(
    dockerfile: Path, target: str, tag: str, context: Path, *args: str, timeout: float = 900
) -> Done:
    argv = ["build", "--progress", "plain", "-f", str(dockerfile), "--target", target, *args]
    return HOST(*argv, "-t", tag, str(context), timeout=timeout)


def image_mb(tag: str) -> int | None:
    text = HOST("image", "inspect", "-f", "{{.Size}}", tag).out.strip()
    return round(int(text) / 1_000_000) if text.isdigit() else None


def load_now(ctx: Context) -> str:
    """Docker 의 리눅스 VM 부하(/proc/loadavg 의 1·5·15분)와 이때 도는 컨테이너 수."""
    running = len(HOST("ps", "-q").out.split())
    probe = ("run", "--rm", "--name", ctx.name("load"), "--network", "none", "--entrypoint", "cat")
    average = HOST(*probe, PROTO, "/proc/loadavg").out.split()
    return f"부하 {'/'.join(average[:3])}, 도는 컨테이너 {running}"


def diff_lines(docker: Docker, name: str) -> list[str]:
    return [line.strip() for line in docker("diff", name).out.splitlines() if line.strip()]


def summarize(paths: Sequence[str]) -> str:
    """`docker diff` 의 줄을 자리로 묶는다. 깊은 경로는 다섯째 조각까지, 트레이스는 `*.jsonl` 로.
    한 폴더 아래 묶음이 다섯을 넘으면 `<폴더>/*` 하나로 접는다(캐시 폴더의 해시 이름들)."""
    counts: Counter[tuple[str, str]] = Counter()
    for line in paths:
        kind, _, path = line.partition(" ")
        parts = path.split("/")
        if "__pycache__" in parts:
            parts = parts[: parts.index("__pycache__") + 1]
        elif parts[-1].endswith(".jsonl"):
            parts = [*parts[:-1], "*.jsonl"]
        elif len(parts) > 5:
            parts = parts[:5]
        counts[kind, "/".join(parts)] += 1
    siblings = Counter((kind, key.rpartition("/")[0]) for kind, key in counts)
    folded: Counter[str] = Counter()
    for (kind, key), count in counts.items():
        parent = key.rpartition("/")[0]
        shown = f"{parent}/*" if siblings[kind, parent] > 5 else key
        folded[f"{kind} {shown}"] += count
    return "; ".join(
        f"{key} x{count}" if count > 1 else key for key, count in sorted(folded.items())
    )


# ---------------------------------------------------------------- 준비


def needed_images(items: set[str]) -> list[str]:
    wanted = [PROTO]
    if items & {"4", "7"}:
        wanted.append(LOCAL)
    if "6" in items:
        wanted += [ROOTOWNED, V2]
    return wanted


def ensure(ctx: Context, images: Sequence[str]) -> bool:
    """시제품과 그 위의 대조군을 캐시로 짓는다. 측정이 아니라 실패만 측정 아님 회차로 적는다."""
    ready = True
    for image in images:
        if image == PROTO:
            done = build(
                HERE / "Dockerfile", "deb-py", PROTO, ROOT, "--build-arg", f"APP_VERSION={RC}"
            )
        else:
            base = ("--build-arg", f"BASE={PROTO}")
            done = build(HERE / "Dockerfile.derived", DERIVED[image], image, HERE, *base)
        print(f"준비: {image} 빌드 종료 코드 {done.code}, {done.seconds}초", flush=True)
        if done.code != 0:
            ctx.rounds.record(f"준비 {image}", measured=False, result=f"빌드 실패 {tail(done.err)}")
            ready = False
    return ready


def environment() -> str:
    version = HOST("version", "--format", "엔진 {{.Server.Version}} {{.Server.Platform.Name}}")
    kernel = HOST("info", "--format", "커널 {{.KernelVersion}}, CPU {{.NCPU}}, {{.Driver}}")
    return f"{version.out.strip()}, {kernel.out.strip()}, 호스트 {sys.platform}"


def cleanup(token: str) -> None:
    """이 실행이 만든 컨테이너와 볼륨만 지운다. 이름 접두가 `ri-serve-<토큰>-` 인 것이다."""
    prefix = f"ri-serve-{token}-"
    listed = HOST("ps", "-a", "--filter", f"name={prefix}", "--format", "{{.Names}}").out.split()
    containers = [name for name in listed if name.startswith(prefix)]
    if containers:
        remove(HOST, *containers)
    listed = HOST("volume", "ls", "--filter", f"name={prefix}", "--format", "{{.Name}}").out.split()
    volumes = [name for name in listed if name.startswith(prefix)]
    if volumes:
        HOST("volume", "rm", *volumes)
    print(f"정리: 컨테이너 {len(containers)}, 볼륨 {len(volumes)}", flush=True)


# ---------------------------------------------------------------- 1 판 번호


@dataclass(frozen=True)
class VersionBuild:
    """Dockerfile.version 의 갈래 하나. fresh 는 캐시를 버릴 단계(`--no-cache-filter`)다."""

    label: str
    target: str
    app: str = ""
    lock: str = ""
    fresh: str = ""
    fails_with: str = ""
    installed: str = ""


RC_NORM = "0.1.0rc1"
VERSION_BUILDS = (
    VersionBuild("control", "control", fresh="control", installed="0.1.0"),
    VersionBuild("a1-rc", "a1-locked", RC, fresh="edited,a1-locked", fails_with=LOCK_ERROR),
    VersionBuild("a2-rc", "a2-frozen", RC, fresh="edited,a2-frozen", installed=RC_NORM),
    VersionBuild(
        "a3-rc-raw", "a3-lock-edited", RC, RC, fresh="edited,a3-lock-edited", installed=RC_NORM
    ),
    VersionBuild(
        "a3-rc-norm",
        "a3-lock-edited",
        RC,
        RC_NORM,
        fresh="edited,a3-lock-edited",
        installed=RC_NORM,
    ),
    VersionBuild("b1-rc", "b1-frozen", RC, fresh="b1-frozen", installed=RC_NORM),
    VersionBuild("b1-final", "b1-frozen", "0.2.0", fresh="b1-frozen", installed="0.2.0"),
    VersionBuild("b2-rc", "b2-pip", RC, fresh="b2-pip", installed=RC_NORM),
    VersionBuild("c-rc", "c-dynamic", RC, fresh="c-dynamic-src,c-dynamic", installed=RC_NORM),
    VersionBuild(
        "c-unset", "c-dynamic-unset", fresh="c-dynamic-src,c-dynamic-unset", fails_with=UNSET_ERROR
    ),
)
OPENAPI_LABELS = ("control", "a2-rc", "b1-rc", "b1-final", "c-rc")


def judge_version_build(spec: VersionBuild, done: Done) -> tuple[bool, str]:
    """성공 갈래의 표지는 uv 설치 줄의 판이 넘긴 판(정규화한 꼴)인 것과 고친 줄이다.
    c-dynamic 은 사본을 고치지 않고 환경 변수로 넘기므로 고친 줄 대신 다시 잠그기 줄을 본다."""
    text = done.text
    if spec.fails_with:
        line = line_with(text, spec.fails_with)
        if done.code != 0 and line:
            return True, f"빌드 실패(기대), `{line}`"
        return False, f"표지 없음: 종료 {done.code}, {tail(done.err)}"
    edits, locks = EDIT_LINE.findall(text), LOCK_LINE.findall(text)
    installs = INSTALL_LINE.findall(text)
    marks = [spec.installed in installs]
    if spec.app and spec.target != "c-dynamic":
        marks.append(spec.app in edits)
    if spec.lock:
        marks.append(spec.lock in locks)
    extra = ""
    if spec.target == "c-dynamic":
        marks.append("Updated agent-os v0.1.0 -> (dynamic)" in text)
        revisions = [f"{side}{number}" for side, number in REVISION_LINE.findall(text)]
        extra = f", 다시 잠그기 `{line_with(text, 'Updated agent-os')}` revision {revisions}"
    result = f"종료 {done.code}, 고친 줄 {edits}, 잠금 줄 {locks}, uv 설치 줄 {installs}{extra}"
    return done.code == 0 and all(marks), result


def version_item(ctx: Context) -> None:
    print("\n## 1 판 번호", flush=True)
    for spec in VERSION_BUILDS:
        tag = f"ri-serve-ver-{spec.label}"
        versions = (
            "--build-arg",
            f"APP_VERSION={spec.app}",
            "--build-arg",
            f"LOCK_VERSION={spec.lock}",
        )
        fresh = ("--no-cache-filter", spec.fresh)
        done = build(HERE / "Dockerfile.version", spec.target, tag, ROOT, *fresh, *versions)
        with case(ctx, f"1 {spec.label} 빌드") as slot:
            measured, result = judge_version_build(spec, done)
            slot.mark(measured=measured, result=result)
        if done.code != 0 or spec.fails_with:
            continue
        with case(ctx, f"1 {spec.label} 이미지 안의 판") as slot:
            info = helper_once(HOST, ctx.name("pkg"), tag, ["--network", "none"], "pkginfo")
            cli = as_text(dig(info, "cli"))
            slot.mark(
                measured=bool(cli),
                result=(
                    f"--version `{cli}`, metadata `{dig(info, 'metadata')}`, "
                    f"METADATA `{dig(info, 'metadata_line')}`, {dig(info, 'dist_info')}, "
                    f"{dig(info, 'wheel_generator')}"
                ),
            )
        if spec.label in OPENAPI_LABELS:
            openapi_round(ctx, spec.label, tag)


def openapi_round(ctx: Context, label: str, tag: str) -> None:
    command = (*SERVE[:5], "/tmp/traces", *SERVE[6:])
    started = serve(ctx, HOST, "ver", tag, ["--network", "none"], command)
    with case(ctx, f"1 {label} /openapi.json") as slot:
        reply = helper(HOST, started.name, "openapi", ADMIN) if started.state == "ready" else None
        version = as_text(dig(reply, "version"))
        slot.mark(
            measured=dig(reply, "status") == 200 and bool(version),
            result=f"info.version `{version}`, 서기까지 {started.ready}초 {tail(started.logs)}",
        )
    remove(HOST, started.name)


# ---------------------------------------------------------------- 2 바탕 이미지

CANDIDATES = ("deb-py", "deb-node", "alpine")
SED_CHECK = (
    "printf 'version = \"0.1.0\"\\n' | sed '0,/^version = .*$/s//version = \"9.9.9\"/'; "
    "sed --version 2>&1 | head -n 1"
)


def base_item(ctx: Context, *, builds: int) -> None:
    print("\n## 2 바탕 이미지", flush=True)
    for target in CANDIDATES:
        tag = f"ri-serve-base-{target}"
        for index in range(builds):
            load = load_now(ctx)
            args = ("--no-cache", "--build-arg", f"APP_VERSION={RC}")
            done = build(HERE / "Dockerfile", target, tag, ROOT, *args, timeout=1500)
            with case(ctx, f"2 {target} 빌드 {index + 1}") as slot:
                named = f"naming to docker.io/library/{tag}" in done.text
                size = image_mb(tag) if done.code == 0 else None
                slot.mark(
                    measured=done.code == 0 and named and size is not None,
                    result=f"{done.seconds:.0f}초, {size}MB, 짓기 직전 {load}",
                )
        smoke(ctx, target, tag)


def smoke(ctx: Context, target: str, tag: str) -> None:
    offline = ["--network", "none"]
    with case(ctx, f"2 {target} 판과 도구") as slot:
        info = helper_once(HOST, ctx.name("pkg"), tag, offline, "pkginfo")
        cli = as_text(dig(info, "cli"))
        slot.mark(
            measured=bool(cli),
            result=(
                f"--version `{cli}`, python {dig(info, 'python')}, node {dig(info, 'node')}, "
                f"npm {dig(info, 'npm')}"
            ),
        )
    with case(ctx, f"2 {target} 실행 파일 이름으로 MCP") as slot:
        shake = ("handshake", "30", "-", "mcp-server-everything")
        measured, result = handshake_result(
            helper_once(HOST, ctx.name("hs"), tag, offline, *shake), offline=True
        )
        slot.mark(measured=measured, result=result)
    with case(ctx, f"2 {target} sed 의 `0,/정규식/` 주소") as slot:
        # 판을 넣는 sed 한 줄(GNU 의 `0,/re/` 주소)이 그 바탕의 sed 에서 듣는지 본다.
        name = ctx.name("sed")
        argv = ("run", "--rm", "--name", name, *offline, "--entrypoint", "sh", tag, "-c", SED_CHECK)
        shown = HOST(*argv).out.splitlines()
        edited = shown[0] if shown else ""
        slot.mark(
            measured=edited.startswith("version = "),
            result=f"고친 뒤 `{edited}`, sed `{shown[1] if len(shown) > 1 else ''}`",
        )
    started = serve(ctx, HOST, "smoke", tag, offline)
    with case(ctx, f"2 {target} serve /health") as slot:
        ready = started.state == "ready"
        result = f"서기까지 {started.ready}초" if ready else f"{started.state} {tail(started.logs)}"
        slot.mark(measured=started.state in ("ready", "exited"), result=result)
    remove(HOST, started.name)


# ---------------------------------------------------------------- 3 사용자


def users_item(ctx: Context) -> None:
    print("\n## 3 사용자와 getpass.getuser()", flush=True)
    command = (*SERVE[:5], "/tmp/traces", *SERVE[6:])
    cases: tuple[tuple[str, tuple[str, ...], str], ...] = (
        ("이미지의 사용자 10001", (), "agentos"),
        ("--user 12345:12345", ("--user", "12345:12345"), ""),
        (
            "--user 12345:12345 -e USER=operator",
            ("--user", "12345:12345", "-e", "USER=operator"),
            "x",
        ),
    )
    for label, options, starts in cases:
        for index in range(2):
            started = serve(ctx, HOST, "user", PROTO, ["--network", "none", *options], command)
            with case(ctx, f"3 {label} {index + 1}") as slot:
                if starts and started.state == "ready":
                    who = helper(HOST, started.name, "whoami")
                    outcome = run_agent(HOST, started.name, seconds=8)
                    slot.mark(
                        measured=bool(outcome.principal),
                        result=(
                            f"섰다({started.ready}초), principal `{outcome.principal}`, getuser "
                            f"`{dig(who, 'getuser')}`, HOME {dig(who, 'env', 'HOME')} 쓰기 "
                            f"{dig(who, 'home_writable')}"
                        ),
                    )
                else:
                    line = line_with(started.logs, "getpwuid()")
                    code = exit_code_of(HOST, started.name)
                    shown = line or tail(started.logs)
                    slot.mark(
                        measured=started.state == "exited" and bool(line),
                        result=f"{started.state}, 종료 코드 {code}, 로그 `{shown}`",
                    )
            remove(HOST, started.name)


# ---------------------------------------------------------------- 4 예시 MCP 서버


@dataclass(frozen=True)
class Shake:
    """stdio MCP 서버 띄우기 하나. extra 는 서버에 더 넘길 환경 변수의 이름이다."""

    label: str
    image: str
    options: tuple[str, ...]
    argv: tuple[str, ...]
    window: int
    offline: bool
    rounds: int
    extra: str = "-"


NONE = ("--network", "none")
HTTP_LOG = ("-e", "npm_config_loglevel=http")
SHAKES = (
    Shake("npx -y 패키지@2.3.0", PROTO, NONE, ("npx", "-y", PINNED), 100, offline=True, rounds=2),
    Shake("npx -y 패키지", PROTO, NONE, ("npx", "-y", PACKAGE), 100, offline=True, rounds=2),
    Shake("실행 파일 이름", PROTO, NONE, ("mcp-server-everything",), 30, offline=True, rounds=3),
    Shake(
        "npx --offline -y 패키지@2.3.0",
        PROTO,
        NONE,
        ("npx", "--offline", "-y", PINNED),
        30,
        offline=True,
        rounds=1,
    ),
    Shake(
        "네트워크 있음, npx -y 패키지@2.3.0",
        PROTO,
        HTTP_LOG,
        ("npx", "-y", PINNED),
        60,
        offline=False,
        rounds=1,
        extra="npm_config_loglevel",
    ),
    Shake(
        "네트워크 있음, npx -y 패키지",
        PROTO,
        HTTP_LOG,
        ("npx", "-y", PACKAGE),
        60,
        offline=False,
        rounds=1,
        extra="npm_config_loglevel",
    ),
    Shake(
        "작업 폴더 /app 에 깐 이미지, npx -y 패키지",
        LOCAL,
        NONE,
        ("npx", "-y", PACKAGE),
        30,
        offline=True,
        rounds=2,
    ),
    Shake(
        "작업 폴더 /app 에 깐 이미지, npx -y 패키지@2.3.0",
        LOCAL,
        NONE,
        ("npx", "-y", PINNED),
        30,
        offline=True,
        rounds=1,
    ),
    Shake(
        "작업 폴더 /app 에 깐 이미지에서 작업 폴더만 /tmp, npx -y 패키지",
        LOCAL,
        (*NONE, "-w", "/tmp"),
        ("npx", "-y", PACKAGE),
        30,
        offline=True,
        rounds=1,
    ),
)


def fetched(reply: Json) -> list[str]:
    """npm 의 http 기록에서 레지스트리 조회를 `<상태> <경로> (<캐시>)` 로 꺼낸다."""
    found: list[str] = []
    for line in as_list(dig(reply, "stderr_http")):
        match = FETCH_LINE.search(as_text(line))
        if match:
            status, path, cache = match.groups()
            found.append(f"{status} {path or '/'}" + (f" ({cache})" if cache else ""))
    return found


def last_error(reply: Json) -> str:
    lines = [as_text(line) for line in as_list(dig(reply, "stderr_tail"))]
    errors = [line for line in lines if "npm error" in line or "ERR" in line] or lines
    return " / ".join(errors[-2:])[:220]


def handshake_result(reply: Json, *, offline: bool) -> tuple[bool, str]:
    """표지: 서버를 띄웠고, 레지스트리에 닿는지가 기대한 네트워크 상태와 같다."""
    reachable = dig(reply, "registry_reachable")
    if dig(reply, "spawned") is not True or reachable != (not offline):
        reason = as_text(dig(reply, "error"))
        return False, f"표지 없음: spawned={dig(reply, 'spawned')} 닿음={reachable} {reason}"
    network = "네트워크 없음" if offline else "네트워크 있음"
    seconds = dig(reply, "initialize_seconds")
    if dig(reply, "answered") is True:
        text = (
            f"{network}, 답함 {seconds}초, {dig(reply, 'server_name')} "
            f"{dig(reply, 'server_version')}, 도구 {dig(reply, 'tools')}개, 입력을 닫고 "
            f"{dig(reply, 'exit_seconds_after_stdin_close')}초 뒤 끝남"
        )
    else:
        ended = "스스로 끝남" if dig(reply, "exit_code") is not None else "창이 다 차 그룹을 끔"
        text = f"{network}, 답 없음, {seconds}초에 {ended}, stderr `{last_error(reply)}`"
    found = fetched(reply)
    return True, text + (f", 레지스트리 조회 {found}" if found or not offline else "")


def mcp_item(ctx: Context) -> None:
    print("\n## 4 예시 MCP 서버를 네트워크 없이", flush=True)
    print(load_now(ctx), flush=True)
    jobs = [(shake, index, ctx.name("hs")) for shake in SHAKES for index in range(shake.rounds)]
    long_jobs = [job for job in jobs if job[0].window >= 100]
    short_jobs = [job for job in jobs if job[0].window < 100]

    def go(job: tuple[Shake, int, str]) -> Json:
        shake, _, name = job
        args = ("handshake", str(shake.window), shake.extra, *shake.argv)
        return helper_once(HOST, name, shake.image, shake.options, *args, timeout=shake.window + 90)

    # 오래 걸리는 갈래(네트워크 없는 npx)는 함께 띄운다. 기다림은 대부분 이름 풀이의 재시도다.
    with ThreadPoolExecutor(max_workers=len(long_jobs) or 1) as pool:
        replies = dict(zip([job[2] for job in long_jobs], pool.map(go, long_jobs), strict=True))
    for job in short_jobs:
        replies[job[2]] = go(job)
    for shake, index, name in jobs:
        concurrent = " (오래 걸리는 갈래 넷을 함께 띄움)" if shake.window >= 100 else ""
        with case(ctx, f"4 {shake.label} {index + 1}{concurrent}") as slot:
            measured, result = handshake_result(replies.get(name), offline=shake.offline)
            slot.mark(measured=measured, result=result)
    mcp_serve(ctx)


def mcp_serve(ctx: Context) -> None:
    plugins, traces = ctx.name("mcp-plugins"), ctx.name("mcp-traces")
    volumes = ["-v", f"{plugins}:/app/plugins", "-v", f"{traces}:/data/traces"]
    options = ["--network", "none", "--read-only", *volumes]
    started = serve(ctx, HOST, "mcp", PROTO, options, (*SERVE, "--run-timeout", "30"))
    with case(ctx, "4 serve(--network none --read-only), 지금 매니페스트") as slot:
        outcome = run_agent(HOST, started.name, seconds=90)
        slot.mark(measured=outcome.failed, result=f"{outcome.brief()}, `{outcome.error}`")
    for index in range(2):
        with case(ctx, f"4 serve(같은 컨테이너), 실행 파일 이름 매니페스트 {index + 1}") as slot:
            changed = helper(HOST, started.name, "setserver", MANIFEST, *DIRECT)
            outcome = run_agent(HOST, started.name, seconds=90)
            line = line_with(logs_of(HOST, started.name), "Starting default (STDIO) server")
            slot.mark(
                measured=dig(changed, "changed") is True and outcome.failed,
                result=f"{outcome.brief()}, `{outcome.error}`, 서버의 시작 줄 `{line}`",
            )
    remove(HOST, started.name)
    HOST("volume", "rm", plugins, traces)


# ---------------------------------------------------------------- 5 쓰는 자리


def writes_item(ctx: Context) -> None:
    """항목 5 의 호스트 엔진 몫. Docker-in-Docker 몫은 `linux_items` 가 항목 6 과 함께 돈다."""
    print("\n## 5 쓰는 자리와 소유권(호스트 엔진)", flush=True)
    diff_flow(ctx, "실행 파일 이름 매니페스트, 네트워크 없음", ["--network", "none"], direct=True)
    diff_flow(ctx, "지금 매니페스트(npx -y), 네트워크 있음", [], direct=False)
    bytecode(ctx)
    readonly_flow(
        ctx, "실행 파일 이름 매니페스트, 네트워크 없음", ["--network", "none"], direct=True
    )
    readonly_flow(ctx, "지금 매니페스트(npx -y), 네트워크 있음", [], direct=False)
    tmpfs = ["--tmpfs", "/home/agentos:uid=10001,gid=10001,mode=0700"]
    readonly_flow(ctx, "지금 매니페스트(npx -y), 네트워크 있음, HOME 에 tmpfs", tmpfs, direct=False)


def linux_items(ctx: Context, items: set[str]) -> None:
    """Docker-in-Docker 하나에서 항목 5 의 바인드 마운트와 항목 6 을 돈다(이미지는 한 번 싣는다)."""
    print("\n## 5·6 Docker-in-Docker(리눅스 엔진)", flush=True)
    images = [PROTO, ROOTOWNED, V2] if "6" in items else [PROTO]
    with dind(ctx, images) as (inner, name):
        if inner is None:
            ctx.rounds.record("Docker-in-Docker", measured=False, result="띄우지 못했다")
            return
        if "5" in items:
            for spec in BINDS:
                bind_case(ctx, inner, name, spec)
        if "6" in items:
            fill_item(ctx, inner, name)


def flow(docker: Docker, name: str, *, direct: bool) -> tuple[Json, Json, Json, Outcome]:
    """끄기·켜기와 실행 하나. direct 면 먼저 매니페스트를 실행 파일 이름으로 바꾼다."""
    changed = helper(docker, name, "setserver", MANIFEST, *DIRECT) if direct else None
    off = put_enabled(docker, name, enabled=False)
    on = put_enabled(docker, name, enabled=True)
    return changed, off, on, run_agent(docker, name, seconds=90)


def diff_flow(ctx: Context, label: str, options: list[str], *, direct: bool) -> None:
    started = serve(ctx, HOST, "diff", PROTO, options, (*SERVE, "--run-timeout", "40"))
    with case(ctx, f"5 docker diff, {label}") as slot:
        _, off, on, outcome = flow(HOST, started.name, direct=direct)
        paths = diff_lines(HOST, started.name)
        slot.mark(
            measured="A /app/plugins/disabled.toml" in paths and outcome.failed,
            result=(
                f"끄기 {status_brief(off)}, 켜기 {status_brief(on)}, 실행 {outcome.brief()}, "
                f"이미지 밖에 쓴 자리 {summarize(paths)}"
            ),
        )
    remove(HOST, started.name)


def bytecode(ctx: Context) -> None:
    """ver 이미지는 root 로 돈다. 시제품도 root 로 띄운 갈래가 있어야 쓸 권한의 차이와 가른다."""
    images: tuple[tuple[str, str, tuple[str, ...]], ...] = (
        ("UV_COMPILE_BYTECODE 없이 지은 ri-serve-ver-b1-rc(root)", "ri-serve-ver-b1-rc", ()),
        ("시제품(UV_COMPILE_BYTECODE=1, 10001)", PROTO, ()),
        ("시제품(UV_COMPILE_BYTECODE=1)을 root 로", PROTO, ("--user", "0:0")),
    )
    for label, image, user in images:
        name = ctx.name("pyc")
        argv = ("run", "--name", name, "--network", "none", *user, image, "agent-os", "--version")
        done = HOST(*argv)
        with case(ctx, f"5 바이트코드, {label}, agent-os --version") as slot:
            written = [path for path in diff_lines(HOST, name) if "__pycache__" in path]
            slot.mark(
                measured=done.code == 0 and RC in done.out,
                result=f"새로 쓴 __pycache__ 줄 {len(written)}, {summarize(written)[:300]}",
            )
        remove(HOST, name)


def readonly_flow(ctx: Context, label: str, options: list[str], *, direct: bool) -> None:
    plugins, traces = ctx.name("ro-plugins"), ctx.name("ro-traces")
    volumes = ["-v", f"{plugins}:/app/plugins", "-v", f"{traces}:/data/traces"]
    command = (*SERVE, "--run-timeout", "40")
    started = serve(ctx, HOST, "ro", PROTO, ["--read-only", *volumes, *options], command)
    with case(ctx, f"5 --read-only, {label}") as slot:
        changed, off, on, outcome = flow(HOST, started.name, direct=direct)
        logs = logs_of(HOST, started.name)
        problems = [
            line_with(logs, word) for word in ("EROFS", "EACCES", "npm error") if word in logs
        ]
        slot.mark(
            measured=started.state == "ready" and outcome.failed,
            result=(
                f"바꿈 {dig(changed, 'changed')}, 끄기 {status_brief(off)}, 켜기 "
                f"{status_brief(on)}, 실행 {outcome.brief()} `{outcome.error}`, 로그 {problems}"
            ),
        )
    remove(HOST, started.name)
    HOST("volume", "rm", plugins, traces)


@contextmanager
def dind(ctx: Context, images: Sequence[str]) -> Generator[tuple[Docker | None, str]]:
    """Docker-in-Docker 하나를 띄우고 이미지를 실은 뒤 그 안의 docker 를 내준다."""
    name = ctx.name("dind")
    started = HOST("run", "-d", "--privileged", "--name", name, DIND_IMAGE, timeout=120)
    inner = Docker(("docker", "exec", "-i", "-e", ADMIN, "-e", CHANNEL, name, "docker"))
    try:
        ready = started.code == 0 and wait_dind(inner)
        loaded = load_into(name, images) if ready else None
        engine = inner("info", "--format", "엔진 {{.ServerVersion}}, {{.Driver}}").out.strip()
        print(f"Docker-in-Docker: 준비 {ready}, {engine}, 이미지 싣기 {loaded}", flush=True)
        yield (inner if loaded is not None and loaded.code == 0 else None), name
    finally:
        remove(HOST, name)


def wait_dind(inner: Docker) -> bool:
    begin = time.monotonic()
    while time.monotonic() - begin < 120:
        if inner("version", "--format", "{{.Server.Version}}", timeout=30).code == 0:
            return True
        time.sleep(1)
    return False


def load_into(container: str, images: Sequence[str]) -> Done:
    """호스트의 이미지를 `docker save | docker exec -i <dind> docker load` 로 싣는다."""
    started = time.monotonic()
    saver = subprocess.Popen(
        ["docker", "save", *images], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    load = ["docker", "exec", "-i", container, "docker", "load"]
    try:
        loaded = subprocess.run(
            load,
            stdin=saver.stdout,
            capture_output=True,
            encoding="utf-8",
            timeout=900,
            check=False,
        )
    except subprocess.TimeoutExpired:
        saver.kill()
        done = Done(-1, "", "900초 안에 끝나지 않았다", round(time.monotonic() - started, 1))
    else:
        done = Done(
            loaded.returncode, loaded.stdout, loaded.stderr, round(time.monotonic() - started, 1)
        )
    if saver.stdout is not None:
        saver.stdout.close()
    try:
        saver.wait(timeout=60)
    except subprocess.TimeoutExpired:
        saver.kill()
    raw(f"docker save {' '.join(images)} | docker exec -i {container} docker load", repr(done))
    return done


@dataclass(frozen=True)
class Bind:
    """바인드 마운트 갈래 하나. owner·mode 는 Docker-in-Docker 쪽 폴더의 소유자와 권한이다."""

    label: str
    owner: str
    mode: str
    options: tuple[str, ...] = ()


BINDS = (
    Bind("다른 uid 1000 소유 0755", "1000:1000", "755"),
    Bind("이미지 사용자 10001 소유 0755(대조군)", "10001:10001", "755"),
    Bind("다른 uid 1000 소유 0777", "1000:1000", "777"),
    Bind("다른 uid 1000 소유 0755, --user 1000:1000", "1000:1000", "755", ("--user", "1000:1000")),
    Bind(
        "다른 uid 1000 소유 0755, --user 1000:1000 -e USER=operator",
        "1000:1000",
        "755",
        ("--user", "1000:1000", "-e", "USER=operator"),
    ),
)
# 이미지의 플러그인을 바인드 마운트 폴더로 옮기고 예시 MCP 서버를 실행 파일 이름으로 바꾼 뒤
# 소유자와 권한을 준다. 실행이 네트워크 없이 MCP 를 지나 모델 호출에서 끝나게 하려는 것이다.
PREPARE = (
    "cp -a /app/plugins/. /out/plugins/"
    " && sed -i 's/^command = .*/command = \"mcp-server-everything\"/; s/^args = .*/args = []/'"
    " /out/plugins/mcp/everything/plugin.toml"
    " && chown -R {owner} /out/plugins /out/traces && chmod {mode} /out/plugins /out/traces"
)


def bind_case(ctx: Context, inner: Docker, dind_name: str, spec: Bind) -> None:
    base = f"/srv/{ctx.name('bind')}"
    plugins, traces = f"{base}/plugins", f"{base}/traces"
    mounts = ["-v", f"{plugins}:/out/plugins", "-v", f"{traces}:/out/traces"]
    script = PREPARE.format(owner=spec.owner, mode=spec.mode)
    prep_name = ctx.name("prep")
    inner(
        "run",
        "--rm",
        "--name",
        prep_name,
        "--user",
        "0:0",
        *mounts,
        "--entrypoint",
        "sh",
        PROTO,
        "-c",
        script,
    )
    before = HOST("exec", dind_name, "stat", "-c", "%u:%g %a", plugins, traces).out.split("\n")
    options = ["--network", "none", "--read-only", *spec.options]
    options += ["-v", f"{plugins}:/app/plugins", "-v", f"{traces}:/data/traces"]
    started = serve(ctx, inner, "bind", PROTO, options, (*SERVE, "--run-timeout", "20"))
    with case(ctx, f"5 바인드 마운트, {spec.label}") as slot:
        prepared = [line.strip() for line in before if line.strip()]
        wanted = f"{spec.owner} {spec.mode}"
        if started.state == "ready":
            off = put_enabled(inner, started.name, enabled=False)
            outcome = run_agent(inner, started.name, seconds=45)
            writes = helper(inner, started.name, "writetest", "/app/plugins", "/data/traces")
            listing = f"stat -c '%u:%g %a %n' {plugins}/disabled.toml {traces}/*.jsonl 2>/dev/null"
            host = HOST("exec", dind_name, "sh", "-c", listing).out.split("\n")
            logged = logs_of(inner, started.name).splitlines()
            denied = sorted({line.strip()[:160] for line in logged if "Errno 13" in line})[:3]
            result = (
                f"섰다, 끄기 {status_brief(off)}, 실행 {outcome.brief()} `{outcome.error[:120]}`, "
                f"쓰기 {writes}, 바깥에서 본 새 파일 {[line for line in host if line.strip()]}, "
                f"서버 로그의 권한 오류 {denied}"
            )
            situation = dig(off, "status") is not None
        else:
            code = exit_code_of(inner, started.name)
            line = line_with(started.logs, "getpwuid()") or tail(started.logs)
            result = f"{started.state}, 종료 코드 {code}, 로그 `{line}`"
            situation = started.state == "exited" and bool(started.logs)
        slot.mark(
            measured=prepared == [wanted, wanted] and situation,
            result=f"준비한 폴더 {prepared}, {result}",
        )
    remove(inner, started.name)


# ---------------------------------------------------------------- 6 첫 채움


def fill_item(ctx: Context, inner: Docker, dind_name: str) -> None:
    print("\n## 6 플러그인 폴더의 첫 채움(Docker-in-Docker)", flush=True)
    for label, image in (("시제품", PROTO), ("root 소유로 바꾼 이미지(대조군)", ROOTOWNED)):
        first_fill(ctx, inner, label, image)
    empty_bind(ctx, inner, dind_name, "Docker 가 만든 빈 폴더(root 소유)", "")
    empty_bind(ctx, inner, dind_name, "미리 만든 빈 폴더(10001 소유)", "10001:10001")
    upgrade(ctx, inner)


def first_fill(ctx: Context, inner: Docker, label: str, image: str) -> None:
    plugins, traces = ctx.name("fill-plugins"), ctx.name("fill-traces")
    options = ["--network", "none", "--read-only"]
    options += ["-v", f"{plugins}:/app/plugins", "-v", f"{traces}:/data/traces"]
    started = serve(ctx, inner, "fill", image, options)
    with case(ctx, f"6 빈 이름 있는 볼륨, {label}") as slot:
        before = helper(inner, started.name, "tree", "/app/plugins")
        off = put_enabled(inner, started.name, enabled=False)
        after = helper(inner, started.name, "tree", "/app/plugins")
        made = "disabled.toml" in as_list(dig(after, "paths"))
        slot.mark(
            measured=isinstance(dig(before, "count"), int) and dig(off, "status") is not None,
            result=(
                f"복사된 항목 {dig(before, 'count')}, 소유자 {dig(before, 'owners')}, 폴더 "
                f"uid {dig(before, 'root_uid')} {dig(before, 'root_mode')}, 끄기 "
                f"{status_brief(off)}, disabled.toml 생김 {made}"
            ),
        )
    remove(inner, started.name)
    inner("volume", "rm", plugins, traces)


def empty_bind(ctx: Context, inner: Docker, dind_name: str, label: str, owner: str) -> None:
    folder = f"/srv/{ctx.name('empty')}/plugins"
    if owner:
        HOST("exec", dind_name, "sh", "-c", f"mkdir -p {folder} && chown {owner} {folder}")
    traces = ctx.name("empty-traces")
    options = ["--network", "none", "--read-only"]
    options += ["-v", f"{folder}:/app/plugins", "-v", f"{traces}:/data/traces"]
    started = serve(ctx, inner, "empty", PROTO, options)
    with case(ctx, f"6 빈 바인드 마운트, {label}") as slot:
        view = helper_once(
            inner,
            ctx.name("look"),
            PROTO,
            ["--network", "none", "-v", f"{folder}:/app/plugins"],
            "tree",
            "/app/plugins",
        )
        code = exit_code_of(inner, started.name)
        slot.mark(
            measured=dig(view, "count") == 0 and started.state in ("ready", "exited"),
            result=(
                f"안에서 본 항목 {dig(view, 'count')}(폴더 uid {dig(view, 'root_uid')}), serve "
                f"{started.state}, 종료 코드 {code}, 로그 `{tail(started.logs, 4)}`"
            ),
        )
    remove(inner, started.name)
    inner("volume", "rm", traces)


def upgrade(ctx: Context, inner: Docker) -> None:
    offline = ["--network", "none"]
    used, fresh = ctx.name("used"), ctx.name("fresh")

    def look(image: str, volume: str) -> tuple[Json, Json]:
        mount = [*offline, "-v", f"{volume}:/app/plugins"]
        version = helper_once(inner, ctx.name("look"), image, mount, "lines", MANIFEST, "version")
        listed = helper_once(inner, ctx.name("look"), image, mount, "tree", "/app/plugins")
        return dig(version, "lines"), dig(listed, "paths")

    first, _ = look(PROTO, used)
    second, second_paths = look(V2, used)
    control, control_paths = look(V2, fresh)
    with case(ctx, "6 앞 판이 채운 볼륨에 다음 판 이미지") as slot:
        slot.mark(
            measured=first == ['version = "0.1.0"'],
            result=(
                f"앞 판이 채운 뒤 {first}, 다음 판을 붙인 뒤 {second}, NEW_IN_V2.txt "
                f"{'NEW_IN_V2.txt' in as_list(second_paths)}"
            ),
        )
    with case(ctx, "6 빈 볼륨에 다음 판 이미지(양성 대조)") as slot:
        carried = "NEW_IN_V2.txt" in as_list(control_paths)
        slot.mark(
            measured=control == ['version = "0.2.0"'] and carried,
            result=f"{control}, NEW_IN_V2.txt {carried}",
        )
    inner("volume", "rm", used, fresh)


# ---------------------------------------------------------------- 7 init 과 종료

INIT_MODES: tuple[tuple[str, tuple[str, ...], tuple[str, ...], str], ...] = (
    ("tini(이미지의 ENTRYPOINT)", (), SERVE, "tini"),
    ("docker run --init", ("--init", "--entrypoint", "agent-os"), SERVE[1:], "docker-init"),
    ("init 없음(--entrypoint agent-os)", ("--entrypoint", "agent-os"), SERVE[1:], "agent-os serve"),
    (
        "셸 감싸기(대조군)",
        ("--entrypoint", "sh"),
        ("-c", " ".join(SERVE) + "; echo serve-exited"),
        "sh -c",
    ),
)


def init_item(ctx: Context, *, repeat: int) -> None:
    print("\n## 7 init 과 종료", flush=True)
    print(load_now(ctx), flush=True)
    for label, options, command, marker in INIT_MODES:
        for index in range(repeat):
            started = serve(ctx, HOST, "init", LOCAL, ["--network", "none", *options], command)
            with case(ctx, f"7 {label} {index + 1}") as slot:
                measured, result = init_round(started, marker)
                slot.mark(measured=measured, result=result)
            remove(HOST, started.name)
    stop_wait(ctx, repeat=repeat)


def stop_wait(ctx: Context, *, repeat: int) -> None:
    """SIGTERM 처리기가 없는 pid 1(`sleep`)에 `docker stop` 을 건다. 엔진이 SIGKILL 까지 기다리는
    시간을 `-t` 를 주지 않은 것과 `-t 10` 으로 견준다. 표지는 종료 코드 137(SIGKILL 로
    끝났다)이다."""
    waits = [((), index) for index in range(repeat)] + [(("-t", "10"), 0)]
    for flags, index in waits:
        name = ctx.name("stopwait")
        sleeper = ("run", "-d", "--name", name, "--network", "none", "--entrypoint", "sleep")
        HOST(*sleeper, LOCAL, "1000")
        time.sleep(1)
        stopped = HOST("stop", *flags, name, timeout=90)
        code = exit_code_of(HOST, name)
        label = " ".join(flags) or "-t 없음"
        with case(ctx, f"7 처리기 없는 pid 1 에 docker stop {label} {index + 1}") as slot:
            slot.mark(
                measured=stopped.code == 0 and code == "137",
                result=f"stop {stopped.seconds}초, 종료 코드 {code}",
            )
        remove(HOST, name)


def init_round(started: Serve, marker: str) -> tuple[bool, str]:
    """MCP 실행 넷(npx 둘, 실행 파일 이름 둘) 뒤 좀비, 고아 거두기, docker stop 을 본다."""
    name = started.name
    pid1 = as_text(dig(helper(HOST, name, "procs"), "pid1"))
    outcomes = [run_agent(HOST, name, seconds=60) for _ in range(2)]
    helper(HOST, name, "setserver", MANIFEST, *DIRECT)
    outcomes += [run_agent(HOST, name, seconds=60) for _ in range(2)]
    zombies = as_list(dig(helper(HOST, name, "procs"), "zombies"))
    orphan = helper(HOST, name, "orphan")
    stop = HOST("stop", name, timeout=90)
    code = exit_code_of(HOST, name)
    graceful = "Finished server process" in logs_of(HOST, name)
    causes = [outcome.cause or outcome.brief() for outcome in outcomes]
    comms = [f"{dig(z, 'comm')}(부모 {dig(z, 'ppid')})" for z in zombies]
    result = (
        f"pid 1 `{pid1[:70]}`, 실행 넷 {causes} 뒤 좀비 {len(zombies)} {comms}, 고아의 끝 "
        f"{dig(orphan, 'state_after_exit')}(부모 {dig(orphan, 'parent_after_orphaned')}), "
        f"stop {stop.seconds}초, 종료 코드 {code}, uvicorn 종료 줄 {graceful}"
    )
    measured = marker in pid1 and stop.code == 0 and all(outcome.failed for outcome in outcomes)
    return measured, result


# ---------------------------------------------------------------- 8 상태 확인


def health_item(ctx: Context) -> None:
    print("\n## 8 상태 확인", flush=True)
    print(load_now(ctx), flush=True)
    started = serve(ctx, HOST, "health", PROTO, ["--network", "none"])
    print(f"serve 가 서기까지 {started.ready}초({started.state})", flush=True)
    commands = (
        ("python 한 줄, 포트 8000", ("python", "-c", HEALTH_PY.format(port=8000))),
        ("python 한 줄, 포트 8001(대조군)", ("python", "-c", HEALTH_PY.format(port=8001))),
        ("node 한 줄, 포트 8000", ("node", "-e", HEALTH_NODE.format(port=8000))),
        ("node 한 줄, 포트 8001(대조군)", ("node", "-e", HEALTH_NODE.format(port=8001))),
    )
    for label, argv in commands:
        with case(ctx, f"8 {label}") as slot:
            timed = helper(HOST, started.name, "timecmd", "3", *argv)
            outer = [HOST("exec", started.name, *argv) for _ in range(2)]
            slot.mark(
                measured=started.state == "ready" and bool(as_list(dig(timed, "codes"))),
                result=(
                    f"안에서 종료 코드 {dig(timed, 'codes')} {dig(timed, 'ms')}ms, docker exec 로 "
                    f"{[done.code for done in outer]} {[done.seconds for done in outer]}초"
                ),
            )
    remove(HOST, started.name)
    checks = (
        ("--health-cmd python 한 줄, 포트 8000", 8000, "3", "30s", "healthy"),
        ("--health-cmd python 한 줄, 포트 8001(대조군)", 8001, "2", "0s", "unhealthy"),
    )
    for label, port, retries, period, want in checks:
        for index in range(2):
            health_check(ctx, f"8 {label} {index + 1}", port, (retries, period), want)


def health_check(ctx: Context, label: str, port: int, policy: tuple[str, str], want: str) -> None:
    retries, period = policy
    name = ctx.name("hc")
    options = ("--health-cmd", f'python -c "{HEALTH_PY.format(port=port)}"')
    options += ("--health-interval", "2s", "--health-timeout", "5s")
    options += ("--health-retries", retries, "--health-start-period", period)
    started = HOST(
        "run",
        "-d",
        "--name",
        name,
        "-e",
        ADMIN,
        "-e",
        CHANNEL,
        "--network",
        "none",
        *options,
        PROTO,
    )
    begin = time.monotonic()
    health: Json = None
    while time.monotonic() - begin < 90:
        health = parse(HOST("inspect", "-f", "{{json .State.Health}}", name).out)
        if dig(health, "Status") == want:
            break
        time.sleep(0.5)
    seconds = round(time.monotonic() - begin, 1)
    log = as_list(dig(health, "Log"))
    last = log[-1] if log else None
    output = as_text(dig(last, "Output")).strip().replace("\n", " ")[-160:]
    with case(ctx, label) as slot:
        slot.mark(
            measured=started.code == 0 and bool(log),
            result=(
                f"상태 {dig(health, 'Status')}, 띄우고 {seconds}초, 검사 {len(log)}번, 마지막 종료 "
                f"코드 {dig(last, 'ExitCode')}, 출력 `{output}`"
            ),
        )
    remove(HOST, name)


# ---------------------------------------------------------------- 실행


def main() -> int:
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--items", default="1,2,3,4,5,6,7,8")
    builds = "항목 2 에서 후보마다 지을 횟수(0 이면 지어 둔 이미지만 본다)"
    parser.add_argument("--builds", type=int, default=2, help=builds)
    parser.add_argument("--repeat", type=int, default=2, help="항목 7 에서 갈래마다 돌 횟수")
    parser.add_argument("--no-dind", action="store_true", help="항목 5 의 Docker-in-Docker 를 뺀다")
    parser.add_argument("--work", type=Path)
    args = parser.parse_args()
    items = set(str(args.items).split(","))
    work = Path(tempfile.mkdtemp(prefix="serve-image-probe-", dir=args.work))
    _raw.append(work / "raw.log")
    token = secrets.token_hex(3)
    os.environ[ADMIN] = secrets.token_urlsafe(24)
    os.environ[CHANNEL] = secrets.token_urlsafe(24)
    ctx = Context(token, Rounds())
    print(f"원본 출력 {_raw[0]}, 회차 토큰 {token}", flush=True)
    print(environment(), flush=True)
    try:
        if ensure(ctx, needed_images(items)):
            run_items(ctx, items, args)
    finally:
        cleanup(token)
    closing = [line for line in ctx.rounds.summary().splitlines() if not line.startswith("결과: ")]
    print("\n".join(closing))
    return ctx.rounds.exit_code()


def run_items(ctx: Context, items: set[str], args: argparse.Namespace) -> None:
    if "1" in items:
        version_item(ctx)
    if "2" in items:
        base_item(ctx, builds=int(args.builds))
    if "3" in items:
        users_item(ctx)
    if "4" in items:
        mcp_item(ctx)
    if "5" in items:
        writes_item(ctx)
    linux = items & {"6"} if args.no_dind else items & {"5", "6"}
    if linux:
        linux_items(ctx, linux)
    if "7" in items:
        init_item(ctx, repeat=int(args.repeat))
    if "8" in items:
        health_item(ctx)


if __name__ == "__main__":
    sys.exit(main())
