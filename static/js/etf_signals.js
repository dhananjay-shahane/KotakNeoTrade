// ETF Signals Manager - ES5 Compatible
function ETFSignalsManager() {
    var self = this;
    this.signals = [];
    this.filteredSignals = [];
    this.currentPage = 1;
    this.itemsPerPage = 25;
    this.isLoading = false;
    this.refreshInterval = null;
    this.sortField = 'id';
    this.sortDirection = 'asc';
    
    // Column visibility settings
    this.availableColumns = [
        { key: 'etf', label: 'ETF', visible: true },
        { key: 'thirty', label: '30', visible: true },
        { key: 'dh', label: 'DH', visible: true },
        { key: 'date', label: 'DATE', visible: true },
        { key: 'qty', label: 'QTY', visible: true },
        { key: 'ep', label: 'EP', visible: true },
        { key: 'cmp', label: 'CMP', visible: true },
        { key: 'chan', label: '%CHAN', visible: true },
        { key: 'inv', label: 'INV.', visible: true },
        { key: 'tp', label: 'TP', visible: false },
        { key: 'tva', label: 'TVA', visible: false },
        { key: 'tpr', label: 'TPR', visible: false },
        { key: 'pl', label: 'PL', visible: true },
        { key: 'ed', label: 'ED', visible: false },
        { key: 'exp', label: 'EXP', visible: false },
        { key: 'pr', label: 'PR', visible: false },
        { key: 'pp', label: 'PP', visible: false },
        { key: 'iv', label: 'IV', visible: false },
        { key: 'ip', label: 'IP', visible: false },
        { key: 'nt', label: 'NT', visible: false },
        { key: 'qt', label: 'QT', visible: false },
        { key: 'seven', label: '7', visible: false },
        { key: 'ch', label: '%CH', visible: true },
        { key: 'actions', label: 'ACTIONS', visible: true }
    ];

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            self.init();
        });
    } else {
        this.init();
    }
}

ETFSignalsManager.prototype.init = function() {
    console.log('ETF Signals Manager initialized');
    this.loadColumnSettings();
    this.setupEventListeners();
    this.setupColumnSettings();
    this.loadSignals();
    this.startAutoRefresh();
};

ETFSignalsManager.prototype.setupEventListeners = function() {
    var self = this;

    // Refresh button
    var refreshBtn = document.getElementById('refreshSignalsBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            self.loadSignals();
        });
    }

    // Auto-refresh controls
    var autoRefreshToggle = document.getElementById('autoRefreshToggle');
    if (autoRefreshToggle) {
        autoRefreshToggle.addEventListener('change', function(e) {
            if (e.target.checked) {
                self.startAutoRefresh();
            } else {
                self.stopAutoRefresh();
            }
        });
    }

    // Search functionality
    var searchInput = document.getElementById('signalSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            self.applyFilters();
        });
    }

    // Items per page selector
    var itemsPerPageSelect = document.getElementById('itemsPerPage');
    if (itemsPerPageSelect) {
        itemsPerPageSelect.addEventListener('change', function(e) {
            self.itemsPerPage = parseInt(e.target.value);
            self.currentPage = 1;
            self.renderSignalsTable();
            self.updatePagination();
        });
    }
};

ETFSignalsManager.prototype.loadSignals = function() {
    var self = this;

    if (this.isLoading) return;

    this.isLoading = true;
    this.showLoadingState();

    console.log('Loading ETF signals from API...');

    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/api/etf-signals-data', true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            self.isLoading = false;
            self.hideLoadingState();

            console.log('API Response Status:', xhr.status);
            console.log('API Response Text:', xhr.responseText);

            if (xhr.status === 200) {
                try {
                    var data = JSON.parse(xhr.responseText);
                    console.log('Parsed API data:', data);

                    if (data.success) {
                        self.signals = data.signals || [];
                        self.filteredSignals = self.signals.slice();
                        self.renderSignalsTable();
                        self.updatePagination();
                        self.updatePortfolioSummary(data.portfolio);
                        self.showSuccessMessage('Loaded ' + self.signals.length + ' signals');
                        console.log('Successfully loaded', self.signals.length, 'signals');
                    } else {
                        throw new Error(data.error || 'Failed to load signals');
                    }
                } catch (parseError) {
                    console.error('Error parsing response:', parseError);
                    self.showErrorMessage('Error parsing server response');
                }
            } else {
                console.error('API request failed with status:', xhr.status);
                self.showErrorMessage('Failed to load signals: Server error ' + xhr.status);
            }
        }
    };
    xhr.send();
};

ETFSignalsManager.prototype.renderSignalsTable = function() {
    var tbody = document.getElementById('signalsTableBody');
    if (!tbody) {
        console.error('Table body not found');
        return;
    }

    var startIdx = (this.currentPage - 1) * this.itemsPerPage;
    var endIdx = startIdx + this.itemsPerPage;
    var pageSignals = this.filteredSignals.slice(startIdx, endIdx);

    if (pageSignals.length === 0) {
        tbody.innerHTML = '<tr><td colspan="25" class="text-center text-muted">No ETF signals found</td></tr>';
        return;
    }

    var self = this;
    tbody.innerHTML = '';

    for (var i = 0; i < pageSignals.length; i++) {
        var signal = pageSignals[i];
        var row = self.createSignalRow(signal);
        tbody.appendChild(row);
    }

    console.log('Rendered', pageSignals.length, 'signals in table');
};

ETFSignalsManager.prototype.createSignalRow = function(signal) {
    var row = document.createElement('tr');

    // Extract and format signal data
    var symbol = signal.etf || signal.symbol || 'N/A';
    var entryPrice = parseFloat(signal.ep || signal.entry_price || 0);
    var currentPrice = parseFloat(signal.cmp || signal.current_price || entryPrice);
    var quantity = parseInt(signal.qty || signal.quantity || 0);
    var pnl = parseFloat(signal.pl || signal.pnl || 0);
    var changePct = parseFloat(signal.change_pct || signal.pp || 0);
    var investment = parseFloat(signal.inv || signal.investment_amount || (entryPrice * quantity));
    var targetPrice = parseFloat(signal.tp || signal.target_price || entryPrice * 1.1);
    var status = signal.status || 'ACTIVE';
    var positionType = signal.position_type || (signal.pos === 1 ? 'LONG' : 'SHORT') || 'LONG';

    // Parse percentage change from chan field (remove % symbol)
    var chanValue = signal.chan || '';
    if (chanValue && typeof chanValue === 'string' && chanValue.includes('%')) {
        changePct = parseFloat(chanValue.replace('%', ''));
    }

    // Calculate values if not provided
    if (!changePct && entryPrice > 0) {
        changePct = ((currentPrice - entryPrice) / entryPrice) * 100;
    }

    if (!pnl && quantity > 0 && entryPrice > 0) {
        pnl = (currentPrice - entryPrice) * quantity;
    }

    // Create table cells based on visible columns
    var cells = '';
    for (var i = 0; i < this.availableColumns.length; i++) {
        var column = this.availableColumns[i];
        if (!column.visible) continue;
        
        var cellValue = '';
        var cellStyle = '';
        
        switch (column.key) {
            case 'etf':
                cellValue = '<span class="fw-bold text-primary">' + symbol + '</span>';
                break;
            case 'thirty':
                cellValue = signal.thirty || '--';
                break;
            case 'dh':
                cellValue = signal.dh || '0';
                break;
            case 'date':
                cellValue = signal.date || '--';
                break;
            case 'qty':
                cellValue = '<span class="badge bg-info">' + quantity + '</span>';
                break;
            case 'ep':
                cellValue = '₹' + entryPrice.toFixed(2);
                break;
            case 'cmp':
                cellValue = '<span class="cmp-value fw-bold" data-symbol="' + symbol + '">₹' + currentPrice.toFixed(2) + '</span>';
                break;
            case 'chan':
                var chanDisplay = signal.chan || changePct.toFixed(2) + '%';
                cellStyle = this.getGradientBackgroundColor(changePct);
                cellValue = '<span class="fw-bold">' + chanDisplay + '</span>';
                break;
            case 'inv':
                cellValue = '₹' + investment.toFixed(0);
                break;
            case 'tp':
                cellValue = '₹' + targetPrice.toFixed(2);
                break;
            case 'tva':
                cellValue = '₹' + (signal.tva || (currentPrice * quantity)).toFixed(2);
                break;
            case 'tpr':
                cellValue = signal.tpr || '--';
                break;
            case 'pl':
                var plClass = pnl >= 0 ? 'text-success' : 'text-danger';
                cellValue = '<span class="fw-bold ' + plClass + '">₹' + pnl.toFixed(2) + '</span>';
                break;
            case 'ed':
                cellValue = signal.ed || '--';
                break;
            case 'exp':
                cellValue = signal.exp || '--';
                break;
            case 'pr':
                cellValue = signal.pr || '--';
                break;
            case 'pp':
                cellValue = signal.pp || '--';
                break;
            case 'iv':
                cellValue = signal.iv || '--';
                break;
            case 'ip':
                cellValue = signal.ip || '--';
                break;
            case 'nt':
                cellValue = signal.nt || '--';
                break;
            case 'qt':
                cellValue = signal.qt || quantity;
                break;
            case 'seven':
                cellValue = signal.seven || '--';
                break;
            case 'ch':
                var chValue = signal.ch || changePct.toFixed(2) + '%';
                cellStyle = this.getGradientBackgroundColor(changePct);
                cellValue = '<span class="fw-bold">' + chValue + '</span>';
                break;
            case 'actions':
                cellValue = '<button class="btn btn-sm btn-success" onclick="addDeal(\'' + symbol + '\', ' + currentPrice + ')"><i class="fas fa-plus me-1"></i>Add Deal</button>';
                break;
            default:
                cellValue = '--';
        }
        
        cells += '<td style="' + cellStyle + '">' + cellValue + '</td>';
    }
    
    row.innerHTML = cells;
    return row;
};

// Gradient Background Color Function for %CH column
ETFSignalsManager.prototype.getGradientBackgroundColor = function(value) {
    var numValue = parseFloat(value);
    if (isNaN(numValue)) return '';
    
    var intensity = Math.min(Math.abs(numValue) / 10, 1); // Scale to 0-1, max at 10%
    var alpha = 0.2 + (intensity * 0.6); // Alpha from 0.2 to 0.8
    
    if (numValue < 0) {
        // Red gradient for negative values
        if (intensity <= 0.3) {
            // Light red for small negative values
            return 'background: rgba(255, 182, 193, ' + alpha + ')'; // Light pink
        } else if (intensity <= 0.6) {
            // Medium red
            return 'background: rgba(255, 99, 71, ' + alpha + ')'; // Tomato
        } else {
            // Dark red for large negative values
            return 'background: rgba(139, 0, 0, ' + alpha + ')'; // Dark red
        }
    } else if (numValue > 0) {
        // Green gradient for positive values
        if (intensity <= 0.3) {
            // Light green for small positive values
            return 'background: rgba(144, 238, 144, ' + alpha + ')'; // Light green
        } else if (intensity <= 0.6) {
            // Medium green
            return 'background: rgba(50, 205, 50, ' + alpha + ')'; // Lime green
        } else {
            // Dark green for large positive values
            return 'background: rgba(0, 128, 0, ' + alpha + ')'; // Green
        }
    }
    return '';
};

ETFSignalsManager.prototype.updateTableHeaders = function() {
    var headerRow = document.getElementById('tableHeaders');
    if (!headerRow) return;
    
    headerRow.innerHTML = '';
    
    for (var i = 0; i < this.availableColumns.length; i++) {
        var column = this.availableColumns[i];
        if (column.visible) {
            var th = document.createElement('th');
            th.style.cursor = 'pointer';
            th.title = column.label + ' - Click to sort';
            if (column.key !== 'actions') {
                th.setAttribute('onclick', 'sortSignalsByColumn(\'' + column.key + '\')');
                th.innerHTML = column.label + ' <i class="fas fa-sort ms-1"></i>';
            } else {
                th.innerHTML = column.label;
            }
            headerRow.appendChild(th);
        }
    }
};

// Column Management Functions
ETFSignalsManager.prototype.loadColumnSettings = function() {
    var savedSettings = localStorage.getItem('etfSignalsColumnSettings');
    if (savedSettings) {
        try {
            var settings = JSON.parse(savedSettings);
            for (var i = 0; i < this.availableColumns.length; i++) {
                var column = this.availableColumns[i];
                if (settings[column.key] !== undefined) {
                    column.visible = settings[column.key];
                }
            }
        } catch (e) {
            console.error('Error loading column settings:', e);
        }
    }
};

ETFSignalsManager.prototype.saveColumnSettings = function() {
    var settings = {};
    for (var i = 0; i < this.availableColumns.length; i++) {
        var column = this.availableColumns[i];
        settings[column.key] = column.visible;
    }
    localStorage.setItem('etfSignalsColumnSettings', JSON.stringify(settings));
};

ETFSignalsManager.prototype.setupColumnSettings = function() {
    var self = this;
    var container = document.getElementById('columnCheckboxes');
    if (!container) return;

    container.innerHTML = '';
    
    for (var i = 0; i < this.availableColumns.length; i++) {
        var column = this.availableColumns[i];
        var colDiv = document.createElement('div');
        colDiv.className = 'col-md-4 mb-2';
        
        var checkDiv = document.createElement('div');
        checkDiv.className = 'form-check';
        
        var checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'form-check-input';
        checkbox.id = 'col_' + column.key;
        checkbox.checked = column.visible;
        checkbox.setAttribute('data-column', column.key);
        
        var label = document.createElement('label');
        label.className = 'form-check-label text-light';
        label.setAttribute('for', checkbox.id);
        label.textContent = column.label;
        
        checkDiv.appendChild(checkbox);
        checkDiv.appendChild(label);
        colDiv.appendChild(checkDiv);
        container.appendChild(colDiv);
    }
};

// Global functions for column management
function selectAllColumns() {
    if (window.etfSignalsManager) {
        for (var i = 0; i < window.etfSignalsManager.availableColumns.length; i++) {
            window.etfSignalsManager.availableColumns[i].visible = true;
        }
        window.etfSignalsManager.setupColumnSettings();
        window.etfSignalsManager.updateTableHeaders();
        window.etfSignalsManager.renderSignalsTable();
    }
}

function resetDefaultColumns() {
    if (window.etfSignalsManager) {
        var defaultVisible = ['etf', 'thirty', 'dh', 'date', 'qty', 'ep', 'cmp', 'chan', 'inv', 'pl', 'ch', 'actions'];
        for (var i = 0; i < window.etfSignalsManager.availableColumns.length; i++) {
            var column = window.etfSignalsManager.availableColumns[i];
            column.visible = defaultVisible.indexOf(column.key) !== -1;
        }
        window.etfSignalsManager.setupColumnSettings();
        window.etfSignalsManager.updateTableHeaders();
        window.etfSignalsManager.renderSignalsTable();
    }
}

function applyColumnSettings() {
    if (window.etfSignalsManager) {
        var checkboxes = document.querySelectorAll('#columnCheckboxes input[type="checkbox"]');
        for (var i = 0; i < checkboxes.length; i++) {
            var columnKey = checkboxes[i].getAttribute('data-column');
            var column = window.etfSignalsManager.availableColumns.find(function(col) {
                return col.key === columnKey;
            });
            if (column) {
                column.visible = checkboxes[i].checked;
            }
        }
        
        window.etfSignalsManager.saveColumnSettings();
        window.etfSignalsManager.updateTableHeaders();
        window.etfSignalsManager.renderSignalsTable();
        
        // Close modal
        var modal = bootstrap.Modal.getInstance(document.getElementById('columnSettingsModal'));
        if (modal) modal.hide();
    }
};

    // Format date
    var entryDate = '';
    if (signal.date || signal.created_at) {
        try {
            var dateStr = signal.date || signal.created_at;
            var date = new Date(dateStr);
            entryDate = date.toLocaleDateString('en-GB');
        } catch (e) {
            entryDate = dateStr.toString();
        }
    }

    // Build row HTML
    row.innerHTML = 
        '<td><strong>' + symbol + '</strong></td>' +
        '<td>' + (signal.thirty || '-') + '</td>' +
        '<td>' + (signal.dh || '0') + '</td>' +
        '<td>' + entryDate + '</td>' +
        // '<td><span class="badge ' + (status === 'ACTIVE' ? 'bg-success' : 'bg-secondary') + '">' + positionType + '</span></td>' +
        '<td>' + quantity + '</td>' +
        '<td>₹' + entryPrice.toFixed(2) + '</td>' +
        '<td class="' + changeClass + '">₹' + currentPrice.toFixed(2) + '</td>' +
        '<td class="' + changeClass + '">' + changePct.toFixed(2) + '%</td>' +
        '<td>₹' + investment.toFixed(0) + '</td>' +
        '<td>₹' + targetPrice.toFixed(2) + '</td>' +
        '<td>₹' + (currentPrice * quantity).toFixed(0) + '</td>' +
        '<td class="profit">' + (targetPrice > entryPrice ? '+' + (((targetPrice - entryPrice) / entryPrice * 100)).toFixed(2) + '%' : '-') + '</td>' +
        '<td class="' + pnlClass + '">₹' + pnl.toFixed(0) + '</td>' +
        '<td>' + entryDate + '</td>' +
        '<td>' + (signal.exp || '-') + '</td>' +
        '<td>' + (signal.pr || '-') + '</td>' +
        '<td>' + (signal.pp || changePct.toFixed(1)) + '</td>' +
        '<td>' + (signal.iv || investment.toFixed(0)) + '</td>' +
        '<td class="' + changeClass + '">' + changePct.toFixed(2) + '%</td>' +
        '<td>' + (signal.nt || '-') + '</td>' +
        '<td>' + (signal.qt || '-') + '</td>' +
        '<td class="' + changeClass + '">' + (signal.seven || changePct.toFixed(2) + '%') + '</td>' +
        '<td class="' + changeClass + '">' + changePct.toFixed(2) + '%</td>' +
        '<td>' +
        '<button class="btn btn-sm btn-primary" onclick="addDeal(\'' + symbol + '\', ' + currentPrice + ')">Add Deal</button>' +
        '</td>';

    return row;
};

ETFSignalsManager.prototype.updatePortfolioSummary = function(portfolio) {
    if (!portfolio) return;

    var elements = {
        'totalPositions': portfolio.total_positions || 0,
        'activePositions': portfolio.active_positions || 0,
        'totalInvestment': '₹' + (portfolio.total_investment || 0).toLocaleString(),
        'currentValue': '₹' + (portfolio.current_value || 0).toLocaleString(),
        'totalPnl': '₹' + (portfolio.total_pnl || 0).toLocaleString(),
        'returnPercent': (portfolio.return_percent || 0).toFixed(2) + '%'
    };

    for (var id in elements) {
        var element = document.getElementById(id);
        if (element) element.textContent = elements[id];
    }
};

ETFSignalsManager.prototype.applyFilters = function() {
    var searchInput = document.getElementById('signalSearch');
    var searchTerm = searchInput ? searchInput.value.toLowerCase() : '';

    var self = this;
    this.filteredSignals = this.signals.filter(function(signal) {
        var symbol = signal.etf || signal.symbol || '';
        var status = signal.status || '';
        return symbol.toLowerCase().indexOf(searchTerm) !== -1 ||
               status.toLowerCase().indexOf(searchTerm) !== -1;
    });

    this.currentPage = 1;
    this.renderSignalsTable();
    this.updatePagination();
};

ETFSignalsManager.prototype.updatePagination = function() {
    var totalPages = Math.ceil(this.filteredSignals.length / this.itemsPerPage);

    // Update counts
    var showingCount = document.getElementById('showingCount');
    var totalCount = document.getElementById('totalCount');
    var visibleSignalsCount = document.getElementById('visibleSignalsCount');

    if (showingCount) {
        var startItem = (this.currentPage - 1) * this.itemsPerPage + 1;
        var endItem = Math.min(this.currentPage * this.itemsPerPage, this.filteredSignals.length);
        showingCount.textContent = this.filteredSignals.length > 0 ? startItem + '-' + endItem : '0';
    }

    if (totalCount) totalCount.textContent = this.signals.length;
    if (visibleSignalsCount) visibleSignalsCount.textContent = this.filteredSignals.length;

    // Update pagination buttons
    var prevBtn = document.getElementById('prevBtn');
    var nextBtn = document.getElementById('nextBtn');
    var currentPageSpan = document.getElementById('currentPage');
    var totalPagesSpan = document.getElementById('totalPages');

    if (prevBtn) prevBtn.disabled = this.currentPage <= 1;
    if (nextBtn) nextBtn.disabled = this.currentPage >= totalPages;
    if (currentPageSpan) currentPageSpan.textContent = this.currentPage;
    if (totalPagesSpan) totalPagesSpan.textContent = totalPages;
};

ETFSignalsManager.prototype.showLoadingState = function() {
    var tbody = document.getElementById('signalsTableBody');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="25" class="text-center">Loading ETF signals...</td></tr>';
    }
};

ETFSignalsManager.prototype.hideLoadingState = function() {
    // Loading state is cleared when table is rendered
};

ETFSignalsManager.prototype.showSuccessMessage = function(message) {
    console.log('Success:', message);
};

ETFSignalsManager.prototype.showErrorMessage = function(message) {
    console.error('Error:', message);
    var tbody = document.getElementById('signalsTableBody');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="25" class="text-center text-danger">' + message + '</td></tr>';
    }
};

ETFSignalsManager.prototype.startAutoRefresh = function() {
    var self = this;
    this.stopAutoRefresh();
    this.refreshInterval = setInterval(function() {
        self.loadSignals();
    }, 30000); // 30 seconds
};

ETFSignalsManager.prototype.stopAutoRefresh = function() {
    if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
        this.refreshInterval = null;
    }
};

// Global functions for HTML event handlers
function refreshSignals() {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.loadSignals();
    }
}

function setRefreshInterval(interval, text) {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.stopAutoRefresh();
        if (interval > 0) {
            window.etfSignalsManager.refreshInterval = setInterval(function() {
                window.etfSignalsManager.loadSignals();
            }, interval);
        }
        var currentIntervalSpan = document.getElementById('currentInterval');
        if (currentIntervalSpan) {
            currentIntervalSpan.textContent = text;
        }
        console.log('Refresh interval set to:', interval + 'ms (' + text + ')');
    }
}

function exportSignals() {
    if (window.etfSignalsManager) {
        var signals = window.etfSignalsManager.signals;
        if (!signals || signals.length === 0) {
            alert('No data to export');
            return;
        }

        var csvContent = "data:text/csv;charset=utf-8,";
        csvContent += "ETF,Entry Price,Current Price,Quantity,Investment,P&L,Change %\n";

        signals.forEach(function(signal) {
            var symbol = signal.etf || signal.symbol || '';
            var entryPrice = signal.ep || signal.entry_price || 0;
            var currentPrice = signal.cmp || signal.current_price || 0;
            var quantity = signal.qty || signal.quantity || 0;
            var investment = signal.inv || signal.investment_amount || 0;
            var pnl = signal.pl || signal.pnl || 0;
            var changePct = signal.change_pct || signal.pp || 0;

            var row = [symbol, entryPrice, currentPrice, quantity, investment, pnl, changePct].join(',');
            csvContent += row + "\n";
        });

        var encodedUri = encodeURI(csvContent);
        var link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", "etf_signals.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

function addDeal(symbol, price) {
    // Use SweetAlert2 for better confirmation dialog
    Swal.fire({
        title: 'Add Deal',
        html: `
            <div class="text-start">
                <p><strong>Symbol:</strong> ${symbol}</p>
                <p><strong>Entry Price:</strong> ₹${price.toFixed(2)}</p>
                <p><strong>Quantity:</strong> 1</p>
                <p><strong>Position:</strong> LONG</p>
                <p><strong>Investment:</strong> ₹${price.toFixed(2)}</p>
            </div>
        `,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#28a745',
        cancelButtonColor: '#dc3545',
        confirmButtonText: 'Yes, Add Deal!',
        cancelButtonText: 'Cancel'
    }).then((result) => {
        if (result.isConfirmed) {
            // Show loading
            Swal.fire({
                title: 'Creating Deal...',
                text: 'Please wait while we process your request',
                allowOutsideClick: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });

            var signalData = {
                symbol: symbol,
                pos: 1,
                qty: 1,
                cmp: price,
                ep: price,
                tp: price * 1.05,
                inv: price * 1,
                pl: 0,
                change_pct: 0
            };

            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/api/deals/create-from-signal', true);
            xhr.setRequestHeader('Content-Type', 'application/json');

            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        try {
                            var response = JSON.parse(xhr.responseText);
                            if (response.success) {
                                Swal.fire({
                                    title: 'Success!',
                                    text: 'Deal created successfully for ' + symbol,
                                    icon: 'success',
                                    confirmButtonColor: '#28a745'
                                }).then(() => {
                                    window.location.href = '/deals?symbol=' + encodeURIComponent(symbol) + '&price=' + price.toFixed(2);
                                });
                            } else {
                                Swal.fire({
                                    title: 'Failed!',
                                    text: response.message || 'Unknown error occurred',
                                    icon: 'error',
                                    confirmButtonColor: '#dc3545'
                                });
                            }
                        } catch (parseError) {
                            console.error('Failed to parse API response:', parseError);
                            Swal.fire({
                                title: 'Error!',
                                text: 'Invalid response from server',
                                icon: 'error',
                                confirmButtonColor: '#dc3545'
                            });
                        }
                    } else {
                        Swal.fire({
                            title: 'Server Error!',
                            text: 'Server returned status: ' + xhr.status + '. Please try again or contact support.',
                            icon: 'error',
                            confirmButtonColor: '#dc3545'
                        });
                    }
                }
            };

            xhr.send(JSON.stringify({signal_data: signalData}));
        }
    });
}

// Function to sort signals by any column
function sortSignalsByColumn(column) {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.sortDirection = window.etfSignalsManager.sortDirection === 'asc' ? 'desc' : 'asc';
        var direction = window.etfSignalsManager.sortDirection;
        
        window.etfSignalsManager.filteredSignals.sort(function(a, b) {
            var valueA, valueB;
            
            switch(column) {
                case 'symbol':
                    valueA = (a.etf || a.symbol || '').toLowerCase();
                    valueB = (b.etf || b.symbol || '').toLowerCase();
                    break;
                case 'ep':
                    valueA = parseFloat(a.ep || a.entry_price || 0);
                    valueB = parseFloat(b.ep || b.entry_price || 0);
                    break;
                case 'cmp':
                    valueA = parseFloat(a.cmp || a.current_price || 0);
                    valueB = parseFloat(b.cmp || b.current_price || 0);
                    break;
                case 'qty':
                    valueA = parseInt(a.qty || a.quantity || 0);
                    valueB = parseInt(b.qty || b.quantity || 0);
                    break;
                case 'changePct':
                    valueA = parseFloat(a.change_pct || a.pp || 0);
                    valueB = parseFloat(b.change_pct || b.pp || 0);
                    break;
                case 'inv':
                    valueA = parseFloat(a.inv || a.investment_amount || 0);
                    valueB = parseFloat(b.inv || b.investment_amount || 0);
                    break;
                case 'tp':
                    valueA = parseFloat(a.tp || a.target_price || 0);
                    valueB = parseFloat(b.tp || b.target_price || 0);
                    break;
                case 'pl':
                    valueA = parseFloat(a.pl || a.pnl || 0);
                    valueB = parseFloat(b.pl || b.pnl || 0);
                    break;
                case 'date':
                    valueA = a.date || a.created_at || '';
                    valueB = b.date || b.created_at || '';
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
        
        window.etfSignalsManager.renderSignalsTable();
        window.etfSignalsManager.updatePagination();
    }
}

// Initialize the ETF Signals Manager
window.etfSignalsManager = new ETFSignalsManager();


// Expose global functions for HTML event handlers


// Function to update the CMP value in the table
    function updateCMPValue(symbol, cmp) {
        // Find the cell with the matching symbol
        const cmpCells = document.querySelectorAll(`.cmp-value[data-symbol="${symbol}"]`);
        cmpCells.forEach(cell => {
            cell.textContent = `₹${cmp.toFixed(2)}`;  // Update the CMP value
        });
    }

    // Example usage (assuming you have a way to get live CMP data)
    // setInterval(() => {
    //     // Replace with your logic to fetch live CMP data
    //     const liveCMPData = {
    //         "RELIANCE": 2500.50,
    //         "TCS": 3500.75,
    //         "HDFC": 1500.20
    //     };

    //     // Update CMP values in the table
    //     for (const symbol in liveCMPData) {
    //         if (liveCMPData.hasOwnProperty(symbol)) {
    //             updateCMPValue(symbol, liveCMPData[symbol]);
    //         }
    //     }
    // }, 5000); // Update every 5 seconds (adjust as needed)

document.addEventListener('DOMContentLoaded', function () {
    // Initial column settings (you can customize these)
    let visibleColumns = {
        'ETF': true,
        '30': true,
        'DH': true,
        'Date': true,
        // 'Pos': true,
        'Qty': true,
        'EP': true,
        'CMP': true,
        '%Chan': true,
        'Inv.': true,
        'TP': true,
        'TVA': true,
        'TPR': true,
        'PL': true,
        'ED': true,
        'EXP': true,
        'PR': true,
        'PP': true,
        'IV': true,
        'IP': true,
        'NT': true,
        'Qt': true,
        '7': true,
        '%Ch': true,
        'Actions': true // Keep the Actions column
    };

    let signalsData = [];
    let filteredSignals = [];
    let currentPage = 1;
    const signalsPerPage = 10;

    // Function to initialize column settings modal
    function initializeColumnSettings() {
        const columnCheckboxesDiv = document.getElementById('columnCheckboxes');
        columnCheckboxesDiv.innerHTML = ''; // Clear existing checkboxes

        for (const column in visibleColumns) {
            if (visibleColumns.hasOwnProperty(column)) {
                const div = document.createElement('div');
                div.classList.add('col-md-3', 'mb-2');

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.id = `checkbox-${column}`;
                checkbox.classList.add('form-check-input');
                checkbox.checked = visibleColumns[column];

                checkbox.addEventListener('change', function () {
                    visibleColumns[column] = this.checked;
                    applyColumnSettings(); // Re-render the table when a checkbox is changed
                });

                const label = document.createElement('label');
                label.htmlFor = `checkbox-${column}`;
                label.classList.add('form-check-label', 'text-light');
                label.textContent = column;

                div.appendChild(checkbox);
                div.appendChild(label);
                columnCheckboxesDiv.appendChild(div);
            }
        }
    }

    // Function to select all columns
    window.selectAllColumns = function () {
        for (const column in visibleColumns) {
            if (visibleColumns.hasOwnProperty(column)) {
                visibleColumns[column] = true;
            }
        }
        initializeColumnSettings(); // Re-render the modal
        applyColumnSettings(); // Re-render the table
    };

    // Function to reset to default columns
    window.resetDefaultColumns = function () {
        visibleColumns = {
            'ETF': true,
            '30': true,
            'DH': true,
            'Date': true,
            // 'Pos': true,
            'Qty': true,
            'EP': true,
            'CMP': true,
            '%Chan': true,
            'Inv.': true,
            'TP': true,
            'TVA': true,
            'TPR': true,
            'PL': true,
            'ED': true,
            'EXP': true,
            'PR': true,
            'PP': true,
            'IV': true,
            'IP': true,
            'NT': true,
            'Qt': true,
            '7': true,
            '%Ch': true,
            'Actions': true // Keep the Actions column
        };
        initializeColumnSettings(); // Re-render the modal
        applyColumnSettings(); // Re-render the table
    };

    // Function to apply column settings
    window.applyColumnSettings = function () {
        console.log('Applying column settings...');
        // Don't modify the existing table headers since ETF signals manager handles this
        // Just trigger a refresh of the data
        if (window.etfSignalsManager) {
            window.etfSignalsManager.loadPositions();
        }
    };

    // Function to fetch signals data - delegated to ETF Signals Manager
    function fetchSignals() {
        if (window.etfSignalsManager) {
            window.etfSignalsManager.loadPositions();
        }
    }

    // Table rendering is handled by ETF Signals Manager
    function renderTable(signals) {
        // Delegated to ETF Signals Manager
        console.log('Render table called with', signals ? signals.length : 0, 'signals');
    }

    // Function to update pagination buttons
    function updatePaginationButtons() {
        const totalPages = Math.ceil(filteredSignals.length / signalsPerPage);
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const currentPageSpan = document.getElementById('currentPage');
        const totalPagesSpan = document.getElementById('totalPages');

        currentPageSpan.textContent = currentPage;
        totalPagesSpan.textContent = totalPages;

        prevBtn.disabled = currentPage <= 1;
        nextBtn.disabled = currentPage >= totalPages;
    }

    // Function to go to the previous page
    window.previousPage = function () {
        if (currentPage > 1) {
            currentPage--;
            renderTable(filteredSignals);
            updatePaginationButtons();
        }
    };

    // Function to go to the next page
    window.nextPage = function () {
        const totalPages = Math.ceil(filteredSignals.length / signalsPerPage);
        if (currentPage < totalPages) {
            currentPage++;
            renderTable(filteredSignals);
            updatePaginationButtons();
        }
    };

    // Function to update counts
    function updateCounts() {
        const showingCount = document.getElementById('showingCount');
        const totalCount = document.getElementById('totalCount');
        const visibleSignalsCount = document.getElementById('visibleSignalsCount');

        showingCount.textContent = filteredSignals.length > 0 ? ((currentPage - 1) * signalsPerPage) + 1 : 0;
        totalCount.textContent = signalsData.length;
        visibleSignalsCount.textContent = filteredSignals.length;

        if (filteredSignals.length > 0) {
            showingCount.textContent = Math.min(filteredSignals.length, ((currentPage - 1) * signalsPerPage) + signalsPerPage);
        } else {
            showingCount.textContent = '0';
        }
    }

    // Function to apply filters
    window.applyFilters = function () {
        const orderTypeFilter = document.getElementById('orderTypeFilter').value;
        const statusFilter = document.getElementById('statusFilter').value;
        const symbolFilter = document.getElementById('symbolFilter').value.toUpperCase();
        const minPnlFilter = parseFloat(document.getElementById('minPnlFilter').value) || -Infinity;
        const maxPnlFilter = parseFloat(document.getElementById('maxPnlFilter').value) || Infinity;

        filteredSignals = signalsData.filter(data => {
            if (orderTypeFilter && data.order_type !== orderTypeFilter) return false;
            if (statusFilter && data.status !== statusFilter) return false;
            if (symbolFilter && !data.symbol.toUpperCase().includes(symbolFilter)) return false;
            if (data.profit_loss < minPnlFilter || data.profit_loss > maxPnlFilter) return false;
            return true;
        });

        currentPage = 1; // Reset to first page after filtering
        updateCounts();
        renderTable(filteredSignals);
        updatePaginationButtons();
    };

    // Function to clear filters
    window.clearFilters = function () {
        document.getElementById('orderTypeFilter').value = '';
        document.getElementById('statusFilter').value = '';
        document.getElementById('symbolFilter').value = '';
        document.getElementById('minPnlFilter').value = '';
        document.getElementById('maxPnlFilter').value = '';
        applyFilters();
    };

    // Function to refresh signals
    window.refreshSignals = function () {
        fetchSignals();
    };

    // Function to export signals
    window.exportSignals = function () {
        const csvContent = "data:text/csv;charset=utf-8," +
            Object.keys(signalsData[0]).join(",") + "\n" +
            signalsData.map(row => Object.values(row).join(",")).join("\n");

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", "etf_signals.csv");
        document.body.appendChild(link); // Required for FF

        link.click();
        document.body.removeChild(link);
    };

    // Auto-refresh functionality
    let autoRefreshInterval;

    function setAutoRefresh(enabled) {
        if (enabled) {
            const refreshIntervalDropdown = document.getElementById('refreshIntervalDropdown');
            let currentInterval = refreshIntervalDropdown.textContent.trim();
            let intervalMs = 30000;

            if (currentInterval === '5s') intervalMs = 5000;
            else if (currentInterval === '10s') intervalMs = 10000;
            else if (currentInterval === '1m') intervalMs = 60000;
            else if (currentInterval === '5m') intervalMs = 300000;
            else if (currentInterval === '10m') intervalMs = 600000;

            autoRefreshInterval = setInterval(fetchSignals, intervalMs);
        } else {
            clearInterval(autoRefreshInterval);
        }
    }

    const autoRefreshToggle = document.getElementById('autoRefreshToggle');
    autoRefreshToggle.addEventListener('change', function () {
        setAutoRefresh(this.checked);
    });

    // Set refresh interval
    window.setRefreshInterval = function (interval, text) {
        const currentIntervalSpan = document.getElementById('currentInterval');
        currentIntervalSpan.textContent = text;
        clearInterval(autoRefreshInterval);
        if (autoRefreshToggle.checked) {
            autoRefreshInterval = setInterval(fetchSignals, interval);
        }
    };

    // Initialize the page
    initializeColumnSettings();
    fetchSignals();
    setAutoRefresh(autoRefreshToggle.checked);
});