"""
简历信息提取服务模块

提供从简历PDF/Word文件中提取结构化信息的能力
支持多引擎PDF解析、OCR识别、版面分析和混合策略提取
"""

# 首先配置PaddleOCR模型路径（必须在导入其他模块之前）
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.paddlex_config import ensure_model_path, PADDLEX_MODEL_PATH

from .models import (
    ParsedDocument,
    TextBlock,
    ImageBlock,
    OCRResult,
    ResumeData,
    PersonalInfo,
    EducationEntry,
    WorkEntry,
    ProjectEntry,
    SkillEntry,
    ExtractionMetadata,
    QualityReport,
    DocumentStructure,
    Section,
)
from .pdf_parser import PDFParser
from .ocr_engine import OCREngine
from .layout_analyzer import LayoutAnalyzer
from .extraction_engine import ExtractionEngine
from .quality_assessor import QualityAssessor
from .resume_extraction_service import ResumeExtractionService

__all__ = [
    # 数据模型
    "ParsedDocument",
    "TextBlock",
    "ImageBlock",
    "OCRResult",
    "ResumeData",
    "PersonalInfo",
    "EducationEntry",
    "WorkEntry",
    "ProjectEntry",
    "SkillEntry",
    "ExtractionMetadata",
    "QualityReport",
    "DocumentStructure",
    "Section",
    # 核心服务
    "PDFParser",
    "OCREngine",
    "LayoutAnalyzer",
    "ExtractionEngine",
    "QualityAssessor",
    "ResumeExtractionService",
]
