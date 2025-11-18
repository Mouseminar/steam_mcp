"""
Steam游戏推荐Agent核心模块
整合需求分析、Steam爬虫和LLM，提供智能游戏推荐
"""
import json
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from requirement_analyzer import RequirementAnalyzer
from steam_crawler import SteamCrawler
from llm_util import llm_gen
from config_loader import config
from logger import logger


class SteamRecommendationAgent:
    """Steam游戏推荐Agent"""
    
    def __init__(self, model: str = None):
        if model is None:
            model = config.get('llm.model', 'qwen-plus')
        self.model = model
        self.analyzer = RequirementAnalyzer(model=model)
        self.crawler = SteamCrawler()
        
        logger.info(f"推荐Agent初始化完成 (LLM模型={self.model})")
        
    def recommend_games(self, user_query: str, max_output_results: int = None) -> Dict:
        """
        根据用户查询推荐游戏
        
        Args:
            user_query: 用户查询文本
            max_output_results: 最大输出结果数（None则使用配置文件的值）
            
        Returns:
            包含推荐游戏列表的字典
        """
        if max_output_results is None:
            max_output_results = config.get('steam.max_output_results', 20)
        
        max_search_results = config.get('steam.max_search_results', 30)
        
        logger.log_recommendation_start(user_query)
        print(f"📝 分析用户需求: {user_query}")
        
        # 1. 分析用户需求
        analysis = self.analyzer.analyze_user_query(user_query)
        logger.info(f"需求分析完成: 关键词={analysis['keywords']}, 价格={analysis['max_price']}")
        print(f"✓ 需求分析完成")
        print(f"  - 关键词: {', '.join(analysis['keywords'])}")
        print(f"  - 价格范围: ¥{analysis['min_price']}-¥{analysis['max_price']}")
        print(f"  - 标签: {', '.join(analysis['tags'])}")
        
        # 2. 生成搜索查询
        search_query = self.analyzer.generate_search_query(analysis)
        logger.info(f"Steam搜索查询: {search_query}")
        print(f"\n🔍 搜索Steam: {search_query}")
        
        # 3. 搜索游戏
        games = self.crawler.search_games(
            keywords=search_query,
            max_price=analysis['max_price'],
            max_results=max_search_results
        )
        
        print(f"✓ 找到 {len(games)} 款游戏")
        logger.info(f"搜索到 {len(games)} 款游戏")
        
        if not games:
            logger.warning("未找到符合条件的游戏")
            return {
                'query': user_query,
                'analysis': analysis,
                'recommendations': [],
                'message': '抱歉，没有找到符合条件的游戏。'
            }
        
        # 4. 使用多线程并行为每个游戏生成推荐理由和评分
        print(f"\n💡 生成推荐理由（并行处理共{len(games)}款游戏）...")
        logger.info(f"开始生成推荐理由，搜索到{len(games)}款游戏")
        recommendations = []
        
        # 使用线程池并行生成推荐,最多8个并发（LLM调用较慢）
        max_workers = min(8, len(games))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有LLM任务
            future_to_game = {
                executor.submit(self._generate_recommendation, game, analysis, user_query): (i, game)
                for i, game in enumerate(games, 1)
            }
            
            # 收集完成的推荐
            completed = 0
            for future in as_completed(future_to_game):
                i, game = future_to_game[future]
                completed += 1
                try:
                    recommendation = future.result()
                    recommendations.append(recommendation)
                    print(f"  ✅ [{completed}/{len(games)}] 已完成: {game['name']} (评分: {recommendation['recommendation_score']})")
                    logger.info(f"[{completed}/{len(games)}] 推荐生成完成: {game['name']} - 评分{recommendation['recommendation_score']}")
                except Exception as e:
                    logger.error(f"生成推荐失败 {game['name']}: {e}")
                    # 即使失败也添加基本推荐
                    try:
                        basic_rec = self._create_basic_recommendation(game, analysis)
                        recommendations.append(basic_rec)
                    except:
                        pass
        
        # 5. 按推荐力度排序并返回前N个
        recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
        top_recommendations = recommendations[:max_output_results]
        
        print(f"\n✓ 推荐生成完成！从{len(recommendations)}款游戏中筛选出评分最高的{len(top_recommendations)}款")
        logger.info(f"从{len(recommendations)}款游戏中返回评分最高的{len(top_recommendations)}款")
        logger.log_recommendation_complete(len(top_recommendations))
        
        return {
            'query': user_query,
            'analysis': analysis,
            'total_found': len(games),
            'total_evaluated': len(recommendations),
            'recommendations': top_recommendations
        }
    
    def _generate_recommendation(self, game: Dict, analysis: Dict, user_query: str) -> Dict:
        """
        为单个游戏生成推荐信息
        
        Args:
            game: 游戏信息
            analysis: 用户需求分析结果
            user_query: 原始用户查询
            
        Returns:
            包含推荐信息的字典
        """
        # 基础推荐信息
        recommendation = {
            'name': game['name'],
            'app_id': game['app_id'],
            'price': game['price'],
            'original_price': game['price'] / (1 - game['discount'] / 100) if game['discount'] > 0 else game['price'],
            'discount': game['discount'],
            'tags': game['tags'][:8],  # 只保留前8个标签
            'url': game['url'],
            'release_date': game.get('release_date', ''),
            'description': game.get('description', '')[:200],  # 限制长度
        }
        
        # 使用LLM生成推荐理由和评分
        try:
            llm_result = self._generate_recommendation_with_llm(game, analysis, user_query)
            recommendation['recommendation_reason'] = llm_result.get('reason', '该游戏符合您的需求。')
            recommendation['recommendation_score'] = llm_result.get('score', 50)
            recommendation['highlights'] = llm_result.get('highlights', [])
        except Exception as e:
            logger.error(f"LLM生成推荐失败: {e}")
            print(f"    LLM生成失败，使用规则评分: {e}")
            # 降级到规则评分
            recommendation['recommendation_reason'] = self._generate_simple_reason(game, analysis)
            recommendation['recommendation_score'] = self._calculate_simple_score(game, analysis)
            recommendation['highlights'] = []
        
        return recommendation
    
    def _generate_recommendation_with_llm(self, game: Dict, analysis: Dict, user_query: str) -> Dict:
        """使用LLM生成推荐理由和评分"""
        
        system_prompt = """你是一个专业的游戏推荐专家。基于用户的需求和游戏信息，你需要：
1. 评估游戏与用户需求的匹配度（0-100分）
2. 生成简洁的推荐理由（1-2句话，50字以内）
3. 提炼游戏的3个核心亮点

请以JSON格式返回，格式如下：
{
    "score": 85,
    "reason": "这是一款高质量的开放世界RPG游戏，世界观宏大，自由度极高，完美符合您的需求。",
    "highlights": ["开放世界探索", "丰富的剧情", "高自由度"]
}

评分标准：
- 90-100: 完美匹配用户需求
- 80-89: 高度匹配
- 70-79: 较好匹配
- 60-69: 一般匹配
- 60以下: 匹配度较低

只返回JSON，不要有其他文字。"""

        user_prompt = f"""用户需求：{user_query}

用户偏好：
- 价格范围：¥{analysis['min_price']}-¥{analysis['max_price']}
- 期望标签：{', '.join(analysis['tags'])}
- 偏好类型：{', '.join(analysis['genres'])}

游戏信息：
- 名称：{game['name']}
- 价格：¥{game['price']}
- 折扣：{game['discount']}%
- 标签：{', '.join(game['tags'][:10])}
- 简介：{game.get('description', '暂无')[:300]}

请评估这款游戏并生成推荐信息。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        result_json = llm_gen(messages, self.model)
        result = json.loads(result_json)
        
        if 'choices' in result and len(result['choices']) > 0:
            content = result['choices'][0]['message']['content']
            
            # 提取JSON
            if '```json' in content:
                start = content.find('```json') + 7
                end = content.find('```', start)
                content = content[start:end].strip()
            elif '```' in content:
                start = content.find('```') + 3
                end = content.find('```', start)
                content = content[start:end].strip()
            
            llm_data = json.loads(content)
            
            return {
                'score': int(llm_data.get('score', 50)),
                'reason': llm_data.get('reason', ''),
                'highlights': llm_data.get('highlights', [])
            }
        
        raise Exception("LLM返回格式错误")
    
    def _generate_simple_reason(self, game: Dict, analysis: Dict) -> str:
        """生成简单的推荐理由（降级方案）"""
        reasons = []
        
        # 价格优势
        if game['price'] <= analysis['max_price'] * 0.5:
            reasons.append("价格实惠")
        
        # 折扣
        if game['discount'] > 50:
            reasons.append(f"{game['discount']}%折扣")
        elif game['discount'] > 0:
            reasons.append("正在打折")
        
        # 标签匹配
        matching_tags = set(game['tags']) & set(analysis['tags'])
        if matching_tags:
            reasons.append(f"匹配类型：{', '.join(list(matching_tags)[:2])}")
        
        if reasons:
            return f"该游戏{', '.join(reasons)}，值得一试。"
        else:
            return "该游戏符合您的基本需求。"
    
    def _calculate_simple_score(self, game: Dict, analysis: Dict) -> int:
        """计算简单的推荐评分（降级方案）"""
        score = 50  # 基础分
        
        # 价格匹配度 (0-25分)
        max_price = analysis['max_price']
        if game['price'] <= max_price:
            price_ratio = game['price'] / max_price if max_price > 0 else 0
            # 价格越接近预算上限，分数略低
            score += int(25 * (1 - price_ratio * 0.3))
        else:
            score -= 20  # 超出预算扣分
        
        # 标签匹配度 (0-20分)
        if analysis['tags']:
            matching_tags = set(game['tags']) & set(analysis['tags'])
            match_ratio = len(matching_tags) / len(analysis['tags'])
            score += int(20 * match_ratio)
        
        # 折扣加分 (0-10分)
        score += min(10, game['discount'] // 10)
        
        # 确保分数在0-100范围内
        return max(0, min(100, score))
    
    def _create_basic_recommendation(self, game: Dict, analysis: Dict) -> Dict:
        """创建基本推荐（无LLM）"""
        return {
            'name': game['name'],
            'app_id': game['app_id'],
            'price': game['price'],
            'original_price': game['price'] / (1 - game['discount'] / 100) if game['discount'] > 0 else game['price'],
            'discount': game['discount'],
            'tags': game['tags'][:8],
            'url': game['url'],
            'release_date': game.get('release_date', ''),
            'description': game.get('description', '')[:200],
            'recommendation_reason': self._generate_simple_reason(game, analysis),
            'recommendation_score': self._calculate_simple_score(game, analysis),
            'highlights': []
        }
    
    def format_output(self, result: Dict) -> str:
        """格式化输出为JSON字符串"""
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def save_to_file(self, result: Dict, filename: str = None):
        """保存推荐结果到文件"""
        if filename is None:
            filename = config.get('recommendation.output_file', 'recommendations.json')
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"推荐结果已保存到: {filename}")
        print(f"\n💾 推荐结果已保存到: {filename}")


if __name__ == "__main__":
    # 测试代码
    agent = SteamRecommendationAgent()
    
    query = "推荐一些开放世界RPG游戏，100元以内"
    result = agent.recommend_games(query, max_results=5)
    
    print("\n" + "="*60)
    print("推荐结果：")
    print("="*60)
    print(agent.format_output(result))
