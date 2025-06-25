#!/bin/bash
# 农产品市场价格系统完整迁移脚本
# Complete Migration Script for Agricultural Market Price System

echo "=== 农产品市场价格系统迁移到Odoo ERP ==="
echo "开始时间: $(date)"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "Python3未安装，请先安装Python3"
    exit 1
fi

# 安装Python依赖
echo "安装Python依赖包..."
pip3 install -r requirements_odoo.txt

# 给脚本执行权限
chmod +x odoo_setup.sh

# 运行Odoo部署脚本
echo "部署Odoo ERP系统..."
./odoo_setup.sh

# 等待Odoo服务启动
echo "等待Odoo服务完全启动..."
sleep 60

# 检查Odoo服务状态
echo "检查Odoo服务状态..."
if curl -f http://localhost:8069 > /dev/null 2>&1; then
    echo "✅ Odoo服务启动成功"
else
    echo "❌ Odoo服务启动失败，请检查日志"
    docker-compose -f odoo-agricultural/docker-compose.yml logs
    exit 1
fi

# 创建Odoo模块文件
echo "创建农产品管理模块..."
python3 odoo_models.py

# 提示用户进行手动配置
echo ""
echo "=== 下一步操作指南 ==="
echo "1. 访问 http://localhost:8069"
echo "2. 创建数据库："
echo "   - 数据库名: agricultural_db"
echo "   - 邮箱: admin@example.com"
echo "   - 密码: admin123"
echo "   - 语言: 简体中文"
echo "   - 国家: 中国"
echo ""
echo "3. 安装必要模块："
echo "   - Sales (销售)"
echo "   - Purchase (采购)"
echo "   - Inventory (库存)"
echo "   - Accounting (会计)"
echo ""
echo "4. 安装农产品管理模块："
echo "   - 进入应用商店"
echo "   - 搜索 '农产品市场价格管理'"
echo "   - 点击安装"
echo ""
echo "5. 配置完成后运行数据迁移："
echo "   python3 odoo_migration.py"
echo ""
echo "完成以上步骤后，您的农产品数据将成功迁移到Odoo ERP系统中！"
echo ""
echo "如遇问题，请查看日志文件: migration.log"
