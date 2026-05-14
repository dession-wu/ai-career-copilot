"""
系统功能验证测试脚本
覆盖登录功能及登录后核心功能模块
"""
from playwright.sync_api import sync_playwright
import os
import time

BASE_URL = "http://localhost:3001"
API_URL = "http://localhost:8001"
SCREENSHOT_DIR = "e:/Desktop/AI Career Co-pilot/functional_test_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

results = []

def log(phase, name, expected, actual, passed, severity="P2", fix=""):
    results.append({"phase": phase, "name": name, "expected": expected, "actual": actual, "passed": passed, "severity": severity, "fix": fix})
    status = "✅" if passed else "❌"
    print(f"\n  [{status}] {name} [{severity}]")
    print(f"    预期: {expected}")
    print(f"    实际: {actual}")
    if not passed and fix:
        print(f"    建议: {fix}")


def phase1_login(page):
    """Phase 1: 登录功能验证"""
    print("\n" + "=" * 60)
    print("Phase 1: 登录功能验证")
    print("=" * 60)

    # 1.1 页面可访问性
    start = time.time()
    page.goto(f"{BASE_URL}/zh/login", wait_until="networkidle")
    load_time = time.time() - start
    page.set_viewport_size({"width": 390, "height": 844})
    log("P1", "页面加载", "< 5秒", f"{load_time:.2f}秒", load_time < 5, "P0")

    # 1.2 元素完整性
    checks = {
        "用户名输入框": 'input[type="text"]',
        "密码输入框": 'input[type="password"]',
        "登录按钮": 'button[type="submit"]',
        "眼睛图标": 'button[type="button"]',
        "注册链接": 'a[href*="register"]',
    }
    for name, selector in checks.items():
        count = page.locator(selector).count()
        log("P1", f"元素存在 - {name}", ">0", str(count), count > 0, "P0" if name in ["用户名输入框", "密码输入框", "登录按钮"] else "P2")

    page.screenshot(path=f"{SCREENSHOT_DIR}/p1_login_page.png", full_page=True)

    # 1.3 空表单验证
    before = page.url
    page.locator('button[type="submit"]').click()
    page.wait_for_timeout(500)
    after = page.url
    log("P1", "空表单提交阻止", "URL不变", f"{'未变' if before == after else '已变'}", before == after, "P1")

    # 1.4 实时验证 - 用户名空值
    page.goto(f"{BASE_URL}/zh/login", wait_until="networkidle")
    username = page.locator('input[type="text"]')
    username.fill("")
    username.blur()
    page.wait_for_timeout(300)
    has_error = page.locator('text=请输入用户名').count() > 0
    log("P1", "用户名空值验证", "显示错误", f"{'有' if has_error else '无'}错误提示", has_error, "P1")

    # 1.5 实时验证 - 密码长度
    password = page.locator('input[type="password"]')
    password.fill("123")
    password.blur()
    page.wait_for_timeout(300)
    has_error = page.locator('text=密码至少 6 位').count() > 0
    log("P1", "密码长度验证", "显示错误", f"{'有' if has_error else '无'}错误提示", has_error, "P1")

    # 1.6 密码可见性切换
    page.goto(f"{BASE_URL}/zh/login", wait_until="networkidle")
    password = page.locator('input[type="password"]')
    password.fill("testpass")
    eye_btn = page.locator('button[type="button"]').first
    eye_btn.click()
    page.wait_for_timeout(200)
    is_text = page.locator('input[type="text"]').count() > 1  # 用户名 + 密码都变成 text
    log("P1", "密码可见性切换", "type=text", f"{'是' if is_text else '否'}", is_text, "P3")

    page.screenshot(path=f"{SCREENSHOT_DIR}/p1_password_visible.png")

    # 1.7 错误凭据登录
    page.goto(f"{BASE_URL}/zh/login", wait_until="networkidle")
    page.locator('input[type="text"]').fill("nonexistent_user_12345")
    page.locator('input[type="password"]').fill("wrongpassword")
    page.locator('button[type="submit"]').click()
    page.wait_for_timeout(2500)
    toast = page.locator('[data-sonner-toast]')
    has_toast = toast.count() > 0
    toast_text = toast.inner_text() if has_toast else "无toast"
    log("P1", "错误凭据提示", "显示错误toast", f"{'有' if has_toast else '无'}: {toast_text[:40]}", has_toast, "P1")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p1_error_toast.png")

    # 1.8 Loading 状态 — 使用 route 拦截并延迟响应，确保 loading 状态可见
    page.goto(f"{BASE_URL}/zh/login", wait_until="networkidle")
    
    # 1.8 Loading 状态 — 在浏览器端覆盖 XMLHttpRequest 来延迟响应
    # axios 使用 XMLHttpRequest 而非 fetch
    page.goto(f"{BASE_URL}/zh/login", wait_until="networkidle")
    
    page.evaluate("""
        () => {
            const OriginalXHR = window.XMLHttpRequest;
            window.__originalXHR = OriginalXHR;
            window.XMLHttpRequest = function() {
                const xhr = new OriginalXHR();
                const originalOpen = xhr.open;
                const originalSend = xhr.send;
                let url = '';
                xhr.open = function(method, reqUrl, ...args) {
                    url = reqUrl;
                    return originalOpen.call(xhr, method, reqUrl, ...args);
                };
                xhr.send = function(body) {
                    if (url.includes('/api/auth/login')) {
                        // 延迟 2 秒后返回 401
                        setTimeout(() => {
                            Object.defineProperty(xhr, 'status', { value: 401, writable: false });
                            Object.defineProperty(xhr, 'responseText', { value: JSON.stringify({detail: "Unauthorized"}), writable: false });
                            Object.defineProperty(xhr, 'readyState', { value: 4, writable: false });
                            if (xhr.onreadystatechange) xhr.onreadystatechange();
                            if (xhr.onloadend) xhr.onloadend();
                        }, 2000);
                    } else {
                        return originalSend.call(xhr, body);
                    }
                };
                return xhr;
            };
        }
    """)
    
    page.locator('input[type="text"]').fill("loading_test_user")
    page.locator('input[type="password"]').fill("loading_test_pass")
    page.locator('button[type="submit"]').click()
    
    # 等待 loading 状态出现（XHR 被延迟 2 秒）
    page.wait_for_timeout(500)
    
    is_disabled = page.locator('button[type="submit"]').is_disabled()
    has_spinner = page.locator('.animate-spin').count() > 0
    
    log("P1", "Loading状态-禁用", "disabled", f"{is_disabled}", is_disabled, "P1")
    log("P1", "Loading状态-旋转图标", "存在", f"{'有' if has_spinner else '无'}", has_spinner, "P1")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p1_loading.png")

    # 恢复 XHR 并等待延迟响应完成
    page.evaluate("""
        () => {
            if (window.__originalXHR) {
                window.XMLHttpRequest = window.__originalXHR;
                window.__originalXHR = null;
            }
        }
    """)
    page.wait_for_timeout(2500)

    # 1.9 已登录用户自动跳转
    page.evaluate("() => localStorage.setItem('token', 'fake_token_test')")
    page.goto(f"{BASE_URL}/zh/login", wait_until="networkidle")
    page.wait_for_timeout(1500)
    current = page.url
    is_dashboard = "/dashboard" in current
    log("P1", "已登录自动跳转", "跳转到dashboard", f"URL: {current}", is_dashboard, "P2")
    page.evaluate("() => localStorage.removeItem('token')")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p1_auto_redirect.png")


def phase2_register(page):
    """Phase 2: 注册功能验证"""
    print("\n" + "=" * 60)
    print("Phase 2: 注册功能验证")
    print("=" * 60)

    page.goto(f"{BASE_URL}/zh/register", wait_until="networkidle")
    page.set_viewport_size({"width": 390, "height": 844})

    # 2.1 元素完整性
    inputs = page.locator('input').count()
    has_submit = page.locator('button[type="submit"]').count() > 0
    has_login_link = page.locator('a[href*="login"]').count() > 0
    log("P2", "注册页-4个输入框", "4", str(inputs), inputs == 4, "P0")
    log("P2", "注册页-提交按钮", "存在", f"{'有' if has_submit else '无'}", has_submit, "P0")
    log("P2", "注册页-登录链接", "存在", f"{'有' if has_login_link else '无'}", has_login_link, "P3")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p2_register_page.png", full_page=True)

    # 2.2 密码匹配验证 — 先填写所有必填字段
    page.locator('input[type="text"]').fill("testuser")
    page.locator('input[type="email"]').fill("test@example.com")
    page.locator('input[type="password"]').nth(0).fill("password1")
    page.locator('input[type="password"]').nth(1).fill("password2")
    page.locator('button[type="submit"]').click()
    page.wait_for_timeout(1500)  # 增加等待时间让 toast 出现
    toast = page.locator('[data-sonner-toast]')
    has_toast = toast.count() > 0
    toast_text = toast.inner_text() if has_toast else "无"
    log("P2", "密码不匹配提示", "显示toast", f"{'有' if has_toast else '无'}: {toast_text[:30]}", has_toast, "P1")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p2_password_mismatch.png")


def phase3_post_login(page):
    """Phase 3: 登录后核心功能验证"""
    print("\n" + "=" * 60)
    print("Phase 3: 登录后核心功能验证")
    print("=" * 60)

    # 先模拟登录状态
    page.evaluate("() => localStorage.setItem('token', 'test_token')")

    # 3.1 首页加载
    page.goto(f"{BASE_URL}/zh/dashboard", wait_until="networkidle")
    page.set_viewport_size({"width": 390, "height": 844})
    # 移除 Next.js dev overlay（开发模式错误遮罩层会拦截点击）
    page.evaluate("""
        () => {
            const overlay = document.querySelector('nextjs-portal');
            if (overlay) overlay.remove();
        }
    """)
    has_welcome = page.locator('text=欢迎回来').count() > 0
    has_stats = page.locator('text=本周投递').count() > 0
    has_todos = page.locator('text=今日待办').count() > 0
    log("P3", "首页-欢迎语", "存在", f"{'有' if has_welcome else '无'}", has_welcome, "P1")
    log("P3", "首页-数据概览", "存在", f"{'有' if has_stats else '无'}", has_stats, "P1")
    log("P3", "首页-今日待办", "存在", f"{'有' if has_todos else '无'}", has_todos, "P1")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p3_dashboard.png", full_page=True)

    # 3.2 数据概览跳转 - 点击"本周投递"进入求职页
    page.locator('text=本周投递').first.click()
    page.wait_for_timeout(1500)
    is_jobs = "/jobs" in page.url
    log("P3", "跳转-数据概览", "URL含/jobs", f"URL: {page.url}", is_jobs, "P1")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p3_jobs_click.png")

    # 3.3 经历总库内容
    page.goto(f"{BASE_URL}/zh/vault", wait_until="networkidle")
    has_empty = page.locator('text=暂无简历数据').count() > 0
    has_features = page.locator('text=智能解析').count() > 0
    log("P3", "总库-空状态", "存在", f"{'有' if has_empty else '无'}", has_empty, "P2")
    log("P3", "总库-特性展示", "存在", f"{'有' if has_features else '无'}", has_features, "P2")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p3_vault.png")

    # 3.4 投递管理
    page.goto(f"{BASE_URL}/zh/jobs", wait_until="networkidle")
    page.wait_for_timeout(500)  # 等待页面完全渲染
    has_empty = page.locator('text=暂无投递记录').count() > 0
    # Link 组件渲染后可能不是标准 <a> 标签，使用更通用的选择器
    has_add = page.locator('a[href*="/jobs/new"]').count() > 0 or page.locator('button, a').filter(has_text="+").count() > 0
    # 检查 Plus 图标所在的链接/按钮
    if not has_add:
        has_add = page.locator('svg.lucide-plus').count() > 0
    log("P3", "投递-空状态", "存在", f"{'有' if has_empty else '无'}", has_empty, "P2")
    log("P3", "投递-添加按钮", "存在", f"{'有' if has_add else '无'}", has_add, "P2")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p3_jobs.png")

    # 3.5 底部导航
    page.goto(f"{BASE_URL}/zh/dashboard", wait_until="networkidle")
    # 移除 dev overlay
    page.evaluate("""
        () => {
            const overlay = document.querySelector('nextjs-portal');
            if (overlay) overlay.remove();
        }
    """)
    nav_items = ["首页", "简历", "求职", "数据", "我的"]
    for item in nav_items:
        found = page.locator(f'text={item}').count() > 0
        log("P3", f"导航-{item}", "存在", f"{'有' if found else '无'}", found, "P1" if item == "首页" else "P2")

    # 点击导航跳转 - 简历 (使用 nav a 选择器避免 dev overlay 拦截)
    page.locator('nav a[href*="/vault"]').click()
    page.wait_for_timeout(1500)
    is_vault = "/vault" in page.url
    log("P3", "导航点击-简历", "跳转到vault", f"URL: {page.url}", is_vault, "P1")

    # 点击导航跳转 - 数据
    page.goto(f"{BASE_URL}/zh/dashboard", wait_until="networkidle")
    page.evaluate("() => { const o = document.querySelector('nextjs-portal'); if(o) o.remove(); }")
    page.locator('nav a[href*="/analytics"]').click()
    page.wait_for_timeout(1500)
    is_analytics = "/analytics" in page.url
    log("P3", "导航点击-数据", "跳转到analytics", f"URL: {page.url}", is_analytics, "P1")

    # 点击导航跳转 - 我的
    page.goto(f"{BASE_URL}/zh/dashboard", wait_until="networkidle")
    page.evaluate("() => { const o = document.querySelector('nextjs-portal'); if(o) o.remove(); }")
    page.locator('nav a[href*="/settings"]').click()
    page.wait_for_timeout(1500)
    is_settings = "/settings" in page.url
    log("P3", "导航点击-我的", "跳转到settings", f"URL: {page.url}", is_settings, "P1")

    # 激活状态
    page.goto(f"{BASE_URL}/zh/dashboard", wait_until="networkidle")
    active = page.locator('nav .text-terra').count() > 0
    log("P3", "导航-激活状态", "高亮样式", f"{'有' if active else '无'}text-terra", active, "P2")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p3_nav_active.png")


def phase4_edge_cases(page):
    """Phase 4: 边缘场景验证"""
    print("\n" + "=" * 60)
    print("Phase 4: 边缘场景验证")
    print("=" * 60)

    # 4.1 新页面验证 (interview, settings 页面已创建)
    page.goto(f"{BASE_URL}/zh/interview", wait_until="networkidle")
    has_content = page.locator('text=面试准备').count() > 0
    log("P4", "面试页面", "正常显示", f"{'是' if has_content else '否'}", has_content, "P2")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p4_interview.png")

    page.goto(f"{BASE_URL}/zh/settings", wait_until="networkidle")
    has_content = page.locator('text=我的').count() > 0
    log("P4", "设置页面", "正常显示", f"{'是' if has_content else '否'}", has_content, "P2")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p4_settings.png")

    # 4.2 直接访问 /login
    page.goto(f"{BASE_URL}/login", wait_until="networkidle")
    page.wait_for_timeout(1000)
    current = page.url
    has_locale = "/zh/" in current or "/en/" in current
    log("P4", "无locale重定向", "含/zh/", f"URL: {current}", has_locale, "P2")

    # 4.3 控制台错误 - 收集并检查
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    for route in ["/zh/login", "/zh/register", "/zh/dashboard", "/zh/vault", "/zh/jobs"]:
        page.goto(f"{BASE_URL}{route}", wait_until="networkidle")
        page.wait_for_timeout(300)
    log("P4", "控制台JS错误", "0个", f"{len(console_errors)}个", len(console_errors) == 0, "P1")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p4_console.png")


def generate_report():
    print("\n" + "=" * 60)
    print("功能验证测试报告")
    print("=" * 60)

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f"\n总计: {passed}/{total} 通过 ({passed/total*100:.1f}%)")

    phases = {}
    for r in results:
        phases.setdefault(r["phase"], []).append(r)

    for phase, items in phases.items():
        p = sum(1 for i in items if i["passed"])
        print(f"\n【{phase}】{p}/{len(items)} 通过")
        for item in items:
            status = "✅" if item["passed"] else "❌"
            print(f"  {status} {item['name']} [{item['severity']}]")

    issues = [r for r in results if not r["passed"]]
    if issues:
        print(f"\n\n{'=' * 60}")
        print("问题清单")
        print("=" * 60)
        for i, issue in enumerate(issues, 1):
            print(f"\n{i}. [{issue['severity']}] {issue['name']}")
            print(f"   预期: {issue['expected']}")
            print(f"   实际: {issue['actual']}")
            if issue['fix']:
                print(f"   建议: {issue['fix']}")

    print(f"\n截图保存: {SCREENSHOT_DIR}")
    return results


def main():
    print("=" * 60)
    print("AI Career Co-pilot 系统功能验证测试")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        phase1_login(page)
        phase2_register(page)
        phase3_post_login(page)
        phase4_edge_cases(page)

        browser.close()

    generate_report()


if __name__ == "__main__":
    main()
