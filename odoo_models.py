# -*- coding: utf-8 -*-
"""
农产品市场价格Odoo模型文件
Agricultural Market Price Odoo Models
"""

# models/market_price.py
MARKET_PRICE_MODEL = '''# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta

class MarketPrice(models.Model):
    _name = 'agricultural.market.price'
    _description = '农产品市场价格'
    _order = 'date desc, id desc'
    _rec_name = 'product_name'

    # 基本信息
    product_name = fields.Char('产品名称', required=True, index=True)
    product_id = fields.Many2one('product.product', '关联产品', ondelete='cascade')
    category = fields.Selection([
        ('vegetable', '蔬菜类'),
        ('fruit', '水果类'),
        ('meat', '肉类'),
        ('aquatic', '水产类'),
        ('grain', '粮食类'),
        ('other', '其他')
    ], string='产品分类', required=True, default='other')
    
    # 价格信息
    price = fields.Float('价格(元/公斤)', digits=(10, 2), required=True)
    unit = fields.Char('单位', default='公斤')
    currency_id = fields.Many2one('res.currency', '货币', default=lambda self: self.env.company.currency_id)
    
    # 时间和地点
    date = fields.Date('价格日期', required=True, default=fields.Date.today)
    market_location = fields.Char('市场地点', default='全国平均')
    source = fields.Char('数据来源', default='市场调研')
    
    # 价格变化
    price_change = fields.Float('价格变化', compute='_compute_price_change', store=True)
    price_change_percent = fields.Float('变化百分比(%)', compute='_compute_price_change', store=True)
    
    # 状态
    active = fields.Boolean('有效', default=True)
    state = fields.Selection([
        ('draft', '草稿'),
        ('confirmed', '已确认'),
        ('archived', '已归档')
    ], string='状态', default='draft')
    
    # 统计字段
    avg_price_7d = fields.Float('7天平均价格', compute='_compute_avg_prices', store=True)
    avg_price_30d = fields.Float('30天平均价格', compute='_compute_avg_prices', store=True)
    
    @api.depends('product_name', 'date', 'price')
    def _compute_price_change(self):
        for record in self:
            # 查找前一天的价格记录
            previous_record = self.search([
                ('product_name', '=', record.product_name),
                ('date', '<', record.date),
                ('active', '=', True)
            ], limit=1, order='date desc')
            
            if previous_record:
                record.price_change = record.price - previous_record.price
                if previous_record.price > 0:
                    record.price_change_percent = (record.price_change / previous_record.price) * 100
                else:
                    record.price_change_percent = 0
            else:
                record.price_change = 0
                record.price_change_percent = 0
    
    @api.depends('product_name', 'date', 'price')
    def _compute_avg_prices(self):
        for record in self:
            # 计算7天平均价格
            date_7d_ago = record.date - timedelta(days=7)
            records_7d = self.search([
                ('product_name', '=', record.product_name),
                ('date', '>=', date_7d_ago),
                ('date', '<=', record.date),
                ('active', '=', True)
            ])
            record.avg_price_7d = sum(records_7d.mapped('price')) / len(records_7d) if records_7d else record.price
            
            # 计算30天平均价格
            date_30d_ago = record.date - timedelta(days=30)
            records_30d = self.search([
                ('product_name', '=', record.product_name),
                ('date', '>=', date_30d_ago),
                ('date', '<=', record.date),
                ('active', '=', True)
            ])
            record.avg_price_30d = sum(records_30d.mapped('price')) / len(records_30d) if records_30d else record.price
    
    def action_confirm(self):
        self.write({'state': 'confirmed'})
    
    def action_archive(self):
        self.write({'state': 'archived', 'active': False})
    
    @api.model
    def get_price_trend_data(self, product_name=None, days=30):
        """获取价格趋势数据"""
        domain = [('active', '=', True)]
        if product_name:
            domain.append(('product_name', '=', product_name))
        
        date_from = fields.Date.today() - timedelta(days=days)
        domain.append(('date', '>=', date_from))
        
        records = self.search(domain, order='date asc')
        
        trend_data = []
        for record in records:
            trend_data.append({
                'date': record.date.strftime('%Y-%m-%d'),
                'product_name': record.product_name,
                'price': record.price,
                'category': record.category
            })
        
        return trend_data
'''

# models/product_category.py  
PRODUCT_CATEGORY_MODEL = '''# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProductCategoryExtended(models.Model):
    _inherit = 'product.category'
    
    # 农产品特有字段
    is_agricultural = fields.Boolean('农产品分类', default=False)
    seasonal = fields.Boolean('季节性产品', default=False)
    storage_days = fields.Integer('保存天数', default=7)
    origin_region = fields.Char('主要产地')
    
    # 价格统计
    avg_price = fields.Float('平均价格', compute='_compute_price_stats', store=True)
    price_volatility = fields.Float('价格波动率(%)', compute='_compute_price_stats', store=True)
    
    @api.depends('product_ids.list_price')
    def _compute_price_stats(self):
        for category in self:
            products = category.product_ids.filtered('active')
            if products:
                prices = products.mapped('list_price')
                category.avg_price = sum(prices) / len(prices)
                
                # 计算价格波动率
                if len(prices) > 1:
                    import statistics
                    category.price_volatility = (statistics.stdev(prices) / category.avg_price) * 100 if category.avg_price > 0 else 0
                else:
                    category.price_volatility = 0
            else:
                category.avg_price = 0
                category.price_volatility = 0
'''

# views/market_price_views.xml
MARKET_PRICE_VIEWS = '''<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- 市场价格列表视图 -->
    <record id="view_market_price_tree" model="ir.ui.view">
        <field name="name">agricultural.market.price.tree</field>
        <field name="model">agricultural.market.price</field>
        <field name="arch" type="xml">
            <tree string="市场价格" decoration-success="price_change &gt; 0" decoration-danger="price_change &lt; 0">
                <field name="date"/>
                <field name="product_name"/>
                <field name="category"/>
                <field name="price"/>
                <field name="unit"/>
                <field name="price_change"/>
                <field name="price_change_percent"/>
                <field name="market_location"/>
                <field name="state"/>
            </tree>
        </field>
    </record>

    <!-- 市场价格表单视图 -->
    <record id="view_market_price_form" model="ir.ui.view">
        <field name="name">agricultural.market.price.form</field>
        <field name="model">agricultural.market.price</field>
        <field name="arch" type="xml">
            <form string="市场价格">
                <header>
                    <button name="action_confirm" string="确认" type="object" class="oe_highlight" states="draft"/>
                    <button name="action_archive" string="归档" type="object" states="confirmed"/>
                    <field name="state" widget="statusbar" statusbar_visible="draft,confirmed,archived"/>
                </header>
                <sheet>
                    <group>
                        <group>
                            <field name="product_name"/>
                            <field name="category"/>
                            <field name="price"/>
                            <field name="unit"/>
                        </group>
                        <group>
                            <field name="date"/>
                            <field name="market_location"/>
                            <field name="source"/>
                            <field name="active"/>
                        </group>
                    </group>
                    <group string="价格变化">
                        <group>
                            <field name="price_change"/>
                            <field name="price_change_percent"/>
                        </group>
                        <group>
                            <field name="avg_price_7d"/>
                            <field name="avg_price_30d"/>
                        </group>
                    </group>
                </sheet>
            </form>
        </field>
    </record>

    <!-- 搜索视图 -->
    <record id="view_market_price_search" model="ir.ui.view">
        <field name="name">agricultural.market.price.search</field>
        <field name="model">agricultural.market.price</field>
        <field name="arch" type="xml">
            <search string="搜索市场价格">
                <field name="product_name"/>
                <field name="category"/>
                <field name="market_location"/>
                <filter string="今天" name="today" domain="[('date', '=', context_today().strftime('%Y-%m-%d'))]"/>
                <filter string="本周" name="this_week" domain="[('date', '&gt;=', (context_today() - datetime.timedelta(days=7)).strftime('%Y-%m-%d'))]"/>
                <filter string="本月" name="this_month" domain="[('date', '&gt;=', (context_today().replace(day=1)).strftime('%Y-%m-%d'))]"/>
                <separator/>
                <filter string="价格上涨" name="price_up" domain="[('price_change', '&gt;', 0)]"/>
                <filter string="价格下跌" name="price_down" domain="[('price_change', '&lt;', 0)]"/>
                <group expand="0" string="分组">
                    <filter string="产品分类" name="group_category" context="{'group_by': 'category'}"/>
                    <filter string="日期" name="group_date" context="{'group_by': 'date'}"/>
                    <filter string="市场地点" name="group_location" context="{'group_by': 'market_location'}"/>
                </group>
            </search>
        </field>
    </record>

    <!-- 动作定义 -->
    <record id="action_market_price" model="ir.actions.act_window">
        <field name="name">市场价格</field>
        <field name="res_model">agricultural.market.price</field>
        <field name="view_mode">tree,form</field>
        <field name="search_view_id" ref="view_market_price_search"/>
        <field name="help" type="html">
            <p class="o_view_nocontent_smiling_face">
                创建第一个市场价格记录
            </p>
            <p>
                在这里管理农产品的市场价格信息，跟踪价格变化趋势。
            </p>
        </field>
    </record>
</odoo>
'''

def create_odoo_module_files():
    """创建Odoo模块文件"""
    import os
    
    # 创建目录结构
    base_dir = "odoo-agricultural/addons/agricultural_market"
    os.makedirs(f"{base_dir}/models", exist_ok=True)
    os.makedirs(f"{base_dir}/views", exist_ok=True)
    os.makedirs(f"{base_dir}/data", exist_ok=True)
    os.makedirs(f"{base_dir}/security", exist_ok=True)
    
    # 写入模型文件
    with open(f"{base_dir}/models/market_price.py", 'w', encoding='utf-8') as f:
        f.write(MARKET_PRICE_MODEL)
    
    with open(f"{base_dir}/models/product_category.py", 'w', encoding='utf-8') as f:
        f.write(PRODUCT_CATEGORY_MODEL)
    
    # 写入视图文件
    with open(f"{base_dir}/views/market_price_views.xml", 'w', encoding='utf-8') as f:
        f.write(MARKET_PRICE_VIEWS)
    
    print("Odoo模块文件创建完成！")

if __name__ == "__main__":
    create_odoo_module_files()
