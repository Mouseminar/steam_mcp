#!/usr/bin/env python3
"""
测试脚本：验证 FastMCP 在阿里云环境的启动
用于诊断 412 错误
"""
import os
import sys
import time

print("="*70)
print("🔍 FastMCP 启动诊断测试")
print("="*70)

# 1. 环境检查
print("\n📋 环境信息:")
print(f"  Python版本: {sys.version}")
print(f"  工作目录: {os.getcwd()}")
print(f"  FC_RUNTIME: {os.environ.get('FC_RUNTIME', '未设置')}")
print(f"  FC_SERVER_PORT: {os.environ.get('FC_SERVER_PORT', '未设置')}")
print(f"  FC_FUNCTION_NAME: {os.environ.get('FC_FUNCTION_NAME', '未设置')}")

# 2. 依赖检查
print("\n📦 依赖检查:")
try:
    import fastmcp
    print(f"  ✓ fastmcp: {fastmcp.__version__ if hasattr(fastmcp, '__version__') else 'installed'}")
except ImportError as e:
    print(f"  ✗ fastmcp: {e}")
    sys.exit(1)

try:
    import uvicorn
    print(f"  ✓ uvicorn: {uvicorn.__version__ if hasattr(uvicorn, '__version__') else 'installed'}")
except ImportError as e:
    print(f"  ✗ uvicorn: {e}")

# 3. 创建最小 MCP 服务器
print("\n🚀 创建最小 MCP 服务器:")
try:
    from fastmcp import FastMCP
    
    mcp = FastMCP("test-server")
    
    @mcp.tool()
    async def test_tool() -> str:
        """测试工具"""
        return "OK"
    
    print("  ✓ MCP 服务器创建成功")
    
    # 4. 尝试启动
    port = int(os.environ.get('FC_SERVER_PORT', '8000'))
    print(f"\n🎯 启动配置:")
    print(f"  Host: 0.0.0.0")
    print(f"  Port: {port}")
    print(f"  Path: /sse")
    print(f"  Transport: sse")
    
    print("\n⏱️  启动计时开始...")
    start_time = time.time()
    
    # 启动服务器
    print("🔄 调用 mcp.run()...", flush=True)
    mcp.run(
        transport="sse",
        host="0.0.0.0",
        port=port,
        path="/sse",
        log_level="debug"
    )
    
except Exception as e:
    print(f"\n❌ 启动失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
