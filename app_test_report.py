"""
移动端应用功能测试脚本
使用 Playwright 对 AI Career Co-pilot App 进行全面测试
"""
from playwright.sync_api import sync_playwright
import os

BASE_URL = "http://localhost:3001"
SCREENSHOT_DIR = "e:/Desktop/AI Career Co-pilot/app_test_screenshots"

# 确保截图目录存在
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# 测试路由列表
ROUTES = [
    ("/", "根路由重定向"),
    ("/zh/login", "登录页"),
    ("/zh/register", "注册页"),
    ("/zh/dashboard", "首页/仪表盘"),
    ("/zh/vault", "经历总库"),
    ("/zh/jobs", "投递管理"),
    ("/zh/interview", "面试准备（未实现）"),
    ("/zh/settings", "设置（未实现）"),
    ("/zh/analytics", "数据分析（未实现）"),
    ("/zh/unknown", "不存在路由"),
]

# 移动端视口尺寸
VIEWPORTS = [
    {"name": "iPhone_SE", "width": 375, "height": 667},
    {"name": "iPhone_14", "width": 390, "height": 844},
    {"name": "Pixel_7", "width": 412, "height": 915},
]


def test_page_accessibility(page, route, name):
    """Phase 1: 页面可访问性测试"""
    print(f"\n[Phase 1] 测试: {name} ({route})")
    try:
        response = page.goto(f"{BASE_URL}{route}", wait_until="networkidle", timeout=15000)
        status = response.status if response else "No response"
        url = page.url
        print(f"  HTTP 状态: {status}")
        print(f"  最终 URL: {url}")

        # 截图
        safe_name = name.replace("/", "_").replace(" ", "_")
        screenshot_path = f"{SCREENSHOT_DIR}/01_access_{safe_name}.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"  截图: {screenshot_path}")

        # 检查页面内容
        title = page.title()
        body_text = page.locator("body").inner_text()[:200].replace("\n", " ")
        print(f"  页面标题: {title}")
        print(f"  页面内容: {body_text}...")

        return {
            "name": name,
            "route": route,
            "status": status,
            "final_url": url,
            "title": title,
            "screenshot": screenshot_path,
            "passed": status == 200 or (route == "/" and "/zh/dashboard" in url),
        }
    except Exception as e:
        print(f"  错误: {e}")
        return {
            "name": name,
            "route": route,
            "status": f"Error: {e}",
            "passed": False,
        }


def test_login_page(page):
    """Phase 2: 登录页功能测试"""
    print("\n[Phase 2] 测试: 登录页功能")
    results = []

    page.goto(f"{BASE_URL}/zh/login", wait_until="networkidle")
    page.set_viewport_size({"width": 390, "height": 844})

    # 1. 检查表单元素存在
    username_input = page.locator('input[type="text"]')
    password_input = page.locator('input[type="password"]')
    submit_btn = page.locator('button[type="submit"]')

    has_username = username_input.count() > 0
    has_password = password_input.count() > 0
    has_submit = submit_btn.count() > 0

    print(f"  用户名输入框: {'✓' if has_username else '✗'}")
    print(f"  密码输入框: {'✓' if has_password else '✗'}")
    print(f"  提交按钮: {'✓' if has_submit else '✗'}")

    results.append({"test": "表单元素存在", "passed": has_username and has_password and has_submit})

    # 2. 测试输入功能
    if has_username and has_password:
        username_input.fill("testuser")
        password_input.fill("testpass")
        print("  输入测试: ✓")
        results.append({"test": "表单输入", "passed": True})

        # 截图
        page.screenshot(path=f"{SCREENSHOT_DIR}/02_login_filled.png")

        # 3. 测试提交按钮（不实际提交，避免后端调用）
        if has_submit:
            is_disabled = submit_btn.is_disabled()
            print(f"  提交按钮禁用状态: {is_disabled}")
            results.append({"test": "提交按钮状态", "passed": not is_disabled})

    return results


def test_register_page(page):
    """Phase 2: 注册页功能测试"""
    print("\n[Phase 2] 测试: 注册页功能")
    results = []

    page.goto(f"{BASE_URL}/zh/register", wait_until="networkidle")
    page.set_viewport_size({"width": 390, "height": 844})

    # 检查表单元素
    inputs = page.locator('input').all()
    print(f"  输入框数量: {len(inputs)}")

    # 应该有 4 个输入框：用户名、邮箱、密码、确认密码
    has_4_inputs = len(inputs) == 4
    results.append({"test": "4个输入框", "passed": has_4_inputs})

    # 检查登录链接
    login_link = page.locator('a[href="/login"]')
    has_login_link = login_link.count() > 0
    print(f"  登录链接: {'✓' if has_login_link else '✗'}")
    results.append({"test": "登录链接", "passed": has_login_link})

    page.screenshot(path=f"{SCREENSHOT_DIR}/02_register.png")
    return results


def test_dashboard_page(page):
    """Phase 2: 首页功能测试"""
    print("\n[Phase 2] 测试: 首页功能")
    results = []

    page.goto(f"{BASE_URL}/zh/dashboard", wait_until="networkidle")
    page.set_viewport_size({"width": 390, "height": 844})

    # 检查欢迎语
    welcome = page.locator('text=欢迎使用 AI Career Co-pilot')
    has_welcome = welcome.count() > 0
    print(f"  欢迎语: {'✓' if has_welcome else '✗'}")
    results.append({"test": "欢迎语展示", "passed": has_welcome})

    # 检查快捷入口
    quick_actions = page.locator('a[href^="/"]').all()
    print(f"  快捷入口数量: {len(quick_actions)}")
    results.append({"test": "4个快捷入口", "passed": len(quick_actions) >= 4})

    # 测试点击跳转
    for action in quick_actions[:4]:
        href = action.get_attribute("href")
        print(f"  快捷入口: {href}")

    page.screenshot(path=f"{SCREENSHOT_DIR}/02_dashboard.png")
    return results


def test_vault_page(page):
    """Phase 2: 经历总库功能测试"""
    print("\n[Phase 2] 测试: 经历总库功能")
    results = []

    page.goto(f"{BASE_URL}/zh/vault", wait_until="networkidle")
    page.set_viewport_size({"width": 390, "height": 844})

    # 检查空状态
    empty_state = page.locator('text=暂无简历数据')
    has_empty = empty_state.count() > 0
    print(f"  空状态提示: {'✓' if has_empty else '✗'}")
    results.append({"test": "空状态展示", "passed": has_empty})

    # 检查功能特性展示
    features = ["智能解析", "结构管理", "精准匹配"]
    for feature in features:
        found = page.locator(f'text={feature}').count() > 0
        print(f"  特性 '{feature}': {'✓' if found else '✗'}")
        results.append({"test": f"特性-{feature}", "passed": found})

    page.screenshot(path=f"{SCREENSHOT_DIR}/02_vault.png")
    return results


def test_jobs_page(page):
    """Phase 2: 投递管理功能测试"""
    print("\n[Phase 2] 测试: 投递管理功能")
    results = []

    page.goto(f"{BASE_URL}/zh/jobs", wait_until="networkidle")
    page.set_viewport_size({"width": 390, "height": 844})

    # 检查空状态
    empty_state = page.locator('text=暂无投递记录')
    has_empty = empty_state.count() > 0
    print(f"  空状态提示: {'✓' if has_empty else '✗'}")
    results.append({"test": "空状态展示", "passed": has_empty})

    # 检查添加按钮
    add_btn = page.locator('a[href="/jobs/new"]')
    has_add = add_btn.count() > 0
    print(f"  添加按钮: {'✓' if has_add else '✗'}")
    results.append({"test": "添加按钮", "passed": has_add})

    page.screenshot(path=f"{SCREENSHOT_DIR}/02_jobs.png")
    return results


def test_bottom_navigation(page):
    """Phase 2: 底部导航栏测试"""
    print("\n[Phase 2] 测试: 底部导航栏")
    results = []

    page.goto(f"{BASE_URL}/zh/dashboard", wait_until="networkidle")
    page.set_viewport_size({"width": 390, "height": 844})

    # 检查导航项
    nav_items = ["首页", "总库", "投递", "面试", "设置"]
    for item in nav_items:
        found = page.locator(f'text={item}').count() > 0
        print(f"  导航项 '{item}': {'✓' if found else '✗'}")
        results.append({"test": f"导航项-{item}", "passed": found})

    # 测试点击跳转
    page.locator('text=总库').first.click()
    page.wait_for_load_state("networkidle")
    current_url = page.url
    is_vault = "/vault" in current_url
    print(f"  点击'总库'后 URL: {current_url} {'✓' if is_vault else '✗'}")
    results.append({"test": "导航跳转-总库", "passed": is_vault})

    page.screenshot(path=f"{SCREENSHOT_DIR}/02_nav_vault.png")

    # 测试高亮状态
    page.goto(f"{BASE_URL}/zh/dashboard", wait_until="networkidle")
    active_nav = page.locator('nav a').filter(has_text="首页")
    # 检查是否有激活样式（text-terra 类）
    has_active_style = page.locator('nav .text-terra').count() > 0
    print(f"  激活状态样式: {'✓' if has_active_style else '✗'}")
    results.append({"test": "导航激活状态", "passed": has_active_style})

    return results


def test_responsive_layout(page):
    """Phase 3: 响应式布局测试"""
    print("\n[Phase 3] 测试: 响应式布局")
    results = []

    for vp in VIEWPORTS:
        print(f"\n  视口: {vp['name']} ({vp['width']}x{vp['height']})")
        page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
        page.goto(f"{BASE_URL}/zh/dashboard", wait_until="networkidle")

        # 检查底部导航是否存在
        bottom_nav = page.locator('nav.fixed.bottom-0')
        has_nav = bottom_nav.count() > 0
        print(f"    底部导航: {'✓' if has_nav else '✗'}")

        # 检查页面头部是否存在
        header = page.locator('header.sticky')
        has_header = header.count() > 0
        print(f"    页面头部: {'✓' if has_header else '✗'}")

        # 截图
        page.screenshot(path=f"{SCREENSHOT_DIR}/03_responsive_{vp['name']}.png")

        results.append({
            "test": f"响应式-{vp['name']}",
            "passed": has_nav and has_header,
        })

    return results


def test_console_errors(page):
    """Phase 4: 控制台错误检查"""
    print("\n[Phase 4] 测试: 控制台错误检查")
    errors = []

    # 监听控制台消息
    page.on("console", lambda msg: errors.append(msg) if msg.type == "error" else None)

    # 访问所有主要页面
    for route, name in ROUTES[:6]:  # 只测试已实现的页面
        page.goto(f"{BASE_URL}{route}", wait_until="networkidle")
        page.wait_for_timeout(500)

    console_errors = [e for e in errors if e.type == "error"]
    print(f"  控制台错误数量: {len(console_errors)}")
    for err in console_errors[:5]:
        print(f"    - {err.text}")

    return {
        "test": "控制台错误",
        "passed": len(console_errors) == 0,
        "error_count": len(console_errors),
        "errors": [e.text for e in console_errors[:10]],
    }


def main():
    print("=" * 60)
    print("AI Career Co-pilot 移动端应用功能测试")
    print("=" * 60)

    all_results = {
        "accessibility": [],
        "functional": [],
        "responsive": [],
        "edge_cases": [],
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Phase 1: 页面可访问性测试
        print("\n" + "=" * 60)
        print("Phase 1: 页面可访问性测试")
        print("=" * 60)
        for route, name in ROUTES:
            result = test_page_accessibility(page, route, name)
            all_results["accessibility"].append(result)

        # Phase 2: 功能交互测试
        print("\n" + "=" * 60)
        print("Phase 2: 功能交互测试")
        print("=" * 60)
        all_results["functional"].extend(test_login_page(page))
        all_results["functional"].extend(test_register_page(page))
        all_results["functional"].extend(test_dashboard_page(page))
        all_results["functional"].extend(test_vault_page(page))
        all_results["functional"].extend(test_jobs_page(page))
        all_results["functional"].extend(test_bottom_navigation(page))

        # Phase 3: 响应式布局测试
        print("\n" + "=" * 60)
        print("Phase 3: 响应式布局测试")
        print("=" * 60)
        all_results["responsive"].extend(test_responsive_layout(page))

        # Phase 4: 边缘场景测试
        print("\n" + "=" * 60)
        print("Phase 4: 边缘场景测试")
        print("=" * 60)
        all_results["edge_cases"].append(test_console_errors(page))

        browser.close()

    # 生成测试报告
    print("\n" + "=" * 60)
    print("测试报告汇总")
    print("=" * 60)

    total_passed = 0
    total_tests = 0

    for category, results in all_results.items():
        print(f"\n【{category}】")
        for r in results:
            if isinstance(r, dict) and "passed" in r:
                status = "✓ 通过" if r["passed"] else "✗ 失败"
                test_name = r.get("test", r.get("name", "未知"))
                print(f"  {status} - {test_name}")
                total_tests += 1
                if r["passed"]:
                    total_passed += 1

    print(f"\n总计: {total_passed}/{total_tests} 通过 ({total_passed/total_tests*100:.1f}%)")
    print(f"截图保存位置: {SCREENSHOT_DIR}")

    return all_results


if __name__ == "__main__":
    main()
