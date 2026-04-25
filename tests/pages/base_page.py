"""
基础页面类 - Page Object Model
"""

from playwright.sync_api import Page, Locator, expect
from typing import Optional, List
import os


class BasePage:
    """基础页面类"""
    
    def __init__(self, page: Page):
        self.page = page
        self.base_url = os.getenv("TEST_BASE_URL", "http://localhost:3000")
    
    def goto(self, path: str = ""):
        """导航到页面"""
        self.page.goto(f"{self.base_url}{path}")
        return self
    
    def wait_for_load(self):
        """等待页面加载完成"""
        self.page.wait_for_load_state("networkidle")
        return self
    
    def get_by_test_id(self, test_id: str) -> Locator:
        """通过data-testid获取元素"""
        return self.page.get_by_test_id(test_id)
    
    def get_by_role(self, role: str, name: Optional[str] = None) -> Locator:
        """通过ARIA role获取元素"""
        if name:
            return self.page.get_by_role(role, name=name)
        return self.page.get_by_role(role)
    
    def get_by_text(self, text: str) -> Locator:
        """通过文本获取元素"""
        return self.page.get_by_text(text)
    
    def expect_visible(self, locator: Locator, timeout: int = 5000):
        """期望元素可见"""
        expect(locator).to_be_visible(timeout=timeout)
        return self
    
    def expect_text(self, locator: Locator, text: str):
        """期望元素包含文本"""
        expect(locator).to_contain_text(text)
        return self
    
    def screenshot(self, name: str):
        """截图"""
        self.page.screenshot(path=f"test-results/screenshots/{name}.png", full_page=True)
        return self
