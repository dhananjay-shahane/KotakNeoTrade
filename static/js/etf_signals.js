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

    // Column visibility settings - using compact widths like deals page
    this.availableColumns = [
        { key: "trade_signal_id", label: "ID", width: "50px", visible: true },
        { key: "etf", label: "SYMBOL", width: "80px", visible: true },
        { key: "seven", label: "7D", width: "50px", visible: true },
        { key: "ch", label: "7D%", width: "50px", visible: true },
        { key: "thirty", label: "30D", width: "50px", visible: true },
        { key: "dh", label: "30D%", width: "50px", visible: true },
        { key: "date", label: "DATE", width: "80px", visible: true },
        { key: "qty", label: "QTY", width: "60px", visible: true },
        { key: "ep", label: "EP", width: "70px", visible: true },
        { key: "cmp", label: "CMP", width: "70px", visible: true },
        { key: "chan", label: "%CHAN", width: "60px", visible: true },
        { key: "inv", label: "INV.", width: "70px", visible: true },
        { key: "tp", label: "TP", width: "60px", visible: true },
        { key: "tpr", label: "TPR", width: "70px", visible: true },
        { key: "tva", label: "TVA", width: "70px", visible: true },
        { key: "cpl", label: "CPL", width: "60px", visible: true },
        { key: "ed", label: "ED", width: "70px", visible: false },
        { key: "exp", label: "EXP", width: "70px", visible: false },
        { key: "pr", label: "PR", width: "80px", visible: false },
        { key: "pp", label: "PP", width: "50px", visible: false },
        { key: "iv", label: "IV", width: "60px", visible: false },
        { key: "ip", label: "IP", width: "60px", visible: false },
        { key: "actions", label: "ACTION", width: "80px", visible: true },
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
    this.generateDynamicHeaders(); // Generate dynamic headers with sorting
    this.createPaginationControls(); // Create pagination controls

    // Show skeleton loading while data loads
    this.showLoadingState();

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
            clearTimeout(self.searchTimeout);
            self.searchTimeout = setTimeout(function() {
                self.applyFilters();
            }, 300);
        });

        searchInput.addEventListener("keypress", function(e) {
            if (e.key === "Enter") {
                self.applyFilters();
            }
        });
    }


    // Remove filter dropdowns - keeping only search functionality

    // Items per page selector
    var itemsPerPageSelect = document.getElementById("itemsPerPage");
    if (itemsPerPageSelect) {
        itemsPerPageSelect.addEventListener("change", function (e) {
            self.itemsPerPage = parseInt(e.target.value);
            self.currentPage = 1;
            self.renderSignalsTable();
            self.updatePagination();
        });
    }
};

// Generate dynamic table headers with sorting functionality
ETFSignalsManager.prototype.generateDynamicHeaders = function () {
    var self = this;
    var headersRow = document.getElementById("tableHeaders");
    if (!headersRow) {
        console.error("Table headers row not found");
        return;
    }

    // Clear existing headers
    headersRow.innerHTML = "";

    // Generate headers for visible columns
    for (var i = 0; i < this.availableColumns.length; i++) {
        var column = this.availableColumns[i];
        if (!column.visible) continue;

        var th = document.createElement("th");
        th.style.width = column.width;
        th.className = "text-center";
        th.style.backgroundColor = "var(--secondary-color)";
        th.style.color = "var(--text-primary)";
        th.style.fontWeight = "600";
        th.style.fontSize = "0.7rem";
        th.style.padding = "6px 3px";
        th.style.border = "1px solid var(--border-color)";
        th.style.position = "sticky";
        th.style.top = "0";
        th.style.zIndex = "10";
        th.style.whiteSpace = "nowrap";
        th.style.cursor = "pointer";

        // Add sorting functionality for most columns
        if (column.key !== "actions") {
            th.onclick = (function (columnKey) {
                return function () {
                    self.sortSignalsByColumn(columnKey);
                };
            })(column.key);
            th.innerHTML = column.label + ' <i class="fas fa-sort ms-1"></i>';
            th.title = self.getColumnTooltip(column.key) + " - Click to sort";
        } else {
            th.innerHTML = column.label;
            th.title = self.getColumnTooltip(column.key);
            th.style.cursor = "default";
        }

        headersRow.appendChild(th);
    }

    console.log("Dynamic headers generated for", this.availableColumns.filter(c => c.visible).length, "visible columns");
};

// Add sorting functionality for signals
ETFSignalsManager.prototype.sortSignalsByColumn = function (columnKey) {
    var self = this;

    // Toggle sort direction if clicking the same column
    if (this.sortField === columnKey) {
        this.sortDirection = this.sortDirection === "asc" ? "desc" : "asc";
    } else {
        this.sortField = columnKey;
        this.sortDirection = "asc";
    }

    // Sort the filtered signals
    this.filteredSignals.sort(function (a, b) {
        var aValue = self.getSortValue(a, columnKey);
        var bValue = self.getSortValue(b, columnKey);

        // Handle numeric comparisons
        if (!isNaN(aValue) && !isNaN(bValue)) {
            return self.sortDirection === "asc" ? aValue - bValue : bValue - aValue;
        }

        // Handle string comparisons
        aValue = String(aValue).toLowerCase();
        bValue = String(bValue).toLowerCase();

        if (aValue < bValue) return self.sortDirection === "asc" ? -1 : 1;
        if (aValue > bValue) return self.sortDirection === "asc" ? 1 : -1;
        return 0;
    });

    // Update displayed signals and re-render
    this.updateDisplayedSignals();
    this.renderSignalsTable();
    this.updateSortIcons(columnKey);

    console.log("Sorted signals by", columnKey, "in", this.sortDirection, "order");
};

// Get sortable value from signal object
ETFSignalsManager.prototype.getSortValue = function (signal, columnKey) {
    switch (columnKey) {
        case "trade_signal_id":
            return parseInt(signal.ID || signal.trade_signal_id || signal.id || 0);
        case "etf":
            return signal.Symbol || signal.etf || signal.symbol || "";
        case "seven":
            return parseFloat(signal["7D"] || signal.seven || 0);
        case "ch":
            var chValue = signal["7D%"] || signal.ch || "0%";
            return parseFloat(String(chValue).replace("%", ""));
        case "thirty":
            return parseFloat(signal["30D"] || signal.thirty || 0);
        case "dh":
            var dhValue = signal["30D%"] || signal.dh || "0%";
            return parseFloat(String(dhValue).replace("%", ""));
        case "date":
            return signal.DATE || signal.date || "";
        case "qty":
            return parseInt(signal.QTY || signal.qty || 0);
        case "ep":
            return parseFloat(signal.EP || signal.ep || 0);
        case "cmp":
            return parseFloat(signal.CMP || signal.cmp || 0);
        case "chan":
            var chanValue = signal["%CHAN"] || signal.chan || "0%";
            return parseFloat(String(chanValue).replace("%", ""));
        case "inv":
            return parseFloat(signal.INV || signal.inv || 0);
        case "tp":
            return parseFloat(signal.TP || signal.tp || 0);
        case "cpl":
            return parseFloat(signal.CPL || signal.pl || 0);
        default:
            return signal[columnKey] || "";
    }
};

// Update sort icons in headers
ETFSignalsManager.prototype.updateSortIcons = function (sortedColumn) {
    var headers = document.querySelectorAll("#tableHeaders th");
    for (var i = 0; i < headers.length; i++) {
        var th = headers[i];
        var icon = th.querySelector("i");
        if (icon) {
            // Reset all icons to default sort
            icon.className = "fas fa-sort ms-1";
        }
    }

    // Update the sorted column icon
    var sortedHeader = Array.from(headers).find(function (th) {
        return th.onclick && th.onclick.toString().includes(sortedColumn);
    });

    if (sortedHeader) {
        var icon = sortedHeader.querySelector("i");
        if (icon) {
            icon.className = this.sortDirection === "asc" 
                ? "fas fa-sort-up ms-1" 
                : "fas fa-sort-down ms-1";
        }
    }
};

// Get column tooltip for better UX
ETFSignalsManager.prototype.getColumnTooltip = function (columnKey) {
    var tooltips = {
        trade_signal_id: "Trade Signal ID",
        etf: "ETF Symbol", 
        seven: "7 Day Performance",
        ch: "7 Day Change Percentage",
        thirty: "30 Day Performance",
        dh: "30 Day Change Percentage",
        date: "Entry Date",
        qty: "Quantity",
        ep: "Entry Price",
        cmp: "Current Market Price",
        chan: "Percentage Change",
        inv: "Investment Amount",
        tp: "Target Price",
        tpr: "Target Profit Return",
        tva: "Target Value Amount",
        cpl: "Current Profit/Loss",
        ed: "Exit Date",
        exp: "Expiry Date",
        pr: "Price Range",
        pp: "Performance Points",
        iv: "Implied Volatility",
        ip: "Intraday Performance",
        actions: "Available Actions"
    };
    return tooltips[columnKey] || columnKey.toUpperCase();
};

ETFSignalsManager.prototype.loadSignals = function (resetData) {
    var self = this;
    if (this.isLoading) {
        console.log("Already loading signals, skipping duplicate request");
        return;
    }

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
                        self.updatePagination();

                        // Hide loading state even on error
                        self.hideLoadingState();
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
                        self.updatePagination();

                        // Hide loading state
                        self.hideLoadingState();

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
    var tbody =
        document.getElementById("signalsTableBody") ||
        document.getElementById("etfSignalsTableBody");
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

    // Extract and format signal data using new format from get_all_trade_metrics()
    var symbol = signal.Symbol || signal.etf || signal.symbol || "N/A";
    var entryPrice = parseFloat(
        signal.EP || signal.ep || signal.entry_price || 0,
    );
    var currentPrice = parseFloat(
        signal.CMP || signal.cmp || signal.current_price || entryPrice,
    );
    var quantity = parseInt(signal.QTY || signal.qty || signal.quantity || 0);
    var pnl = parseFloat(signal.CPL || signal.pl || signal.pnl || 0);
    var changePct = parseFloat(signal.change_pct || signal.pp || 0);
    var investment = parseFloat(
        signal.INV ||
            signal.inv ||
            signal.investment_amount ||
            entryPrice * quantity,
    );
    var targetPrice = parseFloat(
        signal.TP || signal.tp || signal.target_price || entryPrice * 1.1,
    );
    var status = signal.status || "ACTIVE";
    var positionType =
        signal.position_type || (signal.pos === 1 ? "LONG" : "SHORT") || "LONG";

    // Parse percentage change from %CHAN field (remove % symbol)
    var chanValue = signal["%CHAN"] || signal.chan || "";
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
                var tradeId =
                    signal.ID || signal.trade_signal_id || signal.id || "N/A";
                cellValue =
                    '<span class="badge bg-secondary">' + tradeId + "</span>";
                break;
            case "etf":
                cellValue =
                    '<span class="fw-bold text-primary">' + symbol + "</span>";
                break;
            case "thirty":
                var thirtyValue =
                    signal["30D"] || signal.thirty || signal.d30 || 0;
                if (typeof thirtyValue === "string") {
                    thirtyValue = parseFloat(thirtyValue) || 0;
                }
                cellValue =
                    thirtyValue > 0 ? "₹" + thirtyValue.toFixed(2) : "₹0.00";
                break;
            case "dh":
                var dhValue =
                    signal["30D%"] || signal.dh || signal.ch30 || "0.00%";
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
                    '<span class="fw-bold text-white">' + dhValue + "</span>";
                break;
            case "date":
                cellValue = signal.DATE || signal.date || "--";
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
                var chanDisplay =
                    signal["%CHAN"] ||
                    signal.chan ||
                    changePct.toFixed(2) + "%";
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
                var ivValue = signal.IV || signal.iv || 0;
                if (typeof ivValue === "number" && ivValue > 0) {
                    cellValue = "₹" + parseFloat(ivValue).toFixed(2);
                } else {
                    cellValue = "--";
                }
                break;
            case "ip":
                var ipValue = signal.IP || signal.ip || 0;
                if (typeof ipValue === "number" && ipValue > 0) {
                    cellValue = "₹" + parseFloat(ipValue).toFixed(2);
                } else {
                    cellValue = "--";
                }
                break;
            case "nt":
                cellValue = signal.nt || "--";
                break;
            // case "qt":
            //     cellValue = signal.qt || quantity;
            //     break;
            case "seven":
                var sevenValue = signal["7D"] || signal.seven || signal.d7 || 0;
                if (typeof sevenValue === "string") {
                    sevenValue = parseFloat(sevenValue) || 0;
                }
                cellValue =
                    sevenValue > 0 ? "₹" + sevenValue.toFixed(2) : "₹0.00";
                break;
            case "ch":
                var chValue =
                    signal["7D%"] || signal.ch || signal.ch7 || "0.00%";
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
                    '<span class="fw-bold text-white">' + chValue + "</span>";
                break;
            case "actions":
                var signalId = signal.ID || signal.id || signal.trade_signal_id;
                cellValue =
                    '<button class="btn btn-sm btn-success add-deal-btn" onclick="addDeal(' +
                    signalId +
                    ')" data-signal-id="' +
                    signalId +
                    '"><i class="fas fa-plus me-1"></i>Add Deal</button>';
                break;
            default:
                cellValue = "--";
        }

        cells += '<td class="text-center" style="padding: 4px 3px; border: 1px solid var(--border-color); font-size: 0.75rem; ' + cellStyle + '">' + cellValue + "</td>";
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
                bValue = parseFloat(b.dataset.chanPercent || b.dataset.ch) || 0;
                break;
            default:
                aValue = a.textContent.toLowerCase();
                bValue = b.textContent.toLowerCase();
        }

        if (sortState.direction === "asc") {
            return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
        } else {
            return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
        }
    });

    // Clear and re-populate tbody
    tbody.innerHTML = "";
    rows.forEach(function(row) {
        tbody.appendChild(row);
    });

    // Update sort icons
    updateSortIcons(column);
}

function updateSortIcons(activeColumn) {
    // Remove all sort icons
    document.querySelectorAll("th[onclick] i").forEach(function(icon) {
        icon.className = "fas fa-sort ms-1";
    });

    // Add active sort icon
    var activeHeader = document.querySelector('th[onclick*="' + activeColumn + '"]');
    if (activeHeader) {
        var icon = activeHeader.querySelector("i");
        if (icon) {
            icon.className = sortState.direction === "asc" ? "fas fa-sort-up ms-1" : "fas fa-sort-down ms-1";
        }
    }
}

// Pagination functions
ETFSignalsManager.prototype.createPaginationControls = function() {
    // Pagination controls are handled in the footer
    this.updatePagination();
};

ETFSignalsManager.prototype.updatePagination = function() {
    this.totalPages = Math.ceil(this.filteredSignals.length / this.itemsPerPage);
    
    // Update pagination info
    var showingCount = document.getElementById("showingCount");
    var totalCount = document.getElementById("totalCount");
    var visibleSignalsCount = document.getElementById("visibleSignalsCount");
    
    if (showingCount) {
        showingCount.textContent = this.displayedSignals.length;
    }
    if (totalCount) {
        totalCount.textContent = this.signals.length;
    }
    if (visibleSignalsCount) {
        visibleSignalsCount.textContent = this.filteredSignals.length;
    }
};

ETFSignalsManager.prototype.updateDisplayedSignals = function() {
    var startIndex = (this.currentPage - 1) * this.itemsPerPage;
    var endIndex = startIndex + this.itemsPerPage;
    this.displayedSignals = this.filteredSignals.slice(startIndex, endIndex);
};

// Filter and search functionality
ETFSignalsManager.prototype.applyFilters = function() {
    var searchTerm = "";
    var searchInput = document.getElementById("signalSearch");
    if (searchInput) {
        searchTerm = searchInput.value.toLowerCase().trim();
    }

    // Reset to all signals
    this.filteredSignals = this.signals.slice();

    // Apply search filter
    if (searchTerm) {
        this.filteredSignals = this.filteredSignals.filter(function(signal) {
            var symbol = (signal.Symbol || signal.etf || signal.symbol || "").toLowerCase();
            var id = String(signal.ID || signal.trade_signal_id || signal.id || "").toLowerCase();
            return symbol.includes(searchTerm) || id.includes(searchTerm);
        });
    }

    // Reset to first page
    this.currentPage = 1;
    this.updateDisplayedSignals();
    this.renderSignalsTable();
    this.updatePagination();
};

// Auto-refresh functionality
ETFSignalsManager.prototype.startAutoRefresh = function() {
    this.stopAutoRefresh();
    var self = this;
    this.refreshInterval = setInterval(function() {
        self.loadSignals(false);
    }, 300000); // 5 minutes
};

ETFSignalsManager.prototype.stopAutoRefresh = function() {
    if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
        this.refreshInterval = null;
    }
};

// Column settings functionality
ETFSignalsManager.prototype.setupColumnSettings = function() {
    var self = this;
    var columnCheckboxes = document.getElementById("columnCheckboxes");
    if (!columnCheckboxes) return;

    columnCheckboxes.innerHTML = "";
    
    for (var i = 0; i < this.availableColumns.length; i++) {
        var column = this.availableColumns[i];
        var colDiv = document.createElement("div");
        colDiv.className = "col-md-4 mb-2";
        
        var checkboxDiv = document.createElement("div");
        checkboxDiv.className = "form-check";
        
        var checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.className = "form-check-input";
        checkbox.id = "col_" + column.key;
        checkbox.checked = column.visible;
        checkbox.setAttribute("data-column", column.key);
        
        var label = document.createElement("label");
        label.className = "form-check-label text-light";
        label.setAttribute("for", "col_" + column.key);
        label.textContent = column.label;
        
        checkboxDiv.appendChild(checkbox);
        checkboxDiv.appendChild(label);
        colDiv.appendChild(checkboxDiv);
        columnCheckboxes.appendChild(colDiv);
    }
};

// Global functions for UI interactions
function refreshSignals() {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.loadSignals(true);
    }
}

function exportSignals() {
    if (window.etfSignalsManager && window.etfSignalsManager.signals.length > 0) {
        // Create CSV content
        var csvContent = "data:text/csv;charset=utf-8,";
        
        // Add headers
        var headers = window.etfSignalsManager.availableColumns
            .filter(col => col.visible)
            .map(col => col.label);
        csvContent += headers.join(",") + "\n";
        
        // Add data rows
        window.etfSignalsManager.displayedSignals.forEach(function(signal) {
            var row = [];
            window.etfSignalsManager.availableColumns.forEach(function(col) {
                if (col.visible) {
                    var value = signal[col.key] || "";
                    row.push('"' + String(value).replace(/"/g, '""') + '"');
                }
            });
            csvContent += row.join(",") + "\n";
        });
        
        // Download file
        var encodedUri = encodeURI(csvContent);
        var link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", "etf_signals_" + new Date().toISOString().split('T')[0] + ".csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

function selectAllColumns() {
    var checkboxes = document.querySelectorAll('#columnCheckboxes input[type="checkbox"]');
    checkboxes.forEach(function(checkbox) {
        checkbox.checked = true;
    });
}

function resetDefaultColumns() {
    var checkboxes = document.querySelectorAll('#columnCheckboxes input[type="checkbox"]');
    checkboxes.forEach(function(checkbox) {
        var columnKey = checkbox.getAttribute("data-column");
        var column = window.etfSignalsManager.availableColumns.find(c => c.key === columnKey);
        if (column) {
            // Set to default visibility
            checkbox.checked = ["trade_signal_id", "etf", "seven", "ch", "thirty", "dh", "date", "qty", "ep", "cmp", "chan", "inv", "tp", "tpr", "tva", "cpl", "actions"].includes(columnKey);
        }
    });
}

function applyColumnSettings() {
    var checkboxes = document.querySelectorAll('#columnCheckboxes input[type="checkbox"]');
    checkboxes.forEach(function(checkbox) {
        var columnKey = checkbox.getAttribute("data-column");
        var column = window.etfSignalsManager.availableColumns.find(c => c.key === columnKey);
        if (column) {
            column.visible = checkbox.checked;
        }
    });
    
    // Save settings
    var settings = {};
    window.etfSignalsManager.availableColumns.forEach(function(col) {
        settings[col.key] = col.visible;
    });
    localStorage.setItem("etfSignalsColumnSettings", JSON.stringify(settings));
    
    // Regenerate table
    window.etfSignalsManager.generateDynamicHeaders();
    window.etfSignalsManager.renderSignalsTable();
    
    // Close modal
    var modal = bootstrap.Modal.getInstance(document.getElementById('columnSettingsModal'));
    if (modal) {
        modal.hide();
    }
}

function clearFilters() {
    // Clear all filter inputs
    document.getElementById("positionTypeFilter").value = "";
    document.getElementById("modalStatusFilter").value = "";
    document.getElementById("modalSymbolFilter").value = "";
    document.getElementById("minInvestmentFilter").value = "";
    document.getElementById("maxInvestmentFilter").value = "";
    document.getElementById("minPnlFilter").value = "";
    document.getElementById("maxPnlFilter").value = "";
    document.getElementById("signalSearch").value = "";
}

function applyFilters() {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.applyFilters();
    }
}

function addDeal(signalId) {
    // Implementation for adding deal from signal
    console.log("Adding deal for signal:", signalId);
    // This would typically open a modal or redirect to add deal page
}

// Loading and error state management
ETFSignalsManager.prototype.showLoadingState = function() {
    var tbody = document.getElementById("signalsTableBody");
    if (tbody) {
        var visibleColumnCount = this.availableColumns.filter(col => col.visible).length;
        tbody.innerHTML = '<tr><td colspan="' + visibleColumnCount + '" class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></td></tr>';
    }
};

ETFSignalsManager.prototype.hideLoadingState = function() {
    // Loading state will be hidden when table is rendered
};

ETFSignalsManager.prototype.showErrorMessage = function(message) {
    console.error("ETF Signals Error:", message);
    // You could add toast notifications here
};

ETFSignalsManager.prototype.showSuccessMessage = function(message) {
    console.log("ETF Signals Success:", message);
    // You could add toast notifications here
};

// Initialize the ETF Signals Manager
window.etfSignalsManager = new ETFSignalsManager();
window.currentPage = 1;