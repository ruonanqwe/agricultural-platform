#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
农产品市场价格数据迁移到Odoo ERP系统
Migration script for Agricultural Market Price data to Odoo ERP
"""

import pandas as pd
import xmlrpc.client
import json
import logging
import sys
from datetime import datetime
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class OdooMigration:
    def __init__(self, config):
        """初始化Odoo连接配置"""
        self.url = config['url']
        self.db = config['database']
        self.username = config['username']
        self.password = config['password']
        self.uid = None
        self.models = None
        self.common = None
        
    def connect(self):
        """连接到Odoo服务器"""
        try:
            logger.info(f"正在连接到Odoo服务器: {self.url}")
            self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            
            # 验证服务器版本
            version = self.common.version()
            logger.info(f"Odoo服务器版本: {version}")
            
            # 用户认证
            self.uid = self.common.authenticate(self.db, self.username, self.password, {})
            if not self.uid:
                raise Exception("认证失败，请检查用户名和密码")
            
            logger.info(f"用户认证成功，UID: {self.uid}")
            self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
            return True
            
        except Exception as e:
            logger.error(f"连接Odoo失败: {str(e)}")
            return False
    
    def create_custom_module(self):
        """创建农产品市场价格自定义模块"""
        logger.info("检查并创建自定义模块...")
        
        # 检查模块是否存在
        module_exists = self.models.execute_kw(
            self.db, self.uid, self.password,
            'ir.module.module', 'search',
            [[['name', '=', 'agricultural_market']]]
        )
        
        if not module_exists:
            logger.info("创建农产品市场价格模块...")
            # 这里需要通过文件系统创建模块，暂时跳过
            logger.warning("需要手动创建模块文件，请参考后续说明")
        
        return True
    
    def prepare_data(self, csv_file):
        """准备和清理CSV数据"""
        logger.info(f"读取CSV文件: {csv_file}")
        
        try:
            # 读取CSV文件
            df = pd.read_csv(csv_file, encoding='utf-8')
            logger.info(f"成功读取 {len(df)} 条记录")
            
            # 显示数据结构
            logger.info("数据列名:")
            for col in df.columns:
                logger.info(f"  - {col}")
            
            # 数据清理和转换
            cleaned_data = []
            for index, row in df.iterrows():
                try:
                    # 根据实际CSV结构调整字段映射
                    record = {
                        'name': str(row.get('product_name', row.get('name', f'产品_{index}'))),
                        'category': self.map_category(row.get('category', 'other')),
                        'price': float(row.get('price', row.get('avg_price', 0))),
                        'date': self.parse_date(row.get('date', row.get('report_date', datetime.now().strftime('%Y-%m-%d')))),
                        'market_location': str(row.get('market', row.get('location', '未知市场'))),
                        'unit': str(row.get('unit', '公斤')),
                        'source': str(row.get('source', '数据迁移')),
                        'active': True
                    }
                    cleaned_data.append(record)
                    
                except Exception as e:
                    logger.warning(f"处理第 {index} 行数据时出错: {str(e)}")
                    continue
            
            logger.info(f"数据清理完成，有效记录: {len(cleaned_data)}")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"读取CSV文件失败: {str(e)}")
            return []
    
    def map_category(self, category):
        """映射产品分类"""
        category_mapping = {
            'vegetables': 'vegetable',
            'fruits': 'fruit', 
            'meat': 'meat',
            'aquatic': 'aquatic',
            'grain': 'grain',
            '蔬菜': 'vegetable',
            '水果': 'fruit',
            '肉类': 'meat',
            '水产': 'aquatic',
            '粮食': 'grain'
        }
        return category_mapping.get(str(category).lower(), 'other')
    
    def parse_date(self, date_str):
        """解析日期字符串"""
        try:
            if pd.isna(date_str):
                return datetime.now().strftime('%Y-%m-%d')
            
            # 尝试多种日期格式
            date_formats = ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%d-%m-%Y']
            for fmt in date_formats:
                try:
                    return datetime.strptime(str(date_str), fmt).strftime('%Y-%m-%d')
                except:
                    continue
            
            return datetime.now().strftime('%Y-%m-%d')
            
        except:
            return datetime.now().strftime('%Y-%m-%d')
    
    def create_product_categories(self):
        """创建产品分类"""
        logger.info("创建产品分类...")
        
        categories = [
            {'name': '蔬菜类', 'code': 'vegetable'},
            {'name': '水果类', 'code': 'fruit'},
            {'name': '肉类', 'code': 'meat'},
            {'name': '水产类', 'code': 'aquatic'},
            {'name': '粮食类', 'code': 'grain'},
            {'name': '其他', 'code': 'other'}
        ]
        
        created_categories = {}
        for cat in categories:
            try:
                # 检查分类是否已存在
                existing = self.models.execute_kw(
                    self.db, self.uid, self.password,
                    'product.category', 'search',
                    [[['name', '=', cat['name']]]]
                )
                
                if existing:
                    created_categories[cat['code']] = existing[0]
                    logger.info(f"分类已存在: {cat['name']}")
                else:
                    # 创建新分类
                    cat_id = self.models.execute_kw(
                        self.db, self.uid, self.password,
                        'product.category', 'create',
                        [{'name': cat['name']}]
                    )
                    created_categories[cat['code']] = cat_id
                    logger.info(f"创建分类: {cat['name']} (ID: {cat_id})")
                    
            except Exception as e:
                logger.error(f"创建分类 {cat['name']} 失败: {str(e)}")
        
        return created_categories
    
    def migrate_products(self, data, categories):
        """迁移产品数据"""
        logger.info("开始迁移产品数据...")
        
        success_count = 0
        error_count = 0
        
        for record in data:
            try:
                # 检查产品是否已存在
                existing = self.models.execute_kw(
                    self.db, self.uid, self.password,
                    'product.product', 'search',
                    [[['name', '=', record['name']]]]
                )
                
                if existing:
                    logger.info(f"产品已存在，跳过: {record['name']}")
                    continue
                
                # 创建产品
                product_data = {
                    'name': record['name'],
                    'categ_id': categories.get(record['category'], categories.get('other')),
                    'list_price': record['price'],
                    'standard_price': record['price'],
                    'type': 'product',
                    'sale_ok': True,
                    'purchase_ok': True,
                    'active': record['active']
                }
                
                product_id = self.models.execute_kw(
                    self.db, self.uid, self.password,
                    'product.product', 'create',
                    [product_data]
                )
                
                success_count += 1
                logger.info(f"创建产品成功: {record['name']} (ID: {product_id})")
                
            except Exception as e:
                error_count += 1
                logger.error(f"创建产品失败 {record['name']}: {str(e)}")
        
        logger.info(f"产品迁移完成 - 成功: {success_count}, 失败: {error_count}")
        return success_count, error_count

def main():
    """主函数"""
    logger.info("=== 农产品市场价格数据迁移到Odoo开始 ===")
    
    # Odoo连接配置
    config = {
        'url': 'http://localhost:8069',  # 修改为您的Odoo服务器地址
        'database': 'odoo',              # 修改为您的数据库名
        'username': 'admin',             # 修改为您的用户名
        'password': 'admin'              # 修改为您的密码
    }
    
    # CSV文件路径
    csv_file = 'data/backups/backup_20250625_121804.csv'
    
    # 检查文件是否存在
    if not os.path.exists(csv_file):
        logger.error(f"CSV文件不存在: {csv_file}")
        return False
    
    # 创建迁移实例
    migration = OdooMigration(config)
    
    # 连接Odoo
    if not migration.connect():
        logger.error("无法连接到Odoo服务器")
        return False
    
    # 准备数据
    data = migration.prepare_data(csv_file)
    if not data:
        logger.error("没有有效数据可迁移")
        return False
    
    # 创建产品分类
    categories = migration.create_product_categories()
    
    # 迁移产品数据
    success, errors = migration.migrate_products(data, categories)
    
    logger.info("=== 迁移完成 ===")
    logger.info(f"总记录数: {len(data)}")
    logger.info(f"成功迁移: {success}")
    logger.info(f"失败记录: {errors}")
    
    return True

if __name__ == "__main__":
    main()
