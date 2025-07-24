/**
 * Skeleton Loader Management System
 * Handles loading states for all pages with shimmer animations
 */

class SkeletonLoader {
    constructor() {
        this.isLoading = false;
        this.loadingTimeout = null;
    }

    // Show skeleton loading for specific page
    showSkeleton(pageType) {
        const skeletonId = `${pageType}Skeleton`;
        const contentId = pageType === 'charts' ? 'chartsMainContent' : pageType === 'deals' ? 'dealsMainContent' : `${pageType}Content`;
        
        const skeletonElement = document.getElementById(skeletonId);
        const contentElement = document.getElementById(contentId);
        
        // Ensure parent container has relative positioning for absolute children
        const parentContainer = skeletonElement?.parentElement;
        if (parentContainer) {
            parentContainer.style.position = 'relative';
            
            // Set appropriate min-height based on page type
            switch(pageType) {
                case 'charts':
                    parentContainer.style.minHeight = '600px';
                    break;
                case 'deals':
                    parentContainer.style.minHeight = '600px';
                    break;
                case 'signals':
                    parentContainer.style.minHeight = '500px';
                    break;
                case 'portfolio':
                    parentContainer.style.minHeight = '600px';
                    break;
                default:
                    parentContainer.style.minHeight = '400px';
            }
        }
        
        if (skeletonElement) {
            skeletonElement.classList.remove('skeleton-hidden');
            skeletonElement.classList.add('skeleton-loading');
        }
        
        if (contentElement) {
            contentElement.classList.remove('content-loaded');
            contentElement.classList.add('content-loading');
        }
        
        this.isLoading = true;
        console.log(`🔄 Skeleton loading started for ${pageType}`);
    }

    // Hide skeleton loading and show content
    hideSkeleton(pageType, delay = 500) {
        // Add delay to show the skeleton animation briefly
        setTimeout(() => {
            const skeletonId = `${pageType}Skeleton`;
            const contentId = pageType === 'charts' ? 'chartsMainContent' : pageType === 'deals' ? 'dealsMainContent' : `${pageType}Content`;
            
            const skeletonElement = document.getElementById(skeletonId);
            const contentElement = document.getElementById(contentId);
            
            if (skeletonElement) {
                skeletonElement.classList.remove('skeleton-loading');
                skeletonElement.classList.add('skeleton-hidden');
            }
            
            if (contentElement) {
                contentElement.classList.remove('content-loading');
                contentElement.classList.add('content-loaded');
            }
            
            this.isLoading = false;
            console.log(`✅ Skeleton loading completed for ${pageType}`);
        }, delay);
    }

    // Portfolio page skeleton management
    showPortfolioSkeleton() {
        this.showSkeleton('portfolio');
    }

    hidePortfolioSkeleton() {
        this.hideSkeleton('portfolio');
    }

    // Trading signals page skeleton management
    showSignalsSkeleton() {
        this.showSkeleton('signals');
    }

    hideSignalsSkeleton() {
        this.hideSkeleton('signals');
    }

    // Deals page skeleton management
    showDealsSkeleton() {
        this.showSkeleton('deals');
    }

    hideDealsSkeleton() {
        this.hideSkeleton('deals');
    }

    // Charts page skeleton management
    showChartsSkeleton() {
        this.showSkeleton('charts');
    }

    hideChartsSkeleton() {
        this.hideSkeleton('charts');
    }

    // Auto-hide skeleton after timeout (fallback)
    autoHideSkeleton(pageType, timeout = 5000) {
        this.loadingTimeout = setTimeout(() => {
            if (this.isLoading) {
                console.warn(`⚠️ Auto-hiding skeleton for ${pageType} after timeout`);
                this.hideSkeleton(pageType, 0);
            }
        }, timeout);
    }

    // Clear timeout
    clearAutoHide() {
        if (this.loadingTimeout) {
            clearTimeout(this.loadingTimeout);
            this.loadingTimeout = null;
        }
    }

    // Get current loading state
    getLoadingState() {
        return this.isLoading;
    }

    // Initialize skeleton based on current page
    initializeForPage() {
        const currentPath = window.location.pathname;
        
        // Determine page type and show appropriate skeleton
        if (currentPath.includes('/portfolio')) {
            this.showPortfolioSkeleton();
            this.autoHideSkeleton('portfolio');
        } else if (currentPath.includes('/trading-signals')) {
            this.showSignalsSkeleton();
            this.autoHideSkeleton('signals');
        } else if (currentPath.includes('/deals')) {
            this.showDealsSkeleton();
            this.autoHideSkeleton('deals');
        } else if (currentPath.includes('/charts')) {
            this.showChartsSkeleton();
            this.autoHideSkeleton('charts');
        }
    }

    // Manual control functions for API calls
    showLoadingForAPI(pageType) {
        this.clearAutoHide();
        this.showSkeleton(pageType);
    }

    hideLoadingForAPI(pageType) {
        this.clearAutoHide();
        this.hideSkeleton(pageType, 200); // Shorter delay for API responses
    }
}

// Create global instance
window.skeletonLoader = new SkeletonLoader();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize skeleton loader for current page
    window.skeletonLoader.initializeForPage();
    
    // Add event listeners for navigation
    const navLinks = document.querySelectorAll('.nav-link[href]');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href && !href.startsWith('#') && !href.startsWith('javascript:')) {
                // Determine target page and show skeleton
                if (href.includes('/portfolio')) {
                    window.skeletonLoader.showPortfolioSkeleton();
                } else if (href.includes('/trading-signals')) {
                    window.skeletonLoader.showSignalsSkeleton();
                } else if (href.includes('/deals')) {
                    window.skeletonLoader.showDealsSkeleton();
                } else if (href.includes('/charts')) {
                    window.skeletonLoader.showChartsSkeleton();
                }
            }
        });
    });
    
    console.log('🎨 Skeleton loader system initialized');
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SkeletonLoader;
}