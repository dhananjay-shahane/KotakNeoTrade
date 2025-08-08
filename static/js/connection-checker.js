/**
 * Internet Connection Checker
 * Monitors internet connectivity and shows offline/online status
 */

class ConnectionChecker {
    constructor() {
        this.isOnline = navigator.onLine;
        this.offlineMessage = null;
        this.retryInterval = null;
        this.checkInterval = 30000; // Check every 30 seconds
        this.retryDelay = 5000; // Retry every 5 seconds when offline
        
        this.init();
    }

    init() {
        // Create offline message UI
        this.createOfflineUI();
        
        // Listen for online/offline events
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.handleOffline());
        
        // Start periodic connection checks
        this.startPeriodicCheck();
        
        // Initial check
        this.checkConnection();
        
        console.log('🌐 Connection checker initialized');
    }

    createOfflineUI() {
        this.offlineMessage = document.createElement('div');
        this.offlineMessage.id = 'offline-message';
        this.offlineMessage.className = 'connection-status offline';
        this.offlineMessage.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(45deg, #dc3545, #c82333);
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(220, 53, 69, 0.4);
            z-index: 10000;
            font-family: 'Inter', sans-serif;
            font-weight: 500;
            display: none;
            min-width: 300px;
            animation: slideInRight 0.3s ease-out;
        `;
        
        this.offlineMessage.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-wifi" style="font-size: 18px; color: #ffcccc;"></i>
                <div>
                    <div style="font-weight: 600; margin-bottom: 2px;">No Internet Connection</div>
                    <div style="font-size: 12px; opacity: 0.9;">Please check your internet connection</div>
                </div>
                <button id="retry-connection" style="
                    background: rgba(255, 255, 255, 0.2);
                    border: none;
                    color: white;
                    padding: 5px 10px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                    margin-left: auto;
                ">Retry</button>
            </div>
        `;
        
        document.body.appendChild(this.offlineMessage);
        
        // Add retry button functionality
        document.getElementById('retry-connection').addEventListener('click', () => {
            this.checkConnection();
        });
        
        // Add CSS animations
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideInRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOutRight {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
            .connection-status.hiding {
                animation: slideOutRight 0.3s ease-in forwards;
            }
        `;
        document.head.appendChild(style);
    }

    async checkConnection() {
        try {
            // Try to fetch a small resource to test connectivity
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
            
            const response = await fetch('/api/health-check', {
                method: 'HEAD',
                cache: 'no-cache',
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (response.ok) {
                this.handleOnline();
                return true;
            } else {
                this.handleOffline();
                return false;
            }
        } catch (error) {
            console.warn('Connection check failed:', error.message);
            this.handleOffline();
            return false;
        }
    }

    handleOnline() {
        if (!this.isOnline) {
            this.isOnline = true;
            console.log('🌐 Connection restored');
            
            // Hide offline message
            this.hideOfflineMessage();
            
            // Clear retry interval
            if (this.retryInterval) {
                clearInterval(this.retryInterval);
                this.retryInterval = null;
            }
            
            // Show brief online notification
            this.showOnlineMessage();
            
            // Trigger custom event for other components
            window.dispatchEvent(new CustomEvent('connectionrestored'));
        }
    }

    handleOffline() {
        if (this.isOnline) {
            this.isOnline = false;
            console.warn('🌐 Connection lost');
            
            // Show offline message
            this.showOfflineMessage();
            
            // Start retry attempts
            this.startRetryAttempts();
            
            // Trigger custom event for other components
            window.dispatchEvent(new CustomEvent('connectionlost'));
        }
    }

    showOfflineMessage() {
        if (this.offlineMessage) {
            this.offlineMessage.style.display = 'block';
            this.offlineMessage.classList.remove('hiding');
        }
    }

    hideOfflineMessage() {
        if (this.offlineMessage && this.offlineMessage.style.display !== 'none') {
            this.offlineMessage.classList.add('hiding');
            setTimeout(() => {
                this.offlineMessage.style.display = 'none';
                this.offlineMessage.classList.remove('hiding');
            }, 300);
        }
    }

    showOnlineMessage() {
        const onlineMessage = document.createElement('div');
        onlineMessage.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(40, 167, 69, 0.4);
            z-index: 10001;
            font-family: 'Inter', sans-serif;
            font-weight: 500;
            animation: slideInRight 0.3s ease-out;
        `;
        
        onlineMessage.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-wifi" style="font-size: 16px; color: #d4edda;"></i>
                <span>Connection restored</span>
            </div>
        `;
        
        document.body.appendChild(onlineMessage);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            onlineMessage.classList.add('hiding');
            setTimeout(() => {
                if (onlineMessage.parentNode) {
                    onlineMessage.parentNode.removeChild(onlineMessage);
                }
            }, 300);
        }, 3000);
    }

    startRetryAttempts() {
        if (this.retryInterval) {
            clearInterval(this.retryInterval);
        }
        
        this.retryInterval = setInterval(() => {
            if (!this.isOnline) {
                this.checkConnection();
            }
        }, this.retryDelay);
    }

    startPeriodicCheck() {
        // Periodic background check
        setInterval(() => {
            this.checkConnection();
        }, this.checkInterval);
    }

    // Public method to manually check connection
    async testConnection() {
        return await this.checkConnection();
    }

    // Get current connection status
    getStatus() {
        return {
            isOnline: this.isOnline,
            lastCheck: new Date()
        };
    }
}

// Initialize connection checker when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.connectionChecker = new ConnectionChecker();
    
    // Add global event listeners for connection status changes
    window.addEventListener('connectionlost', function() {
        console.warn('📡 Application is now offline');
        // You can add specific offline behavior here
    });
    
    window.addEventListener('connectionrestored', function() {
        console.log('📡 Application is back online');
        // You can add specific online behavior here
        // Maybe refresh data or resume operations
    });
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ConnectionChecker;
}