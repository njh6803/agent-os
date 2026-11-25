"""위젯 설정의 모양과 사이트 이름의 꼴(ADR 0064).

이 모듈의 모델이 `GET /widget-settings/<사이트 이름>` 의 성공 응답이고, 계약 파일
(`widget-admin/openapi.json`) 의 스키마가 여기서 나온다. 모델의 독스트링은 한 줄로 쓴다. pydantic 이
그것을 스키마의 `description` 으로 계약 파일에 그대로 싣기 때문이다. 논증은 `#` 주석에 둔다.

칸 이름과 값의 어휘는 명세(`.scratch/widget-admin-server/spec.md` 의 "답의 모양")가 정했다. 서버는
값을 바꾸지 않고 표에서 읽은 대로 싣는다. 값이 없는 칸은 `null` 이고, 예시 질문은 빈 목록, 밝기
스위치 숨기기는 거짓이다.
"""

from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

# 사이트 이름의 꼴. 소문자로 시작하고 소문자·숫자·붙임표로 2자 이상 63자 이하다. 표의 `CHECK` 와
# 마이그레이션이 같은 식을 글자 그대로 들고, 시험이 두 식이 같은 이름을 받는지 견준다. 읽는 쪽은
# `re.fullmatch` 로 본다. `$` 는 끝의 줄바꿈 앞에서도 맞는데 `fullmatch` 는 맞지 않는다.
SITE_NAME_PATTERN = r"^[a-z][a-z0-9-]{1,62}$"
_SITE_NAME = re.compile(SITE_NAME_PATTERN)

# 이 판의 응답 형식 번호. 위젯이 이 번호로 응답을 읽는 방식을 정한다. 형식이 바뀌면 이 번호를
# 올린다.
SCHEMA_VERSION = 1


def is_site_name(text: str) -> bool:
    """사이트 이름의 꼴에 맞는가(질의)."""
    return _SITE_NAME.fullmatch(text) is not None


class Theme(StrEnum):
    """위젯의 색 이름."""

    GUNCHEONG = "guncheong"
    NOKCHEONG = "nokcheong"
    JACHO = "jacho"
    JJOKBIT = "jjokbit"


class Mode(StrEnum):
    """위젯의 밝기."""

    LIGHT = "light"
    DARK = "dark"


class LogoutMethod(StrEnum):
    """로그아웃 주소를 부르는 방법."""

    BACKGROUND = "background"
    NEW_WINDOW = "new_window"


class ExpiryNoticeStyle(StrEnum):
    """로그인 만료 안내를 보이는 모양."""

    CARD = "card"
    OVERLAY = "overlay"
    BANNER = "banner"


class LoginPromptStyle(StrEnum):
    """로그인 전의 모양."""

    CARD = "card"
    INPUT_BUTTON = "input_button"
    INTRO_BUTTON = "intro_button"


class NoticeFullStyle(StrEnum):
    """고지 전문을 보이는 모양."""

    INLINE = "inline"
    OVERLAY = "overlay"
    CARD = "card"


# 칸의 순서가 응답의 열쇠 순서다. 표의 칸 이름과 같은 글자이고, 질의는 이 목록으로 칸을 이름으로
# 골라 읽는다(`SELECT *` 가 아니다). 표에 칸이 더 생겨도 응답에 새지 않는다.
COLUMNS = (
    "agent",
    "heading",
    "intro",
    "theme",
    "mode",
    "placeholder",
    "notice_summary",
    "notice_full",
    "login_url",
    "login_label",
    "logout_url",
    "logout_method",
    "expiry_notice_style",
    "tab_title",
    "contact_url",
    "example_questions",
    "hide_mode_switch",
    "login_prompt_style",
    "notice_full_style",
)


# `schema_version` 에 기본값도 const 도 enum 도 두지 않는다. 기본값이 있으면 스키마의 required 에서
# 빠져 생성 클라이언트가 선택 필드로 받고, const 나 enum 이면 형식이 올라갈 때 계약 파일의 모양이
# 바뀐다.
class WidgetSettings(BaseModel):
    """사이트의 위젯 설정. 값이 없으면 null, 예시 질문은 빈 목록, 밝기 스위치 숨기기는 거짓이다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: int
    agent: str | None
    heading: str | None
    intro: str | None
    theme: Theme | None
    mode: Mode | None
    placeholder: str | None
    notice_summary: str | None
    notice_full: str | None
    login_url: str | None
    login_label: str | None
    logout_url: str | None
    logout_method: LogoutMethod | None
    expiry_notice_style: ExpiryNoticeStyle | None
    tab_title: str | None
    contact_url: str | None
    example_questions: tuple[str, ...]
    hide_mode_switch: bool
    login_prompt_style: LoginPromptStyle | None
    notice_full_style: NoticeFullStyle | None
