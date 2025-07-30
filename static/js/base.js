// CRITICAL: Define toggleSidebar function first and expose it immediately
function toggleSidebar() {
    var sidebar = document.getElementById("sidebar");
    var overlay = document.getElementById("sidebarOverlay");

    if (!sidebar || !overlay) {
        console.error("Sidebar or overlay element not found");
        return;
    }

    var isOpen = sidebar.classList.contains("show");

    if (isOpen) {
        sidebar.classList.remove("show");
        overlay.classList.remove("show");
        document.body.style.overflow = "";
    } else {
        sidebar.classList.add("show");
        overlay.classList.add("show");
        document.body.style.overflow = "hidden";
    }
}

// Immediately expose toggleSidebar to global scope
window.toggleSidebar = toggleSidebar;

// Toaster notification system
function showToaster(title, message, type = "info", duration = 3000) {
    // Create toaster container if it doesn't exist
    let container = document.getElementById("toasterContainer");
    if (!container) {
        container = document.createElement("div");
        container.id = "toasterContainer";
        container.className = "toaster-container";
        document.body.appendChild(container);
    }

    // Create toaster element
    const toaster = document.createElement("div");
    toaster.className = "toaster";

    const iconClass =
        {
            success: "fas fa-check",
            error: "fas fa-times",
            warning: "fas fa-exclamation-triangle",
            info: "fas fa-info-circle",
        }[type] || "fas fa-info-circle";

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
    setTimeout(() => toaster.classList.add("show"), 10);

    // Auto remove
    setTimeout(() => {
        toaster.classList.remove("show");
        setTimeout(() => toaster.remove(), 300);
    }, duration);
}

// Set active navigation item based on current page
function setActiveNavigation() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    
    console.log('Setting active navigation for path:', currentPath);
    console.log('Found nav links:', navLinks.length);
    
    // Remove active class from all nav links
    navLinks.forEach(link => {
        link.classList.remove('active');
        link.parentElement.classList.remove('active');
    });
    
    let found = false;
    
    // Add active class to current page link
    navLinks.forEach((link, index) => {
        const href = link.getAttribute('href');
        console.log(`Link ${index}: href="${href}", currentPath="${currentPath}"`);
        
        if (href && currentPath === href) {
            console.log('Exact match found for:', href);
            link.classList.add('active');
            link.parentElement.classList.add('active');
            found = true;
        }
    });
    
    // Force portfolio page active if not found
    if (!found && currentPath === '/portfolio') {
        console.log('Forcing portfolio active state');
        const portfolioLinks = document.querySelectorAll('a[href*="portfolio"]');
        console.log('Found portfolio links:', portfolioLinks.length);
        
        portfolioLinks.forEach(link => {
            console.log('Portfolio link href:', link.getAttribute('href'));
            if (link.getAttribute('href').includes('portfolio')) {
                link.classList.add('active');
                link.parentElement.classList.add('active');
                console.log('Applied active class to portfolio link');
            }
        });
    }
    
    console.log('Active navigation setup complete');
}

// Missing functions that are called from the HTML
function showLoginModal() {
    const modal = new bootstrap.Modal(
        document.getElementById("loginAccountModal"),
    );
    modal.show();
}

// Handle Kotak-only logout
function logoutKotakOnly(event) {
    event.preventDefault();
    
    // Check if we're in a login flow to prevent duplicate notifications
    if (window.location.pathname.includes('/login')) {
        return;
    }
    
    // Make AJAX request to logout only from Kotak
    fetch('/logout-kotak', {
        method: 'GET',
        credentials: 'same-origin'
    })
    .then(response => {
        if (response.ok) {
            // Redirect to portfolio page after successful logout
            showToaster('Success', 'Logged out from Kotak Neo successfully', 'success');
            setTimeout(() => {
                window.location.href = '/portfolio';
            }, 1000);
        } else {
            showToaster('Error', 'Failed to logout from Kotak', 'error');
        }
    })
    .catch(error => {
        console.error('Logout error:', error);
        showToaster('Error', 'An error occurred during logout', 'error');
    });
}

// Enhanced mobile sidebar toggle with touch handling
function toggleSidebarEnhanced() {
    var sidebar = document.getElementById("sidebar");
    var overlay = document.getElementById("sidebarOverlay");

    if (!sidebar || !overlay) {
        console.error("Sidebar or overlay element not found");
        return;
    }

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
    const currentTheme =
        document.documentElement.getAttribute("data-theme") || "dark";
    const newTheme = currentTheme === "light" ? "dark" : "light";

    document.documentElement.setAttribute("data-theme", newTheme);
    localStorage.setItem("theme", newTheme);

    // Update toggle state
    const themeToggle = document.getElementById("themeToggle");
    if (themeToggle) {
        themeToggle.checked = newTheme === "light";
    }

    // Show feedback with proper capitalization
    if (typeof showToaster === "function") {
        const themeDisplayName = newTheme === 'dark' ? 'Dark' : 'Light';
        showToaster("Theme Changed", `Switched to ${themeDisplayName} mode`, "success", 2000);
    }
}

// Expose other global functions (toggleSidebar already exposed above)
if (typeof window !== 'undefined') {
    window.showSettingsModal = showSettingsModal;
    window.toggleNotificationInbox = toggleNotificationInbox;
    window.closeNotificationInbox = closeNotificationInbox;
    window.adjustFontSize = adjustFontSize;
    window.applySettings = applySettings;
    window.showKotakLoginForm = showKotakLoginForm;
    window.toggleUserProfile = toggleUserProfile;
    window.toggleUserMenu = toggleUserMenu;
    window.showUserProfile = showUserProfile;
    window.logoutKotakOnly = logoutKotakOnly;
    window.showLoginModal = showLoginModal;
    window.toggleTheme = toggleTheme;
}

// Initialize theme on page load
document.addEventListener("DOMContentLoaded", function () {
    const savedTheme = localStorage.getItem("theme") || "dark";
    document.documentElement.setAttribute("data-theme", savedTheme);

    const themeToggle = document.getElementById("themeToggle");
    if (themeToggle) {
        themeToggle.checked = savedTheme === "light";
        themeToggle.addEventListener("change", toggleTheme);
    }
    
    // Initialize font size
    const savedFontSize = localStorage.getItem('website-font-size') || '14';
    document.documentElement.style.setProperty('--global-font-size', savedFontSize + 'px');
    
    // Initialize settings modal
    initializeSettingsModal();
    
    // Initialize notification system
    initializeNotifications();
});

// Settings Modal functionality
function showSettingsModal() {
    const modal = new bootstrap.Modal(document.getElementById('settingsModal'));
    modal.show();
}

// Notification functionality
function toggleNotificationInbox() {
    const inbox = document.getElementById('notificationInbox');
    if (inbox) {
        inbox.style.display = inbox.style.display === 'none' ? 'block' : 'none';
    }
}

function closeNotificationInbox() {
    const inbox = document.getElementById('notificationInbox');
    if (inbox) {
        inbox.style.display = 'none';
    }
}

// Font size adjustment
function adjustFontSize(action) {
    const root = document.documentElement;
    const currentSize = parseInt(getComputedStyle(root).getPropertyValue('--global-font-size')) || 14;
    let newSize = currentSize;
    
    if (action === 'increase' && currentSize < 20) {
        newSize = currentSize + 1;
    } else if (action === 'decrease' && currentSize > 10) {
        newSize = currentSize - 1;
    } else if (action === 'reset') {
        newSize = 14;
    }
    
    root.style.setProperty('--global-font-size', newSize + 'px');
    localStorage.setItem('website-font-size', newSize);
    
    // Update display
    const fontSizeDisplay = document.getElementById('fontSizeDisplay');
    if (fontSizeDisplay) {
        fontSizeDisplay.textContent = newSize + 'px';
    }
    
    if (typeof showToaster === 'function') {
        showToaster('Font Size', `Font size set to ${newSize}px`, 'success');
    }
}

// User profile dropdown
function toggleUserProfile() {
    const dropdown = document.getElementById('userProfileDropdown');
    if (dropdown) {
        dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
    }
}

// Apply settings from modal
function applySettings() {
    const fontSizeSelect = document.getElementById('fontSizeSelect');
    if (fontSizeSelect) {
        const newSize = parseInt(fontSizeSelect.value);
        document.documentElement.style.setProperty('--global-font-size', newSize + 'px');
        localStorage.setItem('website-font-size', newSize);
        
        if (typeof showToaster === 'function') {
            showToaster('Settings Applied', `Font size set to ${newSize}px`, 'success');
        }
    }
    
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('settingsModal'));
    if (modal) {
        modal.hide();
    }
}

// Initialize font size in settings modal
function initializeSettingsModal() {
    const savedFontSize = localStorage.getItem('website-font-size') || '14';
    const fontSizeSelect = document.getElementById('fontSizeSelect');
    if (fontSizeSelect) {
        fontSizeSelect.value = savedFontSize;
        
        // Add event listener for live preview
        fontSizeSelect.addEventListener('change', function() {
            const preview = document.querySelector('.font-size-preview');
            if (preview) {
                preview.style.fontSize = this.value + 'px';
            }
        });
    }
}

// Broker selection functions
function showKotakLoginForm() {
    // Highlight selected broker
    document.querySelectorAll('.broker-card-mobile').forEach(card => {
        card.classList.remove('active');
    });
    document.getElementById('kotakCard')?.classList.add('active');
    
    // Show Kotak login form
    const loginForm = document.getElementById('kotakLoginForm');
    if (loginForm) {
        loginForm.style.display = 'block';
    }
}

// Initialize notifications
function initializeNotifications() {
    // Set initial notification count
    const notificationCount = document.getElementById('notificationCount');
    if (notificationCount) {
        notificationCount.textContent = '0';
    }
    
    // Close notification inbox when clicking outside
    document.addEventListener('click', function(event) {
        const inbox = document.getElementById('notificationInbox');
        const notificationBtn = document.querySelector('.notification-btn');
        
        if (inbox && notificationBtn && 
            !inbox.contains(event.target) && 
            !notificationBtn.contains(event.target) &&
            inbox.style.display === 'block') {
            closeNotificationInbox();
        }
    });
}

// User menu toggle function
function toggleUserMenu() {
    const userMenu = document.getElementById('userMenu');
    if (userMenu) {
        userMenu.style.display = userMenu.style.display === 'none' ? 'block' : 'none';
    }
}

// Show user profile modal
function showUserProfile() {
    const modal = new bootstrap.Modal(document.getElementById('userProfileModal'));
    modal.show();
}

// Show login modal
function showLoginModal() {
    const modal = new bootstrap.Modal(document.getElementById('loginAccountModal'));
    modal.show();
}

// Functions are already exposed above before DOMContentLoaded

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

// Debug function for sidebar toggle
function debugSidebarToggle() {
    console.log("Debugging sidebar toggle...");
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebarOverlay");
    const toggle = document.querySelector(".mobile-toggle");

    console.log("Sidebar element:", sidebar);
    console.log("Overlay element:", overlay);
    console.log("Toggle button:", toggle);

    if (sidebar) {
        console.log("Sidebar classes:", sidebar.className);
        console.log("Sidebar transform:", getComputedStyle(sidebar).transform);
    }
}

// Make debug function available globally
window.debugSidebarToggle = debugSidebarToggle;

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
function updateFontSize() {
    const fontSize = document.getElementById("fontSizeSlider").value;
    document.documentElement.style.setProperty(
        "--global-font-size",
        fontSize + "px",
    );

    // Update all elements with font size
    const elements = document.querySelectorAll(
        "body, .card, .table, .form-control, .form-select, .nav-link, .dropdown-item, .modal-body, .card-body, .card-header, .alert, p, span, div",
    );
    elements.forEach((el) => {
        el.style.fontSize = fontSize + "px";
    });

    // Update preview
    const preview = document.querySelector(".font-size-preview");
    if (preview) {
        preview.style.fontSize = fontSize + "px";
    }

    // Store in localStorage
    localStorage.setItem("globalFontSize", fontSize);
}

// Load saved font size on page load
document.addEventListener("DOMContentLoaded", function () {
    const savedFontSize = localStorage.getItem("globalFontSize") || "14";
    document.documentElement.style.setProperty(
        "--global-font-size",
        savedFontSize + "px",
    );

    // Apply to all elements immediately
    const elements = document.querySelectorAll(
        "body, .card, .table, .form-control, .form-select, .nav-link, .dropdown-item, .modal-body, .card-body, .card-header, .alert, p, span, div",
    );
    elements.forEach((el) => {
        el.style.fontSize = savedFontSize + "px";
    });

    const slider = document.getElementById("fontSizeSlider");
    if (slider) {
        slider.value = savedFontSize;
    }
});

// Settings modal functionality
function applySettings() {
    const fontSizeSelect = document.getElementById("fontSizeSelect");

    if (fontSizeSelect) {
        const newFontSize = fontSizeSelect.value;
        document.documentElement.style.setProperty(
            "--global-font-size",
            newFontSize + "px",
        );
        localStorage.setItem("website-font-size", newFontSize);
    }

    // Close modal
    const modal = bootstrap.Modal.getInstance(
        document.getElementById("settingsModal"),
    );
    if (modal) {
        modal.hide();
    }

    // Show success message
    if (typeof showToaster === "function") {
        showToaster(
            "Settings Applied",
            "Your preferences have been saved",
            "success",
        );
    }
}

// Settings modal functionality
function applySettings() {
    const fontSizeSelect = document.getElementById("fontSizeSelect");

    if (fontSizeSelect) {
        const newFontSize = fontSizeSelect.value;
        document.documentElement.style.setProperty(
            "--global-font-size",
            newFontSize + "px",
        );
        localStorage.setItem("website-font-size", newFontSize);
    }

    // Close modal
    const modal = bootstrap.Modal.getInstance(
        document.getElementById("settingsModal"),
    );
    if (modal) {
        modal.hide();
    }

    // Show success message
    if (typeof showToaster === "function") {
        showToaster(
            "Settings Applied",
            "Your preferences have been saved",
            "success",
        );
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

// Navigation active state - enhanced version
document.addEventListener("DOMContentLoaded", function () {
    console.log('DOM loaded, setting up navigation...');
    // Small delay to ensure DOM is fully rendered
    setTimeout(() => {
        setActiveNavigation();
    }, 100);
});

// Also call on page visibility change
document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
        setTimeout(() => {
            setActiveNavigation();
        }, 100);
    }
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

// Show forget password modal
function showForgetPasswordModal() {
    var modal = new bootstrap.Modal(document.getElementById('forgetPasswordModal'));
    modal.show();
}

// Toggle password visibility - handles both input ID and button element
function togglePasswordVisibility(inputIdOrButton) {
    var input, toggleButton, icon;
    
    // Check if it's a string (inputId) or button element
    if (typeof inputIdOrButton === 'string') {
        // Handle input ID
        input = document.getElementById(inputIdOrButton);
        if (!input) {
            console.error('Password input not found:', inputIdOrButton);
            return;
        }
        
        var wrapper = input.parentElement;
        toggleButton = wrapper.querySelector('.password-toggle');
        icon = toggleButton ? toggleButton.querySelector('i') : null;
    } else if (inputIdOrButton && inputIdOrButton.nodeType === Node.ELEMENT_NODE) {
        // Handle button element
        toggleButton = inputIdOrButton;
        icon = toggleButton.querySelector('i');
        
        // Find the input field - it should be the previous sibling or in the same wrapper
        input = toggleButton.previousElementSibling;
        
        if (!input || input.tagName !== 'INPUT') {
            // Try to find input in parent wrapper
            var wrapper = toggleButton.parentElement;
            input = wrapper.querySelector('input[type="password"], input[type="text"]');
        }
        
        if (!input || input.tagName !== 'INPUT') {
            // Try to find input as sibling in wrapper
            var parentWrapper = toggleButton.parentElement;
            var inputs = parentWrapper.querySelectorAll('input[type="password"], input[type="text"]');
            if (inputs.length > 0) {
                input = inputs[0];
            }
        }
    } else {
        console.error('Invalid parameter for togglePasswordVisibility:', inputIdOrButton);
        return;
    }
    
    if (!input) {
        console.error('Password input not found for toggle button');
        return;
    }
    
    if (!icon) {
        console.error('Icon not found in toggle button');
        return;
    }
    
    // Toggle password visibility
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// Submit password reset with enhanced validation
function submitPasswordReset() {
    var oldPassword = document.getElementById('oldPassword').value;
    var newPassword = document.getElementById('newPassword').value;
    var confirmPassword = document.getElementById('confirmPassword').value;
    var submitBtn = document.getElementById('resetPasswordBtn');
    
    // Get username from session or modal display
    var usernameElement = document.querySelector('#forgetPasswordModal .bg-secondary');
    var currentUsername = usernameElement ? usernameElement.textContent.trim() : '';
    
    // Validation
    if (!oldPassword || !newPassword || !confirmPassword) {
        Swal.fire({
            icon: 'error',
            title: 'Validation Error',
            text: 'Please fill in all password fields.',
            background: 'var(--card-bg)',
            color: 'var(--text-primary)'
        });
        return;
    }
    
    if (newPassword !== confirmPassword) {
        Swal.fire({
            icon: 'error',
            title: 'Password Mismatch',
            text: 'New password and confirm password do not match.',
            background: 'var(--card-bg)',
            color: 'var(--text-primary)'
        });
        return;
    }
    
    if (newPassword.length < 6) {
        Swal.fire({
            icon: 'error',
            title: 'Invalid Password',
            text: 'Password must be at least 6 characters long.',
            background: 'var(--card-bg)',
            color: 'var(--text-primary)'
        });
        return;
    }
    
    // Check for common weak passwords
    var weakPasswords = ['123456', 'password', '123456789', 'qwerty', 'abc123'];
    if (weakPasswords.includes(newPassword.toLowerCase())) {
        Swal.fire({
            icon: 'error',
            title: 'Weak Password',
            text: 'Please choose a stronger password.',
            background: 'var(--card-bg)',
            color: 'var(--text-primary)'
        });
        return;
    }
    
    // Show loading state
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Updating...';
    }
    
    // Send password reset request
    fetch('/api/reset-password', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin',
        body: JSON.stringify({
            oldPassword: oldPassword,
            newPassword: newPassword,
            confirmPassword: confirmPassword,
            username: currentUsername
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            Swal.fire({
                icon: 'success',
                title: 'Password Updated',
                text: 'Your password has been successfully updated.',
                timer: 2000,
                showConfirmButton: false,
                background: 'var(--card-bg)',
                color: 'var(--text-primary)'
            });
            
            // Close modal and reset form
            const modal = bootstrap.Modal.getInstance(document.getElementById('forgetPasswordModal'));
            if (modal) {
                modal.hide();
            }
            const form = document.getElementById('forgetPasswordForm');
            if (form) {
                form.reset();
            }
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Update Failed',
                text: data.message || 'Failed to update password. Please try again.',
                background: 'var(--card-bg)',
                color: 'var(--text-primary)'
            });
        }
    })
    .catch(error => {
        console.error('Error:', error);
        let errorMessage = 'Failed to connect to server. Please try again.';
        if (error.message.includes('404')) {
            errorMessage = 'Password reset service not available. Please contact support.';
        }
        Swal.fire({
            icon: 'error',
            title: 'Network Error',
            text: errorMessage,
            background: 'var(--card-bg)',
            color: 'var(--text-primary)'
        });
    })
    .finally(() => {
        // Reset button state
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-save me-1"></i>Update Password';
        }
    });
}

// Password visibility toggle function (alternative implementation)
function togglePassword(fieldIdOrButton) {
    // Handle both fieldId string and button element
    if (typeof fieldIdOrButton === 'string') {
        const passwordField = document.getElementById(fieldIdOrButton);
        const eyeIcon = document.getElementById(fieldIdOrButton + "-eye");

        if (passwordField && eyeIcon) {
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
    } else if (fieldIdOrButton && fieldIdOrButton.nodeType) {
        // Handle button element directly
        togglePasswordVisibility(fieldIdOrButton);
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
    fetch("/kotak/api/authenticate", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(loginData),
    })
        .then((response) => response.json())
        .then((data) => {
            // Reset button
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;

            if (data.success) {
                // Close modal and redirect to Kotak dashboard
                const modal = bootstrap.Modal.getInstance(
                    document.getElementById("loginAccountModal"),
                );
                if (modal) {
                    modal.hide();
                }

                // Show success message
                Swal.fire({
                    icon: "success",
                    title: "Login Successful",
                    text: "Successfully logged in to Kotak Neo!",
                    background: "var(--card-bg)",
                    color: "var(--text-primary)",
                    timer: 2000,
                    showConfirmButton: false,
                });

                // Redirect to Kotak dashboard
                setTimeout(() => {
                    window.location.href = "/kotak/dashboard";
                }, 2000);
            } else {
                // Show error message
                Swal.fire({
                    icon: "error",
                    title: "Login Failed",
                    text:
                        data.error ||
                        "Authentication failed. Please check your credentials.",
                    background: "var(--card-bg)",
                    color: "var(--text-primary)",
                });
            }
        })
        .catch((error) => {
            console.error("Error:", error);
            // Reset button
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;

            // Show error message
            Swal.fire({
                icon: "error",
                title: "Connection Error",
                text: "Unable to connect to authentication service. Please try again.",
                background: "var(--card-bg)",
                color: "var(--text-primary)",
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

// Ensure toggleSidebar is available globally
window.toggleSidebar = toggleSidebar;

// Kotak Neo Login Functionality

// Update sidebar with logged-in accounts

// Simple function to check if user is authenticated
function isKotakAuthenticated() {
    return fetch("/kotak/api/status")
        .then((response) => response.json())
        .then((data) => data.authenticated)
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

// Show Kotak account box with account data
function showKotakAccountBox(accountData) {
    const kotakAccountBox = document.getElementById("kotakAccountBox");
    const accountLogin = document.getElementById("accountLogin");
    const addAccountSection = document.getElementById("addAccountSection");

    if (kotakAccountBox && accountLogin) {
        // Hide login button and show account box
        accountLogin.style.display = "none";
        kotakAccountBox.style.display = "block";

        // Show add account section
        if (addAccountSection) {
            addAccountSection.style.display = "block";
        }

        // Populate account data
        const kotakUCCDisplay = document.getElementById("kotakUCCDisplay");
        const kotakMobileDisplay =
            document.getElementById("kotakMobileDisplay");
        const kotakLastLogin = document.getElementById("kotakLastLogin");

        if (kotakUCCDisplay && accountData.ucc) {
            kotakUCCDisplay.textContent = accountData.ucc;
        }

        if (kotakMobileDisplay && accountData.mobile) {
            kotakMobileDisplay.textContent = accountData.mobile;
        }

        if (kotakLastLogin) {
            kotakLastLogin.textContent = formatLoginTime();
        }
    }
}

// Hide Kotak account box
function hideKotakAccountBox() {
    const kotakAccountBox = document.getElementById("kotakAccountBox");
    const accountLogin = document.getElementById("accountLogin");
    const addAccountSection = document.getElementById("addAccountSection");

    if (kotakAccountBox && accountLogin) {
        // Show login button and hide account box
        kotakAccountBox.style.display = "none";
        accountLogin.style.display = "block";

        // Hide add account section
        if (addAccountSection) {
            addAccountSection.style.display = "none";
        }
    }
}

// Switch to Kotak dashboard
function switchToKotakDashboard() {
    window.location.href = "/kotak/dashboard";
}

// Format login time for display
function formatLoginTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
    });
    return timeString;
}

function updateSidebar(accountData) {
    console.log('Updating sidebar with data:', accountData);

    if (!accountData) {
        console.log('No account data provided');
        return;
    }

    try {
        // Update Kotak account section visibility
        const kotakSection = document.querySelector('.kotak-account-section');
        if (kotakSection) {
            kotakSection.style.display = accountData ? 'block' : 'none';
        }

        // Update account info elements if they exist
        const ucc = document.getElementById('sidebar-ucc');
        const mobile = document.getElementById('sidebar-mobile'); 
        const greeting = document.getElementById('sidebar-greeting');
        const status = document.getElementById('sidebar-status');

        if (ucc && accountData.ucc) ucc.textContent = accountData.ucc;
        if (mobile && accountData.mobile) mobile.textContent = accountData.mobile;
        if (greeting && accountData.greeting_name) greeting.textContent = accountData.greeting_name;
        if (status && accountData.status) status.textContent = accountData.status;

        console.log('Sidebar updated successfully');
    } catch (error) {
        console.error('Error updating sidebar:', error);
    }
}

// Enhanced function for account updates
function updateSidebarWithAccountsEnhanced(accountData) {
    try {
        updateSidebar(accountData);
    } catch (error) {
        console.error('Error updating sidebar:', error);
    }
}

// Use the enhanced function as the main one
window.updateSidebarWithAccounts = updateSidebarWithAccountsEnhanced;

// Fallback updateSidebar function if not already defined
if (typeof updateSidebar !== 'function') {
    function updateSidebar(accountData) {
        console.log('updateSidebar called with:', accountData);
        // Basic sidebar update logic
        if (accountData && typeof accountData === 'object') {
            // Update sidebar elements if they exist
            const kotakSection = document.getElementById('kotakNeoSection');
            const kotakAccountBox = document.getElementById('kotakAccountBox');

            if (kotakSection && accountData.ucc) {
                kotakSection.style.display = 'block';
            }

            if (kotakAccountBox && accountData.greeting_name) {
                kotakAccountBox.style.display = 'block';
            }
        }
    }
}

// Initialize account display on page load
document.addEventListener("DOMContentLoaded", function () {
    // Update sidebar with accounts if user is logged in
    updateSidebarWithAccounts();

    // Update active navigation link
    updateActiveNavLink();
});