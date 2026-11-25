"""제품 마이그레이션 폴더의 파일들이 정한 꼴인지 본다(ADR 0066, 명세 postgres-foundation).

꼴은 명세 "마이그레이션 파일"이 정했다. 번호는 `0001`부터 하나씩 오르는 네 자리 수이고, 파일
이름은 `<번호>_<짧은 영문 이름>.py` 다. 파일마다 앞 번호를 가리켜 사슬을 이루고, 마지막 번호는
하나이며, 되돌리는 함수 `downgrade` 는 없다. 나란히 짠 두 브랜치가 같은 번호를 들고 오면 나중에
병합하는 쪽이 기준 브랜치를 합친 뒤 이 시험이 빨개진다.

파일을 실행하지 않고 `ast` 로 읽는다. 파일 최상위의 `revision`·`down_revision` 대입에 쓴 글자
값(리터럴)만 보고, 계산해서 만든 값은 읽지 못한다(그때는 "글자 값이 아니다"나 "글자 값으로 읽지
못했다"는 까닭으로 센다). `downgrade` 는 함수 정의뿐 아니라 같은 이름의 대입과 import 도 센다
(alembic 은 모듈의 그 이름을 찾기 때문이다). 계산해서 만든 이름(`globals()` 로 넣는 것 등)은 보지
못한다.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Mapping
from pathlib import Path

import pytest

from tools import check_notes

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / check_notes.PRODUCT_MIGRATIONS
WIDGET_FOLDER = ROOT / "widget-admin" / "src" / "widget_admin" / "migrations" / "versions"

_NAME = re.compile(r"(?P<number>[0-9]{4})_[a-z][a-z0-9_]*\.py")


def read_folder(folder: Path) -> dict[str, str]:
    """폴더 바로 아래의 `.py` 파일 이름과 글. 폴더가 없으면 빈 사전이다."""
    if not folder.is_dir():
        return {}
    return {path.name: path.read_text(encoding="utf-8") for path in sorted(folder.glob("*.py"))}


def _literal(tree: ast.Module, name: str) -> tuple[bool, str | None]:
    """최상위 대입 `name = <글자 값>` 의 값. 앞은 읽었는지, 뒤는 그 값(`None` 이거나 글자)이다.

    같은 이름의 최상위 대입이 둘 이상이면 읽지 못한 것으로 센다. 나중 대입이 모듈의 최종 값을
    바꾸는데 첫 대입만 보고 지나가는 일을 막으려는 것이다.
    """
    values: list[ast.expr | None] = []
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target, value = node.target.id, node.value
        elif (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            target, value = node.targets[0].id, node.value
        else:
            continue
        if target == name:
            values.append(value)
    if len(values) != 1:
        return False, None
    value = values[0]
    if isinstance(value, ast.Constant) and (value.value is None or isinstance(value.value, str)):
        return True, value.value
    return False, None


def _binds_downgrade(node: ast.AST) -> bool:
    """이 노드가 `downgrade` 라는 이름을 함수 정의, 대입, import 로 묶는가."""
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
        return node.name == "downgrade"
    if isinstance(node, ast.Name):
        return node.id == "downgrade" and isinstance(node.ctx, ast.Store)
    if isinstance(node, ast.alias):
        # `import a.b` 는 이름 `a` 를 묶는다. `as` 가 있으면 그 이름이다
        bound = node.asname or node.name.split(".")[0]
        return bound == "downgrade"
    return False


def shape_problems(sources: Mapping[str, str]) -> list[str]:
    """마이그레이션 파일들이 꼴에 맞지 않는 까닭들. 비어 있으면 맞다.

    `sources` 는 파일 이름에서 글로 가는 사전이다. 훑은 파일이 하나도 없으면 맞다고 하지 않고
    까닭으로 센다. 경로가 틀려도 위반 0 으로 조용히 초록이 되는 일을 막으려는 것이다.
    """
    if not sources:
        return ["마이그레이션 파일을 하나도 읽지 못했다. 폴더 경로를 본다."]
    problems: list[str] = []
    numbered: dict[str, list[str]] = {}
    revisions: dict[str, str | None] = {}
    for name, text in sources.items():
        match = _NAME.fullmatch(name)
        if match is None:
            problems.append(f"{name}: 파일 이름이 `<네 자리 번호>_<영문 이름>.py` 꼴이 아니다.")
            continue
        number = match.group("number")
        numbered.setdefault(number, []).append(name)
        try:
            tree = ast.parse(text)
        except SyntaxError as error:
            problems.append(f"{name}: 파이썬으로 읽지 못한다: {error.msg}")
            continue
        found, revision = _literal(tree, "revision")
        if not found or revision != number:
            problems.append(
                f"{name}: `revision` 이 파일 이름의 번호 {number} 와 같은 글자 값이 아니다."
            )
        found, previous = _literal(tree, "down_revision")
        if not found:
            problems.append(f"{name}: `down_revision` 을 글자 값(없으면 None)으로 읽지 못했다.")
        else:
            revisions[number] = previous
        if any(_binds_downgrade(node) for node in ast.walk(tree)):
            problems.append(f"{name}: `downgrade` 가 있다. 되돌리는 함수는 두지 않는다.")
    problems += [
        f"겹친 번호 {number}: {', '.join(sorted(names))}"
        for number, names in sorted(numbered.items())
        if len(names) > 1
    ]
    numbers = sorted(numbered)
    expected = [f"{index:04d}" for index in range(1, len(numbers) + 1)]
    if numbers != expected:
        problems.append(f"번호가 0001 부터 하나씩 오르지 않는다: {', '.join(numbers)}")
    for index, number in enumerate(numbers):
        if number not in revisions:
            continue
        before = numbers[index - 1] if index else None
        if revisions[number] != before:
            problems.append(
                f"{number} 의 앞 번호 `down_revision` 이 {revisions[number]!r} 이다."
                f" 앞 번호 {before!r} 를 가리켜야 한다."
            )
    heads = [n for n in numbers if n in revisions and n not in set(revisions.values())]
    if len(heads) != 1:
        problems.append(f"마지막 번호가 하나가 아니다: {', '.join(heads) or '없음'}")
    return problems


def _file(number: str, previous: str | None, *, downgrade: bool = False) -> str:
    text = f'revision: str = "{number}"\ndown_revision: str | None = {previous!r}\n'
    text = text.replace("'", '"')
    text += "\n\ndef upgrade() -> None:\n    pass\n"
    if downgrade:
        text += "\n\ndef downgrade() -> None:\n    pass\n"
    return text


GOOD = {
    "0001_first.py": _file("0001", None),
    "0002_second.py": _file("0002", "0001"),
    "0003_third.py": _file("0003", "0002"),
}


def test_이_저장소의_마이그레이션_폴더는_꼴이_맞다() -> None:
    sources = read_folder(FOLDER)
    assert sources, f"훑을 파일이 없다: {FOLDER}"
    assert shape_problems(sources) == []


def test_이_저장소의_위젯_관리_마이그레이션_폴더도_꼴이_맞다() -> None:
    # 둘째 설치 묶음의 폴더다. 노트 검사의 `PRODUCT_MIGRATIONS` 는 Agent OS 의 폴더 하나라 이
    # 폴더를 알지 못하고, 그 갈래의 느낌표 규칙은 위젯 관리 서버의 배포를 짓는 티켓(04)이 정한다.
    sources = read_folder(WIDGET_FOLDER)
    assert sources, f"훑을 파일이 없다: {WIDGET_FOLDER}"
    assert shape_problems(sources) == []


def test_꼴이_맞는_사슬은_문제가_없다() -> None:
    assert shape_problems(GOOD) == []


def test_파일이_하나도_없으면_맞다고_하지_않는다() -> None:
    assert shape_problems({}) == ["마이그레이션 파일을 하나도 읽지 못했다. 폴더 경로를 본다."]


def test_없는_폴더는_빈_사전으로_읽어_꼴이_맞다고_하지_않는다(tmp_path: Path) -> None:
    assert read_folder(tmp_path / "없다") == {}
    assert shape_problems(read_folder(tmp_path / "없다")) != []


def test_겹친_번호를_잡는다() -> None:
    sources = {**GOOD, "0002_other.py": _file("0002", "0001")}
    assert shape_problems(sources) == ["겹친 번호 0002: 0002_other.py, 0002_second.py"]


def test_건너뛴_번호를_잡는다() -> None:
    sources = {"0001_first.py": GOOD["0001_first.py"], "0003_third.py": _file("0003", "0001")}
    assert shape_problems(sources) == ["번호가 0001 부터 하나씩 오르지 않는다: 0001, 0003"]


def test_0001이_아닌_번호로_시작하면_잡는다() -> None:
    sources = {"0002_second.py": _file("0002", None)}
    assert shape_problems(sources) == ["번호가 0001 부터 하나씩 오르지 않는다: 0002"]


def test_끊긴_사슬을_잡는다() -> None:
    sources = {**GOOD, "0003_third.py": _file("0003", "0001")}
    assert shape_problems(sources)[0] == (
        "0003 의 앞 번호 `down_revision` 이 '0001' 이다. 앞 번호 '0002' 를 가리켜야 한다."
    )


def test_첫_파일이_앞_번호를_가리키면_잡는다() -> None:
    sources = {**GOOD, "0001_first.py": _file("0001", "0000")}
    assert shape_problems(sources) == [
        "0001 의 앞 번호 `down_revision` 이 '0000' 이다. 앞 번호 None 를 가리켜야 한다."
    ]


def test_마지막_번호가_둘이면_잡는다() -> None:
    # 0002 와 0003 이 모두 0001 을 가리키는 갈래: 사슬 문제 말고도 마지막 번호가 둘이다
    sources = {**GOOD, "0003_third.py": _file("0003", "0001")}
    assert shape_problems(sources)[1:] == ["마지막 번호가 하나가 아니다: 0002, 0003"]


def test_downgrade가_든_파일을_잡는다() -> None:
    sources = {**GOOD, "0002_second.py": _file("0002", "0001", downgrade=True)}
    assert shape_problems(sources) == [
        "0002_second.py: `downgrade` 가 있다. 되돌리는 함수는 두지 않는다."
    ]


@pytest.mark.parametrize(
    "hidden",
    [
        "downgrade = upgrade\n",
        "downgrade: object = None\n",
        "from somewhere import downgrade\n",
        "from somewhere import other as downgrade\n",
        "import downgrade\n",
    ],
)
def test_downgrade를_함수가_아닌_꼴로_들여도_잡는다(hidden: str) -> None:
    sources = {**GOOD, "0002_second.py": _file("0002", "0001") + hidden}
    assert shape_problems(sources) == [
        "0002_second.py: `downgrade` 가 있다. 되돌리는 함수는 두지 않는다."
    ]


def test_이름에_downgrade가_들었을_뿐인_것은_잡지_않는다() -> None:
    harmless = "downgrade_note = 1\nfrom somewhere import downgrade_helper\n"
    sources = {**GOOD, "0002_second.py": _file("0002", "0001") + harmless}
    assert shape_problems(sources) == []


def test_revision이_파일_이름의_번호와_다르면_잡는다() -> None:
    sources = {**GOOD, "0002_second.py": _file("0009", "0001")}
    assert shape_problems(sources) == [
        "0002_second.py: `revision` 이 파일 이름의 번호 0002 와 같은 글자 값이 아니다."
    ]


def test_revision과_down_revision을_뒤에서_다시_대입하면_잡는다() -> None:
    again = '\nrevision = "9999"\ndown_revision = None\n'
    sources = {**GOOD, "0002_second.py": _file("0002", "0001") + again}
    assert shape_problems(sources) == [
        "0002_second.py: `revision` 이 파일 이름의 번호 0002 와 같은 글자 값이 아니다.",
        "0002_second.py: `down_revision` 을 글자 값(없으면 None)으로 읽지 못했다.",
        "마지막 번호가 하나가 아니다: 0001, 0003",
    ]


def test_파일_이름이_꼴이_아니면_잡는다() -> None:
    sources = {**GOOD, "second.py": _file("0002", "0001"), "__init__.py": ""}
    problems = shape_problems(sources)
    assert any(p.startswith("second.py:") for p in problems)
    assert any(p.startswith("__init__.py:") for p in problems)


def test_글자_값이_아닌_revision은_읽지_못했다고_센다() -> None:
    computed = 'revision = "00" + "02"\ndown_revision = "0001"\n'
    sources = {**GOOD, "0002_second.py": computed}
    assert shape_problems(sources) == [
        "0002_second.py: `revision` 이 파일 이름의 번호 0002 와 같은 글자 값이 아니다."
    ]
