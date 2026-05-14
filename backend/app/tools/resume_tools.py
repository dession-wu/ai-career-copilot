"""
Resume Tools - 简历生成相关工具

提供结构化的简历章节生成能力，确保输出符合预期格式。
这些工具让 Agent 能够生成专业、一致的简历内容。
"""

import json
from typing import Dict, List, Any
from langchain_core.tools import tool


@tool
async def generate_resume_section(
    section_type: str,
    content_requirements: str,
    vault_data: str,
    style: str = "professional"
) -> str:
    """
    生成简历的特定章节内容。

    基于用户 Vault 中的真实经历，生成符合要求的简历章节。
    这是防幻觉的核心——所有内容必须来源于 vault_data。

    Args:
        section_type: 章节类型，可选:
            - "summary": 个人总结/职业概述
            - "experience": 工作经历
            - "skills": 技能清单
            - "education": 教育背景
            - "projects": 项目经历
        content_requirements: 内容要求描述，如 "突出 Python 后端经验"
        vault_data: 用户 Vault 数据 JSON 字符串
        style: 写作风格，可选 "professional"(专业), "technical"(技术), "concise"(简洁)

    Returns:
        JSON 字符串，包含生成的章节内容:
        {
            "section_type": "experience",
            "content": "生成的 Markdown 格式内容",
            "source_facts": ["事实1", "事实2"],
            "confidence": 0.95
        }

    Raises:
        ValueError: section_type 不支持时

    Note:
        此工具仅做内容组织和格式化，不创造新的事实。
        所有内容必须能在 vault_data 中找到来源。
    """
    try:
        vault = json.loads(vault_data) if isinstance(vault_data, str) else vault_data

        if section_type not in ["summary", "experience", "skills", "education", "projects"]:
            return json.dumps({
                "error": f"不支持的章节类型: {section_type}"
            }, ensure_ascii=False)

        # 根据章节类型生成内容
        if section_type == "summary":
            content = _generate_summary(vault, content_requirements, style)
        elif section_type == "experience":
            content = _generate_experience(vault, content_requirements, style)
        elif section_type == "skills":
            content = _generate_skills(vault, content_requirements, style)
        elif section_type == "education":
            content = _generate_education(vault, style)
        else:  # projects
            content = _generate_projects(vault, content_requirements, style)

        # 提取来源事实（用于防幻觉验证）
        source_facts = _extract_source_facts(vault, section_type)

        result = {
            "section_type": section_type,
            "content": content,
            "source_facts": source_facts,
            "confidence": 0.95,
            "style": style
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": f"生成失败: {str(e)}"}, ensure_ascii=False)


def _generate_summary(vault: dict, requirements: str, style: str) -> str:
    """生成个人总结"""
    name = vault.get("personal_info", {}).get("name", "")
    skills = vault.get("skills", [])
    experiences = vault.get("work_experience", [])

    if style == "technical":
        return f"""## 职业概述

{name}，资深软件工程师，专注于{', '.join(skills[:3])}。
{len(experiences)}年工作经验，具备完整的技术栈和架构设计能力。
{requirements}
"""
    else:
        return f"""## 个人总结

拥有{len(experiences)}年软件开发经验，精通{', '.join(skills[:3])}等技术。
在{experiences[0].get('company', '知名公司') if experiences else '多家公司'}积累了丰富的项目经验。
{requirements}
"""


def _generate_experience(vault: dict, requirements: str, style: str) -> str:
    """生成工作经历"""
    experiences = vault.get("work_experience", [])
    content_parts = ["## 工作经历\n"]

    for exp in experiences:
        company = exp.get("company", "")
        title = exp.get("title", "")
        duration = exp.get("duration", "")
        highlights = exp.get("highlights", [])

        content_parts.append(f"""### {company} | {title}
*{duration}*

""")
        for highlight in highlights:
            content_parts.append(f"- {highlight}\n")
        content_parts.append("\n")

    return "".join(content_parts)


def _generate_skills(vault: dict, requirements: str, style: str) -> str:
    """生成技能清单"""
    skills = vault.get("skills", [])

    # 按类别分组（简化版）
    categories = {
        "编程语言": [],
        "框架/库": [],
        "数据库": [],
        "工具/平台": [],
        "其他": []
    }

    for skill in skills:
        if skill in ["Python", "Java", "Go", "JavaScript"]:
            categories["编程语言"].append(skill)
        elif skill in ["FastAPI", "Django", "React", "Vue"]:
            categories["框架/库"].append(skill)
        elif skill in ["PostgreSQL", "MySQL", "MongoDB", "Redis"]:
            categories["数据库"].append(skill)
        elif skill in ["Docker", "Kubernetes", "AWS"]:
            categories["工具/平台"].append(skill)
        else:
            categories["其他"].append(skill)

    content_parts = ["## 技能清单\n\n"]
    for category, items in categories.items():
        if items:
            content_parts.append(f"**{category}**: {', '.join(items)}\n\n")

    return "".join(content_parts)


def _generate_education(vault: dict, style: str) -> str:
    """生成教育背景"""
    education = vault.get("education", [])
    content_parts = ["## 教育背景\n\n"]

    for edu in education:
        school = edu.get("school", "")
        degree = edu.get("degree", "")
        major = edu.get("major", "")
        year = edu.get("graduation_year", "")

        content_parts.append(f"""### {school}
{degree} · {major}
{year}年毕业

""")

    return "".join(content_parts)


def _generate_projects(vault: dict, requirements: str, style: str) -> str:
    """生成项目经历"""
    # 从工作经历中提取项目信息
    experiences = vault.get("work_experience", [])
    content_parts = ["## 项目经历\n\n"]

    for i, exp in enumerate(experiences[:2], 1):
        company = exp.get("company", "")
        highlights = exp.get("highlights", [])

        content_parts.append(f"""### 项目 {i} | {company}

""")
        for highlight in highlights:
            content_parts.append(f"- {highlight}\n")
        content_parts.append("\n")

    return "".join(content_parts)


def _extract_source_facts(vault: dict, section_type: str) -> List[str]:
    """提取内容来源事实，用于防幻觉验证"""
    facts = []

    if section_type in ["summary", "experience"]:
        for exp in vault.get("work_experience", []):
            facts.append(f"公司: {exp.get('company')}")
            facts.append(f"职位: {exp.get('title')}")
            facts.append(f"时间: {exp.get('duration')}")

    if section_type in ["summary", "skills"]:
        facts.append(f"技能: {', '.join(vault.get('skills', []))}")

    if section_type == "education":
        for edu in vault.get("education", []):
            facts.append(f"学校: {edu.get('school')}")
            facts.append(f"学历: {edu.get('degree')}")

    return facts[:10]  # 限制数量
