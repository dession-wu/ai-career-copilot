from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class InterviewQuestionBase(BaseModel):
    question_text: str
    question_type: Optional[str] = None  # technical, behavioral, situational
    intent_analysis: Optional[str] = None
    suggested_answer_star: Optional[str] = None
    difficulty: Optional[int] = None


class InterviewQuestionCreate(InterviewQuestionBase):
    pass


class InterviewQuestionUpdate(BaseModel):
    """用于更新面试题的 schema（用户笔记）"""
    question_text: Optional[str] = None
    question_type: Optional[str] = None
    intent_analysis: Optional[str] = None
    suggested_answer_star: Optional[str] = None
    difficulty: Optional[int] = None


class InterviewQuestionResponse(InterviewQuestionBase):
    id: str
    application_id: str
    related_experience_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
