# AI Career Co-pilot 部署指南

## 部署状态

### 前端（已部署）
- **平台**: Vercel
- **地址**: https://ai-career-copilot-pewgaarw2-dession-wus-projects.vercel.app
- **状态**: 构建中/已完成

### 后端（待部署）
- **平台**: Render
- **地址**: https://ai-career-copilot-api.onrender.com (预计)
- **状态**: 需要手动部署

---

## 后端部署步骤（Render）

### 1. 注册 Render 账号
访问 https://render.com 并注册账号（支持 GitHub 账号登录）

### 2. 创建 PostgreSQL 数据库
1. 在 Render Dashboard 点击 "New +" → "PostgreSQL"
2. 配置：
   - **Name**: career-copilot-db
   - **Database**: career_copilot
   - **User**: career_copilot
   - **Plan**: Free
3. 创建后保存 **Internal Database URL**

### 3. 创建 Web Service
1. 点击 "New +" → "Web Service"
2. 连接 Git 仓库（需要先将代码推送到 GitHub/GitLab）
3. 配置：
   - **Name**: ai-career-copilot-api
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

### 4. 设置环境变量
在 Render Dashboard → Web Service → Environment 中添加：

```
DATABASE_URL=<PostgreSQL Internal Database URL>
SECRET_KEY=<随机生成的密钥>
OPENAI_API_KEY=<你的 OpenAI API 密钥>
ANTHROPIC_API_KEY=<你的 Anthropic API 密钥（可选）>
CORS_ORIGINS_JSON=["https://ai-career-copilot-pewgaarw2-dession-wus-projects.vercel.app"]
UPLOAD_DIR=/tmp/uploads
```

### 5. 部署
点击 "Deploy" 开始部署

---

## 前端环境变量更新

部署完成后，需要在 Vercel 更新 API 地址：

```bash
vercel env add NEXT_PUBLIC_API_URL production --scope "dession-wus-projects"
# 输入: https://ai-career-copilot-api.onrender.com
```

然后重新部署前端：
```bash
vercel deploy --prod --scope "dession-wus-projects"
```

---

## 数据库迁移

后端首次启动后，需要创建数据库表：

```bash
# 在 Render Shell 中执行
cd backend
python -c "from app.database import init_db; init_db()"
```

或使用 Alembic 迁移：
```bash
cd backend
alembic upgrade head
```

---

## 监控与维护

### 免费额度监控
| 服务 | 免费额度 | 监控链接 |
|------|---------|---------|
| Vercel | 100GB/月 | https://vercel.com/dashboard |
| Render | 750小时/月 | https://dashboard.render.com |
| PostgreSQL | 500MB | https://dashboard.render.com |

### 保持 Render 实例活跃
免费实例会在 15 分钟无活动后休眠。可以使用 UptimeRobot 定时 ping：
- 注册 https://uptimerobot.com
- 添加监控: https://ai-career-copilot-api.onrender.com/health
- 设置每 5 分钟检查一次

---

## 故障排除

### 前端构建失败
检查 Vercel 构建日志，常见问题：
- 依赖缺失: 确保 package.json 完整
- 环境变量: 确认 NEXT_PUBLIC_API_URL 已设置

### 后端启动失败
检查 Render 日志，常见问题：
- 数据库连接失败: 确认 DATABASE_URL 正确
- 端口冲突: Render 自动分配 PORT 环境变量
- 依赖安装失败: 确认 requirements.txt 完整

### CORS 错误
确认后端 CORS_ORIGINS_JSON 包含前端域名

---

## 联系方式

如有部署问题，请检查各平台的文档：
- Vercel: https://vercel.com/docs
- Render: https://render.com/docs
