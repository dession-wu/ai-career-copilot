"""add interview review and analytics models

Revision ID: 001
Revises:
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 创建 interview_reviews 表
    op.create_table(
        'interview_reviews',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('application_id', sa.String(36), sa.ForeignKey('job_applications.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('round_number', sa.Integer, default=1),
        sa.Column('round_type', sa.String(50), nullable=False),
        sa.Column('interview_date', sa.DateTime, nullable=False),
        sa.Column('duration_minutes', sa.Integer, nullable=True),
        sa.Column('interview_format', sa.String(50), nullable=True),
        sa.Column('interviewer_count', sa.Integer, default=1),
        sa.Column('overall_rating', sa.Integer, nullable=True),
        sa.Column('technical_rating', sa.Integer, nullable=True),
        sa.Column('communication_rating', sa.Integer, nullable=True),
        sa.Column('problem_solving_rating', sa.Integer, nullable=True),
        sa.Column('cultural_fit_rating', sa.Integer, nullable=True),
        sa.Column('questions_asked', sa.JSON, nullable=True),
        sa.Column('questions_answered_well', sa.JSON, nullable=True),
        sa.Column('questions_answered_poorly', sa.JSON, nullable=True),
        sa.Column('unexpected_questions', sa.JSON, nullable=True),
        sa.Column('what_went_well', sa.Text, nullable=True),
        sa.Column('what_to_improve', sa.Text, nullable=True),
        sa.Column('key_takeaways', sa.Text, nullable=True),
        sa.Column('next_steps', sa.Text, nullable=True),
        sa.Column('confidence_level', sa.Integer, nullable=True),
        sa.Column('stress_level', sa.Integer, nullable=True),
        sa.Column('mood_notes', sa.Text, nullable=True),
        sa.Column('ai_analysis', sa.JSON, nullable=True),
        sa.Column('ai_suggestions', sa.JSON, nullable=True),
        sa.Column('tags', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # 创建 career_analytics 表
    op.create_table(
        'career_analytics',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('total_applications', sa.Integer, default=0),
        sa.Column('total_interviews', sa.Integer, default=0),
        sa.Column('total_offers', sa.Integer, default=0),
        sa.Column('total_rejections', sa.Integer, default=0),
        sa.Column('application_to_interview_rate', sa.Float, nullable=True),
        sa.Column('interview_to_offer_rate', sa.Float, nullable=True),
        sa.Column('overall_success_rate', sa.Float, nullable=True),
        sa.Column('avg_response_time_days', sa.Float, nullable=True),
        sa.Column('avg_interview_process_days', sa.Float, nullable=True),
        sa.Column('channel_effectiveness', sa.JSON, nullable=True),
        sa.Column('company_size_distribution', sa.JSON, nullable=True),
        sa.Column('top_mentioned_skills', sa.JSON, nullable=True),
        sa.Column('skill_gaps', sa.JSON, nullable=True),
        sa.Column('interview_rating_trend', sa.JSON, nullable=True),
        sa.Column('last_calculated_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # 添加索引
    op.create_index('idx_review_application', 'interview_reviews', ['application_id'])
    op.create_index('idx_review_user', 'interview_reviews', ['user_id'])
    op.create_index('idx_review_date', 'interview_reviews', ['interview_date'])

    # 扩展 job_applications 表
    op.add_column('job_applications', sa.Column('interview_stage', sa.String(50), nullable=True))
    op.add_column('job_applications', sa.Column('application_channel', sa.String(100), nullable=True))
    op.add_column('job_applications', sa.Column('salary_min', sa.Integer, nullable=True))
    op.add_column('job_applications', sa.Column('salary_max', sa.Integer, nullable=True))
    op.add_column('job_applications', sa.Column('salary_currency', sa.String(10), default='CNY'))
    op.add_column('job_applications', sa.Column('company_size', sa.String(50), nullable=True))
    op.add_column('job_applications', sa.Column('company_industry', sa.String(100), nullable=True))
    op.add_column('job_applications', sa.Column('company_location', sa.String(200), nullable=True))
    op.add_column('job_applications', sa.Column('applied_at', sa.DateTime, nullable=True))
    op.add_column('job_applications', sa.Column('first_response_at', sa.DateTime, nullable=True))
    op.add_column('job_applications', sa.Column('interview_scheduled_at', sa.DateTime, nullable=True))
    op.add_column('job_applications', sa.Column('final_result_at', sa.DateTime, nullable=True))


def downgrade():
    # 删除 interview_reviews 表
    op.drop_table('interview_reviews')

    # 删除 career_analytics 表
    op.drop_table('career_analytics')

    # 删除 job_applications 表的扩展字段
    op.drop_column('job_applications', 'interview_stage')
    op.drop_column('job_applications', 'application_channel')
    op.drop_column('job_applications', 'salary_min')
    op.drop_column('job_applications', 'salary_max')
    op.drop_column('job_applications', 'salary_currency')
    op.drop_column('job_applications', 'company_size')
    op.drop_column('job_applications', 'company_industry')
    op.drop_column('job_applications', 'company_location')
    op.drop_column('job_applications', 'applied_at')
    op.drop_column('job_applications', 'first_response_at')
    op.drop_column('job_applications', 'interview_scheduled_at')
    op.drop_column('job_applications', 'final_result_at')
