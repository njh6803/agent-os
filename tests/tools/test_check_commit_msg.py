"""tools/check_commit_msg.py 의 순수 함수. 정규식 하나가 판정자인데 경계값 시험이 없었다."""

from __future__ import annotations

from tools.check_commit_msg import MAX_SUBJECT, problems_for, subject_of


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
