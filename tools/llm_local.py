"""로컬 모델 시험의 모델 서버를 Runpod에 빌려 띄웠다 지운다(ADR 0058, 명세
`.scratch/local-model/spec.md` "모델 서버를 띄우는 명령", 티켓
`.scratch/local-model/issues/03-llm-local-command-rents-model-servers.md`).

이 저장소를 고치는 세션이 로컬 모델 시험을 돌려야 할 때(병합 전의 로컬 모델 시험을 만진 PR)
친다. 워크트리에서는 주 체크아웃의 `.env`가 계정 키를 프로세스 환경으로 넘기게 한다. 세션은 그
값을 읽지 않는다.

    uv run --env-file ../../../.env python tools/llm_local.py run               # 예상 비용만
    uv run --env-file ../../../.env python tools/llm_local.py run --yes         # 비용 확인 뒤
    uv run --env-file ../../../.env python tools/llm_local.py run --yes -- <명령>  # 시험 대신
    uv run --env-file ../../../.env python tools/llm_local.py sweep             # 남은 것 치우기

`run`은 `--yes` 없이 치면 예상 비용(GPU 후보마다 단가, 파드 수, 어림 30분과 타이머까지 간 최악
90분의 값)만 찍고 아무것도 띄우지 않은 채 끝난다. 세션은 그 출력을 사용자에게 보여 확인을 받은
뒤에만 `--yes`를 붙여 다시 친다. `--yes`가 붙으면 서버 키를 만들고,
Terraform(`tools/llm_local_server/`)으로 모델 서버 둘 (A.X 4.0 Light, gpt-oss-20b)을 90분 뒤
스스로 지워지게 걸린 채로 띄우고, 두 서버가 준비되기를 기다리고, `--` 뒤의 명령(기본 `uv run
pytest -m llm_local`)을 자식 프로세스로 돌리고, 시험이 어떻게 끝났든 (Ctrl-C로 끊겨도) 서버를
지운 뒤 기록 묶음을 찍는다.

걸음(명세의 번호): 1 환경(`RUNPOD_API_KEY` 이름, Terraform 1.6 이상, 분리 HEAD가 아닌 브랜치) 2
상태 폴더 3 잠금 4 남은 자원 지우기 5 예상 비용(`--yes` 없으면 여기서 끝) 6 서버 키 7
띄우기(재고가 없으면 다음 후보) 8 준비 기다리기(상한 `READY_LIMIT_SECONDS`) 9 시험 10 실패했으면
서버가 살아 있는지 확인 11 지우기 12 기록 묶음.

종료 코드. 0 시험 통과. 1 서버가 살아 있던 회차의 시험 실패. 2 무효 회차(시험이 실패했는데
서버가 답하지 않는다, 띄운 뒤 Ctrl-C로 끊겼다, 값이 예상보다 커서 지웠다, 준비 상한을 넘겼다,
GPU 후보를 모두 띄우지 못했다). 3 지우기 실패(상태 폴더의 경로를 크게 알린다. 타이머가 뒤를
받친다. apply가 시간 제한에 걸려 상태 파일에 자원이 없는 회차도 지울 방법이 없어 3이다).
4 아무것도 띄우지 않고 끝났다 (환경이 모자라다, 앞 세션이 쓰고 있다, `--yes`가 없다, 첫 `apply`
앞에서 끊겼다). 겹치면 3, 2, 1의 차례다. `sweep`은 0(지우지 못한 것이 없다. 산 잠금이나 표지
없는 폴더를 건드리지 않은 것은 지우지 못한 것이 아니다)과 3(지우지 못한 것이 있다)이다. 무효
회차는 실패로 세지 않고 다시 돌릴 수 있고, 다시 띄울 때도 비용 확인을 받는다. 무효 회차로
끝나면 연달은 무효 회차의 수를 찍고(`consecutive_invalid_rounds`가 상태 폴더의 회차 파일로 센다)
둘 이상이면 세션이 멈춰 보고한다고 알린다.

상태 폴더는 `~/.agent-os/llm-local/<브랜치 이름>/`이다(`folder_name`이 브랜치 이름을 폴더에 쓸
수 있는 글자로 바꾼다). Terraform의 상태 파일, 작업 폴더(`TF_DATA_DIR`), 회차마다 파일 하나인
기록(`records/`)이 거기 선다. 저장소와 워크트리 밖이라 워크트리가 지워져도 남고, 브랜치마다
따로라 나란히 도는 세션이 서로의 서버를 지우지 않는다. 서버 키는 파드의 시작 명령에 실려 상태
파일에 평문으로 남으므로, 지우기가 성공한 회차는 상태와 백업과 키가 든 파일을
지운다(`scrub_state`). 지우기가 실패한 회차의 상태는 `sweep`이 지울 때까지 그대로 둔다. 세션은
그 폴더 안의 상태 파일을 읽지 않는다.

잠금은 상태 폴더 밖의 `<폴더 이름>.lock`(그 폴더를 쓰는 `run`이나 `sweep`의 프로세스 번호와
시각)이다. 번호의 프로세스가 살아 있고 그 명령 줄이 이 스크립트의 `run`이나 `sweep`일 때만 산
잠금이다(번호만 보지 않는다. 번호는 다시 쓰인다). 잠금은 배타적 생성(`O_CREAT | O_EXCL`)으로
얻고, 죽은 잠금의 판정과 제거와 새로 얻기는 `<폴더 이름>.guard`에 건 OS의 배타적 파일 잠금
안에서 하며(윈도 `msvcrt.locking`, 리눅스 `fcntl.flock`) 이미 잡혀 있으면 기다리지 않고 산
잠금을 만난 것으로 끝난다.

`sweep`은 `~/.agent-os/llm-local/` 바로 아래를 훑어 죽은 잠금의 폴더마다 남은 자원을 `terraform
destroy`로 지우고, 자원이 없음을 확인한 폴더를 지운다. 이 스크립트가 심은 표지 파일(`MARKER`)이
있는 폴더만 지우고 링크는 따라가지 않는다. 치는 때는 병합 절차가 로컬 모델 시험을 돌린 PR을
병합한 뒤와, 남은 서버가 걱정될 때다.

비밀. 서버 키는 화면, 로그, 기록 묶음, 파일 어디에도 찍지 않는다. Terraform과 자식 프로세스의
출력은 받아 두었다가 `Reporter`가 서버 키를 글자 그대로 찾아 `***`로 바꾼 뒤에만 보이고, 받은
그대로를 파일에 쓰지 않는다. 자식 프로세스의 환경에서는 `RUNPOD_API_KEY`를 뺀다. 기록 묶음에는
서버 키와 주소를 넣지 않는다.

못 보는 것. 2026-11-14에 이 스크립트로 `pods` 구성(RTX 3090 두 장)이 서고 두 모델이 `tool_calls`로
답하는 것과, `shared` 구성의 서버 둘이 서서 준비 확인을 통과하는 것은 봤다(티켓 03의 "띄워 확인하는
것"). 타이머는 첫 판이 파드 이미지의 `runpodctl`에 없는 하위 명령을 써서 파드를 지우지 못했고, 고친
판이 5분 값(`TIMER_MINUTES`를 임시로 바꿔 띄웠다)으로 파드를 지우는 것은 봤다. 90분 값은 띄워 보지
않았다. 단가 표는 Runpod 가격 페이지(Secure Cloud)를
`PRICE_TABLE_DATE`에 WebFetch로 받아 그 웹 요약에서 읽은 값이다. 원문과 대조하지 않았다. 띄워 본
Terraform `cost`는 A40(0.59)과 RTX 3090 두 장(1.0)만 표와 같았다.
프로세스의 명령 줄을 읽지 못하는 프로세스(다른 사용자의 것)는 죽은 것으로 읽어 그 잠금을 치운다.
위 `sweep`과 `run`은 같은 사용자의 프로세스만 본다. 모델 목록을 읽는 요청은 시스템의 프록시
설정을 따른다.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import secrets
import shlex
import signal
import stat
import subprocess
import sys
import tempfile
import time
import urllib.request
import xml.etree.ElementTree as ElementTree
from collections.abc import Generator, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote

if __package__ in (None, ""):  # 스크립트로 부르면 저장소 루트가 import 경로에 없다
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.proc_command_line import command_line  # noqa: E402

from tools import llm_tokens  # noqa: E402

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = Path(__file__).resolve().parent / "llm_local_server"
SCRIPT_NAME = "llm_local.py"

VLLM_VERSION = "0.33.0"
IMAGE = f"vllm/vllm-openai:v{VLLM_VERSION}"
MARKER = ".agent-os-llm-local"
PRICE_TABLE_DATE = "2026-11-13"
ESTIMATE_MINUTES = 30
TIMER_MINUTES = 90
READY_LIMIT_SECONDS = 30 * 60
READY_POLL_SECONDS = 15.0
# 타이머 90분 = 준비 상한 30분 + 시험 50분 + 여유. 시험이 이 시간을 넘으면 실패한 시험으로 본다.
CHILD_TIMEOUT_SECONDS = 50 * 60
SHORT_TIMEOUT = 120.0
INIT_TIMEOUT = 600.0
APPLY_TIMEOUT = 15 * 60.0
DESTROY_TIMEOUT = 15 * 60.0
OUTPUT_TAIL_LINES = 40
SHARED_UTILIZATION = 0.45
# shared 배치에서 서버마다 고정하는 KV 캐시 크기(바이트). 비율(`--gpu-memory-utilization`)만으로는
# 한 GPU에 서버 둘이 서지 않았다. 근거는 2026-11-14에 파드 로그를 손으로 본 것이고, 시험
# `tests/tools/test_llm_local_state.py`의 주석에 적었다.
SHARED_KV_CACHE_BYTES = 4 * 1024**3
DEFAULT_TEST_COMMAND = ("uv", "run", "pytest", "-m", "llm_local")
MASK = "***"
USER_AGENT = "agent-os-llm-local"

# 종료 코드
PASSED, TEST_FAILED, INVALID, DESTROY_FAILED, NOT_LAUNCHED = 0, 1, 2, 3, 4


@dataclass(frozen=True)
class Model:
    number: int
    model_id: str
    parser: str


MODELS = (
    Model(1, "skt/A.X-4.0-Light", "hermes"),
    Model(2, "openai/gpt-oss-20b", "openai"),
)


def env_names(number: int) -> tuple[str, str, str]:
    """로컬 모델 시험이 모델 `number`(1이나 2)에 받는 환경 변수 셋의 이름. 원천은 여기다."""
    prefix = f"AGENT_OS_LLM_LOCAL_{number}"
    return f"{prefix}_BASE_URL", f"{prefix}_MODEL_ID", f"{prefix}_API_KEY"


ENV_NAMES = tuple(name for model in MODELS for name in env_names(model.number))


@dataclass(frozen=True)
class Gpu:
    label: str
    type_id: str
    hourly: float  # 파드 하나의 시간당 값(달러, Secure Cloud)


GPUS = (
    Gpu("RTX A5000", "NVIDIA RTX A5000", 0.27),
    Gpu("RTX 3090", "NVIDIA GeForce RTX 3090", 0.50),
    Gpu("A40", "NVIDIA A40", 0.59),
)


@dataclass(frozen=True)
class Candidate:
    layout: str  # pods: 모델마다 파드 하나. shared: 파드 하나에 서버 둘
    gpu: Gpu
    pods: int


def candidates() -> tuple[Candidate, ...]:
    """띄워 볼 차례. 첫째 구성의 GPU 셋, 그다음 둘째 구성(A40 한 장에 서버 둘)이다. 셋째 구성(파드
    하나에 모델을 차례로)은 두 모델을 한 자식 프로세스에 함께 넘기는 모양과 맞지 않아 짓지
    않는다."""
    first = tuple(Candidate("pods", gpu, len(MODELS)) for gpu in GPUS)
    return (*first, Candidate("shared", GPUS[-1], 1))


def expected_cost(candidate: Candidate, minutes: float) -> float:
    return candidate.gpu.hourly * candidate.pods * minutes / 60


def cost_table() -> str:
    lines = [
        f"예상 비용(Runpod 가격 페이지의 Secure Cloud 단가를 {PRICE_TABLE_DATE}에 웹 요약에서 "
        "읽은 값. 원문과 대조하지 않았다):",
    ]
    for c in candidates():
        hourly = c.gpu.hourly * c.pods
        lines.append(
            f"  {c.layout} | {c.gpu.label} | 파드 {c.pods} | 시간당 ${hourly:.2f}"
            f" | 어림 {ESTIMATE_MINUTES}분 ${expected_cost(c, ESTIMATE_MINUTES):.2f}"
            f" | 최악 {TIMER_MINUTES}분 ${expected_cost(c, TIMER_MINUTES):.2f}"
        )
    lines.append(
        "  띄우지 못하면(재고 없음 등) 위 차례로 다음 후보를 시도한다. "
        "타이머가 90분 뒤 파드를 지운다."
    )
    return "\n".join(lines)


# --- 외부 세계: 시험이 가짜로 바꿔 끼우는 자리 ---


@dataclass(frozen=True)
class Outcome:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


def _kill_tree(child: subprocess.Popen[bytes]) -> None:
    """`child`와 그 아래 프로세스를 모두 끊고 거둔다. 윈도는 `taskkill /T`, 리눅스는 `execute`가 새
    세션으로 띄운 프로세스 그룹 전체에 보낸다."""
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(child.pid)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=SHORT_TIMEOUT,
            check=False,
        )
    else:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(child.pid, signal.SIGKILL)
    child.kill()
    child.wait(timeout=SHORT_TIMEOUT)


def execute(
    argv: Sequence[str], *, env: Mapping[str, str], cwd: Path, timeout: float | None
) -> Outcome:
    """외부 명령(terraform, git, 시험 자식)은 모두 이 함수를 지난다. 출력은 파이프가 아니라 임시
    파일로 받는다. 명령이 띄운 손자(Terraform의 프로바이더)가 파이프를 쥐면 시간 제한으로 죽인
    뒤에도 호출이 돌아오지 않는다(`.claude/rules/tools.md`). 시간 제한이나 Ctrl-C로 끊을 때는
    직계 자식만이 아니라 그 아래 프로세스 트리를 끊는다(`uv run pytest`는 pytest를 손자로
    띄운다)."""
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        try:
            child = subprocess.Popen(
                list(argv),
                env=dict(env),
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                stdout=out,
                stderr=err,
                start_new_session=sys.platform != "win32",
            )
        except OSError as problem:
            return Outcome(127, "", f"{argv[0]}을(를) 실행하지 못했다: {problem}")
        try:
            code, timed_out = child.wait(timeout=timeout), False
        except subprocess.TimeoutExpired:
            _kill_tree(child)
            code, timed_out = -1, True
        except BaseException:
            _kill_tree(child)
            raise
        out.seek(0)
        err.seek(0)
        return Outcome(
            code,
            out.read().decode("utf-8", errors="replace"),
            err.read().decode("utf-8", errors="replace"),
            timed_out,
        )


def fetch_models(base_url: str, key: str) -> list[str] | None:
    """`GET <주소>/models`가 200으로 낸 모델 이름들. 답하지 않거나 200이 아니면 None."""
    # Runpod 프록시는 urllib의 기본 User-Agent(`Python-urllib/…`)를 403(`error code: 1010`)으로
    # 거절한다.
    request = urllib.request.Request(  # noqa: S310 - 주소는 Terraform 출력의 https 주소다
        base_url.rstrip("/") + "/models",
        headers={"Authorization": f"Bearer {key}", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:  # noqa: S310
            if response.status != 200:
                return None
            body: Json = json.load(response)
    except (OSError, ValueError):
        return None
    data = _members(body, "data")
    ids: list[str] = []
    for item in data if isinstance(data, list) else []:
        name = _members(item, "id")
        if isinstance(name, str):
            ids.append(name)
    return ids


def state_root() -> Path:
    return Path.home() / ".agent-os" / "llm-local"


def cmdline_of(pid: int) -> tuple[str, ...] | None:
    return command_line(pid)


def pause(seconds: float) -> None:
    time.sleep(seconds)


def clock() -> float:
    return time.monotonic()


def _members(value: Json, key: str) -> Json:
    return value.get(key) if isinstance(value, dict) else None


# --- 비밀을 가리는 출력 ---


@dataclass
class Reporter:
    """사람(세션)에게 보이는 모든 글은 여기를 지난다. 서버 키를 글자 그대로 찾아 가린다."""

    secrets: list[str] = field(default_factory=list[str])
    masked: bool = False  # 어느 글에서든 가렸다
    terraform_masked: bool = False  # Terraform의 출력에서 가렸다(성공한 단계의 출력도 센다)

    def reset(self) -> None:
        self.secrets.clear()
        self.masked = False
        self.terraform_masked = False

    def watch_terraform(self, outcome: Outcome) -> None:
        """Terraform 명령의 출력에 서버 키가 되울렸는지만 센다. 보이지는 않는다."""
        if any(s in text for s in self.secrets for text in (outcome.stdout, outcome.stderr)):
            self.terraform_masked = True

    def add_secret(self, value: str) -> None:
        if value:
            self.secrets.append(value)

    def clean(self, text: str) -> str:
        for secret in self.secrets:
            if secret in text:
                self.masked = True
                text = text.replace(secret, MASK)
        return text

    def say(self, text: str) -> None:
        print(self.clean(text), flush=True)

    def tail(self, title: str, outcome: Outcome) -> None:
        text = "\n".join(part for part in (outcome.stdout.strip(), outcome.stderr.strip()) if part)
        lines = text.splitlines()[-OUTPUT_TAIL_LINES:]
        if lines:
            self.say(f"--- {title}(끝 {len(lines)}줄) ---\n" + "\n".join(lines))


OUT = Reporter()


# --- 상태 폴더와 잠금 ---


def folder_name(branch: str) -> str:
    """브랜치 이름을 폴더 이름으로. `/`와 `.`를 포함해 쓸 수 없는 글자는 `%XX`로 바꾸고 `%`도
    바꾸므로 다른 브랜치가 같은 폴더가 되지 않는다. `.`가 없으므로 `<이름>.lock`, `<이름>.guard`와
    겹치지 않는다."""
    return quote(branch, safe="").replace(".", "%2E")


def is_link(path: Path) -> bool:
    return path.is_symlink() or os.path.isjunction(path)


if sys.platform == "win32":
    import msvcrt

    def _try_lock(fd: int) -> bool:
        os.lseek(fd, 0, os.SEEK_SET)
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        except OSError:
            return False
        return True

    def _unlock(fd: int) -> None:
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)

else:
    import fcntl

    def _try_lock(fd: int) -> bool:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return False
        return True

    def _unlock(fd: int) -> None:
        fcntl.flock(fd, fcntl.LOCK_UN)


@contextlib.contextmanager
def file_guard(path: Path) -> Generator[bool]:
    """OS의 배타적 파일 잠금. 이미 잡혀 있으면 기다리지 않고 False를 준다. 프로세스가 끝나면 OS가
    풀므로 죽은 것인지 판정할 필요가 없다. 파일 자체는 지우지 않는다."""
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        held = _try_lock(fd)
        try:
            yield held
        finally:
            if held:
                _unlock(fd)
    finally:
        os.close(fd)


def lock_is_live(path: Path) -> bool:
    try:
        info: Json = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    pid = _members(info, "pid")
    if not isinstance(pid, int) or isinstance(pid, bool):
        return False
    words = cmdline_of(pid)
    if words is None:
        return False
    for index, word in enumerate(words):
        if Path(word).name == SCRIPT_NAME:
            return words[index + 1 : index + 2] in (("run",), ("sweep",))
    return False


@dataclass
class Lock:
    path: Path

    def release(self) -> None:
        self.path.unlink(missing_ok=True)


def acquire(root: Path, name: str) -> Lock | None:
    """폴더 `name`의 잠금을 얻는다. 산 잠금이거나 판정 구간의 파일 잠금이 잡혀 있으면 None."""
    root.mkdir(parents=True, exist_ok=True)
    with file_guard(root / f"{name}.guard") as held:
        if not held:
            return None
        return _take(root / f"{name}.lock")


def _take(path: Path) -> Lock | None:
    for _ in range(2):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            if lock_is_live(path):
                return None
            try:
                path.unlink(missing_ok=True)
            except OSError:
                return None
            continue
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump({"pid": os.getpid(), "started": time.time()}, handle)
        return Lock(path)
    return None


def state_has_resources(folder: Path) -> bool:
    """상태 파일에 자원이 남았는지. 읽지 못하면 있다고 본다(지우려 시도하는 쪽이 안전하다)."""
    state = folder / "terraform.tfstate"
    if not state.is_file():
        return False
    try:
        loaded: Json = json.loads(state.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return True
    resources = _members(loaded, "resources")
    return not isinstance(resources, list) or bool(resources)


def long_path(path: Path) -> Path:
    """윈도에서 260자를 넘는 경로를 다루도록 `\\\\?\\` 접두를 붙인다. 시험 자식(pytest)의 임시
    폴더가 깊어져 일반 경로로는 지우지 못했다. 경로를 정규화하지 않는다(`abspath`는 끝의 `.`를
    지운다). 윈도가 아니거나 절대 경로가 아니거나 이미 `\\\\`로 시작하면 그대로 둔다."""
    text = str(path)
    if sys.platform != "win32" or not path.is_absolute() or text.startswith("\\\\"):
        return path
    return Path("\\\\?\\" + text)


def _files_under(folder: Path) -> Iterator[Path]:
    """링크를 따라가지 않고 폴더 아래 파일을 낸다."""
    with os.scandir(folder) as entries:
        children = [Path(entry.path) for entry in entries]
    for child in children:
        if is_link(child):
            continue
        if child.is_dir():
            yield from _files_under(child)
        elif child.is_file():
            yield child


def _unlink(path: Path) -> None:
    try:
        path.unlink()
    except PermissionError:
        path.chmod(stat.S_IWRITE)
        path.unlink()


def delete_tree(folder: Path) -> None:
    """폴더를 지운다. 링크(symlink, junction)는 따라가지 않고 링크만 끊는다."""
    _delete_tree(long_path(folder))


def _delete_tree(folder: Path) -> None:
    with os.scandir(folder) as entries:
        children = [Path(entry.path) for entry in entries]
    for child in children:
        if is_link(child):
            try:
                os.unlink(child)
            except OSError:
                os.rmdir(child)
        elif child.is_dir():
            _delete_tree(child)
        else:
            _unlink(child)
    folder.rmdir()


def scrub_state(folder: Path, key: str | None) -> None:
    """지우기가 성공한 뒤 상태 폴더에서 서버 키가 든 파일을 없앤다. 상태 파일과 그 백업은 키를 알든
    모르든 지운다(백업은 지우기 전의 상태를 담는다). 키를 알면 다른 파일도 훑어 그 값이 든 것을
    지운다."""
    for path in folder.glob("terraform.tfstate*"):
        if path.is_file() and not is_link(path):
            _unlink(path)
    if not key:
        return
    needle = key.encode()
    try:
        files = list(_files_under(long_path(folder)))
    except OSError as problem:
        OUT.say(f"상태 폴더를 끝까지 훑지 못했다. 서버 키가 든 파일이 남았을 수 있다: {problem}")
        return
    for path in files:
        try:
            if needle in path.read_bytes():
                _unlink(path)
        except OSError:
            continue


# --- Terraform ---


def terraform_env(
    folder: Path, key: str, *, layout: str = "pods", gpu_type_id: str = GPUS[0].type_id
) -> dict[str, str]:
    env = dict(os.environ)
    env["TF_DATA_DIR"] = str(folder / ".tfdata")
    env["TF_IN_AUTOMATION"] = "1"
    env["TF_INPUT"] = "0"
    env["TF_VAR_server_key"] = key
    env["TF_VAR_layout"] = layout
    env["TF_VAR_gpu_type_id"] = gpu_type_id
    env["TF_VAR_timer_minutes"] = str(TIMER_MINUTES)
    env["TF_VAR_models"] = json.dumps(
        {str(m.number): {"model_id": m.model_id, "parser": m.parser} for m in MODELS}
    )
    return env


def terraform_argv(*args: str) -> tuple[str, ...]:
    return ("terraform", f"-chdir={CONFIG_DIR}", *args)


def _state_arg(folder: Path) -> str:
    return f"-state={folder / 'terraform.tfstate'}"


def terraform_step(
    env: Mapping[str, str], title: str, args: Sequence[str], timeout: float
) -> Outcome:
    outcome = execute(terraform_argv(*args), env=env, cwd=REPO_ROOT, timeout=timeout)
    OUT.watch_terraform(outcome)
    if outcome.returncode != 0:
        OUT.say(
            f"terraform {title} 실패(종료 코드 {outcome.returncode}, 시간 제한 {outcome.timed_out})"
        )
        OUT.tail(f"terraform {title}", outcome)
    return outcome


def terraform_init(env: Mapping[str, str]) -> bool:
    outcome = terraform_step(env, "init", ("init", "-input=false", "-no-color"), INIT_TIMEOUT)
    return outcome.returncode == 0


@contextlib.contextmanager
def interrupts_ignored() -> Generator[None]:
    """지우는 동안의 Ctrl-C는 무시한다. 끊긴 destroy는 서버를 남긴다. 메인 스레드가 아니면 그대로
    둔다."""
    try:
        previous = signal.signal(signal.SIGINT, signal.SIG_IGN)
    except ValueError:
        yield
        return
    try:
        yield
    finally:
        signal.signal(signal.SIGINT, previous)


def destroy_folder(folder: Path, key: str | None) -> bool:
    """폴더의 자원을 `terraform destroy`로 지운다. 타이머가 이미 지운 파드로 실패하면
    `apply -refresh-only`로 상태를 실제와 맞춘 뒤 다시 지운다. 성공하면 비밀을 치운다."""
    if not os.environ.get("RUNPOD_API_KEY"):
        OUT.say("RUNPOD_API_KEY가 환경에 없어 자원을 지우지 못한다.")
        return False
    env = terraform_env(folder, key or "destroy-only")
    destroy = ("destroy", "-auto-approve", "-input=false", "-no-color", _state_arg(folder))
    refresh = (
        "apply",
        "-refresh-only",
        "-auto-approve",
        "-input=false",
        "-no-color",
        _state_arg(folder),
    )
    with interrupts_ignored():
        if not terraform_init(env):
            return False
        if terraform_step(env, "destroy", destroy, DESTROY_TIMEOUT).returncode != 0:
            if terraform_step(env, "apply -refresh-only", refresh, APPLY_TIMEOUT).returncode != 0:
                return False
            if terraform_step(env, "destroy(다시)", destroy, DESTROY_TIMEOUT).returncode != 0:
                return False
    scrub_state(folder, key)
    return True


# --- 시험 자식 ---


def child_env(
    base: Mapping[str, str], folder: Path, servers: Sequence[tuple[str, str, str]]
) -> dict[str, str]:
    """시험 자식의 환경. 환경 변수 여섯을 채우고 `RUNPOD_API_KEY`를 뺀다. `PYTEST_ADDOPTS`로 JUnit
    XML과 basetemp를 상태 폴더 안에 두게 한다(자식이 pytest가 아니면 그 변수는 쓰이지 않는다)."""
    env = {k: v for k, v in base.items() if k != "RUNPOD_API_KEY"}
    for model, (url, model_id, key) in zip(MODELS, servers, strict=True):
        url_name, id_name, key_name = env_names(model.number)
        env[url_name], env[id_name], env[key_name] = url, model_id, key
    # pytest는 PYTEST_ADDOPTS를 shlex로 나누므로 윈도 경로의 역슬래시가 사라지지 않게 `/`로 쓴다.
    ours = (
        f"--junitxml={shlex.quote((folder / 'junit.xml').as_posix())}"
        f" --basetemp={shlex.quote((folder / 'basetemp').as_posix())}"
    )
    env["PYTEST_ADDOPTS"] = f"{base.get('PYTEST_ADDOPTS', '')} {ours}".strip()
    return env


@dataclass(frozen=True)
class Results:
    passed: int | None
    tokens: llm_tokens.Tokens | None


def clear_results(folder: Path) -> None:
    """앞 회차가 상태 폴더에 남긴 JUnit XML과 basetemp를 지운다. 자식이 pytest가 아니면 이번
    회차에는 이 둘이 없어야 하고, 남아 있으면 앞 회차의 통과 수와 토큰 합계가 이번 기록에
    실린다."""
    (folder / "junit.xml").unlink(missing_ok=True)
    basetemp = folder / "basetemp"
    if basetemp.is_dir() and not is_link(basetemp):
        delete_tree(basetemp)


def read_results(folder: Path) -> Results:
    """자식이 pytest였으면 통과 수(JUnit XML)와 토큰 합계(basetemp의 트레이스). 아니면 둘 다
    없음."""
    junit = folder / "junit.xml"
    if not junit.is_file():
        return Results(None, None)
    passed: int | None
    try:
        body = junit.read_text(encoding="utf-8")
        if "<!DOCTYPE" in body or "<!ENTITY" in body:
            return Results(None, None)
        suites = list(ElementTree.fromstring(body).iter("testsuite"))
        passed = sum(
            int(s.get("tests", "0"))
            - int(s.get("failures", "0"))
            - int(s.get("errors", "0"))
            - int(s.get("skipped", "0"))
            for s in suites
        )
    except (ElementTree.ParseError, OSError, ValueError):
        passed = None
    basetemp = folder / "basetemp"
    tokens = llm_tokens.count(basetemp) if basetemp.is_dir() else llm_tokens.Tokens()
    return Results(passed, tokens)


# --- 모델 서버 ---


@dataclass(frozen=True)
class Server:
    model: Model
    base_url: str


def parse_outputs(text: str) -> tuple[list[Server], float] | None:
    """`terraform output -json`에서 모델마다의 주소와 파드 시간당 값의 합. 모양이 다르면 None."""
    try:
        outputs: Json = json.loads(text)
    except ValueError:
        return None
    listed = _members(_members(outputs, "servers"), "value")
    pods = _members(_members(outputs, "pods"), "value")
    if not isinstance(listed, list) or not isinstance(pods, list):
        return None
    servers: list[Server] = []
    for model in MODELS:
        url = next(
            (
                _members(item, "base_url")
                for item in listed
                if _members(item, "n") == str(model.number)
            ),
            None,
        )
        if not isinstance(url, str):
            return None
        servers.append(Server(model, url))
    total = 0.0
    for pod in pods:
        cost = _members(pod, "cost_per_hr")
        if isinstance(cost, bool) or not isinstance(cost, int | float):
            return None
        total += float(cost)
    return servers, total


def servers_ready(servers: Sequence[Server], key: str) -> bool:
    return all(
        server.model.model_id in (fetch_models(server.base_url, key) or []) for server in servers
    )


def wait_ready(servers: Sequence[Server], key: str) -> bool:
    start = clock()
    while True:
        if servers_ready(servers, key):
            return True
        if clock() - start >= READY_LIMIT_SECONDS:
            return False
        pause(READY_POLL_SECONDS)


def server_options(candidate: Candidate) -> list[str]:
    """서버에 준 옵션(서버 키를 뺀 글자 그대로). `tools/llm_local_server/main.tf`와 같아야 한다."""
    options: list[str] = []
    for model in MODELS:
        port = 8000 + model.number - 1 if candidate.layout == "shared" else 8000
        words = [
            f"vllm serve {model.model_id}",
            "--host 0.0.0.0",
            f"--port {port}",
            "--enable-auto-tool-choice",
            f"--tool-call-parser {model.parser}",
        ]
        if candidate.layout == "shared":
            words.append(f"--gpu-memory-utilization {SHARED_UTILIZATION}")
            words.append(f"--kv-cache-memory={SHARED_KV_CACHE_BYTES}")
        options.append(" ".join(words))
    return options


# --- 회차 기록 ---


def records_dir(folder: Path) -> Path:
    return folder / "records"


def write_record(folder: Path, record: Mapping[str, object]) -> Path:
    directory = records_dir(folder)
    directory.mkdir(parents=True, exist_ok=True)
    number = len(list(directory.glob("round-*.json"))) + 1
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    path = directory / f"round-{number:04d}-{stamp}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def consecutive_invalid_rounds(folder: Path) -> int:
    """가장 최근 회차부터 거슬러 무효 회차(종료 코드 2)가 몇 번 이어졌는지."""
    count = 0
    for path in sorted(records_dir(folder).glob("round-*.json"), reverse=True):
        try:
            record: Json = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            break
        if _members(record, "exit_code") != INVALID:
            break
        count += 1
    return count


# --- run ---


@dataclass
class Round:
    folder: Path
    key: str
    command: tuple[str, ...]
    commit: str
    started: float
    candidate: Candidate | None = None
    servers: list[Server] = field(default_factory=list[Server])
    hourly: float | None = None
    launched: bool = False
    invalid_reason: str | None = None
    interrupted: bool = False
    child: Outcome | None = None
    results: Results = field(default_factory=lambda: Results(None, None))
    destroy_failed: bool = False


def check_environment() -> tuple[list[str], str, str]:
    """없는 것의 이름들, 브랜치, 커밋."""
    problems: list[str] = []
    if not os.environ.get("RUNPOD_API_KEY"):
        problems.append("RUNPOD_API_KEY(환경 변수)가 없다")
    env = dict(os.environ)
    version = execute(("terraform", "-version"), env=env, cwd=REPO_ROOT, timeout=SHORT_TIMEOUT)
    match = None
    if version.returncode == 0:
        match = re.search(r"Terraform v(\d+)\.(\d+)", version.stdout)
    if version.returncode != 0:
        problems.append("terraform을 실행하지 못했다(설치와 PATH를 본다. 1.6 이상이 필요하다)")
    elif match is None or (int(match.group(1)), int(match.group(2))) < (1, 6):
        problems.append(f"terraform 1.6 이상이 필요하다(지금 {version.stdout.splitlines()[:1]})")
    branch = execute(
        ("git", "branch", "--show-current"), env=env, cwd=REPO_ROOT, timeout=SHORT_TIMEOUT
    ).stdout.strip()
    if not branch:
        problems.append("브랜치가 없다(분리 HEAD다. 브랜치를 따서 다시 친다)")
    commit = execute(
        ("git", "rev-parse", "HEAD"), env=env, cwd=REPO_ROOT, timeout=SHORT_TIMEOUT
    ).stdout.strip()
    return problems, branch, commit


def run(*, yes: bool, command: Sequence[str]) -> int:
    OUT.reset()
    try:
        return _run(yes=yes, command=tuple(command) or DEFAULT_TEST_COMMAND)
    except KeyboardInterrupt:
        OUT.say("띄우기 전에 끊겼다. 아무것도 띄우지 않았다.")
        return NOT_LAUNCHED


def _run(*, yes: bool, command: tuple[str, ...]) -> int:
    problems, branch, commit = check_environment()
    if problems:
        OUT.say("띄우지 않고 끝난다. 모자란 것:\n" + "\n".join(f"  - {p}" for p in problems))
        return NOT_LAUNCHED
    root = state_root()
    name = folder_name(branch)
    lock = acquire(root, name)
    if lock is None:
        OUT.say(
            f"앞 세션의 명령이 이 브랜치({branch})의 상태 폴더를 쓰고 있다. "
            "아무것도 건드리지 않는다."
        )
        return NOT_LAUNCHED
    try:
        folder = root / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / MARKER).write_text("agent-os llm_local\n", encoding="utf-8")
        if state_has_resources(folder):
            OUT.say("앞 세션이 남긴 자원을 먼저 지운다(비용 확인을 기다리지 않는다).")
            if not destroy_folder(folder, None):
                OUT.say(f"지우지 못했다. 새로 띄우지 않는다. 상태 폴더: {folder}")
                return DESTROY_FAILED
            OUT.say("남은 자원을 지웠다.")
        OUT.say(cost_table())
        if not yes:
            OUT.say(
                "아무것도 띄우지 않았다. 사용자에게 이 비용을 보여 확인을 받은 뒤 "
                "--yes를 붙여 다시 친다."
            )
            return NOT_LAUNCHED
        key = "sk-local-" + secrets.token_urlsafe(24)
        OUT.add_secret(key)
        state = Round(folder, key, command, commit, clock())
        return _launch_and_test(state)
    finally:
        lock.release()


def _launch_and_test(state: Round) -> int:
    try:
        _bring_up(state)
        if state.invalid_reason is None:
            _test(state)
    except KeyboardInterrupt:
        state.interrupted = True
        if state.launched:
            state.invalid_reason = "무효 회차: 띄운 뒤 시험이 판정을 내기 전에 Ctrl-C로 끊겼다"
        else:
            OUT.say("띄우기 전에 끊겼다. 아무것도 띄우지 않았다.")
    if state_has_resources(state.folder):
        state.destroy_failed = not destroy_folder(state.folder, state.key) or state.destroy_failed
    if state.interrupted and not state.launched and not state.destroy_failed:
        return NOT_LAUNCHED
    if state.invalid_reason is not None and state.interrupted:
        OUT.say(state.invalid_reason)
    return _finish(state)


def _bring_up(state: Round) -> None:
    for candidate in candidates():
        env = terraform_env(
            state.folder, state.key, layout=candidate.layout, gpu_type_id=candidate.gpu.type_id
        )
        OUT.say(f"띄운다: {candidate.layout} / {candidate.gpu.label} x {candidate.pods}")
        apply = ("apply", "-auto-approve", "-input=false", "-no-color", _state_arg(state.folder))
        applied: Outcome | None = None
        if terraform_init(env):
            # 이 apply부터가 띄우기다. 이 앞에서 끊기면 아무것도 띄우지 않았다(종료 코드 4).
            state.launched = True
            applied = terraform_step(env, "apply", apply, APPLY_TIMEOUT)
        if applied is not None and applied.returncode == 0:
            outcome = execute(
                terraform_argv("output", "-json", _state_arg(state.folder)),
                env=env,
                cwd=REPO_ROOT,
                timeout=SHORT_TIMEOUT,
            )
            OUT.watch_terraform(outcome)
            parsed = parse_outputs(outcome.stdout) if outcome.returncode == 0 else None
            state.candidate = candidate
            if parsed is None:
                state.invalid_reason = (
                    "무효 회차: terraform 출력의 모양이 달라 서버 주소를 읽지 못했다"
                )
                return
            state.servers, state.hourly = parsed
            expected = candidate.gpu.hourly * candidate.pods
            if state.hourly > expected + 1e-9:
                state.invalid_reason = (
                    f"무효 회차: Terraform이 돌려준 시간당 값 ${state.hourly:.2f}가 "
                    f"예상 ${expected:.2f}보다 커서 지웠다"
                )
                OUT.say(state.invalid_reason)
                return
            OUT.say("서버 준비를 기다린다.")
            if not wait_ready(state.servers, state.key):
                state.invalid_reason = "무효 회차: 준비 상한을 넘겨 지웠다"
                OUT.say(state.invalid_reason)
            return
        if applied is not None and applied.timed_out and not state_has_resources(state.folder):
            # 죽은 apply는 상태 파일을 쓰지 못했을 수 있다. 파드가 떴어도 지울 방법이 없고
            # 다음 후보를 띄우면 파드가 더 는다. 여기서 멈춘다. 타이머가 90분 뒤 지운다.
            state.destroy_failed = True
            state.invalid_reason = (
                "무효 회차: apply가 시간 제한에 걸렸고 상태 파일에 자원이 없다. 파드가 떠 있을 수 "
                "있다. Runpod 콘솔에서 이 계정의 파드를 확인한다(타이머가 90분 뒤 지운다)"
            )
            OUT.say(state.invalid_reason)
            return
        if state_has_resources(state.folder) and not destroy_folder(state.folder, state.key):
            state.destroy_failed = True
            state.invalid_reason = "무효 회차: 실패한 apply 뒤 남은 자원을 지우지 못했다"
            OUT.say(state.invalid_reason)
            return
    state.invalid_reason = (
        "무효 회차: GPU 후보를 모두 띄우지 못했다"
        "(재고 없음이나 다른 실패. 위 terraform 출력을 본다). "
        "셋째 구성(파드 하나에 모델을 차례로)은 "
        "띄우지 않았다. 시험을 어떻게 나눌지 사용자에게 묻는다"
    )
    OUT.say(state.invalid_reason)


def _test(state: Round) -> None:
    triples = [(s.base_url, s.model.model_id, state.key) for s in state.servers]
    clear_results(state.folder)  # 앞 회차의 XML과 basetemp가 이번 기록에 실리지 않게 한다
    env = child_env(dict(os.environ), state.folder, triples)
    OUT.say("시험을 돌린다: " + " ".join(state.command))
    state.child = execute(state.command, env=env, cwd=REPO_ROOT, timeout=CHILD_TIMEOUT_SECONDS)
    OUT.tail("시험 출력", state.child)
    state.results = read_results(state.folder)
    if _test_ok(state):
        return
    if not servers_ready(state.servers, state.key):
        state.invalid_reason = "무효 회차: 시험이 실패했고 그 직후 서버가 모델 목록에 답하지 않는다"
        OUT.say(state.invalid_reason)


def _test_ok(state: Round) -> bool:
    return state.child is not None and state.child.returncode == 0 and not state.child.timed_out


def _finish(state: Round) -> int:
    if state.destroy_failed:
        code = DESTROY_FAILED
        OUT.say(f"지우기에 실패했다. 서버가 남아 있을 수 있다. 상태 폴더: {state.folder}")
    elif state.invalid_reason is not None:
        code = INVALID
    else:
        code = PASSED if _test_ok(state) else TEST_FAILED
    record = _record(state, code)
    path = write_record(state.folder, record)
    if code == INVALID:
        streak = consecutive_invalid_rounds(state.folder)
        OUT.say(f"연달은 무효 회차 {streak}번(상태 폴더의 회차 파일로 센다).")
        if streak >= 2:
            OUT.say("연달은 무효 회차가 둘 이상이다. 다시 띄우지 말고 멈춰 사용자에게 보고한다.")
    OUT.say(
        "기록 묶음(일지와 PR 코멘트에 옮긴다):\n" + json.dumps(record, ensure_ascii=False, indent=2)
    )
    OUT.say(f"회차 파일: {path}")
    if state.results.passed is not None:
        OUT.say(f"통과 {state.results.passed}")
    return code


def _record(state: Round, code: int) -> dict[str, object]:
    tokens = state.results.tokens
    options = server_options(state.candidate) if state.candidate else []
    return {
        "commit": state.commit,
        "models": [m.model_id for m in MODELS],
        "engine": f"vLLM {VLLM_VERSION} (이미지 {IMAGE})",
        "server_options": options,
        "gpu": state.candidate.gpu.label if state.candidate else None,
        "layout": state.candidate.layout if state.candidate else None,
        "passed": state.results.passed if state.results.passed is not None else "없음",
        "tokens": (
            {
                "input_tokens": tokens.input_tokens,
                "output_tokens": tokens.output_tokens,
                "calls": tokens.calls,
                "traces": tokens.traces,
            }
            if tokens is not None
            else "없음"
        ),
        "elapsed_seconds": round(clock() - state.started, 1),
        "cost_per_hour": state.hourly,
        "price_table_date": PRICE_TABLE_DATE,
        "terraform_output_masked": OUT.terraform_masked,
        "test_command": list(state.command),
        "test_exit_code": state.child.returncode if state.child else None,
        "reason": state.invalid_reason
        or ("지우기 실패" if state.destroy_failed else "시험이 끝났다"),
        "exit_code": code,
    }


# --- sweep ---


def sweep() -> int:
    OUT.reset()
    root = state_root()
    if not root.is_dir():
        OUT.say("남은 것이 없다.")
        return PASSED
    code = PASSED
    for child in sorted(root.iterdir()):
        if "." in child.name:  # `<이름>.lock`, `<이름>.guard`
            continue
        if is_link(child):
            OUT.say(f"링크라 건드리지 않는다: {child.name}")
            continue
        if not child.is_dir():
            continue
        if not (child / MARKER).is_file() or is_link(child / MARKER):
            OUT.say(f"표지가 없어 건드리지 않는다: {child.name}")
            continue
        lock = acquire(root, child.name)
        if lock is None:
            OUT.say(f"산 잠금이라 건드리지 않는다: {child.name}")
            continue
        try:
            if state_has_resources(child) and not destroy_folder(child, None):
                OUT.say(f"자원을 지우지 못했다. 폴더를 둔다: {child}")
                code = DESTROY_FAILED
                continue
            try:
                delete_tree(child)
            except OSError as problem:
                OUT.say(f"폴더를 지우지 못했다: {child} ({problem})")
                code = DESTROY_FAILED
                continue
            OUT.say(f"치웠다: {child.name}")
        finally:
            lock.release()
    return code


def main(argv: Sequence[str] | None = None) -> int:
    words = list(sys.argv[1:] if argv is None else argv)
    command: list[str] = []
    if "--" in words:
        split = words.index("--")
        words, command = words[:split], words[split + 1 :]
    parser = argparse.ArgumentParser(
        prog="llm_local.py", description=(__doc__ or "").splitlines()[0]
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)
    run_parser = sub.add_parser("run", help="서버를 띄우고 시험을 돌린 뒤 지운다")
    run_parser.add_argument("--yes", action="store_true", help="비용을 확인받았다")
    sub.add_parser("sweep", help="남은 서버와 상태 폴더를 치운다")
    args = parser.parse_args(words)
    if args.subcommand == "sweep":
        return sweep()
    return run(yes=bool(args.yes), command=command)


if __name__ == "__main__":
    sys.exit(main())
