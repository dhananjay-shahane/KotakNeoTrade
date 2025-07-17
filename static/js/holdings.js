
var holdingsData = [];
var holdingsRefreshInterval = null;

function initializeHoldingsPage() {
    loadHoldingsData();
    // Auto-refresh every 30 seconds
    holdingsRefreshInterval = setInterval(loadHoldingsData, 30000);
}

function cleanupHoldingsPage() {
    if (holdingsRefreshInterval) {
        clearInterval(holdingsRefreshInterval);
        holdingsRefreshInterval = null;
    }
}

async function loadHoldingsData() {
    try {
        var response = await fetch('/api/kotak/holdings');
        var data = await response.json();

        if (data.success) {
            holdingsData = data.holdings || [];
            updateHoldingsTable(holdingsData);
            updateHoldingsSummary(data.summary || {});
        } else {
            console.error('Failed to load holdings:', data.message);
            showNoHoldingsMessage();
        }
    } catch (error) {
        console.error('Error loading holdings:', error);
        showNoHoldingsMessage();
    }
}

function updateHoldingsTable(holdings) {
    var tableBody = document.getElementById('holdingsTableBody');
    if (!tableBody) return;

    if (!holdings || holdings.length === 0) {
        showNoHoldingsMessage();
        return;
    }

    var tableHTML = '';
    holdings.forEach(function(holding) {
        var symbol = holding.tradingSymbol || holding.trdSym || 'N/A';
        var isin = holding.isin || holding.instrumentName || '';
        var quantity = parseInt(holding.quantity || holding.qty || 0);
        var avgPrice = parseFloat(holding.avgPrice || holding.avg_price || 0);
        var ltp = parseFloat(holding.ltp || holding.last_price || 0);
        var investedValue = parseFloat(holding.investedValue || (avgPrice * quantity) || 0);
        var currentValue = parseFloat(holding.currentValue || (ltp * quantity) || 0);
        var pnl = currentValue - investedValue;
        var pnlPercent = investedValue > 0 ? ((pnl / investedValue) * 100) : 0;

        // Calculate allocation percentage (you might want to pass total portfolio value)
        var allocationPercent = 0; // This should be calculated based on total portfolio

        var pnlClass = pnl >= 0 ? 'pnl-positive' : 'pnl-negative';
        var pnlIcon = pnl >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';

        tableHTML += `
            <tr class="holding-row">
                <td>
                    <div>
                        <strong class="holding-symbol">${symbol}</strong>
                        ${isin ? `<br><small class="holding-isin">${isin}</small>` : ''}
                    </div>
                </td>
                <td>${quantity.toLocaleString()}</td>
                <td>₹${avgPrice.toFixed(2)}</td>
                <td>₹${ltp.toFixed(2)}</td>
                <td>₹${investedValue.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                <td>₹${currentValue.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                <td>
                    <span class="${pnlClass}">
                        <i class="fas ${pnlIcon} me-1"></i>
                        ₹${Math.abs(pnl).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                    <br>
                    <small class="${pnlClass}">
                        ${pnlPercent >= 0 ? '+' : ''}${pnlPercent.toFixed(2)}%
                    </small>
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-success btn-sm" onclick="sellHolding('${symbol}')" title="Sell">
                            <i class="fas fa-minus"></i>
                        </button>
                        <button class="btn btn-primary btn-sm" onclick="buyMoreHolding('${symbol}')" title="Buy More">
                            <i class="fas fa-plus"></i>
                        </button>
                        <button class="btn btn-info btn-sm" onclick="viewHoldingDetails('${symbol}')" title="View Details">
                            <i class="fas fa-eye"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });

    tableBody.innerHTML = tableHTML;
}

function updateHoldingsSummary(summary) {
    if (!summary) return;

    var summaryData = {
        'totalHoldingsCount': summary.total_holdings || 0,
        'totalInvestedAmount': summary.total_invested || 0,
        'currentPortfolioValue': summary.current_value || 0,
        'totalHoldingsPnl': summary.total_pnl || 0
    };

    Object.keys(summaryData).forEach(function(id) {
        var element = document.getElementById(id);
        if (element) {
            if (id === 'totalHoldingsPnl') {
                var pnl = summaryData[id];
                var pnlClass = pnl >= 0 ? 'text-profit' : 'text-loss';
                element.className = `value ${pnlClass}`;
                element.textContent = `₹${Math.abs(pnl).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
            } else if (id.includes('Amount') || id.includes('Value')) {
                element.textContent = `₹${summaryData[id].toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
            } else {
                element.textContent = summaryData[id];
            }
        }
    });
}

function showNoHoldingsMessage() {
    var tableBody = document.getElementById('holdingsTableBody');
    if (!tableBody) return;
    
    tableBody.innerHTML = `
        <tr>
            <td colspan="8" class="text-center py-5">
                <i class="fas fa-briefcase fa-3x text-muted mb-3"></i>
                <h4 class="text-muted">No Holdings Found</h4>
                <p class="text-muted">Your investment portfolio is empty.</p>
            </td>
        </tr>
    `;

    // Reset summary
    var summaryIds = ['totalHoldingsCount'];
    summaryIds.forEach(function(id) {
        var element = document.getElementById(id);
        if (element) element.textContent = '0';
    });
    
    var amountIds = ['totalInvestedAmount', 'currentPortfolioValue'];
    amountIds.forEach(function(id) {
        var element = document.getElementById(id);
        if (element) element.textContent = '₹0.00';
    });

    var pnlElement = document.getElementById('totalHoldingsPnl');
    if (pnlElement) {
        pnlElement.textContent = '₹0.00';
        pnlElement.className = 'value';
    }
}

async function refreshHoldingsTable() {
    var button = document.querySelector('[onclick="refreshHoldingsTable()"]');
    if (!button) return;
    
    var originalHtml = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Refreshing...';
    button.disabled = true;

    try {
        await loadHoldingsData();
        showHoldingsNotification('Holdings refreshed successfully', 'success');
    } catch (error) {
        console.error('Error refreshing holdings:', error);
        showHoldingsNotification('Error refreshing holdings', 'error');
    } finally {
        button.innerHTML = originalHtml;
        button.disabled = false;
    }
}

function showHoldingsNotification(message, type = 'info') {
    if (typeof showToaster === 'function') {
        showToaster('Holdings', message, type);
    }
}

function sellHolding(symbol) {
    console.log('Sell holding:', symbol);
    showHoldingsNotification('Sell functionality coming soon', 'info');
}

function buyMoreHolding(symbol) {
    console.log('Buy more holding:', symbol);
    showHoldingsNotification('Buy more functionality coming soon', 'info');
}

function viewHoldingDetails(symbol) {
    var holding = holdingsData.find(h => (h.tradingSymbol || h.trdSym) === symbol);
    if (!holding) return;

    console.log('Holding details for:', symbol, holding);
    showHoldingsNotification('Holding details view coming soon', 'info');
}
