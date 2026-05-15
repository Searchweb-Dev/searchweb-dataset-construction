"""init: AI 사이트 판별 테이블 생성

Revision ID: 26d5b0df2416
Revises:
Create Date: 2026-05-04 17:17:02.946728

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26d5b0df2416'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'ai_site',
        sa.Column('site_id', sa.BigInteger(), autoincrement=True, nullable=False,
                  comment='사이트 고유 식별자'),
        sa.Column('title', sa.String(length=255), nullable=True,
                  comment='사이트 제목'),
        sa.Column('url', sa.String(length=2048), nullable=False,
                  comment='정규화된 사이트 URL (유니크)'),
        sa.Column('canonical_url', sa.String(length=2048), nullable=True,
                  comment='사이트가 선언한 canonical URL'),
        sa.Column('analyzer', sa.String(length=50), nullable=True,
                  comment='분석에 사용된 분석기 종류 (rule / gemini 등)'),
        sa.Column('is_ai_tool', sa.Boolean(), nullable=False,
                  comment='AI 도구 여부'),
        sa.Column('description', sa.Text(), nullable=True,
                  comment='사이트 기능 요약 설명'),
        sa.Column('favicon_url', sa.String(length=2048), nullable=True,
                  comment='파비콘 이미지 URL'),
        sa.Column('screenshot_url', sa.String(length=2048), nullable=True,
                  comment='스크린샷 이미지 URL'),
        sa.Column('score_utility', sa.Integer(), nullable=True,
                  comment='유용성 점수 (1–10)'),
        sa.Column('score_trust', sa.Integer(), nullable=True,
                  comment='신뢰성 점수 (1–10)'),
        sa.Column('score_originality', sa.Integer(), nullable=True,
                  comment='독창성 점수 (1–10)'),
        sa.Column('total_score', sa.Float(), nullable=True,
                  comment='규칙기반 파이프라인 종합 점수 (0–100)'),
        sa.Column('hard_pass', sa.Boolean(), nullable=True,
                  comment='필수 품질 기준 전체 통과 여부'),
        sa.Column('review_required', sa.Boolean(), nullable=True,
                  comment='수동 검수 필요 여부'),
        sa.Column('last_analyzed_at', sa.DateTime(), nullable=True,
                  comment='마지막 분석 완료 시각 (UTC)'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False,
                  comment='레코드 생성 시각 (UTC)'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False,
                  comment='레코드 최종 수정 시각 (UTC)'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True,
                  comment='소프트 삭제 시각 (NULL이면 유효 레코드)'),
        sa.Column('created_by_member_id', sa.Integer(), nullable=True,
                  comment='생성한 회원 ID'),
        sa.Column('updated_by_member_id', sa.Integer(), nullable=True,
                  comment='최종 수정한 회원 ID'),
        sa.Column('deleted_by_member_id', sa.Integer(), nullable=True,
                  comment='삭제한 회원 ID'),
        sa.PrimaryKeyConstraint('site_id'),
    )
    op.create_index(op.f('ix_ai_site_is_ai_tool'), 'ai_site', ['is_ai_tool'], unique=False)
    op.create_index(op.f('ix_ai_site_last_analyzed_at'), 'ai_site', ['last_analyzed_at'], unique=False)
    op.create_index(op.f('ix_ai_site_url'), 'ai_site', ['url'], unique=True)

    op.create_table(
        'ai_category',
        sa.Column('category_id', sa.BigInteger(), autoincrement=True, nullable=False,
                  comment='카테고리 고유 식별자'),
        sa.Column('site_id', sa.BigInteger(), nullable=False,
                  comment='연결된 사이트 ID (ai_site.site_id 참조)'),
        sa.Column('level_1', sa.String(length=50), nullable=False,
                  comment='대분류 카테고리 (예: text, code, image)'),
        sa.Column('level_2', sa.String(length=100), nullable=False,
                  comment='중분류 카테고리 (예: text-generation, code-generation)'),
        sa.Column('level_3', sa.String(length=100), nullable=True,
                  comment='소분류 카테고리 (선택)'),
        sa.Column('is_primary', sa.Boolean(), nullable=False,
                  comment='대표 카테고리 여부'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False,
                  comment='레코드 생성 시각 (UTC)'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False,
                  comment='레코드 최종 수정 시각 (UTC)'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True,
                  comment='소프트 삭제 시각 (NULL이면 유효 레코드)'),
        sa.Column('created_by_member_id', sa.Integer(), nullable=True,
                  comment='생성한 회원 ID'),
        sa.Column('updated_by_member_id', sa.Integer(), nullable=True,
                  comment='최종 수정한 회원 ID'),
        sa.Column('deleted_by_member_id', sa.Integer(), nullable=True,
                  comment='삭제한 회원 ID'),
        sa.ForeignKeyConstraint(['site_id'], ['ai_site.site_id']),
        sa.PrimaryKeyConstraint('category_id'),
        sa.UniqueConstraint('site_id', 'level_1', 'level_2', name='uq_ai_category_site_level'),
    )
    op.create_index(op.f('ix_ai_category_level_1'), 'ai_category', ['level_1'], unique=False)
    op.create_index(op.f('ix_ai_category_level_2'), 'ai_category', ['level_2'], unique=False)
    op.create_index(op.f('ix_ai_category_site_id'), 'ai_category', ['site_id'], unique=False)

    op.create_table(
        'ai_tag',
        sa.Column('tag_id', sa.BigInteger(), autoincrement=True, nullable=False,
                  comment='태그 고유 식별자'),
        sa.Column('site_id', sa.BigInteger(), nullable=False,
                  comment='연결된 사이트 ID (ai_site.site_id 참조)'),
        sa.Column('tag_name', sa.String(length=50), nullable=False,
                  comment='태그명 (예: 코드 생성, 번역)'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False,
                  comment='레코드 생성 시각 (UTC)'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False,
                  comment='레코드 최종 수정 시각 (UTC)'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True,
                  comment='소프트 삭제 시각 (NULL이면 유효 레코드)'),
        sa.Column('created_by_member_id', sa.Integer(), nullable=True,
                  comment='생성한 회원 ID'),
        sa.Column('updated_by_member_id', sa.Integer(), nullable=True,
                  comment='최종 수정한 회원 ID'),
        sa.Column('deleted_by_member_id', sa.Integer(), nullable=True,
                  comment='삭제한 회원 ID'),
        sa.ForeignKeyConstraint(['site_id'], ['ai_site.site_id']),
        sa.PrimaryKeyConstraint('tag_id'),
        sa.UniqueConstraint('site_id', 'tag_name', name='uq_ai_tag_site_name'),
    )
    op.create_index(op.f('ix_ai_tag_site_id'), 'ai_tag', ['site_id'], unique=False)
    op.create_index(op.f('ix_ai_tag_tag_name'), 'ai_tag', ['tag_name'], unique=False)

    op.create_table(
        'analysis_job',
        sa.Column('job_id', sa.UUID(), nullable=False,
                  comment='작업 고유 식별자 (UUID v4)'),
        sa.Column('site_id', sa.BigInteger(), nullable=True,
                  comment='분석 완료 후 연결된 사이트 ID (ai_site.site_id 참조)'),
        sa.Column('url', sa.String(length=2048), nullable=False,
                  comment='분석 요청 URL'),
        sa.Column('status', sa.String(length=20), nullable=False,
                  comment='작업 상태 (pending / processing / success / failed)'),
        sa.Column('error_message', sa.Text(), nullable=True,
                  comment='실패 시 오류 메시지'),
        sa.Column('started_at', sa.DateTime(), nullable=True,
                  comment='작업 시작 시각 (UTC)'),
        sa.Column('completed_at', sa.DateTime(), nullable=True,
                  comment='작업 완료 시각 (UTC)'),
        sa.Column('retry_count', sa.Integer(), nullable=False,
                  comment='재시도 횟수'),
        sa.Column('request_source', sa.String(length=50), nullable=True,
                  comment='요청 출처 (예: api, batch, manual)'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False,
                  comment='레코드 생성 시각 (UTC)'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False,
                  comment='레코드 최종 수정 시각 (UTC)'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True,
                  comment='소프트 삭제 시각 (NULL이면 유효 레코드)'),
        sa.Column('created_by_member_id', sa.Integer(), nullable=True,
                  comment='생성한 회원 ID'),
        sa.Column('updated_by_member_id', sa.Integer(), nullable=True,
                  comment='최종 수정한 회원 ID'),
        sa.Column('deleted_by_member_id', sa.Integer(), nullable=True,
                  comment='삭제한 회원 ID'),
        sa.ForeignKeyConstraint(['site_id'], ['ai_site.site_id']),
        sa.PrimaryKeyConstraint('job_id'),
    )
    op.create_index(op.f('ix_analysis_job_site_id'), 'analysis_job', ['site_id'], unique=False)
    op.create_index(op.f('ix_analysis_job_status'), 'analysis_job', ['status'], unique=False)
    op.create_index(op.f('ix_analysis_job_url'), 'analysis_job', ['url'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_analysis_job_url'), table_name='analysis_job')
    op.drop_index(op.f('ix_analysis_job_status'), table_name='analysis_job')
    op.drop_index(op.f('ix_analysis_job_site_id'), table_name='analysis_job')
    op.drop_table('analysis_job')
    op.drop_index(op.f('ix_ai_tag_tag_name'), table_name='ai_tag')
    op.drop_index(op.f('ix_ai_tag_site_id'), table_name='ai_tag')
    op.drop_table('ai_tag')
    op.drop_index(op.f('ix_ai_category_site_id'), table_name='ai_category')
    op.drop_index(op.f('ix_ai_category_level_2'), table_name='ai_category')
    op.drop_index(op.f('ix_ai_category_level_1'), table_name='ai_category')
    op.drop_table('ai_category')
    op.drop_index(op.f('ix_ai_site_url'), table_name='ai_site')
    op.drop_index(op.f('ix_ai_site_last_analyzed_at'), table_name='ai_site')
    op.drop_index(op.f('ix_ai_site_is_ai_tool'), table_name='ai_site')
    op.drop_table('ai_site')
