#!/bin/bash
# Odoo ERP 部署脚本
# Agricultural Market Price System Migration to Odoo

echo "=== 农产品市场价格系统迁移到Odoo ERP ==="

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "Docker未安装，正在安装..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "Docker安装完成，请重新登录后运行此脚本"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose未安装，正在安装..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# 创建项目目录
mkdir -p odoo-agricultural
cd odoo-agricultural

# 创建docker-compose.yml文件
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: postgres
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: odoo123
    volumes:
      - odoo-db-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  odoo:
    image: odoo:16.0
    depends_on:
      - db
    ports:
      - "8069:8069"
    environment:
      HOST: db
      USER: odoo
      PASSWORD: odoo123
    volumes:
      - odoo-web-data:/var/lib/odoo
      - ./config:/etc/odoo
      - ./addons:/mnt/extra-addons
    restart: unless-stopped
    command: -- --dev=reload

volumes:
  odoo-web-data:
  odoo-db-data:
EOF

# 创建配置目录
mkdir -p config addons

# 创建Odoo配置文件
cat > config/odoo.conf << 'EOF'
[options]
addons_path = /mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons
data_dir = /var/lib/odoo
db_host = db
db_port = 5432
db_user = odoo
db_password = odoo123
admin_passwd = admin123
logfile = /var/log/odoo/odoo.log
log_level = info
EOF

# 创建农产品管理模块目录结构
mkdir -p addons/agricultural_market/{models,views,data,security,static/description}

# 创建模块清单文件
cat > addons/agricultural_market/__manifest__.py << 'EOF'
{
    'name': '农产品市场价格管理',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'summary': 'Agricultural Market Price Management System',
    'description': """
        农产品市场价格管理系统
        ========================
        
        功能包括：
        * 农产品价格数据管理
        * 市场价格趋势分析
        * 价格波动监控
        * 数据报表和仪表盘
    """,
    'author': 'Agricultural Platform Team',
    'website': 'https://your-website.com',
    'depends': ['base', 'product', 'sale', 'purchase', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/market_price_views.xml',
        'views/menu_views.xml',
        'data/product_category_data.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
EOF

# 创建模块初始化文件
cat > addons/agricultural_market/__init__.py << 'EOF'
from . import models
EOF

# 创建模型初始化文件
cat > addons/agricultural_market/models/__init__.py << 'EOF'
from . import market_price
from . import product_category
EOF

echo "正在启动Odoo服务..."
docker-compose up -d

echo "等待服务启动..."
sleep 30

echo "检查服务状态..."
docker-compose ps

echo ""
echo "=== 部署完成 ==="
echo "Odoo访问地址: http://localhost:8069"
echo "数据库名: odoo"
echo "管理员密码: admin123"
echo ""
echo "请等待约2-3分钟让服务完全启动，然后访问上述地址进行初始化设置"
echo ""
echo "下一步："
echo "1. 访问 http://localhost:8069 创建数据库"
echo "2. 安装农产品管理模块"
echo "3. 运行数据迁移脚本: python3 odoo_migration.py"
