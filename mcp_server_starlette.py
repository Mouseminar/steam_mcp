"""
备用方案：使用原生 Starlette 实现 MCP SSE 服务器
解决 FastMCP 在阿里云函数计算环境的兼容性问题
"""
import os
import sys
import json
import asyncio
from typing import Any

# 添加src目录到路径
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import StreamingResponse, JSONResponse
from sse_starlette import EventSourceResponse
import uvicorn

from src.config_loader import config
from src.logger import logger
from dotenv import load_dotenv

load_dotenv()

# 检测运行环境
IS_ALIYUN_FC = os.environ.get('FC_RUNTIME') is not None

# MCP 协议消息
async def create_mcp_response(method: str, result: Any = None, error: Any = None):
    """创建 MCP 协议响应"""
    response = {
        "jsonrpc": "2.0",
        "id": 1
    }
    if error:
        response["error"] = error
    else:
        response["result"] = result
    return response


# SSE 端点
async def sse_endpoint(request):
    """SSE 连接端点"""
    logger.info(f"收到 SSE 连接请求: {request.client}")
    
    async def event_generator():
        """SSE 事件生成器"""
        # 发送初始连接消息
        yield {
            "event": "message",
            "data": json.dumps({
                "jsonrpc": "2.0",
                "method": "server/initialized",
                "params": {
                    "serverInfo": {
                        "name": "steam-game-recommender",
                        "version": "1.0.0"
                    }
                }
            })
        }
        
        # 保持连接
        while True:
            await asyncio.sleep(30)
            yield {
                "event": "ping",
                "data": "keepalive"
            }
    
    return EventSourceResponse(event_generator())


# 健康检查端点
async def health_check(request):
    """健康检查"""
    return JSONResponse({
        "status": "healthy",
        "service": "steam-mcp",
        "environment": "aliyun-fc" if IS_ALIYUN_FC else "other"
    })


# 根路径
async def root(request):
    """根路径"""
    return JSONResponse({
        "name": "Steam Game Recommender MCP Server",
        "version": "1.0.0",
        "transport": "sse",
        "endpoint": "/sse"
    })


# 创建应用
app = Starlette(
    debug=not IS_ALIYUN_FC,
    routes=[
        Route('/', root),
        Route('/health', health_check),
        Route('/sse', sse_endpoint),
    ]
)


def main():
    """启动服务器"""
    import time
    start_time = time.time()
    
    print("="*70, flush=True)
    print("🎮 Steam MCP 服务器 (Starlette 版本)", flush=True)
    print("="*70, flush=True)
    
    if IS_ALIYUN_FC:
        print(f"✓ 阿里云函数计算环境", flush=True)
        print(f"✓ Runtime: {os.environ.get('FC_RUNTIME')}", flush=True)
        print(f"✓ 函数: {os.environ.get('FC_FUNCTION_NAME')}", flush=True)
    
    port = int(os.environ.get('FC_SERVER_PORT', '8000'))
    print(f"✓ 端口: {port}", flush=True)
    print(f"✓ SSE 端点: /sse", flush=True)
    print(f"✓ 健康检查: /health", flush=True)
    
    startup_time = time.time() - start_time
    print(f"✓ 启动耗时: {startup_time:.3f}秒", flush=True)
    print("="*70, flush=True)
    
    logger.info(f"服务器启动: port={port}")
    
    # 启动 Uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
