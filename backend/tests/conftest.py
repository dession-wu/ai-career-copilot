"""
Pytest 配置文件
提供测试所需的 fixtures 和配置
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate


# 使用内存数据库进行测试
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    """创建测试数据库引擎"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(engine):
    """为每个测试函数创建新的数据库会话"""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    """创建测试用户"""
    auth_service = AuthService(db_session)
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpassword123"
    )
    user = auth_service.create_user(user_data)
    return user


@pytest.fixture(scope="function")
def auth_headers(client, test_user):
    """获取认证 headers"""
    response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "testpassword123"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def sample_job_data():
    """示例职位数据"""
    return {
        "company_name": "测试科技有限公司",
        "job_title": "高级Python工程师",
        "location": "北京",
        "jd_text": """
        岗位职责：
        1. 负责后端系统架构设计与开发
        2. 使用Python、FastAPI开发高性能API
        3. 熟悉Docker、Kubernetes部署
        
        任职要求：
        1. 5年以上Python开发经验
        2. 精通FastAPI、Django等框架
        3. 熟悉微服务架构
        4. 有Kubernetes、Docker使用经验
        5. 良好的团队合作精神
        """,
        "status": "preparing"
    }


@pytest.fixture(scope="function")
def sample_resume_data():
    """示例简历数据"""
    return {
        "name": "张三",
        "email": "zhangsan@example.com",
        "phone": "13800138000",
        "summary": "5年Python后端开发经验，精通FastAPI和Django框架",
        "skills": ["Python", "FastAPI", "Django", "Docker", "Kubernetes", "MySQL", "Redis"],
        "experience": [
            {
                "company": "ABC科技",
                "title": "高级后端工程师",
                "duration": "2020-01 至 2024-01",
                "description": "负责微服务架构设计，使用FastAPI开发核心API"
            }
        ],
        "education": [
            {
                "school": "北京大学",
                "degree": "本科",
                "major": "计算机科学",
                "year": "2016-2020"
            }
        ]
    }


@pytest.fixture(scope="function")
def sample_match_request():
    """示例匹配分析请求数据"""
    return {
        "resume_text": """
        姓名：张三
        工作经验：5年Python后端开发
        技能：Python, FastAPI, Django, Docker, Kubernetes, MySQL, Redis
        工作经历：
        - ABC科技（2020-2024）：高级后端工程师，负责微服务架构设计
        教育背景：北京大学计算机科学本科
        """,
        "jd_text": """
        高级Python工程师
        要求：
        - 5年以上Python开发经验
        - 精通FastAPI、Django框架
        - 熟悉Docker、Kubernetes
        - 良好的团队合作能力
        """,
        "weights": {
            "skills": 0.35,
            "experience": 0.35,
            "projects": 0.20,
            "education": 0.10
        }
    }
