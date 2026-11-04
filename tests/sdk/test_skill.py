"""스킬 문서를 읽는 sdk 함수. 프로브 두 파일(`frontmatter_split.py`, `frontmatter_values.py`)의
사례를 같은 입력으로 시험한다. 규칙의 출처는 `.scratch/skill-plugin/spec.md` 의 "머리말을 본문에서
떼는 규칙" 이하 여섯 절이다.

실패를 기대하는 시험은 실패의 까닭(표지)을 단언한다. 문구에 값이 없는 시험은 값이 있어야 할 양성
대조(`str(error)`)와 함께 본다.
"""

import dataclasses
import traceback

import pytest
import yaml
from pydantic import ValidationError
from yaml.composer import ComposerError
from yaml.scanner import ScannerError

from agent_os.sdk import PluginName, Skill, parse_skill

SECRET = "sk-ant-probe-secret"
NAME = "pdf-processing"
BOM = chr(0xFEFF)
HEAD_LINES = f"name: {NAME}\ndescription: PDF 를 다룬다\n"


def _document(head: str, body: str = "본문\n") -> str:
    return f"---\n{head}---\n{body}"


def _first_error(text: str) -> tuple[str, tuple[int | str, ...]]:
    with pytest.raises(ValidationError) as caught:
        parse_skill(text)
    first = caught.value.errors()[0]
    return first["type"], first["loc"]


def _yaml_failure(head: str) -> Exception:
    """YAML 읽기가 낸 원래 예외. 문구에 값이 있어야 할 양성 대조를 위해 직접 읽어 본다."""
    try:
        yaml.safe_load(head)
    except Exception as error:  # noqa: BLE001 - 어떤 예외가 나는지가 대조의 대상이다
        return error
    raise AssertionError("YAML 이 이 입력을 거부해야 한다")


# ─── 가르기 ──────────────────────────────────────────────────────────────────────

ACCEPTED_SPLITS = [
    pytest.param(
        f"---\n{HEAD_LINES}---\n# 제목\n\n본문이다.\n",
        "# 제목\n\n본문이다.\n",
        id="LF와 본문",
    ),
    pytest.param(
        "---\r\nname: pdf-processing\r\ndescription: PDF 를 다룬다\r\n---\r\n"
        "# 제목\r\n본문이다.\r\n",
        "# 제목\r\n본문이다.\r\n",
        id="CRLF와 본문은 본문의 줄 끝을 그대로 둔다",
    ),
    pytest.param(
        f"---\n{HEAD_LINES}---\n앞\n---\n뒤\n",
        "앞\n---\n뒤\n",
        id="본문 안의 --- 줄은 본문에 남는다",
    ),
    pytest.param(f"---\n{HEAD_LINES}---\n", "", id="본문이 없다"),
    pytest.param(f"---\n{HEAD_LINES}---", "", id="닫는 줄 뒤에 줄 바꿈도 없다"),
]


@pytest.mark.parametrize(("text", "body"), ACCEPTED_SPLITS)
def test_머리말과_본문을_줄_단위로_가른다(text: str, body: str) -> None:
    skill = parse_skill(text)
    assert skill == Skill(name=PluginName(NAME), description="PDF 를 다룬다", body=body)


def test_머리말_값_안의_표지는_값_그대로이고_본문도_그대로다() -> None:
    skill = parse_skill(_document(f"name: {NAME}\ndescription: 가 --- 나\n"))
    assert skill.description == "가 --- 나"
    assert skill.body == "본문\n"


def test_본문은_앞뒤를_다듬지_않는다() -> None:
    skill = parse_skill(_document(HEAD_LINES, "\n  들여쓴 본문  \n\n"))
    assert skill.body == "\n  들여쓴 본문  \n\n"


def test_설명의_앞뒤_공백도_다듬지_않는다() -> None:
    skill = parse_skill(_document(f'name: {NAME}\ndescription: "  가  "\n'))
    assert skill.description == "  가  "


REJECTED_SPLITS = [
    pytest.param(f"---\n{HEAD_LINES}본문\n", "머리말이 닫히지 않았다", id="닫는 줄이 없다"),
    pytest.param(f"{BOM}---\n{HEAD_LINES}---\n", "머리말로 시작하지 않는다", id="BOM으로 시작한다"),
    pytest.param(f"\n---\n{HEAD_LINES}---\n", "머리말로 시작하지 않는다", id="앞에 빈 줄이 있다"),
    pytest.param("# 제목\n본문\n", "머리말로 시작하지 않는다", id="머리말 없이 본문뿐이다"),
    pytest.param(
        f"---\r\r\n{HEAD_LINES}---\n", "머리말로 시작하지 않는다", id="첫 줄 끝의 \\r 이 둘이다"
    ),
    pytest.param(
        "---\rname: pdf-processing\rdescription: PDF\r---\r본문\r",
        "머리말로 시작하지 않는다",
        id="홀로 선 \\r 뿐이다(글을 직접 넘길 때)",
    ),
    pytest.param("", "머리말로 시작하지 않는다", id="빈 글이다"),
]


@pytest.mark.parametrize(("text", "message"), REJECTED_SPLITS)
def test_가를_수_없는_글은_고정_문구의_ValueError다(text: str, message: str) -> None:
    with pytest.raises(ValueError, match=message) as caught:
        parse_skill(text)
    assert not isinstance(caught.value, ValidationError)


def test_빈_머리말은_맵이_아니라서_거부한다() -> None:
    with pytest.raises(ValueError, match="머리말이 맵이 아니다"):
        parse_skill("---\n---\n본문\n")


@pytest.mark.parametrize(
    "head",
    [
        pytest.param("- a\n- b\n", id="목록"),
        pytest.param("그냥 글\n", id="스칼라"),
    ],
)
def test_맵이_아닌_머리말은_거부한다(head: str) -> None:
    with pytest.raises(ValueError, match="머리말이 맵이 아니다"):
        parse_skill(_document(head))


# 머리말 안의 --- 줄(열 0)은 YAML 자체가 문서 시작으로 읽어 거부하므로, 닫는 줄로 삼은 --- 줄이
# 유효한 머리말 안에 있을 수 없다. 규칙이 잃는 유효 입력이 없다는 근거다(프로브 갈래 회차).
MARKER_INSIDE = [
    pytest.param(f'name: {NAME}\ndescription: "앞\n---\n뒤"\n', ScannerError, id="큰따옴표 안"),
    pytest.param(
        f"name: {NAME}\ndescription: |\n  앞\n---\n  뒤\n",
        ComposerError,
        id="블록 안",
    ),
    pytest.param(
        f"name: {NAME}\ndescription: 앞\n---\n  뒤\n",
        ComposerError,
        id="평문의 이어짐",
    ),
]


@pytest.mark.parametrize(("head", "kind"), MARKER_INSIDE)
def test_머리말_안의_표지_줄은_YAML_이_거부한다(head: str, kind: type[Exception]) -> None:
    with pytest.raises(kind):
        yaml.safe_load(head)


WITHOUT_MARKER = [
    pytest.param(f'name: {NAME}\ndescription: "앞\n뒤"\n', "앞 뒤", id="큰따옴표 안"),
    pytest.param(f"name: {NAME}\ndescription: |\n  앞\n  뒤\n", "앞\n뒤\n", id="블록 안"),
    pytest.param(f"name: {NAME}\ndescription: 앞\n  뒤\n", "앞 뒤", id="평문의 이어짐"),
]


@pytest.mark.parametrize(("head", "description"), WITHOUT_MARKER)
def test_같은_자리에서_표지_줄만_빼면_받아들인다(head: str, description: str) -> None:
    assert parse_skill(_document(head)).description == description


def test_파일_전체를_YAML_로_읽으면_거부된다() -> None:
    # 양성 대조: 그래서 YAML 에 넘기기 전에 머리말을 떼는 규칙이 선다.
    with pytest.raises(ComposerError):
        yaml.safe_load(_document(HEAD_LINES))


# ─── 두 칸의 모양 ────────────────────────────────────────────────────────────────


def test_두_칸이_문자열이면_받는다() -> None:
    skill = parse_skill(_document(HEAD_LINES))
    assert (skill.name, skill.description) == (NAME, "PDF 를 다룬다")


def test_표준의_선택_칸과_제품별_키는_무시한다() -> None:
    head = (
        f"name: {NAME}\ndescription: 한 줄\nlicense: MIT\ncompatibility: Requires git\n"
        "metadata:\n  a: b\nallowed-tools: Bash(git:*)\ndisable-model-invocation: true\n"
    )
    skill = parse_skill(_document(head))
    assert skill == Skill(name=PluginName(NAME), description="한 줄", body="본문\n")


def test_접힌_여러_줄_설명을_받는다() -> None:
    skill = parse_skill(_document(f"name: {NAME}\ndescription: >\n  여러 줄\n  설명\n"))
    assert skill.description == "여러 줄 설명\n"


REJECTED_VALUES = [
    pytest.param("name: 123\ndescription: 한 줄\n", "string_type", "name", id="name 이 정수"),
    pytest.param(
        f"name: {NAME}\ndescription: [a, b]\n", "string_type", "description", id="설명이 목록"
    ),
    pytest.param("name: true\ndescription: 한 줄\n", "string_type", "name", id="name 이 불린"),
    pytest.param("name: ~\ndescription: 한 줄\n", "string_type", "name", id="name 이 널"),
    pytest.param(
        "name: 2026-11-03\ndescription: 한 줄\n", "string_type", "name", id="name 이 날짜로 읽힘"
    ),
    pytest.param(
        "name: !!binary aGk=\ndescription: 한 줄\n", "string_type", "name", id="name 이 bytes"
    ),
    pytest.param(
        f"name: {NAME}\ndescription: ''\n", "string_too_short", "description", id="빈 설명"
    ),
    pytest.param(
        f"name: {NAME}\ndescription: '   '\n", "value_error", "description", id="공백뿐인 설명"
    ),
    pytest.param(
        "name: PDF-Processing\ndescription: 한 줄\n",
        "string_pattern_mismatch",
        "name",
        id="name 이 패턴 밖(대문자)",
    ),
    pytest.param(
        "name: a\ndescription: 한 줄\n", "string_pattern_mismatch", "name", id="name 이 한 글자"
    ),
    pytest.param("description: 한 줄\n", "missing", "name", id="name 이 없음"),
    pytest.param(f"name: {NAME}\n", "missing", "description", id="설명이 없음"),
    # 정규화하지 않는다: 한글 이름과 전각 글자 이름은 들어오지 못한다(명세 Out of Scope)
    pytest.param(
        "name: 피디에프\ndescription: 한 줄\n", "string_pattern_mismatch", "name", id="한글 이름"
    ),
    pytest.param(
        "name: ｐｄｆ-ｔｏｏｌ\ndescription: 한 줄\n",
        "string_pattern_mismatch",
        "name",
        id="전각 글자 이름",
    ),
]


@pytest.mark.parametrize(("head", "error_type", "field"), REJECTED_VALUES)
def test_두_칸의_잘못된_값은_ValidationError_이고_까닭을_든다(
    head: str, error_type: str, field: str
) -> None:
    assert _first_error(_document(head)) == (error_type, (field,))


def test_위치가_없는_YAML_오류는_종류만_든다() -> None:
    # ReaderError 는 problem_mark 가 없다. 줄·칸 없이 종류만 싣는다.
    with pytest.raises(ValueError) as caught:
        parse_skill(_document(f"name: {NAME}\ndescription: 한 줄\x00\n"))

    assert str(caught.value) == "머리말이 YAML로 읽히지 않는다: ReaderError"


# ─── 문구에 값이 없다 ────────────────────────────────────────────────────────────

UNCLOSED_QUOTE = f'name: {NAME}\ndescription: 한 줄\nextra: "{SECRET}\n'
UNUSED_TAGGED = f"name: {NAME}\ndescription: 한 줄\nother: !!int {SECRET}\n"

LEAKY_YAML = [
    pytest.param(UNCLOSED_QUOTE, id="닫히지 않은 따옴표"),
    pytest.param(f"name: {NAME}\ndescription: !!int {SECRET}\n", id="!!int 태그"),
    pytest.param(f"name: {NAME}\ndescription: !!float {SECRET}\n", id="!!float 태그"),
    pytest.param(f"name: {NAME}\ndescription: !!bool {SECRET}\n", id="!!bool 태그"),
    pytest.param(UNUSED_TAGGED, id="쓰지 않는 칸의 !!int 태그"),
]


@pytest.mark.parametrize("head", LEAKY_YAML)
def test_YAML_로_읽히지_않는_머리말의_문구에_적은_값이_없다(head: str) -> None:
    # 양성 대조: 원래 예외의 str 에는 값이 있다.
    assert SECRET in str(_yaml_failure(head))
    with pytest.raises(ValueError, match="머리말이 YAML로 읽히지 않는다") as caught:
        parse_skill(_document(head))
    assert SECRET not in str(caught.value)


def test_YAML_가_아닌_예외도_종류만_든_ValueError_로_바뀐다() -> None:
    # !!timestamp 의 변환 실패는 AttributeError 라 YAMLError 로는 잡히지 않는 길이다.
    head = f"name: {NAME}\ndescription: !!timestamp {SECRET}\n"
    assert not isinstance(_yaml_failure(head), yaml.YAMLError)
    with pytest.raises(ValueError) as caught:
        parse_skill(_document(head))
    assert str(caught.value) == "머리말이 YAML로 읽히지 않는다: AttributeError"


def test_YAMLError_가_아닌_ValueError_의_문구는_종류만_든다() -> None:
    with pytest.raises(ValueError) as caught:
        parse_skill(_document(f"name: {NAME}\ndescription: !!int {SECRET}\n"))
    assert str(caught.value) == "머리말이 YAML로 읽히지 않는다: ValueError"


def test_위치가_있는_YAML_오류는_파일_기준_1부터_센_줄과_칸을_든다() -> None:
    # 깨진 줄(값 안의 둘째 콜론)이 파일의 넷째 줄이다: 여는 --- 가 1, name 이 2, description 이 3.
    head = f"name: {NAME}\ndescription: 한 줄\nbad: a: b\n"
    mark = _yaml_failure(head)
    assert isinstance(mark, yaml.MarkedYAMLError)
    assert mark.problem_mark is not None
    assert (mark.problem_mark.line, mark.problem_mark.column) == (2, 6)  # 넘긴 글 기준 0부터
    with pytest.raises(ValueError) as caught:
        parse_skill(_document(head))
    assert str(caught.value) == "머리말이 YAML로 읽히지 않는다: ScannerError (줄 4, 칸 7)"


def test_닫히지_않은_따옴표의_문구에_종류와_줄이_있고_값은_없다() -> None:
    with pytest.raises(ValueError, match=r"ScannerError \(줄 \d+, 칸 \d+\)") as caught:
        parse_skill(_document(UNCLOSED_QUOTE))
    assert SECRET not in str(caught.value)


def test_두_칸의_거부_문구에_적은_값이_없다() -> None:
    with pytest.raises(ValidationError) as caught:
        parse_skill(_document(f"name: {NAME}\ndescription: [{SECRET}]\n"))
    # 양성 대조: pydantic 의 str 에는 값이 있다. 어댑터가 입력 없이 다시 만든다.
    assert SECRET in str(caught.value)
    described = caught.value.errors(include_url=False, include_context=False, include_input=False)
    assert SECRET not in str(described)


@pytest.mark.parametrize("head", LEAKY_YAML)
def test_바꿔_던진_예외는_원래_예외를_잇지_않는다(head: str) -> None:
    with pytest.raises(ValueError, match="머리말이 YAML로 읽히지 않는다") as caught:
        parse_skill(_document(head))
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert SECRET not in "".join(traceback.format_exception(caught.value))


# ─── 값 ─────────────────────────────────────────────────────────────────────────


def test_스킬은_불변이다() -> None:
    skill = parse_skill(_document(HEAD_LINES))
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(skill, "body", "x")  # noqa: B010
    assert [field.name for field in dataclasses.fields(skill)] == ["name", "description", "body"]
