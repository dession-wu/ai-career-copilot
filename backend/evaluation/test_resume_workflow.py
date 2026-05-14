"""
Resume Workflow 集成测试

验证 LangGraph StateGraph 工作流的核心能力：
1. 节点执行顺序和状态传递
2. 条件路由（重试逻辑）
3. 错误处理和降级
4. 端到端工作流执行

运行: pytest backend/evaluation/test_resume_workflow.py -v
"""

import pytest
import json
import time
import asyncio
import os
from typing import Dict, Any
from unittest.mock import patch, MagicMock

# 导入被测组件
import sys
sys.path.insert(0, "e:\\Desktop\\AI Career Co-pilot\\backend")

from app.graphs.resume_workflow import (
    create_resume_workflow,
    run_resume_workflow,
    ResumeWorkflowState,
    analyze_jd_node,
    search_vault_node,
    calculate_match_node,
    generate_resume_node,
    verify_facts_node,
    route_after_verification,
    route_on_error,
    _combine_sections
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


# ========== 工作流构建测试 ==========

class TestWorkflowConstruction:
    """测试工作流构建和结构"""

    def test_create_workflow(self):
        """测试工作流能正确创建"""
        workflow = create_resume_workflow()
        assert workflow is not None

    def test_workflow_nodes_registered(self):
        """测试所有节点已注册"""
        workflow = create_resume_workflow()
        # 编译后的工作流应该包含所有节点
        # 注意：编译后的 graph 结构取决于 LangGraph 版本
        assert hasattr(workflow, 'invoke') or hasattr(workflow, 'ainvoke')


# ========== 节点单元测试 ==========

class TestAnalyzeJDNode:
    """测试 JD 分析节点"""

    @pytest.mark.asyncio
    async def test_analyze_jd_success(self):
        """测试 JD 分析成功"""
        state = ResumeWorkflowState(
            vault_data=json.dumps(SAMPLE_VAULT, ensure_ascii=False),
            jd_text=SAMPLE_JD,
            style="professional",
            jd_analysis="",
            vault_search_results="",
            match_score="",
            generated_sections=[],
            final_resume="",
            verification_result="",
            is_valid=False,
            current_step="started",
            retry_count=0,
            errors=[]
        )

        result = await analyze_jd_node(state)

        assert result["current_step"] == "jd_analyzed"
        assert result["jd_analysis"] != ""
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_analyze_jd_error_handling(self):
        """测试 JD 分析错误处理"""
        state = ResumeWorkflowState(
            vault_data="",
            jd_text="",  # 空 JD 应该也能处理
            style="professional",
            jd_analysis="",
            vault_search_results="",
            match_score="",
            generated_sections=[],
            final_resume="",
            verification_result="",
            is_valid=False,
            current_step="started",
            retry_count=0,
            errors=[]
        )

        result = await analyze_jd_node(state)

        # 即使失败也应该返回状态，不抛异常
        assert result["current_step"] in ["jd_analyzed", "jd_analysis_failed"]


class TestSearchVaultNode:
    """测试 Vault 搜索节点"""

    @pytest.mark.asyncio
    async def test_search_vault_success(self):
        """测试 Vault 搜索成功"""
        # 先执行 JD 分析
        state = ResumeWorkflowState(
            vault_data=json.dumps(SAMPLE_VAULT, ensure_ascii=False),
            jd_text=SAMPLE_JD,
            style="professional",
            jd_analysis=json.dumps({
                "priority_skills": ["Python", "FastAPI"],
                "required_skills": [{"skill": "Python"}, {"skill": "PostgreSQL"}]
            }),
            vault_search_results="",
            match_score="",
            generated_sections=[],
            final_resume="",
            verification_result="",
            is_valid=False,
            current_step="jd_analyzed",
            retry_count=0,
            errors=[]
        )

        result = await search_vault_node(state)

        assert result["current_step"] == "vault_searched"
        assert result["vault_search_results"] != ""
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_search_vault_with_invalid_analysis(self):
        """测试 JD 分析结果异常时的处理"""
        state = ResumeWorkflowState(
            vault_data=json.dumps(SAMPLE_VAULT, ensure_ascii=False),
            jd_text=SAMPLE_JD,
            style="professional",
            jd_analysis="invalid json",  # 无效 JSON
            vault_search_results="",
            match_score="",
            generated_sections=[],
            final_resume="",
            verification_result="",
            is_valid=False,
            current_step="jd_analyzed",
            retry_count=0,
            errors=[]
        )

        result = await search_vault_node(state)

        # 应该处理错误，不抛异常
        assert result["current_step"] in ["vault_searched", "vault_search_failed"]


class TestCalculateMatchNode:
    """测试匹配度计算节点"""

    @pytest.mark.asyncio
    async def test_calculate_match_success(self):
        """测试匹配度计算成功"""
        state = ResumeWorkflowState(
            vault_data=json.dumps(SAMPLE_VAULT, ensure_ascii=False),
            jd_text=SAMPLE_JD,
            style="professional",
            jd_analysis="",
            vault_search_results="",
            match_score="",
            generated_sections=[],
            final_resume="",
            verification_result="",
            is_valid=False,
            current_step="vault_searched",
            retry_count=0,
            errors=[]
        )

        result = await calculate_match_node(state)

        assert result["current_step"] == "match_calculated"
        assert result["match_score"] != ""
        assert len(result["errors"]) == 0


class TestGenerateResumeNode:
    """测试简历生成节点"""

    @pytest.mark.asyncio
    async def test_generate_resume_success(self):
        """测试简历生成成功"""
        state = ResumeWorkflowState(
            vault_data=json.dumps(SAMPLE_VAULT, ensure_ascii=False),
            jd_text=SAMPLE_JD,
            style="professional",
            jd_analysis=json.dumps({"test": "analysis"}),
            vault_search_results="",
            match_score=json.dumps({"overall_score": 85}),
            generated_sections=[],
            final_resume="",
            verification_result="",
            is_valid=False,
            current_step="match_calculated",
            retry_count=0,
            errors=[]
        )

        result = await generate_resume_node(state)

        assert result["current_step"] == "resume_generated"
        assert result["final_resume"] != ""
        assert len(result["generated_sections"]) > 0

    @pytest.mark.asyncio
    async def test_generate_resume_empty_vault(self):
        """测试空 Vault 数据时的处理"""
        state = ResumeWorkflowState(
            vault_data=json.dumps({"skills": []}, ensure_ascii=False),
            jd_text=SAMPLE_JD,
            style="professional",
            jd_analysis=json.dumps({"test": "analysis"}),
            vault_search_results="",
            match_score="",
            generated_sections=[],
            final_resume="",
            verification_result="",
            is_valid=False,
            current_step="match_calculated",
            retry_count=0,
            errors=[]
        )

        result = await generate_resume_node(state)

        # 应该生成内容，即使 Vault 为空
        assert result["current_step"] in ["resume_generated", "resume_gen_failed"]


class TestVerifyFactsNode:
    """测试事实校验节点"""

    @pytest.mark.asyncio
    async def test_verify_valid_content(self):
        """测试验证真实内容"""
        state = ResumeWorkflowState(
            vault_data=json.dumps(SAMPLE_VAULT, ensure_ascii=False),
            jd_text=SAMPLE_JD,
            style="professional",
            jd_analysis="",
            vault_search_results="",
            match_score="",
            generated_sections=[],
            final_resume="精通 Python、FastAPI 和 PostgreSQL",
            verification_result="",
            is_valid=False,
            current_step="resume_generated",
            retry_count=0,
            errors=[]
        )

        result = await verify_facts_node(state)

        assert result["current_step"] == "verified"
        assert result["verification_result"] != ""

    @pytest.mark.asyncio
    async def test_verify_with_hallucination(self):
        """测试检测到幻觉时的重试逻辑"""
        state = ResumeWorkflowState(
            vault_data=json.dumps(SAMPLE_VAULT, ensure_ascii=False),
            jd_text=SAMPLE_JD,
            style="professional",
            jd_analysis="",
            vault_search_results="",
            match_score="",
            generated_sections=[],
            final_resume="精通 Python、FastAPI、Kubernetes 和 Rust",
            verification_result="",
            is_valid=False,
            current_step="resume_generated",
            retry_count=0,
            errors=[]
        )

        result = await verify_facts_node(state)

        # 应该检测到幻觉并标记需要重试
        assert result["current_step"] == "needs_retry"
        assert result["is_valid"] is False
        assert result["retry_count"] == 1

    @pytest.mark.asyncio
    async def test_verify_max_retries(self):
        """测试达到最大重试次数"""
        state = ResumeWorkflowState(
            vault_data=json.dumps(SAMPLE_VAULT, ensure_ascii=False),
            jd_text=SAMPLE_JD,
            style="professional",
            jd_analysis="",
            vault_search_results="",
            match_score="",
            generated_sections=[],
            final_resume="精通 Kubernetes 和 Rust",
            verification_result="",
            is_valid=False,
            current_step="resume_generated",
            retry_count=2,  # 已达到最大重试次数
            errors=[]
        )

        result = await verify_facts_node(state)

        # 超过重试次数，应该结束
        assert result["current_step"] == "verified"
        assert result["retry_count"] == 2


# ========== 路由函数测试 ==========

class TestRouteAfterVerification:
    """测试校验后路由决策"""

    def test_route_retry(self):
        """测试需要重试时的路由"""
        state = ResumeWorkflowState(
            vault_data="",
            jd_text="",
            style="",
            jd_analysis="",
            vault_search_results="",
            match_score="",
            generated_sections=[],
            final_resume="",
            verification_result="",
            is_valid=False,
            current_step="needs_retry",
            retry_count=1,
            errors=[]
        )

        result = route_after_verification(state)
        assert result == "generate_resume"

    def test_route_end_when_valid(self):
        """测试验证通过时的路由"""
        state = ResumeWorkflowState(
            vault_data="",
            jd_text="",
            style="",
            jd_analysis="",
            vault_search_results="",
            match_score="",
            generated_sections=[],
            final_resume="",
            verification_result="",
            is_valid=True,
            current_step="verified",
            retry_count=0,
            errors=[]
        )

        result = route_after_verification(state)
        assert result == "end"

    def test_route_end_when_max_retries(self):
        """测试达到最大重试次数时的路由"""
        state = ResumeWorkflowState(
            vault_data="",
            jd_text="",
            style="",
            jd_analysis="",
            vault_search_results="",
            match_score="",
            generated_sections=[],
            final_resume="",
            verification_result="",
            is_valid=False,
            current_step="needs_retry",
            retry_count=2,  # 最大重试次数
            errors=[]
        )

        result = route_after_verification(state)
        assert result == "end"


class TestRouteOnError:
    """测试错误处理路由"""

    def test_continue_with_few_errors(self):
        """测试错误较少时继续执行"""
        state = ResumeWorkflowState(
            vault_data="",
            jd_text="",
            style="",
            jd_analysis="",
            vault_search_results="",
            match_score="",
            generated_sections=[],
            final_resume="",
            verification_result="",
            is_valid=False,
            current_step="",
            retry_count=0,
            errors=["error1"]
        )

        result = route_on_error(state)
        assert result == "continue"

    def test_end_with_many_errors(self):
        """测试错误过多时提前结束"""
        state = ResumeWorkflowState(
            vault_data="",
            jd_text="",
            style="",
            jd_analysis="",
            vault_search_results="",
            match_score="",
            generated_sections=[],
            final_resume="",
            verification_result="",
            is_valid=False,
            current_step="",
            retry_count=0,
            errors=["error1", "error2", "error3"]
        )

        result = route_on_error(state)
        assert result == "end"


# ========== 辅助函数测试 ==========

class TestCombineSections:
    """测试章节合并函数"""

    def test_combine_sections_basic(self):
        """测试基本合并功能"""
        sections = [
            {"section_type": "summary", "content": "这是摘要"},
            {"section_type": "experience", "content": "这是经历"},
            {"section_type": "skills", "content": "这是技能"}
        ]
        state = ResumeWorkflowState(
            vault_data="",
            jd_text="",
            style="",
            jd_analysis="",
            vault_search_results="",
            match_score=json.dumps({"overall_score": 85}),
            generated_sections=[],
            final_resume="",
            verification_result="",
            is_valid=False,
            current_step="",
            retry_count=0,
            errors=[]
        )

        result = _combine_sections(sections, state)

        assert "定制简历" in result
        assert "匹配度评分" in result
        assert "这是摘要" in result
        assert "这是经历" in result
        assert "这是技能" in result

    def test_combine_sections_with_error(self):
        """测试包含错误章节的合并"""
        sections = [
            {"section_type": "summary", "content": "这是摘要"},
            {"section_type": "experience", "error": "生成失败"},
            {"section_type": "skills", "content": "这是技能"}
        ]
        state = ResumeWorkflowState(
            vault_data="",
            jd_text="",
            style="",
            jd_analysis="",
            vault_search_results="",
            match_score="",
            generated_sections=[],
            final_resume="",
            verification_result="",
            is_valid=False,
            current_step="",
            retry_count=0,
            errors=[]
        )

        result = _combine_sections(sections, state)

        assert "这是摘要" in result
        assert "这是技能" in result
        # 错误的章节不应该出现在结果中
        assert "生成失败" not in result


# ========== 端到端工作流测试 ==========

class TestEndToEndWorkflow:
    """测试端到端工作流执行"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_run_workflow_success(self):
        """测试完整工作流成功执行"""
        start_time = time.time()

        result = await run_resume_workflow(
            vault_data=SAMPLE_VAULT,
            jd_text=SAMPLE_JD,
            style="professional"
        )

        elapsed = time.time() - start_time

        # 验证结果结构
        assert "final_resume" in result
        assert "is_valid" in result
        assert "match_score" in result
        assert "verification_result" in result
        assert "errors" in result
        assert "steps_completed" in result

        # 验证最终输出
        assert result["final_resume"] != ""
        assert result["steps_completed"] != ""

        # 性能断言（端到端应该 < 60s）
        assert elapsed < 60, f"工作流执行过慢: {elapsed:.2f}s"

        print(f"\n端到端延迟: {elapsed:.2f}s")
        print(f"生成简历长度: {len(result['final_resume'])} 字符")
        print(f"完成步骤: {result['steps_completed']}")
        print(f"错误数: {len(result['errors'])}")

    @pytest.mark.asyncio
    async def test_run_workflow_empty_jd(self):
        """测试空 JD 的处理"""
        result = await run_resume_workflow(
            vault_data=SAMPLE_VAULT,
            jd_text="",
            style="professional"
        )

        # 应该返回结果，不抛异常
        assert "final_resume" in result
        assert "errors" in result

    @pytest.mark.asyncio
    async def test_run_workflow_empty_vault(self):
        """测试空 Vault 的处理"""
        result = await run_resume_workflow(
            vault_data={"skills": []},
            jd_text=SAMPLE_JD,
            style="professional"
        )

        # 应该返回结果，不抛异常
        assert "final_resume" in result
        assert "errors" in result


# ========== 状态管理测试 ==========

class TestStateManagement:
    """测试状态管理"""

    def test_state_immutability_pattern(self):
        """测试状态不可变模式（节点返回新状态）"""
        original_state = ResumeWorkflowState(
            vault_data="test",
            jd_text="test",
            style="professional",
            jd_analysis="",
            vault_search_results="",
            match_score="",
            generated_sections=[],
            final_resume="",
            verification_result="",
            is_valid=False,
            current_step="started",
            retry_count=0,
            errors=[]
        )

        # 模拟节点修改状态
        new_state = {**original_state, "current_step": "modified"}

        # 原始状态不应被修改
        assert original_state["current_step"] == "started"
        assert new_state["current_step"] == "modified"

    def test_state_error_accumulation(self):
        """测试错误累积"""
        state = ResumeWorkflowState(
            vault_data="",
            jd_text="",
            style="",
            jd_analysis="",
            vault_search_results="",
            match_score="",
            generated_sections=[],
            final_resume="",
            verification_result="",
            is_valid=False,
            current_step="",
            retry_count=0,
            errors=["error1"]
        )

        # 模拟添加新错误
        new_state = {
            **state,
            "errors": state["errors"] + ["error2"]
        }

        assert len(new_state["errors"]) == 2
        assert "error1" in new_state["errors"]
        assert "error2" in new_state["errors"]


# ========== 性能测试 ==========

class TestWorkflowPerformance:
    """工作流性能测试"""

    @pytest.mark.asyncio
    async def test_node_execution_latency(self):
        """测试单个节点执行延迟"""
        state = ResumeWorkflowState(
            vault_data=json.dumps(SAMPLE_VAULT, ensure_ascii=False),
            jd_text=SAMPLE_JD,
            style="professional",
            jd_analysis="",
            vault_search_results="",
            match_score="",
            generated_sections=[],
            final_resume="",
            verification_result="",
            is_valid=False,
            current_step="started",
            retry_count=0,
            errors=[]
        )

        start = time.time()
        result = await analyze_jd_node(state)
        latency = time.time() - start

        # 节点执行应该 < 5s
        assert latency < 5.0, f"节点执行过慢: {latency:.2f}s"
        print(f"\nanalyze_jd_node 延迟: {latency*1000:.1f}ms")

    @pytest.mark.asyncio
    async def test_parallel_section_generation(self):
        """测试并行章节生成性能"""
        state = ResumeWorkflowState(
            vault_data=json.dumps(SAMPLE_VAULT, ensure_ascii=False),
            jd_text=SAMPLE_JD,
            style="professional",
            jd_analysis=json.dumps({"test": "analysis"}),
            vault_search_results="",
            match_score=json.dumps({"overall_score": 85}),
            generated_sections=[],
            final_resume="",
            verification_result="",
            is_valid=False,
            current_step="match_calculated",
            retry_count=0,
            errors=[]
        )

        start = time.time()
        result = await generate_resume_node(state)
        elapsed = time.time() - start

        # 并行生成应该比串行快
        assert result["current_step"] == "resume_generated"
        assert len(result["generated_sections"]) > 0

        print(f"\n并行生成 {len(result['generated_sections'])} 个章节耗时: {elapsed*1000:.1f}ms")


# ========== 主入口 ==========

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
