/**
 * 农产品市场价格管理平台 - 仪表盘
 */

class Dashboard {
    constructor() {
        this.apiBase = '/api';
        this.charts = {};
        this.dashboardData = null;
        this.init();
    }

    async init() {
        try {
            this.showLoading(true);
            await this.loadDashboardData();
            this.initializeCharts();
            this.updateOverviewCards();
            this.updateSummary();
            this.showLoading(false);
        } catch (error) {
            console.error('初始化仪表盘失败:', error);
            this.showMessage('初始化仪表盘失败', 'error');
            this.showLoading(false);
        }
    }

    async refresh() {
        try {
            this.showLoading(true);
            await this.loadDashboardData();
            this.updateOverviewCards();
            this.updateSummary();

            // 更新图表数据
            this.updatePriceIndexChart();
            this.updateCategoryChart();
            this.updateProductsChart();
            this.updateVolatilityAnalysis();

            this.showLoading(false);
            this.showMessage('数据刷新成功', 'success');
        } catch (error) {
            console.error('刷新数据失败:', error);
            this.showMessage('刷新数据失败', 'error');
            this.showLoading(false);
        }
    }

    async loadDashboardData() {
        try {
            const response = await fetch(`${this.apiBase}/dashboard/data`);
            const result = await response.json();

            if (result.success) {
                this.dashboardData = result.data;
                console.log('仪表盘数据加载成功:', this.dashboardData);
            } else {
                throw new Error(result.error || '加载数据失败');
            }
        } catch (error) {
            console.error('加载仪表盘数据失败:', error);
            throw error;
        }
    }

    initializeCharts() {
        this.initPriceIndexChart();
        this.initCategoryChart();
        this.initProductsChart();
        this.updateVolatilityAnalysis();
    }

    initPriceIndexChart() {
        const ctx = document.getElementById('priceIndexChart').getContext('2d');
        const priceIndexData = this.dashboardData.price_index_trend || [];

        const labels = priceIndexData.map(item => this.formatDate(item.date));
        const priceIndex200 = priceIndexData.map(item => item.price_index_200);
        const basketIndex = priceIndexData.map(item => item.basket_index);

        this.charts.priceIndex = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '农产品批发价格200指数',
                        data: priceIndex200,
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: '菜篮子产品批发价格指数',
                        data: basketIndex,
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: '日期'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: '指数'
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    }

    initCategoryChart() {
        const ctx = document.getElementById('categoryChart').getContext('2d');
        const categoryData = this.dashboardData.category_price_trends || {};

        // 默认显示蔬菜数据
        const vegetableData = categoryData.vegetables || [];
        const labels = vegetableData.map(item => this.formatDate(item.date));
        const prices = vegetableData.map(item => item.avg_price);

        this.charts.category = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '蔬菜平均价格 (元/公斤)',
                    data: prices,
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
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
                        position: 'top',
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: '日期'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: '价格 (元/公斤)'
                        }
                    }
                }
            }
        });
    }

    initProductsChart() {
        const ctx = document.getElementById('productsChart').getContext('2d');
        const productsData = this.dashboardData.key_products_trends || {};

        const datasets = [];
        const colors = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1'];
        let colorIndex = 0;

        // 获取所有产品的最新价格
        const latestPrices = [];
        const productNames = [];

        Object.keys(productsData).forEach(productName => {
            const productTrend = productsData[productName];
            if (productTrend && productTrend.length > 0) {
                const latestData = productTrend[productTrend.length - 1];
                productNames.push(productName);
                latestPrices.push(latestData.price);
            }
        });

        this.charts.products = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: productNames,
                datasets: [{
                    label: '最新价格 (元/公斤)',
                    data: latestPrices,
                    backgroundColor: colors.slice(0, productNames.length),
                    borderColor: colors.slice(0, productNames.length),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: '产品'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: '价格 (元/公斤)'
                        }
                    }
                }
            }
        });
    }

    updateCategoryChart() {
        const selectedCategory = document.getElementById('categorySelect').value;
        const categoryData = this.dashboardData.category_price_trends || {};

        if (selectedCategory === 'all') {
            // 显示所有类别的对比
            this.updateAllCategoriesChart();
        } else {
            // 显示单个类别的趋势
            this.updateSingleCategoryChart(selectedCategory, categoryData);
        }
    }

    updateAllCategoriesChart() {
        const categoryData = this.dashboardData.category_price_trends || {};
        const datasets = [];
        const colors = {
            vegetables: '#28a745',
            fruits: '#ffc107',
            meat: '#dc3545',
            aquatic: '#17a2b8'
        };
        const labels = {
            vegetables: '蔬菜',
            fruits: '水果',
            meat: '畜产品',
            aquatic: '水产品'
        };

        // 获取最长的日期序列
        let allDates = [];
        Object.values(categoryData).forEach(data => {
            if (data && data.length > 0) {
                const dates = data.map(item => item.date);
                allDates = [...new Set([...allDates, ...dates])].sort();
            }
        });

        Object.keys(categoryData).forEach(category => {
            const data = categoryData[category] || [];
            if (data.length > 0) {
                const prices = allDates.map(date => {
                    const item = data.find(d => d.date === date);
                    return item ? item.avg_price : null;
                });

                datasets.push({
                    label: labels[category] || category,
                    data: prices,
                    borderColor: colors[category] || '#6c757d',
                    backgroundColor: `${colors[category] || '#6c757d'}20`,
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4
                });
            }
        });

        this.charts.category.data.labels = allDates.map(date => this.formatDate(date));
        this.charts.category.data.datasets = datasets;
        this.charts.category.update();
    }

    updateSingleCategoryChart(category, categoryData) {
        const data = categoryData[category] || [];
        const labels = data.map(item => this.formatDate(item.date));
        const prices = data.map(item => item.avg_price);

        const categoryLabels = {
            vegetables: '蔬菜平均价格',
            fruits: '水果平均价格',
            meat: '畜产品价格',
            aquatic: '水产品价格'
        };

        const categoryColors = {
            vegetables: '#28a745',
            fruits: '#ffc107',
            meat: '#dc3545',
            aquatic: '#17a2b8'
        };

        this.charts.category.data.labels = labels;
        this.charts.category.data.datasets = [{
            label: `${categoryLabels[category] || category} (元/公斤)`,
            data: prices,
            borderColor: categoryColors[category] || '#007bff',
            backgroundColor: `${categoryColors[category] || '#007bff'}20`,
            borderWidth: 2,
            fill: true,
            tension: 0.4
        }];
        this.charts.category.update();
    }

    // 更新图表数据的方法
    updatePriceIndexChart() {
        if (!this.charts.priceIndex || !this.dashboardData) return;

        const priceIndexData = this.dashboardData.price_index_trend || [];
        const labels = priceIndexData.map(item => this.formatDate(item.date));
        const priceIndex200 = priceIndexData.map(item => item.price_index_200);
        const basketIndex = priceIndexData.map(item => item.basket_index);

        this.charts.priceIndex.data.labels = labels;
        this.charts.priceIndex.data.datasets[0].data = priceIndex200;
        this.charts.priceIndex.data.datasets[1].data = basketIndex;
        this.charts.priceIndex.update();
    }

    updateProductsChart() {
        if (!this.charts.products || !this.dashboardData) return;

        const productsData = this.dashboardData.key_products || [];
        const labels = productsData.map(item => item.product);
        const prices = productsData.map(item => item.latest_price);

        this.charts.products.data.labels = labels;
        this.charts.products.data.datasets[0].data = prices;
        this.charts.products.update();
    }

    updateVolatilityAnalysis() {
        const volatilityData = this.dashboardData.volatility_analysis || {};
        const topGainers = volatilityData.top_gainers || [];
        const topLosers = volatilityData.top_losers || [];

        // 更新涨幅前五
        const gainersContainer = document.getElementById('topGainers');
        gainersContainer.innerHTML = '';
        
        // 获取最新的涨幅数据
        const latestGainers = this.getLatestVolatilityData(topGainers, 5);
        latestGainers.forEach(item => {
            const div = document.createElement('div');
            div.className = 'volatility-item';
            div.innerHTML = `
                <span class="product-name">${item.product}</span>
                <span class="change-rate positive">+${item.change_rate.toFixed(1)}%</span>
            `;
            gainersContainer.appendChild(div);
        });

        // 更新跌幅前五
        const losersContainer = document.getElementById('topLosers');
        losersContainer.innerHTML = '';
        
        const latestLosers = this.getLatestVolatilityData(topLosers, 5);
        latestLosers.forEach(item => {
            const div = document.createElement('div');
            div.className = 'volatility-item';
            div.innerHTML = `
                <span class="product-name">${item.product}</span>
                <span class="change-rate negative">${item.change_rate.toFixed(1)}%</span>
            `;
            losersContainer.appendChild(div);
        });
    }

    getLatestVolatilityData(data, limit) {
        if (!data || data.length === 0) return [];
        
        // 按日期分组，获取最新日期的数据
        const groupedByDate = {};
        data.forEach(item => {
            if (!groupedByDate[item.date]) {
                groupedByDate[item.date] = [];
            }
            groupedByDate[item.date].push(item);
        });

        // 获取最新日期
        const latestDate = Object.keys(groupedByDate).sort().pop();
        const latestData = groupedByDate[latestDate] || [];

        // 按变化幅度排序并取前N个
        return latestData
            .sort((a, b) => Math.abs(b.change_rate) - Math.abs(a.change_rate))
            .slice(0, limit);
    }

    updateOverviewCards() {
        try {
            // 更新价格指数卡片
            const priceIndexData = this.dashboardData.price_index_trend || [];
            if (priceIndexData.length > 0) {
                const latest = priceIndexData[priceIndexData.length - 1];
                const previous = priceIndexData.length > 1 ? priceIndexData[priceIndexData.length - 2] : null;

                this.animateNumber('latestPriceIndex', latest.price_index_200, 2);

                if (previous) {
                    const change = latest.price_index_200 - previous.price_index_200;
                    const changeElement = document.getElementById('priceIndexChange');
                    changeElement.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}`;
                    changeElement.className = `metric-change ${change >= 0 ? 'positive' : 'negative'}`;
                }
            }

            // 更新蔬菜价格卡片
            const vegetableData = this.dashboardData.category_price_trends?.vegetables || [];
            if (vegetableData.length > 0) {
                const latest = vegetableData[vegetableData.length - 1];
                this.animatePrice('latestVegPrice', latest.avg_price);

                const changeElement = document.getElementById('vegPriceChange');
                changeElement.textContent = `${latest.change_rate >= 0 ? '+' : ''}${latest.change_rate.toFixed(1)}%`;
                changeElement.className = `metric-change ${latest.change_rate >= 0 ? 'positive' : 'negative'}`;
            }

            // 更新水果价格卡片
            const fruitData = this.dashboardData.category_price_trends?.fruits || [];
            if (fruitData.length > 0) {
                const latest = fruitData[fruitData.length - 1];
                this.animatePrice('latestFruitPrice', latest.avg_price);

                const changeElement = document.getElementById('fruitPriceChange');
                changeElement.textContent = `${latest.change_rate >= 0 ? '+' : ''}${latest.change_rate.toFixed(1)}%`;
                changeElement.className = `metric-change ${latest.change_rate >= 0 ? 'positive' : 'negative'}`;
            }

            // 更新猪肉价格卡片
            const meatData = this.dashboardData.category_price_trends?.meat || [];
            if (meatData.length > 0) {
                const latest = meatData[meatData.length - 1];
                this.animatePrice('latestMeatPrice', latest.avg_price);

                const changeElement = document.getElementById('meatPriceChange');
                changeElement.textContent = `${latest.change_rate >= 0 ? '+' : ''}${latest.change_rate.toFixed(1)}%`;
                changeElement.className = `metric-change ${latest.change_rate >= 0 ? 'positive' : 'negative'}`;
            }

        } catch (error) {
            console.error('更新概览卡片失败:', error);
        }
    }

    // 数字动画效果
    animateNumber(elementId, targetValue, decimals = 0) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const startValue = 0;
        const duration = 1500; // 1.5秒
        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // 使用缓动函数
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            const currentValue = startValue + (targetValue - startValue) * easeOutQuart;

            element.textContent = currentValue.toFixed(decimals);

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    // 价格动画效果
    animatePrice(elementId, targetValue) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const startValue = 0;
        const duration = 1500;
        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            const currentValue = startValue + (targetValue - startValue) * easeOutQuart;

            element.textContent = `${currentValue.toFixed(2)} 元/公斤`;

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    updateSummary() {
        try {
            const summary = this.dashboardData.market_summary || {};

            // 更新日期范围
            if (summary.date_range) {
                const dateRange = `${this.formatDate(summary.date_range.start)} 至 ${this.formatDate(summary.date_range.end)}`;
                document.getElementById('dateRange').textContent = dateRange;
            }

            // 更新报告总数
            if (summary.total_reports) {
                document.getElementById('totalReports').textContent = `${summary.total_reports} 篇`;
            }

            // 更新最后更新时间
            document.getElementById('lastUpdate').textContent = new Date().toLocaleString('zh-CN');

        } catch (error) {
            console.error('更新摘要信息失败:', error);
        }
    }

    async refreshChart(chartType) {
        try {
            this.showLoading(true);
            await this.loadDashboardData();

            switch (chartType) {
                case 'priceIndex':
                    this.charts.priceIndex.destroy();
                    this.initPriceIndexChart();
                    break;
                case 'category':
                    this.charts.category.destroy();
                    this.initCategoryChart();
                    this.updateCategoryChart();
                    break;
                case 'products':
                    this.charts.products.destroy();
                    this.initProductsChart();
                    break;
                case 'volatility':
                    this.updateVolatilityAnalysis();
                    break;
            }

            this.updateOverviewCards();
            this.updateSummary();
            this.showMessage('图表已刷新', 'success');

        } catch (error) {
            console.error('刷新图表失败:', error);
            this.showMessage('刷新图表失败', 'error');
        } finally {
            this.showLoading(false);
        }
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

    showLoading(show) {
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = show ? 'flex' : 'none';
        }
    }

    showMessage(message, type = 'info', duration = 3000) {
        const container = document.getElementById('messageContainer');
        if (!container) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${type}`;

        const icon = type === 'success' ? 'check-circle' :
                    type === 'error' ? 'exclamation-circle' :
                    type === 'warning' ? 'exclamation-triangle' : 'info-circle';

        messageDiv.innerHTML = `
            <i class="fas fa-${icon}"></i>
            <span>${message}</span>
        `;

        container.appendChild(messageDiv);

        // 自动移除消息
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.parentNode.removeChild(messageDiv);
            }
        }, duration);
    }
}

// 全局函数
function refreshChart(chartType) {
    if (window.dashboard) {
        window.dashboard.refreshChart(chartType);
    }
}

function updateCategoryChart() {
    if (window.dashboard) {
        window.dashboard.updateCategoryChart();
    }
}

// 全局刷新函数
function refreshDashboard() {
    if (window.dashboard) {
        window.dashboard.refresh();
    }
}

// 初始化仪表盘
document.addEventListener('DOMContentLoaded', function() {
    window.dashboard = new Dashboard();
});
