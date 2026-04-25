from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.schemas.analytics import (
    CareerAnalyticsOverview,
    CareerAnalyticsResponse,
    FunnelAnalysisResponse,
    TrendsAnalysisResponse,
    ChannelAnalysisResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=CareerAnalyticsOverview)
async def get_analytics_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取求职数据概览"""
    analytics_service = AnalyticsService(db)
    analytics = analytics_service.get_analytics(current_user.id)
    
    if not analytics:
        return CareerAnalyticsOverview(
            total_applications=0,
            total_interviews=0,
            total_offers=0,
            total_rejections=0,
            conversion_rates={
                "application_to_interview": 0,
                "interview_to_offer": 0,
                "overall": 0
            },
            recent_trend="stable",
            last_calculated_at=None
        )
    
    # 计算趋势
    funnel = analytics_service.get_funnel_analysis(current_user.id)
    recent_trend = "stable"
    
    return CareerAnalyticsOverview(
        total_applications=analytics.total_applications,
        total_interviews=analytics.total_interviews,
        total_offers=analytics.total_offers,
        total_rejections=analytics.total_rejections,
        conversion_rates=funnel["conversion_rates"],
        recent_trend=recent_trend,
        last_calculated_at=analytics.last_calculated_at
    )


@router.get("/detailed", response_model=CareerAnalyticsResponse)
async def get_detailed_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取详细的求职分析数据"""
    analytics_service = AnalyticsService(db)
    analytics = analytics_service.get_analytics(current_user.id)
    
    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analytics data not found"
        )
    
    return analytics


@router.get("/funnel", response_model=FunnelAnalysisResponse)
async def get_funnel_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取求职漏斗分析"""
    analytics_service = AnalyticsService(db)
    return analytics_service.get_funnel_analysis(current_user.id)


@router.get("/trends", response_model=TrendsAnalysisResponse)
async def get_trends_analysis(
    time_range: str = Query("3m", description="时间范围: 1m, 3m, 6m, 1y"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取趋势分析"""
    if time_range not in ["1m", "3m", "6m", "1y"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid time range. Use: 1m, 3m, 6m, 1y"
        )
    
    analytics_service = AnalyticsService(db)
    return analytics_service.get_trends_analysis(current_user.id, time_range)


@router.get("/channels", response_model=ChannelAnalysisResponse)
async def get_channel_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取渠道效果分析"""
    analytics_service = AnalyticsService(db)
    return analytics_service.get_channel_analysis(current_user.id)


@router.post("/refresh")
async def refresh_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """手动刷新分析数据"""
    analytics_service = AnalyticsService(db)
    analytics = analytics_service.calculate_analytics(current_user.id)
    
    return {
        "message": "Analytics refreshed successfully",
        "last_calculated_at": analytics.last_calculated_at
    }
