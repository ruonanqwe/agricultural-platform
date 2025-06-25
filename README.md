# 农产品市场价格管理系统

## 🌾 项目简介

农产品市场价格管理系统是一个集成了数据采集、价格分析、趋势预测和ERP管理的综合性平台。系统支持实时价格监控、数据可视化分析，并可与Odoo ERP系统无缝集成。

## ✨ 主要功能

### 📊 数据管理
- **实时价格采集**: 自动抓取农产品市场价格数据
- **数据存储**: 支持CSV文件和数据库双重存储
- **历史数据**: 完整的价格历史记录和趋势分析
- **数据备份**: 自动定时备份，确保数据安全

### 📈 数据分析
- **价格趋势**: 实时价格走势图表
- **波动分析**: 价格波动率统计和预警
- **分类统计**: 按产品分类进行价格分析
- **市场对比**: 不同市场价格对比分析

### 🎯 可视化仪表盘
- **实时仪表盘**: 美观的数据可视化界面
- **动态图表**: 支持多种图表类型展示
- **响应式设计**: 完美适配桌面和移动设备
- **交互式操作**: 支持数据筛选和实时刷新

### 🔗 ERP集成
- **Odoo集成**: 与Odoo ERP系统无缝对接
- **数据同步**: 自动同步价格数据到ERP系统
- **业务流程**: 支持采购、销售、库存管理
- **报表生成**: 自动生成各类业务报表

## 🚀 技术架构

### 后端技术
- **Python 3.11**: 主要开发语言
- **FastAPI**: 高性能Web框架
- **Pandas**: 数据处理和分析
- **BeautifulSoup**: 网页数据抓取
- **Schedule**: 定时任务调度

### 前端技术
- **HTML5/CSS3**: 现代化界面设计
- **JavaScript ES6+**: 交互逻辑实现
- **Chart.js**: 数据可视化图表
- **Bootstrap**: 响应式UI框架

### 数据库
- **PostgreSQL**: 主数据库（Odoo集成）
- **CSV文件**: 轻量级数据存储
- **数据备份**: 多重备份策略

### 部署方案
- **Docker**: 容器化部署
- **Docker Compose**: 多服务编排
- **Nginx**: 反向代理和负载均衡
- **云服务器**: 支持华为云、阿里云等

## 📦 项目结构

```
agricultural-platform/
├── app.py                 # 主应用程序
├── start.py              # 启动脚本
├── requirements.txt      # Python依赖
├── docker-compose.yml    # Docker编排文件
├── Dockerfile           # Docker镜像构建
├── README.md            # 项目说明
├── data/                # 数据目录
│   ├── market_prices.csv
│   └── backups/
├── static/              # 静态资源
│   ├── css/
│   ├── js/
│   └── html/
├── templates/           # 模板文件
├── utils/              # 工具模块
├── config/             # 配置文件
├── logs/               # 日志文件
├── scripts/            # 部署脚本
└── docs/               # 文档
```

## 🛠️ 快速开始

### 环境要求
- Python 3.11+
- Docker & Docker Compose
- 4GB+ 内存
- 20GB+ 磁盘空间

### 本地开发

```bash
# 1. 克隆项目
git clone https://gitcode.com/your-username/agricultural-platform.git
cd agricultural-platform

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动服务
python start.py
```

### Docker部署

```bash
# 1. 克隆项目
git clone https://gitcode.com/your-username/agricultural-platform.git
cd agricultural-platform

# 2. 启动服务
docker-compose up -d

# 3. 访问系统
# 价格系统: http://localhost:8000
# Odoo ERP: http://localhost:8069
```

### 云服务器部署

```bash
# 1. 下载部署脚本
wget https://gitcode.com/your-username/agricultural-platform/raw/main/scripts/deploy.sh

# 2. 执行部署
chmod +x deploy.sh
./deploy.sh

# 3. 访问系统
# 使用服务器公网IP访问
```

## 🔧 配置说明

### 环境变量
```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=agricultural_db
DB_USER=admin
DB_PASSWORD=your_password

# Odoo配置
ODOO_URL=http://localhost:8069
ODOO_DB=agricultural_db
ODOO_USER=admin
ODOO_PASSWORD=admin123
ODOO_MASTER_PASSWORD=ZH3Y-6YB6-GAQV

# API配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
```

### 数据源配置
系统支持多个数据源：
- 农业农村部价格监测平台
- 各地农产品批发市场
- 第三方价格数据API
- 手动数据录入

## 📊 使用指南

### 1. 系统初始化
- 访问系统首页
- 配置数据源
- 设置采集频率
- 初始化数据库

### 2. 数据采集
- 自动定时采集
- 手动触发采集
- 数据验证和清洗
- 异常数据处理

### 3. 数据分析
- 查看实时价格
- 分析价格趋势
- 生成分析报告
- 设置价格预警

### 4. ERP集成
- 连接Odoo系统
- 同步产品数据
- 管理采购销售
- 生成业务报表

## 🔐 安全说明

- 所有API接口支持认证
- 数据传输使用HTTPS加密
- 定期安全更新和漏洞修复
- 支持角色权限管理

## 📈 性能优化

- 数据库索引优化
- 缓存机制实现
- 异步任务处理
- 负载均衡配置

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系我们

- 项目主页: https://gitcode.com/your-username/agricultural-platform
- 问题反馈: https://gitcode.com/your-username/agricultural-platform/issues
- 邮箱: support@agricultural-platform.com

## 🙏 致谢

感谢所有为本项目做出贡献的开发者和用户！

---

**⭐ 如果这个项目对您有帮助，请给我们一个Star！**
