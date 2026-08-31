# 前端镜像：node 构建 Next.js 静态导出 → nginx 托管
# 注意：构建上下文为项目根目录（monorepo 需要访问 shared/）
# 构建命令：docker build -f frontend/Dockerfile .

# ---------- 构建阶段 ----------
FROM node:20-alpine AS build

# 复刻本地 monorepo 布局：/build/frontend + /build/shared
# （tsconfig 的 @shared/* 指向 ../shared/*，turbopack.root 为 frontend 上级目录）
WORKDIR /build

# 依赖分层：先复制 package 文件再安装，利用缓存
COPY package.json ./
COPY frontend/package.json frontend/package-lock.json* ./frontend/

COPY shared/package.json ./shared/
RUN npm install --no-audit --no-fund --registry=https://registry.npmmirror.com

# 复制前端源码与共享代码
COPY frontend/ ./frontend/
COPY shared/ ./shared/

# 构建时注入 API 基地址（默认空串 = 同源相对路径，经 nginx /api 反代）
ARG NEXT_PUBLIC_API_URL=""
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Next.js 静态导出（output: 'export'），产物输出到 /build/frontend/out
RUN cd frontend && npm run build

# ---------- 运行阶段 ----------
FROM nginx:1.27-alpine

# nginx 配置（先复制配置，避免被后续 COPY 覆盖）
COPY frontend/nginx/default.conf /etc/nginx/conf.d/default.conf

# 静态导出产物（注意：是 out/ 目录，不是 .next/ 或 dist/）
COPY --from=build /build/frontend/out /usr/share/nginx/html

EXPOSE 80

# 容器内探活：nginx 自身首页
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -q --spider http://localhost/ || exit 1