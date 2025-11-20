#!/usr/bin/env python3
"""
启动包装脚本 - 确保日志输出到 stdout
用于阿里云函数计算诊断
"""
import sys
import os

# 强制无缓冲输出
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)

print("="*70, flush=True)
print("🚀 启动包装脚本", flush=True)
print("="*70, flush=True)
print(f"工作目录: {os.getcwd()}", flush=True)
print(f"Python: {sys.executable}", flush=True)
print(f"版本: {sys.version}", flush=True)
print(f"环境变量 FC_SERVER_PORT: {os.environ.get('FC_SERVER_PORT', '未设置')}", flush=True)
print(f"环境变量 FC_RUNTIME: {os.environ.get('FC_RUNTIME', '未设置')}", flush=True)
print("="*70, flush=True)

# 导入并运行 mcp_server
try:
    print("🔄 导入 mcp_server 模块...", flush=True)
    import mcp_server
    
    print("🔄 调用 mcp_server.main()...", flush=True)
    mcp_server.main()
    
except Exception as e:
    print(f"❌ 启动失败: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)
