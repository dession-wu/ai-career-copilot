"""
规则引擎 - 基于规则和模式的信息提取
修复技能识别问题，支持多维度技能提取
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple

from .models import (
    ParsedDocument, DocumentStructure, Section, SectionType,
    PersonalInfo, EducationEntry, WorkEntry, ProjectEntry, SkillEntry,
    Certification, Language
)
from .config import skill_config
from .utils import (
    extract_email, extract_phone, extract_linkedin, extract_website,
    extract_date_range, clean_text, is_chinese_name, is_english_name,
    infer_skill_level
)

logger = logging.getLogger(__name__)


class RuleEngine:
    """基于规则的信息提取引擎"""
    
    def __init__(self):
        self.skill_config = skill_config
        self._compile_patterns()
    
    def _compile_patterns(self):
        """编译正则表达式模式"""
        # 姓名模式
        self.name_patterns = [
            re.compile(r'^[\u4e00-\u9fa5]{2,4}$'),  # 中文姓名
            re.compile(r'^[A-Z][a-z]+\s+[A-Z][a-z]+$'),  # 英文姓名
        ]
        
        # 时间模式
        self.date_patterns = [
            re.compile(r'(20\d{2})[\.\-/年](\d{1,2})?\s*[\-–~]\s*(20\d{2})?[\.\-/年]?(\d{1,2}|至今|Present)?'),
            re.compile(r'(20\d{2})\s*[\-–~]\s*(20\d{2}|至今|Present)'),
        ]
        
        # 技能模式 - 扩展版本，支持别名
        self.skill_patterns = []
        self.skill_aliases = {}  # 别名到标准名称的映射
        
        for category, config in self.skill_config.skill_categories.items():
            # 添加主关键词
            for skill in config["keywords"]:
                # 单词边界匹配（英文）或精确匹配（中文）
                if any('\u4e00' <= c <= '\u9fff' for c in skill):
                    # 中文技能 - 使用精确匹配
                    pattern = rf'(?:^|[\s\、\,\，\;\；\|\/\·]){re.escape(skill)}(?:$|[\s\、\,\，\;\；\|\/\·])'
                else:
                    # 英文技能 - 使用单词边界
                    pattern = rf'\b{re.escape(skill)}\b'
                self.skill_patterns.append((category, skill, re.compile(pattern, re.IGNORECASE)))
            
            # 添加别名映射
            if "aliases" in config:
                for standard_name, aliases in config["aliases"].items():
                    self.skill_aliases[standard_name.lower()] = standard_name
                    for alias in aliases:
                        self.skill_aliases[alias.lower()] = standard_name
                        # 为别名也创建匹配模式
                        if any('\u4e00' <= c <= '\u9fff' for c in alias):
                            pattern = rf'(?:^|[\s\、\,\，\;\；\|\/\·]){re.escape(alias)}(?:$|[\s\、\,\，\;\；\|\/\·])'
                        else:
                            pattern = rf'\b{re.escape(alias)}\b'
                        self.skill_patterns.append((category, standard_name, re.compile(pattern, re.IGNORECASE)))
    
    def extract(self, document: ParsedDocument, structure: DocumentStructure) -> Dict[str, Any]:
        """
        使用规则引擎提取信息
        
        Args:
            document: 解析后的文档
            structure: 文档结构
            
        Returns:
            提取的结构化数据
        """
        logger.info("使用规则引擎提取信息...")
        
        result = {
            "personal_info": self._extract_personal_info(document.raw_text),
            "education": [],
            "work_experience": [],
            "projects": [],
            "skills": [],
            "certifications": [],
            "languages": [],
        }
        
        # 按章节提取
        for section in structure.sections:
            if section.section_type == SectionType.EDUCATION:
                result["education"] = self._extract_education(section)
            elif section.section_type == SectionType.WORK_EXPERIENCE:
                result["work_experience"] = self._extract_work_experience(section)
            elif section.section_type == SectionType.PROJECTS:
                result["projects"] = self._extract_projects(section)
            elif section.section_type == SectionType.SKILLS:
                result["skills"] = self._extract_skills(section, document.raw_text)
            elif section.section_type == SectionType.CERTIFICATIONS:
                result["certifications"] = self._extract_certifications(section)
            elif section.section_type == SectionType.LANGUAGES:
                result["languages"] = self._extract_languages(section)
        
        # 如果没有找到技能章节，从全文提取
        if not result["skills"]:
            result["skills"] = self._extract_skills_from_full_text(document.raw_text)
        
        logger.info(f"规则引擎提取完成: {len(result['education'])} 教育, {len(result['work_experience'])} 工作, {len(result['skills'])} 技能")
        return result
    
    def _extract_personal_info(self, text: str) -> PersonalInfo:
        """提取个人信息 - 增强版本，支持多行解析和特殊分隔符"""
        info = PersonalInfo()
        
        lines = text.split('\n')
        
        # 提取姓名（通常在开头）
        for line in lines[:15]:  # 检查前15行
            line = line.strip()
            # 跳过空行和纯分隔符行
            if not line or line in ['丨', '|', '/', '-']:
                continue
            
            if is_chinese_name(line):
                info.name = line
                info.confidence = 0.9
                break
            elif is_english_name(line):
                info.name = line
                info.confidence = 0.8
                break
        
        # 提取邮箱 - 支持特殊分隔符
        email = self._extract_email_with_separators(text)
        if email:
            info.email = email
        
        # 提取电话
        phone = extract_phone(text)
        if phone:
            info.phone = phone
        
        # 提取LinkedIn
        linkedin = extract_linkedin(text)
        if linkedin:
            info.linkedin = linkedin
        
        # 提取个人网站
        website = extract_website(text)
        if website:
            info.website = website
        
        # 尝试从包含分隔符的行中提取额外信息
        self._extract_from_separated_lines(text, info)
        
        return info
    
    def _extract_email_with_separators(self, text: str) -> Optional[str]:
        """提取邮箱，支持特殊分隔符"""
        # 首先尝试标准提取
        email = extract_email(text)
        if email:
            return email
        
        # 尝试从分隔符行中提取
        # 模式：xxx丨邮箱：name@example.com丨xxx
        separator_patterns = [
            r'[\s丨|/]*(?:邮箱|E.?mail)[：:\s]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})',
            r'[\s丨|/]+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})[\s丨|/]+',
        ]
        
        for pattern in separator_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_from_separated_lines(self, text: str, info: PersonalInfo):
        """从包含分隔符的行中提取个人信息"""
        lines = text.split('\n')
        
        for line in lines[:20]:  # 检查前20行
            line = line.strip()
            if not line:
                continue
            
            # 检查是否包含分隔符
            has_separator = any(sep in line for sep in ['丨', '|', '/', '·'])
            
            if has_separator:
                # 尝试提取邮箱
                if not info.email:
                    email_match = re.search(r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})', line)
                    if email_match:
                        info.email = email_match.group(1)
                
                # 尝试提取电话
                if not info.phone:
                    phone_match = re.search(r'1[3-9]\d{9}', line)
                    if phone_match:
                        info.phone = phone_match.group(0)
    
    def _extract_education(self, section: Section) -> List[EducationEntry]:
        """提取教育经历"""
        entries = []
        content = section.content
        
        # 按条目分割
        paragraphs = self._split_into_entries(content)
        
        for para in paragraphs:
            entry = EducationEntry()
            
            # 提取学校
            school_patterns = [
                r'([\u4e00-\u9fa5]{2,20}(?:大学|学院|学校))',
                r'([\u4e00-\u9fa5]{2,20}(?:University|College|Institute|School))',
            ]
            for pattern in school_patterns:
                match = re.search(pattern, para, re.IGNORECASE)
                if match:
                    school = match.group(1).strip()
                    if len(school) > 2:
                        entry.school = school
                        break
            
            # 提取学位
            degree_keywords = {
                "博士": ["博士", "PhD", "Ph.D", "Doctor"],
                "硕士": ["硕士", "Master", "MBA", "EMBA"],
                "本科": ["本科", "学士", "Bachelor"],
                "专科": ["专科", "大专", "Associate"],
            }
            for degree, keywords in degree_keywords.items():
                for keyword in keywords:
                    if keyword in para:
                        entry.degree = degree
                        break
                if entry.degree:
                    break
            
            # 提取专业
            field_patterns = [
                r'(?:专业|Major)[:\s]*([\u4e00-\u9fa5]{2,15})',
                r'([\u4e00-\u9fa5]{2,10}(?:学|工程|技术|科学))',
            ]
            for pattern in field_patterns:
                match = re.search(pattern, para, re.IGNORECASE)
                if match:
                    field = match.group(1).strip()
                    if len(field) > 1 and field not in ["专业"]:
                        entry.field = field
                        break
            
            # 提取时间
            start_date, end_date = extract_date_range(para)
            entry.start_date = start_date
            entry.end_date = end_date
            
            # 提取GPA
            gpa_match = re.search(r'GPA[:\s]*([\d\.]+)', para, re.IGNORECASE)
            if gpa_match:
                entry.gpa = gpa_match.group(1)
            
            if entry.school:
                entry.confidence = 0.85
                entries.append(entry)
        
        return entries
    
    def _extract_work_experience(self, section: Section) -> List[WorkEntry]:
        """提取工作经历 - 增强版本，支持更多公司名称格式"""
        entries = []
        content = section.content
        
        # 按条目分割
        paragraphs = self._split_into_entries(content)
        
        for para in paragraphs:
            entry = WorkEntry()
            
            # 提取公司 - 扩展匹配模式
            company_patterns = [
                # 标准格式：XXX公司/集团
                r'([\u4e00-\u9fa5]{2,30}(?:公司|集团))',
                # 包含科技/网络/软件的
                r'([\u4e00-\u9fa5]{2,20}(?:科技|网络|软件|信息|技术))',
                # 知名互联网公司（可能不带公司后缀）
                r'\b(阿里巴巴|腾讯|字节跳动|百度|美团|京东|滴滴|快手|拼多多|网易|小米|华为|Google|Microsoft|Amazon|Facebook|Meta|Apple)\b',
                # 金融机构
                r'([\u4e00-\u9fa5]{2,20}(?:证券|银行|保险|基金|投资))',
                # 外企
                r'([A-Za-z\s]{2,30}(?:Corp|Inc|Ltd|Company|Group))',
            ]
            for pattern in company_patterns:
                match = re.search(pattern, para, re.IGNORECASE)
                if match:
                    company = match.group(1).strip()
                    if len(company) > 1 and len(company) < 80:
                        entry.company = company
                        break
            
            # 如果没有找到公司，尝试提取第一行作为公司（常见格式）
            if not entry.company:
                lines = para.strip().split('\n')
                if lines:
                    first_line = lines[0].strip()
                    # 如果第一行不太长，可能包含公司名称
                    if 2 < len(first_line) < 40:
                        # 排除纯日期行
                        if not re.match(r'^\d{4}', first_line):
                            entry.company = first_line
            
            # 提取职位
            title_patterns = [
                r'(?:职位|岗位|职务)[:\s]*([^\n]+)',
                r'((?:高级|资深|初级|助理)?\s*[^\n]{2,20}(?:工程师|开发|经理|主管|总监|架构师|设计师|分析师|研究员))',
                r'((?:高级|资深|初级|助理)?\s*[^\n]{2,15}(?:专员|顾问|代表))',
            ]
            for pattern in title_patterns:
                match = re.search(pattern, para, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    title = re.sub(r'^(?:职位|岗位|职务)[:\s]*', '', title, flags=re.IGNORECASE)
                    if len(title) > 1 and len(title) < 50:
                        entry.title = title
                        break
            
            # 提取时间
            start_date, end_date = extract_date_range(para)
            entry.start_date = start_date
            entry.end_date = end_date
            
            # 提取描述
            entry.description = para
            
            if entry.company:
                entry.confidence = 0.8
                entries.append(entry)
        
        return entries
    
    def _extract_projects(self, section: Section) -> List[ProjectEntry]:
        """提取项目经历"""
        entries = []
        content = section.content
        
        # 按条目分割
        paragraphs = self._split_into_entries(content)
        
        for para in paragraphs:
            entry = ProjectEntry()
            
            lines = para.split('\n')
            
            # 第一行通常是项目名称
            if lines:
                first_line = lines[0].strip()
                first_line = re.sub(r'^[•\-\*・《]', '', first_line).strip()
                if first_line and len(first_line) < 100:
                    entry.name = first_line
            
            # 提取角色
            role_patterns = [
                r'(?:角色|职责|Role)[:\s]*([^\n]+)',
                r'((?:负责|担任)[^\n]{2,20}(?:开发|工程师|负责人))',
            ]
            for pattern in role_patterns:
                match = re.search(pattern, para, re.IGNORECASE)
                if match:
                    role = match.group(1).strip()
                    if len(role) > 1 and len(role) < 50:
                        entry.role = role
                        break
            
            # 提取时间
            start_date, end_date = extract_date_range(para)
            entry.start_date = start_date
            entry.end_date = end_date
            
            # 提取描述
            entry.description = para
            
            if entry.name:
                entry.confidence = 0.75
                entries.append(entry)
        
        return entries
    
    def _extract_skills(self, section: Section, full_text: str) -> List[SkillEntry]:
        """提取技能 - 修复版本，支持多维度提取"""
        skills = []
        content = section.content
        
        # 策略1: 从技能章节提取
        section_skills = self._extract_skills_from_text(content)
        skills.extend(section_skills)
        
        # 策略2: 如果技能章节内容较少，从全文补充
        if len(skills) < 5:
            full_text_skills = self._extract_skills_from_full_text(full_text)
            # 合并去重
            existing_names = {s.name.lower() for s in skills}
            for skill in full_text_skills:
                if skill.name.lower() not in existing_names:
                    skills.append(skill)
        
        return skills
    
    def _extract_skills_from_text(self, text: str) -> List[SkillEntry]:
        """从文本中提取技能"""
        skills = []
        found_skills = {}  # 用于去重
        
        # 方法1: 使用预定义的技能词库匹配
        for category, skill_name, pattern in self.skill_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                skill_name_clean = match.group(0)
                skill_key = skill_name_clean.lower()
                
                if skill_key not in found_skills:
                    found_skills[skill_key] = True
                    
                    # 推断熟练度
                    level = infer_skill_level(text, skill_name_clean)
                    
                    skill = SkillEntry(
                        name=skill_name_clean,
                        level=level,
                        category=self.skill_config.skill_categories[category]["display_name"],
                        confidence=0.85
                    )
                    skills.append(skill)
        
        # 方法2: 解析列表格式的技能
        list_skills = self._parse_skill_list(text)
        for skill_name in list_skills:
            skill_key = skill_name.lower()
            if skill_key not in found_skills:
                found_skills[skill_key] = True
                
                # 推断熟练度
                level = infer_skill_level(text, skill_name)
                
                # 推断类别
                category = self._infer_skill_category(skill_name)
                
                skill = SkillEntry(
                    name=skill_name,
                    level=level,
                    category=category,
                    confidence=0.75
                )
                skills.append(skill)
        
        return skills
    
    def _extract_skills_from_full_text(self, text: str) -> List[SkillEntry]:
        """从全文提取技能（用于补充）"""
        skills = []
        found_skills = {}
        
        # 只使用高置信度的技能词库匹配
        for category, skill_name, pattern in self.skill_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                skill_name_clean = match.group(0)
                skill_key = skill_name_clean.lower()
                
                if skill_key not in found_skills:
                    found_skills[skill_key] = True
                    
                    level = infer_skill_level(text, skill_name_clean)
                    
                    skill = SkillEntry(
                        name=skill_name_clean,
                        level=level,
                        category=self.skill_config.skill_categories[category]["display_name"],
                        confidence=0.7
                    )
                    skills.append(skill)
        
        return skills
    
    def _parse_skill_list(self, text: str) -> List[str]:
        """解析列表格式的技能 - 改进版本，支持多种分隔符混合"""
        skills = []
        
        # 清理文本 - 移除常见前缀
        text = re.sub(r'^[•\-\*・\s]+', '', text.strip())
        # 移除熟练度前缀
        text = re.sub(r'^(?:熟练掌握|精通|熟悉|了解|掌握|熟练)\s*', '', text)
        
        # 尝试多种分隔符 - 按优先级排序
        separators = ['、', '，', ',', ';', '；', '|', '/', '·', '\n', '\t']
        
        # 首先尝试找到主要分隔符
        primary_separator = None
        max_splits = 0
        for sep in separators:
            count = text.count(sep)
            if count > max_splits and count >= 2:  # 至少要有2个分隔符才认为是列表
                max_splits = count
                primary_separator = sep
        
        if primary_separator:
            items = text.split(primary_separator)
        else:
            # 尝试使用正则表达式分割多种分隔符
            items = re.split(r'[、,，;；|/·\n\t]+', text)
        
        for item in items:
            item = item.strip()
            # 清理列表符号和多余空格
            item = re.sub(r'^[•\-\*・\s]+', '', item).strip()
            item = re.sub(r'\s+', ' ', item)  # 合并多个空格
            # 移除每个项目中的熟练度前缀
            item = re.sub(r'^(?:熟练掌握|精通|熟悉|了解|掌握|熟练)\s*', '', item)
            
            # 过滤无效项
            if item and 1 < len(item) < 40 and not self._is_noise(item):
                # 标准化技能名称（使用别名映射）
                normalized = self._normalize_skill_name(item)
                skills.append(normalized)
        
        # 去重（保持顺序）
        seen = set()
        unique_skills = []
        for skill in skills:
            skill_lower = skill.lower()
            if skill_lower not in seen:
                seen.add(skill_lower)
                unique_skills.append(skill)
        
        return unique_skills
    
    def _normalize_skill_name(self, skill_name: str) -> str:
        """标准化技能名称 - 使用别名映射"""
        skill_lower = skill_name.lower()
        
        # 检查是否有别名映射
        if skill_lower in self.skill_aliases:
            return self.skill_aliases[skill_lower]
        
        # 检查是否是已知技能的变体
        for category, config in self.skill_config.skill_categories.items():
            keywords = config.get("keywords", [])
            for keyword in keywords:
                if skill_lower == keyword.lower():
                    return keyword
        
        return skill_name
    
    def _extract_skills_from_text(self, text: str) -> List[SkillEntry]:
        """从文本中提取技能 - 改进版本"""
        skills = []
        found_skills = {}  # 用于去重
        
        # 方法1: 使用预定义的技能词库匹配
        for category, skill_name, pattern in self.skill_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                skill_name_clean = match.group(0)
                skill_key = skill_name_clean.lower()
                
                if skill_key not in found_skills:
                    found_skills[skill_key] = True
                    
                    # 推断熟练度
                    level = infer_skill_level(text, skill_name_clean)
                    
                    skill = SkillEntry(
                        name=skill_name_clean,
                        level=level,
                        category=self.skill_config.skill_categories[category]["display_name"],
                        confidence=0.85
                    )
                    skills.append(skill)
        
        # 方法2: 解析列表格式的技能
        list_skills = self._parse_skill_list(text)
        for skill_name in list_skills:
            skill_key = skill_name.lower()
            if skill_key not in found_skills:
                found_skills[skill_key] = True
                
                # 推断熟练度
                level = infer_skill_level(text, skill_name)
                
                # 推断类别
                category = self._infer_skill_category(skill_name)
                
                skill = SkillEntry(
                    name=skill_name,
                    level=level,
                    category=category,
                    confidence=0.75
                )
                skills.append(skill)
        
        # 方法3: 处理组合格式（如"PS/PR"）
        combo_skills = self._extract_combo_skills(text)
        for skill_name in combo_skills:
            skill_key = skill_name.lower()
            if skill_key not in found_skills:
                found_skills[skill_key] = True
                
                level = infer_skill_level(text, skill_name)
                category = self._infer_skill_category(skill_name)
                
                skill = SkillEntry(
                    name=skill_name,
                    level=level,
                    category=category,
                    confidence=0.75
                )
                skills.append(skill)
        
        # 方法4: 全文扫描补充（用于极简格式简历）
        # 如果提取的技能太少，尝试从全文扫描
        if len(skills) < 3:
            full_text_skills = self._extract_skills_from_full_text(text)
            for skill in full_text_skills:
                skill_key = skill.name.lower()
                if skill_key not in found_skills:
                    found_skills[skill_key] = True
                    skills.append(skill)
        
        return skills
    
    def _extract_combo_skills(self, text: str) -> List[str]:
        """提取组合格式的技能（如"PS/PR"、"AI/AE"）"""
        skills = []
        
        # 查找类似 "PS/PR"、"AI/AE" 的模式
        # 这些通常是设计软件的缩写组合
        combo_pattern = r'\b([A-Z]{1,3})\/([A-Z]{1,3})\b'
        matches = re.finditer(combo_pattern, text)
        
        for match in matches:
            part1 = match.group(1)
            part2 = match.group(2)
            
            # 尝试标准化每个部分
            for part in [part1, part2]:
                normalized = self._normalize_skill_name(part)
                if normalized != part or part in ['PS', 'PR', 'AI', 'AE', 'LR', 'AU', 'CAD']:
                    skills.append(normalized)
        
        return skills
    
    def _is_noise(self, text: str) -> bool:
        """判断是否为噪声文本 - 增强版本"""
        # 过长的文本
        if len(text) > 50:
            return True
        
        # 纯数字
        if text.isdigit():
            return True
        
        # 常见噪声词
        noise_words = [
            '技能', '清单', '列表', 'Skills', '熟练掌握', '精通', '了解', '熟悉',
            '掌握', 'Skill', 'List', '清单', '列表', '技能清单', '技能列表',
            '专业技能', '职业技能', '个人技能', '技术技能', '技术栈',
            '熟练度', '水平', '能力', '特长', '专长'
        ]
        if text.strip() in noise_words:
            return True
        
        # 纯标点符号
        if re.match(r'^[\s\W]+$', text):
            return True
        
        # 过短的中文（可能是标点或语气词）
        if len(text) == 1 and any('\u4e00' <= c <= '\u9fff' for c in text):
            # 排除单个汉字技能如"R"、"C"、"Go"等
            if text not in ['R', 'C', 'D', 'Go']:
                return True
        
        return False
    
    def _infer_skill_category(self, skill_name: str) -> str:
        """推断技能类别"""
        skill_lower = skill_name.lower()
        
        for category, config in self.skill_config.skill_categories.items():
            keywords = [k.lower() for k in config["keywords"]]
            if skill_lower in keywords:
                return config["display_name"]
        
        return "其他"
    
    def _extract_certifications(self, section: Section) -> List[Certification]:
        """提取证书"""
        certifications = []
        content = section.content
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 移除列表符号
            line = re.sub(r'^[•\-\*・]', '', line).strip()
            
            if line and len(line) < 100:
                cert = Certification(name=line)
                certifications.append(cert)
        
        return certifications
    
    def _extract_languages(self, section: Section) -> List[Language]:
        """提取语言能力"""
        languages = []
        content = section.content
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 移除列表符号
            line = re.sub(r'^[•\-\*・]', '', line).strip()
            
            if line and len(line) < 50:
                lang = Language(name=line)
                languages.append(lang)
        
        return languages
    
    def _split_into_entries(self, text: str) -> List[str]:
        """将文本分割成条目"""
        # 策略1: 按空行分割
        paragraphs = re.split(r'\n\s*\n', text)
        
        # 策略2: 按时间模式分割
        if len(paragraphs) <= 1:
            paragraphs = re.split(r'(?=20\d{2}[\.\-/年])', text)
        
        # 策略3: 按列表符号分割
        if len(paragraphs) <= 1:
            paragraphs = re.split(r'(?=[•\-\*・])', text)
        
        return [p.strip() for p in paragraphs if p.strip()]


# 单例模式
_rule_engine = None

def get_rule_engine() -> RuleEngine:
    """获取规则引擎单例"""
    global _rule_engine
    if _rule_engine is None:
        _rule_engine = RuleEngine()
    return _rule_engine
