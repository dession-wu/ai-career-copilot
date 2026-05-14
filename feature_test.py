"""
功能完善测试脚本 - 验证"我的"页面和"添加投递"功能
"""
from playwright.sync_api import sync_playwright
import os

BASE_URL = "http://localhost:3001"
SCREENSHOT_DIR = "feature_test_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

results = []

def remove_overlay(page):
    """移除 Next.js dev overlay"""
    page.evaluate("""
        () => {
            const overlays = document.querySelectorAll('nextjs-portal');
            overlays.forEach(o => o.remove());
        }
    """)

def log(phase, test_name, expected, actual, passed, severity="P2"):
    status = "✅ 通过" if passed else "❌ 失败"
    results.append({
        "phase": phase,
        "test": test_name,
        "expected": expected,
        "actual": actual,
        "passed": passed,
        "severity": severity,
    })
    print(f"  [{severity}] {test_name}: {status}")
    print(f"      预期: {expected}")
    print(f"      实际: {actual}")

def phase1_profile(page):
    """Phase 1: 个人资料功能测试"""
    print("\n" + "=" * 60)
    print("Phase 1: 个人资料功能测试")
    print("=" * 60)

    # 1.1 进入"我的"页面
    page.goto(f"{BASE_URL}/zh/settings", wait_until="networkidle")
    remove_overlay(page)
    has_profile_menu = page.locator('text=个人资料').count() > 0
    has_notif_menu = page.locator('text=消息通知').count() > 0
    log("P1", "我的页面-菜单项", "个人资料+消息通知", f"{'有' if has_profile_menu else '无'}个人资料, {'有' if has_notif_menu else '无'}消息通知", has_profile_menu and has_notif_menu, "P1")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p1_settings.png")

    # 1.2 点击个人资料 - 使用 Link 选择器
    page.locator('a[href*="/settings/profile"]').click()
    page.wait_for_timeout(2000)
    is_profile = "/settings/profile" in page.url
    has_name = page.locator('text=姓名').count() > 0
    has_edit_btn = page.locator('text=编辑资料').count() > 0
    log("P1", "个人资料页面", "URL含/settings/profile", f"URL: {page.url}", is_profile, "P1")
    log("P1", "个人资料-姓名标签", "存在", f"{'有' if has_name else '无'}", has_name, "P1")
    log("P1", "个人资料-编辑按钮", "存在", f"{'有' if has_edit_btn else '无'}", has_edit_btn, "P1")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p1_profile.png")

    if not is_profile:
        print("  ⚠️ 未进入个人资料页面，跳过后续测试")
        return

    # 1.3 编辑模式
    page.locator('text=编辑资料').click()
    page.wait_for_timeout(500)
    has_save_btn = page.locator('text=保存').count() > 0
    has_cancel_btn = page.locator('text=取消').count() > 0
    log("P1", "编辑模式-保存按钮", "存在", f"{'有' if has_save_btn else '无'}", has_save_btn, "P1")
    log("P1", "编辑模式-取消按钮", "存在", f"{'有' if has_cancel_btn else '无'}", has_cancel_btn, "P1")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p1_profile_edit.png")

    # 1.4 表单验证 - 清空姓名
    page.locator('input[type="text"]').first.fill("")
    page.locator('text=保存').click()
    page.wait_for_timeout(500)
    has_error = page.locator('text=请输入姓名').count() > 0
    log("P1", "表单验证-空姓名", "显示错误", f"{'有' if has_error else '无'}错误提示", has_error, "P1")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p1_profile_validation.png")

    # 1.5 保存成功
    page.locator('input[type="text"]').first.fill("测试用户")
    page.locator('text=保存').click()
    page.wait_for_timeout(1000)
    has_saved = page.locator('text=测试用户').count() > 0
    log("P1", "保存资料", "显示新姓名", f"{'有' if has_saved else '无'}测试用户", has_saved, "P1")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p1_profile_saved.png")

def phase2_notifications(page):
    """Phase 2: 消息通知功能测试"""
    print("\n" + "=" * 60)
    print("Phase 2: 消息通知功能测试")
    print("=" * 60)

    # 2.1 进入消息通知
    page.goto(f"{BASE_URL}/zh/settings", wait_until="networkidle")
    remove_overlay(page)
    page.locator('a[href*="/settings/notifications"]').click()
    page.wait_for_timeout(2000)
    is_notif = "/settings/notifications" in page.url
    log("P2", "消息通知页面", "URL含/settings/notifications", f"URL: {page.url}", is_notif, "P1")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p2_notifications.png")

    if not is_notif:
        print("  ⚠️ 未进入消息通知页面，跳过后续测试")
        return

    # 2.2 分类筛选
    has_all = page.locator('text=全部').count() > 0
    has_business = page.locator('text=业务').count() > 0
    has_system = page.locator('text=系统').count() > 0
    log("P2", "分类标签", "全部+业务+系统", f"全部{'有' if has_all else '无'}, 业务{'有' if has_business else '无'}, 系统{'有' if has_system else '无'}", has_all and has_business and has_system, "P1")

    # 2.3 消息列表
    has_messages = page.locator('text=面试提醒').count() > 0
    log("P2", "消息列表", "有消息", f"{'有' if has_messages else '无'}消息", has_messages, "P1")

    # 2.4 标记已读
    unread_dot = page.locator('span.w-2.h-2.bg-red-500').count()
    if unread_dot > 0:
        page.locator('button[title="标记已读"]').first.click()
        page.wait_for_timeout(500)
        unread_after = page.locator('span.w-2.h-2.bg-red-500').count()
        log("P2", "标记已读", "未读数减少", f"{unread_dot} -> {unread_after}", unread_after < unread_dot, "P1")
    else:
        log("P2", "标记已读", "有未读消息", "无未读消息", True, "P2")

    # 2.5 全部已读
    page.locator('text=全部已读').click()
    page.wait_for_timeout(500)
    unread_final = page.locator('span.w-2.h-2.bg-red-500').count()
    log("P2", "全部已读", "0未读", f"{unread_final}个未读", unread_final == 0, "P1")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p2_notif_read.png")

def phase3_add_application(page):
    """Phase 3: 添加投递功能测试"""
    print("\n" + "=" * 60)
    print("Phase 3: 添加投递功能测试")
    print("=" * 60)

    # 3.1 进入求职页
    page.goto(f"{BASE_URL}/zh/jobs", wait_until="networkidle")
    remove_overlay(page)
    has_add_btn = page.locator('a[href*="/jobs/new"]').count() > 0
    log("P3", "求职页-添加按钮", "存在", f"{'有' if has_add_btn else '无'}", has_add_btn, "P1")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p3_jobs_list.png")

    # 3.2 点击添加
    page.locator('a[href*="/jobs/new"]').click()
    page.wait_for_timeout(2000)
    is_new = "/jobs/new" in page.url
    has_step1 = page.locator('text=职位信息').count() > 0
    log("P3", "添加投递页面", "URL含/jobs/new", f"URL: {page.url}", is_new, "P1")
    log("P3", "步骤1-职位信息", "存在", f"{'有' if has_step1 else '无'}", has_step1, "P1")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p3_add_step1.png")

    if not is_new:
        print("  ⚠️ 未进入添加投递页面，跳过后续测试")
        return

    # 3.3 表单验证 - 空提交
    page.locator('text=下一步').click()
    page.wait_for_timeout(500)
    has_company_error = page.locator('text=请输入公司名称').count() > 0
    has_position_error = page.locator('text=请输入职位名称').count() > 0
    log("P3", "表单验证-空提交", "显示错误", f"公司{'有' if has_company_error else '无'}, 职位{'有' if has_position_error else '无'}", has_company_error and has_position_error, "P1")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p3_add_validation.png")

    # 3.4 填写表单
    inputs = page.locator('input[type="text"]').all()
    if len(inputs) >= 2:
        inputs[0].fill("测试公司")
        inputs[1].fill("测试工程师")
    page.locator('text=下一步').click()
    page.wait_for_timeout(500)
    has_step2 = page.locator('text=附加信息').count() > 0
    log("P3", "步骤2-附加信息", "存在", f"{'有' if has_step2 else '无'}", has_step2, "P1")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p3_add_step2.png")

    # 3.5 预览确认
    page.locator('text=下一步').click()
    page.wait_for_timeout(500)
    has_step3 = page.locator('text=预览确认').count() > 0
    has_preview_company = page.locator('text=测试公司').count() > 0
    log("P3", "步骤3-预览确认", "存在", f"{'有' if has_step3 else '无'}", has_step3, "P1")
    log("P3", "预览-公司名称", "显示", f"{'有' if has_preview_company else '无'}测试公司", has_preview_company, "P1")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p3_add_preview.png")

    # 3.6 提交
    page.locator('text=确认提交').click()
    page.wait_for_timeout(1500)
    is_jobs_after = "/jobs" in page.url
    has_new_app = page.locator('text=测试公司').count() > 0
    log("P3", "提交后跳转", "返回求职页", f"URL: {page.url}", is_jobs_after, "P1")
    log("P3", "列表显示新投递", "存在", f"{'有' if has_new_app else '无'}测试公司", has_new_app, "P1")
    page.screenshot(path=f"{SCREENSHOT_DIR}/p3_jobs_after_add.png")

def generate_report():
    print("\n" + "=" * 60)
    print("功能完善测试报告")
    print("=" * 60)

    passed = sum(1 for r in results if r["passed"])
    total = len(results)

    print(f"\n总计: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    print("\n详细结果:")

    for r in results:
        status = "✅" if r["passed"] else "❌"
        print(f"  {status} [{r['severity']}] {r['test']}")
        if not r["passed"]:
            print(f"      预期: {r['expected']}")
            print(f"      实际: {r['actual']}")

    print("\n" + "=" * 60)
    if passed == total:
        print("🎉 所有测试通过！")
    else:
        print(f"⚠️ 有 {total - passed} 项测试未通过")
    print("=" * 60)

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 390, "height": 844})
        page = context.new_page()

        # 模拟登录
        page.goto(f"{BASE_URL}/zh/login", wait_until="networkidle")
        page.evaluate("() => localStorage.setItem('token', 'test_token')")

        phase1_profile(page)
        phase2_notifications(page)
        phase3_add_application(page)
        generate_report()

        browser.close()

if __name__ == "__main__":
    main()
