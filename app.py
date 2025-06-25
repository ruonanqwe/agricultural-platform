#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
农产品市场价格管理平台
前后端一体化Web应用
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import json
import pandas as pd
from datetime import datetime, timedelta
import asyncio
import threading
import time
import logging
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

# 导入自定义模块
from core.data_manager import get_data_manager
from core.crawler import get_crawler
from core.report_crawler import get_report_crawler
from core.report_analyzer import ReportAnalyzer
from core.scheduler import get_scheduler
from core.config import config

# 创建FastAPI应用
app = FastAPI(
    title="农产品市场价格管理平台",
    description="前后端一体化的市场价格数据管理系统",
    version="2.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
data_manager = get_data_manager()
crawler = get_crawler()
report_crawler = get_report_crawler()
scheduler = get_scheduler()
report_analyzer = ReportAnalyzer(data_manager)

# 数据模型
class CrawlConfig(BaseModel):
    enabled: bool = True
    interval_minutes: int = 30
    provinces: List[str] = []

class SearchQuery(BaseModel):
    province: Optional[str] = None
    variety: Optional[str] = None
    market: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    limit: int = 100

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """主页"""
    return FileResponse("static/index.html")

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

@app.get("/api/stats")
async def get_stats():
    """获取系统统计信息"""
    try:
        stats = data_manager.get_statistics()
        crawler_status = crawler.get_status()
        scheduler_status = scheduler.get_status()
        
        return {
            "success": True,
            "data": {
                "data_stats": stats,
                "crawler_status": crawler_status,
                "scheduler_status": scheduler_status
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search")
async def search_data(query: SearchQuery):
    """搜索数据"""
    try:
        results = data_manager.search_data(
            province=query.province,
            variety=query.variety,
            market=query.market,
            date_from=query.date_from,
            date_to=query.date_to,
            limit=query.limit
        )
        
        return {
            "success": True,
            "count": len(results),
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/latest")
async def get_latest_data(limit: int = 50):
    """获取最新数据"""
    try:
        results = data_manager.get_latest_data(limit)
        return {
            "success": True,
            "count": len(results),
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/provinces")
async def get_provinces():
    """获取省份列表"""
    try:
        provinces = data_manager.get_provinces()
        return {
            "success": True,
            "data": provinces
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/varieties")
async def get_varieties():
    """获取品种列表"""
    try:
        varieties = data_manager.get_varieties()
        return {
            "success": True,
            "data": varieties
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/markets")
async def get_markets():
    """获取市场列表"""
    try:
        markets = data_manager.get_markets()
        return {
            "success": True,
            "data": markets
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/crawler/start")
async def start_crawler(background_tasks: BackgroundTasks):
    """启动爬虫"""
    try:
        background_tasks.add_task(crawler.start_crawling)
        return {"success": True, "message": "爬虫已启动"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/crawler/stop")
async def stop_crawler():
    """停止爬虫"""
    try:
        crawler.stop_crawling()
        return {"success": True, "message": "爬虫已停止"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/crawler/status")
async def get_crawler_status():
    """获取爬虫状态"""
    try:
        status = crawler.get_status()
        return {"success": True, "data": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/crawler/config")
async def update_crawler_config(config: CrawlConfig):
    """更新爬虫配置"""
    try:
        crawler.update_config(config.model_dump())
        return {"success": True, "message": "配置已更新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 报告爬虫API接口
@app.post("/api/report-crawler/start")
async def start_report_crawler(background_tasks: BackgroundTasks):
    """启动报告爬虫"""
    try:
        background_tasks.add_task(report_crawler.start_crawling)
        return {"success": True, "message": "报告爬虫已启动"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/report-crawler/stop")
async def stop_report_crawler():
    """停止报告爬虫"""
    try:
        report_crawler.stop_crawling()
        return {"success": True, "message": "报告爬虫已停止"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/report-crawler/status")
async def get_report_crawler_status():
    """获取报告爬虫状态"""
    try:
        status = report_crawler.get_status()
        return {"success": True, "data": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/report-crawler/crawl-once")
async def crawl_reports_once(background_tasks: BackgroundTasks, full_crawl: bool = True):
    """执行一次报告爬取

    Args:
        full_crawl: 是否进行完整爬取（所有页面）
    """
    try:
        # 临时设置爬取模式
        original_config = report_crawler.config.get('full_crawl', True)
        report_crawler.config['full_crawl'] = full_crawl

        background_tasks.add_task(report_crawler.crawl_once)

        # 恢复原始配置
        report_crawler.config['full_crawl'] = original_config

        crawl_mode = "完整爬取" if full_crawl else "快速爬取"
        return {"success": True, "message": f"开始执行单次报告爬取（{crawl_mode}）"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/latest")
async def get_latest_reports(limit: int = 20, page: int = 1, report_type: str = "all"):
    """获取最新报告

    Args:
        limit: 每页数量
        page: 页码
        report_type: 报告类型 (all, daily, monthly, yearly)
    """
    try:
        reports_file = data_manager.data_dir / "analysis_reports.csv"

        if not reports_file.exists():
            return {
                "success": True,
                "count": 0,
                "data": [],
                "total": 0,
                "page": page,
                "total_pages": 0,
                "report_type": report_type
            }

        import pandas as pd
        df = pd.read_csv(reports_file, encoding='utf-8-sig')

        if df.empty:
            return {
                "success": True,
                "count": 0,
                "data": [],
                "total": 0,
                "page": page,
                "total_pages": 0,
                "report_type": report_type
            }

        # 清理数据
        df = df.fillna('')

        # 根据报告类型过滤
        if report_type != "all":
            if report_type == "daily":
                df = df[df['报告类型'] == '农产品批发市场价格日报']
            elif report_type == "monthly":
                df = df[df['报告类型'] == '农业分析报告']
            elif report_type == "yearly":
                # 目前没有年报，预留接口
                df = df[df['报告类型'].str.contains('年报', na=False)]

        # 按爬取时间排序
        if '爬取时间' in df.columns:
            df = df.sort_values('爬取时间', ascending=False)

        # 计算分页
        total_records = len(df)
        total_pages = (total_records + limit - 1) // limit
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit

        # 获取当前页数据
        page_df = df.iloc[start_idx:end_idx]

        # 转换为字典并清理数值
        records = page_df.to_dict('records')

        return {
            "success": True,
            "count": len(records),
            "data": records,
            "total": total_records,
            "page": page,
            "total_pages": total_pages,
            "limit": limit,
            "report_type": report_type
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/stats")
async def get_report_stats():
    """获取报告统计信息"""
    try:
        reports_file = data_manager.data_dir / "analysis_reports.csv"

        if not reports_file.exists():
            return {
                "total": 0,
                "daily_count": 0,
                "monthly_count": 0,
                "yearly_count": 0,
                "types": []
            }

        import pandas as pd
        df = pd.read_csv(reports_file, encoding='utf-8-sig')

        if df.empty:
            return {
                "total": 0,
                "daily_count": 0,
                "monthly_count": 0,
                "yearly_count": 0,
                "types": []
            }

        # 统计各类型报告数量
        daily_count = len(df[df['报告类型'] == '农产品批发市场价格日报'])
        monthly_count = len(df[df['报告类型'] == '农业分析报告'])
        yearly_count = len(df[df['报告类型'].str.contains('年报', na=False)])

        # 获取所有报告类型
        types = df['报告类型'].value_counts().to_dict()

        return {
            "total": len(df),
            "daily_count": daily_count,
            "monthly_count": monthly_count,
            "yearly_count": yearly_count,
            "types": types
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/export")
async def export_reports():
    """导出报告数据"""
    try:
        reports_file = data_manager.data_dir / "analysis_reports.csv"

        if not reports_file.exists():
            raise HTTPException(status_code=404, detail="报告文件不存在")

        return FileResponse(
            reports_file,
            media_type='application/octet-stream',
            filename=f"analysis_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/csv")
async def export_csv(
    province: Optional[str] = None,
    variety: Optional[str] = None,
    market: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """导出CSV文件"""
    try:
        file_path = data_manager.export_csv(
            province=province,
            variety=variety,
            market=market,
            date_from=date_from,
            date_to=date_to
        )
        
        return FileResponse(
            file_path,
            media_type='application/octet-stream',
            filename=f"market_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/trends")
async def get_dashboard_trends(days: int = 30):
    """获取仪表板趋势数据"""
    try:
        # 获取价格数据趋势
        price_trends = await get_price_trends(days)

        # 获取报告数据趋势
        report_trends = await get_report_trends()

        # 获取关键指标
        key_metrics = await get_key_metrics()

        return {
            "success": True,
            "data": {
                "price_trends": price_trends,
                "report_trends": report_trends,
                "key_metrics": key_metrics,
                "last_update": datetime.now().isoformat(),
                "time_range": f"{days}天"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_price_trends(days: int = 30):
    """获取价格趋势数据"""
    try:
        # 从CSV文件获取指定天数的价格数据
        csv_file = data_manager.data_dir / "market_prices.csv"

        import pandas as pd

        real_data = []
        if csv_file.exists():
            df = pd.read_csv(csv_file, encoding='utf-8-sig')

            if not df.empty:
                # 清理数据
                df = df.fillna(0)

                # 按日期分组计算平均价格
                if '交易日期' in df.columns and '平均价' in df.columns:
                    df['交易日期'] = pd.to_datetime(df['交易日期'], errors='coerce')
                    df = df.dropna(subset=['交易日期'])

                    # 获取指定天数的数据
                    recent_date = df['交易日期'].max()
                    start_date = recent_date - pd.Timedelta(days=days)
                    recent_df = df[df['交易日期'] >= start_date]

                    # 按日期分组计算平均价格
                    daily_avg = recent_df.groupby('交易日期')['平均价'].mean().reset_index()
                    daily_avg = daily_avg.sort_values('交易日期')

                    for _, row in daily_avg.iterrows():
                        real_data.append({
                            '交易日期': row['交易日期'].strftime('%Y-%m-%d'),
                            '平均价': float(row['平均价'])
                        })

        # 只返回真实数据，不生成模拟数据

        return real_data

    except Exception as e:
        logger.error(f"获取价格趋势失败: {e}")
        return []

async def get_report_trends():
    """获取报告趋势数据"""
    try:
        # 从CSV文件获取报告数据
        reports_file = data_manager.data_dir / "analysis_reports.csv"
        if not reports_file.exists():
            return []

        import pandas as pd
        df = pd.read_csv(reports_file, encoding='utf-8-sig')

        if df.empty:
            return []

        # 按报告类型统计
        type_counts = df['报告类型'].value_counts().to_dict()

        # 按日期统计报告数量
        if '爬取时间' in df.columns:
            df['爬取时间'] = pd.to_datetime(df['爬取时间'], errors='coerce')
            df = df.dropna(subset=['爬取时间'])
            df['日期'] = df['爬取时间'].dt.date

            daily_counts = df.groupby('日期').size().reset_index(name='报告数量')
            daily_counts['日期'] = daily_counts['日期'].astype(str)

            return {
                "type_distribution": type_counts,
                "daily_counts": daily_counts.to_dict('records')
            }

        return {"type_distribution": type_counts, "daily_counts": []}
    except Exception as e:
        logger.error(f"获取报告趋势失败: {e}")
        return {}

async def get_key_metrics():
    """获取关键指标"""
    try:
        metrics = {}

        # 价格指标
        csv_file = data_manager.data_dir / "market_prices.csv"
        if csv_file.exists():
            import pandas as pd
            df = pd.read_csv(csv_file, encoding='utf-8-sig')

            if not df.empty:
                df = df.fillna(0)

                # 计算价格指标
                if '平均价' in df.columns:
                    metrics['avg_price'] = float(df['平均价'].mean())
                    metrics['max_price'] = float(df['平均价'].max())
                    metrics['min_price'] = float(df['平均价'].min())

                # 计算价格变化趋势
                if '交易日期' in df.columns and '平均价' in df.columns:
                    df['交易日期'] = pd.to_datetime(df['交易日期'], errors='coerce')
                    df = df.dropna(subset=['交易日期'])
                    df = df.sort_values('交易日期')

                    if len(df) >= 2:
                        recent_price = df.iloc[-1]['平均价']
                        previous_price = df.iloc[-2]['平均价']
                        if previous_price > 0:
                            price_change = ((recent_price - previous_price) / previous_price) * 100
                            metrics['price_change_percent'] = round(price_change, 2)

        # 报告指标
        reports_file = data_manager.data_dir / "analysis_reports.csv"
        if reports_file.exists():
            import pandas as pd
            df = pd.read_csv(reports_file, encoding='utf-8-sig')

            if not df.empty:
                metrics['total_reports'] = len(df)
                metrics['report_types'] = df['报告类型'].nunique() if '报告类型' in df.columns else 0

        return metrics
    except Exception as e:
        logger.error(f"获取关键指标失败: {e}")
        return {}

@app.get("/api/dashboard/data")
async def get_dashboard_data():
    """获取仪表盘数据"""
    try:
        dashboard_data = report_analyzer.get_dashboard_data()
        return dashboard_data
    except Exception as e:
        logger.error(f"获取仪表盘数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/trends")
async def get_trends_data(category: str = "all"):
    """获取趋势数据

    Args:
        category: 数据类别 (all, price_index, vegetables, fruits, meat, aquatic)
    """
    try:
        dashboard_data = report_analyzer.get_dashboard_data()

        if not dashboard_data.get("success"):
            return dashboard_data

        trends_data = dashboard_data["data"]

        if category == "all":
            return {"success": True, "data": trends_data}
        elif category == "price_index":
            return {"success": True, "data": {"price_index_trend": trends_data.get("price_index_trend", [])}}
        elif category in ["vegetables", "fruits", "meat", "aquatic"]:
            category_trends = trends_data.get("category_price_trends", {})
            return {"success": True, "data": {category: category_trends.get(category, [])}}
        else:
            return {"success": False, "error": "无效的数据类别"}

    except Exception as e:
        logger.error(f"获取趋势数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    print("🚀 农产品市场价格管理平台启动中...")
    
    # 初始化数据管理器
    data_manager.initialize()
    
    # 启动调度器
    scheduler.start()
    
    print("✅ 平台启动完成!")
    print(f"📊 管理界面: http://localhost:8000")
    print(f"📖 API文档: http://localhost:8000/docs")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    print("🛑 平台正在关闭...")
    
    # 停止爬虫
    crawler.stop_crawling()
    
    # 停止调度器
    scheduler.stop()
    
    print("✅ 平台已安全关闭")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
