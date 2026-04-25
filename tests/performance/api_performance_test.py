"""
API性能测试脚本
测试匹配分析API的响应时间和并发性能
"""

import asyncio
import time
import statistics
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from typing import List, Dict, Any

# 配置
BASE_URL = "http://localhost:8000"
TEST_USER = {"username": "testuser", "password": "testpass123"}
CONCURRENT_REQUESTS = [1, 5, 10, 20]  # 并发请求数
REQUESTS_PER_CONCURRENCY = 10  # 每个并发级别发送的请求数


class PerformanceTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_job_id = None
        self.results = []

    def login(self) -> bool:
        """登录获取token"""
        try:
            response = self.session.post(
                f"{BASE_URL}/api/auth/login",
                data={"username": TEST_USER["username"], "password": TEST_USER["password"]}
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                print(f"✓ 登录成功，获取到token")
                return True
            else:
                print(f"✗ 登录失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ 登录异常: {e}")
            return False

    def create_test_job(self) -> bool:
        """创建测试职位"""
        try:
            job_data = {
                "company_name": "测试公司",
                "job_title": "Python后端工程师",
                "location": "北京",
                "jd_text": """
                岗位职责：
                1. 负责后端服务的设计与开发
                2. 使用Python、FastAPI框架开发API
                3. 数据库设计与优化，使用PostgreSQL、Redis
                4. 微服务架构设计与实现
                5. Docker容器化部署

                任职要求：
                1. 3年以上Python开发经验
                2. 熟悉FastAPI、Flask等Web框架
                3. 熟悉SQLAlchemy、Alembic等ORM工具
                4. 熟悉Docker、Kubernetes
                5. 熟悉Git版本控制
                6. 良好的沟通能力和团队协作精神
                """,
                "status": "preparing"
            }
            response = self.session.post(f"{BASE_URL}/api/jobs", json=job_data)
            if response.status_code == 201:
                job = response.json()
                self.test_job_id = job.get("id")
                print(f"✓ 创建测试职位成功，ID: {self.test_job_id}")
                return True
            else:
                print(f"✗ 创建职位失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ 创建职位异常: {e}")
            return False

    def test_match_analysis_single(self) -> Dict[str, Any]:
        """单次匹配分析测试"""
        start_time = time.time()
        try:
            response = self.session.post(
                f"{BASE_URL}/api/jobs/{self.test_job_id}/analyze-weighted"
            )
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # 转换为毫秒

            if response.status_code == 200:
                data = response.json()
                processing_time = data.get("processing_time_ms", 0)
                return {
                    "success": True,
                    "response_time_ms": response_time,
                    "processing_time_ms": processing_time,
                    "overall_score": data.get("overall_score"),
                    "confidence": data.get("confidence"),
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "response_time_ms": response_time,
                    "error": f"HTTP {response.status_code}",
                    "status_code": response.status_code
                }
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            return {
                "success": False,
                "response_time_ms": response_time,
                "error": str(e),
                "status_code": 0
            }

    def run_concurrent_test(self, concurrency: int) -> Dict[str, Any]:
        """运行并发测试"""
        print(f"\n--- 并发测试: {concurrency} 个请求 ---")

        results = []
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(self.test_match_analysis_single)
                      for _ in range(REQUESTS_PER_CONCURRENCY)]

            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                status = "✓" if result["success"] else "✗"
                print(f"  {status} 响应时间: {result['response_time_ms']:.2f}ms")

        # 计算统计信息
        success_count = sum(1 for r in results if r["success"])
        response_times = [r["response_time_ms"] for r in results if r["success"]]

        if response_times:
            stats = {
                "concurrency": concurrency,
                "total_requests": len(results),
                "success_count": success_count,
                "success_rate": success_count / len(results) * 100,
                "avg_response_time": statistics.mean(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "median_response_time": statistics.median(response_times),
                "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)],
                "p99_response_time": sorted(response_times)[int(len(response_times) * 0.99)] if len(response_times) >= 100 else max(response_times)
            }
        else:
            stats = {
                "concurrency": concurrency,
                "total_requests": len(results),
                "success_count": 0,
                "success_rate": 0,
                "error": "所有请求都失败了"
            }

        return stats

    def run_all_tests(self):
        """运行所有性能测试"""
        print("=" * 60)
        print("API性能测试开始")
        print("=" * 60)

        # 登录
        if not self.login():
            print("登录失败，退出测试")
            return

        # 创建测试职位
        if not self.create_test_job():
            print("创建测试职位失败，退出测试")
            return

        # 运行并发测试
        all_stats = []
        for concurrency in CONCURRENT_REQUESTS:
            stats = self.run_concurrent_test(concurrency)
            all_stats.append(stats)
            self.results.append(stats)

        # 生成报告
        self.generate_report(all_stats)

    def generate_report(self, stats_list: List[Dict]):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("性能测试报告")
        print("=" * 60)

        # 表格头
        print(f"{'并发数':<10} {'成功率%':<10} {'平均(ms)':<12} {'最小(ms)':<12} {'最大(ms)':<12} {'P95(ms)':<12} {'状态':<10}")
        print("-" * 80)

        all_passed = True
        for stats in stats_list:
            concurrency = stats["concurrency"]
            success_rate = stats.get("success_rate", 0)
            avg_time = stats.get("avg_response_time", 0)
            min_time = stats.get("min_response_time", 0)
            max_time = stats.get("max_response_time", 0)
            p95_time = stats.get("p95_response_time", 0)

            # 判断是否达标 (响应时间 < 2s)
            passed = avg_time < 2000 and success_rate >= 95
            status = "✓ 通过" if passed else "✗ 失败"
            if not passed:
                all_passed = False

            print(f"{concurrency:<10} {success_rate:<10.1f} {avg_time:<12.2f} {min_time:<12.2f} {max_time:<12.2f} {p95_time:<12.2f} {status:<10}")

        print("-" * 80)

        # 目标指标对比
        print("\n目标指标对比:")
        print(f"  - 匹配分析响应时间 < 2s: {'✓ 达标' if all(s.get('avg_response_time', 9999) < 2000 for s in stats_list) else '✗ 未达标'}")
        print(f"  - 成功率 >= 95%: {'✓ 达标' if all(s.get('success_rate', 0) >= 95 for s in stats_list) else '✗ 未达标'}")

        # 保存详细报告
        report = {
            "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "base_url": BASE_URL,
            "test_job_id": self.test_job_id,
            "results": stats_list,
            "summary": {
                "all_passed": all_passed,
                "target_response_time_ms": 2000,
                "target_success_rate": 95
            }
        }

        report_file = "e:/Desktop/AI Career Co-pilot/tests/performance/api_performance_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n详细报告已保存: {report_file}")

        return all_passed


def main():
    tester = PerformanceTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
