// Mobile sidebar toggle
function toggleSidebar() {
    var sidebar = document.getElementById("sidebar");
    var overlay = document.getElementById("sidebarOverlay");
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

// User menu toggle
function toggleUserMenu() {
    var userMenu = document.getElementById("userMenu");
    var isVisible = userMenu.style.display !== "none";
    userMenu.style.display = isVisible ? "none" : "block";
}

// Close user menu when clicking outside
document.addEventListener("click", function (event) {
    var userProfile = document.querySelector(".user-profile");
    var userMenu = document.getElementById("userMenu");

    if (userProfile && userMenu && !userProfile.contains(event.target)) {
        userMenu.style.display = "none";
    }
});

// Show notifications
function showNotifications() {
    showToaster(
        "Live Market Updates",
        "Portfolio value updated successfully",
        "success",
    );
    setTimeout(function () {
        showToaster("Order Status", "Order execution completed", "info");
    }, 500);
    setTimeout(function () {
        showToaster(
            "Market Alert",
            "High volatility detected in selected stocks",
            "warning",
        );
    }, 1000);
}

// Theme Toggle Functionality
function initializeTheme() {
    // Get saved theme from localStorage or default to 'dark'
    var savedTheme = localStorage.getItem("theme") || "dark";

    // Apply the theme immediately before DOM content loads
    document.documentElement.setAttribute("data-theme", savedTheme);

    // Wait for DOM to be ready before setting up toggle
    function setupThemeToggle() {
        var themeToggle = document.getElementById("themeToggle");
        if (!themeToggle) {
            // Element doesn't exist on this page - skip silently
            return;
        }

        // Set toggle state based on saved theme
        themeToggle.checked = savedTheme === "light";

        // Add event listener for theme changes
        themeToggle.addEventListener("change", function () {
            var newTheme = this.checked ? "light" : "dark";
            document.documentElement.setAttribute("data-theme", newTheme);
            localStorage.setItem("theme", newTheme);

            // Show confirmation toast
            var message =
                newTheme === "light"
                    ? "Switched to light mode"
                    : "Switched to dark mode";
            if (typeof showToaster === "function") {
                showToaster("Theme Updated", message, "info");
            }

            console.log("Theme changed to:", newTheme);
        });
    }

    // If DOM is already loaded, setup immediately
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", setupThemeToggle);
    } else {
        setupThemeToggle();
    }
}

// Toaster Functionality
function showToaster(title, message, type = "info") {
    var container = document.getElementById("toasterContainer");
    if (!container) return;

    var toaster = document.createElement("div");
    toaster.className = "toaster";

    var iconMap = {
        success: "fas fa-check",
        error: "fas fa-times",
        warning: "fas fa-exclamation-triangle",
        info: "fas fa-info",
    };

    toaster.innerHTML = `
                <div class="toaster-icon ${type}">
                    <i class="${iconMap[type]}"></i>
                </div>
                <div class="toaster-content">
                    <div class="toaster-title">${title}</div>
                    <div class="toaster-message">${message}</div>
                </div>
                <button class="toaster-close" onclick="removeToaster(this.parentElement)">
                    <i class="fas fa-times"></i>
                </button>
            `;

    container.appendChild(toaster);

    // Show animation
    setTimeout(function () {
        toaster.classList.add("show");
    }, 100);

    // Auto-remove after 3 seconds
    setTimeout(function () {
        removeToaster(toaster);
    }, 3000);
}

function removeToaster(toaster) {
    if (toaster && toaster.parentElement) {
        toaster.classList.remove("show");
        setTimeout(function () {
            if (toaster.parentElement) {
                toaster.parentElement.removeChild(toaster);
            }
        }, 300);
    }
}

// Show user profile
function showUserProfile() {
    fetch("/api/user/profile")
        .then(function (response) {
            return response.json();
        })
        .then(function (data) {
            if (data.success) {
                var profile = data.data;
                var profileInfo = "Account Details:\n";
                profileInfo += "UCC: " + (profile.ucc || "N/A") + "\n";
                profileInfo +=
                    "Name: " + (profile.greeting_name || "N/A") + "\n";
                profileInfo += "User ID: " + (profile.user_id || "N/A") + "\n";
                profileInfo +=
                    "Account Type: " + (profile.account_type || "N/A") + "\n";
                profileInfo += "Branch: " + (profile.branch_code || "N/A");
                alert(profileInfo);
            }
        })
        .catch(function (error) {
            alert("Unable to load profile information");
        });
}

// Show account summary
function showAccountSummary() {
    fetch("/api/portfolio/summary")
        .then(function (response) {
            return response.json();
        })
        .then(function (data) {
            if (data.success) {
                var summary = data.data;
                var summaryInfo = `Portfolio Summary:\n`;
                summaryInfo += `Net Worth: ₹${summary.net_worth || "N/A"}\n`;
                summaryInfo += `Available Margin: ₹${summary.available_margin || "N/A"}\n`;
                summaryInfo += `Used Margin: ₹${summary.used_margin || "N/A"}\n`;
                summaryInfo += `P&L: ₹${summary.total_pnl || "N/A"}`;
                alert(summaryInfo);
            }
        })
        .catch(function (error) {
            alert("Unable to load account summary");
        });
}

// Auto-refresh data every 30 seconds (only for authenticated users)
var isAuthenticated =
    "{{ 'true' if session.authenticated else 'false' }}" === "true";
if (isAuthenticated) {
    setInterval(function () {
        if (!document.hidden) {
            var currentPage = window.location.pathname;
            if (currentPage === "/dashboard" && window.realTimeDashboard) {
                // Use AJAX refresh instead of page reload
                window.realTimeDashboard.refreshData();
            }
        }
    }, 30000);
}

// Toggle sidebar function
function toggleSidebarAlt() {
    var sidebar = document.querySelector(".sidebar");
    var overlay = document.querySelector(".sidebar-overlay");

    if (!sidebar) {
        return; // Sidebar element doesn't exist, skip
    }

    var isOpen = sidebar.classList.contains("active");

    if (isOpen) {
        sidebar.classList.remove("active");
        if (overlay) overlay.classList.remove("active");
        document.body.style.overflow = "";
    } else {
        sidebar.classList.add("active");
        if (overlay) overlay.classList.add("active");
        document.body.style.overflow = "hidden";
    }
}

// Close sidebar when clicking overlay
document.addEventListener("click", function (e) {
    if (e.target.classList.contains("sidebar-overlay")) {
        toggleSidebar();
    }
});

// Debug function to check theme toggle
function debugThemeToggle() {
    var toggle = document.getElementById("themeToggle");
    var saved = localStorage.getItem("theme");
    if (toggle) {
        console.log("Theme toggle element:", toggle);
        console.log("Saved theme:", saved);
        console.log(
            "Current theme attribute:",
            document.documentElement.getAttribute("data-theme"),
        );
    }
}

// Settings Modal Functionality
function showSettingsModal() {
    // Load current settings
    loadCurrentSettings();
    new bootstrap.Modal(document.getElementById("settingsModal")).show();
}

function loadCurrentSettings() {
    // Load font size
    var savedFontSize = localStorage.getItem("website-font-size") || "14";
    var fontSizeSelect = document.getElementById("fontSizeSelect");
    if (fontSizeSelect) {
        fontSizeSelect.value = savedFontSize;
        updateFontPreview(savedFontSize);
    }

    // Load theme
    var savedTheme = localStorage.getItem("theme") || "dark";
    var themeSelect = document.getElementById("themeSelect");
    if (themeSelect) {
        themeSelect.value = savedTheme;
    }

    // Data source removed - using Kotak Neo API only
}

function updateFontPreview(fontSize) {
    var preview = document.querySelector(".font-size-preview");
    if (preview) {
        preview.style.fontSize = fontSize + "px";
    }
}

function applySettings() {
    var fontSizeSelect = document.getElementById("fontSizeSelect");

    // Apply font size
    if (fontSizeSelect) {
        var newFontSize = fontSizeSelect.value;
        document.documentElement.style.setProperty(
            "--global-font-size",
            newFontSize + "px",
        );
        localStorage.setItem("website-font-size", newFontSize);

        if (typeof showToaster === "function") {
            showToaster(
                "Font Size Updated",
                "Font size changed to " + newFontSize + "px",
                "success",
            );
        }
    }

    // Close modal
    var modal = bootstrap.Modal.getInstance(
        document.getElementById("settingsModal"),
    );
    if (modal) {
        modal.hide();
    }
}

// Font Size Control Functionality
function initializeFontSize() {
    // Get saved font size from localStorage or default to 14px
    var savedFontSize = localStorage.getItem("website-font-size") || "14";

    // Apply the font size immediately
    document.documentElement.style.setProperty(
        "--global-font-size",
        savedFontSize + "px",
    );

    // Wait for DOM to be ready before setting up select
    function setupFontSizeControl() {
        var fontSizeSelect = document.getElementById("fontSizeSelect");
        if (!fontSizeSelect) {
            // Element doesn't exist on this page - skip silently
            return;
        }

        // Set select value based on saved font size
        fontSizeSelect.value = savedFontSize;

        // Add event listener for font size changes in settings modal
        fontSizeSelect.addEventListener("change", function () {
            updateFontPreview(this.value);
        });
    }

    // If DOM is already loaded, setup immediately
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", setupFontSizeControl);
    } else {
        setupFontSizeControl();
    }
}

// Initialize font size immediately (before DOM loads)
initializeFontSize();

// Initialize theme immediately (before DOM loads)
initializeTheme();

// Page Loader Functions
function showPageLoader(
    message = "Loading Neo Trading",
    subtitle = "Preparing your trading dashboard",
) {
    var loader = document.getElementById("pageLoader");
    var loaderText = loader.querySelector(".loader-text");
    var loaderSubtitle = loader.querySelector(".loader-subtitle");

    if (loaderText) {
        loaderText.innerHTML =
            message +
            '<div class="loading-dots"><span></span><span></span><span></span></div>';
    }
    if (loaderSubtitle) {
        loaderSubtitle.textContent = subtitle;
    }

    loader.classList.remove("hide");
    document.body.style.overflow = "hidden";
}

function hidePageLoader() {
    var loader = document.getElementById("pageLoader");
    if (loader) {
        loader.classList.add("hide");
        document.body.style.overflow = "";

        // Add fade-in effect to main content
        var mainContent = document.querySelector(".main-content");
        if (mainContent) {
            mainContent.classList.add("content-fade-in");
        }
    }
}

function updateLoaderMessage(message, subtitle = "") {
    var loader = document.getElementById("pageLoader");
    if (loader) {
        var loaderText = loader.querySelector(".loader-text");
        var loaderSubtitle = loader.querySelector(".loader-subtitle");

        if (loaderText) {
            loaderText.innerHTML =
                message +
                '<div class="loading-dots"><span></span><span></span><span></span></div>';
        }
        if (loaderSubtitle && subtitle) {
            loaderSubtitle.textContent = subtitle;
        }
    }
}

// Hide page loader when page is fully loaded
window.addEventListener("load", function () {
    setTimeout(function () {
        hidePageLoader();
    }, 800); // Small delay for smooth transition
});

// Data Source Management Functions - Removed (Using Kotak Neo API only)

// Initialize everything when DOM is ready
document.addEventListener("DOMContentLoaded", function () {
    // Debug theme setup
    setTimeout(function () {
        debugThemeToggle();
    }, 100);

    // Ensure font size control is working
    var fontSizeSelect = document.getElementById("fontSizeSelect");
    if (fontSizeSelect) {
        console.log(
            "Font size control initialized with value:",
            fontSizeSelect.value,
        );
    }

    // Highlight active navigation
    var currentPath = window.location.pathname;
    var navLinks = document.querySelectorAll(".nav-link");

    navLinks.forEach(function (link) {
        var href = link.getAttribute("href");
        if (href && currentPath === href) {
            link.classList.add("active");
        }
    });

    // Convert flash messages to toasters
    var alerts = document.querySelectorAll(".alert");
    for (var i = 0; i < alerts.length; i++) {
        var alert = alerts[i];
        if (alert && alert.textContent) {
            var message = alert.textContent.trim();
            var type =
                alert.classList && alert.classList.contains("alert-success")
                    ? "success"
                    : "error";
            if (typeof showToaster === "function") {
                showToaster("System Message", message, type);
            }
            alert.remove();
        }
    }
});

// Theme toggle functionality
document.addEventListener("DOMContentLoaded", function () {
    var themeToggle = document.getElementById("themeToggle");

    var savedTheme = localStorage.getItem("theme") || "dark";
    document.documentElement.setAttribute("data-bs-theme", savedTheme);

    if (themeToggle) {
        // Update icon based on current theme
        var icon = themeToggle.querySelector("i");
        if (icon) {
            icon.className =
                savedTheme === "dark" ? "fas fa-sun" : "fas fa-moon";
        }

        themeToggle.addEventListener("click", function () {
            var currentTheme =
                document.documentElement.getAttribute("data-bs-theme");
            var newTheme = currentTheme === "dark" ? "light" : "dark";

            document.documentElement.setAttribute("data-bs-theme", newTheme);
            localStorage.setItem("theme", newTheme);

            // Update icon
            var icon = this.querySelector("i");
            if (icon) {
                icon.className =
                    newTheme === "dark" ? "fas fa-sun" : "fas fa-moon";
            }
        });
    }
});

// User Profile Functions
function showUserProfile() {
    // Set login time if not already set
    var loginTimeElement = document.getElementById("loginTime");
    if (loginTimeElement && loginTimeElement.textContent === "N/A") {
        var now = new Date();
        loginTimeElement.textContent = now.toLocaleString();
    }

    new bootstrap.Modal(document.getElementById("userProfileModal")).show();
}

function showAccountSummary() {
    // Close user profile modal if open
    var userProfileModal = bootstrap.Modal.getInstance(
        document.getElementById("userProfileModal"),
    );
    if (userProfileModal) {
        userProfileModal.hide();
    }

    // Show account summary modal
    new bootstrap.Modal(document.getElementById("accountSummaryModal")).show();
}

// notification functionality
// Close user menu when clicking outside
document.addEventListener("click", function (event) {
    var userProfile = document.querySelector(".user-profile");
    var userMenu = document.getElementById("userMenu");
    var notificationContainer = document.querySelector(
        ".notification-container",
    );
    var notificationInbox = document.getElementById("notificationInbox");

    if (userProfile && userMenu && !userProfile.contains(event.target)) {
        userMenu.style.display = "none";
    }

    // Close notification inbox when clicking outside
    if (
        notificationContainer &&
        notificationInbox &&
        !notificationContainer.contains(event.target) &&
        notificationInbox.style.display !== "none"
    ) {
        closeNotificationInbox();
    }
});

// Notification Inbox Management

var notificationInboxData = [];
var notificationCheckInterval = null;

function toggleNotificationInbox() {
    var inbox = document.getElementById("notificationInbox");
    var isVisible = inbox.style.display !== "none";

    if (isVisible) {
        closeNotificationInbox();
    } else {
        openNotificationInbox();
    }
}

function openNotificationInbox() {
    var inbox = document.getElementById("notificationInbox");
    inbox.style.display = "block";
    loadNotifications();

    // Auto-close after 10 seconds
    setTimeout(function () {
        closeNotificationInbox();
    }, 10000);
}

function closeNotificationInbox() {
    var inbox = document.getElementById("notificationInbox");
    inbox.style.display = "none";
}

function loadNotifications() {
    fetch("/api/notifications")
        .then(function (response) {
            return response.json();
        })
        .then(function (data) {
            if (data.success) {
                notificationInboxData = data.notifications || [];
                updateNotificationBadge(data.unread_count || 0);
                renderNotifications();
            }
        })
        .catch(function (error) {
            console.error("Error loading notifications:", error);
        });
}

function renderNotifications() {
    var listElement = document.getElementById("notificationList");

    if (notificationInboxData.length === 0) {
        listElement.innerHTML = `
                    <div class="no-notifications">
                        <i class="fas fa-bell-slash"></i>
                        <p>No new notifications</p>
                    </div>
                `;
        return;
    }

    var html = "";
    for (var i = 0; i < notificationInboxData.length; i++) {
        var notification = notificationInboxData[i];
        var timeAgo = formatTimeAgo(new Date(notification.created_at));
        var unreadClass = !notification.is_read ? "unread" : "";

        html += `
                    <div class="notification-item ${unreadClass}" onclick="markNotificationAsRead(${notification.id})">
                        <div class="notification-title">${notification.title}</div>
                        <div class="notification-message">${notification.message}</div>
                        <div class="notification-time">
                            <i class="fas fa-clock"></i>
                            ${timeAgo}
                        </div>
                    </div>
                `;
    }

    listElement.innerHTML = html;
}

function updateNotificationBadge(count) {
    var badge = document.getElementById("notificationCount");
    if (badge) {
        badge.textContent = count > 0 ? count : "0";
        badge.style.display = count > 0 ? "flex" : "none";
    }
}

function markNotificationAsRead(notificationId) {
    fetch("/api/notifications/" + notificationId + "/read", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
    })
        .then(function (response) {
            return response.json();
        })
        .then(function (data) {
            if (data.success) {
                // Update local data
                for (var i = 0; i < notificationInboxData.length; i++) {
                    if (notificationInboxData[i].id === notificationId) {
                        notificationInboxData[i].is_read = true;
                        break;
                    }
                }
                renderNotifications();
                loadNotifications(); // Refresh count
            }
        })
        .catch(function (error) {
            console.error("Error marking notification as read:", error);
        });
}

function formatTimeAgo(date) {
    var now = new Date();
    var diffInMs = now - date;
    var diffInMinutes = Math.floor(diffInMs / (1000 * 60));
    var diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
    var diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

    if (diffInMinutes < 1) {
        return "Just now";
    } else if (diffInMinutes < 60) {
        return diffInMinutes + " minutes ago";
    } else if (diffInHours < 24) {
        return diffInHours + " hours ago";
    } else {
        return diffInDays + " days ago";
    }
}

function addNewNotification(title, message) {
    var newNotification = {
        id: Date.now(),
        title: title,
        message: message,
        created_at: new Date().toISOString(),
        is_read: false,
    };

    notificationInboxData.unshift(newNotification);
    updateNotificationBadge(
        notificationInboxData.filter(function (n) {
            return !n.is_read;
        }).length,
    );

    if (document.getElementById("notificationInbox").style.display !== "none") {
        renderNotifications();
    }

    // Show toaster as well
    showToaster(title, message, "info");
}

// Auto-refresh notifications every 30 seconds
function startNotificationPolling() {
    notificationCheckInterval = setInterval(function () {
        if (
            document.getElementById("notificationInbox").style.display ===
            "none"
        ) {
            loadNotifications();
        }
    }, 30000);
}

// Show notifications (legacy function for compatibility)
function showNotifications() {
    openNotificationInbox();
}
// Initialize dashboard if we're on dashboard page
if (window.location.pathname === "/dashboard") {
    initializeDashboard();
}

// Check session expiration every 5 minutes
setInterval(checkSessionExpiration, 5 * 60 * 1000);
// Auto-refresh functions
function refreshAllData() {
    console.log("🔄 Refreshing all dashboard data...");

    // Refresh positions
    if (typeof refreshPositions === "function") {
        refreshPositions();
    }

    // Refresh holdings
    if (typeof refreshHoldings === "function") {
        refreshHoldings();
    }

    // Refresh portfolio summary
    if (typeof loadPortfolioSummary === "function") {
        loadPortfolioSummary();
    }

    console.log("✅ All data refresh initiated");
}

// Session expiration check
function checkSessionExpiration() {
    fetch("/api/user_profile")
        .then((response) => {
            if (response.status === 401 || response.status === 403) {
                // Session expired
                showSessionExpiredNotification();
                setTimeout(() => {
                    window.location.href = "/login?expired=true";
                }, 3000);
            }
            return response.json();
        })
        .then((data) => {
            if (!data.success || !data.profile.authenticated) {
                showSessionExpiredNotification();
                setTimeout(() => {
                    window.location.href = "/login?expired=true";
                }, 3000);
            }
        })
        .catch((error) => {
            console.log("Session check failed:", error);
        });
}

function showSessionExpiredNotification() {
    const notification = document.createElement("div");
    notification.className =
        "alert alert-warning alert-dismissible fade show position-fixed";
    notification.style.cssText =
        "top: 20px; right: 20px; z-index: 9999; min-width: 300px;";
    notification.innerHTML = `
            <i class="fas fa-clock me-2"></i>
            <strong>Session Expired!</strong> You will be redirected to login page.
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
    document.body.appendChild(notification);
}
// CMP update functions removed - Using Kotak Neo API only

// Email Settings Modal Functions
function showSettingsModal() {
    const modal = new bootstrap.Modal(document.getElementById("settingsModal"));
    loadEmailSettings();
    modal.show();
}

// Make showSettingsModal globally available
window.showSettingsModal = showSettingsModal;

function loadEmailSettings() {
    // Load email notification settings from new dedicated API
    fetch("/api/check-email-notification-status", {
        method: "GET",
        credentials: "same-origin",
        headers: {
            Accept: "application/json",
        },
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.success && data.authenticated) {
                const status = data.status;

                // Update email notification toggle switch in settings modal
                const emailNotificationToggle =
                    document.getElementById("sendDealsInMail");
                if (emailNotificationToggle) {
                    emailNotificationToggle.checked = Boolean(
                        status.email_notification,
                    );
                    console.log(
                        "📧 Email notification toggle loaded:",
                        status.email_notification,
                    );
                }

                // Update email field
                const userEmailField = document.getElementById("userEmail");
                if (userEmailField && status.user_email) {
                    userEmailField.value = status.user_email;
                }

                // Handle other settings if they exist
                const dailyChangeToggle = document.getElementById(
                    "sendDailyChangeData",
                );
                if (dailyChangeToggle) {
                    dailyChangeToggle.checked =
                        status.send_daily_change_data || false;
                    toggleDailyEmailTimeContainer(
                        status.send_daily_change_data || false,
                    );
                }

                const dailyTimeField =
                    document.getElementById("dailyEmailTime");
                if (dailyTimeField && status.daily_email_time) {
                    dailyTimeField.value = status.daily_email_time;
                }
            } else {
                if (!data.authenticated) {
                    console.warn(
                        "🔒 User not authenticated for email settings",
                    );
                } else {
                    console.error(
                        "❌ Failed to load email settings:",
                        data.error,
                    );
                }
                // Set default values for unauthenticated users
                setDefaultEmailSettingsInModal();
            }
        })
        .catch((error) => {
            console.error("❌ Error loading email settings:", error);
            setDefaultEmailSettingsInModal();
        });
}

function setDefaultEmailSettingsInModal() {
    // Set safe defaults in the settings modal
    const emailNotificationToggle = document.getElementById("sendDealsInMail");
    if (emailNotificationToggle) {
        emailNotificationToggle.checked = false;
        console.log("📧 Set default email notification to: false");
    }

    const dailyChangeToggle = document.getElementById("sendDailyChangeData");
    if (dailyChangeToggle) {
        dailyChangeToggle.checked = false;
        toggleDailyEmailTimeContainer(false);
    }
}

function toggleDailyEmailTimeContainer(show) {
    const container = document.getElementById("dailyEmailTimeContainer");
    container.style.display = show ? "block" : "none";
}

function applySettings() {
    // Save font settings (existing functionality)
    const fontSize = document.getElementById("fontSizeSelect").value;
    localStorage.setItem("website-font-size", fontSize);
    document.documentElement.style.setProperty(
        "--global-font-size",
        fontSize + "px",
    );

    // Save email settings
    saveEmailSettings();
}

function saveEmailSettings() {
    // Save email notification setting using new dedicated API
    const emailNotificationToggle = document.getElementById("sendDealsInMail");

    if (emailNotificationToggle) {
        const isEnabled = Boolean(emailNotificationToggle.checked);

        console.log("💾 Saving email notification status:", isEnabled);

        fetch("/api/update-email-notification-status", {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                email_notification: isEnabled,
            }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    console.log(
                        "✅ Email notification status saved:",
                        data.status.email_notification,
                    );
                    showToaster(
                        "Success",
                        "Email notification setting saved",
                        "success",
                    );
                } else {
                    if (!data.authenticated) {
                        console.warn(
                            "🔒 Authentication required for saving email settings",
                        );
                        showToaster(
                            "Warning",
                            "Please login to save email settings",
                            "warning",
                        );
                    } else {
                        console.error(
                            "❌ Failed to save email settings:",
                            data.error,
                        );
                        showToaster(
                            "Error",
                            "Failed to save email settings",
                            "error",
                        );
                    }
                }
            })
            .catch((error) => {
                console.error("❌ Error saving email settings:", error);
                showToaster("Error", "Error saving email settings", "error");
            });
    }

    // Handle other settings if they exist
    const settings = {
        send_deals_in_mail: document.getElementById("sendDealsInMail")
            ? document.getElementById("sendDealsInMail").checked
            : false,
        send_daily_change_data: document.getElementById("sendDailyChangeData")
            .checked,
        daily_email_time: document.getElementById("dailyEmailTime").value,
        user_email: document.getElementById("userEmail").value.trim(),
    };

    fetch("/api/email-settings", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(settings),
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                showToaster(
                    "Success",
                    "Email settings saved successfully",
                    "success",
                );
                // Close modal
                const modal = bootstrap.Modal.getInstance(
                    document.getElementById("settingsModal"),
                );
                modal.hide();
            } else {
                showToaster(
                    "Error",
                    data.error || "Failed to save settings",
                    "error",
                );
            }
        })
        .catch((error) => {
            console.error("Error saving email settings:", error);
            showToaster("Error", "Failed to save email settings", "error");
        });
}

// Event listeners for email settings
document.addEventListener("DOMContentLoaded", function () {
    // Toggle time container when daily data switch changes
    const dailyDataSwitch = document.getElementById("sendDailyChangeData");
    if (dailyDataSwitch) {
        dailyDataSwitch.addEventListener("change", function () {
            toggleDailyEmailTimeContainer(this.checked);
        });
    }
});

window.applySettings = applySettings;

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
