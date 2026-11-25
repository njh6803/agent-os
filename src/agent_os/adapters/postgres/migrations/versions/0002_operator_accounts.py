"""제품 마이그레이션 0002: 운영자 계정의 표 여섯과 시스템 관리자에만 거는 유일 색인(admin-login).

표는 운영자 계정, 로그인 한 건, 갱신용 번호, 비밀번호 링크, 서명 키, 로그인 기록이다. 아직 로그인할
길은 없다. 로그인은 뒤 티켓이 들인다.

**줄을 넣거나 바꾸거나 형을 바꾸지 않는다.** 표와 색인을 만들기만 한다. 그래서 이 마이그레이션이
PostgreSQL 의 형 변환 실패나 유일 제약 위반을 내 그 값이 `migrate` 의 기록에 실리는 길이 없다.
앞으로 이 표들의 해시와 키 칸을 건드리는 마이그레이션도 같은 규칙을 지킨다. 해시와 키 칸은 토큰
구실을 하는 값이라, 값을 싣는 실패가 나면 서버가 낸 오류 글에 그 값이 실린다.

**시각을 담는 칸에 기본값(`server_default`)이나 `now()` 를 두지 않는다.** 시각은 `agent_os.http` 가
주입된 시계에서 읽어 넘긴다. 칸의 기본값으로 지으면 시험의 가짜 시계가 그 칸을 움직이지 못해 만료와
유예와 잠금 시간을 잴 수 없다.

표 이름은 모두 `operator_` 로 시작한다. 서명 키의 표는 다섯째라, 그 표와 같은 이름의 표가 미리
있으면 앞의 네 표를 만든 뒤 멈추고 한 트랜잭션이 모두 되돌린다(시험이 그 모양을 고정한다).

이미 dev 에 들어간 파일은 고치지 않고 새 파일을 더한다(운영자의 데이터베이스가 이미 이 파일로 올라가
있을 수 있다). 되돌리는 함수는 두지 않는다. 되돌리는 길은 올리기 전의 백업을 복원하는 것이다.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"


def upgrade() -> None:
    """표 여섯과 시스템 관리자에만 거는 유일 색인을 만든다."""
    op.create_table(
        "operator_accounts",
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("tier", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failures", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("name", name="pk_operator_accounts"),
        sa.CheckConstraint("tier IN ('system_admin', 'admin')", name="ck_operator_accounts_tier"),
    )
    # 단계가 시스템 관리자인 줄에만 건다. 시스템 관리자가 둘 생기지 못하게 데이터베이스가 막는다
    op.create_index(
        "uq_operator_accounts_one_system_admin",
        "operator_accounts",
        ["tier"],
        unique=True,
        postgresql_where=sa.text("tier = 'system_admin'"),
    )
    op.create_table(
        "operator_logins",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account", sa.Text(), nullable=False),
        sa.Column("logged_in_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("refreshed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_operator_logins"),
        sa.ForeignKeyConstraint(
            ["account"], ["operator_accounts.name"], name="fk_operator_logins_account"
        ),
    )
    op.create_index("ix_operator_logins_account", "operator_logins", ["account"])
    op.create_table(
        "operator_refresh_tokens",
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("login_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("token_hash", name="pk_operator_refresh_tokens"),
        sa.ForeignKeyConstraint(
            ["login_id"],
            ["operator_logins.id"],
            name="fk_operator_refresh_tokens_login_id",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_operator_refresh_tokens_login_id", "operator_refresh_tokens", ["login_id"])
    op.create_table(
        "operator_password_links",
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("account", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("token_hash", name="pk_operator_password_links"),
        sa.ForeignKeyConstraint(
            ["account"], ["operator_accounts.name"], name="fk_operator_password_links_account"
        ),
    )
    op.create_index("ix_operator_password_links_account", "operator_password_links", ["account"])
    # 서명 키의 표는 한 줄만 든다. 줄을 넣는 쪽이 `id = 1` 로 넣고 데이터베이스가 둘째 줄을 막는다
    op.create_table(
        "operator_signing_key",
        # 자동 번호(SERIAL)를 끈다. 줄은 늘 `id = 1` 로 넣고 칸에 기본값을 두지 않는다
        sa.Column("id", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("key", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_operator_signing_key"),
        sa.CheckConstraint("id = 1", name="ck_operator_signing_key_one_row"),
        sa.CheckConstraint("octet_length(key) = 32", name="ck_operator_signing_key_32_bytes"),
    )
    op.create_table(
        "operator_login_records",
        sa.Column("seq", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("account", sa.Text(), nullable=True),
        sa.Column("actor", sa.Text(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("seq", name="pk_operator_login_records"),
    )
