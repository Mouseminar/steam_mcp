"""
用户需求分析模块
使用LLM分析用户的游戏推荐需求，提取关键信息
"""
import json
from typing import Dict, List, Optional
from llm_util import llm_gen
from config_loader import config
from logger import logger


class RequirementAnalyzer:
    """用户需求分析器"""
    
    def __init__(self, model: str = None):
        if model is None:
            model = config.get('llm.model', 'qwen-plus')
        self.model = model
        logger.info(f"需求分析器初始化完成 (LLM模型={self.model})")
        
    def analyze_user_query(self, user_query: str) -> Dict:
        """
        分析用户查询，提取游戏推荐需求
        
        Args:
            user_query: 用户输入的查询文本
            
        Returns:
            包含分析结果的字典，包括：
            - keywords: 搜索关键词列表
            - max_price: 最大价格
            - min_price: 最小价格
            - tags: 游戏标签/类型
            - preferences: 其他偏好信息
        """
        
        system_prompt = """你是一个专业的游戏推荐分析助手。你的任务是分析用户的游戏推荐需求，提取关键信息。

请从用户的查询中提取以下信息：
1. 游戏类型/标签（如：RPG、开放世界、射击、策略等）
2. 价格范围（提取最大价格和最小价格，单位为人民币元）
3. 其他关键偏好（如：多人游戏、单机、画质要求、剧情导向等）
4. 搜索关键词（用于Steam搜索的英文关键词）

请以JSON格式返回结果，格式如下：
{
    "keywords": ["关键词1", "关键词2"],  // 英文关键词，用于Steam搜索
    "max_price": 1000.0,  // 最大价格，数字类型，如果无则设为1000.0
    "min_price": 0.0,  // 最小价格，数字类型
    "tags": ["标签1", "标签2"],  // 游戏类型标签，中文
    "genres": ["类型1", "类型2"],  // 游戏流派，英文
    "preferences": {
        "multiplayer": false,  // 是否偏好多人游戏
        "singleplayer": true,  // 是否偏好单人游戏
        "story_rich": false,  // 是否注重剧情
        "open_world": true,  // 是否偏好开放世界
        "other": "其他偏好描述"
    }
}

只返回JSON，不要有其他文字说明。"""

        user_prompt = f"用户查询：{user_query}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            # 调用LLM
            logger.info(f"调用LLM分析需求: {user_query[:50]}...")
            result_json = llm_gen(messages, self.model)
            result = json.loads(result_json)
            
            # 提取content
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                
                # 解析JSON内容
                # 尝试从markdown代码块中提取JSON
                if '```json' in content:
                    start = content.find('```json') + 7
                    end = content.find('```', start)
                    content = content[start:end].strip()
                elif '```' in content:
                    start = content.find('```') + 3
                    end = content.find('```', start)
                    content = content[start:end].strip()
                
                analyzed_data = json.loads(content)
                
                # 验证和设置默认值
                return self._validate_analysis(analyzed_data)
            else:
                return self._get_default_analysis()
                
        except Exception as e:
            logger.error(f"需求分析出错: {e}")
            print(f"⚠️  需求分析失败，使用降级方案")
            # 返回基础解析结果
            return self._fallback_analysis(user_query)
    
    def _validate_analysis(self, data: Dict) -> Dict:
        """验证和标准化分析结果"""
        result = {
            'keywords': data.get('keywords', []),
            'max_price': float(data.get('max_price', 1000.0)),
            'min_price': float(data.get('min_price', 0.0)),
            'tags': data.get('tags', []),
            'genres': data.get('genres', []),
            'preferences': data.get('preferences', {})
        }
        
        # 确保keywords不为空
        if not result['keywords']:
            if result['genres']:
                result['keywords'] = result['genres']
            elif result['tags']:
                result['keywords'] = result['tags']
        
        return result
    
    def _get_default_analysis(self) -> Dict:
        """返回默认分析结果"""
        return {
            'keywords': [],
            'max_price': 1000.0,
            'min_price': 0.0,
            'tags': [],
            'genres': [],
            'preferences': {}
        }
    
    def _fallback_analysis(self, user_query: str) -> Dict:
        """降级分析方法，使用简单规则"""
        result = self._get_default_analysis()
        
        # 简单的关键词提取
        query_lower = user_query.lower()
        
        # 价格提取
        import re
        price_pattern = r'(\d+)\s*元'
        prices = re.findall(price_pattern, user_query)
        if prices:
            result['max_price'] = float(prices[0])
        
        # 类型识别
        type_mapping = {
            'rpg': ['RPG', 'role-playing'],
            '开放世界': ['开放世界', 'open world'],
            '射击': ['射击', 'shooter'],
            '策略': ['策略', 'strategy'],
            '动作': ['动作', 'action'],
            '冒险': ['冒险', 'adventure'],
            '模拟': ['模拟', 'simulation'],
            '角色扮演': ['角色扮演', 'role-playing'],
            '多人': ['多人游戏', 'multiplayer'],
            '单机': ['单机游戏', 'singleplayer'],
            '剧情': ['剧情向', 'story-rich'],
            '恐怖': ['恐怖', 'horror'],
            '体育': ['体育', 'sports'],
            '竞速': ['竞速', 'racing'],
            '独立': ['独立游戏', 'indie']
        }
        
        for key, values in type_mapping.items():
            if key in query_lower:
                result['tags'].extend(values)
                result['keywords'].append(values[1] if len(values) > 1 else values[0])
        
        return result
    
    def generate_search_query(self, analysis: Dict) -> str:
        """
        根据分析结果生成Steam搜索查询
        
        Args:
            analysis: 需求分析结果
            
        Returns:
            搜索查询字符串
        """
        keywords = analysis.get('keywords', [])
        genres = analysis.get('genres', [])
        
        # 优先使用genres，其次使用keywords
        search_terms = genres if genres else keywords
        
        # 组合搜索词
        query = ' '.join(search_terms[:3])  # 最多使用3个关键词
        
        return query if query else "games"


if __name__ == "__main__":
    # 测试代码
    analyzer = RequirementAnalyzer()
    
    test_queries = [
        "推荐一些开放世界RPG游戏，100元以内",
        "想玩多人在线射击游戏，预算200元",
        "找一些剧情向的单机冒险游戏"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        result = analyzer.analyze_user_query(query)
        print(f"分析结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        print(f"搜索查询: {analyzer.generate_search_query(result)}")
