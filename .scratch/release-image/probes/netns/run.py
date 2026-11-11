"""release-image 설계의 "모든 컨테이너가 프록시의 네트워크 이름공간을 함께 쓴다" 배치를 잰다.
결정은 하지 않고 회차마다 본 것을 한 줄씩 낸다.

저장소 루트에서

    uv run python .scratch/release-image/probes/netns/run.py [--sections 1,2,3,4,5,6,7]
        [--nginx-image <참조>] [--python-image <참조>] [--work <원본 출력을 둘 폴더>]

필요한 것. 도는 Docker 데몬과 compose, 로컬에 이미 있는 이미지 둘(기본값은 아래 NGINX_IMAGE 와
PYTHON_IMAGE 의 digest 참조. 받지 않는다, compose 파일의 pull_policy: never), 비어 있는 호스트 포트
39411~39417(127.0.0.1 에만 연다). compose 프로젝트 이름은 release-image-netns-probe 하나이고,
갈래마다 `down -v --remove-orphans` 로 지운 뒤 다시 띄우며 끝에서도 지운다. 다른 프로젝트의
컨테이너와 이미지는 건드리지 않는다. 모든 명령의 원본 출력은 --work(없으면 시스템 임시 폴더) 아래
raw.log 에 남긴다.

누가 답했는지. 서버 컨테이너는 시작할 때 marker.txt 에 '<이름>:<회차 토큰>' 을 쓴다(compose 파일의
command). "닿는다"는 상태 200 과 그 본문을 함께 본 것이다. 토큰은 실행마다 새로 뽑는다.

항목(번호는 일을 맡긴 지시문의 것이다)

1. compose.shared.yml. proxy(nginx)가 127.0.0.1 에 연 포트로 호스트에서 요청해, proxy 의
   이름공간을 빌린 app(127.0.0.1:8000 에만 묶임)의 답이 오는지. 표지는 app 의 NetworkMode 가
   container:<proxy id> 이고 두 컨테이너의 /proc/self/ns/net 이 같은 것이다. 같은 이름공간의
   eth0 주소로는 8000 이 거부되는지도 본다(양성 대조는 같은 주소의 nginx 8080).
2. compose.bridge.yml(대조군). 루프백에만 묶인 app 을 보통의 bridge 네트워크에 두고 ports 로
   열었을 때 (가) 호스트에서 발행 포트로, (나) 다른 컨테이너에서 서비스 이름으로 닿는지. 양성
   대조는 같은 배치의 0.0.0.0 에 묶은 app-open 이고, app 이 자기 루프백에서는 답한다는 것과 두
   컨테이너의 이름공간이 다르다는 것도 함께 본다. 셋이 서지 않으면 측정이 아니다.
3. compose.shared.yml 에 덧씌움 셋(없음, depends_on 짧은 꼴, depends_on 의 restart: true)을 바꿔
   가며 proxy 를 흔드는 조작을 갈래마다 새로 띄운 배치에서 한다. compose 조작은 넷이다.
   `restart proxy`, `up -d --force-recreate proxy`, proxy 의 환경 값을 바꾼 뒤 `up -d`, 이름 없는
   `restart`. 표지는 proxy 가 실제로 다시 시작됐거나(같은 컨테이너, 새 시작 시각) 다시 만들어진
   것(새 컨테이너 id)이다. compose 를 거치지 않는 조작은 둘이다. `docker restart <proxy>` 와,
   재시작 정책(restart: always)을 둔 채 proxy 안에서 `nginx -s stop` 을 쳐 Docker 데몬이 proxy 를
   다시 띄우게 하는 것(표지는 RestartCount 증가). 이 둘은 app 을 다시 띄운 것이 compose 인지
   데몬인지를 가른다. 닿지 않으면 까닭을 가르는 관찰(두 컨테이너의 이름공간, app 이 자기
   루프백에서 답하는지, nginx 오류 기록의 상류 연결 실패)을 덧붙이고, 회복 명령을 약한
   것부터(`restart app`, `up -d`, `up -d --force-recreate app`) 닿을 때까지 친다. 그 차례에서
   `up -d` 는 `restart app` 뒤에 오므로, `up -d --force-recreate proxy` 는 한 번 더 해서 회복을
   `up -d` 부터 친다(app 이 옛 이름공간에서 아직 도는 채로 `up -d` 만으로 회복되는지).
4. 이름공간을 빌린 app 에 ports 를 직접 준 파일(compose.ports-on-app.yml)을 받는지와 거부 문구,
   proxy 서비스가 8000 을 대신 발행하면 호스트에서 닿는지, nginx 의 둘째 listen(8081)을
   127.0.0.1 에만 발행하면 admin 에 닿는지, 그 포트가 호스트의 다른 주소로는 닿지 않는지(이
   호스트 안에서 건 연결이다. 다른 기기에서는 재지 않는다), 호스트의 듣는 소켓이 어느 주소에
   묶였는지(netstat, 윈도만). 첫 갈래의 표지는 거부 문구가 port 와 network mode 를 함께 드는
   것이고(포트가 이미 쓰여 난 실패와 가른다), 발행 갈래의 표지는 docker inspect 의 발행 주소다.
5. limit_req 의 한도를 넘긴 요청의 상태 코드(기본값과 limit_req_status 429). 표지는 첫 요청이
   app 에 닿았고 거부된 요청마다 nginx 오류 기록에 그 구역의 'limiting requests' 줄이 있는
   것이다. 그리고 호스트에서 온 요청과 같은 네트워크의 다른 컨테이너(peer)에서 온 요청의
   $remote_addr(접근 기록의 rid 로 찾는다), 주소가 다른 둘의 한도가 따로 세어지는지.
6. (지시문에 없는 덧붙임) compose.loopback6.yml. 같은 배치에서 서버가 ::1 에만 묶이고 nginx 가
   `proxy_pass http://[::1]:8002` 로 넘길 때 닿는지. 네 프로세스의 규칙이 ::1 도 받기 때문이다.
7. (뒤에 받은 지시) compose.holder.yml. 이름공간의 주인을 프록시가 아니라 sleep 하나만 도는
   holder 로 두고 proxy 와 app 과 admin 이 모두 그것을 빌리는 배치다. 호스트 포트는 holder 에
   발행한다. 갈래는 다섯이다.
   7.1 호스트에서 app 과 admin 에 닿는지. 표지는 빌린 셋의 NetworkMode 가 container:<holder id>
       이고 네 컨테이너의 /proc/self/ns/net 이 같은 것이다.
   7.2 항목 3 의 조작 여섯을 proxy 에 한다. 표지는 항목 3 과 같다(proxy 가 실제로 다시
       시작됐거나 다시 만들어졌다). 닿는지와 함께 네 컨테이너가 저마다 그대로인지(같은 id 에 같은
       State.StartedAt) 다시 시작됐는지 다시 만들어졌는지를 낸다.
   7.3 holder 를 흔든다. `restart holder`, `docker restart <holder>`, 재시작 정책을 둔 채
       `docker kill <holder>`, `up -d --force-recreate holder`. docker kill 의 표지는 holder 가 멈춘
       채 남았거나 다시 뜬 것이고, 어느 쪽인지를 결과에 낸다. 재시작 정책이 실제로 다시 띄우는
       것은 holder 의 프로세스가 스스로 끝나는 갈래(양성 대조, 표지는 RestartCount 증가)로 본다.
       닿지 않으면 네 컨테이너의 이름공간과, 빌린 셋이 저희끼리는 닿는지를 덧붙이고, 회복 명령을
       `up -d`, `restart proxy app admin`, `up -d --force-recreate proxy app admin` 차례로 친다.
   7.4 app 하나만 다시 만든다(`up -d --force-recreate app`, 그리고 app 의 환경 값을 바꾼 뒤
       `up -d`). 표지는 app 의 컨테이너 id 가 바뀐 것이다.
   7.5 `nginx -s reload`. proxy 컨테이너 안의 설정 폴더에 location 하나를 써 넣고 다시 읽게
       한다. 표지는 그 location 이 다시 읽기 전에는 답하지 않고 뒤에는 새 설정의 답을 내는
       것이다. holder 배치와, 주인이 proxy 인 배치(compose.shared.yml 에
       compose.reload-conf.yml 을 덧씌운 것)에서 한 번씩 한다.

못 보는 것. 다른 기기에서 오는 요청(실제 클라이언트 주소, 다른 인터페이스로의 접근), Docker
데몬이나 호스트를 다시 켠 뒤의 순서(데몬을 다시 시작하지 않는다), 리눅스 호스트의 Docker Engine 과
podman. 이 스크립트는 그것을 재지 않는다. 결과는 같은 폴더의 README.md 에 있다.
"""

from __future__ import annotations

import argparse
import http.client
import io
import json
import os
import re
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Generator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds, Slot  # noqa: E402

PROJECT = "release-image-netns-probe"
# 2026-11-11 이 PC 에 이미 있던 공식 이미지다. nginx:alpine(nginx 1.31.6)과
# python:3.12.10-slim-bookworm.
NGINX_IMAGE = "nginx@sha256:c8497b180665e631ec92a5091125bec5b214f0e2b99409e30653a125b37557da"
PYTHON_IMAGE = "python@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db"
PORTS = {
    "PUBLIC": 39411,
    "ADMIN": 39412,
    "DIRECT": 39413,
    "BRIDGE_LOOPBACK": 39414,
    "BRIDGE_OPEN": 39415,
    "PORTS_ON_APP": 39416,
    "LOOPBACK6": 39417,
}
ACCESS = re.compile(r"probe-access addr=(\S+) listen=(\d+) status=(\d+) rid=(\S+)")
# 컨테이너 안에서 도는 요청 하나. `python - <host> <port> <path>` 의 표준 입력으로 넘긴다.
INSIDE = """\
import http.client, sys
host, port, path = sys.argv[1], int(sys.argv[2]), sys.argv[3]
connection = http.client.HTTPConnection(host, port, timeout=5)
try:
    connection.request('GET', path)
    reply = connection.getresponse()
    print('STATUS', reply.status, reply.read().decode())
except Exception as error:
    print('ERROR', type(error).__name__, error)
"""

_raw: list[Path] = []


def raw(title: str, text: str) -> None:
    if _raw:
        with _raw[0].open("a", encoding="utf-8") as out:
            out.write(f"\n===== {time.strftime('%H:%M:%S')} {title}\n{text}\n")


def tail(text: str, count: int = 3) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " / ".join(lines[-count:])


# docker 와 compose 가 내는 JSON 을 읽는 자리. 모양이 기대와 다르면 예외 대신 빈 값이 나오고, 그
# 빈 값으로는 아래의 표지(컨테이너 id, 시작 시각, NetworkMode)가 서지 않아 측정 아님으로 세어진다.
type Json = dict[str, Json] | list[Json] | str | int | float | bool | None


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


def as_text(value: Json, default: str = "") -> str:
    return value if isinstance(value, str) else default


def dig(value: Json, *keys: str | int) -> Json:
    """JSON 값을 열쇠(객체)와 차례(배열)를 따라 내려간다. 길이 끊기면 None 이다."""
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


def run(
    argv: list[str],
    *,
    env: Mapping[str, str] | None = None,
    stdin: str | None = None,
    timeout: float = 240,
) -> Done:
    """명령 하나. 표준 입력은 늘 닫힌 파이프다(물려받지 않는다). 시간을 넘기면 종료 코드 -1."""
    try:
        completed = subprocess.run(
            argv,
            cwd=HERE,
            env={**os.environ, **(env or {})},
            input=stdin or "",
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        done = Done(-1, "", f"{timeout:.0f}초 안에 끝나지 않았다")
    else:
        done = Done(completed.returncode, completed.stdout, completed.stderr)
    raw(" ".join(argv), f"exit={done.code}\n--- stdout\n{done.out}\n--- stderr\n{done.err}")
    return done


@dataclass(frozen=True)
class Stack:
    """compose 파일 묶음 하나. 프로젝트 이름은 늘 PROJECT 다."""

    files: tuple[str, ...]
    env: Mapping[str, str]
    profiles: tuple[str, ...] = ()

    def compose(self, *args: str, stdin: str | None = None, timeout: float = 240) -> Done:
        argv = ["docker", "compose", "--ansi", "never", "--progress", "plain", "-p", PROJECT]
        for name in self.files:
            argv += ["-f", str(HERE / name)]
        for profile in self.profiles:
            argv += ["--profile", profile]
        return run([*argv, *args], env=self.env, stdin=stdin, timeout=timeout)

    def with_env(self, extra: Mapping[str, str]) -> Stack:
        return Stack(self.files, {**self.env, **extra}, self.profiles)


@dataclass(frozen=True)
class Box:
    """컨테이너 하나의 지금 모습(docker inspect)."""

    id: str
    started: str
    running: bool
    restarts: int
    network_mode: str
    addresses: tuple[str, ...]
    published: Mapping[str, tuple[str, ...]]


def boxes() -> dict[str, Box]:
    """이 프로젝트의 컨테이너 전부의 지금 모습(멈춘 것 포함)을 서비스 이름으로 모은다.
    compose 가 붙인 라벨로 찾는다. 서비스마다 컨테이너가 하나인 배치만 다룬다."""
    label = f"label=com.docker.compose.project={PROJECT}"
    listed = run(["docker", "ps", "-a", "-q", "--no-trunc", "--filter", label], timeout=60)
    ids = listed.out.split()
    if listed.code != 0 or not ids:
        return {}
    inspected = run(["docker", "inspect", *ids], timeout=60)
    if inspected.code != 0:
        return {}
    found: dict[str, Box] = {}
    for info in as_list(parse(inspected.out)):
        networks = as_map(dig(info, "NetworkSettings", "Networks"))
        ports = as_map(dig(info, "NetworkSettings", "Ports"))
        addresses = (as_text(dig(net, "IPAddress")) for net in networks.values())
        count = dig(info, "RestartCount")
        service = as_text(dig(info, "Config", "Labels", "com.docker.compose.service"))
        found[service] = Box(
            id=as_text(dig(info, "Id")),
            started=as_text(dig(info, "State", "StartedAt")),
            running=dig(info, "State", "Running") is True,
            restarts=count if isinstance(count, int) else 0,
            network_mode=as_text(dig(info, "HostConfig", "NetworkMode")),
            addresses=tuple(address for address in addresses if address),
            published={port: bindings_of(bound) for port, bound in ports.items()},
        )
    return found


def bindings_of(value: Json) -> tuple[str, ...]:
    """발행 포트 하나가 묶인 호스트 쪽 자리들('주소:포트')."""
    pairs = ((dig(bound, "HostIp"), dig(bound, "HostPort")) for bound in as_list(value))
    return tuple(f"{as_text(address)}:{as_text(port)}" for address, port in pairs)


def borrows(borrower: Box | None, owner: Box | None) -> bool:
    """borrower 의 NetworkMode 가 owner 컨테이너의 네트워크 이름공간을 가리키는가."""
    if borrower is None or owner is None:
        return False
    return borrower.network_mode == f"container:{owner.id}"


def change(before: Box | None, after: Box | None) -> str:
    if after is None:
        return "없어짐"
    if before is None:
        return "새로 생김"
    if after.id != before.id:
        return "다시 만들어짐(새 id)"
    state = "" if after.running else ", 지금 멈춤"
    if after.started != before.started:
        return f"다시 시작됨(같은 id, 새 시작 시각{state})"
    return f"그대로(같은 id, 같은 시작 시각{state})"


@dataclass(frozen=True)
class Reply:
    """요청 하나의 결과. status 가 0 이면 HTTP 응답을 받지 못한 것이고 error 가 까닭이다.
    asked 가 거짓이면 요청을 보내 보지도 못한 것이다(컨테이너 안의 실행이 돌지 않았다)."""

    status: int = 0
    body: str = ""
    error: str = ""
    asked: bool = True

    def brief(self) -> str:
        return str(self.status) if self.status else self.error[:140]

    def kind(self) -> str:
        return str(self.status) if self.status else self.error.split(":")[0].split(" ")[0]


def fetch(port: int, path: str, *, host: str = "127.0.0.1", timeout: float = 5.0) -> Reply:
    """호스트에서 보내는 GET 하나. 시스템 프록시 설정을 타지 않게 http.client 로 바로 건다."""
    connection = http.client.HTTPConnection(host, port, timeout=timeout)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        body = response.read().decode("utf-8", errors="replace")
    except (OSError, http.client.HTTPException) as error:
        return Reply(error=f"{type(error).__name__}: {error}")
    finally:
        connection.close()
    return Reply(response.status, body)


def fetch_inside(stack: Stack, service: str, host: str, port: int, path: str) -> Reply:
    """그 서비스의 컨테이너 안에서 보내는 GET 하나."""
    done = stack.compose(
        "exec", "-T", service, "python", "-", host, str(port), path, stdin=INSIDE, timeout=60
    )
    kind, _, rest = done.out.strip().partition(" ")
    if kind == "STATUS":
        status, _, body = rest.partition(" ")
        return Reply(int(status), body)
    if kind == "ERROR":
        return Reply(error=rest)
    return Reply(error=f"exec 가 돌지 않았다(종료 {done.code}): {tail(done.err)}", asked=False)


def wait_for(
    ask: Callable[[], Reply], want: Callable[[Reply], bool], *, seconds: float
) -> tuple[Reply, list[str]]:
    """want 가 참이 될 때까지 0.5초마다 묻는다. 끝 응답과, 본 응답의 갈래를 본 차례로 돌려준다."""
    deadline = time.monotonic() + seconds
    seen: list[str] = []
    while True:
        reply = ask()
        if not seen or seen[-1] != reply.kind():
            seen.append(reply.kind())
        if want(reply) or time.monotonic() >= deadline:
            return reply, seen
        time.sleep(0.5)


def answered_by(who: str, token: str) -> Callable[[Reply], bool]:
    expected = f"{who}:{token}"
    return lambda reply: reply.status == 200 and reply.body == expected


def netns(stack: Stack, service: str) -> str:
    """그 컨테이너의 네트워크 이름공간(net:[inode]). 같은 값이면 같은 이름공간이다."""
    done = stack.compose("exec", "-T", service, "readlink", "/proc/self/ns/net", timeout=60)
    text = done.out.strip()
    if done.code == 0 and text.startswith("net:["):
        return text
    return f"?(종료 {done.code}: {tail(done.err, 1)})"


def proxy_log(stack: Stack, needles: list[str], *, seconds: float = 8.0) -> list[str]:
    """proxy 컨테이너의 기록에서 needles 가운데 하나라도 든 줄. needles 마다 줄이 생길 때까지
    기다린다."""
    deadline = time.monotonic() + seconds
    while True:
        done = stack.compose("logs", "--no-color", "--no-log-prefix", "proxy", timeout=60)
        lines = (done.out + "\n" + done.err).splitlines()
        complete = all(any(needle in line for line in lines) for needle in needles)
        if complete or time.monotonic() >= deadline:
            return [line for line in lines if any(needle in line for needle in needles)]
        time.sleep(0.5)


def logged_address(stack: Stack, rid: str) -> str:
    """접근 기록에서 그 rid 의 요청을 찾아 nginx 가 본 $remote_addr 를 돌려준다. 없으면 빈 글."""
    for line in proxy_log(stack, [f"rid={rid}"]):
        match = ACCESS.search(line)
        if match is not None and match.group(4) == rid:
            return match.group(1)
    return ""


def mask(address: str) -> str:
    """호스트의 실제 주소는 출력에 남기지 않는다. 루프백과 0.0.0.0 과 IPv6 는 그대로, 나머지는 앞 두
    마디만."""
    parts = address.split(".")
    if len(parts) != 4 or address.startswith("127.") or address == "0.0.0.0":
        return address
    return f"{parts[0]}.{parts[1]}.x.x"


@contextmanager
def case(rounds: Rounds, label: str) -> Generator[Slot]:
    """회차 하나를 세고 끝나면 한 줄로 낸다."""
    with rounds.round(label) as slot:
        yield slot
    entry = rounds.entries[-1]
    verdict = "측정" if entry.measured else "측정 아님"
    print(f"- [{verdict}] {entry.label} => {entry.result}", flush=True)


@dataclass(frozen=True)
class Context:
    token: str
    env: Mapping[str, str]
    rounds: Rounds

    def stack(self, *files: str, profiles: tuple[str, ...] = ()) -> Stack:
        return Stack(files, self.env, profiles)

    def down(self) -> None:
        """이 프로젝트의 컨테이너와 네트워크를 모두 지운다. 파일 없이 프로젝트 이름으로만 찾는다."""
        done = Stack((), self.env).compose("down", "-v", "--remove-orphans", "--timeout", "3")
        if done.code != 0:
            print(f"! down 실패(종료 {done.code}): {tail(done.err)}", flush=True)

    def reach_app(self) -> Callable[[Reply], bool]:
        return answered_by("app", self.token)

    def rid(self, name: str) -> str:
        return f"{self.token}-{name}-{secrets.token_hex(2)}"


def reach_text(reply: Reply, seen: list[str], *, reached: bool) -> str:
    if reached:
        return f"닿는다(본 차례 {seen})"
    return f"닿지 않는다(끝 응답 {reply.brief()}, 본 차례 {seen})"


# ---------- 항목 4 의 첫 갈래: 이름공간을 빌린 서비스에 ports ----------


def ports_on_app(ctx: Context) -> None:
    stack = ctx.stack("compose.ports-on-app.yml")
    port = PORTS["PORTS_ON_APP"]
    with case(ctx.rounds, "4 이름공간을 빌린 app 에 ports 를 직접 준 파일로 up -d") as current:
        done = stack.compose("up", "-d")
        if done.code == 0:
            reply, seen = wait_for(lambda: fetch(port, "/"), lambda r: r.status == 200, seconds=6)
            text = reach_text(reply, seen, reached=reply.status == 200)
            current.mark(measured=True, result=f"compose 가 받아들였다. 호스트에서 그 포트: {text}")
        else:
            # 포트와 네트워크 모드를 함께 든 거부만 측정이다. 포트가 이미 쓰여 난 실패와 가른다.
            words = done.err.lower()
            said = "port" in words and ("network mode" in words or "network_mode" in words)
            current.mark(measured=said, result=f"거부(종료 {done.code}): {tail(done.err, 2)}")
    ctx.down()


# ---------- 항목 1·4·5: 이름공간 공유 배치 ----------


def shared(ctx: Context, sections: set[str]) -> None:
    stack = ctx.stack("compose.shared.yml", profiles=("full",))
    up = stack.compose("up", "-d")
    reply, seen = wait_for(
        lambda: fetch(PORTS["PUBLIC"], "/marker.txt"), ctx.reach_app(), seconds=30
    )
    with case(
        ctx.rounds, "1 호스트 → proxy 가 127.0.0.1 에 연 포트 → 루프백에만 묶인 app"
    ) as current:
        now = boxes()
        proxy, app = now.get("proxy"), now.get("app")
        spaces = netns(stack, "proxy"), netns(stack, "app")
        borrowed = borrows(app, proxy)
        same = spaces[0] == spaces[1] and spaces[0].startswith("net:[")
        text = reach_text(reply, seen, reached=ctx.reach_app()(reply))
        mode = app.network_mode[:22] if app is not None else "?"
        detail = f"app 의 NetworkMode {mode}…, 이름공간 proxy {spaces[0]} app {spaces[1]}"
        note = "" if up.code == 0 else f"; up 종료 {up.code}: {tail(up.err)}"
        current.mark(measured=borrowed and same, result=f"{text}; {detail}{note}")
    versions = [
        tail(stack.compose("exec", "-T", "proxy", "nginx", "-v", timeout=60).err, 1),
        tail(stack.compose("exec", "-T", "app", "python", "--version", timeout=60).out, 1),
    ]
    print(f"  컨테이너 안의 판: {versions}", flush=True)
    if "1" in sections:
        item_1(ctx, stack)
    if "4" in sections:
        item_4(ctx, stack)
    if "5" in sections:
        item_5(ctx, stack)
    ctx.down()


def item_1(ctx: Context, stack: Stack) -> None:
    reach = ctx.reach_app()
    proxy = boxes().get("proxy")
    address = proxy.addresses[0] if proxy is not None and proxy.addresses else ""
    with case(ctx.rounds, "1 같은 이름공간의 다른 컨테이너(admin) → 127.0.0.1:8000") as current:
        reply = fetch_inside(stack, "admin", "127.0.0.1", 8000, "/marker.txt")
        text = "app 이 답한다" if reach(reply) else f"닿지 않는다({reply.brief()})"
        current.mark(measured=reply.asked, result=text)
    with case(ctx.rounds, "1 같은 이름공간에서 proxy 의 eth0 주소로 8000(app)") as current:
        control = fetch_inside(stack, "admin", address, 8080, "/marker.txt")
        reply = fetch_inside(stack, "admin", address, 8000, "/marker.txt")
        text = "닿는다" if reach(reply) else f"닿지 않는다({reply.brief()})"
        positive = "닿는다" if reach(control) else f"닿지 않는다({control.brief()})"
        result = f"{text}; 양성 대조인 같은 주소({address})의 nginx 8080 은 {positive}"
        current.mark(measured=reach(control) and reply.asked, result=result)


def host_addresses() -> list[str]:
    """이 호스트의 루프백이 아닌 IPv4 주소."""
    infos = socket.getaddrinfo(socket.gethostname(), None, family=socket.AF_INET)
    return sorted({str(info[4][0]) for info in infos if not str(info[4][0]).startswith("127.")})


def tcp_connect(host: str, port: int, *, timeout: float = 5.0) -> str:
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    with socket.socket(family, socket.SOCK_STREAM) as probe:
        probe.settimeout(timeout)
        try:
            probe.connect((host, port))
        except OSError as error:
            return type(error).__name__
    return "연결됨"


def listening_addresses(port: int) -> list[str]:
    """윈도 netstat 의 듣는 소켓 가운데 그 포트의 로컬 주소."""
    found: list[str] = []
    for protocol in ("TCP", "TCPv6"):
        done = run(["netstat", "-ano", "-p", protocol], timeout=60)
        for line in done.out.splitlines():
            words = line.split()
            listening = (
                len(words) >= 4 and words[0] == "TCP" and words[2] in ("0.0.0.0:0", "[::]:0")
            )
            if listening and words[1].endswith(f":{port}"):
                found.append(mask(words[1].rsplit(":", 1)[0]))
    return found


def item_4(ctx: Context, stack: Stack) -> None:
    reach = ctx.reach_app()
    proxy = boxes().get("proxy")
    published = dict(proxy.published) if proxy is not None else {}
    direct, admin = PORTS["DIRECT"], PORTS["ADMIN"]
    with case(ctx.rounds, "4 proxy 서비스가 이름공간의 8000(app 의 루프백)을 대신 발행") as current:
        reply, seen = wait_for(lambda: fetch(direct, "/marker.txt"), reach, seconds=5)
        bound = published.get("8000/tcp", ())
        text = reach_text(reply, seen, reached=reach(reply))
        current.mark(measured=bound == (f"127.0.0.1:{direct}",), result=f"{text}; 발행 {bound}")
    with case(ctx.rounds, "4 nginx 의 둘째 listen(8081)을 127.0.0.1 에만 발행 → admin") as current:
        want = answered_by("admin", ctx.token)
        reply, seen = wait_for(lambda: fetch(admin, "/marker.txt"), want, seconds=15)
        bound = published.get("8081/tcp", ())
        text = reach_text(reply, seen, reached=want(reply))
        current.mark(measured=bound == (f"127.0.0.1:{admin}",), result=f"{text}; 발행 {bound}")
    with case(
        ctx.rounds, "4 관리 포트에 호스트의 다른 주소로 TCP 연결(이 호스트 안에서)"
    ) as current:
        loopback = tcp_connect("127.0.0.1", admin)
        others = [*host_addresses(), "::1"]
        results = [f"{mask(address)} {tcp_connect(address, admin)}" for address in others]
        measured = loopback == "연결됨" and len(others) > 1
        current.mark(measured=measured, result=f"127.0.0.1 {loopback}; 다른 주소 {results}")
    if os.name == "nt":
        with case(ctx.rounds, "4 관리 포트를 듣는 호스트 소켓의 로컬 주소(netstat)") as current:
            found = listening_addresses(admin)
            current.mark(measured=bool(found), result=f"{found}")


def network_gateway() -> tuple[str, str]:
    """compose 기본 네트워크의 (서브넷, 게이트웨이)."""
    done = run(["docker", "network", "inspect", f"{PROJECT}_default"], timeout=60)
    if done.code != 0:
        return "?", "?"
    config = dig(parse(done.out), 0, "IPAM", "Config", 0)
    return as_text(dig(config, "Subnet"), "?"), as_text(dig(config, "Gateway"), "?")


def item_5(ctx: Context, stack: Stack) -> None:
    reach = ctx.reach_app()
    public = PORTS["PUBLIC"]
    zones = (
        ("기본값", "/limited-default", "per_addr_default"),
        ("limit_req_status 429", "/limited-429", "per_addr_429"),
    )
    for label, prefix, zone in zones:
        with case(ctx.rounds, f"5 한도를 넘긴 요청의 상태 코드({label})") as current:
            rids = [ctx.rid(f"burst{index}") for index in range(5)]
            replies = [fetch(public, f"{prefix}/marker.txt?rid={rid}") for rid in rids]
            pairs = zip(rids, replies, strict=True)
            rejected = [rid for rid, reply in pairs if not reach(reply)]
            lines = proxy_log(stack, rejected) if rejected else []
            limited = [line for line in lines if "limiting requests, excess" in line]
            logged = [rid for rid in rejected if any(rid in line for line in limited)]
            in_zone = all(f'zone "{zone}"' in line for line in limited)
            statuses = [reply.kind() for reply in replies]
            measured = reach(replies[0]) and bool(rejected) and logged == rejected and in_zone
            sign = f"거부 {len(rejected)}건 가운데 {len(logged)}건에 그 구역({zone})의 줄"
            result = f"연달아 5번의 상태 {statuses}; {sign}(limiting requests)"
            current.mark(measured=measured, result=result)
    subnet, gateway = network_gateway()
    now = boxes()
    proxy, peer = now.get("proxy"), now.get("peer")
    known = f"compose 네트워크 {subnet}, 게이트웨이 {gateway}"
    known += f", proxy {proxy.addresses if proxy else '?'}, peer {peer.addresses if peer else '?'}"
    print(f"  {known}", flush=True)
    host_address = ""
    with case(ctx.rounds, "5 호스트에서 발행 포트로 온 요청의 $remote_addr") as current:
        rid = ctx.rid("addr-host")
        reply = fetch(public, f"/marker.txt?rid={rid}")
        host_address = logged_address(stack, rid)
        where = "게이트웨이와 같다" if host_address == gateway else "게이트웨이와 다르다"
        measured = reach(reply) and host_address != ""
        current.mark(measured=measured, result=f"{host_address} ({where}. {known})")
    peer_address = ""
    with case(
        ctx.rounds, "5 같은 compose 네트워크의 peer 컨테이너에서 온 요청의 $remote_addr"
    ) as current:
        rid = ctx.rid("addr-peer")
        reply = fetch_inside(stack, "peer", "proxy", 8080, f"/marker.txt?rid={rid}")
        peer_address = logged_address(stack, rid)
        mine = peer is not None and peer_address in peer.addresses
        where = "peer 자신의 주소다" if mine else "peer 의 주소가 아니다"
        current.mark(
            measured=reach(reply) and peer_address != "", result=f"{peer_address} ({where})"
        )
    with case(ctx.rounds, "5 호스트가 한도를 넘긴 구역에 주소가 다른 peer 가 요청") as current:
        path = "/limited-429/marker.txt"
        fetch(public, f"{path}?rid={ctx.rid('fill')}")
        over = fetch(public, f"{path}?rid={ctx.rid('over')}")
        other = fetch_inside(stack, "peer", "proxy", 8080, f"{path}?rid={ctx.rid('peer')}")
        again = fetch_inside(stack, "peer", "proxy", 8080, f"{path}?rid={ctx.rid('peer2')}")
        still = fetch(public, f"{path}?rid={ctx.rid('still')}")
        distinct = host_address != "" and peer_address != "" and host_address != peer_address
        measured = over.status == 429 and still.status == 429 and other.asked and distinct
        result = f"호스트 둘째 {over.kind()}, peer 첫째 {other.kind()}, peer 둘째 {again.kind()}"
        current.mark(measured=measured, result=f"{result}, 그 뒤 호스트 {still.kind()}")


# ---------- 항목 2: 대조군 ----------


def bridge(ctx: Context) -> None:
    stack = ctx.stack("compose.bridge.yml")
    reach, reach_open = ctx.reach_app(), answered_by("open", ctx.token)
    up = stack.compose("up", "-d")
    if up.code != 0:
        print(f"! 대조군 up 실패(종료 {up.code}): {tail(up.err)}", flush=True)
    open_host, open_seen = wait_for(
        lambda: fetch(PORTS["BRIDGE_OPEN"], "/marker.txt"), reach_open, seconds=30
    )
    alive, _ = wait_for(
        lambda: fetch_inside(stack, "app", "127.0.0.1", 8000, "/marker.txt"), reach, seconds=15
    )
    open_inside = fetch_inside(stack, "client", "app-open", 8000, "/marker.txt")
    spaces = netns(stack, "app"), netns(stack, "client")
    apart = spaces[0] != spaces[1] and spaces[0].startswith("net:[")
    self_text = (
        "app 은 자기 루프백에서 답한다" if reach(alive) else f"app 자기 루프백 {alive.brief()}"
    )
    with case(
        ctx.rounds, "2 양성 대조: 0.0.0.0 에 묶은 app-open 을 호스트에서 발행 포트로"
    ) as current:
        text = reach_text(open_host, open_seen, reached=reach_open(open_host))
        current.mark(measured=True, result=text)
    with case(
        ctx.rounds, "2 양성 대조: 0.0.0.0 에 묶은 app-open 을 client 에서 서비스 이름으로"
    ) as current:
        text = "닿는다" if reach_open(open_inside) else f"닿지 않는다({open_inside.brief()})"
        current.mark(measured=open_inside.asked, result=text)
    with case(ctx.rounds, "2(가) 루프백에만 묶인 app 을 호스트에서 발행 포트로") as current:
        port = PORTS["BRIDGE_LOOPBACK"]
        reply, seen = wait_for(lambda: fetch(port, "/marker.txt"), reach, seconds=6)
        measured = reach_open(open_host) and reach(alive) and apart
        text = reach_text(reply, seen, reached=reach(reply))
        current.mark(measured=measured, result=f"{text}; {self_text}")
    with case(ctx.rounds, "2(나) 루프백에만 묶인 app 을 client 에서 서비스 이름으로") as current:
        reply = fetch_inside(stack, "client", "app", 8000, "/marker.txt")
        measured = reach_open(open_inside) and reach(alive) and apart and reply.asked
        text = "닿는다" if reach(reply) else f"닿지 않는다({reply.brief()})"
        detail = f"이름공간 app {spaces[0]} client {spaces[1]}"
        current.mark(measured=measured, result=f"{text}; {self_text}; {detail}")
    ctx.down()


# ---------- 덧붙인 항목 6: ::1 에만 묶인 서버 ----------


def loopback6(ctx: Context) -> None:
    stack = ctx.stack("compose.loopback6.yml")
    want = answered_by("app6", ctx.token)
    up = stack.compose("up", "-d")
    reply, seen = wait_for(lambda: fetch(PORTS["LOOPBACK6"], "/marker.txt"), want, seconds=20)
    with case(ctx.rounds, "6 ::1 에만 묶인 서버 ← proxy_pass http://[::1]:8002") as current:
        now = boxes()
        proxy, app6 = now.get("proxy"), now.get("app6")
        borrowed = borrows(app6, proxy)
        running = app6 is not None and app6.running
        inside = fetch_inside(stack, "app6", "::1", 8002, "/marker.txt")
        self_text = "자기 ::1 에서 답한다" if want(inside) else f"자기 ::1 {inside.brief()}"
        logs = stack.compose("logs", "--no-log-prefix", "--tail", "3", "app6", timeout=60)
        last = tail(logs.out + "\n" + logs.err, 1)
        state = "돌고 있다" if running else f"돌지 않는다(기록의 끝 줄: {last})"
        text = reach_text(reply, seen, reached=want(reply))
        result = f"{text}; app6 컨테이너는 {state}, {self_text}"
        current.mark(measured=borrowed and up.code == 0, result=result)
    ctx.down()


# ---------- 항목 3: proxy 를 다시 띄운다 ----------


@dataclass(frozen=True)
class Operation:
    """proxy 를 흔드는 compose 조작 하나. sign 은 proxy 가 실제로 어떻게 됐어야 측정인가다."""

    name: str
    args: tuple[str, ...]
    env: Mapping[str, str] = field(default_factory=dict[str, str])
    sign: str = "restarted"


VARIANTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("depends_on 없음", ()),
    ("depends_on 짧은 꼴", ("compose.depends.yml",)),
    ("depends_on 의 restart: true", ("compose.depends-restart.yml",)),
)
OPERATIONS = (
    Operation("restart proxy", ("restart", "proxy")),
    Operation(
        "up -d --force-recreate proxy", ("up", "-d", "--force-recreate", "proxy"), sign="recreated"
    ),
    Operation(
        "proxy 의 환경 값을 바꾼 뒤 up -d", ("up", "-d"), {"NETNS_PROXY_REV": "1"}, "recreated"
    ),
    Operation("restart(이름 없이 전부)", ("restart",)),
)
RECOVERIES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("restart app", ("restart", "app")),
    ("up -d", ("up", "-d")),
    ("up -d --force-recreate app", ("up", "-d", "--force-recreate", "app")),
)
AUTO_VARIANTS = (VARIANTS[0], VARIANTS[2])


def signed(sign: str, before: Box | None, after: Box | None) -> bool:
    """그 컨테이너가 그 조작으로 실제로 다시 시작됐거나 다시 만들어졌는가."""
    if before is None or after is None:
        return False
    if sign == "killed":
        # docker kill 뒤의 두 모습. 멈춘 채 남았거나(다시 띄워지지 않았다) 데몬이 다시 띄웠다.
        return after.id == before.id and (not after.running or after.started != before.started)
    if not after.running:
        return False
    if sign == "recreated":
        return after.id != before.id
    if sign == "auto":
        return after.id == before.id and after.restarts > before.restarts
    return after.id == before.id and after.started != before.started


def baseline(ctx: Context, stack: Stack) -> bool:
    """배치를 지우고 새로 띄워 app 에 닿는 것까지 본다."""
    ctx.down()
    up = stack.compose("up", "-d")
    if up.code != 0:
        print(f"! 기준선 up 실패(종료 {up.code}): {tail(up.err)}", flush=True)
        return False
    reply, _ = wait_for(lambda: fetch(PORTS["PUBLIC"], "/marker.txt"), ctx.reach_app(), seconds=30)
    return ctx.reach_app()(reply)


def observe(ctx: Context, stack: Stack) -> tuple[bool, str]:
    """공개 포트로 app 에 닿는지 8초까지 본다. 닿지 않으면 까닭을 가르는 관찰을 덧붙인다."""
    reach = ctx.reach_app()
    rid = ctx.rid("observe")
    path = f"/marker.txt?rid={rid}"
    reply, seen = wait_for(lambda: fetch(PORTS["PUBLIC"], path), reach, seconds=8)
    if reach(reply):
        return True, reach_text(reply, seen, reached=True)
    spaces = f"이름공간 proxy {netns(stack, 'proxy')} app {netns(stack, 'app')}"
    alive = fetch_inside(stack, "app", "127.0.0.1", 8000, "/marker.txt")
    self_text = (
        "app 은 자기 루프백에서 답한다" if reach(alive) else f"app 자기 루프백 {alive.brief()}"
    )
    failed = [line for line in proxy_log(stack, [rid], seconds=3) if "connect() failed" in line]
    found = re.search(r"connect\(\) failed \([^)]*\)", failed[-1]) if failed else None
    cause = found.group(0) if found is not None else "상류 연결 실패 줄 없음"
    text = reach_text(reply, seen, reached=False)
    return False, f"{text}; {spaces}; {self_text}; nginx 오류 기록: {cause}"


def disturb(
    ctx: Context,
    label: str,
    stack: Stack,
    acted: Stack,
    act: Callable[[], Done],
    sign: str,
    recoveries: tuple[tuple[str, tuple[str, ...]], ...] = RECOVERIES,
) -> None:
    """새로 띄운 배치에서 조작 하나를 하고 닿는지 본다. 닿지 않으면 회복 명령을 약한 것부터 친다."""
    broken = False
    with case(ctx.rounds, label) as current:
        if not baseline(ctx, stack):
            current.mark(
                measured=False, result="기준선(새로 띄운 배치에서 app 에 닿는다)이 서지 않았다"
            )
            return
        before = boxes()
        done = act()
        after = boxes()
        reached, text = observe(ctx, acted)
        happened = signed(sign, before.get("proxy"), after.get("proxy"))
        moved = f"proxy {change(before.get('proxy'), after.get('proxy'))}, "
        moved += f"app {change(before.get('app'), after.get('app'))}"
        said = "" if done.code == 0 else f" ({tail(done.err, 1)})"
        result = f"{text}; {moved}; 명령 종료 {done.code}{said}"
        current.mark(measured=happened, result=result)
        broken = happened and not reached
    if not broken:
        return
    for name, args in recoveries:
        reached = False
        with case(ctx.rounds, f"{label} → 회복 시도 `{name}`") as current:
            before = boxes()
            done = acted.compose(*args)
            after = boxes()
            reached, text = observe(ctx, acted)
            moved = f"proxy {change(before.get('proxy'), after.get('proxy'))}, "
            moved += f"app {change(before.get('app'), after.get('app'))}"
            said = "" if done.code == 0 else f" ({tail(done.err, 2)})"
            verdict = "회복됨" if reached else "회복 안 됨"
            result = f"{verdict}: {text}; {moved}; 명령 종료 {done.code}{said}"
            current.mark(measured=done.code != -1, result=result)
        if reached:
            return


NGINX_STOP = ("nginx", "-s", "stop")
# init: true 인 컨테이너의 1번 프로세스(tini)에 TERM 을 보내면 tini 가 자식에게 넘기고 함께 끝난다.
END_INIT = ("sh", "-c", "kill -TERM 1")


def restarted_by_daemon(service: str, before: Box | None, seconds: float) -> bool:
    """재시작 정책이 그 컨테이너를 다시 띄울 때(RestartCount 증가)까지 기다린다."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if signed("auto", before, boxes().get(service)):
            return True
        time.sleep(0.5)
    return False


def end_and_wait(stack: Stack, service: str, command: tuple[str, ...]) -> Done:
    """그 컨테이너 안에서 주 프로세스를 끝내는 명령을 치고, 재시작 정책이 다시 띄울 때까지 30초까지
    기다린다."""
    before = boxes().get(service)
    done = stack.compose("exec", "-T", service, *command, timeout=60)
    restarted_by_daemon(service, before, 30)
    return done


def docker_restart(service: str) -> Done:
    """compose 를 거치지 않고 Docker 에 바로 그 서비스의 컨테이너를 다시 시작시킨다."""
    box = boxes().get(service)
    if box is None:
        return Done(-1, "", f"{service} 컨테이너를 찾지 못했다")
    return run(["docker", "restart", box.id], timeout=120)


def docker_kill_and_wait(service: str) -> Done:
    """Docker 에 바로 그 서비스의 컨테이너를 죽이게 하고(SIGKILL), 재시작 정책이 다시 띄우는지
    10초까지 기다린다. 이 프로젝트의 라벨로 찾은 컨테이너만 죽인다."""
    box = boxes().get(service)
    if box is None:
        return Done(-1, "", f"{service} 컨테이너를 찾지 못했다")
    done = run(["docker", "kill", box.id], timeout=60)
    restarted_by_daemon(service, box, 10)
    return done


def resolved_dependency(stack: Stack, service: str = "app") -> str:
    """compose 가 파일을 푼 모델(`config`)에서 그 서비스의 depends_on. 적지 않은 것도 보인다."""
    done = stack.compose("config", "--format", "json", timeout=60)
    if done.code != 0:
        return f"config 실패(종료 {done.code}): {tail(done.err, 1)}"
    depends = dig(parse(done.out), "services", service, "depends_on")
    return json.dumps(depends, ensure_ascii=False, sort_keys=True)


def restarts(ctx: Context) -> None:
    for variant, files in VARIANTS:
        stack = ctx.stack("compose.shared.yml", *files)
        resolved = resolved_dependency(stack)
        print(f"  [{variant}] config 가 푼 app 의 depends_on: {resolved}", flush=True)
        for operation in OPERATIONS:
            acted = stack.with_env(operation.env)
            label = f"3 [{variant}] {operation.name}"
            args = operation.args
            disturb(ctx, label, stack, acted, lambda a=acted, g=args: a.compose(*g), operation.sign)
    # 위의 차례에서 `up -d` 는 실패한 `restart app` 이 app 을 멈춘 뒤에 친다. app 이 옛 이름공간에서
    # 아직 도는 채로 `up -d` 만 쳐도 회복되는지를 따로 본다.
    stack = ctx.stack("compose.shared.yml")
    recreate = OPERATIONS[1]
    label = f"3 [depends_on 없음] {recreate.name} (회복을 `up -d` 부터)"
    act = partial(stack.compose, *recreate.args)
    disturb(ctx, label, stack, stack, act, recreate.sign, RECOVERIES[1:])
    # compose 를 거치지 않는 조작 둘. app 을 다시 띄우는 것이 compose 인지 Docker 데몬인지를 가른다.
    for variant, files in AUTO_VARIANTS:
        stack = ctx.stack("compose.shared.yml", *files)
        label = f"3 [{variant}] docker restart <proxy>(compose 를 거치지 않고)"
        disturb(ctx, label, stack, stack, partial(docker_restart, "proxy"), "restarted")
    for variant, files in AUTO_VARIANTS:
        stack = ctx.stack("compose.shared.yml", *files, "compose.restart-policy.yml")
        label = f"3 [{variant} + restart: always] nginx 가 끝나 Docker 가 proxy 를 다시 띄움"
        disturb(ctx, label, stack, stack, partial(end_and_wait, stack, "proxy", NGINX_STOP), "auto")
    ctx.down()


# ---------- 항목 7: 이름공간의 주인이 holder 인 배치 ----------

HOLDER_FILE = "compose.holder.yml"
HOLDER_POLICY = "compose.holder-restart-policy.yml"
BORROWERS = ("proxy", "app", "admin")
HOLDER_SERVICES = ("holder", *BORROWERS)
HOLDER_RECOVERIES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("up -d", ("up", "-d")),
    ("restart proxy app admin", ("restart", *BORROWERS)),
    ("up -d --force-recreate proxy app admin", ("up", "-d", "--force-recreate", *BORROWERS)),
)
# 다시 읽기 갈래가 proxy 컨테이너 안의 설정 폴더에 써 넣는 location 하나. nginx.holder.conf 의
# include 가 그 폴더를 들인다.
RELOAD_SNIPPET = 'location = /reloaded {{ return 200 "reloaded:{token}"; }}\n'
WRITE_SNIPPET = "mkdir -p /tmp/probe-extra && cat > /tmp/probe-extra/reloaded.conf"


def brief_change(before: Box | None, after: Box | None) -> str:
    """change 의 짧은 꼴. '그대로'는 같은 컨테이너 id 에 같은 State.StartedAt 이다."""
    if after is None:
        return "없어짐"
    if before is None:
        return "새로 생김"
    if after.id != before.id:
        return "다시 만들어짐"
    state = "" if after.running else "(지금 멈춤)"
    if after.started != before.started:
        return f"다시 시작됨{state}"
    return f"그대로{state}"


def moves(before: Mapping[str, Box], after: Mapping[str, Box], names: tuple[str, ...]) -> str:
    return ", ".join(f"{name} {brief_change(before.get(name), after.get(name))}" for name in names)


def holder_settle(ctx: Context, stack: Stack) -> bool:
    """배치를 지우고 새로 띄워, 공개 포트로 app 에, 관리 포트로 admin 에 닿는 것까지 본다."""
    ctx.down()
    up = stack.compose("up", "-d")
    if up.code != 0:
        print(f"! 기준선 up 실패(종료 {up.code}): {tail(up.err)}", flush=True)
        return False
    reach, reach_admin = ctx.reach_app(), answered_by("admin", ctx.token)
    reply, _ = wait_for(lambda: fetch(PORTS["PUBLIC"], "/marker.txt"), reach, seconds=30)
    admin, _ = wait_for(lambda: fetch(PORTS["ADMIN"], "/marker.txt"), reach_admin, seconds=15)
    return reach(reply) and reach_admin(admin)


def holder_view(ctx: Context, stack: Stack) -> tuple[bool, str]:
    """공개 포트로 app 에, 관리 포트로 admin 에 닿는지 8초까지 본다. 닿지 않으면 네 컨테이너의
    이름공간과, 빌린 셋이 저희끼리는 닿는지(admin 컨테이너에서 nginx 를 거쳐 app)를 덧붙인다."""
    reach, reach_admin = ctx.reach_app(), answered_by("admin", ctx.token)
    reply, seen = wait_for(lambda: fetch(PORTS["PUBLIC"], "/marker.txt"), reach, seconds=8)
    patience = 8 if reach(reply) else 1
    admin, admin_seen = wait_for(
        lambda: fetch(PORTS["ADMIN"], "/marker.txt"), reach_admin, seconds=patience
    )
    text = f"app 에 {reach_text(reply, seen, reached=reach(reply))}, "
    text += f"admin 에 {reach_text(admin, admin_seen, reached=reach_admin(admin))}"
    if reach(reply) and reach_admin(admin):
        return True, text
    spaces = ", ".join(f"{name} {netns(stack, name)}" for name in HOLDER_SERVICES)
    inner = fetch_inside(stack, "admin", "127.0.0.1", 8080, "/marker.txt")
    among = "닿는다" if reach(inner) else f"닿지 않는다({inner.brief()})"
    return False, f"{text}; 이름공간 {spaces}; admin 컨테이너 안에서 nginx 를 거쳐 app 에 {among}"


def holder_case(
    ctx: Context,
    label: str,
    stack: Stack,
    acted: Stack,
    act: Callable[[], Done],
    target: str,
    sign: str,
) -> None:
    """새로 띄운 holder 배치에서 조작 하나를 하고, 닿는지와 네 컨테이너가 어떻게 됐는지를 본다.
    표지는 target 컨테이너가 그 조작으로 실제로 바뀐 것이다. 닿지 않으면 회복 명령을 차례로 친다."""
    broken = False
    with case(ctx.rounds, label) as current:
        if not holder_settle(ctx, stack):
            current.mark(measured=False, result="기준선(새로 띄운 배치에서 닿는다)이 서지 않았다")
            return
        before = boxes()
        done = act()
        after = boxes()
        reached, text = holder_view(ctx, acted)
        happened = signed(sign, before.get(target), after.get(target))
        counted = f"{restarts_of(before, target)}→{restarts_of(after, target)}"
        said = "" if done.code == 0 else f" ({tail(done.err, 1)})"
        result = f"{text}; {moves(before, after, HOLDER_SERVICES)}"
        result += f"; {target} 의 RestartCount {counted}; 명령 종료 {done.code}{said}"
        current.mark(measured=happened, result=result)
        broken = happened and not reached
    if not broken:
        return
    for name, args in HOLDER_RECOVERIES:
        reached = False
        with case(ctx.rounds, f"{label} → 회복 시도 `{name}`") as current:
            before = boxes()
            done = acted.compose(*args)
            after = boxes()
            reached, text = holder_view(ctx, acted)
            said = "" if done.code == 0 else f" ({tail(done.err, 2)})"
            verdict = "회복됨" if reached else "회복 안 됨"
            result = f"{verdict}: {text}; {moves(before, after, HOLDER_SERVICES)}"
            current.mark(measured=done.code != -1, result=f"{result}; 명령 종료 {done.code}{said}")
        if reached:
            return


def restarts_of(found: Mapping[str, Box], service: str) -> str:
    box = found.get(service)
    return str(box.restarts) if box is not None else "?"


def holder_item_1(ctx: Context, stack: Stack) -> None:
    label = "7.1 호스트 → holder 가 127.0.0.1 에 연 포트 → nginx → 루프백에만 묶인 app, 둘째 listen"
    with case(ctx.rounds, f"{label} → admin") as current:
        holder_settle(ctx, stack)
        now = boxes()
        owner = now.get("holder")
        borrowed = all(borrows(now.get(name), owner) for name in BORROWERS)
        spaces = [netns(stack, name) for name in HOLDER_SERVICES]
        same = len(set(spaces)) == 1 and spaces[0].startswith("net:[")
        _, text = holder_view(ctx, stack)
        published = dict(owner.published) if owner is not None else {}
        detail = (
            f"빌린 셋의 NetworkMode 가 container:<holder id> {'맞다' if borrowed else '아니다'}"
        )
        detail += f", 이름공간(holder, proxy, app, admin) {spaces}, holder 의 발행 {published}"
        current.mark(measured=borrowed and same, result=f"{text}; {detail}")


def reload_case(
    ctx: Context,
    label: str,
    stack: Stack,
    settle: Callable[[], bool],
    view: Callable[[], tuple[bool, str]],
    names: tuple[str, ...],
) -> None:
    """새 location 하나를 proxy 컨테이너 안의 설정 폴더에 써 넣고 `nginx -s reload` 를 친다.
    표지는 그 location 이 다시 읽기 전에는 답하지 않고(app 으로 넘어간다) 뒤에는 새 설정의 답을
    내는 것이다."""
    want = answered_by("reloaded", ctx.token)
    with case(ctx.rounds, label) as current:
        if not settle():
            current.mark(measured=False, result="기준선(새로 띄운 배치에서 닿는다)이 서지 않았다")
            return
        snippet = RELOAD_SNIPPET.format(token=ctx.token)
        wrote = stack.compose(
            "exec", "-T", "proxy", "sh", "-c", WRITE_SNIPPET, stdin=snippet, timeout=60
        )
        early = fetch(PORTS["PUBLIC"], "/reloaded")
        before = boxes()
        done = stack.compose("exec", "-T", "proxy", "nginx", "-s", "reload", timeout=60)
        late, seen = wait_for(lambda: fetch(PORTS["PUBLIC"], "/reloaded"), want, seconds=8)
        after = boxes()
        _, text = view()
        measured = wrote.code == 0 and done.code == 0 and not want(early) and want(late)
        effect = f"새 location 이 다시 읽기 전 {early.kind()}, 뒤 {late.kind()}(본 차례 {seen})"
        result = f"{effect}; {text}; {moves(before, after, names)}; 명령 종료 {done.code}"
        current.mark(measured=measured, result=result)


def holder(ctx: Context) -> None:
    stack = ctx.stack(HOLDER_FILE)
    policy = ctx.stack(HOLDER_FILE, HOLDER_POLICY)
    for name in BORROWERS:
        resolved = resolved_dependency(stack, name)
        print(f"  [holder 배치] config 가 푼 {name} 의 depends_on: {resolved}", flush=True)
    holder_item_1(ctx, stack)
    # 7.2 proxy 를 흔든다. 항목 3 의 조작 여섯이다.
    for operation in OPERATIONS:
        acted = stack.with_env(operation.env)
        act = partial(acted.compose, *operation.args)
        holder_case(ctx, f"7.2 {operation.name}", stack, acted, act, "proxy", operation.sign)
    label = "7.2 docker restart <proxy>(compose 를 거치지 않고)"
    holder_case(ctx, label, stack, stack, partial(docker_restart, "proxy"), "proxy", "restarted")
    label = "7.2 [restart: always] nginx 가 끝나 Docker 가 proxy 를 다시 띄움"
    act = partial(end_and_wait, policy, "proxy", NGINX_STOP)
    holder_case(ctx, label, policy, policy, act, "proxy", "auto")
    # 7.3 holder 를 흔든다. docker kill 은 재시작 정책이 다시 띄우지 않을 수 있어, 프로세스가 스스로
    # 끝나는 갈래를 양성 대조로 함께 둔다(정책이 실제로 다시 띄우는 것을 본다).
    shaken: tuple[tuple[str, Stack, Callable[[], Done], str], ...] = (
        ("restart holder", stack, partial(stack.compose, "restart", "holder"), "restarted"),
        (
            "docker restart <holder>(compose 를 거치지 않고)",
            stack,
            partial(docker_restart, "holder"),
            "restarted",
        ),
        (
            "[restart: always] docker kill <holder>",
            policy,
            partial(docker_kill_and_wait, "holder"),
            "killed",
        ),
        (
            "[restart: always] holder 의 프로세스가 끝나 Docker 가 holder 를 다시 띄움",
            policy,
            partial(end_and_wait, policy, "holder", END_INIT),
            "auto",
        ),
        (
            "up -d --force-recreate holder",
            stack,
            partial(stack.compose, "up", "-d", "--force-recreate", "holder"),
            "recreated",
        ),
    )
    for name, used, act, sign in shaken:
        holder_case(ctx, f"7.3 {name}", used, used, act, "holder", sign)
    # 7.4 app 하나만 다시 만든다. 뒤의 것은 판을 올리는 장면에 가깝게 app 의 구성을 바꾼 뒤
    # `up -d` 를 친다.
    act = partial(stack.compose, "up", "-d", "--force-recreate", "app")
    holder_case(ctx, "7.4 up -d --force-recreate app", stack, stack, act, "app", "recreated")
    bumped = stack.with_env({"NETNS_APP_REV": "1"})
    act = partial(bumped.compose, "up", "-d")
    holder_case(ctx, "7.4 app 의 환경 값을 바꾼 뒤 up -d", stack, bumped, act, "app", "recreated")
    # 7.5 컨테이너를 다시 띄우지 않고 nginx 설정을 다시 읽는다. 주인이 proxy 인 배치에서도 한 번
    # 본다.
    reload_case(
        ctx,
        "7.5 [holder 배치] nginx -s reload",
        stack,
        partial(holder_settle, ctx, stack),
        partial(holder_view, ctx, stack),
        HOLDER_SERVICES,
    )
    owner = ctx.stack("compose.shared.yml", "compose.reload-conf.yml")
    reload_case(
        ctx,
        "7.5 [proxy 가 주인인 배치] nginx -s reload",
        owner,
        partial(baseline, ctx, owner),
        partial(observe, ctx, owner),
        ("proxy", "app"),
    )
    ctx.down()


# ---------- 본체 ----------


def port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def preflight(ctx: Context) -> bool:
    """데몬, compose, 이미지, 포트를 본다. 하나라도 없으면 아무것도 띄우지 않고 멈춘다."""
    version = run(["docker", "version", "--format", "{{json .}}"], timeout=60)
    if version.code != 0:
        print(f"Docker 데몬에 닿지 않는다(종료 {version.code}): {tail(version.err)}")
        return False
    facts = parse(version.out)
    platform = as_text(dig(facts, "Server", "Platform", "Name"), "?")
    client = as_text(dig(facts, "Client", "Version"), "?")
    server = as_text(dig(facts, "Server", "Version"), "?")
    print(f"docker 클라이언트 {client}, 서버 {server} ({platform})")
    print(f"compose {run(['docker', 'compose', 'version', '--short'], timeout=60).out.strip()}")
    info = run(["docker", "info", "--format", "{{json .}}"], timeout=60)
    if info.code == 0:
        about = parse(info.out)
        keys = ("OperatingSystem", "KernelVersion", "OSType", "Architecture")
        print("docker info: " + ", ".join(f"{key} {as_text(dig(about, key), '?')}" for key in keys))
    for reference in (ctx.env["NETNS_NGINX_IMAGE"], ctx.env["NETNS_PYTHON_IMAGE"]):
        image = run(["docker", "image", "inspect", reference], timeout=60)
        if image.code != 0:
            print(f"이미지가 로컬에 없다(받지 않는다): {reference}")
            return False
        found = dig(parse(image.out), 0)
        settings = (as_text(item) for item in as_list(dig(found, "Config", "Env")))
        marks = [item for item in settings if "_VERSION=" in item]
        tags = [as_text(tag) for tag in as_list(dig(found, "RepoTags"))]
        print(f"이미지 {reference}: id {as_text(dig(found, 'Id'))}, 태그 {tags}, {marks}")
    ctx.down()
    busy = [port for port in PORTS.values() if not port_free(port)]
    if busy:
        print(f"호스트 포트가 쓰이고 있다: {busy}")
        return False
    return True


def main() -> int:
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--sections", default="1,2,3,4,5,6,7")
    parser.add_argument("--nginx-image", default=NGINX_IMAGE)
    parser.add_argument("--python-image", default=PYTHON_IMAGE)
    parser.add_argument("--work", type=Path)
    args = parser.parse_args()
    sections = set(str(args.sections).split(","))
    work = Path(tempfile.mkdtemp(prefix="netns-probe-", dir=args.work))
    _raw.append(work / "raw.log")
    token = secrets.token_hex(4)
    env = {
        "NETNS_NGINX_IMAGE": str(args.nginx_image),
        "NETNS_PYTHON_IMAGE": str(args.python_image),
        "NETNS_TOKEN": token,
        **{f"NETNS_{name}_PORT": str(port) for name, port in PORTS.items()},
    }
    ctx = Context(token, env, Rounds())
    print(f"원본 출력 {_raw[0]}, 회차 토큰 {token}, 호스트 {sys.platform}")
    if not preflight(ctx):
        return 2
    try:
        if "4" in sections:
            ports_on_app(ctx)
        if sections & {"1", "4", "5"}:
            shared(ctx, sections)
        if "2" in sections:
            bridge(ctx)
        if "6" in sections:
            loopback6(ctx)
        if "3" in sections:
            restarts(ctx)
        if "7" in sections:
            holder(ctx)
    finally:
        ctx.down()
    # 회차의 결과는 위에 한 줄씩 냈다. 여기서는 셈과 측정이 아닌 회차만 낸다(결과 갈래별 수는 뺀다).
    closing = [line for line in ctx.rounds.summary().splitlines() if not line.startswith("결과: ")]
    print("\n".join(closing))
    return ctx.rounds.exit_code()


if __name__ == "__main__":
    sys.exit(main())
