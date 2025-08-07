// Market Watch Functionality

// Market watch data storage
var defaultMarketWatchData = [];
var filteredDefaultData = [];
var allSymbolsData = []; // For search suggestions

// Pagination variables
var defaultCurrentPage = 1;
var defaultPageSize = 10;
var defaultTotalPages = 1;

// Search variables
var defaultSearchTimeout = null;


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
    if (!searchInput) {
        console.error("symbolSearchInput element not found");
        return;
    }
    
    const searchTerm = searchInput.value.trim().toUpperCase();

    // Clear previous timeout
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }

    // Check if we have any filters selected
    const companyFilter = document.getElementById("companyFilter");
    const sectorFilter = document.getElementById("sectorFilter");
    const subSectorFilter = document.getElementById("subSectorFilter");
    
    const hasFilters =
        (companyFilter && companyFilter.value) ||
        (sectorFilter && sectorFilter.value) ||
        (subSectorFilter && subSectorFilter.value);

    // Show suggestions if search term is >= 1 char OR filters are selected
    if (searchTerm.length < 1 && !hasFilters) {
        hideSuggestions();
        return;
    }

    // Show loading state immediately
    showSearchLoading();
    
    // Debounce search
    searchTimeout = setTimeout(() => {
        performSymbolSearch(searchTerm || "");
    }, 300);
}

// Perform actual symbol search
function performSymbolSearch(searchTerm) {
    const finalSearchTerm = searchTerm || "";

    // Get filter elements safely
    const niftyCheck = document.getElementById("niftyCheck");
    const nifty500Check = document.getElementById("nifty500Check");
    const etfCheck = document.getElementById("etfCheck");
    const companyFilter = document.getElementById("companyFilter");
    const sectorFilter = document.getElementById("sectorFilter");
    const subSectorFilter = document.getElementById("subSectorFilter");

    const params = new URLSearchParams({
        q: finalSearchTerm,
        nifty: niftyCheck && niftyCheck.checked ? "1" : "0",
        nifty_500: nifty500Check && nifty500Check.checked ? "1" : "0", 
        etf: etfCheck && etfCheck.checked ? "1" : "0",
        company: companyFilter ? companyFilter.value : "",
        sector: sectorFilter ? sectorFilter.value : "",
        sub_sector: subSectorFilter ? subSectorFilter.value : "",
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
    
    if (!suggestionsDiv) {
        console.error("symbolSuggestions element not found");
        return;
    }

    if (symbols.length === 0) {
        suggestionsDiv.innerHTML =
            '<div class="p-3 text-muted text-center"><i class="fas fa-search me-2"></i>No symbols found matching your criteria</div>';
        suggestionsDiv.classList.remove("d-none");
        return;
    }

    let html = "";
    symbols.forEach((symbol) => {
        const categories = [];
        if (symbol.categories && symbol.categories.nifty)
            categories.push('<span class="badge bg-success me-1">Nifty</span>');
        if (symbol.categories && symbol.categories.nifty_500)
            categories.push(
                '<span class="badge bg-primary me-1">Nifty 500</span>',
            );
        if (symbol.categories && symbol.categories.etf)
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

// Show search loading state
function showSearchLoading() {
    const suggestionsDiv = document.getElementById("symbolSuggestions");
    if (suggestionsDiv) {
        suggestionsDiv.innerHTML = `
            <div class="p-3 text-center">
                <div class="d-flex align-items-center justify-content-center">
                    <div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
                    <span class="text-muted">Searching symbols...</span>
                </div>
            </div>
        `;
        suggestionsDiv.classList.remove("d-none");
    }
}

// Hide suggestions
function hideSuggestions() {
    const suggestionsDiv = document.getElementById("symbolSuggestions");
    if (suggestionsDiv) {
        suggestionsDiv.classList.add("d-none");
    }
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
                const symbolInput = document.getElementById("symbolSearchInput");
                const addBtn = document.getElementById("addSymbolBtn");
                if (symbolInput) symbolInput.value = symbol;
                if (addBtn) addBtn.disabled = false;
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
    if (!searchInput) return;
    
    const searchTerm = searchInput.value.trim();
    
    // Show suggestions even with empty search if filters are selected
    const companyFilter = document.getElementById("companyFilter");
    const sectorFilter = document.getElementById("sectorFilter");
    const subSectorFilter = document.getElementById("subSectorFilter");
    
    const hasFilters =
        (companyFilter && companyFilter.value) ||
        (sectorFilter && sectorFilter.value) ||
        (subSectorFilter && subSectorFilter.value);

    if (searchTerm.length >= 1 || hasFilters) {
        performSymbolSearch(searchTerm || "");
    } else {
        hideSuggestions();
    }
}

// Validate and add direct symbol entry
function validateAndAddDirectSymbol(symbol) {
    // Show loading state
    const addBtn = document.getElementById("addSymbolBtn");
    const originalText = addBtn.innerHTML;
    addBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Validating...';
    addBtn.disabled = true;
    
    // Try to get symbol details from API
    fetch(`/api/symbols/${encodeURIComponent(symbol)}/details`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.symbol) {
                // Symbol exists, use it
                selectedSymbolData = data.symbol;
                displaySelectedSymbolDetails();
                addSymbolToCurrentWatchlist();
            } else {
                // Symbol not found, but still allow adding it
                selectedSymbolData = {
                    symbol: symbol,
                    company: "Unknown",
                    sector: "Unknown",
                    sub_sector: "Unknown",
                    categories: {}
                };
                addSymbolToCurrentWatchlist();
            }
        })
        .catch(error => {
            console.error('Error validating symbol:', error);
            // Even on error, allow adding the symbol
            selectedSymbolData = {
                symbol: symbol,
                company: "Unknown",
                sector: "Unknown", 
                sub_sector: "Unknown",
                categories: {}
            };
            addSymbolToCurrentWatchlist();
        })
        .finally(() => {
            // Restore button state
            addBtn.innerHTML = originalText;
            addBtn.disabled = false;
        });
}

// Add symbol to current watchlist
function addSymbolToCurrentWatchlist() {
    if (!selectedSymbolData) return;
    
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
                // Reload the specific watchlist using enhanced version
                if (window.currentWatchlistName) {
                    loadWatchlistMarketDataEnhanced(window.currentWatchlistName);
                }
                
                Swal.fire({
                    icon: 'success',
                    title: 'Symbol Added',
                    text: data.message,
                    background: '#1a1a1a',
                    color: '#fff',
                    timer: 2000,
                    showConfirmButton: false
                });
                
                // Close modal and clear selection
                const modal = bootstrap.Modal.getInstance(document.getElementById("addSymbolModal"));
                if (modal) modal.hide();
                clearSymbolSelection();
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
    }
}

// Make sure functions are available globally
window.searchSymbols = searchSymbols;
window.updateSymbolSearch = updateSymbolSearch;

// Clear symbol selection
function clearSymbolSelection() {
    selectedSymbolData = null;
    const detailsElement = document.getElementById("selectedSymbolDetails");
    const addBtn = document.getElementById("addSymbolBtn");
    const symbolInput = document.getElementById("symbolSearchInput");
    
    if (detailsElement) detailsElement.classList.add("d-none");
    if (addBtn) addBtn.disabled = true;
    if (symbolInput) symbolInput.value = "";
    hideSuggestions();
}

// Submit advanced add symbol
function submitAdvancedAddSymbol() {
    const symbolSearchInput = document.getElementById("symbolSearchInput");
    const inputSymbol = symbolSearchInput ? symbolSearchInput.value.trim().toUpperCase() : "";
    
    // If no symbol selected but user typed a symbol, try to validate and use it
    if (!selectedSymbolData && inputSymbol) {
        validateAndAddDirectSymbol(inputSymbol);
        return;
    }
    
    if (!selectedSymbolData) {
        Swal.fire({
            icon: "error",
            title: "No Symbol Selected",
            text: "Please enter a symbol name or select from suggestions.",
            background: "#1a1a1a",
            color: "#fff",
        });
        return;
    }

    // Use the new function to add symbol
    addSymbolToCurrentWatchlist();
}

// Legacy function for backward compatibility
function submitAddSymbol() {
    submitAdvancedAddSymbol();
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

// Update default market watch table with pagination
function updateDefaultMarketWatchTable() {
    var tableBody = document.getElementById("defaultMarketWatchTableBody");
    
    // Use filtered data if available, otherwise use all data
    var dataToShow = filteredDefaultData.length > 0 ? filteredDefaultData : defaultMarketWatchData;

    if (dataToShow.length === 0) {
        tableBody.innerHTML = `
            <tr class="no-data-row">
                <td colspan="10" class="text-center text-muted py-4">
                    <i class="fas fa-chart-line fa-2x mb-2"></i><br>
                    ${filteredDefaultData.length === 0 && defaultMarketWatchData.length > 0 ? 'No symbols found matching your search' : 'Loading default market watch data...'}
                </td>
            </tr>
        `;
        updateDefaultPagination();
        return;
    }

    // Calculate pagination
    var startIndex = (defaultCurrentPage - 1) * defaultPageSize;
    var endIndex = startIndex + defaultPageSize;
    var pageData = dataToShow.slice(startIndex, endIndex);

    var html = "";
    pageData.forEach(function (item) {
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
                    <!-- Action buttons removed for Default watchlist -->
                </td>
            </tr>
        `;
    });

    tableBody.innerHTML = html;
    updateDefaultPagination();
    updateDefaultCounts();
}



// Update default counts with pagination info
function updateDefaultCounts() {
    var dataToShow = filteredDefaultData.length > 0 ? filteredDefaultData : defaultMarketWatchData;
    var startIndex = (defaultCurrentPage - 1) * defaultPageSize;
    var endIndex = Math.min(startIndex + defaultPageSize, dataToShow.length);
    
    document.getElementById("defaultCount").textContent = dataToShow.length;
    document.getElementById("defaultTotalCount").textContent = dataToShow.length;
    document.getElementById("defaultShowingCount").textContent = Math.min(defaultPageSize, dataToShow.length - startIndex);
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
            allSymbolsData = data.symbols; // Store for search suggestions
            filteredDefaultData = []; // Reset filter
            defaultCurrentPage = 1; // Reset to first page
            updateDefaultMarketWatchTable();
            initializeFilterOptions();
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

function refreshMarketWatch() {
    refreshDefaultList();
}

// Export function
function exportMarketWatch() {
    var data = {
        defaultList: "Default market watch data"
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
            
            // Load filter options for each watchlist
            setTimeout(() => {
                data.watchlists.forEach(watchlist => {
                    loadWatchlistFilterOptions(watchlist.name);
                });
            }, 500); // Small delay to ensure UI elements are rendered
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
    
    // Load market data for all watchlists (enhanced version)
    watchlists.forEach(watchlist => {
        loadWatchlistMarketDataEnhanced(watchlist.name);
    });
}

// Create HTML for a watchlist card with enhanced search and filter functionality
function createWatchlistCard(watchlist) {
    const cardId = `watchlist-${watchlist.name.replace(/[^a-zA-Z0-9]/g, '_')}`;
    const tableId = `${cardId}-table`;
    const bodyId = `${cardId}-tbody`;
    const searchContainerId = `${cardId}-search-container`;
    const symbolSearchId = `${cardId}-symbol-search`;
    const companyFilterId = `${cardId}-company-filter`;
    const sectorFilterId = `${cardId}-sector-filter`;
    const searchSuggestionsId = `${cardId}-search-suggestions`;
    
    return `
        <div class="card bg-secondary border-0 shadow-lg mb-4" id="${cardId}">
            <div class="card-header bg-dark border-0 d-flex justify-content-between align-items-center">
                <h5 class="mb-0 text-light">
                    <i class="fas fa-list me-2 text-warning"></i>${watchlist.name}
                    <span class="badge bg-warning text-dark ms-2" id="${cardId}-count">${watchlist.count}</span>
                </h5>
                <div class="d-flex gap-2 align-items-center">
                    <button class="btn btn-sm btn-outline-light" onclick="toggleWatchlistSection('${watchlist.name}')">
                        <i class="fas fa-minus" id="${cardId}-minimize-icon"></i>
                    </button>
                    <button class="btn btn-sm btn-success" onclick="addSymbolToWatchlist('${watchlist.name}')">
                        <i class="fas fa-plus me-1"></i>Add Symbol
                    </button>
                    <button class="btn btn-sm btn-outline-light" onclick="editWatchlistName('${watchlist.name}')">
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
            
            <!-- Search and Filter Section for Custom Watchlist -->
            <div class="border-bottom border-secondary p-3" id="${searchContainerId}">
                <div class="row g-2">
                    <div class="col-md-6">
                        <div class="input-group">
                            <span class="input-group-text bg-secondary border-0">
                                <i class="fas fa-search text-light"></i>
                            </span>
                            <input
                                type="text"
                                class="form-control bg-dark text-light border-0"
                                id="${symbolSearchId}"
                                placeholder="Search by symbol name (e.g. 'A' for AAPL, ADANI...)"
                                onkeyup="performWatchlistSearch('${watchlist.name}')"
                                autocomplete="off"
                            />
                            <button
                                class="btn btn-sm btn-outline-light"
                                type="button"
                                onclick="clearWatchlistSearch('${watchlist.name}')"
                                title="Clear search"
                            >
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                        <!-- Search suggestions dropdown -->
                        <div class="position-relative">
                            <div id="${searchSuggestionsId}" class="dropdown-menu bg-dark border-secondary d-none" style="width: 100%; max-height: 200px; overflow-y: auto; position: absolute; z-index: 1000;">
                                <!-- Search suggestions will be populated here -->
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <select class="form-select bg-dark text-light border-secondary" id="${companyFilterId}" onchange="performWatchlistSearch('${watchlist.name}')">
                            <option value="">All Companies</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <select class="form-select bg-dark text-light border-secondary" id="${sectorFilterId}" onchange="performWatchlistSearch('${watchlist.name}')">
                            <option value="">All Sectors</option>
                        </select>
                    </div>
                </div>
            </div>
            
            <div class="card-body p-0" id="${cardId}-table-container">
                <div class="table-responsive" style="overflow-y: auto; max-height: 400px;">
                    <table class="table table-dark table-hover mb-0 signals-table" id="${tableId}">
                        <thead class="sticky-top">
                            <tr>
                                <th style="width: 50px" onclick="sortWatchlistTable('${watchlist.name}', 'id')">
                                    ID <i class="fas fa-sort" id="${cardId}-sort-id"></i>
                                </th>
                                <th style="width: 80px" onclick="sortWatchlistTable('${watchlist.name}', 'symbol')">
                                    Symbol <i class="fas fa-sort" id="${cardId}-sort-symbol"></i>
                                </th>
                                <th style="width: 70px" onclick="sortWatchlistTable('${watchlist.name}', 'price_7d')">
                                    7D <i class="fas fa-sort" id="${cardId}-sort-price_7d"></i>
                                </th>
                                <th style="width: 70px" onclick="sortWatchlistTable('${watchlist.name}', 'price_30d')">
                                    30D <i class="fas fa-sort" id="${cardId}-sort-price_30d"></i>
                                </th>
                                <th style="width: 60px" onclick="sortWatchlistTable('${watchlist.name}', 'change_7d_pct')">
                                    7D% <i class="fas fa-sort" id="${cardId}-sort-change_7d_pct"></i>
                                </th>
                                <th style="width: 60px" onclick="sortWatchlistTable('${watchlist.name}', 'change_30d_pct')">
                                    30D% <i class="fas fa-sort" id="${cardId}-sort-change_30d_pct"></i>
                                </th>
                                <th style="width: 70px" onclick="sortWatchlistTable('${watchlist.name}', 'cmp')">
                                    CMP <i class="fas fa-sort" id="${cardId}-sort-cmp"></i>
                                </th>
                                <th style="width: 70px" onclick="sortWatchlistTable('${watchlist.name}', 'change_pct')">
                                    %CHAN <i class="fas fa-sort" id="${cardId}-sort-change_pct"></i>
                                </th>
                                <th style="width: 70px" onclick="sortWatchlistTable('${watchlist.name}', 'change_val')">
                                    CPL <i class="fas fa-sort" id="${cardId}-sort-change_val"></i>
                                </th>
                                <th style="width: 100px">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="${bodyId}">
                            ${generateSkeletonRows()}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="card-footer bg-dark border-0 d-flex justify-content-between align-items-center text-light">
                <div class="d-flex align-items-center gap-3">
                    <small>Showing <span id="${cardId}-showing">${watchlist.count}</span> of <span id="${cardId}-total">${watchlist.count}</span> symbols</small>
                </div>
                <div class="d-flex gap-2 align-items-center">
                    <div class="btn-group" role="group">
                        <button
                            type="button"
                            class="btn btn-sm btn-outline-light"
                            onclick="previousWatchlistPage('${watchlist.name}')"
                            id="${cardId}-prev-btn"
                            disabled
                        >
                            <i class="fas fa-chevron-left"></i> Previous
                        </button>
                        <button
                            type="button"
                            class="btn btn-sm btn-outline-light"
                            disabled
                        >
                            Page <span id="${cardId}-current-page">1</span> of
                            <span id="${cardId}-total-pages">1</span>
                        </button>
                        <button
                            type="button"
                            class="btn btn-sm btn-outline-light"
                            onclick="nextWatchlistPage('${watchlist.name}')"
                            id="${cardId}-next-btn"
                            disabled
                        >
                            Next <i class="fas fa-chevron-right"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Generate skeleton shimmer rows for loading state
function generateSkeletonRows() {
    const skeletonRow = `
        <tr class="skeleton-row">
            <td><div class="skeleton-shimmer" style="width: 20px; height: 16px;"></div></td>
            <td><div class="skeleton-shimmer" style="width: 60px; height: 16px;"></div></td>
            <td><div class="skeleton-shimmer" style="width: 50px; height: 16px;"></div></td>
            <td><div class="skeleton-shimmer" style="width: 50px; height: 16px;"></div></td>
            <td><div class="skeleton-shimmer" style="width: 45px; height: 16px;"></div></td>
            <td><div class="skeleton-shimmer" style="width: 45px; height: 16px;"></div></td>
            <td><div class="skeleton-shimmer" style="width: 55px; height: 16px;"></div></td>
            <td><div class="skeleton-shimmer" style="width: 50px; height: 16px;"></div></td>
            <td><div class="skeleton-shimmer" style="width: 50px; height: 16px;"></div></td>
            <td><div class="skeleton-shimmer" style="width: 30px; height: 16px;"></div></td>
        </tr>
    `;
    
    return Array(5).fill(skeletonRow).join('');
}

// Load market data for a specific watchlist
function loadWatchlistMarketData(listName) {
    if (!listName) {
        console.error('List name is required for loadWatchlistMarketData');
        return;
    }
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

// Enhanced version with data storage for search/pagination - compatibility function
function loadWatchlistMarketDataEnhanced(listName) {
    // Use the proper enhanced version defined at the bottom of the file
    if (window.loadWatchlistMarketDataEnhanced && window.loadWatchlistMarketDataEnhanced !== loadWatchlistMarketDataEnhanced) {
        window.loadWatchlistMarketDataEnhanced(listName);
    } else {
        loadWatchlistMarketData(listName);
    }
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
                <button class="btn btn-sm btn-outline-light mt-2" onclick="loadWatchlistMarketDataEnhanced('${listName}')">
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
                    loadWatchlistMarketDataEnhanced(listName);
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
    loadWatchlistMarketDataEnhanced(listName);
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

// Edit watchlist name function
window.editWatchlistName = function(listName) {
    Swal.fire({
        title: 'Edit Watchlist Name',
        input: 'text',
        inputValue: listName,
        inputPlaceholder: 'Enter new name for the watchlist',
        background: '#1a1a1a',
        color: '#fff',
        showCancelButton: true,
        confirmButtonText: 'Save',
        cancelButtonText: 'Cancel',
        confirmButtonColor: '#007bff',
        cancelButtonColor: '#6c757d',
        inputValidator: (value) => {
            if (!value || value.trim().length === 0) {
                return 'Please enter a valid name';
            }
            if (value.trim().length > 50) {
                return 'Name must be 50 characters or less';
            }
            if (value.trim() === listName) {
                return 'Please enter a different name';
            }
            return null;
        }
    }).then((result) => {
        if (result.isConfirmed) {
            const newName = result.value.trim();
            
            fetch(`/api/market-watch/watchlists/${encodeURIComponent(listName)}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: newName
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Success',
                        text: data.message,
                        background: '#1a1a1a',
                        color: '#fff',
                        timer: 2000,
                        showConfirmButton: false
                    });
                    
                    // Reload custom watchlists to reflect the change
                    setTimeout(() => {
                        loadCustomWatchlists();
                    }, 500);
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: data.error || 'Failed to rename watchlist',
                        background: '#1a1a1a',
                        color: '#fff'
                    });
                }
            })
            .catch(error => {
                console.error('Error editing watchlist name:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'Failed to rename watchlist. Please try again.',
                    background: '#1a1a1a',
                    color: '#fff'
                });
            });
        }
    });
};



// Toggle section visibility functions
window.toggleDefaultSection = function() {
    const container = document.getElementById('defaultTableContainer');
    const icon = document.getElementById('defaultMinimizeIcon');
    
    if (container.style.display === 'none') {
        container.style.display = 'block';
        icon.className = 'fas fa-minus';
    } else {
        container.style.display = 'none';
        icon.className = 'fas fa-plus';
    }
};



window.toggleCreateSection = function() {
    const container = document.getElementById('createFormContainer');
    const icon = document.getElementById('createMinimizeIcon');
    
    if (container.style.display === 'none') {
        container.style.display = 'block';
        icon.className = 'fas fa-minus';
    } else {
        container.style.display = 'none';
        icon.className = 'fas fa-plus';
    }
};

// Search watchlists functionality
window.searchWatchlists = function() {
    const input = document.getElementById('watchlistSearchInput');
    const suggestions = document.getElementById('watchlistSuggestions');
    const query = input.value.trim().toLowerCase();
    
    if (query.length < 1) {
        suggestions.classList.add('d-none');
        return;
    }
    
    // Get all existing watchlists
    fetch('/api/market-watch/watchlists')
    .then(response => response.json())
    .then(data => {
        if (data.success && data.watchlists.length > 0) {
            const filtered = data.watchlists.filter(w => 
                w.name.toLowerCase().includes(query)
            );
            
            if (filtered.length > 0) {
                let html = '';
                filtered.forEach(watchlist => {
                    html += `
                        <div class="p-2 border-bottom border-secondary suggestion-item" 
                             style="cursor: pointer;"
                             onmouseover="this.style.backgroundColor='#343a40'"
                             onmouseout="this.style.backgroundColor=''"
                             onclick="jumpToWatchlist('${watchlist.name}')">
                            <div class="d-flex justify-content-between align-items-center">
                                <span class="text-light">
                                    <i class="fas fa-list me-2 text-warning"></i>${watchlist.name}
                                </span>
                                <small class="text-muted">${watchlist.count} symbols</small>
                            </div>
                        </div>
                    `;
                });
                suggestions.innerHTML = html;
                suggestions.classList.remove('d-none');
            } else {
                suggestions.innerHTML = '<div class="p-2 text-muted text-center">No watchlists found</div>';
                suggestions.classList.remove('d-none');
            }
        } else {
            suggestions.classList.add('d-none');
        }
    })
    .catch(error => {
        console.error('Error searching watchlists:', error);
        suggestions.classList.add('d-none');
    });
};

// Jump to specific watchlist
window.jumpToWatchlist = function(listName) {
    const cardId = `watchlist-${listName.replace(/[^a-zA-Z0-9]/g, '_')}`;
    const element = document.getElementById(cardId);
    
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        // Highlight the card briefly
        element.style.boxShadow = '0 0 20px rgba(0, 123, 255, 0.5)';
        setTimeout(() => {
            element.style.boxShadow = '';
        }, 2000);
    }
    
    // Clear search
    document.getElementById('watchlistSearchInput').value = '';
    document.getElementById('watchlistSuggestions').classList.add('d-none');
};

// Sorting functionality
let defaultSortState = { column: null, direction: 'asc' };
let userSortState = { column: null, direction: 'asc' };

window.sortDefaultTable = function(column) {
    // Update sort state
    if (defaultSortState.column === column) {
        defaultSortState.direction = defaultSortState.direction === 'asc' ? 'desc' : 'asc';
    } else {
        defaultSortState.column = column;
        defaultSortState.direction = 'asc';
    }
    
    // Update sort icons
    updateSortIcons('default', column, defaultSortState.direction);
    
    // Sort the data
    if (defaultMarketWatchData && defaultMarketWatchData.length > 0) {
        defaultMarketWatchData.sort((a, b) => {
            let valueA = a[column] || '';
            let valueB = b[column] || '';
            
            // Convert to numbers if possible
            if (!isNaN(valueA) && !isNaN(valueB)) {
                valueA = parseFloat(valueA);
                valueB = parseFloat(valueB);
            }
            
            if (defaultSortState.direction === 'asc') {
                return valueA > valueB ? 1 : -1;
            } else {
                return valueA < valueB ? 1 : -1;
            }
        });
        
        updateDefaultMarketWatchTable();
    }
};



function updateSortIcons(tableType, activeColumn, direction) {
    // Reset all icons for this table
    const prefix = tableType === 'default' ? 'default-sort-' : 'sort-';
    document.querySelectorAll(`[id^="${prefix}"]`).forEach(icon => {
        icon.className = 'fas fa-sort';
    });
    
    // Set active icon
    const activeIcon = document.getElementById(`${prefix}${activeColumn}`);
    if (activeIcon) {
        activeIcon.className = direction === 'asc' ? 'fas fa-sort-up' : 'fas fa-sort-down';
    }
}



// Toggle individual watchlist sections
window.toggleWatchlistSection = function(listName) {
    const cardId = `watchlist-${listName.replace(/[^a-zA-Z0-9]/g, '_')}`;
    const container = document.getElementById(`${cardId}-table-container`);
    const icon = document.getElementById(`${cardId}-minimize-icon`);
    
    if (container && icon) {
        if (container.style.display === 'none') {
            container.style.display = 'block';
            icon.className = 'fas fa-minus';
        } else {
            container.style.display = 'none';
            icon.className = 'fas fa-plus';
        }
    }
};

// Sort individual watchlist tables
let watchlistSortStates = {};

window.sortWatchlistTable = function(listName, column) {
    // Initialize sort state for this watchlist if it doesn't exist
    if (!watchlistSortStates[listName]) {
        watchlistSortStates[listName] = { column: null, direction: 'asc' };
    }
    
    const sortState = watchlistSortStates[listName];
    
    // Update sort state
    if (sortState.column === column) {
        sortState.direction = sortState.direction === 'asc' ? 'desc' : 'asc';
    } else {
        sortState.column = column;
        sortState.direction = 'asc';
    }
    
    // Update sort icons for this watchlist
    const cardId = `watchlist-${listName.replace(/[^a-zA-Z0-9]/g, '_')}`;
    updateWatchlistSortIcons(cardId, column, sortState.direction);
    
    // Reload data and apply sorting
    fetch(`/api/market-watch/watchlists/${encodeURIComponent(listName)}/symbols-with-data`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Sort the data
            data.symbols.sort((a, b) => {
                let valueA = a[column] || '';
                let valueB = b[column] || '';
                
                // Convert to numbers if possible
                if (!isNaN(valueA) && !isNaN(valueB)) {
                    valueA = parseFloat(valueA);
                    valueB = parseFloat(valueB);
                } else {
                    // Convert to strings for comparison
                    valueA = String(valueA).toLowerCase();
                    valueB = String(valueB).toLowerCase();
                }
                
                if (sortState.direction === 'asc') {
                    return valueA > valueB ? 1 : -1;
                } else {
                    return valueA < valueB ? 1 : -1;
                }
            });
            
            updateWatchlistTable(listName, data.symbols);
        }
    })
    .catch(error => {
        console.error(`Error sorting watchlist ${listName}:`, error);
    });
};

function updateWatchlistSortIcons(cardId, activeColumn, direction) {
    // Reset all icons for this watchlist
    document.querySelectorAll(`[id^="${cardId}-sort-"]`).forEach(icon => {
        icon.className = 'fas fa-sort';
    });
    
    // Set active icon
    const activeIcon = document.getElementById(`${cardId}-sort-${activeColumn}`);
    if (activeIcon) {
        activeIcon.className = direction === 'asc' ? 'fas fa-sort-up' : 'fas fa-sort-down';
    }
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", function () {
    // Load market watch lists
    loadDefaultMarketWatch();
    
    // Load custom watchlists
    setTimeout(() => {
        loadCustomWatchlists();
    }, 1000);

    // Initialize advanced symbol modal
    initializeAdvancedSymbolModal();

    // Auto-uppercase symbol input and enable button
    var symbolInput = document.getElementById("symbolSearchInput");
    if (symbolInput) {
        symbolInput.addEventListener("input", function () {
            this.value = this.value.toUpperCase();
            
            // Enable/disable Add Symbol button based on input
            const addBtn = document.getElementById("addSymbolBtn");
            if (addBtn) {
                if (this.value.trim().length > 0) {
                    addBtn.disabled = false;
                } else if (!selectedSymbolData) {
                    addBtn.disabled = true;
                }
            }
        });

        // Enter key submission
        symbolInput.addEventListener("keypress", function (e) {
            if (e.key === "Enter") {
                e.preventDefault();
                const trimmedValue = this.value.trim();
                if (trimmedValue.length > 0) {
                    // If there's a selected suggestion, use it; otherwise validate direct entry
                    if (selectedSymbolData) {
                        submitAdvancedAddSymbol();
                    } else {
                        validateAndAddDirectSymbol(trimmedValue.toUpperCase());
                    }
                }
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
        
        // Hide watchlist suggestions when clicking outside
        if (
            !e.target.closest("#watchlistSearchInput") &&
            !e.target.closest("#watchlistSuggestions")
        ) {
            const watchlistSuggestions = document.getElementById("watchlistSuggestions");
            if (watchlistSuggestions) {
                watchlistSuggestions.classList.add("d-none");
            }
        }
    });
});

// Pagination functions for default market watch
function updateDefaultPagination() {
    var dataToShow = filteredDefaultData.length > 0 ? filteredDefaultData : defaultMarketWatchData;
    defaultTotalPages = Math.ceil(dataToShow.length / defaultPageSize);
    
    var currentPageElement = document.getElementById("defaultCurrentPage");
    var totalPagesElement = document.getElementById("defaultTotalPages");
    var prevBtn = document.getElementById("defaultPrevBtn");
    var nextBtn = document.getElementById("defaultNextBtn");
    
    if (currentPageElement) currentPageElement.textContent = defaultCurrentPage;
    if (totalPagesElement) totalPagesElement.textContent = defaultTotalPages;
    if (prevBtn) prevBtn.disabled = defaultCurrentPage <= 1;
    if (nextBtn) nextBtn.disabled = defaultCurrentPage >= defaultTotalPages;
}

function previousDefaultPage() {
    if (defaultCurrentPage > 1) {
        defaultCurrentPage--;
        updateDefaultMarketWatchTable();
    }
}

function nextDefaultPage() {
    if (defaultCurrentPage < defaultTotalPages) {
        defaultCurrentPage++;
        updateDefaultMarketWatchTable();
    }
}

// Search and filter functions for default market watch
function performDefaultSearch() {
    // Clear previous timeout
    if (defaultSearchTimeout) {
        clearTimeout(defaultSearchTimeout);
    }
    
    // Set timeout to avoid too many API calls while typing
    defaultSearchTimeout = setTimeout(function() {
        var searchTerm = document.getElementById("defaultSymbolSearchInput").value.toLowerCase().trim();
        var companyFilter = document.getElementById("defaultCompanyFilter").value.toLowerCase();
        var sectorFilter = document.getElementById("defaultSectorFilter").value.toLowerCase();
        
        if (!searchTerm && !companyFilter && !sectorFilter) {
            filteredDefaultData = [];
            hideDefaultSearchSuggestions();
        } else {
            filteredDefaultData = defaultMarketWatchData.filter(function(item) {
                var matchesSearch = !searchTerm || 
                    (item.symbol && item.symbol.toLowerCase().startsWith(searchTerm)) ||
                    (item.company_name && item.company_name.toLowerCase().includes(searchTerm));
                
                var matchesCompany = !companyFilter || 
                    (item.company_name && item.company_name.toLowerCase().includes(companyFilter));
                
                var matchesSector = !sectorFilter || 
                    (item.sector && item.sector.toLowerCase().includes(sectorFilter));
                
                return matchesSearch && matchesCompany && matchesSector;
            });
            
            // Show search suggestions if only searching by symbol
            if (searchTerm && !companyFilter && !sectorFilter) {
                showDefaultSearchSuggestions(searchTerm);
            } else {
                hideDefaultSearchSuggestions();
            }
        }
        
        defaultCurrentPage = 1; // Reset to first page
        updateDefaultMarketWatchTable();
    }, 300);
}

function showDefaultSearchSuggestions(searchTerm) {
    var suggestions = defaultMarketWatchData.filter(function(item) {
        return item.symbol && item.symbol.toLowerCase().startsWith(searchTerm.toLowerCase());
    }).slice(0, 8); // Show max 8 suggestions
    
    var suggestionsDiv = document.getElementById("defaultSearchSuggestions");
    if (!suggestionsDiv) return;
    
    if (suggestions.length === 0) {
        hideDefaultSearchSuggestions();
        return;
    }
    
    var html = '';
    suggestions.forEach(function(item) {
        html += `
            <div class="dropdown-item" onclick="selectDefaultSymbol('${item.symbol}')">
                <strong>${item.symbol}</strong>
                ${item.company_name ? `<small class="text-muted d-block">${item.company_name}</small>` : ''}
            </div>
        `;
    });
    
    suggestionsDiv.innerHTML = html;
    suggestionsDiv.classList.remove("d-none");
}

function hideDefaultSearchSuggestions() {
    var suggestionsDiv = document.getElementById("defaultSearchSuggestions");
    if (suggestionsDiv) {
        suggestionsDiv.classList.add("d-none");
    }
}

function selectDefaultSymbol(symbol) {
    document.getElementById("defaultSymbolSearchInput").value = symbol;
    hideDefaultSearchSuggestions();
    performDefaultSearch();
}

function clearDefaultSearch() {
    document.getElementById("defaultSymbolSearchInput").value = "";
    document.getElementById("defaultCompanyFilter").value = "";
    document.getElementById("defaultSectorFilter").value = "";
    filteredDefaultData = [];
    defaultCurrentPage = 1;
    hideDefaultSearchSuggestions();
    updateDefaultMarketWatchTable();
}

// Initialize filter options
function initializeFilterOptions() {
    if (!defaultMarketWatchData || defaultMarketWatchData.length === 0) return;
    
    var companies = [...new Set(defaultMarketWatchData.map(item => item.company_name).filter(name => name))].sort();
    var sectors = [...new Set(defaultMarketWatchData.map(item => item.sector).filter(sector => sector))].sort();
    
    var companySelect = document.getElementById("defaultCompanyFilter");
    var sectorSelect = document.getElementById("defaultSectorFilter");
    
    if (companySelect) {
        companySelect.innerHTML = '<option value="">All Companies</option>';
        companies.forEach(function(company) {
            companySelect.innerHTML += `<option value="${company}">${company}</option>`;
        });
    }
    
    if (sectorSelect) {
        sectorSelect.innerHTML = '<option value="">All Sectors</option>';
        sectors.forEach(function(sector) {
            sectorSelect.innerHTML += `<option value="${sector}">${sector}</option>`;
        });
    }
}

// Variables to store watchlist data for search and pagination
var watchlistData = {};
var watchlistFilteredData = {};
var watchlistPagination = {};
var watchlistSearchTimeouts = {};

// Load filter options for a specific watchlist
function loadWatchlistFilterOptions(listName) {
    fetch('/api/symbols/filters')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            populateWatchlistFilterDropdowns(listName, data);
        }
    })
    .catch(error => {
        console.error(`Error loading filter options for ${listName}:`, error);
    });
}

// Populate filter dropdowns for a specific watchlist
function populateWatchlistFilterDropdowns(listName, filterOptions) {
    const cardId = `watchlist-${listName.replace(/[^a-zA-Z0-9]/g, '_')}`;
    
    // Populate company filter
    const companySelect = document.getElementById(`${cardId}-company-filter`);
    if (companySelect) {
        companySelect.innerHTML = '<option value="">All Companies</option>';
        filterOptions.companies.slice(0, 50).forEach(company => {
            const option = document.createElement('option');
            option.value = company;
            option.textContent = company;
            companySelect.appendChild(option);
        });
    }
    
    // Populate sector filter
    const sectorSelect = document.getElementById(`${cardId}-sector-filter`);
    if (sectorSelect) {
        sectorSelect.innerHTML = '<option value="">All Sectors</option>';
        filterOptions.sectors.forEach(sector => {
            const option = document.createElement('option');
            option.value = sector;
            option.textContent = sector;
            sectorSelect.appendChild(option);
        });
    }
}

// Search functionality for custom watchlists
function performWatchlistSearch(listName) {
    const cardId = `watchlist-${listName.replace(/[^a-zA-Z0-9]/g, '_')}`;
    const searchInput = document.getElementById(`${cardId}-symbol-search`);
    const companyFilter = document.getElementById(`${cardId}-company-filter`);
    const sectorFilter = document.getElementById(`${cardId}-sector-filter`);
    
    if (!searchInput || !watchlistData[listName]) return;
    
    const searchTerm = searchInput.value.trim().toLowerCase();
    const companyFilterValue = companyFilter ? companyFilter.value : '';
    const sectorFilterValue = sectorFilter ? sectorFilter.value : '';
    
    // Clear previous timeout
    if (watchlistSearchTimeouts[listName]) {
        clearTimeout(watchlistSearchTimeouts[listName]);
    }
    
    // Debounce search
    watchlistSearchTimeouts[listName] = setTimeout(() => {
        let filteredData = watchlistData[listName];
        
        // Apply search filter
        if (searchTerm) {
            filteredData = filteredData.filter(symbol => 
                symbol.symbol.toLowerCase().includes(searchTerm) ||
                (symbol.company && symbol.company.toLowerCase().includes(searchTerm))
            );
        }
        
        // Apply company filter
        if (companyFilterValue) {
            filteredData = filteredData.filter(symbol => 
                symbol.company && symbol.company.toLowerCase().includes(companyFilterValue.toLowerCase())
            );
        }
        
        // Apply sector filter
        if (sectorFilterValue) {
            filteredData = filteredData.filter(symbol => 
                symbol.sector && symbol.sector.toLowerCase().includes(sectorFilterValue.toLowerCase())
            );
        }
        
        watchlistFilteredData[listName] = filteredData;
        
        // Reset pagination
        if (!watchlistPagination[listName]) {
            watchlistPagination[listName] = {
                currentPage: 1,
                pageSize: 10,
                totalPages: 1
            };
        }
        watchlistPagination[listName].currentPage = 1;
        watchlistPagination[listName].totalPages = Math.ceil(filteredData.length / watchlistPagination[listName].pageSize);
        
        updateWatchlistTableWithPagination(listName, filteredData);
        updateWatchlistPaginationControls(listName);
    }, 300);
}

// Clear search for specific watchlist
function clearWatchlistSearch(listName) {
    const cardId = `watchlist-${listName.replace(/[^a-zA-Z0-9]/g, '_')}`;
    const searchInput = document.getElementById(`${cardId}-symbol-search`);
    const companyFilter = document.getElementById(`${cardId}-company-filter`);
    const sectorFilter = document.getElementById(`${cardId}-sector-filter`);
    
    if (searchInput) searchInput.value = '';
    if (companyFilter) companyFilter.value = '';
    if (sectorFilter) sectorFilter.value = '';
    
    performWatchlistSearch(listName);
}

// Pagination functions for watchlists
function previousWatchlistPage(listName) {
    if (!watchlistPagination[listName]) return;
    
    if (watchlistPagination[listName].currentPage > 1) {
        watchlistPagination[listName].currentPage--;
        const filteredData = watchlistFilteredData[listName] || watchlistData[listName] || [];
        updateWatchlistTableWithPagination(listName, filteredData);
        updateWatchlistPaginationControls(listName);
    }
}

function nextWatchlistPage(listName) {
    if (!watchlistPagination[listName]) return;
    
    if (watchlistPagination[listName].currentPage < watchlistPagination[listName].totalPages) {
        watchlistPagination[listName].currentPage++;
        const filteredData = watchlistFilteredData[listName] || watchlistData[listName] || [];
        updateWatchlistTableWithPagination(listName, filteredData);
        updateWatchlistPaginationControls(listName);
    }
}

// Update watchlist table with pagination
function updateWatchlistTableWithPagination(listName, symbols) {
    const cardId = `watchlist-${listName.replace(/[^a-zA-Z0-9]/g, '_')}`;
    const bodyId = `${cardId}-tbody`;
    const tbody = document.getElementById(bodyId);
    
    if (!tbody) return;
    
    // Initialize pagination if not exists
    if (!watchlistPagination[listName]) {
        watchlistPagination[listName] = {
            currentPage: 1,
            pageSize: 10,
            totalPages: Math.ceil(symbols.length / 10)
        };
    }
    
    const pagination = watchlistPagination[listName];
    const startIndex = (pagination.currentPage - 1) * pagination.pageSize;
    const endIndex = startIndex + pagination.pageSize;
    const paginatedSymbols = symbols.slice(startIndex, endIndex);
    
    if (paginatedSymbols.length === 0) {
        tbody.innerHTML = `
            <tr class="no-data-row">
                <td colspan="10" class="text-center text-muted py-4">
                    <i class="fas fa-chart-line fa-2x mb-2"></i><br>
                    ${symbols.length === 0 ? 'No symbols in this watchlist' : 'No symbols found matching your search'}<br>
                    <button class="btn btn-sm btn-primary mt-2" onclick="addSymbolToWatchlist('${listName}')">
                        <i class="fas fa-plus me-1"></i>Add Symbol
                    </button>
                </td>
            </tr>
        `;
        return;
    }
    
    let html = '';
    paginatedSymbols.forEach((symbol, index) => {
        const change7dStyle = getGradientBackgroundColor(symbol.change_7d_pct);
        const change30dStyle = getGradientBackgroundColor(symbol.change_30d_pct);
        const changePctStyle = getGradientBackgroundColor(symbol.change_pct);
        
        html += `
            <tr>
                <td>${startIndex + index + 1}</td>
                <td class="text-center">
                    <span class="fw-bold text-warning">${symbol.symbol}</span>
                </td>
                <td class="text-center">${symbol.price_7d}</td>
                <td class="text-center">${symbol.price_30d}</td>
                <td class="text-center" style="${change7dStyle}">${symbol.change_7d_pct}</td>
                <td class="text-center" style="${change30dStyle}">${symbol.change_30d_pct}</td>
                <td class="text-center fw-bold text-info">${symbol.cmp}</td>
                <td class="text-center" style="${changePctStyle}">${symbol.change_pct}</td>
                <td class="text-center">${symbol.change_val}</td>
                <td class="text-center">
                    <button class="btn btn-sm btn-outline-danger" onclick="removeSymbolFromWatchlist('${listName}', '${symbol.symbol}')" title="Remove Symbol">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
    
    // Update counts
    const showingElement = document.getElementById(`${cardId}-showing`);
    const totalElement = document.getElementById(`${cardId}-total`);
    if (showingElement) showingElement.textContent = paginatedSymbols.length;
    if (totalElement) totalElement.textContent = symbols.length;
}

// Update pagination controls for watchlists
function updateWatchlistPaginationControls(listName) {
    const cardId = `watchlist-${listName.replace(/[^a-zA-Z0-9]/g, '_')}`;
    const pagination = watchlistPagination[listName];
    
    if (!pagination) return;
    
    // Update page display
    const currentPageElement = document.getElementById(`${cardId}-current-page`);
    const totalPagesElement = document.getElementById(`${cardId}-total-pages`);
    if (currentPageElement) currentPageElement.textContent = pagination.currentPage;
    if (totalPagesElement) totalPagesElement.textContent = pagination.totalPages;
    
    // Update button states
    const prevBtn = document.getElementById(`${cardId}-prev-btn`);
    const nextBtn = document.getElementById(`${cardId}-next-btn`);
    if (prevBtn) prevBtn.disabled = pagination.currentPage <= 1;
    if (nextBtn) nextBtn.disabled = pagination.currentPage >= pagination.totalPages;
}

// Enhanced loadWatchlistMarketData with data storage for search/pagination
window.loadWatchlistMarketDataEnhanced = function(listName) {
    if (!listName) {
        console.error('List name is required for loadWatchlistMarketData');
        return;
    }
    
    fetch(`/api/market-watch/watchlists/${encodeURIComponent(listName)}/symbols-with-data`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Store data for search and pagination
            watchlistData[listName] = data.symbols;
            watchlistFilteredData[listName] = data.symbols;
            
            // Initialize pagination
            if (!watchlistPagination[listName]) {
                watchlistPagination[listName] = {
                    currentPage: 1,
                    pageSize: 10,
                    totalPages: Math.ceil(data.symbols.length / 10)
                };
            }
            
            updateWatchlistTableWithPagination(listName, data.symbols);
            updateWatchlistPaginationControls(listName);
        } else {
            showErrorInWatchlistTable(listName, data.error);
        }
    })
    .catch(error => {
        console.error(`Error loading watchlist ${listName} data:`, error);
        showErrorInWatchlistTable(listName, 'Network error loading data');
    });
};
