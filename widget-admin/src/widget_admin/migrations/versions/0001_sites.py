"""위젯 관리 마이그레이션 0001: 사이트 표 `sites` 를 만든다(ADR 0064).

사이트 하나가 줄 하나이고, 위젯 설정 열아홉 칸이 각각 한 칸이며 사이트 이름 칸 `name` 이 더해져 스무
칸이다. 이미 dev 에 들어간 파일은 고치지 않고 새 파일을 더한다(운영자의 데이터베이스가 이미 이
파일로 올라가 있을 수 있다). 되돌리는 함수는 두지 않는다. 되돌리는 길은 올리기 전의 백업을 복원하는
것이다.

표가 규칙을 스스로 든다. 이름의 꼴, 빈 글자 금지, 어휘 목록, 예시 질문 항목의 검사가 `CHECK` 이고
이름이 `sites_<칸>_check` 다. 이름의 식은 `widget_admin.settings.SITE_NAME_PATTERN` 과 같은
글자이고, 마이그레이션은 한 번 올라가면 고치지 않으므로 상수를 끌어 쓰지 않고 글자 그대로 적는다. 두
식이 같은 이름을 받는지는 시험이 견준다.
"""

from __future__ import annotations

from alembic import op

revision: str = "0001"
down_revision: str | None = None

_VOCABULARIES = {
    "theme": ("guncheong", "nokcheong", "jacho", "jjokbit"),
    "mode": ("light", "dark"),
    "logout_method": ("background", "new_window"),
    "expiry_notice_style": ("card", "overlay", "banner"),
    "login_prompt_style": ("card", "input_button", "intro_button"),
    "notice_full_style": ("inline", "overlay", "card"),
}
_TEXTS = (
    "agent",
    "heading",
    "intro",
    "placeholder",
    "notice_summary",
    "notice_full",
    "login_url",
    "login_label",
    "logout_url",
    "tab_title",
    "contact_url",
)


def _in_list(column: str, words: tuple[str, ...]) -> str:
    quoted = ", ".join(f"'{word}'" for word in words)
    return f"CHECK ({column} IN ({quoted}))"


def upgrade() -> None:
    """`sites` 표를 만든다."""
    columns = [
        "name text PRIMARY KEY",
        *(f"{column} text" for column in _TEXTS),
        *(f"{column} text" for column in _VOCABULARIES),
        "example_questions text[] NOT NULL DEFAULT '{}'",
        "hide_mode_switch boolean NOT NULL DEFAULT false",
    ]
    constraints = [
        "CONSTRAINT sites_name_check CHECK (name ~ '^[a-z][a-z0-9-]{1,62}$')",
        *(f"CONSTRAINT sites_{column}_check CHECK ({column} <> '')" for column in _TEXTS),
        *(
            f"CONSTRAINT sites_{column}_check {_in_list(column, words)}"
            for column, words in _VOCABULARIES.items()
        ),
        "CONSTRAINT sites_example_questions_check CHECK ("
        "array_position(example_questions, NULL) IS NULL AND '' <> ALL (example_questions))",
    ]
    body = ",\n    ".join([*columns, *constraints])
    op.execute(f"CREATE TABLE sites (\n    {body}\n)")
