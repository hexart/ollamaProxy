#!/usr/bin/env python3
"""
配置管理模块
"""

import json
import os
from typing import Dict, Any

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.default_config = {
            "port": 8000,
            "ollama_base_url": "http://localhost:11434",
            "timeout": 60.0,
            "auto_start": False,
            "enable_logging": True
        }
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置和加载的配置
                    merged_config = self.default_config.copy()
                    merged_config.update(config)
                    return merged_config
            except Exception as e:
                print(f"加载配置文件时出错: {e}")
                return self.default_config.copy()
        else:
            # 配置文件不存在，创建默认配置
            self.save_config(self.default_config)
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any] = None) -> bool:
        """保存配置"""
        if config is None:
            config = self.config
            
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置文件时出错: {e}")
            return False
    
    def get(self, key: str, default=None):
        """获取配置项"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """设置配置项"""
        self.config[key] = value
        return self.save_config()
    
    def update(self, updates: Dict[str, Any]) -> bool:
        """批量更新配置"""
        self.config.update(updates)
        return self.save_config()
    
    def reset_to_default(self) -> bool:
        """重置为默认配置"""
        self.config = self.default_config.copy()
        return self.save_config()

# 全局配置管理器实例
config_manager = ConfigManager()
