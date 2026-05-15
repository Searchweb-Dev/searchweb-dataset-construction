"""ai_site에 unreachable_since 컬럼 추가

Revision ID: 26ef75a2768b
Revises: 26d5b0df2416
Create Date: 2026-05-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '26ef75a2768b'
down_revision: Union[str, Sequence[str], None] = '26d5b0df2416'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'ai_site',
        sa.Column(
            'unreachable_since',
            sa.DateTime(),
            nullable=True,
            comment='400 접근 불가 최초 감지 시각 (UTC). NULL이면 접근 가능 상태.',
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('ai_site', 'unreachable_since')
