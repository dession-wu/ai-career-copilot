# 🤖 AI Career Co-pilot (智能求职副驾)

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=next.js" alt="Next.js">
  <img src="https://img.shields.io/badge/FastAPI-0.104+-009688?style=flat-square&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=flat-square&logo=typescript" alt="TypeScript">
  <img src="https://img.shields.io/badge/Tailwind_CSS-v4-06B6D4?style=flat-square&logo=tailwindcss" alt="Tailwind CSS">
  <img src="https://img.shields.io/badge/LangChain-0.1+-1C3C3C?style=flat-square" alt="LangChain">
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

### 后端 (Backend)

| 技术 | 版本 | 用途 |
|------|------|------|
| [FastAPI](https://fastapi.tiangolo.com/) | >= 0.104 | 高性能异步 Web 框架 |
| [SQLAlchemy](https://www.sqlalchemy.org/) | >= 2.0 | ORM 数据库操作 |
| [Pydantic](https://docs.pydantic.dev/) | >= 2.5 | 数据校验与序列化 |
| [LangChain](https://www.langchain.com/) | >= 0.1 | AI 工作流编排 |
| [JWT](https://jwt.io/) | - | 用户认证与授权 |
| [Alembic](https://alembic.sqlalchemy.org/) | >= 1.12 | 数据库迁移管理 |

### 前端 (Frontend)

| 技术 | 版本 | 用途 |
|------|------|------|
| [Next.js](https://nextjs.org/) | 16.1.7 | React 全栈框架 |
| [React](https://react.dev/) | 19.2.3 | UI 组件库 |
| [TypeScript](https://www.typescriptlang.org/) | >= 5.0 | 类型安全 |
| [Tailwind CSS](https://tailwindcss.com/) | v4 | 原子化 CSS |
| [shadcn/ui](https://ui.shadcn.com/) | - | 高质量 UI 组件 |
| [Zustand](https://zustand-demo.pmnd.rs/) | >= 5.0 | 轻量级状态管理 |
| [Axios](https://axios-http.com/) | >= 1.13 | HTTP 客户端 |

---

## 🚀 快速开始

### 环境要求

- **Node.js** >= 18.0
- **Python** >= 3.11
- **npm** >= 9.0 或 **pnpm** >= 8.0

### 1. 克隆项目

```bash
git clone https://github.com/dession-wu/ai-career-copilot.git
cd ai-career-copilot
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填写必要的 API 密钥和配置
```

### 3. 启动后端服务

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 http://localhost:8000 运行  
Swagger API 文档: http://localhost:8000/docs

### 4. 启动前端服务

```bash
cd frontend
npm install
npm run dev
```

前端服务将在 http://localhost:3000 运行

---

## 📁 项目结构

```
ai-career-copilot/
├── 📂 backend/                    # FastAPI 后端
│   ├── 📂 app/
│   │   ├── 📄 main.py            # 应用入口
│   │   ├── 📄 config.py          # 配置管理
│   │   ├── 📄 database.py        # 数据库连接
│   │   ├── 📄 auth.py            # JWT 认证
│   │   ├── 📂 models/            # SQLAlchemy 数据模型
│   │   │   ├── user.py
│   │   │   ├── career_vault.py
│   │   │   ├── job_application.py
│   │   │   └── interview_question.py
│   │   ├── 📂 routers/           # API 路由
│   │   │   ├── auth.py           # 认证路由
│   │   │   ├── vault.py          # 经历总库路由
│   │   │   ├── jobs.py           # 求职管理路由
│   │   │   ├── interview.py      # 面试准备路由
│   │   │   └── scoring.py        # 评分系统路由
│   │   ├── 📂 schemas/           # Pydantic 数据模型
│   │   └── 📂 services/          # 业务逻辑层
│   │       ├── vault_service.py  # 简历解析服务
│   │       ├── llm_service.py    # AI 服务
│   │       ├── job_service.py    # 求职服务
│   │       └── scoring_service.py # 评分引擎
│   ├── 📂 tests/                 # 测试代码
│   └── 📄 requirements.txt       # Python 依赖
│
├── 📂 frontend/                   # Next.js 前端
│   ├── 📂 app/                   # App Router
│   │   ├── 📄 layout.tsx         # 根布局
│   │   ├── 📄 page.tsx           # 首页
│   │   ├── 📂 [locale]/          # 国际化路由
│   │   │   ├── 📂 (auth)/        # 认证页面组
│   │   │   │   ├── 📂 login/
│   │   │   │   └── 📂 register/
│   │   │   └── 📂 (dashboard)/   # 仪表盘页面组
│   │   │       ├── 📂 dashboard/ # 工作台看板
│   │   │       ├── 📂 jobs/      # 求职管理
│   │   │       ├── 📂 tailor/    # 简历定制
│   │   │       ├── 📂 vault/     # 经历总库
│   │   │       ├── 📂 interview/ # 面试准备
│   │   │       └── 📂 settings/  # 系统设置
│   │   └── 📄 globals.css        # 全局样式
│   ├── 📂 components/            # React 组件
│   │   ├── 📂 ui/               # shadcn/ui 组件
│   │   ├── 📂 auth/             # 认证组件
│   │   ├── 📂 jobs/             # 求职组件
│   │   ├── 📂 vault/            # Vault 组件
│   │   ├── 📂 interview/        # 面试组件
│   │   └── 📂 layout/           # 布局组件
│   ├── 📂 store/                # Zustand 状态管理
│   ├── 📂 lib/                  # 工具函数
│   ├── 📂 hooks/                # 自定义 Hooks
│   └── 📂 types/                # TypeScript 类型定义
│
├── 📂 tests/                     # 端到端测试
│   └── 📂 performance/          # 性能测试报告
├── 📄 .env.example              # 环境变量示例
├── 📄 package.json              # 根项目配置
└── 📄 README.md                 # 项目说明
```

---

## 🔌 API 接口概览

### 认证模块 (`/api/auth`)

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/register` | 用户注册 |
| POST | `/login` | 用户登录 |
| GET | `/me` | 获取当前用户信息 |

### 经历总库 (`/api/vault`)

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/upload` | 上传并解析简历 |
| GET | `/` | 获取 Vault 数据 |
| PUT | `/` | 更新 Vault 数据 |
| DELETE | `/` | 删除 Vault |
| POST | `/reparse` | 重新解析简历 |

### 求职管理 (`/api/jobs`)

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/` | 创建投递 |
| GET | `/` | 列表查询 |
| GET | `/{id}` | 详情查询 |
| PUT | `/{id}` | 更新投递 |
| PUT | `/{id}/status` | 更新状态 |
| DELETE | `/{id}` | 删除投递 |
| POST | `/{id}/analyze` | JD 匹配分析 |
| POST | `/{id}/tailor` | 简历定制 |
| POST | `/{id}/export/pdf` | 导出 PDF |

### 面试准备 (`/api/interview`)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/jobs/{id}/interview-prep` | 获取面试题 |
| POST | `/jobs/{id}/interview-prep/regenerate` | 重新生成 |
| PUT | `/questions/{id}` | 更新面试题 |

---

## 🧪 测试

### 前端测试

```bash
cd frontend
npm test              # 运行单元测试
npm run test:coverage # 运行测试并生成覆盖率报告
```

### 后端测试

```bash
cd backend
pytest                # 运行所有测试
pytest -v             # 详细输出
```

### 性能测试

项目包含完整的性能测试报告，涵盖：
- API 并发响应测试
- 前端页面加载性能
- Lighthouse 评分测试

查看 [性能测试报告](tests/performance/performance_report.md)

---

## 📦 部署指南

### 前端部署 (Vercel)

```bash
cd frontend
vercel --prod
```

### 后端部署 (Render)

1. 在 [Render](https://render.com) 创建 Web Service
2. 连接 GitHub 仓库
3. 配置环境变量 (参考 `.env.example`)
4. 部署命令: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

详细部署步骤请参考 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

## ⚙️ 配置说明

### 环境变量

| 变量名 | 说明 | 必填 |
|--------|------|------|
| `DATABASE_URL` | 数据库连接字符串 | ✅ |
| `SECRET_KEY` | JWT 签名密钥 | ✅ |
| `OPENAI_API_KEY` | OpenAI API 密钥 | ⚠️ |
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 | ⚠️ |
| `LLM_PROVIDER` | LLM 提供商 (openai/anthropic) | ✅ |
| `LLM_MODEL` | 模型名称 (gpt-4o/claude-3-5-sonnet) | ✅ |
| `NEXT_PUBLIC_API_URL` | 后端 API 地址 | ✅ |

> ⚠️ 至少需要配置一个 LLM API 密钥才能使用 AI 功能

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 提交 Issue

- 使用清晰的标题描述问题
- 提供复现步骤和环境信息
- 附上相关日志或截图

### 提交 Pull Request

1. Fork 本仓库
2. 创建功能分支: `git checkout -b feat/amazing-feature`
3. 提交更改: `git commit -m 'feat: add amazing feature'`
4. 推送分支: `git push origin feat/amazing-feature`
5. 创建 Pull Request

### 代码规范

- **Python**: 遵循 PEP8，使用类型提示
- **TypeScript**: 严格模式，避免 `any` 类型
- **Git Commit**: 使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范

---

## 📊 项目状态

| 指标 | 状态 |
|------|------|
| 功能完成度 | 85% |
| 代码质量 | 良好 (8/10) |
| 架构设计 | 优秀 (9/10) |
| 测试覆盖率 | 持续完善中 |
| 性能指标 | ✅ 全部达标 |

### 已知问题与改进计划

- [ ] UI 风格一致性优化
- [ ] 补充缺失路由页面
- [ ] 添加更多单元测试和 E2E 测试
- [ ] 大文件处理异步化
- [ ] 添加请求限流

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

---

## 🙏 致谢

感谢以下开源项目为本项目提供支持：

- [FastAPI](https://fastapi.tiangolo.com/) - 高性能 Python Web 框架
- [Next.js](https://nextjs.org/) - React 全栈框架
- [shadcn/ui](https://ui.shadcn.com/) - 精美的 React 组件库
- [LangChain](https://www.langchain.com/) - LLM 应用开发框架

---

<p align="center">
  Made with ❤️ by AI Career Co-pilot Team
</p>
