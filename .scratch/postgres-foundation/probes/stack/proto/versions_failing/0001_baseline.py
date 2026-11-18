"""`versions_failing` 의 첫 마이그레이션. `migrations/versions/0001_baseline.py` 와 몸이 같다."""

from __future__ import annotations

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """만들 표가 없다. 판 기록 표의 줄만 남는다."""
