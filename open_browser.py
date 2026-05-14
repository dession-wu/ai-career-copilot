from playwright.sync_api import sync_playwright
import subprocess
import time

# 启动浏览器并打开登录页面
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--window-size=430,900'])
    context = browser.new_context(viewport={"width": 390, "height": 844})
    page = context.new_page()
    page.goto("http://localhost:3001/zh/login")
    print("浏览器已打开，访问: http://localhost:3001/zh/login")
    print("请手动操作浏览器进行测试。按 Enter 键关闭浏览器...")
    input()
    browser.close()
