"""
ResumeTailorAgent - 简历定制 Agent

基于 ReAct 模式的智能简历定制 Agent。
核心能力：
1. 分析 JD 提取关键要求
2. 从 Vault 检索相关经历
3. 生成定制化简历章节
4. 事实校验防止幻觉

架构：ReAct (Reasoning + Acting)
- Thought: 分析 JD 和 Vault 数据，制定定制策略
- Action: 调用工具（提取关键词、搜索 Vault、生成章节、校验事实）
- Observation: 获取工具执行结果
- 循环直到生成满意简历
"""

import os
import json
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage

from ..config import get_settings

from ..tools import (
    extract_jd_keywords,
    search_vault,
    generate_resume_section,
    verify_facts,
    calculate_match_score,
)


# Agent 系统提示词 —— 定义 Agent 的角色和行为准则
RESUME_TAILOR_SYSTEM_PROMPT = """你是 Career Co-Pilot 的简历定制专家 Agent。

## 核心使命
帮助用户基于真实经历生成针对特定 JD 的定制简历。

## 工作原则
1. **严格基于事实**: 所有内容必须来源于用户的 Career Vault，禁止虚构任何技能或经历
2. **精准匹配**: 深入理解 JD 要求，突出最相关的经历
3. **专业表达**: 使用行业术语，量化成果
4. **防幻觉**: 生成后必须进行事实校验

## 工作流程
当收到定制请求时，按以下步骤执行：

1. **分析 JD**: 调用 extract_jd_keywords 提取职位核心要求
2. **检索经历**: 调用 search_vault 从 Vault 中找到相关经历
3. **评估匹配**: 调用 calculate_match_score 计算匹配度
4. **生成简历**: 调用 generate_resume_section 分章节生成简历
5. **事实校验**: 调用 verify_facts 确保无幻觉内容
6. **输出结果**: 整合所有章节，输出完整定制简历

## 重要约束
- 不得虚构 Vault 中没有的技能
- 不得夸大用户经历（如"主导"改为"参与" unless 有明确证据）
- 时间线必须准确
- 公司名称、职位名称必须完全匹配 Vault

## 输出格式
最终输出应为结构化的 JSON：
{
    "tailored_resume": "完整简历 Markdown",
    "match_analysis": "匹配度分析",
    "key_highlights": ["突出亮点1", "突出亮点2"],
    "suggestions": ["投递建议1"]
}
"""


class ResumeTailorAgent:
    """
    简历定制 Agent

    封装了 ReAct Agent 的创建和调用逻辑。
    提供高级接口，简化使用。

    Attributes:
        agent: LangGraph ReAct Agent 实例
        checkpointer: 记忆检查点（用于对话持久化）
        llm: 底层大语言模型
    """

    def __init__(
        self,
        model_provider: str = "openai",
        model_name: str = "gpt-4o",
        temperature: float = 0.1,
        enable_memory: bool = True
    ):
        """
        初始化 ResumeTailorAgent

        Args:
            model_provider: 模型提供商，"openai" 或 "anthropic"
            model_name: 模型名称，如 "gpt-4o", "claude-3-5-sonnet-20241022"
            temperature: 生成温度，简历定制建议低温度（0.1-0.3）
            enable_memory: 是否启用对话记忆
        """
        self.model_provider = model_provider
        self.model_name = model_name
        self.temperature = temperature

        # 初始化 LLM
        self.llm = self._create_llm()

        # 初始化工具集
        self.tools = [
            extract_jd_keywords,
            search_vault,
            generate_resume_section,
            verify_facts,
            calculate_match_score,
        ]

        # 初始化记忆（Phase 3 将升级为持久化存储）
        self.checkpointer = MemorySaver() if enable_memory else None

        # 创建 ReAct Agent
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=RESUME_TAILOR_SYSTEM_PROMPT,
            checkpointer=self.checkpointer
        )

    def _create_llm(self):
        """创建 LLM 实例"""
        settings = get_settings()

        if self.model_provider == "openai":
            return ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                api_key=settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
            )
        elif self.model_provider == "anthropic":
            return ChatAnthropic(
                model=self.model_name,
                temperature=self.temperature,
                api_key=settings.ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY")
            )
        elif self.model_provider == "deepseek":
            # DeepSeek 使用 OpenAI 兼容接口
            return ChatOpenAI(
                model=settings.DEEPSEEK_MODEL or "deepseek-chat",
                temperature=self.temperature,
                api_key=settings.DEEPSEEK_API_KEY or os.getenv("DEEPSEEK_API_KEY"),
                base_url=settings.DEEPSEEK_BASE_URL or "https://api.deepseek.com/v1"
            )
        else:
            raise ValueError(f"不支持的模型提供商: {self.model_provider}")

    async def tailor_resume(
        self,
        vault_data: Dict[str, Any],
        jd_text: str,
        style: str = "professional",
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        定制简历的主入口

        执行完整的 ReAct 循环：
        1. 分析 JD → 2. 检索 Vault → 3. 生成简历 → 4. 校验事实

        Args:
            vault_data: 用户 Career Vault 数据
            jd_text: 职位描述文本
            style: 简历风格，"professional"/"technical"/"concise"
            thread_id: 对话线程 ID（用于记忆持久化）

        Returns:
            包含定制简历和分析结果的字典

        Example:
            agent = ResumeTailorAgent()
            result = await agent.tailor_resume(
                vault_data=user_vault,
                jd_text="要求：Python, FastAPI, 3年经验...",
                style="technical"
            )
            print(result["tailored_resume"])
        """
        # 构建用户请求
        vault_json = json.dumps(vault_data, ensure_ascii=False)

        user_message = f"""请为以下职位定制简历：

## 职位描述
{jd_text}

## 用户经历数据
{vault_json}

## 要求
- 风格: {style}
- 必须基于真实经历，禁止虚构
- 突出与职位最相关的技能和经验
- 生成后必须进行事实校验

请按照工作流程逐步执行，最终输出 JSON 格式的结果。"""

        # 配置（包含 thread_id 用于记忆）
        config = {"configurable": {}}
        if thread_id:
            config["configurable"]["thread_id"] = thread_id

        # 调用 Agent（触发 ReAct 循环）
        response = await self.agent.ainvoke(
            {"messages": [("user", user_message)]},
            config=config
        )

        # 解析结果
        return self._parse_response(response)

    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析 Agent 响应"""
        messages = response.get("messages", [])

        if not messages:
            return {
                "tailored_resume": "",
                "match_analysis": "生成失败",
                "key_highlights": [],
                "suggestions": [],
                "error": "Agent 未返回有效消息"
            }

        # 获取最后一条 AI 消息
        last_message = messages[-1]
        content = last_message.content if hasattr(last_message, "content") else str(last_message)

        # 尝试解析 JSON
        try:
            # 提取 JSON 部分（Agent 可能包裹在 markdown 代码块中）
            json_match = self._extract_json(content)
            if json_match:
                return json_match
        except Exception:
            pass

        # 如果解析失败，返回原始内容
        return {
            "tailored_resume": content,
            "match_analysis": "",
            "key_highlights": [],
            "suggestions": [],
            "raw_response": content
        }

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """从文本中提取 JSON"""
        # 匹配 ```json ... ``` 格式
        import re
        json_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_pattern, text, re.DOTALL)

        if match:
            return json.loads(match.group(1))

        # 尝试直接解析整个文本
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    async def analyze_match(
        self,
        vault_data: Dict[str, Any],
        jd_text: str
    ) -> Dict[str, Any]:
        """
        快速分析 Vault 与 JD 的匹配度（不生成简历）

        Args:
            vault_data: 用户 Career Vault 数据
            jd_text: 职位描述文本

        Returns:
            匹配度分析结果
        """
        vault_json = json.dumps(vault_data, ensure_ascii=False)

        user_message = f"""请分析以下经历与职位的匹配度：

## 职位描述
{jd_text}

## 用户经历
{vault_json}

请调用 extract_jd_keywords 和 calculate_match_score 工具进行分析，
返回匹配度评分和关键差距。"""

        response = await self.agent.ainvoke(
            {"messages": [("user", user_message)]}
        )

        return self._parse_response(response)


# 全局 Agent 实例（单例模式）
_agent_instance: Optional[ResumeTailorAgent] = None


def get_resume_tailor_agent() -> ResumeTailorAgent:
    """
    获取 ResumeTailorAgent 单例实例

    使用单例模式避免重复创建 Agent，提升性能。

    Returns:
        ResumeTailorAgent 实例
    """
    global _agent_instance

    if _agent_instance is None:
        # 从配置读取（支持 .env 文件）
        settings = get_settings()
        provider = settings.LLM_PROVIDER or os.getenv("LLM_PROVIDER", "openai")
        model = settings.LLM_MODEL or os.getenv("LLM_MODEL", "gpt-4o")

        # 如果配置了 DeepSeek 但没有配置 OpenAI，自动切换
        if provider == "openai" and not settings.OPENAI_API_KEY:
            if settings.DEEPSEEK_API_KEY:
                provider = "deepseek"
                model = settings.DEEPSEEK_MODEL or "deepseek-chat"
                print(f"[Agent] 自动切换到 DeepSeek 提供商")

        _agent_instance = ResumeTailorAgent(
            model_provider=provider,
            model_name=model
        )

    return _agent_instance
