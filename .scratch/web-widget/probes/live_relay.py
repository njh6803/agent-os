"""core 가 모델·도구 호출 중의 이벤트를 바로 내보내게 바꾼 시제품(`live_relay.patch`)을 잰다.

web-widget 명세의 "실시간 중계" 절의 근거다. 시제품은 에이전트를 제 태스크에서 돌리고, 컨텍스트가
모델·도구 호출을 기록하는 자리에서 몸통을 깨워 그 이벤트를 흘리게 한 뒤 몸통이 다음을 청할 때까지
기다린다(맞물림). 이벤트는 컨텍스트의 줄에 남고 몸통이 꺼낸다. 패치는 `BASE` 커밋에 대한 것이고 그
커밋의 `core/run.py` 와 `tests/core/test_run.py` 를 고친다. 테스트의 고침은 "에이전트의 정리 코드가
`run()` 을 부른 태스크에서 돈다" 는 단언을 "에이전트를 돌린 그 태스크에서 돈다" 로 바꾼 것 하나다.

작업 트리가 아니라 `BASE` 를 `git archive` 로 꺼낸 사본 둘(그대로, 패치를 댄 것)을 임시 폴더에
두고, 그 사본의 `src` 를 `PYTHONPATH` 앞에 세워 잰다. 같은 브랜치가 core 를 고쳐도 근거가 흔들리지
않게 하기 위해서다. 재는 것은 넷이다.

- 시각. `event_timing.py`(이 폴더)를 두 사본에서 돌린다. 갈래 넷의 판정을 견준다.
- 기존 시험. 패치를 댄 사본에서 `tests/core`, `tests/channel`, `tests/adapters/test_mcp.py` 를
  돌린다.
- 실패 다시 돌리기. 기존 시험에서 실패한 것이 있을 때만 돈다. 그 시험만 두 사본에서 다시 돌려,
  패치가 깬 것인지 그 회차의 환경 때문인지 가른다. 다른 세션이 CPU 를 88% 쓰던 2026-10-23 의 첫
  실행에서 `tests/channel/cli/test_interrupt.py` 의 Ctrl+C 시험 둘이 30초 상한을 넘겨 실패했고, 그
  시험의 자식 프로세스는 `core/run.py` 를 import 하지 않는다(어댑터가 `core/ports.py` 만 부른다).
- 실제 MCP. 패치를 댄 사본에서 `.scratch/mcp-shutdown/probes/write_failure.py --expect closed` 를
  돌린다. 진짜 MCP 어댑터를 `run()` 에 물려, 에이전트 태스크에서 부른 도구와 트레이스 쓰기가 실패한
  실행의 닫기를 본다.

표지. 시각은 그 사본의 `core:` 줄이 그 사본의 `src` 를 가리키고 `측정 4회차, 측정 아님 0회차` 가
나온 것이다. 시험은 요약 줄이 있고 같은 환경의 파이썬이 `agent_os` 를 그 사본에서 읽는 것이다.
초록인지(`passed` 가 있고 `failed`·`error` 가 없다)는 표지가 아니라 결과다. 다시 돌리기도 두
사본마다 같은 표지를 본다. 실제 MCP 는 마지막 줄이 `{"unmeasured": [], "unexpected":
[]}` 이고 종료 코드가 0인 것이다. 표지가 없는 회차는 측정이 아니라 세고 종료 코드가 1이다.

쓰임: 저장소 루트에서 `uv run python .scratch/web-widget/probes/live_relay.py`. 기존 시험이 이
PC에서 홀로 2분 반쯤, 다른 세션과 겹친 첫 실행에서 9분 48초 걸렸다.
"""

from __future__ import annotations

import io
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tools.probe_kit import Rounds  # noqa: E402

BASE = "934f8dfa334ac060bb224619522d602bed3b5e5e"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PATCH = HERE / "live_relay.patch"
TIMING = HERE / "event_timing.py"
WRITE_FAILURE = ".scratch/mcp-shutdown/probes/write_failure.py"
ARCHIVED = ("src", "tests", "tools", "plugins", "pyproject.toml", WRITE_FAILURE)
SUITE = ("tests/core", "tests/channel", "tests/adapters/test_mcp.py")
MEASURED = "측정 4회차, 측정 아님 0회차"
MCP_CLEAN = '{"unmeasured": [], "unexpected": []}'


def _extract(into: Path) -> None:
    archive = subprocess.run(
        ["git", "-C", str(ROOT), "archive", "--format=tar", BASE, *ARCHIVED],
        capture_output=True,
        check=True,
    )
    with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
        tar.extractall(into, filter="data")


def _env(tree: Path) -> dict[str, str]:
    return {**os.environ, "PYTHONPATH": str(tree / "src"), "PYTHONIOENCODING": "utf-8"}


def _run(command: list[str], tree: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=tree,
        env=_env(tree),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _imports_from(tree: Path) -> bool:
    probe = _run([sys.executable, "-c", "import agent_os.core.run as r; print(r.__file__)"], tree)
    return Path(probe.stdout.strip()).resolve() == (tree / "src/agent_os/core/run.py").resolve()


def _timing(tree: Path, rounds: Rounds, label: str) -> None:
    with rounds.round(f"시각 {label}") as current:
        done = _run([sys.executable, str(TIMING)], tree)
        print(f"--- 시각 {label} (종료 {done.returncode})\n{done.stdout}{done.stderr}")
        core = (tree / "src/agent_os/core/run.py").resolve()
        own = f"core: {core}" in done.stdout
        if not own or MEASURED not in done.stdout or done.returncode != 0:
            current.mark(measured=False, result="그 사본의 core 를 네 갈래 모두 재지 못했다")
            return
        # 갈래마다 도착 줄(`@` 가 든다)과 판정 줄이 나온다. 판정 줄만 모은다.
        verdicts = [
            line for line in done.stdout.splitlines() if "갈래: " in line and "@" not in line
        ]
        current.mark(measured=True, result=" / ".join(verdicts))


def _pytest(tree: Path, targets: list[str]) -> tuple[subprocess.CompletedProcess[str], str]:
    done = _run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *targets], tree)
    summary = done.stdout.strip().splitlines()[-1] if done.stdout.strip() else ""
    return done, summary


def _green(summary: str) -> bool:
    return "passed" in summary and "failed" not in summary and "error" not in summary


def _failed_ids(output: str) -> list[str]:
    """요약의 `FAILED <노드> - <메시지>` 줄에서 노드를 꺼낸다. `ERROR` 줄은 다시 돌리지 않는다."""
    return [
        line.removeprefix("FAILED ").split(" - ")[0]
        for line in output.splitlines()
        if line.startswith("FAILED ")
    ]


def _suite(tree: Path, rounds: Rounds) -> list[str]:
    """패치를 댄 사본에서 기존 시험을 돌리고 실패한 노드를 돌려준다."""
    with rounds.round("기존 시험") as current:
        done, summary = _pytest(tree, list(SUITE))
        print(f"--- 기존 시험 (종료 {done.returncode})\n{summary}")
        if not _imports_from(tree) or not summary:
            current.mark(measured=False, result="그 사본의 agent_os 로 시험을 돌리지 못했다")
            return []
        if not _green(summary):
            print(done.stdout[-6000:])
        current.mark(measured=True, result=f"{summary} (초록={_green(summary)})")
        return _failed_ids(done.stdout)
    return []


def _rerun(base: Path, patched: Path, failed: list[str], rounds: Rounds) -> None:
    """패치를 댄 사본에서 실패한 시험을 두 사본에서 다시 돌린다. 원래 사본에서도 실패하면 패치가
    아니라 그 회차의 환경(다른 세션의 부하, 사본) 때문이라는 해석이고, 원래 사본에서 지나고 패치를
    댄 사본에서 다시 실패하면 패치가 깬 것이라는 해석이다."""
    with rounds.round("실패 다시 돌리기") as current:
        verdicts: list[str] = []
        for tree, label in ((base, "바꾸기 전"), (patched, "바꾼 뒤")):
            done, summary = _pytest(tree, failed)
            print(f"--- 실패 다시 돌리기 {label} (종료 {done.returncode})\n{summary}")
            if not _imports_from(tree) or not summary:
                current.mark(measured=False, result=f"{label} 사본으로 시험을 돌리지 못했다")
                return
            verdicts.append(f"{label}: {summary}")
        current.mark(measured=True, result=" / ".join(verdicts))


def _mcp(tree: Path, rounds: Rounds) -> None:
    with rounds.round("실제 MCP") as current:
        done = _run([sys.executable, WRITE_FAILURE, "--expect", "closed"], tree)
        lines = done.stdout.strip().splitlines()
        print(f"--- 실제 MCP (종료 {done.returncode})\n{done.stdout}")
        if not _imports_from(tree) or not lines or lines[-1] != MCP_CLEAN:
            current.mark(measured=False, result="네 사례를 기대대로 재지 못했다")
            return
        current.mark(measured=True, result=f"네 사례가 기대대로 끝났다(종료 {done.returncode})")


def main() -> int:
    rounds = Rounds()
    with tempfile.TemporaryDirectory(prefix="live-relay-", ignore_cleanup_errors=True) as temp:
        base, patched = Path(temp) / "base", Path(temp) / "patched"
        _extract(base)
        _extract(patched)
        applied = subprocess.run(
            ["git", "apply", str(PATCH)], cwd=patched, capture_output=True, text=True, check=False
        )
        if applied.returncode != 0:
            print(f"패치를 대지 못했다: {applied.stderr}")
            return 1
        _timing(base, rounds, "바꾸기 전")
        _timing(patched, rounds, "바꾼 뒤")
        failed = _suite(patched, rounds)
        if failed:
            _rerun(base, patched, failed, rounds)
        _mcp(patched, rounds)
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    sys.exit(main())
