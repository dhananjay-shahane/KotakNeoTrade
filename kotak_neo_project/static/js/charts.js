function AdvancedTradingChart() {
    this.charts = new Map(); // Store chart instances
    this.selectedSymbols = new Set(); // Track selected symbols
    this.currentPeriod = '1W';
    this.searchTimeout = null;
    this.currentSearchResults = [];

    this.initializeEventListeners();
}

AdvancedTradingChart.prototype.initializeEventListeners = function() {
    var self = this;
    
    // Symbol search
    var searchInput = document.getElementById('symbolSearch');
    searchInput.addEventListener('input', function(e) {
        clearTimeout(self.searchTimeout);
        self.searchTimeout = setTimeout(function() {
            self.searchSymbols(e.target.value);
        }, 300);
    });

    // Hide search results when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.search-container')) {
            document.getElementById('searchResults').classList.remove('show');
        }
    });

    // Timeframe buttons
    document.querySelectorAll('.timeframe-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.timeframe-btn').forEach(function(b) { 
                b.classList.remove('active'); 
            });
            btn.classList.add('active');
            self.currentPeriod = btn.dataset.period;
            self.refreshAllCharts();
        });
    });

    // Clear all button
    document.getElementById('clearAllBtn').addEventListener('click', function() {
        self.clearAllCharts();
    });

    // Connect button
    document.getElementById('connectBtn').addEventListener('click', function() {
        self.connectWebSocket();
    });
};

AdvancedTradingChart.prototype.searchSymbols = async function(query) {
    if (!query || query.length < 2) {
        document.getElementById('searchResults').classList.remove('show');
        return;
    }

    try {
        var response = await fetch(`/api/search-symbols?q=${encodeURIComponent(query)}`);
        var symbols = await response.json();
        this.currentSearchResults = symbols;
        this.displaySearchResults(symbols);
    } catch (error) {
        console.error('Error searching symbols:', error);
    }
};

AdvancedTradingChart.prototype.displaySearchResults = function(symbols) {
    var resultsContainer = document.getElementById('searchResults');

    if (symbols.length === 0) {
        resultsContainer.classList.remove('show');
        return;
    }

    var self = this;
    resultsContainer.innerHTML = symbols.map(function(symbol) { 
        return '<div class="search-result-item" data-symbol="' + symbol.symbol + '" data-name="' + symbol.name + '">' +
            '<input type="checkbox" class="search-result-checkbox" ' + 
                   (self.selectedSymbols.has(symbol.symbol) ? 'checked' : '') + '>' +
            '<div class="search-result-info">' +
                '<div class="search-result-symbol">' + symbol.symbol + '</div>' +
                '<div class="search-result-name">' + symbol.name + '</div>' +
            '</div>' +
        '</div>';
    }).join('');

    // Add event listeners to search results
    resultsContainer.querySelectorAll('.search-result-item').forEach(function(item) {
        var checkbox = item.querySelector('.search-result-checkbox');

        item.addEventListener('click', function(e) {
            if (e.target !== checkbox) {
                checkbox.checked = !checkbox.checked;
            }
            self.toggleSymbol(item.dataset.symbol, item.dataset.name);
        });

        checkbox.addEventListener('change', function() {
            self.toggleSymbol(item.dataset.symbol, item.dataset.name);
        });
    });

    resultsContainer.classList.add('show');
};

AdvancedTradingChart.prototype.toggleSymbol = function(symbol, name) {
    if (this.selectedSymbols.has(symbol)) {
        this.removeSymbol(symbol);
    } else {
        this.addSymbol(symbol, name);
    }
    this.updateSelectedSymbolsDisplay();
    this.updateChartGrid();
};

AdvancedTradingChart.prototype.addSymbol = function(symbol, name) {
    // Clear any existing charts first to maintain single chart display
    this.clearAllCharts();
    this.selectedSymbols.add(symbol);
    this.loadChartData(symbol, name);
};

AdvancedTradingChart.prototype.removeSymbol = function(symbol) {
    this.selectedSymbols.delete(symbol);
    if (this.charts.has(symbol)) {
        var chartInfo = this.charts.get(symbol);
        chartInfo.chart.remove();
        
        // Clean up resize handler
        if (chartInfo.resizeHandler) {
            window.removeEventListener('resize', chartInfo.resizeHandler);
        }
        
        this.charts.delete(symbol);
    }
    
    // Remove chart container from DOM
    var chartContainer = document.getElementById(`chart-${symbol}`);
    if (chartContainer) {
        chartContainer.remove();
    }
    
    this.updateSelectedSymbolsDisplay();
    this.updateChartGrid();
};

AdvancedTradingChart.prototype.retryLoadChart = function(symbol, name) {
    console.log(`Retrying chart load for ${symbol}`);
    this.removeSymbol(symbol);
    this.addSymbol(symbol, name);
};

AdvancedTradingChart.prototype.updateSelectedSymbolsDisplay = function() {
    var container = document.getElementById('selectedSymbols');
    container.innerHTML = Array.from(this.selectedSymbols).map(function(symbol) { 
        return '<div class="selected-symbol-tag">' +
            '<span>' + symbol + '</span>' +
            '<button class="remove-symbol" onclick="advancedChart.removeSymbol(\'' + symbol + '\')">×</button>' +
        '</div>';
    }).join('');
};

AdvancedTradingChart.prototype.updateChartGrid = function() {
    var chartGrid = document.getElementById('chartGrid');
    var noChartsMessage = document.getElementById('noChartsMessage');
    var symbolCount = this.selectedSymbols.size;

    if (symbolCount === 0) {
        chartGrid.style.display = 'none';
        noChartsMessage.style.display = 'block';
        return;
    }

    noChartsMessage.style.display = 'none';
    chartGrid.style.display = 'grid';
    chartGrid.className = 'chart-grid';
};

AdvancedTradingChart.prototype.loadChartData = async function(symbol, name) {
    var chartContainer = this.createChartContainer(symbol, name);
    var chartContent = chartContainer.querySelector('.chart-content');

    try {
        // Show loading state
        chartContent.innerHTML = `
            <div class="d-flex justify-content-center align-items-center h-100">
                <div class="text-center">
                    <div class="spinner-border text-primary" role="status"></div>
                    <p class="mt-2 text-muted">Loading ${symbol} chart...</p>
                </div>
            </div>
        `;

        // Ensure LightweightCharts is loaded
        if (!checkLightweightChartsLoaded()) {
            throw new Error('LightweightCharts library is not loaded. Please refresh the page.');
        }

        var url = `/api/chart-data?symbol=${encodeURIComponent(symbol)}&period=${this.currentPeriod}`;
        console.log('Fetching chart data from:', url);
        
        var response = await fetch(url);
        var data = await response.json();

        console.log('Chart data response:', data);

        if (data.error) {
            throw new Error(data.error);
        }

        if (!data.candlesticks || data.candlesticks.length === 0) {
            throw new Error('No chart data available');
        }

        // Clear loading content
        chartContent.innerHTML = '';

        // Wait for container to be visible
        await new Promise(function(resolve) { setTimeout(resolve, 100); });

        var containerWidth = chartContent.clientWidth || 800;
        var containerHeight = chartContent.clientHeight || 400;

        console.log('Chart container dimensions:', containerWidth, 'x', containerHeight);

        // Check if LightweightCharts is available
        if (typeof LightweightCharts === 'undefined') {
            throw new Error('LightweightCharts library is not loaded. Please include the library script.');
        }

        // Create chart with explicit dimensions
        var chart = LightweightCharts.createChart(chartContent, {
            width: containerWidth,
            height: containerHeight,
            layout: {
                backgroundColor: '#1e293b',
                textColor: '#f8fafc',
            },
            grid: {
                vertLines: { color: '#334155' },
                horzLines: { color: '#334155' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: '#334155',
            },
            timeScale: {
                borderColor: '#334155',
                timeVisible: true,
                secondsVisible: false,
            },
        });

        // Verify chart was created successfully
        if (!chart || typeof chart.addCandlestickSeries !== 'function') {
            throw new Error('Failed to create chart instance. Chart library may not be properly loaded.');
        }

        // Add candlestick series
        var candlestickSeries = chart.addCandlestickSeries({
            upColor: '#16a34a',
            downColor: '#dc2626',
            borderDownColor: '#dc2626',
            borderUpColor: '#16a34a',
            wickDownColor: '#dc2626',
            wickUpColor: '#16a34a',
        });

        // Add volume series
        var volumeSeries = chart.addHistogramSeries({
            color: '#475569',
            priceFormat: { type: 'volume' },
            priceScaleId: '',
            scaleMargins: { top: 0.8, bottom: 0 },
        });

        console.log('Setting candlestick data:', data.candlesticks.length, 'points');
        console.log('Setting volume data:', data.volume.length, 'points');

        // Set data
        candlestickSeries.setData(data.candlesticks);
        volumeSeries.setData(data.volume);

        // Store chart instance
        this.charts.set(symbol, {
            chart: chart,
            candlestickSeries: candlestickSeries,
            volumeSeries: volumeSeries,
            container: chartContainer
        });

        // Update price info
        this.updatePriceInfo(symbol, data);

        // Update data source indicator
        this.updateDataSourceIndicator(symbol, data.real_data_available || false);

        console.log(`Chart created successfully for ${symbol}`);

        // Handle resize
        var self = this;
        var resizeHandler = function() {
            var newWidth = chartContent.clientWidth;
            var newHeight = chartContent.clientHeight;
            if (newWidth > 0 && newHeight > 0) {
                chart.applyOptions({
                    width: newWidth,
                    height: newHeight,
                });
            }
        };

        window.addEventListener('resize', resizeHandler);
        
        // Store resize handler for cleanup
        this.charts.get(symbol).resizeHandler = resizeHandler;

    } catch (error) {
        console.error(`Error loading chart data for ${symbol}:`, error);
        var errorMessage = error.message;
        
        // Provide more specific error messages
        if (errorMessage.includes('LightweightCharts')) {
            errorMessage = 'Chart library not loaded. Please refresh the page.';
        } else if (errorMessage.includes('addCandlestickSeries')) {
            errorMessage = 'Chart initialization failed. Please refresh the page.';
        }
        
        chartContent.innerHTML = `
            <div class="d-flex justify-content-center align-items-center h-100">
                <div class="text-center text-danger">
                    <i class="fas fa-exclamation-triangle fa-2x mb-3"></i>
                    <h6>Error Loading Chart</h6>
                    <p class="mb-2">${errorMessage}</p>
                    <div>
                        <button class="btn btn-outline-light btn-sm me-2" onclick="advancedChart.retryLoadChart('${symbol}', '${name}')">
                            <i class="fas fa-redo me-1"></i>Retry
                        </button>
                        <button class="btn btn-outline-light btn-sm" onclick="location.reload()">
                            <i class="fas fa-refresh me-1"></i>Refresh Page
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
};

AdvancedTradingChart.prototype.createChartContainer = function(symbol, name) {
    var chartGrid = document.getElementById('chartGrid');
    var chartContainer = document.createElement('div');
    chartContainer.className = 'chart-container';
    chartContainer.id = `chart-${symbol}`;

    chartContainer.innerHTML = `
        <div class="chart-header">
            <div>
                <div class="chart-title">${symbol}</div>
                <div class="price-info">
                    <span class="price-value" id="price-${symbol}">--</span>
                    <span class="price-change" id="change-${symbol}">--</span>
                </div>
            </div>
            <button class="remove-chart" onclick="advancedChart.removeSymbol('${symbol}')">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="chart-content" style="height: calc(100% - 80px);"></div>
    `;

    chartGrid.appendChild(chartContainer);
    return chartContainer;
};

AdvancedTradingChart.prototype.updatePriceInfo = function(symbol, data) {
    if (data.candlesticks && data.candlesticks.length > 0) {
        var lastCandle = data.candlesticks[data.candlesticks.length - 1];
        var firstCandle = data.candlesticks[0];
        var change = lastCandle.close - firstCandle.open;
        var changePercent = ((change / firstCandle.open) * 100).toFixed(2);

        var priceElement = document.getElementById(`price-${symbol}`);
        var changeElement = document.getElementById(`change-${symbol}`);

        if (priceElement && changeElement) {
            priceElement.textContent = `₹${lastCandle.close.toFixed(2)}`;
            changeElement.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)} (${changePercent}%)`;
            changeElement.className = `price-change ${change >= 0 ? 'positive' : 'negative'}`;
        }
    }
};

AdvancedTradingChart.prototype.refreshChart = function(symbol) {
    var self = this;
    var url = `/api/chart-data?symbol=${symbol}&period=${this.currentPeriod}`;

    fetch(url)
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.error) {
                console.error('Error loading chart data:', data.error);
                self.showChartError(symbol, data.error);
                return;
            }

            self.updateChart(symbol, data);

            // Update data source indicator
            self.updateDataSourceIndicator(symbol, data.real_data_available || false);

            // Log data source for debugging
            console.log(`Chart for ${symbol}: ${data.data_source} data (Real: ${data.real_data_available})`);
        })
        .catch(function(error) {
            console.error('Error loading chart data:', error);
            self.showChartError(symbol, 'Failed to load chart data');
        });
};

AdvancedTradingChart.prototype.updateChart = function(symbol, data) {
    var chartInfo = this.charts.get(symbol);
    if (!chartInfo) return;

    try {
        // Update chart data
        chartInfo.candlestickSeries.setData(data.candlesticks);
        chartInfo.volumeSeries.setData(data.volume);

        // Update price info
        this.updatePriceInfo(symbol, data);

        console.log(`Chart updated successfully for ${symbol}`);
    } catch (error) {
        console.error(`Error updating chart for ${symbol}:`, error);
    }
};

AdvancedTradingChart.prototype.showChartError = function(symbol, message) {
    var chartContainer = document.getElementById(`chart-${symbol}`);
    if (chartContainer) {
        var chartContent = chartContainer.querySelector('.chart-content');
        if (chartContent) {
            chartContent.innerHTML = `
                <div class="d-flex justify-content-center align-items-center h-100">
                    <div class="text-center text-danger">
                        <i class="fas fa-exclamation-triangle fa-2x mb-3"></i>
                        <h6>Chart Error</h6>
                        <p class="mb-2">${message}</p>
                        <button class="btn btn-outline-light btn-sm" onclick="advancedChart.refreshChart('${symbol}')">
                            <i class="fas fa-redo me-1"></i>Retry
                        </button>
                    </div>
                </div>
            `;
        }
    }
};

AdvancedTradingChart.prototype.updateDataSourceIndicator = function(symbol, isRealData) {
    var chartContainer = document.getElementById(`chart-${symbol}`);
    if (chartContainer) {
        var indicator = chartContainer.querySelector('.data-source-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'data-source-indicator';
            indicator.style.cssText = `
                position: absolute;
                top: 10px;
                right: 10px;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 500;
                z-index: 1000;
            `;
            chartContainer.style.position = 'relative';
            chartContainer.appendChild(indicator);
        }

        if (isRealData) {
            indicator.textContent = '🟢 LIVE DATA';
            indicator.style.backgroundColor = 'rgba(34, 197, 94, 0.1)';
            indicator.style.color = '#22c55e';
            indicator.style.border = '1px solid rgba(34, 197, 94, 0.3)';
        } else {
            indicator.textContent = '🟡 SIMULATED';
            indicator.style.backgroundColor = 'rgba(234, 179, 8, 0.1)';
            indicator.style.color = '#eab308';
            indicator.style.border = '1px solid rgba(234, 179, 8, 0.3)';
        }
    }
};

AdvancedTradingChart.prototype.refreshAllCharts = function() {
    var self = this;
    this.selectedSymbols.forEach(function(symbol) {
        self.refreshChart(symbol);
    });
};

AdvancedTradingChart.prototype.clearAllCharts = function() {
    this.charts.forEach(function(chartInfo, symbol) {
        chartInfo.chart.remove();
    });
    this.charts.clear();
    this.selectedSymbols.clear();
    document.getElementById('chartGrid').innerHTML = '';
    this.updateSelectedSymbolsDisplay();
    this.updateChartGrid();
};

AdvancedTradingChart.prototype.connectWebSocket = function() {
    console.log('Connecting to real-time data feed...');
    // Implement WebSocket connection for real-time updates
};

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

// Initialize the advanced trading chart when page loads
var advancedChart;
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