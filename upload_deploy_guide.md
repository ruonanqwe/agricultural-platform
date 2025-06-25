# 华为云CloudShell部署指南

## 📋 在CloudShell中部署农产品系统的步骤

### 1. 上传部署脚本

在CloudShell终端中执行以下命令：

```bash
# 创建部署脚本
cat > huawei_cloud_deploy.sh << 'EOF'
# 这里粘贴完整的部署脚本内容
EOF

# 给脚本执行权限
chmod +x huawei_cloud_deploy.sh
```

### 2. 或者使用wget下载脚本

如果您有GitHub或其他代码托管：

```bash
# 下载脚本（如果您上传到了代码仓库）
wget https://your-repo.com/huawei_cloud_deploy.sh
chmod +x huawei_cloud_deploy.sh
```

### 3. 直接在CloudShell中创建和运行

**方法一：逐步创建文件**

```bash
# 1. 创建工作目录
mkdir -p ~/agricultural-platform
cd ~/agricultural-platform

# 2. 更新系统
sudo apt update -y
sudo apt install -y curl wget git vim

# 3. 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 4. 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 5. 创建Docker Compose配置
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: postgres
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: odoo123
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  odoo:
    image: odoo:16.0
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
      - ./addons:/mnt/extra-addons
    restart: unless-stopped

volumes:
  postgres_data:
  odoo_data:
EOF

# 6. 启动服务
docker-compose up -d

# 7. 检查服务状态
docker-compose ps
```

### 4. 快速一键部署命令

```bash
# 创建并运行部署脚本
curl -sSL https://raw.githubusercontent.com/your-repo/agricultural-platform/main/deploy.sh | bash
```

### 5. 手动上传文件方式

如果您有本地文件需要上传：

```bash
# 在CloudShell中创建目录
mkdir -p ~/upload
cd ~/upload

# 使用CloudShell的文件上传功能
# 点击右上角的上传按钮，选择您的文件

# 解压上传的文件（如果是压缩包）
unzip your-files.zip
tar -xzf your-files.tar.gz

# 移动到工作目录
mv * ~/agricultural-platform/
```

## 🚀 推荐的部署流程

### 步骤1：准备环境
```bash
# 检查系统信息
uname -a
free -h
df -h

# 更新系统
sudo apt update && sudo apt upgrade -y
```

### 步骤2：安装Docker环境
```bash
# 安装Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

### 步骤3：部署应用
```bash
# 创建项目目录
mkdir -p ~/agricultural-platform
cd ~/agricultural-platform

# 创建配置文件（使用上面提供的docker-compose.yml）

# 启动服务
docker-compose up -d

# 等待服务启动
sleep 30

# 检查服务状态
docker-compose ps
docker-compose logs
```

### 步骤4：配置访问
```bash
# 获取服务器IP地址
curl ifconfig.me

# 配置防火墙（如果需要）
sudo ufw allow 8069
sudo ufw allow 8000
```

## 🔧 常用管理命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 更新服务
docker-compose pull
docker-compose up -d

# 进入容器
docker exec -it agricultural_odoo bash
docker exec -it agricultural_postgres psql -U odoo
```

## 📊 访问地址

部署完成后，您可以通过以下地址访问：

- **Odoo ERP**: `http://您的服务器IP:8069`
- **数据库**: `http://您的服务器IP:5432`

## 🔐 默认登录信息

- **Odoo管理员**: admin
- **Odoo密码**: admin123  
- **Odoo主密码**: ZH3Y-6YB6-GAQV
- **数据库用户**: odoo
- **数据库密码**: odoo123

## 🆘 故障排除

### 常见问题：

1. **Docker权限问题**
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```

2. **端口被占用**
   ```bash
   sudo netstat -tulpn | grep :8069
   sudo kill -9 PID
   ```

3. **服务启动失败**
   ```bash
   docker-compose logs
   docker system prune -f
   ```

4. **内存不足**
   ```bash
   free -h
   # 如果内存不足，考虑添加swap
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

现在您可以在CloudShell中按照这些步骤进行部署！
