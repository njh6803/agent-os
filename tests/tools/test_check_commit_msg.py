"""tools/check_commit_msg.py 의 순수 함수. 정규식 하나가 판정자인데 경계값 시험이 없었다."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from tools.check_commit_msg import MAX_SUBJECT, problems_for, subject_of

ROOT = Path(__file__).resolve().parents[2]


def test_컨벤셔널_제목은_통과한다() -> None:
    assert problems_for("feat: 꺼진 플러그인을 막는다") == []
    assert problems_for("fix(core): 재개의 첫 걸음에서 await 를 뺀다") == []
    assert problems_for("chore(ci)!: 게이트를 하나 더 건다") == []
    assert problems_for("docs: 일지를 남긴다 (#88)") == []


def test_타입이_없거나_틀리면_잡는다() -> None:
    assert len(problems_for("플러그인을 막는다")) == 1
    assert len(problems_for("Feat: 대문자 타입")) == 1
    assert len(problems_for("feature: 없는 타입")) == 1
    assert len(problems_for("feat:공백 없음")) == 1


def test_길이와_마침표는_경계에서_갈린다() -> None:
    assert problems_for("feat: " + "a" * (MAX_SUBJECT - 6)) == []
    assert any("73자" in p for p in problems_for("feat: " + "a" * (MAX_SUBJECT - 5)))
    assert any("마침표" in p for p in problems_for("feat: 끝에 마침표."))


def test_병합과_되돌리기_메시지는_통과한다() -> None:
    assert problems_for("Merge branch 'main' into feature/x") == []
    assert problems_for('Revert "feat: x"') == []
    assert problems_for("fixup! feat: x") == []


def test_제목은_주석이_아닌_첫_줄이다() -> None:
    assert subject_of("# 주석\n\nfeat: 제목\n\n본문") == "feat: 제목"
    assert subject_of("\n\n") == ""


def test_CLI_진입점이_나쁜_메시지에_1을_돌려준다(tmp_path: Path) -> None:
    """commit-msg 훅이 부르는 모양 그대로 — 파일 경로 하나, 빨강이면 1."""
    message = tmp_path / "MSG"
    message.write_text("플러그인을 막는다\n", encoding="utf-8")

    process = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_commit_msg.py"), str(message)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=ROOT,
        env={**os.environ, "PYTHONUTF8": "1"},
        check=False,
    )

    assert process.returncode == 1
    assert "형식이 아니다" in process.stdout
