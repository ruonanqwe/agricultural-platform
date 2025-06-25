#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场数据爬虫 - 负责从农业部网站爬取真实市场价格数据
基于market_crawler.py实现
"""

import requests
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import urllib3

from .config import config
from .data_manager import get_data_manager

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketCrawler:
    """市场数据爬虫 - 真实数据版本"""

    def __init__(self):
        self.config = config.get_crawler_config()
        self.data_manager = get_data_manager()

        self.is_running = False
        self.crawler_thread = None
        self.start_time = None
        self.crawled_count = 0
        self.error_count = 0

        # 真实API配置 - 基于农业部官方接口
        self.base_url = "https://pfsc.agri.cn/api"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://pfsc.agri.cn",
            "Referer": "https://pfsc.agri.cn/",
            "Connection": "keep-alive",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "Windows",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin"
        }

        self.timeout = self.config.get('timeout_seconds', 30)
        self.retry_times = self.config.get('retry_times', 3)

        # 省份列表 - 使用真实的省份代码
        self.provinces = [
            {"code": "110000", "name": "北京市"},
            {"code": "120000", "name": "天津市"},
            {"code": "130000", "name": "河北省"},
            {"code": "140000", "name": "山西省"},
            {"code": "150000", "name": "内蒙古自治区"},
            {"code": "210000", "name": "辽宁省"},
            {"code": "220000", "name": "吉林省"},
            {"code": "230000", "name": "黑龙江省"},
            {"code": "310000", "name": "上海市"},
            {"code": "320000", "name": "江苏省"},
            {"code": "330000", "name": "浙江省"},
            {"code": "340000", "name": "安徽省"},
            {"code": "350000", "name": "福建省"},
            {"code": "360000", "name": "江西省"},
            {"code": "370000", "name": "山东省"},
            {"code": "410000", "name": "河南省"},
            {"code": "420000", "name": "湖北省"},
            {"code": "430000", "name": "湖南省"},
            {"code": "440000", "name": "广东省"},
            {"code": "450000", "name": "广西壮族自治区"},
            {"code": "460000", "name": "海南省"},
            {"code": "500000", "name": "重庆市"},
            {"code": "510000", "name": "四川省"},
            {"code": "520000", "name": "贵州省"},
            {"code": "530000", "name": "云南省"},
            {"code": "540000", "name": "西藏自治区"},
            {"code": "610000", "name": "陕西省"},
            {"code": "620000", "name": "甘肃省"},
            {"code": "630000", "name": "青海省"},
            {"code": "640000", "name": "宁夏回族自治区"},
            {"code": "650000", "name": "新疆维吾尔自治区"}
        ]

        logger.info("真实市场数据爬虫初始化完成")
    
    def start_crawling(self):
        """启动爬虫"""
        if self.is_running:
            logger.warning("爬虫已在运行中")
            return
        
        logger.info("启动市场数据爬虫...")
        self.is_running = True
        self.start_time = datetime.now()
        self.crawled_count = 0
        self.error_count = 0
        
        # 启动爬虫线程
        self.crawler_thread = threading.Thread(target=self._crawl_loop, daemon=True)
        self.crawler_thread.start()
        
        logger.info("市场数据爬虫已启动")
    
    def stop_crawling(self):
        """停止爬虫"""
        if not self.is_running:
            logger.warning("爬虫未在运行")
            return
        
        logger.info("正在停止市场数据爬虫...")
        self.is_running = False
        
        if self.crawler_thread and self.crawler_thread.is_alive():
            self.crawler_thread.join(timeout=10)
        
        logger.info("市场数据爬虫已停止")
    
    def _crawl_loop(self):
        """爬虫主循环"""
        interval_minutes = self.config.get('interval_minutes', 30)
        
        while self.is_running:
            try:
                logger.info("开始新一轮数据爬取...")
                
                # 爬取所有省份的数据
                all_data = self._crawl_all_provinces()
                
                if all_data:
                    # 保存数据
                    saved_count = self.data_manager.save_data(all_data)
                    self.crawled_count += saved_count
                    
                    logger.info(f"本轮爬取完成，获取 {len(all_data)} 条数据，已保存 {saved_count} 条")
                else:
                    logger.warning("本轮爬取未获取到数据")
                
                # 等待下一轮
                if self.is_running:
                    logger.info(f"等待 {interval_minutes} 分钟后进行下一轮爬取...")
                    time.sleep(interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"爬取过程出错: {e}")
                self.error_count += 1
                
                if self.is_running:
                    time.sleep(60)  # 出错后等待1分钟再重试
    
    def _crawl_all_provinces(self) -> List[Dict]:
        """爬取所有省份的数据"""
        all_data = []

        try:
            # 爬取前5个省份的真实数据
            sample_provinces = self.provinces[:5]

            for province in sample_provinces:
                try:
                    province_data = self._crawl_province_real(province)
                    if province_data:
                        all_data.extend(province_data)
                        logger.info(f"省份 {province['name']} 爬取完成，获取 {len(province_data)} 条数据")
                    else:
                        logger.warning(f"省份 {province['name']} 未获取到数据")

                    # 避免请求过快
                    time.sleep(3)

                except Exception as e:
                    logger.error(f"省份 {province['name']} 爬取失败: {e}")
                    self.error_count += 1
                    continue

            return all_data

        except Exception as e:
            logger.error(f"批量爬取失败: {e}")
            return []
    
    def _crawl_province_real(self, province: Dict[str, str]) -> List[Dict]:
        """爬取单个省份的真实数据"""
        province_name = province['name']
        province_code = province['code']
        all_data = []

        try:
            logger.info(f"开始获取{province_name}的市场数据...")

            # 第一步：获取该省份的所有市场
            markets = self._get_province_markets(province_code)
            if not markets:
                logger.warning(f"省份 {province_name} 没有找到市场数据")
                return []

            logger.info(f"{province_name}共有 {len(markets)} 个市场")

            # 第二步：获取每个市场的详细数据
            for market in markets[:3]:  # 限制每个省份最多3个市场，避免请求过多
                market_id = market.get("marketId")
                market_name = market.get("marketName")

                if market_id and market_name:
                    try:
                        market_data = self._get_market_details(market_id, province_name, province_code)
                        if market_data:
                            all_data.extend(market_data)
                            logger.info(f"成功获取市场 {market_name} 的 {len(market_data)} 条数据")

                        # 市场间隔
                        time.sleep(2)

                    except Exception as e:
                        logger.error(f"获取市场 {market_name} 数据失败: {e}")
                        continue

            return all_data

        except Exception as e:
            logger.error(f"爬取省份 {province_name} 失败: {e}")
            return []

    def _get_province_markets(self, province_code: str) -> List[Dict]:
        """获取省份的所有市场"""
        try:
            url = f"{self.base_url}/priceQuotationController/getTodayMarketByProvinceCode"
            params = {"code": province_code}

            response = self._make_request('POST', url, params=params)
            if response and response.get("code") == 200:
                return response.get("content", [])

            return []

        except Exception as e:
            logger.error(f"获取省份 {province_code} 市场列表失败: {e}")
            return []

    def _get_market_details(self, market_id: str, province_name: str, province_code: str) -> List[Dict]:
        """获取市场的详细价格数据"""
        try:
            url = f"{self.base_url}/priceQuotationController/pageList"

            # 构建请求体
            payload = {
                "marketId": market_id,
                "pageNum": 1,
                "pageSize": 20,  # 限制每个市场的数据量
                "order": "desc",
                "key": "",
                "varietyTypeId": "",
                "varietyId": "",
                "startDate": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                "endDate": datetime.now().strftime("%Y-%m-%d")
            }

            response = self._make_request('POST', url, json=payload)
            if not response or response.get("code") != 200:
                return []

            content = response.get("content", {})
            items = content.get("list", [])

            processed_data = []
            timestamp = datetime.now()

            for item in items:
                try:
                    processed_item = {
                        # 基本信息
                        "省份": province_name,
                        "市场名称": str(item.get("marketName", "")),
                        "品种名称": str(item.get("varietyName", "")),

                        # 价格信息
                        "最低价": float(item.get("minimumPrice", 0) or 0),
                        "平均价": float(item.get("middlePrice", 0) or 0),
                        "最高价": float(item.get("highestPrice", 0) or 0),
                        "单位": str(item.get("meteringUnit", "")),

                        # 时间信息
                        "交易日期": str(item.get("reportTime", "")),
                        "更新时间": timestamp.strftime("%Y-%m-%d %H:%M:%S"),

                        # 其他信息
                        "市场ID": str(market_id),
                        "品种ID": str(item.get("varietyId", "")),
                        "产地": str(item.get("producePlace", "")),
                        "交易量": float(item.get("tradingVolume", 0) or 0),
                        "品种类型": str(item.get("varietyTypeName", ""))
                    }

                    # 验证必要字段
                    if processed_item["市场名称"] and processed_item["品种名称"]:
                        processed_data.append(processed_item)

                except Exception as e:
                    logger.error(f"处理市场数据项失败: {e}")
                    continue

            return processed_data

        except Exception as e:
            logger.error(f"获取市场 {market_id} 详细数据失败: {e}")
            return []
    
    def _make_request(self, method: str, url: str, **kwargs) -> Optional[Dict]:
        """发送HTTP请求"""
        for attempt in range(self.retry_times):
            try:
                # 设置默认参数
                request_kwargs = {
                    'headers': self.headers,
                    'timeout': self.timeout,
                    'verify': False,  # 禁用SSL验证
                    **kwargs
                }

                response = requests.request(method, url, **request_kwargs)

                # 检查响应状态
                if response.status_code != 200:
                    raise requests.exceptions.RequestException(f"HTTP {response.status_code}")

                # 检查响应内容
                if not response.content:
                    raise ValueError("Empty response received")

                return response.json()

            except requests.exceptions.RequestException as e:
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{self.retry_times}): {e}")
                if attempt < self.retry_times - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    logger.error(f"请求最终失败: {url}")
                    return None
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}")
                return None
            except Exception as e:
                logger.error(f"请求出现未知错误: {e}")
                return None
    
    def get_status(self) -> Dict[str, Any]:
        """获取爬虫状态"""
        status = {
            'status': '运行中' if self.is_running else '已停止',
            'is_running': self.is_running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'running_time': str(datetime.now() - self.start_time) if self.start_time else None,
            'crawled_count': self.crawled_count,
            'error_count': self.error_count,
            'config': self.config
        }
        
        return status
    
    def update_config(self, new_config: Dict[str, Any]):
        """更新爬虫配置"""
        try:
            # 更新配置
            for key, value in new_config.items():
                if key in self.config:
                    self.config[key] = value
            
            # 保存配置
            config.set('crawler', self.config)
            config.save_config()
            
            logger.info(f"爬虫配置已更新: {new_config}")
            
        except Exception as e:
            logger.error(f"更新爬虫配置失败: {e}")
            raise
    
    def crawl_once(self) -> List[Dict]:
        """执行一次爬取（用于测试）"""
        logger.info("执行单次数据爬取...")
        
        try:
            all_data = self._crawl_all_provinces()
            
            if all_data:
                saved_count = self.data_manager.save_data(all_data)
                logger.info(f"单次爬取完成，获取 {len(all_data)} 条数据，已保存 {saved_count} 条")
            else:
                logger.warning("单次爬取未获取到数据")
            
            return all_data
            
        except Exception as e:
            logger.error(f"单次爬取失败: {e}")
            return []

# 全局爬虫实例
crawler = MarketCrawler()

def get_crawler():
    """获取爬虫实例"""
    return crawler
