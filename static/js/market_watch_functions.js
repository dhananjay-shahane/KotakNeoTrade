// Market Watch Functionality

// User market watch data storage
var userMarketWatchData = [];
var userIdCounter = 1;

// Add symbol to user list from default list
function addToUserList(symbol) {
    // Check if symbol already exists
    var exists = userMarketWatchData.some(function(item) {
        return item.symbol === symbol;
    });
    
    if (exists) {
        Swal.fire({
            icon: 'warning',
            title: 'Symbol Already Added',
            text: symbol + ' is already in your market watch list.',
            background: '#1a1a1a',
            color: '#fff'
        });
        return;
    }
    
    // Generate sample data for the symbol
    var newSymbol = generateSymbolData(symbol, userIdCounter++);
    userMarketWatchData.push(newSymbol);
    
    updateUserMarketWatchTable();
    updateUserCounts();
    
    Swal.fire({
        icon: 'success',
        title: 'Symbol Added',
        text: symbol + ' has been added to your market watch list.',
        background: '#1a1a1a',
        color: '#fff',
        timer: 2000,
        showConfirmButton: false
    });
}

// Submit add symbol form
function submitAddSymbol() {
    var symbolInput = document.getElementById('symbolInput');
    var symbol = symbolInput.value.trim().toUpperCase();
    
    if (!symbol) {
        Swal.fire({
            icon: 'error',
            title: 'Invalid Input',
            text: 'Please enter a valid symbol.',
            background: '#1a1a1a',
            color: '#fff'
        });
        return;
    }
    
    addToUserList(symbol);
    
    // Close modal and clear form
    var modal = bootstrap.Modal.getInstance(document.getElementById('addSymbolModal'));
    modal.hide();
    symbolInput.value = '';
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
            userMarketWatchData = userMarketWatchData.filter(function(item) {
                return item.id !== id;
            });
            
            updateUserMarketWatchTable();
            updateUserCounts();
            
            Swal.fire({
                icon: 'success',
                title: 'Removed',
                text: symbol.symbol + ' has been removed from your market watch.',
                background: '#1a1a1a',
                color: '#fff',
                timer: 2000,
                showConfirmButton: false
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
        var changeClass = parseFloat(item.change) > 0 ? 'profit' : parseFloat(item.change) < 0 ? 'loss' : 'neutral';
        var sevenDayClass = parseFloat(item.sevenDayPercent) > 0 ? 'profit' : parseFloat(item.sevenDayPercent) < 0 ? 'loss' : 'neutral';
        var thirtyDayClass = parseFloat(item.thirtyDayPercent) > 0 ? 'profit' : parseFloat(item.thirtyDayPercent) < 0 ? 'loss' : 'neutral';
        
        html += `
            <tr>
                <td>${item.id}</td>
                <td><strong>${item.symbol}</strong></td>
                <td class="${sevenDayClass}">${item.sevenDay}</td>
                <td class="${thirtyDayClass}">${item.thirtyDay}</td>
                <td class="${sevenDayClass}">${item.sevenDayPercent > 0 ? '+' : ''}${item.sevenDayPercent}%</td>
                <td class="${thirtyDayClass}">${item.thirtyDayPercent > 0 ? '+' : ''}${item.thirtyDayPercent}%</td>
                <td><strong>${item.cmp}</strong></td>
                <td class="${changeClass}">${item.changePercent > 0 ? '+' : ''}${item.changePercent}%</td>
                <td class="${changeClass}">${item.change > 0 ? '+' : ''}${item.cpl}</td>
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

// Update user counts
function updateUserCounts() {
    var count = userMarketWatchData.length;
    document.getElementById('userCount').textContent = count;
    document.getElementById('userTotalCount').textContent = count;
    document.getElementById('userShowingCount').textContent = count;
}

// Refresh functions
function refreshDefaultList() {
    console.log('Refreshing default market watch list...');
    // In a real implementation, this would fetch fresh data from the API
    Swal.fire({
        icon: 'success',
        title: 'Refreshed',
        text: 'Default market watch list has been refreshed.',
        background: '#1a1a1a',
        color: '#fff',
        timer: 1500,
        showConfirmButton: false
    });
}

function refreshUserList() {
    console.log('Refreshing user market watch list...');
    // Simulate real-time data update
    userMarketWatchData.forEach(function(item) {
        var updatedData = generateSymbolData(item.symbol, item.id);
        Object.assign(item, updatedData);
    });
    
    updateUserMarketWatchTable();
    
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
    // Auto-uppercase symbol input
    var symbolInput = document.getElementById('symbolInput');
    if (symbolInput) {
        symbolInput.addEventListener('input', function() {
            this.value = this.value.toUpperCase();
        });
        
        // Enter key submission
        symbolInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                submitAddSymbol();
            }
        });
    }
});