function refreshHoldings() {
    var refreshBtn = document.querySelector('button[onclick="refreshHoldings()"]');
    if (refreshBtn) {
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Refreshing...';
        refreshBtn.disabled = true;
    }
    
    fetch('/api/holdings')
        .then(response => response.json())
        .then(function(data) {
            if (data.success) {
                updateHoldingsTable(data.holdings);
                updateHoldingsSummary(data.summary);
                // Recalculate cards after table update
                setTimeout(calculateAndUpdateCards, 100);
                showNotification('Holdings refreshed successfully', 'success');
            } else {
                showNotification('Failed to refresh holdings: ' + data.message, 'error');
            }
        })
        .catch(function(error) {
            console.error('Error refreshing holdings:', error);
            showNotification('Error refreshing holdings', 'error');
        })
        .finally(function() {
            if (refreshBtn) {
                refreshBtn.innerHTML = '<i class="fas fa-sync me-1"></i>Refresh';
                refreshBtn.disabled = false;
            }
        });
}

function buyHolding(symbol) {
    document.getElementById('actionSymbol').value = symbol;
    document.getElementById('actionType').value = 'BUY';
    document.getElementById('actionQuantity').value = '';
    document.getElementById('holdingActionTitle').textContent = 'Buy More: ' + symbol;
    document.getElementById('maxQuantityText').textContent = '';
    new bootstrap.Modal(document.getElementById('holdingActionModal')).show();
}

function sellHolding(symbol, maxQuantity) {
    document.getElementById('actionSymbol').value = symbol;
    document.getElementById('actionType').value = 'SELL';
    document.getElementById('actionQuantity').value = maxQuantity;
    document.getElementById('actionQuantity').max = maxQuantity;
    document.getElementById('holdingActionTitle').textContent = 'Sell Holding: ' + symbol;
    document.getElementById('maxQuantityText').textContent = 'Maximum quantity: ' + maxQuantity;
    new bootstrap.Modal(document.getElementById('holdingActionModal')).show();
}

function submitHoldingAction() {
    var form = document.getElementById('holdingActionForm');
    var formData = new FormData(form);
    
    // Get form values
    var symbol = formData.get('actionSymbol');
    var transactionType = formData.get('actionType');
    var quantity = formData.get('actionQuantity');
    var price = formData.get('actionPrice') || '0';
    var orderType = formData.get('orderType') || 'MKT';
    var productType = formData.get('productType') || 'CNC';
    
    // Validate required fields
    if (!symbol || !quantity) {
        showNotification('Please fill all required fields', 'error');
        return;
    }

    // Handle different order types
    var triggerPrice = "0";
    
    if (orderType === 'MKT' || orderType === 'SL-M') {
        if (orderType === 'SL-M') {
            triggerPrice = price;
            price = "0";
        } else {
            price = "0";
        }
    } else if (orderType === 'L' && (!price || price <= 0)) {
        showNotification('Please enter a valid limit price', 'error');
        return;
    } else if (orderType === 'SL') {
        if (!price || price <= 0) {
            showNotification('Please enter a valid limit price for stop loss order', 'error');
            return;
        }
        triggerPrice = price;
    }
    
    // Prepare order data for client.place_order API
    var orderData = {
        exchange_segment: "nse_cm",
        product: productType,
        price: price,
        order_type: orderType,
        quantity: quantity,
        validity: "DAY",
        trading_symbol: symbol,
        transaction_type: transactionType,
        amo: "NO",
        disclosed_quantity: "0",
        market_protection: "0",
        pf: "N",
        trigger_price: triggerPrice,
        tag: "HOLDINGS_PAGE"
    };

    console.log('Placing order from holdings page:', orderData);

    // Show loading state
    var submitBtn = document.querySelector('#holdingActionModal .btn-primary');
    var originalText = submitBtn.textContent;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Placing Order...';
    submitBtn.disabled = true;
    
    fetch('/api/trading/place_order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderData)
    })
    .then(response => response.json())
    .then(function(data) {
        // Reset button state
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;

        if (data.success) {
            showNotification('Order placed successfully! Order ID: ' + (data.order_id || 'N/A'), 'success');
            bootstrap.Modal.getInstance(document.getElementById('holdingActionModal')).hide();
            refreshHoldings();
        } else {
            showNotification('Failed to place order: ' + data.message, 'error');
        }
    })
    .catch(function(error) {
        // Reset button state
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
        
        console.error('Error:', error);
        showNotification('Error placing order: ' + error.message, 'error');
    });
}

function getQuote(token, exchange) {
    var quoteData = {
        instrument_tokens: [{
            instrument_token: token,
            exchange_segment: exchange
        }],
        quote_type: "ltp"
    };
    
    fetch('/api/quotes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(quoteData)
    })
    .then(response => response.json())
    .then(function(data) {
        if (data.success) {
            console.log('Quote data:', data.data);
            alert('Current LTP: ₹' + (data.data[0] && data.data[0].ltp ? data.data[0].ltp : 'N/A'));
        } else {
            alert('Failed to get quote: ' + data.message);
        }
    })
    .catch(function(error) {
        console.error('Error:', error);
        alert('Error getting quote');
    });
}

function togglePriceField() {
    var orderType = document.getElementById('orderType').value;
    var priceField = document.getElementById('priceField');
    var priceInput = document.getElementById('actionPrice');
    var priceLabel = priceField.querySelector('label');
    
    if (orderType === 'L') {
        priceField.style.display = 'block';
        priceInput.required = true;
        priceLabel.textContent = 'Limit Price (₹)';
    } else if (orderType === 'SL' || orderType === 'SL-M') {
        priceField.style.display = 'block';
        priceInput.required = true;
        priceLabel.textContent = 'Trigger Price (₹)';
    } else {
        priceField.style.display = 'none';
        priceInput.required = false;
        priceInput.value = '';
    }
}

// Auto-refresh holdings every 2 minutes (reduced frequency)
setInterval(refreshHoldings, 120000);

function updateHoldingsTable(holdings) {
    var tableBody = document.querySelector('table tbody');
    if (!tableBody) return;
    
    if (!holdings || holdings.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center py-5">
                    <i class="fas fa-walvar fa-3x text-muted mb-3"></i>
                    <h4 class="text-muted">No Holdings Found</h4>
                    <p class="text-muted">You don't have any holdings in your portfolio.</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tableBody.innerHTML = '';
    
    holdings.forEach(holding, function() {
        var row = document.createElement('tr');
        var quantity = parseFloat(holding.quantity || 0);
        var avgPrice = parseFloat(holding.averagePrice || 0);
        var ltp = parseFloat(holding.closingPrice || 0);
        var investedValue = parseFloat(holding.holdingCost || 0);
        var marketValue = parseFloat(holding.mktValue || 0);
        var pnl = marketValue - investedValue;
        var pnlPercent = investedValue > 0 ? (pnl / investedValue * 100) : 0;
        var dayChange = avgPrice > 0 ? ((ltp - avgPrice) / avgPrice * 100) : 0;
        
        row.innerHTML = `
            <td>
                <strong>${holding.displaySymbol || holding.symbol || 'N/A'}</strong>
                ${holding.instrumentName ? `<br><small class="text-muted">${holding.instrumentName}</small>` : ''}
            </td>
            <td>
                <span class="badge bg-info">${holding.exchangeSegment || 'N/A'}</span>
            </td>
            <td class="text-info">${quantity}</td>
            <td>₹${avgPrice.toFixed(2)}</td>
            <td>₹${ltp.toFixed(2)}</td>
            <td>₹${marketValue.toFixed(2)}</td>
            <td>
                <span class="${pnl >= 0 ? 'text-success' : 'text-danger'}">
                    ₹${pnl.toFixed(2)}
                    ${investedValue > 0 ? `<br><small>(${pnlPercent.toFixed(2)}%)</small>` : ''}
                </span>
            </td>
            <td>
                <span class="${dayChange >= 0 ? 'text-success' : 'text-danger'}">
                    ${dayChange.toFixed(2)}%
                </span>
            </td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-success btn-sm" onclick="buyHolding('${holding.displaySymbol || holding.symbol}')">
                        <i class="fas fa-plus"></i> Buy
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="sellHolding('${holding.displaySymbol || holding.symbol}', ${holding.sellableQuantity || holding.quantity || 0})">
                        <i class="fas fa-minus"></i> Sell
                    </button>
                    <button class="btn btn-info btn-sm" onclick="getQuote('${holding.instrumentToken}', '${holding.exchangeSegment}')">
                        <i class="fas fa-chart-line"></i>
                    </button>
                </div>
            </td>
        `;
        tableBody.appendChild(row);
    });
}

function updateHoldingsSummary(summary) {
    var totalHoldingsEl = document.getElementById('totalHoldingsCount');
    var totalInvestedEl = document.getElementById('totalInvested');
    var currentValueEl = document.getElementById('currentValue');
    var totalPnlEl = document.getElementById('totalPnl');
    
    if (totalHoldingsEl) totalHoldingsEl.textContent = summary.total_holdings || 0;
    if (totalInvestedEl) totalInvestedEl.textContent = `₹${(summary.total_invested || 0).toFixed(2)}`;
    if (currentValueEl) {
        currentValueEl.textContent = `₹${(summary.current_value || 0).toFixed(2)}`;
        var pnl = (summary.current_value || 0) - (summary.total_invested || 0);
        if (totalPnlEl) {
            totalPnlEl.textContent = `${pnl >= 0 ? '+' : ''}₹${pnl.toFixed(2)}`;
            totalPnlEl.className = `mb-0 ${pnl >= 0 ? 'text-success' : 'text-danger'}`;
        }
    }
}

function showNotification(message, type) {
    if (type === undefined) type = 'info';
    // Create toast notification
    var toast = document.createElement('div');
    toast.className = 'alert alert-' + type + ' alert-dismissible fade show position-fixed';
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = message + '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
    
    document.body.appendChild(toast);
    
    // Auto-remove after 3 seconds
    setTimeout(function() {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 3000);
}

// Table sorting functionality
var sortState = {
    column: null,
    direction: 'asc'
};

function sortTable(column) {
    var table = document.getElementById('holdingsTable');
    var tbody = document.getElementById('holdingsTableBody');
    
    if (!tbody) return;
    
    var rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Toggle sort direction
    if (sortState.column === column) {
        sortState.direction = sortState.direction === 'asc' ? 'desc' : 'asc';
    } else {
        sortState.column = column;
        sortState.direction = 'asc';
    }
    
    // Sort rows based on column
    rows.sort(function(a, b) {
        var aValue, bValue;
        
        switch (column) {
            case 'symbol':
                aValue = a.dataset.symbol || '';
                bValue = b.dataset.symbol || '';
                break;
            case 'exchange':
                aValue = a.dataset.exchange || '';
                bValue = b.dataset.exchange || '';
                break;
            case 'quantity':
                aValue = parseFloat(a.dataset.quantity) || 0;
                bValue = parseFloat(b.dataset.quantity) || 0;
                break;
            case 'avgPrice':
                aValue = parseFloat(a.dataset.avgPrice) || 0;
                bValue = parseFloat(b.dataset.avgPrice) || 0;
                break;
            case 'ltp':
                aValue = parseFloat(a.dataset.ltp) || 0;
                bValue = parseFloat(b.dataset.ltp) || 0;
                break;
            case 'marketValue':
                aValue = parseFloat(a.dataset.marketValue) || 0;
                bValue = parseFloat(b.dataset.marketValue) || 0;
                break;
            case 'pnl':
                aValue = parseFloat(a.dataset.pnl) || 0;
                bValue = parseFloat(b.dataset.pnl) || 0;
                break;
            case 'dayChange':
                aValue = parseFloat(a.dataset.dayChange) || 0;
                bValue = parseFloat(b.dataset.dayChange) || 0;
                break;
            default:
                return 0;
        }
        
        // Compare values
        var result;
        if (typeof aValue === 'string') {
            result = aValue.localeCompare(bValue);
        } else {
            result = aValue - bValue;
        }
        
        return sortState.direction === 'asc' ? result : -result;
    });
    
    // Update sort indicators
    updateSortIndicators(column, sortState.direction);
    
    // Rebuild table with sorted rows
    tbody.innerHTML = '';
    rows.forEach(function(row) {
        tbody.appendChild(row);
    });
    
    // Update sort button text
    var sortBtn = document.getElementById('sortSymbolBtn');
    if (sortBtn && column === 'symbol') {
        var icon = sortState.direction === 'asc' ? 'fa-sort-alpha-down' : 'fa-sort-alpha-up';
        var text = sortState.direction === 'asc' ? 'Sort A-Z' : 'Sort Z-A';
        sortBtn.innerHTML = '<i class="fas ' + icon + ' me-1"></i>' + text;
    }
}

function updateSortIndicators(activeColumn, direction) {
    // Hide all sort indicators
    var indicators = document.querySelectorAll('[id^="sort-"]');
    indicators.forEach(function(indicator) {
        indicator.classList.add('d-none');
    });
    
    // Show active indicator
    var activeIndicator = document.getElementById('sort-' + activeColumn + '-' + direction);
    if (activeIndicator) {
        activeIndicator.classList.remove('d-none');
    }
    
    // Update sort icons in headers
    var sortIcons = document.querySelectorAll('.sortable .fa-sort');
    sortIcons.forEach(function(icon) {
        icon.classList.remove('text-primary');
        icon.classList.add('text-muted');
    });
    
    var activeHeader = document.querySelector('.sortable[onclick*="' + activeColumn + '"] .fa-sort');
    if (activeHeader) {
        activeHeader.classList.remove('text-muted');
        activeHeader.classList.add('text-primary');
    }
}

// Enhanced refresh function with 4-card updates
function updateHoldingsSummary(summary) {
    var totalHoldingsEl = document.getElementById('totalHoldingsCount');
    var totalInvestedEl = document.getElementById('totalInvested');
    var currentValueEl = document.getElementById('currentValue');
    var totalPnlEl = document.getElementById('totalPnl');
    
    if (summary) {
        var totalHoldings = summary.total_holdings || 0;
        var totalInvested = summary.total_invested || 0;
        var currentValue = summary.current_value || 0;
        var totalPnl = currentValue - totalInvested;
        var pnlPercentage = totalInvested > 0 ? (totalPnl / totalInvested * 100) : 0;
        
        // Update Total Holdings
        if (totalHoldingsEl) {
            totalHoldingsEl.textContent = totalHoldings;
        }
        
        // Update Total Invested
        if (totalInvestedEl) {
            totalInvestedEl.textContent = '₹' + Math.round(totalInvested).toLocaleString('en-IN');
        }
        
        // Update Current Value
        if (currentValueEl) {
            currentValueEl.textContent = '₹' + Math.round(currentValue).toLocaleString('en-IN');
        }
        
        // Update Total P&L
        if (totalPnlEl) {
            totalPnlEl.textContent = (totalPnl >= 0 ? '+' : '') + '₹' + Math.round(Math.abs(totalPnl)).toLocaleString('en-IN');
            
            // Update the P&L card gradient dynamically
            var pnlCard = totalPnlEl.closest('.card');
            if (pnlCard) {
                var gradient = totalPnl >= 0 
                    ? 'linear-gradient(135deg, #166534, #22c55e)' 
                    : 'linear-gradient(135deg, #991b1b, #ef4444)';
                pnlCard.style.background = gradient;
            }
        }
        
        console.log('Holdings summary updated:', {
            holdings: totalHoldings,
            invested: totalInvested,
            current: currentValue,
            pnl: totalPnl
        });
    }
}

// Calculate and update card values from table data
function calculateAndUpdateCards() {
    var tableBody = document.getElementById('holdingsTableBody');
    if (!tableBody) return;
    
    var rows = tableBody.querySelectorAll('tr[data-symbol]');
    var totalHoldings = rows.length;
    var totalInvested = 0;
    var totalCurrent = 0;
    
    rows.forEach(function(row) {
        var invested = parseFloat(row.dataset.avgPrice || 0) * parseFloat(row.dataset.quantity || 0);
        var current = parseFloat(row.dataset.marketValue || 0);
        
        totalInvested += invested;
        totalCurrent += current;
    });
    
    var totalPnl = totalCurrent - totalInvested;
    
    // Update cards
    var totalHoldingsEl = document.getElementById('totalHoldingsCount');
    var totalInvestedEl = document.getElementById('totalInvested');
    var currentValueEl = document.getElementById('currentValue');
    var totalPnlEl = document.getElementById('totalPnl');
    
    if (totalHoldingsEl) {
        totalHoldingsEl.textContent = totalHoldings;
    }
    
    if (totalInvestedEl) {
        totalInvestedEl.textContent = '₹' + Math.round(totalInvested).toLocaleString('en-IN');
    }
    
    if (currentValueEl) {
        currentValueEl.textContent = '₹' + Math.round(totalCurrent).toLocaleString('en-IN');
    }
    
    if (totalPnlEl) {
        totalPnlEl.textContent = (totalPnl >= 0 ? '+' : '') + '₹' + Math.round(Math.abs(totalPnl)).toLocaleString('en-IN');
        
        // Update P&L card color
        var pnlCard = totalPnlEl.closest('.card');
        if (pnlCard) {
            var gradient = totalPnl >= 0 
                ? 'linear-gradient(135deg, #166534, #22c55e)' 
                : 'linear-gradient(135deg, #991b1b, #ef4444)';
            pnlCard.style.background = gradient;
        }
    }
    
    console.log('Cards updated:', {
        holdings: totalHoldings,
        invested: totalInvested,
        current: totalCurrent,
        pnl: totalPnl
    });
}

// Initialize default sort by symbol A-Z and calculate cards
document.addEventListener('DOMContentLoaded', function() {
    // Wait a moment for the table to load, then sort and calculate
    setTimeout(function() {
        sortTable('symbol');
        calculateAndUpdateCards();
    }, 500);
    
    // Also update cards when page loads
    setTimeout(calculateAndUpdateCards, 1000);
});