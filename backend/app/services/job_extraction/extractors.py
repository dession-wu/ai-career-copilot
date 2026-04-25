"""
职位信息提取器
包含各个字段的提取逻辑
"""

import re
from typing import Optional, List, Dict, Tuple
from .models import FieldConfidence, ExtractedJobInfo
from .config import config


class BaseExtractor:
    """基础提取器"""
    
    def __init__(self, text: str):
        self.text = text
        self.lines = text.split('\n')
    
    def _create_field(self, field_name: str, value: any, confidence: float, raw_text: str = None) -> FieldConfidence:
        """创建字段置信度对象"""
        return FieldConfidence(
            field_name=field_name,
            value=value,
            confidence=confidence,
            raw_text=raw_text
        )
    
    def _find_line_with_keywords(self, keywords: List[str]) -> Optional[str]:
        """查找包含关键词的行"""
        for line in self.lines:
            for keyword in keywords:
                if keyword in line:
                    return line
        return None


class JobTitleExtractor(BaseExtractor):
    """职位名称提取器"""
    
    def extract(self) -> Optional[FieldConfidence]:
        """提取职位名称"""
        # 策略1: 查找包含职位关键词的行
        for line in self.lines[:20]:  # 检查前20行
            line = line.strip()
            if not line or len(line) > 50:
                continue
            
            # 检查是否包含职位关键词
            for keyword in config.JOB_TITLE_KEYWORDS:
                if keyword in line:
                    # 验证这是否是一个职位名称（不是段落）
                    if self._is_valid_job_title(line):
                        return self._create_field("job_title", line, 0.9, line)
        
        # 策略2: 查找"职位"、"岗位"后面的内容
        pattern = r'(?:职位|岗位|Job Title)[:：\s]*([^\n]{2,30})'
        match = re.search(pattern, self.text, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            if self._is_valid_job_title(title):
                return self._create_field("job_title", title, 0.85, title)
        
        # 策略3: 查找第一行（通常是职位名称）
        if self.lines:
            first_line = self.lines[0].strip()
            if self._is_valid_job_title(first_line):
                return self._create_field("job_title", first_line, 0.7, first_line)
        
        return None
    
    def _is_valid_job_title(self, text: str) -> bool:
        """验证是否为有效的职位名称"""
        if not text or len(text) < 2 or len(text) > 50:
            return False
        
        # 排除纯数字
        if text.isdigit():
            return False
        
        # 排除明显的非职位内容
        excluded = ['公司', '地址', '薪资', '联系', '电话', '邮箱', '微信']
        if any(word in text for word in excluded):
            return False
        
        return True


class CompanyNameExtractor(BaseExtractor):
    """公司名称提取器"""
    
    def extract(self) -> Optional[FieldConfidence]:
        """提取公司名称"""
        # 策略1: 匹配知名公司
        for company in config.WELL_KNOWN_COMPANIES:
            pattern = rf'\b{re.escape(company)}\b'
            if re.search(pattern, self.text, re.IGNORECASE):
                return self._create_field("company_name", company, 0.95, company)
        
        # 策略2: 查找包含公司后缀的名称
        for line in self.lines[:15]:
            line = line.strip()
            for suffix in config.COMPANY_SUFFIXES:
                pattern = rf'([\u4e00-\u9fa5]{{2,20}}(?:{re.escape(suffix)}))'
                match = re.search(pattern, line)
                if match:
                    company = match.group(1)
                    return self._create_field("company_name", company, 0.85, company)
        
        # 策略3: 查找"公司"、"企业"后面的内容
        pattern = r'(?:公司|企业|Company)[:：\s]*([^\n]{2,40})'
        match = re.search(pattern, self.text, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            return self._create_field("company_name", company, 0.8, company)
        
        return None


class LocationExtractor(BaseExtractor):
    """工作地点提取器"""
    
    def extract(self) -> Optional[FieldConfidence]:
        """提取工作地点"""
        locations = []
        
        # 策略1: 查找地点关键词
        for line in self.lines[:20]:
            line = line.strip()
            
            # 检查远程工作
            for keyword in config.REMOTE_KEYWORDS:
                if keyword in line:
                    return self._create_field("location", "远程/居家办公", 0.9, line)
            
            # 检查省份和城市
            for province in config.LOCATION_KEYWORDS["provinces"]:
                if province in line and province not in locations:
                    locations.append(province)
            
            for city in config.LOCATION_KEYWORDS["cities"]:
                if city in line and city not in locations:
                    locations.append(city)
        
        if locations:
            location_str = "、".join(locations[:3])  # 最多3个地点
            return self._create_field("location", location_str, 0.85, location_str)
        
        # 策略2: 查找"地点"、"地址"后面的内容
        pattern = r'(?:地点|地址|Location|Place)[:：\s]*([^\n]{2,30})'
        match = re.search(pattern, self.text, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            return self._create_field("location", location, 0.8, location)
        
        return None


class SalaryExtractor(BaseExtractor):
    """薪资范围提取器"""
    
    def extract(self) -> Tuple[Optional[FieldConfidence], Optional[FieldConfidence], Optional[FieldConfidence]]:
        """提取薪资范围，返回 (min, max, unit)"""
        
        # 策略1: 使用正则表达式匹配
        for pattern_str in config.SALARY_PATTERNS:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            match = pattern.search(self.text)
            if match:
                min_salary = match.group(1)
                max_salary = match.group(2) if match.group(2) else min_salary
                
                # 确定单位
                unit = "月"  # 默认
                if "万" in match.group(0):
                    unit = "年"
                elif "年薪" in match.group(0):
                    unit = "年"
                
                # 转换为数字
                try:
                    min_val = int(min_salary)
                    max_val = int(max_salary)
                    
                    # 标准化（统一为千）
                    if "k" in match.group(0).lower() or min_val < 100:
                        min_val = min_val
                        max_val = max_val
                    elif min_val > 1000:  # 可能是元
                        min_val = min_val // 1000
                        max_val = max_val // 1000
                    elif min_val > 10:  # 可能是万
                        min_val = min_val * 10
                        max_val = max_val * 10
                    
                    return (
                        self._create_field("salary_min", min_val, 0.85, match.group(0)),
                        self._create_field("salary_max", max_val, 0.85, match.group(0)),
                        self._create_field("salary_unit", unit, 0.85, match.group(0))
                    )
                except ValueError:
                    pass
        
        # 策略2: 查找"薪资"、"工资"后面的内容
        pattern = r'(?:薪资|工资|Salary)[:：\s]*([^\n]{2,30})'
        match = re.search(pattern, self.text, re.IGNORECASE)
        if match:
            salary_text = match.group(1).strip()
            # 尝试提取数字
            numbers = re.findall(r'\d+', salary_text)
            if len(numbers) >= 2:
                return (
                    self._create_field("salary_min", int(numbers[0]), 0.7, salary_text),
                    self._create_field("salary_max", int(numbers[1]), 0.7, salary_text),
                    self._create_field("salary_unit", "月", 0.7, salary_text)
                )
            elif len(numbers) == 1:
                val = int(numbers[0])
                return (
                    self._create_field("salary_min", val, 0.7, salary_text),
                    self._create_field("salary_max", val, 0.7, salary_text),
                    self._create_field("salary_unit", "月", 0.7, salary_text)
                )
        
        return None, None, None


class ExperienceExtractor(BaseExtractor):
    """工作经验提取器"""
    
    def extract(self) -> Optional[FieldConfidence]:
        """提取工作经验要求"""
        
        # 策略1: 使用正则表达式匹配
        for pattern_str in config.EXPERIENCE_PATTERNS:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            match = pattern.search(self.text)
            if match:
                years = match.group(1)
                experience = f"{years}年以上"
                return self._create_field("experience_required", experience, 0.85, match.group(0))
        
        # 策略2: 查找经验关键词
        for keyword, value in config.EXPERIENCE_KEYWORDS.items():
            pattern = rf'\b{re.escape(keyword)}\b'
            if re.search(pattern, self.text, re.IGNORECASE):
                return self._create_field("experience_required", value, 0.8, keyword)
        
        # 策略3: 查找"经验"后面的内容
        pattern = r'(?:经验|Experience)[:：\s]*([^\n]{2,20})'
        match = re.search(pattern, self.text, re.IGNORECASE)
        if match:
            experience = match.group(1).strip()
            return self._create_field("experience_required", experience, 0.75, experience)
        
        return None


class EducationExtractor(BaseExtractor):
    """学历要求提取器"""
    
    def extract(self) -> Optional[FieldConfidence]:
        """提取学历要求"""
        
        # 策略1: 查找学历关键词
        for keyword, value in config.EDUCATION_KEYWORDS.items():
            pattern = rf'\b{re.escape(keyword)}\b'
            if re.search(pattern, self.text, re.IGNORECASE):
                return self._create_field("education_required", value, 0.85, keyword)
        
        # 策略2: 查找"学历"后面的内容
        pattern = r'(?:学历|Education)[:：\s]*([^\n]{2,20})'
        match = re.search(pattern, self.text, re.IGNORECASE)
        if match:
            education = match.group(1).strip()
            return self._create_field("education_required", education, 0.75, education)
        
        return None


class JobTypeExtractor(BaseExtractor):
    """工作类型提取器"""
    
    def extract(self) -> Optional[FieldConfidence]:
        """提取工作类型"""
        
        # 查找工作类型关键词
        for keyword, value in config.JOB_TYPE_KEYWORDS.items():
            pattern = rf'\b{re.escape(keyword)}\b'
            if re.search(pattern, self.text, re.IGNORECASE):
                return self._create_field("job_type", value, 0.85, keyword)
        
        # 默认全职
        return self._create_field("job_type", "全职", 0.5, None)


class HeadcountExtractor(BaseExtractor):
    """招聘人数提取器"""
    
    def extract(self) -> Optional[FieldConfidence]:
        """提取招聘人数"""
        
        # 策略1: 查找数字+人
        pattern = r'(\d+)\s*人'
        match = re.search(pattern, self.text)
        if match:
            count = int(match.group(1))
            return self._create_field("headcount", count, 0.8, match.group(0))
        
        # 策略2: 查找"若干"、"不限"、"多名"
        keywords = ["若干", "不限", "多名", "若干名"]
        for keyword in keywords:
            if keyword in self.text:
                return self._create_field("headcount", keyword, 0.75, keyword)
        
        # 策略3: 查找"人数"后面的内容
        pattern = r'(?:人数|Headcount|招聘人数)[:：\s]*([^\n]{1,10})'
        match = re.search(pattern, self.text, re.IGNORECASE)
        if match:
            headcount = match.group(1).strip()
            return self._create_field("headcount", headcount, 0.7, headcount)
        
        return None


class DescriptionExtractor(BaseExtractor):
    """职位描述提取器"""
    
    def extract(self) -> Optional[FieldConfidence]:
        """提取岗位职责"""
        
        # 查找职责章节
        for keyword in config.SECTION_KEYWORDS["job_description"]:
            pattern = rf'{re.escape(keyword)}[：:\s]*\n?([^\n]+(?:\n[^\n]+)*)'
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                description = match.group(1).strip()
                # 限制长度
                if len(description) > 1000:
                    description = description[:1000] + "..."
                return self._create_field("job_description", description, 0.8, description)
        
        return None


class RequirementsExtractor(BaseExtractor):
    """任职资格提取器"""
    
    def extract(self) -> Optional[FieldConfidence]:
        """提取任职资格"""
        
        # 查找要求章节
        for keyword in config.SECTION_KEYWORDS["job_requirements"]:
            pattern = rf'{re.escape(keyword)}[：:\s]*\n?([^\n]+(?:\n[^\n]+)*)'
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                requirements = match.group(1).strip()
                # 限制长度
                if len(requirements) > 1000:
                    requirements = requirements[:1000] + "..."
                return self._create_field("job_requirements", requirements, 0.8, requirements)
        
        return None


class BenefitsExtractor(BaseExtractor):
    """福利待遇提取器"""
    
    def extract(self) -> Optional[FieldConfidence]:
        """提取福利待遇"""
        
        # 查找福利章节
        for keyword in config.SECTION_KEYWORDS["benefits"]:
            pattern = rf'{re.escape(keyword)}[：:\s]*\n?([^\n]+(?:\n[^\n]+)*)'
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                benefits = match.group(1).strip()
                if len(benefits) > 500:
                    benefits = benefits[:500] + "..."
                return self._create_field("benefits", benefits, 0.75, benefits)
        
        return None
