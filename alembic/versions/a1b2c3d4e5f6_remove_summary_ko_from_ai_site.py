"""ai_site 테이블에서 summary_ko 컬럼 제거

Revision ID: a1b2c3d4e5f6
Revises: 26d5b0df2416
Create Date: 2026-05-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '26d5b0df2416'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """summary_ko 컬럼 제거."""
    op.drop_column('ai_site', 'summary_ko')


def downgrade() -> None:
    """summary_ko 컬럼 복원."""
    op.add_column('ai_site', sa.Column('summary_ko', sa.Text(), nullable=True))
