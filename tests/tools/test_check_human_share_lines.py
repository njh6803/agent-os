"""tools/check_human_share_lines.py. `KICKOFF.md`의 준비와 0~8단계마다 사람 몫 줄의 모양을 본다.

모양과 검사의 내용은 명세 `.scratch/kickoff-auto-flow/spec.md`의 "사람 몫 줄의 모양"과 "사람 몫
검사"다. 여기서 고정하는 것은 그 1~6의 위반을 하나씩 심어 잡는 것, 단순히 펜스 줄마다 켜고 끄면
뒤집히는 펜스 셋(틸드, 4중 백틱 안의 3중 백틱, 닫히지 않은 펜스), 근사 모양, 그리고 독스트링의 못
보는 것이다.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from collections.abc import Mapping
from pathlib import Path

import pytest
from tools.check_human_share_lines import (
    KICKOFF,
    ROOT,
    SECTION_KEYS,
    main,
    problems_in,
    sections_in,
)

기본_절: tuple[tuple[str, str], ...] = (
    ("준비", "사람 몫(결정): 무엇을 만들지 이 세션의 선택 화면에서 고른다."),
    ("0단계. 전역", "사람 몫(허락): 전역 플러그인을 끈다(`claude plugin disable x`)."),
    ("1단계. 저장소", "사람 몫(결정): 워크트리를 쓸지 고른다."),
    ("2단계. 스킬", "사람 몫(결정): 함께 설치할 스킬을 고른다."),
    ("3단계. CLAUDE.md", "사람 몫: 없음"),
    ("4단계. 트래커", "사람 몫(결정): 이슈 트래커를 고른다."),
    ("5단계. 헌법", "사람 몫(결정): 헌법 인터뷰의 결정들."),
    ("6단계. 표준", "사람 몫(결정): 씨앗을 넣을지 고른다."),
    ("7단계. 골격", "사람 몫(사람만): 언어 서버를 설치한다. 확인: `pyright --version`"),
    ("8단계. 첫 커밋", "사람 몫(허락): 저장소를 만든다(`gh repo create a/b --public --push`)."),
)
뒤_절 = "## 9단계. 첫 기능\n\n본문이다.\n"
근사_모양 = "모양이 맞지 않는 사람 몫 줄이다(갈래, 괄호, 콜론과 그 뒤의 공백 하나, 내용을 본다)"
표지_모양 = (
    "목록·인용·표·강조 표지를 붙인 사람 몫 줄이다(사람 몫 줄은 표지 없는 첫 칸의 문단 줄이다)"
)
절_밖 = "열 절 밖의 사람 몫 줄이다"
맞는_줄 = "사람 몫(결정): 맞는 줄이다."


def _런북(
    *,
    바꿈: Mapping[str, str] | None = None,
    뺌: str | None = None,
    절들: tuple[tuple[str, str], ...] = 기본_절,
    머리말: str = "머리말이다.",
    뒤: str = 뒤_절,
) -> str:
    """`KICKOFF.md` 모양의 글.

    `바꿈`은 절의 열쇠(`준비`, `4단계` 같은 머리의 첫 마디)마다 본문을 바꾸고, `뺌`은 그 절을 뺀다.
    """
    바꿈 = 바꿈 or {}
    절_글 = "".join(
        f"## {머리}\n\n{바꿈.get(머리.split('.')[0], 본문)}\n\n"
        for 머리, 본문 in 절들
        if 머리.split(".")[0] != 뺌
    )
    return f"# 런북\n\n{머리말}\n\n{절_글}{뒤}"


def _줄_번호(text: str, 줄: str) -> int:
    """`text`에서 `줄`과 글자 그대로 같은 첫 줄의 번호(1부터)."""
    return next(n for n, line in enumerate(text.splitlines(), start=1) if line == 줄)


def _빈_절(text: str, 머리: str) -> str:
    """`머리` 절에 사람 몫 줄이 없다는 어긋남. `머리`는 `## ` 뒤의 글 전부다."""
    return f"{_줄_번호(text, f'## {머리}')}: 이 절에 사람 몫 줄이 없다 — `## {머리.split()[0]}`"


def test_열_절이_모두_있고_줄의_모양이_맞으면_통과한다() -> None:
    assert problems_in(_런북()) == []


def test_훑는_절은_펜스_밖의_준비와_0단계부터_8단계까지다() -> None:
    """6단계의 펜스 안에는 `## 심각도` 같은 줄이 있다. 그 머리로 절을 끊으면 뒤의 줄이 절 밖이
    된다."""
    본문 = "```markdown\n## 심각도\n## 7단계. 펜스 안\n```\n\n사람 몫(결정): 씨앗을 넣을지 고른다."
    text = _런북(바꿈={"6단계": 본문})
    assert sections_in(text) == list(SECTION_KEYS)
    assert problems_in(text) == []


def test_세_단계_이하의_머리는_절을_끊지_않는다() -> None:
    text = _런북(바꿈={"8단계": "### 소절\n\n사람 몫(허락): 병합한다(`gh pr merge`)."})
    assert problems_in(text) == []


def test_머리가_하나도_맞지_않으면_경로를_잘못_가리킨_것이라_잡는다() -> None:
    assert problems_in("# 다른 문서\n\n## 0단계 마침표가 없다\n\n본문이다.\n") == [
        "0: 열 절의 머리가 하나도 없다 — 이 파일을 가리킨 것이 맞는지 본다"
    ]


def test_머리가_하나도_없으면_닫히지_않은_펜스_말고는_더_알리지_않는다() -> None:
    """파일을 잘못 가리켰으면 절 밖의 사람 몫 줄 같은 어긋남은 뜻이 없다."""
    text = "# 다른 문서\n\n사람 몫(결정): 절 밖이다.\n\n```bash\ngit status\n"
    assert problems_in(text) == [
        "0: 열 절의 머리가 하나도 없다 — 이 파일을 가리킨 것이 맞는지 본다",
        f"{_줄_번호(text, '```bash')}: 닫히지 않은 펜스다",
    ]


def test_빠진_머리를_잡는다() -> None:
    assert problems_in(_런북(뺌="5단계")) == ["0: 머리가 없다 — `## 5단계.`"]


def test_준비로_시작하는_다른_낱말의_머리는_준비가_아니다() -> None:
    절들 = (("준비물", 기본_절[0][1]), *기본_절[1:])
    text = _런북(절들=절들)
    assert problems_in(text) == [
        "0: 머리가 없다 — `## 준비`",
        f"{_줄_번호(text, 기본_절[0][1])}: {절_밖}",
    ]


def test_차례가_어긋난_머리를_잡는다() -> None:
    절들 = (*기본_절[:2], 기본_절[3], 기본_절[2], *기본_절[4:])
    text = _런북(절들=절들)
    assert problems_in(text) == [
        f"{_줄_번호(text, '## 1단계. 저장소')}: 머리의 차례가 어긋난다 — "
        "`## 1단계.`가 `## 2단계.` 뒤에 있다"
    ]


def test_두_번_나온_머리를_잡는다() -> None:
    text = _런북(뒤="## 4단계. 또\n\n사람 몫(결정): 다시 고른다.\n")
    assert problems_in(text) == [f"{_줄_번호(text, '## 4단계. 또')}: 머리가 또 있다 — `## 4단계.`"]


def test_사람_몫_줄이_없는_절을_잡는다() -> None:
    text = _런북(바꿈={"4단계": "본문만 있다."})
    assert problems_in(text) == [_빈_절(text, "4단계. 트래커")]


def test_없음이_다른_사람_몫_줄과_한_절에_있으면_잡는다() -> None:
    text = _런북(바꿈={"3단계": "사람 몫: 없음\n\n사람 몫(결정): 고른다."})
    assert problems_in(text) == [
        f"{_줄_번호(text, '사람 몫: 없음')}: `사람 몫: 없음`이 이 절의 유일한 사람 몫 줄이 아니다"
    ]


def test_띄어_쓰지_않은_사람몫_줄을_잡는다() -> None:
    줄 = "사람몫(결정): 붙여 썼다."
    text = _런북(바꿈={"4단계": f"{맞는_줄}\n\n{줄}"})
    assert problems_in(text) == [f"{_줄_번호(text, 줄)}: {근사_모양}"]


def test_전각_콜론을_쓴_줄을_잡는다() -> None:
    줄 = "사람 몫(결정)： 전각 콜론이다."
    text = _런북(바꿈={"4단계": f"{맞는_줄}\n\n{줄}"})
    assert problems_in(text) == [f"{_줄_번호(text, 줄)}: {근사_모양}"]


def test_그_밖의_근사_모양을_잡는다() -> None:
    근사 = [
        "사람 몫(확인): 갈래가 셋 밖이다.",
        "사람 몫 결정: 괄호가 없다.",
        "사람 몫(결정) 콜론이 없다.",
        "사람 몫(결정):콜론 뒤에 공백이 없다.",
        "사람 몫(결정):  콜론 뒤의 공백이 둘이다.",
        "사람 몫(결정): ",
        "사람 몫（결정）: 전각 괄호다.",
        f"사람{chr(0x3000)}몫(결정): 전각 공백이다.",
        "사람  몫(결정): 공백이 둘이다.",
        "사람 몫: 없다",
        "사람 몫:없음",
    ]
    for 줄 in 근사:
        text = _런북(바꿈={"4단계": f"{맞는_줄}\n\n{줄}"})
        assert problems_in(text) == [f"{_줄_번호(text, 줄)}: {근사_모양}"], 줄


def test_목록_인용_표_강조_표지를_붙인_사람_몫_줄을_잡는다() -> None:
    """첫 칸이 아니라서 사람 몫으로 세어지지 않는다. 그대로 두면 그 일이 멈춤 없이 지나간다."""
    표지 = [
        "- 사람 몫(결정): 목록 항목이다.",
        "1. 사람 몫(허락): 번호 목록이다(`gh pr merge`).",
        "  * 사람몫(결정): 들여 쓴 하위 목록이다.",
        "> 사람 몫(결정): 인용이다.",
        "| 사람 몫(결정): 표의 첫 칸이다. | 둘째 칸 |",
        "**사람 몫(결정):** 굵게 썼다.",
        "- **사람 몫(결정)**: 목록 안에서 굵게 썼다.",
    ]
    for 줄 in 표지:
        text = _런북(바꿈={"4단계": f"{맞는_줄}\n\n{줄}"})
        assert problems_in(text) == [f"{_줄_번호(text, 줄)}: {표지_모양}"], 줄


def test_구분선처럼_긴_별표나_밑줄_줄도_곧바로_판정한다() -> None:
    """강조 표지를 1칸·2칸으로 나누는 길을 모두 되짚으면 36자에서 수 초가 걸린다(PR 직전 리뷰)."""
    본문 = f"{맞는_줄}\n\n{'*' * 36}\n\n{'_' * 36}x"
    started = time.perf_counter()
    assert problems_in(_런북(바꿈={"4단계": 본문})) == []
    assert time.perf_counter() - started < 1.0


def test_확인이_없는_사람만_줄을_잡는다() -> None:
    for 줄 in (
        "사람 몫(사람만): 로그인한다.",
        "사람 몫(사람만): 로그인한다. 확인：`gh auth status`",
        "사람 몫(사람만): 로그인한다. 확인:",
    ):
        text = _런북(바꿈={"7단계": 줄})
        assert problems_in(text) == [f"{_줄_번호(text, 줄)}: 사람만 줄에 `확인: `이 없다"], 줄


def test_열_절_밖의_사람_몫_줄을_잡는다() -> None:
    머리말 = "사람 몫(결정): 머리말에 있다."
    구단계 = "사람 몫(허락): 9단계에 있다(`gh pr merge`)."
    text = _런북(머리말=머리말, 뒤=f"## 9단계. 첫 기능\n\n{구단계}\n")
    assert problems_in(text) == [
        f"{_줄_번호(text, 머리말)}: {절_밖}",
        f"{_줄_번호(text, 구단계)}: {절_밖}",
    ]


def test_틸드_펜스_안의_줄은_세지_않는다() -> None:
    text = _런북(바꿈={"2단계": "~~~\n사람 몫(결정): 펜스 안이다.\n~~~"})
    assert problems_in(text) == [_빈_절(text, "2단계. 스킬")]


def test_4중_백틱_안의_3중_백틱은_펜스를_닫지_않는다() -> None:
    text = _런북(바꿈={"2단계": "````markdown\n```\n사람 몫(결정): 펜스 안이다.\n````"})
    assert problems_in(text) == [_빈_절(text, "2단계. 스킬")]


def test_다른_문자나_정보_문자열이나_네_칸_들여쓰기의_줄은_펜스를_닫지_않는다() -> None:
    for 가짜 in ("~~~", "```bash", "    ```"):
        text = _런북(바꿈={"2단계": f"```\n{가짜}\n사람 몫(결정): 펜스 안이다.\n```"})
        assert problems_in(text) == [_빈_절(text, "2단계. 스킬")], 가짜


def test_닫히지_않은_펜스를_잡는다() -> None:
    text = _런북(뒤="## 9단계. 첫 기능\n\n```bash\ngit status\n")
    assert problems_in(text) == [f"{_줄_번호(text, '```bash')}: 닫히지 않은 펜스다"]


def test_정보_문자열에_백틱이_든_줄은_펜스를_열지_않는다() -> None:
    """CommonMark는 백틱 펜스의 정보 문자열에 백틱을 두지 않는다. 그 줄은 문단이다."""
    text = _런북(바꿈={"2단계": "```코드`가 아니다\n\n사람 몫(결정): 펜스 밖이다."})
    assert problems_in(text) == []


def test_네_칸_들여_쓴_백틱_줄은_펜스를_열지_않는다() -> None:
    text = _런북(바꿈={"2단계": "    ```\n\n사람 몫(결정): 펜스 밖이다."})
    assert problems_in(text) == []


def test_못_보는_것_산문_속에_주어_없이_적힌_사람_몫은_지나간다() -> None:
    산문 = "CodeRabbit GitHub App은 공개 저장소이거나 유료 플랜일 때만 설치한다."
    text = _런북(바꿈={"8단계": f"{기본_절[9][1]}\n\n{산문}"})
    assert problems_in(text) == []


def test_못_보는_것_사람_몫이_아닌_일을_사람_몫_줄로_적어도_지나간다() -> None:
    text = _런북(바꿈={"7단계": "사람 몫(사람만): 테스트를 돌린다. 확인: `uv run pytest`"})
    assert problems_in(text) == []


def test_못_보는_것_갈래가_틀려도_지나간다() -> None:
    """저장소 시크릿은 사람만 할 수 있는 일인데 결정으로 적었다."""
    줄 = "사람 몫(결정): 저장소 시크릿 `CLAUDE_CODE_OAUTH_TOKEN`을 넣는다."
    assert problems_in(_런북(바꿈={"8단계": 줄})) == []


def test_못_보는_것_확인_명령이_틀려도_지나간다() -> None:
    줄 = "사람 몫(사람만): `coderabbit auth login`을 친다. 확인: `git status`"
    assert problems_in(_런북(바꿈={"7단계": 줄})) == []


def test_못_보는_것_일이_일어나는_차례가_아닌_자리의_줄도_지나간다() -> None:
    """보호의 허락 줄이 저장소를 만드는 명령보다 앞에 있다. 진행 규율은 저장소가 없을 때 멈춘다."""
    본문 = (
        "사람 몫(허락): main을 보호한다(`gh api -X PUT repos/a/b/branches/main/protection`).\n\n"
        "```bash\ngh repo create a/b --public --push\n```"
    )
    assert problems_in(_런북(바꿈={"8단계": 본문})) == []


def test_못_보는_것_목록_항목_안에_들여_쓴_사람_몫_줄은_세지도_보지도_않는다() -> None:
    """들여 쓴 줄은 줄 머리가 첫 칸이 아니다. 모양이 틀려도 지나가고 절의 사람 몫으로 세지도
    않는다."""
    들여_쓴_줄 = "1. 항목이다.\n   사람 몫(사람만): 확인이 없고 들여 썼다."
    assert problems_in(_런북(바꿈={"7단계": f"{맞는_줄}\n\n{들여_쓴_줄}"})) == []

    text = _런북(바꿈={"7단계": 들여_쓴_줄})
    assert problems_in(text) == [_빈_절(text, "7단계. 골격")]


def test_못_보는_것_한_칸에서_세_칸_들여_쓴_최상위_사람_몫_줄은_세지도_보지도_않는다() -> None:
    """목록 문맥을 따라가지 않아 목록 항목의 이어짐과 가르지 못한다."""
    들여_쓴_줄 = " 사람 몫(사람만): 한 칸 들여 썼고 확인이 없다."
    assert problems_in(_런북(바꿈={"7단계": f"{맞는_줄}\n\n{들여_쓴_줄}"})) == []

    text = _런북(바꿈={"7단계": 들여_쓴_줄})
    assert problems_in(text) == [_빈_절(text, "7단계. 골격")]


def test_못_보는_것_펜스_안의_사람_몫_줄은_같은_절에_다른_줄이_있으면_지나간다() -> None:
    본문 = f"{맞는_줄}\n\n```bash\n사람 몫(사람만): 펜스 안이고 확인이 없다.\n```"
    assert problems_in(_런북(바꿈={"8단계": 본문})) == []


def test_못_보는_것_목록_항목에_빈_줄_없이_붙은_첫_칸의_줄은_목록_안이어도_센다() -> None:
    """CommonMark에서 그 줄은 앞 항목의 게으른 이어짐(lazy continuation)이라 목록 안이다."""
    text = _런북(바꿈={"7단계": "- 항목이다.\n사람 몫(결정): 게으른 이어짐이다."})
    assert problems_in(text) == []


def test_못_보는_것_인용에_빈_줄_없이_붙은_첫_칸의_줄은_인용_안이어도_센다() -> None:
    text = _런북(바꿈={"7단계": "> 인용이다.\n사람 몫(결정): 게으른 이어짐이다."})
    assert problems_in(text) == []


def test_못_보는_것_줄_머리가_아닌_자리의_사람_몫_글자는_보지_않는다() -> None:
    """표의 둘째 칸과 문장 가운데의 `사람 몫`은 모양이 틀려도 지나가고 세지도 않는다."""
    본문 = "| 단계 | 사람 몫(사람만): 확인이 없다 |\n\n이 문장의 사람 몫(결정) 은 가운데에 있다."
    text = _런북(바꿈={"7단계": 본문})
    assert problems_in(text) == [_빈_절(text, "7단계. 골격")]


def test_못_보는_것_HTML_주석_안의_첫_칸의_줄도_센다() -> None:
    """화면에는 보이지 않는 줄이지만 진행 규율이 읽는 날글에는 있다."""
    text = _런북(바꿈={"7단계": "<!--\n사람 몫(결정): 주석 안이다.\n-->"})
    assert problems_in(text) == []


def test_어긋남이_없으면_0이고_아무것도_찍지_않는다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "KICKOFF.md"
    path.write_text(_런북(), encoding="utf-8")
    assert main(path) == 0
    assert capsys.readouterr().out == ""


def test_파일이_없으면_경로를_잘못_가리킨_것이라_실패한다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(tmp_path / "없다.md") == 1
    assert "없다.md가 없다 — 이 파일을 가리킨 것이 맞는지 본다" in capsys.readouterr().out


def test_CLI가_인자로_받은_파일을_판정하고_어긋남을_찍는다(tmp_path: Path) -> None:
    text = _런북(바꿈={"4단계": "본문만 있다."})
    path = tmp_path / "KICKOFF.md"
    path.write_text(text, encoding="utf-8")
    process = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_human_share_lines.py"), str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=ROOT,
        env={**os.environ, "PYTHONUTF8": "1"},
        check=False,
    )
    assert process.returncode == 1
    assert f"KICKOFF.md:{_빈_절(text, '4단계. 트래커')}" in process.stdout


def test_이_저장소의_KICKOFF_md에서_훑는_절은_준비와_0단계부터_8단계까지_열이다() -> None:
    assert sections_in(KICKOFF.read_text(encoding="utf-8")) == list(SECTION_KEYS)


def test_이_저장소의_KICKOFF_md는_사람_몫_줄의_모양을_지킨다() -> None:
    assert main() == 0
