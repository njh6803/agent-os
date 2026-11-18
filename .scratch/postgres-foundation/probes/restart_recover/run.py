"""ADR 0066 의 어림 하나를 리눅스의 Docker Engine 에서 잰다. "데몬이나 서버가 다시 켜진 뒤에는
`serve` 가 PostgreSQL 보다 먼저 뜰 수 있다고 보고, 그때는 `serve` 의 다시 시도와 재시작 정책이
받친다고 본다(어림, 명세가 잰다)"(결정 "compose 배치"). 결정은 하지 않고 회차마다 본 것을 낸다.

저장소 루트에서

    uv run python .scratch/postgres-foundation/probes/restart_recover/run.py
        [--sections 0,1,2,3,4,5] [--rounds 3] [--work <원본 출력을 둘 폴더>]
        [--dind-image <참조>] [--reuse] [--keep]

리눅스의 Docker Engine 을 얻는 길은 `.scratch/release-image/probes/bridge_recover/run.py` 와 같다.
이 PC(Windows 의 Docker Desktop)에서 공식 dind 이미지를 --privileged 로 띄우고, 그 컨테이너(이름
pgf-recover-dind-<무작위>)가 "리눅스 서버" 노릇을 한다. compose 는 그 안에서 돈다(docker exec).
PostgreSQL 이미지는 받지 않고 이 PC 에 있는 것을 `docker save` 로 내보내 안쪽에서 `docker load`
한다. 끝나면 dind 컨테이너와 그 볼륨(pgf-recover-data-<무작위>)을 지운다. 이 프로브의 표지(라벨
pgf-recover-probe=<무작위>)가 없는 것은 건드리지 않고, 호스트 포트를 열지 않는다.

배치(compose.yml). postgres(이름 있는 볼륨, pg_isready 상태 확인, unless-stopped), migrate
대역(migrate.sh, 표를 만들고 줄 하나를 더한 뒤 0으로 끝난다, restart "no", postgres 가 건강해진
뒤), serve 대역(serve.sh, RETRY_SECONDS 동안 다시 시도하고 못 붙으면 1로 끝난다, unless-stopped,
migrate 가 성공으로 끝난 뒤), 그리고 측정 도구인 watch(끝없이 같은 시도를 하며 적는다).

세 사건(bridge_recover 의 방법)
- 데몬만 다시 켬: 안의 dockerd 에 TERM. supervise.sh 가 다시 띄운다. 표지는 supervise.sh 의 dockerd
  시작 횟수가 늘고 dockerd 의 pid 가 바뀐 것이다.
- 서버를 정상으로 껐다 켬: 바깥에서 `docker restart` dind. 표지는 dind 의 새 시작 시각이다.
- 전원 끊김: 바깥에서 `docker kill` dind 뒤 `docker start`. 표지는 dind 의 새 시작 시각과, 돌아온
  PostgreSQL 의 기록에 있는 `database system was interrupted` 다.

항목(README 의 결과 번호와 같다)

0. 환경과 판, 이미지 옮기기(digest 참조가 save·load 를 지나 남는지), serve 대역의 양성 대조 셋
   (붙을 수 있으면 붙고 0으로 끝난다, 포트가 닫힌 이름에는 `Connection refused` 를 적고 1로 끝난다,
   PostgreSQL 컨테이너가 멈춰 있으면 실패를 적고 1로 끝난다).
1. 복귀. RETRY_SECONDS=30 으로 세 사건을 --rounds 번씩. 어떤 컨테이너가 다시 뜨는지, migrate 가
   다시 돌지 않는지(줄 수), serve 와 postgres 의 시작 차례, serve 가 뜬 뒤 붙기까지와 그 전의 실패
   문구, 넣어 둔 줄이 남는지.
2. 다시 시도하는 시간. RETRY_SECONDS 0 과 5 로 같은 사건을 되풀이한다. 재시작 정책만으로 붙는지와
   재시작 횟수, 걸린 시간. 끝에 1·2 의 회차를 모아 분포를 낸다.
3. PostgreSQL 만 죽을 때. `docker kill`, postmaster 를 바깥에서 KILL(Docker 가 시키지 않은 죽음),
   WAL 을 쌓은 뒤의 같은 KILL(복구 창을 넓힌다), `docker stop`(대조).
4. 처음 띄우기가 끊긴 경우. `up -d` 가 도는 중(PostgreSQL 이 초기화 중이거나 migrate 가 일을 하기
   전)에 데몬이 다시 켜지거나 전원이 끊긴다. serve 대역은 표가 없으면 3으로 끝난다(REQUIRE_TABLE).
   초기화 중의 사건은 초기화 끝 문구가 사건 전에 없었다는 것을 표지로 보고, 끊긴 첫 삶의 마지막
   기록 줄(초기화가 어디서 끊겼나)을 적는다. 다시 `up -d` 해도 붙지 않으면 `down`(볼륨은 남김)
   뒤 `up -d`, 그래도 안 되면 `down -v` 뒤 `up -d` 로 볼륨이 까닭인지 가른다.
5. postgres 서비스의 권한을 좁힌 변형(compose.narrow.yml)이 처음 뜨는지와 데몬 재시작 뒤 뜨는지.

회차의 표지. 사건이 실제로 났다, 사건 전의 기준선(postgres 가 돌고, migrate 가 0으로 끝났고, serve
대역이 붙었고, 줄이 둘)이 섰다, 를 회차마다 단언한다. 표지가 없는 회차는 측정 아님으로 센다.
정리 실패(앞 회차의 것이 안쪽 엔진에 남았다)가 나면 그 뒤의 회차는 모두 측정 아님이다.

시각. 컨테이너의 시작은 안쪽 데몬의 이벤트(`docker events`)와 `docker inspect` 의 StartedAt, 기록
줄의 시각은 `docker logs -t` 가 붙인 것이다. 모두 안쪽 dockerd 의 시계다. dind 의 시작 시각과
supervise.sh 의 줄은 바깥 dockerd 의 시계이고, 두 dockerd 는 같은 커널(Docker Desktop 의 가상
머신) 위에 있다.

못 보는 것. 실제 서버의 재부팅(systemd 가 docker.service 와 containerd 를 띄우는 차례, 커널이 다시
뜨는 것, 디스크 검사), 진짜 전원 끊김(커널의 쓰기 버퍼가 날아가는 것. dind 를 죽여도 가상 머신의
커널은 살아 있다), 진짜 `serve`(asyncpg 가 내는 예외의 꼴)와 진짜 `agent-os migrate`, 다른 기기의
디스크 속도, live-restore 를 켠 데몬, rootless Docker. 결과와 한계는 같은 폴더의 README.md 에 있다.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import secrets
import statistics
import subprocess
import sys
import tempfile
import time
from collections import Counter
from collections.abc import Callable, Generator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds, Slot  # noqa: E402

# 이 PC 가 받아 둔 공식 이미지다(ADR 0066 결정 "이미지와 지원 범위"가 적은 digest).
PG_DIGEST = "postgres@sha256:b9f6b8ff03b62f3cfd9d9ba3fe56226a9991c79d3fb46fd46536263bf02be553"
PG_TAG = "postgres:18"
DIND_IMAGE = "docker:29.9.2-dind"

PREFIX = "pgf-recover"
MARK = "pgf-recover-probe"
PROJECT = "pgf-recover"
REMOTE = "/probe"
LINE_ENDING_FILES = (
    "supervise.sh",
    "serve.sh",
    "migrate.sh",
    "crash.sh",
    "compose.yml",
    "compose.narrow.yml",
)
PSQL = ("psql", "-U", "agent_os", "-d", "agent_os", "-tA", "-v", "ON_ERROR_STOP=1")


@dataclass
class Session:
    """실행 하나가 쓰는 바깥 이름과 원본 출력 자리."""

    dind: str = ""
    volume: str = ""
    raw: Path | None = None


SESSION = Session()


def raw(title: str, text: str) -> None:
    if SESSION.raw is not None:
        with SESSION.raw.open("a", encoding="utf-8") as out:
            out.write(f"\n===== {time.strftime('%H:%M:%S')} {title}\n{text}\n")


def say(text: str) -> None:
    print(text, flush=True)
    raw("출력", text)


def tail(text: str, count: int = 3) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " / ".join(lines[-count:])


# docker 가 내는 JSON 을 읽는 자리. 모양이 기대와 다르면 예외 대신 빈 값이 나오고, 그 빈 값으로는
# 아래의 표지가 서지 않아 측정 아님으로 세어진다.
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


def dig(value: Json, *keys: str) -> Json:
    for key in keys:
        value = as_map(value).get(key)
    return value


STAMP = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d+))?Z")


def epoch(text: str) -> float | None:
    """Docker 가 찍는 시각(RFC 3339, UTC)을 초로. 한 번도 시작하지 않은 컨테이너의 0001년과 읽지
    못한 글은 None 이다."""
    match = STAMP.match(text)
    if match is None or text.startswith("0001-"):
        return None
    whole = datetime.strptime(match.group(1), "%Y-%m-%dT%H:%M:%S").replace(tzinfo=UTC)
    return whole.timestamp() + float("0." + (match.group(2) or "0"))


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
    """명령 하나. 시간을 넘기면 종료 코드 -1 이다."""
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


def exec_argv(env: Mapping[str, str] | None) -> list[str]:
    argv = ["docker", "exec"]
    for key, value in (env or {}).items():
        argv += ["-e", f"{key}={value}"]
    return [*argv, SESSION.dind]


def inner(*args: str, env: Mapping[str, str] | None = None, timeout: float = 120) -> Done:
    """dind 컨테이너("리눅스 서버") 안에서 치는 명령."""
    return run([*exec_argv(env), *args], timeout=timeout)


def shell(script: str, *, timeout: float = 60) -> Done:
    return inner("sh", "-c", script, timeout=timeout)


# ---------- 배치와 컨테이너 ----------


@dataclass(frozen=True)
class Stack:
    """compose 파일 묶음 하나. 프로젝트 이름은 늘 PROJECT 이고 compose.yml 위에 덧씌움을 얹는다."""

    image: str
    files: tuple[str, ...] = ()
    env: Mapping[str, str] = field(default_factory=dict[str, str])

    def argv(self, args: Sequence[str]) -> list[str]:
        argv = ["docker", "compose", "--ansi", "never", "--progress", "plain", "-p", PROJECT]
        argv += ["--project-directory", REMOTE]
        for name in ("compose.yml", *self.files):
            argv += ["-f", f"{REMOTE}/{name}"]
        return [*argv, *args]

    def full_env(self) -> dict[str, str]:
        return {"PG_IMAGE": self.image, **self.env}

    def compose(self, *args: str, timeout: float = 240) -> Done:
        return inner(*self.argv(args), env=self.full_env(), timeout=timeout)

    def spawn(self, *args: str) -> subprocess.Popen[bytes]:
        """compose 명령을 기다리지 않고 띄운다. 도는 동안 사건을 내려는 것이다."""
        argv = [*exec_argv(self.full_env()), *self.argv(args)]
        raw("spawn " + " ".join(argv), "")
        return subprocess.Popen(
            argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )

    def with_env(self, extra: Mapping[str, str]) -> Stack:
        return Stack(self.image, self.files, {**self.env, **extra})


def finish(process: subprocess.Popen[bytes], *, seconds: float) -> tuple[int | None, str]:
    """spawn 으로 띄운 명령이 끝나기를 기다린다. 시간을 넘기면 이 프로브가 띄운 그 자식을 손잡이로
    끈다(pid 를 찾아 끄는 것이 아니다)."""
    try:
        out, _ = process.communicate(timeout=seconds)
    except subprocess.TimeoutExpired:
        process.kill()
        out, _ = process.communicate(timeout=30)
        raw("spawn 끝(시간 초과로 끔)", decode(out))
        return None, decode(out)
    raw(f"spawn 끝 exit={process.returncode}", decode(out))
    return process.returncode, decode(out)


@dataclass(frozen=True)
class Box:
    """안쪽 엔진의 컨테이너 하나의 지금 모습(docker inspect)."""

    id: str
    service: str
    status: str
    running: bool
    exit_code: int
    restarts: int
    started: str
    finished: str
    health: str
    pid: int
    user: str
    read_only: bool
    cap_drop: tuple[str, ...]
    security: tuple[str, ...]

    @property
    def started_at(self) -> float | None:
        return epoch(self.started)

    @property
    def finished_at(self) -> float | None:
        return epoch(self.finished)


LIST_BOXES = (
    f'ids="$(docker ps -aq --no-trunc --filter label=com.docker.compose.project={PROJECT})"; '
    '[ -n "$ids" ] || exit 0; docker inspect $ids'
)


def boxes() -> dict[str, Box]:
    """이 compose 프로젝트의 컨테이너(멈춘 것 포함). 열쇠는 서비스 이름이다. 안쪽 데몬이 답하지
    않으면 빈 사전이다. `compose run` 의 한 번짜리 컨테이너는 뺀다."""
    done = shell(LIST_BOXES)
    found: dict[str, Box] = {}
    if done.code != 0:
        return found
    for info in as_list(parse(done.out)):
        labels = as_map(dig(info, "Config", "Labels"))
        if as_text(labels.get("com.docker.compose.oneoff")) == "True":
            continue
        service = as_text(labels.get("com.docker.compose.service"))
        host = as_map(dig(info, "HostConfig"))
        found[service] = Box(
            id=as_text(dig(info, "Id")),
            service=service,
            status=as_text(dig(info, "State", "Status")),
            running=dig(info, "State", "Running") is True,
            exit_code=as_int(dig(info, "State", "ExitCode")),
            restarts=as_int(dig(info, "RestartCount")),
            started=as_text(dig(info, "State", "StartedAt")),
            finished=as_text(dig(info, "State", "FinishedAt")),
            health=as_text(dig(info, "State", "Health", "Status")),
            pid=as_int(dig(info, "State", "Pid")),
            user=as_text(dig(info, "Config", "User")),
            read_only=host.get("ReadonlyRootfs") is True,
            cap_drop=tuple(as_text(item) for item in as_list(host.get("CapDrop"))),
            security=tuple(as_text(item) for item in as_list(host.get("SecurityOpt"))),
        )
    return found


def is_running(now: Mapping[str, Box], service: str) -> bool:
    box = now.get(service)
    return box is not None and box.running


def state_text(box: Box | None) -> str:
    if box is None:
        return "없음"
    if box.status == "exited":
        return f"exited({box.exit_code})"
    return box.status


def change(before: Box | None, after: Box | None) -> str:
    if after is None:
        return "없어짐"
    if before is None:
        return f"새로 생김({state_text(after)})"
    if after.id != before.id:
        return f"다시 만들어짐({state_text(after)})"
    if after.started != before.started:
        return f"다시 시작됨({state_text(after)}, 재시작 횟수 {after.restarts})"
    return f"그대로({state_text(after)})"


# ---------- 기록 읽기 ----------


@dataclass(frozen=True)
class Line:
    at: float
    text: str


def stamped(text: str) -> list[Line]:
    """`docker logs -t` 의 출력을 시각과 글로 가른다. 시각 차례로 세운다."""
    lines: list[Line] = []
    for row in text.splitlines():
        match = STAMP.match(row)
        at = epoch(row)
        if match is not None and at is not None:
            lines.append(Line(at, row[match.end() + 1 :]))
    lines.sort(key=lambda line: line.at)
    return lines


def logs(box: Box | None) -> list[Line]:
    """그 컨테이너의 기록 전부(표준 출력과 표준 오류). 다시 시작돼도 같은 컨테이너면 이어진다."""
    if box is None:
        return []
    done = inner("docker", "logs", "-t", box.id, timeout=60)
    return stamped(done.text) if done.code == 0 else []


@dataclass(frozen=True)
class Attempt:
    """serve.sh 가 찍은 시도 한 줄. at 은 줄이 찍힌 때(시도가 끝난 때)다."""

    at: float
    n: int
    since_ms: int
    took_ms: int
    ready_code: int
    ready: str
    query_code: int
    query: str


@dataclass
class Life:
    """serve.sh 가 한 번 떠서 끝날 때까지. 컨테이너가 다시 시작되면 삶이 하나 는다."""

    started: float
    retry: str
    attempts: list[Attempt] = field(default_factory=list[Attempt])
    connected: float | None = None
    connected_n: int = 0
    connected_ms: int = 0
    ended: str = ""

    def failures(self) -> list[Attempt]:
        return [attempt for attempt in self.attempts if attempt.query_code != 0]


START = re.compile(r"^probe-start mode=(\S+) host=(\S+) retry_seconds=(\S+)")
ATTEMPT = re.compile(
    r"^probe-attempt mode=\S+ n=(\d+) since_ms=(-?\d+) took_ms=(-?\d+) "
    r"ready_code=(\d+) ready=\[(.*?)\] query_code=(\d+) query=\[(.*)\]$"
)
CONNECTED = re.compile(r"^probe-connected mode=\S+ n=(\d+) since_ms=(-?\d+)")
ENDS: Mapping[str, str] = {
    "probe-giving-up": "다시 시도를 그만두고 1로 끝남",
    "probe-schema-behind": "표가 없어 3으로 끝남",
    "probe-term": "TERM 을 받음",
}


def lives_of(lines: Sequence[Line]) -> list[Life]:
    found: list[Life] = []
    for line in lines:
        start = START.match(line.text)
        if start:
            found.append(Life(started=line.at, retry=start.group(3)))
            continue
        if not found:
            continue
        life = found[-1]
        attempt = ATTEMPT.match(line.text)
        if attempt:
            numbers = [int(attempt.group(index)) for index in (1, 2, 3, 4, 6)]
            life.attempts.append(
                Attempt(
                    at=line.at,
                    n=numbers[0],
                    since_ms=numbers[1],
                    took_ms=numbers[2],
                    ready_code=numbers[3],
                    ready=attempt.group(5),
                    query_code=numbers[4],
                    query=attempt.group(7),
                )
            )
            continue
        connected = CONNECTED.match(line.text)
        if connected:
            life.connected = line.at
            life.connected_n = int(connected.group(1))
            life.connected_ms = int(connected.group(2))
            continue
        life.ended = next(
            (name for needle, name in ENDS.items() if line.text.startswith(needle)), life.ended
        )
    return found


def lives_in(box: Box | None) -> list[Life]:
    return lives_of(logs(box))


def plain(text: str) -> list[Line]:
    """시각이 없는 출력(`compose run`)을 줄로."""
    return [Line(0.0, row) for row in text.splitlines()]


KINDS: tuple[tuple[str, str], ...] = (
    ("could not translate host name", "이름을 풀지 못함"),
    ("Connection refused", "접속 거부"),
    ("the database system is starting up", "뜨는 중이라 거절"),
    ("the database system is in recovery mode", "복구 중이라 거절"),
    ("the database system is shutting down", "끄는 중이라 거절"),
    ("not yet accepting connections", "아직 받지 않음"),
    ("No route to host", "길 없음"),
    ("Host is unreachable", "길 없음"),
    ("timeout expired", "시간 초과"),
    ("server closed the connection unexpectedly", "서버가 끊음"),
    ("password authentication failed", "인증 실패"),
)
ADDRESS = re.compile(r"\d+\.\d+\.\d+\.\d+")


def kind(attempt: Attempt) -> str:
    if attempt.query_code == 0:
        return "성공"
    return next((name for needle, name in KINDS if needle in attempt.query), "그 밖")


def masked(text: str) -> str:
    return ADDRESS.sub("<주소>", text)


def kinds_text(attempts: Sequence[Attempt]) -> str:
    counts = Counter(f"{kind(attempt)}(pg_isready {attempt.ready_code})" for attempt in attempts)
    return ", ".join(f"{name} {count}" for name, count in counts.items()) or "없음"


PG_NEEDLES: Mapping[str, str] = {
    "ready": "database system is ready to accept connections",
    "interrupted": "database system was interrupted",
    "recovering": "automatic recovery in progress",
    "clean": "database system was shut down at",
    "redo": "redo done at",
    "skipped_init": "Skipping initialization",
    "init_done": "PostgreSQL init process complete",
}
STARTING_UP = "FATAL:  the database system is starting up"


def pg_firsts(lines: Sequence[Line], since: float) -> dict[str, float]:
    """PostgreSQL 기록에서 since 뒤 그 문구가 처음 나온 때."""
    found: dict[str, float] = {}
    for line in lines:
        if line.at < since:
            continue
        for name, needle in PG_NEEDLES.items():
            if needle in line.text and name not in found:
                found[name] = line.at
    return found


def how_stopped(firsts: Mapping[str, float]) -> str:
    if "interrupted" in firsts:
        return "중단 뒤 복구(database system was interrupted)"
    if "clean" in firsts:
        return "깨끗이 꺼졌다 켜짐(database system was shut down at)"
    return "기록에 없음"


def gap(later: float | None, earlier: float | None) -> float | None:
    return None if later is None or earlier is None else later - earlier


def secs(value: float | None) -> str:
    return "모름" if value is None else f"{value:.2f}초"


def spread(values: Sequence[float | None]) -> str:
    known = [value for value in values if value is not None]
    if not known:
        return "값 없음"
    middle = statistics.median(known)
    return f"최소 {min(known):.2f} / 중앙값 {middle:.2f} / 최대 {max(known):.2f}초 (n={len(known)})"


# ---------- 회차와 맥락 ----------


@dataclass
class Outcome:
    """항목 1·2 의 회차 하나에서 뽑은 수. 끝의 분포를 내는 재료다."""

    event: str
    retry: int
    serve_first: bool | None
    order: float | None
    attached: bool
    restarts: int
    lives: int
    serve_to_attach: float | None
    boot_to_attach: float | None
    pg_to_ready: float | None
    boot_to_ready: float | None
    serve_to_ready: float | None
    pg_to_tcp: float | None
    serve_to_tcp: float | None
    first_try: bool


type Phrase = tuple[str, str, str, str]


@dataclass
class Context:
    token: str
    rounds: Rounds
    dind_image: str
    work: Path
    repeat: int
    pg_image: str = PG_TAG
    tainted: str = ""
    count: int = 0
    outcomes: list[Outcome] = field(default_factory=list[Outcome])
    phrases: Counter[Phrase] = field(default_factory=Counter[Phrase])
    samples: dict[Phrase, str] = field(default_factory=dict[Phrase, str])

    def note(self) -> str:
        self.count += 1
        return f"kept-{self.token}-{self.count}"

    def stack(self, *files: str) -> Stack:
        return Stack(self.pg_image, files)

    def tally(self, source: str, attempts: Sequence[Attempt]) -> None:
        """실패한 시도의 문구를 명령마다 따로 모은다(한 시도 안에서 pg_isready 가 먼저, psql 이
        뒤에 돌아 둘이 본 상태가 다를 수 있다). 주소만 가리고, 가린 꼴마다 원문 하나를 남긴다."""
        for attempt in attempts:
            if attempt.query_code != 0:
                key = (source, "psql", kind(attempt), masked(attempt.query))
                self.phrases[key] += 1
                self.samples.setdefault(key, attempt.query)
            if attempt.ready_code != 0:
                code = f"종료 {attempt.ready_code}"
                key = (source, "pg_isready", code, masked(attempt.ready))
                self.phrases[key] += 1
                self.samples.setdefault(key, attempt.ready)

    def clean(self) -> bool:
        """안쪽 엔진에서 이 프로젝트의 것을 모두 지우고, 남은 것이 없는지 본다. 남았으면 그 뒤의
        회차를 믿지 않는다(tainted)."""
        if self.tainted:
            return False
        self.stack().compose("down", "-v", "--remove-orphans", "--timeout", "2", timeout=180)
        label = f"label=com.docker.compose.project={PROJECT}"
        left = shell(
            f"docker ps -aq --filter {label}; docker network ls -q --filter {label}; "
            f"docker volume ls -q --filter {label}"
        )
        if left.code != 0 or left.out.strip():
            self.tainted = f"정리 뒤에 남은 것(종료 {left.code}): {tail(left.text, 4)}"
            say(f"! 정리 실패. 이 뒤의 회차는 측정으로 세지 않는다: {self.tainted}")
            return False
        return True


@contextmanager
def case(ctx: Context, label: str) -> Generator[Slot]:
    """회차 하나를 세고 끝나면 한 줄로 낸다."""
    with ctx.rounds.round(label) as slot:
        yield slot
    entry = ctx.rounds.entries[-1]
    verdict = "측정" if entry.measured else "측정 아님"
    say(f"- [{verdict}] {entry.label} => {entry.result}")


def detail(text: str) -> None:
    say(f"    · {text}")


def query(box: Box | None, sql: str, *, timeout: float = 60) -> Done:
    """postgres 컨테이너 안에서 유닉스 소켓으로 SQL 하나를 친다."""
    if box is None:
        return Done(-1, "", "postgres 컨테이너가 없다")
    return inner("docker", "exec", box.id, *PSQL, "-c", sql, timeout=timeout)


def notes(box: Box | None) -> list[str] | None:
    """표의 줄(note)을 넣은 차례로. 읽지 못하면 None 이다."""
    done = query(box, "select note from probe_rows order by id")
    return done.out.split() if done.code == 0 else None


def has_table(box: Box | None) -> bool | None:
    done = query(box, "select to_regclass('public.probe_rows') is not null")
    answer = done.out.strip()
    return None if done.code != 0 or answer not in {"t", "f"} else answer == "t"


@dataclass(frozen=True)
class Baseline:
    """사건 전의 정상 상태."""

    boxes: dict[str, Box]
    lives: list[Life]
    note: str
    rows: list[str]
    first_try: bool


def settle(ctx: Context, stack: Stack, *, seconds: float = 120) -> dict[str, Box] | None:
    """배치를 지우고 새로 띄워, serve 대역이 붙은 것까지 본다."""
    if not ctx.clean():
        return None
    up = stack.compose("up", "-d", timeout=seconds + 60)
    if up.code != 0:
        say(f"! 기준선 up 실패(종료 {up.code}): {tail(up.err)}")
        return None
    deadline = time.monotonic() + seconds
    while True:
        now = boxes()
        lives = lives_in(now.get("serve"))
        if lives and lives[-1].connected is not None:
            return now
        if time.monotonic() >= deadline:
            say("! 기준선이 서지 않았다(serve 대역이 붙지 않았다)")
            return None
        time.sleep(0.5)


def baseline(ctx: Context, stack: Stack) -> Baseline | None:
    """새로 띄운 배치에 줄 하나를 넣고, 정상 상태의 표지(postgres 가 돌고, migrate 가 0으로 끝났고,
    serve 대역이 붙었고, 줄이 migrate 의 것과 넣은 것 둘)를 본다."""
    now = settle(ctx, stack)
    if now is None:
        return None
    note = ctx.note()
    postgres = now.get("postgres")
    query(postgres, f"insert into probe_rows (note) values ('{note}')")
    rows = notes(postgres)
    lives = lives_in(now.get("serve"))
    migrate = now.get("migrate")
    held = (
        is_running(now, "postgres")
        and is_running(now, "serve")
        and migrate is not None
        and migrate.status == "exited"
        and migrate.exit_code == 0
        and rows == ["migrate", note]
        and bool(lives)
    )
    if not held:
        states = {name: state_text(box) for name, box in now.items()}
        say(f"! 기준선의 표지가 서지 않았다. 컨테이너 {states}, 줄 {rows}")
        return None
    first_try = len(lives) == 1 and lives[0].connected_n == 1
    return Baseline(now, lives, note, rows or [], first_try)


# ---------- 사건 ----------


@dataclass(frozen=True)
class Happened:
    """사건 하나의 결과. ok 는 사건이 실제로 났다는 표지, boot 는 데몬(서버)이 다시 뜨기 시작한
    때(바깥 dockerd 의 시계)다."""

    ok: bool
    how: str
    boot: float | None


def dind_now() -> int:
    """dind 의 시계(초). 이벤트를 물을 때 쓴다."""
    text = shell("date +%s").out.strip()
    return int(text) if text.isdigit() else int(time.time()) - 5


def supervise_starts() -> list[Line]:
    """supervise.sh 가 dockerd 를 띄운 줄(바깥에서 본 dind 컨테이너의 기록)."""
    done = outer("logs", "-t", SESSION.dind, timeout=60)
    return [line for line in stamped(done.text) if line.text.startswith("supervise: dockerd start")]


def dockerd_pid() -> str:
    return shell("cat /var/run/docker.pid 2>/dev/null").out.strip()


def wait_inner(seconds: float) -> bool:
    """안쪽 dockerd 가 답할 때까지 기다린다."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if inner("docker", "info", "--format", "{{.ServerVersion}}", timeout=30).code == 0:
            return True
        time.sleep(0.5)
    return False


# dockerd 의 pid 파일을 읽고, 그 pid 의 이름이 dockerd 일 때만 TERM 을 보낸다(pid 만 보고 끄지
# 않는다). dind 컨테이너 자기 pid 이름공간 안의 일이다.
TERM_DOCKERD = (
    'pid="$(cat /var/run/docker.pid 2>/dev/null)"; '
    'name="$(cat "/proc/$pid/comm" 2>/dev/null)"; '
    'if [ -n "$pid" ] && [ "$name" = dockerd ]; then kill -TERM "$pid" && echo "sent $pid"; '
    'else echo "skip pid=$pid name=$name"; exit 3; fi'
)


def event_daemon() -> Happened:
    starts = supervise_starts()
    pid = dockerd_pid()
    sent = shell(TERM_DOCKERD)
    deadline = time.monotonic() + 120
    now = starts
    while time.monotonic() < deadline and len(now) <= len(starts):
        time.sleep(0.5)
        now = supervise_starts()
    ready = wait_inner(120)
    new_pid = dockerd_pid()
    ok = sent.code == 0 and len(now) > len(starts) and ready and bool(new_pid) and new_pid != pid
    how = f"dockerd 시작 횟수 {len(starts)}→{len(now)}, dockerd pid {pid}→{new_pid}"
    return Happened(ok, how, now[-1].at if len(now) > len(starts) else None)


def dind_started() -> str:
    done = outer("inspect", SESSION.dind, "--format", "{{.State.StartedAt}}", timeout=60)
    return done.out.strip()


def event_reboot() -> Happened:
    before = dind_started()
    done = outer("restart", "-t", "120", SESSION.dind, timeout=300)
    after = dind_started()
    ready = wait_inner(120)
    ok = done.code == 0 and bool(after) and after != before and ready
    return Happened(ok, f"dind 시작 시각 {before}→{after}", epoch(after))


def event_power() -> Happened:
    before = dind_started()
    killed = outer("kill", SESSION.dind, timeout=120)
    started = outer("start", SESSION.dind, timeout=120)
    after = dind_started()
    ready = wait_inner(120)
    ok = killed.code == 0 and started.code == 0 and bool(after) and after != before and ready
    return Happened(ok, f"dind 를 죽였다 켬, 시작 시각 {before}→{after}", epoch(after))


@dataclass(frozen=True)
class Event:
    key: str
    name: str
    act: Callable[[], Happened]


DAEMON = Event("daemon", "데몬만 다시 켬(dockerd 에 TERM)", event_daemon)
REBOOT = Event("reboot", "서버를 정상으로 껐다 켬(docker restart dind)", event_reboot)
POWER = Event("power", "전원 끊김(docker kill dind 뒤 start)", event_power)
EVENTS = (DAEMON, REBOOT, POWER)

LIST_STARTS = (
    "docker events --since {since} --until $(($(date +%s) + 1)) --filter type=container "
    f"--filter event=start --filter label=com.docker.compose.project={PROJECT} "
    "--format '{{{{json .}}}}'"
)


def first_starts(since: int) -> dict[str, float]:
    """안쪽 데몬의 이벤트에서 서비스마다 since 뒤 처음 시작된 때. 데몬이 다시 켜지면 그 전의
    이벤트는 없다. 이벤트는 데몬이 기억하는 만큼만 남는다."""
    done = shell(LIST_STARTS.format(since=since), timeout=30)
    found: dict[str, float] = {}
    for row in done.out.splitlines():
        info = parse(row)
        service = as_text(dig(info, "Actor", "Attributes", "com.docker.compose.service"))
        nano = as_int(dig(info, "timeNano"))
        if service and nano:
            at = nano / 1e9
            found[service] = min(at, found.get(service, at))
    return found


def earliest(first: Mapping[str, float], second: Mapping[str, float]) -> dict[str, float]:
    merged = dict(first)
    for name, at in second.items():
        merged[name] = min(at, merged.get(name, at))
    return merged


def wait_attached(known: int, *, seconds: float) -> tuple[dict[str, Box], list[Life]]:
    """serve 대역이 사건 뒤의 삶에서 붙을 때까지(또는 seconds 까지) 기다린다. known 은 사건 전의
    삶의 수다."""
    deadline = time.monotonic() + seconds
    while True:
        now = boxes()
        lives = lives_in(now.get("serve"))
        fresh = lives[known:]
        attached = bool(fresh) and fresh[-1].connected is not None
        if (attached and is_running(now, "postgres")) or time.monotonic() >= deadline:
            return now, lives
        time.sleep(1.0)


# ---------- 항목 0: 환경, 이미지 옮기기, 양성 대조 ----------


def image_facts(run_docker: Callable[..., Done], reference: str) -> str:
    done = run_docker(
        "image",
        "inspect",
        reference,
        "--format",
        "id={{.Id}} tags={{json .RepoTags}} digests={{json .RepoDigests}}",
        timeout=60,
    )
    return done.out.strip() if done.code == 0 else f"없음(종료 {done.code}: {tail(done.err, 1)})"


def inner_docker(*args: str, timeout: float = 120) -> Done:
    return inner("docker", *args, timeout=timeout)


def carry(ctx: Context, reference: str, name: str) -> tuple[Done, Done]:
    """바깥의 이미지를 `docker save` 로 내보내 dind 에 넣고 안쪽에서 `docker load` 한다."""
    archive = ctx.work / name
    saved = outer("save", "-o", str(archive), reference, timeout=600)
    if saved.code != 0:
        return saved, Done(-1, "", "save 가 실패해 load 하지 않았다")
    copied = outer("cp", str(archive), f"{SESSION.dind}:/{name}", timeout=600)
    archive.unlink(missing_ok=True)
    if copied.code != 0:
        return saved, Done(-1, "", f"dind 에 넣지 못했다: {tail(copied.err)}")
    loaded = inner("docker", "load", "-i", f"/{name}", timeout=600)
    shell(f"rm -f /{name}")
    return saved, loaded


def transfer(ctx: Context) -> bool:
    """PostgreSQL 이미지를 안쪽 엔진에 넣는다. digest 참조로 내보낸 것과 태그로 내보낸 것을 차례로
    넣어, 안쪽에서 무엇으로 가리킬 수 있는지 본다."""
    say(f"바깥의 이미지: {PG_TAG} {image_facts(outer, PG_TAG)}")
    say(f"바깥의 이미지: {PG_DIGEST} {image_facts(outer, PG_DIGEST)}")
    with case(ctx, "0 이미지 옮기기: digest 참조로 save 한 뒤 안쪽에서 load") as current:
        saved, loaded = carry(ctx, PG_DIGEST, "pg-by-digest.tar")
        by_digest = inner("docker", "image", "inspect", PG_DIGEST, timeout=60)
        listed = inner("docker", "image", "ls", "-a", "--digests", "--no-trunc", timeout=60)
        detail(f"load 의 출력: {tail(loaded.text, 2)}")
        detail(f"안쪽 `docker image ls -a --digests`: {tail(listed.out, 3)}")
        detail(f"안쪽에서 digest 참조로 inspect: {image_facts(inner_docker, PG_DIGEST)}")
        kept = "digest 참조가 남는다" if by_digest.code == 0 else "digest 참조가 사라진다"
        current.mark(measured=saved.code == 0 and loaded.code == 0, result=kept)
    with case(ctx, "0 이미지 옮기기: 태그로 save 한 뒤 안쪽에서 load") as current:
        saved, loaded = carry(ctx, PG_TAG, "pg-by-tag.tar")
        facts = image_facts(inner_docker, PG_TAG)
        version = inner(
            "docker", "run", "--rm", "--entrypoint", "postgres", PG_TAG, "--version", timeout=120
        )
        detail(f"load 의 출력: {tail(loaded.text, 2)}")
        detail(f"안쪽에서 태그로 inspect: {facts}")
        detail(f"안쪽에서 돌린 `postgres --version`: {version.out.strip()}")
        ran = version.code == 0 and "PostgreSQL) 18" in version.out
        if PG_DIGEST in facts:
            digests = "RepoDigests 에 원래 digest 가 남는다"
        elif "digests=[]" in facts:
            digests = "RepoDigests 가 비었다"
        else:
            digests = "RepoDigests 에 원래 것과 다른 digest 가 붙는다"
        current.mark(
            measured=saved.code == 0 and loaded.code == 0 and ran,
            result=f"태그로 가리켜 돈다, {digests}",
        )
        return ran


def versions(ctx: Context) -> None:
    facts = parse(outer("version", "--format", "{{json .}}", timeout=60).out)
    platform = as_text(dig(facts, "Server", "Platform", "Name"), "?")
    say(f"바깥 Docker: {platform}, 엔진 {as_text(dig(facts, 'Server', 'Version'), '?')}")
    say(f"dind 이미지: {ctx.dind_image} {image_facts(outer, ctx.dind_image)}")
    about = parse(inner("docker", "version", "--format", "{{json .}}", timeout=60).out)
    info = parse(inner("docker", "info", "--format", "{{json .}}", timeout=60).out)
    keys = ("OperatingSystem", "KernelVersion", "Driver", "CgroupVersion", "Architecture")
    described = ", ".join(f"{key} {as_text(dig(info, key), '?')}" for key in keys)
    compose = inner("docker", "compose", "version", "--short", timeout=60).out.strip()
    engine = as_text(dig(about, "Server", "Version"), "?")
    say(f"안쪽 Engine {engine}, Compose {compose}; {described}")
    say(f"안쪽의 PostgreSQL 이미지: {ctx.pg_image} {image_facts(inner_docker, ctx.pg_image)}")


def one_off(stack: Stack, *settings: str) -> tuple[Done, list[Life]]:
    """serve 대역을 한 번짜리 컨테이너로 돌리고 그 출력을 읽는다(`compose run --no-deps`)."""
    argv = ["run", "--rm", "-T", "--no-deps"]
    for setting in settings:
        argv += ["-e", setting]
    done = stack.compose(*argv, "serve", timeout=180)
    return done, lives_of(plain(done.out))


def controls(ctx: Context) -> None:
    """serve 대역이 붙음과 실패를 가려 적는다는 양성 대조."""
    stack = ctx.stack()
    base = settle(ctx, stack)
    with case(ctx, "0 대조: 붙을 수 있으면 붙고 0으로 끝난다") as current:
        done, lives = one_off(stack, "AFTER_CONNECT=exit", "RETRY_SECONDS=5")
        connected = bool(lives) and lives[-1].connected is not None
        detail(f"종료 {done.code}, 출력 끝: {tail(done.out, 1)}")
        current.mark(
            measured=base is not None and done.code == 0 and connected,
            result="붙고 0으로 끝남" if connected else f"붙지 못함(종료 {done.code})",
        )
    with case(ctx, "0 대조: 이름은 풀리는데 포트가 닫힌 곳(watch 컨테이너)") as current:
        done, lives = one_off(stack, "DB_HOST=watch", "RETRY_SECONDS=2")
        failures = lives[-1].failures() if lives else []
        ctx.tally("대조(닫힌 포트)", failures)
        refused = bool(failures) and all("Connection refused" in f.query for f in failures)
        gave_up = bool(lives) and lives[-1].ended == ENDS["probe-giving-up"]
        detail(f"종료 {done.code}, 시도 {len(failures)}번: {kinds_text(failures)}")
        detail(f"문구: {failures[0].ready} | {failures[0].query}" if failures else "문구 없음")
        current.mark(
            measured=base is not None and done.code == 1 and gave_up and refused,
            result="Connection refused 를 적고 1로 끝남" if refused else "다른 실패",
        )
    with case(ctx, "0 대조: postgres 컨테이너를 멈춰 둔 채(docker compose stop)") as current:
        stopped = stack.compose("stop", "postgres")
        held = not is_running(boxes(), "postgres")
        done, lives = one_off(stack, "RETRY_SECONDS=3")
        failures = lives[-1].failures() if lives else []
        ctx.tally("대조(멈춘 postgres)", failures)
        gave_up = bool(lives) and lives[-1].ended == ENDS["probe-giving-up"]
        took = [f"{attempt.took_ms}ms" for attempt in failures]
        detail(
            f"종료 {done.code}, 시도 {len(failures)}번: {kinds_text(failures)}, 걸린 시간 {took}"
        )
        detail(f"문구: {failures[0].ready} | {failures[0].query}" if failures else "문구 없음")
        current.mark(
            measured=stopped.code == 0 and held and done.code == 1 and gave_up and bool(failures),
            result=f"실패({kinds_text(failures[:1])})를 적고 1로 끝남",
        )


def section_0(ctx: Context) -> None:
    versions(ctx)
    controls(ctx)


# ---------- 항목 1·2: 복귀와 다시 시도하는 시간 ----------


def recover_round(ctx: Context, label: str, event: Event, retry: int) -> None:
    """새로 띄운 배치에서 사건 하나를 내고, 사람 손 없이 무엇이 돌아오는지 본다."""
    stack = ctx.stack().with_env({"RETRY_SECONDS": str(retry)})
    with case(ctx, label) as current:
        base = baseline(ctx, stack)
        if base is None:
            current.mark(measured=False, result=ctx.tainted or "기준선이 서지 않았다")
            return
        since = dind_now()
        happened = event.act()
        early = first_starts(since)
        after, lives = wait_attached(len(base.lives), seconds=120)
        starts = earliest(early, first_starts(since))
        fresh = lives[len(base.lives) :]
        postgres, serve, migrate = after.get("postgres"), after.get("serve"), after.get("migrate")
        rows = notes(postgres)
        pg_lines = logs(postgres)
        watch_lives = lives_in(after.get("watch"))

        pg_start = starts.get("postgres") or (postgres.started_at if postgres else None)
        serve_start = starts.get("serve") or (fresh[0].started if fresh else None)
        firsts = pg_firsts(pg_lines, (pg_start or 0.0) - 0.5) if pg_start else {}
        ready = firsts.get("ready")
        attached = bool(fresh) and fresh[-1].connected is not None
        attach_at = fresh[-1].connected if attached else None
        order = gap(serve_start, pg_start)
        failures = [attempt for life in fresh for attempt in life.failures()]
        ctx.tally(f"serve({event.key})", failures)
        seen = [a for life in watch_lives for a in life.attempts if pg_start and a.at >= pg_start]
        ctx.tally(f"watch({event.key})", seen)
        watch_ok = next((a.at for a in seen if a.query_code == 0), None)

        detail(f"사건: {happened.how}")
        states = ", ".join(
            f"{name} {change(base.boxes.get(name), after.get(name))}"
            for name in ("postgres", "migrate", "serve", "watch")
        )
        detail(f"컨테이너: {states}")
        source = "이벤트" if "serve" in starts and "postgres" in starts else "StartedAt·기록"
        detail(
            f"차례({source}): serve 의 첫 시작이 postgres 의 시작보다 "
            f"{'모름' if order is None else f'{order * 1000:+.0f}ms'}; "
            f"postgres 는 컨테이너 시작 뒤 {secs(gap(ready, pg_start))}에 ready, "
            f"{how_stopped(firsts)}"
        )
        ends = [life.ended or ("붙음" if life.connected else "도는 중") for life in fresh]
        tries = fresh[-1].connected_n if attached else 0
        restarts = serve.restarts if serve else -1
        detail(
            f"serve: 사건 뒤 삶 {len(fresh)}개 {ends}, 재시작 횟수 {restarts}"
            f", 처음 뜬 뒤 {secs(gap(attach_at, serve_start))}에 붙음(마지막 삶의 {tries}번째 시도)"
            f", 그 전의 실패 [{kinds_text(failures)}]"
        )
        detail(
            f"다시 뜨기 시작한 때부터: postgres ready {secs(gap(ready, happened.boot))}, "
            f"watch 의 첫 성공 {secs(gap(watch_ok, happened.boot))}, "
            f"serve 가 붙음 {secs(gap(attach_at, happened.boot))}"
        )
        detail(
            f"다른 컨테이너(watch)의 TCP 접속이 처음 된 때: postgres 컨테이너 시작 뒤 "
            f"{secs(gap(watch_ok, pg_start))}, serve 첫 시작 뒤 {secs(gap(watch_ok, serve_start))}"
        )
        detail(f"줄: 사건 전 {base.rows}, 사건 뒤 {rows}")

        migrate_same = (
            migrate is not None
            and migrate.status == "exited"
            and migrate.exit_code == 0
            and migrate.started == getattr(base.boxes.get("migrate"), "started", "")
        )
        problems: list[str] = []
        if not is_running(after, "postgres"):
            problems.append("postgres 가 돌아오지 않음")
        if not migrate_same or (rows is not None and rows.count("migrate") != 1):
            problems.append("migrate 가 다시 돎")
        if rows != base.rows:
            problems.append("줄이 달라짐")
        if order is None:
            who = "차례 모름"
        else:
            who = "serve 먼저 뜸" if order < 0 else "postgres 먼저 뜸"
        if not attached:
            how = "붙지 못함"
        elif len(fresh) == 1:
            how = "첫 삶에서 붙음"
        else:
            how = "재시작 정책으로 붙음"
        result = f"{event.key} N={retry}: {who}, {how}" + "".join(f", {p}!" for p in problems)

        marks = {
            "사건이 실제로 났다": happened.ok,
            "serve 가 사건 뒤 다시 떴다(기록의 새 삶)": bool(fresh),
        }
        if event.key == "power" and is_running(after, "postgres"):
            marks["PostgreSQL 기록에 복구 문구가 있다"] = "interrupted" in firsts
        missing = [name for name, held in marks.items() if not held]
        if missing:
            result = f"표지 없음 {missing}; {result}"
        current.mark(measured=not missing, result=result)
        if not missing:
            ctx.outcomes.append(
                Outcome(
                    event=event.key,
                    retry=retry,
                    serve_first=None if order is None else order < 0,
                    order=order,
                    attached=attached,
                    restarts=serve.restarts if serve else -1,
                    lives=len(fresh),
                    serve_to_attach=gap(attach_at, serve_start),
                    boot_to_attach=gap(attach_at, happened.boot),
                    pg_to_ready=gap(ready, pg_start),
                    boot_to_ready=gap(ready, happened.boot),
                    serve_to_ready=gap(ready, serve_start),
                    pg_to_tcp=gap(watch_ok, pg_start),
                    serve_to_tcp=gap(watch_ok, serve_start),
                    first_try=base.first_try,
                )
            )


def section_1(ctx: Context) -> None:
    for event in EVENTS:
        for index in range(ctx.repeat):
            recover_round(ctx, f"1 [{event.name}, N=30] {index + 1}번째", event, 30)


def section_2(ctx: Context) -> None:
    for retry in (0, 5):
        for event in EVENTS:
            for index in range(ctx.repeat):
                recover_round(ctx, f"2 [{event.name}, N={retry}] {index + 1}번째", event, retry)


def report(ctx: Context) -> None:
    """항목 1·2 의 측정인 회차를 모아 분포를 낸다."""
    if not ctx.outcomes:
        return
    say("")
    say("## 항목 1·2 의 분포(측정인 회차만)")
    first_try = sum(1 for outcome in ctx.outcomes if outcome.first_try)
    say(f"처음 `up -d` 에서 serve 대역이 첫 시도에 붙은 회차: {first_try}/{len(ctx.outcomes)}")
    for event in EVENTS:
        rows = [outcome for outcome in ctx.outcomes if outcome.event == event.key]
        if not rows:
            continue
        early = sum(1 for outcome in rows if outcome.serve_first is True)
        late = sum(1 for outcome in rows if outcome.serve_first is False)
        say(f"[{event.name}] 회차 {len(rows)}: serve 먼저 뜸 {early}, postgres 먼저 뜸 {late}")
        say(f"  serve 첫 시작 − postgres 시작: {spread([o.order for o in rows])}")
        say(f"  postgres 컨테이너 시작 → ready: {spread([o.pg_to_ready for o in rows])}")
        say(f"  다시 뜨기 시작 → postgres ready: {spread([o.boot_to_ready for o in rows])}")
        say(f"  serve 첫 시작 → postgres ready: {spread([o.serve_to_ready for o in rows])}")
        say(f"  postgres 컨테이너 시작 → TCP 첫 성공: {spread([o.pg_to_tcp for o in rows])}")
        say(f"  serve 첫 시작 → TCP 첫 성공: {spread([o.serve_to_tcp for o in rows])}")
        for retry in sorted({outcome.retry for outcome in rows}):
            picked = [outcome for outcome in rows if outcome.retry == retry]
            attached = sum(1 for outcome in picked if outcome.attached)
            say(
                f"  N={retry}: 붙음 {attached}/{len(picked)}, "
                f"재시작 횟수 {[o.restarts for o in picked]}, 삶 {[o.lives for o in picked]}, "
                f"serve 첫 시작 → 붙음 {spread([o.serve_to_attach for o in picked])}, "
                f"다시 뜨기 시작 → 붙음 {spread([o.boot_to_attach for o in picked])}"
            )
    waits = spread([outcome.serve_to_ready for outcome in ctx.outcomes])
    boots = spread([outcome.pg_to_ready for outcome in ctx.outcomes])
    tcp = spread([outcome.serve_to_tcp for outcome in ctx.outcomes])
    attach = spread([o.serve_to_attach for o in ctx.outcomes if o.retry == 30])
    say(f"[모든 사건] serve 첫 시작 → postgres ready: {waits}")
    say(f"[모든 사건] postgres 컨테이너 시작 → ready: {boots}")
    say(f"[모든 사건] serve 첫 시작 → TCP 첫 성공: {tcp}")
    say(f"[모든 사건, N=30] serve 첫 시작 → 붙음: {attach}")


def report_phrases(ctx: Context) -> None:
    if not ctx.phrases:
        return
    say("")
    say("## 실패한 시도의 문구(주소만 가려 같은 꼴을 모았다. 적은 글은 꼴마다 원문 하나)")
    for key, count in sorted(ctx.phrases.items()):
        source, command, name, _ = key
        say(f"- [{source}] {command} {name}, {count}번: {ctx.samples[key]}")


# ---------- 항목 3: PostgreSQL 만 죽을 때 ----------

BULK = (
    "create table probe_bulk as select g as id, repeat('x', 200) as pad "
    "from generate_series(1, 1500000) g"
)


@dataclass(frozen=True)
class Blow:
    key: str
    name: str
    watch: float


DOCKER_KILL = Blow("docker kill", "`docker kill` postgres", 25)
CRASH = Blow("crash", "postmaster 를 바깥에서 KILL(Docker 가 시키지 않은 죽음)", 60)
DOCKER_STOP = Blow("docker stop", "`docker stop` postgres(대조)", 25)


def strike(blow: Blow, box: Box) -> Done:
    if blow.key == "docker kill":
        return inner("docker", "kill", box.id, timeout=60)
    if blow.key == "docker stop":
        return inner("docker", "stop", "-t", "10", box.id, timeout=60)
    return inner("sh", f"{REMOTE}/crash.sh", box.id, timeout=60)


def lone_round(ctx: Context, label: str, blow: Blow, *, bulk: bool) -> None:
    """정상 상태에서 postgres 컨테이너만 죽이고, 사람 손 없이 돌아오는지와 다른 컨테이너를 본다."""
    stack = ctx.stack().with_env({"RETRY_SECONDS": "30"})
    with case(ctx, label) as current:
        base = baseline(ctx, stack)
        if base is None:
            current.mark(measured=False, result=ctx.tainted or "기준선이 서지 않았다")
            return
        before = base.boxes["postgres"]
        loaded = query(before, BULK, timeout=300) if bulk else Done(0, "", "")
        serve_lines = len(logs(base.boxes.get("serve")))
        done = strike(blow, before)
        deadline = time.monotonic() + blow.watch
        seen_down = False
        while True:
            now = boxes()
            postgres = now.get("postgres")
            died = postgres is not None and postgres.finished != before.finished
            seen_down = seen_down or died
            pg_lines = logs(postgres)
            killed_at = postgres.finished_at if postgres and died else None
            firsts = pg_firsts(pg_lines, killed_at) if killed_at else {}
            back = died and is_running(now, "postgres") and "ready" in firsts
            if (back and blow.key == "crash") or time.monotonic() >= deadline:
                break
            time.sleep(1.0)
        time.sleep(3.0)  # 돌아온 뒤 watch 가 몇 번 더 시도하게 둔다
        now = boxes()
        postgres, serve = now.get("postgres"), now.get("serve")
        rows = notes(postgres) if is_running(now, "postgres") else None
        watch_attempts = [
            attempt
            for life in lives_in(now.get("watch"))
            for attempt in life.attempts
            if killed_at is not None and attempt.at >= killed_at
        ]
        ctx.tally(f"watch({blow.key}{', WAL' if bulk else ''})", watch_attempts)
        failed = [attempt for attempt in watch_attempts if attempt.query_code != 0]
        watch_ok = next((a.at for a in watch_attempts if a.query_code == 0), None)
        refused = sum(
            1
            for line in pg_lines
            if killed_at and line.at >= killed_at and STARTING_UP in line.text
        )
        serve_same = (
            serve is not None
            and serve.started == base.boxes["serve"].started
            and serve.restarts == base.boxes["serve"].restarts
            and len(logs(serve)) == serve_lines
        )
        restarted_at = postgres.started_at if postgres and back else None

        detail(f"명령: 종료 {done.code}, {tail(done.text, 1)}")
        detail(f"postgres: {change(before, postgres)}, serve: {change(base.boxes['serve'], serve)}")
        detail(
            f"죽은 때부터: 컨테이너 다시 시작 {secs(gap(restarted_at, killed_at))}, "
            f"ready {secs(gap(firsts.get('ready'), killed_at))}, "
            f"watch 의 첫 성공 {secs(gap(watch_ok, killed_at))}; {how_stopped(firsts)}"
        )
        detail(
            f"watch 가 그 뒤 본 실패 {len(failed)}번 [{kinds_text(failed)}]; "
            f"PostgreSQL 기록의 `the database system is starting up` 거절 {refused}줄"
        )
        same_text = "그대로(시작 시각, 재시작 횟수, 기록 줄 수)" if serve_same else "달라짐"
        detail(f"serve 대역은 {same_text}")
        detail(f"줄: 죽이기 전 {base.rows}, 뒤 {rows}")

        if back:
            verdict = "재시작 정책이 다시 띄움"
            if rows != base.rows:
                verdict += ", 줄이 달라짐!"
        else:
            verdict = f"다시 뜨지 않음({state_text(postgres)})"
        verdict += ", serve 그대로" if serve_same else ", serve 달라짐"
        if blow.key == "crash":
            verdict += f", starting up 거절 {'봄' if refused else '못 봄'}"
        marks = {
            "명령이 닿았다": done.code == 0,
            "postgres 컨테이너가 실제로 끝났다": seen_down,
            "watch 가 그 뒤 시도를 적었다": bool(watch_attempts),
        }
        if bulk:
            marks["WAL 을 쌓는 표를 만들었다"] = loaded.code == 0
        if blow.key == "crash" and back:
            marks["PostgreSQL 기록에 복구 문구가 있다"] = "interrupted" in firsts
        missing = [name for name, held in marks.items() if not held]
        result = f"{blow.key}{', WAL 쌓은 뒤' if bulk else ''}: {verdict}"
        if missing:
            result = f"표지 없음 {missing}; {result}"
        current.mark(measured=not missing, result=result)


def section_3(ctx: Context) -> None:
    for index in range(2):
        lone_round(ctx, f"3 [{DOCKER_KILL.name}] {index + 1}번째", DOCKER_KILL, bulk=False)
    for index in range(ctx.repeat):
        lone_round(ctx, f"3 [{CRASH.name}] {index + 1}번째", CRASH, bulk=False)
    for index in range(2):
        lone_round(ctx, f"3 [{CRASH.name}, WAL 을 쌓은 뒤] {index + 1}번째", CRASH, bulk=True)
    for index in range(2):
        lone_round(ctx, f"3 [{DOCKER_STOP.name}] {index + 1}번째", DOCKER_STOP, bulk=False)


# ---------- 항목 4: 처음 띄우기가 끊긴 경우 ----------


def wait_state(service: str, wanted: Callable[[Box], bool], *, seconds: float) -> dict[str, Box]:
    deadline = time.monotonic() + seconds
    while True:
        now = boxes()
        box = now.get(service)
        if (box is not None and wanted(box)) or time.monotonic() >= deadline:
            return now
        time.sleep(0.2)


def dind_clock() -> float | None:
    """dind 의 시계(초, 소수). 안쪽 기록의 시각과 같은 커널 시계다. 읽지 못하면 None 이다."""
    text = shell("date +%s.%N").out.strip()
    try:
        return float(text)
    except ValueError:
        return None


# 끊긴 초기화의 데이터 폴더로 뜬 PostgreSQL 이 내는 문구. 앞선 실행에서 둘 다 봤다. 앞의 것은
# initdb 가 끝나기 전에, 뒤의 둘은 initdb 뒤 진입점의 남은 일(pg_hba.conf 의 줄, 데이터베이스
# 만들기) 전에 끊긴 데이터 폴더에서 났다.
BROKEN_INIT = (
    'could not open file "global/pg_filenode.map"',
    'database "agent_os" does not exist',
    "no pg_hba.conf entry",
)


def attach_again(stack: Stack, *args: str) -> tuple[Done, dict[str, Box], list[Life], bool]:
    """compose 명령 하나를 치고 serve 대역이 새 삶에서 붙는지 본다."""
    known = len(lives_in(boxes().get("serve")))
    done = stack.compose(*args, timeout=240)
    now, lives = wait_attached(known, seconds=90)
    attached = len(lives) > known and lives[-1].connected is not None
    return done, now, lives, attached


def cut_round(ctx: Context, label: str, event: Event, *, when: str) -> None:
    """`up -d` 가 도는 중에 사건을 낸다. when 이 init 이면 postgres 컨테이너가 뜨자마자(초기화
    중), migrate 면 migrate 대역이 뜬 뒤 일을 하기 전(MIGRATE_DELAY 로 잠든 동안)이다."""
    delay = "45" if when == "migrate" else "0"
    env = {"MIGRATE_DELAY": delay, "REQUIRE_TABLE": "1", "RETRY_SECONDS": "30"}
    stack = ctx.stack().with_env(env)
    with case(ctx, label) as current:
        if not ctx.clean():
            current.mark(measured=False, result=ctx.tainted)
            return
        process = stack.spawn("up", "-d")
        target = "postgres" if when == "init" else "migrate"
        before = wait_state(target, lambda box: box.running, seconds=120)
        cut_at = dind_clock()
        happened = event.act()
        code, output = finish(process, seconds=120)
        time.sleep(40.0)  # 사람 손 없이 지켜본다
        now = boxes()
        postgres, migrate, serve = now.get("postgres"), now.get("migrate"), now.get("serve")
        pg_lines = logs(postgres)
        lives = lives_in(serve)
        table = has_table(postgres)
        alive = query(postgres, "select 1")
        endings = Counter(life.ended or ("붙음" if life.connected else "도는 중") for life in lives)
        failures = [attempt for life in lives for attempt in life.failures()]
        ctx.tally(f"serve(처음 띄우기 끊김, {event.key})", failures)
        done_at = next((ln.at for ln in pg_lines if PG_NEEDLES["init_done"] in ln.text), None)
        skipped = any(PG_NEEDLES["skipped_init"] in line.text for line in pg_lines)
        fatal = [line.text for line in pg_lines if "FATAL" in line.text or "PANIC" in line.text]
        broken = {
            needle: sum(1 for line in pg_lines if needle in line.text) for needle in BROKEN_INIT
        }
        # 첫 삶(끊긴 초기화)의 마지막 줄. 다시 뜬 삶은 `Skipping initialization` 으로 시작한다.
        first_life: list[str] = []
        for line in pg_lines:
            if PG_NEEDLES["skipped_init"] in line.text:
                break
            if line.text.strip():
                first_life.append(line.text.strip())
        stage = first_life[-1] if first_life else "(기록 없음)"
        during_init = cut_at is not None and (done_at is None or done_at > cut_at)

        detail(f"사건: {happened.how}")
        detail(
            "사건 직전: " + ", ".join(f"{name} {state_text(before.get(name))}" for name in before)
        )
        detail(
            f"postgres 의 첫 삶(`Skipping initialization` 전)의 마지막 줄: {stage}"
            f" (첫 삶 {len(first_life)}줄)"
        )
        detail(
            f"초기화 끝 문구(PostgreSQL init process complete): "
            f"{'없음' if done_at is None else f'사건 뒤 {secs(gap(done_at, cut_at))}'}"
        )
        detail(f"`up -d` 는 종료 {code}: {tail(output, 2)}")
        detail(
            "40초 뒤: "
            + ", ".join(
                f"{name} {state_text(box)}(재시작 {box.restarts}, 상태 확인 {box.health or '-'})"
                for name, box in now.items()
            )
        )
        detail(
            f"postgres 기록: `Skipping initialization` {'있음' if skipped else '없음'}, "
            + ", ".join(f"`{needle}` {count}줄" for needle, count in broken.items())
            + f", FATAL·PANIC {len(fatal)}줄 {fatal[-1:]}; "
            f"agent_os 로 `select 1` 종료 {alive.code}({tail(alive.err, 1)})"
        )
        detail(
            f"serve: 삶 {len(lives)}개 {dict(endings)}, 실패 [{kinds_text(failures)}]; "
            f"표(probe_rows) {'있음' if table else '없음' if table is False else '모름'}"
        )
        migrate_ran = migrate is not None and migrate.started_at is not None
        serve_ran = bool(lives)

        fixed, mended, _, mended_ok = attach_again(stack, "up", "-d")
        rows = notes(mended.get("postgres"))
        detail(
            f"그 뒤 `docker compose up -d` 를 다시 침: 종료 {fixed.code}({tail(fixed.err, 1)}), "
            + ", ".join(f"{name} {state_text(box)}" for name, box in mended.items())
            + f", serve 가 붙음 {mended_ok}, 줄 {rows}"
        )
        kept_ok: bool | None = None
        wiped_ok: bool | None = None
        if not mended_ok:
            # 볼륨이 까닭인지 가르는 갈래. 컨테이너와 네트워크만 지우고 다시 띄우는 것(볼륨은
            # 남는다)과, 볼륨까지 지우고 다시 띄우는 것을 차례로 본다.
            stack.compose("down", "--timeout", "2", timeout=180)
            again, kept, _, kept_ok = attach_again(stack, "up", "-d")
            detail(
                f"`docker compose down`(볼륨은 남김) 뒤 `up -d`: 종료 {again.code}"
                f"({tail(again.err, 1)}), "
                + ", ".join(f"{name} {state_text(box)}" for name, box in kept.items())
                + f", serve 가 붙음 {kept_ok}"
            )
        if not mended_ok and not kept_ok:
            stack.compose("down", "-v", "--timeout", "2", timeout=180)
            again, wiped, _, wiped_ok = attach_again(stack, "up", "-d")
            detail(
                f"`docker compose down -v` 뒤 `up -d`: 종료 {again.code}, "
                + ", ".join(f"{name} {state_text(box)}" for name, box in wiped.items())
                + f", serve 가 붙음 {wiped_ok}, 줄 {notes(wiped.get('postgres'))}"
            )

        if serve_ran and table is False:
            verdict = "표 없이 serve 대역만 떠서 돎"
        elif serve_ran:
            verdict = "serve 대역이 뜸(표 있음)"
        else:
            verdict = "serve 대역은 뜨지 않음"
        verdict += f", migrate {'돈 적 있음' if migrate_ran else '돈 적 없음'}"
        verdict += f"({state_text(migrate)})"
        seen = [needle for needle, count in broken.items() if count]
        if seen:
            verdict += f", PostgreSQL 이 끊긴 초기화의 데이터 폴더로 뜸({' / '.join(seen)})"
        if mended_ok and rows == ["migrate"]:
            verdict += ", 다시 up 하면 붙음"
        elif mended_ok:
            verdict += f", 다시 up 하면 붙지만 줄이 {rows}"
        elif kept_ok:
            verdict += ", 다시 up 해선 안 붙고 컨테이너를 지우고 띄우면 붙음"
        elif wiped_ok:
            verdict += ", 다시 up 해도, 컨테이너만 지우고 띄워도 안 붙고 볼륨을 지워야 붙음"
        else:
            verdict += ", 볼륨을 지워도 안 붙음"
        marks = {
            "사건이 실제로 났다": happened.ok,
            "사건 때 migrate 가 일을 마치지 않았다(40초 뒤 표가 없거나 읽지 못함)": table
            is not True,
            "사건 직전 그 컨테이너가 돌고 있었다": is_running(before, target),
        }
        if when == "init":
            marks["사건이 초기화 도중에 왔다(초기화 끝 문구가 사건 전에 없다)"] = during_init
        missing = [name for name, held in marks.items() if not held]
        result = f"{when}, {event.key}: {verdict}"
        if missing:
            result = f"표지 없음 {missing}; {result}"
        current.mark(measured=not missing, result=result)


def section_4(ctx: Context) -> None:
    for index in range(2):
        cut_round(ctx, f"4 [초기화 중, {DAEMON.name}] {index + 1}번째", DAEMON, when="init")
    for index in range(max(2, ctx.repeat)):
        cut_round(ctx, f"4 [초기화 중, {POWER.name}] {index + 1}번째", POWER, when="init")
    cut_round(ctx, f"4 [migrate 가 일하기 전, {DAEMON.name}]", DAEMON, when="migrate")


# ---------- 항목 5: 좁힌 권한 ----------


def section_5(ctx: Context) -> None:
    stack = ctx.stack("compose.narrow.yml").with_env({"RETRY_SECONDS": "30"})
    up_ok = False
    with case(ctx, "5 [좁힌 권한] 처음 띄우기") as current:
        if not ctx.clean():
            current.mark(measured=False, result=ctx.tainted)
            return
        up = stack.compose("up", "-d", timeout=240)
        now, lives = wait_attached(0, seconds=30 if up.code == 0 else 1)
        postgres = now.get("postgres")
        applied = (
            postgres is not None
            and postgres.user == "999:999"
            and postgres.read_only
            and "ALL" in postgres.cap_drop
            and any("no-new-privileges" in item for item in postgres.security)
        )
        attached = bool(lives) and lives[-1].connected is not None
        who = inner("docker", "exec", getattr(postgres, "id", ""), "id", timeout=60)
        touch = inner("docker", "exec", getattr(postgres, "id", ""), "touch", "/probe-ro")
        pg_lines = logs(postgres)
        detail(
            f"`up -d` 종료 {up.code}({tail(up.err, 1)}); "
            + ", ".join(f"{name} {state_text(box)}" for name, box in now.items())
        )
        detail(
            f"postgres 설정: user={getattr(postgres, 'user', '')} "
            f"read_only={getattr(postgres, 'read_only', '')} "
            f"cap_drop={getattr(postgres, 'cap_drop', '')} "
            f"security={getattr(postgres, 'security', '')}"
        )
        detail(f"컨테이너 안 `id`: {who.out.strip()}; 루트에 쓰기: {tail(touch.text, 1)}")
        detail(f"postgres 기록의 끝: {' / '.join(line.text for line in pg_lines[-3:])}")
        up_ok = up.code == 0 and attached and is_running(now, "postgres")
        read_only = "Read-only file system" in touch.text
        result = "뜨고 serve 대역이 붙음" if up_ok else f"뜨지 않음(up 종료 {up.code})"
        marks = {"좁힌 설정이 컨테이너에 걸렸다": applied}
        if up_ok:
            marks["루트 파일 시스템이 실제로 읽기 전용이다"] = read_only
            marks["uid 999 로 돈다"] = "uid=999" in who.out
        missing = [name for name, held in marks.items() if not held]
        if missing:
            result = f"표지 없음 {missing}; {result}"
        current.mark(measured=not missing, result=result)
    if not up_ok:
        say("  (처음 띄우기가 되지 않아 데몬 재시작 갈래는 돌리지 않는다)")
        return
    with case(ctx, f"5 [좁힌 권한] {DAEMON.name}") as current:
        before = boxes()
        known = lives_in(before.get("serve"))
        note = ctx.note()
        query(before.get("postgres"), f"insert into probe_rows (note) values ('{note}')")
        rows_before = notes(before.get("postgres"))
        happened = DAEMON.act()
        after, lives = wait_attached(len(known), seconds=120)
        postgres = after.get("postgres")
        rows = notes(postgres)
        fresh = lives[len(known) :]
        attached = bool(fresh) and fresh[-1].connected is not None
        firsts = pg_firsts(logs(postgres), (postgres.started_at or 0.0) - 0.5) if postgres else {}
        detail(f"사건: {happened.how}")
        detail(
            ", ".join(f"{name} {change(before.get(name), box)}" for name, box in after.items())
            + f"; {how_stopped(firsts)}"
        )
        detail(f"줄: 사건 전 {rows_before}, 뒤 {rows}")
        back = attached and is_running(after, "postgres") and rows == rows_before
        current.mark(
            measured=happened.ok and rows_before is not None and note in rows_before,
            result="돌아오고 serve 대역이 붙음, 줄 그대로" if back else "돌아오지 않음",
        )


# ---------- dind 의 삶 ----------


def label_of(kind_name: str, name: str) -> str | None:
    """그 이름의 컨테이너(container)나 볼륨(volume)이 있으면 이 프로브의 표지 값을, 없으면 None."""
    template = (
        '{{index .Config.Labels "%s"}}' if kind_name == "container" else '{{index .Labels "%s"}}'
    )
    done = outer(kind_name, "inspect", name, "--format", template % MARK, timeout=60)
    return done.out.strip() if done.code == 0 else None


def dind_down(token: str) -> bool:
    """이 실행의 dind 컨테이너와 볼륨을 지운다. 이 프로브의 표지가 그 실행의 값일 때만 지우고,
    지워졌는지까지 본다."""
    for kind_name, name, remove in (
        ("container", SESSION.dind, ("rm", "-f", "-v", SESSION.dind)),
        ("volume", SESSION.volume, ("volume", "rm", SESSION.volume)),
    ):
        mark = label_of(kind_name, name)
        if mark is None:
            continue
        if mark != token or not name.startswith(f"{PREFIX}-"):
            say(f"! {kind_name} {name} 에 이 실행의 표지가 없다. 건드리지 않는다.")
            return False
        outer(*remove, timeout=180)
        if label_of(kind_name, name) is not None:
            say(f"! {kind_name} {name} 를 지우지 못했다.")
            return False
    return True


def reusable() -> str | None:
    """--reuse 가 다시 쓸, 떠 있는 dind 컨테이너의 무작위 접미사. 하나일 때만 돌려준다."""
    listed = outer(
        "ps", "--filter", f"label={MARK}", "--format", "{{.Names}}", timeout=60
    ).out.split()
    names = [name for name in listed if name.startswith(f"{PREFIX}-dind-")]
    return names[0].removeprefix(f"{PREFIX}-dind-") if len(names) == 1 else None


def dind_up(ctx: Context, *, reuse: bool) -> bool:
    for name in LINE_ENDING_FILES:
        if b"\r" in (HERE / name).read_bytes():
            say(f"! {name} 의 줄 끝이 CRLF 다. dind 안의 sh 가 읽지 못한다.")
            return False
    if outer("image", "inspect", ctx.dind_image, "--format", "{{.Id}}", timeout=60).code != 0:
        say(f"! dind 이미지 {ctx.dind_image} 가 이 PC 에 없다. 받지 않고 멈춘다.")
        return False
    pinned = outer("image", "inspect", PG_DIGEST, "--format", "{{.Id}}", timeout=60)
    if pinned.code != 0:
        say(f"! PostgreSQL 이미지 {PG_DIGEST} 가 이 PC 에 없다. 받지 않고 멈춘다.")
        return False
    # 안쪽은 태그로 옮긴 이미지로 돈다(항목 0). 그 태그가 digest 와 다른 이미지면 엉뚱한 판을 잰다.
    tagged = outer("image", "inspect", PG_TAG, "--format", "{{.Id}}", timeout=60)
    if tagged.code != 0 or tagged.out.strip() != pinned.out.strip():
        say(f"! 이 PC 의 {PG_TAG} 가 {PG_DIGEST} 와 같은 이미지가 아니다. 멈춘다.")
        return False
    found = reusable() if reuse else None
    if found is not None:
        ctx.token = found
        say(f"있는 dind 컨테이너를 다시 쓴다(--reuse): {PREFIX}-dind-{found}")
    SESSION.dind = f"{PREFIX}-dind-{ctx.token}"
    SESSION.volume = f"{PREFIX}-data-{ctx.token}"
    if found is None:
        label = ("--label", f"{MARK}={ctx.token}")
        created = outer("volume", "create", *label, SESSION.volume, timeout=60)
        if created.code != 0:
            say(f"! 볼륨을 만들지 못했다: {tail(created.err)}")
            return False
        create = ("create", "--privileged", "--init", "--name", SESSION.dind, *label)
        mounts = ("--tmpfs", "/run:exec", "-v", f"{SESSION.volume}:/var/lib/docker")
        command = ("--entrypoint", "sh", ctx.dind_image, f"{REMOTE}/supervise.sh")
        made = outer(*create, *mounts, *command, timeout=120)
        if made.code != 0:
            say(f"! dind 컨테이너를 만들지 못했다: {tail(made.err)}")
            return False
    copied = outer("cp", f"{HERE}/.", f"{SESSION.dind}:{REMOTE}", timeout=120)
    if copied.code != 0:
        say(f"! 프로브 파일을 dind 에 넣지 못했다: {tail(copied.err)}")
        return False
    if found is None and outer("start", SESSION.dind, timeout=120).code != 0:
        say("! dind 컨테이너를 시작하지 못했다.")
        return False
    if not wait_inner(180):
        recent = outer("logs", "--tail", "20", SESSION.dind).text
        say(f"! 안쪽 dockerd 가 답하지 않는다: {tail(recent, 6)}")
        return False
    return True


def image_ready(ctx: Context) -> bool:
    """안쪽 엔진에 PostgreSQL 이미지가 있게 한다. 없으면 옮기고(회차 둘), 있으면 다시 쓴다."""
    if inner("docker", "image", "inspect", PG_TAG, "--format", "{{.Id}}", timeout=60).code == 0:
        say(f"안쪽 엔진에 {PG_TAG} 가 이미 있다. 옮기지 않는다(옮기기 회차는 새 dind 에서만 돈다).")
        return True
    return transfer(ctx)


SECTIONS: Mapping[str, Callable[[Context], None]] = {
    "0": section_0,
    "1": section_1,
    "2": section_2,
    "3": section_3,
    "4": section_4,
    "5": section_5,
}


def main() -> int:
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--sections", default=",".join(SECTIONS))
    parser.add_argument(
        "--rounds", type=int, default=3, help="갈래마다 되풀이하는 횟수(항목 1·2·3)"
    )
    parser.add_argument("--dind-image", default=DIND_IMAGE)
    parser.add_argument("--work", type=Path)
    parser.add_argument("--reuse", action="store_true", help="떠 있는 dind 컨테이너를 다시 쓴다")
    parser.add_argument("--keep", action="store_true", help="끝나도 dind 컨테이너를 지우지 않는다")
    args = parser.parse_args()
    chosen = [name for name in str(args.sections).split(",") if name]
    unknown = [name for name in chosen if name not in SECTIONS]
    if unknown or not chosen or int(args.rounds) < 1:
        # 알 수 없는 항목이나 빈 선택은 Docker 자원을 만들기 전에 막는다.
        parser.error(f"알 수 없거나 빈 --sections {unknown}, 항목은 {list(SECTIONS)}")
    if args.work is not None:
        Path(args.work).mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="restart-recover-", dir=args.work))
    SESSION.raw = work / "raw.log"
    ctx = Context(
        token=secrets.token_hex(3),
        rounds=Rounds(),
        dind_image=str(args.dind_image),
        work=work,
        repeat=int(args.rounds),
    )
    say(f"원본 출력 {SESSION.raw}, 호스트 {sys.platform}, 항목 {chosen}, 되풀이 {ctx.repeat}")
    removed = True
    made = False
    try:
        made = dind_up(ctx, reuse=bool(args.reuse))
        say(f"회차 토큰 {ctx.token}, dind 컨테이너 {SESSION.dind}")
        if not made or not image_ready(ctx):
            return 2
        for name in chosen:
            SECTIONS[name](ctx)
        with case(ctx, "끝 정리(안쪽 엔진에 이 프로젝트의 것이 남지 않았다)") as current:
            current.mark(measured=ctx.clean(), result=ctx.tainted or "남은 것 없음")
    finally:
        if not args.keep and SESSION.dind:
            removed = dind_down(ctx.token)
    if not args.keep:
        ctx.rounds.record(
            "끝 정리(dind 컨테이너와 볼륨을 지웠다)",
            measured=removed,
            result="지웠다" if removed else "지우지 못했다",
        )
    report(ctx)
    report_phrases(ctx)
    say("")
    say(ctx.rounds.summary())
    return ctx.rounds.exit_code()


if __name__ == "__main__":
    sys.exit(main())
