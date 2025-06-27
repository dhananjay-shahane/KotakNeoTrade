var ordersData = [];
var refreshInterval = null;

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
        var response = await fetch('/api/orders');
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

function updateOrdersTable(orders) {
    var tableBody = document.getElementById('ordersTableBody');

    if (!orders || orders.length === 0) {
        showNoOrdersMessage();
        return;
    }

    var tableHTML = '';
    var displayOrders = orders; // Initialize displayOrders with all orders

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
    setTimeout(()=>{}, function() {
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
}

function showNoOrdersMessage() {
    var tableBody = document.getElementById('ordersTableBody');
    tableBody.innerHTML = `
        <tr>
            <td colspan="10" class="text-center py-5">
                <i class="fas fa-list-alt fa-3x text-muted mb-3"></i>
                <h4 class="text-muted">No Orders Found</h4>
                <p class="text-muted">You haven't placed any orders yet.</p>
                <a href="/dashboard" class="btn btn-primary">
                    <i class="fas fa-plus me-1"></i>Place First Order
                </a>
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
    if (confirm('Are you sure you want to cancel this order?')) {
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
                showNotification('Order cancelled successfully!', 'success');
                await loadOrdersData(); // Refresh the table
            } else {
                showNotification('Failed to cancel order: ' + data.message, 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Error cancelling order', 'error');
        }
    }
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
    setTimeout(()=>{}, function() {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 5000);
}