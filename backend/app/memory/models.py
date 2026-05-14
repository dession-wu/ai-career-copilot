"""
记忆系统数据库模型

定义记忆持久化所需的数据表：
- UserPreference: 用户偏好设置
- ConversationSession: 对话会话历史
- AgentCheckpoint: Agent 状态检查点
"""

import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base


class UserPreference(Base):
    """
    用户偏好表 - 长期记忆的核心
    
    存储用户的稳定偏好和画像信息：
    - 简历风格偏好（technical/professional/concise）
    - 目标职位类型
    - 常用技能标签
    - 行业偏好
    - 薪资期望
    
    这些偏好会在多次对话中累积和更新。
    """
    __tablename__ = "user_preferences"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 偏好类别和键值
    preference_type = Column(String(50), nullable=False)  # e.g., "resume_style", "target_role"
    preference_key = Column(String(100), nullable=False)   # e.g., "primary", "secondary"
    preference_value = Column(Text, nullable=False)        # JSON 字符串存储
    
    # 元数据
    confidence = Column(Integer, default=50)  # 置信度 0-100，基于出现频率
    source = Column(String(50), default="explicit")  # explicit(用户明确设置) / inferred(推断)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 复合索引：用户 + 偏好类型
    __table_args__ = (
        Index('idx_user_pref_type', 'user_id', 'preference_type'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "preference_type": self.preference_type,
            "preference_key": self.preference_key,
            "preference_value": json.loads(self.preference_value) if self.preference_value else None,
            "confidence": self.confidence,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<UserPreference(user={self.user_id}, type={self.preference_type}, key={self.preference_key})>"


class ConversationSession(Base):
    """
    对话会话表 - 短期记忆的持久化
    
    存储用户与 Agent 的完整对话历史：
    - 支持多会话（每个会话有唯一 thread_id）
    - 消息按顺序存储
    - 支持会话元数据（如关联的职位 ID）
    
    用于：
    1. 恢复对话上下文
    2. 分析用户行为模式
    3. 生成对话摘要
    """
    __tablename__ = "conversation_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 会话信息
    session_type = Column(String(50), default="resume_tailor")  # resume_tailor, interview_prep, career_advice
    title = Column(String(255), default="")  # 会话标题（可自动生成）
    
    # 关联数据
    related_job_id = Column(String(36), nullable=True)  # 关联的职位申请 ID
    related_vault_id = Column(String(36), nullable=True)  # 关联的 Vault ID
    
    # 消息历史（JSON 数组存储）
    messages = Column(Text, default="[]")  # [{"role": "user", "content": "...", "timestamp": "..."}, ...]
    
    # 会话状态
    status = Column(String(20), default="active")  # active, paused, completed, archived
    message_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    # 索引
    __table_args__ = (
        Index('idx_user_sessions', 'user_id', 'created_at'),
        Index('idx_session_status', 'status', 'updated_at'),
    )
    
    def get_messages(self) -> list:
        """获取消息列表"""
        try:
            return json.loads(self.messages) if self.messages else []
        except json.JSONDecodeError:
            return []
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """添加消息"""
        messages = self.get_messages()
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if metadata:
            message["metadata"] = metadata
        messages.append(message)
        self.messages = json.dumps(messages, ensure_ascii=False)
        self.message_count = len(messages)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "user_id": self.user_id,
            "session_type": self.session_type,
            "title": self.title,
            "related_job_id": self.related_job_id,
            "status": self.status,
            "message_count": self.message_count,
            "messages": self.get_messages(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<ConversationSession(thread={self.thread_id}, messages={self.message_count})>"


class AgentCheckpoint(Base):
    """
    Agent 状态检查点表 - 工作流的持久化
    
    存储 LangGraph 工作流的中间状态：
    - 允许中断后恢复
    - 支持重试和调试
    - 记录执行历史
    
    对应 LangGraph 的 Checkpointer 接口。
    """
    __tablename__ = "agent_checkpoints"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 检查点信息
    checkpoint_type = Column(String(50), default="resume_workflow")  # 工作流类型
    step_name = Column(String(100), nullable=False)  # 当前步骤名称
    step_number = Column(Integer, default=0)  # 步骤序号
    
    # 状态数据（JSON 存储）
    state_data = Column(Text, default="{}")  # 工作流状态的 JSON 序列化
    
    # 执行信息
    status = Column(String(20), default="running")  # running, completed, failed, retrying
    error_message = Column(Text, nullable=True)  # 错误信息
    retry_count = Column(Integer, default=0)  # 重试次数
    
    # 元数据
    metadata_json = Column(Text, nullable=True)  # 额外元数据
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 索引
    __table_args__ = (
        Index('idx_checkpoint_thread', 'thread_id', 'step_number'),
        Index('idx_checkpoint_user', 'user_id', 'checkpoint_type'),
    )
    
    def get_state(self) -> Dict[str, Any]:
        """获取状态数据"""
        try:
            return json.loads(self.state_data) if self.state_data else {}
        except json.JSONDecodeError:
            return {}
    
    def set_state(self, state: Dict[str, Any]):
        """设置状态数据"""
        self.state_data = json.dumps(state, ensure_ascii=False, default=str)
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取元数据"""
        try:
            return json.loads(self.metadata_json) if self.metadata_json else {}
        except json.JSONDecodeError:
            return {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "user_id": self.user_id,
            "checkpoint_type": self.checkpoint_type,
            "step_name": self.step_name,
            "step_number": self.step_number,
            "state": self.get_state(),
            "status": self.status,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "metadata": self.get_metadata(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<AgentCheckpoint(thread={self.thread_id}, step={self.step_name}, status={self.status})>"
