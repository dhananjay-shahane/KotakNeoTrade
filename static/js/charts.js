/**
 * Charts Page JavaScript
 * Handles chart functionality and skeleton loading
 */

var advancedChart;

// Initialize charts when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Load LightweightCharts first, then initialize the chart
    loadLightweightCharts()
        .then(function() {
            advancedChart = new AdvancedTradingChart();

            // Hide skeleton and show content
            if (window.skeletonLoader) {
                window.skeletonLoader.hideChartsSkeleton();
            }

            console.log('Advanced Trading Chart initialized successfully');
        })
        .catch(function(error) {
            console.error('Failed to initialize Advanced Trading Chart:', error);

            // Hide skeleton even on error
            if (window.skeletonLoader) {
                window.skeletonLoader.hideChartsSkeleton();
            }

            // Show error message to user
            var chartGrid = document.getElementById('chartGrid');
            if (chartGrid) {
                chartGrid.innerHTML = `
                    <div class="d-flex justify-content-center align-items-center h-100">
                        <div class="text-center text-danger">
                            <i class="fas fa-exclamation-triangle fa-2x mb-3"></i>
                            <h5>Chart Library Error</h5>
                            <p>Failed to load the charting library. Please check your internet connection and refresh the page.</p>
                            <button class="btn btn-outline-light" onclick="location.reload()">
                                <i class="fas fa-redo me-1"></i>Refresh Page
                            </button>
                        </div>
                    </div>
                `;
            }
        });
});

// Function to check if LightweightCharts is loaded
function checkLightweightChartsLoaded() {
    return typeof LightweightCharts !== 'undefined' && 
           typeof LightweightCharts.createChart === 'function';
}

// Function to load LightweightCharts if not already loaded
function loadLightweightCharts() {
    return new Promise(function(resolve, reject) {
        if (checkLightweightChartsLoaded()) {
            resolve();
            return;
        }

        var script = document.createElement('script');
        script.src = 'https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js';
        script.onload = function() {
            if (checkLightweightChartsLoaded()) {
                resolve();
            } else {
                reject(new Error('Failed to load LightweightCharts library'));
            }
        };
        script.onerror = function() {
            reject(new Error('Failed to load LightweightCharts library'));
        };
        document.head.appendChild(script);
    });
}

// Basic chart functionality placeholder
function AdvancedTradingChart() {
    this.charts = new Map();
    this.selectedSymbols = new Set();
    this.currentPeriod = '1W';

    console.log('AdvancedTradingChart initialized');
}