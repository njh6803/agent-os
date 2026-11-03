"""머리말의 필수 두 칸을 pydantic 모델로 좁힐 때 무엇을 받고 거부하는지, 그리고 거부 문구와 YAML
오류 문구에 운영자가 적은 값이 새는지를 재는 탐침. 명세가 근거로 든다.

재는 것은 셋이다. (1) 명세가 정한 모양의 pydantic 모델(아래 `Frontmatter`. `strict=True`,
`extra="ignore"`, `name` 은 플러그인 이름 패턴, `description` 은 비지 않은 문자열)이 설치된
pydantic 으로 받고 거부하는 경계. 받는 것 — 두 칸이 문자열인 머리말, 표준의 선택 칸과 제품별 키가
섞인 머리말(무시). 거부하는 것 — `name: 123`, `description: [a, b]`, `name: true`, `name: ~`(널),
`description: ""`, 공백뿐인 `description`, YAML 의 `!!binary` 가 만드는 bytes, 날짜로 읽히는 값,
패턴 밖의 `name`(`PDF-Processing`), 칸이 없음. (2) 양성 대조 — pydantic `ValidationError` 의 `str`
은 받은 값(`input_value`)을 싣고, `errors(include_input=False, include_url=False)` 로 만든 문구에는
그 값이 없다(어댑터 `_describe` 가 매니페스트에 쓰는 길과 같다). (3) 양성 대조 — PyYAML 의
`MarkedYAMLError` 의 `str` 은 문제 자리의 원문 조각을 싣고, `problem_mark` 의 줄·칸만 든 문구에는
없다. 그리고 `problem_mark.line` 이 넘긴 글 기준 0부터 센 줄이라 파일 기준 줄로 옮기려면 여는 `---`
줄만큼 더해야 한다는 것(값을 본다). (4) 갈래 — `yaml.safe_load` 가 내는 예외가 `yaml.YAMLError` 만이
아니라는 것. 명시적 태그(`!!int`, `!!float`, `!!bool`, `!!timestamp`)의 값 변환이 실패하면 변환
함수의 예외(`ValueError`, `KeyError`, `AttributeError`)가 그대로 올라오고, 그 가운데 셋의 `str` 에
운영자가 적은 값이 실린다. 대조로 `!!python/...` 태그는 `ConstructorError`(`YAMLError` 의 하위)다.
그래서 `YAMLError` 만 잡는 층은 그 값을 거르지 못한다. (5) 갈래 — 쓰지 않는 칸의 값도
`yaml.safe_load` 가 만든다. 두 칸 밖의 칸에 적은 명시적 태그(`other: !!int <값>`)의 변환 실패도
같은 `ValueError` 로 올라오고 `str` 에 값이 실린다. 그래서 `extra="ignore"` 로 무시되는 칸이라도
YAML 단계의 실패는 머리말 전체의 거부다. (6) 갈래 — 바꿔 던진 예외에 원래 예외가 남는 자리.
`except` 안에서 `from <원래 예외>` 로 이으면 `traceback.format_exception` 의 출력에 원래 예외의
`str`(값)이 실린다(양성 대조). `from None` 으로 던지면 그 출력에는 값이 없지만 `__context__` 에
원래 예외가 그대로 남아 그 `str` 에 값이 있다. `except` 밖에서 던지면 `__cause__` 와 `__context__`
가 모두 `None` 이다.

표지. 받는 회차는 모델의 두 칸이 기대한 값과 같을 때만 측정이다. 거부 회차는 `ValidationError` 가
났고 첫 오류의 `type` 이 기대한 것과 같을 때만 측정이다. 새는지 보는 회차는 비밀로 둔 값이 `str` 에
있고(양성 대조) 거른 문구에 없을 때만 측정이다. 줄 번호 회차는 깨진 줄(값 안의 둘째 콜론
`bad: a: b`)을 셋째 줄(0부터 2)에 두고 `problem_mark.line` 이 2 일 때만 측정이다. 첫 판은 이 회차를
닫히지 않은 따옴표로 쟀는데 그 오류의 자리는 깨진 줄이 아니라 스트림 끝(넷째 줄)이라 측정 아님으로
끝났다. 그래서 자리가 깨진 줄 위에 있는 오류로 바꿨다. 닫히지 않은 따옴표는 새는지 보는 회차에만
남겼다(그 회차는 줄 번호를 단언하지 않는다). 태그 회차는 기대한 클래스의 예외가 났고 그것이
`yaml.YAMLError` 가 아니며 `str` 에 값이 있는지가 기대와 같을 때만 측정이다. 대조 회차는
`ConstructorError` 가 났을 때만 측정이다. 쓰지 않는 칸 회차는 `ValueError` 가 났고 `YAMLError` 가
아니며 `str` 에 값이 있을 때만 측정이다. 잇기 회차 셋은 첫째가 `__cause__` 가 원래 예외이고
트레이스백 출력에 값이 있을 때만, 둘째가 `__cause__` 가 `None` 이고 `__suppress_context__` 가
참이며 트레이스백 출력에는 값이 없고 `__context__` 의 `str` 에 값이 있을 때만, 셋째가 `__cause__` 와
`__context__` 가 모두 `None` 이고 출력에 값이 없을 때만 측정이다. 셋 모두 바꿔 던진 예외의 `str`
에 값이 없어야 한다.

전제와 못 보는 것. 모델은 이 파일의 `Frontmatter` 이고 명세의 글과 같아야 한다. 구현 티켓이 sdk 에
두는 모델이 이것과 같은지는 그 티켓의 시험이 같은 사례로 잰다. pydantic lax 모드가 `int` 를 `str`
로 받지 않는 것은 재지 않았다 — 명세가 `strict=True` 를 정했으므로 그 모드만 잰다. `description` 의
길이 상한(표준의 1024)은 명세 범위 밖이라 넣지 않았다. 태그 회차의 넷은 PyYAML `SafeConstructor` 가
값을 변환하는 태그 가운데 변환 함수가 자기 예외를 내는 것이고, 다른 태그는 넣지 않았다.
`!!binary` 는 글자 수가 base64 의 길이 규칙에 맞으면 틀린 글자를 버리고 bytes 를 내 YAML 단계에서
거부되지 않고, 맞지 않거나(17자) ASCII 밖 글자가 있으면 `ConstructorError`(`YAMLError` 하위)다
(손으로 봤다. 둘째 판은 "거부되지 않는다"로만 적었다). 둘째 판(셀프 리뷰 뒤)이 (4)를 더했다. 첫
판은 `YAMLError` 가 YAML 거부의 전부라고 전제했고 셀프 리뷰 표준 축이 손으로 쳐 반례를 보였다.
셋째 판(PR 봇 회차 뒤)이 (5)와 (6)을 더했다. PR 봇 CodeRabbit 이 쓰지 않는 칸의 태그 실패도 스킬을
거부하는 것을, claude-review 가 `__cause__` 로 이은 원래 예외가 트레이스백으로 새는 것을 짚었다.
(6)의 잇기 회차 셋은 `safe_load` 의 예외를 바꿔 던지는 자리만 흉내 내고 sdk 의 함수를 부르지
않으며, 트레이스백 출력은 `traceback.format_exception` 하나로만 봤다(`logging.exception` 과 pytest
의 실패 출력은 재지 않았다).

돌리는 법: 저장소 루트에서
`PYTHONUTF8=1 uv run python .scratch/skill-plugin/probes/frontmatter_values.py`
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import pydantic  # noqa: E402
import yaml  # noqa: E402
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator  # noqa: E402
from tools.probe_kit import Rounds  # noqa: E402

from agent_os.sdk.ids import PLUGIN_NAME_PATTERN  # noqa: E402


class Frontmatter(BaseModel):
    """명세의 모양. 두 칸만 보고 나머지 키는 무시한다. strict 라 문자열만 문자열이다."""

    model_config = ConfigDict(extra="ignore", frozen=True, strict=True)

    name: str = Field(pattern=PLUGIN_NAME_PATTERN)
    description: str = Field(min_length=1)

    @field_validator("description")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("description 이 공백뿐이다")
        return value


SECRET = "sk-ant-probe-secret"
NAME = "pdf-processing"

ACCEPTED: list[tuple[str, str, str]] = [
    ("두 칸이 문자열", f"name: {NAME}\ndescription: PDF 를 다룬다\n", "PDF 를 다룬다"),
    (
        "선택 칸과 제품별 키는 무시",
        f"name: {NAME}\ndescription: 한 줄\nlicense: MIT\ncompatibility: Requires git\n"
        "metadata:\n  a: b\nallowed-tools: Bash(git:*)\ndisable-model-invocation: true\n",
        "한 줄",
    ),
    ("접힌 여러 줄 설명", f"name: {NAME}\ndescription: >\n  여러 줄\n  설명\n", "여러 줄 설명\n"),
]

REJECTED: list[tuple[str, str, str]] = [
    ("name 이 정수", "name: 123\ndescription: 한 줄\n", "string_type"),
    ("description 이 목록", f"name: {NAME}\ndescription: [a, b]\n", "string_type"),
    ("name 이 불린", "name: true\ndescription: 한 줄\n", "string_type"),
    ("name 이 널", "name: ~\ndescription: 한 줄\n", "string_type"),
    ("name 이 날짜로 읽힘", "name: 2026-11-03\ndescription: 한 줄\n", "string_type"),
    ("name 이 !!binary 의 bytes", "name: !!binary aGk=\ndescription: 한 줄\n", "string_type"),
    ("description 이 빈 문자열", f"name: {NAME}\ndescription: ''\n", "string_too_short"),
    ("description 이 공백뿐", f"name: {NAME}\ndescription: '   '\n", "value_error"),
    (
        "name 이 패턴 밖(대문자)",
        "name: PDF-Processing\ndescription: 한 줄\n",
        "string_pattern_mismatch",
    ),
    ("name 이 패턴 밖(한 글자)", "name: a\ndescription: 한 줄\n", "string_pattern_mismatch"),
    ("name 이 없음", "description: 한 줄\n", "missing"),
    ("description 이 없음", f"name: {NAME}\n", "missing"),
]

LEAKY = f"name: {NAME}\ndescription: [{SECRET}]\n"
BROKEN = f'name: {NAME}\ndescription: 한 줄\nextra: "{SECRET}\n'
MAPPING_IN_VALUE = f"name: {NAME}\ndescription: 한 줄\nbad: a: b\n"

# (태그, 기대한 예외 클래스 이름, str 에 값이 실리는지)
TAGGED: list[tuple[str, str, bool]] = [
    ("!!int", "ValueError", True),
    ("!!float", "ValueError", True),
    ("!!bool", "KeyError", True),
    ("!!timestamp", "AttributeError", False),
]
PYTHON_TAG = f"name: {NAME}\ndescription: !!python/name:os.system\n"
# 두 칸은 멀쩡하고 쓰지 않는 칸에만 변환이 실패하는 태그가 있다.
UNUSED_TAGGED = f"name: {NAME}\ndescription: 한 줄\nother: !!int {SECRET}\n"
FIXED_MESSAGE = "머리말이 YAML로 읽히지 않는다: ValueError"


def describe(error: ValidationError) -> str:
    """어댑터 `_describe` 와 같은 길. 입력·문맥·URL 없이 종류와 위치와 문구만."""
    details = error.errors(include_url=False, include_context=False, include_input=False)
    return "; ".join(
        f"{d['type']} ({'.'.join(str(p) for p in d['loc'])}): {d['msg']}" for d in details
    )


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    rounds = Rounds()

    with rounds.round("설치된 판") as current:
        if "site-packages" in Path(pydantic.__file__).parts:
            current.mark(
                measured=True, result=f"pydantic {pydantic.VERSION}, pyyaml {yaml.__version__}"
            )

    for label, text, description in ACCEPTED:
        with rounds.round(f"받음: {label}") as current:
            parsed = Frontmatter.model_validate(yaml.safe_load(text))
            if parsed.name == NAME and parsed.description == description:
                current.mark(measured=True, result="두 칸이 기대한 값")

    for label, text, error_type in REJECTED:
        with rounds.round(f"거부: {label}") as current:
            try:
                Frontmatter.model_validate(yaml.safe_load(text))
            except ValidationError as error:
                first = error.errors()[0]
                if first["type"] == error_type:
                    current.mark(
                        measured=True, result=f"{error_type} ({'.'.join(map(str, first['loc']))})"
                    )

    with rounds.round(
        "양성 대조: ValidationError 의 str 은 값을 싣고 거른 문구는 싣지 않는다"
    ) as current:
        try:
            Frontmatter.model_validate(yaml.safe_load(LEAKY))
        except ValidationError as error:
            if SECRET in str(error) and SECRET not in describe(error):
                current.mark(measured=True, result=f"str 에 있음, 거른 문구 '{describe(error)}'")

    with rounds.round(
        "양성 대조: MarkedYAMLError 의 str 은 원문 조각을 싣고 줄·칸 문구는 싣지 않는다"
    ) as current:
        try:
            yaml.safe_load(BROKEN)
        except yaml.MarkedYAMLError as error:
            mark = error.problem_mark
            if mark is not None:
                terse = f"{type(error).__name__} (줄 {mark.line + 1}, 칸 {mark.column + 1})"
                if SECRET in str(error) and SECRET not in terse:
                    current.mark(measured=True, result=f"str 에 있음, 줄·칸 문구 '{terse}'")

    with rounds.round("problem_mark.line 은 넘긴 글 기준 0부터다") as current:
        try:
            yaml.safe_load(MAPPING_IN_VALUE)
        except yaml.MarkedYAMLError as error:
            mark = error.problem_mark
            if mark is not None and mark.line == 2:
                current.mark(
                    measured=True,
                    result=f"line={mark.line} (셋째 줄이 깨졌다), column={mark.column}",
                )

    for tag, expected, leaks in TAGGED:
        with rounds.round(f"갈래: 명시적 태그의 변환 실패는 YAMLError 가 아니다: {tag}") as current:
            try:
                yaml.safe_load(f"name: {NAME}\ndescription: {tag} {SECRET}\n")
            except Exception as error:  # noqa: BLE001 - 어떤 예외가 나는지가 측정이다
                is_yaml = isinstance(error, yaml.YAMLError)
                if type(error).__name__ == expected and not is_yaml:
                    if (SECRET in str(error)) == leaks:
                        where = "있음" if leaks else "없음"
                        current.mark(
                            measured=True,
                            result=f"{expected} (YAMLError 아님), str 에 값 {where}",
                        )

    with rounds.round("대조: !!python 태그는 ConstructorError(YAMLError 의 하위)다") as current:
        try:
            yaml.safe_load(PYTHON_TAG)
        except yaml.constructor.ConstructorError as error:
            current.mark(measured=True, result=f"거부 {type(error).__name__}")

    with rounds.round(
        "갈래: 쓰지 않는 칸의 명시적 태그 변환 실패도 safe_load 에서 난다"
    ) as current:
        try:
            yaml.safe_load(UNUSED_TAGGED)
        except Exception as error:  # noqa: BLE001 - 어떤 예외가 나는지가 측정이다
            is_yaml = isinstance(error, yaml.YAMLError)
            if isinstance(error, ValueError) and not is_yaml and SECRET in str(error):
                current.mark(measured=True, result="ValueError (YAMLError 아님), str 에 값 있음")

    with rounds.round(
        "양성 대조: except 안에서 from error 로 이으면 트레이스백 출력에 원래 예외의 값이 실린다"
    ) as current:
        try:
            try:
                yaml.safe_load(UNUSED_TAGGED)
            except Exception as error:  # noqa: BLE001 - 둘째 판의 명세가 정한 잇기다
                raise ValueError(FIXED_MESSAGE) from error
        except ValueError as wrapped:
            printed = "".join(traceback.format_exception(wrapped))
            cause = wrapped.__cause__
            if cause is not None and SECRET in str(cause) and SECRET not in str(wrapped):
                if SECRET in printed:
                    current.mark(
                        measured=True, result="__cause__ 에 원래 예외, 트레이스백 출력에 값 있음"
                    )

    with rounds.round(
        "갈래: except 안에서 from None 으로 던지면 __context__ 에 원래 예외가 남는다"
    ) as current:
        try:
            try:
                yaml.safe_load(UNUSED_TAGGED)
            except Exception:  # noqa: BLE001 - 바꿔 던지는 자리를 흉내 낸다
                raise ValueError(FIXED_MESSAGE) from None
        except ValueError as wrapped:
            printed = "".join(traceback.format_exception(wrapped))
            context = wrapped.__context__
            hidden = wrapped.__cause__ is None and wrapped.__suppress_context__
            if hidden and context is not None and SECRET in str(context):
                if SECRET not in str(wrapped) and SECRET not in printed:
                    current.mark(
                        measured=True,
                        result="__cause__ None, 출력에 값 없음, __context__ 에 원래 예외(값 있음)",
                    )

    with rounds.round(
        "고친 길: except 밖에서 던지면 __cause__ 와 __context__ 가 모두 None 이다"
    ) as current:
        kind: str | None = None
        try:
            yaml.safe_load(UNUSED_TAGGED)
        except Exception as error:  # noqa: BLE001 - 종류만 뽑는다
            kind = type(error).__name__
        if kind is not None:
            try:
                raise ValueError(f"머리말이 YAML로 읽히지 않는다: {kind}")
            except ValueError as wrapped:
                printed = "".join(traceback.format_exception(wrapped))
                if wrapped.__cause__ is None and wrapped.__context__ is None:
                    if SECRET not in str(wrapped) and SECRET not in printed:
                        current.mark(
                            measured=True, result="__cause__ None, __context__ None, 출력에 값 없음"
                        )

    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
