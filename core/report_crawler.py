#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
农业部分析报告爬虫 - 负责从农业部网站爬取分析报告数据
基于 https://pfsc.agri.cn/#/analysisReport
"""

import requests
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import urllib3
from bs4 import BeautifulSoup
import re

from .config import config
from .data_manager import get_data_manager

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReportCrawler:
    """农业部分析报告爬虫"""
    
    def __init__(self):
        self.config = config.get_report_crawler_config()
        self.data_manager = get_data_manager()
        
        self.is_running = False
        self.crawler_thread = None
        self.start_time = None
        self.crawled_count = 0
        self.error_count = 0
        
        # 农业部分析报告API配置
        self.base_url = "https://pfsc.agri.cn/api"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://pfsc.agri.cn",
            "Referer": "https://pfsc.agri.cn/",
            "Connection": "keep-alive",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "Windows",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin"
        }
        
        self.timeout = self.config.get('timeout_seconds', 30)
        self.retry_times = self.config.get('retry_times', 3)
        
        # 报告类型配置 - 多种报告类型
        self.report_types = [
            {"id": "daily", "name": "农产品批发市场价格日报", "code": "daily_price_report", "api": "FarmDaily/list"},
            {"id": "weekly", "name": "农产品批发市场价格周报", "code": "weekly_price_report", "api": "farmWeekly/pageList"},
            {"id": "analysis", "name": "农业分析报告", "code": "analysis_report", "api": "portal-analysis-report/selectListByPage"}
        ]
        
        logger.info("农业部分析报告爬虫初始化完成")
    
    def start_crawling(self):
        """启动报告爬虫"""
        if self.is_running:
            logger.warning("报告爬虫已在运行中")
            return
        
        logger.info("启动农业部分析报告爬虫...")
        self.is_running = True
        self.start_time = datetime.now()
        self.crawled_count = 0
        self.error_count = 0
        
        # 启动爬虫线程
        self.crawler_thread = threading.Thread(target=self._crawl_loop, daemon=True)
        self.crawler_thread.start()
        
        logger.info("分析报告爬虫已启动")
    
    def stop_crawling(self):
        """停止报告爬虫"""
        if not self.is_running:
            logger.warning("报告爬虫未在运行")
            return
        
        logger.info("正在停止分析报告爬虫...")
        self.is_running = False
        
        if self.crawler_thread and self.crawler_thread.is_alive():
            self.crawler_thread.join(timeout=10)
        
        logger.info("分析报告爬虫已停止")
    
    def _crawl_loop(self):
        """爬虫主循环"""
        interval_hours = self.config.get('report_interval_hours', 6)  # 6小时爬取一次报告
        
        while self.is_running:
            try:
                logger.info("开始新一轮分析报告爬取...")
                
                # 爬取所有类型的报告
                all_reports = self._crawl_all_reports()
                
                if all_reports:
                    # 保存报告数据
                    saved_count = self._save_reports(all_reports)
                    self.crawled_count += saved_count
                    
                    logger.info(f"本轮报告爬取完成，获取 {len(all_reports)} 篇报告，已保存 {saved_count} 篇")
                else:
                    logger.warning("本轮报告爬取未获取到数据")
                
                # 等待下一轮
                if self.is_running:
                    logger.info(f"等待 {interval_hours} 小时后进行下一轮报告爬取...")
                    time.sleep(interval_hours * 3600)
                
            except Exception as e:
                logger.error(f"报告爬取过程出错: {e}")
                self.error_count += 1
                
                if self.is_running:
                    time.sleep(300)  # 出错后等待5分钟再重试
    
    def _crawl_all_reports(self) -> List[Dict]:
        """爬取所有类型的分析报告"""
        all_reports = []
        
        try:
            for report_type in self.report_types:
                try:
                    reports = self._crawl_report_type(report_type)
                    if reports:
                        all_reports.extend(reports)
                        logger.info(f"报告类型 {report_type['name']} 爬取完成，获取 {len(reports)} 篇报告")
                    else:
                        logger.warning(f"报告类型 {report_type['name']} 未获取到数据")
                    
                    # 避免请求过快
                    time.sleep(3)
                    
                except Exception as e:
                    logger.error(f"报告类型 {report_type['name']} 爬取失败: {e}")
                    self.error_count += 1
                    continue
            
            return all_reports
            
        except Exception as e:
            logger.error(f"批量爬取报告失败: {e}")
            return []
    
    def _crawl_report_type(self, report_type: Dict[str, str]) -> List[Dict]:
        """爬取特定类型的报告"""
        try:
            logger.info(f"开始获取{report_type['name']}...")

            # 获取报告列表
            reports_list = self._get_reports_list(report_type)
            if not reports_list:
                logger.warning(f"报告类型 {report_type['name']} 没有找到报告列表")
                return []

            logger.info(f"{report_type['name']}共有 {len(reports_list)} 篇报告")

            # 处理所有爬取到的报告数据
            detailed_reports = []
            total_reports = len(reports_list)

            for i, report in enumerate(reports_list, 1):
                try:
                    report_detail = self._get_report_detail(report, report_type)
                    if report_detail:
                        detailed_reports.append(report_detail)
                        logger.info(f"成功处理报告 ({i}/{total_reports}): {report_detail.get('报告标题', '未知标题')}")

                    # 每处理10个报告休息一下，避免过快
                    if i % 10 == 0:
                        time.sleep(1)

                except Exception as e:
                    logger.error(f"处理报告数据失败 ({i}/{total_reports}): {e}")
                    continue

            logger.info(f"{report_type['name']} 处理完成，成功处理 {len(detailed_reports)}/{total_reports} 篇报告")
            return detailed_reports

        except Exception as e:
            logger.error(f"爬取报告类型 {report_type['name']} 失败: {e}")
            return []
    
    def _get_reports_list(self, report_type: Dict[str, str]) -> List[Dict]:
        """获取报告列表 - 支持多种API端点，分页爬取直到结束"""
        try:
            api_endpoint = report_type.get("api", "FarmDaily/list")
            url = f"{self.base_url}/{api_endpoint}"
            all_reports = []
            page_num = 1
            page_size = 20 if api_endpoint == "FarmDaily/list" else 10
            max_reports = self.config.get('max_reports_per_type', 1000)
            full_crawl = self.config.get('full_crawl', True)
            page_delay = self.config.get('page_delay_seconds', 2)

            logger.info(f"开始分页爬取 {report_type['name']}，完整爬取: {full_crawl}，最大数量: {max_reports}...")

            while True:
                try:
                    # 根据不同API构建请求参数
                    if api_endpoint == "FarmDaily/list":
                        # 日报API - POST请求
                        payload = {"pageNum": page_num, "pageSize": page_size}
                        response = self._make_request('POST', url, json=payload)
                    elif api_endpoint == "farmWeekly/pageList":
                        # 周报API - GET请求
                        params = {"pageNum": page_num, "pageSize": page_size}
                        response = self._make_request('GET', url, params=params)
                    elif api_endpoint == "portal-analysis-report/selectListByPage":
                        # 分析报告API - GET请求
                        params = {"pageable": True, "pageSize": page_size, "pageNum": page_num}
                        response = self._make_request('GET', url, params=params)
                    else:
                        logger.warning(f"未知的API端点: {api_endpoint}")
                        break

                    if not response or response.get("code") != 200:
                        logger.warning(f"{report_type['name']} 第{page_num}页请求失败")
                        break

                    content = response.get("content", {})

                    # 处理不同API的响应格式
                    if api_endpoint == "FarmDaily/list":
                        reports_list = content.get("list", [])
                        total_pages = content.get("pages", 0)
                    elif api_endpoint == "farmWeekly/pageList":
                        reports_list = content.get("list", [])
                        total_pages = content.get("pages", 0)
                    elif api_endpoint == "portal-analysis-report/selectListByPage":
                        reports_list = content.get("list", [])
                        total_pages = content.get("pages", 0)
                    else:
                        reports_list = []
                        total_pages = 0

                    # 如果当前页没有数据，停止爬取
                    if not reports_list:
                        logger.info(f"{report_type['name']} 第{page_num}页无数据，爬取结束")
                        break

                    # 为每个报告添加类型信息
                    for report in reports_list:
                        report['report_type'] = report_type

                    all_reports.extend(reports_list)
                    logger.info(f"{report_type['name']} 第{page_num}页获取 {len(reports_list)} 篇报告，累计 {len(all_reports)} 篇")

                    # 检查是否达到最大数量限制
                    if len(all_reports) >= max_reports:
                        logger.info(f"{report_type['name']} 已达到最大爬取数量 {max_reports}，停止爬取")
                        break

                    # 如果不是完整爬取模式，只爬取第一页
                    if not full_crawl:
                        logger.info(f"{report_type['name']} 非完整爬取模式，只爬取第一页")
                        break

                    # 如果已经是最后一页，停止爬取
                    if total_pages > 0 and page_num >= total_pages:
                        logger.info(f"{report_type['name']} 已爬取完所有 {total_pages} 页")
                        break

                    # 如果当前页数据少于页面大小，可能是最后一页
                    if len(reports_list) < page_size:
                        logger.info(f"{report_type['name']} 当前页数据不足，可能已到最后一页")
                        break

                    page_num += 1

                    # 避免请求过快
                    time.sleep(page_delay)

                except Exception as e:
                    logger.error(f"{report_type['name']} 第{page_num}页爬取失败: {e}")
                    break

            logger.info(f"成功获取 {report_type['name']} 报告列表，共 {len(all_reports)} 篇")
            return all_reports

        except Exception as e:
            logger.error(f"获取报告列表失败: {e}")
            return []
    
    def _get_report_detail(self, report: Dict, report_type: Dict[str, str]) -> Optional[Dict]:
        """获取报告详细内容 - 支持多种报告类型"""
        try:
            timestamp = datetime.now()
            api_endpoint = report_type.get("api", "FarmDaily/list")

            if api_endpoint == "FarmDaily/list":
                # 处理日报数据
                return self._process_daily_report(report, report_type, timestamp)
            elif api_endpoint == "farmWeekly/pageList":
                # 处理周报数据
                return self._process_weekly_report(report, report_type, timestamp)
            elif api_endpoint == "portal-analysis-report/selectListByPage":
                # 处理分析报告数据
                return self._process_analysis_report(report, report_type, timestamp)
            else:
                logger.warning(f"未知的报告类型: {api_endpoint}")
                return None

        except Exception as e:
            logger.error(f"处理报告数据失败: {e}")
            return None

    def _process_daily_report(self, report: Dict, report_type: Dict[str, str], timestamp: datetime) -> Dict:
        """处理日报数据"""
        return {
            # 基本信息
            "报告ID": str(report.get("id", "")),
            "报告标题": str(report.get("remark", "")),
            "报告类型": report_type.get("name", ""),
            "报告类型代码": report_type.get("code", ""),

            # 内容信息
            "总体结论": str(report.get("counclesion", "")),
            "畜产品结论": str(report.get("animalConclusion", "")),
            "水产品结论": str(report.get("aquaticConclusion", "")),
            "蔬菜结论": str(report.get("vegetablesConclusion", "")),
            "水果结论": str(report.get("fruitsConclusion", "")),
            "价格指数结论": str(report.get("indexConclusion", "")),
            "涨跌幅分析": str(report.get("incOrReduRange", "")),

            # 完整内容
            "报告内容": self._clean_html_content(report.get("countent", "")),
            "纯文本内容": str(report.get("countentstr", "")),

            # 时间信息
            "日报日期": str(report.get("daylyDate", "")),
            "创建时间": str(report.get("createDate", "")),
            "爬取时间": timestamp.strftime("%Y-%m-%d %H:%M:%S"),

            # 其他信息
            "来源": str(report.get("source", "")),
            "年份": str(report.get("year", "")),

            # 结构化数据
            "JSON数据": str(report.get("wordJson", "")),

            # 分类信息
            "数据类型": "价格监测",
            "监测范围": "全国农产品批发市场"
        }

    def _process_weekly_report(self, report: Dict, report_type: Dict[str, str], timestamp: datetime) -> Dict:
        """处理周报数据"""
        return {
            # 基本信息
            "报告ID": str(report.get("id", "")),
            "报告标题": str(report.get("title", "") or report.get("remark", "")),
            "报告类型": report_type.get("name", ""),
            "报告类型代码": report_type.get("code", ""),

            # 内容信息
            "报告摘要": str(report.get("summary", "")),
            "报告内容": self._clean_html_content(report.get("content", "")),
            "关键词": str(report.get("keywords", "")),

            # 时间信息
            "发布时间": str(report.get("publishTime", "")),
            "创建时间": str(report.get("createTime", "")),
            "爬取时间": timestamp.strftime("%Y-%m-%d %H:%M:%S"),

            # 其他信息
            "来源": str(report.get("source", "")),
            "作者": str(report.get("author", "")),
            "状态": str(report.get("status", "")),

            # 分类信息
            "数据类型": "周度分析",
            "监测范围": "全国农产品市场"
        }

    def _process_analysis_report(self, report: Dict, report_type: Dict[str, str], timestamp: datetime) -> Dict:
        """处理分析报告数据"""
        return {
            # 基本信息
            "报告ID": str(report.get("id", "")),
            "报告标题": str(report.get("title", "")),
            "报告类型": report_type.get("name", ""),
            "报告类型代码": report_type.get("code", ""),

            # 内容信息
            "报告摘要": str(report.get("summary", "")),
            "报告内容": self._clean_html_content(report.get("content", "")),
            "关键词": str(report.get("keywords", "")),

            # 时间信息
            "发布时间": str(report.get("publishTime", "")),
            "创建时间": str(report.get("createTime", "")),
            "爬取时间": timestamp.strftime("%Y-%m-%d %H:%M:%S"),

            # 其他信息
            "来源": str(report.get("source", "")),
            "作者": str(report.get("author", "")),
            "阅读量": int(report.get("readCount", 0) or 0),

            # 分类信息
            "数据类型": "深度分析",
            "分析领域": str(report.get("category", ""))
        }
    
    def _clean_html_content(self, html_content: str) -> str:
        """清理HTML内容，提取纯文本"""
        try:
            if not html_content:
                return ""
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 移除脚本和样式标签
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 获取纯文本
            text = soup.get_text()
            
            # 清理多余的空白字符
            text = re.sub(r'\s+', ' ', text).strip()
            
            # 限制长度
            if len(text) > 5000:
                text = text[:5000] + "..."
            
            return text
            
        except Exception as e:
            logger.error(f"清理HTML内容失败: {e}")
            return str(html_content)[:1000] if html_content else ""
    
    def _save_reports(self, reports: List[Dict]) -> int:
        """保存报告数据到CSV文件"""
        try:
            if not reports:
                return 0
            
            # 创建报告专用的CSV文件
            reports_file = self.data_manager.data_dir / "analysis_reports.csv"
            
            import pandas as pd
            
            # 转换为DataFrame
            df = pd.DataFrame(reports)
            
            # 如果文件已存在，合并数据
            if reports_file.exists() and reports_file.stat().st_size > 0:
                existing_df = pd.read_csv(reports_file, encoding='utf-8-sig')
                
                # 合并数据
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                
                # 去重（基于报告ID）
                if '报告ID' in combined_df.columns:
                    combined_df = combined_df.drop_duplicates(subset=['报告ID'], keep='last')
                
                df = combined_df
            
            # 保存到CSV
            df.to_csv(reports_file, index=False, encoding='utf-8-sig')
            
            logger.info(f"成功保存 {len(reports)} 篇报告，CSV文件总记录数: {len(df)}")
            
            return len(reports)
            
        except Exception as e:
            logger.error(f"保存报告数据失败: {e}")
            return 0
    
    def _make_request(self, method: str, url: str, **kwargs) -> Optional[Dict]:
        """发送HTTP请求"""
        for attempt in range(self.retry_times):
            try:
                # 设置默认参数
                request_kwargs = {
                    'headers': self.headers,
                    'timeout': self.timeout,
                    'verify': False,  # 禁用SSL验证
                    **kwargs
                }
                
                response = requests.request(method, url, **request_kwargs)
                
                # 检查响应状态
                if response.status_code != 200:
                    raise requests.exceptions.RequestException(f"HTTP {response.status_code}")
                
                # 检查响应内容
                if not response.content:
                    raise ValueError("Empty response received")
                
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{self.retry_times}): {e}")
                if attempt < self.retry_times - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    logger.error(f"请求最终失败: {url}")
                    return None
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}")
                return None
            except Exception as e:
                logger.error(f"请求出现未知错误: {e}")
                return None
    
    def get_status(self) -> Dict[str, Any]:
        """获取爬虫状态"""
        status = {
            'status': '运行中' if self.is_running else '已停止',
            'is_running': self.is_running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'running_time': str(datetime.now() - self.start_time) if self.start_time else None,
            'crawled_count': self.crawled_count,
            'error_count': self.error_count,
            'report_types': len(self.report_types)
        }
        
        return status
    
    def crawl_once(self) -> List[Dict]:
        """执行一次报告爬取（用于测试）"""
        logger.info("执行单次报告爬取...")
        
        try:
            all_reports = self._crawl_all_reports()
            
            if all_reports:
                saved_count = self._save_reports(all_reports)
                logger.info(f"单次报告爬取完成，获取 {len(all_reports)} 篇报告，已保存 {saved_count} 篇")
            else:
                logger.warning("单次报告爬取未获取到数据")
            
            return all_reports
            
        except Exception as e:
            logger.error(f"单次报告爬取失败: {e}")
            return []

# 全局报告爬虫实例
report_crawler = ReportCrawler()

def get_report_crawler():
    """获取报告爬虫实例"""
    return report_crawler
