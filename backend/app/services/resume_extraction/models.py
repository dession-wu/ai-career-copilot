"""
简历信息提取数据模型
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class PDFType(Enum):
    """PDF类型"""
    TEXT = "text"           # 文本型PDF
    SCANNED = "scanned"     # 扫描件PDF
    MIXED = "mixed"         # 混合型PDF
    UNKNOWN = "unknown"     # 未知类型


class SectionType(Enum):
    """章节类型"""
    PERSONAL_INFO = "personal_info"
    EDUCATION = "education"
    WORK_EXPERIENCE = "work_experience"
    PROJECTS = "projects"
    SKILLS = "skills"
    CERTIFICATIONS = "certifications"
    LANGUAGES = "languages"
    AWARDS = "awards"
    SELF_EVALUATION = "self_evaluation"
    OTHER = "other"


@dataclass
class TextBlock:
    """文本块"""
    text: str
    x: float
    y: float
    width: float
    height: float
    page: int
    font_name: Optional[str] = None
    font_size: Optional[float] = None
    is_bold: bool = False
    is_italic: bool = False
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "page": self.page,
            "font_name": self.font_name,
            "font_size": self.font_size,
            "is_bold": self.is_bold,
            "is_italic": self.is_italic,
            "confidence": self.confidence,
        }


@dataclass
class ImageBlock:
    """图片块"""
    image_data: bytes
    x: float
    y: float
    width: float
    height: float
    page: int
    format: str = "png"


@dataclass
class OCRResult:
    """OCR识别结果"""
    text: str
    confidence: float
    bbox: Tuple[float, float, float, float]  # x, y, width, height
    page: int


@dataclass
class Section:
    """文档章节"""
    section_type: SectionType
    title: str
    content: str
    start_line: int
    end_line: int
    confidence: float = 1.0


@dataclass
class DocumentStructure:
    """文档结构"""
    sections: List[Section] = field(default_factory=list)
    text_blocks: List[TextBlock] = field(default_factory=list)
    image_blocks: List[ImageBlock] = field(default_factory=list)


@dataclass
class ParsedDocument:
    """解析后的文档"""
    raw_text: str
    text_blocks: List[TextBlock]
    image_blocks: List[ImageBlock]
    pdf_type: PDFType
    page_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    structure: Optional[DocumentStructure] = None
    full_text: Optional[str] = None  # 完整文本 (含未截断内容)


@dataclass
class PersonalInfo:
    """个人信息"""
    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    job_intent: Optional[str] = None
    years_of_experience: Optional[int] = None
    portfolio: Optional[str] = None
    political_status: str = ""   # ★ P0-6a 新增: party_member/league_member/mass
    birth_date: str = ""         # ★ P0-6a 新增: YYYY-MM
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "linkedin": self.linkedin,
            "website": self.website,
            "location": self.location,
            "gender": self.gender,
            "age": self.age,
            "job_intent": self.job_intent,
            "years_of_experience": self.years_of_experience,
            "portfolio": self.portfolio,
            "political_status": self.political_status,  # ★ P0-6a 新增
            "birth_date": self.birth_date,              # ★ P0-6a 新增
            "confidence": self.confidence,
        }


@dataclass
class EducationEntry:
    """教育经历条目"""
    school: str = ""
    degree: str = ""
    field_of_study: str = ""
    start_date: str = ""
    end_date: str = ""
    gpa: Optional[str] = None
    honors: List[str] = field(default_factory=list)
    is_transfer: bool = False
    description: str = ""
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "school": self.school,
            "degree": self.degree,
            "field": self.field_of_study,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "gpa": self.gpa,
            "honors": self.honors,
            "is_transfer": self.is_transfer,
            "description": self.description,
            "confidence": self.confidence,
        }


@dataclass
class WorkEntry:
    """工作经历条目"""
    company: str = ""
    title: str = ""
    start_date: str = ""
    end_date: str = ""
    location: Optional[str] = None
    department: Optional[str] = None
    description: str = ""
    achievements: List[str] = field(default_factory=list)
    projects: List[dict] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "company": self.company,
            "title": self.title,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "location": self.location,
            "department": self.department,
            "description": self.description,
            "achievements": self.achievements,
            "projects": self.projects,
            "confidence": self.confidence,
        }


@dataclass
class ProjectEntry:
    """项目经历条目"""
    name: str = ""
    role: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""
    technologies: List[str] = field(default_factory=list)
    tech_stack: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)
    contributions: List[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "description": self.description,
            "technologies": self.technologies,
            "tech_stack": self.tech_stack,
            "achievements": self.achievements,
            "contributions": self.contributions,
            "confidence": self.confidence,
        }


@dataclass
class SkillEntry:
    """技能条目"""
    name: str = ""
    level: str = "熟练"  # 入门/熟练/精通
    category: str = ""   # 编程语言/前端技术/后端框架等
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "level": self.level,
            "category": self.category,
            "confidence": self.confidence,
        }


@dataclass
class Certification:
    """证书"""
    name: str = ""
    issuer: str = ""
    date: str = ""
    confidence: float = 0.0


@dataclass
class Language:
    """语言能力"""
    name: str = ""
    level: str = ""  # CET-4/CET-6/雅思/托福等
    proficiency: str = ""  # 初级/中级/高级/母语
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "level": self.level,
            "proficiency": self.proficiency,
            "confidence": self.confidence,
        }


@dataclass
class ExtractionMetadata:
    """提取元数据"""
    parser_engine: str = ""
    ocr_engine: Optional[str] = None
    confidence_score: float = 0.0
    field_confidence: Dict[str, float] = field(default_factory=dict)
    completeness_score: float = 0.0
    extraction_time_ms: int = 0
    extracted_at: datetime = field(default_factory=datetime.utcnow)
    pdf_type: PDFType = PDFType.UNKNOWN

    def to_dict(self) -> Dict[str, Any]:
        return {
            "parser_engine": self.parser_engine,
            "ocr_engine": self.ocr_engine,
            "confidence_score": self.confidence_score,
            "field_confidence": self.field_confidence,
            "completeness_score": self.completeness_score,
            "extraction_time_ms": self.extraction_time_ms,
            "extracted_at": self.extracted_at.isoformat(),
            "pdf_type": self.pdf_type.value,
        }


@dataclass
class Award:
    """奖项荣誉"""
    name: str = ""
    date: str = ""
    description: str = ""
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "date": self.date,
            "description": self.description,
            "confidence": self.confidence,
        }


@dataclass
class ResumeData:
    """简历结构化数据"""
    personal_info: PersonalInfo = field(default_factory=PersonalInfo)
    education: List[EducationEntry] = field(default_factory=list)
    work_experience: List[WorkEntry] = field(default_factory=list)
    projects: List[ProjectEntry] = field(default_factory=list)
    skills: List[SkillEntry] = field(default_factory=list)
    certifications: List[Certification] = field(default_factory=list)
    languages: List[Language] = field(default_factory=list)
    awards: List[Award] = field(default_factory=list)
    raw_text_preview: str = ""
    metadata: ExtractionMetadata = field(default_factory=ExtractionMetadata)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "personal_info": self.personal_info.to_dict(),
            "education": [e.to_dict() for e in self.education],
            "work_experience": [e.to_dict() for e in self.work_experience],
            "projects": [e.to_dict() for e in self.projects],
            "skills": [e.to_dict() for e in self.skills],
            "certifications": [c.__dict__ for c in self.certifications],
            "languages": [l.__dict__ for l in self.languages],
            "awards": [a.to_dict() for a in self.awards],
            "raw_text_preview": self.raw_text_preview[:1000] if len(self.raw_text_preview) > 1000 else self.raw_text_preview,
            "metadata": self.metadata.to_dict(),
        }


@dataclass
class QualityReport:
    """质量评估报告"""
    overall_score: float  # 0-1
    accuracy_score: float  # 准确度
    completeness_score: float  # 完整度
    field_scores: Dict[str, float]  # 各字段评分
    issues: List[str] = field(default_factory=list)  # 发现的问题
    suggestions: List[str] = field(default_factory=list)  # 改进建议
    low_confidence_fields: List[str] = field(default_factory=list)  # 低置信度字段

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "accuracy_score": self.accuracy_score,
            "completeness_score": self.completeness_score,
            "field_scores": self.field_scores,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "low_confidence_fields": self.low_confidence_fields,
        }


# ==================== v2 数据模型（对标字节跳动投递网页 13 段）====================
# 命名约定：每个 dataclass 都有 schema_version='v2' 标识
# 字段命名与 frontend/types/vault.ts 保持一致
# 顺序：personal_info / educations / internships / work_experiences / projects /
#       portfolios / competitions / certifications / awards / languages /
#       self_evaluation / social_accounts / source


@dataclass
class PersonalInfoV2:
    """v2 个人信息 — 对标字节跳动基础信息"""
    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: Optional[str] = None
    website: Optional[str] = None
    gender: str = ""                    # male/female/other
    age: Optional[int] = None
    location_city: str = ""             # 所在地
    intent_position: str = ""           # 期望职位
    intent_city: str = ""               # 期望地点
    current_status: str = ""            # employed/unemployed/student/fresh_graduate
    years_of_experience: Optional[int] = None
    political_status: str = ""          # party_member/league_member/mass
    expected_salary_min: Optional[int] = None  # K/月
    expected_salary_max: Optional[int] = None
    source_of_info: str = ""            # 内推/官网/...
    source_detail: str = ""
    id_card_type: str = ""              # mainland/hk/macau/taiwan/foreign
    id_card_number: str = ""
    confidence: float = 0.0
    needs_review: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "email": self.email, "phone": self.phone,
            "linkedin": self.linkedin, "website": self.website,
            "gender": self.gender, "age": self.age,
            "location_city": self.location_city,
            "intent_position": self.intent_position, "intent_city": self.intent_city,
            "current_status": self.current_status,
            "years_of_experience": self.years_of_experience,
            "political_status": self.political_status,
            "expected_salary_min": self.expected_salary_min,
            "expected_salary_max": self.expected_salary_max,
            "source_of_info": self.source_of_info,
            "source_detail": self.source_detail,
            "id_card_type": self.id_card_type,
            "id_card_number": self.id_card_number,
            "confidence": self.confidence, "needs_review": self.needs_review,
        }


@dataclass
class EducationV2:
    """v2 教育经历 — 对标字节跳动教育经历段"""
    school: str = ""
    degree: str = ""                    # high_school/associate/bachelor/master/phd
    degree_type: str = ""               # full_time/part_time/online/self_study
    field_of_study: str = ""            # 专业
    major_category: str = ""            # 工科/理科/文科
    gpa: Optional[str] = None
    gpa_scale: str = ""                 # 4.0/5.0/100
    gpa_rank: str = ""                  # 前 5%
    ranking_label: str = ""
    honors: List[str] = field(default_factory=list)
    is_transfer: bool = False
    start_date: str = ""
    end_date: str = ""
    description: str = ""
    courses: List[str] = field(default_factory=list)
    confidence: float = 0.0
    needs_review: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "school": self.school, "degree": self.degree,
            "degree_type": self.degree_type, "field_of_study": self.field_of_study,
            "major_category": self.major_category,
            "gpa": self.gpa, "gpa_scale": self.gpa_scale,
            "gpa_rank": self.gpa_rank, "ranking_label": self.ranking_label,
            "honors": self.honors, "is_transfer": self.is_transfer,
            "start_date": self.start_date, "end_date": self.end_date,
            "description": self.description, "courses": self.courses,
            "confidence": self.confidence, "needs_review": self.needs_review,
        }


@dataclass
class InternshipV2:
    """v2 实习经历 — 与工作经历分开"""
    company: str = ""
    title: str = ""
    department: str = ""
    start_date: str = ""
    end_date: str = ""
    location: str = ""
    description: str = ""
    achievements: List[str] = field(default_factory=list)
    confidence: float = 0.0
    needs_review: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "company": self.company, "title": self.title,
            "department": self.department, "start_date": self.start_date,
            "end_date": self.end_date, "location": self.location,
            "description": self.description,
            "achievements": self.achievements,
            "confidence": self.confidence, "needs_review": self.needs_review,
        }


@dataclass
class WorkV2:
    """v2 工作经历"""
    company: str = ""
    title: str = ""
    department: str = ""
    start_date: str = ""
    end_date: str = ""
    location: str = ""
    employment_type: str = ""           # full_time/part_time/contract/freelance
    description: str = ""
    achievements: List[str] = field(default_factory=list)
    projects: List[str] = field(default_factory=list)
    confidence: float = 0.0
    needs_review: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "company": self.company, "title": self.title,
            "department": self.department, "start_date": self.start_date,
            "end_date": self.end_date, "location": self.location,
            "employment_type": self.employment_type,
            "description": self.description,
            "achievements": self.achievements, "projects": self.projects,
            "confidence": self.confidence, "needs_review": self.needs_review,
        }


@dataclass
class ProjectV2:
    """v2 项目经历"""
    name: str = ""
    role: str = ""
    start_date: str = ""
    end_date: str = ""
    project_link: str = ""              # 字节跳动"项目链接"
    description: str = ""
    contributions: List[str] = field(default_factory=list)
    tech_stack: List[str] = field(default_factory=list)
    project_outcome: str = ""
    confidence: float = 0.0
    needs_review: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "role": self.role,
            "start_date": self.start_date, "end_date": self.end_date,
            "project_link": self.project_link,
            "description": self.description,
            "contributions": self.contributions,
            "tech_stack": self.tech_stack,
            "project_outcome": self.project_outcome,
            "confidence": self.confidence, "needs_review": self.needs_review,
        }


@dataclass
class PortfolioV2:
    """作品（字节"作品"段）"""
    name: str = ""
    link: str = ""
    platform: str = ""                  # GitHub / 站酷 / B 站...
    role: str = ""
    description: str = ""
    date: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "link": self.link,
            "platform": self.platform, "role": self.role,
            "description": self.description, "date": self.date,
        }


@dataclass
class CompetitionV2:
    """竞赛（独立于 Award）"""
    name: str = ""
    organizer: str = ""
    level: str = ""                     # international/national/provincial/school
    date: str = ""
    description: str = ""
    role: str = ""
    result: str = ""                    # 一等奖/Top 5/冠军

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "organizer": self.organizer,
            "level": self.level, "date": self.date,
            "description": self.description,
            "role": self.role, "result": self.result,
        }


@dataclass
class SelfEvaluation:
    """自我评价（字节"自我评价"段）"""
    text: str = ""
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
        }


@dataclass
class SocialAccountV2:
    """社交账号（字节"社交账号"段）"""
    platform: str = ""                  # github/linkedin/csdn/juejin/zhihu/...
    url: str = ""
    label: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform, "url": self.url, "label": self.label,
        }


@dataclass
class SourceOfInfo:
    """了解渠道（字节"了解渠道"段）"""
    channel: str = ""                   # referral/official_website/social_media/...
    detail: str = ""                    # 内推人姓名

    def to_dict(self) -> Dict[str, Any]:
        return {"channel": self.channel, "detail": self.detail}


@dataclass
class ResumeDataV2:
    """v2 简历结构化数据 — 对标字节跳动投递网页 13 段"""
    schema_version: str = "v2"
    personal_info: PersonalInfoV2 = field(default_factory=PersonalInfoV2)
    has_work_experience: bool = True   # 字节"无工作经历" toggle
    educations: List[EducationV2] = field(default_factory=list)
    internships: List[InternshipV2] = field(default_factory=list)
    work_experiences: List[WorkV2] = field(default_factory=list)
    projects: List[ProjectV2] = field(default_factory=list)
    portfolios: List[PortfolioV2] = field(default_factory=list)
    competitions: List[CompetitionV2] = field(default_factory=list)
    certifications: List[Certification] = field(default_factory=list)
    awards: List[Award] = field(default_factory=list)
    languages: List[Language] = field(default_factory=list)
    skills: List[SkillEntry] = field(default_factory=list)
    self_evaluation: Optional[SelfEvaluation] = None
    social_accounts: List[SocialAccountV2] = field(default_factory=list)
    source: SourceOfInfo = field(default_factory=SourceOfInfo)
    raw_text_preview: str = ""
    needs_review: bool = False
    extraction_quality: Optional[ExtractionMetadata] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "personal_info": self.personal_info.to_dict(),
            "has_work_experience": self.has_work_experience,
            "educations": [e.to_dict() for e in self.educations],
            "internships": [e.to_dict() for e in self.internships],
            "work_experiences": [e.to_dict() for e in self.work_experiences],
            "projects": [e.to_dict() for e in self.projects],
            "portfolios": [p.to_dict() for p in self.portfolios],
            "competitions": [c.to_dict() for c in self.competitions],
            "certifications": [c.__dict__ for c in self.certifications],
            "awards": [a.to_dict() for a in self.awards],
            "languages": [l.__dict__ for l in self.languages],
            "skills": [s.to_dict() for s in self.skills],
            "self_evaluation": self.self_evaluation.to_dict() if self.self_evaluation else None,
            "social_accounts": [a.to_dict() for a in self.social_accounts],
            "source": self.source.to_dict(),
            "raw_text_preview": (self.raw_text_preview or "")[:1000],
            "needs_review": self.needs_review,
            "extraction_quality": self.extraction_quality.to_dict() if self.extraction_quality else None,
        }

    @classmethod
    def empty(cls) -> "ResumeDataV2":
        return cls(schema_version="v2")

    @classmethod
    def from_v1_dict(cls, v1: Dict[str, Any]) -> "ResumeDataV2":
        """v1 → v2 兼容迁移"""
        if not v1:
            return cls.empty()

        # 已经是 v2
        if v1.get("schema_version") == "v2":
            # 已经是 v2 字典,尽量转回 dataclass
            v2 = cls.empty()
            v2.personal_info = PersonalInfoV2(**{k: v for k, v in v1.get("personal_info", {}).items() if k in v2.personal_info.to_dict()})
            v2.has_work_experience = v1.get("has_work_experience", {}).get("has_work_experience", True) if isinstance(v1.get("has_work_experience"), dict) else v1.get("has_work_experience", True)
            for e in v1.get("educations", v1.get("education", [])):
                v2.educations.append(EducationV2(**{k: v for k, v in e.items() if k in EducationV2().to_dict()}))
            for w in v1.get("internships", []):
                v2.internships.append(InternshipV2(**{k: v for k, v in w.items() if k in InternshipV2().to_dict()}))
            for w in v1.get("work_experiences", v1.get("experiences", [])):
                v2.work_experiences.append(WorkV2(**{k: v for k, v in w.items() if k in WorkV2().to_dict()}))
            for p in v1.get("projects", []):
                v2.projects.append(ProjectV2(**{k: v for k, v in p.items() if k in ProjectV2().to_dict()}))
            for x in v1.get("portfolios", []):
                v2.portfolios.append(PortfolioV2(**x))
            for c in v1.get("competitions", []):
                v2.competitions.append(CompetitionV2(**c))
            for c in v1.get("certifications", []):
                v2.certifications.append(Certification(**c))
            for a in v1.get("awards", []):
                v2.awards.append(Award(**{k: v for k, v in a.items() if k in Award().to_dict()}))
            for l in v1.get("languages", []):
                v2.languages.append(Language(**l))
            for s in v1.get("skills", []):
                v2.skills.append(SkillEntry(**{k: v for k, v in s.items() if k in SkillEntry().to_dict()}))
            if v1.get("self_evaluation"):
                v2.self_evaluation = SelfEvaluation(**v1["self_evaluation"])
            for s in v1.get("social_accounts", []):
                v2.social_accounts.append(SocialAccountV2(**s))
            if v1.get("source"):
                v2.source = SourceOfInfo(**v1["source"])
            v2.raw_text_preview = v1.get("raw_text_preview", "")
            v2.needs_review = v1.get("needs_review", False)
            return v2

        # v1 迁移
        v2 = cls.empty()
        pi = v1.get("personal_info", {}) or {}
        v2.personal_info = PersonalInfoV2(
            name=pi.get("name", ""),
            email=pi.get("email", ""),
            phone=pi.get("phone", ""),
            linkedin=pi.get("linkedin"),
            website=pi.get("website") or pi.get("portfolio"),
            gender=pi.get("gender", ""),
            age=pi.get("age"),
            location_city=pi.get("location", ""),
            years_of_experience=pi.get("years_of_experience"),
            intent_position=pi.get("job_intent", ""),
            confidence=pi.get("confidence", 0.0),
        )

        for e in v1.get("education", v1.get("educations", [])):
            v2.educations.append(EducationV2(
                school=e.get("school", ""),
                degree=e.get("degree", ""),
                field_of_study=e.get("field_of_study") or e.get("field", ""),
                start_date=e.get("start_date", ""),
                end_date=e.get("end_date", ""),
                gpa=e.get("gpa"),
                honors=e.get("honors", []),
                is_transfer=e.get("is_transfer", False),
                description=e.get("description", ""),
                confidence=e.get("confidence", 0.0),
            ))

        for w in v1.get("experiences", v1.get("work_experience", [])):
            # 启发式：若 title 含 "实习" / "intern" / 起始时间 < 3 个月 → 实习
            title = (w.get("title", "") or "").lower()
            is_intern = any(k in title for k in ["实习", "intern"])
            target = v2.internships if is_intern else v2.work_experiences
            target.append(WorkV2(
                company=w.get("company", ""),
                title=w.get("title", ""),
                department=w.get("department", ""),
                start_date=w.get("start_date", ""),
                end_date=w.get("end_date", ""),
                location=w.get("location", ""),
                description=w.get("description", ""),
                achievements=w.get("achievements", []),
                confidence=w.get("confidence", 0.0),
            ))

        for p in v1.get("projects", []):
            v2.projects.append(ProjectV2(
                name=p.get("name", ""),
                role=p.get("role", ""),
                start_date=p.get("start_date", ""),
                end_date=p.get("end_date", ""),
                description=p.get("description", ""),
                tech_stack=p.get("tech_stack", []) or p.get("technologies", []),
                contributions=p.get("contributions", []),
                confidence=p.get("confidence", 0.0),
            ))

        for c in v1.get("certifications", []):
            v2.certifications.append(Certification(**{k: v for k, v in c.items() if k in Certification().__dict__ or k == "confidence"}))

        for l in v1.get("languages", []):
            v2.languages.append(Language(
                name=l.get("name", ""),
                level=l.get("level", ""),
                proficiency=l.get("proficiency", ""),
                confidence=l.get("confidence", 0.0),
            ))

        for a in v1.get("awards", []):
            v2.awards.append(Award(
                name=a.get("name", ""),
                date=a.get("date", ""),
                description=a.get("description", ""),
                confidence=a.get("confidence", 0.0),
            ))

        for s in v1.get("skills", []):
            v2.skills.append(SkillEntry(
                name=s.get("name", ""),
                level=s.get("level", ""),
                category=s.get("category", ""),
                confidence=s.get("confidence", 0.0),
            ))

        # 个人主页 → social_accounts
        website = v2.personal_info.website
        if website:
            v2.social_accounts.append(SocialAccountV2(
                platform="blog" if "blog" in (website or "") else "other",
                url=website,
                label="个人主页",
            ))

        v2.raw_text_preview = v1.get("raw_text_preview", "")
        v2.needs_review = v1.get("needs_review", False)
        return v2

