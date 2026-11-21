"""`migrations/versions/0001_baseline.py` 와 같은 번호. 다음 판의 마이그레이션 묶음을 흉내 낸다."""

from __future__ import annotations

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """만들 표가 없다."""
