# Career Guide 小程序开发

新增工程在 `miniprogram/`，网页前端仍位于 `frontend/`。根目录脚本已移除不存在的 app workspace，不把原生小程序当 Next.js 构建。

## 本地后端

在独立 Python 3.12 虚拟环境安装 `backend/requirements.txt`，测试额外安装 pytest/httpx。使用 UTF-8 运行 Python，避免 Windows pip 读取中文注释时出错。

进入 backend 后设置环境变量 SECRET_KEY（自行生成，不写入前端）、DATABASE_URL（全新测试 SQLite 的绝对路径）、UPLOAD_DIR（测试目录）；启动 `python -m uvicorn app.main:app --host 127.0.0.1 --port 8020`。不要直接复用旧数据库、生产密钥或真实简历作测试。开发密钥更换后已有 token 失效，需要重新登录。

微信登录另需服务端环境变量 WECHAT_APP_ID / WECHAT_APP_SECRET；目前用户尚未注册独立 AppID。不要将播客项目 AppID/密钥填入本工程。配置缺失时微信登录返回 503，账号注册登录仍可本地使用。

## 验证

根目录 `npm run test:mini` 执行客户端测试；backend 内 `python -m pytest tests -q` 执行后端测试。

`npm run check:mini:release` 是发布配置门禁；默认开发配置必须失败。它不代替平台审核或真机验证。配置合法域名需要分别覆盖 request / uploadFile / downloadFile。

## 数据库变更

新增 wechat_identities 表，以 app_id+openid 唯一映射旧 User。不会按同名或邮箱合并旧账户。全新开发数据库由 init_db 建表；已有数据库升级需先进行一致性备份，确认 Alembic 当前修订再按迁移链执行。005 是增量迁移，不应在未确认迁移状态的历史数据库上盲目执行。保留回滚备份，不能删除旧表。

## 交付边界

已实现原生首版核心流程及基础匹配；真实模型模式、扫描件 OCR、大文件后台任务在进程重启后的持久恢复、真实微信登录、PDF 渲染服务、模拟器及 iOS/Android 真机验收仍需补齐或验证。当前服务无 PDF 渲染服务时明确回退 Markdown，不冒充 PDF。当前上传任务仍为既有后端内存状态，页面可恢复轮询但服务重启后任务不能续跑。

未新增付费、招聘信息发布或自动投递。未提交审核、上传体验版或正式发布。备案、类目、隐私主体/联系渠道需为 Career Guide 单独确认，不自动沿用播客状态。
