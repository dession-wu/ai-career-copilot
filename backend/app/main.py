from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging
import asyncio

# 首先配置PaddleOCR模型路径（必须在导入其他模块之前）
from app.paddlex_config import ensure_model_path, PADDLEX_MODEL_PATH

from app.config import get_settings
from app.database import init_db
from app.routers import auth_router, vault_router, jobs_router, interview_router, scoring_router, interview_review_router, analytics_router, ai_analysis_router

settings = get_settings()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 限流配置
rate_limit_storage = {}
RATE_LIMIT = 100  # 每分钟请求数
RATE_WINDOW = 60  # 窗口秒数


async def cleanup_rate_limit_storage():
    """定期清理过期的限流记录"""
    while True:
        await asyncio.sleep(300)  # 每5分钟清理一次
        current_time = time.time()
        expired_ips = [
            ip for ip, requests in rate_limit_storage.items()
            if not any(current_time - req_time < RATE_WINDOW for req_time in requests)
        ]
        for ip in expired_ips:
            del rate_limit_storage[ip]
        if expired_ips:
            logger.info(f"Cleaned up {len(expired_ips)} expired rate limit entries")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理器"""
    # 启动时执行
    init_db()
    # 启动限流清理任务
    cleanup_task = asyncio.create_task(cleanup_rate_limit_storage())
    logger.info(f"[PaddleX] 模型路径配置: {PADDLEX_MODEL_PATH}")
    logger.info("Application startup complete")
    yield
    # 关闭时执行
    cleanup_task.cancel()
    logger.info("Application shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Career Co-pilot 后端 API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """限流中间件"""
    # 跳过健康检查端点
    if request.url.path == "/health":
        response = await call_next(request)
        return response

    # 获取客户端IP
    client_ip = request.client.host

    # 检查限流
    current_time = time.time()
    if client_ip in rate_limit_storage:
        requests = rate_limit_storage[client_ip]
        # 清理过期的请求记录
        requests = [req_time for req_time in requests if current_time - req_time < RATE_WINDOW]

        if len(requests) >= RATE_LIMIT:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": "请求过于频繁，请稍后再试"}
            )

        requests.append(current_time)
        rate_limit_storage[client_ip] = requests
    else:
        rate_limit_storage[client_ip] = [current_time]

    response = await call_next(request)
    return response


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """请求日志中间件"""
    start_time = time.time()
    client_ip = request.client.host
    method = request.method
    path = request.url.path

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(f"{client_ip} - {method} {path} - {response.status_code} - {process_time:.3f}s")

    return response


# 注册路由
app.include_router(auth_router)
app.include_router(vault_router)
app.include_router(jobs_router)
app.include_router(interview_router)
app.include_router(scoring_router)
app.include_router(interview_review_router)
app.include_router(analytics_router)
app.include_router(ai_analysis_router)


@app.get("/health", tags=["Health"])
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/", tags=["Root"])
async def root():
    """根路径"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
