"""
测试新增的MCP工具
"""
import sys
import os

# 添加src目录到路径
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

from src.steam_crawler import SteamCrawler


def test_search_games():
    """测试快速搜索功能"""
    print("\n" + "="*70)
    print("测试1: 快速搜索游戏 (search_games)")
    print("="*70)
    
    crawler = SteamCrawler()
    games = crawler.search_games("射击", max_price=100, max_results=5)
    
    print(f"\n✅ 找到 {len(games)} 款游戏:")
    for i, game in enumerate(games, 1):
        print(f"\n{i}. {game['name']}")
        print(f"   价格: ¥{game['price']}")
        print(f"   折扣: {game['discount']}%")
        print(f"   标签: {', '.join(game.get('tags', [])[:3])}")


def test_get_discounted_games():
    """测试获取折扣游戏"""
    print("\n" + "="*70)
    print("测试2: 获取折扣游戏 (get_discounted_games)")
    print("="*70)
    
    crawler = SteamCrawler()
    games = crawler.get_discounted_games(min_discount=60, max_price=100, max_results=5)
    
    print(f"\n✅ 找到 {len(games)} 款折扣游戏:")
    for i, game in enumerate(games, 1):
        print(f"\n{i}. {game['name']}")
        print(f"   现价: ¥{game['price']}")
        print(f"   折扣: -{game['discount']}%")


def test_get_game_details():
    """测试获取游戏详情"""
    print("\n" + "="*70)
    print("测试3: 获取游戏详情 (get_game_details)")
    print("="*70)
    
    crawler = SteamCrawler()
    
    # 测试通过游戏名称获取
    print("\n📖 方法1: 通过游戏名称获取")
    details = crawler.get_game_by_name("艾尔登法环")
    
    if details:
        print(f"\n游戏名称: {details['name']}")
        print(f"类型: {details['type']}")
        print(f"开发商: {', '.join(details.get('developers', []))}")
        print(f"发行商: {', '.join(details.get('publishers', []))}")
        print(f"发行日期: {details.get('release_date', 'N/A')}")
        print(f"价格: ¥{details['price']['current']}")
        if details['price']['discount'] > 0:
            print(f"折扣: -{details['price']['discount']}% (原价 ¥{details['price']['original']})")
        print(f"是否免费: {'是' if details.get('is_free') else '否'}")
        print(f"类型/标签: {', '.join(details.get('genres', []))}")
        print(f"Metacritic评分: {details.get('metacritic_score', 'N/A')}")
        print(f"推荐数: {details.get('recommendations', 'N/A')}")
        print(f"成就数: {details.get('achievements', 0)}")
        print(f"简介: {details.get('short_description', '')[:150]}...")
    
    # 测试通过AppID获取
    print("\n📖 方法2: 通过AppID获取")
    details2 = crawler.get_game_details("1245620")  # 艾尔登法环的AppID
    
    if details2:
        print(f"\n游戏名称: {details2['name']}")
        print(f"AppID: {details2['app_id']}")
        print(f"平台支持: Windows={details2.get('platforms', {}).get('windows', False)}, "
              f"Mac={details2.get('platforms', {}).get('mac', False)}, "
              f"Linux={details2.get('platforms', {}).get('linux', False)}")


def test_get_top_games():
    """测试获取热门游戏"""
    print("\n" + "="*70)
    print("测试4: 获取热门游戏 (get_top_games)")
    print("="*70)
    
    crawler = SteamCrawler()
    
    # 测试畅销榜
    print("\n🔥 获取畅销榜 Top 10")
    top_games = crawler.get_top_games(max_results=10, filter_type='topsellers')
    
    print(f"\n✅ 找到 {len(top_games)} 款畅销游戏:")
    for game in top_games[:5]:
        print(f"\n#{game['rank']} {game['name']}")
        print(f"   价格: ¥{game['price']}")
        if game['discount'] > 0:
            print(f"   折扣: -{game['discount']}%")
        print(f"   标签: {', '.join(game.get('tags', [])[:3])}")


def test_get_free_games():
    """测试获取免费游戏"""
    print("\n" + "="*70)
    print("测试5: 获取免费游戏 (get_free_games)")
    print("="*70)
    
    crawler = SteamCrawler()
    
    # 测试获取免费游戏
    print("\n🆓 获取免费游戏 Top 15")
    free_games = crawler.get_free_games(max_results=15)
    
    print(f"\n✅ 找到 {len(free_games)} 款免费游戏:")
    for i, game in enumerate(free_games[:5], 1):
        print(f"\n{i}. {game['name']}")
        print(f"   价格: 免费")
        print(f"   标签: {', '.join(game.get('tags', [])[:3])}")
        print(f"   简介: {game.get('description', '')[:80]}...")


def main():
    """运行所有测试"""
    print("\n" + "🎮"*35)
    print("Steam MCP 新工具测试")
    print("🎮"*35)
    
    try:
        test_search_games()
        test_get_discounted_games()
        test_get_game_details()
        test_get_top_games()
        test_get_free_games()
        
        print("\n" + "="*70)
        print("✅ 所有测试完成!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
