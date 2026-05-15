"""ai_site에 status 컬럼 추가

Revision ID: 80b30e8e3a59
Revises: 26ef75a2768b
Create Date: 2026-05-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '80b30e8e3a59'
down_revision: Union[str, Sequence[str], None] = '26ef75a2768b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'ai_site',
        sa.Column(
            'status',
            sa.String(length=20),
            nullable=True,
            comment='분석 상태 (ok / unreachable / blocked / failure). NULL은 미분류.',
        ),
    )
    op.create_index(op.f('ix_ai_site_status'), 'ai_site', ['status'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_ai_site_status'), table_name='ai_site')
    op.drop_column('ai_site', 'status')
