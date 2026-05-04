"""init: create all tables

Revision ID: 2475942fca07
Revises: 
Create Date: 2026-05-04 16:35:09.460075

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2475942fca07'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Member table
    op.create_table(
        'member',
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('login_id', sa.String(length=50), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('member_name', sa.String(length=20), nullable=False),
        sa.Column('job', sa.String(length=20), nullable=True),
        sa.Column('major', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_member_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_member_id', sa.Integer(), nullable=True),
        sa.Column('deleted_by_member_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('member_id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('login_id'),
    )
    op.create_index('idx_member_status', 'member', ['status'])
    op.create_index('idx_member_created_at', 'member', ['created_at'])

    # 2. OAuthMember table
    op.create_table(
        'oauth_member',
        sa.Column('oauth_member_id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=30), nullable=False),
        sa.Column('provider_member_key', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_member_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_member_id', sa.Integer(), nullable=True),
        sa.Column('deleted_by_member_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('oauth_member_id'),
        sa.UniqueConstraint('provider', 'provider_member_key', name='uq_oauth_provider_key'),
    )
    op.create_index('idx_oauth_member_id', 'oauth_member', ['member_id'])

    # 3. CategoryMaster table
    op.create_table(
        'category_master',
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('parent_category_id', sa.Integer(), nullable=True),
        sa.Column('category_name', sa.String(length=80), nullable=False),
        sa.Column('category_level', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_member_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_member_id', sa.Integer(), nullable=True),
        sa.Column('deleted_by_member_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('category_id'),
    )
    op.create_index('idx_category_is_active', 'category_master', ['is_active'])
    op.create_index('idx_category_level', 'category_master', ['category_level'])
    op.create_index('idx_category_parent', 'category_master', ['parent_category_id'])

    # 4. MemberFolder table
    op.create_table(
        'member_folder',
        sa.Column('member_folder_id', sa.Integer(), nullable=False),
        sa.Column('owner_member_id', sa.Integer(), nullable=False),
        sa.Column('parent_folder_id', sa.Integer(), nullable=True),
        sa.Column('folder_name', sa.String(length=80), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_member_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_member_id', sa.Integer(), nullable=True),
        sa.Column('deleted_by_member_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('member_folder_id'),
    )
    op.create_index('idx_member_folder_owner', 'member_folder', ['owner_member_id'])
    op.create_index('idx_member_folder_parent', 'member_folder', ['parent_folder_id'])

    # 5. MemberTag table
    op.create_table(
        'member_tag',
        sa.Column('member_tag_id', sa.Integer(), nullable=False),
        sa.Column('owner_member_id', sa.Integer(), nullable=False),
        sa.Column('tag_name', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_member_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_member_id', sa.Integer(), nullable=True),
        sa.Column('deleted_by_member_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('member_tag_id'),
        sa.UniqueConstraint('owner_member_id', 'tag_name', name='uq_member_tag_owner_name'),
    )
    op.create_index('idx_member_tag_owner', 'member_tag', ['owner_member_id'])

    # 6. Link table
    op.create_table(
        'link',
        sa.Column('link_id', sa.Integer(), nullable=False),
        sa.Column('canonical_url', sa.String(), nullable=False, unique=True),
        sa.Column('original_url', sa.String(), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('thumbnail_url', sa.String(), nullable=True),
        sa.Column('favicon_url', sa.String(), nullable=True),
        sa.Column('content_type', sa.String(length=30), nullable=False),
        sa.Column('primary_category_id', sa.Integer(), nullable=False),
        sa.Column('category_score', sa.Float(), nullable=True),
        sa.Column('classifier_version', sa.String(length=50), nullable=True),
        sa.Column('categorized_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_member_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_member_id', sa.Integer(), nullable=True),
        sa.Column('deleted_by_member_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('link_id'),
    )
    op.create_index('idx_link_canonical_url', 'link', ['canonical_url'])
    op.create_index('idx_link_domain', 'link', ['domain'])
    op.create_index('idx_link_category', 'link', ['primary_category_id'])
    op.create_index('idx_link_created_at', 'link', ['created_at'])

    # 7. MemberSavedLink table
    op.create_table(
        'member_saved_link',
        sa.Column('member_saved_link_id', sa.Integer(), nullable=False),
        sa.Column('link_id', sa.Integer(), nullable=False),
        sa.Column('link_enrichment_id', sa.Integer(), nullable=True),
        sa.Column('member_folder_id', sa.Integer(), nullable=False),
        sa.Column('display_title', sa.String(length=255), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('primary_category_id', sa.Integer(), nullable=True),
        sa.Column('category_source', sa.String(length=10), nullable=False),
        sa.Column('category_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_member_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_member_id', sa.Integer(), nullable=True),
        sa.Column('deleted_by_member_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('member_saved_link_id'),
    )
    op.create_index('idx_member_saved_link_folder', 'member_saved_link', ['member_folder_id'])
    op.create_index('idx_member_saved_link_link', 'member_saved_link', ['link_id'])

    # 8. MemberSavedLinkTag table
    op.create_table(
        'member_saved_link_tag',
        sa.Column('member_saved_link_tag_id', sa.Integer(), nullable=False),
        sa.Column('member_saved_link_id', sa.Integer(), nullable=False),
        sa.Column('member_tag_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('member_saved_link_tag_id'),
        sa.UniqueConstraint('member_saved_link_id', 'member_tag_id', name='uq_saved_link_tag'),
    )
    op.create_index('idx_member_saved_link_tag_link', 'member_saved_link_tag', ['member_saved_link_id'])
    op.create_index('idx_member_saved_link_tag_tag', 'member_saved_link_tag', ['member_tag_id'])

    # 9. MemberFolderTag table
    op.create_table(
        'member_folder_tag',
        sa.Column('member_folder_tag_id', sa.Integer(), nullable=False),
        sa.Column('member_folder_id', sa.Integer(), nullable=False),
        sa.Column('member_tag_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('member_folder_tag_id'),
        sa.UniqueConstraint('member_folder_id', 'member_tag_id', name='uq_folder_tag'),
    )
    op.create_index('idx_member_folder_tag_folder', 'member_folder_tag', ['member_folder_id'])
    op.create_index('idx_member_folder_tag_tag', 'member_folder_tag', ['member_tag_id'])

    # 10. FolderSuggestionRule table
    op.create_table(
        'folder_suggestion_rule',
        sa.Column('folder_suggestion_rule_id', sa.Integer(), nullable=False),
        sa.Column('scope_type', sa.String(length=10), nullable=False),
        sa.Column('owner_member_id', sa.Integer(), nullable=True),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('member_folder_id', sa.Integer(), nullable=True),
        sa.Column('team_folder_id', sa.Integer(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_member_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_member_id', sa.Integer(), nullable=True),
        sa.Column('deleted_by_member_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('folder_suggestion_rule_id'),
    )
    op.create_index('idx_suggestion_scope', 'folder_suggestion_rule', ['scope_type'])
    op.create_index('idx_suggestion_category', 'folder_suggestion_rule', ['category_id'])
    op.create_index('idx_suggestion_owner', 'folder_suggestion_rule', ['owner_member_id'])

    # 11. LinkEnrichment table
    op.create_table(
        'link_enrichment',
        sa.Column('link_enrichment_id', sa.Integer(), nullable=False),
        sa.Column('link_id', sa.Integer(), nullable=False),
        sa.Column('request_url', sa.String(), nullable=False),
        sa.Column('final_url', sa.String(), nullable=True),
        sa.Column('fetch_status', sa.String(length=20), nullable=False),
        sa.Column('classify_status', sa.String(length=20), nullable=False),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_attempt_at', sa.DateTime(), nullable=True),
        sa.Column('error_code', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('http_status', sa.Integer(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('selected_site_name', sa.String(length=255), nullable=True),
        sa.Column('selected_title', sa.Text(), nullable=True),
        sa.Column('selected_description', sa.Text(), nullable=True),
        sa.Column('fetched_at', sa.DateTime(), nullable=True),
        sa.Column('predicted_category_id', sa.Integer(), nullable=True),
        sa.Column('predicted_score', sa.Float(), nullable=True),
        sa.Column('classifier_version', sa.String(length=50), nullable=True),
        sa.Column('classified_at', sa.DateTime(), nullable=True),
        sa.Column('keyword_extractor_version', sa.String(length=50), nullable=True),
        sa.Column('keyword_source', sa.String(length=30), nullable=True),
        sa.Column('keyword_extracted_at', sa.DateTime(), nullable=True),
        sa.Column('suggested_member_folder_id', sa.Integer(), nullable=True),
        sa.Column('suggested_team_folder_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_member_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_member_id', sa.Integer(), nullable=True),
        sa.Column('deleted_by_member_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('link_enrichment_id'),
    )
    op.create_index('idx_link_enrichment_link', 'link_enrichment', ['link_id'])
    op.create_index('idx_link_enrichment_status', 'link_enrichment', ['fetch_status', 'classify_status'])

    # 12. LinkEnrichmentKeyword table
    op.create_table(
        'link_enrichment_keyword',
        sa.Column('link_enrichment_keyword_id', sa.Integer(), nullable=False),
        sa.Column('link_enrichment_id', sa.Integer(), nullable=False),
        sa.Column('keyword', sa.String(length=100), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=30), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('link_enrichment_keyword_id'),
    )
    op.create_index('idx_enrichment_keyword_enrichment', 'link_enrichment_keyword', ['link_enrichment_id'])

    # 13. LinkEnrichmentFeedback table
    op.create_table(
        'link_enrichment_feedback',
        sa.Column('link_enrichment_feedback_id', sa.Integer(), nullable=False),
        sa.Column('link_enrichment_id', sa.Integer(), nullable=False),
        sa.Column('member_saved_link_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('suggested_member_folder_id', sa.Integer(), nullable=True),
        sa.Column('final_member_folder_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('link_enrichment_feedback_id'),
    )
    op.create_index('idx_enrichment_feedback_enrichment', 'link_enrichment_feedback', ['link_enrichment_id'])
    op.create_index('idx_enrichment_feedback_action', 'link_enrichment_feedback', ['action'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_enrichment_feedback_action', table_name='link_enrichment_feedback')
    op.drop_index('idx_enrichment_feedback_enrichment', table_name='link_enrichment_feedback')
    op.drop_table('link_enrichment_feedback')
    op.drop_index('idx_enrichment_keyword_enrichment', table_name='link_enrichment_keyword')
    op.drop_table('link_enrichment_keyword')
    op.drop_index('idx_link_enrichment_status', table_name='link_enrichment')
    op.drop_index('idx_link_enrichment_link', table_name='link_enrichment')
    op.drop_table('link_enrichment')
    op.drop_index('idx_suggestion_owner', table_name='folder_suggestion_rule')
    op.drop_index('idx_suggestion_category', table_name='folder_suggestion_rule')
    op.drop_index('idx_suggestion_scope', table_name='folder_suggestion_rule')
    op.drop_table('folder_suggestion_rule')
    op.drop_index('idx_member_folder_tag_tag', table_name='member_folder_tag')
    op.drop_index('idx_member_folder_tag_folder', table_name='member_folder_tag')
    op.drop_table('member_folder_tag')
    op.drop_index('idx_member_saved_link_tag_tag', table_name='member_saved_link_tag')
    op.drop_index('idx_member_saved_link_tag_link', table_name='member_saved_link_tag')
    op.drop_table('member_saved_link_tag')
    op.drop_index('idx_member_saved_link_link', table_name='member_saved_link')
    op.drop_index('idx_member_saved_link_folder', table_name='member_saved_link')
    op.drop_table('member_saved_link')
    op.drop_index('idx_link_created_at', table_name='link')
    op.drop_index('idx_link_category', table_name='link')
    op.drop_index('idx_link_domain', table_name='link')
    op.drop_index('idx_link_canonical_url', table_name='link')
    op.drop_table('link')
    op.drop_index('idx_member_tag_owner', table_name='member_tag')
    op.drop_table('member_tag')
    op.drop_index('idx_member_folder_parent', table_name='member_folder')
    op.drop_index('idx_member_folder_owner', table_name='member_folder')
    op.drop_table('member_folder')
    op.drop_index('idx_category_parent', table_name='category_master')
    op.drop_index('idx_category_level', table_name='category_master')
    op.drop_index('idx_category_is_active', table_name='category_master')
    op.drop_table('category_master')
    op.drop_index('idx_oauth_member_id', table_name='oauth_member')
    op.drop_table('oauth_member')
    op.drop_index('idx_member_created_at', table_name='member')
    op.drop_index('idx_member_status', table_name='member')
    op.drop_table('member')
