"""
验证登录页面是否正常显示
"""
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3001"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.set_viewport_size({"width": 390, "height": 844})

    page.goto(f"{BASE_URL}/zh/login", wait_until="networkidle")

    # 检查关键元素
    title = page.title()
    h1 = page.locator('h1').inner_text() if page.locator('h1').count() > 0 else "NO H1"
    username = page.locator('input[type="text"]').count()
    password = page.locator('input[type="password"]').count()
    submit = page.locator('button[type="submit"]').count()
    eye = page.locator('button').filter(has_text="").count()
    register_link = page.locator('a[href*="register"]').count()

    print(f"Page title: {title}")
    print(f"H1 text: {h1}")
    print(f"Username input: {username}")
    print(f"Password input: {password}")
    print(f"Submit button: {submit}")
    print(f"Register link: {register_link}")

    # 截图
    page.screenshot(path="e:/Desktop/AI Career Co-pilot/login_test_screenshots/verify_login.png", full_page=True)
    print("Screenshot saved!")

    browser.close()
