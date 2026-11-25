"""hash_load 프로브의 실행 전체. 로그인의 비밀번호 견줌이 한꺼번에 몰릴 때와 비밀번호 글자의 처리를
잰다. 해시 설정은 ADR 0062 의 것(Argon2id, m=19456, t=2, p=1, `argon2-cffi`)으로 고정이다.

두 하위 명령.
- `docker`: 호스트에서 친다. 이미 있는 이미지 `admin-login-pwhash-probe-linux:latest`(앞선 프로브
  `../password_hash/` 가 지은 것. 저장소 잠금과 argon2-cffi 가 `/app/.venv` 에 있다)로 컨테이너
  하나를 띄우고 그 안에서 `here` 를 돈다. 이미지를 짓지도 받지도 않는다. 저장소는 읽기 전용으로
  `/repo` 에, `--work` 는 `/work` 에 붙인다. 컨테이너에는 메모리 2 GiB(스왑 없음)와 CPU 0~5 의
  고정을 건다. 이름은 `admin-login-hashload-probe-<실행 토큰>` 이고 `--rm` 으로 뜨며, 끝에서 그
  이름으로 찾아 남은 것을 지운다. 컨테이너의 출력은 `--work` 의 `raw-<토큰>.log` 에 남는다.
- `here`: 이 자리(컨테이너 안이나 호스트)에서 항목을 돈다. 모든 결과는 `--work` 의
  `results-<토큰>.json` 에, 하위 프로세스의 원본 출력은 `children-<토큰>.log` 에 남는다.

항목과 표지(재려는 상황이 그 회차에 났다는 것). 표지가 없는 회차는 측정으로 세지 않고
(`tools/probe_kit.py` 의 `Rounds`), 그런 회차가 하나라도 있으면 종료 코드가 1 이다. 시간 비교는 같은
묶음(갈래마다 한 번씩을 섞은 차례로 바로 이어 돈 것)의 두 갈래를 짝지어, 짝지은 차의 윌콕슨 부호
순위 검정(정규 근사의 양쪽 p, `common.py`)으로 가른다. 문턱은 p < 0.01 이다. 짝지은 차의 중앙값과 그
붓스트랩 95% 구간, 두 갈래의 값 분포 전체를 견준 콜모고로프-스미르노프 D 와 p 는 참고로 함께 낸다.

- `unicode`(항목 4): 입력 하나가 회차 하나다. 표지는 정규화한 글로 만든 저장 값을 같은 글이
  통과하고 한 글자 더한 글이 걸리는 것(해시와 견줌이 실제로 돌았다), 또는 해시가 예외로 끝난 것이다.
- `timing`(항목 3, 함수 길): `timing.py` 를 CPU 하나에 고정해 돈다. 되풀이, 갈래, 시간의 종류(CPU
  시간과 벽시계 시간)마다 회차 하나다. 견줌의 결과가 모든 표본에서 기대대로이고, 같은 되풀이의 같은
  시간에서 작은 차의 대조 `control_plus_1ms` 가 `correct` 와 갈릴 때 대조가 아닌 갈래를 측정으로
  센다. 대조가 갈리지 않으면 그 되풀이의 그 시간은 1ms 의 차도 보지 못하는 잡음 아래였다는 뜻이라
  읽지 않는다. `control_plus_0_25ms` 와 `control_plus_5ms` 는 보는 힘의 아래 끝과 위를 알리려고
  함께 낸다.
- `alloc`(항목 1 의 덧붙임): 메모리 할당기 설정(`GLIBC_TUNABLES` 로 mmap 문턱을 정한다)이 견줌 한
  번의 시간을 바꾸는지. 설정이 프로세스마다라서 `timing.py` 를 갈래 하나로 띄운 프로세스 사이를
  견준다(`item_alloc`). 짝마다 셋(설정 없음, 설정, 설정 없이 5ms 를 더하는 양성 대조)을 섞은 차례로
  띄우고 프로세스마다 중앙값을 낸다. 회차는 비교 하나다. 결과가 모든 프로세스에서 기대대로이고 각
  프로세스가 본 설정이 준 대로일 때, 설정 비교는 거기에 양성 대조가 갈릴 때 측정으로 센다.
- `burst`(항목 1): 갈래마다 새 프로세스(`burst.py`)다. 먼저 메모리 읽기의 양성 대조(64 MiB 를 써서
  최고 상주의 차가 64 MiB 를 사이에 두는가)를 보고, 그것이 서지 않으면 뒤의 회차를 측정으로 세지
  않는다. 회차의 표지는 K 개의 견줌이 모두 참이고, 견줌 안에 동시에 있던 스레드 수의 최대값(실제로
  겹친 해시의 수)이 1 이상이고 한도를 넘지 않는 것이다. 그 최대값은 결과로 낸다. 대조 `sleep` 은
  같은 길로 `time.sleep` 을 넘긴다. 끝난 뒤에 남는 상주를 가르는 갈래가 여섯이다(K=40). 늦게
  읽기(`--late`)는 오래 논 일꾼 스레드가 정리된 뒤(살아 있는 스레드 2, 까닭은 `burst.py`)를 표지로
  더 본다. 잇달아 셋(`--repeat 3`)은 번이 셋 다 돈 것을 더 본다. 남는 상주가 새는 것인지 다시 쓰는
  것인지 가른다. 할당기 설정은 늦게 읽기에 `GLIBC_TUNABLES=glibc.malloc.mmap_threshold=131072` 를
  환경으로 준다. glibc 의 malloc 은 큰 블록을 mmap 으로 잡다가 그것을 풀면 mmap 으로 잡는 문턱을 그
  크기까지 올리고, 그 뒤의 같은 크기는 아레나에서 잡아 풀어도 운영체제에 돌려주지 않는다(어림, glibc
  의 동작으로 알려진 것이고 이 프로브에서 코드를 읽지 않았다). 문턱을 정해 주면 그 올리기가 꺼진다.
  남는 상주가 그 몫이면 이 갈래에서 사라진다. 프로세스가 그 설정을 본 것을 표지로 더 본다. 다른
  스레드 일과 잇달아 셋(`--repeat 3 --churn 40`, 한도 4 와 2)은 해시가 아닌 스레드 일이 기본
  한도로 함께 도는 동안 해시를 넘긴다. 그 일이 해시를 넘기는 동안 한 번 이상 돈 것을 표지로 더
  본다. 그 갈래에 할당기 설정(mmap 문턱)을 더한 것과 아레나를 하나로 묶는 설정
  (`glibc.malloc.arena_max=1`)을 더한 것(둘 다 한도 4)은 남는 상주를 줄이는 길을 견준다. 둘 다
  프로세스가 그 설정을 본 것을 표지로 더 본다. 모든 burst 회차는 견줌을 맡은 일꾼 스레드의 가짓수를
  함께 낸다.
- `http`(항목 2, 항목 3 의 HTTP 길): 서버 설정마다 `server.py` 를 띄우고 표본 프로세스
  (`client.py sample`)와 부하 프로세스(`client.py load`)를 다른 CPU 에 고정해 띄운다. 창(로그인 K
  개를 보낸 때부터 마지막 응답까지) 하나가 회차 하나다. 표지는 K 개가 모두 200 과 참이고, 서버가 센
  견줌 안의 동시 스레드 수의 최대값이 1 이상이고 한도를 넘지 않으며(`direct` 는 1), 창과 겹친
  표본(`/health` 나 `/thread-health`)이 하나 이상 있는 것이다. 창과 겹친 표본은 보낸 때부터 받은
  때까지가 창과 겹치는 것이고, 바탕 표본은 연결을 미리 연 뒤 0.2초부터 창 앞 0.02초까지 안에서
  보내고 받은 것이다. HTTP 길의 시간 비교(`client.py timing`)는 `thread`·기본 한도 서버에서 표본
  프로세스를 끈 뒤에 돈다. 견줌의 결과가 모든 요청에서 기대대로이고 작은 차의 대조(`plus5ms_control`
  대 `unknown`)가 갈릴 때 대조가 아닌 비교를 측정으로 센다. `plus1ms_control` 은 보는 힘의 아래
  끝을 알리려고 함께 낸다.

실행 `9f1d11` 뒤에 더한 항목 셋(결과는 실행 `075196`). 앞의 항목은 그대로이고 이 셋만 `--items` 로
따로 돌 수 있다. 표지와 문턱은 시험 실행 `b61b40`(회차를 줄인 것) 앞에 정했고 그 뒤 바꾸지 않았다.
- `burst_pool`(항목 1 의 덧붙임): 해시를 AnyIO 의 기본 일꾼 묶음이 아니라 해시만 도는 스레드
  넷(`burst.py --pool 4`)에서 돌리고 끝난 뒤에 남는 상주를 본다. 갈래는 다른 스레드 일 없이 잇달아
  셋과 다른 스레드 일과 잇달아 셋(K=40)이고, 같은 실행에서 견주려고 앞선 갈래 둘(한도 4 의 잇달아
  셋, 다른 스레드 일과 잇달아 셋)을 다시 돈다. 먼저 `burst` 와 같은 메모리 읽기의 양성 대조를 본다.
  전용 스레드 갈래의 표지는 `burst` 의 표지(`burst_round`)에 더해, 견줌을 맡은 스레드 이름이 모두
  전용 묶음의 머리이고(해시가 전용 스레드에서만 돌았다) 그 가짓수가 4 를 넘지 않는 것이다.
- `alloc_arena`(`alloc` 의 덧붙임): `alloc` 과 같은 짜임으로 아레나 하나 설정
  (`glibc.malloc.arena_max=1`)이 견줌 한 번의 시간을 바꾸는지. 짝마다 설정 없음, 아레나 하나, 설정
  없이 5ms 를 더하는 양성 대조를 섞은 차례로 띄운다(한 스레드, CPU 0). 한 스레드의 판에서는 모든
  할당이 주 아레나로 가서 아레나 수를 묶어도 달라질 것이 없다는 해석(어림)을 가르려고, 같은 짜임을
  스레드 넷이 함께 해시하는 판(`timing.py --threads 4`, CPU 0~3)으로 한 번 더 돈다. 그 판에는 mmap
  문턱 설정도 넣는다. 회차의 표지는 `alloc` 의 것(결과가 기대대로, 프로세스가 본 설정이 준 대로,
  양성 대조가 갈린다)에 더해, 스레드 넷의 판에서는 견줌을 맡은 스레드가 넷이고 호출의 90% 이상에서
  넷이 함께 견줌 안에 있었던 것이다(`FULL_SHARE`).
- `http_pool`(항목 2 의 덧붙임): `server.py --mode pool --limit 4`(해시만 도는 스레드 넷)를 CPU 4
  개에 띄워 `http` 와 같은 창을 돈다. 같은 실행에서 견주려고 `thread` 한도 4 서버를 다시 돈다. 창의
  표지는 `http` 의 것에 더해, 전용 스레드 서버에서는 서버가 센 견줌 스레드 이름이 모두 전용 묶음의
  머리이고 그 가짓수가 4 를 넘지 않는 것이다.

판정 기준을 바꾼 것(모두 시험 실행의 결과를 본 뒤다).
- 첫 판은 burst 와 http 의 표지를 "동시 스레드 수의 최대값이 `min(K, 한도)` 와 같다"로 두었다. 시험
  실행 `c00f0f`(CPU 2 개, 회차마다 1 번)에서 기본 한도의 K=40 이 35, HTTP 의 K=16·40·100 이
  15·31·34 였다. 해시가 겹치는 수가 CPU 와 요청이 닿는 빠르기에 따라 K 보다 적은 것이 재려는 상황의
  결과이지 그 상황이 나지 않은 것이 아니라서, 표지를 "1 이상이고 한도를 넘지 않는다"로 바꾸고 그
  최대값을 결과로 낸다.
- 첫 판의 시간 비교는 모든 표본을 한꺼번에 섞은 차례로 돌고 두 갈래의 값 분포를 짝짓지 않고
  견줬다(콜모고로프-스미르노프 검정). `c00f0f` 에서 1ms 대조가 벽시계 시간으로 갈리지 않아(n=20)
  CPU 시간을 더하고 벽시계 시간의 대조를 5ms 로 바꿨다. 둘째 시험 실행(CPU 시간과 벽시계 시간,
  n=30)에서도 1ms 대조가 두 시간 모두 갈리지 않았다(CPU 시간이 벽시계 시간과 거의 같아 잡음을 덜지
  못했다). 그래서 묶음으로 짝짓는 짜임과 부호 순위 검정으로 바꾸고, 함수 길의 대조를 두 시간 모두
  1ms 로 되돌렸다. HTTP 길의 대조는 5ms 그대로다.
- 첫 판의 `--late` 표지는 "12초 쉰 뒤 살아 있는 스레드 1"이었다. 둘째 시험 실행에서 41 과 5 가
  나왔고, AnyIO 의 일꾼이 스스로 끝나지 않는다는 것을 코드에서 읽어 빈 일 하나로 정리를 부르고
  표지를 2 로 바꿨다(`burst.py`).

CPU 배치(리눅스만). 서버와 `burst.py` 는 CPU 0 부터 `--server-cpus` 개, 표본 프로세스는 CPU 4,
부하 프로세스는 CPU 5, `timing.py` 는 CPU 0 이다. 윈도에서는 고정하지 않는다.

프로세스 끄기. 서버는 이 스크립트가 띄운 자식이고 끄기 전에 `/proc/<pid>/cmdline` 에 그 서버의
포트와 `server.py` 가 있는지 본다(윈도에서는 `Popen` 이 쥔 프로세스 핸들이 pid 를 묶어 두므로 보지
않는다). 표본 프로세스는 끄지 않고 멈춤 파일로 끝낸다.

못 보는 것.
- 배포할 서버의 CPU 수와 다른 일. CPU 를 2·4 개로 고정한 이 PC 의 WSL2 위 컨테이너만 본다. 고정한
  CPU 가 같은 물리 코어의 두 하이퍼스레드인지는 모른다. 같은 PC 를 다른 세션이 함께 쓴다.
- 실제 제품의 로그인 길(데이터베이스 조회, 세션 쿠키, 요청 출처 검사). 흉내 낸 앱의 견줌만 본다.
- 잡았다가 쓰지 않은 메모리. 상주 메모리만 읽는다.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import random
import secrets
import statistics
import subprocess
import sys
import time
import unicodedata
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from common import (  # noqa: E402
    MIB,
    ks_p_value,
    ks_statistic,
    median_interval,
    quantile,
    signed_rank,
    summary,
)
from tools.probe_kit import LineReader, Rounds  # noqa: E402

PREFIX = "admin-login-hashload-probe"
IMAGE = "admin-login-pwhash-probe-linux:latest"
PYTHON_IN_IMAGE = "/app/.venv/bin/python"
PROBE_IN_CONTAINER = "/repo/.scratch/admin-login/probes/hash_load"
CONTAINER_CPUS = "0-5"
CONTAINER_MEMORY = "2g"
SERVER_CPU_POOL = (0, 1, 2, 3)
SAMPLER_CPU = "4"
LOAD_CPU = "5"
TIMING_CPU = "0"
KS = (1, 4, 16, 40, 100)
LIMITS = (0, 4, 2)
LATE_SECONDS = 12.0
LATE_THREADS = 2
REPEAT = 3
CHURN = 40
TUNABLE = "glibc.malloc.mmap_threshold=131072"
ARENA_ONE = "glibc.malloc.arena_max=1"
POOL = 4
TOGETHER = 4
FULL_SHARE = 0.9
HTTP_POOL_CPUS = 4
ALPHA = 0.01
TIMING_GATE = "control_plus_1ms"
HTTP_GATE = "plus5ms_control"
PACKAGES = ("argon2-cffi", "argon2-cffi-bindings", "anyio", "starlette", "uvicorn", "httpx", "h11")
OPTIONAL = ("uvloop", "httptools")
LINUX = sys.platform.startswith("linux")

Verdict = tuple[bool, str, str]


@dataclass
class Context:
    rounds: Rounds
    work: Path
    token: str
    log: IO[str]
    options: argparse.Namespace
    results: dict[str, object] = field(default_factory=dict[str, object])

    def judge(self, label: str, verdict: Callable[[], Verdict]) -> bool:
        """회차 하나를 세고 한 줄로 낸다. 판정은 (측정인가, 결과의 갈래, 자세한 값) 이다. 판정이
        예외로 끝나면 측정 아님으로 센다."""
        detail = ""
        with self.rounds.round(label) as slot:
            measured, result, detail = verdict()
            slot.mark(measured=measured, result=result)
        entry = self.rounds.entries[-1]
        mark = "측정" if entry.measured else "측정 아님"
        tail = f" | {detail}" if detail else ""
        print(f"- [{mark}] {entry.label} => {entry.result}{tail}", flush=True)
        return entry.measured


def child_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env.update(extra or {})
    return env


def child(
    ctx: Context, argv: Sequence[str], timeout: float, extra: dict[str, str] | None = None
) -> str:
    """하위 프로세스 하나를 끝까지 돌리고 표준 출력을 돌려준다. 원본은 기록에 남긴다."""
    started = time.monotonic()
    shown = " ".join(f"{name}={value}" for name, value in (extra or {}).items())
    command = f"{shown} {' '.join(argv)}".strip()
    try:
        done = subprocess.run(
            list(argv),
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=child_env(extra),
            check=False,
        )
    except subprocess.TimeoutExpired:
        ctx.log.write(f"$ {command}\n{timeout:.0f}초 안에 끝나지 않았다\n")
        return ""
    seconds = time.monotonic() - started
    ctx.log.write(
        f"$ {command}\nexit={done.returncode} seconds={seconds:.1f}\n"
        f"--- stdout\n{done.stdout}\n--- stderr\n{done.stderr}\n"
    )
    ctx.log.flush()
    return done.stdout


def result_of(text: str) -> dict[str, object]:
    lines = [line for line in text.splitlines() if line.startswith("RESULT ")]
    if not lines:
        raise ValueError("RESULT 줄이 없다")
    found: dict[str, object] = json.loads(lines[-1][len("RESULT ") :])
    return found


def num(value: object) -> float:
    """JSON 에서 읽은 수."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(f"수가 아니다: {value!r}")
    return float(value)


def floats(value: object) -> list[float]:
    """JSON 에서 읽은 수의 목록."""
    if not isinstance(value, list):
        raise TypeError(f"목록이 아니다: {value!r}")
    items: list[object] = list(value)
    return [num(item) for item in items]


def mapping(value: object) -> dict[str, object]:
    """JSON 에서 읽은 객체."""
    if not isinstance(value, dict):
        raise TypeError(f"객체가 아니다: {value!r}")
    found: dict[str, object] = {str(key): item for key, item in value.items()}
    return found


def records(value: object) -> list[dict[str, object]]:
    """JSON 에서 읽은 객체의 목록."""
    if not isinstance(value, list):
        raise TypeError(f"목록이 아니다: {value!r}")
    items: list[object] = list(value)
    return [mapping(item) for item in items]


def ms(value: float) -> str:
    return f"{value * 1000:.1f}"


def us(value: float) -> str:
    return f"{value * 1_000_000:.0f}"


def mib(value: float) -> str:
    return f"{value / MIB:.1f}"


def server_cpus(count: int) -> str:
    if not LINUX:
        return ""
    return ",".join(str(cpu) for cpu in SERVER_CPU_POOL[:count])


def pinned(cpu: str) -> str:
    return cpu if LINUX else ""


def rows(value: object) -> list[list[float]]:
    """JSON 에서 읽은 수 목록의 목록(`[묶음 번호, 값, ...]`)."""
    if not isinstance(value, list):
        raise TypeError(f"목록이 아니다: {value!r}")
    items: list[object] = list(value)
    return [floats(item) for item in items]


@dataclass
class Series:
    """한 갈래의 표본. 묶음 번호에서 한 열의 값으로."""

    entries: list[list[float]]
    column: int

    def values(self) -> list[float]:
        return [entry[self.column] for entry in self.entries]

    def by_block(self) -> dict[int, float]:
        return {int(entry[0]): entry[self.column] for entry in self.entries}


def paired_compare(left: Series, right: Series, *, seed: int, unit: str) -> tuple[float, str]:
    """같은 묶음의 두 값을 짝지어 견준다. (부호 순위 검정의 p, 자세한 값). 차는 오른쪽 - 왼쪽이다.

    판정은 짝지은 차의 부호 순위 검정이다. 두 갈래의 값 분포 전체를 견준 콜모고로프-스미르노프 D 와
    p 는 참고로 함께 적는다. `unit` 은 `us` 나 `ms` 다."""
    found = left.by_block()
    differences = [
        value - found[block] for block, value in right.by_block().items() if block in found
    ]
    if not differences:
        return 1.0, "짝이 없다"
    z, p = signed_rank(differences)
    median, low, high = median_interval(differences, seed=seed)
    left_values, right_values = left.values(), right.values()
    d = ks_statistic(left_values, right_values)
    ks_p = ks_p_value(d, len(left_values), len(right_values))
    show = us if unit == "us" else ms
    detail = (
        f"짝 {len(differences)}, 짝지은 차의 중앙 {show(median)} {unit}"
        f"(95% {show(low)}~{show(high)}), 부호 순위 z={z:.2f} p={p:.4f}, "
        f"분포 D={d:.3f} p={ks_p:.4f}"
    )
    return p, detail


def separated(p: float) -> str:
    return "갈린다" if p < ALPHA else "가르지 못했다"


# ---------------------------------------------------------------- 환경


def facts() -> dict[str, object]:
    found: dict[str, object] = {
        "platform": sys.platform,
        "python": sys.version,
        "cpu_count": os.cpu_count(),
        "unidata_version": unicodedata.unidata_version,
    }
    for name in (*PACKAGES, *OPTIONAL):
        try:
            found[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            found[name] = None
    if LINUX:
        found["libc"] = os.confstr("CS_GNU_LIBC_VERSION")
        found["affinity"] = sorted(os.sched_getaffinity(0))
        for name in ("memory.max", "memory.swap.max", "cpu.max", "cpuset.cpus.effective"):
            path = Path("/sys/fs/cgroup") / name
            found[name] = path.read_text(encoding="ascii").strip() if path.exists() else None
    return found


# ---------------------------------------------------------------- unicode


def item_unicode(ctx: Context) -> None:
    data = result_of(child(ctx, [sys.executable, str(HERE / "unicode_check.py")], 300))
    ctx.results["unicode"] = data
    print(f"유니코드 판 {data['unidata_version']}", flush=True)
    print(
        "  입력 | 바뀜 | 코드 포인트 앞→뒤 | UTF-8 바이트 앞→뒤 | UTF-16 단위 앞→뒤"
        " | 규칙(ascii) 앞→뒤 | 규칙(unicode) 앞→뒤",
        flush=True,
    )
    for row in records(data["rows"]):
        ctx.judge(f"unicode {row['label']}", lambda row=row: unicode_verdict(row))
        rules = [
            "/".join("통과" if mapping(one)["pass"] else "걸림" for one in records(row[name]))
            for name in ("rule_ascii", "rule_unicode")
        ]
        points, octets, units = (floats_or_none(row[name]) for name in counts_names())
        print(
            f"  {row['label']} | {row['changed']} | {points} | {octets} | {units} | "
            f"{rules[0]} | {rules[1]}",
            flush=True,
        )


def counts_names() -> tuple[str, str, str]:
    return ("code_points", "utf8_bytes", "utf16_units")


def floats_or_none(value: object) -> str:
    if not isinstance(value, list):
        raise TypeError(f"목록이 아니다: {value!r}")
    items: list[object] = list(value)
    return "→".join("인코딩 불가" if item is None else str(item) for item in items)


def unicode_verdict(row: dict[str, object]) -> Verdict:
    trip = mapping(row["round_trip"])
    if "hash_error" in trip:
        return True, f"해시가 {trip['hash_error']}", str(trip.get("hash_error_text", ""))
    if trip.get("same") is True and trip.get("plus_one") is False:
        tail = ""
        if "original_against_normal" in trip:
            tail = f", 정규화 앞의 글은 {'통과' if trip['original_against_normal'] else '걸림'}"
        if "before_nul" in trip:
            tail += f", NUL 앞까지의 글은 {'통과' if trip['before_nul'] else '걸림'}"
        detail = f"마지막 글자를 뺀 글은 {'통과' if trip['minus_last'] else '걸림'}{tail}"
        return True, "왕복 됨", detail
    return False, "견줌이 가르지 못했다", json.dumps(trip, ensure_ascii=False)


# ---------------------------------------------------------------- timing


def item_timing(ctx: Context) -> None:
    argv = [sys.executable, str(HERE / "timing.py"), "--cpus", pinned(TIMING_CPU)]
    argv += ["--n", str(ctx.options.timing_n), "--repeats", str(ctx.options.timing_repeats)]
    data = result_of(child(ctx, argv, 3600))
    ctx.results["timing"] = data
    for index, repeat in enumerate(records(data["repeats"]), start=1):
        arms = {name: rows(values) for name, values in mapping(repeat["samples"]).items()}
        expected = mapping(repeat["expected"])
        outcomes = {name: num(expected[name]) == len(arms[name]) for name in arms}
        for kind, column in (("CPU", 2), ("벽시계", 1)):
            series = {name: Series(values, column) for name, values in arms.items()}
            timing_repeat(ctx, index, kind, series, outcomes)


def timing_repeat(
    ctx: Context,
    index: int,
    kind: str,
    series: dict[str, Series],
    outcomes: dict[str, bool],
) -> None:
    base = series["correct"]
    gate_p, _ = paired_compare(base, series[TIMING_GATE], seed=index, unit="us")
    power = gate_p < ALPHA and outcomes[TIMING_GATE]
    for arm_index, (arm, values) in enumerate(series.items()):
        stats = summary(values.values())
        print(
            f"  되풀이 {index} {kind} {arm}: 중앙 {ms(stats['median'])} ms, 10~90 분위 "
            f"{ms(stats['p10'])}~{ms(stats['p90'])}, 최소 {ms(stats['min'])}, 최대 "
            f"{ms(stats['max'])}, n={stats['n']}, 기대대로 {outcomes[arm]}",
            flush=True,
        )
        if arm == "correct":
            continue
        p, detail = paired_compare(base, values, seed=index * 100 + arm_index, unit="us")
        both = outcomes[arm] and outcomes["correct"]
        ok = both if arm.startswith("control") else both and power
        if not ok:
            detail += f" (결과 기대대로 {both}, {TIMING_GATE} 대조 섰나 {power})"
        ctx.judge(
            f"timing 되풀이 {index} {kind} correct 대 {arm}",
            lambda ok=ok, p=p, detail=detail: (ok, separated(p), detail),
        )


# ---------------------------------------------------------------- alloc


def alloc_kinds() -> list[tuple[str, str, dict[str, str] | None]]:
    """(이름, `timing.py` 의 갈래, 더할 환경). `control` 은 프로세스 사이 비교의 양성 대조다."""
    return [
        ("plain", "correct", None),
        ("tunable", "correct", {"GLIBC_TUNABLES": TUNABLE}),
        ("control", "control_plus_5ms", None),
    ]


@dataclass
class AllocShape:
    """`alloc` 짜임 하나. `head` 는 회차 이름의 머리, `key` 는 결과의 자리, `kinds` 는
    `alloc_kinds` 꼴(첫째가 `plain`, `control` 이 양성 대조), `threads` 는 `timing.py --threads`."""

    head: str
    key: str
    kinds: list[tuple[str, str, dict[str, str] | None]]
    threads: int
    cpus: str


def alloc_process(
    ctx: Context, shape: AllocShape, pair: int, arm: str, extra: dict[str, str] | None
) -> tuple[float, bool, str]:
    """프로세스 하나의 견줌 시간 중앙값(벽시계)과, 결과가 기대대로이고 설정을 본 대로인가(스레드
    여럿의 판이면 그 스레드가 함께 견줌 안에 있었나까지), 그 동시의 셈."""
    argv = [sys.executable, str(HERE / "timing.py"), "--cpus", shape.cpus]
    argv += ["--n", str(ctx.options.alloc_n), "--repeats", "1", "--arms", arm]
    argv += ["--seed", str(pair)]
    if shape.threads > 1:
        argv += ["--threads", str(shape.threads)]
    data = result_of(child(ctx, argv, 600, extra))
    repeat = records(data["repeats"])[0]
    values = Series(rows(mapping(repeat["samples"])[arm]), 1).values()
    expected = num(mapping(repeat["expected"])[arm]) == len(values) > 0
    seen = mapping(data["malloc_env"]).get("GLIBC_TUNABLES")
    want = extra.get("GLIBC_TUNABLES") if extra else None
    ok = expected and seen == want
    note = ""
    if shape.threads > 1:
        together = mapping(data["concurrency"])
        calls, full = num(together["calls"]), num(together["full"])
        threads = int(num(together["threads"]))
        ok = ok and threads == shape.threads and calls > 0 and full / calls >= FULL_SHARE
        note = f"넷이 함께 {full:.0f}/{calls:.0f}, 스레드 {threads}"
    return statistics.median(values), ok, note


def alloc_compare(ctx: Context, shape: AllocShape) -> None:
    """설정은 프로세스마다라서 같은 프로세스 안에서 짝지을 수 없다. 짝 하나가 `shape.kinds` 의
    프로세스를 섞은 차례로 하나씩 띄우고, 프로세스마다 견줌 `--alloc-n` 번의 중앙값을 낸다. 같은
    짝의 두 프로세스를 짝지어 견준다. 양성 대조(`control`)가 갈려야 설정의 비교를 측정으로 센다."""
    chooser = random.Random(5)
    medians: dict[str, list[list[float]]] = {name: [] for name, _, _ in shape.kinds}
    good: dict[str, bool] = {name: True for name, _, _ in shape.kinds}
    notes: dict[str, list[str]] = {name: [] for name, _, _ in shape.kinds}
    for pair in range(ctx.options.alloc_pairs):
        order = list(shape.kinds)
        chooser.shuffle(order)
        for name, arm, extra in order:
            median, ok, note = alloc_process(ctx, shape, pair, arm, extra)
            medians[name].append([float(pair), median])
            good[name] = good[name] and ok
            if note:
                notes[name].append(note)
    found: dict[str, object] = {"medians": medians, "good": good}
    if shape.threads > 1:
        found["notes"] = notes
    ctx.results[shape.key] = found
    series = {name: Series(values, 1) for name, values in medians.items()}
    for name, values in series.items():
        stats = summary(values.values())
        tail = f", {'; '.join(notes[name])}" if notes[name] else ""
        print(
            f"  {shape.head} {name}: 프로세스 중앙값의 중앙 {ms(stats['median'])} ms, 최소 "
            f"{ms(stats['min'])}, 최대 {ms(stats['max'])}, 프로세스 {stats['n']}, "
            f"기대대로 {good[name]}{tail}",
            flush=True,
        )
    gate_p, gate_detail = paired_compare(series["plain"], series["control"], seed=1, unit="ms")
    control_ok = good["plain"] and good["control"]
    ctx.judge(
        f"{shape.head} 프로세스 사이 plain 대 control(+5ms)",
        lambda: (control_ok, separated(gate_p), gate_detail),
    )
    power = control_ok and gate_p < ALPHA
    others = [name for name, _, _ in shape.kinds if name not in ("plain", "control")]
    for index, name in enumerate(others, start=2):
        p, detail = paired_compare(series["plain"], series[name], seed=index, unit="ms")
        both = good["plain"] and good[name]
        ok = both and power
        if not ok:
            detail += f" (결과와 설정 기대대로 {both}, 대조 섰나 {power})"
        ctx.judge(
            f"{shape.head} 프로세스 사이 plain 대 {name}",
            lambda ok=ok, p=p, detail=detail: (ok, separated(p), detail),
        )


def item_alloc(ctx: Context) -> None:
    """할당기 설정(`TUNABLE`)이 견줌 한 번의 시간을 바꾸는지(`alloc_compare`, 한 스레드, CPU 0)."""
    alloc_compare(ctx, AllocShape("alloc", "alloc", alloc_kinds(), 1, pinned(TIMING_CPU)))


def item_alloc_arena(ctx: Context) -> None:
    """아레나 하나 설정(`ARENA_ONE`)이 견줌 한 번의 시간을 바꾸는지. 한 스레드(CPU 0)와, 스레드
    넷이 함께 해시하는 판(CPU 0~3. mmap 문턱 설정도 함께 견준다)."""
    plain = ("plain", "correct", None)
    arena = ("arena", "correct", {"GLIBC_TUNABLES": ARENA_ONE})
    tunable = ("tunable", "correct", {"GLIBC_TUNABLES": TUNABLE})
    control = ("control", "control_plus_5ms", None)
    single = AllocShape(
        "alloc_arena 한 스레드",
        "alloc_arena_single",
        [plain, arena, control],
        1,
        pinned(TIMING_CPU),
    )
    alloc_compare(ctx, single)
    together = AllocShape(
        f"alloc_arena 스레드 {TOGETHER} 함께",
        "alloc_arena_together",
        [plain, arena, tunable, control],
        TOGETHER,
        server_cpus(TOGETHER),
    )
    alloc_compare(ctx, together)


# ---------------------------------------------------------------- burst


def control_memory(ctx: Context) -> bool:
    argv = [sys.executable, str(HERE / "burst.py"), "--k", "0", "--work", "control"]
    argv += ["--cpus", server_cpus(1)]

    def verdict() -> Verdict:
        data = result_of(child(ctx, argv, 120))
        low = num(data["peak_after"]) - num(data["peak_before"])
        high = num(data["peak_after"]) - num(data["rss_before"])
        nominal = num(data["nominal_bytes"])
        ok = bool(data["genuine"]) and low <= nominal + MIB / 2 and high >= nominal - MIB / 2
        detail = f"최고 상주가 는 양 {mib(low)}~{mib(high)} MiB(쓴 양 {mib(nominal)} MiB)"
        return ok, "읽기가 쓴 양을 본다" if ok else "읽기가 쓴 양을 보지 못했다", detail

    return ctx.judge("burst 메모리 읽기의 양성 대조", verdict)


def burst_arms() -> list[tuple[str, int, int]]:
    arms = [("argon2", k, limit) for limit in LIMITS for k in KS]
    arms += [("sleep", k, 0) for k in (40, 100)]
    return arms


def burst_round(
    ctx: Context,
    argv: list[str],
    *,
    control_ok: bool,
    kind: str,
    store: list[dict[str, object]],
) -> Verdict:
    """`kind` 는 `plain`, `late`(늦게 읽기), `repeat`(잇달아 넘기기), `tunable`(할당기 설정),
    `churn`(다른 스레드 일과 함께), `churn_tunable`(다른 스레드 일과 함께, 할당기 설정),
    `churn_arena`(다른 스레드 일과 함께, 아레나 하나), `pool_repeat`(전용 스레드, 잇달아 넘기기),
    `pool_churn`(전용 스레드, 다른 스레드 일과 함께)."""
    tunable = KIND_TUNABLES.get(kind)
    extra = {"GLIBC_TUNABLES": tunable} if tunable else None
    data = result_of(child(ctx, argv, 600, extra))
    peak = int(num(data["peak_inside"]))
    tokens = int(num(data["tokens"]))
    ok = control_ok and bool(data["genuine"]) and 1 <= peak <= tokens
    detail = f"동시 {peak}(한도 {tokens}), 견줌을 맡은 스레드 {int(num(data['hash_threads']))}"
    if kind in POOL_KINDS:
        dedicated = data.get("dedicated") is True
        threads = int(num(data["hash_threads"]))
        ok = ok and dedicated and threads <= tokens and int(num(data["pool"])) == POOL
        detail += f", 전용 스레드에서만 {dedicated}"
    if kind in CHURN_KINDS:
        during = int(num(data["churn_during"]))
        ok = ok and during >= 1
        detail += f", 그동안 다른 스레드 일 {during}"
    if kind in ("late", "tunable"):
        threads = int(num(data["threads_late"]))
        ok = ok and threads == LATE_THREADS
        detail += f", {LATE_SECONDS:.0f}초 뒤 스레드 {threads}"
    base = num(data["rss_before"])
    if kind in ("repeat", "pool_repeat") or kind in CHURN_KINDS:
        repeats = rows(data["repeats"])
        ok = ok and len(repeats) == REPEAT
        detail += ", 번마다 끝난 직후 는 상주 / 최고 상주 " + " · ".join(
            f"{mib(rss - base)} / {mib(peak_after - base)}" for rss, peak_after in repeats
        )
    if tunable:
        seen = mapping(data["malloc_env"]).get("GLIBC_TUNABLES")
        ok = ok and seen == tunable
        detail += f", 프로세스가 본 설정 {seen}, 끝난 직후 는 상주 "
        detail += f"{mib(num(data['rss_after']) - base)} MiB"
    if ok:
        store.append(data)
    return ok, "한도 안에서 겹쳤다" if ok else "표지 없음", detail


def item_burst(ctx: Context) -> None:
    control_ok = control_memory(ctx)
    stored: dict[str, list[dict[str, object]]] = {}
    counts = ctx.options.server_cpus if LINUX else [0]
    for count in counts:
        for index in range(ctx.options.burst_rounds):
            for work, k, limit in burst_arms():
                key = f"cpu{count} {work} K={k} 한도={limit or '기본'}"
                argv = [sys.executable, str(HERE / "burst.py"), "--k", str(k)]
                argv += ["--limit", str(limit), "--work", work, "--cpus", server_cpus(count)]
                store = stored.setdefault(key, [])
                ctx.judge(
                    f"burst {key} #{index + 1}",
                    lambda argv=argv, store=store: burst_round(
                        ctx, argv, control_ok=control_ok, kind="plain", store=store
                    ),
                )
        for index in range(ctx.options.late_rounds):
            for kind, limit, tail in retention_arms():
                key = f"cpu{count} argon2 K=40 한도={limit or '기본'} {RETENTION_NAMES[kind]}"
                argv = [sys.executable, str(HERE / "burst.py"), "--k", "40"]
                argv += ["--limit", str(limit), "--cpus", server_cpus(count), *tail]
                store = stored.setdefault(key, [])
                ctx.judge(
                    f"burst {key} #{index + 1}",
                    lambda argv=argv, store=store, kind=kind: burst_round(
                        ctx, argv, control_ok=control_ok, kind=kind, store=store
                    ),
                )
    ctx.results["burst"] = stored
    burst_table(stored)


RETENTION_NAMES = {
    "late": "늦게 읽기",
    "repeat": "잇달아 셋",
    "tunable": "할당기 설정",
    "churn": "다른 스레드 일과 잇달아 셋",
    "churn_tunable": "다른 스레드 일과 잇달아 셋, 할당기 설정",
    "churn_arena": "다른 스레드 일과 잇달아 셋, 아레나 하나",
}
KIND_TUNABLES = {"tunable": TUNABLE, "churn_tunable": TUNABLE, "churn_arena": ARENA_ONE}
CHURN_KINDS = ("churn", "churn_tunable", "churn_arena", "pool_churn")
POOL_KINDS = ("pool_repeat", "pool_churn")
POOL_NAMES = {
    "pool_repeat": f"전용 스레드 {POOL}, 잇달아 셋",
    "pool_churn": f"전용 스레드 {POOL}, 다른 스레드 일과 잇달아 셋",
    "repeat": "한도 4, 잇달아 셋(같은 실행의 견줌)",
    "churn": "한도 4, 다른 스레드 일과 잇달아 셋(같은 실행의 견줌)",
}


def pool_arms() -> list[tuple[str, list[str]]]:
    """`burst_pool` 의 갈래. (종류, 넘길 인자). 견줌인 앞선 갈래 둘은 `retention_arms` 의 것과
    같다."""
    repeat = ["--repeat", str(REPEAT)]
    churn = [*repeat, "--churn", str(CHURN)]
    pool = ["--limit", "0", "--pool", str(POOL)]
    return [
        ("pool_repeat", [*pool, *repeat]),
        ("pool_churn", [*pool, *churn]),
        ("repeat", ["--limit", "4", *repeat]),
        ("churn", ["--limit", "4", *churn]),
    ]


def item_burst_pool(ctx: Context) -> None:
    control_ok = control_memory(ctx)
    stored: dict[str, list[dict[str, object]]] = {}
    counts = ctx.options.server_cpus if LINUX else [0]
    for count in counts:
        for index in range(ctx.options.late_rounds):
            for kind, tail in pool_arms():
                key = f"cpu{count} argon2 K=40 {POOL_NAMES[kind]}"
                argv = [sys.executable, str(HERE / "burst.py"), "--k", "40"]
                argv += ["--cpus", server_cpus(count), *tail]
                store = stored.setdefault(key, [])
                ctx.judge(
                    f"burst_pool {key} #{index + 1}",
                    lambda argv=argv, store=store, kind=kind: burst_round(
                        ctx, argv, control_ok=control_ok, kind=kind, store=store
                    ),
                )
    ctx.results["burst_pool"] = stored
    burst_table(stored)
    pool_table(stored)


def pool_table(stored: dict[str, list[dict[str, object]]]) -> None:
    """회차마다 한 줄. 남는 상주와 최고 상주는 해시 앞의 바닥(`rss_before`)에서 잰 MiB 다."""
    print(
        "burst_pool 회차: 갈래 | 견줌 스레드 가짓수 | 번마다 끝난 직후 남는 상주"
        " | 0.5초 뒤 남는 상주 | 최고 상주가 는 양(아래 끝~위 끝) | 첫 번의 요청 중앙 / 최대 ms"
        " | 그동안 다른 스레드 일",
        flush=True,
    )
    for key, items in stored.items():
        for data in items:
            base = num(data["rss_before"])
            waves = rows(data["repeats"])
            last_peak = max(peak for _, peak in waves)
            low = last_peak - num(data["peak_before"])
            latencies = floats(data["latencies"])
            print(
                f"  {key} | {num(data['hash_threads']):.0f} | "
                + " · ".join(mib(rss - base) for rss, _ in waves)
                + f" | {mib(num(data['rss_idle']) - base)} | {mib(low)}~{mib(last_peak - base)}"
                f" | {ms(statistics.median(latencies))} / {ms(max(latencies))}"
                f" | {num(data['churn_during']):.0f}",
                flush=True,
            )


def retention_arms() -> list[tuple[str, int, list[str]]]:
    """끝난 뒤에 남는 상주를 가르는 갈래. (종류, 한도, 더 넘길 인자)."""
    late = ["--late", str(LATE_SECONDS)]
    repeat = ["--repeat", str(REPEAT)]
    return [
        ("late", 0, late),
        ("late", 4, late),
        ("repeat", 0, repeat),
        ("repeat", 4, repeat),
        ("tunable", 0, late),
        ("churn", 4, [*repeat, "--churn", str(CHURN)]),
        ("churn", 2, [*repeat, "--churn", str(CHURN)]),
        ("churn_tunable", 4, [*repeat, "--churn", str(CHURN)]),
        ("churn_arena", 4, [*repeat, "--churn", str(CHURN)]),
    ]


def burst_table(stored: dict[str, list[dict[str, object]]]) -> None:
    print(
        "burst 표: 갈래 | 회차 | 동시(최소~최대) | 견줌 스레드 가짓수(최소~최대)"
        " | 최고 상주가 는 양 MiB(아래 끝 최소~위 끝 최대)"
        " | 견줌 스레드 하나당 MiB 중앙 | 끝난 직후 는 양 중앙 | 0.5초 뒤 중앙 | 12초 뒤 중앙"
        " | 걸린 시간 ms 중앙(회차 중앙의 중앙) | 최대 | 전체 중앙",
        flush=True,
    )
    for key, items in stored.items():
        if not items:
            print(f"  {key} | 0", flush=True)
            continue
        peaks = [num(d["peak_inside"]) for d in items]
        kinds = [num(d["hash_threads"]) for d in items]
        low = [num(d["peak_after"]) - num(d["peak_before"]) for d in items]
        high = [num(d["peak_after"]) - num(d["rss_before"]) for d in items]
        each = [gap / count for gap, count in zip(low, kinds, strict=True)]
        after = [num(d["rss_after"]) - num(d["rss_before"]) for d in items]
        idle = [num(d["rss_idle"]) - num(d["rss_before"]) for d in items]
        late = [num(d["rss_late"]) - num(d["rss_before"]) for d in items if "rss_late" in d]
        medians = [statistics.median(floats(d["latencies"])) for d in items]
        maxima = [max(floats(d["latencies"])) for d in items]
        walls = [num(d["wall"]) for d in items]
        late_text = mib(statistics.median(late)) if late else "-"
        print(
            f"  {key} | {len(items)} | {min(peaks):.0f}~{max(peaks):.0f} | "
            f"{min(kinds):.0f}~{max(kinds):.0f} | "
            f"{mib(min(low))}~{mib(max(high))} | {mib(statistics.median(each))} | "
            f"{mib(statistics.median(after))} | {mib(statistics.median(idle))} | {late_text} | "
            f"{ms(statistics.median(medians))} | {ms(max(maxima))} | "
            f"{ms(statistics.median(walls))}",
            flush=True,
        )


# ---------------------------------------------------------------- http


def wait_ready(port: int, seconds: float) -> dict[str, object] | None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/stats", timeout=2) as answer:
                return mapping(json.loads(answer.read()))
        except OSError:
            time.sleep(0.2)
    return None


def ours(process: subprocess.Popen[bytes], port: int) -> bool:
    """끄기 직전에 그 pid 가 이 회차의 서버인지 본다(리눅스). 윈도는 핸들이 pid 를 묶는다."""
    if not LINUX:
        return True
    path = Path(f"/proc/{process.pid}/cmdline")
    if not path.exists():
        return False
    words = path.read_bytes().split(b"\0")
    has_port = b"--port" in words and str(port).encode() in words
    return has_port and any(word.endswith(b"server.py") for word in words)


def stop_server(process: subprocess.Popen[bytes], port: int) -> None:
    if process.poll() is not None:
        return
    if ours(process, port):
        process.terminate()
    try:
        process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        if ours(process, port):
            process.kill()
        process.wait(timeout=30)


def http_configs() -> list[tuple[str, int, tuple[int, ...]]]:
    return [
        ("thread", 0, KS),
        ("thread", 4, KS),
        ("thread", 2, KS),
        ("sleep", 0, KS),
        ("direct", 0, (1, 4, 16)),
    ]


@dataclass
class Serving:
    port: int
    count: int
    mode: str
    limit: int
    ks: tuple[int, ...]
    windows: list[dict[str, object]] = field(default_factory=list[dict[str, object]])
    samples: list[dict[str, object]] = field(default_factory=list[dict[str, object]])
    timing: dict[str, object] | None = None
    ready: dict[str, object] | None = None


def serve_once(ctx: Context, serving: Serving, *, with_timing: bool) -> None:
    port = serving.port
    server_log = ctx.work / f"server-{ctx.token}-{port}.log"
    samples_path = ctx.work / f"samples-{ctx.token}-{port}.jsonl"
    stop = ctx.work / f"stop-{ctx.token}-{port}"
    argv = [sys.executable, str(HERE / "server.py"), "--port", str(port)]
    argv += ["--mode", serving.mode, "--limit", str(serving.limit)]
    argv += ["--cpus", server_cpus(serving.count)]
    with server_log.open("wb") as log:
        server = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, env=child_env())
    try:
        serving.ready = wait_ready(port, 60)
        if serving.ready is None:
            return
        run_load(ctx, serving, samples_path, stop)
        if with_timing:
            argv = [sys.executable, str(HERE / "client.py"), "timing", "--port", str(port)]
            argv += ["--cpus", pinned(LOAD_CPU), "--n", str(ctx.options.http_timing_n)]
            serving.timing = result_of(child(ctx, argv, 1800))
    finally:
        stop_server(server, port)
    if samples_path.exists():
        lines = samples_path.read_text(encoding="utf-8").splitlines()
        serving.samples = [mapping(json.loads(line)) for line in lines if line.strip()]


def run_load(ctx: Context, serving: Serving, samples_path: Path, stop: Path) -> None:
    port = str(serving.port)
    sampler_argv = [sys.executable, str(HERE / "client.py"), "sample", "--port", port]
    sampler_argv += ["--cpus", pinned(SAMPLER_CPU), "--out", str(samples_path)]
    sampler_argv += ["--stop", str(stop), "--max-seconds", "1800"]
    sampler_log = ctx.work / f"sampler-{ctx.token}-{port}.log"
    with sampler_log.open("wb") as log:
        sampler = subprocess.Popen(
            sampler_argv, stdout=subprocess.DEVNULL, stderr=log, env=child_env()
        )
    try:
        time.sleep(1.0)
        argv = [sys.executable, str(HERE / "client.py"), "load", "--port", port]
        argv += ["--cpus", pinned(LOAD_CPU), "--ks", ",".join(str(k) for k in serving.ks)]
        argv += ["--rounds", str(ctx.options.http_rounds), "--gap", "1.0"]
        text = child(ctx, argv, 3600)
        prefix = "WINDOW "
        found = [line[len(prefix) :] for line in text.splitlines() if line.startswith(prefix)]
        serving.windows = [mapping(json.loads(line)) for line in found]
        time.sleep(0.5)
    finally:
        stop.touch()
        sampler.wait(timeout=120)


def overlapping(
    samples: list[dict[str, object]], start: float, end: float, path: str
) -> list[float]:
    """보낸 때부터 받은 때까지가 창과 겹친 표본의 걸린 시간."""
    found: list[float] = []
    for sample in samples:
        sent, latency = num(sample["sent"]), num(sample["latency"])
        if sample["path"] == path and sent <= end and sent + latency >= start:
            found.append(latency)
    return found


def inside(samples: list[dict[str, object]], start: float, end: float, path: str) -> list[float]:
    """보낸 때와 받은 때가 모두 구간 안인 표본의 걸린 시간."""
    found: list[float] = []
    for sample in samples:
        sent, latency = num(sample["sent"]), num(sample["latency"])
        if sample["path"] == path and sent >= start and sent + latency <= end:
            found.append(latency)
    return found


def item_http(ctx: Context) -> None:
    servings: list[Serving] = []
    port = 18100
    counts = ctx.options.server_cpus if LINUX else [0]
    for count_index, count in enumerate(counts):
        for mode, limit, ks in http_configs():
            port += 1
            serving = Serving(port=port, count=count, mode=mode, limit=limit, ks=ks)
            with_timing = count_index == 0 and mode == "thread" and limit == 0
            serve_once(ctx, serving, with_timing=with_timing)
            judge_serving(ctx, serving)
            servings.append(serving)
    ctx.results["http"] = serving_records(ctx, servings)


def item_http_pool(ctx: Context) -> None:
    """전용 스레드 넷 서버(`--mode pool`)와 같은 실행의 견줌인 `thread` 한도 4 서버. CPU 4 개."""
    servings: list[Serving] = []
    port = 18200
    count = HTTP_POOL_CPUS if LINUX else 0
    for mode, limit in (("pool", POOL), ("thread", 4)):
        port += 1
        serving = Serving(port=port, count=count, mode=mode, limit=limit, ks=KS)
        serve_once(ctx, serving, with_timing=False)
        judge_serving(ctx, serving)
        servings.append(serving)
    ctx.results["http_pool"] = serving_records(ctx, servings)


def serving_records(ctx: Context, servings: list[Serving]) -> list[dict[str, object]]:
    return [
        {
            "port": s.port,
            "count": s.count,
            "mode": s.mode,
            "limit": s.limit,
            "ready": s.ready,
            "windows": s.windows,
            "timing": s.timing,
            "samples_file": f"samples-{ctx.token}-{s.port}.jsonl",
        }
        for s in servings
    ]


def judge_serving(ctx: Context, serving: Serving) -> None:
    head = f"http cpu{serving.count} {serving.mode} 한도={serving.limit or '기본'}"
    if serving.ready is None:
        ctx.judge(f"{head} 서버", lambda: (False, "서버가 뜨지 않았다", ""))
        return
    print(f"{head} 서버: {json.dumps(serving.ready)}", flush=True)
    by_k: dict[int, list[dict[str, object]]] = {}
    for window in serving.windows:
        by_k.setdefault(int(num(window["k"])), []).append(window)
    for k in serving.ks:
        found = by_k.get(k, [])
        for index in range(ctx.options.http_rounds):
            label = f"{head} K={k} #{index + 1}"
            if index >= len(found):
                ctx.judge(label, lambda: (False, "창이 없다", ""))
                continue
            window = found[index]
            ctx.judge(label, lambda window=window, k=k: window_verdict(serving, window, k))
    summarize_serving(serving, by_k)
    if serving.timing is not None:
        judge_http_timing(ctx, head, serving.timing)


def window_verdict(serving: Serving, window: dict[str, object], k: int) -> Verdict:
    stats = mapping(window["stats"])
    peak = int(num(stats["peak_inside"]))
    tokens = 1 if serving.mode == "direct" else int(num(stats["tokens"]))
    start, end = num(window["start"]), num(window["end"])
    health = overlapping(serving.samples, start, end, "/health")
    thread = overlapping(serving.samples, start, end, "/thread-health")
    ok = window["ok"] == k and 1 <= peak <= tokens and bool(health or thread)
    window["health_under"] = health
    window["thread_under"] = thread
    window["any_under"] = health + thread
    base_start = num(window["warm_end"]) + 0.2
    window["health_base"] = inside(serving.samples, base_start, start - 0.02, "/health")
    window["thread_base"] = inside(serving.samples, base_start, start - 0.02, "/thread-health")
    detail = (
        f"동시 {peak}(한도 {tokens}), 성공 {window['ok']}/{k}, "
        f"겹친 표본 /health {len(health)}·/thread-health {len(thread)}"
    )
    if serving.mode == "pool":
        dedicated = stats.get("dedicated") is True
        threads = int(num(stats["hash_threads"]))
        ok = ok and dedicated and threads <= tokens
        detail += f", 견줌 스레드 {threads}, 전용 스레드에서만 {dedicated}"
    return ok, "창 섰다" if ok else "표지 없음", detail


def pooled(windows: list[dict[str, object]], name: str) -> list[float]:
    found: list[float] = []
    for window in windows:
        found.extend(floats(window.get(name, [])))
    return found


def peak_of(window: dict[str, object]) -> float:
    return num(mapping(window["stats"])["peak"])


def inside_of(window: dict[str, object]) -> float:
    return num(mapping(window["stats"])["peak_inside"])


def summarize_serving(serving: Serving, by_k: dict[int, list[dict[str, object]]]) -> None:
    print(
        "  K | 동시(최소~최대) | 로그인 ms 중앙 / 최대 | /health 바탕 중앙 / 최대"
        " | /health 부하 중앙 / 90분위 / 최대 | /thread-health 바탕 중앙 / 최대"
        " | /thread-health 부하 중앙 / 90분위 / 최대 | 두 경로 합친 부하 최대 | 서버 최고 상주 MiB"
        " | 서버가 뜬 뒤 견줌을 맡은 스레드 가짓수",
        flush=True,
    )
    for k in serving.ks:
        windows = by_k.get(k, [])
        logins = pooled(windows, "latencies")
        if not logins:
            print(f"  {k} | 창이 없다", flush=True)
            continue
        overlap = [inside_of(w) for w in windows]
        both = pooled(windows, "any_under")
        print(
            f"  {k} | {min(overlap):.0f}~{max(overlap):.0f} | "
            f"{ms(statistics.median(logins))} / {ms(max(logins))} | "
            f"{fmt(pooled(windows, 'health_base'))} | {fmt3(pooled(windows, 'health_under'))} | "
            f"{fmt(pooled(windows, 'thread_base'))} | {fmt3(pooled(windows, 'thread_under'))} | "
            f"{ms(max(both)) if both else '-'} | {mib(max(peak_of(w) for w in windows))} | "
            f"{max(num(mapping(w['stats'])['hash_threads']) for w in windows):.0f}",
            flush=True,
        )


def fmt(values: list[float]) -> str:
    if not values:
        return "-"
    return f"{ms(statistics.median(values))} / {ms(max(values))}"


def fmt3(values: list[float]) -> str:
    if not values:
        return "-"
    return f"{ms(statistics.median(values))} / {ms(quantile(values, 0.9))} / {ms(max(values))}"


def judge_http_timing(ctx: Context, head: str, data: dict[str, object]) -> None:
    raw = mapping(data["samples"])
    series = {name: Series(rows(values), 1) for name, values in raw.items()}
    expected = mapping(data["expected"])
    outcomes = {name: num(expected[name]) == len(series[name].entries) for name in series}
    for arm, values in series.items():
        stats = summary(values.values())
        print(
            f"  HTTP {arm}: 중앙 {ms(stats['median'])} ms, 10~90 분위 {ms(stats['p10'])}~"
            f"{ms(stats['p90'])}, 최대 {ms(stats['max'])}, n={stats['n']}, 기대대로 "
            f"{outcomes[arm]}",
            flush=True,
        )
    gate_p, _ = paired_compare(series["unknown"], series[HTTP_GATE], seed=1, unit="ms")
    power = gate_p < ALPHA and outcomes[HTTP_GATE]
    pairs = [
        ("unknown", HTTP_GATE),
        ("unknown", "plus1ms_control"),
        ("correct", "skip_control"),
        ("correct", "wrong"),
        ("correct", "unknown"),
        ("wrong", "unknown"),
    ]
    for index, (left, right) in enumerate(pairs, start=2):
        p, detail = paired_compare(series[left], series[right], seed=index, unit="ms")
        both = outcomes[left] and outcomes[right]
        ok = both if "control" in right else both and power
        if not ok:
            detail += f" (결과 기대대로 {both}, {HTTP_GATE} 대조 섰나 {power})"
        ctx.judge(
            f"{head} HTTP 시간 {left} 대 {right}",
            lambda ok=ok, p=p, detail=detail: (ok, separated(p), detail),
        )


# ---------------------------------------------------------------- 실행


def here(options: argparse.Namespace) -> int:
    work = Path(options.work)
    work.mkdir(parents=True, exist_ok=True)
    token = options.token or secrets.token_hex(3)
    rounds = Rounds()
    with (work / f"children-{token}.log").open("a", encoding="utf-8") as log:
        ctx = Context(rounds=rounds, work=work, token=token, log=log, options=options)
        ctx.results["facts"] = facts()
        print(f"실행 토큰 {token}, 환경 {json.dumps(ctx.results['facts'])}", flush=True)
        items = options.items.split(",")
        steps: dict[str, Callable[[Context], None]] = {
            "unicode": item_unicode,
            "timing": item_timing,
            "alloc": item_alloc,
            "burst": item_burst,
            "http": item_http,
            "alloc_arena": item_alloc_arena,
            "burst_pool": item_burst_pool,
            "http_pool": item_http_pool,
        }
        for name, step in steps.items():
            if name in items:
                started = time.monotonic()
                print(f"== {name} 시작 {time.strftime('%H:%M:%S')}", flush=True)
                try:
                    step(ctx)
                except Exception as error:  # 항목 하나의 실패가 다른 항목을 잃게 하지 않는다
                    rounds.record(f"{name} 항목", measured=False, result=f"예외: {error!r}")
                    print(f"== {name} 이 예외로 끝났다: {error!r}", flush=True)
                print(f"== {name} 끝 {time.monotonic() - started:.0f}초", flush=True)
        ctx.results["summary"] = rounds.summary()
        path = work / f"results-{token}.json"
        path.write_text(json.dumps(ctx.results, ensure_ascii=False), encoding="utf-8")
    print(rounds.summary(), flush=True)
    return rounds.exit_code()


def host_load() -> str:
    """호스트 CPU 부하(윈도만). 시간을 읽을 때의 사정을 적으려는 것이고 회차로 세지 않는다."""
    if sys.platform != "win32":
        return "(윈도가 아니라 재지 않았다)"
    command = "(Get-CimInstance Win32_Processor).LoadPercentage"
    try:
        done = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "(읽지 못했다)"
    return f"{done.stdout.strip()}%" if done.returncode == 0 else "(읽지 못했다)"


def cleanup(name: str) -> None:
    """이 실행이 만든 컨테이너만 지운다. 이름이 그 실행의 것과 같은 것이다."""
    listed = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"name={name}", "--format", "{{.Names}}"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    ).stdout.split()
    containers = [found for found in listed if found == name]
    if containers:
        subprocess.run(["docker", "rm", "-f", *containers], timeout=120, check=False)
    print(f"정리: 컨테이너 {len(containers)}", flush=True)


def passthrough(options: argparse.Namespace) -> list[str]:
    pairs = {
        "--items": options.items,
        "--server-cpus": ",".join(str(count) for count in options.server_cpus),
        "--burst-rounds": str(options.burst_rounds),
        "--late-rounds": str(options.late_rounds),
        "--http-rounds": str(options.http_rounds),
        "--timing-n": str(options.timing_n),
        "--timing-repeats": str(options.timing_repeats),
        "--http-timing-n": str(options.http_timing_n),
        "--alloc-pairs": str(options.alloc_pairs),
        "--alloc-n": str(options.alloc_n),
    }
    return [part for pair in pairs.items() for part in pair]


def in_docker(options: argparse.Namespace) -> int:
    token = secrets.token_hex(3)
    work = Path(options.work).resolve()
    work.mkdir(parents=True, exist_ok=True)
    name = f"{PREFIX}-{token}"
    command = ["docker", "run", "--rm", "--name", name, "--memory", CONTAINER_MEMORY]
    command += ["--memory-swap", CONTAINER_MEMORY, "--cpuset-cpus", CONTAINER_CPUS]
    command += ["-e", "PYTHONPATH=", "-e", "PYTHONUTF8=1", "-e", "PYTHONDONTWRITEBYTECODE=1"]
    command += ["-v", f"{ROOT}:/repo:ro", "-v", f"{work}:/work", IMAGE, PYTHON_IN_IMAGE]
    command += [f"{PROBE_IN_CONTAINER}/run.py", "here", "--work", "/work", "--token", token]
    command += passthrough(options)
    print(f"실행 토큰 {token}, 시작 {time.strftime('%H:%M:%S')}, 호스트 부하 {host_load()}")
    deadline = time.monotonic() + options.timeout
    with (work / f"raw-{token}.log").open("w", encoding="utf-8") as raw:
        raw.write(" ".join(command) + "\n")
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if process.stdout is None:
            raise RuntimeError("docker 의 출력을 받지 못했다")
        reader = LineReader(process.stdout)
        while time.monotonic() < deadline:
            line = reader.readline(5)
            if line is None:
                if reader.ended:
                    break
                continue
            raw.write(line)
            raw.flush()
            print(line, end="", flush=True)
        else:
            print(f"{options.timeout:.0f}초 안에 끝나지 않아 컨테이너를 지운다", flush=True)
            cleanup(name)
        code = process.wait(timeout=120)
    print(f"끝 {time.strftime('%H:%M:%S')}, 호스트 부하 {host_load()}, 컨테이너 종료 코드 {code}")
    cleanup(name)
    return code


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("place", choices=("docker", "here"))
    parser.add_argument("--work", required=True)
    parser.add_argument("--token", default="")
    parser.add_argument(
        "--items", default="unicode,timing,alloc,burst,http,alloc_arena,burst_pool,http_pool"
    )
    parser.add_argument(
        "--server-cpus",
        type=lambda text: [int(part) for part in text.split(",")],
        default=[2, 4],
    )
    parser.add_argument("--burst-rounds", type=int, default=5)
    parser.add_argument("--late-rounds", type=int, default=2)
    parser.add_argument("--http-rounds", type=int, default=3)
    parser.add_argument("--timing-n", type=int, default=400)
    parser.add_argument("--timing-repeats", type=int, default=2)
    parser.add_argument("--http-timing-n", type=int, default=200)
    parser.add_argument("--alloc-pairs", type=int, default=10)
    parser.add_argument("--alloc-n", type=int, default=60)
    parser.add_argument("--timeout", type=float, default=7200)
    options = parser.parse_args()
    if options.place == "docker":
        return in_docker(options)
    return here(options)


if __name__ == "__main__":
    raise SystemExit(main())
