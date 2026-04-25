"""
职位信息提取服务
主服务类，协调文件解析和信息提取
"""

import time
import os
from typing import Optional
from pathlib import Path

from .models import (
    ExtractedJobInfo, 
    ExtractionResult, 
    JobExtractionRequest,
    JobExtractionResponse
)
from .config import config
from .parsers import TextExtractor, FileValidator
from .extractors import (
    JobTitleExtractor,
    CompanyNameExtractor,
    LocationExtractor,
    SalaryExtractor,
    ExperienceExtractor,
    EducationExtractor,
    JobTypeExtractor,
    HeadcountExtractor,
    DescriptionExtractor,
    RequirementsExtractor,
    BenefitsExtractor
)


class JobExtractionService:
    """职位信息提取服务"""
    
    def __init__(self):
        self.validator = FileValidator()
    
    def extract_from_file(self, file_path: str) -> ExtractionResult:
        """
        从文件中提取职位信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            ExtractionResult: 提取结果
        """
        start_time = time.time()
        
        # 验证文件
        is_valid, error_msg = self.validator.validate(file_path, config.MAX_FILE_SIZE)
        if not is_valid:
            return ExtractionResult(
                success=False,
                error_message=error_msg,
                processing_time=time.time() - start_time
            )
        
        # 获取文件信息
        file_size = os.path.getsize(file_path)
        file_type = self.validator.get_file_type(file_path)
        
        # 提取文本
        success, text, error_msg = TextExtractor.extract_text(file_path)
        if not success:
            return ExtractionResult(
                success=False,
                error_message=error_msg,
                processing_time=time.time() - start_time,
                file_type=file_type,
                file_size=file_size
            )
        
        # 提取职位信息
        job_info = self._extract_job_info(text)
        
        processing_time = time.time() - start_time
        
        return ExtractionResult(
            success=True,
            data=job_info,
            processing_time=processing_time,
            file_type=file_type,
            file_size=file_size
        )
    
    def extract_from_text(self, text: str) -> ExtractedJobInfo:
        """
        从文本中提取职位信息
        
        Args:
            text: 职位描述文本
            
        Returns:
            ExtractedJobInfo: 提取的职位信息
        """
        return self._extract_job_info(text)
    
    def _extract_job_info(self, text: str) -> ExtractedJobInfo:
        """
        提取职位信息的核心逻辑
        
        Args:
            text: 文本内容
            
        Returns:
            ExtractedJobInfo: 提取的职位信息
        """
        job_info = ExtractedJobInfo()
        job_info.raw_text = text
        
        # 提取职位名称
        extractor = JobTitleExtractor(text)
        job_info.job_title = extractor.extract()
        
        # 提取公司名称
        extractor = CompanyNameExtractor(text)
        job_info.company_name = extractor.extract()
        
        # 提取工作地点
        extractor = LocationExtractor(text)
        job_info.location = extractor.extract()
        
        # 提取薪资
        extractor = SalaryExtractor(text)
        salary_min, salary_max, salary_unit = extractor.extract()
        job_info.salary_min = salary_min
        job_info.salary_max = salary_max
        job_info.salary_unit = salary_unit
        
        # 提取经验要求
        extractor = ExperienceExtractor(text)
        job_info.experience_required = extractor.extract()
        
        # 提取学历要求
        extractor = EducationExtractor(text)
        job_info.education_required = extractor.extract()
        
        # 提取工作类型
        extractor = JobTypeExtractor(text)
        job_info.job_type = extractor.extract()
        
        # 提取招聘人数
        extractor = HeadcountExtractor(text)
        job_info.headcount = extractor.extract()
        
        # 提取职位描述
        extractor = DescriptionExtractor(text)
        job_info.job_description = extractor.extract()
        
        # 提取任职资格
        extractor = RequirementsExtractor(text)
        job_info.job_requirements = extractor.extract()
        
        # 提取福利待遇
        extractor = BenefitsExtractor(text)
        job_info.benefits = extractor.extract()
        
        return job_info
    
    def process_request(self, request: JobExtractionRequest) -> JobExtractionResponse:
        """
        处理提取请求
        
        Args:
            request: 提取请求
            
        Returns:
            JobExtractionResponse: 提取响应
        """
        result = self.extract_from_file(request.file_path)
        
        if result.success:
            return JobExtractionResponse(
                success=True,
                job_info=result.data,
                message=f"提取成功，处理时间: {result.processing_time:.2f}秒",
                suggestions=self._generate_suggestions(result.data)
            )
        else:
            return JobExtractionResponse(
                success=False,
                message=result.error_message or "提取失败",
                suggestions=["请检查文件格式是否正确", "尝试上传更清晰的图片或PDF"]
            )
    
    def _generate_suggestions(self, job_info: ExtractedJobInfo) -> list:
        """生成改进建议"""
        suggestions = []
        
        # 检查低置信度字段
        fields_to_check = [
            (job_info.job_title, "职位名称"),
            (job_info.company_name, "公司名称"),
            (job_info.salary_min, "薪资范围"),
            (job_info.job_description, "职位描述"),
            (job_info.job_requirements, "任职资格"),
        ]
        
        for field, name in fields_to_check:
            if field is None or field.confidence < config.CONFIDENCE_THRESHOLD_MEDIUM:
                suggestions.append(f"{name}识别置信度较低，建议核对")
        
        # 检查缺失字段
        if job_info.job_title is None:
            suggestions.append("未识别到职位名称，请手动输入")
        if job_info.company_name is None:
            suggestions.append("未识别到公司名称，请手动输入")
        
        if not suggestions:
            suggestions.append("提取完成，请核对信息准确性")
        
        return suggestions


# 全局服务实例
job_extraction_service = JobExtractionService()
