// Page Loader Functionality
class PageLoader {
    constructor() {
        this.loader = null;
        this.loadingMessages = [
            'Loading trading dashboard...',
            'Fetching market data...',
            'Updating portfolio...',
            'Connecting to servers...',
            'Preparing your account...'
        ];
        this.currentMessageIndex = 0;
        this.messageInterval = null;
        this.init();
    }

    init() {
        // Create loader HTML structure
        this.createLoader();
        
        // Show loader on page load
        this.show();
        
        // Hide loader when page is fully loaded
        this.setupLoadingComplete();
    }

    createLoader() {
        const loaderHTML = `
            <div id="pageLoader" class="page-loader trading-loader">
                <div class="loader-content">
                    <div class="trading-icon-loader">
                        <i class="fas fa-chart-line"></i>
                    </div>
                    <div class="loader-spinner"></div>
                    <div class="loader-text" id="loaderText">Loading Kotak Neo Trading...</div>
                    <div class="loader-subtext" id="loaderSubtext">Please wait while we prepare your dashboard</div>
                    <div class="loader-progress">
                        <div class="loader-progress-bar"></div>
                    </div>
                </div>
            </div>
        `;
        
        // Insert loader at the beginning of body
        document.body.insertAdjacentHTML('afterbegin', loaderHTML);
        this.loader = document.getElementById('pageLoader');
    }

    show() {
        if (this.loader) {
            this.loader.style.display = 'flex';
            this.loader.classList.remove('fade-out');
            this.startMessageRotation();
        }
    }

    hide() {
        if (this.loader) {
            this.loader.classList.add('fade-out');
            this.stopMessageRotation();
            
            // Remove loader from DOM after animation
            setTimeout(() => {
                if (this.loader && this.loader.parentNode) {
                    this.loader.parentNode.removeChild(this.loader);
                }
                
                // Show content with animation
                this.showContent();
            }, 500);
        }
    }

    startMessageRotation() {
        const loaderText = document.getElementById('loaderText');
        const loaderSubtext = document.getElementById('loaderSubtext');
        
        if (loaderText && loaderSubtext) {
            this.messageInterval = setInterval(() => {
                this.currentMessageIndex = (this.currentMessageIndex + 1) % this.loadingMessages.length;
                loaderSubtext.textContent = this.loadingMessages[this.currentMessageIndex];
            }, 1500);
        }
    }

    stopMessageRotation() {
        if (this.messageInterval) {
            clearInterval(this.messageInterval);
            this.messageInterval = null;
        }
    }

    showContent() {
        const contentWrapper = document.querySelector('.content-wrapper, main, .container-fluid');
        if (contentWrapper) {
            contentWrapper.classList.add('loaded');
        }
    }

    setupLoadingComplete() {
        // Wait for DOM content and additional resources
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.waitForResources();
            });
        } else {
            this.waitForResources();
        }
    }

    waitForResources() {
        // Wait for images, stylesheets, and other resources
        window.addEventListener('load', () => {
            // Add a small delay to ensure smooth transition
            setTimeout(() => {
                this.hide();
            }, 800);
        });

        // Fallback: hide loader after maximum wait time
        setTimeout(() => {
            this.hide();
        }, 5000);
    }
}

// AJAX Loader for dynamic content
class AjaxLoader {
    static show(targetElement = null) {
        const loader = `
            <div class="ajax-loader text-center p-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div class="mt-2 text-muted">
                    <small>Updating data...</small>
                </div>
            </div>
        `;
        
        if (targetElement) {
            targetElement.innerHTML = loader;
        }
        
        return loader;
    }

    static hide(targetElement = null) {
        if (targetElement) {
            const ajaxLoader = targetElement.querySelector('.ajax-loader');
            if (ajaxLoader) {
                ajaxLoader.remove();
            }
        }
    }
}

// Auto-initialize page loader
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if not already present
    if (!document.getElementById('pageLoader')) {
        new PageLoader();
    }
});

// Export for global use
window.PageLoader = PageLoader;
window.AjaxLoader = AjaxLoader;