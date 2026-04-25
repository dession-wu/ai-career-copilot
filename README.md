# AI Career Co-pilot (智能求职副驾)

基于真实经历的、拒绝 AI 杜撰的智能求职辅助平台。

## 核心功能

- **经历总库管理 (Career Vault)**: 上传简历，自动解析并结构化提取个人信息、教育经历、技能清单和工作经历
- **JD 智能匹配**: 分析岗位 JD，计算匹配度评分，识别技能差距
- **简历精准定制**: 基于 JD 要求智能生成定制简历，严格防幻觉
- **面试准备**: 生成针对性面试题，提供 STAR 框架回答建议
- **求职看板**: Kanban 视图管理求职投递状态

## 技术栈

### 后端
- Python 3.10+
- FastAPI
- SQLAlchemy + SQLite/PostgreSQL
- LangChain + OpenAI/Claude
- PyPDF2 / pdfplumber / python-docx

### 前端
- Next.js 14+ (App Router)
- TypeScript
- Tailwind CSS
- Shadcn UI
- Zustand
- Axios

## 快速开始

### 1. 克隆项目

```bash
cd "AI Career Co-pilot"
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填写必要的配置
```

### 3. 启动后端服务

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 http://localhost:8000 运行
Swagger UI: http://localhost:8000/docs

### 4. 启动前端服务

```bash
cd frontend
npm install
npm run dev
```

前端服务将在 http://localhost:3000 运行

## 项目结构

```
ai-career-copilot/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── config.py          # 配置管理
│   │   ├── database.py        # 数据库连接
│   │   ├── main.py            # 应用入口
│   │   ├── models/            # SQLAlchemy 模型
│   │   ├── routers/           # API 路由
│   │   ├── services/          # 业务逻辑
│   │   └── schemas/           # Pydantic 模型
│   ├── alembic/               # 数据库迁移
│   └── requirements.txt
├── frontend/                   # Next.js 前端
│   ├── app/                   # App Router
│   ├── components/            # React 组件
│   ├── lib/                   # 工具函数
│   ├── store/                 # Zustand 状态管理
│   └── types/                 # TypeScript 类型
└── .env.example               # 环境变量示例
```

## 核心原则

**严格基于事实 (Fact-based Only)**: 所有的优化只是"提取、重组、润色和关键词映射"，绝对禁止凭空捏造技能或经历。

## 开发计划

- Phase 1: 基础设施搭建 (Week 1)
- Phase 2: 后端核心功能 (Week 2-3)
- Phase 3: 前端核心页面 (Week 3-4)
- Phase 4: 高级功能 (Week 4-5)
- Phase 5: 测试与优化 (Week 5-6)

## 许可证

MIT License
