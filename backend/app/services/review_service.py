import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models.interview_review import InterviewReview
from app.models.job_application import JobApplication
from app.schemas.interview_review import InterviewReviewCreate, InterviewReviewUpdate

logger = logging.getLogger(__name__)


class ReviewService:
    def __init__(self, db: Session):
        self.db = db

    def create_review(self, user_id: str, review_data: InterviewReviewCreate) -> InterviewReview:
        """创建新的面试复盘记录"""
        review = InterviewReview(
            user_id=user_id,
            application_id=review_data.application_id,
            round_number=review_data.round_number,
            round_type=review_data.round_type,
            interview_date=review_data.interview_date,
            duration_minutes=review_data.duration_minutes,
            interview_format=review_data.interview_format,
            interviewer_count=review_data.interviewer_count,
            overall_rating=review_data.overall_rating,
            technical_rating=review_data.technical_rating,
            communication_rating=review_data.communication_rating,
            problem_solving_rating=review_data.problem_solving_rating,
            cultural_fit_rating=review_data.cultural_fit_rating,
            questions_asked=review_data.questions_asked,
            questions_answered_well=review_data.questions_answered_well,
            questions_answered_poorly=review_data.questions_answered_poorly,
            unexpected_questions=review_data.unexpected_questions,
            what_went_well=review_data.what_went_well,
            what_to_improve=review_data.what_to_improve,
            key_takeaways=review_data.key_takeaways,
            next_steps=review_data.next_steps,
            confidence_level=review_data.confidence_level,
            stress_level=review_data.stress_level,
            mood_notes=review_data.mood_notes,
            tags=review_data.tags,
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        logger.info(f"Created interview review: {review.id}")
        return review

    def get_review_by_id(self, review_id: str) -> Optional[InterviewReview]:
        """通过 ID 获取复盘记录"""
        return self.db.query(InterviewReview).filter(
            InterviewReview.id == review_id
        ).first()

    def get_review_by_id_with_validation(
        self,
        review_id: str,
        user_id: str
    ) -> Optional[InterviewReview]:
        """通过 ID 获取复盘记录并验证用户权限"""
        return self.db.query(InterviewReview).filter(
            and_(
                InterviewReview.id == review_id,
                InterviewReview.user_id == user_id
            )
        ).first()

    def get_reviews_by_application(
        self,
        application_id: str,
        user_id: str
    ) -> List[InterviewReview]:
        """获取指定岗位的所有复盘记录"""
        return self.db.query(InterviewReview).filter(
            and_(
                InterviewReview.application_id == application_id,
                InterviewReview.user_id == user_id
            )
        ).order_by(desc(InterviewReview.interview_date)).all()

    def get_reviews_by_user(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        round_type: Optional[str] = None,
        rating_min: Optional[int] = None,
        rating_max: Optional[int] = None,
        tags: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[InterviewReview]:
        """获取用户的所有复盘记录（支持筛选和分页）"""
        query = self.db.query(InterviewReview).filter(
            InterviewReview.user_id == user_id
        )

        if start_date:
            query = query.filter(InterviewReview.interview_date >= start_date)
        if end_date:
            query = query.filter(InterviewReview.interview_date <= end_date)
        if round_type:
            query = query.filter(InterviewReview.round_type == round_type)
        if rating_min is not None:
            query = query.filter(InterviewReview.overall_rating >= rating_min)
        if rating_max is not None:
            query = query.filter(InterviewReview.overall_rating <= rating_max)
        if tags:
            for tag in tags:
                query = query.filter(
                    InterviewReview.tags.contains([tag])
                )

        return query.order_by(desc(InterviewReview.interview_date)).offset(skip).limit(limit).all()

    def get_reviews_count(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        round_type: Optional[str] = None
    ) -> int:
        """获取复盘记录总数"""
        query = self.db.query(InterviewReview).filter(
            InterviewReview.user_id == user_id
        )

        if start_date:
            query = query.filter(InterviewReview.interview_date >= start_date)
        if end_date:
            query = query.filter(InterviewReview.interview_date <= end_date)
        if round_type:
            query = query.filter(InterviewReview.round_type == round_type)

        return query.count()

    def get_recent_reviews(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[InterviewReview]:
        """获取最近的复盘记录"""
        return self.db.query(InterviewReview).filter(
            InterviewReview.user_id == user_id
        ).order_by(desc(InterviewReview.created_at)).limit(limit).all()

    def update_review(
        self,
        review: InterviewReview,
        update_data: InterviewReviewUpdate
    ) -> InterviewReview:
        """更新复盘记录"""
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(review, field, value)

        review.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(review)
        logger.info(f"Updated interview review: {review.id}")
        return review

    def update_review_ai_analysis(
        self,
        review: InterviewReview,
        ai_analysis: Dict[str, Any],
        ai_suggestions: Optional[Dict[str, Any]] = None
    ) -> InterviewReview:
        """更新复盘记录的 AI 分析结果"""
        review.ai_analysis = ai_analysis
        review.ai_suggestions = ai_suggestions
        review.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(review)
        logger.info(f"Updated AI analysis for review: {review.id}")
        return review

    def delete_review(self, review: InterviewReview) -> None:
        """删除复盘记录"""
        review_id = review.id
        self.db.delete(review)
        self.db.commit()
        logger.info(f"Deleted interview review: {review_id}")

    def get_review_stats_by_user(self, user_id: str) -> Dict[str, Any]:
        """获取用户的复盘统计数据"""
        reviews = self.db.query(InterviewReview).filter(
            InterviewReview.user_id == user_id
        ).all()

        if not reviews:
            return {
                "total_reviews": 0,
                "avg_rating": None,
                "avg_technical_rating": None,
                "avg_communication_rating": None,
                "rating_distribution": {},
                "round_type_distribution": {},
                "tags_frequency": {}
            }

        ratings = [r.overall_rating for r in reviews if r.overall_rating]
        technical_ratings = [r.technical_rating for r in reviews if r.technical_rating]
        communication_ratings = [r.communication_rating for r in reviews if r.communication_rating]

        rating_distribution = {}
        for r in reviews:
            if r.overall_rating:
                rating_distribution[r.overall_rating] = rating_distribution.get(r.overall_rating, 0) + 1

        round_type_distribution = {}
        for r in reviews:
            round_type_distribution[r.round_type] = round_type_distribution.get(r.round_type, 0) + 1

        tags_frequency = {}
        for r in reviews:
            if r.tags:
                for tag in r.tags:
                    tags_frequency[tag] = tags_frequency.get(tag, 0) + 1

        return {
            "total_reviews": len(reviews),
            "avg_rating": sum(ratings) / len(ratings) if ratings else None,
            "avg_technical_rating": sum(technical_ratings) / len(technical_ratings) if technical_ratings else None,
            "avg_communication_rating": sum(communication_ratings) / len(communication_ratings) if communication_ratings else None,
            "rating_distribution": rating_distribution,
            "round_type_distribution": round_type_distribution,
            "tags_frequency": tags_frequency
        }
