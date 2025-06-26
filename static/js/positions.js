async function refreshPositions() {
    var refreshBtn = document.querySelector('[onclick="refreshPositions()"]');
    if (refreshBtn) {
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Loading...';
        refreshBtn.disabled = true;
    }

    try {
        console.log('Fetching positions data...');
        var response = await fetch('/api/positions');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        var data = await response.json();
        console.log('Positions API response:', data);

        if (data.success) {
            var positions = data.positions || [];
            console.log(`Received ${positions.length} positions`);
            
            updatePositionsTable(positions);
            updatePositionsSummary(positions);
            
            if (positions.length > 0) {
                showUpdateNotification(`Positions refreshed: ${positions.length} positions loaded`, 'success');
            } else {
                showUpdateNotification('No positions found in your account', 'info');
            }
        } else {
            var errorMsg = data.message || data.error || 'Unknown error occurred';
            console.error('API Error:', errorMsg);
            console.error('Full response:', data);
            showUpdateNotification('Failed to refresh positions: ' + errorMsg, 'error');
        }
    } catch (error) {
        console.error('Error refreshing positions:', error);
        console.error('Error type:', error.name);
        console.error('Error details:', error);
        
        var errorMessage = 'Network error';
        if (error.message) {
            errorMessage += ': ' + error.message;
        }
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            errorMessage = 'Unable to connect to server. Please check your connection.';
        }
        
        showUpdateNotification(errorMessage, 'error');
    } finally {
        if (refreshBtn) {
            refreshBtn.innerHTML = '<i class="fas fa-sync me-1"></i>Refresh';
            refreshBtn.disabled = false;
        }
    }
}

// Auto-refresh positions every 30 seconds
var positionsRefreshInterval = setInterval(refreshPositions, 30000);

// Refresh positions on page load
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(refreshPositions, 1000); // Initial refresh after 1 second
});

function updatePositionsTable(positions) {
    var tableBody = document.getElementById('positionsTableBody');
    if (!tableBody) return;

    if (!positions || positions.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="11" class="text-center py-5">
                    <i class="fas fa-chart-pie fa-3x text-light mb-3"></i>
                    <h4 class="text-light">No Positions Found</h4>
                    <p class="text-light">You don't have any open positions at the moment.</p>
                    <a href="/dashboard" class="btn btn-primary">
                        <i class="fas fa-plus me-1"></i>Place Order
                    </a>
                </td>
            </tr>
        `;
        return;
    }

    var tableHTML = '';
    positions.forEach((position, index), function() {
        var buyQty = parseFloat(position.flBuyQty || position.buyQty || 0);
        var sellQty = parseFloat(position.flSellQty || position.sellQty || 0);
        var netQty = buyQty - sellQty;
        
        var buyAvg = parseFloat(position.flBuyAvgPrc || position.buyAvgPrc || position.avgBuyPrice || 0);
        var sellAvg = parseFloat(position.flSellAvgPrc || position.sellAvgPrc || position.avgSellPrice || 0);
        
        var pnl = parseFloat(position.urPnl || position.pnl || position.rpnl || position.unrealised || 0);
        var ltp = parseFloat(position.mktPrice || position.ltp || position.LastPrice || 0);
        
        // Calculate percentage if investment exists
        var pnlPercentage = '';
        if (pnl !== 0 && buyAvg > 0 && buyQty > 0) {
            var investment = buyAvg * buyQty;
            var percentage = (pnl / investment) * 100;
            pnlPercentage = `<br><small>(${percentage >= 0 ? '+' : ''}${percentage.toFixed(2)}%)</small>`;
        }

        tableHTML += `
            <tr data-position-id="${position.tok || index}">
                <td>
                    <strong>${position.trdSym || position.sym || position.tradingsymbol || 'N/A'}</strong>
                    ${position.series ? `<br><small class="text-light">${position.series}</small>` : ''}
                    ${position.opTyp && position.opTyp !== 'XX' ? 
                        `<br><small class="text-warning">${position.opTyp} ${position.stkPrc || position.strike_price || ''}</small>` : ''}
                </td>
                <td>
                    <span class="badge bg-info">${position.exSeg || position.exchange || 'NSE'}</span>
                </td>
                <td>
                    <span class="badge bg-secondary">${position.prdCode || position.product || 'CNC'}</span>
                </td>
                <td class="text-success">
                    ${buyQty.toFixed(0)}
                </td>
                <td class="text-danger">
                    ${sellQty.toFixed(0)}
                </td>
                <td>
                    <span class="${netQty > 0 ? 'text-success' : netQty < 0 ? 'text-danger' : 'text-light'}">
                        ${netQty.toFixed(0)}
                    </span>
                </td>
                <td>
                    ${buyAvg > 0 ? `₹${buyAvg.toFixed(2)}` : '<span class="text-light">N/A</span>'}
                </td>
                <td>
                    ${sellAvg > 0 ? `₹${sellAvg.toFixed(2)}` : '<span class="text-light">N/A</span>'}
                </td>
                <td class="price-ltp">₹${ltp.toFixed(2)}</td>
                <td>
                    <span class="position-pnl ${pnl > 0 ? 'text-success' : pnl < 0 ? 'text-danger' : 'text-light'}">
                        ₹${pnl.toFixed(2)}
                        ${pnlPercentage}
                    </span>
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        ${netQty > 0 ? 
                            `<button class="btn btn-danger btn-sm" onclick="sellPosition('${position.trdSym || position.sym}', ${Math.abs(netQty)})">
                                <i class="fas fa-minus"></i> Sell
                            </button>` : 
                            netQty < 0 ? 
                            `<button class="btn btn-success btn-sm" onclick="buyPosition('${position.trdSym || position.sym}', ${Math.abs(netQty)})">
                                <i class="fas fa-plus"></i> Buy
                            </button>` : ''
                        }
                        <button class="btn btn-info btn-sm" onclick="getQuote('${position.tok || ''}', '${position.exSeg || ''}')">
                            <i class="fas fa-chart-line"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });

    tableBody.innerHTML = tableHTML;
    
    // Add update animation with visual feedback
    tableBody.classList.add('data-updated');
    setTimeout(()=>{}, function() {
        tableBody.classList.remove('data-updated');
    }, 1500);
    
    console.log(`✅ Updated positions table with ${positions.length} positions`);
}

function updatePositionsSummary(positions) {
    // Update total positions count
    var totalPositionsEl = document.getElementById('totalPositionsCount');
    if (totalPositionsEl) {
        totalPositionsEl.textContent = positions.length;
    }

    // Calculate totals with better field mapping
    var totalPnl = 0;
    var realizedPnl = 0;
    var unrealizedPnl = 0;
    var longPositions = 0;
    var shortPositions = 0;

    positions.forEach(position, function() {
        // Calculate P&L with multiple field fallbacks
        var pnl = 0;
        if (position.urPnl !== undefined) {
            pnl = parseFloat(position.urPnl) || 0;
        } else if (position.pnl !== undefined) {
            pnl = parseFloat(position.pnl) || 0;
        } else if (position.rpnl !== undefined) {
            pnl = parseFloat(position.rpnl) || 0;
        }
        
        // Calculate realized P&L
        var rPnl = 0;
        if (position.rlPnl !== undefined) {
            rPnl = parseFloat(position.rlPnl) || 0;
        } else if (position.realised_pnl !== undefined) {
            rPnl = parseFloat(position.realised_pnl) || 0;
        } else if (position.rpnl !== undefined) {
            rPnl = parseFloat(position.rpnl) || 0;
        }
        
        // Calculate unrealized P&L
        var uPnl = 0;
        if (position.urPnl !== undefined) {
            uPnl = parseFloat(position.urPnl) || 0;
        } else if (position.unrealised !== undefined) {
            uPnl = parseFloat(position.unrealised) || 0;
        } else if (pnl !== 0) {
            uPnl = pnl; // Use total PnL as unrealized if no specific field
        }

        // Calculate net position
        var buyQty = parseFloat(position.flBuyQty || position.buyQty || 0);
        var sellQty = parseFloat(position.flSellQty || position.sellQty || 0);
        var netQty = buyQty - sellQty;

        totalPnl += pnl;
        realizedPnl += rPnl;
        unrealizedPnl += uPnl;

        if (netQty > 0) longPositions++;
        else if (netQty < 0) shortPositions++;
    });

    // Update summary cards with proper IDs
    var totalPnlEl = document.getElementById('totalPnl');
    if (totalPnlEl) {
        totalPnlEl.textContent = `₹${totalPnl.toFixed(2)}`;
        totalPnlEl.className = `mb-1 ${totalPnl > 0 ? 'text-light' : totalPnl < 0 ? 'text-light' : 'text-light'}`;
    }

    var realizedPnlEl = document.getElementById('realizedPnl');
    if (realizedPnlEl) {
        realizedPnlEl.textContent = `₹${realizedPnl.toFixed(2)}`;
    }

    var unrealizedPnlEl = document.getElementById('unrealizedPnl');
    if (unrealizedPnlEl) {
        unrealizedPnlEl.textContent = `₹${unrealizedPnl.toFixed(2)}`;
    }

    // Update footer summary with proper IDs
    var footerTotalPositions = document.getElementById('footerTotalPositions');
    if (footerTotalPositions) {
        footerTotalPositions.textContent = positions.length;
    }
    
    var footerTotalPnl = document.getElementById('footerTotalPnl');
    if (footerTotalPnl) {
        footerTotalPnl.textContent = `₹${totalPnl.toFixed(2)}`;
        footerTotalPnl.className = `mb-0 ${totalPnl > 0 ? 'text-success' : totalPnl < 0 ? 'text-danger' : 'text-light'}`;
    }
    
    var footerLongPositions = document.getElementById('footerLongPositions');
    if (footerLongPositions) {
        footerLongPositions.textContent = longPositions;
    }
    
    var footerShortPositions = document.getElementById('footerShortPositions');
    if (footerShortPositions) {
        footerShortPositions.textContent = shortPositions;
    }

    console.log('Position Summary Updated:', {
        totalPositions: positions.length,
        totalPnl: totalPnl.toFixed(2),
        realizedPnl: realizedPnl.toFixed(2),
        unrealizedPnl: unrealizedPnl.toFixed(2),
        longPositions,
        shortPositions
    });
}

function showUpdateNotification(message, type = 'info') {
    var notification = document.createElement('div');
    notification.className = `alert alert-${type === 'success' ? 'success' : 'warning'} position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
            <div class="flex-grow-1">${message}</div>
            <button type="button" class="btn-close" onclick="this.closest('.alert').remove()"></button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(()=>{}, function() {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

function sellPosition(symbol, quantity) {
    document.getElementById('actionSymbol').value = symbol;
    document.getElementById('actionType').value = 'SELL';
    document.getElementById('actionQuantity').value = quantity;
    document.getElementById('positionActionTitle').textContent = 'Sell Position: ' + symbol;
    new bootstrap.Modal(document.getElementById('positionActionModal')).show();
}

function buyPosition(symbol, quantity) {
    document.getElementById('actionSymbol').value = symbol;
    document.getElementById('actionType').value = 'BUY';
    document.getElementById('actionQuantity').value = quantity;
    document.getElementById('positionActionTitle').textContent = 'Buy Position: ' + symbol;
    new bootstrap.Modal(document.getElementById('positionActionModal')).show();
}

function submitPositionAction() {
    var form = document.getElementById('positionActionForm');
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
    .then(data, function() {
        if (data.success) {
            alert('Order placed successfully!');
            bootstrap.Modal.getInstance(document.getElementById('positionActionModal')).hide();
            refreshPositions();
        } else {
            alert('Failed to place order: ' + data.message);
        }
    })
    .catch(error, function() {
        console.error('Error:', error);
        alert('Error placing order');
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
            // Display quote data in a modal or update UI
            alert('Current LTP: ₹' + (data.data[0] && data.data[0].ltp ? data.data[0].ltp : 'N/A'));
        } else {
            alert('Failed to get quote: ' + data.message);
        }
    })
    .catch(error, function() {
        console.error('Error:', error);
        alert('Error getting quote');
    });
}

// Auto-refresh positions every 30 seconds (reduced frequency for better UX)
setInterval(refreshPositions, 30000);

// Add CSS for update animations
var style = document.createElement('style');
style.textContent = `
    .data-updated {
        animation: dataUpdate 1.5s ease-in-out;
    }
    
    @keyframes dataUpdate {
        0% { background-color: rgba(40, 167, 69, 0.3); }
        50% { background-color: rgba(40, 167, 69, 0.1); }
        100% { background-color: transparent; }
    }
    
    .price-ltp {
        transition: all 0.3s ease;
    }
    
    .position-pnl {
        transition: all 0.3s ease;
    }
    
    .price-up {
        background-color: rgba(40, 167, 69, 0.2);
        animation: priceUp 1s ease-in-out;
    }
    
    .price-down {
        background-color: rgba(220, 53, 69, 0.2);
        animation: priceDown 1s ease-in-out;
    }
    
    @keyframes priceUp {
        0% { background-color: rgba(40, 167, 69, 0.4); }
        100% { background-color: transparent; }
    }
    
    @keyframes priceDown {
        0% { background-color: rgba(220, 53, 69, 0.4); }
        100% { background-color: transparent; }
    }
`;
document.head.appendChild(style);