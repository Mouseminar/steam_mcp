"""
Steam游戏信息爬虫模块
通过Steam Store API和网页爬虫获取游戏信息
"""
import requests
import time
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from config_loader import config
from logger import logger


class SteamCrawler:
    """Steam游戏信息爬虫"""
    
    def __init__(self):
        self.base_url = "https://store.steampowered.com"
        self.search_url = f"{self.base_url}/search/"
        self.api_url = f"{self.base_url}/api"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        
        # 从配置加载参数
        self.request_timeout = config.get('steam.request_timeout', 10)
        self.search_delay = config.get('steam.search_delay', 0.5)
        self.language = config.get('steam.language', 'schinese')
        self.country_code = config.get('steam.country_code', 'CN')
        
        logger.info(f"Steam爬虫初始化完成 (超时={self.request_timeout}s, 延迟={self.search_delay}s)")
        
    def search_games(self, keywords: str, max_price: Optional[float] = None, 
                     tags: Optional[List[str]] = None, max_results: int = None) -> List[Dict]:
        """
        搜索Steam游戏
        
        Args:
            keywords: 搜索关键词
            max_price: 最大价格（人民币）
            tags: 游戏标签列表
            max_results: 最大返回结果数（None则使用配置文件的值）
            
        Returns:
            游戏信息列表
        """
        if max_results is None:
            max_results = config.get('steam.max_search_results', 50)
        
        logger.log_search_start(f"关键词='{keywords}', 最大价格={max_price}, 最大结果={max_results}")
        print(f"\n🔍 正在搜索Steam游戏: '{keywords}' (最多返回 {max_results} 款)...")
        
        games = []
        
        # 构建搜索参数
        params = {
            'term': keywords,
            'l': self.language,
            'cc': self.country_code,
            'ndl': 1,
        }
        
        # 添加价格过滤
        if max_price:
            params['maxprice'] = int(max_price)
        
        try:
            response = requests.get(self.search_url, params=params, headers=self.headers, timeout=self.request_timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            game_items = soup.find_all('a', class_='search_result_row', limit=max_results * 2)
            
            logger.info(f"Steam搜索返回 {len(game_items)} 个结果")
            
            for idx, item in enumerate(game_items, 1):
                try:
                    game_info = self._parse_game_item(item)
                    if game_info:
                        # 价格过滤
                        if max_price and game_info.get('price', float('inf')) > max_price:
                            continue
                        games.append(game_info)
                        
                        # 显示进度
                        print(f"  找到: {game_info['name']} - ¥{game_info['price']}")
                        
                        # if len(games) >= max_results:
                        #     break
                except Exception as e:
                    logger.error(f"解析游戏项出错: {e}")
                    continue
            
            logger.info(f"过滤后得到 {len(games)} 款游戏")
            
            # 使用多线程并行获取详细信息
            print(f"\n🔍 获取游戏详细信息（并行处理）...")
            # games_to_enrich = games[:max_results]
            games_to_enrich = games
            
            # 使用线程池并行获取,最多max_results * 2个并发
            max_workers = min(max_results * 2, len(games_to_enrich))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_game = {
                    executor.submit(self._enrich_game_info, game): game 
                    for game in games_to_enrich
                }
                
                # 收集完成的任务
                completed = 0
                for future in as_completed(future_to_game):
                    game = future_to_game[future]
                    completed += 1
                    try:
                        future.result()  # 获取结果,如果有异常会在这里抛出
                        print(f"  [{completed}/{len(games_to_enrich)}] 已获取: {game['name']}")
                        logger.log_search_game(game['name'], completed, len(games_to_enrich))
                    except Exception as e:
                        logger.error(f"获取 {game['name']} 详情失败: {e}")
            
            logger.log_search_complete(len(games_to_enrich))
                
        except Exception as e:
            logger.error(f"搜索Steam游戏出错: {e}")
            print(f"❌ 搜索出错: {e}")
            
        return games
    
    def _parse_game_item(self, item) -> Optional[Dict]:
        """解析游戏搜索结果项"""
        try:
            # 获取AppID
            app_id = item.get('data-ds-appid')
            if not app_id:
                return None
            
            # 获取游戏名称
            title_elem = item.find('span', class_='title')
            title = title_elem.text.strip() if title_elem else "未知游戏"
            
            # 获取价格
            price = 0.0
            price_elem = item.find('div', class_='discount_final_price')
            if not price_elem:
                price_elem = item.find('div', class_='search_price')
            
            if price_elem:
                price_text = price_elem.text.strip()
                # 提取价格数字
                price_match = re.search(r'¥\s*([\d,]+\.?\d*)', price_text)
                if price_match:
                    price = float(price_match.group(1).replace(',', ''))
                elif '免费' in price_text or 'Free' in price_text:
                    price = 0.0
            
            # 获取折扣信息
            discount = 0
            discount_elem = item.find('div', class_='discount_pct')
            if discount_elem:
                discount_text = discount_elem.text.strip().replace('-', '').replace('%', '')
                try:
                    discount = int(discount_text)
                except:
                    discount = 0
            
            # 获取游戏链接
            game_url = item.get('href', '')
            
            # 获取发行日期
            release_date = ""
            release_elem = item.find('div', class_='search_released')
            if release_elem:
                release_date = release_elem.text.strip()
            
            return {
                'app_id': app_id,
                'name': title,
                'price': price,
                'discount': discount,
                'url': game_url,
                'release_date': release_date,
                'tags': [],
                'description': "",
                'reviews': ""
            }
        except Exception as e:
            print(f"解析游戏项出错: {e}")
            return None
    
    def _enrich_game_info(self, game: Dict):
        """丰富游戏详细信息"""
        try:
            app_id = game.get('app_id')
            if not app_id:
                return
            
            # 使用Steam Store API获取详细信息
            api_url = f"{self.api_url}/appdetails"
            params = {
                'appids': app_id,
                'l': self.language,
                'cc': self.country_code
            }
            
            response = requests.get(api_url, params=params, headers=self.headers, timeout=self.request_timeout)
            data = response.json()
            
            if data and app_id in data and data[app_id].get('success'):
                game_data = data[app_id]['data']
                
                # 更新游戏信息
                game['description'] = game_data.get('short_description', '')
                game['tags'] = [genre['description'] for genre in game_data.get('genres', [])]
                
                # 添加类别标签
                if game_data.get('categories'):
                    categories = [cat['description'] for cat in game_data.get('categories', [])]
                    game['tags'].extend(categories[:3])  # 只取前3个类别
                
                # 评价信息
                if game_data.get('metacritic'):
                    game['metacritic_score'] = game_data['metacritic'].get('score', 0)
                
                # 开发商和发行商
                game['developers'] = game_data.get('developers', [])
                game['publishers'] = game_data.get('publishers', [])
                
                # 支持的语言
                game['supported_languages'] = game_data.get('supported_languages', '')
                
        except Exception as e:
            logger.debug(f"丰富游戏信息出错 (AppID: {game.get('app_id')}): {e}")
    
    def get_game_details(self, app_id: str) -> Optional[Dict]:
        """获取单个游戏的详细信息"""
        try:
            api_url = f"{self.api_url}/appdetails"
            params = {
                'appids': app_id,
                'l': self.language,
                'cc': self.country_code
            }
            
            response = requests.get(api_url, params=params, headers=self.headers, timeout=self.request_timeout)
            data = response.json()
            
            if data and app_id in data and data[app_id].get('success'):
                game_data = data[app_id]['data']
                
                # 格式化返回结果
                formatted_data = {
                    'app_id': app_id,
                    'name': game_data.get('name', ''),
                    'type': game_data.get('type', ''),
                    'description': game_data.get('detailed_description', ''),
                    'short_description': game_data.get('short_description', ''),
                    'about_the_game': game_data.get('about_the_game', ''),
                    'developers': game_data.get('developers', []),
                    'publishers': game_data.get('publishers', []),
                    'release_date': game_data.get('release_date', {}).get('date', ''),
                    'price': self._parse_price_data(game_data.get('price_overview', {})),
                    'is_free': game_data.get('is_free', False),
                    'supported_languages': game_data.get('supported_languages', ''),
                    'header_image': game_data.get('header_image', ''),
                    'website': game_data.get('website', ''),
                    'platforms': game_data.get('platforms', {}),
                    'categories': [cat['description'] for cat in game_data.get('categories', [])],
                    'genres': [genre['description'] for genre in game_data.get('genres', [])],
                    'screenshots': [ss['path_thumbnail'] for ss in game_data.get('screenshots', [])[:5]],
                    'metacritic_score': game_data.get('metacritic', {}).get('score', None),
                    'recommendations': game_data.get('recommendations', {}).get('total', None),
                    'achievements': game_data.get('achievements', {}).get('total', 0),
                    'dlc': game_data.get('dlc', []),
                    'pc_requirements': game_data.get('pc_requirements', {}),
                    'legal_notice': game_data.get('legal_notice', ''),
                }
                
                return formatted_data
                
        except Exception as e:
            logger.error(f"获取游戏详情出错 (AppID: {app_id}): {e}")
            print(f"❌ 获取游戏详情出错 (AppID: {app_id}): {e}")
            
        return None
    
    def _parse_price_data(self, price_overview: Dict) -> Dict:
        """解析价格数据"""
        if not price_overview:
            return {'current': 0.0, 'original': 0.0, 'discount': 0, 'currency': 'CNY'}
        
        # Steam API返回的价格是以分为单位
        current_price = price_overview.get('final', 0) / 100.0
        original_price = price_overview.get('initial', 0) / 100.0
        discount = price_overview.get('discount_percent', 0)
        
        return {
            'current': current_price,
            'original': original_price,
            'discount': discount,
            'currency': price_overview.get('currency', 'CNY')
        }
    
    def get_game_by_name(self, game_name: str) -> Optional[Dict]:
        """根据游戏名称获取详细信息"""
        logger.info(f"根据名称搜索游戏: {game_name}")
        print(f"\n🔍 搜索游戏: {game_name}...")
        
        # 先搜索游戏获取AppID
        games = self.search_games(game_name, max_results=1)
        
        if not games:
            logger.warning(f"未找到游戏: {game_name}")
            print(f"❌ 未找到游戏: {game_name}")
            return None
        
        # 获取第一个搜索结果的详细信息
        app_id = games[0]['app_id']
        return self.get_game_details(app_id)
    
    def get_discounted_games(self, min_discount: int = 0, max_price: Optional[float] = None, 
                            max_results: int = 20) -> List[Dict]:
        """获取折扣游戏
        
        Args:
            min_discount: 最低折扣百分比 (0-100)
            max_price: 最大价格（人民币）
            max_results: 最大返回结果数
            
        Returns:
            折扣游戏列表
        """
        logger.info(f"获取折扣游戏: 最低折扣={min_discount}%, 最大价格={max_price}, 最多{max_results}款")
        print(f"\n🎁 正在获取折扣游戏 (折扣≥{min_discount}%)...")
        
        games = []
        
        try:
            # 使用Steam的特惠页面
            specials_url = f"{self.base_url}/search/"
            params = {
                'specials': 1,  # 只显示特惠商品
                'l': self.language,
                'cc': self.country_code,
                'ndl': 1,
            }
            
            if max_price:
                params['maxprice'] = int(max_price)
            
            response = requests.get(specials_url, params=params, headers=self.headers, 
                                   timeout=self.request_timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            game_items = soup.find_all('a', class_='search_result_row', limit=max_results * 3)
            
            logger.info(f"Steam折扣页返回 {len(game_items)} 个结果")
            
            for item in game_items:
                try:
                    game_info = self._parse_game_item(item)
                    if game_info:
                        # 过滤折扣和价格
                        if game_info.get('discount', 0) >= min_discount:
                            if max_price is None or game_info.get('price', float('inf')) <= max_price:
                                games.append(game_info)
                                print(f"  找到: {game_info['name']} - ¥{game_info['price']} (-{game_info['discount']}%)")
                                
                                if len(games) >= max_results:
                                    break
                except Exception as e:
                    logger.error(f"解析折扣游戏项出错: {e}")
                    continue
            
            # 按折扣力度排序
            games.sort(key=lambda x: x.get('discount', 0), reverse=True)
            
            logger.info(f"获取到 {len(games)} 款折扣游戏")
            print(f"✅ 找到 {len(games)} 款符合条件的折扣游戏")
            
        except Exception as e:
            logger.error(f"获取折扣游戏出错: {e}")
            print(f"❌ 获取折扣游戏出错: {e}")
        
        return games
    
    def get_free_games(self, max_results: int = 20, tags: Optional[List[str]] = None) -> List[Dict]:
        """获取免费游戏
        
        Args:
            max_results: 最大返回结果数
            tags: 可选的游戏标签过滤列表
            
        Returns:
            免费游戏列表
        """
        logger.info(f"获取免费游戏: 最多{max_results}款, 标签={tags}")
        print(f"\n🆓 正在获取Steam免费游戏...")
        
        games = []
        
        try:
            # 使用Steam的免费游戏页面
            search_url = f"{self.base_url}/search/"
            params = {
                'maxprice': 'free',  # 只显示免费游戏
                'l': self.language,
                'cc': self.country_code,
                'ndl': 1,
            }
            
            response = requests.get(search_url, params=params, headers=self.headers, 
                                   timeout=self.request_timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            game_items = soup.find_all('a', class_='search_result_row', limit=max_results * 3)
            
            logger.info(f"Steam免费游戏页返回 {len(game_items)} 个结果")
            
            for item in game_items:
                try:
                    game_info = self._parse_game_item(item)
                    if game_info and game_info.get('price', 0) == 0:
                        # 标签过滤（如果指定）
                        if tags:
                            game_tags_lower = [t.lower() for t in game_info.get('tags', [])]
                            if not any(tag.lower() in game_tags_lower for tag in tags):
                                continue
                        
                        games.append(game_info)
                        print(f"  找到: {game_info['name']} - 免费")
                        
                        if len(games) >= max_results:
                            break
                except Exception as e:
                    logger.error(f"解析免费游戏项出错: {e}")
                    continue
            
            logger.info(f"获取到 {len(games)} 款免费游戏")
            print(f"✅ 找到 {len(games)} 款免费游戏")
            
            # 获取详细信息（并行）
            if games:
                print(f"\n🔍 获取游戏详细信息（并行处理）...")
                max_workers = min(10, len(games))
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_game = {
                        executor.submit(self._enrich_game_info, game): game 
                        for game in games
                    }
                    
                    completed = 0
                    for future in as_completed(future_to_game):
                        game = future_to_game[future]
                        completed += 1
                        try:
                            future.result()
                            print(f"  [{completed}/{len(games)}] 已获取: {game['name']}")
                        except Exception as e:
                            logger.error(f"获取 {game['name']} 详情失败: {e}")
            
        except Exception as e:
            logger.error(f"获取免费游戏出错: {e}")
            print(f"❌ 获取免费游戏出错: {e}")
        
        return games
    
    def get_top_games(self, max_results: int = 20, filter_type: str = 'topsellers') -> List[Dict]:
        """获取Steam热门游戏排行
        
        Args:
            max_results: 最大返回结果数
            filter_type: 排行榜类型
                - 'topsellers': 畅销榜（默认）
                - 'popularnew': 热门新品
                - 'trendingweek': 本周热门
                
        Returns:
            热门游戏列表
        """
        logger.info(f"获取热门游戏: 类型={filter_type}, 最多{max_results}款")
        print(f"\n🔥 正在获取Steam热门游戏榜单 ({filter_type})...")
        
        games = []
        
        try:
            # 使用Steam的热门游戏页面
            search_url = f"{self.base_url}/search/"
            params = {
                'filter': filter_type,
                'l': self.language,
                'cc': self.country_code,
                'ndl': 1,
            }
            
            response = requests.get(search_url, params=params, headers=self.headers, 
                                   timeout=self.request_timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            game_items = soup.find_all('a', class_='search_result_row', limit=max_results * 2)
            
            logger.info(f"Steam热门榜返回 {len(game_items)} 个结果")
            
            for idx, item in enumerate(game_items, 1):
                try:
                    game_info = self._parse_game_item(item)
                    if game_info:
                        # 添加排名信息
                        game_info['rank'] = len(games) + 1
                        games.append(game_info)
                        print(f"  #{len(games)} {game_info['name']} - ¥{game_info['price']}")
                        
                        if len(games) >= max_results:
                            break
                except Exception as e:
                    logger.error(f"解析热门游戏项出错: {e}")
                    continue
            
            logger.info(f"获取到 {len(games)} 款热门游戏")
            print(f"✅ 找到 {len(games)} 款热门游戏")
            
            # 获取详细信息（并行）
            if games:
                print(f"\n🔍 获取游戏详细信息（并行处理）...")
                max_workers = min(10, len(games))
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_game = {
                        executor.submit(self._enrich_game_info, game): game 
                        for game in games
                    }
                    
                    completed = 0
                    for future in as_completed(future_to_game):
                        game = future_to_game[future]
                        completed += 1
                        try:
                            future.result()
                            print(f"  [{completed}/{len(games)}] 已获取: {game['name']}")
                        except Exception as e:
                            logger.error(f"获取 {game['name']} 详情失败: {e}")
            
        except Exception as e:
            logger.error(f"获取热门游戏出错: {e}")
            print(f"❌ 获取热门游戏出错: {e}")
        
        return games


if __name__ == "__main__":
    # 测试代码
    crawler = SteamCrawler()
    
    # 测试搜索
    print("=" * 60)
    print("测试1: 搜索游戏")
    print("=" * 60)
    games = crawler.search_games("open world rpg", max_price=100, max_results=5)
    print(f"\n找到 {len(games)} 款游戏:")
    for game in games[:3]:
        print(f"\n游戏: {game['name']}")
        print(f"价格: ¥{game['price']}")
        print(f"标签: {', '.join(game['tags'][:5])}")
    
    # 测试折扣游戏
    print("\n" + "=" * 60)
    print("测试2: 获取折扣游戏")
    print("=" * 60)
    discounted = crawler.get_discounted_games(min_discount=50, max_price=100, max_results=5)
    print(f"\n找到 {len(discounted)} 款折扣游戏:")
    for game in discounted[:3]:
        print(f"\n游戏: {game['name']}")
        print(f"价格: ¥{game['price']}")
        print(f"折扣: -{game['discount']}%")
    
    # 测试热门游戏
    print("\n" + "=" * 60)
    print("测试3: 获取热门游戏")
    print("=" * 60)
    top_games = crawler.get_top_games(max_results=10, filter_type='topsellers')
    print(f"\n找到 {len(top_games)} 款热门游戏:")
    for game in top_games[:5]:
        print(f"\n#{game['rank']} {game['name']}")
        print(f"价格: ¥{game['price']}")
        print(f"标签: {', '.join(game.get('tags', [])[:3])}")
    
    # 测试游戏详情
    if games:
        print("\n" + "=" * 60)
        print("测试4: 获取游戏详情")
        print("=" * 60)
        details = crawler.get_game_details(games[0]['app_id'])
        if details:
            print(f"\n游戏名称: {details['name']}")
            print(f"开发商: {', '.join(details.get('developers', [])[:3])}")
            print(f"发行商: {', '.join(details.get('publishers', [])[:3])}")
            print(f"发行日期: {details.get('release_date', 'N/A')}")
            print(f"类型: {', '.join(details.get('genres', [])[:5])}")
