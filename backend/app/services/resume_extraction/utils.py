"""
简历信息提取工具函数
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


def clean_text(text: str) -> str:
    """清理文本"""
    if not text:
        return ""
    # 移除多余空格
    text = re.sub(r'\s+', ' ', text)
    # 移除特殊字符
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', text)
    return text.strip()


def normalize_date(date_str: str) -> str:
    """标准化日期格式"""
    if not date_str:
        return ""
    
    date_str = date_str.strip()
    
    # 处理"至今"
    if date_str in ["至今", "Present", "现在", "Current"]:
        return "至今"
    
    # 提取年份
    year_match = re.search(r'(20\d{2})', date_str)
    if year_match:
        return year_match.group(1)
    
    return date_str


def extract_date_range(text: str) -> Tuple[str, str]:
    """提取日期范围"""
    # 模式1: 2020.09 - 2024.06
    pattern1 = r'(20\d{2})[\.\-/年](\d{1,2})?\s*[\-–~]\s*(20\d{2})?[\.\-/年]?(\d{1,2}|至今|Present)?'
    match = re.search(pattern1, text, re.IGNORECASE)
    if match:
        start_year = match.group(1)
        end_part = match.group(4) or match.group(3)
        if end_part:
            if end_part in ["至今", "Present"]:
                return start_year, "至今"
            elif re.match(r'20\d{2}', str(end_part)):
                return start_year, end_part
        return start_year, ""
    
    # 模式2: 2020 - 2024
    pattern2 = r'(20\d{2})\s*[\-–~]\s*(20\d{2}|至今|Present)'
    match = re.search(pattern2, text, re.IGNORECASE)
    if match:
        end = match.group(2)
        if end in ["至今", "Present"]:
            end = "至今"
        return match.group(1), end
    
    # 模式3: 2020年9月 - 2024年6月
    pattern3 = r'(20\d{2})年(?:\d{1,2}月)?\s*[\-–~]\s*(?:(20\d{2})年)?(?:至今)?'
    match = re.search(pattern3, text)
    if match:
        return match.group(1), match.group(2) or ""
    
    return "", ""


def is_chinese_name(name: str) -> bool:
    """判断是否为中文姓名"""
    if not name:
        return False
    # 2-4个汉字
    return bool(re.match(r'^[\u4e00-\u9fa5]{2,4}$', name.strip()))


def is_english_name(name: str) -> bool:
    """判断是否为英文姓名"""
    if not name:
        return False
    # 英文姓名格式
    return bool(re.match(r'^[A-Za-z]+(\s+[A-Za-z]+)*$', name.strip()))


def merge_similar_entries(entries: List[Dict], similarity_threshold: float = 0.8) -> List[Dict]:
    """合并相似的条目"""
    if not entries:
        return []
    
    merged = []
    for entry in entries:
        is_duplicate = False
        for existing in merged:
            if calculate_similarity(entry, existing) >= similarity_threshold:
                # 合并信息
                existing.update({k: v for k, v in entry.items() if v and not existing.get(k)})
                is_duplicate = True
                break
        if not is_duplicate:
            merged.append(entry.copy())
    
    return merged


def calculate_similarity(entry1: Dict, entry2: Dict) -> float:
    """计算两个条目的相似度"""
    # 基于关键字段计算相似度
    key_fields = ["school", "company", "name", "title"]
    
    similarities = []
    for field in key_fields:
        val1 = str(entry1.get(field, "")).lower()
        val2 = str(entry2.get(field, "")).lower()
        if val1 and val2:
            # 简单的字符串相似度
            if val1 == val2:
                similarities.append(1.0)
            elif val1 in val2 or val2 in val1:
                similarities.append(0.8)
    
    return sum(similarities) / len(similarities) if similarities else 0.0


def extract_email(text: str) -> Optional[str]:
    """提取邮箱 - 增强版本，支持特殊分隔符"""
    # 首先清理文本中的特殊分隔符
    cleaned_text = text.replace('丨', ' ').replace('|', ' ').replace('/', ' ')
    
    # 标准邮箱模式
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(pattern, cleaned_text)
    if match:
        return match.group(0)
    
    # 尝试更宽松的模式（处理被特殊字符包围的邮箱）
    # 例如："手机：138xxx丨邮箱：name@example.com丨地址：xxx"
    loose_pattern = r'[\s丨|/]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})[\s丨|/]*'
    match = re.search(loose_pattern, text)
    if match:
        return match.group(1)
    
    return None


def extract_phone(text: str) -> Optional[str]:
    """提取电话"""
    # 中国大陆手机号
    pattern = r'1[3-9]\d{9}'
    match = re.search(pattern, text)
    if match:
        return match.group(0)
    
    # 座机
    pattern = r'\d{3,4}-\d{7,8}'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_linkedin(text: str) -> Optional[str]:
    """提取LinkedIn链接"""
    pattern = r'(?:linkedin\.com/in/|linkedin\.com/profile\?id=)([a-zA-Z0-9\-_]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return f"https://linkedin.com/in/{match.group(1)}"
    return None


def extract_website(text: str) -> Optional[str]:
    """提取个人网站"""
    patterns = [
        r'(https?://[^\s\n]+(?:github\.io|vercel\.app|netlify\.app|gitee\.io)[^\s\n]*)',
        r'(https?://[^\s\n]+blog\.csdn\.net[^\s\n]*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def infer_skill_level(text: str, skill_name: str) -> str:
    """推断技能熟练度"""
    # 查找技能附近的文本
    pattern = r'[^。\n]*' + re.escape(skill_name) + r'[^。\n]*'
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    if not matches:
        return "熟练"
    
    context = ' '.join(matches).lower()
    
    # 熟练度关键词
    expert_keywords = ['精通', 'expert', 'master', '高级', 'advanced', '非常熟悉', '熟练掌握']
    proficient_keywords = ['熟练', 'proficient', '熟悉', 'familiar', '掌握', 'skilled', '中级', 'intermediate']
    beginner_keywords = ['了解', 'beginner', '入门', 'basic', '初级', '接触过', '知道']
    
    for keyword in expert_keywords:
        if keyword in context:
            return "精通"
    for keyword in beginner_keywords:
        if keyword in context:
            return "入门"
    for keyword in proficient_keywords:
        if keyword in context:
            return "熟练"
    
    return "熟练"


def split_into_paragraphs(text: str) -> List[str]:
    """将文本分割成段落"""
    # 按空行分割
    paragraphs = re.split(r'\n\s*\n', text)
    return [p.strip() for p in paragraphs if p.strip()]


def is_section_header(line: str) -> bool:
    """判断是否为章节标题"""
    line = line.strip()
    if not line:
        return False
    
    # 章节关键词
    section_keywords = [
        "教育", "工作", "项目", "技能", "证书", "语言", "奖项", "荣誉",
        "Education", "Experience", "Project", "Skill", "Certification",
        "Language", "Award", "Honor"
    ]
    
    # 检查是否包含章节关键词
    has_keyword = any(keyword in line for keyword in section_keywords)
    
    # 章节标题通常较短
    is_short = len(line) < 30
    
    # 可能包含分隔符
    has_separator = any(sep in line for sep in ["=", "-", "：", ":"])
    
    return has_keyword and (is_short or has_separator)


def normalize_company_name(name: str) -> str:
    """标准化公司名称"""
    if not name:
        return ""
    
    # 移除常见后缀
    suffixes = ["有限公司", "有限责任公司", "股份有限公司", "公司", "集团"]
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            break
    
    return name.strip()


def normalize_school_name(name: str) -> str:
    """标准化学校名称"""
    if not name:
        return ""
    
    # 移除常见后缀
    suffixes = ["大学", "学院", "学校"]
    for suffix in suffixes:
        if name.endswith(suffix):
            return name  # 保留完整名称
    
    return name.strip()


def calculate_text_similarity(text1: str, text2: str) -> float:
    """计算两段文本的相似度（基于共有词）"""
    if not text1 or not text2:
        return 0.0
    
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1 & words2
    union = words1 | words2
    
    return len(intersection) / len(union)


def format_duration(start_date: str, end_date: str) -> str:
    """格式化时长"""
    if not start_date:
        return ""
    
    if not end_date or end_date == "至今":
        return f"{start_date} - 至今"
    
    return f"{start_date} - {end_date}"


def is_valid_date(date_str: str) -> bool:
    """验证日期格式"""
    if not date_str:
        return False
    
    # 支持格式：2020, 2020.09, 2020-09, 2020/09, 2020年9月
    patterns = [
        r'^20\d{2}$',
        r'^20\d{2}[\.\-/年]\d{1,2}$',
    ]
    
    for pattern in patterns:
        if re.match(pattern, date_str):
            return True
    
    # 特殊值
    if date_str in ["至今", "Present"]:
        return True
    
    return False


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """截断文本"""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def remove_html_tags(text: str) -> str:
    """移除HTML标签"""
    return re.sub(r'<[^>]+>', '', text)


def normalize_whitespace(text: str) -> str:
    """标准化空白字符"""
    return re.sub(r'\s+', ' ', text).strip()
