"""accounts 와 refresh_tokens. `migrations/` 의 SQL 두 파일과 같은 표를 Alembic 의 op 로 만든다."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.BigInteger, sa.Identity(always=True), primary_key=True),
        sa.Column("name", sa.Text, nullable=False, unique=True),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("failed_attempts", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("accounts_locked_until", "accounts", ["locked_until"])
    op.create_table(
        "refresh_tokens",
        sa.Column("token_hash", sa.LargeBinary, primary_key=True),
        sa.Column(
            "account_id",
            sa.BigInteger,
            sa.ForeignKey("accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("refresh_tokens_account", "refresh_tokens", ["account_id"])


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("accounts")
