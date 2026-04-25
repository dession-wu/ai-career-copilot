import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class CareerAnalytics(Base):
    """用户求职数据分析汇总表（缓存计算结果）"""
    __tablename__ = "career_analytics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    # 投递统计
    total_applications = Column(Integer, default=0)  # 总投递数
    total_interviews = Column(Integer, default=0)  # 总面试数
    total_offers = Column(Integer, default=0)  # 总Offer数
    total_rejections = Column(Integer, default=0)  # 总拒信数

    # 转化率
    application_to_interview_rate = Column(Float, nullable=True)  # 投递到面试转化率
    interview_to_offer_rate = Column(Float, nullable=True)  # 面试到Offer转化率
    overall_success_rate = Column(Float, nullable=True)  # 整体成功率

    # 时间分析
    avg_response_time_days = Column(Float, nullable=True)  # 平均回复时间
    avg_interview_process_days = Column(Float, nullable=True)  # 平均面试流程时长

    # 渠道效果分析
    channel_effectiveness = Column(JSON, nullable=True)  # 各渠道效果 {"官网": 0.15, "内推": 0.35}

    # 公司规模偏好分析
    company_size_distribution = Column(JSON, nullable=True)  # 公司规模分布

    # 技能标签分析
    top_mentioned_skills = Column(JSON, nullable=True)  # 最常出现的技能要求
    skill_gaps = Column(JSON, nullable=True)  # 常见技能缺口

    # 面试表现趋势
    interview_rating_trend = Column(JSON, nullable=True)  # 面试评分趋势

    # 最后更新时间
    last_calculated_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="career_analytics")

    def __repr__(self):
        return f"<CareerAnalytics(user_id={self.user_id}, applications={self.total_applications})>"
