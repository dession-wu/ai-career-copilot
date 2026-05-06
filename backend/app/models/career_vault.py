import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class CareerVault(Base):
    __tablename__ = "career_vaults"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    raw_content = Column(Text, nullable=True)
    structured_data = Column(JSON, nullable=False, default=dict)
    parsed_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)

    # Relationships
    user = relationship("User", back_populates="career_vault")

    def __repr__(self):
        return f"<CareerVault(id={self.id}, user_id={self.user_id})>"
