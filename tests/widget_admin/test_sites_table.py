"""표 `sites` 가 스스로 드는 규칙과 마이그레이션 `0001_sites`(명세 widget-admin-server "표",
"마이그레이션과 표를 올리는 때").

규칙은 응용 코드가 아니라 표의 `CHECK` 와 기본키가 든다. 표를 직접 만지는 손(SQL 콘솔, 다른
도구)이 규칙을 어길 수 없다는 것을 진짜 데이터베이스에 SQL 을 넣어 보인다.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from tests.postgres_support import plain
from tests.widget_admin.support import FULL_SETTINGS, insert_site
from tools.database_for_tests import ScopedDatabase

from widget_admin.database import PRODUCT_VERSIONS, WidgetAdminDatabase
from widget_admin.settings import SITE_NAME_PATTERN, is_site_name

FIRST_MIGRATION = Path(PRODUCT_VERSIONS) / "0001_sites.py"


async def _rejected_constraint(
    database: ScopedDatabase, name: str, settings: dict[str, object]
) -> str:
    """넣기가 거절된 제약의 이름. 거절되지 않으면 시험이 실패한다."""
    with pytest.raises(IntegrityError) as raised:
        await insert_site(database, name, settings)
    return str(raised.value.orig)


@pytest.mark.parametrize(
    "name", ["Acme", "a", "a" * 64, "1acme", "-acme", "acme_site", "한글", "acme\n", ""]
)
async def test_꼴이_틀린_이름은_표가_거절한다(database: ScopedDatabase, name: str) -> None:
    message = await _rejected_constraint(database, name, {})

    assert "sites_name_check" in message


async def test_같은_이름은_표에_하나뿐이다(database: ScopedDatabase) -> None:
    await insert_site(database, "acme")

    message = await _rejected_constraint(database, "acme", {})

    assert "sites_pkey" in message


@pytest.mark.parametrize(
    "column",
    [
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
    ],
)
async def test_글_칸의_빈_글자는_표가_거절한다(database: ScopedDatabase, column: str) -> None:
    message = await _rejected_constraint(database, "acme", {column: ""})

    assert f"sites_{column}_check" in message


@pytest.mark.parametrize(
    ("column", "outside"),
    [
        ("theme", "red"),
        ("mode", "auto"),
        ("logout_method", "popup"),
        ("expiry_notice_style", "toast"),
        ("login_prompt_style", "modal"),
        ("notice_full_style", "tooltip"),
        ("theme", ""),
    ],
)
async def test_어휘_밖의_글은_표가_거절한다(
    database: ScopedDatabase, column: str, outside: str
) -> None:
    message = await _rejected_constraint(database, "acme", {column: outside})

    assert f"sites_{column}_check" in message


@pytest.mark.parametrize("questions", [["좋은 질문", ""], ["첫째", None]])
async def test_예시_질문의_빈_항목과_널_항목은_표가_거절한다(
    database: ScopedDatabase, questions: list[str | None]
) -> None:
    message = await _rejected_constraint(database, "acme", {"example_questions": questions})

    assert "sites_example_questions_check" in message


async def test_넣지_않은_칸의_기본값은_널과_빈_목록과_거짓이다(database: ScopedDatabase) -> None:
    await insert_site(database, "acme")

    async with plain(database) as connection:
        result = await connection.execute(
            text("SELECT theme, example_questions, hide_mode_switch FROM sites")
        )
        theme, questions, hidden = result.one()

    assert (theme, questions, hidden) == (None, [], False)


async def test_모든_칸을_채운_줄도_들어간다(database: ScopedDatabase) -> None:
    await insert_site(database, "acme", FULL_SETTINGS)


def test_파이썬의_이름_꼴과_표의_이름_꼴은_같은_이름을_받는다() -> None:
    # 표의 식은 마이그레이션이 글자 그대로 든다. 두 식이 갈리면 읽는 쪽은 맞다고 보고 묻는데 표는
    # 거절했을 이름(또는 반대)이 생긴다. 마이그레이션 파일의 식과 설정의 식이 같은 글자인지 본다.
    source = FIRST_MIGRATION.read_text(encoding="utf-8")
    found = re.search(r"CHECK \(name ~ '([^']+)'\)", source)

    assert found is not None
    assert found.group(1) == SITE_NAME_PATTERN


@pytest.mark.parametrize(
    "name", ["ab", "a1", "acme-site", "a" * 63, "a-1-b", "a" * 64, "A", "ab\n", "a_b", "a-"]
)
async def test_읽는_쪽의_꼴_판정과_표의_꼴_판정은_같은_이름을_받는다(
    database: ScopedDatabase, name: str
) -> None:
    try:
        await insert_site(database, name)
        accepted_by_table = True
    except (IntegrityError, DBAPIError):
        accepted_by_table = False

    assert accepted_by_table == is_site_name(name)


async def test_마이그레이션을_다시_올려도_그대로다(
    database: ScopedDatabase, opened: WidgetAdminDatabase
) -> None:
    await insert_site(database, "acme")

    await opened.migrate()

    async with plain(database) as connection:
        versions = (await connection.execute(text("SELECT version_num FROM alembic_version"))).all()
        names = (await connection.execute(text("SELECT name FROM sites"))).all()
    assert [row[0] for row in versions] == ["0001"]
    assert [row[0] for row in names] == ["acme"]
