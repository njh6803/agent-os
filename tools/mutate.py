"""바이트 그대로 되돌리는 변이 도구.

테스트가 무엇을 재는지 변이로 본다. 구현 전부터 초록인 가드, 구현 뒤에 쓴 테스트, 새 검사가 그
대상이다. 세션마다 스크래치에 변이 스크립트를 새로 짓다가 같은 함정을 두 번 밟아서 여기 있다(대기열
29). 텍스트로 되돌려 줄 끝이 CRLF 가 됐고, 기대 결과를 받지 않아 아무것도 재지 않은 변이가 초록으로
지나갔다.

사용: PYTHONUTF8=1 uv run python tools/mutate.py <변이 파일.toml> [이름 ...]
LLM 테스트가 대상이면 `PYTHONUTF8=1 uv run --env-file .env python tools/mutate.py …` 이고 tests 에
`-m llm` 을 넣는다. 이름을 주면 그 변이만 돈다.

변이 파일은 TOML 이다. 원문은 리터럴 여러 줄 문자열(`'''`)로 적으면 이스케이프가 없다. 여는 `'''`
바로 뒤의 줄바꿈은 TOML 이 버린다. 아래 예시는 네 칸 들여쓴 채라 옮길 때 그 네 칸을 걷어 낸다.

    [[mutation]]
    name = "꺼짐을 깨짐 앞에"
    tests = ["tests/core/test_run.py"]   # pytest 인자 그대로다. -k, -m 도 된다
    expect = "red"                       # red 또는 green
    repeat = 1                           # 선택. 매번 기대와 같아야 한다

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

하는 일, 차례대로:
1. 변이마다 원문이 파일에 정확히 한 번 있는지 본다. 하나라도 틀리면 아무 파일도 쓰지 않고 끝낸다.
2. 대상 테스트를 변이 없이 한 번씩 돌린다(기준선). 초록이 아니면 변이를 넣지 않는다. 기준선이
   빨간데 변이가 빨가면 그 빨강은 아무것도 말하지 않는다.
3. 변이마다 원래 바이트를 쥐고 변이를 넣어 돌린 뒤 `finally` 에서 그 바이트를 그대로 쓴다.
4. pytest 종료 코드 0 은 초록, 1 은 빨강, 나머지(수집 오류, 없는 경로, 선택된 테스트 없음)는
   오류다. 오류는 기대가 무엇이든 어긋남이다 — 문법 오류로 모든 것이 빨간 변이는 테스트의 이빨을
   재지 않는다. 종료 코드가 0 이어도 skip 이 섞였으면 오류다. 재지 않은 테스트가 있다(원칙 II).
5. 종료 코드: 모두 기대대로면 0, 어긋나거나 기준선이 초록이 아니면 1, 변이 파일을 읽지 못했거나
   틀렸으면 2(아무 파일도 쓰지 않았다), 테스트를 돌리지 못했거나 되돌리지 못했으면 3.

하위 pytest 는 `PYTHONDONTWRITEBYTECODE=1` 로 돈다. 변이된 소스의 `.pyc` 가 남으면 되돌린 원본과
크기와 수정 시각이 겹칠 때 낡은 바이트코드가 쓰인다. `-p no:cacheprovider` 는 변이의 실패가
`.pytest_cache` 의 lastfailed 에 남지 않게 한다.

못 보는 것: 프로세스가 강제로 죽으면(`finally` 가 돌지 않으면) 되돌리지 못한다. 되돌리는 쓰기가
실패하면(파일이 잠겼다) 나머지 파일은 되돌리고 남은 파일을 알린다. 두 경우 모두 `git diff` 로 본다.
원문의 줄 끝은 파일과 같아야 한다 — 변이 파일의 `\\n` 은 CRLF 파일에서 맞지 않는다.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tomllib
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

ROOT = Path(__file__).resolve().parent.parent

type Outcome = Literal["green", "red", "error"]

_OUTCOMES: dict[int, Outcome] = {0: "green", 1: "red"}
_LABELS: dict[Outcome, str] = {"green": "초록", "red": "빨강", "error": "오류"}
_SKIPPED = re.compile(r"\b\d+ skipped\b")


class SpecError(Exception):
    """변이 파일을 읽지 못했거나 틀렸다. 아무 파일도 쓰기 전에 난다."""


class RestoreError(Exception):
    """변이를 되돌리지 못한 파일이 있다. 그 파일은 변이된 채 남았다."""


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class Edit(_Model):
    file: str
    old: str
    new: str


class Mutation(_Model):
    name: str
    tests: list[str]
    expect: Literal["red", "green"]
    repeat: int = Field(default=1, ge=1)
    edit: list[Edit] = Field(min_length=1)


class Spec(_Model):
    mutation: list[Mutation] = Field(min_length=1)


@dataclass(frozen=True)
class PytestResult:
    """pytest 한 번의 결과."""

    exit_code: int
    output: str

    @property
    def outcome(self) -> Outcome:
        outcome = _OUTCOMES.get(self.exit_code, "error")
        if outcome == "green" and _SKIPPED.search(self.summary):
            return "error"
        return outcome

    @property
    def failed(self) -> list[str]:
        """빨간 테스트의 노드 아이디. `-q` 의 짧은 요약 줄(`FAILED …`, `ERROR …`)에서 읽는다."""
        return [
            line.split(" ", 1)[1].split(" - ", 1)[0]
            for line in self.output.splitlines()
            if line.startswith(("FAILED ", "ERROR "))
        ]

    @property
    def summary(self) -> str:
        lines = [line for line in self.output.splitlines() if line.strip()]
        return lines[-1].strip("= ") if lines else f"출력 없음(종료 코드 {self.exit_code})"


type Runner = Callable[[Sequence[str]], PytestResult]


def load_spec(text: str) -> Spec:
    try:
        spec = Spec.model_validate(tomllib.loads(text))
    except (tomllib.TOMLDecodeError, ValidationError) as error:
        raise SpecError(str(error)) from error
    names = [m.name for m in spec.mutation]
    repeated = sorted({name for name in names if names.count(name) > 1})
    if repeated:
        raise SpecError(f"이름이 겹친다: {', '.join(repeated)}. 이름으로 골라 다시 돌린다")
    return spec


def read_spec(path: Path) -> Spec:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise SpecError(f"{path} 를 읽지 못했다: {error}") from error
    return load_spec(text)


def select(spec: Spec, names: Sequence[str]) -> Spec:
    """이름으로 고른다. 이름이 없으면 전부다."""
    if not names:
        return spec
    known = {m.name for m in spec.mutation}
    unknown = [name for name in names if name not in known]
    if unknown:
        raise SpecError(f"변이 파일에 없는 이름: {', '.join(unknown)}")
    return Spec(mutation=[m for m in spec.mutation if m.name in names])


def _mutated(root: Path, mutation: Mutation) -> dict[Path, tuple[bytes, bytes]]:
    """파일마다 (원래 바이트, 변이된 바이트). 편집은 적힌 차례로 앞 편집의 결과 위에 들어간다."""
    files: dict[Path, tuple[bytes, bytes]] = {}
    for edit in mutation.edit:
        path = (root / edit.file).resolve()
        if not path.is_relative_to(root.resolve()):
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


def _validate(root: Path, spec: Spec) -> None:
    """모든 변이의 원문을 파일에서 찾는다. 아무 파일도 쓰지 않는다."""
    for mutation in spec.mutation:
        _mutated(root, mutation)


def _run_mutated(root: Path, mutation: Mutation, runner: Runner) -> list[PytestResult]:
    files = _mutated(root, mutation)
    try:
        for path, (_, mutated) in files.items():
            path.write_bytes(mutated)
        return [runner(mutation.tests) for _ in range(mutation.repeat)]
    finally:
        stuck: list[str] = []
        for path, (original, _) in files.items():
            try:
                path.write_bytes(original)
            except OSError as error:
                stuck.append(f"{path.relative_to(root.resolve()).as_posix()} ({error})")
        if stuck:
            raise RestoreError(f"{mutation.name}: {', '.join(stuck)}")


def _details(results: Sequence[PytestResult], out: Callable[[str], None]) -> None:
    """빨간 테스트의 노드 아이디, 그리고 오류면 출력의 끝."""
    for nodeid in dict.fromkeys(nodeid for result in results for nodeid in result.failed):
        out(f"   {nodeid}")
    for result in results:
        if result.outcome == "error":
            for line in result.output.splitlines()[-10:]:
                out(f"   | {line}")


def measure(spec: Spec, *, root: Path, runner: Runner, out: Callable[[str], None]) -> int:
    """기준선을 재고 변이를 하나씩 넣어 돌린다. 모두 기대대로면 0, 아니면 1."""
    _validate(root, spec)

    baseline_green = True
    for tests in dict.fromkeys(tuple(m.tests) for m in spec.mutation):
        result = runner(tests)
        out(f"기준선 {' '.join(tests)}: {_LABELS[result.outcome]} — {result.summary}")
        if result.outcome != "green":
            _details([result], out)
            baseline_green = False
    if not baseline_green:
        out("기준선이 초록이 아니라 변이를 넣지 않았다. 빨간 기준선 위의 빨강은 재는 것이 없다")
        return 1

    mismatched: list[str] = []
    for mutation in spec.mutation:
        results = _run_mutated(root, mutation, runner)
        outcomes = ", ".join(_LABELS[result.outcome] for result in results)
        matched = all(result.outcome == mutation.expect for result in results)
        head = "==" if matched else "!! 어긋남 —"
        out(
            f"{head} {mutation.name}: 기대 {_LABELS[mutation.expect]}, 결과 {outcomes}"
            f" — {results[-1].summary}"
        )
        _details(results, out)
        if not matched:
            mismatched.append(mutation.name)

    if mismatched:
        out(f"변이 {len(spec.mutation)} 중 어긋남 {len(mismatched)}: {', '.join(mismatched)}")
        return 1
    out(f"변이 {len(spec.mutation)} 모두 기대대로")
    return 0


def run_pytest(args: Sequence[str]) -> PytestResult:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return PytestResult(completed.returncode, completed.stdout + completed.stderr)


def main(
    argv: Sequence[str],
    *,
    root: Path = ROOT,
    runner: Runner = run_pytest,
    out: Callable[[str], None] = print,
) -> int:
    if not argv:
        out(__doc__ or "")
        return 2
    spec_path, *names = argv
    try:
        spec = select(read_spec(Path(spec_path)), names)
        return measure(spec, root=root, runner=runner, out=out)
    except SpecError as error:
        out(f"변이 파일 오류(아무 파일도 쓰지 않았다): {error}")
        return 2
    except RestoreError as error:
        out(f"되돌리지 못했다. 변이된 채 남은 파일을 git diff 로 보고 되돌린다: {error}")
        return 3
    except OSError as error:
        out(f"테스트를 돌리지 못했다(변이는 되돌렸다): {error}")
        return 3


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
