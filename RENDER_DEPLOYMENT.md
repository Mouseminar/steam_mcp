# Render 部署说明（完全免费 🎉）

## 为什么选择 Render？

✅ **完全免费** - 不需要信用卡
✅ **自动部署** - 推送到 GitHub 自动更新
✅ **简单易用** - 几分钟完成部署
⚠️ **注意** - 免费版服务闲置 15 分钟后会休眠，首次访问需要等待 30-60 秒唤醒

## 🚀 部署步骤

### 1. 确保代码已推送到 GitHub

你的代码已经在：https://github.com/Mouseminar/steam_mcp

### 2. 注册 Render 账号

1. 访问 **https://render.com/**
2. 点击右上角 **Sign Up**
3. 选择 **Sign up with GitHub**（用 GitHub 账号登录，最方便）
4. 授权 Render 访问你的 GitHub

### 3. 创建新的 Web Service

1. 登录后，点击 **Dashboard** 或 **New +** 按钮
2. 选择 **Web Service**
3. 选择 **Build and deploy from a Git repository**
4. 点击 **Next**

### 4. 连接 GitHub 仓库

1. 在仓库列表中找到 `Mouseminar/steam_mcp`
   - 如果看不到，点击 **Configure account** 授权访问该仓库
2. 点击仓库右侧的 **Connect** 按钮

### 5. 配置服务

Render 会自动检测到 `render.yaml` 配置文件，大部分设置已自动填充：

- **Name**: `steam-mcp-server`（可自定义）
- **Region**: 选择 `Singapore (Southeast Asia)` 或 `Oregon (US West)`（距离中国较近）
- **Branch**: `main`
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python mcp_server.py`
- **Instance Type**: 选择 **Free** 💰

### 6. 配置环境变量（⭐ 重要）

在 **Environment Variables** 部分，Render 会自动从 `render.yaml` 读取大部分变量，但你需要**手动添加你的 API Key**：

点击 **Add Environment Variable**，添加：

| Key | Value |
|-----|-------|
| `DASHSCOPE_API_KEY` | `sk-7c9a13f21d3442e097f9d46f1e3495db` |

其他变量应该已经自动填充了，确认以下变量存在：
- `DASHSCOPE_BASE_URL`
- `LLM_MODEL`
- `LLM_TIMEOUT`
- `STEAM_MAX_SEARCH_RESULTS`
- `STEAM_MAX_OUTPUT_RESULTS`
- `LOG_LEVEL`

### 7. 开始部署

1. 滚动到底部，点击 **Create Web Service**
2. Render 开始构建和部署（大约 2-5 分钟）
3. 你可以在页面上实时查看部署日志

### 8. 获取公网 URL

部署成功后，你会在页面顶部看到你的服务 URL：

```
https://steam-mcp-server.onrender.com
```

你的 MCP 服务访问地址是：
```
https://steam-mcp-server.onrender.com/mcp
```

（实际 URL 中的 `steam-mcp-server` 部分可能会不同，取决于你的服务名称）

## 🧪 测试部署

### 方式 1：浏览器测试

访问：`https://your-service.onrender.com/mcp`

### 方式 2：在 Claude Desktop 中使用

编辑 Claude Desktop 配置文件：

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "steam-recommender": {
      "transport": "streamableHttp",
      "url": "https://your-service.onrender.com/mcp"
    }
  }
}
```

重启 Claude Desktop，你应该能看到 Steam 推荐工具了！

## 📊 监控和维护

### 查看日志
1. 在 Render Dashboard 点击你的服务
2. 点击 **Logs** 标签
3. 实时查看应用运行日志

### 查看状态
- **Events** 标签：查看部署历史
- **Metrics** 标签：查看流量和性能

### 重新部署
Render 会自动监控你的 GitHub 仓库：
- 每次推送到 `main` 分支时自动重新部署
- 也可以手动点击 **Manual Deploy** → **Deploy latest commit**

## ⚠️ 免费版限制

- **休眠机制**: 闲置 15 分钟后服务会休眠
- **首次访问**: 休眠后首次访问需要等待 30-60 秒唤醒
- **带宽限制**: 每月 100GB 流量（对于 MCP 服务足够了）
- **构建时间**: 免费版构建可能稍慢

**解决方案**：
- 可以使用免费的 Uptime 监控服务（如 UptimeRobot）每 14 分钟 ping 一次，保持服务活跃
- 或者升级到付费版（$7/月），无休眠限制

## 🔧 常见问题

**Q: 部署失败怎么办？**
- 查看 Logs 标签中的构建日志
- 确保 requirements.txt 中的依赖正确
- 确保环境变量已正确设置

**Q: 访问 URL 显示错误？**
- 确认服务状态是 "Live"（绿色）
- 查看 Logs 确认应用已启动
- 确认访问的是 `/mcp` 端点，不是根路径

**Q: 如何更新代码？**
- 推送到 GitHub，Render 自动部署
- 或在 Render Dashboard 手动触发部署

**Q: 如何删除服务？**
- 在服务页面点击 Settings
- 滚动到底部点击 "Delete Web Service"

## 🎯 下一步

部署成功后，你可以：
1. 在 Claude Desktop 中配置并使用
2. 设置自定义域名（可选，需要 DNS 配置）
3. 配置 Uptime 监控避免休眠

---

**有问题？** 查看 Render 日志或联系支持！
