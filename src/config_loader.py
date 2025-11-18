"""
配置文件加载模块
从config.json读取系统配置
"""
import json
import os
from typing import Dict, Any


class ConfigLoader:
    """配置加载器"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self.load_config()
    
    def load_config(self, config_path: str = None):
        """加载配置文件"""
        if config_path is None:
            # 默认配置文件路径
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, 'config.json')
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except FileNotFoundError:
            print(f"配置文件未找到: {config_path}，使用默认配置")
            self._config = self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"配置文件解析错误: {e}，使用默认配置")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        print("使用默认配置")
        return {
            "llm": {
                "model": "qwen-plus",
                "enable_thinking": False
            },
            "steam": {
                "max_search_results": 50,
                "max_output_results": 20,
                "request_timeout": 10,
                "search_delay": 0.5,
                "max_price_default": 1000.0,
                "language": "schinese",
                "country_code": "CN"
            },
            "recommendation": {
                "show_detail_prompt": True,
                "save_json": True,
                "output_file": "recommendations.json"
            },
            "logging": {
                "enabled": True,
                "level": "INFO",
                "file": "logs/steam_agent.log",
                "max_file_size_mb": 10,
                "backup_count": 5,
                "console_output": True
            }
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key_path: 配置键路径，使用.分隔，如 "steam.max_results"
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_section(self, section: str) -> Dict:
        """获取整个配置节"""
        return self._config.get(section, {})
    
    def set(self, key_path: str, value: Any):
        """设置配置值（运行时）"""
        keys = key_path.split('.')
        config = self._config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def save(self, config_path: str = None):
        """保存配置到文件"""
        if config_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, 'config.json')
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)


# 全局配置实例
config = ConfigLoader()


if __name__ == "__main__":
    # 测试配置加载
    print("LLM模型:", config.get('llm.model'))
    print("最大结果数:", config.get('steam.max_results'))
    print("日志文件:", config.get('logging.file'))
    print("\nSteam配置节:")
    print(config.get_section('steam'))
