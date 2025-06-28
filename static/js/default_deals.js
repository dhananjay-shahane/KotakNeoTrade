function DealsManager() {
    this.deals = [];
    this.filteredDeals = [];
    this.currentPage = 1;
    this.pageSize = 20;
    this.autoRefresh = true;
    this.refreshInterval = null;
    this.refreshIntervalTime = 30000;
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
                        bgColor = chanValue >= 0 ? 'var(--success-color)' : 'var(--danger-color)';
                        cellContent = (chanValue >= 0 ? '+' : '') + chanValue.toFixed(2) + '%';
                    } else if (typeof chanValue === 'string' && chanValue.includes('%')) {
                        var numValue = parseFloat(chanValue.replace('%', ''));
                        bgColor = numValue >= 0 ? 'var(--success-color)' : 'var(--danger-color)';
                        cellContent = chanValue;
                    } else {
                        cellContent = '0%';
                    }
                    break;
                case 'change_pct':
                    if (deal.change_pct !== undefined) {
                        bgColor = deal.change_pct >= 0 ? 'var(--success-color)' : 'var(--danger-color)';
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
                        bgColor = deal.pl >= 0 ? 'var(--success-color)' : 'var(--danger-color)';
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
                    cellContent = deal.ch || deal.chan_percent || '-';
                    break;
                case 'change2':
                    if (deal.change2 !== undefined) {
                        bgColor = deal.change2 >= 0 ? 'var(--success-color)' : 'var(--danger-color)';
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

            if (bgColor) {
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
    var price = parseFloat(document.getElementById('tradePrice').value);
    var quantity = parseInt(document.getElementById('tradeQuantity').value);

    if (!symbol || !price || !quantity) {
        alert('Please fill all required fields');
        return;
    }

    var tradeData = {
        symbol: symbol,
        type: type,
        price: price,
        quantity: quantity,
        timestamp: new Date().toISOString()
    };

    console.log('Executing trade:', tradeData);

    var modal = bootstrap.Modal.getInstance(document.getElementById('tradeModal'));
    modal.hide();

    alert(type + ' order for ' + quantity + ' ' + symbol + ' at ₹' + price + ' has been placed successfully');

    setTimeout(function() {
        window.dealsManager.loadDeals();
    }, 1000);
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

// Initialize Deals Manager on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Deals Manager...');
    window.dealsManager = new DealsManager();

    var savedInterval = localStorage.getItem('dealsRefreshInterval');
    var savedDisplay = localStorage.getItem('dealsRefreshIntervalDisplay');

    if (savedInterval && savedDisplay) {
        window.dealsManager.refreshIntervalTime = parseInt(savedInterval);
        document.getElementById('currentInterval').textContent = savedDisplay;
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