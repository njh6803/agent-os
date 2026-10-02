"""tools/launch_hook.py — 훅 등록의 실행 래퍼(대기열 91).

래퍼 사본을 임시 디렉터리에 두고 그 옆에 손으로 지은 훅을 둔다. 래퍼는 자기 옆에서 훅을 찾으므로
사본은 이 저장소의 훅이 아니라 임시 훅을 돈다. 이 저장소의 훅을 래퍼로 도는 것은
tools/run_hooks.py 가 pre-commit 에서 잰다.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from tools.run_hooks import ROOT, hook_environment

LAUNCHER = ROOT / "tools" / "launch_hook.py"


def _돌린다(*argv: str, stdin: bytes = b"") -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, *argv],
        input=stdin,
        capture_output=True,
        env=hook_environment(),
        check=False,
        timeout=60,
    )


def _래퍼_사본을_둔다(directory: Path) -> str:
    launcher = directory / "launch_hook.py"
    shutil.copyfile(LAUNCHER, launcher)
    return str(launcher)


def test_훅_파일이_없으면_막지_않고_침묵으로_지나간다(tmp_path: Path) -> None:
    """옛 등록(`python <훅 경로>`)은 같은 자리에서 2로 끝났다. PreToolUse 에서 2는 막기다."""
    launcher = _래퍼_사본을_둔다(tmp_path)

    launched = _돌린다(launcher, "hook_없다.py", stdin=b'{"tool_name": "Bash"}')
    direct = _돌린다(str(tmp_path / "hook_없다.py"), stdin=b'{"tool_name": "Bash"}')

    assert launched.returncode == 0
    assert launched.stdout == b""
    assert direct.returncode == 2


def test_훅_이름이_없어도_지나간다(tmp_path: Path) -> None:
    """등록 모양이 틀린 것이다. 그것은 tools/run_hooks.py 의 대조가 잡고, 세션은 막지 않는다."""
    launched = _돌린다(_래퍼_사본을_둔다(tmp_path))

    assert launched.returncode == 0
    assert launched.stdout == b""


def test_훅의_종료_코드와_stdin_stdout_stderr_는_그대로다(tmp_path: Path) -> None:
    (tmp_path / "hook_막는다.py").write_text(
        "import sys\n"
        "sys.stdout.buffer.write(sys.stdin.buffer.read())\n"
        "sys.stderr.buffer.write('막은 이유'.encode('utf-8'))\n"
        "raise SystemExit(2)\n",
        encoding="utf-8",
    )
    payload = '{"tool_input": {"command": "한글 명령"}}'.encode()

    launched = _돌린다(_래퍼_사본을_둔다(tmp_path), "hook_막는다.py", stdin=payload)

    assert launched.returncode == 2
    assert launched.stdout == payload
    assert launched.stderr.decode("utf-8") == "막은 이유"


def test_훅_안의_예외는_바로_돌릴_때처럼_1이다(tmp_path: Path) -> None:
    """PreToolUse 에서 1은 막지 않는 오류다. 래퍼가 이것을 2로 바꾸거나 삼키지 않는다."""
    (tmp_path / "hook_깨진다.py").write_text("raise RuntimeError('버그')\n", encoding="utf-8")

    launched = _돌린다(_래퍼_사본을_둔다(tmp_path), "hook_깨진다.py")

    assert launched.returncode == 1
    assert b"RuntimeError" in launched.stderr


def test_훅은_바로_돌릴_때와_같은_이름과_인자와_경로를_본다(tmp_path: Path) -> None:
    hook = tmp_path / "hook_본다.py"
    hook.write_text(
        "import json, sys\n"
        "print(json.dumps({'name': __name__, 'argv': sys.argv, 'file': __file__,"
        " 'path0': sys.path[0]}))\n",
        encoding="utf-8",
    )

    launched = _돌린다(_래퍼_사본을_둔다(tmp_path), "hook_본다.py")
    seen = json.loads(launched.stdout)

    assert launched.returncode == 0
    assert seen["name"] == "__main__"
    assert [Path(arg).resolve() for arg in seen["argv"]] == [hook.resolve()]
    assert Path(seen["file"]).resolve() == hook.resolve()
    assert Path(seen["path0"]).resolve() == tmp_path.resolve()
