"""
测试运行器 - 自动化测试执行和报告生成

使用方法：
    python tests/run_tests.py [options]

选项：
    --smoke       运行冒烟测试
    --e2e         运行端到端测试
    --api         运行API测试
    --hallucination 运行防幻觉测试
    --all         运行所有测试
    --headed      显示浏览器窗口（调试用）
    --report      生成HTML报告
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime


class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.results_dir = self.test_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
    
    def run_tests(
        self,
        markers: list = None,
        headed: bool = False,
        report: bool = False,
        verbose: bool = True
    ) -> int:
        """
        运行测试
        
        Args:
            markers: pytest标记列表
            headed: 是否显示浏览器
            report: 是否生成HTML报告
            verbose: 是否详细输出
            
        Returns:
            int: 退出码
        """
        cmd = ["python", "-m", "pytest"]
        
        # 测试目录
        cmd.append(str(self.test_dir))
        
        # 标记
        if markers:
            for marker in markers:
                cmd.extend(["-m", marker])
        
        # 浏览器模式
        if headed:
            os.environ["TEST_HEADLESS"] = "false"
        else:
            os.environ["TEST_HEADLESS"] = "true"
        
        # 报告
        if report:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = self.results_dir / f"report_{timestamp}.html"
            cmd.extend(["--html", str(report_path), "--self-contained-html"])
            print(f"📊 报告将生成: {report_path}")
        
        # 详细输出
        if verbose:
            cmd.append("-v")
        
        # 失败时继续
        cmd.append("--continue-on-collection-errors")
        
        # 截图目录
        screenshot_dir = self.results_dir / "screenshots"
        screenshot_dir.mkdir(exist_ok=True)
        
        print(f"🚀 运行测试: {' '.join(cmd)}")
        print(f"📸 截图目录: {screenshot_dir}")
        print("-" * 60)
        
        # 执行测试
        result = subprocess.run(cmd, cwd=self.test_dir.parent)
        
        return result.returncode
    
    def run_smoke_tests(self, headed: bool = False, report: bool = False) -> int:
        """运行冒烟测试"""
        print("\n🔥 运行冒烟测试...")
        return self.run_tests(
            markers=["smoke"],
            headed=headed,
            report=report
        )
    
    def run_e2e_tests(self, headed: bool = False, report: bool = False) -> int:
        """运行端到端测试"""
        print("\n🎭 运行端到端测试...")
        return self.run_tests(
            markers=["e2e"],
            headed=headed,
            report=report
        )
    
    def run_api_tests(self, report: bool = False) -> int:
        """运行API测试"""
        print("\n🔌 运行API测试...")
        return self.run_tests(
            markers=["api"],
            report=report
        )
    
    def run_hallucination_tests(self, report: bool = False) -> int:
        """运行防幻觉测试"""
        print("\n🧠 运行防幻觉测试...")
        return self.run_tests(
            markers=["hallucination"],
            report=report
        )
    
    def run_all_tests(self, headed: bool = False, report: bool = False) -> int:
        """运行所有测试"""
        print("\n🎯 运行所有测试...")
        return self.run_tests(
            headed=headed,
            report=report
        )
    
    def check_dependencies(self) -> bool:
        """检查测试依赖"""
        print("\n📦 检查测试依赖...")
        
        # 检查pytest
        try:
            import pytest
            print(f"✅ pytest: {pytest.__version__}")
        except ImportError:
            print("❌ pytest 未安装")
            print("   运行: pip install pytest pytest-html")
            return False
        
        # 检查playwright
        try:
            import playwright
            print(f"✅ playwright: {playwright.__version__}")
        except ImportError:
            print("❌ playwright 未安装")
            print("   运行: pip install pytest-playwright")
            return False
        
        # 检查浏览器
        result = subprocess.run(
            ["python", "-m", "playwright", "chromium", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ Chromium浏览器: 已安装")
        else:
            print("⚠️ Chromium浏览器: 需要安装")
            print("   运行: python -m playwright install chromium")
        
        print("-" * 60)
        return True
    
    def generate_report_summary(self):
        """生成报告摘要"""
        reports = list(self.results_dir.glob("report_*.html"))
        if reports:
            latest_report = max(reports, key=lambda p: p.stat().st_mtime)
            print(f"\n📊 最新测试报告: {latest_report}")
            print(f"   在浏览器中打开查看详情")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AI Career Co-pilot 测试运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python tests/run_tests.py --smoke              # 运行冒烟测试
  python tests/run_tests.py --e2e --headed       # 运行E2E测试（显示浏览器）
  python tests/run_tests.py --all --report       # 运行所有测试并生成报告
  python tests/run_tests.py --api                # 只运行API测试
        """
    )
    
    parser.add_argument("--smoke", action="store_true", help="运行冒烟测试")
    parser.add_argument("--e2e", action="store_true", help="运行端到端测试")
    parser.add_argument("--api", action="store_true", help="运行API测试")
    parser.add_argument("--hallucination", action="store_true", help="运行防幻觉测试")
    parser.add_argument("--all", action="store_true", help="运行所有测试")
    parser.add_argument("--headed", action="store_true", help="显示浏览器窗口（调试用）")
    parser.add_argument("--report", action="store_true", help="生成HTML报告")
    parser.add_argument("--check", action="store_true", help="检查依赖")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # 检查依赖
    if args.check:
        runner.check_dependencies()
        return 0
    
    # 如果没有指定测试类型，默认运行冒烟测试
    if not any([args.smoke, args.e2e, args.api, args.hallucination, args.all]):
        args.smoke = True
    
    # 运行测试
    exit_code = 0
    
    if args.smoke:
        code = runner.run_smoke_tests(headed=args.headed, report=args.report)
        exit_code = max(exit_code, code)
    
    if args.e2e:
        code = runner.run_e2e_tests(headed=args.headed, report=args.report)
        exit_code = max(exit_code, code)
    
    if args.api:
        code = runner.run_api_tests(report=args.report)
        exit_code = max(exit_code, code)
    
    if args.hallucination:
        code = runner.run_hallucination_tests(report=args.report)
        exit_code = max(exit_code, code)
    
    if args.all:
        code = runner.run_all_tests(headed=args.headed, report=args.report)
        exit_code = max(exit_code, code)
    
    # 生成报告摘要
    if args.report:
        runner.generate_report_summary()
    
    # 输出结果
    print("\n" + "=" * 60)
    if exit_code == 0:
        print("🎉 所有测试通过！")
    else:
        print(f"❌ 测试失败 (退出码: {exit_code})")
        print("   查看截图: tests/results/screenshots/")
    print("=" * 60)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
