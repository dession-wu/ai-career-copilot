"""
Vault Tools V2 - 对接真实 Vault Service

Phase 2 升级：
- 对接真实的 VaultService（不再是 mock）
- 支持异步数据库会话
- 添加错误恢复和降级策略
- 支持批量/并行操作
"""

import json
import logging
from typing import Dict, List, Any, Optional
from langchain_core.tools import tool
from sqlalchemy.orm import Session
from fastapi import Depends

# 导入真实服务
from ..services.vault_service import VaultService
from ..database import get_db

logger = logging.getLogger(__name__)


# ========== 依赖注入辅助函数 ==========

def get_vault_service(db: Session = Depends(get_db)) -> VaultService:
    """获取 VaultService 实例（用于 FastAPI 依赖注入）"""
    return VaultService(db)


# ========== Tool 定义 ==========

@tool
async def parse_resume_v2(
    file_path: str,
    file_type: str = "pdf",
    db_session: Optional[Session] = None
) -> str:
    """
    解析简历文件，提取结构化信息（V2 - 对接真实服务）。

    支持 PDF 和 DOCX 格式。使用 VaultService 的真实解析逻辑，
    包括文本提取、结构化数据抽取、技能识别等。

    Args:
        file_path: 简历文件的本地路径
        file_type: 文件类型，"pdf" 或 "docx"
        db_session: 可选的数据库会话（用于依赖注入）

    Returns:
        JSON 字符串，包含解析后的结构化简历数据

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 不支持的文件类型
    """
    try:
        logger.info(f"[Tool] parse_resume_v2: 开始解析 {file_path}")

        # 创建 VaultService 实例
        if db_session:
            vault_service = VaultService(db_session)
        else:
            # 无数据库会话时使用简化解析
            vault_service = VaultService(None)

        # 读取文件内容
        with open(file_path, "rb") as f:
            from fastapi import UploadFile
            from io import BytesIO

            file_content = f.read()
            upload_file = UploadFile(
                filename=f"resume.{file_type}",
                file=BytesIO(file_content)
            )

            # 调用真实解析服务
            raw_text = vault_service.parse_resume_file(upload_file)

        # 提取结构化数据
        structured_data = vault_service.extract_structured_data(raw_text)

        logger.info(f"[Tool] parse_resume_v2: 解析完成，提取到 {len(structured_data.get('skills', []))} 个技能")

        return json.dumps(structured_data, ensure_ascii=False, indent=2)

    except FileNotFoundError:
        logger.error(f"[Tool] parse_resume_v2: 文件不存在 {file_path}")
        return json.dumps({"error": f"文件不存在: {file_path}"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[Tool] parse_resume_v2: 解析失败: {str(e)}")
        # 降级策略：返回基本错误信息
        return json.dumps({
            "error": f"解析失败: {str(e)}",
            "fallback": "请检查文件格式或稍后重试"
        }, ensure_ascii=False)


@tool
async def search_vault_v2(
    query: str,
    vault_data: str,
    top_k: int = 5,
    search_type: str = "semantic"  # "semantic" 或 "keyword"
) -> str:
    """
    在 Career Vault 中语义搜索相关经历（V2 - 增强版）。

    支持两种搜索模式：
    - semantic: 语义搜索（需要 Embedding 模型，更智能）
    - keyword: 关键词搜索（无需额外依赖，更快速）

    Args:
        query: 搜索查询，如 "Python 后端开发经验"
        vault_data: 用户 Vault 数据 JSON 字符串
        top_k: 返回最相关的 K 条结果
        search_type: 搜索类型，"semantic" 或 "keyword"

    Returns:
        JSON 字符串，包含匹配的经历片段

    Note:
        此工具是防幻觉的核心保障。Agent 在生成简历前，
        必须先用此工具检索相关经历，确保内容基于事实。
    """
    try:
        logger.info(f"[Tool] search_vault_v2: 搜索 '{query}' (type={search_type})")

        vault = json.loads(vault_data) if isinstance(vault_data, str) else vault_data
        results = []

        if search_type == "semantic":
            # 语义搜索（Phase 3 将集成 Embedding）
            results = await _semantic_search(query, vault, top_k)
        else:
            # 关键词搜索（当前实现）
            results = await _keyword_search(query, vault, top_k)

        logger.info(f"[Tool] search_vault_v2: 找到 {len(results)} 条相关经历")

        return json.dumps({
            "query": query,
            "search_type": search_type,
            "results_count": len(results),
            "results": results
        }, ensure_ascii=False, indent=2)

    except json.JSONDecodeError:
        logger.error("[Tool] search_vault_v2: Vault 数据 JSON 解析失败")
        return json.dumps({
            "error": "Vault 数据格式错误",
            "query": query,
            "results": []
        }, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[Tool] search_vault_v2: 搜索失败: {str(e)}")
        # 降级：返回空结果
        return json.dumps({
            "error": f"搜索失败: {str(e)}",
            "query": query,
            "results": [],
            "fallback": "使用全部 Vault 数据作为上下文"
        }, ensure_ascii=False)


async def _semantic_search(query: str, vault: dict, top_k: int) -> List[dict]:
    """
    语义搜索（预留，Phase 3 集成 Embedding）

    将使用 Vector Store 进行语义相似度搜索。
    """
    # 当前降级为关键词搜索
    logger.info("[Tool] semantic_search: 降级为关键词搜索（Embedding 未配置）")
    return await _keyword_search(query, vault, top_k)


async def _keyword_search(query: str, vault: dict, top_k: int) -> List[dict]:
    """关键词搜索实现"""
    results = []
    query_keywords = set(query.lower().split())

    # 搜索工作经历
    for exp in vault.get("experiences", vault.get("work_experience", [])):
        content = " ".join([
            exp.get("company", ""),
            exp.get("title", ""),
            exp.get("description", ""),
            str(exp.get("highlights", ""))
        ]).lower()

        relevance = _calculate_keyword_relevance(query_keywords, content)
        if relevance > 0.1:
            results.append({
                "source": "work_experience",
                "relevance_score": round(relevance, 3),
                "content": exp.get("description", ""),
                "highlights": exp.get("highlights", []),
                "metadata": {
                    "company": exp.get("company"),
                    "title": exp.get("title"),
                    "duration": f"{exp.get('start_date', '')} - {exp.get('end_date', '')}"
                }
            })

    # 搜索技能
    for skill in vault.get("skills", []):
        skill_name = skill.get("name", skill) if isinstance(skill, dict) else skill
        if any(kw in str(skill_name).lower() for kw in query_keywords):
            results.append({
                "source": "skills",
                "relevance_score": 0.9,
                "content": f"技能: {skill_name}",
                "metadata": {
                    "skill": skill_name,
                    "level": skill.get("level", "熟练") if isinstance(skill, dict) else "熟练"
                }
            })

    # 搜索项目经历
    for proj in vault.get("projects", []):
        content = " ".join([
            proj.get("name", ""),
            proj.get("description", ""),
            proj.get("role", "")
        ]).lower()

        relevance = _calculate_keyword_relevance(query_keywords, content)
        if relevance > 0.1:
            results.append({
                "source": "projects",
                "relevance_score": round(relevance, 3),
                "content": proj.get("description", ""),
                "metadata": {
                    "project_name": proj.get("name"),
                    "role": proj.get("role")
                }
            })

    # 按相关度排序
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return results[:top_k]


def _calculate_keyword_relevance(query_keywords: set, content: str) -> float:
    """计算关键词相关度"""
    if not query_keywords:
        return 0.0

    content_words = set(content.lower().split())
    overlap = query_keywords & content_words

    # Jaccard 相似度
    union = query_keywords | content_words
    if not union:
        return 0.0

    return len(overlap) / len(union)


@tool
async def get_vault_summary(vault_data: str) -> str:
    """
    生成 Vault 数据的摘要概述。

    快速了解用户的整体背景，用于 Agent 制定策略。

    Args:
        vault_data: 用户 Vault 数据 JSON 字符串

    Returns:
        JSON 字符串，包含摘要信息
    """
    try:
        vault = json.loads(vault_data) if isinstance(vault_data, str) else vault_data

        # 统计信息
        total_experiences = len(vault.get("experiences", vault.get("work_experience", [])))
        total_skills = len(vault.get("skills", []))
        total_projects = len(vault.get("projects", []))
        total_education = len(vault.get("education", []))

        # 提取核心技能（按类别分组）
        skills_by_category = {}
        for skill in vault.get("skills", []):
            if isinstance(skill, dict):
                category = skill.get("category", "其他")
                name = skill.get("name", "")
            else:
                category = "其他"
                name = skill

            if category not in skills_by_category:
                skills_by_category[category] = []
            skills_by_category[category].append(name)

        # 计算总工作年限
        total_years = _calculate_total_years(vault)

        summary = {
            "profile_overview": {
                "name": vault.get("personal_info", {}).get("name", "未知"),
                "total_years_experience": total_years,
                "current_title": _get_current_title(vault)
            },
            "statistics": {
                "work_experiences": total_experiences,
                "skills": total_skills,
                "projects": total_projects,
                "education": total_education
            },
            "core_skills": skills_by_category,
            "strengths": _identify_strengths(vault),
            "gaps": []  # 由 Agent 分析填充
        }

        return json.dumps(summary, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"[Tool] get_vault_summary: 生成摘要失败: {str(e)}")
        return json.dumps({
            "error": f"生成摘要失败: {str(e)}",
            "fallback": "请提供 Vault 数据"
        }, ensure_ascii=False)


def _calculate_total_years(vault: dict) -> int:
    """计算总工作年限"""
    experiences = vault.get("experiences", vault.get("work_experience", []))
    total = 0

    for exp in experiences:
        start = exp.get("start_date", "")
        end = exp.get("end_date", "")

        # 简单年份提取
        import re
        start_year = re.search(r'(20\d{2})', str(start))
        end_year = re.search(r'(20\d{2})', str(end))

        if start_year:
            sy = int(start_year.group(1))
            ey = int(end_year.group(1)) if end_year else 2024
            total += max(0, ey - sy)

    return max(total, 0)


def _get_current_title(vault: dict) -> str:
    """获取当前职位"""
    experiences = vault.get("experiences", vault.get("work_experience", []))
    if experiences:
        latest = experiences[0]  # 假设第一个是最新的
        return latest.get("title", "")
    return ""


def _identify_strengths(vault: dict) -> List[str]:
    """识别用户优势"""
    strengths = []

    experiences = vault.get("experiences", vault.get("work_experience", []))
    if len(experiences) >= 3:
        strengths.append("丰富的工作经历")

    skills = vault.get("skills", [])
    if len(skills) >= 10:
        strengths.append("广泛的技术栈")

    # 检查是否有管理经验
    for exp in experiences:
        title = str(exp.get("title", "")).lower()
        if any(kw in title for kw in ["经理", "主管", "总监", "manager", "lead"]):
            strengths.append("管理经验")
            break

    return strengths[:5]
