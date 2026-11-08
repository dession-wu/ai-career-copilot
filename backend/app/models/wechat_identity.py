import uuid
from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from app.database import Base

class WechatIdentity(Base):
    __tablename__ = 'wechat_identities'
    __table_args__ = (UniqueConstraint('app_id', 'openid', name='uq_wechat_app_openid'),)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    app_id = Column(String(128), nullable=False)
    openid = Column(String(128), nullable=False)
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
