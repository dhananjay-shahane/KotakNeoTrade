// ETF Signals Manager - ES5 Compatible
function ETFSignalsManager() {
    this.positions = [];
    this.liveDataInterval = null;
    this.autoRefreshInterval = 30000; // Default 30 seconds
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
    this.startAutoRefresh();
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

    // Auto refresh interval
    var autoRefreshInterval = document.getElementById('autoRefreshInterval');
    if (autoRefreshInterval) {
        autoRefreshInterval.addEventListener('change', function(e) {
            self.autoRefreshInterval = parseInt(e.target.value) * 1000;
            self.startAutoRefresh();
        });
    }

    // Auto refresh toggle
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
                    console.log('API Response:', data);
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
        row.innerHTML = '<td colspan="25" class="text-center text-muted">No ETF signals found in database.</td>';
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

    // Extract data from position object with proper fallbacks
    var symbol = position.symbol || position.etf || 'N/A';
    var entryPrice = parseFloat(position.entry_price || position.ep || 0);
    var currentPrice = parseFloat(position.current_price || position.cmp || entryPrice);
    var quantity = parseInt(position.quantity || position.qty || 0);
    var pnl = parseFloat(position.pnl || position.pl || 0);
    var changePct = parseFloat(position.pnl_percentage || position.change_pct || 0);
    var investment = parseFloat(position.investment_amount || position.inv || (entryPrice * quantity));
    var targetPrice = parseFloat(position.target_price || position.tp || entryPrice * 1.1);
    var createdAt = position.created_at || position.date || '';
    var positionType = position.position_type || (position.pos === 1 ? 'LONG' : 'SHORT') || 'LONG';
    var status = position.status || 'ACTIVE';

    // Calculate change percentage if not provided
    if (!changePct && entryPrice > 0) {
        changePct = ((currentPrice - entryPrice) / entryPrice) * 100;
    }

    // Recalculate P&L if not provided
    if (!pnl && quantity > 0 && entryPrice > 0) {
        var currentValue = currentPrice * quantity;
        pnl = currentValue - investment;
    }

    var pnlClass = pnl >= 0 ? 'profit' : 'loss';
    var changeClass = changePct >= 0 ? 'profit' : 'loss';

    // Format date
    var entryDate = '';
    if (createdAt) {
        try {
            var date = typeof createdAt === 'string' ? new Date(createdAt) : createdAt;
            entryDate = date.toLocaleDateString('en-GB');
        } catch (e) {
            entryDate = createdAt.toString();
        }
    }

    // Calculate days held
    var daysHeld = '';
    if (createdAt) {
        try {
            var entryDateObj = typeof createdAt === 'string' ? new Date(createdAt) : createdAt;
            var today = new Date();
            var diffTime = Math.abs(today - entryDateObj);
            var diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            daysHeld = diffDays.toString();
        } catch (e) {
            daysHeld = '0';
        }
    }

    // Format display values
    var displaySymbol = symbol !== 'N/A' ? symbol : '-';
    var displayQuantity = quantity > 0 ? quantity : '-';
    var displayEntryPrice = entryPrice > 0 ? '₹' + entryPrice.toFixed(2) : '-';
    var displayCurrentPrice = currentPrice > 0 ? '₹' + currentPrice.toFixed(2) : displayEntryPrice;
    var displayInvestment = investment > 0 ? '₹' + investment.toFixed(0) : '-';
    var displayTargetPrice = targetPrice > 0 ? '₹' + targetPrice.toFixed(2) : '-';
    var displayCurrentValue = (currentPrice * quantity) > 0 ? '₹' + (currentPrice * quantity).toFixed(0) : '-';
    var displayPnl = pnl !== 0 ? '₹' + pnl.toFixed(0) : '₹0';
    var displayChangePct = changePct !== 0 ? changePct.toFixed(2) + '%' : '0.00%';

    console.log('Displaying CMP for', symbol, ':', currentPrice, 'Change:', changePct.toFixed(2) + '%');

    row.innerHTML = 
        '<td><strong>' + displaySymbol + '</strong></td>' +
        '<td>-</td>' + // 30 day performance
        '<td>' + (daysHeld || '-') + '</td>' +
        '<td>' + (entryDate || '-') + '</td>' +
        '<td><span class="badge ' + (status === 'ACTIVE' ? 'bg-success' : 'bg-secondary') + '">' + (status === 'ACTIVE' ? 'OPEN' : 'CLOSED') + '</span></td>' +
        '<td>' + displayQuantity + '</td>' +
        '<td>' + displayEntryPrice + '</td>' +
        '<td class="' + changeClass + '">' + displayCurrentPrice + '</td>' +
        '<td class="' + changeClass + '">' + displayChangePct + '</td>' +
        '<td>' + displayInvestment + '</td>' +
        '<td>' + displayTargetPrice + '</td>' +
        '<td>' + displayCurrentValue + '</td>' +
        '<td class="profit">' + (targetPrice > entryPrice && entryPrice > 0 ? '+' + (((targetPrice - entryPrice) / entryPrice * 100)).toFixed(2) + '%' : '-') + '</td>' +
        '<td class="' + pnlClass + '">' + displayPnl + '</td>' +
        '<td>' + (entryDate || '-') + '</td>' +
        '<td>-</td>' + // Expected/Expiry
        '<td>-</td>' + // Price Range
        '<td>' + changePct.toFixed(1) + '</td>' + // Performance Points
        '<td>' + (investment > 0 ? investment.toFixed(0) : '-') + '</td>' + // IV
        '<td class="' + changeClass + '">' + displayChangePct + '</td>' + // Intraday Performance
        '<td><small>-</small></td>' + // Notes/Tags
        '<td><small>-</small></td>' + // Quote Time
        '<td class="' + changeClass + '">-</td>' + // 7 Day Change
        '<td class="' + changeClass + '">' + displayChangePct + '</td>' +
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

    var showingCount = document.getElementById('showingCount');
    if (showingCount) {
        showingCount.textContent = this.positions.length;
    }

    var totalCount = document.getElementById('totalCount');
    if (totalCount) {
        totalCount.textContent = this.positions.length;
    }
};

ETFSignalsManager.prototype.startAutoRefresh = function() {
    var self = this;
    this.stopAutoRefresh(); // Clear any existing interval

    if (this.autoRefreshInterval && this.autoRefreshInterval > 0) {
        this.liveDataInterval = setInterval(function() {
            self.loadPositions();
        }, this.autoRefreshInterval);
        console.log('Auto refresh started with interval:', this.autoRefreshInterval + 'ms');
    }
};

ETFSignalsManager.prototype.stopAutoRefresh = function() {
    if (this.liveDataInterval) {
        clearInterval(this.liveDataInterval);
        this.liveDataInterval = null;
        console.log('Auto refresh stopped');
    }
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
    if (!this.positions || this.positions.length === 0) {
        alert('No data to export');
        return;
    }

    var csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "ETF,Entry Price,Current Price,Quantity,Investment,P&L,Change %\n";

    this.positions.forEach(function(position) {
        var symbol = position.symbol || position.etf || '';
        var entryPrice = position.entry_price || position.ep || 0;
        var currentPrice = position.current_price || position.cmp || 0;
        var quantity = position.quantity || position.qty || 0;
        var investment = position.investment_amount || position.inv || 0;
        var pnl = position.pnl || position.pl || 0;
        var changePct = position.pnl_percentage || position.change_pct || 0;

        var row = [symbol, entryPrice, currentPrice, quantity, investment, pnl, changePct].join(',');
        csvContent += row + "\n";
    });

    var encodedUri = encodeURI(csvContent);
    var link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "etf_signals.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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
    if (window.etfSignalsManager) {
        window.etfSignalsManager.stopAutoRefresh();
        window.etfSignalsManager.autoRefreshInterval = interval;
        if (interval > 0) {
            window.etfSignalsManager.startAutoRefresh();
        }
        var currentIntervalSpan = document.getElementById('currentInterval');
        if (currentIntervalSpan) {
            currentIntervalSpan.textContent = text;
        }
        console.log('Refresh interval set to:', interval + 'ms (' + text + ')');
    }
}

function exportSignals() {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.exportToCSV();
    }
}

function addDeal(symbol, price) {
    // Find the current signal data for this symbol
    var currentSignal = null;
    if (window.etfSignalsManager && window.etfSignalsManager.signals) {
        currentSignal = window.etfSignalsManager.signals.find(function(signal) {
            return (signal.symbol || signal.etf) === symbol;
        });
    }

    // Show confirmation dialog
    if (!confirm('Add deal for ' + symbol + ' at ₹' + price.toFixed(2) + '?')) {
        return;
    }

    // Create complete signal data for the deal
    var signalData = {
        symbol: symbol,
        pos: 1, // LONG position
        qty: 1,
        cmp: price,
        ep: price,
        tp: currentSignal ? currentSignal.tp : (price * 1.05),
        inv: price * 1,
        pl: 0,
        change_pct: 0,
        thirty: currentSignal ? currentSignal.thirty : '0%',
        dh: 0,
        date: new Date().toISOString().split('T')[0],
        ed: new Date().toISOString().split('T')[0],
        pr: currentSignal ? currentSignal.pr : '0%',
        pp: currentSignal ? currentSignal.pp : '★★',
        iv: currentSignal ? currentSignal.iv : 'Medium',
        ip: '0%',
        nt: 'Added from ETF signals',
        qt: new Date().toLocaleTimeString('en-GB', {hour: '2-digit', minute: '2-digit'}),
        seven: currentSignal ? currentSignal.seven : '0%',
        change2: 0
    };

    // Send POST request to create deal in database
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/deals/create-from-signal', true);
    xhr.setRequestHeader('Content-Type', 'application/json');

    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            console.log('API Response Status:', xhr.status);
            console.log('API Response Text:', xhr.responseText);
            if (xhr.status === 200) {
                try {
                    var response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        // Show success message
                        alert('Deal created successfully for ' + symbol + '!');

                        // Add to localStorage for immediate display
                        var userDeals = JSON.parse(localStorage.getItem('userDeals') || '[]');
                        var existingDealIndex = -1;
                        for (var i = 0; i < userDeals.length; i++) {
                            if (userDeals[i].symbol === symbol && Math.abs(parseFloat(userDeals[i].ep) - parseFloat(price)) < 0.01) {
                                existingDealIndex = i;
                                break;
                            }
                        }

                        // Only add if no duplicate exists
                        if (existingDealIndex === -1) {
                            var newDeal = {
                                id: response.deal_id || 'deal_' + Date.now(),
                                symbol: symbol,
                                pos: 1, // LONG position
                                qty: 1,
                                ep: price,
                                cmp: price,
                                pl: 0,
                                change_pct: 0,
                                inv: price * 1,
                                tp: signalData.tp,
                                tva: signalData.tp * 1,
                                tpr: (signalData.tp - price) * 1,
                                date: signalData.date,
                                status: 'ACTIVE',
                                thirty: signalData.thirty,
                                dh: 0,
                                ed: signalData.ed,
                                pr: signalData.pr,
                                pp: signalData.pp,
                                iv: signalData.iv,
                                ip: signalData.ip,
                                nt: signalData.nt,
                                qt: signalData.qt,
                                seven: signalData.seven,
                                change2: 0
                            };
                            userDeals.unshift(newDeal);
                            localStorage.setItem('userDeals', JSON.stringify(userDeals));
                        }

                        // Trigger storage event to update deals page if it's open in another tab
                        var storageEvent = document.createEvent('Event');
                        storageEvent.initEvent('storage', true, true);
                        storageEvent.key = 'userDeals';
                        storageEvent.newValue = JSON.stringify(userDeals);
                        window.dispatchEvent(storageEvent);

                        // Navigate to deals page with symbol and price parameters
                        setTimeout(function() {
                            window.location.href = '/deals?symbol=' + encodeURIComponent(symbol) + '&price=' + price.toFixed(2);
                        }, 1000);
                    } else {
                        alert('Failed to create deal: ' + (response.message || 'Unknown error'));
                    }
                } catch (parseError) {
                    console.error('Failed to parse API response:', parseError);
                    alert('Invalid response from server');
                }
            } else {
                console.error('API call failed with status:', xhr.status);
                alert('Failed to create deal. Server returned status: ' + xhr.status);
            }
        }
    };

    xhr.send(JSON.stringify({signal_data: signalData}));
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
// Update auto-refresh functionality for Yahoo Finance
        this.autoRefreshInterval = null;
        this.updateInterval = 300000; // 5 minutes (Yahoo Finance rate limits)

        // Setup auto-refresh controls
        this.setupAutoRefresh();
// Add Yahoo Finance update button to refresh section
        const refreshSection = document.querySelector('.auto-refresh-section');
        if (refreshSection) {
            const updateBtn = document.createElement('button');
            updateBtn.className = 'btn btn-success btn-sm me-2';
            updateBtn.innerHTML = '<i class="fas fa-chart-line"></i> Update from Yahoo Finance';
            updateBtn.onclick = () => this.forceYahooUpdate();
            refreshSection.appendChild(updateBtn);
        }
forceUpdate() {
        console.log('🔄 Force updating ETF signals...');
        this.loadSignals();
    }

    async forceYahooUpdate() {
        console.log('🔄 Force updating prices from Yahoo Finance...');

        const updateBtn = document.querySelector('button[onclick*="forceYahooUpdate"]');
        if (updateBtn) {
            updateBtn.disabled = true;
            updateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
        }

        try {
            const response = await fetch('/api/yahoo/update-prices', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (result.success) {
                console.log(`✅ Updated ${result.signals_updated} signals and ${result.quotes_updated} quotes`);
                this.showNotification(`Updated ${result.signals_updated} signals from Yahoo Finance`, 'success');

                // Reload signals to show updated data
                setTimeout(() => {
                    this.loadSignals();
                }, 1000);
            } else {
                console.error('❌ Failed to update from Yahoo Finance:', result.error);
                this.showNotification('Failed to update prices from Yahoo Finance', 'danger');
            }
        } catch (error) {
            console.error('❌ Error updating from Yahoo Finance:', error);
            this.showNotification('Error updating prices from Yahoo Finance', 'danger');
        } finally {
            if (updateBtn) {
                updateBtn.disabled = false;
                updateBtn.innerHTML = '<i class="fas fa-chart-line"></i> Update from Yahoo Finance';
            }
        }
    }
// ETF Signals Manager - ES5 Compatible
function ETFSignalsManager() {
    var self = this;
    this.signals = [];
    this.filteredSignals = [];
    this.currentPage = 1;
    this.itemsPerPage = 25;
    this.isLoading = false;
    this.refreshInterval = null;
    this.sortField = 'id';
    this.sortDirection = 'desc';

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            self.init();
        });
    } else {
        this.init();
    }
}
// ETF Signals Manager - ES5 Compatible
function ETFSignalsManager() {
    var self = this;
    this.signals = [];
    this.filteredSignals = [];
    this.currentPage = 1;
    this.itemsPerPage = 25;
    this.isLoading = false;
    this.refreshInterval = null;
    this.sortField = 'id';
    this.sortDirection = 'desc';

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            self.init();
        });
    } else {
        this.init();
    }
}
ETFSignalsManager.prototype.init = function() {
    console.log('ETF Signals Manager initialized');
    this.setupEventListeners();
    this.loadSignals();
    this.startAutoRefresh();
};
// ETF Signals Manager - ES5 Compatible
function ETFSignalsManager() {
    var self = this;
    this.signals = [];
    this.filteredSignals = [];
    this.currentPage = 1;
    this.itemsPerPage = 25;
    this.isLoading = false;
    this.refreshInterval = null;
    this.sortField = 'id';
    this.sortDirection = 'desc';

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            self.init();
        });
    } else {
        this.init();
    }
}
ETFSignalsManager.prototype.init = function() {
    console.log('ETF Signals Manager initialized');
    this.setupEventListeners();
    this.loadSignals();
    this.startAutoRefresh();
};
ETFSignalsManager.prototype.setupEventListeners = function() {
    var self = this;

    // Refresh button
    var refreshBtn = document.getElementById('refreshSignalsBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            self.loadSignals();
        });
    }

    // Auto-refresh controls
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

    // Search functionality
    var searchInput = document.getElementById('signalSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            self.applyFilters();
        });
    }

    // Items per page selector
    var itemsPerPageSelect = document.getElementById('itemsPerPage');
    if (itemsPerPageSelect) {
        itemsPerPageSelect.addEventListener('change', function(e) {
            self.itemsPerPage = parseInt(e.target.value);
            self.currentPage = 1;
            self.renderSignalsTable();
            self.updatePagination();
        });
    }
};
// ETF Signals Manager - ES5 Compatible
function ETFSignalsManager() {
    var self = this;
    this.signals = [];
    this.filteredSignals = [];
    this.currentPage = 1;
    this.itemsPerPage = 25;
    this.isLoading = false;
    this.refreshInterval = null;
    this.sortField = 'id';
    this.sortDirection = 'desc';

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            self.init();
        });
    } else {
        this.init();
    }
}
ETFSignalsManager.prototype.init = function() {
    console.log('ETF Signals Manager initialized');
    this.setupEventListeners();
    this.loadSignals();
    this.startAutoRefresh();
};
ETFSignalsManager.prototype.setupEventListeners = function() {
    var self = this;

    // Refresh button
    var refreshBtn = document.getElementById('refreshSignalsBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            self.loadSignals();
        });
    }

    // Auto-refresh controls
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

    // Search functionality
    var searchInput = document.getElementById('signalSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            self.applyFilters();
        });
    }

    // Items per page selector
    var itemsPerPageSelect = document.getElementById('itemsPerPage');
    if (itemsPerPageSelect) {
        itemsPerPageSelect.addEventListener('change', function(e) {
            self.itemsPerPage = parseInt(e.target.value);
            self.currentPage = 1;
            self.renderSignalsTable();
            self.updatePagination();
        });
    }
};
ETFSignalsManager.prototype.loadSignals = function() {
    var self = this;

    if (this.isLoading) return;

    this.isLoading = true;
    this.showLoadingState();

    fetch('/api/etf-signals-data')
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.success) {
                self.signals = data.signals || [];
                self.filteredSignals = self.signals.slice();
                self.renderSignalsTable();
                self.updatePagination();
                self.updatePortfolioSummary(data.portfolio);
                self.showSuccessMessage('Loaded ' + self.signals.length + ' signals');
            } else {
                throw new Error(data.error || 'Failed to load signals');
            }
        })
        .catch(function(error) {
            console.error('Error loading signals:', error);
            self.showErrorMessage(error.message);
        })
        .finally(function() {
            self.isLoading = false;
            self.hideLoadingState();
        });
};
// ETF Signals Manager - ES5 Compatible
function ETFSignalsManager() {
    var self = this;
    this.signals = [];
    this.filteredSignals = [];
    this.currentPage = 1;
    this.itemsPerPage = 25;
    this.isLoading = false;
    this.refreshInterval = null;
    this.sortField = 'id';
    this.sortDirection = 'desc';

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            self.init();
        });
```text
        });
    } else {
        this.init();
    }
}
ETFSignalsManager.prototype.init = function() {
    console.log('ETF Signals Manager initialized');
    this.setupEventListeners();
    this.loadSignals();
    this.startAutoRefresh();
};
ETFSignalsManager.prototype.setupEventListeners = function() {
    var self = this;

    // Refresh button
    var refreshBtn = document.getElementById('refreshSignalsBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            self.loadSignals();
        });
    }

    // Auto-refresh controls
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

    // Search functionality
    var searchInput = document.getElementById('signalSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            self.applyFilters();
        });
    }

    // Items per page selector
    var itemsPerPageSelect = document.getElementById('itemsPerPage');
    if (itemsPerPageSelect) {
        itemsPerPageSelect.addEventListener('change', function(e) {
            self.itemsPerPage = parseInt(e.target.value);
            self.currentPage = 1;
            self.renderSignalsTable();
            self.updatePagination();
        });
    }
};
ETFSignalsManager.prototype.loadSignals = function() {
    var self = this;

    if (this.isLoading) return;

    this.isLoading = true;
    this.showLoadingState();

    fetch('/api/etf-signals-data')
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.success) {
                self.signals = data.signals || [];
                self.filteredSignals = self.signals.slice();
                self.renderSignalsTable();
                self.updatePagination();
                self.updatePortfolioSummary(data.portfolio);
                self.showSuccessMessage('Loaded ' + self.signals.length + ' signals');
            } else {
                throw new Error(data.error || 'Failed to load signals');
            }
        })
        .catch(function(error) {
            console.error('Error loading signals:', error);
            self.showErrorMessage(error.message);
        })
        .finally(function() {
            self.isLoading = false;
            self.hideLoadingState();
        });
};
ETFSignalsManager.prototype.renderSignalsTable = function() {
    var tbody = document.getElementById('signalsTableBody');
    if (!tbody) return;

    var startIdx = (this.currentPage - 1) * this.itemsPerPage;
    var endIdx = startIdx + this.itemsPerPage;
    var pageSignals = this.filteredSignals.slice(startIdx, endIdx);

    if (pageSignals.length === 0) {
        tbody.innerHTML = '<tr><td colspan="12" class="text-center">No signals found</td></tr>';
        return;
    }

    var self = this;
    tbody.innerHTML = pageSignals.map(function(signal) {
        return self.createSignalRow(signal);
    }).join('');
};

ETFSignalsManager.prototype.createSignalRow = function(signal) {
    var pnlClass = signal.pl >= 0 ? 'text-success' : 'text-danger';
    var statusClass = signal.status === 'ACTIVE' ? 'badge-success' : 'badge-secondary';
    var changeClass = signal.change_pct >= 0 ? 'text-success' : 'text-danger';

    return '<tr>' +
        '<td>' + (signal.etf || 'N/A') + '</td>' +
        '<td>₹' + (signal.ep || 0).toFixed(2) + '</td>' +
        '<td>₹' + (signal.cmp || 0).toFixed(2) + '</td>' +
        '<td>' + (signal.qty || 0) + '</td>' +
        '<td>₹' + (signal.inv || 0).toLocaleString() + '</td>' +
        '<td class="' + pnlClass + '">₹' + (signal.pl || 0).toLocaleString() + '</td>' +
        '<td class="' + changeClass + '">' + (signal.change_pct || 0).toFixed(2) + '%</td>' +
        '<td><span class="badge ' + statusClass + '">' + (signal.status || 'UNKNOWN') + '</span></td>' +
        '<td>' + (signal.date || 'N/A') + '</td>' +
        '<td>₹' + (signal.tp || 0).toFixed(2) + '</td>' +
        '<td>₹' + (signal.tva || 0).toLocaleString() + '</td>' +
        '<td>' +
            '<button class="btn btn-primary btn-sm" onclick="addDealFromSignal(' + signal.id + ')">' +
                '<i class="fas fa-plus me-1"></i>Add Deal' +
            '</button>' +
        '</td>' +
    '</tr>';
};
ETFSignalsManager.prototype.updatePortfolioSummary = function(portfolio) {
    if (!portfolio) return;

    var elements = {
        'totalPositions': portfolio.total_positions || 0,
        'activePositions': portfolio.active_positions || 0,
        'totalInvestment': '₹' + (portfolio.total_investment || 0).toLocaleString(),
        'currentValue': '₹' + (portfolio.current_value || 0).toLocaleString(),
        'totalPnl': '₹' + (portfolio.total_pnl || 0).toLocaleString(),
        'returnPercent': (portfolio.return_percent || 0).toFixed(2) + '%'
    };

    for (var id in elements) {
        var element = document.getElementById(id);
        if (element) element.textContent = elements[id];
    }
};

ETFSignalsManager.prototype.applyFilters = function() {
    var searchInput = document.getElementById('signalSearch');
    var searchTerm = searchInput ? searchInput.value.toLowerCase() : '';

    var self = this;
    this.filteredSignals = this.signals.filter(function(signal) {
        return (signal.etf && signal.etf.toLowerCase().indexOf(searchTerm) !== -1) ||
               (signal.status && signal.status.toLowerCase().indexOf(searchTerm) !== -1);
    });

    this.currentPage = 1;
    this.renderSignalsTable();
    this.updatePagination();
};

ETFSignalsManager.prototype.updatePagination = function() {
    var totalPages = Math.ceil(this.filteredSignals.length / this.itemsPerPage);
    var paginationInfo = document.getElementById('paginationInfo');

    if (paginationInfo) {
        var startItem = (this.currentPage - 1) * this.itemsPerPage + 1;
        var endItem = Math.min(this.currentPage * this.itemsPerPage, this.filteredSignals.length);
        paginationInfo.textContent = 'Showing ' + startItem + '-' + endItem + ' of ' + this.filteredSignals.length + ' signals';
    }

    // Update pagination buttons
    var prevBtn = document.getElementById('prevPageBtn');
    var nextBtn = document.getElementById('nextPageBtn');

    if (prevBtn) prevBtn.disabled = this.currentPage <= 1;
    if (nextBtn) nextBtn.disabled = this.currentPage >= totalPages;
};

ETFSignalsManager.prototype.showLoadingState = function() {
    var refreshBtn = document.getElementById('refreshSignalsBtn');
    if (refreshBtn) {
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Loading...';
        refreshBtn.disabled = true;
    }
};

ETFSignalsManager.prototype.hideLoadingState = function() {
    var refreshBtn = document.getElementById('refreshSignalsBtn');
    if (refreshBtn) {
        refreshBtn.innerHTML = '<i class="fas fa-sync me-1"></i>Refresh';
        refreshBtn.disabled = false;
    }
};

ETFSignalsManager.prototype.showSuccessMessage = function(message) {
    console.log('Success:', message);
};

ETFSignalsManager.prototype.showErrorMessage = function(message) {
    console.error('Error:', message);
    var tbody = document.getElementById('signalsTableBody');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="12" class="text-center text-danger">' + message + '</td></tr>';
    }
};

ETFSignalsManager.prototype.startAutoRefresh = function() {
    var self = this;
    this.stopAutoRefresh();
    this.refreshInterval = setInterval(function() {
        self.loadSignals();
    }, 30000);
};

ETFSignalsManager.prototype.stopAutoRefresh = function() {
    if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
        this.refreshInterval = null;
    }
};
// Initialize the ETF Signals Manager
window.etfSignalsManager = new ETFSignalsManager();

// Global functions for HTML event handlers
function refreshSignals() {
    window.etfSignalsManager.loadSignals();
}

function addDealFromSignal(signalId) {
    var signal = null;
    for (var i = 0; i < window.etfSignalsManager.signals.length; i++) {
        if (window.etfSignalsManager.signals[i].id === signalId) {
            signal = window.etfSignalsManager.signals[i];
            break;
        }
    }

    if (!signal) {
        alert('Signal not found');
        return;
    }

    var signalData = {
        symbol: signal.etf,
        qty: signal.qty,
        cmp: signal.cmp,
        pos: signal.pos,
        tp: signal.tp,
        nt: signal.nt || ''
    };

    fetch('/api/deals/create-from-signal', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            signal_data: signalData
        })
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        if (data.success) {
            alert('Deal added successfully!');
            // Optionally redirect to deals page
            window.location.href = '/deals';
        } else {
            alert('Error adding deal: ' + data.message);
        }
    })
    .catch(function(error) {
        console.error('Error:', error);
        alert('Error adding deal');
    });
}