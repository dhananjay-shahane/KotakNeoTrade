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
    this.isLoading = false;

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
    this.checkPriceUpdateStatus();

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

DealsManager.prototype.checkPriceUpdateStatus = function() {
    var self = this;

    // Check Google Finance scheduler status
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/api/google-finance-scheduler/status', true);
    xhr.setRequestHeader('Content-Type', 'application/json');

    xhr.onload = function() {
        if (xhr.status === 200) {
            var response = JSON.parse(xhr.responseText);
            var statusElement = document.getElementById('priceUpdateStatus');
            var lastUpdateElement = document.getElementById('lastPriceUpdate');

            if (response.status === 'running') {
                if (statusElement) {
                    statusElement.innerHTML = '<i class="fas fa-sync-alt fa-spin me-1"></i>Live CMP Updates';
                    statusElement.className = 'badge bg-success me-2';
                }
                if (lastUpdateElement) {
                    lastUpdateElement.textContent = 'Every 5 minutes';
                }
            } else {
                if (statusElement) {
                    statusElement.innerHTML = '<i class="fas fa-pause me-1"></i>CMP Updates Paused';
                    statusElement.className = 'badge bg-warning me-2';
                }
                if (lastUpdateElement) {
                    lastUpdateElement.textContent = 'Not running';
                }
            }
        }
    };

    xhr.onerror = function() {
        var statusElement = document.getElementById('priceUpdateStatus');
        if (statusElement) {
            statusElement.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>CMP Update Error';
            statusElement.className = 'badge bg-danger me-2';
        }
    };

    xhr.send();

    // Check status every 30 seconds
    setTimeout(function() {
        self.checkPriceUpdateStatus();
    }, 30000);
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

    // Prevent multiple simultaneous requests
    if (self.isLoading) {
        console.log('Request already in progress, skipping...');
        return;
    }

    self.isLoading = true;
    console.log('Loading deals from external database...');

    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/api/deals/user', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.timeout = 10000; // 10 second timeout

    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            self.isLoading = false;

            if (xhr.status === 200) {
                try {
                    var response = JSON.parse(xhr.responseText);

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

                        // Only update if data has changed
                        if (JSON.stringify(uniqueDeals) !== JSON.stringify(self.deals)) {
                            self.deals = uniqueDeals;
                            self.filteredDeals = self.deals.slice();
                            self.renderDealsTable();
                            self.updatePagination();
                            console.log('Updated ' + uniqueDeals.length + ' deals from database');
                        } else {
                            console.log('No data changes detected');
                        }
                    } else {
                        console.log('No deals found in API response');
                        if (self.deals.length === 0) {
                            self.deals = [];
                            self.filteredDeals = [];
                            self.renderDealsTable();
                            self.updatePagination();
                        }
                    }
                } catch (parseError) {
                    console.error('Failed to parse deals API response:', parseError);
                    self.showError('Invalid response from server');
                }
            } else if (xhr.status === 0) {
                console.error('Network error - request was aborted or connection failed');
                self.showError('Network connection error');
            } else {
                console.error('Deals API call failed with status:', xhr.status);
                self.showError('Failed to load deals from server (Status: ' + xhr.status + ')');
            }
        }
    };

    xhr.ontimeout = function() {
        self.isLoading = false;
        console.error('Request timeout');
        self.showError('Request timeout - please try again');
    };

    xhr.onerror = function() {
        self.isLoading = false;
        console.error('Network error occurred');
        self.showError('Network error occurred');
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
                '<p class="text-muted mb-3">You haven\'t added any deals yet</p>' +
                '<button class="btn btn-primary btn-sm me-2" onclick="createSampleDeals()">' +
                    '<i class="fas fa-plus me-1"></i>Create Sample Deals' +
                '</button>' +
                '<small class="text-muted d-block mt-2">Or visit the ETF Signals page to add deals from trading signals</small>' +
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
                            '<button class="btn btn-success btn-sm" onclick="buyTrade(\'' + (deal.symbol || '') + '\', ' + (deal.cmp || 0) + ')">'+
                                '<i class="fas fa-plus"></i> Buy </button>' +
                            '<button class="btn btn-danger btn-sm" onclick="sellTrade(\'' + (deal.symbol || '') + '\', ' + (deal.cmp || 0) + ')">'+
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

    var visibleDealsCount = document.getElementById('visibleDealsCount');
    var showingCount = document.getElementById('showingCount');
    var totalCount = document.getElementById('totalCount');

    if (visibleDealsCount) visibleDealsCount.textContent = this.filteredDeals.length;
    if (showingCount) showingCount.textContent = Math.min(endIndex, this.filteredDeals.length);
    if (totalCount) totalCount.textContent = this.filteredDeals.length;
};

DealsManager.prototype.updatePagination = function() {
    var totalPages = Math.ceil(this.filteredDeals.length / this.pageSize);

    var currentPageElement = document.getElementById('currentPage');
    var totalPagesElement = document.getElementById('totalPages');
    var prevBtn = document.getElementById('prevBtn');
    var nextBtn = document.getElementById('nextBtn');

    if (currentPageElement) currentPageElement.textContent = this.currentPage;
    if (totalPagesElement) totalPagesElement.textContent = totalPages;
    if (prevBtn) prevBtn.disabled = this.currentPage <= 1;
    if (nextBtn) nextBtn.disabled = this.currentPage >= totalPages;
};

DealsManager.prototype.startAutoRefresh = function() {
    if (this.refreshInterval) clearInterval(this.refreshInterval);
    if (this.autoRefresh) {
        var self = this;
        this.refreshInterval = setInterval(function() {
            // Only refresh if page is visible and not already loading
            if (!document.hidden && !self.isLoading) {
                self.loadDeals();
                // Update CMP using selected data source every refresh
                var dataSource = localStorage.getItem('data-source') || 'google';
                updateDealsCMP();
            }
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
    // Validate parameters before opening modal
    if (!symbol || symbol.trim() === '' || symbol === 'undefined') {
        showNotification('Invalid symbol provided. Cannot open buy trade modal.', 'error');
        console.error('buyTrade called with invalid symbol:', symbol);
        return;
    }

    if (!currentPrice || isNaN(currentPrice) || currentPrice <= 0) {
        currentPrice = 100; // Default fallback price
        console.warn('Invalid price provided, using fallback:', currentPrice);
    }
    console.log('Opening buy trade modal for:', symbol, 'at price:', currentPrice);

    var modal = new bootstrap.Modal(document.getElementById('tradeModal'));
    document.getElementById('tradeModalLabel').innerHTML = '<i class="fas fa-arrow-up text-success me-2"></i>Buy Trade';
    document.getElementById('tradeSymbol').value = symbol.trim().toUpperCase();
    document.getElementById('tradeType').value = 'BUY';
    document.getElementById('tradePrice').value = currentPrice.toFixed(2);
    document.getElementById('tradeQuantity').value = '1';

    // Update modal styling for buy order
    var modal_content = document.querySelector('#tradeModal .modal-content');
    modal_content.style.borderLeft = '4px solid #28a745';

    modal.show();
}

function sellTrade(symbol, currentPrice) {
    // Validate parameters before opening modal
    if (!symbol || symbol.trim() === '' || symbol === 'undefined') {
        showNotification('Invalid symbol provided. Cannot open sell trade modal.', 'error');
        console.error('sellTrade called with invalid symbol:', symbol);
        return;
    }

    if (!currentPrice || isNaN(currentPrice) || currentPrice <= 0) {
        currentPrice = 100; // Default fallback price
        console.warn('Invalid price provided, using fallback:', currentPrice);
    }

    console.log('Opening sell trade modal for:', symbol, 'at price:', currentPrice);

    var modal = new bootstrap.Modal(document.getElementById('tradeModal'));
    document.getElementById('tradeModalLabel').innerHTML = '<i class="fas fa-arrow-down text-danger me-2"></i>Sell Trade';
    document.getElementById('tradeSymbol').value = symbol.trim().toUpperCase();
    document.getElementById('tradeType').value = 'SELL';
    document.getElementById('tradePrice').value = currentPrice.toFixed(2);
    document.getElementById('tradeQuantity').value = '1';

    // Update modal styling for sell order
    var modal_content = document.querySelector('#tradeModal .modal-content');
    modal_content.style.borderLeft = '4px solid #dc3545';

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
    var orderType = document.getElementById('orderType').value;
    var productType = document.getElementById('productType').value;
    var price = parseFloat(document.getElementById('tradePrice').value) || 0;
    var quantity = parseInt(document.getElementById('tradeQuantity').value);
    var validity = document.getElementById('validity').value;
    var triggerPrice = parseFloat(document.getElementById('triggerPrice').value) || 0;

    // Enhanced validation with detailed logging
    console.log('Submit Trade - Symbol:', symbol, 'Type:', type, 'Quantity:', quantity);

    if (!symbol || symbol.trim() === '' || symbol === 'undefined' || symbol === 'null') {
        console.error('Invalid symbol detected:', symbol);
        showNotification('Symbol is required and cannot be empty. Please try selecting the trade again.', 'error');
        return;
    }

    if (!type || (type !== 'BUY' && type !== 'SELL')) {
        console.error('Invalid transaction type:', type);
        showNotification('Invalid transaction type. Please try again.', 'error');
        return;
    }

    if (!quantity || quantity <= 0 || isNaN(quantity)) {
        showNotification('Please enter a valid quantity greater than 0', 'error');
        return;
    }

    // For market orders, price should be 0
    if (orderType === 'MKT') {
        price = 0;
    } else if (orderType !== 'MKT' && price <= 0) {
        showNotification('Please enter a valid price for limit/stop loss orders', 'error');
        return;
    }

    // Prepare order data for API
    var orderData = {
        exchange_segment: "nse_cm",
        product: productType || "CNC",
        price: price.toString(),
        order_type: orderType || "MKT",
        quantity: quantity.toString(),
        validity: validity || "DAY",
        trading_symbol: symbol.toUpperCase(),
        symbol: symbol.toUpperCase(), // Add this for compatibility
        transaction_type: type === 'BUY' ? 'B' : 'S',
        amo: "NO",
        disclosed_quantity: "0",
        market_protection: "0",
        pf: "N",
        trigger_price: triggerPrice.toString(),
        tag: "DEALS_PAGE"
    };

    console.log('Placing order:', orderData);

    // Show loading state
    var submitBtn = document.querySelector('#tradeModal .btn-primary');
    if (!submitBtn) {
        showNotification('Submit button not found', 'error');
        return;
    }

    var originalText = submitBtn.textContent;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Placing Order...';
    submitBtn.disabled = true;

    // Call the place_order API with timeout
    var controller = new AbortController();
    var timeoutId = setTimeout(function() {
        controller.abort();
    }, 15000); // 15 second timeout

    fetch('/api/place-order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderData),
        signal: controller.signal
    })
    .then(function(response) {
        clearTimeout(timeoutId);

        // Try to get response text first
        return response.text().then(function(text) {
            if (!response.ok) {
                console.error('API Error Response:', text);
                var errorMsg = 'Server error';
                try {
                    var errorData = JSON.parse(text);
                    errorMsg = errorData.message || errorData.error || 'Request failed';
                } catch (e) {
                    errorMsg = 'Request failed with status ' + response.status;
                }
                throw new Error(errorMsg);
            }

            try {
                return JSON.parse(text);
            } catch (e) {
                throw new Error('Invalid response format');
            }
        });
    })
    .then(function(data) {
        // Reset button state
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;

        if (data && data.success) {
            var modal = bootstrap.Modal.getInstance(document.getElementById('tradeModal'));
            if (modal) {
                modal.hide();
            }

            // Show success notification with order details
            var orderTypeText = orderType === 'MKT' ? 'Market' : orderType === 'L' ? 'Limit' : 'Stop Loss';
            var priceText = orderType === 'MKT' ? 'at market price' : 'at ₹' + price;

            showNotification(
                orderTypeText + ' ' + type.toLowerCase() + ' order for ' + quantity + ' ' + symbol + ' ' + priceText + ' placed successfully!' +
                (data.order_id ? ' (Order ID: ' + data.order_id + ')' : ''),
                'success'
            );

            // Refresh deals data after a delay
            setTimeout(function() {
                if (window.dealsManager && !window.dealsManager.isLoading) {
                    window.dealsManager.loadDeals();
                }
            }, 2000);
        } else {
            // Show error notification
            showNotification('Order placement failed: ' + (data && data.message ? data.message : 'Unknown error'), 'error');
        }
    })
    .catch(function(error) {
        clearTimeout(timeoutId);
        // Reset button state
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;

        console.error('Order placement error:', error);
        if (error.name === 'AbortError') {
            showNotification('Order placement timed out - please try again', 'error');
        } else {
            showNotification('Order placement failed: ' + (error.message || 'Network error'), 'error');
        }
    });
}

// Enhanced sorting functionality for deals table
var sortState = {
    column: null,
    direction: 'asc'
};

function sortTable(column) {
    var tbody = document.getElementById('dealsTableBody');
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
            case 'date':
                aValue = new Date(a.dataset.date || 0);
                bValue = new Date(b.dataset.date || 0);
                break;
            default:
                return 0;
        }

        // Compare values
        var result;
        if (aValue instanceof Date) {
            result = aValue.getTime() - bValue.getTime();
        } else if (typeof aValue === 'string') {
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

// Notification function for user feedback
function showNotification(message, type) {
    // Create notification element
    var notification = document.createElement('div');
    notification.className = 'alert alert-' + (type === 'success' ? 'success' : 'danger') + ' alert-dismissible fade show position-fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';

    notification.innerHTML = 
        '<i class="fas fa-' + (type === 'success' ? 'check-circle' : 'exclamation-triangle') + ' me-2"></i>' +
        message +
        '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';

    document.body.appendChild(notification);

    // Auto remove after 5 seconds
    setTimeout(function() {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

// Function to update CMP values for deals page
function updateDealsCMP() {
    var dataSource = localStorage.getItem('data-source') || 'google';
    var apiEndpoint = dataSource === 'google' ? '/api/google-finance/update-etf-cmp' : '/api/yahoo/update-prices';
    var sourceName = dataSource === 'google' ? 'Google Finance' : 'Yahoo Finance';

    console.log('Updating deals CMP using ' + sourceName);

    fetch(apiEndpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Deals CMP update response from ' + sourceName + ':', data);

            // Refresh the deals table
            if (window.dealsManager) {
                window.dealsManager.loadDeals();
            }

            var updatedCount = data.updated_count || data.signals_updated || 0;
            showNotification('Updated CMP for ' + updatedCount + ' records from ' + sourceName, 'success');
        } else {
            console.error('Deals CMP update failed:', data.error);
            showNotification('Failed to update CMP from ' + sourceName + ': ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error updating deals CMP:', error);
        showNotification('Error updating CMP from ' + sourceName + ': ' + error.message, 'error');
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
    if (typeof showNotification === 'function') {
        showNotification('Data Source Changed to ' + sourceName + ' - Updating CMP...', 'info');
    }

    // Immediately update CMP when source changes
    if (newSource !== oldSource) {
        updateDealsCMP();
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

// Function to create // Sample deals creation functionality removed

// Auto CMP update functionality removedm // Google Finance CMP update functionality removeda// Auto CMP update functionality removede CMP update function for manual trigger
function forceCMPUpdate() {
    console.log('🚀 Force CMP update triggered by user');
    updateDealsCMPFromGoogleFinance();
}

// Initialize Deals Manager on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Deals Manager...');
    window.dealsManager = new DealsManager();

    // Load initial data
    window.dealsManager.loadDeals();

    // Check price update status
    window.dealsManager.checkPriceUpdateStatus();

    // Start automatic CMP updates
    startDealsCMPUpdates();

    // Update CMP immediately on page load
    setTimeout(() => {
        console.log('🚀 Initial deals CMP update on page load');
        updateDealsCMPFromGoogleFinance();
    }, 3000); // Wait 3 seconds for page to fully load

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

    // Pause auto-refresh when tab is not visible
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            console.log('Tab hidden - pausing auto-refresh');
            window.dealsManager.stopAutoRefresh();
        } else {
            console.log('Tab visible - resuming auto-refresh');
            if (window.dealsManager.autoRefresh) {
                window.dealsManager.startAutoRefresh();
                // Load fresh data when tab becomes visible
                window.dealsManager.loadDeals();
            }
        }
    });

    window.addEventListener('storage', function(e) {
        if (e.key === 'userDeals') {
            console.log('Deals updated in localStorage, refreshing...');
            if (!window.dealsManager.isLoading) {
                window.dealsManager.loadDeals();
            }
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

// Clean up interval when page unloads
window.addEventListener('beforeunload', function() {
    if (dealsCmpUpdateInterval) {
        clearInterval(dealsCmpUpdateInterval);
        dealsCmpUpdateInterval = null;
    }
});