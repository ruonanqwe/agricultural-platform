#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据管理器 - 负责CSV数据的存储、查询和管理
"""

import os
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataManager:
    """数据管理器 - 专注于CSV文件操作"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.csv_file = self.data_dir / "market_prices.csv"
        self.backup_dir = self.data_dir / "backups"
        self.initialize()
    
    def initialize(self):
        """初始化数据目录和文件"""
        try:
            # 创建数据目录
            self.data_dir.mkdir(exist_ok=True)
            self.backup_dir.mkdir(exist_ok=True)
            
            # 如果CSV文件不存在，创建空文件
            if not self.csv_file.exists():
                self.create_empty_csv()
                
            logger.info(f"数据管理器初始化完成，数据目录: {self.data_dir}")
            
        except Exception as e:
            logger.error(f"数据管理器初始化失败: {e}")
            raise
    
    def create_empty_csv(self):
        """创建空的CSV文件"""
        columns = [
            '省份', '市场名称', '品种名称', '最低价', '平均价', '最高价', 
            '单位', '交易日期', '更新时间', '保存时间'
        ]
        
        df = pd.DataFrame(columns=columns)
        df.to_csv(self.csv_file, index=False, encoding='utf-8-sig')
        logger.info(f"创建空CSV文件: {self.csv_file}")
    
    def save_data(self, data_list: List[Dict]) -> int:
        """保存数据到CSV文件"""
        if not data_list:
            logger.warning("没有数据需要保存")
            return 0
        
        try:
            # 转换为DataFrame
            df = pd.DataFrame(data_list)
            
            # 添加保存时间戳
            df['保存时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 标准化列名
            df = self._standardize_columns(df)
            
            # 如果CSV文件已存在，合并数据
            if self.csv_file.exists() and self.csv_file.stat().st_size > 0:
                existing_df = pd.read_csv(self.csv_file, encoding='utf-8-sig')
                
                # 合并数据
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                
                # 去重（基于关键字段）
                if self._has_key_columns(combined_df):
                    combined_df = combined_df.drop_duplicates(
                        subset=['市场名称', '品种名称', '交易日期'], 
                        keep='last'
                    )
                
                df = combined_df
            
            # 保存到CSV
            df.to_csv(self.csv_file, index=False, encoding='utf-8-sig')
            
            logger.info(f"成功保存 {len(data_list)} 条数据，CSV文件总记录数: {len(df)}")
            
            # 创建备份
            self._create_backup()
            
            return len(data_list)
            
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            raise
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名"""
        column_mapping = {
            'province': '省份',
            'market_name': '市场名称',
            'variety_name': '品种名称',
            'min_price': '最低价',
            'avg_price': '平均价',
            'max_price': '最高价',
            'unit': '单位',
            'trade_date': '交易日期',
            'crawl_time': '更新时间'
        }
        
        # 重命名列
        df = df.rename(columns=column_mapping)
        
        # 确保必要的列存在
        required_columns = ['省份', '市场名称', '品种名称', '最低价', '平均价', '最高价', '单位', '交易日期']
        for col in required_columns:
            if col not in df.columns:
                df[col] = ''
        
        return df
    
    def _has_key_columns(self, df: pd.DataFrame) -> bool:
        """检查是否有关键列用于去重"""
        key_columns = ['市场名称', '品种名称', '交易日期']
        return all(col in df.columns for col in key_columns)
    
    def search_data(self, province: Optional[str] = None, variety: Optional[str] = None, 
                   market: Optional[str] = None, date_from: Optional[str] = None,
                   date_to: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """搜索数据"""
        try:
            if not self.csv_file.exists():
                return []
            
            df = pd.read_csv(self.csv_file, encoding='utf-8-sig')
            
            if df.empty:
                return []
            
            # 应用过滤条件
            if province:
                df = df[df['省份'].str.contains(province, na=False)]
            
            if variety:
                df = df[df['品种名称'].str.contains(variety, na=False)]
            
            if market:
                df = df[df['市场名称'].str.contains(market, na=False)]
            
            if date_from:
                df = df[df['交易日期'] >= date_from]
            
            if date_to:
                df = df[df['交易日期'] <= date_to]
            
            # 排序和限制数量
            if '交易日期' in df.columns:
                df = df.sort_values('交易日期', ascending=False)
            
            df = df.head(limit)
            
            # 清理数据并转换为字典列表
            df = df.fillna('')  # 将NaN替换为空字符串
            records = df.to_dict('records')

            # 进一步清理数据，确保JSON序列化兼容
            cleaned_records = []
            for record in records:
                cleaned_record = {}
                for key, value in record.items():
                    if pd.isna(value):
                        cleaned_record[key] = ''
                    elif isinstance(value, float) and (pd.isna(value) or value == float('inf') or value == float('-inf')):
                        cleaned_record[key] = 0
                    else:
                        cleaned_record[key] = value
                cleaned_records.append(cleaned_record)

            return cleaned_records
            
        except Exception as e:
            logger.error(f"搜索数据失败: {e}")
            return []
    
    def get_latest_data(self, limit: int = 50) -> List[Dict]:
        """获取最新数据"""
        try:
            if not self.csv_file.exists():
                return []

            df = pd.read_csv(self.csv_file, encoding='utf-8-sig')

            if df.empty:
                return []

            # 清理数据：处理NaN值
            df = df.fillna('')  # 将NaN替换为空字符串

            # 按保存时间排序
            if '保存时间' in df.columns:
                df = df.sort_values('保存时间', ascending=False)
            elif '交易日期' in df.columns:
                df = df.sort_values('交易日期', ascending=False)

            df = df.head(limit)

            # 转换为字典并清理数值
            records = df.to_dict('records')

            # 进一步清理数据，确保JSON序列化兼容
            cleaned_records = []
            for record in records:
                cleaned_record = {}
                for key, value in record.items():
                    if pd.isna(value):
                        cleaned_record[key] = ''
                    elif isinstance(value, float) and (pd.isna(value) or value == float('inf') or value == float('-inf')):
                        cleaned_record[key] = 0
                    else:
                        cleaned_record[key] = value
                cleaned_records.append(cleaned_record)

            return cleaned_records

        except Exception as e:
            logger.error(f"获取最新数据失败: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据统计信息"""
        try:
            if not self.csv_file.exists():
                return {
                    'total_records': 0,
                    'total_markets': 0,
                    'total_varieties': 0,
                    'total_provinces': 0,
                    'last_update': None
                }
            
            df = pd.read_csv(self.csv_file, encoding='utf-8-sig')
            
            if df.empty:
                return {
                    'total_records': 0,
                    'total_markets': 0,
                    'total_varieties': 0,
                    'total_provinces': 0,
                    'last_update': None
                }
            
            stats = {
                'total_records': len(df),
                'total_markets': df['市场名称'].nunique() if '市场名称' in df.columns else 0,
                'total_varieties': df['品种名称'].nunique() if '品种名称' in df.columns else 0,
                'total_provinces': df['省份'].nunique() if '省份' in df.columns else 0,
                'last_update': df['保存时间'].max() if '保存时间' in df.columns else None
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                'total_records': 0,
                'total_markets': 0,
                'total_varieties': 0,
                'total_provinces': 0,
                'last_update': None
            }
    
    def get_provinces(self) -> List[str]:
        """获取省份列表"""
        try:
            if not self.csv_file.exists():
                return []
            
            df = pd.read_csv(self.csv_file, encoding='utf-8-sig')
            
            if df.empty or '省份' not in df.columns:
                return []
            
            provinces = df['省份'].dropna().unique().tolist()
            return sorted(provinces)
            
        except Exception as e:
            logger.error(f"获取省份列表失败: {e}")
            return []
    
    def get_varieties(self) -> List[str]:
        """获取品种列表"""
        try:
            if not self.csv_file.exists():
                return []
            
            df = pd.read_csv(self.csv_file, encoding='utf-8-sig')
            
            if df.empty or '品种名称' not in df.columns:
                return []
            
            varieties = df['品种名称'].dropna().unique().tolist()
            return sorted(varieties)
            
        except Exception as e:
            logger.error(f"获取品种列表失败: {e}")
            return []
    
    def get_markets(self) -> List[str]:
        """获取市场列表"""
        try:
            if not self.csv_file.exists():
                return []
            
            df = pd.read_csv(self.csv_file, encoding='utf-8-sig')
            
            if df.empty or '市场名称' not in df.columns:
                return []
            
            markets = df['市场名称'].dropna().unique().tolist()
            return sorted(markets)
            
        except Exception as e:
            logger.error(f"获取市场列表失败: {e}")
            return []
    
    def export_csv(self, province: Optional[str] = None, variety: Optional[str] = None,
                   market: Optional[str] = None, date_from: Optional[str] = None,
                   date_to: Optional[str] = None) -> str:
        """导出CSV文件"""
        try:
            # 搜索数据
            data = self.search_data(
                province=province,
                variety=variety,
                market=market,
                date_from=date_from,
                date_to=date_to,
                limit=10000  # 导出时不限制数量
            )
            
            if not data:
                raise ValueError("没有数据可导出")
            
            # 创建导出文件
            export_file = self.data_dir / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            df = pd.DataFrame(data)
            df.to_csv(export_file, index=False, encoding='utf-8-sig')
            
            logger.info(f"数据导出成功: {export_file}")
            
            return str(export_file)
            
        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            raise
    
    def _create_backup(self):
        """创建数据备份"""
        try:
            if not self.csv_file.exists():
                return
            
            backup_file = self.backup_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            # 复制文件
            import shutil
            shutil.copy2(self.csv_file, backup_file)
            
            # 清理旧备份（保留最近10个）
            self._cleanup_old_backups()
            
        except Exception as e:
            logger.error(f"创建备份失败: {e}")
    
    def _cleanup_old_backups(self, keep_count: int = 10):
        """清理旧备份文件"""
        try:
            backup_files = list(self.backup_dir.glob("backup_*.csv"))
            
            if len(backup_files) > keep_count:
                # 按修改时间排序
                backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                # 删除多余的备份
                for backup_file in backup_files[keep_count:]:
                    backup_file.unlink()
                    logger.info(f"删除旧备份: {backup_file}")
                    
        except Exception as e:
            logger.error(f"清理备份失败: {e}")

# 全局数据管理器实例
data_manager = DataManager()

def get_data_manager():
    """获取数据管理器实例"""
    return data_manager
