var ordersData = [];
var refreshInterval = null;
var currentSortColumn = '';
var currentSortDirection = 'asc';
var currentFilter = 'all';

// Load orders when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadOrdersData();
    // Auto-refresh every 30 seconds
    refreshInterval = setInterval(loadOrdersData, 30000);
});

// Clear interval when page unloads
window.addEventListener('beforeunload', function() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});

async function loadOrdersData() {
    try {
        console.log('Fetching orders data...');
        var response = await fetch('/api/orders', {
            credentials: 'same-origin', // Include cookies
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        console.log('Orders response status:', response.status);
        var data = await response.json();
        console.log('Orders response data:', data);

        if (data.success) {
            ordersData = data.orders || [];
            console.log('Orders loaded:', ordersData.length, 'orders');
            updateOrdersTable(ordersData);
            updateOrdersSummary(ordersData);
        } else {
            console.error('Failed to load orders:', data.error || data.message);
            if (data.error && data.error.includes('Not authenticated')) {
                console.log('User not authenticated, showing login message');
                showAuthenticationErrorOrders();
            } else {
                showNoOrdersMessage();
            }
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
        icon.className = 'fas fa-sort ms-1';
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

    var displayOrders = orders;
    displayOrders.forEach(function(order) {
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
    document.getElementById('totalOrdersCount').textContent = totalOrders;
    document.getElementById('completedOrdersCount').textContent = completed;
    document.getElementById('pendingOrdersCount').textContent = pending;
    document.getElementById('rejectedOrdersCount').textContent = rejected;
    document.getElementById('cancelledOrdersCount').textContent = cancelled;
    document.getElementById('buyOrdersCount').textContent = buyOrders;

    // Update available margin
    updateAvailableMargin();
}

function showNoOrdersMessage() {
    var tableBody = document.getElementById('ordersTableBody');
    tableBody.innerHTML = `
        <tr>
            <td colspan="10" class="text-center py-5">
                <i class="fas fa-list-alt fa-3x text-muted mb-3"></i>
                <h4 class="text-muted">No Orders Found</h4>
                <p class="text-muted">You haven't placed any orders yet.</p>
                <button class="btn btn-primary" onclick="window.location.href='/dashboard'">
                    <i class="fas fa-plus me-1"></i>Place First Order
                </button>
            </td>
        </tr>
    `;

    // Reset summary counts
    document.getElementById('totalOrdersCount').textContent = '0';
    document.getElementById('completedOrdersCount').textContent = '0';
    document.getElementById('pendingOrdersCount').textContent = '0';
    document.getElementById('rejectedOrdersCount').textContent = '0';
    document.getElementById('cancelledOrdersCount').textContent = '0';
    document.getElementById('buyOrdersCount').textContent = '0';

    // Update available margin even when no orders
    updateAvailableMargin();
}

function showAuthenticationErrorOrders() {
    var tableBody = document.getElementById('ordersTableBody');
    tableBody.innerHTML = `
        <tr>
            <td colspan="10" class="text-center py-5">
                <i class="fas fa-lock fa-3x text-warning mb-3"></i>
                <h4 class="text-warning">Authentication Required</h4>
                <p class="text-muted">Please log in to your Kotak Neo account to view orders.</p>
                <button class="btn btn-warning" onclick="window.location.href='/trading-account/login'">
                    <i class="fas fa-sign-in-alt me-1"></i>Login to Kotak Neo
                </button>
            </td>
        </tr>
    `;

    // Reset summary counts
    document.getElementById('totalOrdersCount').textContent = '0';
    document.getElementById('completedOrdersCount').textContent = '0';
    document.getElementById('pendingOrdersCount').textContent = '0';
    document.getElementById('rejectedOrdersCount').textContent = '0';
    document.getElementById('cancelledOrdersCount').textContent = '0';
    document.getElementById('buyOrdersCount').textContent = '0';

    // Update available margin even when no orders
    updateAvailableMargin();
}

async function refreshOrdersTable() {
    var button = document.querySelector('[onclick="refreshOrdersTable()"]');
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

function modifyOrder(orderId) {
    document.getElementById('modifyOrderId').value = orderId;
    new bootstrap.Modal(document.getElementById('modifyOrderModal')).show();
}

async function submitModifyOrder() {
    var form = document.getElementById('modifyOrderForm');
    var formData = new FormData(form);
    var orderData = Object.fromEntries(formData.entries());

    try {
        var response = await fetch('/api/modify_order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(orderData)
        });

        var data = await response.json();

        if (data.success) {
            showNotification('Order modified successfully!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('modifyOrderModal')).hide();
            await loadOrdersData(); // Refresh the table
        } else {
            showNotification('Failed to modify order: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error modifying order', 'error');
    }
}

async function cancelOrder(orderId) {
    // Show SweetAlert confirmation popup
    Swal.fire({
        title: 'Cancel Order?',
        text: 'Are you sure you want to cancel this order? This action cannot be undone.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Yes, Cancel Order',
        cancelButtonText: 'No, Keep Order',
        background: '#2d3748',
        color: '#ffffff',
        customClass: {
            popup: 'swal-dark-popup',
            title: 'swal-dark-title',
            content: 'swal-dark-content'
        }
    }).then(async (result) => {
        if (result.isConfirmed) {
            // Show loading spinner
            Swal.fire({
                title: 'Cancelling Order...',
                text: 'Please wait while we cancel your order.',
                icon: 'info',
                allowOutsideClick: false,
                allowEscapeKey: false,
                showConfirmButton: false,
                background: '#2d3748',
                color: '#ffffff',
                didOpen: () => {
                    Swal.showLoading()
                }
            });

            try {
                var response = await fetch('/api/cancel_order', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({order_id: orderId, isVerify: true})
                });

                var data = await response.json();

                if (data.success) {
                    Swal.fire({
                        title: 'Order Cancelled!',
                        text: 'Your order has been cancelled successfully.',
                        icon: 'success',
                        confirmButtonColor: '#28a745',
                        background: '#2d3748',
                        color: '#ffffff',
                        timer: 3000,
                        timerProgressBar: true
                    });
                    await loadOrdersData(); // Refresh the table
                } else {
                    Swal.fire({
                        title: 'Cancellation Failed',
                        text: 'Failed to cancel order: ' + (data.message || 'Unknown error'),
                        icon: 'error',
                        confirmButtonColor: '#dc3545',
                        background: '#2d3748',
                        color: '#ffffff'
                    });
                }
            } catch (error) {
                console.error('Error:', error);
                Swal.fire({
                    title: 'Error',
                    text: 'An error occurred while cancelling the order. Please try again.',
                    icon: 'error',
                    confirmButtonColor: '#dc3545',
                    background: '#2d3748',
                    color: '#ffffff'
                });
            }
        }
    });
}

function viewOrderDetails(orderId) {
    var order = ordersData.find(o => (o.nOrdNo || o.orderId || o.exchOrdId) === orderId);

    document.getElementById('orderDetailsContent').innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6 class="text-info mb-3">Order Information</h6>
                <table class="table table-sm table-dark">
                    <tr><td><strong>Order ID:</strong></td><td>${orderId}</td></tr>
                    <tr><td><strong>Symbol:</strong></td><td>${order?.trdSym || order?.sym || 'N/A'}</td></tr>
                    <tr><td><strong>Type:</strong></td><td>${order?.transType || 'N/A'}</td></tr>
                    <tr><td><strong>Product:</strong></td><td>${order?.prod || 'N/A'}</td></tr>
                    <tr><td><strong>Exchange:</strong></td><td>${order?.exSeg || 'N/A'}</td></tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6 class="text-info mb-3">Order Details</h6>
                <table class="table table-sm table-dark">
                    <tr><td><strong>Quantity:</strong></td><td>${order?.qty || '0'}</td></tr>
                    <tr><td><strong>Price:</strong></td><td>₹${parseFloat(order?.prc || 0).toFixed(2)}</td></tr>
                    <tr><td><strong>Status:</strong></td><td>${order?.ordSt || order?.status || 'N/A'}</td></tr>
                    <tr><td><strong>Time:</strong></td><td>${order?.orderTime || order?.ordEntTm || 'N/A'}</td></tr>
                    <tr><td><strong>Filled Qty:</strong></td><td>${order?.filledQty || '0'}</td></tr>
                </table>
            </div>
        </div>
        ${order?.rejRsn ? `
            <div class="alert alert-danger mt-3">
                <strong>Rejection Reason:</strong> ${order.rejRsn}
            </div>
        ` : ''}
    `;

    new bootstrap.Modal(document.getElementById('orderDetailsModal')).show();
}

function showNotification(message, type = 'info') {
    var toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(toast);

    // Auto-remove after 5 seconds
    setTimeout(function() {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 5000);
}

async function updateAvailableMargin() {
    try {
        var response = await fetch('/api/dashboard-data');
        var data = await response.json();

        if (data && data.limits) {
            // Try different possible field names for available margin from API
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
        } else {
            console.log('No limits data available from API');
            var marginElement = document.getElementById('availableMarginAmount');
            if (marginElement) {
                marginElement.textContent = '₹0.00';
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

// Add filter card click functionality
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.filter-card').forEach(function(card) {
        card.addEventListener('click', function() {
            var filter = this.getAttribute('data-filter');
            currentFilter = filter;

            // Remove active class from all cards
            document.querySelectorAll('.filter-card').forEach(function(c) {
                c.style.opacity = '0.7';
            });

            // Add active class to clicked card
            this.style.opacity = '1';

            // Update table with filtered data
            updateOrdersTable(ordersData);
        });
    });
});