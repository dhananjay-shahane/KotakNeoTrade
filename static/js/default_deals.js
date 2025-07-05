function DealsManager() {
    this.deals = [];
    this.filteredDeals = [];
    this.currentPage = 1;
    this.pageSize = 20;
    this.autoRefresh = true;
    this.refreshInterval = null;
    this.refreshIntervalTime = 300000; // 5 minutes
    this.searchTimeout = null;
    this.sortDirection = 'asc';

    this.availableColumns = {
        'trade_signal_id': { label: 'ID', default: true, width: '50px', sortable: true },
        'symbol': { label: 'ETF', default: true, width: '80px', sortable: true },
        'pos': { label: 'POS', default: false, width: '50px', sortable: true },
        'thirty': { label: '30', default: false, width: '50px', sortable: true },
        'dh': { label: 'DH', default: false, width: '40px', sortable: true },
        'date': { label: 'DATE', default: true, width: '80px', sortable: true },
        'qty': { label: 'QTY', default: true, width: '60px', sortable: true },
        'ep': { label: 'EP', default: true, width: '70px', sortable: true },
        'cmp': { label: 'CMP', default: true, width: '70px', sortable: true },
        'chan_percent': { label: '%CHAN', default: true, width: '60px', sortable: true },
        'inv': { label: 'INV.', default: false, width: '70px', sortable: true },
        'tp': { label: 'TP', default: false, width: '60px', sortable: true },
        'tva': { label: 'TVA', default: false, width: '70px', sortable: true },
        'tpr': { label: 'TPR', default: false, width: '70px', sortable: true },
        'pl': { label: 'PL', default: true, width: '60px', sortable: true },
        'ed': { label: 'ED', default: false, width: '70px', sortable: true },
        'exp': { label: 'EXP', default: false, width: '70px', sortable: true },
        'pr': { label: 'PR', default: false, width: '80px', sortable: true },
        'pp': { label: 'PP', default: false, width: '50px', sortable: true },
        'iv': { label: 'IV', default: false, width: '60px', sortable: true },
        'ip': { label: 'IP', default: false, width: '60px', sortable: true },
        'nt': { label: 'NT', default: false, width: '120px', sortable: true },
        'qt': { label: 'QT', default: false, width: '60px', sortable: true },
        'seven': { label: '7', default: false, width: '50px', sortable: true },
        'ch': { label: '%CH', default: false, width: '60px', sortable: true },
        'actions': { label: 'ACTIONS', default: true, width: '80px', sortable: false }
    };

    this.selectedColumns = this.getDefaultColumns();
    this.init();
}

DealsManager.prototype.getDefaultColumns = function() {
    var defaultCols = [];
    for (var col in this.availableColumns) {
        if (this.availableColumns.hasOwnProperty(col) && this.availableColumns[col].default) {
            defaultCols.push(col);
        }
    }
    return defaultCols;
};

DealsManager.prototype.init = function() {
    this.updateTableHeaders();
    this.loadDeals();
    this.startAutoRefresh();
    this.setupEventListeners();
    this.setupColumnSettingsModal();

    var autoRefreshToggle = document.getElementById('autoRefreshToggle');
    var self = this;
    if (autoRefreshToggle) {
        autoRefreshToggle.addEventListener('change', function(e) {
            self.autoRefresh = e.target.checked;
            if (self.autoRefresh) {
                self.startAutoRefresh();
            } else {
                self.stopAutoRefresh();
            }
        });
    }
};

DealsManager.prototype.setupColumnSettingsModal = function() {
    var self = this;
    var modal = document.getElementById('columnSettingsModal');
    if (modal) {
        modal.addEventListener('show.bs.modal', function() {
            console.log('Column Settings modal opening...');
            self.generateColumnCheckboxes();
        });

        // Also generate checkboxes immediately to ensure they exist
        self.generateColumnCheckboxes();
    }
};

DealsManager.prototype.generateColumnCheckboxes = function() {
    var container = document.getElementById('columnCheckboxes');
    if (!container) {
        console.error('Column checkboxes container not found');
        return;
    }

    container.innerHTML = '';
    console.log('Generating column checkboxes for', Object.keys(this.availableColumns).length, 'columns');

    var self = this;
    var columns = Object.keys(this.availableColumns);
    for (var i = 0; i < columns.length; i++) {
        var column = columns[i];
        var colInfo = self.availableColumns[column];
        var colDiv = document.createElement('div');
        colDiv.className = 'col-md-4 col-lg-3 mb-2';

        var isChecked = false;
        for (var j = 0; j < self.selectedColumns.length; j++) {
            if (self.selectedColumns[j] === column) {
                isChecked = true;
                break;
            }
        }

        colDiv.innerHTML = 
            '<div class="form-check">' +
                '<input class="form-check-input" type="checkbox" id="col_' + column + '" ' +
                       (isChecked ? 'checked' : '') + '>' +
                '<label class="form-check-label text-light" for="col_' + column + '">' +
                    colInfo.label +
                '</label>' +
            '</div>';

        container.appendChild(colDiv);
    }
    console.log('Generated', columns.length, 'column checkboxes');
};

DealsManager.prototype.updateTableHeaders = function() {
    var headersRow = document.getElementById('tableHeaders');
    headersRow.innerHTML = '';

    var self = this;
    for (var i = 0; i < this.selectedColumns.length; i++) {
        var column = this.selectedColumns[i];
        var th = document.createElement('th');
        var colInfo = self.availableColumns[column];
        th.style.width = colInfo.width;
        th.className = 'text-center';
        th.style.backgroundColor = 'var(--secondary-color)';
        th.style.color = 'var(--text-primary)';
        th.style.fontWeight = '600';
        th.style.fontSize = '0.7rem';
        th.style.padding = '6px 3px';
        th.style.border = '1px solid var(--border-color)';
        th.style.position = 'sticky';
        th.style.top = '0';
        th.style.zIndex = '10';
        th.style.whiteSpace = 'nowrap';

        if (colInfo.sortable) {
            th.style.cursor = 'pointer';
            th.onclick = function(col) {
                return function() {
                    sortDefaultDealsByColumn(col);
                };
            }(column);
            th.innerHTML = colInfo.label + ' <i class="fas fa-sort ms-1"></i>';
            th.title = self.getColumnTooltip(column) + ' - Click to sort';
        } else {
            th.textContent = colInfo.label;
            th.title = self.getColumnTooltip(column);
        }

        headersRow.appendChild(th);
    }
};

DealsManager.prototype.getColumnTooltip = function(column) {
    var tooltips = {
        'trade_signal_id': 'Trade Signal ID',
        'symbol': 'Trading Symbol',
        'pos': 'Position (1=Long, 0=Short)',
        'thirty': '30 Day Performance',
        'dh': 'Days Held',
        'date': 'Order Date',
        'qty': 'Quantity',
        'ep': 'Entry Price',
        'cmp': 'Current Market Price',
        'chan_percent': 'Percentage Change',
        'change_pct': 'Percentage Change',
        'inv': 'Investment Amount',
        'tp': 'Target Price',
        'tva': 'Target Value Amount',
        'tpr': 'Target Profit Return',
        'pl': 'Profit/Loss',
        'ed': 'Entry Date',
        'pr': 'Price Range',
        'pp': 'Performance Points',
        'iv': 'Implied Volatility',
        'ip': 'Intraday Performance',
        'nt': 'Notes/Tags',
        'qt': 'Quote Time',
        'seven': '7 Day Change',
        'ch': 'Change Percentage',
        'change2': 'Percentage Change',
        'actions': 'Actions'
    };
    return tooltips[column] || column.toUpperCase();
};

DealsManager.prototype.setupEventListeners = function() {
    // Filter event listeners can be added here
};

// Global function for sync button
function syncDefaultDeals() {
    console.log('Syncing admin_trade_signals to default_deals...');

    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/sync-default-deals', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                try {
                    var response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        console.log('Sync successful:', response.message);
                        showSuccessMessage('Synced ' + response.synced_count + ' records from admin signals');
                        // Refresh the deals table after sync
                        if (window.dealsManager) {
                            window.dealsManager.loadDeals();
                        }
                    } else {
                        console.error('Sync failed:', response.error);
                        showErrorMessage('Sync failed: ' + response.error);
                    }
                } catch (e) {
                    console.error('Failed to parse sync response:', e);
                    showErrorMessage('Failed to parse server response');
                }
            } else {
                console.error('Sync request failed with status:', xhr.status);
                showErrorMessage('Failed to sync data from server');
            }
        }
    };
    xhr.send();
}

function showSuccessMessage(message) {
    var alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show position-fixed';
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = 
        '<i class="fas fa-check-circle me-2"></i>' + message +
        '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
    document.body.appendChild(alertDiv);

    setTimeout(function() {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

function showErrorMessage(message) {
    var alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed';
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = 
        '<i class="fas fa-exclamation-circle me-2"></i>' + message +
        '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
    document.body.appendChild(alertDiv);

    setTimeout(function() {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

DealsManager.prototype.loadDeals = function() {
    var self = this;
    console.log('Loading deals from external database...');

    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/api/default-deals-data', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                try {
                    var response = JSON.parse(xhr.responseText);
                    console.log('API Response:', response);

                    if (response.success && response.data && Array.isArray(response.data)) {
                        var uniqueDeals = response.data.map(function(deal) {
                            var changePercent = parseFloat(deal.price_change_percent || 0);
                            var pnl = parseFloat(deal.pnl || 0);
                            var investment = parseFloat(deal.investment_amount || 0);
                            var currentPrice = parseFloat(deal.current_price || deal.entry_price || 0);
                            var entryPrice = parseFloat(deal.entry_price || 0);
                            var quantity = parseInt(deal.quantity || 0);

                            return {
                                id: deal.id,
                                trade_signal_id: deal.admin_signal_id || deal.id,
                                symbol: deal.symbol || '',
                                pos: deal.position_type === 'BUY' ? 1 : 0,
                                qty: quantity,
                                ep: entryPrice,
                                cmp: currentPrice,
                                pl: pnl,
                                chan_percent: changePercent,
                                change_pct: changePercent,
                                inv: investment,
                                tp: parseFloat(deal.target_price || 0),
                                tva: parseFloat(deal.total_value || 0),
                                tpr: parseFloat(deal.profit_ratio || 0),
                                date: deal.entry_date || new Date().toISOString().split('T')[0],
                                status: deal.signal_strength || 'ACTIVE',
                                thirty: changePercent.toFixed(2) + '%',
                                dh: Math.floor((new Date() - new Date(deal.entry_date || new Date())) / (1000 * 60 * 60 * 24)) || 0,
                                ed: deal.entry_date || '',
                                pr: changePercent.toFixed(2) + '%',
                                pp: deal.notes ? deal.notes.substring(0, 10) + '...' : '-',
                                iv: investment.toLocaleString('en-IN'),
                                ip: changePercent > 0 ? '+' + changePercent.toFixed(1) + '%' : changePercent.toFixed(1) + '%',
                                nt: '--',
                                qt: new Date().toLocaleTimeString('en-GB', {hour: '2-digit', minute: '2-digit'}),
                                seven: changePercent.toFixed(2) + '%',
                                ch: changePercent.toFixed(2) + '%',
                                change2: changePercent,
                                admin_signal_id: deal.admin_signal_id
                            };
                        });

                        self.deals = uniqueDeals;
                        self.filteredDeals = self.deals.slice();
                        self.renderDealsTable();
                        self.updatePagination();
                        console.log('Loaded ' + uniqueDeals.length + ' deals from database');
                    } else {
                        console.log('No deals found in API response');
                        self.deals = [];
                        self.filteredDeals = [];
                        self.renderDealsTable();
                        self.updatePagination();
                    }
                } catch (parseError) {
                    console.error('Failed to parse deals API response:', parseError);
                    self.showError('Invalid response from server');
                }
            } else {
                console.error('Deals API call failed with status:', xhr.status);
                self.showError('Failed to load deals from server');
            }
        }
    };
    xhr.send();
};

DealsManager.prototype.renderDealsTable = function() {
    var tbody = document.getElementById('dealsTableBody');
    var startIndex = (this.currentPage - 1) * this.pageSize;
    var endIndex = startIndex + this.pageSize;
    var pageDeals = this.filteredDeals.slice(startIndex, endIndex);

    tbody.innerHTML = '';

    if (pageDeals.length === 0) {
        var row = document.createElement('tr');
        row.innerHTML = 
            '<td colspan="' + this.selectedColumns.length + '" class="text-center py-4">' +
                '<i class="fas fa-handshake fa-3x mb-3 text-primary"></i>' +
                '<h6 class="text-light">No Deals Found</h6>' +
                '<p class="text-muted mb-0">You haven\'t added any deals yet</p>' +
                '<small class="text-muted">Visit the ETF Signals page to add deals from trading signals</small>' +
            '</td>';
        tbody.appendChild(row);
        return;
    }

    var self = this;
    for (var i = 0; i < pageDeals.length; i++) {
        var deal = pageDeals[i];
        var row = document.createElement('tr');

        for (var j = 0; j < self.selectedColumns.length; j++) {
            var columnKey = self.selectedColumns[j];
            var cell = document.createElement('td');
            cell.className = 'text-center';
            cell.style.padding = '4px 3px';
            cell.style.border = '1px solid var(--border-color)';
            cell.style.fontSize = '0.75rem';

            var cellContent = '';
            var bgColor = '';
            var style = '';

            switch(columnKey) {
                case 'trade_signal_id':
                    cellContent = '<span class="badge bg-info">' + (deal.trade_signal_id || deal.admin_signal_id || deal.id || '-') + '</span>';
                    break;
                case 'symbol':
                    cellContent = '<strong>' + (deal.symbol || '') + '</strong>';
                    break;
                case 'thirty':
                    cellContent = deal.thirty || '-';
                    break;
                case 'dh':
                    cellContent = deal.dh !== undefined ? deal.dh + 'd' : '0d';
                    break;
                case 'date':
                    cellContent = deal.date || '';
                    break;
                case 'pos':
                    cellContent = deal.pos === 1 ? '1' : '0';
                    break;
                case 'qty':
                    cellContent = deal.qty ? deal.qty.toLocaleString('en-IN') : '';
                    break;
                case 'ep':
                    cellContent = deal.ep ? '₹' + deal.ep.toFixed(2) : '';
                    break;
                case 'cmp':
                    cellContent = deal.cmp ? '₹' + deal.cmp.toFixed(2) : '';
                    break;
                case 'chan_percent':
                    var chanValue = deal.chan_percent || deal.change_pct || '';
                    if (typeof chanValue === 'number') {
                        style = self.getGradientBackgroundColor(chanValue);
                        cellContent = (chanValue >= 0 ? '+' : '') + chanValue.toFixed(2) + '%';
                    } else if (typeof chanValue === 'string' && chanValue.includes('%')) {
                        var numValue = parseFloat(chanValue.replace('%', ''));
                        style = self.getGradientBackgroundColor(numValue);
                        cellContent = chanValue;
                    } else {
                        cellContent = '0%';
                    }
                    break;
                case 'change_pct':
                    if (deal.change_pct !== undefined) {
                        style = self.getGradientBackgroundColor(deal.change_pct);
                        cellContent = (deal.change_pct >= 0 ? '+' : '') + deal.change_pct.toFixed(2) + '%';
                    }
                    break;
                case 'inv':
                    cellContent = deal.inv ? '₹' + deal.inv.toLocaleString('en-IN') : '';
                    break;
                case 'tp':
                    cellContent = deal.tp ? '₹' + deal.tp.toFixed(2) : '-';
                    break;
                case 'tva':
                    cellContent = deal.tva ? '₹' + deal.tva.toLocaleString('en-IN') : '';
                    break;
                case 'tpr':
                    cellContent = deal.tpr ? '₹' + deal.tpr.toFixed(0) : '0';
                    break;
                case 'pl':
                    if (deal.pl !== undefined) {
                        style = self.getGradientBackgroundColor(deal.pl);
                        cellContent = '₹' + (deal.pl >= 0 ? '+' : '') + deal.pl.toFixed(0);
                    }
                    break;
                case 'ed':
                    cellContent = deal.ed || '';
                    break;
                case 'exp':
                    cellContent = deal.exp || '-';
                    break;
                case 'pr':
                    cellContent = deal.pr || '-';
                    break;
                case 'pp':
                    cellContent = deal.pp || '-';
                    break;
                case 'iv':
                    cellContent = '<span class="badge bg-info">' + (deal.iv || '--') + '</span>';
                    break;
                case 'ip':
                    cellContent = deal.ip || '-';
                    if (deal.change_pct > 0) {
                        cell.style.color = 'var(--success-color)';
                    } else if (deal.change_pct < 0) {
                        cell.style.color = 'var(--danger-color)';
                    }
                    break;
                case 'nt':
                    cellContent = '<small>' + (deal.nt || '-') + '</small>';
                    break;
                case 'qt':
                    cellContent = '<small>' + (deal.qt || '-') + '</small>';
                    break;
                case 'seven':
                    cellContent = deal.seven || '-';
                    break;
                case 'ch':
                    var chValue = deal.ch || deal.chan_percent || '';
                    if (chValue && chValue !== '-') {
                        var numChValue = parseFloat(chValue.toString().replace('%', ''));
                        if (!isNaN(numChValue)) {
                            style = self.getGradientBackgroundColor(numChValue);
                            cellContent = chValue;
                        } else {
                            cellContent = chValue;
                        }
                    } else {
                        cellContent = '-';
                    }
                    break;
                case 'change2':
                    if (deal.change2 !== undefined) {
                        style = self.getGradientBackgroundColor(deal.change2);
                        cellContent = (deal.change2 >= 0 ? '+' : '') + deal.change2.toFixed(2) + '%';
                    }
                    break;
                case 'actions':
                    cellContent = 
                       '<div class="btn-group btn-group-sm">' +
                            '<button class="btn btn-success btn-sm" onclick="buyTrade(\'' + deal.symbol + '\', ' + deal.cmp + ')">'+
                                '<i class="fas fa-plus"></i> Buy </button>' +
                            '<button class="btn btn-danger btn-sm" onclick="sellTrade(\'' + deal.symbol + '\', ' + deal.cmp + ')"">'+
                                '<i class="fas fa-minus"></i> Sell' +
                            '</button>' +
                        '</div>';
                    break;
                default:
                    cellContent = '';
            }

            if (style && style !== '') {
                cell.setAttribute('style', (cell.getAttribute('style') || '') + '; ' + style + ' font-weight: bold;');
            } else if (bgColor) {
                cell.style.backgroundColor = bgColor;
                cell.style.color = 'white';
                cell.style.fontWeight = 'bold';
            }

            cell.innerHTML = cellContent;
            row.appendChild(cell);
        }

        tbody.appendChild(row);
    }

    document.getElementById('visibleDealsCount').textContent = this.filteredDeals.length;
    document.getElementById('showingCount').textContent = Math.min(endIndex, this.filteredDeals.length);
    document.getElementById('totalCount').textContent = this.filteredDeals.length;
};

DealsManager.prototype.updatePagination = function() {
    var totalPages = Math.ceil(this.filteredDeals.length / this.pageSize);

    document.getElementById('currentPage').textContent = this.currentPage;
    document.getElementById('totalPages').textContent = totalPages;

    document.getElementById('prevBtn').disabled = this.currentPage <= 1;
    document.getElementById('nextBtn').disabled = this.currentPage >= totalPages;
};

DealsManager.prototype.startAutoRefresh = function() {
    if (this.refreshInterval) clearInterval(this.refreshInterval);
    if (this.autoRefresh) {
        var self = this;
        this.refreshInterval = setInterval(function() {
            self.loadDeals();
            // Update CMP using selected data source every refresh
            var dataSource = localStorage.getItem('data-source') || 'google';
            updateDefaultDealsCMP();
        }, this.refreshIntervalTime);
    }
};

DealsManager.prototype.stopAutoRefresh = function() {
    if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
        this.refreshInterval = null;
    }
};

DealsManager.prototype.showError = function(message) {
    var tbody = document.getElementById('dealsTableBody');
    tbody.innerHTML = 
        '<tr>' +
            '<td colspan="' + this.selectedColumns.length + '" class="text-center py-4">' +
                '<i class="fas fa-exclamation-triangle fa-3x mb-3 text-danger"></i>' +
                '<h6 class="text-danger">' + message + '</h6>' +
                '<button class="btn btn-outline-primary btn-sm mt-2" onclick="window.dealsManager.loadDeals()">' +
                    '<i class="fas fa-sync me-1"></i>Retry' +
                '</button>' +
            '</td>' +
        '</tr>';
};

function applyFilters() {
    var orderType = document.getElementById('orderTypeFilter').value;
    var status = document.getElementById('statusFilter').value;
    var symbol = document.getElementById('symbolFilter').value.toLowerCase();
    var minPnl = parseFloat(document.getElementById('minPnlFilter').value) || -Infinity;
    var maxPnl = parseFloat(document.getElementById('maxPnlFilter').value) || Infinity;

    window.dealsManager.filteredDeals = window.dealsManager.deals.filter(function(deal) {
        var matchesOrderType = !orderType || (orderType === 'BUY' && deal.pos === 1) || (orderType === 'SELL' && deal.pos === 0);
        var matchesStatus = !status || deal.status === status;
        var matchesSymbol = !symbol || deal.symbol.toLowerCase().indexOf(symbol) !== -1;
        var matchesPnl = deal.pl >= minPnl && deal.pl <= maxPnl;

        return matchesOrderType && matchesStatus && matchesSymbol && matchesPnl;
    });

    window.dealsManager.currentPage = 1;
    window.dealsManager.renderDealsTable();
    window.dealsManager.updatePagination();
}

function clearFilters() {
    document.getElementById('orderTypeFilter').value = '';
    document.getElementById('statusFilter').value = '';
    document.getElementById('symbolFilter').value = '';
    document.getElementById('minPnlFilter').value = '';
    document.getElementById('maxPnlFilter').value = '';

    window.dealsManager.filteredDeals = window.dealsManager.deals.slice();
    window.dealsManager.currentPage = 1;
    window.dealsManager.renderDealsTable();
    window.dealsManager.updatePagination();
}

function refreshDeals() {
    window.dealsManager.loadDeals();
}

// Buy/Sell Trading Functions for Default Deals
function buyTrade(symbol, currentPrice) {
    showTradeModal(symbol, currentPrice, 'BUY');
}

function sellTrade(symbol, currentPrice) {
    showTradeModal(symbol, currentPrice, 'SELL');
}

function showTradeModal(symbol, currentPrice, tradeType) {
    // Update modal title and icon
    var modalTitle = tradeType === 'BUY' ? 'Buy Trade' : 'Sell Trade';
    var iconClass = tradeType === 'BUY' ? 'fas fa-plus' : 'fas fa-minus';
    document.getElementById('tradeModalLabel').innerHTML = '<i class="' + iconClass + ' me-2"></i>' + modalTitle;

    // Set form values
    document.getElementById('tradeSymbol').value = symbol;
    document.getElementById('tradeType').value = tradeType;
    document.getElementById('tradePrice').value = currentPrice || 0;
    document.getElementById('tradeQuantity').value = 1;

    // Reset form to defaults
    document.getElementById('orderType').value = 'L'; // Default to Limit
    document.getElementById('productType').value = 'CNC';
    document.getElementById('validityType').value = 'DAY';
    document.getElementById('triggerPrice').value = 0;

    // Enable/disable price fields based on order type
    togglePriceFields();

    var modal = new bootstrap.Modal(document.getElementById('tradeModal'));
    modal.show();
}

// Toggle price fields based on order type
function togglePriceFields() {
    var orderType = document.getElementById('orderType').value;
    var priceField = document.getElementById('tradePrice');
    var triggerField = document.getElementById('triggerPrice');

    if (orderType === 'MKT') {
        // Market order - disable price and trigger
        priceField.disabled = true;
        priceField.value = 0;
        triggerField.disabled = true;
        triggerField.value = 0;
    } else if (orderType === 'L') {
        // Limit order - enable price, disable trigger
        priceField.disabled = false;
        triggerField.disabled = true;
        triggerField.value = 0;
    } else if (orderType === 'SL') {
        // Stop Loss - enable both price and trigger
        priceField.disabled = false;
        triggerField.disabled = false;
    } else if (orderType === 'SL-M') {
        // Stop Loss Market - disable price, enable trigger
        priceField.disabled = true;
        priceField.value = 0;
        triggerField.disabled = false;
    }
}

function submitAdvancedTrade() {
    var symbol = document.getElementById('tradeSymbol').value;
    var tradeType = document.getElementById('tradeType').value;
    var orderType = document.getElementById('orderType').value;
    var productType = document.getElementById('productType').value;
    var price = document.getElementById('tradePrice').value;
    var quantity = document.getElementById('tradeQuantity').value;
    var validity = document.getElementById('validityType').value;
    var triggerPrice = document.getElementById('triggerPrice').value;

    if (!symbol || !quantity || quantity <= 0) {
        showNotification('Please enter valid trade details', 'error');
        return;
    }

    // Validate price for limit orders
    if ((orderType === 'L' || orderType === 'SL') && (!price || price <= 0)) {
        showNotification('Please enter a valid price for limit orders', 'error');
        return;
    }

    // Validate trigger price for stop loss orders
    if ((orderType === 'SL' || orderType === 'SL-M') && (!triggerPrice || triggerPrice <= 0)) {
        showNotification('Please enter a valid trigger price for stop loss orders', 'error');
        return;
    }

    var orderData = {
        symbol: symbol,
        quantity: quantity,
        transaction_type: tradeType === 'BUY' ? 'B' : 'S',
        order_type: orderType,
        price: orderType === 'MKT' || orderType === 'SL-M' ? '0' : price,
        trigger_price: orderType === 'SL' || orderType === 'SL-M' ? triggerPrice : '0',
        exchange_segment: 'nse_cm',
        product: productType,
        validity: validity,
        disclosed_quantity: '0',
        amo: 'NO',
        market_protection: '0',
        pf: 'N'
    };

    var submitBtn = document.querySelector('#tradeModal .btn-primary');
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
            bootstrap.Modal.getInstance(document.getElementById('tradeModal')).hide();
            refreshDeals();
        } else {
            showNotification('Failed to place order: ' + data.message, 'error');<previous_generation>```text

</previous_generation>
            return;
        }
    })
    .catch(function(error) {
        submitBtn.innerHTML = '<i class="fas fa-chart-line me-2"></i>Place Trade';
        submitBtn.disabled = false;
        console.error('Error:', error);
        showNotification('Error placing order: ' + error.message, 'error');
    });
}

// Keep the old function for compatibility
function submitTrade() {
    submitAdvancedTrade();
}

// Enhanced sorting functionality for default deals table
var sortState = {
    column: null,
    direction: 'asc'
};

function sortTable(column) {
    var tbody = document.getElementById('defaultDealsTableBody');
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
                aValue = (a.dataset.symbol || '').toLowerCase();
                bValue = (b.dataset.symbol || '').toLowerCase();
                break;
            case 'quantity':
                aValue = parseFloat(a.dataset.quantity) || 0;
                bValue = parseFloat(b.dataset.quantity) || 0;
                break;
            case 'entryPrice':
                aValue = parseFloat(a.dataset.entryPrice) || 0;
                bValue = parseFloat(b.dataset.entryPrice) || 0;
                break;
            case 'currentPrice':
                aValue = parseFloat(a.dataset.currentPrice) || 0;
                bValue = parseFloat(b.dataset.currentPrice) || 0;
                break;
            case 'pnl':
                aValue = parseFloat(a.dataset.pnl) || 0;
                bValue = parseFloat(b.dataset.pnl) || 0;
                break;
            case 'investment':
                aValue = parseFloat(a.dataset.investment) || 0;
                bValue = parseFloat(b.dataset.investment) || 0;
                break;
            case 'currentValue':
                aValue = parseFloat(a.dataset.currentValue) || 0;
                bValue = parseFloat(b.dataset.currentValue) || 0;
                break;
            case 'chanPercent':
                aValue = parseFloat(a.dataset.chanPercent) || 0;
                bValue = parseFloat(b.dataset.chanPercent) || 0;
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

function previousPage() {
    if (window.dealsManager.currentPage > 1) {
        window.dealsManager.currentPage--;
        window.dealsManager.renderDealsTable();
        window.dealsManager.updatePagination();
    }
}

function nextPage() {
    var totalPages = Math.ceil(window.dealsManager.filteredDeals.length / window.dealsManager.pageSize);
    if (window.dealsManager.currentPage < totalPages) {
        window.dealsManager.currentPage++;
        window.dealsManager.renderDealsTable();
        window.dealsManager.updatePagination();
    }
}

function viewDealDetails(dealId) {
    alert('Viewing details for deal ' + dealId);
}

function modifyOrder(dealId) {
    alert('Modify order functionality for ' + dealId + ' - to be implemented');
}

function cancelOrder(dealId) {
    if (confirm('Are you sure you want to cancel order ' + dealId + '?')) {
        alert('Cancel order functionality for ' + dealId + ' - to be implemented');
    }
}

function buyTrade(symbol, currentPrice) {
    var modal = new bootstrap.Modal(document.getElementById('tradeModal'));
    document.getElementById('tradeModalLabel').innerHTML = '<i class="fas fa-arrow-up text-success me-2"></i>Buy Trade';
    document.getElementById('tradeSymbol').value = symbol;
    document.getElementById('tradeType').value = 'BUY';
    document.getElementById('tradePrice').value = currentPrice.toFixed(2);
    document.getElementById('tradeQuantity').value = '1';
    modal.show();
}

function sellTrade(symbol, currentPrice) {
    var modal = new bootstrap.Modal(document.getElementById('tradeModal'));
    document.getElementById('tradeModalLabel').innerHTML = '<i class="fas fa-arrow-down text-danger me-2"></i>Sell Trade';
    document.getElementById('tradeSymbol').value = symbol;
    document.getElementById('tradeType').value = 'SELL';
    document.getElementById('tradePrice').value = currentPrice.toFixed(2);
    document.getElementById('tradeQuantity').value = '1';
    modal.show();
}

function viewChart(symbol) {
    var modal = new bootstrap.Modal(document.getElementById('chartModal'));
    document.getElementById('chartModalLabel').innerHTML = '<i class="fas fa-chart-line text-info me-2"></i>Chart - ' + symbol;

    var chartContainer = document.getElementById('chartContainer');
    chartContainer.innerHTML = '<canvas id="priceChart" width="400" height="200"></canvas>';

    var ctx = document.getElementById('priceChart').getContext('2d');
    var labels = [];
    var data = [];
    var basePrice = Math.random() * 1000 + 500;

    for (var i = 29; i >= 0; i--) {
        var date = new Date();
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }));

        var volatility = 0.02;
        var change = (Math.random() - 0.5) * volatility;
        var price = basePrice * (1 + change * i * 0.1);
        data.push(price.toFixed(2));
    }

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: symbol + ' Price',
                data: data,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: symbol + ' - 30 Day Price Chart',
                    color: '#fff'
                },
                legend: {
                    labels: {
                        color: '#fff'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        color: '#fff',
                        callback: function(value) {
                            return '₹' + value;
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                x: {
                    ticks: {
                        color: '#fff'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });

    modal.show();
}

function setRefreshInterval(intervalMs, displayText) {
    // Only allow 5 minute intervals
    if (intervalMs !== 300000) {
        intervalMs = 300000;
        displayText = '5 Min';
    }

    window.dealsManager.refreshIntervalTime = intervalMs;
    document.getElementById('currentInterval').textContent = displayText;

    if (window.dealsManager.autoRefresh) {
        window.dealsManager.startAutoRefresh();
    }

    localStorage.setItem('dealsRefreshInterval', intervalMs);
    localStorage.setItem('dealsRefreshIntervalDisplay', displayText);
}

function submitTrade() {
    var symbol = document.getElementById('tradeSymbol').value;
    var type = document.getElementById('tradeType').value;
    var price = parseFloat(document.getElementById('tradePrice').value) || 0;
    var quantity = parseInt(document.getElementById('tradeQuantity').value);

    if (!symbol || !quantity || quantity <= 0) {
        alert('Please enter a valid symbol and quantity');
        return;
    }

    if (price <= 0) {
        alert('Please enter a valid price');
        return;
    }

    // Prepare order data for client.place_order API
    var orderData = {
        exchange_segment: "nse_cm",
        product: "MIS", // Intraday for default deals
        price: price.toString(),
        order_type: "L", // Limit order
        quantity: quantity.toString(),
        validity: "DAY",
        trading_symbol: symbol,
        transaction_type: type,
        amo: "NO",
        disclosed_quantity: "0",
        market_protection: "0",
        pf: "N",
        trigger_price: "0",
        tag: "DEFAULT_DEALS_PAGE"
    };

    console.log('Placing order from default deals page:', orderData);

    // Show loading state
    var submitBtn = document.querySelector('#tradeModal .btn-primary');
    var originalText = submitBtn.textContent;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Placing Order...';
    submitBtn.disabled = true;

    // Make API call to place order
    fetch('/api/place-order', {
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
            var modal = bootstrap.Modal.getInstance(document.getElementById('tradeModal'));
            modal.hide();
            alert(type + ' order for ' + quantity + ' ' + symbol + ' at ₹' + price + ' placed successfully! Order ID: ' + (data.order_id || 'N/A'));

            // Refresh deals after order placement
            setTimeout(function() {
                window.dealsManager.loadDeals();
            }, 1000);
        } else {
            alert('Error placing order: ' + (data.message || 'Unknown error'));
        }
    })
    .catch(function(error) {
        // Reset button state
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;

        console.error('Error placing order:', error);
        alert('Error placing order: ' + error.message);
    });
}

function exportDeals() {
    var data = window.dealsManager.filteredDeals;
    if (!data || data.length === 0) {
        alert('No data to export');
        return;
    }

    var csvContent = "data:text/csv;charset=utf-8," + 
        Object.keys(data[0]).join(",") + "\n" +
        data.map(function(row){return Object.values(row).join(",")} ).join("\n");

    var encodedUri = encodeURI(csvContent);
    var link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", 'deals_' + new Date().toISOString().split('T')[0] + '.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Global functions for column settings and filters
function applyColumnSettings() {
    console.log('Applying column settings...');

    if (!window.dealsManager) {
        console.error('DealsManager not initialized');
        return;
    }

    window.dealsManager.selectedColumns = [];

    var columns = Object.keys(window.dealsManager.availableColumns);
    for (var i = 0; i < columns.length; i++) {
        var column = columns[i];
        var checkbox = document.getElementById('col_' + column);
        if (checkbox && checkbox.checked) {
            window.dealsManager.selectedColumns.push(column);
        }
    }

    console.log('Selected columns:', window.dealsManager.selectedColumns);

    // Update table headers and re-render
    window.dealsManager.updateTableHeaders();
    window.dealsManager.renderDealsTable();

    // Close modal safely
    var modal = document.getElementById('columnSettingsModal');
    if (modal) {
        var modalInstance = bootstrap.Modal.getInstance(modal);
        if (modalInstance) {
            modalInstance.hide();
        } else {
            // Fallback: hide modal manually
            modal.classList.remove('show');
            modal.style.display = 'none';
            document.body.classList.remove('modal-open');
            var backdrop = document.querySelector('.modal-backdrop');
            if (backdrop) backdrop.remove();
        }
    }

    console.log('Column settings applied successfully');
}

function selectAllColumns() {
    console.log('Selecting all columns...');
    if (!window.dealsManager) {
        console.error('DealsManager not initialized');
        return;
    }

    var columns = Object.keys(window.dealsManager.availableColumns);
    for (var i = 0; i < columns.length; i++) {
        var column = columns[i];
        var checkbox = document.getElementById('col_' + column);
        if (checkbox) checkbox.checked = true;
    }
    console.log('All columns selected');
}

function resetDefaultColumns() {
    console.log('Resetting to default columns...');
    if (!window.dealsManager) {
        console.error('DealsManager not initialized');
        return;
    }

    var columns = Object.keys(window.dealsManager.availableColumns);
    for (var i = 0; i < columns.length; i++) {
        var column = columns[i];
        var checkbox = document.getElementById('col_' + column);
        if (checkbox) {
            checkbox.checked = window.dealsManager.availableColumns[column].default;
        }
    }
    console.log('Reset to default columns completed');
}

// Function to sort default deals by any column
function sortDefaultDealsByColumn(column) {
    if (window.dealsManager) {
        window.dealsManager.sortDirection = window.dealsManager.sortDirection === 'asc' ? 'desc' : 'asc';
        var direction = window.dealsManager.sortDirection;

        window.dealsManager.filteredDeals.sort(function(a, b) {
            var valueA, valueB;

            switch(column) {
                case 'symbol':
                    valueA = (a.symbol || '').toLowerCase();
                    valueB = (b.symbol || '').toLowerCase();
                    break;
                case 'qty':
                    valueA = parseFloat(a.qty || 0);
                    valueB = parseFloat(b.qty || 0);
                    break;
                case 'ep':
                    valueA = parseFloat(a.ep || 0);
                    valueB = parseFloat(b.ep || 0);
                    break;
                case 'cmp':
                    valueA = parseFloat(a.cmp || 0);
                    valueB = parseFloat(b.cmp || 0);
                    break;
                case 'change_pct':
                    valueA = parseFloat(a.change_pct || 0);
                    valueB = parseFloat(b.change_pct || 0);
                    break;
                case 'inv':
                    valueA = parseFloat(a.inv || 0);
                    valueB = parseFloat(b.inv || 0);
                    break;
                case 'tp':
                    valueA = parseFloat(a.tp || 0);
                    valueB = parseFloat(b.tp || 0);
                    break;
                case 'pl':
                    valueA = parseFloat(a.pl || 0);
                    valueB = parseFloat(b.pl || 0);
                    break;
                case 'date':
                    valueA = a.date || '';
                    valueB = b.date || '';
                    break;
                case 'pos':
                    valueA = a.pos || 0;
                    valueB = b.pos || 0;
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

        window.dealsManager.renderDealsTable();
        window.dealsManager.updatePagination();
    }
}

// Gradient Background Color Function for percentage values
DealsManager.prototype.getGradientBackgroundColor = function(value) {
    var numValue = parseFloat(value);
    if (isNaN(numValue)) return '';

    var intensity = Math.min(Math.abs(numValue) / 3, 1); // Scale to 0-1, max at 3%
    var alpha = 0.4 + (intensity * 0.6); // Alpha from 0.4 to 1.0

    if (numValue < 0) {
        // Red gradient for negative values
        if (intensity <= 0.3) {
            // Light red for small negative values
            return 'background-color: rgba(220, 53, 69, ' + (alpha * 0.6) + '); color: #fff;'; // Light red
        } else if (intensity <= 0.6) {
            // Medium red
            return 'background-color: rgba(220, 53, 69, ' + (alpha * 0.8) + '); color: #fff;'; // Medium red
        } else {
            // Dark red for large negative values
            return 'background-color: rgba(220, 53, 69, ' + alpha + '); color: #fff;'; // Dark red
        }
    } else if (numValue > 0) {
        // Green gradient for positive values
        if (intensity <= 0.3) {
            // Light green for small positive values
            return 'background-color: rgba(25, 135, 84, ' + (alpha * 0.6) + '); color: #fff;'; // Light green
        } else if (intensity <= 0.6) {
            // Medium green
            return 'background-color: rgba(25, 135, 84, ' + (alpha * 0.8) + '); color: #fff;'; // Medium green
        } else {
            // Dark green for large positive values
            return 'background-color: rgba(25, 135, 84, ' + alpha + '); color: #fff;'; // Dark green
        }
    }
    return '';
};

// Function to update CMP values for default deals page
function updateDefaultDealsCMP() {
    var dataSource = localStorage.getItem('data-source') || 'google';
    var apiEndpoint = dataSource === 'google' ? '/api/google-finance/update-etf-cmp' : '/api/yahoo/update-prices';
    var sourceName = dataSource === 'google' ? 'Google Finance' : 'Yahoo Finance';

    console.log('Updating default deals CMP using ' + sourceName);

    fetch(apiEndpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Default deals CMP update response from ' + sourceName + ':', data);

            // Refresh the deals table
            if (window.dealsManager) {
                window.dealsManager.loadDeals();
            }

            var updatedCount = data.updated_count || data.signals_updated || 0;
            showSuccessMessage('Updated CMP for ' + updatedCount + ' records from ' + sourceName);
        } else {
            console.error('Default deals CMP update failed:', data.error);
            showErrorMessage('Failed to update CMP from ' + sourceName + ': ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error updating default deals CMP:', error);
        showErrorMessage('Error updating CMP from ' + sourceName + ': ' + error.message);
    });
}

// Data source switching functions
function switchDataSource(newSource) {
    var oldSource = localStorage.getItem('data-source') || 'google';
    localStorage.setItem('data-source', newSource);

    var sourceName = newSource === 'google' ? 'Google Finance' : 'Yahoo Finance';

    // Update UI indicator
    var currentDataSourceSpan = document.getElementById('currentDataSource');
    if (currentDataSourceSpan) {
        currentDataSourceSpan.textContent = sourceName;
    }

    // Show immediate notification
    if (typeof showSuccessMessage === 'function') {
        showSuccessMessage('Data Source Changed to ' + sourceName + ' - Updating CMP...');
    }

    // Immediately update CMP when source changes
    if (newSource !== oldSource) {
        updateDefaultDealsCMP();
    }
}

function updateCurrentDataSourceIndicator() {
    var dataSource = localStorage.getItem('data-source') || 'google';
    var sourceName = dataSource === 'google' ? 'Google Finance' : 'Yahoo Finance';

    var currentDataSourceSpan = document.getElementById('currentDataSource');
    if (currentDataSourceSpan) {
        currentDataSourceSpan.textContent = sourceName;
    }
}

// Initialize Deals Manager on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Deals Manager...');
    window.dealsManager = new DealsManager();

    // Set default data source to Google Finance if not already set
    if (!localStorage.getItem('data-source')) {
        localStorage.setItem('data-source', 'google');
    }

    // Ensure Google Finance is selected by default
    switchDataSource('google');
    updateCurrentDataSourceIndicator();

    var savedInterval = localStorage.getItem('dealsRefreshInterval');
    var savedDisplay = localStorage.getItem('dealsRefreshIntervalDisplay');

    if (savedInterval && savedDisplay && parseInt(savedInterval) === 300000) {
        window.dealsManager.refreshIntervalTime = parseInt(savedInterval);
        document.getElementById('currentInterval').textContent = savedDisplay;
    } else {
        // Force 5 minute interval
        window.dealsManager.refreshIntervalTime = 300000;
        if (document.getElementById('currentInterval')) {
            document.getElementById('currentInterval').textContent = '5 Min';
        }
    }

    window.addEventListener('storage', function(e) {
        if (e.key === 'userDeals') {
            console.log('Deals updated in localStorage, refreshing...');
            window.dealsManager.loadDeals();
        }
    });

    document.addEventListener('shown.bs.dropdown', function(e) {
        var dropdown = e.target.closest('.dropdown');
        var toggle = dropdown.querySelector('.dropdown-toggle');
        var menu = dropdown.querySelector('.dropdown-menu');

        if (menu && toggle) {
            var rect = toggle.getBoundingClientRect();
            var menuHeight = 200;
            var menuWidth = 160;

            menu.style.position = 'fixed';
            menu.style.zIndex = '10000';
            menu.style.transform = 'none';
            menu.style.margin = '0';

            var top = rect.bottom + 2;
            var left = rect.left;

            if (top + menuHeight > window.innerHeight - 20) {
                top = rect.top - menuHeight - 2;
            }

            if (left + menuWidth > window.innerWidth - 20) {
                left = rect.right - menuWidth;
            }

            if (left < 10) {
                left = 10;
            }

            menu.style.top = top + 'px';
            menu.style.left = left + 'px';
            menu.style.right = 'auto';
            menu.style.bottom = 'auto';
        }
    });

    document.addEventListener('hidden.bs.dropdown', function(e) {
        var dropdown = e.target.closest('.dropdown');
        var menu = dropdown.querySelector('.dropdown-menu');

        if (menu) {
            menu.style.position = '';
            menu.style.top = '';
            menu.style.left = '';
            menu.style.right = '';
            menu.style.bottom = '';
            menu.style.transform = '';
            menu.style.margin = '';
            menu.style.zIndex = '';
        }
    });
});

// Auto CMP update variables for default deals
let defaultDealsCmpUpdateInterval = null;

// Function to update CMP from Google Finance for default deals
function updateDefaultDealsCMPFromGoogleFinance() {
    console.log('🔄 Updating default deals CMP from Google Finance...');

    fetch('/api/google-finance/update-etf-cmp', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('✅ Default deals CMP updated successfully:', data.updated_count, 'records');
            
            // Show success notification
            showSuccessMessage(`Updated CMP for ${data.updated_count || 0} records from Google Finance`);
            
            // Refresh the deals table after update
            if (window.dealsManager) {
                window.dealsManager.loadDeals();
            }
        } else {
            console.error('❌ Default deals CMP update failed:', data.error);
            showErrorMessage(`CMP update failed: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('❌ Error updating default deals CMP:', error);
        showErrorMessage(`Error updating CMP: ${error.message}`);
    });
}

// Function to start automatic CMP updates for default deals
function startDefaultDealsCMPUpdates() {
    // Clear any existing interval
    if (defaultDealsCmpUpdateInterval) {
        clearInterval(defaultDealsCmpUpdateInterval);
    }

    // Set up 5-minute interval for CMP updates
    defaultDealsCmpUpdateInterval = setInterval(() => {
        console.log('🕐 Auto default deals CMP update triggered (5min interval)');
        updateDefaultDealsCMPFromGoogleFinance();
    }, 5 * 60 * 1000); // 5 minutes in milliseconds

    console.log('✅ Auto default deals CMP updates started (every 5 minutes)');
}

// Force CMP update function for manual trigger
function forceCMPUpdate() {
    console.log('🚀 Force CMP update triggered by user');
    updateDefaultDealsCMPFromGoogleFinance();
}

// Initialize when document is ready
$(document).ready(function() {
    console.log('Default deals page loaded, initializing...');

    // Initialize the default deals manager
    window.defaultDealsManager = new DealsManager();

    // Load initial data
    window.defaultDealsManager.loadDeals();

    // Start automatic CMP updates
    startDefaultDealsCMPUpdates();

    // Update CMP immediately on page load
    setTimeout(() => {
        console.log('🚀 Initial default deals CMP update on page load');
        updateDefaultDealsCMPFromGoogleFinance();
    }, 3000); // Wait 3 seconds for page to fully load
});

// Clean up interval when page unloads
window.addEventListener('beforeunload', function() {
    if (defaultDealsCmpUpdateInterval) {
        clearInterval(defaultDealsCmpUpdateInterval);
        defaultDealsCmpUpdateInterval = null;
    }
});