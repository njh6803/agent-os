"""release-image 단독 배포의 가장자리를 리눅스의 Docker Engine 에서 잰다. 프록시가 보는 접속 주소,
주소별 빈도 제한, 127.0.0.1 에만 발행한 포트, 잘못 발행한 포트, TLS·80·404 와 root 가 아닌 nginx,
호스트 폴더의 쓰기 권한이다. 결정은 하지 않고 회차마다 본 것을 한 줄씩 낸다. 항목 7 은 안쪽
네트워크에 IPv6 를 켠 배치에서 같은 L2 의 이웃이 서버를 경유해 컨테이너의 IPv6 주소로 바로 거는
길이고, 항목 8 은 443 과 80 을 IPv4 에만 발행한 배치다(둘 다 기본 `--sections` 에는 들지 않는다).

저장소 루트에서

    uv run python .scratch/release-image/probes/bridge_edge/run.py
        [--sections 1,2,3,4,5,6] [--engines 29.9.2,28.0.0,27.5.1] [--modes on,off]
        [--work <원본 출력을 둘 폴더>] [--keep]
    uv run python .scratch/release-image/probes/bridge_edge/run.py
        --sections 7,8 --engines 29.9.2,28.3.3,28.0.0,27.5.1

어떻게 재나. Docker Desktop 의 포트 발행은 리눅스 서버의 Docker Engine 과 달라서, 공식
`docker:<판>-dind` 이미지를 `--privileged` 로 띄운 컨테이너를 "리눅스 서버"로 쓴다(그 안에 독립된
Docker Engine 이 돈다). 바깥에 브리지 네트워크 `ri-edge-lan` 을 만들어 서버와 "이웃 기기" 둘(n1,
n2)을 붙인다. 이웃은 서버와 같은 L2 구간의 다른 호스트이고, 이웃에서 서버의 주소로 건 요청이 서버
밖의 다른 기기에서 온 요청이다. 항목 3 을 돌 때는 루프백 경로를 서버로 돌린 이웃 n3 을 하나 더
붙인다. 서버 안에서는 같은 폴더의 compose.yml(시제품)과
compose.probe.yml(측정 전용 덧씌움)을 띄운다. 요청은 이웃 컨테이너와 서버 자신(서버 안에서 호스트
네트워크로 띄운 컨테이너)에서 client.py 가 보낸다.

필요한 것. 도는 Docker 데몬과, 로컬에 이미 있는 이미지(아래 DIND, NGINX_IMAGE, NGINX_UNPRIV_IMAGE,
PYTHON_IMAGE 의 digest 참조. 이 스크립트는 받지 않는다). 호스트 포트는 쓰지 않는다. 만드는 것은
이름이 `ri-edge-` 로 시작하고 라벨 `ri-edge-probe` 가 붙은 컨테이너와 네트워크, 그리고 이미지 태그
셋 (`ri-edge-*:pinned`)이다. 시작과 끝에 그 라벨의 것만 지운다. 시험용 인증서와 키는 서버 컨테이너
안에서 만들고 컨테이너와 함께 사라진다. 인증서(공개 쪽)만 --work 폴더를 거쳐 이웃에 건넨 뒤 지운다.

시나리오. 엔진 판(--engines)마다 userland-proxy 를 켠 때와 끈 때(--modes)를 한 번씩 띄운다. 첫
엔진의 켠 때가 전체 항목을 돌고, 나머지는 항목 1(접속 주소), 3(127.0.0.1 발행과 경유 공격), 4(잘못
발행)만 돈다. 항목 4 는 켠 때만 돈다. 항목 7 과 8 은 `--sections` 에 그 번호를 주면 고른 엔진과
모드마다 돈다.

항목마다 무엇을 표지로 보는가(표지가 없는 회차는 측정 아님으로 세고 종료 코드가 1 이다)
0. 서버와 배치가 떴다. 안쪽 엔진의 판이 고른 판과 같고, docker-proxy 프로세스가 있는지가 고른
   userland-proxy 와 맞고, 서버 자신에서 프록시를 거쳐 뒷단의 답이 온다.
1. 접속 주소. 뒷단이 받은 X-Forwarded-For(프록시가 $remote_addr 로 덮어쓴 값)와 프록시 접근 기록의
   $remote_addr 가 같은 요청(rid)에서 같다. 닿지 않은 회차는 HTTP 응답이 없고 접근 기록에 그 rid
   의 줄이 없으며, 같은 길의 대조(IPv4 는 n1 이 서버의 443 에 TCP 로 닿는다, IPv6 는 n1 이 서버
   호스트의 [::] 대조 포트에 닿는다)가 섰을 때만 측정이다. 응답이나 그 줄이 있는데 serve 의 답이
   아니면(프록시가 낸 502 등) 프록시까지는 닿은 것이고, 주소를 견줄 표지(뒷단이 받은
   X-Forwarded-For)가 없어 측정 아님이다. 그 회차는 접근 기록의 $remote_addr 를 함께 적는다.
2. 빈도 제한. 보낸 요청마다 접근 기록의 줄이 있고(프록시에 닿았다), 거부된 요청마다 오류 기록에 그
   구역의 `limiting requests` 줄이 있다(거부가 빈도 제한의 것이다). 주소별로 따로 세는지는 n1 과 n2
   가 동시에 한도를 넘기게 해서 각자 `1+burst` 개를 받는지로 본다. 한 통에서 세면 둘의 합이
   그만큼이어야 한다. 그 해석의 양성 대조가 "뭉침" 회차다(두 이웃이 같은 주소로 보이는 길에서는 합이
   `1+burst`).
3. 127.0.0.1 발행. 서버 자신에서 127.0.0.1:3000 이 관리 화면 대역의 답을 낸다(양성 대조). 경유
   공격은 둘이다. A 는 n1 이 안쪽 대역(컨테이너 주소)으로 가는 경로를 서버로 잡고 컨테이너 주소로
   건다. B 는 n3 이 목적지 127.0.0.1 을 서버로 보내 서버의 127.0.0.1:3000 에 건다. 회차의 표지는
   이웃의 경로가 실제로 서버를 경유하고(`ip route get`), 공격 패킷이 서버의 eth0 에 닿았고(이
   스크립트가 raw PREROUTING 맨 앞에 넣은 셈 전용 규칙의 패킷 수가 늘었다), 그 대상이 답한다는
   양성 대조가 섰다는 것이다. A 의 대조는 서버 자신에서 그 컨테이너 주소와 포트로 걸어 기대한
   대역이 답하는 것이고, B 의 대조는 위 서버 자신의 127.0.0.1:3000 이다. 막힌 회차에는 그 사이
   패킷 수가 늘어난 DROP 규칙을 함께 적어, 누가 막았는지를 가른다.
4. 잘못 발행. 덧씌움 전에는 이웃에서 서버의 8000 이 닿지 않고, 덧씌운 뒤 `docker port` 가
   0.0.0.0:8000 을 보인다.
5. TLS 와 경로. 이웃이 받은 인증서의 지문이 서버에서 만든 인증서의 지문과 같다. 404 와 308 과 400 은
   응답에 뒷단의 표지(X-Stub)가 없다. root 가 아님은 컨테이너의 모든 프로세스(`docker top`)의
   `/proc/<pid>/status` 에 적힌 실제·유효 uid 다.
6. 쓰기 권한. 컨테이너 안의 `id -u` 가 10001 이고, 실패한 회차는 stderr 에 `Permission denied` 가
   있다.
7. IPv6 경유. 배치(compose.ipv6.yml 과 compose.ipv6-listen.yml 을 덧씌움)는 안쪽 네트워크의
   EnableIPv6 가 참이고 관리 화면·serve·프록시에 안쪽 IPv6 대역의 주소가 있을 때 떴다고 센다.
   대상마다 서버 자신에서 그 컨테이너의 IPv6 주소로 걸어 그 대역이 답하는 것이 양성 대조다(대역이
   `::` 에도 듣는다). 경유 공격은 n1 이 안쪽 IPv6 대역으로 가는 경로를 서버의 바깥 IPv6 주소로 잡고
   컨테이너의 IPv6 주소로 건다. 회차의 표지는 n1 의 경로가 서버를 경유하고(`ip -6 route get`),
   공격 패킷이 서버의 eth0 에 닿았고(ip6tables raw PREROUTING 맨 앞에 넣은 셈 전용 규칙의 패킷 수가
   늘었다), 그 대상의 양성 대조가 섰다는 것이다. 막힌 회차에는 패킷 수가 늘어난 ip6tables 의 DROP
   규칙을 적는다. 막은 것이 엔진의 규칙인지는 보호를 끈 네트워크
   (`gateway_mode_ipv6=nat-unprotected`)의 컨테이너에 같은 길로 닿는지로 가른다. 서버 주소로 거는
   길(n1 → 서버의 IPv6 :3000·:8000)은 서버 자신의 127.0.0.1:3000 이 관리 화면의 답을 내고 n1 이
   서버의 [::] 대조 포트에 닿았을 때만 측정이다.
8. IPv4 에만 발행. 배치(compose.v4-publish.yml 을 덧씌움)는 `docker port` 가 0.0.0.0 의 443 과 80
   두 줄뿐일 때 떴다고 센다. 그 배치에서 항목 1 의 갈래를 다시 돈다(표지는 항목 1 과 같다). 닿지
   않는 IPv6 회차의 대조는 이 배치에서 다시 띄운 [::] 대조 포트에 n1 과 n2 가 모두 닿은 것이다.
   서버 안의 443·80 이 IPv6 쪽에 열렸는지는 듣는 소켓, docker-proxy 의 인자, ip6tables nat 의 DNAT
   로 보고, 같은 방법이 IPv4 쪽 443 을 볼 때만 측정이다. 시제품 배치에서 같은 관찰을 먼저 해 둔다.

못 보는 것. 실제 서버와의 차이는 README.md 의 "한계"에 있다. 바깥 "LAN" 이 Docker Desktop 의
브리지이고, 서버가 컨테이너라 커널을 Docker Desktop 의 VM 과 함께 쓰며, dind 안에서는 IP 포워딩이
처음부터 켜져 있어 Docker 가 FORWARD 정책을 DROP 으로 바꾸지 않는다(그래서 항목 3 은 정책을 두
값으로 바꿔 가며 잰다). rootless Docker, firewalld·ufw 와의 조합, 실제 뒷단 이미지, 데몬을 다시 켠
뒤는 재지 않는다.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import re
import secrets
import subprocess
import sys
import tempfile
import time
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds, Slot  # noqa: E402

LABEL = "ri-edge-probe"
LAN = "ri-edge-lan"
SERVER = "ri-edge-server"
N1 = "ri-edge-n1"
N2 = "ri-edge-n2"
N3 = "ri-edge-n3"
NEIGHBOR3 = "10.77.0.23"
LOOPBACK = "127.0.0.1/32"
SELF = "self"
PROJECT = "ri-edge"

LAN4_SUBNET = "10.77.0.0/24"
LAN4_GATEWAY = "10.77.0.1"
LAN6_SUBNET = "fd00:77::/64"
SERVER4 = "10.77.0.10"
SERVER6 = "fd00:77::10"
NEIGHBOR4 = {N1: "10.77.0.21", N2: "10.77.0.22"}
NEIGHBOR6 = {N1: "fd00:77::21", N2: "fd00:77::22"}
INNER4_SUBNET = "172.30.0.0/24"
OPEN4_SUBNET = "172.31.0.0/24"
V6_CONTROL_PORT = 39459

# 2026-11-13 에 Docker Hub 에서 받은 공식 이미지의 색인 digest 다.
DIND = {
    "29.9.2": "docker@sha256:9e79b879b177fbd72c34376a3dd3d91747da5db49e1f560f76aea59561471977",
    "28.3.3": "docker@sha256:a56b3bdde89315ed2cc0e4906e582b5033d93bf20d9cb9510c2cdd4e7f7690b1",
    "28.0.0": "docker@sha256:0a9c58ebc9f86e5af35e4330f6c738dc64fce3ca2e2574b5becdfb88765b308b",
    "27.5.1": "docker@sha256:aa3df78ecf320f5fafdce71c659f1629e96e9de0968305fe1de670e0ca9176ce",
}
HELPER_IMAGE = DIND["29.9.2"]  # 이웃의 경로를 고치는 `ip` 를 빌려 쓴다
# nginx:1.30.6-alpine, nginxinc/nginx-unprivileged:1.30.6-alpine, python:3.12.10-slim-bookworm
NGINX_IMAGE = "nginx@sha256:583b7f2fce1cdb8da5ad5c39ebd3c33b98b87d493190e548bdee1fa8c619c311"
NGINX_UNPRIV_IMAGE = (
    "nginxinc/nginx-unprivileged@sha256:"
    "f5116ed4606f3eb015dd4a8e28cb9b351476dc0ad4bc6e9f93b19cec130cdf03"
)
PYTHON_IMAGE = "python@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db"
NGINX_TAG = "ri-edge-nginx:pinned"
NGINX_UNPRIV_TAG = "ri-edge-nginx-unpriv:pinned"
PYTHON_TAG = "ri-edge-python:pinned"
TAGS = {NGINX_TAG: NGINX_IMAGE, NGINX_UNPRIV_TAG: NGINX_UNPRIV_IMAGE, PYTHON_TAG: PYTHON_IMAGE}

BASE = ("compose.yml", "compose.probe.yml")
TLS_MAIN = "/probe-tls/main"
# 배포 안내에 적을 후보 명령 그대로다(이름과 주소만 시험용). 서버 컨테이너 안에서 돈다.
CERT_COMMAND = (
    "openssl req -x509 -newkey rsa:2048 -nodes -days 30 "
    "-keyout privkey.pem -out fullchain.pem -subj /CN=edge.test "
    "-addext subjectAltName=DNS:edge.test,IP:10.77.0.10,IP:127.0.0.1,IP:fd00:77::10,IP:::1"
)
CERT_SCRIPT = f"""set -e
mkdir -p {TLS_MAIN} /probe-tls/root600 /probe-tls/own101
cd {TLS_MAIN}
{CERT_COMMAND} 2>/dev/null
cp fullchain.pem privkey.pem /probe-tls/root600/
cp fullchain.pem privkey.pem /probe-tls/own101/
chgrp 101 {TLS_MAIN}/privkey.pem
chmod 640 {TLS_MAIN}/privkey.pem
chmod 600 /probe-tls/root600/privkey.pem
chown 101:101 /probe-tls/own101/privkey.pem
chmod 600 /probe-tls/own101/privkey.pem
"""

ACCESS = re.compile(r'^(\S+) \[[^\]]+\] "([^"]*)" (\d{3}) limit=(\S+) up=(\S+)')
RULE = re.compile(r"^\[(\d+):\d+\] (.+)$")
POLICY = re.compile(r"^:(\S+) (\S+) \[(\d+):\d+\]$")
# (구역 이름, 분당 횟수, burst)
COMBOS = (("r10b0", 10, 0), ("r10b5", 10, 5), ("r30b10", 30, 10), ("r60b20", 60, 20))
TOKEN_RATE, TOKEN_BURST = 30, 10  # nginx/edge.conf 의 portal_token 구역과 같아야 한다

_raw: list[Path] = []


def raw(title: str, text: str) -> None:
    if _raw:
        with _raw[0].open("a", encoding="utf-8") as out:
            out.write(f"\n===== {time.strftime('%H:%M:%S')} {title}\n{text}\n")


def tail(text: str, count: int = 3) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " / ".join(lines[-count:])


# docker 와 client.py 가 내는 JSON 을 읽는 자리. 모양이 기대와 다르면 예외 대신 빈 값이 나오고, 그
# 빈 값으로는 아래의 표지가 서지 않아 측정 아님으로 세어진다.
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


def as_number(value: Json) -> float:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0.0


@dataclass(frozen=True)
class Done:
    code: int
    out: str
    err: str

    @property
    def both(self) -> str:
        return f"{self.out}\n{self.err}"


def run(argv: list[str], *, timeout: float = 240) -> Done:
    """명령 하나. 표준 입력은 늘 닫힌 파이프다. 시간을 넘기면 종료 코드 -1."""
    try:
        completed = subprocess.run(
            argv,
            cwd=HERE,
            input="",
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


def docker(*args: str, timeout: float = 240) -> Done:
    return run(["docker", *args], timeout=timeout)


def server(*args: str, env: Mapping[str, str] | None = None, timeout: float = 240) -> Done:
    """서버(dind 컨테이너) 안에서 도는 명령 하나."""
    flags = [item for key, value in (env or {}).items() for item in ("-e", f"{key}={value}")]
    return docker("exec", *flags, SERVER, *args, timeout=timeout)


def inner(*args: str, env: Mapping[str, str] | None = None, timeout: float = 240) -> Done:
    """서버 안의 Docker Engine 에 내리는 docker 명령 하나."""
    return server("docker", *args, env=env, timeout=timeout)


def compose(files: tuple[str, ...], *args: str, tls: str = TLS_MAIN, timeout: float = 240) -> Done:
    argv = ["compose", "--ansi", "never", "--progress", "plain", "-p", PROJECT]
    for name in files:
        argv += ["-f", f"/probe/{name}"]
    return inner(*argv, *args, env={"RI_EDGE_TLS_DIR": tls}, timeout=timeout)


@dataclass(frozen=True)
class Reply:
    """요청 하나의 결과. status 가 0 이면 HTTP 응답을 받지 못한 것이고 kind 가 그 갈래다.
    asked 가 거짓이면 client.py 가 결과를 내지 못한 것이다(요청을 보냈는지 알 수 없다)."""

    status: int = 0
    headers: Mapping[str, str] = field(default_factory=dict[str, str])
    body: str = ""
    error: str = ""
    kind: str = ""
    ms: float = 0.0
    start: float = 0.0
    cert: str = ""
    tls: str = ""
    asked: bool = True

    @property
    def stub(self) -> dict[str, Json]:
        return as_map(parse(self.body)) if self.headers.get("x-stub") else {}

    @property
    def stub_name(self) -> str:
        return self.headers.get("x-stub", "")

    @property
    def seen_path(self) -> str:
        return as_text(self.stub.get("path"))

    @property
    def xff(self) -> str:
        return as_text(self.stub.get("xff"))

    def brief(self) -> str:
        if not self.asked:
            return "요청을 보내지 못함"
        return str(self.status) if self.status else (self.kind or self.error[:80])


def reply_of(value: Json) -> Reply:
    item = as_map(value)
    status = item.get("status")
    headers = {name: as_text(text) for name, text in as_map(item.get("headers")).items()}
    return Reply(
        status=status if isinstance(status, int) else 0,
        headers=headers,
        body=as_text(item.get("body")),
        error=as_text(item.get("error")),
        kind=as_text(item.get("error_kind")),
        ms=as_number(item.get("ms")),
        start=as_number(item.get("t")),
        cert=as_text(item.get("cert_sha256")),
        tls=as_text(item.get("tls")),
        asked=bool(item),
    )


def get(
    host: str,
    path: str,
    *,
    port: int = 443,
    scheme: str = "https",
    method: str = "GET",
    count: int = 1,
    parallel: bool = False,
    headers: Mapping[str, str] | None = None,
    body_bytes: int = 0,
    timeout: float = 5.0,
    verify: bool = True,
) -> dict[str, Json]:
    """client.py 에 넘길 http 일 하나."""
    sent: dict[str, Json] = {name: value for name, value in (headers or {}).items()}
    return {
        "kind": "http",
        "scheme": scheme,
        "host": host,
        "port": port,
        "path": path,
        "method": method,
        "count": count,
        "parallel": parallel,
        "headers": sent,
        "body_bytes": body_bytes,
        "timeout": timeout,
        "ca": "/ca.pem" if scheme == "https" and verify else "",
    }


def ask(where: str, ops: list[dict[str, Json]], *, timeout: float = 180) -> list[Json]:
    """이웃 컨테이너나 서버 자신(SELF)에서 client.py 를 돌려 일마다의 결과를 받는다."""
    payload = base64.b64encode(json.dumps(ops).encode()).decode()
    if where == SELF:
        mounts = ("-v", "/probe/client.py:/client.py:ro")
        mounts += ("-v", f"{TLS_MAIN}/fullchain.pem:/ca.pem:ro")
        command = (PYTHON_TAG, "python", "/client.py", payload)
        done = inner("run", "--rm", "--network", "host", *mounts, *command, timeout=timeout)
    else:
        done = docker("exec", where, "python", "/client.py", payload, timeout=timeout)
    for line in done.out.splitlines():
        if line.startswith("PROBE-RESULT "):
            return as_list(parse(line.removeprefix("PROBE-RESULT ")))
    return []


def replies_of(results: list[Json], index: int) -> list[Reply]:
    if index >= len(results):
        return []
    return [reply_of(item) for item in as_list(results[index])]


def many(where: str, op: dict[str, Json]) -> list[Reply]:
    return replies_of(ask(where, [op]), 0)


def one(where: str, op: dict[str, Json]) -> Reply:
    replies = many(where, op)
    return replies[0] if replies else Reply(asked=False)


def tcp(where: str, host: str, port: int) -> bool:
    spec: dict[str, Json] = {"kind": "tcp", "host": host, "port": port, "timeout": 3.0}
    results = ask(where, [spec])
    return bool(results) and as_map(results[0]).get("connected") is True


@dataclass(frozen=True)
class Access:
    addr: str
    request: str
    status: int
    limit: str
    upstream: str


def proxy_log() -> str:
    return inner("logs", f"{PROJECT}-proxy-1").both


def access_of(log: str, rid: str) -> Access | None:
    """프록시 접근 기록에서 그 rid 의 줄. rid 는 늘 질의의 끝에 두어 뒤가 빈칸이다."""
    for line in log.splitlines():
        if f"rid={rid} " not in line:
            continue
        if matched := ACCESS.match(line):
            return Access(matched[1], matched[2], int(matched[3]), matched[4], matched[5])
    return None


def limited(log: str, rid: str, zone: str) -> bool:
    """그 rid 의 요청이 그 구역의 빈도 제한으로 거부됐다는 오류 기록의 줄이 있는가."""
    return any(
        "limiting requests" in line and f'zone "{zone}"' in line and f"rid={rid} " in line
        for line in log.splitlines()
    )


@dataclass
class Report:
    rounds: Rounds = field(default_factory=Rounds)
    rows: list[Json] = field(default_factory=list[Json])
    facts: list[Json] = field(default_factory=list[Json])

    def close(self, slot: Slot, *, measured: bool, result: str, detail: str = "") -> None:
        slot.mark(measured=measured, result=result)
        self.rows.append(
            {"label": slot.label, "measured": measured, "result": result, "detail": detail}
        )
        head = "측정" if measured else "측정 아님"
        print(f"[{head}] {slot.label}: {result}" + (f" | {detail}" if detail else ""), flush=True)


@dataclass
class Ctx:
    """시나리오 하나(엔진 판과 userland-proxy 한 값)에서 띄운 서버의 사정."""

    engine: str
    mode: str
    lan6: bool
    full: bool
    repeat: int = 2
    loop_routed: bool = False
    cert: str = ""
    v4_path: bool = False
    v6_path: bool = False
    self6_path: bool = False
    services: dict[str, str] = field(default_factory=dict[str, str])
    gateways: set[str] = field(default_factory=set[str])

    @property
    def tag(self) -> str:
        return f"{self.engine}/proxy-{self.mode}"

    @property
    def major(self) -> int:
        return int(self.engine.split(".")[0])


# ---------------------------------------------------------------------------------------------
# 띄우고 거두기


def labelled(kind: str, token: str = "") -> list[str]:
    """이 프로브의 라벨이 붙은 컨테이너나 네트워크의 id. 라벨이 없는 것은 건드리지 않는다."""
    wanted = f"label={LABEL}={token}" if token else f"label={LABEL}"
    if kind == "container":
        return docker("ps", "-aq", "--filter", wanted).out.split()
    return docker("network", "ls", "-q", "--filter", wanted).out.split()


def cleanup() -> None:
    if ids := labelled("container"):
        docker("rm", "-f", "-v", *ids)
    if networks := labelled("network"):
        docker("network", "rm", *networks)


def remove_server(token: str) -> None:
    listed = docker(
        "ps", "-aq", "--filter", f"name=^{SERVER}$", "--filter", f"label={LABEL}={token}"
    )
    if ids := listed.out.split():
        docker("rm", "-f", "-v", *ids)


def prepare_images(work: Path, engines: list[str]) -> str:
    """측정에 쓸 이미지에 프로브 전용 태그를 달고 서버에 실을 tar 로 저장한다. 문제가 있으면 그
    글."""
    needed = [*TAGS.values(), HELPER_IMAGE, *(DIND[engine] for engine in engines)]
    for reference in needed:
        if docker("image", "inspect", reference, "--format", "{{.Id}}").code != 0:
            return f"로컬에 이미지가 없다: docker pull {reference}"
    for tag, reference in TAGS.items():
        if docker("tag", reference, tag).code != 0:
            return f"태그를 달지 못했다: {tag}"
    saved = docker(
        "save", "--platform", "linux/amd64", "-o", str(work / "images.tar"), *TAGS, timeout=900
    )
    return "" if saved.code == 0 else f"이미지를 저장하지 못했다: {tail(saved.err)}"


def start_lan(token: str) -> bool:
    """바깥 "LAN". IPv6 를 함께 켜 보고 안 되면 IPv4 만으로 만든다. IPv6 가 켜졌는지를 돌려준다."""
    base = ["network", "create", "--label", f"{LABEL}={token}"]
    v4 = ["--subnet", LAN4_SUBNET, "--gateway", LAN4_GATEWAY]
    if docker(*base, *v4, "--ipv6", "--subnet", LAN6_SUBNET, LAN).code == 0:
        return True
    made = docker(*base, *v4, LAN)
    if made.code != 0:
        raise RuntimeError(f"네트워크를 만들지 못했다: {tail(made.err)}")
    return False


def start_neighbors(token: str, *, lan6: bool) -> None:
    for name, address in NEIGHBOR4.items():
        argv = ["run", "-d", "--name", name, "--label", f"{LABEL}={token}", "--network", LAN]
        argv += ["--ip", address]
        if lan6:
            argv += ["--ip6", NEIGHBOR6[name]]
        made = docker(*argv, PYTHON_IMAGE, "sleep", "infinity")
        copied = docker("cp", str(HERE / "client.py"), f"{name}:/client.py")
        if made.code != 0 or copied.code != 0:
            raise RuntimeError(f"이웃 {name} 을 띄우지 못했다: {tail(made.err + copied.err)}")


def first_line(done: Done) -> str:
    lines = [line.strip() for line in done.both.splitlines() if line.strip()]
    return lines[0] if lines else ""


def start_server(ctx: Ctx, token: str, work: Path) -> dict[str, Json]:
    """dind 컨테이너를 띄우고 이미지와 프로브 파일을 싣고 시험용 인증서를 만든다. 본 사실을
    돌려준다."""
    argv = ["run", "-d", "--name", SERVER, "--hostname", SERVER, "--label", f"{LABEL}={token}"]
    argv += ["--privileged", "--network", LAN, "--ip", SERVER4]
    if ctx.lan6:
        argv += ["--ip6", SERVER6]
    argv.append(DIND[ctx.engine])
    if ctx.mode == "off":
        argv.append("--userland-proxy=false")
    if docker(*argv).code != 0:
        raise RuntimeError("서버 컨테이너를 띄우지 못했다")
    deadline = time.monotonic() + 120
    version = ""
    while not version and time.monotonic() < deadline:
        asked = inner("version", "--format", "{{.Server.Version}}", timeout=30)
        version = asked.out.strip() if asked.code == 0 else ""
        if not version:
            time.sleep(2)
    if not version:
        raise RuntimeError(
            f"안쪽 Docker Engine 이 뜨지 않았다: {tail(docker('logs', SERVER).both)}"
        )
    steps = (
        docker("cp", str(work / "images.tar"), f"{SERVER}:/images.tar", timeout=900),
        inner("load", "-i", "/images.tar", timeout=900),
        server("rm", "/images.tar"),
        server("mkdir", "-p", "/probe"),
        docker("cp", f"{HERE.as_posix()}/.", f"{SERVER}:/probe/"),
        server("sh", "-c", CERT_SCRIPT),
    )
    for step in steps:
        if step.code != 0:
            raise RuntimeError(f"서버 준비가 실패했다: {tail(step.both)}")
    pem = server("cat", f"{TLS_MAIN}/fullchain.pem").out
    (work / "ca.pem").write_text(pem, encoding="ascii", newline="\n")
    for name in NEIGHBOR4:
        docker("cp", str(work / "ca.pem"), f"{name}:/ca.pem")
    x509 = ("openssl", "x509", "-in", f"{TLS_MAIN}/fullchain.pem", "-noout")
    printed = server(*x509, "-fingerprint", "-sha256")
    ctx.cert = printed.out.strip().rpartition("=")[2].replace(":", "").lower()
    nginx_v = "--entrypoint", "nginx"
    return {
        "scenario": ctx.tag,
        "engine": version,
        "compose": first_line(inner("compose", "version", "--short")),
        "iptables": first_line(server("iptables", "-V")),
        "kernel": first_line(server("uname", "-r")),
        "openssl": first_line(server("openssl", "version")),
        "nginx": first_line(inner("run", "--rm", *nginx_v, NGINX_TAG, "-v")),
        "nginx_unprivileged": first_line(inner("run", "--rm", *nginx_v, NGINX_UNPRIV_TAG, "-v")),
        "python": first_line(inner("run", "--rm", PYTHON_TAG, "python", "--version")),
        "storage": first_line(inner("info", "--format", "{{.Driver}}")),
        "ip_forward": first_line(server("cat", "/proc/sys/net/ipv4/ip_forward")),
        "forward_policy": forward_policy(),
        "cert_sha256": ctx.cert,
    }


def forward_policy() -> str:
    """서버의 filter FORWARD 사슬의 정책(ACCEPT 나 DROP)."""
    listed = server("iptables", "-S", "FORWARD").out.splitlines()
    return listed[0].removeprefix("-P FORWARD ").strip() if listed else ""


def stack_up(files: tuple[str, ...], *extra: str) -> bool:
    """배치를 띄우고, 서버 자신에서 프록시를 거쳐 뒷단의 답이 올 때까지 기다린다."""
    if compose(files, "up", "-d", "--remove-orphans", *extra).code != 0:
        return False
    deadline = time.monotonic() + 40
    while time.monotonic() < deadline:
        reply = one(SELF, get(SERVER4, "/portal/health"))
        if reply.status == 200 and reply.stub_name == "portal":
            return True
        time.sleep(1)
    return False


def stack_down(files: tuple[str, ...]) -> None:
    compose(files, "down", "-v", "--remove-orphans")


def refresh(ctx: Ctx) -> None:
    """안쪽 네트워크를 다시 읽는다. 서비스마다의 IPv4 주소와, 그 네트워크의 게이트웨이 주소들이다.
    게이트웨이는 프록시 컨테이너의 엔드포인트에서 읽는다. 27.5.1 과 28.0.0 의 `docker network
    inspect` 는 대역만 적은 네트워크의 IPAM 설정에 게이트웨이를 싣지 않았다(edge-run4 의 원본)."""
    info = as_list(parse(inner("network", "inspect", f"{PROJECT}_edge").out))
    network = as_map(info[0] if info else None)
    found: dict[str, str] = {}
    for item in as_map(network.get("Containers")).values():
        name = as_text(as_map(item).get("Name")).removeprefix(f"{PROJECT}-").rsplit("-", 1)[0]
        found[name] = as_text(as_map(item).get("IPv4Address")).split("/")[0]
    ctx.services = found
    template = "{{range .NetworkSettings.Networks}}{{.Gateway}} {{.IPv6Gateway}} {{end}}"
    shown = inner("inspect", f"{PROJECT}-proxy-1", "--format", template).out
    # 29.9.2 는 IPv6 가 없는 네트워크의 IPv6Gateway 를 "invalid IP" 로 적는다(edge-run5 의 원본).
    ctx.gateways = {item for item in shown.split() if item.count(".") == 3 or ":" in item}


def bring_up(ctx: Ctx, report: Report, token: str, work: Path) -> bool:
    """회차 0. 서버와 배치가 고른 조건으로 떴는가."""
    ready = False
    with report.rounds.round(f"0.{ctx.tag}.서버와 배치 띄우기") as slot:
        facts = start_server(ctx, token, work)
        up = stack_up(BASE)
        proxies = server("pgrep", "-f", "docker-proxy").out.split()
        refresh(ctx)
        ctx.v4_path = tcp(N1, SERVER4, 443)
        # IPv6 로 닿지 않는 회차의 대조. 서버의 [::] 포트에 이웃과 자신이 닿는가.
        control = "ri-edge-v6-control"
        listen = ["python", "-m", "http.server", str(V6_CONTROL_PORT), "--bind", "::"]
        inner("run", "-d", "--name", control, "--network", "host", PYTHON_TAG, *listen)
        time.sleep(2)
        ctx.self6_path = tcp(SELF, "::1", V6_CONTROL_PORT)
        if ctx.lan6:
            ctx.v6_path = tcp(N1, SERVER6, V6_CONTROL_PORT)
            ctx.self6_path = ctx.self6_path and tcp(SELF, SERVER6, V6_CONTROL_PORT)
        inner("rm", "-f", control)
        facts["docker_proxy_processes"] = len(proxies)
        facts["lan_ipv6_path"] = ctx.v6_path
        facts["self_ipv6_path"] = ctx.self6_path
        report.facts.append(facts)
        ready = (
            up
            and as_text(facts.get("engine")) == ctx.engine
            and (len(proxies) > 0) == (ctx.mode == "on")
            and ctx.v4_path
            and len(ctx.services) == 5
        )
        shown = ", ".join(f"{key}={value}" for key, value in facts.items() if key != "scenario")
        report.close(
            slot, measured=ready, result="떴다" if ready else "조건이 서지 않았다", detail=shown
        )
    return ready


# ---------------------------------------------------------------------------------------------
# 항목 1. 프록시에 보이는 접속 주소


def classify(address: str, own: set[str], gateways: set[str]) -> str:
    if address in own:
        return "보낸 쪽의 주소"
    if address in gateways:
        return "안쪽 네트워크의 게이트웨이"
    return f"그 밖({address})"


def who(ctx: Ctx, report: Report, label: str, where: str, host: str) -> None:
    """요청 하나를 보내 프록시가 본 접속 주소를 적는다."""
    own = {SERVER4, SERVER6} if where == SELF else {NEIGHBOR4[where], NEIGHBOR6[where]}
    rid = secrets.token_hex(4)
    spoof = {"X-Forwarded-For": "203.0.113.9"}
    with report.rounds.round(f"1.{ctx.tag}.{label}") as slot:
        reply = one(where, get(host, f"/end-user/whoami?rid={rid}", headers=spoof))
        if reply.status == 200 and reply.stub_name == "serve":
            seen = access_of(proxy_log(), rid)
            logged = seen.addr if seen else "기록 없음"
            report.close(
                slot,
                measured=reply.xff != "" and logged == reply.xff,
                result=classify(reply.xff, own, ctx.gateways),
                detail=f"$remote_addr={logged}, 뒷단이 받은 X-Forwarded-For={reply.xff}, "
                f"안쪽 게이트웨이 {sorted(ctx.gateways)}",
            )
            return
        # serve 의 답이 아니다. HTTP 응답이나 접근 기록의 그 rid 줄이 있으면 프록시까지는
        # 닿은 것이고(프록시가 낸 502 등), 주소를 견줄 표지(뒷단이 받은 X-Forwarded-For)가
        # 없어 세지 않는다.
        log = proxy_log()
        entry = access_of(log, rid)
        if reply.status or entry:
            report.close(
                slot,
                measured=False,
                result=f"프록시에 닿았으나 serve 의 답이 아님({reply.brief()})",
                detail=f"$remote_addr={entry.addr if entry else '기록 없음'}, "
                f"답한 쪽 {reply.stub_name or 'nginx'}",
            )
            return
        # 닿지 않았다. 접근 기록을 읽었고(줄이 하나라도 있다) 같은 길의 대조가 섰을 때만 측정이다.
        read = any(ACCESS.match(line) for line in log.splitlines())
        path_up = ctx.v4_path
        if ":" in host:
            path_up = ctx.self6_path if where == SELF else ctx.v6_path
        report.close(
            slot,
            measured=reply.asked and read and path_up,
            result=f"닿지 않음({reply.brief()})",
            detail=reply.error[:120],
        )


def section_addresses(ctx: Ctx, report: Report, variant: str) -> None:
    branches = [
        ("n1→서버의 IPv4", N1, SERVER4),
        ("n2→서버의 IPv4", N2, SERVER4),
        ("서버 자신→127.0.0.1", SELF, "127.0.0.1"),
        ("서버 자신→자기 바깥 IPv4", SELF, SERVER4),
        ("서버 자신→::1", SELF, "::1"),
    ]
    if ctx.lan6:
        branches += [
            ("n1→서버의 IPv6", N1, SERVER6),
            ("n2→서버의 IPv6", N2, SERVER6),
            ("서버 자신→자기 바깥 IPv6", SELF, SERVER6),
        ]
    else:
        print(f"[건너뜀] 1.{ctx.tag}.{variant}: 바깥 네트워크에 IPv6 가 없어 그 갈래는 뺐다")
    for attempt in range(1, ctx.repeat + 1):
        for label, where, host in branches:
            who(ctx, report, f"{variant}.{label}#{attempt}", where, host)


def section_addresses_dual(ctx: Ctx, report: Report) -> None:
    """안쪽 네트워크에도 IPv6 를 켠 배치. 끝나면 IPv4 만의 배치로 되돌린다."""
    dual = (*BASE, "compose.ipv6.yml")
    stack_down(BASE)
    ready = False
    with report.rounds.round(f"1.{ctx.tag}.안쪽 IPv6 켬.배치 띄우기") as slot:
        up = stack_up(dual)
        networks = inner("network", "inspect", f"{PROJECT}_edge", "--format", "{{.EnableIPv6}}")
        refresh(ctx)
        ready = up and networks.out.strip() == "true" and "172.30.0.1" in ctx.gateways
        report.close(
            slot,
            measured=ready,
            result="떴다" if up else "뜨지 않았다",
            detail=f"안쪽 게이트웨이 {sorted(ctx.gateways)}",
        )
    if ready:
        section_addresses(ctx, report, "안쪽 IPv6 켬")
        rid = secrets.token_hex(4)
        with report.rounds.round(f"1.{ctx.tag}.안쪽 IPv6 켬.0.0.0.0 에만 묶인 뒷단") as slot:
            replies = many(N1, get(SERVER4, f"/end-user/x?rid={rid}-{{i}}", count=8))
            log = proxy_log()
            reached = sum(access_of(log, f"{rid}-{index}") is not None for index in range(8))
            marks = ("connect() failed", f"rid={rid}-", 'upstream: "http://[')
            failed = [line for line in log.splitlines() if all(mark in line for mark in marks)]
            good = sum(reply.status == 200 for reply in replies)
            report.close(
                slot,
                measured=len(replies) == 8 and reached == 8,
                result=f"200 {good}/8, 뒷단의 IPv6 주소로 건 연결 실패 {len(failed)}줄",
                detail=tail(failed[0], 1)[-160:] if failed else "",
            )
    stack_down(dual)
    stack_up(BASE)
    refresh(ctx)


# ---------------------------------------------------------------------------------------------
# 항목 2. 주소별 빈도 제한


def both(op1: dict[str, Json], op2: dict[str, Json]) -> tuple[list[Reply], list[Reply]]:
    """n1 과 n2 가 같은 때에 저마다의 일을 한다."""
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(many, N1, op1)
        second = pool.submit(many, N2, op2)
        return first.result(), second.result()


def span(replies: list[Reply]) -> float:
    """요청 묶음이 걸린 초."""
    return max((reply.start + reply.ms / 1000 for reply in replies), default=0.0)


def burst_marks(log: str, rid: str, replies: list[Reply], zone: str) -> bool:
    """요청마다 프록시에 닿았고, 200 이 아닌 응답마다 그 구역의 거부 기록이 있다."""
    for index, reply in enumerate(replies):
        if access_of(log, f"{rid}-{index}") is None:
            return False
        if reply.status != 200 and not limited(log, f"{rid}-{index}", zone):
            return False
    return bool(replies)


def codes(replies: list[Reply]) -> str:
    return " ".join(reply.brief() for reply in replies)


def verdict_of(ok1: int, ok2: int, burst: int, refill: int) -> str:
    """두 이웃이 받은 수를 두 해석에 댄다. 한 통이든 따로든 묶음을 보내는 동안 채워진
    몫(refill)만큼은 더 받을 수 있어, 기대를 `1+burst` 부터 `1+burst+refill` 까지의 폭으로 본다."""
    low, high = 1 + burst, 1 + burst + refill
    if low <= ok1 <= high and low <= ok2 <= high:
        return "주소별로 따로 센다"
    if low <= ok1 + ok2 <= high:
        return "둘을 한 통에서 센다"
    return "두 해석 모두로 설명되지 않는다"


def combo_round(ctx: Ctx, report: Report, zone: str, rate: int, burst: int) -> None:
    count = burst + 6
    rid1, rid2 = secrets.token_hex(4), secrets.token_hex(4)
    path = f"/limit/{zone}/?rid="
    with report.rounds.round(f"2.{ctx.tag}.{zone}.n1 과 n2 가 동시에 {count}번씩") as slot:
        first, second = both(
            get(SERVER4, f"{path}{rid1}-{{i}}", port=8081, scheme="http", count=count),
            get(SERVER4, f"{path}{rid2}-{{i}}", port=8081, scheme="http", count=count),
        )
        log = proxy_log()
        marks = burst_marks(log, rid1, first, zone) and burst_marks(log, rid2, second, zone)
        ok1 = sum(reply.status == 200 and reply.stub_name == "portal" for reply in first)
        ok2 = sum(reply.status == 200 and reply.stub_name == "portal" for reply in second)
        refill = int(max(span(first), span(second)) * rate / 60)
        verdict = verdict_of(ok1, ok2, burst, refill)
        first_reject = next((i for i, reply in enumerate(first) if reply.status != 200), -1)
        rejected = sorted({reply.status for reply in [*first, *second] if reply.status != 200})
        report.close(
            slot,
            measured=marks and len(first) == count and len(second) == count,
            result=f"n1 {ok1}, n2 {ok2} 허용, 기대 {1 + burst}~{1 + burst + refill}: {verdict}",
            detail=f"n1 의 첫 거부는 {first_reject + 1}번째 요청, 거부 코드 {rejected}, "
            f"걸린 초 n1 {span(first):.2f} n2 {span(second):.2f}, 채워지는 간격 {60 / rate:.0f}초",
        )
    wait = 60 / rate + 0.4
    rid3 = secrets.token_hex(4)
    with report.rounds.round(f"2.{ctx.tag}.{zone}.{wait:.1f}초 쉰 뒤 n1 이 3번") as slot:
        time.sleep(wait)
        after = many(N1, get(SERVER4, f"{path}{rid3}-{{i}}", port=8081, scheme="http", count=3))
        log = proxy_log()
        report.close(
            slot,
            measured=len(after) == 3 and burst_marks(log, rid3, after, zone),
            result=f"상태 {codes(after)}",
            detail="한 간격 뒤에는 하나만 더 받는다" if codes(after) == "200 429 429" else "",
        )


def section_limits(ctx: Ctx, report: Report) -> None:
    for zone, rate, burst in COMBOS:
        combo_round(ctx, report, zone, rate, burst)

    # nodelay 없는 burst. 차례로 보내면 늦춰질 뿐 넘치지 않으므로 한꺼번에 보낸다.
    rid = secrets.token_hex(4)
    with report.rounds.round(f"2.{ctx.tag}.r60b3q(nodelay 없음).n1 이 한꺼번에 7번") as slot:
        op = get(SERVER4, f"/limit/r60b3q/?rid={rid}-{{i}}", port=8081, scheme="http", count=7)
        op["parallel"] = True
        replies = many(N1, op)
        log = proxy_log()
        waits = sorted(round(reply.ms / 1000, 1) for reply in replies if reply.status == 200)
        report.close(
            slot,
            measured=len(replies) == 7 and burst_marks(log, rid, replies, "r60b3q"),
            result=f"200 {len(waits)}개, 429 {sum(reply.status == 429 for reply in replies)}개",
            detail=f"200 인 응답이 걸린 초 {waits}",
        )

    rid = secrets.token_hex(4)
    with report.rounds.round(f"2.{ctx.tag}.r60b0d(limit_req_status 없음).n1 이 3번") as slot:
        replies = many(
            N1, get(SERVER4, f"/limit/r60b0d/?rid={rid}-{{i}}", port=8081, scheme="http", count=3)
        )
        log = proxy_log()
        report.close(
            slot,
            measured=len(replies) == 3 and burst_marks(log, rid, replies, "r60b0d"),
            result=f"상태 {codes(replies)}",
        )

    token_path_rounds(ctx, report)
    variant_round(ctx, report)
    if ctx.v6_path and ctx.mode == "on":
        merged_round(ctx, report)


def token_path_rounds(ctx: Ctx, report: Report) -> None:
    """시제품의 토큰 경로(443). n1 은 한도를 넘긴 바로 뒤에 다른 경로를 부르고 토큰 경로를 한 번 더
    부른다."""
    count = TOKEN_BURST + 6
    rid1, rid2, rid3 = secrets.token_hex(4), secrets.token_hex(4), secrets.token_hex(4)
    token = "/portal/sites/demo/token?rid="
    others = ("/portal/", "/portal/sites/demo/acknowledgement", "/widget", "/end-user/runs", "/")
    ops1 = [get(SERVER4, f"{token}{rid1}-{{i}}", method="POST", count=count)]
    ops1 += [get(SERVER4, f"{path}?rid={rid3}-o{index}") for index, path in enumerate(others)]
    ops1.append(get(SERVER4, f"{token}{rid3}-last", method="POST"))
    with ThreadPoolExecutor(max_workers=2) as pool:
        future1 = pool.submit(ask, N1, ops1)
        future2 = pool.submit(
            many, N2, get(SERVER4, f"{token}{rid2}-{{i}}", method="POST", count=count)
        )
        results1, second = future1.result(), future2.result()
    first = replies_of(results1, 0)
    log = proxy_log()
    expected = 1 + TOKEN_BURST
    with report.rounds.round(f"2.{ctx.tag}.토큰 경로(443).n1 과 n2 가 동시에 {count}번씩") as slot:
        marks = burst_marks(log, rid1, first, "portal_token")
        marks = marks and burst_marks(log, rid2, second, "portal_token")
        ok1 = sum(reply.status == 200 and reply.stub_name == "portal" for reply in first)
        ok2 = sum(reply.status == 200 and reply.stub_name == "portal" for reply in second)
        refill = int(max(span(first), span(second)) * TOKEN_RATE / 60)
        verdict = verdict_of(ok1, ok2, TOKEN_BURST, refill)
        report.close(
            slot,
            measured=marks and len(first) == count and len(second) == count,
            result=f"n1 허용 {ok1}, n2 허용 {ok2}, 기대 {expected}~{expected + refill}: {verdict}",
            detail=f"설정 {TOKEN_RATE}r/m burst={TOKEN_BURST} nodelay, "
            f"걸린 초 n1 {span(first):.2f} n2 {span(second):.2f}",
        )
    with report.rounds.round(f"2.{ctx.tag}.토큰 경로(443).한도를 넘긴 n1 의 다른 경로") as slot:
        rest = [replies_of(results1, index + 1) for index in range(len(others))]
        last = replies_of(results1, len(others) + 1)
        seen = [access_of(log, f"{rid3}-o{index}") for index in range(len(others))]
        still = (
            bool(last) and last[0].status == 429 and limited(log, f"{rid3}-last", "portal_token")
        )
        free = all(entry is not None and entry.limit == "-" for entry in seen)
        passed = all(len(item) == 1 and item[0].status == 200 for item in rest)
        names = [item[0].stub_name if item else "?" for item in rest]
        report.close(
            slot,
            measured=still and all(entry is not None for entry in seen),
            result="다른 경로는 제한을 받지 않는다" if free and passed else "다른 경로도 걸렸다",
            detail=f"경로 {list(others)} 의 답 {names}, 접근 기록의 limit 칸은 모두 '-', "
            "그 뒤의 토큰 요청은 429",
        )
    with report.rounds.round(f"2.{ctx.tag}.토큰 경로(443).거부 응답의 모양") as slot:
        rejected = [reply for reply in first if reply.status == 429]
        sample = rejected[0] if rejected else Reply(asked=False)
        retry = "Retry-After 있음" if "retry-after" in sample.headers else "Retry-After 없음"
        hsts = "HSTS 있음" if "strict-transport-security" in sample.headers else "HSTS 없음"
        report.close(
            slot,
            measured=bool(rejected) and "429 Too Many Requests" in sample.body,
            result=f"429, {retry}, {hsts}",
            detail=f"헤더 {sorted(sample.headers)}, 본문은 nginx 의 429 쪽",
        )


VARIANTS = (
    "/portal/sites/demo/token",
    "/portal/sites/demo/token?x=1&",
    "/portal/sites/demo/token/",
    "/portal/sites/de%6Do/token",
    "/portal//sites/demo/token",
    "/portal/sites/demo/x/../token",
    "/portal/sites/demo/TOKEN",
    "/portal/sites/demo/token%2F",
    "/portal/sites/demo/token;x",
)


def variant_round(ctx: Ctx, report: Report) -> None:
    """토큰 경로를 다르게 적은 요청이 빈도 제한의 location 에 걸리는지와 뒷단이 받는 경로."""
    rid = secrets.token_hex(4)
    ops: list[dict[str, Json]] = []
    for index, path in enumerate(VARIANTS):
        joiner = "" if path.endswith("&") else "?"
        ops.append(get("127.0.0.1", f"{path}{joiner}rid={rid}-{index}", method="POST"))
    with report.rounds.round(f"2.{ctx.tag}.토큰 경로(443).경로를 다르게 적은 요청") as slot:
        results = ask(SELF, ops)
        log = proxy_log()
        shown: list[str] = []
        found = 0
        for index, path in enumerate(VARIANTS):
            replies = replies_of(results, index)
            entry = access_of(log, f"{rid}-{index}")
            found += entry is not None
            limit = {"-": "제한 밖", "PASSED": "제한 안"}.get(entry.limit if entry else "", "?")
            reply = replies[0] if replies else Reply(asked=False)
            got = reply.seen_path.partition("?")[0] if reply.stub_name else f"({reply.brief()})"
            shown.append(f"{path} → {limit}, 뒷단이 받은 경로 {got}")
        report.close(
            slot,
            measured=found == len(VARIANTS),
            result=f"{len(VARIANTS)}가지를 봤다",
            detail=" ; ".join(shown),
        )


def merged_round(ctx: Ctx, report: Report) -> None:
    """두 이웃이 같은 주소로 보이는 길(IPv6 로 걸고 안쪽은 IPv4 뿐, userland-proxy 켬)에서의 빈도
    제한."""
    zone, burst = "r10b5", 5
    count = burst + 6
    rid1, rid2 = secrets.token_hex(4), secrets.token_hex(4)
    path = f"/limit/{zone}/?rid="
    with report.rounds.round(f"2.{ctx.tag}.뭉침.n1 과 n2 가 IPv6 로 동시에 {count}번씩") as slot:
        first, second = both(
            get(SERVER6, f"{path}{rid1}-{{i}}", port=8081, scheme="http", count=count),
            get(SERVER6, f"{path}{rid2}-{{i}}", port=8081, scheme="http", count=count),
        )
        log = proxy_log()
        seen1, seen2 = access_of(log, f"{rid1}-0"), access_of(log, f"{rid2}-0")
        same = seen1 is not None and seen2 is not None and seen1.addr == seen2.addr
        marks = burst_marks(log, rid1, first, zone) and burst_marks(log, rid2, second, zone)
        ok1 = sum(reply.status == 200 for reply in first)
        ok2 = sum(reply.status == 200 for reply in second)
        refill = int(max(span(first), span(second)) * 10 / 60)
        report.close(
            slot,
            measured=marks and same,
            result=f"n1 허용 {ok1}, n2 허용 {ok2}: {verdict_of(ok1, ok2, burst, refill)}",
            detail=f"두 이웃의 $remote_addr 가 모두 {seen1.addr if seen1 else '?'}, "
            f"따로 세면 각자 {1 + burst}, 한 통이면 합이 {1 + burst}(채워진 몫 {refill})",
        )


# ---------------------------------------------------------------------------------------------
# 항목 3. 127.0.0.1 에만 발행한 포트와 경유 공격


def counters() -> dict[str, int]:
    """서버의 iptables 규칙과 사슬 정책마다의 패킷 수. 열쇠는 '<표> <규칙>' 이다."""
    table = ""
    found: dict[str, int] = {}
    for line in server("iptables-save", "-c").out.splitlines():
        if line.startswith("*"):
            table = line[1:]
        elif matched := RULE.match(line):
            found[f"{table} {matched[2]}"] = int(matched[1])
        elif matched := POLICY.match(line):
            found[f"{table} :{matched[1]} {matched[2]}"] = int(matched[3])
    return found


def is_probe_rule(key: str, subnet: str) -> bool:
    """이 스크립트가 넣은 셈 전용 규칙(대상이 없다)인가."""
    return key.startswith("raw ") and f"-d {subnet}" in key and "-i eth0" in key and "-j" not in key


def helper(neighbor: str, *args: str) -> Done:
    """이웃의 네트워크 이름공간에서 `ip` 를 돌린다(이웃 이미지에는 ip 가 없다)."""
    return docker(
        "run", "--rm", "--network", f"container:{neighbor}", "--cap-add", "NET_ADMIN",
        "--entrypoint", "ip", HELPER_IMAGE, *args,
    )  # fmt: skip


def start_loopback_neighbor(token: str) -> bool:
    """경유 공격 B 의 이웃 n3. 목적지가 127.0.0.1 인 패킷을 서버로 보내려고 자기 루프백의 local 경로
    둘을 지우고 127.0.0.1 을 서버로 돌린다. 서버가 되돌려 보내는 답은 출발지가 127.0.0.1 이라
    `route_localnet` 을 켜야 받는다. n1·n2 와 따로 두어 그 둘의 루프백을 건드리지 않는다. 경로가
    서버로 가는지를 돌려준다."""
    argv = ["run", "-d", "--name", N3, "--label", f"{LABEL}={token}", "--network", LAN]
    argv += ["--ip", NEIGHBOR3, "--sysctl", "net.ipv4.conf.all.route_localnet=1"]
    made = docker(*argv, PYTHON_IMAGE, "sleep", "infinity")
    copied = docker("cp", str(HERE / "client.py"), f"{N3}:/client.py")
    for local in ("127.0.0.1", "127.0.0.0/8"):
        helper(N3, "route", "del", "local", local, "dev", "lo", "table", "local")
    helper(N3, "route", "add", "127.0.0.1/32", "via", SERVER4, "dev", "eth0")
    routed = f"via {SERVER4}" in helper(N3, "route", "get", "127.0.0.1").out
    return made.code == 0 and copied.code == 0 and routed


def attack(
    ctx: Ctx,
    report: Report,
    label: str,
    op: dict[str, Json],
    subnet: str,
    *,
    ready: bool,
    where: str = N1,
) -> None:
    """이웃이 서버를 경유지로 삼아 서버의 바깥 주소가 아닌 목적지(컨테이너 주소나 127.0.0.1)로 바로
    건다. 표지는 그 목적지로 가는 패킷이 서버의 eth0 에 닿은 것(셈 전용 규칙의 패킷 수)과, 경로와
    대상의 양성 대조가 섰다는 것(ready)이다. 대상이 답하지 않는 회차의 "막힌다"를 막은 것으로
    세지 않으려는 것이다(`attack6` 와 같다)."""
    with report.rounds.round(f"3.{ctx.tag}.{label}") as slot:
        before = counters()
        reply = one(where, op)
        after = counters()
        grown = {key: after[key] - before.get(key, 0) for key in after}
        arrived = any(is_probe_rule(key, subnet) and count > 0 for key, count in grown.items())
        drops = [f"{key} (+{count})" for key, count in grown.items() if count > 0 and "DROP" in key]
        if reply.status:
            result = f"닿는다({reply.status}, 답한 쪽 {reply.stub_name or 'nginx'})"
        else:
            result = f"막힌다({reply.brief()})"
        report.close(
            slot,
            measured=ready and arrived and reply.asked,
            result=result,
            detail="패킷 수가 늘어난 DROP: " + (" ; ".join(drops) if drops else "없음"),
        )


def section_loopback(ctx: Ctx, report: Report) -> None:
    admin, serve, proxy = (ctx.services.get(name, "") for name in ("admin", "serve", "proxy"))
    bound = inner("port", f"{PROJECT}-admin-1").out.strip()
    self_ok = False
    with report.rounds.round(f"3.{ctx.tag}.서버 자신→127.0.0.1:3000(양성 대조)") as slot:
        reply = one(SELF, get("127.0.0.1", "/", port=3000, scheme="http"))
        self_ok = reply.status == 200 and reply.stub_name == "admin"
        report.close(
            slot,
            measured=reply.asked and bound == "3000/tcp -> 127.0.0.1:3000",
            result="닿는다" if self_ok else f"닿지 않음({reply.brief()})",
            detail=f"docker port: {bound}",
        )
    targets = [
        ("n1→서버의 IPv4:3000", SERVER4, 3000),
        ("n1→서버의 IPv4:8000(발행 안 함)", SERVER4, 8000),
    ]
    if ctx.v6_path:
        targets.append(("n1→서버의 IPv6:3000", SERVER6, 3000))
    for label, host, port in targets:
        with report.rounds.round(f"3.{ctx.tag}.{label}") as slot:
            reply = one(N1, get(host, "/", port=port, scheme="http", timeout=3.0))
            report.close(
                slot,
                measured=reply.asked and self_ok and ctx.v4_path,
                result=f"닿는다({reply.stub_name})"
                if reply.status
                else f"닿지 않음({reply.brief()})",
            )

    # 경유 공격. 이웃이 안쪽 대역으로 가는 경로를 서버를 경유지로 삼아 더한다.
    helper(N1, "route", "replace", INNER4_SUBNET, "via", SERVER4)
    routed = f"via {SERVER4}" in helper(N1, "route", "get", admin or "172.30.0.2").out
    server("iptables", "-t", "raw", "-I", "PREROUTING", "1", "-i", "eth0", "-d", INNER4_SUBNET)
    server("iptables", "-t", "raw", "-I", "PREROUTING", "1", "-i", "eth0", "-d", LOOPBACK)
    original = forward_policy()
    targets_inside = [
        # (표에 적을 말, 컨테이너 주소, 포트, 방식, 답할 대역)
        ("관리 화면 컨테이너:3000(127.0.0.1 에만 발행)", admin, 3000, "http", "admin"),
        ("serve 컨테이너:8000(발행 안 함)", serve, 8000, "http", "serve"),
        ("프록시 컨테이너:8443(모든 주소에 발행)", proxy, 8443, "https", "portal"),
    ]
    # 대상의 양성 대조. 서버 자신에서 컨테이너 주소로 걸면 그 대역이 답한다(`transit6_rounds`
    # 와 같다).
    answered: dict[str, bool] = {}
    for label, host, port, scheme, stub in targets_inside:
        with report.rounds.round(f"3.{ctx.tag}.서버 자신→{label}(양성 대조)") as slot:
            op = get(host, "/portal/health", port=port, scheme=scheme, timeout=3.0, verify=False)
            reply = one(SELF, op)
            answered[label] = bool(host) and reply.status == 200 and reply.stub_name == stub
            report.close(
                slot,
                measured=reply.asked,
                result="닿는다" if answered[label] else f"닿지 않음({reply.brief()})",
                detail=f"컨테이너 주소 {host}, 답한 쪽 {reply.stub_name}",
            )
    for policy in (original, "DROP" if original == "ACCEPT" else "ACCEPT"):
        server("iptables", "-P", "FORWARD", policy)
        note = f"FORWARD 정책 {forward_policy()}"
        for attempt in range(1, ctx.repeat + 1):
            for label, host, port, scheme, _ in targets_inside:
                # 컨테이너 주소는 시험용 인증서의 이름에 없어 검증을 끈다(client.py 의 그 갈래).
                op = get(
                    host, "/portal/health", port=port, scheme=scheme, timeout=3.0, verify=False
                )
                name = f"경유.n1→{label}.{note}#{attempt}"
                ready = routed and answered.get(label, False)
                attack(ctx, report, name, op, INNER4_SUBNET, ready=ready)
            # 경유 공격 B. 목적지 자체가 127.0.0.1 이다(관리 화면을 발행한 주소).
            op = get("127.0.0.1", "/attack-b", port=3000, scheme="http", timeout=3.0)
            name = f"경유.n3→127.0.0.1:3000(목적지를 루프백으로).{note}#{attempt}"
            ready = ctx.loop_routed and self_ok
            attack(ctx, report, name, op, LOOPBACK, ready=ready, where=N3)
    server("iptables", "-P", "FORWARD", original)
    server("iptables", "-t", "raw", "-D", "PREROUTING", "-i", "eth0", "-d", LOOPBACK)
    server("iptables", "-t", "raw", "-D", "PREROUTING", "-i", "eth0", "-d", INNER4_SUBNET)
    helper(N1, "route", "del", INNER4_SUBNET)
    raw("경유 공격 뒤의 iptables-save -c", server("iptables-save", "-c").out)
    if ctx.major >= 28:
        open_network_control(ctx, report)


def open_network_control(ctx: Ctx, report: Report) -> None:
    """경유 경로 자체가 통한다는 양성 대조. 보호를 끈 네트워크(nat-unprotected)의 컨테이너에는
    닿아야 한다."""
    option = "com.docker.network.bridge.gateway_mode_ipv4=nat-unprotected"
    name = "ri-edge-open"
    inner("network", "create", "--subnet", OPEN4_SUBNET, "-o", option, name)
    mount = "/probe/stub.py:/stub.py:ro"
    inner(
        "run", "-d", "--name", f"{name}-stub", "--network", name, "-v", mount, PYTHON_TAG,
        "python", "/stub.py", "open", "8000",
    )  # fmt: skip
    template = "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}"
    address = inner("inspect", f"{name}-stub", "--format", template).out.strip()
    helper(N1, "route", "replace", OPEN4_SUBNET, "via", SERVER4)
    routed = f"via {SERVER4}" in helper(N1, "route", "get", address or "172.31.0.2").out
    server("iptables", "-t", "raw", "-I", "PREROUTING", "1", "-i", "eth0", "-d", OPEN4_SUBNET)
    time.sleep(1)
    attack(
        ctx, report, "경유.n1→보호를 끈 네트워크의 컨테이너:8000(양성 대조)",
        get(address, "/", port=8000, scheme="http", timeout=3.0), OPEN4_SUBNET, ready=routed,
    )  # fmt: skip
    server("iptables", "-t", "raw", "-D", "PREROUTING", "-i", "eth0", "-d", OPEN4_SUBNET)
    helper(N1, "route", "del", OPEN4_SUBNET)
    inner("rm", "-f", f"{name}-stub")
    inner("network", "rm", name)


# ---------------------------------------------------------------------------------------------
# 항목 4. 잘못 연 포트


def section_wrong_port(ctx: Ctx, report: Report) -> None:
    wrong = (*BASE, "compose.wrong-port.yml")
    plain = get(SERVER4, "/health", port=8000, scheme="http", timeout=3.0)
    with report.rounds.round(f"4.{ctx.tag}.덧씌우기 전 n1→서버:8000") as slot:
        reply = one(N1, plain)
        report.close(
            slot,
            measured=reply.asked and ctx.v4_path,
            result=f"닿는다({reply.stub_name})" if reply.status else f"닿지 않음({reply.brief()})",
        )
    with report.rounds.round(f"4.{ctx.tag}.serve 에 8000:8000 을 발행한 뒤 n1→서버:8000") as slot:
        up = compose(wrong, "up", "-d").code == 0
        time.sleep(3)
        bound = inner("port", f"{PROJECT}-serve-1").out.strip().splitlines()
        reply = one(N1, plain)
        reached = f"평문으로 닿는다({reply.stub_name})"
        report.close(
            slot,
            measured=up and reply.asked and "8000/tcp -> 0.0.0.0:8000" in bound,
            result=reached if reply.status == 200 else f"닿지 않음({reply.brief()})",
            detail=f"docker port: {bound}",
        )
    # 되돌린다. serve 가 다시 만들어지므로 프록시까지 새로 띄워 뒤 항목이 옛 주소를 보지 않게 한다.
    stack_up(BASE, "--force-recreate")
    refresh(ctx)


# ---------------------------------------------------------------------------------------------
# 항목 5. TLS, 80, 404, root 가 아닌 nginx

ALLOWED = (
    ("GET", "/", "portal", "/"),
    ("GET", "/?site=demo&", "portal", "/?site=demo&"),
    ("GET", "/portal/", "portal", "/portal/"),
    ("GET", "/portal/health", "portal", "/portal/health"),
    ("GET", "/portal/sites/demo/acknowledgement", "portal", "/portal/sites/demo/acknowledgement"),
    ("GET", "/widget", "widget", "/widget"),
    ("GET", "/widget?agent=calc&", "widget", "/widget?agent=calc&"),
    ("GET", "/widget/element.js", "widget", "/widget/element.js"),
    ("POST", "/end-user/runs", "serve", "/end-user/runs"),
    ("GET", "/runs/../end-user/x", "serve", "/end-user/x"),
)
DENIED = (
    "/runs", "/health", "/docs", "/openapi.json", "/admin", "/api/runs", "/plugins",
    "/widgetx", "/widget-admin", "/end-userx/a", "/end-user", "/portal", "/portalx",
    "/END-USER/runs", "/Widget", "/end-user/../runs", "/end-user/%2e%2e/runs",
    "/portal/../runs", "/widget/../admin", "/.well-known/acme-challenge/x",
)  # fmt: skip


def with_rid(path: str, rid: str) -> str:
    return f"{path}rid={rid}" if path.endswith("&") else f"{path}?rid={rid}"


def section_tls(ctx: Ctx, report: Report) -> None:
    with report.rounds.round(f"5.{ctx.tag}.자체 서명 인증서 만들기") as slot:
        files = (f"{TLS_MAIN}/fullchain.pem", f"{TLS_MAIN}/privkey.pem")
        x509 = ("openssl", "x509", "-in", files[0], "-noout")
        shown = server(*x509, "-subject", "-ext", "subjectAltName")
        modes = server("stat", "-c", "%n %u:%g %a", *files)
        report.close(
            slot,
            measured=len(ctx.cert) == 64 and "edge.test" in shown.out,
            result="만들어졌다",
            detail=f"{tail(shown.out, 4)} / {tail(modes.out, 2)}",
        )

    with report.rounds.round(f"5.{ctx.tag}.n1→443 을 TLS 로") as slot:
        reply = one(N1, get(SERVER4, "/portal/"))
        same = reply.cert == ctx.cert and ctx.cert != ""
        report.close(
            slot,
            measured=reply.status == 200 and reply.stub_name == "portal" and same,
            result=f"{reply.tls}, 받은 인증서의 지문이 만든 것과 같다"
            if same
            else f"다르다({reply.brief()})",
            detail="인증서와 이름(IP)을 그 인증서만 믿는 설정으로 검증했다",
        )

    with report.rounds.round(f"5.{ctx.tag}.n1→443 을 평문으로") as slot:
        reply = one(N1, get(SERVER4, "/portal/", scheme="http", port=443))
        refused = "plain HTTP request was sent to HTTPS port" in reply.body
        report.close(
            slot,
            measured=reply.asked and (refused or reply.status == 0),
            result=f"{reply.brief()}, 뒷단으로 넘기지 않는다"
            if not reply.stub_name
            else "뒷단이 답했다",
            detail="본문이 nginx 의 'plain HTTP request was sent to HTTPS port'" if refused else "",
        )

    with report.rounds.round(f"5.{ctx.tag}.HSTS 헤더") as slot:
        results = ask(
            SELF,
            [
                get("127.0.0.1", "/portal/"),
                get("127.0.0.1", "/runs"),
                get("127.0.0.1", "/portal/sites/demo/token", method="POST", count=TOKEN_BURST + 4),
            ],
        )
        samples = {"200": replies_of(results, 0), "404": replies_of(results, 1)}
        samples["429"] = [reply for reply in replies_of(results, 2) if reply.status == 429]
        values = {
            name: (
                found[0].headers.get("strict-transport-security", "없음") if found else "응답 없음"
            )
            for name, found in samples.items()
        }
        kinds = all(found and str(found[0].status) == name for name, found in samples.items())
        everywhere = all("max-age" in value for value in values.values())
        report.close(
            slot,
            measured=kinds,
            result="200·404·429 모두에 있다" if everywhere else "빠진 곳이 있다",
            detail=str(values),
        )

    with report.rounds.round(f"5.{ctx.tag}.n1→80") as slot:
        host = {"Host": "edge.test"}
        paths = ("/portal/?a=1", "/end-user/runs", "/.well-known/acme-challenge/x", "/")
        ops = [get(SERVER4, path, port=80, scheme="http", headers=host) for path in paths]
        ops.append(
            get(SERVER4, "/end-user/runs", port=80, scheme="http", headers=host, method="POST")
        )
        results = ask(N1, ops)
        replies = [found[0] for index in range(len(ops)) if (found := replies_of(results, index))]
        wanted = [f"https://edge.test{path}" for path in (*paths, "/end-user/runs")]
        located = [reply.headers.get("location", "") for reply in replies]
        from_nginx = all(reply.headers.get("server") == "nginx" for reply in replies)
        passed_on = any(reply.stub_name for reply in replies)
        report.close(
            slot,
            measured=len(replies) == len(ops) and from_nginx,
            result=f"상태 {sorted({reply.status for reply in replies})}, "
            + ("모두 같은 경로의 https 로 넘긴다" if located == wanted else f"Location {located}")
            + (", 뒷단이 답했다" if passed_on else ", 뒷단이 답한 것 없음"),
            detail="GET 넷(확인 경로 /.well-known/acme-challenge/ 포함)과 POST 하나",
        )

    path_round(ctx, report)
    header_round(ctx, report)
    body_round(ctx, report)
    sse_round(ctx, report)
    nonroot_rounds(ctx, report)


def path_round(ctx: Ctx, report: Report) -> None:
    rid = secrets.token_hex(4)
    ops: list[dict[str, Json]] = []
    for index, (method, path, _, _) in enumerate(ALLOWED):
        ops.append(get(SERVER4, with_rid(path, f"{rid}-a{index}"), method=method))
    ops += [get(SERVER4, with_rid(path, f"{rid}-d{i}")) for i, path in enumerate(DENIED)]
    with report.rounds.round(f"5.{ctx.tag}.넘기는 경로와 404") as slot:
        results = ask(N1, ops)
        wrong: list[str] = []
        answered = 0
        for index, (_, path, name, upstream) in enumerate(ALLOWED):
            found = replies_of(results, index)
            reply = found[0] if found else Reply(asked=False)
            answered += reply.asked
            got = reply.seen_path.replace(f"rid={rid}-a{index}", "").removesuffix("?")
            if reply.status != 200 or reply.stub_name != name or got != upstream:
                wrong.append(f"{path} → {reply.brief()} {reply.stub_name} {got}")
        for index, path in enumerate(DENIED):
            found = replies_of(results, len(ALLOWED) + index)
            reply = found[0] if found else Reply(asked=False)
            answered += reply.asked
            if reply.status != 404 or reply.stub_name:
                wrong.append(f"{path} → {reply.brief()} {reply.stub_name}")
        total = len(ALLOWED) + len(DENIED)
        report.close(
            slot,
            measured=answered == total and len(wrong) < len(ALLOWED),
            result=f"넘기는 {len(ALLOWED)}가지, 404 {len(DENIED)}가지, 기대와 다른 것 {len(wrong)}",
            detail=" ; ".join(wrong),
        )


def header_round(ctx: Ctx, report: Report) -> None:
    with report.rounds.round(f"5.{ctx.tag}.뒷단으로 넘기는 헤더") as slot:
        sent = {"X-Forwarded-For": "203.0.113.9", "X-Forwarded-Proto": "http", "Host": "edge.test"}
        reply = one(N1, get(SERVER4, "/end-user/runs", headers=sent))
        stub = reply.stub
        got = {key: as_text(stub.get(key)) for key in ("xff", "xfp", "host", "http_version")}
        wanted = {
            "xff": NEIGHBOR4[N1],
            "xfp": "https",
            "host": "edge.test",
            "http_version": "HTTP/1.1",
        }
        report.close(
            slot,
            measured=reply.status == 200 and reply.stub_name == "serve",
            result="받은 값을 덮어쓴다" if got == wanted else "기대와 다르다",
            detail=f"X-Forwarded-For 203.0.113.9, X-Forwarded-Proto http 를 보냈고 뒷단은 {got}",
        )


def body_round(ctx: Ctx, report: Report) -> None:
    with report.rounds.round(f"5.{ctx.tag}.본문 크기 상한(client_max_body_size 1m)") as slot:
        results = ask(
            N1,
            [
                get(SERVER4, "/end-user/runs", method="POST", body_bytes=512 * 1024),
                get(SERVER4, "/end-user/runs", method="POST", body_bytes=2 * 1024 * 1024),
            ],
        )
        small, large = replies_of(results, 0), replies_of(results, 1)
        under = small[0] if small else Reply(asked=False)
        over = large[0] if large else Reply(asked=False)
        passed = under.status == 200 and as_number(under.stub.get("body_bytes")) == 512 * 1024
        report.close(
            slot,
            measured=under.asked and over.asked and passed,
            result=f"512KiB 는 뒷단이 받고 2MiB 는 {over.brief()}"
            + ("(nginx 가 답한다)" if not over.stub_name else "(뒷단이 답했다)"),
        )


def sse_round(ctx: Ctx, report: Report) -> None:
    for accel, label in (("1", "X-Accel-Buffering: no 있음"), ("0", "그 헤더 없음(대조)")):
        with report.rounds.round(f"5.{ctx.tag}.SSE.{label}") as slot:
            spec = get(SERVER4, f"/end-user/sse?n=4&gap=0.5&accel={accel}", timeout=15.0)
            spec["kind"] = "sse"
            results = ask(N1, [spec])
            item = as_map(results[0] if results else None)
            arrivals = [as_number(value) for value in as_list(item.get("arrivals"))]
            spread = arrivals[-1] - arrivals[0] if arrivals else 0.0
            report.close(
                slot,
                measured=item.get("status") == 200 and len(arrivals) == 4,
                result="이벤트가 띄엄띄엄 온다" if spread > 1.0 else "이벤트가 끝에 한꺼번에 온다",
                detail=f"data 줄 넷이 닿은 초 {arrivals}(뒷단은 0.5초 간격으로 낸다)",
            )


def nginx_test(report: Report, label: str, tls: str, *flags: str, expect: str) -> None:
    """그 인증서 폴더와 사용자로 `nginx -t` 를 돌린다(배치의 proxy 서비스 정의 그대로)."""
    with report.rounds.round(label) as slot:
        done = compose(
            BASE, "run", "--rm", "--no-deps", "-T", *flags, "proxy", "nginx", "-t", tls=tls
        )
        key = server("stat", "-c", "%u:%g %a", f"{tls}/privkey.pem").out.strip()
        if "test is successful" in done.both and done.code == 0:
            seen, result = "ok", "설정 검사를 지난다"
        elif "Permission denied" in done.both and "privkey.pem" in done.both:
            seen, result = "key", "키를 읽지 못한다(Permission denied)"
        elif "chown(" in done.both and "Operation not permitted" in done.both:
            seen, result = "chown", "임시 폴더의 소유자를 바꾸지 못한다(chown, EPERM)"
        else:
            seen, result = "", f"알 수 없는 실패({tail(done.both, 1)})"
        report.close(
            slot,
            measured=seen != "",
            result=result + ("" if seen == expect else " (어림과 다르다)"),
            detail=f"키 파일 {key}",
        )


def process_uids(container: str) -> list[str]:
    """컨테이너의 프로세스마다 실제·유효 uid("101 101" 꼴). 서버 커널의 /proc 에서 읽는다. dind 의
    `docker top` 은 BusyBox ps 를 불러 첫 칸이 UID 가 아니라 PID 다(edge-run5 의 원본)."""
    pids = inner("top", container, "-o", "pid").out.split()[1:]
    if not pids:
        return []
    shown = server("grep", "^Uid:", *(f"/proc/{pid}/status" for pid in pids)).out
    return [" ".join(line.split()[1:3]) for line in shown.splitlines() if "Uid:" in line]


def nonroot_rounds(ctx: Ctx, report: Report) -> None:
    with report.rounds.round(f"5.{ctx.tag}.프록시 컨테이너의 사용자") as slot:
        top = inner("top", f"{PROJECT}-proxy-1").out.splitlines()
        master = any("nginx: master process" in line for line in top)
        uids = process_uids(f"{PROJECT}-proxy-1")
        template = "user={{.Config.User}} readonly={{.HostConfig.ReadonlyRootfs}}"
        template += " capdrop={{.HostConfig.CapDrop}}"
        shape = inner("inspect", f"{PROJECT}-proxy-1", "--format", template)
        report.close(
            slot,
            measured=master and len(uids) == len(top) - 1 > 0,
            result=f"모든 프로세스의 실제·유효 UID 가 {sorted(set(uids))}",
            detail=f"{shape.out.strip()}, 프로세스 {len(uids)}개(/proc/<pid>/status)",
        )

    base = f"5.{ctx.tag}.nginx -t"
    nginx_test(report, f"{base}.uid 101, 키 root:root 600", "/probe-tls/root600", expect="key")
    nginx_test(report, f"{base}.uid 101, 키 root:101 640", TLS_MAIN, expect="ok")
    nginx_test(report, f"{base}.uid 101, 키 101:101 600", "/probe-tls/own101", expect="ok")
    # 대조. root 로 돌면 nginx 는 -t 에서도 임시 폴더의 소유자를 worker 사용자로 바꾸려 하고,
    # 서비스 정의의 cap_drop: [ALL] 이 그 chown 을 막는다고 어림했다. 그래서 CHOWN 을 더한 갈래도
    # 둔다.
    as_root = ("--user", "0:0")
    label = f"{base}.root, 키 root:root 600(대조)"
    nginx_test(report, label, "/probe-tls/root600", *as_root, expect="chown")
    label = f"{base}.root 에 CHOWN 을 더함, 키 root:root 600(대조)"
    nginx_test(report, label, "/probe-tls/root600", *as_root, "--cap-add", "CHOWN", expect="ok")

    with report.rounds.round(f"5.{ctx.tag}.root 아닌 사용자가 80·443 에 바로 묶기") as slot:
        payload = base64.b64encode(
            json.dumps([{"kind": "bind", "port": 80}, {"kind": "bind", "port": 443}]).encode()
        ).decode()
        flags = ("--user", "101:101", "--cap-drop", "ALL", "-v", "/probe/client.py:/client.py:ro")
        done = inner("run", "--rm", *flags, PYTHON_TAG, "python", "/client.py", payload)
        results = as_list(parse(done.out.partition("PROBE-RESULT ")[2]))
        bound = [as_map(item).get("bound") is True for item in results]
        uids = {as_number(as_map(item).get("uid")) for item in results}
        start = inner(
            "run", "--rm", PYTHON_TAG, "cat", "/proc/sys/net/ipv4/ip_unprivileged_port_start"
        )
        report.close(
            slot,
            measured=len(results) == 2 and uids == {101.0},
            result="묶인다" if all(bound) else f"묶이지 않는다({bound})",
            detail=f"컨테이너 안의 net.ipv4.ip_unprivileged_port_start={start.out.strip()}, "
            "nginx 가 아니라 파이썬 소켓으로 봤다",
        )

    unprivileged = ("compose.yml", "compose.unprivileged.yml")
    stack_down(BASE)
    with report.rounds.round(f"5.{ctx.tag}.nginx-unprivileged 이미지에 edge.conf 만 얹기") as slot:
        up = stack_up(unprivileged)
        reply = one(N1, get(SERVER4, "/portal/"))
        uids = process_uids(f"{PROJECT}-proxy-1")
        image = inner("inspect", f"{PROJECT}-proxy-1", "--format", "{{.Config.Image}}").out.strip()
        report.close(
            slot,
            measured=up and image == NGINX_UNPRIV_TAG and reply.asked and len(uids) > 0,
            result=f"{reply.brief()}({reply.stub_name}), 인증서 지문 "
            + ("같음" if reply.cert == ctx.cert else "다름")
            + f", 실제·유효 UID {sorted(set(uids))}",
        )
    stack_down(unprivileged)
    stack_up(BASE)
    refresh(ctx)


# ---------------------------------------------------------------------------------------------
# 항목 6. 호스트 폴더와 볼륨의 쓰기 권한

WRITE = 'id -u; stat -c "%u:%g %a" /data; touch /data/probe.txt && echo WROTE'


def write_round(
    report: Report, label: str, mount: str, image: str, *, user: str = "10001:10001"
) -> bool:
    """고정 uid 로 띄운 컨테이너가 /data 에 파일을 만들 수 있는가."""
    wrote = False
    with report.rounds.round(label) as slot:
        done = inner(
            "run", "--rm", "--user", user, "-v", f"{mount}:/data", image, "sh", "-c", WRITE
        )
        lines = done.out.splitlines()
        uid = lines[0].strip() if lines else ""
        seen = lines[1].strip() if len(lines) > 1 else ""
        wrote = "WROTE" in done.out
        denied = "Permission denied" in done.err
        report.close(
            slot,
            measured=uid == user.split(":")[0] and seen != "" and (wrote or denied),
            result="쓴다" if wrote else "쓰지 못한다(Permission denied)",
            detail=f"컨테이너의 uid {uid}, 컨테이너가 본 /data 의 소유자와 권한 {seen}",
        )
    return wrote


def section_mounts(ctx: Ctx, report: Report) -> None:
    base = f"6.{ctx.tag}"
    owned = "ri-edge-owned:probe"
    server("mkdir", "-p", "/srv/ri-edge/traces")
    write_round(report, f"{base}.root 소유의 호스트 폴더를 붙임", "/srv/ri-edge/traces", PYTHON_TAG)
    write_round(
        report,
        f"{base}.없는 호스트 경로를 붙임(Docker 가 만든다)",
        "/srv/ri-edge/missing",
        PYTHON_TAG,
    )
    made = server("stat", "-c", "%u:%g %a", "/srv/ri-edge/missing").out.strip()
    print(f"[덧붙임] {base}: Docker 가 만든 /srv/ri-edge/missing 의 소유자와 권한은 {made}")
    server("chown", "10001:10001", "/srv/ri-edge/traces")
    if write_round(
        report,
        f"{base}.소유자를 10001 로 바꾼 호스트 폴더를 붙임",
        "/srv/ri-edge/traces",
        PYTHON_TAG,
    ):
        owner = server("stat", "-c", "%u:%g", "/srv/ri-edge/traces/probe.txt").out.strip()
        print(f"[덧붙임] {base}: 호스트에서 본 새 파일의 소유자는 {owner}")

    # 이미지 안의 /data 가 10001 소유인 이미지. 빈 named volume 은 처음 붙을 때 그 소유자를
    # 물려받는다.
    build = ("sh", "-c", "mkdir -p /data && chown 10001:10001 /data")
    inner("run", "--name", "ri-edge-owned-build", "--user", "0:0", PYTHON_TAG, *build)
    inner("commit", "ri-edge-owned-build", owned)
    inner("rm", "-f", "ri-edge-owned-build")
    for name in ("ri-edge-vol-plain", "ri-edge-vol-owned", "ri-edge-vol-rooted"):
        inner("volume", "create", name)
    write_round(
        report, f"{base}.빈 named volume, 이미지에 /data 없음", "ri-edge-vol-plain", PYTHON_TAG
    )
    write_round(
        report, f"{base}.빈 named volume, 이미지의 /data 가 10001 소유", "ri-edge-vol-owned", owned
    )
    rooted = ("--user", "0:0", "-v", "ri-edge-vol-rooted:/data")
    inner("run", "--rm", *rooted, PYTHON_TAG, "touch", "/data/root.txt")
    label = f"{base}.root 가 먼저 쓴 named volume, 이미지의 /data 가 10001 소유"
    write_round(report, label, "ri-edge-vol-rooted", owned)


# ---------------------------------------------------------------------------------------------
# 항목 7. 안쪽 네트워크에 IPv6 를 켠 배치와 IPv6 경유 공격

INNER6_SUBNET = "fd00:30::/64"  # compose.ipv6.yml 의 안쪽 IPv6 대역과 같아야 한다
OPEN6_SUBNET = "fd00:31::/64"
OPEN6_V4_SUBNET = "172.29.0.0/24"
TRANSIT6 = (*BASE, "compose.ipv6.yml", "compose.ipv6-listen.yml")
TRANSIT6_TARGETS = (
    # (이름, 표에 적을 말, 포트, 방식, 답할 대역)
    ("admin", "관리 화면 컨테이너의 IPv6:3000(127.0.0.1 에만 발행)", 3000, "http", "admin"),
    ("serve", "serve 컨테이너의 IPv6:8000(발행 안 함)", 8000, "http", "serve"),
    ("proxy", "프록시 컨테이너의 IPv6:8443(모든 주소에 발행)", 8443, "https", "portal"),
)


def counters6() -> dict[str, int]:
    """`counters` 의 IPv6 판. 서버의 `ip6tables-save -c` 를 같은 꼴로 읽는다."""
    table = ""
    found: dict[str, int] = {}
    for line in server("ip6tables-save", "-c").out.splitlines():
        if line.startswith("*"):
            table = line[1:]
        elif matched := RULE.match(line):
            found[f"{table} {matched[2]}"] = int(matched[1])
        elif matched := POLICY.match(line):
            found[f"{table} :{matched[1]} {matched[2]}"] = int(matched[3])
    return found


def forward_policy6() -> str:
    """서버의 ip6tables filter FORWARD 사슬의 정책(ACCEPT 나 DROP)."""
    listed = server("ip6tables", "-S", "FORWARD").out.splitlines()
    return listed[0].removeprefix("-P FORWARD ").strip() if listed else ""


def services6() -> dict[str, str]:
    """안쪽 네트워크의 서비스마다 IPv6 주소(없으면 빈 글)."""
    info = as_list(parse(inner("network", "inspect", f"{PROJECT}_edge").out))
    network = as_map(info[0] if info else None)
    found: dict[str, str] = {}
    for item in as_map(network.get("Containers")).values():
        name = as_text(as_map(item).get("Name")).removeprefix(f"{PROJECT}-").rsplit("-", 1)[0]
        found[name] = as_text(as_map(item).get("IPv6Address")).split("/")[0]
    return found


def attack6(
    ctx: Ctx, report: Report, label: str, op: dict[str, Json], subnet: str, *, ready: bool
) -> None:
    """`attack` 의 IPv6 판(이웃은 n1). 표지는 그 목적지로 가는 패킷이 서버의 eth0 에 닿은 것
    (ip6tables 의 셈 전용 규칙)과, 경로와 대상의 양성 대조가 섰다는 것(ready)이다. 대역이 답하면 그
    대역이 본 TCP 상대 주소를 함께 적는다(이웃의 주소 그대로인지)."""
    with report.rounds.round(f"7.{ctx.tag}.{label}") as slot:
        before = counters6()
        reply = one(N1, op)
        after = counters6()
        grown = {key: after[key] - before.get(key, 0) for key in after}
        arrived = any(is_probe_rule(key, subnet) and count > 0 for key, count in grown.items())
        drops = [f"{key} (+{count})" for key, count in grown.items() if count > 0 and "DROP" in key]
        if reply.status:
            result = f"닿는다({reply.status}, 답한 쪽 {reply.stub_name or 'nginx'})"
        else:
            result = f"막힌다({reply.brief()})"
        peer = as_text(reply.stub.get("peer"))
        seen = f"대역이 본 상대 주소 {peer}, " if peer and reply.stub_name != "portal" else ""
        report.close(
            slot,
            measured=ready and arrived and reply.asked,
            result=result,
            detail=seen + "패킷 수가 늘어난 DROP: " + (" ; ".join(drops) if drops else "없음"),
        )


def section_transit6(ctx: Ctx, report: Report) -> None:
    """항목 7. 안쪽 네트워크에 IPv6 를 켜고 관리 화면과 serve 대역이 `::` 에도 듣게 한 배치. 끝나면
    IPv4 만의 배치로 되돌린다."""
    if not ctx.v6_path:
        why = "이웃이 서버의 IPv6 에 닿지 않아(회차 0 의 대조) 항목 7 을 뺐다"
        print(f"[건너뜀] 7.{ctx.tag}: {why}")
        # 요청한 항목을 재지 못한 회차는 측정 아님으로 적어 종료 코드가 0이 되지 않게 한다.
        report.rounds.record(f"7.{ctx.tag}.IPv6 경유", measured=False, result=why)
        return
    stack_down(BASE)
    ready = False
    addresses: dict[str, str] = {}
    with report.rounds.round(f"7.{ctx.tag}.안쪽 IPv6 켬.배치 띄우기") as slot:
        up = stack_up(TRANSIT6)
        enabled = inner("network", "inspect", f"{PROJECT}_edge", "--format", "{{.EnableIPv6}}")
        refresh(ctx)
        addresses = services6()
        inner6: dict[str, Json] = {name: addresses[name] for name in sorted(addresses)}
        facts: dict[str, Json] = {
            "scenario": f"{ctx.tag} 항목 7",
            "ip6tables": first_line(server("ip6tables", "-V")),
            "ipv6_forwarding": first_line(server("cat", "/proc/sys/net/ipv6/conf/all/forwarding")),
            "forward_policy_ipv6": forward_policy6(),
            "admin_port": inner("port", f"{PROJECT}-admin-1").out.strip(),
            "inner_ipv6": inner6,
        }
        report.facts.append(facts)
        ready = (
            up
            and enabled.out.strip() == "true"
            and all(addresses.get(name, "").startswith("fd00:30:") for name in ("admin", "serve"))
            and addresses.get("proxy", "").startswith("fd00:30:")
        )
        shown = ", ".join(f"{key}={value}" for key, value in facts.items() if key != "scenario")
        report.close(
            slot, measured=ready, result="떴다" if ready else "조건이 서지 않았다", detail=shown
        )
    if ready:
        transit6_rounds(ctx, report, addresses)
    stack_down(TRANSIT6)
    stack_up(BASE)
    refresh(ctx)


def transit6_rounds(ctx: Ctx, report: Report, addresses: dict[str, str]) -> None:
    # 양성 대조. 서버 자신에서 컨테이너의 IPv6 주소로 걸면 그 대역이 답한다.
    answered: dict[str, bool] = {}
    for name, _, port, scheme, stub in TRANSIT6_TARGETS:
        label = f"7.{ctx.tag}.서버 자신→{name} 컨테이너의 IPv6:{port}(양성 대조)"
        with report.rounds.round(label) as slot:
            op = get(addresses[name], "/portal/health", port=port, scheme=scheme, verify=False)
            reply = one(SELF, op)
            answered[name] = reply.status == 200 and reply.stub_name == stub
            report.close(
                slot,
                measured=reply.asked,
                result="닿는다" if answered[name] else f"닿지 않음({reply.brief()})",
                detail=f"답한 쪽 {reply.stub_name}" if reply.stub_name else reply.error[:120],
            )

    # 서버 주소로 거는 길. 항목 3 첫 줄의 IPv6 판이다.
    published = False
    with report.rounds.round(f"7.{ctx.tag}.서버 자신→127.0.0.1:3000(양성 대조)") as slot:
        reply = one(SELF, get("127.0.0.1", "/", port=3000, scheme="http"))
        published = reply.status == 200 and reply.stub_name == "admin"
        report.close(
            slot,
            measured=reply.asked,
            result="닿는다" if published else f"닿지 않음({reply.brief()})",
        )
    for label, port in (("n1→서버의 IPv6:3000", 3000), ("n1→서버의 IPv6:8000(발행 안 함)", 8000)):
        with report.rounds.round(f"7.{ctx.tag}.{label}") as slot:
            reply = one(N1, get(SERVER6, "/", port=port, scheme="http", timeout=3.0))
            report.close(
                slot,
                measured=reply.asked and published and ctx.v6_path,
                result=f"닿는다({reply.stub_name})"
                if reply.status
                else f"닿지 않음({reply.brief()})",
            )

    # 경유 공격. n1 이 안쪽 IPv6 대역으로 가는 경로를 서버의 바깥 IPv6 주소로 잡는다.
    helper(N1, "-6", "route", "replace", INNER6_SUBNET, "via", SERVER6)
    routed = f"via {SERVER6}" in helper(N1, "-6", "route", "get", addresses["admin"]).out
    server("ip6tables", "-t", "raw", "-I", "PREROUTING", "1", "-i", "eth0", "-d", INNER6_SUBNET)
    original = forward_policy6()
    for policy in (original, "DROP" if original == "ACCEPT" else "ACCEPT"):
        server("ip6tables", "-P", "FORWARD", policy)
        note = f"IPv6 FORWARD 정책 {forward_policy6()}"
        for attempt in range(1, ctx.repeat + 1):
            for name, label, port, scheme, _ in TRANSIT6_TARGETS:
                op = get(
                    addresses[name], "/portal/health", port=port, scheme=scheme, timeout=3.0,
                    verify=False,
                )  # fmt: skip
                name_round = f"경유.n1→{label}.{note}#{attempt}"
                ready = routed and answered.get(name, False)
                attack6(ctx, report, name_round, op, INNER6_SUBNET, ready=ready)
    server("ip6tables", "-P", "FORWARD", original)
    server("ip6tables", "-t", "raw", "-D", "PREROUTING", "-i", "eth0", "-d", INNER6_SUBNET)
    helper(N1, "-6", "route", "del", INNER6_SUBNET)
    raw("항목 7 경유 공격 뒤의 ip6tables-save -c", server("ip6tables-save", "-c").out)
    open_network_control6(ctx, report, original)


def open_network_control6(ctx: Ctx, report: Report, original: str) -> None:
    """IPv6 경유 경로 자체가 통한다는 양성 대조. 보호를 끈 네트워크(IPv6 의 nat-unprotected)의
    컨테이너에는 닿아야 한다. 정책 두 값에서 한 번씩 건다. 그 모드가 없는 판은 네트워크를 만들지
    못해 돌지 않는다."""
    option = "com.docker.network.bridge.gateway_mode_ipv6=nat-unprotected"
    name = "ri-edge-open6"
    subnets = ("--subnet", OPEN6_V4_SUBNET, "--subnet", OPEN6_SUBNET)
    made = inner("network", "create", "--ipv6", *subnets, "-o", option, name)
    if made.code != 0:
        why = f"만들지 못했다({tail(made.err, 1)})"
        print(f"[건너뜀] 7.{ctx.tag}.보호를 끈 네트워크: {why}")
        report.rounds.record(f"7.{ctx.tag}.보호를 끈 네트워크", measured=False, result=why)
        return
    mount = "/probe/stub.py:/stub.py:ro"
    inner(
        "run", "-d", "--name", f"{name}-stub", "--network", name, "-v", mount, PYTHON_TAG,
        "python", "/stub.py", "open", "8000", "::",
    )  # fmt: skip
    template = "{{range .NetworkSettings.Networks}}{{.GlobalIPv6Address}}{{end}}"
    address = inner("inspect", f"{name}-stub", "--format", template).out.strip()
    helper(N1, "-6", "route", "replace", OPEN6_SUBNET, "via", SERVER6)
    routed = f"via {SERVER6}" in helper(N1, "-6", "route", "get", address or "fd00:31::2").out
    server("ip6tables", "-t", "raw", "-I", "PREROUTING", "1", "-i", "eth0", "-d", OPEN6_SUBNET)
    time.sleep(1)
    listening = False
    label = f"7.{ctx.tag}.서버 자신→보호를 끈 네트워크의 컨테이너 IPv6:8000(양성 대조)"
    with report.rounds.round(label) as slot:
        reply = one(SELF, get(address, "/", port=8000, scheme="http", timeout=3.0))
        listening = reply.status == 200 and reply.stub_name == "open"
        report.close(
            slot,
            measured=reply.asked and address.startswith("fd00:31:"),
            result="닿는다" if listening else f"닿지 않음({reply.brief()})",
            detail=f"그 컨테이너의 IPv6 주소 {address}",
        )
    for policy in (original, "DROP" if original == "ACCEPT" else "ACCEPT"):
        server("ip6tables", "-P", "FORWARD", policy)
        note = f"IPv6 FORWARD 정책 {forward_policy6()}"
        attack6(
            ctx, report, f"경유.n1→보호를 끈 네트워크의 컨테이너 IPv6:8000(양성 대조).{note}",
            get(address, "/", port=8000, scheme="http", timeout=3.0), OPEN6_SUBNET,
            ready=routed and listening,
        )  # fmt: skip
    server("ip6tables", "-P", "FORWARD", original)
    server("ip6tables", "-t", "raw", "-D", "PREROUTING", "-i", "eth0", "-d", OPEN6_SUBNET)
    helper(N1, "-6", "route", "del", OPEN6_SUBNET)
    raw("항목 7 양성 대조 뒤의 ip6tables-save -c", server("ip6tables-save", "-c").out)
    inner("rm", "-f", f"{name}-stub")
    inner("network", "rm", name)


# ---------------------------------------------------------------------------------------------
# 항목 8. 443 과 80 을 IPv4 에만 발행한 배치

V4_PUBLISH = (*BASE, "compose.v4-publish.yml")
DNAT_PORT = re.compile(r"--dport (443|80) ")
PROXY_PORT = re.compile(r"-host-port (443|80)\b")


@dataclass(frozen=True)
class Bindings:
    """서버 안에서 443·80 이 어느 주소족으로 열렸는지 본 것. 듣는 소켓(BusyBox `netstat -ltn`),
    docker-proxy 의 인자, nat 표의 DNAT 규칙(iptables 와 ip6tables)이다."""

    ran: bool
    listen4: list[str]
    listen6: list[str]
    proxies: list[str]
    dnat4: list[str]
    dnat6: list[str]

    @property
    def sees_v4(self) -> bool:
        """같은 방법이 IPv4 쪽 443 은 보는가(관찰의 양성 대조)."""
        listening = any(item.endswith(":443") for item in self.listen4)
        return listening or any("--dport 443 " in line for line in self.dnat4)

    @property
    def v6(self) -> list[str]:
        """IPv6 쪽에 443·80 이 열렸다는 관찰 전부."""
        proxies = [line for line in self.proxies if "-host-ip ::" in line]
        return [*self.listen6, *proxies, *self.dnat6]


def bindings() -> Bindings:
    listed = server("netstat", "-ltn")
    listen4: list[str] = []
    listen6: list[str] = []
    for line in listed.out.splitlines():
        fields = line.split()
        if len(fields) < 4 or not fields[0].startswith("tcp"):
            continue
        local = fields[3]
        if local.rsplit(":", 1)[-1] in ("443", "80"):
            (listen6 if local.count(":") > 1 else listen4).append(local)
    shown = server("sh", "-c", "ps -o args | grep docker-prox[y]")
    proxies = [line.strip() for line in shown.out.splitlines() if PROXY_PORT.search(line)]
    nat4 = server("iptables-save", "-t", "nat")
    nat6 = server("ip6tables-save", "-t", "nat")
    dnat4 = [line for line in nat4.out.splitlines() if "DNAT" in line and DNAT_PORT.search(line)]
    dnat6 = [line for line in nat6.out.splitlines() if "DNAT" in line and DNAT_PORT.search(line)]
    ran = listed.code == 0 and nat4.code == 0 and nat6.code == 0
    return Bindings(ran, listen4, listen6, proxies, dnat4, dnat6)


def bindings_round(ctx: Ctx, report: Report, label: str) -> None:
    """443·80 이 IPv6 쪽에 열렸는가. 같은 방법이 IPv4 쪽 443 을 볼 때만 측정이다."""
    with report.rounds.round(f"8.{ctx.tag}.{label}") as slot:
        seen = bindings()
        found = seen.v6
        report.close(
            slot,
            measured=seen.ran and seen.sees_v4,
            result="IPv6 쪽 443·80 없음" if not found else f"IPv6 쪽 443·80 있음({len(found)}가지)",
            detail=f"IPv4 듣는 소켓 {seen.listen4}, IPv6 듣는 소켓 {seen.listen6}, "
            f"docker-proxy {seen.proxies}, iptables DNAT {seen.dnat4}, ip6tables DNAT {seen.dnat6}",
        )


def v6_controls() -> tuple[bool, dict[str, bool]]:
    """서버 호스트의 [::] 대조 포트를 띄워 이웃 둘과 서버 자신이 닿는지 본다(띄웠는지, 닿았는지)."""
    control = "ri-edge-v6-control"
    listen = ["python", "-m", "http.server", str(V6_CONTROL_PORT), "--bind", "::"]
    started = inner("run", "-d", "--name", control, "--network", "host", PYTHON_TAG, *listen)
    time.sleep(2)
    seen = {
        N1: tcp(N1, SERVER6, V6_CONTROL_PORT),
        N2: tcp(N2, SERVER6, V6_CONTROL_PORT),
        "서버 자신 ::1": tcp(SELF, "::1", V6_CONTROL_PORT),
        "서버 자신 바깥 IPv6": tcp(SELF, SERVER6, V6_CONTROL_PORT),
    }
    inner("rm", "-f", control)
    return started.code == 0, seen


def section_v4_publish(ctx: Ctx, report: Report) -> None:
    """항목 8. 안쪽 네트워크는 IPv4 뿐이고 프록시의 443 과 80 을 IPv4(0.0.0.0)에만 발행한 배치. 항목
    1 의 갈래를 그 배치에서 다시 돌고(회차 이름은 `1.<시나리오>.443·80 IPv4 에만 발행.…`), 80 의
    IPv6 와 서버 안의 443·80 의 IPv6 쪽을 본다. 끝나면 시제품 배치로 되돌린다."""
    label = "시제품 배치(443·80 을 모든 주소에 발행).IPv6 쪽 443·80(관찰의 대조)"
    bindings_round(ctx, report, label)
    stack_down(BASE)
    ready = False
    with report.rounds.round(f"8.{ctx.tag}.443·80 IPv4 에만 발행.배치 띄우기") as slot:
        up = stack_up(V4_PUBLISH)
        bound = sorted(inner("port", f"{PROJECT}-proxy-1").out.strip().splitlines())
        refresh(ctx)
        wanted = ["8080/tcp -> 0.0.0.0:80", "8443/tcp -> 0.0.0.0:443"]
        ready = up and bound == wanted and "172.30.0.1" in ctx.gateways
        report.close(
            slot,
            measured=ready,
            result="떴다" if ready else "조건이 서지 않았다",
            detail=f"docker port: {bound}",
        )
    if ready:
        bindings_round(ctx, report, "443·80 IPv4 에만 발행.IPv6 쪽 443·80")
        v4_publish_rounds(ctx, report)
    stack_down(V4_PUBLISH)
    stack_up(BASE)
    refresh(ctx)


def v4_publish_rounds(ctx: Ctx, report: Report) -> None:
    # 닿지 않는 회차의 대조를 이 배치에서 다시 본다. 이웃 둘이 모두 닿아야 이웃의 IPv6 회차를 센다.
    saved = (ctx.v6_path, ctx.self6_path)
    with report.rounds.round(f"8.{ctx.tag}.443·80 IPv4 에만 발행.IPv6 대조 포트") as slot:
        started, seen = v6_controls()
        ctx.v6_path = ctx.lan6 and seen[N1] and seen[N2]
        ctx.self6_path = seen["서버 자신 ::1"] and (seen["서버 자신 바깥 IPv6"] or not ctx.lan6)
        report.close(
            slot,
            measured=started,
            result="모두 닿는다" if all(seen.values()) else "닿지 않은 쪽이 있다",
            detail=", ".join(f"{who_}={reached}" for who_, reached in seen.items()),
        )
    section_addresses(ctx, report, "443·80 IPv4 에만 발행")
    for attempt in range(1, ctx.repeat + 1):
        for where in (N1, N2):
            with report.rounds.round(f"8.{ctx.tag}.{where}→서버의 IPv6:80#{attempt}") as slot:
                reply = one(where, get(SERVER6, "/portal/", port=80, scheme="http", timeout=3.0))
                report.close(
                    slot,
                    measured=reply.asked and ctx.v6_path,
                    result=f"닿는다({reply.status}, {reply.headers.get('server', '')})"
                    if reply.status
                    else f"닿지 않음({reply.brief()})",
                )
        with report.rounds.round(f"8.{ctx.tag}.n1→서버의 IPv4:80(대조)#{attempt}") as slot:
            host = {"Host": "edge.test"}
            reply = one(N1, get(SERVER4, "/portal/", port=80, scheme="http", headers=host))
            redirected = reply.status == 308 and reply.headers.get("server") == "nginx"
            report.close(
                slot,
                measured=reply.asked,
                result="nginx 의 308" if redirected else f"다르다({reply.brief()})",
                detail=f"Location {reply.headers.get('location', '')}",
            )
    ctx.v6_path, ctx.self6_path = saved


# ---------------------------------------------------------------------------------------------


def scenario(
    ctx: Ctx, report: Report, sections: set[int], token: str, work: Path, *, keep: bool
) -> None:
    print(f"\n=== 시나리오 {ctx.tag} ===", flush=True)
    remove_server(token)
    if bring_up(ctx, report, token, work):
        if 1 in sections:
            section_addresses(ctx, report, "안쪽 IPv4 만")
        if 2 in sections and ctx.full:
            section_limits(ctx, report)
        if 5 in sections and ctx.full:
            section_tls(ctx, report)
        if 6 in sections and ctx.full:
            section_mounts(ctx, report)
        if 3 in sections:
            section_loopback(ctx, report)
        if 1 in sections and ctx.lan6 and ctx.major >= 29:
            section_addresses_dual(ctx, report)
        if 4 in sections and ctx.mode == "on":
            section_wrong_port(ctx, report)
        if 7 in sections:
            section_transit6(ctx, report)
        if 8 in sections:
            section_v4_publish(ctx, report)
    raw(f"{ctx.tag} 프록시 기록", proxy_log())
    if not keep:
        remove_server(token)


def main() -> int:
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="단독 배포의 가장자리를 dind 로 잰다")
    parser.add_argument("--sections", default="1,2,3,4,5,6")
    parser.add_argument("--engines", default="29.9.2,28.0.0,27.5.1")
    parser.add_argument("--modes", default="on,off")
    parser.add_argument("--work", default="")
    parser.add_argument("--repeat", type=int, default=2, help="항목 1 과 3 의 갈래마다 회차 수")
    parser.add_argument("--keep", action="store_true", help="끝난 뒤 컨테이너와 네트워크를 남긴다")
    args = parser.parse_args()
    sections = {int(item) for item in str(args.sections).split(",") if item}
    engines = [item for item in str(args.engines).split(",") if item in DIND]
    modes = [item for item in str(args.modes).split(",") if item in ("on", "off")]
    work = (
        Path(str(args.work)).resolve() if args.work else Path(tempfile.mkdtemp(prefix="ri-edge-"))
    )
    work.mkdir(parents=True, exist_ok=True)
    _raw.append(work / "raw.log")
    report = Report()
    token = secrets.token_hex(4)
    outer = docker("version", "--format", "{{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}")
    print(f"바깥 Docker {outer.out.strip()}, 원본 출력 {work / 'raw.log'}", flush=True)
    cleanup()
    try:
        problem = prepare_images(work, engines)
        if problem:
            print(problem)
            return 2
        lan6 = start_lan(token)
        start_neighbors(token, lan6=lan6)
        loop_routed = start_loopback_neighbor(token) if 3 in sections else False
        for engine in engines:
            for mode in modes:
                full = engine == engines[0] and mode == "on"
                ctx = Ctx(engine, mode, lan6, full, repeat=max(1, int(args.repeat)))
                ctx.loop_routed = loop_routed
                scenario(ctx, report, sections, token, work, keep=bool(args.keep))
    finally:
        if not args.keep:
            cleanup()
            docker("rmi", *TAGS)
        for name in ("images.tar", "ca.pem"):
            (work / name).unlink(missing_ok=True)
    entries: list[Json] = [
        {"label": entry.label, "measured": entry.measured, "result": entry.result}
        for entry in report.rounds.entries
    ]
    document: Json = {"facts": report.facts, "rows": report.rows, "entries": entries}
    (work / "results.json").write_text(
        json.dumps(document, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n"
    )
    print("\n" + report.rounds.summary())
    print(f"결과 {work / 'results.json'}")
    return report.rounds.exit_code()


if __name__ == "__main__":
    sys.exit(main())
