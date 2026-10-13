"""tools/model_sweep.py 검증. 종류, 갈래, 기간과 CLI.

갈래의 기대값은 해시를 다시 셈하지 않고, 스윕 프로브 사전 등록의 정의(이름의 UTF-8 바이트의 SHA-256
첫 바이트가 짝수면 기준)로 손으로 셈한 첫 바이트를 적었다(2026-10-13, `hashlib`).
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

import pytest
from tools.model_sweep import (
    ARMS,
    BASE,
    COMPARISON,
    END,
    OUTSIDE,
    SWEPT,
    arm,
    assign,
    kind,
    main,
    prereg_kinds,
    sweep_problems,
)

_ROOT = Path(__file__).resolve().parents[2]
_PREREG = _ROOT / ".scratch" / "harness" / "probes" / "model_sweep" / "README.md"
_BEFORE_END = END - timedelta(days=1)


@pytest.mark.parametrize(
    ("branch", "expected"),
    [
        ("feature/01-noto-sans-mono", "구현"),
        ("chore/session-cost-retro", "하네스"),
        ("claude/retro-self-approve-b6cb94", "하네스"),
        ("docs/model-sweep-design", None),
        ("docs/design-refresh-spec", None),
        ("fix/typo", None),
        ("main", None),
        ("worktree-model-sweep-design", None),
    ],
)
def test_종류는_브랜치_이름의_머리로_가른다(branch: str, expected: str | None) -> None:
    assert kind(branch) == expected


_ARM_CASES = [
    ("feature/01-noto-sans-mono", COMPARISON),  # 첫 바이트 117
    ("feature/02-icon-stroke-and-removed-props", BASE),  # 38
    ("feature/03-four-themes-and-colors", BASE),  # 46
    ("chore/session-cost-retro", BASE),  # 242
    ("chore/webfetch-summary-hook", COMPARISON),  # 29
    ("claude/retro-self-approve-b6cb94", COMPARISON),  # 17
]


@pytest.mark.parametrize(("branch", "expected"), _ARM_CASES)
def test_갈래는_이름의_해시_첫_바이트가_짝수면_기준이다(branch: str, expected: str) -> None:
    assert assign(branch, _BEFORE_END) == expected


@pytest.mark.parametrize(("branch", "expected"), _ARM_CASES)
def test_판정이_쓰는_배정은_기간이_끝난_뒤에도_이름만으로_낸다(branch: str, expected: str) -> None:
    # 판정은 끝에서 7일 뒤라 assign 은 그날 갈래를 내지 않는다. 배정은 날짜와 무관해야 한다.
    assert arm(branch) == expected


def test_스윕하지_않는_종류는_갈래가_없다() -> None:
    assert assign("docs/model-sweep-design", _BEFORE_END) is None
    assert assign("docs/kickoff-auto-flow-tickets", _BEFORE_END) is None


def test_기간이_끝난_날부터는_갈래가_없다() -> None:
    assert assign("feature/01-noto-sans-mono", END) is None
    assert assign("chore/session-cost-retro", END + timedelta(days=30)) is None


def _prereg_section() -> str:
    text = _PREREG.read_text(encoding="utf-8")
    return text.split("<!-- 사전 등록 시작 -->", 1)[1].split("<!-- 사전 등록 끝 -->", 1)[0]


def test_사전_등록이_도구의_갈래_값을_이름으로_든다() -> None:
    section = _prereg_section()
    for value in ARMS:
        assert f"`{value}`" in section, f"{_PREREG} 의 사전 등록 절에 `{value}` 가 없다"


def test_사전_등록이_도구의_끝_날짜를_든다() -> None:
    assert END.isoformat() in _prereg_section(), f"{_PREREG} 의 사전 등록 절에 {END} 가 없다"


def test_사전_등록_절에서_스윕하는_종류와_접두사를_읽는다() -> None:
    assert prereg_kinds(_prereg_section()) == {
        "구현": ("feature/",),
        "하네스": ("chore/", "claude/"),
    }


def test_스윕하는_종류를_적은_줄이_없으면_빈_사전이다() -> None:
    assert prereg_kinds("### 갈래\n\n- 기준 갈래는 `Opus 5.5 / xhigh`다.\n") == {}


def test_이_저장소의_도구_스윕_종류는_사전_등록과_어긋나지_않는다() -> None:
    # 사람이 스윕을 멈추면 SWEPT 에서 종류를 뺀다(그 종류의 판정은 결론 없음). 빼는 것 밖의 차이는
    # 판정 모집단과 배정을 조용히 어긋나게 한다(PR #217 claude-review 둘째 회차).
    registered = prereg_kinds(_prereg_section())
    assert registered, "사전 등록 절에서 종류를 하나도 읽지 못했다"
    assert sweep_problems(SWEPT, registered) == []


_REGISTERED = {"구현": ("feature/",), "하네스": ("chore/", "claude/")}


def test_멈춰서_빠진_종류는_어긋남이_아니다() -> None:
    assert sweep_problems({"구현": ("feature/",)}, _REGISTERED) == []


@pytest.mark.parametrize(
    "swept",
    [
        {"구현": ("feature/",), "하네스": ("chore/",)},  # 접두사를 줄였다
        {"구현": ("feature/",), "하네스": ("chore/", "claude/"), "수정": ("fix/",)},  # 더했다
        {"구현": ("feat/",)},  # 바꿨다
    ],
)
def test_빠지는_것_밖의_차이를_잡는다(swept: dict[str, tuple[str, ...]]) -> None:
    assert sweep_problems(swept, _REGISTERED) != []


def test_종류는_주어진_표로도_가른다() -> None:
    table = {"수정": ("fix/",)}
    assert kind("fix/typo", table) == "수정"
    assert kind("feature/01-a", table) is None


def test_main은_갈래를_한_줄로_찍는다(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["chore/session-cost-retro"], today=_BEFORE_END) == 0
    assert capsys.readouterr().out == f"{BASE}\n"


def test_main은_스윕_밖이면_그렇게_찍는다(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["docs/model-sweep-design"], today=_BEFORE_END) == 0
    captured = capsys.readouterr()
    assert captured.out == f"{OUTSIDE}\n"
    assert captured.err == ""


def test_main은_기간이_끝났으면_stderr로도_알린다(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["feature/01-noto-sans-mono"], today=END) == 0
    captured = capsys.readouterr()
    assert captured.out == f"{OUTSIDE}\n"
    assert END.isoformat() in captured.err
    assert "model_sweep/README.md" in captured.err


def test_main은_기간이_끝나도_스윕하지_않는_종류에는_알리지_않는다(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["docs/model-sweep-design"], today=END) == 0
    captured = capsys.readouterr()
    assert captured.out == f"{OUTSIDE}\n"
    assert captured.err == ""


@pytest.mark.parametrize("argv", [[], ["feature/01-a", "feature/02-b"]])
def test_main은_인자가_브랜치_하나가_아니면_2로_끝난다(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(argv, today=_BEFORE_END) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "쓰는 법" in captured.err


def test_CLI로_부르면_스윕_밖인_브랜치에_스윕_밖을_UTF8로_찍는다() -> None:
    # next-session 이 도는 셸이나 pre-commit 에 PYTHONUTF8 이 있다고 가정하지 않는다
    # (.claude/rules/tools.md). 없으면 윈도의 파이프는 cp949 라 한글이 깨진다.
    env = {k: v for k, v in os.environ.items() if k not in {"PYTHONUTF8", "PYTHONIOENCODING"}}
    completed = subprocess.run(
        [sys.executable, str(_ROOT / "tools" / "model_sweep.py"), "docs/model-sweep-design"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        cwd=_ROOT,
        env=env,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == OUTSIDE
