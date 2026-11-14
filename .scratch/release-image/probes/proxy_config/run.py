"""release-image 명세가 고른 nginx 프록시 설정 조합이 실제로 맞물리는지 잰다. 결정은 하지 않고
회차마다 본 것을 한 줄씩 낸다.

저장소 루트에서

    uv run python .scratch/release-image/probes/proxy_config/run.py
        [--sections 0,1,2,3,4,5,6,7,8,9,10] [--work <원본 출력을 둘 폴더>] [--keep]

잴 설정은 같은 폴더의 `nginx/proxy.conf` 다(`bridge_edge/nginx/edge.conf` 에서 셋을 바꾼 것. 무엇을
바꿨는지는 그 파일의 머리 주석). 결과와 갈래는 같은 폴더의 `README.md` 에 있다.

어떻게 재나. 바깥 Docker 데몬(이 PC 에서는 Docker Desktop)에 보통의 브리지 네트워크를 만들고, 뒷단
대역 셋(`stub.py`, `0.0.0.0` 에만 묶는다)을 compose 처럼 서비스 이름(serve, widget, portal)을
별칭으로 붙여 띄운다. 그 앞에 nginx 를 uid 101, 읽기 전용 루트, `cap_drop ALL`, no-new-privileges,
`/tmp` tmpfs, init 으로 띄운다(`docker run` 의 같은 뜻의 옵션). 요청은 같은 네트워크의 클라이언트
컨테이너에서 `client.py` 가 보낸다. 호스트 포트는 쓰지 않는다. 시험용 인증서와 키는 실행 중에 이름
있는 볼륨 안에서 만들고 끝에 볼륨째 지운다.

필요한 것. 도는 Docker 데몬과 로컬에 이미 있는 이미지 둘(아래 NGINX_IMAGE, PYTHON_IMAGE 의 digest.
이 스크립트는 받지 않는다). 만드는 것은 이름이 `ri-pxy-` 로 시작하고 라벨 `ri-pxy-probe` 가 붙은
컨테이너·네트워크·볼륨이다. 시작과 끝에 그 라벨의 것만 지운다. 이미지 태그는 만들지 않는다.

항목마다의 표지. 표지가 없는 회차는 측정 아님으로 세고 종료 코드가 1 이다(`tools/probe_kit.py`).
0. `nginx -t` 가 돌아 성공이나 실패의 문구를 냈다. 이름이 풀리지 않는 자리(`--network none`)에서
   proxy.conf 가 지나는지 보고, 그 자리의 대조는 이름을 proxy_pass 에 바로 쓴 direct.conf 의 실패다.
1. 토큰 경로 변형. 요청마다 nginx 접근 기록에 그 rid 의 줄이 있다.
2. 한도를 넘긴 요청. 요청마다 접근 기록의 줄이 있고 거부된 요청마다 오류 기록에 그 rid 와 구역
   이름이 든 `limiting requests` 줄이 있다. 다른 경로의 회차는 그 뒤에 보낸 토큰 요청이 다시 거부된
   것(아직 한도를 넘긴 채였다)이 표지다.
3. 허용 목록. 모든 요청이 nginx 에 닿았고(접근 기록), 넘긴 경로의 rid 가 뒷단 기록에 있다(뒷단
   기록에서 찾는 방법이 듣는다는 양성 대조).
4. 80. 접근 기록에 308 줄이 있고, 443 으로 보낸 같은 꼴의 요청은 뒷단 기록에 있다(양성 대조).
5. 전달 머리. 뒷단에 바로 보낸 요청에서 뒷단이 보낸 그대로의 머리를 받는다(양성 대조).
6. SSE. 그 머리를 뺀 응답이 끝에 한꺼번에 왔다(양성 대조). 서지 않으면 그 회차는 측정 아님이다.
7. 본문 상한. 상한 아래의 본문이 뒷단에 닿았고(양성 대조), 넘는 본문에 nginx 가 답했거나 오류 기록에
   `client intended to send too large body` 줄이 있다.
8. 키 권한. 0600 은 컨테이너가 끝났고 기록에 키 파일의 `Permission denied` 가 있다. 0640 은 받은
   인증서의 지문이 만든 것과 같다.
9. 다시 만든 뒷단. 주소가 실제로 바뀌었고, 새 컨테이너가 자기 주소에서 스스로 답했고, 지우기 직전의
   요청이 옛 인스턴스에 닿았고, 닿았다고 센 요청이 새 컨테이너의 기록에 있다.
10. IPv6 를 켠 네트워크. 뒷단 이름이 AAAA 로도 풀린다(클라이언트에서 getaddrinfo). 요청마다 접근
    기록이 있다. resolve 설정의 회차는 양성 대조(이름을 바로 쓴 설정)가 IPv6 로 한 번이라도 걸었을
    때만 측정이다.

못 보는 것. 실제 뒷단 이미지가 아니다. 리눅스 서버가 아니라 Docker Desktop(WSL2) 위에서 돈다.
compose 가 아니라 `docker run` 으로 같은 옵션을 준다(서비스 이름은 네트워크 별칭이다). 걸린 시간은
이 PC 의 부하를 함께 탄다.
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
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds, Slot  # noqa: E402

LABEL = "ri-pxy-probe"
NET = "ri-pxy-net"
NET6 = "ri-pxy-net6"
ULA6 = "fd00:70:70::/64"
PROXY = "ri-pxy-proxy"
CLIENT = "ri-pxy-client"
EDGE = "edge.test"
TLS_VOLUME = "ri-pxy-tls"
TLS600_VOLUME = "ri-pxy-tls-root600"
CA_VOLUME = "ri-pxy-ca"
CA = "/ca/fullchain.pem"

# 2026-11-13 에 이 PC 에 받아 둔 공식 이미지의 색인 digest 다(nginx:1.30.6-alpine,
# python:3.12.10-slim-bookworm). 판은 실행마다 nginx -v 와 이미지의 환경 변수로 다시 적는다.
NGINX_IMAGE = "nginx@sha256:583b7f2fce1cdb8da5ad5c39ebd3c33b98b87d493190e548bdee1fa8c619c311"
PYTHON_IMAGE = "python@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db"

STUBS = {"serve": 8000, "widget": 3000, "portal": 3000}
TOKEN_RATE, TOKEN_BURST = 30, 10  # nginx/proxy.conf 의 portal_token 구역과 같아야 한다
HARDENED = (
    "--init",
    "--read-only",
    "--cap-drop",
    "ALL",
    "--security-opt",
    "no-new-privileges:true",
)
SUBJECT_NAMES = "DNS:edge.test,DNS:key600.test,DNS:key640.test,DNS:resolve6.test,DNS:direct6.test"
# 인증서와 키는 도우미 컨테이너의 tmpfs(/work)에서 만들고 볼륨 셋에 나눠 둔다. main 은 키를
# root:101 0640 으로, root600 은 root:root 0600 으로 두고, ca 에는 인증서(공개 쪽)만 둔다.
CERT_SCRIPT = "\n".join(
    (
        "set -e",
        "cd /work",
        "openssl req -x509 -newkey rsa:2048 -nodes -days 2 -keyout privkey.pem"
        f" -out fullchain.pem -subj /CN=edge.test -addext subjectAltName={SUBJECT_NAMES}"
        " 2>/dev/null",
        "cp fullchain.pem privkey.pem /main/",
        "cp fullchain.pem privkey.pem /root600/",
        "cp fullchain.pem /ca/",
        "chown 0:101 /main/privkey.pem && chmod 640 /main/privkey.pem",
        "chown 0:0 /root600/privkey.pem && chmod 600 /root600/privkey.pem",
        "chmod 644 /main/fullchain.pem /root600/fullchain.pem /ca/fullchain.pem",
        "stat -c 'STAT %n %u:%g %a' /main/* /root600/* /ca/*",
        "openssl x509 -in /ca/fullchain.pem -noout -fingerprint -sha256",
        "openssl version",
    )
)

ACCESS = re.compile(
    r'^(\S+) \[[^\]]+\] "((?:[^"\\]|\\.)*)" (\d{3}) limit=(\S+) up="([^"]*)" '
    r'rid=(\S+) uri="([^"]*)"$'
)
LISTENING = re.compile(r"^stub \S+ (\S+) listening on ")

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


def run(argv: list[str], *, timeout: float = 120) -> Done:
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
    raw(" ".join(argv)[:600], f"exit={done.code}\n--- stdout\n{done.out}\n--- stderr\n{done.err}")
    return done


def docker(*args: str, timeout: float = 120) -> Done:
    return run(["docker", *args], timeout=timeout)


def logs(container: str) -> str:
    """컨테이너의 기록 전체(표준 출력과 표준 오류). 이 함수는 원본 기록에 남기지 않는다(끝에 한 번
    남긴다)."""
    try:
        completed = subprocess.run(
            ["docker", "logs", container],
            input="",
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return ""
    return f"{completed.stdout}\n{completed.stderr}"


def wait_log(container: str, needles: list[str], timeout: float = 6.0) -> str:
    """기록에 찾는 글이 모두 들 때까지 기다린다(기록이 늦게 실리는 몫). 끝내 없으면 그때의 기록."""
    deadline = time.monotonic() + timeout
    text = logs(container)
    while not all(needle in text for needle in needles) and time.monotonic() < deadline:
        time.sleep(0.3)
        text = logs(container)
    return text


def bind(path: Path, target: str) -> str:
    return f"type=bind,source={path},target={target},readonly"


def volume_mount(name: str, target: str, *, readonly: bool = True) -> str:
    return f"type=volume,source={name},target={target}" + (",readonly" if readonly else "")


# ---------------------------------------------------------------------------------------------
# 띄우고 거두기


def labelled(kind: str, token: str = "") -> list[str]:
    """이 프로브의 라벨이 붙은 컨테이너·네트워크·볼륨. 라벨이 없는 것은 건드리지 않는다."""
    wanted = f"label={LABEL}={token}" if token else f"label={LABEL}"
    if kind == "container":
        return docker("ps", "-aq", "--filter", wanted).out.split()
    if kind == "network":
        return docker("network", "ls", "-q", "--filter", wanted).out.split()
    return docker("volume", "ls", "-q", "--filter", wanted).out.split()


def cleanup(token: str = "") -> None:
    if ids := labelled("container", token):
        docker("rm", "-f", "-v", *ids)
    if networks := labelled("network", token):
        docker("network", "rm", *networks)
    if volumes := labelled("volume", token):
        docker("volume", "rm", *volumes)


def run_detached(token: str, name: str, network: str, *argv: str) -> Done:
    return docker(
        "run", "-d", "--pull", "never", "--name", name, "--label", f"{LABEL}={token}",
        "--network", network, *argv,
    )  # fmt: skip


def addresses(container: str, network: str) -> tuple[str, str]:
    """그 네트워크에서 컨테이너가 받은 IPv4 와 IPv6 주소."""
    info = as_list(parse(docker("inspect", container).out))
    networks = as_map(
        as_map(as_map(info[0] if info else None).get("NetworkSettings")).get("Networks")
    )
    entry = as_map(networks.get(network))
    return as_text(entry.get("IPAddress")), as_text(entry.get("GlobalIPv6Address"))


def state_of(container: str) -> tuple[str, int]:
    info = as_list(parse(docker("inspect", container).out))
    state = as_map(as_map(info[0] if info else None).get("State"))
    return as_text(state.get("Status")), int(as_number(state.get("ExitCode")))


@dataclass(frozen=True)
class Stub:
    container: str
    service: str
    instance: str
    ipv4: str
    ipv6: str


def first_instance(container: str, timeout: float = 20) -> str:
    """뒷단 대역이 뜬 직후 낸 첫 줄의 인스턴스 표지. 뜨지 않았으면 빈 글."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for line in logs(container).splitlines():
            if matched := LISTENING.match(line.strip()):
                return matched[1]
        time.sleep(0.4)
    return ""


def start_stub(token: str, network: str, container: str, service: str) -> Stub:
    made = run_detached(
        token, container, network, "--network-alias", service, "--user", "10001:10001",
        *HARDENED, "--mount", bind(HERE / "stub.py", "/stub.py"),
        PYTHON_IMAGE, "python", "/stub.py", service, str(STUBS[service]),
    )  # fmt: skip
    instance = first_instance(container) if made.code == 0 else ""
    if not instance:
        raise RuntimeError(f"뒷단 {container} 가 뜨지 않았다: {tail(made.both)}")
    ipv4, ipv6 = addresses(container, network)
    return Stub(container, service, instance, ipv4, ipv6)


def start_nginx(
    token: str, container: str, network: str, alias: str, conf: str, tls: str = TLS_VOLUME
) -> Done:
    return run_detached(
        token, container, network, "--network-alias", alias, "--user", "101:101", *HARDENED,
        "--tmpfs", "/tmp",
        "--mount", bind(HERE / "nginx" / "nginx.conf", "/etc/nginx/nginx.conf"),
        "--mount", bind(HERE / "nginx" / conf, "/etc/nginx/conf.d/default.conf"),
        "--mount", volume_mount(tls, "/etc/nginx/tls"),
        NGINX_IMAGE,
    )  # fmt: skip


def start_client(token: str, container: str, network: str = NET) -> str:
    made = run_detached(
        token, container, network,
        "--mount", bind(HERE / "client.py", "/client.py"),
        "--mount", volume_mount(CA_VOLUME, "/ca"),
        PYTHON_IMAGE, "sleep", "infinity",
    )  # fmt: skip
    if made.code != 0:
        raise RuntimeError(f"클라이언트 {container} 를 띄우지 못했다: {tail(made.both)}")
    return addresses(container, network)[0]


def wait_nginx(container: str, timeout: float = 25) -> tuple[str, int, str]:
    """nginx 컨테이너가 작업 프로세스를 띄우거나 끝날 때까지 기다린다. (상태, 종료 코드, 기록)."""
    deadline = time.monotonic() + timeout
    while True:
        status, code = state_of(container)
        text = logs(container)
        started = "start worker process" in text
        if status != "running" or started or time.monotonic() > deadline:
            return status, code, text
        time.sleep(0.5)


# ---------------------------------------------------------------------------------------------
# 요청과 기록


def http_op(
    path: str,
    *,
    host: str = EDGE,
    port: int = 8443,
    scheme: str = "https",
    method: str = "GET",
    count: int = 1,
    rid: str = "",
    headers: Mapping[str, str] | None = None,
    body_bytes: int = 0,
    timeout: float = 8.0,
) -> dict[str, Json]:
    """client.py 에 넘길 http 일 하나. rid 는 `X-Probe-Rid` 헤더로 싣는다(경로는 그대로 둔다)."""
    sent: dict[str, Json] = {name: value for name, value in (headers or {}).items()}
    if rid:
        sent["X-Probe-Rid"] = rid
    return {
        "kind": "http",
        "scheme": scheme,
        "host": host,
        "port": port,
        "path": path,
        "method": method,
        "count": count,
        "headers": sent,
        "body_bytes": body_bytes,
        "timeout": timeout,
        "ca": CA if scheme == "https" else "",
    }


def ask(client: str, ops: list[dict[str, Json]], *, timeout: float = 180) -> list[Json]:
    """클라이언트 컨테이너에서 client.py 를 돌려 일마다의 결과를 받는다."""
    payload = base64.b64encode(json.dumps(ops).encode()).decode()
    done = docker("exec", client, "python", "/client.py", payload, timeout=timeout)
    for line in done.out.splitlines():
        if line.startswith("PROBE-RESULT "):
            return as_list(parse(line.removeprefix("PROBE-RESULT ")))
    return []


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
    def instance(self) -> str:
        return as_text(self.stub.get("instance"))

    @property
    def seen_path(self) -> str:
        return as_text(self.stub.get("path"))

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


def replies_of(results: list[Json], index: int) -> list[Reply]:
    if index >= len(results):
        return []
    return [reply_of(item) for item in as_list(results[index])]


def single(results: list[Json], index: int) -> Reply:
    found = replies_of(results, index)
    return found[0] if found else Reply(asked=False)


def codes(replies: list[Reply]) -> str:
    return " ".join(reply.brief() for reply in replies)


def span(replies: list[Reply]) -> float:
    """요청 묶음이 걸린 초."""
    return max((reply.start + reply.ms / 1000 for reply in replies), default=0.0)


@dataclass(frozen=True)
class Access:
    addr: str
    request: str
    status: int
    limit: str
    upstream: str
    rid: str
    uri: str


def accesses(log: str) -> dict[str, Access]:
    """nginx 접근 기록의 줄을 rid 로 찾게 모은다."""
    found: dict[str, Access] = {}
    for line in log.splitlines():
        if matched := ACCESS.match(line.strip()):
            entry = Access(
                matched[1], matched[2], int(matched[3]), matched[4], matched[5], matched[6],
                matched[7],
            )  # fmt: skip
            found[entry.rid] = entry
    return found


def error_lines(log: str, *needles: str) -> list[str]:
    return [line.strip() for line in log.splitlines() if all(item in line for item in needles)]


def limited(log: str, rid: str) -> list[str]:
    """그 rid 의 요청(질의 끝에 rid 를 둔 요청)이 portal_token 구역에서 거부됐다는 오류 기록의
    줄."""
    return error_lines(log, "limiting requests", 'zone "portal_token"', f"rid={rid} HTTP/")


def in_stub(text: str, rid: str) -> bool:
    return f" rid={rid} " in text


NGINX_ERROR = re.compile(r"\[(?:warn|error|crit|alert)\] \d+#\d+: (?:\*\d+ )?(.*?)(?:, client: |$)")


def error_kinds(log: str, *needles: str) -> dict[str, int]:
    """nginx 오류 기록(warn 이상)에서 찾는 글이 모두 든 줄을 문구별로 센다. 접근 기록의 줄은 수준
    표시가 없어 빠진다."""
    kinds: dict[str, int] = {}
    for line in error_lines(log, *needles):
        if matched := NGINX_ERROR.search(line):
            kinds[matched[1]] = kinds.get(matched[1], 0) + 1
    return kinds


# ---------------------------------------------------------------------------------------------
# 보고


@dataclass
class Report:
    rounds: Rounds = field(default_factory=Rounds)
    rows: list[Json] = field(default_factory=list[Json])
    facts: dict[str, Json] = field(default_factory=dict[str, Json])

    def close(self, slot: Slot, *, measured: bool, result: str, detail: str = "") -> None:
        slot.mark(measured=measured, result=result)
        self.rows.append(
            {"label": slot.label, "measured": measured, "result": result, "detail": detail}
        )
        head = "측정" if measured else "측정 아님"
        text = f"[{head}] {slot.label}: {result}" + (f" | {detail}" if detail else "")
        print(text, flush=True)
        raw("회차", text)


@dataclass
class Ctx:
    token: str
    cert: str = ""
    client_ip: str = ""
    stubs: dict[str, Stub] = field(default_factory=dict[str, Stub])
    fresh: int = 0

    def fresh_client(self) -> tuple[str, str]:
        """빈도 제한의 통이 비어 있는 새 클라이언트(새 주소). 회차끼리 서로의 몫을 먹지 않게
        한다."""
        self.fresh += 1
        name = f"ri-pxy-c{self.fresh}"
        return name, start_client(self.token, name)


# ---------------------------------------------------------------------------------------------
# 준비


def make_tls(ctx: Ctx, report: Report) -> bool:
    """인증서와 키를 볼륨 셋에 만든다."""
    for name in (TLS_VOLUME, TLS600_VOLUME, CA_VOLUME):
        docker("volume", "create", "--label", f"{LABEL}={ctx.token}", name)
    with report.rounds.round("준비.시험용 인증서와 키 만들기") as slot:
        done = docker(
            "run", "--rm", "--pull", "never", "--name", "ri-pxy-certs",
            "--label", f"{LABEL}={ctx.token}", "--network", "none", "--tmpfs", "/work",
            "--mount", volume_mount(TLS_VOLUME, "/main", readonly=False),
            "--mount", volume_mount(TLS600_VOLUME, "/root600", readonly=False),
            "--mount", volume_mount(CA_VOLUME, "/ca", readonly=False),
            PYTHON_IMAGE, "sh", "-c", CERT_SCRIPT,
        )  # fmt: skip
        modes = [line.removeprefix("STAT ") for line in done.out.splitlines() if "STAT " in line]
        printed = next((line for line in done.out.splitlines() if "Fingerprint=" in line), "")
        ctx.cert = printed.rpartition("=")[2].replace(":", "").lower()
        report.facts["cert_files"] = list[Json](modes)
        report.facts["openssl_for_cert"] = tail(done.out, 1)
        report.close(
            slot,
            measured=done.code == 0 and len(ctx.cert) == 64,
            result="만들었다" if done.code == 0 else f"실패({tail(done.err)})",
            detail=" ; ".join(modes),
        )
    return len(ctx.cert) == 64


def record_versions(ctx: Ctx, report: Report) -> None:
    server = docker("version", "--format", "{{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}")
    nginx = docker(
        "run", "--rm", "--pull", "never", "--name", "ri-pxy-version",
        "--label", f"{LABEL}={ctx.token}", "--entrypoint", "nginx", NGINX_IMAGE, "-v",
    )  # fmt: skip
    env = docker("image", "inspect", PYTHON_IMAGE, "--format", "{{json .Config.Env}}")
    python = [
        as_text(item).removeprefix("PYTHON_VERSION=")
        for item in as_list(parse(env.out))
        if as_text(item).startswith("PYTHON_VERSION=")
    ]
    kernel = docker("info", "--format", "{{.KernelVersion}} {{.OperatingSystem}}")
    report.facts["docker_server"] = server.out.strip()
    report.facts["docker_host"] = kernel.out.strip()
    report.facts["nginx"] = tail(nginx.both, 1)
    report.facts["python"] = python[0] if python else ""
    print(f"판: {json.dumps(report.facts, ensure_ascii=False)}", flush=True)


def start_stack(ctx: Ctx, report: Report) -> bool:
    """IPv4 네트워크와 뒷단 셋, 클라이언트, 프록시를 띄우고 프록시를 거쳐 뒷단 셋에 닿을 때까지
    기다린다."""
    docker("network", "create", "--label", f"{LABEL}={ctx.token}", NET)
    for service in STUBS:
        ctx.stubs[service] = start_stub(ctx.token, NET, f"ri-pxy-{service}", service)
    ctx.client_ip = start_client(ctx.token, CLIENT)
    ready = False
    with report.rounds.round("준비.프록시를 띄우고 뒷단 셋에 닿기") as slot:
        made = start_nginx(ctx.token, PROXY, NET, EDGE, "proxy.conf")
        status, _, _ = wait_nginx(PROXY)
        rid = secrets.token_hex(3)
        paths = {"serve": "/end-user/ready", "widget": "/widget/ready", "portal": "/portal/ready"}
        ops: list[dict[str, Json]] = []
        for service, path in paths.items():
            op = http_op(f"{path}?rid={rid}-{service}-{{i}}", rid=f"{rid}-{service}-{{i}}")
            op.update({"kind": "poll", "window": 30.0, "gap": 0.5})
            op["until_instance"] = ctx.stubs[service].instance
            ops.append(op)
        results = ask(CLIENT, ops)
        shown: list[str] = []
        reached = 0
        for index, service in enumerate(paths):
            samples = replies_of(results, index)
            hit = next((s for s in samples if s.instance == ctx.stubs[service].instance), None)
            reached += hit is not None
            before = codes([s for s in samples if s is not hit])
            when = f"{hit.start:.1f}초" if hit else "닿지 않음"
            shown.append(f"{service}: {when}(그 전 {before or '없음'})")
        top = docker("top", PROXY).out.splitlines()
        workers = sum("worker process" in line for line in top)
        report.facts["nginx_workers"] = workers
        report.facts["net4"] = {
            "client": ctx.client_ip,
            **{name: stub.ipv4 for name, stub in ctx.stubs.items()},
        }
        ready = made.code == 0 and status == "running" and reached == len(paths)
        report.close(
            slot,
            measured=ready,
            result="뜨고 뒷단 셋에 닿았다" if ready else f"서지 않았다(상태 {status})",
            detail=" ; ".join(shown) + f" ; 작업 프로세스 {workers}개",
        )
    return ready


# ---------------------------------------------------------------------------------------------
# 항목 0. 설정 검사


def nginx_test(ctx: Ctx, report: Report, label: str, conf: str, *, expect_ok: bool) -> None:
    with report.rounds.round(label) as slot:
        done = docker(
            "run", "--rm", "--pull", "never", "--name", f"ri-pxy-test-{conf.split('.')[0]}",
            "--label", f"{LABEL}={ctx.token}", "--network", "none", "--user", "101:101",
            *HARDENED, "--tmpfs", "/tmp",
            "--mount", bind(HERE / "nginx" / "nginx.conf", "/etc/nginx/nginx.conf"),
            "--mount", bind(HERE / "nginx" / conf, "/etc/nginx/conf.d/default.conf"),
            "--mount", volume_mount(TLS_VOLUME, "/etc/nginx/tls"),
            NGINX_IMAGE, "nginx", "-t",
        )  # fmt: skip
        passed = "test is successful" in done.both and done.code == 0
        failed = "test failed" in done.both and done.code != 0
        emerg = next((line.strip() for line in done.both.splitlines() if "[emerg]" in line), "")
        verdict = "지난다" if passed else "실패한다"
        report.close(
            slot,
            measured=passed or failed,
            result=verdict + ("" if passed == expect_ok else " (기대와 다르다)"),
            detail=emerg[-220:],
        )


def section_test(ctx: Ctx, report: Report) -> None:
    base = "0.nginx -t, 뒷단 이름이 풀리지 않는 자리(--network none)"
    nginx_test(ctx, report, f"{base}.proxy.conf", "proxy.conf", expect_ok=True)
    nginx_test(ctx, report, f"{base}.direct.conf(대조)", "direct.conf", expect_ok=False)


# ---------------------------------------------------------------------------------------------
# 항목 1. 토큰 경로 변형

# (보낸 경로, 기대: 빈도 제한에 드는가, 기대: 뒷단이 받는 경로). 앞의 아홉은 bridge_edge/README.md
# 2절 표의 경로이고, 마지막 하나는 이 프로브가 더했다(세 변형을 겹치고 질의를 붙였다).
VARIANTS = (
    ("/portal/sites/demo/token", True, "/portal/sites/demo/token"),
    ("/portal/sites/demo/token?x=1", True, "/portal/sites/demo/token?x=1"),
    ("/portal/sites/de%6Do/token", True, "/portal/sites/demo/token"),
    ("/portal//sites/demo/token", True, "/portal/sites/demo/token"),
    ("/portal/sites/demo/x/../token", True, "/portal/sites/demo/token"),
    ("/portal/sites/demo/token/", False, "/portal/sites/demo/token/"),
    ("/portal/sites/demo/TOKEN", False, "/portal/sites/demo/TOKEN"),
    ("/portal/sites/demo/token%2F", False, "/portal/sites/demo/token/"),
    ("/portal/sites/demo/token;x", False, "/portal/sites/demo/token;x"),
    ("/portal//sites/de%6Do/x/../token?x=1", True, "/portal/sites/demo/token?x=1"),
)


def variant_round(ctx: Ctx, report: Report, attempt: int) -> None:
    rid = secrets.token_hex(3)
    with report.rounds.round(f"1.토큰 경로 변형#{attempt}") as slot:
        client, _ = ctx.fresh_client()
        ops = [
            http_op(path, method="POST", rid=f"{rid}-{index}")
            for index, (path, _, _) in enumerate(VARIANTS)
        ]
        results = ask(client, ops)
        log = wait_log(PROXY, [f"rid={rid}-{len(VARIANTS) - 1} uri="])
        found = accesses(log)
        shown: list[str] = []
        wrong: list[str] = []
        seen = 0
        for index, (path, inside, upstream) in enumerate(VARIANTS):
            entry = found.get(f"{rid}-{index}")
            reply = single(results, index)
            seen += entry is not None
            limit = entry.limit if entry else "?"
            uri = entry.uri if entry else "?"
            got = reply.seen_path if reply.stub_name else f"({reply.brief()})"
            shown.append(f"{path} → {reply.brief()} limit={limit} $uri={uri} 뒷단={got}")
            if (limit == "PASSED") != inside or got != upstream or reply.status != 200:
                wrong.append(path)
        inside_count = sum(1 for line in shown if "limit=PASSED" in line)
        report.close(
            slot,
            measured=seen == len(VARIANTS),
            result=f"제한 안 {inside_count}, 제한 밖 {len(VARIANTS) - inside_count}, "
            f"기대와 다른 것 {len(wrong)}{wrong if wrong else ''}",
            detail=" ; ".join(shown),
        )


# ---------------------------------------------------------------------------------------------
# 항목 2. 한도를 넘긴 요청과 빈 열쇠

TOKEN = "/portal/sites/demo/token"
ACK = "/portal/sites/demo/acknowledgement"


def overflow_round(ctx: Ctx, report: Report, attempt: int) -> None:
    """새 클라이언트 하나가 토큰 경로로 12번 연달아 보내고, 곧바로 다른 경로 둘과 토큰 경로 하나를
    더 보낸다. 모두 한 번의 client.py 안에서 차례로 간다."""
    count = TOKEN_BURST + 2
    rid = secrets.token_hex(3)
    others = (("GET", "/portal/"), ("POST", ACK))
    client, _ = ctx.fresh_client()
    ops = [http_op(f"{TOKEN}?rid={rid}-{{i}}", method="POST", rid=f"{rid}-{{i}}", count=count)]
    for index, (method, path) in enumerate(others):
        ops.append(http_op(f"{path}?rid={rid}-o{index}", method=method, rid=f"{rid}-o{index}"))
    ops.append(http_op(f"{TOKEN}?rid={rid}-last", method="POST", rid=f"{rid}-last"))
    results = ask(client, ops)
    log = wait_log(PROXY, [f"rid={rid}-last uri="])
    found = accesses(log)
    first = replies_of(results, 0)
    with report.rounds.round(f"2.토큰 경로로 {count}번 연달아#{attempt}") as slot:
        reached = all(f"{rid}-{index}" in found for index in range(count))
        attributed = all(
            reply.status == 200 or bool(limited(log, f"{rid}-{index}"))
            for index, reply in enumerate(first)
        )
        passed = sum(reply.status == 200 and reply.stub_name == "portal" for reply in first)
        rejected = [index + 1 for index, reply in enumerate(first) if reply.status == 429]
        refill = int(span(first) * TOKEN_RATE / 60)
        sample = next(iter(limited(log, f"{rid}-{rejected[0] - 1}")), "") if rejected else ""
        statuses = [found[f"{rid}-{i}"].limit for i in range(count) if f"{rid}-{i}" in found]
        report.close(
            slot,
            measured=reached and attributed and len(first) == count,
            result=f"200 {passed}번, 첫 429 는 {rejected[0] if rejected else '없음'}번째"
            f"(기대 200 {1 + TOKEN_BURST}~{1 + TOKEN_BURST + refill}번)",
            detail=f"상태 {codes(first)} ; limit 칸 {statuses} ; 걸린 초 {span(first):.2f} ; "
            f"첫 거부의 오류 기록: {sample[-260:]}",
        )
    with report.rounds.round(f"2.한도를 넘긴 클라이언트의 다른 경로#{attempt}") as slot:
        last = single(results, 1 + len(others))
        still = last.status == 429 and bool(limited(log, f"{rid}-last"))
        shown: list[str] = []
        free = True
        for index, (method, path) in enumerate(others):
            reply = single(results, 1 + index)
            entry = found.get(f"{rid}-o{index}")
            limit = entry.limit if entry else "?"
            free = free and reply.status == 200 and reply.stub_name == "portal" and limit == "-"
            shown.append(f"{method} {path} → {reply.brief()} limit={limit}")
        report.close(
            slot,
            measured=still and all(f"{rid}-o{i}" in found for i in range(len(others))),
            result="다른 경로는 200 이고 제한 밖(빈 값)" if free else "다른 경로도 걸렸다",
            detail=" ; ".join(shown) + f" ; 그 뒤 토큰 경로 → {last.brief()}(오류 기록에 거부 줄)",
        )


def empty_key_round(ctx: Ctx, report: Report, attempt: int) -> None:
    """빈 열쇠의 요청을 세지 않는지. 새 클라이언트가 확인 경로(빈 열쇠)로 15번 보낸 뒤 토큰 경로로
    12번 보낸다. 빈 열쇠의 요청을 하나의 통(빈 글)에서 센다면 확인 경로가 12번째부터 거부된다."""
    acks, tokens = 15, TOKEN_BURST + 2
    rid = secrets.token_hex(3)
    with report.rounds.round(f"2.빈 열쇠 {acks}번 뒤 토큰 경로 {tokens}번#{attempt}") as slot:
        client, _ = ctx.fresh_client()
        ops = [
            http_op(f"{ACK}?rid={rid}-a{{i}}", method="POST", rid=f"{rid}-a{{i}}", count=acks),
            http_op(f"{TOKEN}?rid={rid}-t{{i}}", method="POST", rid=f"{rid}-t{{i}}", count=tokens),
        ]
        results = ask(client, ops)
        log = wait_log(PROXY, [f"rid={rid}-t{tokens - 1} uri="])
        found = accesses(log)
        ack_replies, token_replies = replies_of(results, 0), replies_of(results, 1)
        ack_limits = sorted(
            {found[f"{rid}-a{i}"].limit for i in range(acks) if f"{rid}-a{i}" in found}
        )
        reached = all(f"{rid}-a{i}" in found for i in range(acks)) and all(
            f"{rid}-t{i}" in found for i in range(tokens)
        )
        ack_ok = sum(reply.status == 200 for reply in ack_replies)
        token_ok = sum(reply.status == 200 for reply in token_replies)
        rejected = [index + 1 for index, reply in enumerate(token_replies) if reply.status == 429]
        refill = int(span(token_replies) * TOKEN_RATE / 60)
        report.close(
            slot,
            measured=reached and len(ack_replies) == acks and len(token_replies) == tokens,
            result=f"확인 경로 200 {ack_ok}/{acks}(limit 칸 {ack_limits}), 그 뒤 토큰 경로 200 "
            f"{token_ok}번·첫 429 는 {rejected[0] if rejected else '없음'}번째"
            f"(기대 200 {1 + TOKEN_BURST}~{1 + TOKEN_BURST + refill}번)",
            detail=f"확인 경로 {codes(ack_replies)} ; 토큰 경로 {codes(token_replies)}",
        )


# ---------------------------------------------------------------------------------------------
# 항목 3. 허용 목록

ALLOWED = (
    ("/", "portal", "/"),
    ("/widget", "widget", "/widget"),
    ("/widget/x", "widget", "/widget/x"),
    ("/end-user/runs", "serve", "/end-user/runs"),
    ("/portal/", "portal", "/portal/"),
)
DENIED = ("/health", "/admin", "/api/agents", "/end-user", "/portal", "/plugins", "/WIDGET")


def allowlist_round(ctx: Ctx, report: Report, attempt: int) -> None:
    rid = secrets.token_hex(3)
    with report.rounds.round(f"3.허용 목록#{attempt}") as slot:
        ops = [http_op(path, rid=f"{rid}-a{index}") for index, (path, _, _) in enumerate(ALLOWED)]
        ops += [http_op(path, rid=f"{rid}-d{index}") for index, path in enumerate(DENIED)]
        results = ask(CLIENT, ops)
        log = wait_log(PROXY, [f"rid={rid}-d{len(DENIED) - 1} uri="])
        found = accesses(log)
        stub_logs = {name: logs(stub.container) for name, stub in ctx.stubs.items()}
        wrong: list[str] = []
        shown: list[str] = []
        control = 0
        for index, (path, name, upstream) in enumerate(ALLOWED):
            reply = single(results, index)
            logged = in_stub(stub_logs[name], f"{rid}-a{index}")
            control += logged
            got = f"{reply.stub_name} {reply.seen_path}" if reply.stub_name else "nginx"
            shown.append(f"{path}→{reply.brief()} {got}" + ("" if logged else "(뒷단 기록에 없음)"))
            if reply.status != 200 or reply.stub_name != name or reply.seen_path != upstream:
                wrong.append(path)
        hsts = 0
        leaked: list[str] = []
        for index, path in enumerate(DENIED):
            reply = single(results, len(ALLOWED) + index)
            has_hsts = "max-age" in reply.headers.get("strict-transport-security", "")
            hsts += has_hsts
            reached = [name for name, text in stub_logs.items() if in_stub(text, f"{rid}-d{index}")]
            leaked += [f"{path}→{name}" for name in reached]
            where = f"뒷단 {reached}" if reached else "뒷단 기록에 없음"
            shown.append(f"{path}→{reply.brief()}{' HSTS' if has_hsts else ''} {where}")
            if reply.status != 404 or reply.stub_name:
                wrong.append(path)
        answered = all(f"{rid}-a{i}" in found for i in range(len(ALLOWED))) and all(
            f"{rid}-d{i}" in found for i in range(len(DENIED))
        )
        report.close(
            slot,
            measured=answered and control > 0,
            result=f"넘김 {len(ALLOWED)}가지·404 {len(DENIED)}가지 가운데 기대와 다른 것 "
            f"{len(wrong)}{wrong if wrong else ''}, 404 에 HSTS {hsts}/{len(DENIED)}, "
            f"404 가 뒷단에 닿은 것 {len(leaked)}",
            detail=" ; ".join(shown) + f" ; 뒷단 기록에서 찾은 넘긴 요청 {control}",
        )


# ---------------------------------------------------------------------------------------------
# 항목 4. 80


def http80_round(ctx: Ctx, report: Report, attempt: int) -> None:
    rid = secrets.token_hex(3)
    path = "/portal/?a=1"
    with report.rounds.round(f"4.80 의 GET {path}#{attempt}") as slot:
        hosts = (("h", "edge.test"), ("p", "edge.test:8080"))
        ops = [
            http_op(path, port=8080, scheme="http", rid=f"{rid}-{tag}", headers={"Host": host})
            for tag, host in hosts
        ]
        ops.append(http_op(path, rid=f"{rid}-s"))  # 443 으로 같은 요청(뒷단 기록의 양성 대조)
        results = ask(CLIENT, ops)
        log = wait_log(PROXY, [f"rid={rid}-s uri="])
        found = accesses(log)
        portal_log = wait_log(ctx.stubs["portal"].container, [f" rid={rid}-s "])
        shown: list[str] = []
        good = True
        for index, (tag, host) in enumerate(hosts):
            reply = single(results, index)
            location = reply.headers.get("location", "")
            entry = found.get(f"{rid}-{tag}")
            reached = in_stub(portal_log, f"{rid}-{tag}")
            good = good and reply.status == 308 and location == "https://edge.test/portal/?a=1"
            good = good and not reached and not reply.stub_name
            logged = entry.status if entry else "없음"
            shown.append(
                f"Host {host} → {reply.brief()} Location {location}, 접근 기록 {logged}, "
                + ("뒷단에 닿았다" if reached else "뒷단 기록에 없다")
            )
        control = in_stub(portal_log, f"{rid}-s")
        measured = control and all(f"{rid}-{tag}" in found for tag, _ in hosts)
        report.close(
            slot,
            measured=measured,
            result="308 과 같은 Host 의 https 주소, 뒷단에 닿지 않는다"
            if good
            else "기대와 다르다",
            detail=" ; ".join(shown) + f" ; 443 대조는 뒷단 기록에 {'있다' if control else '없다'}",
        )


# ---------------------------------------------------------------------------------------------
# 항목 5. 전달 머리


def forwarded_round(ctx: Ctx, report: Report, attempt: int) -> None:
    rid = secrets.token_hex(3)
    spoof = {"X-Forwarded-For": "203.0.113.9", "X-Forwarded-Proto": "http"}
    with report.rounds.round(f"5.X-Forwarded-For 를 실어 보낸 요청#{attempt}") as slot:
        direct = http_op(
            "/end-user/whoami", host="serve", port=8000, scheme="http", rid=f"{rid}-d",
            headers=spoof,
        )  # fmt: skip
        results = ask(CLIENT, [direct, http_op("/end-user/whoami", rid=f"{rid}-n", headers=spoof)])
        log = wait_log(PROXY, [f"rid={rid}-n uri="])
        entry = accesses(log).get(f"{rid}-n")
        straight, through = single(results, 0), single(results, 1)
        sent_ok = as_text(straight.stub.get("xff")) == "203.0.113.9"
        sent_ok = sent_ok and as_text(straight.stub.get("xfp")) == "http"
        xff = as_text(through.stub.get("xff"))
        xfp = as_text(through.stub.get("xfp"))
        good = xff == ctx.client_ip and xfp == "https"
        report.close(
            slot,
            measured=sent_ok and through.stub_name == "serve" and entry is not None,
            result="뒷단은 클라이언트 주소 하나와 https 를 받는다" if good else "기대와 다르다",
            detail=f"nginx 거쳐 받은 X-Forwarded-For={xff}, X-Forwarded-Proto={xfp}, "
            f"$remote_addr={entry.addr if entry else '?'}, 클라이언트 주소 {ctx.client_ip} ; "
            f"뒷단에 바로 보낸 대조는 {straight.stub.get('xff')}, {straight.stub.get('xfp')}",
        )


# ---------------------------------------------------------------------------------------------
# 항목 6. SSE


def bunched(arrivals: list[float]) -> bool:
    """끝에 한꺼번에 왔다. 뒷단이 1.5초에 걸쳐 낸 넷이 1.2초 뒤에, 0.3초 안에 모두 왔다."""
    return len(arrivals) == 4 and arrivals[0] >= 1.2 and arrivals[-1] - arrivals[0] <= 0.3


def separate(arrivals: list[float]) -> bool:
    """이벤트마다 따로 왔다. 이웃한 도착의 간격이 모두 0.25초 이상이다(뒷단의 간격은 0.5초)."""
    gaps = [later - earlier for earlier, later in zip(arrivals, arrivals[1:], strict=False)]
    return len(arrivals) == 4 and min(gaps) >= 0.25


def sse_round(ctx: Ctx, report: Report, attempt: int) -> None:
    rid = secrets.token_hex(3)
    with report.rounds.round(f"6.SSE 이벤트 넷(0.5초 간격)#{attempt}") as slot:
        ops: list[dict[str, Json]] = []
        for accel, tag in (("0", "c"), ("1", "t")):
            op = http_op(
                f"/end-user/sse?n=4&gap=0.5&accel={accel}&rid={rid}-{tag}",
                rid=f"{rid}-{tag}",
                timeout=15.0,
            )
            op["kind"] = "sse"
            ops.append(op)
        results = ask(CLIENT, ops)
        items = [as_map(results[index] if index < len(results) else None) for index in (0, 1)]
        arrivals = [[as_number(v) for v in as_list(item.get("arrivals"))] for item in items]
        heads = [as_map(item.get("headers")) for item in items]
        through = all(
            as_text(head.get("x-stub")) == "serve" and "strict-transport-security" in head
            for head in heads
        )
        control = bunched(arrivals[0])
        complete = all(
            item.get("status") == 200 and len(got) == 4
            for item, got in zip(items, arrivals, strict=True)
        )
        apart = separate(arrivals[1])
        accel_seen = as_text(heads[1].get("x-accel-buffering"), "없음")
        report.close(
            slot,
            measured=through and complete and control,
            result=(
                "X-Accel-Buffering: no 가 있으면 이벤트마다 따로 온다"
                if apart
                else "그 머리가 있어도 따로 오지 않는다"
            ),
            detail=f"그 머리 있음 {arrivals[1]} ; 그 머리 없음(대조) {arrivals[0]}"
            f"{'(한꺼번에)' if control else '(한꺼번에가 아니다)'} ; "
            f"클라이언트가 받은 X-Accel-Buffering: {accel_seen}",
        )


# ---------------------------------------------------------------------------------------------
# 항목 7. 본문 상한

SIZES = (("a", 1_000_000), ("b", 1_048_576), ("c", 1_048_577))


def body_round(ctx: Ctx, report: Report, attempt: int) -> None:
    rid = secrets.token_hex(3)
    with report.rounds.round(f"7.본문 크기(client_max_body_size 1m)#{attempt}") as slot:
        ops = [
            http_op(
                f"/end-user/upload?rid={rid}-{tag}",
                method="POST",
                rid=f"{rid}-{tag}",
                body_bytes=size,
                timeout=30.0,
            )  # fmt: skip
            for tag, size in SIZES
        ]
        results = ask(CLIENT, ops)
        log = wait_log(PROXY, [f"rid={rid}-c"])
        serve_log = logs(ctx.stubs["serve"].container)
        shown: list[str] = []
        for index, (tag, size) in enumerate(SIZES):
            reply = single(results, index)
            got = int(as_number(reply.stub.get("body_bytes")))
            where = "뒷단" if in_stub(serve_log, f"{rid}-{tag}") else "뒷단 기록에 없음"
            shown.append(
                f"{size:,}바이트 → {reply.brief()} {where}" + (f"({got:,})" if got else "")
            )
        under = single(results, 0)
        over = single(results, 2)
        too_large = error_lines(log, "client intended to send too large body", f"rid={rid}-c HTTP/")
        control = under.status == 200 and int(as_number(under.stub.get("body_bytes"))) == 1_000_000
        nginx_answered = (over.status == 413 and not over.stub_name) or bool(too_large)
        leaked = in_stub(serve_log, f"{rid}-c")
        report.close(
            slot,
            measured=control and nginx_answered,
            result=" ; ".join(shown),
            detail=(too_large[0][-220:] if too_large else "오류 기록에 too large 줄 없음")
            + ("" if not leaked else " ; 넘는 본문이 뒷단에 닿았다"),
        )


# ---------------------------------------------------------------------------------------------
# 항목 8. 키 파일의 권한


def key_round(ctx: Ctx, report: Report, attempt: int, case: str) -> None:
    volume_name, alias = (
        (TLS600_VOLUME, "key600.test") if case == "600" else (TLS_VOLUME, "key640.test")
    )
    container = f"ri-pxy-key{case}-{attempt}"
    label = "root:root 0600" if case == "600" else "root:101 0640"
    with report.rounds.round(f"8.키 {label} 로 uid 101 nginx 띄우기#{attempt}") as slot:
        made = start_nginx(ctx.token, container, NET, alias, "proxy.conf", tls=volume_name)
        status, code, text = wait_nginx(container)
        denied = [
            line.strip()
            for line in text.splitlines()
            if "Permission denied" in line and "privkey.pem" in line
        ]
        reply = Reply(asked=False)
        if status == "running":
            reply = single(ask(CLIENT, [http_op("/portal/x", host=alias)]), 0)
        handshake = reply.cert == ctx.cert and ctx.cert != ""
        if status == "exited" and denied:
            measured, result = True, f"뜨지 못한다(종료 코드 {code}, 키를 읽지 못한다)"
        elif status == "running" and handshake:
            measured, result = True, f"뜬다, {reply.tls} 연결이 되고 지문이 만든 것과 같다"
        else:
            measured, result = False, f"갈래 밖(상태 {status}, 응답 {reply.brief()})"
        report.close(
            slot,
            measured=made.code == 0 and measured,
            result=result,
            detail=(denied[0][-260:] if denied else tail(text, 2)[-260:]),
        )
    docker("rm", "-f", container)


# ---------------------------------------------------------------------------------------------
# 항목 9. 다시 만든 뒷단


def fill_spares(ctx: Ctx, attempt: int, old_ip: str) -> list[str]:
    """자리 채움 컨테이너를 옛 주소를 받을 때까지(여덟까지) 하나씩 띄운다. Docker 가 빈 주소 가운데
    낮은 것부터 주면(이 PC 의 앞선 실행에서 그랬다) 옛 주소보다 낮은 빈 주소가 먼저 찬다."""
    spares: list[str] = []
    for index in range(8):
        name = f"ri-pxy-spare-{attempt}-{index}"
        run_detached(ctx.token, name, NET, PYTHON_IMAGE, "sleep", "infinity")
        spares.append(name)
        if addresses(name, NET)[0] == old_ip:
            break
    return spares


def recreate_round(ctx: Ctx, report: Report, attempt: int) -> None:
    """portal 대역을 지우고 같은 이름으로 다시 만든다. 옛 주소는 자리 채움 컨테이너가 잠시 쥐어
    새 컨테이너가 다른 주소를 받게 하고, 새 컨테이너가 뜬 뒤 자리 채움을 지운다(옛 주소가 빈다)."""
    rid = secrets.token_hex(3)
    old = ctx.stubs["portal"]
    with report.rounds.round(f"9.portal 을 다시 만든 뒤#{attempt}") as slot:
        base = single(ask(CLIENT, [http_op(f"/portal/x?rid={rid}-b", rid=f"{rid}-b")]), 0)
        unresolved_before = sum(error_kinds(logs(PROXY), "could not be resolved").values())
        started = time.monotonic()
        docker("rm", "-f", old.container)
        spares = fill_spares(ctx, attempt, old.ipv4)
        new = start_stub(ctx.token, NET, old.container, "portal")
        ready_at = time.monotonic()
        docker("rm", "-f", *spares)
        ctx.stubs["portal"] = new
        poll = http_op(f"/portal/x?rid={rid}-{{i}}", rid=f"{rid}-{{i}}", timeout=3.0)
        poll.update({"kind": "poll", "window": 45.0, "gap": 0.5, "until_instance": new.instance})
        before_poll = time.monotonic()
        direct = http_op("/self", host=new.ipv4, port=3000, scheme="http", rid=f"{rid}-self")
        results = ask(CLIENT, [poll, direct], timeout=150)
        polled = time.monotonic() - before_poll
        samples = replies_of(results, 0)
        own = single(results, 1)
        hit_index = next(
            (index for index, sample in enumerate(samples) if sample.instance == new.instance), -1
        )
        log = wait_log(PROXY, [f"rid={rid}-{max(hit_index, 0)} uri="])
        found = accesses(log)
        unresolved = sum(error_kinds(log, "could not be resolved").values()) - unresolved_before
        request_errors = error_kinds(log, f"rid={rid}-")
        new_log = wait_log(new.container, [f" rid={rid}-{max(hit_index, 0)} "])
        trail = [
            f"{s.start:.1f}초 {s.brief()} {s.stub_name}"
            f" up={found[f'{rid}-{i}'].upstream if f'{rid}-{i}' in found else '?'}"
            for i, s in enumerate(samples)
        ]
        hit = samples[hit_index] if hit_index >= 0 else None
        moved = old.ipv4 != new.ipv4 and new.ipv4 != ""
        answered_itself = own.instance == new.instance
        logged = hit_index >= 0 and in_stub(new_log, f"{rid}-{hit_index}")
        report.close(
            slot,
            measured=moved
            and answered_itself
            and base.instance == old.instance
            and (hit is None or logged),
            result=(
                f"새 컨테이너에 닿았다: poll 시작 뒤 {hit.start:.1f}초({hit_index + 1}번째 표본)"
                if hit
                else "45초 안에 새 컨테이너에 닿지 않았다"
            ),
            detail=f"주소 {old.ipv4}→{new.ipv4}, 자리 채움 {len(spares)}개 ; 옛 컨테이너를 지운 "
            f"뒤 새 컨테이너가 뜨기까지 {ready_at - started:.1f}초, 그 뒤 poll 을 보내기까지 "
            f"{before_poll - ready_at:.1f}초(exec 를 띄우는 몫은 빼고), exec 포함 poll "
            f"{polled:.1f}초 ; 그사이 이름을 풀지 못한 오류 줄 {unresolved} ; 이 회차 요청의 "
            f"오류 기록 {request_errors} ; 표본 하나의 제한 3초 ; 표본 {trail}",
        )


# ---------------------------------------------------------------------------------------------
# 항목 10. IPv6 를 켠 내부 네트워크


def make_net6(ctx: Ctx, report: Report) -> bool:
    """대역을 주지 않고 IPv6 를 켜서 만들어 본다. IPv6 대역이 없으면 ULA 대역을 주고 다시 만든다."""
    with report.rounds.round("10.IPv6 를 켠 네트워크 만들기") as slot:
        label = ("--label", f"{LABEL}={ctx.token}")
        made = docker("network", "create", *label, "--ipv6", NET6)
        subnets = net6_subnets()
        auto = made.code == 0 and any(":" in item for item in subnets)
        how = f"대역을 주지 않아도 Docker 가 잡았다 {subnets}"
        if not auto:
            docker("network", "rm", NET6)
            made = docker("network", "create", *label, "--ipv6", "--subnet", ULA6, NET6)
            subnets = net6_subnets()
            how = f"대역 없이는 IPv6 대역이 없어({tail(made.err, 1)}) ULA 를 줬다 {subnets}"
        report.facts["net6"] = list[Json](subnets)
        report.close(
            slot,
            measured=made.code == 0 and any(":" in item for item in subnets),
            result="자동" if auto else "ULA 를 줬다",
            detail=how,
        )
    return any(":" in item for item in subnets)


def net6_subnets() -> list[str]:
    info = as_list(parse(docker("network", "inspect", NET6).out))
    configs = as_list(as_map(as_map(info[0] if info else None).get("IPAM")).get("Config"))
    return [as_text(as_map(item).get("Subnet")) for item in configs]


@dataclass
class Batch:
    """IPv6 네트워크에서 프록시 하나로 보낸 회차 하나의 모음."""

    proxy: str
    rid: str
    replies: dict[str, list[Reply]] = field(default_factory=dict[str, list[Reply]])
    found: dict[str, Access] = field(default_factory=dict[str, Access])
    failures: list[str] = field(default_factory=list[str])
    error: str = ""

    def total(self) -> int:
        return sum(len(items) for items in self.replies.values())


V6_PATHS = {"s": "/end-user/x", "w": "/widget/x", "p": "/portal/x"}
V6_COUNT = 20


def v6_batch(proxy: str, alias: str) -> Batch:
    """회차 하나를 모은다. 모으다 난 예외는 그 회차의 error 로 남겨, 판정할 때 측정 아님이 된다."""
    batch = Batch(proxy, secrets.token_hex(3))
    try:
        v6_collect(batch, alias)
    except (OSError, ValueError, RuntimeError) as error:
        batch.error = repr(error)
    return batch


def v6_collect(batch: Batch, alias: str) -> None:
    ops = [
        http_op(
            f"{path}?rid={batch.rid}-{tag}{{i}}",
            host=alias,
            rid=f"{batch.rid}-{tag}{{i}}",
            count=V6_COUNT,
        )
        for tag, path in V6_PATHS.items()
    ]
    results = ask("ri-pxy-v6-client", ops)
    log = wait_log(batch.proxy, [f"rid={batch.rid}-p{V6_COUNT - 1} uri="])
    batch.replies = {tag: replies_of(results, index) for index, tag in enumerate(V6_PATHS)}
    batch.found = accesses(log)
    batch.failures = error_lines(
        log, "connect() failed", f"rid={batch.rid}-", 'upstream: "http://['
    )


def v6_view(batch: Batch) -> tuple[bool, int, int, str]:
    """(요청마다 접근 기록이 있다, 200 의 수, $upstream_addr 에 IPv6 가 든 줄의 수, 보일 글)."""
    keys = [f"{batch.rid}-{tag}{i}" for tag in V6_PATHS for i in range(V6_COUNT)]
    reached = batch.total() == len(keys) and all(key in batch.found for key in keys)
    ok = sum(reply.status == 200 for items in batch.replies.values() for reply in items)
    v6_up = [key for key in keys if key in batch.found and "[" in batch.found[key].upstream]
    per = {tag: sum(1 for key in v6_up if key.startswith(f"{batch.rid}-{tag}")) for tag in V6_PATHS}
    first = batch.failures[0] if batch.failures else ""
    sample = first[first.find("connect() failed") :][:230] if first else "없음"
    shown = f"IPv6 가 든 up 칸(s=serve·w=widget·p=portal) {per} ; 실패 줄 예: {sample}"
    return reached, ok, len(v6_up), shown


def section_ipv6(ctx: Ctx, report: Report) -> None:
    if not make_net6(ctx, report):
        return
    v6_stubs = {
        service: start_stub(ctx.token, NET6, f"ri-pxy-v6-{service}", service) for service in STUBS
    }
    start_client(ctx.token, "ri-pxy-v6-client", NET6)
    with report.rounds.round("10.뒷단 이름이 AAAA 로도 풀린다") as slot:
        ops: list[dict[str, Json]] = [{"kind": "resolve", "host": service} for service in STUBS]
        results = ask("ri-pxy-v6-client", ops)
        families = {
            service: sorted(
                {
                    as_text(as_list(pair)[0])
                    for pair in as_list(as_map(item).get("addresses"))
                    if as_list(pair)
                }
            )
            for service, item in zip(STUBS, results, strict=False)
        }
        both = len(families) == len(STUBS) and all(
            "AF_INET6" in found and "AF_INET" in found for found in families.values()
        )
        addresses_seen = {name: (stub.ipv4, stub.ipv6) for name, stub in v6_stubs.items()}
        report.close(
            slot,
            measured=len(families) == len(STUBS),
            result="A 와 AAAA 둘 다" if both else f"갈래 {families}",
            detail=f"뒷단의 주소 {addresses_seen}",
        )
    start_nginx(ctx.token, "ri-pxy-v6-direct", NET6, "direct6.test", "direct.conf")
    start_nginx(ctx.token, "ri-pxy-v6-resolve", NET6, "resolve6.test", "proxy.conf")
    wait_nginx("ri-pxy-v6-direct")
    wait_nginx("ri-pxy-v6-resolve")
    time.sleep(6)  # resolve 쪽이 첫 이름 풀기를 마칠 몫(valid=5s)
    direct: list[Batch] = []
    resolved: list[Batch] = []
    for attempt in range(3):
        if attempt:
            time.sleep(11)  # 실패한 IPv6 주소를 쉬게 두는 fail_timeout(기본 10초)이 지나게 한다
        direct.append(v6_batch("ri-pxy-v6-direct", "direct6.test"))
        resolved.append(v6_batch("ri-pxy-v6-resolve", "resolve6.test"))
    control_v6 = 0
    for attempt, batch in enumerate(direct, start=1):
        with report.rounds.round(f"10.이름을 바로 쓴 설정(양성 대조)#{attempt}") as slot:
            reached, ok, v6_up, shown = v6_view(batch)
            control_v6 += v6_up + len(batch.failures)
            report.close(
                slot,
                measured=reached and not batch.error,
                result=f"200 {ok}/{batch.total()}, up 칸에 IPv6 {v6_up}줄, "
                f"IPv6 로 건 연결 실패 {len(batch.failures)}줄",
                detail=batch.error or shown,
            )
    for attempt, batch in enumerate(resolved, start=1):
        with report.rounds.round(f"10.resolve 와 ipv6=off 설정#{attempt}") as slot:
            reached, ok, v6_up, shown = v6_view(batch)
            report.close(
                slot,
                measured=reached and not batch.error and control_v6 > 0,
                result=f"200 {ok}/{batch.total()}, up 칸에 IPv6 {v6_up}줄, "
                f"IPv6 로 건 연결 실패 {len(batch.failures)}줄",
                detail=(batch.error or shown)
                + ("" if control_v6 > 0 else " ; 양성 대조가 IPv6 로 한 번도 걸지 않았다"),
            )
    # 회차 밖(뜬 직후, 회차 사이)까지 센 기록 전체의 IPv6 연결 실패 줄과 그 밖의 warn 이상 줄.
    whole: dict[str, Json] = {}
    for proxy in ("ri-pxy-v6-direct", "ri-pxy-v6-resolve"):
        text = logs(proxy)
        failed = error_lines(text, "connect() failed", 'upstream: "http://[')
        kinds = dict[str, Json](error_kinds(text))
        whole[proxy] = {"ipv6_connect_failed": len(failed), "warn_or_worse": kinds}
    report.facts["v6_whole_log"] = whole
    print(f"IPv6 기록 전체: {json.dumps(whole, ensure_ascii=False)}", flush=True)


# ---------------------------------------------------------------------------------------------
# 차례


def section_rounds(ctx: Ctx, report: Report, sections: set[int]) -> None:
    repeat = (1, 2)
    if 1 in sections:
        for attempt in repeat:
            variant_round(ctx, report, attempt)
    if 2 in sections:
        for attempt in repeat:
            overflow_round(ctx, report, attempt)
        for attempt in repeat:
            empty_key_round(ctx, report, attempt)
    if 3 in sections:
        for attempt in repeat:
            allowlist_round(ctx, report, attempt)
    if 4 in sections:
        for attempt in repeat:
            http80_round(ctx, report, attempt)
    if 5 in sections:
        for attempt in repeat:
            forwarded_round(ctx, report, attempt)
    if 6 in sections:
        for attempt in repeat:
            sse_round(ctx, report, attempt)
    if 7 in sections:
        for attempt in repeat:
            body_round(ctx, report, attempt)
    if 8 in sections:
        for attempt in repeat:
            key_round(ctx, report, attempt, "600")
            key_round(ctx, report, attempt, "640")
    if 9 in sections:
        for attempt in repeat:
            recreate_round(ctx, report, attempt)


def keep_logs(ctx: Ctx) -> None:
    for container in docker(
        "ps", "-a", "--format", "{{.Names}}", "--filter", f"label={LABEL}={ctx.token}"
    ).out.split():
        raw(f"{container} 의 기록", logs(container))


def everything(ctx: Ctx, report: Report, sections: set[int]) -> None:
    record_versions(ctx, report)
    if not make_tls(ctx, report):
        return
    if 0 in sections:
        section_test(ctx, report)
    if sections & {1, 2, 3, 4, 5, 6, 7, 8, 9} and start_stack(ctx, report):
        section_rounds(ctx, report, sections)
    if 10 in sections:
        section_ipv6(ctx, report)


def verify_cleanup(report: Report) -> None:
    with report.rounds.round("정리.라벨이 붙은 자원이 남지 않았다") as slot:
        cleanup()
        left = {kind: labelled(kind) for kind in ("container", "network", "volume")}
        empty = not any(left.values())
        report.close(
            slot,
            measured=True,
            result="남은 것 없음" if empty else f"남았다 {left}",
        )


def main() -> int:
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="명세가 고른 nginx 프록시 설정 조합을 잰다")
    parser.add_argument("--sections", default="0,1,2,3,4,5,6,7,8,9,10")
    parser.add_argument("--work", default="")
    parser.add_argument("--keep", action="store_true", help="끝난 뒤 컨테이너와 네트워크를 남긴다")
    args = parser.parse_args()
    sections = {int(item) for item in str(args.sections).split(",") if item}
    work = Path(str(args.work)) if args.work else Path(tempfile.mkdtemp(prefix="ri-pxy-"))
    work.mkdir(parents=True, exist_ok=True)
    _raw.append(work / "raw.log")
    report = Report()
    ctx = Ctx(secrets.token_hex(4))
    print(f"원본 출력 {work / 'raw.log'}", flush=True)
    cleanup()
    try:
        everything(ctx, report, sections)
    except (RuntimeError, OSError, ValueError) as error:
        # 띄우기가 실패하면 뒤 항목을 돌지 않는다. 앞서 모은 회차는 잃지 않고 이 실행을 측정
        # 아님으로 센다.
        report.rounds.record("중단", measured=False, result=f"예외: {error!r}")
        print(f"[중단] {error!r}", flush=True)
    finally:
        keep_logs(ctx)
        if not args.keep:
            verify_cleanup(report)
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
