"""
Pytest配置和共享fixtures
"""

import pytest
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from typing import Generator, Dict, Any
import requests
import time

# 测试配置
TEST_CONFIG = {
    "base_url": os.getenv("TEST_BASE_URL", "http://localhost:3000"),
    "api_url": os.getenv("TEST_API_URL", "http://localhost:8000"),
    "headless": os.getenv("TEST_HEADLESS", "true").lower() == "true",
    "slow_mo": int(os.getenv("TEST_SLOW_MO", "0")),
    "viewport": {"width": 1280, "height": 720},
}


@pytest.fixture(scope="session")
def browser() -> Generator[Browser, None, None]:
    """创建浏览器实例（会话级别）"""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=TEST_CONFIG["headless"],
            slow_mo=TEST_CONFIG["slow_mo"]
        )
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """创建浏览器上下文（每个测试函数）"""
    context = browser.new_context(
        viewport=TEST_CONFIG["viewport"],
        record_video_dir="test-results/videos" if not TEST_CONFIG["headless"] else None
    )
    
    # 启用控制台日志捕获
    context.on("console", lambda msg: print(f"[Console {msg.type}]: {msg.text}"))
    
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Generator[Page, None, None]:
    """创建页面实例"""
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture(scope="session")
def api_client() -> Generator[requests.Session, None, None]:
    """API测试客户端"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json"
    })
    yield session
    session.close()


@pytest.fixture(scope="function")
def test_user() -> Dict[str, str]:
    """测试用户数据"""
    timestamp = int(time.time())
    return {
        "username": f"testuser_{timestamp}",
        "email": f"test_{timestamp}@example.com",
        "password": "Test123456!"
    }


@pytest.fixture(scope="function")
def authenticated_page(page: Page, api_client: requests.Session, test_user: Dict[str, str]) -> Page:
    """已认证的页面（自动登录）"""
    # 注册并登录
    register_response = api_client.post(
        f"{TEST_CONFIG['api_url']}/api/auth/register",
        json=test_user
    )
    
    if register_response.status_code not in [200, 201, 400]:  # 400可能是用户已存在
        raise Exception(f"注册失败: {register_response.text}")
    
    # 登录获取token
    login_response = api_client.post(
        f"{TEST_CONFIG['api_url']}/api/auth/login",
        data={
            "username": test_user["email"],
            "password": test_user["password"]
        }
    )
    
    if login_response.status_code != 200:
        raise Exception(f"登录失败: {login_response.text}")
    
    token = login_response.json()["access_token"]
    
    # 设置localStorage
    page.goto(TEST_CONFIG["base_url"])
    page.evaluate(f"""
        localStorage.setItem('token', '{token}');
        localStorage.setItem('user', '{test_user["username"]}');
    """)
    
    return page


# 自定义pytest标记
def pytest_configure(config):
    """配置pytest"""
    config.addinivalue_line("markers", "smoke: 冒烟测试")
    config.addinivalue_line("markers", "e2e: 端到端测试")
    config.addinivalue_line("markers", "api: API测试")
    config.addinivalue_line("markers", "hallucination: 防幻觉测试")
    config.addinivalue_line("markers", "slow: 慢速测试")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """测试失败时自动截图"""
    outcome = yield
    report = outcome.get_result()
    
    if report.when == "call" and report.failed:
        # 获取page fixture
        page = item.funcargs.get("page")
        if page:
            screenshot_dir = Path("test-results/screenshots")
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = screenshot_dir / f"{item.name}.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"\n📸 截图已保存: {screenshot_path}")
