/**
 * Candlestick Charts Integration for existing charts.html UI
 * Uses Plotly.js for rendering candlestick charts with external PostgreSQL data
 */

// Global variables
let currentSymbol = null;
let currentPeriod = "1M";
let searchTimeout = null;
let chart = null;

// Initialize when page loads
document.addEventListener("DOMContentLoaded", function () {
    // Hide skeleton first
    if (window.skeletonLoader) {
        window.skeletonLoader.hideChartsSkeleton();
    }
    bindEventListeners();
    hideChart();
    // Ensure chart container is hidden by default
    hideChartContainer();
});

function bindEventListeners() {
    // Symbol search input
    const symbolInput = document.getElementById("symbolSearch");

    if (symbolInput) {
        // Debounced search input
        symbolInput.addEventListener("input", function (e) {
            const query = e.target.value.trim();

            // Clear previous timeout
            clearTimeout(searchTimeout);

            if (query.length === 0) {
                // When search box is cleared, hide everything
                hideSearchResults();
                clearSymbolSearchAndChart();
                hideChartContainer();
            } else if (query.length >= 1) {
                // Search for any character input (reduced from 2 to 1)
                searchTimeout = setTimeout(() => {
                    fetchSymbolSuggestions(query);
                }, 300);
            } else {
                hideSearchResults();
            }
        });

        // Load chart on Enter key
        symbolInput.addEventListener("keypress", function (e) {
            if (e.key === "Enter") {
                clearTimeout(searchTimeout);
                const symbol = e.target.value.trim().toUpperCase();
                if (symbol) {
                    selectSymbol(symbol);
                    hideSearchResults();
                }
            }
        });
    }

    // Category checkboxes
    const categoryCheckboxes = document.querySelectorAll(
        '.category-checkboxes input[type="checkbox"]',
    );
    categoryCheckboxes.forEach((checkbox) => {
        checkbox.addEventListener("change", function () {
            const query = document.getElementById("symbolSearch").value.trim();
            if (query.length >= 2) {
                clearTimeout(searchTimeout);
                fetchSymbolSuggestions(query);
            }
        });
    });

    // Timeframe buttons with debouncing
    let timeframeTimeout = null;
    const timeframeBtns = document.querySelectorAll(".timeframe-btn");
    timeframeBtns.forEach((btn) => {
        btn.addEventListener("click", function () {
            // Clear previous timeout
            if (timeframeTimeout) {
                clearTimeout(timeframeTimeout);
            }

            // Update active state immediately
            timeframeBtns.forEach((b) => b.classList.remove("active"));
            this.classList.add("active");

            // Update current period
            currentPeriod = this.dataset.period;

            // Debounce the actual data loading
            if (currentSymbol) {
                showLoading();
                timeframeTimeout = setTimeout(() => {
                    loadCandlestickData(currentSymbol, currentPeriod);
                }, 100); // Small delay to prevent rapid clicks
            }
        });
    });

    // Set default timeframe to 1W and ensure only one is selected
    timeframeBtns.forEach((btn) => btn.classList.remove("active"));

    const defaultBtn = document.querySelector(
        '.timeframe-btn[data-period="1W"]',
    );
    if (defaultBtn) {
        defaultBtn.classList.add("active");
        currentPeriod = "1W";
    } else {
        // Fallback to first button if 1W not found
        const firstBtn = timeframeBtns[0];
        if (firstBtn) {
            firstBtn.classList.add("active");
            currentPeriod = firstBtn.dataset.period;
        }
    }
}

function getSelectedCategories() {
    const selectedCategories = [];
    const checkboxes = document.querySelectorAll(
        '.category-checkboxes input[type="checkbox"]:checked',
    );
    checkboxes.forEach((checkbox) => {
        selectedCategories.push(checkbox.value);
    });
    return selectedCategories.length > 0 ? selectedCategories : ["NIFTY"];
}

function fetchSymbolSuggestions(query) {
    const categories = getSelectedCategories();
    const params = new URLSearchParams({
        search: query,
        categories: categories.join(","),
    });

    fetch(`/api/available-symbols?${params}`)
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                showSearchResults(data.symbols);
            } else {
                showSearchResults([]);
            }
        })
        .catch((error) => {
            console.error("Error fetching symbols:", error);
            showSearchResults([]);
        });
}

function showSearchResults(symbols) {
    const searchResults = document.getElementById("searchResults");

    if (symbols.length === 0) {
        searchResults.innerHTML =
            '<div class="search-result-item text-muted">No symbols found</div>';
    } else {
        searchResults.innerHTML = symbols
            .map(
                (symbol) =>
                    `<div class="search-result-item" data-symbol="${symbol}">${symbol}</div>`,
            )
            .join("");

        // Add click handlers for search results
        searchResults
            .querySelectorAll(".search-result-item")
            .forEach((item) => {
                if (item.dataset.symbol) {
                    item.addEventListener("click", function () {
                        const symbol = this.dataset.symbol;
                        document.getElementById("symbolSearch").value = symbol;
                        selectSymbol(symbol);
                        hideSearchResults();
                    });
                }
            });
    }

    searchResults.style.display = "block";
}

function hideSearchResults() {
    const searchResults = document.getElementById("searchResults");
    if (searchResults) {
        searchResults.style.display = "none";
    }
}

function selectSymbol(symbol) {
    // Validate symbol exists (you can add more validation here)
    if (!symbol || symbol.trim() === "") {
        clearSymbolSearchAndChart();
        hideChartContainer();
        return;
    }

    currentSymbol = symbol.toUpperCase();

    // Update selected symbols display
    updateSelectedSymbolsDisplay(currentSymbol);

    // Show chart container and loading
    showChartContainer();
    showLoading();

    // Load both metrics and chart data
    Promise.all([
        loadSymbolMetrics(currentSymbol),
        loadCandlestickData(currentSymbol, currentPeriod),
    ])
        .then(() => {
            hideLoading();
            // Chart container should remain visible on success
        })
        .catch((error) => {
            hideLoading();
            showErrorState(error.message);
            // If there's an error loading the symbol, hide chart container
            hideChartContainer();
            clearSymbolSearchAndChart();
        });
}

function updateSelectedSymbolsDisplay(symbol) {
    const selectedSymbolsDiv = document.getElementById("selectedSymbols");
    if (selectedSymbolsDiv) {
        selectedSymbolsDiv.innerHTML = `
            <div class="selected-symbol-tag">
                <span>${symbol}</span>
                <button class="remove-symbol" onclick="removeSymbol('${symbol}')">×</button>
            </div>
        `;
    }
}

function removeSymbol(symbol) {
    const selectedSymbolsDiv = document.getElementById("selectedSymbols");
    if (selectedSymbolsDiv) {
        selectedSymbolsDiv.innerHTML = "";
    }
    document.getElementById("symbolSearch").value = "";
    hideChart();
    hideChartContainer();
    currentSymbol = null;
}

function showChartContainer() {
    const noChartsMessage = document.getElementById("noChartsMessage");
    const chartContainer = document.getElementById("candlestickChartContainer");
    const noChartsInContainer = document.getElementById("noChartsInContainer");

    if (noChartsMessage) {
        noChartsMessage.style.display = "none";
    }
    if (chartContainer) {
        chartContainer.style.display = "block";
    }
    if (noChartsInContainer) {
        noChartsInContainer.style.display = "none";
    }

    // Also show price info container when showing chart
    const priceInfo = document.getElementById("priceInfo");
    if (priceInfo) {
        priceInfo.style.display = "flex";
    }
}

function hideChart() {
    const noChartsMessage = document.getElementById("noChartsMessage");
    const chartContainer = document.getElementById("candlestickChartContainer");

    if (noChartsMessage) {
        noChartsMessage.style.display = "block";
    }
    if (chartContainer) {
        chartContainer.style.display = "none";
    }

    // Clear selected symbols display
    const selectedSymbolsDiv = document.getElementById("selectedSymbols");
    if (selectedSymbolsDiv) {
        selectedSymbolsDiv.innerHTML = "";
    }

    // Clear chart title
    const chartTitle = document.getElementById("chartTitle");
    if (chartTitle) {
        chartTitle.textContent = "Chart";
    }

    currentSymbol = null;
}

function showLoading() {
    const loadingDiv = document.getElementById("chartLoading");
    if (loadingDiv) {
        loadingDiv.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="sr-only">Loading...</span>
                </div>
                <div class="loading-text">Loading chart data...</div>
                <div class="text-muted small mt-2">This may take a moment for longer time periods</div>
            </div>
        `;
        loadingDiv.style.display = "flex";
    }
}

function hideLoading() {
    const loadingDiv = document.getElementById("chartLoading");
    if (loadingDiv) {
        loadingDiv.style.display = "none";
    }
}

function loadSymbolMetrics(symbol) {
    return fetch(`/api/symbol-metrics?symbol=${symbol}`)
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                updateMetricsDisplay(data.metrics);
            }
        });
}

function updateMetricsDisplay(metrics) {
    const chartTitle = document.getElementById("chartTitle");
    const currentPrice = document.getElementById("currentPrice");
    const priceChange = document.getElementById("priceChange");
    const priceInfo = document.getElementById("priceInfo");

    if (chartTitle) {
        chartTitle.textContent = `${metrics.symbol}`;
    }

    if (currentPrice && metrics.current_price) {
        currentPrice.textContent = `₹${metrics.current_price.toFixed(2)}`;
    }

    if (priceChange && metrics.change_5d_pct !== null) {
        priceChange.textContent = metrics.change_5d_str;
        priceChange.className = `price-change ${metrics.change_5d_pct >= 0 ? "positive" : "negative"}`;
    }

    if (priceInfo) {
        priceInfo.style.display = "flex";
    }
}

function loadCandlestickData(symbol, period) {
    console.log(`🔄 Loading candlestick data for ${symbol} with period ${period}`);

    // Shorter timeout for better UX
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

    // Show specific loading message based on period
    const loadingMessages = {
        "1D": "Loading intraday data...",
        "1W": "Loading weekly data...",
        "1M": "Loading monthly data...",
        "3M": "Loading quarterly data...",
        "1Y": "Loading yearly data...",
        "5Y": "Loading 5-year data...",
    };

    updateLoadingMessage(loadingMessages[period] || "Loading chart data...");

    return fetch(`/api/candlestick-data?symbol=${symbol}&period=${period}`, {
        signal: controller.signal,
        headers: {
            "Cache-Control": "max-age=60", // 1 minute cache
        },
    })
        .then((response) => {
            clearTimeout(timeoutId);
            console.log(`📡 API response status: ${response.status}`);
            if (!response.ok) {
                if (response.status === 500) {
                    throw new Error(
                        "Database connection error. Please try again.",
                    );
                } else if (response.status === 408) {
                    throw new Error(
                        "Request timed out. Try selecting a shorter time period.",
                    );
                }
                throw new Error(`Server error: ${response.status}`);
            }
            return response.json();
        })
        .then((data) => {
            console.log(`📊 Received data:`, {
                success: data.success,
                dataCount: data.data ? data.data.length : 0,
                error: data.error,
                symbol: data.symbol,
                period: data.period
            });

            if (data.success && data.data && data.data.length > 0) {
                console.log(`✅ Calling renderCandlestickChart with ${data.data.length} data points`);
                renderCandlestickChart(data.data, symbol, period);
            } else if (data.error) {
                console.log(`❌ API returned error: ${data.error}`);
                showErrorState(data.error);
            } else {
                console.log(`⚠️ No data available for ${symbol} ${period}`);
                showErrorState("No data available for this symbol and period");
            }
        })
        .catch((error) => {
            clearTimeout(timeoutId);
            console.error(`💥 Error in loadCandlestickData:`, error);
            if (error.name === "AbortError") {
                showErrorState(
                    "Request timed out. Try selecting a shorter time period for faster loading.",
                );
            } else {
                console.error("Error loading chart data:", error);
                showErrorState(
                    error.message ||
                        "Error loading chart data. Please try again.",
                );
            }
        });
}

function updateLoadingMessage(message) {
    const loadingDiv = document.getElementById("chartLoading");
    if (loadingDiv) {
        const loadingText = loadingDiv.querySelector(".loading-text");
        if (loadingText) {
            loadingText.textContent = message;
        }
    }
}

function renderCandlestickChart(data, symbol, period = '1D') {
    console.log('renderCandlestickChart called with', data.length, 'data points for', symbol);

    // Show chart container when rendering
    showChartContainer();

    // Hide the no charts message inside container
    const noChartsInContainer = document.getElementById("noChartsInContainer");
    if (noChartsInContainer) {
        noChartsInContainer.style.display = "none";
    }

    const chartDiv = document.getElementById("candlestickChart");
    if (!chartDiv) {
        console.error('Chart div not found');
        return;
    }

    // Ensure chart container is visible and properly sized
    chartDiv.style.height = '400px';
    chartDiv.style.minHeight = '400px';
    chartDiv.style.width = '100%';
    chartDiv.style.display = 'block';
    chartDiv.style.position = 'relative';

    // Force layout recalculation
    chartDiv.offsetHeight;

    // Limit data points for better performance
    const maxDataPoints = 500;
    let chartData = data;

    if (data.length > maxDataPoints) {
        const step = Math.ceil(data.length / maxDataPoints);
        chartData = data.filter((_, index) => index % step === 0);
        console.log('Data reduced from', data.length, 'to', chartData.length, 'points');
    }

    // Clear previous chart
    chartDiv.innerHTML = "";

    // Debug data structure
    console.log('Sample data point:', chartData[0]);
    console.log('Total data points to render:', chartData.length);

    const trace = {
        x: chartData.map((d) => d.x),
        close: chartData.map((d) => parseFloat(d.close)),
        high: chartData.map((d) => parseFloat(d.high)),
        low: chartData.map((d) => parseFloat(d.low)),
        open: chartData.map((d) => parseFloat(d.open)),
        type: "candlestick",
        name: symbol,
        increasing: { line: { color: "#16a34a", width: 1 } },
        decreasing: { line: { color: "#dc2626", width: 1 } },
    };

    console.log('Trace prepared:', {
        xLength: trace.x.length,
        closeLength: trace.close.length,
        sampleClose: trace.close[0]
    });

    const layout = {
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: {
            color: "#ffffff",
            size: 11,
        },
        title: {
            text: `${symbol} Candlestick Chart`,
            font: { color: "#ffffff", size: 14 }
        },
        xaxis: {
            gridcolor: "#444444",
            color: "#cccccc",
            showgrid: true,
            zeroline: false,
            type: 'date',
            // For 1D period, show IST time with date. For other periods, show date and time
            tickformat: period === '1D' ? '%Y-%m-%d %H:%M IST' : '%Y-%m-%d %H:%M'
        },
        yaxis: {
            gridcolor: "#444444",
            color: "#cccccc",
            showgrid: true,
            zeroline: false,
            title: { text: 'Price', font: { color: "#cccccc" } }
        },
        margin: {
            l: 60,
            r: 30,
            t: 50,
            b: 60,
        },
        height: 400,
        autosize: true,
        showlegend: false,
        dragmode: "zoom",
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ["pan2d", "lasso2d", "select2d", "autoScale2d"],
        displaylogo: false,
        scrollZoom: true,
    };

    // Use Plotly.react for better performance with comprehensive error handling
    try {
        console.log('🎯 Attempting to render chart...');
        console.log('📋 Chart div dimensions:', {
            width: chartDiv.offsetWidth,
            height: chartDiv.offsetHeight,
            display: window.getComputedStyle(chartDiv).display
        });

        if (typeof Plotly !== 'undefined') {
            console.log('✅ Plotly library is available, proceeding with render...');
            console.log('📊 Final trace data preview:', {
                xCount: trace.x.length,
                closeCount: trace.close.length,
                firstX: trace.x[0],
                firstClose: trace.close[0],
                lastX: trace.x[trace.x.length - 1],
                lastClose: trace.close[trace.close.length - 1]
            });

            // Use newPlot instead of react for more reliable rendering
            Plotly.newPlot(chartDiv, [trace], layout, config).then(() => {
                console.log('🎉 Chart rendered successfully for', symbol);
                // Update chart title after successful render
                const chartTitle = document.getElementById("chartTitle");
                if (chartTitle) {
                    chartTitle.textContent = `${symbol} Chart`;
                }

                // Verify chart was actually rendered
                const plotlyDiv = chartDiv.querySelector('.plotly-graph-div');
                console.log('📈 Plotly chart div created:', !!plotlyDiv);

                if (!plotlyDiv) {
                    console.error('⚠️ Chart div not created, trying alternative approach...');
                    // Force resize and redraw
                    setTimeout(() => {
                        try {
                            Plotly.Plots.resize(chartDiv);
                            console.log('🔄 Forced chart resize');
                        } catch (e) {
                            console.error('Resize failed:', e);
                        }
                    }, 100);
                }

            }).catch((error) => {
                console.error('💥 Plotly rendering error:', error);
                console.error('Error details:', {
                    name: error.name,
                    message: error.message,
                    stack: error.stack
                });
                showErrorState(`Chart rendering failed: ${error.message}`);
            });
        } else {
            console.error('❌ Plotly not loaded - checking script tags');
            const plotlyScript = document.querySelector('script[src*="plotly"]');
            console.log('Plotly script found:', !!plotlyScript);
            if (plotlyScript) {
                console.log('Plotly script src:', plotlyScript.src);
            }
            showErrorState('Chart library not loaded. Please refresh the page.');
        }
    } catch (error) {
        console.error('💥 Exception in chart rendering function:', error);
        console.error('Error details:', {
            name: error.name,
            message: error.message,
            stack: error.stack
        });
        showErrorState(`Chart rendering failed: ${error.message}`);
    }
}

// Function to clear search and chart
function clearSymbolSearchAndChart() {
    const searchInput = document.getElementById("symbolSearch");
    const searchResults = document.getElementById("searchResults");

    if (searchInput) {
        searchInput.value = "";
    }

    if (searchResults) {
        searchResults.innerHTML = "";
        searchResults.style.display = "none";
    }

    // Clear chart content
    const chartDiv = document.getElementById("candlestickChart");
    if (chartDiv) {
        chartDiv.innerHTML = "";
    }

    // Hide chart container and show "No Charts Selected" message
    hideChart();
    hideChartContainer();

    // Show no charts message inside container
    const noChartsInContainer = document.getElementById("noChartsInContainer");
    if (noChartsInContainer) {
        noChartsInContainer.style.display = "block";
    }

    // Clear selected symbols display
    const selectedSymbolsDiv = document.getElementById("selectedSymbols");
    if (selectedSymbolsDiv) {
        selectedSymbolsDiv.innerHTML = "";
    }

    // Clear price info
    const priceInfo = document.getElementById("priceInfo");
    if (priceInfo) {
        priceInfo.style.display = "none";
    }

    // Reset chart title
    const chartTitle = document.getElementById("chartTitle");
    if (chartTitle) {
        chartTitle.textContent = "Chart";
    }

    // Reset global state
    currentSymbol = null;
}

// Function to show chart container and hide "No Charts Selected" message
function showChartContainer() {
    const chartContainer = document.getElementById("candlestickChartContainer");
    const noChartsMessage = document.getElementById("noChartsMessage");

    if (chartContainer) {
        chartContainer.style.display = "block";
    }

    if (noChartsMessage) {
        noChartsMessage.style.display = "none";
    }
}

// Function to hide chart container and show "No Charts Selected" message  
function hideChartContainer() {
    const chartContainer = document.getElementById("candlestickChartContainer");
    const noChartsMessage = document.getElementById("noChartsMessage");
    const noChartsInContainer = document.getElementById("noChartsInContainer");

    if (chartContainer) {
        chartContainer.style.display = "block"; // Keep container visible
    }

    if (noChartsMessage) {
        noChartsMessage.style.display = "none"; // Hide external message
    }

    if (noChartsInContainer) {
        noChartsInContainer.style.display = "block"; // Show internal message
    }
}

// Function to show "No Charts Selected" message
function showNoChartsMessage() {
    const noChartsMessage = document.getElementById("noChartsMessage");
    if (noChartsMessage) {
        noChartsMessage.style.display = "block";
    }
}

function showErrorState(message) {
    const chartDiv = document.getElementById("candlestickChart");
    if (chartDiv) {
        chartDiv.innerHTML = `
            <div class="chart-error text-center py-5">
                <i class="fas fa-exclamation-triangle fa-3x mb-3 text-warning"></i>
                <h4 class="text-muted">Error Loading Chart</h4>
                <p class="text-muted">${message}</p>
            </div>
        `;
    }
}



// Additional cleanup when clicking outside search container
document.addEventListener("click", function (e) {
    if (!e.target.closest(".search-container")) {
        hideSearchResults();
    }
});