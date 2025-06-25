#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo数据库迁移脚本 - 农产品市场价格系统
Odoo Database Migration Script for Agricultural Market Price System
"""

import os
import json
import logging
import pandas as pd
import xmlrpc.client
from datetime import datetime, timedelta
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('odoo_migration.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Odoo配置信息
ODOO_CONFIG = {
    'url': 'http://localhost:8069',
    'database': 'agricultural_db',  # 数据库名称
    'username': 'admin',
    'password': 'admin123',
    'master_password': 'ZH3Y-6YB6-GAQV'  # 您的Odoo主密码
}

# 保存配置到文件
def save_config():
    """保存配置信息到文件"""
    config_file = 'odoo_config.json'
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(ODOO_CONFIG, f, ensure_ascii=False, indent=2)
    logger.info(f"配置已保存到: {config_file}")

class OdooMigrationTool:
    def __init__(self):
        self.config = ODOO_CONFIG
        self.uid = None
        self.models = None
        self.common = None
        
    def connect_odoo(self):
        """连接到Odoo服务器"""
        try:
            logger.info(f"连接Odoo服务器: {self.config['url']}")
            self.common = xmlrpc.client.ServerProxy(f"{self.config['url']}/xmlrpc/2/common")
            
            # 获取版本信息
            version = self.common.version()
            logger.info(f"Odoo版本: {version}")
            
            # 用户认证
            self.uid = self.common.authenticate(
                self.config['database'], 
                self.config['username'], 
                self.config['password'], 
                {}
            )
            
            if not self.uid:
                raise Exception("用户认证失败")
                
            logger.info(f"认证成功，用户ID: {self.uid}")
            self.models = xmlrpc.client.ServerProxy(f"{self.config['url']}/xmlrpc/2/object")
            return True
            
        except Exception as e:
            logger.error(f"连接失败: {str(e)}")
            return False
    
    def check_database_exists(self):
        """检查数据库是否存在"""
        try:
            db_list = self.common.list()
            if self.config['database'] in db_list:
                logger.info(f"数据库 '{self.config['database']}' 已存在")
                return True
            else:
                logger.warning(f"数据库 '{self.config['database']}' 不存在")
                return False
        except Exception as e:
            logger.error(f"检查数据库失败: {str(e)}")
            return False
    
    def create_database(self):
        """创建新数据库"""
        try:
            logger.info(f"创建数据库: {self.config['database']}")
            
            # 使用主密码创建数据库
            result = self.common.create_database(
                self.config['master_password'],  # 主密码
                self.config['database'],         # 数据库名
                True,                           # 演示数据
                'zh_CN',                        # 语言
                self.config['password']         # 管理员密码
            )
            
            if result:
                logger.info("数据库创建成功")
                return True
            else:
                logger.error("数据库创建失败")
                return False
                
        except Exception as e:
            logger.error(f"创建数据库失败: {str(e)}")
            return False
    
    def install_modules(self):
        """安装必要的模块"""
        required_modules = [
            'sale_management',      # 销售管理
            'purchase',            # 采购管理
            'stock',               # 库存管理
            'account',             # 会计
            'product',             # 产品管理
        ]
        
        for module in required_modules:
            try:
                # 查找模块
                module_ids = self.models.execute_kw(
                    self.config['database'], self.uid, self.config['password'],
                    'ir.module.module', 'search',
                    [[['name', '=', module]]]
                )
                
                if module_ids:
                    # 检查模块状态
                    module_info = self.models.execute_kw(
                        self.config['database'], self.uid, self.config['password'],
                        'ir.module.module', 'read',
                        [module_ids], {'fields': ['name', 'state']}
                    )
                    
                    if module_info[0]['state'] != 'installed':
                        # 安装模块
                        self.models.execute_kw(
                            self.config['database'], self.uid, self.config['password'],
                            'ir.module.module', 'button_immediate_install',
                            [module_ids]
                        )
                        logger.info(f"模块 {module} 安装成功")
                    else:
                        logger.info(f"模块 {module} 已安装")
                        
            except Exception as e:
                logger.error(f"安装模块 {module} 失败: {str(e)}")
    
    def migrate_csv_data(self, csv_file):
        """迁移CSV数据到Odoo"""
        if not os.path.exists(csv_file):
            logger.error(f"CSV文件不存在: {csv_file}")
            return False
        
        try:
            # 读取CSV数据
            df = pd.read_csv(csv_file, encoding='utf-8')
            logger.info(f"读取到 {len(df)} 条记录")
            
            # 创建产品分类
            categories = self.create_product_categories()
            
            # 迁移产品数据
            success_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                try:
                    # 数据清理和映射
                    product_data = {
                        'name': str(row.get('product_name', f'产品_{index}')),
                        'list_price': float(row.get('price', row.get('avg_price', 0))),
                        'standard_price': float(row.get('price', row.get('avg_price', 0))),
                        'categ_id': categories.get(self.map_category(row.get('category', 'other')), 1),
                        'type': 'product',
                        'sale_ok': True,
                        'purchase_ok': True,
                        'active': True
                    }
                    
                    # 检查产品是否已存在
                    existing = self.models.execute_kw(
                        self.config['database'], self.uid, self.config['password'],
                        'product.product', 'search',
                        [[['name', '=', product_data['name']]]]
                    )
                    
                    if not existing:
                        # 创建产品
                        product_id = self.models.execute_kw(
                            self.config['database'], self.uid, self.config['password'],
                            'product.product', 'create',
                            [product_data]
                        )
                        success_count += 1
                        logger.info(f"创建产品: {product_data['name']} (ID: {product_id})")
                    else:
                        logger.info(f"产品已存在，跳过: {product_data['name']}")
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"处理第 {index} 行数据失败: {str(e)}")
            
            logger.info(f"数据迁移完成 - 成功: {success_count}, 失败: {error_count}")
            return True
            
        except Exception as e:
            logger.error(f"迁移CSV数据失败: {str(e)}")
            return False
    
    def create_product_categories(self):
        """创建产品分类"""
        categories = {
            'vegetable': '蔬菜类',
            'fruit': '水果类', 
            'meat': '肉类',
            'aquatic': '水产类',
            'grain': '粮食类',
            'other': '其他'
        }
        
        created_categories = {}
        
        for code, name in categories.items():
            try:
                # 检查分类是否存在
                existing = self.models.execute_kw(
                    self.config['database'], self.uid, self.config['password'],
                    'product.category', 'search',
                    [[['name', '=', name]]]
                )
                
                if existing:
                    created_categories[code] = existing[0]
                    logger.info(f"分类已存在: {name}")
                else:
                    # 创建分类
                    cat_id = self.models.execute_kw(
                        self.config['database'], self.uid, self.config['password'],
                        'product.category', 'create',
                        [{'name': name}]
                    )
                    created_categories[code] = cat_id
                    logger.info(f"创建分类: {name} (ID: {cat_id})")
                    
            except Exception as e:
                logger.error(f"创建分类 {name} 失败: {str(e)}")
        
        return created_categories
    
    def map_category(self, category):
        """映射产品分类"""
        mapping = {
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
        return mapping.get(str(category).lower(), 'other')
    
    def export_migration_report(self):
        """导出迁移报告"""
        try:
            # 获取产品统计
            products = self.models.execute_kw(
                self.config['database'], self.uid, self.config['password'],
                'product.product', 'search_count',
                [[['active', '=', True]]]
            )
            
            # 获取分类统计
            categories = self.models.execute_kw(
                self.config['database'], self.uid, self.config['password'],
                'product.category', 'search_count',
                [[]]
            )
            
            report = {
                'migration_date': datetime.now().isoformat(),
                'database_name': self.config['database'],
                'total_products': products,
                'total_categories': categories,
                'odoo_url': self.config['url'],
                'status': 'completed'
            }
            
            with open('migration_report.json', 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info("迁移报告已生成: migration_report.json")
            return report
            
        except Exception as e:
            logger.error(f"生成迁移报告失败: {str(e)}")
            return None

def main():
    """主函数"""
    logger.info("=== 开始Odoo数据库迁移 ===")
    
    # 保存配置
    save_config()
    
    # 创建迁移工具实例
    migration_tool = OdooMigrationTool()
    
    # 检查并创建数据库
    if not migration_tool.check_database_exists():
        logger.info("数据库不存在，将创建新数据库")
        if not migration_tool.create_database():
            logger.error("数据库创建失败，退出")
            return False
    
    # 连接Odoo
    if not migration_tool.connect_odoo():
        logger.error("无法连接到Odoo，退出")
        return False
    
    # 安装必要模块
    migration_tool.install_modules()
    
    # 迁移CSV数据
    csv_files = [
        'data/backups/backup_20250625_121804.csv',
        'data/market_prices.csv'
    ]
    
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            logger.info(f"迁移文件: {csv_file}")
            migration_tool.migrate_csv_data(csv_file)
            break
    else:
        logger.warning("未找到CSV数据文件")
    
    # 生成迁移报告
    report = migration_tool.export_migration_report()
    
    logger.info("=== 迁移完成 ===")
    if report:
        logger.info(f"数据库: {report['database_name']}")
        logger.info(f"产品数量: {report['total_products']}")
        logger.info(f"分类数量: {report['total_categories']}")
        logger.info(f"访问地址: {report['odoo_url']}")
    
    return True

if __name__ == "__main__":
    main()
