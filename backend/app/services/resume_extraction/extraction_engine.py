"""
信息提取引擎
整合规则引擎和版面分析，提供统一的提取接口
"""

import logging
import time
from typing import Dict, Any, Optional
from dataclasses import asdict

from .models import (
    ParsedDocument, DocumentStructure, ResumeData, ExtractionMetadata,
    PersonalInfo, EducationEntry, WorkEntry, ProjectEntry, SkillEntry
)
from .pdf_parser import get_pdf_parser
from .layout_analyzer import get_layout_analyzer
from .rule_engine import get_rule_engine
from .quality_assessor import get_quality_assessor
from .config import extraction_config
from .utils import clean_text

logger = logging.getLogger(__name__)


class ExtractionEngine:
    """信息提取引擎"""
    
    def __init__(self):
        self.config = extraction_config
        self.pdf_parser = get_pdf_parser()
        self.layout_analyzer = get_layout_analyzer()
        self.rule_engine = get_rule_engine()
        self.quality_assessor = get_quality_assessor()
    
    def extract_from_file(self, file_path: str) -> ResumeData:
        """
        从文件提取简历信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            ResumeData: 提取的简历数据
        """
        start_time = time.time()
        
        logger.info(f"开始提取简历信息: {file_path}")
        
        # 1. 解析PDF
        document = self.pdf_parser.parse(file_path)
        
        # 2. 版面分析
        structure = self.layout_analyzer.analyze(document)
        document.structure = structure
        
        # 3. 信息提取
        extracted_data = self.rule_engine.extract(document, structure)
        
        # 4. 构建ResumeData
        resume_data = self._build_resume_data(extracted_data, document)
        
        # 5. 质量评估
        quality_report = self.quality_assessor.assess(resume_data, document.raw_text)
        
        # 6. 更新元数据
        extraction_time_ms = int((time.time() - start_time) * 1000)
        resume_data.metadata = ExtractionMetadata(
            parser_engine=document.metadata.get("engine", "unknown"),
            ocr_engine=document.metadata.get("ocr_engine"),
            confidence_score=quality_report.overall_score,
            field_confidence=quality_report.field_scores,
            completeness_score=quality_report.completeness_score,
            extraction_time_ms=extraction_time_ms,
            pdf_type=document.pdf_type
        )
        
        # 保存原始文本预览
        resume_data.raw_text_preview = document.raw_text[:2000] if len(document.raw_text) > 2000 else document.raw_text
        
        logger.info(f"简历提取完成: 耗时 {extraction_time_ms}ms, 置信度 {quality_report.overall_score:.2f}")
        
        return resume_data
    
    def extract_from_text(self, text: str) -> ResumeData:
        """
        从文本提取简历信息
        
        Args:
            text: 简历文本
            
        Returns:
            ResumeData: 提取的简历数据
        """
        start_time = time.time()
        
        logger.info("开始从文本提取简历信息...")
        
        # 创建ParsedDocument
        from .models import ParsedDocument, PDFType
        document = ParsedDocument(
            raw_text=text,
            text_blocks=[],
            image_blocks=[],
            pdf_type=PDFType.TEXT,
            page_count=1,
            metadata={"source": "text"}
        )
        
        # 版面分析
        structure = self.layout_analyzer.analyze(document)
        document.structure = structure
        
        # 信息提取
        extracted_data = self.rule_engine.extract(document, structure)
        
        # 构建ResumeData
        resume_data = self._build_resume_data(extracted_data, document)
        
        # 质量评估
        quality_report = self.quality_assessor.assess(resume_data, text)
        
        # 更新元数据
        extraction_time_ms = int((time.time() - start_time) * 1000)
        resume_data.metadata = ExtractionMetadata(
            parser_engine="text",
            confidence_score=quality_report.overall_score,
            field_confidence=quality_report.field_scores,
            completeness_score=quality_report.completeness_score,
            extraction_time_ms=extraction_time_ms,
            pdf_type=PDFType.TEXT
        )
        
        resume_data.raw_text_preview = text[:2000] if len(text) > 2000 else text
        
        logger.info(f"文本提取完成: 耗时 {extraction_time_ms}ms, 置信度 {quality_report.overall_score:.2f}")
        
        return resume_data
    
    def _build_resume_data(self, extracted_data: Dict[str, Any], document: ParsedDocument) -> ResumeData:
        """构建ResumeData对象"""
        
        # 个人信息
        personal_info = extracted_data.get("personal_info", PersonalInfo())
        
        # 教育经历
        education = []
        for edu_dict in extracted_data.get("education", []):
            education.append(EducationEntry(**edu_dict))
        
        # 工作经历
        work_experience = []
        for work_dict in extracted_data.get("work_experience", []):
            work_experience.append(WorkEntry(**work_dict))
        
        # 项目经历
        projects = []
        for proj_dict in extracted_data.get("projects", []):
            projects.append(ProjectEntry(**proj_dict))
        
        # 技能
        skills = []
        for skill_dict in extracted_data.get("skills", []):
            skills.append(SkillEntry(**skill_dict))
        
        # 证书
        from .models import Certification
        certifications = []
        for cert_dict in extracted_data.get("certifications", []):
            certifications.append(Certification(**cert_dict))
        
        # 语言
        from .models import Language
        languages = []
        for lang_dict in extracted_data.get("languages", []):
            languages.append(Language(**lang_dict))
        
        return ResumeData(
            personal_info=personal_info,
            education=education,
            work_experience=work_experience,
            projects=projects,
            skills=skills,
            certifications=certifications,
            languages=languages,
            raw_text_preview="",
            metadata=ExtractionMetadata()
        )


# 单例模式
_extraction_engine = None


def get_extraction_engine() -> ExtractionEngine:
    """获取提取引擎单例"""
    global _extraction_engine
    if _extraction_engine is None:
        _extraction_engine = ExtractionEngine()
    return _extraction_engine


# 便捷函数
def extract_resume(file_path: str) -> ResumeData:
    """从文件提取简历的便捷函数"""
    engine = get_extraction_engine()
    return engine.extract_from_file(file_path)


def extract_resume_from_text(text: str) -> ResumeData:
    """从文本提取简历的便捷函数"""
    engine = get_extraction_engine()
    return engine.extract_from_text(text)
