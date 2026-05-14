"""
LangGraph Checkpointer 集成

提供工作流状态的持久化和恢复能力：
1. 保存工作流中间状态
2. 支持中断后恢复
3. 记录执行历史

与 LangGraph 的 checkpointer 接口兼容。
"""

import json
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from .models import AgentCheckpoint

logger = logging.getLogger(__name__)


class DatabaseCheckpointer:
    """
    数据库检查点实现
    
    将 LangGraph 工作流状态持久化到数据库：
    - 每个步骤完成后自动保存
    - 支持按 thread_id 恢复
    - 记录执行历史
    
    使用方式:
        checkpointer = DatabaseCheckpointer(db_session)
        
        # 保存状态
        checkpointer.save_checkpoint(
            thread_id="thread_123",
            step="analyze_jd",
            state={"jd_analysis": "...", "current_step": "analyze_jd"}
        )
        
        # 恢复状态
        state = checkpointer.load_checkpoint("thread_123")
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        self.db = db_session
    
    def save_checkpoint(
        self,
        thread_id: str,
        user_id: str,
        step_name: str,
        state: Dict[str, Any],
        checkpoint_type: str = "resume_workflow",
        status: str = "running",
        error_message: Optional[str] = None,
        retry_count: int = 0,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        保存检查点
        
        Args:
            thread_id: 线程 ID
            user_id: 用户 ID
            step_name: 当前步骤名称
            state: 工作流状态（会被 JSON 序列化）
            checkpoint_type: 检查点类型
            status: 状态（running/completed/failed/retrying）
            error_message: 错误信息
            retry_count: 重试次数
            metadata: 额外元数据
        
        Returns:
            是否保存成功
        """
        if not self.db:
            logger.warning("[Checkpointer] 无数据库会话，跳过保存")
            return False
        
        try:
            # 获取当前步骤序号
            step_number = self._get_next_step_number(thread_id)
            
            checkpoint = AgentCheckpoint(
                thread_id=thread_id,
                user_id=user_id,
                checkpoint_type=checkpoint_type,
                step_name=step_name,
                step_number=step_number,
                state_data=json.dumps(state, ensure_ascii=False, default=str),
                status=status,
                error_message=error_message,
                retry_count=retry_count,
                metadata_json=json.dumps(metadata, ensure_ascii=False) if metadata else None,
            )
            
            self.db.add(checkpoint)
            self.db.commit()
            
            logger.debug(
                f"[Checkpointer] 保存检查点: thread={thread_id}, "
                f"step={step_name}, number={step_number}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"[Checkpointer] 保存检查点失败: {e}")
            if self.db:
                self.db.rollback()
            return False
    
    def load_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        加载最新检查点
        
        Args:
            thread_id: 线程 ID
        
        Returns:
            状态字典，或 None（如果没有检查点）
        """
        if not self.db:
            return None
        
        try:
            checkpoint = self.db.query(AgentCheckpoint).filter(
                AgentCheckpoint.thread_id == thread_id
            ).order_by(AgentCheckpoint.created_at.desc()).first()
            
            if checkpoint:
                state = checkpoint.get_state()
                logger.info(
                    f"[Checkpointer] 恢复检查点: thread={thread_id}, "
                    f"step={checkpoint.step_name}"
                )
                return state
            
            return None
            
        except Exception as e:
            logger.error(f"[Checkpointer] 加载检查点失败: {e}")
            return None
    
    def get_checkpoint_history(
        self,
        thread_id: str,
        limit: int = 10
    ) -> list:
        """
        获取检查点历史
        
        Args:
            thread_id: 线程 ID
            limit: 返回数量
        
        Returns:
            检查点列表
        """
        if not self.db:
            return []
        
        try:
            checkpoints = self.db.query(AgentCheckpoint).filter(
                AgentCheckpoint.thread_id == thread_id
            ).order_by(AgentCheckpoint.created_at.desc()).limit(limit).all()
            
            return [cp.to_dict() for cp in checkpoints]
            
        except Exception as e:
            logger.error(f"[Checkpointer] 查询历史失败: {e}")
            return []
    
    def delete_checkpoints(self, thread_id: str) -> bool:
        """
        删除检查点
        
        用于清理已完成的工作流
        """
        if not self.db:
            return False
        
        try:
            self.db.query(AgentCheckpoint).filter(
                AgentCheckpoint.thread_id == thread_id
            ).delete()
            self.db.commit()
            
            logger.info(f"[Checkpointer] 删除检查点: thread={thread_id}")
            return True
            
        except Exception as e:
            logger.error(f"[Checkpointer] 删除检查点失败: {e}")
            if self.db:
                self.db.rollback()
            return False
    
    def _get_next_step_number(self, thread_id: str) -> int:
        """获取下一个步骤序号"""
        if not self.db:
            return 0
        
        try:
            latest = self.db.query(AgentCheckpoint).filter(
                AgentCheckpoint.thread_id == thread_id
            ).order_by(AgentCheckpoint.step_number.desc()).first()
            
            if latest:
                return latest.step_number + 1
            return 0
            
        except Exception:
            return 0


def create_checkpointer(db_session: Optional[Session] = None) -> DatabaseCheckpointer:
    """
    创建检查点实例的工厂函数
    
    Args:
        db_session: 数据库会话
    
    Returns:
        DatabaseCheckpointer 实例
    """
    return DatabaseCheckpointer(db_session)
