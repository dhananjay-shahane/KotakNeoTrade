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
        'pos': { label: 'POS', default: true, width: '50px', sortable: true },
        'thirty': { label: '30', default: true, width: '50px', sortable: true },
        'dh': { label: 'DH', default: true, width: '40px', sortable: true },
        'date': { label: 'DATE', default: true, width: '80px', sortable: true },
        'qty': { label: 'QTY', default: true, width: '60px', sortable: true },
        'ep': { label: 'EP', default: true, width: '70px', sortable: true },
        'cmp': { label: 'CMP', default: true, width: '70px', sortable: true },
        'chan_percent': { label: '%CHAN', default: true, width: '60px', sortable: true },
        'inv': { label: 'INV.', default: true, width: '70px', sortable: true },
        'tp': { label: 'TP', default: true, width: '60px', sortable: true },
        'tva': { label: 'TVA', default: true, width: '70px', sortable: true },
        'tpr': { label: 'TPR', default: true, width: '70px', sortable: true },
        'pl': { label: 'PL', default: true, width: '60px', sortable: true },
        'ed': { label: 'ED', default: true, width: '70px', sortable: true },
        'exp': { label: 'EXP', default: true, width: '70px', sortable: true },
        'pr': { label: 'PR', default: true, width: '80px', sortable: true },
        'pp': { label: 'PP', default: true, width: '50px', sortable: true },
        'iv': { label: 'IV', default: true, width: '60px', sortable: true },
        'ip': { label: 'IP', default: true, width: '60px', sortable: true },
        'nt': { label: 'NT', default: true, width: '120px', sortable: true },
        'qt': { label: 'QT', default: true, width: '60px', sortable: true },
        'seven': { label: '7', default: true, width: '50px', sortable: true },
        'ch': { label: '%CH', default: true, width: '60px', sortable: true },
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
            self.generateColumnCheckboxes();
        });
    }
};

DealsManager.prototype.generateColumnCheckboxes = function() {
    var container = document.getElementById('columnCheckboxes');
    container.innerHTML = '';

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
                    sortDealsByColumn(col);
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
        'symbol': 'Trading Symbol',
        'thirty': '30 Day Performance',
        'dh': 'Days Held',
        'date': 'Order Date',
        'pos': 'Position Type',
        'qty': 'Quantity',
        'ep': 'Entry Price',
        'cmp': 'Current Market Price',
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
        'change2': 'Percentage Change',
        'actions': 'Actions'
    };
    return tooltips[column] || column.toUpperCase();
};

DealsManager.prototype.setupEventListeners = function() {
    // Filter event listeners can be added here
};

DealsManager.prototype.loadDeals = function() {
    var self = this;
    console.log('Loading deals from external database...');

    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/api/deals/user', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                try {
                    var response = JSON.parse(xhr.responseText);
                    console.log('API Response:', response);

                    if (response.success && response.deals && Array.isArray(response.deals)) {
                        var uniqueDeals = response.deals.map(function(deal) {
                            return {
                                id: deal.id,
                                trade_signal_id: deal.trade_signal_id || deal.id || '',
                                symbol: deal.symbol || deal.etf || '',
                                pos: deal.pos || (deal.position_type === 'LONG' ? 1 : -1),
                                qty: deal.qty || deal.quantity || 0,
                                ep: parseFloat(deal.ep || deal.entry_price || 0),
                                cmp: parseFloat(deal.cmp || deal.current_price || deal.entry_price || 0),
                                pl: parseFloat(deal.pl || deal.pnl_amount || 0),
                                chan_percent: deal.chan_percent || (deal.pnl_percent ? deal.pnl_percent.toFixed(2) + '%' : '0%'),
                                inv: parseFloat(deal.inv || deal.invested_amount || 0),
                                tp: parseFloat(deal.tp || deal.target_price || 0),
                                tva: parseFloat(deal.tva || 0) || (parseFloat(deal.target_price || 0) * (deal.quantity || 0)),
                                tpr: parseFloat(deal.tpr || 0),
                                date: deal.signal_date || deal.date || (deal.entry_date ? deal.entry_date.split('T')[0] : ''),
                                status: deal.status || 'ACTIVE',
                                thirty: deal.thirty || '0%',
                                dh: deal.dh || deal.days_held || 0,
                                ed: deal.ed || (deal.entry_date ? deal.entry_date.split('T')[0] : ''),
                                exp: deal.exp || '',
                                pr: deal.pr || '0%',
                                pp: deal.pp || '--',
                                iv: deal.iv || '',
                                ip: deal.ip || (deal.pnl_percent ? (deal.pnl_percent > 0 ? '+' : '') + deal.pnl_percent.toFixed(1) + '%' : '0%'),
                                nt: deal.nt || deal.notes || '--',
                                qt: deal.qt || new Date().toLocaleTimeString('en-GB', {hour: '2-digit', minute: '2-digit'}),
                                seven: deal.seven || '0%',
                                ch: deal.ch || deal.chan_percent || '0%',
                                entry_price: parseFloat(deal.entry_price || deal.ep || 0),
                                current_price: parseFloat(deal.current_price || deal.cmp || deal.entry_price || 0),
                                invested_amount: parseFloat(deal.invested_amount || deal.inv || 0),
                                pnl_amount: parseFloat(deal.pnl_amount || deal.pl || 0),
                                pnl_percent: parseFloat(deal.pnl_percent || 0),
                                deal_type: deal.deal_type || 'SIGNAL'
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

// Gradient Background Color Function for percentage values
DealsManager.prototype.getGradientBackgroundColor = function(value) {
    var numValue = parseFloat(value);
    if (isNaN(numValue)) return '';

    var intensity = Math.min(Math.abs(numValue) / 5, 1); // Scale to 0-1, max at 5%
    var alpha = 0.3 + (intensity * 0.5); // Alpha from 0.3 to 0.8

    if (numValue < 0) {
        // Red gradient for negative values
        if (intensity <= 0.3) {
            // Light red for small negative values
            return 'background-color: rgba(255, 182, 193, ' + alpha + '); color: #000;'; // Light pink
        } else if (intensity <= 0.6) {
            // Medium red
            return 'background-color: rgba(255, 99, 71, ' + alpha + '); color: #fff;'; // Tomato
        } else {
            // Dark red for large negative values
            return 'background-color: rgba(139, 0, 0, ' + alpha + '); color: #fff;'; // Dark red
        }
    } else if (numValue > 0) {
        // Green gradient for positive values
        if (intensity <= 0.3) {
            // Light green for small positive values
            return 'background-color: rgba(144, 238, 144, ' + alpha + '); color: #000;'; // Light green
        } else if (intensity <= 0.6) {
            // Medium green
            return 'background-color: rgba(50, 205, 50, ' + alpha + '); color: #fff;'; // Lime green
        } else {
            // Dark green for large positive values
            return 'background-color: rgba(0, 100, 0, ' + alpha + '); color: #fff;'; // Dark green
        }
    }

    return '';
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
                    cellContent = '<span class="badge bg-info">' + (deal.trade_signal_id || deal.id || '-') + '</span>';
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
                    var chanValue = deal.chan_percent || '';
                    style = self.getGradientBackgroundColor(chanValue.replace('%', ''));
                    cellContent = chanValue;
                    break;
                case 'change_pct':
                    if (deal.change_pct !== undefined) {
                        var changePctValue = deal.change_pct;
                        style = self.getGradientBackgroundColor(changePctValue);
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
                        var plValue = deal.pl;
                        style = self.getGradientBackgroundColor(plValue);
                        cellContent = '₹' + (deal.pl >= 0 ? '+' : '') + deal.pl.toFixed(0);
                    }
                    break;
                case 'ed':
                    cellContent = deal.ed || '';
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
                    cellContent = '<small>--</small>';
                    break;
                case 'qt':
                    cellContent = '<small>' + (deal.qt || '-') + '</small>';
                    break;
                case 'seven':
                    cellContent = deal.seven || '-';
                    break;
                case 'ch':
                    cellContent = deal.ch || '-';
                    break;
                case 'exp':
                    cellContent = deal.exp || '-';
                    break;
                case 'entry_price':
                    cellContent = deal.entry_price ? '₹' + deal.entry_price.toFixed(2) : '';
                    break;
                case 'current_price':
                    cellContent = deal.current_price ? '₹' + deal.current_price.toFixed(2) : '';
                    break;
                case 'invested_amount':
                    cellContent = deal.invested_amount ? '₹' + deal.invested_amount.toLocaleString('en-IN') : '';
                    break;
                case 'pnl_amount':
                    if (deal.pnl_amount !== undefined) {
                        var pnlAmountValue = deal.pnl_amount;
                        style = self.getGradientBackgroundColor(pnlAmountValue);
                        cellContent = '₹' + deal.pnl_amount.toLocaleString('en-IN');
                    }
                    break;
                case 'pnl_percent':
                    if (deal.pnl_percent !== undefined) {
                        var pnlPercentValue = deal.pnl_percent;
                        style = self.getGradientBackgroundColor(pnlPercentValue);
                        cellContent = (deal.pnl_percent >= 0 ? '+' : '') + deal.pnl_percent.toFixed(2) + '%';
                    }
                    break;
                case 'status':
                    var statusClass = deal.status === 'ACTIVE' ? 'bg-success' : deal.status === 'CLOSED' ? 'bg-secondary' : 'bg-warning';
                    cellContent = '<span class="badge ' + statusClass + '">' + (deal.status || 'ACTIVE') + '</span>';
                    break;
                case 'deal_type':
                    cellContent = '<span class="badge bg-primary">' + (deal.deal_type || 'SIGNAL') + '</span>';
                    break;
                case 'change2':
                    if (deal.change2 !== undefined) {
                        var change2Value = deal.change2;
                        style = self.getGradientBackgroundColor(change2Value);
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

            if (style) {
                cell.setAttribute('style', cell.getAttribute('style') + '; ' + style);
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
    document.getElementById('currentInterval').textContent = displayText;    if (window.dealsManager.autoRefresh) {
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

// Function to sort deals by any column
function sortDealsByColumn(column) {
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