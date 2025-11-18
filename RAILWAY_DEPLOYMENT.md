# Railway 部署说明

## 部署步骤

### 1. 准备工作
确保你已经有：
- GitHub 账号
- Railway 账号（使用 GitHub 登录即可）
- OpenAI API Key

### 2. 将代码推送到 GitHub

⚠️ **重要安全提示**：
- `.env.example` 是配置模板，可以提交（不包含真实密钥）
- `.env` 包含真实密钥，已在 `.gitignore` 中，不会被提交
- 真实的 API Key 通过 Railway 后台配置，不要写在代码中

如果还没有推送到 GitHub，执行以下步骤：

```bash
# 初始化 git 仓库（如果还没有）
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit for Railway deployment"

# 添加远程仓库（替换成你的仓库地址）
git remote add origin https://github.com/your-username/your-repo-name.git

# 推送到 GitHub
git push -u origin main
```

### 3. 在 Railway 上部署

1. **登录 Railway**
   - 访问 https://railway.app/
   - 使用 GitHub 账号登录

2. **创建新项目**
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 授权 Railway 访问你的 GitHub
   - 选择你刚才推送的仓库

3. **配置环境变量**（⭐ 重要）
   
   Railway 会自动检测你的 Python 项目并开始部署。**必须**通过 Railway 后台设置环境变量：
   
   - 在 Railway 项目页面，点击你的服务
   - 点击 "Variables" 标签
   - 点击 "New Variable" 逐个添加以下环境变量：
   
     | 变量名 | 值 | 说明 |
     |--------|-----|------|
     | `OPENAI_API_KEY` | `sk-xxxxx` | 你的 OpenAI API 密钥 |
     | `OPENAI_API_BASE` | `https://api.openai.com/v1` | API 端点 |
     | `LLM_MODEL` | `gpt-4o-mini` | 使用的模型 |
     | `LLM_TIMEOUT` | `300` | 超时时间(秒) |
     | `STEAM_MAX_SEARCH_RESULTS` | `20` | 最大搜索结果数 |
     | `STEAM_MAX_OUTPUT_RESULTS` | `5` | 最大输出结果数 |
     | `LOG_LEVEL` | `INFO` | 日志级别 |
   
   ⚠️ **注意**：
   - 这些环境变量只存在于 Railway 服务器上
   - 不会被提交到 GitHub，保证密钥安全
   - Railway 会在运行时自动注入到你的应用中

4. **等待部署完成**
   - Railway 会自动安装依赖并启动你的服务
   - 在 "Deployments" 标签可以查看部署日志
   - 部署成功后，会看到 "Success" 标志

5. **获取公网 URL**
   - 在项目页面，点击 "Settings" 标签
   - 找到 "Networking" 部分
   - 点击 "Generate Domain"
   - Railway 会生成一个 `.railway.app` 域名
   - 你的 MCP 服务访问地址为：`https://your-app.railway.app/mcp`

### 4. 测试部署

使用你获得的 URL 测试服务：

```bash
# 健康检查
curl https://your-app.railway.app/mcp/health

# 测试 MCP 工具
# 使用你的 MCP 客户端连接到：https://your-app.railway.app/mcp
```

### 5. 在 Claude Desktop 中使用

编辑 Claude Desktop 的配置文件，添加你的 MCP 服务器：

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "steam-recommender": {
      "transport": "streamableHttp",
      "url": "https://your-app.railway.app/mcp"
    }
  }
}
```

### 常见问题

**Q: 部署失败怎么办？**
- 检查 Deployments 标签中的错误日志
- 确保所有环境变量都已正确设置
- 检查 requirements.txt 中的依赖是否正确

**Q: 服务启动后无法访问？**
- 确保 Railway 已经生成域名
- 检查服务是否成功绑定到 0.0.0.0:8000
- 查看服务日志是否有错误

**Q: 如何查看运行日志？**
- 在 Railway 项目页面点击你的服务
- 选择 "Deployments" 标签
- 点击最新的部署查看实时日志

**Q: Railway 免费额度是多少？**
- Railway 提供每月 $5 的免费额度
- 如果流量不大，免费额度足够使用
- 可以在 Project Settings 中设置预算上限

### 更新部署

当你修改代码后，只需推送到 GitHub：

```bash
git add .
git commit -m "Update description"
git push
```

Railway 会自动检测更新并重新部署。

### 监控和维护

- **查看运行状态**：在 Railway 项目页面实时监控 CPU、内存使用
- **查看日志**：随时检查应用日志排查问题
- **设置告警**：在 Settings 中配置部署失败或资源超限通知

---

## 项目文件说明

- `Procfile`: 告诉 Railway 如何启动应用
- `railway.toml`: Railway 部署配置
- `runtime.txt`: 指定 Python 版本
- `requirements.txt`: Python 依赖列表
- `.gitignore`: Git 忽略文件列表
