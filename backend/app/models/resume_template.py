import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class ResumeTemplate(Base):
    __tablename__ = "resume_templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    template_type = Column(String(50), nullable=True)  # technical, management, creative
    css_styles = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ResumeTemplate(id={self.id}, name={self.name}, type={self.template_type})>"
