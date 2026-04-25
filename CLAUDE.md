# AI Career Co-pilot - Claude Code Configuration

## Project Overview

AI Career Co-pilot 是一个全栈应用，帮助用户管理求职过程，包括：
- 职业档案管理 (Career Vault)
- 职位申请跟踪
- 简历定制
- 面试准备
- AI 辅助功能

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT (python-jose, passlib/bcrypt)
- **AI Integration**: LangChain

### Frontend
- **Framework**: Next.js 14+ with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Shadcn UI
- **State Management**: Zustand with persistence
- **HTTP Client**: Axios

## Project Structure

```
AI Career Co-pilot/
├── CLAUDE.md                    # 项目核心配置与 Claude Code 指令
├── README.md                    # 项目说明文档
├── .trae/                       # Trae IDE 配置与文档
│   ├── documents/               # 计划文档、PRD、规范文件
│   └── rules/                   # 项目规则配置
├── docs/                        # 项目文档
│   ├── architecture.md          # 架构设计文档
│   ├── decisions/               # 架构决策记录 (ADR)
│   └── runbooks/                # 运维手册
├── .claude/                     # Claude Code 配置
│   ├── settings.json            # Claude 行为设置
│   ├── hooks/                   # 自动化钩子脚本
│   └── skills/                  # 可复用技能定义
├── backend/                     # 后端服务 (FastAPI)
│   ├── app/                     # 应用代码
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置管理
│   │   ├── models/              # SQLAlchemy 模型
│   │   ├── routers/             # API 路由
│   │   ├── services/            # 业务逻辑层
│   │   ├── schemas/             # Pydantic 模型
│   │   └── core/                # 核心工具
│   ├── alembic/                 # 数据库迁移
│   └── tests/                   # 测试代码
├── frontend/                    # 前端应用 (Next.js)
│   ├── app/                     # Next.js App Router
│   │   ├── layout.tsx           # 根布局
│   │   ├── page.tsx             # 首页
│   │   ├── login/               # 登录页面
│   │   ├── register/            # 注册页面
│   │   ├── dashboard/           # 仪表盘
│   │   ├── vault/               # 经历总库
│   │   ├── jobs/                # 求职管理
│   │   └── tailor/              # 简历定制
│   ├── components/              # React 组件
│   │   ├── ui/                  # shadcn/ui 组件
│   │   ├── auth/                # 认证相关组件
│   │   └── vault/               # Vault 相关组件
│   ├── store/                   # Zustand 状态管理
│   ├── lib/                     # 工具函数
│   └── hooks/                   # 自定义 Hooks
└── tools/                       # 开发工具与脚本
    ├── scripts/                 # 自动化脚本
    └── prompts/                 # LLM 提示模板
```

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Python files | snake_case | `vault_service.py` |
| React components | PascalCase | `LoginForm.tsx` |
| TypeScript types | PascalCase | `UserProfile.ts` |
| API routes | snake_case | `auth.py`, `vault.py` |
| Directories | lowercase | `components/`, `services/` |

## Layer Architecture

```
Presentation Layer (frontend/app/)
         ↓
    API Layer (backend/routers/)
         ↓
 Service Layer (backend/services/)
         ↓
   Data Layer (backend/models/)
```

## Development Commands

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## gstack

Use /browse from gstack for all web browsing. Never use mcp__claude-in-chrome__* tools.

Available skills: /office-hours, /plan-ceo-review, /plan-eng-review, /plan-design-review,
/design-consultation, /review, /ship, /browse, /qa, /qa-only, /design-review,
/setup-browser-cookies, /retro, /investigate, /document-release, /codex, /careful,
/freeze, /guard, /unfreeze, /gstack-upgrade.

If gstack skills aren't working, run `cd .claude/skills/gstack && ./setup` to build the binary and register skills.

### gstack Skills Overview

| Skill | Description |
|-------|-------------|
| `/office-hours` | YC Office Hours - startup diagnostic + builder brainstorm |
| `/plan-ceo-review` | CEO/Founder review - rethink the problem |
| `/plan-eng-review` | Eng Manager review - architecture, data flow, edge cases |
| `/plan-design-review` | Senior Designer review - design audit |
| `/design-consultation` | Design Partner - build design system from scratch |
| `/review` | Staff Engineer - find production bugs |
| `/investigate` | Debugger - systematic root-cause debugging |
| `/design-review` | Designer Who Codes - design audit + fixes |
| `/qa` | QA Lead - test app, find bugs, fix with atomic commits |
| `/qa-only` | QA Reporter - report bugs without fixes |
| `/ship` | Release Engineer - sync main, run tests, open PR |
| `/document-release` | Technical Writer - update project docs |
| `/retro` | Eng Manager - weekly retro with stats |
| `/browse` | QA Engineer - real Chromium browser automation |
| `/setup-browser-cookies` | Session Manager - import browser cookies |
| `/codex` | Second Opinion - independent review from OpenAI Codex |
| `/careful` | Safety Guardrails - warns before destructive commands |
| `/freeze` | Edit Lock - restrict edits to one directory |
| `/guard` | Full Safety - /careful + /freeze |
| `/unfreeze` | Unlock - remove /freeze boundary |
| `/gstack-upgrade` | Self-Updater - upgrade gstack to latest |

## Coding Conventions

- Use TypeScript for all new frontend code
- Follow existing code patterns and naming conventions
- Use Shadcn UI components when available
- Use Zustand for state management with persistence
- Backend: Use Pydantic models for request/response validation
- Backend: Use SQLAlchemy for database operations
- Backend: Use dependency injection for authentication

## Project Structure Guidelines

### Adding New Features

When adding a new feature, follow this structure:

**Backend:**
1. Add model in `backend/app/models/` (if needed)
2. Add schema in `backend/app/schemas/` (if needed)
3. Add service in `backend/app/services/` (if needed)
4. Add router in `backend/app/routers/`
5. Register router in `backend/app/main.py`
6. Add tests in `backend/tests/`

**Frontend:**
1. Add page in `frontend/app/{feature}/page.tsx`
2. Add components in `frontend/components/{feature}/`
3. Add store in `frontend/store/` (if needed)
4. Add types in `frontend/types/` (if needed)
5. Add hooks in `frontend/hooks/` (if needed)

### File Organization Principles

1. **Co-location**: Keep related files close together
2. **Single Responsibility**: Each file has one clear purpose
3. **Explicit Dependencies**: All imports must be explicit
4. **No Circular Dependencies**: Use interfaces/events to decouple
5. **Test Coverage**: Every module has corresponding tests

### Module Boundaries

- **Models**: Data structures and database schema
- **Schemas**: API request/response validation
- **Services**: Business logic and external integrations
- **Routers**: HTTP endpoints and request handling
- **Components**: UI elements and user interactions
- **Store**: Global state management
- **Lib**: Utility functions and helpers

## Testing

- Backend: Run tests with `pytest` (when implemented)
- Frontend: Run tests with `npm test` (when implemented)
- Use `/qa` skill from gstack for end-to-end testing
