"""
Steam MCP服务器测试客户端
用于测试MCP服务器的各个工具
"""
import asyncio
import json
from fastmcp import Client


async def test_recommend_games():
    """测试游戏推荐功能"""
    print("\n" + "="*70)
    print("测试1: 游戏推荐")
    print("="*70)
    
    async with Client("http://localhost:8000/mcp") as client:
        result = await client.call_tool(
            "recommend_games",
            {
                "user_query": "推荐一些开放世界RPG游戏，100元以内",
                "max_results": 3
            }
        )
        
        # 解析结果
        response = json.loads(result[0].text)
        
        print(f"\n✅ 推荐成功！")
        print(f"查询: {response['query']}")
        print(f"找到游戏: {response['total_found']}款")
        print(f"推荐游戏: {response['recommendations_count']}款\n")
        
        print("推荐列表:")
        for i, game in enumerate(response['recommendations'], 1):
            print(f"\n【{i}】{game['name']}")
            print(f"  价格: ¥{game['price']}")
            print(f"  评分: {game['recommendation_score']}/100")
            print(f"  推荐理由: {game['recommendation_reason']}")


async def test_search_games():
    """测试游戏搜索功能"""
    print("\n" + "="*70)
    print("测试2: 游戏搜索")
    print("="*70)
    
    async with Client("http://localhost:8000/mcp") as client:
        result = await client.call_tool(
            "search_steam_games",
            {
                "keywords": "rpg",
                "max_price": 50,
                "max_results": 5
            }
        )
        
        response = json.loads(result[0].text)
        
        print(f"\n✅ 搜索成功！")
        print(f"关键词: {response['keywords']}")
        print(f"找到: {response['count']}款游戏\n")
        
        for i, game in enumerate(response['games'], 1):
            print(f"{i}. {game['name']} - ¥{game['price']}")


async def test_analyze_requirement():
    """测试需求分析功能"""
    print("\n" + "="*70)
    print("测试3: 需求分析")
    print("="*70)
    
    async with Client("http://localhost:8000/mcp") as client:
        result = await client.call_tool(
            "analyze_user_requirement",
            {
                "user_query": "推荐一些双人合作的射击游戏，价格在80元以下"
            }
        )
        
        response = json.loads(result[0].text)
        analysis = response['analysis']
        
        print(f"\n✅ 分析成功！")
        print(f"原始查询: {response['query']}")
        print(f"\n分析结果:")
        print(f"  关键词: {', '.join(analysis['keywords'])}")
        print(f"  价格范围: ¥{analysis['min_price']} - ¥{analysis['max_price']}")
        print(f"  标签: {', '.join(analysis['tags'])}")
        print(f"  类型: {', '.join(analysis['genres'])}")


async def test_get_config():
    """测试获取配置功能"""
    print("\n" + "="*70)
    print("测试4: 获取服务器配置")
    print("="*70)
    
    async with Client("http://localhost:8000/mcp") as client:
        result = await client.call_tool("get_server_config", {})
        
        response = json.loads(result[0].text)
        config = response['config']
        
        print(f"\n✅ 配置获取成功！")
        print(f"  LLM模型: {config['llm_model']}")
        print(f"  最大搜索结果: {config['max_search_results']}")
        print(f"  最大输出结果: {config['max_output_results']}")
        print(f"  语言: {config['language']}")
        print(f"  国家代码: {config['country_code']}")


async def run_all_tests():
    """运行所有测试"""
    print("\n🎮 Steam MCP服务器测试客户端")
    print("="*70)
    
    try:
        # 测试1: 获取配置
        await test_get_config()
        
        # 测试2: 需求分析
        await test_analyze_requirement()
        
        # 测试3: 游戏搜索
        await test_search_games()
        
        # 测试4: 游戏推荐（最耗时）
        await test_recommend_games()
        
        print("\n" + "="*70)
        print("✅ 所有测试完成！")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("⚠️  请确保MCP服务器正在运行 (python mcp_server.py)")
    print("按Enter键开始测试...")
    input()
    
    asyncio.run(run_all_tests())
