from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class InterviewReviewBase(BaseModel):
    application_id: str
    round_number: int = Field(default=1, ge=1)
    round_type: str
    interview_date: datetime
    duration_minutes: Optional[int] = None
    interview_format: Optional[str] = None
    interviewer_count: int = Field(default=1, ge=1)
    overall_rating: Optional[int] = Field(None, ge=1, le=5)
    technical_rating: Optional[int] = Field(None, ge=1, le=5)
    communication_rating: Optional[int] = Field(None, ge=1, le=5)
    problem_solving_rating: Optional[int] = Field(None, ge=1, le=5)
    cultural_fit_rating: Optional[int] = Field(None, ge=1, le=5)
    questions_asked: Optional[List[str]] = []
    questions_answered_well: Optional[List[str]] = []
    questions_answered_poorly: Optional[List[str]] = []
    unexpected_questions: Optional[List[str]] = []
    what_went_well: Optional[str] = Field(None, max_length=5000)
    what_to_improve: Optional[str] = Field(None, max_length=5000)
    key_takeaways: Optional[str] = Field(None, max_length=3000)
    next_steps: Optional[str] = Field(None, max_length=3000)
    confidence_level: Optional[int] = Field(None, ge=1, le=5)
    stress_level: Optional[int] = Field(None, ge=1, le=5)
    mood_notes: Optional[str] = Field(None, max_length=2000)
    tags: Optional[List[str]] = Field(default_factory=list, max_length=20)


class InterviewReviewCreate(InterviewReviewBase):
    pass


class InterviewReviewUpdate(BaseModel):
    application_id: Optional[str] = None
    round_number: Optional[int] = Field(None, ge=1)
    round_type: Optional[str] = None
    interview_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    interview_format: Optional[str] = None
    interviewer_count: Optional[int] = Field(None, ge=1)
    overall_rating: Optional[int] = Field(None, ge=1, le=5)
    technical_rating: Optional[int] = Field(None, ge=1, le=5)
    communication_rating: Optional[int] = Field(None, ge=1, le=5)
    problem_solving_rating: Optional[int] = Field(None, ge=1, le=5)
    cultural_fit_rating: Optional[int] = Field(None, ge=1, le=5)
    questions_asked: Optional[List[str]] = None
    questions_answered_well: Optional[List[str]] = None
    questions_answered_poorly: Optional[List[str]] = None
    unexpected_questions: Optional[List[str]] = None
    what_went_well: Optional[str] = None
    what_to_improve: Optional[str] = None
    key_takeaways: Optional[str] = None
    next_steps: Optional[str] = None
    confidence_level: Optional[int] = Field(None, ge=1, le=5)
    stress_level: Optional[int] = Field(None, ge=1, le=5)
    mood_notes: Optional[str] = None
    tags: Optional[List[str]] = None


class InterviewReviewResponse(InterviewReviewBase):
    id: str
    user_id: str
    ai_analysis: Optional[Dict[str, Any]] = None
    ai_suggestions: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InterviewReviewWithJobResponse(InterviewReviewResponse):
    job_application: Optional["JobApplicationBasicResponse"] = None


class JobApplicationBasicResponse(BaseModel):
    id: str
    company_name: str
    job_title: str
    status: str

    class Config:
        from_attributes = True


InterviewReviewWithJobResponse.model_rebuild()
