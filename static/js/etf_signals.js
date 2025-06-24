// ETF Signals Manager - ES5 Compatible
function ETFSignalsManager() {
    this.positions = [];
    this.liveDataInterval = null;
    this.searchTimeout = null;
    
    // Initialize after DOM is ready
    var self = this;
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            self.init();
        });
    } else {
        this.init();
    }
}

ETFSignalsManager.prototype.init = function() {
    this.setupEventListeners();
    this.loadPositions();
    this.initLiveDataConnection();
};

ETFSignalsManager.prototype.setupEventListeners = function() {
    var self = this;

    // Add deal button
    var addDealBtn = document.getElementById('addDealBtn');
    if (addDealBtn) {
        addDealBtn.addEventListener('click', function() {
            self.showAddDealModal();
        });
    }

    // Save position button
    var savePositionBtn = document.getElementById('savePositionBtn');
    if (savePositionBtn) {
        savePositionBtn.addEventListener('click', function() {
            self.savePosition();
        });
    }

    // Refresh button
    var refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            self.loadPositions();
        });
    }

    // Auto refresh interval removed

    // ETF symbol search
    var etfSymbol = document.getElementById('etfSymbol');
    if (etfSymbol) {
        etfSymbol.addEventListener('input', function(e) {
            clearTimeout(self.searchTimeout);
            self.searchTimeout = setTimeout(function() {
                self.searchETFSymbols(e.target.value);
            }, 300);
        });
    }

    // Position filters
    var positionFilter = document.getElementById('positionFilter');
    if (positionFilter) {
        positionFilter.addEventListener('change', function() {
            self.filterPositions();
        });
    }

    var statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            self.filterPositions();
        });
    }

    // Auto refresh toggle removed

    // Export buttons
    var exportCsvBtn = document.getElementById('exportCsvBtn');
    if (exportCsvBtn) {
        exportCsvBtn.addEventListener('click', function() {
            self.exportToCSV();
        });
    }

    var exportPdfBtn = document.getElementById('exportPdfBtn');
    if (exportPdfBtn) {
        exportPdfBtn.addEventListener('click', function() {
            self.exportToPDF();
        });
    }
};

ETFSignalsManager.prototype.loadPositions = function() {
    var self = this;
    this.showLoading(true);

    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/api/etf-signals-data', true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            self.showLoading(false);
            if (xhr.status === 200) {
                try {
                    var data = JSON.parse(xhr.responseText);
                    if (data.success) {
                        self.positions = data.signals || [];
                        self.renderPositionsTable();
                        self.updateSummaryCards(data.portfolio || {});
                        self.updateVisibleCount();
                        console.log('Loaded', self.positions.length, 'ETF signals');
                    } else {
                        self.showAlert('Error loading positions: ' + (data.message || 'Unknown error'), 'error');
                    }
                } catch (e) {
                    console.error('Error parsing response:', e);
                    self.showAlert('Error parsing server response', 'error');
                }
            } else {
                self.showAlert('Error loading positions: Server error ' + xhr.status, 'error');
            }
        }
    };
    xhr.send();
};

ETFSignalsManager.prototype.showLoading = function(show) {
    var loader = document.getElementById('loadingSpinner');
    if (loader) {
        loader.style.display = show ? 'block' : 'none';
    }

    var tbody = document.getElementById('signalsTableBody');
    if (tbody && show) {
        tbody.innerHTML = '<tr><td colspan="25" class="text-center">Loading ETF signals...</td></tr>';
    }
};

ETFSignalsManager.prototype.showAlert = function(message, type) {
    var alertClass = type === 'error' ? 'alert-danger' : 'alert-success';
    var alertHtml = '<div class="alert ' + alertClass + ' alert-dismissible fade show" role="alert">' +
        message +
        '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
        '</div>';

    var container = document.querySelector('.container');
    if (container) {
        container.insertAdjacentHTML('afterbegin', alertHtml);
    }

    // Auto remove after 5 seconds
    setTimeout(function() {
        var alert = document.querySelector('.alert:first-of-type');
        if (alert && alert.classList.contains(alertClass)) {
            alert.remove();
        }
    }, 5000);
};

ETFSignalsManager.prototype.renderPositionsTable = function() {
    var tbody = document.getElementById('signalsTableBody');
    if (!tbody) {
        console.error('Table body not found');
        return;
    }

    tbody.innerHTML = '';

    if (!this.positions || this.positions.length === 0) {
        var row = tbody.insertRow();
        row.innerHTML = '<td colspan="25" class="text-center text-muted">No admin trade signals found in database. Only real admin_trade_signals records are displayed.</td>';
        return;
    }

    console.log('Rendering', this.positions.length, 'positions');

    for (var i = 0; i < this.positions.length; i++) {
        var position = this.positions[i];
        var row = this.createPositionRow(position);
        tbody.appendChild(row);
    }
};

ETFSignalsManager.prototype.createPositionRow = function(position) {
    var row = document.createElement('tr');

    // Ensure we have valid data with fallbacks
    var symbol = position.symbol || position.etf || 'N/A';
    var entryPrice = parseFloat(position.ep || position.entry_price || 0);
    var currentPrice = parseFloat(position.cmp || position.current_price || 0);
    var quantity = parseInt(position.qty || position.quantity || 0);
    var pnl = parseFloat(position.pl || position.pnl_amount || 0);
    var changePct = parseFloat(position.change_pct || position.change_percent || 0);
    var investment = parseFloat(position.inv || position.invested_amount || (entryPrice * quantity));
    var targetPrice = parseFloat(position.tp || position.target_price || 0);

    // Always show current price directly, even if same as entry price
    if (!currentPrice || currentPrice <= 0) {
        currentPrice = entryPrice; // Fallback to entry price if no CMP available
        changePct = 0; // No change when no valid CMP
        console.log('No CMP available for', symbol, ', using entry price');
    } else {
        // Calculate change percentage based on actual CMP vs entry price
        changePct = ((currentPrice - entryPrice) / entryPrice) * 100;
        console.log('Displaying CMP for', symbol, ':', currentPrice, 'Change:', changePct.toFixed(2) + '%');
    }

    // Recalculate P&L based on current price
    var currentValue = currentPrice * quantity;
    pnl = currentValue - investment;

    var pnlClass = pnl >= 0 ? 'profit' : 'loss';
    var changeClass = changePct >= 0 ? 'profit' : 'loss';

    row.innerHTML = 
        '<td><strong>' + symbol + '</strong></td>' +
        '<td>' + (position.thirty || '0%') + '</td>' +
        '<td>' + (position.dh || '0') + '</td>' +
        '<td>' + (position.date || '') + '</td>' +
        '<td><span class="badge ' + (position.pos == 1 ? 'bg-success' : 'bg-secondary') + '">' + (position.pos == 1 ? '1 (OPEN)' : '0 (CLOSED)') + '</span></td>' +
        '<td>' + quantity + '</td>' +
        '<td>₹' + entryPrice.toFixed(2) + '</td>' +
        '<td class="' + changeClass + '">' + 
        (currentPrice > 0 ? '₹' + currentPrice.toFixed(2) : 
         '<span class="text-muted">-</span>') + '</td>' +
        '<td class="' + changeClass + '">' + changePct.toFixed(2) + '%</td>' +
        '<td>₹' + investment.toFixed(0) + '</td>' +
        '<td>₹' + targetPrice.toFixed(2) + '</td>' +
        '<td>₹' + (currentValue || (currentPrice * quantity)).toFixed(0) + '</td>' +
        '<td class="profit">' + ((targetPrice > entryPrice ? '+' : '') + (((targetPrice - entryPrice) / entryPrice * 100)).toFixed(2)) + '%</td>' +
        '<td class="' + pnlClass + '">₹' + pnl.toFixed(0) + '</td>' +
        '<td>' + (position.ed || '') + '</td>' +
        '<td>' + (position.exp || '') + '</td>' +
        '<td>' + (position.pr || '0%') + '</td>' +
        '<td>' + (position.pp || changePct.toFixed(1)) + '</td>' +
        '<td>' + (position.iv || investment.toFixed(0)) + '</td>' +
        '<td class="' + changeClass + '">' + (position.ip || changePct.toFixed(2) + '%') + '</td>' +
        '<td><small>' + (position.nt || '') + '</small></td>' +
        '<td><small>' + (position.qt || '') + '</small></td>' +
        '<td class="' + changeClass + '">' + (position.seven || '0%') + '</td>' +
        '<td class="' + changeClass + '">' + changePct.toFixed(2) + '%</td>' +
        '<td>' +
        '<button class="btn btn-sm btn-primary" onclick="addDeal(\'' + symbol + '\', ' + currentPrice + ')">Add Deal</button>' +
        '</td>';

    return row;
};

ETFSignalsManager.prototype.updateSummaryCards = function(portfolio) {
    var totalValue = document.getElementById('totalValue');
    var totalPnl = document.getElementById('totalPnl');
    var totalPositions = document.getElementById('totalPositions');

    if (totalValue && portfolio.current_value !== undefined) {
        totalValue.textContent = '₹' + portfolio.current_value.toFixed(2);
    }

    if (totalPnl && portfolio.total_pnl !== undefined) {
        totalPnl.textContent = '₹' + portfolio.total_pnl.toFixed(2);
        totalPnl.className = portfolio.total_pnl >= 0 ? 'text-success' : 'text-danger';
    }

    if (totalPositions && portfolio.total_positions !== undefined) {
        totalPositions.textContent = portfolio.total_positions;
    }
};

ETFSignalsManager.prototype.updateVisibleCount = function() {
    var countElement = document.getElementById('visibleCount');
    if (countElement) {
        countElement.textContent = this.positions.length;
    }

    var visibleSignalsCount = document.getElementById('visibleSignalsCount');
    if (visibleSignalsCount) {
        visibleSignalsCount.textContent = this.positions.length;
    }
};

ETFSignalsManager.prototype.startAutoRefresh = function() {
    // Auto refresh functionality removed
    console.log('Auto refresh disabled');
};

ETFSignalsManager.prototype.stopAutoRefresh = function() {
    // Auto refresh functionality removed
    console.log('Auto refresh disabled');
};

ETFSignalsManager.prototype.initLiveDataConnection = function() {
    console.log('Live data connection initialized');
};

ETFSignalsManager.prototype.showAddDealModal = function() {
    var modal = document.getElementById('addDealModal');
    if (modal && typeof bootstrap !== 'undefined') {
        var bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    }
};

ETFSignalsManager.prototype.savePosition = function() {
    console.log('Save position called');
};

ETFSignalsManager.prototype.searchETFSymbols = function(query) {
    console.log('Searching ETF symbols:', query);
};

ETFSignalsManager.prototype.filterPositions = function() {
    console.log('Filtering positions');
};

ETFSignalsManager.prototype.editPosition = function(id) {
    console.log('Edit position:', id);
};

ETFSignalsManager.prototype.deletePosition = function(id) {
    console.log('Delete position:', id);
};

ETFSignalsManager.prototype.exportToCSV = function() {
    console.log('Export to CSV');
};

ETFSignalsManager.prototype.exportToPDF = function() {
    console.log('Export to PDF');
};

// Global functions for button onclick handlers
function refreshSignals() {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.loadPositions();
    }
}

function setRefreshInterval(interval, text) {
    // Auto refresh functionality removed
    console.log('Auto refresh disabled');
}

function exportSignals() {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.exportToCSV();
    }
}

function addDeal(symbol, price) {
    var dealUrl = '/deals?symbol=' + encodeURIComponent(symbol) + '&price=' + price;
    window.location.href = dealUrl;
}

// Initialize ETF Signals Manager when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (typeof window.etfSignalsManager === 'undefined') {
        window.etfSignalsManager = new ETFSignalsManager();
        console.log('ETF Signals Manager initialized');
    }
});

// Fallback initialization
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    if (typeof window.etfSignalsManager === 'undefined') {
        window.etfSignalsManager = new ETFSignalsManager();
        console.log('ETF Signals Manager initialized (fallback)');
    }
}