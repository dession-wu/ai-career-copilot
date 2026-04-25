import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_name = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=False)
    jd_text = Column(Text, nullable=False)
    status = Column(String(50), default="preparing")  # preparing, applied, interviewing, offered, rejected
    match_score = Column(Integer, nullable=True)
    match_analysis = Column(JSON, nullable=True)
    tailored_resume_md = Column(Text, nullable=True)
    tailored_resume_versions = Column(JSON, nullable=True, default=list)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # === 新增字段：面试复盘相关 ===

    # 面试阶段细分
    interview_stage = Column(String(50), nullable=True)  # hr_screen, tech_interview, final_round, etc.

    # 投递渠道
    application_channel = Column(String(100), nullable=True)  # 官网, 内推, BOSS直聘, 猎聘, LinkedIn等

    # 薪资信息
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    salary_currency = Column(String(10), default="CNY")

    # 公司信息补充
    company_size = Column(String(50), nullable=True)  # 初创, 中型, 大型, 巨头
    company_industry = Column(String(100), nullable=True)
    company_location = Column(String(200), nullable=True)

    # 时间线记录
    applied_at = Column(DateTime, nullable=True)  # 投递时间
    first_response_at = Column(DateTime, nullable=True)  # 首次回复时间
    interview_scheduled_at = Column(DateTime, nullable=True)  # 面试安排时间
    final_result_at = Column(DateTime, nullable=True)  # 最终结果时间

    # Relationships
    user = relationship("User", back_populates="job_applications")
    interview_questions = relationship("InterviewQuestion", back_populates="job_application", cascade="all, delete-orphan")
    interview_reviews = relationship("InterviewReview", back_populates="job_application", cascade="all, delete-orphan")
    status_history = relationship("JobStatusHistory", back_populates="job_application",
                                  order_by="JobStatusHistory.changed_at.desc()",
                                  cascade="all, delete-orphan")

    def __repr__(self):
        return f"<JobApplication(id={self.id}, company={self.company_name}, title={self.job_title})>"
