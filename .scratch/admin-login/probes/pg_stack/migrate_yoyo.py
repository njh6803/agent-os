"""표 관리 후보: yoyo-migrations. `migrations/` 의 같은 SQL 파일을 그 라이브러리의 API 로 적용한다.

이 파일은 pyright strict 에서 오류가 나는지를 보려고 타입 검사 대상에 둔다(결과는 README).
"""

from __future__ import annotations

from pathlib import Path

from yoyo import get_backend, read_migrations


def apply(url: str, folder: Path) -> int:
    """적용한 마이그레이션 수를 돌려준다. url 은 `postgresql+psycopg://…` 꼴이다."""
    backend = get_backend(url)
    migrations = read_migrations(str(folder))
    with backend.lock():
        pending = backend.to_apply(migrations)
        count = len(pending)
        backend.apply_migrations(pending)
    return count
