// Dashboard JavaScript functionality for Kotak Neo Trading App

function TradingDashboard() {
    this.isConnected = false;
    this.refreshInterval = null;
    this.wsHandler = null;
    this.init();
}

TradingDashboard.prototype.init = function() {
    this.setupEventListeners();
    this.startAutoRefresh();
    this.initializeWebSocket();
    console.log('Trading Dashboard initialized');
};

TradingDashboard.prototype.setupEventListeners = function() {
    var self = this;
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            self.initializeEventListeners();
        });
    } else {
        this.initializeEventListeners();
    }
};

TradingDashboard.prototype.initializeEventListeners = function() {
    var self = this;
    try {
        var refreshButtons = document.querySelectorAll('[onclick*="refresh"]');
        for (var i = 0; i < refreshButtons.length; i++) {
            var btn = refreshButtons[i];
            if (btn && typeof btn.addEventListener === 'function') {
                btn.addEventListener('click', function(event) {
                    self.handleRefresh(event);
                });
            }
        }

        var orderForms = document.querySelectorAll('form[id*="Order"]');
        for (var j = 0; j < orderForms.length; j++) {
            var form = orderForms[j];
            if (form && typeof form.addEventListener === 'function') {
                form.addEventListener('submit', function(event) {
                    self.handleOrderSubmit(event);
                });
            }
        }

        this.setupPriceUpdateHandlers();
    } catch (error) {
        console.warn('Error initializing event listeners:', error);
    }
};

TradingDashboard.prototype.setupPriceUpdateHandlers = function() {
    var priceElements = document.querySelectorAll('[data-price], .price-ltp, [id*="ltp"]');
    for (var i = 0; i < priceElements.length; i++) {
        priceElements[i].classList.add('live-data');
    }
};

TradingDashboard.prototype.handleRefresh = function(event) {
    var button = event.target.closest('button');
    if (button) {
        button.classList.add('loading');
        setTimeout(function() {
            button.classList.remove('loading');
        }, 1000);
    }
};

TradingDashboard.prototype.handleOrderSubmit = function(event) {
    event.preventDefault();
    var form = event.target;
    var submitBtn = form.querySelector('button[type="submit"]');

    if (submitBtn) {
        submitBtn.classList.add('loading');
        submitBtn.disabled = true;
    }

    setTimeout(function() {
        if (submitBtn) {
            submitBtn.classList.remove('loading');
            submitBtn.disabled = false;
        }
    }, 2000);
};

TradingDashboard.prototype.startAutoRefresh = function() {
    var self = this;
    if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
    }

    this.refreshInterval = setInterval(function() {
        self.refreshData();
    }, 30000);
};

TradingDashboard.prototype.refreshData = function() {
    if (this.isConnected) {
        this.fetchLatestData();
    }
};

TradingDashboard.prototype.fetchLatestData = function() {
    var self = this;
    fetch('/api/dashboard-data')
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            self.updateDashboard(data);
        })
        .catch(function(error) {
            console.warn('Error fetching dashboard data:', error);
        });
};

TradingDashboard.prototype.updateDashboard = function(data) {
    try {
        if (data.positions) {
            this.updatePositionsTable(data.positions);
        }
        if (data.holdings) {
            this.updateHoldingsTable(data.holdings);
        }
        if (data.summary) {
            this.updateSummaryCards(data.summary);
        }
    } catch (error) {
        console.warn('Error updating dashboard:', error);
    }
};

TradingDashboard.prototype.updatePositionsTable = function(positions) {
    var tbody = document.querySelector('#positionsTable tbody');
    if (!tbody) return;

    tbody.innerHTML = '';
    for (var i = 0; i < positions.length; i++) {
        var position = positions[i];
        var row = this.createPositionRow(position);
        tbody.appendChild(row);
    }
};

TradingDashboard.prototype.createPositionRow = function(position) {
    var row = document.createElement('tr');
    row.innerHTML = 
        '<td>' + (position.symbol || '') + '</td>' +
        '<td>' + (position.quantity || 0) + '</td>' +
        '<td>₹' + (position.avg_price || 0).toFixed(2) + '</td>' +
        '<td>₹' + (position.ltp || 0).toFixed(2) + '</td>' +
        '<td class="' + (position.pnl >= 0 ? 'text-success' : 'text-danger') + '">' +
        '₹' + (position.pnl || 0).toFixed(2) + '</td>';
    return row;
};

TradingDashboard.prototype.updateHoldingsTable = function(holdings) {
    var tbody = document.querySelector('#holdingsTable tbody');
    if (!tbody) return;

    tbody.innerHTML = '';
    for (var i = 0; i < holdings.length; i++) {
        var holding = holdings[i];
        var row = this.createHoldingRow(holding);
        tbody.appendChild(row);
    }
};

TradingDashboard.prototype.createHoldingRow = function(holding) {
    var row = document.createElement('tr');
    row.innerHTML = 
        '<td>' + (holding.symbol || '') + '</td>' +
        '<td>' + (holding.quantity || 0) + '</td>' +
        '<td>₹' + (holding.avg_price || 0).toFixed(2) + '</td>' +
        '<td>₹' + (holding.ltp || 0).toFixed(2) + '</td>' +
        '<td class="' + (holding.pnl >= 0 ? 'text-success' : 'text-danger') + '">' +
        '₹' + (holding.pnl || 0).toFixed(2) + '</td>';
    return row;
};

TradingDashboard.prototype.updateSummaryCards = function(summary) {
    var elements = {
        totalPnl: document.querySelector('#totalPnl'),
        totalValue: document.querySelector('#totalValue'),
        todayPnl: document.querySelector('#todayPnl')
    };

    if (elements.totalPnl && summary.total_pnl !== undefined) {
        elements.totalPnl.textContent = '₹' + summary.total_pnl.toFixed(2);
        elements.totalPnl.className = summary.total_pnl >= 0 ? 'text-success' : 'text-danger';
    }

    if (elements.totalValue && summary.total_value !== undefined) {
        elements.totalValue.textContent = '₹' + summary.total_value.toFixed(2);
    }

    if (elements.todayPnl && summary.today_pnl !== undefined) {
        elements.todayPnl.textContent = '₹' + summary.today_pnl.toFixed(2);
        elements.todayPnl.className = summary.today_pnl >= 0 ? 'text-success' : 'text-danger';
    }
};

TradingDashboard.prototype.initializeWebSocket = function() {
    try {
        if (typeof WebSocketHandler !== 'undefined') {
            this.wsHandler = new WebSocketHandler();
            this.wsHandler.connect();
            this.isConnected = true;
        }
    } catch (error) {
        console.warn('WebSocket initialization failed:', error);
        this.isConnected = false;
    }
};

TradingDashboard.prototype.destroy = function() {
    if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
    }
    if (this.wsHandler) {
        this.wsHandler.disconnect();
    }
};

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (typeof window.tradingDashboard === 'undefined') {
        window.tradingDashboard = new TradingDashboard();
    }
});

// Fallback initialization if DOM is already loaded
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    if (typeof window.tradingDashboard === 'undefined') {
        window.tradingDashboard = new TradingDashboard();
    }
}