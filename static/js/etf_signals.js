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

    // Date filtering
    this.dateFilters = {
        startDate: null,
        endDate: null,
        quickFilter: null
    };

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
    this.setupNewFeatures();
    this.loadPerformanceAnalysis(); // Load real performance data
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

        // Add sorting functionality for most columns
        if (column.key !== "actions") {
            th.className += " sortable-header";
            
            // Check if this column is currently being sorted
            var isActiveSort = (self.sortField === column.key);
            if (isActiveSort) {
                th.className += " active";
            }
            
            th.onclick = (function (columnKey) {
                return function () {
                    self.sortSignalsByColumn(columnKey);
                };
            })(column.key);
            
            var sortIcon = '';
            if (isActiveSort) {
                sortIcon = self.sortDirection === "asc" 
                    ? '<i class="fas fa-sort-up sort-icon sort-asc"></i>'
                    : '<i class="fas fa-sort-down sort-icon sort-desc"></i>';
            } else {
                sortIcon = '<i class="fas fa-sort sort-icon"></i>';
            }
            
            th.innerHTML = column.label + ' ' + sortIcon;
            th.title = self.getColumnTooltip(column.key) + " - Click to sort";
        } else {
            th.innerHTML = column.label;
            th.title = self.getColumnTooltip(column.key);
            th.style.cursor = "default";
        }

        headersRow.appendChild(th);
    }

    console.log(
        "Dynamic headers generated for",
        this.availableColumns.filter((c) => c.visible).length,
        "visible columns",
    );
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
            return self.sortDirection === "asc"
                ? aValue - bValue
                : bValue - aValue;
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
    this.generateDynamicHeaders(); // Refresh headers to show active sort state

    console.log(
        "Sorted signals by",
        columnKey,
        "in",
        this.sortDirection,
        "order",
    );
};

// Get sortable value from signal object
ETFSignalsManager.prototype.getSortValue = function (signal, columnKey) {
    switch (columnKey) {
        case "trade_signal_id":
            return parseInt(
                signal.ID || signal.trade_signal_id || signal.id || 0,
            );
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
            icon.className =
                this.sortDirection === "asc"
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
        actions: "Available Actions",
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

                        // Calculate performance metrics and advanced analytics after data is loaded
                        self.calculatePerformanceMetrics();
                        self.calculateAdvancedAnalytics();

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

        cells +=
            '<td class="text-center" style="padding: 4px 3px; border: 1px solid var(--border-color); font-size: 0.75rem; ' +
            cellStyle +
            '">' +
            cellValue +
            "</td>";
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
        window.etfSignalsManager.updatePagination();

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
            "yP" + (portfolio.total_investment || 0).toLocaleString(),
        currentValue: "₹" + (portfolio.current_value || 0).toLocaleString(),
        totalPnl: "₹" + (portfolio.total_pnl || 0).toLocaleString(),
        returnPercent: (portfolio.return_percent || 0).toFixed(2) + "%",
    };

    for (var id in elements) {
        var element = document.getElementById(id);
        if (element) element.textContent = elements[id];
    }
};

// Add applySearch method for search functionality
ETFSignalsManager.prototype.applySearch = function () {
    var searchInput = document.getElementById("signalSearchInput");
    var searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : "";

    if (!searchTerm) {
        // Reset to show all signals when search is empty
        this.filteredSignals = this.signals.slice();
    } else {
        // Filter signals based on search term
        var self = this;
        this.filteredSignals = this.signals.filter(function (signal) {
            var symbol = (
                signal.Symbol ||
                signal.etf ||
                signal.symbol ||
                ""
            ).toLowerCase();
            var status = (signal.status || "ACTIVE").toLowerCase();
            var date = (signal.DATE || signal.date || "")
                .toString()
                .toLowerCase();
            var ep = (signal.EP || signal.ep || "").toString().toLowerCase();
            var cmp = (signal.CMP || signal.cmp || "").toString().toLowerCase();
            var qty = (signal.QTY || signal.qty || "").toString().toLowerCase();
            var signalId = (signal.signal_id || signal.id || "")
                .toString()
                .toLowerCase();

            return (
                symbol.includes(searchTerm) ||
                status.includes(searchTerm) ||
                date.includes(searchTerm) ||
                ep.includes(searchTerm) ||
                cmp.includes(searchTerm) ||
                qty.includes(searchTerm) ||
                signalId.includes(searchTerm)
            );
        });
    }

    // Reset to first page and update display
    this.currentPage = 1;
    this.updateDisplayedSignals();
    this.renderSignalsTable();
    this.updatePagination();
};

ETFSignalsManager.prototype.applyFilters = function () {
    var searchInput = document.getElementById("signalSearchInput");
    var modalStatusFilter = document.getElementById("modalStatusFilter");
    var modalSymbolFilter = document.getElementById("modalSymbolFilter");
    var positionTypeFilter = document.getElementById("positionTypeFilter");
    var minInvestmentFilter = document.getElementById("minInvestmentFilter");
    var maxInvestmentFilter = document.getElementById("maxInvestmentFilter");
    var minPnlFilter = document.getElementById("minPnlFilter");
    var maxPnlFilter = document.getElementById("maxPnlFilter");

    var searchTerm = searchInput ? searchInput.value.toLowerCase() : "";
    var modalStatusValue = modalStatusFilter ? modalStatusFilter.value : "";
    var modalSymbolValue = modalSymbolFilter
        ? modalSymbolFilter.value.toLowerCase()
        : "";
    var positionTypeValue = positionTypeFilter ? positionTypeFilter.value : "";
    var minInvestment = minInvestmentFilter
        ? parseFloat(minInvestmentFilter.value) || 0
        : 0;
    var maxInvestment = maxInvestmentFilter
        ? parseFloat(maxInvestmentFilter.value) || Infinity
        : Infinity;
    var minPnl = minPnlFilter
        ? parseFloat(minPnlFilter.value) || -Infinity
        : -Infinity;
    var maxPnl = maxPnlFilter
        ? parseFloat(maxPnlFilter.value) || Infinity
        : Infinity;

    var self = this;
    this.filteredSignals = this.signals.filter(function (signal) {
        var symbol = (
            signal.Symbol ||
            signal.etf ||
            signal.symbol ||
            ""
        ).toLowerCase();
        var status = (signal.status || "ACTIVE").toUpperCase();
        var investment = parseFloat(signal.INV || signal.inv || 0);
        var pnl = parseFloat(signal.CPL || signal.cpl || signal.pl || 0);
        var positionType = signal.pos > 0 ? "BUY" : "SELL";

        // Enhanced search term filter - search across multiple fields
        if (searchTerm) {
            var searchFields = [
                symbol,
                status.toLowerCase(),
                (signal.DATE || signal.date || "").toLowerCase(),
                (signal.EP || signal.ep || "").toString(),
                (signal.CMP || signal.cmp || "").toString(),
                (signal.QTY || signal.qty || "").toString(),
            ].join(" ");

            if (searchFields.indexOf(searchTerm) === -1) {
                return false;
            }
        }

        // Modal status filter
        if (modalStatusValue && status !== modalStatusValue.toUpperCase()) {
            return false;
        }

        // Modal symbol filter
        if (modalSymbolValue && symbol.indexOf(modalSymbolValue) === -1) {
            return false;
        }

        // Position type filter
        if (positionTypeValue && positionType !== positionTypeValue) {
            return false;
        }

        // Investment range filter
        if (investment < minInvestment || investment > maxInvestment) {
            return false;
        }

        // P&L range filter
        if (pnl < minPnl || pnl > maxPnl) {
            return false;
        }

        return true;
    });

    // Reset to first page after filtering
    this.currentPage = 1;
    this.updateDisplayedSignals();
    this.renderSignalsTable();
    this.updatePagination();
};

// Pagination Functions
ETFSignalsManager.prototype.updateDisplayedSignals = function () {
    var startIndex = (this.currentPage - 1) * this.itemsPerPage;
    var endIndex = startIndex + this.itemsPerPage;
    this.displayedSignals = this.filteredSignals.slice(startIndex, endIndex);
    this.totalPages = Math.ceil(
        this.filteredSignals.length / this.itemsPerPage,
    );

    // Ensure we don't exceed available pages
    if (this.currentPage > this.totalPages && this.totalPages > 0) {
        this.currentPage = this.totalPages;
        window.currentPage = this.currentPage;
        startIndex = (this.currentPage - 1) * this.itemsPerPage;
        endIndex = startIndex + this.itemsPerPage;
        this.displayedSignals = this.filteredSignals.slice(
            startIndex,
            endIndex,
        );
    }

    console.log("updateDisplayedSignals:", {
        currentPage: this.currentPage,
        itemsPerPage: this.itemsPerPage,
        totalSignals: this.filteredSignals.length,
        startIndex: startIndex,
        endIndex: endIndex,
        displayedCount: this.displayedSignals.length,
        totalPages: this.totalPages,
    });
};

ETFSignalsManager.prototype.updatePagination = function () {
    var showingCount = document.getElementById("showingCount");
    var totalCount = document.getElementById("totalCount");
    var visibleSignalsCount = document.getElementById("visibleSignalsCount");

    // Calculate the range being shown
    var startItem =
        this.filteredSignals.length > 0
            ? (this.currentPage - 1) * this.itemsPerPage + 1
            : 0;
    var endItem = Math.min(
        this.currentPage * this.itemsPerPage,
        this.filteredSignals.length,
    );

    if (showingCount) {
        showingCount.textContent = this.displayedSignals.length;
    }

    if (totalCount) totalCount.textContent = this.signals.length;
    if (visibleSignalsCount) {
        // Update both visible signals count elements
        visibleSignalsCount.textContent = this.filteredSignals.length;
        var otherVisibleCount = document.querySelectorAll(
            "#visibleSignalsCount",
        );
        otherVisibleCount.forEach(
            function (el) {
                el.textContent = this.filteredSignals.length;
            }.bind(this),
        );
    }

    // Update the items per page selector
    var itemsPerPageSelect = document.getElementById("itemsPerPageSelect");
    if (itemsPerPageSelect && itemsPerPageSelect.value != this.itemsPerPage) {
        itemsPerPageSelect.value = this.itemsPerPage;
    }

    // Update pagination controls
    this.updatePaginationControls();

    console.log(
        "Pagination updated - showing",
        startItem,
        "to",
        endItem,
        "of",
        this.filteredSignals.length,
        "items",
    );
};

ETFSignalsManager.prototype.updatePaginationControls = function () {
    // Update global currentPage variable
    window.currentPage = this.currentPage;

    var prevPageItem = document.getElementById("prevPageItem");
    var nextPageItem = document.getElementById("nextPageItem");
    var currentPageDisplay = document.getElementById("currentPageDisplay");

    if (prevPageItem) {
        if (this.currentPage <= 1) {
            prevPageItem.classList.add("disabled");
        } else {
            prevPageItem.classList.remove("disabled");
        }
    }

    if (nextPageItem) {
        if (this.currentPage >= this.totalPages) {
            nextPageItem.classList.add("disabled");
        } else {
            nextPageItem.classList.remove("disabled");
        }
    }

    if (currentPageDisplay) {
        currentPageDisplay.textContent =
            this.currentPage + " of " + this.totalPages;
    }
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
            "</div>";

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
    var endIndex = Math.min(
        this.currentPage * this.itemsPerPage,
        this.filteredSignals.length,
    );

    if (startItem) startItem.textContent = startIndex;
    if (endItem) endItem.textContent = endIndex;
    if (totalItems) totalItems.textContent = this.filteredSignals.length;

    // Generate pagination buttons
    var buttonsHTML = "";

    // Previous button
    buttonsHTML +=
        '<button class="btn btn-sm btn-outline-primary me-2" ' +
        (this.currentPage === 1 ? "disabled" : "") +
        ' onclick="goToPage(' +
        (this.currentPage - 1) +
        ')">' +
        '<i class="fas fa-chevron-left"></i></button>';

    // Page numbers
    var startPage = Math.max(1, this.currentPage - 2);
    var endPage = Math.min(this.totalPages, this.currentPage + 2);

    if (startPage > 1) {
        buttonsHTML +=
            '<button class="btn btn-sm btn-outline-primary me-1" onclick="goToPage(1)">1</button>';
        if (startPage > 2) {
            buttonsHTML += '<span class="me-1">...</span>';
        }
    }

    for (var i = startPage; i <= endPage; i++) {
        buttonsHTML +=
            '<button class="btn btn-sm ' +
            (i === this.currentPage ? "btn-primary" : "btn-outline-primary") +
            ' me-1" onclick="goToPage(' +
            i +
            ')">' +
            i +
            "</button>";
    }

    if (endPage < this.totalPages) {
        if (endPage < this.totalPages - 1) {
            buttonsHTML += '<span class="me-1">...</span>';
        }
        buttonsHTML +=
            '<button class="btn btn-sm btn-outline-primary me-1" onclick="goToPage(' +
            this.totalPages +
            ')">' +
            this.totalPages +
            "</button>";
    }

    // Next button
    buttonsHTML +=
        '<button class="btn btn-sm btn-outline-primary ms-1" ' +
        (this.currentPage === this.totalPages ? "disabled" : "") +
        ' onclick="goToPage(' +
        (this.currentPage + 1) +
        ')">' +
        '<i class="fas fa-chevron-right"></i></button>';

    buttonsContainer.innerHTML = buttonsHTML;
};

ETFSignalsManager.prototype.showLoadingState = function () {
    var tbody = document.getElementById("signalsTableBody");
    if (tbody) {
        tbody.innerHTML =
            '<tr><td colspan="25" class="text-center py-5">' +
            '<div class="d-flex flex-column justify-content-center align-items-center">' +
            '<div class="spinner-border text-primary mb-3" role="status" style="width: 2.5rem; height: 2.5rem;">' +
            '<span class="visually-hidden">Loading...</span></div>' +
            '<h6 class="text-light mb-2">Loading ETF Signals</h6>' +
            '<small class="text-muted">Fetching data from external database...</small>' +
            '<div class="mt-2"><small class="text-warning">This may take up to 45 seconds</small></div>' +
            "</div></td></tr>";
    }
};

ETFSignalsManager.prototype.hideLoadingState = function () {
    // Loading state is cleared when table is rendered
};

ETFSignalsManager.prototype.showSuccessMessage = function (message) {
    console.log("Success:", message);
};

ETFSignalsManager.prototype.showErrorMessage = function (message) {
    console.error("Error:", message);
    var tbody = document.getElementById("signalsTableBody");
    if (tbody) {
        tbody.innerHTML =
            '<tr><td colspan="25" class="text-center py-5">' +
            '<div class="d-flex flex-column justify-content-center align-items-center">' +
            '<i class="fas fa-exclamation-triangle fa-3x mb-3 text-warning"></i>' +
            '<h6 class="text-light mb-2">Error Loading Data</h6>' +
            '<p class="text-danger mb-3">' +
            message +
            "</p>" +
            '<button class="btn btn-primary" onclick="refreshSignals()">Try Again</button>' +
            "</div></td></tr>";
    }
};

ETFSignalsManager.prototype.startAutoRefresh = function () {
    var self = this;
    this.stopAutoRefresh();
    this.refreshInterval = setInterval(function () {
        self.loadSignals(true);
    }, 300000); // 5 minutes
};

ETFSignalsManager.prototype.stopAutoRefresh = function () {
    if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
        this.refreshInterval = null;
    }
};

// Global functions for HTML event handlers
function refreshSignals() {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.loadSignals(true);
    }
}

// Clear search function for signals
function clearSignalSearch() {
    var searchInput = document.getElementById("signalSearchInput");
    if (searchInput) {
        searchInput.value = "";
        if (window.etfSignalsManager) {
            window.etfSignalsManager.applySearch();
        }
    }
}

// Column settings functions
function selectAllColumns() {
    if (window.etfSignalsManager) {
        var checkboxes = document.querySelectorAll(
            '#columnCheckboxes input[type="checkbox"]',
        );
        checkboxes.forEach(function (checkbox) {
            checkbox.checked = true;
            var columnKey = checkbox.getAttribute("data-column");
            var column = window.etfSignalsManager.availableColumns.find(
                function (col) {
                    return col.key === columnKey;
                },
            );
            if (column) {
                column.visible = true;
            }
        });
    }
}

function resetDefaultColumns() {
    if (window.etfSignalsManager) {
        // Reset to default visibility
        window.etfSignalsManager.availableColumns.forEach(function (column) {
            column.visible =
                column.key === "symbol" ||
                column.key === "ep" ||
                column.key === "cmp" ||
                column.key === "qty" ||
                column.key === "date" ||
                column.key === "chan" ||
                column.key === "inv" ||
                column.key === "tp" ||
                column.key === "tpr" ||
                column.key === "tva" ||
                column.key === "cpl" ||
                column.key === "actions";
        });

        // Update checkboxes
        var checkboxes = document.querySelectorAll(
            '#columnCheckboxes input[type="checkbox"]',
        );
        checkboxes.forEach(function (checkbox) {
            var columnKey = checkbox.getAttribute("data-column");
            var column = window.etfSignalsManager.availableColumns.find(
                function (col) {
                    return col.key === columnKey;
                },
            );
            checkbox.checked = column ? column.visible : false;
        });
    }
}

function applyColumnSettings() {
    if (window.etfSignalsManager) {
        // Save settings and update display
        window.etfSignalsManager.saveColumnSettings();
        window.etfSignalsManager.updateTableHeaders();
        window.etfSignalsManager.renderSignalsTable();
        window.etfSignalsManager.updatePagination();

        // Close modal
        var modal = bootstrap.Modal.getInstance(
            document.getElementById("columnSettingsModal"),
        );
        if (modal) {
            modal.hide();
        }
    }
}

// Global search function for backward compatibility
function applySearch() {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.applySearch();
    }
}

function applyFilters() {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.applyFilters();
    }
}

function clearFilters() {
    // Clear all filter inputs
    var filterInputs = [
        "signalSearch",
        "statusFilter",
        "profitFilter",
        "modalStatusFilter",
        "modalSymbolFilter",
        "positionTypeFilter",
        "minInvestmentFilter",
        "maxInvestmentFilter",
        "minPnlFilter",
        "maxPnlFilter",
    ];

    filterInputs.forEach(function (inputId) {
        var element = document.getElementById(inputId);
        if (element) {
            element.value = "";
        }
    });

    // Apply filters to reset the view
    if (window.etfSignalsManager) {
        window.etfSignalsManager.applyFilters();
    }
}

// Pagination functions
function goToPage(pageNumber) {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.goToPage(pageNumber);
    }
}

function changeItemsPerPage() {
    var select = document.getElementById("itemsPerPageSelect");
    if (select && window.etfSignalsManager) {
        var newValue = parseInt(select.value) || 10;
        console.log("Global changeItemsPerPage called with:", newValue);
        window.etfSignalsManager.changeItemsPerPage(newValue);
    }
}

function setRefreshInterval(interval, text) {
    // Only allow 5 minute intervals
    if (interval !== 300000) {
        interval = 300000;
        text = "5 Min";
    }

    if (window.etfSignalsManager) {
        window.etfSignalsManager.stopAutoRefresh();
        if (interval > 0) {
            window.etfSignalsManager.refreshInterval = setInterval(function () {
                window.etfSignalsManager.loadSignals(true);
            }, interval);
        }
        var currentIntervalSpan = document.getElementById("currentInterval");
        var refreshIntervalDropdown = document.getElementById(
            "refreshIntervalDropdown",
        );
        if (currentIntervalSpan) {
            currentIntervalSpan.textContent = text;
        }
        if (refreshIntervalDropdown) {
            refreshIntervalDropdown.textContent = text;
        }
        console.log("Refresh interval set to:", interval + "ms (" + text + ")");
    }
}

function exportSignals() {
    if (window.etfSignalsManager) {
        var signals = window.etfSignalsManager.signals;
        if (!signals || signals.length === 0) {
            alert("No data to export");
            return;
        }

        var csvContent = "data:text/csv;charset=utf-8,";
        csvContent +=
            "ETF,Entry Price,Current Price,Quantity,Investment,P&L,Change %\n";

        signals.forEach(function (signal) {
            var symbol = signal.etf || signal.symbol || "";
            var entryPrice = signal.ep || signal.entry_price || 0;
            var currentPrice = signal.cmp || signal.current_price || 0;
            var quantity = signal.qty || signal || signal.quantity || 0;
            var investment = signal.inv || signal.investment_amount || 0;
            var pnl = signal.pl || signal.pnl || 0;
            var changePct = signal.change_pct || signal.pp || 0;

            var row = [
                symbol,
                entryPrice,
                currentPrice,
                quantity,
                investment,
                pnl,
                changePct,
            ].join(",");
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
    console.log("Add Deal called with signalId:", signalId);

    // Prevent double-clicking by disabling the button temporarily
    var buttonElement = event ? event.target : null;
    if (buttonElement && buttonElement.tagName === "BUTTON") {
        buttonElement.disabled = true;
        buttonElement.innerHTML =
            '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';

        // Re-enable button after 3 seconds
        setTimeout(function () {
            buttonElement.disabled = false;
            buttonElement.innerHTML =
                '<i class="fas fa-plus me-1"></i>Add Deal';
        }, 3000);
    }

    // Wait for signals to be loaded if they're not available yet
    if (
        !window.etfSignalsManager ||
        !window.etfSignalsManager.signals ||
        window.etfSignalsManager.signals.length === 0
    ) {
        console.log("Signals not loaded yet, waiting...");
        showSwalMessage("Loading signals data, please wait...", "info");

        // Wait up to 5 seconds for signals to load
        var attempts = 0;
        var checkInterval = setInterval(function () {
            attempts++;
            if (
                window.etfSignalsManager &&
                window.etfSignalsManager.signals &&
                window.etfSignalsManager.signals.length > 0
            ) {
                clearInterval(checkInterval);
                findAndProcessSignal(signalId);
            } else if (attempts >= 10) {
                // 5 seconds
                clearInterval(checkInterval);
                showSwalMessage(
                    "Failed to load signals data. Please refresh the page.",
                    "error",
                );
                if (buttonElement) {
                    buttonElement.disabled = false;
                    buttonElement.innerHTML =
                        '<i class="fas fa-plus me-1"></i>Add Deal';
                }
            }
        }, 500);
        return;
    }

    findAndProcessSignal(signalId);
}

function findAndProcessSignal(signalId) {
    console.log("Finding signal for ID:", signalId);

    // Find the complete signal data from the current signals array with multiple ID checks
    var signal = null;
    if (window.etfSignalsManager && window.etfSignalsManager.signals) {
        signal = window.etfSignalsManager.signals.find(function (s) {
            // Check multiple possible ID fields
            return (
                s.ID == signalId ||
                s.id == signalId ||
                s.trade_signal_id == signalId ||
                parseInt(s.ID) == parseInt(signalId) ||
                parseInt(s.id) == parseInt(signalId)
            );
        });
    }

    if (!signal) {
        console.error("Signal not found for ID:", signalId);
        console.log(
            "Available signals:",
            window.etfSignalsManager
                ? window.etfSignalsManager.signals
                : "No manager",
        );
        showSwalMessage(
            "Signal data not found. Please refresh the page and try again.",
            "error",
        );
        return;
    }

    console.log("Found signal:", signal);

    var symbol = signal.Symbol || signal.symbol || signal.etf;
    var price = signal.EP || signal.ep || signal.entry_price;
    var quantity = signal.QTY || signal.qty || signal.quantity;
    var investment = signal.INV || signal.inv || signal.investment_amount;

    // Validate data before proceeding
    if (!symbol || symbol === "UNKNOWN" || price <= 0 || quantity <= 0) {
        showSwalMessage("Invalid signal data. Cannot create deal.", "error");
        return;
    }

    // Show SweetAlert2 confirmation dialog
    if (typeof Swal !== "undefined") {
        Swal.fire({
            title: "Add Deal",
            html:
                "Add deal for <strong>" +
                symbol +
                "</strong> at ₹" +
                parseFloat(price).toFixed(2) +
                " (Qty: " +
                quantity +
                ")?",
            icon: "question",
            showCancelButton: true,
            confirmButtonColor: "#28a745",
            cancelButtonColor: "#6c757d",
            confirmButtonText: "OK",
            cancelButtonText: "Cancel",
            background: "#2c3e50",
            color: "#fff",
            customClass: {
                popup: "swal-dark-theme",
            },
        }).then((result) => {
            if (result.isConfirmed) {
                proceedWithAddingDeal(
                    signal,
                    symbol,
                    price,
                    quantity,
                    investment,
                );
            }
        });
    } else {
        // Fallback to regular confirm if SweetAlert2 is not available
        if (
            confirm(
                "Add deal for " +
                    symbol +
                    " at ₹" +
                    parseFloat(price).toFixed(2) +
                    " (Qty: " +
                    quantity +
                    ")?",
            )
        ) {
            proceedWithAddingDeal(signal, symbol, price, quantity, investment);
        }
    }
}

function proceedWithAddingDeal(
    signal,
    symbol,
    price,
    quantity,
    investment,
    forceAdd,
) {
    console.log("Proceeding with adding deal:", {
        signal: signal,
        symbol: symbol,
        price: price,
        quantity: quantity,
        investment: investment,
        forceAdd: forceAdd,
    });

    // Show loading indicator
    if (typeof Swal !== "undefined") {
        Swal.fire({
            title: "Creating Deal...",
            text: "Please wait while we process your request",
            allowOutsideClick: false,
            allowEscapeKey: false,
            showConfirmButton: false,
            background: "#2c3e50",
            color: "#fff",
            customClass: {
                popup: "swal-dark-theme",
            },
            didOpen: () => {
                Swal.showLoading();
            },
        });
    }

    // Prepare complete signal data for the API
    var signalData = {
        etf: signal.etf || signal.symbol || symbol,
        symbol: signal.etf || signal.symbol || symbol,
        trade_signal_id: signal.trade_signal_id || signal.id,
        pos: signal.pos || "",
        qty: signal.QTY || "",
        ep: signal.EP || "",
        cmp: signal.CMP || "",
        tp: signal.TP || "",
        inv: signal.INV || "",
        pl: signal.PL || "",
        change_pct: signal.CHAN,
        thirty: signal.thirty,
        dh: signal.dh || 0,
        date: signal.date || new Date().toISOString().split("T")[0],
        ed: signal.ED,
        exp: signal.EXP || "",
        pr: signal.PR || "",
        pp: signal.PP || "",
        iv: signal.IV || "",
        ip: signal.IP || "",
        seven: signal.seven || 0,
        ch: signal.ch || signal.change_pct || 0,
        tva: signal.TVA,
        tpr: signal.TPR,
    };

    console.log("Sending signal data:", signalData);

    // Send the request with sanitized data structure
    var requestData = {
        signal_data: {
            symbol: signal.symbol || signal.etf || symbol,
            qty: signal.qty || signal.QTY || 1,
            ep: signal.ep || signal.EP || 0,
            cmp: signal.cmp || signal.CMP || signal.ep || signal.EP || 0,
            pos: signal.pos || 1,
            tp: signal.tp || signal.TP || 0,
            date: signal.date || new Date().toISOString().split("T")[0],
        },
        force_add: forceAdd || false
    };

    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/deals/create-from-signal", true);
    xhr.setRequestHeader("Content-Type", "application/json");

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            console.log("Response status:", xhr.status);
            console.log("Response text:", xhr.responseText);

            if (xhr.status === 200) {
                try {
                    var response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        showSwalMessage(
                            "Deal created successfully for " +
                                symbol +
                                " - Deal ID: " +
                                response.deal_id +
                                " - Investment: ₹" +
                                (response.invested_amount || 0).toFixed(2),
                            "success",
                        );
                    } else {
                        showSwalMessage(
                            "Failed to create deal: " +
                                (response.error ||
                                    response.message ||
                                    "Unknown error"),
                            "error",
                        );
                    }
                } catch (parseError) {
                    console.error("Failed to parse response:", parseError);
                    showSwalMessage(
                        "Server returned invalid response",
                        "error",
                    );
                }
            } else if (xhr.status === 409) {
                // Handle duplicate deal case
                try {
                    var response = JSON.parse(xhr.responseText);
                    if (response.duplicate) {
                        // Show confirmation dialog for duplicate
                        if (typeof Swal !== "undefined") {
                            Swal.fire({
                                title: "Duplicate Deal Detected",
                                html: response.message + "<br><br>Do you want to add it anyway?",
                                icon: "warning",
                                showCancelButton: true,
                                confirmButtonColor: "#ff6b35",
                                cancelButtonColor: "#6c757d",
                                confirmButtonText: "Yes, Add Anyway",
                                cancelButtonText: "Cancel",
                                background: "#2c3e50",
                                color: "#fff",
                                customClass: {
                                    popup: "swal-dark-theme",
                                },
                            }).then((result) => {
                                if (result.isConfirmed) {
                                    // Add force_add flag and retry
                                    var retryRequestData = {
                                        signal_data: requestData.signal_data,
                                        force_add: true
                                    };
                                    
                                    // Retry with force_add flag
                                    proceedWithAddingDeal(signal, symbol, price, quantity, investment, true);
                                }
                            });
                        } else {
                            // Fallback confirm dialog
                            if (confirm(response.message + "\n\nDo you want to add it anyway?")) {
                                proceedWithAddingDeal(signal, symbol, price, quantity, investment, true);
                            }
                        }
                    } else {
                        showSwalMessage(
                            response.message || "Conflict occurred",
                            "error",
                        );
                    }
                } catch (parseError) {
                    console.error("Failed to parse duplicate response:", parseError);
                    showSwalMessage(
                        "Duplicate deal detected but failed to parse response",
                        "error",
                    );
                }
            } else if (xhr.status === 500) {
                showSwalMessage(
                    "Server error occurred. Please try again.",
                    "error",
                );
            } else if (xhr.status === 404) {
                showSwalMessage(
                    "API endpoint not found. Please contact support.",
                    "error",
                );
            } else {
                showSwalMessage(
                    "Request failed with status: " + xhr.status,
                    "error",
                );
            }
        }
    };

    xhr.ontimeout = function () {
        showSwalMessage("Request timed out. Please try again.", "error");
    };

    xhr.onerror = function () {
        showSwalMessage(
            "Network error occurred. Please check your connection.",
            "error",
        );
    };

    xhr.timeout = 10000;
    xhr.send(JSON.stringify(requestData));
}

function createUserDealFromSignal(
    signal,
    symbol,
    entryPrice,
    currentPrice,
    quantity,
    targetPrice,
    investment,
) {
    console.log("Creating user deal from signal:", {
        signal: signal,
        symbol: symbol,
        entryPrice: entryPrice,
        currentPrice: currentPrice,
        quantity: quantity,
        targetPrice: targetPrice,
        investment: investment,
    });

    // Show loading indicator
    if (typeof Swal !== "undefined") {
        Swal.fire({
            title: "Creating Deal...",
            text: "Please wait while we create your deal",
            allowOutsideClick: false,
            allowEscapeKey: false,
            showConfirmButton: false,
            background: "#2c3e50",
            color: "#fff",
            customClass: {
                popup: "swal-dark-theme",
            },
            didOpen: () => {
                Swal.showLoading();
            },
        });
    }

    // Prepare deal data for user_deals table with complete signal information
    var dealData = {
        signal_data: {
            // Core identification
            symbol: symbol,
            etf: symbol,
            Symbol: symbol,
            ID: signal.ID || signal.id || signal.trade_signal_id,
            id: signal.ID || signal.id || signal.trade_signal_id,
            trade_signal_id: signal.ID || signal.id || signal.trade_signal_id,

            // Quantity fields
            qty: quantity,
            QTY: quantity,
            quantity: quantity,

            // Price fields
            ep: entryPrice,
            EP: entryPrice,
            entry_price: entryPrice,
            cmp: currentPrice,
            CMP: currentPrice,
            current_price: currentPrice,
            tp: targetPrice,
            TP: targetPrice,
            target_price: targetPrice,

            // Investment fields
            inv: investment,
            INV: investment,
            investment: investment,
            investment_amount: investment,

            // Position and status
            pos: 1, // Default to LONG position
            position_type: "LONG",
            status: "ACTIVE",

            // Date fields
            date:
                signal.DATE ||
                signal.date ||
                signal.created_at ||
                new Date().toLocaleDateString(),
            DATE:
                signal.DATE ||
                signal.date ||
                signal.created_at ||
                new Date().toLocaleDateString(),
            created_at:
                signal.DATE ||
                signal.date ||
                signal.created_at ||
                new Date().toISOString(),

            // Include all other signal fields as-is
            "7D": signal["7D"] || 0,
            "7D%": signal["7D%"] || "0.00%",
            "30D": signal["30D"] || 0,
            "30D%": signal["30D%"] || "0.00%",
            "%CHAN": signal["%CHAN"] || "0.00%",
            CPL: signal.CPL || 0,
            TPR: signal.TPR || "0.00%",
            TVA: signal.TVA || 0,

            // Add any additional fields from the original signal
            seven: signal.seven || signal["7D"] || 0,
            ch: signal.ch || signal["7D%"] || "0.00%",
            thirty: signal.thirty || signal["30D"] || 0,
            dh: signal.dh || signal["30D%"] || "0.00%",
            chan: signal.chan || signal["%CHAN"] || "0.00%",
        },
    };

    console.log("Sending deal data to user_deals API:", dealData);

    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/deals", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.timeout = 15000; // 15 second timeout

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            console.log("Response status:", xhr.status);
            console.log("Response text:", xhr.responseText);

            if (xhr.status === 200 || xhr.status === 201) {
                try {
                    var response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        if (typeof Swal !== "undefined") {
                            Swal.fire({
                                title: "Success!",
                                html:
                                    "Deal created successfully!<br>" +
                                    "<strong>Symbol:</strong> " +
                                    symbol +
                                    "<br>" +
                                    "<strong>Quantity:</strong> " +
                                    quantity +
                                    "<br>" +
                                    "<strong>Entry Price:</strong> ₹" +
                                    entryPrice.toFixed(2) +
                                    "<br>" +
                                    "<strong>Investment:</strong> ₹" +
                                    investment.toFixed(2),
                                icon: "success",
                                confirmButtonColor: "#28a745",
                                background: "#2c3e50",
                                color: "#fff",
                                customClass: {
                                    popup: "swal-dark-theme",
                                },
                            }).then(() => {
                                // Optional: Redirect to deals page
                                var goToDeals = confirm(
                                    "Would you like to view your deals page?",
                                );
                                if (goToDeals) {
                                    window.location.href = "/deals";
                                }
                            });
                        } else {
                            alert(
                                "Deal created successfully for " + symbol + "!",
                            );
                            var goToDeals = confirm(
                                "Would you like to view your deals page?",
                            );
                            if (goToDeals) {
                                window.location.href = "/deals";
                            }
                        }
                    } else {
                        if (typeof Swal !== "undefined") {
                            Swal.fire({
                                title: "Error!",
                                text:
                                    "Failed to create deal: " +
                                    (response.message || "Unknown error"),
                                icon: "error",
                                confirmButtonColor: "#dc3545",
                                background: "#2c3e50",
                                color: "#fff",
                                customClass: {
                                    popup: "swal-dark-theme",
                                },
                            });
                        } else {
                            alert(
                                "Failed to create deal: " +
                                    (response.message || "Unknown error"),
                            );
                        }
                    }
                } catch (parseError) {
                    console.error("Error parsing response:", parseError);
                    if (typeof Swal !== "undefined") {
                        Swal.fire({
                            title: "Error!",
                            text: "Invalid response from server",
                            icon: "error",
                            confirmButtonColor: "#dc3545",
                            background: "#2c3e50",
                            color: "#fff",
                            customClass: {
                                popup: "swal-dark-theme",
                            },
                        });
                    } else {
                        alert("Invalid response from server");
                    }
                }
            } else if (xhr.status === 401) {
                if (typeof Swal !== "undefined") {
                    Swal.fire({
                        title: "Authentication Required!",
                        text: "Please login to create deals",
                        icon: "warning",
                        confirmButtonColor: "#ffc107",
                        background: "#2c3e50",
                        color: "#fff",
                        customClass: {
                            popup: "swal-dark-theme",
                        },
                    }).then(() => {
                        window.location.href = "/trading-account/login";
                    });
                } else {
                    alert("Please login to create deals");
                    window.location.href = "/trading-account/login";
                }
            } else {
                if (typeof Swal !== "undefined") {
                    Swal.fire({
                        title: "Error!",
                        text:
                            "Server error (" +
                            xhr.status +
                            "). Please try again.",
                        icon: "error",
                        confirmButtonColor: "#dc3545",
                        background: "#2c3e50",
                        color: "#fff",
                        customClass: {
                            popup: "swal-dark-theme",
                        },
                    });
                } else {
                    alert(
                        "Server error (" + xhr.status + "). Please try again.",
                    );
                }
            }
        }
    };

    xhr.ontimeout = function () {
        console.error("Request timed out");
        if (typeof Swal !== "undefined") {
            Swal.fire({
                title: "Timeout!",
                text: "Request timed out. Please try again.",
                icon: "error",
                confirmButtonColor: "#dc3545",
                background: "#2c3e50",
                color: "#fff",
                customClass: {
                    popup: "swal-dark-theme",
                },
            });
        } else {
            alert("Request timed out. Please try again.");
        }
    };

    xhr.onerror = function () {
        console.error("Network error occurred");
        if (typeof Swal !== "undefined") {
            Swal.fire({
                title: "Network Error!",
                text: "Network error occurred. Please check your connection.",
                icon: "error",
                confirmButtonColor: "#dc3545",
                background: "#2c3e50",
                color: "#fff",
                customClass: {
                    popup: "swal-dark-theme",
                },
            });
        } else {
            alert("Network error occurred. Please check your connection.");
        }
    };

    xhr.send(JSON.stringify(dealData));
}

// Function to sort signals by any column
function sortSignalsByColumn(column) {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.sortDirection =
            window.etfSignalsManager.sortDirection === "asc" ? "desc" : "asc";
        var direction = window.etfSignalsManager.sortDirection;

        window.etfSignalsManager.filteredSignals.sort(function (a, b) {
            var valueA, valueB;

            switch (column) {
                case "trade_signal_id":
                    valueA = parseInt(a.trade_signal_id || a.id || 0);
                    valueB = parseInt(b.trade_signal_id || b.id || 0);
                    break;
                case "symbol":
                    valueA = (a.etf || a.symbol || "").toLowerCase();
                    valueB = (b.etf || b.symbol || "").toLowerCase();
                    break;
                case "ep":
                    valueA = parseFloat(a.ep || a.entry_price || 0);
                    valueB = parseFloat(b.ep || b.entry_price || 0);
                    break;
                case "cmp":
                    valueA = parseFloat(a.cmp || a.current_price || 0);
                    valueB = parseFloat(b.cmp || b.current_price || 0);
                    break;
                case "qty":
                    valueA = parseInt(a.qty || a.quantity || 0);
                    valueB = parseInt(b.qty || b.quantity || 0);
                    break;
                case "changePct":
                    valueA = parseFloat(a.change_pct || a.pp || 0);
                    valueB = parseFloat(b.change_pct || a.pp || 0);
                    break;
                case "inv":
                    valueA = parseFloat(a.inv || a.investment_amount || 0);
                    valueB = parseFloat(b.inv || b.investment_amount || 0);
                    break;
                case "tp":
                    valueA = parseFloat(a.tp || a.target_price || 0);
                    valueB = parseFloat(b.tp || b.target_price || 0);
                    break;
                case "pl":
                    valueA = parseFloat(a.pl || a.pnl || 0);
                    valueB = parseFloat(b.pl || b.pnl || 0);
                    break;
                case "date":
                    valueA = a.date || a.created_at || "";
                    valueB = b.date || b.created_at || "";
                    break;
                default:
                    return 0;
            }

            if (typeof valueA === "string") {
                return direction === "asc"
                    ? valueA.localeCompare(valueB)
                    : valueB.localeCompare(valueA);
            } else {
                return direction === "asc" ? valueA - valueB : valueB - valueA;
            }
        });

        window.etfSignalsManager.displayedSignals =
            window.etfSignalsManager.filteredSignals.slice();
        window.etfSignalsManager.renderSignalsTable();
        window.etfSignalsManager.updateCounts();
    }
}

// Initialize the ETF Signals Manager
window.etfSignalsManager = new ETFSignalsManager();
// Initialize global currentPage variable
window.currentPage = 1;

document.addEventListener("DOMContentLoaded", function () {
    // Set default refresh interval to 5 minutes
    var currentIntervalSpan = document.getElementById("currentInterval");
    var refreshIntervalDropdown = document.getElementById(
        "refreshIntervalDropdown",
    );
    if (currentIntervalSpan) {
        currentIntervalSpan.textContent = "5 Min";
    }
    if (refreshIntervalDropdown) {
        refreshIntervalDropdown.textContent = "5 Min";
    }
});

// Add Deal functionality
function addDealFromSignal(symbol, signalData) {
    try {
        var signal =
            typeof signalData === "string"
                ? JSON.parse(signalData)
                : signalData;

        console.log("Adding deal for signal:", signal);
        console.log("Symbol:", symbol);

        // Validate signal data
        if (!signal || !symbol) {
            showMessage("Invalid signal data. Cannot create deal.", "error");
            return;
        }

        var price = signal.cmp || signal.ep || 0;
        var quantity = signal.qty || 1;

        if (
            confirm(
                "Add deal for " +
                    symbol +
                    " at ₹" +
                    price.toFixed(2) +
                    " (Qty: " +
                    quantity +
                    ")?",
            )
        ) {
            return;
        }

        // Show loading state
        showMessage("Creating deal for " + symbol + "...", "info");

        var xhr = new XMLHttpRequest();
        xhr.open("POST", "/api/dynamic/add-deal", true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.timeout = 10000; // 10 second timeout

        xhr.onreadystatechange = function () {
            if (xhr.readyState === 4) {
                try {
                    if (xhr.status === 200) {
                        var response = JSON.parse(xhr.responseText);
                        if (response.success) {
                            showMessage(
                                "Deal created successfully for " +
                                    symbol +
                                    "! Deal ID: " +
                                    response.deal_id,
                                "success",
                            );

                            // Optional: redirect to deals page after a delay
                            setTimeout(function () {
                                if (
                                    confirm(
                                        "Deal created! Would you like to view your deals page?",
                                    )
                                ) {
                                    window.location.href = "/deals";
                                }
                            }, 2000);
                        } else {
                            showMessage(
                                "Failed to create deal: " +
                                    (response.message || "Unknown error"),
                                "error",
                            );
                        }
                    } else if (xhr.status === 400) {
                        var errorResponse = JSON.parse(xhr.responseText);
                        showMessage(
                            "Invalid request: " +
                                (errorResponse.message || "Bad request"),
                            "error",
                        );
                    } else if (xhr.status === 500) {
                        var errorResponse = JSON.parse(xhr.responseText);
                        showMessage(
                            "Server error: " +
                                (errorResponse.message ||
                                    "Internal server error"),
                            "error",
                        );
                    } else {
                        showMessage(
                            "Request failed with status: " +
                                xhr.status +
                                ". Please try again.",
                            "error",
                        );
                    }
                } catch (parseError) {
                    console.error("Error parsing response:", parseError);
                    showMessage(
                        "Invalid response from server. Please try again.",
                        "error",
                    );
                }
            }
        };

        xhr.ontimeout = function () {
            showMessage("Request timed out. Please try again.", "error");
        };

        xhr.onerror = function () {
            showMessage(
                "Network error. Please check your connection and try again.",
                "error",
            );
        };

        xhr.send(
            JSON.stringify({
                signal_data: signal,
            }),
        );
    } catch (error) {
        console.error("Error adding deal:", error);
        showMessage("Error processing request: " + error.message, "error");
    }
}

// Function to stop automatic CMP updates
function stopAutoCMPUpdates() {
    if (typeof cmpUpdateInterval !== "undefined" && cmpUpdateInterval) {
        clearInterval(cmpUpdateInterval);
        cmpUpdateInterval = null;
        console.log("⏹️ Auto CMP updates stopped");
    }
}

// Clean up interval when page unloads
window.addEventListener("beforeunload", function () {
    stopAutoCMPUpdates();
});

function showMessage(message, type) {
    // Remove any existing alerts first
    var existingAlerts = document.querySelectorAll(".custom-alert");
    existingAlerts.forEach(function (alert) {
        alert.remove();
    });

    var alertClass, iconClass;
    switch (type) {
        case "success":
            alertClass = "alert-success";
            iconClass = "fa-check-circle";
            break;
        case "error":
            alertClass = "alert-danger";
            iconClass = "fa-exclamation-triangle";
            break;
        case "info":
            alertClass = "alert-info";
            iconClass = "fa-info-circle";
            break;
        default:
            alertClass = "alert-primary";
            iconClass = "fa-info-circle";
    }

    var alertHtml =
        '<div class="alert ' +
        alertClass +
        ' alert-dismissible fade show custom-alert position-fixed" role="alert" style="top: 20px; right: 20px; z-index: 9999; min-width: 300px;">' +
        '<i class="fas ' +
        iconClass +
        ' me-2"></i>' +
        message +
        '<button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>' +
        "</div>";

    var alertDiv = document.createElement("div");
    alertDiv.innerHTML = alertHtml;
    document.body.appendChild(alertDiv);

    // Auto-remove after 5 seconds
    setTimeout(function () {
        var alert = document.querySelector(".custom-alert");
        if (alert) {
            alert.remove();
        }
    }, 5000);
}

function showSwalMessage(message, type) {
    if (typeof Swal !== "undefined") {
        var icon = "info";
        var color = "#28a745";

        switch (type) {
            case "success":
                icon = "success";
                color = "#28a745";
                break;
            case "error":
                icon = "error";
                color = "#dc3545";
                break;
            case "warning":
                icon = "warning";
                color = "#ffc107";
                break;
            default:
                icon = "info";
                color = "#17a2b8";
        }

        Swal.fire({
            title: type.charAt(0).toUpperCase() + type.slice(1),
            text: message,
            icon: icon,
            confirmButtonColor: color,
            background: "#2c3e50",
            color: "#fff",
            customClass: {
                popup: "swal-dark-theme",
            },
        });
    } else {
        // Fallback to regular alert
        alert(message);
    }
}

ETFSignalsManager.prototype.updateCounts = function () {
    // Update total count display
    var totalElement = document.getElementById("totalCount");
    var visibleElement = document.getElementById("visibleSignalsCount");
    var showingElement = document.getElementById("showingCount");

    if (totalElement) {
        totalElement.textContent = this.signals.length;
    }
    if (visibleElement) {
        visibleElement.textContent = this.filteredSignals.length;
    }
    if (showingElement) {
        showingElement.textContent = this.filteredSignals.length;
    }
};

// Page navigation function
ETFSignalsManager.prototype.goToPage = function (page) {
    if (page >= 1 && page <= this.totalPages && page !== this.currentPage) {
        this.currentPage = page;
        this.updateDisplayedSignals();
        this.renderSignalsTable();
        this.renderPaginationHTML();
    }
};

// New Enhanced Features for Trading Signals
ETFSignalsManager.prototype.setupNewFeatures = function () {
    console.log("Setting up new enhanced features");
    this.setupDateFilters();
    this.initializeCharts();
    
    // Calculate performance metrics only if signals are already loaded
    if (this.signals && this.signals.length > 0) {
        this.calculatePerformanceMetrics();
    }
};

// Performance Metrics Calculation
ETFSignalsManager.prototype.calculatePerformanceMetrics = function () {
    console.log('Calculating performance metrics for', this.signals ? this.signals.length : 0, 'signals');
    
    if (!this.signals || this.signals.length === 0) {
        console.log('No signals data available for performance calculation');
        this.updatePerformanceDisplay({
            totalSignals: 0,
            activeSignals: 0,
            profitableSignals: 0,
            winRate: 0,
            totalInvestment: 0,
            totalCurrentValue: 0,
            totalPnl: 0,
            topPerformers: [],
            worstPerformers: []
        });
        return;
    }

    var totalSignals = this.signals.length;
    var activeSignals = 0;
    var profitableSignals = 0;
    var totalInvestment = 0;
    var totalCurrentValue = 0;
    var totalPnl = 0;
    var topPerformers = [];

    console.log('Processing', totalSignals, 'signals for performance metrics');

    this.signals.forEach(function(signal, index) {
        console.log('Processing signal', index + 1, ':', signal);
        
        // Use the actual property names from your real data
        var quantity = parseFloat(signal.QTY || signal.qty || 0);
        var entryPrice = parseFloat(signal.EP || signal.ep || 0);
        var currentPrice = parseFloat(signal.CMP || signal.cmp || 0);
        var investment = parseFloat(signal.INV || signal.inv || 0);
        var currentValue = parseFloat(signal.TVA || signal.tva || 0);
        var pnl = parseFloat(signal.CPL || signal.cpl || 0);
        var chanPercent = signal['%CHAN'] || signal.chan || '0%';
        
        // If INV and TVA are not available, calculate them
        if (!investment && quantity && entryPrice) {
            investment = quantity * entryPrice;
        }
        if (!currentValue && quantity && currentPrice) {
            currentValue = quantity * currentPrice;
        }
        if (!pnl && investment && currentValue) {
            pnl = currentValue - investment;
        }
        
        console.log('Signal calculations - Investment:', investment, 'Current Value:', currentValue, 'P&L:', pnl);
        
        totalInvestment += investment;
        totalCurrentValue += currentValue;
        totalPnl += pnl;
        
        if (pnl > 0) profitableSignals++;
        activeSignals++; // Assuming all loaded signals are active
        
        // Collect for top/worst performers
        topPerformers.push({
            symbol: signal.Symbol || signal.symbol || signal.etf || signal.scrip || 'Signal-' + (index + 1),
            pnl: pnl,
            pct: chanPercent,
            investment: investment,
            currentValue: currentValue
        });
    });

    var winRate = totalSignals > 0 ? (profitableSignals / totalSignals * 100) : 0;

    console.log('Performance Summary:', {
        totalSignals: totalSignals,
        activeSignals: activeSignals,
        profitableSignals: profitableSignals,
        winRate: winRate,
        totalInvestment: totalInvestment,
        totalCurrentValue: totalCurrentValue,
        totalPnl: totalPnl
    });

    // Sort performers by P&L
    topPerformers.sort(function(a, b) { return b.pnl - a.pnl; });
    var worstPerformers = topPerformers.slice().reverse().slice(0, 5);

    this.updatePerformanceDisplay({
        totalSignals: totalSignals,
        activeSignals: activeSignals,
        profitableSignals: profitableSignals,
        winRate: winRate,
        totalInvestment: totalInvestment,
        totalCurrentValue: totalCurrentValue,
        totalPnl: totalPnl,
        topPerformers: topPerformers.slice(0, 5),
        worstPerformers: worstPerformers
    });
};

ETFSignalsManager.prototype.updatePerformanceDisplay = function (metrics) {
    // Update summary cards
    this.updateElement('totalSignalsCount', metrics.totalSignals);
    this.updateElement('activeSignalsCount', metrics.activeSignals);
    this.updateElement('profitableSignalsCount', metrics.profitableSignals);
    this.updateElement('winRatePercentage', metrics.winRate.toFixed(1) + '%');
    this.updateElement('totalInvestmentAmount', '₹' + this.formatNumber(metrics.totalInvestment));
    this.updateElement('totalCurrentValue', '₹' + this.formatNumber(metrics.totalCurrentValue));
    
    var pnlElement = document.getElementById('totalPnlAmount');
    if (pnlElement) {
        pnlElement.textContent = '₹' + this.formatNumber(metrics.totalPnl);
        pnlElement.className = 'mb-0 ' + (metrics.totalPnl >= 0 ? 'text-success' : 'text-danger');
    }

    // Update performers tables
    this.updatePerformersTable('topPerformersTable', metrics.topPerformers || []);
    this.updatePerformersTable('lowPerformersTable', metrics.worstPerformers || []);
};

ETFSignalsManager.prototype.updateElement = function (id, value) {
    var element = document.getElementById(id);
    if (element) {
        element.textContent = value;
        console.log('Updated element', id, 'with value:', value);
    } else {
        console.log('Element not found:', id);
    }
};

ETFSignalsManager.prototype.formatNumber = function (num) {
    return new Intl.NumberFormat('en-IN').format(Math.abs(num));
};

ETFSignalsManager.prototype.updatePerformersTable = function (tableId, performers) {
    var tbody = document.getElementById(tableId);
    if (!tbody) {
        console.log('Table body not found:', tableId);
        return;
    }

    if (!performers || performers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">No data available</td></tr>';
        return;
    }

    var html = '';
    performers.forEach(function(performer) {
        var pnlClass = performer.pnl >= 0 ? 'text-success' : 'text-danger';
        var formattedPnl = isNaN(performer.pnl) ? '₹0.00' : '₹' + performer.pnl.toFixed(2);
        html += '<tr>' +
            '<td>' + (performer.symbol || 'N/A') + '</td>' +
            '<td class="' + pnlClass + '">' + formattedPnl + '</td>' +
            '<td class="' + pnlClass + '">' + (performer.pct || '0%') + '</td>' +
            '</tr>';
    });
    tbody.innerHTML = html;
    console.log('Updated performers table:', tableId, 'with', performers.length, 'entries');
};

// Date Filter Functions
ETFSignalsManager.prototype.setupDateFilters = function () {
    var startDateInput = document.getElementById('startDateFilter');
    var endDateInput = document.getElementById('endDateFilter');
    
    if (startDateInput) {
        startDateInput.addEventListener('change', this.applyDateFilters.bind(this));
    }
    if (endDateInput) {
        endDateInput.addEventListener('change', this.applyDateFilters.bind(this));
    }
};

// Global functions for date filtering
function applyQuickDateFilter(days) {
    console.log('Applying quick date filter for', days, 'days');
    if (window.etfSignalsManager) {
        var endDate = new Date();
        var startDate = new Date();
        startDate.setDate(startDate.getDate() - days);
        
        window.etfSignalsManager.dateFilters.startDate = startDate;
        window.etfSignalsManager.dateFilters.endDate = endDate;
        window.etfSignalsManager.dateFilters.quickFilter = days;
        
        // Update input fields
        var startInput = document.getElementById('startDateFilter');
        var endInput = document.getElementById('endDateFilter');
        
        if (startInput) startInput.value = startDate.toISOString().split('T')[0];
        if (endInput) endInput.value = endDate.toISOString().split('T')[0];
        
        // Apply the filter immediately
        window.etfSignalsManager.filterAndRenderSignals();
        
        // Show a success message
        console.log('Date filter applied: Last', days, 'days');
        
        // Close the modal if it's open
        var modal = document.getElementById('signalFiltersModal');
        if (modal) {
            var modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        }
    }
}

function clearDateFilter() {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.dateFilters = {
            startDate: null,
            endDate: null,
            quickFilter: null
        };
        
        var startInput = document.getElementById('startDateFilter');
        var endInput = document.getElementById('endDateFilter');
        
        if (startInput) startInput.value = '';
        if (endInput) endInput.value = '';
        
        window.etfSignalsManager.applyDateFilters();
    }
}

ETFSignalsManager.prototype.applyDateFilters = function () {
    var startDateInput = document.getElementById('startDateFilter');
    var endDateInput = document.getElementById('endDateFilter');
    
    if (startDateInput && startDateInput.value) {
        this.dateFilters.startDate = new Date(startDateInput.value);
    }
    if (endDateInput && endDateInput.value) {
        this.dateFilters.endDate = new Date(endDateInput.value);
    }
    
    this.filterAndRenderSignals();
};

// Section Toggle Functions - Direct style manipulation approach
function toggleTableSection() {
    var content = document.getElementById('signalsContent');
    var icon = document.getElementById('tableToggleIcon');
    var button = document.querySelector('[onclick="toggleTableSection()"]');
    
    var cardBody = content ? content.querySelector('.card-body') : null;
    
    if (cardBody && cardBody.style.display === 'none') {
        cardBody.style.display = 'block';
        if (icon) icon.className = 'fas fa-minus me-1';
        if (button) button.innerHTML = '<i class="fas fa-minus me-1" id="tableToggleIcon"></i>Minimize';
    } else if (cardBody) {
        cardBody.style.display = 'none';
        if (icon) icon.className = 'fas fa-plus me-1';
        if (button) button.innerHTML = '<i class="fas fa-plus me-1" id="tableToggleIcon"></i>Maximize';
    }
}

function togglePerformanceSection() {
    var cardBody = document.getElementById('performanceBody');
    var icon = document.getElementById('performanceToggleIcon');
    var button = document.querySelector('[onclick="togglePerformanceSection()"]');
    
    console.log('Toggling performance section - cardBody:', cardBody, 'display:', cardBody ? cardBody.style.display : 'not found');
    
    if (cardBody && cardBody.style.display === 'none') {
        cardBody.style.display = 'block';
        if (icon) icon.className = 'fas fa-minus me-1';
        if (button) button.innerHTML = '<i class="fas fa-minus me-1" id="performanceToggleIcon"></i>Minimize';
    } else if (cardBody) {
        cardBody.style.display = 'none';
        if (icon) icon.className = 'fas fa-plus me-1';
        if (button) button.innerHTML = '<i class="fas fa-plus me-1" id="performanceToggleIcon"></i>Maximize';
    }
}

function toggleAnalyticsSection() {
    var cardBody = document.getElementById('analyticsBody');
    var icon = document.getElementById('analyticsToggleIcon');
    var button = document.querySelector('[onclick="toggleAnalyticsSection()"]');
    
    console.log('Toggling analytics section - cardBody:', cardBody, 'display:', cardBody ? cardBody.style.display : 'not found');
    
    if (cardBody && cardBody.style.display === 'none') {
        cardBody.style.display = 'block';
        if (icon) icon.className = 'fas fa-minus me-1';
        if (button) button.innerHTML = '<i class="fas fa-minus me-1" id="analyticsToggleIcon"></i>Minimize';
    } else if (cardBody) {
        cardBody.style.display = 'none';
        if (icon) icon.className = 'fas fa-plus me-1';
        if (button) button.innerHTML = '<i class="fas fa-plus me-1" id="analyticsToggleIcon"></i>Maximize';
    }
}

// Full Screen Functions
function toggleFullScreen() {
    var modal = document.getElementById('fullScreenModal');
    var tableContainer = document.querySelector('.table-responsive');
    var fullScreenContainer = document.getElementById('fullScreenTableContainer');
    
    if (modal) {
        // Move table to full screen container
        if (tableContainer && fullScreenContainer) {
            var tableClone = tableContainer.cloneNode(true);
            tableClone.classList.add('full-screen-table');
            fullScreenContainer.innerHTML = '';
            fullScreenContainer.appendChild(tableClone);
        }
        
        // Show modal
        var modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
    }
}

function exitFullScreen() {
    var modal = document.getElementById('fullScreenModal');
    if (modal) {
        var modalInstance = bootstrap.Modal.getInstance(modal);
        if (modalInstance) {
            modalInstance.hide();
        }
    }
}

// Advanced Analytics Calculations and Display
ETFSignalsManager.prototype.initializeCharts = function () {
    console.log("Calculating advanced analytics");
    this.calculateAdvancedAnalytics();
};

ETFSignalsManager.prototype.calculateAdvancedAnalytics = function () {
    if (!this.signals || this.signals.length === 0) {
        this.updateAdvancedAnalyticsDisplay({
            avgHoldPeriod: '0 days',
            maxDrawdown: '0%',
            sharpeRatio: '0.00',
            riskRewardRatio: '1:0',
            successRate: '0%'
        });
        return;
    }

    var totalSignals = this.signals.length;
    var profitableSignals = 0;
    var totalReturn = 0;
    var returns = [];
    
    this.signals.forEach(function(signal) {
        var pnl = parseFloat(signal.CPL || signal.cpl || 0);
        var investment = parseFloat(signal.INV || signal.inv || 0);
        
        if (pnl > 0) profitableSignals++;
        
        if (investment > 0) {
            var returnPct = (pnl / investment) * 100;
            returns.push(returnPct);
            totalReturn += returnPct;
        }
    });

    var successRate = totalSignals > 0 ? (profitableSignals / totalSignals * 100) : 0;
    var avgReturn = returns.length > 0 ? totalReturn / returns.length : 0;
    
    // Calculate risk metrics (simplified)
    var variance = 0;
    if (returns.length > 1) {
        returns.forEach(function(ret) {
            variance += Math.pow(ret - avgReturn, 2);
        });
        variance = variance / (returns.length - 1);
    }
    var volatility = Math.sqrt(variance);
    var sharpeRatio = volatility > 0 ? avgReturn / volatility : 0;
    
    // Find max drawdown (simplified)
    var maxDrawdown = 0;
    var peak = 0;
    var runningPnl = 0;
    
    this.signals.forEach(function(signal) {
        var pnl = parseFloat(signal.CPL || signal.cpl || 0);
        runningPnl += pnl;
        if (runningPnl > peak) peak = runningPnl;
        var drawdown = ((peak - runningPnl) / Math.abs(peak)) * 100;
        if (drawdown > maxDrawdown) maxDrawdown = drawdown;
    });

    this.updateAdvancedAnalyticsDisplay({
        avgHoldPeriod: '5 days', // Placeholder - would need entry/exit dates
        maxDrawdown: maxDrawdown.toFixed(2) + '%',
        sharpeRatio: sharpeRatio.toFixed(2),
        riskRewardRatio: '1:' + (avgReturn > 0 ? (avgReturn/10).toFixed(1) : '0'),
        successRate: successRate.toFixed(1) + '%'
    });
};

ETFSignalsManager.prototype.updateAdvancedAnalyticsDisplay = function (analytics) {
    this.updateElement('avgHoldPeriod', analytics.avgHoldPeriod);
    this.updateElement('maxDrawdown', analytics.maxDrawdown);
    this.updateElement('sharpeRatio', analytics.sharpeRatio);
    this.updateElement('riskRewardRatio', analytics.riskRewardRatio);
    this.updateElement('successRate', analytics.successRate);
    
    console.log('Updated advanced analytics:', analytics);
};

// Enhanced filtering with date support
ETFSignalsManager.prototype.filterAndRenderSignals = function () {
    console.log('Filtering signals with date filters:', this.dateFilters);
    
    this.filteredSignals = this.signals.filter(function(signal) {
        var passesFilters = true;
        
        // Date filtering
        if (this.dateFilters.startDate || this.dateFilters.endDate) {
            // Try multiple date field variations
            var signalDateStr = signal.date || signal.DATE || signal.created_at || signal.timestamp;
            var signalDate;
            
            if (signalDateStr) {
                // Handle different date formats
                if (typeof signalDateStr === 'string') {
                    // Try to parse DDMMYY format if it looks like one
                    if (signalDateStr.length === 6 && /^\d{6}$/.test(signalDateStr)) {
                        var day = signalDateStr.substring(0, 2);
                        var month = signalDateStr.substring(2, 4);
                        var year = '20' + signalDateStr.substring(4, 6);
                        signalDate = new Date(year + '-' + month + '-' + day);
                    } else {
                        signalDate = new Date(signalDateStr);
                    }
                } else {
                    signalDate = new Date(signalDateStr);
                }
                
                // If date is invalid, use current date as fallback
                if (isNaN(signalDate.getTime())) {
                    console.log('Invalid date for signal:', signalDateStr, 'using current date');
                    signalDate = new Date();
                }
            } else {
                // No date found, use current date
                signalDate = new Date();
            }
            
            console.log('Signal date:', signalDate, 'Start filter:', this.dateFilters.startDate, 'End filter:', this.dateFilters.endDate);
            
            if (this.dateFilters.startDate && signalDate < this.dateFilters.startDate) {
                passesFilters = false;
                console.log('Signal filtered out by start date');
            }
            if (this.dateFilters.endDate && signalDate > this.dateFilters.endDate) {
                passesFilters = false;
                console.log('Signal filtered out by end date');
            }
        }
        
        return passesFilters;
    }.bind(this));
    
    console.log('Filtered', this.filteredSignals.length, 'signals from', this.signals.length, 'total');
    
    this.renderSignalsTable();
    this.calculatePerformanceMetrics();
    this.updateSignalCounts();
};

// Initialize ETF Signals Manager when DOM is ready
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
        window.etfSignalsManager = new ETFSignalsManager();
    });
} else {
    window.etfSignalsManager = new ETFSignalsManager();
}

// Date filtering functions
function applyQuickDateFilter(days) {
    console.log('Applying quick date filter for last', days, 'days');
    
    var endDate = new Date();
    var startDate = new Date();
    startDate.setDate(endDate.getDate() - days);
    
    var startDateStr = startDate.toISOString().split('T')[0];
    var endDateStr = endDate.toISOString().split('T')[0];
    
    console.log('Date range:', startDateStr, 'to', endDateStr);
    
    var startDateInput = document.getElementById('startDateFilter');
    var endDateInput = document.getElementById('endDateFilter');
    
    if (startDateInput) startDateInput.value = startDateStr;
    if (endDateInput) endDateInput.value = endDateStr;
    
    if (window.etfSignalsManager) {
        window.etfSignalsManager.dateFilters.startDate = startDateStr;
        window.etfSignalsManager.dateFilters.endDate = endDateStr;
        window.etfSignalsManager.dateFilters.quickFilter = days;
        
        // Show loading for performance analysis
        window.etfSignalsManager.showPerformanceLoading();
        
        // Apply filters with a small delay to show loading
        setTimeout(function() {
            window.etfSignalsManager.applyFilters();
        }, 100);
    }
    
    console.log('Quick date filter applied for last', days, 'days');
}

function clearDateFilter() {
    var startDateInput = document.getElementById('startDateFilter');
    var endDateInput = document.getElementById('endDateFilter');
    
    if (startDateInput) startDateInput.value = '';
    if (endDateInput) endDateInput.value = '';
    
    if (window.etfSignalsManager) {
        window.etfSignalsManager.dateFilters = { startDate: null, endDate: null, quickFilter: null };
        window.etfSignalsManager.applyFilters();
    }
    
    console.log('Cleared date filters');
}

function applyFilters() {
    if (!window.etfSignalsManager) return;
    
    var startDate = document.getElementById('startDateFilter')?.value;
    var endDate = document.getElementById('endDateFilter')?.value;
    
    window.etfSignalsManager.dateFilters.startDate = startDate;
    window.etfSignalsManager.dateFilters.endDate = endDate;
    window.etfSignalsManager.applyFilters();
}

function clearFilters() {
    var inputs = ['startDateFilter', 'endDateFilter', 'positionTypeFilter', 'modalStatusFilter', 'modalSymbolFilter'];
    inputs.forEach(function(id) {
        var input = document.getElementById(id);
        if (input) input.value = '';
    });
    
    if (window.etfSignalsManager) {
        window.etfSignalsManager.dateFilters = { startDate: null, endDate: null, quickFilter: null };
        window.etfSignalsManager.applyFilters();
    }
}

// Enhanced applyFilters method with better date parsing
ETFSignalsManager.prototype.applyFilters = function() {
    console.log('Applying filters with date range:', this.dateFilters);
    
    var filteredSignals = this.signals.slice();
    
    // Apply date filtering if dates are set
    if (this.dateFilters.startDate || this.dateFilters.endDate) {
        var startDate = this.dateFilters.startDate ? new Date(this.dateFilters.startDate) : null;
        var endDate = this.dateFilters.endDate ? new Date(this.dateFilters.endDate) : null;
        
        filteredSignals = filteredSignals.filter(function(signal) {
            var signalDate = signal.DATE || signal.date;
            if (!signalDate || signalDate === '--') return true;
            
            console.log('Processing signal date:', signalDate, 'Length:', signalDate.length);
            var parsedDate = null;
            
            // Handle different date formats
            if (signalDate.length === 7) {
                // Format: "12Dec24"
                var day = signalDate.substring(0, 2);
                var monthStr = signalDate.substring(2, 5);
                var year = '20' + signalDate.substring(5, 7);
                
                var monthMap = {
                    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                    'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                    'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                };
                
                var monthNum = monthMap[monthStr];
                if (monthNum) {
                    parsedDate = new Date(year + '-' + monthNum + '-' + day);
                }
            } else if (signalDate.length === 6) {
                // Format: "1Dec24" 
                var day = signalDate.substring(0, 1);
                var monthStr = signalDate.substring(1, 4);
                var year = '20' + signalDate.substring(4, 6);
                
                var monthMap = {
                    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                    'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                    'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                };
                
                var monthNum = monthMap[monthStr];
                if (monthNum) {
                    parsedDate = new Date(year + '-' + monthNum + '-0' + day);
                }
            } else if (signalDate.includes('-')) {
                // Format: "2024-12-01" or similar
                parsedDate = new Date(signalDate);
            } else if (signalDate.includes('/')) {
                // Format: "12/01/2024" or similar
                parsedDate = new Date(signalDate);
            }
            
            if (parsedDate && !isNaN(parsedDate.getTime())) {
                // Set time to beginning/end of day for proper comparison
                var compareDate = new Date(parsedDate.getFullYear(), parsedDate.getMonth(), parsedDate.getDate());
                var compareStart = startDate ? new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate()) : null;
                var compareEnd = endDate ? new Date(endDate.getFullYear(), endDate.getMonth(), endDate.getDate()) : null;
                
                console.log('Date comparison:', compareDate, 'vs start:', compareStart, 'vs end:', compareEnd);
                if (compareStart && compareDate < compareStart) {
                    console.log('Filtering out signal - before start date');
                    return false;
                }
                if (compareEnd && compareDate > compareEnd) {
                    console.log('Filtering out signal - after end date');
                    return false;
                }
            }
            
            return true;
        });
        
        console.log('Filtered from', this.signals.length, 'to', filteredSignals.length, 'signals');
    }
    
    this.filteredSignals = filteredSignals;
    this.currentPage = 1;
    this.updatePagination();
    this.renderSignalsTable();
    
    // Update performance analysis with filtered data
    if (this.updatePerformanceAnalysis) {
        this.updatePerformanceAnalysis();
    }
};

// Update Performance Analysis with real data
ETFSignalsManager.prototype.updatePerformanceAnalysis = function() {
    if (!this.filteredSignals || this.filteredSignals.length === 0) return;
    
    var totalSignals = this.filteredSignals.length;
    var activeSignals = 0;
    var profitableSignals = 0;
    var totalInvestment = 0;
    var totalCurrentValue = 0;
    var totalPnl = 0;
    var topPerformers = [];
    var worstPerformers = [];
    
    this.filteredSignals.forEach(function(signal) {
        var investment = parseFloat(signal.INV || signal.investment || 0);
        var pnl = parseFloat(signal.CPL || signal.pnl || 0);
        var cmp = parseFloat(signal.CMP || signal.current_price || 0);
        var qty = parseFloat(signal.QTY || signal.qty || 0);
        var symbol = signal.Symbol || signal.symbol || signal.etf;
        var changePercent = parseFloat(String(signal['%CHAN'] || '0').replace('%', ''));
        
        totalInvestment += investment;
        totalCurrentValue += (cmp * qty);
        totalPnl += pnl;
        
        if (pnl > 0) profitableSignals++;
        if (signal.status !== 'CLOSED') activeSignals++;
        
        if (symbol && symbol !== '--') {
            var perfData = { symbol: symbol, pnl: pnl, percent: changePercent };
            
            if (pnl > 0) {
                topPerformers.push(perfData);
            } else if (pnl < 0) {
                worstPerformers.push(perfData);
            }
        }
    });
    
    // Sort performers
    topPerformers.sort(function(a, b) { return b.pnl - a.pnl; });
    worstPerformers.sort(function(a, b) { return a.pnl - b.pnl; });
    
    var winRate = totalSignals > 0 ? ((profitableSignals / totalSignals) * 100) : 0;
    
    // Update summary cards
    document.getElementById('totalSignalsCount').textContent = totalSignals;
    document.getElementById('activeSignalsCount').textContent = activeSignals;
    document.getElementById('profitableSignalsCount').textContent = profitableSignals;
    document.getElementById('winRatePercentage').textContent = winRate.toFixed(1) + '%';
    document.getElementById('totalInvestmentAmount').textContent = '₹' + totalInvestment.toLocaleString();
    document.getElementById('totalCurrentValue').textContent = '₹' + totalCurrentValue.toLocaleString();
    
    var pnlElement = document.getElementById('totalPnlAmount');
    pnlElement.textContent = '₹' + totalPnl.toLocaleString();
    pnlElement.className = 'mb-0 ' + (totalPnl >= 0 ? 'text-success' : 'text-danger');
    
    // Update performer tables
    this.updatePerformerTable('topPerformersTable', topPerformers.slice(0, 5), true);
    this.updatePerformerTable('lowPerformersTable', worstPerformers.slice(0, 5), false);
};

ETFSignalsManager.prototype.updatePerformerTable = function(tableId, data, isPositive) {
    var tbody = document.getElementById(tableId);
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">No data available</td></tr>';
        return;
    }
    
    data.forEach(function(item) {
        var row = document.createElement('tr');
        var pnlClass = isPositive ? 'text-success' : 'text-danger';
        var percentClass = item.percent >= 0 ? 'text-success' : 'text-danger';
        
        row.innerHTML = '<td>' + item.symbol + '</td>' +
                       '<td class="' + pnlClass + '">₹' + item.pnl.toLocaleString() + '</td>' +
                       '<td class="' + percentClass + '">' + item.percent.toFixed(2) + '%</td>';
        tbody.appendChild(row);
    });
};

// Show loading state for performance analysis
ETFSignalsManager.prototype.showPerformanceLoading = function() {
    var loadingElements = [
        'totalSignalsCount',
        'activeSignalsCount', 
        'profitableSignalsCount',
        'winRatePercentage',
        'totalInvestmentAmount',
        'totalCurrentValue',
        'totalPnlAmount'
    ];
    
    loadingElements.forEach(function(elementId) {
        var element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
        }
    });
    
    // Show loading for performer tables
    var topPerformersTable = document.getElementById('topPerformersTable');
    var lowPerformersTable = document.getElementById('lowPerformersTable');
    
    if (topPerformersTable) {
        topPerformersTable.innerHTML = '<tr><td colspan="3" class="text-center text-muted"><i class="fas fa-spinner fa-spin me-2"></i>Loading...</td></tr>';
    }
    
    if (lowPerformersTable) {
        lowPerformersTable.innerHTML = '<tr><td colspan="3" class="text-center text-muted"><i class="fas fa-spinner fa-spin me-2"></i>Loading...</td></tr>';
    }
};

// Global pagination functions
window.goToPage = function(page) {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.currentPage = page;
        window.etfSignalsManager.updateDisplayedSignals();
        window.etfSignalsManager.renderSignalsTable();
        window.etfSignalsManager.updatePagination();
    }
};

window.changeItemsPerPage = function(newPerPage) {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.itemsPerPage = parseInt(newPerPage);
        window.etfSignalsManager.currentPage = 1;
        window.etfSignalsManager.updateDisplayedSignals();
        window.etfSignalsManager.renderSignalsTable();
        window.etfSignalsManager.updatePagination();
    }
};

// Initialize ETF Signals Manager when DOM is ready
window.etfSignalsManager = new ETFSignalsManager();

