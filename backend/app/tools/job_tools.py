"""
Job Tools - 职位分析相关工具

提供 JD 关键词提取、匹配度计算、招聘市场搜索等功能。
让 Agent 能够深入理解职位要求并评估匹配度。
"""

import json
import re
from typing import Dict, List, Any
from langchain_core.tools import tool


@tool
async def extract_jd_keywords(jd_text: str) -> str:
    """
    从职位描述(JD)中提取核心技能要求和关键信息。

    分析 JD 文本，提取：
    - 必需技能（hard skills）
    - 加分技能（nice-to-have）
    - 经验年限要求
    - 学历要求
    - 核心职责

    Args:
        jd_text: 职位描述文本，可以是完整 JD 或片段

    Returns:
        JSON 字符串，包含结构化分析结果:
        {
            "required_skills": ["Python", "FastAPI"],
            "nice_to_have": ["Kubernetes", "React"],
            "experience_years": "3-5年",
            "education": "本科及以上",
            "key_responsibilities": ["负责后端架构", "优化性能"],
            "company_culture": ["技术驱动", "扁平管理"]
        }

    Example:
        jd = "要求：3年以上 Python 开发经验，熟悉 FastAPI 框架..."
        result = await extract_jd_keywords(jd)
    """
    try:
        # 使用规则 + LLM 混合提取（这里先用规则演示）
        result = {
            "required_skills": [],
            "nice_to_have": [],
            "experience_years": None,
            "education": None,
            "key_responsibilities": [],
            "company_culture": []
        }

        # 提取技能关键词（常见技术栈）
        skill_patterns = [
            r"Python", r"Java", r"Go", r"Rust", r"C\+\+",
            r"FastAPI", r"Django", r"Flask", r"Spring",
            r"React", r"Vue", r"Angular",
            r"PostgreSQL", r"MySQL", r"MongoDB", r"Redis",
            r"Docker", r"Kubernetes", r"AWS", r"Azure",
            r"机器学习", r"深度学习", r"NLP", r"CV"
        ]

        for pattern in skill_patterns:
            if re.search(pattern, jd_text, re.IGNORECASE):
                result["required_skills"].append(pattern)

        # 提取经验年限
        exp_match = re.search(r'(\d+)[\+\-]?(\d*)\s*年.*经验', jd_text)
        if exp_match:
            if exp_match.group(2):
                result["experience_years"] = f"{exp_match.group(1)}-{exp_match.group(2)}年"
            else:
                result["experience_years"] = f"{exp_match.group(1)}年以上"

        # 提取学历要求
        edu_patterns = [r'本科', r'硕士', r'博士', r'大专']
        for pattern in edu_patterns:
            if pattern in jd_text:
                result["education"] = pattern + "及以上"
                break

        # 提取职责（以动词开头的句子）
        responsibility_patterns = re.findall(r'[负负主主参参协协].*?[。；\n]', jd_text)
        result["key_responsibilities"] = [r.strip() for r in responsibility_patterns[:5]]

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": f"提取失败: {str(e)}"}, ensure_ascii=False)


@tool
async def calculate_match_score(vault_data: str, jd_requirements: str) -> str:
    """
    计算用户 Vault 与职位要求的匹配度评分。

    对比分析：
    - 技能匹配度（硬技能覆盖比例）
    - 经验匹配度（年限、领域相关性）
    - 教育匹配度
    - 综合评分

    Args:
        vault_data: 用户 Vault 数据 JSON 字符串
        jd_requirements: JD 分析结果 JSON 字符串（来自 extract_jd_keywords）

    Returns:
        JSON 字符串，包含详细评分:
        {
            "overall_score": 78,
            "skill_match": {
                "score": 85,
                "matched": ["Python", "FastAPI"],
                "missing": ["Kubernetes"],
                "extra": ["Django"]
            },
            "experience_match": {
                "score": 70,
                "user_years": 4,
                "required_years": "3-5年",
                "assessment": "符合"
            },
            "education_match": {"score": 100, "assessment": "符合"},
            "recommendations": ["建议补充 Kubernetes 经验"]
        }
    """
    try:
        vault = json.loads(vault_data) if isinstance(vault_data, str) else vault_data
        jd = json.loads(jd_requirements) if isinstance(jd_requirements, str) else jd_requirements

        # 技能匹配
        user_skills = set(s.lower() for s in vault.get("skills", []))
        required_skills = set(s.lower() for s in jd.get("required_skills", []))

        matched_skills = user_skills & required_skills
        missing_skills = required_skills - user_skills
        extra_skills = user_skills - required_skills

        skill_score = int((len(matched_skills) / len(required_skills) * 100)) if required_skills else 100

        # 经验匹配（简化计算）
        exp_score = 70  # 默认中等匹配
        user_exp_years = _estimate_experience_years(vault)
        required_exp = jd.get("experience_years", "")

        if "3-5" in required_exp and 3 <= user_exp_years <= 5:
            exp_score = 95
        elif "3年以上" in required_exp and user_exp_years >= 3:
            exp_score = 90

        # 综合评分
        overall = int((skill_score * 0.5) + (exp_score * 0.3) + (100 * 0.2))

        result = {
            "overall_score": min(overall, 100),
            "skill_match": {
                "score": skill_score,
                "matched": list(matched_skills),
                "missing": list(missing_skills),
                "extra": list(extra_skills)
            },
            "experience_match": {
                "score": exp_score,
                "user_years": user_exp_years,
                "required_years": required_exp,
                "assessment": "符合" if exp_score >= 70 else "需关注"
            },
            "education_match": {
                "score": 100,
                "assessment": "符合"
            },
            "recommendations": [
                f"建议补充: {', '.join(missing_skills)}" if missing_skills else "技能匹配良好"
            ]
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": f"评分失败: {str(e)}"}, ensure_ascii=False)


@tool
async def search_job_market(skill: str, location: str = "") -> str:
    """
    搜索特定技能在招聘市场的需求和薪资水平。

    获取市场数据帮助用户了解技能价值和趋势。
    数据来自招聘平台 API（实际实现需对接第三方服务）。

    Args:
        skill: 要搜索的技能名称，如 "Python", "React"
        location: 可选的地点筛选，如 "北京", "上海", "深圳"

    Returns:
        JSON 字符串，包含市场分析:
        {
            "skill": "Python",
            "location": "北京",
            "demand_level": "高",
            "avg_salary_range": "25k-45k",
            "job_count": 1250,
            "trend": "上升",
            "related_skills": ["FastAPI", "Django", "数据分析"]
        }

    Note:
        当前为模拟数据。生产环境需对接真实招聘 API
        （如 Boss 直聘、拉勾、猎聘等）。
    """
    # 模拟市场数据
    market_data = {
        "Python": {"demand": "高", "salary": "25k-45k", "trend": "稳定"},
        "React": {"demand": "高", "salary": "20k-40k", "trend": "上升"},
        "Kubernetes": {"demand": "中高", "salary": "30k-50k", "trend": "上升"},
        "FastAPI": {"demand": "中", "salary": "25k-40k", "trend": "上升"},
    }

    data = market_data.get(skill, {"demand": "中", "salary": "15k-30k", "trend": "稳定"})

    result = {
        "skill": skill,
        "location": location or "全国",
        "demand_level": data["demand"],
        "avg_salary_range": data["salary"],
        "job_count": 1000,  # 模拟数据
        "trend": data["trend"],
        "related_skills": [f"{skill}相关技能1", f"{skill}相关技能2"],
        "note": "当前为模拟数据，生产环境将对接真实招聘 API"
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


def _estimate_experience_years(vault: dict) -> int:
    """根据 Vault 工作经历估算总工作年限"""
    experiences = vault.get("work_experience", [])
    total_years = 0

    for exp in experiences:
        duration = exp.get("duration", "")
        # 简单解析 "2020-07 至 2024-03" 格式
        years_match = re.findall(r'(\d{4})', duration)
        if len(years_match) >= 2:
            start_year = int(years_match[0])
            end_year = int(years_match[1])
            total_years += end_year - start_year

    return max(total_years, 1)  # 至少1年
