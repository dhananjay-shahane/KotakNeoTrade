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
                // Store holdings data globally for price lookup
                window.holdingsData = data;
                updateHoldingsTable(data.holdings);
                updateHoldingsSummary(data.summary);
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
    showHoldingTradeModal(symbol, null, 'BUY');
}

function sellHolding(symbol, maxQuantity) {
    showHoldingTradeModal(symbol, maxQuantity, 'SELL');
}

function showHoldingTradeModal(symbol, maxQuantity, tradeType) {
    var modalTitle = tradeType === 'BUY' ? 'Buy Holdings' : 'Sell Holdings';
    var iconClass = tradeType === 'BUY' ? 'fas fa-plus' : 'fas fa-minus';
    document.getElementById('holdingActionTitle').innerHTML = '<i class="' + iconClass + ' me-2"></i>' + modalTitle;
    
    document.getElementById('actionSymbol').value = symbol;
    document.getElementById('actionType').value = tradeType;
    document.getElementById('actionQuantity').value = tradeType === 'SELL' ? maxQuantity : 1;
    
    if (tradeType === 'SELL' && maxQuantity) {
        document.getElementById('actionQuantity').max = maxQuantity;
        document.getElementById('maxQuantityText').textContent = 'Maximum quantity: ' + maxQuantity;
    } else {
        document.getElementById('actionQuantity').removeAttribute('max');
        document.getElementById('maxQuantityText').textContent = '';
    }
    
    // Find current market price from holdings data
    var currentPrice = '';
    if (window.holdingsData && window.holdingsData.holdings) {
        var holding = window.holdingsData.holdings.find(function(h) {
            return h.displaySymbol === symbol || h.symbol === symbol;
        });
        
        if (holding) {
            // Use closingPrice (current market price) or mktValue/quantity as fallback
            var marketPrice = parseFloat(holding.closingPrice || (holding.mktValue / holding.quantity) || holding.averagePrice || 0);
            if (marketPrice > 0) {
                currentPrice = marketPrice.toFixed(2);
                console.log('Found market price for', symbol, ':', currentPrice);
            }
        }
    }
    
    document.getElementById('orderType').value = 'L';
    document.getElementById('productType').value = 'CNC';
    document.getElementById('validityType').value = 'DAY';
    document.getElementById('triggerPrice').value = currentPrice; // Set trigger price too
    document.getElementById('actionPrice').value = currentPrice; // Set current market price
    
    toggleHoldingPriceFields();
    
    var modal = new bootstrap.Modal(document.getElementById('holdingActionModal'));
    modal.show();
}

function toggleHoldingPriceFields() {
    var orderType = document.getElementById('orderType').value;
    var priceField = document.getElementById('actionPrice');
    var triggerField = document.getElementById('triggerPrice');
    
    if (orderType === 'MKT') {
        priceField.disabled = true;
        priceField.value = 0;
        triggerField.disabled = true;
        triggerField.value = 0;
    } else if (orderType === 'L') {
        priceField.disabled = false;
        triggerField.disabled = true;
        triggerField.value = 0;
    } else if (orderType === 'SL') {
        priceField.disabled = false;
        triggerField.disabled = false;
    } else if (orderType === 'SL-M') {
        priceField.disabled = true;
        priceField.value = 0;
        triggerField.disabled = false;
    }
}

function submitAdvancedHoldingAction() {
    var symbol = document.getElementById('actionSymbol').value;
    var tradeType = document.getElementById('actionType').value;
    var orderType = document.getElementById('orderType').value;
    var productType = document.getElementById('productType').value;
    var price = document.getElementById('actionPrice').value;
    var quantity = document.getElementById('actionQuantity').value;
    var validity = document.getElementById('validityType').value;
    var triggerPrice = document.getElementById('triggerPrice').value;
    
    if (!symbol || !quantity || quantity <= 0) {
        showNotification('Please enter valid trade details', 'error');
        return;
    }
    
    if ((orderType === 'L' || orderType === 'SL') && (!price || price <= 0)) {
        showNotification('Please enter a valid price for limit orders', 'error');
        return;
    }
    
    if ((orderType === 'SL' || orderType === 'SL-M') && (!triggerPrice || triggerPrice <= 0)) {
        showNotification('Please enter a valid trigger price for stop loss orders', 'error');
        return;
    }
    
    // Prepare order data matching the working format from positions page
    var orderData = {
        exchange_segment: 'nse_cm',
        product: productType,
        price: (orderType === 'MKT' || orderType === 'SL-M') ? '0' : price.toString(),
        order_type: orderType,
        quantity: quantity.toString(),
        validity: validity,
        trading_symbol: symbol,
        symbol: symbol, // Add both for compatibility
        transaction_type: tradeType === 'BUY' ? 'B' : 'S',
        amo: 'NO',
        disclosed_quantity: '0',
        market_protection: '0',
        pf: 'N',
        trigger_price: (orderType === 'SL' || orderType === 'SL-M') ? triggerPrice.toString() : '0',
        tag: 'HOLDINGS_PAGE'
    };
    
    var submitBtn = document.querySelector('#holdingActionModal .btn-primary');
    var originalText = submitBtn.textContent;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Placing Order...';
    submitBtn.disabled = true;
    
    fetch('/api/place-order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderData)
    })
    .then(response => response.json())
    .then(function(data) {
        submitBtn.innerHTML = '<i class="fas fa-chart-line me-2"></i>Place Trade';
        submitBtn.disabled = false;
        
        if (data.success) {
            var orderTypeText = orderType === 'MKT' ? 'Market' : orderType === 'L' ? 'Limit' : 'Stop Loss';
            showNotification(tradeType + ' ' + orderTypeText + ' order placed successfully for ' + symbol, 'success');
            bootstrap.Modal.getInstance(document.getElementById('holdingActionModal')).hide();
            refreshHoldings();
        } else {
            showNotification('Failed to place order: ' + data.message, 'error');
        }
    })
    .catch(function(error) {
        submitBtn.innerHTML = '<i class="fas fa-chart-line me-2"></i>Place Trade';
        submitBtn.disabled = false;
        console.error('Error:', error);
        showNotification('Error placing order: ' + error.message, 'error');
    });
}

function submitHoldingAction() {
    submitAdvancedHoldingAction();
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

function showNotification(message, type) {
    if (type === undefined) type = 'info';
    var toast = document.createElement('div');
    toast.className = 'alert alert-' + type + ' alert-dismissible fade show position-fixed';
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = message + '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
    
    document.body.appendChild(toast);
    
    setTimeout(function() {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 3000);
}

var sortState = {
    column: null,
    direction: 'asc'
};

function sortTable(column) {
    var tbody = document.getElementById('holdingsTableBody');
    
    if (!tbody) return;
    
    var rows = Array.from(tbody.querySelectorAll('tr'));
    
    if (sortState.column === column) {
        sortState.direction = sortState.direction === 'asc' ? 'desc' : 'asc';
    } else {
        sortState.column = column;
        sortState.direction = 'asc';
    }
    
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
        
        var result;
        if (typeof aValue === 'string') {
            result = aValue.localeCompare(bValue);
        } else {
            result = aValue - bValue;
        }
        
        return sortState.direction === 'asc' ? result : -result;
    });
    
    updateSortIndicators(column, sortState.direction);
    
    tbody.innerHTML = '';
    rows.forEach(function(row) {
        tbody.appendChild(row);
    });
    
    var sortBtn = document.getElementById('sortSymbolBtn');
    if (sortBtn && column === 'symbol') {
        var icon = sortState.direction === 'asc' ? 'fa-sort-alpha-down' : 'fa-sort-alpha-up';
        var text = sortState.direction === 'asc' ? 'Sort A-Z' : 'Sort Z-A';
        sortBtn.innerHTML = '<i class="fas ' + icon + ' me-1"></i>' + text;
    }
}

function updateSortIndicators(activeColumn, direction) {
    var indicators = document.querySelectorAll('[id^="sort-"]');
    indicators.forEach(function(indicator) {
        indicator.classList.add('d-none');
    });
    
    var activeIndicator = document.getElementById('sort-' + activeColumn + '-' + direction);
    if (activeIndicator) {
        activeIndicator.classList.remove('d-none');
    }
    
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
        
        if (totalHoldingsEl) {
            totalHoldingsEl.textContent = totalHoldings;
        }
        
        if (totalInvestedEl) {
            totalInvestedEl.textContent = '₹' + Math.round(totalInvested).toLocaleString('en-IN');
        }
        
        if (currentValueEl) {
            currentValueEl.textContent = '₹' + Math.round(currentValue).toLocaleString('en-IN');
        }
        
        if (totalPnlEl) {
            totalPnlEl.textContent = (totalPnl >= 0 ? '+' : '') + '₹' + Math.round(Math.abs(totalPnl)).toLocaleString('en-IN');
            
            var pnlCard = totalPnlEl.closest('.card');
            if (pnlCard) {
                var gradient = totalPnl >= 0 
                    ? 'linear-gradient(135deg, #166534, #22c55e)' 
                    : 'linear-gradient(135deg, #991b1b, #ef4444)';
                pnlCard.style.background = gradient;
            }
        }
    }
}

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
        
        var pnlCard = totalPnlEl.closest('.card');
        if (pnlCard) {
            var gradient = totalPnl >= 0 
                ? 'linear-gradient(135deg, #166534, #22c55e)' 
                : 'linear-gradient(135deg, #991b1b, #ef4444)';
            pnlCard.style.background = gradient;
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Load holdings data immediately when page loads
    refreshHoldings();
    
    setTimeout(function() {
        sortTable('symbol');
        calculateAndUpdateCards();
    }, 500);
    
    setTimeout(calculateAndUpdateCards, 1000);
});

setInterval(refreshHoldings, 120000);