"""
认证流程集成测试
测试用户注册、登录、获取用户信息等完整流程
"""

import pytest


class TestAuthFlow:
    """认证流程测试类"""

    def test_register_user_success(self, client):
        """测试用户注册成功"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "id" in data

    def test_register_duplicate_username(self, client, test_user):
        """测试注册重复用户名失败"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "another@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 400
        assert "用户名已存在" in response.json()["detail"]

    def test_login_success(self, client, test_user):
        """测试登录成功"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": "testuser",
                "password": "testpassword123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        """测试登录密码错误"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """测试登录不存在的用户"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": "nonexistent",
                "password": "password123"
            }
        )

        assert response.status_code == 401

    def test_get_current_user(self, client, auth_headers, test_user):
        """测试获取当前用户信息"""
        response = client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["id"] == test_user.id

    def test_get_current_user_no_auth(self, client):
        """测试未认证获取用户信息失败"""
        response = client.get("/api/auth/me")

        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """测试无效token获取用户信息失败"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    def test_complete_auth_flow(self, client):
        """测试完整认证流程"""
        # 1. 注册用户
        register_response = client.post(
            "/api/auth/register",
            json={
                "username": "flowtest",
                "email": "flow@example.com",
                "password": "flowpass123"
            }
        )
        assert register_response.status_code == 201

        # 2. 登录获取token
        login_response = client.post(
            "/api/auth/login",
            data={
                "username": "flowtest",
                "password": "flowpass123"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # 3. 使用token获取用户信息
        me_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        assert me_response.json()["username"] == "flowtest"
