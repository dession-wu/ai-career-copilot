from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlite3
import logging

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# 创建数据库引擎 - 添加编码支持
engine_args = {
    "echo": settings.DEBUG
}

is_sqlite = settings.DATABASE_URL.startswith("sqlite")

if is_sqlite:
    # SQLite 配置（本地开发）
    engine_args["connect_args"] = {"check_same_thread": False}
    engine_args["connect_args"]["isolation_level"] = None
else:
    # PostgreSQL 配置（生产环境）
    engine_args["pool_pre_ping"] = True  # 连接池健康检查
    engine_args["pool_recycle"] = 300    # 5分钟回收连接
    engine_args["pool_size"] = 5         # 连接池大小
    engine_args["max_overflow"] = 10     # 最大溢出连接

engine = create_engine(settings.DATABASE_URL, **engine_args)

# 为 SQLite 数据库设置 UTF-8 编码
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    if is_sqlite and isinstance(dbapi_conn, sqlite3.Connection):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA encoding='UTF-8'")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()


def get_db():
    """获取数据库会话的依赖函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)
