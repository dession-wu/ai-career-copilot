from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime


class DimensionWeights(BaseModel):
    """多维度评分权重配置"""
    skills: float = Field(default=0.35, ge=0, le=1, description="技能匹配维度权重")
    experience: float = Field(default=0.35, ge=0, le=1, description="工作经验维度权重")
    projects: float = Field(default=0.20, ge=0, le=1, description="项目经历维度权重")
    education: float = Field(default=0.10, ge=0, le=1, description="教育背景维度权重")

    class Config:
        json_schema_extra = {
            "example": {
                "skills": 0.35,
                "experience": 0.35,
                "projects": 0.20,
                "education": 0.10
            }
        }


class MatchRequest(BaseModel):
    """简历-JD匹配评分请求"""
    resume_text: str = Field(..., min_length=50, description="简历文本内容")
    jd_text: str = Field(..., min_length=20, description="职位描述文本")
    weights: Optional[DimensionWeights] = Field(
        default=None,
        description="自定义评分权重（可选，使用默认权重）"
    )
    llm_config: Optional[Dict] = Field(
        default=None,
        description="LLM配置（可选，覆盖系统默认配置）"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "resume_text": "5年Python开发经验...",
                "jd_text": "招聘高级后端工程师...",
                "weights": {
                    "skills": 0.40,
                    "experience": 0.30,
                    "projects": 0.20,
                    "education": 0.10
                }
            }
        }


class DimensionScore(BaseModel):
    """单维度评分详情"""
    score: int = Field(..., ge=0, le=100, description="维度得分 (0-100)")
    matched: List[str] = Field(default=[], description="匹配的项目列表")
    missing: List[str] = Field(default=[], description="缺失的项目列表")
    analysis: str = Field(default="", description="维度分析说明")
    suggestions: List[str] = Field(default=[], description="改进建议")


class MatchResponse(BaseModel):
    """简历-JD匹配评分响应"""
    overall_score: int = Field(..., ge=0, le=100, description="综合匹配度分数")
    dimensions: Dict[str, DimensionScore] = Field(
        ...,
        description="各维度评分详情 (skills, experience, projects, education)"
    )
    weights_used: DimensionWeights = Field(
        ...,
        description="实际使用的评分权重"
    )
    summary: str = Field(..., description="总体评价摘要")
    top_strengths: List[str] = Field(default=[], description="核心优势")
    key_gaps: List[str] = Field(default=[], description="关键差距")
    action_items: List[str] = Field(default=[], description="行动建议")
    processed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "overall_score": 78,
                "dimensions": {
                    "skills": {
                        "score": 85,
                        "matched": ["Python", "FastAPI", "PostgreSQL"],
                        "missing": ["Kubernetes", "Redis"],
                        "analysis": "核心技能匹配度较高",
                        "suggestions": ["补充云原生技术栈"]
                    },
                    "experience": {
                        "score": 75,
                        "matched": ["5年开发经验", "团队管理经验"],
                        "missing": ["大型分布式系统经验"],
                        "analysis": "经验年限符合要求",
                        "suggestions": ["突出高并发项目经验"]
                    },
                    "projects": {
                        "score": 80,
                        "matched": ["微服务架构项目"],
                        "missing": [],
                        "analysis": "项目经历与岗位相关度高",
                        "suggestions": ["量化项目成果数据"]
                    },
                    "education": {
                        "score": 70,
                        "matched": ["计算机科学本科"],
                        "missing": ["硕士学历"],
                        "analysis": "学历符合基本要求",
                        "suggestions": ["突出持续学习经历"]
                    }
                },
                "weights_used": {
                    "skills": 0.35,
                    "experience": 0.35,
                    "projects": 0.20,
                    "education": 0.10
                },
                "summary": "综合匹配度良好，技能和经验符合岗位要求",
                "top_strengths": ["Python技术栈熟练", "有微服务实战经验"],
                "key_gaps": ["缺少云原生技术经验"],
                "action_items": ["补充Kubernetes项目经验", "量化现有项目成果"]
            }
        }


class ResumeScoreRecord(BaseModel):
    """简历评分记录（用于数据库存储）"""
    id: Optional[str] = None
    user_id: str
    job_application_id: Optional[str] = None
    resume_text_hash: str
    jd_text_hash: str
    overall_score: int
    dimension_scores: Dict[str, int]
    weights: DimensionWeights
    summary: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
