
var ordersData = [];
var refreshInterval = null;
var currentSortColumn = '';
var currentSortDirection = 'asc';
var currentFilter = 'all';

// Load orders when page loads
function initializeOrdersPage() {
    loadOrdersData();
    // Auto-refresh every 30 seconds
    refreshInterval = setInterval(loadOrdersData, 30000);
}

// Clear interval when page unloads
function cleanupOrdersPage() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

async function loadOrdersData() {
    try {
        var response = await fetch('/api/kotak/orders');
        var data = await response.json();

        if (data.success) {
            ordersData = data.orders || [];
            updateOrdersTable(ordersData);
            updateOrdersSummary(ordersData);
        } else {
            console.error('Failed to load orders:', data.message);
            showNoOrdersMessage();
        }
    } catch (error) {
        console.error('Error loading orders:', error);
        showNoOrdersMessage();
    }
}

function filterOrders(orders, filter) {
    if (filter === 'all') return orders;
    
    return orders.filter(function(order) {
        var status = (order.ordSt || order.status || '').toLowerCase();
        var transType = order.transType || order.transactionType || '';
        
        switch(filter) {
            case 'completed':
                return status.includes('complete') || status.includes('executed');
            case 'pending':
                return status.includes('pending') || status.includes('open');
            case 'rejected':
                return status.includes('reject');
            case 'cancelled':
                return status.includes('cancel');
            case 'buy':
                return transType === 'BUY';
            default:
                return true;
        }
    });
}

function sortTable(column) {
    if (currentSortColumn === column) {
        currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        currentSortColumn = column;
        currentSortDirection = 'asc';
    }
    
    // Update sort icons
    document.querySelectorAll('#ordersTable th i[id^="sort-"]').forEach(function(icon) {
        if (icon) icon.className = 'fas fa-sort ms-1';
    });
    
    var sortIcon = document.getElementById('sort-' + column);
    if (sortIcon) {
        sortIcon.className = 'fas fa-sort-' + (currentSortDirection === 'asc' ? 'up' : 'down') + ' ms-1';
    }
    
    // Sort the data
    ordersData.sort(function(a, b) {
        var aVal, bVal;
        
        switch(column) {
            case 'symbol':
                aVal = (a.trdSym || a.sym || '').toLowerCase();
                bVal = (b.trdSym || b.sym || '').toLowerCase();
                break;
            case 'time':
                aVal = a.orderTime || a.ordEntTm || '';
                bVal = b.orderTime || b.ordEntTm || '';
                break;
            case 'orderid':
                aVal = a.nOrdNo || a.orderId || '';
                bVal = b.nOrdNo || b.orderId || '';
                break;
            case 'type':
                aVal = (a.transType || '').toLowerCase();
                bVal = (b.transType || '').toLowerCase();
                break;
            case 'quantity':
                aVal = parseFloat(a.qty || 0);
                bVal = parseFloat(b.qty || 0);
                break;
            case 'price':
                aVal = parseFloat(a.prc || 0);
                bVal = parseFloat(b.prc || 0);
                break;
            case 'status':
                aVal = (a.ordSt || a.status || '').toLowerCase();
                bVal = (b.ordSt || b.status || '').toLowerCase();
                break;
            case 'product':
                aVal = (a.prod || '').toLowerCase();
                bVal = (b.prod || '').toLowerCase();
                break;
            case 'exchange':
                aVal = (a.exSeg || '').toLowerCase();
                bVal = (b.exSeg || '').toLowerCase();
                break;
            default:
                return 0;
        }
        
        if (typeof aVal === 'string' && typeof bVal === 'string') {
            return currentSortDirection === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        } else {
            return currentSortDirection === 'asc' ? aVal - bVal : bVal - aVal;
        }
    });
    
    updateOrdersTable(ordersData);
}

function updateOrdersTable(orders) {
    var tableBody = document.getElementById('ordersTableBody');
    if (!tableBody) return;

    if (!orders || orders.length === 0) {
        showNoOrdersMessage();
        return;
    }

    var tableHTML = '';
    var displayOrders = filterOrders(orders, currentFilter);

    displayOrders.forEach(function(order) {
        var orderTime = order.orderTime || order.ordEntTm || order.exchOrdId || 'N/A';
        var orderId = order.nOrdNo || order.orderId || order.exchOrdId || 'N/A';
        var symbol = order.trdSym || order.sym || order.tradingSymbol || 'N/A';
        var transactionType = order.transType || order.transactionType || 'N/A';
        var quantity = order.qty || order.quantity || '0';
        var filledQty = order.filledQty || order.fillShares || '0';
        var price = order.prc || order.price || '0';
        var orderType = order.ordTyp || order.orderType || 'N/A';
        var status = order.ordSt || order.status || order.orderStatus || 'N/A';
        var product = order.prod || order.product || 'N/A';
        var exchange = order.exSeg || order.exchange || order.exchangeSegment || 'N/A';
        var rejectionReason = order.rejRsn || order.rejectionReason || '';
        
        // Clean up long RMS error messages
        if (rejectionReason.includes('RMS:Margin Exceeds')) {
            rejectionReason = 'RMS: Margin Exceeds';
        }

        // Format price
        var formattedPrice = parseFloat(price) || 0;

        // Status badge styling
        var statusClass = 'bg-info';
        var statusLower = status.toLowerCase();
        if (statusLower.includes('complete') || statusLower.includes('executed')) {
            statusClass = 'bg-success';
        } else if (statusLower.includes('reject')) {
            statusClass = 'bg-danger';
        } else if (statusLower.includes('cancel')) {
            statusClass = 'bg-secondary';
        } else if (statusLower.includes('pending') || statusLower.includes('open')) {
            statusClass = 'bg-warning';
        }

        // Transaction type badge styling
        var transTypeClass = transactionType === 'BUY' ? 'bg-success' : 'bg-danger';

        tableHTML += `
            <tr data-order-id="${orderId}">
                <td>
                    <small>${orderTime}</small>
                </td>
                <td>
                    <small class="text-muted">${orderId}</small>
                </td>
                <td>
                    <strong>${symbol}</strong>
                </td>
                <td>
                    <span class="badge ${transTypeClass}">
                        ${transactionType}
                    </span>
                </td>
                <td>
                    ${quantity}
                    ${filledQty && filledQty !== '0' ? 
                        `<br><small class="text-success">Filled: ${filledQty}</small>` : ''
                    }
                </td>
                <td>
                    ₹${formattedPrice.toFixed(2)}
                    ${orderType !== 'N/A' ? 
                        `<br><small class="text-muted">${orderType}</small>` : ''
                    }
                </td>
                <td>
                    <span class="badge ${statusClass}">
                        ${status}
                    </span>
                    ${rejectionReason ? 
                        `<br><small class="text-danger">${rejectionReason}</small>` : ''
                    }
                </td>
                <td>
                    <span class="badge bg-info">${product}</span>
                </td>
                <td>
                    <span class="badge bg-secondary">${exchange}</span>
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        ${!statusLower.includes('complete') && !statusLower.includes('reject') && !statusLower.includes('cancel') ? `
                            <button class="btn btn-warning btn-sm" onclick="modifyOrder('${orderId}')" title="Modify Order">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-danger btn-sm" onclick="cancelOrder('${orderId}')" title="Cancel Order">
                                <i class="fas fa-times"></i>
                            </button>
                        ` : ''}
                        <button class="btn btn-info btn-sm" onclick="viewOrderDetails('${orderId}')" title="View Details">
                            <i class="fas fa-info"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });

    tableBody.innerHTML = tableHTML;

    // Add update animation
    tableBody.classList.add('data-updated');
    setTimeout(function() {
        tableBody.classList.remove('data-updated');
    }, 1000);
}

function updateOrdersSummary(orders) {
    var totalOrders = orders.length;
    var completed = 0, pending = 0, rejected = 0, cancelled = 0, buyOrders = 0;

    orders.forEach(function(order) {
        var status = (order.ordSt || order.status || '').toLowerCase();
        var transType = order.transType || order.transactionType || '';

        if (status.includes('complete') || status.includes('executed')) {
            completed++;
        } else if (status.includes('pending') || status.includes('open')) {
            pending++;
        } else if (status.includes('reject')) {
            rejected++;
        } else if (status.includes('cancel')) {
            cancelled++;
        }

        if (transType === 'BUY') {
            buyOrders++;
        }
    });

    // Update summary counts
    var summaryElements = {
        'totalOrdersCount': totalOrders,
        'completedOrdersCount': completed,
        'pendingOrdersCount': pending,
        'rejectedOrdersCount': rejected,
        'cancelledOrdersCount': cancelled,
        'buyOrdersCount': buyOrders
    };

    Object.keys(summaryElements).forEach(function(id) {
        var element = document.getElementById(id);
        if (element) {
            element.textContent = summaryElements[id];
        }
    });
    
    // Update available margin
    updateAvailableMargin();
}

function showNoOrdersMessage() {
    var tableBody = document.getElementById('ordersTableBody');
    if (!tableBody) return;
    
    tableBody.innerHTML = `
        <tr>
            <td colspan="10" class="text-center py-5">
                <i class="fas fa-list-alt fa-3x text-muted mb-3"></i>
                <h4 class="text-muted">No Orders Found</h4>
                <p class="text-muted">You haven't placed any orders yet.</p>
            </td>
        </tr>
    `;

    // Reset summary counts
    var summaryIds = ['totalOrdersCount', 'completedOrdersCount', 'pendingOrdersCount', 'rejectedOrdersCount', 'cancelledOrdersCount', 'buyOrdersCount'];
    summaryIds.forEach(function(id) {
        var element = document.getElementById(id);
        if (element) element.textContent = '0';
    });
    
    // Update available margin even when no orders
    updateAvailableMargin();
}

async function refreshOrdersTable() {
    var button = document.querySelector('[onclick="refreshOrdersTable()"]');
    if (!button) return;
    
    var originalHtml = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Refreshing...';
    button.disabled = true;

    try {
        await loadOrdersData();
        showNotification('Orders refreshed successfully', 'success');
    } catch (error) {
        console.error('Error refreshing orders:', error);
        showNotification('Error refreshing orders', 'error');
    } finally {
        button.innerHTML = originalHtml;
        button.disabled = false;
    }
}

async function updateAvailableMargin() {
    try {
        var response = await fetch('/api/kotak/dashboard-data');
        var data = await response.json();
        
        if (data && data.limits) {
            var availableMargin = parseFloat(
                data.limits.Net || 
                data.limits.available_margin || 
                data.limits.availableMargin ||
                data.limits.cash ||
                data.limits.available_cash ||
                0
            );
            
            var marginElement = document.getElementById('availableMarginAmount');
            if (marginElement) {
                marginElement.textContent = '₹' + availableMargin.toLocaleString('en-IN', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
            }
        }
    } catch (error) {
        console.error('Error fetching available margin:', error);
        var marginElement = document.getElementById('availableMarginAmount');
        if (marginElement) {
            marginElement.textContent = '₹0.00';
        }
    }
}

function showNotification(message, type = 'info') {
    if (typeof showToaster === 'function') {
        showToaster('Orders', message, type);
    }
}

// Add filter functionality
function setOrdersFilter(filter) {
    currentFilter = filter;
    
    // Remove active class from all filter cards
    document.querySelectorAll('.filter-card').forEach(function(card) {
        card.style.opacity = '0.7';
    });
    
    // Add active class to selected filter
    var activeCard = document.querySelector(`[data-filter="${filter}"]`);
    if (activeCard) {
        activeCard.style.opacity = '1';
    }
    
    // Update table with filtered data
    updateOrdersTable(ordersData);
}
