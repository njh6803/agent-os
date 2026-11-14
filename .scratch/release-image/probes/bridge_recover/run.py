"""release-image 단독 배포의 배치를 리눅스의 Docker Engine 에서 잰다. 프록시(nginx) 하나와 뒷단
넷을 compose 의 보통 Docker 네트워크로 묶고 프록시가 서비스 이름으로 접속하는 배치다(ADR 0056
결정 "컨테이너 배치"). 결정은 하지 않고 회차마다 본 것을 한 줄씩 낸다.

저장소 루트에서

    uv run python .scratch/release-image/probes/bridge_recover/run.py [--sections 0,1,...,8]
        [--nginx-image <digest 참조>] [--python-image <digest 참조>] [--dind-image <digest 참조>]
        [--work <원본 출력을 둘 폴더>] [--reuse] [--keep] [--long]

리눅스의 Docker Engine 을 얻는 길. 이 PC(Windows 의 Docker Desktop)에서 공식 dind 이미지를
--privileged 로 띄운다. 그 컨테이너(이름 ri-recover-dind) 안에 리눅스 커널 위의 독립된 dockerd 가
돌고, 그 컨테이너가 "리눅스 서버" 노릇을 한다. compose 와 모든 요청은 그 안에서 돈다(docker
exec). 뒷단 넷은 실제 이미지가 아니라 backend/server.py 다. 프로브가 안쪽 엔진에서 nginx 와
python 이미지를 digest 로 받고(인터넷이 필요하다) 뒷단 이미지를 v1·v2 두 태그로 짓는다. 끝나면
dind 컨테이너와 그 볼륨(ri-recover-dind-data)을 지운다. 이 프로브가 만든 표지(라벨
ri-recover-probe=1)가 없는 컨테이너와 볼륨은 이름이 같아도 건드리지 않고 멈춘다. 바깥 데몬의 다른
컨테이너·이미지·네트워크는 건드리지 않고 호스트 포트도 열지 않는다.

- "서버를 껐다 켠다"는 바깥에서 dind 컨테이너를 `docker restart`(정상 종료) 하거나 `docker kill`
  뒤 `docker start`(전원이 나간 꼴) 하는 것으로 흉내 낸다. dind 의 /run 은 tmpfs 라 그때 비고
  /var/lib/docker 는 볼륨이라 남는다.
- "Docker 데몬만 다시 켠다"(`systemctl restart docker`)는 안의 dockerd 에 TERM 을 보내는 것으로
  흉내 낸다. supervise.sh 가 주 프로세스로 남아 dockerd 를 다시 띄운다.

누가 답했는지. 뒷단은 응답 본문에 자기 이름과 컨테이너 호스트 이름을 싣고 접근 기록에 요청의
rid 를 남긴다. "닿는다"는 프록시를 거친 요청이 상태 200 이고, 본문의 이름이 그 경로의 서비스이며,
본문의 호스트 이름이 지금 그 서비스 컨테이너의 것이고, 그 컨테이너의 접근 기록에 그 rid 가 있는
것이다(프록시의 상태 코드만 보지 않는다).

항목(README 의 결과 번호와 같다)

0. 환경과 판. 세 설정을 이름이 풀리지 않는 자리에서 `nginx -t` 로 본다. 표지는 (가)가 `host not
   found in upstream` 으로 실패하는 것이다(그 자리에서 이름이 정말 풀리지 않는다는 대조). 그
   대조가 선 실행에서 (다)가 통과하면 오픈 소스 nginx 의 이 판이 `server … resolve` 를 받고 시작할
   때 이름을 풀지 않는다는 뜻이다.
1. 뒷단을 다시 띄운 뒤 프록시가 새 주소를 찾는지. 설정 셋((가) 정적, (나) resolver 와 변수, (다)
   upstream 의 resolve)마다 조작 다섯을 갈래마다 새로 띄운 배치에서 한다. 표지는 넷이다. 조작이 그
   컨테이너에 실제로 닿았다(새 컨테이너 id, 또는 같은 id 의 새 시작 시각). 그 컨테이너의 주소가
   실제로 바뀌었다(바뀌지 않은 회차는 측정이 아니다. 바뀌게 하려고 낮은 주소를 미리 차지한 자리
   채움 넷을 조작 직전에 지운다). 새 컨테이너가 자기 주소에서 스스로 답했다(프록시의 탓과 뒷단의
   탓을 가른다). 닿았다고 센 요청이 그 컨테이너의 접근 기록에 있다. 닿지 않으면 회복 조작을
   약한 것부터(`nginx -s reload`, `docker compose restart proxy`) 치고, 회복 조작이 프록시에 실제로
   닿았다는 표지(reload 는 nginx 기록의 `reconfiguring` 줄이 는 것, restart 는 새 시작 시각)를 본다.
2. (가)에 `depends_on` 의 `restart: true` 를 더한 판에서 같은 조작과, compose 를 거치지 않는 조작
   둘(`docker restart`, 뒷단 프로세스가 죽어 재시작 정책이 다시 띄움)을 한다. compose 가 프록시를
   함께 다시 시작해 주는 범위를 본다.
3. 해석을 가르는 갈래. 3a 는 다시 만든 serve 의 옛 주소를 같은 포트의 다른 컨테이너(squatter)가
   차지하게 한 뒤 프록시의 /serve/ 를 누가 답하는지 본다. (가)가 닿지 않는 까닭이 "nginx 가 옛
   주소를 기억한다"라면 squatter 가 답한다. 표지는 squatter 가 정말 옛 주소를 받았고 스스로 답한
   것이다. 3b 는 자리 채움 없이 판 올림(태그를 바꾼 `up -d`)을 주소가 바뀔 때까지 되풀이해, 손대지
   않은 배치에서 주소가 얼마나 자주 바뀌는지와 그때 누가 답하는지 본다. 3c 는 (나)에서 valid 를
   뺀 설정과 내장 DNS 의 TTL 이다.
4. 껐다 켠 뒤 스스로 돌아오는지. 설정 셋마다 세 사건(데몬만 다시 켬, dind 정상 재시작, dind 를
   죽였다 켬) 뒤에 사람 손 없이 다섯 컨테이너가 다시 떠 네 경로가 답하는지 본다. 표지는 사건이
   실제로 났다는 것(supervise.sh 의 dockerd 시작 횟수가 늘었거나 dind 컨테이너의 시작 시각이
   바뀌었다)이고, 결과에 컨테이너마다 다시 시작됐는지를 함께 낸다.
5. 재시작 정책. `always`, `unless-stopped`, 정책 없음(대조)과, 운영자가 뒷단 하나를
   `docker compose stop` 으로 멈춰 둔 채 사건이 난 경우를 본다.
6. 프록시가 뜰 때 뒷단 하나의 이름이 풀리지 않는 경우. 위젯을 멈춘 채 프록시를 다시 시작하고,
   그동안 다른 경로가 답하는지와 위젯을 다시 띄운 뒤 스스로 돌아오는지 본다. 표지는 위젯이 멈춰
   있었고 프록시가 실제로 다시 시작된 것이다.
7. 늦게 뜨는 위젯(포트를 20초 뒤에 연다). `depends_on` 과 healthcheck 를 둔 판과 두지 않은 판에서
   처음 띄울 때, 그리고 둔 판에서 데몬을 다시 켠 뒤를 본다. 표지는 위젯의 기록에 지연이 찍혔고
   위젯 경로가 닿기 전에 닿지 않는 응답을 실제로 본 것이다.
8. 호스트에서 고친 nginx 설정 파일과 `nginx -s reload`. 설정을 폴더로 얹은 판과 파일 하나로 얹은
   판에서, 파일을 제자리에서 고친 것과 새 파일을 만들어 바꿔 끼운 것(이름 바꾸기, `sed -i`)을
   가른다. 표지는 호스트 파일의 inode 가 바뀌었는지(기대한 쪽인지)와 reload 가 nginx 에 닿은
   것이다. 깨진 설정으로 reload 를 친 갈래도 둔다.

정리 실패. 회차마다 시작 전에 앞 회차의 것을 지우고, 안쪽 엔진에 이 프로젝트의 컨테이너나
네트워크가 남았는지 본다. 남았으면 그 뒤의 회차는 모두 측정 아님으로 센다.

못 보는 것. 실제 서버의 재부팅(systemd 가 docker.service 와 containerd 를 띄우는 차례, 커널이
다시 뜨는 것, 디스크 검사), 네트워크 장비를 거쳐 다른 기기에서 오는 요청, 실제 이미지 넷의 시작
시간과 종료 처리, IPv6 네트워크, rootless Docker 와 podman. 결과와 한계는 같은 폴더의 README.md
에 있다.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import secrets
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Generator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds, Slot  # noqa: E402

# 2026-11-13 에 받은 공식 이미지다. docker:29.9.2-dind, nginx:alpine(nginx 1.31.6),
# python:3.12.10-slim-bookworm.
DIND_IMAGE = "docker@sha256:9e79b879b177fbd72c34376a3dd3d91747da5db49e1f560f76aea59561471977"
NGINX_IMAGE = "nginx@sha256:c8497b180665e631ec92a5091125bec5b214f0e2b99409e30653a125b37557da"
PYTHON_IMAGE = "python@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db"

DIND = "ri-recover-dind"
VOLUME = "ri-recover-dind-data"
MARK = "ri-recover-probe"
PROJECT = "ri-recover"
NETWORK = f"{PROJECT}_default"
REMOTE = "/probe"
SQUAT = "ri-recover-squat"
BACKENDS: Mapping[str, int] = {"serve": 8000, "admin": 3000, "widget": 3000, "portal": 3000}
ROUTES = tuple(BACKENDS)
PROXY_URL = "http://127.0.0.1:8080"
BODY = re.compile(r"name=(\S+) host=(\S+) version=(\S+) path=(\S*)")
SHELL_FILES = ("supervise.sh", "client.sh")

_raw: list[Path] = []


def raw(title: str, text: str) -> None:
    if _raw:
        with _raw[0].open("a", encoding="utf-8") as out:
            out.write(f"\n===== {time.strftime('%H:%M:%S')} {title}\n{text}\n")


def tail(text: str, count: int = 3) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " / ".join(lines[-count:])


# docker 가 내는 JSON 을 읽는 자리. 모양이 기대와 다르면 예외 대신 빈 값이 나오고, 그 빈 값으로는
# 아래의 표지(컨테이너 id, 시작 시각, 주소)가 서지 않아 측정 아님으로 세어진다.
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


def as_int(value: Json, default: int = 0) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else default


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

    @property
    def text(self) -> str:
        return self.out + "\n" + self.err


def decode(data: bytes) -> str:
    return data.decode("utf-8", errors="replace").replace("\r\n", "\n")


def run(argv: Sequence[str], *, stdin: str | None = None, timeout: float = 240) -> Done:
    """명령 하나. 표준 입력은 바이트로 넘긴다(글 모드는 윈도에서 줄 끝을 바꾼다). 시간을 넘기면
    종료 코드 -1 이다."""
    try:
        completed = subprocess.run(
            list(argv),
            input=(stdin or "").encode("utf-8"),
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        done = Done(-1, "", f"{timeout:.0f}초 안에 끝나지 않았다")
    else:
        done = Done(completed.returncode, decode(completed.stdout), decode(completed.stderr))
    raw(" ".join(argv), f"exit={done.code}\n--- stdout\n{done.out}\n--- stderr\n{done.err}")
    return done


def outer(*args: str, timeout: float = 120) -> Done:
    """바깥(이 PC 의 Docker Desktop) 데몬에 치는 docker 명령."""
    return run(["docker", *args], timeout=timeout)


def exec_argv(env: Mapping[str, str] | None, *, piped: bool) -> list[str]:
    argv = ["docker", "exec"]
    if piped:
        argv.append("-i")
    for key, value in (env or {}).items():
        argv += ["-e", f"{key}={value}"]
    return [*argv, DIND]


def inner(
    *args: str,
    env: Mapping[str, str] | None = None,
    stdin: str | None = None,
    timeout: float = 120,
) -> Done:
    """dind 컨테이너("리눅스 서버") 안에서 치는 명령."""
    argv = exec_argv(env, piped=stdin is not None)
    return run([*argv, *args], stdin=stdin, timeout=timeout)


def shell(script: str, *, timeout: float = 60) -> Done:
    return inner("sh", "-c", script, timeout=timeout)


@dataclass(frozen=True)
class Stack:
    """compose 파일 묶음 하나. 프로젝트 이름은 늘 PROJECT 이고 compose.yml 위에 덧씌움을 얹는다."""

    variant: str
    files: tuple[str, ...] = ()
    env: Mapping[str, str] = field(default_factory=dict[str, str])

    def argv(self, profiles: Sequence[str], args: Sequence[str]) -> list[str]:
        argv = ["docker", "compose", "--ansi", "never", "--progress", "plain", "-p", PROJECT]
        argv += ["--project-directory", REMOTE]
        for name in ("compose.yml", *self.files):
            argv += ["-f", f"{REMOTE}/{name}"]
        for profile in profiles:
            argv += ["--profile", profile]
        return [*argv, *args]

    def full_env(self) -> dict[str, str]:
        return {"NGINX_VARIANT": self.variant, **self.env}

    def compose(
        self,
        *args: str,
        profiles: Sequence[str] = (),
        stdin: str | None = None,
        timeout: float = 240,
    ) -> Done:
        argv = self.argv(profiles, args)
        return inner(*argv, env=self.full_env(), stdin=stdin, timeout=timeout)

    def spawn(self, *args: str) -> subprocess.Popen[bytes]:
        """compose 명령을 기다리지 않고 띄운다. 도는 동안 요청을 보내 보려는 것이다."""
        argv = [*exec_argv(self.full_env(), piped=False), *self.argv((), args)]
        return subprocess.Popen(
            argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )

    def with_env(self, extra: Mapping[str, str]) -> Stack:
        return Stack(self.variant, self.files, {**self.env, **extra})

    def with_files(self, *names: str) -> Stack:
        return Stack(self.variant, (*self.files, *names), self.env)


@dataclass(frozen=True)
class Box:
    """안쪽 엔진의 컨테이너 하나의 지금 모습(docker inspect)."""

    id: str
    name: str
    started: str
    running: bool
    status: str
    exit_code: int
    restarts: int
    ip: str
    hostname: str
    image: str


LIST_BOXES = (
    'ids="$(docker ps -aq --no-trunc --filter label={label})"; '
    '[ -n "$ids" ] || exit 0; docker inspect $ids'
)


def inspect_by_label(label: str) -> dict[str, Box] | None:
    """그 라벨의 컨테이너 전부(멈춘 것 포함). 안쪽 데몬이 답하지 않으면 None 이다."""
    done = shell(LIST_BOXES.format(label=label))
    if done.code != 0:
        return None
    found: dict[str, Box] = {}
    for info in as_list(parse(done.out)):
        networks = as_map(dig(info, "NetworkSettings", "Networks"))
        addresses = [as_text(dig(net, "IPAddress")) for net in networks.values()]
        name = as_text(dig(info, "Name")).lstrip("/")
        found[name.removeprefix(f"{PROJECT}-")] = Box(
            id=as_text(dig(info, "Id")),
            name=name,
            started=as_text(dig(info, "State", "StartedAt")),
            running=dig(info, "State", "Running") is True,
            status=as_text(dig(info, "State", "Status")),
            exit_code=as_int(dig(info, "State", "ExitCode")),
            restarts=as_int(dig(info, "RestartCount")),
            ip=next((address for address in addresses if address), ""),
            hostname=as_text(dig(info, "Config", "Hostname")),
            image=as_text(dig(info, "Config", "Image")),
        )
    return found


def boxes() -> dict[str, Box]:
    """이 compose 프로젝트의 컨테이너. 열쇠는 '<서비스>-<번호>'(serve-1, spare-3)다."""
    return inspect_by_label(f"com.docker.compose.project={PROJECT}") or {}


def of(now: Mapping[str, Box], service: str) -> Box | None:
    return now.get(f"{service}-1")


def ip_of(now: Mapping[str, Box], service: str) -> str:
    box = of(now, service)
    return box.ip if box is not None else ""


def is_running(now: Mapping[str, Box], service: str) -> bool:
    box = of(now, service)
    return box is not None and box.running


def restarts_of(now: Mapping[str, Box], service: str) -> int:
    box = of(now, service)
    return box.restarts if box is not None else 0


def last(address: str) -> str:
    """주소의 끝 마디(.6). 표에 짧게 적으려는 것이다."""
    return "." + address.rsplit(".", 1)[-1] if address else "(없음)"


@dataclass(frozen=True)
class Reply:
    """요청 하나의 결과. status 가 0 이면 HTTP 응답을 받지 못한 것이고 note 가 까닭이다.
    asked 가 거짓이면 요청을 보내 보지도 못한 것이다(dind 안의 실행이 돌지 않았다)."""

    url: str = ""
    status: int = 0
    body: str = ""
    note: str = ""
    asked: bool = True

    @property
    def name(self) -> str:
        match = BODY.search(self.body)
        return match.group(1) if match else ""

    @property
    def host(self) -> str:
        match = BODY.search(self.body)
        return match.group(2) if match else ""

    @property
    def version(self) -> str:
        match = BODY.search(self.body)
        return match.group(3) if match else ""

    def kind(self) -> str:
        if self.status:
            return str(self.status)
        if not self.asked:
            return "서버에 닿지 않음"
        if "timed out" in self.note:
            return "시간 초과"
        if "refused" in self.note:
            return "연결 거부"
        return self.note.removeprefix("wget: ")[:50] or "응답 없음"


def ask(urls: Sequence[str], *, limit: int = 8) -> list[Reply]:
    """dind 컨테이너 안에서 GET 여럿을 함께 보낸다(client.sh)."""
    done = inner("sh", f"{REMOTE}/client.sh", str(limit), *urls, timeout=limit + 40)
    found: dict[str, Reply] = {}
    for line in done.out.splitlines():
        parts = line.split("\t")
        if len(parts) == 5 and parts[0] == "REPLY":
            status = int(parts[2]) if parts[2].isdigit() else 0
            found[parts[1]] = Reply(parts[1], status, parts[3], parts[4].strip())
    missing = Reply(
        note=f"요청을 보내지 못했다(종료 {done.code}): {tail(done.err, 1)}", asked=False
    )
    return [found.get(url, replace(missing, url=url)) for url in urls]


def good(reply: Reply, route: str, box: Box | None) -> bool:
    """그 경로의 요청을 그 컨테이너가 답했는가(상태, 본문의 이름, 본문의 호스트 이름)."""
    if box is None or not box.hostname:
        return False
    return reply.status == 200 and reply.name == route and reply.host == box.hostname


def logged(box: Box | None, needle: str) -> bool:
    """그 컨테이너의 기록(표준 출력과 표준 오류)에 그 글이 있는가."""
    if box is None:
        return False
    done = inner("docker", "logs", "--tail", "2000", box.id, timeout=60)
    return done.code == 0 and needle in done.text


def count_logged(box: Box | None, needle: str) -> int:
    if box is None:
        return -1
    done = inner("docker", "logs", box.id, timeout=60)
    if done.code != 0:
        return -1
    return sum(1 for line in done.text.splitlines() if needle in line)


def log_lines(box: Box | None, needle: str, count: int = 2) -> str:
    if box is None:
        return ""
    done = inner("docker", "logs", "--tail", "400", box.id, timeout=60)
    lines = [line.strip() for line in done.text.splitlines() if needle in line]
    return " / ".join(line[-230:] for line in lines[-count:])


@dataclass(frozen=True)
class Sample:
    """한 번에 함께 보낸 요청들. at 은 기준 시각 뒤 보낸 때(초), took 은 모두 돌아올 때까지다."""

    at: float
    took: float
    rid: str
    via: Mapping[str, Reply]
    direct: Mapping[str, Reply]
    alive: Reply


@dataclass
class Context:
    token: str
    rounds: Rounds
    nginx_image: str
    python_image: str
    dind_image: str
    long: bool = False
    tainted: str = ""
    count: int = 0

    def rid(self) -> str:
        self.count += 1
        return f"{self.token}-{self.count}"

    def stack(self, variant: str, *files: str) -> Stack:
        return Stack(variant, files, {"NGINX_IMAGE": self.nginx_image})

    def clean(self) -> bool:
        """안쪽 엔진에서 이 프로젝트의 것을 모두 지우고, 남은 것이 없는지 본다. 남았으면 그 뒤의
        회차를 믿지 않는다(tainted)."""
        if self.tainted:
            return False
        # squatter 는 compose 밖에서 같은 네트워크에 붙인 것이라 먼저 지운다. 붙어 있는 채 down 하면
        # 네트워크가 "Resource is still in use" 로 남는다(첫 판이 그렇게 정리 실패를 냈다).
        shell(
            f'ids="$(docker ps -aq --filter label={SQUAT}=1)"; [ -z "$ids" ] || docker rm -f $ids'
        )
        down = ["docker", "compose", "--ansi", "never", "-p", PROJECT, "down", "-v"]
        inner(*down, "--remove-orphans", "--timeout", "2", timeout=180)
        left = shell(
            f"docker ps -aq --filter label=com.docker.compose.project={PROJECT}; "
            f"docker ps -aq --filter label={SQUAT}=1; "
            f"docker network ls -q --filter label=com.docker.compose.project={PROJECT}"
        )
        if left.code != 0 or left.out.strip():
            self.tainted = f"정리 뒤에 남은 것(종료 {left.code}): {tail(left.text, 4)}"
            print(f"! 정리 실패. 이 뒤의 회차는 측정으로 세지 않는다: {self.tainted}", flush=True)
            return False
        return True


def sample(ctx: Context, since: float, directs: Mapping[str, Box]) -> Sample:
    """네 경로를 프록시로, directs 의 컨테이너를 그 주소로 바로, 함께 묻는다."""
    rid = ctx.rid()
    via = {route: f"{PROXY_URL}/{route}/?rid={rid}" for route in ROUTES}
    alive = f"{PROXY_URL}/proxy-alive"
    direct = {
        service: f"http://{box.ip}:{BACKENDS[service]}/direct?rid={rid}"
        for service, box in directs.items()
        if box.ip
    }
    at = time.monotonic() - since
    replies = ask([*via.values(), alive, *direct.values()])
    took = time.monotonic() - since - at
    by_url = {reply.url: reply for reply in replies}
    return Sample(
        at=at,
        took=took,
        rid=rid,
        via={route: by_url[url] for route, url in via.items()},
        direct={service: by_url[url] for service, url in direct.items()},
        alive=by_url[alive],
    )


def watch(
    ctx: Context,
    since: float,
    directs: Mapping[str, Box],
    done_when: Callable[[Sample], bool],
    *,
    seconds: float,
    hits: int = 1,
    pause: float = 0.5,
) -> list[Sample]:
    """done_when 이 hits 번 잇달아 참이 되거나 seconds 가 지날 때까지 되풀이해 묻는다."""
    deadline = time.monotonic() + seconds
    samples: list[Sample] = []
    streak = 0
    while True:
        current = sample(ctx, since, directs)
        samples.append(current)
        streak = streak + 1 if done_when(current) else 0
        if streak >= hits or time.monotonic() >= deadline:
            return samples
        time.sleep(pause)


def trace(samples: Sequence[Sample], pick: Callable[[Sample], str]) -> str:
    """본 응답의 갈래를 본 차례로 줄여 적는다. '502(0.4초부터 3번) → 새 컨테이너(5.1초부터 2번)'."""
    runs: list[tuple[str, float, int]] = []
    for current in samples:
        kind = pick(current)
        if runs and runs[-1][0] == kind:
            runs[-1] = (kind, runs[-1][1], runs[-1][2] + 1)
        else:
            runs.append((kind, current.at, 1))
    return " → ".join(f"{kind}({at:.1f}초부터 {count}번)" for kind, at, count in runs)


def first_at(samples: Sequence[Sample], hit: Callable[[Sample], bool]) -> float | None:
    return next((current.at for current in samples if hit(current)), None)


def sent(samples: Sequence[Sample]) -> bool:
    """표본의 요청(네 경로와 /proxy-alive)이 모두 실제로 나갔는가. 나가지 못한 요청(asked
    거짓)도 good 이 아니라 '닿지 않았다'로 읽히므로, 닿지 않음을 결과로 내는 회차는 이것을
    표지로 본다. good 인 응답은 늘 나간 요청의 것이라, 이것은 good 이 아닌 응답이 모두 나간
    요청의 것인지와 같다."""
    return all(
        reply.asked for current in samples for reply in (*current.via.values(), current.alive)
    )


def seconds_text(value: float | None) -> str:
    return "끝까지 없음" if value is None else f"{value:.1f}초"


@contextmanager
def case(ctx: Context, label: str) -> Generator[Slot]:
    """회차 하나를 세고 끝나면 한 줄로 낸다."""
    with ctx.rounds.round(label) as slot:
        yield slot
    entry = ctx.rounds.entries[-1]
    verdict = "측정" if entry.measured else "측정 아님"
    print(f"- [{verdict}] {entry.label} => {entry.result}", flush=True)


def wait_good(ctx: Context, *, seconds: float) -> dict[str, Box] | None:
    """네 경로가 저마다 지금의 제 컨테이너의 답을 낼 때까지 기다린다."""
    deadline = time.monotonic() + seconds
    while True:
        now = boxes()
        current = sample(ctx, time.monotonic(), {})
        if all(good(current.via[route], route, of(now, route)) for route in ROUTES):
            return now
        if time.monotonic() >= deadline:
            kinds = {route: current.via[route].kind() for route in ROUTES}
            print(f"! 기준선이 서지 않았다. 끝 응답 {kinds}", flush=True)
            return None
        time.sleep(0.5)


def settle(
    ctx: Context, stack: Stack, *, spares: int = 0, seconds: float = 60
) -> dict[str, Box] | None:
    """배치를 지우고 새로 띄워, 네 경로가 저마다 제 컨테이너의 답을 내는 것까지 본다. spares 를
    주면 그 수의 자리 채움을 먼저 띄워 낮은 주소를 차지하게 한다."""
    if not ctx.clean():
        return None
    if spares:
        scaled = ("up", "-d", "--scale", f"spare={spares}", "spare")
        first = stack.compose(*scaled, profiles=("spare",))
        if first.code != 0:
            print(f"! 자리 채움 up 실패(종료 {first.code}): {tail(first.err)}", flush=True)
            return None
    up = stack.compose("up", "-d")
    if up.code != 0:
        print(f"! 기준선 up 실패(종료 {up.code}): {tail(up.err)}", flush=True)
        return None
    return wait_good(ctx, seconds=seconds)


def free_spares(stack: Stack) -> bool:
    """자리 채움을 지워 낮은 주소를 비운다. 지워졌는지까지 본다."""
    stack.compose("rm", "-s", "-f", "spare", profiles=("spare",))
    return not any(name.startswith("spare-") for name in boxes())


def signed(sign: str, before: Box | None, after: Box | None) -> bool:
    """그 컨테이너가 그 조작으로 실제로 다시 만들어졌거나(새 id) 다시 시작됐는가(같은 id, 새 시작
    시각). auto 는 재시작 정책이 다시 띄운 것(RestartCount 증가)이다."""
    if before is None or after is None or not after.running:
        return False
    if sign == "recreated":
        return after.id != before.id
    if sign == "auto":
        return after.id == before.id and after.restarts > before.restarts
    return after.id == before.id and after.started != before.started


def change(before: Box | None, after: Box | None) -> str:
    if after is None:
        return "없어짐"
    if before is None:
        return "새로 생김"
    if after.id != before.id:
        return "다시 만들어짐"
    state = "" if after.running else f"(지금 {after.status}, 종료 코드 {after.exit_code})"
    if after.started != before.started:
        return f"다시 시작됨{state}"
    return f"그대로{state}"


# ---------- 항목 0: 환경과 판 ----------


def versions(ctx: Context) -> None:
    facts = parse(outer("version", "--format", "{{json .}}", timeout=60).out)
    platform = as_text(dig(facts, "Server", "Platform", "Name"), "?")
    engine = as_text(dig(facts, "Server", "Version"), "?")
    print(f"바깥 Docker: {platform}, 엔진 {engine}", flush=True)
    image = outer("image", "inspect", ctx.dind_image, "--format", "{{json .RepoTags}}", timeout=60)
    print(f"dind 이미지: {ctx.dind_image} 태그 {image.out.strip()}", flush=True)
    about = parse(inner("docker", "version", "--format", "{{json .}}", timeout=60).out)
    inner_engine = as_text(dig(about, "Server", "Version"), "?")
    info = parse(inner("docker", "info", "--format", "{{json .}}", timeout=60).out)
    keys = ("OperatingSystem", "KernelVersion", "Driver", "CgroupVersion", "Architecture")
    described = ", ".join(f"{key} {as_text(dig(info, key), '?')}" for key in keys)
    compose = inner("docker", "compose", "version", "--short", timeout=60).out.strip()
    print(f"안쪽 Engine {inner_engine}, Compose {compose}; {described}", flush=True)
    nginx = inner("docker", "run", "--rm", "--entrypoint", "nginx", ctx.nginx_image, "-v")
    python = inner("docker", "run", "--rm", ctx.python_image, "python", "--version")
    print(f"nginx: {tail(nginx.text, 1)} ({ctx.nginx_image})", flush=True)
    print(f"python: {tail(python.text, 1)} ({ctx.python_image})", flush=True)


def config_tests(ctx: Context) -> None:
    """compose 네트워크 밖(이름 serve·admin·widget·portal 이 풀리지 않는 자리)에서 세 설정을
    `nginx -t` 로 본다."""
    results: dict[str, Done] = {}
    for variant in ("static", "variable", "upstream"):
        mount = f"{REMOTE}/nginx/{variant}:/etc/nginx/conf.d:ro"
        run_test = ("docker", "run", "--rm", "-v", mount, ctx.nginx_image, "nginx", "-t")
        results[variant] = inner(*run_test, timeout=120)
    static = results["static"]
    unresolved = static.code != 0 and "host not found in upstream" in static.text
    with case(ctx, "0 [(가) 정적] 이름이 풀리지 않는 자리에서 nginx -t") as current:
        current.mark(measured=unresolved, result=f"종료 {static.code}: {tail(static.text, 1)}")
    for variant, title in (
        ("variable", "(나) resolver 와 변수"),
        ("upstream", "(다) upstream resolve"),
    ):
        done = results[variant]
        with case(ctx, f"0 [{title}] 이름이 풀리지 않는 자리에서 nginx -t") as current:
            passed = done.code == 0 and "test is successful" in done.text
            said = done.code != 0 and "nginx: [emerg]" in done.text
            verdict = "통과" if passed else "실패"
            result = f"{verdict}(종료 {done.code}): {tail(done.text, 1)}"
            # (가)가 이름을 풀지 못해 실패한 실행에서만 측정이다. 그래야 통과가 "이름을 풀지 않고
            # 시작한다"는 뜻이 된다.
            current.mark(measured=unresolved and (passed or said), result=result)


# ---------- 항목 1·2: 뒷단을 다시 띄운 뒤 프록시가 새 주소를 찾는지 ----------


@dataclass(frozen=True)
class Operation:
    """뒷단을 다시 띄우는 조작 하나. sign 은 targets 가 실제로 어떻게 됐어야 측정인가다."""

    name: str
    targets: tuple[str, ...]
    sign: str
    act: Callable[[Stack, Mapping[str, Box]], Done]
    env: Mapping[str, str] = field(default_factory=dict[str, str])


def act_recreate(stack: Stack, before: Mapping[str, Box]) -> Done:
    return stack.compose("up", "-d", "--force-recreate", "serve")


def act_restart(stack: Stack, before: Mapping[str, Box]) -> Done:
    return stack.compose("restart", "serve")


def act_remove_then_up(stack: Stack, before: Mapping[str, Box]) -> Done:
    box = of(before, "serve")
    if box is None:
        return Done(-1, "", "serve 컨테이너를 찾지 못했다")
    removed = inner("docker", "rm", "-f", box.id, timeout=60)
    up = stack.compose("up", "-d")
    return Done(up.code or removed.code, removed.out + up.out, removed.err + up.err)


def act_up(stack: Stack, before: Mapping[str, Box]) -> Done:
    return stack.compose("up", "-d")


def act_recreate_all(stack: Stack, before: Mapping[str, Box]) -> Done:
    return stack.compose("up", "-d", "--force-recreate", *ROUTES)


def act_docker_restart(stack: Stack, before: Mapping[str, Box]) -> Done:
    box = of(before, "serve")
    if box is None:
        return Done(-1, "", "serve 컨테이너를 찾지 못했다")
    return inner("docker", "restart", box.id, timeout=120)


# 컨테이너 안에서 서버 프로세스만 죽인다(1번 프로세스인 init 과 자기 자신은 뺀다). init 이 따라
# 끝나 컨테이너가 스스로 끝난 꼴이 되고, 재시작 정책이 다시 띄운다. `docker kill` 은 사람이 멈춘
# 것으로 세어져 정책이 다시 띄우지 않는다(netns 프로브 항목 7.3).
CRASH = """\
import os, signal
for entry in os.listdir('/proc'):
    if not entry.isdigit() or int(entry) in (1, os.getpid()):
        continue
    try:
        with open('/proc/' + entry + '/cmdline', 'rb') as source:
            line = source.read()
    except OSError:
        continue
    if b'/srv/server.py' in line:
        os.kill(int(entry), signal.SIGKILL)
"""


def act_crash(stack: Stack, before: Mapping[str, Box]) -> Done:
    box = of(before, "serve")
    if box is None:
        return Done(-1, "", "serve 컨테이너를 찾지 못했다")
    done = inner("docker", "exec", "-i", box.id, "python", "-", stdin=CRASH, timeout=60)
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline and not signed("auto", box, of(boxes(), "serve")):
        time.sleep(0.5)
    return done


OPERATIONS = (
    Operation("up -d --force-recreate serve", ("serve",), "recreated", act_recreate),
    Operation("restart serve", ("serve",), "restarted", act_restart),
    Operation("docker rm -f <serve> 뒤 up -d", ("serve",), "recreated", act_remove_then_up),
    Operation(
        "뒷단 넷의 이미지 태그를 v1→v2 로 바꾼 뒤 up -d(판 올림)",
        ROUTES,
        "recreated",
        act_up,
        {"BACKEND_TAG": "v2"},
    ),
    Operation(
        "up -d --force-recreate serve admin widget portal", ROUTES, "recreated", act_recreate_all
    ),
)
OUTSIDE_COMPOSE = (
    Operation(
        "docker restart <serve>(compose 를 거치지 않고)",
        ("serve",),
        "restarted",
        act_docker_restart,
    ),
    Operation(
        "serve 의 서버 프로세스가 죽어 재시작 정책이 다시 띄움", ("serve",), "auto", act_crash
    ),
)


@dataclass(frozen=True)
class Recovery:
    name: str
    sign: str
    act: Callable[[Stack], Done]


RELOAD = Recovery(
    "docker compose exec proxy nginx -s reload",
    "reloaded",
    lambda stack: stack.compose("exec", "-T", "proxy", "nginx", "-s", "reload"),
)
RESTART_PROXY = Recovery(
    "docker compose restart proxy", "restarted", lambda stack: stack.compose("restart", "proxy")
)


def answered(reply: Reply, route: str, before: Box | None, after: Box | None) -> str:
    """프록시를 거친 응답 하나를 누가 답했는지로 가른다."""
    if good(reply, route, after):
        return "새 컨테이너"
    if good(reply, route, before):
        return "옛 컨테이너"
    if reply.status == 200 and reply.name:
        return f"엉뚱한 컨테이너({reply.name})"
    return reply.kind()


def proven(samples: Sequence[Sample], route: str, box: Box | None) -> tuple[float | None, bool]:
    """그 경로가 그 컨테이너에 처음 닿은 때와, 그 요청이 그 컨테이너의 접근 기록에 있는지."""
    hit = next((current for current in samples if good(current.via[route], route, box)), None)
    if hit is None:
        return None, False
    return hit.at, logged(box, f"path=/{route}/?rid={hit.rid}")


ACCESS = re.compile(
    r"probe-access uri=(\S+) status=(\d+) upstream=(.*?) upstream_status=\S* took=\S+ pid=(\d+)"
)
IPV4 = re.compile(r"^\d+\.\d+\.\d+\.\d+$")


@dataclass(frozen=True)
class Access:
    """프록시의 접근 기록 한 줄(nginx/main/*.conf 의 probe 형식)."""

    status: str
    upstream: str
    pid: str


def access_log(box: Box | None) -> dict[str, Access]:
    """프록시의 접근 기록. 열쇠는 요청 URI 다."""
    if box is None:
        return {}
    done = inner("docker", "logs", "--tail", "5000", box.id, timeout=60)
    found: dict[str, Access] = {}
    for line in done.text.splitlines():
        match = ACCESS.search(line)
        if match:
            found[match.group(1)] = Access(match.group(2), match.group(3), match.group(4))
    return found


def aimed(entry: Access | None, old: Box | None, new: Box | None) -> str:
    """접근 기록 한 줄을, nginx 가 건 상류 주소가 옛 컨테이너의 것인지 새 컨테이너의 것인지로
    가른다. 상류에 닿지 못하고 끝난 요청(499, 502)도 nginx 가 걸려던 주소가 찍힌다."""
    if entry is None:
        return "접근 기록 없음"
    host = entry.upstream.rsplit(":", 1)[0]
    if not IPV4.match(host):
        return f"상류 {entry.upstream} {entry.status}"
    if new is not None and host == new.ip:
        where = "새 주소"
    elif old is not None and host == old.ip:
        where = "옛 주소"
    else:
        where = f"다른 주소 {last(host)}"
    return f"{where} {entry.status}"


CAUSES = (
    re.compile(r"connect\(\) failed \([^)]*\)"),
    re.compile(r"upstream timed out \([^)]*\)"),
    re.compile(r"no live upstreams"),
    re.compile(r"\S+ could not be resolved \([^)]*\)"),
)
UPSTREAM = re.compile(r'upstream: "([^"]*)"')


def upstream_errors(now: Mapping[str, Box]) -> str:
    """프록시의 오류 기록에서 상류로 못 간 까닭과 그때 nginx 가 건 상류 주소(끝의 한 줄)."""
    done = inner("docker", "logs", "--tail", "400", getattr(of(now, "proxy"), "id", ""), timeout=60)
    for line in reversed(done.text.splitlines()):
        cause = next((found.group(0) for pattern in CAUSES if (found := pattern.search(line))), "")
        if "[error]" in line and cause:
            target = UPSTREAM.search(line)
            return f"{cause}, 상류 {target.group(1) if target else '(적히지 않음)'}"
    return "상류 오류 줄 없음"


def disturb(
    ctx: Context,
    label: str,
    stack: Stack,
    operation: Operation,
    recoveries: Sequence[Recovery],
    *,
    window: float = 25,
) -> None:
    """새로 띄운 배치에서 조작 하나를 하고, 프록시를 거친 요청이 새 컨테이너에 닿는지 본다."""
    acted = stack.with_env(operation.env)
    lost: list[str] = []
    after: dict[str, Box] = {}
    with case(ctx, label) as current:
        before = settle(ctx, stack, spares=4)
        if before is None:
            current.mark(measured=False, result=ctx.tainted or "기준선이 서지 않았다")
            return
        freed = free_spares(stack)
        # 조작 직전에 한 번 묻는다. nginx 가 푼 주소를 막 기억한 때에 조작이 오게 하려는 것이다.
        warm = sample(ctx, time.monotonic(), {})
        done = operation.act(acted, before)
        since = time.monotonic()
        after = boxes()
        targets = {service: of(after, service) for service in operation.targets}
        moved = all(
            signed(operation.sign, of(before, service), box) for service, box in targets.items()
        )
        readdressed = all(
            box is not None and box.ip and box.ip != getattr(of(before, service), "ip", "")
            for service, box in targets.items()
        )
        directs = {service: box for service, box in targets.items() if box is not None}

        def reached(current_sample: Sample) -> bool:
            return all(good(current_sample.via[s], s, box) for s, box in targets.items())

        samples = watch(ctx, since, directs, reached, seconds=window, hits=2)
        log = access_log(of(after, "proxy"))
        parts: list[str] = []
        answered_alone = True
        log_ok = True
        for service, box in targets.items():
            old = of(before, service)
            alone = first_at(
                samples, lambda s, sv=service, b=box: good(s.direct.get(sv, Reply()), sv, b)
            )
            at, in_log = proven(samples, service, box)
            answered_alone = answered_alone and alone is not None
            if at is None:
                lost.append(service)
            else:
                log_ok = log_ok and in_log
            seen = trace(samples, lambda s, sv=service, o=old, b=box: answered(s.via[sv], sv, o, b))
            aims = trace(
                samples,
                lambda s, sv=service, o=old, b=box: aimed(log.get(f"/{sv}/?rid={s.rid}"), o, b),
            )
            primed = aimed(log.get(f"/{service}/?rid={warm.rid}"), old, box)
            moved_to = f"{last(old.ip if old else '')}→{last(box.ip if box else '')}"
            proof = "" if at is None else f", 접근 기록에 {'있다' if in_log else '없다'}"
            parts.append(
                f"{service}: 주소 {moved_to}, 스스로 답한 때 {seconds_text(alone)}, "
                f"프록시로 닿은 때 {seconds_text(at)}{proof}, 본 차례 [{seen}], "
                f"nginx 가 건 상류 [조작 직전 {primed} | 조작 뒤 {aims}]"
            )
        others = [route for route in ROUTES if route not in targets]
        steady = [
            route
            for route in others
            if all(good(s.via[route], route, of(before, route)) for s in samples)
        ]
        upset = {
            route: trace(
                samples, lambda s, r=route, b=before: answered(s.via[r], r, None, of(b, r))
            )
            for route in others
            if route not in steady
        }
        proxy = f"proxy {change(of(before, 'proxy'), of(after, 'proxy'))}"
        verdict = (
            "닿는다" if not lost else ("닿지 않는다" if len(lost) == len(targets) else "일부만")
        )
        if others:
            rest = "다른 경로는 내내 제 컨테이너" if not upset else f"다른 경로 {upset}"
        else:
            rest = "다른 경로 없음"
        cause = "" if not lost else f"; nginx 오류 기록: {upstream_errors(after)}"
        said = "" if done.code == 0 else f"; 명령 종료 {done.code}({tail(done.err, 1)})"
        result = f"{verdict}; {'; '.join(parts)}; {proxy}; {rest}{cause}{said}"
        marks = {
            "자리 채움을 지웠다": freed,
            "조작이 컨테이너에 닿았다": moved,
            "주소가 바뀌었다": readdressed,
            "새 컨테이너가 스스로 답했다": answered_alone,
            "닿은 요청이 접근 기록에 있다": log_ok,
        }
        missing = [name for name, held in marks.items() if not held]
        if missing:
            result = f"표지 없음 {missing}; {result}"
        current.mark(measured=not missing, result=result)
        if missing:
            lost.clear()
    for recovery in recoveries:
        if not lost:
            return
        lost = recover(ctx, f"{label} → 회복 `{recovery.name}`", acted, recovery, after, lost)


def recover(
    ctx: Context,
    label: str,
    stack: Stack,
    recovery: Recovery,
    settled: Mapping[str, Box],
    lost: Sequence[str],
) -> list[str]:
    """회복 조작 하나를 치고 닿지 않던 경로가 닿는지 본다. 아직 닿지 않는 경로를 돌려준다."""
    still = list(lost)
    with case(ctx, label) as current:
        before = boxes()
        reloads = count_logged(of(before, "proxy"), "reconfiguring")
        done = recovery.act(stack)
        since = time.monotonic()
        after = boxes()
        if recovery.sign == "reloaded":
            deadline = time.monotonic() + 5
            now_count = count_logged(of(after, "proxy"), "reconfiguring")
            while now_count <= reloads and time.monotonic() < deadline:
                time.sleep(0.5)
                now_count = count_logged(of(after, "proxy"), "reconfiguring")
            same = change(of(before, "proxy"), of(after, "proxy")) == "그대로"
            touched = done.code == 0 and reloads >= 0 and now_count > reloads and same
            how = f"nginx 기록의 reconfiguring 줄 {reloads}→{now_count}, proxy 그대로"
        else:
            touched = signed("restarted", of(before, "proxy"), of(after, "proxy"))
            how = f"proxy {change(of(before, 'proxy'), of(after, 'proxy'))}"

        def reached(current_sample: Sample) -> bool:
            return all(good(current_sample.via[s], s, of(after, s)) for s in lost)

        samples = watch(ctx, since, {}, reached, seconds=15, hits=2)
        proofs = {service: proven(samples, service, of(after, service)) for service in lost}
        still = [service for service, (at, in_log) in proofs.items() if at is None or not in_log]
        seen = {
            service: trace(
                samples, lambda s, sv=service: answered(s.via[sv], sv, None, of(after, sv))
            )
            for service in lost
        }
        moved = [s for s in ROUTES if of(after, s) != of(settled, s)]
        verdict = "회복됨" if not still else f"회복 안 됨({still})"
        said = "" if done.code == 0 else f"; 명령 종료 {done.code}({tail(done.err, 1)})"
        extra = f"; 그사이 뒷단이 바뀜 {moved}" if moved else ""
        current.mark(measured=touched, result=f"{verdict}; {how}; 본 차례 {seen}{extra}{said}")
    return still


VARIANTS = (
    ("(가) 정적", "static"),
    ("(나) resolver 와 변수", "variable"),
    ("(다) upstream resolve", "upstream"),
)


def section_1(ctx: Context) -> None:
    for title, variant in VARIANTS:
        stack = ctx.stack(variant)
        for operation in OPERATIONS:
            disturb(ctx, f"1 [{title}] {operation.name}", stack, operation, (RELOAD, RESTART_PROXY))
    # 위의 차례에서 restart proxy 는 reload 가 회복하지 못했을 때만 친다. reload 없이 restart proxy
    # 만으로 회복되는지를 따로 본다.
    stack = ctx.stack("static")
    label = f"1 [(가) 정적] {OPERATIONS[0].name} (회복을 restart proxy 부터)"
    disturb(ctx, label, stack, OPERATIONS[0], (RESTART_PROXY,))


def section_1w(ctx: Context) -> None:
    """(나)와 (다)를 작업 프로세스 하나(nginx/main/one-worker.conf)로 띄워 같은 조작을 한다.
    조작 직전의 요청이 옛 주소를 기억시킨 프로세스가 다음 요청을 꼭 받으므로, 다시 풀기 전까지
    옛 주소로 보내는 틈이 있는지 본다. 그 요청이 옛 주소로 갔다는 것은 접근 기록의 상류 주소로
    본다(결과의 "조작 직전")."""
    for title, variant in VARIANTS[1:]:
        stack = ctx.stack(variant).with_env({"NGINX_MAIN": "one-worker"})
        for operation in (OPERATIONS[0], OPERATIONS[3]):
            label = f"1w [{title}, 작업 프로세스 하나] {operation.name}"
            disturb(ctx, label, stack, operation, (RELOAD, RESTART_PROXY))


def section_2(ctx: Context) -> None:
    stack = ctx.stack("static", "compose.health.yml", "compose.depends-restart.yml")
    resolved = stack.compose("config", "--format", "json", timeout=60)
    depends = dig(parse(resolved.out), "services", "proxy", "depends_on", "serve")
    print(
        f"  config 가 푼 proxy 의 depends_on.serve: {json.dumps(depends, sort_keys=True)}",
        flush=True,
    )
    for operation in (*OPERATIONS, *OUTSIDE_COMPOSE):
        label = f"2 [(가) 정적 + depends_on restart: true] {operation.name}"
        disturb(ctx, label, stack, operation, (RELOAD, RESTART_PROXY))


# ---------- 항목 3: 해석을 가르는 갈래 ----------


def squatters() -> dict[str, Box]:
    """squatter 컨테이너. 열쇠는 inspect_by_label 이 이름에서 프로젝트 머리를 뗀
    'squat-<번호>'다."""
    return inspect_by_label(f"{SQUAT}=1") or {}


def squat(address: str, port: int, *, tries: int = 8) -> Box | None:
    """같은 네트워크에 squatter 를 하나씩 띄워, 그 주소를 받은 것이 나오면 돌려준다."""
    for index in range(tries):
        name = f"{SQUAT}-{index}"
        env = ("-e", "BACKEND_NAME=squatter", "-e", f"BACKEND_PORT={port}")
        create = ("docker", "run", "-d", "--init", "--name", name, "--label", f"{SQUAT}=1")
        started = inner(*create, "--network", NETWORK, *env, "ri-recover-backend:v1", timeout=60)
        if started.code != 0:
            return None
        # 첫 판은 여기서 머리를 떼지 않은 이름으로 찾아 옛 주소를 받은 squatter 를 늘 놓쳤다.
        box = squatters().get(name.removeprefix(f"{PROJECT}-"))
        if box is not None and box.ip == address:
            return box
    return None


def who(reply: Reply, new: Box | None, taker: Box | None) -> str:
    if good(reply, "serve", new):
        return "새 serve"
    if taker is not None and reply.status == 200 and reply.host == taker.hostname:
        return f"squatter(엉뚱한 컨테이너, 이름 {reply.name})"
    return reply.kind()


def taken(ctx: Context, label: str, stack: Stack) -> None:
    """serve 를 다시 만들어 주소를 옮기고, 옛 주소를 같은 포트의 squatter 가 차지하게 한 뒤 프록시의
    /serve/ 를 누가 답하는지 본다."""
    with case(ctx, label) as current:
        before = settle(ctx, stack, spares=4)
        if before is None:
            current.mark(measured=False, result=ctx.tainted or "기준선이 서지 않았다")
            return
        free_spares(stack)
        old = of(before, "serve")
        sample(ctx, time.monotonic(), {})
        stack.compose("up", "-d", "--force-recreate", "serve")
        since = time.monotonic()
        new = of(boxes(), "serve")
        taker = squat(old.ip if old else "", BACKENDS["serve"])
        directs = {"serve": new} if new is not None else {}
        # resolver 의 valid(5초)가 지난 뒤의 응답을 본다.
        time.sleep(max(0.0, 7 - (time.monotonic() - since)))
        samples = [sample(ctx, since, directs) for _ in range(4)]
        rid = samples[-1].rid
        port = BACKENDS["serve"]
        alone = ask([f"http://{taker.ip}:{port}/direct?rid={rid}"])[0] if taker else Reply()
        taker_alone = taker is not None and alone.status == 200 and alone.host == taker.hostname
        new_alone = any(good(s.direct.get("serve", Reply()), "serve", new) for s in samples)
        seen = trace(samples, lambda s: who(s.via["serve"], new, taker))
        final = samples[-1].via["serve"]
        in_log = True
        if good(final, "serve", new):
            in_log = logged(new, f"path=/serve/?rid={rid}")
        elif taker is not None and final.status == 200 and final.host == taker.hostname:
            in_log = logged(taker, f"path=/serve/?rid={rid}")
        marks = {
            "serve 가 다시 만들어졌다": signed("recreated", old, new),
            "serve 의 주소가 바뀌었다": bool(new and old and new.ip and new.ip != old.ip),
            "squatter 가 옛 주소를 받았다": taker is not None,
            "squatter 가 스스로 답했다": taker_alone,
            "새 serve 가 스스로 답했다": new_alone,
            "끝 요청이 답한 컨테이너의 접근 기록에 있다": in_log,
        }
        missing = [name for name, held in marks.items() if not held]
        moved_to = f"{last(old.ip if old else '')}→{last(new.ip if new else '')}"
        result = f"프록시의 /serve/ 를 답한 것 [{seen}]; serve 주소 {moved_to}, squatter 주소 "
        result += last(taker.ip) if taker else "(받지 못함)"
        if missing:
            result = f"표지 없음 {missing}; {result}"
        current.mark(measured=not missing, result=result)


def section_3a(ctx: Context) -> None:
    for title, variant in VARIANTS:
        label = f"3a [{title}] 다시 만든 serve 의 옛 주소를 같은 포트의 squatter 가 차지"
        taken(ctx, label, ctx.stack(variant))


def bump_until_moved(
    ctx: Context, stack: Stack, tries: int
) -> tuple[dict[str, Box], dict[str, Box], float, list[int], bool]:
    """자리 채움 없이 판 올림(태그를 바꾼 up -d)을 뒷단의 주소가 하나라도 바뀔 때까지 되풀이한다.
    마지막 올림의 앞 모습, 뒤 모습, 끝난 시각, 올림마다 주소가 바뀐 뒷단의 수, 올림마다 뒷단 넷이
    모두 다시 만들어졌는지를 돌려준다."""
    tag = "v1"
    history: list[int] = []
    recreated = True
    before = boxes()
    after = before
    since = time.monotonic()
    for _ in range(tries):
        before = boxes()
        tag = "v2" if tag == "v1" else "v1"
        sample(ctx, time.monotonic(), {})
        stack.with_env({"BACKEND_TAG": tag}).compose("up", "-d")
        since = time.monotonic()
        after = boxes()
        recreated = recreated and all(
            signed("recreated", of(before, route), of(after, route)) for route in ROUTES
        )
        history.append(len(readdressed(before, after)))
        if history[-1]:
            break
    return before, after, since, history, recreated


def readdressed(before: Mapping[str, Box], after: Mapping[str, Box]) -> list[str]:
    """다시 만들어졌고 주소도 바뀐 뒷단."""
    return [
        route
        for route in ROUTES
        if signed("recreated", of(before, route), of(after, route))
        and ip_of(after, route) != ip_of(before, route)
    ]


def natural(ctx: Context, label: str, stack: Stack, tries: int) -> None:
    with case(ctx, label) as current:
        if settle(ctx, stack) is None:
            current.mark(measured=False, result=ctx.tainted or "기준선이 서지 않았다")
            return
        before, after, since, history, recreated = bump_until_moved(ctx, stack, tries)
        changed = readdressed(before, after)
        if not changed:
            # 주소가 바뀌지 않은 것도 결과다. 표지는 올림마다 뒷단 넷이 실제로 다시 만들어진 것이다.
            result = (
                f"{len(history)}번 올렸고 주소가 바뀐 뒷단이 없었다(올림마다 바뀐 수 {history}, "
                f"올림마다 뒷단 넷이 다시 만들어졌는가 {recreated})"
            )
            current.mark(measured=recreated, result=result)
            return
        directs = {route: box for route in ROUTES if (box := of(after, route)) is not None}

        def reached(current_sample: Sample) -> bool:
            return all(good(current_sample.via[r], r, of(after, r)) for r in ROUTES)

        samples = watch(ctx, since, directs, reached, seconds=20, hits=2)
        alone = all(
            any(good(s.direct.get(r, Reply()), r, of(after, r)) for s in samples) for r in changed
        )
        table = ", ".join(
            f"{r} {last(ip_of(before, r))}→{last(ip_of(after, r))}" for r in ("proxy", *ROUTES)
        )
        seen = {
            r: trace(samples, lambda s, r=r: answered(s.via[r], r, None, of(after, r)))
            for r in changed
        }
        # 프록시의 접근 기록으로 nginx 가 실제로 건 주소를 본다(옛 주소의 새 주인에게 갔는지).
        log = access_log(of(after, "proxy"))
        aims = {
            r: trace(
                samples,
                lambda s, r=r: aimed(log.get(f"/{r}/?rid={s.rid}"), of(before, r), of(after, r)),
            )
            for r in changed
        }
        proofs = {r: proven(samples, r, of(after, r)) for r in changed}
        log_ok = all(in_log for at, in_log in proofs.values() if at is not None)
        lost = [r for r, (at, _) in proofs.items() if at is None]
        verdict = "닿는다" if not lost else f"닿지 않는다({lost})"
        result = (
            f"{verdict}; 올린 횟수 {len(history)}(올림마다 주소가 바뀐 뒷단 수 {history}); "
            f"주소 {table}; 바뀐 경로의 본 차례 {seen}; nginx 가 건 상류 {aims}"
        )
        if lost:
            result += f"; nginx 오류 기록: {upstream_errors(after)}"
        # 주소가 바뀐 갈래도 올림마다 뒷단 넷이 모두 다시 만들어진 회차만 판 올림을 잰 것이다.
        # 일부만 다시 만들어지면 바뀐 경로가 닿아도 측정이 아니다.
        if not recreated:
            result = f"표지 없음 ['올림마다 뒷단 넷이 다시 만들어졌다']; {result}"
        current.mark(measured=recreated and alone and log_ok, result=result)


def section_3b(ctx: Context, *, tries: int = 6) -> None:
    for title, variant in VARIANTS:
        label = f"3b [{title}] 자리 채움 없이 판 올림(up -d)을 주소가 바뀔 때까지(최대 {tries}번)"
        natural(ctx, label, ctx.stack(variant), tries)


def dns_ttl(stack: Stack, name: str) -> str:
    done = stack.compose("exec", "-T", "admin", "python", "/srv/dns_ttl.py", name, timeout=60)
    return tail(done.out, 1) or f"질의 실패(종료 {done.code}): {tail(done.err, 1)}"


def section_3c(ctx: Context) -> None:
    stack = ctx.stack("variable-novalid")
    window = 660.0 if ctx.long else 25.0
    label = f"3c [(나)에서 valid 를 뺀 설정] {OPERATIONS[0].name} ({window:.0f}초까지 본다)"
    disturb(ctx, label, stack, OPERATIONS[0], (RELOAD, RESTART_PROXY), window=window)
    with case(ctx, "3c 내장 DNS(127.0.0.11)가 서비스 이름에 주는 TTL") as current:
        before = settle(ctx, ctx.stack("variable"))
        if before is None:
            current.mark(measured=False, result=ctx.tainted or "기준선이 서지 않았다")
            return
        answer = dns_ttl(ctx.stack("variable"), "serve")
        serve = of(before, "serve")
        expected = f"{serve.ip}:" if serve is not None else "?"
        current.mark(measured=expected in answer and "rcode=0" in answer, result=answer)


# ---------- 항목 4·5: 껐다 켠 뒤 스스로 돌아오는지 ----------


def daemon_starts() -> int:
    """supervise.sh 가 dockerd 를 띄운 횟수(dind 컨테이너의 기록에서 센다)."""
    done = outer("logs", DIND, timeout=60)
    return sum(1 for line in done.text.splitlines() if line.startswith("supervise: dockerd start"))


def wait_inner(seconds: float) -> bool:
    """안쪽 dockerd 가 답할 때까지 기다린다."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if inner("docker", "info", "--format", "{{.ServerVersion}}", timeout=30).code == 0:
            return True
        time.sleep(1)
    return False


# dockerd 의 pid 파일을 읽고, 그 pid 의 이름이 dockerd 일 때만 TERM 을 보낸다(pid 만 보고 끄지
# 않는다). dind 컨테이너 자기 pid 이름공간 안의 일이다.
TERM_DOCKERD = (
    'pid="$(cat /var/run/docker.pid 2>/dev/null)"; '
    'name="$(cat "/proc/$pid/comm" 2>/dev/null)"; '
    'if [ -n "$pid" ] && [ "$name" = dockerd ]; then kill -TERM "$pid" && echo "sent $pid"; '
    'else echo "skip pid=$pid name=$name"; exit 3; fi'
)


def event_daemon() -> tuple[bool, str]:
    starts = daemon_starts()
    sent = shell(TERM_DOCKERD)
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline and daemon_starts() <= starts:
        time.sleep(0.5)
    now = daemon_starts()
    ready = wait_inner(120)
    return sent.code == 0 and now > starts and ready, f"dockerd 시작 횟수 {starts}→{now}"


def dind_started() -> str:
    return outer("inspect", DIND, "--format", "{{.State.StartedAt}}", timeout=60).out.strip()


def event_reboot() -> tuple[bool, str]:
    before = dind_started()
    done = outer("restart", "-t", "120", DIND, timeout=300)
    after = dind_started()
    ready = wait_inner(120)
    return done.code == 0 and bool(
        after
    ) and after != before and ready, "dind 컨테이너 새 시작 시각"


def event_power() -> tuple[bool, str]:
    before = dind_started()
    killed = outer("kill", DIND, timeout=120)
    started = outer("start", DIND, timeout=120)
    after = dind_started()
    ready = wait_inner(120)
    happened = killed.code == 0 and started.code == 0 and bool(after) and after != before
    return happened and ready, "dind 컨테이너를 죽였다 켬, 새 시작 시각"


EVENTS: tuple[tuple[str, Callable[[], tuple[bool, str]]], ...] = (
    ("데몬만 다시 켬(dockerd 에 TERM)", event_daemon),
    ("서버를 정상으로 껐다 켬(docker restart dind)", event_reboot),
    ("서버가 죽었다 켜짐(docker kill dind 뒤 start)", event_power),
)


def state_of(name: str, before: Mapping[str, Box], after: Mapping[str, Box]) -> str:
    """사건 앞뒤로 그 서비스의 컨테이너가 어떻게 됐는지(다시 시작됐는지, 주소, 재시작 횟수)."""
    text = f"{name} {change(of(before, name), of(after, name))}"
    if of(after, name) is None:
        return text
    moved = f"{last(ip_of(before, name))}→{last(ip_of(after, name))}"
    more = restarts_of(after, name) - restarts_of(before, name)
    return f"{text} 주소 {moved} 재시작 횟수 +{more}"


def boot(
    ctx: Context,
    label: str,
    stack: Stack,
    event: Callable[[], tuple[bool, str]],
    *,
    stopped: Sequence[str] = (),
    window: float = 75,
    settle_seconds: float = 60,
) -> None:
    """새로 띄운 배치에서 사건 하나를 내고, 사람 손 없이 컨테이너가 다시 떠 경로가 답하는지 본다."""
    with case(ctx, label) as current:
        before = settle(ctx, stack, seconds=settle_seconds)
        if before is None:
            current.mark(measured=False, result=ctx.tainted or "기준선이 서지 않았다")
            return
        for service in stopped:
            stack.compose("stop", service)
        before = boxes()
        held = not any(is_running(before, service) for service in stopped)
        emerg = count_logged(of(before, "proxy"), "host not found in upstream")
        since = time.monotonic()
        happened, how = event()
        ready = time.monotonic() - since

        def reached(current_sample: Sample) -> bool:
            return all(good(current_sample.via[r], r, of(before, r)) for r in ROUTES)

        samples = watch(ctx, since, {}, reached, seconds=window, hits=2, pause=1.0)
        after = boxes()
        log = access_log(of(after, "proxy"))
        states = ", ".join(state_of(name, before, after) for name in ("proxy", *ROUTES))
        routes: list[str] = []
        log_ok = True
        for route in ROUTES:
            at, in_log = proven(samples, route, of(before, route))
            if at is not None:
                log_ok = log_ok and in_log
            seen = trace(samples, lambda s, r=route: answered(s.via[r], r, None, of(before, r)))
            text = f"{route} {seconds_text(at)} [{seen}]"
            if at is None:
                aims = trace(
                    samples,
                    lambda s, r=route: aimed(log.get(f"/{r}/?rid={s.rid}"), None, of(after, r)),
                )
                text += f"(nginx 가 건 상류 [{aims}])"
            routes.append(text)
        back = all(is_running(after, name) for name in ("proxy", *ROUTES))
        all_at = first_at(samples, reached)
        emerg_now = count_logged(of(after, "proxy"), "host not found in upstream")
        if all_at is not None:
            verdict = f"스스로 돌아온다(네 경로 모두 {seconds_text(all_at)})"
        elif back:
            verdict = "컨테이너는 모두 떴지만 닿지 않는 경로가 있다"
        else:
            verdict = "돌아오지 않은 컨테이너가 있다"
        result = (
            f"{verdict}; 데몬이 다시 답한 때 {ready:.1f}초({how}); {states}; 경로가 처음 닿은 때 "
            f"{'; '.join(routes)}; 프록시 기록의 host not found 줄 {emerg}→{emerg_now}"
        )
        marks = {"사건이 실제로 났다": happened, "멈춰 둔 뒷단이 멈춰 있었다": held}
        marks["닿은 요청이 접근 기록에 있다"] = log_ok
        marks["요청이 모두 실제로 나갔다"] = sent(samples)
        missing = [name for name, held_mark in marks.items() if not held_mark]
        if missing:
            result = f"표지 없음 {missing}; {result}"
        current.mark(measured=not missing, result=result)


def section_4(ctx: Context) -> None:
    for title, variant in VARIANTS:
        stack = ctx.stack(variant)
        for name, event in EVENTS:
            boot(ctx, f"4 [{title}, unless-stopped] {name}", stack, event)


def section_5(ctx: Context) -> None:
    daemon_name, daemon = EVENTS[0]
    reboot_name, reboot = EVENTS[1]
    variable = ctx.stack("variable")
    always = variable.with_env({"RESTART_POLICY": "always"})
    none = variable.with_env({"RESTART_POLICY": "no"})
    boot(ctx, f"5 [(나), always] {daemon_name}", always, daemon)
    boot(ctx, f"5 [(나), 정책 없음(대조)] {daemon_name}", none, daemon, window=20)
    boot(ctx, f"5 [(나), 정책 없음(대조)] {reboot_name}", none, reboot, window=20)
    for event_name, event in ((daemon_name, daemon), (reboot_name, reboot)):
        label = f"5 [(나), unless-stopped, 위젯을 compose stop 으로 멈춰 둠] {event_name}"
        boot(ctx, label, variable, event, stopped=("widget",), window=25)
        label = f"5 [(나), always, 위젯을 compose stop 으로 멈춰 둠] {event_name}"
        boot(ctx, label, always, event, stopped=("widget",), window=40)
    for title, variant in (VARIANTS[0], VARIANTS[2]):
        label = f"5 [{title}, unless-stopped, 위젯을 compose stop 으로 멈춰 둠] {daemon_name}"
        boot(ctx, label, ctx.stack(variant), daemon, stopped=("widget",), window=30)


# ---------- 항목 6: 프록시가 뜰 때 뒷단 하나의 이름이 풀리지 않는 경우 ----------


def proxy_state(before: Mapping[str, Box], now: Mapping[str, Box]) -> tuple[bool, str]:
    """프록시가 before 뒤에 다시 시작됐는지(새 시작 시각이거나 재시작 횟수 증가)와 지금 모습."""
    old, new = of(before, "proxy"), of(now, "proxy")
    if old is None or new is None:
        return False, "proxy 없음"
    restarted = new.started != old.started or new.restarts > old.restarts
    state = f"proxy {new.status}(재시작 횟수 {new.restarts}, 종료 코드 {new.exit_code})"
    return restarted, state


def unresolved(ctx: Context, label: str, stack: Stack, outage: float) -> None:
    """위젯을 멈춘 채(이름이 풀리지 않는다) 프록시를 다시 시작하고, 그동안과 위젯을 다시 띄운 뒤를
    본다."""
    with case(ctx, label) as current:
        settled = settle(ctx, stack)
        if settled is None:
            current.mark(measured=False, result=ctx.tainted or "기준선이 서지 않았다")
            return
        stack.compose("stop", "widget")
        before = boxes()
        widget_down = not is_running(before, "widget")
        # 멈춘 서비스의 이름을 내장 DNS 에 물으면 무엇이 얼마 만에 오는지(같은 네트워크의 admin
        # 에서 묻는다).
        lookup = dns_ttl(stack, "widget")
        done = stack.compose("restart", "proxy", timeout=120)
        since = time.monotonic()
        during = watch(ctx, since, {}, lambda _: False, seconds=outage, pause=1.0)
        middle = boxes()
        restarted, state = proxy_state(before, middle)
        emerg = log_lines(of(middle, "proxy"), "host not found in upstream", 1)
        stack.compose("start", "widget")
        again = time.monotonic()

        def reached(current_sample: Sample) -> bool:
            return all(good(current_sample.via[r], r, of(settled, r)) for r in ROUTES)

        def seen(samples: Sequence[Sample], route: str) -> str:
            box = of(settled, route)
            return trace(samples, lambda s: answered(s.via[route], route, None, box))

        later = watch(ctx, again, {}, reached, seconds=90, hits=2, pause=1.0)
        final = boxes()
        at, in_log = proven(later, "widget", of(settled, "widget"))
        seen_during = {
            "프록시 자신(/proxy-alive)": trace(during, lambda s: s.alive.kind()),
            "serve": seen(during, "serve"),
            "widget": seen(during, "widget"),
        }
        seen_later = trace(
            later, lambda s: "네 경로 모두 닿음" if reached(s) else f"아직({s.alive.kind()})"
        )
        result = (
            f"위젯이 멈춘 동안 {seen_during}; 그때 {state}; 위젯을 다시 띄운 뒤 네 경로가 모두 "
            f"닿은 때 {seconds_text(first_at(later, reached))}, 본 차례 [{seen_later}], "
            f"끝의 proxy 재시작 횟수 {restarts_of(final, 'proxy')}"
        )
        if emerg:
            result += f"; nginx 기록: {emerg[-160:]}"
        if done.code != 0:
            result += f"; restart proxy 종료 {done.code}({tail(done.err, 1)})"
        result += f"; 멈춘 위젯의 이름을 내장 DNS 에 물은 결과: {lookup}"
        marks = {
            "위젯이 멈춰 있었다": widget_down,
            "프록시가 다시 시작됐다": restarted,
            "위젯이 다시 떴다": is_running(final, "widget"),
            "닿은 요청이 접근 기록에 있다": at is None or in_log,
            "요청이 모두 실제로 나갔다": sent(during) and sent(later),
        }
        missing = [name for name, held in marks.items() if not held]
        if missing:
            result = f"표지 없음 {missing}; {result}"
        current.mark(measured=not missing, result=result)


def section_6(ctx: Context, *, outage: float = 20) -> None:
    for title, variant in VARIANTS:
        label = f"6 [{title}] 위젯을 멈춘 채 restart proxy, {outage:.0f}초 뒤 위젯을 다시 띄움"
        unresolved(ctx, label, ctx.stack(variant), outage)


# ---------- 항목 7: 늦게 뜨는 위젯 ----------

DELAY = 20
HEALTHY = ("compose.health.yml", "compose.depends.yml")


def slow_up(ctx: Context, label: str, stack: Stack) -> None:
    """위젯이 DELAY 초 뒤에 포트를 여는 배치를 처음 띄우며, 그동안 경로마다 무엇이 답하는지 본다."""
    acted = stack.with_env({"WIDGET_DELAY": str(DELAY)})
    with case(ctx, label) as current:
        if not ctx.clean():
            current.mark(measured=False, result=ctx.tainted)
            return
        since = time.monotonic()
        process = acted.spawn("up", "-d")

        def reached(current_sample: Sample) -> bool:
            now = boxes()
            return all(good(current_sample.via[r], r, of(now, r)) for r in ROUTES)

        samples = watch(ctx, since, {}, reached, seconds=DELAY + 45, hits=2, pause=1.0)
        try:
            output, _ = process.communicate(timeout=120)
        except subprocess.TimeoutExpired:
            process.kill()
            output, _ = process.communicate(timeout=30)
        up_took = time.monotonic() - since
        raw("spawned up -d", decode(output))
        now = boxes()
        widget = of(now, "widget")
        delayed = logged(widget, f"delay={float(DELAY)}") and logged(widget, "backend-listen")
        firsts = {
            route: first_at(samples, lambda s, r=route: good(s.via[r], r, of(now, r)))
            for route in ROUTES
        }
        alive_at = first_at(samples, lambda s: s.alive.status == 200)
        widget_at = firsts["widget"]
        # 보내지 못한 요청(asked 거짓)도 good 이 아니다. 실제로 보낸 요청이 닿지 않은 것만
        # 기다림이다.
        waited = any(
            s.via["widget"].asked and not good(s.via["widget"], "widget", widget)
            for s in samples
            if widget_at is None or s.at < widget_at
        )
        _, in_log = proven(samples, "widget", widget)
        seen = {
            route: trace(samples, lambda s, r=route: answered(s.via[r], r, None, of(now, r)))
            for route in ("serve", "widget")
        }
        # nginx 가 건 상류: 주소가 찍히면 이름은 풀렸고, '-'나 upstream 이름이면 주소 없이 끝났다.
        log = access_log(of(now, "proxy"))
        aims = {
            route: trace(
                samples, lambda s, r=route: aimed(log.get(f"/{r}/?rid={s.rid}"), None, of(now, r))
            )
            for route in ("serve", "widget")
        }
        result = (
            f"프록시가 처음 답한 때 {seconds_text(alive_at)}; serve 가 처음 닿은 때 "
            f"{seconds_text(firsts['serve'])}; widget 이 처음 닿은 때 {seconds_text(widget_at)}; "
            f"본 차례 {seen}; nginx 가 건 상류 {aims}; 끝의 proxy 재시작 횟수 "
            f"{restarts_of(now, 'proxy')}; up -d 가 끝난 때 {up_took:.1f}초 이내"
            f"(종료 {process.returncode})"
        )
        marks = {
            "위젯의 기록에 지연이 찍혔다": delayed,
            "위젯 경로가 닿기 전에 닿지 않는 응답을 봤다": waited,
            "위젯이 지연 뒤에 닿았다": widget_at is not None and widget_at >= DELAY - 5 and in_log,
        }
        missing = [name for name, held in marks.items() if not held]
        if missing:
            result = f"표지 없음 {missing}; {result}"
        current.mark(measured=not missing, result=result)


def section_7(ctx: Context) -> None:
    for title, variant in VARIANTS:
        stack = ctx.stack(variant)
        slow_up(ctx, f"7 [{title}, depends_on 없음] 위젯이 {DELAY}초 늦게 뜨는 배치를 up -d", stack)
        label = f"7 [{title}, depends_on service_healthy] 위젯이 {DELAY}초 늦게 뜨는 배치를 up -d"
        slow_up(ctx, label, stack.with_files(*HEALTHY))
    name, event = EVENTS[0]
    for title, variant in (VARIANTS[0], VARIANTS[1]):
        stack = ctx.stack(variant, *HEALTHY).with_env({"WIDGET_DELAY": str(DELAY)})
        label = f"7 [{title}, depends_on service_healthy, 위젯 {DELAY}초 지연] {name}"
        boot(ctx, label, stack, event, settle_seconds=DELAY + 60)


# ---------- 항목 8: 호스트에서 고친 설정 파일과 nginx -s reload ----------

LIVE = f"{REMOTE}/live"
STAGE = f"{REMOTE}/stage"
EDIT_LINE = '    location = /edited {{ return 200 "edited-{token}\\n"; }}\n'


def edited_conf(token: str) -> str:
    """정적 설정에 location 하나를 더한 새 설정."""
    source = (HERE / "nginx" / "static" / "default.conf").read_text(encoding="utf-8")
    anchor = "    location = /proxy-alive {"
    return source.replace(anchor, EDIT_LINE.format(token=token) + anchor, 1)


def inode() -> str:
    return shell(f"stat -c %i {LIVE}/default.conf").out.strip()


@dataclass(frozen=True)
class Edit:
    """호스트(dind)에서 설정 파일을 고치는 방법 하나. replaces 는 그 방법이 파일을 새로 만들어 바꿔
    끼우는가(inode 가 바뀌어야 하는가)다."""

    name: str
    script: str
    replaces: bool


SED = (
    "sed -i 's|    location = /proxy-alive {|"
    '    location = /edited { return 200 "edited-TOKEN\\\\n"; }\\n&|\' '
)
EDITS = (
    Edit(
        "제자리에서 덮어쓴다(cat 새것 > 파일)",
        f"cat {STAGE}/next.conf > {LIVE}/default.conf",
        replaces=False,
    ),
    Edit(
        "새 파일을 만들어 바꿔 끼운다(mv 새것 파일)",
        f"mv {STAGE}/next.conf {LIVE}/default.conf",
        replaces=True,
    ),
    Edit("sed -i 로 한 줄을 더한다", f"{SED}{LIVE}/default.conf", replaces=True),
)
MOUNTS = (
    ("설정을 폴더로 얹음", "compose.mount-dir.yml"),
    ("설정을 파일 하나로 얹음", "compose.mount-file.yml"),
)


def prepare_live() -> bool:
    script = (
        f"rm -rf {LIVE} {STAGE} && mkdir -p {LIVE} {STAGE} && "
        f"cp {REMOTE}/nginx/static/default.conf {LIVE}/default.conf"
    )
    return shell(script).code == 0


def edited_reply(token: str) -> tuple[bool, str]:
    reply = ask([f"{PROXY_URL}/edited"])[0]
    return reply.status == 200 and reply.body.strip() == f"edited-{token}", reply.kind()


def section_8(ctx: Context) -> None:
    for mount_title, mount_file in MOUNTS:
        for edit in EDITS:
            label = f"8 [{mount_title}] 호스트에서 {edit.name} 뒤 nginx -s reload"
            reload_round(ctx, label, ctx.stack("static", mount_file), edit)
    broken_round(ctx, ctx.stack("static", MOUNTS[0][1]))


def reload_round(ctx: Context, label: str, stack: Stack, edit: Edit) -> None:
    token = secrets.token_hex(3)
    with case(ctx, label) as current:
        if not ctx.clean() or not prepare_live():
            current.mark(measured=False, result=ctx.tainted or "설정 폴더를 준비하지 못했다")
            return
        if stack.compose("up", "-d").code != 0 or wait_good(ctx, seconds=60) is None:
            current.mark(measured=False, result="기준선이 서지 않았다")
            return
        before_edit, _ = edited_reply(token)
        inode_before = inode()
        inner("sh", "-c", f"cat > {STAGE}/next.conf", stdin=edited_conf(token), timeout=30)
        edited = shell(edit.script.replace("TOKEN", token))
        inode_after = inode()
        host_has = shell(f"grep -c 'edited-{token}' {LIVE}/default.conf").out.strip() == "1"
        grep = ("grep", "-c", f"edited-{token}", "/etc/nginx/conf.d/default.conf")
        inside = stack.compose("exec", "-T", "proxy", *grep, timeout=60).out.strip() == "1"
        proxy = of(boxes(), "proxy")
        reloads = count_logged(proxy, "reconfiguring")
        reload = RELOAD.act(stack)
        deadline = time.monotonic() + 5
        while count_logged(proxy, "reconfiguring") <= reloads and time.monotonic() < deadline:
            time.sleep(0.5)
        reloaded = reload.code == 0 and count_logged(proxy, "reconfiguring") > reloads
        time.sleep(1)
        after_reload, kind_reload = edited_reply(token)
        took = "먹었다" if after_reload else f"먹지 않았다(/edited 가 {kind_reload})"
        result = (
            f"reload 뒤 새 설정이 {took}; "
            f"호스트 파일의 inode {'바뀜' if inode_after != inode_before else '그대로'}, "
            f"컨테이너 안의 파일에 새 줄이 {'보인다' if inside else '보이지 않는다'}"
        )
        if not after_reload:
            for name, act in (
                ("docker compose up -d", lambda: stack.compose("up", "-d")),
                ("docker compose restart proxy", lambda: stack.compose("restart", "proxy")),
            ):
                act()
                time.sleep(2)
                fixed, kind = edited_reply(token)
                result += f"; `{name}` 뒤 {'먹었다' if fixed else f'먹지 않았다({kind})'}"
                if fixed:
                    break
        marks = {
            "고치기 전에는 새 location 이 없었다": not before_edit,
            "호스트의 파일이 고쳐졌다": edited.code == 0 and host_has,
            "inode 가 기대한 쪽이다": (inode_after != inode_before) == edit.replaces
            and bool(inode_before),
            "reload 가 nginx 에 닿았다": reloaded,
        }
        missing = [name for name, held in marks.items() if not held]
        if missing:
            result = f"표지 없음 {missing}; {result}"
        current.mark(measured=not missing, result=result)


def broken_round(ctx: Context, stack: Stack) -> None:
    label = "8 [설정을 폴더로 얹음] 깨진 설정으로 바꾼 뒤 nginx -t 와 nginx -s reload"
    with case(ctx, label) as current:
        if not ctx.clean() or not prepare_live():
            current.mark(measured=False, result=ctx.tainted or "설정 폴더를 준비하지 못했다")
            return
        if stack.compose("up", "-d").code != 0 or wait_good(ctx, seconds=60) is None:
            current.mark(measured=False, result="기준선이 서지 않았다")
            return
        broken = edited_conf("x").replace("listen 8080;", "listen 8080; no_such_directive on;", 1)
        inner("sh", "-c", f"cat > {LIVE}/default.conf", stdin=broken, timeout=30)
        test = stack.compose("exec", "-T", "proxy", "nginx", "-t", timeout=60)
        proxy = of(boxes(), "proxy")
        reload = RELOAD.act(stack)
        time.sleep(2)
        refused = log_lines(proxy, "no_such_directive", 1)
        still = wait_good(ctx, seconds=10) is not None
        after = of(boxes(), "proxy")
        result = (
            f"nginx -t 종료 {test.code}({tail(test.text, 1)[-120:]}); "
            f"nginx -s reload 종료 {reload.code}; "
            f"그 뒤 네 경로는 {'옛 설정으로 계속 답한다' if still else '답하지 않는다'}; "
            f"proxy {change(proxy, after)}; nginx 기록: {refused[-160:] or '없음'}"
        )
        # reload 가 깨진 설정 때문에 거부됐다는 표지. reload 명령 자신이 설정을 읽다 그 줄로
        # 끝났거나(신호를 보내지 않은 길), 신호를 받은 nginx 가 기록에 그 줄을 남겼다(신호를 보낸
        # 길). docker compose exec 가 실행 오류로 끝나도 옛 프록시는 계속 답하므로 종료 코드로는
        # 가르지 못한다.
        rejected = (reload.code != 0 and "no_such_directive" in reload.text) or bool(refused)
        if not rejected:
            result = f"표지 없음 ['reload 가 깨진 설정 때문에 거부됐다']; {result}"
        tested = test.code != 0 and "no_such_directive" in test.text
        current.mark(measured=tested and rejected, result=result)


# ---------- dind 의 삶 ----------


def labelled(kind: str, name: str) -> str | None:
    """그 이름의 컨테이너(container)나 볼륨(volume)이 있으면 이 프로브의 표지 값을, 없으면 None 을
    돌려준다."""
    template = '{{index .Config.Labels "%s"}}' if kind == "container" else '{{index .Labels "%s"}}'
    done = outer(kind, "inspect", name, "--format", template % MARK, timeout=60)
    return done.out.strip() if done.code == 0 else None


def dind_down() -> bool:
    """dind 컨테이너와 그 볼륨을 지운다. 이 프로브의 표지가 있을 때만 지우고, 지워졌는지까지
    본다."""
    for kind, name, remove in (
        ("container", DIND, ("rm", "-f", "-v", DIND)),
        ("volume", VOLUME, ("volume", "rm", VOLUME)),
    ):
        mark = labelled(kind, name)
        if mark is None:
            continue
        if mark != "1":
            print(f"! {kind} {name} 에 이 프로브의 표지가 없다. 건드리지 않는다.", flush=True)
            return False
        outer(*remove, timeout=180)
        if labelled(kind, name) is not None:
            print(f"! {kind} {name} 를 지우지 못했다.", flush=True)
            return False
    return True


def dind_up(ctx: Context, *, reuse: bool) -> bool:
    for name in SHELL_FILES:
        if b"\r" in (HERE / name).read_bytes():
            print(f"! {name} 의 줄 끝이 CRLF 다. dind 안의 sh 가 읽지 못한다.", flush=True)
            return False
    running = outer("inspect", DIND, "--format", "{{.State.Running}}", timeout=60).out.strip()
    if reuse and labelled("container", DIND) == "1" and running == "true":
        print("있는 dind 컨테이너를 다시 쓴다(--reuse).", flush=True)
    else:
        if not dind_down():
            return False
        created = outer("volume", "create", "--label", f"{MARK}=1", VOLUME, timeout=60)
        if created.code != 0:
            print(f"! 볼륨을 만들지 못했다: {tail(created.err)}", flush=True)
            return False
        create = ("create", "--privileged", "--init", "--name", DIND, "--label", f"{MARK}=1")
        mounts = ("--tmpfs", "/run:exec", "-v", f"{VOLUME}:/var/lib/docker")
        command = ("--entrypoint", "sh", ctx.dind_image, f"{REMOTE}/supervise.sh")
        made = outer(*create, *mounts, *command, timeout=120)
        if made.code != 0:
            print(f"! dind 컨테이너를 만들지 못했다: {tail(made.err)}", flush=True)
            return False
        # 새로 만든 컨테이너는 멈춰 있다. 지우기 전에 읽은 값이 "true" 여도(--keep 으로 남긴 것을
        # --reuse 없이 다시 돌린 때) 아래에서 시작해야 한다.
        running = "false"
    copied = outer("cp", f"{HERE}/.", f"{DIND}:{REMOTE}", timeout=120)
    if copied.code != 0:
        print(f"! 프로브 파일을 dind 에 넣지 못했다: {tail(copied.err)}", flush=True)
        return False
    if running != "true" and outer("start", DIND, timeout=120).code != 0:
        print("! dind 컨테이너를 시작하지 못했다.", flush=True)
        return False
    if not wait_inner(180):
        print(
            f"! 안쪽 dockerd 가 답하지 않는다: {tail(outer('logs', '--tail', '20', DIND).text, 6)}"
        )
        return False
    return True


def load_images(ctx: Context) -> bool:
    """안쪽 엔진에 nginx 와 python 이미지를 digest 로 받고 뒷단 이미지를 v1·v2 로 짓는다."""
    for reference in (ctx.nginx_image, ctx.python_image):
        if inner("docker", "image", "inspect", reference, timeout=60).code == 0:
            continue
        pulled = inner("docker", "pull", "-q", reference, timeout=900)
        if pulled.code != 0:
            print(f"! 안쪽 엔진이 이미지를 받지 못했다 {reference}: {tail(pulled.err)}", flush=True)
            return False
    for tag in ("v1", "v2"):
        build = ("docker", "build", "-q", "--build-arg", f"BASE={ctx.python_image}")
        target = ("--build-arg", f"VERSION={tag}", "-t", f"ri-recover-backend:{tag}")
        built = inner(*build, *target, f"{REMOTE}/backend", timeout=600)
        if built.code != 0:
            print(f"! 뒷단 이미지를 짓지 못했다({tag}): {tail(built.err)}", flush=True)
            return False
    return True


def section_3(ctx: Context) -> None:
    section_3a(ctx)
    section_3b(ctx)
    section_3c(ctx)


SECTIONS: Mapping[str, Callable[[Context], None]] = {
    "0": config_tests,
    "1": section_1,
    "1w": section_1w,
    "2": section_2,
    "3": section_3,
    "4": section_4,
    "5": section_5,
    "6": section_6,
    "7": section_7,
    "8": section_8,
}


def main() -> int:
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--sections", default=",".join(SECTIONS))
    parser.add_argument("--nginx-image", default=NGINX_IMAGE)
    parser.add_argument("--python-image", default=PYTHON_IMAGE)
    parser.add_argument("--dind-image", default=DIND_IMAGE)
    parser.add_argument("--work", type=Path)
    parser.add_argument("--reuse", action="store_true", help="떠 있는 dind 컨테이너를 다시 쓴다")
    parser.add_argument("--keep", action="store_true", help="끝나도 dind 컨테이너를 지우지 않는다")
    parser.add_argument("--long", action="store_true", help="3c 를 TTL 이 지날 때까지(11분) 본다")
    args = parser.parse_args()
    chosen = [name for name in str(args.sections).split(",") if name in SECTIONS]
    work = Path(tempfile.mkdtemp(prefix="bridge-recover-", dir=args.work))
    _raw.append(work / "raw.log")
    ctx = Context(
        token=secrets.token_hex(3),
        rounds=Rounds(),
        nginx_image=str(args.nginx_image),
        python_image=str(args.python_image),
        dind_image=str(args.dind_image),
        long=bool(args.long),
    )
    print(f"원본 출력 {_raw[0]}, 회차 토큰 {ctx.token}, 호스트 {sys.platform}", flush=True)
    removed = True
    try:
        if not dind_up(ctx, reuse=bool(args.reuse)) or not load_images(ctx):
            return 2
        versions(ctx)
        for name in chosen:
            SECTIONS[name](ctx)
        with case(ctx, "끝 정리(안쪽 엔진에 이 프로젝트의 것이 남지 않았다)") as current:
            current.mark(measured=ctx.clean(), result=ctx.tainted or "남은 것 없음")
    finally:
        if not args.keep:
            removed = dind_down()
    if not args.keep:
        ctx.rounds.record(
            "끝 정리(dind 컨테이너와 볼륨을 지웠다)",
            measured=removed,
            result="지웠다" if removed else "지우지 못했다",
        )
    closing = [line for line in ctx.rounds.summary().splitlines() if not line.startswith("결과: ")]
    print("\n".join(closing), flush=True)
    return ctx.rounds.exit_code()


if __name__ == "__main__":
    sys.exit(main())
