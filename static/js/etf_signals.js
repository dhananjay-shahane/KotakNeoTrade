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
        { key: 'trade_signal_id', label: 'ID', visible: true },
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
            case 'qt':
                cellValue = signal.qt || quantity;
                break;
            case 'seven':
                cellValue = signal.seven || '--';
                break;
            case 'ch':
                var chValue = signal.ch || changePct.toFixed(2) + '%';
                var bgColor = this.getGradientBackgroundColor(changePct);
                cellStyle = bgColor;
                cellValue = '<span class="fw-bold">' + chValue + '</span>';
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

    // Use SweetAlert2 for better confirmation dialog
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
                                    confirmButtonColor: '#28a745'
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

// Column settings functionality is handled by ETF Signals Manager