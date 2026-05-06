from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.schemas.analytics import AIInsightsResponse
from app.services.review_analysis_service import ReviewAnalysisService

router = APIRouter(prefix="/ai", tags=["ai_analysis"])


@router.post("/analyze-review/{review_id}")
async def analyze_single_review(
    review_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """分析单条复盘记录"""
    from app.services.review_service import ReviewService
    
    # 验证复盘记录归属
    review_service = ReviewService(db)
    review = review_service.get_review_by_id_with_validation(review_id, current_user.id)
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # 执行 AI 分析
    analysis_service = ReviewAnalysisService(db)
    analysis_result = await analysis_service.analyze_single_review(review_id)
    
    # 保存分析结果
    review_service.update_review_ai_analysis(
        review,
        ai_analysis=analysis_result,
        ai_suggestions=analysis_result.get("action_items", [])
    )
    
    return {
        "review_id": review_id,
        "analysis": analysis_result
    }


@router.post("/generate-insights")
async def generate_career_insights(
    time_range: str = "3m",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """生成整体求职洞察"""
    if time_range not in ["1m", "3m", "6m", "1y"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid time range. Use: 1m, 3m, 6m, 1y"
        )
    
    analysis_service = ReviewAnalysisService(db)
    insights = await analysis_service.generate_career_insights(
        current_user.id,
        time_range
    )
    
    return insights


@router.post("/compare-reviews")
async def compare_reviews(
    review_ids: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """对比多次面试复盘"""
    if len(review_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 review IDs are required for comparison"
        )
    
    # 验证所有复盘记录归属
    from app.services.review_service import ReviewService
    review_service = ReviewService(db)
    
    for rid in review_ids:
        review = review_service.get_review_by_id_with_validation(rid, current_user.id)
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review not found: {rid}"
            )
    
    analysis_service = ReviewAnalysisService(db)
    comparison = await analysis_service.compare_reviews(review_ids)
    
    return comparison
