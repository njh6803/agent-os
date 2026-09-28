"""tools/check_quotes.py — 인용을 뽑는 것과 원문 대조. 저장소 전체를 도는 스모크 하나."""

from __future__ import annotations

from pathlib import Path

import pytest
from tools.check_quotes import (
    ROOT,
    Quote,
    added_lines_from_diff,
    default_files,
    quotes_in,
    staged_added_lines,
    warnings_for,
)

원문 = "지침을 쓰는 사람이 그 지침을 가장 먼저 어긴다는 것이 이 저장소가 훅을 위에 두는 이유다"


def _저장소를_만든다(root: Path, 문서: str, 원천: str = 원문) -> Path:
    (root / "docs").mkdir()
    (root / "docs" / "source.md").write_text(f"# 원천\n\n{원천}\n", encoding="utf-8")
    quoting = root / "docs" / "quoting.md"
    quoting.write_text(문서, encoding="utf-8")
    return quoting


def test_원문이_다른_파일에_있으면_경고가_없다(tmp_path: Path) -> None:
    quoting = _저장소를_만든다(tmp_path, f'감사가 말한 "{원문}"가 여기 적용된다.\n')

    assert warnings_for([quoting], tmp_path) == []


def test_원문이_어디에도_없으면_파일과_줄을_들어_경고한다(tmp_path: Path) -> None:
    문서 = '첫 줄\n감사가 말한 "지침을 쓰는 사람이 그 지침을 나중에야 어긴다는 것"이라는 말.\n'
    quoting = _저장소를_만든다(tmp_path, 문서)

    warnings = warnings_for([quoting], tmp_path)

    assert len(warnings) == 1
    assert warnings[0].startswith("docs/quoting.md:2:")
    assert "글자 그대로 없다" in warnings[0]


def test_같은_파일_안의_원문도_두_번째_자리다(tmp_path: Path) -> None:
    문서 = f'{원문}\n\n위 문장, 곧 "{원문}"를 다시 든다.\n'
    quoting = _저장소를_만든다(tmp_path, 문서, 원천="다른 것")

    assert warnings_for([quoting], tmp_path) == []


def test_인용문_줄과_코드_안은_보지_않는다() -> None:
    markdown = (
        '> 사용자: "이것은 사용자가 말한 긴 문장이라 저장소에 원문이 없다"\n'
        '`"코드 스팬 안의 긴 문장도 인용이 아니라 문자열이다"`\n'
        '```\nprint("펜스 안의 긴 문장도 인용이 아니라 문자열이다")\n```\n'
        '산문의 "이것만 산문의 진짜 인용이고 스무 자를 넘는다".\n'
    )

    assert quotes_in(markdown) == [Quote(6, "이것만 산문의 진짜 인용이고 스무 자를 넘는다", None)]


def test_코드_스팬과_강조는_벗기고_대조한다(tmp_path: Path) -> None:
    """원문에 `itemSchema`가 백틱으로 있고 인용은 백틱을 뗐거나 강조를 더한 경우가 잦다."""
    quoting = _저장소를_만든다(
        tmp_path,
        '명세는 "스트림의 항목 스키마는 itemSchema로 계약에 **실린다**"고 적는다.\n',
        원천="스트림의 항목 스키마는 `itemSchema`로 계약에 실린다.",
    )

    assert warnings_for([quoting], tmp_path) == []


def test_따옴표_쌍이_어긋나_잡힌_조각은_버린다() -> None:
    앞 = '앱이 지은 제목("첫 인용 스무 자를 넘기는 문장이다 정말로")가 붙어 왔다. '
    markdown = 앞 + '로 지은 것("둘째")도.\n'

    assert quotes_in(markdown) == [Quote(1, "첫 인용 스무 자를 넘기는 문장이다 정말로", None)]


def test_diff_헝크_머리에서_더한_줄을_읽는다() -> None:
    diff = (
        "--- a/x.md\n+++ b/x.md\n@@ -1,2 +3,4 @@\n+a\n+b\n+c\n+d\n"
        "@@ -9 +12 @@\n+e\n@@ -20,3 +20,0 @@\n-x\n"
    )

    assert added_lines_from_diff(diff) == {3, 4, 5, 6, 12}


def test_스테이지된_줄만_볼_때_diff_가_없으면_전체를_본다(tmp_path: Path) -> None:
    """저장소 밖(테스트)에서는 diff 가 없어 None 이고 전체가 대상이다. 조용히 비지 않는다."""
    문서 = '첫 줄\n감사가 말한 "지침을 쓰는 사람이 그 지침을 나중에야 어긴다는 것"이라는 말.\n'
    quoting = _저장소를_만든다(tmp_path, 문서)

    filtered = warnings_for(
        [quoting], tmp_path, line_filter=lambda p: staged_added_lines(p, tmp_path)
    )

    assert len(filtered) == 1


def test_상대_경로로_넘어온_파일도_한_번만_센다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """pre-commit 은 상대 경로를 넘긴다. 같은 파일이 두 키로 들어가면 인용이 두 번 세어진다."""
    문서 = '첫 줄\n감사가 말한 "지침을 쓰는 사람이 그 지침을 나중에야 어긴다는 것"이라는 말.\n'
    _저장소를_만든다(tmp_path, 문서)
    monkeypatch.chdir(tmp_path)

    assert len(warnings_for([Path("docs/quoting.md")], tmp_path)) == 1


def test_추적되지_않은_새_파일의_옳은_인용은_자기_자리를_센다(tmp_path: Path) -> None:
    """corpus 는 git ls-files 인데 새 파일은 거기 없다. 그러면 옳은 인용도 한 자리 모자란다."""
    quoting = _저장소를_만든다(tmp_path, f'감사가 말한 "{원문}"가 여기 적용된다.\n')

    assert warnings_for([quoting], tmp_path) == []


def test_가운데가_생략된_인용은_조각마다_찾는다(tmp_path: Path) -> None:
    quoting = _저장소를_만든다(
        tmp_path,
        '헌법은 "플러그인은 sdk만 import한다. … import-linter가 판정한다"고 적었다.\n',
        원천="플러그인은 sdk만 import한다. 의존 방향은 여섯이다. import-linter가 판정한다.",
    )

    assert warnings_for([quoting], tmp_path) == []


def test_코드_스팬_안의_셸_인용은_인용이_아니다() -> None:
    markdown = '`uv run --project "${DIR}" python "${DIR}/tools/hook.py"` 로 돈다.\n'

    assert quotes_in(markdown) == []


def test_스무_자_미만은_보지_않는다() -> None:
    assert quotes_in('짧은 "열여덟 자짜리 인용문은 세지 않아"와 "an agent OS"\n') == []
    assert len(quotes_in('"꼭 스무 자가 되는 인용은 본다. 여기가 스무 자"\n')) == 1


def test_ADR_가까이의_인용은_그_ADR_파일에서_찾는다(tmp_path: Path) -> None:
    (tmp_path / "docs" / "adr").mkdir(parents=True)
    (tmp_path / "docs" / "adr" / "0009-resume.md").write_text(
        "### 2026-09-22 결정은 정책이 아니라 멈춘 호출에 묶인다. 마스킹의 범위는 인자뿐이다\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "adr" / "0010-server.md").write_text(
        "### 2026-09-22 조립은 서버가\n", encoding="utf-8"
    )
    quoting = tmp_path / "docs" / "note.md"
    quoting.write_text(
        'ADR 0009의 2026-09-22 이력 "결정은 정책이 아니라 멈춘 호출에 묶인다"가 원천이다.\n'
        'ADR 0009("정책이 결정을 정한다")는 틀린 인용이다.\n'
        'ADR 0099("없는 ADR 의 인용")도 잡는다.\n'
        'ADR 0009("결정은 정책이 … 인자뿐이다")처럼 생략된 것은 조각으로 본다.\n'
        'ADR 0009의 이력과 ADR 0010("조립은 서버가")는 뒤의 ADR 것이다.\n',
        encoding="utf-8",
    )

    warnings = warnings_for([quoting], tmp_path)

    assert len(warnings) == 2
    assert "ADR 0009 에 이 문구가 글자 그대로 없다" in warnings[0]
    assert "ADR 0099 파일이 없다" in warnings[1]


def test_ADR_가까이_적혔을_뿐_다른_자리에_있는_인용은_경고하지_않는다(tmp_path: Path) -> None:
    (tmp_path / "docs" / "adr").mkdir(parents=True)
    (tmp_path / "docs" / "adr" / "0009-resume.md").write_text("### 이력\n", encoding="utf-8")
    (tmp_path / "docs" / "spec.md").write_text(
        "명세는 재개를 트레이스 재생으로 정한다.\n", encoding="utf-8"
    )
    quoting = tmp_path / "docs" / "note.md"
    quoting.write_text(
        'ADR 0009 뒤에 명세가 "재개를 트레이스 재생으로 정한다"고 했다.\n', encoding="utf-8"
    )

    assert warnings_for([quoting], tmp_path) == []


def test_생략된_인용의_조각도_두_번째_자리를_요구한다(tmp_path: Path) -> None:
    """조각을 인용 파일 자신에서 찾으면 생략 인용은 영영 경고하지 않는다(2026-09-28 적대 검증)."""
    quoting = _저장소를_만든다(
        tmp_path, '없는 말을 "이 조각은 어디에도 없다 … 이 조각도 어디에 없다"고 적었다.\n'
    )

    assert len(warnings_for([quoting], tmp_path)) == 1


def test_코드_스팬_안의_홑_따옴표_하나가_줄의_인용을_지우지_않는다() -> None:
    markdown = '`"` 하나 뒤의 "이것은 스무 자를 넘는 진짜 인용이고 잡혀야 한다"는 인용이다.\n'

    assert quotes_in(markdown) == [
        Quote(1, "이것은 스무 자를 넘는 진짜 인용이고 잡혀야 한다", None)
    ]


def test_목록_안의_인용문과_펜스도_뺀다() -> None:
    markdown = (
        '- > 사용자: "목록 안 인용문의 긴 문장은 원문이 없어도 본다면 거짓 양성"\n'
        '- ````\n  "네 백틱 펜스 안의 긴 문장도 코드라서 인용이 아니다"\n  ````\n'
        '```\n"닫히지 않은 펜스 뒤는 전부 코드라서 인용이 아니다 정말로"\n'
    )

    assert quotes_in(markdown) == []


def test_닫는_펜스가_여는_것보다_길어도_닫힌다() -> None:
    """PR #92 리뷰: ``` 를 ```` 로 닫으면 열린 펜스로 봐서 뒤의 산문을 전부 코드로 버렸다."""
    markdown = '```python\n코드\n````\n"펜스 뒤의 산문 인용은 스무 자를 넘고 잡혀야 한다"\n'

    assert quotes_in(markdown) == [
        Quote(4, "펜스 뒤의 산문 인용은 스무 자를 넘고 잡혀야 한다", None)
    ]


def test_굽은_따옴표도_인용이다() -> None:
    assert quotes_in("그가 “굽은 따옴표로 감싼 스무 자 넘는 인용문이다 정말로”라 했다\n") == [
        Quote(1, "굽은 따옴표로 감싼 스무 자 넘는 인용문이다 정말로", None)
    ]


def test_독스트링이_못_본다고_적은_것은_정말_못_본다(tmp_path: Path) -> None:
    """못 본다는 주장도 잰다(.claude/rules/tools.md). 잡게 되면 독스트링을 고친다."""
    홑따옴표 = "'홑따옴표로 감싼 스무 자 넘는 인용은 보지 않는다 정말로'\n"
    줄바꿈 = '"줄바꿈을 넘는 인용은 첫 줄에서 끊겨\n보지 않는다 정말로 스무 자를 넘어도"\n'
    assert quotes_in(홑따옴표) == []
    assert quotes_in(줄바꿈) == []

    같은_틀린_인용 = f'하나 "{원문[:-3]} 까닭이다"\n둘 "{원문[:-3]} 까닭이다"\n'
    quoting = _저장소를_만든다(tmp_path, 같은_틀린_인용, 원천="다른 것")
    assert warnings_for([quoting], tmp_path) == []


def test_이_저장소_전체를_돌려도_끝난다() -> None:
    """경고 수는 고정하지 않는다 — 경고만 내는 검사라 초록의 기준이 없다. 돌아가는 것만 본다."""
    files = default_files(ROOT)

    assert files
    assert all("/.claude/skills/" not in path.as_posix() for path in files)
    warnings_for(files, ROOT)
