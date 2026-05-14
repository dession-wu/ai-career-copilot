"""
Job Tools V2 - 对接真实 Scoring Service

Phase 2 升级：
- 对接 ResumeScoringEngine（真实评分引擎）
- 支持多维度评分（skills/experience/projects/education）
- 并行评分计算
- 错误恢复和降级
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from langchain_core.tools import tool
from sqlalchemy.orm import Session

# 导入真实服务
from ..services.scoring_service import ResumeScoringEngine
from ..schemas.scoring import MatchRequest, DimensionWeights

logger = logging.getLogger(__name__)


@tool
async def analyze_jd_v2(jd_text: str) -> str:
    """
    深度分析职位描述，提取结构化要求（V2 - 增强版）。

    不仅提取关键词，还分析：
    - 核心职责优先级
    - 技能熟练度要求（精通/熟悉/了解）
    - 隐性要求（团队协作、沟通能力等）
    - 公司技术栈推断

    Args:
        jd_text: 职位描述文本

    Returns:
        JSON 字符串，包含结构化分析结果
    """
    try:
        logger.info(f"[Tool] analyze_jd_v2: 分析 JD，长度 {len(jd_text)} 字符")

        # 使用 LLM 进行深度分析（简化版，实际可调用 LLM Service）
        analysis = {
            "basic_info": _extract_basic_info(jd_text),
            "required_skills": _extract_skills_with_level(jd_text),
            "responsibilities": _extract_responsibilities(jd_text),
            "implicit_requirements": _extract_implicit_requirements(jd_text),
            "company_tech_stack": _infer_tech_stack(jd_text),
            "priority_skills": _identify_priority_skills(jd_text)
        }

        logger.info(f"[Tool] analyze_jd_v2: 提取到 {len(analysis['required_skills'])} 个技能要求")

        return json.dumps(analysis, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"[Tool] analyze_jd_v2: 分析失败: {str(e)}")
        return json.dumps({
            "error": f"JD 分析失败: {str(e)}",
            "fallback": "使用基础关键词提取"
        }, ensure_ascii=False)


@tool
async def calculate_match_score_v2(
    vault_data: str,
    jd_text: str,
    weights: Optional[str] = None
) -> str:
    """
    多维度匹配度评分（V2 - 对接真实评分引擎）。

    使用 ResumeScoringEngine 进行专业评分：
    - skills: 技能匹配度（权重 35%）
    - experience: 经验匹配度（权重 35%）
    - projects: 项目匹配度（权重 20%）
    - education: 教育匹配度（权重 10%）

    Args:
        vault_data: 用户 Vault 数据 JSON 字符串
        jd_text: 职位描述文本
        weights: 可选的自定义权重 JSON 字符串

    Returns:
        JSON 字符串，包含详细评分结果
    """
    try:
        logger.info("[Tool] calculate_match_score_v2: 开始多维度评分")

        # 解析 Vault 数据
        vault = json.loads(vault_data) if isinstance(vault_data, str) else vault_data

        # 构建简历文本（用于评分引擎）
        resume_text = _build_resume_text(vault)

        # 解析自定义权重
        custom_weights = None
        if weights:
            w = json.loads(weights)
            custom_weights = DimensionWeights(
                skills=w.get("skills", 0.35),
                experience=w.get("experience", 0.35),
                projects=w.get("projects", 0.20),
                education=w.get("education", 0.10)
            )

        # 创建评分请求
        request = MatchRequest(
            resume_text=resume_text,
            jd_text=jd_text,
            weights=custom_weights
        )

        # 调用真实评分引擎
        scoring_engine = ResumeScoringEngine()
        result = scoring_engine.calculate_match(request)

        # 转换为 JSON 友好格式
        response = {
            "overall_score": result.overall_score,
            "level": _get_score_level(result.overall_score),
            "dimensions": {
                dim: {
                    "score": data.score,
                    "matched": data.matched,
                    "missing": data.missing,
                    "analysis": data.analysis,
                    "suggestions": data.suggestions
                }
                for dim, data in result.dimensions.items()
            },
            "weights_used": {
                "skills": result.weights_used.skills,
                "experience": result.weights_used.experience,
                "projects": result.weights_used.projects,
                "education": result.weights_used.education
            },
            "summary": result.summary,
            "top_strengths": result.top_strengths,
            "key_gaps": result.key_gaps,
            "action_items": result.action_items
        }

        logger.info(f"[Tool] calculate_match_score_v2: 评分完成，总分 {result.overall_score}")

        return json.dumps(response, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"[Tool] calculate_match_score_v2: 评分失败: {str(e)}")
        # 降级：返回基础评分
        return json.dumps({
            "error": f"评分失败: {str(e)}",
            "fallback": _calculate_fallback_score(vault_data, jd_text)
        }, ensure_ascii=False)


@tool
async def calculate_match_score_parallel(
    vault_data: str,
    jd_text: str
) -> str:
    """
    并行多维度评分（演示 asyncio.gather 用法）。

    同时计算所有维度的评分，提升性能。

    Args:
        vault_data: 用户 Vault 数据 JSON 字符串
        jd_text: 职位描述文本

    Returns:
        JSON 字符串，包含评分结果
    """
    try:
        logger.info("[Tool] calculate_match_score_parallel: 并行评分开始")

        vault = json.loads(vault_data) if isinstance(vault_data, str) else vault_data
        resume_text = _build_resume_text(vault)

        # 定义维度列表
        dimensions = ["skills", "experience", "projects", "education"]

        # 并行计算各维度评分
        tasks = [
            _score_dimension_async(dim, resume_text, jd_text)
            for dim in dimensions
        ]

        # 使用 asyncio.gather 并行执行
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        dimension_scores = {}
        for dim, result in zip(dimensions, results):
            if isinstance(result, Exception):
                logger.warning(f"[Tool] 维度 {dim} 评分失败: {result}")
                dimension_scores[dim] = {
                    "score": 50,
                    "error": str(result)
                }
            else:
                dimension_scores[dim] = result

        # 计算加权总分
        weights = {"skills": 0.35, "experience": 0.35, "projects": 0.20, "education": 0.10}
        overall = sum(
            dimension_scores[dim].get("score", 50) * weights[dim]
            for dim in dimensions
        )

        response = {
            "overall_score": int(overall),
            "dimensions": dimension_scores,
            "parallel": True,
            "completed_dimensions": sum(1 for r in results if not isinstance(r, Exception))
        }

        logger.info(f"[Tool] calculate_match_score_parallel: 并行评分完成，总分 {int(overall)}")

        return json.dumps(response, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"[Tool] calculate_match_score_parallel: 失败: {str(e)}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)


async def _score_dimension_async(
    dimension: str,
    resume_text: str,
    jd_text: str
) -> Dict[str, Any]:
    """异步评分单个维度"""
    # 模拟异步操作（实际可调用异步 LLM）
    await asyncio.sleep(0.01)  # 模拟 IO 等待

    scoring_engine = ResumeScoringEngine()
    result = scoring_engine._score_dimension(dimension, resume_text, jd_text)

    return {
        "score": result.score,
        "matched": result.matched,
        "missing": result.missing,
        "analysis": result.analysis,
        "suggestions": result.suggestions
    }


# ========== 辅助函数 ==========

def _build_resume_text(vault: dict) -> str:
    """从 Vault 数据构建简历文本"""
    parts = []

    # 个人信息
    personal = vault.get("personal_info", {})
    if personal:
        parts.append(f"姓名: {personal.get('name', '')}")

    # 技能
    skills = vault.get("skills", [])
    if skills:
        skill_names = [s.get("name", s) if isinstance(s, dict) else s for s in skills]
        parts.append(f"技能: {', '.join(skill_names)}")

    # 工作经历
    experiences = vault.get("experiences", vault.get("work_experience", []))
    for exp in experiences:
        parts.append(f"\n公司: {exp.get('company', '')}")
        parts.append(f"职位: {exp.get('title', '')}")
        parts.append(f"时间: {exp.get('start_date', '')} - {exp.get('end_date', '')}")
        if exp.get("description"):
            parts.append(f"描述: {exp['description']}")
        if exp.get("highlights"):
            parts.append(f"亮点: {', '.join(exp['highlights'])}")

    # 教育
    education = vault.get("education", [])
    for edu in education:
        parts.append(f"\n学校: {edu.get('school', '')}")
        parts.append(f"学历: {edu.get('degree', '')}")
        parts.append(f"专业: {edu.get('field', edu.get('major', ''))}")

    return "\n".join(parts)


def _get_score_level(score: int) -> str:
    """获取评分等级"""
    if score >= 85:
        return "非常匹配"
    elif score >= 70:
        return "良好匹配"
    elif score >= 55:
        return "部分匹配"
    else:
        return "匹配度较低"


def _calculate_fallback_score(vault_data: str, jd_text: str) -> Dict[str, Any]:
    """评分失败时的降级方案"""
    return {
        "overall_score": 50,
        "level": "无法评估",
        "note": "评分服务暂时不可用，请稍后重试",
        "suggestions": ["检查 LLM 配置", "稍后重试"]
    }


def _extract_basic_info(jd_text: str) -> Dict[str, Any]:
    """提取基本信息"""
    import re

    info = {
        "title": "",
        "department": "",
        "location": "",
        "salary_range": ""
    }

    # 提取职位名称（通常在前几行）
    lines = jd_text.strip().split('\n')[:5]
    for line in lines:
        line = line.strip()
        if line and len(line) < 50 and not line.startswith('-'):
            info["title"] = line
            break

    # 提取地点
    location_match = re.search(r'(北京|上海|广州|深圳|杭州|成都|武汉|西安|南京|苏州)', jd_text)
    if location_match:
        info["location"] = location_match.group(1)

    return info


def _extract_skills_with_level(jd_text: str) -> List[Dict[str, str]]:
    """提取带熟练度要求的技能"""
    import re

    skills = []
    skill_patterns = [
        r'(精通|熟悉|掌握|了解)\s*([A-Za-z+#]+|[\u4e00-\u9fa5]+)',
        r'([A-Za-z+#]+|[\u4e00-\u9fa5]+)\s*(精通|熟悉|掌握|了解)'
    ]

    for pattern in skill_patterns:
        matches = re.finditer(pattern, jd_text)
        for match in matches:
            groups = match.groups()
            if len(groups) == 2:
                level = groups[0] if groups[0] in ['精通', '熟悉', '掌握', '了解'] else groups[1]
                skill = groups[1] if groups[0] in ['精通', '熟悉', '掌握', '了解'] else groups[0]
                skills.append({
                    "skill": skill,
                    "required_level": level,
                    "priority": "high" if level == "精通" else "medium"
                })

    return skills[:20]


def _extract_responsibilities(jd_text: str) -> List[str]:
    """提取职责要求"""
    import re

    responsibilities = []
    # 匹配以动词开头的句子
    patterns = [
        r'(?:负责|参与|承担|主导|协助|配合|完成|进行|开展)([^。；\n]+)',
        r'(?:设计|开发|维护|优化|管理|支持|解决|分析|测试|部署)([^。；\n]+)'
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, jd_text)
        for match in matches:
            resp = match.group(0).strip()
            if len(resp) > 5 and len(resp) < 100:
                responsibilities.append(resp)

    return responsibilities[:10]


def _extract_implicit_requirements(jd_text: str) -> List[str]:
    """提取隐性要求"""
    implicit = []

    keywords = {
        "团队协作": ["团队", "协作", "合作", "沟通"],
        "抗压能力": ["抗压", "压力", "高强度", "快节奏"],
        "学习能力": ["学习", "新技术", "快速上手"],
        "英语能力": ["英语", "英文", "CET", "雅思", "托福"],
        "ownership": ["owner", "ownership", "主人翁", "责任心"]
    }

    for requirement, keywords_list in keywords.items():
        if any(kw in jd_text for kw in keywords_list):
            implicit.append(requirement)

    return implicit


def _infer_tech_stack(jd_text: str) -> List[str]:
    """推断公司技术栈"""
    tech_indicators = {
        "微服务": ["微服务", "Microservices", "Service Mesh"],
        "云原生": ["Kubernetes", "Docker", "云原生", "Cloud Native"],
        "大数据": ["Hadoop", "Spark", "Flink", "Kafka", "大数据"],
        "AI/ML": ["机器学习", "深度学习", "TensorFlow", "PyTorch", "模型"]
    }

    stack = []
    for tech, indicators in tech_indicators.items():
        if any(ind in jd_text for ind in indicators):
            stack.append(tech)

    return stack


def _identify_priority_skills(jd_text: str) -> List[str]:
    """识别优先技能（必须掌握的）"""
    import re

    # 查找"必须"、"必备"、"必需"等关键词附近的技能
    priority_patterns = [
        r'(?:必须|必备|必需|硬性要求|硬性条件).*?([A-Za-z+#]+|[\u4e00-\u9fa5]+)',
        r'([A-Za-z+#]+|[\u4e00-\u9fa5]+).*?(?:必须|必备|必需)'
    ]

    priorities = []
    for pattern in priority_patterns:
        matches = re.finditer(pattern, jd_text)
        for match in matches:
            skill = match.group(1) if match.groups() else match.group(0)
            skill = re.sub(r'(?:必须|必备|必需|要求)', '', skill).strip()
            if skill and len(skill) < 30:
                priorities.append(skill)

    return priorities[:10]
