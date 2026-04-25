import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.job_application import JobApplication
from app.models.interview_review import InterviewReview
from app.models.career_analytics import CareerAnalytics

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def calculate_analytics(self, user_id: str) -> CareerAnalytics:
        """计算并更新用户的求职分析数据"""
        analytics = self.db.query(CareerAnalytics).filter(
            CareerAnalytics.user_id == user_id
        ).first()

        if not analytics:
            analytics = CareerAnalytics(user_id=user_id)
            self.db.add(analytics)

        applications = self.db.query(JobApplication).filter(
            JobApplication.user_id == user_id
        ).all()

        analytics.total_applications = len(applications)
        analytics.total_interviews = len([a for a in applications if a.status in ['interviewing', 'offered', 'rejected']])
        analytics.total_offers = len([a for a in applications if a.status == 'offered'])
        analytics.total_rejections = len([a for a in applications if a.status == 'rejected'])

        if analytics.total_applications > 0:
            analytics.application_to_interview_rate = analytics.total_interviews / analytics.total_applications
            analytics.overall_success_rate = analytics.total_offers / analytics.total_applications
        else:
            analytics.application_to_interview_rate = None
            analytics.overall_success_rate = None

        if analytics.total_interviews > 0:
            analytics.interview_to_offer_rate = analytics.total_offers / analytics.total_interviews
        else:
            analytics.interview_to_offer_rate = None

        self._calculate_time_analytics(analytics, applications)
        self._calculate_channel_effectiveness(analytics, applications)
        self._calculate_company_size_distribution(analytics, applications)
        self._calculate_interview_rating_trend(analytics, user_id)

        analytics.last_calculated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(analytics)

        logger.info(f"Updated analytics for user: {user_id}")
        return analytics

    def _calculate_time_analytics(self, analytics: CareerAnalytics, applications: List[JobApplication]):
        response_times = []
        process_times = []

        for app in applications:
            if app.applied_at and app.first_response_at:
                response_time = (app.first_response_at - app.applied_at).days
                if response_time >= 0:
                    response_times.append(response_time)

            if app.applied_at and app.final_result_at:
                process_time = (app.final_result_at - app.applied_at).days
                if process_time >= 0:
                    process_times.append(process_time)

        analytics.avg_response_time_days = sum(response_times) / len(response_times) if response_times else None
        analytics.avg_interview_process_days = sum(process_times) / len(process_times) if process_times else None

    def _calculate_channel_effectiveness(self, analytics: CareerAnalytics, applications: List[JobApplication]):
        channel_stats = {}

        for app in applications:
            channel = app.application_channel or "unknown"
            if channel not in channel_stats:
                channel_stats[channel] = {"applications": 0, "interviews": 0, "offers": 0}

            channel_stats[channel]["applications"] += 1
            if app.status in ['interviewing', 'offered', 'rejected']:
                channel_stats[channel]["interviews"] += 1
            if app.status == 'offered':
                channel_stats[channel]["offers"] += 1

        channel_effectiveness = {}
        for channel, stats in channel_stats.items():
            if stats["applications"] > 0:
                conversion_rate = stats["interviews"] / stats["applications"]
                channel_effectiveness[channel] = round(conversion_rate, 4)

        analytics.channel_effectiveness = channel_effectiveness

    def _calculate_company_size_distribution(self, analytics: CareerAnalytics, applications: List[JobApplication]):
        size_distribution = {}

        for app in applications:
            size = app.company_size or "unknown"
            size_distribution[size] = size_distribution.get(size, 0) + 1

        analytics.company_size_distribution = size_distribution

    def _calculate_interview_rating_trend(self, analytics: CareerAnalytics, user_id: str):
        reviews = self.db.query(InterviewReview).filter(
            InterviewReview.user_id == user_id
        ).order_by(InterviewReview.interview_date).all()

        if not reviews:
            analytics.interview_rating_trend = None
            return

        ratings_by_month = {}
        for review in reviews:
            if review.interview_date and review.overall_rating:
                month_key = review.interview_date.strftime("%Y-%m")
                if month_key not in ratings_by_month:
                    ratings_by_month[month_key] = []
                ratings_by_month[month_key].append(review.overall_rating)

        trend_data = {}
        for month, ratings in sorted(ratings_by_month.items()):
            trend_data[month] = round(sum(ratings) / len(ratings), 2)

        analytics.interview_rating_trend = trend_data

    def get_analytics(self, user_id: str) -> Optional[CareerAnalytics]:
        analytics = self.db.query(CareerAnalytics).filter(
            CareerAnalytics.user_id == user_id
        ).first()

        if not analytics:
            analytics = self.calculate_analytics(user_id)

        return analytics

    def get_funnel_analysis(self, user_id: str) -> Dict[str, Any]:
        applications = self.db.query(JobApplication).filter(
            JobApplication.user_id == user_id
        ).all()

        total = len(applications)
        if total == 0:
            return {
                "funnel_data": [],
                "total_applications": 0,
                "conversion_rates": {"application_to_interview": 0, "interview_to_offer": 0, "overall": 0}
            }

        applied = total
        interviewing = len([a for a in applications if a.status in ['interviewing', 'offered', 'rejected']])
        offered = len([a for a in applications if a.status == 'offered'])

        funnel_data = [
            {"stage": "投递", "count": applied, "percentage": 100.0},
            {"stage": "面试", "count": interviewing, "percentage": round(interviewing / applied * 100, 2) if applied > 0 else 0},
            {"stage": "Offer", "count": offered, "percentage": round(offered / applied * 100, 2) if applied > 0 else 0},
        ]

        return {
            "funnel_data": funnel_data,
            "total_applications": total,
            "conversion_rates": {
                "application_to_interview": round(interviewing / applied, 4) if applied > 0 else 0,
                "interview_to_offer": round(offered / interviewing, 4) if interviewing > 0 else 0,
                "overall": round(offered / applied, 4) if applied > 0 else 0
            }
        }

    def get_trends_analysis(self, user_id: str, time_range: str = "3m") -> Dict[str, Any]:
        end_date = datetime.utcnow()
        if time_range == "1m":
            start_date = end_date - timedelta(days=30)
        elif time_range == "3m":
            start_date = end_date - timedelta(days=90)
        elif time_range == "6m":
            start_date = end_date - timedelta(days=180)
        else:  # 1y
            start_date = end_date - timedelta(days=365)

        applications = self.db.query(JobApplication).filter(
            JobApplication.user_id == user_id,
            JobApplication.created_at >= start_date
        ).all()

        data_points = []
        current_date = start_date

        while current_date <= end_date:
            week_end = current_date + timedelta(days=7)
            week_apps = [a for a in applications if current_date <= a.created_at < week_end]
            week_interviews = len([a for a in week_apps if a.status in ['interviewing', 'offered', 'rejected']])
            week_offers = len([a for a in week_apps if a.status == 'offered'])

            data_points.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "applications": len(week_apps),
                "interviews": week_interviews,
                "offers": week_offers,
                "interview_rate": round(week_interviews / len(week_apps), 4) if week_apps else 0,
                "offer_rate": round(week_offers / week_interviews, 4) if week_interviews else 0
            })

            current_date = week_end

        recent_rates = [dp["interview_rate"] for dp in data_points[-4:] if dp["applications"] > 0]
        earlier_rates = [dp["interview_rate"] for dp in data_points[:4] if dp["applications"] > 0]

        if recent_rates and earlier_rates:
            recent_avg = sum(recent_rates) / len(recent_rates)
            earlier_avg = sum(earlier_rates) / len(earlier_rates)
            if recent_avg > earlier_avg * 1.1:
                trend_direction = "improving"
            elif recent_avg < earlier_avg * 0.9:
                trend_direction = "declining"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "stable"

        return {
            "time_range": time_range,
            "data_points": data_points,
            "trend_direction": trend_direction
        }

    def get_channel_analysis(self, user_id: str) -> Dict[str, Any]:
        applications = self.db.query(JobApplication).filter(
            JobApplication.user_id == user_id
        ).all()

        channel_stats = {}
        for app in applications:
            channel = app.application_channel or "unknown"
            if channel not in channel_stats:
                channel_stats[channel] = {"applications": 0, "interviews": 0, "offers": 0}

            channel_stats[channel]["applications"] += 1
            if app.status in ['interviewing', 'offered', 'rejected']:
                channel_stats[channel]["interviews"] += 1
            if app.status == 'offered':
                channel_stats[channel]["offers"] += 1

        channels = []
        for channel, stats in channel_stats.items():
            conversion_rate = round(stats["interviews"] / stats["applications"], 4) if stats["applications"] > 0 else 0
            channels.append({
                "channel": channel,
                "applications": stats["applications"],
                "interviews": stats["interviews"],
                "offers": stats["offers"],
                "conversion_rate": conversion_rate
            })

        channels.sort(key=lambda x: x["conversion_rate"], reverse=True)
        best_channel = channels[0]["channel"] if channels else None

        recommendations = []
        if best_channel and best_channel != "unknown":
            recommendations.append(f"{best_channel}渠道的转化率最高，建议优先使用该渠道投递")

        return {
            "channels": channels,
            "best_performing_channel": best_channel,
            "recommendations": recommendations
        }
