"""
生成测试用的有效JWT token
"""

import jwt
from datetime import datetime, timedelta, timezone

# 从后端配置获取或使用默认值
SECRET_KEY = "your-secret-key-here"  # 需要与后端一致
ALGORITHM = "HS256"

# 创建测试token
def create_test_token():
    """创建测试用的JWT token"""
    # 尝试读取后端配置
    try:
        import sys
        sys.path.insert(0, 'e:\\Desktop\\AI Career Co-pilot\\backend')
        from app.config import settings
        secret = settings.SECRET_KEY
        algo = settings.ALGORITHM
    except Exception as e:
        print(f"无法读取后端配置，使用默认值: {e}")
        secret = SECRET_KEY
        algo = ALGORITHM
    
    # 创建payload
    expire = datetime.now(timezone.utc) + timedelta(days=1)
    to_encode = {
        "sub": "test-user",
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    
    # 编码token
    encoded_jwt = jwt.encode(to_encode, secret, algorithm=algo)
    return encoded_jwt

if __name__ == "__main__":
    token = create_test_token()
    print("生成的测试Token:")
    print(token)
    
    # 验证token
    try:
        import sys
        sys.path.insert(0, 'e:\\Desktop\\AI Career Co-pilot\\backend')
        from app.config import settings
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print("\nToken验证成功:")
        print(f"  用户: {payload.get('sub')}")
        print(f"  过期时间: {payload.get('exp')}")
    except Exception as e:
        print(f"\nToken验证失败: {e}")
