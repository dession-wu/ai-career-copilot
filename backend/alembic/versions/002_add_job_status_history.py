"""add job status history table

Revision ID: 002
Revises: 001
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # 创建 job_status_history 表
    op.create_table(
        'job_status_history',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('job_application_id', sa.String(36), sa.ForeignKey('job_applications.id', ondelete='CASCADE'), nullable=False),
        sa.Column('old_status', sa.String(50), nullable=True),
        sa.Column('new_status', sa.String(50), nullable=False),
        sa.Column('changed_at', sa.DateTime, nullable=False),
        sa.Column('changed_by', sa.String(50), default='user'),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # 创建索引
    op.create_index('idx_status_history_job', 'job_status_history', ['job_application_id'])
    op.create_index('idx_status_history_changed', 'job_status_history', ['changed_at'])


def downgrade():
    # 删除索引
    op.drop_index('idx_status_history_job', table_name='job_status_history')
    op.drop_index('idx_status_history_changed', table_name='job_status_history')
    
    # 删除 job_status_history 表
    op.drop_table('job_status_history')
