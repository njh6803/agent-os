"""widget-runtime-values 명세가 결정을 내리려고, 미리 지어 둔 위젯 이미지의 컨테이너가 뜰 때 사이트
파일의 두 값(허용 출처, 요청 글자 수 상한)만 받아 서는지를 리눅스 컨테이너에서 잰다. 결정은 하지
않고 회차마다 본 것을 한 줄씩 낸다.

저장소 루트에서

    uv run python .scratch/widget-runtime-values/probes/prebuilt_start/run.py --sections build
    uv run python .scratch/widget-runtime-values/probes/prebuilt_start/run.py
        --sections start,reflect,readonly,sitefile,health,browser [--rounds <되풀이 수>]
        [--work <폴더>]

재는 꼴. 시제품 Dockerfile 이 위젯을 이미지를 지을 때 사이트 파일 없이 한 번 빌드해 둔다(응답 머리는
frame-ancestors 'none'). 컨테이너가 뜰 때 진입 단계(entry.mjs)가 사이트 파일을 읽어 두 가지만 한다.
지어 둔 routes-manifest 원본에서 frame-ancestors 값을 바꿔 뜰 때 쓰는 파일에 쓰고, 값 파일
(public/runtime.json)을 쓴다. 그 뒤 next start 만 부른다. 이미지는 둘이다. image 는 그 두 파일의
자리를 쓰기 가능한 폴더 하나(/run/agent-os-widget)로 가는 심볼릭 링크로 두고, image-inplace 는 앱
폴더 안의 보통 파일로 둔다.

필요한 것. 도는 Docker 데몬(리눅스 컨테이너, BuildKit), build 섹션에는 Docker Hub 와 npm
레지스트리에 닿는 네트워크. 다른 섹션은 build 가 지어 둔 이미지(wrv-img:<단계>)만 쓴다. browser
섹션은 호스트의 node 와, 깔린 web/node_modules(`pnpm -C web install --frozen-lockfile`)와, 그 판의
Playwright 가 받은 Chromium 과, 빈 호스트 포트 둘(그 실행이 고른다)이 든다. 띄운 컨테이너와 볼륨에는
라벨 wrv-probe=<실행 토큰>을 달고, 컨테이너는 그것을 띄운 회차가 끝날 때, 남은 것은 실행이 끝날 때
이 실행의 토큰이 붙은 것만 지운다. 이미지는 남긴다. 명령의 원본 출력은 --work(없으면 시스템 임시
폴더) 아래 raw.log 에, 회차의 값은 results.jsonl 에 남는다(되풀이해 묻는 상태 조회와 실행 끝의
지우기는 원본 출력에 남기지 않는다).

표지. 회차마다 "재려는 상황이 실제로 났다"는 관찰을 본 뒤에만 측정으로 센다. 서는 것을 기대하는
회차는 응답의 상태 200 과 그 회차의 사이트 파일에서만 나오는 글(허용 출처, 요청 글자 수 상한)을
보고, 뜰 때 빌드하지 않았다는 표지로 컨테이너가 내는 BUILD_ID 가 이미지에 든 것과 같은지와 기록에
next 의 빌드 머리말이 없는지를 본다(빌드는 BUILD_ID 를 새로 짓는다). 실패를 기대하는 회차는 종료
코드가 아니라 그 까닭의 문구를 본다. 섹션마다의 표지는 섹션 함수의 독스트링에 있다. 시간은 다른
세션이 같은 Docker 데몬을 쓰는 PC 에서 잰 값이라 범위로만 읽는다.

못 보는 것. 리눅스 호스트의 Docker Engine(이 스크립트가 돈 곳은 윈도의 Docker Desktop, WSL2
커널이다), 호스트 폴더를 붙이는 바인드 마운트(사이트 파일은 이름 붙은 볼륨이나 이미지 안의 파일로
준다), 프록시 (nginx)를 거친 요청, 위젯의 코드가 값 파일을 받아 쓰는 것(브라우저의 fetch 로 받을 수
있는지까지만 본다), 위젯 시작 래퍼의 루프백 검사(진입 단계가 그 래퍼를 거치지 않는다). 결과는 같은
폴더의 README.md 에 있다.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Generator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds, Slot  # noqa: E402

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None

WEB = ROOT / "web"
LABEL = "wrv-probe"
REPO = "wrv-img"
APP = "/app/web/apps/widget"
RUN_DIR = "/run/agent-os-widget"
# 읽기 전용 루트에서 뜰 때 쓰는 두 파일을 받을 자리. compose 의 tmpfs 줄과 같은 꼴이다.
TMPFS = f"{RUN_DIR}:uid=10001,gid=10001,mode=0700"
# 단독 compose 의 web 컨테이너(관리 화면, 위젯 테스트 페이지)가 받는 제한은 read_only
# 하나다(READ_ONLY). HARDENED 는 거기에 프록시와 postgres 가 받는 cap_drop, security_opt 까지 더해
# 더 조인 꼴이다. 두 꼴을 모두 잰다.
READ_ONLY = ("--read-only",)
HARDENED = ("--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true")
# 단독 compose 의 x-health 와 같은 값(간격 30초, 제한 10초, 재시도 3, 시작 간격 2초)에, 명세가
# 위젯에 주려는 시작 유예 30초를 둔 것이다(지금 compose 의 위젯은 300초다).
HEALTH = (
    "--health-interval",
    "30s",
    "--health-timeout",
    "10s",
    "--health-retries",
    "3",
    "--health-start-period",
    "30s",
    "--health-start-interval",
    "2s",
)
# 상태 확인을 지켜보는 동안. 시작 유예(30초)보다 짧게 둔다. 지켜보는 마지막 한 번이 늦게 돌아올 수
# 있어, healthy 를 본 회차는 그것을 본 시각(띄우기 전부터 잰 시간)이 이 값보다 짧은지를 본다.
HEALTH_WINDOW = 25.0
# HEALTH 의 --health-start-period 와 같은 값(초).
START_PERIOD = 30.0
# 아무도 듣지 않는 포트에 건 요청이 실패한 까닭으로 node 의 fetch 가 드는 오류 코드.
REFUSED = "ECONNREFUSED"
NO_NETWORK = ("--network", "none")
BASE = "http://127.0.0.1:3000"
# 값 파일에 건 응답 머리 규칙이 지어 둔 routes-manifest 에 실리는 모양(patch-config.mjs 가 더한 것).
VALUES_RULE: Json = {
    "source": "/widget/runtime.json",
    "headers": [{"key": "Access-Control-Allow-Origin", "value": "*"}],
}
# 뜬 뒤의 이미지에서 크기를 재는 폴더(작업 폴더는 위젯 앱 폴더다).
DU_PATHS = (".next", "public", "/app/web/node_modules")
SITE_A = "/probe/sites_a.toml"
SITE_BROKEN = "/probe/sites_broken.toml"
MOUNTED = "/etc/agent-os/site/sites.toml"
ORIGINS_A = ("https://probe-a.example",)
ORIGINS_B = ("https://probe-b.example", "https://www.probe-b.example:8443")
CHARS_A = 771133
CHARS_B = 583927
# 사이트가 없을 때의 상한(@agent-os/site-file 의 DEFAULT_REQUEST_CHARS).
DEFAULT_CHARS = 20000
# next 가 값 파일(공개 파일)과 미리 그려 둔 페이지에 다는 머리. 명세가 근거로 드는 값이라 서는
# 회차마다 표지로 단언한다(serves).
VALUES_CACHE = "public, max-age=0"
VALUES_TYPE = "application/json; charset=UTF-8"
PAGE_SHARED_CACHE = "s-maxage=31536000"
# Dockerfile 의 단계. 차례대로 짓는다(앞 단계의 층을 뒤 단계가 다시 쓴다).
TARGETS = ("deps-full", "deps-prod", "build", "build-inspect", "image-inplace", "image")
BUILD_BANNER = "Creating an optimized production build"
FIRST_OK = "WRV_PROBE first-ok t="
NEXT_START = "WRV_PROBE next-start t="
NEXT_BIN = "node_modules/next/dist/bin/next"

_work: list[Path] = []
_token = secrets.token_hex(3)
# 만드는 것마다 라벨 키는 같고 값은 이 실행의 토큰이다. 지우기는 값까지 맞는 것만 고른다.
TAG = f"{LABEL}={_token}"
_serial = [0]
# 이미지 ID 마다 그 이미지에 든 BUILD_ID.
_build_ids: dict[str, str] = {}
# 단계마다 이 실행이 쓰는 이미지의 ID.
_image_ids: dict[str, str] = {}
# 이 실행에서 빌드가 실패한 단계. 앞서 지어 둔 같은 태그의 이미지로 재지 않으려고 둔다(image).
_failed: set[str] = set()
# 이 실행이 띄우고 아직 지우지 않은 컨테이너(owned 가 회차나 섹션이 끝날 때 지운다).
_live: list[str] = []


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
    """JSON 한 덩이. 풀지 못하면 None 이다(잘린 줄을 예외로 던지지 않는다)."""
    try:
        found: Json = json.loads(text)
    except ValueError:
        return None
    return found


def last_json(text: str) -> dict[str, Json]:
    """출력의 마지막 줄을 JSON 객체로 푼다. 객체가 아니면 빈 것이다."""
    lines = text.strip().splitlines()
    found = parse(lines[-1]) if lines else None
    return found if isinstance(found, dict) else {}


@dataclass
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
            check=False,
        )
    except subprocess.TimeoutExpired as expired:
        partial_out = (
            expired.stdout.decode("utf-8", errors="replace")
            if isinstance(expired.stdout, bytes)
            else (expired.stdout or "")
        )
        partial_err = (
            expired.stderr.decode("utf-8", errors="replace")
            if isinstance(expired.stderr, bytes)
            else (expired.stderr or "")
        )
        done = Done(
            -1,
            partial_out,
            f"{partial_err}\n{timeout:.0f}초 안에 끝나지 않았다",
            time.monotonic() - started,
        )
    else:
        done = Done(
            completed.returncode, completed.stdout, completed.stderr, time.monotonic() - started
        )
    if not quiet:
        raw(" ".join(argv), f"exit={done.code}\n--- stdout\n{done.out}\n--- stderr\n{done.err}")
    return done


def docker(*args: str, timeout: float = 300, quiet: bool = False) -> Done:
    return run(["docker", *args], timeout=timeout, quiet=quiet)


def tag(target: str) -> str:
    return f"{REPO}:{target}"


def pin(target: str, ref: str) -> str:
    """`ref`(태그나 빌드가 낸 ID)를 이미지 ID 로 풀어, 그 단계가 이 실행에서 쓸 이미지로 굳히고
    결과에 적는다. 풀지 못하면 예외다. 태그 그대로 띄우면 어느 이미지를 쟀는지 적지 못한 채 그
    회차가 측정으로 세어질 수 있어, 태그로 돌아가지 않는다."""
    done = docker("image", "inspect", "-f", "{{.Id}} {{.Created}}", ref, timeout=60)
    found = done.out.split()
    if done.code != 0 or len(found) != 2 or not found[0].startswith("sha256:"):
        raise RuntimeError(f"{ref} 를 이미지 ID 로 풀지 못했다: {tail(done.text)}")
    _image_ids[target] = found[0]
    note("쓴 이미지", {"target": target, "id": found[0], "created": found[1], "from": ref})
    return found[0]


def image(target: str) -> str:
    """그 단계의 이미지를 ID 로 가리킨다. 태그(wrv-img:<단계>)는 다시 지으면 다른 이미지로 옮겨
    가고 같은 Docker 데몬을 쓰는 다른 실행도 옮길 수 있다. 그래서 build 섹션은 빌드가 낸 ID 를 바로
    받아 쓰고(build), build 섹션 없이 돈 실행은 그 단계를 처음 쓸 때 태그를 ID 로 한 번 풀어 그
    뒤로 같은 ID 를 쓴다(pin). 풀지 못하면 예외이고 그 회차는 측정이 아니다. 이 실행에서 그 단계의
    빌드가 실패했으면 앞서 지어 둔 이미지가 남아 있어도 쓰지 않는다. build 섹션 없이 돈 실행이 어느
    빌드의 이미지를 쟀는지는 적힌 ID 로만 알 수 있다(못 보는 것)."""
    if target in _failed:
        raise RuntimeError(
            f"이 실행에서 {target} 의 빌드가 실패했다. 앞서 지어 둔 이미지로 재지 않는다"
        )
    if target not in _image_ids:
        pin(target, tag(target))
    return _image_ids[target]


def fresh(kind: str) -> str:
    """이 실행이 만드는 컨테이너와 볼륨의 이름. 실행마다 토큰이 다르다."""
    _serial[0] += 1
    return f"wrv-p-{_token}-{kind}-{_serial[0]}"


KINDS = (
    ("container", ("ps", "-aq"), ("rm", "-f", "-v")),
    ("volume", ("volume", "ls", "-q"), ("volume", "rm", "-f")),
)


def sweep() -> None:
    """이 실행의 토큰을 라벨 값으로 단(TAG) 컨테이너와 볼륨만 지운다. 같은 프로브의 다른 실행과 다른
    세션의 것은 건드리지 않는다. 원본 기록(raw.log)을 쓰지 못하는 때에도 지우기는 끝까지 가게, 이
    안의 docker 호출은 원본 기록에 남기지 않고 결과만 화면에 찍는다."""
    for kind, lister, remover in KINDS:
        listed = docker(*lister, "--filter", f"label={TAG}", timeout=60, quiet=True)
        ids = listed.out.split()
        if listed.code != 0:
            print(f"sweep {kind}: 목록을 읽지 못했다(exit={listed.code}): {tail(listed.text)}")
        elif ids:
            removed = docker(*remover, *ids, timeout=180, quiet=True)
            failed = "" if removed.code == 0 else f": {tail(removed.text)}"
            print(f"sweep {kind}: {len(ids)}개, exit={removed.code}{failed}", flush=True)


def leftovers() -> None:
    """시작할 때 라벨 키는 같고 값이 다른 자원(끊긴 앞 실행이나 함께 도는 다른 실행의 것)을 세어
    알린다. 둘을 가르지 못해 지우지 않는다."""
    found: list[str] = []
    for kind, lister, _ in KINDS:
        listed = docker(*lister, "--filter", f"label={LABEL}", timeout=60)
        if listed.code == 0 and listed.out.split():
            found.append(f"{kind} {len(listed.out.split())}")
    if found:
        print(
            f"라벨 {LABEL} 가 붙은 다른 실행의 자원이 있다({', '.join(found)}). 지우지 않았다. "
            f"도는 실행이 없으면 --filter label={LABEL} 로 골라 손으로 지운다.",
            flush=True,
        )


# ---------------------------------------------------------------------------------------------
# 컨테이너를 다루는 도우미


def tail(text: str, count: int = 3) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " / ".join(lines[-count:])


def start(
    target: str,
    *options: str,
    command: Sequence[str] = (),
    env: Mapping[str, str] | None = None,
) -> str:
    """컨테이너를 뒤에서 띄우고 이름을 낸다. 띄우지 못하면 예외다(그 회차는 측정이 아니다). 이름은
    띄우기 전에 적어 둔다(_live). 만들어지기만 하고 뜨지 못한 컨테이너도 owned 가 지운다."""
    name = fresh("c")
    envs = [item for key, value in (env or {}).items() for item in ("-e", f"{key}={value}")]
    ref = image(target)
    _live.append(name)
    done = docker("run", "-d", "--name", name, "--label", TAG, *envs, *options, ref, *command)
    if done.code != 0:
        raise RuntimeError(f"docker run 실패: {tail(done.text)}")
    return name


@contextmanager
def owned() -> Generator[None]:
    """이 안에서 띄운 컨테이너를 나갈 때 지운다. 서지 않아 일찍 돌아온 회차나 예외로 끝난 회차의
    컨테이너가 남아 뒤 회차와 CPU 와 메모리를 나눠 쓰지 않게 한다. 볼륨은 실행 끝의 sweep 이
    지운다."""
    before = len(_live)
    try:
        yield
    finally:
        names = _live[before:]
        del _live[before:]
        if names:
            docker("rm", "-f", "-v", *names, timeout=180)


@contextmanager
def owned_round(rounds: Rounds, label: str) -> Generator[Slot]:
    """회차 하나. 그 회차가 띄운 컨테이너는 회차가 끝날 때 지운다(owned)."""
    with rounds.round(label) as current, owned():
        yield current


def up(
    target: str,
    *options: str,
    site: str | None = SITE_A,
    command: Sequence[str] = (),
) -> str:
    """위젯 컨테이너를 띄운다. `site` 가 None 이면 사이트 파일의 환경 변수를 주지 않는다."""
    env = {"WRV_PROBE_WAIT_URL": f"{BASE}/widget"}
    if site is not None:
        env["AGENT_OS_SITE_FILE"] = site
    return start(target, *options, env=env, command=command)


def logs(name: str) -> Done:
    return docker("logs", name, timeout=60, quiet=True)


def judged_logs(name: str) -> str:
    """요청을 건 뒤의 기록. 회차의 판정(빌드 머리말이 없다, 오류 번호가 없다)과 시간이 이 글에서
    나오므로 원본 기록에도 남긴다. until 이 남기는 것은 첫 200 때의 기록이라 이보다 짧다. 기록을
    읽지 못하면 예외다(그 회차는 측정이 아니다). 읽지 못하고 받은 글에 그 문구가 없는 것을 "없다"는
    표지로 세지 않는다."""
    done = logs(name)
    raw(f"logs {name} (판정에 쓴 기록, exit={done.code})", done.text)
    if done.code != 0:
        raise RuntimeError(
            f"판정에 쓸 기록을 읽지 못했다(docker logs exit={done.code}): {tail(done.text)}"
        )
    return done.text


def state(name: str) -> dict[str, Json]:
    done = docker("inspect", "-f", "{{json .State}}", name, timeout=60, quiet=True)
    found = parse(done.out.strip())
    return found if isinstance(found, dict) else {}


def until(name: str, needle: str, *, count: int = 1, timeout: float = 90) -> str:
    """기록에 `needle` 이 `count` 번 나오거나 컨테이너가 끝날 때까지 기다리고 그때의 기록을 낸다."""
    deadline = time.monotonic() + timeout
    text = ""
    while time.monotonic() < deadline:
        text = logs(name).text
        if text.count(needle) >= count:
            break
        if state(name).get("Running") is not True:
            text = logs(name).text
            break
        time.sleep(0.3)
    raw(f"logs {name}", text)
    return text


def finished(name: str, *, timeout: float = 60) -> dict[str, Json]:
    """컨테이너가 끝나기를 기다리고 상태를 낸다. 끝나지 않으면 그때의 상태다."""
    deadline = time.monotonic() + timeout
    found = state(name)
    while found.get("Running") is True and time.monotonic() < deadline:
        time.sleep(0.3)
        found = state(name)
    return found


def shell(name: str, script: str) -> Done:
    return docker("exec", name, "sh", "-c", script, timeout=60)


def fetch(name: str, path: str, *extra: str) -> dict[str, Json]:
    """컨테이너 안에서 요청 하나를 건다(fetch.mjs)."""
    done = docker("exec", name, "node", "/probe/fetch.mjs", BASE + path, *extra, timeout=60)
    return last_json(done.out) or {"error": tail(done.text)}


def head(found: Mapping[str, Json], key: str) -> str:
    headers = found.get("headers")
    value = headers.get(key) if isinstance(headers, dict) else None
    return value if isinstance(value, str) else ""


def csp_of(origins: Sequence[str]) -> str:
    return "frame-ancestors " + (" ".join(origins) if origins else "'none'")


def observe(name: str) -> dict[str, Json]:
    """떠 있는 위젯이 내는 것. 페이지, 값 파일, 페이지 안 번들, 글꼴 파일 하나, 없는 경로."""
    page = fetch(name, "/widget")
    values = fetch(name, "/widget/runtime.json", "--body")
    element = fetch(name, "/widget/element.js")
    missing = fetch(name, "/widget/wrv-probe-no-such-path")
    font_name = shell(name, "ls public/fonts | head -n 1").out.strip()
    font = fetch(name, f"/widget/fonts/{font_name}") if font_name else {}
    body = values.get("body")
    return {
        "page": page.get("status"),
        "page_csp": head(page, "content-security-policy"),
        "page_cache": head(page, "cache-control"),
        "values": values.get("status"),
        "values_body": parse(body) if isinstance(body, str) else None,
        "values_acao": head(values, "access-control-allow-origin"),
        "values_csp": head(values, "content-security-policy"),
        "values_cache": head(values, "cache-control"),
        "values_etag": head(values, "etag"),
        "values_type": head(values, "content-type"),
        "element": element.get("status"),
        "element_acao": head(element, "access-control-allow-origin"),
        "element_csp": head(element, "content-security-policy"),
        "font": font.get("status"),
        "font_acao": head(font, "access-control-allow-origin"),
        "missing": missing.get("status"),
        "missing_csp": head(missing, "content-security-policy"),
    }


def serves(seen: Mapping[str, Json], origins: Sequence[str], chars: int) -> bool:
    """그 사이트 파일의 두 값을 내는지. /widget 아래의 네 응답(페이지, 페이지 안 번들, 값 파일, 없는
    경로의 404)의 frame-ancestors 머리, 값 파일의 내용과 머리(다른 출처에 여는 머리, 캐시 머리,
    내용의 종류, 비지 않은 ETag), 글꼴 파일의 다른 출처에 여는 머리, 페이지의 공유 캐시 머리다. 값
    파일과 404 의 frame-ancestors, 캐시 머리 둘, 내용의 종류, ETag, 글꼴은 첫 세 실행 뒤에 더한
    표지다(README 의 "결과를 본 뒤 바꾼 것")."""
    want = csp_of(origins)
    return (
        seen["page"] == 200
        and seen["page_csp"] == want
        and PAGE_SHARED_CACHE in str(seen["page_cache"])
        and seen["values"] == 200
        and seen["values_body"] == {"allowedOrigins": list(origins), "requestChars": chars}
        and seen["values_acao"] == "*"
        and seen["values_csp"] == want
        and seen["values_cache"] == VALUES_CACHE
        and seen["values_type"] == VALUES_TYPE
        and bool(seen["values_etag"])
        and seen["element"] == 200
        and seen["element_acao"] == "*"
        and seen["element_csp"] == want
        and seen["font"] == 200
        and seen["font_acao"] == "*"
        and seen["missing"] == 404
        and seen["missing_csp"] == want
    )


def epoch(stamp: str) -> float:
    """Docker 의 시각(나노초까지의 RFC 3339. 끝이 Z 이거나 +09:00 같은 시간대 차이다)을 초로. 풀지
    못했거나 시간대가 없으면 0 이다. 마이크로초 아래는 버려진다."""
    try:
        found = datetime.fromisoformat(stamp)
    except ValueError:
        return 0.0
    return found.timestamp() if found.tzinfo is not None else 0.0


def stamps(text: str, mark: str) -> list[float]:
    return [float(found) for found in re.findall(rf"WRV_PROBE {mark} t=([0-9.]+)", text)]


def ready_ms(text: str) -> float | None:
    """next 가 찍은 마지막 `Ready in` 의 값(ms)."""
    found = re.findall(r"Ready in ([0-9.]+)\s*(ms|s)\b", text)
    if not found:
        return None
    value, unit = found[-1]
    return float(value) * (1000 if unit == "s" else 1)


def timings(name: str, text: str) -> dict[str, Json]:
    """마지막 시작의 구간. 진입 단계가 걸린 시간, 진입에서 첫 200 까지, 컨테이너 시작에서 첫 200
    까지."""
    entry, begun, ok = stamps(text, "entry"), stamps(text, "next-start"), stamps(text, "first-ok")
    started = epoch(str(state(name).get("StartedAt", "")))
    out: dict[str, Json] = {"next_ready_ms": ready_ms(text)}
    if entry and begun:
        out["entry_step_s"] = round(begun[-1] - entry[-1], 3)
    if entry and ok:
        out["entry_to_first_ok_s"] = round(ok[-1] - entry[-1], 2)
    if started and ok:
        out["container_to_first_ok_s"] = round(ok[-1] - started, 2)
    return out


def memory(name: str) -> dict[str, Json]:
    done = shell(name, "cat /sys/fs/cgroup/memory.peak /sys/fs/cgroup/memory.current")
    numbers = [int(word) for word in done.out.split() if word.isdigit()]
    if len(numbers) != 2:
        return {}
    return {
        "peak_mib": round(numbers[0] / 2**20, 1),
        "current_mib": round(numbers[1] / 2**20, 1),
    }


def image_build_id(target: str) -> str:
    """그 단계의 이미지에 든 BUILD_ID. 이미지 ID 마다 한 번 읽는다(같은 실행에서 그 단계를 다시
    지으면 새 이미지의 것을 다시 읽는다). 읽지 못하면 빈 글이고 기억해 두지 않는다."""
    ref = image(target)
    if ref not in _build_ids:
        done = docker("run", "--rm", "--label", TAG, "--entrypoint", "cat", ref, ".next/BUILD_ID")
        found = done.out.strip()
        if done.code != 0 or not found:
            return ""
        _build_ids[ref] = found
    return _build_ids[ref]


def prebuilt(name: str, target: str, text: str) -> bool:
    """뜰 때 빌드하지 않았다는 표지. 내는 BUILD_ID 가 이미지의 것과 같고 기록에 빌드 머리말이
    없다. 머리말이 없다는 것은 그 컨테이너의 기록을 실제로 읽었을 때만 뜻이 있어, 그 글이 첫 200 의
    줄을 든 것도 함께 본다."""
    served = shell(name, "cat .next/BUILD_ID").out.strip()
    return (
        bool(served)
        and served == image_build_id(target)
        and FIRST_OK in text
        and BUILD_BANNER not in text
    )


def stop(name: str, *, grace: int = 10) -> dict[str, Json]:
    done = docker("stop", "-t", str(grace), name, timeout=grace + 60)
    found = state(name)
    return {"stop_s": round(done.seconds, 2), "exit": found.get("ExitCode")}


def site_text(origins: Sequence[str] | None = None, *, name: str = "sites_a.toml") -> str:
    """프로브의 사이트 파일의 글. `origins` 를 주면 sites_a.toml 의 허용 출처 줄을 그것으로
    바꾼다."""
    text = (HERE / name).read_text(encoding="utf-8")
    if origins is None:
        return text
    line = 'allowed_origins = ["https://probe-a.example"]'
    if text.count(line) != 1:
        raise RuntimeError(f"{name} 에서 허용 출처 줄을 찾지 못했다")
    return text.replace(line, f"allowed_origins = {json.dumps(list(origins))}")


WRITER = (
    "require('node:fs').writeFileSync('/cfg/sites.toml',Buffer.from(process.env.WRV_B64,'base64'))"
)


def put(volume: str, text: str) -> None:
    """이름 붙은 볼륨의 sites.toml 을 그 글로 쓴다(root 로 도는 일회용 컨테이너). 글은 base64 로
    넘긴다."""
    encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
    done = docker(
        "run",
        "--rm",
        "--label",
        TAG,
        "--user",
        "0",
        "-v",
        f"{volume}:/cfg",
        "-e",
        f"WRV_B64={encoded}",
        "--entrypoint",
        "node",
        image("image"),
        "-e",
        WRITER,
        timeout=120,
    )
    if done.code != 0:
        raise RuntimeError(f"볼륨에 사이트 파일을 쓰지 못했다: {tail(done.text)}")


def volume_with(text: str) -> str:
    name = fresh("vol")
    made = docker("volume", "create", "--label", TAG, name, timeout=60)
    if made.code != 0:
        raise RuntimeError(f"볼륨을 만들지 못했다: {tail(made.text)}")
    put(name, text)
    return name


# ---------------------------------------------------------------------------------------------
# build


def size_mb(target: str) -> float:
    done = docker("image", "inspect", "-f", "{{.Size}}", image(target), timeout=60)
    text = done.out.strip()
    return round(int(text) / 2**20, 1) if text.isdigit() else 0.0


def inspect(target: str, *args: str) -> dict[str, Json]:
    done = docker(
        "run",
        "--rm",
        "--label",
        TAG,
        "--entrypoint",
        "node",
        image(target),
        "/probe/inspect.mjs",
        *args,
        timeout=120,
    )
    return last_json(done.out)


def build(target: str) -> Done:
    """Dockerfile 의 그 단계를 짓는다. 지어지면 빌드가 낸 이미지 ID(--iidfile)를 받아 그 단계가 이
    실행에서 쓸 이미지로 굳힌다(pin). 지은 뒤에 태그를 다시 풀면, 같은 Docker 데몬에서 같은 단계를
    짓는 다른 실행이 그 사이에 옮긴 이미지를 집을 수 있다. 짓지 못했거나 ID 를 받지 못하면 그 단계를
    실패로 적어 두어, 앞서 지어 둔 같은 태그의 이미지를 뒤의 회차가 쓰지 못하게 한다(image)."""
    built = _work[0] / f"iid-{target}.txt"
    built.unlink(missing_ok=True)
    _image_ids.pop(target, None)
    _failed.add(target)
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
        tag(target),
        "--iidfile",
        str(built),
        str(WEB),
        timeout=2400,
    )
    if done.code == 0:
        try:
            ref = built.read_text(encoding="utf-8").strip()
        except OSError as error:
            raise RuntimeError(f"빌드가 이미지 ID 파일을 남기지 않았다: {error}") from error
        pin(target, ref)
        _failed.discard(target)
    return done


def section_build(rounds: Rounds, _repeat: int) -> None:
    """Dockerfile 의 단계를 차례로 짓고 지어진 것을 들여다본다. 걸린 시간은 층 캐시가 있으면 0 에
    가까워 빌드 시간의 근거가 아니다. 뒤의 세 회차는 이 실행이 지은 이미지만 본다. 그 단계의 빌드가
    실패했으면 앞서 지어 둔 이미지가 남아 있어도 그 회차는 측정이 아니다(image).

    - 단계마다: 표지는 docker build 가 0 으로 끝나고, 빌드가 낸 ID 의 이미지가 크기를 내는
      것이다.
    - 깔린 것: 표지는 image 에 next 가 깔려 있고 빌드 도구(vite, @tailwindcss/vite, typescript)가
      없으며, 같은 도우미가 deps-full 로 지은 build 단계(build-inspect)에서는 넷 모두 판을 내는
      것이다(없다는 답이 도구가 실제로 없어서라는 대조).
    - 응답 머리의 자리: 표지는 지어 둔 routes-manifest 원본에 frame-ancestors 지시어가 든 응답
      머리가 정확히 하나이고 그 값이 frame-ancestors 'none' 이며, .next 아래에서 그 글이 든 파일이
      routes-manifest 둘(뜰 때 쓰는 것은 링크라 세지 않는다)뿐이고 크기 때문에 훑지 않고 넘긴
      파일이 없는 것이다. 값 파일의 경로(/widget/runtime.json)에 건 응답 머리 규칙이 정확히 하나이고
      그것이 Access-Control-Allow-Origin: * 하나만 다는 것도 본다.
    - 산출물의 크기: 표지는 du 가 0 으로 끝나고 세 폴더(.next, public, node_modules) 모두의 크기를
      낸 것이다.
    """
    for target in TARGETS:
        with rounds.round(f"build {target}") as current:
            done = build(target)
            size = size_mb(target) if done.code == 0 else 0.0
            note(
                f"build {target}",
                {"exit": done.code, "seconds": round(done.seconds, 1), "size_mib": size},
            )
            if done.code != 0:
                note(f"build {target} 끝줄", {"tail": tail(done.text, 6)})
            built = done.code == 0 and size > 0
            current.mark(measured=built, result="지어졌다" if built else "짓지 못했다")
    names = ("next", "vite", "@tailwindcss/vite", "typescript")
    with rounds.round("build 깔린 것") as current:
        runtime = inspect("image", "resolvable", *names)
        full = inspect("build-inspect", "resolvable", *names)
        info = docker("version", "--format", "{{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}")
        kernel = docker("info", "--format", "{{.KernelVersion}} cgroup v{{.CgroupVersion}}")
        node = docker("run", "--rm", "--label", TAG, "--entrypoint", "node", image("image"), "-v")
        note(
            "깔린 것",
            {
                "docker": info.out.strip(),
                "kernel": kernel.out.strip(),
                "node": node.out.strip(),
                "image": runtime,
                "build": full,
            },
        )
        lean = (
            isinstance(runtime.get("next"), str)
            and all(runtime.get(name) is None for name in names[1:])
            and all(isinstance(full.get(name), str) for name in names)
        )
        current.mark(
            measured=lean,
            result="image 에는 next 만 있고 빌드 도구는 없다" if lean else "기대와 다르다",
        )
    with rounds.round("build 응답 머리의 자리") as current:
        found = inspect("image-inplace", "manifest")
        note("지어 둔 routes-manifest", found)
        slots = found.get("slots")
        rules = found.get("valueFileRules")
        one = (
            isinstance(slots, list)
            and len(slots) == 1
            and isinstance(slots[0], dict)
            and slots[0].get("value") == "frame-ancestors 'none'"
            and found.get("holding") == ["routes-manifest.build.json", "routes-manifest.json"]
            and found.get("skipped") == []
            and rules == [VALUES_RULE]
        )
        current.mark(
            measured=one,
            result="frame-ancestors 의 자리는 routes-manifest 의 한 곳이다" if one else "다르다",
        )
    with rounds.round("build 산출물의 크기") as current:
        done = docker(
            "run",
            "--rm",
            "--label",
            TAG,
            "--entrypoint",
            "du",
            image("image"),
            "-sm",
            *DU_PATHS,
            timeout=120,
        )
        sizes = dict(
            (path, size) for size, path in re.findall(r"^(\d+)\s+(\S+)$", done.out, re.MULTILINE)
        )
        note(
            "산출물의 크기(MB)",
            {
                "exit": done.code,
                "du": " ".join(f"{sizes[path]}={path}" for path in DU_PATHS if path in sizes),
            },
        )
        sized = done.code == 0 and all(path in sizes for path in DU_PATHS)
        current.mark(measured=sized, result="쟀다" if sized else "못 쟀다")


# ---------------------------------------------------------------------------------------------
# start


def start_round(rounds: Rounds, label: str, target: str, *options: str) -> None:
    with owned_round(rounds, label) as current:
        name = up(target, *options)
        text = until(name, FIRST_OK)
        if FIRST_OK not in text:
            note(label, {"state": str(state(name).get("Status")), "tail": tail(text, 6)})
            current.mark(measured=False, result="서지 않았다")
            return
        seen = observe(name)
        used = memory(name)
        text = judged_logs(name)
        fixed = prebuilt(name, target, text)
        timing = timings(name, text)
        stopped = stop(name)
        note(label, {**timing, **used, **stopped, "prebuilt": fixed, **seen})
        good = serves(seen, ORIGINS_A, CHARS_A) and fixed
        current.mark(
            measured=good,
            result="빌드 없이 서서 사이트 파일 A 의 두 값을 냈다" if good else "기대와 다르다",
        )


def section_start(rounds: Rounds, repeat: int) -> None:
    """미리 지은 이미지를 사이트 파일 A 로 띄운다. 표지는 첫 200, 페이지와 페이지 안 번들의 응답
    머리가 A 의 허용 출처이고 값 파일이 A 의 두 값과 Access-Control-Allow-Origin: * 를 내는 것,
    그리고 뜰 때 빌드하지 않았다는 표지(prebuilt)다. 시간은 진입 단계가 찍은 시각과 wait.mjs 가 찍은
    첫 200 의 시각의 차이고, 메모리는 요청 몇을 건 뒤의 cgroup memory.peak 다. 링크 없는
    이미지(image-inplace)는 같은 조합이 링크 없이도 서는지의 갈래다."""
    for index in range(repeat):
        start_round(rounds, f"start image #{index + 1}", "image")
    for index in range(repeat):
        start_round(rounds, f"start image-inplace #{index + 1}", "image-inplace")
    start_round(rounds, "start image --cpus 1 --memory 256m", "image", "--cpus", "1", "-m", "256m")


# ---------------------------------------------------------------------------------------------
# reflect


def reflect_round(rounds: Rounds, label: str, target: str, *options: str) -> None:
    """사이트 파일 A 로 띄운 뒤 볼륨의 파일을 B 로 바꾸고 같은 컨테이너를 docker restart 한다.
    표지는 처음 실행이 A 의 두 값을, 다시 띄운 실행이 B 의 두 값을 내고(A 의 값은 없다) 값 파일의
    ETag 가 달라지며 둘 다 빌드하지 않은 것이다."""
    with owned_round(rounds, label) as current:
        volume = volume_with(site_text())
        name = up(target, "-v", f"{volume}:/etc/agent-os/site:ro", *options, site=MOUNTED)
        text = until(name, FIRST_OK)
        if FIRST_OK not in text:
            note(label, {"tail": tail(text, 6)})
            current.mark(measured=False, result="처음 실행이 서지 않았다")
            return
        first = observe(name)
        put(volume, site_text(name="sites_b.toml"))
        restarted = docker("restart", "-t", "10", name, timeout=120)
        text = until(name, FIRST_OK, count=2)
        if restarted.code != 0 or text.count(FIRST_OK) < 2:
            note(label, {"restart_exit": restarted.code, "tail": tail(text, 6)})
            current.mark(measured=False, result="다시 띄운 실행이 서지 않았다")
            return
        second = observe(name)
        fixed = prebuilt(name, target, text)
        timing = timings(name, text)
        used = memory(name)
        stop(name)
        note(
            label,
            {
                **timing,
                **used,
                "prebuilt": fixed,
                "first_csp": first["page_csp"],
                "first_values": first["values_body"],
                "first_etag": first["values_etag"],
                "second_csp": second["page_csp"],
                "second_values": second["values_body"],
                "second_etag": second["values_etag"],
            },
        )
        good = (
            serves(first, ORIGINS_A, CHARS_A)
            and serves(second, ORIGINS_B, CHARS_B)
            and ORIGINS_A[0] not in json.dumps(second)
            and first["values_etag"] != second["values_etag"]
            and fixed
        )
        current.mark(
            measured=good,
            result="다시 띄우자 사이트 파일 B 의 두 값을 냈다" if good else "기대와 다르다",
        )


def section_reflect(rounds: Rounds, repeat: int) -> None:
    """사이트 파일을 바꾸고 다시 띄우면 반영되는지. 링크 있는 이미지와 링크 없는 이미지 둘 다 본다
    (읽기 전용 루트의 같은 회차는 readonly 섹션에 있다)."""
    for index in range(repeat):
        reflect_round(rounds, f"reflect image #{index + 1}", "image")
    reflect_round(rounds, "reflect image-inplace", "image-inplace")


# ---------------------------------------------------------------------------------------------
# readonly


def exits_round(
    rounds: Rounds,
    label: str,
    target: str,
    options: Sequence[str],
    *,
    needles: Sequence[str],
    result: str,
    site: str | None = SITE_A,
    command: Sequence[str] = (),
    exit_code: int | None = None,
) -> None:
    """서지 않고 끝나기를 기대하는 회차. 표지는 0 이 아닌 종료와 그 까닭의 문구(`needles`)가 모두
    기록에 있고, 진입 단계가 next 를 부르는 데까지 가지 않은 것(next-start 줄이 없다)이다. `command`
    로 진입 단계를 건너뛴 회차에서는 뒤의 것이 늘 참이라, 까닭의 문구만이 표지다. `exit_code` 를
    주면 종료 코드가 그 값인 것까지 표지다. `result` 는 표지가 맞은 회차의 결과 이름이다."""
    with owned_round(rounds, label) as current:
        name = up(target, *options, site=site, command=command)
        found = finished(name)
        text = logs(name).text
        raw(f"logs {name}", text)
        code = found.get("ExitCode")
        note(
            label,
            {"running": found.get("Running"), "exit": code, "tail": tail(text, 4)},
        )
        good = (
            found.get("Running") is False
            and isinstance(code, int)
            and code != 0
            and (exit_code is None or code == exit_code)
            and all(needle in text for needle in needles)
            and NEXT_START not in text
        )
        current.mark(measured=good, result=result if good else "기대와 다르다")


def readonly_round(
    rounds: Rounds, label: str, limits: Sequence[str] = HARDENED, *, network: bool = False
) -> None:
    """읽기 전용 루트로 띄운 회차 하나. `network` 가 거짓이면 네트워크를 끊고(--network none),
    참이면 Docker 의 기본 네트워크를 붙인 채 띄운다. 그 꼴이 실제로 났다는 표지로 컨테이너 안의
    네트워크 장치를 본다. 끊었으면 lo 하나뿐이고, 붙였으면 lo 밖의 장치가 있다."""
    with owned_round(rounds, label) as current:
        name = up("image", *limits, "--tmpfs", TMPFS, *(() if network else NO_NETWORK))
        text = until(name, FIRST_OK)
        if FIRST_OK not in text:
            note(label, {"tail": tail(text, 6)})
            current.mark(measured=False, result="서지 않았다")
            return
        seen = observe(name)
        tried = shell(
            name,
            f"touch {APP}/public/wrv-x 2>&1; touch /tmp/wrv-x 2>&1; "
            f"touch {RUN_DIR}/wrv-x 2>&1 && echo run-dir-writable",
        )
        denied = tried.text.count("Read-only file system")
        mounts = shell(name, f"grep -c ' {RUN_DIR} tmpfs ' /proc/mounts").out.strip()
        devices = shell(name, "ls /sys/class/net").out.split()
        wired = any(device != "lo" for device in devices)
        text = judged_logs(name)
        quiet = "EROFS" not in text and "EACCES" not in text
        fixed = prebuilt(name, "image", text)
        used = memory(name)
        timing = timings(name, text)
        stopped = stop(name)
        note(
            label,
            {
                **timing,
                **used,
                **stopped,
                "prebuilt": fixed,
                "root_writes_denied": denied,
                "run_dir_writable": "run-dir-writable" in tried.text,
                "tmpfs_mounts": mounts,
                "net": " ".join(devices),
                "log_quiet": quiet,
                "page_csp": seen["page_csp"],
                "values_body": seen["values_body"],
                "font": seen["font"],
                "missing": seen["missing"],
            },
        )
        good = (
            serves(seen, ORIGINS_A, CHARS_A)
            and fixed
            and denied == 2
            and "run-dir-writable" in tried.text
            and mounts == "1"
            and quiet
            and "lo" in devices
            and wired == network
        )
        current.mark(
            measured=good,
            result="읽기 전용 루트에서 tmpfs 폴더 하나로 섰다" if good else "기대와 다르다",
        )


def section_readonly(rounds: Rounds, repeat: int) -> None:
    """읽기 전용 루트. 링크 있는 이미지를 --read-only, 능력 모두 빼기, no-new-privileges, 네트워크
    없음, /run/agent-os-widget 의 tmpfs 하나로 띄운다. 표지는 A 의 두 값을 내고, 루트의 두 자리(앱의
    public, /tmp)에 쓰기가 Read-only file system 으로 거절되고, tmpfs 폴더에는 써지며, 그 폴더가
    실제로 tmpfs 로 붙었고(/proc/mounts), 요청 뒤의 기록에 EROFS 도 EACCES 도 없으며, 컨테이너 안의
    네트워크 장치가 lo 하나뿐인 것이다. 대조 둘은 서는 회차에서 하나씩만 바꾼다. 같은 이미지에서
    tmpfs 를 빼거나, tmpfs 는 그대로 주고 링크 없는 이미지를 쓰면 진입 단계가 EROFS 로 끝나는
    것이다(서게 한 것이 tmpfs 폴더와 링크라는 갈래. 링크 없는 이미지의 대조는 첫 네 실행에서 tmpfs
    도 함께 뺀 꼴이었고, 두 대조 모두 첫 다섯 실행에서는 네트워크를 끊지 않아 서는 회차와 그것도
    달랐다. README 의 "결과를 본 뒤 바꾼 것"). 그다음 회차는 단독 compose 가 web 컨테이너에 주는
    꼴대로 제한을 read_only 하나만 걸고 네트워크는 붙인 채 띄운다(더 조인 꼴에서 선 것이 그 꼴에서도
    서는지. 표지에서 네트워크 장치만 반대로 본다. lo 밖의 장치가 있어야 한다. 이 회차도 첫 다섯
    실행에서는 네트워크를 끊은 채였다). 마지막 회차는 조인 제한에서 네트워크를 붙인 채 사이트 파일을
    바꾸고 다시 띄운다."""
    for index in range(repeat):
        readonly_round(rounds, f"readonly image tmpfs #{index + 1}")
    readonly_round(
        rounds, "readonly image tmpfs, read_only 만(네트워크 있음)", READ_ONLY, network=True
    )
    unwritable = "진입 단계가 EROFS 로 끝나 next 를 부르지 않았다"
    exits_round(
        rounds,
        "readonly image, tmpfs 없음(대조)",
        "image",
        (*HARDENED, *NO_NETWORK),
        needles=["EROFS", "routes-manifest.json"],
        result=unwritable,
    )
    exits_round(
        rounds,
        "readonly image-inplace, tmpfs 있음(대조)",
        "image-inplace",
        (*HARDENED, "--tmpfs", TMPFS, *NO_NETWORK),
        needles=["EROFS", "routes-manifest.json"],
        result=unwritable,
    )
    reflect_round(rounds, "readonly image tmpfs, 다시 띄우기", "image", *HARDENED, "--tmpfs", TMPFS)


# ---------------------------------------------------------------------------------------------
# sitefile


def section_sitefile(rounds: Rounds, _repeat: int) -> None:
    """사이트 파일이 없거나 깨졌을 때와 진입 단계를 건너뛰었을 때.

    - 없는 파일, 깨진 파일: 표지는 지금의 빌드가 내는 것과 같은 진단 문구와 진입 단계의
      site-file-rejected 줄이고, next 를 부르지 않고 종료 코드 1 로 끝나는 것이다.
    - 환경 변수 없음: 멈추지 않고 서되 어느 사이트도 품지 못하는 값을 낸다. 표지는 응답 머리가
      frame-ancestors 'none' 이고 값 파일이 빈 허용 출처와 기본 상한인 것이다.
    - 진입 단계를 건너뛴 시작(링크 있는 이미지에서 next start 를 바로 부른다): 뜰 때 쓰는
      routes-manifest 가 끊긴 링크라 next 가 서지 못한다. 표지는 종료 코드 1 과, 기록에 그 파일을
      열지 못했다는 오류(ENOENT 와 routes-manifest.json 이라는 글)가 있는 것이다.
    """
    rejected = "진입 단계가 사이트 파일의 진단을 내고 next 를 부르지 않았다"
    exits_round(
        rounds,
        "sitefile 없는 파일",
        "image",
        (),
        needles=["파일이 없다", "WRV_PROBE site-file-rejected"],
        result=rejected,
        site="/probe/none.toml",
        exit_code=1,
    )
    exits_round(
        rounds,
        "sitefile 깨진 파일",
        "image",
        (),
        needles=["모르는 키다", "WRV_PROBE site-file-rejected"],
        result=rejected,
        site=SITE_BROKEN,
        exit_code=1,
    )
    with owned_round(rounds, "sitefile 환경 변수 없음") as current:
        name = up("image", site=None)
        text = until(name, FIRST_OK)
        seen = observe(name) if FIRST_OK in text else {}
        stop(name)
        note(
            "sitefile 환경 변수 없음",
            {"page_csp": seen.get("page_csp"), "values_body": seen.get("values_body")},
        )
        good = bool(seen) and serves(seen, (), DEFAULT_CHARS)
        current.mark(
            measured=good,
            result="서되 어느 사이트도 품지 못하는 값을 냈다" if good else "기대와 다르다",
        )
    exits_round(
        rounds,
        "sitefile 진입 단계를 건너뛴 시작",
        "image",
        (),
        needles=["ENOENT", "routes-manifest.json"],
        result="next 가 뜰 때 쓰는 routes-manifest 를 열지 못해 서지 못했다",
        command=("node", NEXT_BIN, "start", "--hostname", "127.0.0.1", "--port", "3000"),
        exit_code=1,
    )


# ---------------------------------------------------------------------------------------------
# health


def health_cmd(port: int, *, explain: bool = False) -> str:
    """compose 의 위젯 상태 확인과 같은 node 한 줄이다. 포트만 바꿀 수 있다. compose 는 셸 없이
    부르고(CMD) docker run 의 --health-cmd 는 sh -c 로 부르는 것이 다르다. `explain` 이면 요청이
    실패했을 때 그 까닭의 오류 코드를 한 줄 찍고 끝난다(종료 코드는 그대로 1 이다). Docker 가
    확인마다 그 출력을 확인 기록에 남긴다."""
    failed = (
        "e=>{console.log(e.cause&&e.cause.code);process.exit(1)}"
        if explain
        else "()=>process.exit(1)"
    )
    return (
        f"node -e \"fetch('http://127.0.0.1:{port}/widget')"
        f'.then(r=>process.exit(r.ok?0:1),{failed})"'
    )


def health_round(rounds: Rounds, label: str, port: int, *, healthy: bool) -> None:
    """상태 확인을 단 위젯을 읽기 전용 루트로 띄우고 HEALTH_WINDOW 동안 지켜본다. `healthy` 가
    참이면 그 안에 healthy 가 되기를, 거짓이면 확인이 실패하며 starting 으로 남기를 기대한다. 거짓인
    회차는 실패의 까닭을 그 확인의 기록에서 본다. 위젯이 3000 번에서 첫 200 을 낸 시각(기록의
    first-ok)보다 뒤에 시작한 확인이 하나 이상 있고, 그런 확인이 모두 종료 코드 1 과 연결
    거절(ECONNREFUSED)을 남긴다. 위젯이 선 뒤에 돈 확인이라, 그 실패는 위젯이 서지 않아서가 아니라
    그 포트를 아무도 듣지 않아서 난 것이다. 그 오류 코드를 찍으려고 거짓인 회차의 확인 명령만 실패
    처리에 출력 한 줄을 더한다(health_cmd 의 explain)."""
    with owned_round(rounds, label) as current:
        begun = time.monotonic()
        name = up(
            "image",
            *READ_ONLY,
            "--tmpfs",
            TMPFS,
            *NO_NETWORK,
            "--health-cmd",
            health_cmd(port, explain=not healthy),
            *HEALTH,
        )
        seen: dict[str, Json] = {}
        while time.monotonic() - begun < HEALTH_WINDOW:
            found = state(name).get("Health")
            seen = found if isinstance(found, dict) else {}
            if seen.get("Status") == "healthy":
                break
            time.sleep(0.25)
        waited = round(time.monotonic() - begun, 2)
        log = seen.get("Log")
        entries = [item for item in log if isinstance(item, dict)] if isinstance(log, list) else []
        codes = [item.get("ExitCode") for item in entries]
        status = seen.get("Status")
        values: dict[str, Json] = {
            "status": status,
            "watched_s": waited,
            "exit_codes": list(codes),
        }
        if healthy:
            stop(name)
            # waited 는 healthy 를 본 조회가 돌아온 시각이다. 지켜보는 동안 안에 봤는지를 본다.
            good = (
                status == "healthy"
                and bool(codes)
                and codes[-1] == 0
                and waited < HEALTH_WINDOW < START_PERIOD
            )
            result = "시작 유예 30초 안에 healthy 가 됐다"
        else:
            text = logs(name).text
            raw(f"logs {name}", text)
            first_ok = stamps(text, "first-ok")
            late = [
                item for item in entries if first_ok and epoch(str(item.get("Start"))) > first_ok[0]
            ]
            stop(name)
            checks: list[Json] = [
                {
                    "start": item.get("Start"),
                    "exit": item.get("ExitCode"),
                    "output": str(item.get("Output")).strip(),
                }
                for item in entries
            ]
            values["first_ok_t"] = first_ok[0] if first_ok else None
            values["checks"] = checks
            values["checks_after_first_ok"] = len(late)
            good = (
                status == "starting"
                and bool(codes)
                and all(code == 1 for code in codes)
                and bool(late)
                and all(REFUSED in str(item.get("Output")) for item in late)
            )
            result = "듣지 않는 포트의 확인은 실패했고 healthy 가 되지 않았다"
        note(label, values)
        current.mark(measured=good, result=result if good else "기대와 다르다")


def section_health(rounds: Rounds, repeat: int) -> None:
    """상태 확인. compose 의 위젯 상태 확인과 같은 node 한 줄을, compose 의 공통 값에 시작 유예
    30초를 둔 옵션으로 달고 읽기 전용 루트의 위젯을 띄운다. 표지는 상태가 healthy 인 것을 본 시각이
    띄우기 전부터 재어 지켜보는 25초 안이고(그 25초는 시작 유예 30초보다 짧다) 마지막 확인의 종료
    코드가 0 인 것이다. 대조는 같은 요청을 아무도 듣지 않는 포트에 건 것이고(실패하면 오류 코드를
    찍는 것만 다르다), 표지는 남은 확인 기록이 비지 않고 모두 종료 코드 1 이며 상태가 starting 으로
    남고, 위젯이 3000 번에서 첫 200 을 낸 뒤에 시작한 확인이 하나 이상 있으며, 그런 확인의 출력이
    모두 연결 거절(ECONNREFUSED)을 든 것이다(healthy 가 확인이 성공해서 난 것이라는 갈래)."""
    for index in range(repeat):
        health_round(rounds, f"health image #{index + 1}", 3000, healthy=True)
    health_round(rounds, "health 듣지 않는 포트(대조)", 3999, healthy=False)


# ---------------------------------------------------------------------------------------------
# browser


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as found:
        found.bind(("127.0.0.1", 0))
        port: int = found.getsockname()[1]
    return port


def browse(parent_port: int, widget_port: int) -> dict[str, Json]:
    done = run(
        [
            "node",
            str(HERE / "browser.mjs"),
            "--playwright",
            str(WEB / "apps" / "widget" / "package.json"),
            "--parent-port",
            str(parent_port),
            "--widget",
            f"http://127.0.0.1:{widget_port}",
            "--labels",
            "allowed,other",
        ],
        timeout=150,
    )
    return last_json(done.out) or {"error": tail(done.text, 4)}


def visit_of(found: Mapping[str, Json], label: str) -> dict[str, Json]:
    visits = found.get("visits")
    visit = visits.get(label) if isinstance(visits, dict) else None
    return visit if isinstance(visit, dict) else {}


def embedded(visit: Mapping[str, Json], widget_url: str) -> bool:
    """그 부모 페이지의 iframe 안에 위젯의 문서가 실렸는지. iframe 의 주소가 위젯 페이지이고 그 안의
    문서가 위젯 출처의 것이며 next 의 스크립트를 든다."""
    inside = visit.get("inside")
    scripts = inside.get("nextScripts") if isinstance(inside, dict) else 0
    return visit.get("frameUrl") == widget_url and isinstance(scripts, int) and scripts > 0


def blocked(visit: Mapping[str, Json], want_csp: str) -> bool:
    """그 부모 페이지의 iframe 이 막혔는지. 위젯 페이지는 200 과 그 CSP 로 답했고, iframe 은
    Chromium 의 오류 페이지로 끝났으며, 콘솔 오류가 그 frame-ancestors 값을 든다."""
    responses = visit.get("frameResponses")
    answered = (
        isinstance(responses, list)
        and bool(responses)
        and all(
            isinstance(item, dict) and item.get("status") == 200 and item.get("csp") == want_csp
            for item in responses
        )
    )
    errors = visit.get("consoleErrors")
    told = isinstance(errors, list) and any(
        isinstance(item, str) and want_csp in item for item in errors
    )
    return answered and visit.get("frameUrl") == "chrome-error://chromewebdata/" and told


def fetched(visit: Mapping[str, Json], key: str) -> dict[str, Json]:
    found = visit.get("fetched")
    item = found.get(key) if isinstance(found, dict) else None
    return item if isinstance(item, dict) else {}


# Chromium 이 다른 출처의 응답에 여는 머리가 없어 fetch 를 막을 때 콘솔에 남기는 글의 두 토막.
CORS_BLOCKED = "blocked by CORS policy"
CORS_NO_HEADER = "No 'Access-Control-Allow-Origin' header"


def cors_refused(visit: Mapping[str, Json], url: str) -> bool:
    """그 문서의 fetch 가 `url` 을 받지 못한 까닭이 다른 출처 거절이라는 표지. Chromium 의 콘솔 오류
    하나가 그 주소와 CORS_BLOCKED 와 CORS_NO_HEADER 를 함께 든다. 응답은 왔는데 그 머리가 없었다는
    글이라, 연결하지 못해 실패한 fetch 와 가른다."""
    errors = visit.get("consoleErrors")
    return isinstance(errors, list) and any(
        isinstance(item, str)
        and f"'{url}'" in item
        and CORS_BLOCKED in item
        and CORS_NO_HEADER in item
        for item in errors
    )


def browser_phase(
    label: str,
    parent_port: int,
    widget_port: int,
    *,
    allowed: str,
    other: str,
    chars: int,
) -> bool:
    """브라우저로 한 번 본다. `allowed` 라벨의 부모 페이지만 위젯을 품어야 한다."""
    widget_url = f"http://127.0.0.1:{widget_port}/widget"
    origin = f"http://{allowed}.localhost:{parent_port}"
    want = csp_of([origin])
    found = browse(parent_port, widget_port)
    inside, outside = visit_of(found, allowed), visit_of(found, other)
    values = fetched(outside, "values")
    body = values.get("body")
    read = parse(body) if isinstance(body, str) else None
    page = fetched(outside, "page")
    note(
        label,
        {
            "browser": found.get("browser"),
            "error": found.get("error"),
            "allowed_frame": inside.get("frameUrl"),
            "allowed_inside": inside.get("inside"),
            "allowed_console": inside.get("consoleErrors"),
            "other_frame": outside.get("frameUrl"),
            "other_responses": outside.get("frameResponses"),
            "other_console": outside.get("consoleErrors"),
            "cross_origin_values": values,
            "cross_origin_page": page,
            "cross_origin_page_cors": cors_refused(outside, widget_url),
        },
    )
    return (
        embedded(inside, widget_url)
        and blocked(outside, want)
        and values.get("status") == 200
        and read == {"allowedOrigins": [origin], "requestChars": chars}
        and "error" in page
        and cors_refused(outside, widget_url)
    )


def section_browser(rounds: Rounds, _repeat: int) -> None:
    """소비 지점. 호스트의 Chromium 으로, 읽기 전용 루트로 띄운 위젯을 사이트 페이지 둘이 품어 본다.

    - 첫 회차: 사이트 파일의 허용 출처가 http://allowed.localhost:<포트> 하나다. 표지는 그 출처의
      부모 페이지의 iframe 에는 위젯의 문서가 실리고, 다른 출처(other.localhost)의 부모 페이지의
      iframe 은 Chromium 의 오류 페이지로 끝나며 콘솔 오류가 바꿔 넣은 frame-ancestors 값을 드는
      것이다. 그리고 허용 밖 출처의 문서에서 fetch 로 값 파일을 받으면 두 값이
      읽히고(Access-Control-Allow-Origin: *), 같은 fetch 로 그 머리가 없는 위젯 페이지를 받으면
      실패한다(값 파일이 읽힌 것이 그 머리 덕이라는 대조). 그 실패의 까닭도 본다. 콘솔 오류 하나가
      위젯 페이지의 주소와 다른 출처 거절의 글을 함께 든다(cors_refused).
    - 둘째 회차: 사이트 파일의 허용 출처를 other 로, 상한을 B 의 값으로 바꾸고 다시 띄운다. 표지는
      두 부모 페이지의 결과가 뒤바뀌고 값 파일이 새 값을 내는 것이다. 뒤바뀜은 첫 회차가 표지를 본
      뒤에만 잴 수 있어, 첫 회차가 측정이 아니면 이 회차도 측정이 아니다.

    호스트 포트 둘은 free_port 가 고른 뒤 닫고 넘기므로, 그 사이에 다른 프로세스가 가져가면 부모
    페이지의 서버나 docker run 이 실패해 그 회차가 측정 아님이 된다(조용히 지나지 않는다). 컨테이너
    하나를 두 회차가 이어 쓰므로 회차가 아니라 섹션이 끝날 때 지운다.
    """
    with owned():
        browser_rounds(rounds)


def browser_rounds(rounds: Rounds) -> None:
    parent_port, widget_port = free_port(), free_port()
    serve = ("node", "tools/entry.mjs", "--hostname", "0.0.0.0", "--port", "3000")  # noqa: S104
    name = ""
    first_good = False
    with rounds.round("browser 허용 출처만 품는다") as current:
        volume = volume_with(site_text([f"http://allowed.localhost:{parent_port}"]))
        name = up(
            "image",
            *HARDENED,
            "--tmpfs",
            TMPFS,
            "-p",
            f"127.0.0.1:{widget_port}:3000",
            "-v",
            f"{volume}:/etc/agent-os/site:ro",
            site=MOUNTED,
            command=serve,
        )
        text = until(name, FIRST_OK)
        good = FIRST_OK in text and browser_phase(
            "browser 처음",
            parent_port,
            widget_port,
            allowed="allowed",
            other="other",
            chars=CHARS_A,
        )
        first_good = good
        current.mark(
            measured=good,
            result="허용 출처의 페이지만 위젯을 품었고 값 파일이 교차 출처로 읽혔다"
            if good
            else "기대와 다르다",
        )
    with rounds.round("browser 사이트 파일을 바꾸고 다시 띄운 뒤") as current:
        if not name:
            current.mark(measured=False, result="앞 회차가 컨테이너를 띄우지 못했다")
            return
        if not first_good:
            current.mark(measured=False, result="앞 회차가 표지를 보지 못해 뒤바뀜을 잴 수 없다")
            return
        swapped = site_text([f"http://other.localhost:{parent_port}"]).replace(
            f"request_chars = {CHARS_A}", f"request_chars = {CHARS_B}"
        )
        put(volume, swapped)
        restarted = docker("restart", "-t", "10", name, timeout=120)
        text = until(name, FIRST_OK, count=2)
        good = (
            restarted.code == 0
            and text.count(FIRST_OK) >= 2
            and browser_phase(
                "browser 바꾼 뒤",
                parent_port,
                widget_port,
                allowed="other",
                other="allowed",
                chars=CHARS_B,
            )
        )
        stop(name)
        current.mark(
            measured=good,
            result="다시 띄우자 품을 수 있는 출처와 값 파일이 뒤바뀌었다"
            if good
            else "기대와 다르다",
        )


# ---------------------------------------------------------------------------------------------

SECTIONS: dict[str, Callable[[Rounds, int], None]] = {
    "build": section_build,
    "start": section_start,
    "reflect": section_reflect,
    "readonly": section_readonly,
    "sitefile": section_sitefile,
    "health": section_health,
    "browser": section_browser,
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
    work = args.work or Path(tempfile.mkdtemp(prefix="wrv-prebuilt-start-"))
    work.mkdir(parents=True, exist_ok=True)
    _work.append(work)
    print(f"원본 출력: {work}", flush=True)
    leftovers()
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
