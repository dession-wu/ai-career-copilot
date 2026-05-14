"""
记忆管理器 - 统一入口

整合短期记忆和长期记忆，提供统一的记忆操作接口。
这是 Agent 与记忆系统交互的唯一入口。

设计模式: Facade（外观模式）
- 隐藏短期/长期记忆的复杂交互
- 提供简洁的 API
- 自动处理记忆之间的同步
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from .short_term import ShortTermMemory
from .long_term import LongTermMemory

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    记忆管理器
    
    统一管理三层记忆：
    1. 短期记忆（ShortTermMemory）- 当前会话
    2. 长期记忆（LongTermMemory）- 用户偏好和历史
    3. 工作记忆（Working Memory）- 当前任务状态
    
    使用示例:
        memory = MemoryManager(user_id="user_123", thread_id="thread_456", db=db_session)
        
        # 保存对话
        memory.save_message("user", "帮我定制简历")
        memory.save_message("assistant", "好的，请提供 JD")
        
        # 获取上下文（自动合并长期记忆）
        context = memory.get_context_for_llm()
        
        # 保存偏好到长期记忆
        memory.save_user_preference("resume_style", "technical")
        
        # 结束会话时归档
        memory.archive_session()
    """
    
    def __init__(
        self,
        user_id: str,
        thread_id: str,
        db: Optional[Session] = None,
        session_type: str = "resume_tailor"
    ):
        self.user_id = user_id
        self.thread_id = thread_id
        self.db = db
        self.session_type = session_type
        
        # 初始化两层记忆
        self.short_term = ShortTermMemory(
            thread_id=thread_id,
            user_id=user_id
        )
        self.long_term = LongTermMemory(
            user_id=user_id,
            db_session=db
        )
        
        # 尝试从长期记忆恢复会话
        if db:
            self._try_restore_session()
        
        logger.info(
            f"[MemoryManager] 初始化: user={user_id}, thread={thread_id}, "
            f"type={session_type}"
        )
    
    # ========== 对话管理 ==========
    
    def save_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        保存消息到短期记忆
        
        Args:
            role: 角色 ("user", "assistant", "system", "tool")
            content: 消息内容
            metadata: 可选元数据
        """
        self.short_term.add_message(role, content, metadata)
        logger.debug(f"[MemoryManager] 保存消息: role={role}, thread={self.thread_id}")
    
    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return self.short_term.get_messages(limit)
    
    def get_context_for_llm(
        self,
        system_prompt: Optional[str] = None,
        include_preferences: bool = True
    ) -> List[Dict[str, str]]:
        """
        获取 LLM 调用的完整上下文
        
        自动：
        1. 合并系统提示
        2. 注入用户偏好
        3. 管理 Token 预算
        
        Returns:
            消息列表，可直接传给 LLM
        """
        messages = []
        
        # 构建增强的系统提示
        enhanced_system = system_prompt or ""
        
        if include_preferences:
            # 注入用户偏好
            preferences = self.get_user_preferences_summary()
            if preferences:
                pref_text = f"\n\n[用户偏好]\n{preferences}"
                enhanced_system += pref_text
        
        # 获取对话历史（自动处理 Token 限制）
        messages = self.short_term.get_messages_for_llm(enhanced_system)
        
        return messages
    
    # ========== 用户偏好管理 ==========
    
    def save_user_preference(
        self,
        preference_type: str,
        preference_value: Any,
        preference_key: str = "primary",
        confidence: int = 50,
        source: str = "explicit"
    ) -> bool:
        """
        保存用户偏好到长期记忆
        
        同时更新短期记忆的缓存
        """
        # 保存到长期记忆
        success = self.long_term.save_preference(
            preference_type=preference_type,
            preference_key=preference_key,
            preference_value=preference_value,
            confidence=confidence,
            source=source
        )
        
        # 同步到短期记忆的工作记忆
        self.short_term.set_working_memory(
            f"preference:{preference_type}:{preference_key}",
            preference_value
        )
        
        if success:
            logger.info(
                f"[MemoryManager] 保存偏好: type={preference_type}, "
                f"key={preference_key}"
            )
        
        return success
    
    def get_user_preference(
        self,
        preference_type: str,
        preference_key: str = "primary",
        default: Any = None
    ) -> Any:
        """获取用户偏好"""
        # 先查短期记忆（更快）
        cache_key = f"preference:{preference_type}:{preference_key}"
        cached = self.short_term.get_working_memory(cache_key)
        if cached is not None:
            return cached
        
        # 再查长期记忆
        return self.long_term.get_preference(
            preference_type=preference_type,
            preference_key=preference_key,
            default=default
        )
    
    def get_user_preferences_summary(self) -> str:
        """
        生成用户偏好的文本摘要
        
        用于注入到系统提示中
        """
        # 从长期记忆获取
        preferences = self.long_term.get_all_preferences()
        
        # 从短期记忆的工作记忆中获取（无数据库时的回退）
        working_memory = self.short_term.get_all_working_memory()
        for key, value in working_memory.items():
            if key.startswith("preference:"):
                # 解析 preference:type:key 格式
                parts = key.split(":")
                if len(parts) == 3:
                    pref_type = parts[1]
                    pref_key = parts[2]
                    if pref_type not in preferences:
                        preferences[pref_type] = {}
                    if isinstance(preferences[pref_type], dict):
                        preferences[pref_type][pref_key] = value
                    else:
                        preferences[pref_type] = {pref_key: value}
        
        if not preferences:
            return ""
        
        parts = []
        for pref_type, values in preferences.items():
            if isinstance(values, dict) and "primary" in values:
                parts.append(f"- {pref_type}: {values['primary']}")
            elif isinstance(values, dict):
                for key, value in values.items():
                    parts.append(f"- {pref_type}.{key}: {value}")
            else:
                parts.append(f"- {pref_type}: {values}")
        
        return "\n".join(parts)
    
    def get_user_profile(self) -> Dict[str, Any]:
        """获取完整用户画像"""
        return self.long_term.build_user_profile()
    
    # ========== 工作记忆管理 ==========
    
    def set_working_memory(self, key: str, value: Any):
        """设置工作记忆"""
        self.short_term.set_working_memory(key, value)
    
    def get_working_memory(self, key: str, default: Any = None) -> Any:
        """获取工作记忆"""
        return self.short_term.get_working_memory(key, default)
    
    # ========== 会话归档 ==========
    
    def archive_session(self, status: str = "completed") -> bool:
        """
        归档当前会话到长期记忆
        
        在会话结束时调用：
        1. 保存对话历史
        2. 生成摘要
        3. 提取偏好更新
        """
        if not self.db:
            logger.warning("[MemoryManager] 无数据库会话，无法归档")
            return False
        
        try:
            # 生成会话摘要
            summary = self.short_term.generate_summary()
            
            # 准备会话数据
            session_data = self.short_term.to_db_format()
            session_data.update({
                "session_type": self.session_type,
                "title": summary[:100] if summary else f"会话 {self.thread_id}",
                "status": status,
            })
            
            # 保存到长期记忆
            success = self.long_term.save_session(session_data)
            
            if success:
                logger.info(
                    f"[MemoryManager] 会话归档成功: thread={self.thread_id}, "
                    f"messages={session_data['message_count']}"
                )
            
            return success
            
        except Exception as e:
            logger.error(f"[MemoryManager] 会话归档失败: {e}")
            return False
    
    # ========== 检查点管理 ==========
    
    def save_checkpoint(self, step_name: str, state: Dict[str, Any], **kwargs) -> bool:
        """
        保存工作流检查点
        
        Args:
            step_name: 当前步骤名称
            state: 工作流状态
            **kwargs: 额外参数
        """
        if not self.db:
            return False
        
        checkpoint_data = {
            "thread_id": self.thread_id,
            "step_name": step_name,
            "state": state,
            **kwargs
        }
        
        return self.long_term.save_checkpoint(checkpoint_data)
    
    def get_latest_checkpoint(self) -> Optional[Dict[str, Any]]:
        """获取最新检查点"""
        return self.long_term.get_latest_checkpoint(self.thread_id)
    
    # ========== 内部方法 ==========
    
    def _try_restore_session(self):
        """尝试从数据库恢复会话"""
        try:
            session = self.long_term.get_session(self.thread_id)
            if session and session.get("status") == "active":
                # 恢复消息
                for msg in session.get("messages", []):
                    self.short_term.add_message(
                        role=msg["role"],
                        content=msg["content"]
                    )
                logger.info(
                    f"[MemoryManager] 恢复会话: thread={self.thread_id}, "
                    f"messages={len(session.get('messages', []))}"
                )
        except Exception as e:
            logger.warning(f"[MemoryManager] 恢复会话失败: {e}")
    
    def __repr__(self):
        return (
            f"<MemoryManager(user={self.user_id}, thread={self.thread_id}, "
            f"messages={len(self.short_term.get_messages())})>"
        )


# ========== 工厂函数 ==========

# 全局缓存（按 thread_id）
_memory_cache: Dict[str, MemoryManager] = {}


def get_memory_manager(
    user_id: str,
    thread_id: str,
    db: Optional[Session] = None,
    session_type: str = "resume_tailor"
) -> MemoryManager:
    """
    获取记忆管理器实例（工厂函数）
    
    使用缓存避免重复创建：
    - 同一线程返回同一实例
    - 新线程创建新实例
    
    Args:
        user_id: 用户 ID
        thread_id: 线程 ID
        db: 数据库会话
        session_type: 会话类型
    
    Returns:
        MemoryManager 实例
    """
    cache_key = f"{user_id}:{thread_id}"
    
    if cache_key in _memory_cache:
        return _memory_cache[cache_key]
    
    # 创建新实例
    manager = MemoryManager(
        user_id=user_id,
        thread_id=thread_id,
        db=db,
        session_type=session_type
    )
    
    _memory_cache[cache_key] = manager
    
    return manager


def clear_memory_cache(thread_id: Optional[str] = None):
    """
    清除记忆缓存
    
    Args:
        thread_id: 指定线程（None=清除全部）
    """
    global _memory_cache
    
    if thread_id:
        # 清除指定线程
        keys_to_remove = [k for k in _memory_cache if k.endswith(f":{thread_id}")]
        for key in keys_to_remove:
            del _memory_cache[key]
    else:
        # 清除全部
        _memory_cache.clear()
    
    logger.info(f"[MemoryManager] 清除缓存: thread={thread_id}")
