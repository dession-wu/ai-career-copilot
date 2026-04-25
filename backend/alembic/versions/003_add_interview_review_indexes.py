"""add interview review indexes

Revision ID: 003
Revises: 002
Create Date: 2024-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # 添加复合索引：application_id + user_id，用于关联查询
    op.create_index(
        'idx_reviews_job_user',
        'interview_reviews',
        ['application_id', 'user_id']
    )

    # 添加索引：user_id + interview_date，用于时间排序查询
    op.create_index(
        'idx_reviews_date_user',
        'interview_reviews',
        ['user_id', 'interview_date']
    )

    # 添加索引：round_type，用于按类型筛选
    op.create_index(
        'idx_reviews_round_type',
        'interview_reviews',
        ['round_type']
    )


def downgrade():
    # 删除索引
    op.drop_index('idx_reviews_job_user', table_name='interview_reviews')
    op.drop_index('idx_reviews_date_user', table_name='interview_reviews')
    op.drop_index('idx_reviews_round_type', table_name='interview_reviews')
