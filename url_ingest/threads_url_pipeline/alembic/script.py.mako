"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}


# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    """마이그레이션 업그레이드 로직을 실행한다."""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """마이그레이션 다운그레이드 로직을 실행한다."""
    ${downgrades if downgrades else "pass"}
