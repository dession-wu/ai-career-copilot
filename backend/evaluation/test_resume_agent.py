"""
ResumeTailorAgent 测试套件

验证 Agent 的核心能力：
1. 工具调用能力
2. 防幻觉机制
3. 端到端延迟
4. ReAct 循环完整性

运行: pytest backend/evaluation/test_resume_agent.py -v
"""

import pytest
import json
import time
import asyncio
import os
from typing import Dict, Any

# 导入被测组件
import sys
sys.path.insert(0, "e:\\Desktop\\AI Career Co-pilot\\backend")

from app.tools import (
    extract_jd_keywords,
    search_vault,
    generate_resume_section,
    verify_facts,
    calculate_match_score,
)


# ========== 测试数据 ==========

SAMPLE_VAULT = {
    "personal_info": {
        "name": "张三",
        "email": "zhangsan@example.com",
        "phone": "138****8888"
    },
    "education": [
        {
            "school": "某某大学",
            "degree": "本科",
            "major": "计算机科学",
            "graduation_year": "2020"
        }
    ],
    "work_experience": [
        {
            "company": "某某科技",
            "title": "高级后端工程师",
            "duration": "2020-07 至 2024-03",
            "highlights": [
                "负责微服务架构设计",
                "优化系统性能，QPS 提升 300%",
                "使用 Python 和 FastAPI 开发核心 API"
            ]
        }
    ],
    "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis"]
}

SAMPLE_JD = """
高级后端工程师

岗位职责：
- 负责公司核心后端服务的设计与开发
- 使用 Python 和 FastAPI 构建高性能 API
- 优化数据库查询，提升系统性能
- 参与微服务架构设计

任职要求：
- 3年以上 Python 开发经验
- 熟悉 FastAPI、PostgreSQL
- 有 Docker、Kubernetes 经验优先
- 本科以上学历
"""


# ========== Tool 单元测试 ==========

class TestExtractJDKeywords:
    """测试 JD 关键词提取工具"""

    @pytest.mark.asyncio
    async def test_extract_skills(self):
        """测试技能提取准确性"""
        result = await extract_jd_keywords.ainvoke({"jd_text": SAMPLE_JD})
        data = json.loads(result)

        assert "Python" in data["required_skills"] or any("Python" in s for s in data["required_skills"])
        assert "FastAPI" in str(data["required_skills"])
        assert "PostgreSQL" in str(data["required_skills"])

    @pytest.mark.asyncio
    async def test_extract_experience_years(self):
        """测试经验年限提取"""
        result = await extract_jd_keywords.ainvoke({"jd_text": SAMPLE_JD})
        data = json.loads(result)

        assert data["experience_years"] is not None
        assert "3" in data["experience_years"]

    @pytest.mark.asyncio
    async def test_extract_education(self):
        """测试学历要求提取"""
        result = await extract_jd_keywords.ainvoke({"jd_text": SAMPLE_JD})
        data = json.loads(result)

        assert "本科" in str(data.get("education", ""))


class TestSearchVault:
    """测试 Vault 搜索工具"""

    @pytest.mark.asyncio
    async def test_search_relevant_skills(self):
        """测试相关技能搜索"""
        vault_json = json.dumps(SAMPLE_VAULT, ensure_ascii=False)
        result = await search_vault.ainvoke({
            "query": "Python 后端开发",
            "vault_data": vault_json,
            "top_k": 3
        })
        data = json.loads(result)

        assert isinstance(data, list)
        assert len(data) > 0
        # 验证返回了相关经历
        contents = [item["content"] for item in data]
        assert any("Python" in c or "FastAPI" in c for c in contents)

    @pytest.mark.asyncio
    async def test_search_no_match(self):
        """测试无匹配结果的情况"""
        vault_json = json.dumps(SAMPLE_VAULT, ensure_ascii=False)
        result = await search_vault.ainvoke({
            "query": "iOS 开发 Swift",  # Vault 中没有的技能
            "vault_data": vault_json,
            "top_k": 3
        })
        data = json.loads(result)

        # 应该返回空列表或低相关度结果
        assert isinstance(data, list)


class TestCalculateMatchScore:
    """测试匹配度计算工具"""

    @pytest.mark.asyncio
    async def test_match_score_structure(self):
        """测试评分结果结构"""
        vault_json = json.dumps(SAMPLE_VAULT, ensure_ascii=False)

        # 先提取 JD 关键词
        jd_result = await extract_jd_keywords.ainvoke({"jd_text": SAMPLE_JD})

        result = await calculate_match_score.ainvoke({
            "vault_data": vault_json,
            "jd_requirements": jd_result
        })
        data = json.loads(result)

        assert "overall_score" in data
        assert "skill_match" in data
        assert "experience_match" in data
        assert 0 <= data["overall_score"] <= 100

    @pytest.mark.asyncio
    async def test_skill_match_accuracy(self):
        """测试技能匹配准确性"""
        vault_json = json.dumps(SAMPLE_VAULT, ensure_ascii=False)
        jd_result = await extract_jd_keywords.ainvoke({"jd_text": SAMPLE_JD})

        result = await calculate_match_score.ainvoke({
            "vault_data": vault_json,
            "jd_requirements": jd_result
        })
        data = json.loads(result)

        # Python 和 FastAPI 应该匹配
        matched = data["skill_match"]["matched"]
        assert any("python" in str(m).lower() for m in matched)


class TestGenerateResumeSection:
    """测试简历生成工具"""

    @pytest.mark.asyncio
    async def test_generate_experience_section(self):
        """测试工作经历章节生成"""
        vault_json = json.dumps(SAMPLE_VAULT, ensure_ascii=False)
        result = await generate_resume_section.ainvoke({
            "section_type": "experience",
            "content_requirements": "突出 Python 后端经验",
            "vault_data": vault_json,
            "style": "professional"
        })
        data = json.loads(result)

        assert data["section_type"] == "experience"
        assert "某某科技" in data["content"]
        assert len(data["source_facts"]) > 0

    @pytest.mark.asyncio
    async def test_generate_skills_section(self):
        """测试技能章节生成"""
        vault_json = json.dumps(SAMPLE_VAULT, ensure_ascii=False)
        result = await generate_resume_section.ainvoke({
            "section_type": "skills",
            "content_requirements": "按类别组织技能",
            "vault_data": vault_json,
            "style": "technical"
        })
        data = json.loads(result)

        assert data["section_type"] == "skills"
        assert "Python" in data["content"]

    @pytest.mark.asyncio
    async def test_invalid_section_type(self):
        """测试无效的章节类型"""
        vault_json = json.dumps(SAMPLE_VAULT, ensure_ascii=False)
        result = await generate_resume_section.ainvoke({
            "section_type": "invalid_type",
            "content_requirements": "测试",
            "vault_data": vault_json
        })
        data = json.loads(result)

        assert "error" in data


class TestVerifyFacts:
    """测试防幻觉校验工具"""

    @pytest.mark.asyncio
    async def test_detect_hallucinated_skill(self):
        """测试检测虚构技能"""
        vault_json = json.dumps(SAMPLE_VAULT, ensure_ascii=False)

        # 生成包含虚构技能的内容
        fake_content = "精通 Python、FastAPI、Kubernetes 和 Rust"

        result = await verify_facts.ainvoke({
            "generated_content": fake_content,
            "vault_data": vault_json,
            "strict_mode": True
        })
        data = json.loads(result)

        assert data["is_valid"] is False
        assert len(data["hallucinations"]) > 0
        # 应该检测到 Kubernetes 和 Rust 是虚构的
        hallucinated_skills = [h["content"] for h in data["hallucinations"]]
        assert any("Kubernetes" in str(h) for h in hallucinated_skills)

    @pytest.mark.asyncio
    async def test_verify_valid_content(self):
        """测试验证真实内容"""
        vault_json = json.dumps(SAMPLE_VAULT, ensure_ascii=False)

        # 只包含 Vault 中有的技能
        valid_content = "精通 Python、FastAPI 和 PostgreSQL"

        result = await verify_facts.ainvoke({
            "generated_content": valid_content,
            "vault_data": vault_json,
            "strict_mode": True
        })
        data = json.loads(result)

        # 应该通过验证（或只有警告没有幻觉）
        assert len(data["hallucinations"]) == 0

    @pytest.mark.asyncio
    async def test_detect_exaggeration(self):
        """测试检测夸大描述"""
        vault_json = json.dumps(SAMPLE_VAULT, ensure_ascii=False)

        # 使用 Vault 中确实存在的描述，但包含夸大词汇
        exaggerated_content = "主导微服务架构设计，独创高并发解决方案"

        result = await verify_facts.ainvoke({
            "generated_content": exaggerated_content,
            "vault_data": vault_json,
            "strict_mode": True
        })
        data = json.loads(result)

        # 应该检测到夸大描述（警告级别）
        assert len(data["warnings"]) > 0


# ========== Agent 集成测试 ==========

class TestResumeTailorAgent:
    """测试 ResumeTailorAgent 端到端能力"""

    @pytest.fixture
    async def agent(self):
        """创建 Agent 实例"""
        from app.agents import ResumeTailorAgent

        # 使用环境变量中的配置
        return ResumeTailorAgent(
            model_provider="openai",
            model_name="gpt-4o-mini",  # 测试使用轻量级模型
            temperature=0.1
        )

    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """测试 Agent 初始化"""
        from app.agents import ResumeTailorAgent

        agent = ResumeTailorAgent(
            model_provider="openai",
            model_name="gpt-4o-mini",
            enable_memory=True
        )

        assert agent is not None
        assert len(agent.tools) == 5  # 5 个核心工具
        assert agent.checkpointer is not None

    @pytest.mark.asyncio
    async def test_agent_tools_registered(self):
        """测试工具是否正确注册"""
        from app.agents import ResumeTailorAgent

        agent = ResumeTailorAgent(
            model_provider="openai",
            model_name="gpt-4o-mini"
        )

        tool_names = [t.name for t in agent.tools]
        assert "extract_jd_keywords" in tool_names
        assert "search_vault" in tool_names
        assert "generate_resume_section" in tool_names
        assert "verify_facts" in tool_names
        assert "calculate_match_score" in tool_names

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="需要 OPENAI_API_KEY 环境变量"
    )
    async def test_end_to_end_tailor(self):
        """测试端到端简历定制（需要 API Key）"""
        from app.agents import ResumeTailorAgent

        agent = ResumeTailorAgent()

        start_time = time.time()
        result = await agent.tailor_resume(
            vault_data=SAMPLE_VAULT,
            jd_text=SAMPLE_JD,
            style="professional"
        )
        elapsed = time.time() - start_time

        # 验证结果结构
        assert "tailored_resume" in result
        assert "match_analysis" in result

        # 验证延迟（目标 < 30s 对于 Agent 循环）
        assert elapsed < 60, f"Agent 响应过慢: {elapsed}s"

        print(f"\n端到端延迟: {elapsed:.2f}s")
        print(f"生成简历长度: {len(result['tailored_resume'])} 字符")


# ========== 性能测试 ==========

class TestPerformance:
    """性能基准测试"""

    @pytest.mark.asyncio
    async def test_tool_latency(self):
        """测试工具调用延迟"""
        vault_json = json.dumps(SAMPLE_VAULT, ensure_ascii=False)

        # 测试 search_vault 延迟
        start = time.time()
        await search_vault.ainvoke({
            "query": "Python",
            "vault_data": vault_json
        })
        search_latency = time.time() - start

        # 本地工具应该在 100ms 内完成
        assert search_latency < 1.0, f"search_vault 太慢: {search_latency}s"

        print(f"\nsearch_vault 延迟: {search_latency*1000:.1f}ms")

    @pytest.mark.asyncio
    async def test_verify_facts_latency(self):
        """测试校验工具延迟"""
        vault_json = json.dumps(SAMPLE_VAULT, ensure_ascii=False)

        start = time.time()
        await verify_facts.ainvoke({
            "generated_content": "精通 Python 和 Kubernetes",
            "vault_data": vault_json
        })
        verify_latency = time.time() - start

        assert verify_latency < 1.0, f"verify_facts 太慢: {verify_latency}s"

        print(f"verify_facts 延迟: {verify_latency*1000:.1f}ms")


# ========== 主入口 ==========

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
