"""
长期记忆系统 - 用户偏好与历史持久化

管理用户的稳定偏好和历史记录：
1. 用户偏好（简历风格、目标职位等）
2. 会话历史摘要
3. 行为模式（常用操作、偏好技能等）
4. 知识积累（行业洞察、面试经验）

特点：
- 生命周期：永久（随用户使用累积）
- 存储位置：数据库
- 检索方式：关键词搜索 + 语义搜索（Phase 3.5）
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from .models import UserPreference, ConversationSession, AgentCheckpoint

logger = logging.getLogger(__name__)


class LongTermMemory:
    """
    长期记忆管理器
    
    类比人类的长时记忆：
    - 容量几乎无限
    - 需要"提取线索"才能回忆
    - 会随时间衰减（需要复习强化）
    
    在 Agent 中：
    - 存储用户明确设置的偏好
    - 从行为中推断的偏好
    - 历史会话的压缩摘要
    """
    
    def __init__(self, user_id: str, db_session: Optional[Session] = None):
        self.user_id = user_id
        self.db = db_session
        
        # 内存缓存（减少数据库查询）
        self._preference_cache: Dict[str, Any] = {}
        self._cache_loaded = False
        
        logger.info(f"[LongTermMemory] 初始化: user={user_id}")
    
    # ========== 偏好管理 ==========
    
    def save_preference(
        self,
        preference_type: str,
        preference_key: str,
        preference_value: Any,
        confidence: int = 50,
        source: str = "explicit"
    ) -> bool:
        """
        保存用户偏好
        
        Args:
            preference_type: 偏好类型（resume_style, target_role 等）
            preference_key: 偏好键（primary, secondary 等）
            preference_value: 偏好值（任意 JSON 可序列化类型）
            confidence: 置信度 0-100
            source: 来源（explicit 用户明确设置 / inferred 系统推断）
        
        Returns:
            是否保存成功
        """
        if not self.db:
            logger.warning("[LongTermMemory] 无数据库会话，偏好仅缓存")
            self._preference_cache[f"{preference_type}:{preference_key}"] = preference_value
            return False
        
        try:
            # 查找是否已存在
            existing = self.db.query(UserPreference).filter(
                UserPreference.user_id == self.user_id,
                UserPreference.preference_type == preference_type,
                UserPreference.preference_key == preference_key
            ).first()
            
            value_json = json.dumps(preference_value, ensure_ascii=False)
            
            if existing:
                # 更新现有偏好
                existing.preference_value = value_json
                existing.confidence = confidence
                existing.source = source
                existing.updated_at = datetime.utcnow()
                logger.info(
                    f"[LongTermMemory] 更新偏好: "
                    f"type={preference_type}, key={preference_key}"
                )
            else:
                # 创建新偏好
                preference = UserPreference(
                    user_id=self.user_id,
                    preference_type=preference_type,
                    preference_key=preference_key,
                    preference_value=value_json,
                    confidence=confidence,
                    source=source
                )
                self.db.add(preference)
                logger.info(
                    f"[LongTermMemory] 创建偏好: "
                    f"type={preference_type}, key={preference_key}"
                )
            
            self.db.commit()
            
            # 更新缓存
            self._preference_cache[f"{preference_type}:{preference_key}"] = preference_value
            
            return True
            
        except Exception as e:
            logger.error(f"[LongTermMemory] 保存偏好失败: {e}")
            self.db.rollback()
            return False
    
    def get_preference(
        self,
        preference_type: str,
        preference_key: str = "primary",
        default: Any = None
    ) -> Any:
        """
        获取用户偏好
        
        Args:
            preference_type: 偏好类型
            preference_key: 偏好键
            default: 默认值
        
        Returns:
            偏好值或默认值
        """
        cache_key = f"{preference_type}:{preference_key}"
        
        # 先查缓存
        if cache_key in self._preference_cache:
            return self._preference_cache[cache_key]
        
        # 再查数据库
        if self.db:
            try:
                preference = self.db.query(UserPreference).filter(
                    UserPreference.user_id == self.user_id,
                    UserPreference.preference_type == preference_type,
                    UserPreference.preference_key == preference_key
                ).first()
                
                if preference:
                    value = json.loads(preference.preference_value)
                    self._preference_cache[cache_key] = value
                    return value
                    
            except Exception as e:
                logger.error(f"[LongTermMemory] 查询偏好失败: {e}")
        
        return default
    
    def get_preferences_by_type(self, preference_type: str) -> Dict[str, Any]:
        """
        获取某类型的所有偏好
        
        Args:
            preference_type: 偏好类型
        
        Returns:
            {preference_key: preference_value}
        """
        result = {}
        
        if not self.db:
            return result
        
        try:
            preferences = self.db.query(UserPreference).filter(
                UserPreference.user_id == self.user_id,
                UserPreference.preference_type == preference_type
            ).all()
            
            for pref in preferences:
                try:
                    result[pref.preference_key] = json.loads(pref.preference_value)
                except json.JSONDecodeError:
                    result[pref.preference_key] = pref.preference_value
                    
        except Exception as e:
            logger.error(f"[LongTermMemory] 查询偏好列表失败: {e}")
        
        return result
    
    def get_all_preferences(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有偏好
        
        Returns:
            {preference_type: {preference_key: preference_value}}
        """
        result = {}
        
        if not self.db:
            return result
        
        try:
            preferences = self.db.query(UserPreference).filter(
                UserPreference.user_id == self.user_id
            ).all()
            
            for pref in preferences:
                if pref.preference_type not in result:
                    result[pref.preference_type] = {}
                
                try:
                    result[pref.preference_type][pref.preference_key] = json.loads(pref.preference_value)
                except json.JSONDecodeError:
                    result[pref.preference_type][pref.preference_key] = pref.preference_value
                    
        except Exception as e:
            logger.error(f"[LongTermMemory] 查询所有偏好失败: {e}")
        
        return result
    
    def delete_preference(self, preference_type: str, preference_key: str = "primary") -> bool:
        """删除偏好"""
        if not self.db:
            return False
        
        try:
            self.db.query(UserPreference).filter(
                UserPreference.user_id == self.user_id,
                UserPreference.preference_type == preference_type,
                UserPreference.preference_key == preference_key
            ).delete()
            self.db.commit()
            
            # 清除缓存
            cache_key = f"{preference_type}:{preference_key}"
            self._preference_cache.pop(cache_key, None)
            
            return True
            
        except Exception as e:
            logger.error(f"[LongTermMemory] 删除偏好失败: {e}")
            self.db.rollback()
            return False
    
    # ========== 会话历史管理 ==========
    
    def save_session(self, session_data: Dict[str, Any]) -> bool:
        """
        保存会话到长期记忆
        
        将短期记忆的会话归档到数据库
        """
        if not self.db:
            return False
        
        try:
            # 查找是否已存在
            existing = self.db.query(ConversationSession).filter(
                ConversationSession.thread_id == session_data["thread_id"]
            ).first()
            
            if existing:
                # 更新
                existing.messages = session_data.get("messages", "[]")
                existing.message_count = session_data.get("message_count", 0)
                existing.status = session_data.get("status", "completed")
                existing.updated_at = datetime.utcnow()
            else:
                # 创建
                session = ConversationSession(
                    thread_id=session_data["thread_id"],
                    user_id=self.user_id,
                    session_type=session_data.get("session_type", "resume_tailor"),
                    title=session_data.get("title", ""),
                    related_job_id=session_data.get("related_job_id"),
                    messages=session_data.get("messages", "[]"),
                    message_count=session_data.get("message_count", 0),
                    status=session_data.get("status", "completed"),
                )
                self.db.add(session)
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"[LongTermMemory] 保存会话失败: {e}")
            self.db.rollback()
            return False
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的会话列表
        
        Args:
            limit: 返回数量
        
        Returns:
            会话列表（不含详细消息）
        """
        if not self.db:
            return []
        
        try:
            sessions = self.db.query(ConversationSession).filter(
                ConversationSession.user_id == self.user_id
            ).order_by(desc(ConversationSession.updated_at)).limit(limit).all()
            
            return [
                {
                    "thread_id": s.thread_id,
                    "session_type": s.session_type,
                    "title": s.title,
                    "message_count": s.message_count,
                    "status": s.status,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                }
                for s in sessions
            ]
            
        except Exception as e:
            logger.error(f"[LongTermMemory] 查询会话失败: {e}")
            return []
    
    def get_session(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取单个会话详情"""
        if not self.db:
            return None
        
        try:
            session = self.db.query(ConversationSession).filter(
                ConversationSession.thread_id == thread_id,
                ConversationSession.user_id == self.user_id
            ).first()
            
            if session:
                return session.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"[LongTermMemory] 查询会话详情失败: {e}")
            return None
    
    # ========== 检查点管理 ==========
    
    def save_checkpoint(self, checkpoint_data: Dict[str, Any]) -> bool:
        """保存 Agent 检查点"""
        if not self.db:
            return False
        
        try:
            checkpoint = AgentCheckpoint(
                thread_id=checkpoint_data["thread_id"],
                user_id=self.user_id,
                checkpoint_type=checkpoint_data.get("checkpoint_type", "resume_workflow"),
                step_name=checkpoint_data["step_name"],
                step_number=checkpoint_data.get("step_number", 0),
                state_data=json.dumps(checkpoint_data.get("state", {}), ensure_ascii=False, default=str),
                status=checkpoint_data.get("status", "running"),
                error_message=checkpoint_data.get("error_message"),
                retry_count=checkpoint_data.get("retry_count", 0),
                metadata_json=json.dumps(checkpoint_data.get("metadata", {}), ensure_ascii=False) if checkpoint_data.get("metadata") else None,
            )
            self.db.add(checkpoint)
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"[LongTermMemory] 保存检查点失败: {e}")
            self.db.rollback()
            return False
    
    def get_latest_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取最新的检查点"""
        if not self.db:
            return None
        
        try:
            checkpoint = self.db.query(AgentCheckpoint).filter(
                AgentCheckpoint.thread_id == thread_id,
                AgentCheckpoint.user_id == self.user_id
            ).order_by(desc(AgentCheckpoint.created_at)).first()
            
            if checkpoint:
                return checkpoint.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"[LongTermMemory] 查询检查点失败: {e}")
            return None
    
    # ========== 用户画像构建 ==========
    
    def build_user_profile(self) -> Dict[str, Any]:
        """
        构建用户画像
        
        综合所有长期记忆信息，生成用户画像：
        - 技能偏好
        - 目标职位
        - 行为模式
        - 活跃时段
        """
        profile = {
            "user_id": self.user_id,
            "preferences": self.get_all_preferences(),
            "recent_sessions": self.get_recent_sessions(limit=5),
        }
        
        # 统计信息
        if self.db:
            try:
                # 总会话数
                total_sessions = self.db.query(ConversationSession).filter(
                    ConversationSession.user_id == self.user_id
                ).count()
                profile["total_sessions"] = total_sessions
                
                # 总消息数
                total_messages = self.db.query(func.sum(ConversationSession.message_count)).filter(
                    ConversationSession.user_id == self.user_id
                ).scalar() or 0
                profile["total_messages"] = int(total_messages)
                
                # 最活跃的会话类型
                session_types = self.db.query(
                    ConversationSession.session_type,
                    func.count(ConversationSession.id).label("count")
                ).filter(
                    ConversationSession.user_id == self.user_id
                ).group_by(ConversationSession.session_type).all()
                
                profile["session_type_distribution"] = {
                    st.session_type: st.count for st in session_types
                }
                
            except Exception as e:
                logger.error(f"[LongTermMemory] 构建用户画像失败: {e}")
        
        return profile
    
    def __repr__(self):
        return f"<LongTermMemory(user={self.user_id}, cache_keys={list(self._preference_cache.keys())})>"
