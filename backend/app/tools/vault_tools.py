"""
Vault Tools - 经历总库相关工具

提供简历解析、Vault 数据查询等功能。
这些工具让 Agent 能够访问用户的 Career Vault 数据。
"""

import json
from typing import Dict, List, Any
from langchain_core.tools import tool


@tool
async def parse_resume(file_path: str, file_type: str = "pdf") -> str:
    """
    解析简历文件，提取结构化信息。

    支持 PDF 和 DOCX 格式。返回 JSON 格式的结构化数据，
    包含个人信息、教育经历、工作经历、技能清单等。

    Args:
        file_path: 简历文件的本地路径或 URL
        file_type: 文件类型，可选 "pdf" 或 "docx"，默认 "pdf"

    Returns:
        JSON 字符串，包含解析后的结构化简历数据:
        {
            "personal_info": {"name": "", "email": "", "phone": ""},
            "education": [{"school": "", "degree": "", "major": ""}],
            "work_experience": [{"company": "", "title": "", "duration": ""}],
            "skills": ["skill1", "skill2"]
        }

    Raises:
        FileNotFoundError: 文件不存在时
        ValueError: 不支持的文件类型
    """
    # 实际实现会调用 vault_service 的解析逻辑
    # 这里提供模拟实现用于演示架构
    try:
        # 模拟解析结果
        result = {
            "personal_info": {
                "name": "张三",
                "email": "zhangsan@example.com",
                "phone": "138****8888"
            },
            "education": [
                {
                    "school": "某某大学",
                    "degree": "本科",
                    "major": "计算机科学",
                    "graduation_year": "2020"
                }
            ],
            "work_experience": [
                {
                    "company": "某某科技",
                    "title": "高级后端工程师",
                    "duration": "2020-07 至 2024-03",
                    "highlights": [
                        "负责微服务架构设计",
                        "优化系统性能，QPS 提升 300%"
                    ]
                }
            ],
            "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes"]
        }
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": f"解析失败: {str(e)}"}, ensure_ascii=False)


@tool
async def search_vault(query: str, vault_data: str, top_k: int = 3) -> str:
    """
    在用户的 Career Vault 中搜索相关经历。

    使用语义匹配，从 Vault 数据中找到与查询最相关的经历片段。
    这是防幻觉的关键工具——确保 Agent 只基于用户真实经历生成内容。

    Args:
        query: 搜索查询，如 "Python 后端开发经验"
        vault_data: 用户的 Vault 数据 JSON 字符串
        top_k: 返回最相关的 K 条结果，默认 3

    Returns:
        JSON 字符串，包含匹配的经历片段列表:
        [
            {
                "source": "work_experience",
                "relevance_score": 0.95,
                "content": "负责微服务架构设计...",
                "metadata": {"company": "某某科技", "title": "高级后端工程师"}
            }
        ]

    Note:
        此工具是防幻觉的核心保障。Agent 在生成简历前，
        必须先用此工具检索相关经历，确保内容基于事实。
    """
    try:
        vault = json.loads(vault_data) if isinstance(vault_data, str) else vault_data

        # 模拟语义搜索（实际实现会使用 Embedding + Vector Store）
        results = []

        # 搜索工作经历
        for exp in vault.get("work_experience", []):
            content = " ".join(exp.get("highlights", []))
            # 简单关键词匹配作为演示
            relevance = _calculate_relevance(query, content)
            if relevance > 0.3:
                results.append({
                    "source": "work_experience",
                    "relevance_score": round(relevance, 2),
                    "content": content,
                    "metadata": {
                        "company": exp.get("company"),
                        "title": exp.get("title"),
                        "duration": exp.get("duration")
                    }
                })

        # 搜索技能
        for skill in vault.get("skills", []):
            if skill.lower() in query.lower():
                results.append({
                    "source": "skills",
                    "relevance_score": 0.9,
                    "content": f"技能: {skill}",
                    "metadata": {"skill": skill}
                })

        # 按相关度排序
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return json.dumps(results[:top_k], ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": f"搜索失败: {str(e)}"}, ensure_ascii=False)


def _calculate_relevance(query: str, content: str) -> float:
    """计算查询与内容的相关度（简化版，实际使用 Embedding 相似度）"""
    query_words = set(query.lower().split())
    content_words = set(content.lower().split())

    if not query_words:
        return 0.0

    overlap = query_words & content_words
    return len(overlap) / len(query_words)
