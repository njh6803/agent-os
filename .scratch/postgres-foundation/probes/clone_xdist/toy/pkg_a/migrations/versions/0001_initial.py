"""패키지 A 의 첫 판. 표 셋과 색인 둘이다.

판 번호는 패키지 B 의 첫 판과 일부러 같게 두었다. 두 패키지의 마이그레이션이 한 프로세스에서 차례로
적용돼도 서로의 판 파일을 집지 않는지를 보려는 것이다. 되돌리는 단계(`downgrade`)는 두지 않았다.
"""

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
    op.create_table(
        "login_attempts",
        sa.Column("id", sa.BigInteger, sa.Identity(always=True), primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
    )
