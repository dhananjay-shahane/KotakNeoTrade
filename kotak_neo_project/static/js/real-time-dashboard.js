// Real-time Dashboard Updates - No Page Refresh System
function RealTimeDashboard() {
    this.refreshInterval = null;
    this.isRefreshing = false;
    this.init();
}

RealTimeDashboard.prototype.init = function() {
    this.setupEventListeners();
    this.startAutoRefresh();
    this.addCustomCSS();
    console.log('Real-time dashboard initialized');
};

RealTimeDashboard.prototype.addCustomCSS = function() {
    var style = document.createElement('style');
    style.textContent = 
        '.data-updated {' +
        '    animation: dataUpdate 1.5s ease-in-out;' +
        '}' +
        '@keyframes dataUpdate {' +
        '    0% { background-color: rgba(40, 167, 69, 0.3); }' +
        '    50% { background-color: rgba(40, 167, 69, 0.1); }' +
        '    100% { background-color: transparent; }' +
        '}' +
        '.refresh-loading {' +
        '    opacity: 0.7;' +
        '    pointer-events: none;' +
        '}' +
        '.refresh-loading::after {' +
        '    content: "";' +
        '    position: absolute;' +
        '    top: 50%;' +
        '    left: 50%;' +
        '    transform: translate(-50%, -50%);' +
        '    width: 20px;' +
        '    height: 20px;' +
        '    border: 2px solid #f3f3f3;' +
        '    border-top: 2px solid #007bff;' +
        '    border-radius: 50%;' +
        '    animation: spin 1s linear infinite;' +
        '}' +
        '@keyframes spin {' +
        '    0% { transform: translate(-50%, -50%) rotate(0deg); }' +
        '    100% { transform: translate(-50%, -50%) rotate(360deg); }' +
        '}';
    
    document.head.appendChild(style);
};

RealTimeDashboard.prototype.setupEventListeners = function() {
    var self = this;
    
    // Refresh buttons
    var refreshButtons = document.querySelectorAll('.btn-refresh, [data-action="refresh"]');
    for (var i = 0; i < refreshButtons.length; i++) {
        refreshButtons[i].addEventListener('click', function(e) {
            e.preventDefault();
            self.manualRefresh();
        });
    }
    
    // Auto-refresh toggle
    var autoRefreshToggle = document.getElementById('autoRefreshToggle');
    if (autoRefreshToggle) {
        autoRefreshToggle.addEventListener('change', function(e) {
            if (e.target.checked) {
                self.startAutoRefresh();
            } else {
                self.stopAutoRefresh();
            }
        });
    }
    
    // Refresh interval selector
    var refreshIntervalSelect = document.getElementById('refreshInterval');
    if (refreshIntervalSelect) {
        refreshIntervalSelect.addEventListener('change', function(e) {
            var interval = parseInt(e.target.value) * 1000;
            self.setRefreshInterval(interval);
        });
    }
};

RealTimeDashboard.prototype.startAutoRefresh = function() {
    var self = this;
    this.stopAutoRefresh();
    
    this.refreshInterval = setInterval(function() {
        self.refreshData();
    }, 30000); // 30 seconds default
};

RealTimeDashboard.prototype.stopAutoRefresh = function() {
    if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
        this.refreshInterval = null;
    }
};

RealTimeDashboard.prototype.setRefreshInterval = function(interval) {
    this.stopAutoRefresh();
    var self = this;
    
    this.refreshInterval = setInterval(function() {
        self.refreshData();
    }, interval);
};

RealTimeDashboard.prototype.manualRefresh = function() {
    this.refreshData(true);
};

RealTimeDashboard.prototype.refreshData = function(isManual) {
    if (this.isRefreshing && !isManual) {
        return;
    }
    
    var self = this;
    this.isRefreshing = true;
    
    // Show loading state
    this.showLoadingState(true);
    
    // Fetch dashboard data
    fetch('/api/dashboard-data')
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            self.updateDashboardData(data);
            self.showUpdateAnimation();
        })
        .catch(function(error) {
            console.warn('Dashboard refresh failed:', error);
            self.showError('Failed to refresh data');
        })
        .finally(function() {
            self.isRefreshing = false;
            self.showLoadingState(false);
        });
};

RealTimeDashboard.prototype.updateDashboardData = function(data) {
    if (data.positions) {
        this.updatePositionsTable(data.positions);
    }
    
    if (data.holdings) {
        this.updateHoldingsTable(data.holdings);
    }
    
    if (data.summary) {
        this.updateSummaryCards(data.summary);
    }
    
    if (data.recent_orders) {
        this.updateRecentOrders(data.recent_orders);
    }
};

RealTimeDashboard.prototype.updatePositionsTable = function(positions) {
    var tbody = document.querySelector('#positionsTable tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    for (var i = 0; i < positions.length; i++) {
        var position = positions[i];
        var row = this.createPositionRow(position);
        tbody.appendChild(row);
    }
};

RealTimeDashboard.prototype.createPositionRow = function(position) {
    var row = document.createElement('tr');
    var pnlClass = (position.pnl || 0) >= 0 ? 'text-success' : 'text-danger';
    
    row.innerHTML = 
        '<td>' + (position.symbol || '') + '</td>' +
        '<td>' + (position.quantity || 0) + '</td>' +
        '<td>₹' + (position.avg_price || 0).toFixed(2) + '</td>' +
        '<td>₹' + (position.ltp || 0).toFixed(2) + '</td>' +
        '<td class="' + pnlClass + '">₹' + (position.pnl || 0).toFixed(2) + '</td>';
    
    return row;
};

RealTimeDashboard.prototype.updateHoldingsTable = function(holdings) {
    var tbody = document.querySelector('#holdingsTable tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    for (var i = 0; i < holdings.length; i++) {
        var holding = holdings[i];
        var row = this.createHoldingRow(holding);
        tbody.appendChild(row);
    }
};

RealTimeDashboard.prototype.createHoldingRow = function(holding) {
    var row = document.createElement('tr');
    var pnlClass = (holding.pnl || 0) >= 0 ? 'text-success' : 'text-danger';
    
    row.innerHTML = 
        '<td>' + (holding.symbol || '') + '</td>' +
        '<td>' + (holding.quantity || 0) + '</td>' +
        '<td>₹' + (holding.avg_price || 0).toFixed(2) + '</td>' +
        '<td>₹' + (holding.ltp || 0).toFixed(2) + '</td>' +
        '<td class="' + pnlClass + '">₹' + (holding.pnl || 0).toFixed(2) + '</td>';
    
    return row;
};

RealTimeDashboard.prototype.updateSummaryCards = function(summary) {
    var elements = {
        totalPnl: document.querySelector('#totalPnl'),
        totalValue: document.querySelector('#totalValue'),
        todayPnl: document.querySelector('#todayPnl'),
        totalPositions: document.querySelector('#totalPositions'),
        totalHoldings: document.querySelector('#totalHoldings')
    };
    
    for (var key in elements) {
        if (elements[key] && summary[key] !== undefined) {
            if (key.includes('Pnl')) {
                elements[key].textContent = '₹' + summary[key].toFixed(2);
                elements[key].className = summary[key] >= 0 ? 'text-success' : 'text-danger';
            } else if (key.includes('Value')) {
                elements[key].textContent = '₹' + summary[key].toFixed(2);
            } else {
                elements[key].textContent = summary[key];
            }
        }
    }
};

RealTimeDashboard.prototype.updateRecentOrders = function(orders) {
    var tbody = document.querySelector('#recentOrdersTable tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    for (var i = 0; i < Math.min(orders.length, 10); i++) {
        var order = orders[i];
        var row = this.createOrderRow(order);
        tbody.appendChild(row);
    }
};

RealTimeDashboard.prototype.createOrderRow = function(order) {
    var row = document.createElement('tr');
    var statusClass = order.status === 'COMPLETE' ? 'text-success' : 
                     order.status === 'REJECTED' ? 'text-danger' : 'text-warning';
    
    row.innerHTML = 
        '<td>' + (order.symbol || '') + '</td>' +
        '<td>' + (order.side || '') + '</td>' +
        '<td>' + (order.quantity || 0) + '</td>' +
        '<td>₹' + (order.price || 0).toFixed(2) + '</td>' +
        '<td class="' + statusClass + '">' + (order.status || '') + '</td>';
    
    return row;
};

RealTimeDashboard.prototype.showLoadingState = function(show) {
    var containers = document.querySelectorAll('.data-container, .card-body');
    for (var i = 0; i < containers.length; i++) {
        if (show) {
            containers[i].classList.add('refresh-loading');
        } else {
            containers[i].classList.remove('refresh-loading');
        }
    }
};

RealTimeDashboard.prototype.showUpdateAnimation = function() {
    var containers = document.querySelectorAll('.data-container, .card-body');
    for (var i = 0; i < containers.length; i++) {
        containers[i].classList.add('data-updated');
        setTimeout(function(container) {
            container.classList.remove('data-updated');
        }, 1500, containers[i]);
    }
};

RealTimeDashboard.prototype.showError = function(message) {
    var alertHtml = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' +
        message +
        '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
        '</div>';
    
    var container = document.querySelector('.container, .container-fluid');
    if (container) {
        container.insertAdjacentHTML('afterbegin', alertHtml);
        
        setTimeout(function() {
            var alert = document.querySelector('.alert-danger');
            if (alert) {
                alert.remove();
            }
        }, 5000);
    }
};

RealTimeDashboard.prototype.destroy = function() {
    this.stopAutoRefresh();
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (typeof window.realTimeDashboard === 'undefined') {
        window.realTimeDashboard = new RealTimeDashboard();
    }
});

// Fallback initialization
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    if (typeof window.realTimeDashboard === 'undefined') {
        window.realTimeDashboard = new RealTimeDashboard();
    }
}