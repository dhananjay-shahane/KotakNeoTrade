
var positionsData = [];
var positionsRefreshInterval = null;

function initializePositionsPage() {
    loadPositionsData();
    // Auto-refresh every 30 seconds
    positionsRefreshInterval = setInterval(loadPositionsData, 30000);
}

function cleanupPositionsPage() {
    if (positionsRefreshInterval) {
        clearInterval(positionsRefreshInterval);
        positionsRefreshInterval = null;
    }
}

async function loadPositionsData() {
    try {
        var response = await fetch('/api/kotak/positions');
        var data = await response.json();

        if (data.success) {
            positionsData = data.positions || [];
            updatePositionsTable(positionsData);
            updatePositionsSummary(data.summary || {});
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
    if (!tableBody) return;

    if (!positions || positions.length === 0) {
        showNoPositionsMessage();
        return;
    }

    var tableHTML = '';
    positions.forEach(function(position) {
        var symbol = position.tradingSymbol || position.trdSym || 'N/A';
        var netQty = position.netQty || position.net_qty || '0';
        var avgPrice = parseFloat(position.avgPrice || position.avg_price || 0);
        var ltp = parseFloat(position.ltp || position.last_price || 0);
        var pnl = parseFloat(position.pnl || position.realized_pnl || 0);
        var pnlPercent = parseFloat(position.pnlPercent || position.pnl_percent || 0);
        var product = position.prod || position.product || 'N/A';
        var exchange = position.exSeg || position.exchange || 'N/A';

        // Determine position type and styling
        var qtyClass = parseInt(netQty) > 0 ? 'quantity-long' : 'quantity-short';
        var pnlClass = pnl >= 0 ? 'pnl-positive' : 'pnl-negative';
        var pnlIcon = pnl >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';

        tableHTML += `
            <tr class="position-row">
                <td>
                    <strong class="holding-symbol">${symbol}</strong>
                    <br><small class="text-muted">${product}</small>
                </td>
                <td>
                    <span class="${qtyClass}">
                        ${netQty}
                    </span>
                </td>
                <td>₹${avgPrice.toFixed(2)}</td>
                <td>₹${ltp.toFixed(2)}</td>
                <td>
                    <span class="${pnlClass}">
                        <i class="fas ${pnlIcon} me-1"></i>
                        ₹${Math.abs(pnl).toFixed(2)}
                    </span>
                </td>
                <td>
                    <span class="${pnlClass}">
                        ${pnlPercent >= 0 ? '+' : ''}${pnlPercent.toFixed(2)}%
                    </span>
                </td>
                <td>
                    <span class="badge bg-secondary">${exchange}</span>
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-primary btn-sm" onclick="squareOffPosition('${symbol}')" title="Square Off">
                            <i class="fas fa-times"></i>
                        </button>
                        <button class="btn btn-info btn-sm" onclick="viewPositionDetails('${symbol}')" title="View Details">
                            <i class="fas fa-eye"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });

    tableBody.innerHTML = tableHTML;
}

function updatePositionsSummary(summary) {
    if (!summary) return;

    var summaryData = {
        'totalPositionsCount': summary.total_positions || 0,
        'totalPnlAmount': summary.total_pnl || 0,
        'longPositionsCount': summary.long_positions || 0,
        'shortPositionsCount': summary.short_positions || 0
    };

    Object.keys(summaryData).forEach(function(id) {
        var element = document.getElementById(id);
        if (element) {
            if (id === 'totalPnlAmount') {
                var pnl = summaryData[id];
                var pnlClass = pnl >= 0 ? 'text-profit' : 'text-loss';
                element.className = `value ${pnlClass}`;
                element.textContent = `₹${Math.abs(pnl).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
            } else {
                element.textContent = summaryData[id];
            }
        }
    });
}

function showNoPositionsMessage() {
    var tableBody = document.getElementById('positionsTableBody');
    if (!tableBody) return;
    
    tableBody.innerHTML = `
        <tr>
            <td colspan="8" class="text-center py-5">
                <i class="fas fa-chart-line fa-3x text-muted mb-3"></i>
                <h4 class="text-muted">No Open Positions</h4>
                <p class="text-muted">You don't have any active positions.</p>
            </td>
        </tr>
    `;

    // Reset summary
    var summaryIds = ['totalPositionsCount', 'longPositionsCount', 'shortPositionsCount'];
    summaryIds.forEach(function(id) {
        var element = document.getElementById(id);
        if (element) element.textContent = '0';
    });
    
    var pnlElement = document.getElementById('totalPnlAmount');
    if (pnlElement) {
        pnlElement.textContent = '₹0.00';
        pnlElement.className = 'value';
    }
}

async function refreshPositionsTable() {
    var button = document.querySelector('[onclick="refreshPositionsTable()"]');
    if (!button) return;
    
    var originalHtml = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Refreshing...';
    button.disabled = true;

    try {
        await loadPositionsData();
        showPositionsNotification('Positions refreshed successfully', 'success');
    } catch (error) {
        console.error('Error refreshing positions:', error);
        showPositionsNotification('Error refreshing positions', 'error');
    } finally {
        button.innerHTML = originalHtml;
        button.disabled = false;
    }
}

function showPositionsNotification(message, type = 'info') {
    if (typeof showToaster === 'function') {
        showToaster('Positions', message, type);
    }
}

function squareOffPosition(symbol) {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: 'Square Off Position?',
            text: `Are you sure you want to square off position in ${symbol}?`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'Yes, Square Off',
            cancelButtonText: 'Cancel'
        }).then((result) => {
            if (result.isConfirmed) {
                // Implementation for square off
                console.log('Square off position for:', symbol);
                showPositionsNotification('Square off functionality coming soon', 'info');
            }
        });
    } else {
        if (confirm(`Are you sure you want to square off position in ${symbol}?`)) {
            console.log('Square off position for:', symbol);
            showPositionsNotification('Square off functionality coming soon', 'info');
        }
    }
}

function viewPositionDetails(symbol) {
    var position = positionsData.find(p => (p.tradingSymbol || p.trdSym) === symbol);
    if (!position) return;

    console.log('Position details for:', symbol, position);
    showPositionsNotification('Position details view coming soon', 'info');
}
