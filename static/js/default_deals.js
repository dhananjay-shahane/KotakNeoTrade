function DefaultDealsManager() {
    this.deals = [];
    this.filteredDeals = [];
    this.currentPage = 1;
    this.pageSize = 20;
    this.autoRefresh = true;
    this.refreshInterval = null;
    this.refreshIntervalTime = 300000; // 5 minutes
    this.searchTimeout = null;
    this.sortDirection = "asc";
    this.isLoading = false;

    this.availableColumns = {
        id: {
            label: "ID",
            default: true,
            width: "50px",
            sortable: true,
        },
        symbol: {
            label: "Symbol",
            default: true,
            width: "80px",
            sortable: true,
        },
        seven: { label: "7D", default: true, width: "50px", sortable: true },
        seven_percent: {
            label: "7D%",
            default: true,
            width: "50px",
            sortable: true,
        },
        thirty: { label: "30D", default: true, width: "50px", sortable: true },
        thirty_percent: {
            label: "30D%",
            default: true,
            width: "50px",
            sortable: true,
        },
        date: { label: "DATE", default: true, width: "80px", sortable: true },
        qty: { label: "QTY", default: true, width: "60px", sortable: true },
        ep: { label: "EP", default: true, width: "70px", sortable: true },
        cmp: { label: "CMP", default: true, width: "70px", sortable: true },
        pos: { label: "POS", default: true, width: "50px", sortable: true },
        chan_percent: {
            label: "%CHAN",
            default: true,
            width: "60px",
            sortable: true,
        },
        inv: { label: "INV.", default: true, width: "70px", sortable: true },
        tp: { label: "TP", default: true, width: "60px", sortable: true },
        tpr: { label: "TPR", default: true, width: "70px", sortable: true },
        tva: { label: "TVA", default: true, width: "70px", sortable: true },
        pl: { label: "CPL", default: true, width: "60px", sortable: true },
        qt: { label: "QT", default: true, width: "60px", sortable: true },
        ed: { label: "ED", default: true, width: "70px", sortable: true },
        exp: { label: "EXP", default: false, width: "70px", sortable: true },
        pr: { label: "PR", default: false, width: "80px", sortable: true },
        pp: { label: "PP", default: false, width: "50px", sortable: true },
        iv: { label: "IV", default: false, width: "60px", sortable: true },
        ip: { label: "IP", default: false, width: "60px", sortable: true },
        status: {
            label: "STATUS",
            default: true,
            width: "80px",
            sortable: true,
        },
    };

    this.selectedColumns = this.getDefaultColumns();
    this.init();
}

DefaultDealsManager.prototype.getDefaultColumns = function () {
    const columns = [];
    for (const key in this.availableColumns) {
        if (this.availableColumns[key].default) {
            columns.push(key);
        }
    }
    return columns;
};

DefaultDealsManager.prototype.init = function () {
    console.log("🚀 Initializing Default Deals Manager");
    this.setupColumnSettings();
    this.loadDeals();
    this.startAutoRefresh();
    
    // Setup search functionality
    const searchInput = document.getElementById('symbolSearchInput');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            this.performSearch();
        });
    }
};

DefaultDealsManager.prototype.loadDeals = function () {
    console.log("📊 Loading default deals data...");
    this.isLoading = true;
    
    // Show loading state
    this.showLoadingState();
    
    fetch("/api/default-deals")
        .then((response) => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then((data) => {
            console.log("✅ Default deals data loaded:", data);
            this.deals = data.deals || [];
            this.filteredDeals = [...this.deals];
            this.renderTable();
            this.updateStats();
            this.isLoading = false;
        })
        .catch((error) => {
            console.error("❌ Error loading default deals:", error);
            this.showErrorState(error.message);
            this.isLoading = false;
        });
};

DefaultDealsManager.prototype.showLoadingState = function () {
    const tbody = document.getElementById("dealsTableBody");
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="20" class="text-center text-muted py-4">
                    <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                    Loading default deals data...
                </td>
            </tr>
        `;
    }
};

DefaultDealsManager.prototype.showErrorState = function (errorMessage) {
    const tbody = document.getElementById("dealsTableBody");
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="20" class="text-center text-danger py-4">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Error loading data: ${errorMessage}
                    <br>
                    <button class="btn btn-sm btn-outline-primary mt-2" onclick="defaultDealsManager.loadDeals()">
                        <i class="fas fa-sync-alt me-1"></i>Retry
                    </button>
                </td>
            </tr>
        `;
    }
};

DefaultDealsManager.prototype.renderTable = function () {
    console.log("🎨 Rendering default deals table...");
    this.renderHeaders();
    this.renderRows();
    this.updatePagination();
};

DefaultDealsManager.prototype.renderHeaders = function () {
    const headersRow = document.getElementById("tableHeaders");
    if (!headersRow) return;

    let headersHTML = "";
    this.selectedColumns.forEach((columnKey) => {
        const column = this.availableColumns[columnKey];
        if (column) {
            const sortIcon = column.sortable 
                ? '<i class="fas fa-sort sort-icon"></i>' 
                : '';
            headersHTML += `
                <th style="width: ${column.width}; min-width: ${column.width};" 
                    ${column.sortable ? `class="sortable-header" onclick="defaultDealsManager.sortBy('${columnKey}')"` : ''}>
                    ${column.label}${sortIcon}
                </th>
            `;
        }
    });
    headersRow.innerHTML = headersHTML;
};

DefaultDealsManager.prototype.renderRows = function () {
    const tbody = document.getElementById("dealsTableBody");
    if (!tbody) return;

    if (this.filteredDeals.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="${this.selectedColumns.length}" class="text-center text-muted py-4">
                    <i class="fas fa-inbox me-2"></i>
                    No default deals data available
                </td>
            </tr>
        `;
        return;
    }

    const startIndex = (this.currentPage - 1) * this.pageSize;
    const endIndex = startIndex + this.pageSize;
    const pageDeals = this.filteredDeals.slice(startIndex, endIndex);

    let rowsHTML = "";
    pageDeals.forEach((deal) => {
        rowsHTML += "<tr>";
        this.selectedColumns.forEach((columnKey) => {
            const value = this.formatCellValue(deal, columnKey);
            const cssClass = this.getCellClass(deal, columnKey);
            rowsHTML += `<td class="${cssClass}">${value}</td>`;
        });
        rowsHTML += "</tr>";
    });

    tbody.innerHTML = rowsHTML;
};

DefaultDealsManager.prototype.formatCellValue = function (deal, columnKey) {
    const value = deal[columnKey];
    
    if (value === null || value === undefined) {
        return "--";
    }

    switch (columnKey) {
        case "cmp":
        case "ep":
        case "tp":
        case "tpr":
        case "tva":
        case "inv":
            return typeof value === "number" ? value.toFixed(2) : value;
        
        case "chan_percent":
        case "seven_percent":
        case "thirty_percent":
            if (typeof value === "number") {
                const formatted = value.toFixed(2) + "%";
                return value >= 0 ? `+${formatted}` : formatted;
            }
            return value;
        
        case "pl":
            if (typeof value === "number") {
                const formatted = value.toFixed(2);
                return value >= 0 ? `+${formatted}` : formatted;
            }
            return value;
        
        case "date":
        case "ed":
            if (value && value !== "--") {
                try {
                    const date = new Date(value);
                    return date.toLocaleDateString('en-IN');
                } catch (e) {
                    return value;
                }
            }
            return "--";
        
        case "status":
            return `<span class="status-badge status-${(value || 'active').toLowerCase()}">${value || 'ACTIVE'}</span>`;
        
        default:
            return value;
    }
};

DefaultDealsManager.prototype.getCellClass = function (deal, columnKey) {
    let cssClass = "";
    
    switch (columnKey) {
        case "chan_percent":
        case "seven_percent":
        case "thirty_percent":
        case "pl":
            const value = deal[columnKey];
            if (typeof value === "number") {
                if (value > 0) cssClass = "profit";
                else if (value < 0) cssClass = "loss";
                else cssClass = "neutral";
            }
            break;
        
        case "pos":
            cssClass = deal[columnKey] === "BUY" ? "text-success" : "text-danger";
            break;
        
        default:
            cssClass = "";
    }
    
    return cssClass;
};

DefaultDealsManager.prototype.updateStats = function () {
    const totalCount = document.getElementById("totalCount");
    const showingCount = document.getElementById("showingCount");
    const visibleDealsCount = document.getElementById("visibleDealsCount");
    
    if (totalCount) totalCount.textContent = this.deals.length;
    if (showingCount) showingCount.textContent = Math.min(this.filteredDeals.length, this.pageSize);
    if (visibleDealsCount) visibleDealsCount.textContent = this.filteredDeals.length;
};

DefaultDealsManager.prototype.updatePagination = function () {
    const totalPages = Math.ceil(this.filteredDeals.length / this.pageSize);
    
    const currentPageSpan = document.getElementById("currentPage");
    const totalPagesSpan = document.getElementById("totalPages");
    const prevBtn = document.getElementById("prevBtn");
    const nextBtn = document.getElementById("nextBtn");
    
    if (currentPageSpan) currentPageSpan.textContent = this.currentPage;
    if (totalPagesSpan) totalPagesSpan.textContent = totalPages;
    
    if (prevBtn) prevBtn.disabled = this.currentPage <= 1;
    if (nextBtn) nextBtn.disabled = this.currentPage >= totalPages;
};

DefaultDealsManager.prototype.performSearch = function () {
    const searchInput = document.getElementById('symbolSearchInput');
    if (!searchInput) return;
    
    const searchTerm = searchInput.value.toLowerCase().trim();
    
    if (searchTerm === '') {
        this.filteredDeals = [...this.deals];
    } else {
        this.filteredDeals = this.deals.filter(deal => {
            return Object.values(deal).some(value => {
                if (value === null || value === undefined) return false;
                return value.toString().toLowerCase().includes(searchTerm);
            });
        });
    }
    
    this.currentPage = 1;
    this.renderTable();
    this.updateStats();
};

DefaultDealsManager.prototype.clearSearch = function () {
    const searchInput = document.getElementById('symbolSearchInput');
    if (searchInput) {
        searchInput.value = '';
        this.performSearch();
    }
};

DefaultDealsManager.prototype.sortBy = function (columnKey) {
    console.log(`🔄 Sorting by ${columnKey}`);
    
    this.filteredDeals.sort((a, b) => {
        let valueA = a[columnKey];
        let valueB = b[columnKey];
        
        // Handle null/undefined values
        if (valueA === null || valueA === undefined) valueA = '';
        if (valueB === null || valueB === undefined) valueB = '';
        
        // Convert to numbers if possible
        if (!isNaN(valueA) && !isNaN(valueB)) {
            valueA = parseFloat(valueA);
            valueB = parseFloat(valueB);
        }
        
        if (this.sortDirection === "asc") {
            return valueA > valueB ? 1 : -1;
        } else {
            return valueA < valueB ? 1 : -1;
        }
    });
    
    this.sortDirection = this.sortDirection === "asc" ? "desc" : "asc";
    this.renderRows();
};

DefaultDealsManager.prototype.setupColumnSettings = function () {
    const checkboxContainer = document.getElementById("columnCheckboxes");
    if (!checkboxContainer) return;

    let checkboxHTML = "";
    for (const key in this.availableColumns) {
        const column = this.availableColumns[key];
        const isChecked = this.selectedColumns.includes(key) ? "checked" : "";
        checkboxHTML += `
            <div class="col-md-4 mb-2">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" 
                           id="col_${key}" value="${key}" ${isChecked}>
                    <label class="form-check-label" for="col_${key}">
                        ${column.label}
                    </label>
                </div>
            </div>
        `;
    }
    checkboxContainer.innerHTML = checkboxHTML;
};

DefaultDealsManager.prototype.applyColumnSettings = function () {
    const checkboxes = document.querySelectorAll('#columnCheckboxes input[type="checkbox"]');
    this.selectedColumns = [];
    
    checkboxes.forEach(checkbox => {
        if (checkbox.checked) {
            this.selectedColumns.push(checkbox.value);
        }
    });
    
    this.renderTable();
    const modal = bootstrap.Modal.getInstance(document.getElementById('columnSettingsModal'));
    if (modal) modal.hide();
};

DefaultDealsManager.prototype.selectAllColumns = function () {
    const checkboxes = document.querySelectorAll('#columnCheckboxes input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.checked = true;
    });
};

DefaultDealsManager.prototype.resetDefaultColumns = function () {
    const defaultColumns = this.getDefaultColumns();
    const checkboxes = document.querySelectorAll('#columnCheckboxes input[type="checkbox"]');
    
    checkboxes.forEach(checkbox => {
        checkbox.checked = defaultColumns.includes(checkbox.value);
    });
};

DefaultDealsManager.prototype.startAutoRefresh = function () {
    if (this.autoRefresh && !this.refreshInterval) {
        this.refreshInterval = setInterval(() => {
            console.log("🔄 Auto-refreshing default deals...");
            this.loadDeals();
        }, this.refreshIntervalTime);
    }
};

DefaultDealsManager.prototype.stopAutoRefresh = function () {
    if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
        this.refreshInterval = null;
    }
};

DefaultDealsManager.prototype.setRefreshInterval = function (interval, displayText) {
    this.refreshIntervalTime = interval;
    const currentIntervalElement = document.getElementById('currentInterval');
    if (currentIntervalElement) {
        currentIntervalElement.textContent = displayText;
    }
    
    this.stopAutoRefresh();
    this.startAutoRefresh();
};

DefaultDealsManager.prototype.exportDeals = function () {
    const csvContent = this.convertToCSV(this.filteredDeals);
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `default_deals_${new Date().getTime()}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
};

DefaultDealsManager.prototype.convertToCSV = function (data) {
    if (data.length === 0) return '';
    
    const headers = this.selectedColumns.map(key => this.availableColumns[key].label);
    const csvRows = [headers.join(',')];
    
    data.forEach(deal => {
        const row = this.selectedColumns.map(key => {
            let value = deal[key];
            if (value === null || value === undefined) value = '';
            // Escape quotes and wrap in quotes if contains comma
            if (typeof value === 'string' && value.includes(',')) {
                value = `"${value.replace(/"/g, '""')}"`;
            }
            return value;
        });
        csvRows.push(row.join(','));
    });
    
    return csvRows.join('\n');
};

// Global functions for template compatibility
function refreshDeals() {
    if (window.defaultDealsManager) {
        window.defaultDealsManager.loadDeals();
    }
}

function clearSearch() {
    if (window.defaultDealsManager) {
        window.defaultDealsManager.clearSearch();
    }
}

function performSearch() {
    if (window.defaultDealsManager) {
        window.defaultDealsManager.performSearch();
    }
}

function applyColumnSettings() {
    if (window.defaultDealsManager) {
        window.defaultDealsManager.applyColumnSettings();
    }
}

function selectAllColumns() {
    if (window.defaultDealsManager) {
        window.defaultDealsManager.selectAllColumns();
    }
}

function resetDefaultColumns() {
    if (window.defaultDealsManager) {
        window.defaultDealsManager.resetDefaultColumns();
    }
}

function setRefreshInterval(interval, displayText) {
    if (window.defaultDealsManager) {
        window.defaultDealsManager.setRefreshInterval(interval, displayText);
    }
}

function exportDeals() {
    if (window.defaultDealsManager) {
        window.defaultDealsManager.exportDeals();
    }
}

function previousPage() {
    if (window.defaultDealsManager && window.defaultDealsManager.currentPage > 1) {
        window.defaultDealsManager.currentPage--;
        window.defaultDealsManager.renderTable();
    }
}

function nextPage() {
    if (window.defaultDealsManager) {
        const totalPages = Math.ceil(window.defaultDealsManager.filteredDeals.length / window.defaultDealsManager.pageSize);
        if (window.defaultDealsManager.currentPage < totalPages) {
            window.defaultDealsManager.currentPage++;
            window.defaultDealsManager.renderTable();
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log("🎯 DOM loaded, initializing Default Deals Manager");
    window.defaultDealsManager = new DefaultDealsManager();
});