from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated
import logging

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["认证"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

logger = logging.getLogger(__name__)


def get_current_user(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
) -> User:
    """获取当前登录用户"""
    # Never log bearer tokens or Authorization headers.
    
    auth_service = AuthService(db)
    username = auth_service.verify_token(token)
    if username is None:
        logger.warning("[Auth] Token verification failed - username is None")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.info(f"[Auth] Token verified, username: {username}")
    user = auth_service.get_user_by_username(username)
    if user is None:
        logger.warning(f"[Auth] User not found: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.info(f"[Auth] User found: {user.username}")
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    auth_service = AuthService(db)
    try:
        user = auth_service.create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    """用户登录"""
    auth_service = AuthService(db)
    user_data = UserLogin(username=form_data.username, password=form_data.password)
    user = auth_service.authenticate_user(user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_service.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: UserResponse = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user

from pydantic import BaseModel, Field, ConfigDict
from app.config import get_settings
from app.services.wechat_service import exchange_code, resolve_user

class WechatLogin(BaseModel):
    model_config = ConfigDict(extra='forbid')
    code: str = Field(min_length=1, max_length=512, pattern=r'^\S+$')

@router.post('/wechat', response_model=Token)
def wechat_login(payload: WechatLogin, db: Session = Depends(get_db)):
    settings = get_settings()
    openid = exchange_code(payload.code, settings)
    user = resolve_user(db, settings.WECHAT_APP_ID, openid)
    return {'access_token': AuthService(db).create_access_token(data={'sub': user.username}), 'token_type': 'bearer'}
