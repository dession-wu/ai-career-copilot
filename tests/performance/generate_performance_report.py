"""
综合性能测试报告生成器
整合所有性能测试结果并生成最终报告
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any


class PerformanceReportGenerator:
    def __init__(self, output_dir: str = "e:/Desktop/AI Career Co-pilot/tests/performance"):
        self.output_dir = output_dir
        self.report_data = {
            "test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "test_environment": {
                "os": "Windows",
                "backend": "FastAPI (Python 3.11+)",
                "frontend": "Next.js 14+",
                "database": "SQLite"
            },
            "target_metrics": {
                "match_analysis_response_time_ms": 2000,
                "frontend_load_time_ms": 3000,
                "memory_usage_mb": 100,
                "lighthouse_score": 80
            },
            "results": {}
        }

    def load_api_results(self) -> Dict[str, Any]:
        """加载API性能测试结果"""
        try:
            with open(os.path.join(self.output_dir, "api_performance_report.json"), "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print("警告: 未找到API性能测试报告")
            return None

    def load_frontend_results(self) -> Dict[str, Any]:
        """加载前端性能测试结果"""
        try:
            with open(os.path.join(self.output_dir, "frontend_performance_report.json"), "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print("警告: 未找到前端性能测试报告")
            return None

    def load_lighthouse_results(self) -> Dict[str, Any]:
        """加载Lighthouse测试结果"""
        try:
            with open(os.path.join(self.output_dir, "lighthouse_report.json"), "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print("警告: 未找到Lighthouse测试报告")
            return None

    def analyze_api_performance(self, data: Dict) -> Dict[str, Any]:
        """分析API性能"""
        if not data:
            return {"status": "未测试", "passed": False}

        results = data.get("results", [])
        if not results:
            return {"status": "无数据", "passed": False}

        # 找出最大平均响应时间
        max_avg_time = max(r.get("avg_response_time", 0) for r in results)
        min_success_rate = min(r.get("success_rate", 0) for r in results)

        passed = max_avg_time < 2000 and min_success_rate >= 95

        return {
            "status": "通过" if passed else "未通过",
            "passed": passed,
            "max_avg_response_time_ms": round(max_avg_time, 2),
            "min_success_rate": round(min_success_rate, 2),
            "details": results
        }

    def analyze_frontend_performance(self, data: Dict) -> Dict[str, Any]:
        """分析前端性能"""
        if not data:
            return {"status": "未测试", "passed": False}

        results = data.get("results", [])
        if not results:
            return {"status": "无数据", "passed": False}

        # 找出最大加载时间和内存占用
        max_load_time = max(r["average"]["loadTime"] for r in results)
        max_memory = max(
            float(r["average"]["memoryUsedMB"]) 
            for r in results 
            if r["average"]["memoryUsedMB"] != "N/A"
        )

        passed = max_load_time < 3000 and max_memory < 100

        return {
            "status": "通过" if passed else "未通过",
            "passed": passed,
            "max_load_time_ms": max_load_time,
            "max_memory_mb": round(max_memory, 2),
            "details": [
                {
                    "page": r["page"],
                    "avg_load_time_ms": r["average"]["loadTime"],
                    "avg_memory_mb": r["average"]["memoryUsedMB"]
                }
                for r in results
            ]
        }

    def analyze_lighthouse_performance(self, data: Dict) -> Dict[str, Any]:
        """分析Lighthouse性能"""
        if not data:
            return {"status": "未测试", "passed": False}

        results = data.get("results", [])
        valid_results = [r for r in results if not r.get("error")]

        if not valid_results:
            return {"status": "无有效数据", "passed": False}

        # 计算平均分
        avg_scores = {
            "performance": round(sum(r["scores"]["performance"] for r in valid_results) / len(valid_results)),
            "accessibility": round(sum(r["scores"]["accessibility"] for r in valid_results) / len(valid_results)),
            "bestPractices": round(sum(r["scores"]["bestPractices"] for r in valid_results) / len(valid_results)),
            "seo": round(sum(r["scores"]["seo"] for r in valid_results) / len(valid_results))
        }

        passed = all(score >= 80 for score in avg_scores.values())

        return {
            "status": "通过" if passed else "未通过",
            "passed": passed,
            "average_scores": avg_scores,
            "details": [
                {
                    "page": r["page"],
                    "scores": r["scores"]
                }
                for r in valid_results
            ]
        }

    def generate_summary(self) -> Dict[str, Any]:
        """生成测试摘要"""
        api_data = self.load_api_results()
        frontend_data = self.load_frontend_results()
        lighthouse_data = self.load_lighthouse_results()

        api_analysis = self.analyze_api_performance(api_data)
        frontend_analysis = self.analyze_frontend_performance(frontend_data)
        lighthouse_analysis = self.analyze_lighthouse_performance(lighthouse_data)

        self.report_data["results"] = {
            "api_performance": api_analysis,
            "frontend_performance": frontend_analysis,
            "lighthouse": lighthouse_analysis
        }

        # 总体评估
        all_passed = (
            api_analysis.get("passed", False) and
            frontend_analysis.get("passed", False) and
            lighthouse_analysis.get("passed", False)
        )

        self.report_data["summary"] = {
            "all_tests_passed": all_passed,
            "api_passed": api_analysis.get("passed", False),
            "frontend_passed": frontend_analysis.get("passed", False),
            "lighthouse_passed": lighthouse_analysis.get("passed", False)
        }

        return self.report_data

    def generate_markdown_report(self) -> str:
        """生成Markdown格式的报告"""
        data = self.generate_summary()

        report = f"""# 性能测试报告

**测试时间**: {data['test_time']}

## 测试环境

| 组件 | 版本/类型 |
|------|----------|
| 操作系统 | {data['test_environment']['os']} |
| 后端框架 | {data['test_environment']['backend']} |
| 前端框架 | {data['test_environment']['frontend']} |
| 数据库 | {data['test_environment']['database']} |

## 目标指标

| 指标 | 目标值 |
|------|--------|
| 匹配分析响应时间 | < 2s |
| 前端首屏加载时间 | < 3s |
| 内存占用 | < 100MB |
| Lighthouse评分 | >= 80 |

## 测试结果摘要

| 测试项 | 状态 | 备注 |
|--------|------|------|
| API性能测试 | {'✅ 通过' if data['summary']['api_passed'] else '❌ 未通过'} | {'所有并发级别响应时间<2s' if data['summary']['api_passed'] else '部分测试未达标'} |
| 前端性能测试 | {'✅ 通过' if data['summary']['frontend_passed'] else '❌ 未通过'} | {'加载时间和内存占用达标' if data['summary']['frontend_passed'] else '部分指标未达标'} |
| Lighthouse测试 | {'✅ 通过' if data['summary']['lighthouse_passed'] else '❌ 未通过'} | {'所有评分>=80' if data['summary']['lighthouse_passed'] else '部分评分未达标'} |

**总体结果**: {'✅ 全部通过' if data['summary']['all_tests_passed'] else '❌ 存在未达标项'}

---

## 详细测试结果

### 1. API性能测试

**状态**: {data['results']['api_performance']['status']}

| 指标 | 实际值 | 目标值 | 状态 |
|------|--------|--------|------|
| 最大平均响应时间 | {data['results']['api_performance'].get('max_avg_response_time_ms', 'N/A')} ms | < 2000 ms | {'✅' if data['results']['api_performance'].get('max_avg_response_time_ms', 9999) < 2000 else '❌'} |
| 最小成功率 | {data['results']['api_performance'].get('min_success_rate', 'N/A')}% | >= 95% | {'✅' if data['results']['api_performance'].get('min_success_rate', 0) >= 95 else '❌'} |

#### 并发测试详情

"""

        # 添加API并发测试详情
        api_details = data['results']['api_performance'].get('details', [])
        if api_details:
            report += "| 并发数 | 平均响应时间(ms) | 成功率(%) | P95(ms) |\n"
            report += "|--------|------------------|-----------|----------|\n"
            for detail in api_details:
                report += f"| {detail.get('concurrency', 'N/A')} | {detail.get('avg_response_time', 'N/A'):.2f} | {detail.get('success_rate', 'N/A'):.1f} | {detail.get('p95_response_time', 'N/A'):.2f} |\n"

        report += f"""

### 2. 前端性能测试

**状态**: {data['results']['frontend_performance']['status']}

| 指标 | 实际值 | 目标值 | 状态 |
|------|--------|--------|------|
| 最大加载时间 | {data['results']['frontend_performance'].get('max_load_time_ms', 'N/A')} ms | < 3000 ms | {'✅' if data['results']['frontend_performance'].get('max_load_time_ms', 9999) < 3000 else '❌'} |
| 最大内存占用 | {data['results']['frontend_performance'].get('max_memory_mb', 'N/A')} MB | < 100 MB | {'✅' if data['results']['frontend_performance'].get('max_memory_mb', 999) < 100 else '❌'} |

#### 页面加载详情

"""

        # 添加前端页面详情
        frontend_details = data['results']['frontend_performance'].get('details', [])
        if frontend_details:
            report += "| 页面 | 平均加载时间(ms) | 平均内存(MB) |\n"
            report += "|------|------------------|--------------|\n"
            for detail in frontend_details:
                report += f"| {detail.get('page', 'N/A')} | {detail.get('avg_load_time_ms', 'N/A')} | {detail.get('avg_memory_mb', 'N/A')} |\n"

        report += f"""

### 3. Lighthouse性能测试

**状态**: {data['results']['lighthouse']['status']}

| 类别 | 平均评分 | 目标值 | 状态 |
|------|----------|--------|------|
| Performance | {data['results']['lighthouse'].get('average_scores', {}).get('performance', 'N/A')} | >= 80 | {'✅' if data['results']['lighthouse'].get('average_scores', {}).get('performance', 0) >= 80 else '❌'} |
| Accessibility | {data['results']['lighthouse'].get('average_scores', {}).get('accessibility', 'N/A')} | >= 80 | {'✅' if data['results']['lighthouse'].get('average_scores', {}).get('accessibility', 0) >= 80 else '❌'} |
| Best Practices | {data['results']['lighthouse'].get('average_scores', {}).get('bestPractices', 'N/A')} | >= 80 | {'✅' if data['results']['lighthouse'].get('average_scores', {}).get('bestPractices', 0) >= 80 else '❌'} |
| SEO | {data['results']['lighthouse'].get('average_scores', {}).get('seo', 'N/A')} | >= 80 | {'✅' if data['results']['lighthouse'].get('average_scores', {}).get('seo', 0) >= 80 else '❌'} |

#### 各页面评分详情

"""

        # 添加Lighthouse页面详情
        lighthouse_details = data['results']['lighthouse'].get('details', [])
        if lighthouse_details:
            report += "| 页面 | Performance | Accessibility | Best Practices | SEO |\n"
            report += "|------|-------------|---------------|----------------|-----|\n"
            for detail in lighthouse_details:
                scores = detail.get('scores', {})
                report += f"| {detail.get('page', 'N/A')} | {scores.get('performance', 'N/A')} | {scores.get('accessibility', 'N/A')} | {scores.get('bestPractices', 'N/A')} | {scores.get('seo', 'N/A')} |\n"

        report += """

---

## 结论与建议

"""

        if data['summary']['all_tests_passed']:
            report += """✅ **所有性能测试均已通过**

系统性能表现良好，所有指标均达到目标要求。建议：
- 继续保持当前优化水平
- 定期进行性能监控
- 关注用户实际使用反馈
"""
        else:
            report += """❌ **部分性能测试未通过**

需要优化的方面：
"""
            if not data['summary']['api_passed']:
                report += "- API响应时间需要优化，建议检查数据库查询和算法效率\n"
            if not data['summary']['frontend_passed']:
                report += "- 前端加载时间或内存占用过高，建议优化资源加载和组件渲染\n"
            if not data['summary']['lighthouse_passed']:
                report += "- Lighthouse评分未达标，建议优化代码分割、图片压缩和缓存策略\n"

        report += """

---

*报告生成时间: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """*
"""

        return report

    def save_reports(self):
        """保存所有报告"""
        # 保存JSON报告
        json_path = os.path.join(self.output_dir, "performance_report.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.report_data, f, ensure_ascii=False, indent=2)
        print(f"JSON报告已保存: {json_path}")

        # 保存Markdown报告
        markdown_report = self.generate_markdown_report()
        md_path = os.path.join(self.output_dir, "performance_report.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_report)
        print(f"Markdown报告已保存: {md_path}")

        return md_path


def main():
    generator = PerformanceReportGenerator()
    generator.save_reports()
    print("\n性能测试报告生成完成!")


if __name__ == "__main__":
    main()
