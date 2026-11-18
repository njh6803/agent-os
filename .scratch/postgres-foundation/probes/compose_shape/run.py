"""단독 배포의 compose 에 PostgreSQL 과 한 번 도는 `migrate` 를 더한 모양을 실제 Docker 에서 잰다
(ADR 0066 결정 "표를 올리는 때", "비밀번호와 계정", "compose 배치"와 Consequences "재지 않은 것").
결정은 하지 않고 회차마다 본 것을 한 줄씩 낸다. 결과와 한계는 같은 폴더의 README.md 에 있다.

저장소 루트에서

    uv run python .scratch/postgres-foundation/probes/compose_shape/run.py [--sections 1,3,4,5,2]
        [--work <원본 출력을 둘 폴더>] [--image <digest 참조>] [--repeat <2번의 되풀이 수>]
        [--bash <4번의 절차를 칠 bash>] [--verbose]

필요한 것. Docker Engine 과 Compose 플러그인, 로컬에 이미 받은 PostgreSQL 이미지(IMAGE). 새 이미지를
받지 않는다(5마의 `docker compose pull` 은 레지스트리에 닿지만 이미 받은 digest 라 새 층이 없다).
`migrate` 와 `serve` 의 대역도 같은 이미지다(`psql`, `pg_isready`, `sh` 가 들어 있다).
4번의 절차는 docker 에 닿는 bash(윈도에서는 Git Bash)로 친다. 호스트 포트는 발행하지 않고, 접속
확인은 같은 네트워크의 다른 컨테이너에서 한다. 원본 출력은 `--work` 아래 실행마다 새 폴더의
`raw.log`(명령마다 종료 코드와 출력)와 `rounds.jsonl`(회차마다 본 것 전부)이다.

만들고 지우는 것. compose 프로젝트 이름은 모두 `pgf-shape-<무작위>-<회차>` 이고, 이 실행이 만든
프로젝트만 `docker compose -p <이름> down -v` 로 지운다. 따로 띄운 컨테이너에는 라벨
`pgf-shape=<무작위>` 를 붙이고 그 라벨의 것만 지운다. 넓은 정리 명령(`prune`)은 치지 않는다. 끝에
이 실행의 이름을 단 컨테이너·볼륨·네트워크가 남았는지 보고, 남았으면 측정 아님 회차로 센다. 작업
폴더(`--work`)에는 실행마다 새 하위 폴더를 만들 뿐 지우지 않는다.

항목(README 의 결과 번호와 같다)

1. PostgreSQL 컨테이너의 권한. 이름 있는 볼륨을 `/var/lib/postgresql` 에 붙이고, 조합마다 빈 볼륨의
   처음 띄우기와 데이터가 있는 볼륨의 다시 띄우기(컨테이너를 지우고 새로 만든다)를 본다. 뜨는 조합의
   표지는 다섯이다. 다른 컨테이너에서 TCP 로 친 `psql` 이 답한다. `docker inspect` 의 설정이 그
   조합의 것이다. PostgreSQL 프로세스의 uid 가 999 다. 읽기 전용이면 루트 파일시스템의 쓰기가
   `Read-only file system` 으로 거부된다(대조: 읽기 전용이 아닌 기준에서는 같은 쓰기가 된다). 다시
   띄운 회차는 컨테이너 id 가 바뀌었고 앞에서 넣은 줄이 남아 있다. 실패를 기대하는 조합의 표지는
   컨테이너가 끝난 것과 로그의 실패 문구다(문구가 다르면 측정이 아니다). 뜬 조합은 회차 끝에
   `docker compose stop` 으로 멈추고, 마지막 서버의 준비 줄 뒤에 `database system is shut down` 이
   찍혔는지(깨끗한 멈춤)와 다음 회차의 시작이 복구를 돌았는지를 본다.
2. 상태 확인. 빈 볼륨으로 띄우며 컨테이너 안의 유닉스 소켓 `pg_isready`, 127.0.0.1 의 `pg_isready`,
   다른 컨테이너의 TCP 접속(`select 1`)이 처음 0 을 내는 때를 0.1 초 간격의 표본으로 견준다(2가).
   표본 줄의 시각은 그 줄의 첫 확인을 치기 직전이다. 2가·2나는 진입 스크립트를 HOLD_SECONDS 늦게
   띄워 안쪽 표본이 서버보다 먼저 돌게 한다. 표지는 안쪽 표본의 첫 줄이 아직 답하지 않는 것, 바깥
   표본이 시작 전부터 돌았고 처음에는 실패한 것, 세 확인이 모두 한 번은 0 을 낸 것, 그리고 처음
   띄우기는 로그의 준비 줄이 둘(초기화용 임시 서버와 마지막 서버), 데이터가 있는 볼륨으로 다시
   띄운 대조(2나)는 하나인 것이다. 2다는 compose 의 healthcheck 꼴 넷을 늦추지 않고 띄워
   `health_status: healthy` 이벤트 뒤에 시작한 다른 컨테이너의 접속 가운데 실패한 것을 센다(표지에
   더해 healthy 뒤에 바깥 표본이 하나는 돌았어야 한다).
3. `depends_on` 과 한 번 도는 서비스. 같은 폴더의 `compose.yaml`(제안하는 모양에 대역을 끼운 것)을
   그대로 띄운다. 대역은 `probe_rows` 표에 누가(migrate, serve 의 시작·쥔 접속·새 접속) 어느 판으로
   언제 넣었는지 줄을 남기고, 그 줄의 수와 시각, `docker inspect` 의 시작·끝 시각, `docker events`
   로 차례를 본다.
4. 데이터가 있는 볼륨에서 비밀번호 바꾸기. 비밀번호를 바꿨다는 표지는 다른 컨테이너에서 새 값으로는
   들어가고 옛 값은 `password authentication failed` 로 막히는 것이다. 제안하는 절차는 같은 폴더의
   `change_password.sh` 를 bash 로 한 줄씩 친다.
5. compose 의 변수 치환과 `.env`. 치환 꼴마다 `docker compose config` 가 받는지 거부하는지(받는 꼴이
   양성 대조), `:?` 문구, 부모 셸 값과 `.env` 의 우선, 특수 글자가 든 값을 컨테이너가 실제로 받은
   환경 변수(`docker compose create` 뒤 `docker inspect`), 몇 값은 띄워서 데이터베이스의 비밀번호와
   migrate 대역의 `psql` 접속을 본다. 배포 안내 9절의 `pull` 과 `config --images` 가 비밀번호 칸이
   빈 `.env` 에서 멈추는지와 셸 값을 앞에 붙이면 지나는지도 본다(5마).

못 보는 것. 리눅스 서버의 Docker Engine(이 프로브는 Windows 의 Docker Desktop 이 WSL2 에 띄운 리눅스
엔진에서 돌았다), 호스트 폴더를 붙인 볼륨의 소유, rootless Docker 와 userns-remap, 데몬이나 서버를
다시 켠 뒤의 복귀, 실제 `agent-os migrate` 와 `serve`(대역은 `psql` 을 부르는 셸이다), SQLAlchemy 와
asyncpg 가 연결 문자열을 읽는 방식.
"""

from __future__ import annotations

import argparse
import calendar
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from functools import partial
from itertools import pairwise
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds, Slot  # noqa: E402

# 공식 이미지 postgres:18(18.7, Debian trixie). ADR 0066 결정 "이미지와 지원 범위"가 적은 digest 다.
IMAGE = "postgres@sha256:b9f6b8ff03b62f3cfd9d9ba3fe56226a9991c79d3fb46fd46536263bf02be553"
PREFIX = "pgf-shape"
ROLE = "agent_os"
DATABASE = "agent_os"
PGDATA = "/var/lib/postgresql/18/docker"
PASSWORD_VAR = "AGENT_OS_DATABASE_PASSWORD"
MISSING = f".env 에 {PASSWORD_VAR} 가 없다"
COMPOSE = ("docker", "compose", "--ansi", "never", "--progress", "plain")
# 부모 셸의 값이 `.env` 를 이기지 않게, compose 가 읽는 이름을 자식 환경에서 뺀다.
STRIPPED = ("AGENT_OS_", "COMPOSE_", "POSTGRES_", "PROBE_", "PG")

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

    @property
    def text(self) -> str:
        return self.out + "\n" + self.err


def decode(data: bytes) -> str:
    return data.decode("utf-8", errors="replace").replace("\r\n", "\n")


def child_env() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if not key.startswith(STRIPPED)}


@dataclass
class Lab:
    """실행 하나. 무작위 이름, 원본 출력을 두는 폴더, 회차, 이 실행이 만든 프로젝트."""

    token: str
    folder: Path
    image: str
    repeat: int
    verbose: bool = False
    bash: str = ""
    rounds: Rounds = field(default_factory=Rounds)
    projects: list[Project] = field(default_factory=list["Project"])
    serial: int = 0

    @property
    def label(self) -> str:
        return f"{PREFIX}={self.token}"

    def raw(self, title: str, text: str) -> None:
        with (self.folder / "raw.log").open("a", encoding="utf-8") as out:
            out.write(f"\n===== {time.strftime('%H:%M:%S')} {title}\n{text}\n")

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | None = None,
        stdin: str | None = None,
        timeout: float = 120,
        env: Mapping[str, str] | None = None,
    ) -> Done:
        """명령 하나. 표준 입력은 바이트로 넘긴다(글 모드는 윈도에서 줄 끝을 바꾼다). 시간을 넘기면
        종료 코드 -1 이다. `env` 는 벗긴 자식 환경 위에 얹는 값이다."""
        try:
            completed = subprocess.run(
                list(argv),
                input=(stdin or "").encode("utf-8"),
                capture_output=True,
                timeout=timeout,
                cwd=cwd,
                env={**child_env(), **(env or {})},
            )
        except subprocess.TimeoutExpired:
            done = Done(-1, "", f"{timeout:.0f}초 안에 끝나지 않았다")
        else:
            done = Done(completed.returncode, decode(completed.stdout), decode(completed.stderr))
        self.raw(
            " ".join(argv), f"exit={done.code}\n--- stdout\n{done.out}\n--- stderr\n{done.err}"
        )
        return done

    def docker(self, *args: str, stdin: str | None = None, timeout: float = 120) -> Done:
        return self.run(["docker", *args], stdin=stdin, timeout=timeout)

    def project(self, key: str) -> Project:
        made = Project(self, f"{PREFIX}-{self.token}-{key}", self.folder / key)
        made.folder.mkdir(parents=True, exist_ok=False)
        self.projects.append(made)
        return made

    def note(self, slot: Slot, *, measured: bool, result: str, detail: Mapping[str, Json]) -> None:
        """회차의 표지와 결과를 적는다. 화면에는 한 줄을, `rounds.jsonl` 에는 본 것 전부를
        남긴다."""
        slot.mark(measured=measured, result=result)
        line = json.dumps(
            {"round": slot.label, "measured": measured, "result": result, "detail": dict(detail)},
            ensure_ascii=False,
        )
        with (self.folder / "rounds.jsonl").open("a", encoding="utf-8") as out:
            out.write(line + "\n")
        print(f"[{'측정' if measured else '측정 아님'}] {slot.label} → {result}", flush=True)
        if self.verbose or not measured:
            print(f"    {json.dumps(dict(detail), ensure_ascii=False)}", flush=True)


@dataclass
class Project:
    """compose 프로젝트 하나. 폴더에 `compose.yaml` 과 `.env` 를 두고 그 폴더에서 compose 를
    친다."""

    lab: Lab
    name: str
    folder: Path

    def write(self, name: str, text: str) -> None:
        (self.folder / name).write_bytes(text.encode("utf-8"))

    def write_env(self, values: Mapping[str, str]) -> None:
        """`.env` 를 줄마다 `이름=값` 으로 쓴다. 값은 글자 그대로 넣는다(따옴표를 붙이지 않는다)."""
        self.write(".env", "".join(f"{key}={value}\n" for key, value in values.items()))

    def compose(
        self,
        *args: str,
        stdin: str | None = None,
        timeout: float = 180,
        env: Mapping[str, str] | None = None,
    ) -> Done:
        argv = [*COMPOSE, "-p", self.name, *args]
        return self.lab.run(argv, cwd=self.folder, stdin=stdin, timeout=timeout, env=env)

    def box(self, service: str) -> str:
        return f"{self.name}-{service}-1"

    @property
    def network(self) -> str:
        return f"{self.name}_default"

    def exec(self, service: str, *argv: str, stdin: str | None = None, timeout: float = 60) -> Done:
        flags = ["-i"] if stdin is not None else []
        return self.lab.docker(
            "exec", *flags, self.box(service), *argv, stdin=stdin, timeout=timeout
        )

    def inspect(self, service: str) -> Json:
        done = self.lab.docker("inspect", self.box(service))
        return dig(parse(done.out), 0) if done.code == 0 else None

    def client(self, *argv: str, env: Mapping[str, str] | None = None, timeout: float = 60) -> Done:
        """같은 네트워크의 다른 컨테이너에서 명령 하나를 돌리고 그 컨테이너를 지운다."""
        flags: list[str] = []
        for key, value in (env or {}).items():
            flags += ["-e", f"{key}={value}"]
        return self.lab.docker(
            *("run", "--rm", "--network", self.network, "--label", self.lab.label),
            *flags,
            *("--entrypoint", argv[0], self.lab.image),
            *argv[1:],
            timeout=timeout,
        )

    def psql_tcp(self, password: str, *sql: str, host: str = "postgres") -> Done:
        """다른 컨테이너에서 TCP 로 접속해 SQL 을 차례로 친다. 출력은 값만이다(`-qtA`)."""
        commands: list[str] = []
        for statement in sql:
            commands += ["-c", statement]
        return self.client(
            *("psql", "-h", host, "-U", ROLE, "-d", DATABASE, "-v", "ON_ERROR_STOP=1", "-qtA"),
            *commands,
            env={"PGPASSWORD": password, "PGCONNECT_TIMEOUT": "5"},
        )

    def psql_local(self, *sql: str, timeout: float = 60) -> Done:
        """PostgreSQL 컨테이너 안에서 유닉스 소켓으로 접속해 SQL 을 친다(비밀번호를 주지 않는다)."""
        commands: list[str] = []
        for statement in sql:
            commands += ["-c", statement]
        return self.exec(
            *("postgres", "psql", "-U", ROLE, "-d", DATABASE, "-v", "ON_ERROR_STOP=1", "-qtA"),
            *commands,
            timeout=timeout,
        )

    def logs(self, service: str, tail: int = 200) -> str:
        return self.lab.docker("logs", "--tail", str(tail), self.box(service)).text

    def down(self, *, volumes: bool) -> Done:
        extra = ["-v"] if volumes else []
        return self.compose("down", *extra, "--remove-orphans", "--timeout", "5", timeout=120)


def last_lines(text: str, count: int = 3) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " / ".join(lines[-count:])


@dataclass(frozen=True)
class Settled:
    state: str  # ready, exited, timeout, missing
    exit_code: int
    seconds: float


def settle(project: Project, service: str = "postgres", limit: float = 90) -> Settled:
    """컨테이너가 TCP 접속을 받거나(안에서 127.0.0.1 의 `pg_isready` 가 0) 끝날 때까지 기다린다.
    초기화 중의 임시 서버는 TCP 를 열지 않으므로, 0 은 마지막 서버가 떴다는 뜻이다."""
    started = time.monotonic()
    while (elapsed := time.monotonic() - started) < limit:
        state = dig(project.inspect(service), "State")
        status = as_text(dig(state, "Status"))
        if not status:
            return Settled("missing", -1, elapsed)
        if status == "exited":
            code = dig(state, "ExitCode")
            return Settled("exited", code if isinstance(code, int) else -1, elapsed)
        ready = project.exec(
            service, "pg_isready", "-h", "127.0.0.1", "-U", ROLE, "-d", DATABASE, timeout=15
        )
        if ready.code == 0:
            return Settled("ready", 0, time.monotonic() - started)
        time.sleep(0.2)
    return Settled("timeout", -1, limit)


# ---------------------------------------------------------------------------------------------
# 1. PostgreSQL 컨테이너의 권한
# ---------------------------------------------------------------------------------------------

HARDENED: Mapping[str, Json] = {
    "read_only": True,
    "cap_drop": ["ALL"],
    "security_opt": ["no-new-privileges:true"],
}
SOCKET_TMPFS = "/var/run/postgresql"
MINIMAL_CAPS = ("CHOWN", "DAC_OVERRIDE", "SETGID", "SETUID")
LOCK_FAILURE = (
    'could not create lock file "/var/run/postgresql/.s.PGSQL.5432.lock": Read-only file system'
)
MKDIR_FAILURE = "mkdir: cannot create directory ‘/var/lib/postgresql/18’: Permission denied"
FIND_FAILURE = "find: ‘/var/lib/postgresql/18/docker’: Permission denied"
CHOWN_DATA_FAILURE = (
    "chown: changing ownership of '/var/lib/postgresql/18/docker': Operation not permitted"
)
CHOWN_SOCKET_FAILURE = "chown: changing ownership of '/var/run/postgresql': Operation not permitted"
GOSU_FAILURE = "error: failed switching to 'postgres': operation not permitted"
# PostgreSQL 로그의 줄. 준비 줄은 처음 띄울 때 둘(초기화용 임시 서버와 마지막 서버)이다. 그래서
# 멈춤은 마지막 준비 줄 뒤의 줄로만 본다(임시 서버를 멈출 때도 같은 멈춤 줄이 찍힌다).
READY_LINE = "database system is ready to accept connections"
SHUT_DOWN_LINE = "database system is shut down"
RECOVERY_LINE = "database system was not properly shut down; automatic recovery in progress"
TINI_FAILURE = "[FATAL tini (1)] Unexpected error when forwarding signal"

INSIDE = r"""
echo "comm1=$(cat /proc/1/comm)"
grep -E '^(Uid|CapEff|CapBnd|NoNewPrivs):' /proc/1/status | sed 's/^/status1 /'
for p in /proc/[0-9]*; do
  [ "$(cat "$p/comm" 2>/dev/null)" = postgres ] && grep '^Uid:' "$p/status" | sed 's/^/postgres /'
done | sort -u
stat -c 'stat %n %u:%g %a' /var/lib/postgresql /var/lib/postgresql/18 \
  /var/lib/postgresql/18/docker /var/run/postgresql
touch /probe-write
echo "touch=$?"
"""


def hardened(**extra: Json) -> dict[str, Json]:
    return {**HARDENED, "tmpfs": [SOCKET_TMPFS], **extra}


def with_caps(*caps: str, **extra: Json) -> dict[str, Json]:
    return hardened(cap_add=list(caps), **extra)


def postgres_only(service: Mapping[str, Json]) -> str:
    """PostgreSQL 서비스 하나만 든 compose 파일. JSON 은 YAML 이라 compose 가 그대로 읽는다."""
    base: dict[str, Json] = {
        "image": IMAGE,
        "environment": {
            "POSTGRES_USER": ROLE,
            "POSTGRES_DB": DATABASE,
            "POSTGRES_PASSWORD": f"${{{PASSWORD_VAR}:?{MISSING}}}",
        },
        "volumes": ["pgdata:/var/lib/postgresql"],
    }
    document: dict[str, Json] = {
        "services": {"postgres": {**base, **service}},
        "volumes": {"pgdata": {}},
        "networks": {"default": {"enable_ipv6": False}},
    }
    return json.dumps(document, ensure_ascii=False, indent=2) + "\n"


def expected_host_config(service: Mapping[str, Json]) -> dict[str, Json]:
    names = sorted(name for name in as_list(service.get("cap_add")) if isinstance(name, str))
    caps: list[Json] = [f"CAP_{name}" for name in names]
    return {
        "ReadonlyRootfs": service.get("read_only") is True,
        "CapDrop": service.get("cap_drop"),
        "CapAdd": caps or None,
        "User": as_text(service.get("user")),
        "SecurityOpt": service.get("security_opt"),
        "Init": service.get("init"),
    }


def actual_host_config(info: Json) -> dict[str, Json]:
    names = sorted(
        name for name in as_list(dig(info, "HostConfig", "CapAdd")) if isinstance(name, str)
    )
    caps: list[Json] = [name for name in names]
    return {
        "ReadonlyRootfs": dig(info, "HostConfig", "ReadonlyRootfs"),
        "CapDrop": dig(info, "HostConfig", "CapDrop"),
        "CapAdd": caps or None,
        "User": as_text(dig(info, "Config", "User")),
        "SecurityOpt": dig(info, "HostConfig", "SecurityOpt"),
        "Init": dig(info, "HostConfig", "Init"),
    }


def read_inside(text: str) -> dict[str, Json]:
    """컨테이너 안에서 돌린 INSIDE 의 출력을 읽는다."""
    seen: dict[str, Json] = {"postgres_uids": [], "stat": {}}
    uids: list[Json] = []
    stats: dict[str, Json] = {}
    for line in text.splitlines():
        if match := re.fullmatch(r"comm1=(\S+)", line):
            seen["pid1_comm"] = match[1]
        elif match := re.fullmatch(r"status1 (\w+):\s+(\S+).*", line):
            seen[f"pid1_{match[1]}"] = match[2]
        elif match := re.fullmatch(r"postgres Uid:\s+(\d+)\s.*", line):
            uids.append(match[1])
        elif match := re.fullmatch(r"stat (\S+) (\S+) (\S+)", line):
            stats[match[1]] = f"{match[2]} {match[3]}"
        elif match := re.fullmatch(r"touch=(\d+)", line):
            seen["touch_exit"] = int(match[1])
    seen["postgres_uids"] = uids
    seen["stat"] = stats
    seen["touch_refused"] = "touch: cannot touch '/probe-write': Read-only file system" in text
    return seen


@dataclass(frozen=True)
class Step:
    """조합 하나를 한 번 띄우는 일. `fails` 가 있으면 그 문구로 끝나기를 기대한다."""

    label: str
    service: Mapping[str, Json]
    fails: str = ""


def start_step(lab: Lab, project: Project, step: Step, *, kept: str, previous_id: str) -> str:
    """회차 하나. 컨테이너를 (다시) 만들어 띄우고 표지를 본다. 돌려주는 것은 그 컨테이너의 id 다.
    `previous_id` 가 비지 않았으면 데이터가 있는 볼륨으로 다시 띄우는 회차다."""
    password = project.name
    with lab.rounds.round(step.label) as slot:
        project.write("compose.yaml", postgres_only(step.service))
        project.write_env({PASSWORD_VAR: password})
        up = project.compose("up", "-d")
        settled = settle(project)
        info = project.inspect("postgres")
        box_id = as_text(dig(info, "Id"))
        config = actual_host_config(info)
        expected = expected_host_config(step.service)
        detail: dict[str, Json] = {
            "up_exit": up.code,
            "state": settled.state,
            "exit_code": settled.exit_code,
            "seconds": round(settled.seconds, 1),
            "config": config,
        }
        shaped = up.code == 0 and config == expected and bool(box_id) and box_id != previous_id
        if not shaped:
            detail["why"] = "컨테이너가 기대한 설정으로 새로 만들어지지 않았다"
            lab.note(slot, measured=False, result="조합이 서지 않았다", detail=detail)
            return box_id
        logs = project.logs("postgres")
        if settled.state != "ready":
            detail["log_tail"] = last_lines(logs, 4)
            phrase = step.fails if step.fails and step.fails in logs else ""
            detail["phrase"] = phrase
            measured = settled.state == "exited" and bool(phrase)
            result = f"끝남({settled.exit_code}): {phrase}" if measured else "까닭 모를 실패"
            lab.note(slot, measured=measured, result=result, detail=detail)
            return box_id
        inside = read_inside(project.exec("postgres", "sh", "-c", INSIDE).text)
        detail["inside"] = inside
        if previous_id:
            query = project.psql_tcp(password, "select note from kept")
            answered = query.code == 0 and query.out.strip() == kept
        else:
            query = project.psql_tcp(
                password,
                "create table kept (note text)",
                f"insert into kept values ('{kept}')",
                "select 1",
            )
            answered = query.code == 0 and query.out.strip() == "1"
        detail["tcp_psql"] = {
            "exit": query.code,
            "out": query.out.strip(),
            "err": query.err.strip(),
        }
        read_only = expected["ReadonlyRootfs"] is True
        write_as_expected = (
            inside.get("touch_refused") is True
            if read_only
            else inside.get("touch_exit") == 0 and inside.get("touch_refused") is False
        )
        measured = answered and write_as_expected and inside.get("postgres_uids") == ["999"]
        if step.fails:
            detail["why"] = "실패를 기대했는데 떴다"
        if previous_id:
            # 앞 회차의 멈춤이 깨끗하지 않았으면 이번 시작이 복구를 돈다.
            detail["recovered_on_start"] = RECOVERY_LINE in logs
        stopped, stop_detail = stop_and_judge(project)
        detail["stop"] = stop_detail
        clean = stop_detail.get("clean") is True
        result = (
            f"뜸(PID 1 은 {inside.get('pid1_comm')}, uid {inside.get('pid1_Uid')}), "
            f"멈춤은 {'깨끗함' if clean else '깨끗하지 않음'}"
            f"{'(tini 가 신호를 넘기지 못함)' if stop_detail.get('tini_failed') else ''}"
            f"{', 시작할 때 복구를 돌았다' if detail.get('recovered_on_start') else ''}"
        )
        lab.note(slot, measured=measured and stopped, result=result, detail=detail)
        return box_id


def stop_and_judge(project: Project) -> tuple[bool, dict[str, Json]]:
    """`docker compose stop` 으로 멈추고 멈춤이 깨끗했는지 본다. 표지는 멈춘 뒤 컨테이너가 돌지 않고
    로그에 마지막 서버의 준비 줄이 있는 것이다(그 뒤의 줄로 판정한다). 깨끗한 멈춤은 그 뒤에
    `database system is shut down` 이 찍힌 것이다."""
    began = time.monotonic()
    project.compose("stop", "--timeout", "10", "postgres", timeout=60)
    seconds = round(time.monotonic() - began, 1)
    info = project.inspect("postgres")
    lines = project.logs("postgres", 400).splitlines()
    last_ready = max((index for index, line in enumerate(lines) if READY_LINE in line), default=-1)
    after = [line.strip() for line in lines[last_ready + 1 :] if line.strip()]
    tail: list[Json] = [*after[-3:]]
    stopped = dig(info, "State", "Running") is False and last_ready >= 0
    return stopped, {
        "seconds": seconds,
        "exit_code": dig(info, "State", "ExitCode"),
        "clean": any(SHUT_DOWN_LINE in line for line in after),
        "tini_failed": any(TINI_FAILURE in line for line in after),
        "after_ready": tail,
    }


def run_pair(
    lab: Lab, key: str, first: Step, second: Step | None, *, seed: Mapping[str, Json] | None = None
) -> None:
    """프로젝트 하나에서 처음 띄우기와 다시 띄우기를 잇는다. `seed` 가 있으면 그 설정으로 먼저
    데이터를 만든 뒤(회차로 세지 않는다) `first` 를 데이터가 있는 볼륨에서 띄운다."""
    project = lab.project(key)
    kept = f"kept-{secrets.token_hex(4)}"
    try:
        previous = ""
        if seed is not None:
            project.write("compose.yaml", postgres_only(seed))
            project.write_env({PASSWORD_VAR: project.name})
            project.compose("up", "-d")
            seeded = settle(project).state == "ready"
            made = project.psql_local(
                "create table kept (note text)", f"insert into kept values ('{kept}')"
            )
            previous = as_text(dig(project.inspect("postgres"), "Id"))
            project.down(volumes=False)
            if not (seeded and made.code == 0 and previous):
                lab.rounds.record(
                    first.label, measured=False, result="데이터가 든 볼륨을 만들지 못했다"
                )
                return
        previous = start_step(lab, project, first, kept=kept, previous_id=previous)
        if second is not None:
            project.down(volumes=False)
            start_step(lab, project, second, kept=kept, previous_id=previous)
    finally:
        project.down(volumes=True)


def section_permissions(lab: Lab) -> None:
    plain: dict[str, Json] = {}
    as_postgres = hardened(user="999:999")
    minimal = with_caps(*MINIMAL_CAPS)
    pairs: list[tuple[str, str, Mapping[str, Json]]] = [
        ("s1-a", "1가 기준(좁히지 않음)", plain),
        ("s1-b", "1나 user 999 + 읽기 전용 + 권한 모두 빼기", as_postgres),
        (
            "s1-b2",
            "1나 같은 조합에 소켓 폴더 tmpfs 를 uid=999,mode=0700 으로",
            {**as_postgres, "tmpfs": [f"{SOCKET_TMPFS}:uid=999,gid=999,mode=0700"]},
        ),
        ("s1-c", "1다 root 로 떠서 gosu + 최소 권한 넷", minimal),
        ("s1-bi", "1나 + init", {**as_postgres, "init": True}),
        ("s1-ci", "1다 + init", {**minimal, "init": True}),
        # 갈래: 1다 + init 의 멈춤이 깨끗하지 않은 까닭이 root 인 tini 에게 남의 프로세스(uid 999)에
        # 신호를 보낼 권한(KILL)이 없어서인지. 맞으면 KILL 을 더한 이 조합은 깨끗이 멈춘다.
        ("s1-ck", "1다 + init + KILL", {**with_caps(*MINIMAL_CAPS, "KILL"), "init": True}),
    ]
    for key, title, service in pairs:
        run_pair(lab, key, Step(f"{title} / 처음", service), Step(f"{title} / 다시", service))
    # 기준(root 로 떠서 진입 스크립트가 소유를 맞춘 것)으로 만든 볼륨을 1나로 다시 띄우면.
    run_pair(lab, "s1-ab", Step("1나 / 1가로 만든 볼륨에서 다시", as_postgres), None, seed=plain)

    # 1나에서 소켓 폴더의 tmpfs 를 빼면: 처음 띄우기가 임시 서버에서 끝난다.
    no_tmpfs: dict[str, Json] = {**HARDENED, "user": "999:999"}
    run_pair(lab, "s1-bx", Step("1나 tmpfs 없음 / 처음", no_tmpfs, LOCK_FAILURE), None)
    run_pair(
        lab, "s1-bxr", Step("1나 tmpfs 없음 / 다시", no_tmpfs, LOCK_FAILURE), None, seed=as_postgres
    )

    # 1다에서 권한을 하나씩 뺀다. 빈 볼륨의 처음 띄우기와, 최소 집합으로 만든 볼륨의 다시 띄우기.
    first_failures = {
        "CHOWN": CHOWN_DATA_FAILURE,
        "DAC_OVERRIDE": MKDIR_FAILURE,
        "SETGID": GOSU_FAILURE,
        "SETUID": GOSU_FAILURE,
    }
    again_failures = {**first_failures, "CHOWN": CHOWN_SOCKET_FAILURE, "DAC_OVERRIDE": FIND_FAILURE}
    for cap in MINIMAL_CAPS:
        rest = with_caps(*(name for name in MINIMAL_CAPS if name != cap))
        key = cap.lower().replace("_", "")
        run_pair(
            lab, f"s1-c-{key}", Step(f"1다 {cap} 빼기 / 처음", rest, first_failures[cap]), None
        )
        run_pair(
            lab,
            f"s1-c-{key}-r",
            Step(f"1다 {cap} 빼기 / 다시", rest, again_failures[cap]),
            None,
            seed=minimal,
        )
    swapped = with_caps("CHOWN", "DAC_READ_SEARCH", "SETGID", "SETUID")
    title = "1다 DAC_OVERRIDE 를 DAC_READ_SEARCH 로 바꿈"
    run_pair(lab, "s1-c-rs", Step(f"{title} / 처음", swapped, MKDIR_FAILURE), None)
    run_pair(lab, "s1-c-rs-r", Step(f"{title} / 다시", swapped), None, seed=minimal)

    # 1라: 권한만 모두 뺀 root. 실패를 기대하는 대조다.
    bare: dict[str, Json] = {"cap_drop": ["ALL"]}
    run_pair(lab, "s1-d", Step("1라 cap_drop ALL 만 / 처음", bare, MKDIR_FAILURE), None)
    run_pair(
        lab, "s1-d-r", Step("1라 cap_drop ALL 만 / 다시", bare, FIND_FAILURE), None, seed=plain
    )


# ---------------------------------------------------------------------------------------------
# 2~5번이 함께 쓰는 것: 제안하는 모양의 compose 파일, 컨테이너의 지금 모습, 이벤트, 줄 세기
# ---------------------------------------------------------------------------------------------

SERVICES = ("postgres", "migrate", "serve")


def stamp(text: str) -> float | None:
    """docker 가 찍는 시각(RFC 3339, 나노초까지)을 유닉스 초로 바꾼다. 빈 시각(0001년)은 None
    이다."""
    match = re.fullmatch(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d+))?Z", text)
    if match is None or text.startswith("0001-"):
        return None
    whole = calendar.timegm(time.strptime(match[1], "%Y-%m-%dT%H:%M:%S"))
    return whole + float(f"0.{match[2] or '0'}")


@dataclass(frozen=True)
class Box:
    """컨테이너 하나의 지금 모습(docker inspect)."""

    id: str
    status: str
    exit_code: int
    started: float | None
    finished: float | None
    restarts: int
    health: str
    env: Mapping[str, str]

    def brief(self) -> dict[str, Json]:
        return {
            "id": self.id[:12],
            "status": self.status,
            "exit_code": self.exit_code,
            "restarts": self.restarts,
            "health": self.health,
        }


def box(project: Project, service: str) -> Box | None:
    info = project.inspect(service)
    box_id = as_text(dig(info, "Id"))
    if not box_id:
        return None
    code = dig(info, "State", "ExitCode")
    restarts = dig(info, "RestartCount")
    env: dict[str, str] = {}
    for item in as_list(dig(info, "Config", "Env")):
        name, _, value = as_text(item).partition("=")
        env[name] = value
    return Box(
        id=box_id,
        status=as_text(dig(info, "State", "Status")),
        exit_code=code if isinstance(code, int) else -1,
        started=stamp(as_text(dig(info, "State", "StartedAt"))),
        finished=stamp(as_text(dig(info, "State", "FinishedAt"))),
        restarts=restarts if isinstance(restarts, int) else -1,
        health=as_text(dig(info, "State", "Health", "Status")),
        env=env,
    )


def boxes(project: Project) -> dict[str, Box | None]:
    return {service: box(project, service) for service in SERVICES}


def briefs(found: Mapping[str, Box | None]) -> dict[str, Json]:
    return {name: (one.brief() if one else None) for name, one in found.items()}


@dataclass(frozen=True)
class Event:
    at: float
    action: str
    service: str
    box: str


def daemon_now(lab: Lab) -> str:
    """Docker 데몬의 지금 시각. 이벤트를 자르는 경계로 쓴다(이 PC 의 시계와 다를 수 있다)."""
    return lab.docker("info", "--format", "{{.SystemTime}}").out.strip()


def events(lab: Lab, project: Project, since: str) -> list[Event]:
    """`since` 부터 지금까지 이 프로젝트의 컨테이너에 난 일."""
    done = lab.docker(
        *("events", "--since", since, "--until", daemon_now(lab)),
        *("--filter", "type=container"),
        *("--filter", f"label=com.docker.compose.project={project.name}"),
        *("--format", "{{json .}}"),
        timeout=60,
    )
    found: list[Event] = []
    for line in done.out.splitlines():
        item = parse(line)
        nanos = dig(item, "timeNano")
        action = as_text(dig(item, "Action"))
        if not isinstance(nanos, int) or not action:
            continue
        attributes = dig(item, "Actor", "Attributes")
        service = as_text(dig(attributes, "com.docker.compose.service"))
        found.append(Event(nanos / 1e9, action, service, as_text(dig(item, "Actor", "ID"))))
    return sorted(found, key=lambda event: event.at)


def first_event(
    found: Sequence[Event], action: str, *, service: str = "", box_id: str = ""
) -> float | None:
    for event in found:
        if event.action != action:
            continue
        if (service and event.service != service) or (box_id and event.box != box_id):
            continue
        return event.at
    return None


def stack(lab: Lab, key: str, env: Mapping[str, str], *, text: str = "") -> Project:
    """같은 폴더의 `compose.yaml`(제안하는 모양에 대역을 끼운 것)을 그대로 쓰는 프로젝트."""
    project = lab.project(key)
    project.write("compose.yaml", text or (HERE / "compose.yaml").read_text(encoding="utf-8"))
    project.write_env(env)
    return project


def row_counts(project: Project) -> dict[str, int]:
    """대역이 넣은 줄의 수. 열쇠는 `누가/판` 이다. 표가 없으면 빈 사전이다."""
    done = project.psql_local("select who || '/' || version, count(*) from probe_rows group by 1")
    counts: dict[str, int] = {}
    for line in done.out.splitlines():
        name, _, count = line.partition("|")
        if count.isdigit():
            counts[name] = int(count)
    return counts


def row_time(project: Project, pick: str, where: str) -> float | None:
    """조건에 맞는 줄의 가장 이른(min) 또는 늦은(max) 시각. 데이터베이스의 시계다."""
    done = project.psql_local(
        f"select extract(epoch from {pick}(at)) from probe_rows where {where}"
    )
    try:
        return float(done.out.strip())
    except ValueError:
        return None


def wait_until(check: Callable[[], bool], limit: float, step: float = 0.5) -> bool:
    deadline = time.monotonic() + limit
    while time.monotonic() < deadline:
        if check():
            return True
        time.sleep(step)
    return check()


def migrate_finished(project: Project) -> bool:
    migrate = box(project, "migrate")
    return migrate is not None and migrate.status == "exited"


def postgres_healthy(project: Project) -> bool:
    postgres = box(project, "postgres")
    return postgres is not None and postgres.health == "healthy"


def serve_healthy(project: Project) -> bool:
    serve = box(project, "serve")
    return serve is not None and serve.status == "running" and serve.health == "healthy"


def progress(text: str, *words: str) -> list[Json]:
    """compose 의 진행 줄 가운데 낱말이 든 줄. 이어서 두 번 찍힌 같은 줄은 한 번만 든다."""
    kept: list[Json] = []
    for line in text.splitlines():
        line = line.strip()
        if line and any(word in line for word in words) and (not kept or kept[-1] != line):
            kept.append(line)
    return kept


def recreated(old: Box | None, new: Box | None) -> str:
    """앞뒤 컨테이너의 id 가 다르면 다시 만들어진 것이다."""
    return "다시 만들어짐" if old and new and old.id != new.id else "그대로"


def arrow(before: Mapping[str, int], after: Mapping[str, int], key: str) -> str:
    """같은 열쇠의 줄 수가 앞에서 뒤로 어떻게 바뀌었는지(`3→5`)."""
    return f"{before.get(key)}→{after.get(key)}"


def ascending(*values: float | None) -> bool:
    """모두 아는 시각이고 적힌 차례대로 늦어지는가."""
    known = [value for value in values if value is not None]
    return len(known) == len(values) and known == sorted(known)


def offsets(base: float | None, **times: float | None) -> dict[str, Json]:
    """기준 시각에서 잰 초. 모르는 시각은 None 이다."""
    return {
        name: (round(value - base, 2) if base is not None and value is not None else None)
        for name, value in times.items()
    }


# ---------------------------------------------------------------------------------------------
# 3. depends_on 과 한 번 도는 서비스
# ---------------------------------------------------------------------------------------------

UP_FORMS: tuple[tuple[str, ...], ...] = (
    ("up", "-d"),
    ("up", "-d", "--wait"),
    # deploy/standalone/README.md 4절이 치라고 적은 꼴
    ("up", "-d", "--wait", "--wait-timeout", "600"),
    # web/packages/e2e-standalone/e2e/stack.ts 가 치는 꼴
    ("up", "--detach", "--wait", "--wait-timeout", "600"),
)
MIGRATE_FAILED = 'service "migrate" didn\'t complete successfully: exit 1'
MIGRATE_DONE_V1 = "migrate 대역: 판 v1 을 올렸다"


def fresh_up(lab: Lab, project: Project, form: Sequence[str]) -> tuple[str, bool]:
    """빈 볼륨에서 `up` 한 꼴을 친다. 돌려주는 것은 이벤트를 자를 시각과 serve 가 떴는지다."""
    since = daemon_now(lab)
    with lab.rounds.round(f"3가 {' '.join(form)}") as slot:
        started = time.monotonic()
        up = project.compose(*form, timeout=660)
        seconds = time.monotonic() - started
        seen = boxes(project)
        counts = row_counts(project)
        migrate, serve = seen["migrate"], seen["serve"]
        # 재려는 상황: `up` 이 돌아왔을 때 migrate 가 한 번 돌고 0 으로 끝나 있다.
        finished = (
            migrate is not None
            and migrate.status == "exited"
            and migrate.exit_code == 0
            and counts.get("migrate/v1") == 1
        )
        healthy = wait_until(lambda: serve_healthy(project), 90)
        lab.note(
            slot,
            measured=finished and serve is not None and healthy,
            result=(
                f"종료 {up.code}, 돌아온 때 migrate 는 Exited (0), serve 는 "
                f"{serve.status if serve else '없음'}/{serve.health if serve else ''}"
            ),
            detail={
                "seconds": round(seconds, 1),
                "at_return": briefs(seen),
                "progress": progress(up.err, "migrate", "serve"),
                "stdout": up.out.strip(),
            },
        )
        return since, healthy
    return since, False


def start_order(lab: Lab, project: Project, since: str) -> None:
    with lab.rounds.round("3나 시작 차례") as slot:
        seen = boxes(project)
        found = events(lab, project, since)
        postgres, migrate, serve = seen["postgres"], seen["migrate"], seen["serve"]
        healthy = first_event(found, "health_status: healthy", service="postgres")
        times = {
            "postgres_healthy": healthy,
            "migrate_started": migrate.started if migrate else None,
            "migrate_finished": migrate.finished if migrate else None,
            "serve_started": serve.started if serve else None,
        }
        base = postgres.started if postgres else None
        known = all(value is not None for value in times.values())
        lab.note(
            slot,
            measured=base is not None and known,
            result=(
                "postgres healthy → migrate 시작 → migrate 끝 → serve 시작"
                if ascending(base, *times.values())
                else "차례가 다르다"
            ),
            detail={"seconds_after_postgres_started": offsets(base, **times)},
        )


def listing(lab: Lab, project: Project) -> None:
    with lab.rounds.round("3바 ps 와 logs") as slot:
        running = project.compose("ps")
        everything = project.compose("ps", "-a")
        logs = project.compose("logs", "migrate")
        name = project.box("migrate")
        line = next((row for row in everything.out.splitlines() if name in row), "")
        lab.note(
            slot,
            # 표지: 끝난 migrate 가 `ps -a` 에 있고, `ps` 가 도는 serve 를 낸다(목록이 비지 않았다).
            measured=bool(line) and project.box("serve") in running.out,
            result=(
                f"ps 에 migrate {'있음' if name in running.out else '없음'}, "
                f"ps -a 에 {'Exited (0)' if 'Exited (0)' in line else '다른 상태'}, "
                f"logs 에 대역의 줄 {'있음' if MIGRATE_DONE_V1 in logs.out else '없음'}"
            ),
            detail={"ps_a_line": line, "logs": logs.out.strip()},
        )


def up_again(lab: Lab, project: Project, form: Sequence[str]) -> None:
    with lab.rounds.round(f"3라 모두 뜬 채 다시 {' '.join(form)}") as slot:
        before, rows_before = boxes(project), row_counts(project)
        settled = serve_healthy(project) and before["migrate"] is not None
        up = project.compose(*form, timeout=300)
        wait_until(
            lambda: row_counts(project).get("migrate/v1", 0) > rows_before.get("migrate/v1", 0), 15
        )
        after, rows_after = boxes(project), row_counts(project)
        old_migrate, new_migrate = before["migrate"], after["migrate"]
        old_serve, new_serve = before["serve"], after["serve"]
        same_migrate = (
            old_migrate is not None and new_migrate is not None and old_migrate.id == new_migrate.id
        )
        if old_serve is None or new_serve is None:
            serve_change = "serve 없음"
        elif old_serve.id != new_serve.id:
            serve_change = "serve 다시 만들어짐"
        elif old_serve.started != new_serve.started:
            serve_change = "serve 다시 시작됨"
        else:
            serve_change = "serve 그대로"
        lab.note(
            slot,
            measured=settled and up.code == 0,
            result=(
                f"migrate 줄 {rows_before.get('migrate/v1')}→{rows_after.get('migrate/v1')}"
                f"({'같은 컨테이너' if same_migrate else '새 컨테이너'}), {serve_change}"
            ),
            detail={"up_exit": up.code, "progress": progress(up.err, "migrate", "serve")},
        )


def change_version(lab: Lab, project: Project, env: Mapping[str, str]) -> None:
    with lab.rounds.round("3마 판 바꾸기(환경 변수 하나를 바꾸고 up -d --wait)") as slot:
        before = boxes(project)
        since = daemon_now(lab)
        project.write_env({**env, "PROBE_VERSION": "v2"})
        up = project.compose("up", "-d", "--wait", timeout=300)
        after = boxes(project)
        found = events(lab, project, since)
        old_serve, new_serve = before["serve"], after["serve"]
        old_migrate, new_migrate = before["migrate"], after["migrate"]
        old_died = first_event(found, "die", box_id=old_serve.id if old_serve else "?")
        migrate_started = first_event(found, "start", box_id=new_migrate.id if new_migrate else "?")
        migrate_died = first_event(found, "die", box_id=new_migrate.id if new_migrate else "?")
        serve_started = first_event(found, "start", box_id=new_serve.id if new_serve else "?")
        last_old_row = row_time(project, "max", "version = 'v1' and who like 'serve-%'")
        new_migrate_row = row_time(project, "min", "version = 'v2' and who = 'migrate'")
        new_serve_row = row_time(project, "min", "version = 'v2' and who = 'serve-start'")
        replaced = (
            old_serve is not None
            and new_serve is not None
            and old_serve.id != new_serve.id
            and old_migrate is not None
            and new_migrate is not None
            and old_migrate.id != new_migrate.id
        )
        times = (old_died, migrate_started, migrate_died, serve_started)
        rows = (last_old_row, new_migrate_row, new_serve_row)
        known = all(value is not None for value in (*times, *rows))
        no_overlap = ascending(*times) and ascending(*rows)
        gap = (
            round(new_serve_row - last_old_row, 2)
            if new_serve_row is not None and last_old_row is not None
            else None
        )
        lab.note(
            slot,
            measured=up.code == 0 and replaced and known,
            result=(
                "옛 serve 멈춤 → 새 migrate 시작 → 새 migrate 끝 → 새 serve 시작(겹침 없음)"
                if no_overlap
                else "옛 serve 가 새 migrate 와 겹쳤거나 차례가 다르다"
            ),
            detail={
                "events_after_old_serve_died": offsets(
                    old_died,
                    migrate_started=migrate_started,
                    migrate_died=migrate_died,
                    serve_started=serve_started,
                ),
                "rows_after_last_old_serve_row": offsets(
                    last_old_row, new_migrate_row=new_migrate_row, new_serve_row=new_serve_row
                ),
                "seconds_without_serve_rows": gap,
                "progress": progress(up.err, "migrate", "serve"),
            },
        )


def down_and_up(lab: Lab, project: Project) -> None:
    with lab.rounds.round("3사 down(볼륨 남김) 뒤 up -d --wait") as slot:
        before, rows_before = boxes(project), row_counts(project)
        down = project.compose("down", "--timeout", "5")
        scope = f"label=com.docker.compose.project={project.name}"
        left = lab.docker("ps", "-aq", "--filter", scope).out.split()
        volumes = lab.docker("volume", "ls", "-q", "--filter", scope).out.split()
        up = project.compose("up", "-d", "--wait", timeout=300)
        after, rows_after = boxes(project), row_counts(project)
        old, new = before["postgres"], after["postgres"]
        recreated = old is not None and new is not None and old.id != new.id
        kept: dict[str, Json] = {
            name: f"{count}→{rows_after.get(name)}"
            for name, count in sorted(rows_before.items())
            if name.endswith("/v1")
        }
        survived = bool(kept) and all(
            rows_after.get(name) == count
            for name, count in rows_before.items()
            if name.endswith("/v1")
        )
        lab.note(
            slot,
            # 표지: down 뒤 컨테이너가 하나도 없었고, 볼륨은 남았고, PostgreSQL 컨테이너가 새것이다.
            measured=down.code == 0
            and not left
            and len(volumes) == 1
            and up.code == 0
            and recreated,
            result=(
                f"넣어 둔 줄이 {'남았다' if survived else '남지 않았다'}, migrate 줄(v2) "
                f"{rows_before.get('migrate/v2')}→{rows_after.get('migrate/v2')}"
            ),
            detail={"v1_rows": kept, "volumes_after_down": [*volumes]},
        )


def restart_all(lab: Lab, project: Project) -> None:
    with lab.rounds.round("3사 docker compose restart") as slot:
        before, rows_before = boxes(project), row_counts(project)
        since = daemon_now(lab)
        restart = project.compose("restart", timeout=120)
        recovered = wait_until(
            lambda: (
                serve_healthy(project)
                and row_counts(project).get("serve-new/v2", 0) > rows_before.get("serve-new/v2", 0)
            ),
            60,
        )
        # migrate 가 끝난 뒤에 종료 코드를 읽는다. 끝나기 전에 읽으면 도는 컨테이너의 0 을 읽는다
        # (이름 풀기를 몇 초 다시 해 serve 가 돌아온 뒤에 끝나기도 했다).
        finished = wait_until(lambda: migrate_finished(project), 60)
        after, rows_after = boxes(project), row_counts(project)
        found = events(lab, project, since)
        old, new = before["postgres"], after["postgres"]
        restarted = (
            old is not None and new is not None and old.id == new.id and old.started != new.started
        )
        migrate, serve = after["migrate"], after["serve"]
        old_migrate = before["migrate"]
        migrate_again = (
            old_migrate is not None
            and migrate is not None
            and old_migrate.started != migrate.started
        )
        starts = [f"{event.service}" for event in found if event.action == "start"]
        # 다시 켜기 전의 조회가 실패해 기준이 비면(`{}`) 남았다고도 남지 않았다고도 하지 않는다.
        survived = bool(rows_before) and all(
            rows_after.get(name, 0) >= count for name, count in rows_before.items()
        )
        lab.note(
            slot,
            measured=restart.code == 0
            and restarted
            and recovered
            and finished
            and bool(rows_before)
            and bool(rows_after),
            result=(
                f"넣어 둔 줄이 {'남았다' if survived else '남지 않았다'}, migrate 는 "
                f"{'다시 시작돼' if migrate_again else '다시 시작하지 않고'} "
                f"종료 {migrate.exit_code if migrate else '?'}(줄 {rows_before.get('migrate/v2')}→"
                f"{rows_after.get('migrate/v2')}), serve 의 RestartCount "
                f"{serve.restarts if serve else '?'}"
            ),
            detail={
                "start_events_in_order": list(starts),
                "progress": progress(restart.err, "Container"),
                # 같은 컨테이너의 앞선 실행이 남긴 줄을 빼고, 다시 시작한 뒤의 줄만.
                "migrate_log_since_restart": last_lines(
                    lab.docker("logs", "--since", since, project.box("migrate")).text, 3
                ),
            },
        )


def restart_postgres(lab: Lab, project: Project) -> None:
    with lab.rounds.round("3아 docker compose restart postgres") as slot:
        wait_until(lambda: serve_healthy(project), 30)
        before, rows_before = boxes(project), row_counts(project)
        restart = project.compose("restart", "postgres", timeout=120)
        recovered = wait_until(
            lambda: (
                row_counts(project).get("serve-new/v2", 0) > rows_before.get("serve-new/v2", 0) + 2
            ),
            60,
        )
        held_then = row_counts(project).get("serve-held/v2", 0)
        time.sleep(2)
        after, rows_after = boxes(project), row_counts(project)
        old, new = before["postgres"], after["postgres"]
        restarted = (
            old is not None and new is not None and old.id == new.id and old.started != new.started
        )
        old_serve, new_serve = before["serve"], after["serve"]
        untouched = (
            old_serve is not None
            and new_serve is not None
            and old_serve.id == new_serve.id
            and old_serve.started == new_serve.started
            and old_serve.restarts == new_serve.restarts
        )
        logs = project.logs("serve", 40)
        box_said = "그대로(id, 시작 시각, RestartCount 같음)" if untouched else "건드려졌다"
        held_said = "끊긴 채다" if rows_after.get("serve-held/v2", 0) == held_then else "이어졌다"
        lab.note(
            slot,
            measured=restart.code == 0 and restarted,
            result=(
                f"serve 컨테이너는 {box_said}, "
                f"새 접속은 {'돌아왔다' if recovered else '돌아오지 않았다'}, "
                f"쥐고 있던 접속은 {held_said}"
            ),
            detail={
                "serve_new_rows": arrow(rows_before, rows_after, "serve-new/v2"),
                "serve_held_rows": arrow(rows_before, rows_after, "serve-held/v2"),
                "serve_log": progress(logs, "FATAL", "error", "대역"),
            },
        )


def failing_migrate(lab: Lab, password: str) -> None:
    env = {PASSWORD_VAR: password, "PROBE_MIGRATE_EXIT": "1"}
    project = stack(lab, "s3f", env)
    try:
        for form in (("up", "-d"), ("up", "-d", "--wait")):
            with lab.rounds.round(f"3다 migrate 가 1 로 끝날 때 {' '.join(form)}") as slot:
                up = project.compose(*form, timeout=300)
                seen = boxes(project)
                migrate, serve = seen["migrate"], seen["serve"]
                # 표지: migrate 가 일부러 낸 1 로 끝났다(다른 까닭의 실패가 아니다).
                failed = (
                    migrate is not None
                    and migrate.exit_code == 1
                    and "migrate 대역: 일부러 1 로 끝난다" in project.logs("migrate", 5)
                )
                message = next(
                    (line.strip() for line in reversed(up.err.splitlines()) if line.strip()), ""
                )
                lab.note(
                    slot,
                    # 이번 `up` 이 실패를 직접 보았다는 표지도 본다. 앞 회차가 남긴 종료 1 과 로그
                    # 줄만으로는 이번 명령이 migrate 를 다시 돌렸는지 모른다.
                    measured=failed and serve is not None and MIGRATE_FAILED in up.err,
                    result=(
                        f"종료 {up.code}, 문구 {'있음' if MIGRATE_FAILED in up.err else '없음'}, "
                        f"serve 는 {serve.status if serve else '없음'}"
                        f"({'시작한 적 없음' if serve and serve.started is None else '시작했었다'})"
                    ),
                    detail={"last_line": message, "progress": progress(up.err, "migrate", "serve")},
                )
        with lab.rounds.round("3다 고친 뒤 up -d --wait") as slot:
            before = boxes(project)
            project.write_env({**env, "PROBE_MIGRATE_EXIT": "0"})
            up = project.compose("up", "-d", "--wait", timeout=300)
            after = boxes(project)
            old, new = before["migrate"], after["migrate"]
            which = "새 컨테이너" if old and new and old.id != new.id else "같은 컨테이너"
            lab.note(
                slot,
                # 고친 .env 가 컨테이너에 닿았고(`up` 이 시간 초과로 끊기지 않았다) 앞서 1 로 끝난
                # 컨테이너가 있었다.
                measured=old is not None
                and old.exit_code == 1
                and new is not None
                and up.code != -1
                and new.env.get("PROBE_MIGRATE_EXIT") == "0",
                result=(
                    f"종료 {up.code}, migrate 는 {which}로 종료 "
                    f"{new.exit_code if new else '?'}, serve 는 "
                    f"{after['serve'].health if after['serve'] else '없음'}"
                ),
                detail={"progress": progress(up.err, "migrate", "serve")},
            )
    finally:
        project.down(volumes=True)


def section_depends(lab: Lab) -> None:
    password = secrets.token_hex(32)
    env = {PASSWORD_VAR: password, "PROBE_VERSION": "v1"}
    project = stack(lab, "s3", env)
    try:
        since, healthy = "", False
        for index, form in enumerate(UP_FORMS):
            if index:
                project.down(volumes=True)
            since, healthy = fresh_up(lab, project, form)
        if not healthy:
            lab.rounds.record(
                "3나~3아", measured=False, result="배치가 뜨지 않아 뒤 회차를 돌지 못했다"
            )
            return
        start_order(lab, project, since)
        listing(lab, project)
        up_again(lab, project, ("up", "-d"))
        up_again(lab, project, ("up", "-d", "--wait"))
        change_version(lab, project, env)
        down_and_up(lab, project)
        restart_all(lab, project)
        restart_postgres(lab, project)
    finally:
        project.down(volumes=True)
    failing_migrate(lab, password)


# ---------------------------------------------------------------------------------------------
# 4. 데이터가 있는 볼륨에서 비밀번호 바꾸기
# ---------------------------------------------------------------------------------------------

AUTH_FAILED = 'FATAL:  password authentication failed for user "agent_os"'


def logs_in(project: Project, password: str) -> tuple[bool, str]:
    """다른 컨테이너에서 TCP 로 그 비밀번호의 접속이 되는가. 안 되면 psql 의 마지막 줄도 준다."""
    done = project.psql_tcp(password, "select 1")
    return done.code == 0 and done.out.strip() == "1", last_lines(done.err, 1)


def database_has(project: Project, *, accepts: str, refuses: str) -> bool:
    """데이터베이스의 비밀번호가 `accepts` 이고 `refuses` 가 아닌가(뒤의 것은 인증 실패
    문구까지)."""
    accepted, _ = logs_in(project, accepts)
    refused, message = logs_in(project, refuses)
    return accepted and not refused and AUTH_FAILED in message


def alter_role(project: Project, password: str) -> Done:
    """운영자가 칠 꼴 그대로. 컨테이너 안의 로컬 소켓이라 비밀번호를 묻지 않는다."""
    statement = f"ALTER ROLE {ROLE} PASSWORD '{password}'"
    return project.compose(
        "exec", "-T", "postgres", "psql", "-U", ROLE, "-d", DATABASE, "-c", statement
    )


def env_only(lab: Lab, project: Project, old: str, new: str) -> None:
    with lab.rounds.round("4가 .env 의 비밀번호만 바꾸고 up -d") as slot:
        before = boxes(project)
        project.write_env({PASSWORD_VAR: new})
        up = project.compose("up", "-d", timeout=300)
        after = boxes(project)
        old_box, new_box = before["postgres"], after["postgres"]
        migrate, serve = after["migrate"], after["serve"]
        # 재려는 상황: PostgreSQL 컨테이너는 새 값을 받았는데 데이터베이스의 비밀번호는 옛것
        # 그대로다.
        handed = new_box is not None and new_box.env.get("POSTGRES_PASSWORD") == new
        unchanged = database_has(project, accepts=old, refuses=new)
        migrate_log = project.logs("migrate", 5)
        message = next((line.strip() for line in reversed(up.err.splitlines()) if line.strip()), "")
        lab.note(
            slot,
            measured=handed and unchanged and migrate is not None and serve is not None,
            result=(
                f"up 종료 {up.code}, postgres 는 {recreated(old_box, new_box)}, "
                f"migrate 종료 {migrate.exit_code if migrate else '?'}"
                f"({'인증 실패 문구' if AUTH_FAILED in migrate_log else '다른 문구'}), "
                f"serve 는 {serve.status if serve else '없음'}"
            ),
            detail={
                "last_line": message,
                "migrate_log": last_lines(migrate_log, 1),
                "after": briefs(after),
            },
        )


def alter_then_up(lab: Lab, project: Project, old: str, new: str) -> None:
    with lab.rounds.round(
        "4나 로컬 소켓의 ALTER ROLE(비밀번호를 묻지 않는다) 뒤 up -d --wait"
    ) as slot:
        rows_before = row_counts(project)
        altered = alter_role(project, new)
        changed = database_has(project, accepts=new, refuses=old)
        up = project.compose("up", "-d", "--wait", timeout=300)
        after, rows_after = boxes(project), row_counts(project)
        migrate, serve = after["migrate"], after["serve"]
        survived = bool(rows_before) and all(
            rows_after.get(name, 0) >= count for name, count in rows_before.items()
        )
        lab.note(
            slot,
            measured=altered.code == 0 and altered.out.strip() == "ALTER ROLE" and changed,
            result=(
                f"ALTER ROLE 종료 {altered.code}, up 종료 {up.code}, migrate 종료 "
                f"{migrate.exit_code if migrate else '?'}, "
                f"serve 는 {serve.health if serve else '없음'}, "
                f"넣어 둔 줄은 {'남았다' if survived else '남지 않았다'}"
            ),
            detail={
                "rows": {
                    name: f"{count}→{rows_after.get(name)}" for name, count in rows_before.items()
                }
            },
        )


def alter_first(lab: Lab, project: Project, old: str, new: str) -> None:
    with lab.rounds.round("4다 ALTER ROLE 을 먼저(serve 가 떠 있는 채)") as slot:
        ready = wait_until(lambda: serve_healthy(project), 30)
        altered = alter_role(project, new)
        changed = database_has(project, accepts=new, refuses=old)
        rows_then = row_counts(project)
        time.sleep(4)
        rows_now = row_counts(project)
        logs = project.logs("serve", 6)
        held = rows_now.get("serve-held/v1", 0) - rows_then.get("serve-held/v1", 0)
        fresh = rows_now.get("serve-new/v1", 0) - rows_then.get("serve-new/v1", 0)
        lab.note(
            slot,
            measured=ready and altered.code == 0 and changed,
            result=(
                f"4초 동안 이미 맺은 접속의 줄 +{held}, 새 접속의 줄 +{fresh}"
                f"({'인증 실패 문구' if AUTH_FAILED in logs else '실패 문구 없음'})"
            ),
            detail={"serve_log": last_lines(logs, 2)},
        )
    with lab.rounds.round("4다 이어서 .env 를 고치고 up -d --wait") as slot:
        before, rows_before = boxes(project), row_counts(project)
        project.write_env({PASSWORD_VAR: new})
        up = project.compose("up", "-d", "--wait", timeout=300)
        after, rows_after = boxes(project), row_counts(project)
        old_box, new_box = before["postgres"], after["postgres"]
        migrate, serve = after["migrate"], after["serve"]
        survived = bool(rows_before) and all(
            rows_after.get(name, 0) >= count for name, count in rows_before.items()
        )
        lab.note(
            slot,
            measured=database_has(project, accepts=new, refuses=old) and new_box is not None,
            result=(
                f"up 종료 {up.code}, postgres 는 {recreated(old_box, new_box)}, "
                f"migrate 종료 {migrate.exit_code if migrate else '?'}, "
                f"serve 는 {serve.health if serve else '없음'}, "
                f"넣어 둔 줄은 {'남았다' if survived else '남지 않았다'}"
            ),
            detail={"progress": progress(up.err, "Recreate", "Error")},
        )


def auth_settings(lab: Lab, project: Project, used: Sequence[str]) -> None:
    with lab.rounds.round("4라 pg_hba.conf 와 password_encryption") as slot:
        script = "grep -v '^#' \"$PGDATA/pg_hba.conf\" | grep -v '^$'"
        hba = [
            line.split() for line in project.exec("postgres", "sh", "-c", script).out.splitlines()
        ]
        rules = {
            " ".join(fields[:-1]): fields[-1]
            for fields in hba
            if len(fields) >= 4 and fields[1] == "all"
        }
        shown = project.psql_local(
            "show password_encryption",
            f"select left(rolpassword, 13) from pg_authid where rolname = '{ROLE}'",
            "show log_statement",
            "show log_min_error_statement",
        ).out.split()
        lab.note(
            slot,
            measured=len(rules) >= 4 and len(shown) == 4,
            result=(
                f"로컬 소켓 {rules.get('local all all')}, "
                f"127.0.0.1 {rules.get('host all all 127.0.0.1/32')}, "
                f"그 밖의 TCP {rules.get('host all all all')}, "
                f"password_encryption {shown[0] if shown else '?'}"
            ),
            detail={"pg_hba": [" ".join(fields) for fields in hba], "show": list(shown)},
        )
    with lab.rounds.round("4라 ALTER ROLE 의 비밀번호가 PostgreSQL 로그에 남는가") as slot:
        marker = f"ctl-{secrets.token_hex(4)}"
        statement = f"ALTER ROLE {ROLE} PASSWORD '{marker}' BOGUS"
        failed = project.compose(
            "exec", "-T", "postgres", "psql", "-U", ROLE, "-d", DATABASE, "-c", statement
        )
        logs = project.compose("logs", "postgres").text
        leaked = [index for index, password in enumerate(used, start=1) if password in logs]
        # 대조: 실패한 문장은 로그에 글자 그대로 남는다(로그를 실제로 읽었고, 남을 때는 남는다).
        lab.note(
            slot,
            measured=failed.code != 0 and marker in logs,
            result=(
                f"성공한 ALTER ROLE 의 비밀번호 {len(used)}개 가운데 "
                f"로그에 남은 것 {len(leaked)}개, "
                "문법이 틀려 실패한 문장은 비밀번호째 남는다"
            ),
            detail={
                "failed_statement_log": next(
                    (line for line in logs.splitlines() if marker in line and "STATEMENT" in line),
                    "",
                ),
                "psql_error": last_lines(failed.err, 3),
            },
        )


def bash_path(lab: Lab, wanted: str) -> str:
    """절차를 글자 그대로 치는 데 쓸 bash. docker 에 닿지 않는 bash(예: WSL 의 것)는 쓰지 않는다."""
    found = wanted or shutil.which("bash") or ""
    if not found:
        return ""
    check = lab.run([found, "-c", "docker compose version --short"], timeout=60)
    return found if check.code == 0 and check.out.strip() else ""


PROCEDURE_PRELUDE = f"unset {PASSWORD_VAR}"


def procedure_lines() -> tuple[str, list[str]]:
    """`change_password.sh` 의 첫 줄(셸의 변수 지우기)과 && 로 이은 뒤의 줄들(끝의 && 를 뗀다)."""
    lines = [
        line.strip()
        for line in (HERE / "change_password.sh").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    if not lines:
        return "", []
    return lines[0], [line.removesuffix("&&").rstrip() for line in lines[1:]]


def procedure(lab: Lab, project: Project, old: str, new: str) -> None:
    with lab.rounds.round(
        "4마 제안하는 절차(change_password.sh 를 bash 로 한 줄씩, 부모 셸에 옛 값을 export 한 채)"
    ) as slot:
        bash = bash_path(lab, lab.bash)
        prelude, lines = procedure_lines()
        if not bash:
            lab.note(slot, measured=False, result="docker 에 닿는 bash 가 없다", detail={})
            return
        wait_until(lambda: serve_healthy(project), 30)
        before, rows_before = boxes(project), row_counts(project)
        # 틈은 바꾸기 직전의 마지막 새 접속 줄부터 잰다(다른 종류의 줄이 그 뒤에 와도 빠지지 않게).
        began = row_time(project, "max", "who in ('serve-new', 'serve-start')")
        project.write_env({PASSWORD_VAR: new})
        # 운영자의 셸에 옛 값이 export 돼 있던 경우. 절차의 첫 줄이 그것을 지워야 .env 의 새 값이
        # 쓰인다.
        env = {
            **child_env(),
            PASSWORD_VAR: old,
            "COMPOSE_PROJECT_NAME": project.name,
            "MSYS_NO_PATHCONV": "1",
        }
        codes: list[Json] = []
        untouched: Json = None
        for index, line in enumerate(lines):
            try:
                done = subprocess.run(
                    [bash, "-c", f"{prelude}\n{line}"],
                    capture_output=True,
                    timeout=660,
                    cwd=project.folder,
                    env=env,
                )
                code, text = done.returncode, decode(done.stdout) + decode(done.stderr)
            except subprocess.TimeoutExpired:
                code, text = -1, "시간 초과"
            lab.raw(f"(bash) {prelude}; {line}", f"exit={code}\n{text}")
            codes.append(code)
            if code != 0:
                # && 와 같다. 앞 줄이 0 이 아니면 다음 줄을 치지 않는다.
                break
            if index == 0:
                middle = boxes(project)
                untouched = all(
                    (one := before[name]) is not None
                    and (other := middle[name]) is not None
                    and one.id == other.id
                    and one.started == other.started
                    for name in ("migrate", "serve")
                )
        after, rows_after = boxes(project), row_counts(project)
        migrate, serve = after["migrate"], after["serve"]
        changed = database_has(project, accepts=new, refuses=old)
        gap = project.psql_local(
            "select coalesce(round(extract(epoch from max(gap))::numeric, 1), 0) from ("
            "select at - lag(at) over (order by at) as gap from probe_rows "
            "where who in ('serve-new', 'serve-start') "
            f"and at >= to_timestamp({began or 0})) as gaps"
        ).out.strip()
        logs = project.compose("logs", "postgres").text
        survived = bool(rows_before) and all(
            rows_after.get(name, 0) >= count for name, count in rows_before.items()
        )
        lab.note(
            slot,
            # 표지: 셸의 변수를 지우는 첫 줄 뒤 세 줄을 모두 쳤고, 데이터베이스가 새 비밀번호만
            # 받는다(옛것은 인증 실패).
            measured=prelude == PROCEDURE_PRELUDE and len(codes) == len(lines) == 3 and changed,
            result=(
                f"세 줄의 종료 코드 {codes}, migrate 종료 {migrate.exit_code if migrate else '?'}, "
                f"serve 는 {serve.health if serve else '없음'}, 넣어 둔 줄은 "
                f"{'남았다' if survived else '남지 않았다'}, 새 비밀번호는 로그에 "
                f"{'남았다' if new in logs else '없다'}"
            ),
            detail={
                "bash": bash,
                "migrate_and_serve_untouched_after_first_line": untouched,
                "longest_gap_between_new_connection_rows_seconds": gap,
            },
        )


MISSING_ROLE = "probe_missing_role"


def password_failure(lab: Lab, project: Project) -> None:
    with lab.rounds.round(
        "4바 절차의 둘째 줄(\\password)이 서버에서 실패할 때 PostgreSQL 로그에 남는 것"
    ) as slot:
        marker = f"ctl{secrets.token_hex(8)}"
        # 절차의 둘째 줄과 같은 꼴로, 없는 계정을 고쳐 서버가 ALTER 를 거절하게 한다.
        script = (
            'printf "%s\\n%s\\n" "$PROBE_PASSWORD" "$PROBE_PASSWORD" | '
            f'psql -U {ROLE} -d {DATABASE} -v ON_ERROR_STOP=1 -c "\\password {MISSING_ROLE}"'
        )
        failed = project.compose(
            "exec", "-T", "-e", f"PROBE_PASSWORD={marker}", "postgres", "sh", "-c", script
        )
        logs = project.compose("logs", "postgres").text
        statement = next(
            (line for line in logs.splitlines() if "STATEMENT" in line and MISSING_ROLE in line), ""
        )
        # 표지: 서버가 그 실패를 문장째 기록했다(실패한 문장이 로그에 실리는 길을 실제로 지났다).
        # 그래야 평문이 없다는 것이 "기록하지 않아서"가 아니라 "평문을 받지 않아서"가 된다.
        lab.note(
            slot,
            measured=failed.code != 0
            and f'role "{MISSING_ROLE}" does not exist' in logs
            and bool(statement),
            result=(
                f"psql 종료 {failed.code}, 실패한 문장은 로그에 남았고, 그 문장의 비밀번호는 "
                f"{'SCRAM 해시' if 'SCRAM-SHA-256$' in statement else '다른 꼴'}, 평문은 로그에 "
                f"{'남았다' if marker in logs else '없다'}"
            ),
            detail={"psql_error": last_lines(failed.err, 2)},
        )


def section_password(lab: Lab) -> None:
    first, second, third, fourth = (f"pw{index}{secrets.token_hex(16)}" for index in range(1, 5))
    project = stack(lab, "s4", {PASSWORD_VAR: first})
    try:
        up = project.compose("up", "-d", "--wait", timeout=300)
        if up.code != 0 or not database_has(project, accepts=first, refuses=second):
            lab.rounds.record("4 준비", measured=False, result="처음 비밀번호로 띄우지 못했다")
            return
        env_only(lab, project, first, second)
        alter_then_up(lab, project, first, second)
        alter_first(lab, project, second, third)
        auth_settings(lab, project, (second, third))
        procedure(lab, project, third, fourth)
        password_failure(lab, project)
    finally:
        project.down(volumes=True)


# ---------------------------------------------------------------------------------------------
# 5. compose 의 변수 치환과 .env
# ---------------------------------------------------------------------------------------------

INVALID_FORMAT = "invalid interpolation format"
# 값 V=prefix-body-suffix 에 건 꼴. 앞의 일곱은 Compose 가 받는다고 원문이 적은 꼴(양성 대조)이고,
# 뒤의 여섯은 셸에서 값의 일부를 떼거나 바꾸는 꼴이다. None 은 거부를 기대한다는 뜻이다.
FORMS: tuple[tuple[str, str | None], ...] = (
    ("${V}", "prefix-body-suffix"),
    ("${V:-d}", "prefix-body-suffix"),
    ("${U:-d}", "d"),
    ("${U-d}", "d"),
    ("${V:+r}", "r"),
    ("${V+r}", "r"),
    ("${V:?e}", "prefix-body-suffix"),
    ("${V#prefix-}", None),
    ("${V%-suffix}", None),
    ("${V##*-}", None),
    ("${V/body/x}", None),
    ("${V:0:6}", None),
    ("${#V}", None),
)


def one_value(form: str) -> str:
    """꼴 하나를 환경 변수 하나에 건 compose 파일. 이미지는 쓰지 않으니 띄우지 않는다."""
    document: dict[str, Json] = {
        "services": {"probe": {"image": IMAGE, "environment": {"OUT": form}}},
    }
    return json.dumps(document) + "\n"


def config_env(
    project: Project, service: str, *, env: Mapping[str, str] | None = None
) -> tuple[Done, dict[str, str]]:
    """`docker compose config --format json` 이 그 서비스에 낸 환경 변수."""
    done = project.compose("config", "--format", "json", env=env)
    found: dict[str, str] = {}
    for key, value in as_map(dig(parse(done.out), "services", service, "environment")).items():
        if isinstance(value, str):
            found[key] = value
    return done, found


def interpolation_forms(lab: Lab) -> None:
    project = lab.project("s5-forms")
    project.write_env({"V": "prefix-body-suffix"})
    for form, expected in FORMS:
        with lab.rounds.round(f"5가 {form}") as slot:
            project.write("compose.yaml", one_value(form))
            done, env = config_env(project, "probe")
            message = done.err.strip()
            if expected is None:
                # 표지: 거부의 까닭이 치환 꼴이다(파일을 못 읽은 것 같은 다른 실패가 아니다).
                lab.note(
                    slot,
                    measured=done.code != 0 and INVALID_FORMAT in done.err,
                    result=f"거부(종료 {done.code})"
                    if done.code != 0
                    else f"받음: {env.get('OUT')!r}",
                    detail={"stderr": message},
                )
            else:
                lab.note(
                    slot,
                    measured=done.code == 0 and env.get("OUT") == expected,
                    result=f"받음: {env.get('OUT')!r}",
                    detail={"stderr": message},
                )


def required_message(lab: Lab) -> None:
    for title, env_text in (("줄이 없을 때", ""), ("빈 값일 때", f"{PASSWORD_VAR}=\n")):
        project = lab.project(f"s5-req-{len(env_text)}")
        project.write("compose.yaml", (HERE / "compose.yaml").read_text(encoding="utf-8"))
        project.write(".env", env_text)
        for command in (("config",), ("up", "-d")):
            with lab.rounds.round(f"5나 {title} docker compose {' '.join(command)}") as slot:
                done = project.compose(*command, timeout=120)
                created = lab.docker(
                    "ps", "-aq", "--filter", f"label=com.docker.compose.project={project.name}"
                ).out.split()
                # 표지: 문구가 글자 그대로(한국어 포함) 나왔다. 깨지면 이 글이 나오지 않는다.
                lab.note(
                    slot,
                    measured=MISSING in done.err,
                    result=f"종료 {done.code}, 만든 컨테이너 {len(created)}개",
                    detail={"stderr": done.err.strip()},
                )
        project.down(volumes=True)


def shell_wins(lab: Lab) -> None:
    with lab.rounds.round("5나 부모 셸의 같은 이름 변수와 .env 가 다를 때") as slot:
        project = lab.project("s5-shell")
        project.write("compose.yaml", (HERE / "compose.yaml").read_text(encoding="utf-8"))
        project.write_env({PASSWORD_VAR: "from-dotenv"})
        _, quiet = config_env(project, "postgres")
        done, loud = config_env(project, "postgres", env={PASSWORD_VAR: "from-shell"})
        # 대조: 셸 값이 없을 때는 .env 의 값이 든다.
        lab.note(
            slot,
            measured=done.code == 0 and quiet.get("POSTGRES_PASSWORD") == "from-dotenv",
            result=f"셸 값이 있으면 {loud.get('POSTGRES_PASSWORD')!r} 가 든다",
            detail={
                "without_shell": quiet.get("POSTGRES_PASSWORD"),
                "with_shell": loud.get("POSTGRES_PASSWORD"),
            },
        )


def images_listing(lab: Lab) -> None:
    """배포 안내 9절이 인터넷이 되는 PC에서 `.env.example` 을 베낀 뒤 치는 두 명령. 비밀번호 칸이
    빈 `.env` 에서 둘이 어떻게 끝나는지와, 같은 `.env` 에 셸 값 하나를 앞에 붙이면 지나는지를 본다.

    `pull` 은 레지스트리에 닿는다. 이미지는 이미 받은 digest 하나라 새로 받는 층은 없다.
    """
    project = lab.project("s5-images")
    project.write("compose.yaml", (HERE / "compose.yaml").read_text(encoding="utf-8"))
    project.write(".env", f"{PASSWORD_VAR}=\n")
    for title, env in (("빈 값", None), ("셸 값을 앞에 붙임", {PASSWORD_VAR: "unused"})):
        with lab.rounds.round(f"5마 {title} docker compose pull") as slot:
            done = project.compose("pull", env=env, timeout=300)
            # 표지: 빈 값은 `:?` 문구로 멈췄다. 셸 값은 그 이미지를 받았다는 줄이 찍혔다.
            pulled = f"Image {IMAGE} Pulled" in done.err + done.out
            measured = MISSING in done.err if env is None else done.code == 0 and pulled
            lab.note(
                slot,
                measured=measured,
                result=f"종료 {done.code}, 받았다는 줄 {pulled}",
                detail={"stdout": done.out.strip(), "stderr": done.err.strip()},
            )
        with lab.rounds.round(f"5마 {title} docker compose config --images") as slot:
            done = project.compose("config", "--images", env=env)
            listed = sorted(set(done.out.split()))
            # 표지: 빈 값은 `:?` 문구로 멈췄다. 셸 값은 이미지 줄을 냈고, 세 서비스가 같은 이미지라
            # 겹치는 줄을 빼면 하나다(9절의 `sort -u`).
            measured = MISSING in done.err if env is None else listed == [IMAGE]
            lab.note(
                slot,
                measured=measured,
                result=f"종료 {done.code}, 줄 {len(done.out.split())}개, 겹침을 뺀 줄 {listed}",
                detail={"stdout": done.out.strip(), "stderr": done.err.strip()},
            )


def special_values() -> list[tuple[str, str]]:
    """(이름, `.env` 의 `=` 뒤에 글자 그대로 쓸 값)."""
    return [
        ("openssl rand -hex 32 꼴", secrets.token_hex(32)),
        ("@ : /", "p@s:s/w"),
        ("$ 하나", "abc$def"),
        ("$$", "abc$$def"),
        ("작은따옴표 안의 $", "'abc$def'"),
        ("# 붙여 씀", "abc#def"),
        ("공백 뒤 #", "abc #def"),
        ("공백", "a b"),
        ("작은따옴표", "'quoted'"),
        ("큰따옴표", '"quoted"'),
        ("%", "a%b"),
        ("역슬래시", "a\\b"),
    ]


def received_env(project: Project, service: str) -> dict[str, str]:
    one = box(project, service)
    return dict(one.env) if one else {}


def special_table(lab: Lab) -> list[tuple[str, str, str]]:
    """값마다 compose 가 끼워 넣는 값. 돌려주는 것은 (이름, .env 에 쓴 값, 컨테이너가 받은
    비밀번호)."""
    received: list[tuple[str, str, str]] = []
    project = lab.project("s5-table")
    project.write("compose.yaml", (HERE / "compose.yaml").read_text(encoding="utf-8"))
    for name, raw_value in special_values():
        with lab.rounds.round(f"5다 .env 값 {name}") as slot:
            project.write(".env", f"{PASSWORD_VAR}={raw_value}\n")
            config, shown = config_env(project, "postgres")
            create = project.compose("create", "postgres", "migrate", timeout=120)
            password = received_env(project, "postgres").get("POSTGRES_PASSWORD")
            url = received_env(project, "migrate").get("AGENT_OS_DATABASE_URL")
            project.down(volumes=True)
            warnings = [
                line.strip() for line in config.err.splitlines() if "variable is not set" in line
            ]
            # 표지: config 가 돌았고, 컨테이너를 만들어 실제로 받은 환경 변수를 읽었다.
            lab.note(
                slot,
                measured=config.code == 0
                and create.code == 0
                and password is not None
                and url is not None,
                result=f"POSTGRES_PASSWORD={password!r}",
                detail={
                    "dotenv_line": f"{PASSWORD_VAR}={raw_value}",
                    "config_shows": shown.get("POSTGRES_PASSWORD"),
                    "container_url": url,
                    "warnings": [*warnings],
                },
            )
            if password is not None:
                received.append((name, raw_value, password))
    return received


LAUNCHED = ("openssl rand -hex 32 꼴", "@ : /", "$$", "공백", "%")


def special_launch(lab: Lab, received: Sequence[tuple[str, str, str]]) -> None:
    """몇 값은 실제로 띄워, 데이터베이스에 설정된 비밀번호와 migrate 대역의 psql 접속을 본다."""
    for index, (name, raw_value, password) in enumerate(received):
        if name not in LAUNCHED:
            continue
        with lab.rounds.round(f"5라 .env 값 {name} 으로 띄우기") as slot:
            project = lab.project(f"s5-launch-{index}")
            try:
                project.write("compose.yaml", (HERE / "compose.yaml").read_text(encoding="utf-8"))
                project.write(".env", f"{PASSWORD_VAR}={raw_value}\n")
                up = project.compose("up", "-d", "--wait", "postgres", timeout=180)
                accepted, _ = logs_in(project, password)
                refused, message = logs_in(project, password + "x")
                run = project.compose("run", "--rm", "--no-deps", "-T", "migrate", timeout=120)
                postgres_env = received_env(project, "postgres")
                # 표지: 컨테이너가 받은 값으로는 들어가고, 한 글자 더한 값은 인증 실패로 막힌다.
                # migrate 대역의 psql 이 실제로 돌았다는 것(올렸다는 줄이나 psql 의 오류 줄)도 본다.
                ran = MIGRATE_DONE_V1 in run.out or "psql: error:" in run.err
                lab.note(
                    slot,
                    measured=up.code == 0
                    and accepted
                    and not refused
                    and AUTH_FAILED in message
                    and ran,
                    result=(
                        "데이터베이스의 비밀번호는 컨테이너가 받은 값, migrate 대역의 psql 은 "
                        + ("접속했다" if run.code == 0 else f"종료 {run.code}")
                    ),
                    detail={
                        "migrate_stdout": last_lines(run.out, 1),
                        "psql_error": next(
                            (line for line in run.err.splitlines() if "psql:" in line), ""
                        ),
                        "postgres_env_password": postgres_env.get("POSTGRES_PASSWORD"),
                    },
                )
            finally:
                project.down(volumes=True)


def section_interpolation(lab: Lab) -> None:
    interpolation_forms(lab)
    required_message(lab)
    shell_wins(lab)
    images_listing(lab)
    special_launch(lab, special_table(lab))


# ---------------------------------------------------------------------------------------------
# 2. 상태 확인
# ---------------------------------------------------------------------------------------------

# 컨테이너 안에서 0.1초마다 유닉스 소켓과 127.0.0.1 의 pg_isready 를 친다. 둘 다 0 이 다섯 번
# 이어지면 멈춘다. 줄마다 `시각 유닉스의_종료코드 TCP의_종료코드` 다.
INSIDE_SAMPLER = r"""
end=$(( $(date +%s) + 45 )); run=0
while [ "$(date +%s)" -lt "$end" ]; do
  t=$(date +%s.%N)
  pg_isready -q -U agent_os -d agent_os; u=$?
  pg_isready -q -h 127.0.0.1 -U agent_os -d agent_os; h=$?
  echo "$t $u $h"
  if [ "$u" = 0 ] && [ "$h" = 0 ]; then run=$((run + 1)); else run=0; fi
  [ "$run" -ge 5 ] && break
  sleep 0.1
done
"""
# 같은 네트워크의 다른 컨테이너에서 0.1초마다 TCP 로 접속해 `select 1` 을 친다. 줄마다
# `시각 종료코드`. 성공이 열다섯 번 이어지면 멈춘다(2다의 healthy 가 첫 성공보다 늦어도 그 뒤의
# 표본이 남게, start_interval 2초보다 길게 돈다).
OUTSIDE_SAMPLER = r"""
end=$(( $(date +%s) + 60 )); run=0
while [ "$(date +%s)" -lt "$end" ]; do
  t=$(date +%s.%N)
  psql -h postgres -U agent_os -d agent_os -tAc 'select 1' >/dev/null 2>&1; c=$?
  echo "$t $c"
  if [ "$c" = 0 ]; then run=$((run + 1)); else run=0; fi
  [ "$run" -ge 15 ] && break
  sleep 0.1
done
"""


def samples(text: str, width: int) -> list[tuple[float, ...]]:
    """표본 줄을 숫자 열로 읽는다. 모양이 다른 줄은 버린다."""
    found: list[tuple[float, ...]] = []
    for line in text.splitlines():
        fields = line.split()
        if len(fields) != width:
            continue
        try:
            found.append(tuple(float(field) for field in fields))
        except ValueError:
            continue
    return found


def first_zero(rows: Sequence[tuple[float, ...]], column: int) -> float | None:
    return next((row[0] for row in rows if row[column] == 0), None)


def ready_times(project: Project) -> list[float]:
    """PostgreSQL 로그의 '접속을 받을 준비가 됐다' 줄마다 Docker 가 찍은 시각."""
    done = project.lab.docker("logs", "--timestamps", project.box("postgres"))
    found: list[float] = []
    for line in done.text.splitlines():
        if READY_LINE in line:
            moment = stamp(line.split(" ", 1)[0])
            if moment is not None:
                found.append(moment)
    return found


def spawn(lab: Lab, argv: Sequence[str]) -> subprocess.Popen[bytes]:
    """끝날 때까지 기다릴 명령을 띄운다. 끝에 `collect` 로 출력을 거둔다."""
    lab.raw("(띄움) " + " ".join(argv), "")
    return subprocess.Popen(
        list(argv),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env=child_env(),
    )


def collect(lab: Lab, process: subprocess.Popen[bytes], title: str, timeout: float = 90) -> str:
    """띄운 명령의 출력을 거둔다. 제한 시간을 넘기면 이 손으로 띄운 그 프로세스(핸들)만 끈다."""
    try:
        out, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        out, _ = process.communicate(timeout=30)
    text = decode(out)
    lab.raw(f"(거둠) {title} exit={process.returncode}", text)
    return text


def outside_sampler(lab: Lab, project: Project, password: str) -> subprocess.Popen[bytes]:
    return spawn(
        lab,
        [
            *("docker", "run", "--rm", "--network", project.network, "--label", lab.label),
            *("-e", f"PGPASSWORD={password}", "-e", "PGCONNECT_TIMEOUT=2"),
            *("--entrypoint", "sh", lab.image, "-c", OUTSIDE_SAMPLER),
        ],
    )


@dataclass(frozen=True)
class Sampled:
    started: float | None
    inside: list[tuple[float, ...]]
    outside: list[tuple[float, ...]]
    ready: list[float]


def sample_start(lab: Lab, project: Project, password: str) -> Sampled:
    """컨테이너를 만들어 두고, 바깥 표본을 먼저 띄운 뒤 PostgreSQL 을 시작하고 안쪽 표본을
    띄운다."""
    project.compose("create", "postgres")
    outside = outside_sampler(lab, project, password)
    time.sleep(2.5)
    project.compose("start", "postgres")
    inside = spawn(lab, ["docker", "exec", project.box("postgres"), "sh", "-c", INSIDE_SAMPLER])
    inside_text = collect(lab, inside, "안쪽 표본")
    outside_text = collect(lab, outside, "바깥 표본")
    postgres = box(project, "postgres")
    return Sampled(
        started=postgres.started if postgres else None,
        inside=samples(inside_text, 3),
        outside=samples(outside_text, 2),
        ready=ready_times(project),
    )


def judge_samples(sampled: Sampled) -> tuple[bool, dict[str, Json]]:
    """표지와 견준 값. 표지는 셋이다. 안쪽 표본의 첫 줄이 아직 답하지 않는 때다. 바깥 표본이 시작
    전부터 돌았고 처음에는 실패했다. 세 확인이 모두 한 번은 0 을 냈다."""
    inside, outside, base = sampled.inside, sampled.outside, sampled.started
    unix = first_zero(inside, 1)
    tcp = first_zero(inside, 2)
    remote = first_zero(outside, 1)
    window = [row[0] for row in inside if row[1] == 0 and row[2] != 0]
    after_first = [row for row in inside if unix is not None and row[0] >= unix]
    flapped = any(row[1] != 0 for row in after_first)
    gaps = sorted(later[0] - earlier[0] for earlier, later in pairwise(inside))
    measured = (
        base is not None
        and bool(inside)
        and inside[0][1] != 0
        and bool(outside)
        and outside[0][0] < base
        and outside[0][1] != 0
        and None not in (unix, tcp, remote)
    )
    detail: dict[str, Json] = {
        "seconds_after_start": offsets(
            base,
            unix_first_ok=unix,
            tcp_127_first_ok=tcp,
            other_container_first_ok=remote,
            first_inside_sample=inside[0][0] if inside else None,
        ),
        "ready_log_lines_after_start": [
            round(moment - base, 2) for moment in sampled.ready if base is not None
        ],
        "unix_ok_while_tcp_not": {
            "samples": len(window),
            "span_seconds": round(window[-1] - window[0], 2) if window else 0,
        },
        "unix_failed_again_after_first_ok": flapped,
        "samples": {"inside": len(inside), "outside": len(outside)},
        # 표본 줄의 시각은 그 줄의 첫 확인을 치기 직전이다. 간격이 0.1초보다 길면 확인이 느렸던
        # 것이다.
        "inside_gap_median_seconds": round(gaps[len(gaps) // 2], 2) if gaps else None,
    }
    return measured, detail


def health_service(test: Sequence[str], start_interval: str) -> dict[str, Json]:
    return {
        **hardened(user="999:999"),
        "healthcheck": {
            "test": ["CMD", *test],
            "interval": "30s",
            "timeout": "10s",
            "retries": 3,
            "start_period": "30s",
            "start_interval": start_interval,
        },
    }


UNIX_CHECK = ("pg_isready", "-U", ROLE, "-d", DATABASE)
TCP_CHECK = ("pg_isready", "-h", "127.0.0.1", "-U", ROLE, "-d", DATABASE)
HEALTH_VARIANTS: tuple[tuple[str, Sequence[str], str], ...] = (
    ("유닉스 소켓, start_interval 200ms", UNIX_CHECK, "200ms"),
    ("TCP 127.0.0.1, start_interval 200ms", TCP_CHECK, "200ms"),
    ("TCP 127.0.0.1, start_interval 1s", TCP_CHECK, "1s"),
    ("TCP 127.0.0.1, start_interval 2s(지금 앵커)", TCP_CHECK, "2s"),
)


# 2가·2나에서 진입 스크립트를 이만큼 늦게 띄운다. 데이터가 있는 볼륨은 시작 뒤 0.3초 안에 준비되기도
# 해서, `docker exec` 로 띄운 안쪽 표본의 첫 줄이 이미 준비된 서버를 봐 대조가 무엇도 보지 못했다
# (늦추기 전 판의 2나 다섯 가운데 넷). 늦추면 안쪽 표본이 서버가 뜨기 전부터 돈다.
HOLD_SECONDS = 5


def section_health(lab: Lab) -> None:
    proposed = hardened(
        user="999:999",
        entrypoint=["sh", "-c", f"sleep {HOLD_SECONDS} && exec docker-entrypoint.sh postgres"],
    )
    for index in range(1, lab.repeat + 1):
        project = lab.project(f"s2-{index}")
        password = secrets.token_hex(16)
        try:
            project.write("compose.yaml", postgres_only(proposed))
            project.write_env({PASSWORD_VAR: password})
            with lab.rounds.round(f"2가 빈 볼륨으로 처음 띄우기 {index}") as slot:
                sampled = sample_start(lab, project, password)
                measured, detail = judge_samples(sampled)
                times = as_map(detail["seconds_after_start"])
                unix, tcp = times.get("unix_first_ok"), times.get("tcp_127_first_ok")
                earlier = isinstance(unix, float) and isinstance(tcp, float) and unix < tcp
                detail["entrypoint_held_seconds"] = HOLD_SECONDS
                lab.note(
                    slot,
                    # 처음 띄우기라는 표지: 준비 줄이 둘(초기화용 임시 서버와 마지막 서버)이다.
                    measured=measured and len(sampled.ready) == 2,
                    result=(
                        "유닉스 소켓이 TCP 보다 먼저 0"
                        if earlier
                        else "유닉스 소켓과 TCP 가 함께 0"
                    ),
                    detail=detail,
                )
            project.compose("down", "--timeout", "5")
            with lab.rounds.round(f"2나 데이터가 있는 볼륨으로 다시 띄우기 {index}(대조)") as slot:
                sampled = sample_start(lab, project, password)
                measured, detail = judge_samples(sampled)
                times = as_map(detail["seconds_after_start"])
                unix, tcp = times.get("unix_first_ok"), times.get("tcp_127_first_ok")
                window = as_map(detail["unix_ok_while_tcp_not"]).get("samples")
                detail["entrypoint_held_seconds"] = HOLD_SECONDS
                lab.note(
                    slot,
                    measured=measured and len(sampled.ready) == 1,
                    result=(
                        "유닉스 소켓만 답하는 표본 없음"
                        if window == 0
                        else f"유닉스 소켓만 답하는 표본 {window}개"
                    ),
                    detail=detail,
                )
        finally:
            project.down(volumes=True)
    for variant, (name, test, start_interval) in enumerate(HEALTH_VARIANTS):
        for index in range(1, 4):
            project = lab.project(f"s2-h{variant}-{index}")
            password = secrets.token_hex(16)
            try:
                project.write("compose.yaml", postgres_only(health_service(test, start_interval)))
                project.write_env({PASSWORD_VAR: password})
                with lab.rounds.round(f"2다 {name} {index}") as slot:
                    since = daemon_now(lab)
                    sampled = sample_start(lab, project, password)
                    wait_until(partial(postgres_healthy, project), 60)
                    found = events(lab, project, since)
                    healthy = first_event(found, "health_status: healthy", service="postgres")
                    remote = first_zero(sampled.outside, 1)
                    lead = (
                        round(remote - healthy, 2)
                        if healthy is not None and remote is not None
                        else None
                    )
                    measured, detail = judge_samples(sampled)
                    detail["healthy_after_start"] = (
                        round(healthy - sampled.started, 2)
                        if healthy is not None and sampled.started is not None
                        else None
                    )
                    detail["unhealthy_events"] = len(
                        [event for event in found if event.action == "health_status: unhealthy"]
                    )
                    # 판정: healthy 이벤트 뒤에 시작한 바깥 표본 가운데 실패한 것의 수. 첫 성공
                    # 시각끼리 견주면 표본 간격(약 0.2~0.3초) 안의 차이로 갈려 판정하지 않는다.
                    after = [
                        row for row in sampled.outside if healthy is not None and row[0] >= healthy
                    ]
                    failed = [row for row in after if row[1] != 0]
                    detail["outside_after_healthy"] = {"samples": len(after), "failed": len(failed)}
                    lab.note(
                        slot,
                        # 표지에 더해, healthy 뒤에 바깥 표본이 하나는 돌았어야 판정할 수 있다.
                        measured=(
                            measured
                            and healthy is not None
                            and len(sampled.ready) == 2
                            and bool(after)
                        ),
                        result=f"healthy 뒤에 시작한 다른 컨테이너의 접속 {len(after)}개 가운데 "
                        f"실패 {len(failed)}개",
                        detail={**detail, "other_container_ok_minus_healthy": lead},
                    )
            finally:
                project.down(volumes=True)


# ---------------------------------------------------------------------------------------------
# 정리와 진입점
# ---------------------------------------------------------------------------------------------


def leftovers(lab: Lab) -> list[str]:
    """이 실행의 이름을 단 컨테이너·볼륨·네트워크 가운데 남은 것."""
    found: list[str] = []
    stray = lab.docker("ps", "-aq", "--filter", f"label={lab.label}")
    found += [f"container {line}" for line in stray.out.split()]
    for project in lab.projects:
        scope = f"label=com.docker.compose.project={project.name}"
        for kind, argv in (
            ("container", ("ps", "-aq", "--filter", scope)),
            ("volume", ("volume", "ls", "-q", "--filter", scope)),
            ("network", ("network", "ls", "-q", "--filter", scope)),
        ):
            listed = lab.docker(*argv)
            if listed.code != 0:
                found.append(f"{kind} 목록을 읽지 못했다({project.name})")
            found += [f"{kind} {line}" for line in listed.out.split()]
    return found


def clean_up(lab: Lab) -> None:
    for project in lab.projects:
        project.down(volumes=True)
    stray = lab.docker("ps", "-aq", "--filter", f"label={lab.label}")
    for box_id in stray.out.split():
        lab.docker("rm", "-f", box_id)
    left = leftovers(lab)
    if left:
        lab.rounds.record("정리", measured=False, result="남은 것: " + ", ".join(left))


SECTIONS: Mapping[str, Callable[[Lab], None]] = {
    "1": section_permissions,
    "3": section_depends,
    "4": section_password,
    "5": section_interpolation,
    "2": section_health,
}


def environment(lab: Lab) -> bool:
    """판을 찍고, 이미지가 로컬에 있는지 본다. 없으면 받지 않고 멈춘다."""
    version = lab.docker("version", "--format", "{{.Client.Version}} / {{.Server.Version}}")
    compose = lab.run(["docker", "compose", "version", "--short"])
    info = lab.docker("info", "--format", "{{.OperatingSystem}} / {{.KernelVersion}}")
    image = lab.docker("image", "inspect", lab.image, "--format", "{{.Id}}")
    print(f"docker(클라이언트 / 엔진): {version.out.strip()}")
    print(f"compose: {compose.out.strip()}")
    print(f"엔진의 운영체제와 커널: {info.out.strip()}")
    print(f"이미지: {lab.image} ({image.out.strip() or '로컬에 없다'})")
    return version.code == 0 and compose.code == 0 and image.code == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="단독 배포 compose 의 PostgreSQL 모양을 잰다")
    parser.add_argument("--sections", default=",".join(SECTIONS), help="쉼표로 이은 항목 번호")
    parser.add_argument("--work", type=Path, default=Path(tempfile.gettempdir()) / PREFIX)
    parser.add_argument("--image", default=IMAGE)
    parser.add_argument("--repeat", type=int, default=5, help="2번(상태 확인)의 되풀이 수")
    parser.add_argument(
        "--verbose", action="store_true", help="회차마다 본 것 전부를 화면에도 찍는다"
    )
    parser.add_argument("--bash", default="", help="4번의 절차를 칠 bash. 비우면 PATH 에서 찾는다")
    args = parser.parse_args()
    wanted = [name.strip() for name in str(args.sections).split(",") if name.strip()]
    unknown = [name for name in wanted if name not in SECTIONS]
    if unknown:
        parser.error(f"모르는 항목: {', '.join(unknown)}")
    token = secrets.token_hex(3)
    work: Path = args.work
    folder = work.resolve() / f"run-{time.strftime('%Y%m%d-%H%M%S')}-{token}"
    folder.mkdir(parents=True, exist_ok=False)
    lab = Lab(
        token=token,
        folder=folder,
        image=str(args.image),
        repeat=int(args.repeat),
        verbose=bool(args.verbose),
        bash=str(args.bash),
    )
    print(f"원본 출력: {folder / 'raw.log'}")
    if not environment(lab):
        print("Docker 나 이미지가 없다. 이미지를 받지 않고 멈춘다.")
        return 1
    try:
        for name in wanted:
            print(f"--- 항목 {name}", flush=True)
            SECTIONS[name](lab)
    finally:
        clean_up(lab)
    print(lab.rounds.summary())
    return lab.rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
