"""
Steam游戏推荐MCP服务器
提供智能游戏推荐服务的MCP接口
"""
import asyncio
import json
import sys
import os
from typing import Optional

# 添加src目录到路径
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

from fastmcp import FastMCP
from dotenv import load_dotenv
from src.recommendation_agent import SteamRecommendationAgent
from src.config_loader import config
from src.logger import logger

# 加载环境变量
load_dotenv()

# 创建MCP服务器实例
mcp = FastMCP("steam-game-recommender 🎮")


@mcp.tool()
async def recommend_games(
    user_query: str,
    max_results: int = 5
) -> str:
    """
    根据用户需求推荐Steam游戏（智能推荐，包含LLM评分）
    
    Args:
        user_query: 用户的游戏推荐需求描述，例如："推荐一些开放世界RPG游戏，100元以内"
        max_results: 返回的最大推荐游戏数量，默认5款（建议≤10，过多会很慢）
        
    Returns:
        JSON格式的推荐结果，包含游戏列表及详细信息
    
    注意：此工具会为每个游戏调用LLM生成推荐理由，较慢但结果精准。
    如需快速响应，请使用 quick_search_games 工具。
    """
    logger.info(f"收到MCP推荐请求: {user_query}, max_results={max_results}")
    print(f"\n🎮 MCP服务器收到请求: {user_query}")
    
    try:
        # 创建推荐Agent
        agent = SteamRecommendationAgent()
        
        # 获取推荐结果
        result = agent.recommend_games(user_query, max_output_results=max_results)
        
        # 格式化返回结果
        response = {
            'success': True,
            'query': user_query,
            'total_found': result.get('total_found', 0),
            'total_evaluated': result.get('total_evaluated', 0),
            'recommendations_count': len(result['recommendations']),
            'recommendations': result['recommendations']
        }
        
        logger.info(f"MCP推荐完成: 返回{len(result['recommendations'])}款游戏")
        return json.dumps(response, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_msg = f"推荐失败: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        
        return json.dumps({
            'success': False,
            'error': error_msg,
            'query': user_query
        }, ensure_ascii=False, indent=2)


@mcp.tool()
async def search_games(
    keywords: str,
    max_price: float = None,
    max_results: int = 10
) -> str:
    """
    快速搜索Steam游戏（不使用LLM，响应速度快）
    
    Args:
        keywords: 搜索关键词，例如："open world rpg", "射击游戏"
        max_price: 最大价格（人民币），例如：100.0，不设置则不限价格
        max_results: 返回的最大游戏数量，默认10款
        
    Returns:
        JSON格式的搜索结果，包含游戏列表及基本信息
    
    优势：响应速度快（秒级），适合快速查询
    """
    logger.info(f"收到快速搜索请求: {keywords}, max_price={max_price}, max_results={max_results}")
    print(f"\n🔍 MCP快速搜索: {keywords}")
    
    try:
        from src.steam_crawler import SteamCrawler
        
        crawler = SteamCrawler()
        games = crawler.search_games(keywords, max_price=max_price, max_results=max_results)
        
        response = {
            'success': True,
            'keywords': keywords,
            'max_price': max_price,
            'total_found': len(games),
            'games': games
        }
        
        logger.info(f"快速搜索完成: 返回{len(games)}款游戏")
        return json.dumps(response, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_msg = f"搜索失败: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        
        return json.dumps({
            'success': False,
            'error': error_msg,
            'keywords': keywords
        }, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_discounted_games(
    min_discount: int = 0,
    max_price: float = None,
    max_results: int = 20
) -> str:
    """
    获取当前正在打折的Steam游戏
    
    Args:
        min_discount: 最低折扣百分比 (0-100)，例如：50 表示至少5折，默认0（所有折扣）
        max_price: 最大价格（人民币），例如：100.0，不设置则不限价格
        max_results: 返回的最大游戏数量，默认20款
        
    Returns:
        JSON格式的折扣游戏列表，按折扣力度排序
    
    适用场景：寻找优惠促销、节日特卖、性价比游戏
    """
    logger.info(f"收到折扣游戏请求: min_discount={min_discount}%, max_price={max_price}, max_results={max_results}")
    print(f"\n🎁 MCP获取折扣游戏: 折扣≥{min_discount}%")
    
    try:
        from src.steam_crawler import SteamCrawler
        
        crawler = SteamCrawler()
        games = crawler.get_discounted_games(
            min_discount=min_discount,
            max_price=max_price,
            max_results=max_results
        )
        
        response = {
            'success': True,
            'min_discount': min_discount,
            'max_price': max_price,
            'total_found': len(games),
            'games': games
        }
        
        logger.info(f"获取折扣游戏完成: 返回{len(games)}款游戏")
        return json.dumps(response, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_msg = f"获取折扣游戏失败: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        
        return json.dumps({
            'success': False,
            'error': error_msg
        }, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_game_details(
    game_identifier: str
) -> str:
    """
    获取单个游戏的详细信息
    
    Args:
        game_identifier: 游戏名称或Steam AppID，例如："艾尔登法环" 或 "1245620"
        
    Returns:
        JSON格式的游戏详细信息，包括：
        - 基本信息（名称、价格、折扣）
        - 详细描述
        - 开发商/发行商
        - 游戏类型/标签
        - 支持语言
        - 系统要求
        - 评分信息
        - 截图链接
    
    适用场景：了解某款游戏的完整信息、对比游戏特性
    """
    logger.info(f"收到游戏详情请求: {game_identifier}")
    print(f"\n📖 MCP获取游戏详情: {game_identifier}")
    
    try:
        from src.steam_crawler import SteamCrawler
        
        crawler = SteamCrawler()
        
        # 判断是AppID还是游戏名称
        if game_identifier.isdigit():
            # 是AppID
            game_details = crawler.get_game_details(game_identifier)
        else:
            # 是游戏名称
            game_details = crawler.get_game_by_name(game_identifier)
        
        if game_details:
            response = {
                'success': True,
                'game_identifier': game_identifier,
                'details': game_details
            }
            logger.info(f"获取游戏详情成功: {game_details.get('name', 'Unknown')}")
        else:
            response = {
                'success': False,
                'error': f"未找到游戏: {game_identifier}",
                'game_identifier': game_identifier
            }
            logger.warning(f"未找到游戏: {game_identifier}")
        
        return json.dumps(response, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_msg = f"获取游戏详情失败: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        
        return json.dumps({
            'success': False,
            'error': error_msg,
            'game_identifier': game_identifier
        }, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_top_games(
    max_results: int = 20,
    filter_type: str = 'topsellers'
) -> str:
    """
    获取Steam热门游戏排行榜
    
    Args:
        max_results: 返回的最大游戏数量，默认20款
        filter_type: 排行榜类型，可选值：
            - 'topsellers': 畅销榜（默认，最受欢迎）
            - 'popularnew': 热门新品
            - 'trendingweek': 本周热门趋势
        
    Returns:
        JSON格式的热门游戏列表，包含排名信息
    
    适用场景：发现当前流行游戏、了解市场趋势、找热门游戏
    """
    logger.info(f"收到热门游戏请求: filter_type={filter_type}, max_results={max_results}")
    print(f"\n🔥 MCP获取热门游戏: {filter_type}")
    
    try:
        from src.steam_crawler import SteamCrawler
        
        crawler = SteamCrawler()
        games = crawler.get_top_games(
            max_results=max_results,
            filter_type=filter_type
        )
        
        response = {
            'success': True,
            'filter_type': filter_type,
            'total_found': len(games),
            'games': games
        }
        
        logger.info(f"获取热门游戏完成: 返回{len(games)}款游戏")
        return json.dumps(response, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_msg = f"获取热门游戏失败: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        
        return json.dumps({
            'success': False,
            'error': error_msg,
            'filter_type': filter_type
        }, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_free_games(
    max_results: int = 20,
    tags: list = None
) -> str:
    """
    获取Steam免费游戏列表
    
    Args:
        max_results: 返回的最大游戏数量，默认20款
        tags: 可选的游戏标签过滤列表，例如：["动作", "冒险", "多人"]
        
    Returns:
        JSON格式的免费游戏列表
    
    适用场景：寻找免费游戏、预算为零的用户、试玩体验
    """
    logger.info(f"收到免费游戏请求: max_results={max_results}, tags={tags}")
    print(f"\n🆓 MCP获取免费游戏")
    
    try:
        from src.steam_crawler import SteamCrawler
        
        crawler = SteamCrawler()
        games = crawler.get_free_games(
            max_results=max_results,
            tags=tags
        )
        
        response = {
            'success': True,
            'tags_filter': tags,
            'total_found': len(games),
            'games': games
        }
        
        logger.info(f"获取免费游戏完成: 返回{len(games)}款游戏")
        return json.dumps(response, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_msg = f"获取免费游戏失败: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        
        return json.dumps({
            'success': False,
            'error': error_msg
        }, ensure_ascii=False, indent=2)


def main():
    """启动MCP服务器"""
    print("="*70)
    print("🎮 Steam游戏推荐MCP服务器")
    print("="*70)
    print(f"LLM模型: {config.get('llm.model')}")
    print(f"LLM超时: {config.get('llm.timeout', 300)}秒")
    print(f"最大搜索结果: {config.get('steam.max_search_results')}")
    print(f"最大输出结果: {config.get('steam.max_output_results')}")
    print(f"⚠️  智能推荐工具可能需要1-3分钟，请耐心等待")
    print("="*70)
    
    logger.info("="*60)
    logger.info("Steam MCP服务器启动")
    logger.info("="*60)
    
    # 启动MCP服务器
    mcp.run(
        transport="streamableHttp",  # 使用 streamableHttp 传输
        host="0.0.0.0", 
        port=8000,
        path="/mcp",
        log_level="debug",
    )


if __name__ == "__main__":
    main()
