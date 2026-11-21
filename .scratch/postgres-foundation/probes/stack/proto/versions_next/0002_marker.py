"""둘째 마이그레이션. 표 하나를 만든다. 0001 까지 올린 데이터베이스가 뒤처진 상태가 되게 한다."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table("probe_marker", sa.Column("id", sa.Integer, primary_key=True))
