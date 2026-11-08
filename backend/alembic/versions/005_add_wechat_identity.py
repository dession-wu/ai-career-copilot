"""Independent WeChat identity mapping."""
from alembic import op
import sqlalchemy as sa
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('wechat_identities',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('app_id', sa.String(128), nullable=False),
        sa.Column('openid', sa.String(128), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.UniqueConstraint('app_id', 'openid', name='uq_wechat_app_openid'))

def downgrade():
    op.drop_table('wechat_identities')
