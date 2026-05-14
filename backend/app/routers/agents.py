"""
Agent API Router - Agent 服务接口

提供 Agent 能力的 REST API 接口，包括：
- 简历定制 Agent（ReAct 模式）
- 简历定制工作流（LangGraph StateGraph 模式 - Phase 2 添加）
- JD 分析 Agent
- 面试教练 Agent

所有端点都遵循 FastAPI 最佳实践，包含完整的输入校验和错误处理。
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import logging
import json
import time

from ..agents import get_resume_tailor_agent
from ..graphs.resume_workflow import run_resume_workflow
from ..memory import get_memory_manager
from ..auth import get_current_user

logger = logging.getLogger(__name__)

# Router 定义
router = APIRouter(
    prefix="/api/agents",
    tags=["agents"],
    responses={404: {"description": "Not found"}}
)


# ========== 请求/响应模型 ==========

class TailorResumeRequest(BaseModel):
    """简历定制请求"""
    vault_data: Dict[str, Any] = Field(
        ...,
        description="用户 Career Vault 数据",
        example={
            "personal_info": {"name": "张三"},
            "skills": ["Python", "FastAPI"],
            "work_experience": [
                {
                    "company": "某某科技",
                    "title": "后端工程师",
                    "highlights": ["负责微服务架构"]
                }
            ]
        }
    )
    jd_text: str = Field(
        ...,
        description="职位描述文本",
        example="要求：3年以上 Python 开发经验，熟悉 FastAPI..."
    )
    style: str = Field(
        default="professional",
        description="简历风格: professional/technical/concise",
        example="technical"
    )
    thread_id: Optional[str] = Field(
        default=None,
        description="对话线程 ID（用于记忆持久化）"
    )


class TailorResumeResponse(BaseModel):
    """简历定制响应"""
    tailored_resume: str = Field(..., description="定制后的简历内容（Markdown）")
    match_analysis: str = Field(..., description="匹配度分析")
    key_highlights: list = Field(default=[], description="突出亮点")
    suggestions: list = Field(default=[], description="投递建议")
    raw_response: Optional[str] = Field(default=None, description="原始响应（调试用）")


class WorkflowTailorRequest(BaseModel):
    """工作流简历定制请求（LangGraph StateGraph）"""
    vault_data: Dict[str, Any] = Field(
        ...,
        description="用户 Career Vault 数据",
        example={
            "personal_info": {"name": "张三"},
            "skills": ["Python", "FastAPI"],
            "work_experience": [
                {
                    "company": "某某科技",
                    "title": "后端工程师",
                    "highlights": ["负责微服务架构"]
                }
            ]
        }
    )
    jd_text: str = Field(
        ...,
        description="职位描述文本",
        example="要求：3年以上 Python 开发经验，熟悉 FastAPI..."
    )
    style: str = Field(
        default="professional",
        description="简历风格: professional/technical/concise",
        example="technical"
    )


class WorkflowTailorResponse(BaseModel):
    """工作流简历定制响应"""
    final_resume: str = Field(..., description="定制后的简历内容（Markdown）")
    is_valid: bool = Field(..., description="是否通过事实校验")
    match_score: Dict[str, Any] = Field(..., description="匹配度评分详情")
    verification_result: Dict[str, Any] = Field(..., description="事实校验结果")
    steps_completed: str = Field(..., description="完成的工作流步骤")
    retry_count: int = Field(..., description="重试次数")
    errors: list = Field(default=[], description="执行过程中的错误")
    execution_time_ms: Optional[int] = Field(default=None, description="执行耗时（毫秒）")


class AnalyzeMatchRequest(BaseModel):
    """匹配度分析请求"""
    vault_data: Dict[str, Any] = Field(..., description="用户 Career Vault 数据")
    jd_text: str = Field(..., description="职位描述文本")


class AnalyzeMatchResponse(BaseModel):
    """匹配度分析响应"""
    overall_score: int = Field(..., description="综合匹配度评分 0-100")
    skill_match: Dict[str, Any] = Field(..., description="技能匹配详情")
    experience_match: Dict[str, Any] = Field(..., description="经验匹配详情")
    recommendations: list = Field(default=[], description="改进建议")


# ========== 记忆系统 API 模型 ==========

class SavePreferenceRequest(BaseModel):
    """保存用户偏好请求"""
    preference_type: str = Field(..., description="偏好类型", example="resume_style")
    preference_value: Any = Field(..., description="偏好值", example="technical")
    preference_key: str = Field(default="primary", description="偏好键")


class GetPreferencesResponse(BaseModel):
    """获取用户偏好响应"""
    preferences: Dict[str, Any] = Field(..., description="用户偏好字典")
    user_id: str = Field(..., description="用户 ID")


class ConversationMessageRequest(BaseModel):
    """保存对话消息请求"""
    role: str = Field(..., description="角色: user/assistant/system", example="user")
    content: str = Field(..., description="消息内容", example="帮我定制简历")
    thread_id: Optional[str] = Field(default=None, description="线程 ID（None=新建）")


class ConversationResponse(BaseModel):
    """对话响应"""
    thread_id: str = Field(..., description="线程 ID")
    messages: List[Dict[str, Any]] = Field(..., description="消息列表")
    message_count: int = Field(..., description="消息数量")


class UserProfileResponse(BaseModel):
    """用户画像响应"""
    user_id: str = Field(..., description="用户 ID")
    preferences: Dict[str, Any] = Field(..., description="用户偏好")
    total_sessions: int = Field(default=0, description="总会话数")
    total_messages: int = Field(default=0, description="总消息数")
    session_type_distribution: Dict[str, int] = Field(default={}, description="会话类型分布")


# ========== API 端点 ==========

@router.post(
    "/tailor-resume",
    response_model=TailorResumeResponse,
    summary="简历定制 Agent",
    description="""
    使用 ReAct Agent 为用户定制针对特定 JD 的简历。

    Agent 执行流程：
    1. 分析 JD 提取关键要求
    2. 从 Vault 检索相关经历
    3. 计算匹配度评分
    4. 分章节生成定制简历
    5. 事实校验防止幻觉

    此端点替代原有的 `/api/jobs/{id}/tailor` 单体 LLM 调用。
    """
)
async def tailor_resume(
    request: TailorResumeRequest,
    current_user: Dict = Depends(get_current_user)
) -> TailorResumeResponse:
    """
    简历定制 Agent 入口

    Args:
        request: 包含 vault_data, jd_text, style 的请求体
        current_user: 当前登录用户（JWT 认证）

    Returns:
        定制简历和分析结果

    Raises:
        HTTPException 500: Agent 执行失败
    """
    try:
        logger.info(f"用户 {current_user.get('id')} 请求简历定制")

        # 获取 Agent 实例
        agent = get_resume_tailor_agent()

        # 调用 Agent（触发 ReAct 循环）
        result = await agent.tailor_resume(
            vault_data=request.vault_data,
            jd_text=request.jd_text,
            style=request.style,
            thread_id=request.thread_id
        )

        logger.info("简历定制完成")

        return TailorResumeResponse(
            tailored_resume=result.get("tailored_resume", ""),
            match_analysis=result.get("match_analysis", ""),
            key_highlights=result.get("key_highlights", []),
            suggestions=result.get("suggestions", []),
            raw_response=result.get("raw_response")
        )

    except Exception as e:
        logger.error(f"简历定制失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Agent 执行失败: {str(e)}"
        )


@router.post(
    "/tailor-resume/workflow",
    response_model=WorkflowTailorResponse,
    summary="简历定制工作流（LangGraph）",
    description="""
    使用 LangGraph StateGraph 工作流为用户定制简历。

    相比传统的 ReAct Agent，工作流模式提供：
    1. 显式状态管理（每个步骤可观测）
    2. 精确的执行顺序控制
    3. 条件路由（自动重试机制）
    4. 更精细的错误处理

    工作流步骤：
    1. analyze_jd: 分析 JD 提取关键要求
    2. search_vault: 从 Vault 检索相关经历
    3. calculate_match: 计算匹配度评分
    4. generate_resume: 分章节生成定制简历
    5. verify_facts: 事实校验防止幻觉
    6. 条件路由: 校验失败时自动重试（最多2次）
    """
)
async def tailor_resume_workflow(
    request: WorkflowTailorRequest,
    current_user: Dict = Depends(get_current_user)
) -> WorkflowTailorResponse:
    """
    简历定制工作流入口（LangGraph StateGraph）

    Args:
        request: 包含 vault_data, jd_text, style 的请求体
        current_user: 当前登录用户（JWT 认证）

    Returns:
        包含最终简历、校验结果和执行状态的响应

    Raises:
        HTTPException 500: 工作流执行失败
    """
    import time

    try:
        logger.info(f"用户 {current_user.get('id')} 请求工作流简历定制")

        start_time = time.time()

        # 调用 LangGraph 工作流
        result = await run_resume_workflow(
            vault_data=request.vault_data,
            jd_text=request.jd_text,
            style=request.style
        )

        elapsed_ms = int((time.time() - start_time) * 1000)

        logger.info(f"工作流执行完成，耗时 {elapsed_ms}ms，步骤: {result['steps_completed']}")

        # 解析 match_score（如果是字符串）
        match_score = result.get("match_score", {})
        if isinstance(match_score, str):
            try:
                match_score = json.loads(match_score)
            except json.JSONDecodeError:
                match_score = {"raw": match_score}

        # 解析 verification_result（如果是字符串）
        verification = result.get("verification_result", {})
        if isinstance(verification, str):
            try:
                verification = json.loads(verification)
            except json.JSONDecodeError:
                verification = {"raw": verification}

        return WorkflowTailorResponse(
            final_resume=result.get("final_resume", ""),
            is_valid=result.get("is_valid", False),
            match_score=match_score,
            verification_result=verification,
            steps_completed=result.get("steps_completed", ""),
            retry_count=result.get("retry_count", 0),
            errors=result.get("errors", []),
            execution_time_ms=elapsed_ms
        )

    except Exception as e:
        logger.error(f"工作流执行失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"工作流执行失败: {str(e)}"
        )


@router.post(
    "/analyze-match",
    response_model=AnalyzeMatchResponse,
    summary="匹配度分析 Agent",
    description="分析用户 Vault 与职位 JD 的匹配度，不生成简历"
)
async def analyze_match(
    request: AnalyzeMatchRequest,
    current_user: Dict = Depends(get_current_user)
) -> AnalyzeMatchResponse:
    """
    快速匹配度分析

    Args:
        request: 包含 vault_data 和 jd_text
        current_user: 当前登录用户

    Returns:
        匹配度评分和详细分析
    """
    try:
        logger.info(f"用户 {current_user.get('id')} 请求匹配度分析")

        agent = get_resume_tailor_agent()
        result = await agent.analyze_match(
            vault_data=request.vault_data,
            jd_text=request.jd_text
        )

        # 解析匹配度结果
        match_data = result.get("match_analysis", {})
        if isinstance(match_data, str):
            # 如果返回的是字符串，构造默认响应
            return AnalyzeMatchResponse(
                overall_score=70,
                skill_match={"score": 70, "matched": [], "missing": []},
                experience_match={"score": 70, "assessment": "需要分析"},
                recommendations=["请查看详细分析"]
            )

        return AnalyzeMatchResponse(
            overall_score=match_data.get("overall_score", 0),
            skill_match=match_data.get("skill_match", {}),
            experience_match=match_data.get("experience_match", {}),
            recommendations=match_data.get("recommendations", [])
        )

    except Exception as e:
        logger.error(f"匹配度分析失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"分析失败: {str(e)}"
        )


@router.get(
    "/health",
    summary="Agent 健康检查",
    description="检查 Agent 系统是否正常运行"
)
async def agent_health() -> Dict[str, Any]:
    """
    Agent 健康检查端点

    Returns:
        系统状态信息
    """
    try:
        agent = get_resume_tailor_agent()
        return {
            "status": "healthy",
            "agent": "resume_tailor",
            "model_provider": agent.model_provider,
            "model_name": agent.model_name,
            "tools_count": len(agent.tools),
            "memory_enabled": agent.checkpointer is not None
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get(
    "/tools",
    summary="列出可用工具",
    description="获取当前 Agent 支持的所有工具列表"
)
async def list_tools() -> Dict[str, Any]:
    """
    获取 Agent 工具列表

    Returns:
        工具名称和描述列表
    """
    agent = get_resume_tailor_agent()

    tools_info = []
    for tool in agent.tools:
        tools_info.append({
            "name": tool.name,
            "description": tool.description[:100] + "..." if len(tool.description) > 100 else tool.description,
            "args": list(tool.args.keys()) if hasattr(tool, "args") else []
        })

    return {
        "agent": "resume_tailor",
        "tools_count": len(tools_info),
        "tools": tools_info
    }


# ========== 记忆系统 API 端点 ==========

@router.post(
    "/memory/preference",
    response_model=Dict[str, Any],
    summary="保存用户偏好",
    description="保存用户偏好到长期记忆"
)
async def save_preference(
    request: SavePreferenceRequest,
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    保存用户偏好

    Args:
        request: 偏好类型和值
        current_user: 当前用户

    Returns:
        保存结果
    """
    try:
        memory = get_memory_manager(
            user_id=current_user.get("id"),
            thread_id="preference_api"
        )

        success = memory.save_user_preference(
            preference_type=request.preference_type,
            preference_value=request.preference_value,
            preference_key=request.preference_key
        )

        return {
            "success": success,
            "preference_type": request.preference_type,
            "preference_key": request.preference_key,
            "preference_value": request.preference_value
        }

    except Exception as e:
        logger.error(f"保存偏好失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/memory/preferences",
    response_model=GetPreferencesResponse,
    summary="获取用户偏好",
    description="获取用户所有偏好设置"
)
async def get_preferences(
    current_user: Dict = Depends(get_current_user)
) -> GetPreferencesResponse:
    """
    获取用户偏好

    Args:
        current_user: 当前用户

    Returns:
        用户偏好字典
    """
    try:
        memory = get_memory_manager(
            user_id=current_user.get("id"),
            thread_id="preference_api"
        )

        preferences = memory.long_term.get_all_preferences()

        return GetPreferencesResponse(
            preferences=preferences,
            user_id=current_user.get("id")
        )

    except Exception as e:
        logger.error(f"获取偏好失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/memory/message",
    response_model=ConversationResponse,
    summary="保存对话消息",
    description="保存消息到对话历史"
)
async def save_message(
    request: ConversationMessageRequest,
    current_user: Dict = Depends(get_current_user)
) -> ConversationResponse:
    """
    保存对话消息

    Args:
        request: 消息内容
        current_user: 当前用户

    Returns:
        更新后的对话状态
    """
    try:
        thread_id = request.thread_id or f"thread_{current_user.get('id')}_{int(time.time())}"

        memory = get_memory_manager(
            user_id=current_user.get("id"),
            thread_id=thread_id
        )

        memory.save_message(request.role, request.content)

        messages = memory.get_messages()

        return ConversationResponse(
            thread_id=thread_id,
            messages=messages,
            message_count=len(messages)
        )

    except Exception as e:
        logger.error(f"保存消息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/memory/conversation/{thread_id}",
    response_model=ConversationResponse,
    summary="获取对话历史",
    description="获取指定线程的对话历史"
)
async def get_conversation(
    thread_id: str,
    current_user: Dict = Depends(get_current_user)
) -> ConversationResponse:
    """
    获取对话历史

    Args:
        thread_id: 线程 ID
        current_user: 当前用户

    Returns:
        对话历史
    """
    try:
        memory = get_memory_manager(
            user_id=current_user.get("id"),
            thread_id=thread_id
        )

        messages = memory.get_messages()

        return ConversationResponse(
            thread_id=thread_id,
            messages=messages,
            message_count=len(messages)
        )

    except Exception as e:
        logger.error(f"获取对话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/memory/profile",
    response_model=UserProfileResponse,
    summary="获取用户画像",
    description="获取用户完整画像（偏好、统计等）"
)
async def get_user_profile(
    current_user: Dict = Depends(get_current_user)
) -> UserProfileResponse:
    """
    获取用户画像

    Args:
        current_user: 当前用户

    Returns:
        用户画像
    """
    try:
        memory = get_memory_manager(
            user_id=current_user.get("id"),
            thread_id="profile_api"
        )

        profile = memory.get_user_profile()

        return UserProfileResponse(
            user_id=profile.get("user_id", current_user.get("id")),
            preferences=profile.get("preferences", {}),
            total_sessions=profile.get("total_sessions", 0),
            total_messages=profile.get("total_messages", 0),
            session_type_distribution=profile.get("session_type_distribution", {})
        )

    except Exception as e:
        logger.error(f"获取用户画像失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/memory/clear/{thread_id}",
    summary="清除记忆缓存",
    description="清除指定线程的记忆缓存"
)
async def clear_memory(
    thread_id: str,
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    清除记忆缓存

    Args:
        thread_id: 线程 ID
        current_user: 当前用户

    Returns:
        操作结果
    """
    try:
        from ..memory import clear_memory_cache
        clear_memory_cache(thread_id)

        return {
            "success": True,
            "thread_id": thread_id,
            "message": "记忆缓存已清除"
        }

    except Exception as e:
        logger.error(f"清除记忆失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
