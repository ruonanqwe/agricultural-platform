#!/bin/bash
# 华为云服务器部署脚本 - 农产品市场价格系统 + Odoo ERP
# Huawei Cloud Server Deployment Script

set -e  # 遇到错误立即退出

echo "=== 华为云服务器部署开始 ==="
echo "系统信息: $(uname -a)"
echo "当前用户: $(whoami)"
echo "当前目录: $(pwd)"
echo "开始时间: $(date)"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查系统环境
check_system() {
    log_info "检查系统环境..."
    
    # 检查Ubuntu版本
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        log_info "操作系统: $NAME $VERSION"
    fi
    
    # 检查内存
    MEMORY=$(free -h | awk '/^Mem:/ {print $2}')
    log_info "系统内存: $MEMORY"
    
    # 检查磁盘空间
    DISK=$(df -h / | awk 'NR==2 {print $4}')
    log_info "可用磁盘空间: $DISK"
}

# 更新系统包
update_system() {
    log_info "更新系统包..."
    sudo apt update -y
    sudo apt upgrade -y
    sudo apt install -y curl wget git vim unzip software-properties-common
}

# 安装Docker
install_docker() {
    log_info "安装Docker..."
    
    if command -v docker &> /dev/null; then
        log_info "Docker已安装: $(docker --version)"
        return
    fi
    
    # 安装Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    
    # 添加用户到docker组
    sudo usermod -aG docker $USER
    
    # 启动Docker服务
    sudo systemctl start docker
    sudo systemctl enable docker
    
    log_info "Docker安装完成"
}

# 安装Docker Compose
install_docker_compose() {
    log_info "安装Docker Compose..."
    
    if command -v docker-compose &> /dev/null; then
        log_info "Docker Compose已安装: $(docker-compose --version)"
        return
    fi
    
    # 下载Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    log_info "Docker Compose安装完成"
}

# 创建项目目录结构
create_project_structure() {
    log_info "创建项目目录结构..."
    
    # 创建主项目目录
    mkdir -p ~/agricultural-platform
    cd ~/agricultural-platform
    
    # 创建子目录
    mkdir -p {data,logs,config,backups,scripts}
    mkdir -p odoo/{addons,config,data}
    
    log_info "项目目录创建完成: $(pwd)"
}

# 创建Docker Compose配置
create_docker_compose() {
    log_info "创建Docker Compose配置..."
    
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # PostgreSQL数据库
  postgres:
    image: postgres:13
    container_name: agricultural_postgres
    environment:
      POSTGRES_DB: postgres
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: odoo123
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    networks:
      - agricultural_network

  # Odoo ERP系统
  odoo:
    image: odoo:16.0
    container_name: agricultural_odoo
    depends_on:
      - postgres
    environment:
      HOST: postgres
      USER: odoo
      PASSWORD: odoo123
    ports:
      - "8069:8069"
    volumes:
      - odoo_data:/var/lib/odoo
      - ./odoo/addons:/mnt/extra-addons
      - ./odoo/config:/etc/odoo
    restart: unless-stopped
    networks:
      - agricultural_network

  # 农产品价格API服务
  price_api:
    image: python:3.11-slim
    container_name: agricultural_api
    working_dir: /app
    volumes:
      - ./api:/app
      - ./data:/app/data
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    environment:
      - PYTHONPATH=/app
    command: >
      bash -c "
        pip install fastapi uvicorn pandas requests beautifulsoup4 schedule &&
        python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
      "
    restart: unless-stopped
    networks:
      - agricultural_network

  # Nginx反向代理
  nginx:
    image: nginx:alpine
    container_name: agricultural_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - odoo
      - price_api
    restart: unless-stopped
    networks:
      - agricultural_network

volumes:
  postgres_data:
  odoo_data:

networks:
  agricultural_network:
    driver: bridge
EOF

    log_info "Docker Compose配置创建完成"
}

# 创建Nginx配置
create_nginx_config() {
    log_info "创建Nginx配置..."
    
    mkdir -p nginx
    
    cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream odoo {
        server odoo:8069;
    }
    
    upstream api {
        server price_api:8000;
    }
    
    server {
        listen 80;
        server_name _;
        
        # Odoo ERP
        location / {
            proxy_pass http://odoo;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # 价格API
        location /api/ {
            proxy_pass http://api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # 静态文件
        location /static/ {
            proxy_pass http://api/static/;
        }
    }
}
EOF

    log_info "Nginx配置创建完成"
}

# 创建Odoo配置
create_odoo_config() {
    log_info "创建Odoo配置..."
    
    cat > odoo/config/odoo.conf << 'EOF'
[options]
addons_path = /mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons
data_dir = /var/lib/odoo
db_host = postgres
db_port = 5432
db_user = odoo
db_password = odoo123
admin_passwd = ZH3Y-6YB6-GAQV
logfile = /var/log/odoo/odoo.log
log_level = info
workers = 2
max_cron_threads = 1
EOF

    log_info "Odoo配置创建完成"
}

# 下载项目代码
download_project_code() {
    log_info "准备项目代码..."
    
    # 创建API目录和基础文件
    mkdir -p api/static/{css,js,html}
    
    # 创建基础API文件
    cat > api/main.py << 'EOF'
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import pandas as pd
import os
from datetime import datetime

app = FastAPI(title="农产品市场价格API", version="1.0.0")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {"message": "农产品市场价格管理系统", "version": "1.0.0", "status": "running"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/prices")
async def get_prices():
    try:
        # 检查数据文件是否存在
        data_file = "data/market_prices.csv"
        if os.path.exists(data_file):
            df = pd.read_csv(data_file)
            return {
                "success": True,
                "data": df.to_dict('records'),
                "count": len(df)
            }
        else:
            return {
                "success": True,
                "data": [],
                "count": 0,
                "message": "暂无数据"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

    # 创建示例数据
    mkdir -p data
    cat > data/market_prices.csv << 'EOF'
product_name,category,price,date,market,unit
白菜,vegetables,2.5,2025-01-25,北京新发地,公斤
苹果,fruits,8.0,2025-01-25,北京新发地,公斤
猪肉,meat,28.0,2025-01-25,北京新发地,公斤
带鱼,aquatic,35.0,2025-01-25,北京新发地,公斤
EOF

    log_info "项目代码准备完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 启动Docker服务
    sudo systemctl start docker
    
    # 构建并启动容器
    docker-compose up -d
    
    log_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    docker-compose ps
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."
    
    # 检查ufw是否安装
    if command -v ufw &> /dev/null; then
        sudo ufw allow 22    # SSH
        sudo ufw allow 80    # HTTP
        sudo ufw allow 443   # HTTPS
        sudo ufw allow 8000  # API
        sudo ufw allow 8069  # Odoo
        sudo ufw --force enable
        log_info "防火墙配置完成"
    else
        log_warn "ufw未安装，跳过防火墙配置"
    fi
}

# 创建管理脚本
create_management_scripts() {
    log_info "创建管理脚本..."
    
    # 创建启动脚本
    cat > scripts/start.sh << 'EOF'
#!/bin/bash
cd ~/agricultural-platform
docker-compose up -d
echo "服务已启动"
docker-compose ps
EOF

    # 创建停止脚本
    cat > scripts/stop.sh << 'EOF'
#!/bin/bash
cd ~/agricultural-platform
docker-compose down
echo "服务已停止"
EOF

    # 创建重启脚本
    cat > scripts/restart.sh << 'EOF'
#!/bin/bash
cd ~/agricultural-platform
docker-compose down
docker-compose up -d
echo "服务已重启"
docker-compose ps
EOF

    # 创建备份脚本
    cat > scripts/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=~/agricultural-platform/backups
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
docker exec agricultural_postgres pg_dump -U odoo postgres > $BACKUP_DIR/db_backup_$DATE.sql

# 备份数据文件
tar -czf $BACKUP_DIR/data_backup_$DATE.tar.gz data/

echo "备份完成: $BACKUP_DIR"
ls -la $BACKUP_DIR/
EOF

    # 给脚本执行权限
    chmod +x scripts/*.sh
    
    log_info "管理脚本创建完成"
}

# 显示部署信息
show_deployment_info() {
    log_info "=== 部署完成 ==="
    
    # 获取服务器IP
    PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "获取IP失败")
    PRIVATE_IP=$(hostname -I | awk '{print $1}')
    
    echo ""
    echo "🌐 访问地址:"
    echo "  Odoo ERP系统: http://$PUBLIC_IP (或 http://$PRIVATE_IP)"
    echo "  价格API: http://$PUBLIC_IP:8000 (或 http://$PRIVATE_IP:8000)"
    echo ""
    echo "🔐 登录信息:"
    echo "  Odoo管理员: admin"
    echo "  Odoo密码: admin123"
    echo "  Odoo主密码: ZH3Y-6YB6-GAQV"
    echo ""
    echo "📁 项目目录: ~/agricultural-platform"
    echo ""
    echo "🛠️ 管理命令:"
    echo "  启动服务: ~/agricultural-platform/scripts/start.sh"
    echo "  停止服务: ~/agricultural-platform/scripts/stop.sh"
    echo "  重启服务: ~/agricultural-platform/scripts/restart.sh"
    echo "  数据备份: ~/agricultural-platform/scripts/backup.sh"
    echo ""
    echo "📊 服务状态:"
    cd ~/agricultural-platform && docker-compose ps
}

# 主函数
main() {
    log_info "开始华为云服务器部署..."
    
    check_system
    update_system
    install_docker
    install_docker_compose
    create_project_structure
    create_docker_compose
    create_nginx_config
    create_odoo_config
    download_project_code
    create_management_scripts
    start_services
    configure_firewall
    show_deployment_info
    
    log_info "部署完成！"
}

# 执行主函数
main
