"""패키지 B 의 첫 판. 표 둘과 색인 하나다. 판 번호는 패키지 A 의 첫 판과 일부러 같다."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "widgets",
        sa.Column("id", sa.BigInteger, sa.Identity(always=True), primary_key=True),
        sa.Column("slug", sa.Text, nullable=False, unique=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "widget_origins",
        sa.Column("id", sa.BigInteger, sa.Identity(always=True), primary_key=True),
        sa.Column(
            "widget_id",
            sa.BigInteger,
            sa.ForeignKey("widgets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("origin", sa.Text, nullable=False),
    )
    op.create_index("widget_origins_widget", "widget_origins", ["widget_id"])
