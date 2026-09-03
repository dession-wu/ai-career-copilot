# 后端镜像：FastAPI + uvicorn
# 注意：构建上下文为项目根目录
# 构建命令：docker build -t ai-career-copilot-backend .

FROM python:3.10-slim

# curl 用于容器健康检查探活
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 依赖分层：先复制 requirements 再安装，利用缓存
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    -r requirements.txt

# 复制后端源码（tests / .venv / db 文件等由 .dockerignore 排除）
COPY backend/ ./backend/

WORKDIR /app/backend

# 创建非 root 用户并接管运行目录（uploads / models 卷挂载点需可写）
RUN useradd -m -u 1000 appuser \
    && mkdir -p /app/backend/uploads /app/models \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# 容器内探活：后端 /health 端点
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

# 前端反代走 nginx，uvicorn 只需监听容器内网
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]