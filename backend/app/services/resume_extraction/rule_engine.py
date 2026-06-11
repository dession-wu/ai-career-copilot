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


def _normalize_local_date(date_str: str) -> str:
    """
    统一日期格式为 YYYY-MM（与 resume_extraction_service._normalize_date 行为一致）
    支持: YYYY.MM / YYYY/MM / YYYY-MM / YYYY / "至今" / "Present"
    P0-5 新增：用于 rule_engine 教育/工作条目的日期统一
    """
    if not date_str or not isinstance(date_str, str):
        return ""
    s = date_str.strip()
    if not s:
        return ""
    # 至今 / present 原样保留
    if s in ("至今", "现在", "Present", "present", "Now", "now"):
        return s
    # YYYY.MM / YYYY/MM / YYYY-MM
    m = re.match(r'^(\d{4})[\.\-/](\d{1,2})$', s)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    # YYYY年MM月
    m = re.match(r'^(\d{4})年(\d{1,2})月?$', s)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    # YYYY
    m = re.match(r'^(\d{4})$', s)
    if m:
        return f"{m.group(1)}-01"
    return s


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
        
        # 从工作经历中提取嵌套的项目经历
        if result["work_experience"]:
            nested_projects = self._extract_nested_projects_from_work(result["work_experience"])
            if nested_projects:
                # 合并到现有项目列表中，去重
                existing_names = {p.name for p in result["projects"]}
                for project in nested_projects:
                    if project.name not in existing_names:
                        result["projects"].append(project)
                        existing_names.add(project.name)
        
        logger.info(f"规则引擎提取完成: {len(result['education'])} 教育, {len(result['work_experience'])} 工作, {len(result['projects'])} 项目, {len(result['skills'])} 技能")
        return result
    
    def _extract_personal_info(self, text: str) -> PersonalInfo:
        """提取个人信息 - 增强版本，支持多行解析和特殊分隔符，扩展至前30行"""
        info = PersonalInfo()
        
        lines = text.split('\n')
        
        # 提取姓名（通常在开头）- 扩展至前30行
        for line in lines[:30]:
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
        
        # 提取求职意向
        job_intent = self._extract_job_intent(text)
        if job_intent:
            info.job_intent = job_intent
        
        # 提取工作年限
        years = self._extract_years_of_experience(text)
        if years:
            info.years_of_experience = years
        
        # 提取所在地
        location = self._extract_location(text)
        if location:
            info.location = location
        
        # 提取性别
        gender = self._extract_gender(text)
        if gender:
            info.gender = gender
        
        # 提取年龄
        age = self._extract_age(text)
        if age:
            info.age = age
        
        # 尝试从包含分隔符的行中提取额外信息
        self._extract_from_separated_lines(text, info)

        # ★ P0-6b: 增强基础信息提取 — 政治面貌 / 出生年月 / 籍贯
        self._extract_political_and_demographics(text, info)

        return info
    
    def _extract_job_intent(self, text: str) -> Optional[str]:
        """提取求职意向"""
        patterns = [
            r'(?:求职意向|目标岗位|应聘岗位|期望职位|意向岗位)[：:\s]*([^\n]{2,30})',
            r'(?:求职|应聘)[^\n]{0,10}(?:岗位|职位)[：:\s]*([^\n]{2,30})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                intent = match.group(1).strip()
                if len(intent) > 1 and len(intent) < 30:
                    return intent
        return None
    
    def _extract_years_of_experience(self, text: str) -> Optional[int]:
        """提取工作年限"""
        patterns = [
            r'(\d+)\s*年(?:以上)?\s*(?:工作|经验|相关经验)',
            r'(?:工作年限|经验)[：:\s]*(\d+)\s*年',
            r'(?:\d{4})\s*[-~至]\s*(?:至今|现在|present)',  # 从时间范围推算
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    years = int(match.group(1))
                    if 0 < years < 50:
                        return years
                except (ValueError, IndexError):
                    continue
        return None
    
    def _extract_location(self, text: str) -> Optional[str]:
        """提取所在地"""
        patterns = [
            r'(?:所在地|现居|居住|城市|地区)[：:\s]*([^\n]{2,20})',
            r'(?:所在城市|所在地区)[：:\s]*([^\n]{2,20})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                if len(location) > 1 and len(location) < 20:
                    return location
        return None
    
    def _extract_gender(self, text: str) -> Optional[str]:
        """提取性别"""
        patterns = [
            r'(?:性别|性別)[：:\s]*([男女])',
            r'\b([男女])\s*性\b',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _extract_age(self, text: str) -> Optional[int]:
        """提取年龄"""
        patterns = [
            r'(?:年龄|年齡)[：:\s]*(\d{2})',
            r'(\d{2})\s*岁',
            r'(19\d{2}|20\d{2})\s*年\s*出生',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    age = int(match.group(1))
                    if age > 1900:  # 出生年份
                        from datetime import datetime
                        age = datetime.now().year - age
                    if 18 < age < 70:
                        return age
                except (ValueError, IndexError):
                    continue
        return None
    
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

    def _extract_political_and_demographics(self, text: str, info: PersonalInfo):
        """
        P0-6b 新增：从文本中提取政治面貌、出生年月、籍贯
        支持格式：'中共党员丨2002.10丨安徽安庆' 等带 丨/|/｜/ 分隔符的行
        """
        lines = text.split('\n')
        # 政治面貌映射表（中文 → 内部值）
        political_map = [
            ('中共预备党员', 'party_member'),
            ('中共党员', 'party_member'),
            ('预备党员', 'party_member'),
            ('共青团员', 'league_member'),
            ('群众', 'mass'),
            ('无党派人士', 'mass'),
            ('民主党派', 'mass'),
            ('民盟盟员', 'mass'),
            ('民革党员', 'mass'),
            ('民建会员', 'mass'),
            ('民进会员', 'mass'),
            ('致公党党员', 'mass'),
            ('九三学社社员', 'mass'),
            ('台盟盟员', 'mass'),
        ]

        for line in lines[:25]:  # 检查前 25 行
            line_stripped = line.strip()
            if not line_stripped or len(line_stripped) > 120:
                continue
            # 必须含分隔符
            if not any(sep in line_stripped for sep in ['丨', '|', '｜', '/']):
                continue

            parts = re.split(r'[丨|｜/]', line_stripped)
            for part in parts:
                part = part.strip()
                if not part:
                    continue

                # 政治面貌（按出现顺序匹配，'中共预备党员' 必须先于'中共党员'）
                if not info.political_status:
                    for cn, en in political_map:
                        if cn in part:
                            info.political_status = en
                            break

                # 出生年月
                if not info.birth_date:
                    # 2002.10 / 2002/10 / 2002-10 / 2002年10月
                    m = re.match(r'^(19|20)\d{2}[\.\-/年](\d{1,2})?', part)
                    if m:
                        raw = m.group(0)
                        year = raw[:4]
                        rest = raw[4:]
                        m2 = re.search(r'(\d{1,2})', rest)
                        month = m2.group(1).zfill(2) if m2 else '01'
                        info.birth_date = f"{year}-{month}"
                        # 推算年龄
                        from datetime import datetime
                        info.age = datetime.now().year - int(year)

                # 籍贯/所在地
                if not info.location:
                    # 常见省市简称（无需后缀也能识别）
                    known_cities = [
                        '北京', '上海', '天津', '重庆',
                        '广州', '深圳', '杭州', '南京', '苏州', '武汉', '成都',
                        '西安', '青岛', '厦门', '宁波', '济南', '合肥', '福州',
                        '长沙', '郑州', '石家庄', '太原', '兰州', '南昌', '贵阳',
                        '昆明', '南宁', '海口', '三亚', '拉萨', '乌鲁木齐', '银川',
                        '西宁', '呼和浩特', '沈阳', '大连', '长春', '哈尔滨', '安庆',
                        '香港', '澳门', '台北',
                    ]
                    # 常见省份前缀
                    known_provinces = [
                        '河北', '山西', '辽宁', '吉林', '黑龙江', '江苏', '浙江',
                        '安徽', '福建', '江西', '山东', '河南', '湖北', '湖南',
                        '广东', '海南', '四川', '贵州', '云南', '陕西', '甘肃',
                        '青海', '台湾', '内蒙古', '广西', '西藏', '宁夏', '新疆',
                    ]
                    location_keywords = ['省', '市', '区', '县', '州', '盟', '旗', '地区']
                    is_location = (
                        any(kw in part for kw in location_keywords)
                        or part in known_cities
                        or any(part.endswith(c) for c in known_cities)
                        or part in known_provinces
                    )
                    if is_location and 2 <= len(part) <= 20:
                        # 排除明显是手机号/邮箱/日期的行
                        if not re.match(r'^\d+$', part) and '@' not in part and not re.match(r'^(19|20)\d{2}', part):
                            info.location = part

    def _extract_education(self, section: Section) -> List[EducationEntry]:
        """提取教育经历 — P0-5 增强版

        优化点：
        1. 教育特征优先判定（含学校/学历关键词）
        2. 日期+学校同时出现 → 强教育信号（覆盖工作特征误判）
        3. 调用 _parse_education_paragraph 支持括号内专业提取
        """
        entries = []
        if not section or not section.content:
            return entries

        paragraphs = self._split_into_entries(section.content)

        # 关键词定义
        school_keywords = ['大学', '学院', '学校', 'University', 'College', 'Institute', '理工', '师范']
        degree_keywords = ['本科', '硕士', '博士', '学士', 'Bachelor', 'Master', 'PhD', '研究生', '专科', '大专']
        work_keywords = ['公司', '集团', 'Corp', 'Inc', 'Ltd', '工程师', '开发', '经理', '主管']
        date_pattern = r'20\d{2}[\.\-/年]'

        for para in paragraphs:
            if not para or not para.strip():
                continue

            # ★ 优先判定为教育：含学校/学历关键词
            has_school_kw = any(kw in para for kw in school_keywords)
            has_degree_kw = any(kw in para for kw in degree_keywords)
            is_education = has_school_kw or has_degree_kw

            # ★ 日期+学校同时出现 → 强教育信号（覆盖默认判定）
            has_date = re.search(date_pattern, para)
            if has_date and has_school_kw:
                is_education = True

            # 排除工作特征干扰（仅当无学校关键词时才排除）
            has_work = any(kw in para for kw in work_keywords)
            if is_education and not (has_work and not has_school_kw):
                entry = self._parse_education_paragraph(para)
                if entry and entry.school:
                    entries.append(entry)

        return entries

    def _parse_education_paragraph(self, para: str) -> Optional[EducationEntry]:
        """解析单个教育段落 — P0-5 新增

        支持格式：
        - "2024.09-至今 浙江大学 环境科学（硕士）"
        - "2020.09-2024.07 北京科技大学（3.6/4.0） 环境工程（本科）"
        - "2022.08-2023.01 华南理工大学（4.0/4.0） 环境工程（交流）"
        """
        entry = EducationEntry()
        text = para.strip()

        # 1. 提取学校
        school_patterns = [
            # 中文校名（2-15 个汉字 + 大学/学院/学校）
            r'([\u4e00-\u9fa5]{2,15}(?:大学|学院|学校))',
            # 英文校名（University / College / Institute / School）
            r'((?:[A-Z][a-z]+\s+){0,3}(?:University|College|Institute|School))',
        ]
        for pattern in school_patterns:
            m = re.search(pattern, text)
            if m:
                entry.school = m.group(1).strip()
                break

        if not entry.school:
            return None  # 必须有学校才能算教育条目

        # 2. 提取学历
        degree_map = [
            ('博士', ['博士', 'PhD', 'Ph.D', 'Doctor']),
            ('硕士', ['硕士', 'Master', 'MBA', 'EMBA', '研究生']),
            ('本科', ['本科', '学士', 'Bachelor', 'Undergraduate']),
            ('专科', ['专科', '大专', 'Associate']),
        ]
        for degree_name, keywords in degree_map:
            if any(kw in text for kw in keywords):
                entry.degree = degree_name
                break

        # 3. 提取专业（从括号内 / "专业"后 / 紧跟学校后）
        field_patterns = [
            # 优先级 1: 括号内含 field 类型字符
            r'[\(（]([\u4e00-\u9fa5]{2,15}(?:学|工程|技术|科学|管理|艺术))[\)）]',
            # 优先级 2: "专业：xxx" / "Major: xxx"
            r'(?:专业|Major)[:：\s]*([\u4e00-\u9fa5]{2,15})',
        ]
        for pattern in field_patterns:
            m = re.search(pattern, text)
            if m:
                field = m.group(1).strip()
                if field and field not in ['专业', 'Major']:
                    entry.field_of_study = field
                    break

        # 优先级 3: 紧跟学校后的专业 — 先去掉学校名再匹配，避免 "江大学" 误识别
        if not entry.field_of_study:
            text_no_school = text.replace(entry.school, ' ', 1)
            m = re.search(
                r'[\s,，][\u4e00-\u9fa5]{2,10}(?:学|工程|技术|科学|管理)(?=[\s,，()（）]|$)',
                text_no_school,
            )
            if m:
                field = m.group(0).strip().lstrip(',，\s')
                if field and field not in ['专业', 'Major', entry.school]:
                    entry.field_of_study = field

        # 4. 提取时间范围（规范化 YYYY-MM）
        start_date, end_date = extract_date_range(text)
        entry.start_date = _normalize_local_date(start_date)
        entry.end_date = _normalize_local_date(end_date)

        # 5. GPA
        gpa_match = re.search(r'GPA[:\s]*([\d\.]+)', text, re.IGNORECASE)
        if gpa_match:
            entry.gpa = gpa_match.group(1)

        # 设置置信度
        entry.confidence = 0.85
        return entry

    def _extract_education_legacy(self, section: Section) -> List[EducationEntry]:
        """旧版教育提取（已废弃，保留仅为向后兼容）"""
        return self._extract_education(section)

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
        """提取项目经历 - 支持独立章节和嵌套在工作经历中的项目"""
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
            
            # 提取技术栈
            entry.tech_stack = self._extract_tech_stack(para)
            entry.technologies = entry.tech_stack
            
            # 提取贡献点（bullet points）
            entry.contributions = self._extract_contributions(para)
            
            if entry.name:
                entry.confidence = 0.75
                entries.append(entry)
        
        return entries
    
    def _extract_nested_projects_from_work(self, work_entries: List[WorkEntry]) -> List[ProjectEntry]:
        """从工作经历描述中提取嵌套的项目经历"""
        projects = []
        
        for work in work_entries:
            if not work.description:
                continue
                
            # 项目指示器模式
            project_indicators = [
                r'(?:项目|课题)[：:\s]*([^\n]{2,50})',
                r'(?:负责|主导|参与)[^\n]{0,20}(?:项目)[：:\s]*([^\n]{2,50})',
                r'《([^》]{2,50})》',
                r'"([^"]{2,50})"',
            ]
            
            for pattern in project_indicators:
                matches = re.finditer(pattern, work.description, re.IGNORECASE)
                for match in matches:
                    project_name = match.group(1).strip()
                    if len(project_name) < 5 or len(project_name) > 50:
                        continue
                    
                    # 提取项目描述（从项目名到下一个项目名或段落结束）
                    start_pos = match.end()
                    next_match = re.search(r'(?:项目|课题)[：:\s]*', work.description[start_pos:])
                    if next_match:
                        project_desc = work.description[start_pos:start_pos + next_match.start()].strip()
                    else:
                        project_desc = work.description[start_pos:].strip()
                    
                    project = ProjectEntry(
                        name=project_name,
                        role=work.title,
                        start_date=work.start_date,
                        end_date=work.end_date,
                        description=project_desc,
                        tech_stack=self._extract_tech_stack(project_desc),
                        technologies=self._extract_tech_stack(project_desc),
                        contributions=self._extract_contributions(project_desc),
                        confidence=0.7
                    )
                    projects.append(project)
        
        return projects
    
    def _extract_tech_stack(self, text: str) -> List[str]:
        """从文本中提取技术栈"""
        tech_stack = []
        
        # 技术栈指示器模式
        tech_patterns = [
            r'(?:技术栈|技术|工具|Tech Stack)[：:\s]*([^\n]+)',
            r'(?:使用|采用|基于)[^\n]{0,10}(?:技术|工具|框架)[：:\s]*([^\n]+)',
        ]
        
        for pattern in tech_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                tech_text = match.group(1)
                # 分割技术项
                tech_items = re.split(r'[、,，;/\|\\\s]+', tech_text)
                for item in tech_items:
                    item = item.strip()
                    if item and len(item) < 30:
                        tech_stack.append(item)
        
        return tech_stack
    
    def _extract_contributions(self, text: str) -> List[str]:
        """从文本中提取贡献点（bullet points）"""
        contributions = []
        
        # 查找列表项
        bullet_patterns = [
            r'[•\-\*・]\s*([^\n]+)',
            r'\d+[\.、]\s*([^\n]+)',
        ]
        
        for pattern in bullet_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                contribution = match.group(1).strip()
                if contribution and len(contribution) > 5:
                    contributions.append(contribution)
        
        # 如果没有列表项，尝试按句子分割
        if not contributions:
            sentences = re.split(r'[。；;]', text)
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and len(sentence) > 10 and len(sentence) < 200:
                    # 排除纯描述性句子
                    if re.search(r'(负责|完成|实现|开发|设计|优化|提升|降低|增加|减少)', sentence):
                        contributions.append(sentence)
        
        return contributions
    
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
        # 阈值从3提高到8，因为现代简历通常包含大量技能
        skill_density = len(skills) / max(len(text) / 100, 1)  # 每100字符的技能数
        if len(skills) < 8 or skill_density < 0.05:
            full_text_skills = self._extract_skills_from_full_text(text)
            for skill in full_text_skills:
                skill_key = skill.name.lower()
                if skill_key not in found_skills:
                    found_skills[skill_key] = True
                    skills.append(skill)
        
        return skills
    
    def _extract_combo_skills(self, text: str) -> List[str]:
        """提取组合格式的技能（如"PS/PR"、"AI/AE"、"Python/R"）"""
        skills = []
        
        # 查找类似 "PS/PR"、"AI/AE"、"Python/R" 的模式
        # 支持中文标点、空格、换行前后的组合
        # 匹配规则：技能名(1-20字符) + /或、或| + 技能名(1-20字符)
        combo_pattern = r'(?:^|[\s\、\,\，\;\；\|\/\·\n\r\t])([A-Za-z\+\#]{1,20}|[\u4e00-\u9fa5]{2,10})[\/\|\、]([A-Za-z\+\#]{1,20}|[\u4e00-\u9fa5]{2,10})(?:$|[\s\、\,\，\;\；\|\/\·\n\r\t])'
        matches = re.finditer(combo_pattern, text)
        
        for match in matches:
            part1 = match.group(1).strip()
            part2 = match.group(2).strip()
            
            # 尝试标准化每个部分
            for part in [part1, part2]:
                if not part:
                    continue
                normalized = self._normalize_skill_name(part)
                # 如果标准化成功，或者该缩写是已知的设计软件缩写
                known_abbrevs = ['PS', 'PR', 'AI', 'AE', 'LR', 'AU', 'CAD', 'ID', 'XD', 'UI', 'UX', '3D', 'C4D', 'R', 'C', 'C++', 'C#', 'Go', 'SQL', 'NoSQL']
                if normalized != part or part.upper() in known_abbrevs:
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

    # ==================== v2 扩展（对标字节跳动 13 段）====================
    def extract_v2(self, document: ParsedDocument, structure: DocumentStructure) -> Dict[str, Any]:
        """v2 提取入口 — 调用新增的 v2_extractors 集合"""
        from .extractors.v2_extractors import (
            extract_competitions, extract_portfolios, extract_social_accounts,
            extract_self_evaluation, extract_source_of_info, extract_languages_enhanced,
        )
        text = document.full_text or ""
        existing_languages = self.extract(document, structure).get("languages", [])

        # 把 dataclass 还原为 Language
        from .models import Language
        lang_objs = []
        for l in existing_languages:
            if isinstance(l, Language):
                lang_objs.append(l)
            elif isinstance(l, dict):
                lang_objs.append(Language(**{k: v for k, v in l.items() if k in Language().__dict__}))

        return {
            "competitions": [c.to_dict() for c in extract_competitions(text)],
            "portfolios": [p.to_dict() for p in extract_portfolios(text)],
            "social_accounts": [a.to_dict() for a in extract_social_accounts(text)],
            "self_evaluation": extract_self_evaluation(text).to_dict(),
            "source": extract_source_of_info(text).to_dict(),
            "languages_enhanced": [l.to_dict() if hasattr(l, 'to_dict') else l.__dict__ for l in extract_languages_enhanced(text, lang_objs)],
        }


# 单例模式
_rule_engine = None

def get_rule_engine() -> RuleEngine:
    """获取规则引擎单例"""
    global _rule_engine
    if _rule_engine is None:
        _rule_engine = RuleEngine()
    return _rule_engine
