"""create initial tables

Revision ID: 0001_create_tables
Revises:
Create Date: 2026-04-07
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_create_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """초기 스키마(posts/extracted_urls/extracted_tools)를 생성한다."""
    # posts:
    # 키워드 검색으로 수집한 원본 게시글을 저장하는 기준 테이블.
    # platform_post_id를 유니크 키로 사용해 중복 수집을 방지한다.
    op.create_table(
        "posts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("platform_post_id", sa.String(length=255), nullable=False),
        sa.Column("keyword", sa.String(length=255), nullable=False),
        sa.Column("author_handle", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("raw_json", sa.JSON(), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("platform_post_id"),
    )
    op.create_index("ix_posts_keyword", "posts", ["keyword"], unique=False)
    op.create_index("ix_posts_author_handle", "posts", ["author_handle"], unique=False)
    op.create_index("ix_posts_collected_at", "posts", ["collected_at"], unique=False)

    # extracted_urls:
    # 게시글 본문에서 추출한 URL과 정규화 결과를 저장한다.
    # 같은 게시글(post_id)에서 동일 raw_url이 중복 저장되지 않도록 제약을 둔다.
    op.create_table(
        "extracted_urls",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("raw_url", sa.String(length=2048), nullable=False),
        sa.Column("normalized_url", sa.String(length=2048), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_id", "raw_url", name="uq_extracted_urls_post_raw"),
    )
    op.create_index("ix_extracted_urls_domain", "extracted_urls", ["domain"], unique=False)

    # extracted_tools:
    # URL이 없는 게시글 등을 위해 보조적으로 추출한 툴/서비스명 후보를 저장한다.
    # 같은 게시글(post_id)에서 동일 normalized_tool_name 중복을 방지한다.
    op.create_table(
        "extracted_tools",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("tool_name", sa.String(length=255), nullable=False),
        sa.Column("normalized_tool_name", sa.String(length=255), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_id", "normalized_tool_name", name="uq_extracted_tools_post_normalized_name"),
    )
    op.create_index("ix_extracted_tools_name", "extracted_tools", ["normalized_tool_name"], unique=False)


def downgrade() -> None:
    """업그레이드에서 생성한 테이블/인덱스를 역순으로 제거한다."""
    # 업그레이드 시 생성한 의존성 역순으로 제거한다.
    op.drop_index("ix_extracted_tools_name", table_name="extracted_tools")
    op.drop_table("extracted_tools")
    op.drop_index("ix_extracted_urls_domain", table_name="extracted_urls")
    op.drop_table("extracted_urls")
    op.drop_index("ix_posts_collected_at", table_name="posts")
    op.drop_index("ix_posts_author_handle", table_name="posts")
    op.drop_index("ix_posts_keyword", table_name="posts")
    op.drop_table("posts")
