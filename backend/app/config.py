from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import secrets
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # 应用配置
    APP_NAME: str = "AI Career Co-pilot API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # 数据库配置 - 支持 SQLite (开发) 和 PostgreSQL (生产)
    DATABASE_URL: str = "sqlite:///./career_copilot.db"

    # 安全配置 - 移除默认值，强制从环境变量读取
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # LLM 配置
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    LLM_PROVIDER: str = "openai"  # openai, anthropic
    LLM_MODEL: str = "gpt-4o"

    # 文件上传配置
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    # CORS 配置 - 支持从环境变量 JSON 字符串解析
    CORS_ORIGINS_JSON: str = ""  # 生产环境使用: '["https://your-app.vercel.app"]'

    # Cloudflare R2 配置（可选，用于生产环境文件存储）
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = ""
    R2_PUBLIC_URL: str = ""

    @property
    def cors_origins(self) -> list[str]:
        """解析 CORS 来源列表"""
        if self.CORS_ORIGINS_JSON:
            try:
                return json.loads(self.CORS_ORIGINS_JSON)
            except json.JSONDecodeError:
                pass
        return [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:5173"
        ]

    @property
    def is_production(self) -> bool:
        """判断是否生产环境"""
        return not self.DATABASE_URL.startswith("sqlite")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


def generate_secret_key() -> str:
    """生成安全的随机密钥"""
    return secrets.token_urlsafe(32)
