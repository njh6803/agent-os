"""스킬 문서(`SKILL.md`)를 읽은 값과 읽는 함수(ADR 0041).

스킬은 운영자가 플러그인 폴더(`plugins/skills/<이름>/`)에 둔 문서이고 에이전트가 지시로 엮는 절차
지식이다. 머리말의 두 칸(`name`, `description`)과 본문을 든 불변 값 `Skill` 하나가 플러그인에
보인다.

**신뢰 경계.** 스킬 본문은 운영자가 둔 파일이라 에이전트 코드와 같은 신뢰 수준이다. `Conversation`
의 요약과 요청(최종 사용자의 입력과 같은 수준이라 데이터로 엮는다)과 반대편이다. 에이전트는 본문을
지시로 엮어도 된다. 런타임은 `llm()` 의 프롬프트에 이것을 붙이지 않는다. 프롬프트는 에이전트가
짓는다.

`import yaml` 은 이 모듈만 한다. sdk 밖의 층은 직접 import 하지 못하고(`pyproject.toml` 의
import-linter 계약), 그래서 YAML 읽기가 내는 예외의 타입을 아는 층이 여기 하나다.
"""

from __future__ import annotations

from dataclasses import dataclass

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from agent_os.sdk.ids import PLUGIN_NAME_PATTERN, PluginName

_MARKER = "---"


@dataclass(frozen=True)
class Skill:
    """스킬 문서 하나가 남긴 값. 본문은 머리말 뒤의 글 그대로다(앞뒤를 다듬지 않는다).

    `name` 은 플러그인 이름 패턴을 지난 값이고, 폴더 이름과 같은지는 읽는 쪽이 대 본다.
    """

    name: PluginName
    description: str
    body: str


# 머리말의 두 칸만 보고 나머지 키는 무시한다(표준의 선택 칸과 제품별 키가 그대로 들어온다). strict
# 라 YAML 이 문자열이 아니게 읽은 값(정수, 불린, 널, 날짜, bytes, 목록)은 모두 string_type 으로
# 거부된다. 공개 표면에 올리지 않는다. 플러그인이 쓸 것은 `Skill` 뿐이다.
class _Frontmatter(BaseModel):
    model_config = ConfigDict(strict=True, extra="ignore", frozen=True)

    name: str = Field(pattern=PLUGIN_NAME_PATTERN)
    description: str = Field(min_length=1)

    @field_validator("description")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("description 이 공백뿐이다")
        return value


def parse_skill(text: str) -> Skill:
    """스킬 문서의 글을 머리말과 본문으로 가르고 머리말의 두 칸을 좁혀 값을 만든다.

    실패는 모두 `ValueError` 계열이다. 가르기와 맵 아님은 고정 문구의 `ValueError`, 두 칸은
    pydantic `ValidationError`, YAML 읽기는 `머리말이 YAML로 읽히지 않는다: <오류 종류>` 의
    `ValueError` 다. 가르기와 YAML 읽기의 문구는 머리말에 적은 값을 되울리지 않는다. 두 칸의
    `ValidationError` 문구는 틀린 값을 `input_value` 로 싣는다. 그래서 이 오류를 내보내는 쪽은
    `str(error)` 를 그대로 쓰지 않고 입력 없이 다시 만든다(어댑터의 `_describe` 가 그 예다).
    폴더 이름과의 대조는 이 함수의 몫이 아니다.
    """
    head, body = _split(text)
    loaded = _load(head)
    if not isinstance(loaded, dict):
        raise ValueError("머리말이 맵이 아니다")
    front = _Frontmatter.model_validate(loaded)
    return Skill(name=PluginName(front.name), description=front.description, body=body)


def _is_marker(line: str) -> bool:
    """줄 끝의 `\\r` 하나만 떼고 `---` 그대로인지 본다. `\\r` 이 둘이면 표지 줄이 아니다."""
    return line.removesuffix("\r") == _MARKER


def _split(text: str) -> tuple[str, str]:
    """첫 줄이 `---` 그대로여야 하고, 그 뒤 처음 나오는 `---` 그대로인 줄이 닫는 줄이다.

    줄은 `\\n` 으로 가른다. 머리말은 두 표지 줄 사이의 글 그대로이고(마지막 줄의 줄 바꿈까지 든다.
    블록 스칼라 설명의 끝 개행이 그 줄에 달려 있다) 본문은 닫는 줄의 줄 바꿈 뒤의 글 그대로다. 파일
    전체를 `yaml.safe_load` 에 넘기면 둘째 `---` 가 둘째 문서의 시작이라 거부되므로 YAML 에 넘기기
    전에 이 규칙이 선다. 글자 열로 가르면(`split("---", 2)`) 머리말 값 안의 `---` 에서 끊기므로 줄
    단위다.
    """
    lines = text.split("\n")
    if not _is_marker(lines[0]):
        raise ValueError("머리말로 시작하지 않는다: 첫 줄이 --- 가 아니다")
    head_start = len(lines[0]) + 1
    closing_start = head_start
    for line in lines[1:]:
        if _is_marker(line):
            return text[head_start:closing_start], text[closing_start + len(line) + 1 :]
        closing_start += len(line) + 1
    raise ValueError("머리말이 닫히지 않았다: --- 줄이 없다")


def _load(head: str) -> object:
    """머리말을 YAML 로 읽는다. 읽다 난 어떤 예외든 종류와 줄·칸만 든 `ValueError` 로 바꾼다.

    `yaml.safe_load` 가 내는 예외는 `YAMLError` 만이 아니다. 명시적 태그(`!!int` 등)의 변환 실패는
    변환 함수의 `ValueError`·`KeyError`·`AttributeError` 가 그대로 올라오고, `str` 에 운영자가 적은
    값이 실린다. `MarkedYAMLError` 의 `str` 도 문제 자리의 원문 조각을 싣는다. 그래서 `str(error)`
    와 `problem`·`context` 문구는 어디에도 싣지 않는다.

    원래 예외를 잇지 않는다. `except` 에서는 종류와 줄·칸만 뽑고 `ValueError` 는 그 블록 밖에서
    던진다. 블록 안에서 `from error` 로 이으면 트레이스백 출력에 원래 예외의 `str` 이 실리고,
    `from None` 은 `__context__` 에 원래 예외를 남긴다.
    """
    try:
        return yaml.safe_load(head)
    except Exception as error:  # noqa: BLE001 - 어떤 예외든 같은 문구가 된다
        reason = f"{type(error).__name__}{_position(error)}"
    raise ValueError(f"머리말이 YAML로 읽히지 않는다: {reason}")


def _position(error: Exception) -> str:
    """파일 기준 1부터 센 줄과 칸. `problem_mark.line` 은 넘긴 머리말 기준 0부터라 여는 `---` 줄과
    1부터 세는 몫으로 2를 더한다. 자리가 없으면 빈 글이다."""
    if not isinstance(error, yaml.MarkedYAMLError) or error.problem_mark is None:
        return ""
    mark = error.problem_mark
    return f" (줄 {mark.line + 2}, 칸 {mark.column + 1})"
