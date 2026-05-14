"""
记忆系统测试

验证三层记忆的核心能力：
1. 短期记忆: 对话历史、工作记忆、Token 管理
2. 长期记忆: 偏好持久化、会话归档、检查点
3. 记忆管理器: 统一接口、缓存、恢复

运行: pytest backend/evaluation/test_memory_system.py -v
"""

import pytest
import json
import time
from datetime import datetime
from typing import Dict, Any

import sys
sys.path.insert(0, "e:\\Desktop\\AI Career Co-pilot\\backend")

from app.memory.short_term import ShortTermMemory
from app.memory.long_term import LongTermMemory
from app.memory.manager import MemoryManager, get_memory_manager, clear_memory_cache
from app.memory.checkpointer import DatabaseCheckpointer, create_checkpointer


# ========== 测试数据 ==========

SAMPLE_USER_ID = "test_user_123"
SAMPLE_THREAD_ID = "test_thread_456"


# ========== 短期记忆测试 ==========

class TestShortTermMemory:
    """测试短期记忆"""
    
    def test_create_memory(self):
        """测试创建短期记忆"""
        memory = ShortTermMemory(
            thread_id=SAMPLE_THREAD_ID,
            user_id=SAMPLE_USER_ID
        )
        
        assert memory.thread_id == SAMPLE_THREAD_ID
        assert memory.user_id == SAMPLE_USER_ID
        assert len(memory.get_messages()) == 0
    
    def test_add_message(self):
        """测试添加消息"""
        memory = ShortTermMemory(
            thread_id=SAMPLE_THREAD_ID,
            user_id=SAMPLE_USER_ID
        )
        
        memory.add_message("user", "你好")
        memory.add_message("assistant", "你好！有什么可以帮您？")
        
        messages = memory.get_messages()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "你好"
        assert messages[1]["role"] == "assistant"
    
    def test_message_limit(self):
        """测试消息数量限制"""
        memory = ShortTermMemory(
            thread_id=SAMPLE_THREAD_ID,
            user_id=SAMPLE_USER_ID,
            max_messages=3
        )
        
        # 添加超过限制的消息
        for i in range(5):
            memory.add_message("user", f"消息 {i}")
        
        messages = memory.get_messages()
        assert len(messages) == 3  # 只保留最近 3 条
        assert messages[0]["content"] == "消息 2"
        assert messages[-1]["content"] == "消息 4"
    
    def test_working_memory(self):
        """测试工作记忆"""
        memory = ShortTermMemory(
            thread_id=SAMPLE_THREAD_ID,
            user_id=SAMPLE_USER_ID
        )
        
        # 设置工作记忆
        memory.set_working_memory("current_jd", "Python 后端工程师")
        memory.set_working_memory("extracted_skills", ["Python", "FastAPI"])
        
        # 获取
        assert memory.get_working_memory("current_jd") == "Python 后端工程师"
        assert memory.get_working_memory("extracted_skills") == ["Python", "FastAPI"]
        assert memory.get_working_memory("nonexistent", "default") == "default"
        
        # 获取全部
        all_working = memory.get_all_working_memory()
        assert "current_jd" in all_working
        assert "extracted_skills" in all_working
    
    def test_cache(self):
        """测试缓存"""
        memory = ShortTermMemory(
            thread_id=SAMPLE_THREAD_ID,
            user_id=SAMPLE_USER_ID
        )
        
        # 设置缓存
        memory.set_cache("vault_data", {"skills": ["Python"]})
        
        # 获取
        cached = memory.get_cache("vault_data")
        assert cached == {"skills": ["Python"]}
        
        # 获取不存在的
        assert memory.get_cache("nonexistent") is None
    
    def test_clear(self):
        """测试清空"""
        memory = ShortTermMemory(
            thread_id=SAMPLE_THREAD_ID,
            user_id=SAMPLE_USER_ID
        )
        
        memory.add_message("user", "测试")
        memory.set_working_memory("key", "value")
        memory.set_cache("key", "value")
        
        # 清空消息
        memory.clear_messages()
        assert len(memory.get_messages()) == 0
        
        # 清空工作记忆
        memory.clear_working_memory()
        assert len(memory.get_all_working_memory()) == 0
        
        # 清空缓存
        memory.clear_cache()
        assert memory.get_cache("key") is None
    
    def test_generate_summary(self):
        """测试生成摘要"""
        memory = ShortTermMemory(
            thread_id=SAMPLE_THREAD_ID,
            user_id=SAMPLE_USER_ID
        )
        
        # 空会话
        assert "空会话" in memory.generate_summary()
        
        # 有消息
        memory.add_message("user", "帮我定制简历")
        memory.add_message("assistant", "好的")
        
        summary = memory.generate_summary()
        assert "2 条消息" in summary
        assert "用户提问 1 次" in summary
    
    def test_token_estimation(self):
        """测试 Token 估算"""
        memory = ShortTermMemory(
            thread_id=SAMPLE_THREAD_ID,
            user_id=SAMPLE_USER_ID
        )
        
        # 中文 Token 估算
        tokens = memory._estimate_tokens("你好世界")
        assert tokens > 0
        
        # 英文 Token 估算
        tokens_en = memory._estimate_tokens("Hello World")
        assert tokens_en > 0
        
        # 空字符串
        assert memory._estimate_tokens("") == 0
        assert memory._estimate_tokens(None) == 0
    
    def test_messages_for_llm(self):
        """测试获取 LLM 消息格式"""
        memory = ShortTermMemory(
            thread_id=SAMPLE_THREAD_ID,
            user_id=SAMPLE_USER_ID
        )
        
        memory.add_message("user", "问题 1")
        memory.add_message("assistant", "回答 1")
        
        # 带系统提示
        messages = memory.get_messages_for_llm(system_prompt="你是一个助手")
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "你是一个助手"
        assert messages[1]["role"] == "user"
        
        # 不带系统提示
        messages_no_system = memory.get_messages_for_llm()
        assert messages_no_system[0]["role"] == "user"
    
    def test_serialization(self):
        """测试序列化"""
        memory = ShortTermMemory(
            thread_id=SAMPLE_THREAD_ID,
            user_id=SAMPLE_USER_ID
        )
        
        memory.add_message("user", "测试")
        memory.set_working_memory("key", "value")
        
        # 序列化
        data = memory.to_dict()
        assert data["thread_id"] == SAMPLE_THREAD_ID
        assert data["user_id"] == SAMPLE_USER_ID
        assert len(data["messages"]) == 1
        assert data["working_memory"]["key"] == "value"
        
        # 数据库格式
        db_data = memory.to_db_format()
        assert db_data["thread_id"] == SAMPLE_THREAD_ID
        assert db_data["message_count"] == 1
        assert json.loads(db_data["messages"])[0]["content"] == "测试"


# ========== 长期记忆测试 ==========

class TestLongTermMemory:
    """测试长期记忆（无数据库）"""
    
    def test_create_memory(self):
        """测试创建长期记忆"""
        memory = LongTermMemory(user_id=SAMPLE_USER_ID)
        
        assert memory.user_id == SAMPLE_USER_ID
        assert memory.db is None
    
    def test_preference_cache(self):
        """测试偏好缓存（无数据库）"""
        memory = LongTermMemory(user_id=SAMPLE_USER_ID)
        
        # 保存偏好（仅缓存）
        memory.save_preference(
            preference_type="resume_style",
            preference_key="primary",
            preference_value="technical"
        )
        
        # 从缓存读取
        pref = memory.get_preference("resume_style", "primary")
        assert pref == "technical"
        
        # 读取不存在的
        assert memory.get_preference("nonexistent", "primary", "default") == "default"
    
    def test_build_profile_no_db(self):
        """测试构建画像（无数据库）"""
        memory = LongTermMemory(user_id=SAMPLE_USER_ID)
        
        profile = memory.build_user_profile()
        assert profile["user_id"] == SAMPLE_USER_ID
        assert profile["preferences"] == {}
        assert profile["recent_sessions"] == []


# ========== 记忆管理器测试 ==========

class TestMemoryManager:
    """测试记忆管理器"""
    
    def test_create_manager(self):
        """测试创建管理器"""
        manager = MemoryManager(
            user_id=SAMPLE_USER_ID,
            thread_id=SAMPLE_THREAD_ID
        )
        
        assert manager.user_id == SAMPLE_USER_ID
        assert manager.thread_id == SAMPLE_THREAD_ID
        assert manager.short_term is not None
        assert manager.long_term is not None
    
    def test_save_and_get_message(self):
        """测试保存和获取消息"""
        manager = MemoryManager(
            user_id=SAMPLE_USER_ID,
            thread_id="thread_msg_test"
        )
        
        manager.save_message("user", "你好")
        manager.save_message("assistant", "你好！")
        
        messages = manager.get_messages()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
    
    def test_working_memory(self):
        """测试工作记忆"""
        manager = MemoryManager(
            user_id=SAMPLE_USER_ID,
            thread_id="thread_work_test"
        )
        
        manager.set_working_memory("jd_text", "Python 工程师")
        assert manager.get_working_memory("jd_text") == "Python 工程师"
        assert manager.get_working_memory("nonexistent", "default") == "default"
    
    def test_user_preference_cache(self):
        """测试用户偏好缓存"""
        manager = MemoryManager(
            user_id=SAMPLE_USER_ID,
            thread_id="thread_pref_test"
        )
        
        # 保存偏好
        manager.save_user_preference("resume_style", "technical")
        
        # 获取偏好
        pref = manager.get_user_preference("resume_style")
        assert pref == "technical"
        
        # 获取不存在的
        assert manager.get_user_preference("nonexistent", default="default") == "default"
    
    def test_preferences_summary(self):
        """测试偏好摘要"""
        manager = MemoryManager(
            user_id=SAMPLE_USER_ID,
            thread_id="thread_summary_test"
        )
        
        # 空偏好
        assert manager.get_user_preferences_summary() == ""
        
        # 有偏好
        manager.save_user_preference("resume_style", "technical")
        summary = manager.get_user_preferences_summary()
        assert "resume_style" in summary
        assert "technical" in summary
    
    def test_archive_session_no_db(self):
        """测试归档（无数据库）"""
        manager = MemoryManager(
            user_id=SAMPLE_USER_ID,
            thread_id="thread_archive_test"
        )
        
        manager.save_message("user", "测试")
        
        # 无数据库时应返回 False
        result = manager.archive_session()
        assert result is False
    
    def test_checkpoint_no_db(self):
        """测试检查点（无数据库）"""
        manager = MemoryManager(
            user_id=SAMPLE_USER_ID,
            thread_id="thread_cp_test"
        )
        
        # 无数据库时应返回 False
        result = manager.save_checkpoint("step_1", {"data": "test"})
        assert result is False
        
        # 获取应为 None
        assert manager.get_latest_checkpoint() is None


# ========== 工厂函数测试 ==========

class TestMemoryFactory:
    """测试工厂函数"""
    
    def test_get_memory_manager(self):
        """测试获取管理器"""
        clear_memory_cache()
        
        manager1 = get_memory_manager(
            user_id=SAMPLE_USER_ID,
            thread_id="factory_test"
        )
        
        manager2 = get_memory_manager(
            user_id=SAMPLE_USER_ID,
            thread_id="factory_test"
        )
        
        # 应该是同一个实例
        assert manager1 is manager2
    
    def test_clear_cache(self):
        """测试清除缓存"""
        clear_memory_cache()
        
        # 创建实例
        manager1 = get_memory_manager(
            user_id=SAMPLE_USER_ID,
            thread_id="clear_test"
        )
        
        # 清除特定线程
        clear_memory_cache("clear_test")
        
        # 再次获取应该是新实例
        manager2 = get_memory_manager(
            user_id=SAMPLE_USER_ID,
            thread_id="clear_test"
        )
        
        assert manager1 is not manager2
    
    def test_clear_all_cache(self):
        """测试清除所有缓存"""
        clear_memory_cache()
        
        get_memory_manager(
            user_id=SAMPLE_USER_ID,
            thread_id="clear_all_1"
        )
        get_memory_manager(
            user_id=SAMPLE_USER_ID,
            thread_id="clear_all_2"
        )
        
        # 清除全部
        clear_memory_cache()
        
        # 应该创建新实例
        manager = get_memory_manager(
            user_id=SAMPLE_USER_ID,
            thread_id="clear_all_1"
        )
        assert manager is not None


# ========== Checkpointer 测试 ==========

class TestCheckpointer:
    """测试检查点"""
    
    def test_create_checkpointer(self):
        """测试创建检查点"""
        cp = create_checkpointer()
        assert cp is not None
        assert cp.db is None
    
    def test_save_checkpoint_no_db(self):
        """测试保存检查点（无数据库）"""
        cp = create_checkpointer()
        
        result = cp.save_checkpoint(
            thread_id="test",
            user_id="user",
            step_name="step_1",
            state={"data": "test"}
        )
        
        assert result is False
    
    def test_load_checkpoint_no_db(self):
        """测试加载检查点（无数据库）"""
        cp = create_checkpointer()
        
        result = cp.load_checkpoint("test")
        assert result is None


# ========== 集成测试 ==========

class TestMemoryIntegration:
    """记忆系统集成测试"""
    
    def test_full_conversation_flow(self):
        """测试完整对话流程"""
        clear_memory_cache()
        
        manager = get_memory_manager(
            user_id=SAMPLE_USER_ID,
            thread_id="integration_test"
        )
        
        # 模拟对话
        manager.save_message("user", "我想找 Python 工作")
        manager.save_message("assistant", "好的，我来帮您分析")
        manager.save_message("user", "这是我的简历")
        
        # 设置工作记忆
        manager.set_working_memory("current_task", "resume_tailor")
        
        # 保存偏好
        manager.save_user_preference("target_role", "Python 后端工程师")
        
        # 验证
        assert len(manager.get_messages()) == 3
        assert manager.get_working_memory("current_task") == "resume_tailor"
        assert manager.get_user_preference("target_role") == "Python 后端工程师"
        
        # 获取 LLM 上下文
        context = manager.get_context_for_llm(
            system_prompt="你是一个求职助手"
        )
        assert len(context) > 0
        assert context[0]["role"] == "system"
    
    def test_memory_isolation(self):
        """测试记忆隔离"""
        clear_memory_cache()
        
        # 用户 A
        manager_a = get_memory_manager(
            user_id="user_a",
            thread_id="isolation_test"
        )
        manager_a.save_user_preference("resume_style", "technical")
        
        # 用户 B
        manager_b = get_memory_manager(
            user_id="user_b",
            thread_id="isolation_test"
        )
        
        # 用户 B 不应该看到用户 A 的偏好
        assert manager_b.get_user_preference("resume_style") is None


# ========== 性能测试 ==========

class TestMemoryPerformance:
    """记忆系统性能测试"""
    
    def test_message_add_latency(self):
        """测试消息添加延迟"""
        memory = ShortTermMemory(
            thread_id="perf_test",
            user_id=SAMPLE_USER_ID
        )
        
        start = time.time()
        for i in range(100):
            memory.add_message("user", f"消息 {i}")
        elapsed = time.time() - start
        
        # 100 条消息应该在 100ms 内
        assert elapsed < 0.1, f"消息添加太慢: {elapsed:.3f}s"
    
    def test_token_estimation_performance(self):
        """测试 Token 估算性能"""
        memory = ShortTermMemory(
            thread_id="perf_test",
            user_id=SAMPLE_USER_ID
        )
        
        long_text = "这是一个测试文本 " * 1000  # 约 1 万字
        
        start = time.time()
        tokens = memory._estimate_tokens(long_text)
        elapsed = time.time() - start
        
        # 应该在 10ms 内
        assert elapsed < 0.01, f"Token 估算太慢: {elapsed:.3f}s"
        assert tokens > 0


# ========== 主入口 ==========

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
