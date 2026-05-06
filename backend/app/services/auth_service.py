from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """获取密码哈希"""
        return pwd_context.hash(password)

    def create_user(self, user_data: UserCreate) -> User:
        """创建新用户"""
        # 检查用户名是否已存在
        if self.db.query(User).filter(User.username == user_data.username).first():
            raise ValueError("Username already registered")
        
        # 检查邮箱是否已存在
        if self.db.query(User).filter(User.email == user_data.email).first():
            raise ValueError("Email already registered")

        hashed_password = self.get_password_hash(user_data.password)
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def authenticate_user(self, user_data: UserLogin) -> Optional[User]:
        """验证用户登录"""
        user = self.db.query(User).filter(User.username == user_data.username).first()
        if not user:
            return None
        if not self.verify_password(user_data.password, user.hashed_password):
            return None
        return user

    def get_user_by_username(self, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """通过 ID 获取用户"""
        return self.db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """创建 JWT 访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[str]:
        """验证 JWT 令牌"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                return None
            return username
        except JWTError:
            return None
