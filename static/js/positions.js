/**
 * Positions Manager - Handle live positions data with comprehensive P&L analysis
 * Displays data from Kotak Neo API response format with Long/Short position tracking
 */

function PositionsManager() {
    this.positions = [];
    this.refreshInterval = null;
    this.autoRefreshTime = 30000; // 30 seconds default
    this.initialize();
}

PositionsManager.prototype.initialize = function() {
    console.log('Initializing Positions Manager...');
    this.loadPositions();
    this.setupAutoRefresh();
};

PositionsManager.prototype.loadPositions = function() {
    console.log('Loading positions data...');
    
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/api/positions', true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                try {
                    var response = JSON.parse(xhr.responseText);
                    console.log('Positions API Response:', response);
                    console.log('Response keys:', Object.keys(response));
                    console.log('Response.success:', response.success);
                    console.log('Response.positions type:', typeof response.positions);
                    console.log('Response.positions isArray:', Array.isArray(response.positions));
                    
                    if (response.success && response.positions && Array.isArray(response.positions)) {
                        console.log('Using wrapped API format with', response.positions.length, 'positions');
                        this.positions = response.positions;
                        this.displayPositions();
                        this.updateSummaryCards();
                    } else if (response.stat === 'Ok' && response.data && Array.isArray(response.data)) {
                        console.log('Using direct Kotak Neo API format with', response.data.length, 'positions');
                        this.positions = response.data;
                        this.displayPositions();
                        this.updateSummaryCards();
                    } else if (response.success === false && response.message) {
                        console.error('API returned error:', response.message);
                        this.showError(response.message);
                    } else {
                        console.error('Invalid positions response format:', response);
                        console.error('Expected: {success: true, positions: []} or {stat: "Ok", data: []}');
                        this.showError('Invalid response format from positions API');
                    }
                } catch (e) {
                    console.error('Failed to parse positions response:', e);
                    this.showError('Failed to parse positions data');
                }
            } else {
                console.error('Positions API request failed:', xhr.status);
                this.showError('Failed to load positions data');
            }
        }
    }.bind(this);
    xhr.send();
};

PositionsManager.prototype.displayPositions = function() {
    var tbody = document.getElementById('positionsTableBody');
    if (!tbody) return;
    
    if (this.positions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="12" class="text-center py-4 text-muted">No positions found</td></tr>';
        return;
    }
    
    var html = '';
    for (var i = 0; i < this.positions.length; i++) {
        var position = this.positions[i];
        
        // Calculate net quantity and position type
        var buyQty = parseFloat(position.flBuyQty || 0);
        var sellQty = parseFloat(position.flSellQty || 0);
        var netQty = buyQty - sellQty;
        
        // Calculate P&L
        var buyAmt = parseFloat(position.buyAmt || 0);
        var sellAmt = parseFloat(position.sellAmt || 0);
        var pnl = sellAmt - buyAmt;
        
        // Determine position type
        var positionType = '';
        var positionClass = '';
        if (netQty > 0) {
            positionType = 'LONG';
            positionClass = 'text-success';
        } else if (netQty < 0) {
            positionType = 'SHORT';
            positionClass = 'text-danger';
        } else {
            positionType = 'SQUARED';
            positionClass = 'text-muted';
        }
        
        // Format P&L display
        var pnlDisplay = '';
        var pnlClass = '';
        if (pnl > 0) {
            pnlDisplay = '+₹' + pnl.toFixed(2);
            pnlClass = 'text-success';
        } else if (pnl < 0) {
            pnlDisplay = '-₹' + Math.abs(pnl).toFixed(2);
            pnlClass = 'text-danger';
        } else {
            pnlDisplay = '₹0.00';
            pnlClass = 'text-muted';
        }
        
        // Format expiry date
        var expiryDisplay = position.expDt || 'N/A';
        
        // Format last updated time
        var lastUpdated = position.hsUpTm || 'N/A';
        
        html += '<tr>';
        html += '<td><strong>' + (position.trdSym || position.sym || 'N/A') + '</strong></td>';
        html += '<td><span class="badge bg-secondary">' + (position.prod || 'N/A') + '</span></td>';
        html += '<td><small class="text-muted">' + (position.exSeg || 'N/A') + '</small></td>';
        html += '<td class="text-success">' + buyQty.toLocaleString() + '</td>';
        html += '<td class="text-danger">' + sellQty.toLocaleString() + '</td>';
        html += '<td class="' + positionClass + '"><strong>' + netQty.toLocaleString() + '</strong></td>';
        html += '<td class="text-success">₹' + buyAmt.toLocaleString('en-IN', {minimumFractionDigits: 2}) + '</td>';
        html += '<td class="text-danger">₹' + sellAmt.toLocaleString('en-IN', {minimumFractionDigits: 2}) + '</td>';
        html += '<td class="' + pnlClass + '"><strong>' + pnlDisplay + '</strong></td>';
        html += '<td><span class="badge ' + (positionType === 'LONG' ? 'bg-success' : positionType === 'SHORT' ? 'bg-danger' : 'bg-secondary') + '">' + positionType + '</span></td>';
        html += '<td><small>' + expiryDisplay + '</small></td>';
        html += '<td><small class="text-muted">' + lastUpdated + '</small></td>';
        html += '</tr>';
    }
    
    tbody.innerHTML = html;
    
    // Update table count
    var countElement = document.getElementById('positionsTableCount');
    if (countElement) {
        countElement.textContent = this.positions.length;
    }
};

PositionsManager.prototype.updateSummaryCards = function() {
    var totalPositions = this.positions.length;
    var longPositions = 0;
    var shortPositions = 0;
    var longValue = 0;
    var shortValue = 0;
    var totalPnl = 0;
    
    for (var i = 0; i < this.positions.length; i++) {
        var position = this.positions[i];
        
        var buyQty = parseFloat(position.flBuyQty || 0);
        var sellQty = parseFloat(position.flSellQty || 0);
        var netQty = buyQty - sellQty;
        
        var buyAmt = parseFloat(position.buyAmt || 0);
        var sellAmt = parseFloat(position.sellAmt || 0);
        var pnl = sellAmt - buyAmt;
        
        totalPnl += pnl;
        
        if (netQty > 0) {
            longPositions++;
            longValue += buyAmt;
        } else if (netQty < 0) {
            shortPositions++;
            shortValue += Math.abs(sellAmt);
        }
    }
    
    // Update summary cards
    this.updateElement('totalPositionsCount', totalPositions);
    this.updateElement('longPositionsCount', longPositions);
    this.updateElement('shortPositionsCount', shortPositions);
    this.updateElement('longPositionsValue', '₹' + longValue.toLocaleString('en-IN', {minimumFractionDigits: 2}));
    this.updateElement('shortPositionsValue', '₹' + shortValue.toLocaleString('en-IN', {minimumFractionDigits: 2}));
    
    // Update total P&L with appropriate color
    var totalPnlElement = document.getElementById('totalPnlValue');
    var pnlBadgeElement = document.getElementById('pnlBadge');
    
    if (totalPnlElement) {
        var pnlDisplay = '';
        if (totalPnl > 0) {
            pnlDisplay = '+₹' + totalPnl.toFixed(2);
            totalPnlElement.className = 'text-success mb-1';
        } else if (totalPnl < 0) {
            pnlDisplay = '-₹' + Math.abs(totalPnl).toFixed(2);
            totalPnlElement.className = 'text-danger mb-1';
        } else {
            pnlDisplay = '₹0.00';
            totalPnlElement.className = 'text-muted mb-1';
        }
        totalPnlElement.textContent = pnlDisplay;
    }
    
    if (pnlBadgeElement) {
        var totalInvestment = longValue + shortValue;
        var pnlPercentage = totalInvestment > 0 ? (totalPnl / totalInvestment * 100) : 0;
        var percentageDisplay = (pnlPercentage >= 0 ? '+' : '') + pnlPercentage.toFixed(2) + '%';
        
        pnlBadgeElement.textContent = percentageDisplay;
        if (pnlPercentage > 0) {
            pnlBadgeElement.className = 'badge bg-success';
        } else if (pnlPercentage < 0) {
            pnlBadgeElement.className = 'badge bg-danger';
        } else {
            pnlBadgeElement.className = 'badge bg-secondary';
        }
    }
};

PositionsManager.prototype.updateElement = function(id, value) {
    var element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
};

PositionsManager.prototype.showError = function(message) {
    var tbody = document.getElementById('positionsTableBody');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="12" class="text-center py-4 text-danger">' +
            '<i class="fas fa-exclamation-triangle me-2"></i>' + message + '</td></tr>';
    }
};

PositionsManager.prototype.setupAutoRefresh = function() {
    if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
    }
    
    if (this.autoRefreshTime > 0) {
        this.refreshInterval = setInterval(function() {
            this.loadPositions();
        }.bind(this), this.autoRefreshTime);
    }
};

// Global functions for template
function refreshPositions() {
    if (window.positionsManager) {
        window.positionsManager.loadPositions();
    }
}

function setAutoRefresh(seconds) {
    if (window.positionsManager) {
        window.positionsManager.autoRefreshTime = seconds * 1000;
        window.positionsManager.setupAutoRefresh();
        
        var intervalElement = document.getElementById('refreshInterval');
        if (intervalElement) {
            if (seconds === 0) {
                intervalElement.textContent = 'Disabled';
            } else {
                intervalElement.textContent = seconds + 's';
            }
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.positionsManager = new PositionsManager();
});