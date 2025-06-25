#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
农产品市场价格管理平台启动脚本
"""

import uvicorn
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """主函数"""
    print("🚀 启动农产品市场价格管理平台...")
    print("=" * 50)
    
    # 确保必要的目录存在
    directories = ['data', 'logs', 'static/css', 'static/js']
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # 启动配置
    config = {
        "app": "app:app",
        "host": "0.0.0.0",
        "port": 8000,
        "reload": True,
        "log_level": "info",
        "access_log": True
    }
    
    print(f"📊 管理界面: http://localhost:{config['port']}")
    print(f"📖 API文档: http://localhost:{config['port']}/docs")
    print("=" * 50)
    
    try:
        uvicorn.run(**config)
    except KeyboardInterrupt:
        print("\n🛑 平台已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
