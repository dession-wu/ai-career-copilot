"""
调试测试：检查 401 响应的详细信息
"""
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3001"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.set_viewport_size({"width": 390, "height": 844})

    # 监听所有网络请求
    def handle_route(route, request):
        if "api/auth/login" in request.url:
            print(f"\n[Request] {request.method} {request.url}")
            print(f"[Headers] {request.headers}")
        route.continue_()

    def handle_response(response):
        if "api/auth/login" in response.url:
            print(f"\n[Response] {response.status} {response.url}")
            print(f"[Headers] {dict(response.headers)}")
            try:
                body = response.body()
                print(f"[Body] {body.decode('utf-8')}")
            except:
                print("[Body] Could not read body")

    page.route("**/*", handle_route)
    page.on("response", handle_response)

    # 监听控制台
    page.on("console", lambda msg: print(f"[Console {msg.type}] {msg.text}"))

    page.goto(f"{BASE_URL}/zh/login", wait_until="networkidle")

    # 填写错误凭据并提交
    page.locator('input[type="text"]').fill("nonexistent_user_12345")
    page.locator('input[type="password"]').fill("wrongpassword")
    page.locator('button[type="submit"]').click()

    # 等待一段时间观察
    page.wait_for_timeout(4000)

    # 截图
    page.screenshot(path="e:/Desktop/AI Career Co-pilot/login_test_screenshots/debug_401.png")

    # 检查 toast
    toast = page.locator('[data-sonner-toast]')
    print(f"\n[Toast] count={toast.count()}")
    if toast.count() > 0:
        print(f"[Toast text] {toast.inner_text()}")

    browser.close()
