"""
面试复盘新建功能 API 测试脚本
系统性测试所有后端接口
"""
import requests
import json
from datetime import datetime, timedelta
import uuid

BASE_URL = "http://localhost:8000"

class InterviewReviewAPITester:
    def __init__(self):
        self.access_token = None
        self.headers = {}
        self.test_job_id = None
        self.created_review_id = None
        self.errors = []
        
    def log_error(self, error_id, test_case, error_type, severity, description, expected, actual, steps):
        """记录错误"""
        error = {
            "error_id": error_id,
            "test_case": test_case,
            "error_type": error_type,
            "severity": severity,
            "description": description,
            "expected": expected,
            "actual": actual,
            "steps": steps,
            "timestamp": datetime.now().isoformat(),
            "status": "待修复"
        }
        self.errors.append(error)
        print(f"  [错误] {error_id}: {description}")
        return error
    
    def login(self):
        """测试登录获取token"""
        print("\n" + "="*60)
        print("[SETUP] 用户登录获取访问令牌")
        print("="*60)
        
        login_data = {
            "username": "test@example.com",
            "password": "testpassword"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                self.headers = {"Authorization": f"Bearer {self.access_token}"}
                print(f"✓ 登录成功，获取到访问令牌")
                return True
            else:
                print(f"✗ 登录失败: {response.status_code}")
                print(f"  响应: {response.text}")
                # 创建测试用户
                return self.register_test_user()
        except Exception as e:
            print(f"✗ 登录请求失败: {e}")
            return False
    
    def register_test_user(self):
        """注册测试用户"""
        print("\n[SETUP] 注册测试用户...")
        
        register_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
            if response.status_code == 201:
                print(f"✓ 测试用户注册成功")
                # 重新登录
                return self.login()
            else:
                print(f"✗ 注册失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ 注册请求失败: {e}")
            return False
    
    def create_test_job(self):
        """创建测试职位"""
        print("\n[SETUP] 创建测试职位...")
        
        job_data = {
            "company_name": "测试公司",
            "job_title": "测试岗位",
            "jd_text": "这是一个测试职位描述",
            "status": "applied"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/jobs", json=job_data, headers=self.headers)
            if response.status_code == 201:
                job = response.json()
                self.test_job_id = job["id"]
                print(f"✓ 测试职位创建成功: {self.test_job_id}")
                return True
            else:
                print(f"✗ 创建职位失败: {response.status_code}")
                print(f"  响应: {response.text}")
                return False
        except Exception as e:
            print(f"✗ 创建职位请求失败: {e}")
            return False
    
    def test_form_validation(self):
        """测试表单字段验证 - TC-FV-001 ~ TC-FV-010"""
        print("\n" + "="*60)
        print("[TEST GROUP] 表单字段验证测试")
        print("="*60)
        
        # TC-FV-001: 必填项验证-岗位
        print("\n[TC-FV-001] 必填项验证-岗位...")
        invalid_data = {
            "application_id": "",
            "round_type": "technical",
            "interview_date": datetime.utcnow().isoformat()
        }
        try:
            response = requests.post(f"{BASE_URL}/reviews/jobs/{self.test_job_id}", 
                                   json=invalid_data, headers=self.headers)
            if response.status_code == 422:
                print("✓ 后端正确拒绝空application_id (422)")
            else:
                self.log_error("ERR-FV-001", "TC-FV-001", "功能", "中等",
                             "空application_id未被正确拒绝",
                             "返回422错误", f"返回{response.status_code}",
                             ["1. 提交空application_id", "2. 检查响应状态码"])
        except Exception as e:
            print(f"✗ 请求失败: {e}")
        
        # TC-FV-002: 必填项验证-面试类型
        print("\n[TC-FV-002] 必填项验证-面试类型...")
        invalid_data = {
            "application_id": self.test_job_id,
            "round_type": "",
            "interview_date": datetime.utcnow().isoformat()
        }
        try:
            response = requests.post(f"{BASE_URL}/reviews/jobs/{self.test_job_id}", 
                                   json=invalid_data, headers=self.headers)
            if response.status_code == 422:
                print("✓ 后端正确拒绝空round_type (422)")
            else:
                self.log_error("ERR-FV-002", "TC-FV-002", "功能", "中等",
                             "空round_type未被正确拒绝",
                             "返回422错误", f"返回{response.status_code}",
                             ["1. 提交空round_type", "2. 检查响应状态码"])
        except Exception as e:
            print(f"✗ 请求失败: {e}")
        
        # TC-FV-003: 必填项验证-面试日期
        print("\n[TC-FV-003] 必填项验证-面试日期...")
        invalid_data = {
            "application_id": self.test_job_id,
            "round_type": "technical"
            # 缺少 interview_date
        }
        try:
            response = requests.post(f"{BASE_URL}/reviews/jobs/{self.test_job_id}", 
                                   json=invalid_data, headers=self.headers)
            if response.status_code == 422:
                print("✓ 后端正确拒绝缺少interview_date (422)")
            else:
                self.log_error("ERR-FV-003", "TC-FV-003", "功能", "中等",
                             "缺少interview_date未被正确拒绝",
                             "返回422错误", f"返回{response.status_code}",
                             ["1. 提交缺少interview_date的数据", "2. 检查响应状态码"])
        except Exception as e:
            print(f"✗ 请求失败: {e}")
        
        # TC-FV-004: 轮次号边界-最小值
        print("\n[TC-FV-004] 轮次号边界-最小值...")
        invalid_data = {
            "application_id": self.test_job_id,
            "round_type": "technical",
            "interview_date": datetime.utcnow().isoformat(),
            "round_number": 0
        }
        try:
            response = requests.post(f"{BASE_URL}/reviews/jobs/{self.test_job_id}", 
                                   json=invalid_data, headers=self.headers)
            if response.status_code == 422:
                print("✓ 后端正确拒绝round_number=0 (422)")
            else:
                print(f"⚠ round_number=0被接受，实际返回: {response.status_code}")
                print(f"  注意: 后端应添加ge=1验证")
        except Exception as e:
            print(f"✗ 请求失败: {e}")
        
        # TC-FV-005: 轮次