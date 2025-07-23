/**
 * ETF Signals Manager - ES5 Compatible
 * Manages real-time ETF trading signals display and updates
 * Fetches authentic market data from external trading database
 */
function ETFSignalsManager() {
    var self = this;

    // Core data management
    this.signals = []; // All ETF signals from database
    this.filteredSignals = []; // Filtered signals based on search/sort
    this.displayedSignals = []; // Currently displayed signals
    this.currentPage = 1; // Current page in pagination
    this.itemsPerPage = 20; // Number of signals per page
    this.totalPages = 1; // Total number of pages
    this.isLoading = false; // Loading state flag
    this.refreshInterval = null; // Auto-refresh timer

    // Table sorting configuration
    this.sortField = "id"; // Current sort field
    this.sortDirection = "asc"; // Sort direction (asc/desc)

    // Column visibility settings
    this.availableColumns = [
        { key: "trade_signal_id", label: "ID", visible: true },
        { key: "etf", label: "Symbol", visible: true },
        { key: "seven", label: "7D", visible: true },
        { key: "ch", label: "7D%", visible: true },
        { key: "thirty", label: "30D", visible: true },
        { key: "dh", label: "30D%", visible: true },
        { key: "date", label: "DATE", visible: true },
        { key: "qty", label: "QTY", visible: true },
        { key: "ep", label: "EP", visible: true },
        { key: "cmp", label: "CMP", visible: true },
        { key: "chan", label: "%CHAN", visible: true },
        { key: "inv", label: "INV.", visible: true },
        { key: "tp", label: "TP", visible: false },
        { key: "tpr", label: "TPR", visible: false },
        { key: "tva", label: "TVA", visible: false },
        { key: "cpl", label: "CPL", visible: true },
        { key: "ed", label: "ED", visible: false },
        { key: "exp", label: "EXP", visible: false },
        { key: "pr", label: "PR", visible: false },
        { key: "pp", label: "PP", visible: false },
        { key: "iv", label: "IV", visible: false },
        { key: "ip", label: "IP", visible: false },

        // { key: "qt", label: "QT", visible: false },
        { key: "actions", label: "ACTIONS", visible: true },
    ];

    // Initialize when DOM is ready
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () {
            self.init();
        });
    } else {
        this.init();
    }
}

ETFSignalsManager.prototype.init = function () {
    console.log("ETF Signals Manager initialized");
    this.loadColumnSettings();
    this.setupEventListeners();
    this.setupColumnSettings();
    this.updateTableHeaders(); // Update headers based on column settings
    this.createPaginationControls(); // Create pagination controls
    this.loadSignals(true);
    this.startAutoRefresh();
};

ETFSignalsManager.prototype.setupEventListeners = function () {
    var self = this;

    // Refresh button
    var refreshBtn = document.getElementById("refreshSignalsBtn");
    if (refreshBtn) {
        refreshBtn.addEventListener("click", function () {
            self.loadSignals(true);
        });
    }

    // Auto-refresh controls
    var autoRefreshToggle = document.getElementById("autoRefreshToggle");
    if (autoRefreshToggle) {
        autoRefreshToggle.addEventListener("change", function (e) {
            if (e.target.checked) {
                self.startAutoRefresh();
            } else {
                self.stopAutoRefresh();
            }
        });
    }

    // Search functionality
    var searchInput = document.getElementById("signalSearch");
    if (searchInput) {
        searchInput.addEventListener("input", function () {
            self.applyFilters();
        });
    }

    // Items per page selector - REMOVE
    // var itemsPerPageSelect = document.getElementById("itemsPerPage");
    // if (itemsPerPageSelect) {
    //     itemsPerPageSelect.addEventListener("change", function (e) {
    //         self.itemsPerPage = parseInt(e.target.value);
    //         self.currentPage = 1;
    //         self.renderSignalsTable();
    //         self.updatePagination();
    //     });
    // }
};

ETFSignalsManager.prototype.loadSignals = function (resetData) {
    var self = this;
    if (this.isLoading) return;

    if (resetData === true) {
        this.currentPage = 1;
        this.signals = [];
        this.filteredSignals = [];
    }

    this.isLoading = true;
    this.showLoadingState();

    var url = "/api/etf-signals-data";

    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.timeout = 45000; // 45 second timeout

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            self.isLoading = false;
            self.hideLoadingState();

            console.log("API Response Status:", xhr.status);
            console.log("API Response Text:", xhr.responseText);

            if (xhr.status === 200) {
                try {
                    var data = JSON.parse(xhr.responseText);
                    console.log("Parsed API data:", data);

                    if (data.success === false) {
                        // Handle API errors gracefully
                        self.showErrorMessage(
                            data.message ||
                                data.error ||
                                "Unknown error occurred",
                        );
                        self.signals = [];
                        self.filteredSignals = [];
                        self.renderSignalsTable();
                        self.updateCounts();
                        return;
                    }

                    if (data.data && Array.isArray(data.data)) {
                        // Load all signals at once (server-side handles pagination)
                        self.signals = data.data || [];
                        self.filteredSignals = self.signals.slice();

                        // Reset to first page when loading new data
                        if (resetData === true) {
                            self.currentPage = 1;
                            window.currentPage = 1;
                        }

                        // Update displayed signals based on current page
                        self.updateDisplayedSignals();
                        self.renderSignalsTable();
                        self.renderPaginationHTML();
                        self.updateCounts();
                        self.showSuccessMessage(
                            "Loaded " + self.signals.length + " signals",
                        );
                        console.log(
                            "Successfully loaded",
                            self.signals.length,
                            "signals",
                        );
                    } else if (data.error) {
                        throw new Error(data.error);
                    } else {
                        throw new Error("Invalid response format");
                    }
                } catch (parseError) {
                    console.error("Error parsing response:", parseError);
                    self.showErrorMessage("Error parsing server response");
                }
            } else {
                console.error("API request failed with status:", xhr.status);
                self.showErrorMessage(
                    "Failed to load signals: Server error " + xhr.status,
                );
            }
        }
    };

    xhr.ontimeout = function () {
        self.isLoading = false;
        self.hideLoadingState();
        console.error("API request timed out");
        self.showErrorMessage(
            "Request timed out - database connection slow. Please try again.",
        );
    };

    xhr.onerror = function () {
        self.isLoading = false;
        self.hideLoadingState();
        console.error("API request failed");
        self.showErrorMessage("Network error - please check your connection.");
    };

    xhr.send();
};

ETFSignalsManager.prototype.renderSignalsTable = function () {
    var tbody = document.getElementById("signalsTableBody") || document.getElementById("etfSignalsTableBody");
    if (!tbody) {
        console.error("Table body not found");
        return;
    }

    // Count visible columns for colspan
    var visibleColumnCount = 0;
    for (var i = 0; i < this.availableColumns.length; i++) {
        if (this.availableColumns[i].visible) visibleColumnCount++;
    }

    // Initialize displayedSignals if not done
    if (!this.displayedSignals || this.displayedSignals.length === 0) {
        if (this.signals && this.signals.length > 0) {
            this.updateDisplayedSignals();
        } else {
            tbody.innerHTML =
                '<tr><td colspan="' +
                visibleColumnCount +
                '" class="text-center text-muted">No ETF signals found</td></tr>';
            return;
        }
    }

    var self = this;
    tbody.innerHTML = "";

    for (var i = 0; i < this.displayedSignals.length; i++) {
        var signal = this.displayedSignals[i];
        var row = self.createSignalRow(signal);
        tbody.appendChild(row);
    }

    console.log("Rendered", this.displayedSignals.length, "signals in table");
};

ETFSignalsManager.prototype.createSignalRow = function (signal) {
    var row = document.createElement("tr");

    // Extract and format signal data
    var symbol = signal.etf || signal.symbol || "N/A";
    var entryPrice = parseFloat(signal.ep || signal.entry_price || 0);
    var currentPrice = parseFloat(
        signal.cmp || signal.current_price || entryPrice,
    );
    var quantity = parseInt(signal.qty || signal.quantity || 0);
    var pnl = parseFloat(signal.pl || signal.pnl || 0);
    var changePct = parseFloat(signal.change_pct || signal.pp || 0);
    var investment = parseFloat(
        signal.inv || signal.investment_amount || entryPrice * quantity,
    );
    var targetPrice = parseFloat(
        signal.tp || signal.target_price || entryPrice * 1.1,
    );
    var status = signal.status || "ACTIVE";
    var positionType =
        signal.position_type || (signal.pos === 1 ? "LONG" : "SHORT") || "LONG";

    // Parse percentage change from chan field (remove % symbol)
    var chanValue = signal.chan || "";
    if (chanValue && typeof chanValue === "string" && chanValue.includes("%")) {
        changePct = parseFloat(chanValue.replace("%", ""));
    }

    // Calculate values if not provided
    if (!changePct && entryPrice > 0) {
        changePct = ((currentPrice - entryPrice) / entryPrice) * 100;
    }

    if (!pnl && quantity > 0 && entryPrice > 0) {
        pnl = (currentPrice - entryPrice) * quantity;
    }

    // Create table cells based on visible columns
    var cells = "";
    for (var i = 0; i < this.availableColumns.length; i++) {
        var column = this.availableColumns[i];
        if (!column.visible) continue;

        var cellValue = "";
        var cellStyle = "";

        switch (column.key) {
            case "trade_signal_id":
                var tradeId = signal.trade_signal_id || signal.id || "N/A";
                cellValue =
                    '<span class="badge bg-secondary">' + tradeId + "</span>";
                break;
            case "etf":
                cellValue =
                    '<span class="fw-bold text-primary">' + symbol + "</span>";
                break;
            case "thirty":
                var thirtyValue = signal.thirty || signal.d30 || 0;
                if (typeof thirtyValue === "string") {
                    thirtyValue = parseFloat(thirtyValue) || 0;
                }
                cellValue =
                    thirtyValue > 0 ? "₹" + thirtyValue.toFixed(2) : "₹0.00";
                break;
            case "dh":
                var dhValue = signal.dh || signal.ch30 || "0.00%";
                if (typeof dhValue === "number") {
                    dhValue = dhValue.toFixed(2) + "%";
                }
                if (typeof dhValue === "string" && !dhValue.includes("%")) {
                    dhValue = parseFloat(dhValue).toFixed(2) + "%";
                }
                var percentage = parseFloat(dhValue.replace("%", ""));
                var bgColor = this.getGradientBackgroundColor(percentage);
                cellStyle = bgColor;
                cellValue =
                    '<span class="fw-bold text-white">' +
                    dhValue +
                    "</span>";
                break;
            case "date":
                cellValue = signal.date || "--";
                break;
            case "qty":
                cellValue =
                    '<span class="badge bg-info">' + quantity + "</span>";
                break;
            case "ep":
                cellValue = "₹" + entryPrice.toFixed(2);
                break;
            case "cmp":
                cellValue =
                    '<span class="cmp-value fw-bold" data-symbol="' +
                    symbol +
                    '">₹' +
                    currentPrice.toFixed(2) +
                    "</span>";
                break;
            case "chan":
                var chanDisplay = signal.chan || changePct.toFixed(2) + "%";
                var bgColor = this.getGradientBackgroundColor(changePct);
                cellStyle = bgColor;
                cellValue = '<span class="fw-bold">' + chanDisplay + "</span>";
                break;
            case "inv":
                cellValue = "₹" + investment.toFixed(0);
                break;
            case "tp":
                cellValue = "₹" + targetPrice.toFixed(2);
                break;
            case "tva":
                cellValue =
                    "₹" + (signal.tva || currentPrice * quantity).toFixed(2);
                break;
            case "tpr":
                // TPR = Target Price Return percentage = (Target Price - Entry Price) / Entry Price * 100
                var tpValue = parseFloat(signal.tp || targetPrice);
                var epValue = parseFloat(signal.ep || entryPrice);
                if (epValue > 0) {
                    var tprPercent = ((tpValue - epValue) / epValue) * 100;
                    cellValue = tprPercent.toFixed(2) + "%";
                } else {
                    cellValue = "--";
                }
                break;
            case "cpl":
                var plClass = pnl >= 0 ? "text-success" : "text-danger";
                cellValue =
                    '<span class="fw-bold ' +
                    plClass +
                    '">₹' +
                    pnl.toFixed(2) +
                    "</span>";
                break;
            case "ed":
                cellValue = signal.ed || "--";
                break;
            case "exp":
                cellValue = signal.exp || "--";
                break;
            case "pr":
                cellValue = signal.pr || "--";
                break;
            case "pp":
                cellValue = signal.pp || "--";
                break;
            case "iv":
                cellValue = signal.iv || "--";
                break;
            case "ip":
                cellValue = signal.ip || "--";
                break;
            case "nt":
                cellValue = signal.nt || "--";
                break;
            // case "qt":
            //     cellValue = signal.qt || quantity;
            //     break;
            case "seven":
                var sevenValue = signal.seven || signal.d7 || 0;
                if (typeof sevenValue === "string") {
                    sevenValue = parseFloat(sevenValue) || 0;
                }
                cellValue =
                    sevenValue > 0 ? "₹" + sevenValue.toFixed(2) : "₹0.00";
                break;
            case "ch":
                var chValue = signal.ch || signal.ch7 || "0.00%";
                if (typeof chValue === "number") {
                    chValue = chValue.toFixed(2) + "%";
                }
                if (typeof chValue === "string" && !chValue.includes("%")) {
                    chValue = parseFloat(chValue).toFixed(2) + "%";
                }
                var percentage = parseFloat(chValue.replace("%", ""));
                var bgColor = this.getGradientBackgroundColor(percentage);
                cellStyle = bgColor;
                cellValue =
                    '<span class="fw-bold text-white">' +
                    chValue +
                    "</span>";
                break;
            case "actions":
                var signalId = signal.trade_signal_id || signal.id || index;
                cellValue =
                    '<button class="btn btn-sm btn-success" onclick="addDeal(' +
                    signalId +
                    ')"><i class="fas fa-plus me-1"></i>Add Deal</button>';
                break;
            default:
                cellValue = "--";
        }

        cells += '<td style="' + cellStyle + '">' + cellValue + "</td>";
    }

    row.innerHTML = cells;
    return row;
};

// Gradient Background Color Function for %CH column
ETFSignalsManager.prototype.getGradientBackgroundColor = function (value) {
    var numValue = parseFloat(value);
    if (isNaN(numValue)) return "";

    var intensity = Math.min(Math.abs(numValue) / 5, 1); // Scale to 0-1, max at 5%
    var alpha = 0.4 + intensity * 0.6; // Alpha from 0.4 to 1.0 for better contrast

    if (numValue < 0) {
        // Red gradient for negative values - all with white text
        if (intensity <= 0.3) {
            // Light red for small negative values
            return (
                "background-color: rgba(220, 53, 69, " +
                alpha +
                "); color: #fff;"
            ); // Bootstrap danger color
        } else if (intensity <= 0.6) {
            // Medium red
            return (
                "background-color: rgba(198, 40, 40, " +
                alpha +
                "); color: #fff;"
            ); // Darker red
        } else {
            // Dark red for large negative values
            return (
                "background-color: rgba(139, 0, 0, " + alpha + "); color: #fff;"
            ); // Dark red
        }
    } else if (numValue > 0) {
        // Green gradient for positive values - all with white text
        if (intensity <= 0.3) {
            // Light green for small positive values
            return (
                "background-color: rgba(40, 167, 69, " +
                alpha +
                "); color: #fff;"
            ); // Bootstrap success color
        } else if (intensity <= 0.6) {
            // Medium green
            return (
                "background-color: rgba(34, 139, 34, " +
                alpha +
                "); color: #fff;"
            ); // Forest green
        } else {
            // Dark green for large positive values
            return (
                "background-color: rgba(0, 100, 0, " + alpha + "); color: #fff;"
            ); // Dark green
        }
    }
    return "";
};

ETFSignalsManager.prototype.updateTableHeaders = function () {
    var headerRow = document.getElementById("tableHeaders");
    if (!headerRow) return;

    headerRow.innerHTML = "";

    for (var i = 0; i < this.availableColumns.length; i++) {
        var column = this.availableColumns[i];
        if (column.visible) {
            var th = document.createElement("th");
            th.style.cursor = "pointer";
            th.title = column.label + " - Click to sort";
            if (column.key !== "actions") {
                th.setAttribute(
                    "onclick",
                    "sortSignalsByColumn('" + column.key + "')",
                );
                th.innerHTML =
                    column.label + ' <i class="fas fa-sort ms-1"></i>';
            } else {
                th.innerHTML = column.label;
            }
            headerRow.appendChild(th);
        }
    }
};

// Column Management Functions
ETFSignalsManager.prototype.loadColumnSettings = function () {
    var savedSettings = localStorage.getItem("etfSignalsColumnSettings");
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
            console.error("Error loading column settings:", e);
        }
    }
};

// Enhanced sorting functionality for ETF signals table
var sortState = {
    column: null,
    direction: "asc",
};

function sortTable(column) {
    var tbody = document.getElementById("etfSignalsTableBody");
    if (!tbody) return;

    var rows = Array.from(tbody.querySelectorAll("tr"));

    // Toggle sort direction
    if (sortState.column === column) {
        sortState.direction = sortState.direction === "asc" ? "desc" : "asc";
    } else {
        sortState.column = column;
        sortState.direction = "asc";
    }

    // Sort rows based on column
    rows.sort(function (a, b) {
        var aValue, bValue;

        switch (column) {
            case "symbol":
            case "etf":
                aValue = (
                    a.dataset.symbol ||
                    a.dataset.etf ||
                    ""
                ).toLowerCase();
                bValue = (
                    b.dataset.symbol ||
                    b.dataset.etf ||
                    ""
                ).toLowerCase();
                break;
            case "quantity":
            case "qty":
                aValue = parseFloat(a.dataset.quantity || a.dataset.qty) || 0;
                bValue = parseFloat(b.dataset.quantity || b.dataset.qty) || 0;
                break;
            case "entryPrice":
            case "ep":
                aValue = parseFloat(a.dataset.entryPrice || a.dataset.ep) || 0;
                bValue = parseFloat(b.dataset.entryPrice || b.dataset.ep) || 0;
                break;
            case "currentPrice":
            case "cmp":
                aValue =
                    parseFloat(a.dataset.currentPrice || a.dataset.cmp) || 0;
                bValue =
                    parseFloat(b.dataset.currentPrice || b.dataset.cmp) || 0;
                break;
            case "pnl":
            case "cpl":
                aValue = parseFloat(a.dataset.pnl || a.dataset.cpl) || 0;
                bValue = parseFloat(b.dataset.pnl || b.dataset.cpl) || 0;
                break;
            case "investment":
            case "inv":
                aValue = parseFloat(a.dataset.investment || a.dataset.inv) || 0;
                bValue = parseFloat(b.dataset.investment || b.dataset.inv) || 0;
                break;
            case "currentValue":
            case "tva":
                aValue =
                    parseFloat(a.dataset.currentValue || a.dataset.tva) || 0;
                bValue =
                    parseFloat(b.dataset.currentValue || b.dataset.tva) || 0;
                break;
            case "chanPercent":
            case "ch":
                aValue = parseFloat(a.dataset.chanPercent || a.dataset.ch) || 0;
                bValue = parseFloat(b.dataset.chanPercent || a.dataset.ch) || 0;
                break;
            case "targetPrice":
            case "tp":
                aValue = parseFloat(a.dataset.targetPrice || a.dataset.tp) || 0;
                bValue = parseFloat(b.dataset.targetPrice || b.dataset.tp) || 0;
                break;
            case "date":
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
        } else if (typeof aValue === "string") {
            result = aValue.localeCompare(bValue);
        } else {
            result = aValue - bValue;
        }

        return sortState.direction === "asc" ? result : -result;
    });

    // Update sort indicators
    updateSortIndicators(column, sortState.direction);

    // Rebuild table with sorted rows
    tbody.innerHTML = "";
    rows.forEach(function (row) {
        tbody.appendChild(row);
    });
}

function updateSortIndicators(activeColumn, direction) {
    // Hide all sort indicators
    var indicators = document.querySelectorAll('[id^="sort-"]');
    indicators.forEach(function (indicator) {
        indicator.classList.add("d-none");
    });

    // Show active indicator
    var activeIndicator = document.getElementById(
        "sort-" + activeColumn + "-" + direction,
    );
    if (activeIndicator) {
        activeIndicator.classList.remove("d-none");
    }

    // Update sort icons in headers
    var sortIcons = document.querySelectorAll(".sortable .fa-sort");
    sortIcons.forEach(function (icon) {
        icon.classList.remove("text-primary");
        icon.classList.add("text-muted");
    });

    var activeHeader = document.querySelector(
        '.sortable[onclick*="' + activeColumn + '"] .fa-sort',
    );
    if (activeHeader) {
        activeHeader.classList.remove("text-muted");
        activeHeader.classList.add("text-primary");
    }
}

// Legacy function for compatibility with existing onclick handlers
function sortSignalsByColumn(column) {
    sortTable(column);
}

ETFSignalsManager.prototype.saveColumnSettings = function () {
    var settings = {};
    for (var i = 0; i < this.availableColumns.length; i++) {
        var column = this.availableColumns[i];
        settings[column.key] = column.visible;
    }
    localStorage.setItem("etfSignalsColumnSettings", JSON.stringify(settings));
};

ETFSignalsManager.prototype.setupColumnSettings = function () {
    var self = this;
    var container = document.getElementById("columnCheckboxes");
    if (!container) return;

    container.innerHTML = "";

    for (var i = 0; i < this.availableColumns.length; i++) {
        var column = this.availableColumns[i];
        var colDiv = document.createElement("div");
        colDiv.className = "col-md-4 mb-2";

        var checkDiv = document.createElement("div");
        checkDiv.className = "form-check";

        var checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.className = "form-check-input";
        checkbox.id = "col_" + column.key;
        checkbox.checked = column.visible;
        checkbox.setAttribute("data-column", column.key);

        var label = document.createElement("label");
        label.className = "form-check-label text-light";
        label.setAttribute("for", checkbox.id);
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
        for (
            var i = 0;
            i < window.etfSignalsManager.availableColumns.length;
            i++
        ) {
            window.etfSignalsManager.availableColumns[i].visible = true;
        }

        // Update all checkboxes to checked
        var checkboxes = document.querySelectorAll(
            '#columnCheckboxes input[type="checkbox"]',
        );
        for (var i = 0; i < checkboxes.length; i++) {
            checkboxes[i].checked = true;
        }

        console.log("All columns selected");
    }
}

function resetDefaultColumns() {
    if (window.etfSignalsManager) {
        var defaultVisible = [
            "trade_signal_id",
            "etf",
            "thirty",
            "dh",
            "date",
            "qty",
            "ep",
            "cmp",
            "chan",
            "inv",
            "cpl",
            "ch",
            "actions",
        ];

        // Update column visibility
        for (
            var i = 0;
            i < window.etfSignalsManager.availableColumns.length;
            i++
        ) {
            var column = window.etfSignalsManager.availableColumns[i];
            column.visible = defaultVisible.indexOf(column.key) !== -1;
        }

        // Update checkboxes to match default settings
        var checkboxes = document.querySelectorAll(
            '#columnCheckboxes input[type="checkbox"]',
        );
        for (var i = 0; i < checkboxes.length; i++) {
            var columnKey = checkboxes[i].getAttribute("data-column");
            checkboxes[i].checked = defaultVisible.indexOf(columnKey) !== -1;
        }

        console.log("Reset to default columns");
    }
}

function applyColumnSettings() {
    console.log("Applying column settings...");
    if (window.etfSignalsManager) {
        var checkboxes = document.querySelectorAll(
            '#columnCheckboxes input[type="checkbox"]',
        );
        console.log("Found checkboxes:", checkboxes.length);

        // Update column visibility based on checkbox states
        for (var i = 0; i < checkboxes.length; i++) {
            var columnKey = checkboxes[i].getAttribute("data-column");
            var isChecked = checkboxes[i].checked;

            // Find and update the column in availableColumns array
            for (
                var j = 0;
                j < window.etfSignalsManager.availableColumns.length;
                j++
            ) {
                if (
                    window.etfSignalsManager.availableColumns[j].key ===
                    columnKey
                ) {
                    window.etfSignalsManager.availableColumns[j].visible =
                        isChecked;
                    console.log(
                        "Updated column",
                        columnKey,
                        "visible:",
                        isChecked,
                    );
                    break;
                }
            }
        }

        // Save settings and update display
        window.etfSignalsManager.saveColumnSettings();
        window.etfSignalsManager.updateTableHeaders();
        window.etfSignalsManager.renderSignalsTable();
        window.etfSignalsManager.renderPaginationHTML();

        // Close modal
        var modalElement = document.getElementById("columnSettingsModal");
        if (modalElement && window.bootstrap) {
            var modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) {
                modal.hide();
            } else {
                var newModal = new bootstrap.Modal(modalElement);
                newModal.hide();
            }
        }
        console.log("Column settings applied successfully");
    } else {
        console.error("ETF Signals Manager not found");
    }
}

ETFSignalsManager.prototype.updatePortfolioSummary = function (portfolio) {
    if (!portfolio) return;

    var elements = {
        totalPositions: portfolio.total_positions || 0,
        activePositions: portfolio.active_positions || 0,
        totalInvestment:
            "₹" + (portfolio.total_investment || 0).toLocaleString(),
        currentValue: "₹" + (portfolio.current_value || 0).toLocaleString(),
        totalPnl: "₹" + (portfolio.total_pnl || 0).toLocaleString(),
        returnPercent: (portfolio.return_percent || 0).toFixed(2) + "%",
    };

    for (var id in elements) {
        var element = document.getElementById(id);
        if (element) element.textContent = elements[id];
    }
};

ETFSignalsManager.prototype.applyFilters = function () {
    var searchInput = document.getElementById("signalSearch");
    var searchTerm = searchInput ? searchInput.value.toLowerCase() : "";

    var self = this;
    this.filteredSignals = this.signals.filter(function (signal) {
        var symbol = signal.etf || signal.symbol || "";
        var status = signal.status || "";
        return (
            symbol.toLowerCase().indexOf(searchTerm) !== -1 ||
            status.toLowerCase().indexOf(searchTerm) !== -1
        );
    });

    // Reset to first page after filtering
    this.currentPage = 1;
    this.updateDisplayedSignals();
    this.renderSignalsTable();
    this.renderPaginationHTML();
    this.updateCounts();
};

// Removing pagination and showing all data requires changes to updatePagination and related functions.
ETFSignalsManager.prototype.updateCounts = function () {
    // Update total count display
    var totalElement = document.getElementById("totalCount");
    var visibleElement = document.getElementById("visibleSignalsCount");
    var showingElement = document.getElementById("showingCount");

    if (totalElement) {
        totalElement.textContent = this.signals.length;    }
    if (visibleElement) {
        visibleElement.textContent = this.filteredSignals.length;
    }
    if (showingElement) {
        showingElement.textContent = this.filteredSignals.length;
    }
};

// Old loadMoreSignals function removed - replaced with pagination

ETFSignalsManager.prototype.updatePagination = function () {
    // No longer needed as pagination is removed
};

ETFSignalsManager.prototype.updatePaginationControls = function () {
    // No longer needed as pagination is removed
};

ETFSignalsManager.prototype.createPaginationControls = function () {
    var cardFooter = document.querySelector(".card-footer");
    if (!cardFooter) {
        // If card-footer doesn't exist, create it
        var card = document.querySelector(".card.bg-secondary");
        if (card) {
            cardFooter = document.createElement("div");
            cardFooter.className = "card-footer bg-dark border-0";
            card.appendChild(cardFooter);
        }
    }

    if (cardFooter) {
        var paginationHTML =
            '<div id="paginationContainer" class="d-flex justify-content-between align-items-center mt-3">' +
            '<div class="d-flex align-items-center">' +
            '<label for="itemsPerPage" class="form-label me-2 mb-0 text-light">Items per page:</label>' +
            '<select id="itemsPerPage" class="form-select form-select-sm bg-secondary text-light" style="width: auto;" onchange="changeItemsPerPage(this.value)">' +
            '<option value="10">10</option>' +
            '<option value="20" selected>20</option>' +
            '<option value="25">25</option>' +
            '<option value="50">50</option>' +
            '<option value="100">100</option>' +
            '</select>' +
            '</div>' +
            '<div id="paginationButtons" class="d-flex align-items-center">' +
            '</div>' +
            '<div class="text-muted small">' +
            'Showing <span id="startItem">1</span>-<span id="endItem">20</span> of <span id="totalItems">0</span> items' +
            '</div>' +
            '</div>';

        cardFooter.insertAdjacentHTML("beforeend", paginationHTML);
    }
};

ETFSignalsManager.prototype.renderPaginationHTML = function () {
    var buttonsContainer = document.getElementById("paginationButtons");
    var startItem = document.getElementById("startItem");
    var endItem = document.getElementById("endItem");
    var totalItems = document.getElementById("totalItems");
    var itemsPerPageSelect = document.getElementById("itemsPerPage");

    if (!buttonsContainer) return;

    // Update items per page selector
    if (itemsPerPageSelect) {
        itemsPerPageSelect.value = this.itemsPerPage;
    }

    // Update items display
    var startIndex = (this.currentPage - 1) * this.itemsPerPage + 1;
    var endIndex = Math.min(this.currentPage * this.itemsPerPage, this.filteredSignals.length);

    if (startItem) startItem.textContent = startIndex;
    if (endItem) endItem.textContent = endIndex;
    if (totalItems) totalItems.textContent = this.filteredSignals.length;

    // Generate pagination buttons
    var buttonsHTML = '';

    // Previous button
    buttonsHTML += '<button class="btn btn-sm btn-outline-light me-2" ' +
        (this.currentPage === 1 ? 'disabled' : '') + 
        ' onclick="goToPage(' + (this.currentPage - 1) + ')">' +
        '<i class="fas fa-chevron-left"></i></button>';

    // Page numbers
    var startPage = Math.max(1, this.currentPage - 2);
    var endPage = Math.min(this.totalPages, this.currentPage + 2);

    if (startPage > 1) {
        buttonsHTML += '<button class="btn btn-sm btn-outline-light me-1" onclick="goToPage(1)">1</button>';
        if (startPage > 2) {
            buttonsHTML += '<span class="me-1 text-light">...</span>';
        }
    }

    for (var i = startPage; i <= endPage; i++) {
        buttonsHTML += '<button class="btn btn-sm ' + 
            (i === this.currentPage ? 'btn-primary' : 'btn-outline-light') + 
            ' me-1" onclick="goToPage(' + i + ')">' + i + '</button>';
    }

    if (endPage < this.totalPages) {
        if (endPage < this.totalPages - 1) {
            buttonsHTML += '<span class="me-1 text-light">...</span>';
        }
        buttonsHTML += '<button class="btn btn-sm btn-outline-light me-1" onclick="goToPage(' + this.totalPages + ')">' + this.totalPages + '</button>';
    }

    // Next button
    buttonsHTML += '<button class="btn btn-sm btn-outline-light ms-1" ' +
        (this.currentPage === this.totalPages ? 'disabled' : '') + 
        ' onclick="goToPage(' + (this.currentPage + 1) + ')">' +
        '<i class="fas fa-chevron-right"></i></button>';

    buttonsContainer.innerHTML = buttonsHTML;
};

ETFSignalsManager.prototype.updateDisplayedSignals = function () {
    var startIndex = (this.currentPage - 1) * this.itemsPerPage;
    var endIndex = startIndex + this.itemsPerPage;
    this.displayedSignals = this.filteredSignals.slice(startIndex, endIndex);
    this.totalPages = Math.ceil(this.filteredSignals.length / this.itemsPerPage);

    // Ensure we don't exceed available pages
    if (this.currentPage > this.totalPages && this.totalPages > 0) {
        this.currentPage = this.totalPages;
        window.currentPage = this.currentPage;
        startIndex = (this.currentPage - 1) * this.itemsPerPage;
        endIndex = startIndex + this.itemsPerPage;
        this.displayedSignals = this.filteredSignals.slice(startIndex, endIndex);
    }

    console.log("updateDisplayedSignals:", {
        currentPage: this.currentPage,
        itemsPerPage: this.itemsPerPage,
        totalSignals: this.filteredSignals.length,
        startIndex: startIndex,
        endIndex: endIndex,
        displayedCount: this.displayedSignals.length,
        totalPages: this.totalPages
    });
};

ETFSignalsManager.prototype.goToPage = function (pageNumber) {
    if (pageNumber < 1 || pageNumber > this.totalPages) return;
    this.currentPage = pageNumber;
    window.currentPage = this.currentPage; // Update global variable
    this.updateDisplayedSignals();
    this.renderSignalsTable();
    this.renderPaginationHTML();
};

ETFSignalsManager.prototype.changeItemsPerPage = function (newItemsPerPage) {
    // No longer needed as pagination is removed
};

ETFSignalsManager.prototype.applyFilters = function () {
    var searchInput = document.getElementById("signalSearch");
    var searchTerm = searchInput ? searchInput.value.toLowerCase() : "";

    var self = this;
    this.filteredSignals = this.signals.filter(function (signal) {
        var symbol = signal.etf || signal.symbol || "";
        var status = signal.status || "";
        return (
            symbol.toLowerCase().indexOf(searchTerm) !== -1 ||
            status.toLowerCase().indexOf(searchTerm) !== -1
        );
    });

    // Reset to first page after filtering
    this.currentPage = 1;
    this.updateDisplayedSignals();
    this.renderSignalsTable();
    this.renderPaginationHTML();
    this.updateCounts();
};

ETFSignalsManager.prototype.init = function () {
    console.log("ETF Signals Manager initialized");
    this.loadColumnSettings();
    this.setupEventListeners();
    this.setupColumnSettings();
    this.updateTableHeaders(); // Update headers based on column settings
    this.createPaginationControls(); // Create pagination controls (but it will be empty)
    this.loadSignals(true);
    this.startAutoRefresh();
};

ETFSignalsManager.prototype.saveColumnSettings = function () {
    var settings = {};
    for (var i = 0; i < this.availableColumns.length; i++) {
        var column = this.availableColumns[i];
        settings[column.key] = column.visible;
    }
    localStorage.setItem("etfSignalsColumnSettings", JSON.stringify(settings));
};

// Add the following CSS to your stylesheet or in a <style> tag in the HTML:
/* Add this CSS to your stylesheet or in a &lt;style&gt; tag in the HTML */
/* Ensures the table fills its container and handles overflow */
#etfSignalsTableContainer {
    width: 100%;
    overflow-x: auto; /* Horizontal scroll */
    position: relative; /* Required for positioning the scrollbars */
}

/* Style for the table itself */
#etfSignalsTable {
    width: 100%; /* Ensure the table takes up the full width */
    border-collapse: collapse; /* Collapses borders between cells */
    table-layout: fixed; /* Ensures consistent column widths */
}

/* Basic table cell styling for readability */
#etfSignalsTable th,
#etfSignalsTable td {
    padding: 8px;
    border: 1px solid #ddd; /* Light gray border */
    text-align: left;
    white-space: nowrap; /* Prevents text from wrapping, forces scrolling */
}

/* Style for table headers */
#etfSignalsTable th {
    background-color: #343a40; /* Dark background for headers */
    color: white;
    font-weight: bold;
}

/* Optional: Zebra striping for improved readability */
#etfSignalsTable tbody tr:nth-child(odd) {
    background-color: #212529; /* Darker background for alternating rows */
}

/* Custom scrollbar styles */
/* WebKit (Chrome, Safari) */
#etfSignalsTableContainer::-webkit-scrollbar {
    width: 10px;
    height: 10px; /* For horizontal scrollbar */
}

#etfSignalsTableContainer::-webkit-scrollbar-thumb {
    background: #6c757d; /* Bootstrap's secondary color */
    border-radius: 5px;
}

#etfSignalsTableContainer::-webkit-scrollbar-thumb:hover {
    background: #5a6268;
}

/* Firefox */
/* Note: Firefox scrollbar styling is limited and requires more complex CSS */
/* You can use JavaScript libraries for more advanced styling */
#etfSignalsTableContainer {
    scrollbar-width: thin;
    scrollbar-color: #6c757d #212529;
}