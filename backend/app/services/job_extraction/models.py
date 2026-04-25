"""
职位信息提取数据模型
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class JobType(str, Enum):
    """工作类型"""
    FULL_TIME = "全职"
    PART_TIME = "兼职"
    INTERNSHIP = "实习"
    CONTRACT = "合同"
    FREELANCE = "自由职业"


class ExperienceLevel(str, Enum):
    """经验要求级别"""
    FRESH_GRADUATE = "应届生"
    LESS_THAN_1_YEAR = "1年以内"
    ONE_TO_3_YEARS = "1-3年"
    THREE_TO_5_YEARS = "3-5年"
    FIVE_TO_10_YEARS = "5-10年"
    MORE_THAN_10_YEARS = "10年以上"
    NO_REQUIREMENT = "经验不限"


class EducationLevel(str, Enum):
    """学历要求级别"""
    HIGH_SCHOOL = "高中"
    ASSOCIATE = "大专"
    BACHELOR = "本科"
    MASTER = "硕士"
    PHD = "博士"
    NO_REQUIREMENT = "学历不限"


@dataclass
class FieldConfidence:
    """字段置信度"""
    field_name: str
    value: Any
    confidence: float  # 0.0 - 1.0
    raw_text: Optional[str] = None


@dataclass
class ExtractedJobInfo:
    """提取的职位信息"""
    # 基本信息
    job_title: Optional[FieldConfidence] = None  # 职位名称
    company_name: Optional[FieldConfidence] = None  # 公司名称
    location: Optional[FieldConfidence] = None  # 工作地点
    
    # 薪资福利
    salary_min: Optional[FieldConfidence] = None  # 最低薪资
    salary_max: Optional[FieldConfidence] = None  # 最高薪资
    salary_unit: Optional[FieldConfidence] = None  # 薪资单位（月/年）
    
    # 要求
    experience_required: Optional[FieldConfidence] = None  # 经验要求
    education_required: Optional[FieldConfidence] = None  # 学历要求
    
    # 职位详情
    job_type: Optional[FieldConfidence] = None  # 工作类型
    headcount: Optional[FieldConfidence] = None  # 招聘人数
    
    # 详细描述
    job_description: Optional[FieldConfidence] = None  # 岗位职责
    job_requirements: Optional[FieldConfidence] = None  # 任职资格
    
    # 额外信息
    benefits: Optional[FieldConfidence] = None  # 福利待遇
    department: Optional[FieldConfidence] = None  # 所属部门
    report_to: Optional[FieldConfidence] = None  # 汇报对象
    
    # 原始文本
    raw_text: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        for key, value in self.__dict__.items():
            if key == "raw_text":
                continue
            if isinstance(value, FieldConfidence):
                result[key] = {
                    "value": value.value,
                    "confidence": value.confidence,
                    "raw_text": value.raw_text
                }
            else:
                result[key] = value
        return result
    
    def get_overall_confidence(self) -> float:
        """获取整体置信度"""
        confidences = []
        for key, value in self.__dict__.items():
            if isinstance(value, FieldConfidence) and value.confidence > 0:
                confidences.append(value.confidence)
        
        if not confidences:
            return 0.0
        return sum(confidences) / len(confidences)


@dataclass
class ExtractionResult:
    """提取结果"""
    success: bool
    data: Optional[ExtractedJobInfo] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0  # 处理时间（秒）
    file_type: Optional[str] = None  # 文件类型
    file_size: int = 0  # 文件大小（字节）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "data": self.data.to_dict() if self.data else None,
            "error_message": self.error_message,
            "processing_time": self.processing_time,
            "file_type": self.file_type,
            "file_size": self.file_size
        }


@dataclass
class JobExtractionRequest:
    """提取请求"""
    file_path: str
    file_name: str
    file_type: str
    user_id: Optional[str] = None
    
    
@dataclass
class JobExtractionResponse:
    """提取响应"""
    success: bool
    job_info: Optional[ExtractedJobInfo] = None
    message: str = ""
    suggestions: List[str] = field(default_factory=list)
