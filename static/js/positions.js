var positionsData = [];
var refreshInterval = null;
var currentSortColumn = '';
var currentSortDirection = 'asc';
var currentFilter = 'ALL';

// Load positions when page loads
document.addEventListener('DOMContentLoaded', function() {
    showLoadingSkeleton();
    loadPositionsData();
    // Auto-refresh every 30 seconds
    refreshInterval = setInterval(loadPositionsData, 30000);
});

function showLoadingSkeleton() {
    document.getElementById('loadingSkeleton').style.display = 'block';
    document.getElementById('tableContent').style.display = 'none';
}

function hideLoadingSkeleton() {
    document.getElementById('loadingSkeleton').style.display = 'none';
    document.getElementById('tableContent').style.display = 'block';
}

// Clear interval when page unloads
window.addEventListener('beforeunload', function() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});

async function loadPositionsData() {
    try {
        console.log('Fetching positions data...');
        var response = await fetch('/api/positions', {
            credentials: 'same-origin', // Include cookies
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        console.log('Response status:', response.status);
        var data = await response.json();
        console.log('Response data:', data);

        if (data.success) {
            positionsData = data.positions || [];
            console.log('Positions loaded:', positionsData.length, 'positions');
            hideLoadingSkeleton();
            updatePositionsTable(positionsData);
            updatePositionsSummary(positionsData);
        } else {
            hideLoadingSkeleton();
            console.error('Failed to load positions:', data.error || data.message);
            if (data.error && data.error.includes('Not authenticated')) {
                console.log('User not authenticated, showing login message');
                showAuthenticationError();
            } else {
                showNoPositionsMessage();
            }
        }
    } catch (error) {
        console.error('Error loading positions:', error);
        hideLoadingSkeleton();
        showNoPositionsMessage();
    }
}

function updatePositionsTable(positions) {
    var tableBody = document.getElementById('positionsTableBody');

    if (!positions || positions.length === 0) {
        showNoPositionsMessage();
        return;
    }

    var tableHTML = '';
    var displayPositions = currentFilter === 'ALL' ? positions : filterPositionsByType(positions, currentFilter);

    displayPositions.forEach(function(position) {
        console.log('Processing position:', position);
        
        var symbol = position.trdSym || position.sym || position.tradingSymbol || 'N/A';
        var product = position.prod || position.product || 'N/A';
        var exchange = position.exSeg || position.exchange || 'N/A';
        
        // Handle quantity fields - Kotak Neo API uses specific field names
        var buyQty = position.flBuyQty || position.buyQty || position.brdLtQty || '0';
        var sellQty = position.flSellQty || position.sellQty || '0';
        var netQty = position.flNetQty || position.netQty || (parseInt(buyQty) - parseInt(sellQty)) || '0';
        
        // Handle amount fields
        var buyAmt = position.buyAmt || position.flBuyAmt || '0';
        var sellAmt = position.sellAmt || position.flSellAmt || '0';
        
        // Calculate P&L - may need to be calculated from price differences
        var pnl = position.pnl || position.flPnl || '0';
        
        var position_type = parseInt(netQty) > 0 ? 'LONG' : parseInt(netQty) < 0 ? 'SHORT' : 'FLAT';

        // Format amounts
        var formattedBuyAmt = parseFloat(buyAmt) || 0;
        var formattedSellAmt = parseFloat(sellAmt) || 0;
        var formattedPnl = parseFloat(pnl) || 0;

        // Position type badge styling
        var positionClass = 'bg-secondary';
        if (position_type === 'LONG') {
            positionClass = 'bg-success';
        } else if (position_type === 'SHORT') {
            positionClass = 'bg-danger';
        }

        // P&L styling
        var pnlClass = formattedPnl >= 0 ? 'text-success' : 'text-danger';
        var pnlIcon = formattedPnl >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';

        tableHTML += `
            <tr data-position-symbol="${symbol}">
                <td class="px-4 py-3">
                    <div class="d-flex align-items-center">
                        <div class="me-3" style="width: 40px; height: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 0.8rem;">
                            ${symbol.substring(0, 2)}
                        </div>
                        <div>
                            <div class="fw-bold text-white">${symbol}</div>
                            <small class="text-white-50">${exchange}</small>
                        </div>
                    </div>
                </td>
                <td class="px-4 py-3">
                    <span class="badge bg-info position-badge">${product}</span>
                </td>
                <td class="px-4 py-3">
                    <div class="fw-bold text-white">${netQty}</div>
                    <small class="text-white-50">Net Quantity</small>
                </td>
                <td class="px-4 py-3">
                    <div class="text-success fw-bold">₹${formattedBuyAmt.toFixed(2)}</div>
                    <small class="text-white-50">${buyQty} qty</small>
                </td>
                <td class="px-4 py-3">
                    <div class="text-danger fw-bold">₹${formattedSellAmt.toFixed(2)}</div>
                    <small class="text-white-50">${sellQty} qty</small>
                </td>
                <td class="px-4 py-3">
                    <div class="d-flex align-items-center">
                        <i class="fas ${pnlIcon} me-2 ${pnlClass}"></i>
                        <div>
                            <div class="${pnlClass} fw-bold">₹${formattedPnl.toFixed(2)}</div>
                            <small class="text-white-50">${formattedPnl >= 0 ? 'Profit' : 'Loss'}</small>
                        </div>
                    </div>
                </td>
                <td class="px-4 py-3">
                    <span class="badge ${positionClass} position-badge">${position_type}</span>
                </td>
                <td class="px-4 py-3">
                    <div class="d-flex gap-2">
                        <button class="action-btn btn btn-primary" onclick="showPlaceOrderModal('${symbol}', '${exchange}')" title="Place Order">
                            <i class="fas fa-plus"></i>
                        </button>
                        <button class="action-btn btn btn-info" onclick="viewPositionDetails('${symbol}')" title="View Details">
                            <i class="fas fa-info"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });

    tableBody.innerHTML = tableHTML;
    document.getElementById('positionsTableCount').textContent = displayPositions.length;

    // Add update animation
    tableBody.classList.add('data-updated');
    setTimeout(function() {
        tableBody.classList.remove('data-updated');
    }, 1000);
}

function updatePositionsSummary(positions) {
    var totalPositions = positions.length;
    var longPositions = 0;
    var shortPositions = 0;
    var totalPnl = 0;
    var longValue = 0;
    var shortValue = 0;

    positions.forEach(function(position) {
        var netQty = parseFloat(position.netQty || position.flNetQty || 0);
        var pnl = parseFloat(position.pnl || position.flPnl || 0);

        totalPnl += pnl;

        if (netQty > 0) {
            longPositions++;
            longValue += Math.abs(pnl);
        } else if (netQty < 0) {
            shortPositions++;
            shortValue += Math.abs(pnl);
        }
    });

    // Update summary cards
    document.getElementById('totalPositionsCount').textContent = totalPositions;
    document.getElementById('longPositionsCount').textContent = longPositions + ' positions';
    document.getElementById('shortPositionsCount').textContent = shortPositions + ' positions';
    document.getElementById('longPositionsValue').textContent = '₹' + longValue.toFixed(2);
    document.getElementById('shortPositionsValue').textContent = '₹' + shortValue.toFixed(2);
    document.getElementById('totalPnlValue').textContent = '₹' + totalPnl.toFixed(2);

    // Update P&L badge
    var pnlBadge = document.getElementById('pnlBadge');
    var pnlClass = totalPnl >= 0 ? 'bg-success' : 'bg-danger';
    var pnlPercentage = totalPnl >= 0 ? '+' + (totalPnl * 0.1).toFixed(2) + '%' : (totalPnl * 0.1).toFixed(2) + '%';

    pnlBadge.className = 'badge ' + pnlClass;
    pnlBadge.textContent = pnlPercentage;

    // Update total P&L color
    var totalPnlElement = document.getElementById('totalPnlValue');
    totalPnlElement.className = totalPnl >= 0 ? 'text-success mb-1' : 'text-danger mb-1';
}

function showNoPositionsMessage() {
    var tableBody = document.getElementById('positionsTableBody');
    tableBody.innerHTML = `
        <tr>
            <td colspan="8" class="text-center py-5">
                <div class="empty-state">
                    <i class="fas fa-chart-line mb-4" style="font-size: 4rem; color: rgba(102, 126, 234, 0.3);"></i>
                    <h4 class="text-white-50 mb-3">No Positions Found</h4>
                    <p class="text-white-50 mb-4">You don't have any open positions yet. Start trading to see your portfolio here.</p>
                    <button class="btn btn-primary px-4 py-2" onclick="window.location.href='/dashboard'" style="border-radius: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none;">
                        <i class="fas fa-plus me-2"></i>Start Trading
                    </button>
                </div>
            </td>
        </tr>
    `;

    // Reset summary counts
    document.getElementById('totalPositionsCount').textContent = '0';
    document.getElementById('longPositionsCount').textContent = '0 positions';
    document.getElementById('shortPositionsCount').textContent = '0 positions';
    document.getElementById('longPositionsValue').textContent = '₹0.00';
    document.getElementById('shortPositionsValue').textContent = '₹0.00';
    document.getElementById('totalPnlValue').textContent = '₹0.00';
    document.getElementById('positionsTableCount').textContent = '0';
}

function showAuthenticationError() {
    var tableBody = document.getElementById('positionsTableBody');
    tableBody.innerHTML = `
        <tr>
            <td colspan="8" class="text-center py-5">
                <div class="empty-state">
                    <i class="fas fa-lock mb-4" style="font-size: 4rem; color: rgba(255, 193, 7, 0.6);"></i>
                    <h4 class="text-warning mb-3">Authentication Required</h4>
                    <p class="text-white-50 mb-4">Please log in to your Kotak Neo account to view your positions.</p>
                    <button class="btn btn-warning px-4 py-2" onclick="window.location.href='/trading-account/login'" style="border-radius: 12px;">
                        <i class="fas fa-sign-in-alt me-2"></i>Login to Kotak Neo
                    </button>
                </div>
            </td>
        </tr>
    `;

    // Reset summary counts
    document.getElementById('totalPositionsCount').textContent = '0';
    document.getElementById('longPositionsCount').textContent = '0 positions';
    document.getElementById('shortPositionsCount').textContent = '0 positions';
    document.getElementById('longPositionsValue').textContent = '₹0.00';
    document.getElementById('shortPositionsValue').textContent = '₹0.00';
    document.getElementById('totalPnlValue').textContent = '₹0.00';
    document.getElementById('positionsTableCount').textContent = '0';
}

function filterPositionsByType(positions, type) {
    if (type === 'ALL') return positions;

    return positions.filter(function(position) {
        var netQty = parseFloat(position.netQty || position.flNetQty || 0);
        if (type === 'LONG') return netQty > 0;
        if (type === 'SHORT') return netQty < 0;
        return true;
    });
}

function refreshPositions() {
    var button = document.querySelector('[onclick="refreshPositions()"]');
    var originalHtml = button.innerHTML;

    button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Refreshing...';
    button.disabled = true;

    loadPositionsData().finally(function() {
        button.innerHTML = originalHtml;
        button.disabled = false;
    });
}

function setAutoRefresh(seconds) {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }

    if (seconds > 0) {
        refreshInterval = setInterval(loadPositionsData, seconds * 1000);
        document.getElementById('refreshInterval').textContent = seconds + 's';
    } else {
        document.getElementById('refreshInterval').textContent = 'Off';
    }
}

function sortTable(column) {
    if (currentSortColumn === column) {
        currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        currentSortColumn = column;
        currentSortDirection = 'asc';
    }

    // Clear all sort icons
    document.querySelectorAll('.sort-icon').forEach(icon => {
        icon.className = 'fas fa-sort ms-1 sort-icon';
    });
    
    // Set active sort icon
    const sortIcon = document.getElementById(`sort-${column}`);
    if (sortIcon) {
        sortIcon.className = `fas fa-sort-${currentSortDirection === 'asc' ? 'up' : 'down'} ms-1 sort-icon active`;
    }

    positionsData.sort(function(a, b) {
        var aVal, bVal;

        switch(column) {
            case 'symbol':
                aVal = (a.trdSym || a.sym || '').toLowerCase();
                bVal = (b.trdSym || b.sym || '').toLowerCase();
                break;
            case 'product':
                aVal = (a.prod || '').toLowerCase();
                bVal = (b.prod || '').toLowerCase();
                break;
            case 'exchange':
                aVal = (a.exSeg || '').toLowerCase();
                bVal = (b.exSeg || '').toLowerCase();
                break;
            case 'buyQty':
                aVal = parseFloat(a.buyQty || 0);
                bVal = parseFloat(b.buyQty || 0);
                break;
            case 'sellQty':
                aVal = parseFloat(a.sellQty || 0);
                bVal = parseFloat(b.sellQty || 0);
                break;
            case 'netQty':
                aVal = parseFloat(a.netQty || 0);
                bVal = parseFloat(b.netQty || 0);
                break;
            case 'buyAmt':
                aVal = parseFloat(a.buyAmt || 0);
                bVal = parseFloat(b.buyAmt || 0);
                break;
            case 'sellAmt':
                aVal = parseFloat(a.sellAmt || 0);
                bVal = parseFloat(b.sellAmt || 0);
                break;
            case 'pnl':
                aVal = parseFloat(a.pnl || 0);
                bVal = parseFloat(b.pnl || 0);
                break;
            default:
                return 0;
        }

        if (typeof aVal === 'string' && typeof bVal === 'string') {
            return currentSortDirection === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        } else {
            return currentSortDirection === 'asc' ? aVal - bVal : bVal - aVal;
        }
    });

    updatePositionsTable(positionsData);
}

function showPlaceOrderModal(symbol, exchange) {
    document.getElementById('orderSymbol').value = symbol;
    document.getElementById('orderExchange').value = exchange;

    var modal = new bootstrap.Modal(document.getElementById('placeOrderModal'));
    modal.show();
}

function handleOrderTypeChange() {
    var orderType = document.getElementById('orderType').value;
    var priceField = document.getElementById('orderPrice');
    var triggerPriceField = document.getElementById('orderTriggerPrice');

    if (orderType === 'MKT' || orderType === 'SL-M') {
        priceField.disabled = true;
        priceField.required = false;
    } else {
        priceField.disabled = false;
        priceField.required = true;
    }

    if (orderType === 'SL' || orderType === 'SL-M') {
        triggerPriceField.disabled = false;
        triggerPriceField.required = true;
    } else {
        triggerPriceField.disabled = true;
        triggerPriceField.required = false;
    }
}

function submitPlaceOrder() {
    var form = document.getElementById('placeOrderForm');
    var formData = new FormData(form);
    var orderData = Object.fromEntries(formData.entries());

    fetch('/api/place_order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Order placed successfully!');
            bootstrap.Modal.getInstance(document.getElementById('placeOrderModal')).hide();
            loadPositionsData();
        } else {
            alert('Failed to place order: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error placing order');
    });
}

function viewPositionDetails(symbol) {
    var position = positionsData.find(p => (p.trdSym || p.sym) === symbol);

    if (position) {
        // Helper function to safely set element content
        function safeSetContent(elementId, content) {
            var element = document.getElementById(elementId);
            if (element) {
                element.textContent = content;
            } else {
                console.warn('Element not found:', elementId);
            }
        }

        // Helper function to safely set element class
        function safeSetClass(elementId, className) {
            var element = document.getElementById(elementId);
            if (element) {
                element.className = className;
            } else {
                console.warn('Element not found:', elementId);
            }
        }

        // Populate modal with position details
        safeSetContent('detailTradingSymbol', position.trdSym || position.sym || 'N/A');
        safeSetContent('detailExchange', position.exSeg || 'N/A');
        safeSetContent('detailProduct', position.prod || 'N/A');
        safeSetContent('detailToken', position.tok || 'N/A');
        
        var buyQty = position.flBuyQty || position.buyQty || '0';
        var sellQty = position.flSellQty || position.sellQty || '0';
        var netQty = position.flNetQty || position.netQty || (parseInt(buyQty) - parseInt(sellQty)) || '0';
        var positionType = parseInt(netQty) > 0 ? 'LONG' : parseInt(netQty) < 0 ? 'SHORT' : 'FLAT';
        
        safeSetContent('detailNetQty', netQty);
        safeSetContent('detailBuyQty', buyQty);
        safeSetContent('detailSellQty', sellQty);
        
        var positionBadge = document.getElementById('detailPositionType');
        if (positionBadge) {
            positionBadge.textContent = positionType;
            positionBadge.className = 'badge ' + (positionType === 'LONG' ? 'bg-success' : positionType === 'SHORT' ? 'bg-danger' : 'bg-secondary');
        }
        
        var buyAmt = parseFloat(position.buyAmt || position.flBuyAmt || '0');
        var sellAmt = parseFloat(position.sellAmt || position.flSellAmt || '0');
        var pnl = parseFloat(position.pnl || position.flPnl || '0');
        var currentPrice = parseFloat(position.stkPrc || position.currentPrice || '0');
        
        safeSetContent('detailBuyAmt', '₹' + buyAmt.toFixed(2));
        safeSetContent('detailSellAmt', '₹' + sellAmt.toFixed(2));
        safeSetContent('detailCurrentPrice', '₹' + currentPrice.toFixed(2));
        
        var pnlElement = document.getElementById('detailPnl');
        if (pnlElement) {
            pnlElement.textContent = '₹' + pnl.toFixed(2);
            pnlElement.className = pnl >= 0 ? 'text-success' : 'text-danger';
        }
        
        safeSetContent('detailExpiry', position.expDt || position.exp || position.expiry || 'N/A');
        safeSetContent('detailLotSize', position.lotSz || 'N/A');
        safeSetContent('detailLastUpdated', position.hsUpTm || position.updRecvTm || 'N/A');
        
        // Show modal
        var modalElement = document.getElementById('positionDetailsModal');
        if (modalElement && typeof bootstrap !== 'undefined') {
            var modal = new bootstrap.Modal(modalElement);
            modal.show();
        } else {
            console.error('Position details modal not found or Bootstrap not loaded');
            // Fallback: show position info in an alert
            alert('Position Details:\n' + 
                  'Symbol: ' + (position.trdSym || position.sym || 'N/A') + '\n' +
                  'Net Quantity: ' + netQty + '\n' +
                  'P&L: ₹' + pnl.toFixed(2));
        }
    }
}

function openTradeFromDetails() {
    var symbol = document.getElementById('detailTradingSymbol').textContent;
    var exchange = document.getElementById('detailExchange').textContent;
    
    // Close details modal
    bootstrap.Modal.getInstance(document.getElementById('positionDetailsModal')).hide();
    
    // Open trade modal
    setTimeout(() => {
        showPlaceOrderModal(symbol, exchange);
    }, 300);
}

// Expose functions globally
window.refreshPositions = refreshPositions;
window.setAutoRefresh = setAutoRefresh;
window.sortTable = sortTable;
window.filterPositionsByType = function(type) {
    currentFilter = type;
    
    // Update filter button states
    document.querySelectorAll('.filter-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    if (type === 'ALL') {
        document.getElementById('filterAll').classList.add('active');
    } else if (type === 'LONG') {
        document.getElementById('filterLong').classList.add('active');
    } else if (type === 'SHORT') {
        document.getElementById('filterShort').classList.add('active');
    }
    
    if (positionsData && positionsData.length > 0) {
        updatePositionsTable(positionsData);
    }
};
window.showPlaceOrderModal = showPlaceOrderModal;
window.handleOrderTypeChange = handleOrderTypeChange;
window.submitPlaceOrder = submitPlaceOrder;
window.viewPositionDetails = viewPositionDetails;
window.openTradeFromDetails = openTradeFromDetails;