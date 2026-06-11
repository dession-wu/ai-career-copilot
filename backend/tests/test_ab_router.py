"""
P0-11 验证：ABRouter 单元测试
"""
import asyncio
import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.resume_extraction.ab_router import (
    ABRouter,
    DEFAULT_EXPERIMENTS,
    get_ab_router,
    reset_ab_router,
)


@pytest.fixture(autouse=True)
def _reset_singleton():
    """每个用例前后重置单例，避免污染"""
    reset_ab_router()
    yield
    reset_ab_router()


def test_assign_bucket_disabled_returns_control():
    """实验禁用时，所有 user 都走 control"""
    router = ABRouter()
    router.experiments = {"test_exp": {"enabled": False, "control_ratio": 0.5}}
    assert router.assign_bucket("user-1", "test_exp") == "control"
    assert router.assign_bucket("user-2", "test_exp") == "control"
    assert router.assign_bucket("user-3", "test_exp") == "control"


def test_assign_bucket_distribution():
    """验证分流分布接近 control_ratio（70/30 ±5%）"""
    router = ABRouter()
    router.experiments = {
        "test_exp": {
            "enabled": True,
            "control_ratio": 0.7,
            "treatment_strategies": ["variant_a"],
        }
    }
    counts = {"control": 0, "treatment_variant_a": 0}
    for i in range(1000):
        bucket = router.assign_bucket(f"user-{i}", "test_exp")
        counts[bucket] += 1
    assert 650 < counts["control"] < 750, f"control 桶分布异常: {counts}"
    assert 250 < counts["treatment_variant_a"] < 350, f"treatment 桶分布异常: {counts}"


def test_assign_bucket_stable_for_same_user():
    """同一 user 多次调用应分到相同桶（哈希稳定）"""
    router = ABRouter()
    router.experiments = {
        "test_exp": {
            "enabled": True,
            "control_ratio": 0.5,
            "treatment_strategies": ["variant_a", "variant_b"],
        }
    }
    for i in range(50):
        u = f"user-{i}"
        b1 = router.assign_bucket(u, "test_exp")
        b2 = router.assign_bucket(u, "test_exp")
        b3 = router.assign_bucket(u, "test_exp")
        assert b1 == b2 == b3, f"user {u} 桶不稳定: {b1} {b2} {b3}"


def test_record_metric_thread_safe():
    """多线程并发 record_metric 不丢数据"""
    router = ABRouter()
    n_threads = 10
    n_per_thread = 100

    def worker():
        for i in range(n_per_thread):
            router.record_metric(
                user_id="u",
                experiment_name="exp",
                bucket="control",
                metric="m",
                value=i,
            )

    threads = [threading.Thread(target=worker) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    values = router.get_metrics("exp", "control", "m")
    assert len(values) == n_threads * n_per_thread, f"丢失数据: 期望 {n_threads*n_per_thread}, 实际 {len(values)}"


def test_record_metric_in_resume_extraction_pipeline():
    """集成：完整提取链路能正常发出 metric（验证 P0-10 监控实际生效）

    注意：v2 路径才有 P0-10 监控埋点；v1 路径无埋点。LLM 不可用时 v2 会
    降级到 v1，因此这里直接调用 v2 以验证埋点是否被触发。
    """
    # 触发单例初始化（必须用与生产相同的代码路径）
    ab = get_ab_router()
    ab.reset_metrics()

    from app.services.resume_extraction.resume_extraction_service import (
        get_resume_extraction_service,
    )

    text = (
        "吴烨\n"
        "18133004892\n"
        "18133004892@163.com\n"
        "安徽安庆\n"
        "教育经历\n"
        "2021.09 - 2025.06 浙江大学 环境科学 本科\n"
    )
    svc = get_resume_extraction_service()
    # 调用 v2 路径（即使 LLM 不可用，规则引擎部分仍会触发 P0-10 埋点）
    asyncio.run(svc.extract_from_text_v2(text, user_id="test-p0-11", use_llm=False))

    ab = get_ab_router()
    summary = ab.get_summary()
    assert "resume_extraction_v1" in summary, f"未生成 metric: {summary}"
    total = sum(
        sum(metrics.values())
        for buckets in summary["resume_extraction_v1"].values()
        for metrics in [buckets]
    )
    assert total >= 1, f"应至少 1 条 metric 记录，实际: {summary}"


def test_get_summary_returns_counts():
    """get_summary 返回各实验/桶/metric 的计数"""
    router = ABRouter()
    router.record_metric("u1", "exp1", "control", "quality", 0.9)
    router.record_metric("u2", "exp1", "control", "quality", 0.8)
    router.record_metric("u3", "exp1", "treatment_a", "quality", 0.7)
    summary = router.get_summary()
    assert summary["exp1"]["control"]["quality"] == 2
    assert summary["exp1"]["treatment_a"]["quality"] == 1


def test_default_experiments_loaded():
    """默认实验配置（resume_extraction_v1）正确加载"""
    ab = get_ab_router()
    assert "resume_extraction_v1" in ab.experiments
    assert ab.experiments["resume_extraction_v1"]["enabled"] is True
    assert ab.experiments["resume_extraction_v1"]["control_ratio"] == 0.9
