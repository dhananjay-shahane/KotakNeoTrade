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

// Load user watchlist from CSV API with real market data
function loadUserWatchlist() {
    fetch('/api/market-watch/user-symbols-with-data')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            userMarketWatchData = data.symbols;
            updateUserMarketWatchTable();
            updateUserCounts();
        } else {
            console.error('Failed to load user watchlist:', data.error);
        }
    })
    .catch(error => {
        console.error('Error loading user watchlist:', error);
    });
}

// Load default market watch with real market data
function loadDefaultMarketWatch() {
    fetch('/api/market-watch/default-symbols-with-data')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            defaultMarketWatchData = data.symbols;
            updateDefaultMarketWatchTable();
            updateDefaultCounts();
        } else {
            console.error('Failed to load default market watch:', data.error);
        }
    })
    .catch(error => {
        console.error('Error loading default market watch:', error);
    });
}

// Add symbol to user list from default list
function addToUserList(symbol) {
    // Make API call to add symbol to user's CSV watchlist
    fetch('/api/market-watch/user-symbols', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            symbol: symbol
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reload the user watchlist
            loadUserWatchlist();
            
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
}

// Advanced symbol search and selection variables
var selectedSymbolData = null;
var searchTimeout = null;
var filterOptions = { companies: [], sectors: [], sub_sectors: [] };

// Initialize advanced symbol modal
function initializeAdvancedSymbolModal() {
    // Load filter options when modal opens
    document.getElementById('addSymbolModal').addEventListener('shown.bs.modal', function() {
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
    fetch('/api/symbols/filters')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                filterOptions = data;
                populateFilterDropdowns();
            }
        })
        .catch(error => {
            console.error('Error loading filter options:', error);
        });
}

// Populate filter dropdowns
function populateFilterDropdowns() {
    // Populate company filter
    const companySelect = document.getElementById('companyFilter');
    companySelect.innerHTML = '<option value="">All Companies</option>';
    filterOptions.companies.slice(0, 50).forEach(company => {
        const option = document.createElement('option');
        option.value = company;
        option.textContent = company;
        companySelect.appendChild(option);
    });

    // Populate sector filter
    const sectorSelect = document.getElementById('sectorFilter');
    sectorSelect.innerHTML = '<option value="">All Sectors</option>';
    filterOptions.sectors.forEach(sector => {
        const option = document.createElement('option');
        option.value = sector;
        option.textContent = sector;
        sectorSelect.appendChild(option);
    });

    // Populate sub sector filter
    const subSectorSelect = document.getElementById('subSectorFilter');
    subSectorSelect.innerHTML = '<option value="">All Sub Sectors</option>';
    filterOptions.sub_sectors.forEach(subSector => {
        const option = document.createElement('option');
        option.value = subSector;
        option.textContent = subSector;
        subSectorSelect.appendChild(option);
    });
}

// Search symbols with current filters
function searchSymbols() {
    const searchInput = document.getElementById('symbolSearchInput');
    const searchTerm = searchInput.value.trim();
    
    // Clear previous timeout
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }
    
    // Check if we have any filters selected
    const hasFilters = document.getElementById('companyFilter').value || 
                      document.getElementById('sectorFilter').value || 
                      document.getElementById('subSectorFilter').value;
    
    // Show suggestions if search term is >= 1 char OR filters are selected
    if (searchTerm.length < 1 && !hasFilters) {
        hideSuggestions();
        return;
    }
    
    // Debounce search
    searchTimeout = setTimeout(() => {
        performSymbolSearch(searchTerm || '*');
    }, 300);
}

// Perform actual symbol search
function performSymbolSearch(searchTerm) {
    // Use empty string instead of '*' for wildcard search
    const finalSearchTerm = searchTerm === '*' ? '' : searchTerm;
    
    const params = new URLSearchParams({
        q: finalSearchTerm,
        nifty: document.getElementById('niftyCheck').checked ? '1' : '0',
        nifty_500: document.getElementById('nifty500Check').checked ? '1' : '0',
        etf: document.getElementById('etfCheck').checked ? '1' : '0',
        company: document.getElementById('companyFilter').value,
        sector: document.getElementById('sectorFilter').value,
        sub_sector: document.getElementById('subSectorFilter').value,
        limit: '15'
    });
    
    console.log('Searching with params:', params.toString());
    
    fetch(`/api/symbols/search?${params.toString()}`)
        .then(response => response.json())
        .then(data => {
            console.log('Search response:', data);
            if (data.success) {
                displaySymbolSuggestions(data.symbols);
            } else {
                console.error('Search failed:', data.error);
                displaySymbolSuggestions([]);
            }
        })
        .catch(error => {
            console.error('Search error:', error);
            displaySymbolSuggestions([]);
        });
}

// Display symbol suggestions
function displaySymbolSuggestions(symbols) {
    const suggestionsDiv = document.getElementById('symbolSuggestions');
    
    if (symbols.length === 0) {
        suggestionsDiv.innerHTML = '<div class="p-3 text-muted text-center"><i class="fas fa-search me-2"></i>No symbols found matching your criteria</div>';
        suggestionsDiv.classList.remove('d-none');
        return;
    }
    
    let html = '';
    symbols.forEach(symbol => {
        const categories = [];
        if (symbol.categories.nifty) categories.push('<span class="badge bg-success me-1">Nifty</span>');
        if (symbol.categories.nifty_500) categories.push('<span class="badge bg-primary me-1">Nifty 500</span>');
        if (symbol.categories.etf) categories.push('<span class="badge bg-warning me-1">ETF</span>');
        
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
                            ${categories.join('')}
                        </div>
                        <div class="text-muted small mb-1">${symbol.company || 'N/A'}</div>
                        <div class="text-muted small">${symbol.sector || 'N/A'} • ${symbol.sub_sector || 'N/A'}</div>
                    </div>
                    <div class="text-end">
                        <i class="fas fa-plus-circle text-success" style="font-size: 18px;"></i>
                    </div>
                </div>
            </div>
        `;
    });
    
    suggestionsDiv.innerHTML = html;
    suggestionsDiv.classList.remove('d-none');
    
    console.log('Displayed', symbols.length, 'symbol suggestions');
}

// Hide suggestions
function hideSuggestions() {
    document.getElementById('symbolSuggestions').classList.add('d-none');
}

// Select a symbol from suggestions
function selectSymbol(symbol) {
    fetch(`/api/symbols/${symbol}/details`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                selectedSymbolData = data.symbol;
                displaySelectedSymbolDetails();
                hideSuggestions();
                document.getElementById('symbolSearchInput').value = symbol;
                document.getElementById('addSymbolBtn').disabled = false;
            }
        })
        .catch(error => {
            console.error('Error getting symbol details:', error);
        });
}

// Display selected symbol details
function displaySelectedSymbolDetails() {
    if (!selectedSymbolData) return;
    
    document.getElementById('detailSymbol').textContent = selectedSymbolData.symbol;
    document.getElementById('detailCompany').textContent = selectedSymbolData.company;
    document.getElementById('detailSector').textContent = selectedSymbolData.sector;
    document.getElementById('detailSubSector').textContent = selectedSymbolData.sub_sector;
    
    // Display categories
    const categories = [];
    if (selectedSymbolData.categories.nifty) categories.push('<span class="badge bg-success">Nifty</span>');
    if (selectedSymbolData.categories.nifty_500) categories.push('<span class="badge bg-primary">Nifty 500</span>');
    if (selectedSymbolData.categories.etf) categories.push('<span class="badge bg-warning">ETF</span>');
    
    document.getElementById('detailCategories').innerHTML = categories.join(' ');
    document.getElementById('selectedSymbolDetails').classList.remove('d-none');
}

// Update symbol search when filters change
function updateSymbolSearch() {
    const searchInput = document.getElementById('symbolSearchInput');
    const searchTerm = searchInput.value.trim();
    
    // Show suggestions even with empty search if filters are selected
    const hasFilters = document.getElementById('companyFilter').value || 
                      document.getElementById('sectorFilter').value || 
                      document.getElementById('subSectorFilter').value;
    
    if (searchTerm.length >= 1 || hasFilters) {
        performSymbolSearch(searchTerm || '*');
    } else {
        hideSuggestions();
    }
}

// Clear symbol selection
function clearSymbolSelection() {
    selectedSymbolData = null;
    document.getElementById('selectedSymbolDetails').classList.add('d-none');
    document.getElementById('addSymbolBtn').disabled = true;
    document.getElementById('symbolSearchInput').value = '';
    hideSuggestions();
}

// Submit advanced add symbol
function submitAdvancedAddSymbol() {
    if (!selectedSymbolData) {
        Swal.fire({
            icon: 'error',
            title: 'No Symbol Selected',
            text: 'Please select a symbol first.',
            background: '#1a1a1a',
            color: '#fff'
        });
        return;
    }
    
    // Use the same API call as the simple add function
    addToUserList(selectedSymbolData.symbol);
    
    // Close modal and clear selection
    var modal = bootstrap.Modal.getInstance(document.getElementById('addSymbolModal'));
    modal.hide();
    clearSymbolSelection();
}

// Legacy function for backward compatibility
function submitAddSymbol() {
    submitAdvancedAddSymbol();
}

// Remove symbol from user list
function removeFromUserList(id) {
    var symbol = userMarketWatchData.find(function(item) {
        return item.id === id;
    });
    
    if (!symbol) return;
    
    Swal.fire({
        title: 'Remove Symbol',
        text: 'Are you sure you want to remove ' + symbol.symbol + ' from your market watch?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Yes, remove it!',
        background: '#1a1a1a',
        color: '#fff'
    }).then((result) => {
        if (result.isConfirmed) {
            // Make API call to remove symbol from CSV
            fetch('/api/market-watch/user-symbols', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symbol: symbol.symbol
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Reload the user watchlist
                    loadUserWatchlist();
                    
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
                console.error('Error removing symbol from watchlist:', error);
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
}

// Generate sample market data for a symbol
function generateSymbolData(symbol, id) {
    var basePrice = Math.random() * 3000 + 100; // Random price between 100-3100
    var change = (Math.random() - 0.5) * 100; // Random change between -50 to +50
    var changePercent = (change / basePrice) * 100;
    
    var sevenDayPrice = basePrice - (Math.random() * 50);
    var thirtyDayPrice = basePrice - (Math.random() * 100);
    var sevenDayPercent = ((basePrice - sevenDayPrice) / sevenDayPrice) * 100;
    var thirtyDayPercent = ((basePrice - thirtyDayPrice) / thirtyDayPrice) * 100;
    
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
        cpl: change.toFixed(2)
    };
}

// Update user market watch table
function updateUserMarketWatchTable() {
    var tableBody = document.getElementById('userMarketWatchTableBody');
    
    if (userMarketWatchData.length === 0) {
        tableBody.innerHTML = `
            <tr class="no-data-row">
                <td colspan="10" class="text-center text-muted py-4">
                    <i class="fas fa-plus-circle fa-2x mb-2"></i><br>
                    No symbols added yet. Click "Add Symbol" to start building your watchlist.
                </td>
            </tr>
        `;
        return;
    }
    
    var html = '';
    userMarketWatchData.forEach(function(item) {
        // Get gradient styles for percentage columns
        var change7dStyle = getGradientBackgroundColor(item.change_7d_pct);
        var change30dStyle = getGradientBackgroundColor(item.change_30d_pct);
        var changePctStyle = getGradientBackgroundColor(item.change_pct);
        
        html += `
            <tr>
                <td>${item.id}</td>
                <td><strong>${item.symbol}</strong></td>
                <td>${item.price_7d || '--'}</td>
                <td>${item.price_30d || '--'}</td>
                <td style="${change7dStyle}">${item.change_7d_pct || '--'}</td>
                <td style="${change30dStyle}">${item.change_30d_pct || '--'}</td>
                <td><strong>${item.cmp || '--'}</strong></td>
                <td style="${changePctStyle}">${item.change_pct || '--'}</td>
                <td>${item.change_val || '--'}</td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="removeFromUserList(${item.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    tableBody.innerHTML = html;
}

// Update default market watch table
function updateDefaultMarketWatchTable() {
    var tableBody = document.getElementById('defaultMarketWatchTableBody');
    
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
    
    var html = '';
    defaultMarketWatchData.forEach(function(item) {
        // Get gradient styles for percentage columns
        var change7dStyle = getGradientBackgroundColor(item.change_7d_pct);
        var change30dStyle = getGradientBackgroundColor(item.change_30d_pct);
        var changePctStyle = getGradientBackgroundColor(item.change_pct);
        
        html += `
            <tr>
                <td>${item.id}</td>
                <td><strong>${item.symbol}</strong></td>
                <td>${item.price_7d || '--'}</td>
                <td>${item.price_30d || '--'}</td>
                <td style="${change7dStyle}">${item.change_7d_pct || '--'}</td>
                <td style="${change30dStyle}">${item.change_30d_pct || '--'}</td>
                <td><strong>${item.cmp || '--'}</strong></td>
                <td style="${changePctStyle}">${item.change_pct || '--'}</td>
                <td>${item.change_val || '--'}</td>
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
    document.getElementById('userCount').textContent = count;
    document.getElementById('userTotalCount').textContent = count;
    document.getElementById('userShowingCount').textContent = count;
}

// Update default counts
function updateDefaultCounts() {
    var count = defaultMarketWatchData.length;
    document.getElementById('defaultCount').textContent = count;
    document.getElementById('defaultTotalCount').textContent = count;
    document.getElementById('defaultShowingCount').textContent = count;
}

// Add symbol to user list from default market watch
function addToUserListFromDefault(symbol) {
    // Use the existing addToUserList function
    addToUserList(symbol);
}

// Refresh functions
function refreshDefaultList() {
    console.log('Refreshing default market watch list...');
    // Reload default market watch data from API
    loadDefaultMarketWatch();
    
    Swal.fire({
        icon: 'success',
        title: 'Refreshed',
        text: 'Default market watch list has been refreshed with latest market data.',
        background: '#1a1a1a',
        color: '#fff',
        timer: 1500,
        showConfirmButton: false
    });
}

function refreshUserList() {
    console.log('Refreshing user market watch list...');
    // Reload user watchlist from API
    loadUserWatchlist();
    
    Swal.fire({
        icon: 'success',
        title: 'Refreshed',
        text: 'Your market watch list has been refreshed with latest data.',
        background: '#1a1a1a',
        color: '#fff',
        timer: 1500,
        showConfirmButton: false
    });
}

function refreshMarketWatch() {
    refreshDefaultList();
    refreshUserList();
}

// Pagination functions for user list
function previousUserPage() {
    console.log('Previous user page');
}

function nextUserPage() {
    console.log('Next user page');
}

// Export function
function exportMarketWatch() {
    var data = {
        defaultList: 'Default market watch data',
        userList: userMarketWatchData
    };
    
    var dataStr = JSON.stringify(data, null, 2);
    var dataBlob = new Blob([dataStr], {type: 'application/json'});
    var url = URL.createObjectURL(dataBlob);
    var link = document.createElement('a');
    link.href = url;
    link.download = 'market_watch_export.json';
    link.click();
    URL.revokeObjectURL(url);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Load both market watch lists
    loadDefaultMarketWatch();
    loadUserWatchlist();
    
    // Initialize advanced symbol modal
    initializeAdvancedSymbolModal();
    
    // Auto-uppercase symbol input
    var symbolInput = document.getElementById('symbolSearchInput');
    if (symbolInput) {
        symbolInput.addEventListener('input', function() {
            this.value = this.value.toUpperCase();
        });
        
        // Enter key submission
        symbolInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                // Don't submit, just search
            }
        });
    }
    
    // Hide suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('#symbolSearchInput') && !e.target.closest('#symbolSuggestions')) {
            hideSuggestions();
        }
    });
});