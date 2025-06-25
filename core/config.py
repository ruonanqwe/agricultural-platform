#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List

class Config:
    """配置管理类"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "app": {
                "name": "农产品市场价格管理平台",
                "version": "2.0.0",
                "debug": False
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "workers": 1
            },
            "data": {
                "csv_dir": "data",
                "backup_dir": "backups",
                "max_records": 100000,
                "cleanup_days": 30
            },
            "crawler": {
                "enabled": True,
                "interval_minutes": 30,
                "timeout_seconds": 30,
                "retry_times": 3,
                "concurrent_requests": 5,
                "provinces": [
                    {"name": "北京", "code": "110000"},
                    {"name": "天津", "code": "120000"},
                    {"name": "河北", "code": "130000"},
                    {"name": "山西", "code": "140000"},
                    {"name": "内蒙古", "code": "150000"},
                    {"name": "辽宁", "code": "210000"},
                    {"name": "吉林", "code": "220000"},
                    {"name": "黑龙江", "code": "230000"},
                    {"name": "上海", "code": "310000"},
                    {"name": "江苏", "code": "320000"},
                    {"name": "浙江", "code": "330000"},
                    {"name": "安徽", "code": "340000"},
                    {"name": "福建", "code": "350000"},
                    {"name": "江西", "code": "360000"},
                    {"name": "山东", "code": "370000"},
                    {"name": "河南", "code": "410000"},
                    {"name": "湖北", "code": "420000"},
                    {"name": "湖南", "code": "430000"},
                    {"name": "广东", "code": "440000"},
                    {"name": "广西", "code": "450000"},
                    {"name": "海南", "code": "460000"},
                    {"name": "重庆", "code": "500000"},
                    {"name": "四川", "code": "510000"},
                    {"name": "贵州", "code": "520000"},
                    {"name": "云南", "code": "530000"},
                    {"name": "西藏", "code": "540000"},
                    {"name": "陕西", "code": "610000"},
                    {"name": "甘肃", "code": "620000"},
                    {"name": "青海", "code": "630000"},
                    {"name": "宁夏", "code": "640000"},
                    {"name": "新疆", "code": "650000"}
                ]
            },
            "report_crawler": {
                "enabled": True,
                "full_crawl": True,  # 是否进行完整爬取（所有页面）
                "max_reports_per_type": 1000,  # 每种类型最大爬取数量
                "interval_hours": 6,  # 爬取间隔（小时）
                "timeout_seconds": 30,
                "retry_times": 3,
                "page_delay_seconds": 2  # 页面间延迟
            },
            "api": {
                "base_url": "https://pfsc.agri.cn/pfsc/api",
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
                }
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 合并配置
                    self._merge_config(default_config, user_config)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
        
        return default_config
    
    def _merge_config(self, default: Dict, user: Dict):
        """递归合并配置"""
        for key, value in user.items():
            if key in default:
                if isinstance(default[key], dict) and isinstance(value, dict):
                    self._merge_config(default[key], value)
                else:
                    default[key] = value
            else:
                default[key] = value
    
    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default=None):
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_provinces(self) -> List[Dict[str, str]]:
        """获取省份列表"""
        return self.get('crawler.provinces', [])
    
    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置"""
        return self.get('api', {})
    
    def get_crawler_config(self) -> Dict[str, Any]:
        """获取爬虫配置"""
        return self.get('crawler', {})
    
    def get_data_config(self) -> Dict[str, Any]:
        """获取数据配置"""
        return self.get('data', {})

    def get_report_crawler_config(self) -> Dict[str, Any]:
        """获取报告爬虫配置"""
        return self.get('report_crawler', {})

# 全局配置实例
config = Config()
