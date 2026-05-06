"""
自动化测试Agent

这个脚本作为"测试审查员"角色，在开发完成后自动执行测试，
并生成详细的测试报告。

使用方法：
    python tests/test_agent.py [--watch]

功能：
1. 自动检测代码变更
2. 运行相关测试
3. 生成测试报告
4. 发现问题时自动通知
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import json


class TestAgent:
    """
    自动化测试Agent
    
    角色：测试审查员
    职责：
    - 验证功能完整性
    - 检查代码质量
    - 验证用户体验
    - 生成测试报告
    """
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_dir = self.project_root / "tests"
        self.results_dir = self.test_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        # 测试报告
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "tests": [],
            "issues": [],
            "recommendations": []
        }
    
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "TEST": "🧪",
            "AGENT": "🤖"
        }.get(level, "ℹ️")
        
        print(f"{prefix} [{timestamp}] {message}")
    
    def run_command(self, cmd: List[str], cwd: Path = None) -> tuple:
        """运行命令"""
        if cwd is None:
            cwd = self.project_root
        
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True
        )
        return result.returncode, result.stdout, result.stderr
    
    def check_environment(self) -> bool:
        """检查测试环境"""
        self.log("检查测试环境...", "AGENT")
        
        checks = []
        
        # 检查后端服务
        code, _, _ = self.run_command(
            ["curl", "-s", "http://localhost:8000/health"],
            cwd=self.project_root
        )
        backend_ok = code == 0
        checks.append(("后端服务", backend_ok, "http://localhost:8000"))
        
        # 检查前端服务
        code, _, _ = self.run_command(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://localhost:3000"],
            cwd=self.project_root
        )
        frontend_ok = code == 0
        checks.append(("前端服务", frontend_ok, "http://localhost:3000"))
        
        # 检查数据库
        db_ok = (self.project_root / "backend" / "app.db").exists()
        checks.append(("数据库文件", db_ok, "backend/app.db"))
        
        # 输出结果
        all_ok = True
        for name, ok, detail in checks:
            status = "运行中" if ok else "未启动"
            level = "SUCCESS" if ok else "ERROR"
            self.log(f"{name}: {status} ({detail})", level)
            if not ok:
                all_ok = False
        
        return all_ok
    
    def run_test_suite(self, suite: str) -> Dict[str, Any]:
        """运行测试套件"""
        self.log(f"运行测试套件: {suite}", "TEST")
        
        cmd = ["python", "-m", "pytest", f"tests/test_user_journey.py", "-v", "-m", suite]
        
        start_time = time.time()
        code, stdout, stderr = self.run_command(cmd)
        duration = time.time() - start_time
        
        # 解析结果
        passed = code == 0
        
        result = {
            "suite": suite,
            "passed": passed,
            "duration": round(duration, 2),
            "exit_code": code,
            "output": stdout,
            "errors": stderr if stderr else None
        }
        
        if passed:
            self.log(f"{suite} 测试通过 ({duration:.1f}s)", "SUCCESS")
        else:
            self.log(f"{suite} 测试失败 ({duration:.1f}s)", "ERROR")
            if stderr:
                self.log(f"错误: {stderr[:200]}", "ERROR")
        
        return result
    
    def analyze_code_quality(self) -> Dict[str, Any]:
        """分析代码质量"""
        self.log("分析代码质量...", "AGENT")
        
        issues = []
        
        # 检查后端代码
        backend_dir = self.project_root / "backend" / "app"
        if backend_dir.exists():
            py_files = list(backend_dir.rglob("*.py"))
            
            # 检查是否有测试
            test_coverage = len(list(self.test_dir.rglob("test_*.py")))
            if test_coverage < 3:
                issues.append({
                    "type": "coverage",
                    "severity": "warning",
                    "message": f"测试覆盖率较低，仅有 {test_coverage} 个测试文件"
                })
            
            # 检查文件数量
            self.log(f"后端代码文件: {len(py_files)} 个", "INFO")
            self.log(f"测试文件: {test_coverage} 个", "INFO")
        
        # 检查前端代码
        frontend_dir = self.project_root / "frontend"
        if frontend_dir.exists():
            tsx_files = list(frontend_dir.rglob("*.tsx"))
            self.log(f"前端组件: {len(tsx_files)} 个", "INFO")
        
        return {
            "issues": issues,
            "backend_files": len(py_files) if backend_dir.exists() else 0,
            "test_files": test_coverage
        }
    
    def generate_report(self) -> str:
        """生成测试报告"""
        report_path = self.results_dir / f"agent_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)
        
        self.log(f"报告已生成: {report_path}", "SUCCESS")
        return str(report_path)
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 70)
        print("🤖 测试Agent报告摘要")
        print("=" * 70)
        
        # 测试统计
        tests = self.report.get("tests", [])
        passed = sum(1 for t in tests if t.get("passed"))
        total = len(tests)
        
        print(f"\n📊 测试结果: {passed}/{total} 通过")
        
        for test in tests:
            status = "✅" if test.get("passed") else "❌"
            suite = test.get("suite", "unknown")
            duration = test.get("duration", 0)
            print(f"   {status} {suite}: {duration:.1f}s")
        
        # 问题列表
        issues = self.report.get("issues", [])
        if issues:
            print(f"\n⚠️ 发现 {len(issues)} 个问题:")
            for issue in issues:
                severity = issue.get("severity", "info")
                message = issue.get("message", "")
                print(f"   [{severity.upper()}] {message}")
        
        # 建议
        recommendations = self.report.get("recommendations", [])
        if recommendations:
            print(f"\n💡 建议:")
            for rec in recommendations:
                print(f"   • {rec}")
        
        print("\n" + "=" * 70)
        
        if passed == total and not issues:
            print("🎉 所有检查通过！代码可以提交。")
        else:
            print("⚠️  发现问题，请修复后再提交。")
        
        print("=" * 70 + "\n")
    
    def run_full_check(self) -> bool:
        """运行完整检查"""
        self.log("开始完整测试检查...", "AGENT")
        print("-" * 70)
        
        # 1. 环境检查
        if not self.check_environment():
            self.log("环境检查失败，请启动服务", "ERROR")
            self.report["issues"].append({
                "type": "environment",
                "severity": "error",
                "message": "测试环境未就绪，请确保前后端服务已启动"
            })
            return False
        
        print("-" * 70)
        
        # 2. 运行冒烟测试
        smoke_result = self.run_test_suite("smoke")
        self.report["tests"].append(smoke_result)
        
        if not smoke_result["passed"]:
            self.report["issues"].append({
                "type": "test",
                "severity": "error",
                "message": "冒烟测试失败，核心功能可能存在问题"
            })
        
        print("-" * 70)
        
        # 3. 运行API测试
        api_result = self.run_test_suite("api")
        self.report["tests"].append(api_result)
        
        print("-" * 70)
        
        # 4. 代码质量分析
        quality = self.analyze_code_quality()
        self.report["code_quality"] = quality
        self.report["issues"].extend(quality.get("issues", []))
        
        print("-" * 70)
        
        # 5. 生成建议
        if not smoke_result["passed"]:
            self.report["recommendations"].append(
                "修复冒烟测试失败的问题后再继续开发"
            )
        
        if quality.get("test_files", 0) < 5:
            self.report["recommendations"].append(
                "增加测试覆盖率，建议为核心功能编写单元测试"
            )
        
        # 6. 生成报告
        report_path = self.generate_report()
        self.report["report_path"] = report_path
        
        # 7. 打印摘要
        self.print_summary()
        
        # 返回是否通过
        all_passed = all(t.get("passed") for t in self.report["tests"])
        return all_passed
    
    def watch_mode(self):
        """监听模式 - 监控代码变更并自动测试"""
        self.log("启动监听模式...", "AGENT")
        self.log("监控目录: backend/app, frontend", "INFO")
        
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            class CodeChangeHandler(FileSystemEventHandler):
                def __init__(self, agent):
                    self.agent = agent
                    self.last_run = 0
                
                def on_modified(self, event):
                    if event.is_directory:
                        return
                    
                    # 防抖：5秒内不重复运行
                    if time.time() - self.last_run < 5:
                        return
                    
                    # 只监控代码文件
                    if event.src_path.endswith(('.py', '.tsx', '.ts')):
                        self.agent.log(f"检测到变更: {event.src_path}", "INFO")
                        self.agent.run_full_check()
                        self.last_run = time.time()
            
            # 设置监控
            event_handler = CodeChangeHandler(self)
            observer = Observer()
            
            # 监控后端
            backend_dir = self.project_root / "backend" / "app"
            if backend_dir.exists():
                observer.schedule(event_handler, str(backend_dir), recursive=True)
            
            # 监控前端
            frontend_dir = self.project_root / "frontend"
            if frontend_dir.exists():
                observer.schedule(event_handler, str(frontend_dir), recursive=True)
            
            observer.start()
            self.log("监听已启动，按 Ctrl+C 停止", "SUCCESS")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                observer.stop()
                self.log("监听已停止", "INFO")
            
            observer.join()
            
        except ImportError:
            self.log("watchdog 未安装，无法使用监听模式", "ERROR")
            self.log("运行: pip install watchdog", "INFO")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="AI Career Co-pilot 测试Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python tests/test_agent.py           # 运行完整检查
  python tests/test_agent.py --watch   # 监听模式
  python tests/test_agent.py --quick   # 快速检查
        """
    )
    
    parser.add_argument("--watch", action="store_true", help="监听代码变更")
    parser.add_argument("--quick", action="store_true", help="快速检查（只检查环境）")
    
    args = parser.parse_args()
    
    agent = TestAgent()
    
    if args.watch:
        agent.watch_mode()
    elif args.quick:
        agent.check_environment()
    else:
        success = agent.run_full_check()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
