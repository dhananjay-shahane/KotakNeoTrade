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

        // User menu toggle
        function toggleUserMenu() {
            var userMenu = document.getElementById('userMenu');
            var isVisible = userMenu.style.display !== 'none';
            userMenu.style.display = isVisible ? 'none' : 'block';
        }

        // Close user menu when clicking outside
        document.addEventListener('click', function(event) {
            var userProfile = document.querySelector('.user-profile');
            var userMenu = document.getElementById('userMenu');

            if (userProfile && userMenu && !userProfile.contains(event.target)) {
                userMenu.style.display = 'none';
            }
        });

        // Show notifications
        function showNotifications() {
            showToaster('Live Market Updates', 'Portfolio value updated successfully', 'success');
            setTimeout(function() { showToaster('Order Status', 'Order execution completed', 'info'); }, 500);
            setTimeout(function() { showToaster('Market Alert', 'High volatility detected in selected stocks', 'warning'); }, 1000);
        }

        // Theme Toggle Functionality
        function initializeTheme() {
            // Get saved theme from localStorage or default to 'dark'
            var savedTheme = localStorage.getItem('theme') || 'dark';

            // Apply the theme immediately before DOM content loads
            document.documentElement.setAttribute('data-theme', savedTheme);

            // Wait for DOM to be ready before setting up toggle
            function setupThemeToggle() {
                var themeToggle = document.getElementById('themeToggle');
                if (!themeToggle) {
                    // Element doesn't exist on this page - skip silently
                    return;
                }

                // Set toggle state based on saved theme
                themeToggle.checked = savedTheme === 'light';

                // Add event listener for theme changes
                themeToggle.addEventListener('change', function() {
                    var newTheme = this.checked ? 'light' : 'dark';
                    document.documentElement.setAttribute('data-theme', newTheme);
                    localStorage.setItem('theme', newTheme);

                    // Show confirmation toast
                    var message = newTheme === 'light' ? 'Switched to light mode' : 'Switched to dark mode';
                    if (typeof showToaster === 'function') {
                        showToaster('Theme Updated', message, 'info');
                    }

                    console.log('Theme changed to:', newTheme);
                });
            }

            // If DOM is already loaded, setup immediately
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', setupThemeToggle);
            } else {
                setupThemeToggle();
            }
        }

        // Toaster Functionality
        function showToaster(title, message, type = 'info') {
            var container = document.getElementById('toasterContainer');
            if (!container) return;

            var toaster = document.createElement('div');
            toaster.className = 'toaster';

            var iconMap = {
                success: 'fas fa-check',
                error: 'fas fa-times',
                warning: 'fas fa-exclamation-triangle',
                info: 'fas fa-info'
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
            setTimeout(function() {
                toaster.classList.add('show');
            }, 100);

            // Auto-remove after 3 seconds
            setTimeout(function() {
                removeToaster(toaster);
            }, 3000);
        }

        function removeToaster(toaster) {
            if (toaster && toaster.parentElement) {
                toaster.classList.remove('show');
                setTimeout(function() {
                    if (toaster.parentElement) {
                        toaster.parentElement.removeChild(toaster);
                    }
                }, 300);
            }
        }

        // Show user profile
        function showUserProfile() {
            fetch('/api/user/profile')
                .then(function(response) { return response.json(); })
                .then(function(data) {
                    if (data.success) {
                        var profile = data.data;
                                        var profileInfo = 'Account Details:\n';
                        profileInfo += 'UCC: ' + (profile.ucc || 'N/A') + '\n';
                        profileInfo += 'Name: ' + (profile.greeting_name || 'N/A') + '\n';
                        profileInfo += 'User ID: ' + (profile.user_id || 'N/A') + '\n';
                        profileInfo += 'Account Type: ' + (profile.account_type || 'N/A') + '\n';
                        profileInfo += 'Branch: ' + (profile.branch_code || 'N/A');
                        alert(profileInfo);
                    }
                })
                .catch(function(error) {
                    alert('Unable to load profile information');
                });
        }

        // Show account summary
        function showAccountSummary() {
            fetch('/api/portfolio/summary')
                .then(function(response) { return response.json(); })
                .then(function(data) {
                    if (data.success) {
                        var summary = data.data;
                        var summaryInfo = `Portfolio Summary:\n`;
                        summaryInfo += `Net Worth: ₹${summary.net_worth || 'N/A'}\n`;
                        summaryInfo += `Available Margin: ₹${summary.available_margin || 'N/A'}\n`;
                        summaryInfo += `Used Margin: ₹${summary.used_margin || 'N/A'}\n`;
                        summaryInfo += `P&L: ₹${summary.total_pnl || 'N/A'}`;
                        alert(summaryInfo);
                    }
                })
                .catch(function(error) {
                    alert('Unable to load account summary');
                });
        }

        // Auto-refresh data every 30 seconds (only for authenticated users)
           var isAuthenticated = "{{ 'true' if session.authenticated else 'false' }}" === "true";
        if (isAuthenticated) {
            setInterval(function() {
                if (!document.hidden) {
                    var currentPage = window.location.pathname;
                    if (currentPage === '/dashboard' && window.realTimeDashboard) {
                        // Use AJAX refresh instead of page reload
                        window.realTimeDashboard.refreshData();
                    }
                }
            }, 30000);
        }

        // Toggle sidebar function
        function toggleSidebarAlt() {
            var sidebar = document.querySelector('.sidebar');
            var overlay = document.querySelector('.sidebar-overlay');

            if (!sidebar) {
                return; // Sidebar element doesn't exist, skip
            }

            var isOpen = sidebar.classList.contains('active');

            if (isOpen) {
                sidebar.classList.remove('active');
                if (overlay) overlay.classList.remove('active');
                document.body.style.overflow = '';
            } else {
                sidebar.classList.add('active');
                if (overlay) overlay.classList.add('active');
                document.body.style.overflow = 'hidden';
            }
        }

        // Close sidebar when clicking overlay
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('sidebar-overlay')) {
                toggleSidebar();
            }
        });

        // Debug function to check theme toggle
        function debugThemeToggle() {
            var toggle = document.getElementById('themeToggle');
            var saved = localStorage.getItem('theme');
            if (toggle) {
                console.log('Theme toggle element:', toggle);
                console.log('Saved theme:', saved);
                console.log('Current theme attribute:', document.documentElement.getAttribute('data-theme'));
            }
        }

        // Initialize theme immediately (before DOM loads)
        initializeTheme();

        // Initialize everything when DOM is ready
        document.addEventListener('DOMContentLoaded', function() {
            // Debug theme setup
            setTimeout(function() {
                debugThemeToggle();
            }, 100);

            // Highlight active navigation
            var currentPath = window.location.pathname;
            var navLinks = document.querySelectorAll('.nav-link');

            navLinks.forEach(function(link) {
                var href = link.getAttribute('href');
                if (href && currentPath === href) {
                    link.classList.add('active');
                }
            });

            // Convert flash messages to toasters
            var alerts = document.querySelectorAll('.alert');
            for (var i = 0; i < alerts.length; i++) {
                var alert = alerts[i];
                if (alert && alert.textContent) {
                    var message = alert.textContent.trim();
                    var type = alert.classList && alert.classList.contains('alert-success') ? 'success' : 'error';
                    if (typeof showToaster === 'function') {
                        showToaster('System Message', message, type);
                    }
                    alert.remove();
                }
            }
        });

        // Theme toggle functionality
        document.addEventListener('DOMContentLoaded', function() {
            var themeToggle = document.getElementById('themeToggle');

            var savedTheme = localStorage.getItem('theme') || 'dark';
            document.documentElement.setAttribute('data-bs-theme', savedTheme);

            if (themeToggle) {
                // Update icon based on current theme
                var icon = themeToggle.querySelector('i');
                if (icon) {
                    icon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
                }

                themeToggle.addEventListener('click', function() {
                    var currentTheme = document.documentElement.getAttribute('data-bs-theme');
                    var newTheme = currentTheme === 'dark' ? 'light' : 'dark';

                    document.documentElement.setAttribute('data-bs-theme', newTheme);
                    localStorage.setItem('theme', newTheme);

                    // Update icon
                    var icon = this.querySelector('i');
                    if (icon) {
                        icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
                    }
                });
            }
        });

        // User Profile Functions
        function showUserProfile() {
            // Set login time if not already set
            var loginTimeElement = document.getElementById('loginTime');
            if (loginTimeElement && loginTimeElement.textContent === 'N/A') {
                var now = new Date();
                loginTimeElement.textContent = now.toLocaleString();
            }

            new bootstrap.Modal(document.getElementById('userProfileModal')).show();
        }

        function showAccountSummary() {
            // Close user profile modal if open
            var userProfileModal = bootstrap.Modal.getInstance(document.getElementById('userProfileModal'));
            if (userProfileModal) {
                userProfileModal.hide();
            }

            // Show account summary modal
            new bootstrap.Modal(document.getElementById('accountSummaryModal')).show();
        }