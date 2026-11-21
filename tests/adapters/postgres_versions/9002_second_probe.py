"""시험용 마이그레이션 9002: 표 하나를 더 만든다."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "9002"
down_revision: str | None = "9001"


def upgrade() -> None:
    op.create_table("probe_two", sa.Column("id", sa.Integer(), nullable=False))
