"""
A/B 实验路由 + 监控埋点
P0-11: 补齐 resume_extraction_service 调用的 assign_bucket / record_metric 方法
与 SmartRouter（字段策略路由）解耦，独立演进
"""
import hashlib
import json
import logging
import threading
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# 默认实验配置（与 backend/config/ab_test.json 一致）
DEFAULT_EXPERIMENTS: Dict[str, Dict[str, Any]] = {
    "resume_extraction_v1": {
        "enabled": True,
        "control_ratio": 0.9,  # 90% 走 control（旧）
        "treatment_strategies": ["rule_v2_fallback"],  # 10% 走 treatment（新）
    }
}


class ABRouter:
    """
    A/B 实验路由器
    - 按 user_id 哈希稳定分流（同 user 多次请求落到同一桶）
    - 支持多实验并行
    - 监控埋点写入内存缓冲区（生产可替换为 Prometheus/Datadog）
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.experiments: Dict[str, Dict[str, Any]] = {
            name: cfg.copy() for name, cfg in DEFAULT_EXPERIMENTS.items()
        }
        if config_path and config_path.exists():
            try:
                cfg = json.loads(config_path.read_text(encoding="utf-8"))
                # 浅合并，文件配置覆盖默认
                for exp_name, exp_cfg in cfg.get("experiments", {}).items():
                    if exp_name in self.experiments:
                        self.experiments[exp_name].update(exp_cfg)
                    else:
                        self.experiments[exp_name] = exp_cfg
            except Exception as e:
                logger.warning("ABRouter config load failed (using defaults): %s", e)
        # 内存指标缓冲：experiment → bucket → metric → list[(ts, value, meta)]
        self._metrics: Dict[str, Dict[str, Dict[str, List[Tuple[float, float, Dict[str, Any]]]]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )
        self._lock = threading.Lock()
        logger.info(
            "ABRouter initialized with %d experiments: %s",
            len(self.experiments),
            list(self.experiments.keys()),
        )

    def assign_bucket(self, user_id: str, experiment_name: str) -> str:
        """
        为 user 分配实验桶
        Returns: "control" | "treatment_<strategy_name>"
        """
        exp = self.experiments.get(experiment_name, {})
        if not exp.get("enabled", False):
            return "control"
        # 哈希 key 包含 experiment_name，避免不同实验间 hash 冲突
        h = int(hashlib.md5(f"{experiment_name}:{user_id}".encode("utf-8")).hexdigest(), 16)
        ratio = float(exp.get("control_ratio", 0.9))
        bucket_value = (h % 10000) / 10000.0
        if bucket_value < ratio:
            return "control"
        strategies = exp.get("treatment_strategies", [])
        if not strategies:
            return "control"
        idx = h % len(strategies)
        return f"treatment_{strategies[idx]}"

    def record_metric(
        self,
        user_id: str,
        experiment_name: str,
        bucket: str,
        metric: str,
        value: float,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """记录监控指标（线程安全）"""
        with self._lock:
            self._metrics[experiment_name][bucket][metric].append(
                (time.time(), value, meta or {})
            )

    def get_metrics(
        self, experiment_name: str, bucket: str, metric: str
    ) -> List[Tuple[float, float, Dict[str, Any]]]:
        """查询指标（用于周报 / 调试）"""
        with self._lock:
            return list(
                self._metrics.get(experiment_name, {})
                .get(bucket, {})
                .get(metric, [])
            )

    def get_summary(self) -> Dict[str, Any]:
        """获取所有实验的摘要（用于调试 / 监控页）"""
        with self._lock:
            return {
                exp: {
                    bucket: {
                        metric: len(values)
                        for metric, values in metrics.items()
                    }
                    for bucket, metrics in buckets.items()
                }
                for exp, buckets in self._metrics.items()
            }

    def reset_metrics(self) -> None:
        """重置指标（仅供测试使用）"""
        with self._lock:
            self._metrics.clear()


_ab_router: Optional[ABRouter] = None


def get_ab_router() -> ABRouter:
    """获取 A/B 路由单例"""
    global _ab_router
    if _ab_router is None:
        # 配置文件路径：backend/config/ab_test.json
        # Path(__file__) = backend/app/services/resume_extraction/ab_router.py
        # parents[0] = resume_extraction
        # parents[1] = services
        # parents[2] = app
        # parents[3] = backend
        config_path = Path(__file__).resolve().parents[3] / "config" / "ab_test.json"
        _ab_router = ABRouter(config_path=config_path)
    return _ab_router


def reset_ab_router() -> None:
    """重置单例（仅供测试使用）"""
    global _ab_router
    _ab_router = None
