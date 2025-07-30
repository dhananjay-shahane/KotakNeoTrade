// Deals JavaScript functionality
let currentDealsData = [];
let filteredDealsData = [];
let currentPage = 1;
let itemsPerPage = 50;
let sortColumn = 'timestamp';
let sortDirection = 'desc';
let autoRefreshInterval = null;
let autoRefreshEnabled = true;
let refreshIntervalMs = 30000; // 30 seconds default

// Column configuration
const defaultColumns = [
    'symbol', 'orderType', 'quantity', 'price', 'timestamp', 'status', 'pnl', 'actions'
];

let visibleColumns = [...defaultColumns];

// Initialize deals page
document.addEventListener('DOMContentLoaded', function() {
    initializeDeals();
});

function initializeDeals() {
    loadDeals();
    setupAutoRefresh();
    generateColumnSettings();
    
    // Setup auto-refresh toggle
    const autoRefreshToggle = document.getElementById('autoRefreshToggle');
    if (autoRefreshToggle) {
        autoRefreshToggle.addEventListener('change', function() {
            autoRefreshEnabled = this.checked;
            if (autoRefreshEnabled) {
                setupAutoRefresh();
            } else {
                clearInterval(autoRefreshInterval);
            }
        });
    }
}

function loadDeals() {
    fetch('/api/deals')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentDealsData = data.deals || [];
                filteredDealsData = [...currentDealsData];
                updateTable();
                updateCounts();
            } else {
                console.error('Failed to load deals:', data.message);
                showError('Failed to load deals data');
            }
        })
        .catch(error => {
            console.error('Error loading deals:', error);
            showError('Error loading deals data');
        });
}

function updateTable() {
    const tableBody = document.getElementById('dealsTableBody');
    const tableHeaders = document.getElementById('tableHeaders');
    
    if (!tableBody || !tableHeaders) return;
    
    // Generate headers
    tableHeaders.innerHTML = generateTableHeaders();
    
    // Sort data
    const sortedData = sortData(filteredDealsData);
    
    // Paginate data
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginatedData = sortedData.slice(startIndex, endIndex);
    
    // Generate table rows
    tableBody.innerHTML = paginatedData.map(deal => generateTableRow(deal)).join('');
    
    updatePagination();
}

function generateTableHeaders() {
    return visibleColumns.map(column => {
        const columnConfig = getColumnConfig(column);
        const sortIcon = getSortIcon(column);
        
        if (column === 'actions') {
            return `<th class="text-center" style="width: 120px;">Actions</th>`;
        }
        
        return `
            <th class="sortable" onclick="sortTable('${column}')" style="cursor: pointer;">
                ${columnConfig.label}
                ${sortIcon}
            </th>
        `;
    }).join('');
}

function generateTableRow(deal) {
    const rowClass = deal.status === 'CLOSED' ? 'table-secondary opacity-75' : '';
    
    return `
        <tr class="${rowClass}" data-deal-id="${deal.id}">
            ${visibleColumns.map(column => generateTableCell(deal, column)).join('')}
        </tr>
    `;
}

function generateTableCell(deal, column) {
    switch (column) {
        case 'symbol':
            return `<td class="fw-bold text-primary">${deal.symbol}</td>`;
        case 'orderType':
            const typeClass = deal.order_type === 'BUY' ? 'text-success' : 'text-danger';
            return `<td><span class="badge bg-dark ${typeClass}">${deal.order_type}</span></td>`;
        case 'quantity':
            return `<td>${deal.quantity}</td>`;
        case 'price':
            return `<td>₹${parseFloat(deal.price).toFixed(2)}</td>`;
        case 'timestamp':
            return `<td>${formatDateTime(deal.timestamp)}</td>`;
        case 'status':
            return `<td><span class="badge ${getStatusBadgeClass(deal.status)}">${deal.status}</span></td>`;
        case 'pnl':
            const pnl = parseFloat(deal.pnl || 0);
            const pnlClass = pnl >= 0 ? 'text-success' : 'text-danger';
            return `<td class="${pnlClass}">₹${pnl.toFixed(2)}</td>`;
        case 'actions':
            return generateActionsCell(deal);
        default:
            return `<td>${deal[column] || '-'}</td>`;
    }
}

function generateActionsCell(deal) {
    if (deal.status === 'CLOSED') {
        return `
            <td class="text-center">
                <button class="btn btn-sm btn-outline-info" onclick="editExitDate(${deal.id})" title="Edit Exit Date">
                    <i class="fas fa-calendar-alt"></i>
                </button>
            </td>
        `;
    }
    
    return `
        <td class="text-center">
            <div class="btn-group" role="group">
                <button class="btn btn-sm btn-outline-warning" onclick="editDeal(${deal.id})" title="Edit Deal">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="closeDeal(${deal.id})" title="Close Deal">
                    <i class="fas fa-times-circle"></i>
                </button>
            </div>
        </td>
    `;
}

function editDeal(dealId) {
    const deal = currentDealsData.find(d => d.id === dealId);
    if (!deal) {
        showError('Deal not found');
        return;
    }
    
    // Populate edit modal
    document.getElementById('editDealId').value = deal.id;
    document.getElementById('editSymbol').value = deal.symbol;
    document.getElementById('editQuantity').value = deal.quantity;
    document.getElementById('editTargetPrice').value = deal.target_price || deal.price;
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('editDealModal'));
    modal.show();
}

function submitEditDeal() {
    const dealId = document.getElementById('editDealId').value;
    const quantity = document.getElementById('editQuantity').value;
    const targetPrice = document.getElementById('editTargetPrice').value;
    
    if (!quantity || !targetPrice) {
        showError('Please fill all required fields');
        return;
    }
    
    const data = {
        quantity: parseInt(quantity),
        target_price: parseFloat(targetPrice)
    };
    
    fetch(`/api/deals/${dealId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess('Deal updated successfully');
            bootstrap.Modal.getInstance(document.getElementById('editDealModal')).hide();
            loadDeals(); // Refresh data
        } else {
            showError(data.message || 'Failed to update deal');
        }
    })
    .catch(error => {
        console.error('Error updating deal:', error);
        showError('Error updating deal');
    });
}

function closeDeal(dealId) {
    const deal = currentDealsData.find(d => d.id === dealId);
    if (!deal) {
        showError('Deal not found');
        return;
    }
    
    // Populate close modal
    document.getElementById('closeDealId').value = deal.id;
    document.getElementById('closeSymbol').value = deal.symbol;
    
    // Set today's date as default
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('exitDate').value = today;
    document.getElementById('exitDate').max = today;
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('closeDealModal'));
    modal.show();
}

function submitCloseDeal() {
    const dealId = document.getElementById('closeDealId').value;
    const exitDate = document.getElementById('exitDate').value;
    
    if (!exitDate) {
        showError('Please select an exit date');
        return;
    }
    
    const data = {
        exit_date: exitDate,
        status: 'CLOSED'
    };
    
    fetch(`/api/deals/${dealId}/close`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess('Deal closed successfully');
            bootstrap.Modal.getInstance(document.getElementById('closeDealModal')).hide();
            loadDeals(); // Refresh data
        } else {
            showError(data.message || 'Failed to close deal');
        }
    })
    .catch(error => {
        console.error('Error closing deal:', error);
        showError('Error closing deal');
    });
}

function editExitDate(dealId) {
    const deal = currentDealsData.find(d => d.id === dealId);
    if (!deal) {
        showError('Deal not found');
        return;
    }
    
    // Populate edit exit date modal
    document.getElementById('editExitDealId').value = deal.id;
    document.getElementById('editExitSymbol').value = deal.symbol;
    document.getElementById('editExitDateInput').value = deal.exit_date || '';
    
    // Set max date to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('editExitDateInput').max = today;
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('editExitDateModal'));
    modal.show();
}

function submitEditExitDate() {
    const dealId = document.getElementById('editExitDealId').value;
    const exitDate = document.getElementById('editExitDateInput').value;
    
    if (!exitDate) {
        showError('Please select an exit date');
        return;
    }
    
    const data = {
        exit_date: exitDate
    };
    
    fetch(`/api/deals/${dealId}/exit-date`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess('Exit date updated successfully');
            bootstrap.Modal.getInstance(document.getElementById('editExitDateModal')).hide();
            loadDeals(); // Refresh data
        } else {
            showError(data.message || 'Failed to update exit date');
        }
    })
    .catch(error => {
        console.error('Error updating exit date:', error);
        showError('Error updating exit date');
    });
}

// Utility functions
function getColumnConfig(column) {
    const configs = {
        symbol: { label: 'Symbol' },
        orderType: { label: 'Type' },
        quantity: { label: 'Quantity' },
        price: { label: 'Price' },
        timestamp: { label: 'Date/Time' },
        status: { label: 'Status' },
        pnl: { label: 'P&L' },
        actions: { label: 'Actions' }
    };
    return configs[column] || { label: column };
}

function getSortIcon(column) {
    if (sortColumn !== column) {
        return '<i class="fas fa-sort text-muted ms-1"></i>';
    }
    
    const icon = sortDirection === 'asc' ? 'fa-sort-up' : 'fa-sort-down';
    return `<i class="fas ${icon} text-primary ms-1"></i>`;
}

function getStatusBadgeClass(status) {
    const classes = {
        'EXECUTED': 'bg-success',
        'PENDING': 'bg-warning text-dark',
        'CANCELLED': 'bg-secondary',
        'REJECTED': 'bg-danger',
        'CLOSED': 'bg-info text-dark'
    };
    return classes[status] || 'bg-secondary';
}

function formatDateTime(timestamp) {
    if (!timestamp) return '-';
    const date = new Date(timestamp);
    return date.toLocaleString();
}

function sortData(data) {
    return [...data].sort((a, b) => {
        let aValue = a[sortColumn];
        let bValue = b[sortColumn];
        
        // Handle numeric sorting
        if (['quantity', 'price', 'pnl'].includes(sortColumn)) {
            aValue = parseFloat(aValue) || 0;
            bValue = parseFloat(bValue) || 0;
        }
        
        if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
        if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
        return 0;
    });
}

function sortTable(column) {
    if (sortColumn === column) {
        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        sortColumn = column;
        sortDirection = 'asc';
    }
    
    updateTable();
}

function updateCounts() {
    const totalCount = currentDealsData.length;
    const showingCount = filteredDealsData.length;
    
    document.getElementById('totalCount').textContent = totalCount;
    document.getElementById('showingCount').textContent = showingCount;
}

function updatePagination() {
    const totalPages = Math.ceil(filteredDealsData.length / itemsPerPage);
    
    document.getElementById('currentPage').textContent = currentPage;
    document.getElementById('totalPages').textContent = totalPages;
    
    document.getElementById('prevBtn').disabled = currentPage === 1;
    document.getElementById('nextBtn').disabled = currentPage === totalPages;
}

function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        updateTable();
    }
}

function nextPage() {
    const totalPages = Math.ceil(filteredDealsData.length / itemsPerPage);
    if (currentPage < totalPages) {
        currentPage++;
        updateTable();
    }
}

function refreshDeals() {
    loadDeals();
}

function setupAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    if (autoRefreshEnabled) {
        autoRefreshInterval = setInterval(() => {
            loadDeals();
        }, refreshIntervalMs);
    }
}

function setRefreshInterval(intervalMs, displayText) {
    refreshIntervalMs = intervalMs;
    document.getElementById('currentInterval').textContent = displayText;
    setupAutoRefresh();
}

function showSuccess(message) {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            icon: 'success',
            title: 'Success',
            text: message,
            timer: 3000,
            showConfirmButton: false
        });
    } else {
        alert(message);
    }
}

function showError(message) {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: message
        });
    } else {
        alert(message);
    }
}

function generateColumnSettings() {
    // Implementation for column settings
}

function applyColumnSettings() {
    // Implementation for applying column settings
}

function performSearch() {
    // Implementation for search functionality
}

function clearSearch() {
    // Implementation for clearing search
}

function applyFilters() {
    // Implementation for applying filters
}

function clearFilters() {
    // Implementation for clearing filters
}

function exportDeals() {
    // Implementation for exporting deals
}