from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, Dict, Any


class JobStatusHistoryBase(BaseModel):
    old_status: Optional[str] = None
    new_status: str
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class JobStatusHistoryCreate(JobStatusHistoryBase):
    job_application_id: str
    changed_at: Optional[datetime] = None


class JobStatusHistoryResponse(JobStatusHistoryBase):
    id: str
    job_application_id: str
    changed_at: datetime
    changed_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class JobStatusUpdateRequest(BaseModel):
    new_status: str = Field(..., description="新状态")
    changed_at: Optional[datetime] = Field(None, description="状态变更时间")
    notes: Optional[str] = Field(None, max_length=1000, description="备注")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")

    @validator('new_status')
    def validate_status(cls, v):
        valid_statuses = [
            "preparing", "applied", "resume_screening", "interview_scheduled",
            "interviewing", "offer_pending", "offered", "rejected", "withdrawn"
        ]
        if v not in valid_statuses:
            raise ValueError(f'无效的状态值，必须是以下之一: {", ".join(valid_statuses)}')
        return v

    @validator('notes')
    def validate_notes(cls, v):
        if v and len(v) > 1000:
            raise ValueError('备注长度不能超过1000字符')
        return v


class JobStatusHistoryListResponse(BaseModel):
    history: list[JobStatusHistoryResponse]
    total: int
