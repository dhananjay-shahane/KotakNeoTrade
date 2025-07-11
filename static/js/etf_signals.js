/**
 * ETF Signals Manager - ES5 Compatible
 * Manages real-time ETF trading signals display and updates
 * Fetches authentic market data from external trading database
 */
function ETFSignalsManager() {
    var self = this;

    // Core data management
    this.signals = [];                  // All ETF signals from database
    this.filteredSignals = [];          // Filtered signals based on search/sort
    this.currentPage = 1;               // Current page in pagination
    this.itemsPerPage = 25;             // Number of signals per page
    this.isLoading = false;             // Loading state flag
    this.refreshInterval = null;        // Auto-refresh timer

    // Table sorting configuration
    this.sortField = 'id';              // Current sort field
    this.sortDirection = 'asc';         // Sort direction (asc/desc)

    // Column visibility settings
    this.availableColumns = [
        { key: 'trade_signal_id', label: 'ID', visible: true },
        { key: 'etf', label: 'ETF', visible: true },
        { key: 'thirty', label: '30D', visible: true },
        { key: 'dh', label: '30D%', visible: true },
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
        { key: 'seven', label: '7D', visible: true },
        { key: 'ch', label: '7D%', visible: true },
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
    this.updateTableHeaders(); // Update headers based on column settings
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

                    if (data.data && Array.isArray(data.data)) {
                        self.signals = data.data || [];
                        self.filteredSignals = self.signals.slice();
                        self.renderSignalsTable();
                        self.updatePagination();
                        self.showSuccessMessage('Loaded ' + self.signals.length + ' signals');
                        console.log('Successfully loaded', self.signals.length, 'signals');
                    } else if (data.error) {
                        throw new Error(data.error);
                    } else {
                        throw new Error('Invalid response format');
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

    // Count visible columns for colspan
    var visibleColumnCount = 0;
    for (var i = 0; i < this.availableColumns.length; i++) {
        if (this.availableColumns[i].visible) visibleColumnCount++;
    }

    if (pageSignals.length === 0) {
        tbody.innerHTML = '<tr><td colspan="' + visibleColumnCount + '" class="text-center text-muted">No ETF signals found</td></tr>';
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
            case 'trade_signal_id':
                var tradeId = signal.trade_signal_id || signal.id || 'N/A';
                cellValue = '<span class="badge bg-secondary">' + tradeId + '</span>';
                break;
            case 'etf':
                cellValue = '<span class="fw-bold text-primary">' + symbol + '</span>';
                break;
            case 'thirty':
                var thirtyValue = signal.thirty || signal.d30 || 0;
                if (typeof thirtyValue === 'string') {
                    thirtyValue = parseFloat(thirtyValue) || 0;
                }
                cellValue = thirtyValue > 0 ? '₹' + thirtyValue.toFixed(2) : '₹0.00';
                break;
            case 'dh':
                var dhValue = signal.dh || signal.ch30 || '0.00%';
                if (typeof dhValue === 'number') {
                    dhValue = dhValue.toFixed(2) + '%';
                }
                if (typeof dhValue === 'string' && !dhValue.includes('%')) {
                    dhValue = parseFloat(dhValue).toFixed(2) + '%';
                }
                var percentage = parseFloat(dhValue.replace('%', ''));
                var colorClass = percentage >= 0 ? 'text-success' : 'text-danger';
                var bgColor = this.getGradientBackgroundColor(percentage);
                cellStyle = bgColor;
                cellValue = '<span class="fw-bold ' + colorClass + '">' + dhValue + '</span>';
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
                var bgColor = this.getGradientBackgroundColor(changePct);
                cellStyle = bgColor;
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
            // case 'qt':
            //     cellValue = signal.qt || quantity;
            //     break;
            case 'seven':
                var sevenValue = signal.seven || signal.d7 || 0;
                if (typeof sevenValue === 'string') {
                    sevenValue = parseFloat(sevenValue) || 0;
                }
                cellValue = sevenValue > 0 ? '₹' + sevenValue.toFixed(2) : '₹0.00';
                break;
            case 'ch':
                var chValue = signal.ch || signal.ch7 || '0.00%';
                if (typeof chValue === 'number') {
                    chValue = chValue.toFixed(2) + '%';
                }
                if (typeof chValue === 'string' && !chValue.includes('%')) {
                    chValue = parseFloat(chValue).toFixed(2) + '%';
                }
                var percentage = parseFloat(chValue.replace('%', ''));
                var colorClass = percentage >= 0 ? 'text-success' : 'text-danger';
                var bgColor = this.getGradientBackgroundColor(percentage);
                cellStyle = bgColor;
                cellValue = '<span class="fw-bold ' + colorClass + '">' + chValue + '</span>';
                break;
            case 'actions':
                var signalId = signal.trade_signal_id || signal.id || index;
                cellValue = '<button class="btn btn-sm btn-success" onclick="addDeal(' + signalId + ')"><i class="fas fa-plus me-1"></i>Add Deal</button>';
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
            return 'background-color: rgba(0, 128, 0, ' + alpha + '); color: #fff;'; // Green
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

// Enhanced sorting functionality for ETF signals table
var sortState = {
    column: null,
    direction: 'asc'
};

function sortTable(column) {
    var tbody = document.getElementById('etfSignalsTableBody');
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
            case 'etf':
                aValue = (a.dataset.symbol || a.dataset.etf || '').toLowerCase();
                bValue = (b.dataset.symbol || b.dataset.etf || '').toLowerCase();
                break;
            case 'quantity':
            case 'qty':
                aValue = parseFloat(a.dataset.quantity || a.dataset.qty) || 0;
                bValue = parseFloat(b.dataset.quantity || b.dataset.qty) || 0;
                break;
            case 'entryPrice':
            case 'ep':
                aValue = parseFloat(a.dataset.entryPrice || a.dataset.ep) || 0;
                bValue = parseFloat(b.dataset.entryPrice || b.dataset.ep) || 0;
                break;
            case 'currentPrice':
            case 'cmp':
                aValue = parseFloat(a.dataset.currentPrice || a.dataset.cmp) || 0;
                bValue = parseFloat(b.dataset.currentPrice || b.dataset.cmp) || 0;
                break;
            case 'pnl':
            case 'pl':
                aValue = parseFloat(a.dataset.pnl || a.dataset.pl) || 0;
                bValue = parseFloat(b.dataset.pnl || b.dataset.pl) || 0;
                break;
            case 'investment':
            case 'inv':
                aValue = parseFloat(a.dataset.investment || a.dataset.inv) || 0;
                bValue = parseFloat(b.dataset.investment || b.dataset.inv) || 0;
                break;
            case 'currentValue':
            case 'tva':
                aValue = parseFloat(a.dataset.currentValue || a.dataset.tva) || 0;
                bValue = parseFloat(b.dataset.currentValue || b.dataset.tva) || 0;
                break;
            case 'chanPercent':
            case 'ch':
                aValue = parseFloat(a.dataset.chanPercent || a.dataset.ch) || 0;
                bValue = parseFloat(b.dataset.chanPercent || b.dataset.ch) || 0;
                break;
            case 'targetPrice':
            case 'tp':
                aValue = parseFloat(a.dataset.targetPrice || a.dataset.tp) || 0;
                bValue = parseFloat(b.dataset.targetPrice || b.dataset.tp) || 0;
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

// Legacy function for compatibility with existing onclick handlers
function sortSignalsByColumn(column) {
    sortTable(column);
}

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
        // Update all columns to visible
        for (var i = 0; i < window.etfSignalsManager.availableColumns.length; i++) {
            window.etfSignalsManager.availableColumns[i].visible = true;
        }

        // Update all checkboxes to checked
        var checkboxes = document.querySelectorAll('#columnCheckboxes input[type="checkbox"]');
        for (var i = 0; i < checkboxes.length; i++) {
            checkboxes[i].checked = true;
        }

        console.log('All columns selected');
    }
}

function resetDefaultColumns() {
    if (window.etfSignalsManager) {
        var defaultVisible = ['trade_signal_id', 'etf', 'thirty', 'dh', 'date', 'qty', 'ep', 'cmp', 'chan', 'inv', 'pl', 'ch', 'actions'];

        // Update column visibility
        for (var i = 0; i < window.etfSignalsManager.availableColumns.length; i++) {
            var column = window.etfSignalsManager.availableColumns[i];
            column.visible = defaultVisible.indexOf(column.key) !== -1;
        }

        // Update checkboxes to match default settings
        var checkboxes = document.querySelectorAll('#columnCheckboxes input[type="checkbox"]');
        for (var i = 0; i < checkboxes.length; i++) {
            var columnKey = checkboxes[i].getAttribute('data-column');
            checkboxes[i].checked = defaultVisible.indexOf(columnKey) !== -1;
        }

        console.log('Reset to default columns');
    }
}

function applyColumnSettings() {
    console.log('Applying column settings...');
    if (window.etfSignalsManager) {
        var checkboxes = document.querySelectorAll('#columnCheckboxes input[type="checkbox"]');
        console.log('Found checkboxes:', checkboxes.length);

        // Update column visibility based on checkbox states
        for (var i = 0; i < checkboxes.length; i++) {
            var columnKey = checkboxes[i].getAttribute('data-column');
            var isChecked = checkboxes[i].checked;

            // Find and update the column in availableColumns array
            for (var j = 0; j < window.etfSignalsManager.availableColumns.length; j++) {
                if (window.etfSignalsManager.availableColumns[j].key === columnKey) {
                    window.etfSignalsManager.availableColumns[j].visible = isChecked;
                    console.log('Updated column', columnKey, 'visible:', isChecked);
                    break;
                }
            }
        }

        // Save settings and update display
        window.etfSignalsManager.saveColumnSettings();
        window.etfSignalsManager.updateTableHeaders();
        window.etfSignalsManager.renderSignalsTable();
        window.etfSignalsManager.updatePagination();

        // Close modal
        var modalElement = document.getElementById('columnSettingsModal');
        if (modalElement && window.bootstrap) {
            var modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) {
                modal.hide();
            } else {
                var newModal = new bootstrap.Modal(modalElement);
                newModal.hide();
            }
        }
        console.log('Column settings applied successfully');
    } else {
        console.error('ETF Signals Manager not found');
    }
}

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
        tbody.innerHTML = '<tr><td colspan="25" class="text-center py-5">' +
                         '<div class="d-flex flex-column justify-content-center align-items-center">' +
                         '<div class="spinner-border text-primary mb-3" role="status" style="width: 2.5rem; height: 2.5rem;">' +
                         '<span class="visually-hidden">Loading...</span></div>' +
                         '<h6 class="text-light mb-2">Loading ETF Signals</h6>' +
                         '<small class="text-muted">Fetching data from database...</small>' +
                         '</div></td></tr>';
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
        // Update CMP values with selected data source every refresh
        var dataSource = localStorage.getItem('data-source') || 'google';
        updateCMPDirectlyFromSource(dataSource);
    }, 300000); // 5 minutes
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
    // Only allow 5 minute intervals
    if (interval !== 300000) {
        interval = 300000;
        text = '5 Min';
    }

    if (window.etfSignalsManager) {
        window.etfSignalsManager.stopAutoRefresh();
        if (interval > 0) {
            window.etfSignalsManager.refreshInterval = setInterval(function() {
                window.etfSignalsManager.loadSignals();
                // Update CMP using selected data source
                var dataSource = localStorage.getItem('data-source') || 'google';
                updateCMPDirectlyFromSource(dataSource);
            }, interval);
        }
        var currentIntervalSpan = document.getElementById('currentInterval');
        var refreshIntervalDropdown = document.getElementById('refreshIntervalDropdown');
        if (currentIntervalSpan) {
            currentIntervalSpan.textContent = text;
        }
        if (refreshIntervalDropdown) {
            refreshIntervalDropdown.textContent = text;
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
            var quantity = signal.qty || signal|| signal.quantity || 0;
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

function addDeal(signalId) {
    // Find the complete signal data from the current signals array
    var signal = null;
    if (window.etfSignalsManager && window.etfSignalsManager.signals) {
        signal = window.etfSignalsManager.signals.find(function(s) {
            return s.id == signalId || s.trade_signal_id == signalId;
        });
    }

    if (!signal) {
        alert('Signal data not found. Please refresh the page and try again.');
        return;
    }

    var symbol = signal.etf || signal.symbol || 'UNKNOWN';
    var price = signal.cmp || signal.ep || 0;
    var quantity = signal.qty || 1;
    var investment = signal.inv || (price * quantity);

    // First, check if this deal already exists
    checkExistingDeal(symbol, price, function(exists) {
        if (exists) {
            // Show duplicate confirmation dialog
            Swal.fire({
                title: 'Trade Already Added!',
                html: '<div class="text-start">' +
                    '<p class="text-warning"><i class="fas fa-exclamation-triangle"></i> This trade is already added to your deals page.</p>' +
                    '<hr>' +
                    '<p><strong>Symbol:</strong> ' + symbol + '</p>' +
                    '<p><strong>Entry Price:</strong> ₹' + parseFloat(price).toFixed(2) + '</p>' +
                    '<p><strong>Quantity:</strong> ' + quantity + '</p>' +
                    '<p><strong>Investment:</strong> ₹' + parseFloat(investment).toFixed(2) + '</p>' +
                    '<hr>' +
                    '<p class="text-info">Do you want to add this trade again?</p>' +
                    '</div>',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#28a745',
                cancelButtonColor: '#6c757d',
                confirmButtonText: '<i class="fas fa-plus"></i> Yes, Add Again',
                cancelButtonText: '<i class="fas fa-times"></i> Cancel'
            }).then(function(result) {
                if (result.isConfirmed) {
                    // User confirmed to add duplicate
                    proceedWithAddingDeal(signal, symbol, price, quantity, investment);
                }
                // If cancelled, do nothing
            });
        } else {
            // No duplicate, show regular confirmation dialog
            Swal.fire({
                title: 'Add Deal',
                html: '<div class="text-start">' +
                    '<p><strong>Symbol:</strong> ' + symbol + '</p>' +
                    '<p><strong>Entry Price:</strong> ₹' + parseFloat(price).toFixed(2) + '</p>' +
                    '<p><strong>Quantity:</strong> ' + quantity + '</p>' +
                    '<p><strong>Position:</strong> ' + (signal.pos == 1 ? 'LONG' : 'SHORT') + '</p>' +
                    '<p><strong>Investment:</strong> ₹' + parseFloat(investment).toFixed(2) + '</p>' +
                    '<p><strong>Target Price:</strong> ₹' + parseFloat(signal.tp || price * 1.05).toFixed(2) + '</p>' +
                    '</div>',
                icon: 'question',
                showCancelButton: true,
                confirmButtonColor: '#28a745',
                cancelButtonColor: '#dc3545',
                confirmButtonText: 'Yes, Add Deal!',
                cancelButtonText: 'Cancel'
            }).then(function(result) {
                if (result.isConfirmed) {
                    proceedWithAddingDeal(signal, symbol, price, quantity, investment);
                }
            });
        }
    });
}

function checkExistingDeal(symbol, price, callback) {
    // Check for existing deals via API
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/api/deals/user?symbol=' + encodeURIComponent(symbol), true);
    xhr.withCredentials = true; // Include cookies for authentication

    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                try {
                    var response = JSON.parse(xhr.responseText);
                    var deals = response.deals || [];

                    console.log('Duplicate check - Symbol:', symbol, 'Found deals:', deals.length);

                    // Simply check if any deal has the same symbol
                    var duplicate = deals.length > 0 && deals.some(function(deal) {
                        var dealSymbol = deal.symbol || deal.etf || '';
                        return dealSymbol.toUpperCase() === symbol.toUpperCase();
                    });

                    console.log('Duplicate detected:', duplicate);
                    callback(duplicate);
                } catch (parseError) {
                    console.error('Failed to parse deals response:', parseError);
                    callback(false);
                }
            } else {
                console.error('Failed to check existing deals - Status:', xhr.status);
                // For authentication issues, assume no duplicate to avoid blocking
                callback(false);
            }
        }
    };

    xhr.send();
}

function proceedWithAddingDeal(signal, symbol, price, quantity, investment) {
    // Show loading
    Swal.fire({
        title: 'Creating Deal...',
        text: 'Please wait while we process your request',
        allowOutsideClick: false,
        didOpen: function() {
            Swal.showLoading();
        }
    });

    // Prepare complete signal data for the API
    var signalData = {
        etf: signal.etf || signal.symbol,
        symbol: signal.etf || signal.symbol,
        trade_signal_id: signal.trade_signal_id || signal.id,
        pos: signal.pos || 1,
        qty: signal.qty || 1,
        ep: signal.ep || price,
        cmp: signal.cmp || price,
        tp: signal.tp || (price * 1.05),
        inv: signal.inv || investment,
        pl: signal.pl || 0,
        change_pct: signal.chan || signal.change_pct || 0,
        thirty: signal.thirty || 0,
        dh: signal.dh || 0,
        date: signal.date || new Date().toISOString().split('T')[0],
        ed: signal.ed || signal.date,
        exp: signal.exp || '',
        pr: signal.pr || '',
        pp: signal.pp || '',
        iv: signal.iv || '',
        ip: signal.ip || '',
        nt: signal.nt || 'Added from ETF signals',
        qt: signal.qt || new Date().toLocaleTimeString(),
        seven: signal.seven || 0,
        ch: signal.ch || signal.change_pct || 0,
        tva: signal.tva || (signal.tp || price * 1.05) * quantity,
        tpr: signal.tpr || ((signal.tp || price * 1.05) - price) * quantity
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
                            confirmButtonColor: '#28a745',
                            timer: 2000,
                            timerProgressBar: true
                        }).then(function() {
                            window.location.href = '/deals?symbol=' + encodeURIComponent(symbol) + '&price=' + parseFloat(price).toFixed(2);
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

// Function to sort signals by any column
function sortSignalsByColumn(column) {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.sortDirection = window.etfSignalsManager.sortDirection === 'asc' ? 'desc' : 'asc';
        var direction = window.etfSignalsManager.sortDirection;

        window.etfSignalsManager.filteredSignals.sort(function(a, b) {
            var valueA, valueB;

            switch(column) {
                case 'trade_signal_id':
                    valueA = parseInt(a.trade_signal_id || a.id || 0);
                    valueB = parseInt(b.trade_signal_id || b.id || 0);
                    break;
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
    if (typeof showToaster === 'function') {
        showToaster('Data Source Changed', 'Switched to ' + sourceName + ' - Updating CMP...', 'info');
    }

    // Immediately update CMP when source changes
    if (newSource !== oldSource) {
        updateCMPDirectlyFromSource(newSource);
    }
}

function updateCMPDirectlyFromSource(source) {
    // Show update status icon
    var statusIcon = document.getElementById('updateStatusIcon');
    if (statusIcon) {
        statusIcon.style.display = 'inline';
    }

    // Show enhanced loading indicator in table with better styling
    var loadingHtml = '<tr><td colspan="25" class="text-center py-5">' +
                     '<div class="d-flex flex-column justify-content-center align-items-center">' +
                     '<div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;">' +
                     '<span class="visually-hidden">Loading...</span></div>' +
                     '<h5 class="text-light mb-2">Updating CMP</h5>' +
                     '<p class="text-muted">Fetching live prices from ' + 
                     (source === 'google' ? 'Google Finance' : 'Yahoo Finance') + '...</p>' +
                     '<small class="text-warning">Please wait, this may take a few moments</small>' +
                     '</div></td></tr>';

    var tableBody = document.getElementById('signalsTableBody');
    if (tableBody) {
        tableBody.innerHTML = loadingHtml;
    }

    // Use the appropriate API endpoint based on source
    var apiEndpoint = source === 'google' ? '/api/google-finance/update-etf-cmp' : '/api/yahoo/update-prices';

    // Create AbortController for timeout handling
    var controller = new AbortController();
    var timeoutId = setTimeout(function() {
        controller.abort();
    }, 35000); // 35 second timeout

    fetch(apiEndpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            direct_update: true,
            source: source
        }),
        signal: controller.signal
    })
    .then(function(response) {
        clearTimeout(timeoutId); // Clear the timeout since request completed
        return response.json();
    })
    .then(function(data) {
        // Hide update status icon
        var statusIcon = document.getElementById('updateStatusIcon');
        if (statusIcon) {
            statusIcon.style.display = 'none';
        }

        if (data.success) {
            // Show success notification with detailed info
            var updatedCount = data.updated_count || data.successful_updates || 0;
            var sourceName = source === 'google' ? 'Google Finance' : 'Yahoo Finance';

            if (typeof showToaster === 'function') {
                showToaster(
                    'CMP Updated Successfully', 
                    'Updated ' + updatedCount + ' records directly from ' + sourceName + ' in ' + (data.duration || 0).toFixed(1) + 's',
                    'success'
                );
            }
        }

        // Show error notification
        if (typeof showToaster === 'function') {
            showToaster(
                'Network Error', 
                'Failed to update CMP from selected source',
                'error'
            );
        }

        // Still try to refresh the table
        if (window.etfSignalsManager) {
            window.etfSignalsManager.loadSignals();
        }
    })
    .catch(function(error) {
        // Hide update status icon
        var statusIcon = document.getElementById('updateStatusIcon');
        if (statusIcon) {
            statusIcon.style.display = 'none';
        }

        var errorMessage = 'Network error occurred';
        if (error.name === 'AbortError') {
            errorMessage = 'Update request timed out after 35 seconds';
        } else if (error.message) {
            errorMessage = error.message;
        }

        // Show error notification
        if (typeof showToaster === 'function') {
            showToaster(
                'Network Error', 
                errorMessage,
                'error'
            );
        }

        // Still try to refresh the table
        if (window.etfSignalsManager) {
            window.etfSignalsManager.loadSignals();
        }
    });
}

// Function to update CMP from Google Finance
function updateCMPFromGoogleFinance() {
    console.log('🔄 Updating CMP from Google Finance...');

    var updateBtn = document.querySelector('[onclick*="updateCMPDirectlyFromSource"]');
    if (updateBtn) {
        updateBtn.innerHTML = '<i class="fas fa-sync-alt fa-spin me-2"></i>Updating...';
        updateBtn.disabled = true;
    }

    fetch('/api/google-finance/update-etf-cmp', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        if (data.success) {
            console.log('✅ CMP updated successfully:', data.updated_count, 'records');
            // Refresh the signals table after update
            if (window.etfSignalsManager) {
                window.etfSignalsManager.loadSignals();
            }
        } else {
            console.error('❌ CMP update failed:', data.error);
        }
    })
    .catch(function(error) {
        console.error('❌ Error updating CMP:', error);
    })
    .finally(function() {
        if (updateBtn) {
            updateBtn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Force Update CMP';
            updateBtn.disabled = false;
        }
    });
}

// Function to force update a specific symbol
function forceUpdateSymbol(symbol) {
    console.log('🔄 Force updating ' + symbol + '...');

    fetch('/api/google-finance/force-update-symbol/' + symbol, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        if (data.success) {
            console.log('✅ ' + symbol + ' updated successfully to ₹' + data.price);
            // Show success message
            if (window.showToaster) {
                window.showToaster('Symbol Updated', symbol + ' CMP updated to ₹' + data.price, 'success');
            }
            // Refresh the signals table
            if (window.etfSignalsManager) {
                window.etfSignalsManager.loadSignals();
            }
        } else {
            console.error('❌ Failed to update ' + symbol + ':', data.error);
            if (window.showToaster) {
                window.showToaster('Update Failed', 'Failed to update ' + symbol + ': ' + data.error, 'error');
            }
        }
    })
    .catch(function(error) {
        console.error('❌ Error updating ' + symbol + ':', error);
        if (window.showToaster) {
            window.showToaster('Update Error', 'Error updating ' + symbol, 'error');
        }
    });
}

// Function to stop automatic CMP updates
function stopAutoCMPUpdates() {
    if (typeof cmpUpdateInterval !== 'undefined' && cmpUpdateInterval) {
        clearInterval(cmpUpdateInterval);
        cmpUpdateInterval = null;
        console.log('⏹️ Auto CMP updates stopped');
    }
}

// Initialize the ETF Signals Manager
window.etfSignalsManager = new ETFSignalsManager();

// Update data source indicator when page loads
document.addEventListener('DOMContentLoaded', function() {
    updateCurrentDataSourceIndicator();

    // Set default refresh interval to 5 minutes
    var currentIntervalSpan = document.getElementById('currentInterval');
    var refreshIntervalDropdown = document.getElementById('refreshIntervalDropdown');
    if (currentIntervalSpan) {
        currentIntervalSpan.textContent = '5 Min';
    }
    if (refreshIntervalDropdown) {
        refreshIntervalDropdown.textContent = '5 Min';
    }

    // Set default data source to Google Finance if not already set
    if (!localStorage.getItem('data-source')) {
        localStorage.setItem('data-source', 'google');
    }

    // Ensure Google Finance is selected by default
    switchDataSource('google');

    // Start automatic CMP updates
    startAutoCMPUpdates();

    // Update CMP immediately on page load
    setTimeout(() => {
        console.log('🚀 Initial CMP update on page load');
        updateCMPFromGoogleFinance();
    }, 2000); // Wait 2 seconds for page to fully load
});

// Clean up interval when page unloads
window.addEventListener('beforeunload', function() {
    stopAutoCMPUpdates();
});


// Expose global functions for HTML event handlers


// Function to update the CMP value in the table
function updateCMPValue(symbol, cmp) {
    // Find the cell with the matching symbol
    const cmpCells = document.querySelectorAll(`.cmp-value[data-symbol="${symbol}"]`);
    cmpCells.forEach(cell => {
        const oldPrice = parseFloat(cell.textContent.replace('₹', '').replace(',', ''));
        cell.textContent = `₹${cmp.toFixed(2)}`;

        // Add visual feedback for price changes
        if (oldPrice && oldPrice !== cmp) {
            cell.classList.add(cmp > oldPrice ? 'price-up' : 'price-down');
            setTimeout(() => {
                cell.classList.remove('price-up', 'price-down');
            }, 2000);
        }
    });
}

// Function to update all CMP values using selected data source
function updateAllCMPValues() {
    if (!window.etfSignalsManager || !window.etfSignalsManager.signals) {
        console.log('No signals data available for CMP update');
        return;
    }

    // Get unique symbols from current signals
    var symbolsArray = window.etfSignalsManager.signals.map(function(signal) {
        return signal.etf || signal.symbol;
    }).filter(function(symbol) {
        return symbol;
    });

    // Remove duplicates using a simple approach
    var symbols = [];
    for (var i = 0; i < symbolsArray.length; i++) {
        if (symbols.indexOf(symbolsArray[i]) === -1) {
            symbols.push(symbolsArray[i]);
        }
    }

    if (symbols.length === 0) {
        console.log('No symbols found for CMP update');
        return;
    }

    // Get selected data source from localStorage
    var dataSource = localStorage.getItem('data-source') || 'google';
    var apiEndpoint = dataSource === 'google' ? '/api/update-live-cmp' : '/api/yahoo/update-prices';
    var sourceName = dataSource === 'google' ? 'Google Finance' : 'Yahoo Finance';

    console.log('Updating CMP for symbols using ' + sourceName + ':', symbols);

    // Call selected API to update all symbols
    fetch(apiEndpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
                timeout: 30000  // 30 second timeout
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        if (data.success) {
            console.log('CMP update response from ' + sourceName + ':', data);

            // Refresh the signals table to show updated prices
            if (window.etfSignalsManager) {
                window.etfSignalsManager.loadSignals();
            }

            // Show success message
            var updatedCount = data.updated_count || data.signals_updated || 0;
            showUpdateMessage('Updated CMP for ' + updatedCount + ' records from ' + sourceName, 'success');
        } else {
            console.error('CMP update failed:', data.error);
            showUpdateMessage('Failed to update CMP from ' + sourceName + ': ' + data.error, 'error');
        }
    })
    .catch(function(error) {
        console.error('Error updating CMP:', error);
        showUpdateMessage('Error updating CMP from ' + sourceName + ': ' + error.message, 'error');
    });
}

// Function to show update messages
function showUpdateMessage(message, type = 'info') {
    // Create or update a message element
    let messageEl = document.getElementById('cmp-update-message');
    if (!messageEl) {
        messageEl = document.createElement('div');
        messageEl.id = 'cmp-update-message';
        messageEl.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
            z-index: 1000;
            transition: opacity 0.3s;
        `;
        document.body.appendChild(messageEl);
    }

    // Set message and style based on type
    messageEl.textContent = message;
    messageEl.style.backgroundColor = type === 'success' ? '#28a745' : 
                                     type === 'error' ? '#dc3545' : '#17a2b8';
    messageEl.style.opacity = '1';

    // Hide message after 3 seconds
    setTimeout(() => {
        messageEl.style.opacity = '0';
        setTimeout(() => {
            if (messageEl.parentNode) {
                messageEl.parentNode.removeChild(messageEl);
            }
        }, 300);
    }, 3000);
}

// Function to get live price for a single symbol
function getLivePrice(symbol) {
    return fetch(`/api/google-finance/live-price/${symbol}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                return data.price;
            } else {
                throw new Error(data.error || 'Failed to fetch price');
            }
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

// Column settings functionality is handled by ETF Signals Manager

// Note: jQuery-dependent DataTable functionality removed to avoid $ dependency
// The main ETF signals functionality is handled by ETFSignalsManager class above