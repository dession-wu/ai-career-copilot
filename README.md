# 🤖 AI Career Co-pilot (智能求职副驾)

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=next.js" alt="Next.js">
  <img src="https://img.shields.io/badge/FastAPI-0.104+-009688?style=flat-square&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=flat-square&logo=typescript" alt="TypeScript">
  <img src="https://img.shields.io/badge/Tailwind_CSS-v4-06B6D4?style=flat-square&logo=tailwindcss" alt="Tailwind CSS">
  <img src="https://img.shields.io/badge/LangChain-0.1+-1C3C3C?style=flat-square" alt="LangChain">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker" alt="Docker">
</p>

<p align="center">
  <b>基于真实经历的、拒绝 AI 杜撰的智能求职辅助平台</b>
</p>

<p align="center">
  <a href="#核心功能">核心功能</a> •
  <a href="#技术栈">技术栈</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#项目结构">项目结构</a> •
  <a href="#部署指南">部署</a> •
  <a href="#贡献指南">贡献</a>
</p>

---

<img width="1024" height="522" alt="Career Guide" src="https://github.com/user-attachments/assets/ae48e59e-c7d6-46bd-88a9-dfd05d953091" />

## ✨ 核心功能

| 模块 | 功能描述 | 状态 |
|------|----------|------|
| 📁 **经历总库 (Career Vault)** | 上传简历 PDF/DOCX，AI 自动解析并结构化提取个人信息、教育经历、技能清单和工作经历 | ✅ 已完成 |
| 🎯 **JD 智能匹配** | 分析岗位 JD，计算匹配度评分 (0-100)，识别技能差距 (Skills Gap) | ✅ 已完成 |
| ✏️ **简历精准定制** | 基于 JD 要求智能生成定制简历，严格防幻觉，仅提取重组已有经历 | ✅ 已完成 |
| 🎤 **面试准备** | 生成针对性面试题，提供 STAR 框架回答建议和考察意图分析 | ✅ 已完成 |
| 📊 **求职看板** | Kanban 视图管理求职投递状态，支持状态流转追踪 | ✅ 已完成 |
| 🤖 **AI 双轨制** | 基础模式 + LLM 模式，灵活应对不同场景需求 | ✅ 已完成 |
| 🌍 **多语言支持** | 支持中英文界面切换 | ✅ 已完成 |

### 核心原则

> **严格基于事实 (Fact-based Only)**：所有的优化只是"提取、重组、润色和关键词映射"，绝对禁止凭空捏造技能或经历。

---

## 🛠 技术栈

| 层 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 前端 | [Next.js](https://nextjs.org/) | 16.1.7 | React 框架，App Router + 静态导出 (`output: 'export'`) |
| 前端 | [React](https://react.dev/) | 19.2.3 | UI 组件库 |
| 前端 | [TypeScript](https://www.typescriptlang.org/) | >= 5.0 | 类型安全 |
| 前端 | [Tailwind CSS](https://tailwindcss.com/) | v4 | 原子化 CSS |
| 前端 | [Zustand](https://zustand-demo.pmnd.rs/) | >= 5.0 | 轻量级状态管理 |
| 前端 | [Axios](https://axios-http.com/) | >= 1.13 | HTTP 客户端 |
| 前端 | [next-intl](https://next-intl.dev/) | - | 中英双语国际化 |
| 共享 | shared/ (TS 包) | - | 前后端共享类型、常量与工具 |
| 后端 | [FastAPI](https://fastapi.tiangolo.com/) | 0.141 | 高性能异步 Web 框架 |
| 后端 | [SQLAlchemy](https://www.sqlalchemy.org/) | 2.0.52 | ORM（本地 SQLite / 容器 PostgreSQL） |
| 后端 | [Pydantic](https://docs.pydantic.dev/) | 2.13 | 数据校验与序列化 |
| 后端 | [LangChain](https://www.langchain.com/) | 1.3 | AI 工作流编排 |
| 后端 | JWT (python-jose) | 3.5 | 用户认证与授权 |
| 后端 | EasyOCR / PaddleX | - | 简历 OCR 识别 |
| 服务 | [nginx](https://nginx.org/) | 1.27 | 前端静态托管 + `/api` `/ai` 同源反向代理 |
| 服务 | [PostgreSQL](https://www.postgresql.org/) | 15 | 容器化生产数据库 |
| 服务 | pdf-service (Node) | - | 可选 PDF 导出服务，失败自动降级 Markdown |
| 交付 | [Docker Compose](https://docs.docker.com/compose/) | - | 一键编排三服务 |

---

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

```bash
git clone https://github.com/dession-wu/ai-career-copilot.git
cd ai-career-copilot

cp .env.example .env
# 编辑 .env：SECRET_KEY 必填；OPENAI_API_KEY 可选（无 key 时 AI 功能自动降级）

docker compose up -d --build
```

启动后访问 **http://localhost:8082**（唯一对外端口）。

编排内容（`docker-compose.yml`）：

| 服务 | 说明 |
|------|------|
| `frontend` | Next.js 静态导出产物由 nginx 托管，浏览器请求 `/api/*` `/ai/*` 经同源反代转发到 backend，无跨域问题 |
| `backend` | FastAPI + PostgreSQL，模型/上传目录挂载卷持久化 |
| `db` | PostgreSQL 15，`pg_isready` 健康检查 |

> 💡 容器 healthcheck 使用 `127.0.0.1` 探活（而非 `localhost`），避免部分基础镜像 IPv6 解析问题导致误判 unhealthy。

> 💡 OCR 模型体积较大，不打入镜像；首次启动后可将 EasyOCR/PaddleX 模型放入 `models_data` 卷对应目录，或设置 `PADDLEX_MODEL_DIR` / `EASYOCR_MODEL_DIR` 指向已有模型。

### 方式二：本地开发

**环境要求**

- **Node.js** >= 18.0（经 nvm 安装时先 `source ~/.nvm/nvm.sh`）
- **Python** >= 3.10
- **npm** >= 9.0

```bash
# 1. 配置环境变量
cp .env.example .env

# 2. 启动后端（默认 SQLite）
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. 启动前端（另开终端）
cd frontend
npm install
npm run dev
```

也可使用根目录一键脚本 `start_all_local.sh` 同时拉起前后端。

**服务地址**

| 服务 | 本地开发 | Docker Compose |
|------|----------|----------------|
| 前端 | http://localhost:3000 | http://localhost:8082 |
| 后端 API | http://localhost:8000 | http://localhost:8082/api（同源反代） |
| Swagger 文档 | http://localhost:8000/docs | http://localhost:8082/api/docs |
| pdf-service（可选） | http://localhost:3002 | 未编排，按需自行部署 |

---

## 📂 项目结构

```
ai-career-copilot/
├── frontend/                  # Next.js 前端（App Router + next-intl 双语）
│   ├── src/
│   │   ├── app/               # 页面路由（静态导出）
│   │   ├── components/        # UI 组件
│   │   ├── lib/               # API 客户端等工具（api.ts）
│   │   ├── stores/            # Zustand 状态管理
│   │   └── messages/          # zh.json / en.json 国际化文案
│   ├── Dockerfile             # node:20 构建 + nginx:1.27 运行
│   └── nginx/default.conf     # 静态托管 + /api /ai 反代
├── backend/                   # FastAPI 后端
│   ├── app/
│   │   ├── main.py            # 入口，路由注册
│   │   ├── models/            # SQLAlchemy 数据模型
│   │   ├── routes/            # API 路由
│   │   └── services/          # 业务逻辑（解析/匹配/LLM 等）
│   └── requirements.txt       # 锁定版本依赖
├── shared/                    # 前后端共享 TS 包（类型/常量/工具）
├── pdf-service/               # 可选 PDF 导出服务（Node）
├── models/                    # OCR 模型目录（不入库/不入镜像）
├── tests/                     # 后端测试
├── Dockerfile                 # 前端构建入口（monorepo 布局）
├── docker-compose.yml         # 三服务编排
├── .env.example               # 环境变量模板
└── start_all_local.sh         # 本地一键启动脚本
```

---

## 🔌 API 概览

| 方法 | 路径 | 描述 |
|------|------|------|
| `POST` | `/api/auth/register` | 用户注册 |
| `POST` | `/api/auth/login` | 用户登录，返回 JWT |
| `GET` | `/api/career/me` | 获取当前用户经历总库 |
| `POST` | `/api/resume/upload` | 上传简历文件（PDF/DOCX） |
| `POST` | `/api/match/analyze` | JD 匹配度分析 |
| `POST` | `/api/optimize/resume` | 生成定制化简历 |
| `GET` | `/api/health` | 健康检查 |

完整接口见 Swagger 文档（`/docs`）。

---

## ⚙️ 配置说明

`.env` 关键变量（完整列表见 [.env.example](.env.example)）：

| 变量 | 必填 | 说明 |
|------|------|------|
| `SECRET_KEY` | ✅ | JWT 签名密钥，无默认值，缺失时后端无法启动 |
| `DATABASE_URL` | - | 容器内由 compose 注入 PostgreSQL；本地默认 SQLite |
| `OPENAI_API_KEY` | - | 可选。未配置时 AI 功能降级为基础模式 |
| `LLM_BASE_URL` | - | 可选。自定义 LLM 网关地址 |
| `PADDLEX_MODEL_DIR` | - | PaddleX 模型目录，默认 `./models/paddlex` |
| `PDF_SERVICE_URL` | - | 可选 pdf-service 地址，未配置时导出降级 Markdown |
| `POSTGRES_PASSWORD` | ✅(Docker) | 数据库密码 |

---

## 🌐 部署指南

### 阿里云 ECS 部署（当前生产方式）

当前已在阿里云 ECS（路径 `/opt/projects/ai_career_copilot`，端口 8082）运行三容器编排：

```bash
# 服务器上首次部署
cd /opt/projects/ai_career_copilot
git clone https://github.com/dession-wu/ai-career-copilot.git .
cp .env.example .env   # 填入 SECRET_KEY / POSTGRES_PASSWORD / 可选 LLM Key
docker compose up -d --build

# 后续更新
git pull
docker compose up -d --build
```

**运维要点**

- 唯一对外端口 **8082**（nginx），`/api` `/ai` 均为同源反代，无需额外 CORS/网关配置
- healthcheck 使用 `127.0.0.1` 探活，规避 IPv6 误判；`docker ps` 确认三容器 `healthy`
- `pgdata` / `uploads_data` / `models_data` 三个卷持久化，重建容器不丢数据
- LLM Key 可后续通过编辑 `.env` + `docker compose up -d` 热更新注入

> 更详细的部署排障见 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)。

### Vercel / Render 部署（备选）

前端可部署到 [Vercel](https://vercel.com)（根目录含 `vercel.json`），后端可部署到 [Render](https://render.com)。该方案适合前端 API 直连模式，需相应配置 CORS 与 `NEXT_PUBLIC_API_URL`。当前推荐的 Docker Compose 方案为同源架构，无需跨域配置。

---

## 🧪 测试

```bash
# 前端单元测试
cd frontend && npm test

# 后端测试
cd backend && python -m pytest ../tests/ -v
```

---

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'feat: add amazing feature'`（遵循 Conventional Commits）
4. 推送分支：`git push origin feature/amazing-feature`
5. 提交 Pull Request

---

## 📄 License

本项目采用 MIT License，详见 [LICENSE](LICENSE)。

---

## 🙏 致谢

- [Next.js](https://nextjs.org/) / [FastAPI](https://fastapi.tiangolo.com/) / [Tailwind CSS](https://tailwindcss.com/)
- 所有为本项目提出建议与反馈的朋友


---