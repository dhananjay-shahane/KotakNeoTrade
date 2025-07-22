var positionsData = [];
var refreshInterval = null;
var currentSortColumn = '';
var currentSortDirection = 'asc';
var currentFilter = 'ALL';

// Load positions when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadPositionsData();
    // Auto-refresh every 30 seconds
    refreshInterval = setInterval(loadPositionsData, 30000);
});

// Clear interval when page unloads
window.addEventListener('beforeunload', function() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});

async function loadPositionsData() {
    try {
        var response = await fetch('/api/positions');
        var data = await response.json();

        if (data.success) {
            positionsData = data.positions || [];
            updatePositionsTable(positionsData);
            updatePositionsSummary(positionsData);
        } else {
            console.error('Failed to load positions:', data.message);
            showNoPositionsMessage();
        }
    } catch (error) {
        console.error('Error loading positions:', error);
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
    var displayPositions = filterPositionsByType(positions, currentFilter);

    displayPositions.forEach(function(position) {
        var symbol = position.trdSym || position.sym || position.tradingSymbol || 'N/A';
        var product = position.prod || position.product || 'N/A';
        var exchange = position.exSeg || position.exchange || 'N/A';
        var buyQty = position.buyQty || position.flBuyQty || '0';
        var sellQty = position.sellQty || position.flSellQty || '0';
        var netQty = position.netQty || position.flNetQty || '0';
        var buyAmt = position.buyAmt || position.flBuyAmt || '0';
        var sellAmt = position.sellAmt || position.flSellAmt || '0';
        var pnl = position.pnl || position.flPnl || '0';
        var position_type = parseInt(netQty) > 0 ? 'LONG' : parseInt(netQty) < 0 ? 'SHORT' : 'FLAT';
        var expiry = position.expiry || position.expDate || 'N/A';
        var lastUpdated = position.lastUpdated || 'N/A';

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

        tableHTML += `
            <tr data-position-symbol="${symbol}">
                <td><strong>${symbol}</strong></td>
                <td><span class="badge bg-info">${product}</span></td>
                <td><span class="badge bg-secondary">${exchange}</span></td>
                <td>${buyQty}</td>
                <td>${sellQty}</td>
                <td><strong>${netQty}</strong></td>
                <td>₹${formattedBuyAmt.toFixed(2)}</td>
                <td>₹${formattedSellAmt.toFixed(2)}</td>
                <td class="${pnlClass}"><strong>₹${formattedPnl.toFixed(2)}</strong></td>
                <td><span class="badge ${positionClass}">${position_type}</span></td>
                <td><small>${expiry}</small></td>
                <td><small>${lastUpdated}</small></td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-primary btn-sm" onclick="showPlaceOrderModal('${symbol}', '${exchange}')" title="Place Order">
                            <i class="fas fa-plus"></i>
                        </button>
                        <button class="btn btn-info btn-sm" onclick="viewPositionDetails('${symbol}')" title="View Details">
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
    document.getElementById('longPositionsCount').textContent = longPositions;
    document.getElementById('shortPositionsCount').textContent = shortPositions;
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
            <td colspan="13" class="text-center py-5">
                <i class="fas fa-chart-line fa-3x text-muted mb-3"></i>
                <h4 class="text-muted">No Positions Found</h4>
                <p class="text-muted">You don't have any open positions yet.</p>
                <button class="btn btn-primary" onclick="window.location.href='/dashboard'">
                    <i class="fas fa-plus me-1"></i>Start Trading
                </button>
            </td>
        </tr>
    `;

    // Reset summary counts
    document.getElementById('totalPositionsCount').textContent = '0';
    document.getElementById('longPositionsCount').textContent = '0';
    document.getElementById('shortPositionsCount').textContent = '0';
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
        alert('Position Details:\n' + JSON.stringify(position, null, 2));
    }
}

// Expose functions globally
window.refreshPositions = refreshPositions;
window.setAutoRefresh = setAutoRefresh;
window.sortTable = sortTable;
window.filterPositionsByType = function(type) {
    currentFilter = type;
    updatePositionsTable(positionsData);
};
window.showPlaceOrderModal = showPlaceOrderModal;
window.handleOrderTypeChange = handleOrderTypeChange;
window.submitPlaceOrder = submitPlaceOrder;
window.viewPositionDetails = viewPositionDetails;