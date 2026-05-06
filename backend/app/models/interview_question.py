import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String(36), ForeignKey("job_applications.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=True)  # technical, behavioral, situational
    intent_analysis = Column(Text, nullable=True)
    suggested_answer_star = Column(Text, nullable=True)
    related_experience_id = Column(String(36), nullable=True)
    difficulty = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job_application = relationship("JobApplication", back_populates="interview_questions")

    def __repr__(self):
        return f"<InterviewQuestion(id={self.id}, type={self.question_type})>"
