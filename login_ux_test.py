"""
登录界面用户体验测试脚本
覆盖 Phase 1-7 完整测试流程
"""
from playwright.sync_api import sync_playwright, expect
import os
import time

BASE_URL = "http://localhost:3001"
SCREENSHOT_DIR = "e:/Desktop/AI Career Co-pilot/login_test_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# 全局测试结果
results = []

def log_result(phase, test_name, expected, actual, passed, severity="P2", fix_suggestion=""):
    results.append({
        "phase": phase,
        "test": test_name,
        "expected": expected,
        "actual": actual,
        "passed": passed,
        "severity": severity,
        "fix": fix_suggestion,
    })
    status = "✅ 通过" if passed else "❌ 失败"
    print(f"\n  [{status}] {test_name}")
    print(f"    预期: {expected}")
    print(f"    实际: {actual}")
    if not passed and fix_suggestion:
        print(f"    建议: {fix_suggestion}")


def phase1_page_loading(page):
    """Phase 1: 页面加载与元素完整性测试"""
    print("\n" + "=" * 60)
    print("Phase 1: 页面加载与元素完整性测试")
    print("=" * 60)

    # 1.1 页面加载
    start = time.time()
    page.goto(f"{BASE_URL}/zh/login", wait_until="networkidle")
    load_time = time.time() - start
    page.set_viewport_size({"width": 390, "height": 844})

    log_result("P1", "页面加载时间",
        "< 5秒", f"{load_time:.2f}秒",
        load_time < 5, "P1" if load_time >= 5 else "P3")

    # 截图
    page.screenshot(path=f"{SCREENSHOT_DIR}/p1_initial_load.png", full_page=True)

    # 1.2 检查页面标题
    title = page.title()
    log_result("P1", "页面标题",
        "AI Career Co-pilot", title,
        title == "AI Career Co-pilot", "P2")

    # 1.3 检查可见元素
    elements = {
        "页面标题文字": page.locator('h1:has-text("AI Career Co-pilot")'),
        "用户名标签": page.locator('label:has-text("用户名")'),
        "用户名输入框": page.locator('input[type="text"]'),
        "密码标签": page.locator('label:has-text("密码")'),
        "密码输入框": page.locator('input[type="password"]'),
        "登录按钮": page.locator('button[type="submit"]'),
        "表单元素": page.locator('form'),
    }

    for name, locator in elements.items():
        count = locator.count()
        log_result("P1", f"元素存在 - {name}",
            "存在", f"count={count}",
            count > 0, "P0" if name in ["用户名输入框", "密码输入框", "登录按钮"] else "P2")

    # 1.4 HTML 结构完整性
    html_has_lang = page.locator('html[lang]').count() > 0
    body_exists = page.locator('body').count() > 0
    log_result("P1", "HTML lang 属性",
        "存在", f"{'存在' if html_has_lang else '缺失'}",
        html_has_lang, "P2")
    log_result("P1", "body 标签存在",
        "存在", f"{'存在' if body_exists else '缺失'}",
        body_exists, "P0")

    # 1.5 CSS 样式检查
    card = page.locator('.rounded-2xl').first
    has_shadow = card.evaluate("el => getComputedStyle(el).boxShadow !== 'none'") if card.count() > 0 else False
    log_result("P1", "卡片阴影样式",
        "已应用", f"{'已应用' if has_shadow else '未应用'}",
        has_shadow, "P3")

    # 1.6 控制台错误
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    page.wait_for_timeout(500)
    log_result("P1", "控制台错误",
        "0 个", f"{len(console_errors)} 个",
        len(console_errors) == 0, "P1",
        f"错误详情: {console_errors[:3]}" if console_errors else "")


def phase2_form_validation(page):
    """Phase 2: 表单输入与验证测试"""
    print("\n" + "=" * 60)
    print("Phase 2: 表单输入与验证测试")
    print("=" * 60)

    page.goto(f"{BASE_URL}/zh/login", wait_until="networkidle")
    page.set_viewport_size({"width": 390, "height": 844})

    # 2.1 空表单提交
    submit_btn = page.locator('button[type="submit"]')
    # 记录提交前的 URL
    before_url = page.url
    submit_btn.click()
    page.wait_for_timeout(500)
    after_url = page.url
    # HTML5 验证会阻止提交，URL 不应变化
    log_result("P2", "空表单提交阻止",
        "URL 不变（HTML5 验证阻止）", f"URL {'未变' if before_url == after_url else '已变'}",
        before_url == after_url, "P1")

    page.screenshot(path=f"{SCREENSHOT_DIR}/p2_empty_form.png")

    # 2.2 仅输入用户名
    username = page.locator('input[type="text"]')
    password = page.locator('input[type="password"]')
    username.fill("testuser")
    before_url = page.url
    submit_btn.click()
    page.wait_for_timeout(500)
    after_url = page.url
    log_result("P2", "仅用户名提交阻止",
        "URL 不变（密码 required）", f"URL {'未变' if before_url == after_url else '已变'}",
        before_url == after_url, "P1")

    # 2.3 仅输入密码
    username.fill("")
    password.fill("testpass")
    before_url = page.url
    submit_btn.click()
    page.wait_for_timeout(500)
    after_url = page.url
    log_result("P2", "仅密码提交阻止",
        "URL 不变（用户名 required）", f"URL {'未变' if before_url == after_url else '已变'}",
        before_url == after_url, "P1")

    # 2.4 特殊字符输入
    username.fill("<script>alert(1)</script>")
    val = username.input_value()
    log_result("P2", "特殊字符输入",
        "正常显示", f"输入值: {val[:30]}...",
        "<script>" in val, "P2")

    # 2.5 超长输入
    long_text = "a" * 200
    username.fill(long_text)
    val = username.input_value()
    log_result("P2", "超长输入（200字符）",
        "正常输入无截断", f"长度: {len(val)}",
        len(val) == 200, "P3")

    # 2.6 密码可见性切换
    eye_icon = page.locator('[data-testid="eye-icon"], .eye-icon, button:has-text("👁")').count()
    log_result("P2", "密码可见性切换",
        "存在眼睛图标", f"{'存在' if eye_icon > 0 else '不存在'}",
        False, "建议", "添加 Eye/EyeOff 图标切换密码显示")

    # 2.7 输入框焦点样式
    username.focus()
    page.wait_for_timeout(200)
    focused = username.evaluate("el => el === document.activeElement")
    log_result("P2", "输入框焦点状态",
        "可获取焦点", f"{'是' if focused else '否'}",
        focused, "P1")

    page.screenshot(path=f"{SCREENSHOT_DIR}/p2_focused.png")


def phase3_submit_loading(page):
    """Phase 3: 提交与加载状态测试"""
    print("\n" + "=" * 60)
    print("Phase 3: 提交与加载状态测试")
    print("=" * 60)

    page.goto(f"{BASE_URL}/zh/login", wait_until="networkidle")
    page.set_viewport_size({"width": 390, "height": 844})

    username = page.locator('input[type="text"]')
    password = page.locator('input[type="password"]')
    submit_btn = page.locator('button[type="submit"]')

    # 3.1 填写表单并提交
    username.fill("testuser")
    password.fill("wrongpassword")

    # 3.2 检查 loading 状态
    submit_btn.click()
    page.wait_for_timeout(300)  # 等待状态更新

    is_disabled = submit_btn.is_disabled()
    has_spinner = page.locator('.animate-spin').count() > 0

    log_result("P3", "提交按钮禁用状态",
        "disabled=true", f"disabled={is_disabled}",
        is_disabled, "P1")
    log_result("P3", "Loading 旋转图标",
        "存在", f"{'存在' if has_spinner else '不存在'}",
        has_spinner, "P1")

    page.screenshot(path=f"{SCREENSHOT_DIR}/p3_loading.png")

    # 等待请求完成
    page.wait_for_timeout(3000)

    # 3.3 加载结束后按钮恢复
    is_disabled_after = submit_btn.is_disabled()
    log_result("P3", "加载结束后按钮恢复",
        "disabled=false", f"disabled={is_disabled_after}",
        not is_disabled_after, "P1")


def phase4_error_handling(page):
    """Phase 4: 错误提示测试"""
    print("\n" + "=" * 60)
    print("Phase 4: 错误提示测试")
    print("=" * 60)

    page.goto(f"{BASE_URL}/zh/login", wait_until="networkidle")
    page.set_viewport_size({"width": 390, "height": 844})

    username = page.locator('input[type="text"]')
    password = page.locator('input[type="password"]')
    submit_btn = page.locator('button[type="submit"]')

    # 4.1 错误凭据登录
    username.fill("nonexistent_user_12345")
    password.fill("wrongpassword")
    submit_btn.click()

    # 等待 toast 出现
    page.wait_for_timeout(2000)

    # 检查 toast 是否存在
    toast = page.locator('[data-sonner-toast]')
    has_toast = toast.count() > 0
    toast_text = toast.inner_text() if has_toast else "无 toast"

    log_result("P4", "错误凭据提示",
        "显示错误 toast", f"{'有' if has_toast else '无'} toast: {toast_text[:50]}",
        has_toast, "P1")

    page.screenshot(path=f"{SCREENSHOT_DIR}/p4_error_toast.png")

    # 4.2 Toast 位置检查
    toast_position = toast.evaluate("el => getComputedStyle(el).position") if has_toast else "N/A"
    log_result("P4", "Toast 定位方式",
        "fixed", toast_position,
        toast_position == "fixed", "P2")

    # 4.3 网络断开模拟（通过拦截请求）
    page.route("**/api/auth/login", lambda route: route.abort("internetdisconnected"))
    page.goto(f"{BASE_URL}/zh/login", wait_until="networkidle")
    username.fill("testuser")
    password.fill("testpass")
    submit_btn.click()
    page.wait_for_timeout(2000)

    toast_network = page.locator('[data-sonner-toast]')
    has_network_toast = toast_network.count() > 0
    network_text = toast_network.inner_text() if has_network_toast else "无 toast"

    log_result("P4", "网络断开提示",
        "显示网络错误 toast", f"{'有' if has_network_toast else '无'} toast: {network_text[:50]}",
        has_network_toast, "P2",
        "建议添加专门的网络断开错误文案")

    page.unroute("**/api/auth/login")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p4_network_error.png")


def phase5_success_flow(page):
    """Phase 5: 登录成功流程测试"""
    print("\n" + "=" * 60)
    print("Phase 5: 登录成功流程测试")
    print("=" * 60)

    page.goto(f"{BASE_URL}/zh/login", wait_until="networkidle")
    page.set_viewport_size({"width": 390, "height": 844})

    username = page.locator('input[type="text"]')
    password = page.locator('input[type="password"]')
    submit_btn = page.locator('button[type="submit"]')

    # 5.1 由于后端可能没有 testuser，先检查是否能正常处理
    username.fill("testuser")
    password.fill("testpass")
    submit_btn.click()
    page.wait_for_timeout(3000)

    # 检查 URL 是否跳转
    current_url = page.url
    did_redirect = "/dashboard" in current_url

    log_result("P5", "登录后跳转",
        "跳转到 /dashboard", f"当前 URL: {current_url}",
        did_redirect, "P1",
        "如果后端无此用户，需先创建测试账号")

    page.screenshot(path=f"{SCREENSHOT_DIR}/p5_after_login.png")

    # 5.2 检查 localStorage（如果跳转成功）
    if did_redirect:
        token = page.evaluate("() => localStorage.getItem('token')")
        log_result("P5", "Token 存储",
            "localStorage.token 存在", f"token={'存在' if token else '不存在'}",
            token is not None, "P0")
    else:
        log_result("P5", "Token 存储",
            "localStorage.token 存在", "未跳转，无法验证",
            False, "P0", "登录失败导致未存储 token")


def phase6_responsive(page):
    """Phase 6: 响应式与兼容性测试"""
    print("\n" + "=" * 60)
    print("Phase 6: 响应式与兼容性测试")
    print("=" * 60)

    viewports = [
        {"name": "iPhone_SE", "width": 375, "height": 667},
        {"name": "iPhone_14", "width": 390, "height": 844},
        {"name": "Pixel_7", "width": 412, "height": 915},
    ]

    for vp in viewports:
        page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
        page.goto(f"{BASE_URL}/zh/login", wait_until="networkidle")

        # 检查表单是否完整可见
        form = page.locator('form')
        form_visible = form.is_visible()
        btn_visible = page.locator('button[type="submit"]').is_visible()

        log_result("P6", f"视口适配 - {vp['name']} ({vp['width']}x{vp['height']})",
            "表单和按钮可见", f"表单={form_visible}, 按钮={btn_visible}",
            form_visible and btn_visible, "P1")

        page.screenshot(path=f"{SCREENSHOT_DIR}/p6_{vp['name']}.png")

    # 横屏测试
    page.set_viewport_size({"width": 844, "height": 390})
    page.goto(f"{BASE_URL}/zh/login", wait_until="networkidle")
    form_landscape = page.locator('form').is_visible()
    log_result("P6", "横屏模式适配",
        "表单可见", f"表单={form_landscape}",
        form_landscape, "P3")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p6_landscape.png")


def phase7_edge_cases(page):
    """Phase 7: 边缘场景测试"""
    print("\n" + "=" * 60)
    print("Phase 7: 边缘场景测试")
    print("=" * 60)

    # 7.1 直接访问 /login（无 locale）
    page.goto(f"{BASE_URL}/login", wait_until="networkidle")
    current_url = page.url
    has_locale = "/zh/" in current_url or "/en/" in current_url
    log_result("P7", "无 locale 访问重定向",
        "重定向到 /zh/login", f"当前 URL: {current_url}",
        has_locale, "P2")

    # 7.2 已登录状态访问登录页
    # 先模拟设置 token
    page.evaluate("() => localStorage.setItem('token', 'fake_token_123')")
    page.goto(f"{BASE_URL}/zh/login", wait_until="networkidle")
    current_url = page.url
    still_on_login = "/login" in current_url
    log_result("P7", "已登录用户访问登录页",
        "自动跳转到首页", f"当前 URL: {current_url}",
        not still_on_login, "P2",
        "建议添加：检查 localStorage token，存在则自动跳转 /dashboard")

    # 清除 token
    page.evaluate("() => localStorage.removeItem('token')")

    page.screenshot(path=f"{SCREENSHOT_DIR}/p7_edge_cases.png")


def generate_report():
    """生成测试报告"""
    print("\n" + "=" * 60)
    print("登录界面用户体验测试报告")
    print("=" * 60)

    passed = sum(1 for r in results if r["passed"])
    total = len(results)

    print(f"\n总计: {passed}/{total} 通过 ({passed/total*100:.1f}%)")

    # 按阶段分组
    phases = {}
    for r in results:
        phases.setdefault(r["phase"], []).append(r)

    for phase, items in phases.items():
        print(f"\n【{phase}】")
        for item in items:
            status = "✅" if item["passed"] else "❌"
            print(f"  {status} {item['test']} [{item['severity']}]")

    # 问题清单
    issues = [r for r in results if not r["passed"]]
    if issues:
        print(f"\n\n{'=' * 60}")
        print("发现的问题清单")
        print("=" * 60)
        for i, issue in enumerate(issues, 1):
            print(f"\n{i}. [{issue['severity']}] {issue['test']}")
            print(f"   预期: {issue['expected']}")
            print(f"   实际: {issue['actual']}")
            if issue['fix']:
                print(f"   修复建议: {issue['fix']}")

    print(f"\n截图保存位置: {SCREENSHOT_DIR}")
    return results


def main():
    print("=" * 60)
    print("AI Career Co-pilot 登录界面用户体验测试")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        phase1_page_loading(page)
        phase2_form_validation(page)
        phase3_submit_loading(page)
        phase4_error_handling(page)
        phase5_success_flow(page)
        phase6_responsive(page)
        phase7_edge_cases(page)

        browser.close()

    generate_report()


if __name__ == "__main__":
    main()
