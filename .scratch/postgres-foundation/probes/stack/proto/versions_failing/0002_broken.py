"""일부러 실패하는 둘째 마이그레이션. 표 하나를 만든 뒤 예외를 던진다.

올리기가 실패했을 때 판 기록 표의 줄과 만들다 만 표가 어떻게 남는지를 잰다. 예외의 글이
이 파일의 것이면 표를 만드는 문장까지는 돌았다는 표지다.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | None = None
depends_on: str | None = None

BROKEN = "probe: 일부러 실패하는 마이그레이션"


def upgrade() -> None:
    op.create_table("probe_broken", sa.Column("id", sa.Integer, primary_key=True))
    raise RuntimeError(BROKEN)
