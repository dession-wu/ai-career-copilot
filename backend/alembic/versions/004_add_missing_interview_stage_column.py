"""add missing interview_stage column and related fields

Revision ID: 004
Revises: 003
Create Date: 2024-01-25 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """添加 job_applications 表缺失的字段"""
    
    # 获取数据库连接
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # 获取现有列
    existing_columns = [col['name'] for col in inspector.get_columns('job_applications')]
    
    # 添加 interview_stage 列（如果不存在）
    if 'interview_stage' not in existing_columns:
        op.add_column('job_applications', sa.Column('interview_stage', sa.String(50), nullable=True))
    
    # 添加 application_channel 列（如果不存在）
    if 'application_channel' not in existing_columns:
        op.add_column('job_applications', sa.Column('application_channel', sa.String(100), nullable=True))
    
    # 添加薪资相关列（如果不存在）
    if 'salary_min' not in existing_columns:
        op.add_column('job_applications', sa.Column('salary_min', sa.Integer, nullable=True))
    
    if 'salary_max' not in existing_columns:
        op.add_column('job_applications', sa.Column('salary_max', sa.Integer, nullable=True))
    
    if 'salary_currency' not in existing_columns:
        op.add_column('job_applications', sa.Column('salary_currency', sa.String(10), default='CNY'))
    
    # 添加公司信息列（如果不存在）
    if 'company_size' not in existing_columns:
        op.add_column('job_applications', sa.Column('company_size', sa.String(50), nullable=True))
    
    if 'company_industry' not in existing_columns:
        op.add_column('job_applications', sa.Column('company_industry', sa.String(100), nullable=True))
    
    if 'company_location' not in existing_columns:
        op.add_column('job_applications', sa.Column('company_location', sa.String(200), nullable=True))
    
    # 添加时间线记录列（如果不存在）
    if 'applied_at' not in existing_columns:
        op.add_column('job_applications', sa.Column('applied_at', sa.DateTime, nullable=True))
    
    if 'first_response_at' not in existing_columns:
        op.add_column('job_applications', sa.Column('first_response_at', sa.DateTime, nullable=True))
    
    if 'interview_scheduled_at' not in existing_columns:
        op.add_column('job_applications', sa.Column('interview_scheduled_at', sa.DateTime, nullable=True))
    
    if 'final_result_at' not in existing_columns:
        op.add_column('job_applications', sa.Column('final_result_at', sa.DateTime, nullable=True))


def downgrade():
    """回滚：删除添加的列"""
    
    # 获取数据库连接
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # 获取现有列
    existing_columns = [col['name'] for col in inspector.get_columns('job_applications')]
    
    # 删除列（如果存在）
    columns_to_drop = [
        'final_result_at',
        'interview_scheduled_at',
        'first_response_at',
        'applied_at',
        'company_location',
        'company_industry',
        'company_size',
        'salary_currency',
        'salary_max',
        'salary_min',
        'application_channel',
        'interview_stage',
    ]
    
    for column in columns_to_drop:
        if column in existing_columns:
            op.drop_column('job_applications', column)
