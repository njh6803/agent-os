"""바이트 그대로 되돌리는 변이 도구.

테스트가 무엇을 재는지 변이로 본다. 구현 전부터 초록인 가드, 구현 뒤에 쓴 테스트, 새 검사가 그
대상이다. 세션마다 스크래치에 변이 스크립트를 새로 짓다가 같은 함정을 두 번 밟아서 여기 있다(대기열
29). 텍스트로 되돌려 줄 끝이 CRLF 가 됐고, 기대 결과를 받지 않아 아무것도 재지 않은 변이가 초록으로
지나갔다. pytest 밖의 명령(Vitest, Playwright, tsc)도 돈다. web 티켓 03~08이 같은 규약의 JS 러너를
저마다 지었고 첫 판정이 틀렸다(대기열 59, tsc 의 종료 코드 2를 빨강으로, TS1360 을 문법 오류로).

사용: PYTHONUTF8=1 uv run python tools/mutate.py <변이 파일.toml> [이름 ...] [--check]
      uv run python tools/mutate.py --check <변이 파일.toml> <변이 파일.toml> ...
LLM 테스트가 대상이면 `PYTHONUTF8=1 uv run --env-file .env python tools/mutate.py …` 이고 tests 에
`-m llm` 을 넣는다. 이름을 주면 그 변이만 돈다. `--check` 는 원문만 본다 — 명령을 돌리지 않고, 고른
변이마다 원문이 파일에 정확히 한 번 있는지(와 러너의 자리, 되돌릴 파일)를 보고 틀린 것을 모두
알린다. 코드를 고친 뒤 다른 변이 파일의 원문이 옮겨 가지 않았는지 볼 때 쓴다. `--check` 만 변이
파일 여럿(`.toml` 로 끝나는 인자)을 받고, 그때는 이름을 섞지 않는다. 이름 없이 주면 줄마다 그
파일의 경로가 붙고 읽지 못한 파일이 있어도 나머지를 본다. pre-commit 이 커밋에 든 변이
표(`_mutations.toml`)를 이 모양으로 넘긴다 — 변이를 돌린 뒤 `ruff format` 이 코드를 고쳐 커밋한
표의 원문이 사라진 일이 있었다(대기열 92). 커밋에 들지 않은 옛 표는 보지 않는다. 옛 프로브의
원문은 코드가 바뀌면 썩어도 되고, 다시 돌리거나 고쳐 커밋할 때 이 확인이 알린다.

변이 파일은 TOML 이다. 원문은 리터럴 여러 줄 문자열(`'''`)로 적으면 이스케이프가 없다. 여는 `'''`
바로 뒤의 줄바꿈은 TOML 이 버린다. 아래 예시는 네 칸 들여쓴 채라 옮길 때 그 네 칸을 걷어 낸다.

    [runner.vitest]                      # 선택. 이름은 마음대로이고 pytest 만 내장이라 못 쓴다
    command = ["pnpm", "exec", "vitest", "run"]
    cwd = "web"                          # 저장소 루트 기준. 기본은 루트
    judge = "vitest"                     # pytest, vitest, playwright, tsc

    [[mutation]]
    name = "꺼짐을 깨짐 앞에"
    runner = "pytest"                    # 선택. 기본은 내장 pytest(-q -p no:cacheprovider)
    tests = ["tests/core/test_run.py"]   # 명령 뒤에 붙는다. -k(pytest), -t(vitest)로 좁힌다
    expect = "red"                       # red, green, 또는 unhandled(vitest 판정만)
    repeat = 1                           # 선택. 매번 기대와 같아야 한다
    # diagnostic_in = "clients.test-d.ts"   tsc 판정이면 반드시. 빨강이 날 파일
    # restore = ["web/gen/openapi.ts"]      선택. 명령이 고쳐 쓸 수 있어 되돌릴 파일

    [[mutation.edit]]                    # 여럿이면 차례로 들어간다
    file = "src/agent_os/core/run.py"    # 저장소 루트 기준
    old = '''
        servers = _resolve_servers(plugins, manifest)
        _reject_masked_approvals(manifest, servers)
        _reject_disabled(plugins.read_disabled(), manifest)
    '''
    new = '''
        _reject_disabled(plugins.read_disabled(), manifest)
        servers = _resolve_servers(plugins, manifest)
        _reject_masked_approvals(manifest, servers)
    '''

판정(`judge`). 종료 코드만으로는 빨강과 오류를 가를 수 없는 명령이 있어 판정마다 출력의 요약을
읽는다. 오류는 기대가 무엇이든 어긋남이다 — 문법 오류로 모든 것이 빨간 변이는 테스트의 이빨을 재지
않는다.
- pytest: 종료 코드 0 은 초록, 1 은 빨강, 나머지(수집 오류, 없는 경로, 선택된 테스트 없음)는 오류다.
  0 이어도 skip 이 섞였으면 오류다. 재지 않은 테스트가 있다(원칙 II).
- vitest: 종료 코드가 실패, 수집 오류, 처리하지 않은 에러에 모두 1 이다. 요약의 `Tests` 줄에 실패가
  셀 때만 빨강이고, 파일 단위의 FAIL(`[ 파일 ]` 로 끝나는 줄, 수집 오류)이 하나라도 있으면 오류다.
  실패 없이 `Errors` 줄만 있으면 처리하지 않은 에러(unhandled)다. 가드가 막는 것이 그것뿐인 변이는
  그것을 기대로 적는다. 초록은 통과한 테스트가 하나 이상일 때다.
- playwright: 요약에 `N failed` 가 셀 때만 빨강이다. 초록은 종료 코드 0 에 통과가 있고 skip 이 없을
  때다.
- tsc: 종료 코드가 문법 오류와 타입 에러에 같고(2) 오류 번호로도 가를 수 없다(`satisfies` 의
  어긋남이 TS1360 이다). 빨강은 `diagnostic_in` 파일에서 난 진단이고, 그 파일 밖에서만 나면 오류다.
  `diagnostic_in` 은 진단 경로의 꼬리로 맞춘다. 이름만 적으면 다른 디렉터리의 같은 이름
  (`index.ts`)도 맞으니, 이름이 겹치면 디렉터리까지 적는다.

하는 일, 차례대로:
1. 변이 파일의 모양과 러너·판정의 짝을 보고, 변이마다 원문이 파일에 정확히 한 번 있는지, 러너의
   자리와 되돌릴 파일이 저장소 안에 있는지 본다. 하나라도 틀리면 아무 파일도 쓰지 않고 끝낸다.
2. 러너와 인자의 짝마다 변이 없이 한 번씩 돌린다(기준선). 초록이 아니면 변이를 넣지 않는다. 기준선이
   빨간데 변이가 빨가면 그 빨강은 아무것도 말하지 않는다. 이름으로 좁힌 선택이 비었는지도 여기서
   본다.
3. 변이마다 원래 바이트(되돌릴 파일 포함)를 쥐고 변이를 넣어 돌린 뒤 `finally` 에서 그 바이트를
   그대로 쓴다. 쓰기 전에 편집한 파일이 쓴 변이 바이트 그대로인지 본다. 다르면 변이가 든 동안 다른
   쓰기(편집기, 다른 세션)가 들어온 것이라 덮지 않고 알린다(대기열 77). 되돌릴 파일(`restore`)은
   명령이 고쳐 쓰는 파일이라 보지 않고 쓴다.
4. 종료 코드: 모두 기대대로면 0, 어긋나거나 기준선이 초록이 아니면 1, 변이 파일을 읽지 못했거나
   틀렸으면 2(아무 파일도 쓰지 않았다), 테스트를 돌리지 못했거나 되돌리지 못했으면 3.

제자리가 아닌 실행. 변이는 이 도구가 든 체크아웃을 고친다. 도는 동안(web 변이 수십 개는 40분이
넘는다) 그 체크아웃을 고치거나 소스를 읽는 리뷰를 띄우면 변이된 소스를 본다. 그래서 잴 코드를
커밋하고 다른 워크트리에서 그 워크트리의 도구로 돌린다. 변이 파일은 어느 경로여도 되고 편집의 `file`
은 도는 도구가 든 체크아웃 기준이다. pnpm 은 저장소(store)에서 링크만 해 네트워크를 타지
않는다(2026-10-01 13초, 일지 2026-10-01-01). `.env` 는 추적하지 않으므로 LLM 변이면 새 워크트리에
복사한다. 변이가 끝나면 지우는 워크트리라 사본이 남지 않는다. 남겨 두고 일하는 워크트리는 사본을
만들지 않고 `--env-file` 로 주 체크아웃의 것을 읽는다(operations.md LLM 테스트). 에이전트의
명령 상한(10분)을 넘는 실행은 백그라운드로 돌린다. 도는 동안 변이한 파일을 고치면(되돌릴 파일로
적지 않았으면) 되돌림이 그 파일을 덮지 않고 3으로 멈추고, 변이는 손으로 걷어 낸다.

    git worktree add --detach <임시 경로> HEAD
    (그 경로에서) uv sync
    (그 경로에서) pnpm -C web install --frozen-lockfile --offline    # web 변이일 때
    (그 경로에서) PYTHONUTF8=1 uv run python tools/mutate.py <변이 파일>
    git worktree remove <임시 경로>

바이트코드 캐시는 소스의 수정 시각(초)과 크기로만 맞춰 보므로, 크기가 같은 변이가 같은 초에 쓰이면
낡은 캐시가 돈다. 그래서 변이를 쓴 직후와 되돌린 직후에 그 소스의 `__pycache__/<이름>.*.pyc`(CPython
의 것과 pytest assertion rewrite 의 것)를 지우고, 하위 명령은 `PYTHONDONTWRITEBYTECODE=1` 로 돌아
변이된 소스의 캐시를 새로 남기지 않는다. `-p no:cacheprovider` 는 변이의 실패가 `.pytest_cache` 의
lastfailed 에 남지 않게 한다.

못 보는 것: 프로세스가 강제로 죽으면(`finally` 가 돌지 않으면) 되돌리지 못한다. 되돌리는 쓰기가
실패하거나(파일이 잠겼다) 다른 쓰기가 들어왔으면 나머지 파일은 되돌리고 남은 파일을 알린다. 세 경우
모두 `git diff` 로 본다. 되돌릴 파일(`restore`, 편집한 파일을 함께 적은 것 포함)에 든 다른 쓰기는
명령의 쓰기와 가를 수 없어 덮는다. 편집한 파일을 읽은 뒤 쓰기까지의 틈에 든 쓰기도 덮는다. 틈은
다음과 같다.
- 원래 바이트를 읽고 변이를 쓰기까지.
- 되돌리기 전에 읽어 보고 다시 쓰기까지.
- 앞 파일의 변이 쓰기가 실패해 변이를 쓰지 못한 파일이면, 처음 읽은 뒤 되돌리기까지. 쓴 변이
  바이트가 없어 보지 않는다.

원문의 줄 끝은 파일과 같아야 한다 — 변이 파일의 `\\n` 은 CRLF 파일에서 맞지 않는다. vitest 의 skip
은 세지 않는다. `-t` 로 좁히면 고르지 않은 테스트가 skipped 로 세어져 `it.skip` 과 가를 수 없다. tsc
의 빨강은 진단이 난 파일만 본다. 변이가 낸 문법 오류가 적은 파일까지 번져도 빨강이다. 윈도우에서
`pnpm.CMD` 같은 배치 파일은 cmd.exe 가 돌려 인자의 `&`·`%`·`^` 가 해석될 수 있다. 좁힌 선택이 비면
기준선이 오류로 잡는다(통과가 없다).

판정은 출력의 요약 문구에 기댄다. 초록과 빨강을 읽는 문구(vitest 의 `Tests` 줄, playwright 의
`N passed`·`N failed`, tsc 의 진단 줄)가 도구의 판에서 바뀌면 오류로 기운다. 초록이나 빨강을
거르는 표지(vitest 파일 단위 FAIL 의 `[ 파일 ]`, pytest·playwright 의 `N skipped`)가 바뀌면 그것을
못 봐 수집 오류가 섞인 실패가 빨강으로, skip 이 섞인 통과가 초록으로 지나간다.
"""

from __future__ import annotations

import io
import os
import re
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

ROOT = Path(__file__).resolve().parent.parent

type Outcome = Literal["green", "red", "unhandled", "error"]
type JudgeName = Literal["pytest", "vitest", "playwright", "tsc"]

_LABELS: dict[Outcome, str] = {
    "green": "초록",
    "red": "빨강",
    "unhandled": "처리하지 않은 에러",
    "error": "오류",
}
_PYTEST_OUTCOMES: dict[int, Outcome] = {0: "green", 1: "red"}
_ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
_PYTEST_SKIPPED = re.compile(r"\b\d+ skipped\b")
_VITEST_SUMMARY = re.compile(r"^\s*(Test Files|Tests|Errors)\s+(.+?)\s*$", re.MULTILINE)
_VITEST_FAIL = re.compile(r"^\s*FAIL\s+(.+?)\s*$", re.MULTILINE)
_VITEST_FILE_LEVEL = re.compile(r"\[ .+ \]$")
_PLAYWRIGHT_COUNT = re.compile(
    r"^\s*(\d+) (passed|failed|skipped|flaky|interrupted|did not run)\b", re.MULTILINE
)
_PLAYWRIGHT_FAILED = re.compile(r"\s*\d+ failed\s*")
_TSC_DIAGNOSTIC = re.compile(r"(\S+)\((\d+),(\d+)\): error (TS\d+)")


class SpecError(Exception):
    """변이 파일을 읽지 못했거나 틀렸다. 아무 파일도 쓰기 전에 난다."""


class RestoreError(Exception):
    """변이를 되돌리지 못한 파일이 있다. 변이가 든 동안 다른 쓰기가 들어왔거나, 그 파일을 읽거나
    다시 쓰다가 `OSError` 가 났다."""


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class Edit(_Model):
    file: str
    old: str
    new: str


class RunnerSpec(_Model):
    command: list[str] = Field(min_length=1)
    cwd: str = "."
    judge: JudgeName


class Mutation(_Model):
    name: str
    runner: str = "pytest"
    tests: list[str] = Field(default_factory=list[str])
    expect: Literal["red", "green", "unhandled"]
    diagnostic_in: str | None = None
    restore: list[str] = Field(default_factory=list[str])
    repeat: int = Field(default=1, ge=1)
    edit: list[Edit] = Field(min_length=1)


class Spec(_Model):
    runner: dict[str, RunnerSpec] = Field(default_factory=dict[str, RunnerSpec])
    mutation: list[Mutation] = Field(min_length=1)


_BUILTIN: dict[str, RunnerSpec] = {
    "pytest": RunnerSpec(
        command=[sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], judge="pytest"
    )
}


@dataclass(frozen=True)
class CommandResult:
    """명령 한 번의 결과. 출력은 stdout 뒤에 stderr 를 이은 것이다."""

    exit_code: int
    output: str

    @property
    def plain(self) -> str:
        """색 코드를 벗긴 출력."""
        return _ANSI.sub("", self.output)


@dataclass(frozen=True)
class Verdict:
    """판정 하나. `failed` 는 빨간 테스트(tsc 면 진단)의 이름이다."""

    outcome: Outcome
    summary: str
    failed: tuple[str, ...] = ()


type Runner = Callable[[Sequence[str], Path], CommandResult]


def _last_line(text: str, exit_code: int) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    return lines[-1].strip("= ") if lines else f"출력 없음(종료 코드 {exit_code})"


def _count(pattern: str, text: str) -> int:
    found = re.search(pattern, text)
    return int(found.group(1)) if found else 0


def _judge_pytest(exit_code: int, text: str) -> Verdict:
    summary = _last_line(text, exit_code)
    failed = tuple(
        line.split(" ", 1)[1].split(" - ", 1)[0]
        for line in text.splitlines()
        if line.startswith(("FAILED ", "ERROR "))
    )
    outcome = _PYTEST_OUTCOMES.get(exit_code, "error")
    if outcome == "green" and _PYTEST_SKIPPED.search(summary):
        outcome = "error"
    return Verdict(outcome, summary, failed)


def _judge_vitest(exit_code: int, text: str) -> Verdict:
    lines = {m.group(1): m.group(2) for m in _VITEST_SUMMARY.finditer(text)}
    summary = ", ".join(f"{key} {value}" for key, value in lines.items())
    tests = lines.get("Tests", "")
    fails = tuple(m.group(1) for m in _VITEST_FAIL.finditer(text))
    outcome: Outcome
    if any(_VITEST_FILE_LEVEL.search(fail) for fail in fails):
        outcome = "error"
    elif exit_code == 0:
        outcome = "green" if _count(r"(\d+) passed", tests) > 0 else "error"
    elif _count(r"(\d+) failed", tests) > 0:
        outcome = "red"
    elif "Errors" in lines:
        outcome = "unhandled"
    else:
        outcome = "error"
    return Verdict(outcome, summary or _last_line(text, exit_code), fails)


def _playwright_failed(text: str) -> tuple[str, ...]:
    """요약의 `N failed` 아래에 들여 적힌 `[프로젝트] › …` 줄들."""
    titles: list[str] = []
    lines = text.splitlines()
    for at, line in enumerate(lines):
        if _PLAYWRIGHT_FAILED.fullmatch(line):
            for follow in lines[at + 1 :]:
                if not follow.strip().startswith("["):
                    break
                titles.append(follow.strip())
    return tuple(titles)


def _judge_playwright(exit_code: int, text: str) -> Verdict:
    counts: dict[str, int] = {}
    for m in _PLAYWRIGHT_COUNT.finditer(text):
        counts[m.group(2)] = counts.get(m.group(2), 0) + int(m.group(1))
    summary = ", ".join(f"{n} {word}" for word, n in counts.items())
    outcome: Outcome
    if exit_code == 0:
        passed = counts.get("passed", 0) > 0 and counts.get("skipped", 0) == 0
        outcome = "green" if passed else "error"
    else:
        outcome = "red" if counts.get("failed", 0) > 0 else "error"
    return Verdict(outcome, summary or _last_line(text, exit_code), _playwright_failed(text))


def _judge_tsc(exit_code: int, text: str, diagnostic_in: str | None) -> Verdict:
    if exit_code == 0:
        return Verdict("green", "진단 없음")
    diagnostics = [(m.group(1), m.group(0)) for m in _TSC_DIAGNOSTIC.finditer(text)]
    summary = f"진단 {len(diagnostics)}" if diagnostics else _last_line(text, exit_code)
    target = diagnostic_in or ""
    hit = any(path == target or path.endswith(f"/{target}") for path, _ in diagnostics)
    return Verdict("red" if hit else "error", summary, tuple(line for _, line in diagnostics))


def judge(kind: JudgeName, result: CommandResult, diagnostic_in: str | None = None) -> Verdict:
    """명령의 결과를 초록, 빨강, 처리하지 않은 에러, 오류로 가른다. 색 코드는 벗기고 읽는다."""
    text = result.plain
    match kind:
        case "pytest":
            return _judge_pytest(result.exit_code, text)
        case "vitest":
            return _judge_vitest(result.exit_code, text)
        case "playwright":
            return _judge_playwright(result.exit_code, text)
        case "tsc":
            return _judge_tsc(result.exit_code, text, diagnostic_in)


def _runners(spec: Spec) -> dict[str, RunnerSpec]:
    """내장 러너와 변이 파일의 러너 표."""
    return {**_BUILTIN, **spec.runner}


def _pairing_problems(spec: Spec) -> list[str]:
    """러너와 판정의 짝. 파일을 보지 않는다."""
    problems = [
        f"러너 이름 {name} 는 내장이다. 다른 이름을 쓴다"
        for name in spec.runner
        if name in _BUILTIN
    ]
    runners = _runners(spec)
    for m in spec.mutation:
        if m.runner not in runners:
            problems.append(f"{m.name}: 러너 {m.runner} 가 [runner.{m.runner}] 에 없다")
            continue
        kind = runners[m.runner].judge
        if kind == "tsc" and m.diagnostic_in is None:
            problems.append(f"{m.name}: tsc 판정은 diagnostic_in(빨강이 날 파일)이 있어야 한다")
        if kind != "tsc" and m.diagnostic_in is not None:
            problems.append(f"{m.name}: diagnostic_in 은 tsc 판정만 쓴다(이 러너는 {kind})")
        if m.expect == "unhandled" and kind != "vitest":
            problems.append(f"{m.name}: expect unhandled 는 vitest 판정만 쓴다(이 러너는 {kind})")
    return problems


def load_spec(text: str) -> Spec:
    try:
        spec = Spec.model_validate(tomllib.loads(text))
    except (tomllib.TOMLDecodeError, ValidationError) as error:
        raise SpecError(str(error)) from error
    names = [m.name for m in spec.mutation]
    repeated = sorted({name for name in names if names.count(name) > 1})
    if repeated:
        raise SpecError(f"이름이 겹친다: {', '.join(repeated)}. 이름으로 골라 다시 돌린다")
    problems = _pairing_problems(spec)
    if problems:
        raise SpecError("\n".join(problems))
    return spec


def read_spec(path: Path) -> Spec:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise SpecError(f"{path} 를 읽지 못했다: {error}") from error
    return load_spec(text)


def select(spec: Spec, names: Sequence[str]) -> Spec:
    """이름으로 고른다. 이름이 없으면 전부다. 러너 표는 그대로 둔다."""
    if not names:
        return spec
    known = {m.name for m in spec.mutation}
    unknown = [name for name in names if name not in known]
    if unknown:
        raise SpecError(f"변이 파일에 없는 이름: {', '.join(unknown)}")
    return Spec(runner=spec.runner, mutation=[m for m in spec.mutation if m.name in names])


def _inside(root: Path, relative: str) -> Path | None:
    """저장소 안이면 그 경로, 밖이면 None."""
    path = (root / relative).resolve()
    return path if path.is_relative_to(root.resolve()) else None


def _mutated(root: Path, mutation: Mutation) -> dict[Path, tuple[bytes, bytes]]:
    """파일마다 (원래 바이트, 변이된 바이트). 편집은 적힌 차례로 앞 편집의 결과 위에 들어간다."""
    files: dict[Path, tuple[bytes, bytes]] = {}
    for edit in mutation.edit:
        path = _inside(root, edit.file)
        if path is None:
            raise SpecError(f"{mutation.name}: {edit.file} 는 저장소 밖이다")
        if path not in files:
            try:
                data = path.read_bytes()
            except OSError as error:
                raise SpecError(f"{mutation.name}: {edit.file} 를 읽지 못했다: {error}") from error
            files[path] = (data, data)
        original, current = files[path]
        old = edit.old.encode("utf-8")
        count = current.count(old)
        if count != 1:
            raise SpecError(
                f"{mutation.name}: {edit.file} 에 원문이 {count}번 있다. 정확히 한 번이어야 한다"
                " (줄 끝과 들여쓰기까지 바이트로 맞춘다)"
            )
        files[path] = (original, current.replace(old, edit.new.encode("utf-8")))
    return files


def _file_problems(root: Path, spec: Spec) -> list[str]:
    """고른 변이의 원문, 그 변이들이 쓰는 러너의 자리, 되돌릴 파일. 아무 파일도 쓰지 않는다."""
    problems: list[str] = []
    for name in sorted({m.runner for m in spec.mutation} & spec.runner.keys()):
        where = _inside(root, spec.runner[name].cwd)
        if where is None or not where.is_dir():
            problems.append(
                f"러너 {name}: 자리 {spec.runner[name].cwd} 가 저장소 안의 디렉터리가 아니다"
            )
    for mutation in spec.mutation:
        try:
            _mutated(root, mutation)
        except SpecError as error:
            problems.append(str(error))
        for relative in mutation.restore:
            path = _inside(root, relative)
            if path is None or not path.is_file():
                problems.append(f"{mutation.name}: 되돌릴 파일 {relative} 가 저장소 안에 없다")
    return problems


def _validate(root: Path, spec: Spec) -> None:
    problems = _file_problems(root, spec)
    if problems:
        raise SpecError("\n".join(problems))


def _drop_bytecode(path: Path) -> None:
    """그 소스의 바이트코드 캐시를 지운다. CPython 의 것과 pytest assertion rewrite 의 것이다."""
    for cached in path.parent.glob(f"__pycache__/{path.stem}.*.pyc"):
        cached.unlink(missing_ok=True)


def _invoke(
    root: Path, spec: Spec, name: str, tests: Sequence[str], runner: Runner
) -> CommandResult:
    command = _runners(spec)[name]
    return runner([*command.command, *tests], root / command.cwd)


class _WrittenMeanwhile(Exception):
    """변이가 든 동안 다른 쓰기가 들어와, 파일이 쓴 변이 바이트가 아니다."""


def _restore_file(path: Path, original: bytes, written: bytes | None) -> None:
    """원래 바이트를 되쓴다. 쓴 변이 바이트(`written`)가 있는데 파일이 그것과 다르면 덮지 않고
    `_WrittenMeanwhile`."""
    if written is not None and path.read_bytes() != written:
        raise _WrittenMeanwhile
    path.write_bytes(original)
    _drop_bytecode(path)


def _restore(root: Path, name: str, held: dict[Path, bytes], written: dict[Path, bytes]) -> None:
    """쥔 파일을 모두 되쓰고, 남은 파일이 있으면 그 뒤에 `RestoreError`."""
    stuck: list[str] = []
    for path, original in held.items():
        relative = path.relative_to(root.resolve()).as_posix()
        try:
            _restore_file(path, original, written.get(path))
        except _WrittenMeanwhile:
            stuck.append(f"{relative} (변이가 든 동안 다른 쓰기가 들어와 덮지 않았다)")
        except OSError as error:
            stuck.append(f"{relative} ({error})")
    if stuck:
        raise RestoreError(f"{name}: {', '.join(stuck)}")


def _run_mutated(root: Path, spec: Spec, mutation: Mutation, runner: Runner) -> list[CommandResult]:
    files = _mutated(root, mutation)
    rewritable = [(root / relative).resolve() for relative in mutation.restore]
    held = {path: original for path, (original, _) in files.items()}
    for path in rewritable:
        held.setdefault(path, path.read_bytes())
    written: dict[Path, bytes] = {}  # 쓰기가 끝난 변이 바이트. 되돌릴 파일은 넣지 않는다
    try:
        for path, (_, mutated) in files.items():
            path.write_bytes(mutated)
            _drop_bytecode(path)
            if path not in rewritable:
                written[path] = mutated
        return [
            _invoke(root, spec, mutation.runner, mutation.tests, runner)
            for _ in range(mutation.repeat)
        ]
    finally:
        _restore(root, mutation.name, held, written)


def _details(judged: Sequence[tuple[CommandResult, Verdict]], out: Callable[[str], None]) -> None:
    """빨간 테스트의 이름, 그리고 빨강도 초록도 아니면 출력의 끝."""
    for name in dict.fromkeys(name for _, verdict in judged for name in verdict.failed):
        out(f"   {name}")
    for result, verdict in judged:
        if verdict.outcome in ("error", "unhandled"):
            for line in result.plain.splitlines()[-10:]:
                out(f"   | {line}")


def check(spec: Spec, *, root: Path, out: Callable[[str], None]) -> int:
    """원문만 본다. 명령을 돌리지 않는다. 모두 맞으면 0, 하나라도 틀리면 틀린 것을 모두 알리고 2."""
    problems = _file_problems(root, spec)
    for problem in problems:
        out(f"!! {problem}")
    if problems:
        out(f"원문 확인: 변이 {len(spec.mutation)} 중 문제 {len(problems)}")
        return 2
    out(f"원문 확인: 변이 {len(spec.mutation)} 모두 원문이 한 번씩 있다")
    return 0


def measure(spec: Spec, *, root: Path, runner: Runner, out: Callable[[str], None]) -> int:
    """기준선을 재고 변이를 하나씩 넣어 돌린다. 모두 기대대로면 0, 아니면 1."""
    _validate(root, spec)

    baseline_green = True
    for name, tests in dict.fromkeys((m.runner, tuple(m.tests)) for m in spec.mutation):
        result = _invoke(root, spec, name, tests, runner)
        verdict = judge(_runners(spec)[name].judge, result)
        out(f"기준선 {' '.join((name, *tests))}: {_LABELS[verdict.outcome]} — {verdict.summary}")
        if verdict.outcome != "green":
            _details([(result, verdict)], out)
            baseline_green = False
    if not baseline_green:
        out("기준선이 초록이 아니라 변이를 넣지 않았다. 빨간 기준선 위의 빨강은 재는 것이 없다")
        return 1

    mismatched: list[str] = []
    for mutation in spec.mutation:
        kind = _runners(spec)[mutation.runner].judge
        results = _run_mutated(root, spec, mutation, runner)
        judged = [(result, judge(kind, result, mutation.diagnostic_in)) for result in results]
        outcomes = ", ".join(_LABELS[verdict.outcome] for _, verdict in judged)
        matched = all(verdict.outcome == mutation.expect for _, verdict in judged)
        head = "==" if matched else "!! 어긋남 —"
        out(
            f"{head} {mutation.name}: 기대 {_LABELS[mutation.expect]}, 결과 {outcomes}"
            f" — {judged[-1][1].summary}"
        )
        _details(judged, out)
        if not matched:
            mismatched.append(mutation.name)

    if mismatched:
        out(f"변이 {len(spec.mutation)} 중 어긋남 {len(mismatched)}: {', '.join(mismatched)}")
        return 1
    out(f"변이 {len(spec.mutation)} 모두 기대대로")
    return 0


def run_command(argv: Sequence[str], cwd: Path) -> CommandResult:
    """셸을 거치지 않는다. 윈도우의 `pnpm.CMD` 처럼 PATHEXT 로 찾는 이름은 `shutil.which` 가 풀고,
    그런 배치 파일은 cmd.exe 가 돌린다(독스트링의 못 보는 것)."""
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}
    completed = subprocess.run(
        [shutil.which(argv[0]) or argv[0], *argv[1:]],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return CommandResult(completed.returncode, completed.stdout + completed.stderr)


def _check_files(paths: Sequence[str], *, root: Path, out: Callable[[str], None]) -> int:
    """변이 파일 여럿의 원문을 본다. 줄마다 앞에 그 파일의 경로를 붙이고, 읽지 못한 파일이 있어도
    나머지를 본다. 모두 맞으면 0, 하나라도 틀리면 2."""
    code = 0
    for path in paths:
        lines: list[str] = []
        try:
            code = max(code, check(read_spec(Path(path)), root=root, out=lines.append))
        except SpecError as error:
            lines.append(f"!! 변이 파일 오류: {error}")
            code = 2
        # 변이 파일 오류는 문제를 줄바꿈으로 잇는다. 줄마다 붙여야 둘째 줄의 출처가 보인다
        for line in "\n".join(lines).splitlines():
            out(f"{path}: {line}")
    return code


def main(
    argv: Sequence[str],
    *,
    root: Path = ROOT,
    runner: Runner = run_command,
    out: Callable[[str], None] = print,
) -> int:
    checking = "--check" in argv
    rest = [arg for arg in argv if arg != "--check"]
    flags = [arg for arg in rest if arg.startswith("--")]
    if flags:
        out(f"모르는 선택: {', '.join(flags)}. 아는 것은 --check 하나다")
        return 2
    if not rest:
        out(__doc__ or "")
        return 2
    spec_path, *names = rest
    more_tables = [name for name in names if name.endswith(".toml")]
    if more_tables and (not checking or len(more_tables) != len(names)):
        out("변이 파일 여럿은 --check 로만 받고 이름과 섞지 않는다. 변이는 표 하나씩 돌린다")
        return 2
    if checking and len(more_tables) == len(names):
        return _check_files([spec_path, *more_tables], root=root, out=out)
    try:
        spec = select(read_spec(Path(spec_path)), names)
        if checking:
            return check(spec, root=root, out=out)
        return measure(spec, root=root, runner=runner, out=out)
    except SpecError as error:
        out(f"변이 파일 오류(아무 파일도 쓰지 않았다): {error}")
        return 2
    except RestoreError as error:
        out(f"되돌리지 못했다. 남은 파일을 git diff 로 보고 변이만 걷어 낸다: {error}")
        if error.__context__ is not None:  # finally 에서 던져 가린, 그 전에 난 예외
            out(f"되돌리기 전에 난 예외: {error.__context__!r}")
        return 3
    except OSError as error:
        out(f"테스트를 돌리지 못했다(변이는 되돌렸다): {error}")
        return 3


if __name__ == "__main__":
    # pre-commit 훅 환경에 PYTHONUTF8 이 있다고 가정하지 않는다. 없으면 윈도우의 파이프는 cp949 다.
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8")
    raise SystemExit(main(sys.argv[1:]))
