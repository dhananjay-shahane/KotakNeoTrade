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

// Theme toggle functionality
document.addEventListener("DOMContentLoaded", function () {
    const themeToggle = document.getElementById("themeToggle");
    const currentTheme = localStorage.getItem("theme") || "dark";

    // Set initial theme
    document.documentElement.setAttribute("data-theme", currentTheme);
    themeToggle.checked = currentTheme === "light";

    themeToggle.addEventListener("change", function () {
        const newTheme = this.checked ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", newTheme);
        localStorage.setItem("theme", newTheme);
    });
});

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
    const fontSizeSelect = document.getElementById("fontSizeSelect");
    const preview = document.querySelector(".font-size-preview");

    // Load saved font size
    const savedFontSize = localStorage.getItem("website-font-size") || "14";
    fontSizeSelect.value = savedFontSize;
    document.documentElement.style.setProperty(
        "--global-font-size",
        savedFontSize + "px",
    );

    // Update preview
    if (preview) {
        preview.style.fontSize = savedFontSize + "px";
    }

    fontSizeSelect.addEventListener("change", function () {
        const fontSize = this.value;
        document.documentElement.style.setProperty(
            "--global-font-size",
            fontSize + "px",
        );
        localStorage.setItem("website-font-size", fontSize);

        // Update preview
        if (preview) {
            preview.style.fontSize = fontSize + "px";
        }
    });
});

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
    const eyeIcon = document.getElementById(fieldId + '-eye');
    
    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        eyeIcon.classList.remove('fa-eye');
        eyeIcon.classList.add('fa-eye-slash');
    } else {
        passwordField.type = 'password';
        eyeIcon.classList.remove('fa-eye-slash');
        eyeIcon.classList.add('fa-eye');
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

// Alias for backward compatibility
function redirectToKotakLogin() {
    redirectToKotakNeoLogin();
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

// Missing functions that are called from the HTML
function showLoginModal() {
    const modal = new bootstrap.Modal(
        document.getElementById("loginAccountModal"),
    );
    modal.show();
}

function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebarOverlay");

    if (sidebar && overlay) {
        sidebar.classList.toggle("show");
        overlay.classList.toggle("show");
    }
}

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
