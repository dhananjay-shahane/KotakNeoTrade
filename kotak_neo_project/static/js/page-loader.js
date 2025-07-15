
// Page Loader Utility Functions
(function() {
    'use strict';

    window.PageLoader = {
        // Show loader with custom message
        show: function(message, subtitle) {
            message = message || 'Loading';
            subtitle = subtitle || 'Please wait';
            
            var loader = document.getElementById('pageLoader');
            if (!loader) return;

            var loaderText = loader.querySelector('.loader-text');
            var loaderSubtitle = loader.querySelector('.loader-subtitle');
            
            if (loaderText) {
                loaderText.innerHTML = message + '<div class="loading-dots"><span></span><span></span><span></span></div>';
            }
            if (loaderSubtitle) {
                loaderSubtitle.textContent = subtitle;
            }
            
            loader.classList.remove('hide');
            document.body.style.overflow = 'hidden';
        },

        // Hide loader
        hide: function() {
            var loader = document.getElementById('pageLoader');
            if (!loader) return;

            loader.classList.add('hide');
            document.body.style.overflow = '';
            
            // Add fade-in effect to main content
            var mainContent = document.querySelector('.main-content');
            if (mainContent) {
                mainContent.classList.add('content-fade-in');
            }
        },

        // Update loader message without hiding
        update: function(message, subtitle) {
            var loader = document.getElementById('pageLoader');
            if (!loader) return;

            var loaderText = loader.querySelector('.loader-text');
            var loaderSubtitle = loader.querySelector('.loader-subtitle');
            
            if (loaderText && message) {
                loaderText.innerHTML = message + '<div class="loading-dots"><span></span><span></span><span></span></div>';
            }
            if (loaderSubtitle && subtitle) {
                loaderSubtitle.textContent = subtitle;
            }
        },

        // Show for specific duration
        showFor: function(duration, message, subtitle) {
            this.show(message, subtitle);
            setTimeout(() => {
                this.hide();
            }, duration);
        },

        // Show during API calls
        showForApiCall: function(apiCall, loadingMessage, successMessage) {
            loadingMessage = loadingMessage || 'Processing request';
            successMessage = successMessage || 'Request completed';
            
            this.show(loadingMessage, 'Please wait...');
            
            return apiCall.then(function(result) {
                PageLoader.update(successMessage, 'Success!');
                setTimeout(function() {
                    PageLoader.hide();
                }, 1000);
                return result;
            }).catch(function(error) {
                PageLoader.update('Request failed', 'Please try again');
                setTimeout(function() {
                    PageLoader.hide();
                }, 2000);
                throw error;
            });
        }
    };

    // Auto-hide loader when page is fully loaded
    window.addEventListener('load', function() {
        setTimeout(function() {
            if (window.PageLoader) {
                window.PageLoader.hide();
            }
        }, 1000);
    });

    // Show loader immediately if page is still loading
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            if (window.PageLoader) {
                window.PageLoader.show();
            }
        });
    }

})();
