from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.routers.auth import get_current_user
from app.schemas.user import UserResponse
from app.schemas.scoring import MatchRequest, MatchResponse
from app.services.scoring_service import ResumeScoringEngine

router = APIRouter(prefix="/api/v1/resume", tags=["简历评分"])


@router.post("/match", response_model=MatchResponse)
def match_resume_jd(
    request: MatchRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    简历-JD多维度契合度评分

    从四个维度评估简历与职位描述的匹配度：
    - **skills**: 技能匹配度（默认权重 35%）
    - **experience**: 工作经验匹配度（默认权重 35%）
    - **projects**: 项目经历匹配度（默认权重 20%）
    - **education**: 教育背景匹配度（默认权重 10%）

    支持自定义权重配置，返回综合评分和各维度详细分析。

    **示例请求**:
    ```json
    {
        "resume_text": "5年Python后端开发经验，精通FastAPI和Django...",
        "jd_text": "招聘高级Python工程师，要求熟悉微服务架构...",
        "weights": {
            "skills": 0.40,
            "experience": 0.30,
            "projects": 0.20,
            "education": 0.10
        }
    }
    ```

    **示例响应**:
    ```json
    {
        "overall_score": 78,
        "dimensions": {
            "skills": {
                "score": 85,
                "matched": ["Python", "FastAPI"],
                "missing": ["Kubernetes"],
                "analysis": "核心技能匹配度高",
                "suggestions": ["补充云原生技术"]
            },
            ...
        },
        "summary": "综合匹配度良好...",
        "top_strengths": ["Python技术栈熟练"],
        "key_gaps": ["缺少云原生经验"],
        "action_items": ["补充K8s项目经验"]
    }
    ```
    """
    try:
        scoring_engine = ResumeScoringEngine(db)
        result = scoring_engine.calculate_match(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"评分引擎执行失败: {str(e)}"
        )


@router.post("/match/demo", response_model=MatchResponse)
def match_resume_jd_demo(request: MatchRequest):
    """
    简历-JD评分演示接口（无需认证）

    用于测试和演示评分功能，不需要登录。
    功能与 `/match` 相同，但跳过身份验证。

    **注意**: 生产环境建议禁用此接口或添加限流。
    """
    try:
        scoring_engine = ResumeScoringEngine()
        result = scoring_engine.calculate_match(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"评分引擎执行失败: {str(e)}"
        )
