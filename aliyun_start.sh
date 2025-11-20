#!/bin/bash
# 阿里云函数计算启动脚本

echo "========================================="
echo "阿里云函数计算 - Steam MCP 服务器启动"
echo "========================================="
echo "当前目录: $(pwd)"
echo "Python版本: $(python --version 2>&1)"
echo "环境变量 FC_SERVER_PORT: ${FC_SERVER_PORT:-8000}"
echo "========================================="

# 检查必要文件
if [ ! -f "mcp_server.py" ]; then
    echo "错误: 找不到 mcp_server.py"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo "警告: 找不到 requirements.txt"
fi

# 列出当前目录文件
echo "当前目录文件:"
ls -la

# 启动服务器
echo "========================================="
echo "启动 MCP 服务器..."
echo "========================================="
exec python mcp_server.py
