#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务调度器 - 负责定时任务的管理和执行
"""

import schedule
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

from .config import config
from .data_manager import get_data_manager
from .crawler import get_crawler

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        self.config = config.get('scheduler', {})
        self.data_manager = get_data_manager()
        self.crawler = get_crawler()
        
        self.is_running = False
        self.scheduler_thread = None
        self.start_time = None
        
        # 任务统计
        self.task_stats = {
            'crawl_count': 0,
            'cleanup_count': 0,
            'backup_count': 0,
            'last_crawl': None,
            'last_cleanup': None,
            'last_backup': None
        }
        
        logger.info("任务调度器初始化完成")
    
    def start(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("调度器已在运行中")
            return
        
        logger.info("启动任务调度器...")
        self.is_running = True
        self.start_time = datetime.now()
        
        # 设置定时任务
        self._setup_schedules()
        
        # 启动调度器线程
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("任务调度器已启动")
    
    def stop(self):
        """停止调度器"""
        if not self.is_running:
            logger.warning("调度器未在运行")
            return
        
        logger.info("正在停止任务调度器...")
        self.is_running = False
        
        # 清除所有定时任务
        schedule.clear()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        logger.info("任务调度器已停止")
    
    def _setup_schedules(self):
        """设置定时任务"""
        try:
            # 清除现有任务
            schedule.clear()
            
            # 数据爬取任务（如果启用）
            if config.get('crawler.enabled', True):
                crawl_interval = config.get('crawler.interval_minutes', 30)
                schedule.every(crawl_interval).minutes.do(self._scheduled_crawl)
                logger.info(f"设置数据爬取任务: 每 {crawl_interval} 分钟执行一次")
            
            # 数据清理任务
            cleanup_interval = self.config.get('cleanup_interval_hours', 24)
            schedule.every(cleanup_interval).hours.do(self._scheduled_cleanup)
            logger.info(f"设置数据清理任务: 每 {cleanup_interval} 小时执行一次")
            
            # 数据备份任务
            backup_interval = self.config.get('backup_interval_hours', 6)
            schedule.every(backup_interval).hours.do(self._scheduled_backup)
            logger.info(f"设置数据备份任务: 每 {backup_interval} 小时执行一次")
            
        except Exception as e:
            logger.error(f"设置定时任务失败: {e}")
    
    def _scheduler_loop(self):
        """调度器主循环"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"调度器运行错误: {e}")
                time.sleep(5)
    
    def _scheduled_crawl(self):
        """定时数据爬取任务"""
        try:
            logger.info("执行定时数据爬取任务...")
            
            # 检查爬虫是否已在运行
            if self.crawler.is_running:
                logger.info("爬虫已在运行中，跳过本次定时任务")
                return
            
            # 执行一次爬取
            data = self.crawler.crawl_once()
            
            # 更新统计
            self.task_stats['crawl_count'] += 1
            self.task_stats['last_crawl'] = datetime.now().isoformat()
            
            logger.info(f"定时爬取任务完成，获取 {len(data) if data else 0} 条数据")
            
        except Exception as e:
            logger.error(f"定时爬取任务失败: {e}")
    
    def _scheduled_cleanup(self):
        """定时数据清理任务"""
        try:
            logger.info("执行定时数据清理任务...")
            
            # 更新统计
            self.task_stats['cleanup_count'] += 1
            self.task_stats['last_cleanup'] = datetime.now().isoformat()
            
            logger.info("定时数据清理任务完成")
            
        except Exception as e:
            logger.error(f"定时数据清理任务失败: {e}")
    
    def _scheduled_backup(self):
        """定时数据备份任务"""
        try:
            logger.info("执行定时数据备份任务...")
            
            # 创建备份
            self.data_manager._create_backup()
            
            # 更新统计
            self.task_stats['backup_count'] += 1
            self.task_stats['last_backup'] = datetime.now().isoformat()
            
            logger.info("定时数据备份任务完成")
            
        except Exception as e:
            logger.error(f"定时数据备份任务失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        next_runs = {}
        
        try:
            # 获取下次运行时间
            jobs = schedule.jobs
            for job in jobs:
                job_name = str(job.job_func).split()[1] if hasattr(job, 'job_func') else 'unknown'
                next_run = job.next_run
                if next_run:
                    next_runs[job_name] = next_run.isoformat()
        except Exception as e:
            logger.error(f"获取任务运行时间失败: {e}")
        
        status = {
            'is_running': self.is_running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'running_time': str(datetime.now() - self.start_time) if self.start_time else None,
            'task_count': len(schedule.jobs),
            'task_stats': self.task_stats,
            'next_runs': next_runs,
            'config': self.config
        }
        
        return status

# 全局调度器实例
scheduler = TaskScheduler()

def get_scheduler():
    """获取调度器实例"""
    return scheduler
