from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, List, Any, Optional


class JobApplicationBase(BaseModel):
    company_name: str
    job_title: str
    jd_text: str


class JobApplicationCreate(JobApplicationBase):
    pass


class JobApplicationUpdate(BaseModel):
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    jd_text: Optional[str] = None
    status: Optional[str] = None  # preparing, applied, interviewing, offered, rejected
    match_score: Optional[float] = None
    match_analysis: Optional[Dict[str, Any]] = None
    tailored_resume_md: Optional[str] = None


class JobApplicationResponse(JobApplicationBase):
    id: str
    user_id: str
    status: str
    match_score: Optional[float] = None
    match_analysis: Optional[Dict[str, Any]] = None
    tailored_resume_md: Optional[str] = None
    tailored_resume_versions: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DimensionScoreItem(BaseModel):
    """维度得分项"""
    dimension: str = Field(..., description="维度名称: core_tech, framework, tool, soft_skill")
    score: float = Field(..., ge=0, le=100, description="得分 (0-100)")
    weight: float = Field(..., description="权重")
    max_score: float = Field(default=100.0, description="满分")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")


class SkillMatchDetail(BaseModel):
    """技能匹配详情"""
    matched: List[str] = Field(default_factory=list, description="匹配的技能")
    missing: List[str] = Field(default_factory=list, description="缺失的技能")
    extra: List[str] = Field(default_factory=list, description="简历中有但JD未要求的技能")


class CategoryDetail(BaseModel):
    """类别详情"""
    category: str = Field(..., description="类别名称")
    score: float = Field(..., description="类别得分")
    weight: float = Field(..., description="类别权重")
    matched: List[str] = Field(default_factory=list, description="匹配的技能")
    missing: List[str] = Field(default_factory=list, description="缺失的技能")
    extra: List[str] = Field(default_factory=list, description="额外的技能")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")


class WeightedSkillItem(BaseModel):
    """加权技能项"""
    name: str = Field(..., description="技能名称")
    category: str = Field(..., description="类别")
    weight: float = Field(..., description="权重")
    matched: bool = Field(..., description="是否匹配")
    confidence: float = Field(..., ge=0, le=1, description="置信度")


class MatchDetails(BaseModel):
    """匹配详情"""
    by_category: List[CategoryDetail] = Field(default_factory=list, description="按类别分组详情")
    total_jd_keywords: int = Field(default=0, description="JD关键词总数")
    total_resume_keywords: int = Field(default=0, description="简历关键词总数")
    total_matched: int = Field(default=0, description="匹配总数")
    weighted_skills: List[WeightedSkillItem] = Field(default_factory=list, description="加权技能列表")


class WeightedMatchAnalysisResponse(BaseModel):
    """加权匹配分析响应"""
    overall_score: float = Field(..., ge=0, le=100, description="总体匹配分数 (0-100)")
    confidence: float = Field(..., ge=0, le=1, description="匹配置信度 (0-1)")
    dimension_scores: List[DimensionScoreItem] = Field(default_factory=list, description="各维度得分")
    skill_match: SkillMatchDetail = Field(default_factory=SkillMatchDetail, description="技能匹配详情")
    details: MatchDetails = Field(default_factory=MatchDetails, description="详细匹配信息")
    processing_time_ms: float = Field(default=0.0, description="处理时间（毫秒）")
    suggestions: List[str] = Field(default_factory=list, description="优化建议")


class MatchAnalysisResponse(BaseModel):
    """传统匹配分析响应（向后兼容）"""
    overall_score: int
    skill_match: Dict[str, List[str]]  # matched, missing
    suggestions: List[str]


class TailoredResumeResponse(BaseModel):
    content: str
    version: int
    created_at: datetime
    # 防幻觉校验结果
    verification: Optional[Dict[str, Any]] = None
    # 技能映射关系
    mapping: Optional[Dict[str, Any]] = None
    # 生成模式：llm 或 fallback
    mode: Optional[str] = None


class ResumeVersionCreate(BaseModel):
    content: str
    note: Optional[str] = None


# ==================== Phase 3: 工作流详情与溯源 Schema ====================

class JDRequirementItem(BaseModel):
    """JD 核心诉求项"""
    skill: str = Field(..., description="技能/要求名称")
    category: str = Field(..., description="类别：core_tech, framework, tool, soft_skill")
    importance: str = Field(default="high", description="重要性：high/medium/low")
    context: Optional[str] = Field(default=None, description="JD 中的上下文描述")


class ExperienceEvidenceItem(BaseModel):
    """经历证据项"""
    experience_id: str = Field(..., description="经历唯一标识")
    title: str = Field(..., description="经历标题")
    company: Optional[str] = Field(default=None, description="公司/组织名称")
    period: Optional[str] = Field(default=None, description="时间段")
    evidence_text: str = Field(..., description="具体证据文本")
    match_score: float = Field(..., ge=0, le=100, description="匹配度分数")
    match_reason: str = Field(..., description="匹配原因说明")


class WorkflowStepDetail(BaseModel):
    """工作流步骤详情"""
    step_name: str = Field(..., description="步骤名称")
    step_description: str = Field(..., description="步骤描述")
    jd_requirements: List[JDRequirementItem] = Field(default_factory=list, description="JD 诉求列表")
    recalled_experiences: List[ExperienceEvidenceItem] = Field(default_factory=list, description="召回的经历列表")
    processing_status: str = Field(default="completed", description="处理状态")


class WorkflowDetailsResponse(BaseModel):
    """工作流详情响应"""
    job_id: str = Field(..., description="职位ID")
    steps: List[WorkflowStepDetail] = Field(default_factory=list, description="步骤详情列表")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="生成时间")


class ProvenanceItem(BaseModel):
    """数据溯源项"""
    claim: str = Field(..., description="AI 生成的声明/数值")
    claim_type: str = Field(..., description="声明类型：metric, skill, project, other")
    source_type: str = Field(..., description="来源类型：vault_experience, inferred, hallucinated")
    source_experience_id: Optional[str] = Field(default=None, description="来源经历ID")
    source_text: Optional[str] = Field(default=None, description="来源原文")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    verification_status: str = Field(default="verified", description="验证状态：verified/warning/unverified")


class ProvenanceMapResponse(BaseModel):
    """数据溯源映射响应"""
    job_id: str = Field(..., description="职位ID")
    provenance_items: List[ProvenanceItem] = Field(default_factory=list, description="溯源项列表")
    overall_confidence: float = Field(..., ge=0, le=1, description="整体置信度")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="生成时间")
