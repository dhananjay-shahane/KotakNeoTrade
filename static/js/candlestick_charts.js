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

            if (query.length >= 2) {
                // Add debouncing to reduce API calls
                searchTimeout = setTimeout(() => {
                    fetchSymbolSuggestions(query);
                }, 300);
            } else {
                hideSearchResults();
                if (query.length === 0) {
                    hideChart();
                }
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
    currentSymbol = symbol;

    // Update selected symbols display
    updateSelectedSymbolsDisplay(symbol);

    // Show chart container and loading
    showChartContainer();
    showLoading();

    // Load both metrics and chart data
    Promise.all([
        loadSymbolMetrics(symbol),
        loadCandlestickData(symbol, currentPeriod),
    ])
        .then(() => {
            hideLoading();
        })
        .catch((error) => {
            hideLoading();
            showErrorState(error.message);
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
    currentSymbol = null;
}

function showChartContainer() {
    const noChartsMessage = document.getElementById("noChartsMessage");
    const chartContainer = document.getElementById("candlestickChartContainer");

    if (noChartsMessage) {
        noChartsMessage.style.display = "none";
    }
    if (chartContainer) {
        chartContainer.style.display = "block";
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
            if (data.success && data.data && data.data.length > 0) {
                renderCandlestickChart(data.data, symbol);
            } else if (data.error) {
                showErrorState(data.error);
            } else {
                showErrorState("No data available for this symbol and period");
            }
        })
        .catch((error) => {
            clearTimeout(timeoutId);
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

function renderCandlestickChart(data, symbol) {
    const chartDiv = document.getElementById("candlestickChart");

    if (!chartDiv) return;

    // Limit data points for better performance
    const maxDataPoints = 500;
    let chartData = data;

    if (data.length > maxDataPoints) {
        // Sample data to reduce rendering load
        const step = Math.ceil(data.length / maxDataPoints);
        chartData = data.filter((_, index) => index % step === 0);
    }

    // Clear previous chart
    chartDiv.innerHTML = "";

    const trace = {
        x: chartData.map((d) => d.x),
        close: chartData.map((d) => d.close),
        high: chartData.map((d) => d.high),
        low: chartData.map((d) => d.low),
        open: chartData.map((d) => d.open),
        type: "candlestick",
        name: symbol,
        increasing: { line: { color: "#16a34a", width: 1 } },
        decreasing: { line: { color: "#dc2626", width: 1 } },
    };

    const layout = {
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: {
            color: "#ffffff",
            size: 11,
        },
        xaxis: {
            gridcolor: "#444444",
            color: "#cccccc",
            showgrid: true,
            zeroline: false,
        },
        yaxis: {
            gridcolor: "#444444",
            color: "#cccccc",
            showgrid: true,
            zeroline: false,
        },
        margin: {
            l: 45,
            r: 45,
            t: 25,
            b: 45,
        },
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

    // Use Plotly.react for better performance with error handling
    try {
        if (typeof Plotly !== 'undefined') {
            Plotly.react(chartDiv, [trace], layout, config).then(() => {
                console.log('Chart rendered successfully for', symbol);
            }).catch((error) => {
                console.error('Plotly rendering error:', error);
                showErrorState('Chart rendering failed. Please try again.');
            });
        } else {
            console.error('Plotly not loaded');
            showErrorState('Chart library not loaded. Please refresh the page.');
        }
    } catch (error) {
        console.error('Error rendering chart:', error);
        showErrorState('Chart rendering failed. Please try again.');
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

// Hide search results when clicking outside
document.addEventListener("click", function (e) {
    if (!e.target.closest(".search-container")) {
        hideSearchResults();
    }
});
