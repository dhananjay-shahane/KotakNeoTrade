
// Toaster notification system
function showToaster(title, message, type = 'info', duration = 3000) {
    // Create toaster container if it doesn't exist
    let container = document.getElementById('toasterContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toasterContainer';
        container.className = 'toaster-container';
        document.body.appendChild(container);
    }

    // Create toaster element
    const toaster = document.createElement('div');
    toaster.className = 'toaster';
    
    const iconClass = {
        success: 'fas fa-check',
        error: 'fas fa-times',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    }[type] || 'fas fa-info-circle';

    toaster.innerHTML = `
        <div class="toaster-icon ${type}">
            <i class="${iconClass}"></i>
        </div>
        <div class="toaster-content">
            <div class="toaster-title">${title}</div>
            <div class="toaster-message">${message}</div>
        </div>
        <button class="toaster-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;

    container.appendChild(toaster);

    // Trigger animation
    setTimeout(() => toaster.classList.add('show'), 10);

    // Auto remove
    setTimeout(() => {
        toaster.classList.remove('show');
        setTimeout(() => toaster.remove(), 300);
    }, duration);
}


// Missing functions that are called from the HTML
function showLoginModal() {
    const modal = new bootstrap.Modal(
        document.getElementById("loginAccountModal"),
    );
    modal.show();
}

// Mobile sidebar toggle with improved touch handling
function toggleSidebar() {
    var sidebar = document.getElementById("sidebar");
    var overlay = document.getElementById("sidebarOverlay");
    var isOpen = sidebar.classList.contains("show");

    if (isOpen) {
        sidebar.classList.remove("show");
        overlay.classList.remove("show");
        document.body.style.overflow = "";
        // Remove touch event listeners when closing
        document.removeEventListener("touchstart", handleTouchStart, {
            passive: false,
        });
        document.removeEventListener("touchmove", handleTouchMove, {
            passive: false,
        });
    } else {
        sidebar.classList.add("show");
        overlay.classList.add("show");
        document.body.style.overflow = "hidden";
        // Add touch event listeners for swipe to close
        document.addEventListener("touchstart", handleTouchStart, {
            passive: false,
        });
        document.addEventListener("touchmove", handleTouchMove, {
            passive: false,
        });
    }
}

// Touch handling for mobile sidebar
let touchStartX = 0;
let touchStartY = 0;

function handleTouchStart(event) {
    touchStartX = event.touches[0].clientX;
    touchStartY = event.touches[0].clientY;
}

function handleTouchMove(event) {
    if (!touchStartX || !touchStartY) return;

    var touchEndX = event.touches[0].clientX;
    var touchEndY = event.touches[0].clientY;
    var diffX = touchStartX - touchEndX;
    var diffY = touchStartY - touchEndY;

    // Only handle horizontal swipes
    if (Math.abs(diffX) > Math.abs(diffY)) {
        // Swipe left to close sidebar
        if (diffX > 50) {
            var sidebar = document.getElementById("sidebar");
            if (sidebar && sidebar.classList.contains("show")) {
                toggleSidebar();
            }
        }
    }

    touchStartX = 0;
    touchStartY = 0;
}

// Close sidebar when clicking outside on mobile
document.addEventListener("click", function (event) {
    var sidebar = document.getElementById("sidebar");
    var toggle = document.querySelector(".mobile-toggle");
    var overlay = document.getElementById("sidebarOverlay");

    if (
        window.innerWidth <= 992 &&
        sidebar &&
        sidebar.classList.contains("show") &&
        !sidebar.contains(event.target) &&
        !toggle.contains(event.target)
    ) {
        toggleSidebar();
    }
});

// Handle window resize
window.addEventListener("resize", function () {
    var sidebar = document.getElementById("sidebar");
    var overlay = document.getElementById("sidebarOverlay");

    if (window.innerWidth > 992) {
        sidebar.classList.remove("show");
        overlay.classList.remove("show");
        document.body.style.overflow = "";
    }
});

// Theme toggle functionality
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
    const newTheme = currentTheme === "light" ? "dark" : "light";

    document.documentElement.setAttribute("data-theme", newTheme);
    localStorage.setItem("theme", newTheme);

    // Update toggle state
    const themeToggle = document.getElementById("themeToggle");
    if (themeToggle) {
        themeToggle.checked = newTheme === "light";
    }

    // Show feedback
    if (typeof showToaster === 'function') {
        showToaster('Theme Changed', `Switched to ${newTheme} mode`, 'success');
    }
}

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.checked = savedTheme === 'light';
        themeToggle.addEventListener('change', toggleTheme);
    }
});

// Show error message
function showPageError(pageType) {
    const mainContent =
        document.querySelector(".main-content") ||
        document.querySelector(".content");
    if (mainContent) {
        mainContent.innerHTML = `
            <div class="container-fluid">
                <div class="row justify-content-center">
                    <div class="col-md-6 text-center py-5">
                        <i class="fas fa-exclamation-triangle fa-3x text-warning mb-3"></i>
                        <h3>Error Loading ${pageType.charAt(0).toUpperCase() + pageType.slice(1)}</h3>
                        <p class="text-muted">Unable to load ${pageType} content. Please try again.</p>
                        <button class="btn btn-primary" onclick="loadKotakPage('${pageType}', {preventDefault: () => {}})">
                            <i class="fas fa-refresh me-2"></i>Retry
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
}

// Initialize page-specific functionality
function initializeOrdersPage() {
    // Load orders data
    loadOrdersData();

    // Set up auto-refresh
    if (window.ordersRefreshInterval) {
        clearInterval(window.ordersRefreshInterval);
    }
    window.ordersRefreshInterval = setInterval(loadOrdersData, 30000);
}

function initializePositionsPage() {
    // Load positions data
    loadPositionsData();

    // Set up auto-refresh
    if (window.positionsRefreshInterval) {
        clearInterval(window.positionsRefreshInterval);
    }
    window.positionsRefreshInterval = setInterval(loadPositionsData, 30000);
}

function initializeHoldingsPage() {
    // Load holdings data
    loadHoldingsData();

    // Set up auto-refresh
    if (window.holdingsRefreshInterval) {
        clearInterval(window.holdingsRefreshInterval);
    }
    window.holdingsRefreshInterval = setInterval(loadHoldingsData, 30000);
}

// Table update functions
function updateOrdersTable(orders) {
    const tableBody = document.querySelector("#ordersTable tbody");
    if (!tableBody) return;

    tableBody.innerHTML = orders
        .map(
            (order) => `
        <tr>
            <td>${order.orderId || "-"}</td>
            <td>${order.tradingSymbol || "-"}</td>
            <td>${order.transactionType || "-"}</td>
            <td>${order.quantity || "-"}</td>
            <td>₹${order.price || "0"}</td>
            <td><span class="badge ${getOrderStatusClass(order.status)}">${order.status || "-"}</span></td>
            <td>${order.orderTime || "-"}</td>
        </tr>
    `,
        )
        .join("");
}

function updatePositionsTable(positions) {
    const tableBody = document.querySelector("#positionsTable tbody");
    if (!tableBody) return;

    tableBody.innerHTML = positions
        .map(
            (position) => `
        <tr>
            <td>${position.tradingSymbol || "-"}</td>
            <td>${position.netQty || "0"}</td>
            <td>₹${position.avgPrice || "0"}</td>
            <td>₹${position.ltp || "0"}</td>
            <td class="${getPnlClass(position.pnl)}">₹${position.pnl || "0"}</td>
            <td class="${getPnlClass(position.pnlPercent)}">${position.pnlPercent || "0"}%</td>
        </tr>
    `,
        )
        .join("");
}

function updateHoldingsTable(holdings) {
    const tableBody = document.querySelector("#holdingsTable tbody");
    if (!tableBody) return;

    tableBody.innerHTML = holdings
        .map(
            (holding) => `
        <tr>
            <td>${holding.tradingSymbol || "-"}</td>
            <td>${holding.quantity || "0"}</td>
            <td>₹${holding.avgPrice || "0"}</td>
            <td>₹${holding.ltp || "0"}</td>
            <td>₹${holding.investedValue || "0"}</td>
            <td>₹${holding.currentValue || "0"}</td>
            <td class="${getPnlClass(holding.pnl)}">₹${holding.pnl || "0"}</td>
        </tr>
    `,
        )
        .join("");
}

// Helper functions
function getOrderStatusClass(status) {
    switch (status?.toLowerCase()) {
        case "complete":
            return "bg-success";
        case "pending":
            return "bg-warning";
        case "cancelled":
            return "bg-danger";
        default:
            return "bg-secondary";
    }
}

function getPnlClass(value) {
    const numValue = parseFloat(value) || 0;
    return numValue >= 0 ? "text-success" : "text-danger";
}

function updatePositionsSummary(summary) {
    if (!summary) return;

    const summaryElement = document.querySelector("#positionsSummary");
    if (summaryElement) {
        summaryElement.innerHTML = `
            <div class="row">
                <div class="col-md-3">
                    <div class="summary-card">
                        <h6>Total Positions</h6>
                        <p>${summary.total_positions || 0}</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="summary-card">
                        <h6>Total P&L</h6>
                        <p class="${getPnlClass(summary.total_pnl)}">₹${summary.total_pnl || 0}</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="summary-card">
                        <h6>Long Positions</h6>
                        <p>${summary.long_positions || 0}</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="summary-card">
                        <h6>Short Positions</h6>
                        <p>${summary.short_positions || 0}</p>
                    </div>
                </div>
            </div>
        `;
    }
}

function updateHoldingsSummary(summary) {
    if (!summary) return;

    const summaryElement = document.querySelector("#holdingsSummary");
    if (summaryElement) {
        summaryElement.innerHTML = `
            <div class="row">
                <div class="col-md-4">
                    <div class="summary-card">
                        <h6>Total Holdings</h6>
                        <p>${summary.total_holdings || 0}</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="summary-card">
                        <h6>Invested Value</h6>
                        <p>₹${summary.total_invested || 0}</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="summary-card">
                        <h6>Current Value</h6>
                        <p>₹${summary.current_value || 0}</p>
                    </div>
                </div>
            </div>
        `;
    }
}

// User menu toggle
function toggleUserMenu() {
    const userMenu = document.getElementById("userMenu");
    const isVisible = userMenu.style.display !== "none";

    if (isVisible) {
        userMenu.style.display = "none";
    } else {
        userMenu.style.display = "block";
    }
}

// Close user menu when clicking outside
document.addEventListener("click", function (event) {
    const userMenu = document.getElementById("userMenu");
    const userProfile = document.querySelector(".user-profile");

    if (
        userMenu &&
        userProfile &&
        !userProfile.contains(event.target) &&
        !userMenu.contains(event.target)
    ) {
        userMenu.style.display = "none";
    }
});

// Show user profile modal
function showUserProfile() {
    const userMenu = document.getElementById("userMenu");
    userMenu.style.display = "none";

    const modal = new bootstrap.Modal(
        document.getElementById("userProfileModal"),
    );
    modal.show();
}

// Show settings modal
function showSettingsModal() {
    const modal = new bootstrap.Modal(document.getElementById("settingsModal"));
    modal.show();
}

// Font size functionality
document.addEventListener("DOMContentLoaded", function () {
    // Initialize font size
    const savedFontSize = localStorage.getItem("website-font-size") || "14";
    document.documentElement.style.setProperty("--global-font-size", savedFontSize + "px");

    const fontSizeSelect = document.getElementById("fontSizeSelect");
    const preview = document.querySelector(".font-size-preview");

    if (fontSizeSelect) {
        fontSizeSelect.value = savedFontSize;
        
        // Update preview
        if (preview) {
            preview.style.fontSize = savedFontSize + "px";
        }

        fontSizeSelect.addEventListener("change", function () {
            const fontSize = this.value;
            document.documentElement.style.setProperty("--global-font-size", fontSize + "px");
            localStorage.setItem("website-font-size", fontSize);

            // Update preview
            if (preview) {
                preview.style.fontSize = fontSize + "px";
            }

            // Show feedback
            if (typeof showToaster === 'function') {
                showToaster('Font Size Updated', `Changed to ${fontSize}px`, 'success');
            }
        });
    }
});

// Settings modal functionality
function applySettings() {
    const fontSizeSelect = document.getElementById('fontSizeSelect');
    
    if (fontSizeSelect) {
        const newFontSize = fontSizeSelect.value;
        document.documentElement.style.setProperty('--global-font-size', newFontSize + 'px');
        localStorage.setItem('website-font-size', newFontSize);
    }

    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('settingsModal'));
    if (modal) {
        modal.hide();
    }

    // Show success message
    if (typeof showToaster === 'function') {
        showToaster('Settings Applied', 'Your preferences have been saved', 'success');
    }
}

// Notification functionality
function toggleNotificationInbox() {
    const inbox = document.getElementById("notificationInbox");
    const isVisible = inbox.style.display !== "none";

    if (isVisible) {
        inbox.style.display = "none";
    } else {
        inbox.style.display = "block";
    }
}

function closeNotificationInbox() {
    const inbox = document.getElementById("notificationInbox");
    inbox.style.display = "none";
}

// Close notification inbox when clicking outside
document.addEventListener("click", function (event) {
    const inbox = document.getElementById("notificationInbox");
    const notificationContainer = document.querySelector(
        ".notification-container",
    );

    if (
        inbox &&
        notificationContainer &&
        !notificationContainer.contains(event.target)
    ) {
        inbox.style.display = "none";
    }
});

// Navigation active state
document.addEventListener("DOMContentLoaded", function () {
    const navLinks = document.querySelectorAll(".nav-link");
    const currentPath = window.location.pathname;

    navLinks.forEach((link) => {
        const href = link.getAttribute("href");
        if (href && (href === currentPath || currentPath.includes(href))) {
            link.classList.add("active");
        } else {
            link.classList.remove("active");
        }
    });
});

// Smooth transitions for theme changes
document.addEventListener("DOMContentLoaded", function () {
    // Add transition styles for smooth theme switching
    const style = document.createElement("style");
    style.textContent = `
        * {
            transition: background-color 0.3s ease, 
                       color 0.3s ease, 
                       border-color 0.3s ease !important;
        }
    `;
    document.head.appendChild(style);
});

// Initialize tooltips (if Bootstrap tooltips are used)
document.addEventListener("DOMContentLoaded", function () {
    var tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]'),
    );
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Password visibility toggle function
function togglePassword(fieldId) {
    const passwordField = document.getElementById(fieldId);
    const eyeIcon = document.getElementById(fieldId + "-eye");

    if (passwordField.type === "password") {
        passwordField.type = "text";
        eyeIcon.classList.remove("fa-eye");
        eyeIcon.classList.add("fa-eye-slash");
    } else {
        passwordField.type = "password";
        eyeIcon.classList.remove("fa-eye-slash");
        eyeIcon.classList.add("fa-eye");
    }
}

// Page loader utility (if needed)
function showPageLoader() {
    const loader = document.createElement("div");
    loader.id = "pageLoader";
    loader.innerHTML = `
        <div class="d-flex justify-content-center align-items-center" style="height: 100vh;">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
    loader.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: var(--dark-bg);
        z-index: 9999;
    `;
    document.body.appendChild(loader);
}

function hidePageLoader() {
    const loader = document.getElementById("pageLoader");
    if (loader) {
        loader.remove();
    }
}

// Utility function for AJAX requests with proper error handling
function makeRequest(url, options = {}) {
    const defaultOptions = {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
        },
    };

    const finalOptions = { ...defaultOptions, ...options };

    return fetch(url, finalOptions)
        .then((response) => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .catch((error) => {
            console.error("Request failed:", error);
            throw error;
        });
}

// Auto-update timestamp functionality (for login time, etc.)
function updateTimestamps() {
    const timestampElements = document.querySelectorAll("[data-timestamp]");
    timestampElements.forEach((element) => {
        const timestamp = element.getAttribute("data-timestamp");
        if (timestamp) {
            const date = new Date(timestamp);
            element.textContent = formatRelativeTime(date);
        }
    });
}

function formatRelativeTime(date) {
    const now = new Date();
    const diffInMs = now - date;
    const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
    const diffInHours = Math.floor(diffInMinutes / 60);
    const diffInDays = Math.floor(diffInHours / 24);

    if (diffInMinutes < 1) return "Just now";
    if (diffInMinutes < 60)
        return `${diffInMinutes} minute${diffInMinutes > 1 ? "s" : ""} ago`;
    if (diffInHours < 24)
        return `${diffInHours} hour${diffInHours > 1 ? "s" : ""} ago`;
    if (diffInDays < 7)
        return `${diffInDays} day${diffInDays > 1 ? "s" : ""} ago`;

    return date.toLocaleDateString();
}

// Run timestamp updates every minute
setInterval(updateTimestamps, 60000);

// Run initial timestamp update
document.addEventListener("DOMContentLoaded", updateTimestamps);

// Trading Account Login Functions
function showLoginModal() {
    const loginModal = new bootstrap.Modal(
        document.getElementById("loginAccountModal"),
    );
    loginModal.show();
}

// Broker redirect functions
// function showKotakLoginForm() {
//     // Remove active class from all broker cards (both desktop and mobile)
//     document.querySelectorAll(".broker-card, .broker-card-mobile").forEach((card) => {
//         card.classList.remove("active");
//     });

//     // Add active class to Kotak cards (both desktop and mobile)
//     const kotakCard = document.getElementById("kotakCard");
//     const kotakCardDesktop = document.getElementById("kotakCardDesktop");
//     if (kotakCard) kotakCard.classList.add("active");
//     if (kotakCardDesktop) kotakCardDesktop.classList.add("active");

//     document.getElementById("welcomeScreen").style.display = "none";
//     document.getElementById("kotakLoginForm").style.display = "block";
// }

// function goBackToBrokerSelection() {
//     // Remove active class from all broker cards (both desktop and mobile)
//     document
//         .querySelectorAll(".broker-card, .broker-card-mobile")
//         .forEach((card) => {
//             card.classList.remove("active");
//         });

//     document.getElementById("kotakLoginForm").style.display = "none";
//     document.getElementById("welcomeScreen").style.display = "block";
// }

function showComingSoon(brokerName) {
    Swal.fire({
        icon: "info",
        title: "Coming Soon",
        text: `${brokerName} integration is under development`,
        background: "var(--card-bg)",
        color: "var(--text-primary)",
    });
}

function togglePasswordVisibility(button) {
    const input = button.previousElementSibling;
    const icon = button.querySelector("i");

    if (input.type === "password") {
        input.type = "text";
        icon.classList.remove("fa-eye");
        icon.classList.add("fa-eye-slash");
    } else {
        input.type = "password";
        icon.classList.remove("fa-eye-slash");
        icon.classList.add("fa-eye");
    }
}

function handleKotakLogin(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const loginData = {
        mobile_number: formData.get("mobile_number"),
        ucc: formData.get("ucc"),
        mpin: formData.get("mpin"),
        totp_code: formData.get("totp_code"),
    };

    // Show loading state
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML =
        '<i class="fas fa-spinner fa-spin me-2"></i>Logging in...';
    submitBtn.disabled = true;

    // Make actual API call to Kotak Neo authentication
    fetch('/kotak/api/authenticate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(loginData)
    })
    .then(response => response.json())
    .then(data => {
        // Reset button
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;

        if (data.success) {
            // Close modal and redirect to Kotak dashboard
            const modal = bootstrap.Modal.getInstance(document.getElementById("loginAccountModal"));
            if (modal) {
                modal.hide();
            }
            
            // Show success message
            Swal.fire({
                icon: 'success',
                title: 'Login Successful',
                text: 'Successfully logged in to Kotak Neo!',
                background: 'var(--card-bg)',
                color: 'var(--text-primary)',
                timer: 2000,
                showConfirmButton: false
            });
            
            // Redirect to Kotak dashboard
            setTimeout(() => {
                window.location.href = "/kotak/dashboard";
            }, 2000);
        } else {
            // Show error message
            Swal.fire({
                icon: 'error',
                title: 'Login Failed',
                text: data.error || 'Authentication failed. Please check your credentials.',
                background: 'var(--card-bg)',
                color: 'var(--text-primary)',
            });
        }
    })
    .catch(error => {
        console.error('Error:', error);
        // Reset button
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
        
        // Show error message
        Swal.fire({
            icon: 'error',
            title: 'Connection Error',
            text: 'Unable to connect to authentication service. Please try again.',
            background: 'var(--card-bg)',
            color: 'var(--text-primary)',
        });
    });
}

// Reset modal when it's closed
document.addEventListener("DOMContentLoaded", function () {
    const loginModal = document.getElementById("loginAccountModal");
    if (loginModal) {
        loginModal.addEventListener("hidden.bs.modal", function () {
            // Reset to default state - Kotak Neo selected
            const welcomeScreen = document.getElementById("welcomeScreen");
            const kotakLoginForm = document.getElementById("kotakLoginForm");

            // if (kotakLoginForm) kotakLoginForm.style.display = "block";

            // Remove active class from all broker cards
            document.querySelectorAll(".broker-card").forEach((card) => {
                card.classList.remove("active");
            });

            // Add active class to Kotak card
            const kotakCard = document.getElementById("kotakCard");
            if (kotakCard) kotakCard.classList.add("active");

            // Reset form
            const form = document.getElementById("kotakLoginFormElement");
            if (form) {
                form.reset();
            }
        });
    }
});

// Initialize modal with Kotak Neo selected when page loads
document.addEventListener("DOMContentLoaded", function () {
    // Ensure Kotak Neo is selected by default
    setTimeout(() => {
        const kotakCard = document.getElementById("kotakCard");
        const welcomeScreen = document.getElementById("welcomeScreen");
        const kotakLoginForm = document.getElementById("kotakLoginForm");

        if (kotakCard) {
            kotakCard.classList.add("active");
        }

        // Ensure correct initial state
        if (welcomeScreen) welcomeScreen.style.display = "none";
        // if (kotakLoginForm) kotakLoginForm.style.display = "block";
    }, 100);
});

// Alias for backward compatibility
function redirectToKotakLogin() {
    redirectToKotakNeoLogin();
}

function redirectToKotakNeoLogin() {
    const modal = bootstrap.Modal.getInstance(
        document.getElementById("loginAccountModal"),
    );
    if (modal) {
        modal.hide();
    }

    // Redirect to the Kotak Neo project (will start it if needed)
    window.open("/kotak/login", "_blank");
}

function redirectToUpstoxLogin() {
    const modal = bootstrap.Modal.getInstance(
        document.getElementById("loginAccountModal"),
    );
    if (modal) {
        modal.hide();
    }

    alert("Upstox integration coming soon!");
}

function redirectToAngelLogin() {
    const modal = bootstrap.Modal.getInstance(
        document.getElementById("loginAccountModal"),
    );
    if (modal) {
        modal.hide();
    }

    alert("Angel One integration coming soon!");
}

function redirectToZerodhaLogin() {
    const modal = bootstrap.Modal.getInstance(
        document.getElementById("loginAccountModal"),
    );
    modal.hide();

    Swal.fire({
        icon: "info",
        title: "Coming Soon",
        text: "Zerodha integration is under development",
        background: "var(--card-bg)",
        color: "var(--text-primary)",
    });
}

// Additional utility functions for backward compatibility
function showSettingsModal() {
    const modal = new bootstrap.Modal(document.getElementById("settingsModal"));
    modal.show();
}

function toggleNotificationInbox() {
    const inbox = document.getElementById("notificationInbox");
    if (inbox) {
        inbox.style.display = inbox.style.display === "none" ? "block" : "none";
    }
}

function closeNotificationInbox() {
    const inbox = document.getElementById("notificationInbox");
    if (inbox) {
        inbox.style.display = "none";
    }
}

function toggleUserMenu() {
    const userMenu = document.getElementById("userMenu");
    if (userMenu) {
        userMenu.style.display =
            userMenu.style.display === "none" ? "block" : "none";
    }
}

function showUserProfile() {
    const modal = new bootstrap.Modal(
        document.getElementById("userProfileModal"),
    );
    modal.show();
}

function handleAccountLogin() {
    // This function is no longer needed as we use direct redirects
    // Keeping for backward compatibility
    console.log("handleAccountLogin called - using direct redirects instead");
}

function updateLoginState(isLoggedIn, broker, userId) {
    const loginButton = document.querySelector(".btn-login-account");
    const accountsHeader = document.querySelector(".accounts-header h6");

    if (isLoggedIn) {
        // Update button to show logout option
        loginButton.innerHTML =
            '<i class="fas fa-sign-out-alt me-2"></i>Logout';
        loginButton.onclick = handleAccountLogout;
        loginButton.classList.add("btn-logout");

        // Update header to show connected account
        accountsHeader.innerHTML = `<i class="fas fa-check-circle me-2"></i>Connected: ${broker.toUpperCase()}`;
        accountsHeader.style.color = "var(--success-color)";
    } else {
        // Reset to login state
        loginButton.innerHTML =
            '<i class="fas fa-sign-in-alt me-2"></i>Login Account';
        loginButton.onclick = showLoginModal;
        loginButton.classList.remove("btn-logout");

        // Reset header
        accountsHeader.innerHTML =
            '<i class="fas fa-university me-2"></i>Trading Accounts';
        accountsHeader.style.color = "var(--text-secondary)";
    }
}

function handleAccountLogout() {
    Swal.fire({
        title: "Logout Confirmation",
        text: "Are you sure you want to logout from your trading account?",
        icon: "question",
        showCancelButton: true,
        confirmButtonText: "Yes, Logout",
        cancelButtonText: "Cancel",
        background: "var(--card-bg)",
        color: "var(--text-primary)",
        confirmButtonColor: "var(--danger-color)",
        cancelButtonColor: "var(--secondary-color)",
    }).then((result) => {
        if (result.isConfirmed) {
            // Make logout request
            fetch("/api/account/logout", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
            })
                .then((response) => response.json())
                .then((data) => {
                    // Update UI regardless of response
                    updateLoginState(false);

                    Swal.fire({
                        icon: "success",
                        title: "Logged Out",
                        text: "Successfully logged out from trading account.",
                        background: "var(--card-bg)",
                        color: "var(--text-primary)",
                        timer: 2000,
                        showConfirmButton: false,
                    });
                })
                .catch((error) => {
                    console.error("Logout error:", error);
                    // Update UI even if request fails
                    updateLoginState(false);
                });
        }
    });
}
document.addEventListener("DOMContentLoaded", updateTimestamps);

function toggleSidebar() {
    const sidebar = document.querySelector(".sidebar");
    const content = document.querySelector(".content");

    if (sidebar && content) {
        sidebar.classList.toggle("collapsed");
        content.classList.toggle("expanded");
    }
}

// Ensure all functions are properly defined
if (typeof toggleSidebar !== "function") {
    window.toggleSidebar = function () {
        const sidebar = document.getElementById("sidebar");
        const overlay = document.getElementById("sidebarOverlay");
        const isOpen = sidebar && sidebar.classList.contains("show");

        if (isOpen) {
            sidebar.classList.remove("show");
            overlay && overlay.classList.remove("show");
            document.body.style.overflow = "";
        } else {
            sidebar && sidebar.classList.add("show");
            overlay && overlay.classList.add("show");
            document.body.style.overflow = "hidden";
        }
    };
}

// Kotak Neo Login Functionality
async function handleKotakLogin(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;

    // Show loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML =
        '<i class="fas fa-spinner fa-spin me-2"></i>Logging in...';

    try {
        const response = await fetch("/kotak/api/authenticate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                mobile_number: formData.get("mobile_number"),
                ucc: formData.get("ucc"),
                mpin: formData.get("mpin"),
                totp_code: formData.get("totp_code"),
            }),
        });

        const data = await response.json();

        if (data.success) {
            // Show success message
            Swal.fire({
                icon: "success",
                title: "Login Successful!",
                text: data.message,
                timer: 2000,
                showConfirmButton: false,
            });

            // Close modal
            const modal = bootstrap.Modal.getInstance(
                document.getElementById("loginModal"),
            );
            if (modal) {
                modal.hide();
            }

            // Update sidebar with account info
            updateSidebarWithAccounts();

            // Show Kotak Neo section
            showKotakNeoSection(data.account);

            // Reset form
            form.reset();
        } else {
            // Show error message
            Swal.fire({
                icon: "error",
                title: "Login Failed",
                text: data.error,
                confirmButtonText: "Try Again",
            });
        }
    } catch (error) {
        console.error("Login error:", error);
        Swal.fire({
            icon: "error",
            title: "Connection Error",
            text: "Unable to connect to the server. Please try again.",
            confirmButtonText: "OK",
        });
    } finally {
        // Reset button state
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

// Update sidebar with logged-in accounts
async function updateSidebarWithAccounts() {
    try {
        const response = await fetch("/kotak/api/status");
        const data = await response.json();

        if (data.authenticated) {
            // Show the Kotak Neo section if authenticated
            const kotakNeoSection = document.getElementById("kotakNeoSection");
            if (kotakNeoSection) {
                kotakNeoSection.style.display = "block";
            }
        } else {
            // Hide the Kotak Neo section if not authenticated
            const kotakNeoSection = document.getElementById("kotakNeoSection");
            if (kotakNeoSection) {
                kotakNeoSection.style.display = "none";
            }
        }
    } catch (error) {
        console.error("Error updating sidebar:", error);
    }
}

// Simple function to check if user is authenticated
function isKotakAuthenticated() {
    return fetch("/kotak/api/status")
        .then(response => response.json())
        .then(data => data.authenticated)
        .catch(() => false);
}

// Check authentication status and update UI accordingly
async function checkAuthStatus() {
    try {
        const response = await fetch("/kotak/api/status");
        const data = await response.json();
        
        if (data.authenticated) {
            updateSidebarWithAccounts();
        }
    } catch (error) {
        console.error("Auth check error:", error);
    }
}

// Format date for display
function formatDate(dateString) {
    if (!dateString) return "Never";

    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;

    // If less than 24 hours ago
    if (diff < 24 * 60 * 60 * 1000) {
        if (diff < 60 * 60 * 1000) {
            const minutes = Math.floor(diff / (60 * 1000));
            return `${minutes}m ago`;
        } else {
            const hours = Math.floor(diff / (60 * 60 * 1000));
            return `${hours}h ago`;
        }
    } else {
        return date.toLocaleDateString();
    }
}

// Show Kotak Neo section after successful login
function showKotakNeoSection(account) {
    const kotakNeoSection = document.getElementById("kotakNeoSection");
    const kotakUCC = document.getElementById("kotakUCC");

    if (kotakNeoSection && kotakUCC) {
        kotakNeoSection.style.display = "block";
        kotakUCC.textContent = account.ucc || "N/A";

        // Update active navigation link based on current page
        updateActiveNavLink();
    }
}

// Hide Kotak Neo section when no accounts are logged in
function hideKotakNeoSection() {
    const kotakNeoSection = document.getElementById("kotakNeoSection");

    if (kotakNeoSection) {
        kotakNeoSection.style.display = "none";
    }
}

// Update active navigation link
function updateActiveNavLink() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll(".kotak-neo-section .nav-link");

    navLinks.forEach((link) => {
        link.classList.remove("active");
        if (link.getAttribute("href") === currentPath) {
            link.classList.add("active");
        }
    });
}

// Update sidebar with logged-in accounts (modified to show/hide Kotak section)
async function updateSidebarWithAccountsEnhanced() {
    try {
        const response = await fetch("/kotak/api/status");
        const data = await response.json();

        if (data.authenticated) {
            // Show the Kotak Neo section if authenticated
            const kotakNeoSection = document.getElementById("kotakNeoSection");
            if (kotakNeoSection) {
                kotakNeoSection.style.display = "block";
            }
        } else {
            // Hide the Kotak Neo section if not authenticated
            const kotakNeoSection = document.getElementById("kotakNeoSection");
            if (kotakNeoSection) {
                kotakNeoSection.style.display = "none";
            }
        }
    } catch (error) {
        console.error("Error updating sidebar:", error);
        hideKotakNeoSection();
    }
}

// Use the enhanced function as the main one
updateSidebarWithAccounts = updateSidebarWithAccountsEnhanced;

// Initialize account display on page load
document.addEventListener("DOMContentLoaded", function () {
    // Update sidebar with accounts if user is logged in
    updateSidebarWithAccounts();

    // Update active navigation link
    updateActiveNavLink();
});
