"""
Steam游戏推荐Agent主程序
使用示例：python main.py "推荐一些开放世界RPG游戏，100元以内"
"""
import sys
import os

# 添加src目录到路径
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

from recommendation_agent import SteamRecommendationAgent
from config_loader import config
from logger import logger


def print_banner():
    """打印欢迎横幅"""
    banner = """
╔════════════════════════════════════════════════════════════╗
║           🎮 Steam游戏智能推荐Agent 🎮                      ║
║                                                            ║
║  基于LLM的智能游戏推荐系统                                  ║
║  支持需求分析、Steam搜索、智能评分                          ║
╚════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_recommendation_summary(recommendations: list):
    """打印推荐摘要"""
    print("\n" + "="*70)
    print(f"{'排名':<6} {'游戏名称':<30} {'价格':<10} {'评分':<8} {'折扣'}")
    print("="*70)
    
    for i, rec in enumerate(recommendations, 1):
        name = rec['name'][:28] + '..' if len(rec['name']) > 30 else rec['name']
        price = f"¥{rec['price']:.1f}"
        score = f"{rec['recommendation_score']}/100"
        discount = f"-{rec['discount']}%" if rec['discount'] > 0 else "无"
        
        print(f"{i:<6} {name:<30} {price:<10} {score:<8} {discount}")
    
    print("="*70)


def print_detailed_recommendation(rec: dict, rank: int):
    """打印详细推荐信息"""
    print(f"\n【推荐#{rank}】{rec['name']}")
    print(f"{'─'*70}")
    print(f"💰 价格: ¥{rec['price']:.1f}", end="")
    if rec['discount'] > 0:
        print(f" (原价¥{rec['original_price']:.1f}, 折扣{rec['discount']}%)", end="")
    print()
    
    print(f"⭐ 推荐指数: {rec['recommendation_score']}/100")
    print(f"📝 推荐理由: {rec['recommendation_reason']}")
    
    if rec.get('highlights'):
        print(f"✨ 游戏亮点: {' | '.join(rec['highlights'])}")
    
    if rec.get('tags'):
        print(f"🏷️  游戏标签: {', '.join(rec['tags'][:8])}")
    
    if rec.get('description'):
        desc = rec['description'][:150] + '...' if len(rec['description']) > 150 else rec['description']
        print(f"📖 游戏简介: {desc}")
    
    print(f"🔗 商店链接: {rec['url']}")
    print()

# python main.py "推荐一些双人格斗游戏，80元以内"

def main():
    """主程序"""
    print_banner()
    
    logger.info("="*60)
    logger.info("Steam游戏推荐Agent启动")
    logger.info("="*60)
    
    # 获取用户查询
    if len(sys.argv) > 1:
        user_query = ' '.join(sys.argv[1:])
    else:
        print("请输入您的游戏推荐需求（例如：推荐一些开放世界RPG游戏，100元以内）")
        user_query = input("\n🎯 您的需求: ").strip()
        
        if not user_query:
            print("❌ 需求不能为空！")
            logger.warning("用户输入为空")
            return
    
    print(f"\n{'='*70}")
    print(f"正在为您推荐游戏...")
    print(f"{'='*70}\n")
    
    # 创建Agent并获取推荐
    agent = SteamRecommendationAgent()
    
    try:
        # 从配置获取max_output_results
        max_output_results = config.get('steam.max_output_results', 20)
        result = agent.recommend_games(user_query, max_output_results=max_output_results)
        
        if not result['recommendations']:
            print(f"\n❌ {result.get('message', '没有找到符合条件的游戏')}")
            return
        
        # 打印摘要
        print_recommendation_summary(result['recommendations'])
        
        # 询问是否查看详情
        if config.get('recommendation.show_detail_prompt', True):
            print("\n📋 是否查看详细推荐信息？[y/n]", end=" ")
            try:
                show_detail = input().strip().lower()
            except:
                show_detail = 'n'
            
            if show_detail == 'y':
                for i, rec in enumerate(result['recommendations'], 1):
                    print_detailed_recommendation(rec, i)
        
        # 保存结果
        if config.get('recommendation.save_json', True):
            output_file = config.get('recommendation.output_file', 'recommendations.json')
            agent.save_to_file(result, output_file)
        
        print(f"\n✅ 推荐完成！共找到 {len(result['recommendations'])} 款游戏")
        logger.info(f"推荐任务成功完成")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        logger.warning("用户中断操作")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        logger.error(f"推荐任务失败: {e}")
        import traceback
        traceback.print_exc()
        logger.error(traceback.format_exc())


def quick_recommend(query: str, max_results: int = 5, show_detail: bool = False):
    """快速推荐接口（用于其他程序调用）"""
    agent = SteamRecommendationAgent()
    result = agent.recommend_games(query, max_results=max_results)
    
    if show_detail:
        for i, rec in enumerate(result['recommendations'], 1):
            print_detailed_recommendation(rec, i)
    
    return result


if __name__ == "__main__":
    main()
