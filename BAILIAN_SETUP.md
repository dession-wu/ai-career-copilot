# 百炼配置
运营侧仅使用 BAILIAN_API_KEY 或 BAILIAN_API_KEY_FILE。后者是 Windows CryptProtectData LocalMachine 原始密文文件，禁止明文文件；Linux容器用环境变量注入。默认北京 https://dashscope.aliyuncs.com/compatible-mode/v1，qwen3.7-flash，enable_thinking=false。不要将Key写入前端或提交Git。
MODEL_DATA_DIR必须持久化，包括models.sqlite、model-encryption.key和usage.sqlite；Compose已配置private_model_data命名卷。备份/恢复三者必须一致。运营Key最终在本机安全输入，本实现不启动输入窗口。
每用户累计3次，个人Key优先，匿名不能使用运营Key。一个请求内多次invoke共用预留，成功响应且有模型内容才计数。流式中断在已有模型有效内容时结算。请勿将测试结果等同真实上游连通性验证。
幂等重放返回409避免重复扣次，客户端失败重试保持请求ID；个人Key保存前会发最小验证请求；多进程PID恢复有PID复用限制。这些是剩余验收项。

Windows未指定环境变量时，仅回退统一标准DPAPI文件 E:\podnotes\podnotes-server\config\ops-secrets\bailian-secret.bin。该文件仅管理员/SYSTEM可读，因此后端需提升权限运行，入口run-with-bailian.ps1会请求UAC并启动仅127.0.0.1监听的后端。不得提升公开前端或将密钥文件授予所有用户。容器不使用该Windows默认路径，仍显式注入运营环境变量。
