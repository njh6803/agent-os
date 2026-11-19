"""시험용 마이그레이션 9001: 표 하나를 만든다. 제품의 폴더 밖이라 휠에 들지 않는다."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "9001"
down_revision: str | None = None


def upgrade() -> None:
    op.create_table("probe_one", sa.Column("id", sa.Integer(), nullable=False))
