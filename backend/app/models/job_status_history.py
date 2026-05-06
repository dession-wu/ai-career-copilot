import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class JobStatusHistory(Base):
    __tablename__ = "job_status_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_application_id = Column(String(36), ForeignKey("job_applications.id", ondelete="CASCADE"), nullable=False)

    # 状态信息
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)

    # 变更详情
    changed_at = Column(DateTime, default=datetime.utcnow)
    changed_by = Column(String(50), default="user")  # user, system
    notes = Column(Text, nullable=True)

    # 额外数据（JSON格式，根据状态类型存储不同信息）
    meta_data = Column("metadata", JSON, nullable=True)
    # 例如：
    # - 面试状态: {"interview_date": "2024-01-12", "interview_type": "onsite", "round": 2}
    # - Offer状态: {"salary": 350000, "start_date": "2024-01-30", "deadline": "2024-01-30"}

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    job_application = relationship("JobApplication", back_populates="status_history")

    def __repr__(self):
        return f"<JobStatusHistory(id={self.id}, job_id={self.job_application_id}, {self.old_status} -> {self.new_status})>"
