# 🚀 AI Career Co-pilot (智能求职副驾) - 项目蓝图与开发指南

## 1. 项目概述与核心愿景
**项目名称：** TailorCV / AI Career Co-pilot
**核心愿景：** 打造一个基于真实经历的、拒绝 AI 杜撰的智能求职辅助平台。
**解决痛点：** 
1. 简历海投匹配度低，无法通过 ATS（自动追踪系统）。
2. AI 修改简历容易胡编乱造，导致面试露馅。
3. 面试准备缺乏针对特定 JD 的实战模拟。
**核心原则（Agent 必须遵守）：** **严格基于事实（Fact-based Only）**。所有的优化只是“提取、重组、润色和关键词映射”，绝对禁止凭空捏造技能或经历。

---

## 2. 技术栈选型 (Tech Stack)
Agent 在初始化项目时，必须严格采用以下技术栈：

*   **前端 (Frontend):** 
    *   框架：Next.js (App Router, React 18+)
    *   样式：Tailwind CSS + Shadcn UI (用于快速搭建高质量组件)
    *   状态管理：Zustand (轻量级)
*   **后端 (Backend):** 
    *   框架：Python 3.10+ + FastAPI (高性能，原生支持异步和 OpenAPI)
    *   数据校验：Pydantic V2
    *   ORM：SQLAlchemy + SQLite (MVP 阶段优先使用 SQLite，后续可平滑迁移至 PostgreSQL)
*   **AI 与大模型 (AI & LLM):** 
    *   编排框架：LangChain (Python)
    *   文档解析：PyPDF2 / pdfplumber / MarkItDown
    *   大模型接口：OpenAI API 格式 (兼容 GPT-4o / Claude 3.5 / 深度求索等)

---

## 3. 核心功能模块 (MVP 阶段定义)

### 模块一：经历主数据资产库 (Career Vault)
*   **功能：** 用户上传原始简历（PDF/Word），系统解析并结构化提取为：个人信息、教育经历、技能清单（分级）、工作经历（包含具体项目、STAR 描述）。
*   **机制：** 这是唯一的“事实源 (Single Source of Truth)”。后续所有的简历生成，只能从这里“拿词”，不能“造词”。

### 模块二：JD 匹配度与差距分析 (Gap Analysis)
*   **功能：** 用户输入目标岗位的 JD 文本。系统对比 JD 与 Career Vault，输出：
    1. 匹配度评分 (0-100)。
    2. 匹配的关键词 / 缺失的关键词 (Skills Gap)。

### 模块三：简历精准定制 (Tailored Resume Generation)
*   **功能：** 基于 JD 要求的权重，从 Career Vault 中抽取相关经历，重写描述（向 JD 靠拢），并生成 Markdown 格式的定制简历。
*   **输出：** 提供 Web 端实时预览界面，并支持导出为排版干净的 PDF。

### 模块四：针对性面试题库 (Interview Prep)
*   **功能：** 结合生成的“定制简历”和“目标 JD”，AI 扮演面试官，生成 5-10 道极具针对性的面试题，并给出“考察意图”和“回答思路 (STAR 法则)”。

---

## 4. 数据库设计 (Database Schema)

Agent 请基于 SQLAlchemy 创建以下核心表结构：

1.  **User (用户表)**
    *   `id` (UUID, PK)
    *   `username` (String)
    *   `created_at` (DateTime)
2.  **Career_Vault (经历总库表)**
    *   `id` (UUID, PK)
    *   `user_id` (UUID, FK -> User.id)
    *   `raw_content` (Text) - 原始简历文本
    *   `structured_data` (JSON) - 解析后的结构化数据 (包含 skills, experiences, educations 等)
3.  **Job_Application (求职投递表/看板)**
    *   `id` (UUID, PK)
    *   `user_id` (UUID, FK -> User.id)
    *   `company_name` (String)
    *   `job_title` (String)
    *   `jd_text` (Text) - 目标岗位的 JD 原文
    *   `status` (String) - Enum: 'preparing', 'applied', 'interviewing', 'offered'
    *   `tailored_resume_md` (Text) - 为该岗位定制的简历内容 (Markdown)
    *   `match_score` (Integer) - 匹配度分数
4.  **Interview_Questions (面试题表)**
    *   `id` (UUID, PK)
    *   `application_id` (UUID, FK -> Job_Application.id)
    *   `question_text` (Text)
    *   `intent_analysis` (Text) - 考察意图
    *   `suggested_answer_star` (Text) - 建议回答框架

---

## 5. 核心 AI 工作流设计 (Prompt & Logic)

Agent 在编写 `services/llm_service.py` 时，必须实现以下严格的工作流：

### Workflow A: 防幻觉定制简历生成 (Anti-Hallucination Generation)
采用 **Map-Reduce** 或 **3步 Prompt 链**：
*   **Step 1: 提取与对标 (Extraction & Mapping)**
    *   *Prompt:* "分析输入的 JD，提取前 10 个核心硬技能和软技能。在用户的 Career Vault 中寻找是否有能够证明这些技能的经历。输出 JSON 映射表。"
*   **Step 2: 严格重写 (Strict Rewriting)**
    *   *System Prompt:* "你是高级简历顾问。你只能使用 `Career Vault` 中提供的事实。任务：根据 `Step 1` 的映射关系，重写工作经历描述。你可以修改动词（如：参与->主导）、调整语序、突出相关数据，但**绝对禁止**添加未提及的技术栈或虚构项目数据。"
*   **Step 3: 校验与 Diff (Verification)**
    *   *Logic:* 代码层面比对生成的简历和原始 Vault 里的技能词，如果出现了 Vault 里不存在的技术名词，触发警告或重新生成。

### Workflow B: 面试问题生成 (Mock Interview)
*   *Prompt:* "你现在是 [JD公司] 的技术/业务主管。请阅读该候选人的 [定制化简历] 和我们岗位的 [JD]。请设计 5 个只有真正做过这些项目且符合 JD 要求的候选人才能回答出的深度问题（Deep Dive）。不仅要问 'What'，还要问 'Why' 和 'How'。"

---

## 6. API 接口规范 (RESTful Endpoints)

Agent 请在 FastAPI 中实现以下核心路由 (Routers)：

*   **`POST /api/vault/upload`** 
    *   接收 PDF 文件，解析并提取文本，调用 LLM 结构化后存入 `Career_Vault`。
*   **`POST /api/jobs/analyze`**
    *   接收 JD 文本，基于用户的 Vault，返回匹配度评分和 Gap 分析 (缺失技能)。
*   **`POST /api/jobs/{job_id}/tailor-resume`**
    *   触发核心 AI 工作流，生成定制版的 Markdown 简历。
*   **`GET /api/jobs/{job_id}/interview-prep`**
    *   生成并返回针对该岗位的面试题及解析。
*   **`POST /api/export/pdf`**
    *   接收 Markdown 文本，使用如 `WeasyPrint` 或 `Puppeteer` 服务将其转换为高保真 PDF 返回给前端。

---

## 7. 前端界面设计需求 (UI/UX)

Agent 在构建 Next.js 页面时，应包含以下核心页面：

1.  **Dashboard (工作台 / 看板):**
    *   展示当前的求职状态 (Kanban 视图)。
    *   入口：上传更新“总库简历”，或“新建求职投递”。
2.  **Job Tailoring Page (简历定制工作区 - 核心交互区):**
    *   **左侧分栏：** JD 输入框与分析面板（展示雷达图、匹配分数、缺失技能标签）。
    *   **中间分栏：** AI 实时生成的 Markdown 简历预览器。
    *   **右侧分栏 (Copilot Chat)：** 聊天框，用户可以发指令微调（如：“把第二个项目描述得更偏向管理一点”）。
3.  **Interview Prep Page (面试准备区):**
    *   卡片式展示面试题。
    *   点击卡片翻转，显示“考察意图”和“我的简历中对应的 STAR 故事提示”。

---

## 8. Agent 执行指令 (给 AI 助手的行动纲领)

**请严格按照以下顺序执行开发任务（Do not skip steps）：**

1.  **Phase 1: 基础设施搭建**
    *   初始化 FastAPI 后端，配置 Pydantic、SQLAlchemy 和 SQLite。
    *   初始化 Next.js 前端，配置 Tailwind、Shadcn UI 和 Axios。
2.  **Phase 2: 后端数据流与 API**
    *   创建数据库模型 (Models)。
    *   实现简历解析逻辑（集成 PDF 提取库）。
    *   集成 LangChain，实现 `LLM_Service`，**必须严格植入第 5 节的防幻觉 Prompt**。
    *   完成所有 API 端点，并使用 Swagger UI (`/docs`) 进行测试验证。
3.  **Phase 3: 前端页面与联调**
    *   搭建左右分栏的“简历定制工作区” UI。
    *   联调 `/api/jobs/analyze` 和 `/api/jobs/tailor-resume`。
    *   实现 Markdown 到 PDF 的渲染与导出功能。
4.  **Phase 4: 面试模块与完善**
    *   实现面试题卡片的 UI 和后端生成逻辑。
    *   进行全局错误处理 (Error Handling) 和加载状态 (Loading States) 优化。

**(End of Document)**