"""
职位信息自动提取服务
支持从截图和PDF文档中提取职位信息
"""

from .service import JobExtractionService
from .models import ExtractedJobInfo, ExtractionResult, JobExtractionRequest
from .config import JobExtractionConfig

__all__ = [
    "JobExtractionService",
    "ExtractedJobInfo",
    "ExtractionResult",
    "JobExtractionConfig",
    "JobExtractionRequest",
]
