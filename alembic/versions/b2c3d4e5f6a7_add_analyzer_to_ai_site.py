"""ai_site 테이블에 analyzer 컬럼 추가

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """analyzer 컬럼 추가."""
    op.add_column('ai_site', sa.Column('analyzer', sa.String(50), nullable=True))


def downgrade() -> None:
    """analyzer 컬럼 제거."""
    op.drop_column('ai_site', 'analyzer')
