// Market Watch Functionality

// Market watch data storage
var userMarketWatchData = [];
var defaultMarketWatchData = [];
var userIdCounter = 1;

// Gradient Background Color Function for percentage values
function getGradientBackgroundColor(value) {
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
}

// Add symbol to user list from default list
function addToUserList(symbol) {
    // Make API call to add symbol to user's CSV watchlist
    fetch("/api/market-watch/user-symbols", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            symbol: symbol,
        }),
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                // Reload the user watchlist
                loadUserWatchlist();

                Swal.fire({
                    icon: "success",
                    title: "Symbol Added",
                    text: data.message,
                    background: "#1a1a1a",
                    color: "#fff",
                    timer: 2000,
                    showConfirmButton: false,
                });
            } else {
                Swal.fire({
                    icon: "error",
                    title: "Error",
                    text: data.error || "Failed to add symbol to watchlist",
                    background: "#1a1a1a",
                    color: "#fff",
                });
            }
        })
        .catch((error) => {
            console.error("Error adding symbol to watchlist:", error);
            Swal.fire({
                icon: "error",
                title: "Error",
                text: "Failed to add symbol. Please try again.",
                background: "#1a1a1a",
                color: "#fff",
            });
        });
}

// Advanced symbol search and selection variables
var selectedSymbolData = null;
var searchTimeout = null;
var filterOptions = { companies: [], sectors: [], sub_sectors: [] };

// Initialize advanced symbol modal
function initializeAdvancedSymbolModal() {
    // Load filter options when modal opens
    document
        .getElementById("addSymbolModal")
        .addEventListener("shown.bs.modal", function () {
            loadFilterOptions();
            clearSymbolSelection();
            // Show initial symbols based on default Nifty selection
            setTimeout(() => {
                updateSymbolSearch();
            }, 500);
        });
}

// Load filter options from API
function loadFilterOptions() {
    fetch("/api/symbols/filters")
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                filterOptions = data;
                populateFilterDropdowns();
            }
        })
        .catch((error) => {
            console.error("Error loading filter options:", error);
        });
}

// Populate filter dropdowns
function populateFilterDropdowns() {
    // Populate company filter
    const companySelect = document.getElementById("companyFilter");
    companySelect.innerHTML = '<option value="">All Companies</option>';
    filterOptions.companies.slice(0, 50).forEach((company) => {
        const option = document.createElement("option");
        option.value = company;
        option.textContent = company;
        companySelect.appendChild(option);
    });

    // Populate sector filter
    const sectorSelect = document.getElementById("sectorFilter");
    sectorSelect.innerHTML = '<option value="">All Sectors</option>';
    filterOptions.sectors.forEach((sector) => {
        const option = document.createElement("option");
        option.value = sector;
        option.textContent = sector;
        sectorSelect.appendChild(option);
    });

    // Populate sub sector filter
    const subSectorSelect = document.getElementById("subSectorFilter");
    subSectorSelect.innerHTML = '<option value="">All Sub Sectors</option>';
    filterOptions.sub_sectors.forEach((subSector) => {
        const option = document.createElement("option");
        option.value = subSector;
        option.textContent = subSector;
        subSectorSelect.appendChild(option);
    });
}

// Search symbols with current filters
function searchSymbols() {
    const searchInput = document.getElementById("symbolSearchInput");
    const searchTerm = searchInput.value.trim();

    // Clear previous timeout
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }

    // Check if we have any filters selected
    const hasFilters =
        document.getElementById("companyFilter").value ||
        document.getElementById("sectorFilter").value ||
        document.getElementById("subSectorFilter").value;

    // Show suggestions if search term is >= 1 char OR filters are selected
    if (searchTerm.length < 1 && !hasFilters) {
        hideSuggestions();
        return;
    }

    // Debounce search
    searchTimeout = setTimeout(() => {
        performSymbolSearch(searchTerm || "*");
    }, 300);
}

// Perform actual symbol search
function performSymbolSearch(searchTerm) {
    // Use empty string instead of '*' for wildcard search
    const finalSearchTerm = searchTerm === "*" ? "" : searchTerm;

    const params = new URLSearchParams({
        q: finalSearchTerm,
        nifty: document.getElementById("niftyCheck").checked ? "1" : "0",
        nifty_500: document.getElementById("nifty500Check").checked ? "1" : "0",
        etf: document.getElementById("etfCheck").checked ? "1" : "0",
        company: document.getElementById("companyFilter").value,
        sector: document.getElementById("sectorFilter").value,
        sub_sector: document.getElementById("subSectorFilter").value,
        limit: "15",
    });

    console.log("Searching with params:", params.toString());

    fetch(`/api/symbols/search?${params.toString()}`)
        .then((response) => response.json())
        .then((data) => {
            console.log("Search response:", data);
            if (data.success) {
                displaySymbolSuggestions(data.symbols);
            } else {
                console.error("Search failed:", data.error);
                displaySymbolSuggestions([]);
            }
        })
        .catch((error) => {
            console.error("Search error:", error);
            displaySymbolSuggestions([]);
        });
}

// Display symbol suggestions
function displaySymbolSuggestions(symbols) {
    const suggestionsDiv = document.getElementById("symbolSuggestions");

    if (symbols.length === 0) {
        suggestionsDiv.innerHTML =
            '<div class="p-3 text-muted text-center"><i class="fas fa-search me-2"></i>No symbols found matching your criteria</div>';
        suggestionsDiv.classList.remove("d-none");
        return;
    }

    let html = "";
    symbols.forEach((symbol) => {
        const categories = [];
        if (symbol.categories.nifty)
            categories.push('<span class="badge bg-success me-1">Nifty</span>');
        if (symbol.categories.nifty_500)
            categories.push(
                '<span class="badge bg-primary me-1">Nifty 500</span>',
            );
        if (symbol.categories.etf)
            categories.push('<span class="badge bg-warning me-1">ETF</span>');

        html += `
            <div class="suggestion-item p-3 border-bottom border-secondary" 
                 onclick="selectSymbol('${symbol.symbol}')" 
                 style="cursor: pointer; transition: background-color 0.2s;"
                 onmouseover="this.style.backgroundColor='#495057'" 
                 onmouseout="this.style.backgroundColor='transparent'">
                <div class="d-flex justify-content-between align-items-start">
                    <div style="flex: 1;">
                        <div class="d-flex align-items-center mb-1">
                            <strong class="text-light me-2" style="font-size: 14px;">${symbol.symbol}</strong>
                            ${categories.join("")}
                        </div>
                        <div class="text-muted small mb-1">${symbol.company || "N/A"}</div>
                        <div class="text-muted small">${symbol.sector || "N/A"} • ${symbol.sub_sector || "N/A"}</div>
                    </div>
                    <div class="text-end">
                        <i class="fas fa-plus-circle text-success" style="font-size: 18px;"></i>
                    </div>
                </div>
            </div>
        `;
    });

    suggestionsDiv.innerHTML = html;
    suggestionsDiv.classList.remove("d-none");

    console.log("Displayed", symbols.length, "symbol suggestions");
}

// Hide suggestions
function hideSuggestions() {
    document.getElementById("symbolSuggestions").classList.add("d-none");
}

// Select a symbol from suggestions
function selectSymbol(symbol) {
    fetch(`/api/symbols/${symbol}/details`)
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                selectedSymbolData = data.symbol;
                displaySelectedSymbolDetails();
                hideSuggestions();
                document.getElementById("symbolSearchInput").value = symbol;
                document.getElementById("addSymbolBtn").disabled = false;
            }
        })
        .catch((error) => {
            console.error("Error getting symbol details:", error);
        });
}

// Display selected symbol details
function displaySelectedSymbolDetails() {
    if (!selectedSymbolData) return;

    document.getElementById("detailSymbol").textContent =
        selectedSymbolData.symbol;
    document.getElementById("detailCompany").textContent =
        selectedSymbolData.company;
    document.getElementById("detailSector").textContent =
        selectedSymbolData.sector;
    document.getElementById("detailSubSector").textContent =
        selectedSymbolData.sub_sector;

    // Display categories
    const categories = [];
    if (selectedSymbolData.categories.nifty)
        categories.push('<span class="badge bg-success">Nifty</span>');
    if (selectedSymbolData.categories.nifty_500)
        categories.push('<span class="badge bg-primary">Nifty 500</span>');
    if (selectedSymbolData.categories.etf)
        categories.push('<span class="badge bg-warning">ETF</span>');

    document.getElementById("detailCategories").innerHTML =
        categories.join(" ");
    document.getElementById("selectedSymbolDetails").classList.remove("d-none");
}

// Update symbol search when filters change
function updateSymbolSearch() {
    const searchInput = document.getElementById("symbolSearchInput");
    const searchTerm = searchInput.value.trim();

    // Show suggestions even with empty search if filters are selected
    const hasFilters =
        document.getElementById("companyFilter").value ||
        document.getElementById("sectorFilter").value ||
        document.getElementById("subSectorFilter").value;

    if (searchTerm.length >= 1 || hasFilters) {
        performSymbolSearch(searchTerm || "*");
    } else {
        hideSuggestions();
    }
}

// Clear symbol selection
function clearSymbolSelection() {
    selectedSymbolData = null;
    document.getElementById("selectedSymbolDetails").classList.add("d-none");
    document.getElementById("addSymbolBtn").disabled = true;
    document.getElementById("symbolSearchInput").value = "";
    hideSuggestions();
}

// Submit advanced add symbol
function submitAdvancedAddSymbol() {
    if (!selectedSymbolData) {
        Swal.fire({
            icon: "error",
            title: "No Symbol Selected",
            text: "Please select a symbol first.",
            background: "#1a1a1a",
            color: "#fff",
        });
        return;
    }

    // Check if we're adding to a custom watchlist
    if (window.currentWatchlistName) {
        // Add to custom watchlist
        fetch(`/api/market-watch/watchlists/${encodeURIComponent(window.currentWatchlistName)}/symbols`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: selectedSymbolData.symbol
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Reload the specific watchlist
                loadWatchlistMarketData(window.currentWatchlistName);
                
                Swal.fire({
                    icon: 'success',
                    title: 'Symbol Added',
                    text: data.message,
                    background: '#1a1a1a',
                    color: '#fff',
                    timer: 2000,
                    showConfirmButton: false
                });
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: data.error || 'Failed to add symbol to watchlist',
                    background: '#1a1a1a',
                    color: '#fff'
                });
            }
        })
        .catch(error => {
            console.error('Error adding symbol to watchlist:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'Failed to add symbol. Please try again.',
                background: '#1a1a1a',
                color: '#fff'
            });
        });
        
        // Clear current watchlist name
        window.currentWatchlistName = null;
    } else {
        // Use the same API call as the simple add function for default user list
        addToUserList(selectedSymbolData.symbol);
    }

    // Close modal and clear selection
    var modal = bootstrap.Modal.getInstance(
        document.getElementById("addSymbolModal"),
    );
    modal.hide();
    clearSymbolSelection();
}

// Legacy function for backward compatibility
function submitAddSymbol() {
    submitAdvancedAddSymbol();
}

// Remove symbol from user list
function removeFromUserList(id) {
    var symbol = userMarketWatchData.find(function (item) {
        return item.id === id;
    });

    if (!symbol) return;

    Swal.fire({
        title: "Remove Symbol",
        text:
            "Are you sure you want to remove " +
            symbol.symbol +
            " from your market watch?",
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#d33",
        cancelButtonColor: "#6c757d",
        confirmButtonText: "Yes, remove it!",
        background: "#1a1a1a",
        color: "#fff",
    }).then((result) => {
        if (result.isConfirmed) {
            // Make API call to remove symbol from CSV
            fetch("/api/market-watch/user-symbols", {
                method: "DELETE",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    symbol: symbol.symbol,
                }),
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success) {
                        // Reload the user watchlist
                        loadUserWatchlist();

                        Swal.fire({
                            icon: "success",
                            title: "Removed",
                            text: data.message,
                            background: "#1a1a1a",
                            color: "#fff",
                            timer: 2000,
                            showConfirmButton: false,
                        });
                    } else {
                        Swal.fire({
                            icon: "error",
                            title: "Error",
                            text: data.error || "Failed to remove symbol",
                            background: "#1a1a1a",
                            color: "#fff",
                        });
                    }
                })
                .catch((error) => {
                    console.error(
                        "Error removing symbol from watchlist:",
                        error,
                    );
                    Swal.fire({
                        icon: "error",
                        title: "Error",
                        text: "Failed to remove symbol. Please try again.",
                        background: "#1a1a1a",
                        color: "#fff",
                    });
                });
        }
    });
}

// Generate sample market data for a symbol
function generateSymbolData(symbol, id) {
    var basePrice = Math.random() * 3000 + 100; // Random price between 100-3100
    var change = (Math.random() - 0.5) * 100; // Random change between -50 to +50
    var changePercent = (change / basePrice) * 100;

    var sevenDayPrice = basePrice - Math.random() * 50;
    var thirtyDayPrice = basePrice - Math.random() * 100;
    var sevenDayPercent = ((basePrice - sevenDayPrice) / sevenDayPrice) * 100;
    var thirtyDayPercent =
        ((basePrice - thirtyDayPrice) / thirtyDayPrice) * 100;

    return {
        id: id,
        symbol: symbol,
        cmp: basePrice.toFixed(2),
        change: change.toFixed(2),
        changePercent: changePercent.toFixed(2),
        sevenDay: sevenDayPrice.toFixed(2),
        thirtyDay: thirtyDayPrice.toFixed(2),
        sevenDayPercent: sevenDayPercent.toFixed(2),
        thirtyDayPercent: thirtyDayPercent.toFixed(2),
        cpl: change.toFixed(2),
    };
}

// Update default market watch table
function updateDefaultMarketWatchTable() {
    var tableBody = document.getElementById("defaultMarketWatchTableBody");

    if (defaultMarketWatchData.length === 0) {
        tableBody.innerHTML = `
            <tr class="no-data-row">
                <td colspan="10" class="text-center text-muted py-4">
                    <i class="fas fa-chart-line fa-2x mb-2"></i><br>
                    Loading default market watch data...
                </td>
            </tr>
        `;
        return;
    }

    var html = "";
    defaultMarketWatchData.forEach(function (item) {
        // Get gradient styles for percentage columns
        var change7dStyle = getGradientBackgroundColor(item.change_7d_pct);
        var change30dStyle = getGradientBackgroundColor(item.change_30d_pct);
        var changePctStyle = getGradientBackgroundColor(item.change_pct);

        html += `
            <tr>
                <td>${item.id}</td>
                <td><strong>${item.symbol}</strong></td>
                <td>${item.price_7d || "--"}</td>
                <td>${item.price_30d || "--"}</td>
                <td style="${change7dStyle}">${item.change_7d_pct || "--"}</td>
                <td style="${change30dStyle}">${item.change_30d_pct || "--"}</td>
                <td><strong>${item.cmp || "--"}</strong></td>
                <td style="${changePctStyle}">${item.change_pct || "--"}</td>
                <td>${item.change_val || "--"}</td>
                <td>
                    <button class="btn btn-sm btn-success" onclick="addToUserListFromDefault('${item.symbol}')">
                        <i class="fas fa-plus"></i>
                    </button>
                </td>
            </tr>
        `;
    });

    tableBody.innerHTML = html;
}

// Update user counts
function updateUserCounts() {
    var count = userMarketWatchData.length;
    document.getElementById("userCount").textContent = count;
    document.getElementById("userTotalCount").textContent = count;
    document.getElementById("userShowingCount").textContent = count;
}

// Update default counts
function updateDefaultCounts() {
    var count = defaultMarketWatchData.length;
    document.getElementById("defaultCount").textContent = count;
    document.getElementById("defaultTotalCount").textContent = count;
    document.getElementById("defaultShowingCount").textContent = count;
}

// Add symbol to user list from default market watch
function addToUserListFromDefault(symbol) {
    // Use the existing addToUserList function
    addToUserList(symbol);
}

// Load default market watch data from API with async/await and loader
async function loadDefaultMarketWatch() {
    console.log("Loading default market watch data...");

    // Show loading state
    showDefaultTableLoader();

    try {
        const response = await fetch(
            "/api/market-watch/default-symbols-with-data",
        );
        const data = await response.json();

        if (data.success) {
            defaultMarketWatchData = data.symbols;
            updateDefaultMarketWatchTable();
            updateDefaultCounts();
            console.log(`✓ Loaded ${data.symbols.length} default symbols`);
        } else {
            console.error("Error loading default market watch:", data.error);
            showErrorInDefaultTable(
                "Failed to load default market watch data: " + data.error,
            );
        }
    } catch (error) {
        console.error("Network error loading default market watch:", error);
        showErrorInDefaultTable("Network error loading market data");
    }
}

// Show loader for default table
function showDefaultTableLoader() {
    var tableBody = document.getElementById("defaultMarketWatchTableBody");
    tableBody.innerHTML = `
        <tr class="loading-row">
            <td colspan="10" class="text-center py-4">
                <div class="d-flex justify-content-center align-items-center">
                    <div class="spinner-border text-primary me-2" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <span class="text-muted">Loading default market watch data...</span>
                </div>
            </td>
        </tr>
    `;
}

// Show loader for user table
function showUserTableLoader() {
    var tableBody = document.getElementById("userMarketWatchTableBody");
    if (tableBody) {
        tableBody.innerHTML = `
            <tr class="loading-row">
                <td colspan="10" class="text-center py-4">
                    <div class="d-flex justify-content-center align-items-center">
                        <div class="spinner-border text-success me-2" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <span class="text-muted">Loading your market watch data...</span>
                    </div>
                </td>
            </tr>
        `;
    }
}

// Show error in default table
function showErrorInDefaultTable(message) {
    var tableBody = document.getElementById("defaultMarketWatchTableBody");
    tableBody.innerHTML = `
        <tr class="error-row">
            <td colspan="10" class="text-center py-4">
                <div class="d-flex justify-content-center align-items-center text-danger">
                    <i class="fas fa-exclamation-triangle fa-2x me-2"></i>
                    <span>${message}</span>
                </div>
            </td>
        </tr>
    `;
}

// Show error in user table
function showErrorInUserTable(message) {
    var tableBody = document.getElementById("userMarketWatchTableBody");
    if (tableBody) {
        tableBody.innerHTML = `
            <tr class="error-row">
                <td colspan="10" class="text-center py-4">
                    <div class="d-flex justify-content-center align-items-center text-danger">
                        <i class="fas fa-exclamation-triangle fa-2x me-2"></i>
                        <span>${message}</span>
                    </div>
                </td>
            </tr>
        `;
    }
}

// Refresh functions
function refreshDefaultList() {
    console.log("Refreshing default market watch list...");
    // Reload default market watch data from API
    loadDefaultMarketWatch();

    Swal.fire({
        icon: "success",
        title: "Refreshed",
        text: "Default market watch list has been refreshed with latest market data.",
        background: "#1a1a1a",
        color: "#fff",
        timer: 1500,
        showConfirmButton: false,
    });
}

function refreshUserList() {
    console.log("Refreshing user market watch list...");
    // Reload user watchlist from API
    loadUserWatchlist();

    Swal.fire({
        icon: "success",
        title: "Refreshed",
        text: "Your market watch list has been refreshed with latest data.",
        background: "#1a1a1a",
        color: "#fff",
        timer: 1500,
        showConfirmButton: false,
    });
}

function refreshMarketWatch() {
    refreshDefaultList();
    refreshUserList();
}

// Pagination functions for user list
function previousUserPage() {
    console.log("Previous user page");
}

function nextUserPage() {
    console.log("Next user page");
}

// Export function
function exportMarketWatch() {
    var data = {
        defaultList: "Default market watch data",
        userList: userMarketWatchData,
    };

    var dataStr = JSON.stringify(data, null, 2);
    var dataBlob = new Blob([dataStr], { type: "application/json" });
    var url = URL.createObjectURL(dataBlob);
    var link = document.createElement("a");
    link.href = url;
    link.download = "market_watch_export.json";
    link.click();
    URL.revokeObjectURL(url);
}

// Load user watchlist data from API (missing function)
function loadUserWatchlist() {
    console.log("Loading user watchlist data...");
    
    // Show loading state
    showUserTableLoader();
    
    fetch("/api/market-watch/user-symbols-with-data")
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                userMarketWatchData = data.symbols;
                updateUserMarketWatchTable();
                updateUserCounts();
                console.log(`✓ Loaded ${data.symbols.length} user symbols`);
            } else {
                console.error("Error loading user watchlist:", data.error);
                showErrorInUserTable(
                    "Failed to load your watchlist: " + data.error,
                );
            }
        })
        .catch((error) => {
            console.error("Network error loading user watchlist:", error);
            showErrorInUserTable("Network error loading your watchlist");
        });
}

// Custom Watchlist Management Functions
window.createNewWatchlist = function() {
    const nameInput = document.getElementById('newListNameInput');
    const listName = nameInput.value.trim();
    
    if (!listName) {
        Swal.fire({
            icon: 'error',
            title: 'Invalid Input',
            text: 'Please enter a valid list name.',
            background: '#1a1a1a',
            color: '#fff'
        });
        return;
    }
    
    if (listName.length > 50) {
        Swal.fire({
            icon: 'error',
            title: 'Name Too Long',
            text: 'List name must be 50 characters or less.',
            background: '#1a1a1a',
            color: '#fff'
        });
        return;
    }
    
    // Create watchlist via API
    fetch('/api/market-watch/watchlists', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: listName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Clear input
            nameInput.value = '';
            
            // Reload custom watchlists
            loadCustomWatchlists();
            
            Swal.fire({
                icon: 'success',
                title: 'Success',
                text: data.message,
                background: '#1a1a1a',
                color: '#fff',
                timer: 2000,
                showConfirmButton: false
            });
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: data.error || 'Failed to create watchlist',
                background: '#1a1a1a',
                color: '#fff'
            });
        }
    })
    .catch(error => {
        console.error('Error creating watchlist:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Failed to create watchlist. Please try again.',
            background: '#1a1a1a',
            color: '#fff'
        });
    });
};

// Load and display custom watchlists
window.loadCustomWatchlists = function() {
    console.log('Loading custom watchlists...');
    
    fetch('/api/market-watch/watchlists')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayCustomWatchlists(data.watchlists);
            console.log(`✓ Loaded ${data.watchlists.length} custom watchlists`);
        } else {
            console.error('Error loading custom watchlists:', data.error);
        }
    })
    .catch(error => {
        console.error('Network error loading custom watchlists:', error);
    });
};

// Display custom watchlists in the UI
function displayCustomWatchlists(watchlists) {
    const container = document.getElementById('customWatchlistsContainer');
    
    if (watchlists.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-list fa-2x mb-2"></i><br>
                <p>No custom watchlists created yet.<br>Create your first watchlist above!</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    watchlists.forEach(watchlist => {
        html += createWatchlistCard(watchlist);
    });
    
    container.innerHTML = html;
    
    // Load market data for all watchlists
    watchlists.forEach(watchlist => {
        loadWatchlistMarketData(watchlist.name);
    });
}

// Create HTML for a watchlist card
function createWatchlistCard(watchlist) {
    const cardId = `watchlist-${watchlist.name.replace(/[^a-zA-Z0-9]/g, '_')}`;
    const tableId = `${cardId}-table`;
    const bodyId = `${cardId}-tbody`;
    
    return `
        <div class="card bg-secondary border-0 shadow-lg mb-4" id="${cardId}">
            <div class="card-header bg-dark border-0 d-flex justify-content-between align-items-center">
                <h5 class="mb-0 text-light">
                    <i class="fas fa-list me-2 text-warning"></i>${watchlist.name}
                    <span class="badge bg-warning text-dark ms-2" id="${cardId}-count">${watchlist.count}</span>
                </h5>
                <div class="d-flex gap-2 align-items-center">
                    <button class="btn btn-sm btn-success" onclick="addSymbolToWatchlist('${watchlist.name}')">
                        <i class="fas fa-plus me-1"></i>Add Symbol
                    </button>
                    <button class="btn btn-sm btn-outline-light" onclick="editWatchlist('${watchlist.name}')">
                        <i class="fas fa-edit me-1"></i>Edit
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteWatchlist('${watchlist.name}')">
                        <i class="fas fa-trash me-1"></i>Delete
                    </button>
                    <button class="btn btn-sm btn-outline-light" onclick="refreshWatchlistData('${watchlist.name}')">
                        <i class="fas fa-sync-alt me-1"></i>Refresh
                    </button>
                </div>
            </div>
            
            <div class="card-body p-0">
                <div class="table-responsive" style="overflow-y: auto; max-height: 400px;">
                    <table class="table table-dark table-hover mb-0 signals-table" id="${tableId}">
                        <thead class="sticky-top">
                            <tr>
                                <th style="width: 50px">ID</th>
                                <th style="width: 80px">Symbol</th>
                                <th style="width: 70px">7D</th>
                                <th style="width: 70px">30D</th>
                                <th style="width: 60px">7D%</th>
                                <th style="width: 60px">30D%</th>
                                <th style="width: 70px">CMP</th>
                                <th style="width: 70px">%CHAN</th>
                                <th style="width: 70px">CPL</th>
                                <th style="width: 100px">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="${bodyId}">
                            <tr class="loading-row">
                                <td colspan="10" class="text-center py-4">
                                    <div class="d-flex justify-content-center align-items-center">
                                        <div class="spinner-border text-warning me-2" role="status">
                                            <span class="visually-hidden">Loading...</span>
                                        </div>
                                        <span class="text-muted">Loading ${watchlist.name} data...</span>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="card-footer bg-dark border-0 d-flex justify-content-between align-items-center text-light">
                <div class="d-flex align-items-center gap-3">
                    <small>Showing <span id="${cardId}-showing">${watchlist.count}</span> of <span id="${cardId}-total">${watchlist.count}</span> symbols</small>
                </div>
                <div class="d-flex gap-2">
                    <button class="btn btn-sm btn-outline-light" onclick="exportWatchlist('${watchlist.name}')">
                        <i class="fas fa-download me-1"></i>Export
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Load market data for a specific watchlist
function loadWatchlistMarketData(listName) {
    const cardId = `watchlist-${listName.replace(/[^a-zA-Z0-9]/g, '_')}`;
    const bodyId = `${cardId}-tbody`;
    
    fetch(`/api/market-watch/watchlists/${encodeURIComponent(listName)}/symbols-with-data`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateWatchlistTable(listName, data.symbols);
        } else {
            showErrorInWatchlistTable(listName, data.error);
        }
    })
    .catch(error => {
        console.error(`Error loading watchlist ${listName} data:`, error);
        showErrorInWatchlistTable(listName, 'Network error loading data');
    });
}

// Update watchlist table with market data
function updateWatchlistTable(listName, symbols) {
    const cardId = `watchlist-${listName.replace(/[^a-zA-Z0-9]/g, '_')}`;
    const bodyId = `${cardId}-tbody`;
    const tbody = document.getElementById(bodyId);
    
    if (!tbody) return;
    
    if (symbols.length === 0) {
        tbody.innerHTML = `
            <tr class="no-data-row">
                <td colspan="10" class="text-center text-muted py-4">
                    <i class="fas fa-chart-line fa-2x mb-2"></i><br>
                    No symbols in this watchlist<br>
                    <button class="btn btn-sm btn-primary mt-2" onclick="addSymbolToWatchlist('${listName}')">
                        <i class="fas fa-plus me-1"></i>Add Symbol
                    </button>
                </td>
            </tr>
        `;
        return;
    }
    
    let html = '';
    symbols.forEach((symbol, index) => {
        const change7dStyle = getGradientBackgroundColor(symbol.change_7d_pct);
        const change30dStyle = getGradientBackgroundColor(symbol.change_30d_pct);
        const changePctStyle = getGradientBackgroundColor(symbol.change_pct);
        
        html += `
            <tr>
                <td>${index + 1}</td>
                <td><strong>${symbol.symbol}</strong></td>
                <td>${symbol.price_7d || '--'}</td>
                <td>${symbol.price_30d || '--'}</td>
                <td style="${change7dStyle}">${symbol.change_7d_pct || '--'}</td>
                <td style="${change30dStyle}">${symbol.change_30d_pct || '--'}</td>
                <td><strong>${symbol.cmp || '--'}</strong></td>
                <td style="${changePctStyle}">${symbol.change_pct || '--'}</td>
                <td>${symbol.change_val || '--'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-danger" onclick="removeSymbolFromWatchlist('${listName}', '${symbol.symbol}')" title="Remove symbol">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
    
    // Update counts
    const countElement = document.getElementById(`${cardId}-count`);
    const showingElement = document.getElementById(`${cardId}-showing`);
    const totalElement = document.getElementById(`${cardId}-total`);
    
    if (countElement) countElement.textContent = symbols.length;
    if (showingElement) showingElement.textContent = symbols.length;
    if (totalElement) totalElement.textContent = symbols.length;
}

// Show error in watchlist table
function showErrorInWatchlistTable(listName, message) {
    const cardId = `watchlist-${listName.replace(/[^a-zA-Z0-9]/g, '_')}`;
    const bodyId = `${cardId}-tbody`;
    const tbody = document.getElementById(bodyId);
    
    if (!tbody) return;
    
    tbody.innerHTML = `
        <tr class="error-row">
            <td colspan="10" class="text-center text-danger py-4">
                <i class="fas fa-exclamation-triangle fa-2x mb-2"></i><br>
                ${message}<br>
                <button class="btn btn-sm btn-outline-light mt-2" onclick="loadWatchlistMarketData('${listName}')">
                    <i class="fas fa-retry me-1"></i>Retry
                </button>
            </td>
        </tr>
    `;
}

// Add symbol to specific watchlist
window.addSymbolToWatchlist = function(listName) {
    // Store the current list name for the modal
    window.currentWatchlistName = listName;
    
    // Open the add symbol modal
    const modal = new bootstrap.Modal(document.getElementById('addSymbolModal'));
    modal.show();
    
    // Update modal title
    const modalTitle = document.querySelector('#addSymbolModal .modal-title');
    modalTitle.innerHTML = `<i class="fas fa-plus me-2"></i>Add Symbol to ${listName}`;
};

// Remove symbol from watchlist
window.removeSymbolFromWatchlist = function(listName, symbol) {
    Swal.fire({
        title: 'Remove Symbol',
        text: `Are you sure you want to remove ${symbol} from ${listName}?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Yes, remove it!',
        background: '#1a1a1a',
        color: '#fff'
    }).then(result => {
        if (result.isConfirmed) {
            fetch(`/api/market-watch/watchlists/${encodeURIComponent(listName)}/symbols`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ symbol: symbol })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadWatchlistMarketData(listName);
                    Swal.fire({
                        icon: 'success',
                        title: 'Removed',
                        text: data.message,
                        background: '#1a1a1a',
                        color: '#fff',
                        timer: 2000,
                        showConfirmButton: false
                    });
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: data.error || 'Failed to remove symbol',
                        background: '#1a1a1a',
                        color: '#fff'
                    });
                }
            })
            .catch(error => {
                console.error('Error removing symbol:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'Failed to remove symbol. Please try again.',
                    background: '#1a1a1a',
                    color: '#fff'
                });
            });
        }
    });
};

// Edit watchlist name
window.editWatchlist = function(listName) {
    Swal.fire({
        title: 'Edit Watchlist Name',
        input: 'text',
        inputValue: listName,
        inputPlaceholder: 'Enter new name for the watchlist',
        inputAttributes: {
            maxlength: 50
        },
        showCancelButton: true,
        confirmButtonText: 'Update',
        background: '#1a1a1a',
        color: '#fff',
        inputValidator: (value) => {
            if (!value || value.trim().length === 0) {
                return 'Please enter a valid name';
            }
            if (value.length > 50) {
                return 'Name must be 50 characters or less';
            }
        }
    }).then(result => {
        if (result.isConfirmed) {
            const newName = result.value.trim();
            
            // For now, show info that edit is not implemented in backend
            Swal.fire({
                icon: 'info',
                title: 'Feature Coming Soon',
                text: 'Watchlist renaming will be available in the next update. For now, you can delete and recreate the list.',
                background: '#1a1a1a',
                color: '#fff'
            });
        }
    });
};

// Delete watchlist
window.deleteWatchlist = function(listName) {
    Swal.fire({
        title: 'Delete Watchlist',
        text: `Are you sure you want to delete the watchlist "${listName}"? This action cannot be undone.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Yes, delete it!',
        background: '#1a1a1a',
        color: '#fff'
    }).then(result => {
        if (result.isConfirmed) {
            fetch(`/api/market-watch/watchlists/${encodeURIComponent(listName)}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadCustomWatchlists();
                    Swal.fire({
                        icon: 'success',
                        title: 'Deleted',
                        text: data.message,
                        background: '#1a1a1a',
                        color: '#fff',
                        timer: 2000,
                        showConfirmButton: false
                    });
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: data.error || 'Failed to delete watchlist',
                        background: '#1a1a1a',
                        color: '#fff'
                    });
                }
            })
            .catch(error => {
                console.error('Error deleting watchlist:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'Failed to delete watchlist. Please try again.',
                    background: '#1a1a1a',
                    color: '#fff'
                });
            });
        }
    });
};

// Refresh watchlist data
window.refreshWatchlistData = function(listName) {
    loadWatchlistMarketData(listName);
};

// Export watchlist to CSV
window.exportWatchlist = function(listName) {
    fetch(`/api/market-watch/watchlists/${encodeURIComponent(listName)}/symbols`)
    .then(response => response.json())
    .then(data => {
        if (data.success && data.symbols.length > 0) {
            // Create CSV content according to user's format: Market Watch Name, Symbol 1, Symbol 2, etc.
            const symbols = data.symbols.map(s => s.symbol).join(',');
            const csvContent = `Market Watch Name,Symbol 1,Symbol 2,Symbol 3,Symbol 4,Symbol 5\n${listName},${symbols}`;
            
            // Create and download file
            const blob = new Blob([csvContent], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${listName.replace(/[^a-zA-Z0-9]/g, '_')}_watchlist.csv`;
            a.click();
            window.URL.revokeObjectURL(url);
            
            Swal.fire({
                icon: 'success',
                title: 'Exported',
                text: 'Watchlist exported successfully!',
                background: '#1a1a1a',
                color: '#fff',
                timer: 2000,
                showConfirmButton: false
            });
        } else {
            Swal.fire({
                icon: 'warning',
                title: 'No Data',
                text: 'No symbols to export in this watchlist.',
                background: '#1a1a1a',
                color: '#fff'
            });
        }
    })
    .catch(error => {
        console.error('Error exporting watchlist:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Failed to export watchlist. Please try again.',
            background: '#1a1a1a',
            color: '#fff'
        });
    });
};

// Initialize on page load
document.addEventListener("DOMContentLoaded", function () {
    // Load both market watch lists
    loadDefaultMarketWatch();
    loadUserWatchlist();
    
    // Load custom watchlists
    setTimeout(() => {
        loadCustomWatchlists();
    }, 1000);

    // Initialize advanced symbol modal
    initializeAdvancedSymbolModal();

    // Auto-uppercase symbol input
    var symbolInput = document.getElementById("symbolSearchInput");
    if (symbolInput) {
        symbolInput.addEventListener("input", function () {
            this.value = this.value.toUpperCase();
        });

        // Enter key submission
        symbolInput.addEventListener("keypress", function (e) {
            if (e.key === "Enter") {
                e.preventDefault();
                // Don't submit, just search
            }
        });
    }

    // Hide suggestions when clicking outside
    document.addEventListener("click", function (e) {
        if (
            !e.target.closest("#symbolSearchInput") &&
            !e.target.closest("#symbolSuggestions")
        ) {
            hideSuggestions();
        }
    });
});
