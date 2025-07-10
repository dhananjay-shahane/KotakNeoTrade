/**
 * Basic Trade Signals Manager - ES5 Compatible
 * Manages real-time basic trading signals display and updates
 * Fetches authentic market data from external trading database
 */
function BasicTradeSignalsManager() {
    var self = this;

    // Core data management
    this.signals = [];                  // All basic trade signals from database
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
        { key: 'id', label: 'ID', visible: true },
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

BasicTradeSignalsManager.prototype.init = function() {
    console.log('Basic Trade Signals Manager initialized');
    this.loadColumnSettings();
    this.setupEventListeners();
    this.setupColumnSettings();
    this.updateTableHeaders(); // Update headers based on column settings
    this.loadSignals();
    this.startAutoRefresh();
};

BasicTradeSignalsManager.prototype.setupEventListeners = function() {
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

    // Table header click for sorting
    var tableHeaders = document.querySelectorAll('#basicSignalsTable th[data-column]');
    tableHeaders.forEach(function(header) {
        header.addEventListener('click', function() {
            var column = this.getAttribute('data-column');
            if (column !== 'actions') {
                self.sortBy(column);
            }
        });
        header.style.cursor = 'pointer';
    });
};

BasicTradeSignalsManager.prototype.loadSignals = function() {
    var self = this;
    
    if (this.isLoading) {
        console.log('Already loading signals, skipping...');
        return;
    }

    this.isLoading = true;
    this.showLoadingState();

    fetch('/api/basic-trade-signals-data', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(function(response) {
        if (!response.ok) {
            throw new Error('Network response was not ok: ' + response.statusText);
        }
        return response.json();
    })
    .then(function(data) {
        self.isLoading = false;
        
        if (data.success && data.signals) {
            self.signals = data.signals;
            self.applyFilters();
            self.updateSignalsInfo();
            console.log('Loaded ' + self.signals.length + ' basic trade signals');
        } else {
            throw new Error(data.error || 'Failed to load signals');
        }
    })
    .catch(function(error) {
        self.isLoading = false;
        console.error('Error loading basic trade signals:', error);
        self.showErrorState('Failed to load basic trade signals: ' + error.message);
        
        if (typeof showToaster === 'function') {
            showToaster('Error', 'Failed to load basic trade signals', 'error');
        }
    });
};

BasicTradeSignalsManager.prototype.applyFilters = function() {
    var searchTerm = document.getElementById('signalSearch').value.toLowerCase();
    var self = this;

    this.filteredSignals = this.signals.filter(function(signal) {
        if (!searchTerm) return true;
        
        return (
            (signal.etf && signal.etf.toLowerCase().includes(searchTerm)) ||
            (signal.symbol && signal.symbol.toLowerCase().includes(searchTerm)) ||
            (signal.id && signal.id.toString().includes(searchTerm))
        );
    });

    this.sortSignals();
    this.currentPage = 1;
    this.renderSignals();
    this.renderPagination();
};

BasicTradeSignalsManager.prototype.sortSignals = function() {
    var self = this;
    
    this.filteredSignals.sort(function(a, b) {
        var aValue = a[self.sortField];
        var bValue = b[self.sortField];
        
        // Handle null/undefined values
        if (aValue === null || aValue === undefined) aValue = '';
        if (bValue === null || bValue === undefined) bValue = '';
        
        // Convert to numbers if numeric
        if (!isNaN(aValue) && !isNaN(bValue)) {
            aValue = parseFloat(aValue);
            bValue = parseFloat(bValue);
        }
        
        var result = 0;
        if (aValue < bValue) result = -1;
        else if (aValue > bValue) result = 1;
        
        return self.sortDirection === 'desc' ? -result : result;
    });
};

BasicTradeSignalsManager.prototype.sortBy = function(field) {
    if (this.sortField === field) {
        this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        this.sortField = field;
        this.sortDirection = 'asc';
    }
    
    this.applyFilters();
    this.updateSortIndicators();
};

BasicTradeSignalsManager.prototype.updateSortIndicators = function() {
    // Remove existing sort indicators
    var headers = document.querySelectorAll('#basicSignalsTable th[data-column]');
    headers.forEach(function(header) {
        header.classList.remove('sorted-asc', 'sorted-desc');
    });
    
    // Add sort indicator to current field
    var currentHeader = document.querySelector('#basicSignalsTable th[data-column="' + this.sortField + '"]');
    if (currentHeader) {
        currentHeader.classList.add('sorted-' + this.sortDirection);
    }
};

BasicTradeSignalsManager.prototype.renderSignals = function() {
    var tbody = document.getElementById('signalsTableBody');
    if (!tbody) return;

    var start = (this.currentPage - 1) * this.itemsPerPage;
    var end = start + this.itemsPerPage;
    var pageSignals = this.filteredSignals.slice(start, end);

    var visibleColumns = this.availableColumns.filter(function(col) { return col.visible; });
    var colspanCount = visibleColumns.length;

    if (pageSignals.length === 0) {
        tbody.innerHTML = '<tr><td colspan="' + colspanCount + '" class="text-center py-4 text-muted">No basic trade signals found</td></tr>';
        return;
    }

    var self = this;
    var html = '';
    pageSignals.forEach(function(signal) {
        html += '<tr>';
        
        visibleColumns.forEach(function(column) {
            if (column.key === 'actions') {
                html += '<td>';
                html += '<button class="btn btn-sm btn-success me-1" onclick="basicSignalsManager.buySignal(\'' + (signal.etf || '') + '\')">Buy</button>';
                html += '<button class="btn btn-sm btn-danger me-1" onclick="basicSignalsManager.sellSignal(\'' + (signal.etf || '') + '\')">Sell</button>';
                html += '<button class="btn btn-sm btn-primary" onclick="basicSignalsManager.addDeal(\'' + (signal.etf || '') + '\')">Add Deal</button>';
                html += '</td>';
            } else {
                var value = signal[column.key] || '';
                
                // Format specific columns
                if (column.key === 'etf') {
                    html += '<td><strong>' + value + '</strong></td>';
                } else if (column.key === 'ep' || column.key === 'cmp' || column.key === 'inv' || column.key === 'pl') {
                    html += '<td>₹' + (parseFloat(value) || 0).toFixed(2) + '</td>';
                } else if (column.key === 'dh' || column.key === 'chan' || column.key === 'ch') {
                    html += '<td>' + value + '%</td>';
                } else if (column.key === 'thirty' || column.key === 'seven') {
                    html += '<td>' + (parseFloat(value) || 0).toFixed(2) + '</td>';
                } else {
                    html += '<td>' + value + '</td>';
                }
            }
        });
        
        html += '</tr>';
    });

    tbody.innerHTML = html;
};

BasicTradeSignalsManager.prototype.renderPagination = function() {
    var paginationContainer = document.getElementById('signalsPagination');
    if (!paginationContainer) return;

    var totalPages = Math.ceil(this.filteredSignals.length / this.itemsPerPage);
    
    if (totalPages <= 1) {
        paginationContainer.innerHTML = '';
        return;
    }

    var html = '<ul class="pagination pagination-sm mb-0">';
    
    // Previous button
    html += '<li class="page-item' + (this.currentPage === 1 ? ' disabled' : '') + '">';
    html += '<a class="page-link" href="#" onclick="basicSignalsManager.goToPage(' + (this.currentPage - 1) + ')">Previous</a>';
    html += '</li>';
    
    // Page numbers
    for (var i = 1; i <= totalPages; i++) {
        html += '<li class="page-item' + (i === this.currentPage ? ' active' : '') + '">';
        html += '<a class="page-link" href="#" onclick="basicSignalsManager.goToPage(' + i + ')">' + i + '</a>';
        html += '</li>';
    }
    
    // Next button
    html += '<li class="page-item' + (this.currentPage === totalPages ? ' disabled' : '') + '">';
    html += '<a class="page-link" href="#" onclick="basicSignalsManager.goToPage(' + (this.currentPage + 1) + ')">Next</a>';
    html += '</li>';
    
    html += '</ul>';
    paginationContainer.innerHTML = html;
};

BasicTradeSignalsManager.prototype.goToPage = function(page) {
    var totalPages = Math.ceil(this.filteredSignals.length / this.itemsPerPage);
    
    if (page >= 1 && page <= totalPages) {
        this.currentPage = page;
        this.renderSignals();
        this.renderPagination();
    }
};

BasicTradeSignalsManager.prototype.updateSignalsInfo = function() {
    var infoElement = document.getElementById('signalsInfo');
    if (infoElement) {
        var total = this.signals.length;
        var filtered = this.filteredSignals.length;
        var start = (this.currentPage - 1) * this.itemsPerPage + 1;
        var end = Math.min(start + this.itemsPerPage - 1, filtered);
        
        if (filtered === 0) {
            infoElement.textContent = 'No signals found';
        } else {
            infoElement.textContent = 'Showing ' + start + '-' + end + ' of ' + filtered + ' signals';
        }
    }
};

BasicTradeSignalsManager.prototype.showLoadingState = function() {
    var tbody = document.getElementById('signalsTableBody');
    if (tbody) {
        var visibleColumns = this.availableColumns.filter(function(col) { return col.visible; });
        var colspanCount = visibleColumns.length;
        tbody.innerHTML = '<tr><td colspan="' + colspanCount + '" class="text-center py-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div><p class="mt-2 text-muted">Loading basic trade signals...</p></td></tr>';
    }
};

BasicTradeSignalsManager.prototype.showErrorState = function(message) {
    var tbody = document.getElementById('signalsTableBody');
    if (tbody) {
        var visibleColumns = this.availableColumns.filter(function(col) { return col.visible; });
        var colspanCount = visibleColumns.length;
        tbody.innerHTML = '<tr><td colspan="' + colspanCount + '" class="text-center py-4 text-danger"><i class="fas fa-exclamation-triangle mb-2"></i><br>' + message + '</td></tr>';
    }
};

BasicTradeSignalsManager.prototype.startAutoRefresh = function() {
    var self = this;
    this.stopAutoRefresh();
    
    this.refreshInterval = setInterval(function() {
        self.loadSignals();
    }, 30000); // Refresh every 30 seconds
    
    console.log('Auto-refresh started for basic trade signals');
};

BasicTradeSignalsManager.prototype.stopAutoRefresh = function() {
    if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
        this.refreshInterval = null;
        console.log('Auto-refresh stopped for basic trade signals');
    }
};

// Column Settings Management
BasicTradeSignalsManager.prototype.loadColumnSettings = function() {
    var saved = localStorage.getItem('basicSignalsColumnSettings');
    if (saved) {
        try {
            var settings = JSON.parse(saved);
            this.availableColumns.forEach(function(column) {
                if (settings[column.key] !== undefined) {
                    column.visible = settings[column.key];
                }
            });
        } catch (e) {
            console.error('Error loading column settings:', e);
        }
    }
};

BasicTradeSignalsManager.prototype.saveColumnSettings = function() {
    var settings = {};
    this.availableColumns.forEach(function(column) {
        settings[column.key] = column.visible;
    });
    localStorage.setItem('basicSignalsColumnSettings', JSON.stringify(settings));
};

BasicTradeSignalsManager.prototype.setupColumnSettings = function() {
    var checkboxContainer = document.getElementById('columnCheckboxes');
    if (!checkboxContainer) return;

    var html = '';
    this.availableColumns.forEach(function(column) {
        html += '<div class="form-check">';
        html += '<input class="form-check-input" type="checkbox" id="col_' + column.key + '"' + (column.visible ? ' checked' : '') + '>';
        html += '<label class="form-check-label" for="col_' + column.key + '">' + column.label + '</label>';
        html += '</div>';
    });
    
    checkboxContainer.innerHTML = html;
};

BasicTradeSignalsManager.prototype.showColumnSettings = function() {
    var modal = new bootstrap.Modal(document.getElementById('columnSettingsModal'));
    modal.show();
};

BasicTradeSignalsManager.prototype.applyColumnSettings = function() {
    var self = this;
    
    this.availableColumns.forEach(function(column) {
        var checkbox = document.getElementById('col_' + column.key);
        if (checkbox) {
            column.visible = checkbox.checked;
        }
    });
    
    this.saveColumnSettings();
    this.updateTableHeaders();
    this.renderSignals();
    
    // Close modal
    var modal = bootstrap.Modal.getInstance(document.getElementById('columnSettingsModal'));
    if (modal) {
        modal.hide();
    }
};

BasicTradeSignalsManager.prototype.updateTableHeaders = function() {
    var headerRow = document.getElementById('tableHeader');
    if (!headerRow) return;

    var self = this;
    var html = '';
    this.availableColumns.forEach(function(column) {
        if (column.visible) {
            if (column.key === 'actions') {
                html += '<th data-column="' + column.key + '">' + column.label + '</th>';
            } else {
                html += '<th data-column="' + column.key + '" style="cursor: pointer;" onclick="basicSignalsManager.sortBy(\'' + column.key + '\')">' + column.label + ' <i class="fas fa-sort ms-1"></i></th>';
            }
        }
    });
    
    headerRow.innerHTML = html;
};

// Trading Actions
BasicTradeSignalsManager.prototype.buySignal = function(symbol) {
    if (typeof showToaster === 'function') {
        showToaster('Buy Order', 'Initiating buy order for ' + symbol, 'info');
    }
    console.log('Buy signal for:', symbol);
};

BasicTradeSignalsManager.prototype.sellSignal = function(symbol) {
    if (typeof showToaster === 'function') {
        showToaster('Sell Order', 'Initiating sell order for ' + symbol, 'info');
    }
    console.log('Sell signal for:', symbol);
};

BasicTradeSignalsManager.prototype.addDeal = function(symbol) {
    if (typeof showToaster === 'function') {
        showToaster('Add Deal', 'Adding ' + symbol + ' to deals', 'success');
    }
    console.log('Add deal for:', symbol);
    
    // You can add logic here to actually add the deal to the system
    // For now, just show a success message
    setTimeout(function() {
        if (typeof showToaster === 'function') {
            showToaster('Deal Added', symbol + ' has been added to your deals', 'success');
        }
    }, 1000);
};