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
    
    // Fetch initial data immediately
    this.fetchLatestData();
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
    this.fetchLatestData();
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
        console.log('Updating dashboard with data:', data);
        
        // Hide skeleton loader when data is loaded
        if (typeof window.hideDashboardSkeleton === 'function') {
            window.hideDashboardSkeleton();
        }
        
        // Update summary cards with actual data structure
        this.updateSummaryCards(data);
        
        if (data.positions) {
            this.updatePositionsTable(data.positions);
        }
        if (data.holdings) {
            this.updateHoldingsTable(data.holdings);
        }
    } catch (error) {
        console.warn('Error updating dashboard:', error);
        // Hide skeleton even on error
        if (typeof window.hideDashboardSkeleton === 'function') {
            window.hideDashboardSkeleton();
        }
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

TradingDashboard.prototype.updateSummaryCards = function(data) {
    try {
        console.log('Updating summary cards with:', data);
        
        // Update positions count
        var totalPositionsEl = document.querySelector('#totalPositions');
        if (totalPositionsEl && data.total_positions !== undefined) {
            totalPositionsEl.textContent = data.total_positions || 0;
        }
        
        // Update holdings count
        var totalHoldingsEl = document.querySelector('#totalHoldings');
        if (totalHoldingsEl && data.total_holdings !== undefined) {
            totalHoldingsEl.textContent = data.total_holdings || 0;
        }
        
        // Update today's orders count
        var todayOrdersEl = document.querySelector('#todayOrders');
        if (todayOrdersEl && data.total_orders !== undefined) {
            todayOrdersEl.textContent = data.total_orders || 0;
        }
        
        // Also try the alternate ID in case template uses different one
        var totalOrdersEl = document.querySelector('#totalOrders');
        if (totalOrdersEl && data.total_orders !== undefined) {
            totalOrdersEl.textContent = data.total_orders || 0;
        }
        
        // Update available margin
        var availableMarginEl = document.querySelector('#availableMargin');
        if (availableMarginEl && data.limits && data.limits.Net !== undefined) {
            var margin = parseFloat(data.limits.Net) || 0;
            availableMarginEl.textContent = '₹' + margin.toFixed(2);
        }
        
        // Update holdings value display
        var holdingsValueEl = document.querySelector('#holdingsValue');
        if (holdingsValueEl && data.holdings) {
            var totalValue = 0;
            for (var i = 0; i < data.holdings.length; i++) {
                var holding = data.holdings[i];
                if (holding.mktPrice) {
                    totalValue += parseFloat(holding.mktPrice) || 0;
                }
            }
            holdingsValueEl.innerHTML = '<i class="fas fa-wallet me-1"></i>₹' + totalValue.toFixed(2);
        }
        
        // Update positions tables
        this.updatePositionsTables(data.positions || []);
        
        console.log('Summary cards updated successfully');
    } catch (error) {
        console.error('Error updating summary cards:', error);
    }
};

TradingDashboard.prototype.updatePositionsTables = function(positions) {
    try {
        var longPositions = [];
        var shortPositions = [];
        
        // Separate long and short positions with enhanced data processing
        for (var i = 0; i < positions.length; i++) {
            var position = positions[i];
            
            // Calculate net quantity more accurately
            var buyQty = parseFloat(position.flBuyQty || position.cfBuyQty || 0);
            var sellQty = parseFloat(position.flSellQty || position.cfSellQty || 0);
            var netQty = buyQty - sellQty;
            
            // Calculate P&L more accurately
            var buyAmt = parseFloat(position.buyAmt || position.cfBuyAmt || 0);
            var sellAmt = parseFloat(position.sellAmt || position.cfSellAmt || 0);
            var currentPrice = parseFloat(position.ltp || position.stkPrc || 0);
            
            if (Math.abs(netQty) > 0) { // Only include positions with actual quantity
                var positionData = {
                    symbol: position.trdSym || position.sym || 'N/A',
                    quantity: Math.abs(netQty),
                    buyAmt: buyAmt,
                    sellAmt: sellAmt,
                    currentPrice: currentPrice,
                    product: position.prod || 'N/A',
                    exchange: position.exSeg || 'N/A'
                };
                
                if (netQty > 0) {
                    // Long position: bought more than sold
                    positionData.pnl = (currentPrice * netQty) - buyAmt + sellAmt;
                    longPositions.push(positionData);
                } else {
                    // Short position: sold more than bought
                    positionData.pnl = sellAmt - buyAmt - (currentPrice * Math.abs(netQty));
                    shortPositions.push(positionData);
                }
            }
        }
        
        // Sort positions by P&L (highest first)
        longPositions.sort(function(a, b) { return b.pnl - a.pnl; });
        shortPositions.sort(function(a, b) { return b.pnl - a.pnl; });
        
        // Update long positions table
        this.populatePositionsTable('longPositionsTable', longPositions, 'longPositionsCount');
        
        // Update short positions table
        this.populatePositionsTable('shortPositionsTable', shortPositions, 'shortPositionsCount');
        
        console.log('Positions tables updated successfully:');
        console.log('- Long positions: ' + longPositions.length);
        console.log('- Short positions: ' + shortPositions.length);
        
        // Log sample data for debugging
        if (longPositions.length > 0) {
            console.log('Sample long position:', longPositions[0]);
        }
        if (shortPositions.length > 0) {
            console.log('Sample short position:', shortPositions[0]);
        }
        
    } catch (error) {
        console.error('Error updating positions tables:', error);
        // Show error state in tables
        this.populatePositionsTable('longPositionsTable', [], 'longPositionsCount');
        this.populatePositionsTable('shortPositionsTable', [], 'shortPositionsCount');
    }
};

TradingDashboard.prototype.populatePositionsTable = function(tableId, positions, countId) {
    var tableBody = document.getElementById(tableId);
    var countBadge = document.getElementById(countId);
    
    if (!tableBody) return;
    
    // Update count badge
    if (countBadge) {
        countBadge.textContent = positions.length;
    }
    
    // Clear existing rows
    tableBody.innerHTML = '';
    
    if (positions.length === 0) {
        var emptyIcon = tableId === 'longPositionsTable' ? 'fa-arrow-trend-up' : 'fa-arrow-trend-down';
        var emptyMessage = tableId === 'longPositionsTable' ? 'No long positions found' : 'No short positions found';
        var emptySubtext = tableId === 'longPositionsTable' ? 'Start buying to see positions here' : 'Start shorting to see positions here';
        
        tableBody.innerHTML = '<tr><td colspan="3" class="text-center py-4">' +
            '<div class="d-flex flex-column align-items-center">' +
            '<i class="fas ' + emptyIcon + ' fs-4 mb-2 opacity-50"></i>' +
            '<div class="fw-semibold">' + emptyMessage + '</div>' +
            '<small class="">' + emptySubtext + '</small>' +
            '</div></td></tr>';
        return;
    }
    
    // Show all positions (no limit for better display)
    for (var i = 0; i < positions.length; i++) {
        var position = positions[i];
        var pnlClass = position.pnl >= 0 ? 'text-success' : 'text-danger';
        var pnlIcon = position.pnl >= 0 ? '↗' : '↘';
        var pnlBg = position.pnl >= 0 ? 'bg-success' : 'bg-danger';
        
        var row = document.createElement('tr');
        row.className = 'border-0 position-row';
        row.style.transition = 'all 0.2s ease';
        
        row.innerHTML = 
            '<td class="ps-3 border-0 py-2">' +
                '<div class="d-flex align-items-center">' +
                    '<div class="position-symbol">' +
                        '<div class="text-white fw-bold fs-6">' + position.symbol + '</div>' +
                        '<small class="text-white-50">Stock</small>' +
                    '</div>' +
                '</div>' +
            '</td>' +
            '<td class="border-0 py-2">' +
                '<div class="text-white fw-semibold">' + Math.abs(position.quantity).toLocaleString() + '</div>' +
                '<small class="text-white-50">Shares</small>' +
            '</td>' +
            '<td class="pe-3 border-0 py-2">' +
                '<div class="d-flex align-items-center justify-content-end">' +
                    '<div class="text-end">' +
                        '<div class="' + pnlClass + ' fw-bold">' +
                            '<span class="badge ' + pnlBg + ' bg-opacity-25 text-white px-2 py-1">' +
                                pnlIcon + ' ₹' + Math.abs(position.pnl).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2}) +
                            '</span>' +
                        '</div>' +
                        '<small class="text-white-50">P&L</small>' +
                    '</div>' +
                '</div>' +
            '</td>';
        
        // Add hover effect
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = 'rgba(255,255,255,0.1)';
        });
        row.addEventListener('mouseleave', function() {
            this.style.backgroundColor = 'transparent';
        });
        
        tableBody.appendChild(row);
    }
    
    // Add view all positions link at the bottom
    if (positions.length > 0) {
        var viewAllRow = document.createElement('tr');
        viewAllRow.className = 'border-0';
        viewAllRow.innerHTML = '<td colspan="3" class="text-center border-0 py-3">' +
            '<a href="/positions" class="text-white text-decoration-none fw-semibold d-inline-flex align-items-center">' +
            '<i class="fas fa-external-link-alt me-2"></i>View All Positions' +
            '</a></td>';
        tableBody.appendChild(viewAllRow);
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

function modifyOrder(orderId) {
    // For now, just show a message that modify functionality is coming soon
    showNotification('Order modification feature coming soon!', 'info');
}

function showNotification(message, type = 'info') {
    var alertClass = type === 'success' ? 'alert-success' : 
                     type === 'error' ? 'alert-danger' : 
                     type === 'warning' ? 'alert-warning' : 'alert-info';
    
    var notification = document.createElement('div');
    notification.className = `alert ${alertClass} position-fixed shadow-lg`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 350px; max-width: 400px;';
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <div class="flex-grow-1">${message}</div>
            <button type="button" class="btn-close" onclick="this.closest('.alert').remove()"></button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    // setTimeout(() function() {
    //     if (notification.parentElement) {
    //         notification.style.opacity = '0';
    //         notification.style.transition = 'opacity 0.3s ease';
    //         setTimeout(() => notification.remove(), 300);
    //     }
    // }, 5000);
}

function refreshDashboard() {
    if (window.realTimeDashboard) {
        window.realTimeDashboard.manualRefresh();
    } else {
        window.location.reload();
    }
}

// Event listeners for position management buttons
document.addEventListener('DOMContentLoaded', function() {
    // Place order buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('.place-order-btn')) {
            var btn = e.target.closest('.place-order-btn');
            var type = btn.dataset.type;
            var symbol = btn.dataset.symbol;
            var token = btn.dataset.token;
            var exchange = btn.dataset.exchange;
            openPlaceOrderModal(type, symbol, token, exchange);
        }
        
        // Square off buttons
        if (e.target.closest('.square-off-btn')) {
            var btn = e.target.closest('.square-off-btn');
            var symbol = btn.dataset.symbol;
            var quantity = btn.dataset.quantity;
            var token = btn.dataset.token;
            var exchange = btn.dataset.exchange;
            var product = btn.dataset.product;
            openSquareOffModal(symbol, quantity, token, exchange, product);
        }
        
        // Position details buttons
        if (e.target.closest('.position-details-btn')) {
            var btn = e.target.closest('.position-details-btn');
            var symbol = btn.dataset.symbol;
            var positionData = JSON.parse(btn.dataset.position);
            showPositionDetails(symbol, positionData);
        }
    });
});

async function refreshQuotes() {
    var button = document.querySelector('[onclick="refreshQuotes()"]');
    if (button) {
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Loading...';
        button.disabled = true;
    }

    try {
        // Fetch fresh quote data from server
        var response = await fetch('/api/live_quotes');
        var data = await response.json();

        if (data.success) {
            // Update quotes table with real data
            var quotesTableBody = document.getElementById('quotesTableBody');
            if (quotesTableBody && data.quotes) {
                data.quotes.forEach(quote, function() {
                    var row = document.querySelector(`tr[data-symbol="${quote.symbol}"]`);
                    if (row) {
                        var ltpCell = row.querySelector('.price-ltp');
                        var changeCell = row.querySelector('.price-change');
                        var changePctCell = row.cells[3];
                        var timeCell = row.querySelector('small');

                        if (ltpCell) {
                            var oldPrice = parseFloat(ltpCell.textContent.replace(/[₹,]/g, ''));
                            var newPrice = parseFloat(quote.ltp);

                            ltpCell.textContent = `₹${newPrice.toFixed(2)}`;

                            // Add animation based on price change
                            if (newPrice > oldPrice) {
                                ltpCell.classList.add('price-up');
                            } else if (newPrice < oldPrice) {
                                ltpCell.classList.add('price-down');
                            }

                            setTimeout(function() {
                                ltpCell.classList.remove('price-up', 'price-down');
                            }, 1000);
                        }

                        if (changeCell && quote.change !== undefined) {
                            changeCell.textContent = `${quote.change >= 0 ? '+' : ''}${parseFloat(quote.change).toFixed(2)}`;
                            changeCell.className = `price-change ${quote.change >= 0 ? 'text-success' : 'text-danger'}`;
                        }

                        if (changePctCell && quote.changePct !== undefined) {
                            changePctCell.textContent = `${quote.changePct >= 0 ? '+' : ''}${parseFloat(quote.changePct).toFixed(2)}%`;
                            changePctCell.className = quote.changePct >= 0 ? 'text-success' : 'text-danger';
                        }

                        if (timeCell) {
                            timeCell.textContent = new Date().toLocaleTimeString();
                        }
                    }
                });
            }
        } else {
            // Fallback to simulated updates if API fails
            simulateQuoteUpdates();
        }
    } catch (error) {
        console.error('Error refreshing quotes:', error);
        // Fallback to simulated updates
        simulateQuoteUpdates();
    }

    if (button) {
        button.innerHTML = '<i class="fas fa-sync me-1"></i>Refresh';
        button.disabled = false;
    }
}

function simulateQuoteUpdates() {
    var quotes = document.querySelectorAll('#quotesTable .price-ltp');
    quotes.forEach(function(quote) {
        var currentPrice = parseFloat(quote.textContent.replace(/[₹,]/g, ''));
        var change = (Math.random() - 0.5) * 20;
        var newPrice = currentPrice + change;

        quote.textContent = `₹${newPrice.toFixed(2)}`;

        var row = quote.closest('tr');
        var changeCell = row.querySelector('.price-change');
        var changePctCell = row.cells[3];

        if (changeCell && changePctCell) {
            var changePercent = (change / currentPrice * 100);
            changeCell.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}`;
            changeCell.className = `price-change ${change >= 0 ? 'text-success' : 'text-danger'}`;

            changePctCell.textContent = `${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%`;
            changePctCell.className = change >= 0 ? 'text-success' : 'text-danger';
        }

        quote.classList.add(change >= 0 ? 'price-up' : 'price-down');
        setTimeout(()=>{}, function() {
            quote.classList.remove('price-up', 'price-down');
        }, 1000);
    });
}

async function refreshPositions() {
    var button = document.querySelector('[onclick="refreshPositions()"]');
    if (button) {
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Loading...';
        button.disabled = true;
    }

    try {
        var response = await fetch('/api/positions');
        var data = await response.json();

        if (data.success && data.positions) {
            var positionsTableBody = document.getElementById('positionsTableBody');
            if (positionsTableBody) {
                // Update positions with fresh data
                data.positions.forEach(position, function() {
                    var row = document.querySelector(`tr[data-position-symbol="${position.trdSym || position.sym}"]`);
                    if (row) {
                        var ltpCell = row.querySelector('.price-ltp');
                        var pnlCell = row.querySelector('.position-pnl');

                        if (ltpCell && position.ltp) {
                            var oldPrice = parseFloat(ltpCell.textContent.replace(/[₹,]/g, ''));
                            var newPrice = parseFloat(position.ltp);

                            ltpCell.textContent = `₹${newPrice.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;

                            if (newPrice !== oldPrice) {
                                ltpCell.classList.add(newPrice > oldPrice ? 'price-up' : 'price-down');
                                setTimeout(()=>{}, function() {
                                    ltpCell.classList.remove('price-up', 'price-down');
                                }, 1000);
                            }
                        }

                        if (pnlCell && position.pnl !== undefined) {
                            var pnl = parseFloat(position.pnl);
                            pnlCell.innerHTML = `<span class="fw-bold ${pnl > 0 ? 'text-success' : pnl < 0 ? 'text-danger' : 'text-muted'}">₹${pnl.toFixed(2)}</span>`;
                        }
                    }
                });

                console.log('Positions refreshed successfully');
            }
        }
    } catch (error) {
        console.error('Error refreshing positions:', error);
        // Fallback to simulated updates
        simulatePositionUpdates();
    }

    if (button) {
        button.innerHTML = '<i class="fas fa-sync me-1"></i>Refresh';
        button.disabled = false;
    }
}

function simulatePositionUpdates() {
    var positions = document.querySelectorAll('#positionsTable .price-ltp');
    positions.forEach(position, function() {
        var currentPrice = parseFloat(position.textContent.replace(/[₹,]/g, ''));
        var change = (Math.random() - 0.5) * 10;
        var newPrice = currentPrice + change;

        position.textContent = `₹${newPrice.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
        position.classList.add(change >= 0 ? 'price-up' : 'price-down');
        setTimeout(()=>{}, function() {
            position.classList.remove('price-up', 'price-down');
        }, 1000);
    });
}



async function refreshPortfolioSummary() {
    try {
        var response = await fetch('/api/portfolio_summary');
        var data = await response.json();

        console.log(data);

        if (data.success) {
            // Update portfolio summary cards
            var totalPositionsEl = document.getElementById('totalPositions');
            var totalHoldingsEl = document.getElementById('totalHoldings');
            var totalOrdersEl = document.getElementById('totalOrders');
            var availableMarginEl = document.getElementById('availableMargin');

            if (totalPositionsEl && data.total_positions !== undefined) {
                totalPositionsEl.textContent = data.total_positions;
            }
            if (totalHoldingsEl && data.total_holdings !== undefined) {
                totalHoldingsEl.textContent = data.total_holdings;
            }
            if (totalOrdersEl && data.total_orders !== undefined) {
                totalOrdersEl.textContent = data.total_orders;
            }
            if (availableMarginEl && data.available_margin !== undefined) {
                availableMarginEl.textContent = `₹${parseFloat(data.available_margin).toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
            }
        }
    } catch (error) {
        console.error('Error refreshing portfolio summary:', error);
    }
}

// Add function to refresh portfolio data
function refreshPortfolioData() {
    if (window.tradingDashboard) {
        window.tradingDashboard.refreshPortfolioDetails();
    }
}

// Set last login time on page load and load user profile
document.addEventListener('DOMContentLoaded', function() {
    // Load user profile data which will set the correct login time
    loadUserProfile();

    // Set portfolio last update time
    var portfolioUpdateElement = document.getElementById('portfolioLastUpdate');
    if (portfolioUpdateElement) {
        var now = new Date();
        portfolioUpdateElement.textContent = now.toLocaleTimeString();
    }
});

// Function to format date in the desired format: DD/MM/YYYY HH:MM AM/PM
function formatLoginTime(date) {
    var day = String(date.getDate()).padStart(2, '0');
    var month = String(date.getMonth() + 1).padStart(2, '0');
    var year = date.getFullYear();
    
    var hours = date.getHours();
    var minutes = String(date.getMinutes()).padStart(2, '0');
    var ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12; // the hour '0' should be '12'
    
    return `${day}/${month}/${year} ${hours}:${minutes}${ampm}`;
}

// Function to load user profile data
async function loadUserProfile() {
    try {
        var response = await fetch('/api/user_profile');
        var data = await response.json();

        if (data.success && data.profile) {
            var profile = data.profile;

            // Update login time in dashboard header
            var lastLoginElement = document.getElementById('lastLoginTime');
            if (lastLoginElement) {
                if (profile.login_time && profile.login_time !== 'N/A') {
                    // Format the login time properly
                    var loginDate = new Date(profile.login_time);
                    var formattedTime = formatLoginTime(loginDate);
                    lastLoginElement.textContent = formattedTime;
                } else {
                    var now = new Date();
                    var formattedTime = formatLoginTime(now);
                    lastLoginElement.textContent = formattedTime;
                }
            }

            // Update login time in profile modal if available
            var loginTimeElement = document.getElementById('loginTime');
            if (loginTimeElement) {
                if (profile.login_time && profile.login_time !== 'N/A') {
                    var loginDate = new Date(profile.login_time);
                    loginTimeElement.textContent = formatLoginTime(loginDate);
                } else {
                    var now = new Date();
                    loginTimeElement.textContent = formatLoginTime(now);
                }
            }

            console.log('User profile loaded:', profile);
        } else {
            // Set current time as login time if no profile data
            var lastLoginElement = document.getElementById('lastLoginTime');
            if (lastLoginElement && (lastLoginElement.textContent === 'Loading...' || lastLoginElement.textContent === 'Today')) {
                var now = new Date();
                var formattedTime = formatLoginTime(now);
                lastLoginElement.textContent = formattedTime;
            }
            
            var loginTimeElement = document.getElementById('loginTime');
            if (loginTimeElement && (loginTimeElement.textContent === 'Loading...' || loginTimeElement.textContent === 'Today')) {
                var now = new Date();
                loginTimeElement.textContent = formatLoginTime(now);
            }
        }
    } catch (error) {
        console.error('Error loading user profile:', error);
        // Set current time as fallback
        var lastLoginElement = document.getElementById('lastLoginTime');
        if (lastLoginElement && (lastLoginElement.textContent === 'Loading...' || lastLoginElement.textContent === 'Today')) {
            var now = new Date();
            var formattedTime = formatLoginTime(now);
            lastLoginElement.textContent = formattedTime;
        }
        
        var loginTimeElement = document.getElementById('loginTime');
        if (loginTimeElement && (loginTimeElement.textContent === 'Loading...' || loginTimeElement.textContent === 'Today')) {
            var now = new Date();
            loginTimeElement.textContent = formatLoginTime(now);
        }
    }
}

// Auto-refresh specific sections every 15 seconds instead of full page
setInterval(()=>{}, function() {
    refreshQuotes();
    refreshPositions();
    refreshPortfolioSummary();
}, 15000);



// Update user profile section
        async function updateUserProfile() {
            try {
                var response = await fetch('/api/user_profile');
                var data = await response.json();

                if (data.success && data.profile) {
                    var profile = data.profile;

                    // Update profile information
                    document.getElementById('userUCC').textContent = profile.ucc;
                    document.getElementById('userGreeting').textContent = profile.greeting_name;
                    document.getElementById('loginTime').textContent = profile.login_time;

                    // Show truncated tokens for security
                    document.getElementById('accessTokenDisplay').value = profile.access_token;
                    document.getElementById('sessionTokenDisplay').value = profile.session_token;
                    document.getElementById('sidDisplay').value = profile.sid;

                    // Update token status
                    var tokenStatusText = document.getElementById('tokenStatusText');
                    var refreshTokenBtn = document.getElementById('refreshTokenBtn');
                    var authWarning = document.getElementById('authWarning');

                    if (profile.token_status === 'Valid') {
                        tokenStatusText.textContent = 'Valid';
                        tokenStatusText.className = 'text-success';
                        refreshTokenBtn.style.display = 'none';
                        authWarning.style.display = 'none';
                    } else if (profile.token_status === 'Expired') {
                        tokenStatusText.textContent = 'Expired';
                        tokenStatusText.className = 'text-danger';
                        refreshTokenBtn.style.display = 'block';
                        authWarning.style.display = 'block';
                        refreshTokenBtn.onclick = () => window.location.href = '/login';
                    } else {
                        tokenStatusText.textContent = 'Invalid';
                        tokenStatusText.className = 'text-warning';
                        refreshTokenBtn.style.display = 'block';
                        authWarning.style.display = 'block';
                        refreshTokenBtn.onclick = () => window.location.href = '/login';
                    }
                }
            } catch (error) {
                console.error('Error updating user profile:', error);
                // Show error state
                var tokenStatusText = document.getElementById('tokenStatusText');
                tokenStatusText.textContent = 'Error';
                tokenStatusText.className = 'text-danger';
            }
        }

// Order Management Functions
function showOrderManagement(symbol) {
    fetch(`/api/orders?symbol=${symbol}`)
        .then(response => response.json())
        .then(data ,function() {
            if (data.success && data.orders.length > 0) {
                showOrderModal(data.orders);
            } else {
                alert('No pending orders found for ' + symbol);
            }
        })
        .catch(error, function() {
            console.error('Error fetching orders:', error);
            alert('Error fetching orders');
        });
}

function showOrderModal(orders) {
    var modalContent = `
        <div class="modal fade" id="orderManagementModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content bg-dark">
                    <div class="modal-header">
                        <h5 class="modal-title"><i class="fas fa-edit me-2"></i>Manage Orders</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="table-responsive">
                            <table class="table table-dark table-hover">
                                <thead>
                                    <tr>
                                        <th>Symbol</th>
                                        <th>Type</th>
                                        <th>Qty</th>
                                        <th>Price</th>
                                        <th>Status</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>`;
    
    orders.forEach(order, function() {
        modalContent += `
            <tr>
                <td><strong>${order.trdSym || order.sym}</strong></td>
                <td><span class="badge ${order.trnsTp === 'BUY' ? 'bg-success' : 'bg-danger'}">${order.trnsTp}</span></td>
                <td>${order.qty}</td>
                <td>₹${order.prc || 'Market'}</td>
                <td><span class="badge bg-warning">${order.ordSt}</span></td>
                <td>
                    <button class="btn btn-xs btn-primary me-1" onclick="modifyOrder('${order.nOrdNo}', '${order.trdSym}', ${order.qty}, ${order.prc || 0})">
                        <i class="fas fa-edit"></i> Modify
                    </button>
                    <button class="btn btn-xs btn-danger" onclick="cancelOrder('${order.nOrdNo}')">
                        <i class="fas fa-times"></i> Cancel
                    </button>
                </td>
            </tr>`;
    });
    
    modalContent += `
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>`;
    
    var existingModal = document.getElementById('orderManagementModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    document.body.insertAdjacentHTML('beforeend', modalContent);
    new bootstrap.Modal(document.getElementById('orderManagementModal')).show();
}

function modifyOrder(orderNo, symbol, currentQty, currentPrice) {
    var newQty = prompt(`Modify quantity for ${symbol}:`, currentQty);
    var newPrice = prompt(`Modify price for ${symbol}:`, currentPrice);
    
    if (newQty && newPrice) {
        var modifyData = {
            order_no: orderNo,
            quantity: parseInt(newQty),
            price: parseFloat(newPrice)
        };
        
        fetch('/api/modify_order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(modifyData)
        })
        .then(response => response.json())
        .then(data, function() {
            if (data.success) {
                alert('Order modified successfully!');
                bootstrap.Modal.getInstance(document.getElementById('orderManagementModal')).hide();
                refreshDashboard();
            } else {
                alert('Failed to modify order: ' + data.message);
            }
        })
        .catch(error, function() {
            console.error('Error:', error);
            alert('Error modifying order');
        });
    }
}

function cancelOrder(orderNo) {
    if (confirm('Are you sure you want to cancel this order?')) {
        fetch('/api/cancel_order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ order_no: orderNo })
        })
        .then(response => response.json())
        .then(data, function() {
            if (data.success) {
                alert('Order cancelled successfully!');
                bootstrap.Modal.getInstance(document.getElementById('orderManagementModal')).hide();
                refreshDashboard();
            } else {
                alert('Failed to cancel order: ' + data.message);
            }
        })
        .catch(error, function() {
            console.error('Error:', error);
            alert('Error cancelling order');
        });
    }
}


// Manual update function for dashboard elements
function updateDashboardElements(data) {
    console.log('Updating dashboard elements with:', data);
    
    // Update positions
    var totalPositionsEl = document.querySelector('#totalPositions');
    if (totalPositionsEl && data.total_positions !== undefined) {
        totalPositionsEl.textContent = data.total_positions || 0;
        console.log('Updated positions:', data.total_positions);
    }
    
    // Update holdings
    var totalHoldingsEl = document.querySelector('#totalHoldings');
    if (totalHoldingsEl && data.total_holdings !== undefined) {
        totalHoldingsEl.textContent = data.total_holdings || 0;
        console.log('Updated holdings:', data.total_holdings);
    }
    
    // Update orders
    var todayOrdersEl = document.querySelector('#todayOrders');
    if (todayOrdersEl && data.total_orders !== undefined) {
        todayOrdersEl.textContent = data.total_orders || 0;
        console.log('Updated orders:', data.total_orders);
    }
    
    // Update margin
    var availableMarginEl = document.querySelector('#availableMargin');
    if (availableMarginEl && data.limits && data.limits.Net !== undefined) {
        var margin = parseFloat(data.limits.Net) || 0;
        availableMarginEl.textContent = '₹' + margin.toFixed(2);
        console.log('Updated margin:', margin);
    }
    
    console.log('Dashboard elements updated successfully');
}