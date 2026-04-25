"""
登录页面 - Page Object
"""

from playwright.sync_api import Page, Locator, expect
from tests.pages.base_page import BasePage


class LoginPage(BasePage):
    """登录页面"""
    
    def __init__(self, page: Page):
        super().__init__(page)
        self.path = "/login"
    
    # 页面元素
    @property
    def email_input(self) -> Locator:
        return self.page.get_by_label("邮箱")
    
    @property
    def password_input(self) -> Locator:
        return self.page.get_by_label("密码")
    
    @property
    def login_button(self) -> Locator:
        return self.page.get_by_role("button", name="登录")
    
    @property
    def register_link(self) -> Locator:
        return self.page.get_by_text("注册")
    
    @property
    def error_message(self) -> Locator:
        return self.page.get_by_role("alert")
    
    # 页面操作
    def navigate(self):
        """导航到登录页"""
        self.goto(self.path)
        self.wait_for_load()
        return self
    
    def fill_email(self, email: str):
        """填写邮箱"""
        self.email_input.fill(email)
        return self
    
    def fill_password(self, password: str):
        """填写密码"""
        self.password_input.fill(password)
        return self
    
    def click_login(self):
        """点击登录按钮"""
        self.login_button.click()
        return self
    
    def login(self, email: str, password: str):
        """完整登录流程"""
        self.fill_email(email).fill_password(password).click_login()
        return self
    
    def click_register(self):
        """点击注册链接"""
        self.register_link.click()
        return self
    
    # 验证
    def expect_login_success(self):
        """期望登录成功"""
        self.page.wait_for_url("**/dashboard")
        return self
    
    def expect_error(self, message: str = None):
        """期望显示错误"""
        expect(self.error_message).to_be_visible()
        if message:
            expect(self.error_message).to_contain_text(message)
        return self
    
    def expect_on_login_page(self):
        """期望在登录页面"""
        expect(self.page).to_have_url(f"{self.base_url}{self.path}")
        expect(self.login_button).to_be_visible()
        return self
