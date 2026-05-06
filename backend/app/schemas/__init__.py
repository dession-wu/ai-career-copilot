from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.schemas.vault import CareerVaultCreate, CareerVaultResponse, CareerVaultUpdate
from app.schemas.job import (
    JobApplicationCreate,
    JobApplicationResponse,
    JobApplicationUpdate,
    MatchAnalysisResponse,
    TailoredResumeResponse,
)
from app.schemas.interview import InterviewQuestionCreate, InterviewQuestionResponse
from app.schemas.scoring import (
    DimensionWeights,
    MatchRequest,
    DimensionScore,
    MatchResponse,
    ResumeScoreRecord,
)
from app.schemas.interview_review import (
    InterviewReviewCreate,
    InterviewReviewUpdate,
    InterviewReviewResponse,
    InterviewReviewWithJobResponse,
)
from app.schemas.analytics import (
    CareerAnalyticsOverview,
    CareerAnalyticsResponse,
    FunnelAnalysisResponse,
    TrendsAnalysisResponse,
    ChannelAnalysisResponse,
    SkillAnalysisResponse,
    AIInsightsResponse,
    TimeRangeRequest,
)

__all__ = [
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "Token",
    "CareerVaultCreate",
    "CareerVaultResponse",
    "CareerVaultUpdate",
    "JobApplicationCreate",
    "JobApplicationResponse",
    "JobApplicationUpdate",
    "MatchAnalysisResponse",
    "TailoredResumeResponse",
    "InterviewQuestionCreate",
    "InterviewQuestionResponse",
    "DimensionWeights",
    "MatchRequest",
    "DimensionScore",
    "MatchResponse",
    "ResumeScoreRecord",
    "InterviewReviewCreate",
    "InterviewReviewUpdate",
    "InterviewReviewResponse",
    "InterviewReviewWithJobResponse",
    "CareerAnalyticsOverview",
    "CareerAnalyticsResponse",
    "FunnelAnalysisResponse",
    "TrendsAnalysisResponse",
    "ChannelAnalysisResponse",
    "SkillAnalysisResponse",
    "AIInsightsResponse",
    "TimeRangeRequest",
]
