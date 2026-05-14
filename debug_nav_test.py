from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3001"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 390, "height": 844})
    page = context.new_page()

    # 监听控制台消息
    errors = []
    def on_console(msg):
        if msg.type == "error":
            errors.append(msg.text)
            print(f"[CONSOLE ERROR] {msg.text}")
        elif msg.type == "warning":
            print(f"[CONSOLE WARN] {msg.text}")

    page.on("console", on_console)
    page.on("pageerror", lambda err: print(f"[PAGE ERROR] {err}"))

    # 模拟登录
    page.goto(f"{BASE_URL}/zh/login", wait_until="networkidle")
    page.evaluate("() => localStorage.setItem('token', 'test_token')")

    # 访问首页
    page.goto(f"{BASE_URL}/zh/dashboard", wait_until="networkidle")
    page.wait_for_timeout(2000)

    print(f"\nTotal console errors: {len(errors)}")
    for i, err in enumerate(errors[:10]):
        print(f"  {i+1}. {err[:200]}")

    browser.close()
