// 农产品市场价格管理平台 - 前端JavaScript

class MarketPlatform {
    constructor() {
        this.apiBase = '/api';
        this.currentData = [];
        this.currentReports = [];
        this.currentSection = 'dashboard';
        this.currentReportData = null;
        this.charts = {};
        this.currentTimeRange = 30; // 默认30天
        this.currentReportPage = 1;
        this.reportPageSize = 10;
        this.totalReportPages = 0;
        this.currentReportType = 'all'; // 当前报告类型
        this.dashboardData = null; // 仪表盘数据
        this.previewChart = null; // 预览图表
        this.init();
    }

    async init() {
        console.log('🚀 农产品市场价格管理平台初始化中...');

        // 绑定事件
        this.bindEvents();

        // 初始化侧边栏
        this.initSidebar();

        // 加载初始数据
        await this.loadInitialData();

        console.log('✅ 平台初始化完成');
    }

    initSidebar() {
        // 设置默认激活的导航项
        this.showSection('dashboard');
    }

    bindEvents() {
        // 搜索表单提交
        const searchForm = document.getElementById('searchForm');
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.searchData();
            });
        }

        // 定时刷新数据
        setInterval(() => {
            this.refreshStats();
        }, 30000); // 30秒刷新一次统计数据
    }

    async loadInitialData() {
        try {
            // 加载统计数据
            await this.refreshStats();

            // 加载下拉选项
            await this.loadDropdownOptions();

            // 加载最新数据
            await this.loadLatestData();

            // 加载最新报告
            await this.loadLatestReports();

            // 加载报告统计信息
            await this.loadReportStats();

            // 加载仪表盘数据
            await this.loadDashboardData();

        } catch (error) {
            console.error('加载初始数据失败:', error);
            this.showMessage('加载数据失败，请刷新页面重试', 'error');
        }
    }

    async refreshStats() {
        try {
            const response = await fetch(`${this.apiBase}/stats`);
            const result = await response.json();
            
            if (result.success) {
                this.updateStatsDisplay(result.data);
            }
        } catch (error) {
            console.error('刷新统计数据失败:', error);
        }
    }

    updateStatsDisplay(data) {
        const { data_stats, crawler_status } = data;
        
        // 更新统计卡片
        this.updateElement('totalRecords', data_stats?.total_records || 0);
        this.updateElement('totalMarkets', data_stats?.total_markets || 0);
        this.updateElement('totalVarieties', data_stats?.total_varieties || 0);
        this.updateElement('crawlerStatus', crawler_status?.status || '未知');
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    async loadDropdownOptions() {
        try {
            // 加载省份选项
            const provincesResponse = await fetch(`${this.apiBase}/data/provinces`);
            const provincesResult = await provincesResponse.json();
            if (provincesResult.success) {
                this.populateSelect('province', provincesResult.data);
            }

            // 加载品种选项
            const varietiesResponse = await fetch(`${this.apiBase}/data/varieties`);
            const varietiesResult = await varietiesResponse.json();
            if (varietiesResult.success) {
                this.populateSelect('variety', varietiesResult.data);
            }

            // 加载市场选项
            const marketsResponse = await fetch(`${this.apiBase}/data/markets`);
            const marketsResult = await marketsResponse.json();
            if (marketsResult.success) {
                this.populateSelect('market', marketsResult.data);
            }

        } catch (error) {
            console.error('加载下拉选项失败:', error);
        }
    }

    populateSelect(selectId, options) {
        const select = document.getElementById(selectId);
        if (!select) return;

        // 清空现有选项（保留第一个默认选项）
        const firstOption = select.firstElementChild;
        select.innerHTML = '';
        if (firstOption) {
            select.appendChild(firstOption);
        }

        // 添加新选项
        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option;
            optionElement.textContent = option;
            select.appendChild(optionElement);
        });
    }

    async loadLatestData() {
        try {
            this.showLoading(true);
            
            const response = await fetch(`${this.apiBase}/data/latest?limit=100`);
            const result = await response.json();
            
            if (result.success) {
                this.currentData = result.data;
                this.displayData(result.data);
                this.updateDataCount(result.count);
            } else {
                this.showMessage('加载数据失败', 'error');
            }
        } catch (error) {
            console.error('加载最新数据失败:', error);
            this.showMessage('网络错误，请检查连接', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async searchData() {
        try {
            this.showLoading(true);
            
            const formData = new FormData(document.getElementById('searchForm'));
            const searchParams = Object.fromEntries(formData.entries());
            
            // 移除空值
            Object.keys(searchParams).forEach(key => {
                if (!searchParams[key]) {
                    delete searchParams[key];
                }
            });

            const response = await fetch(`${this.apiBase}/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(searchParams)
            });

            const result = await response.json();
            
            if (result.success) {
                this.currentData = result.data;
                this.displayData(result.data);
                this.updateDataCount(result.count);
                this.showMessage(`搜索完成，找到 ${result.count} 条记录`, 'success');
            } else {
                this.showMessage('搜索失败', 'error');
            }
        } catch (error) {
            console.error('搜索数据失败:', error);
            this.showMessage('搜索出错，请重试', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    displayData(data) {
        const tbody = document.getElementById('dataTableBody');
        if (!tbody) return;

        if (!data || data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="no-data">暂无数据</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(item => `
            <tr>
                <td>${item.省份 || item.province || '-'}</td>
                <td>${item.市场名称 || item.market_name || '-'}</td>
                <td>${item.品种名称 || item.variety_name || '-'}</td>
                <td>${item.最低价 || item.min_price || '-'}</td>
                <td>${item.平均价 || item.avg_price || '-'}</td>
                <td>${item.最高价 || item.max_price || '-'}</td>
                <td>${item.单位 || item.unit || '-'}</td>
                <td>${item.交易日期 || item.trade_date || '-'}</td>
                <td>${item.更新时间 || item.crawl_time || '-'}</td>
            </tr>
        `).join('');
    }

    updateDataCount(count) {
        const countElement = document.getElementById('dataCount');
        if (countElement) {
            countElement.textContent = `共 ${count} 条记录`;
        }
    }

    async startCrawler() {
        try {
            this.showLoading(true);
            
            const response = await fetch(`${this.apiBase}/crawler/start`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showMessage('爬虫启动成功', 'success');
                setTimeout(() => this.refreshStats(), 2000);
            } else {
                this.showMessage('爬虫启动失败', 'error');
            }
        } catch (error) {
            console.error('启动爬虫失败:', error);
            this.showMessage('启动爬虫出错', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async stopCrawler() {
        try {
            this.showLoading(true);
            
            const response = await fetch(`${this.apiBase}/crawler/stop`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showMessage('爬虫停止成功', 'success');
                setTimeout(() => this.refreshStats(), 2000);
            } else {
                this.showMessage('爬虫停止失败', 'error');
            }
        } catch (error) {
            console.error('停止爬虫失败:', error);
            this.showMessage('停止爬虫出错', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async getCrawlerStatus() {
        try {
            const response = await fetch(`${this.apiBase}/crawler/status`);
            const result = await response.json();
            
            if (result.success) {
                const status = result.data;
                const message = `爬虫状态: ${status.status}\n运行时间: ${status.running_time || '未知'}\n已爬取: ${status.crawled_count || 0} 条数据`;
                alert(message);
            } else {
                this.showMessage('获取状态失败', 'error');
            }
        } catch (error) {
            console.error('获取爬虫状态失败:', error);
            this.showMessage('获取状态出错', 'error');
        }
    }

    async exportData() {
        try {
            this.showLoading(true);
            
            // 构建导出参数
            const formData = new FormData(document.getElementById('searchForm'));
            const params = new URLSearchParams();
            
            for (const [key, value] of formData.entries()) {
                if (value) {
                    params.append(key, value);
                }
            }
            
            const url = `${this.apiBase}/export/csv?${params.toString()}`;
            
            // 创建下载链接
            const link = document.createElement('a');
            link.href = url;
            link.download = `market_data_${new Date().toISOString().slice(0, 10)}.csv`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            this.showMessage('数据导出成功', 'success');
        } catch (error) {
            console.error('导出数据失败:', error);
            this.showMessage('导出数据出错', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    showLoading(show) {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.classList.toggle('hidden', !show);
        }
    }

    showMessage(text, type = 'info') {
        const message = document.getElementById('message');
        const messageText = message?.querySelector('.message-text');
        
        if (message && messageText) {
            messageText.textContent = text;
            message.classList.remove('hidden');
            
            // 3秒后自动隐藏
            setTimeout(() => {
                message.classList.add('hidden');
            }, 3000);
        }
    }

    hideMessage() {
        const message = document.getElementById('message');
        if (message) {
            message.classList.add('hidden');
        }
    }

    // 报告相关方法
    async loadLatestReports(page = 1, reportType = 'all') {
        try {
            const response = await fetch(`${this.apiBase}/reports/latest?limit=${this.reportPageSize}&page=${page}&report_type=${reportType}`);
            const result = await response.json();

            if (result.success) {
                this.displayReports(result.data);
                this.updateReportPagination(result);
                this.updateReportCount(result.total);
                this.updateReportTypeStats(result);
                this.currentReportPage = page;
                this.totalReportPages = result.total_pages;
                this.currentReportType = reportType;
            } else {
                this.showMessage('加载报告失败', 'error');
            }
        } catch (error) {
            console.error('加载报告失败:', error);
            // 不显示错误消息，因为可能还没有报告数据
        }
    }

    async loadReportStats() {
        try {
            const response = await fetch(`${this.apiBase}/reports/stats`);
            const result = await response.json();
            this.updateReportTypeStats(result);
        } catch (error) {
            console.error('加载报告统计失败:', error);
        }
    }

    updateReportTypeStats(stats) {
        // 更新报告类型统计信息
        this.updateElement('totalReportsCount', stats.total || 0);
        this.updateElement('dailyReportsCount', stats.daily_count || 0);
        this.updateElement('monthlyReportsCount', stats.monthly_count || 0);
        this.updateElement('yearlyReportsCount', stats.yearly_count || 0);
    }

    // 切换报告类型
    switchReportType(reportType) {
        this.currentReportType = reportType;
        this.currentReportPage = 1; // 重置到第一页
        this.loadLatestReports(1, reportType);

        // 更新按钮状态
        document.querySelectorAll('.report-type-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-report-type="${reportType}"]`)?.classList.add('active');
    }

    // 仪表盘相关方法
    async loadDashboardData() {
        try {
            const response = await fetch(`${this.apiBase}/dashboard/data`);
            const result = await response.json();

            if (result.success) {
                this.dashboardData = result.data;
                this.updateDashboardPreview();
                console.log('仪表盘数据加载成功:', this.dashboardData);
            } else {
                console.warn('仪表盘数据加载失败:', result.error);
            }
        } catch (error) {
            console.error('加载仪表盘数据失败:', error);
        }
    }

    updateDashboardPreview() {
        if (!this.dashboardData) return;

        try {
            // 更新价格指数
            const priceIndexData = this.dashboardData.price_index_trend || [];
            if (priceIndexData.length > 0) {
                const latest = priceIndexData[priceIndexData.length - 1];
                const previous = priceIndexData.length > 1 ? priceIndexData[priceIndexData.length - 2] : null;

                this.updateElement('dashboardPriceIndex', latest.price_index_200.toFixed(2));

                if (previous) {
                    const change = latest.price_index_200 - previous.price_index_200;
                    const changeElement = document.getElementById('dashboardPriceIndexChange');
                    if (changeElement) {
                        changeElement.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}`;
                        changeElement.className = `metric-change ${change >= 0 ? 'positive' : 'negative'}`;
                    }
                }
            }

            // 更新蔬菜价格
            const vegetableData = this.dashboardData.category_price_trends?.vegetables || [];
            if (vegetableData.length > 0) {
                const latest = vegetableData[vegetableData.length - 1];
                this.updateElement('dashboardVegPrice', `${latest.avg_price.toFixed(2)} 元/公斤`);

                const changeElement = document.getElementById('dashboardVegChange');
                if (changeElement) {
                    changeElement.textContent = `${latest.change_rate >= 0 ? '+' : ''}${latest.change_rate.toFixed(1)}%`;
                    changeElement.className = `metric-change ${latest.change_rate >= 0 ? 'positive' : 'negative'}`;
                }
            }

            // 更新水果价格
            const fruitData = this.dashboardData.category_price_trends?.fruits || [];
            if (fruitData.length > 0) {
                const latest = fruitData[fruitData.length - 1];
                this.updateElement('dashboardFruitPrice', `${latest.avg_price.toFixed(2)} 元/公斤`);

                const changeElement = document.getElementById('dashboardFruitChange');
                if (changeElement) {
                    changeElement.textContent = `${latest.change_rate >= 0 ? '+' : ''}${latest.change_rate.toFixed(1)}%`;
                    changeElement.className = `metric-change ${latest.change_rate >= 0 ? 'positive' : 'negative'}`;
                }
            }

            // 更新猪肉价格
            const meatData = this.dashboardData.category_price_trends?.meat || [];
            if (meatData.length > 0) {
                const latest = meatData[meatData.length - 1];
                this.updateElement('dashboardMeatPrice', `${latest.avg_price.toFixed(2)} 元/公斤`);

                const changeElement = document.getElementById('dashboardMeatChange');
                if (changeElement) {
                    changeElement.textContent = `${latest.change_rate >= 0 ? '+' : ''}${latest.change_rate.toFixed(1)}%`;
                    changeElement.className = `metric-change ${latest.change_rate >= 0 ? 'positive' : 'negative'}`;
                }
            }

            // 更新摘要信息
            const summary = this.dashboardData.market_summary || {};
            if (summary.date_range) {
                const dateRange = `${this.formatDate(summary.date_range.start)} 至 ${this.formatDate(summary.date_range.end)}`;
                this.updateElement('dashboardDateRange', dateRange);
            }
            if (summary.total_reports) {
                this.updateElement('dashboardTotalReports', `${summary.total_reports} 篇`);
            }
            this.updateElement('dashboardLastUpdate', new Date().toLocaleString('zh-CN'));

            // 更新预览图表
            this.updatePreviewChart();

        } catch (error) {
            console.error('更新仪表盘预览失败:', error);
        }
    }

    updatePreviewChart() {
        const canvas = document.getElementById('previewChart');
        if (!canvas || !this.dashboardData) return;

        const ctx = canvas.getContext('2d');
        const priceIndexData = this.dashboardData.price_index_trend || [];

        if (priceIndexData.length === 0) return;

        // 销毁现有图表
        if (this.previewChart) {
            this.previewChart.destroy();
        }

        const labels = priceIndexData.map(item => this.formatDate(item.date));
        const data = priceIndexData.map(item => item.price_index_200);

        this.previewChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '农产品批发价格200指数',
                    data: data,
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        display: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                }
            }
        });
    }

    formatDate(dateString) {
        if (!dateString) return '';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('zh-CN', {
                month: '2-digit',
                day: '2-digit'
            });
        } catch (error) {
            return dateString;
        }
    }

    updateReportPagination(result) {
        const pagination = document.getElementById('reportPagination');
        if (!pagination) return;

        if (result.total_pages <= 1) {
            pagination.classList.add('hidden');
            return;
        }

        pagination.classList.remove('hidden');

        // 更新分页信息
        this.updateElement('reportPageInfo', `第 ${result.page} 页，共 ${result.total_pages} 页`);
        this.updateElement('reportTotalInfo', `总计 ${result.total} 条记录`);

        // 更新按钮状态
        const firstBtn = document.getElementById('reportFirstPage');
        const prevBtn = document.getElementById('reportPrevPage');
        const nextBtn = document.getElementById('reportNextPage');
        const lastBtn = document.getElementById('reportLastPage');

        if (firstBtn) firstBtn.disabled = result.page <= 1;
        if (prevBtn) prevBtn.disabled = result.page <= 1;
        if (nextBtn) nextBtn.disabled = result.page >= result.total_pages;
        if (lastBtn) lastBtn.disabled = result.page >= result.total_pages;

        // 生成页码
        this.generateReportPageNumbers(result.page, result.total_pages);
    }

    generateReportPageNumbers(currentPage, totalPages) {
        const container = document.getElementById('reportPageNumbers');
        if (!container) return;

        let html = '';
        const maxVisible = 5;
        let start = Math.max(1, currentPage - Math.floor(maxVisible / 2));
        let end = Math.min(totalPages, start + maxVisible - 1);

        if (end - start + 1 < maxVisible) {
            start = Math.max(1, end - maxVisible + 1);
        }

        for (let i = start; i <= end; i++) {
            const isActive = i === currentPage;
            html += `<button class="page-number ${isActive ? 'active' : ''}" onclick="goToReportPage(${i})">${i}</button>`;
        }

        container.innerHTML = html;
    }

    goToReportPage(page) {
        if (typeof page === 'string') {
            if (page === 'prev') {
                page = Math.max(1, this.currentReportPage - 1);
            } else if (page === 'next') {
                page = Math.min(this.totalReportPages, this.currentReportPage + 1);
            } else if (page === 'last') {
                page = this.totalReportPages;
            }
        }

        if (page !== this.currentReportPage && page >= 1 && page <= this.totalReportPages) {
            this.loadLatestReports(page, this.currentReportType);
        }
    }

    displayReports(reports) {
        const tbody = document.getElementById('reportTableBody');
        if (!tbody) return;

        if (!reports || reports.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="no-data">暂无报告数据</td></tr>';
            return;
        }

        // 保存当前报告数据
        this.currentReports = reports;

        tbody.innerHTML = reports.map((report, index) => `
            <tr>
                <td title="${report.报告标题 || ''}">${this.truncateText(report.报告标题 || '-', 50)}</td>
                <td>${report.报告类型 || '-'}</td>
                <td>${report.日报日期 || report.发布时间 || '-'}</td>
                <td>${report.来源 || '-'}</td>
                <td>${report.爬取时间 || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-info" onclick="viewReportDetail(${index})">
                        <i class="fas fa-eye"></i> 查看
                    </button>
                </td>
            </tr>
        `).join('');
    }

    // 侧边栏导航功能
    showSection(sectionName) {
        // 隐藏所有section
        const sections = document.querySelectorAll('.content-section');
        sections.forEach(section => {
            section.classList.remove('active');
        });

        // 显示目标section
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.classList.add('active');
        }

        // 更新导航状态
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.classList.remove('active');
        });

        const activeLink = document.querySelector(`[onclick="showSection('${sectionName}')"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }

        // 更新页面标题
        const titles = {
            'dashboard': '数据概览',
            'trends': '趋势仪表板',
            'price-data': '价格数据',
            'reports': '分析报告',
            'crawler-control': '爬虫控制',
            'settings': '系统设置'
        };

        const pageTitle = document.getElementById('pageTitle');
        if (pageTitle) {
            pageTitle.textContent = titles[sectionName] || '农产品平台';
        }

        this.currentSection = sectionName;

        // 根据不同section加载相应数据
        if (sectionName === 'price-data') {
            this.loadLatestData();
        } else if (sectionName === 'reports') {
            this.loadLatestReports();
        } else if (sectionName === 'trends') {
            this.loadTrendsData();
        }
    }

    // 侧边栏切换
    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const mainContent = document.querySelector('.main-content');

        if (window.innerWidth <= 768) {
            // 移动端：显示/隐藏侧边栏
            sidebar.classList.toggle('show');
        } else {
            // 桌面端：收缩/展开
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('expanded');
        }
    }

    // 报告详情查看
    viewReportDetail(reportIndex) {
        if (!this.currentReports || !this.currentReports[reportIndex]) {
            this.showMessage('报告数据不存在', 'error');
            return;
        }

        const report = this.currentReports[reportIndex];
        this.currentReportData = report;

        // 填充模态框数据
        this.populateReportModal(report);

        // 显示模态框
        const modal = document.getElementById('reportModal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    populateReportModal(report) {
        // 基本信息
        this.setElementText('modalReportTitle', report.报告标题 || '未知报告');
        this.setElementText('modalReportType', report.报告类型 || '-');
        this.setElementText('modalReportDate', report.日报日期 || report.发布时间 || '-');
        this.setElementText('modalReportSource', report.来源 || '-');

        // 详细内容
        this.setElementText('modalReportConclusion', report.总体结论 || '-');
        this.setElementText('modalAnimalConclusion', report.畜产品结论 || '-');
        this.setElementText('modalAquaticConclusion', report.水产品结论 || '-');
        this.setElementText('modalVegetablesConclusion', report.蔬菜结论 || '-');
        this.setElementText('modalFruitsConclusion', report.水果结论 || '-');
        this.setElementText('modalIndexConclusion', report.价格指数结论 || '-');
        this.setElementText('modalIncOrReduRange', report.涨跌幅分析 || '-');

        // HTML内容
        const contentElement = document.getElementById('modalReportContent');
        if (contentElement) {
            contentElement.innerHTML = report.报告内容 || report.纯文本内容 || '-';
        }
    }

    setElementText(elementId, text) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = text;
        }
    }

    closeReportModal() {
        const modal = document.getElementById('reportModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    // 刷新当前section的数据
    refreshCurrentSection() {
        switch (this.currentSection) {
            case 'dashboard':
                this.refreshStats();
                break;
            case 'price-data':
                this.loadLatestData();
                break;
            case 'reports':
                this.loadLatestReports();
                break;
            default:
                this.refreshStats();
        }
    }

    // 导出当前section的数据
    exportCurrentData() {
        switch (this.currentSection) {
            case 'price-data':
                this.exportData();
                break;
            case 'reports':
                this.exportReports();
                break;
            default:
                this.exportData();
        }
    }

    // 打印报告
    printReport() {
        if (!this.currentReportData) {
            this.showMessage('没有可打印的报告', 'error');
            return;
        }

        // 创建打印窗口
        const printWindow = window.open('', '_blank');
        const reportHtml = this.generatePrintableReport(this.currentReportData);

        printWindow.document.write(reportHtml);
        printWindow.document.close();
        printWindow.print();
    }

    generatePrintableReport(report) {
        return `
            <!DOCTYPE html>
            <html>
            <head>
                <title>${report.报告标题}</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
                    h1 { color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
                    h2 { color: #555; margin-top: 20px; }
                    .meta { background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
                    .content { margin-bottom: 15px; }
                    @media print { body { margin: 0; } }
                </style>
            </head>
            <body>
                <h1>${report.报告标题}</h1>
                <div class="meta">
                    <p><strong>报告类型：</strong>${report.报告类型}</p>
                    <p><strong>发布时间：</strong>${report.日报日期 || report.发布时间}</p>
                    <p><strong>来源：</strong>${report.来源}</p>
                </div>
                <div class="content">
                    <h2>总体结论</h2>
                    <p>${report.总体结论}</p>
                    <h2>畜产品价格</h2>
                    <p>${report.畜产品结论}</p>
                    <h2>水产品价格</h2>
                    <p>${report.水产品结论}</p>
                    <h2>蔬菜价格</h2>
                    <p>${report.蔬菜结论}</p>
                    <h2>水果价格</h2>
                    <p>${report.水果结论}</p>
                    <h2>价格指数</h2>
                    <p>${report.价格指数结论}</p>
                    <h2>涨跌幅分析</h2>
                    <p>${report.涨跌幅分析}</p>
                </div>
            </body>
            </html>
        `;
    }

    // 导出当前报告
    exportCurrentReport() {
        if (!this.currentReportData) {
            this.showMessage('没有可导出的报告', 'error');
            return;
        }

        // 创建CSV内容
        const csvContent = this.generateReportCSV(this.currentReportData);

        // 下载文件
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `report_${this.currentReportData.报告ID || 'unknown'}_${new Date().toISOString().slice(0, 10)}.csv`;
        link.click();

        this.showMessage('报告导出成功', 'success');
    }

    generateReportCSV(report) {
        const headers = ['字段', '内容'];
        const rows = [
            ['报告标题', report.报告标题 || ''],
            ['报告类型', report.报告类型 || ''],
            ['发布时间', report.日报日期 || report.发布时间 || ''],
            ['来源', report.来源 || ''],
            ['总体结论', report.总体结论 || ''],
            ['畜产品结论', report.畜产品结论 || ''],
            ['水产品结论', report.水产品结论 || ''],
            ['蔬菜结论', report.蔬菜结论 || ''],
            ['水果结论', report.水果结论 || ''],
            ['价格指数结论', report.价格指数结论 || ''],
            ['涨跌幅分析', report.涨跌幅分析 || '']
        ];

        const csvRows = [headers, ...rows];
        return csvRows.map(row =>
            row.map(field => `"${String(field).replace(/"/g, '""')}"`).join(',')
        ).join('\n');
    }

    // 仪表板相关方法
    async loadTrendsData(days = null) {
        try {
            this.showLoading(true);

            const timeRange = days || this.currentTimeRange;
            const response = await fetch(`${this.apiBase}/dashboard/trends?days=${timeRange}`);
            const result = await response.json();

            if (result.success) {
                this.updateMetrics(result.data.key_metrics);
                this.updateCharts(result.data);
                this.updateActivityData(result.data);

                // 更新图表标题
                this.updateChartTitle(result.data.time_range);
            } else {
                this.showMessage('加载趋势数据失败', 'error');
            }
        } catch (error) {
            console.error('加载趋势数据失败:', error);
            this.showMessage('网络错误，请检查连接', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    updateChartTitle(timeRange) {
        const chartTitle = document.querySelector('#trends-section .chart-panel h2');
        if (chartTitle) {
            chartTitle.innerHTML = `<i class="fas fa-chart-line"></i> 价格趋势 (${timeRange})`;
        }
    }

    changeTrendTimeRange() {
        const select = document.getElementById('timeRangeSelect');
        if (select) {
            this.currentTimeRange = parseInt(select.value);
            this.loadTrendsData(this.currentTimeRange);
        }
    }

    updateMetrics(metrics) {
        // 更新关键指标
        this.updateElement('avgPrice', metrics.avg_price ? metrics.avg_price.toFixed(2) : '-');
        this.updateElement('maxPrice', metrics.max_price ? metrics.max_price.toFixed(2) : '-');
        this.updateElement('minPrice', metrics.min_price ? metrics.min_price.toFixed(2) : '-');
        this.updateElement('totalReportsMetric', metrics.total_reports || 0);
        this.updateElement('reportTypes', `${metrics.report_types || 0} 种类型`);

        // 更新价格变化
        const priceChangeElement = document.getElementById('priceChange');
        if (priceChangeElement && metrics.price_change_percent !== undefined) {
            const change = metrics.price_change_percent;
            priceChangeElement.textContent = `${change > 0 ? '+' : ''}${change}%`;
            priceChangeElement.className = `metric-change ${change >= 0 ? 'positive' : 'negative'}`;
        }
    }

    updateCharts(data) {
        // 销毁现有图表
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });
        this.charts = {};

        // 创建价格趋势图
        this.createPriceChart(data.price_trends);

        // 创建报告分布图
        this.createReportDistributionChart(data.report_trends);

        // 创建报告趋势图
        this.createReportTrendChart(data.report_trends);
    }

    createPriceChart(priceData) {
        const ctx = document.getElementById('priceChart');
        if (!ctx || !priceData || priceData.length === 0) return;

        const labels = priceData.map(item => item.交易日期);
        const prices = priceData.map(item => item.平均价);

        this.charts.priceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '平均价格',
                    data: prices,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: '价格 (元/公斤)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: '日期'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    createReportDistributionChart(reportData) {
        const ctx = document.getElementById('reportChart');
        if (!ctx || !reportData || !reportData.type_distribution) return;

        const distribution = reportData.type_distribution;
        const labels = Object.keys(distribution);
        const values = Object.values(distribution);

        this.charts.reportChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: [
                        '#667eea',
                        '#764ba2',
                        '#f093fb',
                        '#f5576c',
                        '#4facfe',
                        '#00f2fe'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    createReportTrendChart(reportData) {
        const ctx = document.getElementById('reportTrendChart');
        if (!ctx || !reportData || !reportData.daily_counts) return;

        const dailyCounts = reportData.daily_counts;
        const labels = dailyCounts.map(item => item.日期);
        const counts = dailyCounts.map(item => item.报告数量);

        this.charts.reportTrendChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '报告数量',
                    data: counts,
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: '#667eea',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '报告数量'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: '日期'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    updateActivityData(data) {
        // 更新活跃度数据
        this.updateElement('activeMarkets', this.currentData ? new Set(this.currentData.map(item => item.市场名称 || item.market_name)).size : '-');
        this.updateElement('monitoredVarieties', this.currentData ? new Set(this.currentData.map(item => item.品种名称 || item.variety_name)).size : '-');
        this.updateElement('lastUpdate', data.last_update ? new Date(data.last_update).toLocaleString() : '-');
        this.updateElement('coverageProvinces', this.currentData ? new Set(this.currentData.map(item => item.省份 || item.province)).size : '-');
    }

    refreshTrends() {
        this.loadTrendsData();
    }

    truncateText(text, maxLength) {
        if (!text || text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    updateReportCount(count) {
        const countElement = document.getElementById('reportCount');
        if (countElement) {
            countElement.textContent = `共 ${count} 篇报告`;
        }
    }

    async startReportCrawler() {
        try {
            this.showLoading(true);

            const response = await fetch(`${this.apiBase}/report-crawler/start`, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                this.showMessage('报告爬虫启动成功', 'success');
            } else {
                this.showMessage('报告爬虫启动失败', 'error');
            }
        } catch (error) {
            console.error('启动报告爬虫失败:', error);
            this.showMessage('启动报告爬虫出错', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async stopReportCrawler() {
        try {
            this.showLoading(true);

            const response = await fetch(`${this.apiBase}/report-crawler/stop`, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                this.showMessage('报告爬虫停止成功', 'success');
            } else {
                this.showMessage('报告爬虫停止失败', 'error');
            }
        } catch (error) {
            console.error('停止报告爬虫失败:', error);
            this.showMessage('停止报告爬虫出错', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async getReportCrawlerStatus() {
        try {
            const response = await fetch(`${this.apiBase}/report-crawler/status`);
            const result = await response.json();

            if (result.success) {
                const status = result.data;
                const message = `报告爬虫状态: ${status.status}\n运行时间: ${status.running_time || '未知'}\n已爬取: ${status.crawled_count || 0} 篇报告\n报告类型: ${status.report_types || 0} 种`;
                alert(message);
            } else {
                this.showMessage('获取报告爬虫状态失败', 'error');
            }
        } catch (error) {
            console.error('获取报告爬虫状态失败:', error);
            this.showMessage('获取状态出错', 'error');
        }
    }

    async crawlReportsOnce() {
        try {
            this.showLoading(true);

            // 获取完整爬取模式选项
            const fullCrawlCheckbox = document.getElementById('fullCrawlMode');
            const fullCrawl = fullCrawlCheckbox ? fullCrawlCheckbox.checked : true;

            const crawlMode = fullCrawl ? '完整爬取' : '快速爬取';

            // 确认对话框
            if (fullCrawl) {
                const confirmed = confirm(
                    '完整爬取模式将爬取所有可用的历史报告数据，可能需要较长时间。\n' +
                    '确定要继续吗？\n\n' +
                    '提示：如果只需要最新数据，可以取消勾选"完整爬取模式"。'
                );
                if (!confirmed) {
                    this.showLoading(false);
                    return;
                }
            }

            const response = await fetch(`${this.apiBase}/report-crawler/crawl-once?full_crawl=${fullCrawl}`, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                this.showMessage(`${result.message}`, 'success');

                // 显示爬取提示
                if (fullCrawl) {
                    this.showMessage(
                        '完整爬取已开始，请耐心等待。可以在控制台查看爬取进度。',
                        'info',
                        8000
                    );
                } else {
                    // 快速爬取5秒后自动刷新报告列表
                    setTimeout(() => {
                        this.loadLatestReports();
                    }, 5000);
                }
            } else {
                this.showMessage(result.message || '爬取失败', 'error');
            }
        } catch (error) {
            console.error('执行报告爬取失败:', error);
            this.showMessage('执行报告爬取出错', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async exportReports() {
        try {
            this.showLoading(true);

            const url = `${this.apiBase}/reports/export`;

            // 创建下载链接
            const link = document.createElement('a');
            link.href = url;
            link.download = `analysis_reports_${new Date().toISOString().slice(0, 10)}.csv`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            this.showMessage('报告数据导出成功', 'success');
        } catch (error) {
            console.error('导出报告数据失败:', error);
            this.showMessage('导出报告数据出错', 'error');
        } finally {
            this.showLoading(false);
        }
    }
}

// 全局函数（供HTML调用）
let platform;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    platform = new MarketPlatform();
});

// 全局函数
function refreshData() {
    if (platform) {
        platform.loadLatestData();
    }
}

function exportData() {
    if (platform) {
        platform.exportData();
    }
}

function startCrawler() {
    if (platform) {
        platform.startCrawler();
    }
}

function stopCrawler() {
    if (platform) {
        platform.stopCrawler();
    }
}

function getCrawlerStatus() {
    if (platform) {
        platform.getCrawlerStatus();
    }
}

function resetSearch() {
    const form = document.getElementById('searchForm');
    if (form) {
        form.reset();
        if (platform) {
            platform.loadLatestData();
        }
    }
}

function hideMessage() {
    if (platform) {
        platform.hideMessage();
    }
}

// 报告相关全局函数
function startReportCrawler() {
    if (platform) {
        platform.startReportCrawler();
    }
}

function stopReportCrawler() {
    if (platform) {
        platform.stopReportCrawler();
    }
}

function getReportCrawlerStatus() {
    if (platform) {
        platform.getReportCrawlerStatus();
    }
}

function crawlReportsOnce() {
    if (platform) {
        platform.crawlReportsOnce();
    }
}

function refreshReports() {
    if (platform) {
        platform.loadLatestReports();
    }
}

function exportReports() {
    if (platform) {
        platform.exportReports();
    }
}

// 侧边栏导航全局函数
function showSection(sectionName) {
    if (platform) {
        platform.showSection(sectionName);
    }
}

function toggleSidebar() {
    if (platform) {
        platform.toggleSidebar();
    }
}

function refreshCurrentSection() {
    if (platform) {
        platform.refreshCurrentSection();
    }
}

function exportCurrentData() {
    if (platform) {
        platform.exportCurrentData();
    }
}

// 报告详情全局函数
function viewReportDetail(reportIndex) {
    if (platform) {
        platform.viewReportDetail(reportIndex);
    }
}

function closeReportModal() {
    if (platform) {
        platform.closeReportModal();
    }
}

function printReport() {
    if (platform) {
        platform.printReport();
    }
}

function exportCurrentReport() {
    if (platform) {
        platform.exportCurrentReport();
    }
}

// 仪表板全局函数
function refreshTrends() {
    if (platform) {
        platform.refreshTrends();
    }
}

function changeTrendTimeRange() {
    if (platform) {
        platform.changeTrendTimeRange();
    }
}

// 报告分页全局函数
function goToReportPage(page) {
    if (platform) {
        platform.goToReportPage(page);
    }
}

// 切换报告类型全局函数
function switchReportType(reportType) {
    if (platform) {
        platform.switchReportType(reportType);
    }
}

// 仪表盘全局函数
function openDashboard() {
    window.open('/static/dashboard.html', '_blank');
}

function refreshDashboardData() {
    if (platform) {
        platform.loadDashboardData();
        platform.showMessage('仪表盘数据已刷新', 'success');
    }
}

// 窗口大小变化时调整侧边栏
window.addEventListener('resize', () => {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.main-content');

    if (window.innerWidth > 768) {
        // 桌面端：移除移动端的show类
        sidebar.classList.remove('show');
    }
});

// 点击模态框背景关闭
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        closeReportModal();
    }
});
