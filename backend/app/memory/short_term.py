"""
短期记忆系统 - 对话上下文与工作记忆

管理当前会话的临时状态：
1. 对话历史（messages）
2. 工作记忆（当前任务上下文）
3. 缓存数据（Vault 数据等）

特点：
- 生命周期：单次会话
- 存储位置：内存 + 可选数据库持久化
- 容量限制：防止上下文过长（Token 溢出）
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class ShortTermMemory:
    """
    短期记忆管理器
    
    类比人类的工作记忆：
    - 能同时保持 7±2 个信息块
    - 信息会快速衰减（需要刷新）
    - 可以通过复习转入长期记忆
    
    在 Agent 中：
    - 保持最近 N 轮对话
    - 缓存当前任务的关键数据
    - 限制 Token 使用量
    """
    
    # 默认配置
    DEFAULT_MAX_MESSAGES = 20  # 保留最近 20 条消息
    DEFAULT_MAX_TOKENS = 4000  # 最大 Token 数（留余量给系统提示）
    
    def __init__(
        self,
        thread_id: str,
        user_id: str,
        max_messages: int = DEFAULT_MAX_MESSAGES,
        max_tokens: int = DEFAULT_MAX_TOKENS
    ):
        self.thread_id = thread_id
        self.user_id = user_id
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        
        # 对话历史（双端队列，自动淘汰旧消息）
        self._messages: deque = deque(maxlen=max_messages)
        
        # 工作记忆（当前任务的临时数据）
        self._working_memory: Dict[str, Any] = {}
        
        # 缓存（Vault 数据等不变内容）
        self._cache: Dict[str, Any] = {}
        
        # 会话元数据
        self._metadata = {
            "created_at": datetime.utcnow().isoformat(),
            "message_count": 0,
            "token_estimate": 0,
        }
        
        logger.info(f"[ShortTermMemory] 创建新会话: thread={thread_id}")
    
    # ========== 对话历史管理 ==========
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        添加消息到对话历史
        
        Args:
            role: 角色 ("user", "assistant", "system", "tool")
            content: 消息内容
            metadata: 可选元数据（如工具调用信息）
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if metadata:
            message["metadata"] = metadata
        
        self._messages.append(message)
        self._metadata["message_count"] = len(self._messages)
        self._metadata["token_estimate"] += self._estimate_tokens(content)
        
        logger.debug(f"[ShortTermMemory] 添加消息: role={role}, thread={self.thread_id}")
    
    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取对话历史
        
        Args:
            limit: 限制返回的消息数量（None=全部）
        
        Returns:
            消息列表
        """
        messages = list(self._messages)
        if limit and limit < len(messages):
            # 返回最近 N 条
            return messages[-limit:]
        return messages
    
    def get_messages_for_llm(self, system_prompt: Optional[str] = None) -> List[Dict[str, str]]:
        """
        获取适合 LLM 调用的消息格式
        
        自动处理：
        1. Token 超限截断
        2. 系统提示插入
        3. 格式转换
        
        Returns:
            [{"role": "user", "content": "..."}, ...]
        """
        messages = []
        
        # 添加系统提示
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加历史消息（从旧到新）
        total_tokens = self._estimate_tokens(system_prompt or "")
        
        for msg in self._messages:
            msg_tokens = self._estimate_tokens(msg["content"])
            
            # 如果添加这条消息会超限，停止添加
            if total_tokens + msg_tokens > self.max_tokens and messages:
                logger.warning(
                    f"[ShortTermMemory] Token 超限，截断历史: "
                    f"current={total_tokens}, msg={msg_tokens}, max={self.max_tokens}"
                )
                break
            
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
            total_tokens += msg_tokens
        
        return messages
    
    def clear_messages(self):
        """清空对话历史"""
        self._messages.clear()
        self._metadata["message_count"] = 0
        self._metadata["token_estimate"] = 0
        logger.info(f"[ShortTermMemory] 清空对话历史: thread={self.thread_id}")
    
    def get_last_message(self) -> Optional[Dict[str, Any]]:
        """获取最后一条消息"""
        if self._messages:
            return self._messages[-1]
        return None
    
    # ========== 工作记忆管理 ==========
    
    def set_working_memory(self, key: str, value: Any):
        """
        设置工作记忆
        
        用于存储当前任务的中间状态：
        - 当前分析的 JD
        - 提取的技能列表
        - 匹配结果
        """
        self._working_memory[key] = value
        logger.debug(f"[ShortTermMemory] 设置工作记忆: key={key}")
    
    def get_working_memory(self, key: str, default: Any = None) -> Any:
        """获取工作记忆"""
        return self._working_memory.get(key, default)
    
    def get_all_working_memory(self) -> Dict[str, Any]:
        """获取所有工作记忆"""
        return self._working_memory.copy()
    
    def clear_working_memory(self):
        """清空工作记忆"""
        self._working_memory.clear()
        logger.info(f"[ShortTermMemory] 清空工作记忆: thread={self.thread_id}")
    
    # ========== 缓存管理 ==========
    
    def set_cache(self, key: str, value: Any):
        """
        设置缓存
        
        用于存储不常变化的数据：
        - Vault 数据（用户不修改时不变）
        - JD 分析结果（同一 JD 不变）
        """
        self._cache[key] = {
            "value": value,
            "cached_at": datetime.utcnow().isoformat(),
        }
    
    def get_cache(self, key: str) -> Optional[Any]:
        """获取缓存"""
        entry = self._cache.get(key)
        if entry:
            return entry["value"]
        return None
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
    
    # ========== 会话摘要 ==========
    
    def generate_summary(self) -> str:
        """
        生成会话摘要
        
        用于：
        1. 长期记忆存储（压缩后存入）
        2. 会话列表展示
        3. 快速恢复上下文
        """
        messages = self.get_messages()
        
        if not messages:
            return "空会话"
        
        # 提取关键信息
        user_messages = [m for m in messages if m["role"] == "user"]
        assistant_messages = [m for m in messages if m["role"] == "assistant"]
        
        # 简单摘要（实际可用 LLM 生成更好摘要）
        summary_parts = [
            f"会话包含 {len(messages)} 条消息",
            f"用户提问 {len(user_messages)} 次",
            f"助手回复 {len(assistant_messages)} 次",
        ]
        
        # 提取用户意图（从第一条消息）
        if user_messages:
            first_msg = user_messages[0]["content"][:100]
            summary_parts.append(f"初始请求: {first_msg}...")
        
        return "; ".join(summary_parts)
    
    # ========== 序列化 ==========
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "thread_id": self.thread_id,
            "user_id": self.user_id,
            "messages": list(self._messages),
            "working_memory": self._working_memory,
            "metadata": self._metadata,
        }
    
    def to_db_format(self) -> Dict[str, Any]:
        """转换为数据库存储格式"""
        return {
            "thread_id": self.thread_id,
            "user_id": self.user_id,
            "messages": json.dumps(list(self._messages), ensure_ascii=False),
            "message_count": len(self._messages),
            "status": "active",
        }
    
    @classmethod
    def from_db_format(cls, data: Dict[str, Any]) -> "ShortTermMemory":
        """从数据库格式恢复"""
        memory = cls(
            thread_id=data["thread_id"],
            user_id=data["user_id"],
        )
        
        # 恢复消息
        messages = json.loads(data.get("messages", "[]"))
        for msg in messages:
            memory._messages.append(msg)
        
        memory._metadata["message_count"] = len(memory._messages)
        
        return memory
    
    # ========== 内部方法 ==========
    
    def _estimate_tokens(self, text: Optional[str]) -> int:
        """
        估算 Token 数
        
        简单估算：中文 ≈ 1.5 tokens/字，英文 ≈ 0.25 tokens/字
        实际应使用 tiktoken 库精确计算
        """
        if not text:
            return 0
        
        # 粗略估算
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        
        return int(chinese_chars * 1.5 + other_chars * 0.25)
    
    def __repr__(self):
        return (
            f"<ShortTermMemory(thread={self.thread_id}, "
            f"messages={len(self._messages)}, "
            f"working_keys={list(self._working_memory.keys())})>"
        )
