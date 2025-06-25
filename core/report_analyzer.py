#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告数据分析器 - 从报告中提取关键数据指标
"""

import pandas as pd
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class ReportAnalyzer:
    """报告数据分析器"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        
    def extract_key_metrics(self, reports_df: pd.DataFrame) -> Dict[str, Any]:
        """从报告数据中提取关键指标"""
        try:
            if reports_df.empty:
                return {}
            
            # 按日期排序
            reports_df = reports_df.sort_values('日报日期', ascending=True)
            
            metrics = {
                'price_index_trend': self._extract_price_index_trend(reports_df),
                'category_price_trends': self._extract_category_price_trends(reports_df),
                'key_products_trends': self._extract_key_products_trends(reports_df),
                'market_summary': self._extract_market_summary(reports_df),
                'volatility_analysis': self._extract_volatility_analysis(reports_df)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"提取关键指标失败: {e}")
            return {}
    
    def _extract_price_index_trend(self, reports_df: pd.DataFrame) -> List[Dict]:
        """提取价格指数趋势"""
        trend_data = []
        
        for _, row in reports_df.iterrows():
            try:
                date = row.get('日报日期', '')
                content = row.get('总体结论', '')
                
                # 提取农产品批发价格200指数
                price_index_match = re.search(r'"农产品批发价格200指数".*?(\d+\.?\d*)', content)
                basket_index_match = re.search(r'"菜篮子"产品批发价格指数.*?(\d+\.?\d*)', content)
                
                if price_index_match:
                    trend_data.append({
                        'date': date,
                        'price_index_200': float(price_index_match.group(1)),
                        'basket_index': float(basket_index_match.group(1)) if basket_index_match else None
                    })
                    
            except Exception as e:
                logger.warning(f"解析价格指数失败: {e}")
                continue
        
        return trend_data
    
    def _extract_category_price_trends(self, reports_df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """提取各类别价格趋势"""
        categories = {
            'vegetables': [],  # 蔬菜
            'fruits': [],      # 水果
            'meat': [],        # 畜产品
            'aquatic': []      # 水产品
        }
        
        for _, row in reports_df.iterrows():
            try:
                date = row.get('日报日期', '')
                
                # 蔬菜价格
                veg_content = row.get('蔬菜结论', '')
                veg_price_match = re.search(r'(\d+\.?\d*)元/公斤', veg_content)
                veg_change_match = re.search(r'比.*?([上下]升|下降)(\d+\.?\d*)%', veg_content)
                
                if veg_price_match:
                    change_rate = 0
                    if veg_change_match:
                        direction = veg_change_match.group(1)
                        rate = float(veg_change_match.group(2))
                        change_rate = rate if '上升' in direction else -rate
                    
                    categories['vegetables'].append({
                        'date': date,
                        'avg_price': float(veg_price_match.group(1)),
                        'change_rate': change_rate
                    })
                
                # 水果价格
                fruit_content = row.get('水果结论', '')
                fruit_price_match = re.search(r'(\d+\.?\d*)元/公斤', fruit_content)
                fruit_change_match = re.search(r'比.*?([上下]升|下降)(\d+\.?\d*)%', fruit_content)
                
                if fruit_price_match:
                    change_rate = 0
                    if fruit_change_match:
                        direction = fruit_change_match.group(1)
                        rate = float(fruit_change_match.group(2))
                        change_rate = rate if '上升' in direction else -rate
                    
                    categories['fruits'].append({
                        'date': date,
                        'avg_price': float(fruit_price_match.group(1)),
                        'change_rate': change_rate
                    })
                
                # 畜产品价格 - 提取猪肉价格作为代表
                meat_content = row.get('畜产品结论', '')
                pork_price_match = re.search(r'猪肉.*?(\d+\.?\d*)元/公斤', meat_content)
                pork_change_match = re.search(r'猪肉.*?比.*?([上下]升|下降)(\d+\.?\d*)%', meat_content)
                
                if pork_price_match:
                    change_rate = 0
                    if pork_change_match:
                        direction = pork_change_match.group(1)
                        rate = float(pork_change_match.group(2))
                        change_rate = rate if '上升' in direction else -rate
                    
                    categories['meat'].append({
                        'date': date,
                        'avg_price': float(pork_price_match.group(1)),
                        'change_rate': change_rate,
                        'product': '猪肉'
                    })
                
            except Exception as e:
                logger.warning(f"解析类别价格趋势失败: {e}")
                continue
        
        return categories
    
    def _extract_key_products_trends(self, reports_df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """提取重点产品价格趋势"""
        products = {}
        
        for _, row in reports_df.iterrows():
            try:
                date = row.get('日报日期', '')
                
                # 从畜产品结论中提取各种肉类价格
                meat_content = row.get('畜产品结论', '')
                
                # 猪肉
                pork_match = re.search(r'猪肉.*?(\d+\.?\d*)元/公斤', meat_content)
                if pork_match:
                    if '猪肉' not in products:
                        products['猪肉'] = []
                    products['猪肉'].append({
                        'date': date,
                        'price': float(pork_match.group(1)),
                        'unit': '元/公斤'
                    })
                
                # 牛肉
                beef_match = re.search(r'牛肉.*?(\d+\.?\d*)元/公斤', meat_content)
                if beef_match:
                    if '牛肉' not in products:
                        products['牛肉'] = []
                    products['牛肉'].append({
                        'date': date,
                        'price': float(beef_match.group(1)),
                        'unit': '元/公斤'
                    })
                
                # 鸡蛋
                egg_match = re.search(r'鸡蛋.*?(\d+\.?\d*)元/公斤', meat_content)
                if egg_match:
                    if '鸡蛋' not in products:
                        products['鸡蛋'] = []
                    products['鸡蛋'].append({
                        'date': date,
                        'price': float(egg_match.group(1)),
                        'unit': '元/公斤'
                    })
                
            except Exception as e:
                logger.warning(f"解析重点产品趋势失败: {e}")
                continue
        
        return products
    
    def _extract_market_summary(self, reports_df: pd.DataFrame) -> Dict[str, Any]:
        """提取市场总结信息"""
        try:
            latest_report = reports_df.iloc[-1] if not reports_df.empty else None
            if not latest_report:
                return {}
            
            summary = {
                'latest_date': latest_report.get('日报日期', ''),
                'total_reports': len(reports_df),
                'date_range': {
                    'start': reports_df['日报日期'].min() if '日报日期' in reports_df.columns else '',
                    'end': reports_df['日报日期'].max() if '日报日期' in reports_df.columns else ''
                },
                'latest_conclusions': {
                    'overall': latest_report.get('总体结论', ''),
                    'vegetables': latest_report.get('蔬菜结论', ''),
                    'fruits': latest_report.get('水果结论', ''),
                    'meat': latest_report.get('畜产品结论', ''),
                    'aquatic': latest_report.get('水产品结论', '')
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"提取市场总结失败: {e}")
            return {}
    
    def _extract_volatility_analysis(self, reports_df: pd.DataFrame) -> Dict[str, Any]:
        """提取价格波动分析"""
        try:
            volatility_data = {
                'top_gainers': [],
                'top_losers': [],
                'volatility_summary': {}
            }
            
            for _, row in reports_df.iterrows():
                try:
                    date = row.get('日报日期', '')
                    analysis_content = row.get('涨跌幅分析', '')
                    
                    # 提取涨幅前五名
                    gainers_match = re.search(r'价格升幅前五名的是(.+?)，幅度分别为(.+?)；', analysis_content)
                    if gainers_match:
                        products = gainers_match.group(1).split('、')
                        rates = re.findall(r'(\d+\.?\d*)%', gainers_match.group(2))
                        
                        for i, product in enumerate(products):
                            if i < len(rates):
                                volatility_data['top_gainers'].append({
                                    'date': date,
                                    'product': product,
                                    'change_rate': float(rates[i])
                                })
                    
                    # 提取跌幅前五名
                    losers_match = re.search(r'价格降幅前五名的是(.+?)，幅度分别为(.+?)。', analysis_content)
                    if losers_match:
                        products = losers_match.group(1).split('、')
                        rates = re.findall(r'(\d+\.?\d*)%', losers_match.group(2))
                        
                        for i, product in enumerate(products):
                            if i < len(rates):
                                volatility_data['top_losers'].append({
                                    'date': date,
                                    'product': product,
                                    'change_rate': -float(rates[i])  # 负值表示下跌
                                })
                
                except Exception as e:
                    logger.warning(f"解析波动分析失败: {e}")
                    continue
            
            return volatility_data
            
        except Exception as e:
            logger.error(f"提取波动分析失败: {e}")
            return {}
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表盘数据"""
        try:
            # 读取报告数据
            reports_file = self.data_manager.data_dir / "analysis_reports.csv"
            if not reports_file.exists():
                return {"error": "报告数据文件不存在"}
            
            reports_df = pd.read_csv(reports_file, encoding='utf-8-sig')
            
            # 只处理日报数据
            daily_reports = reports_df[reports_df['报告类型代码'] == 'daily_price_report'].copy()
            
            if daily_reports.empty:
                return {"error": "没有找到日报数据"}
            
            # 提取关键指标
            metrics = self.extract_key_metrics(daily_reports)
            
            return {
                "success": True,
                "data": metrics,
                "summary": {
                    "total_reports": len(daily_reports),
                    "date_range": {
                        "start": daily_reports['日报日期'].min() if '日报日期' in daily_reports.columns else '',
                        "end": daily_reports['日报日期'].max() if '日报日期' in daily_reports.columns else ''
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"获取仪表盘数据失败: {e}")
            return {"error": str(e)}
