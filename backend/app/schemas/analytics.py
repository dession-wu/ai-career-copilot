from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any


class ConversionRates(BaseModel):
    application_to_interview: Optional[float] = None
    interview_to_offer: Optional[float] = None
    overall: Optional[float] = None


class CareerAnalyticsOverview(BaseModel):
    total_applications: int
    total_interviews: int
    total_offers: int
    total_rejections: int
    conversion_rates: ConversionRates
    recent_trend: str  # improving, stable, declining
    last_calculated_at: Optional[datetime] = None


class CareerAnalyticsResponse(BaseModel):
    id: str
    user_id: str
    total_applications: int
    total_interviews: int
    total_offers: int
    total_rejections: int
    application_to_interview_rate: Optional[float] = None
    interview_to_offer_rate: Optional[float] = None
    overall_success_rate: Optional[float] = None
    avg_response_time_days: Optional[float] = None
    avg_interview_process_days: Optional[float] = None
    channel_effectiveness: Optional[Dict[str, float]] = None
    company_size_distribution: Optional[Dict[str, int]] = None
    top_mentioned_skills: Optional[List[str]] = None
    skill_gaps: Optional[List[str]] = None
    interview_rating_trend: Optional[Dict[str, Any]] = None
    last_calculated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FunnelData(BaseModel):
    stage: str
    count: int
    percentage: float


class FunnelAnalysisResponse(BaseModel):
    funnel_data: List[FunnelData]
    total_applications: int
    conversion_rates: ConversionRates


class TrendDataPoint(BaseModel):
    date: str
    applications: int
    interviews: int
    offers: int
    interview_rate: float
    offer_rate: float


class TrendsAnalysisResponse(BaseModel):
    time_range: str
    data_points: List[TrendDataPoint]
    trend_direction: str  # improving, stable, declining


class ChannelEffectiveness(BaseModel):
    channel: str
    applications: int
    interviews: int
    offers: int
    conversion_rate: float


class ChannelAnalysisResponse(BaseModel):
    channels: List[ChannelEffectiveness]
    best_performing_channel: Optional[str] = None
    recommendations: List[str]


class SkillAnalysisResponse(BaseModel):
    top_mentioned_skills: List[Dict[str, Any]]  # skill name and frequency
    skill_gaps: List[Dict[str, Any]]  # skill name and gap frequency
    recommendations: List[str]


class AIInsight(BaseModel):
    category: str
    title: str
    description: str
    priority: str  # high, medium, low
    expected_impact: Optional[str] = None


class AIInsightsResponse(BaseModel):
    summary: str
    key_findings: List[str]
    strengths: List[str]
    areas_for_improvement: List[str]
    trends: Dict[str, str]
    recommendations: List[AIInsight]
    next_milestones: List[str]


class TimeRangeRequest(BaseModel):
    time_range: str = "3m"  # 1m, 3m, 6m, 1y
