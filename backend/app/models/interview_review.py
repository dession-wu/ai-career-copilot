import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class InterviewReview(Base):
    """面试复盘记录表"""
    __tablename__ = "interview_reviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String(36), ForeignKey("job_applications.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 面试轮次信息
    round_number = Column(Integer, default=1)  # 第几轮面试
    round_type = Column(String(50), nullable=False)  # hr_screen, technical, coding, system_design, behavioral, final
    interview_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=True)  # 面试时长

    # 面试形式
    interview_format = Column(String(50), nullable=True)  # video, phone, onsite, online_coding
    interviewer_count = Column(Integer, default=1)  # 面试官人数

    # 面试表现评估（1-5分制）
    overall_rating = Column(Integer, nullable=True)  # 整体表现
    technical_rating = Column(Integer, nullable=True)  # 技术能力
    communication_rating = Column(Integer, nullable=True)  # 沟通表达
    problem_solving_rating = Column(Integer, nullable=True)  # 问题解决
    cultural_fit_rating = Column(Integer, nullable=True)  # 文化匹配

    # 面试内容记录
    questions_asked = Column(JSON, nullable=True)  # 被问到的问题列表
    questions_answered_well = Column(JSON, nullable=True)  # 回答得好的问题
    questions_answered_poorly = Column(JSON, nullable=True)  # 回答得不好的问题
    unexpected_questions = Column(JSON, nullable=True)  # 意外/没准备到的问题

    # 复盘内容
    what_went_well = Column(Text, nullable=True)  # 做得好的地方
    what_to_improve = Column(Text, nullable=True)  # 需要改进的地方
    key_takeaways = Column(Text, nullable=True)  # 关键收获
    next_steps = Column(Text, nullable=True)  # 后续行动计划

    # 情绪与感受
    confidence_level = Column(Integer, nullable=True)  # 自信程度 1-5
    stress_level = Column(Integer, nullable=True)  # 压力程度 1-5
    mood_notes = Column(Text, nullable=True)  # 心情备注

    # AI 分析结果
    ai_analysis = Column(JSON, nullable=True)  # AI 分析结果存储
    ai_suggestions = Column(JSON, nullable=True)  # AI 建议

    # 标签
    tags = Column(JSON, nullable=True)  # 自定义标签 ["算法", "系统设计", "压力面"]

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    job_application = relationship("JobApplication", back_populates="interview_reviews")
    user = relationship("User", back_populates="interview_reviews")

    def __repr__(self):
        return f"<InterviewReview(id={self.id}, round={self.round_number}, type={self.round_type})>"
