"""표를 만들지 않는 첫 마이그레이션. 되돌리는 단계(`downgrade`)를 두지 않는다."""

from __future__ import annotations

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """만들 표가 없다. 판 기록 표의 줄만 남는다."""
