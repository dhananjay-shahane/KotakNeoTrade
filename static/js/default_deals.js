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
        actions: {
            label: "ACTION",
            default: true,
            width: "120px",
            sortable: false,
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
    const searchInput = document.getElementById("symbolSearchInput");
    if (searchInput) {
        searchInput.addEventListener("input", () => {
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
        tbody.innerHTML =
            "<tr>" +
            '<td colspan="' +
            this.selectedColumns.length +
            '" class="text-center py-5" style="background: var(--card-bg); min-height: 300px;">' +
            '<div class="d-flex flex-column justify-content-center align-items-center" style="min-height: 250px;">' +
            '<div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem; border-width: 4px;">' +
            '<span class="visually-hidden">Loading...</span>' +
            "</div>" +
            '<h6 class="text-light mb-2">Loading Defult Deals Data</h6>' +
            '<p class="text-muted mb-3">Fetching Defult data from database...</p>' +
            '<small class="text-warning">This may take up to 15 seconds</small>' +
            "</div>" +
            "</td>" +
            "</tr>";
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
                : "";
            headersHTML += `
                <th style="width: ${column.width}; min-width: ${column.width};" 
                    ${column.sortable ? `class="sortable-header" onclick="defaultDealsManager.sortBy('${columnKey}')"` : ""}>
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
        // Check if deal is closed to apply row styling
        const isClosed = deal.pos === 0 || deal.pos === "0";
        const rowClass = isClosed ? "closed-deal" : "";

        rowsHTML += `<tr class="${rowClass}">`;
        this.selectedColumns.forEach((columnKey) => {
            const value = this.formatCellValue(deal, columnKey);
            const cssClass = this.getCellClass(deal, columnKey);
            const gradientStyle = this.getGradientStyle(deal, columnKey);
            rowsHTML += `<td class="${cssClass}" style="${gradientStyle}">${value}</td>`;
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
                    return date.toLocaleDateString("en-IN");
                } catch (e) {
                    return value;
                }
            }
            return "--";

        case "status":
            return `<span class="status-badge status-${(value || "active").toLowerCase()}">${value || "ACTIVE"}</span>`;

        case "pos":
            // Default to 1, becomes 0 when closed
            return deal.pos === 1 || deal.pos === "1" ? "1api/default-deals" : "1";

        case "actions":
            // Check if deal is closed
            const isClosed = deal.pos === 0 || deal.pos === "0";

            if (isClosed) {
                // Show disabled buttons for closed deals
                return `
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-warning btn-sm" disabled title="Deal is closed">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                        <button class="btn btn-danger btn-sm" disabled title="Deal is closed">
                            <i class="fas fa-times"></i> Close
                        </button>
                    </div>
                `;
            } else {
                // Show enabled buttons for active deals
                return `
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-warning btn-sm" onclick="editDefaultDeal('${deal.id || deal.trade_signal_id || ""}', '${deal.symbol || ""}', ${deal.ep || 0}, ${deal.tp || 0})">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="closeDefaultDeal('${deal.id || deal.trade_signal_id || ""}', '${deal.symbol || ""}')">
                            <i class="fas fa-times"></i> Close
                        </button>
                    </div>
                `;
            }

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
            cssClass =
                deal[columnKey] === "BUY" ? "text-success" : "text-danger";
            break;

        default:
            cssClass = "";
    }

    return cssClass;
};

DefaultDealsManager.prototype.getGradientStyle = function (deal, columnKey) {
    // Apply gradient colors to percentage and profit/loss columns
    switch (columnKey) {
        case "chan_percent":
        case "seven_percent":
        case "thirty_percent":
            const percentValue = deal[columnKey];
            if (typeof percentValue === "number") {
                return this.getGradientBackgroundColor(percentValue);
            }
            break;

        case "pl":
            const plValue = deal[columnKey];
            if (typeof plValue === "number") {
                return this.getGradientBackgroundColor(plValue);
            }
            break;

        default:
            return "";
    }
    return "";
};

DefaultDealsManager.prototype.updateStats = function () {
    const totalCount = document.getElementById("totalCount");
    const showingCount = document.getElementById("showingCount");
    const visibleDealsCount = document.getElementById("visibleDealsCount");

    if (totalCount) totalCount.textContent = this.deals.length;
    if (showingCount)
        showingCount.textContent = Math.min(
            this.filteredDeals.length,
            this.pageSize,
        );
    if (visibleDealsCount)
        visibleDealsCount.textContent = this.filteredDeals.length;
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
    const searchInput = document.getElementById("symbolSearchInput");
    if (!searchInput) return;

    const searchTerm = searchInput.value.toLowerCase().trim();

    if (searchTerm === "") {
        this.filteredDeals = [...this.deals];
    } else {
        this.filteredDeals = this.deals.filter((deal) => {
            return Object.values(deal).some((value) => {
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
    const searchInput = document.getElementById("symbolSearchInput");
    if (searchInput) {
        searchInput.value = "";
        this.performSearch();
    }
};

DefaultDealsManager.prototype.sortBy = function (columnKey) {
    console.log(`🔄 Sorting by ${columnKey}`);

    this.filteredDeals.sort((a, b) => {
        let valueA = a[columnKey];
        let valueB = b[columnKey];

        // Handle null/undefined values
        if (valueA === null || valueA === undefined) valueA = "";
        if (valueB === null || valueB === undefined) valueB = "";

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
    const checkboxes = document.querySelectorAll(
        '#columnCheckboxes input[type="checkbox"]',
    );
    this.selectedColumns = [];

    checkboxes.forEach((checkbox) => {
        if (checkbox.checked) {
            this.selectedColumns.push(checkbox.value);
        }
    });

    this.renderTable();
    const modal = bootstrap.Modal.getInstance(
        document.getElementById("columnSettingsModal"),
    );
    if (modal) modal.hide();
};

DefaultDealsManager.prototype.selectAllColumns = function () {
    const checkboxes = document.querySelectorAll(
        '#columnCheckboxes input[type="checkbox"]',
    );
    checkboxes.forEach((checkbox) => {
        checkbox.checked = true;
    });
};

DefaultDealsManager.prototype.resetDefaultColumns = function () {
    const defaultColumns = this.getDefaultColumns();
    const checkboxes = document.querySelectorAll(
        '#columnCheckboxes input[type="checkbox"]',
    );

    checkboxes.forEach((checkbox) => {
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

DefaultDealsManager.prototype.setRefreshInterval = function (
    interval,
    displayText,
) {
    this.refreshIntervalTime = interval;
    const currentIntervalElement = document.getElementById("currentInterval");
    if (currentIntervalElement) {
        currentIntervalElement.textContent = displayText;
    }

    this.stopAutoRefresh();
    this.startAutoRefresh();
};

DefaultDealsManager.prototype.exportDeals = function () {
    const csvContent = this.convertToCSV(this.filteredDeals);
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", `default_deals_${new Date().getTime()}.csv`);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
};

DefaultDealsManager.prototype.convertToCSV = function (data) {
    if (data.length === 0) return "";

    const headers = this.selectedColumns.map(
        (key) => this.availableColumns[key].label,
    );
    const csvRows = [headers.join(",")];

    data.forEach((deal) => {
        const row = this.selectedColumns.map((key) => {
            let value = deal[key];
            if (value === null || value === undefined) value = "";
            // Escape quotes and wrap in quotes if contains comma
            if (typeof value === "string" && value.includes(",")) {
                value = `"${value.replace(/"/g, '""')}"`;
            }
            return value;
        });
        csvRows.push(row.join(","));
    });

    return csvRows.join("\n");
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
    if (
        window.defaultDealsManager &&
        window.defaultDealsManager.currentPage > 1
    ) {
        window.defaultDealsManager.currentPage--;
        window.defaultDealsManager.renderTable();
    }
}

function nextPage() {
    if (window.defaultDealsManager) {
        const totalPages = Math.ceil(
            window.defaultDealsManager.filteredDeals.length /
                window.defaultDealsManager.pageSize,
        );
        if (window.defaultDealsManager.currentPage < totalPages) {
            window.defaultDealsManager.currentPage++;
            window.defaultDealsManager.renderTable();
        }
    }
}

// Gradient background color function for styling cells based on values
DefaultDealsManager.prototype.getGradientBackgroundColor = function (value) {
    var numValue = parseFloat(value);
    if (isNaN(numValue)) return "";

    var intensity = Math.min(Math.abs(numValue) / 5, 1); // Scale to 0-1, max at 5%
    var alpha = 0.3 + intensity * 0.5; // Alpha from 0.3 to 0.8

    if (numValue < 0) {
        // Red gradient for negative values
        if (intensity <= 0.3) {
            // Light red for small negative values
            return (
                "background-color: rgba(255, 182, 193, " +
                alpha +
                "); color: #000;"
            ); // Light pink
        } else if (intensity <= 0.6) {
            // Medium red
            return (
                "background-color: rgba(255, 99, 71, " +
                alpha +
                "); color: #fff;"
            ); // Tomato
        } else {
            // Dark red for large negative values
            return (
                "background-color: rgba(139, 0, 0, " + alpha + "); color: #fff;"
            ); // Dark red
        }
    } else if (numValue > 0) {
        // Green gradient for positive values
        if (intensity <= 0.3) {
            // Light green for small positive values
            return (
                "background-color: rgba(144, 238, 144, " +
                alpha +
                "); color: #000;"
            ); // Light green
        } else if (intensity <= 0.6) {
            // Medium green
            return (
                "background-color: rgba(50, 205, 50, " +
                alpha +
                "); color: #fff;"
            ); // Lime green
        } else {
            // Dark green for large positive values
            return (
                "background-color: rgba(0, 100, 0, " + alpha + "); color: #fff;"
            ); // Dark green
        }
    }

    return "";
};

// Edit Deal Function for Default Deals
function editDefaultDeal(dealId, symbol, entryPrice, targetPrice) {
    // Input validation
    if (!dealId || dealId.trim() === "") {
        alert("Invalid deal ID provided");
        return;
    }

    if (!symbol || symbol.trim() === "") {
        alert("Invalid symbol provided");
        return;
    }

    // Show edit modal
    showEditDefaultDealModal(dealId, symbol, entryPrice, targetPrice);
}

// Close Deal Function for Default Deals
function closeDefaultDeal(dealId, symbol) {
    // Input validation
    if (!dealId || dealId.trim() === "") {
        Swal.fire({
            icon: "error",
            title: "Error",
            text: "Invalid deal ID provided",
        });
        return;
    }

    if (!symbol || symbol.trim() === "") {
        Swal.fire({
            icon: "error",
            title: "Error",
            text: "Invalid symbol provided",
        });
        return;
    }

    // SweetAlert confirmation dialog
    Swal.fire({
        title: "Close Deal",
        text: `Are you sure you want to close the deal for ${symbol}?`,
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#d33",
        cancelButtonColor: "#6c757d",
        confirmButtonText: "Yes, Close Deal",
        cancelButtonText: "Cancel",
    }).then((result) => {
        if (result.isConfirmed) {
            // Submit close deal request via AJAX
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/default-close-deal", true);
            xhr.setRequestHeader("Content-Type", "application/json");

            xhr.onreadystatechange = function () {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        Swal.fire({
                            icon: "success",
                            title: "Success",
                            text: `Deal closed successfully for ${symbol}`,
                            timer: 2000,
                            showConfirmButton: false,
                        });
                        // Refresh deals table
                        window.defaultDealsManager.loadDeals();
                    } else {
                        Swal.fire({
                            icon: "error",
                            title: "Error",
                            text: "Failed to close deal. Please try again.",
                        });
                    }
                }
            };

            xhr.send(
                JSON.stringify({
                    deal_id: dealId,
                    symbol: symbol,
                }),
            );
        }
    });
}

// Show Edit Modal for Default Deals
function showEditDefaultDealModal(dealId, symbol, entryPrice, targetPrice) {
    // Set values in the edit modal
    document.getElementById("editDefaultDealId").value = dealId;
    document.getElementById("editDefaultSymbol").value = symbol;
    document.getElementById("editDefaultEntryPrice").value = entryPrice || "";
    document.getElementById("editDefaultTargetPrice").value = targetPrice || "";

    // Show the modal
    var editModal = new bootstrap.Modal(
        document.getElementById("editDefaultDealModal"),
    );
    editModal.show();
}

// Submit Edit Deal for Default Deals
function submitEditDefaultDeal() {
    var dealId = document.getElementById("editDefaultDealId").value;
    var symbol = document.getElementById("editDefaultSymbol").value;
    var entryPrice = parseFloat(
        document.getElementById("editDefaultEntryPrice").value,
    );
    var targetPrice = parseFloat(
        document.getElementById("editDefaultTargetPrice").value,
    );

    // Validation
    if (!dealId || !symbol) {
        alert("Deal ID and Symbol are required");
        return;
    }

    if (isNaN(entryPrice) || entryPrice <= 0) {
        alert("Please enter a valid entry price");
        return;
    }

    if (isNaN(targetPrice) || targetPrice <= 0) {
        alert("Please enter a valid target price");
        return;
    }

    // Submit edit request via AJAX
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/default-edit-deal", true);
    xhr.setRequestHeader("Content-Type", "application/json");

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                alert("Deal updated successfully for " + symbol);
                // Hide modal
                var editModal = bootstrap.Modal.getInstance(
                    document.getElementById("editDefaultDealModal"),
                );
                editModal.hide();
                // Refresh deals table
                window.defaultDealsManager.loadDeals();
            } else {
                alert("Failed to update deal. Please try again.");
            }
        }
    };

    xhr.send(
        JSON.stringify({
            deal_id: dealId,
            symbol: symbol,
            entry_price: entryPrice,
            target_price: targetPrice,
        }),
    );
}

// Initialize when DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
    console.log("🎯 DOM loaded, initializing Default Deals Manager");
    window.defaultDealsManager = new DefaultDealsManager();
});
