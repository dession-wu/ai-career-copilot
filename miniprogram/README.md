# 简历指南 原生微信小程序

用微信开发者工具导入本目录。默认 touristappid 与 http://127.0.0.1:8020 仅供本地开发；project.config.json 的 urlCheck 默认开启。开发者如需访问本地 HTTP，必须自行在开发者工具本地设置选择对应调试设置，正式版保持域名校验。真机的 127.0.0.1 指手机本身，需要自行配置可访问服务。

无需依赖。运行 node --test tests/*.test.js；node scripts/preflight.js 执行发布配置预检，当前示例必须失败。正式发布前填写独立真实 AppID、HTTPS API 域名和隐私联系主体，配置 request/uploadFile/downloadFile 合法域名、正式隐私政策并完成真机验收。本工程不包含任何真实身份或密钥，不复用其他项目身份。

认证 token 使用微信本地存储；不持久化简历编辑草稿。异步上传任务按 /auth/me 返回的用户 ID 隔离保存，隐藏停止轮询、回来继续，15 分钟终止。账号切换及 401 清理本机个人状态，请求响应绑定会话代次。结构化编辑递归保留未知字段。PDF 下载先检查文件签名，JSON Markdown 降级展示并可复制。

当前用户尚未注册小程序 AppID，因此不能完成真实微信身份与官方模拟器验收。发布前须设置 development: false，填写 privacyOperator 与 privacyContact。发布预检同时读取 project.private.config.json 的 urlCheck 覆盖值。
