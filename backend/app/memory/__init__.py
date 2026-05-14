"""
Career Co-Pilot 记忆系统

提供 Agent 的多层记忆能力：
- 短期记忆: 当前对话上下文（ConversationBufferMemory）
- 工作记忆: 当前任务状态（LangGraph State）
- 长期记忆: 用户偏好、历史记录（数据库存储）

使用方式:
    from app.memory import get_memory_manager
    
    memory = get_memory_manager(user_id="user_123")
    
    # 短期记忆 - 保存对话
    memory.save_short_term("user", "我想找 Python 后端工作")
    memory.save_short_term("assistant", "好的，我来帮您分析...")
    
    # 长期记忆 - 保存偏好
    memory.save_preference("resume_style", "technical")
    memory.save_preference("target_role", "高级后端工程师")
    
    # 检索相关历史
    related = memory.search_long_term("Python 后端经验", top_k=3)
"""

from .manager import MemoryManager, get_memory_manager
from .short_term import ShortTermMemory
from .long_term import LongTermMemory
from .models import UserPreference, ConversationSession, AgentCheckpoint

__all__ = [
    "MemoryManager",
    "get_memory_manager",
    "ShortTermMemory",
    "LongTermMemory",
    "UserPreference",
    "ConversationSession",
    "AgentCheckpoint",
]
