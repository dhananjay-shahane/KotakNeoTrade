// Mobile sidebar toggle
function toggleSidebar() {
    var sidebar = document.getElementById('sidebar');
    var overlay = document.getElementById('sidebarOverlay');
    var isOpen = sidebar.classList.contains('show');

    if (isOpen) {
        sidebar.classList.remove('show');
        overlay.classList.remove('show');
        document.body.style.overflow = '';
    } else {
        sidebar.classList.add('show');
        overlay.classList.add('show');
        document.body.style.overflow = 'hidden';
    }
}

// Close sidebar when clicking outside on mobile
document.addEventListener('click', function(event) {
    var sidebar = document.getElementById('sidebar');
    var toggle = document.querySelector('.mobile-toggle');
    var overlay = document.getElementById('sidebarOverlay');

    if (window.innerWidth <= 992 && 
        sidebar && sidebar.classList.contains('show') && 
        !sidebar.contains(event.target) && 
        !toggle.contains(event.target)) {
        toggleSidebar();
    }
});

// Handle window resize
window.addEventListener('resize', function() {
    var sidebar = document.getElementById('sidebar');
    var overlay = document.getElementById('sidebarOverlay');

    if (window.innerWidth > 992) {
        sidebar.classList.remove('show');
        overlay.classList.remove('show');
        document.body.style.overflow = '';
    }
});

// Theme toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('themeToggle');
    const currentTheme = localStorage.getItem('theme') || 'dark';
    
    // Set initial theme
    document.documentElement.setAttribute('data-theme', currentTheme);
    themeToggle.checked = currentTheme === 'light';
    
    themeToggle.addEventListener('change', function() {
        const newTheme = this.checked ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });
});

// User menu toggle
function toggleUserMenu() {
    const userMenu = document.getElementById('userMenu');
    const isVisible = userMenu.style.display !== 'none';
    
    if (isVisible) {
        userMenu.style.display = 'none';
    } else {
        userMenu.style.display = 'block';
    }
}

// Close user menu when clicking outside
document.addEventListener('click', function(event) {
    const userMenu = document.getElementById('userMenu');
    const userProfile = document.querySelector('.user-profile');
    
    if (userMenu && userProfile && 
        !userProfile.contains(event.target) && 
        !userMenu.contains(event.target)) {
        userMenu.style.display = 'none';
    }
});

// Show user profile modal
function showUserProfile() {
    const userMenu = document.getElementById('userMenu');
    userMenu.style.display = 'none';
    
    const modal = new bootstrap.Modal(document.getElementById('userProfileModal'));
    modal.show();
}

// Show settings modal
function showSettingsModal() {
    const modal = new bootstrap.Modal(document.getElementById('settingsModal'));
    modal.show();
}

// Font size functionality
document.addEventListener('DOMContentLoaded', function() {
    const fontSizeSelect = document.getElementById('fontSizeSelect');
    const preview = document.querySelector('.font-size-preview');
    
    // Load saved font size
    const savedFontSize = localStorage.getItem('website-font-size') || '14';
    fontSizeSelect.value = savedFontSize;
    document.documentElement.style.setProperty('--global-font-size', savedFontSize + 'px');
    
    // Update preview
    if (preview) {
        preview.style.fontSize = savedFontSize + 'px';
    }
    
    fontSizeSelect.addEventListener('change', function() {
        const fontSize = this.value;
        document.documentElement.style.setProperty('--global-font-size', fontSize + 'px');
        localStorage.setItem('website-font-size', fontSize);
        
        // Update preview
        if (preview) {
            preview.style.fontSize = fontSize + 'px';
        }
    });
});

// Notification functionality
function toggleNotificationInbox() {
    const inbox = document.getElementById('notificationInbox');
    const isVisible = inbox.style.display !== 'none';
    
    if (isVisible) {
        inbox.style.display = 'none';
    } else {
        inbox.style.display = 'block';
    }
}

function closeNotificationInbox() {
    const inbox = document.getElementById('notificationInbox');
    inbox.style.display = 'none';
}

// Close notification inbox when clicking outside
document.addEventListener('click', function(event) {
    const inbox = document.getElementById('notificationInbox');
    const notificationContainer = document.querySelector('.notification-container');
    
    if (inbox && notificationContainer && 
        !notificationContainer.contains(event.target)) {
        inbox.style.display = 'none';
    }
});

// Navigation active state
document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('.nav-link');
    const currentPath = window.location.pathname;
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && (href === currentPath || currentPath.includes(href))) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
});

// Smooth transitions for theme changes
document.addEventListener('DOMContentLoaded', function() {
    // Add transition styles for smooth theme switching
    const style = document.createElement('style');
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
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Page loader utility (if needed)
function showPageLoader() {
    const loader = document.createElement('div');
    loader.id = 'pageLoader';
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
    const loader = document.getElementById('pageLoader');
    if (loader) {
        loader.remove();
    }
}

// Utility function for AJAX requests with proper error handling
function makeRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    return fetch(url, finalOptions)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error('Request failed:', error);
            throw error;
        });
}

// Auto-update timestamp functionality (for login time, etc.)
function updateTimestamps() {
    const timestampElements = document.querySelectorAll('[data-timestamp]');
    timestampElements.forEach(element => {
        const timestamp = element.getAttribute('data-timestamp');
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
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes} minute${diffInMinutes > 1 ? 's' : ''} ago`;
    if (diffInHours < 24) return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`;
    if (diffInDays < 7) return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString();
}

// Run timestamp updates every minute
setInterval(updateTimestamps, 60000);

// Run initial timestamp update
document.addEventListener('DOMContentLoaded', updateTimestamps);