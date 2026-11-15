"""표 관리 후보: Alembic. `alembic.ini` 없이 설정을 코드로 짓고 `upgrade head` 를 부른다.

ini 파일을 두지 않는 것은 선행 저장소의 함정 때문이다(`docs/constitution/operations.md` 환경 규약
상세의 "ini 계열은 ASCII 만"). URL 은 설정 객체에만 넣고 파일에 쓰지 않는다. configparser 가 `%` 를
보간 문자로 읽으므로 URL 의 `%` 는 둘로 겹친다.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

HERE = Path(__file__).resolve().parent


def upgrade(url: str, env: str) -> None:
    """env 는 환경 폴더 이름이다(`alembic_sync` 또는 `alembic_async`)."""
    config = Config()
    config.set_main_option("script_location", str(HERE / env))
    config.set_main_option("version_locations", str(HERE / "alembic_versions"))
    config.set_main_option("path_separator", "os")
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    command.upgrade(config, "head")
