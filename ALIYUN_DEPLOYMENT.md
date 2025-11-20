# 阿里云函数计算部署指南

## 部署配置

### 环境要求
- **运行环境**: Python 3.12
- **传输类型**: SSE (Server-Sent Events)
- **监听端口**: 8000
- **启动命令**: `python mcp_server.py`

### 函数计算配置
```yaml
运行环境: python3.12
运行时类型: custom.debian12
启动命令: python mcp_server.py
监听端口: 8000
超时时间: 600秒
内存: 2048 MB
CPU: 1 核
磁盘大小: 512 MB
实例并发: 200
会话亲和性: MCP_SSE
会话路径: /sse
每实例会话并发: 20
```

### 层配置
需要添加以下层：
1. `acs:fc:cn-hangzhou:1730431480417716:layers/MCP-Runtime-V2/versions/1`
2. `acs:fc:cn-hangzhou:official:layers/Python312/versions/1`

### 构建命令
```bash
在路径在 . 下运行 pip install -r requirements.txt
```

### 环境变量
确保设置以下环境变量：
- `DASHSCOPE_API_KEY`: 阿里云 DashScope API 密钥
- `DASHSCOPE_BASE_URL`: https://dashscope.aliyuncs.com/compatible-mode/v1
- `FC_SERVER_PORT`: 8000 (自动注入)
- `FC_RUNTIME`: 函数计算运行时标识 (自动注入)

## 问题排查

### 412 错误 (Precondition Failed)
**症状**: 部署后访问 SSE 端点返回 412 状态码

**可能原因**:
1. 服务启动超时 - 阿里云健康检查在服务启动前就开始
2. SSE 路径配置不匹配
3. 端口监听问题
4. 依赖安装失败

**解决方案**:
1. **加快启动速度**:
   - 减少导入模块数量
   - 延迟加载重型依赖
   - 优化配置加载逻辑

2. **确认配置一致性**:
   ```python
   # mcp_server.py 中确保：
   port = int(os.environ.get('FC_SERVER_PORT', '8000'))
   mcp.run(
       transport="sse",
       host="0.0.0.0",
       port=port,
       path="/sse"  # 必须与配置中的 sseEndpointPath 一致
   )
   ```

3. **检查日志**:
   - 查看函数计算日志，确认服务是否成功启动
   - 查看是否有 Python 异常或导入错误
   - 确认端口绑定成功

4. **验证依赖安装**:
   - 确保 `requirements.txt` 中的所有包都能成功安装
   - 检查是否有版本冲突
   - 确认所有包与 Python 3.12 兼容

### 常见错误

#### 1. 导入错误
```
ModuleNotFoundError: No module named 'xxx'
```
**解决**: 确保模块在 `requirements.txt` 中，且构建命令执行成功

#### 2. 超时错误
```
Function timeout after 600 seconds
```
**解决**: 
- 增加超时时间配置
- 优化代码性能
- 减少 max_results 参数

#### 3. 内存不足
```
Out of memory
```
**解决**: 增加内存配置到 3072 MB 或更高

## 性能优化建议

### 1. 冷启动优化
- 使用预留实例保持容器温热
- 减少全局导入的模块
- 使用懒加载模式

### 2. 并发配置
```yaml
实例并发: 200
每实例会话并发: 20
```
根据实际负载调整这些参数

### 3. 日志级别
生产环境建议使用 `INFO` 而不是 `DEBUG`，减少日志开销

## 测试验证

### 1. 健康检查
部署后访问 SSE 端点验证：
```bash
curl -N https://your-function-url/sse
```

应该看到 SSE 连接建立，持续输出心跳

### 2. 工具调用测试
使用 MCP 客户端测试各个工具是否正常工作

### 3. 性能测试
- 测试冷启动时间
- 测试并发处理能力
- 监控内存使用情况

## 部署清单

部署前确认：
- [x] 代码已适配阿里云环境（端口、环境变量检测）
- [x] requirements.txt 包含所有依赖
- [x] 环境变量已正确配置
- [x] 层配置正确
- [x] 启动命令正确
- [x] SSE 路径配置一致
- [x] 超时和资源配置合理

## 代码改动说明

### mcp_server.py
1. **环境检测**: 添加 `IS_ALIYUN_FC` 标志检测阿里云环境
2. **动态端口**: 从 `FC_SERVER_PORT` 环境变量读取端口
3. **日志优化**: 在阿里云环境使用 `info` 级别而非 `debug`
4. **启动监控**: 记录启动时间，便于优化冷启动
5. **错误处理**: 增强异常捕获和日志记录

### aliyun_start.sh (可选)
备用启动脚本，包含更多诊断信息

## 监控和维护

### 关键指标
- 冷启动时间
- 平均响应时间
- 错误率
- 内存使用率
- 并发连接数

### 日志位置
函数计算控制台 → 函数详情 → 日志查询

## 成本优化

1. **按量计费**: 适合低频使用场景
2. **预留实例**: 适合高频使用，减少冷启动
3. **合理配置资源**: 根据实际使用情况调整内存和 CPU

## 支持

遇到问题请检查：
1. 函数计算日志
2. 本地是否能正常运行
3. 环境变量是否正确
4. 依赖是否完整安装
