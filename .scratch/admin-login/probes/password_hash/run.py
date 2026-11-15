"""admin-login password_hash 프로브. 비밀번호를 저장하는 방식의 후보 둘을 고르는 데 쓸 사실을 잰다.

후보는 표준 라이브러리 `hashlib.scrypt`(`store_scrypt.py`)와 `argon2-cffi` 의 Argon2id
(`store_argon2.py`)다. 결정하지 않고 본 것만 낸다. 회차마다 재려는 상황이 그 회차에 났다는 표지를
보고 `tools/probe_kit.py` 의 `Rounds` 로 센다. 표지 없는 회차가 하나라도 있으면 종료 코드가 1 이다.
후보 패키지를 깐 환경의 파이썬으로 띄운다(README 의 다시 돌리기). 자식 프로세스는 이 스크립트를
띄운 인터프리터(`sys.executable`)로 돈다. 표지와 갈래의 기준(문턱 포함)은 아래에 적은 것이고
코드의 상수다. 해시로 고정한 사전 등록은 아니다. 문턱에 기대지 않고 읽을 수 있게 회차마다 잰 값을
함께 낸다.

항목(`--items types,host,linux`).
  types  이 폴더의 파이썬 파일을 pyright strict(저장소 잠금의 판)로 본다. 분석했다는 표지는
         `filesAnalyzed` 가 파일 수와 같은 것과 양성 대조 `control_checks.py` 의
         `reportMissingParameterType` 이다. 파일마다 오류 수를 내고, 오류를 기대하는 대조군 셋
         (`friction_*.py`)은 그 규칙이 그 파일에 났는지를 표지로 본다. 같은 검사를
         `--pythonplatform Linux` 로 한 번 더 한다. 타입 우회 검사는 `tools/check_type_escapes.py`
         의 `escapes_in` 을 파일마다 부른다. 표지는 양성 대조에서 금지된 이름 둘과 억제 주석이
         나오는 것이다. `--bare-python`(기본값은 저장소의 `.venv`)은 argon2-cffi 가 없는 환경이고
         그것으로 한 번 더 본다. 후보 모듈의 오류 0 이 그 패키지의 타입에 기댄 것인지를 가른다.
  host   이 PC 에서 아래 일곱을 돈다.
  linux  `Dockerfile` 로 이미지를 짓고(`uv sync --no-build`) 그 컨테이너 안에서 같은 일곱을 돈다.
         이미지의 설치 층이 이번 빌드에서 돌았는지 캐시였는지는 적기만 하고 회차로 세지 않는다.

일곱(`--sections` 로 고른다. 기본은 전부). 스크립트마다 `RESULT <json>` 줄을 내고 여기서 표지를
본다. 기대한 줄이 없으면 측정 아님이다.
  versions  깔린 판, 라이선스, 휠 태그, `py.typed`. 표지는 그 환경의 플랫폼이 기대한 것이고
            argon2-cffi 의 판이 `requirements.in` 의 것과 같은 것이다.
  install   그 자리의 빈 폴더에 `uv pip install --target … --no-build` 로 argon2-cffi 와
            argon2-cffi-bindings 를 판을 못 박아 깐다(스크립트가 아니라 uv 를 바로 부른다). 표지는
            출력의 `+ argon2-cffi-bindings==<판>` 줄이다. 양성 대조는 같은 명령에 맞는 휠이 없는
            플랫폼(`--python-platform x86_64-manylinux_2_17`)을 준 것이고, `has no usable wheels`
            와 `building from source is disabled` 로 거부돼야 한다. 대조가 거부되지 않으면 그
            자리의 설치 회차는 측정 아님이다. 그래야 깔린 것이 "소스를 짓지 않고 휠로"다.
  exercise  후보 모듈의 세 동작. 표지는 지금·약한·센 설정으로 만든 문자열 셋이 저마다 제 매개변수의
            머리를 갖고 맞는 비밀번호만 통과하는 것이다. 결과는 다시 해시 판정 셋이다.
  maxmem    `scrypt_maxmem.py`. 줄마다의 표지는 같은 매개변수가 `128·r·(N+p+2)` 에서 통과하고 그보다
            1 작은 값에서 `memory limit exceeded` 로 거부되는 것이다. 그래야 기본값에서의 결과가
            한도 탓이다.
  bench     `bench.py`. 회차의 표지는 `genuine`(문자열의 머리가 그 줄의 매개변수이고 맞는 비밀번호만
            통과한다)이다. 시간은 측정인 회차만으로 최솟값·중앙값·최댓값을 낸다.
  memory    `peak_memory.py` 를 줄마다 프로세스 하나로. 표지는 `genuine` 과, 같은 자리의 대조(64 MiB
            를 잡아 쓴 프로세스)가 모두 아래 끝 기준으로 64 MiB 의 ±5% 안에 든 것이다. 대조가
            벗어나면 그 자리의 메모리 회차는 측정 아님이다.
  loop      `loop_block.py`. 회차의 표지는 `genuine`, 작업 앞의 틱 100 개 이상, 작업 뒤의 틱 1 개
            이상이다. thread 와 direct 갈래는 가장 긴 틈이 작업 시간의 0.8 배 이상이면 "막힌다",
            0.2 배 이하이고 작업 동안의 틱이 100 개 이상이면 "돈다", 그 사이는 "가르지 못했다"다.
            parallel 갈래는 걸린 시간을 같은 작업의 thread 갈래 중앙값으로 나눈 값이 2.0 이하면
            "함께 돈다", 3.2 이상이면 "차례로 돈다", 그 사이는 "가르지 못했다"다. 해시의 thread 와
            parallel 회차는 같은 실행의 대조가 모든 회차에서 기대대로일 때만 측정이다(thread 는
            gil-held 가 "막힌다", gil-free 가 "돈다". parallel 은 gil-held 가 "차례로 돈다",
            gil-free 가 "함께 돈다").

자원. 만드는 컨테이너의 이름은 `admin-login-pwhash-probe-<토큰>-` 으로 시작하고 끝에서(예외가 나도)
그 접두로 찾아 지운다. 네트워크와 볼륨은 만들지 않는다. 이미지 `admin-login-pwhash-probe-linux` 는
남긴다. 모든 명령의 원본 출력은 `--work` 아래 `raw-<토큰>.log` 에 남는다.

못 보는 것.
- 배포 환경의 CPU 와 메모리 한도. 시간은 이 PC 와 이 PC 의 Docker 엔진(WSL2)에서 잰 것이다.
- 다른 측정 세션이 같은 PC 와 같은 Docker 데몬을 쓴다. 시간은 범위로 읽는다.
- 해시가 잡고 쓰지 않은 메모리. 상주 메모리만 읽는다.
"""

from __future__ import annotations

import argparse
import io
import json
import secrets
import statistics
import subprocess
import sys
import tempfile
import time
import tokenize
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

import loop_block  # noqa: E402
import scrypt_maxmem  # noqa: E402
from rows import MIB, ROWS  # noqa: E402
from tools.check_type_escapes import escapes_in  # noqa: E402
from tools.probe_kit import Rounds  # noqa: E402

PREFIX = "admin-login-pwhash-probe"
LINUX_IMAGE = f"{PREFIX}-linux"
BASE_IMAGE = "python:3.12-slim-trixie"
PROBE_IN_IMAGE = "/app/.scratch/admin-login/probes/password_hash"
PYTHON_IN_IMAGE = "/app/.venv/bin/python"
SYNC_LINE = "uv sync --frozen --no-install-project --no-build"
CONTROL = "control_checks.py"
SUBJECTS = ("store_scrypt.py", "store_argon2.py")
FRICTIONS = {
    "friction_argon2_arg.py": "reportArgumentType",
    "friction_argon2_low_level.py": "reportUnknownMemberType",
    "friction_scrypt_arg.py": "reportArgumentType",
}
REFUSED = "memory limit exceeded"
WHEEL_TAGS = {"win32": ("win_amd64",), "linux": ("manylinux", "x86_64")}
NO_WHEEL_PLATFORM = "x86_64-manylinux_2_17"
NO_WHEEL = "has no usable wheels"
NO_BUILD = "building from source is disabled"
TARGET_IN_IMAGE = "/tmp/fresh"
SECTIONS = ("versions", "install", "exercise", "maxmem", "bench", "memory", "loop")
BLOCKED, RUNS, UNCLEAR = "막힌다", "돈다", "가르지 못했다"
TOGETHER, IN_TURN = "함께 돈다", "차례로 돈다"

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


def as_number(value: Json) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"수가 아니다: {value!r}")
    return float(value)


def dig(value: Json, *keys: str) -> Json:
    for key in keys:
        value = value.get(key) if isinstance(value, dict) else None
    return value


def results_in(text: str) -> list[Json]:
    """출력에서 `RESULT <json>` 줄을 모은다."""
    lines = [line.removeprefix("RESULT ") for line in text.splitlines() if "RESULT {" in line]
    return [parse(line) for line in lines]


def spread(values: Sequence[float]) -> str:
    if not values:
        return "(측정인 회차 없음)"
    low, middle, high = min(values), statistics.median(values), max(values)
    return f"최소 {low:.1f} / 중앙 {middle:.1f} / 최대 {high:.1f} (n={len(values)})"


@dataclass(frozen=True)
class Done:
    code: int
    out: str
    err: str
    seconds: float

    @property
    def text(self) -> str:
        return f"{self.out}\n{self.err}"


def run(argv: Sequence[str], *, timeout: float = 300) -> Done:
    """명령 하나. 표준 입력은 닫힌 파이프다. 시간을 넘기면 종료 코드 -1 이다."""
    started = time.monotonic()
    try:
        completed = subprocess.run(
            list(argv),
            input="",
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


def docker(*args: str, timeout: float = 300) -> Done:
    return run(["docker", *args], timeout=timeout)


@dataclass(frozen=True)
class Verdict:
    measured: bool
    result: str
    detail: str = ""


def counted(result: str, detail: str = "") -> Verdict:
    """표지를 본 회차."""
    return Verdict(measured=True, result=result, detail=detail)


def uncounted(result: str, detail: str = "") -> Verdict:
    """표지를 보지 못한 회차. 측정으로 세지 않는다."""
    return Verdict(measured=False, result=result, detail=detail)


@dataclass
class Context:
    token: str
    rounds: Rounds
    work: Path
    serial: int = 0

    def name(self, label: str) -> str:
        self.serial += 1
        return f"{PREFIX}-{self.token}-{label}-{self.serial}"

    def judge(self, label: str, verdict: Callable[[], Verdict]) -> bool:
        """회차 하나를 세고 한 줄로 낸다. 판정이 예외로 끝나면 측정 아님으로 센다."""
        detail = ""
        with self.rounds.round(label) as slot:
            found = verdict()
            slot.mark(measured=found.measured, result=found.result)
            detail = found.detail
        entry = self.rounds.entries[-1]
        mark = "측정" if entry.measured else "측정 아님"
        tail = f" | {detail}" if detail else ""
        print(f"- [{mark}] {entry.label} => {entry.result}{tail}", flush=True)
        return entry.measured


@dataclass(frozen=True)
class Place:
    """스크립트를 띄우는 자리. 이 PC 이거나 리눅스 컨테이너다."""

    name: str
    platform: str
    launch: Callable[[str, Sequence[str], float], Done]
    install: Callable[[str, Sequence[str]], Done]


def host_load() -> str:
    """호스트 CPU 부하(윈도만). 시간을 읽을 때의 사정을 적으려는 것이고 회차로 세지 않는다."""
    if sys.platform != "win32":
        return "(윈도가 아니라 재지 않았다)"
    command = "(Get-CimInstance Win32_Processor).LoadPercentage"
    done = run(["powershell", "-NoProfile", "-Command", command], timeout=60)
    return f"{done.out.strip()}%" if done.code == 0 else "(읽지 못했다)"


def cleanup(token: str) -> None:
    """이 실행이 만든 컨테이너만 지운다. 이름 접두가 `<PREFIX>-<토큰>-` 인 것이다."""
    prefix = f"{PREFIX}-{token}-"
    listed = docker("ps", "-a", "--filter", f"name={prefix}", "--format", "{{.Names}}").out.split()
    containers = [name for name in listed if name.startswith(prefix)]
    if containers:
        docker("rm", "-f", *containers)
    print(f"정리: 컨테이너 {len(containers)}", flush=True)


# ---------------------------------------------------------------- types


def typecheck(*extra: str) -> Json:
    done = run([sys.executable, str(HERE / "typecheck.py"), *extra], timeout=900)
    return parse(done.out)


def errors_by_file(report: Json) -> dict[str, list[str]]:
    """파일(이 폴더 기준 경로)마다 오류의 규칙 이름."""
    found: dict[str, list[str]] = {}
    for item in as_list(dig(report, "generalDiagnostics")):
        if dig(item, "severity") != "error":
            continue
        path = Path(as_text(dig(item, "file")))
        key = path.relative_to(HERE).as_posix() if path.is_relative_to(HERE) else path.name
        found.setdefault(key, []).append(as_text(dig(item, "rule")) or "(규칙 없음)")
    return found


def revealed(report: Json) -> list[str]:
    lines: list[str] = []
    for item in as_list(dig(report, "generalDiagnostics")):
        message = as_text(dig(item, "message"))
        if dig(item, "severity") == "information" and message.startswith("Type of"):
            lines.append(message.replace("\n", " "))
    return lines


def probe_files() -> list[str]:
    paths = [path for path in HERE.rglob("*.py") if "__pycache__" not in path.parts]
    return sorted(path.relative_to(HERE).as_posix() for path in paths)


def code_lines(name: str) -> int:
    """주석, 빈 줄, 모듈 독스트링을 뺀 줄 수. 후보 모듈의 크기를 견주려는 것이고 회차가 아니다."""
    source = (HERE / name).read_text(encoding="utf-8")
    skipped = {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT}
    skipped |= {tokenize.ENCODING, tokenize.ENDMARKER}
    tokens = [
        token
        for token in tokenize.generate_tokens(io.StringIO(source).readline)
        if token.type not in skipped
    ]
    if tokens and tokens[0].type == tokenize.STRING:
        tokens = tokens[1:]
    lines: set[int] = set()
    for token in tokens:
        lines.update(range(token.start[0], token.end[0] + 1))
    return len(lines)


def analysis_seen(report: Json, files: Sequence[str]) -> tuple[bool, str]:
    errors = errors_by_file(report)
    analyzed = dig(report, "summary", "filesAnalyzed")
    strict = "reportMissingParameterType" in errors.get(CONTROL, [])
    text = (
        f"pyright {dig(report, 'version')}, filesAnalyzed {analyzed}/{len(files)}, "
        f"양성 대조의 오류 {sorted(set(errors.get(CONTROL, [])))}"
    )
    return analyzed == len(files) and strict, text


def types_item(ctx: Context, bare_python: str) -> None:
    print("\n## types", flush=True)
    files = probe_files()
    reports = {
        "호스트 플랫폼": typecheck(),
        "pythonPlatform Linux": typecheck("--pythonplatform", "Linux"),
    }
    for label, report in reports.items():
        errors = errors_by_file(report)
        seen, text = analysis_seen(report, files)
        ctx.judge(
            f"types pyright 분석 범위({label})",
            lambda seen=seen, text=text: Verdict(seen, "분석했다", text),
        )
        for name in files:
            if name == CONTROL:
                continue
            rules = errors.get(name, [])
            expected = FRICTIONS.get(name)
            measured = seen and (expected is None or expected in rules)
            ctx.judge(
                f"types pyright {name}({label})",
                lambda measured=measured, rules=rules: Verdict(
                    measured, f"오류 {len(rules)}", f"{sorted(set(rules))}"
                ),
            )
    print("타입 드러내기(reveal.py 와 friction_argon2_low_level.py, 호스트 플랫폼):", flush=True)
    for line in revealed(reports["호스트 플랫폼"]):
        print(f"  {line}", flush=True)
    control = escapes_in((HERE / CONTROL).read_text(encoding="utf-8"))
    listening = all(any(word in line for line in control) for word in ("`Any`", "`cast`", "억제"))
    ctx.judge(
        "types 타입 우회 검사의 양성 대조",
        lambda: Verdict(listening, "듣는다" if listening else "듣지 않는다", f"{control}"),
    )
    for name in files:
        if name == CONTROL:
            continue
        found = escapes_in((HERE / name).read_text(encoding="utf-8"))
        ctx.judge(
            f"types 타입 우회 {name}",
            lambda found=found: Verdict(listening, f"우회 {len(found)}", f"{found}"),
        )
    for name in SUBJECTS:
        print(f"코드 줄 수(주석·빈 줄·모듈 독스트링 제외) {name}: {code_lines(name)}", flush=True)
    if not bare_python:
        return
    report = typecheck("--interpreter", bare_python)
    errors = errors_by_file(report)
    seen, text = analysis_seen(report, files)
    ctx.judge(
        "types argon2-cffi 없는 환경의 분석 범위",
        lambda: Verdict(seen, "분석했다", f"{text}, 인터프리터 {bare_python}"),
    )
    for name in (*SUBJECTS, "friction_argon2_arg.py"):
        rules = errors.get(name, [])
        ctx.judge(
            f"types argon2-cffi 없는 환경 {name}",
            lambda rules=rules: Verdict(seen, f"오류 {len(rules)}", f"{sorted(set(rules))}"),
        )


# ---------------------------------------------------------------- versions


def pinned_version() -> str:
    lines = (HERE / "requirements.in").read_text(encoding="utf-8").splitlines()
    return next(line.partition("==")[2].strip() for line in lines if line.startswith("argon2-cffi"))


def versions_section(ctx: Context, place: Place) -> str:
    """깔린 것을 내고, 그 자리에 깔린 argon2-cffi-bindings 의 판을 돌려준다(없으면 빈 문자열)."""
    print(f"\n### {place.name} versions", flush=True)
    items = results_in(place.launch("versions.py", [], 120).out)
    for item in items:
        print(f"  {json.dumps(item, ensure_ascii=False)}", flush=True)
    environment = next((item for item in items if dig(item, "platform") is not None), None)
    packages = {as_text(dig(item, "name")): item for item in items if dig(item, "name")}
    here = dig(environment, "platform") == place.platform
    pinned = dig(packages.get("argon2-cffi"), "version") == pinned_version()

    def wheel() -> Verdict:
        tags = [as_text(tag) for tag in as_list(dig(packages["argon2-cffi-bindings"], "tags"))]
        wanted = WHEEL_TAGS[place.platform]
        fits = any(all(part in tag for part in wanted) for tag in tags)
        compilers = dig(environment, "compilers")
        paths = compilers if isinstance(compilers, dict) else {}
        found = [name for name, path in paths.items() if path]
        result = "그 플랫폼의 휠이다" if fits else "그 플랫폼의 휠이 아니다"
        return Verdict(here and pinned, result, f"태그 {tags}, 경로의 컴파일러 {found or '없음'}")

    def typed() -> Verdict:
        marks = {
            name: bool(as_list(dig(packages[name], "py_typed")))
            for name in ("argon2-cffi", "argon2-cffi-bindings", "cffi")
        }
        result = "py.typed " + ", ".join(
            f"{name} {'있음' if has else '없음'}" for name, has in marks.items()
        )
        return Verdict(here and pinned, result)

    ctx.judge(f"{place.name} versions argon2-cffi-bindings 의 휠", wheel)
    ctx.judge(f"{place.name} versions 타입 표지", typed)
    return as_text(dig(packages.get("argon2-cffi-bindings"), "version"))


# ---------------------------------------------------------------- install


def flat(text: str) -> str:
    """줄바꿈과 들여쓰기를 한 칸으로. uv 의 오류 글은 줄을 감아 낸다."""
    return " ".join(text.split())


def install_section(ctx: Context, place: Place, bindings: str) -> None:
    """빈 폴더에 `--no-build` 로 후보를 깐다. 판을 둘 다 못 박아 다른 판으로 물러서지 않게 한다."""
    print(f"\n### {place.name} install", flush=True)
    pins = [f"argon2-cffi=={pinned_version()}", f"argon2-cffi-bindings=={bindings}"]
    refused: list[bool] = []

    def control() -> Verdict:
        done = place.install("no-wheel", ["--python-platform", NO_WHEEL_PLATFORM, *pins])
        text = flat(done.text)
        seen = done.code != 0 and NO_WHEEL in text and NO_BUILD in text
        refused.append(seen)
        detail = f"exit {done.code}, {text[-220:]}"
        return Verdict(seen, "거부됐다" if seen else "거부되지 않았다", detail)

    def wheel_only() -> Verdict:
        done = place.install("wheel", pins)
        added = [line.strip() for line in done.text.splitlines() if line.startswith(" + ")]
        detail = f"exit {done.code}, {added or flat(done.text)[-220:]}"
        if not (bindings and all(refused)):
            return uncounted("대조가 서지 않아 읽지 못한다", detail)
        if done.code == 0 and f"+ {pins[1]}" in added:
            return counted("깔렸다", detail)
        text = flat(done.text)
        if done.code != 0 and NO_WHEEL in text and NO_BUILD in text:
            return counted("거부됐다(맞는 휠이 없다)", detail)
        return uncounted("판정하지 못했다", detail)

    ctx.judge(f"{place.name} install 대조: 맞는 휠이 없는 플랫폼({NO_WHEEL_PLATFORM})", control)
    ctx.judge(f"{place.name} install --no-build 로 그 자리에", wheel_only)


# ---------------------------------------------------------------- exercise


def exercise_section(ctx: Context, place: Place) -> None:
    print(f"\n### {place.name} exercise", flush=True)
    items = results_in(place.launch("exercise.py", [], 300).out)
    by_name = {as_text(dig(item, "candidate")): item for item in items if dig(item, "candidate")}

    def candidate(name: str) -> Verdict:
        item = by_name[name]
        triples = [as_list(dig(item, key)) for key in ("current", "weaker", "stronger")]
        heads = as_list(dig(item, "prefixes_ok"))
        genuine = heads == [True, True, True] and all(
            triple[:2] == [True, False] for triple in triples
        )
        broken = dig(item, "broken")
        leaks = (
            {
                label: as_list(calls)
                for label, calls in broken.items()
                if any("예외" in as_text(call) for call in as_list(calls))
            }
            if isinstance(broken, dict)
            else {}
        )
        result = "다시 해시 판정: " + ", ".join(
            f"{label} {triple[2]}"
            for label, triple in zip(("지금", "약한", "센"), triples, strict=True)
        )
        detail = (
            f"문자열 길이 {dig(item, 'stored_len')}, 소금이 달라짐 {dig(item, 'salts_differ')}, "
            f"깨진 입력 {len(broken) if isinstance(broken, dict) else 0}개 가운데 예외가 샌 것 "
            f"{json.dumps(leaks, ensure_ascii=False)}"
        )
        return Verdict(genuine, result, detail)

    def raised() -> Verdict:
        found = next(dig(item, "raised") for item in items if dig(item, "raw"))
        if not isinstance(found, dict) or len(found) != 4:
            return uncounted("줄이 모자라다", f"{found}")
        kinds = sorted({as_text(text).partition(":")[0] for text in found.values()})
        return counted(f"예외 종류 {kinds}", json.dumps(found, ensure_ascii=False))

    for name in ("scrypt", "argon2"):
        ctx.judge(f"{place.name} exercise {name}", lambda name=name: candidate(name))
    ctx.judge(f"{place.name} exercise hashlib.scrypt 가 던지는 예외", raised)


# ---------------------------------------------------------------- maxmem


def maxmem_section(ctx: Context, place: Place) -> None:
    print(f"\n### {place.name} maxmem", flush=True)
    items = results_in(place.launch("scrypt_maxmem.py", [], 600).out)
    by_kind: dict[str, list[Json]] = {}
    for item in items:
        by_kind.setdefault(as_text(dig(item, "kind")), []).append(item)
    print(f"  {json.dumps(by_kind.get('openssl', []), ensure_ascii=False)}", flush=True)
    defaults = {as_text(dig(item, "label")): item for item in by_kind.get("default", [])}
    scrypt_rows = [row for row in ROWS if row.candidate == "scrypt"]

    def default(label: str) -> Verdict:
        item = defaults[label]
        outcome = as_text(dig(item, "default"))
        boundary = dig(item, "at_formula") == "ok" and REFUSED in as_text(
            dig(item, "below_formula")
        )
        result = "통과" if outcome == "ok" else "거부" if REFUSED in outcome else "다른 오류"
        return Verdict(boundary, result, f"{outcome}, 식의 값 {dig(item, 'formula')} 바이트")

    def least() -> Verdict:
        item = by_kind["least"][0]
        ends = [as_text(end) for end in as_list(dig(item, "ends"))]
        bracketed = len(ends) == 2 and REFUSED in ends[0] and ends[1] == "ok"
        found, formula = dig(item, "least"), dig(item, "formula")
        result = "식과 같다" if found == formula else "식과 다르다"
        detail = f"가장 작은 maxmem {found}, 식 {formula}, 부른 횟수 {dig(item, 'calls')}"
        return Verdict(bracketed, result, detail)

    def limit() -> Verdict:
        item = by_kind["limit"][0]
        passes, refused = as_text(dig(item, "passes")), as_text(dig(item, "refused"))
        low, high = dig(item, "passes_bytes"), dig(item, "refused_bytes")
        found = passes == "ok" and REFUSED in refused
        result = "32 MiB 바로 아래에서 통과, 바로 위에서 거부" if found else "그 자리가 아니다"
        return counted(result, f"{low} 바이트 {passes} / {high} 바이트 {refused}")

    def ceiling() -> Verdict:
        item = by_kind["ceiling"][0]
        low, high = as_text(dig(item, "at_2_31_minus_1")), as_text(dig(item, "at_2_31"))
        return Verdict(bool(low and high), f"2^31-1 {low} / 2^31 {high.partition(':')[0]}", high)

    for row in (*scrypt_rows, scrypt_maxmem.CONTROL):
        ctx.judge(f"{place.name} maxmem 기본값 {row.label}", lambda label=row.label: default(label))
    ctx.judge(f"{place.name} maxmem 가장 작은 값(이분법)", least)
    ctx.judge(f"{place.name} maxmem 기본 한도의 자리", limit)
    ctx.judge(f"{place.name} maxmem 인자의 위 끝", ceiling)


# ---------------------------------------------------------------- bench


def bench_section(ctx: Context, place: Place, rounds: int, other_rounds: int) -> None:
    print(f"\n### {place.name} bench", flush=True)
    print(f"호스트 CPU 부하(시작): {host_load()}", flush=True)
    args = ["--rounds", str(rounds), "--other-rounds", str(other_rounds)]
    items = results_in(place.launch("bench.py", args, 1800).out)
    print(f"호스트 CPU 부하(끝): {host_load()}", flush=True)
    index = {(as_text(dig(item, "key")), dig(item, "round")): item for item in items}
    for row in ROWS:
        hashes: list[float] = []
        verifies: list[float] = []

        def one(key: str, number: int, hashes: list[float], verifies: list[float]) -> Verdict:
            item = index[key, number]
            hash_ms, verify_ms = as_number(dig(item, "hash_ms")), as_number(dig(item, "verify_ms"))
            if dig(item, "genuine") is not True:
                return uncounted("표지가 없다", f"{item}")
            hashes.append(hash_ms)
            verifies.append(verify_ms)
            return counted("해시됨", f"해시 {hash_ms}ms, 견줌 {verify_ms}ms")

        for number in range(1, (rounds if row.headline else other_rounds) + 1):
            ctx.judge(
                f"{place.name} bench {row.key} #{number}",
                lambda key=row.key, number=number, hashes=hashes, verifies=verifies: one(
                    key, number, hashes, verifies
                ),
            )
        print(
            f"STAT {place.name} bench {row.key} [{row.source}] 해시 ms {spread(hashes)}, "
            f"견줌 ms {spread(verifies)}",
            flush=True,
        )


# ---------------------------------------------------------------- memory


def memory_section(ctx: Context, place: Place, rounds: int) -> None:
    print(f"\n### {place.name} memory", flush=True)

    def read(key: str) -> Json:
        found = results_in(place.launch("peak_memory.py", ["--key", key], 300).out)
        return found[0] if found else None

    def ends(item: Json) -> tuple[float, float]:
        after = as_number(dig(item, "peak_after"))
        return (
            after - as_number(dig(item, "peak_before")),
            after - as_number(dig(item, "rss_before")),
        )

    def describe(item: Json) -> str:
        low, high = ends(item)
        nominal = as_number(dig(item, "nominal_bytes"))
        return (
            f"아래 끝 {low / MIB:.2f} MiB, 위 끝 {high / MIB:.2f} MiB, "
            f"줄이 적은 값 {nominal / MIB:.2f} MiB"
        )

    controls_ok: list[bool] = []

    def control() -> Verdict:
        item = read("control")
        low, _ = ends(item)
        nominal = as_number(dig(item, "nominal_bytes"))
        fits = abs(low - nominal) <= 0.05 * nominal
        controls_ok.append(dig(item, "genuine") is True and fits)
        result = "64 MiB 를 본다" if fits else "64 MiB 를 보지 못한다"
        return Verdict(dig(item, "genuine") is True, result, describe(item))

    for number in range(1, rounds + 1):
        ctx.judge(f"{place.name} memory 대조 #{number}", control)
    gate = len(controls_ok) == rounds and all(controls_ok)
    for row in ROWS:
        lows: list[float] = []
        highs: list[float] = []

        def one(key: str, lows: list[float], highs: list[float]) -> Verdict:
            item = read(key)
            if not gate:
                return uncounted("대조가 벗어나 읽지 못한다", describe(item))
            if dig(item, "genuine") is not True:
                return uncounted("표지가 없다", f"{item}")
            low, high = ends(item)
            lows.append(low / MIB)
            highs.append(high / MIB)
            return counted("읽었다", describe(item))

        for number in range(1, rounds + 1):
            ctx.judge(
                f"{place.name} memory {row.key} #{number}",
                lambda key=row.key, lows=lows, highs=highs: one(key, lows, highs),
            )
        print(
            f"STAT {place.name} memory {row.key} 줄이 적은 값 {row.nominal_bytes / MIB:.2f} MiB, "
            f"아래 끝 MiB {spread(lows)}, 위 끝 MiB {spread(highs)}",
            flush=True,
        )


# ---------------------------------------------------------------- loop


def alive(item: Json) -> bool:
    """재려는 상황의 표지. 작업이 제 값을 냈고 틱이 작업 앞뒤로 찍혔다."""
    return (
        dig(item, "genuine") is True
        and as_number(dig(item, "idle_ticks")) >= 100
        and as_number(dig(item, "after_ticks")) >= 1
    )


def gap_verdict(item: Json) -> str:
    work, gap = as_number(dig(item, "work_ms")), as_number(dig(item, "max_gap_ms"))
    if gap >= 0.8 * work:
        return BLOCKED
    if gap <= 0.2 * work and as_number(dig(item, "ticks")) >= 100:
        return RUNS
    return UNCLEAR


def ratio_verdict(ratio: float) -> str:
    if ratio <= 2.0:
        return TOGETHER
    if ratio >= 0.8 * loop_block.PARALLEL:
        return IN_TURN
    return UNCLEAR


def loop_section(ctx: Context, place: Place, rounds: int) -> None:
    print(f"\n### {place.name} loop", flush=True)
    items = results_in(place.launch("loop_block.py", ["--rounds", str(rounds)], 1800).out)
    environment = next((item for item in items if dig(item, "kind") == "loop-env"), None)
    print(f"  {json.dumps(environment, ensure_ascii=False)}", flush=True)
    index = {
        (as_text(dig(item, "job")), as_text(dig(item, "mode")), dig(item, "round")): item
        for item in items
        if dig(item, "kind") == "loop"
    }
    numbers = range(1, rounds + 1)

    def kept(job: str, mode: str) -> list[Json]:
        found = [index.get((job, mode, number)) for number in numbers]
        return [item for item in found if item is not None and alive(item)]

    def single(job: str) -> float | None:
        works = [as_number(dig(item, "work_ms")) for item in kept(job, "thread")]
        return statistics.median(works) if works else None

    def ratio(job: str, item: Json) -> float | None:
        base = single(job)
        return None if base is None else as_number(dig(item, "work_ms")) / base

    def control_holds(mode: str) -> bool:
        if mode == "thread":
            held = [gap_verdict(item) for item in kept(loop_block.HELD, mode)]
            free = [gap_verdict(item) for item in kept(loop_block.FREE, mode)]
            wanted = (BLOCKED, RUNS)
        else:
            held = [
                ratio_verdict(ratio(loop_block.HELD, item) or 0.0)
                for item in kept(loop_block.HELD, mode)
            ]
            free = [
                ratio_verdict(ratio(loop_block.FREE, item) or 0.0)
                for item in kept(loop_block.FREE, mode)
            ]
            wanted = (IN_TURN, TOGETHER)
        return (
            len(held) == rounds
            and len(free) == rounds
            and all(found == wanted[0] for found in held)
            and all(found == wanted[1] for found in free)
        )

    gates = {"thread": control_holds("thread"), "parallel": control_holds("parallel")}
    print(f"대조가 기대대로인가: {gates}", flush=True)

    def one(job: loop_block.Job, mode: str, number: int, seen: list[str]) -> Verdict:
        item = index[job.name, mode, number]
        work, gap = as_number(dig(item, "work_ms")), as_number(dig(item, "max_gap_ms"))
        detail = (
            f"작업 {work}ms, 가장 긴 틈 {gap}ms, 작업 동안의 틱 {dig(item, 'ticks')}, "
            f"작업 앞의 가장 긴 틈 {dig(item, 'idle_max_ms')}ms"
        )
        if not alive(item):
            return uncounted("표지가 없다", detail)
        if mode == "parallel":
            found = ratio(job.name, item)
            if found is None:
                return uncounted("견줄 thread 회차가 없다", detail)
            result = ratio_verdict(found)
            detail = f"{detail}, thread 중앙값의 {found:.2f}배"
        else:
            result = gap_verdict(item)
        if job.is_hash and mode in gates and not gates[mode]:
            return uncounted("대조가 기대와 달라 읽지 못한다", f"{result}, {detail}")
        seen.append(result)
        return counted(result, detail)

    for job in loop_block.jobs():
        for mode in loop_block.MODES:
            if mode == "direct" and not job.is_hash:
                continue
            seen: list[str] = []
            for number in numbers:
                ctx.judge(
                    f"{place.name} loop {job.name} {mode} #{number}",
                    lambda job=job, mode=mode, number=number, seen=seen: one(
                        job, mode, number, seen
                    ),
                )
            works = [as_number(dig(item, "work_ms")) for item in kept(job.name, mode)]
            gaps = [as_number(dig(item, "max_gap_ms")) for item in kept(job.name, mode)]
            print(
                f"STAT {place.name} loop {job.name} {mode} 판정 {dict(Counter(seen))}, "
                f"작업 ms {spread(works)}, 가장 긴 틈 ms {spread(gaps)}",
                flush=True,
            )


# ---------------------------------------------------------------- 자리


def sections(ctx: Context, place: Place, args: argparse.Namespace) -> None:
    rounds: int = args.rounds
    other_rounds: int = args.other_rounds
    memory_rounds: int = args.memory_rounds
    loop_rounds: int = args.loop_rounds
    chosen = {item for item in str(args.sections).split(",") if item}
    if chosen & {"versions", "install"}:
        bindings = versions_section(ctx, place)
        if "install" in chosen:
            install_section(ctx, place, bindings)
    if "exercise" in chosen:
        exercise_section(ctx, place)
    if "maxmem" in chosen:
        maxmem_section(ctx, place)
    if "bench" in chosen:
        bench_section(ctx, place, rounds, other_rounds)
    if "memory" in chosen:
        memory_section(ctx, place, memory_rounds)
    if "loop" in chosen:
        loop_section(ctx, place, loop_rounds)


def host_item(ctx: Context, args: argparse.Namespace) -> None:
    print("\n## host", flush=True)

    def launch(script: str, extra: Sequence[str], timeout: float) -> Done:
        return run([sys.executable, str(HERE / script), *extra], timeout=timeout)

    def install(label: str, extra: Sequence[str]) -> Done:
        target = ctx.work / f"fresh-{ctx.token}-{label}"
        head = ["uv", "pip", "install", "--python", sys.executable, "--target", str(target)]
        return run([*head, "--no-build", *extra])

    sections(ctx, Place("host", sys.platform, launch, install), args)


def linux_item(ctx: Context, args: argparse.Namespace) -> None:
    print("\n## linux", flush=True)
    tree = Path(str(args.tree))
    identify = ("image", "inspect", LINUX_IMAGE, "--format", "{{.Id}}")
    before = docker(*identify).out.strip()
    built = docker(
        "build", "--progress", "plain", "-f", str(HERE / "Dockerfile"),
        "--build-context", f"tree={tree}", "-t", LINUX_IMAGE, str(HERE), timeout=1500,
    )  # fmt: skip
    named = f"naming to docker.io/library/{LINUX_IMAGE}" in built.text
    ok = built.code == 0 and named
    ctx.judge("linux 이미지 빌드", lambda: Verdict(ok, "지었다", f"{built.seconds:.0f}초"))
    if not ok:
        return
    # 설치 층이 이번 빌드에서 돌았으면 uv 가 깐 패키지를 `+ 이름==판` 으로 낸다. 캐시된 층에는 그
    # 줄이 없다. 회차로 세지 않는다. 휠만으로 깔리는지는 `install` 이 회차마다 본다.
    ran = any(" + argon2-cffi-bindings==" in line for line in built.text.splitlines())
    state = "이번 빌드에서 돌았다" if ran else "캐시된 층"
    print(f"이미지의 설치 층({SYNC_LINE}): {state}", flush=True)
    # 파일이 바뀌어 새로 지으면 앞선 빌드의 이미지가 이름을 잃고 남는다. 빌드 직전에 이 이름이
    # 가리키던 것만 지운다. 다른 이름이 붙었거나 컨테이너가 쓰면 `docker image rm` 이 거부한다.
    after = docker(*identify).out.strip()
    if before.startswith("sha256:") and after.startswith("sha256:") and before != after:
        gone = "지웠다" if docker("image", "rm", before).code == 0 else "지우지 못했다"
        print(f"앞선 빌드의 이미지 {before[7:19]}: {gone}", flush=True)
    base = docker("image", "inspect", BASE_IMAGE, "--format", "{{index .RepoDigests 0}}")
    size = docker("image", "inspect", LINUX_IMAGE, "--format", "{{.Size}}")
    print(f"바탕 {base.out.strip()}", flush=True)
    print(f"지은 이미지 {LINUX_IMAGE} {size.out.strip()} 바이트", flush=True)

    def launch(script: str, extra: Sequence[str], timeout: float) -> Done:
        label = script.removesuffix(".py").replace("_", "-")
        head = ("run", "--rm", "--name", ctx.name(label), "-w", "/app", LINUX_IMAGE)
        command = (PYTHON_IN_IMAGE, f"{PROBE_IN_IMAGE}/{script}", *extra)
        return docker(*head, *command, timeout=timeout)

    def install(label: str, extra: Sequence[str]) -> Done:
        head = ("run", "--rm", "--name", ctx.name(f"install-{label}"), "-w", "/app", LINUX_IMAGE)
        uv = ("uv", "pip", "install", "--python", PYTHON_IN_IMAGE, "--target", TARGET_IN_IMAGE)
        return docker(*head, *uv, "--no-build", *extra)

    sections(ctx, Place("linux", "linux", launch, install), args)


# ---------------------------------------------------------------- 진입


def default_bare_python() -> str:
    relative = "Scripts/python.exe" if sys.platform == "win32" else "bin/python"
    path = ROOT / ".venv" / relative
    return str(path) if path.exists() else ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--items", default="types,host,linux")
    parser.add_argument("--sections", default=",".join(SECTIONS), help="host 와 linux 안에서 돌 것")
    parser.add_argument("--tree", default="", help="후보를 더한 pyproject.toml 과 uv.lock 의 폴더")
    parser.add_argument("--bare-python", default=default_bare_python())
    parser.add_argument("--rounds", type=int, default=10, help="bench 요약 줄의 회차")
    parser.add_argument("--other-rounds", type=int, default=5, help="bench 나머지 줄의 회차")
    parser.add_argument("--memory-rounds", type=int, default=2)
    parser.add_argument("--loop-rounds", type=int, default=5)
    parser.add_argument("--work", default="")
    args = parser.parse_args()
    items = {item for item in str(args.items).split(",") if item}
    work = Path(str(args.work) or tempfile.mkdtemp(prefix="password-hash-"))
    work.mkdir(parents=True, exist_ok=True)
    token = secrets.token_hex(3)
    _raw.append(work / f"raw-{token}.log")
    ctx = Context(token, Rounds(), work)
    print(f"실행 토큰 {token}, 원본 기록 {_raw[0]}", flush=True)
    print(f"파이썬 {sys.version.split()[0]}, 호스트 {sys.platform}", flush=True)
    try:
        if "types" in items:
            types_item(ctx, str(args.bare_python))
        if "host" in items:
            host_item(ctx, args)
        if "linux" in items:
            version = docker("version", "--format", "엔진 {{.Server.Version}} {{.Server.Os}}")
            print(version.out.strip(), flush=True)
            linux_item(ctx, args)
    finally:
        if "linux" in items:
            cleanup(token)
    print(f"\n{ctx.rounds.summary()}", flush=True)
    return ctx.rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
