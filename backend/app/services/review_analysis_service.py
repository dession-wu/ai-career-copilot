import logging
import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.interview_review import InterviewReview
from app.models.job_application import JobApplication
from app.models.career_analytics import CareerAnalytics
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class ReviewAnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()

    async def analyze_single_review(self, review_id: str) -> Dict[str, Any]:
        """分析单条复盘记录，生成洞察和建议"""
        review = self.db.query(InterviewReview).filter(
            InterviewReview.id == review_id
        ).first()

        if not review:
            raise ValueError(f"Review not found: {review_id}")

        job = review.job_application

        prompt = f"""你是一位资深职业顾问和面试辅导专家。请分析以下面试复盘记录，提供专业的分析和可执行的建议。

## 面试信息
- 公司: {job.company_name if job else 'Unknown'}
- 岗位: {job.job_title if job else 'Unknown'}
- 面试轮次: 第{review.round_number}轮 ({review.round_type})
- 面试日期: {review.interview_date.strftime('%Y-%m-%d') if review.interview_date else 'Unknown'}
- 整体评分: {review.overall_rating}/5

## 各项评分
- 技术能力: {review.technical_rating}/5
- 沟通表达: {review.communication_rating}/5
- 问题解决: {review.problem_solving_rating}/5
- 文化匹配: {review.cultural_fit_rating}/5

## 面试问题
被问到的问题:
{json.dumps(review.questions_asked or [], ensure_ascii=False, indent=2)}

回答得不好的问题:
{json.dumps(review.questions_answered_poorly or [], ensure_ascii=False, indent=2)}

## 复盘内容
做得好的地方:
{review.what_went_well or '未记录'}

需要改进的地方:
{review.what_to_improve or '未记录'}

关键收获:
{review.key_takeaways or '未记录'}

## 请输出以下分析结果（JSON格式）:
{{
    "strengths": ["优势1", "优势2"],
    "weaknesses": ["不足1", "不足2"],
    "patterns": ["模式1", "模式2"],
    "skill_gaps": ["技能缺口1"],
    "action_items": [
        {{
            "priority": "high/medium/low",
            "action": "具体行动",
            "timeline": "建议完成时间",
            "resources": ["推荐学习资源"]
        }}
    ],
    "preparation_tips": ["下次准备建议1"],
    "confidence_assessment": "对自信程度的评估",
    "follow_up_suggestions": "后续跟进建议"
}}"""

        try:
            response = await self.llm_service.generate_json(prompt)
            return response
        except Exception as e:
            logger.error(f"Error analyzing review {review_id}: {e}")
            return {
                "strengths": [],
                "weaknesses": [],
                "patterns": [],
                "skill_gaps": [],
                "action_items": [],
                "preparation_tips": [],
                "confidence_assessment": "分析失败",
                "follow_up_suggestions": "请稍后重试",
                "error": str(e)
            }

    async def generate_career_insights(self, user_id: str, time_range: str = "3m") -> Dict[str, Any]:
        """生成用户在一段时间内的整体求职洞察"""
        from datetime import datetime, timedelta

        end_date = datetime.utcnow()
        if time_range == "1m":
            start_date = end_date - timedelta(days=30)
        elif time_range == "3m":
            start_date = end_date - timedelta(days=90)
        elif time_range == "6m":
            start_date = end_date - timedelta(days=180)
        else:
            start_date = end_date - timedelta(days=365)

        applications = self.db.query(JobApplication).filter(
            JobApplication.user_id == user_id,
            JobApplication.created_at >= start_date
        ).all()

        reviews = self.db.query(InterviewReview).filter(
            InterviewReview.user_id == user_id,
            InterviewReview.interview_date >= start_date
        ).all()

        analytics = self.db.query(CareerAnalytics).filter(
            CareerAnalytics.user_id == user_id
        ).first()

        total_apps = len(applications)
        total_interviews = len([a for a in applications if a.status in ['interviewing', 'offered', 'rejected']])
        total_offers = len([a for a in applications if a.status == 'offered'])

        interview_rate = round(total_interviews / total_apps, 4) if total_apps > 0 else 0
        offer_rate = round(total_offers / total_interviews, 4) if total_interviews > 0 else 0

        channel_stats = {}
        for app in applications:
            channel = app.application_channel or "unknown"
            if channel not in channel_stats:
                channel_stats[channel] = {"applications": 0, "interviews": 0}
            channel_stats[channel]["applications"] += 1
            if app.status in ['interviewing', 'offered', 'rejected']:
                channel_stats[channel]["interviews"] += 1

        avg_rating = None
        if reviews:
            ratings = [r.overall_rating for r in reviews if r.overall_rating]
            avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None

        prompt = f"""你是一位资深职业顾问。请基于以下求职数据，生成全面的分析和建议。

## 数据概览（最近{time_range}）
- 总投递: {total_apps}
- 获得面试: {total_interviews} (转化率: {interview_rate*100:.1f}%)
- 获得Offer: {total_offers} (转化率: {offer_rate*100:.1f}%)
- 平均面试评分: {avg_rating if avg_rating else 'N/A'}/5

## 渠道效果
{json.dumps(channel_stats, ensure_ascii=False, indent=2)}

## 面试复盘数量: {len(reviews)}

## 请输出以下分析结果（JSON格式）:
{{
    "summary": "整体表现总结（2-3句话）",
    "key_findings": ["发现1", "发现2", "发现3"],
    "strengths": ["优势1", "优势2"],
    "areas_for_improvement": ["改进点1", "改进点2"],
    "trends": {{
        "interview_performance": "improving/stable/declining",
        "success_rate": "improving/stable/declining",
        "confidence_level": "improving/stable/declining"
    }},
    "recommendations": [
        {{
            "category": "策略/技能/心态",
            "title": "建议标题",
            "description": "详细说明",
            "priority": "high/medium/low",
            "expected_impact": "预期效果"
        }}
    ],
    "benchmarks": {{
        "vs_industry": "与行业平均水平对比",
        "vs_previous": "与过往表现对比"
    }},
    "next_milestones": ["里程碑1", "里程碑2"]
}}"""

        try:
            response = await self.llm_service.generate_json(prompt)
            return response
        except Exception as e:
            logger.error(f"Error generating career insights for user {user_id}: {e}")
            return {
                "summary": "分析生成失败，请稍后重试",
                "key_findings": [],
                "strengths": [],
                "areas_for_improvement": [],
                "trends": {
                    "interview_performance": "stable",
                    "success_rate": "stable",
                    "confidence_level": "stable"
                },
                "recommendations": [],
                "benchmarks": {
                    "vs_industry": "无法获取",
                    "vs_previous": "无法获取"
                },
                "next_milestones": [],
                "error": str(e)
            }

    async def compare_reviews(self, review_ids: List[str]) -> Dict[str, Any]:
        """对比多次面试，识别模式和进步"""
        reviews = []
        for rid in review_ids:
            review = self.db.query(InterviewReview).filter(
                InterviewReview.id == rid
            ).first()
            if review:
                reviews.append(review)

        if len(reviews) < 2:
            return {
                "error": "Need at least 2 reviews to compare",
                "progress_indicators": [],
                "recurring_issues": [],
                "consistency_analysis": "数据不足",
                "improvement_trajectory": "无法分析",
                "focus_areas": []
            }

        reviews_data = []
        for review in reviews:
            job = review.job_application
            reviews_data.append({
                "company": job.company_name if job else "Unknown",
                "round": review.round_number,
                "type": review.round_type,
                "date": review.interview_date.strftime('%Y-%m-%d') if review.interview_date else "Unknown",
                "overall_rating": review.overall_rating,
                "technical_rating": review.technical_rating,
                "communication_rating": review.communication_rating,
                "what_went_well": review.what_went_well or "",
                "what_to_improve": review.what_to_improve or ""
            })

        prompt = f"""请对比分析以下 {len(reviews)} 次面试复盘记录，识别进步趋势和重复出现的问题。

## 面试记录
{json.dumps(reviews_data, ensure_ascii=False, indent=2)}

## 请输出（JSON格式）:
{{
    "progress_indicators": ["进步点1", "进步点2"],
    "recurring_issues": ["重复问题1"],
    "consistency_analysis": "稳定性分析",
    "improvement_trajectory": "改进轨迹描述",
    "focus_areas": ["需要重点关注的领域1"]
}}"""

        try:
            response = await self.llm_service.generate_json(prompt)
            return response
        except Exception as e:
            logger.error(f"Error comparing reviews: {e}")
            return {
                "progress_indicators": [],
                "recurring_issues": [],
                "consistency_analysis": "分析失败",
                "improvement_trajectory": "无法分析",
                "focus_areas": [],
                "error": str(e)
            }
