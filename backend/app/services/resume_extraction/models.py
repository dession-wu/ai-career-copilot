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
            "confidence": self.confidence,
        }


@dataclass
class EducationEntry:
    """教育经历条目"""
    school: str = ""
    degree: str = ""
    field: str = ""
    start_date: str = ""
    end_date: str = ""
    gpa: Optional[str] = None
    description: str = ""
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "school": self.school,
            "degree": self.degree,
            "field": self.field,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "gpa": self.gpa,
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
    description: str = ""
    achievements: List[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "company": self.company,
            "title": self.title,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "location": self.location,
            "description": self.description,
            "achievements": self.achievements,
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
    achievements: List[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "description": self.description,
            "technologies": self.technologies,
            "achievements": self.achievements,
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
    confidence: float = 0.0


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
class ResumeData:
    """简历结构化数据"""
    personal_info: PersonalInfo = field(default_factory=PersonalInfo)
    education: List[EducationEntry] = field(default_factory=list)
    work_experience: List[WorkEntry] = field(default_factory=list)
    projects: List[ProjectEntry] = field(default_factory=list)
    skills: List[SkillEntry] = field(default_factory=list)
    certifications: List[Certification] = field(default_factory=list)
    languages: List[Language] = field(default_factory=list)
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
