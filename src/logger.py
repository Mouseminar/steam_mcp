"""
日志模块
提供统一的日志记录功能
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from config_loader import config


class Logger:
    """日志管理器"""
    
    _instance = None
    _logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is None:
            self._setup_logger()
    
    def _setup_logger(self):
        """配置日志系统"""
        # 创建logger
        self._logger = logging.getLogger('SteamAgent')
        
        # 从配置读取日志级别
        log_level = config.get('logging.level', 'INFO')
        self._logger.setLevel(getattr(logging, log_level))
        
        # 清除已有的handlers
        self._logger.handlers.clear()
        
        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 文件handler
        if config.get('logging.enabled', True):
            log_file = config.get('logging.file', 'logs/steam_agent.log')
            
            # 确保日志目录存在
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # 使用RotatingFileHandler支持日志轮转
            max_bytes = config.get('logging.max_file_size_mb', 10) * 1024 * 1024
            backup_count = config.get('logging.backup_count', 5)
            
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)
        
        # 控制台handler
        if config.get('logging.console_output', True):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)
    
    def info(self, message: str):
        """记录INFO级别日志"""
        self._logger.info(message)
    
    def debug(self, message: str):
        """记录DEBUG级别日志"""
        self._logger.debug(message)
    
    def warning(self, message: str):
        """记录WARNING级别日志"""
        self._logger.warning(message)
    
    def error(self, message: str):
        """记录ERROR级别日志"""
        self._logger.error(message)
    
    def critical(self, message: str):
        """记录CRITICAL级别日志"""
        self._logger.critical(message)
    
    def log_search_start(self, query: str):
        """记录搜索开始"""
        self.info(f"开始搜索: {query}")
    
    def log_search_game(self, game_name: str, index: int, total: int):
        """记录正在处理的游戏"""
        self.info(f"[{index}/{total}] 正在处理: {game_name}")
    
    def log_search_complete(self, count: int):
        """记录搜索完成"""
        self.info(f"搜索完成，找到 {count} 款游戏")
    
    def log_recommendation_start(self, query: str):
        """记录推荐开始"""
        self.info(f"="*60)
        self.info(f"推荐任务开始")
        self.info(f"用户查询: {query}")
        self.info(f"="*60)
    
    def log_recommendation_complete(self, count: int):
        """记录推荐完成"""
        self.info(f"="*60)
        self.info(f"推荐任务完成，共推荐 {count} 款游戏")
        self.info(f"="*60)
    
    def log_error_with_context(self, error: Exception, context: str):
        """记录带上下文的错误"""
        self.error(f"{context}: {type(error).__name__} - {str(error)}")


# 全局日志实例
logger = Logger()


if __name__ == "__main__":
    # 测试日志系统
    logger.info("这是一条INFO日志")
    logger.debug("这是一条DEBUG日志")
    logger.warning("这是一条WARNING日志")
    logger.error("这是一条ERROR日志")
    
    logger.log_recommendation_start("测试查询")
    logger.log_search_game("测试游戏", 1, 10)
    logger.log_recommendation_complete(10)
