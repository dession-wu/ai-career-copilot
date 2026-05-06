from app.routers.auth import router as auth_router
from app.routers.vault import router as vault_router
from app.routers.jobs import router as jobs_router
from app.routers.interview import router as interview_router
from app.routers.scoring import router as scoring_router
from app.routers.interview_review import router as interview_review_router
from app.routers.analytics import router as analytics_router
from app.routers.ai_analysis import router as ai_analysis_router

__all__ = [
    "auth_router",
    "vault_router",
    "jobs_router",
    "interview_router",
    "scoring_router",
    "interview_review_router",
    "analytics_router",
    "ai_analysis_router",
]
