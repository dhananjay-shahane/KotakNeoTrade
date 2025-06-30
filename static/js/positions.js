/**
 * Positions Manager - Handle live positions data with comprehensive P&L analysis
 * Displays data from Kotak Neo API response format with Long/Short position tracking
 */

function PositionsManager() {
    this.positions = [];
    this.refreshInterval = null;
    this.autoRefreshTime = 30000; // 30 seconds default
    this.currentFilter = 'ALL'; // Track current filter
    this.sortDirection = 'asc'; // Track sort direction
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

                    // Handle different response formats
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
                    } else if (Array.isArray(response)) {
                        console.log('Using direct array format with', response.length, 'positions');
                        this.positions = response;
                        this.displayPositions();
                        this.updateSummaryCards();
                    } else if (response.success === false && response.message) {
                        console.error('API returned error:', response.message);
                        this.showError(response.message);
                    } else {
                        console.error('Invalid positions response format:', response);
                        this.showError('Unable to load positions data');
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
        tbody.innerHTML = '<tr><td colspan="13" class="text-center py-4 text-muted">No positions found</td></tr>';
        return;
    }

    // Filter positions based on current filter
    var filterValue = this.currentFilter || 'ALL';

    var filteredPositions = this.positions.filter(function(position) {
        if (filterValue === 'ALL') {
            return true;
        } else {
            // Calculate net quantity and position type using all available fields
            var buyQty = parseFloat(position.flBuyQty || position.cfBuyQty || 0);
            var sellQty = parseFloat(position.flSellQty || position.cfSellQty || 0);
            var netQty = buyQty - sellQty;

            if (filterValue === 'LONG' && netQty > 0) {
                return true;
            } else if (filterValue === 'SHORT' && netQty < 0) {
                return true;
            } else {
                return false;
            }
        }
    });

    console.log('Filtering positions:', filterValue, 'Total:', this.positions.length, 'Filtered:', filteredPositions.length);

    var html = '';
    for (var i = 0; i < filteredPositions.length; i++) {
        var position = filteredPositions[i];

        // Calculate net quantity and position type using all available fields
        var buyQty = parseFloat(position.flBuyQty || position.cfBuyQty || 0);
        var sellQty = parseFloat(position.flSellQty || position.cfSellQty || 0);
        var netQty = buyQty - sellQty;

        // Calculate P&L using all available amount fields
        var buyAmt = parseFloat(position.buyAmt || position.cfBuyAmt || 0);
        var sellAmt = parseFloat(position.sellAmt || position.cfSellAmt || 0);
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
        html += '<td>';
        var positionSymbol = position.trdSym || position.sym || '';
        var positionExchange = position.exSeg || 'NSE';
        
        // Only show buttons if we have a valid symbol
        if (positionSymbol && positionSymbol !== 'N/A' && positionSymbol.trim() !== '') {
            html += '<button class="btn btn-sm btn-success me-1" onclick="openPlaceOrderModal(\'' + positionSymbol.replace(/'/g, "\\'") + '\', \'' + positionExchange + '\', \'BUY\')" title="Buy">';
            html += '<i class="fas fa-plus"></i> Buy</button>';
            html += '<button class="btn btn-sm btn-danger" onclick="openPlaceOrderModal(\'' + positionSymbol.replace(/'/g, "\\'") + '\', \'' + positionExchange + '\', \'SELL\')" title="Sell">';
            html += '<i class="fas fa-minus"></i> Sell</button>';
        } else {
            html += '<span class="text-muted small">No Symbol</span>';
        }
        html += '</td>';
        html += '</tr>';
    }

    tbody.innerHTML = html;

    // Update table count
    var countElement = document.getElementById('positionsTableCount');
    if (countElement) {
        countElement.textContent = filteredPositions.length;
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

        // Use correct field names from Kotak Neo API
        var buyQty = parseFloat(position.flBuyQty || position.cfBuyQty || 0);
        var sellQty = parseFloat(position.flSellQty || position.cfSellQty || 0);
        var netQty = buyQty - sellQty;

        var buyAmt = parseFloat(position.buyAmt || position.cfBuyAmt || 0);
        var sellAmt = parseFloat(position.sellAmt || position.cfSellAmt || 0);
        var pnl = sellAmt - buyAmt;

        totalPnl += pnl;

        // Debug individual position
        var symbol = position.trdSym || position.sym || 'Unknown';
        console.log('Position Debug - ' + symbol + ':');
        console.log('  Buy Qty:', buyQty, 'Sell Qty:', sellQty, 'Net Qty:', netQty);
        console.log('  Buy Amt:', buyAmt, 'Sell Amt:', sellAmt, 'P&L:', pnl);

        if (netQty > 0) {
            longPositions++;
            longValue += buyAmt;
            console.log('  Classification: LONG');
        } else if (netQty < 0) {
            shortPositions++;
            // For short positions, use the absolute value of net quantity times current price
            var currentPrice = parseFloat(position.stkPrc || position.upldPrc || 0);
            if (currentPrice > 0) {
                shortValue += Math.abs(netQty) * currentPrice;
                console.log('  Classification: SHORT, Value added:', Math.abs(netQty) * currentPrice);
            } else {
                shortValue += Math.abs(sellAmt);
                console.log('  Classification: SHORT, Value added (fallback):', Math.abs(sellAmt));
            }
        } else {
            console.log('  Classification: SQUARED (netQty = 0)');
        }
    }

    // Debug logging for position classification
    console.log('Position Summary Debug:');
    console.log('Total Positions:', totalPositions);
    console.log('Long Positions:', longPositions, 'Value:', longValue);
    console.log('Short Positions:', shortPositions, 'Value:', shortValue);
    console.log('Total P&L:', totalPnl);

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
        tbody.innerHTML = '<tr><td colspan="13" class="text-center py-4 text-danger">' +
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

// Function to filter positions based on position type (LONG/SHORT/ALL)
function filterPositions(type) {
    if (window.positionsManager) {
        window.positionsManager.currentFilter = type || 'ALL';
        window.positionsManager.displayPositions(); // Redisplay based on current filter
        console.log('Filtering positions by type:', window.positionsManager.currentFilter);
    }
}

// Add filterPositions method to PositionsManager prototype
PositionsManager.prototype.filterPositions = function(type) {
    this.currentFilter = type || 'ALL';
    this.displayPositions();
    console.log('Filtering positions by type:', this.currentFilter);
};

// Function to filter positions by type with visual feedback
function filterPositionsByType(type) {
    if (window.positionsManager) {
        // Remove active class from all filter buttons
        var filterButtons = document.querySelectorAll('.card-header .btn');
        filterButtons.forEach(function(btn) {
            btn.classList.remove('btn-primary', 'btn-success', 'btn-danger');
            if (type === 'ALL') {
                btn.classList.add('btn-outline-primary');
            } else if (type === 'LONG') {
                btn.classList.add('btn-outline-success');
            } else if (type === 'SHORT') {
                btn.classList.add('btn-outline-danger');
            }
        });

        // Add active class to clicked button
        var clickedButton = event.target;
        if (clickedButton) {
            clickedButton.classList.remove('btn-outline-primary', 'btn-outline-success', 'btn-outline-danger');
            if (type === 'ALL') {
                clickedButton.classList.add('btn-primary');
            } else if (type === 'LONG') {
                clickedButton.classList.add('btn-success');
            } else if (type === 'SHORT') {
                clickedButton.classList.add('btn-danger');
            }
        }

        // Remove active class from all cards
        var cards = document.querySelectorAll('.position-filter-card');
        cards.forEach(function(card) {
            card.classList.remove('border-primary', 'bg-primary-subtle');
        });

        // Add active class to clicked card
        var activeCard;
        if (type === 'ALL') {
            activeCard = document.querySelector('.total-positions-card');
        } else if (type === 'LONG') {
            activeCard = document.querySelector('.long-positions-card');
        } else if (type === 'SHORT') {
            activeCard = document.querySelector('.short-positions-card');
        }

        if (activeCard) {
            activeCard.classList.add('border-primary', 'bg-primary-subtle');
        }

        // Set the current filter and refresh display
        window.positionsManager.currentFilter = type;
        window.positionsManager.displayPositions();

        console.log('Filtering positions by type:', type);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.positionsManager = new PositionsManager();

    // Add click event listeners to position filter cards
    var totalPositionsCard = document.querySelector('.total-positions-card');
    var longPositionsCard = document.querySelector('.long-positions-card');
    var shortPositionsCard = document.querySelector('.short-positions-card');

    if (totalPositionsCard) {
        totalPositionsCard.addEventListener('click', function() {
            filterPositionsByType('ALL');
        });
        totalPositionsCard.style.cursor = 'pointer';
    }

    if (longPositionsCard) {
        longPositionsCard.addEventListener('click', function() {
            filterPositionsByType('LONG');
        });
        longPositionsCard.style.cursor = 'pointer';
    }

    if (shortPositionsCard) {
        shortPositionsCard.addEventListener('click', function() {
            filterPositionsByType('SHORT');
        });
        shortPositionsCard.style.cursor = 'pointer';
    }

    // Add event listener to symbol table header for sorting
    var symbolHeader = document.querySelector('#positionsTable th:first-child');
    if (symbolHeader) {
        symbolHeader.addEventListener('click', function() {
            sortPositionsBySymbol();
        });
        symbolHeader.style.cursor = 'pointer';
        symbolHeader.title = 'Click to sort A-Z';
    }
});

// Enhanced sorting functionality for positions table
var sortState = {
    column: null,
    direction: 'asc'
};

function sortTable(column) {
    if (!window.positionsManager) return;
    
    // Toggle sort direction
    if (sortState.column === column) {
        sortState.direction = sortState.direction === 'asc' ? 'desc' : 'asc';
    } else {
        sortState.column = column;
        sortState.direction = 'asc';
    }
    
    // Sort positions based on column
    window.positionsManager.positions.sort(function(a, b) {
        var aValue, bValue;
        
        switch (column) {
            case 'symbol':
                aValue = (a.trdSym || a.sym || '').toLowerCase();
                bValue = (b.trdSym || b.sym || '').toLowerCase();
                break;
            case 'product':
                aValue = (a.prod || '').toLowerCase();
                bValue = (b.prod || '').toLowerCase();
                break;
            case 'exchange':
                aValue = (a.exSeg || '').toLowerCase();
                bValue = (b.exSeg || '').toLowerCase();
                break;
            case 'buyQty':
                aValue = parseFloat(a.flBuyQty || a.cfBuyQty || 0);
                bValue = parseFloat(b.flBuyQty || b.cfBuyQty || 0);
                break;
            case 'sellQty':
                aValue = parseFloat(a.flSellQty || a.cfSellQty || 0);
                bValue = parseFloat(b.flSellQty || b.cfSellQty || 0);
                break;
            case 'netQty':
                aValue = (parseFloat(a.flBuyQty || a.cfBuyQty || 0)) - (parseFloat(a.flSellQty || a.cfSellQty || 0));
                bValue = (parseFloat(b.flBuyQty || b.cfBuyQty || 0)) - (parseFloat(b.flSellQty || b.cfSellQty || 0));
                break;
            case 'buyAmt':
                aValue = parseFloat(a.buyAmt || a.cfBuyAmt || 0);
                bValue = parseFloat(b.buyAmt || b.cfBuyAmt || 0);
                break;
            case 'sellAmt':
                aValue = parseFloat(a.sellAmt || a.cfSellAmt || 0);
                bValue = parseFloat(b.sellAmt || b.cfSellAmt || 0);
                break;
            case 'pnl':
                aValue = parseFloat(a.sellAmt || a.cfSellAmt || 0) - parseFloat(a.buyAmt || a.cfBuyAmt || 0);
                bValue = parseFloat(b.sellAmt || b.cfSellAmt || 0) - parseFloat(b.buyAmt || b.cfBuyAmt || 0);
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
    
    // Redisplay positions
    window.positionsManager.displayPositions();
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

// Legacy function for compatibility
function sortPositionsBySymbol() {
    sortTable('symbol');
}

// Function to sort positions by any column
function sortPositionsByColumn(column) {
    if (window.positionsManager) {
        window.positionsManager.sortDirection = window.positionsManager.sortDirection === 'asc' ? 'desc' : 'asc';
        var direction = window.positionsManager.sortDirection;
        
        window.positionsManager.positions.sort(function(a, b) {
            var valueA, valueB;
            
            switch(column) {
                case 'symbol':
                    valueA = (a.trdSym || a.sym || '').toLowerCase();
                    valueB = (b.trdSym || b.sym || '').toLowerCase();
                    break;
                case 'product':
                    valueA = (a.prod || '').toLowerCase();
                    valueB = (b.prod || '').toLowerCase();
                    break;
                case 'exchange':
                    valueA = (a.exSeg || '').toLowerCase();
                    valueB = (b.exSeg || '').toLowerCase();
                    break;
                case 'buyQty':
                    valueA = parseFloat(a.flBuyQty || a.cfBuyQty || 0);
                    valueB = parseFloat(b.flBuyQty || b.cfBuyQty || 0);
                    break;
                case 'sellQty':
                    valueA = parseFloat(a.flSellQty || a.cfSellQty || 0);
                    valueB = parseFloat(b.flSellQty || b.cfSellQty || 0);
                    break;
                case 'netQty':
                    valueA = (parseFloat(a.flBuyQty || a.cfBuyQty || 0)) - (parseFloat(a.flSellQty || a.cfSellQty || 0));
                    valueB = (parseFloat(b.flBuyQty || b.cfBuyQty || 0)) - (parseFloat(b.flSellQty || b.cfSellQty || 0));
                    break;
                case 'buyAmt':
                    valueA = parseFloat(a.buyAmt || a.cfBuyAmt || 0);
                    valueB = parseFloat(b.buyAmt || b.cfBuyAmt || 0);
                    break;
                case 'sellAmt':
                    valueA = parseFloat(a.sellAmt || a.cfSellAmt || 0);
                    valueB = parseFloat(b.sellAmt || b.cfSellAmt || 0);
                    break;
                case 'pnl':
                    valueA = parseFloat(a.sellAmt || a.cfSellAmt || 0) - parseFloat(a.buyAmt || a.cfBuyAmt || 0);
                    valueB = parseFloat(b.sellAmt || b.cfSellAmt || 0) - parseFloat(b.buyAmt || b.cfBuyAmt || 0);
                    break;
                case 'expiry':
                    valueA = a.expDt || '';
                    valueB = b.expDt || '';
                    break;
                case 'lastUpdated':
                    valueA = a.hsUpTm || '';
                    valueB = b.hsUpTm || '';
                    break;
                default:
                    return 0;
            }
            
            if (typeof valueA === 'string') {
                return direction === 'asc' ? valueA.localeCompare(valueB) : valueB.localeCompare(valueA);
            } else {
                return direction === 'asc' ? valueA - valueB : valueB - valueA;
            }
        });
        
        window.positionsManager.displayPositions();
    }
}

// Function to open place order modal
function openPlaceOrderModal(symbol, exchange, transactionType) {
    // Validate and clean symbol parameter
    if (!symbol || symbol === 'undefined' || symbol === 'null' || symbol.trim() === '') {
        console.error('Invalid symbol provided to openPlaceOrderModal:', symbol);
        alert('Invalid symbol. Please try again.');
        return;
    }
    
    var cleanSymbol = symbol.toString().trim().toUpperCase();
    
    document.getElementById('orderSymbol').value = cleanSymbol;
    document.getElementById('orderExchange').value = exchange || 'NSE';
    document.getElementById('orderTransactionType').value = transactionType || 'BUY';
    
    // Set default values
    document.getElementById('orderProduct').value = 'CNC';
    document.getElementById('orderType').value = 'MKT';
    document.getElementById('orderQuantity').value = '1';
    document.getElementById('orderPrice').value = '';
    document.getElementById('orderTriggerPrice').value = '';
    document.getElementById('orderValidity').value = 'DAY';
    document.getElementById('orderDisclosedQuantity').value = '0';
    
    // Update modal title based on transaction type
    var modalTitle = document.getElementById('placeOrderModalLabel');
    if (transactionType === 'BUY') {
        modalTitle.innerHTML = '<i class="fas fa-arrow-up text-success me-2"></i>Buy Order - ' + symbol;
    } else {
        modalTitle.innerHTML = '<i class="fas fa-arrow-down text-danger me-2"></i>Sell Order - ' + symbol;
    }
    
    var modal = new bootstrap.Modal(document.getElementById('placeOrderModal'));
    modal.show();
}

// Function to submit place order
function submitPlaceOrder() {
    var symbol = document.getElementById('orderSymbol').value;
    var exchange = document.getElementById('orderExchange').value;
    var product = document.getElementById('orderProduct').value;
    var price = document.getElementById('orderPrice').value || "0";
    var orderType = document.getElementById('orderType').value;
    var quantity = document.getElementById('orderQuantity').value;
    var validity = document.getElementById('orderValidity').value;
    var transactionType = document.getElementById('orderTransactionType').value;
    var disclosedQuantity = document.getElementById('orderDisclosedQuantity').value || "0";
    var triggerPrice = document.getElementById('orderTriggerPrice').value || "0";

    // Enhanced validation with detailed logging
    console.log('Submit Place Order - Symbol:', symbol, 'Type:', transactionType, 'Quantity:', quantity);

    if (!symbol || symbol.trim() === '' || symbol === 'undefined' || symbol === 'null') {
        console.error('Invalid symbol detected:', symbol);
        alert('Symbol is required and cannot be empty. Please try selecting the order again.');
        return;
    }

    if (!transactionType || (transactionType !== 'BUY' && transactionType !== 'SELL')) {
        console.error('Invalid transaction type:', transactionType);
        alert('Invalid transaction type. Please try again.');
        return;
    }

    if (!quantity || quantity <= 0 || isNaN(quantity)) {
        alert('Please enter a valid quantity greater than 0');
        return;
    }

    // For market orders, price should be 0
    if (orderType === 'MKT') {
        price = "0";
    } else if (orderType === 'L' && (!price || price <= 0)) {
        alert('Please enter a valid price for limit order');
        return;
    }

    if ((orderType === 'SL' || orderType === 'SL-M') && (!triggerPrice || triggerPrice <= 0)) {
        alert('Please enter a valid trigger price for stop loss order');
        return;
    }

    // Clean and prepare symbol
    var cleanSymbol = symbol.toString().trim().toUpperCase();
    
    // Convert transaction type for API compatibility - ensure we only send B or S
    var apiTransactionType;
    if (transactionType.toUpperCase() === 'BUY' || transactionType.toUpperCase() === 'B') {
        apiTransactionType = 'B';
    } else if (transactionType.toUpperCase() === 'SELL' || transactionType.toUpperCase() === 'S') {
        apiTransactionType = 'S';
    } else {
        apiTransactionType = 'B'; // Default to Buy
    }

    // Prepare order data for client.place_order API
    var orderData = {
        exchange_segment: exchange || "nse_cm",
        product: product || "CNC",
        price: price.toString(),
        order_type: orderType || "MKT",
        quantity: quantity.toString(),
        validity: validity || "DAY",
        trading_symbol: cleanSymbol,
        symbol: cleanSymbol, // Add this for compatibility
        transaction_type: apiTransactionType,
        amo: "NO",
        disclosed_quantity: disclosedQuantity.toString(),
        market_protection: "0",
        pf: "N",
        trigger_price: triggerPrice.toString(),
        tag: "POSITIONS_PAGE"
    };

    console.log('Placing order from positions page:', orderData);

    // Show loading state
    var submitButton = document.querySelector('#placeOrderModal .btn-primary');
    var originalText = submitButton.textContent;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Placing Order...';
    submitButton.disabled = true;

    // Make API call to place order
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/place-order', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            submitButton.textContent = originalText;
            submitButton.disabled = false;
            
            if (xhr.status === 200) {
                try {
                    var response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        alert('Order placed successfully! Order ID: ' + (response.order_id || 'N/A'));
                        bootstrap.Modal.getInstance(document.getElementById('placeOrderModal')).hide();
                        // Refresh positions after order placement
                        if (window.positionsManager) {
                            window.positionsManager.loadPositions();
                        }
                    } else {
                        alert('Error placing order: ' + (response.message || 'Unknown error'));
                    }
                } catch (e) {
                    alert('Error processing response: ' + e.message);
                }
            } else {
                try {
                    var errorResponse = JSON.parse(xhr.responseText);
                    alert('Error placing order: ' + (errorResponse.message || 'Request failed'));
                } catch (e) {
                    alert('Error placing order: Request failed with status ' + xhr.status);
                }
            }
        }
    };
    
    xhr.send(JSON.stringify(orderData));
}