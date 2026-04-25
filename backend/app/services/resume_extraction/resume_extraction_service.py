"""
简历信息提取服务
对外提供统一的简历提取接口
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .extraction_engine import get_extraction_engine, extract_resume, extract_resume_from_text
from .quality_assessor import get_quality_assessor
from .models import ResumeData, QualityReport

logger = logging.getLogger(__name__)


class ResumeExtractionService:
    """简历信息提取服务"""
    
    def __init__(self):
        self.extraction_engine = get_extraction_engine()
        self.quality_assessor = get_quality_assessor()
    
    async def extract_from_file(self, file_path: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        从文件提取简历信息
        
        Args:
            file_path: PDF文件路径
            user_id: 用户ID（可选）
            
        Returns:
            包含提取结果和质量报告的字典
        """
        logger.info(f"开始提取简历: {file_path}, user_id={user_id}")
        
        try:
            # 执行提取
            resume_data = self.extraction_engine.extract_from_file(file_path)
            
            # 质量评估
            quality_report = self.quality_assessor.assess(
                resume_data, 
                resume_data.raw_text_preview
            )
            
            # 转换为字典
            result = {
                "success": True,
                "data": resume_data.to_dict(),
                "quality": quality_report.to_dict(),
                "needs_review": quality_report.overall_score < 0.7,
            }
            
            logger.info(f"简历提取成功: 置信度={quality_report.overall_score:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"简历提取失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "data": None,
                "quality": None,
                "needs_review": True,
            }
    
    async def extract_from_text(self, text: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        从文本提取简历信息
        
        Args:
            text: 简历文本
            user_id: 用户ID（可选）
            
        Returns:
            包含提取结果和质量报告的字典
        """
        logger.info(f"开始从文本提取简历, user_id={user_id}")
        
        try:
            # 执行提取
            resume_data = self.extraction_engine.extract_from_text(text)
            
            # 质量评估
            quality_report = self.quality_assessor.assess(resume_data, text)
            
            # 转换为字典
            result = {
                "success": True,
                "data": resume_data.to_dict(),
                "quality": quality_report.to_dict(),
                "needs_review": quality_report.overall_score < 0.7,
            }
            
            logger.info(f"文本提取成功: 置信度={quality_report.overall_score:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"文本提取失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "data": None,
                "quality": None,
                "needs_review": True,
            }
    
    def validate_extraction(self, resume_data: ResumeData) -> Dict[str, Any]:
        """
        验证提取结果
        
        Args:
            resume_data: 提取的简历数据
            
        Returns:
            验证结果
        """
        issues = []
        warnings = []
        
        # 检查关键字段
        if not resume_data.personal_info.name:
            issues.append("缺少姓名")
        
        if not resume_data.education:
            warnings.append("缺少教育经历")
        
        if not resume_data.work_experience and not resume_data.projects:
            warnings.append("缺少工作经历和项目经历")
        
        if len(resume_data.skills) < 3:
            warnings.append("技能数量较少")
        
        # 检查置信度
        if resume_data.metadata.confidence_score < 0.5:
            issues.append("整体置信度过低")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
        }


# 单例模式
_resume_extraction_service = None


def get_resume_extraction_service() -> ResumeExtractionService:
    """获取简历提取服务单例"""
    global _resume_extraction_service
    if _resume_extraction_service is None:
        _resume_extraction_service = ResumeExtractionService()
    return _resume_extraction_service


# 便捷函数
async def extract_resume_file(file_path: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """提取简历文件的便捷函数"""
    service = get_resume_extraction_service()
    return await service.extract_from_file(file_path, user_id)


async def extract_resume_text(text: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """提取简历文本的便捷函数"""
    service = get_resume_extraction_service()
    return await service.extract_from_text(text, user_id)
