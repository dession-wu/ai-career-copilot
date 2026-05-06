from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.schemas.interview_review import (
    InterviewReviewCreate,
    InterviewReviewUpdate,
    InterviewReviewResponse,
)
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["interview_reviews"])


@router.post("/jobs/{job_id}", response_model=InterviewReviewResponse)
async def create_review(
    job_id: str,
    review_data: InterviewReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """为指定岗位创建面试复盘记录"""
    # 验证岗位归属
    from app.models.job_application import JobApplication
    job = db.query(JobApplication).filter(
        JobApplication.id == job_id,
        JobApplication.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job application not found"
        )
    
    # 确保 review_data 中的 application_id 与 URL 中的 job_id 一致
    if review_data.application_id != job_id:
        review_data.application_id = job_id
    
    review_service = ReviewService(db)
    review = review_service.create_review(current_user.id, review_data)
    return review


@router.get("/jobs/{job_id}", response_model=List[InterviewReviewResponse])
async def get_reviews_by_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定岗位的所有复盘记录"""
    review_service = ReviewService(db)
    reviews = review_service.get_reviews_by_application(job_id, current_user.id)
    return reviews


@router.get("/{review_id}", response_model=InterviewReviewResponse)
async def get_review(
    review_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单条复盘记录详情"""
    review_service = ReviewService(db)
    review = review_service.get_review_by_id_with_validation(review_id, current_user.id)
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    return review


@router.put("/{review_id}", response_model=InterviewReviewResponse)
async def update_review(
    review_id: str,
    review_data: InterviewReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新复盘记录"""
    review_service = ReviewService(db)
    review = review_service.get_review_by_id_with_validation(review_id, current_user.id)
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    updated_review = review_service.update_review(review, review_data)
    return updated_review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除复盘记录"""
    review_service = ReviewService(db)
    review = review_service.get_review_by_id_with_validation(review_id, current_user.id)
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    review_service.delete_review(review)
    return None


@router.get("", response_model=List[InterviewReviewResponse])
async def get_reviews(
    start_date: Optional[datetime] = Query(None, description="筛选开始日期"),
    end_date: Optional[datetime] = Query(None, description="筛选结束日期"),
    round_type: Optional[str] = Query(None, description="面试类型筛选"),
    rating_min: Optional[int] = Query(None, ge=1, le=5, description="最低评分"),
    rating_max: Optional[int] = Query(None, ge=1, le=5, description="最高评分"),
    tags: Optional[List[str]] = Query(None, description="标签筛选"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回记录数"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的所有复盘记录（支持筛选和分页）"""
    review_service = ReviewService(db)
    reviews = review_service.get_reviews_by_user(
        current_user.id,
        start_date=start_date,
        end_date=end_date,
        round_type=round_type,
        rating_min=rating_min,
        rating_max=rating_max,
        tags=tags,
        skip=skip,
        limit=limit
    )
    return reviews


@router.get("/recent/list", response_model=List[InterviewReviewResponse])
async def get_recent_reviews(
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取最近的复盘记录"""
    review_service = ReviewService(db)
    reviews = review_service.get_recent_reviews(current_user.id, limit)
    return reviews


@router.get("/stats/overview")
async def get_review_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取复盘统计数据"""
    review_service = ReviewService(db)
    stats = review_service.get_review_stats_by_user(current_user.id)
    return stats
