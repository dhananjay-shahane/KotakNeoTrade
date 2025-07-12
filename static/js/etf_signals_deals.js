// ETF Signals Deals Manager - ES5 Compatible
function ETFSignalsManager() {
    this.signals = [];
    this.filteredSignals = [];
    this.currentPage = 1;
    this.pageSize = 50;
    this.selectedColumns = [
        "etf",
        "thirty",
        "dh",
        "date",
        "pos",
        "qty",
        "ep",
        "cmp",
        "change_pct",
        "inv",
        "tp",
        "tva",
        "tpr",
        "pl",
        "ed",
        "exp",
        "pr",
        "pp",
        "iv",
        "ip",
        "nt",
        "qt",
        "seven",
        "change2",
        "actions",
    ];
    this.columnTitles = {
        etf: "ETF Symbol",
        thirty: "30 Day",
        dh: "Days Held",
        date: "Entry Date",
        pos: "Position",
        qty: "Quantity",
        ep: "Entry Price",
        cmp: "Current Price",
        change_pct: "% Change",
        inv: "Investment",
        tp: "Target Price",
        tva: "Target Value",
        tpr: "Target Return",
        pl: "P&L",
        ed: "Entry Date",
        exp: "Expiry",
        pr: "Price Range",
        pp: "Performance",
        iv: "IV",
        ip: "Intraday %",
        nt: "Notes",
        qt: "Quote Time",
        seven: "7 Day",
        change2: "% Change",
        actions: "Actions",
    };
    this.init();
}

ETFSignalsManager.prototype.init = function () {
    this.loadSignals();
    this.setupEventListeners();
    this.initializeColumnSettings();
};

ETFSignalsManager.prototype.setupEventListeners = function () {
    var self = this;

    // Auto refresh functionality
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
};

ETFSignalsManager.prototype.loadSignals = function() {
    var self = this;
    try {
        // Load ETF signals data from API
        var xhr = new XMLHttpRequest();
        xhr.open('GET', '/api/etf-signals-data?page=1&page_size=50', true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    var data = JSON.parse(xhr.responseText);
                    if (data.data) {
                        self.signals = data.data || [];
                        self.filteredSignals = self.signals.slice();
                        self.renderSignalsTable();
                        self.updatePagination();
                        console.log('✓ Loaded', self.signals.length, 'ETF signals');
                    } else {
                        self.showError('No ETF signals data found');
                    }
                } else {
                    self.showError('Failed to load ETF signals data');
                }
            }
        };
        xhr.send();
    } catch (error) {
        console.error('Error loading signals:', error);
        this.showError('Failed to load signals data');
    }
};

ETFSignalsManager.prototype.renderSignalsTable = function () {
    var tbody = document.getElementById("signalsTableBody");
    if (!tbody) return;

    var startIndex = (this.currentPage - 1) * this.pageSize;
    var endIndex = startIndex + this.pageSize;
    var pageSignals = this.filteredSignals.slice(startIndex, endIndex);

    tbody.innerHTML = "";

    if (pageSignals.length === 0) {
        var row = document.createElement("tr");
        row.innerHTML =
            '<td colspan="' +
            this.selectedColumns.length +
            '" class="text-center py-4">' +
            '<i class="fas fa-chart-line fa-3x mb-3 text-primary"></i>' +
            '<h6 class="text-light">No ETF Signals Found</h6>' +
            '<p class="text-muted mb-0">No ETF trading signals available</p>' +
            '<small class="text-muted">Signals will appear here when available</small>' +
            "</td>";
        tbody.appendChild(row);
        return;
    }

    var self = this;
    pageSignals.forEach(function (signal) {
        var row = document.createElement("tr");

        self.selectedColumns.forEach(function (columnKey) {
            var cell = document.createElement("td");
            cell.className = "text-center";
            cell.style.padding = "4px 3px";
            cell.style.border = "1px solid var(--border-color)";
            cell.style.fontSize = "0.75rem";

            var cellContent = "";
            var bgColor = "";

            switch (columnKey) {
                case "etf":
                    // Display ETF symbol prominently
                    cellContent =
                        "<strong>" +
                        (signal.symbol || signal.etf || "") +
                        "</strong>";
                    break;
                case "thirty":
                    cellContent = signal.thirty || "0%";
                    var thirtyVal = parseFloat(
                        (signal.thirty || "0%").replace("%", ""),
                    );
                    if (thirtyVal > 0) cell.className += " profit";
                    else if (thirtyVal < 0) cell.className += " loss";
                    break;
                case "dh":
                    cellContent = signal.dh || "0";
                    break;
                case "date":
                    cellContent = signal.date || "";
                    break;
                case "pos":
                    if (signal.pos === 1) {
                        cellContent =
                            '<span class="badge bg-success">1 (OPEN)</span>';
                    } else {
                        cellContent =
                            '<span class="badge bg-secondary">0 (CLOSED)</span>';
                    }
                    break;
                case "qty":
                    cellContent = signal.qty || 0;
                    break;
                case "ep":
                    cellContent = "₹" + (signal.ep || 0).toFixed(2);
                    break;
                case "cmp":
                    cellContent =
                        "₹" + (signal.cmp || signal.ep || 0).toFixed(2);
                    if (
                        signal.data_source &&
                        signal.data_source.includes("KOTAK_NEO")
                    ) {
                        cellContent +=
                            ' <span class="badge bg-success badge-sm">KN</span>';
                    }
                    break;
                case "change_pct":
                    var changePct = signal.change_pct || 0;
                    cellContent = changePct.toFixed(2) + "%";
                    if (changePct > 0) cell.className += " profit";
                    else if (changePct < 0) cell.className += " loss";
                    break;
                case "inv":
                    cellContent = "₹" + (signal.inv || 0).toFixed(0);
                    break;
                case "tp":
                    cellContent = "₹" + (signal.tp || 0).toFixed(2);
                    break;
                case "tva":
                    cellContent = "₹" + (signal.tva || 0).toFixed(0);
                    break;
                case "tpr":
                    cellContent = "₹" + (signal.tpr || 0).toFixed(0);
                    cell.className += " profit";
                    break;
                case "pl":
                    var pnl = signal.pl || 0;
                    cellContent = "₹" + pnl.toFixed(0);
                    if (pnl >= 0) cell.className += " profit";
                    else cell.className += " loss";
                    break;
                case "ed":
                    cellContent = signal.ed || "";
                    break;
                case "exp":
                    cellContent = signal.exp || "";
                    break;
                case "pr":
                    cellContent = signal.pr || "0%";
                    break;
                case "pp":
                    cellContent = signal.pp || "★";
                    break;
                case "iv":
                    cellContent = signal.iv || 0;
                    break;
                case "ip":
                    cellContent = signal.ip || "0%";
                    var ipVal = parseFloat(
                        (signal.ip || "0%").replace("%", ""),
                    );
                    if (ipVal > 0) cell.className += " profit";
                    else if (ipVal < 0) cell.className += " loss";
                    break;
                case "nt":
                    cellContent = "<small>" + (signal.nt || "") + "</small>";
                    break;
                case "qt":
                    cellContent = "<small>" + (signal.qt || "") + "</small>";
                    break;
                case "seven":
                    cellContent = signal.seven || "0%";
                    var sevenVal = parseFloat(
                        (signal.seven || "0%").replace("%", ""),
                    );
                    if (sevenVal > 0) cell.className += " profit";
                    else if (sevenVal < 0) cell.className += " loss";
                    break;
                case "change2":
                    var change2 = signal.change2 || 0;
                    cellContent = change2.toFixed(2) + "%";
                    if (change2 > 0) cell.className += " profit";
                    else if (change2 < 0) cell.className += " loss";
                    break;
                case "actions":
                    var signalJson = JSON.stringify(signal).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
                    cellContent =
                        '<button class="btn btn-sm btn-primary" onclick="addDealFromSignal(\'' +
                        (signal.symbol || signal.etf || "") +
                        "', " +
                        "JSON.parse(decodeURIComponent('" + encodeURIComponent(JSON.stringify(signal)) + "'))" +
                        ')">' +
                        "Add Deal</button>";
                    break;
                default:
                    cellContent = signal[columnKey] || "";
            }

            cell.innerHTML = cellContent;
            row.appendChild(cell);
        });

        tbody.appendChild(row);
    });

    this.updateVisibleCount();
};

ETFSignalsManager.prototype.updatePagination = function () {
    var totalPages = Math.ceil(this.filteredSignals.length / this.pageSize);
    var currentPageSpan = document.getElementById("currentPage");
    var totalPagesSpan = document.getElementById("totalPages");
    var prevBtn = document.getElementById("prevBtn");
    var nextBtn = document.getElementById("nextBtn");
    var showingCount = document.getElementById("showingCount");
    var totalCount = document.getElementById("totalCount");

    if (currentPageSpan) currentPageSpan.textContent = this.currentPage;
    if (totalPagesSpan) totalPagesSpan.textContent = totalPages;
    if (prevBtn) prevBtn.disabled = this.currentPage <= 1;
    if (nextBtn) nextBtn.disabled = this.currentPage >= totalPages;

    var startIndex = (this.currentPage - 1) * this.pageSize;
    var endIndex = Math.min(
        startIndex + this.pageSize,
        this.filteredSignals.length,
    );

    if (showingCount)
        showingCount.textContent = Math.min(
            this.pageSize,
            this.filteredSignals.length,
        );
    if (totalCount) totalCount.textContent = this.filteredSignals.length;
};

ETFSignalsManager.prototype.updateVisibleCount = function () {
    var visibleSignalsCount = document.getElementById("visibleSignalsCount");
    if (visibleSignalsCount) {
        visibleSignalsCount.textContent = this.filteredSignals.length;
    }
};

ETFSignalsManager.prototype.startAutoRefresh = function () {
    var self = this;
    this.stopAutoRefresh();
    this.autoRefreshInterval = setInterval(function () {
        self.loadSignals();
    }, 30000); // 30 seconds
};

ETFSignalsManager.prototype.stopAutoRefresh = function () {
    if (this.autoRefreshInterval) {
        clearInterval(this.autoRefreshInterval);
        this.autoRefreshInterval = null;
    }
};

ETFSignalsManager.prototype.initializeColumnSettings = function () {
    // Initialize column settings if needed
    console.log("Column settings initialized");
};

ETFSignalsManager.prototype.showError = function (message) {
    console.error(message);
    var tbody = document.getElementById("signalsTableBody");
    if (tbody) {
        tbody.innerHTML =
            '<tr><td colspan="25" class="text-center text-danger">' +
            message +
            "</td></tr>";
    }
};

// Global functions for button handlers
function applyFilters() {
    if (!window.etfSignalsManager) return;

    var orderType = document.getElementById("orderTypeFilter");
    var status = document.getElementById("statusFilter");
    var symbol = document.getElementById("symbolFilter");
    var minPnl = document.getElementById("minPnlFilter");
    var maxPnl = document.getElementById("maxPnlFilter");

    var orderTypeValue = orderType ? orderType.value : "";
    var statusValue = status ? status.value : "";
    var symbolValue = symbol ? symbol.value.toLowerCase() : "";
    var minPnlValue = minPnl
        ? parseFloat(minPnl.value) || -Infinity
        : -Infinity;
    var maxPnlValue = maxPnl ? parseFloat(maxPnl.value) || Infinity : Infinity;

    window.etfSignalsManager.filteredSignals =
        window.etfSignalsManager.signals.filter(function (signal) {
            var matchesOrderType =
                !orderTypeValue ||
                (orderTypeValue === "BUY" && signal.pos === 1) ||
                (orderTypeValue === "SELL" && signal.pos === 0);
            var matchesStatus = !statusValue || signal.status === statusValue;
            var matchesSymbol =
                !symbolValue ||
                (signal.symbol || "").toLowerCase().indexOf(symbolValue) !== -1;
            var matchesPnl =
                (signal.pl || 0) >= minPnlValue &&
                (signal.pl || 0) <= maxPnlValue;

            return (
                matchesOrderType && matchesStatus && matchesSymbol && matchesPnl
            );
        });

    window.etfSignalsManager.currentPage = 1;
    window.etfSignalsManager.renderSignalsTable();
    window.etfSignalsManager.updatePagination();
}

function clearFilters() {
    var orderTypeFilter = document.getElementById("orderTypeFilter");
    var statusFilter = document.getElementById("statusFilter");
    var symbolFilter = document.getElementById("symbolFilter");
    var minPnlFilter = document.getElementById("minPnlFilter");
    var maxPnlFilter = document.getElementById("maxPnlFilter");

    if (orderTypeFilter) orderTypeFilter.value = "";
    if (statusFilter) statusFilter.value = "";
    if (symbolFilter) symbolFilter.value = "";
    if (minPnlFilter) minPnlFilter.value = "";
    if (maxPnlFilter) maxPnlFilter.value = "";

    if (window.etfSignalsManager) {
        window.etfSignalsManager.filteredSignals =
            window.etfSignalsManager.signals.slice();
        window.etfSignalsManager.currentPage = 1;
        window.etfSignalsManager.renderSignalsTable();
        window.etfSignalsManager.updatePagination();
    }
}

function refreshSignals() {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.loadSignals();
    }
}

function previousPage() {
    if (window.etfSignalsManager && window.etfSignalsManager.currentPage > 1) {
        window.etfSignalsManager.currentPage--;
        window.etfSignalsManager.renderSignalsTable();
        window.etfSignalsManager.updatePagination();
    }
}

function nextPage() {
    if (window.etfSignalsManager) {
        var totalPages = Math.ceil(
            window.etfSignalsManager.filteredSignals.length /
                window.etfSignalsManager.pageSize,
        );
        if (window.etfSignalsManager.currentPage < totalPages) {
            window.etfSignalsManager.currentPage++;
            window.etfSignalsManager.renderSignalsTable();
            window.etfSignalsManager.updatePagination();
        }
    }
}

function setRefreshInterval(interval, text) {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.stopAutoRefresh();
        if (interval > 0) {
            window.etfSignalsManager.autoRefreshInterval = setInterval(
                function () {
                    window.etfSignalsManager.loadSignals();
                },
                interval,
            );
        }
        var currentIntervalSpan = document.getElementById("currentInterval");
        if (currentIntervalSpan) {
            currentIntervalSpan.textContent = text;
        }
    }
}

// Add Deal functionality
function addDealFromSignal(symbol, signalData) {
    try {
        var signal =
            typeof signalData === "string"
                ? JSON.parse(signalData)
                : signalData;

        // Get the current price for confirmation
        var currentPrice = signal.cmp === "--" ? signal.ep : signal.cmp;
        
        if (
            !confirm(
                "Add deal for " +
                    symbol +
                    " at ₹" +
                    (currentPrice || 0).toFixed(2) +
                    "?"
            )
        ) {
            return;
        }

        console.log("Creating deal from signal:", signal);

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
                            showMessage(
                                "✓ Deal created successfully for " + symbol + 
                                " - Deal ID: " + response.deal_id,
                                "success"
                            );
                            
                            // Optionally redirect to deals page after 2 seconds
                            setTimeout(function() {
                                if (confirm("View your deals?")) {
                                    window.location.href = "/deals";
                                }
                            }, 2000);
                        } else {
                            showMessage(
                                "Failed to create deal: " + (response.error || response.message || "Unknown error"),
                                "error"
                            );
                        }
                    } catch (parseError) {
                        console.error("Failed to parse response:", parseError);
                        showMessage("Invalid response from server", "error");
                    }
                } else {
                    showMessage(
                        "Failed to create deal. Server error: " + xhr.status,
                        "error"
                    );
                }
            }
        };

        xhr.send(
            JSON.stringify({
                signal_data: signal
            })
        );
    } catch (error) {
        console.error("Error adding deal:", error);
        showMessage("Error adding deal: " + error.message, "error");
    }
}

function showMessage(message, type) {
    var alertClass = type === "success" ? "alert-success" : "alert-danger";
    var alertHtml =
        '<div class="alert ' +
        alertClass +
        ' alert-dismissible fade show" role="alert">' +
        message +
        '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
        "</div>";

    var container = document.querySelector(".container-fluid") || document.body;
    var alertDiv = document.createElement("div");
    alertDiv.innerHTML = alertHtml;
    container.insertBefore(alertDiv, container.firstChild);

    setTimeout(function () {
        var alert = document.querySelector(".alert");
        if (alert) {
            alert.remove();
        }
    }, 5000);
}

function exportSignals() {
    if (window.etfSignalsManager && window.etfSignalsManager.signals) {
        var csvContent = "data:text/csv;charset=utf-8,";
        csvContent +=
            "ETF,Position,Quantity,Entry Price,Current Price,P&L,Investment\n";

        window.etfSignalsManager.signals.forEach(function (signal) {
            var row = [
                signal.symbol || signal.etf || "",
                signal.pos === 1 ? "LONG" : "SHORT",
                signal.qty || 0,
                signal.ep || 0,
                signal.cmp || 0,
                signal.pl || 0,
                signal.inv || 0,
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

function addDeal(symbol, price) {
    // Show confirmation dialog
    if (!confirm("Add deal for " + symbol + " at ₹" + price.toFixed(2) + "?")) {
        return;
    }

    // Create deal data for API
    var dealData = {
        symbol: symbol,
        position_type: "LONG",
        quantity: 1,
        entry_price: price,
        current_price: price,
        target_price: price * 1.05,
        stop_loss: price * 0.95,
        deal_type: "SIGNAL",
        notes: "Added from ETF signals",
    };

    // Send POST request to create deal in database
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/etf/create-deal", true);
    xhr.setRequestHeader("Content-Type", "application/json");

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            console.log("API Response Status:", xhr.status);
            console.log("API Response Text:", xhr.responseText);
            if (xhr.status === 200) {
                try {
                    var response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        // Show success message
                        alert("Deal created successfully for " + symbol + "!");

                        // Check if deal with same symbol already exists in localStorage to avoid duplicates
                        var userDeals = JSON.parse(
                            localStorage.getItem("userDeals") || "[]",
                        );
                        var existingDealIndex = userDeals.findIndex(
                            function (deal) {
                                return (
                                    deal.symbol === symbol &&
                                    Math.abs(
                                        parseFloat(deal.ep) - parseFloat(price),
                                    ) < 0.01
                                );
                            },
                        );

                        // Only add if no duplicate exists
                        if (existingDealIndex === -1) {
                            var newDeal = {
                                id: response.deal_id || "deal_" + Date.now(),
                                symbol: symbol,
                                pos: 1, // LONG position
                                qty: 1,
                                ep: price,
                                cmp: price,
                                pl: 0,
                                change_pct: 0,
                                inv: price * 1,
                                tp: price * 1.05,
                                tva: price * 1.05 * 1,
                                tpr: price * 0.05,
                                date: new Date().toISOString().split("T")[0],
                                status: "ACTIVE",
                                thirty: "0%",
                                dh: 0,
                                ed: new Date().toISOString().split("T")[0],
                                pr: "0%",
                                pp: "★★",
                                iv: "Medium",
                                ip: "0%",
                                nt: "Added from ETF signals",
                                qt: new Date().toLocaleTimeString("en-GB", {
                                    hour: "2-digit",
                                    minute: "2-digit",
                                }),
                                seven: "0%",
                                change2: 0,
                            };
                            userDeals.unshift(newDeal);
                            localStorage.setItem(
                                "userDeals",
                                JSON.stringify(userDeals),
                            );
                        }

                        // Trigger storage event to update deals page if it's open in another tab
                        var storageEvent = document.createEvent("Event");
                        storageEvent.initEvent("storage", true, true);
                        storageEvent.key = "userDeals";
                        storageEvent.newValue = JSON.stringify(userDeals);
                        window.dispatchEvent(storageEvent);

                        // Navigate to deals page with symbol and price parameters
                        setTimeout(function () {
                            window.location.href =
                                "/deals?symbol=" +
                                encodeURIComponent(symbol) +
                                "&price=" +
                                price.toFixed(2);
                        }, 1000);
                    } else {
                        alert(
                            "Failed to create deal: " +
                                (response.message || "Unknown error"),
                        );
                    }
                } catch (parseError) {
                    console.error("Failed to parse API response:", parseError);
                    alert("Invalid response from server");
                }
            } else {
                console.error("API call failed with status:", xhr.status);
                alert(
                    "Failed to create deal. Server returned status: " +
                        xhr.status,
                );
            }
        }
    };

    xhr.send(JSON.stringify(dealData));
}

// Initialize when DOM is ready
document.addEventListener("DOMContentLoaded", function () {
    if (typeof window.etfSignalsManager === "undefined") {
        window.etfSignalsManager = new ETFSignalsManager();
    }
});

// Fallback initialization
if (
    document.readyState === "complete" ||
    document.readyState === "interactive"
) {
    if (typeof window.etfSignalsManager === "undefined") {
        window.etfSignalsManager = new ETFSignalsManager();
    }
}
