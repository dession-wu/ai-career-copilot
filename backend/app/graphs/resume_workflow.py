"""
Resume Workflow - 简历定制显式状态机

使用 LangGraph StateGraph 实现可控的简历定制流程：

    START → analyze_jd → search_vault → calculate_match → generate_resume → verify_facts → END
               │              │               │                  │              │
               └──────────────┴───────────────┴──────────────────┴──────────────┘
                                      (错误时重试或降级)

相比黑盒 ReAct 的优势：
1. 每个步骤都可观测（可在 LangSmith 中查看）
2. 可精确控制执行顺序和条件分支
3. 错误处理更精细（节点级别重试）
4. 易于扩展新步骤
"""

import json
import logging
from typing import Dict, List, Any, TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage, HumanMessage

# 导入 V2 工具
from ..tools.vault_tools_v2 import search_vault_v2, get_vault_summary
from ..tools.job_tools_v2 import analyze_jd_v2, calculate_match_score_v2
from ..tools.resume_tools import generate_resume_section
from ..tools.verification_tools import verify_facts

logger = logging.getLogger(__name__)


# ========== 状态定义 ==========

class ResumeWorkflowState(TypedDict):
    """
    简历定制工作流状态

    每个字段代表工作流中的一个状态变量。
    Agent 节点读取输入状态，输出更新后的状态。
    """
    # 输入
    vault_data: str           # 用户 Vault JSON
    jd_text: str              # 职位描述
    style: str                # 简历风格

    # 中间结果
    jd_analysis: str          # JD 分析结果
    vault_search_results: str # Vault 搜索结果
    match_score: str          # 匹配度评分

    # 生成内容
    generated_sections: Annotated[List[Dict], "已生成的章节列表"]  # 支持累加
    final_resume: str         # 最终简历

    # 验证
    verification_result: str  # 事实校验结果
    is_valid: bool            # 是否通过校验

    # 控制
    current_step: str         # 当前步骤
    retry_count: int          # 重试次数
    errors: Annotated[List[str], "错误列表"]  # 支持累加


# ========== 节点函数 ==========

async def analyze_jd_node(state: ResumeWorkflowState) -> ResumeWorkflowState:
    """
    节点 1: 分析 JD

    提取职位要求，为后续步骤提供结构化输入。
    """
    logger.info(f"[Workflow] Step 1: 分析 JD")

    try:
        result = await analyze_jd_v2.ainvoke({
            "jd_text": state["jd_text"]
        })

        return {
            **state,
            "jd_analysis": result,
            "current_step": "jd_analyzed"
        }
    except Exception as e:
        logger.error(f"[Workflow] JD 分析失败: {e}")
        return {
            **state,
            "errors": [f"JD 分析失败: {e}"],
            "current_step": "jd_analysis_failed"
        }


async def search_vault_node(state: ResumeWorkflowState) -> ResumeWorkflowState:
    """
    节点 2: 搜索 Vault

    基于 JD 分析结果，从 Vault 检索相关经历。
    """
    logger.info(f"[Workflow] Step 2: 搜索 Vault")

    try:
        # 从 JD 分析中提取关键技能作为搜索查询
        jd_analysis = json.loads(state["jd_analysis"])
        priority_skills = jd_analysis.get("priority_skills", [])
        required_skills = [s["skill"] for s in jd_analysis.get("required_skills", [])]

        # 构建搜索查询
        search_queries = priority_skills[:2] + required_skills[:3]
        query = " ".join(search_queries) if search_queries else "相关经验"

        result = await search_vault_v2.ainvoke({
            "query": query,
            "vault_data": state["vault_data"],
            "top_k": 5,
            "search_type": "keyword"
        })

        return {
            **state,
            "vault_search_results": result,
            "current_step": "vault_searched"
        }
    except Exception as e:
        logger.error(f"[Workflow] Vault 搜索失败: {e}")
        return {
            **state,
            "errors": state.get("errors", []) + [f"Vault 搜索失败: {e}"],
            "current_step": "vault_search_failed"
        }


async def calculate_match_node(state: ResumeWorkflowState) -> ResumeWorkflowState:
    """
    节点 3: 计算匹配度

    评估 Vault 与 JD 的匹配程度。
    """
    logger.info(f"[Workflow] Step 3: 计算匹配度")

    try:
        result = await calculate_match_score_v2.ainvoke({
            "vault_data": state["vault_data"],
            "jd_text": state["jd_text"]
        })

        return {
            **state,
            "match_score": result,
            "current_step": "match_calculated"
        }
    except Exception as e:
        logger.error(f"[Workflow] 匹配度计算失败: {e}")
        return {
            **state,
            "errors": state.get("errors", []) + [f"匹配度计算失败: {e}"],
            "current_step": "match_calc_failed"
        }


async def generate_resume_node(state: ResumeWorkflowState) -> ResumeWorkflowState:
    """
    节点 4: 生成简历

    分章节生成定制简历。
    使用并行生成提升性能。
    """
    logger.info(f"[Workflow] Step 4: 生成简历")

    try:
        import asyncio

        # 定义要生成的章节
        sections = ["summary", "experience", "skills"]

        # 并行生成各章节
        tasks = [
            generate_resume_section.ainvoke({
                "section_type": section,
                "content_requirements": f"基于 JD 分析: {state['jd_analysis'][:200]}...",
                "vault_data": state["vault_data"],
                "style": state.get("style", "professional")
            })
            for section in sections
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        generated_sections = []
        for section, result in zip(sections, results):
            if isinstance(result, Exception):
                logger.warning(f"[Workflow] 章节 {section} 生成失败: {result}")
                generated_sections.append({
                    "section_type": section,
                    "error": str(result)
                })
            else:
                data = json.loads(result)
                generated_sections.append(data)

        # 合并所有章节为完整简历
        final_resume = _combine_sections(generated_sections, state)

        return {
            **state,
            "generated_sections": generated_sections,
            "final_resume": final_resume,
            "current_step": "resume_generated"
        }
    except Exception as e:
        logger.error(f"[Workflow] 简历生成失败: {e}")
        return {
            **state,
            "errors": state.get("errors", []) + [f"简历生成失败: {e}"],
            "current_step": "resume_gen_failed"
        }


async def verify_facts_node(state: ResumeWorkflowState) -> ResumeWorkflowState:
    """
    节点 5: 事实校验

    确保生成的简历内容基于事实，无幻觉。
    """
    logger.info(f"[Workflow] Step 5: 事实校验")

    try:
        result = await verify_facts.ainvoke({
            "generated_content": state["final_resume"],
            "vault_data": state["vault_data"],
            "strict_mode": True
        })

        data = json.loads(result)
        is_valid = data.get("is_valid", False)

        # 如果有幻觉且未超过重试次数，标记需要重试
        retry_count = state.get("retry_count", 0)
        if not is_valid and retry_count < 2:
            logger.warning(f"[Workflow] 发现幻觉，准备重试 (第 {retry_count + 1} 次)")
            return {
                **state,
                "verification_result": result,
                "is_valid": False,
                "retry_count": retry_count + 1,
                "current_step": "needs_retry",
                "errors": state.get("errors", []) + data.get("hallucinations", [])
            }

        # 使用修正后的内容（如果有）
        final_resume = data.get("corrected_content", state["final_resume"])

        return {
            **state,
            "verification_result": result,
            "is_valid": is_valid,
            "final_resume": final_resume,
            "current_step": "verified"
        }
    except Exception as e:
        logger.error(f"[Workflow] 事实校验失败: {e}")
        return {
            **state,
            "errors": state.get("errors", []) + [f"事实校验失败: {e}"],
            "current_step": "verification_failed",
            "is_valid": False
        }


# ========== 路由函数 ==========

def route_after_verification(state: ResumeWorkflowState) -> Literal["generate_resume", "end"]:
    """
    校验后的路由决策

    - 如果校验通过 → 结束
    - 如果需要重试 → 回到生成步骤
    """
    if state.get("current_step") == "needs_retry" and state.get("retry_count", 0) < 2:
        logger.info(f"[Workflow] 路由: 重试生成")
        return "generate_resume"

    logger.info(f"[Workflow] 路由: 结束")
    return "end"


def route_on_error(state: ResumeWorkflowState) -> Literal["continue", "end"]:
    """
    错误处理路由

    - 如果错误过多 → 提前结束
    - 否则 → 继续执行
    """
    errors = state.get("errors", [])
    if len(errors) >= 3:
        logger.error(f"[Workflow] 错误过多，提前结束")
        return "end"
    return "continue"


# ========== 辅助函数 ==========

def _combine_sections(sections: List[Dict], state: ResumeWorkflowState) -> str:
    """合并各章节为完整简历"""
    parts = []

    # 添加标题
    parts.append("# 定制简历\n")

    # 添加匹配度信息
    if state.get("match_score"):
        try:
            score_data = json.loads(state["match_score"])
            overall = score_data.get("overall_score", 0)
            parts.append(f"\n> 匹配度评分: {overall}/100\n")
        except:
            pass

    # 按顺序添加各章节
    section_order = ["summary", "experience", "skills", "education", "projects"]

    for section_type in section_order:
        for section in sections:
            if section.get("section_type") == section_type:
                if "error" not in section:
                    parts.append(section.get("content", ""))
                    parts.append("\n---\n")
                break

    return "\n".join(parts)


# ========== 工作流构建 ==========

def create_resume_workflow() -> StateGraph:
    """
    创建简历定制工作流

    Returns:
        编译后的 StateGraph 工作流
    """
    # 创建工作流构建器
    workflow = StateGraph(ResumeWorkflowState)

    # 添加节点
    workflow.add_node("analyze_jd", analyze_jd_node)
    workflow.add_node("search_vault", search_vault_node)
    workflow.add_node("calculate_match", calculate_match_node)
    workflow.add_node("generate_resume", generate_resume_node)
    workflow.add_node("verify_facts", verify_facts_node)

    # 添加边（执行顺序）
    workflow.add_edge(START, "analyze_jd")
    workflow.add_edge("analyze_jd", "search_vault")
    workflow.add_edge("search_vault", "calculate_match")
    workflow.add_edge("calculate_match", "generate_resume")
    workflow.add_edge("generate_resume", "verify_facts")

    # 添加条件边（校验后路由）
    workflow.add_conditional_edges(
        "verify_facts",
        route_after_verification,
        {
            "generate_resume": "generate_resume",  # 重试
            "end": END
        }
    )

    # 编译工作流
    return workflow.compile()


# ========== 便捷使用函数 ==========

async def run_resume_workflow(
    vault_data: Dict[str, Any],
    jd_text: str,
    style: str = "professional"
) -> Dict[str, Any]:
    """
    运行完整的简历定制工作流

    Args:
        vault_data: 用户 Vault 数据
        jd_text: 职位描述
        style: 简历风格

    Returns:
        包含最终简历和工作流状态的字典
    """
    workflow = create_resume_workflow()

    # 初始状态
    initial_state = ResumeWorkflowState(
        vault_data=json.dumps(vault_data, ensure_ascii=False),
        jd_text=jd_text,
        style=style,
        jd_analysis="",
        vault_search_results="",
        match_score="",
        generated_sections=[],
        final_resume="",
        verification_result="",
        is_valid=False,
        current_step="started",
        retry_count=0,
        errors=[]
    )

    # 执行工作流
    result = await workflow.ainvoke(initial_state)

    return {
        "final_resume": result.get("final_resume", ""),
        "is_valid": result.get("is_valid", False),
        "match_score": result.get("match_score", ""),
        "verification_result": result.get("verification_result", ""),
        "errors": result.get("errors", []),
        "steps_completed": result.get("current_step", ""),
        "retry_count": result.get("retry_count", 0)
    }
